"""Does the order-five-to-four radius statement survive a sixth book chosen by a published rule?

Phase 20 measured the cubic -> quartic -> quintic crossing radii on five books and published, per
book, the ratio of the order-five spot piece to the order-four one at the same measure column. Its
note ends with why a sixth book is allowed at all: "the ratio is published per book so a sixth
book can be checked against it rather than retold" (`docs/analysis/fifth_order_crossing_map.md` §3).
The published span is 0.057 to 0.588, and the two outcomes that disagree with the refuted mechanism
sit at the low end: the smallest ratio produced the largest quintic widening (1.50) and the second
smallest produced none. So the informative direction is *below* the published minimum, and this file
goes there.

The book is chosen before its radius is looked at, and the rule is mechanical:

* candidates are the Cartesian product of maturities ``(0.25, 0.5, 1.0, 3.0)``, volatilities
  ``(0.15, 0.25, 0.45)`` and dividend yields ``(0.0, 0.05)`` at spot 100.0, rate 0.03, strikes
  ``(80.0, 100.0, 120.0)`` and quantity 5000.0 -- 24 sets, any set equal to one of the five
  five published books removed;
* each candidate's order-five-to-four ratio is computed at Phase 20's own measure column;
* candidates are examined in ascending ratio order, ties broken by the iteration order, and the
  first candidate whose radius is *defined* -- at least ``MIN_COLUMNS`` columns carry a priced
  crossing, the same precondition Phase 20's `check` enforces -- becomes the sixth book;
* every candidate examined is published in the artifact, including the rejected ones and the reason
  each was rejected, and so is the full ranking of all 23 candidates by the ratio the rule sorted
  on, because a scan that stops at its first acceptance cannot otherwise be shown to have been
  first: the scan is the prefix priced, the ranking is the order the rule saw.

Nothing here selects a book by its widening factor: the ratio is a property of the truncation's
coefficients, not of the crossing map's outcome.

What is reused rather than re-typed, and why that is the point:

* the books, the grid, the tolerance, the root finder, the radius rule, the piece arithmetic, the
  quintic error and the column sweep all come from `experiments/fifth_order_crossing_map/run.py`,
  which itself loads `experiments/second_book_crossing_map/run.py`, which loads v1.5.0's and
  v1.6.0's files. Calling `measure` on six books is what makes "the same radius, one more book" a
  statement about the same quantity;
* the five published books' radii must come back bit-identical to the values
  `experiments/fifth_order_crossing_map/results/fifth_order_crossing_map.json` already carries, so a
  sixth book cannot quietly move the five it is compared against;
* Phase 20's control is run on the published book, not imitated: `verify_control` requires this
  machinery's coefficients and engine P&L to equal v1.5.0's and v1.6.0's bit for bit.

What is not claimed: that a radius bounds anything (limitation #81: a grid label); that one
more book makes a family (six books with one new ratio is still a scatter, and the widening rule
publishes per book); that the scan explored the space (it explores one axis, chosen because
that axis is where Phase 20's two contradictory outcomes sat).
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import pathlib
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "python"))


def _load(relative: str, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Phase 20 owns the books, the measure column, the piece arithmetic, the sweep and the radius rule.
P20 = _load("experiments/fifth_order_crossing_map/run.py", "quantrisk_fifth_order_for_sixth_book")
P18 = P20.P18

PUBLISHED_BOOKS = P20.BOOKS
MIN_COLUMNS = P18.MIN_COLUMNS_WITH_A_CROSSING
TOLERANCE = P18.TOLERANCE
ORDERS = P20.ORDERS
MEASURE_COLUMN = P20.MEASURE_COLUMN
RESULTS = REPO_ROOT / "experiments" / "sixth_book_crossing_map" / "results"
FIFTH_ORDER_ARTIFACT = (
    REPO_ROOT
    / "experiments"
    / "fifth_order_crossing_map"
    / "results"
    / "fifth_order_crossing_map.json"
)

CANDIDATE_MATURITIES = (0.25, 0.5, 1.0, 3.0)
CANDIDATE_VOLATILITIES = (0.15, 0.25, 0.45)
CANDIDATE_DIVIDENDS = (0.0, 0.05)
CANDIDATE_SPOT = 100.0
CANDIDATE_RATE = 0.03
CANDIDATE_STRIKES = (80.0, 100.0, 120.0)
CANDIDATE_QUANTITY = 5000.0


def candidates() -> list[Any]:
    """The pre-registered grid, minus any set the published books already use.

    Order is the iteration order the tie-break uses: maturity outer, volatility, dividend inner.
    """
    taken = {(book.maturity, book.volatility, book.dividend_yield) for book in PUBLISHED_BOOKS}
    out = []
    for maturity in CANDIDATE_MATURITIES:
        for volatility in CANDIDATE_VOLATILITIES:
            for dividend in CANDIDATE_DIVIDENDS:
                if (maturity, volatility, dividend) in taken:
                    continue
                out.append(
                    P18.Book(
                        label=(f"candidate T={maturity:g}y sig={volatility:g} q={dividend:g}"),
                        why="selected by the lowest order-five-to-four ratio among candidates "
                        "whose radius is defined",
                        spot=CANDIDATE_SPOT,
                        rate=CANDIDATE_RATE,
                        dividend_yield=dividend,
                        volatility=volatility,
                        maturity=maturity,
                        strikes=CANDIDATE_STRIKES,
                        quantity=CANDIDATE_QUANTITY,
                    )
                )
    return out


def ratio_of(book: Any) -> float:
    """The order-five-to-four piece ratio at Phase 20's measure column, and nothing else.

    Deliberately the cheapest quantity available for the rule: six closed forms and a price, with no
    root finding. Choosing on this cannot see the outcome it is meant to be checked against.
    """
    sums = P20.fifth_order_sums(book)
    fourth = abs(book.quartic_piece(MEASURE_COLUMN, 0.0))
    fifth = abs(P20.quintic_piece(book, sums, MEASURE_COLUMN, 0.0))
    assert fourth > 0.0, f"{book.label}: no order-four piece to divide by"
    return fifth / fourth


def scan() -> tuple[Any, list[dict[str, Any]], list[dict[str, Any]]]:
    """Examine candidates in ascending ratio order until one carries a defined radius.

    Two lists come back. The ranking is *every* candidate with the ratio the rule sorted it by --
    the rule computes all of them to sort, so publishing them costs nothing and is the only way a
    reader can see that the winner was first rather than merely first among the rows shown. The
    scan is the prefix the rule actually priced, and it stops at the acceptance because stopping
    there is the pre-registered rule.
    """
    measured = [(index, book, ratio_of(book)) for index, book in enumerate(candidates())]
    measured.sort(key=lambda row: (row[2], row[0]))
    ranking = [
        {
            "rank": rank,
            "label": book.label,
            "maturity_years": book.maturity,
            "volatility": book.volatility,
            "dividend_yield": book.dividend_yield,
            "order_five_over_four_at_measure_column": ratio,
        }
        for rank, (_, book, ratio) in enumerate(measured)
    ]
    examined: list[dict[str, Any]] = []
    for _, book, ratio in measured:
        verdicts, _fits = P20.measure(book)
        columns = verdicts["columns_with_a_priced_crossing"]
        accepted = columns >= MIN_COLUMNS
        examined.append(
            {
                "label": book.label,
                "maturity_years": book.maturity,
                "volatility": book.volatility,
                "dividend_yield": book.dividend_yield,
                "order_five_over_four_at_measure_column": ratio,
                "columns_with_a_priced_crossing": columns,
                "columns_swept": verdicts["columns_swept"],
                "accepted": accepted,
                "rejected_because": (
                    None
                    if accepted
                    else f"fewer than {MIN_COLUMNS} columns carry a priced crossing"
                ),
            }
        )
        if accepted:
            return book, examined, ranking
    raise RuntimeError("no candidate carries a defined radius; the grid needs widening")


def control_against_published(sixth: Any, measured: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """The five published books must return their published radii, bit for bit."""
    artifact = json.loads(FIFTH_ORDER_ARTIFACT.read_text(encoding="utf-8"))
    published = {row["label"]: row for row in artifact["books"]}
    mismatches = []
    for label, row in published.items():
        mine = measured[label]
        for order in ORDERS:
            key = f"radius_{order}"
            if mine[key] != row[key]:
                mismatches.append(f"{label} {key}: {mine[key]} versus published {row[key]}")
    assert not mismatches, "adding a sixth book moved a published radius: " + "; ".join(mismatches)
    return {
        "control": "experiments/fifth_order_crossing_map/run.py::P18.verify_control",
        "control_ran_on": PUBLISHED_BOOKS[0].label,
        "published_books_reproduced_bit_for_bit": len(published),
        "published_artifact": str(FIFTH_ORDER_ARTIFACT.relative_to(REPO_ROOT)),
        "radii_from_that_artifact": {
            label: {order: row[f"radius_{order}"] for order in ORDERS}
            for label, row in published.items()
        },
        "sixth_book": sixth.label,
    }


def build_payload() -> dict[str, Any]:
    P18.verify_control(PUBLISHED_BOOKS[0])
    sixth, examined, ranking = scan()
    books = PUBLISHED_BOOKS + (sixth,)

    measured: dict[str, dict[str, Any]] = {}
    fits: dict[str, dict[str, Any]] = {}
    for book in books:
        verdicts, own_fits = P20.measure(book)
        P20.check(verdicts, own_fits)
        measured[book.label] = verdicts
        fits[book.label] = own_fits
        print(f"  {book.label}: radii {[verdicts[f'radius_{o}'] for o in ORDERS]}")

    rows = [measured[book.label] for book in books]
    widening = [row for row in rows if row["widening_factor_quintic"] is not None]
    widened = [row for row in widening if row["radius_quintic"] > row["radius_quartic"]]
    unchanged = [row for row in widening if row["radius_quintic"] == row["radius_quartic"]]
    thinner = [row for row in widening if row["radius_quintic"] < row["radius_quartic"]]
    edge = [row for row in rows if row["quintic_radius_at_grid_edge"]]
    ratios = {
        row["label"]: fits[row["label"]]["order_five_over_four_at_measure_column"] for row in rows
    }
    ordered = sorted(value for value in ratios.values() if value is not None)
    # The span Phase 20 printed belongs to the five books that were published before this one
    # existed. Taking the span over all six would make the new book its own minimum, and the
    # "is this a new low" statement would answer False by construction -- a derived field that
    # cannot be true is not a guard.
    prior = sorted(
        value for label, value in ratios.items() if label != sixth.label and value is not None
    )
    sixth_ratio = ratios[sixth.label]
    sixth_at_edge = measured[sixth.label]["quintic_radius_at_grid_edge"]

    return {
        "schema": "quantrisk.sixth_book_crossing_map.v1",
        "claim": (
            "the contiguous paired-magnitude crossing radius of the cubic, quartic and quintic "
            "column-error truncations on six books, the sixth chosen by the published "
            "order-five-to-four ratio rule before its radius was read"
        ),
        "command": "uv run python experiments/sixth_book_crossing_map/run.py",
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "environment": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "packages": {"quantrisk": P20.quantrisk.version()},
        },
        "reproduction_policy": {
            # Families, not field names, per Phase 16. The candidate ratios are quotients of
            # pieces obtained by subtracting book values, and the scan's acceptance test reads one
            # of them, so those floats reproduce to their conditioning. Everything that decides a
            # radius -- zero counts, tolerance verdicts, radii, the widened/unchanged/thinned counts
            # and the grid-edge flags -- stays gated by value, because a radius is a grid point.
            "conditioning_limited": [
                "fits",
                "candidate_scan",
                "candidate_ranking",
                "headline.sixth_book_ratio",
                "headline.published_ratio_span_of_the_five_prior_books",
                "headline.ratio_span_over_six_books",
                "headline.sixth_book_ratio_over_the_published_minimum",
            ],
            "why": (
                "the order-five-to-four ratios, and the new-low statement derived from the span of "
                "those ratios come from subtractions of book values near 1e5, so they reproduce to "
                "their conditioning rather than to their last digit; the comparator exempts floats "
                "only, and a radius is a grid point"
            ),
            "everything_else": (
                "the truncations are closed forms on each book's sums, the priced error and the "
                "engine P&L are exact arithmetic on the shipped engine, the published radii are "
                "pinned to Phase 20's artifact bit for bit, and the published book is pinned to "
                "v1.5.0's and v1.6.0's values by those releases' own equality gate"
            ),
        },
        "procedure": {
            "selection_rule": (
                "candidates = maturity x volatility x dividend at fixed spot, rate, strikes and "
                "quantity, minus sets the published books already use; examined in ascending "
                "order-five-to-four ratio at the measure column, ties by iteration order; accepted "
                f"at the first candidate with at least {MIN_COLUMNS} priced-crossing columns"
            ),
            "candidate_grid": {
                "maturities_years": list(CANDIDATE_MATURITIES),
                "volatilities": list(CANDIDATE_VOLATILITIES),
                "dividend_yields": list(CANDIDATE_DIVIDENDS),
                "spot": CANDIDATE_SPOT,
                "rate": CANDIDATE_RATE,
                "strikes": list(CANDIDATE_STRIKES),
                "quantity": CANDIDATE_QUANTITY,
                "candidates_after_removing_published_sets": len(candidates()),
            },
            "measure_column_share_of_spot": MEASURE_COLUMN,
            "tolerance": TOLERANCE,
            "grid_edge": P18.GRID_EDGE,
            "radius_rule": "contiguous paired-magnitude rule, Phase 18's implementation",
            "orders": list(ORDERS),
            "reused_from": [
                "experiments/fifth_order_crossing_map/run.py",
                "experiments/second_book_crossing_map/run.py",
            ],
        },
        "headline": {
            "books_measured": len(rows),
            "books_widening_at_order_five": len(widened),
            "books_unchanged_at_order_five": len(unchanged),
            "books_thinning_at_order_five": len(thinner),
            "books_at_grid_edge": len(edge),
            "sixth_book": sixth.label,
            "sixth_book_ratio": sixth_ratio,
            "published_ratio_span_of_the_five_prior_books": (
                [prior[0], prior[-1]] if prior else None
            ),
            "ratio_span_over_six_books": [ordered[0], ordered[-1]] if ordered else None,
            "sixth_book_is_new_low_of_the_published_span": bool(prior and sixth_ratio < prior[0]),
            "sixth_book_ratio_over_the_published_minimum": (
                sixth_ratio / prior[0] if prior else None
            ),
            # A quartic radius already at the grid edge means the quintic cannot show a widening
            # even if the true radius kept growing, so the verdict is read with these two flags.
            "sixth_book_quintic_radius_at_grid_edge": sixth_at_edge,
            "sixth_book_radius_verdict_is_grid_bounded": bool(
                sixth_at_edge and measured[sixth.label]["radius_quartic"] == P18.GRID_EDGE
            ),
            "sixth_book_radii": {
                order: measured[sixth.label][f"radius_{order}"] for order in ORDERS
            },
            "sixth_book_widening_factor_quintic": measured[sixth.label]["widening_factor_quintic"],
            "columns_with_a_priced_crossing_total": sum(
                row["columns_with_a_priced_crossing"] for row in rows
            ),
        },
        "controls": control_against_published(sixth, measured),
        "candidate_scan": examined,
        "candidate_ranking": ranking,
        "books": rows,
        "fits": fits,
    }


def main() -> int:
    print("sixth book at the order-five-to-four radius")
    payload = build_payload()
    head = payload["headline"]
    span = head["published_ratio_span_of_the_five_prior_books"]
    print(
        f"  sixth book {head['sixth_book']}: ratio {head['sixth_book_ratio']:.4f} against the "
        f"published span {span[0]:.4f} to {span[1]:.4f} "
        f"({head['sixth_book_ratio_over_the_published_minimum']:.3f} of the published minimum)"
    )
    print(
        f"  new low of the published span: {head['sixth_book_is_new_low_of_the_published_span']}; "
        f"quintic radius at grid edge: {head['sixth_book_quintic_radius_at_grid_edge']}; verdict "
        f"grid bounded: {head['sixth_book_radius_verdict_is_grid_bounded']}"
    )
    print(
        f"  radii {head['sixth_book_radii']}, widening factor "
        f"{head['sixth_book_widening_factor_quintic']}"
    )
    print(
        f"  across {head['books_measured']} books: widened {head['books_widening_at_order_five']}, "
        f"unchanged {head['books_unchanged_at_order_five']}, "
        f"thinned {head['books_thinning_at_order_five']}, "
        f"grid edge {head['books_at_grid_edge']}"
    )
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / "sixth_book_crossing_map.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
