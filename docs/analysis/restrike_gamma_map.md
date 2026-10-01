# Analysis — what re-striking gamma at the shocked volatility actually buys the stress map

Owner of the derivation behind `experiments/restrike_gamma_map/`. The numbers themselves belong to
`experiments/restrike_gamma_map/results/restrike_gamma_map.json`; this document explains where they
come from and what they do not mean. Every figure printed below is a formatting of an artifact field,
and `tests/python/test_restrike_gamma_map.py` re-derives each one from it, so a sentence that drifts
from its own evidence goes red rather than looking plausible.

## 1. The recommendation under test

`v1.3.0` (`docs/analysis/two_factor_error_bound.md`) derived the error of the published
delta-gamma-vega map under a joint spot-and-volatility shock and ended with a prioritisation, not a
result. On the repository's own `risk_off` scenario the largest single omitted piece is

    1/2 * V_SSsigma * h^2 * k        (gamma read at the base volatility, applied across a move that
                                      already changed the volatility)

at 10.7× the net quadratic term, and the closing recommendation was: re-strike gamma rather than add
vanna and volga. Nobody measured that. Three releases later this experiment does.

The map is `cpp/src/stress/engine.cpp`'s `delta_i s_i + gamma_i s_i^2 + vega_i a_i`, with `gamma_i`
carrying the one-half and `a_i` an absolute vol move. Four versions of it are built here and every one
is evaluated through `quantrisk.stress.run_scenario`, so the arithmetic is the shipped engine's:

| map | delta | gamma | vega |
| --- | --- | --- | --- |
| `base` | `(S, sigma)` | `(S, sigma)` | `(S, sigma)` |
| `gamma_restrike` | `(S, sigma)` | `(S, sigma + k)` | `(S, sigma)` |
| `gamma_restrike_at_move` | `(S, sigma)` | `(S + h, sigma + k)` | `(S, sigma)` |
| `all_restrike` | `(S + h, sigma + k)` | `(S + h, sigma + k)` | `(S + h, sigma + k)` |

## 2. The mechanism is the term it claims to be

The difference between the re-struck map and the shipped one is exactly

    ( gamma_exposure(sigma + k) - gamma_exposure(sigma) ) * delta^2

— the *relative* move squared, because the exposure already folds in `S^2` — and the divided
difference across `k` is trapped by the segment's own range of `d gamma_exposure / d sigma`, computed
from the core's mixed third partial `V_SSsigma`. Stating it as an inclusion rather than a tolerance is
what makes it falsifiable: one wrong closed form in `black_scholes_mixed_third_derivatives` refutes it
outright. The 7 probes (the published cell among them) violate nothing, and the worst relative
mismatch between the predicted and the engine-observed map difference is 3.7e-15.

## 3. It removes the named term — 86.4 % of it

At `risk_off` (`delta = -0.15`, `k = +0.06`) the recipe subtracts 7,258.51 from the map's P&L. The term
`v1.3.0` named, `1/2 V_SSsigma h^2 k` re-derived here from the same mixed partial, is 8,402.16. So the
finite difference of gamma across a six-point volatility move takes out **86.4 %** of the local
derivative the derivation quoted — which is not a failure of the recommendation but the difference
between a recipe and its linearisation, and it is the number a reader needs before repeating "remove
the dominant term".

The error itself moves from -5,320.79 to +1,937.72: a factor of 0.364, and the sign flips with it. A
map whose error had been too pessimistic is now slightly too optimistic. Anyone using the sign of the
residual for anything should note that both are approximations of the same revaluation.

## 4. The order of the map does not change

Between the two narrowest scales of each of three rays the error of all four maps falls with a local
slope of 1.98-2.01. Re-striking removes a cubic; the quadratic vanna and volga pieces that cubic was
competing with are untouched, and the map stays second order. Regressions over a four-point narrow
window spread the same slopes to 1.89-2.05, and over the whole ray to 1.92-2.34 — the higher-order
content still visible at grid sizes. The pairwise ratio is the number quoted above because it needs no
window; the two window fits are published in `asymptotics` so the spread is visible rather than hidden.

## 5. The naive fix is measurably worse

`all_restrike` — re-pricing every sensitivity at the shocked market, which is what "use the new
greeks" suggests naively — is worse than the gamma-only variant on 116 of the 120 cells swept, and on
`risk_off` its error is 60,275.64 against the shipped map's 5,320.79: a factor of 11. Moving delta and
vega costs more than the cubic it fixes, because the map's linear and vega legs then describe a
tangent at the wrong point of the move. The specificity of `v1.3.0`'s phrasing — gamma, *not* the
others — turns out to have been the load-bearing part.

## 6. The improvement is not uniform, and the cells that lose are the interesting ones

On 45 of 120 cells the re-strike does not reduce the absolute error. On 20 of those it at least
doubles it, worst factor 142. Every one of those 20 is a cell whose shipped-map error was smaller than
the term being removed.

That is the whole mechanism, and it cuts against the recommendation. Write the shipped map's error
along a `delta` column as a function of `k`:

    1/6 V_SSS h^3
    + k   ( V_Ssigma h + 1/2 V_SSsigma h^2 )
    + k^2 ( 1/2 V_sigsigma + 1/2 V_Sssigma h )
    + 1/6 V_sigmasigmasigma k^3

The first piece ignores `k` entirely; the next two are proportional to it. They cancel at some `k`, and
where they do the shipped map is *exact by arithmetic*, not by merit. The re-strike deletes one of the
cancelling pieces, so the cell that looked best gets worse by roughly the amount that was hidden.

The experiment turns that into a prediction rather than a story: it locates the zeros of the
truncation — from core closed forms alone, with nothing fitted to the measured errors — and compares
them with the zeros of the priced error, both found by the same bracket-and-bisect routine. Within
`|delta| <= 0.05` the nearest predicted zero and the nearest priced zero agree to 0.0002-0.0024 in vol
move, against a tolerance of 0.005, and that agreement is gated: the run refuses to publish if it
breaks. Beyond the limit the prediction drifts monotonically with the move size, to 0.093 at
`delta = -0.30`, and at `delta = +0.30` the truncation predicts a zero the priced map never has. The
drift is what a third-order expansion deserves: it is an argument near the base market, which is
exactly where the published scenarios live, and it stops being one out there. Across the twelve columns
the truncation finds 14 zeros and the priced error 13.

## 7. Where this stops being useful

- One three-strike call ladder, one maturity, one 20 % base vol, shocks of at most 30 % in spot and
  20 points in vol. The ranking of the four maps is a property of that grid; a book whose gamma moves
  the other way in volatility would rank them differently, and nothing here estimates by how much.
- `share_improved` counts cells. `value_weighted_reduction` weights each cell by the same error it is
  made of and comes out at 0.3704, so the two disagree about how good the news is, and both are printed.
- The zeros and the slopes are residues of subtracting book values near 1.09e5, so they reproduce to
  their conditioning; the artifact declares which fields that covers. The priced differences, the
  counts and the verdicts are exact arithmetic on the shipped engine.
- Nothing here says the shipped map should change. `run_scenario` publishes a two-factor
  delta-gamma-vega map, and `docs/limitations.md` keeps the consequence: a user who needs the residual
  controlled at joint published sizes is not served by editing the exposures at the call site.

## 8. Reproducing

```bash
uv run python experiments/restrike_gamma_map/run.py
uv run python scripts/run_benchmark_suite.py --only restrike_gamma_map
uv run pytest -q tests/python/test_restrike_gamma_map.py
```

The test file rebuilds the four variants' exposures independently, re-finds the zeros against the
engine, recounts the cancellation cells from the CSV, and re-derives every figure printed above.
