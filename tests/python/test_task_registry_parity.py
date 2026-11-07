"""L5: the task registry and the filesystem must agree, from two independent sources.

This is the guard that makes `REFACTOR_PROMPT.md` §13 L5 mean something. It is deliberately written
so that neither side can be computed from the other: side A discovers runnable units by walking the
tracked tree and never imports the registry; side B imports the registry and never walks the tree.
Each side prints what it enumerated, because a comparison over two silently-empty sets proves
nothing (§4.3: counters must not pass by absence).
"""

from __future__ import annotations

import ast
import importlib
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

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


def test_an_absorbed_task_is_invocable_and_writes_where_it_is_told(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """D1's destination, asserted per absorbed task rather than assumed from the file being there.

    Two things make a moved study usable: it resolves as a module, because that is the form
    `quantrisk run` and the suite's `execute()` will invoke; and it derives its published artifact
    path from a root that is either an explicit `--out` or the checkout it is standing in, refusing
    with the path it searched when it is neither. A module that fell back to its own directory would
    write published numbers into site-packages, and a file that sits in the package without being
    importable is a registry entry that lies.
    """
    import importlib
    import inspect

    from quantrisk.experiments.registry import TASKS, checkout_root, results_directory

    root = Path(__file__).resolve().parents[2]
    absorbed = [task for task in TASKS if task.absorbed]
    assert absorbed, "no task is absorbed yet, so this guard asserts nothing"
    problems: list[str] = []
    for task in absorbed:
        module = importlib.import_module(task.module)
        for name in ("run", "main"):
            entry_point = getattr(module, name, None)
            if not callable(entry_point):
                problems.append(f"{task.task_id}: {task.module} has no callable {name}()")
            elif name == "main" and not inspect.signature(entry_point).parameters:
                problems.append(f"{task.task_id}: main() takes no argv, so it cannot be reused")
        published = results_directory(task)
        if published != root / Path(task.artifact).parent:
            problems.append(
                f"{task.task_id}: resolved {published} instead of the published {task.artifact}"
            )
        replay = results_directory(task, out=tmp_path)
        if not replay.is_relative_to(tmp_path) or replay == tmp_path:
            problems.append(f"{task.task_id}: --out did not keep the artifact under {tmp_path}")
        print(f"  {task.task_id}: {published.relative_to(root)}")
    assert not problems, "absorbed task contract broken:\n" + "\n".join(problems)

    outside = tmp_path / "not-a-checkout"
    outside.mkdir()
    with pytest.raises(RuntimeError, match="not inside a QuantRisk\\+\\+ checkout"):
        checkout_root(start=outside)

    # V3 §4 item 1 closed here. The declaration is guarded against drift, but nothing in this suite
    # reddened if `command_run` stopped consulting it: the only instrument that executed the refusal
    # against a real absence was `tools/verify_installed_surface --refusal pricing_grid`, whose
    # ceiling key SKIPs on the runner by design. Driving the branch from the suite makes the pytest
    # lane itself the gate, and `module_resolves` is monkeypatched rather than the extra being
    # uninstalled, so the reading does not depend on what this machine happens to carry.
    import argparse

    import quantrisk.cli as cli
    from quantrisk.experiments import registry

    refusing = next(task for task in registry.TASKS if task.task_id == "pricing_grid")
    extra = sorted(refusing.requires)[0]
    absent = registry.EXTRA_MODULES[extra][0]
    monkeypatch.setattr(registry, "module_resolves", lambda name: name != absent)
    refused_out = tmp_path / "refused"
    code = cli.command_run(
        argparse.Namespace(task=refusing.task_id, out=refused_out, list_tasks=False)
    )
    captured = capsys.readouterr()
    printed = captured.out + captured.err
    assert code == 1, f"{refusing.task_id} must be refused with exit 1, not {code}"
    assert f"quantrisk[{extra}]" in printed, printed
    published = [path for path in refused_out.rglob("*") if path.is_file()]
    assert not published, f"a refused task published {published} under {refused_out}"


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


# --- N1: the declared requirement set versus the import tree ------------------
#
# The registry's `requires` field is a literal a human writes, and a literal about code drifts the
# moment the code changes: a study that starts importing `scipy` would keep saying `plot` and stay
# green, which is the V2-27 shape (a declaration nothing compares with the artifact it declares).
# The walk below is the comparison. It reads the task's module and follows every `quantrisk.*`
# import into the package, so a dependency reached through a shared helper counts even though the
# task never names it -- which is how `restrike_gamma_map` needs `matplotlib` while the word appears
# in it only in a comment.

PACKAGE = Path(__file__).resolve().parents[2] / "python" / "quantrisk"


def _module_file(dotted: str) -> Path | None:
    """The file a dotted module name resolves to inside this checkout, or None."""
    base = PACKAGE.parent / Path(*dotted.split("."))
    for candidate in (base / "__init__.py", base.with_suffix(".py"), base / "__main__.py"):
        if candidate.is_file():
            return candidate
    return None


def _package_of(dotted: str, path: Path) -> str:
    """The package a file's relative imports are anchored to.

    A package's `__init__.py` *is* the package; any other file is one level below it. Getting this
    wrong by the one level that `__init__.py` differs by turns `from . import x` into an import of
    the parent, which silently loses the matplotlib that most of these studies reach through
    `quantrisk.plotting`.
    """
    return dotted if path.name == "__init__.py" else dotted.rsplit(".", 1)[0]


def _targets(node: ast.ImportFrom, package: str) -> list[str]:
    """Every module a `from ... import ...` can name, absolute and relative alike.

    `from quantrisk import plotting` names two things: the package `quantrisk` and the module
    `quantrisk.plotting`. Both are returned because only one of them may exist as a module, and
    resolving the shorter one alone would miss the import that carries matplotlib.
    """
    if not node.level:
        base = node.module or ""
    else:
        parts = package.split(".")[: len(package.split(".")) - (node.level - 1)]
        base = ".".join([*parts, *(node.module.split(".") if node.module else [])])
    if not base:
        return []
    return [base, *(f"{base}.{alias.name}" for alias in node.names)]


def _walk(dotted: str, seen: set[str], roots: dict[str, set[str]], chain: tuple[str, ...]) -> None:
    """Follow one module's imports, recording every non-`quantrisk` root it can reach."""
    if dotted in seen:
        return
    path = _module_file(dotted)
    if path is None:
        return
    seen.add(dotted)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    package = _package_of(dotted, path)
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.extend(_targets(node, package))
    for name in names:
        root = name.split(".")[0]
        if root == "quantrisk":
            _walk(name, seen, roots, (*chain, name))
        else:
            roots.setdefault(root, set()).add("/".join(chain[-2:]))


def _imported_roots(module: str) -> dict[str, set[str]]:
    roots: dict[str, set[str]] = {}
    _walk(module, set(), roots, (module,))
    return roots


def _base_dependency_roots() -> set[str]:
    """What the wheel installs without any extra, read from the manifest rather than restated."""
    manifest = tomllib.loads((Path(__file__).resolve().parents[2] / "pyproject.toml").read_text())
    roots = {"_quantrisk"}  # the compiled extension ships in the wheel, not in `dependencies`
    for requirement in manifest["project"]["dependencies"]:
        name = re.split(r"[\s<>=!~\[]", requirement, maxsplit=1)[0]
        roots.add(name.replace("-", "_"))
    return roots


def test_the_registry_declared_requirements_match_their_import_trees() -> None:
    """N1, both directions: a task declares exactly the extras its own module tree imports.

    The reading this replaces is V2-24's: fifteen of nineteen tasks failed from a wheel with no
    remedy named, and the failure mode was silent because `run --list` advertised the study and
    said nothing about what it needed. A one-directional guard would not have caught it either --
    `requires: base` on every task is consistent with "no task declares an extra it does not use".
    So the sets are compared symmetrically, and both sides are printed.
    """
    from quantrisk.experiments.registry import EXTRA_MODULES, TASKS, requirement_label

    base_roots = _base_dependency_roots() | set(sys.stdlib_module_names)
    extra_of = {module: extra for extra, modules in EXTRA_MODULES.items() for module in modules}
    derived: dict[str, frozenset[str]] = {}
    undeclared: dict[str, list[str]] = {}
    for task in TASKS:
        reached = _imported_roots(task.module)
        assert reached, (
            f"{task.task_id}: the walk found no import at all, so a comparison over it would be "
            "vacuous -- the module may have moved without the registry noticing"
        )
        derived[task.task_id] = frozenset(extra_of[root] for root in reached if root in extra_of)
        undeclared[task.task_id] = sorted(
            root for root in reached if root not in extra_of and root not in base_roots
        )

    print(f"derived requirements for {len(derived)} tasks:")
    for task in TASKS:
        print(
            f"  {task.task_id:32s} derived={sorted(derived[task.task_id]) or ['base']!s:24s} "
            f"declared={requirement_label(task)}"
        )
    assert any(derived.values()), (
        "no task's tree reaches any optional module, so the two comparisons below would both pass "
        "by absence"
    )
    assert not any(undeclared.values()), (
        "a task imports a module that neither the base dependencies nor a declared extra accounts "
        f"for, so no install line could provide it: { {k: v for k, v in undeclared.items() if v} }"
    )

    over = {
        task.task_id: sorted(task.requires - derived[task.task_id])
        for task in TASKS
        if task.requires - derived[task.task_id]
    }
    under = {
        task.task_id: sorted(derived[task.task_id] - task.requires)
        for task in TASKS
        if derived[task.task_id] - task.requires
    }
    assert not over, (
        "these tasks declare an extra their import tree never reaches, so the install line would "
        f"ask for something they do not use: {over}"
    )
    assert not under, (
        "these tasks need an extra they do not declare, which is the V2-24 failure: a wheel would "
        f"run them and fail inside the study naming no remedy: {under}"
    )
