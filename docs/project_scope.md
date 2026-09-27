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

## 9. Current status (honest, 2026-09-27)

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
| Stress testing, public data layer, research API, release | NOT IMPLEMENTED — no such numbers exist yet |

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

Changing any of the above requires a written migration note.
