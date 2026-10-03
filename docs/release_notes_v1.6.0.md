# v1.6.0 — The release that paid for its own footnote

Released 2026-10-01. Predecessors: `v1.0.0`, `v1.1.0`, `v1.2.0`, `v1.3.0`, `v1.4.0`, `v1.5.0`. Total
monetary cost of building and validating this release: **$0**.

`v1.5.0` ended with a footnote: the recommendation it measured was a third-order argument, and a
third-order argument stops being one outside `|delta| <= 0.05`. The footnote also carried a derivation —
the five order-four partials, "done here so it is not lost between sessions". That derivation was wrong in
two ways, and this release fixes it, ships the corrected forms, and then measures what the next order
actually buys. The answer: a three-fold wider radius around the *place* of the crossing, and nothing
around the *amount*.

## What this release corrects in itself

**The reproduction gate.** Three CI rounds of this phase failed the same test for the same reason, and the
fourth round showed the repair had been incomplete. `reproduction_policy.conditioning_limited` named six
leaf fields as conditioning-limited; the runner re-ran the experiment and disagreed on twenty leaves, all
under `rays.<label>`. Names were the problem, not the numerics: a list of exempted fields can only be as
complete as the last platform that read it. The declaration is now three *families* — `rays`, `columns` and
a nested `headline.fits` built where the fitted numbers are computed — so a new fit joins the exemption by
construction. The runner's diff also exposed one *verdict* of the same kind: whether a ray's residual-ratio
turns back upward at the arithmetic floor compares two values that are themselves the floor's noise, and the
artifact declares those families under `reproduction_policy.noise_decided_verdicts` — empty by default, so
the other two studies keep every verdict gated, and this artifact's own claim that all four rays turn back
is still pinned exactly. `tests/python/test_fourth_order_crossing_map.py` plants both directions (a
perturbed slope must be tolerated, a perturbed zero count must be caught), and both were themselves mutated
to prove they fire. Audit finding 45, limitation #79(d)-(e).

**The closed forms.** §8 of `docs/phase_reports/phase-15-restrike-gamma.md` published three of the five
partials over denominators carrying the wrong power of `T`. The cause was one operator:
`d/dsigma|S` was written dividing by `sqrt(T)` where the chain rule multiplies by it, since
`dv/dsigma = sqrt(T)` with `v = sigma sqrt(T)`. What hid it was the check, not the algebra: the probe ran
at `T = 1`, the single maturity that experiment uses, where the missing factor is exactly `1` and the
residuals vanish. Re-run across tenors the residuals were proportional to `(T - 1)` and `(T^2 + 1)`. The
same reconstruction found `R(0,4)` committed with the opposite sign. The corrected forms now state a
uniform shape,

    V_[S x n_spot][sigma x n_sigma] = P * S^(1 - n_spot) * T^(n_sigma / 2) * R(d1, v) / v^3

with `P = e^{-qT} phi(d1)`, `v = sigma sqrt(T)`, `d2 = d1 - v`, and all five denominators equal to `v^3`.
They were recovered by solving a 28-coefficient linear system against the exact symbolic fourth derivative
of the price at 80 decimal digits and re-tested on 200 fresh points per order spanning `S` 40-160,
`sigma` 0.08-0.60, `T` 0.08-3.0 with non-zero `r` and `q`; worst relative error `4.5e-77`. The finite
difference that had been used first was discarded for its own reason: at fourth order `1/h^4` amplifies
double rounding until the worst relative residual reads 255.

## What this release adds

**Four sensitivities in the core.** `black_scholes_mixed_fourth_derivatives` returns `MixedFourthDerivatives`
— `spot_spot_spot_sigma`, `spot_spot_sigma_sigma`, `spot_sigma_sigma_sigma`, `sigma_sigma_sigma_sigma` —
in the shape above, written as Horner in `d1` with coefficients polynomial in `v`, and the degenerate edge
takes its limit rather than dividing by `v^3`. Validation is layered, because the fourth order is where a
finite difference stops being usable alone:

- ten five-point routes over a nine-rung ladder, each new partial reached as the slope of the published
  partial one order below, worst residual-to-band ratio `1.1e-2`;
- two exact relations obtained by differentiating the published `vanna` and `volga` homogeneity identities
  in volatility, worst relative residual `5.5e-16` and `1.2e-15`, no bump involved;
- bit-exact call/put identity, zero on both degenerate edges, and the same validation errors the Greeks
  raise.

Three of the four partials have an exact order-four partner in what the core already published. The fourth,
`V_sigmasigmasigmasigma`, has none — which is why it is held by three finite-difference routes rather than
an identity. The case that first asserted an identity for it differentiated `volga` in spot, and one spot
derivative of `d2V/dsigma2` is the *third*-order `V_Ssigmasigma`; it failed by a factor of -14 against the
number it claimed to check, which is the shape of the mistake rather than a tolerance problem.

**A wider radius, and the honesty to separate it from accuracy.**
`experiments/fourth_order_crossing_map/run.py` (suite member 16) adds the order-four piece to v1.5.0's own
column truncation — imported from that experiment rather than re-typed, on the same book and the same
bracket-and-bisect — and reports four things:

- **Ordering.** Along four joint-shock rays scaled from published size to a thousandth of it, the residual
  the cubic leaves falls with log-log slope `3.96-4.37` and the one the quartic leaves with `4.73-5.01`:
  fourth order against fifth. The ratio of the two falls against `log scale` with slope `0.62-1.04`, the
  `1.0` an extra order implies, and is down to `0.0013-0.048` by `scale = 3e-3`.
- **Radius.** Within `|delta| <= 0.15` the nearest predicted crossing lies inside the published `0.005`
  tolerance on every column that has a priced zero, worst `0.00162`, where the cubic's worst over the same
  columns is `0.01887` — a factor of `11.6`, and `211.6` inside the `0.05` limit v1.5.0 already gated
  (`1.15e-5` against `0.00243`). The gate is two-sided: the quartic has to pass exactly where the cubic
  fails, so the widening is not an artifact of a widened test.
- **Count.** The priced error has 13 zeros across the twelve columns; the cubic finds 14 and the quartic
  also finds 14. The quartic repairs the cubic's three column-level mistakes and invents a different one,
  at `k = 0.164` on the `delta = +0.10` column. Counts are reported rather than gated, because a tolerance
  on distance alone would have hidden a false zero.
- **Amount.** On `risk_off` the quartic moves the estimate of the shipped map's error from `-4135.87`
  against a priced `-5320.79` (22.3 % short) to `-6182.27` (16.2 % over): closer, on the other side, and
  the order-four piece it adds, `-2046.40`, is larger than the `1184.92` the price needed. For the
  re-struck map the pair reads 61.2 % against 44.5 %. At full shock size on a shallow ray the quartic
  residual is `1.38x` the cubic's with the opposite sign. A wider radius around the place is not a better
  estimate of the amount.

The ordering law is gated over `1e-3 <= scale <= 3e-1`, and the artifact publishes the through-the-floor
fit beside it (`2.46-4.30`): below `1e-3` the residuals are differences of book values near 1.09e5 at the
arithmetic floor, so a wider window would measure the subtraction rather than the series.

## Verification at this release

```text
uv run ruff check .                                     All checks passed!
uv run ruff format --check .                            134 files already formatted
uv run mypy python/quantrisk                            no issues found in 23 source files
uv run ctest --preset dev                               100% tests passed out of 201
                                                        (548,217 assertions in 200 test cases)
uv run pytest tests/python -q                           439 passed
uv run python scripts/run_benchmark_suite.py --require-all   16/16 executed and passed, 0 skipped, 103.9s
uv run quantrisk validate                               7/7 checks passed
uv run --frozen clang-format --dry-run -Werror          exit 0
uv run latexmk -pdf                                     43 pages, 999,330 bytes
uv run python scripts/run_mutation_suite.py             21/21 planted defects rejected
uv run python scripts/build_evidence_manifest.py        83 artifacts frozen
uv run python scripts/verify_evidence_manifest.py       0 missing, 0 unlisted -- Evidence is intact
```

The sweep and the freeze above both ran on commit `e1b67a0`, the tree they describe, because the sweep
refuses a dirty target and its verdict is a claim about a revision rather than about a session. This
commit adds the table, so it cannot carry its own freeze; `CONTRIBUTING.md` §4 step 7.

The suite grew from fifteen members to sixteen; the C++ suite from 198 tests to 201. The performance
artifact moved five times while this release was being verified — `8.12×` → `8.00×` → `7.99×` →
`8.26×` → `8.57×` → `8.06×` against pure Python, and `0.422×` → `0.450×` → `0.423×` → `0.479×` →
`0.471×` → `0.444×` against vectorised NumPy, with 38,284,576 paths/s for the core in the run this
release froze — because those fields are volatile by declaration and every producer run resamples them. The
spread is real and it is machine state, not code: an intermediate run taken while the desktop was busy
read `7.68×` — below the pinned `7.77×` floor, which is the guard telling the truth about a loaded
machine — and it was superseded by the quieter `8.06×` run this release froze rather than accepted, so the
committed history still spans `7.77×`–`8.70×`. Phase 18's verification run added `8.69×` and `0.455×` with
21,130,162 paths/s for the core — the ratio inside the pinned range and the absolute rate nearly halved,
because three other jobs were on the machine — which is the same measurement telling the two claims the
documents separate: the ordering is stable, the throughput is this machine's. That is why the claim the documents carry is the ordering,
never the number. `README.md`, `docs/interview_defense.md` and
`paper/technical_report.tex` were re-synced from the artifact in the same commit as the mutation-anchor
refresh (`CONTRIBUTING.md` §4 step 2). Both ratios remain inside the pinned history range
`7.77×`–`8.70×` and `0.42×`–`0.51×`. Two collateral edits from a blanket replacement — a `5.4` matching
inside `5.45 %` and a `1.17e-4` matching a speed standard deviation — were caught by a numeric-token
set difference against `HEAD` and restored; that is why the sync is scripted per field and audited.

## What is still not here

- `stress.run_scenario` still ships the two-factor delta-gamma-vega map. Nothing in this phase changes
  what the published scenarios report; the fourth order is an analysis surface, not a new default.
- No oracle provides a fourth partial. QuantLib 1.43's `VanillaOption` surface stops at
  delta/gamma/vega/theta/rho, so these are validated by identities and finite differences (row 19 of
  `docs/validation_matrix.md`), and limitation #70 still names that gap.
- The radius is stated for one book: three strikes, one maturity, one base volatility, the same grid as
  v1.5.0. Nothing estimates how it moves for a book whose fourth-order terms do not share these signs.
- Nothing derives that every public core entry point is reachable from Python. A struct bound without its
  function passed the parity guard in this phase, because that guard compares the binary against what the
  bindings *declare* — `docs/integrity_audit.md` finding 43.
- One three-strike ladder, one maturity, one volatility; four documents and eleven guards re-derive the
  numbers above from the artifacts rather than from each other.

## Correction, 2026-10-03 (Phase 18): the radius is this ladder's, and three-fold is not general

`experiments/second_book_crossing_map/` (suite member 17) re-measured the radius above on four further
books, after proving the re-derived machinery bit-identical to this release's on the published ladder —
ten coefficients, both truncations and the engine P&L over 30 joint moves, every difference exactly
zero. The direction holds: order four widens the contiguous crossing radius on 5 of 5 books, and on 5
of 5 its worst nearest-zero distance inside the cubic's own radius is the smaller. The size does not.

| book | cubic radius | quartic radius | widening |
|---|---|---|---|
| published ladder (this release's) | 0.05 | 0.15 | ×3.0 |
| long-dated wide | 0.10 | 0.30 | ×3.0 |
| short-dated tight | 0.02 | 0.05 | ×2.5 |
| deep out of the money | 0.15 | 0.20 | ×1.3 |
| in the money | 0.05 | 0.10 | ×2.0 |

So the sentences above that read "`|delta| <= 0.05` becomes `|delta| <= 0.15`", "a three-fold wider
radius", and the factor of `11.6` describe this three-strike ladder at `sigma = 0.20` and `T = 0.5`.
The bullet in "What is still not here" that said nothing estimated how the radius moves for another
book was correct when written and is now answered rather than assumed away. The mechanism is worse than
book-specific: the set spans the order-four-to-three ratio 254-fold on the expectation that a small
fourth-order piece leaves an added order little to remove, and the book built to that spec tied for the
*largest* widening. No mechanism replaces it. `docs/limitations.md` #81 carries the edges and
`docs/analysis/second_book_crossing_map.md` the reasoning, including the two ways the radius definition
was wrong before it was right.

No number this release published moves: the artifact, its gates, and the `0.00162` against `0.01887`
pair are the published ladder's and still reproduce. What changed is the scope of the sentence around
them.
