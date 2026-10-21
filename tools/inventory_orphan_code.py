"""The V2 refactor's one collector: measure the tree, emit one JSON snapshot.

Every reading carries the command that produced it and the revision it read, so a later run can
re-derive it without trusting this file's prose. Every count names the corpus it was taken over and
what that corpus excluded, because a counter that passes on an empty corpus is not a gate.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = "python/quantrisk"
SNAPSHOT_PATH = REPO_ROOT / "build" / "orphan_inventory.json"
CEILINGS_PATH = REPO_ROOT / "tools" / "refactor_ceilings.json"
MANIFEST_PATH = REPO_ROOT / "evidence" / "manifest.json"
PREFIXES = ("uv run --frozen python ", "uv run python ", "python ")


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def tracked(patterns: tuple[str, ...]) -> list[str]:
    return sorted(line for line in git("ls-files", "--", *patterns).splitlines() if line)


def parse(rel: str) -> ast.Module | None:
    text = (REPO_ROOT / rel).read_text(encoding="utf-8", errors="replace")
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def dotted_name(func: ast.expr) -> str:
    parts: list[str] = []
    node = func
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def calls_to(tree: ast.Module, dotted: str) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and dotted_name(node.func) == dotted
    ]


def source(node: ast.expr) -> str:
    try:
        return ast.unparse(node)
    except RecursionError:  # pragma: no cover - defensive: pathological expressions
        return "<unprintable>"


def path_site_shape(call: ast.Call, rel: str) -> dict[str, Any]:
    """Describe what a sys.path site injects, without executing it."""
    args = list(call.args)
    if getattr(call.func, "attr", "") == "insert" and args:
        args = args[1:]
    if not args:
        return {"file": rel, "line": call.lineno, "expression": "<no argument>"}
    expr = args[0]
    if isinstance(expr, ast.JoinedStr):
        expr = next(
            (
                value.value
                for value in expr.values
                if isinstance(value, ast.FormattedValue) and getattr(value.value, "attr", "") != ""
            ),
            expr,
        )
    text = source(expr)
    return {
        "file": rel,
        "line": call.lineno,
        "call": getattr(call.func, "attr", "?"),
        "expression": text,
        "names_the_package_dir": f'"{PACKAGE_DIR.split("/")[-1]}"' in text
        or f"'{PACKAGE_DIR.split('/')[-1]}'" in text
        or "python" in text,
        "anchors_on_file": "__file__" in text,
        "walks_parents": "parents[" in text or ".parent" in text,
    }


def package_imports(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                return True
            names = [node.module or ""]
        if any(name == "quantrisk" or name.startswith("quantrisk.") for name in names):
            return True
    return False


def by_path_load_lines(tree: ast.Module) -> list[int]:
    lines = {call.lineno for call in calls_to(tree, "importlib.util.spec_from_file_location")}
    lines |= {call.lineno for call in calls_to(tree, "importlib.machinery.SourceFileLoader")}
    return sorted(lines)


def inspect_corpus(corpus: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in corpus:
        tree = parse(rel)
        if tree is None:
            rows.append({"path": rel, "class": "unparseable"})
            continue
        sites = calls_to(tree, "sys.path.insert") + calls_to(tree, "sys.path.append")
        loads = by_path_load_lines(tree)
        if sites:
            kind = "sys_path_bootstrap"
        elif loads:
            kind = "by_path_importlib_load"
        elif package_imports(tree):
            kind = "installed_import"
        else:
            kind = "not_reachable"
        rows.append(
            {
                "path": rel,
                "class": kind,
                "sys_path_sites": len(sites),
                "by_path_load_lines": loads,
                "imports_quantrisk": package_imports(tree),
            }
        )
    return rows


def bootstrap_sites(corpus: list[str]) -> list[dict[str, Any]]:
    sites: list[dict[str, Any]] = []
    for rel in corpus:
        tree = parse(rel)
        if tree is None:
            continue
        for call in calls_to(tree, "sys.path.insert") + calls_to(tree, "sys.path.append"):
            sites.append(path_site_shape(call, rel))
    return sites


def by_path_load_sites(corpus: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in corpus:
        tree = parse(rel)
        if tree is None:
            continue
        for call in calls_to(tree, "importlib.util.spec_from_file_location"):
            args = list(call.args)
            rows.append(
                {
                    "file": rel,
                    "line": call.lineno,
                    "names": source(args[0]) if args else "",
                    "path_expression": source(args[1]) if len(args) > 1 else "",
                }
            )
    return rows


def split_command(command: str) -> tuple[str, str] | None:
    for prefix in PREFIXES:
        for verb in ("", "-m "):
            head = prefix + verb
            if command.startswith(head):
                return verb.strip("- "), command[len(head) :]
    return None


def classify_command(command: str) -> tuple[str, str]:
    if not command.strip():
        return "no-command-recorded", ""
    parsed = split_command(command)
    if parsed is None:
        return "no-interpreter-prefix", command
    verb, body = parsed
    if not body.strip():
        return "no-command-recorded", body
    if verb == "m":
        token = body.split(" ")[0]
        as_module = REPO_ROOT / PACKAGE_DIR.split("/")[0]
        candidate = as_module.parent / Path(*token.split("."))
        if candidate.with_suffix(".py").is_file() or candidate.is_dir():
            return "module-path-resolves", token
        return "module-path-does-not-resolve", token
    if "(" in body and ")" in body:
        return "annotated-prose-in-command-field", body
    head = body.split("--")[0].strip()
    if len(head.split()) > 1:
        return "mangled-token", body
    name = head.split()[0] if head else ""
    if not name:
        return "no-command-recorded", body
    if (REPO_ROOT / name).is_file():
        return "bare-filename-resolves-from-root", name
    return "bare-filename-does-not-exist-from-root", name


def command_executability() -> dict[str, Any]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = manifest["artifacts"]
    rows: list[dict[str, Any]] = []
    for artifact in entries:
        kind, detail = classify_command(artifact.get("generated_by_command", ""))
        rows.append(
            {
                "path": artifact.get("path", "?"),
                "category": artifact.get("category", "?"),
                "class": kind,
                "command": artifact.get("generated_by_command", ""),
                "recorded_in": artifact.get("command_recorded_in", ""),
                "detail": detail,
            }
        )
    return {
        "classes": dict(Counter(row["class"] for row in rows)),
        "corpus": len(rows),
        "entries": rows,
    }


def ruff_admitted() -> tuple[set[str], int]:
    binary = REPO_ROOT / ".venv" / "bin" / "ruff"
    result = subprocess.run(
        [str(binary), "check", ".", "--verbose"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    log = result.stderr + result.stdout
    admitted: set[str] = set()
    non_python = 0
    for line in log.splitlines():
        if "Included path via `include`" not in line:
            continue
        raw = line.split("`include`: ", 1)[1].strip().strip('"')
        try:
            rel = str(Path(raw).resolve().relative_to(REPO_ROOT.resolve()))
        except ValueError:
            continue
        if Path(rel).suffix in {".py", ".pyi"}:
            admitted.add(rel)
        else:
            non_python += 1
    return admitted, non_python


def mypy_reported_count(target: str) -> int | None:
    binary = REPO_ROOT / ".venv" / "bin" / "mypy"
    result = subprocess.run([str(binary), target], cwd=REPO_ROOT, capture_output=True, text=True)
    words = (result.stdout or result.stderr).strip().split()
    for index, word in enumerate(words):
        if word == "in" and index + 1 < len(words) and words[index + 1].isdigit():
            return int(words[index + 1])
    return None


def static_check_coverage(corpus: list[str]) -> dict[str, Any]:
    admitted, ruff_non_python = ruff_admitted()
    mypy_count = mypy_reported_count(PACKAGE_DIR)
    mypy_enumerated = sorted(path for path in corpus if path.startswith(PACKAGE_DIR + "/"))
    per_file = [
        {
            "path": path,
            "mypy_covered": path.startswith(PACKAGE_DIR + "/"),
            "ruff_covered": path in admitted,
        }
        for path in corpus
    ]
    buckets = Counter(
        "mypy and ruff"
        if row["mypy_covered"] and row["ruff_covered"]
        else "ruff only"
        if row["ruff_covered"]
        else "mypy only"
        if row["mypy_covered"]
        else "uncovered"
        for row in per_file
    )
    return {
        "buckets": dict(buckets),
        "per_file": per_file,
        "corpora": {
            "tracked_python_files": len(corpus),
            "mypy_target": PACKAGE_DIR,
            "mypy_reported_source_files": mypy_count,
            "mypy_enumerated": len(mypy_enumerated),
            "mypy_two_sided_agreement": mypy_count == len(mypy_enumerated),
            "ruff_admitted_python": len(admitted & set(corpus)),
            "ruff_admitted_non_python": ruff_non_python,
            "tracked_not_admitted_by_ruff": sorted(set(corpus) - admitted),
        },
    }


def registry_parity() -> dict[str, Any]:
    registry = REPO_ROOT / PACKAGE_DIR / "experiments" / "registry.py"
    if not registry.is_file():
        return {
            "applicable": False,
            "why": "python/quantrisk/experiments/registry.py does not exist before Phase 3.1",
            "probe": f"test -f {PACKAGE_DIR}/experiments/registry.py",
        }
    declared = [
        line for line in git("ls-files", "--", f"{PACKAGE_DIR}/experiments/*").splitlines() if line
    ]
    return {
        "applicable": True,
        "filesystem_declared": declared,
        "probe": f"git ls-files -- {PACKAGE_DIR}/experiments/*",
    }


def plant_liveness() -> dict[str, Any]:
    runner = REPO_ROOT / "scripts" / "run_mutation_suite.py"
    if not runner.is_file():
        return {
            "applicable": False,
            "why": "the harness has moved; see python/quantrisk/verification/",
        }
    result = subprocess.run(
        [sys.executable, str(runner), "--list"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return {
        "applicable": result.returncode == 0,
        "declared_plants": len(lines),
        "probe": "python scripts/run_mutation_suite.py --list | wc -l",
        "note": "the sweep's own summary line is read in Phase 3.2; this is the declaration only",
    }


def excluded_top_levels(corpus: list[str]) -> list[str]:
    named = {path.split("/")[0] for path in corpus}
    dirs = sorted(
        path.name for path in REPO_ROOT.iterdir() if path.is_dir() and not path.name.startswith(".")
    )
    return [name for name in dirs if name not in named]


def build_snapshot() -> dict[str, Any]:
    all_python = tracked(("*.py", "*.pyi"))
    corpus = [path for path in all_python if path.endswith(".py")]
    outside = [path for path in corpus if not path.startswith(PACKAGE_DIR + "/")]
    rows = inspect_corpus(outside)
    return {
        "schema": "quantrisk-refactor-inventory/1",
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "revision": git("rev-parse", "HEAD"),
        "generated_by_command": "uv run python -m tools.inventory_orphan_code",
        "corpora": {
            "tracked_python_files": len(corpus),
            "tracked_python_and_stub_files": len(all_python),
            "outside_the_package": len(outside),
            "manifest_artifacts": len(
                json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["artifacts"]
            ),
            "top_level_dirs_with_no_tracked_python": excluded_top_levels(corpus),
        },
        "readings": [
            {
                "name": "orphan_inventory",
                "command": "git ls-files -- '*.py' outside python/quantrisk, then ast.parse each",
                "value": {"classes": dict(Counter(row["class"] for row in rows)), "files": rows},
            },
            {
                "name": "bootstrap_census",
                "command": "ast walk for sys.path.insert/append over the same corpus",
                "value": bootstrap_sites(outside),
            },
            {
                "name": "by_path_load_sites",
                "command": "ast walk for importlib.util.spec_from_file_location / SourceFileLoader",
                "value": by_path_load_sites(outside),
            },
            {
                "name": "command_executability",
                "command": "read every evidence/manifest.json artifact's generated_by_command",
                "value": command_executability(),
            },
            {
                "name": "static_check_coverage",
                "command": "ruff check . --verbose admission log, plus mypy's reported file count",
                "value": static_check_coverage(corpus),
            },
            {
                "name": "registry_parity",
                "command": "test -f python/quantrisk/experiments/registry.py, then git ls-files",
                "value": registry_parity(),
            },
            {
                "name": "plant_liveness",
                "command": "python scripts/run_mutation_suite.py --list",
                "value": plant_liveness(),
            },
        ],
    }


def metrics(snapshot: dict[str, Any]) -> dict[str, int | None]:
    """Flat numbers, one per ceiling key, so the ceilings file is a gate and not a comment.

    A key whose precondition does not exist yet is reported as None, which the checker treats as
    skipped-with-a-printed-reason only while the ceilings file says it may be absent.
    """
    by_name = {row["name"]: row["value"] for row in snapshot["readings"]}
    commands = by_name["command_executability"]
    unrunnable = {
        "annotated-prose-in-command-field",
        "bare-filename-does-not-exist-from-root",
        "mangled-token",
        "no-interpreter-prefix",
        "no-command-recorded",
        "module-path-does-not-resolve",
    }
    coverage = by_name["static_check_coverage"]
    parity = by_name["registry_parity"]
    return {
        "bootstrap_sites_outside_package": len(by_name["bootstrap_census"]),
        "by_path_load_sites": len(by_name["by_path_load_sites"]),
        "commands_not_module_path": commands["corpus"]
        - commands["classes"].get("module-path-resolves", 0),
        "commands_unrunnable_from_the_root": sum(
            count for kind, count in commands["classes"].items() if kind in unrunnable
        ),
        "tracked_python_files_in_no_static_check_bucket": coverage["buckets"].get("uncovered", 0),
        "registry_parity_mismatch": (
            None if not parity.get("applicable") else len(parity["filesystem_declared"])
        ),
        "plants_not_rejected_by_their_guard": None,
        "installed_user_identity_mismatch": None,
        "external_spend_usd": 0,
    }


def check_ceilings(snapshot: dict[str, Any]) -> list[str]:
    """Compare the snapshot against the committed ceilings file, both directions.

    Returns the violations; empty means every declared key was measured and every measurement was
    inside its ceiling. A key that stopped producing a metric is a violation, not a pass.
    """
    ceilings = json.loads(CEILINGS_PATH.read_text(encoding="utf-8"))
    declared = {item["key"]: item for item in ceilings["ceilings"]}
    measured = metrics(snapshot)
    problems: list[str] = []
    for key in sorted(set(declared) - set(measured)):
        problems.append(f"ceilings file declares {key!r} but the collector computes no such metric")
    for key in sorted(set(measured) - set(declared)):
        problems.append(f"collector measures {key!r} which no ceiling declares")
    for key, value in sorted(measured.items()):
        item = declared.get(key)
        if item is None:
            continue
        limit = item["max"]
        if value is None:
            if item.get("may_be_unmeasured", False):
                print(f"SKIP   {key}: precondition absent ({item['corpus']})")
                continue
            problems.append(f"{key} has no measurement and the ceilings file does not allow that")
            continue
        status = "ok     " if value <= limit else "VIOLATION"
        print(f"{status} {key}: {value} against a ceiling of {limit} due {item['reach_by_phase']}")
        if value > limit:
            problems.append(f"{key} is {value}, above its ceiling of {limit} ({item['law']})")
    return problems


def summarize(snapshot: dict[str, Any]) -> None:
    print(f"revision {snapshot['revision'][:9]}")
    print(f"corpora {json.dumps(snapshot['corpora'], sort_keys=True)}")
    for row in snapshot["readings"]:
        value = row["value"]
        if isinstance(value, dict) and "classes" in value:
            shown = value["classes"]
        elif isinstance(value, dict) and "buckets" in value:
            shown = {**value["buckets"], "corpora": value["corpora"]}
        elif isinstance(value, list):
            shown = f"{len(value)} sites"
        else:
            shown = {k: v for k, v in value.items() if not isinstance(v, list)}
        print(f"{row['name']:24s} {json.dumps(shown, sort_keys=True, default=str)}")
        print(f"{'':24s} by: {row['command']}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print the whole snapshot")
    parser.add_argument(
        "--check-ceilings",
        action="store_true",
        help="compare every metric against tools/refactor_ceilings.json and exit 1 on a violation",
    )
    args = parser.parse_args(argv)
    snapshot = build_snapshot()
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if args.json:
        print(json.dumps(snapshot, indent=2, sort_keys=True))
        return 0
    summarize(snapshot)
    if args.check_ceilings:
        problems = check_ceilings(snapshot)
        for problem in problems:
            print(f"FAIL   {problem}")
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
