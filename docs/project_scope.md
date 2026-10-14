# QuantRisk++ — Project Scope (Phase 0, frozen v0.1)

Date: 2026-09-25 · Status: **SPEC ONLY — nothing is implemented.**
This document answers the Phase 0 Gate: scope complete, math spec exists (see
`mathematical_specification.md`), validation protocol exists
(see `validation_protocol.md`), architecture diagram exists (see `architecture.md`),
and no unimplemented functionality is claimed.

## 1. Motivation

Graduate programs in Financial Engineering / Financial Mathematics / Quantitative
Finance / Applied Mathematics / Statistics / Data Science admit applicants who can
work **with** mathematical models — not just call ML libraries. QuantRisk++ is built
to demonstrate exactly that: a small, reproducible C++/Python engine where every
number is traceable to a definition, an implementation, a test, and a benchmark.

Anti-goal stated upfront: this is not a stock-prediction dashboard, not a trading
bot, and not an LLM wrapper. There are no return guarantees and no trading
recommendations anywhere in this project.

## 2. Central research question

> Can a compact, reproducible C++/Python quantitative risk engine reproduce
> analytical financial results, provide statistically valid risk estimates, and
> expose transparent numerical behavior across pricing, simulation, portfolio risk
> and stress testing?

Sub-questions (one per build phase; each must be answered with evidence, not prose):

1. (Phase 2) Does our Black-Scholes + CRR binomial code reproduce closed forms,
   put-call parity, and QuantLib within stated tolerances?
2. (Phase 3) Does our Monte Carlo engine exhibit the theoretical `O(1/√N)` error
   decay, correct 95% CI coverage, and measured variance reduction?
3. (Phase 4) Can we price path-dependent payoffs and simulate Heston dynamics with
   documented discretization bias and positivity behavior?
4. (Phase 5) Are VaR/ES estimators + Kupiec/Christoffersen backtests statistically
   valid on synthetic distributions before touching real data?
5. (Phase 6) Does our optimizer satisfy constraints, agree with PyPortfolioOpt/cvxpy
   on identical inputs, and degrade gracefully on singular covariance?
6. (Phase 7) Does every stress scenario map to explicit assumptions →
   reproducible transformation → portfolio impact → attribution?
7. (Phase 8–10) Is the whole pipeline reproducible offline with frozen evidence
   (SHA256 manifest) behind every number in the README?

## 3. Intended users

- The applicant (graduate-school portfolio + interview defense).
- Admissions reviewers / professors (3-minute README → validation matrix → report).
- Open-source peers who want a clean, small reference implementation with honest
  limitations (students, RSEs, quants).

## 4. Non-goals (explicit)

- No live trading, order execution, or portfolio advice.
- No price forecasting / alpha signals / "AI stock picker".
- No Web App / dashboard as the core value (a minimal CLI/demo only, Phase 9).
- No paid data, paid APIs, paid cloud, or proprietary solvers ($0 constraint).
- No unsupported models: everything without an oracle gets a written
  "validation weaker than …" disclaimer (Heston is the known case).
- No vanity metrics: any benchmark/speedup/coverage number must come from a
  script → raw result → artifact chain (see `validation_protocol.md`).

## 5. Architecture (summary; detail in `architecture.md`)

```text
Python research layer (orchestration, experiments, plotting, CLI)
        │  pybind11 bindings (thin, no numerics reimplemented)
        ▼
C++20 numerical core (pricing, MC/GBM/Heston, risk, portfolio, stress)
        │  Eigen (linalg) · Catch2/CTest (tests) · CMake (build)
        ▼
Validation oracles (QuantLib, PyPortfolioOpt/cvxpy, SciPy — reference only)
Experiments + evidence/ (CSV/JSON/plots + SHA256 manifest)
Optional data layer (SEC/FRED/CFTC, cached, offline fixtures for CI)
```

Layer rules (frozen):
1. Numerics live in C++20; Python orchestrates and analyzes.
2. Bindings are thin — no second implementation of the same formula.
3. Core never touches the network; data is optional and cached.
4. Every claim needs an artifact; artifacts are hashed in Phase 10.

## 6. Validation philosophy (summary; detail in `validation_protocol.md`)

Three levels, applied per component:

- **Level 1 — Analytical oracle:** closed form / parity / limiting behavior
  (e.g. BS formula, put-call parity, σ→0 / T→0 edges).
- **Level 2 — Independent open-source oracle:** live QuantLib / PyPortfolioOpt /
  cvxpy / SciPy comparison with recorded versions and tolerances.
- **Level 3 — Statistical convergence:** MC `O(1/√N)` slope fit, CI coverage,
  bootstrap uncertainty, backtest distributions.

Plus deterministic policy: `std::mt19937_64`, no global RNG state, recorded seeds,
`double` core precision, recorded compiler/OS/CPU/commit metadata, absolute +
relative tolerances chosen per test family (not tuned to force passes).

## 7. Cost constraint ($0 + AI tokens)

Allowed: local compute, GitHub + Actions free tier, SEC EDGAR, FRED/ALFRED free
API (env-var key, fixture fallback), CFTC public data, synthetic data, QuantLib,
Eigen, pybind11, Catch2, NumPy/SciPy, pandas/Polars, matplotlib, statsmodels,
scikit-learn, cvxpy + open-source solvers, PyPortfolioOpt. Anything requiring
payment gets replaced by a free alternative — never recommended to the user.

## 8. Phase map (from PROJECT_SPEC.md, abbreviated)

Phase 0 (this doc set) → 1 engineering skeleton → 2 BS/binomial/Greeks →
3 Monte Carlo → 4 path-dependent/Heston → 5 VaR/ES/backtesting →
6 portfolio optimization → 7 stress testing → 8 public data →
9 Python API/CLI → 10 validation matrix + frozen evidence + report + release.

Rule: one phase at a time; each phase ends with a Phase Report and stops.

## 9. Current status (honest, refreshed 2026-10-14; first written 2026-09-27)

| Item | Status |
|---|---|
| `docs/project_scope.md` (this file) | DONE (Phase 0) |
| `docs/ecosystem_research.md` | DONE (Phase 0) |
| `docs/mathematical_specification.md` v0.1 | DONE (Phase 0, spec only) |
| `docs/validation_protocol.md` | DONE (Phase 0) |
| `docs/architecture.md` (+ diagram) | DONE (Phase 0) |
| Phase 1 build/packaging/C++ core/bindings/tests/CI | DONE (`docs/phase_reports/phase-01-engineering-foundation.md`) |
| Phase 2 Black-Scholes, Greeks, CRR lattice, QuantLib benchmark, experiment | DONE (`docs/phase_reports/phase-02-deterministic-pricing.md`) |
| Phase 3 Monte Carlo engine, variance reduction, convergence + coverage, speed benchmark | DONE (`docs/phase_reports/phase-03-monte-carlo.md`) |
| Phase 4 Asian + barrier + Heston, oracle benchmark, model cards | DONE (`docs/phase_reports/phase-04-path-dependent-heston.md`) |
| Phase 5 VaR/ES estimators, bootstrap intervals, Kupiec + Christoffersen backtests | DONE (`docs/phase_reports/phase-05-market-risk.md`) |
| Phase 6 covariance estimators, mean-variance, max-Sharpe, ERC, CVaR, PyPortfolioOpt + cvxpy benchmark | DONE (`docs/phase_reports/phase-06-portfolio-optimisation.md`) |
| Phase 7 scenario/stress subsystem, three scenario kinds, attribution with residuals | DONE (`docs/phase_reports/phase-07-stress-testing.md`) |
| Phase 8 optional public data layer (EDGAR, FRED/ALFRED, CFTC) with provenance and offline fixtures | DONE (`docs/phase_reports/phase-08-public-data.md`) |
| Phase 9 research API facades, Python faces of all eight submodules, `quantrisk` CLI | DONE (`docs/phase_reports/phase-09-research-api.md`) |
| Phase 10 validation matrix, benchmark suite, evidence manifest, technical report, README, v1.0.0 release | DONE (`docs/phase_reports/phase-10-release.md`, `docs/validation_matrix.md`, `docs/reproducibility.md`) |
| Phase 11 real-data risk study: long-window FRED fixtures, out-of-sample VaR backtest on market data, coverage tests, bootstrap SE comparison, out-of-sample covariance ranking, three recorded refusals | DONE (`docs/phase_reports/phase-11-real-data-risk-study.md`, `experiments/real_data_risk_study/`) — not a PROJECT_SPEC phase; it is the top-ranked item of `docs/portfolio_audit.md` §10 |
| Phase 12 worked analysis result: closed-form third and fourth spot derivatives, a Lagrange remainder bound for the delta-gamma stress map, five falsified-before-published predictions, and the correction of a false claim in this repository's own published prose | DONE (`docs/phase_reports/phase-12-remainder-bound.md`, `docs/analysis/delta_gamma_error_bound.md`, `experiments/linearisation_error_bound/`) |
| Phase 13 two-factor truncation bound: five mixed spot/volatility closed forms added to the core as new value types, the joint-shock remainder derived and measured, the published `risk_off` scenario bounded with a proved sign, and a Phase 12 refusal converted into a result | DONE (`docs/phase_reports/phase-13-two-factor-bound.md`, `docs/analysis/two_factor_error_bound.md`, `experiments/two_factor_error_bound/`) |
| Phase 14 verification debt: the compiled extension checked against its own registration source in both directions, an analysis note found to carry a stale figure and a statistic its experiment never computed, and the regenerating performance fields given derived-string guards after the runner caught that guard itself reading a clone's git history, and the mutation sweep promoted from `/tmp` to `scripts/run_mutation_suite.py` with its own gate | DONE, released as `v1.4.0` on `f4e8afc13bd7` (`docs/phase_reports/phase-14-verification-debt.md`, `docs/integrity_audit.md` findings 32–35, `docs/limitations.md` #77) |
| Phase 15 the recommendation `v1.3.0` published, measured: the re-struck-gamma-at-shocked-volatility advice put through four priced maps on 120 cells, found half right (the naive variant is worse than the gamma-only fix on 116 cells and by a factor of 11 on `risk_off`; the ordering never moves), with a third-order zero-crossing prediction gated where a cubic truncation is a fair argument and its drift recorded outside it | DONE, released as `v1.5.0` on `2ad54059ae28` (`docs/phase_reports/phase-15-restrike-gamma.md`, `docs/analysis/restrike_gamma_map.md`, `experiments/restrike_gamma_map/`, findings 37–39, `docs/limitations.md` #78) |
| Phase 16 the fourth order shipped: `docs/phase_reports/phase-15-restrike-gamma.md` §8's five mixed order-four partials corrected — three carried the wrong power of `T` because a factor equal to one at the tested tenor hid it — `MixedFourthDerivatives` added to the core and the bindings, and the fourth-order crossing map measured (suite member 16) with the reproduction gate rebuilt to exempt by declared family rather than by field name | DONE, released as `v1.6.0` on `b4e4bea05fd2` (`docs/phase_reports/phase-16-fourth-order-crossing.md`, `experiments/fourth_order_crossing_map/`, findings 40–45, `docs/limitations.md` #79) |
| Phase 17 the surface-coverage debt closed: finding 43 (a core function reachable by neither a binding nor a disclaimer) turned into a third direction of the parity guard, keyed on `[[nodiscard]]` across every header, with 24 disclaimers whose named route each check resolves, the residual non-`[[nodiscard]]` set pinned to one inventoried name, and the fifth-order pre-check promoted from a note into a gate that measured the order-five term above the subtraction noise | DONE, no release (`docs/phase_reports/phase-17-surface-coverage.md`, `tests/python/test_extension_surface_parity.py`, `docs/limitations.md` #80) |
| Phase 18 transferability of the crossing radius, tested on five books instead of one ladder: a re-derived pipeline proved bit-identical to the shipped machinery before any new book was measured, two radius-definition defects (a headline judged by another order's range, a signed pair split into two candidates) found and fixed, and the published `v1.6.0` claim of model-wide transferability narrowed to what the five books actually support, with a dated correction appended to that release's own note | DONE, no release (`docs/phase_reports/phase-18-five-book-radius.md`, `docs/analysis/second_book_crossing_map.md`, `experiments/second_book_crossing_map/`, findings 46–47) |
| Phase 19 the whole core surface rather than the part an attribute marks: seventeen namespace-scope declarations gained `[[nodiscard]]` across four headers, the extension-surface claim re-keyed from the attribute to the surface it now covers, `stats::quantile_linear` given the disclaimer Phase 17 said it needed, and a latent defect in the Phase 17 scanner fixed | DONE, no release (`docs/phase_reports/phase-19-core-surface.md`, finding 48) |
| Phase 20 the order-five terms shipped as arithmetic and the claim withheld: `MixedFifthDerivatives` (six mixed fifth partials) in the core, and their numerators *derived* rather than typed by a committed command (`scripts/derive_fifth_order_partials.py`) that re-differentiates the closed form and asserts polynomial degree, with the consuming experiment deliberately not run so a capability and the claim that consumes it stay separately earned | DONE, no release (`docs/phase_reports/phase-20-fifth-order-partials.md`, findings 49–50, `docs/limitations.md` #82) |
| Phase 21 order five measured: the quintic term added to the cubic and quartic truncations on the same five books under the same rule — 2 of 5 books widen (1.33×, 1.50×), the quintic is the closest truncation inside the quartic radius on 5 of 5, the mechanism that would explain the widening is refuted twice (the ratio spans 0.057–0.588 and orders nothing), two of the three unchanged books sit at the swept grid edge and are reported as unresolvable, and the guard that refused a correct radius is fixed and pinned in both directions | DONE, no release (`docs/phase_reports/phase-21-fifth-order-crossing.md`, `docs/analysis/fifth_order_crossing_map.md`, `experiments/fifth_order_crossing_map/`, findings 51–53, `docs/limitations.md` #83) |
| Phase 22 `v1.7.0`: the release and the post-tag accounting — version moved in the three places that carry it, the full suite re-executed (`--require-all`, 18/18 members) before any prose was synced, evidence re-frozen at 94 artifacts and verified, the sweep run on the committed tree, the tag placed on the CI-verified commit, the release assets hashed from `git archive` both directions, and finding 54 recording the two assertions that were wrong only on the runner plus the one wording that overstated what the manifest diff can see | DONE, released as `v1.7.0` on `79d536a16eeb` (`docs/phase_reports/phase-22-v1.7.0.md`, `docs/release_notes_v1.7.0.md`, finding 54) |
| Phase 23 the report's own prose, audited after the tag: `paper/technical_report.tex` restated the evidence freeze as it stood at `v1.1.0` (69 artifacts, 6,208,835 bytes, 40 experiment files) and shipped that in six releases while its own §1 printed 94, said in the present tense that the fifth-order crossing experiment "was deliberately not run" one phase after it ran and two releases after its answer was published, and `docs/interview_defense.md` annotated the falsification sweep with the plant count Phase 14 had — four derived guards now read those sentences out of the manifest, the suite registry, the artifact and the harness, each with its own declared defect | DONE, post-tag (`docs/phase_reports/phase-23-report-prose.md`, `docs/integrity_audit.md` finding 55, `docs/limitations.md` #84, `docs/release_notes_v1.7.0.md` dated erratum) |
| Phase 24 the derivation became a gate item rather than an offer: `sympy` moved into the `dev` dependency group that `uv sync` installs, so `scripts/derive_fifth_order_partials.py` -- the 60-digit identity behind the published `8.7e-58` residual -- now runs in every lane that sets up the development environment instead of only when a human types `uv run --with sympy`; the new test also requires `docs/validation_matrix.md` row 21 and the technical report to quote the same figure and to quote the run's order of magnitude | DONE, post-tag (`docs/phase_reports/phase-24-dependencies-and-build-products.md`, `docs/integrity_audit.md` finding 56, `docs/limitations.md` #82 amended in place) |
| Phase 25 the two C++ numbers CTest cannot see gained owners: the assertion total is read from the compiled Catch2 binary's summary line and the case total from `TEST_CASE(` blocks in `tests/cpp/*.cpp`, the two required to agree, and five quotations across four documents compared with both; the CTest entry count was left with the guard that already owns it | DONE, post-tag (`docs/phase_reports/phase-25-cpp-total-owners.md`, finding 57, `docs/limitations.md` #85) |
| Phase 26 the oracle-free test count gained a second producer: `scripts/measure_offline_collection.py` blocks the `oracles`-only packages in a child interpreter, collects there, and a guard refuses the probe unless the gated modules skip rather than error before comparing every living quotation of the offline figure with the measurement -- so a phase that adds tests learns both halves of the pair locally instead of from a red runner (findings 55(d), 58) | DONE, post-tag (`docs/phase_reports/phase-26-offline-count-owner.md`, finding 58, `docs/limitations.md` #63 amended in place) |
| Phase 27 every countable claim in `paper/technical_report.tex` is accounted for: an inventory guard reads each `<number> <noun>` statement and requires it to be owned by a named guard, inside the manifest sentence's compared span, cited to a frozen artifact, or declared with a reason -- and each owned pattern has to occur verbatim in the guard that claims it, while each declared anchor is re-run with itself withheld so an exemption that exempts nothing is a failure. It found a stale count shipping in the report's own abstract (`55 recorded limitations` beside the section's 86) and a digit guard that had been comparing a market count with a working precision because both read 60 (findings 55, 59) | DONE, post-tag (`docs/phase_reports/phase-27-claim-inventory.md`, finding 59, `docs/limitations.md` #86) |
| Phase 28 the crossing-radius chain gained a sixth book chosen by a rule written before it was measured: 23 candidates ranked by the order-five-to-four ratio at Phase 20's own measure column, the first with a defined radius taken, and the book it reached has its quintic radius on the grid edge -- so the experiment reports that its own rule cannot distinguish a widening from a truncation, which is a result about the rule, not a null about the expansion. Registered as the 19th suite member, and that registration is the second half of the phase: re-measuring the volatile speed artifact moved five documents' present-tense figures and the committed NumPy band (`0.42×`–`0.57×`), and exposed the one figure the ownership inventory had no rule for -- the caption's timestamp, which says *which* run a table tabulates | DONE, post-tag (`docs/phase_reports/phase-28-sixth-book.md`, finding 60, `docs/limitations.md` #88) |

| Phase 29 the claim inventory left the paper: `README.md` and `docs/reproducibility.md` are now read by the same owned-or-declared rule, with citations resolved through the suite registry (a findings row is cited by the member its key names, and a key the registry dropped cites nothing) and with two sentence-level exclusions the report never needed -- a `#` is a cross-reference, a bare trailing period is a list marker. It found a stale twin on its first pass (`# 481 tests here` three lines under a correct 494, green for three phases because every count guard checks presence of the right spelling, not absence of a wrong one), gave `7 identity checks` a producer by running the installed CLI, and registered #89 for the two documents still policed per figure | DONE, post-tag (`docs/phase_reports/phase-29-markdown-inventory.md`, finding 61, `docs/limitations.md` #89) |
| Phase 30 `v1.8.0`: the release, and the last number in the tree with no owner -- the version string itself. Seven phases sit behind the tag and only one added a measurement (Phase 28's sixth book), so the release's content is producers: `sympy` gating the 60-digit derivation, the Catch2 assertion and case totals read from the binary and the source, the oracle-free count measured locally (429 against 498), the owned-or-declared inventory extended over `README.md` and `docs/reproducibility.md`, and now `test_the_version_string_the_project_declares_is_one_number_not_four`  tying `pyproject.toml`, `CMakeLists.txt`, `CITATION.cff`, `uv.lock`, `README.md`, the rehearsal sheet and `quantrisk.version()` to one number -- `CITATION.cff` being a downloadable release asset with nothing able to disagree with it until this phase. Producers ran before the prose was synced, the freeze rebuilt from the commit that carries the artifact, CI verified `f181427`, the annotated tag points at that commit, the four assets were built from `git archive` and hashed in both directions, and the sweep is `53/53` on the tagged tree. One verification figure in the published note came from the laptop rather than the runner (a Ruff file-walk count: 164 here, 165 on CI), so the release page carries a dated correction appended to its body with both halves committed, tag and assets unmoved |
| Phase 31 closed `docs/limitations.md` #90: the committed report PDF now has a freshness owner. `scripts/build_report.py` typesets the document and writes `paper/technical_report.build.json`, which binds a digest of every source the render consumes -- the tex, the bibliography, and the four `\includegraphics` figures it pulls out of frozen experiment directories, parsed from the document rather than listed -- to the bytes it produced; `test_the_committed_report_pdf_is_bound_to_the_sources_that_rendered_it` re-derives that set in every environment, while `test_rebuilding_the_report_from_the_committed_source_typesets_the_same_text` re-typesets and compares extracted text where TeX Live and poppler exist (a declared skip on the runner, because a render is not byte-reproducible: two builds of one unchanged source measured `e72fcfc5…` and `ac7736aa…` while their text was `c5f09b1a…` both times). The fix #90 itself sketched -- compare last-touch commits -- was rejected as un-buildable, since a history-keyed guard cannot be touched by any plant and so could never be shown to fail. Three plants added (53 → 56); the binding reddened on this phase's own test-count sync within one sitting; tests 500 with the oracles, 431 without; reading the runner's own log during verification also surfaced a denominator the prose never named -- the oracle-free figure is a *collection* count (431) while a runner prints `428 passed, 7 skipped` for the same tree, because four oracle-gated modules are skipped items outside `collected` -- so #91 registers the reconciliation and the rehearsal sheet's annotation now says "tests collected offline" | DONE, no release (`docs/phase_reports/phase-31-report-render-owner.md`, finding 63) |
| Phase 32 closed the two ownership debts Phase 30 registered rather than took on: the completeness of `RANGE_DOCUMENTS`, and `CITATION.cff`'s `date-released`. The band census enumerates 38 candidate documents and asks which print a spread sharing an edge with a policed band -- 16 do, two of them in no list at all (`docs/project_scope.md`'s `0.42×`–`0.57×`, `docs/release_notes_v1.0.0.md`'s `0.42×`–`0.48×`, both dated records now declared with their reason), and two more sat in the policed set while stating a superseded range in the present tense: `paper/technical_report.tex` credited `7.77×`–`8.70×` to "thirteen committed re-freezings" and `docs/release_notes_v1.6.0.md` said both ratios "remain inside the pinned history range" -- against a committed history of twenty-two readings spanning `7.77×`–`10.31×`. The report was corrected in place, the note by dated amendment, and the detector was rebuilt first: a gap-wide regex answers "which file states a band?" with any two nearby decimals, so it invented `8.378× / 0.5656×` as a spread, and the shape now needs the multiplication sign on both edges plus a range mark between them. `date-released` is compared with the annotated tag's *tagger* date rather than the commit's author date, with both skips named (a tagless depth-1 clone; the current version's tag, which the release has not cut yet). Exemptions are load-bearing on pain of redness -- a dated record brought up to date, or an exempt family with no printer, fails -- and three plants (56 → 59) cover the two halves and the citation field. Tests 502 with the oracles, 433 without; register #92 records the half still open: a band's percentage spreads 32.6 %/20.8 % over the raw history and 32.7 %/21.4 % over the pinned rounded edges, so it has no owner a shallow clone can run | DONE, no release (`docs/phase_reports/phase-32-band-census-and-release-date.md`, finding 64, `docs/limitations.md` #92) |
| Phase 33 asked whether the runner could afford the input set three guards were skipping for, and measured it: the pytest lane now checks out with `fetch-depth: 0` and `fetch-tags: true`, which moved the report's release-tag enumeration, the citation's `date-released` and the history-derived speedup bands from always-skip to checked-on-the-runner -- `429 passed, 8 skipped` at depth 1 against `432 passed, 5 skipped` at depth 0 on the same tree, the checkout step costing 1.29 s then 2.17 s for a 7.93 MiB pack over 180 commits, proven on a throwaway branch through `workflow_dispatch` before anything reached `main` and read from the job log rather than the badge. The half of `docs/limitations.md` #92 that needed history then closed: the documented spread percentages are recomputed as `(max - min) / min` over the committed readings -- the denominator chosen rather than inherited, since the alternatives give 24.6 % and 30.3 % and match nothing -- and each living document is compared as a band-plus-percentage block, so keeping the pair while changing the percentage is caught. Two plants (59 -> 61), one of which edits the guard's own pinned constant because that is the derivation guard's only reachable defect. Changing the premise also meant hunting it: eight living passages said CI checks out at depth 1, and the skip messages now name the clone rather than the infrastructure | DONE, no release (`docs/phase_reports/phase-33-runner-history-and-spread-owner.md`, finding 65, `docs/limitations.md` #92 amended) |
| Phase 34 asserted the settings Phase 33 had made load-bearing. `actions/checkout`'s fetch options were now the input set of three guards, and deleting them would not redden the lane -- the guards skip with a named reason and the job prints success -- so `test_the_ci_lane_that_runs_the_guards_fetches_what_they_read` parses the workflow as YAML, finds the jobs whose steps run pytest, and requires the checkout ahead of them to carry `fetch-depth: 0` and `fetch-tags: true`, with a plant (`ci-lane-drops-the-history-its-guards-read`) to prove it reads the file rather than restating it. `pyyaml` entered the `dev` group to make a parser available in every lane, the way `sympy` did in Phase 24. The sweep's own plumbing gained `test_every_subprocess_the_harness_runs_a_guard_in_is_bytecode_isolated`, which intercepts the single `subprocess.run` and requires every guard step to carry a bytecode prefix and consecutive steps to carry different ones. That guard cannot have a declared plant: the harness refuses an anchor that is not unique, and an anchor written into the plant list appears twice in the same file -- once as code, once as the plant's own string. #94 registers that wall and what leaning on a hand demonstration costs; finding 67 records the incident, including the red the demonstration did produce | DONE, no release (`docs/phase_reports/phase-34-ci-settings-and-sweep-isolation.md`, finding 67, `docs/limitations.md` #93 amended, #94 opened) |
| Phase 35 put the last two living documents inside the claim inventory, which is where #89 said the restatements were hiding, and the first pass found three: the rehearsal sheet's own provenance table quoted this register at 84 entries six lines under a correct 94; its three current path rates were owned by a substring comparison that could not tell them from the superseded rate in the same sentence, so ownership moved to phrase patterns read against the artifact; and its opening line's "Nothing added, nothing dropped" was simply false -- the brief asks 22 questions, the sheet carries 28, and a new producer now reads `PROJECT_SPEC.md` and requires the first 22 titles to match in order. The extractor widened its vocabulary (#92's remaining half: `spread`, `runs`, `reading`, `re-freezing`, `path`, and a `%` allowed before the noun), which made three of its silent judgements load-bearing and gave them their own self-test and two plants; one declared exemption was deleted because the label rule made the claim it exempted stop existing. What the rule still cannot read -- a count spelled in words, 112 instances measured -- is opened as #95 | DONE, no release (`docs/phase_reports/phase-35-inventory-for-the-rehearsal-sheet.md`, findings 68 and 69, `docs/limitations.md` #89 and #92 amended, #95 opened) |
| Phase 36 closed the two blind spots the band census shared one root with: its shape required a multiplication unit on both edges, so a document writing `7.77–8.70` was not a printer at all, and its exemptions were path prefixes, so `docs/phase_reports/` and `docs/release_bodies/` were never read. The census now reads a dash or a spoken lead between bare decimals -- bounded by the counter-example this repository already recorded, since the first permissive version paired `10.31×` with `0.495×`, two readings of one run -- and the nine band-printing files in those two directories are named one by one with the revision each records. Measured before writing: 68 united and 44 loose decimal pairs over 80 documents, none of the 44 sharing a policed edge, so the widening changes no verdict today and its red is reachable only by a planted unlisted document. Two records that state today's band sit in a new self-terminating class, exempt only while they keep printing it | DONE, no release (`docs/phase_reports/phase-36-band-census-without-its-unit.md`, finding 71) |
| Phase 37 moved a tool out of the ignored directory it had been doing real work from for four phases: `scripts/rewrap_docstrings.py` now has a self-test that attempts the refusal -- a rewrite that deletes words must exit 1 with the file untouched, an honest re-wrap must preserve every token, the code literals and the whitespace-folded parse -- and it takes its width from `pyproject.toml` because a second copy of the gate's number is the kind of stale fact this repository keeps meeting; two plants, one inverting the proof and one widening the width by 20 while the tool's own report stays tidy. The same phase answered #96 reader by reader with a before/after count each: six more prose-counting guards read the folded view, the band census deliberately does not, because folding the tex manufactures the pair `(10.7, 7.4)` out of two line ends -- measured across 81 documents | DONE, no release (`docs/phase_reports/phase-37-rewrap-tool-promoted-and-folding-answered-per-guard.md`, findings 72 and 73, `docs/limitations.md` #96 amended) |
| Phase 38 let the claim inventory read a count written in words, which #95 had measured at 109 claims and staged document by document because all of them at once is a diff nobody can review: the extractor's number group is generated from the same `SPELLED_NUMBERS` table `_as_int()` has resolved through since Phase 22, switched on per document, and the first pair -- `README.md` and `docs/reproducibility.md`, 28 claims -- now answers for every one of them (15 owned, 9 cited, 2 declared). Reading them found the front page wrong three times over, each in a sentence no numeric reader could see: "Three rows in the full matrix are the ones to interrogate" had enumerated four since Phase 12, the same paragraph cited "Row 14" for the bound the matrix numbers 15, and "quietly skipping four members" was already stale in the commit that wrote it, which declared five then and six now. All three are produced rather than retyped by one new enumeration guard -- bullets counted under their own lead, matrix row labels checked against the table's numbering, the timing paragraph's artifact paths intersected with the freeze -- and five more owners gained the spelled spelling of the pattern they already searched with. Four plants (72 -> 76), one of which is the sweep's own annotation, and a comment's claim about alternation ordering that measurement disproved before it could ship as a plant that cannot fire | DONE, post-tag (`docs/phase_reports/phase-38-spelled-numerals-in-the-inventory-and-the-front-pages-stale-enumeration.md`, findings 74-78, `docs/limitations.md` #95 amended and #97-#99 opened) |
| Phase 39 moved the plant list out of the file that interprets it, which is what #94 said was never fixable in place: an anchor has to occur once in its target, and a plant naming a line of the harness always found that line twice -- the code and its own entry -- so the case was refused and the bytecode-isolation guard could only be shown red by hand. `Mutation` and `MUTATIONS` now live in `scripts/mutation_plants.py`, loaded by path, with a guard that proves the split (list defined there, none of it back in the interpreter, the one unlocked plant's anchor unique), and the plant itself -- `harness-spawns-a-guard-subprocess-without-a-bytecode-prefix` -- names `Harness.uv`'s single call site. 76 -> 77 plants, and the cascade through six documents and four anchors found a wrong-tense claim in the rehearsal sheet: "Nineteen are declared" in the present, of a list now 77 strong, two lines above the `19/19` quotation it belongs to | DONE, no release (`docs/phase_reports/phase-39-the-plant-list-moved-out-of-the-harness.md`, finding 79, `docs/limitations.md` #94 amended) |

## 10. Frozen surfaces

### Phase 1

- `namespace quantrisk`, `Real = double`, `Time/Rate/Volatility/Money/Count/Seed`.
- `Rng` (instance-owned `std::mt19937_64`, explicit seed, no global state).
- `normal_pdf`, `normal_cdf`, `inverse_normal_cdf`, `stats::*`, `version()`,
  `build_metadata()`, `ValidationError`.
- Python smoke surface: `quantrisk.version()`, `quantrisk.normal_cdf(0.0)`.

### Phase 2

- `OptionType`, `ExerciseStyle`, `EuropeanOption`, `MarketParams`,
  `PricingResult`, `Greeks`, `BumpPolicy`, `BinomialResult`.
- `black_scholes`, `black_scholes_greeks`, `finite_difference_greeks`,
  `crr_binomial`, `put_call_parity_residual`, `is_degenerate`.
- Units: Theta per calendar year, Vega and Rho per unit (verified against
  QuantLib 1.43 by measurement, not by assumption).

### Phase 3

- `VarianceReduction`, `MonteCarloResult`, `MonteCarloEngine`,
  `gbm::{terminal_prices, antithetic_terminal_prices, paths_matrix,
  antithetic_paths_matrix, terminal_prices_physical, expected_log_return}`,
  `normal_confidence_multiplier`.
- Convention: `mu` in the physical-measure generator is price appreciation
  *excluding* the dividend yield, so `mu = r` reproduces the risk-neutral stream.

### Phase 4

- `AsianOption`, `AverageType`, `BarrierOption`, `BarrierType`,
  `geometric_asian_price`, `barrier_continuity_constant`,
  `continuity_corrected_barrier`, `path_dependent::{price_asian,
  price_geometric_asian, price_barrier}`, `HestonParams`, `HestonSimulation`,
  `HestonPriceResult`, `simulate_heston`, `price_heston_european`,
  `heston_step_refinement_gap`.
- Convention frozen: the BGK correction moves the effective barrier **toward**
  the spot (an up-and-out barrier is lowered, a down-and-out barrier raised).

### Phase 5

- `quantrisk::log_gamma`, `regularized_lower_incomplete_gamma`,
  `regularized_upper_incomplete_gamma`, `chi_square_sf`, `chi_square_isf`,
  `log_binomial_coefficient`.
- `returns::{arithmetic,log_returns}`; `risk::{historical_var, historical_es,
  gaussian_var, gaussian_es, monte_carlo_var, monte_carlo_es,
  quantile_standard_error, linear_pnl, sample_covariance}`; `RiskEstimate`.
- `BootstrapKind`, `BootstrapEstimate`, `bootstrap_var`, `bootstrap_es`,
  `suggested_block_length` (default `round(n^(1/3))`).
- `ViolationSeries`, `TransitionCounts`, `CoverageTestResult`, `BacktestReport`,
  `flag_violations`, `transition_counts`, `kupiec_pof_test`,
  `christoffersen_independence_test`, `christoffersen_conditional_coverage_test`,
  `backtest_var`.
- Conventions frozen here: loss `L = -R`; a violation is a *strictly* greater loss
  than the VaR level; `stats::*_sorted` primitives require ascending, finite input and
  raise rather than guessing; chi-square critical values are solved from the same
  survival function the p-value uses, never transcribed from a table.

### Phase 6

- `quantrisk::portfolio` and its Python submodule: `CovarianceEstimate`, `LinearSolve`,
  `OptimizerInputs`, `OptimizationRequest`, `PortfolioSolution`, `RiskParitySolution`,
  `LpStatus`, `LinearProgramResult`, `CvarRequest`, `CvarSolution`.
- `sample_covariance`, `ewma_covariance`, `shrinkage_covariance`, `eigenvalues`,
  `condition_number`, `solve`, `minimum_variance`, `efficient_frontier`,
  `maximum_sharpe`, `risk_parity`, `solve_linear_program`, `minimise_cvar`.
- Conventions frozen here: the sample estimator is unbiased (`ddof = 1`); EWMA is
  filtered **about zero** with `half_life = ln 0.5 / ln λ` reported beside `λ`;
  shrinkage is Ledoit–Wolf 2004 with divisor `T` and a scaled-identity target.
- `solve` **refuses** (returns `NaN` plus a reason) when the matrix is not positive
  definite or `rcond < 1e-12`. There is no hidden ridge, no silent pseudo-inverse and no
  automatic shrinkage anywhere in the layer.
- Equality-constrained solves go through the **saddle-point KKT system**, never through
  `Σ⁻¹`: the normal equations return the minimum-norm stationary point, which on a flat
  asset is not the optimum. The KKT multiplier convention is `ν = Σw − Aλ`, frozen
  because the certificate is checked against it.
- Every solution carries its own proof (`verified_optimal`, `certified`, `converged`)
  computed from the original inputs, and the residuals (`budget_residual`,
  `weight_bound_violation`, `target_residual`) are always populated, feasible or not.
- Max-Sharpe is documented as a **frontier search over the §7 QP**, not as a quadratic
  program; the linear-fractional transformation is stated in the returned `note`.
- Eigen is now a real build dependency (v5.0.0 pinned by SHA-256, with
  `find_package(Eigen3 3.4)` preferred when the system provides one).

### Phase 7

- `quantrisk::stress` and its Python submodule `quantrisk.stress`: `RiskFactor`,
  `FactorClass`, `FactorSet`, `ExposureVector`, `Position`, `Portfolio`, `Shock`,
  `DistributionShift`, `Scenario`, `ScenarioKind`, `FactorContribution`,
  `PositionContribution`, `ScenarioResult`, `ScenarioSample`, `FactorSummary`,
  `ScenarioSetResult`.
- `run_scenario`, `shift_covariance`, `sample_factor_moves`,
  `run_historical_scenarios`, `run_monte_carlo_scenarios`.
- Conventions frozen here: `delta`/`gamma` answer to a **relative** factor move and
  `duration`/`vega`/`credit` to an **absolute** one; `gamma` is quoted with the 1/2
  already absorbed; an empty exposure block means "no sensitivity of that type recorded",
  which is not the same as a block of zeros and is preserved through aggregation.
- Portfolio dispersion uses the **first-order** beta only. Convexity moves the mean, never
  the variance, so the second moment cannot depend on the scenario's direction.
- Every result carries its own residuals (`factor_attribution_residual`,
  `position_attribution_residual`, `var_decomposition_residual`,
  `var_component_residual`). They are exact identities, so a non-zero value is an
  implementation defect and is reported rather than absorbed.
- A scenario with no `assumptions` or no `horizon`, and a single-scenario set asked for a
  quantile, are each announced in `note` rather than silently tolerated.
- `sample_factor_moves` refuses a matrix with no Cholesky factor. No jitter, no
  projection, no silent shrinkage.

### Phase 8

- `quantrisk.data` and its modules: `http`, `provenance`, `edgar`, `fred`, `cftc`,
  `fixtures`. Python-only; the extension and `cpp/` gained nothing at all.
- Frozen semantics, not just names:
  * a SHA-256 in a provenance record covers the **bytes as served**, before parsing;
  * `Financials.missing` distinguishes "this filer does not use that tag" from "the value
    is zero", and the two are never conflated;
  * FRED's `"."` placeholder becomes `None`, never a dropped row and never a zero;
  * a current-revision series and an ALFRED vintage are different datasets, and
    `fetch_vintage` refuses without a key rather than degrading to the current revision.
- Credentials: `FRED_API_KEY` and `QUANTRISK_DATA_USER_AGENT` are read from the environment
  only. A key never enters a provenance record, a cache filename, or a fixture — enforced by
  `http.fetch`'s `record_url` parameter and pinned by a test that plants a key and asserts
  its absence everywhere the record can be serialised.
- `data/fixtures/` is committed and is real data (plus one labelled synthetic file and one
  labelled excerpt). `data/cache/` is git-ignored and per-machine.
- The dependency direction is frozen: `quantrisk.data` may use `quantrisk`; no pricing,
  risk, portfolio or stress code may import `quantrisk.data`.

### Phase 10

- `scripts/run_benchmark_suite.py` is an **orchestrator, not an implementation**. It holds no
  financial or statistical formula and computes no result; it executes each member's own script
  and reads headline numbers out of the JSON that script writes, by key path.
- A renamed or removed field **aborts the run** rather than dropping a row. This is the
  load-bearing property: an aggregation that silently lost a metric would look identical to one
  that passed. `tests/python/test_artifact_metadata.py` pins it by re-walking each published key
  path independently of the runner's own lookup.
- `aggregated` is not `passed`. `--no-run` reads artifacts from disk and reports the weaker
  status, because "this file exists and has the fields" is not "this benchmark ran".
- A member whose oracle package is missing is `skipped`, never `passed`; `--require-all` turns
  any skip into a non-zero exit, which is what the CI job uses so it cannot go green by
  measuring nothing.
- `benchmarks/suite/results/` is written **beside**, never inside, the members' own result
  directories, so summarising the evidence cannot overwrite the evidence it summarises.
- `validation_envelope.png` is drawn from the same extracted metrics as the summary table, not
  from a second pass over the CSVs. A figure built by its own extraction can disagree with the
  table printed next to it.
- `evidence/manifest.json` recovers each artifact's generating command **from the artifact**,
  not from a hand-maintained list, and records the revision plus whether the tree was dirty.
  For committed data fixtures the correct provenance is a source URL and retrieval time, read
  from the `.provenance.json` sidecar.
- `scripts/verify_evidence_manifest.py` reports OK / VOLATILE / CHANGED / MISSING / unlisted
  separately and exits non-zero on the last three. "Nothing is missing" and "nothing was edited"
  are different claims, and so is "the numbers moved" from "the file was re-run": the manifest
  carries a byte hash for tamper detection and a content hash, over the artifact with run
  metadata and wall-clock columns removed, for reproducibility.
- The library version is declared in two places (`pyproject.toml` and `CMakeLists.txt`) because
  the C++ core needs it at compile time; `tests/python/test_smoke.py` asserts they agree, so the
  duplication is guarded rather than trusted.

Changing any of the above requires a written migration note.
