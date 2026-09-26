# Model card — Heston stochastic-volatility simulation

| | |
|---|---|
| Component | `quantrisk::HestonParams`, `simulate_heston`, `price_heston_european`, `heston_step_refinement_gap` |
| Source | `cpp/src/stochastic/heston.cpp` |
| Specification | `docs/mathematical_specification.md` §10 |
| Phase | 4 |
| Validation level reached | L1 degenerate limits, L2 semi-analytic oracle, L3 step refinement |

## What is implemented

```text
dS = (r - q) S dt + sqrt(v) S dW1
dv = kappa (theta - v) dt + xi sqrt(v) dW2,      corr(dW1, dW2) = rho
```

discretised by **full-truncation Euler**: the diffusion coefficient of both
equations uses `max(v, 0)`, and the variance update is clamped to zero after the
step. Correlated normals are built as `Z1` and `rho Z1 + sqrt(1 - rho^2) Z2'`,
so one stream per path carries the correlation exactly.

**This is not an exact simulation.** The transition density of the Heston
process is not that of a lognormal over a step, so every price produced here
carries an `O(dt)` discretisation bias in addition to Monte Carlo error. Both are
reported, neither is hidden: `note` on every result, the clamp count in
`negative_variances_clamped`, and the bias probe
`heston_step_refinement_gap`.

## Parameter handling

* Structural validation: `S > 0`, `v_0 >= 0`, `kappa >= 0`, `theta >= 0`,
  `xi >= 0`, `rho in [-1, 1]`, `T >= 0`. Violations raise `ValidationError`.
* The **Feller condition** `2 kappa theta >= xi^2` is *reported*, never enforced:
  `HestonPriceResult::feller_condition_satisfied`. A violating parameter set is an
  admissible, interesting choice (the tests deliberately use one, where variance
  touches zero thousands of times per simulation) and full truncation exists
  precisely because that regime is reachable.

## Validation evidence

| Check | Result |
|---|---|
| `xi = 0`, `v0 = theta = sigma^2` collapses to Black-Scholes vs QuantLib `AnalyticEuropeanEngine` | worst relative error 2.1e-3 at 200k paths / 250 steps, inside sampling error |
| Full parameter set vs QuantLib `AnalyticHestonEngine` (semi-analytic) | worst relative error 4.5e-3, within a few standard errors |
| Risk-neutral martingale: `E[S_T] = S e^{(r-q)T}` | inside 4 standard errors |
| Path positivity: every `S_T > 0`, every variance `>= 0` | asserted over 20 000 paths including a Feller-violating set |
| Reproducibility: same seed => bit-identical terminals and price | asserted in C++ and Python |
| Skew sign: `rho = -0.9` prices an OTM put above `rho = +0.9` | asserted |
| Step refinement: bias below the noise floor at 150k paths for steps 20/80/320 | differences inside 4 combined standard errors |

## Known limitations

1. **Validation is weaker than the Black-Scholes section.** The oracle here is
   QuantLib's semi-analytic Heston engine, which is itself a numerical
   quadrature; agreement at 4.5e-3 mixes our discretisation bias with the
   oracle's integration tolerance. It is a cross-check of a biased scheme, not a
   closed-form verification.
2. **Full truncation is biased** and known to be so; alternatives
   (moment-matched log-normal, QE/Ciricella bilinear, exact CIR transition
   sampling, Alfonsi steps) are not implemented. Under `xi = 0` the bias vanishes
   by construction, which is the only place this card claims exactness.
3. **No implied-volatility inversion or smile fitting.** Prices are produced from
   parameters; calibrating `kappa, theta, xi, rho, v0` to a market surface is
   outside this phase.
4. **No Heston Greeks** (no pathwise/likelihood-ratio estimators yet) and no
   path-dependent payoff under Heston: `price_heston_european` is European-only.
5. Terminal variance is reported at the last step, and realised variance is a
   trapezoidal integral over the same grid, so both inherit the step
   discretisation.
