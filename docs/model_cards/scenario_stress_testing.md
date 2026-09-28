# Model card — scenario and stress testing

Phase 7 · written 2026-09-27 · status: implemented, validated against independent
numerics and against full revaluation. Everything is scored on a synthetic factor fixture;
no market data is used anywhere in this card.

## What is implemented

`cpp/include/quantrisk/stress/`, mirrored by `quantrisk.stress` in Python (5 functions,
16 bound types). The layer is independent of the pricing and portfolio code: it maps
**exposures** to P&L and never re-prices an instrument.

| Object | Role |
| --- | --- |
| `RiskFactor` / `FactorSet` | a named factor, its class, and its quoted level |
| `ExposureVector` | `delta`, `gamma`, `duration`, `vega`, `credit` — each aligned to the factor set, or absent |
| `Position` / `Portfolio` | named exposures over a factor set; `aggregate()` sums them |
| `Shock` | one factor's move, given relatively, absolutely, or both (and rejected if the two disagree) |
| `DistributionShift` | `volatility_multiplier`, `correlation_increment` — the shape of the move distribution |
| `Scenario` | shocks + distribution shift + `kind` + **required `assumptions`** + horizon + seed |
| `ScenarioResult` | P&L, both attributions, both residuals, the VaR/ES/vol change and its level/dispersion split |
| `ScenarioSetResult` | the full outcome vector for historical and Monte-Carlo sets, with its own quantiles |

| Entry point | What it does |
| --- | --- |
| `run_scenario` | one scenario against one book, optionally with a factor-move covariance for risk metrics |
| `shift_covariance` | deforms a covariance: scale every sigma, lift every off-diagonal correlation |
| `sample_factor_moves` | Cholesky + the project `Rng`, reproducible by seed; refuses a matrix with no factor |
| `run_historical_scenarios` | replays every row of an observed move window |
| `run_monte_carlo_scenarios` | draws the outcome distribution *around* the stressed mean |

## The distinctions that matter

**Relative and absolute are different objects, and the factor's class decides which a
shock means.** Delta answers to a fraction of a level; duration, vega and credit answer to
an absolute unit. A −20 % equity move and a +200 bp rate move are not the same kind of
statement, and reading one as the other is invisible in the output — the P&L just comes
out wrong and plausible. Both units are resolved for every factor wherever the quoted
level makes that possible, and a shock that states both and disagrees is rejected.

**An absent sensitivity is not a zero.** A position with no `vega` block carries an empty
vector, and the engine reads that as "no vega sensitivity of any kind is recorded here",
which is a weaker and more honest claim than "vega is zero". The distinction survives
aggregation and is what makes `beta_of` take the factor count rather than sizing itself
from whichever block happens to be first — a bug that once allocated exactly zero risk to a
pure-volatility position.

**Attribution is exact, so its residual is a bug report.** The mapping is a sum over
factors and a sum over positions of the same terms. Both decompositions must reproduce the
total, and `factor_attribution_residual` / `position_attribution_residual` /
`var_component_residual` are reported so a caller can assert on them. Across all 28
scenario/book combinations in the study every residual was exactly **0.0**.

**The VaR change splits into a level leg and a dispersion leg that telescope.**
`var_change_from_level` holds the base dispersion and moves the mean;
`var_change_from_distribution` holds the shocked mean and moves the dispersion. The split
is exact because the Gaussian quantile is affine in (mean, sigma) — and that is also its
limit: it would not telescope for a historical or Cornish-Fisher estimator.

**A single scenario is not a distribution.** `run_historical_scenarios` over one day
returns VaR and ES as NaN with a note saying why, rather than relabelling the one outcome
as a risk measure.

## Validation

| Level | Check | Measured |
| --- | --- | --- |
| L1 | both attributions close on every scenario; Euler components sum to VaR; level/dispersion split telescopes; zero shocks → zero change; single-day replay ≡ deterministic scenario | all residuals exactly 0.0 |
| L2 | P&L mapping, covariance shift, historical replay and its quantile recomputed in NumPy; stressed VaR against SciPy's own normal quantile; Euler allocation against a **central-difference gradient** of the VaR formula | mapping to 1e-9 relative; VaR to 1e-9; Euler to **3e-10** against a 1e-6 bound |
| L2 | delta-gamma map against a full Black-Scholes re-pricing of a three-strike call book | 1.35e-6 relative at a 0.1 % move, 1.33e-4 at 1 %, 5.4e-3 at 20 %, 0.49 at 40 % |
| L1 + FD | the same map under a **joint** spot-and-volatility shock, against `vanna·h·k + ½·volga·k²` plus the Lagrange term `⅙·g‴(ξ)` along the shock ray | inclusion holds on 132/132 joint shocks out to −30 % equity with +20 vol points; error slope → 2.0 on four joint rays while a pure-spot ray holds at 3.0; on the published `risk_off` the interval [−6063.95, −4135.87] excludes zero |
| L3 | Monte-Carlo stress VaR against the parametric number, on the same book and covariance | within 1 % at 400k paths, and the longer run is the closer one |
| L3 | sampled dispersion recovered by an independent estimator, and by NumPy's Generator (different RNG, different normal transform) | within 2 % of the supplied covariance |
| — | reproducibility | identical across runs; all four artifacts byte-identical between independent executions |

## What this must not be used for

- **Not a revaluation engine.** The map is a delta-gamma Taylor expansion. Its error is
  measured above and it is small for small moves and large for large ones — which is the
  honest boundary, not a defect to hide. Note that the error is **not monotone**: it
  *falls* between a 10 % and a 20 % move (9.7e-3 → 5.4e-3) because the cubic term changes
  sign through the strike region and partially cancels. A bound read off one point of the
  curve would be wrong at another.
- **Not a forecast, and not a backtest.** A historical scenario answers "what would this
  book have earned over the window you gave me". It says nothing about whether that window
  is representative, and the `assumptions` field is required precisely so that claim has to
  be written down somewhere.
- **Not a source of factor moves.** The engine consumes shocks, observed windows or a
  covariance. Where those come from — calibration, supervisor guidance, judgement — is
  outside it, and is the part that determines whether the answer matters.
- **Not a two-factor map.** The volatility factor is carried to *first* order
  (`out.volatility = vega * absolute`), with no vol convexity and no spot-vol cross term, so a
  scenario that moves equity and volatility together has a **quadratic** error rather than the
  cubic one a single-factor move has. `experiments/two_factor_error_bound/` bounds it and finds
  that at published sizes the largest omitted piece is `½·V_{SSσ}·h²·k` — gamma applied at a
  volatility the move has already changed — which on `risk_off` is 7.4× the whole second-order
  term and points the other way. Quoting the quadratic correction as "the multi-factor error"
  would therefore be wrong in sign, not just in size.
- **Not linear-in-risk beyond the Gaussian case.** Stressed VaR and ES are the Phase 5
  Gaussian closed forms applied to a shocked beta; the CVaR and historical estimators from
  Phase 5/6 are not wired into the decomposition, because the telescoping split does not
  hold for them.

## Reproducing every number on this card

```bash
uv run pytest -m oracle tests/python/test_stress_vs_oracles.py
uv run python experiments/stress_testing/run.py
./build/dev/quantrisk_tests            # test_stress_engine.cpp, test_stress_simulation.cpp
```

Artifacts: `experiments/stress_testing/results/{scenario_ranking,linearisation_error,var_decomposition}.csv`,
`stress_testing_study.json`, `linearisation_error.png`. Each carries the generating
command, package versions, the Git commit of both tree and binary, and a SHA-256 manifest.
