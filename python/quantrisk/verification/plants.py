"""The falsification plants, kept out of the file that interprets them.

#94's reason is mechanical: `run_mutation_suite.py` requires an anchor to occur exactly once in its
target, and a plant whose anchor is a line of the harness would find that line twice -- once in the
code and once in its own entry -- so the case is refused before it runs and the guard behind it can
only be shown red by hand. Phase 34 demonstrated `Harness.uv` dropping its isolation argument that
way, and a demonstration is not re-run when the plumbing changes. Here the list is data, the
interpreter is separate, and a plant can point at the interpreter's own line.

The harness imports this module as `quantrisk.verification.plants`;
`tests/python/test_mutation_suite.py` reads its source text to prove the list stayed out of the
interpreter. Nothing else imports it.
"""

from __future__ import annotations

from dataclasses import dataclass


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
        replacement="`9.00×`",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_documented_speedup_ranges_contain_the_current_measurement"
        ),
        claim="the documented ratio range is the real spread, not a remembered one",
    ),
    Mutation(
        identifier="fourth-order-docstring-quotes-a-stale-crossing-radius",
        kind="prose",
        path="python/quantrisk/experiments/fourth_order_crossing_map/__init__.py",
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
        anchor="`7.89×` in the artifact now in the tree",
        replacement="`8.70×` in the artifact now in the tree",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_quote_the_performance_figures_the_artifact_actually_holds"
        ),
        claim="the README's present-tense figure is the artifact's current measurement",
    ),
    Mutation(
        identifier="report-cites-a-run-date-the-artifact-does-not-carry",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="2026-10-24T03:08:57+00:00",
        replacement="2026-09-29T08:58:31+00:00",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_quote_the_performance_figures_the_artifact_actually_holds"
        ),
        claim="the table's caption names the timestamp of the run it actually tabulates",
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
        anchor="carries 107 numbered entries",
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
        anchor="all 19 members",
        replacement="all 20 members",
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
        anchor="# 489 tests collected offline",
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
        anchor="is the full table — twenty-six rows over",
        replacement="is the full table — twenty-three rows over",
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
        path="python/quantrisk/experiments/restrike_gamma_map/__init__.py",
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
        identifier="architecture-layout-omits-a-shipped-subpackage",
        kind="prose",
        path="docs/architecture.md",
        anchor="python/quantrisk/{benchmarks,data,experiments,plotting,verification}/",
        replacement="python/quantrisk/{benchmarks,data,experiments,plotting}/",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_path_the_architecture_document_declares_exists"
        ),
        claim="the layout the document presents as the tree names every subpackage the tree ships",
    ),
    Mutation(
        identifier="installed-corpus-refusal-falls-back-to-silence",
        kind="prose",
        path="python/quantrisk/data/fixtures.py",
        anchor="        if root is None:\n            _refuse_unshipped(directory)",
        replacement="        if False:\n            _refuse_unshipped(directory)",
        guard=(
            "tests/python/test_data_layer_offline.py::"
            "test_an_install_without_the_corpus_refuses_instead_of_listing_nothing"
        ),
        claim="an install with no corpus refuses by naming it, not by answering with an empty list",
    ),
    Mutation(
        identifier="git-absence-reports-a-blank-instead-of-a-cause",
        kind="prose",
        path="python/quantrisk/experiments/metadata.py",
        anchor='            "git_unavailable_because": git_availability(),',
        replacement='            "git_unavailable_because": "unavailable",',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_an_absent_git_reports_which_kind_of_absence_it_is"
        ),
        claim="the record names which kind of git absence it is, not just that one is missing",
    ),
    Mutation(
        identifier="ci-lane-drops-a-declared-type-checked-directory",
        kind="prose",
        path=".github/workflows/ci.yml",
        anchor="uv run mypy python/quantrisk tools",
        replacement="uv run mypy python/quantrisk",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_ci_lane_that_runs_the_guards_fetches_what_they_read"
        ),
        claim="the surface the policy declares type-checked is the surface the lane checks",
    ),
    Mutation(
        identifier="formatter-census-sees-a-page-no-commit-declares",
        kind="tree",
        path="experiments/_mutation_probe/page.md",
        anchor="",
        replacement="# Probe page written by the mutation sweep; never committed.\n",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_formatter_walks_exactly_the_tracked_files_of_the_kinds_it_accepts"
        ),
        claim="a Markdown file neither tracked nor ignored moves the formatter's published count",
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
        anchor="Fourteen experiments, each answering",
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
        anchor="19 benchmark-suite members execute",
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
        anchor="and 558 pytest tests with the validation",
        replacement="and 458 pytest tests with the validation",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_documents_that_count_python_tests_count_the_ones_that_exist"
        ),
        claim="the report states the collected total, in this environment or the offline one",
    ),
    Mutation(
        identifier="report-counts-a-manifest-the-freeze-does-not-have",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="95 artifacts, 7{,}210{,}363 bytes",
        replacement="94 artifacts, 7{,}210{,}363 bytes",
        # The report's §Limitations restatement of the freeze was `v1.1.0`'s totals and shipped in
        # six releases, while its own headline paragraph said 94 two pages earlier; the guard reads
        # `totals` from the manifest, so one digit here is enough to redden it.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_report_states_the_manifest_the_freeze_produced"
        ),
        claim="the report's manifest sentence is the frozen manifest's own totals",
    ),
    Mutation(
        identifier="citation-declares-a-release-date-the-tag-does-not-carry",
        kind="prose",
        path="CITATION.cff",
        anchor="\ndate-released: 2026-10-20",
        replacement="\ndate-released: 2027-01-01",
        # The last field of the citation asset, and the only one whose producer is an event rather
        # than a file: the annotated tag's tagger date. Newline-anchored because `date-released`
        # occurs once at top level and could otherwise collide with a reference entry. This plant
        # is only decidable where the clone carries tags -- a checkout at depth 1 has none, and the
        # guard says so and skips, which is why the sweep runs on the full clone.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_release_date_the_citation_declares_is_the_tag_that_cut_it"
        ),
        claim="the release date a downloadable citation states is the date its own tag was cut",
    ),
    Mutation(
        identifier="document-states-an-unowned-speedup-band",
        kind="prose",
        path="docs/model_cards/portfolio_covariance_and_optimisation.md",
        anchor="1.13×–1.26× across cells",
        replacement="7.77×–8.70× across cells",
        # The census's own defect class: a document that states a speedup spread and appears in
        # neither the policed list nor the dated list. A model card is the natural target because
        # nothing has ever read its numbers -- no guard references the file at all -- so the plant
        # puts a superseded band into a document no gate was looking at.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_document_that_prints_a_speedup_band_is_policed_or_declared_dated"
        ),
        claim="every document printing a speedup spread is policed or declared dated",
    ),
    Mutation(
        identifier="dated-band-record-brought-up-to-date",
        kind="prose",
        path="docs/release_notes_v1.4.0.md",
        anchor="`7.77×`–`8.70×` (11.9% spread)",
        replacement="`7.77×`–`10.31×` (32.6% spread)",
        # The other half of the rule. A dated exemption is only honest while the record still
        # prints a superseded spread; rewrite it to the current band and the document is making a
        # living claim under cover of an exemption written for a dead one, which is the way a
        # declaration turns decorative.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_document_that_prints_a_speedup_band_is_policed_or_declared_dated"
        ),
        claim="a dated band record stays a dated record, or joins the policed set",
    ),
    Mutation(
        identifier="living-document-quotes-a-superseded-spread",
        kind="prose",
        path="docs/reproducibility.md",
        anchor="(32.6% spread)",
        replacement="(11.9% spread)",
        # Phase 32 policed the band's two edges and left the percentage beside them transcribed;
        # this is that figure's defect class. The 11.9 % is not invented -- it is the spread of the
        # superseded `7.77x`-`8.70x` band, so the plant puts a true number from the wrong revision
        # into a living sentence, which is how finding 55's mechanism actually arrives.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_living_documents_quote_the_spread_percentage_the_history_produces"
        ),
        claim="a quoted spread percentage is the one the committed readings produce",
    ),
    Mutation(
        identifier="pinned-spread-constant-disagrees-with-the-history",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='SPEEDUP_SPREADS = {"python": 32.6,',
        replacement='SPEEDUP_SPREADS = {"python": 99.9,',
        # The derivation guard's only reachable defect lives in the guard itself: the pinned
        # constant and the recomputed spread are different sources, and nothing but a planted
        # drift proves the comparison runs. 99.9 % is outside anything the artifact measured,
        # the derivation disagreeing with the pin rather than a rounding argument.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_documented_spread_percentages_are_the_committed_historys"
        ),
        claim="the pinned spread equals (max - min) / min over every committed reading",
    ),
    Mutation(
        identifier="report-drops-an-experiment-from-its-own-account",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="python/quantrisk/experiments/fifth_order_crossing_map",
        replacement="docs/analysis/fifth\\_order\\_crossing\\_map.md",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_registered_experiment_is_named_in_the_report"
        ),
        claim="every experiment the suite registers is described by the report",
    ),
    Mutation(
        identifier="report-quotes-a-stale-order-five-headline",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="widens the radius on 2 of the 5",
        replacement="widens the radius on 3 of the 5",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_report_states_the_order_five_headline_the_artifact_holds"
        ),
        claim="the report's order-five paragraph renders the artifact's headline fields",
    ),
    Mutation(
        identifier="docs-command-comment-counts-superseded-plants",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="# 178/178 planted defects rejected",
        replacement="# 34/34 planted defects rejected",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_a_command_line_that_counts_plants_counts_the_declared_ones"
        ),
        claim="a command line that annotates the sweep's verdict names the list the harness holds",
    ),
    Mutation(
        identifier="radius-reads-one-signed-column-at-a-time",
        kind="prose",
        path="python/quantrisk/experiments/second_book_crossing_map/__init__.py",
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
    Mutation(
        identifier="fifth-order-radius-judged-by-another-orders-range",
        kind="prose",
        path="python/quantrisk/experiments/fifth_order_crossing_map/__init__.py",
        anchor='widest = own_fits["worst_distance_inside_own_radius"][order]',
        replacement='widest = own_fits["worst_distance_inside_quartic_radius"][order]',
        guard=(
            "tests/python/test_fifth_order_crossing_map.py::"
            "test_a_radius_is_judged_only_by_columns_inside_it"
        ),
        claim="a radius is judged only by the columns inside that radius, not by another order's",
    ),
    Mutation(
        identifier="fifth-order-sums-drop-the-book-quantity",
        kind="prose",
        path="python/quantrisk/experiments/fifth_order_crossing_map/__init__.py",
        anchor="for o in book.options()) * book.quantity",
        replacement="for o in book.options()) * 1.0",
        # Not the sums test: that one recomputes the sums from the bindings itself, so a producer
        # edit cannot reach it. The reproduction test is the one that consumes what this function
        # returns -- the planted radius differs from the committed artifact, which is the link.
        guard=(
            "tests/python/test_fifth_order_crossing_map.py::"
            "test_rerunning_the_experiment_in_a_temporary_tree_reproduces_the_committed_numbers"
        ),
        claim="the quintic truncation is built on the book's own sums, position for position",
    ),
    Mutation(
        identifier="artifact-publishes-a-book-sum-the-core-does-not",
        kind="prose",
        path="experiments/fifth_order_crossing_map/results/fifth_order_crossing_map.json",
        anchor='"spot_spot_spot_sigma_sigma": -78.60804475268505,',
        replacement='"spot_spot_spot_sigma_sigma": -78.60904475268505,',
        # The counterpart to the producer-edit plant above: this guard compares the artifact against
        # the bindings, so the only thing that can turn it red is an artifact whose sums are not the
        # core's.
        guard=(
            "tests/python/test_fifth_order_crossing_map.py::"
            "test_the_core_sums_behind_the_quintic_term_are_the_shipped_ones"
        ),
        claim="the quintic truncation's book sums are the shipped core's, to the last bit",
    ),
    Mutation(
        identifier="fifth-order-note-quotes-a-stale-widening-count",
        kind="prose",
        path="docs/analysis/fifth_order_crossing_map.md",
        anchor="widens the radius on 2 of 5 books",
        replacement="widens the radius on 3 of 5 books",
        guard=(
            "tests/python/test_fifth_order_crossing_map.py::"
            "test_the_note_figures_are_the_artifacts_own"
        ),
        claim="the note's headline count is the artifact's, re-counted from the rows",
    ),
    Mutation(
        identifier="derivation-prefactor-exponent-off-by-one",
        kind="prose",
        path="python/quantrisk/verification/fifth_order_partials.py",
        anchor="quotient = value * v_value**4 / prefactor",
        replacement="quotient = value * v_value**3 / prefactor",
        # Nothing but the derivation gate can see this: the difference-route tests are banded at
        # 1e-3 relative and the C++ routes at 1e-8, and the identity check runs at 60 working
        # digits, so a wrong prefactor power is a floor-of-precision failure everywhere else and a
        # hard failure here.
        guard=(
            "tests/python/test_fifth_order_partials.py::"
            "test_the_derivation_command_agrees_at_the_precision_floor"
        ),
        claim="the derived numerators meet the exact derivative at the precision floor",
    ),
    Mutation(
        identifier="readme-quotes-a-stale-assertion-total",
        kind="prose",
        path="README.md",
        anchor="204 C++ tests, 548,368 assertions",
        replacement="204 C++ tests, 548,000 assertions",
        # CTest counts tests, so the assertion total is invisible to every other C++ guard: the
        # only producer is the Catch2 binary's summary line, and nothing compared a document to it
        # until Phase 25.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_cpp_assertions_count_the_binarys_own"
        ),
        claim="the C++ assertion and case totals are the compiled binary's own",
    ),
    Mutation(
        identifier="report-quotes-a-count-the-offline-probe-refutes",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="oracles installed, 489 collected without them",
        replacement="oracles installed, 400 collected without them",
        # The other count guard sees only the environment it runs in, so with the oracles in
        # place it cannot tell whether an oracle-free quotation is stale. The probe guard can,
        # and this is the defect shape it exists to catch.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_offline_test_count_is_measurable_before_the_runner"
        ),
        claim="the oracle-free count is what the probe measures, not what a document remembers",
    ),
    Mutation(
        identifier="report-adds-an-unowned-numeric-claim",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="This report describes the design, implementation and validation of QuantRisk++,",
        replacement=(
            "This report describes 41 modules of the design, implementation and validation "
            "of QuantRisk++,"
        ),
        # The abstract is the paragraph the inventory reads with no citation and no declaration, so
        # a number inserted there has to be classified before it can ship. Phase 23 shipped a stale
        # count in this same paragraph because every older guard over the document matched only the
        # phrasing it was written for.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_countable_claim_in_the_report_is_owned_or_declared"
        ),
        claim=(
            "each countable claim in the report is owned by a named guard, cited to a frozen "
            "artifact, or declared with a reason"
        ),
    ),
    Mutation(
        identifier="release-note-cites-a-digest-its-file-does-not-carry",
        kind="prose",
        path="docs/release_notes_v1.7.0.md",
        anchor="229c21a64c6ae190d21665e420e0a449dcfdb62f08eaa8f9bbe023a61ba60c3c",
        replacement="0" * 64,
        # The snapshot is the only reason a saved release body is evidence: a reader restoring the
        # page verifies against this number. Phase 27 wrote the wrong one for exactly this file --
        # the hash of the text before the trailing newline -- so the digest a note cites is now
        # required to be the file's own hash.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_digest_a_release_note_cites_is_its_files_own"
        ),
        claim="a digest a release note cites for a saved body is that file's own hash",
    ),
    Mutation(
        identifier="sixth-book-ranking-is-not-the-order-the-rule-sorts-in",
        kind="prose",
        path="experiments/sixth_book_crossing_map/results/sixth_book_crossing_map.json",
        anchor='      "rank": 12,',
        replacement='      "rank": 3,',
        guard=(
            "tests/python/test_sixth_book_crossing_map.py::"
            "test_the_selection_rule_is_the_order_the_scan_prints"
        ),
        claim="the ranking the artifact publishes is the order the rule's own ratio produces",
    ),
    Mutation(
        identifier="sixth-book-note-quotes-a-radius-the-run-did-not-produce",
        kind="prose",
        path="docs/analysis/sixth_book_crossing_map.md",
        anchor="| candidate T=3y sig=0.45 q=0.05 | 0.2 → 0.3 → 0.3 | 1.000 | **yes** | 0.0024 |",
        replacement=(
            "| candidate T=3y sig=0.45 q=0.05 | 0.2 → 0.3 → 0.4 | 1.333 | **yes** | 0.0024 |"
        ),
        # The replacement is internally consistent -- 0.3 to 0.4 is a factor of 1.333 -- so only
        # the artifact can say the book never reached 0.4: a note whose numbers are plausible and
        # wrong is the shape this guard exists for.
        guard=(
            "tests/python/test_sixth_book_crossing_map.py::"
            "test_the_note_figures_are_the_artifacts_own"
        ),
        claim="the note's book rows are the artifact's own radii, factors, edge flags and ratios",
    ),
    Mutation(
        identifier="sixth-book-grid-bound-claim-reads-a-narrower-grid",
        kind="prose",
        path="python/quantrisk/experiments/second_book_crossing_map/__init__.py",
        anchor="GRID_EDGE = max(abs(delta) for delta in DELTAS)",
        replacement="GRID_EDGE = 0.2",
        # The sixth book's whole message is that its radius could not rise on the ladder that was
        # swept. Narrow what the code calls the edge and the artifact's grid flag stops matching the
        # radii it was computed from, which is the only way to show that statement is about the grid
        # rather than a label copied from the run.
        guard=(
            "tests/python/test_sixth_book_crossing_map.py::"
            "test_a_verdict_bounded_by_the_grid_says_so"
        ),
        claim="the grid-bound flag tracks the ladder the radii were swept on",
    ),
    Mutation(
        identifier="readme-states-an-unowned-module-count",
        kind="prose",
        path="README.md",
        anchor="numbered entries grouped by phase.",
        replacement="numbered entries grouped by phase; 41 core modules are named in them.",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_countable_claim_in_the_readme_and_reproducibility_is_owned_or_declared"
        ),
        claim="a countable claim in README has an owner, a citation or a stated reason",
    ),
    Mutation(
        identifier="readme-cites-a-suite-key-the-registry-dropped",
        kind="prose",
        path="README.md",
        anchor="| `fifth_order_crossing_map` |",
        replacement="| `fifth_order_crossing_map_v2` |",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_countable_claim_in_the_readme_and_reproducibility_is_owned_or_declared"
        ),
        claim=(
            "a findings row is cited through a key the registry resolves to a frozen artifact, not "
            "through a string that merely looks like a member"
        ),
    ),
    Mutation(
        identifier="reproducibility-quotes-a-superseded-pytest-total",
        kind="prose",
        path="docs/reproducibility.md",
        anchor="# 558 pytest tests with the `oracles` extra here",
        replacement="# 494 pytest tests with the `oracles` extra here",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_documents_that_count_python_tests_count_the_ones_that_exist"
        ),
        claim=(
            "the command annotation carries the figure the prose two lines below it carries -- the "
            "stale twin this phase's extension was written to catch"
        ),
    ),
    Mutation(
        identifier="readme-quotes-an-identity-count-the-cli-does-not-run",
        kind="prose",
        path="README.md",
        anchor="# 7 identity checks",
        replacement="# 9 identity checks",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_identity_checks_the_cli_runs_are_the_ones_the_documents_count"
        ),
        claim="the validate command's check count is the installed CLI's own",
    ),
    Mutation(
        identifier="report-counts-release-tags-the-object-store-does-not-carry",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="Ten release tags exist",
        replacement="Nine release tags exist",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_report_lists_the_release_tags_the_repository_carries"
        ),
        claim="the report's enumeration of its own releases is the object store's, not a memory",
    ),
    Mutation(
        identifier="citation-declares-a-version-the-package-does-not",
        kind="prose",
        path="CITATION.cff",
        anchor="\nversion: 1.9.0",
        replacement="\nversion: 1.9.9",
        # The anchor is newline-anchored because `version: <version>` also occurs indented, inside
        # the `references` block, and a bare anchor would occur twice -- the class finding 49
        # records for every prose plant. This file is one of the four assets a release attaches,
        # so a citation naming a version the package does not build is downloadable and was,
        # until this plant, uncheckable by anything in the repository.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_version_string_the_project_declares_is_one_number_not_four"
        ),
        claim="one release version, spelled the same in the packaging, the build, the lock, the "
        "citation and the prose",
    ),
    Mutation(
        identifier="report-source-edited-without-a-rebuild",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="\\section{Limitations}",
        replacement="\\section{Limitations register}",
        # The defect #90 registered: the tex moves and the render does not. The heading is the
        # anchor because it is stable across releases -- an anchor on a count or a tag name would be
        # disarmed by the next phase's own sync, which is finding 49's class and happened seven
        # times in Phase 30 alone.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_committed_report_pdf_is_bound_to_the_sources_that_rendered_it"
        ),
        claim="the build record still names the bytes the document is made of",
    ),
    Mutation(
        identifier="report-source-edited-without-a-rebuild-seen-from-the-render",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="\\section{Limitations}",
        replacement="\\section{Limitations register}",
        # The same defect against the other guard: the binding can be satisfied by
        # editing the record with the tex, and only re-typesetting notices that the
        # shipped page no longer says what the source says. Hand-proved before it was
        # written down (Phase 31 §5): a self-consistent forged record left the binding
        # green and this guard red.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_rebuilding_the_report_from_the_committed_source_typesets_the_same_text"
        ),
        claim="a re-render of the committed source typesets the text the shipped PDF carries",
    ),
    Mutation(
        identifier="report-record-names-a-digest-the-pdf-does-not-carry",
        kind="prose",
        path="paper/technical_report.build.json",
        anchor='"pdf_sha256": "',
        replacement='"pdf_sha256": "00',
        # Anchored on the key rather than a digest value: `pdf_sha256` changes on every honest
        # rebuild, so a value-anchored plant would disarm itself the next time anyone typesets.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_committed_report_pdf_is_bound_to_the_sources_that_rendered_it"
        ),
        claim="the record describes the render that is actually in the tree",
    ),
    Mutation(
        identifier="ci-lane-drops-the-history-its-guards-read",
        kind="prose",
        path=".github/workflows/ci.yml",
        anchor="          fetch-depth: 0",
        replacement="          fetch-depth: 1",
        # Phase 33 made the workflow load-bearing: with a depth-limited checkout the history- and
        # tag-keyed guards do not fail there, they skip with a named reason, and the lane still
        # prints success. The configuration it checks is correct today, so this plant is the only
        # way to show the guard watches the file rather than restating it.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_ci_lane_that_runs_the_guards_fetches_what_they_read"
        ),
        claim="the job that runs the guards fetches the history and tags they read",
    ),
    Mutation(
        identifier="sheet-restates-the-question-set-at-the-wrong-size",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="22 questions in four groups",
        replacement="24 questions in four groups",
        # The rehearsal sheet's opening line counts a set that lives in another file, and nothing
        # read either until this phase. The plant is the cheapest way to show the guard compares
        # the count with `PROJECT_SPEC.md` rather than with the sheet's own heading tally.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_rehearsal_sheet_reproduces_the_question_set_it_cites"
        ),
        claim="the question set the sheet cites is the size the brief states",
    ),
    Mutation(
        identifier="sheet-provenance-cell-quotes-a-stale-register-count",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="`docs/limitations.md` (107 entries)",
        replacement="`docs/limitations.md` (84 entries)",
        # The defect this phase actually found: the sheet's prose said 94 while its own
        # claim-provenance table said 84, three phases behind, and the guard that owns the register
        # count read only the prose spelling. The plant re-opens the cell's spelling.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_limitations_agree_with_the_file"
        ),
        claim="every spelling of the register count, the table's parenthetical too, is the file's",
    ),
    Mutation(
        identifier="sheet-quotes-a-path-rate-the-artifact-does-not-measure",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="versus 4,453,163 paths/s in an equivalent pure-Python loop",
        replacement="versus 3,787,944 paths/s in an equivalent pure-Python loop",
        # The sheet states three rates in running prose beside the current band, and a superseded
        # fourth beside the words that say it is history. Proving the phrase patterns distinguish
        # them is what keeps `21,130,162 paths/s a loaded desktop has shown` from being certified
        # by the reading next to it.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_quote_the_performance_figures_the_artifact_actually_holds"
        ),
        claim="each rate the sheet prints in running prose is the artifact's own measurement",
    ),
    Mutation(
        identifier="sheet-states-a-case-gap-the-collected-pair-does-not-give",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="instead of the 69 cases they",
        replacement="instead of the 70 cases they",
        # "four oracle-gated modules collapse into four skip records instead of the 69 cases they
        # hold" is the two collected totals spoken as a difference, in a document outside the
        # inventory. Nothing compared the difference with the pair above it.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_documents_that_count_python_tests_count_the_ones_that_exist"
        ),
        claim="the cases the gated modules hold is the sheet's own pair of totals subtracted",
    ),
    Mutation(
        identifier="extractor-accepts-a-phase-label-as-a-countable-claim",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='_LABEL_WORDS = ("Phase",)',
        replacement="_LABEL_WORDS: tuple[str, ...] = ()",
        # The label filter is an exclusion, and an exclusion's red is a document the inventory
        # invents work for: with the list empty, `pinned in the Phase 2 test files` becomes a claim
        # about two files again and the report's declared list no longer covers it. The self-test
        # also refuses an empty list, so the filter cannot be deleted into vacuity.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_extractor_reads_percentages_and_refuses_labels"
        ),
        claim="a number that closes a namespace name is not a quantity the inventory asks about",
    ),
    Mutation(
        identifier="extractor-slices-a-number-out-of-a-dotted-token",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='_CLAIM_EXCLUDE_CHARS = r"A-Za-z\\d#.-"',
        replacement='_CLAIM_EXCLUDE_CHARS = r"A-Za-z\\d#-"',
        # The exclusion added when the matrix's `cvxpy 1.9.3 are oracles` was read as 9.3 oracles.
        # Loosening the lookbehind does not raise; it silently hands the inventory a version number
        # and a slice of `1.000`, which is how an extractor teaches a reader to ignore its list.
        # The `.` is lifted out of the middle of the class here, leaving the dash trailing where it
        # is still a literal, so this narrows one exclusion rather than corrupting the set.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_countable_claim_in_the_readme_and_reproducibility_is_owned_or_declared"
        ),
        claim="a claim's number starts a token rather than continuing one",
    ),
    Mutation(
        identifier="unlisted-document-states-a-band-without-its-unit",
        kind="tree",
        path="docs/_mutation_probe_band.md",
        anchor="",
        replacement=(
            "# Probe written by the mutation sweep; never committed.\n\n"
            "The C++ core runs `7.77–8.70` times the pure-Python loop on this machine.\n"
        ),
        # The old shape saw a spread only when both edges carried the unit, so a document writing
        # `7.77–8.70` was not a printer at all: neither policed, nor declared, nor reported. A
        # united version of this file would have been caught before this phase too, which is why the
        # planted sentence drops the units -- the defect must be one only the new shape can see.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_document_that_prints_a_speedup_band_is_policed_or_declared_dated"
        ),
        claim="a band is a band whether or not either edge carries its unit",
    ),
    Mutation(
        identifier="record-of-todays-band-quietly-states-a-superseded-one",
        kind="prose",
        path="docs/release_bodies/v1.8.0-body-2026-10-09.md",
        anchor="`7.77×–10.31×`",
        replacement="`7.77×–8.88×`",
        # The exemption this file holds is the fragile kind: it is dated but holds no superseded
        # spread, because the release it records is the one that produced today's band. That status
        # has to end on its own, so the guard requires the file to still print the band the tree
        # carries -- and rewriting the band to a superseded one under the same exemption is the only
        # way to show the check is live rather than a name on a list.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_document_that_prints_a_speedup_band_is_policed_or_declared_dated"
        ),
        claim="an exemption for a record stating today's band ends when it states another one",
    ),
    Mutation(
        identifier="rewrap-tool-accepts-the-rewrite-it-exists-to-refuse",
        kind="prose",
        path="tools/rewrap_docstrings.py",
        anchor="    if signature(after) != signature(source):",
        replacement="    if signature(after) == signature(source):",
        # The promoted tool's whole claim is its proof, and a proof that appends a problem when
        # nothing changed is as useless as one that appends nothing: it reddens an honest re-wrap
        # and waves through a rewrite that ate a word. Inverting the comparison is the mistake a
        # later edit can actually make while every printed line still says `whitespace-only`.
        guard="tests/python/test_rewrap_docstrings.py::"
        "test_the_rewrite_moves_line_breaks_and_nothing_else",
        claim="a re-wrap is accepted only when the folded parse is identical",
    ),
    Mutation(
        identifier="rewrap-tool-hardcodes-a-wider-line",
        kind="prose",
        path="tools/rewrap_docstrings.py",
        anchor='            return int(line.split("=", 1)[1].strip())',
        replacement='            return int(line.split("=", 1)[1].strip()) + 20',
        # The tool reads the project's line length rather than carrying its own, so that a
        # change to the gate moves the tool. Adding a fudge factor keeps the printed report
        # tidy -- `lines still longer than 120: []` -- while the files it writes violate E501.
        guard="tests/python/test_rewrap_docstrings.py::"
        "test_the_tool_takes_its_width_from_the_configuration_not_from_itself",
        claim="the tool wraps at the width ruff enforces, read from pyproject.toml",
    ),
    Mutation(
        identifier="readme-restates-a-spelled-member-count-the-registry-refutes",
        kind="prose",
        path="README.md",
        anchor="quietly skipping six members",
        replacement="quietly skipping four members",
        # The register's reader has resolved `six` through SPELLED_NUMBERS since Phase 22, but the
        # number was written in words, so the claim inventory could not see it at all (#95) -- which
        # is how this phrase sat at four for 25 phases while the registry already declared five.
        # Restoring the stale figure is the defect the widening exists to catch.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_suite_members_agree_with_the_registry"
        ),
        claim="the members --require-all keeps from skipping is the registry's `requires` count",
    ),
    Mutation(
        identifier="enumeration-count-disagrees-with-the-list-below-it",
        kind="prose",
        path="README.md",
        anchor="Four rows in the full matrix are the ones",
        replacement="Three rows in the full matrix are the ones",
        # The defect Phase 38's own reader found: the front page said three while listing four, and
        # no guard could see the sentence because its number was a word. The count is derived from
        # the bullets now, so this edit reddens instead of waiting for a human to recount.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_their_own_enumerations_agree_with_their_lists"
        ),
        claim="a spelled enumeration is the count of the items printed under it",
    ),
    Mutation(
        identifier="spelled-rule-stops-being-generated-from-the-number-table",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='_SPELLED_WORDS = "|".join(sorted(SPELLED_NUMBERS, key=len, reverse=True))',
        replacement=(
            '_SPELLED_WORDS = "|".join(\n'
            '    sorted((w for w in SPELLED_NUMBERS if w != "twenty-two"), key=len, reverse=True)\n'
            ")"
        ),
        # Dropping one key from the generated alternation does not raise: `twenty-two committed
        # files` stops being a claim of twenty-two. Before #100 the narrowed rule read it as a claim
        # about two of them; with the hyphen excluded it reads no claim at all, which is the quieter
        # failure -- a published quantity that simply stops being policed. Either way the cause is a
        # rule that stopped being generated from the table, and the self-test compares the shipped
        # rule with exactly this narrowing.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_extractor_reads_percentages_and_refuses_labels"
        ),
        claim="the spelled alternatives come from the table the guards resolve through",
    ),
    Mutation(
        identifier="report-stops-reading-spelled-claims",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor="claims = _extract_claims(flat, spelled=True)",
        replacement="claims = _extract_claims(flat)",
        # #95's rollout finished with the report (Phase 43), so the staging plant's original
        # mutation -- widening the document list -- became the shipped state and had to be replaced
        # by its inverse: switching the report's spelled reading back off. The report's own guard
        # stays green under that edit, because every *digit* claim is still classified; the only
        # reader of the regression is property 5's pin, which reads the report guard's call keywords
        # and demands the spelled reading stay on. Same lesson as the 91/92 sweep: the named
        # guard is the one that reads the mutated line.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_extractor_reads_percentages_and_refuses_labels"
        ),
        claim="a document that joined the spelled inventory does not quietly leave it",
    ),
    Mutation(
        identifier="harness-spawns-a-guard-subprocess-without-a-bytecode-prefix",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor=(
            'return _run(("uv", "run", "--frozen", *arguments), '
            "self.verbose, self.next_environment())"
        ),
        replacement='return _run(("uv", "run", "--frozen", *arguments), self.verbose)',
        # The guard behind this one asserts that *every* subprocess the sweep spawns carries a fresh
        # prefix, so its defect is in the plumbing -- and while the plumbing and the plant list
        # shared one file, a plant naming that line found it twice (the code and its own entry) and
        # was refused before running. Phase 34 could only show it red by editing the file, running
        # the node by hand, and restoring it: a demonstration that CI never re-runs. #94's move is
        # what turns that demonstration into this row.
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_every_subprocess_the_harness_runs_a_guard_in_is_bytecode_isolated"
        ),
        claim="no guard step bypasses the isolation, because one named call site carries it",
    ),
    Mutation(
        identifier="extractor-reads-a-hyphenated-compound-tail-as-a-quantity",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='_CLAIM_EXCLUDE_CHARS = r"A-Za-z\\d#.-"',
        replacement='_CLAIM_EXCLUDE_CHARS = r"A-Za-z\\d#."',
        # Taking `-` out of the exclusion does not raise either: it hands back the two phantoms #100
        # measured -- `Level-1 identities` read as one identity, `best of 1 %` as one
        # step -- and the self-test's property 6 compares the shipped rule with precisely
        # this loosening and names
        # them, so the exclusion cannot be dropped or quietly narrowed.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_extractor_reads_percentages_and_refuses_labels"
        ),
        claim="a number after a hyphen is the second half of a compound, not a count of the noun",
    ),
    Mutation(
        identifier="sheet-counts-rays-the-crossing-map-did-not-measure",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="along four rays scaled down",
        replacement="along five rays scaled down",
        # The spelled inventory's value is that the words answer to an artifact rather than to
        # another document: the map publishes its own `rays_number_of`, so a sheet that says five is
        # refuted by the frozen file and not by a reader's memory (#95).
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_crossing_maps_shape_agree_with_the_frozen_artifacts"
        ),
        claim="a spelled count of the map's shape is compared with what the map published",
    ),
    Mutation(
        identifier="sheet-counts-books-the-five-book-experiment-did-not-measure",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="The five books were chosen to span",
        replacement="The six books were chosen to span",
        # The sixth book exists in this tree (`experiments/sixth_book_crossing_map/`), which is
        # exactly why the claim needs the artifact rather than a directory listing: the sentence
        # is about the five-book study's own `books_measured`, and a reader who retyped it to
        # match the newer experiment would be writing a different claim.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_crossing_maps_shape_agree_with_the_frozen_artifacts"
        ),
        claim="the book count is that experiment's headline, not a count of its directories",
    ),
    Mutation(
        identifier="sheet-counts-a-radius-family-the-artifact-does-not-publish",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="that book's two radii",
        replacement="that book's three radii",
        # The count and the pair beside it are read together: with three claimed, the guard
        # reddens on the number of `radii_*` tables the artifact publishes, before the values.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_crossing_maps_shape_agree_with_the_frozen_artifacts"
        ),
        claim="how many radii a book carries is what the artifact's headline tables say",
    ),
    Mutation(
        identifier="sheet-claims-a-third-route-to-the-same-statement",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="Two equivalent routes to the same statement",
        replacement="Three equivalent routes to the same statement",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_their_own_enumerations_agree_with_their_lists"
        ),
        claim="a count of the paragraph's own `Xxx route:` labels is counted from those labels",
    ),
    Mutation(
        identifier="sheet-numbers-more-cases-than-it-enumerates",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="The two cases I would be pushed on",
        replacement="The three cases I would be pushed on",
        # The producer is the `(1)` / `(2)` sequence inside the same paragraph, and the assertion
        # compares the whole sequence with the count, so an extra case is caught whether or not the
        # answer goes on to number it.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_their_own_enumerations_agree_with_their_lists"
        ),
        claim="an inline enumeration has to be numbered as far as the count it states",
    ),
    Mutation(
        identifier="sheet-counts-two-tests-re-executing-the-benchmark-script",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="And one test re-executes the",
        replacement="And two tests re-execute the",
        # The suite is the producer: exactly one module spawns the published script with the flag.
        # The replacement keeps the guard's pattern matching, so the *comparison* reddens rather
        # than the presence check; the tree is restored from the recorded digest either way.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_documents_that_count_python_tests_count_the_ones_that_exist"
        ),
        claim="a behavioural count of the suite is counted from the suite, not from the prose",
    ),
    Mutation(
        identifier="sheet-reads-the-refreeze-count-as-a-longer-history",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="across the twenty-three re-freezings",
        replacement="across the twenty-four re-freezings",
        # The same committed history the note in `docs/reproducibility.md` counts three times
        # over; the sheet is its fourth spelling, and a re-freeze moves all four together or the
        # guard says which one lagged.
        guard=(
            "tests/python/test_artifact_metadata.py::test_the_performance_guards_are_not_vacuous"
        ),
        claim="every spelled count of the frozen reading history is compared with that history",
    ),
    Mutation(
        identifier="declaration-anchor-for-the-backtest-families-stops-matching",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="the two tests specified here",
        replacement="the two tests specified below",
        # A declaration is only as good as the sentence it is anchored to. Moving the words without
        # touching the list makes the anchor stale, and the inventory guard reports an
        # exemption that no longer excuses anything -- the check that caught #100's two phantoms.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_countable_claim_in_the_readme_and_reproducibility_is_owned_or_declared"
        ),
        claim="a declaration has to sit beside the sentence that made it necessary",
    ),
    Mutation(
        identifier="matrix-reads-a-row-count-the-table-does-not-carry",
        kind="prose",
        path="docs/validation_matrix.md",
        anchor="It has twenty-six rows rather",
        replacement="It has twenty-five rows rather",
        # The row count already had a guard that read `twenty-six`; what it lacked was a spelling
        # the inventory could credit, so the claim sat unowned while its producer ran on every
        # gate. The
        # plant moves the count down rather than up on purpose: `twenty-seven` is past the numeral
        # table's ceiling (#97) and would fail as a KeyError, which proves less than a disagreement.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_validation_matrix_rows_agree_with_the_table"
        ),
        claim="the matrix's spelled row count is the table's own labels, not a remembered number",
    ),
    Mutation(
        identifier="matrix-heading-counts-more-caveats-than-it-holds",
        kind="prose",
        path="docs/validation_matrix.md",
        anchor="## Five rows that need the prose",
        replacement="## Six rows that need the prose",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_validation_matrix_heading_counts_its_own_caveat_paragraphs"
        ),
        claim="a heading that counts its paragraphs is checked against the paragraphs under it",
    ),
    Mutation(
        identifier="matrix-counts-rays-the-two-factor-bound-fitted-on-three",
        kind="prose",
        path="docs/validation_matrix.md",
        anchor="2.0 on four rays, 3.0 on",
        replacement="2.0 on three rays, 3.0 on",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_studies_grids_agree_with_their_producers"
        ),
        claim="how many rays a slope was fitted along is the artifact's own ray block",
    ),
    Mutation(
        identifier="matrix-counts-markets-the-derivation-does-not-iterate",
        kind="prose",
        path="docs/validation_matrix.md",
        anchor="differentiation at 4.6e-15 on four markets",
        replacement="differentiation at 4.6e-15 on five markets",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_studies_grids_agree_with_their_producers"
        ),
        claim="a study's grid is counted from the loop that walks it, read as syntax",
    ),
    Mutation(
        identifier="matrix-counts-fields-the-partials-module-defines-six",
        kind="prose",
        path="docs/validation_matrix.md",
        anchor="the six fields reached by",
        replacement="the seven fields reached by",
        # This is the plant for the sentence the phase found wrong: the matrix had said five fields
        # where the module defines six and five distinct parents. The corrected prose carries both
        # numbers, so a drift in either direction is a disagreement with a structure, not a reread.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_studies_grids_agree_with_their_producers"
        ),
        claim="the count of fields is the module's own literal, not the sentence's memory",
    ),
    Mutation(
        identifier="matrix-counts-parents-the-difference-routes-do-not-read",
        kind="prose",
        path="docs/validation_matrix.md",
        anchor="across five fourth-order partials",
        replacement="across six fourth-order partials",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_studies_grids_agree_with_their_producers"
        ),
        claim="the distinct partials a route reads are counted from the route table",
    ),
    Mutation(
        identifier="report-counts-rays-the-restrike-fitted-on-three",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="of each of three rays the error",
        replacement="of each of two rays the error",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_report_counts_what_the_studies_and_the_gates_have"
        ),
        claim="a study's ray count in the report is the artifact's own ray block",
    ),
    Mutation(
        identifier="report-counts-joint-rays-the-bound-did-not-fit",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="windows for the four joint rays",
        replacement="windows for the five joint rays",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_report_counts_what_the_studies_and_the_gates_have"
        ),
        claim="the two-factor bound's ray count is the asymptotics block it publishes",
    ),
    Mutation(
        identifier="report-counts-columns-the-map-did-not-sweep",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="across the twelve columns it finds",
        replacement="across the eleven columns it finds",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_report_counts_what_the_studies_and_the_gates_have"
        ),
        claim="the crossing map's column count is the headline that names it",
    ),
    Mutation(
        identifier="report-counts-books-the-experiment-did-not-measure",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="on all five books, and its worst",
        replacement="on all six books, and its worst",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_report_counts_what_the_studies_and_the_gates_have"
        ),
        claim="the book count is the five-book experiment's own headline",
    ),
    Mutation(
        identifier="report-counts-fixtures-the-directory-outgrew",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="Sixteen committed fixtures of real responses",
        replacement="Fifteen committed fixtures of real responses",
        # This is the plant for the count the phase found false at thirteen: the directory outgrew
        # the sentence by three fixtures, and nothing could see it until the spelled reader reached
        # the report. The corrected count is owned by the directory listing itself.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_report_counts_what_the_studies_and_the_gates_have"
        ),
        claim="a fixture count is what the fixtures directory holds",
    ),
    Mutation(
        identifier="report-counts-identity-checks-the-gate-does-not-run",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="checks seven identities",
        replacement="checks eight identities",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_report_counts_what_the_studies_and_the_gates_have"
        ),
        claim="the validate gate's check count is its own code, read as syntax",
    ),
    Mutation(
        identifier="report-grows-the-suite-by-the-wrong-member-count",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="the suite has grown by seven members since",
        replacement="the suite has grown by six members since",
        # The value the report shipped for four phases: twelve plus six is eighteen, the registry
        # carries nineteen, and no gate could see either spelled number until the report read them.
        # The owner is the relation, so this edit reddens without any constant being retyped.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_report_counts_what_the_studies_and_the_gates_have"
        ),
        claim="a growth sentence has to agree with the registry minus its own quoted past",
    ),
    Mutation(
        identifier="matrix-row-count-survives-the-old-ceiling",
        kind="prose",
        path="docs/validation_matrix.md",
        anchor="It has twenty-six rows rather",
        replacement="It has twenty-seven rows rather",
        # #97's own prediction was that a twenty-seventh row would fail as a KeyError, because the
        # flat numeral table stopped at twenty-six. The table generates to ninety-nine now, so this
        # plant must fail as a *disagreement* -- the guard reads twenty-seven and compares it with
        # the twenty-six labels the table carries -- which is the ceiling's closure, demonstrated.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_validation_matrix_rows_agree_with_the_table"
        ),
        claim="a spelled row count above the old flat dict's limit disagrees instead of crashing",
    ),
    Mutation(
        identifier="report-counts-files-past-the-old-ceiling",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="sixty report files, one per phase",
        replacement="sixty-one report files, one per phase",
        # Phase 43 wrote this count in digits because forty-three was past the ceiling; the
        # generated table retires that fallback, and the spelled form is owned again. The plant
        # moves the count one up so the disagreement, not a resolution failure, is what reddens.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_report_counts_what_the_studies_and_the_gates_have"
        ),
        claim="a report count above twenty-six is owned spelled, as the fallback promised",
    ),
    Mutation(
        identifier="numeral-table-loses-its-hyphenated-compounds",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='f"{_SPELLED_TENS[tens]}-{_SPELLED_ONES[ones]}"',
        replacement='f"{_SPELLED_TENS[tens]}{_SPELLED_ONES[ones]}"',
        # The compound is the generation's product, and the hyphen is the corpus's own spelling of
        # one (`twenty-two committed files`). Dropping it unnames every compound key, so the
        # sentence in property 7 stops being two claims and the generation control names the loss.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_extractor_reads_percentages_and_refuses_labels"
        ),
        claim="a compound numeral exists because the generation builds it, hyphen and all",
    ),
    Mutation(
        identifier="owned-credit-names-a-guard-that-does-not-exist",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor=(
            'r"(\\d+)/(\\d+) benchmark-suite members executed": (\n'
            '        "test_documents_that_count_the_suite_members_agree_with_the_registry",'
        ),
        replacement=(
            'r"(\\d+)/(\\d+) benchmark-suite members executed": (\n'
            '        "test_documents_that_count_the_suite_members_agree_with_the_regisTRY",'
        ),
        # The old credit check was `pattern in holder_source`, and the table sits in the holder's
        # file -- so an entry naming a guard that does not exist passed by construction. The
        # syntax check resolves the named function before it looks at anything else.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_countable_claim_in_the_readme_and_reproducibility_is_owned_or_declared"
        ),
        claim="an owned pattern's owner is a function that exists",
    ),
    Mutation(
        identifier="owned-credit-outlives-its-reader",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='r"(\\d+)/(\\d+) benchmark-suite members executed", sheet',
        replacement='r"(\\d+)/(\\d+) benchmark-suite members ran", sheet',
        # Moving the search away from the pattern leaves the entry matching the document (so the
        # dead-pattern check stays green) while no guard searches with it any more -- precisely the
        # state the old substring check scored as owned, and the syntax check refuses by name.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_countable_claim_in_the_readme_and_reproducibility_is_owned_or_declared"
        ),
        claim="a credit lasts exactly as long as the guard that searches with its pattern",
    ),
    Mutation(
        identifier="owned-credit-loses-the-helper-it-reads-through",
        kind="prose",
        path="tests/python/test_fifth_order_partials.py",
        anchor=r"worst relative over (\d+) markets",
        replacement=r"worst relative across (\d+) markets",
        # The derivation entries are searched inside `_quoted_identity_floor`, a helper the named
        # guard calls -- the credit is real because of the call closure, and this plant cuts the
        # helper's literal away to prove the closure is what carries it. The pattern is a
        # `_MARKDOWN_OWNED` key, so the reader that polices it is the documents' inventory guard,
        # not the report's.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_countable_claim_in_the_readme_and_reproducibility_is_owned_or_declared"
        ),
        claim="a guard owns what it searches for through the helpers it calls",
    ),
    # Phase 46: the fail-fast stop, its three ways of lying, and the flag that opts out of it. The
    # anchors are lines of the interpreter itself, which #94's split is what makes legal -- the list
    # is data in another file, so each of these occurs once where it is applied.
    Mutation(
        identifier="sweep-keeps-going-past-an-escaped-defect",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor=r'if not arguments.all and results[-1]["status"] != CAUGHT:',
        replacement=r'if False and not arguments.all and results[-1]["status"] != CAUGHT:',
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_an_escaped_defect_stops_the_sweep_and_names_what_it_never_ran"
        ),
        claim="an escaped defect stops the sweep at the plant",
    ),
    Mutation(
        identifier="sweep-stops-at-every-plant-not-just-an-escaped-one",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor=r'if not arguments.all and results[-1]["status"] != CAUGHT:',
        replacement=r"if not arguments.all:",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_a_sweep_that_needs_no_stop_prints_the_census_it_always_printed"
        ),
        claim="a clean sweep still runs the whole declared list",
    ),
    Mutation(
        identifier="sweep-stop-counts-what-ran-not-what-was-declared",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor=r"{skipped} of {len(selected)} declared plants",
        replacement=r"{skipped} of {len(results)} declared plants",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_an_escaped_defect_stops_the_sweep_and_names_what_it_never_ran"
        ),
        claim="the stop names its denominator as the declared list, not the plants already run",
    ),
    Mutation(
        identifier="sweep-census-counts-what-ran-not-what-was-declared",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor="{len(caught)}/{len(selected)} planted defects were rejected by their guard.",
        replacement="{len(caught)}/{len(results)} planted defects were rejected by their guard.",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_an_escaped_defect_stops_the_sweep_and_names_what_it_never_ran"
        ),
        claim="the census denominator is the declared list, not the cycles that happened to finish",
    ),
    Mutation(
        identifier="sweep-all-flag-inverts-its-own-meaning",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor='        "--all",\n        action="store_true",',
        replacement='        "--all",\n        action="store_false",',
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_all_flag_runs_every_declared_plant_after_a_stop_would_fire"
        ),
        claim="--all keeps going, which is the census a phase record quotes",
    ),
    # Phase 47 (#99): a claim about a row has to be a claim about *that* row. The first plant is the
    # defect the entry recorded -- a citation moved to an adjacent row that exists, so every
    # existence check stays green. The second deletes a registry entry, and the third blinds the
    # shape regex so the guard is left comparing nothing.
    Mutation(
        identifier="row-claim-moved-to-an-adjacent-existing-row",
        kind="prose",
        path="README.md",
        anchor="**Row 15 is the other kind of weakness:**",
        replacement="**Row 14 is the other kind of weakness:**",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_claim_about_a_validation_matrix_row_describes_that_row"
        ),
        claim="a sentence that names a row says words that row's own cells contain",
    ),
    Mutation(
        identifier="row-claim-registry-drops-a-citation",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='    ("README.md", "13", "the real-data arm"),\n',
        replacement="",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_claim_about_a_validation_matrix_row_describes_that_row"
        ),
        claim="every claiming citation is classified, so the registry cannot quietly fall behind",
    ),
    Mutation(
        identifier="row-claim-shape-stops-matching-anything",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor=r"""[Rr]ow\s+(\d+[a-z]?)(?:,\s+the\s+[^,]{2,60},|\s+is\s+|\u2019s\s|'s\s)""",
        replacement=r"""[Rr]ow\s+(\d+[a-z]?)(?:never-the-shape-of-a-claim)""",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_claim_about_a_validation_matrix_row_describes_that_row"
        ),
        claim="the guard's denominator is asserted, so blinding the shape cannot read as agreement",
    ),
    # Phase 48 (#102): the corpus scores the rule, so each of the three ways that score can lie
    # has a plant -- a needle that no longer names a real unit, a noun list widened so the miss
    # ratchet must move, and the hyphen exclusion removed so a phantom reaches precision.
    Mutation(
        identifier="corpus-needle-stops-naming-a-sentence-in-its-document",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='("README.md", "618 shocks tested", ("618 shocks",)),',
        replacement='("README.md", "618 shocks measured", ("618 shocks",)),',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_rule_is_scored_against_sentences_whose_quantities_are_known"
        ),
        claim="corpus units come from the document, so an invented needle cannot score",
    ),
    Mutation(
        identifier="claim-rule-widens-its-noun-list-under-the-ratchet",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor=r"|stencils|spreads?|runs|readings?|re-freezings?|paths?",
        replacement=r"|stencils|spreads?|runs|readings?|re-freezings?|paths?|shocks?",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_rule_is_scored_against_sentences_whose_quantities_are_known"
        ),
        claim="improving recall has to move the frozen miss list on purpose, not by accident",
    ),
    Mutation(
        identifier="claim-rule-loses-its-hyphen-exclusion",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='_CLAIM_EXCLUDE_CHARS = r"A-Za-z\\d#.-"',
        replacement='_CLAIM_EXCLUDE_CHARS = r"A-Za-z\\d#."',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_rule_is_scored_against_sentences_whose_quantities_are_known"
        ),
        claim="a phantom claim is a precision failure, and the frozen list says so",
    ),
    # Phase 49 (#102's unbiased sample): the frame, the gold and the drawn indices each
    # have a plant, because a measurement is only as honest as the numbers that define it.
    Mutation(
        identifier="claim-sample-frame-stops-covering-the-documents",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor="_CLAIM_SAMPLE_FRAME_MIN = 26",
        replacement="_CLAIM_SAMPLE_FRAME_MIN = 900",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_rules_recall_and_precision_are_estimated_on_a_sample"
        ),
        claim="the frame is asserted to cover the documents before any rate is quoted",
    ),
    Mutation(
        identifier="claim-sample-gold-drops-its-only-hit",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='    420: ("five books",),',
        replacement="    420: (),",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_rules_recall_and_precision_are_estimated_on_a_sample"
        ),
        claim="an extracted phrase gold does not list is a phantom, even the only one",
    ),
    Mutation(
        identifier="claim-sample-redrawn-without-reannotating",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor="_CLAIM_SAMPLE_STEP = 42",
        replacement="_CLAIM_SAMPLE_STEP = 43",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_rules_recall_and_precision_are_estimated_on_a_sample"
        ),
        claim="the sampled indices are pinned, so the sample cannot move under stale gold",
    ),
    # Phase 50 (#101's precision denominator): the census and the closed-class block are two halves
    # of one claim -- the block is why the phantom list is empty, and the census is how anyone would
    # notice. Each direction gets a plant, including the refactor that looks like tidiness.
    Mutation(
        identifier="claim-modifier-slot-reopened-after-the-census",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='    r"\\s*%?\\s+"\n    + _MODIFIER_BLOCK\n',
        replacement='    r"\\s*%?\\s+"\n',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claims_a_document_prints_are_a_census_and_not_a_sample"
        ),
        claim="the census's empty phantom list is the block's own evidence: reopen the slot and a "
        "hit that is not a quantity returns to a document that says it has none",
    ),
    Mutation(
        identifier="closed-class-block-borrowed-a-citation-stopword",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='    "for",\n    "from",\n    "in",',
        replacement='    "for",\n    "from",\n    "further",\n    "in",',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_extractor_reads_percentages_and_refuses_labels"
        ),
        claim="the block is not `_CITATION_STOPWORDS`: `further` classifies a real count in the "
        "report, so the tidy-looking reuse would delete a claim instead of a phantom",
    ),
    Mutation(
        identifier="census-gold-recasts-a-real-count",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='    "582 rolling windows",',
        replacement='    "582 static windows",',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claims_a_document_prints_are_a_census_and_not_a_sample"
        ),
        claim="gold is read out of the document, so a count the document never prints reddens the "
        "census rather than quietly narrowing it",
    ),
    Mutation(
        identifier="precision-queue-drops-a-document",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='    "README.md": (_CENSUS_README_GOLD, _CENSUS_README_PHANTOMS),\n',
        replacement="",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claims_a_document_prints_are_a_census_and_not_a_sample"
        ),
        claim="every inventoried document is censused or pending, so a document cannot leave the "
        "queue by being deleted from it",
    ),
    # Phase 51 (#104): the collision refusal has two failure directions, and the destructive one
    # is a placement error this phase actually made. Both are registered so the mistake cannot be
    # re-made without a red guard.
    Mutation(
        identifier="claim-participle-head-refusal-dropped",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='    + r"(?:"\n    + _PARTICIPLE_HEAD_BLOCK\n    + r"[A-Za-z]+\\.?\\s+)?"',
        replacement='    + r"(?:[A-Za-z]+\\.?\\s+)?"',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_extractor_reads_percentages_and_refuses_labels"
        ),
        claim="without the participle-head block the rule reads `60 markets spread` again, so the "
        "frame property 9 pins stops landing on the markets",
    ),
    Mutation(
        identifier="claim-participle-head-refusal-hoisted-over-the-noun",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor=(
            '    r"\\s*%?\\s+"\n    + _MODIFIER_BLOCK\n    + r"(?:"\n'
            '    + _PARTICIPLE_HEAD_BLOCK\n    + r"[A-Za-z]+\\.?\\s+)?"'
        ),
        replacement=(
            '    r"\\s*%?\\s+"\n    + _MODIFIER_BLOCK\n    + r"(?!"\n'
            '    + _REPORT_NOUNS\n    + r"\\s+(?:spread|spanning)\\s)(?:[A-Za-z]+\\.?\\s+)?"'
        ),
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claims_a_document_prints_are_a_census_and_not_a_sample"
        ),
        claim="the same lookahead hoisted in front of the modifier group refuses the noun as well "
        "as the modifier, and the census is what notices: real counts disappear",
    ),
    Mutation(
        identifier="collision-sentence-leaves-the-corpus",
        kind="prose",
        path="paper/technical_report.tex",
        anchor="markets spread over the $(d_1, v)$ plane",
        replacement="markets laid over the $(d_1, v)$ plane",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_extractor_reads_percentages_and_refuses_labels"
        ),
        claim="the one phrase that earns the collision rule is pinned by name, so rewording it out "
        "of the report reddens the property instead of leaving the refusal unevidenced",
    ),
    # Phase 52 (#101's queue, #105): a census that has found a real phantom must be able to fail
    # when the phantom is reclassified, when gold quotes a phrase the file never prints, and when a
    # document is put back into the queue it has already left.
    Mutation(
        identifier="census-gold-phrase-filed-as-a-phantom",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor="_CENSUS_SHEET_PHANTOMS: tuple[str, ...] = ()",
        replacement='_CENSUS_SHEET_PHANTOMS = ("two radii",)',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claims_a_document_prints_are_a_census_and_not_a_sample"
        ),
        claim="no phantom is left to reclassify since Phase 56, so the disjointness branch is "
        "tested the other way: filing a gold phrase as a phantom too reddens the census",
    ),
    Mutation(
        identifier="census-gold-quotes-a-phrase-the-file-never-prints",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='    "12 artifacts",',
        replacement='    "12 artifact",',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claims_a_document_prints_are_a_census_and_not_a_sample"
        ),
        claim="gold is a transcription of what the document prints, so a phrase the file never "
        "produces reddens the census rather than being accepted as a near miss",
    ),
    Mutation(
        identifier="census-document-put-back-in-the-queue-it-left",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor="_PRECISION_PENDING: tuple[str, ...] = ()",
        replacement='_PRECISION_PENDING = (\n    "docs/interview_defense.md",\n)',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claims_a_document_prints_are_a_census_and_not_a_sample"
        ),
        claim="a document cannot be censused and pending at once, so re-queueing one that has been "
        "read is caught by the membership check rather than by the gold lists",
    ),
    # Phase 53 (#101's queue worked off, #105's second instance): the last two documents get the
    # same three directions tested -- a phantom forgotten, gold quoting a phrase the file never
    # prints, and a phrase filed as both a quantity and a phantom.
    Mutation(
        identifier="census-phantom-claimed-that-the-rule-no-longer-prints",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor="_CENSUS_REPORT_PHANTOMS: tuple[str, ...] = ()",
        replacement='_CENSUS_REPORT_PHANTOMS = ("3 path",)',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claims_a_document_prints_are_a_census_and_not_a_sample"
        ),
        claim="the truncation this list used to name is repaired, so claiming a phantom the rule "
        "no longer prints reddens the census -- a phantom list is measured against the hits",
    ),
    Mutation(
        identifier="census-matrix-gold-quotes-a-phrase-the-table-never-prints",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='    "six fields",',
        replacement='    "six fields of the book",',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claims_a_document_prints_are_a_census_and_not_a_sample"
        ),
        claim="each matrix entry transcribes a phrase the document prints, so an entry the "
        "table never produces fails the gold-is-a-subset check",
    ),
    Mutation(
        identifier="census-phrase-filed-as-quantity-and-phantom",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor="_CENSUS_REPORT_PHANTOMS: tuple[str, ...] = ()",
        replacement='_CENSUS_REPORT_PHANTOMS = ("106 recorded limitations",)',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claims_a_document_prints_are_a_census_and_not_a_sample"
        ),
        claim="the two lists are disjoint by construction, and the guard that enforces it is a "
        "different branch from the one that compares them with the hits",
    ),
    # ------------------------------------------------------------------ Phase 54
    Mutation(
        identifier="declaration-ledger-key-drags-off-the-declaration",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='("docs/reproducibility.md", "within the last one or", "two digits"): (',
        replacement='("docs/reproducibility.md", "within the last one or", "two digit"): (',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="the partition is a set comparison in both directions, and a key whose phrase drifts "
        "by one character is a pair the ledger no longer covers",
    ),
    Mutation(
        identifier="declaration-verdict-cites-a-quote-the-file-dropped",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='"record:docs/phase_reports/phase-09-research-api.md#310 pytest tests"',
        replacement='"record:docs/phase_reports/phase-09-research-api.md#310 pytest suite"',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="the quote presence branch and the number-in-quote branch are separate asserts, so a "
        "producer that stopped printing the cited sentence is caught even when the digits remain",
    ),
    Mutation(
        identifier="declaration-verdict-quotes-a-number-the-quote-omits",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='"card:docs/model_cards/heston.md#250 steps, inside sampling error"',
        replacement='"card:docs/model_cards/heston.md#steps, inside sampling error"',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="a quote that exists but does not print the number is not a producer of it, and that "
        "refusal is its own branch after the quote is found",
    ),
    Mutation(
        identifier="artifact-verdict-names-a-field-that-does-not-resolve",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor=(
            '    ("docs/interview_defense.md", "the equality control is bit-identity over", '
            '"30 joint moves"): (\n        "artifact:experiments/second_book_crossing_map/'
            'results/"\n        "second_book_crossing_map.json#control.control_moves_compared"'
        ),
        replacement=(
            '    ("docs/interview_defense.md", "the equality control is bit-identity over", '
            '"30 joint moves"): (\n        "artifact:experiments/second_book_crossing_map/'
            'results/"\n        "second_book_crossing_map.json#control.control_moves_compares"'
        ),
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="a field that has been renamed is reported as a producer that does not resolve, not "
        "as a disagreement about its value",
    ),
    Mutation(
        identifier="artifact-verdict-points-at-a-sibling-that-holds-another-number",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor=(
            '    ("paper/technical_report.tex", "over 30 joint moves", "30 joint moves"): (\n'
            '        "artifact:experiments/second_book_crossing_map/results/"\n'
            '        "second_book_crossing_map.json#control.control_moves_compared"'
        ),
        replacement=(
            '    ("paper/technical_report.tex", "over 30 joint moves", "30 joint moves"): (\n'
            '        "artifact:experiments/second_book_crossing_map/results/"\n'
            '        "second_book_crossing_map.json#control.v160_radius_quartic"'
        ),
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="the field resolves, so the only thing that can refuse it is the value comparison -- "
        "which is the check a digit-matching attribution would have passed",
    ),
    Mutation(
        identifier="declaration-category-outside-the-vocabulary",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='"none:prose-idiom, agreement in the last place',
        replacement='"none:prose-idioms, agreement in the last place',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="the category vocabulary is closed, so a row invented at the keyboard is refused "
        "rather than counted as a reason",
    ),
    Mutation(
        identifier="declaration-vocabulary-accretes-an-unused-category",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='_DECLARATION_CATEGORIES = (\n    "chosen-configuration",',
        replacement=(
            '_DECLARATION_CATEGORIES = (\n    "chosen-configuration",\n    "waiting-for-a-row",'
        ),
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="the vocabulary is policed in both directions, so a category nobody uses cannot be "
        "added now for the row someone expects to write later",
    ),
    Mutation(
        identifier="declaration-disclosure-drops-the-candidate-field-name",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor=(
            '        "candidate, `widening_factors`, counts how many factors widen the radius on '
            'this "'
        ),
        replacement=(
            '        "candidate is a radius-fit count, which says nothing about what the '
            'installed "'
        ),
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="a `none:` is only auditable when it names the one field it is refusing, so dropping "
        "that name from the reason is a finding rather than a rewording",
    ),
    Mutation(
        identifier="granularity-enumeration-names-an-undeclared-symbol",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='"granularity:family=kupiec_pof_test,christoffersen_independence_test,"',
        replacement='"granularity:family=kupiec_pof_test,christoffersen_independenc_test,"',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="the members of a granularity claim are read off the typed stubs as a syntax tree, "
        "so a symbol the extension does not declare is refused",
    ),
    Mutation(
        identifier="granularity-lists-the-count-the-sentence-claims",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='"christoffersen_conditional_coverage_test"',
        replacement='"granularity:family=kupiec_pof_test"',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="a row that lists exactly as many members as the sentence claims is not recording a "
        "granularity mismatch, and the guard refuses the kind rather than certifying an accident",
    ),
    # ------------------------------------------------------------------ Phase 56
    Mutation(
        identifier="participle-list-loses-the-verb-the-corpus-needs",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='_PARTICIPLE_HEADS = ("spread", "spanning")',
        replacement='_PARTICIPLE_HEADS = ("spanning",)',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_extractor_reads_percentages_and_refuses_labels"
        ),
        claim="the refusal is a word list, not a grammatical insight, so dropping the one verb the "
        "corpus actually uses brings `60 markets spread` back",
    ),
    Mutation(
        identifier="noun-list-not-widened-for-the-compound-heads",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='r"|stencils|spreads?|runs|readings?|re-freezings?|paths?|definitions|budgets"\n)',
        replacement='r"|stencils|spreads?|runs|readings?|re-freezings?|paths?"\n)',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claims_a_document_prints_are_a_census_and_not_a_sample"
        ),
        claim="the head cannot be taken as a head unless it is on the noun list, so un-widening it "
        "returns both truncations and the census gold no longer matches what the rule prints",
    ),
    Mutation(
        identifier="census-gold-still-lists-the-repaired-truncation",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='    "two radius definitions",\n    "two tests",',
        replacement='    "two radius",\n    "two tests",',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claims_a_document_prints_are_a_census_and_not_a_sample"
        ),
        claim="gold transcribes what the document prints under the shipped rule, so keeping the "
        "old truncation in the list fails the subset check rather than reading as a near miss",
    ),
    Mutation(
        identifier="convention-pair-loses-its-declared-anchor",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='    "convention bridge rather than derived, because the": (',
        replacement='    "convention bridge rather than derived, because the other": (',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_countable_claim_in_the_report_is_owned_or_declared"
        ),
        claim="a claim the widened rule revealed needs its own exemption, so an anchor that stops "
        "matching leaves the count unowned instead of silently dropping the row",
    ),
    Mutation(
        identifier="declaration-reading-retires-a-kind",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='_DECLARATION_READING: dict[str, int] = {\n    "artifact": 2,',
        replacement='_DECLARATION_READING: dict[str, int] = {\n    "artifact": 1,',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="the published distribution is compared with the rows, so a reading that moves "
        "without being retold is red rather than silently stale",
    ),
    # ------------------------------------------------------------------ Phase 55
    Mutation(
        identifier="card-verdict-moves-a-measurement-into-the-narrative-tier",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='"card:docs/model_cards/crr_binomial.md#absolute at N = 50"',
        replacement='"record:docs/model_cards/crr_binomial.md#absolute at N = 50"',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="a tier is read off the cited path, so calling a model card a narrative record is "
        "refused even though the quote and the number both still check out",
    ),
    Mutation(
        identifier="record-verdict-moves-an-origin-reading-into-the-card-tier",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='"record:docs/phase_reports/phase-09-research-api.md#310 pytest tests"',
        replacement='"card:docs/phase_reports/phase-09-research-api.md#310 pytest tests"',
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="the two tiers are disjoint prefixes, so a phase report cannot be promoted to a "
        "measurement producer by changing the word in front of it",
    ),
    Mutation(
        identifier="measurement-corpus-accretes-a-prefix-no-verdict-cites",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='_MEASUREMENT_CORPUS: dict[str, str] = {\n    "docs/model_cards/": (',
        replacement=(
            '_MEASUREMENT_CORPUS: dict[str, str] = {\n    "docs/measurement-notes/": "kept for "\n'
            '        "later",\n    "docs/model_cards/": ('
        ),
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="a declared corpus prefix that covers nothing the ledger cites is a guess about a "
        "future phase rather than a rule about this one, and the guard refuses it",
    ),
    Mutation(
        identifier="none-row-drops-the-corpus-file-it-has-to-name",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor=(
            '"Three benchmark fields hold 200000, and `docs/model_cards/heston.md` prints '
            '`200k paths` "'
        ),
        replacement=(
            '"Three benchmark fields hold 200000, and a model card prints the same digits for a "'
        ),
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="the disclosure is the whole content of a forced `none:` -- name the one file that "
        "matches and say why it is a different measurement, or the refusal is unevidenced",
    ),
    Mutation(
        identifier="corpus-disclosure-pin-stops-listing-the-forced-row",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor="_MEASUREMENT_DISCLOSURES: dict[tuple[str, str, str], str] = {\n    (",
        replacement=(
            "_MEASUREMENT_DISCLOSURES: dict[tuple[str, str, str], str] = {\n"
            '    ("unused", "unused", "unused"): "docs/model_cards/heston.md",\n    ('
        ),
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="the firing set is compared with what the search derives, so an empty or padded pin "
        "reddens rather than quietly disabling the rule it is supposed to record",
    ),
    Mutation(
        identifier="clause-window-widened-until-every-file-matches",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor=(
            "    stop = break_re.search(text, end)\n"
            "    return text[lo : stop.start() if stop else len(text)]"
        ),
        replacement="    stop = break_re.search(text, end)\n    del stop\n    return text",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_declared_number_names_a_producer_or_records_that_none_exists"
        ),
        claim="widening the window to whole files does not blur the one forced row, it invents a "
        "second one: `12 artifacts` turns against the card that says `12 functions, 10 bound "
        "types`, and the in-loop pin comparison reddens because the derived firing set no longer "
        "agrees with `_MEASUREMENT_DISCLOSURES`",
    ),
    # ------------------------------------------------------------------ Phase 57
    Mutation(
        identifier="pairing-verdict-demands-the-singleton-103-rejected",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor="    if named in failing:",
        replacement="    if failing == {named}:",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_pairing_audit_reads_membership_of_the_failing_set"
        ),
        claim="#103's own criterion, put back: a plant whose guard shares a module structure with "
        "three other guards is honest, and requiring the failing set to be a singleton refuses "
        "43 of the 71 observable plants measured on `b2df36f`",
    ),
    Mutation(
        identifier="pairing-verdict-calls-a-quiet-name-paired",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor="    return MIS_PAIRED if failing else ESCAPED",
        replacement="    return PAIRED",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_pairing_audit_reads_membership_of_the_failing_set"
        ),
        claim="the audit's only finding is the named guard missing from the set, so a verdict that "
        "returns `paired` whatever the set holds cannot report one -- finding 86's plant "
        "would read as a pass",
    ),
    Mutation(
        identifier="pairing-failure-reader-keeps-the-node-id",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor='        match.group(1).split("::")[-1]',
        replacement="        match.group(1)",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_pairing_audit_reads_membership_of_the_failing_set"
        ),
        claim="membership is tested against the bare test name, so reading the whole `file::name` "
        "node id makes every guard look absent from its own failing set",
    ),
    Mutation(
        identifier="pairing-sample-lets-a-later-probe-plant-evict-a-runnable-one",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor="            blocked.setdefault(guard, reason)",
        replacement=(
            "            blocked.setdefault(guard, reason)\n            chosen.pop(guard, None)"
        ),
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_pairing_audit_samples_a_shared_guard_from_a_plant_that_can_run"
        ),
        claim="a guard is observable if any plant naming it can be run, so letting the last plant "
        "decide hands a guard the audit can read to the unreachable list and shrinks the census",
    ),
    Mutation(
        identifier="pairing-census-counts-an-unrunnable-module-as-observed",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor=(
            '    observed = [r for r in records if r["verdict"] in (PAIRED, MIS_PAIRED, ESCAPED)]'
        ),
        replacement="    observed = list(records)",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_pairing_audit_census_divides_by_what_it_observed"
        ),
        claim="the denominator of a membership claim is the number of modules that actually "
        "ran, and counting a collection error as an observation is how the first version of this "
        "tool printed `0 of 72` over 67 real samples",
    ),
    Mutation(
        identifier="pairing-census-scores-every-paired-plant-as-alone",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor='        "singleton": sum(1 for record in paired if record["size"] == 1),',
        replacement='        "singleton": len(paired),',
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_pairing_audit_census_divides_by_what_it_observed"
        ),
        claim="the wide-versus-lone split is the measurement that closed #103, so a census "
        "that scores every paired plant as alone reports the rejected equality criterion as the "
        "observed truth",
    ),
    Mutation(
        identifier="pairing-module-run-reads-a-collection-error-as-a-run",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor="        return ran, parse_failures(completed.stdout), parse_line_tracebacks(",
        replacement="        return True, parse_failures(completed.stdout), parse_line_tracebacks(",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_a_module_run_that_never_collected_is_not_read_as_an_escaped_plant"
        ),
        claim="pytest returns 2, 3, 4 and 5 for runs that never happened, and reading one "
        "of those as a run turns a broken module into a plant that escaped every guard",
    ),
    Mutation(
        identifier="pairing-sample-counts-a-shared-guard-twice",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor="        if guard not in order:\n            order.append(guard)",
        replacement="        order.append(guard)",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_pairing_audit_samples_one_plant_per_guard_and_names_the_rest"
        ),
        claim="25 guards are named by more than one plant, so appending every occurrence samples "
        "those guards repeatedly -- the census then counts 72 samples against 77 guards, and the "
        "membership ratio is divided by a denominator the run never produced",
    ),
    Mutation(
        identifier="pairing-sample-drops-the-unreachable-list",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor=(
            "    unreachable = [(guard, blocked[guard]) for guard in order if guard not in chosen]"
        ),
        replacement="    unreachable = []",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_pairing_audit_samples_one_plant_per_guard_and_names_the_rest"
        ),
        claim="this is #103's own silence one layer up: an audit that reports 71 of 71 guards "
        "paired while five guards were never observed reads as complete coverage, so the "
        "unreachable list has to be named or the denominator is a fiction",
    ),
    # ------------------------------------------------------------------ Phase 58
    Mutation(
        identifier="attribution-claims-every-plant-is-linked",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor="    if path in closure or Path(path).name in closure:",
        replacement="    if True:",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_plants_the_pairing_audit_cannot_attribute_are_named_and_pinned"
        ),
        claim="the residual is the whole content of #107's honest answer, so a rule that always "
        "says attributed reports coverage the text does not support",
    ),
    Mutation(
        identifier="attribution-forgets-which-lines-the-named-guard-owns",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor="        if Path(file_).name == Path(module).name and span[0] <= line <= span[1]:",
        replacement="        if Path(file_).name == Path(module).name:",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_pairing_audit_attributes_a_failure_to_the_named_guard_s_own_line"
        ),
        claim="the span test is what stops a neighbour's assertion being quoted as the plant's, "
        "which is finding 91 re-opened inside the new instrument",
    ),
    Mutation(
        identifier="line-reader-matches-the-traceback-style-pytest-did-not-print",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor=(
            '    for match in re.finditer(r"^(.+?):(\\d+): ((?:\\w+Error|Exception): .*)$", '
            "output, flags=re.M):"
        ),
        replacement=(
            '    for match in re.finditer(r"^E (.+?):(\\d+): (.*)$", output, flags=re.M):'
        ),
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_pairing_audit_reads_its_evidence_as_lines_and_not_as_a_sliced_transcript"
        ),
        claim="a reader written for `--tb=short` finds nothing in `--tb=line` output, and an empty "
        "attribution reads as a clean audit rather than as a broken reader",
    ),
    Mutation(
        identifier="reading-closure-visits-only-direct-children",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor="        for reference in ast.walk(node):",
        replacement="        for reference in ast.iter_child_nodes(node):",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_reading_closure_reaches_the_helpers_and_constants_a_guard_actually_reads"
        ),
        claim=(
            "a walk over only a node's direct children never reaches a name used inside a "
            "nested helper, so the closure loses the chain and calls a real pairing unlinkable"
        ),
    ),
    Mutation(
        identifier="reading-closure-stops-at-one-hop",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor="        if level >= depth:",
        replacement="        if level >= 1:",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_reading_closure_reaches_the_helpers_and_constants_a_guard_actually_reads"
        ),
        claim=(
            "a depth knob that is smaller than the corpus silently re-creates #103's static "
            "failure mode, where the reachability walk missed a nested helper"
        ),
    ),
    Mutation(
        identifier="pinned-residual-list-emptied",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor=(
            'UNATTRIBUTED_PLANTS = frozenset({"'
            'release-note-cites-a-digest-its-file-does-not-carry"})'
        ),
        replacement="UNATTRIBUTED_PLANTS = frozenset()",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_plants_the_pairing_audit_cannot_attribute_are_named_and_pinned"
        ),
        claim=(
            "an empty exemption list is a pinned set that no longer measures anything, so "
            "the plant that genuinely has no text link would pass as attributed"
        ),
    ),
    Mutation(
        identifier="module-run-drops-the-report-flag-the-attribution-needs",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor='                "--tb=line",',
        replacement='                "--tb=no",',
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_module_run_asks_pytest_for_the_per_assertion_lines_it_needs"
        ),
        claim=(
            "without the flag the audit still names the failing guards and reports every "
            "attribution as empty, which is the silence #107 exists to close"
        ),
    ),
    Mutation(
        identifier="pairing-closure-reads-the-text-after-the-plant-fired",
        kind="prose",
        path="python/quantrisk/verification/runner.py",
        anchor="closure_source = pristine if same_module",
        replacement="closure_source = mutated if same_module",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_the_pairing_audit_reads_the_closure_from_the_text_before_the_plant_fires"
        ),
        claim=(
            "a closure read from the edited text erases the link for the plant whose edit deletes "
            "the reference the closure follows, so the audit calls a real pairing unlinkable while "
            "the offline pin calls it linked"
        ),
    ),
    Mutation(
        identifier="citation-understates-the-limitation-register",
        kind="prose",
        path="CITATION.cff",
        anchor="and 107 numbered limitations record",
        replacement="and 55 numbered limitations record",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_documents_that_count_the_limitations_agree_with_the_file"
        ),
        claim=(
            "the citation file is uploaded as a release asset, and its abstract carried 55 for "
            "four releases while the register passed a hundred because nothing read this file"
        ),
    ),
    Mutation(
        identifier="sheet-state-line-names-a-superseded-phase",
        kind="prose",
        path="docs/interview_defense.md",
        anchor="Phases 0–58 shipped",
        replacement="Phases 0–43 shipped",
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_state_line_of_the_rehearsal_sheet_names_the_phases_the_repository_carries"
        ),
        claim=(
            "the shipped-phase range is a current claim about the report directory, and it sat at "
            "43 for fifteen phases with nothing on disk able to disagree with it"
        ),
    ),
    Mutation(
        identifier="ci-lane-stops-executing-the-documented-invocation",
        kind="prose",
        path=".github/workflows/ci.yml",
        anchor="        run: uv run quantrisk run --list\n",
        replacement="        run: uv run quantrisk --help\n",
        guard=(
            "tests/python/test_mutation_suite.py::"
            "test_a_documented_invocation_is_executed_verbatim_by_the_lane"
        ),
        claim=(
            "the step keeps running the command the contributor documentation prints, so a reader "
            "typing it gets what the lane gets rather than a paraphrase"
        ),
    ),
)
