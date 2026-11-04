"""The V2 refactor's one collector: measure the tree, emit one JSON snapshot.

Every reading carries the command that produced it and the revision it read, so a later run can
re-derive it without trusting this file's prose. Every count names the corpus it was taken over and
what that corpus excluded, because a counter that passes on an empty corpus is not a gate.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
import tomllib
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = "python/quantrisk"
PACKAGE_IMPORT = "quantrisk"
SNAPSHOT_PATH = REPO_ROOT / "build" / "orphan_inventory.json"
CEILINGS_PATH = REPO_ROOT / "tools" / "refactor_ceilings.json"
STATIC_CHECK_KEY = "tracked_python_files_in_no_static_check_bucket"
FORMATTER_KEY = "tracked_files_outside_the_formatter_corpus"
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
        # `-m ` first: the bare prefix is a prefix of it, so trying "" first would hand the module
        # form back as a script path beginning with "-m" and every canonical command would be
        # classified as mangled.
        for verb in ("-m ", ""):
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
        relative = Path(*token.split("."))
        package_root = REPO_ROOT / PACKAGE_DIR.split("/")[0]
        # A module is either a repo tool (`tools.*`, at the checkout root) or shipped code
        # (`quantrisk.*`, under the package directory). Reading only one of the two is the bug this
        # branch carried unseen: nothing reached it while the `-m ` prefix lost to the bare one.
        candidates = [REPO_ROOT / relative, package_root / relative]
        if any(
            candidate.with_suffix(".py").is_file() or candidate.is_dir() for candidate in candidates
        ):
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


def project_binary(name: str) -> str:
    """The tool this project's own environment holds, with the resolution printed by its callers.

    `.venv/bin` first: the census reads *this* ruff's and *this* mypy's walk of the corpus, and a
    PATH lookup could answer the same question about a different tool. The fallback exists because
    the ceilings lane now runs on a runner, where an absolute laptop path is not a fact of the lane
    -- and a census that cannot find its instrument says so by name instead of raising
    FileNotFoundError from a subprocess call.
    """
    venv = REPO_ROOT / ".venv" / "bin" / name
    if venv.exists():
        return str(venv)
    found = shutil.which(name)
    if found is None:
        raise AssertionError(
            f"no `{name}` at {venv} and none on PATH: the census has no instrument"
        )
    return found


def ruff_inclusions(*arguments: str) -> tuple[set[str], int]:
    """Every path Ruff's own resolver admits, and how many of them are not Python.

    The log rather than a glob: the question V2-05 asks is what the tool *walked*, and a walk
    rebuilt from `git ls-files` would answer it with the very set the claim is about. The second
    value counts the admitted paths that are not Python or stubs, because a prose count explained
    only by a tool's defaults is the kind of figure this repository has been bitten by quoting as a
    Python signal.
    """
    binary = project_binary("ruff")
    result = subprocess.run(
        [binary, *arguments, "--verbose"], cwd=REPO_ROOT, capture_output=True, text=True
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
        admitted.add(rel)
        if Path(rel).suffix not in {".py", ".pyi"}:
            non_python += 1
    return admitted, non_python


def ruff_admitted() -> tuple[set[str], int]:
    """The Python and stub files `ruff check` admits, with the rest it admits counted separately."""
    admitted, non_python = ruff_inclusions("check", ".")
    return {path for path in admitted if Path(path).suffix in {".py", ".pyi"}}, non_python


def mypy_targets() -> tuple[list[str], str]:
    """The directories CI type-checks, and the command that says so, read from the workflow.

    D7 extends `mypy`'s target list to `tools/`, and a second copy of that list in this file would
    be a second fact -- the copy is what goes stale, and a stale copy here would certify coverage
    the runner never measured. The workflow is where the list lives, so this parses it and returns
    the command with the reading, because a census that names its own input is the only kind a
    reader can re-derive.
    """
    workflow_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    steps = [
        step
        for job in (workflow.get("jobs") or {}).values()
        for step in (job.get("steps") or [])
        if str(step.get("name", "")) == "mypy"
    ]
    if len(steps) != 1:
        raise AssertionError(
            f"expected one mypy step in {workflow_path.name}, found {len(steps)}: the census "
            "cannot read a target list it has to choose between"
        )
    command = str(steps[0].get("run", "")).strip()
    tokens = command.split()
    if tokens[:3] != ["uv", "run", "mypy"]:
        raise AssertionError(f"the mypy step does not start with `uv run mypy`: {command!r}")
    targets = [token for token in tokens[3:] if not token.startswith("-")]
    if not targets:
        raise AssertionError(f"the mypy step names no target: {command!r}")
    return sorted(targets), command


def under(path: str, prefix: str) -> bool:
    """Whether a repository-relative file sits inside a declared directory."""
    return path == prefix or path.startswith(prefix.rstrip("/") + "/")


def mypy_reported_count(targets: list[str]) -> tuple[int | None, int]:
    """The file count mypy names, and the exit code it printed it with.

    The count comes from the "(checked N source files)" tail, not from the first "in <n>" in the
    line: a failing run prints "Found 5 errors in 1 file (checked 33 source files)", and reading the
    first number after "in" reports the files that broke as if it were the corpus size. The exit
    code travels with the reading so a red type check shows up as a named failure rather than as a
    suspicious count -- §4.3's rule that a measurement which cannot report its own failing branch is
    not a measurement.
    """
    binary = project_binary("mypy")
    result = subprocess.run([binary, *targets], cwd=REPO_ROOT, capture_output=True, text=True)
    output = result.stdout + result.stderr
    for pattern in (r"\(checked (\d+) source files\)", r"found in (\d+) source files"):
        checked = re.search(pattern, output)
        if checked:
            return int(checked.group(1)), result.returncode
    return None, result.returncode


def declared_bucket_expectations() -> tuple[dict[str, dict[str, str]], str]:
    """Where each top-level Python directory is expected to sit, read from the ceilings file.

    L9's end state is that every tracked Python file is in exactly one of mypy-covered,
    ruff-covered-already, or a declared exemption, and D7 adds that nothing may be silently
    uncovered or double-counted. So the directory-to-bucket table lives in the policy asset and this
    reads it: a new directory of Python -- the shape `scripts/` had before P3.4 retired it -- is
    reported by name rather than absorbed into a bucket because the code had nowhere else to put it.
    """
    ceilings = json.loads(CEILINGS_PATH.read_text(encoding="utf-8"))
    row = next(item for item in ceilings["ceilings"] if item["key"] == STATIC_CHECK_KEY)
    return dict(row.get("bucket_expectations") or {}), row["key"]


def static_check_coverage(corpus: list[str]) -> dict[str, Any]:
    """Every tracked Python file in exactly one bucket, with the partition checked both ways.

    Two independent readings decide the buckets: the target list CI hands to `mypy`, parsed from the
    workflow that runs it so a second copy cannot go stale, and ruff's own inclusion log. `mypy`'s
    reported file count is compared with the enumeration of those targets, so a target list that
    stopped matching the lane -- or two targets overlapping and double-counting a file -- is the
    instrument failing, not the code. Each file's bucket is then compared with what the ceilings
    file declares for its directory, both ways: a directory no declaration covers, and a file whose
    bucket moved away from its declaration, are printed by name.
    """
    admitted, ruff_non_python = ruff_admitted()
    targets, command = mypy_targets()
    expectations, expectation_key = declared_bucket_expectations()
    mypy_count, mypy_exit_code = mypy_reported_count(targets)
    enumerated = {
        target: sorted(path for path in corpus if under(path, target)) for target in targets
    }
    checked = [path for group in enumerated.values() for path in group]
    per_file: list[dict[str, Any]] = []
    for path in corpus:
        is_checked = any(under(path, target) for target in targets)
        is_admitted = path in admitted
        bucket = (
            "mypy and ruff"
            if is_checked and is_admitted
            else "mypy only"
            if is_checked
            else "ruff only"
            if is_admitted
            else "uncovered"
        )
        per_file.append(
            {
                "path": path,
                "bucket": bucket,
                "directory": path.split("/")[0] if "/" in path else ".",
                "mypy_covered": is_checked,
                "ruff_covered": is_admitted,
            }
        )
    buckets = Counter(row["bucket"] for row in per_file)
    if sum(buckets.values()) != len(corpus):
        raise AssertionError(
            f"the buckets hold {sum(buckets.values())} of {len(corpus)} files, so a file landed in "
            "no bucket or in two, and the partition the ceiling is read against does not exist"
        )
    if len(checked) != len(set(checked)):
        raise AssertionError(
            f"two mypy targets name the same file, which double-counts it: {targets}"
        )
    undeclared = sorted(
        {row["directory"] for row in per_file if row["directory"] not in expectations}
    )
    misplaced = sorted(
        f"{row['path']} is {row['bucket']}, declared {expectations[row['directory']]['bucket']}"
        for row in per_file
        if row["directory"] in expectations
        and row["bucket"] != expectations[row["directory"]]["bucket"]
    )
    outside = sorted(
        row["path"]
        for row in per_file
        if row["bucket"] == "uncovered"
        or row["directory"] not in expectations
        or row["bucket"] != expectations.get(row["directory"], {}).get("bucket")
    )
    return {
        "buckets": dict(buckets),
        "per_file": per_file,
        "corpora": {
            "tracked_python_files": len(corpus),
            "instruments": {"mypy": project_binary("mypy"), "ruff": project_binary("ruff")},
            "files_outside_their_declaration": len(outside),
            "mypy_command": command,
            "mypy_targets": targets,
            "mypy_enumerated_per_target": {
                target: len(group) for target, group in enumerated.items()
            },
            "mypy_reported_source_files": mypy_count,
            "mypy_exit_code": mypy_exit_code,
            "mypy_two_sided_agreement": mypy_count == len(set(checked)) and mypy_exit_code == 0,
            "expectations_read_from": expectation_key,
            "declared_directories": sorted(expectations),
            "undeclared_directories": undeclared,
            "buckets_moving_from_their_declaration": misplaced,
            "ruff_admitted_python": len(admitted & set(corpus)),
            "ruff_admitted_non_python": ruff_non_python,
            "tracked_not_admitted_by_ruff": sorted(set(corpus) - admitted),
            "outside_the_declaration": outside,
            "uncovered_paths": sorted(
                row["path"] for row in per_file if row["bucket"] == "uncovered"
            ),
        },
    }


FORMATTER_SUFFIXES = (".py", ".pyi", ".md")


def formatter_census() -> dict[str, Any]:
    """What `ruff format --check .` walks, set-differenced against the tracked files it should walk.

    V2-05 is about a figure quoted as a Python-formatting signal by dated records across the tree,
    while Ruff's formatter
    also accepts Markdown: the count moves with the documentation, and with any file neither tracked
    nor ignored, which is why `docs/integrity_audit.md` 62(d) could explain a real spread between
    two readings by machine rather than by corpus. The comparator here is therefore two
    enumerations, not one number: Ruff's own inclusion log, and `git ls-files` over the three kinds
    the formatter accepts. A file on one side and not the other is named, and the count line is
    printed beside it as corroboration -- including the branch where a file needs formatting and the
    sentence splits in two.
    """
    binary = project_binary("ruff")
    plain = subprocess.run(
        [binary, "format", "--check", "."], cwd=REPO_ROOT, capture_output=True, text=True
    )
    text = plain.stdout + plain.stderr
    already = re.search(r"(\d+) files? already formatted", text)
    would = re.search(r"(\d+) files? would be reformatted", text)
    reported = int(already.group(1)) if already else 0
    reformatted = int(would.group(1)) if would else 0
    walked, walked_other = ruff_inclusions("format", "--check", ".")
    formattable = {path for path in walked if Path(path).suffix in FORMATTER_SUFFIXES}
    tracked_kinds = set(tracked(("*.py", "*.pyi", "*.md")))
    return {
        "command": (
            "ruff format --check . --verbose inclusion log, set-differenced against "
            "git ls-files '*.py' '*.pyi' '*.md'"
        ),
        "binary": binary,
        "exit_code": plain.returncode,
        "reported_already_formatted": reported or None,
        "reported_would_reformat": reformatted,
        "reported_total": reported + reformatted,
        "walked_formattable": len(formattable),
        "walked_other_kinds": walked_other,
        "tracked_formattable": len(tracked_kinds),
        "walked_but_not_tracked": sorted(formattable - tracked_kinds),
        "tracked_but_not_walked": sorted(tracked_kinds - formattable),
    }


# --- N6: what the `ast` census cannot see ------------------------------------
#
# `inspect_corpus` classifies a file as `not_reachable` when it holds no `sys.path` bootstrap, no
# by-path load and no `quantrisk` import. That is a statement about *static import edges*, and V3-03
# found it disagreeing with reality on every file it named: twelve of the thirteen were reached by
# pytest's own path convention or by `importlib.import_module`, and the thirteenth was the collector
# you are reading, executed by `-m tools.inventory_orphan_code`. A metric that calls a live module
# dead will eventually be used to delete it, so the class keeps its name and gains a second reader.

_PROBE_SCRIPT = r"""
import importlib, json, sys

roots, names = json.loads(sys.argv[1]), json.loads(sys.argv[2])
sys.path[:0] = roots
failures = {}


def attempt(name):
    try:
        importlib.import_module(name)
    except BaseException as error:  # every way an import fails, not only ImportError
        return f"{type(error).__name__}: {error}"[:160]
    return None


control = attempt("quantrisk")
for relative, name in names.items():
    problem = attempt(name)
    if problem is not None:
        failures[relative] = problem
print(json.dumps({"control": control, "failures": failures}))
"""


def module_name(rel: str) -> str | None:
    """The name a runtime import would use for this file, or None when it has no such name.

    The two conventions are the two the repository runs under: `tests/python` is on pytest's path
    by its own rootdir insertion, so a test module is reachable by its bare stem; `tools` is a
    package on the checkout root, so a tool is reachable as `tools.<stem>`. A path outside both is
    left unnamed rather than guessed at, and the reading says so instead of silently counting it.
    """
    if rel.startswith("tests/python/"):
        return Path(rel).stem
    if rel.startswith("tools/"):
        stem = Path(rel).stem
        return "tools" if stem == "__init__" else f"tools.{stem}"
    return None


def import_probe(dead: list[str]) -> dict[str, Any]:
    """Import every dead file by name in one child interpreter, and record what each one did.

    One child, not thirteen: the question is reachability, and a second process per file would cost
    a second of interpreter start-up each for no additional reading. The control is the package
    itself -- if `quantrisk` will not import, every failure below it is the environment's and the
    reading says so rather than reporting thirteen dead files.
    """
    names = {rel: name for rel in dead if (name := module_name(rel)) is not None}
    roots = [str(REPO_ROOT), str(REPO_ROOT / "tests" / "python")]
    result = subprocess.run(
        [sys.executable, "-c", _PROBE_SCRIPT, json.dumps(roots), json.dumps(names)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return {
            "control": f"the probe process produced no reading (exit {result.returncode})",
            "failures": {},
            "reachable": [],
            "attempted": len(names),
            "unnamed": sorted(set(dead) - set(names)),
            "interpreter": sys.executable,
        }
    failures = payload["failures"]
    return {
        "control": payload["control"],
        "failures": failures,
        "reachable": sorted(set(names) - set(failures)),
        "attempted": len(names),
        "unnamed": sorted(set(dead) - set(names)),
        "interpreter": sys.executable,
    }


def pytest_collection() -> dict[str, Any]:
    """Every file pytest's own collection reaches, by node id, in one collect-only run.

    Collection rather than execution: the question is whether anything will *run* the file, and a
    file that collects is a file the suite will execute. `-p no:cacheprovider` keeps the run from
    writing `.pytest_cache`, so a census never dirties the tree it is measuring.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=1200,
    )
    files: set[str] = set()
    errors: list[str] = []
    for line in result.stdout.splitlines():
        if line.startswith("ERROR "):
            errors.append(line.split(" ", 1)[1][:120])
        elif "::" in line and not line.startswith((" ", "=", "_")):
            files.add(line.split("::", 1)[0])
    tail = next((line for line in reversed(result.stdout.splitlines()) if line.strip()), "")
    return {
        "command": "python -m pytest --collect-only -q -p no:cacheprovider",
        "exit_code": result.returncode,
        "collected": len(files),
        "files": sorted(files),
        "collection_errors": errors,
        "tail": tail[:160],
    }


def runtime_reachability(dead: list[str]) -> dict[str, Any]:
    """Both runtime readings beside the census verdict, with each side's difference named.

    Three sets, never one number: what the parser calls dead, what an import reaches, and what
    pytest collects. The metric the ceilings file gates is the *residual* -- files dead by every
    instrument -- because that is the dangerous direction: a file this reading also cannot reach is
    the only kind a deletion may act on, and even then the reading is required first (N6).
    """
    probe = import_probe(dead)
    collection = pytest_collection()
    collected = set(collection["files"])
    by_import = probe["reachable"]
    by_pytest = sorted(rel for rel in dead if rel in collected)
    reached = set(by_import) | set(by_pytest)
    neither = sorted(set(dead) - reached)
    unavailable: list[str] = []
    if probe["control"] is not None:
        unavailable.append(f"the import probe's control failed: {probe['control']}")
    if not collected:
        unavailable.append("pytest's collection reached no file at all")
    return {
        "available": not unavailable,
        "unavailable_because": unavailable,
        "ast_dead": dead,
        "import_reachable": by_import,
        "import_failures": probe["failures"],
        "pytest_collected": by_pytest,
        "reached_by_neither": neither,
        "ast_dead_but_runtime_reaches": sorted(reached),
        "instruments": {
            "import_probe": {
                "command": "python -c <import probe>",
                "interpreter": probe["interpreter"],
                "attempted": probe["attempted"],
                "unnamed": probe["unnamed"],
                "control": "quantrisk",
                "control_result": probe["control"],
            },
            "pytest_collection": collection,
        },
    }


def external_dependencies() -> dict[str, Any]:
    """The runtime and optional dependency sets, against the names the ceilings file declares.

    L12's row used to report `external_spend_usd: 0` as a literal: a policy file asserting a budget
    and a collector returning the number it was told to return. Phase 4's third audit found it --
    the one shape this repository names as its own (V2-27, a declaration nobody compares) -- and the
    comparison that can disagree is the dependency set. A new package is the only way a refactor
    adds external spend without a network call, and the paid-call half has no static detector at
    all, so it stays a ledger reading rather than a number here.

    The dev group is excluded by name: `pytest`, `ruff`, `mypy`, `cmake`, `ninja`, `clang-format`,
    `pybind11`, `scipy`, `matplotlib`, `sympy` and `pyyaml` are instruments this lane runs, not
    runtime dependencies of the distribution, and counting them would make every tooling addition
    look like spend.
    """
    manifest = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = set(
        next(
            row
            for row in json.loads(CEILINGS_PATH.read_text(encoding="utf-8"))["ceilings"]
            if row["key"] == "external_dependencies_added"
        )["declared_dependencies"]
    )
    measured: set[str] = set()
    for requirement in manifest["project"]["dependencies"]:
        measured.add(re.split(r"[\s<>=!~\[]", requirement, maxsplit=1)[0])
    for group in (manifest["project"].get("optional-dependencies") or {}).values():
        for requirement in group:
            measured.add(re.split(r"[\s<>=!~\[]", requirement, maxsplit=1)[0])
    return {
        "measured": sorted(measured),
        "declared": sorted(declared),
        "added": sorted(measured - declared),
        "removed": sorted(declared - measured),
        "corpus": (
            "pyproject.toml [project].dependencies and every "
            "[project.optional-dependencies] group, set-differenced against this key's "
            "declared_dependencies; [dependency-groups].dev is excluded by name as tooling "
            "rather than runtime need"
        ),
        "probe": "tomllib.loads(pyproject.toml) against tools/refactor_ceilings.json",
    }


def _is_runnable_unit(path: str) -> bool:
    """A file that can be run, in either the root layout or the package layout."""
    if path.startswith("experiments/"):
        return path.endswith("/run.py")
    if path.startswith("benchmarks/"):
        return path.count("/") == 2
    if path.startswith(f"{PACKAGE_DIR}/experiments/"):
        return path.endswith("/__main__.py")
    if path.startswith(f"{PACKAGE_DIR}/benchmarks/"):
        return path.endswith(".py") and not path.endswith(("__init__.py", "registry.py"))
    return False


def registry_parity() -> dict[str, Any]:
    """§4.1 #5: registry against filesystem, from two sources that never call each other.

    The mismatch is the symmetric difference of the *source paths* each side declares, so an entry
    pointing at a moved file and an unregistered runnable unit both become a number that can fail.
    """
    registry = REPO_ROOT / PACKAGE_DIR / "experiments" / "registry.py"
    if not registry.is_file():
        return {
            "applicable": False,
            "why": "python/quantrisk/experiments/registry.py does not exist before Phase 3.1",
            "probe": f"test -f {PACKAGE_DIR}/experiments/registry.py",
        }
    declared = sorted(entry.source for entry in _load_registry().TASKS)
    tracked = sorted(
        path for path in git("ls-files", "--", "*.py").splitlines() if _is_runnable_unit(path)
    )
    return {
        "applicable": True,
        "registry_sources": len(declared),
        "filesystem_units": len(tracked),
        "mismatch": sorted(set(declared) ^ set(tracked)),
        "probe": "uv run python -m tools.inventory_orphan_code (registry_parity)",
    }


def _load_registry() -> Any:
    """Import the registry the way a consumer would.

    Deliberately a package import, not a by-path load: the collector's own census counts by-path
    sites and must not add one while driving that count to zero.
    """
    import importlib

    return importlib.import_module(f"{PACKAGE_IMPORT}.experiments.registry")


def plant_liveness() -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "-m", "quantrisk.verification.runner", "--list"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return {
        "applicable": result.returncode == 0,
        "declared_plants": len(lines),
        "probe": "uv run python -m quantrisk.verification.runner --list",
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
    dead = [row["path"] for row in rows if row["class"] == "not_reachable"]
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
                "name": "runtime_reachability",
                "command": (
                    "importlib.import_module in one child interpreter, plus "
                    "pytest --collect-only over the same corpus"
                ),
                "value": runtime_reachability(dead),
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
                "name": "formatter_census",
                "command": "ruff format --check . differenced against git ls-files",
                "value": formatter_census(),
            },
            {
                "name": "registry_parity",
                "command": "test -f python/quantrisk/experiments/registry.py, then git ls-files",
                "value": registry_parity(),
            },
            {
                "name": "external_dependencies",
                "command": (
                    "tomllib.loads(pyproject.toml) against the declared set in the ceilings file"
                ),
                "value": external_dependencies(),
            },
            {
                "name": "plant_liveness",
                "command": "python python/quantrisk/verification/runner.py --list",
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
    formatter = by_name["formatter_census"]
    parity = by_name["registry_parity"]
    reachability = by_name["runtime_reachability"]
    dependencies = by_name["external_dependencies"]
    return {
        "bootstrap_sites_outside_package": len(by_name["bootstrap_census"]),
        "by_path_load_sites": len(by_name["by_path_load_sites"]),
        "commands_not_module_path": commands["corpus"]
        - commands["classes"].get("module-path-resolves", 0),
        "commands_unrunnable_from_the_root": sum(
            count for kind, count in commands["classes"].items() if kind in unrunnable
        ),
        STATIC_CHECK_KEY: coverage["corpora"]["files_outside_their_declaration"],
        FORMATTER_KEY: len(formatter["walked_but_not_tracked"])
        + len(formatter["tracked_but_not_walked"]),
        "registry_parity_mismatch": None
        if not parity.get("applicable")
        else len(parity["mismatch"]),
        "runtime_reachability_gap": None
        if not reachability.get("available")
        else len(reachability["reached_by_neither"]),
        "plants_not_rejected_by_their_guard": None,
        "installed_user_identity_mismatch": None,
        "external_dependencies_added": len(dependencies["added"]) + len(dependencies["removed"]),
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
        elif isinstance(value, dict) and "reached_by_neither" in value:
            shown = {
                "available": value["available"],
                "ast_dead": len(value["ast_dead"]),
                "import_reachable": len(value["import_reachable"]),
                "pytest_collected": len(value["pytest_collected"]),
                "reached_by_neither": len(value["reached_by_neither"]),
            }
        elif isinstance(value, dict) and "added" in value:
            shown = {
                "measured": len(value["measured"]),
                "declared": len(value["declared"]),
                "added": value["added"],
                "removed": value["removed"],
            }
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
