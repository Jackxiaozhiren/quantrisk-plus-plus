# Model card — Monte Carlo engine (GBM, European payoffs, variance reduction)

| | |
|---|---|
| Component | `quantrisk::MonteCarloEngine`, `quantrisk::gbm::*` |
| Source | `cpp/src/monte_carlo/engine.cpp`, `cpp/src/stochastic/gbm.cpp` |
| Specification | `docs/mathematical_specification.md` §5 |
| Phase | 3 |
| Validation level reached | L1 identities, L2 live oracle, L3 convergence + coverage |

## What it computes

```text
V0 = e^{-rT} E^Q[payoff]      estimated by   V_N = e^{-rT} (1/N) sum_i payoff_i
SE(V_N) = s / sqrt(N)         with           95 % CI = V_N +- z * SE
```

`N` independent risk-neutral draws of `S_T` from the **exact** GBM transition
`S_T = S exp[(r - q - sigma^2/2)T + sigma sqrt(T) Z]`, so a European estimate
carries no discretisation bias by construction; the only error is sampling
error, which is what makes this section's statistics interpretable.

## Estimator conventions (these are the parts usually got wrong)

* Antithetic sampling's independent unit is the **pair mean**, so `iid_units`
  is `paths / 2` and the standard error is computed over pairs. Dividing the
  pair variance by `paths` instead would understate the error by `sqrt(2)`.
* The control variate is the terminal price itself, whose risk-neutral mean
  `S e^{(r-q)T}` is known in closed form; `beta` is fitted on the same sample
  (adaptive), so the reported in-sample variance is slightly optimistic. The
  unbiasedness and the realised gain are therefore measured out of sample, over
  seed ensembles, in `experiments/variance_reduction/`.
* The physical measure is a different function (`terminal_prices_physical`) with
  an explicit `mu` that denotes price appreciation excluding the dividend yield,
  so pricing and risk cannot silently share a drift.
* Path-dependent pricing (`price_path_payoff`) takes a `steps` argument that is
  a bias knob; the returned `note` says so, and Phase 4 studies it.

## Validation evidence

* Level 1 - exactness identities, deterministic and not tolerant:
  a deep-in-the-money call (strike 1.0) has payoff `S_T - K`, which is affine in
  the control variate, so the control-variate estimator must return the analytic
  price to ~1e-12 relative with a standard error below 1e-10 and `beta` of 1.
  A constant payoff returns the discount factor exactly. Antithetic pairs satisfy
  `S+ * S- = S^2 exp(2(r-q-sigma^2/2)T)` exactly.
* Level 2 - `benchmarks/quantlib/monte_carlo_validation.py`: 492 rows, our
  estimate against QuantLib's analytic engine over 4 scenarios x 3 methods x 40
  seeds, reported as z-scores (pooled mean ~0, std ~0.92-1.01, ~96 % inside ±2).
  An independent NumPy/PCG64 simulation is a third yardstick. QuantLib's own MC
  engine could **not** be constructed in this build (`MCEuropeanEngine` rejects
  every traits string); the artifact records `quantlib_mc_engine_used: false`
  with the reason instead of implying the comparison happened.
* Level 3 - `experiments/monte_carlo_convergence/`: log-log slope of |error| on
  N over 1e3..3e6 paths, fitted slope -0.61 ± 0.09 / -0.59 ± 0.10 / -0.51 ± 0.12
  against the theoretical -0.5 (all within 1.3 standard errors), and empirical
  coverage of the nominal 95 % and 99 % intervals over 200 seeds x 3 scenarios x
  2 path counts: **12/12** inside the exact `Binomial(n, level)` band.
* `experiments/variance_reduction/`: measured mean-squared-error reduction vs
  plain Monte Carlo, antithetic 1.1-1.9x, control variate 1.9-2.3x depending on
  scenario and path budget.
* `benchmarks/performance/monte_carlo_speed.py`: terminal-only European pricing
  at ~45.6M paths/s in C++ vs ~5.0M paths/s in a pure-Python loop (≈8.1x on this
  machine) and ~86M paths/s for vectorised NumPy - i.e. the honest finding that
  for one-normal-per-path work NumPy's vectorised generator is faster, and the
  C++ core's advantage lies in per-path state and memory layout.

## Known limitations

* Single-threaded; no quasi-Monte Carlo, no Brownian bridge, no stratification.
* `price_path_payoff` materialises the whole path matrix: `O(paths x steps)`
  memory, which bounds path counts at ~1e6 x 250 on a laptop.
* Confidence intervals are CLT/normal based. That is defensible for a mean of
  i.i.d. payoffs with finite variance, and its empirical coverage is what the
  Level-3 study measures - but it is not an exact interval, and for heavy-tailed
  payoffs (far out-of-the-money digital-style structures) it would not be.
* Adaptive `beta` makes the reported in-sample variance optimistic; the
  experiments compensate by also reporting out-of-sample MSE.
