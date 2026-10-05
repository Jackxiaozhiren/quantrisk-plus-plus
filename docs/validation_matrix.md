# Validation Matrix

Every number below is read from a committed artifact or from the assertion in the named
test. None of them was typed from memory, and `uv run python
scripts/run_benchmark_suite.py --no-run` re-checks the artifact-backed ones against the
key path they came from.

This is the table PROJECT_SPEC.md §Phase 10 asks for: **Component · Method · Oracle ·
Tolerance · Status · Evidence artifact**, over the twelve components §2.2 requires us to
own an implementation of. It has twenty-five rows rather than twelve because a component validated
two ways gets two rows — Black-Scholes has its oracle comparison and its identity checks, Monte
Carlo has its price and its coverage, the backtest machinery has its synthetic arm and its
real-data arm — and collapsing those would hide exactly the difference that matters: which rows
have an independent implementation on the other side and which do not.

## How to read the columns

**Method** names *our* implementation — the C++ entry point that produces the number.
Where §2.2 lists one component that is really several routines (Greeks, optimization),
the row names each of them, because they are validated differently.

**Oracle** names the independent implementation the result is compared against, and says
whether it was called live or whether the comparison is analytic. QuantLib 1.43,
SciPy 1.18.1, scikit-learn 1.9.1, NumPy 2.5.3, PyPortfolioOpt 1.6.0 and cvxpy 1.9.3 are
oracles here and nowhere else: no price, risk measure or weight in the library is
delegated to them (PROJECT_SPEC.md §2.2).

**Tolerance** is the bound the *test* asserts, not the error measured. The measured value
is quoted next to it so the margin is visible. `docs/validation_protocol.md` §2 governs
how a bound may be set: derived from oracle stopping tolerance and curvature where theory
allows it, labelled as measured where it does not. A tolerance that was chosen by
watching a number is marked *(measured)*.

**Status** takes one of four values, and the difference between the last two matters:

| Status | Meaning |
|---|---|
| `validated` | an independent oracle agrees within the stated bound |
| `validated (L1 only)` | agrees with a closed form or an identity it must satisfy; no second implementation exists |
| `partially validated` | one arm has an oracle and another does not, and the row says which |
| `weaker than claimed` | the comparison exists but the oracle is not tight enough to bound the claim — recorded, not smoothed over |

## The matrix

| # | Component | Method (ours) | Oracle | Tolerance | Status | Evidence artifact |
|---|---|---|---|---|---|---|
| 1 | **Black-Scholes** | `pricing.black_scholes` (Merton with continuous dividend yield) | QuantLib 1.43 `AnalyticEuropeanEngine`, called live | `1.0e-10` rel + `1.0e-12` abs, 5 curated cases (`test_pricing_vs_quantlib.py:30`) — **measured** `3.46e-11` rel / `1.49e-13` abs worst over 18,816 grid rows | validated | `benchmarks/quantlib/results/pricing_vs_quantlib.json`, `.csv` |
| 1b | Black-Scholes identities | same | put-call parity, `T→0`, `σ→0`, forward-ATM, `d1`/`d2` relation | parity residual **measured** `8.12e-15`; edges exact to machine precision | validated (L1 only) | `experiments/pricing_validation/results/summary.json`; `tests/cpp/test_black_scholes.cpp` |
| 2 | **Greeks** | `pricing.black_scholes_greeks` analytic; `pricing.finite_difference_greeks` central differences under a `BumpPolicy` | QuantLib `delta/gamma/vega/rho/theta` live; analytic delta against central finite differences | `1.0e-8` rel + `1.0e-9` abs on the 5-case grid (`test_pricing_vs_quantlib.py:31`); the FD error must fall as `O(h^2)` — **measured** delta `1.00e-10`, gamma `3.17e-13`, vega `3.29e-13`, theta `2.53e-10`; rho `1.07e-7` rel over the wide sweep (abs `5.12e-13`) | validated, with the rho caveat below | `benchmarks/quantlib/results/pricing_vs_quantlib.json`; `quantrisk validate` (analytic-vs-FD gap `6.39e-5 → 1.60e-5 → 3.99e-6` under bump halvings, ratios `4.00` and `4.00`) |
| 3 | **Binomial (CRR)** | `pricing.crr_binomial` for European and American exercise | QuantLib binomial engines; the analytic BS limit | no fixed bound — the claim is an order, not a point. **Measured** `|ours−QuantLib|` `1.82` at 50 steps → `0.114` at 800; fitted `log(error)/log(steps)` slope `−0.99405 ± 0.00313` against theory `−1` (1.90 SE) | validated | `benchmarks/quantlib/results/pricing_vs_quantlib.json`; `experiments/pricing_validation/results/lattice_convergence.csv` + `.png` |
| 4 | **Monte Carlo** | `monte_carlo.MonteCarloEngine` drawing from the project `Rng` | analytic Black-Scholes (the exact expectation) and QuantLib's analytic value | `4.0 ×` combined standard error (`test_monte_carlo_vs_oracles.py:90`). **Measured** pooled z over 160 runs: plain mean `0.031`, std `0.930`; `O(1/√N)` slope `−0.6141 ± 0.0888` vs theory `−0.5` (1.28 SE) | validated | `benchmarks/quantlib/results/monte_carlo_validation.json`; `experiments/monte_carlo_convergence/results/summary.json` |
| 4b | Monte Carlo CI coverage | `confidence_interval` on the estimator | exact binomial band around the nominal level | 12/12 intervals inside the binomial band | validated | `experiments/monte_carlo_convergence/results/coverage.csv` + `convergence_slope.png` |
| 5 | **Variance reduction** | `VarianceReduction.ANTITHETIC` pairs; `CONTROL_VARIATE` with `beta` fitted in-sample | analytic BS as truth; out-of-sample MSE over 40 seeds | MSE ratio must exceed 1. **Measured** `1.1155`–`40.468` across the 24 non-plain cells | validated | `experiments/variance_reduction/results/summary.json`, `realised_error.csv` |
| 6 | **Heston** | `stochastic.simulate_heston` / `price_heston_european` (full-truncation Euler); `monte_carlo.price_barrier`, `price_asian` | QuantLib Heston analytic (integration tolerance applies); the `ξ = 0` collapse to BS | `4.0 ×` standard error on the MC arm. **Measured** `4.467e-3` vs the analytic oracle, `2.095e-3` on the degenerate `ξ = 0` arm | partially validated — see limitations #25–27 | `benchmarks/quantlib/results/path_dependent_vs_quantlib.json`; `tests/cpp/test_heston.cpp` |
| 7 | **VaR** | `risk.historical_var`, `risk.gaussian_var`, `risk.monte_carlo_var` | SciPy quantiles; NumPy order statistics recomputed from the definition; closed form | `1.0e-12` rel (`test_risk_measures.py:33`). **Measured** Gaussian 95% bias at n=250: `−8.23e-5`; realised violation at 99% on t(3): `1.389%` Gaussian vs `1.021%` historical vs `1%` nominal | validated | `experiments/var_backtesting/results/var_backtesting_validation.json`, `estimator_convergence.csv` |
| 8 | **Expected Shortfall** | `risk.historical_es`, `risk.gaussian_es`, `risk.monte_carlo_es` | SciPy numerical integration of the tail mean; `σφ(z)/α` closed form | `1.0e-10` rel on the closed form (`tests/cpp/test_risk.cpp:87`); ES ≥ VaR and monotone in α asserted by `test_es_at_least_var_and_both_grow_with_the_confidence_level` | validated | `tests/python/test_risk_measures.py`; `docs/model_cards/var_es.md` |
| 9 | **Backtesting** | `risk.kupiec_pof_test`, `risk.christoffersen_independence_test`, `risk.christoffersen_conditional_coverage_test`, composed by `risk.backtest_var` | SciPy chi-square survival function supplies both the p-value *and* the critical value, so they cannot drift apart | exact binomial interval on the reject rate at 1/5/10% nominal. **Measured** `0.0505` at 5% nominal on calibrated data, KS distance `0.1174`; on clustered data Kupiec `0.120` vs independence `0.554` | validated | `experiments/var_backtesting/results/coverage_test_size_power.csv`, `pvalue_uniformity.png` |
| 9b | Bootstrap intervals | `risk.bootstrap_var` / `risk.bootstrap_es` with `IID` or `MOVING_BLOCK` | truth known by construction on synthetic data; exact binomial band on coverage | nominal 90%. **Measured** `0.8725` iid-design on iid data, `0.625` iid-design on clustered data, `0.6925` block-design on clustered data | partially validated — the shortfall is the claim, not a defect | `experiments/var_backtesting/results/bootstrap_coverage.csv`; limitations #31–33 |
| 10 | **Covariance** | `portfolio.sample_covariance`, `portfolio.ewma_covariance` (RiskMetrics, about zero), `portfolio.shrinkage_covariance` (Ledoit–Wolf 2004 target) | `numpy.cov(ddof=1)`; scikit-learn `LedoitWolf`; PyPortfolioOpt EWMA after a convention bridge | `1.0e-12` rel (`test_covariance_vs_oracles.py:22`) — **measured** sample `7.2e-16`, Ledoit–Wolf `7e-19` abs, EWMA `<1e-13`, shrinkage intensity `<1e-9` | validated | `tests/python/test_covariance_vs_oracles.py`; `docs/model_cards/portfolio_covariance_and_optimisation.md` |
| 11 | **Optimization** | `portfolio.minimum_variance`, `efficient_frontier`, `maximum_sharpe`, `risk_parity`, `minimise_cvar` | cvxpy (OSQP `eps_abs=eps_rel=1e-11`, SCS) and PyPortfolioOpt SLSQP on identical inputs, 75 problems | per problem, all *(measured)*: quadratic weights `1e-11` / value `1e-13`; Sharpe weights `1e-7`; ERC `1e-9`; CVaR weights `1e-5` / value `1e-6` (`test_portfolio_optimisation_vs_oracles.py:50-56`). **Worst observed** objective gap `4.484e-9`, weight gap `4.663e-7`, budget residual `1.450e-12`, bound violation `0` | validated | `benchmarks/pyportfolioopt/results/optimisation_vs_oracles.json`, `.csv` |
| 12 | **Stress engine** | `stress.run_scenario` (delta-gamma P&L map), `run_historical_scenarios`, `run_monte_carlo_scenarios`, `shift_covariance`; attribution and the level/dispersion split are fields on `ScenarioResult` | full Black-Scholes re-pricing of the same book (L2); accounting identity and Euler allocation (L1); parametric vs simulated VaR (L3) | `1.0e-9` rel on the Gaussian closed form, `abs 1e-8` on attribution residuals (`test_stress_vs_oracles.py:35`); MC arm `2%` rel. **Measured** factor and position attribution residuals `0.0`, VaR decomposition residual `0.0`; linearisation error `1.33e-4` at a 1% shock → `0.488` at 40% | validated for the map and the accounting; the *scenario set* has no oracle — it is a choice, not a computation | `experiments/stress_testing/results/stress_testing_study.json`, `linearisation_error.csv` + `.png` |
| 13 | **Same estimators on real market data** | rows 7, 9, 9b and 10 re-run on 586 out-of-sample days of three FRED series (10y par yield, 10y breakeven, VIX), trailing 250-day windows | **none, by construction.** A sample carries no independent truth, which is why this row reports realised violation rates with exact binomial intervals rather than an error against an oracle | no tolerance: the interval *is* the claim. **Measured** Gaussian 99 % realised `2.048 %` `[1.062 %, 3.550 %]` — excludes nominal; historical 99 % `1.365 %` `[0.591 %, 2.672 %]` — covers it. Kupiec `0.160`, independence `0.287`, conditional coverage `0.211`: no test rejects | validated (L1 only) — the arithmetic and the intervals are checkable, the calibration claim is an empirical one and is labelled as such | `experiments/real_data_risk_study/results/real_data_risk_study.json`, `real_data_violation_coverage.png`; limitations #61–62 |

| 14 | **Third and fourth spot sensitivities** | `pricing.black_scholes_spot_derivatives` (closed forms `V^{(3)} = -(\Gamma/S)(1 + d_1/v)` and `V^{(4)} = (\Gamma/S^2)(A^2 + A - 1/v^2)`) | a five-point central difference of this project's own gamma (and of the closed third derivative), plus a difference of QuantLib's delta for the third | asserted in C++ and Python at `abs 1e-9` with the step justified next to the tolerance. **Measured** `2.0e-15` / `1.0e-15` at the reference point, worst over the 7-rung ladder `5.0e-14` / `1.3e-13`; call/put equality exact | validated, with the caveat in limitation #65: no reference library in this dependency set publishes either derivative, so the anchor is a difference scheme and a shared-gamma risk remains | `tests/cpp/test_black_scholes.cpp`, `tests/python/test_linearisation_bound.py` |
| 15 | **Stress-map truncation bound** | `stress.run_scenario`'s delta-gamma map against its own Taylor remainder: `|R| <= (1/6) sup|V^{(3)}| |h|^3`, and the sharp Lagrange trapping of `c = 6R/h^3` between the path's extremes of `V^{(3)}` | none available in the oracle sense: a remainder is not a second implementation of a price. The check is that the coefficient must lie inside a range computed from the same closed forms along the segment | **Measured** 0 violations over 618 shocks (18 swept, 600 dense); `|R|/bound` from 0.9962 to 0.2842; slope `2.9710 -> 2.9988` down and `3.0253 -> 3.0012` up as the window shrinks; remainder zero at a 21.1447 % move, inside the published 20-30 % sign-change bracket | validated (L1 only) — an identity and an inequality, checked against data frozen before the derivation | `experiments/linearisation_error_bound/results/linearisation_error_bound.json`, `docs/analysis/delta_gamma_error_bound.md` |
| 16 | **Mixed spot/volatility sensitivities** | `pricing.black_scholes_vol_cross_derivatives` (vanna `= -e^{-qT} phi(d1) d2 / sigma`, volga `= vega d1 d2 / sigma`) and `black_scholes_mixed_third_derivatives` (`V_SSsigma`, `V_Sssigma`, `V_Sssss`) | **no oracle exists in this dependency set**: QuantLib 1.43's `VanillaOption` surface stops at delta/gamma/vega/theta/rho. The checks are five-point differences taken along the *other* factor (Schwarz makes the two vanna routes independent of each other), the exact identities obtained by differentiating `vega = gamma S^2 sigma T`, and call/put parity | slope routes `1e-8` relative + `1e-13` absolute, curvature routes `1e-4` + `1e-8` because a second stencil cannot share a band with a first. **Measured** worst residual 1.6e-2 of its own band over a 9-rung ladder; the two vanna routes agree to 1.4e-7 with no formula on either side; identities to 1.1e-16 / 4.3e-14; call/put equality exact; 9 deliberate transcription slips all caught | validated (L1 only) — differences and identities, not a second implementation; limitation #70 names the gap | `tests/cpp/test_black_scholes.cpp`, `tests/python/test_two_factor_bound.py` |
| 17 | **Two-factor truncation bound** | the map's joint-shock error against `vanna*h*k + 0.5*volga*k^2` plus `(1/6) g'''(xi)`, where `g'''` is the third directional derivative along the ray `(h, k)` | none in the oracle sense — a remainder is not a second price. The check is that `6*(error - quadratic)` must lie inside the segment's own range of `g'''`, re-derived in Python as a third difference of the *price* | **Measured** 0 violations over 132 joint shocks up to a 30 % equity move with +20 vol points; fitted slope of the error against shock size converges to 2.0 on all four joint rays (1.9975 narrowest) and stays 3.0 on a pure-spot ray; on the published `risk_off` the error −5320.79 lies in [−6063.95, −4135.87], which excludes zero | validated (L1 only) — an inequality plus an identity, and the leading term is *not* the largest term at published sizes (limitation #68) | `experiments/two_factor_error_bound/results/two_factor_bound.json`, `docs/analysis/two_factor_error_bound.md` |
| 18 | **Re-struck-gamma map, measured** | the four map variants in `experiments/restrike_gamma_map/run.py` — exposures all at base, gamma at `(S, sigma+k)`, gamma at `(S+h, sigma+k)`, all three at the shocked market — each priced through `stress.run_scenario` against a revaluation of the same book | none in the oracle sense: the comparison is between approximations of one revaluation. The check is that the re-struck map differs from the shipped one by exactly `(gamma(sigma+k) - gamma(sigma)) * delta^2`, with the divided difference trapped by the segment range of `d gamma / d sigma` from `black_scholes_mixed_third_derivatives`, and that the base map's `risk_off` error is the number row 17's artifact publishes | **Measured** 7 probes, 0 inclusion violations, worst map-difference mismatch 3.7e-15; `k = 0` identity to 0.0; `risk_off` error −5320.79 → +1937.72 (factor 0.364), removing 7258.51 of the 8402.16 term (86.4 %); improves 75 of 120 cells (62.5 % by count, 0.3704 by value), leaves 45 no better and doubles 20 of them, worst factor 142, all of them cancellation cells; naive full re-strike worse on 116 of 120 and by a factor of 11 on `risk_off`; local slope between the two narrowest scales 1.98-2.01 for all four maps | validated (L1 only) — arithmetic identities plus a grid measurement on one book, and the recommendation is *not* uniform (limitation #78) | `experiments/restrike_gamma_map/results/restrike_gamma_map.json`, `restrike_gamma_map.csv`, `cancellation_columns.csv`, `docs/analysis/restrike_gamma_map.md` |
| 19 | **Fourth-order crossing radius** | the base map's error along each `delta` column, truncated at order three (v1.5.0's polynomial, imported from that experiment) and at order four with `black_scholes_mixed_fourth_derivatives`, each set of zeros found by the same bracket-and-bisect and compared with the priced error's zeros | none in the oracle sense: a truncation is not a second price. The checks are that the order-four piece is exactly the documented `1/24 (V_SSSS h^4 + 4 V_SSSsigma h^3 k + 6 V_SSsigmasigma h^2 k^2 + 4 V_Ssigmasigmasigma h k^3 + V_sigmasigmasigmasigma k^4)` contraction, that three of the four new coefficients are five-point volatility slopes of the partial one order below, and that the residuals fall with the slopes a cubic and a quartic truncation must leave | **Measured** cubic residual slope 3.96-4.37 against quartic 4.73-5.01 over `1e-3 <= scale <= 3e-1` (through-the-floor: 2.46-4.30, published as the reason the window is cut there); residual-ratio slope 0.62-1.04, ratio 0.0013-0.048 at `scale = 3e-3`; nearest crossing distance <= 0.00162 on all seven in-range columns that have a priced zero against the cubic's 0.01887 (factor 11.6, and 211.6 inside the published 0.05 limit); 13 priced zeros, 14 cubic, 14 quartic, column-level disagreements 3 -> 1 but a different column; `risk_off` amount error 22.3 % -> 16.2 % with the sign flipped, and 1.38x *worse* on one ray at full shock size; coefficient slopes agree to < 1e-4 relative | validated (L1 only) — identities plus self-consistency of a truncation against a revaluation on one book, and the widened radius is about the place of the crossing, never its amount (limitation #79) | `experiments/fourth_order_crossing_map/results/fourth_order_crossing_map.json`, `fourth_order_crossing_columns.csv`, `fourth_order_residual_rays.csv`, `docs/analysis/fourth_order_crossing_map.md` |
| 20 | **Crossing radius on five books** | the same column truncations as row 19, rebuilt for five books at once in `experiments/second_book_crossing_map/run.py` -- the published ladder, a long-dated wide book, a short-dated tight one, a deep out-of-the-money ladder and an in-the-money mirror -- each radius found by the contiguous paired-magnitude rule against v1.5.0's own 0.005 tolerance | none in the oracle sense: whether a radius transfers is not a second price. The checks are that the re-derived machinery is *bit-identical* to v1.5.0's and v1.6.0's where all three are defined (ten book coefficients, both truncations and the engine P&L over 30 joint moves, every difference exactly zero), that the published book's radii come back at 0.05 and 0.15, and that every radius is re-computed from the per-column distances beside it | **Measured** cubic radii 0.02 / 0.05 / 0.05 / 0.10 / 0.15 and quartic 0.05 / 0.10 / 0.15 / 0.20 / 0.30; quartic at least cubic on 5 of 5 books, factors 1.3 to 3.0; the quartic's worst distance inside the cubic's own radius smaller on 5 of 5 (1.15e-05 to 2.13e-04 against cubic 5.36e-04 to 2.73e-03); the order-four-to-three ratio spans 0.015 to 3.887 and does not order the widening | validated (L1 only) -- the direction transfers, the magnitude and the mechanism do not, and a radius is a grid label rather than an accuracy claim (limitation #81) | `experiments/second_book_crossing_map/results/second_book_crossing_map.json`, `second_book_columns.csv`, `docs/analysis/second_book_crossing_map.md` |
| 21 | **Mixed fifth-order sensitivities** | `pricing.black_scholes_mixed_fifth_derivatives` (the six partials of total order five, each `P * S^(1-n_spot) * T^(n_vol/2) * R(d1, v) / v^4` for a numerator polynomial derived symbolically from the price function and re-obtained by Richardson refinement) | **no oracle exists in this dependency set**: QuantLib 1.43's `VanillaOption` surface stops at order two, and no library here publishes a fifth partial. The checks are ten five-point slope routes taken of partials the core shipped before this phase -- each fifth partial reached as `d(V_SSSS)/dS` and `d(V_SSSsigma)/dS` etc., so no route reuses the formula under test -- plus the multinomial contraction against five *nested* differences of `black_scholes` itself (row 1), exact call/put parity and the degenerate limit | C++ band `1e-8 * |route| + 1e-13` per comparison; Python `1e-3` relative, best of 0.2 %-1 % steps. **Measured** worst of the ninety C++ comparisons 1.9e-3 of its own band (`V_SSSsigmasigma` along the spot axis); Python loosest route 1.5e-4 relative at the finest rung, volatility-axis routes near 1e-9; contraction 4.8e-3 / 1.0e-4 / 5.5e-4 against a 5e-2 band at the widest rung, 6.7 at the finest because five nested divisions by the scale are round-off dominated; call/put equality exact; degenerate limit zero | validated (L1 only) -- the numerator polynomials are an identity against the symbolic derivative of the price (8.7e-58 worst relative over 60 markets, re-runnable), the compiled extension meets 60-digit nested differentiation at 4.6e-15 on four markets, and the five fields reached by difference routes are anchored by this project's own fourth-order family rather than by a second implementation; shipping the terms buys no statement about the crossing map, which was deliberately not measured (limitation #82) | `tests/cpp/test_black_scholes.cpp`, `tests/python/test_fifth_order_partials.py`, `scripts/derive_fifth_order_partials.py`, `docs/phase_reports/phase-20-fifth-order-partials.md` |
| 22 | **Order-five crossing radius, measured** | the same five books, the same delta grid, the same 0.005 tolerance and the same contiguous paired-magnitude rule as row 20, with the six mixed fifth partials contracted along each column's `(h, k)` and added to the quartic truncation -- all of it imported from `experiments/second_book_crossing_map/run.py`, which imports v1.5.0's and v1.6.0's own files | none in the oracle sense: whether a radius widens again is not a second price. The checks are that the shipped equality gate ran (coefficients, both lower truncations and the engine P&L over 30 joint moves bit-identical), that the published book's cubic and quartic radii come back at 0.05 and 0.15, that every radius is re-computed from the per-column distances beside it, and that the multinomial contraction meets five nested differences of the *revalued book* | **Measured** radius grows again on 2 of 5 books (published ladder 0.15 -> 0.20, factor 1.33 against its own cubic-to-quartic 3.00; deep out of the money 0.20 -> 0.30, factor 1.50) and is unchanged on 3; the quintic is the closest of the three orders inside the quartic's radius on 5 of 5; 48 of 60 columns carry a priced crossing; 2 books sit at the swept grid edge; the order-five-to-four piece ratio spans 0.057 to 0.588 and does not order the widening; contraction errors 1e-05 to 8e-04 relative at the widest rung against a 5e-2 band | validated (L1 only) -- direction, not size, and a radius is a grid label; two of the three unmoved books are unresolvable rather than negative (limitation #83) | `experiments/fifth_order_crossing_map/results/fifth_order_crossing_map.json`, `fifth_order_radii.csv`, `fifth_order_columns_*.csv`, `docs/analysis/fifth_order_crossing_map.md` |

## Five rows that need the prose to be honest

**The rho tolerance is not one number.** `test_pricing_vs_quantlib.py` asserts `1e-8`
relative on five curated cases and passes. The benchmark sweeps 18,816 rows including
negative rates and 100% volatility, where rho passes through zero: an absolute error of
`5.12e-13` on a rho of `4.8e-6` is a relative error of `1.07e-7`, which is a larger *number*
and a smaller *problem* than the same relative error on a rho of 50. That is why the
benchmark reports errors above an absolute floor (`greek_floor = 1e-06`) separately from
the raw absolute worst case, and why this row quotes both. Quoting only the relative
figure would overstate the error; quoting only the absolute one would hide where the
relative figure comes from.

**The binomial row asserts a rate, not a value.** A CRR lattice at 50 steps is *expected*
to be `1.82` away from the analytic price on the worst row of the sweep — that is the
`O(Δt)` truncation the model card derives, not a disagreement with QuantLib. The falsifiable
claim is the slope: `−0.99405 ± 0.00313` against a theoretical `−1`, which is 1.90 standard
errors away. A single "error < 1e-6" line here would have been a false claim about a lattice.

**The stress engine's oracle covers the arithmetic, not the scenario.** Re-pricing the same
three-strike book through Black-Scholes bounds the delta-gamma map and nothing else: it says
the map is a correct second-order Taylor expansion, and it says how fast that stops being
true (`0.488` relative error at a 40% equity fall). It says nothing about whether
"equity −20% with correlations +0.2" is the right scenario to run, because there is no
independent implementation of a management assumption. The attribution and decomposition
residuals are exactly zero, which is an identity check on our own algebra — necessary, and
not evidence about markets.

**The new sensitivities have no oracle, and the row says so.** QuantLib 1.43 as installed here
exposes `delta`, `gamma`, `vega`, `theta`, `rho` and nothing second-order in two factors: `vanna`,
`volga` and `speed` are not in its Python surface. So row 16 is validated by finite differences
taken along the *other* factor, by identities derived from `vega = gamma S^2 sigma T`, and by
parity — which is stronger than it sounds (the two routes to vanna share no formula, and agree to
`1.4e-7` with no closed form on either side) but is still L1, not a comparison against someone
else's implementation. A wrong gamma would contaminate both sides of some of these checks, which
is limitation #70 rather than a footnote here.

**On the two-factor row the leading term is not the largest term.** Row 17's claim is that the
map's joint-shock error is quadratic, and the fitted slope confirms it (2.0 on four rays, 3.0 on a
pure-spot ray). At the size the published `risk_off` scenario uses, the quadratic is `+788` and the
error is `−5321`: the leading term of the limit points the wrong way, because a cubic term
`0.5 V_SSsigma h^2 k` — gamma applied at a volatility the move has already changed — is 10.7× the net quadratic — or 7.4× against its two contributions summed in absolute value
What survives at every size is the *inequality*, which holds on 132/132 swept shocks. Quoting the
order without the size would read as "expect ~800 of error" where the defensible statement is
"between 4136 and 6064, and the sign is negative".

## What this matrix does not cover

- **No component is validated against real market data.** Every statistical claim in rows
  4b, 5, 7, 9 and 9b runs on synthetic series whose truth is known. The public data layer
  (Phase 8) is validated for provenance and transport, not for any financial conclusion;
  limitations #28 and #49–52 record the consequence.
- **Single-precision is never claimed.** Everything above is `double`, and the tolerances
  are float64 tolerances.
- **Performance is not correctness.** `benchmarks/performance/results/monte_carlo_speed.json`
  measures one machine: the C++ engine is `7.77×`–`8.70×` pure Python and `0.42×`–`0.51×` NumPy
  over the runs this repository has committed — that is, slower than a vectorised NumPy path at
  200k paths on every one of them. The ratios move by more than 10% between runs, so no single
  figure from that file should be quoted as if it were a constant.
- **The 84 numbered limitations in `docs/limitations.md` are the complete list of what is
  not claimed.** Where a row above says "weaker" or "partially", it points into that file.

## Regenerating

```bash
uv run python scripts/run_benchmark_suite.py            # all 18 members
uv run python scripts/run_benchmark_suite.py --no-run   # re-check the artifact bindings only
uv run python scripts/build_evidence_manifest.py        # re-hash into evidence/manifest.json
uv run python scripts/verify_evidence_manifest.py       # prove nothing changed since
```

The suite runner holds no copy of any number in this file: it reads each one from the JSON
its named script writes, by key path, and aborts if a path has moved. `validation_envelope.png`
is drawn from those same extracted metrics rather than a second pass over the CSVs, so the
figure and this table cannot disagree.
