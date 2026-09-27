# Findings

Three results worth ninety seconds. Each is a number, the confound that makes it mean
something, and the artifact that regenerates it. Everything here is measured; nothing is
asserted from a model's reputation.

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

## What is *not* a finding

Stated because overclaiming is the failure mode this project exists to avoid:

- No real market data was used anywhere. Every result above is about estimators on synthetic
  processes whose truth is known, and none of them licenses a statement about markets.
- No performance improvement is claimed over any library. The measured result is that the C++
  core is roughly 8× an interpreted loop and **slower** than vectorised NumPy (0.42×–0.48×)
  on the benchmarked workload.
- No Sharpe ratio, return forecast or trading recommendation appears in this repository.
- Two components are `partially validated` in the matrix, and the bootstrap interval's
  0.693 coverage against a 0.900 nominal level is published as a failure of the method.
