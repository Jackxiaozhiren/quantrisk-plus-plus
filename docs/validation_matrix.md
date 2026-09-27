# Validation Matrix

Every number below is read from a committed artifact or from the assertion in the named
test. None of them was typed from memory, and `uv run python
scripts/run_benchmark_suite.py --no-run` re-checks the artifact-backed ones against the
key path they came from.

This is the table PROJECT_SPEC.md §Phase 10 asks for: **Component · Method · Oracle ·
Tolerance · Status · Evidence artifact**, over the twelve components §2.2 requires us to
own an implementation of.

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
| 1b | Black-Scholes identities | same | put-call parity, `T→0`, `σ→0`, forward-ATM, `d1`/`d2` relation | parity residual **measured** `7.99e-15`; edges exact to machine precision | validated (L1 only) | `experiments/pricing_validation/results/summary.json`; `tests/cpp/test_black_scholes.cpp` |
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

## Three rows that need the prose to be honest

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

## What this matrix does not cover

- **No component is validated against real market data.** Every statistical claim in rows
  4b, 5, 7, 9 and 9b runs on synthetic series whose truth is known. The public data layer
  (Phase 8) is validated for provenance and transport, not for any financial conclusion;
  limitations #28 and #49–52 record the consequence.
- **Single-precision is never claimed.** Everything above is `double`, and the tolerances
  are float64 tolerances.
- **Performance is not correctness.** `benchmarks/performance/results/monte_carlo_speed.json`
  measures one machine: the C++ engine is `8.0–8.4×` pure Python and `0.42×` NumPy for this
  workload — that is, slower than a vectorised NumPy path at 200k paths. The speedup moves
  by several percent between runs, so no single figure from that file should be quoted as
  if it were a constant.
- **The 58 numbered limitations in `docs/limitations.md` are the complete list of what is
  not claimed.** Where a row above says "weaker" or "partially", it points into that file.

## Regenerating

```bash
uv run python scripts/run_benchmark_suite.py            # all 11 members, ~60 s
uv run python scripts/run_benchmark_suite.py --no-run   # re-check the artifact bindings only
uv run python scripts/build_evidence_manifest.py        # re-hash into evidence/manifest.json
uv run python scripts/verify_evidence_manifest.py       # prove nothing changed since
```

The suite runner holds no copy of any number in this file: it reads each one from the JSON
its named script writes, by key path, and aborts if a path has moved. `validation_envelope.png`
is drawn from those same extracted metrics rather than a second pass over the CSVs, so the
figure and this table cannot disagree.
