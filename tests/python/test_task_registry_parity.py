"""L5: the task registry and the filesystem must agree, from two independent sources.

This is the guard that makes `REFACTOR_PROMPT.md` §13 L5 mean something. It is deliberately written
so that neither side can be computed from the other: side A discovers runnable units by walking the
tracked tree and never imports the registry; side B imports the registry and never walks the tree.
Each side prints what it enumerated, because a comparison over two silently-empty sets proves
nothing (§4.3: counters must not pass by absence).
"""

from __future__ import annotations

import importlib
import subprocess
from typing import Any

REGISTRY_MODULE = "quantrisk.experiments.registry"
UNIT_PATTERNS = (
    "experiments/",
    "benchmarks/",
    "python/quantrisk/experiments/",
    "python/quantrisk/benchmarks/",
)


def _is_runnable_unit(path: str) -> bool:
    """A unit is a file that can be *run*, not every file that exists.

    Both layouts are recognised on purpose: studies live at `experiments/<task>/run.py` until
    absorbed and at `python/quantrisk/experiments/<task>/__main__.py` afterwards, and benchmark
    validators move from `benchmarks/<suite>/<script>.py` to
    `python/quantrisk/benchmarks/<suite>/<script>.py`. A discovery rule that only knew the first
    layout would make every absorption commit look like a lost task.
    """
    if path.startswith("experiments/"):
        return path.endswith("/run.py")
    if path.startswith("benchmarks/"):
        return path.count("/") == 2
    if path.startswith("python/quantrisk/experiments/"):
        return path.endswith("/__main__.py")
    if path.startswith("python/quantrisk/benchmarks/"):
        return path.endswith(".py") and not path.endswith(("__init__.py", "registry.py"))
    return False


def _tracked_python_units() -> list[str]:
    """Side A: every tracked Python file that is a runnable unit, found without the registry."""
    listed = subprocess.run(
        ["git", "ls-files", "--", "*.py"],
        capture_output=True,
        text=True,
        check=True,
    )
    return sorted(
        path
        for path in listed.stdout.splitlines()
        if path.startswith(UNIT_PATTERNS) and _is_runnable_unit(path)
    )


def _registry_entries() -> list[dict[str, Any]]:
    """Side B: the registry's own declaration, read by importing it."""
    module = importlib.import_module(REGISTRY_MODULE)
    return [entry.as_dict() for entry in module.TASKS]


def test_the_registry_and_the_filesystem_enumerate_the_same_runnable_units() -> None:
    from quantrisk.experiments.registry import REGISTRY_VERSION

    units = _tracked_python_units()
    entries = _registry_entries()
    print(f"filesystem enumerated {len(units)} units [{REGISTRY_VERSION}]:")
    for path in units:
        print(f"  {path}")
    print(f"registry enumerated {len(entries)} tasks:")
    for entry in entries:
        print(f"  {entry['task_id']} -> {entry['source']}")

    assert units, "the filesystem walk found no runnable units, so the comparison is vacuous"
    assert entries, "the registry declares no tasks"
    assert len(entries) >= 15, (
        f"the registry names only {len(entries)} tasks; the suite has carried 19 since Phase 18, "
        "and a registry that quietly narrowed is worse than no registry"
    )
    assert sorted(entry["source"] for entry in entries) == units, (
        f"on disk but not registered: {sorted(set(units) - {e['source'] for e in entries})}; "
        f"registered but not on disk: {sorted({e['source'] for e in entries} - set(units))}"
    )


def test_every_registry_task_names_an_artifact_that_exists() -> None:
    """A task whose artifact path is wrong cannot be re-run, so the path is part of the claim."""
    from pathlib import Path

    import quantrisk.experiments.registry as registry

    root = Path(registry.__file__).resolve().parents[3]
    missing = [
        f"{entry.task_id}: {entry.artifact}"
        for entry in registry.TASKS
        if not (root / entry.artifact).is_file()
    ]
    print(f"checked {len(registry.TASKS)} artifact paths under {root}")
    assert not missing, f"registry artifacts missing on disk: {missing}"


def test_a_task_that_does_not_declare_the_canonical_invocation_is_refused() -> None:
    """D4-prime: the command is derived from the module path, never typed by a human."""
    import pytest
    from quantrisk.experiments.registry import Task

    with pytest.raises(ValueError, match="canonical invocation"):
        Task(
            task_id="hand_typed",
            source="experiments/hand_typed/run.py",
            module="quantrisk.experiments.hand_typed",
            artifact="experiments/hand_typed/results/summary.json",
            category="statistical_experiment",
            command="uv run python experiments/hand_typed/run.py",
        )


def test_an_entry_with_an_unknown_key_or_an_unknown_category_is_a_build_failure() -> None:
    """D3-prime: the registry validates itself rather than accepting arbitrary attributes."""
    import dataclasses

    import pytest
    from quantrisk.experiments.registry import Task, validate_task

    with pytest.raises(ValueError, match="category"):
        validate_task(
            dataclasses.replace(
                Task(
                    task_id="ok",
                    source="experiments/ok/run.py",
                    module="quantrisk.experiments.ok",
                    artifact="experiments/ok/results/summary.json",
                    category="statistical_experiment",
                ),
                category="made_up_category",
            )
        )


def test_absorbed_tasks_are_the_ones_whose_source_lives_in_the_package() -> None:
    """The `absorbed` flag and the source path must move together, in one commit.

    A task flagged absorbed while its source still points at a root-level `run.py` would let the
    registry claim a module that is not there; a task whose file is already inside the package but
    still flagged unabsorbed would let `run --list` name a command that cannot run.
    """
    from quantrisk.experiments.registry import TASKS

    inconsistent = [
        f"{entry.task_id}: absorbed={entry.absorbed} source={entry.source}"
        for entry in TASKS
        if entry.absorbed != entry.source.startswith("python/quantrisk/")
    ]
    absorbed = sum(1 for entry in TASKS if entry.absorbed)
    print(f"{absorbed} of {len(TASKS)} tasks absorbed, {len(TASKS) - absorbed} still at the root")
    assert not inconsistent, f"absorbed flag disagrees with the source path: {inconsistent}"


# Phase 1 measured these edges by reading the sibling-study loads in each study's source
# (ledger finding V2-02: 7 edges over 6 studies). They are literals here rather than read from
# the registry, because a guard that derives its own expectation from the thing it checks
# cannot fail.
STUDY_EDGES: dict[str, tuple[str, ...]] = {
    "restrike_gamma_map": ("stress_testing",),
    "fourth_order_crossing_map": ("restrike_gamma_map",),
    "second_book_crossing_map": ("restrike_gamma_map", "fourth_order_crossing_map"),
    "fifth_order_crossing_map": ("second_book_crossing_map",),
    "sixth_book_crossing_map": ("fifth_order_crossing_map",),
    "two_factor_error_bound": ("stress_testing",),
}
STUDY_IDS: tuple[str, ...] = (
    "stress_testing",
    "restrike_gamma_map",
    "fourth_order_crossing_map",
    "second_book_crossing_map",
    "fifth_order_crossing_map",
    "sixth_book_crossing_map",
    "two_factor_error_bound",
)


def test_the_absorption_sequence_never_moves_a_study_before_its_dependencies() -> None:
    """P3.3 commits one task at a time; the order is a constraint from the code."""
    from quantrisk.experiments.registry import TASKS_BY_ID, tasks_in_absorption_order

    ordered = [task.task_id for task in tasks_in_absorption_order()]
    position = {task_id: index for index, task_id in enumerate(ordered)}
    print(f"absorption order has {len(ordered)} tasks; {len(STUDY_EDGES)} carry measured edges")

    assert sorted(ordered) == sorted(TASKS_BY_ID), "ABSORPTION_ORDER is not a permutation of TASKS"
    for task_id in STUDY_IDS:
        assert task_id in position, f"{task_id} is missing from the absorption order"
    for task_id, dependencies in STUDY_EDGES.items():
        for dependency in dependencies:
            assert position[dependency] < position[task_id], (
                f"{task_id} loads {dependency} as a published sibling, so {dependency} must be "
                "absorbed first"
            )
