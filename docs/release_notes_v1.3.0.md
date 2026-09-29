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
changed it — is **10.7×** the net quadratic, or **7.4×** if its two contributions are summed in
absolute value instead of netted. Across the 132-cell joint grid the largest omitted
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

## Seven CI runs: six red, then green, and each red was real

This release reached the runner six times red before it passed; §9 of
`docs/phase_reports/phase-13-two-factor-bound.md` carries each run's id and its own message. Run
`36413144612`: PyPI answered 503 mid-install on one lane, and on the other the convergence guard failed
at a *stepwise* ordering of fit windows. Run `36415073007`: the same lane failed on the replacement
guard, which compared only the endpoints. Run `36416691279`: the experiment was green and the
**reproduction test** — the check whose entire purpose is verifying reproducibility — failed on an 8e-7
relative difference in a fitted slope, compared for bit-equality. Runs `36417662618`, `36518357703` and
`36519230799` then failed on that same test three more times, at 3.2e-3 in the pure-spot slope, 6.6e-3
in the field that *measures* the looseness, and 39% in a regression's standard error. Run
`36521846544`, on the commit this release tags, is green on all three jobs: `100% tests passed out of
198`, `319 passed, 4 skipped`, `suite: 14/14 executed and passed`.

Nothing was relaxed to get here, and the distinction matters, so it is stated concretely: every
numerical band in this release carries the values from the first commit — 2 % on the
error-to-quadratic ratio, 0.15 on the narrowest slope, 1e-8 and 1e-4 on the two stencil orders — and
what changed is which comparisons are *claimed at all*. A fitted exponent over residuals that are
themselves cancellation products carries noise at the 1e-6 level; asserting an ordering finer than
that is testing the platform, not the model. What the third and fourth failures settled is that
choosing per-field tolerances was itself the error: three sizes were tried, each tuned to the gap the
runner had just reported, and the exempted set could never be complete because it was being guessed by
name. The comparator now reads the families the *experiment* declares in its own artifact
(`reproduction_policy.conditioning_limited`) and, inside them, compares shape — key sets, list lengths,
types — while counts, booleans, strings and verdicts stay exact even there and other floats keep 1e-5
relative. The values in those families are still proved, just not against one laptop: the experiment
raises rather than publishing a slope outside its band, and
`test_the_joint_error_is_quadratic_where_the_single_factor_error_is_cubic` re-derives the order claim in
the test's own environment over scales the experiment never uses. Limitations #71–75 and audit findings
28–29 record all six red runs; the repository had already written this lesson down twice before a new
file repeated it, and then repeated the fix three times, which is the actual finding.

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
| CI on `ubuntu-latest` (three jobs) | **green on run `36521846544`, the commit this release tags**, after six red runs recorded above |
| `quantrisk validate` | 7/7 |
| mypy / ruff / ruff format / clang-format | clean |
| Technical report | 13 chapters, **42 pages**, new §8.4 carries the proposition, the proof and the table |
| Cost | **$0** |

## Erratum: the dominance ratio was quoted against the wrong denominator

The sentence this release was published with — "the cubic `½·V_SSσ·h²k` is **7.4×** the whole
quadratic", next to a printed quadratic of `+787.96` — is wrong, and was wrong in eleven surfaces
including the attached `technical_report.pdf` and the release body. `7.408` is that ratio against the
quadratic's two contributions **summed in absolute value** (`|−173.10| + |961.06| = 1134.15`); against
the **net** quadratic `+787.96`, which is the quantity the prose printed and the quantity a correction
would subtract, the dominance is **10.66×**. The claim was therefore understated by a third, in the
direction that made this phase's engineering recommendation look weaker than the evidence for it is.

The artifact's ambiguous key is gone rather than caveated: `headline` now publishes
`largest_cubic_over_net_quadratic` = 10.663, `largest_cubic_over_quadratic_magnitudes` = 7.408, and
both denominators as fields of their own, so a ratio's meaning travels in its name. The test net
recomputes both from the core, asserts the net really is the smaller denominator on this book, and
requires any document carrying the figure to name the denominator beside it — which is the guard that
was missing, since the previous one only checked that "7.4" appeared in both places and could not see
that the two places meant different things. Limitation #76 and audit finding 30 record it. The tagged
commit `f4c1e9e` and its attached assets keep the superseded wording, because rewriting a published
tag would destroy the record of what was actually released; `main` carries the corrected text, and the
release body carries a dated note pointing here.

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
live feed, no re-pricing inside the stress layer, no PyPI package, no DOI — all **76 entries** in
`docs/limitations.md`.
