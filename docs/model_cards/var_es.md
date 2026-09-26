# Model card — market risk: VaR, expected shortfall, bootstrap intervals, coverage backtests

Phase 5 · written 2026-09-26 · status: implemented, validated on synthetic data with
known population values. No real return series is used anywhere in this card.

## What is implemented

`cpp/include/quantrisk/risk/` (mirrored one-for-one by `quantrisk.risk` in Python;
the bindings convert containers and add no numerics):

| Entry point | Estimator | Estimator formula, stated so it can be checked |
| --- | --- | --- |
| `returns::arithmetic` / `returns::log_returns` | return definitions | `R_t = (P_t - P_{t-1})/P_{t-1}`, `r_t = ln(P_t/P_{t-1})` |
| `risk::historical_var` | empirical VaR | linear-interpolated `alpha`-quantile of `L = -R` (NumPy `method="linear"` convention) |
| `risk::historical_es` | empirical ES | mean of the `k = ceil(n (1 - alpha))` largest losses |
| `risk::gaussian_var` | variance-covariance VaR | `-mu_hat + z_alpha sigma_hat`, `z_alpha = Phi^-1(alpha)` |
| `risk::gaussian_es` | variance-covariance ES | `-mu_hat + sigma_hat phi(z_alpha) / (1 - alpha)` |
| `risk::monte_carlo_var` / `monte_carlo_es` | simulated P&L | same two estimators on simulated profit-and-loss (negative = loss); the VaR variant also reports the quantile standard error `sqrt(alpha (1 - alpha) / n) / f(x_alpha)` |
| `bootstrap_var` / `bootstrap_es` | interval uncertainty | iid and moving-block percentile intervals, block length default `round(n^(1/3))` |
| `flag_violations`, `kupiec_pof_test`, `christoffersen_independence_test`, `christoffersen_conditional_coverage_test`, `backtest_var` | coverage tests | violation := `loss > VaR_t`; LR statistics against chi-square(1), chi-square(1), chi-square(2) |

Loss convention is frozen: `L = -R`, positive numbers are losses, larger is worse.
`mu_hat` uses the sample mean and `sigma_hat` the unbiased (`ddof = 1`) sample
standard deviation, both by compensated summation.

## The distinctions that matter

**VaR is not estimable as well as ES is.** VaR is a quantile: its estimator is one
or two order statistics, so its sampling error is set by the density at the tail
point. ES averages the whole tail, so it is far better conditioned at equal `n`.
`quantile_standard_error` returns NaN rather than a plausible-looking zero when the
loss distribution has a flat spot at that level (a tie — common for option P&L, where
most paths finish worthless), because a density of zero means the quantile is not
locally identified.

**A confidence level is not the same statement as a violation rate.** Kupiec's POF
test asks whether the *count* of violations matches `n (1 - alpha)`. Christoffersen's
independence test asks whether *when* they arrive is uninformative. They are
complementary, and a model can pass one and fail the other; the measured numbers
below show exactly that. The conditional-coverage statistic is their sum on 2 degrees
of freedom, which is only a valid chi-square test because the two components are
asymptotically orthogonal.

**These tests are asymptotic and weak at realistic sample sizes.** Two years of
daily data is 500 observations, at 95 % that is 25 expected violations, at 99 % it is 5.
The reported `interpretation` string and `degenerate` flag are there to keep a null
result from being read as a clean bill of health: the independence statistic is not
estimable at all when a state has no transitions, and that case reports NaN rather
than a p-value of 1.

**Critical values are solved, not tabulated.** `chi_square_isf` inverts the same
survival function the p-value is computed from, so a test statistic and its 5 %
threshold cannot disagree because one of them was mistyped. This was not a
hypothetical: two expected values written into this phase's own tests from memory
were wrong — a 5 % point labelled "5 dof" that in fact belongs to 4 dof, and a
chi-square tail value that disagreed with the closed form `exp(-x / 2)` for 2 dof.
Both were caught by running the tests, and every number in the table above is now
either derived from a closed form or produced by a live oracle call.

## Validation evidence

Level 1 (definition and closed form), Level 2 (live SciPy oracle), Level 3 (statistical
behaviour over replications). Regenerate with
`uv run python experiments/var_backtesting/run.py` (~25 s, all streams seeded).

| Question | Measured | Source |
| --- | --- | --- |
| Does each estimator hit its own formula? | historical VaR/ES match `np.quantile` and the explicit tail mean; Gaussian VaR matches `scipy.stats.norm.ppf`; Gaussian ES matches a **quadrature** `E[L | L > VaR]`, not the closed form | `tests/python/test_risk_measures.py` |
| Bias at n = 250, 95 % Gaussian data | `-8.2e-05` against a population value of 0.0329 (0.25 % relative) | `results/estimator_convergence.csv` |
| Realised violation rate, Gaussian data | 5.03 % (historical) / 5.02 % (Gaussian) against 5 % nominal; 1.014 % / 1.009 % against 1 % | `results/estimator_convergence.csv` |
| Realised violation rate, t(3) data at 99 % | historical 1.02 % (on target); **Gaussian 1.39 %** — a normal fit understates the 99 % tail | same |
| Realised violation rate, t(3) data at 95 % | historical 5.01 %; **Gaussian 3.29 %** — the same normal fit *overstates* risk here | same |
| Size of Kupiec under a correct model | reject rate 5.05 % at the 5 % level, 0.75 % at the 1 % level (2 000 replications of 250 days) | `results/coverage_test_size_power.csv` |
| Power against an under-set VaR (12 % true violation rate) | 98.8 % rejection at 250 days, 100 % from 500 days up | same |
| Discrimination: clustered violations with the right unconditional rate | Kupiec rejects 12 % (its binomial count assumption is what breaks, not the frequency), independence test rejects **55.4 %**, conditional 53.5 % | same |
| Correctly rejecting what it should not | with iid violations at a wrong rate, the independence test rejects only 5–6.8 % — no spurious clustering signal | same |
| Bootstrap coverage of the true unconditional VaR (nominal 90 %) | iid design on iid data 87.25 % [83.6, 90.4]; block design on iid data 87.00 % (no harm); iid design on GARCH data 62.50 % [57.6, 67.3]; moving-block on GARCH 69.25 % [64.5, 73.7] | `results/bootstrap_coverage.csv` |
| C++/Python agreement | `tests/python/test_cpp_python_consistency.py` through the reference tool | — |

The t(3) pair of rows is the most useful thing in this card: a Gaussian VaR is not
"conservatively wrong", it is wrong in **opposite directions at the two confidence
levels**, because the normal quantile spacing and the t quantile spacing differ. Any
explanation that promises a one-sided safety margin from a normal fit is false.

## Known limitations

1. Everything here is validated on synthetic data whose truth is known. Real asset
   returns are not stationary, and nothing in this card licenses a claim about them.
2. Empirical VaR at 99 % with 250 observations averages 2 or 3 order statistics; the
   estimate is dominated by which days happened to be in the sample. Use the interval,
   not the point.
3. The Gaussian estimators are wrong by construction for fat tails, as measured above.
   They are kept because they are the reference case, not because they are defensible.
4. Percentile bootstrap intervals are not bias-corrected or accelerated; coverage
   87 % against a 90 % nominal level on iid data is the observed cost of the simple
   percentile method at n = 500.
5. Under GARCH-type clustering, **neither** design reaches nominal coverage at n = 500
   (62.5 % iid, 69.25 % moving-block, both with intervals far below 90 %). The
   block design helps materially and is the right default, but the `n^(1/3)` block rule
   is a general-purpose rule and is not tuned for tail quantiles. Longer blocks, a
   stationary bootstrap, or a conditional (GARCH) model would be needed for a
   defensible interval on clustered data — none is implemented.
6. The bootstrap target is the *unconditional* quantile of the process, estimated from
   a 2 million-draw simulation. A daily re-estimated (conditional) VaR has a different
   estimand and its coverage would need a different experiment.
7. Coverage tests are marginal-frequency tests on a *given* VaR series. They do not
   validate the model that produced it, cannot be repaired by re-tuning the level after
   seeing the violations, and have no power against a model that is wrong in a way that
   leaves the violation rate and its timing intact.
8. `historical_es` averages `ceil(n (1 - alpha))` observations, so at small `n` it is
   discrete and slightly upward-biased; it is not the full "expected shortfall"
   coherent-risk-measure functional estimated at its own optimum.
9. No Cornish-Fisher expansion, no extreme-value tail fit, no filtered historical
   simulation, no expected-shortfall backtest (the Bellini/Frittelli or Acerbi-Tasche
   style tests), and no multiple-comparison correction across the three coverage tests.
