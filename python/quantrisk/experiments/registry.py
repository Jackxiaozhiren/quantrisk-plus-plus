"""The one task registry: what can run, where its artifact is, and how it is invoked.

`REFACTOR_PROMPT.md` §5 D3 makes this table the source of truth for runnable work, and D4-prime
makes the recorded reproduction command *derived* rather than typed: an entry names its module, and
the command is the canonical prefix plus that module. A hand-typed command is refused at
construction, because a string nobody generated is exactly how 43 of this repository's 95 frozen
commands came to name a file that does not exist.

Two rules make the table worth having. An entry validates itself (§5 D3-prime): unknown keys cannot
appear on a dataclass, an unknown category is a build failure, and `absorbed=True` asserts that the
module is importable here. And the table is a literal, never a directory scan: a registry assembled
by globbing would share its source with the filesystem side of the parity test in
`tests/python/test_task_registry_parity.py`, and a two-sided guard computed from one list proves
nothing.
"""

from __future__ import annotations

import argparse
import importlib.util
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from quantrisk.checkout import checkout_root

REGISTRY_VERSION = "1"
COMMAND_PREFIX = "uv run python -m "

CATEGORIES = frozenset(
    {
        "correctness_benchmark",
        "performance_benchmark",
        "statistical_experiment",
    }
)

EXPERIMENTS = "experiments"
BENCHMARKS = "benchmarks"
PACKAGE_DIR = "python/quantrisk"


def canonical_command(module: str) -> str:
    """The one spelling of how a task is run, generated from its module path."""
    return f"{COMMAND_PREFIX}{module}"


def module_resolves(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


def artifact_path(task: Task, out: Path | None = None) -> Path:
    """The published artifact of one task, under the root it is given.

    A study writes *here* rather than to a filename of its own, so the path the registry declares
    and the path the code produces cannot disagree -- which is the half of D3 that a directory
    alone leaves open.
    """
    root = checkout_root() if out is None else Path(out)
    return root / task.artifact


def results_directory(task: Task, out: Path | None = None) -> Path:
    """Where one task's artifacts land: its published path, under the root it is given.

    `--out` names a directory to treat as the repository root, so a replay in a temporary tree
    writes `tmp/experiments/<task>/results/…` and the layout a reviewer diffs against is the
    published one. With no `--out` the root is the checkout the working tree is in; there is no
    third answer, and none is guessed.
    """
    return artifact_path(task, out).parent


def parse_out(argv: Sequence[str], *, description: str = "") -> Path | None:
    """Read the one flag every published study accepts.

    Kept here rather than in each study because 14 copies of an argparse block is 14 chances for
    the flag to mean something slightly different in one of them, and `--out` is the flag the
    installed-user and the temporary-tree proofs both turn on.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="treat this directory as the repository root; required outside a checkout",
    )
    return parser.parse_args(argv).out


@dataclass(frozen=True)
class Task:
    """One runnable unit: its current source, its destination module, its artifact, its category.

    `source` is the path the unit is reachable at today; `module` is the dotted path it will be
    reachable at once absorbed. `absorbed` is flipped by the commit that moves the unit, and it is
    the flag that turns "this module exists" from a hope into an assertion.
    """

    task_id: str
    source: str
    module: str
    artifact: str
    category: str
    absorbed: bool = False
    command: str | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        validate_task(self)

    @property
    def invocation(self) -> str:
        return canonical_command(self.module)

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "source": self.source,
            "module": self.module,
            "artifact": self.artifact,
            "category": self.category,
            "command": self.invocation,
            "absorbed": self.absorbed,
        }


def validate_task(task: Task) -> None:
    """D3-prime: refuse an entry that cannot be honoured, at the moment it is declared."""
    if not task.task_id or not task.task_id.isidentifier():
        raise ValueError(f"task_id {task.task_id!r} is not a usable identifier")
    if task.category not in CATEGORIES:
        raise ValueError(
            f"{task.task_id}: category {task.category!r} is not one the evidence ledger knows "
            f"({sorted(CATEGORIES)})"
        )
    for field_name in ("source", "module", "artifact"):
        value = getattr(task, field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{task.task_id}: {field_name} must be a non-empty string")
    if not task.module.startswith(f"quantrisk.{EXPERIMENTS}.") and not task.module.startswith(
        f"quantrisk.{BENCHMARKS}."
    ):
        raise ValueError(
            f"{task.task_id}: module {task.module!r} is outside the layout "
            "this registry serves (quantrisk.experiments.* or quantrisk.benchmarks.*)"
        )
    if task.command is not None and task.command != canonical_command(task.module):
        raise ValueError(
            f"{task.task_id}: canonical invocation must be generated from the module path; "
            f"refusing the typed command {task.command!r}"
        )
    if task.absorbed and not module_resolves(task.module):
        raise ValueError(f"{task.task_id} claims to be absorbed but {task.module} does not resolve")


def _task(**kwargs: Any) -> Task:
    return Task(**kwargs)


def _study(task_id: str, directory: str, artifact: str, *, absorbed: bool = False) -> Task:
    """A published study, named by its directory in both layouts the lane moves between."""
    package = f"{PACKAGE_DIR}/{EXPERIMENTS}/{directory}"
    return _task(
        task_id=task_id,
        source=(f"{package}/__main__.py" if absorbed else f"{EXPERIMENTS}/{directory}/run.py"),
        module=f"quantrisk.{EXPERIMENTS}.{directory}",
        artifact=f"{EXPERIMENTS}/{directory}/results/{artifact}",
        category="statistical_experiment",
        absorbed=absorbed,
    )


def _benchmark(
    task_id: str, suite: str, script: str, artifact: str, *, absorbed: bool = False
) -> Task:
    package = f"{PACKAGE_DIR}/{BENCHMARKS}/{suite}/{script}.py"
    return _task(
        task_id=task_id,
        source=package if absorbed else f"{BENCHMARKS}/{suite}/{script}.py",
        module=f"quantrisk.{BENCHMARKS}.{suite}.{script}",
        artifact=f"{BENCHMARKS}/{suite}/results/{artifact}",
        category="correctness_benchmark",
        absorbed=absorbed,
    )


TASKS: tuple[Task, ...] = (
    _benchmark(
        "pricing_vs_quantlib",
        "quantlib",
        "pricing_validation",
        "pricing_vs_quantlib.json",
    ),
    _benchmark(
        "monte_carlo_vs_analytic",
        "quantlib",
        "monte_carlo_validation",
        "monte_carlo_validation.json",
    ),
    _benchmark(
        "path_dependent_vs_quantlib",
        "quantlib",
        "path_dependent_validation",
        "path_dependent_vs_quantlib.json",
    ),
    _benchmark(
        "optimisation_vs_oracles",
        "pyportfolioopt",
        "optimisation_validation",
        "optimisation_vs_oracles.json",
    ),
    _task(
        task_id="mc_speed",
        source="benchmarks/performance/monte_carlo_speed.py",
        module=f"quantrisk.{BENCHMARKS}.performance.monte_carlo_speed",
        artifact="benchmarks/performance/results/monte_carlo_speed.json",
        category="performance_benchmark",
    ),
    _study("pricing_grid", "pricing_validation", "summary.json"),
    _study("mc_convergence", "monte_carlo_convergence", "summary.json"),
    _study("variance_reduction", "variance_reduction", "summary.json"),
    _study(
        "var_backtesting",
        "var_backtesting",
        "var_backtesting_validation.json",
    ),
    _study(
        "portfolio_estimation_cost",
        "portfolio_optimization",
        "portfolio_optimisation_study.json",
    ),
    _study(
        "linearisation_error_bound",
        "linearisation_error_bound",
        "linearisation_error_bound.json",
    ),
    _study("two_factor_error_bound", "two_factor_error_bound", "two_factor_bound.json"),
    _study("stress_testing", "stress_testing", "stress_testing_study.json", absorbed=True),
    _study("real_data_risk_study", "real_data_risk_study", "real_data_risk_study.json"),
    _study(
        "restrike_gamma_map",
        "restrike_gamma_map",
        "restrike_gamma_map.json",
        absorbed=True,
    ),
    _study(
        "fourth_order_crossing_map",
        "fourth_order_crossing_map",
        "fourth_order_crossing_map.json",
        absorbed=True,
    ),
    _study(
        "second_book_crossing_map",
        "second_book_crossing_map",
        "second_book_crossing_map.json",
    ),
    _study(
        "fifth_order_crossing_map",
        "fifth_order_crossing_map",
        "fifth_order_crossing_map.json",
    ),
    _study(
        "sixth_book_crossing_map",
        "sixth_book_crossing_map",
        "sixth_book_crossing_map.json",
    ),
)

TASKS_BY_ID: dict[str, Task] = {task.task_id: task for task in TASKS}

# The order absorption must follow, derived from the sibling-study loads measured in Phase 1
# (finding V2-02): a study that imports a published sibling cannot be absorbed before it. The
# parity test refuses a sequence that is not a permutation of TASKS, so an entry added here
# without an order entry goes red rather than being absorbed in a sequence that breaks its input.
ABSORPTION_ORDER: tuple[str, ...] = (
    "stress_testing",
    "restrike_gamma_map",
    "fourth_order_crossing_map",
    "second_book_crossing_map",
    "fifth_order_crossing_map",
    "sixth_book_crossing_map",
    "two_factor_error_bound",
    "pricing_grid",
    "mc_convergence",
    "variance_reduction",
    "var_backtesting",
    "portfolio_estimation_cost",
    "linearisation_error_bound",
    "real_data_risk_study",
    "pricing_vs_quantlib",
    "monte_carlo_vs_analytic",
    "path_dependent_vs_quantlib",
    "optimisation_vs_oracles",
    "mc_speed",
)


def tasks_in_absorption_order() -> Sequence[Task]:
    if sorted(ABSORPTION_ORDER) != sorted(TASKS_BY_ID):
        raise ValueError(
            "ABSORPTION_ORDER is not a permutation of TASKS; missing "
            f"{sorted(set(TASKS_BY_ID) - set(ABSORPTION_ORDER))}, "
            f"extra {sorted(set(ABSORPTION_ORDER) - set(TASKS_BY_ID))}"
        )
    return [TASKS_BY_ID[task_id] for task_id in ABSORPTION_ORDER]
