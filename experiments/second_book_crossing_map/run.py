"""Does the order-four crossing radius belong to the model, or to the book v1.6.0 measured?

`experiments/fourth_order_crossing_map/` published a number and a mechanism: adding the four mixed
fourth partials to v1.5.0's column truncation widens the radius over which the truncation predicts
where the shipped stress map's error crosses zero, from `|delta| <= 0.05` to `|delta| <= 0.15` -- on
a three-strike ladder at one maturity and one base volatility. Its own §7 said the radius is that
book's. This file tests the sentence rather than asserting it: the same procedure, on books chosen
for what each one does to the terms and not for what it does to the claim.

The book is an argument here and nowhere else in this chain, which is a deliberate cost. The v1.5.0
and v1.6.0 experiments read theirs from module constants, correctly -- each is about one book -- and
a question about books cannot be asked of them. So this file re-derives the truncations from the
core's closed forms and re-runs `run_scenario`, and proves the re-derivation *is* the shipped
machinery where both are defined:

* all ten book sums agree bit-for-bit with `restrike_gamma_map.COEFFS` and
  `fourth_order_crossing_map.COEFFS4` on the published ladder,
* the engine P&L and both truncations agree bit-for-bit with those files over 30 joint moves,
* and the published book's two radii, recomputed end to end here, are the 0.05 and 0.15 v1.6.0
  published.

Those are gates that raise, not fields reported generously: a re-implementation that drifted
would make every other number in this artifact a statement about a pipeline nobody validated.

The five books, fixed before any of them was measured:

1. **published ladder** (spot 100, `sigma = 0.20`, `T = 0.5`, strikes 90/100/110) -- the control.
2. **long-dated wide** (`T = 2.0`, `sigma = 0.35`, 80/100/120): `v = sigma sqrt(T) = 0.495` against
   the published 0.141, so the order-four spot piece is a small fraction of the order-three one.
   Chosen as the book on which an added order has least to work with; it measured the widest
   widening in the set, so that expectation is reported as rejected (see `refusals`).
3. **short-dated tight** (`T = 0.10`, `sigma = 0.15`, 95/100/105): `v = 0.047`, and every spot
   partial divides by `v^3`, so the higher orders are the *largest* terms on the book. If the
   widening was an artefact of the fourth order being small, it dies here.
4. **deep out of the money** (`sigma = 0.45`, `T = 0.5`, 110/125/140): every strike far above spot,
   so the book's partials come from one tail instead of straddling the money.
5. **in the money** (`sigma = 0.20`, `T = 0.5`, 70/80/90): the mirror ladder at published vol and
   maturity, which is the case v1.6.0's §7 could not answer.

How the numbers must be read:

* A radius is one of twelve `|delta|** grid labels, chosen by comparing each column's nearest-zero
  distance with v1.5.0's own 0.005 tolerance, contiguously from the smallest column. `0.15` says
  every column with a priced zero at `|delta| <= 0.15` passed and nothing at all about 0.11; a book
  whose radius sits on the swept edge is flagged, because "no column failed" is weaker there than
  anywhere else.
* The contiguity matters and is not a detail: the first pass at this file asked only whether *some*
  column at each `|delta|` passed, and the in-the-money book then appeared to *shrink* its radius
  under order four (0.15 against 0.10) because its cubic had already failed one column at 5.97e-3.
  Under the shipped gate's own definition that book's cubic radius is 0.05, and the quartic widens
  it. A radius that tolerates a hole inside it is a different quantity from the one v1.5.0 gated.
* Contiguity was still not enough, because a magnitude carries two columns: `-x` and `+x` are one
  candidate and must pass together. Reading them one at a time let the long-dated book publish a
  0.15 cubic radius beside a worst in-range distance of 0.0235 -- a radius and the evidence against
  it in the same block -- so `check()` now refuses any radius wider than the tolerance its own
  distances support, and the re-derivation test plants the asymmetric pair in both column orders.
* A radius therefore has a cross-platform value even though the distance that decided it does not,
  and the artifact is split on exactly that line: the distances live in `fits`, everything that
  decides a radius stays compared by value.

What is not claimed: five books is not a family and nothing here estimates a distribution of radii;
the amount of the map's error is not re-opened (on the published book it is still 16.2 % off at
published size after order four, and `docs/limitations.md` #79 keeps that); and a `zero` is a sign
change of a scanned function, not an analytic root.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "python") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "python"))

import quantrisk  # noqa: E402
from quantrisk import stress as STRESS  # noqa: E402


def _load(relative: str, name: str) -> Any:
    path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# v1.5.0 owns the grid, the tolerance and the root finder; v1.6.0 owns the order-four terms of
# the published book and its truncation. Both are loaded rather than re-typed, so "the same
# truncation, on another book" cannot quietly become "a truncation this file invented".
P15 = _load("experiments/restrike_gamma_map/run.py", "quantrisk_restrike_map_for_second_book")
P16 = _load(
    "experiments/fourth_order_crossing_map/run.py", "quantrisk_fourth_order_for_second_book"
)

DELTAS = P15.DELTAS
VOL_MOVES = P15.VOL_MOVES
TOLERANCE = P15.CROSSING_MATCH_TOLERANCE
PREDICTION_SCAN = P15.PREDICTION_SCAN_POINTS
MEASURED_SCAN = P15.MEASURED_SCAN_POINTS

RESULTS = REPO_ROOT / "experiments" / "second_book_crossing_map" / "results"

# The move at which each book's higher-order ratio is quoted: v1.6.0's widening, so this is the
# displacement at which its claim has to survive on a different book.
MEASURE_COLUMN = 0.15

# The joint moves the engine call and both truncations are pinned to on the published book.
CONTROL_DELTAS = (-0.30, -0.15, -0.05, 0.02, 0.10, 0.30)
CONTROL_MOVES = (-0.10, -0.03, 0.0, 0.05, 0.20)

GRID_EDGE = max(abs(delta) for delta in DELTAS)

# A book needs this many columns with a priced crossing before a radius computed on it means
# anything. Three, because a radius decided by one column is a statement about a point.
MIN_COLUMNS_WITH_A_CROSSING = 3


@dataclass(frozen=True)
class Book:
    """An option book, as an argument.

    Seven numbers, because that is what the expansion is a function of: the market, the ladder, and
    the size. `label` and `why` travel with it so the artifact states, next to each measurement, the
    reason that book is in the set.
    """

    label: str
    why: str
    spot: float
    rate: float
    dividend_yield: float
    volatility: float
    maturity: float
    strikes: tuple[float, ...]
    quantity: float

    @property
    def v(self) -> float:
        """`sigma sqrt(T)`: every spot partial divides by a power of this."""
        return self.volatility * math.sqrt(self.maturity)

    def market(self, spot: float | None = None, sigma: float | None = None) -> Any:
        return quantrisk.pricing.MarketParams(
            spot=self.spot if spot is None else spot,
            rate=self.rate,
            dividend_yield=self.dividend_yield,
            volatility=self.volatility if sigma is None else sigma,
            maturity=self.maturity,
        )

    def options(self) -> list[Any]:
        return [
            quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, strike)
            for strike in self.strikes
        ]

    def book_value(self, spot: float, sigma: float) -> float:
        price = quantrisk.pricing.black_scholes
        market = self.market(spot, sigma)
        return sum(price(o, market).price for o in self.options()) * self.quantity

    def base_value(self) -> float:
        return self.book_value(self.spot, self.volatility)

    def totals(self, spot: float, sigma: float) -> dict[str, float]:
        """Map exposures at one market, in the units the stress layer quotes.

        The same three readings as v1.5.0 -- `delta * S`, `0.5 * gamma * S^2`, `vega` -- summed over
        the ladder and scaled by the position size. Scaling by the *argument* spot and not the
        base is what keeps the four map variants distinct, and it is copied deliberately.
        """
        market = self.market(spot, sigma)
        greeks = quantrisk.pricing.black_scholes_greeks
        readings = {
            "delta": lambda o: greeks(o, market).delta * spot,
            "gamma": lambda o: 0.5 * greeks(o, market).gamma * spot * spot,
            "vega": lambda o: greeks(o, market).vega,
        }
        return {
            name: sum(read(o) for o in self.options()) * self.quantity
            for name, read in readings.items()
        }

    def base(self) -> dict[str, float]:
        return self.totals(self.spot, self.volatility)

    def third_order(self) -> dict[str, float]:
        """The third-order book sums, as raw partials at the base market."""
        market = self.market()
        mixed = quantrisk.pricing.black_scholes_mixed_third_derivatives
        cross = quantrisk.pricing.black_scholes_vol_cross_derivatives
        spot_partials = quantrisk.pricing.black_scholes_spot_derivatives
        readings = {
            "speed": lambda o: spot_partials(o, market).third,
            "vanna": lambda o: cross(o, market).vanna,
            "volga": lambda o: cross(o, market).volga,
            "gamma_sigma": lambda o: mixed(o, market).spot_spot_sigma,
            "vanna_sigma": lambda o: mixed(o, market).spot_sigma_sigma,
            "volga_sigma": lambda o: mixed(o, market).sigma_sigma_sigma,
        }
        return {
            name: sum(read(o) for o in self.options()) * self.quantity
            for name, read in readings.items()
        }

    def fourth_order(self) -> dict[str, float]:
        """The order-four book sums, in v1.6.0's own field names."""
        market = self.market()
        mixed = quantrisk.pricing.black_scholes_mixed_fourth_derivatives
        spot_partials = quantrisk.pricing.black_scholes_spot_derivatives
        mixed_fields = (
            "spot_spot_spot_sigma",
            "spot_spot_sigma_sigma",
            "spot_sigma_sigma_sigma",
            "sigma_sigma_sigma_sigma",
        )
        readings: dict[str, Callable[[Any], float]] = {
            "spot_x4": lambda o: spot_partials(o, market).fourth,
            **{
                name: (lambda o, field=name: mixed(o, market).__getattribute__(field))
                for name in mixed_fields
            },
        }
        return {
            name: sum(read(o) for o in self.options()) * self.quantity
            for name, read in readings.items()
        }

    def engine_pnl(self, delta: float, vol_move: float, exposure: dict[str, float]) -> float:
        """One map evaluation, through the shipped stress engine on this book."""
        factors = STRESS.FactorSet()
        factors.factors = [
            STRESS.RiskFactor("EQ0", STRESS.FactorClass.equity_index, self.spot, "index points"),
            STRESS.RiskFactor(
                "VOL", STRESS.FactorClass.volatility, self.volatility, "annualised vol"
            ),
        ]
        vector = STRESS.ExposureVector()
        # Blocks are indexed by factor position, as v1.5.0 records it: a vega parked on the equity
        # factor is multiplied by zero and disappears silently.
        vector.delta = [exposure["delta"], 0.0]
        vector.gamma = [exposure["gamma"], 0.0]
        vector.duration = [0.0, 0.0]
        vector.vega = [0.0, exposure["vega"]]
        vector.credit = [0.0, 0.0]
        position = STRESS.Position()
        position.name = "option_book"
        position.exposures = vector
        portfolio = STRESS.Portfolio()
        portfolio.factors = factors
        portfolio.positions = [position]

        handle = STRESS.Scenario()
        handle.name = "second_book_probe"
        handle.kind = STRESS.ScenarioKind.deterministic
        handle.assumptions = "equity relative move and volatility absolute move, nothing else"
        handle.shocks = [
            STRESS.Shock("EQ0", delta, 0.0),
            STRESS.Shock("VOL", 0.0, vol_move),
        ]
        return float(STRESS.run_scenario(portfolio, handle).pnl_change)

    def exact_move(self, delta: float, vol_move: float) -> float:
        """The revalued book P&L for one joint move, against this book's own base value."""
        moved = self.book_value(self.spot + self.spot * delta, self.volatility + vol_move)
        return moved - self.base_value()

    def map_error(self, delta: float, vol_move: float) -> float:
        """What the shipped map got wrong at one joint move on this book."""
        return self.exact_move(delta, vol_move) - self.engine_pnl(delta, vol_move, self.base())

    def cubic_error(self, delta: float, k: float) -> float:
        """v1.5.0's third-order truncation of that error, on this book's coefficients."""
        h = self.spot * delta
        c = self.third_order()
        return (
            c["speed"] * h**3 / 6.0
            + k * (c["vanna"] * h + 0.5 * c["gamma_sigma"] * h * h)
            + k * k * (0.5 * c["volga"] + 0.5 * c["vanna_sigma"] * h)
            + c["volga_sigma"] * k**3 / 6.0
        )

    def quartic_piece(self, delta: float, k: float) -> float:
        """`(1/24)` times the fourth directional derivative along the joint move `(h, k)`."""
        h = self.spot * delta
        f = self.fourth_order()
        return (
            f["spot_x4"] * h**4
            + 4.0 * f["spot_spot_spot_sigma"] * h**3 * k
            + 6.0 * f["spot_spot_sigma_sigma"] * h * h * k * k
            + 4.0 * f["spot_sigma_sigma_sigma"] * h * k**3
            + f["sigma_sigma_sigma_sigma"] * k**4
        ) / 24.0

    def quartic_error(self, delta: float, k: float) -> float:
        return self.cubic_error(delta, k) + self.quartic_piece(delta, k)

    def predicted_zeros(self, function: Callable[[float], float]) -> list[float]:
        return P15._sign_change_roots(function, min(VOL_MOVES), max(VOL_MOVES), PREDICTION_SCAN)

    def measured_zeros(self, delta: float) -> list[float]:
        return P15._sign_change_roots(
            lambda k: self.map_error(delta, k),
            min(VOL_MOVES),
            max(VOL_MOVES),
            MEASURED_SCAN,
        )


BOOKS: tuple[Book, ...] = (
    Book(
        label="published ladder",
        why="v1.5.0 and v1.6.0's book, and the control: its radii must come out at 0.05 and 0.15",
        spot=100.0,
        rate=0.03,
        dividend_yield=0.0,
        volatility=0.20,
        maturity=0.5,
        strikes=(90.0, 100.0, 110.0),
        quantity=5000.0,
    ),
    Book(
        label="long-dated wide",
        why="v = 0.495 against the published 0.141, so the order-four spot piece is the smallest "
        "fraction of the order-three one in the set: chosen as the book expected to have least for "
        "an added order to remove, which the measured 3.0x widening contradicts",
        spot=100.0,
        rate=0.03,
        dividend_yield=0.01,
        volatility=0.35,
        maturity=2.0,
        strikes=(80.0, 100.0, 120.0),
        quantity=3000.0,
    ),
    Book(
        label="short-dated tight",
        why="v = 0.047 and every spot partial divides by v^3, so the higher orders are the largest "
        "terms on the book: this is where a widening bought by smallness would die",
        spot=100.0,
        rate=0.03,
        dividend_yield=0.0,
        volatility=0.15,
        maturity=0.10,
        strikes=(95.0, 100.0, 105.0),
        quantity=5000.0,
    ),
    Book(
        label="deep out of the money",
        why="every strike far above spot at a high vol, so the book's partials come from one tail "
        "of the distribution rather than straddling the money",
        spot=100.0,
        rate=0.03,
        dividend_yield=0.0,
        volatility=0.45,
        maturity=0.5,
        strikes=(110.0, 125.0, 140.0),
        quantity=5000.0,
    ),
    Book(
        label="in the money",
        why="the mirror ladder at the published vol and maturity: convexity on the other side of "
        "spot, which is the case v1.6.0's note listed as unanswered",
        spot=100.0,
        rate=0.03,
        dividend_yield=0.0,
        volatility=0.20,
        maturity=0.5,
        strikes=(70.0, 80.0, 90.0),
        quantity=5000.0,
    ),
)


def column_row(book: Book, delta: float) -> tuple[dict[str, Any], dict[str, Any]]:
    """One column, split the way the reproduction gate needs it.

    The verdict half -- how many zeros each side has, whether the nearest pair is inside v1.5.0's
    tolerance -- is a decision with a cross-platform value, and the radius is built from it. The
    distance half is a root of a subtraction of book values, so it belongs to `fits`.
    """
    measured = book.measured_zeros(delta)
    cubic = book.predicted_zeros(lambda k: book.cubic_error(delta, k))
    quartic = book.predicted_zeros(lambda k: book.quartic_error(delta, k))
    cubic_distance = min((abs(a - b) for a in cubic for b in measured), default=None)
    quartic_distance = min((abs(a - b) for a in quartic for b in measured), default=None)
    verdicts = {
        "delta": delta,
        "abs_delta": abs(delta),
        "measured_zero_count": len(measured),
        "cubic_zero_count": len(cubic),
        "quartic_zero_count": len(quartic),
        "cubic_within_tolerance": (cubic_distance is not None and cubic_distance <= TOLERANCE),
        "quartic_within_tolerance": (
            quartic_distance is not None and quartic_distance <= TOLERANCE
        ),
    }
    distances = {
        "cubic_nearest_zero_distance": cubic_distance,
        "quartic_nearest_zero_distance": quartic_distance,
    }
    return verdicts, distances


def contiguous_radius(rows: list[dict[str, Any]], order: str) -> float:
    """The widest `|delta|` such that every column with a priced crossing up to it passes.

    Contiguous, not "some column passes": v1.5.0's gate asks each in-range column, and a radius that
    tolerated a hole would be a different quantity from the one this chain has been publishing.

    A magnitude is also signed twice. `delta = -0.15` and `+0.15` are one radius candidate and two
    columns, so the pair passes only when both do; the first version of this function read the
    columns one at a time, which let a book claim 0.15 on a `-0.15` column that passed at 0.00022
    while its `+0.15` partner sat at 0.0235. The re-derivation test plants that shape.
    """
    by_magnitude: dict[float, list[dict[str, Any]]] = {}
    for row in rows:
        by_magnitude.setdefault(row["abs_delta"], []).append(row)
    widest = 0.0
    for magnitude in sorted(by_magnitude):
        crossing = [row for row in by_magnitude[magnitude] if row["measured_zero_count"]]
        if not crossing:
            continue
        if not all(row[f"{order}_within_tolerance"] for row in crossing):
            break
        widest = magnitude
    return widest


def worst_distance(
    distances: list[dict[str, Any]], rows: list[dict[str, Any]], key: str, limit: float
) -> float | None:
    """The loosest distance inside a radius, which is what the radius is asserting."""
    inside = [
        row[key]
        for row, verdict in zip(distances, rows, strict=True)
        if verdict["measured_zero_count"] and verdict["abs_delta"] <= limit and row[key] is not None
    ]
    return max(inside) if inside else None


def measure(book: Book) -> tuple[dict[str, Any], dict[str, Any]]:
    """One book: its verdict block (gated) and its fit block (advisory)."""
    pairs = [column_row(book, delta) for delta in DELTAS]
    rows = [verdicts for verdicts, _ in pairs]
    distances = [distance for _, distance in pairs]
    radius_cubic = contiguous_radius(rows, "cubic")
    radius_quartic = contiguous_radius(rows, "quartic")
    h = book.spot * MEASURE_COLUMN
    third_piece = abs(book.third_order()["speed"] * h**3 / 6.0)
    fourth_piece = abs(book.quartic_piece(MEASURE_COLUMN, 0.0))
    verdicts = {
        "label": book.label,
        "why_this_book": book.why,
        "market": {
            "spot": book.spot,
            "rate": book.rate,
            "dividend_yield": book.dividend_yield,
            "volatility": book.volatility,
            "maturity": book.maturity,
            "strikes": list(book.strikes),
            "quantity": book.quantity,
        },
        "radius_cubic": radius_cubic,
        "radius_quartic": radius_quartic,
        "widening_factor": radius_quartic / radius_cubic if radius_cubic > 0.0 else None,
        "radius_quartic_at_grid_edge": radius_quartic == GRID_EDGE,
        "columns_swept": len(rows),
        "columns_with_a_priced_crossing": sum(1 for row in rows if row["measured_zero_count"]),
        "measured_zero_count_total": sum(row["measured_zero_count"] for row in rows),
        "cubic_zero_count_total": sum(row["cubic_zero_count"] for row in rows),
        "quartic_zero_count_total": sum(row["quartic_zero_count"] for row in rows),
        "columns": rows,
    }
    scalar_fits = {
        "v_sigma_root_T": book.v,
        "order_four_over_three_at_measure_column": (
            fourth_piece / third_piece if third_piece else None
        ),
        "worst_distance_inside_cubic_radius": {
            "cubic": worst_distance(distances, rows, "cubic_nearest_zero_distance", radius_cubic),
            "quartic": worst_distance(
                distances, rows, "quartic_nearest_zero_distance", radius_cubic
            ),
        },
        "worst_distance_inside_quartic_radius_quartic": worst_distance(
            distances, rows, "quartic_nearest_zero_distance", radius_quartic
        ),
        "columns": distances,
    }
    return verdicts, scalar_fits


def control(book: Book) -> dict[str, Any]:
    """The largest difference between this file's machinery and the shipped one, on their book.

    Zero is not the result of a tolerance test -- `verify_control()` raises on any nonzero value --
    so these fields are a published assertion of exactness rather than a band.
    """
    third, fourth = book.third_order(), book.fourth_order()
    coefficient = max(
        [abs(third[name] - value) for name, value in P15.COEFFS.items()]
        + [abs(fourth[name] - value) for name, value in P16.COEFFS4.items()]
    )
    engine = cubic = quartic = 0.0
    for delta in CONTROL_DELTAS:
        for move in CONTROL_MOVES:
            engine = max(
                engine,
                abs(book.engine_pnl(delta, move, P15.BASE) - P15.engine_pnl(delta, move, P15.BASE)),
            )
            cubic = max(
                cubic,
                abs(book.cubic_error(delta, move) - P15.truncated_column_error(delta, move)),
            )
            quartic = max(
                quartic,
                abs(book.quartic_error(delta, move) - P16.quartic_column_error(delta, move)),
            )
    return {
        "book_coefficients_largest_absolute_difference": coefficient,
        "engine_pnl_largest_absolute_difference": engine,
        "cubic_truncation_largest_absolute_difference": cubic,
        "quartic_truncation_largest_absolute_difference": quartic,
        "control_moves_compared": len(CONTROL_DELTAS) * len(CONTROL_MOVES),
        "v150_radius_cubic": P15.SMALL_MOVE_LIMIT,
        "v160_radius_quartic": P16.WIDENED_LIMIT,
    }


def check(result: dict[str, Any], own_fits: dict[str, Any]) -> None:
    """Refuse to publish a book the radius cannot be read off, whatever it then says.

    The second gate is the one the first version of `contiguous_radius` needed. A radius is the
    claim that every crossing column up to it sits inside the tolerance, so the widest distance
    inside it must be inside the tolerance too. Reading the columns one at a time rather than by
    magnitude let a book report a 0.15 radius whose worst in-range distance was 0.0235 -- a radius
    containing a column the same artifact had already called a failure, and nothing raised.
    """
    if result["columns_with_a_priced_crossing"] < MIN_COLUMNS_WITH_A_CROSSING:
        raise RuntimeError(
            f"{result['label']}: only {result['columns_with_a_priced_crossing']} columns have a "
            f"priced crossing, fewer than the {MIN_COLUMNS_WITH_A_CROSSING} a radius needs"
        )
    gated = [
        (
            "cubic",
            result["radius_cubic"],
            own_fits["worst_distance_inside_cubic_radius"]["cubic"],
        ),
        (
            "quartic",
            result["radius_quartic"],
            own_fits["worst_distance_inside_quartic_radius_quartic"],
        ),
    ]
    for order, radius, widest in gated:
        if widest is not None and widest > TOLERANCE:
            raise RuntimeError(
                f"{result['label']}: its {order} radius of {radius} contains a crossing column "
                f"{widest:.3e} away, outside the {TOLERANCE} tolerance that defines it"
            )


def verify_control(book: Book) -> None:
    """The re-implementation has to BE the shipped machinery, on the book both are published on.

    Only `published ladder` is checked, because only it has a shipped counterpart: the other four
    books exist solely in this file, and asserting equality against them would assert nothing.
    """
    third, fourth = book.third_order(), book.fourth_order()
    for name, value in P15.COEFFS.items():
        if third[name] != value:
            raise RuntimeError(
                f"{name} does not equal restrike_gamma_map's on the published book: "
                f"{third[name]!r} against {value!r}"
            )
    for name, value in P16.COEFFS4.items():
        if fourth[name] != value:
            raise RuntimeError(
                f"{name} does not equal fourth_order_crossing_map's on the published book: "
                f"{fourth[name]!r} against {value!r}"
            )
    for delta in CONTROL_DELTAS:
        for move in CONTROL_MOVES:
            if book.engine_pnl(delta, move, P15.BASE) != P15.engine_pnl(delta, move, P15.BASE):
                raise RuntimeError(f"the engine call drifted from v1.5.0's at {delta}, {move}")
            if book.cubic_error(delta, move) != P15.truncated_column_error(delta, move):
                raise RuntimeError(f"the cubic truncation drifted from v1.5.0's at {delta}, {move}")
            if book.quartic_error(delta, move) != P16.quartic_column_error(delta, move):
                raise RuntimeError(
                    f"the quartic truncation drifted from v1.6.0's at {delta}, {move}"
                )


def build_payload() -> dict[str, Any]:
    books = []
    fits = {}
    for book in BOOKS:
        result, own_fits = measure(book)
        check(result, own_fits)
        books.append(result)
        fits[book.label] = own_fits

    verify_control(BOOKS[0])
    published = next(result for result in books if result["label"] == "published ladder")
    if published["radius_cubic"] != P15.SMALL_MOVE_LIMIT:
        raise RuntimeError(
            f"the published ladder's cubic radius recomputed to {published['radius_cubic']} "
            f"against "
            f"v1.5.0's own {P15.SMALL_MOVE_LIMIT}"
        )
    if published["radius_quartic"] != P16.WIDENED_LIMIT:
        raise RuntimeError(
            f"the published ladder's quartic radius recomputed to "
            f"{published['radius_quartic']} against v1.6.0's own {P16.WIDENED_LIMIT}"
        )

    others = [result for result in books if result is not published]
    factors = [result["widening_factor"] for result in others if result["widening_factor"]]
    widened = [result for result in books if result["radius_quartic"] >= result["radius_cubic"]]
    closer = [
        result
        for result in books
        if fits[result["label"]]["worst_distance_inside_cubic_radius"]["quartic"] is not None
        and fits[result["label"]]["worst_distance_inside_cubic_radius"]["cubic"] is not None
        and fits[result["label"]]["worst_distance_inside_cubic_radius"]["quartic"]
        <= fits[result["label"]]["worst_distance_inside_cubic_radius"]["cubic"]
    ]
    ratios = [
        fits[result["label"]]["order_four_over_three_at_measure_column"]
        for result in books
        if fits[result["label"]]["order_four_over_three_at_measure_column"] is not None
    ]
    radii_cubic = {result["label"]: result["radius_cubic"] for result in books}
    radii_quartic = {result["label"]: result["radius_quartic"] for result in books}

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "command": "uv run python experiments/second_book_crossing_map/run.py",
        "claim": (
            "the order-four widening is a property of the expansion and not of v1.6.0's ladder: on "
            f"{len(widened)} of {len(books)} books the quartic's contiguous crossing radius is at "
            "least the cubic's, and on every book its worst distance inside the cubic's own radius "
            f"is the smaller -- but the magnitude does not transfer: the published "
            f"{published['widening_factor']:.1f}x is the widest factor in the set, matched by one "
            f"other book, the four spanning {min(factors):.1f}x to {max(factors):.1f}x"
        ),
        "procedure": {
            "tolerance": TOLERANCE,
            "delta_grid": list(DELTAS),
            "volatility_moves_swept": [min(VOL_MOVES), max(VOL_MOVES)],
            "prediction_scan_points": PREDICTION_SCAN,
            "measured_scan_points": MEASURED_SCAN,
            "bisection_steps": P15.BISECTION_STEPS,
            "radius_definition": (
                "the widest |delta| whose every column with a priced crossing has its nearest "
                "predicted zero inside the tolerance, contiguous from the smallest magnitude "
                "outward, a magnitude passing only when both of its signed columns do"
            ),
            "shared_with": (
                "the grid, the tolerance and _sign_change_roots are imported from "
                "restrike_gamma_map/run.py, and v1.6.0's truncation is imported as the control, "
                "so a "
                "radius here and a radius there mean one thing"
            ),
        },
        "headline": {
            "books_measured": len(books),
            "book_labels": [result["label"] for result in books],
            "radii_cubic": radii_cubic,
            "radii_quartic": radii_quartic,
            "published_control_cubic": published["radius_cubic"],
            "published_control_quartic": published["radius_quartic"],
            "books_where_the_quartic_radius_is_at_least_the_cubic": len(widened),
            "books_where_the_quartic_is_closer_inside_the_cubic_radius": len(closer),
            "widening_factor_published_book": published["widening_factor"],
            "widening_factor_range_other_books": [min(factors), max(factors)],
            "columns_with_a_priced_crossing_minimum": min(
                result["columns_with_a_priced_crossing"] for result in books
            ),
            "grid_edge": GRID_EDGE,
            "books_with_a_radius_at_the_grid_edge": [
                result["label"] for result in books if result["radius_quartic_at_grid_edge"]
            ],
            "measure_column": MEASURE_COLUMN,
            "fits": {
                "widening_factors": {
                    result["label"]: result["widening_factor"] for result in books
                },
                "order_four_over_three_range": [min(ratios), max(ratios)],
                "v_sigma_root_T_range": [
                    min(fits[result["label"]]["v_sigma_root_T"] for result in books),
                    max(fits[result["label"]]["v_sigma_root_T"] for result in books),
                ],
                "worst_distance_inside_cubic_radius": {
                    result["label"]: fits[result["label"]]["worst_distance_inside_cubic_radius"]
                    for result in books
                },
            },
        },
        "control": control(BOOKS[0]),
        "books": books,
        "fits": fits,
        "provenance": {
            "reimplemented_by_this_file": [
                "the third- and fourth-order book sums, from the core's closed forms",
                "the two column truncations",
                "the map P&L, through quantrisk.stress.run_scenario",
            ],
            "imported_unchanged": [
                "restrike_gamma_map: DELTAS, VOL_MOVES, the scans, the tolerance, "
                "BISECTION_STEPS, _sign_change_roots, BASE, COEFFS, truncated_column_error",
                "fourth_order_crossing_map: COEFFS4, quartic_column_error, WIDENED_LIMIT",
            ],
            "equality_gate": (
                "every reimplemented quantity is asserted bit-equal to the shipped one on the "
                "published book, over 10 coefficients and 30 joint moves, and both published "
                "radii are "
                "asserted to recompute exactly; the run raises rather than publishing otherwise"
            ),
        },
        "refusals": {
            "five_books_are_not_a_family": (
                "five points in a seven-parameter space, chosen for what each does to the terms; "
                "nothing here estimates a distribution of radii over books or a probability that a "
                "new book widens"
            ),
            "radius_is_not_accuracy": (
                "every number is about where the map's error crosses zero. On the published book "
                "the "
                "amount at published size is still 16.2 % off after order four, and no book here "
                "changes that"
            ),
            "grid_point_not_crossing": (
                "a radius is one of twelve |delta| labels, so 0.15 says nothing about 0.11, and a "
                "book whose radius sits on the swept edge is flagged rather than rounded down"
            ),
            "no_gate_on_the_finding": (
                "the run refuses a book with too few priced crossings and refuses any drift from "
                "the "
                "shipped machinery, but it does not gate quartic >= cubic: a book where that "
                "failed "
                "would be measured, published and headlined"
            ),
            "ratio_does_not_explain_the_widening": (
                "the order-four-to-three ratio at the measure column was the axis the set was "
                "built to span, on the expectation that a small fourth-order piece leaves an "
                "added order little to remove. The measured widening does not follow that ratio: "
                "the book with the smallest one tied the widest factor. The per-book ratio is "
                "published under `fits` so a later book can be checked against it; no mechanism "
                "is offered here"
            ),
            "zeros_are_sign_changes": (
                "a zero is a sign change of a scanned function found by the imported routine, not "
                "an "
                "analytic root; a column with none is skipped rather than counted as a pass"
            ),
        },
        "reproduction_policy": {
            # Two families and no field names, declared the way Phase 16 learned to declare them.
            # The distances are roots of a subtraction of book values and the fitted quantities are
            # built on them, so neither has a cross-platform value. What sits outside is the whole
            # chain that decides a radius -- the zero counts, the within-tolerance verdicts and the
            # radii themselves, which are grid labels, not measurements.
            "conditioning_limited": ["fits", "headline.fits"],
            "why": (
                "nearest-zero distances are roots of a subtraction of book values and the "
                "mechanism "
                "ratios divide two such terms, so both reproduce to their conditioning rather "
                "than to "
                "their last digit. The radii, widening factors, zero counts and every tolerance "
                "verdict "
                "are compared by value inside the declared families as well, because the "
                "comparator "
                "exempts floats only and a radius is a grid point"
            ),
            "everything_else": (
                "the truncations are closed forms on each book's own sums, the priced error and "
                "the "
                "engine P&L are exact arithmetic on the shipped engine, and the published book is "
                "additionally pinned to v1.5.0's and v1.6.0's values by `control`, which is gated "
                "to "
                "be exactly zero"
            ),
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "packages": {"quantrisk": quantrisk.version()},
        },
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value) if isinstance(value, (list, dict)) else value
                    for key, value in row.items()
                }
            )


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    json_path = RESULTS / "second_book_crossing_map.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    profile_rows = [
        {
            "book": book["label"],
            "radius_cubic": book["radius_cubic"],
            "radius_quartic": book["radius_quartic"],
            **column,
            **distance,
        }
        for book in payload["books"]
        for column, distance in zip(
            book["columns"],
            payload["fits"][book["label"]]["columns"],
            strict=True,
        )
    ]
    write_csv(RESULTS / "second_book_columns.csv", profile_rows)

    for book in payload["books"]:
        factor = book["widening_factor"]
        own = payload["fits"][book["label"]]
        print(
            f"  {book['label']:24s} cubic {book['radius_cubic']:.2f} -> quartic "
            f"{book['radius_quartic']:.2f}"
            + (f" (x{factor:.1f})" if factor else "")
            + f"  v {own['v_sigma_root_T']:.3f}  4th/3rd "
            f"{own['order_four_over_three_at_measure_column']:.3f}"
        )
    print(
        f"{payload['headline']['books_where_the_quartic_radius_is_at_least_the_cubic']} of "
        f"{payload['headline']['books_measured']} books widen, "
        f"{payload['headline']['books_where_the_quartic_is_closer_inside_the_cubic_radius']} "
        f"closer "
        "inside the cubic radius; control differences "
        f"{payload['control']['book_coefficients_largest_absolute_difference']:.0e} / "
        f"{payload['control']['engine_pnl_largest_absolute_difference']:.0e}"
    )
    print(f"wrote {json_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
