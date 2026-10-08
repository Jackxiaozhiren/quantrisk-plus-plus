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

## 9. Current status (honest, refreshed 2026-10-08; first written 2026-09-27)

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
