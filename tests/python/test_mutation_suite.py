"""`scripts/run_mutation_suite.py` needs a gate of its own, because its failure mode is silence.

Finding 25 in `docs/integrity_audit.md` is why this file exists: two of nine mutations in a
hand-rolled sweep never applied — clang-format had reflowed the expression between the time the
needle was read and the time the patch ran — and the sweep still reported "nine mutations caught".
A harness that plants defects can therefore fail in the worst available way: it prints success while
changing nothing. Running the harness cannot be part of the ordinary gate — it edits tracked files
and recompiles the core — so what lives here is the half that can be: the mutation list is
re-validated on every test run, and the decision function that turns a cycle into a status is
exercised against every way a cycle can lie.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_PATH = REPO_ROOT / "scripts" / "run_mutation_suite.py"

# `scripts/` is not a package, so the harness is loaded the way `test_artifact_metadata.py`
# loads the suite runner: by file location, which keeps the tool a tool rather than turning
# it into a module the library imports.
_spec = importlib.util.spec_from_file_location("run_mutation_suite", HARNESS_PATH)
assert _spec and _spec.loader
harness = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = harness
_spec.loader.exec_module(harness)

ALL_CPP_TESTS = "\n".join(
    path.read_text(encoding="utf-8") for path in (REPO_ROOT / "tests" / "cpp").glob("*.cpp")
)


def test_the_plant_list_lives_where_a_plant_can_reach_the_harness() -> None:
    """#94's fix is a file boundary, and a boundary is one refactor away from being undone.

    While the list and the interpreter shared `scripts/run_mutation_suite.py`, a plant naming a line
    of that file found the line twice -- once in the code and once in its own entry -- so the sweep
    refused the case and the bytecode-isolation guard could only be shown red by hand, which CI
    never re-runs. The split is what makes that plant legal, so this asserts three things: the list
    is defined in the data module, no part of it has crept back into the interpreter, and every
    plant that points at the interpreter has one anchor there and no more.
    """
    plants_path = REPO_ROOT / "python" / "quantrisk" / "verification" / "plants.py"
    assert plants_path.is_file(), "the plant list has no module to live in"
    plants_source = plants_path.read_text(encoding="utf-8")
    harness_source = HARNESS_PATH.read_text(encoding="utf-8")
    definition = "MUTATIONS: tuple[Mutation, ...] = ("
    assert definition in plants_source, "the data module no longer defines the list"
    assert definition not in harness_source, (
        "a plant list has reappeared in the interpreter, which is the duplication #94 records: any "
        "plant naming a line of that file would find it twice"
    )
    assert harness.MUTATIONS and all(
        type(item) is harness.Mutation for item in harness.MUTATIONS
    ), "the harness reads a different Mutation type than the list defines"

    pointed = [item for item in harness.MUTATIONS if item.path == "scripts/run_mutation_suite.py"]
    assert pointed, "no plant can reach the interpreter, so #94's split is unprotected"
    harness_source_occurrences = {
        item.identifier: harness_source.count(item.anchor) for item in pointed
    }
    assert all(count == 1 for count in harness_source_occurrences.values()), (
        f"plants whose anchor is not unique in the interpreter: {harness_source_occurrences}; "
        "the sweep would refuse those cases before running them"
    )
    assert all(item.replacement != item.anchor for item in pointed), (
        "a plant would edit a line of the interpreter into itself"
    )


def test_every_declared_mutation_names_one_unique_anchor_and_a_guard_that_exists() -> None:
    """The list may not rot: a stale anchor or a renamed guard would make the harness report a lie.

    This is the check that would have caught finding 25 before a sweep did — not by running the
    mutations, which is slow and destructive, but by asserting on every ordinary test run that
    each anchor still occurs exactly once in the file it names, and that the guard expected to
    reject it is still defined there.
    """
    identifiers = [mutation.identifier for mutation in harness.MUTATIONS]
    assert len(set(identifiers)) == len(identifiers), f"duplicate mutation ids: {identifiers}"
    kinds = [mutation.kind for mutation in harness.MUTATIONS]
    assert set(kinds) == {"prose", "core", "tree"}, set(kinds)
    assert kinds.count("core") >= 3 and kinds.count("prose") >= 5 and kinds.count("tree") >= 1

    for mutation in harness.MUTATIONS:
        assert not Path(mutation.path).is_absolute(), mutation.identifier
        assert ".." not in Path(mutation.path).parts, mutation.identifier
        target = REPO_ROOT / mutation.path
        if mutation.kind == "tree":
            # A probe already in the tree would be overwritten by the sweep, and a probe left behind
            # by an interrupted run is the same fault in the other direction: this assertion is what
            # notices either, because no other test reads that path.
            assert not target.exists(), (
                f"{mutation.identifier}: {mutation.path} exists, so the sweep would overwrite it"
            )
            continue
        assert target.is_file(), f"{mutation.identifier}: {mutation.path} is not in the tree"
        text = target.read_text(encoding="utf-8")
        assert text.count(mutation.anchor) == 1, (
            f"{mutation.identifier}: its anchor occurs {text.count(mutation.anchor)} times in "
            f"{mutation.path}, so the edit would be a guess — the finding 25 failure mode"
        )
        mutated, reason = harness.apply_mutation(text, mutation.anchor, mutation.replacement)
        assert reason is None and mutated != text, f"{mutation.identifier}: {reason}"

        if mutation.kind == "core":
            assert f'TEST_CASE("{mutation.guard}")' in ALL_CPP_TESTS, (
                f"{mutation.identifier}: no C++ TEST_CASE is named {mutation.guard!r}"
            )
        else:
            file_, _, name = mutation.guard.partition("::")
            source = REPO_ROOT / file_
            assert source.is_file(), f"{mutation.identifier}: {file_} is not in the tree"
            assert f"def {name}" in source.read_text(encoding="utf-8"), (
                f"{mutation.identifier}: {file_} does not define {name!r}"
            )


def test_every_documented_figure_guard_in_that_file_has_a_declared_defect() -> None:
    """The sweep must cover the guards, not merely the defects I happened to think of.

    `tests/python/test_artifact_metadata.py` and the Phase 15 producer-docstring guard are the files
    whose entire purpose is comparing a prose figure against its owner, so every count- or
    agreement-shaped guard in them has to appear as some mutation's guard. Without this, adding a
    documented-number guard would leave the sweep silently one short -- the same "absence produces
    no output" failure the registry guard exists to catch, one level up.
    """
    doc_guards = set()
    for file_ in ("test_artifact_metadata.py", "test_restrike_gamma_map.py"):
        source = (REPO_ROOT / "tests" / "python" / file_).read_text(encoding="utf-8")
        doc_guards |= {
            f"tests/python/{file_}::{name}"
            for name in re.findall(r"^def (test_\w*(?:count|agree)\w*)", source, flags=re.M)
        }
    assert len(doc_guards) >= 8, sorted(doc_guards)
    named = {mutation.guard for mutation in harness.MUTATIONS}
    uncovered = sorted(doc_guards - named)
    assert not uncovered, f"documented-figure guards with no declared defect: {uncovered}"


def test_a_control_that_would_not_apply_is_reported_rather_than_counted() -> None:
    """Missing, ambiguous and identity anchors all refuse to produce a mutation."""
    text = "alpha beta alpha"

    mutated, reason = harness.apply_mutation(text, "gamma", "delta")
    assert mutated == text
    assert reason == "anchor occurs 0 times, expected exactly once"

    mutated, reason = harness.apply_mutation(text, "alpha", "delta")
    assert mutated == text
    assert reason == "anchor occurs 2 times, expected exactly once"

    mutated, reason = harness.apply_mutation(text, "beta", "beta")
    assert mutated == text
    assert reason == "replacement is identical to the anchor"

    mutated, reason = harness.apply_mutation(text, "beta", "gamma")
    assert mutated == "alpha gamma alpha" and reason is None

    # A cycle whose edit did not land can never be tallied as a catch, however red the guard runs.
    assert (
        harness.decide(
            anchor_ok=False,
            changed=False,
            build_ok=True,
            guard_ran=True,
            guard_returncode=1,
            restored=True,
            green_again=True,
        )
        == harness.ANCHOR_NOT_UNIQUE
    )


def _synthetic_plants(count: int = 3) -> tuple[object, ...]:
    """Plants that name real files and real guards but are never applied.

    The CLI is exercised against these instead of the declared list because the behaviour under test
    is the loop's, not any plant's: a fake `run_one` decides the statuses, so the only thing read
    from disk is the snapshot the harness takes before the cycle.
    """
    guard = (
        "tests/python/test_mutation_suite.py::"
        "test_the_status_table_only_calls_a_case_caught_when_every_step_fired"
    )
    return tuple(
        harness.Mutation(
            identifier=f"synthetic-{number}",
            kind="prose",
            path="python/quantrisk/verification/plants.py",
            anchor="MUTATIONS: tuple[Mutation, ...] = (",
            replacement="MUTATIONS: tuple[Mutation, ...] = (  #",
            guard=guard,
            claim=f"synthetic plant {number}",
        )
        for number in range(count)
    )


def _run_with_statuses(
    monkeypatch: pytest.MonkeyPatch, arguments: list[str], statuses: list[str]
) -> tuple[int, int]:
    """`main`'s exit code and how many cycles it ran, with the cycle itself replaced."""
    plants = _synthetic_plants(len(statuses))
    calls: list[str] = []

    def fake_run_one(mutation: object, _harness: object) -> dict[str, str]:
        calls.append(mutation.identifier)  # type: ignore[attr-defined]
        status = statuses[len(calls) - 1]
        return {
            "id": mutation.identifier,  # type: ignore[attr-defined]
            "kind": mutation.kind,  # type: ignore[attr-defined]
            "status": status,
            "reason": "",
            "guard": mutation.guard,  # type: ignore[attr-defined]
            "claim": mutation.claim,  # type: ignore[attr-defined]
        }

    monkeypatch.setattr(harness, "MUTATIONS", plants)
    monkeypatch.setattr(harness, "run_one", fake_run_one)
    monkeypatch.setattr(harness, "git_status", lambda _path: "")
    code = harness.main(arguments)
    return code, len(calls)


def test_an_escaped_defect_stops_the_sweep_and_names_what_it_never_ran(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The first plant a guard does not reject ends the run, and says how much was skipped.

    Finding 86 is the reason: a mis-pointed plant reports `guard-stayed-green`, and before this
    behaviour the run carried on through the whole list and printed its verdict at the end, so the
    cost of naming the wrong reader was a full sweep and the discovery was a line in the middle of a
    log nobody re-read. Stopping at the first non-caught status is the sound half of that fix; the
    static half -- proving from the registry that a named guard reads the line it mutates --
    measured seven false alarms out of ten test-file plants and is #103's residual, not this gate's
    claim.
    """
    code, ran = _run_with_statuses(
        monkeypatch, [], [harness.CAUGHT, harness.ESCAPED, harness.CAUGHT]
    )
    assert ran == 2, f"the sweep ran {ran} cycles, so an escaped defect does not stop it"
    assert code == 1, "a sweep that stopped on an escaped defect still reported success"
    output = capsys.readouterr().out
    assert harness.STOPPED in output, output
    assert "synthetic-1" in output, f"the stop did not name the plant: {output}"
    assert "1 of 3" in output, f"the stop did not count what it skipped: {output}"
    # The census line takes the same denominator, because the demo of this behaviour in the terminal
    # read `0/1 planted defects were rejected` over a declared list of two -- the run-so-far count
    # wearing the declared count's clothes, which is the mistake #103's plant marks one line above.
    assert "1/3 planted defects were rejected" in output, (
        f"the census counted what ran rather than what was declared: {output}"
    )


def test_the_all_flag_runs_every_declared_plant_after_a_stop_would_fire(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The census is still available, because a phase record quotes the full list.

    Two assertions so the flag cannot be decorative: the same statuses run to the end, and the stop
    line -- which is what tells a reader the census was truncated -- is absent.
    """
    code, ran = _run_with_statuses(
        monkeypatch,
        ["--all"],
        [harness.CAUGHT, harness.ESCAPED, harness.CAUGHT],
    )
    assert ran == 3, f"--all still stopped after {ran} cycles"
    assert code == 1, "a census with an escaped defect in it must not report success"
    output = capsys.readouterr().out
    assert harness.STOPPED not in output, output
    assert "2/3 planted defects were rejected" in output, output


def test_a_sweep_that_needs_no_stop_prints_the_census_it_always_printed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Fail-fast changes the behaviour only when something escapes.

    Without this, the stop branch could be tested and the ordinary path left unproven, and the
    default invocation is the one a phase record quotes: it has to run all three and print no stop
    line, or `105/105` would no longer mean the whole list.
    """
    code, ran = _run_with_statuses(monkeypatch, [], [harness.CAUGHT] * 3)
    assert ran == 3, f"a clean sweep stopped after {ran} cycles"
    assert code == 0, "a clean sweep reported failure"
    output = capsys.readouterr().out
    assert harness.STOPPED not in output, output
    assert "3/3 planted defects were rejected by their guard." in output, output


def test_the_status_table_only_calls_a_case_caught_when_every_step_fired() -> None:
    """Each lie has its own status, and only the complete chain is a catch."""
    cycle = {
        "anchor_ok": True,
        "changed": True,
        "build_ok": True,
        "guard_ran": True,
        "guard_returncode": 1,
        "restored": True,
        "green_again": True,
    }
    assert harness.decide(**cycle) == harness.CAUGHT
    assert harness.decide(**{**cycle, "probe_free": False}) == harness.PROBE_EXISTS
    assert harness.decide(**{**cycle, "changed": False}) == harness.NO_OP
    assert harness.decide(**{**cycle, "build_ok": False}) == harness.BUILD_FAILED
    assert harness.decide(**{**cycle, "guard_ran": False}) == harness.GUARD_NOT_RUN
    assert harness.decide(**{**cycle, "guard_returncode": 0}) == harness.ESCAPED
    assert harness.decide(**{**cycle, "restored": False}) == harness.NOT_RESTORED
    assert harness.decide(**{**cycle, "green_again": False}) == harness.NOT_GREEN_AGAIN
    # The branches are ordered by step, so an early failure is named rather than masked by a later
    # symptom: a no-op edit is reported as a no-op even though its guard then stayed green, and a
    # restore mismatch is reported as that even though the tree then failed to recover.
    assert harness.decide(**{**cycle, "changed": False, "guard_returncode": 0}) == harness.NO_OP
    assert (
        harness.decide(**{**cycle, "restored": False, "green_again": False}) == harness.NOT_RESTORED
    )


def test_the_selected_mutations_resolve_by_kind_and_identifier(capsys) -> None:
    """`--only` and `--kind` are how an operator runs one case, so they must resolve exactly.

    The CLI is asserted rather than assumed because it drifted once for real: adding the `tree`
    kind left argparse's `choices` listing only the two older kinds, so the new mutation was
    unreachable by name while every function around it handled it correctly. Deriving the choices
    from the declared list fixed it, and this is the check that keeps it fixed.
    """
    for mutation in harness.MUTATIONS:
        chosen = harness.select(None, [mutation.identifier])
        assert [item.identifier for item in chosen] == [mutation.identifier]
    prose = harness.select("prose", [])
    core = harness.select("core", [])
    tree = harness.select("tree", [])
    assert len(prose) + len(core) + len(tree) == len(harness.MUTATIONS)
    assert all(item.kind == "prose" for item in prose)
    assert all(item.kind == "core" for item in core)
    assert all(item.kind == "tree" for item in tree)
    assert harness.select("core", [prose[0].identifier]) == []
    assert harness.kinds_of(harness.MUTATIONS) == {"prose", "core", "tree"}
    for kind in ("prose", "core", "tree"):
        assert harness.main(["--list", "--kind", kind]) == 0
        listed = capsys.readouterr().out.strip().splitlines()
        assert len(listed) == len(harness.select(kind, [])), (kind, listed)


def test_a_command_line_that_counts_plants_counts_the_declared_ones() -> None:
    """The bash blocks are living prose, and one of them still said 18/18 when the list held 34.

    `docs/integrity_audit.md` finding 49 named this shape for the C++ totals -- a command annotated
    with `# 201 C++ tests` inside a block the prose guard was already reading, invisible to it
    because the guard matched a different phrase. The sweep's plant count is the same trap: the
    dated records quote the verdict their own run printed and must keep it, while a command comment
    is an instruction, and an instruction that names a superseded count teaches the reader that the
    harness is smaller than it is.

    Scoped to the annotation rather than the file, because the sentences around it are history.
    """
    declared = len(harness.MUTATIONS)
    pattern = re.compile(r"#\s*(\d+)/(\d+) planted defects")
    checked = 0
    for name in (
        "README.md",
        "docs/interview_defense.md",
        "docs/reproducibility.md",
        "paper/technical_report.tex",
    ):
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        for numerator, denominator in pattern.findall(text):
            assert int(numerator) == declared and int(denominator) == declared, (
                f"{name} annotates the sweep as {numerator}/{denominator} "
                f"while the harness declares {declared}"
            )
            checked += 1
    assert checked, "no command line annotates the plant count, so this guard checks nothing"


def test_a_restored_plant_cannot_be_read_back_from_a_stale_bytecode_cache(
    tmp_path: Path,
) -> None:
    """Phase 33 produced a false verdict this way, and the control below reproduces it.

    A prose plant edits a file and the sweep restores it. When the edit does not change the file's
    length -- `32.6` to `99.9` is the case that happened -- and the restore lands in the same whole
    second as the mutation, CPython's cache key (source mtime in seconds, source size) still matches
    the `.pyc` written while the defect was in place. The guard then re-runs against clean bytes on
    disk and reports the *restored* tree as still failing, which is how a sound plant came back as
    `tree-did-not-recover` and the sweep printed 60/61 over a clean `git status`.

    Two assertions, in the order that matters. The control first: without isolation the stale cache
    is genuinely read, so a test that skipped this step could pass while proving nothing. Then the
    harness's own environment -- and specifically that *consecutive* invocations cannot share one,
    because a plant's mutated run and its restored re-run are two invocations of the same sweep,
    which is the window finding 66 measured.

    A third assertion pins the control's premise rather than inheriting it: the first run must have
    written its bytecode beside the module, because that is the file the control reads. An exported
    prefix silently moved it elsewhere, and the control then failed three lines later blaming the
    fixture for the caller's variable.
    """
    module = tmp_path / "policed_module.py"
    module.write_text("VALUE = 32.6\n", encoding="utf-8")
    read = ["-c", "import policed_module; print(policed_module.VALUE)"]

    # Both runs must look for the cache in the same place, so the prefix is absent from both.
    unisolated = {key: value for key, value in os.environ.items() if key != harness.BYTECODE_PREFIX}

    first = subprocess.run(
        [sys.executable, *read],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        env=unisolated,
    )
    assert first.stdout.strip() == "32.6", first.stdout
    assert any((tmp_path / "__pycache__").glob("policed_module*.pyc")), (
        "the first run wrote no bytecode beside the module, so the control below has no stale "
        "cache to read and this test cannot reproduce the defect"
    )

    stamp = int(module.stat().st_mtime)
    size = module.stat().st_size
    module.write_text("VALUE = 99.9\n", encoding="utf-8")
    os.utime(module, (stamp, stamp))
    assert module.stat().st_size == size and int(module.stat().st_mtime) == stamp, (
        "the plant's edit and restore no longer look identical to a cache key, so the "
        "control below would prove nothing"
    )

    shared = subprocess.run(
        [sys.executable, *read],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        env=unisolated,
    )
    assert shared.stdout.strip() == "32.6", (
        "the stale cache was not read, so this test no longer reproduces the defect and the "
        "isolation it polices is untested"
    )

    isolated = subprocess.run(
        [sys.executable, *read],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        env=harness.isolation_environment(tmp_path / "one-invocation"),
    )
    assert isolated.stdout.strip() == "99.9", (
        "the harness's environment still reads another invocation's bytecode, so a "
        "same-length plant can be reported as an unrestored tree"
    )

    sweep = harness.Harness(build_dir="build/dev")
    first = sweep.next_environment()["PYTHONPYCACHEPREFIX"]
    second = sweep.next_environment()["PYTHONPYCACHEPREFIX"]
    assert first != second, (
        "two guard invocations of one sweep share a bytecode prefix, which is the window the "
        "mutated run and the restored re-run both sit in"
    )


def test_every_subprocess_the_harness_runs_a_guard_in_is_bytecode_isolated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The isolation has to be a property of the plumbing, not of one hand-written call.

    `docs/limitations.md` #93 says the cache defect is the interpreter's, not this harness's, and
    that is true of the mechanism. It is not an excuse: the harness reaches the interpreter through
    exactly one function, so *every* guard step can be required to carry a fresh prefix. Phase 33's
    in-test control proved the environment builder works; this proves nothing bypasses it, which is
    the half a control cannot cover -- a later edit that passes `None` instead would keep that
    control green.
    """
    seen: list[dict[str, str] | None] = []

    def spy(command: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(kwargs.get("env"))
        return subprocess.CompletedProcess(list(command or []), 0, "", "")

    monkeypatch.setattr(harness.subprocess, "run", spy)
    swept = harness.Harness(build_dir="build/dev")
    for node in ("tests/python/a.py::test_one", "tests/python/b.py::test_two"):
        assert swept.pytest(node) == 0

    assert len(seen) == 2, "the guard steps did not both reach the one subprocess function"
    prefixes = []
    for environment in seen:
        assert environment, "a guard subprocess was spawned with no environment at all"
        prefix = environment.get(harness.BYTECODE_PREFIX)
        assert prefix, "a guard subprocess runs without bytecode isolation"
        prefixes.append(str(prefix))
    assert len(set(prefixes)) == len(prefixes), (
        f"two guard steps share {prefixes[0]}, which is the window the mutated run and its "
        "restored re-run both sit in"
    )


def test_the_pairing_audit_reads_membership_of_the_failing_set() -> None:
    """#103 prescribes "exactly the named one objects"; the registry says that is wrong.

    The shipped audit over `b2df36f` found 71 observable of 76 distinct guards, and 43 of those
    71 reddened more than the one guard they name: a plant that edits a module-level structure
    is read by every guard that consumes it, and all of them are honest plants. What the audit is
    for is finding 86's shape -- the guard a plant names stays green while a neighbour takes the
    blame -- so the criterion is membership, a wide set is a pass, and a set without the name is
    not.
    """
    singleton = harness.audit_verdict(ran=True, failing={"alpha"}, named="alpha")
    wide = harness.audit_verdict(ran=True, failing={"alpha", "beta", "gamma"}, named="alpha")
    assert singleton == wide == harness.PAIRED, (
        f"the audit answers {singleton!r} alone and {wide!r} with neighbours, so it has become the "
        "equality test #103 proposed and would refuse the plants that share a structure"
    )
    assert harness.audit_verdict(ran=True, failing={"beta"}, named="alpha") == harness.MIS_PAIRED, (
        "a set that never contains the named guard is the defect this instrument exists to find"
    )
    assert harness.audit_verdict(ran=True, failing=set(), named="alpha") == harness.ESCAPED
    assert (
        harness.audit_verdict(ran=False, failing=set(), named="alpha") == harness.MODULE_NOT_RUN
    ), "a module that never ran is not evidence about any guard"

    read = harness.parse_failures(
        "FAILED tests/python/a.py::test_alpha - AssertionError: x\n"
        "FAILED tests/python/b.py::test_beta\n"
        "2 failed, 40 passed in 61.20s\n"
    )
    assert read == {"test_alpha", "test_beta"}, (
        f"the reader returns {sorted(read)}; membership is tested against bare names, so a node "
        "id or a dropped line makes every plant look mis-paired"
    )


def test_the_pairing_audit_samples_one_plant_per_guard_and_names_the_rest() -> None:
    """The sample has to cover the registry, and what it cannot observe has to be named.

    Both halves are load-bearing. One plant per distinct guard is what bounds the cost -- one module
    run per guard rather than per plant -- and the unreachable list is what stops that bound from
    becoming a silent exclusion, which is the silence #103 was written about: a CTest guard has no
    pytest module to read, and a probe plant's target does not exist until the plant writes it.
    """
    sample, unreachable = harness.pairing_sample(harness.MUTATIONS)
    guards = [mutation.guard for mutation in sample]
    assert len(guards) == len(set(guards)), "one guard is sampled twice, so it is counted twice"

    declared = {mutation.guard for mutation in harness.MUTATIONS}
    covered = set(guards) | {guard for guard, _ in unreachable}
    assert covered == declared, (
        f"the audit never sees {sorted(declared - covered)}: a guard with no observed plant and "
        "no named reason"
    )
    expected_unreachable = declared - {
        mutation.guard
        for mutation in harness.MUTATIONS
        if mutation.kind not in ("core", "tree") and "::" in mutation.guard
    }
    assert {guard for guard, _ in unreachable} == expected_unreachable, (
        "the unreachable list no longer matches the guards this shape cannot run, so either a "
        "runnable guard was dropped or an unrunnable one was counted as observed"
    )
    assert not (set(guards) & expected_unreachable), (
        "a guard is both sampled and named as unreachable"
    )

    for mutation in sample:
        file_, _, name = mutation.guard.partition("::")
        source = REPO_ROOT / file_
        assert source.is_file(), f"{mutation.identifier} samples a guard in a missing file"
        assert f"def {name}" in source.read_text(encoding="utf-8"), (
            f"{mutation.identifier} samples {name!r}, which {file_} does not define"
        )


def test_the_pairing_audit_samples_a_shared_guard_from_a_plant_that_can_run() -> None:
    """A guard named by several plants is decided by what can run, not by who was registered first.

    The shipped registry happens to put a runnable plant first for every shared guard today, so a
    sampler that decided by registry order would pass a census over the real list for the wrong
    reason -- and the day a probe plant is added first, an observable guard silently moves to the
    unreachable list and the audit reports fewer guards than it was given. The premise is forced
    here rather than inherited from the list, because an absence in the current data is not a
    mechanism.
    """
    guard = "tests/python/x.py::test_shared_between_plants"
    probe = harness.Mutation(
        identifier="synthetic-probe-plant",
        kind="tree",
        path="experiments/_mutation_probe/run.py",
        anchor="absent",
        replacement="x = 1\n",
        guard=guard,
        claim="unused by the sampler",
    )
    runnable = harness.Mutation(
        identifier="synthetic-runnable-plant",
        kind="prose",
        path="scripts/run_mutation_suite.py",
        anchor="absent",
        replacement="x = 2\n",
        guard=guard,
        claim="unused by the sampler",
    )
    for order in ([probe, runnable], [runnable, probe]):
        sample, unreachable = harness.pairing_sample(order)
        names = [mutation.identifier for mutation in sample]
        assert names == ["synthetic-runnable-plant"], (
            f"{[m.kind for m in order]} samples {names}, so the guard's fate turned on registry "
            "order rather than on whether a module run can observe it"
        )
        assert unreachable == [], (
            f"{[m.kind for m in order]} left {unreachable} unreachable, reporting a guard as "
            "unobservable while a plant that could run exists"
        )


def test_the_pairing_audit_census_divides_by_what_it_observed() -> None:
    """The first version of this instrument printed `0 of 72` while five samples never ran.

    A membership claim is only as good as its denominator, so every figure is derived from the
    records that were observed, an unrunnable module is its own bucket, and the `declared` total is
    the sum of the two lists rather than a count of the registry the run never reached.
    """
    attributed = harness.ATTRIBUTED
    records: list[dict[str, object]] = [
        {"verdict": harness.PAIRED, "size": 3, "attribution": attributed},
        {"verdict": harness.PAIRED, "size": 1, "attribution": attributed},
        {"verdict": harness.PAIRED, "size": 2, "attribution": harness.UNATTRIBUTED},
        {"verdict": harness.MIS_PAIRED, "size": 2, "attribution": attributed},
        {"verdict": harness.ESCAPED, "size": 0, "attribution": attributed},
        {"verdict": harness.MODULE_NOT_RUN, "size": 0, "attribution": attributed},
    ]
    unreachable = [("tests/python/x.py::test_unreachable", "its guard is a CTest case")]
    counts = harness.audit_counts(records, unreachable)
    assert counts["sampled"] == 6
    assert counts["attributed"] == 4 and counts["unattributed"] == 1, (
        f"attributed={counts['attributed']} unattributed={counts['unattributed']}: the residual of "
        "the derived rule is the number #107 has to be able to name"
    )
    assert counts["observed"] == 5, "a module that never ran was counted as an observation"
    assert counts["not-run"] == 1, "the unrunnable bucket stopped naming its own cases"
    assert counts["paired"] == 3 and counts["singleton"] == 1, (
        f"paired={counts['paired']} singleton={counts['singleton']}: a census that cannot tell "
        "a wide set from a lone one is not the measurement #103 was closed with"
    )
    assert counts["mis-paired"] == 1 and counts["escaped"] == 1
    assert counts["declared"] == counts["sampled"] + counts["unreachable"] == 7

    line = harness.audit_census(counts)
    assert "3/5" in line and "1/5" in line, (
        f"the published census reads {line!r}, so a ratio lost the denominator that makes it a "
        "measurement rather than a count"
    )


def test_a_module_run_that_never_collected_is_not_read_as_an_escaped_plant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`pytest` returns 1 for failures and 2, 3, 4, 5 for runs that never happened.

    Folding those into an empty failing set would report a broken module as a plant that escaped
    every guard -- the opposite of what the audit is for, and indistinguishable in the census. The
    return code is what decides, so both sides of the boundary are pinned here, along with the
    isolation the module run has to carry like every other guard subprocess.
    """
    seen: list[dict[str, str] | None] = []

    def fake(command: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(kwargs.get("env"))
        return subprocess.CompletedProcess(
            list(command or []), 2, "ERROR tests/python/x.py::test_a\nno tests ran\n", ""
        )

    monkeypatch.setattr(harness.subprocess, "run", fake)
    swept = harness.Harness(build_dir="build/dev")
    ran, failing, tracebacks = swept.module_failures("tests/python/x.py")
    assert not ran and failing == set() and tracebacks == [], "a collection error read as a run"
    assert (
        harness.audit_verdict(ran=ran, failing=failing, named="test_a") == harness.MODULE_NOT_RUN
    ), "an unrunnable module reached a pairing verdict"
    prefix = (seen[-1] or {}).get(harness.BYTECODE_PREFIX)
    assert prefix, "the module run spawned a guard without a bytecode prefix of its own"

    def fake_failures(command: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            list(command or []),
            1,
            "FAILED tests/python/x.py::test_a - AssertionError\n"
            "/abs/x.py:12: AssertionError: mine\n",
            "",
        )

    monkeypatch.setattr(harness.subprocess, "run", fake_failures)
    ran, failing, tracebacks = swept.module_failures("tests/python/x.py")
    assert ran and failing == {"test_a"}, "a real failure did not read as one"
    assert tracebacks == [("/abs/x.py", 12, "AssertionError: mine")], (
        f"the per-assertion lines are what #107 needs, and the run returned {tracebacks}"
    )


def test_the_pairing_audit_attributes_a_failure_to_the_named_guard_s_own_line() -> None:
    """#107's question is "did this guard reject about this line", and the line is derivable.

    `--tb=line` prints one entry per failure keyed by the location of the assertion that raised, so
    the audit can say which assert in the named guard spoke -- without slicing a transcript at a
    header. The attribution is also what makes the neighbour invisible: a message from a different
    function in the same file cannot be selected, because its line is outside the named span.
    """
    source = (
        "def test_neighbour():\n"
        "    assert 1 == 2, 'the neighbour objects about something else'\n"
        "\n"
        "\n"
        "def test_named():\n"
        "    value = 1\n"
        "    assert value == 2, 'the named guard reads the mutated slot'\n"
    )
    span = harness.guard_span(source, "test_named")
    assert span == (5, 7), f"the span of test_named is {span}, and a wrong span attributes wrongly"
    lines = [
        ("t.py", 2, "AssertionError: the neighbour objects about something else"),
        ("t.py", 7, "AssertionError: the named guard reads the mutated slot"),
    ]
    site = harness.failing_assertion(lines, module="t.py", name="test_named", source=source)
    assert site == (7, "AssertionError: the named guard reads the mutated slot"), (
        f"the audit attributes the failure to {site}; the named guard's own line is 7"
    )
    assert (
        harness.failing_assertion([lines[0]], module="t.py", name="test_named", source=source)
        is None
    ), "a neighbour's line was read as the named guard's own"
    assert (
        harness.failing_assertion(lines, module="t.py", name="no_such_test", source=source) is None
    ), "a guard that is not defined reported a failing line anyway"


def test_the_pairing_audit_reads_its_evidence_as_lines_and_not_as_a_sliced_transcript() -> None:
    """Finding 91, made permanent: the cutter may not depend on how wide the terminal is.

    The two shapes that defeated a fixed-width separator are both here -- a short test name padded
    with many underscores and a 71-character one padded with two -- and the reader has to return
    each message whole and separate, because a message is the part of a branch audit that is not a
    number.
    """
    long_name = "test_every_declared_number_names_a_producer_or_records_that_none_exists"
    transcript = (
        "=========================== short test summary info ============================\n"
        f"FAILED tests/python/x.py::test_a - AssertionError: mine\n"
        f"FAILED tests/python/x.py::{long_name} - AssertionError: theirs\n"
        "tests/python/x.py:41: AssertionError: mine, with the whole message kept\n"
        "tests/python/x.py:77: AssertionError: theirs and much longer than a terminal "
        "width -- " + "x" * 120 + "\n"
        "2 failed in 61.20s\n"
    )
    read = harness.parse_failures(transcript)
    assert read == {"test_a", long_name}, f"the failing set reads {read}"
    lines = harness.parse_line_tracebacks(transcript)
    assert [entry[1] for entry in lines] == [41, 77], f"the line reader returned {lines}"
    assert len(lines) == 2 and len(lines[1][2]) > 150, (
        f"a message was clipped: {[len(entry[2]) for entry in lines]}"
    )


def test_the_module_run_asks_pytest_for_the_per_assertion_lines_it_needs() -> None:
    """A report format the audit does not ask for is a check that silently stopped happening.

    `--tb=no` would still yield the failing names, so every other part of the audit keeps passing
    while the attribution half reads nothing. The flag is the input to #107's instrument, so it is
    asserted where the command is built rather than trusted from the docstring.
    """
    seen: list[list[str]] = []

    def spy(command: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append([str(part) for part in list(command or [])])
        return subprocess.CompletedProcess(list(command or []), 1, "FAILED x.py::test_a\n", "")

    monkeypatch_module = pytest.MonkeyPatch()
    monkeypatch_module.setattr(harness.subprocess, "run", spy)
    try:
        swept = harness.Harness(build_dir="build/dev")
        ran, failing, _ = swept.module_failures("tests/python/x.py")
    finally:
        monkeypatch_module.undo()
    assert ran and failing == {"test_a"}, "the module run stopped reporting what failed"
    assert seen and "--tb=line" in seen[0], (
        f"the audit runs pytest with {seen[0] if seen else 'nothing'}; without the flag there "
        "are no per-assertion lines to attribute"
    )


def test_the_reading_closure_reaches_the_helpers_and_constants_a_guard_actually_reads() -> None:
    """A guard rarely names the mutated thing in its own body; the closure has to walk to it.

    The chain here is the one the shipped registry has: the test calls a local helper, the helper
    reads a module constant, and the constant is built from the symbol the plant edits. A walk that
    indexes only top-level definitions stops at the nested helper, and a shallow depth cap stops one
    hop earlier -- both leave a real pairing looking unlinkable, which is how #103's static half
    failed.
    """
    source = (
        "_TAIL = _MODIFIER_BLOCK + noun\n"
        "\n"
        "def test_named():\n"
        "    def helper():\n"
        "        return _TAIL\n"
        "    assert helper() == 1, 'the rule reads the slot it should not'\n"
    )
    closure = harness.reading_closure(source, "test_named")
    assert "_TAIL" in closure, f"the closure did not reach the module constant: {closure!r}"
    deep = (
        "_A = _B\n_B = _C\n_C = _D\n_D = _E\n_E = _TARGET\n_TARGET = 1\n"
        "def test_deep():\n    assert _A == 1\n"
    )
    assert "_TARGET" in harness.reading_closure(deep, "test_deep"), (
        "the closure walk stopped short of a five-hop chain, so a depth cap is doing the "
        "attributing rather than the text"
    )


def test_the_pairing_audit_reads_the_closure_from_the_text_before_the_plant_fires() -> None:
    """The link question is about the program as written, so the audit may not read the plant's
    edit.

    `claim-modifier-slot-reopened-after-the-census` deletes the one reference its guard's closure
    follows. An instrument that walks the mutated text therefore erases the evidence of its own
    pairing, and that is what happened on `6ddc965`: the shipped audit called the plant unlinkable
    while the offline pin, which reads the file as committed, called it linked. Two halves of one
    record disagreed only because they read different texts. The other half genuinely has to follow
    the edit -- a traceback's line number indexes the file pytest compiled -- so the choice is
    pinned where it is made, name by name, rather than left to a comment.
    """
    tree = ast.parse(HARNESS_PATH.read_text(encoding="utf-8"))
    audit = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_pairing_audit"
    )
    origins: dict[str, str] = {}
    for node in ast.walk(audit):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not isinstance(node.value, ast.IfExp):
            continue
        if isinstance(node.value.body, ast.Name):
            origins[target.id] = node.value.body.id
    assert origins.get("closure_source") == "pristine", (
        f"the closure is read from {origins.get('closure_source')!r}; the text before the plant "
        "fired is the one that says what the guard was written to read"
    )
    assert origins.get("span_source") == "mutated", (
        f"the span is read from {origins.get('span_source')!r}; a traceback indexes the file "
        "pytest compiled, so this half has to follow the edit"
    )
    calls = [
        node
        for node in ast.walk(audit)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "attribution"
    ]
    assert len(calls) == 1, (
        f"the audit builds its attribution {len(calls)} times, and this pin is lost"
    )
    closure_argument = next(
        keyword.value for keyword in calls[0].keywords if keyword.arg == "closure"
    )
    assert (
        isinstance(closure_argument, ast.Call)
        and isinstance(closure_argument.func, ast.Name)
        and closure_argument.func.id == "reading_closure"
        and isinstance(closure_argument.args[0], ast.Name)
        and closure_argument.args[0].id == "closure_source"
    ), "the attribution call no longer reads the text this pin governs"


def test_the_plants_the_pairing_audit_cannot_attribute_are_named_and_pinned() -> None:
    """The residual of the derived rule is a list, not an silence.

    Computed without running a suite: every sampled plant's guard module is parsed, its reading
    closure built, and the plant's own anchor tokens and edited path looked for in it. What does not
    match has to appear in `UNATTRIBUTED_PLANTS` -- a plant that loses its text link unnoticed is
    #107's defect arriving through the back door, and a plant that gains a link and stays listed is
    a pin that has stopped measuring anything.
    """
    sample, _unreachable = harness.pairing_sample(harness.MUTATIONS)
    unattributed = []
    for plant in sample:
        module, _, name = plant.guard.partition("::")
        source = (REPO_ROOT / module).read_text(encoding="utf-8")
        closure = harness.reading_closure(source, name)
        verdict = harness.attribution(
            closure=closure, path=plant.path, tokens=harness.anchor_tokens(plant.anchor)
        )
        if verdict == harness.UNATTRIBUTED:
            unattributed.append(plant.identifier)
    assert set(unattributed) == set(harness.UNATTRIBUTED_PLANTS), (
        f"unlinkable plants are {sorted(unattributed)} but the pinned set is "
        f"{sorted(harness.UNATTRIBUTED_PLANTS)}: the audit's residual moved without a decision"
    )
    assert len(unattributed) <= 3, (
        f"{len(unattributed)} of {len(sample)} sampled plants cannot be attributed, so the "
        "derived rule is no longer the reason this check is cheap"
    )
