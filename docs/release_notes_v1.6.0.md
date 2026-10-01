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
uv run ruff format --check .                            132 files already formatted
uv run mypy python/quantrisk                            no issues found in 23 source files
uv run ctest --preset dev                               100% tests passed out of 201
                                                        (548,217 assertions in 200 test cases)
uv run pytest tests/python -q                           437 passed
uv run python scripts/run_benchmark_suite.py --require-all   16/16 executed and passed, 0 skipped, 75.0s
uv run quantrisk validate                               7/7 checks passed
uv run --frozen clang-format --dry-run -Werror          exit 0
uv run latexmk -pdf                                     42 pages, 998,781 bytes
uv run python scripts/run_mutation_suite.py             20/20 planted defects rejected
```

The suite grew from fifteen members to sixteen; the C++ suite from 198 tests to 201. The performance
artifact moved three times while this release was being verified — `8.12×` → `8.00×`
→ `7.99×` → `8.26×` against pure Python, `0.422×` → `0.450×` → `0.423×` → `0.479×` against vectorised
NumPy, 45,982,736 paths/s for the core in the run now in the tree — because those fields are volatile by
declaration and every producer run resamples them. `README.md`, `docs/interview_defense.md` and
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
