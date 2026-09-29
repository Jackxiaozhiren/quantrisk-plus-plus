# v1.3.0 — The refusal became a result, and the leading term had the wrong sign

Released 2026-09-28. Predecessors: `v1.0.0`, `v1.1.0`, `v1.2.0`. Total monetary cost of building and
validating this release: **$0**.

`v1.2.0` proved a remainder bound for the stress map and **refused** the multi-factor case, on the
ground that the map treats volatility to first order. That refusal named the project's exact gap:
the published scenario set contains no single-factor scenarios, so the bound covered a case the
reports do not contain. `v1.3.0` takes it apart.

## What this release adds

**The result.** The map is `delta_i * s + gamma_i * s^2 + vega_i * a` — second order in the equity
factor, **strictly linear** in the volatility factor, with no convexity and no cross term. So for a
joint shock (spot `h`, volatility `k`), applying Taylor's theorem once to `g(t) = V(S + th, σ + tk)`
and the chain rule three times gives, for some `xi` in `(0,1)`:

> `error = vanna·h·k + ½·volga·k² + (1/6)·g'''(xi)`, with
> `g''' = V_SSS·h³ + 3V_SSσ·h²k + 3V_Sσσ·hk² + V_σσσ·k³`

The map's joint-shock error is therefore **quadratic**, where the single-factor error was cubic. As
in `v1.2.0` this is not primarily an inequality: `6·(error − quadratic)` *equals* `g'''(xi)`, so it
must lie inside the segment's own range of `g'''` — a form that refutes a wrong partial the moment
one is transcribed badly.

**Five new core functions' worth of closed forms.** `black_scholes_vol_cross_derivatives` (vanna
`−e^{−qT}φ(d₁)d₂/σ`, volga `vega·d₁d₂/σ`) and `black_scholes_mixed_third_derivatives`
(`V_SSσ = γ(d₁d₂−1)/σ`, `V_Sσσ`, `V_σσσ`). They arrived as new value types because `Greeks` is a
frozen, already-released surface.

**What it corrected — in itself.** The plan was to publish the quadratic as *the* multi-factor
correction. Measured, that is wrong in sign, not merely in size: on the repository's own `risk_off`
scenario the closed-form quadratic is **+787.96** while the error is **−5320.79**, because the cubic
`½·V_SSσ·h²k` — gamma evaluated at the base volatility and applied across a move that has already
changed it — is **7.4×** the whole quadratic. Across the 132-cell joint grid the largest omitted
piece is that term in 64 cells, the pure-spot cubic in 36 and volga in 32, while `vanna·h·k`, the
term the order argument singles out, is largest **nowhere**. The actionable conclusion is the opposite
of the obvious one: the cheap improvement to this map is **re-striking gamma at the shocked
volatility**, not adding vanna and volga.

**Measured.** The error's log-log slope against shock size converges on 2.0 along every joint ray
(1.9098 → 1.9975 on the crash ray from widest to narrowest window) while a pure-spot ray on the same
book holds at **3.0009** — `v1.2.0`'s answer, reconciled rather than displaced. The Lagrange inclusion
holds on **132/132** joint shocks, out to a 30 % equity move with +20 volatility points. On
`risk_off` the interval for the error is **[−6063.95, −4135.87]**, which excludes zero: the *sign* of
the published error is proved, not estimated, and the interval's width is 36 % of the quantity it
bounds.

## How it was not gotten wrong

- **Bounded against the shipped engine, not a re-typed formula.** Every error is
  `run_scenario`'s own P&L minus a full Black–Scholes re-pricing. A separate test asserts the
  engine's joint-shock output *is* `delta*s + gamma_map*s² + vega*k`, so the term being subtracted is
  demonstrably the term being omitted.
- **The scenario is imported, not copied.** `risk_off`'s shocks are loaded from
  `experiments/stress_testing/run.py`, so the bound cannot silently drift from the scenario the
  repository publishes.
- **Checked by code that shares nothing with the formulas.** `g'''` is rebuilt as a Richardson-
  corrected third difference of the **price** along the ray — no partial anywhere — and agrees with
  the closed-form assembly to 3.9e-8. Vanna is reached two ways (d(vega)/dS and d(delta)/dσ) that
  agree to 1.4e-7 with no formula on either side; volga is checked against the price's curvature.
- **Nine deliberate transcription slips, all caught.** A dropped minus, `d₁` where `d₂` belongs, an
  extra `σ` in a denominator, a sign inside `d₁d₂ − 1`, an additive term deleted, two mutilations of
  `V_σσσ`, and the minus on the spot cubic: between 18 and 72 failed assertions each.
- **Tolerances sized with their steps.** First-derivative routes are held to `1e-8` relative plus
  `1e-13` absolute; second-derivative routes get a band two orders looser, with the measured reason
  beside the constant — at the σ=0.10/T=0.10 rung the sixth derivative of the price binds at any
  round-off-safe step. Worst observed residual is 1.6e-2 of its own band, so every route sits at
  least 60× inside it.

## Two convergence guards the laptop agreed to and the runner refused

The guards above also asserted, first stepwise and then at the endpoints, that narrowing the fit
window brings the slope closer to theory. Both passed locally; both failed on Linux, on the
pure-spot ray, whose series there read `3.004587 -> 2.991277` against `3.006067 -> 3.000915` here —
every value within 0.009 of 3 on both platforms. The artifact now publishes `fit_conditioning`, which
is what decides it: the pure-spot ray's tightest error sample is 1281× the double spacing of the
1.09e5 book value it is subtracted from, while the four joint rays are 1.3e6–1.9e6×, so ordering the
pure-spot windows compares noise. Convergence is now claimed only where the conditioning makes it
meaningful, every window is published rather than reduced to a boolean, and **no numerical band was
moved** — 2 % on the ratio and 0.15 on the narrowest slope are the values the first commit carried.

## Four CI runs, all red before the last, and each red was real

This release reached the runner four times before it passed. Run 1: PyPI answered 503 mid-install on
one lane, and on the other the convergence guard failed at a *stepwise* ordering of fit windows. Run
2: the same lane failed on the replacement guard, which compared only the endpoints. Run 3: the
experiment was green and the **reproduction test** — the check whose entire purpose is verifying
reproducibility — failed on an 8e-7 relative difference in a fitted slope, compared for bit-equality.
Run 4: both lanes green.

Nothing was relaxed to get there, and the distinction matters, so it is stated concretely: every
numerical band in this release carries the values from the first commit — 2 % on the
error-to-quadratic ratio, 0.15 on the narrowest slope, 1e-8 and 1e-4 on the two stencil orders — and
what changed is which comparisons are *claimed at all*. A fitted exponent over residuals that are
themselves cancellation products carries noise at the 1e-6 level; asserting an ordering finer than
that is testing the platform, not the model. The comparator now gives floats documented slack and
gives counts, booleans, strings and structure none, and it is calibrated by being shown both a
difference to tolerate and eight kinds of difference to reject. Limitations #71–73 and audit findings
28–29 record all three rounds; the repository had already written this lesson down twice before a
new file repeated it, which is the actual finding.

## Two documentation defects this release found in itself

- **The validation matrix had carried two rows numbered 13** since `v1.2.0` added its row on top of
  `v1.1.0`'s. The guard written to catch a stale matrix count could not see it: it counts *rows*, and
  two rows numbered 13 still make eighteen. The numbering is what prose cites, so a reader following
  "row 14" landed on the wrong entry. Renumbered, and the guard now asserts uniqueness, contiguity and
  that every in-file `row N` citation resolves. A neighbouring heading claiming "Four rows" over three
  paragraphs is derived from the body too.
- **A correct asymptotic claim, quoted at report sizes, pointed the wrong way** — recorded above, and
  the reason the order statement is never published without the size decomposition beside it.

## Verification at this release

| Check | Result |
|---|---|
| CTest | **198 passed** (547,845 assertions in 197 Catch2 cases), up from 194 |
| pytest, `oracles` extra installed | **388 passed**, 0 failed, 0 skipped; 319 collected without it |
| Benchmark suite, `--require-all` | **14/14 executed, 0 failed, 0 skipped** |
| Evidence manifest | **76 artifacts**, 0 CHANGED / 0 VOLATILE / 0 MISSING / 0 unlisted |
| `quantrisk validate` | 7/7 |
| mypy / ruff / ruff format / clang-format | clean |
| Technical report | 13 chapters, **41 pages**, new §6.4 carries the proposition, the proof and the table |
| Cost | **$0** |

## What is still not here

The bound covers the equity × volatility pair on a Black–Scholes European book. The rate and credit
legs of `risk_off` are still mapped linearly and their omitted convexity is unbounded anywhere in
this repository, and nothing here travels to Heston, where no equivalent closed form exists. The
near-cancellation that makes the quadratic small is a property of *this* three-strike ladder — its
K=90 and K=110 legs carry vanna of −5089.09 and +5628.57, leaving 192.33 — so a concentrated book
ranks the terms differently. The direction in which the quadratic vanishes is predicted in closed
form and **deliberately not verified**: locating its empirical counterpart needs a bracket whose
useful width shrinks with the shock, so the probe ships in the artifact and the claim is withheld.
No oracle in this dependency set publishes a vanna, a volga or a mixed third partial — QuantLib's
Python surface stops at vega — so the new closed forms rest on differences, exact identities and
parity rather than an external comparison. A bound still says nothing about whether a scenario is
plausible. And the wider gaps survive unchanged: no expected-return model, no term structure, no
live feed, no re-pricing inside the stress layer, no PyPI package, no DOI — all **74 entries** in
`docs/limitations.md`.
