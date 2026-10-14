"""The falsification plants, kept out of the file that interprets them.

#94's reason is mechanical: `run_mutation_suite.py` requires an anchor to occur exactly once in its
target, and a plant whose anchor is a line of the harness would find that line twice -- once in the
code and once in its own entry -- so the case is refused before it runs and the guard behind it can
only be shown red by hand. Phase 34 demonstrated `Harness.uv` dropping its isolation argument that
way, and a demonstration is not re-run when the plumbing changes. Here the list is data, the
interpreter is separate, and a plant can point at the interpreter's own line.

`scripts/` is not a package, so this module is loaded by file path by both readers: the harness, and
`tests/python/test_mutation_suite.py` through it. Nothing else imports it.
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
        anchor="`10.31×` in the artifact now in the tree",
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
        anchor="2026-10-09T04:54:37+00:00",
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
        anchor="carries 99 numbered entries",
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
        anchor="# 447 tests collected offline",
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
        anchor="and 516 pytest tests with the validation",
        replacement="and 456 pytest tests with the validation",
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
        anchor="95 artifacts, 7{,}211{,}281 bytes",
        replacement="94 artifacts, 7{,}211{,}281 bytes",
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
        anchor="\ndate-released: 2026-10-09",
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
        anchor="experiments/fifth\\_order\\_crossing\\_map/run.py",
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
        anchor="# 77/77 planted defects rejected",
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
    Mutation(
        identifier="fifth-order-radius-judged-by-another-orders-range",
        kind="prose",
        path="experiments/fifth_order_crossing_map/run.py",
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
        path="experiments/fifth_order_crossing_map/run.py",
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
        path="scripts/derive_fifth_order_partials.py",
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
        anchor="oracles installed, 447 collected without them",
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
        path="experiments/second_book_crossing_map/run.py",
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
        anchor="# 516 pytest tests with the `oracles` extra here",
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
        anchor="Nine release tags exist",
        replacement="Eight release tags exist",
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
        anchor="\nversion: 1.8.0",
        replacement="\nversion: 1.9.9",
        # The anchor is newline-anchored because `version: 1.8.0` also occurs indented, inside
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
        anchor="`docs/limitations.md` (99 entries)",
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
        anchor="versus 3,787,943 paths/s in an equivalent pure-Python loop",
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
        anchor='r"(?<![A-Za-z\\d#.])"',
        replacement='r"(?<![A-Za-z\\d#])"',
        # The exclusion added when the matrix's `cvxpy 1.9.3 are oracles` was read as 9.3 oracles.
        # Loosening the lookbehind does not raise; it silently hands the inventory a version number
        # and a slice of `1.000`, which is how an extractor teaches a reader to ignore its list.
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
        path="scripts/rewrap_docstrings.py",
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
        path="scripts/rewrap_docstrings.py",
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
        # files` stops being a claim of twenty-two and is read as a claim about two of them, because
        # the shorter branch still completes the tail. The self-test compares the shipped rule with
        # exactly this narrowing, so the generation is what fails rather than the prose.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_the_claim_extractor_reads_percentages_and_refuses_labels"
        ),
        claim="the spelled alternatives come from the table the guards resolve through",
    ),
    Mutation(
        identifier="spelled-rule-widened-to-a-document-nobody-classified",
        kind="prose",
        path="tests/python/test_artifact_metadata.py",
        anchor='_SPELLED_DOCUMENTS = ("README.md", "docs/reproducibility.md")',
        replacement="_SPELLED_DOCUMENTS = _MARKDOWN_INVENTORY",
        # #95's staging is the review decision: 22 spelled claims sit in the matrix and 14 in the
        # rehearsal sheet, none of them classified. A rule switched on corpus-wide would report the
        # inventory complete while silently stopping answering for those claims, so the wider read
        # has to red here -- and the extractor self-test's staging assertion reddens with it.
        guard=(
            "tests/python/test_artifact_metadata.py::"
            "test_every_countable_claim_in_the_readme_and_reproducibility_is_owned_or_declared"
        ),
        claim="a document joins the spelled inventory only after its claims answer for themselves",
    ),
    Mutation(
        identifier="harness-spawns-a-guard-subprocess-without-a-bytecode-prefix",
        kind="prose",
        path="scripts/run_mutation_suite.py",
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
)
