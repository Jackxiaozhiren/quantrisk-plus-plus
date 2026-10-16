r"""Plant a known defect, and require a guard to reject it.

Every test that checks prose against an artifact can go green for two different reasons: the
claim is right, or the check never looked at anything. Finding 25 in `docs/integrity_audit.md`
records the second case happening twice — a mutation sweep that printed `NEEDLE NOT FOUND` for
two of nine cases and still reported "nine mutations caught", and a sweep that died part-way and
left a mutated source file in the tree. This file is the answer: the falsification is a repo tool,
its list of mutations is policed by the ordinary test suite
(`tests/python/test_mutation_suite.py`), and each case proves four things in order —

1. the anchor occurred exactly once, so the edit landed on the text it names;
2. the file bytes actually changed, so the control was not a no-op;
3. the named guard went **red** on the mutated tree, so it can detect this defect;
4. the bytes restored to the recorded SHA-256, and the same guard went **green** again.

Failing any step yields that step's status, never ``caught``.

Three kinds of mutation. ``prose`` edits a file a documented claim lives in and runs one pytest
node;
nothing is rebuilt. That includes `bindings/python_bindings.cpp`, whose parity guard compares the
*source* against the already installed extension, so a declaration the binary cannot serve is caught
without a compile. ``core`` edits a closed form in the C++ library, rebuilds only the Catch2/CTest
target, and requires the named CTest case to fail. It deliberately does not rebuild the Python
extension, so a ``core`` case proves the C++ gate rejects the wrong formula; the Python-visible
consequences of a wrong formula are the province of the reproduction guards and the parity check.
``tree`` exists for the guards whose defect is *absence*: it creates one probe file at a path
preflighted to be free, requires the guard to reject its existence, and removes it again. That kind
never overwrites anything, and refuses the case outright if the path is already occupied.

Refuses to start if any file it would edit is not clean at `HEAD`: the harness must never overwrite
work in progress, and finding 25's second half is what happens when two writers share one tree.

A plant whose guard never objects stops the run: `sweep-stopped-early` names the plant and counts
the declared plants it never ran. Finding 86 measured what the alternative costs -- the registry's
`guard` field is hand-typed, a mis-named reader produces no output of its own, and a census that
only reports at the end turns one bad line into a full sweep before anyone reads it.
``--all`` restores the census for the records that quote it.

Usage::

    uv run python scripts/run_mutation_suite.py --list
    uv run python scripts/run_mutation_suite.py --kind prose --verbose
    uv run python scripts/run_mutation_suite.py --only volga-uses-its-own-square
    uv run python scripts/run_mutation_suite.py --all

"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import re
import signal
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUILD_DIR = "build/dev"
TEST_BINARY_TARGET = "quantrisk_tests"
PLANTS_PATH = Path(__file__).resolve().with_name("mutation_plants.py")

CAUGHT = "caught"
ANCHOR_NOT_UNIQUE = "anchor-not-unique"
NO_OP = "mutation-was-a-no-op"
BUILD_FAILED = "mutation-did-not-compile"
GUARD_NOT_RUN = "guard-could-not-be-run"
ESCAPED = "guard-stayed-green"
NOT_RESTORED = "restore-mismatch"
NOT_GREEN_AGAIN = "tree-did-not-recover"
DIRTY_TARGET = "target-already-modified"
PROBE_EXISTS = "probe-file-already-in-the-tree"
STOPPED = "sweep-stopped-early"


def _load_plants() -> tuple[type, tuple[Mutation, ...]]:
    """Read the list from the module holding it, by path, since `scripts/` is not a package.

    The list cannot live in this file: a plant anchors on a line here, and its own entry is a second
    copy of that line, so the count is always two and the case is refused before it runs (#94).
    """
    spec = importlib.util.spec_from_file_location("mutation_plants", PLANTS_PATH)
    assert spec and spec.loader, f"the plant list is missing from {PLANTS_PATH}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.Mutation, tuple(module.MUTATIONS)


Mutation, MUTATIONS = _load_plants()


def apply_mutation(text: str, anchor: str, replacement: str) -> tuple[str, str | None]:
    """The mutated text and, when it cannot be produced safely, why not. Pure, so it is testable.

    A missing or repeated anchor is refused rather than guessed at: the failure finding 25 recorded
    was an edit that silently applied to nothing and was then counted as a caught defect.
    """
    occurrences = text.count(anchor)
    if occurrences != 1:
        return text, f"anchor occurs {occurrences} times, expected exactly once"
    mutated = text.replace(anchor, replacement)
    if mutated == text:
        return text, "replacement is identical to the anchor"
    return mutated, None


def decide(
    *,
    anchor_ok: bool,
    probe_free: bool = True,
    changed: bool,
    build_ok: bool,
    guard_ran: bool,
    guard_returncode: int,
    restored: bool,
    green_again: bool,
) -> str:
    """Which step of the proof failed, if any. A catch requires all of them to hold, in order."""
    if not anchor_ok:
        return ANCHOR_NOT_UNIQUE
    if not probe_free:
        return PROBE_EXISTS
    if not changed:
        return NO_OP
    if not build_ok:
        return BUILD_FAILED
    if not guard_ran:
        return GUARD_NOT_RUN
    if guard_returncode == 0:
        return ESCAPED
    if not restored:
        return NOT_RESTORED
    if not green_again:
        return NOT_GREEN_AGAIN
    return CAUGHT


# The environment variable CPython reads its bytecode-cache location from. Named once so the
# guard that polices it and the code that sets it cannot drift apart.
BYTECODE_PREFIX = "PYTHONPYCACHEPREFIX"


def isolation_environment(cache_dir: Path) -> dict[str, str]:
    """An environment whose bytecode cache cannot be shared with the repository.

    A prose plant that edits a Python file without changing its length -- `32.6` to `99.9` -- leaves
    the source size identical, and a restore inside the same clock second leaves the integer mtime
    CPython keys its cache on identical too. The mutated module's `.pyc` is then still "valid" for
    the restored file, so the step that re-runs the guard after the tree went clean again reads the
    defect back out of `__pycache__` and reports a clean tree as unrestored. Phase 33 met that as a
    false `tree-did-not-recover` on its own new plant, and the prefix has to be fresh per
    *invocation* for that pair of runs -- a plant's mutated step and its restored step are two
    invocations of one sweep, which is exactly the window the defect lives in. See
    `Harness.next_environment`.
    """
    environment = os.environ.copy()
    environment[BYTECODE_PREFIX] = str(cache_dir)
    return environment


def _run(
    command: Sequence[str], verbose: bool, environment: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(command),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    if verbose:
        tail = (completed.stdout + completed.stderr).strip().splitlines()[-2:]
        print("      " + " / ".join(tail), flush=True)
    return completed


class Harness:
    """Subprocess plumbing for one environment: the uv runner, the cmake build, the guards."""

    def __init__(self, build_dir: str, verbose: bool = False) -> None:
        self.build_dir = build_dir
        self.verbose = verbose
        self.cache_root = Path(tempfile.mkdtemp(prefix="quantrisk-mutation-pycache-"))
        self._invocation = 0

    def next_environment(self) -> dict[str, str]:
        """The environment for one subprocess, with a bytecode prefix nothing has written to.

        Counted per invocation rather than allocated once per sweep, because the failure finding 66
        records happens between a plant's mutated run and its restored re-run.
        """
        self._invocation += 1
        return isolation_environment(self.cache_root / f"invocation-{self._invocation}")

    def uv(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return _run(("uv", "run", "--frozen", *arguments), self.verbose, self.next_environment())

    def build(self) -> bool:
        built = self.uv("cmake", "--build", self.build_dir, "--target", TEST_BINARY_TARGET)
        return built.returncode == 0

    def ctest(self, name: str) -> int:
        """The CTest return code for one case, or -1 when the name is not exactly one test.

        `-R` matching nothing exits non-zero, which would read as a caught defect; the `-N`
        listing is what distinguishes "the guard rejected the mutation" from "the guard never
        ran".
        """
        listed = self.uv("ctest", "--test-dir", self.build_dir, "-N", "-R", name)
        if len(re.findall(r"^\s*Test +#(\d+)", listed.stdout, flags=re.M)) != 1:
            return -1
        return self.uv("ctest", "--test-dir", self.build_dir, "-R", name).returncode

    def pytest(self, node: str) -> int:
        return self.uv("pytest", node, "-q", "-p", "no:cacheprovider").returncode

    def guard(self, mutation: Mutation) -> tuple[bool, int]:
        """``(ran, returncode)`` for the guard alone; the build is the caller's to time."""
        if mutation.kind == "core":
            code = self.ctest(mutation.guard)
            return code != -1, code
        return True, self.pytest(mutation.guard)

    def check_exists(self, mutation: Mutation) -> str | None:
        """Why this mutation's guard could not be invoked at all, or None if it can."""
        if mutation.kind != "core":
            file_, _, name = mutation.guard.partition("::")
            source = REPO_ROOT / file_
            if not source.is_file():
                return f"{file_} is not in the tree"
            if f"def {name}" not in source.read_text(encoding="utf-8"):
                return f"{file_} does not define {name!r}"
            return None
        listed = self.uv("ctest", "--test-dir", self.build_dir, "-N", "-R", mutation.guard)
        found = re.findall(r"^\s*Test +#(\d+)", listed.stdout, flags=re.M)
        if len(found) != 1:
            return f"{mutation.guard!r} resolves to {len(found)} CTest cases, expected 1"
        return None


def git_status(path: str) -> str:
    return _run(("git", "status", "--porcelain", "--", path), False).stdout.strip()


def run_one_probe(mutation: Mutation, harness: Harness) -> dict[str, str]:
    """Plant *absence* rather than a wrong value: create one probe file, then take it away.

    The four steps are the same ones the other kinds run, re-expressed for a guard that fires on
    a file nobody registered: the path must be free before the case (nothing is overwritten), the
    probe must really exist before the guard runs, the guard must reject its existence, and the
    case is only complete when the probe is gone and the same guard passes again.
    """
    path = REPO_ROOT / mutation.path
    probe_free = not path.exists()
    changed = False
    guard_ran = False
    guard_returncode = 0
    restored = False
    green_again = False
    reason = None if probe_free else f"{mutation.path} already exists, so the probe would overwrite"
    if probe_free:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(mutation.replacement, encoding="utf-8")
            changed = path.is_file()
            guard_ran, guard_returncode = harness.guard(mutation)
        finally:
            path.unlink(missing_ok=True)
            parent = path.parent
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
            restored = not path.exists()
        if restored and guard_returncode != 0:
            _, code = harness.guard(mutation)
            green_again = code == 0
    return {
        "id": mutation.identifier,
        "kind": mutation.kind,
        "status": decide(
            anchor_ok=True,
            probe_free=probe_free,
            changed=changed,
            build_ok=True,
            guard_ran=guard_ran,
            guard_returncode=guard_returncode,
            restored=restored,
            green_again=green_again,
        ),
        "reason": reason or "",
        "guard": mutation.guard,
        "claim": mutation.claim,
    }


def run_one(mutation: Mutation, harness: Harness) -> dict[str, str]:
    """One full falsification cycle for a single mutation, reported as a record."""
    if mutation.kind == "tree":
        return run_one_probe(mutation, harness)
    path = REPO_ROOT / mutation.path
    before = path.read_bytes()
    digest = hashlib.sha256(before).hexdigest()
    mutated, reason = apply_mutation(before.decode("utf-8"), mutation.anchor, mutation.replacement)
    anchor_ok = reason is None
    changed = False
    build_ok = True
    guard_ran = False
    guard_returncode = 0
    restored = False
    green_again = False
    if anchor_ok:
        try:
            path.write_text(mutated, encoding="utf-8")
            changed = path.read_bytes() != before
            if changed:
                if mutation.kind == "core":
                    build_ok = harness.build()
                guard_ran, guard_returncode = harness.guard(mutation)
        finally:
            path.write_bytes(before)
            restored = hashlib.sha256(path.read_bytes()).hexdigest() == digest
        if restored and guard_returncode != 0:
            if mutation.kind == "core":
                green_again = harness.build() and harness.ctest(mutation.guard) == 0
            else:
                green_again = harness.pytest(mutation.guard) == 0
    return {
        "id": mutation.identifier,
        "kind": mutation.kind,
        "status": decide(
            anchor_ok=anchor_ok,
            changed=changed,
            build_ok=build_ok,
            guard_ran=guard_ran,
            guard_returncode=guard_returncode,
            restored=restored,
            green_again=green_again,
        ),
        "reason": reason or "",
        "guard": mutation.guard,
        "claim": mutation.claim,
    }


def kinds_of(mutations: Sequence[Mutation]) -> set[str]:
    """Every kind the list declares, so `--kind` cannot drift behind the mutations."""
    return {mutation.kind for mutation in mutations}


def select(kind: str | None, only: Sequence[str]) -> list[Mutation]:
    chosen = [mutation for mutation in MUTATIONS if kind is None or mutation.kind == kind]
    if not only:
        return chosen
    wanted = set(only)
    return [mutation for mutation in chosen if mutation.identifier in wanted]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Require every guard to reject a planted defect.")
    parser.add_argument("--list", action="store_true", help="print the mutations and exit")
    parser.add_argument("--only", action="append", default=[], help="run just these mutation ids")
    parser.add_argument(
        "--kind", choices=tuple(sorted(kinds_of(MUTATIONS))), help="run just one kind"
    )
    parser.add_argument("--build-dir", default=DEFAULT_BUILD_DIR, help="cmake build directory")
    parser.add_argument(
        "--all",
        action="store_true",
        help="keep going after a plant escapes its guard, for the full census",
    )
    parser.add_argument("--verbose", action="store_true", help="echo each guard's own tail")
    arguments = parser.parse_args(argv)

    selected = select(arguments.kind, arguments.only)
    unknown = set(arguments.only).difference(mutation.identifier for mutation in MUTATIONS)
    if unknown:
        print(f"unknown mutation ids: {', '.join(sorted(unknown))}", file=sys.stderr)
        return 2
    if arguments.list:
        for mutation in selected:
            print(f"{mutation.identifier}\t{mutation.kind}\t{mutation.guard}")
        return 0

    dirty = [mutation.path for mutation in selected if git_status(mutation.path)]
    if dirty:
        print(
            f"{DIRTY_TARGET}: these mutation targets differ from HEAD -> "
            + ", ".join(sorted(set(dirty))),
            file=sys.stderr,
        )
        return 2

    harness = Harness(arguments.build_dir, arguments.verbose)
    unavailable = [(mutation, harness.check_exists(mutation)) for mutation in selected]
    broken = [(mutation, reason) for mutation, reason in unavailable if reason]
    if broken:
        for mutation, reason in broken:
            print(f"{GUARD_NOT_RUN:<22} {mutation.identifier}: {reason}", file=sys.stderr)
        return 2

    results: list[dict[str, str]] = []
    snapshots = {
        (REPO_ROOT / mutation.path).resolve(): (REPO_ROOT / mutation.path).read_bytes()
        for mutation in selected
        if mutation.kind != "tree"
    }
    probes = [REPO_ROOT / mutation.path for mutation in selected if mutation.kind == "tree"]

    def on_signal(signum: int, _frame: object) -> None:
        for path, payload in snapshots.items():
            path.write_bytes(payload)
        for probe in probes:
            probe.unlink(missing_ok=True)
            parent = probe.parent
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
        raise SystemExit(128 + signum)

    for number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(number, on_signal)
    stopped_at: str | None = None
    try:
        for mutation in selected:
            print(f"- {mutation.identifier} ({mutation.kind}) ...", flush=True)
            results.append(run_one(mutation, harness))
            print(f"    {results[-1]['status']}", flush=True)
            if not arguments.all and results[-1]["status"] != CAUGHT:
                stopped_at = mutation.identifier
                break
    finally:
        for number in (signal.SIGINT, signal.SIGTERM):
            signal.signal(
                number, signal.default_int_handler if number == signal.SIGINT else signal.SIG_DFL
            )

    width = max((len(result["id"]) for result in results), default=0)
    print()
    for result in results:
        marker = "ok  " if result["status"] == CAUGHT else "FAIL"
        print(f"{marker} {result['status']:<22} {result['id']:<{width}}  {result['claim']}")
    if stopped_at is not None:
        skipped = len(selected) - len(results)
        print(
            f"\n{STOPPED}: {skipped} of {len(selected)} declared plants were never run, after "
            f"{stopped_at}. Pass --all for the full census."
        )
    caught = [result for result in results if result["status"] == CAUGHT]
    left = [path for path in snapshots if git_status(str(path.relative_to(REPO_ROOT)))]
    print(f"\n{len(caught)}/{len(results)} planted defects were rejected by their guard.")
    if left:
        names = ", ".join(sorted(str(path.relative_to(REPO_ROOT)) for path in left))
        print(f"{NOT_RESTORED}: {len(left)} target(s) still differ from HEAD: {names}")
        return 1
    return 0 if len(caught) == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
