# Analysis — what a joint spot-and-volatility shock costs the delta–gamma–vega stress map

Phase 12's [note](delta_gamma_error_bound.md) bounds the stress map's error when **one** factor
moves. Its own refusal list said the multi-factor case was out of scope, on the ground that the
map treats volatility to first order. This note takes that refusal apart: it states the map,
derives the remainder when the equity factor and the volatility level move together, and measures
the result against the published book and the published scenario.

The short version is that the map's error is **quadratic** in a joint shock where it was cubic in
a single-factor one, that the leading term is available in closed form, and that none of that
makes the leading term the one that matters at the sizes a stress report contains — at
`risk_off` the closed-form quadratic is smaller than the largest omitted cubic term by 7.4× and
carries the opposite sign.

## 1. The map, stated exactly

`cpp/src/stress/engine.cpp:116` maps one factor's shock onto one position's P&L as

```
contribution = delta_i * s + gamma_i * s^2 + duration_i * a + vega_i * a + credit_i * a
```

where `s` is that factor's **relative** move and `a` its **absolute** move, `delta_i` is quoted per
unit relative move (so it already carries the spot), and `gamma_i` already carries the one-half
([factor.hpp:57-62](../../cpp/include/quantrisk/stress/factor.hpp)). For the equity option book
only the first, second and vega terms are non-zero, so for an equity move `delta` and a volatility
move `k`

```
P&L_map = Delta * (S * delta) + 1/2 * Gamma * (S * delta)^2 + Vega * k
```

with every Greek evaluated at the **base** market. Two properties of that line decide everything
below: the convexity term is built from base gamma and never re-struck, and the volatility term is
strictly linear — there is no `k^2` and no `h*k`.

Writing `h = S * delta` for the absolute spot move, the map keeps exactly

```
V_S * h + 1/2 * V_SS * h^2 + V_sigma * k.
```

## 2. Regularity, because a bound without hypotheses is a decoration

`V(S, sigma)` is the Black–Scholes price of a European call, `C^inf` in `(S, sigma)` on the open
domain `S > 0, sigma > 0`. The result below needs the segment from the base market to the shocked
market to stay inside that domain, which is the whole content of the hypotheses:

- `S > 0`, `K > 0`, `T > 0`;
- `sigma > 0` and `sigma + k > 0` — a vol move that reaches zero leaves the domain, and the map's
  error there is not a Taylor question at all;
- `S + h > 0`, i.e. `delta > -1`.

Every swept shock in the experiment satisfies these. A joint shock with `sigma + k = 0` is not
bounded by this note, and the core returns the `sigma = 0` limit for every higher derivative
in every one of `black_scholes_spot_derivatives`, `black_scholes_vol_cross_derivatives` and
`black_scholes_mixed_third_derivatives`, so the bound would read `0 <= 0` rather than fail.

## 3. The result

**Proposition.** Let `V` be the Black–Scholes price of a European call as above, let
`(h, k)` satisfy the hypotheses of §2, and let `g(t) = V(S + t h, sigma + t k)` for `t` in `[0, 1]`.
Then for some `xi` in `(0, 1)`

```
V(S + h, sigma + k) - V(S, sigma)
    = V_S h + 1/2 V_SS h^2 + V_sigma k                 (the map)
    + V_Ssigma h k + 1/2 V_sigsigma k^2                (order 2, omitted)
    + (1/6) g'''(xi)                                   (order 3, omitted)
```

where, evaluated at the moving market point `(S + t h, sigma + t k)`,

```
g'''(t) = V_SSS h^3 + 3 V_SSsigma h^2 k + 3 V_Sssigma h k^2 + V_Sssss k^3.
```

Consequently the map's error `R` satisfies both

```
|R - (V_Ssigma h k + 1/2 V_sigsigma k^2)| <= 1/6 * sup_{t in [0,1]} |g'''(t)|      (the bound)
6 * (R - (V_Ssigma h k + 1/2 V_sigsigma k^2)) in [min g''', max g''']               (the sharp form)
```

**Proof.** On the segment, `S + th > 0` and `sigma + tk > 0` by hypothesis, so `g` is a `C^3`
function of one variable and Taylor's theorem with the Lagrange remainder at `t = 1` gives
`g(1) = g(0) + g'(0) + 1/2 g''(0) + (1/6) g'''(xi)`. The chain rule gives
`g'(t) = V_S h + V_sigma k`. Differentiating again, and using that `h` and `k` are constants in
`t`, `g''(t) = V_SS h^2 + 2 V_Ssigma h k + V_sigsigma k^2`. One more application gives
`g'''(t) = V_SSS h^3 + 3 V_SSsigma h^2 k + 3 V_Sssigma h k^2 + V_Sssss k^3`, the binomial
coefficients arising from the number of ways each of the three differentiations can fall across
the two factors. Subtract the three terms the map keeps, and identify
`V_S h + V_sigma k + (V_Ssigma h k + 1/2 V_sigsigma k^2) + 1/2 V_SS h^2` with
`g(0) + g'(0) + 1/2 g''(0)`. The sharp form is the intermediate value property applied to
`g'''` on `[0, 1]`, since `6(R - quadratic)` *equals* `g'''(xi)` for some `xi` in the interval;
the absolute-value bound is its consequence. `|`

The four third-order partials and the two second-order cross partials are implemented in the core
as `black_scholes_spot_derivatives`, `black_scholes_vol_cross_derivatives` and
`black_scholes_mixed_third_derivatives`. The `Greeks` struct is a released surface and was not
touched; these are separate value types beside it.

## 4. Predictions, written down before the comparison

Reading the proposition off the published book's own exposures — `vanna = 192.33`,
`volga = 5.3392e5`, `V_SSsigma = -1244.76`, `speed = -6.9224`, on a base value of `1.0891e5` — five
things can be stated in advance, each of which the data could have contradicted.

**P1 — the order halves.** Along any fixed ray `(h, k) * t` that is not purely along spot, the
map's error must shrink like `t^2`, and `error / (vanna*h*k + 1/2*volga*k^2)` must tend to 1. On a
pure-spot ray it must keep shrinking like `t^3`, because then `k = 0` kills both new terms.

**P2 — the sharp form must hold where P1 stops helping.** The inclusion is exact, so it has to
hold at `t = 1` on a 30% shock, where P1's ratio is nowhere near 1. If the inclusion only holds on
small shocks it would be a statement about the asymptotics rather than about the map.

**P3 — the quadratic is the leading term, not the largest.** On `risk_off` the two legs are
`h = -15` and `k = +0.06`. The quadratic evaluates to `787.96`, while the mixed cubic
`1/2 * V_SSsigma * h^2 * k` evaluates to `-8402.16`. P3 predicts the *interaction of the convexity
with the vol move* dominates the "true" second-order term by an order of magnitude — which is a
claim about what to fix first, and it is false if the numbers come out the other way.

**P4 — the sign is provable on the published scenario.** With `g'''` ranging over
`[-4.1111e4, -2.9543e4]` on that segment, the translated interval for the error is
`[-6063.95, -4135.87]`, which excludes zero. If it straddled zero, no sign statement would be
available, and the analysis would have to say so.

**P5 — the ranking varies across the scenario space.** P3 is one cell. Whether the quadratic, the
spot cubic or the mixed cubic dominates must be counted over the whole joint grid, because a
prioritisation that holds at one scenario and not at its neighbours is not a prioritisation.

## 5. Results

All figures below are from
`experiments/two_factor_error_bound/results/two_factor_bound.json`, reproducible with the command
in §7. `h` is always the absolute spot move, `k` the absolute vol move.

**P1.** The fitted log-log slope of `|error|` against shock size, over four successively narrower
windows:

| ray | widest window | next | next | narrowest |
|---|---|---|---|---|
| crash: `delta = -0.15, k = +0.06` | 1.9098 | 1.9762 | 1.9929 | **1.9975** |
| melt-up: `+0.15, -0.06` | 2.0512 | 2.0208 | 2.0069 | **2.0024** |
| aligned: `+0.15, +0.06` | 1.7979 | 1.9566 | 1.9875 | **1.9957** |
| pure volatility: `0, +0.06` | 1.9944 | 1.9981 | 1.9994 | **1.9998** |
| pure spot: `-0.15, 0` | 3.0061 | 3.0023 | 3.0010 | **3.0009** |

Every joint ray converges to 2 and the pure-spot ray holds at 3, which is where Phase 12 put it. The
ratio of error to the closed-form quadratic at the smallest scale reaches 0.9937, 1.0062, 0.9891 and
0.9997 respectively, held to 2% on all four.

Two different assertions are made about these two groups, and the difference is a measured
conditioning gap rather than a preference. For the **four joint rays** the guard requires both that
the narrowest window sit inside the band and that it be closer to the theory value than the widest
was — a real convergence claim, since the crash ray's distance falls 0.0902 → 0.0025, a 36×
improvement. For the **pure-spot ray** no ordering of any kind is asserted; only that every one of
its four windows lands within 0.05 of 3, and the worst observed anywhere is 0.0087.

The reason is in the artifact under `fit_conditioning`. The error is the residue of subtracting book
values near 1.09e5, whose double spacing is 2.418e-11. At the tightest fit sample the pure-spot ray's
error is 3.098e-08 — **1281×** that floor — while the four joint rays' are 1.3e6 to 1.9e6 times it,
about a thousand-fold better conditioned. A slope fitted across four decades of samples whose last
ones are a few thousand ulps of a cancellation is loose at the 1e-2 level, which is larger than the
6e-3-to-9e-4 "improvement" the macOS series shows. So it is not that the pure-spot estimate is bad —
it is 3.00 to within 0.009 everywhere — but that *ordering* its windows compares two numbers whose
difference is noise. The runner made this unavoidable rather than arguable: a stepwise guard passed
here and raised on Linux (`3.000121 → 2.996952`), then the endpoint version of the same idea failed
there too (`3.004587 → 2.991277`), and both platforms were inside every band the whole time. The
second of those is quotable from run `36415073007`; the first is recorded from run `36413144612`,
whose retained job log ends at `running two_factor_error_bound ...` without the message, so that pair
is the session's record rather than a retrievable artifact. Every
window is published in `slopes` and `asymptotics`, so the trend is visible instead of summarised
into a boolean.

**P2.** Across the swept grid of 12 equity shocks by 11 volatility shocks — 132 joint shocks, the
largest being a 30% equity move with a 20-point vol rise — the inclusion holds on **132/132**. It
also holds on the published-size shocks where P1's ratio is `-6.75`: the inclusion is doing real
work that the asymptotics cannot.

**P3.** On `risk_off` (`delta = -0.15`, `k = +0.06`, the shocks imported from
`experiments/stress_testing/run.py` rather than re-typed here):

| quantity | value |
|---|---|
| re-priced P&L | −71 559.18 |
| map P&L | −66 238.39 |
| error | **−5320.79** |
| `vanna*h*k` | −173.10 |
| `1/2 volga*k^2` | +961.06 |
| whole quadratic | +787.96 |
| `1/2 V_SSsigma*h^2*k` | **−8402.16** |
| `1/6 V_SSS*h^3` | +3893.86 |
| `1/2 V_Sssigma*h*k^2` | −175.07 |
| `1/6 V_Sssss*k^3` | −240.46 |

P3 is confirmed and then some: the mixed cubic is 7.4× the entire quadratic, and the quadratic
alone predicts the error to be **+788** when it is **−5321** — the leading term in the limit points
the wrong way at the size the scenario actually uses.

The mechanism is worth naming, because it is not exotic. The map applies base gamma across a move
that changes gamma: `1/2 Gamma(sigma + k) h^2 = 1/2 Gamma h^2 + 1/2 V_SSsigma h^2 k + O(k^2)`. That
second piece is the largest thing the map loses here. It is also the cheapest to fix: re-striking
gamma at the shocked volatility removes it, while adding vanna and volga terms removes only the
smaller pair.

**P4.** The interval `[−6063.95, −4135.87]` excludes zero, so the *sign* of the map's error on
`risk_off` is proved rather than estimated: the map understates the loss. The interval's width is
1928.09, which is 36.2% of the error it bounds — informative rather than vacuous.

**P5.** Counting the largest omitted piece over the 132-cell grid:

| term | cells |
|---|---|
| `1/2 V_SSsigma h^2 k` (gamma at the wrong vol) | 64 |
| `1/6 V_SSS h^3` (the pure-spot cubic, bounded in Phase 12) | 36 |
| `1/2 V_sigsigma k^2` (volga) | 32 |
| `vanna h k` | 0 |
| the two remaining mixed cubics | 0 |

So the ranking is genuinely three-way and scenario-dependent, and the mixed `vanna*h*k` term —
the one the order argument singles out — is never the largest anywhere on this grid.

## 6. Where the analysis stops being useful

**Order is not size.** "The error is quadratic" is a statement about `t -> 0`. At published sizes
it is a minority term (P3), and on this book the aggregate `vanna` is small for an incidental
reason worth stating: the K=90 and K=110 legs contribute `−5089.09` and `+5628.57` and nearly
cancel, leaving `192.33`. A concentrated single-strike book would rank differently, and nothing
here should be read as a bound on *this map's* error for an arbitrary book.

**The ridge is not verified.** The quadratic form `k*(vanna*h + 1/2*volga*k)` vanishes on the
direction `k/h = -2*vanna/volga = -7.2044e-4`, a closed-form prediction of a direction along which
the map should be unusually accurate. Its empirical counterpart is the root of the *full* error,
and that root's displacement from the predicted one is `O(t)` — so bracketing it needs a grid
whose useful width shrinks with the very parameter being sent to zero. The experiment records what
a fixed 39-point scan does: root at 0.87× the prediction at scale 1, 1.81× at scale 0.5, and not
found at scale 0.1. That pattern is a property of the scan, so neither agreement nor disagreement
is claimed, and the probe ships in the artifact so the refusal can be checked rather than trusted.

**Two factors, not the whole scenario.** `risk_off` also moves rates by −50bp and credit by
+100bp, mapped linearly by duration and credit sensitivity. The omitted convexity in those factors
is a different set of derivatives and is not bounded here.

**Black–Scholes only.** The four third-order partials are closed forms of this model. The Heston
book in `experiments/path_dependent_vs_quantlib` has no equivalent closed form, so the same
argument there would need a numerically differentiated `g'''` and would inherit its error.

**The bound is about the map, not the scenario.** It says how much of a stress number is Taylor
truncation and nothing about how much is choice. The scenario set has no oracle and this note does
not manufacture one ([validation_matrix.md row 12](../validation_matrix.md)).

## 7. Reproducing

```
uv run python experiments/two_factor_error_bound/run.py
uv run python scripts/run_benchmark_suite.py --only two_factor_error_bound
uv run pytest tests/python/test_two_factor_bound.py
```

The tests re-derive `g'''` by differentiating the *price* along the ray rather than assembling it
from the closed forms, and re-check every published figure against the core, so a wrong partial
fails there before it can reach this document. The claim `error = quadratic + (1/6)g'''(xi)` is
falsified by the closed forms themselves if any of the six is transcribed incorrectly: the
experiment raises rather than publishing. Nine such slips were introduced deliberately during this
phase — a dropped minus on vanna, `d1` where `d2` belongs, an extra `sigma` in volga's denominator,
a volga sign slip, a sign inside `d1*d2 - 1`, the `sqrt(T)/sigma` additive term dropped from
`V_Sssigma`, two separate mutilations of `V_Sssss`, and the minus on the spot cubic — and the C++
net caught all nine, between 18 and 72 failed assertions each. Two of them were additionally
caught by the Python tests, which do not share a line of code with the C++ cases.
