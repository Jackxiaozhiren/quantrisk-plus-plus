# Phase 6 Report — Portfolio Covariance and Optimisation

Date: 2026-09-27 · Branch: `main` · Status after this phase: **complete and verified**
Research question answered: *do our own covariance estimators and portfolio solvers
agree with independent references on identical inputs, and — the part a benchmark
cannot answer — what does replacing the true covariance with an estimate actually cost?*

## 1. Completed

- **Three covariance estimators** (`cpp/src/portfolio/covariance.cpp`, Eigen-backed):
  unbiased sample (`ddof = 1`), RiskMetrics EWMA filtered **about zero** with `λ` in and
  `half_life` reported, and Ledoit–Wolf (2004) shrinkage with closed-form intensity.
  Every estimate carries its spectrum, `positive_semidefinite` flag and a `note`, so a
  degenerate matrix is described rather than quietly repaired.
- **A guarded linear solve**: `LLT` with refusal when the matrix is not positive
  definite or when `rcond < 1e-12`, returning `NaN` plus a reason instead of large
  meaningless numbers.
- **Mean-variance with a certificate** (`mean_variance.cpp`): active-set search over
  supports, each candidate solved as a **saddle-point KKT system**, the answer verified
  against the original data for primal feasibility, dual feasibility and complementary
  slackness. Target return is tested for inactivity before being imposed as an equality.
- **Maximum Sharpe** by ternary search along the frontier the same QP produces, with the
  linear-fractional reformulation stated in the returned `note` rather than assumed.
- **Equal risk contribution** (`risk_parity.cpp`): cyclic coordinate descent on
  `½ w'Σw − c Σ log wᵢ` with a closed positive root per sweep, reporting per-asset
  `contributions` and `max_contribution_gap`.
- **A two-phase dense primal simplex with Bland's rule** (`linear_program.cpp`), exposed
  on its own so the CVaR construction can be tested independently of the risk measure.
- **CVaR optimisation** (`cvar.cpp`): Rockafellar–Uryasev as a linear program, `α` split
  as `a⁺ − a`, per-scenario excesses `uᵢ`, LP optimality certificate, and the objective
  recomputed from the definition as a cross-check.
- **Python surface**: `quantrisk.portfolio` — 12 functions, 10 bound types, 81 members,
  all container-taking entry points adapted so NumPy arrays and lists both work.
- **Evidence**: `benchmarks/pyportfolioopt/optimisation_validation.py` (75 problems ×
  three solvers) and `experiments/portfolio_optimization/` (3 CSVs, 1 PNG, 1 JSON).
- **One defect found and fixed while writing this report**: an unreachable target return
  returned `feasible = false` with a correct `weight_bound_violation`, but the human
  readable `note` described only the binding target. The note now states the bound
  violation, guarded by a test that provably fails on the pre-fix source.

Suite after this phase: **158 CTest entries, 546,807 assertions in 157 Catch2 cases,
252 pytest tests.**

## 2. Mathematical assumptions

- Returns are monthly, simple, and treated as weakly stationary **within** a window. The
  estimators assume that; the experiment measures what happens when it is false.
- EWMA is filtered about **zero**, not about the sample mean. For monthly returns near
  zero this is the RiskMetrics convention and it is stated, because the two definitions
  differ and a bridge between them has to be asserted rather than discovered.
- Ledoit–Wolf uses the 2004 single-target form with divisor `T` and the closed-form
  shrinkage intensity toward a scaled identity.
- The portfolio problem is `min ½ w'Σw` s.t. `Aw = b`, `w ≥ 0` with `A = [1, μ]` as the
  constraints require. `Σ ⪰ 0` is enough for the objective to be convex; `Σ ≻ 0` is what
  makes the argmin unique, and the singular case is handled by rank-truncated support
  solves that report the truncation.
- Loss convention inherited from Phase 5: `L = −R`.
- CVaR is the Rockafellar–Uryasev sample counterpart at confidence `β`, with the tail
  weight `1 − β` interpolated when `(1 − β)M` is not an integer, matching the NumPy
  linear-quantile convention used everywhere else in the project.
- ERC is defined by `wᵢ (Σw)ᵢ = (1/n) w'Σw` for all `i`, solved as the unique positive
  fixed point; the log formulation of Spinu is the reference route, not our route.

## 3. Files changed

New in this phase (2,695 lines across the layer, bindings included):

| Path | Lines | Role |
| --- | --- | --- |
| `cpp/include/quantrisk/portfolio/covariance.hpp` | 115 | estimates, diagnostics, guarded solve |
| `cpp/include/quantrisk/portfolio/mean_variance.hpp` | 87 | inputs, request, solution |
| `cpp/include/quantrisk/portfolio/risk_parity.hpp` | 53 | ERC solution |
| `cpp/include/quantrisk/portfolio/linear_program.hpp` | 48 | generic LP and status |
| `cpp/include/quantrisk/portfolio/cvar.hpp` | 52 | RU request and solution |
| `cpp/src/portfolio/covariance.cpp` | 291 | three estimators, spectrum, refusal |
| `cpp/src/portfolio/mean_variance.cpp` | 606 | KKT saddle solve, active set, frontier, Sharpe |
| `cpp/src/portfolio/risk_parity.cpp` | 183 | cyclic coordinate descent |
| `cpp/src/portfolio/linear_program.cpp` | 301 | two-phase primal simplex, Bland's rule |
| `cpp/src/portfolio/cvar.cpp` | 161 | RU construction over our LP |

Also changed: `bindings/python_bindings.cpp` (the `portfolio` submodule),
`CMakeLists.txt` (the new sources and the Eigen dependency), `cpp/src/risk/measures.cpp`
(`risk::sample_covariance` now delegates to the portfolio implementation rather than
duplicating the algebra), and `tests/cpp/test_covariance.cpp`.

Evidence and documentation added: the benchmark and experiment scripts above,
`docs/model_cards/portfolio_covariance_and_optimisation.md`, this report, and
`tests/python/test_covariance_vs_oracles.py`,
`tests/python/test_portfolio_optimisation_vs_oracles.py`.

## 4. Tests executed

| File | Cases | Character |
| --- | --- | --- |
| `tests/cpp/test_covariance.cpp` | 15 | L1 identities, degeneracy, refusal, singularity |
| `tests/cpp/test_mean_variance.cpp` | 14 | L1 closed forms, certificates, pathologies, the two new edge cases |
| `tests/cpp/test_risk_parity.cpp` | 6 | L1 independent-asset ERC, contribution identity |
| `tests/cpp/test_linear_program.cpp` | 7 | L1 LPs, degeneracy, infeasible and unbounded detection |
| `tests/cpp/test_cvar.cpp` | 5 | L1 RU against hand-computed tail means |
| `tests/python/test_covariance_vs_oracles.py` | 24 | L2 vs scikit-learn and PyPortfolioOpt |
| `tests/python/test_portfolio_optimisation_vs_oracles.py` | 23 | L2 vs PyPortfolioOpt (SLSQP) and cvxpy (OSQP/SCS) |
| `benchmarks/pyportfolioopt/optimisation_validation.py` | 75 problems | L2 agreement table, all six gate quantities |
| `experiments/portfolio_optimization/run.py` | 1,119 portfolios | L3 forward cost against analytic truth |

Commands, exactly as run:

```bash
cmake --build build/dev -j8
./build/dev/quantrisk_tests
ctest --test-dir build/dev
uv run pytest -q
uv run pytest -m oracle
uv run python benchmarks/pyportfolioopt/optimisation_validation.py
uv run python experiments/portfolio_optimization/run.py
find cpp bindings tests/cpp -name '*.cpp' -o -name '*.hpp' | sort |
  xargs uv run clang-format --dry-run --Werror
uv run ruff check . && uv run ruff format --check .
```

## 5. Exact test results

```
All tests passed (546807 assertions in 157 test cases)
100% tests passed out of 158          (ctest, Total Tests: 158)
252 passed in 7.24s                   (pytest, full suite)
16 passed, 7 deselected               (pytest -m oracle, optimisation file)
clang-format --dry-run --Werror       clean, no diagnostics
ruff check .                          All checks passed!
ruff format --check .                 51 files already formatted
build                                 zero compiler warnings
```

Determinism: `optimisation_vs_oracles.csv` and the reported agreement block are
byte-identical across independent runs, as are all three experiment CSVs.

The new note-disclosure test was falsified before being trusted: with the pre-fix
`mean_variance.cpp` from `HEAD` swapped in and rebuilt, it fails on
`CHECK_THAT(solution.note, ContainsSubstring("bounds are violated"))` at
`tests/cpp/test_mean_variance.cpp:317`; with the fix it passes. The companion
negative-Sharpe test passed against `HEAD` too, which is the evidence that the code was
already right there and the *model card's* original claim about it was wrong.

## 6. Numerical validation

**Level 2 — agreement with independent solvers** (75 problems: 5 asset counts × 3 seeds
× 5 problem families; worst case per family, weights and achieved objective reported
separately and on purpose):

| Problem | vs PyPortfolioOpt (SLSQP) | vs cvxpy (OSQP/SCS) | worst objective gap |
| --- | --- | --- | --- |
| `min_variance` | 3.5e-13 | 2.4e-12 | 7.3e-16 |
| `efficient_return` | 4.0e-13 | 2.4e-12 | 6.5e-14 |
| `maximum_sharpe` | 7.0e-9 | 7.0e-9 | 1.2e-11 |
| `risk_parity` | 1.4e-11 (cvxpy only) | 1.4e-11 | 2.8e-12 |
| `minimise_cvar` | 4.7e-7 | 4.7e-7 (same route) | 4.5e-9 |

Constraints, measured on all 75: worst budget residual **1.4e-12**, worst long-only
violation **exactly 0**. Covariance estimators separately: sample agrees with
`numpy.cov(ddof=1)` to **7.2e-16** relative and Ledoit–Wolf with scikit-learn's
`LedoitWolf` to **7e-19** absolute; EWMA agrees to the same order through an explicitly
asserted convention bridge.

That sample figure nearly got published wrong. scikit-learn's `EmpiricalCovariance` is
the *biased* ML estimator with divisor `T`, while ours is unbiased with `T − 1`, so
comparing the two returns ~6e-6 on a 400-observation window — a convention difference
that looks exactly like a bug. The reference has to be `numpy.cov(ddof=1)` (or the
sklearn matrix scaled by `T/(T − 1)`), and the test says so in its own name.

Two things in this table were *found*, not assumed. The first draft of the benchmark
compared against PyPortfolioOpt's `clean_weights()`, which rounds to five decimals and
zeroes anything under 1e-4 — it floored every disagreement at ~5e-6 and was measuring
that rounding rather than any optimisation; the tests carried the same defect behind a
comment claiming 1e-9 agreement while asserting 5e-5. Reading the raw solver output
instead tightened the quadratic comparisons by roughly seven orders. The second is the
max-Sharpe row: both independent oracles agree with *each other* to ~1e-10 while each
sits ~7e-9 from us, which is our side being the loose one. A full-precision in-process
probe showed the achieved Sharpe matches to ≤1.3e-12 absolute, so the weight gap is the
flat frontier — a 1e-12 bracket on target return maps to ~1e-9 in coordinates at no cost
in objective — and the objective column, not the weight column, is what the claim rests on.

**Level 3 — what estimation costs** (`experiments/portfolio_optimization/`, synthetic
two-regime factor process, forward covariance known in closed form, 1,119 frozen
portfolios scored against the informed optimum for their own forward slice):

| Window | sample | ewma | shrinkage |
| --- | --- | --- | --- |
| 40 | 1.218 | 1.256 | **1.169** |
| 60 | 1.163 | 1.229 | **1.146** |
| 125 | **1.133** | 1.233 | 1.133 |
| 250 | 1.219 | 1.245 | 1.226 |

Findings, each read back out of the artifact rather than typed into the prose:

- Estimation, not optimisation, is the dominant error: the smallest measured penalty is
  ~13 % in forward variance against a worst numerical disagreement of 4.5e-9 — about
  seven and a half orders of magnitude.
- Shrinkage wins where instability bites: at window 40 it lowers the variance ratio
  1.218 → 1.169, cuts turnover 0.207 → 0.138, and raises effective assets 5.10 → 5.97.
- More history is not monotonically better: window 250 is 0.087 *worse* than 125 for the
  sample estimator, because it pools two different joint distributions.
- Non-stationarity dominates estimation error: forward slices crossing the regime break
  cost 1.57–1.60× for every estimator, against 1.07–1.22× inside a single regime.
- The refusal is the point: on a 5-observation window of 8 assets the sample matrix has
  condition number 6.7e17 and the solve refuses, while shrinkage returns a matrix at 8.0
  that solves and costs 0.0086 rather than 0.0111 in forward volatility.
- An optimiser is only as honest as its input: with an asset flat in the sample but
  volatile in the truth, the solver correctly concentrates into it (`effective_assets`
  1.00) and carries 3.5× the forward volatility of the well-conditioned case.
- Each objective wins its own metric, and max-Sharpe — the only one that consumes an
  estimated *mean* — is worst of the four on all three forward metrics (0.0186 vs 0.0117
  forward volatility), which is error maximisation measured rather than asserted.

## 7. Remaining limitations

Recorded in `docs/limitations.md` as entries 36–42; summarised here.

1. **Long-only and fully invested only.** The max-position, sector and turnover
   constraints the spec lists as later options are not implemented.
2. **No expected-return model.** `expected_returns` is an input. Nothing estimates it,
   and the experiment shows the cost of treating a sample mean as skill.
3. **Single-period.** No multi-period rebalancing policy; turnover is reported
   descriptively, never netted against return.
4. **EWMA is filtered about zero** and its ordering in the study is specific to a DGP
   with a step break and no volatility clustering — the case it is designed for is not
   the case tested.
5. **Ledoit–Wolf targets the identity.** No diagonal-target or custom-target variant, so
   the shrinkage benefit is understated for portfolios where variances differ widely.
6. **The simplex is dense and exponential in the worst case.** Fine at the sizes tested
   (≤12 assets, 250 scenarios); not a production LP.
7. **Every validation number is synthetic.** No claim is made about realised markets.

## 8. Technical debt

- `risk::sample_covariance` now delegates to `portfolio::sample_covariance`, but
  `risk::` still owns return-series algebra (`returns`, `quantile`) that is really
  portfolio-layer furniture. The clean split is a `core/` or `linalg/` home for it.
- `maximum_sharpe` costs ~100 QP evaluations per call. The unit-excess-return
  reformulation (`min ½w'Σw` s.t. `(μ−rf)'w = 1`, `w ≥ 0`, then rescale) is the same
  constraint class the active set already handles and would return machine-precision
  weights with a certificate. Deliberately not done in this phase: the current answer is
  certified and agrees to 1.2e-11 in objective, so the rewrite buys speed and coordinate
  tightness, not correctness.
- The benchmark duplicates the cvxpy column into the PyPortfolioOpt slot for risk parity
  (no ERC in 1.6.0) and vice versa for CVaR (pypfopt solves it *through* cvxpy). Both are
  labelled with an `oracle_note`, but a single "not applicable" value would read better
  than a labelled duplicate.
- `PortfolioSolution` has `feasible`/`verified_optimal` while `CvarSolution` has a
  machine-readable `status` enum. Unify in Phase 9's facade work.
- `-Wall -Wextra -Wpedantic` still applies to `quantrisk_core` only, not to tests or
  bindings. This phase's unused-variable warning surfaced only because the file was
  recompiled; carrying it in the test target would have caught it earlier.
- The experiment's robustness arm draws its forward sample once per case. The exact
  `forward_volatility_under_truth` column is what the argument uses, and the noisy column
  is labelled, but averaging over draws would be better.

## 9. Gate

| Requirement (PROJECT_SPEC.md §Phase 6) | Verdict | Evidence |
| --- | --- | --- |
| Constraints satisfied | **met** | worst budget residual 1.4e-12, worst long-only violation 0.0 across 75 problems |
| Objective sensible | **met** | each solver's own objective compared at full precision; L3 shows min-variance best on variance and max-Sharpe worst on all forward metrics |
| Benchmark agreement | **met** | ≤2.4e-12 weights / ≤6.5e-14 relative objective on the quadratics; ≤4.5e-9 relative on the CVaR LP; ERC ≤1.4e-11 |
| Covariance instability explicitly handled | **met** | spectra and condition numbers on every estimate, `solve` refuses below `rcond 1e-12`, shrinkage offered as the documented route, and the refusal is measured to cost less forward than the answer it replaced |
| Own implementation (§2.2) | **met** | active set, coordinate descent and two-phase simplex are ours; no oracle is imported by the library and no reference value is transcribed |
| Nothing paid for (§3) | **met** | Eigen, PyPortfolioOpt, cvxpy, scikit-learn, OSQP, SCS — all open source, all dev/test only |
| No fabricated number (§4) | **met with one self-correction** | the first benchmark draft measured `clean_weights()` rounding and the test header claimed 1e-9 while asserting 5e-5; both found and fixed in this phase, and the model card's "no finite Sharpe" claim was disproved by testing the code path and rewritten |

**Gate: PASS.** Phase 6 is complete and verified. Next: Phase 7 — the stress-testing
subsystem, which is where the covariance matrices built here get shocked rather than
estimated.
