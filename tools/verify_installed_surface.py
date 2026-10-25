"""The installed-user proof: what a wheel gives a reader who never clones the repository.

    uv run python -m tools.verify_installed_surface \\
        --python /path/to/clean/venv/bin/python --work /path/to/empty/directory

REFACTOR_PROMPT.md §11 item 1 asks four questions that only an installed surface can answer: does
the imported package resolve inside the environment it was installed into (L8), does
`quantrisk run --list` enumerate every registered task from there, does one offline study run end
to end and write into the root the caller named, and does a task that needs something the wheel
does not carry refuse loudly instead of publishing something else. The repository's own environment
cannot answer any of them: it holds the checkout, the extras and the editable install at once,
which is precisely the state a released wheel does not reproduce.

Cost is why this is a tool and not a pytest case. Building a wheel, creating an environment and
running a study takes minutes, and a suite that spends them per commit teaches people to skip the
suite. The reading is recorded in `REFACTOR_LEDGER.md` beside the ceiling it discharges
(`installed_user_identity_mismatch`), and `--self-test` proves the instrument can fail by aiming it
at the checkout's own environment, where the identity assertion is false by construction.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from quantrisk.experiments.registry import TASKS

REPO_ROOT = Path(__file__).resolve().parents[1]
IMPORT_PROBE = (
    "import json, quantrisk, sys;"
    "print(json.dumps({'module': quantrisk.__file__, 'prefix': sys.prefix,"
    " 'version': quantrisk.version()}))"
)
TALLY_LINE = re.compile(r"^(\d+) registered tasks")
NAMES_WHAT_IS_MISSING = re.compile(
    r"No module named '[^']+|no fixture corpus at |not a QuantRisk\+\+ checkout"
)


class ProofFailed(AssertionError):
    """A part of the installed surface did not hold, with the reading that shows it."""


def run(binary: Path, cwd: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(binary), *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def installed_identity(python: Path, cwd: Path) -> dict[str, str]:
    """What the environment's interpreter actually imported, run from outside the checkout."""
    result = run(python, cwd, "-c", IMPORT_PROBE)
    if result.returncode != 0:
        raise ProofFailed(f"the installed package does not import: {result.stderr[-400:]}")
    return json.loads(result.stdout.strip().splitlines()[-1])


def assert_identity(python: Path, venv_root: Path, cwd: Path) -> dict[str, Any]:
    """L8: the import resolves inside the environment, and the checkout is nowhere in it.

    Both halves matter. A `sys.prefix` inside the venv whose module path lands in the checkout is
    what an editable install looks like from outside, and that is the failure this probe exists to
    catch: the code under test would then be the working tree, not the artifact that shipped.
    """
    facts = installed_identity(python, cwd)
    module = Path(facts["module"]).resolve()
    prefix = Path(facts["prefix"]).resolve()
    root = venv_root.resolve()
    checkout = REPO_ROOT.resolve()
    failures = []
    if not str(module).startswith(f"{root}/"):
        failures.append(f"{module} resolves outside the environment root {root}")
    if prefix != root:
        failures.append(f"sys.prefix is {prefix}, not the environment root {root}")
    if str(module).startswith(f"{checkout}/") or str(prefix).startswith(f"{checkout}/"):
        failures.append(f"the checkout {checkout} appears in the resolved import path")
    manifest = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = manifest["project"]["version"]
    if facts["version"] != declared:
        failures.append(
            f"the installed package reports {facts['version']} while the manifest says {declared}"
        )
    if failures:
        raise ProofFailed("identity: " + "; ".join(failures))
    return {"module": str(module), "prefix": str(prefix), "version": facts["version"]}


def registry_ids() -> list[str]:
    """The task ids the registry holds, read from the source of truth rather than from a copy."""
    return sorted(task.task_id for task in TASKS)


def assert_list(cli: Path, work: Path) -> dict[str, Any]:
    """The installed CLI lists exactly the registry's tasks, both ways, from a neutral cwd."""
    result = run(cli, work, "run", "--list")
    if result.returncode != 0:
        raise ProofFailed(
            f"`run --list` failed in the installed environment: {result.stderr[-300:]}"
        )
    listed = sorted(
        line.split()[0]
        for line in result.stdout.splitlines()
        if line.startswith("  ") and not line.startswith("   ") and line.split()
    )
    wanted = registry_ids()
    extra = sorted(set(listed) - set(wanted))
    absent = sorted(set(wanted) - set(listed))
    if listed != wanted:
        raise ProofFailed(
            f"the installed list is not the registry: only-listed={extra} missing={absent}"
        )
    tally = next(
        (m.group(1) for line in result.stdout.splitlines() if (m := TALLY_LINE.match(line))), None
    )
    if tally != str(len(wanted)):
        raise ProofFailed(
            f"the list's own tally says {tally} while the registry holds {len(wanted)}"
        )
    return {"tasks": len(wanted), "tally": tally}


def assert_validate(cli: Path, work: Path) -> dict[str, Any]:
    """The shipped identities hold against the installed binary, not against a source tree."""
    result = run(cli, work, "validate")
    passed = result.stdout.count("PASS ")
    if result.returncode != 0 or passed == 0:
        raise ProofFailed(f"`validate` did not pass installed: {result.stdout[-300:]}")
    return {"passed": passed, "exit": result.returncode}


def assert_study(cli: Path, work: Path, study: str) -> dict[str, Any]:
    """One registered study runs end to end and lands where the caller pointed it.

    The artifact is looked for under the out root, never in the repository: writing beside the
    checkout would prove something else, and the registry's frozen relative path is what ties the
    two readings together.
    """
    out = work / "study-out"
    result = run(cli, work, "run", study, "--out", str(out))
    if result.returncode != 0:
        raise ProofFailed(
            f"study {study!r} failed from the installed wheel: {result.stdout[-500:]}"
        )
    written = sorted(path.name for path in out.rglob("*.json"))
    if not written:
        raise ProofFailed(f"study {study!r} reported success and wrote no JSON under {out}")
    return {"study": study, "artifacts": written, "exit": result.returncode}


def assert_refusal_names_what_is_missing(cli: Path, work: Path, task: str) -> dict[str, Any]:
    """A task the wheel cannot serve refuses by naming the absent thing, and publishes nothing.

    V2-11's rule generalised: the acceptable failure says which module, which corpus or which
    committed artifact is missing. The unacceptable one is a study that runs and publishes numbers
    anyway, which is what a synthesised fixture would look like from here.

    Files and directories are counted apart, because they mean different things and the measured
    reading showed both: the study resolves its output paths before it reads its data, so a refusal
    leaves the directory tree behind and no payload. An empty tree is residue -- the shape
    `docs/integrity_audit.md` 62(e) already records for the sweep's probe directories -- while a
    file under the out root would be a claim the failed run never earned.
    """
    out = work / f"refuse-{task}"
    result = run(cli, work, "run", task, "--out", str(out))
    printed = result.stdout + result.stderr
    if result.returncode == 0:
        raise ProofFailed(
            f"{task} succeeded from a bare wheel, so the refusal this phase added is not firing"
        )
    if not NAMES_WHAT_IS_MISSING.search(printed):
        raise ProofFailed(f"{task} failed without naming what it needed: {printed[-400:]}")
    published = sorted(str(path.relative_to(out)) for path in out.rglob("*") if path.is_file())
    if published:
        raise ProofFailed(f"{task} refused and still published {published} under {out}")
    residue = sum(1 for path in out.rglob("*") if path.is_dir())
    return {
        "task": task,
        "exit": result.returncode,
        "named": True,
        "empty_directories_left": residue,
    }


def self_test(python: Path) -> int:
    """Prove the identity assertion can fail, by pointing it at an environment that must fail it.

    The checkout's own interpreter resolves the package inside the repository, so `assert_identity`
    has to refuse it. A probe that accepted that reading would also accept an editable install
    wearing a wheel's clothes, which is the defect this tool exists to find.
    """
    try:
        assert_identity(python, venv_root=REPO_ROOT / ".venv", cwd=REPO_ROOT)
    except ProofFailed as expected:
        print(f"self-test: the identity check refused the checkout environment -- {expected}")
        return 0
    raise ProofFailed("self-test: the identity check accepted an import inside the checkout")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--python", type=Path, help="interpreter of the clean environment")
    parser.add_argument(
        "--venv",
        type=Path,
        default=None,
        help="environment root; defaults to the interpreter's grandparent, unsymlinked",
    )
    parser.add_argument("--work", type=Path, help="empty working directory outside the checkout")
    parser.add_argument("--study", default="linearisation_error_bound")
    parser.add_argument("--refusal", default="real_data_risk_study")
    parser.add_argument(
        "--self-test", action="store_true", help="prove the identity check can fail"
    )
    arguments = parser.parse_args(argv)
    if arguments.self_test:
        return self_test(Path(sys.executable))
    if arguments.python is None or arguments.work is None:
        parser.error("--python and --work are both required (or run --self-test)")
    # A `uv venv` interpreter is a symlink to the base Python, so resolving it would name the frame
    # rather than the environment; the grandparent of the un-resolved path is the venv itself.
    cli = arguments.python.parent / "quantrisk"
    venv_root = (arguments.venv or arguments.python.parent.parent).resolve()
    work = arguments.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    readings: dict[str, Any] = {
        "identity": assert_identity(arguments.python, venv_root, work),
        "list": assert_list(cli, work),
        "validate": assert_validate(cli, work),
        "study": assert_study(cli, work, arguments.study),
        "refusal": assert_refusal_names_what_is_missing(cli, work, arguments.refusal),
    }
    print(json.dumps(readings, indent=2, sort_keys=True))
    print(
        "installed surface: identity holds, the list is the registry, one study ran, and the "
        "refusal named what it needed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
