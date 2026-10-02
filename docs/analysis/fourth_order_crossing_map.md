# How far a fourth-order truncation predicts the stress map's crossing

Source: `experiments/fourth_order_crossing_map/` · suite member 16 · artifact
`experiments/fourth_order_crossing_map/results/fourth_order_crossing_map.json` · validation matrix
row 19 · limitation #79

## 1. The question v1.5.0 left open

`docs/analysis/restrike_gamma_map.md` §6 predicts where the shipped delta-gamma-vega map happens to
be exactly right. Write the base map's error along a column of fixed relative spot move `delta` (so
`h = S delta`) as a function of the volatility move `k`:

    1/6 V_SSS h^3
    + k   ( V_Ssigma h + 1/2 V_SSsigma h^2 )
    + k^2 ( 1/2 V_sigsigma + 1/2 V_Sssigma h )
    + 1/6 V_sigmasigmasigma k^3

Three pieces of that depend on `k`, and two of them can cancel. Where they do, the map's error is
zero by arithmetic rather than by merit. Locating those zeros from closed forms alone — nothing fitted
to the measured errors — worked within `|delta| <= 0.05`, to 0.0002-0.0024 in vol move against a
tolerance of 0.005, and drifted to 0.093 at `|delta| = 0.30`. The note called the drift "what a
third-order expansion deserves".

This experiment asks what the next order actually buys. The core now ships the four mixed fourth
partials (`black_scholes_mixed_fourth_derivatives`), so the same truncation can be carried to order
four by adding

    1/24 ( V_SSSS h^4 + 4 V_SSSsigma h^3 k + 6 V_SSsigmasigma h^2 k^2
           + 4 V_Ssigmasigmasigma h k^3 + V_sigmasigmasigmasigma k^4 )

on the same book, the same grid and the same bracket-and-bisect root finder, with the cubic truncation
imported from the phase-15 module rather than re-typed.

## 2. The extra order is the order it claims to be

Along four joint-shock rays, scaled from published size down to a thousandth of it, the residual left
by the cubic truncation falls with a log-log slope of **3.96-4.37**, and the residual left by the
quartic falls with **4.73-5.01**. Fourth order against fifth, which is the claim: a cubic truncation
of a two-variable expansion leaves a quartic remainder, and a quartic one leaves a quintic one.

The window is what makes those numbers mean anything, and both fits are published. The residual is a
difference of book values near 1.09e5, so below `scale = 1e-3` it is at the arithmetic floor; a fit
that includes that point returns 2.46-4.30 for the quartic, and on this machine all four rays turn
their residual-ratio back upward at that scale. That last count is not a finding: the comparison that
decides it is between two values which *are* the floor's noise, so the artifact reports it as one of
the quantities a fresh platform is entitled to print differently (see §6), and the claim the documents
carry is the through-the-floor degradation, not the count. The gated window is therefore
`1e-3 <= scale <= 3e-1`, and the through-the-floor fit sits next to it in the artifact so the choice
is auditable rather than asserted.

The bands around those slopes are sized from two platforms rather than one, because the slopes are the
least reproducible numbers in this artifact. The CI runner, on the identical committed artifact,
measured `5.223` on the crash ray where this machine measured `5.014`, and `4.323` on the shallow ray
where this machine measured `4.729` — the shallow ray's fifth-order residual is the smallest of the
four, so its fitted slope is the one sitting nearest the arithmetic floor. A band tight enough to make
`5.014` the ceiling rejects a machine that is not wrong (the first version did, twice: audit finding
44). So the bands are gross-error checks — cubic `3.5-4.6`, quartic `4.0-5.8` — and the load-bearing
ordering statements are scale-free: the quartic residual is smaller in magnitude than the cubic's at
*every* scale in the window, its ratio falls monotonically over the three largest above-floor scales
(`0.3`, `0.1`, `0.03`), and the two fitted slopes are compared to each other inside one run with the
sign gated and no margin — the margin is exactly what differs across machines. The ratio's own
log-log slope is reported (0.62-1.04 here, the `1.0` one extra order implies) and deliberately not
gated: it is a quotient of two subtraction-noise quantities, and the runner put the shallow ray at
0.381 where this machine reads 0.71.

The ratio of the two residuals falls against `log scale` with slope **0.62-1.04** — the 1.0 one extra
order implies — and is down to **0.0013-0.048** by `scale = 3e-3`.

## 3. The crossing radius triples

Within `|delta| <= 0.15`, the nearest zero of the quartic truncation lies inside the published 0.005
tolerance of the nearest zero of the priced error on all **seven** columns that have a priced zero
(eight columns are in range; `delta = -0.02` has none at all). Worst distance **0.00162**. The cubic
truncation, run through the same routine on the same columns, misses the tolerance on exactly the
four columns with `|delta|` = 0.10 and 0.15, worst **0.01887** — a factor of **11.6**.

Inside the limit v1.5.0 already claimed, the gap is larger: **1.15e-5** against **0.00243**, a factor
of **211.6**. Beyond 0.15 both fail, and the quartic fails less: 0.0323 against 0.0934 at
`delta = -0.30`.

The gate is two-sided. It requires the quartic inside tolerance *and* the cubic outside it on those
four columns, so a widened radius cannot be an artifact of a widened test.

## 4. What the extra order buys in count is less than what it buys in place

Across the twelve columns the priced error has **13** zeros. The cubic truncation finds 14 and
disagrees with the priced count on three columns; the quartic also finds 14, and disagrees on one —
a different column.

Concretely: the cubic misses a crossing at `delta = -0.05`, invents one at `delta = +0.05`, and
predicts a zero on the `delta = +0.30` column where the priced map has none. The quartic gets all
three right and then invents a zero at `k = 0.164` on the `delta = +0.10` column, where the priced
error crosses once, near -0.024. So the total count is the same and the *places* are not: the cubic's
errors are three near-misses spread over the grid, the quartic's is one false positive at the far end
of a column.

Which crossings exist is a question the truncation answers differently from the price. The counts are
reported rather than gated, because a tolerance on distance alone would have hidden a false zero
entirely.

## 5. None of it makes the amount cheaper to predict at published size

On the `risk_off` scenario (`delta = -0.15`, `k = +0.06`) the cubic truncation puts the shipped map's
error at **-4,135.87** against a priced **-5,320.79** — 22.3 % short. The quartic puts it at
**-6,182.27**, which is 16.2 % over: closer, on the other side, and the order-four piece it adds
(-2,046.40) is larger than the 1,184.92 correction the price needed. For the re-struck map of v1.5.0
the same pair reads +61.2 % against -44.5 %.

At full shock size the quartic is not even monotonically better. On the shallow ray — `delta = -0.05`,
`k = +0.03`, a third of the crash — its residual is **1.38x** the cubic's with the opposite sign,
where the same ray gives 0.23x at a third of the size. That is the shape of an asymptotic series
evaluated outside its region, and it is why the ordering law in §2 is gated to a third of the
published shock and no wider.

A wider radius around the *crossing* is therefore not a better estimate of the *amount*. Documents
that quote a predicted error still have to quote the priced one.

## 6. The cancellation cells are where the radius matters

v1.5.0's finding was that the re-strike does the most damage exactly where the shipped map looked
best: the 20 cells whose error was smaller than the term the recipe removes. Those cells sit at
crossings. A truncation that locates crossings to 0.0016 rather than 0.0024 inside `|delta| <= 0.05`,
and to 0.0016 rather than 0.019 out at 0.15, says the same mechanism is still the explanation over a
three-fold wider band of the grid — and it says which volatility moves to avoid if a re-struck map is
used anyway.

## 7. Where this stops being useful

- One three-strike call ladder, one maturity, one 20 % base vol, the same grid as v1.5.0. The
  coefficients are that book's sums, so a book whose fourth-order terms do not share its signs has a
  different radius and nothing here estimates by how much.
- The radius is stated in *relative spot move*. The columns are spaced 0.02, 0.05, 0.10, 0.15, 0.20,
  0.30; the widened limit falls between the sampled columns 0.10 and 0.15 in the sense that it is
  demonstrated *at* 0.15, not interpolated to it.
- `measured_zeros` are sign changes of a function sampled at 401 points and refined by 40 bisection
  steps, not distinct analytic roots. Near a shallow crossing two of them can be one root.
- Residuals, ratios, slopes and zero locations are conditioning-limited. The artifact does not name
  them field by field — three CI rounds each went red on a field a hand-written list had missed — it
  declares three *families* (`rays`, `columns`, `headline.fits`) under
  `reproduction_policy.conditioning_limited`, and the reproduction test compares everything inside a
  declared family for shape rather than value. Floats outside those families, and every count and
  label inside `columns`, are still compared by value.
- One *verdict* is in the same case as those floats: which rays turn their ratio back up at the floor
  is decided by comparing two values at the floor. `reproduction_policy.noise_decided_verdicts`
  declares the families where a verdict is advisory too, and the guard test plants it as a perturbation
  that must be tolerated, beside the plants that must still be caught.
- Nothing here changes what `run_scenario` ships.

## 8. Reproducing

```bash
uv run python experiments/fourth_order_crossing_map/run.py
uv run python scripts/run_benchmark_suite.py --only fourth_order_crossing_map
uv run pytest -q tests/python/test_fourth_order_crossing_map.py
```

The test file re-adds the coefficient sums strike by strike, re-derives three of the four partials as
finite differences of the partials one order below, re-finds the priced zeros against the engine,
re-fits both residual slopes from the artifact's own per-scale rows, checks the log-log helper against
synthetic `x^4`, `x^5` and constant series, and re-measures every figure quoted above.
