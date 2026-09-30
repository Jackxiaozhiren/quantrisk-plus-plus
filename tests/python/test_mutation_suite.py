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

import importlib.util
import sys
from pathlib import Path

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


def test_every_declared_mutation_names_one_unique_anchor_and_a_guard_that_exists() -> None:
    """The list may not rot: a stale anchor or a renamed guard would make the harness report a lie.

    This is the check that would have caught finding 25 before a sweep did — not by running the
    mutations, which is slow and destructive, but by asserting on every ordinary test run that
    each anchor still occurs exactly once in the file it names, and that the guard expected to
    reject it is still defined there.
    """
    identifiers = [mutation.identifier for mutation in harness.MUTATIONS]
    assert len(set(identifiers)) == len(identifiers), f"duplicate mutation ids: {identifiers}"
    assert len([m for m in harness.MUTATIONS if m.kind == "core"]) >= 3, identifiers
    assert len([m for m in harness.MUTATIONS if m.kind == "prose"]) >= 5, identifiers

    for mutation in harness.MUTATIONS:
        assert not Path(mutation.path).is_absolute(), mutation.identifier
        assert ".." not in Path(mutation.path).parts, mutation.identifier
        target = REPO_ROOT / mutation.path
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


def test_the_selected_mutations_resolve_by_kind_and_identifier() -> None:
    """`--only` and `--kind` are how an operator runs one case, so they must resolve exactly."""
    for mutation in harness.MUTATIONS:
        chosen = harness.select(None, [mutation.identifier])
        assert [item.identifier for item in chosen] == [mutation.identifier]
    prose = harness.select("prose", [])
    core = harness.select("core", [])
    assert len(prose) + len(core) == len(harness.MUTATIONS)
    assert all(item.kind == "prose" for item in prose)
    assert all(item.kind == "core" for item in core)
    assert harness.select("core", [prose[0].identifier]) == []
