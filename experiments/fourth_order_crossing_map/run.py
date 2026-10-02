#!/usr/bin/env python3
r"""Phase 16 experiment: how far a fourth-order truncation predicts the map's crossing.

    uv run python experiments/fourth_order_crossing_map/run.py
    uv run python scripts/run_benchmark_suite.py --only fourth_order_crossing_map

`v1.5.0` measured the recommendation v1.3.0 had left unmeasured, and closed with the reason it
cannot be extrapolated: the shipped delta-gamma-vega map's error is predicted, term by term, by a
*third*-order truncation of the two-variable expansion, and that truncation locates the volatility
move where the map happens to be exactly right only within `|delta| <= 0.05` -- out to `|delta| =
0.30` its nearest predicted zero drifts to 0.093 away from the priced one, and at `delta = +0.30` it
predicts a crossing the priced map never has. The published note called that "what a third-order
expansion deserves". This experiment tests whether the next order is what it says it is, and how
much radius it buys.

The four mixed fourth partials shipped in the core this phase
(`black_scholes_mixed_fourth_derivatives`) complete the order-four coefficient set. Adding them to
the same column truncation gives

    \frac16 V_{SSS} h^3
    + k   \left( V_{S\sigma} h + \frac12 V_{SS\sigma} h^2 \right)
    + k^2 \left( \frac12 V_{\sigma\sigma} + \frac12 V_{S\sigma\sigma} h \right)
    + \frac16 V_{\sigma\sigma\sigma} k^3
    + \frac{1}{24} \left( V_{SSSS} h^4 + 4 V_{SSS\sigma} h^3 k + 6 V_{SS\sigma\sigma} h^2 k^2
                         + 4 V_{S\sigma\sigma\sigma} h k^3
                         + V_{\sigma\sigma\sigma\sigma} k^4 \right)

with every coefficient summed over the published book at the base market and none of it fitted to
anything measured here. The book, the grid, the engine call and the cubic truncation are imported
from `experiments/restrike_gamma_map/run.py` rather than re-typed: this is a claim about *that*
truncation plus four terms, and sharing the code is what makes "plus four terms" checkable.

Four claims, each falsifiable, and two of them came out other than expected:

1. **The extra order is the order it claims to be.** Along four joint-shock rays scaled from the
   published size down to a thousandth of it, the residual the cubic truncation leaves falls with a
   log-log slope of 3.96-4.37, and the residual the quartic leaves falls with 4.73-5.01: fourth
   order against fifth, which is the claim. The window is what makes that number mean anything and
   it is
   published both ways -- include the point at `scale = 1e-3`, where the residual has reached the
   arithmetic floor of subtracting book values near 1.09e5, and the quartic's fitted slope collapses
   to 2.46-4.30, with all four rays turning back at that scale. The ratio of the two residuals falls
   against `log scale` with slope 0.62-1.04, which is the 1.0 one extra order implies, and sits at
   0.0013-0.048 by `scale = 3e-3`.
2. **The crossing radius triples.** Within `|delta| <= 0.15` the nearest zero of the quartic
   truncation sits within the published 0.005 tolerance of the nearest zero of the priced error on
   every column -- worst 0.00162 -- while the cubic truncation, run through the same
   bracket-and-bisect routine on the same columns, misses that tolerance on exactly four of them
   (`|delta|` = 0.10 and 0.15, both signs), worst 0.01887: a factor of 11.6. Inside the limit v1.5.0
   already claimed, the effect is larger again -- 1.15e-5 against 0.00243, a factor of 211.6. Beyond
   0.15 both fail and the quartic fails less: 0.0323 against 0.0934 at `delta = -0.30`. The gate is
   two-sided, the quartic inside tolerance precisely where the cubic is outside it, so the widening
   cannot be an artifact of a looser test.
3. **What the extra order buys in *count* is smaller than what it buys in *place*.** Across the
   twelve columns the priced error has 13 zeros. The cubic truncation finds 14 and disagrees with
   the priced count on three columns; the quartic also finds 14, and disagrees on one -- a different
   column. It repairs the cubic's two mistakes (a crossing missed at `delta = -0.05`, a spurious one
   at `delta = 0.05`) and the spurious zero at `delta = +0.30`, then invents one of its own at
   `k = 0.164` on the `delta = +0.10` column. The counts are reported, not gated: which crossings
   exist is a question the truncation answers differently from the price, and a tolerance on
   *distance* would have hidden it.
4. **None of this makes the map's error cheaper to predict at published size.** On the `risk_off`
   scenario (`delta = -0.15`, `k = +0.06`) the cubic truncation puts the shipped map's error at
   -4,135.87 against a priced -5,320.79, 22.3 % short; the quartic puts it at -6,182.27, 16.2 %
   over -- closer, but on the other side, and the fourth-order piece it adds (-2,046.40) is larger
   than the 1,184.92 correction the price needed. For the re-struck map of v1.5.0 the same pair
   reads +61.2 % against -44.5 %. At full shock size the quartic is not even monotonically better:
   on the shallow ray its residual is 1.38x the cubic's, with the opposite sign, where the same ray
   gives 0.23x at a third of the size. A wider radius around the *crossing* is therefore not a
   better estimate of the *amount*, and the documents that quote a predicted error still have to
   quote the priced one.

What is deliberately not claimed. One book, one maturity, one base vol, the same three-strike ladder
as v1.5.0: the coefficients are that book's sums, so a book whose fourth-order terms do not share
its signs will have a different radius. `predicted_zeros` and `measured_zeros` are counts of sign

changes on a scanned interval, not of distinct analytic roots. The residuals in claim 1 are
differences of quantities near 1.09e5, so they reproduce to their conditioning, and
`reproduction_policy` says which fields that covers. Nothing here changes what `run_scenario`
ships.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "python") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "python"))

import quantrisk  # noqa: E402

# The phase-15 module is the definition of the book, the grid, the engine call and the cubic
# truncation. Loading it (rather than copying four functions out of it) is what makes "the same
# truncation plus the order-four terms" a statement this file cannot quietly break.
_SPEC = importlib.util.spec_from_file_location(
    "quantrisk_restrike_gamma_map_for_fourth_order",
    REPO_ROOT / "experiments" / "restrike_gamma_map" / "run.py",
)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover
    raise RuntimeError("cannot load experiments/restrike_gamma_map/run.py")
P15 = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = P15
_SPEC.loader.exec_module(P15)

SPOT = P15.SPOT
VOLATILITY = P15.VOLATILITY
DELTAS = P15.DELTAS
VOL_MOVES = P15.VOL_MOVES
SCALES = P15.SCALES
TOLERANCE = P15.CROSSING_MATCH_TOLERANCE
SCAN = P15.PREDICTION_SCAN_POINTS
MEASURED_SCAN = P15.MEASURED_SCAN_POINTS

RESULTS = REPO_ROOT / "experiments" / "fourth_order_crossing_map" / "results"

# Claim 2's widened limit. The cubic is gated at 0.05 by v1.5.0; the quartic is asked to hold to
# 0.15, which is three times the move and the widest column where its worst measured distance
# (0.0016) still sits inside the same 0.005 tolerance rather than a new one.
WIDENED_LIMIT = 0.15

# Claim 1's rays. The first three are v1.5.0's, so the ordering law is tested on the same directions
# its slopes were measured on. The fourth is a shallow one -- a third of the size, same signs as the
# crash -- and it earns its place by being the ray where the quartic is *worse* at full size: any
# claim that survives three published directions and not a fourth has to say so.
RAYS = {
    "crash (equity down, vol up)": (-0.15, 0.06),
    "melt-up (equity up, vol down)": (0.15, -0.06),
    "aligned (equity up, vol up)": (0.15, 0.06),
    "shallow (equity down, vol up, a third of the size)": (-0.05, 0.03),
}

# The scale at which the subtraction of book values reaches double precision. Below it the ratio of
# residuals turns back up, which is arithmetic rather than a fifth-order term, so it is reported and
# never gated.
FIT_FLOOR = 0.003

# The scales the ordering law is gated over: above the floor, and at most a third of the published
# shock. Neither bound is a convenience. The upper one because at grid size one of the four
# rays gets worse (see claim 4), so a gate reaching to scale 1.0 would gate a different
# statement; the lower one because fitting through the floor point at scale 1e-3 pulls the
# quartic's slope from 4.73-5.01 down to 2.46-4.30, which is the arithmetic of the subtraction
# showing up as physics.
ORDERING_CEILING = 0.3

# Two gates, because one machine does not get to fix an absolute band.
#
# The load-bearing one is `MINIMUM_SLOPE_SEPARATION`: in the same run, on the same platform, with
# the
# same subtraction noise, the quartic residual must fall *faster* than the cubic one. That is the
# ordering claim: a cubic truncation leaves a fourth-order remainder, a quartic one a fifth-order
# one,
# expressed without referencing what either slope happens to measure.
#
# The absolute bands are then gross-error checks, and the quartic's is deliberately loose. Two
# platforms, running the identical committed artifact, put its fitted slope between 4.323 (the
# shallow
# ray, whose fifth-order residual is the smallest, closest to the arithmetic floor) and 5.223
# (the crash ray); this machine's four rays read 4.73-5.01. An earlier version gated 4.6-5.2 on
# local span alone and the CI runner rejected it twice -- see docs/integrity_audit.md finding 44. A
# dropped order is still caught: a residual that fell with the third order reads 3.0 and cannot
# clear
# the cubic band, and one that fell with the fourth reads 4.0 and cannot separate from it.
CUBIC_SLOPE_BAND = (3.5, 4.6)
QUARTIC_SLOPE_BAND = (4.0, 5.8)
MINIMUM_SLOPE_SEPARATION = 0.0  # the sign only: the margin is what differs by platform

FOURTH_FIELDS = (
    "spot_spot_spot_sigma",
    "spot_spot_sigma_sigma",
    "spot_sigma_sigma_sigma",
    "sigma_sigma_sigma_sigma",
)


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def book_fourth_coefficients() -> dict[str, float]:
    r"""The order-four coefficients of the book at the base market, as raw partials.

    `ssss` is the pure-spot quartic, already published as `SpotDerivatives::fourth`; the other four
    are `MixedFourthDerivatives`. Each is summed over the ladder and scaled by the position size,
    exactly as `book_expansion_coefficients` does for the third order, so the two sets belong to one
    expansion and one book.
    """
    market = P15.market(SPOT, VOLATILITY)
    mixed = quantrisk.pricing.black_scholes_mixed_fourth_derivatives
    spot = quantrisk.pricing.black_scholes_spot_derivatives
    readings: dict[str, Callable[[Any], float]] = {
        "spot_x4": lambda o: spot(o, market).fourth,
        **{
            name: (lambda o, field=name: mixed(o, market).__getattribute__(field))
            for name in FOURTH_FIELDS
        },
    }
    return {
        name: sum(read(P15.option(strike)) for strike in P15.STRIKES) * P15.QUANTITY
        for name, read in readings.items()
    }


COEFFS4 = book_fourth_coefficients()


def quartic_column_term(delta: float, vol_move: float) -> float:
    r"""The order-four piece of the column truncation, in the engine's own move conventions.

    With `h = S \delta` the spot move and `k` the absolute volatility move, the fourth directional
    derivative of the book value contributes

        \frac{1}{24}\left( V_{SSSS} h^4 + 4 V_{SSS\sigma} h^3 k + 6 V_{SS\sigma\sigma} h^2 k^2
                          + 4 V_{S\sigma\sigma\sigma} h k^3
                          + V_{\sigma\sigma\sigma\sigma} k^4 \right)

    The binomial factors are what make this the coefficient of one directional derivative rather
    than five unrelated numbers: the contraction of the order-four tensor along `(h, k)` is exactly
    the sum above, which is why `1/24`, `4/24`, `6/24`, `4/24`, `1/24` appear.
    """
    h = SPOT * delta
    k = vol_move
    return (
        COEFFS4["spot_x4"] * h**4
        + 4.0 * COEFFS4["spot_spot_spot_sigma"] * h**3 * k
        + 6.0 * COEFFS4["spot_spot_sigma_sigma"] * h * h * k * k
        + 4.0 * COEFFS4["spot_sigma_sigma_sigma"] * h * k**3
        + COEFFS4["sigma_sigma_sigma_sigma"] * k**4
    ) / 24.0


def cubic_column_error(delta: float, vol_move: float) -> float:
    """The truncation v1.5.0 publishes, called through that file so the two cannot drift."""
    return P15.truncated_column_error(delta, vol_move)


def quartic_column_error(delta: float, vol_move: float) -> float:
    """The same truncation with the order-four piece added, and nothing else changed."""
    return cubic_column_error(delta, vol_move) + quartic_column_term(delta, vol_move)


def priced_column_error(delta: float, vol_move: float) -> float:
    """The shipped map's error at one joint move, measured through the engine."""
    return P15.exact_move(delta, vol_move) - P15.engine_pnl(delta, vol_move, P15.BASE)


def zeros(function: Callable[[float], float], points: int) -> list[float]:
    """Every zero of `function` over the swept volatility range, by v1.5.0's shared routine."""
    return P15._sign_change_roots(function, min(VOL_MOVES), max(VOL_MOVES), points)


def nearest(first: list[float], second: list[float]) -> float | None:
    """The smallest distance between two sets of zeros, or None if either set is empty."""
    if not first or not second:
        return None
    return min(abs(a - b) for a in first for b in second)


def column_row(delta: float) -> dict[str, Any]:
    """Claims 2 and 3 for one `delta` column: where each truncation puts the crossing.

    The counts and the positions sit in the same row because they answer the same question, but they
    are not equally portable: the counts are verdicts and the positions are roots of a cancellation,
    so `reproduction_policy` puts them in different classes rather than the row doing it.
    """
    measured = zeros(P15.measured_error_on_column(delta), MEASURED_SCAN)
    cubic = zeros(lambda k: cubic_column_error(delta, k), SCAN)
    quartic = zeros(lambda k: quartic_column_error(delta, k), SCAN)
    return {
        "delta": delta,
        # Full precision, not rounded: a zero re-evaluated at ten decimals sits 5e-11 off the root,
        # and on a column whose error runs at 3e5 per vol point that reads as a 1.6e-5 residual at a
        # zero the finder placed to 1e-16. The CSV rounds for readers; the JSON does not.
        "measured_zeros": list(measured),
        "cubic_zeros": list(cubic),
        "quartic_zeros": list(quartic),
        "measured_zero_count": len(measured),
        "cubic_zero_count": len(cubic),
        "quartic_zero_count": len(quartic),
        "cubic_nearest_zero_distance": nearest(cubic, measured),
        "quartic_nearest_zero_distance": nearest(quartic, measured),
        "cubic_nearest_predicted_zero": _pair(cubic, measured),
        "quartic_nearest_predicted_zero": _pair(quartic, measured),
        "priced_error_at_nearest_measured_zero": (
            min(abs(priced_column_error(delta, k)) for k in measured) if measured else None
        ),
    }


def _pair(predicted: list[float], measured: list[float]) -> list[float] | None:
    """The predicted/measured pair that realises the nearest distance, for the printed row."""
    if not predicted or not measured:
        return None
    best = min(((abs(a - b), a, b) for a in predicted for b in measured), key=lambda t: t[0])
    return [best[1], best[2]]


def ray_rows(direction: tuple[float, float]) -> list[dict[str, Any]]:
    r"""Claim 1 for one joint-shock ray: the residual of each truncation, scaled down.

    Both residuals are differences of quantities near the book value, so each row carries its own
    magnitude next to its ratio; the ratio is the quantity that can be compared across rays without
    arguing about units.
    """
    base_delta, base_move = direction
    rows = []
    for scale in SCALES:
        delta, move = base_delta * scale, base_move * scale
        priced = priced_column_error(delta, move)
        cubic = cubic_column_error(delta, move)
        quartic = cubic_column_error(delta, move) + quartic_column_term(delta, move)
        rows.append(
            {
                "scale": scale,
                "delta": delta,
                "vol_move": move,
                "priced_error": priced,
                "cubic_truncation": cubic,
                "quartic_truncation": quartic,
                "order_four_piece": quartic - cubic,
                "residual_after_cubic": priced - cubic,
                "residual_after_quartic": priced - quartic,
                "residual_ratio_quartic_over_cubic": (
                    (priced - quartic) / (priced - cubic) if priced != cubic else None
                ),
            }
        )
    return rows


def ray_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """The slopes and the floor claim that a ray's seven rows add up to."""
    scales = [row["scale"] for row in rows]
    after_cubic = [row["residual_after_cubic"] for row in rows]
    after_quartic = [row["residual_after_quartic"] for row in rows]
    ratios = [
        abs(row["residual_ratio_quartic_over_cubic"])
        for row in rows
        if row["residual_ratio_quartic_over_cubic"] is not None
    ]
    window = [
        (scale, ratio)
        for scale, ratio in zip(scales, ratios, strict=True)
        if FIT_FLOOR <= scale <= ORDERING_CEILING
    ]
    narrow_scales = [scale for scale, _ in window]
    narrow_ratios = [ratio for _, ratio in window]
    slope, standard_error = _log_log_of(narrow_scales, narrow_ratios)

    def windowed(low: float, high: float, values: list[float]) -> tuple[float, float]:
        kept = [
            (scale, value)
            for scale, value in zip(scales, values, strict=True)
            if low <= scale <= high
        ]
        return _log_log_of([scale for scale, _ in kept], [value for _, value in kept])

    # The gated fit, and the ungated one through the floor, published together so the choice of
    # window is auditable rather than asserted.
    cubic_slope, cubic_se = windowed(FIT_FLOOR, ORDERING_CEILING, after_cubic)
    quartic_slope, quartic_se = windowed(FIT_FLOOR, ORDERING_CEILING, after_quartic)
    cubic_through_floor, _ = windowed(min(scales), 0.03, after_cubic)
    quartic_through_floor, _ = windowed(min(scales), 0.03, after_quartic)
    ordered = sorted(zip(scales, ratios, strict=True))
    return {
        "scales": scales,
        "residual_after_cubic": after_cubic,
        "residual_after_quartic": after_quartic,
        "residual_ratio_quartic_over_cubic": ratios,
        "residual_slope_after_cubic": cubic_slope,
        "residual_slope_after_cubic_standard_error": cubic_se,
        "residual_slope_after_quartic": quartic_slope,
        "residual_slope_after_quartic_standard_error": quartic_se,
        "residual_slope_cubic_through_the_floor": cubic_through_floor,
        "residual_slope_quartic_through_the_floor": quartic_through_floor,
        "ratio_slope_over_the_above_floor_window": slope,
        "ratio_slope_standard_error": standard_error,
        "ratio_at_grid_size": ordered[-1][1] if ordered else None,
        "ratio_at_the_fit_floor": next(
            (ratio for scale, ratio in ordered if scale == FIT_FLOOR), None
        ),
        "ratio_smallest": min(ratios) if ratios else None,
        "ratio_largest": max(ratios) if ratios else None,
        "ratio_monotone_down_to_the_floor": all(
            ordered[index][1] >= ordered[index + 1][1]
            for index in range(len(ordered) - 1)
            if ordered[index + 1][0] >= FIT_FLOOR
        ),
        "floor_turnaround": bool(
            ordered and ordered[0][0] < FIT_FLOOR and ordered[0][1] > ordered[1][1]
        ),
    }


def _log_log_of(x_values: list[float], y_values: list[float]) -> tuple[float, float]:
    """Slope and standard error of `log |y|` against `log x`, for pairs that are both nonzero."""
    pairs = [
        (math.log(x), math.log(abs(y)))
        for x, y in zip(x_values, y_values, strict=True)
        if x > 0.0 and abs(y) > 0.0
    ]
    if len(pairs) < 2:  # pragma: no cover - the ray always offers three points
        return float("nan"), float("nan")
    mean_x = sum(x for x, _ in pairs) / len(pairs)
    mean_y = sum(y for _, y in pairs) / len(pairs)
    denominator = sum((x - mean_x) ** 2 for x, _ in pairs)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in pairs) / denominator
    intercept = mean_y - slope * mean_x
    spread = sum((y - (slope * x + intercept)) ** 2 for x, y in pairs)
    return slope, math.sqrt(spread / denominator / (len(pairs) - 2))


def published_scenario_block() -> dict[str, Any]:
    r"""Claim 4: what each truncation says the error is at the size the documents quote.

    Both the shipped map and the re-struck map of v1.5.0 are read, because the recommendation the
    next order might sharpen is the re-strike, and a predictor that improves the crossing of one map
    while still missing the amount of both is the honest summary.
    """
    scenario = P15.published_scenario("risk_off")
    delta, move = scenario["equity"], scenario["volatility"]
    cubic = cubic_column_error(delta, move)
    quartic = quartic_column_error(delta, move)
    priced_base = priced_column_error(delta, move)
    restrike_exposure = {
        **P15.BASE,
        "gamma": P15.totals(SPOT, VOLATILITY + move)["gamma"],
    }
    priced_restrike = P15.exact_move(delta, move) - P15.engine_pnl(delta, move, restrike_exposure)
    # The re-struck map's truncation: the same expansion, with the finite difference the engine
    # actually applies to the gamma exposure subtracted. That difference is not a Taylor term -- it
    # is `gamma(sigma + k) - gamma(sigma)` over the whole leg -- which is exactly why v1.5.0
    # measured 86 % rather than 100 % of the named term.
    removed = (
        (P15.totals(SPOT, VOLATILITY + move)["gamma"] - P15.totals(SPOT, VOLATILITY)["gamma"])
        * (SPOT * delta) ** 2
        / SPOT**2
    )
    return {
        "scenario": "risk_off",
        "delta": delta,
        "vol_move": move,
        "order_four_piece": quartic - cubic,
        "base_map": {
            "priced_error": priced_base,
            "cubic_truncation": cubic,
            "quartic_truncation": quartic,
            "cubic_relative_error": (cubic - priced_base) / abs(priced_base),
            "quartic_relative_error": (quartic - priced_base) / abs(priced_base),
        },
        "gamma_restrike_map": {
            "priced_error": priced_restrike,
            "cubic_truncation": cubic - removed,
            "quartic_truncation": quartic - removed,
            "cubic_relative_error": (cubic - removed - priced_restrike) / abs(priced_restrike),
            "quartic_relative_error": (quartic - removed - priced_restrike) / abs(priced_restrike),
        },
    }


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)

    # Gate 0: the order-four piece must be the closed form it says it is. At k = 0 the quartic
    # reduces to the pure-spot quartic, and the cubic must be untouched -- otherwise "the same
    # truncation plus four terms" would be a claim about a function this file edited.
    spot_quartic_gap = max(
        abs(
            quartic_column_error(delta, 0.0)
            - cubic_column_error(delta, 0.0)
            - COEFFS4["spot_x4"] * (SPOT * delta) ** 4 / 24.0
        )
        / max(1e-12, abs(COEFFS4["spot_x4"] * (SPOT * delta) ** 4 / 24.0))
        for delta in DELTAS
        if delta != 0.0
    )
    if spot_quartic_gap > 1e-12:
        raise RuntimeError(
            f"at k = 0 the order-four piece is not V_SSSS h^4 / 24: relative mismatch "
            f"{spot_quartic_gap:.3e}"
        )

    columns = [column_row(delta) for delta in DELTAS]
    inside = [
        row for row in columns if abs(row["delta"]) <= WIDENED_LIMIT and row["measured_zero_count"]
    ]
    missed = [
        row
        for row in inside
        if row["quartic_nearest_zero_distance"] is None
        or row["quartic_nearest_zero_distance"] > TOLERANCE
    ]
    if missed:
        offender = missed[0]
        raise RuntimeError(
            f"the quartic truncation's nearest zero is not the priced one inside |delta| <= "
            f"{WIDENED_LIMIT}: first at delta={offender['delta']} predicting "
            f"{offender['quartic_zeros']} "
            f"against a measured {offender['measured_zeros']}"
        )
    # The widening has to be widening: the cubic must actually fail where the quartic passes, or
    # gate 2 would be certifying a looser test rather than a better truncation.
    cubic_outside = [
        row
        for row in inside
        if abs(row["delta"]) > P15.SMALL_MOVE_LIMIT
        and (
            row["cubic_nearest_zero_distance"] is None
            or row["cubic_nearest_zero_distance"] > TOLERANCE
        )
    ]
    if len(cubic_outside) < 4:
        raise RuntimeError(
            f"the cubic was expected to miss the tolerance on at least four of the columns between "
            f"0.05 and {WIDENED_LIMIT}, and misses on {len(cubic_outside)}"
        )
    residual = max(
        (row["priced_error_at_nearest_measured_zero"] or 0.0 for row in columns), default=0.0
    )
    if residual > 1e-6:
        raise RuntimeError(f"a measured zero is not one: the priced error there is {residual:.3e}")

    rays = {label: ray_rows(direction) for label, direction in RAYS.items()}
    ray_stats = {label: ray_summary(rows) for label, rows in rays.items()}
    cubic_slopes = [stat["residual_slope_after_cubic"] for stat in ray_stats.values()]
    quartic_slopes = [stat["residual_slope_after_quartic"] for stat in ray_stats.values()]
    ratio_slopes = [stat["ratio_slope_over_the_above_floor_window"] for stat in ray_stats.values()]
    for label, stat in ray_stats.items():
        for order, value, band in (
            ("cubic", stat["residual_slope_after_cubic"], CUBIC_SLOPE_BAND),
            ("quartic", stat["residual_slope_after_quartic"], QUARTIC_SLOPE_BAND),
        ):
            if not band[0] <= value <= band[1]:
                named = "fourth" if order == "cubic" else "fifth"
                raise RuntimeError(
                    f"the {order} residual on {label} falls with slope {value:.3f}, outside the "
                    f"{band[0]}-{band[1]} band that makes it a {named}-order remainder"
                )
        quartic = stat["residual_slope_after_quartic"]
        cubic = stat["residual_slope_after_cubic"]
        if quartic - cubic <= MINIMUM_SLOPE_SEPARATION:
            raise RuntimeError(
                f"the quartic residual on {label} falls only {quartic - cubic:.3f} orders faster "
                f"than the cubic ({quartic:.3f} against {cubic:.3f}): the added piece is not one "
                "order higher"
            )
    not_improved = [
        (label, row["scale"])
        for label, rows in rays.items()
        for row in rows
        if FIT_FLOOR <= row["scale"] <= ORDERING_CEILING
        and row["residual_ratio_quartic_over_cubic"] is not None
        and abs(row["residual_ratio_quartic_over_cubic"]) >= 1.0
    ]
    if not_improved:
        raise RuntimeError(
            f"the order-four piece does not reduce the residual at every scale in the ordering "
            f"window: {not_improved}"
        )
    # At grid size the same comparison is published rather than gated, because on one of the four
    # rays it goes the other way: the quartic is then a worse estimate of the *amount* even where it
    # is a better estimate of the *place*. A gate that reached to scale 1.0 would silently define
    # "ordering" to mean "the three rays that behave".
    overshoot = {
        label: stat["ratio_at_grid_size"]
        for label, stat in ray_stats.items()
        if stat["ratio_at_grid_size"] is not None and abs(stat["ratio_at_grid_size"]) >= 1.0
    }
    # The ratio's fitted slope is reported, never gated: it is a quotient of two residuals
    # that are themselves subtraction noise, so its slack is platform-dependent in the same
    # way the slope bands were -- the runner put the shallow ray at 0.381 where this machine
    # measures 0.71. What is gated instead is order-of-magnitude free: the ratio must fall as
    # the shock shrinks over the three largest above-floor scales, where the residuals are
    # far enough from the floor for the comparison to mean the same thing on any machine.
    for label, rows in rays.items():
        # Magnitudes, because the sign of the ratio says which side of the crossing the
        # residual landed on, not how large it is: the crash ray's ratio runs -0.159 to
        # -0.014, which is a fourteen-fold *reduction* in a shrinking shock.
        sequence = [
            abs(row["residual_ratio_quartic_over_cubic"])
            for scale in (ORDERING_CEILING, 0.1, 0.03)
            for row in rows
            if row["scale"] == scale
        ]
        if any(a <= b for a, b in zip(sequence, sequence[1:], strict=False)):
            raise RuntimeError(
                f"the residual ratio does not fall as the shock shrinks on {label}: "
                f"{[f'{value:.4f}' for value in sequence]}"
            )

    published = published_scenario_block()

    distances_quartic = [
        row["quartic_nearest_zero_distance"]
        for row in columns
        if row["quartic_nearest_zero_distance"]
    ]
    distances_cubic = [
        row["cubic_nearest_zero_distance"] for row in columns if row["cubic_nearest_zero_distance"]
    ]
    beyond = [row for row in columns if abs(row["delta"]) > WIDENED_LIMIT]
    beyond_quartic = [
        row["quartic_nearest_zero_distance"]
        for row in beyond
        if row["quartic_nearest_zero_distance"]
    ]
    beyond_cubic = [
        row["cubic_nearest_zero_distance"] for row in beyond if row["cubic_nearest_zero_distance"]
    ]
    count_disagree_cubic = [
        row["delta"] for row in columns if row["cubic_zero_count"] != row["measured_zero_count"]
    ]
    count_disagree_quartic = [
        row["delta"] for row in columns if row["quartic_zero_count"] != row["measured_zero_count"]
    ]

    # Everything in `fits` is a statistic estimated on residuals that are themselves cancellation
    # products, a root located in one by bisection, or a percentage of either. It is gathered under
    # one key so the reproduction gate can exempt it *by family*: each of the three rounds that went
    # red went red on a conditioning-limited field whose name had not been written on a list, and
    # hand-picking names is what made that possible. A fitted number added later belongs in `fits`
    # because that is where it is computed, not because someone remembered a list.
    fits = {
        "cubic_distance_max_within_the_published_limit": max(
            (
                row["cubic_nearest_zero_distance"]
                for row in columns
                if abs(row["delta"]) <= P15.SMALL_MOVE_LIMIT and row["cubic_nearest_zero_distance"]
            ),
            default=None,
        ),
        "quartic_distance_max_within_the_published_limit": max(
            (
                row["quartic_nearest_zero_distance"]
                for row in columns
                if abs(row["delta"]) <= P15.SMALL_MOVE_LIMIT
                and row["quartic_nearest_zero_distance"]
            ),
            default=None,
        ),
        "quartic_distance_max_within_the_widened_limit": max(
            (
                row["quartic_nearest_zero_distance"]
                for row in inside
                if row["quartic_nearest_zero_distance"]
            ),
            default=None,
        ),
        "cubic_distance_max_within_the_widened_limit": max(
            (
                row["cubic_nearest_zero_distance"]
                for row in inside
                if row["cubic_nearest_zero_distance"]
            ),
            default=None,
        ),
        "quartic_distance_max_beyond_the_widened_limit": max(beyond_quartic, default=None),
        "cubic_distance_max_beyond_the_widened_limit": max(beyond_cubic, default=None),
        "improvement_factor_at_the_widened_limit": (
            max(
                row["cubic_nearest_zero_distance"]
                for row in inside
                if abs(row["delta"]) > P15.SMALL_MOVE_LIMIT and row["cubic_nearest_zero_distance"]
            )
            / max(
                row["quartic_nearest_zero_distance"]
                for row in inside
                if abs(row["delta"]) > P15.SMALL_MOVE_LIMIT and row["quartic_nearest_zero_distance"]
            )
        ),
        "residual_slope_after_cubic": {
            label: ray_stats[label]["residual_slope_after_cubic"] for label in rays
        },
        "residual_slope_after_quartic": {
            label: ray_stats[label]["residual_slope_after_quartic"] for label in rays
        },
        "residual_slope_cubic_span": [min(cubic_slopes), max(cubic_slopes)],
        "residual_slope_quartic_span": [min(quartic_slopes), max(quartic_slopes)],
        "residual_slope_cubic_through_floor_span": [
            min(stat["residual_slope_cubic_through_the_floor"] for stat in ray_stats.values()),
            max(stat["residual_slope_cubic_through_the_floor"] for stat in ray_stats.values()),
        ],
        "residual_slope_quartic_through_floor_span": [
            min(stat["residual_slope_quartic_through_the_floor"] for stat in ray_stats.values()),
            max(stat["residual_slope_quartic_through_the_floor"] for stat in ray_stats.values()),
        ],
        "residual_slope_separation": {
            label: ray_stats[label]["residual_slope_after_quartic"]
            - ray_stats[label]["residual_slope_after_cubic"]
            for label in rays
        },
        "ratio_slope_span": [min(ratio_slopes), max(ratio_slopes)],
        "residual_ratio_at_grid_size_span": [
            min(stat["ratio_at_grid_size"] for stat in ray_stats.values()),
            max(stat["ratio_at_grid_size"] for stat in ray_stats.values()),
        ],
        "residual_ratio_at_the_fit_floor_span": [
            min(stat["ratio_at_the_fit_floor"] for stat in ray_stats.values()),
            max(stat["ratio_at_the_fit_floor"] for stat in ray_stats.values()),
        ],
        # Which rays turn their ratio back up below the arithmetic floor is decided by comparing two
        # values that *are* the floor's noise, so the count travels with the platform that
        # measured it.
        "rays_with_a_floor_turnaround": sum(
            1 for stat in ray_stats.values() if stat["floor_turnaround"]
        ),
        "residual_ratio_at_grid_size": {
            label: ray_stats[label]["ratio_at_grid_size"] for label in rays
        },
        "k_zero_order_four_relative_mismatch": spot_quartic_gap,
        "root_finder_largest_residual_at_a_measured_zero": residual,
        "nearest_zero_distance_quartic_all": distances_quartic,
        "nearest_zero_distance_cubic_all": distances_cubic,
    }

    headline = {
        "columns_swept": len(columns),
        "joint_shocks_per_column": len(VOL_MOVES),
        "measured_zeros_total": sum(row["measured_zero_count"] for row in columns),
        "cubic_zeros_total": sum(row["cubic_zero_count"] for row in columns),
        "quartic_zeros_total": sum(row["quartic_zero_count"] for row in columns),
        "columns_where_the_cubic_zero_count_disagrees": len(count_disagree_cubic),
        "columns_where_the_quartic_zero_count_disagrees": len(count_disagree_quartic),
        "cubic_count_disagreements": count_disagree_cubic,
        "quartic_count_disagreements": count_disagree_quartic,
        "widened_limit": WIDENED_LIMIT,
        "tolerance": TOLERANCE,
        "columns_the_cubic_misses_between_the_two_limits": [row["delta"] for row in cubic_outside],
        "minimum_slope_separation": MINIMUM_SLOPE_SEPARATION,
        "ordering_window": [FIT_FLOOR, ORDERING_CEILING],
        # The labels, not the ratios: at full shock size the worst margin against the 1.0
        # threshold is 8 %, while the residuals it is computed from are orders of magnitude above
        # the floor, so this classification is not a noise decision and is compared by value like
        # a verdict should be.
        "rays_where_the_quartic_is_worse_at_grid_size": sorted(overshoot),
        "rays_number_of": len(rays),
        "published_scenario": "risk_off",
        "published_base_priced_error": published["base_map"]["priced_error"],
        "published_base_cubic_relative_error": published["base_map"]["cubic_relative_error"],
        "published_base_quartic_relative_error": published["base_map"]["quartic_relative_error"],
        "published_restrike_cubic_relative_error": published["gamma_restrike_map"][
            "cubic_relative_error"
        ],
        "published_restrike_quartic_relative_error": published["gamma_restrike_map"][
            "quartic_relative_error"
        ],
        "published_order_four_piece": published["order_four_piece"],
        "fits": fits,
    }

    payload = {
        "generated_at_utc": utc_timestamp(),
        "command": "uv run python experiments/fourth_order_crossing_map/run.py",
        "claim": (
            "adding the four mixed fourth partials to the column truncation triples the radius over"
            "which it predicts the shipped map's crossing -- |delta| <= 0.15 against the cubic's "
            "0.05, worst distance 0.00162 against 0.01887 -- and the residual it leaves falls "
            "with a fifth-order slope of 4.73-5.01 against the cubic's 3.96-4.37, but it does not "
            "make the map's error cheaper to predict at the size the documents quote: on risk_off "
            "the quartic truncation is still 16.2 % wrong, on the other side, and on one ray at "
            "full shock size its residual is 1.38x the cubic's"
        ),
        "book": {
            "spot": SPOT,
            "rate": P15.RATE,
            "dividend_yield": P15.DIVIDEND_YIELD,
            "volatility": VOLATILITY,
            "maturity": P15.MATURITY,
            "strikes": list(P15.STRIKES),
            "quantity": P15.QUANTITY,
            "base_value": P15.BASE_VALUE,
            "source": "imported from experiments/restrike_gamma_map/run.py",
        },
        "coefficients": {
            "cubic": dict(P15.COEFFS),
            "fourth_order": COEFFS4,
            "note": (
                "book sums of raw partials at the base market, each multiplied by the position "
                "quantity; the cubic set is v1.5.0's and is read from that module, not recomputed"
            ),
        },
        "truncation": {
            "cubic": "v1.5.0's third-order column truncation, called through that experiment",
            "quartic": "the same plus (1/24) times the fourth directional derivative along (h, k)",
            "produced_by": (
                "quantrisk.stress.run_scenario for the priced side; closed forms for both"
                " truncations"
            ),
        },
        "headline": headline,
        "columns": columns,
        "rays": {label: {"rows": rows, **ray_stats[label]} for label, rows in rays.items()},
        "published_scenario": published,
        "refusals": {
            "radius_is_not_accuracy": (
                "claim 2 is about where the error crosses zero; claim 4 says the amount at "
                "published size is still 16.2 % off, so neither number may be quoted as the other"
            ),
            "one_book": (
                "every coefficient is a sum over this three-strike ladder at one maturity and one "
                "base vol; the radius is a property of that book's fourth-order terms"
            ),
            "zeros_are_sign_changes": (
                "a zero is a sign change located by bracketing on a scanned interval, not a proof "
                "that the priced error has a root there; the residual at each measured zero is "
                "published so the reader can see how sharp each one is"
            ),
            "floor_is_not_a_term": (
                "the residual ratio stops falling at scale 1e-3 because the subtraction reaches "
                "double precision on a book near 1.09e5, not because the fifth-order term vanished"
            ),
            "ordering_is_not_a_grid_size_claim": (
                "the ordering law is gated over scales from 3e-3 to 3e-1 of the published shock; "
                "at full size one ray's residual grows, so nothing here says the fourth order "
                "improves the estimate of an amount at the sizes the scenarios use"
            ),
            "counts_are_not_money": (
                "zero counts are per column and say nothing about how large the P&L is where they "
                "sit; the distance fields are in volatility points, not currency"
            ),
        },
        "reproduction_policy": {
            # Three families, no field names. A reproduction test can only compare a number by value
            # if the number *has* a cross-platform value, and nothing under these keys does: each
            # is a difference of book values near 1.09e5, a ratio of two such differences, a fit
            # over them, or a root located in one by bisection. The three CI rounds that went red
            # each went red on a field of exactly that kind which a hand-written list had not
            # named -- first a fitted slope, then the ratio's own standard error, then the two
            # residuals measured at the arithmetic floor -- so the exemption is declared where
            # the quantities are built rather than remembered afterwards.
            "conditioning_limited": ["rays", "columns", "headline.fits"],
            # Inside those families a *verdict* can be noise-decided too, and the shape-only rule
            # for floats does not reach it: `floor_turnaround` compares the two ratios that ARE
            # the subtraction floor, so which side of the comparison it lands on is the
            # platform's, not the model's. Counts and labels stay gated -- the zero counts that
            # carry claim 3 and the ray labels that carry the grid-size reversal are not noise
            # decisions and are not listed here.
            "noise_decided_verdicts": ["rays", "headline.fits"],
            "why": (
                "fits over residuals, ratios of two residuals, roots located by bisection, the "
                "percentages derived from them, and one verdict computed by  "
                "comparing two values at the arithmetic floor: each  "
                "reproduces to the conditioning of a subtraction near 1.09e5, "
                " not to its last digit. What IS still compared by value is  "
                "every count and label in `columns`, the published amounts,  "
                "the coefficient book sums, and this run's own gates, which  "
                "raise rather than publish a number outside their band"
            ),
            "everything_else": (
                "the two truncations and the order-four piece are closed  "
                "forms; the priced error and the engine P&L are exact  "
                "arithmetic on the shipped engine. Both appear outside the  "
                "exempt families too -- in `coefficients`, and as the  "
                "`priced_error`, `cubic_truncation`, `quartic_truncation` and "
                " `order_four_piece` of the risk_off row under  "
                "`published_scenario` -- so the closed forms are still  "
                "compared by value even where the per-ray and per-column  "
                "copies of them are not"
            ),
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "packages": {"quantrisk": quantrisk.version()},
        },
    }

    json_path = RESULTS / "fourth_order_crossing_map.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    write_csv(RESULTS / "fourth_order_crossing_columns.csv", columns)
    write_csv(
        RESULTS / "fourth_order_residual_rays.csv", [r for rows in rays.values() for r in rows]
    )

    cubic_span = fits["residual_slope_cubic_span"]
    quartic_span = fits["residual_slope_quartic_span"]
    print(
        f"quartic radius |delta| <= {WIDENED_LIMIT}: worst distance "
        f"{fits['quartic_distance_max_within_the_widened_limit']:.4f} "
        f"(cubic {fits['cubic_distance_max_within_the_widened_limit']:.4f}); "
        f"zeros measured {headline['measured_zeros_total']}, cubic "
        f"{headline['cubic_zeros_total']}, quartic {headline['quartic_zeros_total']}; "
        f"count disagreements {len(count_disagree_cubic)} -> {len(count_disagree_quartic)}"
    )
    print(
        f"residual ratio quartic/cubic: {fits['residual_ratio_at_grid_size_span'][0]:.3f}"
        f"-{fits['residual_ratio_at_grid_size_span'][1]:.3f} at grid size, "
        f"{fits['residual_ratio_at_the_fit_floor_span'][0]:.4f}"
        f"-{fits['residual_ratio_at_the_fit_floor_span'][1]:.4f} at scale {FIT_FLOOR}; "
        f"slopes {cubic_span[0]:.2f}-{cubic_span[1]:.2f} (cubic) against "
        f"{quartic_span[0]:.2f}-{quartic_span[1]:.2f} (quartic)"
    )
    print(
        f"risk_off: priced base {published['base_map']['priced_error']:.2f}, cubic "
        f"{published['base_map']['cubic_relative_error']:+.2%}, quartic "
        f"{published['base_map']['quartic_relative_error']:+.2%}; restrike cubic "
        f"{published['gamma_restrike_map']['cubic_relative_error']:+.2%}, quartic "
        f"{published['gamma_restrike_map']['quartic_relative_error']:+.2%}"
    )
    print(f"wrote {json_path.relative_to(REPO_ROOT)}")
    return 0


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, list):
        return "|".join(_cell(item) for item in value)
    if isinstance(value, float):
        return f"{value:.10g}"
    return str(value)


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
            writer.writerow({key: _cell(row.get(key)) for key in fields})


if __name__ == "__main__":
    raise SystemExit(main())
