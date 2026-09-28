# Findings

Six results worth ninety seconds. Each is a number, the confound that makes it mean
something, and the artifact that regenerates it. Everything here is measured; nothing is
asserted from a model's reputation.

**On uncertainty, because the first three numbers are deterministic, the fourth is an interval, and the fifth and sixth are exact analysis against floating-point data.**
Findings 1 and 2 are functions of a fully specified, seeded data-generating process: given the
same build, every figure reproduces to the last digit, and the ranges quoted
(1.13×–1.26×, 1.57×–1.60×) are the spread *across window lengths and estimators*, which is the
substantive variation being reported, not sampling noise. Finding 3's residuals are identities,
so their only uncertainty is floating-point. Where sampling error *is* the question —
convergence slopes, coverage rates, backtest size — the standard errors are in
`docs/validation_matrix.md`, and they are the reason two of those claims are stated as
"−0.99405 ± 0.00313 against a theory value of −1" rather than as a match.

Finding 4 is the exception in kind, not just in magnitude: it is the only one measured on a
sample nobody generated, so it carries no ± because the interval *is* the result — an exact
binomial interval around a realised violation rate, quoted with its endpoints. That is also why
it can contradict a synthetic finding without either one being a bug.

For a reader who wants the reasoning rather than the result: the technical report
(`paper/technical_report.pdf`) covers each in its own chapter, and
`docs/validation_matrix.md` lists every bound against every measurement.

---

## 1. Stress does not invert the optimiser ranking — but it inverts the safety ranking

Under a normal-times dispersion measure, the six books rank as expected: minimum-variance is
least risky, max-Sharpe and CVaR sit elsewhere, equal weight is the naive baseline. Under
seven stress scenarios, that ordering **does not reverse**.

That is not because stress is harmless. It is because the books started **20.8%** apart in
normal-times risk while the stress-induced spread is **16.8%** — the gap was simply larger
than the effect, so a reversal was never available. The naive reading ("stress doesn't change
anything") is refuted by the second measurement:

**The stress-*sensitivity* ranking inverts completely.** The minimum-variance book is the
*most* stress-sensitive of the set — a **6.11×** amplification of its normal-times risk,
against **5.23×** for equal weight. The book chosen to be safest under the dispersion it was
estimated on is the one whose assumption breaks hardest when the dispersion changes.

That is the Phase 6 conclusion — that estimating the covariance dominates choosing the
optimiser — seen from the opposite end: the ranking you get depends on which variance you
asked about, and asking the other one reverses it.

- **Confound identified:** gap size versus effect size. A reversal test is only informative
  when the baseline spread is smaller than the perturbation, and the experiment says so
  rather than reporting "no reversal" as a finding about stress.
- **Artifact:** `experiments/stress_testing/results/stress_testing_study.json`
  (`ranking`, `decomposition`), `scenario_ranking.csv`,
  `docs/model_cards/scenario_stress_testing.md`.

## 2. Estimating the covariance costs more than choosing the optimiser

On a two-regime factor data-generating process where the forward covariance is known in
closed form, every portfolio is scored against what an *informed* solver would have carried.
Rolling origin, 1,119 portfolios, 373 solved windows, three estimators, four window lengths.

- Estimation cost: **1.13× to 1.26×** the informed solver's forward variance.
- A regime break, for **every** estimator: **1.57× to 1.60×**.
- Shrinkage wins exactly where instability bites: at a 40-observation window it lowers the
  ratio from **1.2176 to 1.1686**, cuts turnover from **0.2067 to 0.1381**, and raises the
  effective asset count from **5.10 to 5.97**.
- More history is not monotonically better: window 250 is **0.087 worse** than window 125 for
  the raw sample estimator, because it averages across the break.

The ordering of the two effects is the finding: **non-stationarity dominates estimation error,
and estimation error dominates optimiser choice.** No amount of solver sophistication recovers
the regime term, which is why the optimiser comparison in Phase 6 is reported alongside the
input it was handed rather than on its own.

- **Confound controlled:** the truth is analytic, so "cost" is not measured against another
  estimate. Rolling origin prevents the estimator from seeing the window it is scored on.
- **Artifact:** `experiments/portfolio_optimization/results/portfolio_optimisation_study.json`
  (`estimation_cost`, `headline`, `findings`), `estimator_out_of_sample.csv`.

## 3. The two bugs that produced plausible numbers and raised no error

Neither was found by reading the code. Both were found by an identity that failed to close.

**A position can be allocated exactly zero risk.** `beta_of` sized the beta vector from
`exposures.delta.size()`. A book holding only a vega block therefore produced an empty beta,
was allocated zero risk, and still returned a well-formed result. The Euler component sum
disagreed with the portfolio VaR by **−21,451 against a 355k VaR**. Nothing threw. The
attribution-closure identity caught it; the fix takes the factor count explicitly, and
`test_bound_exposure_blocks_are_value_semantic` plus the closure tests pin it down.

**A volatility shock silently changed the correlations.** The stressed covariance rescaled
only the diagonal, so doubling every volatility halved every correlation — an entirely
different market. `Σ → m²Σ` on every entry is the fix. The check that found it is a
correlation-preservation assertion, not a P&L comparison: the P&L numbers were plausible
either way, which is what makes the bug serious rather than merely wrong.

Together these define the project's position on testing. A number that looks reasonable is
not evidence; an identity that must close, and a negative control that must fail, are.

- **Artifact:** `cpp/src/stress/engine.cpp`, `tests/cpp/test_stress_engine.cpp`,
  `docs/phase_reports/phase-07-stress-testing.md` §6, and the same class of catch recorded in
  `docs/phase_reports/phase-06-portfolio-optimisation.md` (the `clean_weights()` rounding
  trap) and `docs/phase_reports/phase-10-release.md` §6 (nine self-corrections during the
  release audit).

---

## 4. Real data confirms the fat-tail prediction and overturns the covariance one

Everything above is measured on processes whose truth is known. That is what makes a bias
measurable — and it is also what keeps every one of those conclusions one step away from an
empirical claim. `experiments/real_data_risk_study/` closes part of that gap: three FRED series
used as risk factors (10-year Treasury par yield, 10-year breakeven, VIX), a fixed set of notional
exposures, trailing 250-day calibration, and **586 out-of-sample days** scored one step at a time.

**The Gaussian tail failure reproduces.** Phase 5's synthetic t(3) arm predicted that a Gaussian
99% VaR would over-reject; on real data it realised **2.048%** violations against 1% nominal, with
an exact binomial interval of **[1.062%, 3.550%]** — which excludes the nominal rate. Historical
simulation at the same level realised **1.365%** with interval **[0.591%, 2.672%]**, which covers
it. The prediction was right, and it is right for the reason it was made for.

**The covariance ranking does not survive — its two ends trade places.** Phase 6 scored the same
three estimators on synthetic data by mean forward-variance ratio against an informed solver and
got **shrinkage 1.169 < sample 1.183 < ewma 1.241**. Scored here on realised out-of-sample
portfolio variance over 582 rolling windows, the ordering is **ewma < sample < shrinkage**: the
estimator that was worst in the generated world is best on market data, and the one that was best
is worst. Neither result is a bug. Shrinkage wins where a short window makes the sample covariance
*unstable*, which is the regime the synthetic DGP was built to create; on a twelve-year record of
three highly persistent rate and index series, that structured target is instead the thing that
lags. The finding is not "shrinkage is bad" — it is that an estimator ranking is a property of the
process it was measured on, and a benchmark that does not name its process says nothing.

**The backtest machinery, however, does not discriminate here.** Three violations-per-day tests on
the same 586 days — Kupiec **p = 0.160**, Christoffersen independence **0.287**, conditional
coverage **0.211** — and *none rejects*. The Phase 5 synthetic arm showed the independence test
rejecting 55.4% of clustered series, so the machinery works; on this particular sample the
clustering is mild enough to miss (a runs test gives z = **−1.17**, the right sign, no power). The
truth-free bootstrap check agrees: the moving-block standard error is only **1.072×** the iid one.

A negative result of that kind is the easiest thing in a portfolio to bury, and it is published
rather than dropped: the same experiment that produced the confirmation produced the non-detection.

**Three questions it refuses.** The artifact records them explicitly instead of proxying them:
how much estimating covariance costs against an informed solver (real data has no observable true
covariance, and substituting the full-sample estimate would smuggle the future into the
comparison); whether the block bootstrap reaches nominal coverage on real data (coverage needs a
truth independent of the series being resampled — an earlier version measured exactly 1.000 this way
and the number was circular, so it was discarded); and whether the book is profitable (there is no
return in it).

- **Confound identified:** the exposures are assumed, not traded, so the violation *rate* is
  invariant to scaling the whole book at once — the script asserts that invariance rather than
  claiming it — but not to the mix of factors, and no sensitivity to the mix is published.
- **Artifact:** `experiments/real_data_risk_study/results/real_data_risk_study.json`
  (`headline`, `A_estimator_validity`, `B_coverage_tests`, `D_covariance`, `refusals`),
  `real_data_violation_coverage.png`, `real_data_violations.csv`.

## 5. The stress map's error has a sign change, and the theory says where

The stress layer maps a shock to P&L with delta and gamma and then re-prices the same book with
full Black-Scholes. `experiments/stress_testing/` published that error and the summary said it grows
with the shock size. It does not, and its own table is the refutation: at a 10 % down move the error
is 649.5, at 20 % it is 528.5, and then it is 12,527 at 30 %. A monotone story was told about a
non-monotone curve.

A Taylor remainder explains it, and `experiments/linearisation_error_bound/` checks the explanation
rather than illustrating it. For a map that keeps terms through order two the remainder is
`R = (1/6)·V‴(ξ)·h³` for some `ξ` on the shocked path, which is not merely an inequality: the
coefficient `c(δ) = 6R/h³` must lie **between the minimum and maximum of V‴ along the path**. That
holds at all 618 shocks tested in both directions, and the envelope is tight — the ratio runs
0.9962 at the smallest shock to 0.2842 at the largest — so it is a bound and not a vacuous one.

The closed form is `V‴ = −(Γ/S)(1 + d₁/(σ√T))`, and for this three-strike ladder it **crosses zero
at spot 94.55**, a 5.45 % down move. Once the segment straddles that point the cubic contributions
cancel, `c(δ)` falls through zero, and so does `R` — at a **21.1446 %** down move. The published
curve, frozen in the evidence manifest a phase before this derivation existed, brackets that with
its single sign change between 20 % and 30 %. Two artifacts produced by different code agreeing on a
location is the check; one agreeing with itself is not.

The asymptotics are reported as a convergence rather than a number, because at any fixed window the
quartic term biases the slope: fitted per direction over shrinking windows the estimate runs
**2.9710 → 2.9988** down and **3.0253 → 3.0012** up against theory 3. And the same departure
confirms the fourth derivative by a second route — `S·V⁗/(4V‴) = 3.752361` predicted, measured
3.759289 down and 3.745379 up at a 0.1 % shock, bracketing it from both sides.

Three limits are stated rather than smoothed. The arithmetic floor is a property of the book's
magnitude, near `δ = 3·10⁻⁵` here, and an earlier draft of this note took it from a similar-looking
single-option test at the wrong unit and the wrong scale. A single pooled fit over up and down moves
returns `3.037 ± 0.003` — eleven sigma from theory, and the sigma are meaningless, because the
deviation *is* the up/down separation. And the bound is about the map, not the scenario: how much of
a stress number is truncation is computable, how much is management choice is not.

- **Confound identified:** an absolute-value bound cannot see a cancellation; the Lagrange form can,
  and only that form predicts the sign change.
- **Artifact:** `experiments/linearisation_error_bound/results/linearisation_error_bound.json`
  (`headline`, `rows`, `proposition`, `asymptotics`), `linearisation_bound.csv`,
  `linearisation_bound.png`; derivation in `docs/analysis/delta_gamma_error_bound.md`.

## 6. Two factors make the stress map wrong in a different way, and it is not the way the theory names

Phase 12 bounded the map's error when one factor moves. The published stress set does not contain
one-factor scenarios: `risk_off` moves equity −15 % **and** volatility +6 points. The map treats
volatility to first order — `out.volatility = vega * absolute` at `cpp/src/stress/engine.cpp:116`,
with no convexity and no cross term — so a joint shock costs it `vanna·h·k + ½·volga·k²`, and the
error stops being cubic in the shock size and becomes **quadratic**.

`experiments/two_factor_error_bound/` checks that rather than asserting it, against
`stress.run_scenario`'s own output on the published book with the published scenario imported from
`experiments/stress_testing/run.py`. Fitted over four successively narrower windows, the log-log
slope of the error against shock size runs **1.9098 → 1.9762 → 1.9929 → 1.9975** on a crash ray and
settles at 2 on all four joint directions, while a pure-spot ray on the same book holds at
**3.0009** — which is Phase 12's answer, reconciled rather than replaced. The sharp Lagrange form,
that `6·(error − quadratic)` must lie inside the segment's own range of the third directional
derivative, holds on **132 of 132** swept joint shocks, out to a 30 % equity move with +20
volatility points.

Then the result that changes a decision. At the published `risk_off` sizes the closed-form quadratic
is **+787.96** and the error is **−5320.79**: the leading term of the limit is not merely
under-sized, it points the opposite way. The largest omitted piece is `½·V_{SSσ}·h²·k` =
**−8402.16**, which is gamma evaluated at the base volatility and applied across a move that has
already changed it — 7.4× the entire quadratic. So the cheap improvement to this map is not vanna
and volga; it is re-striking gamma at the shocked volatility. Counted across the whole grid the
ranking splits three ways — mixed-cubic 64 cells, spot-cubic 36, volga 32, and the mixed `vanna·h·k`
term that the order argument singles out is the largest **nowhere**.

What survives from the inequality is a sign, not a magnitude estimate: on `risk_off` the error lies
in **[−6063.95, −4135.87]**, which excludes zero, so the map is *provably* reporting the loss too
high there, by between 4136 and 6064 on a book of 108,911. The interval's width is 36 % of the
error it bounds, which is what keeps it a bound rather than a tautology.

Two limits are stated rather than buried. The near-cancellation of the quadratic is a property of
*this* book — its K=90 and K=110 legs contribute −5089.09 and +5628.57 of vanna, leaving 192.33 —
so a concentrated book would rank the terms differently, and `dominance_counts` in the artifact is
the only honest guide. And the direction where the quadratic vanishes is a closed-form prediction
whose empirical counterpart cannot be located without a bracket that shrinks with the shock: the
probe ships in the artifact precisely so that this refusal is checkable rather than trusted.

- **Confound identified:** "second order" describes a limit, and a limit statement quoted at
  published shock sizes can carry the wrong sign while being asymptotically correct.
- **Artifact:** `experiments/two_factor_error_bound/results/two_factor_bound.json` (`headline`,
  `slopes`, `dominance_counts`, `published_scenario_bound`, `ridge_probe`), `two_factor_bound.csv`,
  `published_scenario_bound.csv`, `two_factor_bound.png`; derivation in
  `docs/analysis/two_factor_error_bound.md`.

---

## What is *not* a finding

Stated because overclaiming is the failure mode this project exists to avoid:

- The real-data arm is one arm. Six of the seven experiments still run on synthetic processes whose
  truth is known, `docs/limitations.md` #28 says so, and finding 4's exposures are an assumption —
  no number there describes a position anyone held, and a single 12.7-year sample of three factor
  series does not license a statement about markets in general.
- No performance improvement is claimed over any library. The measured result is that the C++
  core is roughly 8× an interpreted loop and **slower** than vectorised NumPy (0.42×–0.48×)
  on the benchmarked workload.
- No Sharpe ratio, return forecast or trading recommendation appears in this repository.
- Two components are `partially validated` in the matrix, and the bootstrap interval's
  0.693 coverage against a 0.900 nominal level is published as a failure of the method.
