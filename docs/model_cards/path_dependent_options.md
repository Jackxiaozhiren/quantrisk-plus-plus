# Model card — path-dependent pricing: Asian and barrier options

| | |
|---|---|
| Components | `quantrisk::AsianOption`, `quantrisk::BarrierOption`, `geometric_asian_price`, `path_dependent::{price_asian, price_geometric_asian, price_barrier}` |
| Source | `cpp/src/pricing/path_dependent.cpp`, `cpp/src/monte_carlo/path_dependent.cpp` |
| Phase | 4 |
| Validation level reached | L1 identities + limits, L2 analytic oracles (QuantLib), L3 step-refinement |

## What is implemented

* **Arithmetic Asian** (equally spaced fixings on `(0, T]`) by Monte Carlo, with
  the **discretely monitored geometric average of the same paths** as a control
  variate.
* **Geometric Asian** by Monte Carlo *and* by a closed form: with `h = T / M`,
  `ln G ~ N(mu, s^2)` where

  ```text
  mu = ln S + (r - q - sigma^2/2) * h * (M + 1) / 2
  s^2 = sigma^2 * h * (M + 1)(2M + 1) / (6M)   ->  sigma^2 T / 3 as M -> infinity
  ```

  whose variance limit is the textbook continuous-averaging value, which is the
  internal consistency check on the derivation.
* **Up-and-out / down-and-out barriers** with **discrete monitoring** on the
  simulation grid, plus the Broadie-Glasserman-Kou continuity correction
  `B_eff = B exp(-+ beta sigma sqrt(dt))`, `beta = -zeta(1/2)/sqrt(2 pi)`.

## Discrete versus continuous monitoring (the distinction that matters)

A barrier checked at `M` dates can only be crossed at those dates, so the
knockout probability is *lower* and the option is *worth more* than the same
contract monitored continuously. The difference is not small: measured here at
**14.0 %** relative error of the raw discrete estimate (250 monitoring dates,
30 vol) against QuantLib's `AnalyticBarrierEngine`, and the corrected estimator
reduces that to **1.0 %** — a 14-fold improvement, and the correction goes the
other way from an intuitive "relax the barrier" reading: the effective barrier
must be moved **toward the spot**.

That direction was initially implemented backwards in this repository, and a test
asserted the wrong inequality (`corrected > discrete`) which passed because the
implementation shared the misconception. The oracle comparison
`benchmarks/quantlib/path_dependent_validation.py` is what caught it; the tests
now assert the tightened barrier, the cheaper price, and the reduced error
against the analytic continuous value.

## Validation evidence

| Check | Result |
|---|---|
| Geometric Asian closed form vs QuantLib `AnalyticDiscreteGeometricAveragePriceAsianEngine` | worst relative error 5.5e-4 (residual is calendar-day rounding of fixing dates) |
| Geometric Asian simulated vs the same oracle | worst relative error 2.3e-3, inside a few standard errors |
| Barrier: discrete vs continuous analytic | 14.0 % ; with BGK correction 1.0 % |
| `M = 1` geometric Asian == Black-Scholes | 1e-12 relative (`tests/cpp`, `tests/python`) |
| AM >= GM pathwise (arithmetic Asian >= geometric Asian) | asserted as a payoff identity and as a price ordering |
| Unreachable barrier == vanilla; breached barrier == discounted rebate | exact |
| Control variate cuts arithmetic Asian SE | > 2x at equal path budget, estimate unchanged |

## Known limitations

1. **Fixing dates are exactly equally spaced in year fractions** and the core does
   not do calendar or business-day arithmetic. A market Asian on a 12-month
   quarterly schedule, or one with a fixing on a holiday, needs a date
   convention layer that does not exist yet. The 5.5e-4 oracle residual is
   precisely this effect, not a pricing error.
2. **The barrier is monitored at the same grid used for the simulation**, so
   `steps` is simultaneously the discretisation of the diffusion and of the
   monitoring schedule. Real contracts monitor monthly while one simulates with
   thousands of steps; separating those knobs is future work.
3. **BGK is an asymptotic correction** (`O(sqrt(dt))` leading term) for a *single*
   barrier on a lognormal diffusion. It is not a claim of exactness, and the
   residual 1.0 % measured here is that approximation error.
4. No basket, chain, double-barrier, with-rebate-discretisation, or
   partially-continuous variants; no arithmetic Asian closed form (none exists —
   which is exactly why it is a Monte Carlo section).
5. The control-variate `beta` is fitted on the same sample, so the reported
   standard error is mildly optimistic (same caveat as Phase 3).
