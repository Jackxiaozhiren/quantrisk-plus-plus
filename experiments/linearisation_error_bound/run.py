#!/usr/bin/env python3
"""Phase 12 experiment: a Taylor remainder bound that predicts a sign change in published data.

    uv run python experiments/linearisation_error_bound/run.py
    uv run python scripts/run_benchmark_suite.py --only linearisation_error_bound

`experiments/stress_testing/results/linearisation_error.csv` freezes the measured error of the
delta-gamma P&L map against a full Black-Scholes re-pricing, and the prose shipped with it said the
error grows with the shock size. Its own numbers refute that: the absolute error is 649.5 at a 10 %
down move and 528.5 at 20 %. A trend statement was simply the wrong shape for this object.

The right object is the Lagrange remainder, derived in
`docs/analysis/delta_gamma_error_bound.md`. For a map that keeps terms through order two,

    R(delta) = (1/6) * V'''(xi) * h**3,        h = S * delta,

for some `xi` strictly between the base and shocked spot. That is not an inequality to be checked in
absolute value -- it traps the *coefficient* `c(delta) = 6R/h**3` between the minimum and maximum of
`V'''` along the path, which is a far sharper claim and would be refuted by the closed form for
`V'''` itself if that form were wrong. Five things are asserted here, each of which could have
failed:

  A. `c(delta) -> V'''(S)` as the shock shrinks, and `log|R|` against `log|delta|` has slope 3;
  B. `c(delta)` lies inside the segment's range of `V'''` for every shock, up and down;
  C. for a down shock the ladder's `V'''` changes sign along the path, so `c` does, so **the
     remainder changes sign** -- the map is nearly exactly right at one specific shock size;
  D. for an up shock nothing crosses and `|R|` really is monotone, so the asymmetry in the published
     curve is a consequence of the closed form rather than of where the sweep happened to land.

No oracle is called: a bound is not a second implementation of a price. The book is copied from the
committed stress sweep so the remainder measured here *is* the published error, not a re-derivation
of it.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import quantrisk
from quantrisk.experiments.metadata import (
    artifact_manifest,
    environment,
    package_versions,
    repo_relative,
    utc_timestamp,
)

RESULTS = Path(__file__).resolve().parent / "results"

SPOT = 100.0
RATE = 0.03
DIVIDEND_YIELD = 0.0
VOLATILITY = 0.20
MATURITY = 0.5
STRIKES = (90.0, 100.0, 110.0)
QUANTITY = 5000.0

# The committed sweep's own shock sizes, so domination and the sign change are checked at exactly
# the grid a reader can compare against.
SWEEP = (0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.40)

# Where the departure from the cubic term is compared against the quartic prediction. Below about
# 3e-5 this book's remainder (|R| ~ 1e-9 against a value near 2.6e4) is at the spacing of the double
# format and the ratio detaches; the window starts an order of magnitude above that.
CORRECTION_DELTAS_NOTE = "1e-3 ... 1e-2"

# Points used for the supremum/infimum of V''' along the segment, and for the dense sign sweep.
SEGMENT_GRID = 601
DENSE_SHOCKS = 300
DENSE_CEILING = 0.499


def market(spot: float) -> quantrisk.pricing.MarketParams:
    return quantrisk.pricing.MarketParams(
        spot=spot,
        rate=RATE,
        dividend_yield=DIVIDEND_YIELD,
        volatility=VOLATILITY,
        maturity=MATURITY,
    )


def option(strike: float, put: bool = False) -> quantrisk.pricing.EuropeanOption:
    kind = quantrisk.pricing.OptionType.PUT if put else quantrisk.pricing.OptionType.CALL
    return quantrisk.pricing.EuropeanOption(kind, strike)


def book_value(spot: float) -> float:
    return (
        sum(
            quantrisk.pricing.black_scholes(option(strike), market(spot)).price
            for strike in STRIKES
        )
        * QUANTITY
    )


def book_delta(spot: float) -> float:
    return (
        sum(
            quantrisk.pricing.black_scholes_greeks(option(strike), market(spot)).delta
            for strike in STRIKES
        )
        * QUANTITY
    )


def book_gamma(spot: float) -> float:
    return (
        sum(
            quantrisk.pricing.black_scholes_greeks(option(strike), market(spot)).gamma
            for strike in STRIKES
        )
        * QUANTITY
    )


def book_speed(spot: float) -> float:
    """Aggregate third spot derivative -- the coefficient the whole analysis is built from."""
    return (
        sum(
            quantrisk.pricing.black_scholes_spot_derivatives(option(strike), market(spot)).third
            for strike in STRIKES
        )
        * QUANTITY
    )


def book_quartic(spot: float) -> float:
    return (
        sum(
            quantrisk.pricing.black_scholes_spot_derivatives(option(strike), market(spot)).fourth
            for strike in STRIKES
        )
        * QUANTITY
    )


def mapped_pnl(delta: float) -> float:
    """The engine's map (1): linear plus convexity, both sensitivities at the unshocked market."""
    shift = SPOT * delta
    return book_delta(SPOT) * shift + 0.5 * book_gamma(SPOT) * shift * shift


def exact_pnl(delta: float) -> float:
    return book_value(SPOT * (1.0 + delta)) - book_value(SPOT)


def remainder(delta: float) -> float:
    """The Lagrange remainder `R = [V(S+h) - V(S)] - m(delta)` -- the sign under which Taylor's
    theorem reads with a plus, which is what makes (4)'s inclusion two-sided rather than absolute.

    The committed CSV's `abs_error` is the negative of this (mapped minus revalued). No magnitude,
    ratio or zero below changes; it is stated because the two artifacts are meant to be read
    against each other line by line.
    """
    return exact_pnl(delta) - mapped_pnl(delta)


def segment_extremes(delta: float) -> tuple[float, float]:
    shift = SPOT * delta
    grid = np.linspace(SPOT, SPOT + shift, SEGMENT_GRID)
    values = [book_speed(float(spot)) for spot in grid]
    return min(values), max(values)


def lagrange_coefficient(delta: float) -> float:
    """c(delta) = 6R/h^3, the value the theorem says equals V''' at some point of the segment."""
    shift = SPOT * delta
    return 6.0 * remainder(delta) / shift**3


def bound(delta: float) -> float:
    low, high = segment_extremes(delta)
    return max(abs(low), abs(high)) / 6.0 * abs(SPOT * delta) ** 3


def solve_speed_zero(lo: float, hi: float) -> float:
    """Bisect the ladder's V''' along the path. Sign is monotone-checked by the caller."""
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if book_speed(SPOT * (1.0 + lo)) * book_speed(SPOT * (1.0 + mid)) <= 0.0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def solve_remainder_zero(direction: float, ceiling: float) -> float | None:
    """Where the signed remainder itself passes through zero, by bracket then bisection."""
    sizes = np.linspace(1e-4, ceiling, 4000)
    values = [remainder(direction * float(size)) for size in sizes]
    for index in range(1, len(values)):
        if values[index - 1] == 0.0 or values[index - 1] * values[index] < 0.0:
            lo, hi = float(sizes[index - 1]), float(sizes[index])
            for _ in range(200):
                mid = 0.5 * (lo + hi)
                if remainder(direction * lo) * remainder(direction * mid) <= 0.0:
                    hi = mid
                else:
                    lo = mid
            return 0.5 * (lo + hi)
    return None


def fit_slope(moves: list[float], floor: float, ceiling: float) -> dict[str, float]:
    """Least squares of log|R| on log|move| for one direction, over a stated window.

    Per direction rather than pooled, and over a window whose shrinkage is reported rather than
    asserted away. An up move and a down move of the same size have different remainders, because
    the segment each traverses sits differently against the sign change in the cubic coefficient, so
    a single fit through both measures a mixture. Pooling also manufactures false precision here:
    the first version fitted three points per direction, called the residual scatter a "standard
    error", and reported 3.037 +/- 0.003 -- eleven sigma from the theory value, where the eleven
    sigma were entirely the up/down separation showing up as curvature.
    """
    sizes = np.array([abs(move) for move in moves], dtype=float)
    # Indexed by `moves`, not by `sizes`: taking the absolute value first would silently fit the
    # same curve twice and report it as two directions.
    errors = np.array([abs(remainder(move)) for move in moves], dtype=float)
    keep = (sizes >= floor) & (sizes <= ceiling) & (errors > 0.0)
    x, y = np.log(sizes[keep]), np.log(errors[keep])
    slope, intercept = np.polyfit(x, y, 1)
    residual = y - (slope * x + intercept)
    n = int(keep.sum())
    standard_error = math.sqrt(
        float((residual**2).sum()) / (n - 2) / float(((x - x.mean()) ** 2).sum())
    )
    return {
        "slope": float(slope),
        "standard_error": standard_error,
        "theory": 3.0,
        "deviation_in_standard_errors": float((slope - 3.0) / standard_error),
        "observations": n,
        "window": [floor, ceiling],
    }


# Windows whose upper end shrinks toward the base point. The fitted slope must approach 3 along
# this sequence: at any fixed window the quartic term biases it, and the bias is proportional to the
# window's top edge. Reporting the sequence is the honest version of "the slope is 3" -- the single
# number invites the reader to treat a window choice as a measurement.
SLOPE_WINDOWS = ((2e-3, 2e-2), (1e-3, 5e-3), (5e-4, 2e-3), (2e-4, 1e-3), (2e-4, 5e-4))

# A dense shock grid for the fits and the sign sweep, so the slope is estimated from hundreds of
# points rather than the nine swept ones. The sweep rows stay at the published sizes, because those
# are what a reader can compare against.
GRID_FLOOR = 2e-4
GRID_CEILING = 0.499
GRID_POINTS = 900


def dense_grid() -> tuple[list[float], list[float]]:
    sizes = list(np.geomspace(GRID_FLOOR, GRID_CEILING, GRID_POINTS))
    return [-size for size in sizes], sizes


def quartic_correction_prediction() -> float:
    """Where `(R - cubic)/cubic` should sit, per unit of delta, as delta -> 0.

    Dividing R = (1/6)V'''h^3 + (1/24)V''''h^4 + O(h^5) by the cubic term gives a leading
    correction of `(V''''/(4 V''')) * S * delta`. So the ratio of the observed departure to delta
    must converge to that constant -- which validates the *fourth*-derivative closed form through
    the remainder, independently of any finite difference of it.
    """
    return SPOT * book_quartic(SPOT) / (4.0 * book_speed(SPOT))


def measured_quartic_correction(delta: float) -> float:
    shift = SPOT * delta
    cubic = book_speed(SPOT) / 6.0 * shift**3
    if cubic == 0.0:
        return float("nan")
    return (remainder(delta) - cubic) / cubic / delta


def sweep_row(direction: str, magnitude: float) -> dict[str, Any]:
    delta = magnitude if direction == "up" else -magnitude
    error = remainder(delta)
    low, high = segment_extremes(delta)
    envelope = bound(delta)
    coefficient = lagrange_coefficient(delta)
    shift = SPOT * delta
    return {
        "direction": direction,
        "move": magnitude,
        "delta": delta,
        "mapped_pnl": mapped_pnl(delta),
        "revalued_pnl": exact_pnl(delta),
        "remainder_signed": error,
        "mapped_minus_revalued": -error,
        "abs_remainder": abs(error),
        "lagrange_coefficient": coefficient,
        "segment_speed_min": low,
        "segment_speed_max": high,
        "coefficient_inside_segment_range": low - 1e-8 <= coefficient <= high + 1e-8,
        "abs_bound": envelope,
        "remainder_over_bound": abs(error) / envelope if envelope else float("nan"),
        "cubic_prediction_at_base_spot": book_speed(SPOT) / 6.0 * shift**3,
        "remainder_over_cubic_prediction": (
            error / (book_speed(SPOT) / 6.0 * shift**3) if shift else float("nan")
        ),
        "quartic_prediction_at_base_spot": book_quartic(SPOT) / 24.0 * shift**4,
        "book_speed_at_base_spot": book_speed(SPOT),
        "book_speed_at_shocked_spot": book_speed(SPOT * (1.0 + delta)),
    }


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)

    rows = [sweep_row("down", move) for move in SWEEP] + [sweep_row("up", move) for move in SWEEP]

    # A. asymptotics: the slope, per direction, and its convergence as the window shrinks
    down_dense, up_dense = dense_grid()
    fitted = {
        direction: [
            fit_slope(down_dense if direction == "down" else up_dense, floor, ceiling)
            for floor, ceiling in SLOPE_WINDOWS
        ]
        for direction in ("down", "up")
    }
    smallest = min(rows, key=lambda row: row["move"])
    leading_agreement = abs(smallest["remainder_over_cubic_prediction"] - 1.0)
    for direction, series in fitted.items():
        widest, narrowest = series[0]["slope"], series[-1]["slope"]
        if abs(widest - 3.0) > 0.1:
            raise RuntimeError(
                f"the {direction}-move remainder's fitted log-log slope is {widest:.5f}, not ~3: "
                "the map is not second order, or the fit window no longer brackets it"
            )
        # Shrinking the window must move the estimate toward the theory value. If it does not, the
        # "convergence" story is a story about one lucky window.
        if abs(narrowest - 3.0) >= abs(widest - 3.0):
            raise RuntimeError(
                f"{direction}: the narrowest window ({narrowest:.5f}) is no closer to 3 than the "
                f"widest ({widest:.5f}), so the residual bias is not the higher-order term"
            )
        previous = None
        for values in series:
            if previous is not None and abs(values["slope"] - 3.0) > abs(previous - 3.0) + 1e-9:
                raise RuntimeError(
                    f"{direction}: the slope estimate moved away from 3 as the window shrank "
                    f"({previous:.6f} -> {values['slope']:.6f})"
                )
            previous = values["slope"]

    # A second, independent consequence of the closed forms: the quartic's fingerprint on the
    # departure from the cubic term.
    predicted_correction = quartic_correction_prediction()
    correction_deltas = (1e-3, 2e-3, 5e-3, 1e-2)
    measured_correction = {
        direction: [measured_quartic_correction(sign * delta) for delta in correction_deltas]
        for direction, sign in (("down", -1.0), ("up", 1.0))
    }
    for direction, values in measured_correction.items():
        closest = min(
            abs(value - predicted_correction) / abs(predicted_correction) for value in values
        )
        if closest > 0.02:
            raise RuntimeError(
                f"{direction}: the departure from the cubic term does not converge to "
                f"S*V''''/(4*V''') = {predicted_correction:.6f}; nearest observed {closest:.4%} off"
            )
    if leading_agreement > 0.02:
        raise RuntimeError(
            f"at the smallest swept move the remainder is not the cubic term of (5): ratio "
            f"{smallest['remainder_over_cubic_prediction']:.6f}"
        )

    # B. the sharp inclusion, on the sweep and on a dense grid in both directions
    violations = [row for row in rows if not row["coefficient_inside_segment_range"]]
    dense_violations: list[dict[str, float]] = []
    for direction in (-1.0, 1.0):
        for magnitude in np.linspace(1e-3, DENSE_CEILING, DENSE_SHOCKS):
            delta = direction * float(magnitude)
            coefficient = lagrange_coefficient(delta)
            low, high = segment_extremes(delta)
            if not low - 1e-8 <= coefficient <= high + 1e-8:
                dense_violations.append(
                    {
                        "move": float(magnitude),
                        "direction": "up" if direction > 0 else "down",
                        "coefficient": coefficient,
                        "segment_min": low,
                        "segment_max": high,
                    }
                )
    if violations or dense_violations:
        raise RuntimeError(
            "the Lagrange coefficient escaped the segment's range of V''', which refutes either "
            f"the closed form (5) or the regularity check: {len(violations)} swept and "
            f"{len(dense_violations)} dense violations, first: "
            f"{(violations or dense_violations)[0]}"
        )
    ratios = [row["remainder_over_bound"] for row in rows]
    if max(ratios) > 1.0:
        raise RuntimeError(f"the absolute bound was violated: ratio {max(ratios):.6f}")
    # Away from the remainder's own zero the envelope has to be close, or it is a loose inequality
    # rather than a bound worth publishing. Near that zero |R| tends to 0 while the supremum of the
    # cubic coefficient over the segment does not, so the ratio there collapses by construction --
    # correct behaviour, reported separately instead of folded into one minimum.
    away_ratios = [
        row["remainder_over_bound"]
        for row in rows
        if not (row["direction"] == "down" and 0.15 <= row["move"] <= 0.30)
    ]
    if min(away_ratios) < 0.2:
        raise RuntimeError(
            f"the bound is vacuous away from the predicted zero: tightest {min(away_ratios):.4f}"
        )

    # C. the sign change down the path, and the remainder zero it predicts
    speed_at_base = book_speed(SPOT)
    speed_at_deep = book_speed(SPOT * (1.0 - 0.9))
    speed_crossing: dict[str, Any] = {"crossing_found": speed_at_base * speed_at_deep <= 0.0}
    predicted_remainder_zero: float | None = None
    observed_signed_reversal = next(
        (
            (rows[index]["move"], rows[index - 1]["move"])
            for index in range(1, len(rows))
            if rows[index]["direction"] == "down"
            and rows[index - 1]["direction"] == "down"
            and rows[index]["remainder_signed"] * rows[index - 1]["remainder_signed"] < 0.0
        ),
        None,
    )
    if speed_crossing["crossing_found"]:
        move_at = solve_speed_zero(-0.9, -1e-6)
        speed_crossing.update(
            {
                "move": abs(move_at),
                "signed_delta": move_at,
                "spot": SPOT * (1.0 + move_at),
                "speed_either_side": [
                    book_speed(SPOT * (1.0 + move_at * 0.999)),
                    book_speed(SPOT * (1.0 + move_at * 1.001)),
                ],
            }
        )
        predicted_remainder_zero = solve_remainder_zero(-1.0, 0.49)
    if predicted_remainder_zero is None:
        raise RuntimeError(
            "the theory says a down-shock remainder zero exists between the swept grid points "
            "because V''' changes sign along the path; none was found, so either the closed form "
            "is wrong or the published curve is not what this describes"
        )
    if observed_signed_reversal is None:
        raise RuntimeError(
            "the committed sweep's own sign reversal disappeared; the artifact this experiment is "
            "meant to explain has changed underneath it"
        )
    high_move, low_move = observed_signed_reversal
    if not low_move < predicted_remainder_zero < high_move:
        raise RuntimeError(
            f"the predicted remainder zero at {predicted_remainder_zero:.4f} lies outside the "
            f"published bracket ({low_move}, {high_move}) -- the prediction failed"
        )

    # D. the up direction must *not* cross, or the asymmetry is a sweep artefact
    up_coefficients = [row["lagrange_coefficient"] for row in rows if row["direction"] == "up"]
    if any(
        first * second <= 0.0
        for first, second in zip(up_coefficients, up_coefficients[1:], strict=False)
    ):
        raise RuntimeError(
            "the up-move Lagrange coefficient changed sign, so the published curve's asymmetry "
            "between up and down is not the consequence of (5) this claims it is"
        )
    up_magnitudes = [row["abs_remainder"] for row in rows if row["direction"] == "up"]
    if up_magnitudes != sorted(up_magnitudes):
        raise RuntimeError(
            "the up-move |R| is not monotone in the shock, contradicting prediction D"
        )

    figure_path = RESULTS / "linearisation_bound.png"
    figure_status = make_figure(rows, speed_crossing, figure_path)

    csv_path = RESULTS / "linearisation_bound.csv"
    fields = sorted({key for row in rows for key in row})
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    payload: dict[str, Any] = {
        "phase": "12 - linearisation error bound",
        "generated_utc": utc_timestamp(),
        "command": "uv run python experiments/linearisation_error_bound/run.py",
        "question": (
            "The stress layer's delta-gamma map has a published error curve, and the prose shipped "
            "with it said the error grows with the shock. Is there a Lagrange remainder "
            "bound that does better than restate the curve -- that traps the coefficient, and that "
            "predicts the feature the prose got wrong?"
        ),
        "result": "yes. The coefficient 6R/h^3 stays inside the path's range of V''' at every "
        "shock tested, and the sign change of V''' down the path predicts the remainder's own zero "
        "inside the bracket the published sweep already contains",
        "book": {
            "spot": SPOT,
            "rate": RATE,
            "dividend_yield": DIVIDEND_YIELD,
            "volatility": VOLATILITY,
            "maturity": MATURITY,
            "strikes": list(STRIKES),
            "quantity": QUANTITY,
            "statement": "the same three-call ladder as experiments/stress_testing's linearisation "
            "sweep, deliberately: the remainder measured here must be the published error and not "
            "a fresh derivation of it",
        },
        "proposition": {
            "map": "m(delta) = book_delta(S) * S*delta + 0.5 * book_gamma(S) * (S*delta)^2",
            "lagrange_form": "R(delta) = (1/6) * V'''(xi) * (S*delta)^3 for some xi strictly "
            "between S and S(1+delta)",
            "sharp_inclusion": "min_[S,M] V''' <= 6R/(S*delta)^3 <= max_[S,M] V'''",
            "absolute_form": "|R| <= (1/6) * sup_[S,M] |V'''| * |S*delta|^3",
            "closed_forms": {
                "third": "V''' = -(Gamma/S) * (1 + d1/(sigma*sqrt(T)))",
                "fourth": "V'''' = (Gamma/S^2) * (A^2 + A - 1/v^2), where "
                "A = 1 + d1/v and v = sigma*sqrt(T)",
            },
            "regularity": "S > 0, strike > 0, sigma*sqrt(T) > 0, delta > -1, segment bounded away "
            "from S = 0. In the sigma -> 0 / T -> 0 limits the core returns zero for every higher "
            "derivative and the bound becomes 0 <= 0: true, vacuous, and the map is exact off the "
            "kink anyway",
            "proof": "docs/analysis/delta_gamma_error_bound.md section 3",
        },
        "headline": {
            "all_predictions_held": True,
            "fitted_cubic_slope_widest_window_down": fitted["down"][0]["slope"],
            "fitted_cubic_slope_widest_window_up": fitted["up"][0]["slope"],
            "fitted_cubic_slope_narrowest_window_down": fitted["down"][-1]["slope"],
            "fitted_cubic_slope_narrowest_window_up": fitted["up"][-1]["slope"],
            "slope_converges_to_theory_as_the_window_shrinks": True,
            "theory_slope": 3.0,
            "quartic_correction_predicted_S_V4_over_4_V3": predicted_correction,
            "quartic_correction_measured_at_delta_1e-3": {
                direction: values[0] for direction, values in measured_correction.items()
            },
            "leading_term_relative_error_at_smallest_move": leading_agreement,
            "smallest_swept_move": smallest["move"],
            "lagrange_inclusion_violations_swept": len(violations),
            "lagrange_inclusion_violations_dense": len(dense_violations),
            "dense_shocks_tested": 2 * DENSE_SHOCKS,
            "bound_tightest_ratio_away_from_the_remainder_zero": min(away_ratios),
            "bound_loosest_ratio": max(ratios),
            "bound_ratio_collapses_near_the_remainder_zero": min(ratios),
            "book_speed_at_base_spot": speed_at_base,
            "aggregate_speed_crosses_zero_at_move": speed_crossing.get("move"),
            "aggregate_speed_crosses_zero_at_spot": speed_crossing.get("spot"),
            "predicted_remainder_zero_at_move": predicted_remainder_zero,
            "published_bracket_containing_that_zero": list(observed_signed_reversal),
        },
        "asymptotics": {
            "widest_fit_window": list(SLOPE_WINDOWS[0]),
            "narrowest_fit_window": list(SLOPE_WINDOWS[-1]),
            "slope_windows": {
                direction: [
                    {
                        "window": values["window"],
                        "slope": values["slope"],
                        "standard_error": values["standard_error"],
                        "observations": values["observations"],
                    }
                    for values in series
                ]
                for direction, series in fitted.items()
            },
            "why_the_window_starts_there": "R is a difference of nearly equal numbers, so below "
            "some shock size its own round-off swamps it. Measured on this book: |R| at delta = "
            "1e-5 is 1.13e-9 against a value near 9.8e4, about 1e-14 relative -- tens of ulp -- "
            "and the ratio of R to the predicted cubic term has already drifted from 0.99958 at "
            "delta = 1e-4 to 0.98191 at 1e-5. So the floor is near delta = 3e-5, an order of "
            "magnitude below the narrowest window used here, and the fits are not contaminated by "
            "it. An earlier draft of this analysis put the floor at 1e-3; that figure came from a "
            "single-option test using absolute price increments rather than relative moves, so it "
            "was the wrong unit on the wrong scale. Recorded because the correction is the "
            "interesting part: an arithmetic floor is a property of the book, not a constant",
            "why_the_window_ends_there": "beyond about 2e-2 the fourth-order term is not "
            "negligible, so a fitted slope there measures a mixture of orders rather than "
            "the cubic -- which is why the windows are reported as a sequence",
        },
        "the_feature_the_prose_got_wrong": {
            "published_claim": "the linearisation error grows with the shock size",
            "narrowest_window_slope_by_direction": {
                direction: series[-1]["slope"] for direction, series in fitted.items()
            },
            "refuted_by": "experiments/stress_testing/results/linearisation_error.csv, whose "
            "abs_error is -528.5 at a 20% down move and +12526.9 at 30% -- it changes sign there, "
            "magnitude at 20% is smaller than at 10%",
            "mechanism": "the ladder's V''' crosses zero at spot "
            f"{speed_crossing.get('spot')}, a down move of {speed_crossing.get('move'):.4f}, so "
            "segments beyond that contain both signs and their cubic contributions cancel. The "
            "cancellation drives the Lagrange coefficient through zero, which drives the remainder "
            "through zero, which is the dip",
            "prediction": f"R = 0 at a down move of {predicted_remainder_zero:.4f}",
            "bracketed_in_published_data_by": list(observed_signed_reversal),
            "up_moves": "no crossing anywhere in the swept range, and |R| monotone there -- the "
            "asymmetry between the directions follows from (5), not from where the sweep landed",
        },
        "rows": rows,
        "refusals": [
            {
                "question": "is the scenario plausible?",
                "refused": "a bound on the map says how much of a stress number is Taylor "
                "truncation and nothing about how much is choice. The scenario set has no oracle "
                "and this experiment does not manufacture one (docs/validation_matrix.md row 12).",
            },
            {
                "question": "does the cubic bound cover the multi-factor scenarios?",
                "refused": "no, and implying otherwise would be the sloppiest move available here. "
                "Once a scenario ties a volatility bump to a spot move, the omitted mixed partials "
                "and the vol convexity enter at order delta^2, so the leading remainder is "
                "quadratic with a different constant. The swept shock is single-factor and "
                "vol-fixed so that the cubic statement is the right one; the two-variable "
                "case is the same style of algebra and this script does not do it.",
            },
            {
                "question": "does the bound hold in the zero-volatility limit?",
                "refused": "it degenerates. The core returns zero for every higher spot derivative "
                "when sigma*sqrt(T) -> 0, so (4) reads 0 <= 0 and the map is exact off the strike "
                "kink anyway. A bound on a C^2 function is not a statement about a step function.",
            },
        ],
        "environment": environment(),
        "oracles": {
            "tool": "none used; a bound is not a second implementation of a price",
            "versions": package_versions(),
        },
    }
    payload["figure_status"] = figure_status
    payload["artifacts"] = artifact_manifest([csv_path, figure_path])

    json_path = RESULTS / "linearisation_error_bound.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["headline"], indent=2))
    print(f"wrote {repo_relative(json_path)}")
    return 0


def make_figure(rows: list[dict[str, Any]], crossing: dict[str, Any], path: Path) -> str:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return "not generated (matplotlib unavailable)"

    figure, axes = plt.subplots(1, 3, figsize=(13.8, 4.4))
    down = [row for row in rows if row["direction"] == "down"]
    up = [row for row in rows if row["direction"] == "up"]

    axis = axes[0]
    axis.loglog(
        [r["move"] for r in down],
        [r["abs_remainder"] for r in down],
        "o-",
        label="|R| measured, down",
    )
    axis.loglog(
        [r["move"] for r in up], [r["abs_remainder"] for r in up], "^-", label="|R| measured, up"
    )
    axis.loglog(
        [r["move"] for r in down],
        [r["abs_bound"] for r in down],
        "s--",
        color="crimson",
        label="bound (1/6)·sup|V'''|·|h|³",
    )
    first = down[0]
    axis.loglog(
        [r["move"] for r in down],
        [first["abs_remainder"] * (r["move"] / first["move"]) ** 3 for r in down],
        ":",
        color="0.45",
        label=r"reference slope $\delta^3$",
    )
    axis.set_xlabel("shock size")
    axis.set_ylabel("P&L error (money)")
    axis.set_title("A. dominated, and cubic", fontsize=10)
    axis.legend(fontsize=6.5)
    axis.grid(which="both", linestyle=":", linewidth=0.5, alpha=0.6)

    axis = axes[1]
    moves = [r["move"] for r in down]
    axis.semilogx(moves, [r["lagrange_coefficient"] for r in down], "o-", label="c = 6R/h³, down")
    axis.fill_between(
        moves,
        [r["segment_speed_min"] for r in down],
        [r["segment_speed_max"] for r in down],
        alpha=0.22,
        color="steelblue",
        label="V''' range along the segment",
    )
    axis.axhline(0.0, color="0.4", linewidth=0.9)
    axis.set_xlabel("shock size")
    axis.set_ylabel(r"book $V_{SSS}$")
    axis.set_title("B. the sharp form: c is trapped, and crosses zero", fontsize=10)
    axis.legend(fontsize=6.5)
    axis.grid(linestyle=":", linewidth=0.5, alpha=0.6)

    axis = axes[2]
    spots = np.linspace(SPOT * (1.0 - 0.45), SPOT, 400)
    axis.plot(spots, [book_speed(float(spot)) for spot in spots], color="navy")
    axis.axhline(0.0, color="0.4", linewidth=0.9)
    if crossing.get("crossing_found"):
        axis.axvline(crossing["spot"], color="crimson", linestyle="--", linewidth=1.0)
        axis.annotate(
            f"book V''' = 0\nS ≈ {crossing['spot']:.2f}\n(down move {crossing['move']:.2%})",
            xy=(crossing["spot"], 0.0),
            xytext=(crossing["spot"] + 1.5, max(abs(book_speed(float(s))) for s in spots) * 0.45),
            fontsize=7,
            color="crimson",
        )
    axis.plot(
        [SPOT * (1.0 - r["move"]) for r in down],
        [r["lagrange_coefficient"] for r in down],
        "o",
        color="darkorange",
        markersize=4,
        label="c at the swept shocks",
    )
    axis.set_xlabel("spot along the down-shocked path")
    axis.set_ylabel(r"book $V_{SSS}(S)$")
    axis.set_title("C. why the published error is not monotone", fontsize=10)
    axis.legend(fontsize=6.5)
    axis.grid(linestyle=":", linewidth=0.5, alpha=0.6)

    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return "generated"


if __name__ == "__main__":
    sys.exit(main())
