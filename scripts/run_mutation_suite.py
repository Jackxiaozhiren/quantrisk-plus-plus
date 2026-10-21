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

``--pairing-audit`` answers the question the stop cannot: not "did the named guard reject this",
which the sweep already proves, but "is the guard that rejected it the one the plant names". It runs
the named guard's whole module instead of one node, so it sees every guard that objected, and it
requires **membership** of the named guard in that set. It does not require the set to be a
singleton, because the shipped instrument measured 43 of the 71 plants it could observe on `b2df36f`
redden more than the one guard they name -- all of them honest plants, and an equality test would
refuse them. The cost is one module run per distinct guard, so this is a per-phase instrument, not a
CI lane, and it must never run while a sweep is in flight: both write to tracked files.

Usage::

    uv run python scripts/run_mutation_suite.py --list
    uv run python scripts/run_mutation_suite.py --kind prose --verbose
    uv run python scripts/run_mutation_suite.py --only volga-uses-its-own-square
    uv run python scripts/run_mutation_suite.py --all
    uv run python scripts/run_mutation_suite.py --pairing-audit
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import os
import re
import signal
import subprocess
import sys
import tempfile
from collections.abc import Collection, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

from quantrisk.verification.plants import MUTATIONS, Mutation

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUILD_DIR = "build/dev"
TEST_BINARY_TARGET = "quantrisk_tests"

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

PAIRED = "paired"
MIS_PAIRED = "named-guard-stayed-green"
ESCAPED = "no-guard-objected"
MODULE_NOT_RUN = "module-could-not-be-run"


# The plant list arrives by package import from `quantrisk.verification.plants`, which is a separate
# module from this interpreter on purpose: finding 94 records that a plant anchoring on a line of
# the file holding the list finds that line twice, so the case is refused before it runs.


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

    def module_failures(self, target: str) -> tuple[bool, set[str], list[tuple[str, int, str]]]:
        """``(ran, failing test names, per-assertion lines)`` for a whole-module run.

        The return code decides whether the module ran at all: 0 is "everything passed" and 1 is
        "some tests failed", while 2, 3, 4 and 5 are collection, internal, usage and
        no-tests-collected errors. Folding those into an empty failing set would report a broken run
        as a plant that escaped every guard, which is the confusion this instrument exists to
        remove.

        `--tb=line` is what makes the third value worth having: one line per failure, carrying the
        file and line of the assertion that raised, with the message whole. The short summary clips
        that message to the terminal width, and slicing traceback sections by header width is how
        finding 91 happened.
        """
        completed = _run(
            (
                "uv",
                "run",
                "--frozen",
                "pytest",
                target,
                "-q",
                "--tb=line",
                "-p",
                "no:cacheprovider",
            ),
            self.verbose,
            self.next_environment(),
        )
        ran = completed.returncode in (0, 1)
        return ran, parse_failures(completed.stdout), parse_line_tracebacks(completed.stdout)

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


@contextmanager
def restore_on_signal(snapshots: dict[Path, bytes], probes: Sequence[Path]) -> Iterator[None]:
    """Put every planted byte back if the run is interrupted, then give the handlers back.

    Both instruments write to tracked files, and the second half of finding 25 is a sweep that died
    part-way and left a mutated source in the tree. The handler has to cover *every* target the run
    intends to touch, so the caller hands in the whole snapshot map rather than the file in flight.
    """

    def on_signal(signum: int, _frame: object) -> None:
        for path, payload in snapshots.items():
            path.write_bytes(payload)
        for probe in probes:
            probe.unlink(missing_ok=True)
            parent = probe.parent
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
        raise SystemExit(128 + signum)

    numbers = (signal.SIGINT, signal.SIGTERM)
    previous = {number: signal.signal(number, on_signal) for number in numbers}
    try:
        yield
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


def tree_of(selected: Sequence[Mutation]) -> tuple[dict[Path, bytes], list[Path]]:
    """What each plant overwrites, and what each `tree` plant creates, for the restore handlers."""
    snapshots = {
        (REPO_ROOT / mutation.path).resolve(): (REPO_ROOT / mutation.path).read_bytes()
        for mutation in selected
        if mutation.kind != "tree"
    }
    probes = [REPO_ROOT / mutation.path for mutation in selected if mutation.kind == "tree"]
    return snapshots, probes


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


def parse_failures(output: str) -> set[str]:
    """The test names pytest printed as FAILED, stripped of their file prefix. Pure."""
    return {
        match.group(1).split("::")[-1]
        for match in re.finditer(r"^FAILED (\S+)", output, flags=re.M)
    }


def audit_verdict(*, ran: bool, failing: Collection[str], named: str) -> str:
    """Whether the guard a plant names is among the guards that actually objected.

    Membership, never equality. #103 prescribed "require that exactly the named one objects", and
    the registry as shipped says that criterion is the wrong one: measured over the plants this
    shape observed on `b2df36f`, 43 of 71 reddened more than the single guard they name, and each
    was an honest plant reading a structure several guards share. What the audit is for is finding
    86's defect -- a hand-typed `guard` field pointing at a reader that stays green while somebody
    else takes the blame -- and a set without the name reports exactly that, whatever its size. A
    run that collected nothing is its own verdict, because an empty set then means "nobody looked",
    not "nothing objected".
    """
    if not ran:
        return MODULE_NOT_RUN
    if named in failing:
        return PAIRED
    return MIS_PAIRED if failing else ESCAPED


ATTRIBUTED = "attributed"
UNATTRIBUTED = "no text link to the mutation"

#: Words that look like identifiers in a prose anchor and mean nothing as a text link.
PROSE_TOKENS = frozenset(
    {
        "and",
        "the",
        "for",
        "not",
        "with",
        "that",
        "this",
        "from",
        "def",
        "return",
        "None",
        "True",
        "False",
        "when",
        "then",
        "than",
        "into",
        "over",
        "its",
        "are",
        "was",
        "were",
        "has",
        "have",
        "but",
        "because",
        "which",
        "while",
        "does",
    }
)
TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
CLOSURE_DEPTH = 8
#: The plants whose named guard has no text link to what they edit, and why. This is the audit's
#: residual, named the way `pairing_sample` names the guards it cannot observe. #107 asks whether
#: the guard rejected *about* the mutated line, and text answers only when the guard spells the
#: mutated name somewhere in what it reads. A plant that leaves this list without a change here,
#: or a new plant that belongs on it, reddens the pairing guard.
UNATTRIBUTED_PLANTS = frozenset({"release-note-cites-a-digest-its-file-does-not-carry"})


def anchor_tokens(anchor: str) -> set[str]:
    """Identifier-shaped tokens of a plant's anchor, prose stopwords removed. Pure."""
    return {token for token in TOKEN_PATTERN.findall(anchor) if token not in PROSE_TOKENS}


def parse_line_tracebacks(output: str) -> list[tuple[str, int, str]]:
    """Every `(file, line, message)` pytest printed under `--tb=line`. Pure.

    One line per failure, keyed by the location of the assertion that raised -- a boundary the
    transcript states rather than one the reader assumes. Finding 91 is what the alternative costs:
    slicing by section header breaks the moment pytest pads a long test name to two underscores, and
    the neighbour's message then reads as the plant's own.
    """
    found = []
    for match in re.finditer(r"^(.+?):(\d+): ((?:\w+Error|Exception): .*)$", output, flags=re.M):
        found.append((match.group(1), int(match.group(2)), match.group(3)))
    return found


def guard_span(source: str, name: str) -> tuple[int, int] | None:
    """The line span of a test function in `source`, or None when it is not defined at top level."""
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node.lineno, (node.end_lineno or node.lineno)
    return None


def reading_closure(source: str, name: str, depth: int = CLOSURE_DEPTH) -> str:
    """The guard's own text plus every same-file binding it reaches, transitively.

    Nested definitions count: the closure that mattered in measurement was reached only through a
    helper defined inside the guard, and a walk that indexes top-level names alone loses the chain
    at that boundary -- which is the same shape #103's static half blamed reachability for, but here
    widening only adds coverage rather than crying wolf.
    """
    tree = ast.parse(source)
    members: dict[str, ast.AST] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            members.setdefault(node.name, node)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    members.setdefault(target.id, node)
    included: list[str] = []
    seen: set[str] = set()
    queue: list[tuple[str, int]] = [(name, 0)]
    while queue:
        current, level = queue.pop(0)
        if current in seen or current not in members:
            continue
        seen.add(current)
        node = members[current]
        included.append(ast.get_source_segment(source, node) or "")
        if level >= depth:
            continue
        for reference in ast.walk(node):
            if isinstance(reference, ast.Name) and reference.id in members:
                queue.append((reference.id, level + 1))
            elif isinstance(reference, ast.Attribute) and reference.attr in members:
                queue.append((reference.attr, level + 1))
    return "\n".join(included)


def attribution(*, closure: str, path: str, tokens: set[str]) -> str:
    """Whether the guard's reading closure names the file or the symbols this plant edited.

    Text, not causality: it says the guard could see the thing that changed. #107's residue is that
    a guard can also reject for a reason the mutation merely coincides with, and no text rule
    settles that -- the one plant on this head that has no link is a digest string no guard spells
    out.
    """
    if path in closure or Path(path).name in closure:
        return ATTRIBUTED
    if any(token in closure for token in tokens):
        return ATTRIBUTED
    return UNATTRIBUTED


def _audit_blocker(mutation: Mutation) -> str | None:
    """Why a whole-module pytest cannot observe this plant, or None when it can."""
    if mutation.kind == "core":
        return "its guard is a CTest case, not a pytest node"
    if mutation.kind == "tree":
        return "its target is a probe file the plant creates"
    if "::" not in mutation.guard:
        return "its guard names no file::test pair"
    return None


def pairing_sample(
    mutations: Sequence[Mutation],
) -> tuple[list[Mutation], list[tuple[str, str]]]:
    """One plant per distinct guard, plus every guard no plant of this shape can observe and why.

    Two families are out of reach: a ``core`` plant's guard is a CTest case, so there is no pytest
    module whose failures could be read, and a ``tree`` plant's target does not exist until the
    plant writes it, so there is nothing to restore and re-read. They are returned as a named list
    rather than dropped, because an audit whose denominator quietly excludes a family reports a
    coverage it does not have -- the same silence #103 was written about.

    The choice is by guard, and a guard shared between plants is decided by the plants it has:
    taking the first plant in registry order would hand an observable guard to the unreachable list
    on the strength of one probe plant, so the first plant this shape can actually run represents
    it.
    """
    chosen: dict[str, Mutation] = {}
    blocked: dict[str, str] = {}
    order: list[str] = []
    for mutation in mutations:
        guard = mutation.guard
        if guard not in order:
            order.append(guard)
        reason = _audit_blocker(mutation)
        if reason is None:
            chosen.setdefault(guard, mutation)
        else:
            blocked.setdefault(guard, reason)
    sample = [chosen[guard] for guard in order if guard in chosen]
    unreachable = [(guard, blocked[guard]) for guard in order if guard not in chosen]
    return sample, unreachable


def audit_counts(
    records: Sequence[dict[str, object]], unreachable: Sequence[tuple[str, str]]
) -> dict[str, int]:
    """The audit's numbers, each against the denominator that can honestly carry it.

    The first version of this instrument printed `0 of 72` while five of its 72 samples never ran,
    and the difference between 67 and 72 is the difference between a measurement and a guess. So
    every figure here is derived from the records that were observed, and `declared` is checked
    against the sample plus the unreachable list rather than asserted from a count of the registry.
    """
    observed = [r for r in records if r["verdict"] in (PAIRED, MIS_PAIRED, ESCAPED)]
    paired = [r for r in observed if r["verdict"] == PAIRED]
    return {
        "declared": len(records) + len(unreachable),
        "sampled": len(records),
        "observed": len(observed),
        "paired": len(paired),
        "singleton": sum(1 for record in paired if record["size"] == 1),
        "mis-paired": sum(1 for r in observed if r["verdict"] == MIS_PAIRED),
        "escaped": sum(1 for r in observed if r["verdict"] == ESCAPED),
        "not-run": len(records) - len(observed),
        "unreachable": len(unreachable),
        "attributed": sum(1 for r in observed if r["attribution"] == ATTRIBUTED),
        "unattributed": sum(1 for r in observed if r["attribution"] == UNATTRIBUTED),
    }


def run_pairing_audit(mutation: Mutation, harness: Harness) -> dict[str, object]:
    """Read every guard in the named guard's module while this plant's defect sits in the tree."""
    path = REPO_ROOT / mutation.path
    before = path.read_bytes()
    digest = hashlib.sha256(before).hexdigest()
    target = mutation.guard.partition("::")[0]
    named = mutation.guard.partition("::")[-1]
    pristine = before.decode("utf-8")
    mutated, reason = apply_mutation(pristine, mutation.anchor, mutation.replacement)
    verdict = ANCHOR_NOT_UNIQUE if reason else None
    ran = False
    failing: set[str] = set()
    tracebacks: list[tuple[str, int, str]] = []
    restored = False
    if reason is None:
        try:
            path.write_text(mutated, encoding="utf-8")
            if path.read_bytes() == before:
                verdict = NO_OP
            else:
                ran, failing, tracebacks = harness.module_failures(target)
                verdict = audit_verdict(ran=ran, failing=failing, named=named)
        finally:
            path.write_bytes(before)
            restored = hashlib.sha256(path.read_bytes()).hexdigest() == digest
        if not restored:
            verdict = NOT_RESTORED
    # Two texts, on purpose. A traceback's line numbers index the file pytest just compiled, so the
    # span that picks the named guard's own assertion comes out of the mutated text. The closure
    # answers a different question -- does this guard read the symbol the plant attacks -- and that
    # is a property of the program as written: a plant whose edit deletes the very reference the
    # closure follows would otherwise erase the evidence of its own pairing, which is how
    # `claim-modifier-slot-reopened-after-the-census` read unlinkable on `6ddc965` while the offline
    # pin read it as linked.
    same_module = target == mutation.path
    closure_source = pristine if same_module else (REPO_ROOT / target).read_text(encoding="utf-8")
    span_source = mutated if same_module else closure_source
    site = failing_assertion(tracebacks, module=target, name=named, source=span_source)
    return {
        "id": mutation.identifier,
        "kind": mutation.kind,
        "verdict": verdict,
        "size": len(failing),
        "others": sorted(failing - {named}),
        "guard": mutation.guard,
        "claim": mutation.claim,
        "assert_line": site[0] if site else None,
        "assert_message": site[1] if site else "",
        "attribution": attribution(
            closure=reading_closure(closure_source, named),
            path=mutation.path,
            tokens=anchor_tokens(mutation.anchor),
        ),
    }


def failing_assertion(
    tracebacks: Sequence[tuple[str, int, str]], *, module: str, name: str, source: str
) -> tuple[int, str] | None:
    """The assertion the named guard itself raised: `(line, message)`, or None when nothing matched.

    Attributed by location rather than by slicing the transcript at a header, so a long test name
    cannot move the boundary (finding 91). None is a real answer, not a failure: the guard can
    reject through an error raised outside any of its assert statements.
    """
    span = guard_span(source, name)
    if span is None:
        return None
    for file_, line, message in tracebacks:
        if Path(file_).name == Path(module).name and span[0] <= line <= span[1]:
            return line, message
    return None


def audit_census(counts: dict[str, int]) -> str:
    """One line a phase record can quote, with each ratio naming the denominator it divides."""
    observed = counts["observed"]
    unreachable = counts["unreachable"]
    return (
        f"{counts['paired']}/{observed} observed had their named guard in the failing set, "
        f"{counts['singleton']}/{observed} had it alone; "
        f"{counts['mis-paired']} mis-paired, {counts['escaped']} escaped, "
        f"{counts['not-run']} unrunnable, {unreachable} guards unreachable; "
        f"{counts['attributed']}/{observed} attributed by text to the line they moved, "
        f"{counts['unattributed']} named as unlinkable; "
        f"{counts['declared']} declared = {counts['sampled']} sampled + {unreachable} named"
    )


def run_pairing_mode(selected: Sequence[Mutation], harness: Harness) -> int:
    """The audit loop: one module run per distinct guard, and a census with honest denominators.

    Cost is the reason this is not a CI lane. Every observed plant is a whole-module pytest, so the
    run is bounded by the number of distinct guards rather than by the number of plants, and it
    writes to tracked files exactly as the sweep does -- which is why the same clean-at-`HEAD`
    preflight gates it and why the two must never be in flight together.
    """
    sample, unreachable = pairing_sample(selected)
    print(
        f"{len(selected)} plants selected, {len(sample) + len(unreachable)} distinct guards behind "
        f"them: {len(sample)} observable by a module run, {len(unreachable)} not.\n"
    )
    for guard, reason in unreachable:
        print(f"{'unsampled':<22} {guard[:72]:<74} {reason}")

    records: list[dict[str, object]] = []
    snapshots, probes = tree_of(sample)
    with restore_on_signal(snapshots, probes):
        for mutation in sample:
            print(f"- {mutation.identifier} ({mutation.kind}) ...", flush=True)
            records.append(run_pairing_audit(mutation, harness))
            record = records[-1]
            print(f"    {str(record['verdict']):<22} failing={record['size']}", flush=True)

    counts = audit_counts(records, unreachable)
    width = max((len(str(record["id"])) for record in records), default=0)
    print()
    for record in records:
        marker = "ok  " if record["verdict"] == PAIRED else "FAIL"
        extra = ""
        if record["verdict"] == PAIRED and record["size"] != 1:
            joined = ", ".join(str(name) for name in record["others"])
            extra = f"  also reddened: {joined}"
        print(f"{marker} {str(record['verdict']):<22} {str(record['id']):<{width}}{extra}")
    residual = sorted(
        str(record["id"])
        for record in records
        if record["attribution"] == UNATTRIBUTED and record["verdict"] == PAIRED
    )
    if residual:
        print(
            f"\n{UNATTRIBUTED}: {', '.join(residual)} -- the reading closure names neither"
            " the edited path nor a token from the anchor"
        )
    unexpected = set(residual) ^ set(UNATTRIBUTED_PLANTS)
    gained = sorted(set(residual) - set(UNATTRIBUTED_PLANTS))
    lost = sorted(set(UNATTRIBUTED_PLANTS) - set(residual))
    if unexpected:
        print(f"unlinkable set moved: new {gained}, gone {lost}")
        print(
            "a plant that loses its text link is a pairing the audit cannot vouch for, and one "
            "that gains a link should leave this list"
        )
    print(f"\n{audit_census(counts)}")
    left = [path for path in snapshots if git_status(str(path.relative_to(REPO_ROOT)))]
    if left:
        names = ", ".join(sorted(str(path.relative_to(REPO_ROOT)) for path in left))
        print(f"{NOT_RESTORED}: {len(left)} target(s) still differ from HEAD: {names}")
        return 1
    clean = counts["mis-paired"] + counts["escaped"] + counts["not-run"]
    return 0 if clean == 0 and not unexpected else 1


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
    parser.add_argument(
        "--pairing-audit",
        action="store_true",
        help="#103's dynamic audit: run each guard's whole module under one mutation and require "
        "that the named guard objects with the others. One module run per distinct guard.",
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

    if arguments.pairing_audit:
        return run_pairing_mode(selected, harness)

    results: list[dict[str, str]] = []
    snapshots, probes = tree_of(selected)
    stopped_at: str | None = None
    with restore_on_signal(snapshots, probes):
        for mutation in selected:
            print(f"- {mutation.identifier} ({mutation.kind}) ...", flush=True)
            results.append(run_one(mutation, harness))
            print(f"    {results[-1]['status']}", flush=True)
            if not arguments.all and results[-1]["status"] != CAUGHT:
                stopped_at = mutation.identifier
                break

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
    print(f"\n{len(caught)}/{len(selected)} planted defects were rejected by their guard.")
    if left:
        names = ", ".join(sorted(str(path.relative_to(REPO_ROOT)) for path in left))
        print(f"{NOT_RESTORED}: {len(left)} target(s) still differ from HEAD: {names}")
        return 1
    return 0 if len(caught) == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
