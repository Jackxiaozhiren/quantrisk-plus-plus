# Model card — Cox-Ross-Rubinstein binomial lattice

| | |
|---|---|
| Component | `quantrisk::crr_binomial` (+ European/American convenience wrappers) |
| Source | `cpp/src/pricing/binomial_crr.cpp` |
| Specification | `docs/mathematical_specification.md` §4 |
| Phase | 2 |
| Validation level reached | L1 identities + limits, L3 convergence study, L2 oracle (QuantLib binomial, order-level only) |

## What it computes

A recombining binomial tree with per-step parameters

```text
dt = T / N
u  = exp(sigma sqrt(dt)),  d = 1/u
p  = (exp((r - q) dt) - d) / (u - d)
value(node) = exp(-r dt) [p * value(up) + (1 - p) * value(down)]
              American: max(value(node), payoff(S_node))
```

Terminal node levels are computed as `S * exp((2j - k) log u)` directly from the
exponent rather than by repeated multiplication, so no drift accumulates as the
tree widens.

## Assumptions and honest caveats

1. The lattice is an *approximation* of continuous-time GBM. Its error against
   Black-Scholes is `O(dt)` (first order) and does not vanish uniformly: near
   the payoff kink the error constant is largest.
2. `p` can leave `[0, 1]` when `(r - q) dt` is far from `0` relative to
   `sigma^2 dt` — typically a coarse lattice with high rates and low
   volatility. The code does not silently accept that: `BinomialResult::note`
   records that the rollback is not a probability measure at that resolution.
3. American exercise is only as good as the lattice: early-exercise decisions
   are made on tree nodes, so the value is biased low for coarse `N`.
4. `sigma == 0` degenerates the tree (`u = d = 1` makes `p` a `0/0`), so it is
   evaluated as the deterministic forward path instead. For an American
   contract on that path the best exercise date is searched on 1001 points — a
   documented approximation, recorded in `note`, not an exact optimisation.

## Validation evidence

* Level 1 — put-call structure, `u*d == 1`, `p` recovered from its definition,
  no-early-exercise theorem for an American call with `q = 0`
  (`tests/cpp/test_binomial.cpp`, `tests/python/test_pricing.py`).
* Level 3 — convergence study in `experiments/pricing_validation/run.py`:
  an OLS fit of `log|error|` on `log N` over N = 25…3200 for four regimes,
  reported with standard errors in
  `experiments/pricing_validation/results/summary.json` under
  `crr_convergence_slope`.
* Level 2 — QuantLib's `BinomialVanillaEngine(process, "crr", N)` is **not**
  the textbook parameterisation: it is a different `O(dt)` discretisation of
  the same dynamics, so the two lattices differ by a convention term
  (measured, ~1.3e-4 absolute at N = 50 for the at-the-money case). The test
  therefore asserts the meaningful property — the mutual gap is far smaller
  than either implementation's error against the analytic Black-Scholes limit
  (`tests/python/test_pricing_vs_quantlib.py`).

## Measured convergence (this run)

From `experiments/pricing_validation/results/summary.json`: fitted slopes of
about -0.99 against the theoretical -1, with the short-dated at-the-money put
deviating by roughly two standard errors because its own standard error is tiny
(higher-order terms of the expansion, reported rather than smoothed away).

## Known limitations

* Cost is `O(N^2)` time and `O(N)` memory per option; no batching across
  strikes or parametrisations yet (Monte Carlo in Phase 3 is the scalable path).
* Only European and American vanilla payoffs. Path-dependent payoffs need the
  full path distribution — handled by Monte Carlo, not by this lattice.
* No Richardson extrapolation is applied to the lattice values; the `O(dt)`
  error is reported as-is instead of being hidden.
