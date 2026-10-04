"""Does the crossing radius widen *again* at order five, on five books?

v1.6.0 shipped a cubic-to-quartic radius of 0.05 -> 0.15 on the published ladder, and Phase 18
measured that widening on five books: the direction transferred to all five, the magnitude to none.
The next question is whether the chain keeps paying for an added order or has stopped meaning
anything, and that needs the order-five terms, which the core shipped in Phase 20.

This file asks one question and refuses to answer another. It measures the contiguous,
paired-magnitude crossing radius of the cubic, quartic and quintic truncations of the map's column
error on the same five books as Phase 18, and publishes whether the quintic radius exceeds the
quartic's. It does not measure residual slopes: Phase 18's five books had already refuted the
mechanism (a small order-four piece leaving little for an added order to remove), so a log-log slope
here would decorate a result the radius already states, and the arithmetic-floor caveat that governs
such fits belongs to the artifacts that carry them.

What is reused rather than re-typed, and why that is the point:

* the books, the grid, the tolerance, the root finder, the radius rule and the worst-distance helper
  all come from `experiments/second_book_crossing_map/run.py`, which itself loads v1.5.0's and
  v1.6.0's files;
* that file's own equality gate is run, not imitated: `verify_control` requires this machinery's
  cubic and quartic coefficients, truncations and engine P&L to be *bit-identical* to v1.5.0's and
  v1.6.0's on the published book over 30 joint moves;
* the published book's cubic and quartic radii must come back at v1.5.0's and v1.6.0's own numbers,
  so an added order cannot quietly shift the baseline it is compared against;
* the multinomial weights `(1, 5, 10, 10, 5, 1)` and the `1/120` are pinned against five nested
  differences of the *revalued book*, which contains no partial of any order.

What is not claimed: that a radius bounds anything (limitation #81 says it is a grid label); that
the quintic term is small (the short-dated book's order-four piece is 3.9x its order-three one,
which is exactly where no widening is found); nor that a book sitting at the swept grid edge has
been measured at all -- such books are flagged rather than counted as wins or losses.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import pathlib
import sys
from datetime import UTC, datetime
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "python"))


def _load(relative: str, name: str) -> Any:
    path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Phase 18 owns the books, the grid and the radius rule; it owns v1.5.0's and v1.6.0's truncations
# transitively. Loading it is what makes "the same radius, one order higher" a statement about the
# same
# quantity rather than about a new one.
P18 = _load("experiments/second_book_crossing_map/run.py", "quantrisk_second_book_for_fifth_order")

quantrisk = P18.quantrisk
BOOKS = P18.BOOKS
DELTAS = P18.DELTAS
TOLERANCE = P18.TOLERANCE
GRID_EDGE = P18.GRID_EDGE
MIN_COLUMNS = P18.MIN_COLUMNS_WITH_A_CROSSING
PUBLISHED_LABEL = "published ladder"

RESULTS = REPO_ROOT / "experiments" / "fifth_order_crossing_map" / "results"

FIFTH_FIELDS = (
    "spot_spot_spot_spot_spot",
    "spot_spot_spot_spot_sigma",
    "spot_spot_spot_sigma_sigma",
    "spot_spot_sigma_sigma_sigma",
    "spot_sigma_sigma_sigma_sigma",
    "sigma_sigma_sigma_sigma_sigma",
)
# The contraction of the five-directional derivative: the term order five adds to the Taylor
# polynomial
# is this sum divided by 5!, which is what the nested-difference control below pins.
MULTINOMIAL = (1.0, 5.0, 10.0, 10.0, 5.0, 1.0)

# The move at which the order-five-to-four piece ratio is quoted: v1.6.0's widened radius, so the
# number
# is taken at the displacement its own claim has to survive at.
MEASURE_COLUMN = 0.15

# The rays the multinomial contraction is checked on: two pure ends, which isolate the first and
# last
# coefficients alone, and three joint rays that only close with all six weights in place.
CONTRACTION_RAYS = ((0.05, 0.0), (0.0, 0.02), (0.12, -0.05), (-0.03, 0.08), (0.20, 0.15))
CONTRACTION_SCALES = (0.008, 0.016, 0.032)
CONTRACTION_BAND = 5.0e-2

ORDERS = ("cubic", "quartic", "quintic")


def fifth_order_sums(book: Any) -> dict[str, float]:
    """The six order-five book sums, read from the core on this book's base market."""
    market = book.market()
    partials = quantrisk.pricing.black_scholes_mixed_fifth_derivatives
    return {
        name: sum(float(getattr(partials(o, market), name)) for o in book.options()) * book.quantity
        for name in FIFTH_FIELDS
    }


def quintic_piece(book: Any, sums: dict[str, float], delta: float, k: float) -> float:
    """`(1/120)` times the fifth directional derivative along the joint move `(h, k)`."""
    h = book.spot * delta
    return (
        sum(
            coefficient * sums[field] * h ** (5 - power) * k**power
            for coefficient, field, power in zip(MULTINOMIAL, FIFTH_FIELDS, range(6), strict=True)
        )
        / 120.0
    )


def quintic_error(book: Any, sums: dict[str, float], delta: float, k: float) -> float:
    return book.quartic_error(delta, k) + quintic_piece(book, sums, delta, k)


def nested_fifth(book: Any, delta: float, k: float, scale: float) -> float:
    """Five nested five-point differences of the revalued book along the ray `(delta, k)`.

    The operand is `book.exact_move`, a revaluation containing no partial of any order, so this is
    the check that the multinomial weights and the `1/120` are the ones the Taylor polynomial uses.
    Five nested divisions by the scale make it round-off dominated at small scales, so the rung is
    passed in rather than searched and the widest `CONTRACTION_SCALES` is the one published.
    """
    weights = (1.0 / 12.0, -2.0 / 3.0, 0.0, 2.0 / 3.0, -1.0 / 12.0)
    offsets = (-2.0, -1.0, 0.0, 1.0, 2.0)

    def point(t: float) -> float:
        return book.exact_move(t * delta, t * k)

    value = point
    for _ in range(5):
        previous = value

        def value(t: float, previous=previous) -> float:
            return (
                sum(
                    weight * previous(t + offset * scale)
                    for weight, offset in zip(weights, offsets, strict=True)
                )
                / scale
            )

    return value(0.0)


def check_contraction(book: Any, sums: dict[str, float]) -> dict[str, Any]:
    """Compare the quintic piece with the fifth directional derivative of the revaluation."""
    rows = []
    for delta, k in CONTRACTION_RAYS:
        closed = 120.0 * quintic_piece(book, sums, delta, k)
        errors = [
            abs(nested_fifth(book, delta, k, scale) - closed) / max(abs(closed), 1.0e-30)
            for scale in CONTRACTION_SCALES
        ]
        widest = errors[-1]
        if widest > CONTRACTION_BAND:
            raise RuntimeError(
                f"{book.label}: the quintic contraction is {widest:.3g} away from the fifth nested "
                f"difference of the revaluation at ray ({delta}, {k}), outside the "
                f"{CONTRACTION_BAND} band"
            )
        rows.append(
            {
                "delta": delta,
                "vol_move": k,
                "closed_form_fifth_directional_derivative": closed,
                "relative_error_widest_rung": widest,
                "relative_error_by_rung": {
                    str(scale): error
                    for scale, error in zip(CONTRACTION_SCALES, errors, strict=True)
                },
            }
        )
    return {"rays": rows, "band": CONTRACTION_BAND, "scales": list(CONTRACTION_SCALES)}


def column_row(
    book: Any, sums: dict[str, float], delta: float
) -> tuple[dict[str, Any], dict[str, Any]]:
    """One column at the three truncation orders, split the way the reproduction gate needs it."""
    measured = book.measured_zeros(delta)
    zeros = {
        "cubic": book.predicted_zeros(lambda k: book.cubic_error(delta, k)),
        "quartic": book.predicted_zeros(lambda k: book.quartic_error(delta, k)),
        "quintic": book.predicted_zeros(lambda k: quintic_error(book, sums, delta, k)),
    }
    distances = {
        order: min((abs(a - b) for a in zeros[order] for b in measured), default=None)
        for order in ORDERS
    }
    verdicts = {
        "delta": delta,
        "abs_delta": abs(delta),
        "measured_zero_count": len(measured),
        **{f"{order}_zero_count": len(zeros[order]) for order in ORDERS},
        **{
            f"{order}_within_tolerance": (
                distances[order] is not None and distances[order] <= TOLERANCE
            )
            for order in ORDERS
        },
    }
    return verdicts, {f"{order}_nearest_zero_distance": distances[order] for order in ORDERS}


def measure(book: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """One book at three orders: the gated verdict block and the advisory fit block."""
    sums = fifth_order_sums(book)
    pairs = [column_row(book, sums, delta) for delta in DELTAS]
    rows = [verdicts for verdicts, _ in pairs]
    distances = [distance for _, distance in pairs]
    radii = {order: P18.contiguous_radius(rows, order) for order in ORDERS}
    h = book.spot * MEASURE_COLUMN
    third_piece = abs(book.third_order()["speed"] * h**3 / 6.0)
    fourth_piece = abs(book.quartic_piece(MEASURE_COLUMN, 0.0))
    fifth_piece = abs(quintic_piece(book, sums, MEASURE_COLUMN, 0.0))

    def worst(order: str, limit: float) -> float | None:
        return P18.worst_distance(distances, rows, f"{order}_nearest_zero_distance", limit)

    verdicts = {
        "label": book.label,
        "why_this_book": book.why,
        "radius_cubic": radii["cubic"],
        "radius_quartic": radii["quartic"],
        "radius_quintic": radii["quintic"],
        "widening_factor_quartic": (
            radii["quartic"] / radii["cubic"] if radii["cubic"] > 0.0 else None
        ),
        "widening_factor_quintic": (
            radii["quintic"] / radii["quartic"] if radii["quartic"] > 0.0 else None
        ),
        "quintic_radius_at_grid_edge": radii["quintic"] == GRID_EDGE,
        "columns_swept": len(rows),
        "columns_with_a_priced_crossing": sum(1 for row in rows if row["measured_zero_count"]),
        **{
            f"{order}_zero_count_total": sum(row[f"{order}_zero_count"] for row in rows)
            for order in ORDERS
        },
        "columns": rows,
    }
    fits = {
        "v_sigma_root_T": book.v,
        "order_five_over_four_at_measure_column": (
            fifth_piece / fourth_piece if fourth_piece else None
        ),
        "order_four_over_three_at_measure_column": (
            fourth_piece / third_piece if third_piece else None
        ),
        "worst_distance_inside_own_radius": {order: worst(order, radii[order]) for order in ORDERS},
        "worst_distance_inside_quartic_radius": {
            order: worst(order, radii["quartic"]) for order in ORDERS
        },
        "worst_distance_inside_quintic_radius": {
            order: worst(order, radii["quintic"]) for order in ORDERS
        },
        "columns": distances,
    }
    return verdicts, fits


def check(result: dict[str, Any], own_fits: dict[str, Any]) -> None:
    """Refuse a radius that contains a column it failed, and a book too thin to carry a radius."""
    for order in ORDERS:
        radius = result[f"radius_{order}"]
        # A radius is decided by the worst distance *inside that same radius*. Reading it from
        # another order's range would reject a radius over columns it never claimed to cover,
        # which is the conflation Phase 18 had to fix twice in the radius rule itself.
        widest = own_fits["worst_distance_inside_own_radius"][order]
        if radius > 0.0 and widest is not None and widest > TOLERANCE:
            raise RuntimeError(
                f"{result['label']}: its {order} radius of {radius} contains a crossing column "
                f"{widest:.3e} away, outside the {TOLERANCE} tolerance that defines it"
            )
    if result["columns_with_a_priced_crossing"] < MIN_COLUMNS:
        raise RuntimeError(
            f"{result['label']}: only {result['columns_with_a_priced_crossing']} of "
            f"{result['columns_swept']} columns have a priced crossing, below the "
            f"{MIN_COLUMNS} a radius needs to be more than a statement about a point"
        )


def build_payload() -> dict[str, Any]:
    books = []
    fits = {}
    for book in BOOKS:
        result, own_fits = measure(book)
        check(result, own_fits)
        books.append(result)
        fits[book.label] = own_fits

    # The shipped equality gate, run rather than imitated: coefficients, both truncations and the
    # engine
    # P&L over 30 joint moves must be bit-identical to v1.5.0's and v1.6.0's.
    P18.verify_control(BOOKS[0])
    published = next(result for result in books if result["label"] == PUBLISHED_LABEL)
    published_fits = fits[PUBLISHED_LABEL]
    contraction = check_contraction(BOOKS[0], fifth_order_sums(BOOKS[0]))

    for order, expected in (
        ("radius_cubic", P18.P15.SMALL_MOVE_LIMIT),
        ("radius_quartic", P18.P16.WIDENED_LIMIT),
    ):
        if published[order] != expected:
            raise RuntimeError(
                f"the published ladder's {order} recomputed to {published[order]} against the "
                f"{expected} its own artifact publishes"
            )

    measured = [result for result in books if not result["quintic_radius_at_grid_edge"]]
    widened = [result for result in books if result["radius_quintic"] > result["radius_quartic"]]
    unchanged = [result for result in books if result["radius_quintic"] == result["radius_quartic"]]
    closer = []
    for result in books:
        inside = fits[result["label"]]["worst_distance_inside_quartic_radius"]
        quintic_worst = inside["quintic"]
        others = [value for order, value in inside.items() if value is not None]
        if quintic_worst is not None and others and quintic_worst <= min(others):
            closer.append(result)
    factors = [
        result["widening_factor_quintic"] for result in books if result["widening_factor_quintic"]
    ]

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "command": "uv run python experiments/fifth_order_crossing_map/run.py",
        "claim": (
            f"order five widens the contiguous paired-magnitude crossing radius on "
            f"{len(widened)} of {len(books)} books and leaves it unchanged on {len(unchanged)}: "
            f"the published ladder goes {published['radius_quartic']:.2f} -> "
            f"{published['radius_quintic']:.2f}, a factor of "
            f"{published['widening_factor_quintic']:.2f} against the cubic-to-quartic "
            f"{published['widening_factor_quartic']:.2f}; "
            f"{len(books) - len(measured)} books sit at the swept grid edge where a radius cannot "
            "be read as a measurement of anything"
        ),
        "procedure": {
            "books": "the five books, the delta grid, the 0.005 tolerance and the contiguous "
            "paired-magnitude radius rule are imported from "
            "experiments/second_book_crossing_map/run.py, which itself loads v1.5.0's and v1.6.0's "
            "files, so this run adds one order and changes nothing else",
            "radius_definition": "a |delta| magnitude passes only when every signed column at "
            "it that has a priced crossing has this truncation's nearest zero inside 0.005; "
            "the radius is the widest magnitude such that all smaller magnitudes pass",
            "quintic_term": "(1/120) times V_SSSSS h^5 + 5 V_SSSSsigma h^4 k + 10 "
            "V_SSSsigmasigma h^3 k^2 + 10 V_SSsigmasigmasigma h^2 k^3 + "
            "5 V_Ssigmasigmasigmasigma h k^4 + V_sigmasigmasigmasigmasigma k^5, with the six "
            "book sums read from pricing.black_scholes_mixed_fifth_derivatives and h the "
            "absolute spot move",
            "not_measured": "residual slopes against shock size: Phase 18's five books had "
            "already refuted the mechanism a slope would illustrate, and the arithmetic-floor "
            "windowing that governs such fits is this chain's published caveat, not a new one",
        },
        "headline": {
            "books_measured": len(books),
            "radii_quintic": {result["label"]: result["radius_quintic"] for result in books},
            "radii_quartic": {result["label"]: result["radius_quartic"] for result in books},
            "published_radius_cubic": published["radius_cubic"],
            "published_radius_quartic": published["radius_quartic"],
            "published_radius_quintic": published["radius_quintic"],
            "published_widening_factor_quartic": published["widening_factor_quartic"],
            "published_widening_factor_quintic": published["widening_factor_quintic"],
            "books_widening_at_order_five": len(widened),
            "books_unchanged_at_order_five": len(unchanged),
            "books_at_grid_edge": len(books) - len(measured),
            "books_with_quintic_closer_inside_the_quartic_radius": len(closer),
            "quintic_widening_factors": factors,
            "columns_with_a_priced_crossing_total": sum(
                result["columns_with_a_priced_crossing"] for result in books
            ),
        },
        "books": books,
        "fits": fits,
        "controls": {
            "machinery_equality_with_v150_and_v160": "verify_control from "
            "experiments/second_book_crossing_map/run.py ran on the published book before this "
            "artifact was written: the ten third- and fourth-order coefficients, both"
            "truncations and"
            "the engine P&L over 30 joint moves are exactly equal, and the run refuses to publish "
            "otherwise",
            "published_radii_reproduced": {
                "cubic": published["radius_cubic"],
                "expected_cubic": P18.P15.SMALL_MOVE_LIMIT,
                "quartic": published["radius_quartic"],
                "expected_quartic": P18.P16.WIDENED_LIMIT,
            },
            "multinomial_contraction_of_the_quintic_piece": contraction,
            "fifth_order_book_sums_published_book": fifth_order_sums(BOOKS[0]),
            "order_five_over_four_at_measure_column_published_book": published_fits[
                "order_five_over_four_at_measure_column"
            ],
        },
        "reproduction_policy": {
            # Families, not field names, per Phase 16. The distances are roots of a subtraction of
            # book values and the contraction errors are nested differences of a revaluation, so
            # neither has a cross-platform last digit. What stays gated by value is the whole chain
            # that decides a radius -- the zero counts, the tolerance verdicts, the radii, the
            # widened/unchanged counts and the grid-edge flags, which are grid labels.
            "conditioning_limited": [
                "fits",
                "controls.multinomial_contraction_of_the_quintic_piece.rays",
                "controls.order_five_over_four_at_measure_column_published_book",
                "headline.books_with_quintic_closer_inside_the_quartic_radius",
            ],
            "why": (
                "the distances, the closer-verdict they feed, the nested-difference "
                "contraction errors and the order-five-to-four ratio all come from "
                "subtractions of book values near 1e5, so they reproduce to their "
                "conditioning rather than to their last digit; the comparator exempts "
                "floats only, and a radius is a grid point"
            ),
            "everything_else": (
                "the truncations are closed forms on each book's own sums, the priced "
                "error and the engine P&L are exact arithmetic on the shipped engine, "
                "and the published book is pinned to v1.5.0's and v1.6.0's values by "
                "those releases' own equality gate, which this run executes and "
                "requires to be exactly zero"
            ),
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "packages": {"quantrisk": quantrisk.version()},
        },
    }


def write_csv(path: pathlib.Path, rows: list[dict[str, Any]]) -> None:
    extras = ["widening_factor_quartic", "widening_factor_quintic", "quintic_radius_at_grid_edge"]
    fields = ["label"] + [f"radius_{order}" for order in ORDERS] + extras
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row[name] for name in fields})


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    (RESULTS / "fifth_order_crossing_map.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(RESULTS / "fifth_order_radii.csv", payload["books"])
    for result in payload["books"]:
        distances = payload["fits"][result["label"]]["columns"]
        with (RESULTS / f"fifth_order_columns_{slug(result['label'])}.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            names = list(result["columns"][0]) + list(distances[0])
            writer = csv.DictWriter(handle, fieldnames=names)
            writer.writeheader()
            for verdict, distance in zip(result["columns"], distances, strict=True):
                writer.writerow({**verdict, **distance})
    print(payload["claim"])
    return 0


def slug(label: str) -> str:
    """A filename-safe form of a book's label, so hyphens count as separators too."""
    return "_".join(label.lower().replace("-", " ").split())


if __name__ == "__main__":
    raise SystemExit(main())
