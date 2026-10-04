# Does the crossing radius widen again at order five? Two of five books say yes

v1.6.0 published a cubic-to-quartic crossing radius of `0.05 -> 0.15` on the reference ladder, and
Phase 18 measured that widening on five books instead of one: the direction held on all five, the
magnitude on none, and the mechanism the set had been built to test -- a small fourth-order piece
leaving an added order little to remove -- was refuted by the measurement. What the chain had not
answered is the next question, because the core could not express the terms it needs: does the radius
widen *again* when the order-five terms are added, or had the truncation already stopped buying
anything the map's own error can see?

Phase 20 shipped `pricing.black_scholes_mixed_fifth_derivatives`, and
`experiments/fifth_order_crossing_map/run.py` asks the question with it.

Reproduce:

```bash
uv run python experiments/fifth_order_crossing_map/run.py
```

## 1. The same rule, the same books, one more order

Nothing in the radius definition changed between this note and the five-book note: the same contiguous
rule at the same `0.005` tolerance on the same delta grid, where a `|delta|` magnitude passes only if
**every** signed column at it that has a priced crossing has the truncation's nearest zero inside the
tolerance, and the radius is the widest magnitude such that all smaller ones pass. The books, the grid,
the tolerance, the root finder and the rule are imported from the Phase 18 experiment, which itself
loads v1.5.0's and v1.6.0's files; this run adds one term to the truncation and changes nothing else.
That import is what makes "the radius at order five" a statement about the same quantity, and it comes
with the shipped equality gate: the re-derived cubic and quartic coefficients, both truncations and the
engine P&L over 30 joint moves are required to be *bit-identical* to the two releases', and the run
refuses to publish otherwise. The published ladder's cubic and quartic radii must also come back at
0.05 and 0.15.

| book | `v = sigma sqrt(T)` | cubic | quartic | quintic | quartic/cubic | quintic/quartic | columns with a crossing |
|---|---|---|---|---|---|---|---|
| published ladder | 0.141 | 0.05 | 0.15 | 0.20 | 3.00 | 1.33 | 10 |
| long-dated wide | 0.495 | 0.10 | 0.30 | 0.30 | 3.00 | 1.00 | 11 |
| short-dated tight | 0.047 | 0.02 | 0.05 | 0.05 | 2.50 | 1.00 | 6 |
| deep out of the money | 0.318 | 0.15 | 0.20 | 0.30 | 1.33 | 1.50 | 12 |
| in the money | 0.141 | 0.05 | 0.10 | 0.10 | 2.00 | 1.00 | 9 |

Order five widens the radius on 2 of 5 books and leaves it unchanged on the other three, over 48
columns with a priced crossing out of 60 swept. On the published ladder it goes `0.15 -> 0.20`, a
factor of 1.33 where the cubic-to-quartic step on the same book was 3.00: the chain is still buying
something, less of it.

Two of the three "unchanged" results are not evidence of anything. The long-dated book reached the
swept grid edge at 0.30 already under the quartic, and the deep out-of-the-money ladder reaches it now;
at the edge, "no column failed" means "nothing in the range I swept failed", so a widening could not be
seen there even if it existed. The honest count is therefore: one book widened inside the swept range
(the published ladder), one widened into the edge (deep out of the money), and one book that is still
resolvable did not widen (the in-the-money mirror, `0.10 -> 0.10`). The short-dated book's radius is
small enough that its edge is far away, and it did not move either.

## 2. What the added order did to the distance, separately from the radius

A radius is a grid label; the nearest-zero distance beside it is the measurement. Inside the quartic's
own radius, on all five books, the quintic truncation is the closest of the three orders to the priced
crossing:

| book | cubic's worst distance inside the quartic radius | quartic's | quintic's |
|---|---|---|---|
| published ladder | 1.89e-02 | 1.62e-03 | 1.18e-03 |
| long-dated wide | 2.35e-02 | 1.07e-03 | 5.83e-04 |
| short-dated tight | 1.43e-02 | 5.67e-04 | 2.29e-04 |
| deep out of the money | 6.90e-03 | 8.82e-04 | 2.18e-04 |
| in the money | 5.97e-03 | 9.05e-04 | 6.71e-05 |

That is 5 of 5, and it is the same direction Phase 18 reported for the cubic-to-quartic step, one order
later. It is also the part of this result with the least cross-platform value: these are roots of a
subtraction of book values near 1e5, which is why they sit in the artifact's `conditioning_limited`
families and why the gate compares the *counts and radii* by value rather than the distances.

The other side of the same column is worth stating, because it is the opposite of a win: the published
ladder's quintic radius of 0.20 contains a column `3.81e-03` away, looser than the `1.62e-03` its 0.15
radius contained. A wider radius that still obeys the tolerance is not a tighter prediction; it is a
bigger region over which the prediction happens to be right about the *place* of the crossing, and the
worst place inside it is worse than before.

## 3. The mechanism that was refuted twice

The five books were chosen to span the ratio of the order-four spot piece to the order-three one, and
Phase 18 used that span to reject the expectation that a small added term leaves an added order little
to remove. The order-five-to-four ratio at the same measure column spans 0.057 to 0.588 here, and it
orders the outcome no better than its predecessor did:

- the smallest ratio in the set, 0.057 on the deep out-of-the-money ladder, produced the largest
  quintic widening, 1.50;
- the second smallest, 0.060 on the in-the-money mirror, produced none;
- the largest, 0.588 on the long-dated book, produced none -- but that book sits at the grid edge, so it
  proves nothing either way.

Two books, 1.50 against 1.00, from ratios that differ by five percent of each other. No mechanism is
offered in place of the one that failed, and five books is not a family: the ratio is published per book
so a sixth book can be checked against it rather than retold.

## 4. What the quintic term is, and how it was shown to be that

The truncation adds `(1/120)` times the fifth directional derivative along the joint move `(h, k)`:

```text
V_SSSSS h^5 + 5 V_SSSSsigma h^4 k + 10 V_SSSsigmasigma h^3 k^2
+ 10 V_SSsigmasigmasigma h^2 k^3 + 5 V_Ssigmasigmasigmasigma h k^4
+ V_sigmasigmasigmasigmasigma k^5
```

with `h` the absolute spot move and `k` the volatility move, the same convention as the published
cubic and quartic truncations, so the three orders compose without a rescaling step.

The multinomial weights `(1, 5, 10, 10, 5, 1)` and the `1/120` were not taken on trust from the closed
forms. Five nested five-point differences of the *revalued book* -- a route containing no partial of any
order -- reproduce the contraction on five rays, at worst `1e-05`, `8e-04`, `3e-06`, `5e-05` and `6e-04`
relative on the widest rung tried, against a `5e-2` band. Finer rungs degrade sharply (the same ray that
gives `1e-05` at scale 0.032 gives `3e-02` at 0.008) because nesting five divisions by the scale is
round-off dominated; the rung is therefore published per ray rather than chosen by a minimum, and the
independent test re-derives the identity on four rays this run never evaluates, so the published list
cannot be the reason the control passes.

## 5. A refusal that was wrong, and what it found

The run refuses to publish a radius whose widest in-range distance exceeds the tolerance that defines
it. The first version of that check read the distances from the *quartic's* range for every order, and
it rejected the published ladder's cubic radius of 0.05 because a column at 0.15 sat 1.89e-02 away -- a
column the cubic radius never claimed to cover. The refusal fired on a defect in the refusal, which is
the only way this class of bug announces itself: a gate that judges a quantity by a range other than its
own will reject correct results and accept incoherent ones. `check()` now reads each order against that
order's own radius, and `tests/python/test_fifth_order_crossing_map.py` pins both directions -- a loose
column outside the cubic radius must not reject it, and the same numbers with the loose column inside it
must.

## 6. What this note does not say

Nothing here changes the amount of the map's error. On the published book the base map is still 16.2 %
off at `risk_off` after the quartic, and the quintic is not evaluated against that figure: this is a
statement about where the column error crosses zero, not about how large it is. No independent library
prices a fifth-order column, so the chain remains self-consistency of one truncation measured against a
revaluation of the same book, and a radius is a grid label rather than a bound. `docs/limitations.md`
#82 carries the validation caveats for the closed forms themselves -- no oracle, five of six fields
anchored by stencils of this project's own fourth-order family -- and #81 carries the ones this
measurement inherits from the five-book design: the transfer is in direction, not in size, and the
edges are flagged rather than rounded down.
