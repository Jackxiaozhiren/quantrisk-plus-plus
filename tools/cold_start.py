"""H1's scripted cold start: a wheel, a fresh environment, a neutral cwd, one command.

    uv run python -m tools.cold_start --record tools/cold_start_record.json

`INTERFACE_ROADMAP.md` line 143 asks for a scripted run with four properties and a wall clock: a
fresh venv, a neutral cwd, one command from install-listing to artifact, and a run that needs no
repository checkout and no file name known in advance. The repository's own environment can prove
none of them -- it holds the checkout, the editable install and the extras at once -- so this tool
builds a wheel, creates an environment and a working directory outside the tree, and runs exactly
one command there.

Cost is why this is a tool and not a pytest case, as with `tools/verify_installed_surface.py`:
building the wheel and installing `numpy`/`pandas` into a fresh environment takes about a minute,
and a suite that spent it per commit would teach people to skip the suite. The record written here
is read by `quantrisk.interface.coldstart.audit()` and held to its ceiling by a guard.

What is *not* claimed: the benchmark's wall-clock columns. They move with machine load -- two runs
on the same machine disagree on every one of them -- so the reproduction compares only the
deterministic fields and the record says which ones it left alone, rather than letting a reader
assume the whole artifact was matched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from importlib import metadata
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
TASK = "mc_speed"
OUT_DIR = "cold-start-out"
PUBLISHED = Path("benchmarks") / "performance" / "results" / "monte_carlo_speed.json"
SCHEMA = "quantrisk-cold-start/1"

# The fields two runs must agree on, and the ones they cannot. The second tuple is recorded rather
# than omitted: a reader is told what the comparison excluded instead of inferring it.
DETERMINISTIC = (
    "analytic_reference_price",
    "measured_prices",
    "reported_standard_errors",
    "paths_per_run",
    "option",
)
VOLATILE = (
    "results_seconds",
    "speedup_vs_numpy",
    "speedup_vs_pure_python",
    "speedup_vs_pure_python_using_min",
)

IMPORT_PROBE = (
    "import json, quantrisk, sys;"
    "print(json.dumps({'module': quantrisk.__file__, 'prefix': sys.prefix,"
    " 'version': quantrisk.version()}))"
)
TALLY = "registered tasks"


class ColdStartFailed(AssertionError):
    """A property of the scripted run did not hold, with the reading that shows it."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def inside(path: Path, root: Path) -> bool:
    """True when `path` sits under `root` once both are resolved."""
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def call(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)


def build_wheel(uv: str, dist: Path) -> tuple[Path, float]:
    """Build the wheel this run installs, as a stand-in for the distribution a reader downloads."""
    started = time.perf_counter()
    result = call([uv, "build", "--wheel", "--out-dir", str(dist)], REPO_ROOT)
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        raise ColdStartFailed(f"the wheel did not build: {(result.stdout + result.stderr)[-500:]}")
    wheels = sorted(dist.glob("*.whl"))
    if len(wheels) != 1:
        raise ColdStartFailed(f"expected one wheel in {dist}, found {[w.name for w in wheels]}")
    return wheels[0], elapsed


def make_venv(uv: str, root: Path) -> tuple[Path, Path, float]:
    """A fresh environment outside the checkout, on the interpreter the wheel was built for."""
    venv = root / "venv"
    started = time.perf_counter()
    result = call([uv, "venv", "--python", sys.executable, str(venv)], root)
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        raise ColdStartFailed(f"the venv was not created: {(result.stdout + result.stderr)[-500:]}")
    python = venv / "bin" / "python"
    cli = venv / "bin" / "quantrisk"
    if not python.is_file():
        raise ColdStartFailed(f"the venv has no interpreter at {python}")
    return venv, cli, elapsed


def dependency_closure(names: tuple[str, ...]) -> dict[str, Any]:
    """The installed distributions `names` need, read from the build environment's metadata."""
    found: dict[str, Any] = {}
    queue = list(names)
    while queue:
        name = queue.pop()
        key = name.lower()
        if key in found:
            continue
        try:
            distribution = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            continue
        if distribution.metadata["Name"].lower() == "quantrisk":
            continue
        found[key] = distribution
        for requirement in distribution.requires or []:
            queue.append(re.split(r"[\s;\[<>=!~]", requirement, maxsplit=1)[0])
    return found


def seed_dependencies(site_packages: Path) -> dict[str, str]:
    """Copy the runtime dependencies into the fresh environment when the index is unreachable.

    A cold user downloads these; this machine's proxy refuses the package index, so the alternative
    to seeding is not measuring H1 at all. The copied set is the dependency closure of the wheel's
    own declared dependencies, taken from the build environment, and `quantrisk` itself is excluded
    by name: the distribution under test still comes from the wheel and nothing is imported from
    the checkout. The record says so rather than letting a reader assume an index install happened.
    """
    seeded: dict[str, str] = {}
    for distribution in dependency_closure(("numpy", "pandas")).values():
        name = distribution.metadata["Name"]
        for relative in distribution.files or []:
            source = Path(distribution.locate_file(relative))
            if not source.is_file():
                continue
            target = site_packages / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        seeded[name] = distribution.version
    return seeded


def install(uv: str, python: Path, wheel: Path) -> dict[str, Any]:
    """Install the wheel into the fresh environment, falling back to seeding its dependencies."""
    argv = [uv, "pip", "install", "--python", str(python), str(wheel)]
    started = time.perf_counter()
    result = call(argv, wheel.parent)
    if result.returncode == 0:
        return {
            "argv": argv,
            "mode": "index",
            "seeded": {},
            "seed_reason": "",
            "wall_seconds": time.perf_counter() - started,
        }
    failure = (result.stdout + result.stderr).strip().splitlines()
    bare = [uv, "pip", "install", "--no-deps", "--python", str(python), str(wheel)]
    second = call(bare, wheel.parent)
    if second.returncode != 0:
        detail = (second.stdout + second.stderr)[-500:]
        raise ColdStartFailed(f"the wheel did not install, with or without dependencies: {detail}")
    site_packages = Path(
        call(
            [str(python), "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
            wheel.parent,
        )
        .stdout.strip()
        .splitlines()[-1]
    )
    seeded = seed_dependencies(site_packages)
    if not {"numpy", "pandas"} <= set(seeded):
        raise ColdStartFailed(f"the seeded set does not cover the runtime deps: {sorted(seeded)}")
    return {
        "argv": bare,
        "mode": "seeded",
        "seeded": seeded,
        "seed_reason": failure[-1] if failure else "the index install failed",
        "wall_seconds": time.perf_counter() - started,
    }


def identity(python: Path, cwd: Path) -> dict[str, Any]:
    """What the environment's interpreter imported, read from outside the checkout."""
    result = call([str(python), "-c", IMPORT_PROBE], cwd)
    if result.returncode != 0:
        raise ColdStartFailed(f"the installed package does not import: {result.stderr[-400:]}")
    facts: dict[str, Any] = json.loads(result.stdout.strip().splitlines()[-1])
    return facts


def listing(cli: Path, cwd: Path) -> dict[str, Any]:
    """The task id is the one this CLI prints, not a name copied from a document."""
    result = call([str(cli), "run", "--list"], cwd)
    if result.returncode != 0:
        raise ColdStartFailed(f"`run --list` failed: {(result.stdout + result.stderr)[-400:]}")
    tally = next((line for line in result.stdout.splitlines() if TALLY in line), "")
    if TASK not in result.stdout:
        raise ColdStartFailed(f"`run --list` does not print {TASK!r}: {result.stdout[-400:]}")
    return {"tally": tally.strip(), "task_listed": True}


def one_command(cli: Path, cwd: Path) -> dict[str, Any]:
    """Exactly one invocation between "the environment is ready" and "the artifact exists"."""
    before = sorted(path.name for path in cwd.iterdir())
    if before:
        raise ColdStartFailed(f"the neutral cwd was not empty before the run: {before}")
    typed = ["quantrisk", "run", TASK, "--out", OUT_DIR]
    existing = [element for element in typed if (cwd / element).exists()]
    if existing:
        raise ColdStartFailed(f"the command names paths that already exist: {existing}")
    if any(str(REPO_ROOT) in element for element in typed):
        raise ColdStartFailed(f"the command names the checkout: {typed}")
    started = time.perf_counter()
    result = call([str(cli), *typed[1:]], cwd)
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        raise ColdStartFailed(f"the command failed: {(result.stdout + result.stderr)[-600:]}")
    return {
        "argv": typed,
        "cwd": str(cwd),
        "subprocess_invocations": 1,
        "existing_paths_before": existing,
        "wall_seconds": elapsed,
        "exit": result.returncode,
    }


def produced_artifact(cwd: Path) -> Path:
    written = sorted(cwd.rglob("*.json"))
    matching = [path for path in written if path.name == PUBLISHED.name]
    if len(matching) != 1:
        raise ColdStartFailed(f"expected one {PUBLISHED.name} under {cwd}, found {written}")
    return matching[0]


def reproduce(written: Path, base: Path) -> dict[str, Any]:
    """Compare the deterministic fields with the published artifact; refuse on any difference."""
    published = json.loads((base / PUBLISHED).read_text(encoding="utf-8"))
    produced = json.loads(written.read_text(encoding="utf-8"))
    missing = [field for field in DETERMINISTIC if field not in produced]
    if missing:
        raise ColdStartFailed(f"the produced artifact omits {missing}")
    differences = [field for field in DETERMINISTIC if produced[field] != published.get(field)]
    if differences:
        raise ColdStartFailed(
            f"the run did not reproduce the published fields {differences}: "
            f"produced={ {f: produced[f] for f in differences} } "
            f"published={ {f: published.get(f) for f in differences} }"
        )
    return {
        "published_artifact": str(PUBLISHED),
        "fields": list(DETERMINISTIC),
        "produced": {field: produced[field] for field in DETERMINISTIC},
        "equal": True,
        "not_compared": list(VOLATILE),
        "not_compared_because": (
            "wall-clock columns move with machine load; two runs on the same machine disagree on "
            "every one of them, so claiming their equality would be the fabrication this record "
            "exists to prevent"
        ),
    }


def measure(root: Path, keep: bool) -> dict[str, Any]:
    uv = shutil.which("uv")
    if uv is None:
        raise ColdStartFailed("uv is not on PATH; there is no way to build or install the wheel")
    checkout = REPO_ROOT.resolve()
    for named, path in (("run root", root), ("venv", root / "venv"), ("cwd", root / "neutral")):
        if inside(path, checkout):
            raise ColdStartFailed(f"the {named} {path} sits inside the checkout {checkout}")
    wheel, build_seconds = build_wheel(uv, root / "dist")
    venv, cli, venv_seconds = make_venv(uv, root)
    installed = install(uv, venv / "bin" / "python", wheel)
    neutral = root / "neutral"
    neutral.mkdir(parents=True, exist_ok=True)
    facts = identity(venv / "bin" / "python", neutral)
    if not inside(Path(facts["module"]), venv) or inside(Path(facts["module"]), checkout):
        raise ColdStartFailed(f"the import resolved outside the fresh environment: {facts}")
    runtime = call(
        [str(venv / "bin" / "python"), "-c", "import numpy, pandas; print(numpy.__version__)"],
        neutral,
    )
    if runtime.returncode != 0:
        raise ColdStartFailed(f"the runtime dependencies do not import: {runtime.stderr[-400:]}")
    listed = listing(cli, neutral)
    measured = one_command(cli, neutral)
    written = produced_artifact(neutral)
    return {
        "schema": SCHEMA,
        "vantage": (
            "a wheel built from this tree, installed into a fresh environment and run from an "
            "empty working directory, both outside the checkout"
        ),
        "checkout": str(checkout),
        "wheel": {"file": wheel.name, "sha256": sha256(wheel)},
        "environment": {
            "venv_root": str(venv.resolve()),
            "identity": facts,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "build": {"command": "uv build --wheel", "wall_seconds": build_seconds},
        "venv": {"command": "uv venv", "wall_seconds": venv_seconds},
        "install": installed,
        "probe": {"invocations": 2, **listed},
        "run": measured,
        "artifact": {
            "relative_path": str(written.relative_to(neutral)),
            "bytes": written.stat().st_size,
            "sha256": sha256(written),
        },
        "reproduction": reproduce(written, checkout),
        "kept": keep,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--record",
        type=Path,
        default=REPO_ROOT / "tools" / "cold_start_record.json",
        help="where the reading is written",
    )
    parser.add_argument(
        "--work-root",
        type=Path,
        default=None,
        help="parent for the throwaway tree; defaults to the system temp directory",
    )
    parser.add_argument("--keep", action="store_true", help="leave the environment behind")
    arguments = parser.parse_args(argv)
    root = Path(tempfile.mkdtemp(prefix="quantrisk-cold-start-", dir=arguments.work_root))
    try:
        record = measure(root, arguments.keep)
        revision = call(["git", "rev-parse", "HEAD"], REPO_ROOT).stdout.strip()
        record["revision"] = revision
        arguments.record.parent.mkdir(parents=True, exist_ok=True)
        arguments.record.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(
            f"cold start: one command, {record['run']['wall_seconds']:.1f}s, "
            f"{record['reproduction']['fields']} reproduced from {PUBLISHED}"
        )
    finally:
        if not arguments.keep and root.name.startswith("quantrisk-cold-start-"):
            shutil.rmtree(root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
