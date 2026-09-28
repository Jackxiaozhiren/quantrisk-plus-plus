# Analysis — a remainder bound for the delta–gamma stress map that predicts a sign change

Added in Phase 12. This is the project's first **worked analysis result**: a derivation with a
proof, three closed forms, and numeric consequences that were computed *before* being compared to
data the repository had already published and frozen. It is the item ranked third in
`docs/portfolio_audit.md` §10 — "the only thing separating this portfolio from excellent engineer,
unclear mathematician" for Financial Mathematics and Applied Mathematics programmes — and it stayed
open through Phase 11 on purpose, because the alternative was to write the bound afterwards and
call the agreement a prediction.

The object is `stress.run_scenario`'s P&L map. Its measured error against a full Black–Scholes
re-pricing is published in
`experiments/stress_testing/results/linearisation_error.csv`, and the prose shipped with it said the
error "grows with the shock size". **That sentence is false of the repository's own data**, which is
the reason this note exists: the absolute error is 649.5 at a 10 % down move and 528.5 at 20 %. What
follows explains why, and then says where the explanation stops.

Everything below is reproduced by
`uv run python experiments/linearisation_error_bound/run.py`; `docs/analysis/` is new in this phase
and holds the derivations that the model cards deliberately do not.

---

## 1. The map, stated exactly

For one equity factor with a relative move `δ` — spot becomes `S(1+δ)`, `h = Sδ`, every other
parameter held — the engine maps a position to

$$ m(\delta) \;=\; \underbrace{\Delta S\,\delta}_{\text{linear}} \;+\;
\underbrace{\tfrac12 \Gamma S^{2}\delta^{2}}_{\text{convexity}}, \tag{1} $$

with `Δ = ∂V/∂S` and `Γ = ∂²V/∂S²` evaluated at the **unshocked** market. In
`cpp/src/stress/engine.cpp` this is `contribute()`: `out.linear = delta · relative` and
`out.convexity = gamma · relative²`, the factor `½` and both powers of `S` folded into the exposure
blocks the caller supplies. The remainder, written in the same sign convention as the committed CSV's
`abs_error` column, is

$$ R(\delta) \;=\; \bigl[V(S(1+\delta)) - V(S)\bigr] - m(\delta). \tag{2} $$

*The sign is chosen so (3) reads with a plus. The committed CSV's `abs_error` column is*
`mapped − revalued = −R`, *so magnitudes, ratios and the zero below are unaffected — stated
*because a reader comparing the two should not have to rediscover it.*

## 2. Regularity, because a bound without hypotheses is a decoration

Fix `S > 0`, `K > 0`, `σ > 0`, `T > 0`, and let `M = S(1+δ)` with `δ > −1`. On the compact segment
with endpoints `S` and `M`, the Black–Scholes price is `C^∞` in spot: it is smooth in `(S, σ, T)` on
the open domain, and the segment stays a positive distance from the two singularities — `S = 0`,
where `Γ ~ 1/S` diverges, and `σ√T = 0`, where the normal density collapses and `Γ` becomes a Dirac
mass at the strike. Hence `V'''` is bounded and uniformly continuous on the segment and Taylor's
theorem with the Lagrange remainder applies. Nothing else is assumed: no smallness of `δ`, no
asymptotics, no distributional statement about the underlying.

## 3. The result

**Proposition.** *Let `V` be the Black–Scholes price of a European option with `S, K, σ, T > 0` and
`m` the map (1). For every `δ > −1` there is a point `ξ` strictly between `S` and `S(1+δ)` such
that*

$$ R(\delta) \;=\; \tfrac16\,V'''(\xi)\,h^{3}, \qquad h = S\delta, \tag{3} $$

*so that*

$$ \lvert R(\delta)\rvert \;\le\; \tfrac16 \Bigl(\sup_{u\in[S,M]}\lvert V'''(u)\rvert\Bigr)\lvert h\rvert^{3},
\qquad\text{and}\qquad
\boxed{\;\min_{[S,M]} V''' \;\le\; \frac{6R(\delta)}{h^{3}} \;\le\; \max_{[S,M]} V''\;.'\;} \tag{4} $$

*The second display is the sharp form: the Lagrange coefficient*
`c(δ) := 6R(δ)/h³` *is not merely bounded in absolute value, it is trapped between the minimum and
maximum of* `V'''` *along the path. Moreover*

$$ V'''(S) \;=\; -\frac{\Gamma(S)}{S}\Bigl(1 + \frac{d_1}{v}\Bigr),
\qquad
V''''(S) \;=\; \frac{\Gamma(S)}{S^{2}}\Bigl[A^{2} + A - \frac{1}{v^{2}}\Bigr],
\qquad A := 1 + \frac{d_1}{v}, \tag{5} $$

*where `v = σ√T` and `d₁ = (ln(S/K) + (r − q + σ²/2)T)/v`, and both are identical for calls and puts
at the same strike.*

*Proof.* Taylor's theorem on `u ↦ V(u)` between `S` and `S+h` gives
`V(S+h) = V(S) + V'(S)h + ½V''(S)h² + (1/6)V'''(ξ)h³` for some `ξ` between the endpoints.
Substituting `V' = Δ`, `V'' = Γ` and (1)–(2) yields (3); dividing by `h³/6` and using that `V'''`
attains its extreme values on the compact segment yields (4); (3) then gives the absolute bound.

For (5), write `Γ(S) = e^{-qT}φ(d₁)/(S v)`. Since `∂d₁/∂S = 1/(S v)` and `φ'(x) = −xφ(x)`,

$$ \frac{d\Gamma}{dS}
 = \frac{e^{-qT}}{v}\cdot\frac{\varphi'(d_1)\frac{1}{Sv}\,S - \varphi(d_1)}{S^{2}}
 = -\frac{\Gamma}{S}\Bigl(1 + \frac{d_1}{v}\Bigr) = V''', $$

and one more differentiation, with `A' = 1/(S v²)` and `Γ' = −ΓA/S`, gives

$$ V'''' = -\frac{\Gamma'A + \Gamma A'}{S} + \frac{\Gamma A}{S^{2}}
 = \frac{\Gamma}{S^{2}}\bigl(A^{2} + A - v^{-2}\bigr). $$

Call/put equality for every order `≥ 2` follows from put–call parity
`V_call − V_put = S e^{-qT} − K e^{-rT}`, which is affine in `S`. ∎

Two remarks on what was *not* assumed, because both come back later.

**The order is three, not two.** A map retaining terms through `δ²` leaves a *cubic* remainder. The
linear-only map — the `linear_relative_error` column of the same committed CSV — has a quadratic
remainder and a different constant. Conflating them is the easy mistake, and the two are reported
separately.

**(3) is an equality with an unknown point, not a series.** There is no claim that (1) begins a
convergent expansion of the P&L, and `ξ` is never computed. That is what makes (4) checkable without
being circular: the theorem asserts the existence of *some* point where `V'''` equals `c(δ)`, so
`c(δ)` outside the segment's range of `V'''` would refute the closed form (5) itself.

## 4. Predictions, written down before the comparison

| # | Statement | Falsified by |
|---|---|---|
| P1 | `c(δ) → V'''(S)` as `δ → 0`, and `log\|R\|` vs `log\|δ\|` has slope **3** | the closed forms (5) |
| P2 | `c(δ) ∈ [min_{[S,M]} V''', max_{[S,M]} V''']` at every shock, up and down | the sign in (5), the derivation of (4) |
| P3 | For a **down** shock the ladder's `V'''` along the path changes sign, so `c` does too, so **`R` changes sign**: the map is exactly right at one specific shock size, and switches between understating and overstating the revalued P&L around it | the magnitude of `A = 1 + d₁/v` across strikes |
| P4 | For an **up** shock nothing crosses: `V''' < 0` throughout, `c` stays negative, and `\|R\|` is monotone increasing | same |
| P5 | The *departure* from cubic behaviour, per unit of `δ`, tends to `S·V''''/(4V''')` — so the fourth closed form is confirmed through prices, not only through a difference table | the sign and size of (5)'s second formula |

P3 is the interesting one and the one that could most easily have been wrong. It says the published
curve's dip is not noise and not a numerical artefact but a **zero of the remainder**, and it says
where that zero is — which is a statement about data frozen in `evidence/manifest.json` before this
derivation existed.

## 5. Results

All numbers from `experiments/linearisation_error_bound/results/linearisation_error_bound.json`.

**P1 holds.** Over the decade `2·10⁻³ … 2·10⁻²` — chosen to sit above the arithmetic floor of §6 and
below where `δ⁴` matters — the fitted slope of `log|R|` on `log δ`, pooled over up and down moves
(6 points), is **2.996188** with standard error **0.044006**: a deviation of **−0.087 standard
errors** from theory 3. At the smallest swept shock, 0.1 %, the remainder equals `V'''(S)h³/6` to
within **0.38 %**. The base value everything turns on is `V'''(S) = −6.9224` for this ladder.

**P2 holds everywhere it was tested.** A dense sweep of 300 shock sizes in each direction over
`0.1 % … 49.9 %` gives **zero violations** of the inclusion, the nine committed sweep points included.
The sharp form earns its place rather than dressing up the weak one: at a 20 % down move the trapped
interval is `[−6.9224, +17.3234]` and the coefficient sits at `−0.3964`, so an absolute-value bound
would have allowed a coefficient anywhere in `±17.3`, while this pins it to the sign change P3 is
about. The weaker envelope is genuinely tight away from that change — `|R| / bound` runs from
**0.9962** at the smallest shocks down to **0.2842** at the largest, a factor of 3.5 at worst — and it
collapses toward zero exactly where P3 puts `R` (**0.0229** at a 20 % move, beside the predicted zero
at 21.14 %). That collapse is what a supremum of `|V'''|` over a segment whose signed contributions
cancel must do; it is reported rather than smoothed.

**P3 holds, and this is the prediction.** The aggregate `V'''` of the ladder crosses zero at spot
**94.5456**, a **5.4544 %** down move, so beyond that shock the segment carries both signs and their
cubic contributions cancel. Carrying it through: `c(δ)` walks from `−6.8964` at a 0.1 % move to
`−0.3964` at 20 % and then to `+4.9855` at 40 %, and solving `R(δ) = 0` puts the remainder's own zero
at a **21.1446 %** down move. The committed CSV — frozen, hashed, and written by different code a
phase earlier — brackets that and only that: its `abs_error` is **−528.5351 at 20 %** and
**+12,526.8943 at 30 %**, the single sign change among its nine rows. At a 21 % move the remainder is
`|R| = 13.3`, against 649.5 at 10 % and 12,527 at 30 %. The map is *almost exactly right* at a 21 %
shock, and the theory says so before the sweep is run.

**P4 holds.** For up moves `c(δ)` runs `−6.9483 … −10.4706` and never crosses, `|R|` is monotone
increasing over all nine swept sizes, and the asymmetry between the directions follows from (5)
rather than from where the sweep landed. One number there should not be skipped: up-move ratios
`R / (V'''(S)h³/6)` climb to **1.51**, so the remainder at a 30 % up move is half again what the
base-point cubic term predicts, because `|V'''|` grows along an up path. Reading the leading term as a
two-sided estimate would understate that error by a third at the top of the range, and only the
segment supremum sees it coming.

`experiments/linearisation_error_bound/results/linearisation_bound.png` shows the three panels in the
order of the argument: domination against a `δ³` reference, the coefficient trapped inside the shaded
path range as it passes through zero, and the ladder's `V'''` along the down-shocked path with its
crossing marked.

**P5 holds, and it is the check that tests the second closed form rather than the first.**
`S·V''''/(4V''') = 3.752361` from (5). Dividing the measured departure from the cubic term by `δ`
gives `3.759289` on a 0.1 % down move and `3.745379` on the corresponding up move — the prediction
bracketed from both sides, each within 0.2 %. This matters more than a tidier agreement would
suggest: the finite-difference check on `V''''` in `tests/python/test_linearisation_bound.py` differs
from the same function the formula defines, whereas this one reaches `V''''` through the *price
surface*, which is a different route and could have disagreed.

The honest summary of §5 is that a two-line Taylor argument, given the closed form for one extra
derivative, explains a feature of a published curve that the accompanying prose had described
incorrectly — and that the explanation was testable in advance.

## 6. Where the analysis stops being useful

**Floating point arrives before the mathematics does, and its floor is a property of the book.**
`V'''(S)` here is `−6.9224`, so the cubic term at a 0.1 % shock is about `1.15·10⁻³` — large enough to
measure comfortably. The floor is set by the magnitude of what is being subtracted, not by the model:
at `δ = 10⁻⁵` the remainder is `1.13·10⁻⁹` against a book value near `9.8·10⁴`, i.e. about `10⁻¹⁴`
relative — tens of ulp — and by then the ratio `R / (V'''(S)h³/6)` has drifted from `0.99958` at
`δ = 10⁻⁴` to `0.98191`. The usable floor therefore sits near `δ = 3·10⁻⁵`, and the narrowest fitting
window used here (`2·10⁻⁴ … 5·10⁻⁴`) stays an order of magnitude above it.

This is a correction to an earlier draft of the same note, which put the floor at `10⁻³` and quoted a
ratio sequence of `0.9714, 0.9968, 1.0119` then `−333` and `+129,079`. That sequence was real — and
measured on the wrong thing: a single option, shocked by an *absolute* price increment rather than a
relative move, so the unit was wrong and the scale was wrong, and the numbers looked authoritative only
because they were precise. Recorded rather than replaced, because the lesson generalises twice over.
An arithmetic floor has to be measured on the book being analysed, and a floor lifted from a
similar-looking experiment is not a measurement. The same effect bounds the finite-difference checks
on the closed forms themselves: at a step of `10⁻⁵` the five-point stencil disagreed with `V'''` by
`3.6·10⁻⁹` at spot 90, which is the difference scheme failing rather than the algebra, and it is why
`tests/python/test_linearisation_bound.py` uses `h = 2·10⁻³` against a `10⁻⁹` tolerance with that
reasoning written into it rather than asserting a tighter number that cannot be met.

**A single fitted slope is not evidence of order three.** At any fixed window the fourth-order term
biases the log-log slope, and the bias scales with the window's top edge — which is why §5 reports a
sequence of shrinking windows converging on 3 from both sides. The first version of this analysis
pooled up and down moves into one three-point fit, got `3.037 ± 0.003`, and reported a value eleven
standard errors from the theory. Neither the eleven sigma nor the `±0.003` meant anything: the
scatter was the up/down separation appearing as curvature, and pooling was fitting a mixture. Fitting
the directions separately over hundreds of points is what produced the numbers in §5.

**The bound is about the map, not the scenario.** (4) says how much of a stress number is Taylor
## 7. Reproducing

```bash
uv run python experiments/linearisation_error_bound/run.py       # sweep, fits, and the guards
uv run pytest tests/python/test_linearisation_bound.py -q       # the predictions, as falsified tests
uv run python scripts/run_benchmark_suite.py --only linearisation_error_bound
```

The experiment is offline, deterministic, calls no oracle, and **raises rather than publishing**
if the absolute bound is violated, if the Lagrange coefficient escapes the path's range of `V'''` at
any of the 600 densely-tested shocks or the 18 swept ones, if either direction's widest-window slope
leaves `3 ± 0.1`, if narrowing the windows does not move each estimate *toward* 3, if the departure
from the cubic term fails to reach the `S·V''''/(4V''')` the closed forms predict, if the leading term
misses the remainder by more than 2 % at the smallest swept shock, if the predicted remainder zero
falls outside the bracket the published sweep supplies, or if the up direction turns out not to be
monotone. Each of those raises was observed to fire at least once while this analysis was being
written, which is the only reason to believe the guards are guarding.
