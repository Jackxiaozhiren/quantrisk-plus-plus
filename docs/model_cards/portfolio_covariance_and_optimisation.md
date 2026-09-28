# Model card — portfolio covariance and optimisation

Phase 6 · written 2026-09-27 · status: implemented, validated against live reference
solvers, studied on synthetic returns with an analytically known forward covariance.
No real return series is used anywhere in this card — Phase 11 ranks the same three estimators on
real factor series and the ordering reverses; see the limitation below.

## What is implemented

`cpp/include/quantrisk/portfolio/`, mirrored by `quantrisk.portfolio` in Python
(12 functions, 10 bound types, 81 members; the bindings convert containers and add no
numerics of their own).

### Estimators

| Entry point | Estimator | Definition, stated so it can be checked |
| --- | --- | --- |
| `sample_covariance` | unbiased sample covariance | `S = (X - x̄)'(X - x̄) / (T - 1)`, `ddof = 1`, compensated summation |
| `ewma_covariance` | RiskMetrics-style filtered covariance | recursion about **zero**, `λ` in, `half_life = ln 0.5 / ln λ` reported alongside |
| `shrinkage_covariance` | Ledoit–Wolf (2004) | `δ̂ Σ̂ + (1 - δ̂) μI`, divisor `T`, closed-form intensity, `shrinkage_intensity` and `target_scale` reported |
| `eigenvalues`, `condition_number` | diagnostics | symmetric spectrum of the estimate; `λ_max / λ_min` |
| `solve` | linear solve | `LLT` factorisation; **refuses** when not positive definite or when `rcond < 1e-12` |

Every estimate carries `positive_semidefinite`, `smallest_eigenvalue` and a `note`.
A degenerate estimate is described, not silently repaired.

### Optimisers

| Entry point | Problem | Method |
| --- | --- | --- |
| `minimum_variance` | `min ½ w'Σw` s.t. `Aw = b`, `w ≥ 0` | active-set search over supports; each candidate support solved as a **saddle-point KKT system**, verified against the original data |
| `minimum_variance` + `target_return` | same, with `μ'w ≥ target` | the constraint is tested for inactivity first; if binding it is imposed as an equality and the search repeats |
| `efficient_frontier` | a sweep of frontier points | one constrained solve per target |
| `maximum_sharpe` | `max (μ'w - rf)/√(w'Σw)` | ternary search over the frontier the QP already produces; the linear-fractional reformulation is stated in the returned `note` |
| `risk_parity` | equal risk contribution | cyclic coordinate descent on `½ w'Σw - c Σ log w_i`, closed positive root per sweep, `contributions` and `max_contribution_gap` reported |
| `minimise_cvar` | Rockafellar–Uryasev | two-phase dense **primal simplex with Bland's rule**; `α` split as `a⁺ - a`, excesses `u_i`, LP optimality certificate |
| `solve_linear_program` | generic `min c'x` s.t. `Ax = b`, `x ≥ 0` | the same simplex, exposed so the CVaR construction can be tested on its own |

## The distinction that carries the phase

**The estimator, not the solver, decides what the portfolio is optimal for.** Every
matrix handed to these optimisers is an estimate, and a minimum-variance portfolio is
optimal only for the matrix it was given. `experiments/portfolio_optimization/`
measures the consequence on a two-regime factor process whose forward covariance is
known in closed form: across window lengths 40–250 and all three estimators, the frozen
portfolio carries **1.13× to 1.26× the forward variance** of the portfolio an informed
solver would have held. The same solver's disagreement with cvxpy and PyPortfolioOpt on
identical inputs is **≤4.5e-9** in the objective. The estimation error is roughly seven
and a half orders of magnitude larger than the numerical error, which is the whole
reason the layer reports condition numbers and refuses ill-conditioned solves.

**A certificate is not a convergence message.** `verified_optimal`, `certified` and
`converged` mean the answer was checked against the *original* inputs — primal
feasibility, dual feasibility, complementary slackness — not that an iteration counter
ran out. This is why the benchmark validates a proof rather than supplying a claim:
when two solvers disagree, the certificate says which one to believe.

**The KKT system is solved directly, never through `Σ⁻¹`.** With a flat or duplicated
asset the normal equations return the minimum-*norm* stationary point rather than the
optimum: on a diagonal `Σ = diag(0.04, 0)` they put the whole position in the risky
asset and report variance 0.04, where the saddle system returns the true answer of
holding the flat asset at zero variance. That case is a test, not a footnote.

**Degenerate LPs do not have unique weights.** `minimise_cvar` agrees with
PyPortfolioOpt to 4.7e-7 in weights but 4.5e-9 in objective. An LP optimum can be a
whole face, so the vertex each method reports is a property of the algorithm; the
objective is the comparable quantity. The same logic applies to `maximum_sharpe`, where
the frontier is flat at the tangency point and a 1e-12 bracket on the target return maps
to ~1e-9 in coordinates at zero cost in objective.

## Validation

| Level | What was compared | Measured agreement |
| --- | --- | --- |
| L1 analytical | two-asset closed forms, diagonal `Σ`, the flat-asset case, ERC `w_i ∝ 1/σ_i` on independent assets, LP duality gap | exact to the working tolerance; ERC identity 4.5e-14 |
| L2 live oracle | `sample` vs `numpy.cov(ddof=1)`; `shrinkage`/`ewma` vs scikit-learn and PyPortfolioOpt; `minimum_variance`/frontier/`maximum_sharpe` vs cvxpy (OSQP) and PyPortfolioOpt (SLSQP); `risk_parity` vs the Spinu log formulation (SCS); `minimise_cvar` vs PyPortfolioOpt | sample 7.2e-16 relative, Ledoit–Wolf 7e-19 absolute; quadratic weights ≤2.4e-12, variance ≤6.5e-14 relative; Sharpe weights ≤7.0e-9 with objective ≤1.2e-11 relative; ERC ≤1.4e-11; CVaR weights ≤4.7e-7 with objective ≤4.5e-9 relative |
| L3 statistical | rolling-origin forward variance ratio against the analytic truth, turnover, concentration, behaviour at a regime break | 1.13×–1.26× across cells; 1.57×–1.60× on straddling windows |

Reference numbers are never transcribed. `clean_weights()` is deliberately not used as
the PyPortfolioOpt reference — it rounds to five decimals, which floors every
comparison at ~5e-6 and would make the test measure that rounding instead of the
optimisation. Tolerances are recorded per problem in the test module header, with the
measured value beside the asserted bound.

## Failure modes, and what the layer does about each

| Input | Behaviour |
| --- | --- |
| `T < n` (singular sample) | estimate reports `positive_semidefinite = false`, `solve` refuses with a note; `shrinkage_covariance` returns a usable matrix that measurably costs less forward |
| near-collinear twins | condition number ~4e8 reported; the optimiser still certifies its answer |
| a genuinely flat asset | minimum variance puts everything in it, correctly; ERC declines and says "zero variance" |
| flat in sample, volatile in truth | the solver is right and the input is wrong: the answer concentrates at `effective_assets = 1.0` and carries 3.5× the forward volatility of the well-conditioned case |
| all assets below the risk-free rate | the maximum Sharpe is negative and attained at a corner, not a tangency; the search returns the least-bad portfolio and certifies it, because -1.6 and -2.45 are both honest answers about a set with no positive excess return in it |
| target return above the feasible maximum | `feasible = false`, `verified_optimal = false`, and `weight_bound_violation` carries the size of the shortfall; the note says the bounds are violated, because an unreachable target still has an equality solution — it just requires shorting, and a reader of the note alone must not come away holding a long portfolio |
| an ill-conditioned but nominally positive-definite matrix | `solve` refuses at `rcond < 1e-12` instead of returning large meaningless numbers |

## What this must not be used for

- Not a forecast. `expected_returns` is an input to be supplied; nothing here estimates
  it, and the max-Sharpe arm of the experiment shows what happens when a sample mean is
  mistaken for skill — it is the worst of the four objectives on every forward metric.
- Not a trading system. No transaction costs, no capacity limits, no borrow costs; the
  turnover column is descriptive, not a P&L.
- Not validated on real returns *in this card*. Phase 11's
  `experiments/real_data_risk_study/` ranks sample, EWMA and shrinkage covariance by realised
  out-of-sample portfolio variance over 582 rolling windows of three real FRED factor series and
  gets **ewma < sample < shrinkage** — the two ends of this card's mean forward-variance ratio
  (**shrinkage 1.169 < sample 1.183 < ewma 1.241**) exchange places. Neither result is a bug:
  shrinkage wins where a short window makes the sample covariance unstable, which is the regime the
  synthetic process was built to create. Read as: an estimator ranking is a property of the process
  it was measured on, which is why this card publishes a ratio against an informed solver rather
  than a winner. Cost $0; the series are committed offline fixtures. Every figure above comes from synthetic processes whose
  truth is known analytically, which is what makes the ratios meaningful and also what
  makes them silent about actual markets.
- Not a portfolio for a live book: long-only, fully invested, single-period, and the
  sector, max-position and turnover constraints the spec lists as later options are not
  implemented.

## Reproducing every number on this card

```bash
uv run python benchmarks/pyportfolioopt/optimisation_validation.py   # L2 agreement
uv run python experiments/portfolio_optimization/run.py             # L1/L3 study
uv run pytest -m oracle                                             # the test-level checks
```

Artifacts: `benchmarks/pyportfolioopt/results/optimisation_vs_oracles.{csv,json}`,
`experiments/portfolio_optimization/results/{estimator_out_of_sample,solver_robustness,objective_comparison}.csv`,
`portfolio_optimisation_study.json`, `estimator_cost_by_window.png`. Each carries the
generating command, the package versions, the Git commit of both the tree and the
binary, and a SHA-256 manifest.
