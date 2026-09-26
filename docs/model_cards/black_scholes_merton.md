# Model card — Black-Scholes-Merton European pricing

| | |
|---|---|
| Component | `quantrisk::black_scholes`, `quantrisk::black_scholes_greeks` |
| Source | `cpp/src/pricing/black_scholes.cpp` |
| Specification | `docs/mathematical_specification.md` §2, §3 |
| Phase | 2 |
| Validation level reached | L1 identities + L2 live oracle (QuantLib, SciPy) |

## What it computes

Closed-form value of a European call or put on an underlying following GBM with
continuous dividend yield, plus the five analytic Greeks.

```text
d1 = [ln(S/K) + (r - q + sigma^2/2) T] / (sigma sqrt(T))
d2 = d1 - sigma sqrt(T)
C  = S e^{-qT} N(d1) - K e^{-rT} N(d2)
P  = K e^{-rT} N(-d2) - S e^{-qT} N(-d1)
```

Units are frozen in the specification: Theta per calendar year (negative for a
long option), Vega per unit of volatility (1.00 = 100 vol points), Rho per unit
of rate. `N(.)` is implemented as `0.5 * erfc(-x/sqrt(2))`.

## Assumptions, stated as claims that can be wrong

1. Constant volatility and constant rates over the option's life. Real
   implied-volatility surfaces are skewed; this model cannot represent that, and
   no smile is fitted here.
2. Lognormal underlying with continuous trading and no jumps.
3. Frictionless markets: no transaction costs, no borrow cost, no bid-offer.
4. European exercise only. Applying this code to an American contract is a
   modelling error, not a numerical one; use the lattice.
5. Constant continuous dividend yield `q`. Discrete dividends are out of scope.
6. Risk-neutral measure: `r` and `q` enter as drift, and the result is a *price*,
   not an expected payoff under the physical measure.
7. Settlement/spot convention: inputs are year fractions directly; no day-count
   inference happens in the core (the benchmark maps days → `days/365`).

## Degenerate edges (implemented as limits, tested)

| Input | Value returned | Greeks |
|---|---|---|
| `T == 0` | expiry payoff `max(S-K, 0)` / `max(K-S, 0)` | Delta = step (1/2 at the kink), all others 0 |
| `sigma == 0`, `T > 0` | `e^{-rT} * payoff(F)`, `F = S e^{(r-q)T}` | Delta = `e^{-qT}` × step, Gamma/Vega = 0 except the ATM Vega limit, Rho/Theta from the piecewise-linear form |
| `d1`, `d2` in either edge | NaN, deliberately | a number from a `0/0` would be a lie |

Put-call parity `C - P = S e^{-qT} - K e^{-rT}` is asserted on every grid point.

## Validation evidence

* Level 1 — `tests/cpp/test_black_scholes.cpp` (parity over 6 markets × 7
  strikes, bounds, monotonicity, degenerate limits, `d1/d2` identity),
  `tests/python/test_pricing.py` (independent recomputation from the spec with
  SciPy, 5 markets × 8 strikes × 2 types).
* Level 2 — `benchmarks/quantlib/pricing_validation.py`, 18 816 rows over
  7 maturities × 11 strikes × 4 volatilities × 2 rates × 2 dividend yields,
  both option types, plus all five Greeks. Worst case in
  `benchmarks/quantlib/results/pricing_vs_quantlib.json`.
* Level 2 (unit conventions) — QuantLib's `vega()`/`rho()` were assumed to be
  per 1 percentage point in the first version of the benchmark; the measured
  0.99 relative error exposed the assumption, and the conventions are now
  recorded as measured (agreement ~1e-15 with no rescaling).

## Measured numbers (this run; regenerate with the command above)

See `benchmarks/quantlib/results/pricing_vs_quantlib.json`
(`worst_absolute_error`, `worst_relative_error_above_floor`) and
`experiments/pricing_validation/results/summary.json`
(`worst_put_call_parity_residual`).

## Known limitations

* Relative error is meaningless for deep out-of-the-money contracts whose value
  is `1e-9`; the benchmark reports absolute error unconditionally and relative
  error only above a notional floor, both recorded in the JSON.
* No term structure: one flat `r` and one flat `q`. Forward curves require a
  different model (out of scope for v0.1, see specification §11).
* American-style path dependency is not expressible with this function; the
  lattice in the sibling model card is the tool for that.
