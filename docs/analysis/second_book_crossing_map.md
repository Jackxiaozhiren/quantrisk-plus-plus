# The crossing radius on five books — does order four travel?

Date: 2026-10-03. Repository state: `quantrisk` 1.6.0 released (`v1.6.0`, tag `b4e4bea`), Phase 17
landed after it. Evidence: `experiments/second_book_crossing_map/`, suite member 17, validation
matrix row 20, limitation #81, `docs/integrity_audit.md` Phase 18 addendum.

## 1. The question v1.6.0 could not answer

`experiments/fourth_order_crossing_map/` measured one book -- v1.5.0's ladder: spot 100, three calls
at 90/100/110, `sigma = 0.20`, `T = 0.5` -- and reported that adding the four mixed fourth partials
widens the radius over which the truncation predicts where the stress map's error crosses zero, from
`|delta| <= 0.05` to `|delta| <= 0.15`. Its own limitations said the radius belongs to that book's
fourth-order terms. Saying it and knowing it are different acts, and the difference is cheap to
close now that the order-four partials are in the core: the same procedure on a different book is a
few lines of arithmetic, not a new theory.

Five books are measured. Four are new and were chosen for what they do to the terms, before any of
them was run:

| book | `v = sigma sqrt(T)` | why it is in the set |
|---|---|---|
| published ladder | 0.141 | the control; its radii must come out at v1.5.0's and v1.6.0's numbers |
| long-dated wide | 0.495 | the order-four spot piece is the smallest fraction of the order-three one, so it was built to be the book where an added order has least to remove -- §3 is what came of that |
| short-dated tight | 0.047 | every spot partial divides by `v^3`, so the higher orders are the *largest* terms: this is where a widening bought by smallness would die |
| deep out of the money | 0.318 | every strike far above spot, so the book's partials come from one tail instead of straddling the money |
| in the money | 0.141 | the mirror ladder at the published vol and maturity: convexity on the other side of spot |

## 2. The radius, on each of them

A radius here is v1.5.0's own quantity: the widest `|delta|` such that *every* column with a priced
crossing up to it has its nearest predicted zero within 0.005 volatility points, contiguous outward
from the smallest magnitude, where a magnitude counts as one candidate and both of its signed columns
must pass. The grid is the twelve `delta` columns v1.5.0 and v1.6.0 swept, so a radius is always one
of those labels and never an interpolated crossing.

| book | cubic radius | quartic radius | widening | worst distance inside the cubic radius, cubic then quartic |
|---|---|---|---|---|
| published ladder | 0.05 | 0.15 | ×3.0 | 0.00243 then 1.15e-05 |
| long-dated wide | 0.10 | 0.30 | ×3.0 | 0.00206 then 3.28e-05 |
| short-dated tight | 0.02 | 0.05 | ×2.5 | 0.00273 then 3.28e-05 |
| deep out of the money | 0.15 | 0.20 | ×1.3 | 0.00273 then 0.000213 |
| in the money | 0.05 | 0.10 | ×2.0 | 0.000536 then 2.45e-05 |

Two readings, and the second is the one that changes a published sentence.

**The direction transfers.** On 5 of 5 books the quartic's radius is at least the cubic's, and on 5
of 5 its worst distance inside the cubic's *own* radius is the smaller. Nothing here is fitted to the
priced error: both truncations are closed forms on each book's own partial sums, so a book where the
extra order hurt would have been a result rather than a parameter.

**The magnitude does not.** The published 3.0 is the *widest* factor in the set, matched by the
long-dated book and followed by 2.5, 2.0 and 1.3; the other four land between 1.3x and 3.0x. The
absolute radii span 0.02 to 0.15 for the cubic and 0.05 to 0.30 for the quartic. `0.05 -> 0.15` is
therefore this ladder's pair of numbers, not the model's, and any document that quotes it as a
general widening is quoting one book.

The columns are not symmetric, and that is where the radius is actually decided. On the long-dated
book the `+0.15` column's cubic error puts its nearest predicted zero at 0.02347 -- four times the
tolerance -- while its `-0.15` partner sits at 0.00022. The cubic therefore stops at 0.10, and the
quartic, which brings that same column to 0.00107, carries the radius to the swept edge. A radius is
a statement about the worst column in the range, and the worst column has a sign.

## 3. The ratio this set was built around, and what it turned out not to explain

The mechanism column of the artifact is the ratio at `|delta| = 0.15` of the order-four spot piece to
the order-three one, `(1/24 V_SSSS h^4) / (1/6 V_SSS h^3)`. It runs from 0.015 on the long-dated book
to 3.887 on the short-dated one -- a factor of 254 across five books -- and the published ladder sits
at 0.563.

The set was chosen to span that ratio on an expectation: a small fourth-order piece means an added
order has little left to remove, so the widening should shrink with the ratio. The measurement
refuses the expectation. Sorted by ratio, the five widening factors come out
`0.015 -> 3.0`, `0.224 -> 2.0`, `0.563 -> 3.0`, `0.931 -> 1.3`, `3.887 -> 2.5`. The book built to have
least to gain tied the published ladder for the largest gain, and the book whose fourth-order piece is
3.9 times the term before it -- where the expansion is not descending at that move at all -- still
widened from 0.02 to 0.05. The smallest factor belongs to a book in the middle of the range.

So the general statement is not "order four triples the radius", and it is not a mechanism either. It
is: order four widens the radius on every book measured, and the size of the order-four spot piece is
not what says how far. Five books is too few to replace the rejected ratio with a better column, so
this file does not offer one; the artifact publishes the ratio and the per-column distances so a sixth
book can be checked against them rather than retold.

## 4. Two wrong definitions, and what the shipped machinery was checked against

Three things a reader should not have to take on trust are executed instead.

**The radius definition, first pass.** The first version asked only whether *some* column at a given
`|delta|` passed. On the in-the-money book that produced a headline in which order four *shrank* the
radius, 0.15 to 0.10 -- and it was an artefact of the loose rule, because the cubic had already failed
one column at 0.10 by 5.97e-3. A radius that tolerates a hole inside it is not the quantity v1.5.0
gated. Both superseded radii are recomputable from the published columns, and are: that book's twelve
rows show `-0.10` at 5.97e-3 and `+0.10` at 1.37e-3, so "some column passes" reaches 0.15 and the
contiguous rule stops at 0.05.

**The radius definition, second pass.** Contiguity was not enough, because a magnitude is signed
twice. Reading the columns one at a time let whichever sign came first set the radius, and on the
long-dated book the `-0.15` column passed at 0.00022 while its `+0.15` partner sat at 0.0235, nearly
five times the tolerance. The book published a cubic radius of 0.15, and a "worst distance inside that
same radius" of 0.0235: an artifact holding a radius and the evidence against it in the same block. That
self-contradiction is what surfaced the bug, when the note's figure test asked for a number the
artifact no longer carried. Two defences are now in place: the run refuses to publish a radius whose
widest in-range distance exceeds the tolerance, and the re-derivation test groups by magnitude and
plants this exact asymmetry in both column orders.

**The re-implementation.** This file's experiment cannot import the book -- the two shipped
experiments keep theirs in module constants -- so it re-derives the truncations from the core's closed
forms and re-runs `run_scenario`. That is only sound if the re-derivation *is* the shipped machinery
where both are defined, so the run refuses to publish unless all ten book coefficients, both
truncations and the engine P&L over 30 joint moves are bit-identical to v1.5.0's and v1.6.0's on the
published book, and unless its two radii come back at exactly 0.05 and 0.15. The artifact carries the
largest differences as `control`, and all four are exactly 0.

## 5. Where this stops being useful

- Five books are five points in a seven-parameter space. Nothing here estimates the probability that a
  new book widens, and no book was sampled at random.
- Radii are grid labels. A radius of 0.15 says nothing about 0.11, and one of the five books -- the
  long-dated one -- has its quartic radius on the swept edge at 0.30, where "no column failed" is
  weaker than a radius found inside the range. It is flagged in the artifact rather than rounded down.
- A radius is decided by the worst column in its range, and a column needs a priced crossing to count.
  The short-dated book has six of its twelve columns with one -- the minimum in the set -- so its 0.02
  is read off three magnitudes, and a book with fewer would have been refused rather than reported.
- Nothing here is about the *amount* of the map's error. On the published book order four still leaves
  it 16.2 % wrong at published size (`docs/limitations.md` #79), and a wider place to be wrong is not
  a smaller error.
- A zero is a sign change of a function scanned at 2001 points and refined by 40 bisections, the same
  routine v1.5.0 uses; near a shallow crossing two of them can be one root.
- Distances are roots of subtracting book values near 1.09e5, so they reproduce to their conditioning
  and the artifact's `reproduction_policy` declares them under `fits`. Radii are not distances -- they
  are grid labels chosen by comparisons against a fixed tolerance -- so they stay compared by value.

## 6. Reproducing

```bash
uv run python experiments/second_book_crossing_map/run.py
uv run pytest tests/python/test_second_book_crossing_map.py
```

The run takes about a minute: five books, twelve columns each, and every column's priced error
revalued through the shipped stress engine at 401 points. It raises rather than publishing a radius
whose book has fewer than three columns with a priced crossing, or whose machinery drifted from the
shipped one.
