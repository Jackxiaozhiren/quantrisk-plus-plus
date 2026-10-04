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

Usage::

    uv run python scripts/run_mutation_suite.py --list
    uv run python scripts/run_mutation_suite.py --kind prose --verbose
    uv run python scripts/run_mutation_suite.py --only volga-uses-its-own-square

"""

from __future__ import annotations

import argparse
import hashlib
import re
import signal
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

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


@dataclass(frozen=True)
class Mutation:
    """One planted defect and the single guard that must reject it."""

    identifier: str
    kind: str
    path: str
    anchor: str
    replacement: str
    guard: str
    claim: str


MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        identifier="note-prints-a-slope-the-artifact-doesnt",
        kind="prose",
        path="docs/analysis/two_factor_error_bound.md",
        anchor="1.9975",
        replacement="1.9976",
        guard=(
            "tests/python/test_two_factor_bound.py::"
            "test_every_figure_the_finding_and_the_note_quote_is_in_the_artifact"
        ),
        claim="the crash-ray slope in the analysis note is owned by the artifact, not typed",
    ),
    Mutation(
        identifier="readme-claims-a-narrower-speedup-band",
        kind="prose",
        path="README.md",
        anchor="`7.77×`",
        replacement="`8.00×`",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_documented_speedup_ranges_contain_the_current_measurement"
        ),
        claim="the documented ratio range is the real spread, not a remembered one",
    ),
    Mutation(
        identifier="fourth-order-docstring-quotes-a-stale-crossing-radius",
        kind="prose",
        path="experiments/fourth_order_crossing_map/run.py",
        anchor="worst 0.00162",
        replacement="worst 0.00152",
        guard=(
            "tests/python/test_fourth_order_crossing_map.py::"
            "test_the_module_docstring_figures_are_the_ones_the_artifact_holds"
        ),
        claim="the producer's own docstring quotes the radius the artifact measured",
    ),
    Mutation(
        identifier="readme-quotes-a-stale-speedup",
        kind="prose",
        path="README.md",
        anchor="`8.69×`",
        replacement="`8.70×`",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_quote_the_performance_figures_the_artifact_actually_holds"
        ),
        claim="the README's present-tense figure is the artifact's current measurement",
    ),
    Mutation(
        identifier="bindings-declare-a-name-the-binary-cannot-serve",
        kind="prose",
        path="bindings/python_bindings.cpp",
        anchor='pricing.def("black_scholes_vol_cross_derivatives"',
        replacement='pricing.def("black_scholes_vol_cross_derivatives_plus"',
        guard=(
            "tests/python/test_extension_surface_parity.py::"
            "test_every_name_the_bindings_declare_is_exposed_by_the_binary"
        ),
        claim="every pybind registration in the source resolves in the imported extension",
    ),
    Mutation(
        identifier="architecture-declares-a-file-that-isn't-there",
        kind="prose",
        path="docs/architecture.md",
        anchor="stress,special}.py",
        replacement="stress,special}.py · python/quantrisk/analytics.py",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_path_the_architecture_document_declares_exists"
        ),
        claim="the layout block describes the tree, as finding 33 required",
    ),
    Mutation(
        identifier="readme-undercounts-the-limitation-register",
        kind="prose",
        path="README.md",
        anchor="carries 82 numbered entries",
        replacement="carries 78 numbered entries",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_limitations_agree_with_the_file"
        ),
        claim="the limitation count in prose is the register's, not a remembered number",
    ),
    Mutation(
        identifier="readme-overcounts-the-cpp-suite",
        kind="prose",
        path="README.md",
        anchor="# 204 C++ tests",
        replacement="# 205 C++ tests",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_cpp_tests_agree_with_the_build"
        ),
        claim="the C++ count in prose is what CTest actually lists",
    ),
    Mutation(
        identifier="reproducibility-overcounts-the-suite",
        kind="prose",
        path="docs/reproducibility.md",
        anchor="all 17 members",
        replacement="all 18 members",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_suite_members_agree_with_the_registry"
        ),
        claim="the suite's member count is owned by its registry",
    ),
    Mutation(
        identifier="core-declares-a-function-nobody-binds",
        kind="prose",
        path="cpp/include/quantrisk/pricing/black_scholes.hpp",
        anchor="[[nodiscard]] bool is_degenerate(const MarketParams &market);",
        replacement=(
            "[[nodiscard]] bool is_degenerate(const MarketParams &market);\n"
            "[[nodiscard]] bool unbound_probe(const MarketParams &market);"
        ),
        guard=(
            "tests/python/test_extension_surface_parity.py::"
            "test_every_core_function_the_core_marks_reachable_is_bound_or_disclaimed"
        ),
        claim=(
            "a core function neither the bindings nor a marker accounts for is a defect, not a gap"
        ),
    ),
    Mutation(
        identifier="reproduction-policy-silences-a-gated-verdict",
        kind="prose",
        path="experiments/fourth_order_crossing_map/results/fourth_order_crossing_map.json",
        anchor='"noise_decided_verdicts": [\n      "rays",',
        replacement='"noise_decided_verdicts": [\n      "rays",\n      "columns",',
        guard=(
            "tests/python/test_fourth_order_crossing_map.py::"
            "test_the_exemption_does_not_reach_a_count_a_closed_form_or_a_shape_change"
        ),
        claim="the zero counts are not noise-decided, and the guard proves the exemption holds",
    ),
    Mutation(
        identifier="interview-doc-overcounts-the-offline-lane",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="# 396 Python tests",
        replacement="# 397 Python tests",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_documents_that_count_python_tests_count_the_ones_that_exist"
        ),
        claim="every spelling of the test count agrees with the same document's headline",
    ),
    Mutation(
        identifier="readme-inflates-the-report-by-a-chapter",
        kind="prose",
        path="README.md",
        anchor="twelve chapters",
        replacement="thirteen chapters",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_paper_chapters_agree_with_the_source"
        ),
        claim="the report's chapter count is counted from the LaTeX, not from memory",
    ),
    Mutation(
        identifier="matrix-heading-overcounts-its-own-paragraphs",
        kind="prose",
        path="docs/validation_matrix.md",
        anchor="## Five rows that need the prose to be honest",
        replacement="## Six rows that need the prose to be honest",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_validation_matrix_heading_counts_its_own_caveat_paragraphs"
        ),
        claim="a section heading counts the paragraphs under it, as finding from Phase 13's audit",
    ),
    Mutation(
        identifier="readme-miscounts-the-findings",
        kind="prose",
        path="README.md",
        anchor="The eight results worth reading are in",
        replacement="The nine results worth reading are in",
        guard=(
            "tests/python/test_two_factor_bound.py::"
            "test_the_findings_are_counted_wherever_they_are_counted"
        ),
        claim="the findings register is counted where it is counted, in both documents",
    ),
    Mutation(
        identifier="readme-miscounts-the-matrix-rows",
        kind="prose",
        path="README.md",
        anchor="is the full table — twenty-four rows over",
        replacement="is the full table — twenty-five rows over",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_validation_matrix_rows_agree_with_the_table"
        ),
        claim="the matrix's row count belongs to the table, not to the sentence quoting it",
    ),
    Mutation(
        identifier="matrix-numbers-two-rows-fourteen",
        kind="prose",
        path="docs/validation_matrix.md",
        anchor="| 15 |",
        replacement="| 14 |",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_validation_matrix_numbers_its_rows_once_and_in_order"
        ),
        claim="row numbers stay unique and contiguous, the defect Phase 13's two 13s shipped",
    ),
    Mutation(
        identifier="producer-docstring-quotes-a-stale-restdike-share",
        kind="prose",
        path="experiments/restrike_gamma_map/run.py",
        anchor="86 % of the local",
        replacement="92 % of the local",
        guard=(
            "tests/python/test_restrike_gamma_map.py::"
            "test_the_docstring_figures_and_counts_are_the_ones_the_artifact_holds"
        ),
        claim="the figures in an experiment's own docstring are re-derived from its artifact",
    ),
    Mutation(
        identifier="experiment-added-without-a-registry-entry",
        kind="tree",
        path="experiments/_mutation_probe/run.py",
        anchor="",
        replacement='"""Probe written by the mutation sweep; never committed."""\n',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_experiment_and_benchmark_script_on_disk_is_a_suite_member"
        ),
        claim="a runnable experiment nobody registers fails the registry's own completeness check",
    ),
    Mutation(
        identifier="experiment-results-the-evidence-freeze-never-saw",
        kind="tree",
        path="experiments/_mutation_probe/results/probe.json",
        anchor="",
        replacement='{"command": "probe written by the mutation sweep; never committed"}\n',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_manifest_hashes_every_experiment_results_directory"
        ),
        claim="an undeclared results directory is evidence the frozen manifest never hashed",
    ),
    Mutation(
        identifier="volga-uses-its-own-square",
        kind="core",
        path="cpp/src/pricing/black_scholes.cpp",
        anchor="cross.volga = vega * first * second / market.volatility;",
        replacement="cross.volga = vega * first * first / market.volatility;",
        guard="vanna and volga are finite differences of the published Greeks and of the price",
        claim="volga is the sigma-derivative of the published vega",
    ),
    Mutation(
        identifier="vanna-loses-its-sign",
        kind="core",
        path="cpp/src/pricing/black_scholes.cpp",
        anchor="cross.vanna = -terms.growth_discount",
        replacement="cross.vanna = terms.growth_discount",
        guard="vanna and volga are finite differences of the published Greeks and of the price",
        claim="vanna carries the sign the closed form derives",
    ),
    Mutation(
        identifier="mixed-partial-drops-a-term",
        kind="core",
        path="cpp/src/pricing/black_scholes.cpp",
        anchor="mixed.spot_spot_sigma = gamma * (first * second - 1.0) / sigma;",
        replacement="mixed.spot_spot_sigma = gamma * first * second / sigma;",
        guard="the three mixed third partials are finite differences taken at least two ways",
        claim="V_SSsigma is the sigma-derivative of gamma, every term included",
    ),
    Mutation(
        identifier="readme-undercounts-the-experiment-table",
        kind="prose",
        path="README.md",
        anchor="Twelve experiments, each answering",
        replacement="Eleven experiments, each answering",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_readme_experiment_count_agrees_with_the_experiments_on_disk"
        ),
        claim="the README's experiment sentence and its rows both belong to the tree",
    ),
    Mutation(
        identifier="report-counts-a-suite-the-registry-does-not-have",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="17 benchmark-suite members execute",
        replacement="16 benchmark-suite members execute",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_suite_members_agree_with_the_registry"
        ),
        claim="the report's suite count belongs to the registry, not to the prose",
    ),
    Mutation(
        identifier="report-counts-stale-python-tests",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="and 465 pytest tests with the validation",
        replacement="and 456 pytest tests with the validation",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_documents_that_count_python_tests_count_the_ones_that_exist"
        ),
        claim="the report states the collected total, in this environment or the offline one",
    ),
    Mutation(
        identifier="radius-reads-one-signed-column-at-a-time",
        kind="prose",
        path="experiments/second_book_crossing_map/run.py",
        anchor='if not all(row[f"{order}_within_tolerance"] for row in crossing):',
        replacement='if not any(row[f"{order}_within_tolerance"] for row in crossing):',
        guard=(
            "tests/python/test_second_book_crossing_map.py::"
            "test_rerunning_the_experiment_in_a_temporary_tree_reproduces_the_committed_numbers"
        ),
        claim="-0.15 and +0.15 are one candidate, and a radius may not contain a column it failed",
    ),
    Mutation(
        identifier="core-returns-a-value-and-says-nothing-about-it",
        kind="prose",
        path="cpp/include/quantrisk/math/normal.hpp",
        anchor="[[nodiscard]] Real normal_cdf(Real x);",
        replacement="Real normal_cdf(Real x);",
        guard=(
            "tests/python/test_extension_surface_parity.py::"
            "test_no_namespace_scope_declaration_is_left_unmarked"
        ),
        claim="every namespace-scope function states that its result is the point of calling it",
    ),
    Mutation(
        identifier="limitations-count-a-stale-core-surface",
        kind="prose",
        path="docs/limitations.md",
        anchor="the surface holds 110 namespace-scope",
        replacement="the surface holds 107 namespace-scope",
        guard=(
            "tests/python/test_extension_surface_parity.py::"
            "test_the_documents_that_count_the_core_surface_count_it_correctly"
        ),
        claim="the size of the core surface belongs to the scan, not to the sentence quoting it",
    ),
    Mutation(
        identifier="fifth-order-numerator-drops-a-cube",
        kind="core",
        path="cpp/src/pricing/black_scholes.cpp",
        anchor="+ 9.0 * first * first * first -",
        replacement="+ 8.0 * first * first * first -",
        guard="the six mixed fifth partials are slopes of partials the core already ships",
        claim="the order-fifth numerators are the polynomials the difference routes agree with",
    ),
)


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


def _run(command: Sequence[str], verbose: bool) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(command), cwd=REPO_ROOT, capture_output=True, text=True, check=False
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

    def uv(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return _run(("uv", "run", "--frozen", *arguments), self.verbose)

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
    try:
        for mutation in selected:
            print(f"- {mutation.identifier} ({mutation.kind}) ...", flush=True)
            results.append(run_one(mutation, harness))
            print(f"    {results[-1]['status']}", flush=True)
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
