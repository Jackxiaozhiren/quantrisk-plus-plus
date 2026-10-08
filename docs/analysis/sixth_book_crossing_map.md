# Does the order-five radius statement survive a sixth book chosen by the published rule?

Short answer: the book is found, the scan is published, and the sixth book says nothing about the
radius — because the parameter set the rule reached has its quartic radius pinned at the grid edge, so
a widening is not expressible on the swept grid. What it does say is narrower and worth keeping: the
quintic truncation is closer to the revalued book than the quartic inside that radius
($3.889 \times 10^{-4}$ against $4.613 \times 10^{-4}$), so the arithmetic improved while the grid
label could not move.

Artifact: `experiments/sixth_book_crossing_map/results/sixth_book_crossing_map.json`. Run:
`uv run python experiments/sixth_book_crossing_map/run.py`. Owned by
`tests/python/test_sixth_book_crossing_map.py`.

## 1. Why a sixth book is allowed, and how it was picked

`docs/analysis/fifth_order_crossing_map.md` §3 ends with the licence this file uses: the
order-five-to-four piece ratio is published *per book*, "so a sixth book can be checked against it
rather than retold". The five prior books span 0.0569 to 0.5876, and the two low-ratio books disagree
with each other — 0.0569 widened by 1.500, 0.0603 not at all — so the informative direction is below
the published minimum, not inside it.

The rule was written before any radius on a new book was read, and it is mechanical:

- candidates are maturity $\in \{0.25, 0.5, 1.0, 3.0\}$ years $\times$ volatility $\in \{0.15, 0.25,
  0.45\}$ $\times$ dividend yield $\in \{0.0, 0.05\}$ at spot 100.0, rate 0.03, strikes (80.0, 100.0,
  120.0) and quantity 5000.0 — 24 sets, of which 23 remain after removing the one set a published book
  already uses;
- each candidate's order-five-to-four ratio is computed at the same measure column the prior note
  quotes ($0.15 S$, $k = 0$), which is six closed forms and a price — deliberately the cheapest
  quantity available, because a rule that can see the outcome would be selecting on the outcome;
- candidates are examined in ascending ratio order, ties by iteration order, and the first whose radius
  is *defined* — at least three of its swept columns carry a priced crossing, the precondition
  `experiments/second_book_crossing_map/run.py` enforces — becomes the sixth book.

The first candidate examined won: `candidate T=3y sig=0.45 q=0.05`, ratio 0.0024, with 12 of 12 columns
carrying a priced crossing. Two lists are published so that sentence can be checked rather than taken:
`candidate_scan` is the prefix the rule actually priced — one row, so nothing was rejected on the way —
and `candidate_ranking` is all 23 candidates with the ratio the rule sorted them by, which the rule
computes for every candidate in order to sort at all. Without the second list a one-row scan would show
only that the winner was first among the rows displayed, and the claim that it is the grid's
lowest-ratio corner rather than a point picked after the fact would be resting on the reader's trust.
`test_the_selection_rule_is_the_order_the_scan_prints` re-derives that ranking from the module's own
`ratio_of` and refuses a published order the rule does not produce.

## 2. The six books

`v` is the measure the prior chain uses to compare books' curvature; for the sixth it is 0.7794, above
the range the five prior books occupy (0.0474 to 0.495), which is the mechanical consequence of asking
for a low ratio: three-year maturity at 45 % volatility with a 5 % dividend.

| book | radii cubic → quartic → quintic | quintic widening | at grid edge | order-five-over-four |
|---|---|---|---|---|
| published ladder | 0.05 → 0.15 → 0.2 | 1.333 | no | 0.2798 |
| long-dated wide | 0.1 → 0.3 → 0.3 | 1.000 | **yes** | 0.5876 |
| short-dated tight | 0.02 → 0.05 → 0.05 | 1.000 | no | 0.1429 |
| deep out of the money | 0.15 → 0.2 → 0.3 | 1.500 | **yes** | 0.0569 |
| in the money | 0.05 → 0.1 → 0.1 | 1.000 | no | 0.0603 |
| candidate T=3y sig=0.45 q=0.05 | 0.2 → 0.3 → 0.3 | 1.000 | **yes** | 0.0024 |

Two of six widen at order five, four are unchanged, none thin, and three sit at the grid edge — the last
figure is the one this book added. Across six books the ratio axis now spans 0.0024 to 0.5876, some
240-fold, and **both ends of that span are grid-edge cases**: the largest ratio (0.5876) and the smallest
(0.0024) are books whose quartic radius is already 0.3, the widest swept move. A radius that cannot grow
is not evidence that the expansion stopped improving; it is a statement about the grid.

## 3. What the sixth book does carry

Inside the quartic radius of 0.3, and inside each order's own radius, the worst column distance is

| order | own radius | worst inside its own radius | worst inside the quartic radius |
|---|---|---|---|
| cubic | 0.2 | 0.001949 | 0.014022 |
| quartic | 0.3 | 0.000461 | 0.000461 |
| quintic | 0.3 | 0.000389 | 0.000389 |

so on this book the quintic is closer than the quartic by 16 % of the quartic's own worst column, while
the cubic keeps its claim inside its own 0.2 (0.001949 against the `5 \times 10^{-3}` tolerance the chain
uses) and is 2.8 times that tolerance at the 0.3 column the quartic does claim -- which is why the cubic
radius stops where it does. That is the arithmetic; the label cannot follow the quintic because 0.3 is
the edge. Had the grid swept to 0.4, this book could have reported a widening, and the run would then
have been a different experiment: every radius in this chain is defined relative to the swept ladder the
published values were produced on.

## 4. What is not claimed

- No bound. A radius is a grid label (`docs/limitations.md` #81), and on three of six books it is a
  label pinned at the boundary of the sweep.
- No family. Six books chosen by two rules (Phase 18's curvature span, this phase's ratio minimum) is
  still a scatter; nothing here is estimated across books.
- No statement that the ratio orders the outcome. The three lowest-ratio books now read 0.0024 → 1.000,
  0.0569 → 1.500, 0.0603 → 1.000: the smallest ratio produced no widening and the middle one the
  largest. If the ratio were a mechanism, one of these three would be wrong.
- No re-tuning. The candidate grid was fixed before the scan; the fact that the winner was the first
  examined is a property of the grid, not a search that stopped early — a rejected candidate would have
  been published in the same table with its reason.

## 5. Limits inherited from the design

The selection axis is one-dimensional. It cannot distinguish a book that is at the grid edge from one
that is not, which is exactly the failure this run surfaced: the rule optimised for the *lowest* ratio
and found, at that corner, a book whose radius is uninformative. The honest fix is a wider move ladder
(a different experiment, because it changes the scale every published radius is quoted on) or a rule
that requires a non-edge radius as a precondition — the latter would have to be registered before
measuring, not after, and it would stop being the ratio minimum.

`experiments/fifth_order_crossing_map/results/fifth_order_crossing_map.json` remains the published
five-book record; this artifact reproduces its radii digit for digit and is checked doing so
(`test_the_five_prior_books_return_the_radii_phase_20_published`).
