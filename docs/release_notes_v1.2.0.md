# v1.2.0 — A worked analysis result, and the sentence it corrected

Released 2026-09-28. Predecessors: `v1.0.0`, `v1.1.0`. Total monetary cost of building and
validating this release: **$0**.

## What this release adds

`v1.1.0` made the project empirical. `v1.2.0` makes it *analytical*: it adds a proved statement,
the closed forms it depends on, and the consequences that can be checked against data the repository
had already frozen. `docs/portfolio_audit.md` §10 ranked this third and warned it was "the only one
that risks being wrong in a way a specialist notices".

**The result.** The stress layer maps a shock to P&L with delta and gamma. For that map, with
`S, K, sigma, T > 0` and the shocked segment bounded away from zero, there is a point xi on the
segment with

> `R(delta) = (1/6) * V'''(xi) * h^3`, with `h = S * delta`,

so the Lagrange coefficient `c = 6R/h^3` is trapped between the minimum and maximum of the third
spot derivative along the path — not merely bounded in absolute value. The closed forms
`V''' = -(Gamma/S)(1 + d1/v)` and `V'''' = (Gamma/S^2)(A^2 + A - 1/v^2)`, with
`A = 1 + d1/v` and `v = sigma * sqrt(T)`, are new core functions, and call/put equality holds
bitwise for every order of two or more because put–call parity is affine in spot.

**What it corrected.** `experiments/stress_testing/results/linearisation_error.csv` has been in the repository
since Phase 7, and the prose beside it said the linearisation error grows with the shock
size. It does not: the error is 649.5 at a 10 % down move, **528.5 at 20 %**, and 12,527 at 30 %.
The theory predicts the shape rather than describing it — the book's third derivative crosses zero
at spot 94.5487, a 5.45 % down move, which puts the remainder's own zero at a **21.1447 %** move,
inside the single sign change the older artifact already contains. Two artifacts, written by
different code a phase apart, agreeing on a location.

**Measured.** 618 shocks in both directions give zero violations of the trap. The absolute envelope
is tight rather than vacuous: `|R|/bound` runs 0.9962 down to 0.2842. Fitted per direction over five
shrinking windows, the log-log slope of `|R|` converges on the theoretical three —
2.971017 → 2.998785 down, 3.025281 → 3.001209 up. The fourth derivative is confirmed a second time
through prices: the departure from cubic behaviour per unit of delta tends to
`S * V''''/(4 * V''') = 3.7523607`, measured 3.7592892 and 3.7453790 from the two directions.

## How it was not gotten wrong

Four plausible analysis results failed before any of them shipped, and each failure is recorded in
`docs/phase_reports/phase-12-remainder-bound.md` §4 and §6 rather than edited out:

- **Pooling up and down moves into one slope fit** returned `3.037 ± 0.003` — eleven standard errors
  from theory, where the sigma were computed from three points and the deviation *was* the
  direction-separation appearing as curvature. Fitting per direction over hundreds of points is what
  produced the numbers above.
- **A helper that indexed errors by `abs(move)`** made the two directions identical to sixteen
  digits. A duplicated result is far more convincing than a wrong one.
- **A finite-difference tolerance of 1e-9 at a step of 1e-5** disagreed with the closed form by
  3.6e-9 at the at-the-money strike. That is the stencil, not the algebra; the step and the
  tolerance are now justified next to each other (limitation #66).
- **A magnitude-only check on a sign-flipped stencil** agreed to 4e-11 and was wrong. The test now
  asserts the sign agrees.

One correction is worth stating twice because it is the generalisable kind: an earlier draft of the
analysis put the floating-point floor at a relative move of 1e-3, quoted to four significant figures.
It had been taken from a single-option test in *absolute price increments* — wrong unit, wrong scale.
Measured on this book the floor is near 3e-5. A floating-point floor is a property of the magnitude
being subtracted and has to be measured per book.

## Verification at this release

| Check | Result |
|---|---|
| CTest | **194 passed** (547,331 assertions in 193 Catch2 cases), up from 190 |
| pytest, `oracles` extra installed | **366 passed**, 0 failed, 0 skipped; 297 collected without it |
| Benchmark suite, `--require-all` | **13/13 executed, 0 failed, 0 skipped** |
| Evidence manifest | **72 artifacts, 6,488,904 bytes, 0 CHANGED / 0 VOLATILE / 0 MISSING / 0 unlisted / 0 warnings** |
| `quantrisk validate` | 7/7 |
| mypy / ruff / ruff format / clang-format | clean |
| Technical report | 13 chapters, **40 pages**, new §8.3 carries the proposition, the proof and the table |
| Cost | **$0** |

## What is still not here

The bound is for one factor with volatility held; a scenario that ties a vol bump to a spot move has
a quadratic leading remainder, and that case is recorded as a refusal rather than attempted
(`experiments/linearisation_error_bound/results/linearisation_error_bound.json`, `refusals`). No
reference library in this dependency set publishes a third or fourth derivative, so the validation
route is a finite difference plus a shared-gamma risk that limitation #65 states. A bound says how
much of a stress number is truncation, never how much is management choice. And the wider gaps
survive unchanged: no expected-return model, no term structure, no live feed, no re-pricing inside
the stress layer, no PyPI package, no DOI — all **66 entries** in `docs/limitations.md`.
