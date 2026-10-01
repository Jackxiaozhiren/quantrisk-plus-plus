#!/usr/bin/env python3
r"""Phase 15 experiment: what re-striking gamma at the shocked volatility actually buys the map.

    uv run python experiments/restrike_gamma_map/run.py
    uv run python scripts/run_benchmark_suite.py --only restrike_gamma_map

`v1.3.0` derived the two-factor error of the published delta-gamma-vega map and ended with a
prioritisation rather than a result: on the repository's own `risk_off` scenario the largest single
omitted piece is `\frac12 V_{SS\sigma} h^2 k` — gamma evaluated at the *base* volatility and then
multiplied across a move that has already changed the volatility — at 10.7× the net quadratic term,
and the recommendation was "re-strike gamma, do not add vanna and volga". That recommendation has
never been measured. This experiment measures it.

The map (`cpp/src/stress/engine.cpp`, published as `delta_i s_i + gamma_i s_i^2 + vega_i a_i` with
`gamma_i` carrying the one-half) is rebuilt here four ways, all four run through
`quantrisk.stress.run_scenario` so the arithmetic is the shipped engine's, not a re-typed formula:

* `base` — every exposure at the base market. What ships.
* `gamma_restrike` — delta and vega at base, gamma at `(S, sigma + k)`: the recommendation, read
  literally, re-striking the one exposure whose sigma-derivative dominates the omission.
* `gamma_restrike_at_move` — gamma at `(S + h, sigma + k)` instead, so the curvature is taken at the
  point the book actually ends up at.
* `all_restrike` — every exposure at `(S + h, sigma + k)`, i.e. "price the sensitivities at the
  shocked market", the naive fix.

Five claims. Each could fail, each is checked against the engine rather than against the algebra
that motivated it, and two of them did not come out the way the derivation suggested:

1. **The mechanism is the term it claims to be.** The difference between the restrike map and the
   base map is exactly `k -> gamma(sigma+k) - gamma(sigma)` times the squared *relative* move (the
   exposure already carries the `S^2`, so the engine's own factor is the relative one), and the
   divided difference `(gamma(sigma+k) - gamma(sigma)) / k` is trapped by the segment's range of
   `d gamma_exposure / d sigma`, computed from the core's mixed third partial `V_SSsigma`. A wrong
   closed form for `V_SSsigma` refutes this immediately, which is why it is stated as an inclusion
   rather than a tolerance.
2. **It removes the named term, but not all of it.** At the published `risk_off` size the finite
   difference of gamma across the whole volatility leg takes out 86 % of the local
   `1/2 V_SSsigma h^2 k` that v1.3.0 named -- the gap between a recipe and its linearisation. The
   absolute error there falls from -5,320.79 to +1,937.72, a factor of 0.364, and the sign flips
   with it.
3. **The order of the map does not change.** Between the two narrowest scales of each of three
   rays the error of all four maps falls with a local slope of 1.98-2.01: re-striking removes a
   cubic, not the quadratic vanna and volga pieces that cubic was competing with, and the order is
   untouched. Regressions over a four-point narrow window spread the same slopes to 1.89-2.05, and
   over the whole ray to 1.92-2.34 -- the higher-order content still visible at grid sizes, which is
   why the pairwise number is the one quoted and all three are published.
4. **`k = 0` is a control, and the naive fix is priced.** With no volatility move the restrike is
   the identity map to exactly 0.0 in engine units. `all_restrike` -- re-pricing delta, gamma and
   vega at the shocked market, the fix a reader would reach for first -- is worse than the
   gamma-only variant on 116 of the 120 cells swept, and on the published scenario it is worse
   than the shipped map by a factor of 11.
5. **The improvement is not uniform, and the cells that lose are predictable.** On 45 of 120 cells
   the restrike does not reduce the absolute error, and on 20 of those it at least doubles it, up to
   a factor of 142. All 20 are cells whose shipped-map error was smaller than the term removed:
   two third-order pieces cancelling, and the map's accuracy being arithmetic luck. So claim 5
   predicts *where* the shipped map looks best from closed-form coefficients alone -- the zeros of
   the third-order truncation of its error along each `delta` column -- and compares them with the
   zeros of the priced error. Within `|delta| <= 0.05` the two agree to 0.0002-0.0024 in vol move
   against a tolerance of 0.005, which is gated. Beyond it the prediction drifts monotonically with
   the move size, worst 0.093 at `delta = -0.30`, and at `delta = +0.30` the truncation predicts a
   zero the priced map never has. That drift is reported, not gated, and it is the interesting half
   of the result: a third-order truncation is a fair argument only near the base market, which is
   where the published scenarios live.

What is deliberately not claimed. The `risk_off` improvement is a statement about a three-strike
ladder on one book at one maturity; `refusals` records that, that the ranking of the four maps is a
property of this scenario grid, and that the share in claim 5 counts cells rather than money -- a
small cell that improves and a large cell that worsens count the same way, so the artifact publishes
the value-weighted version next to the count.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import quantrisk
from quantrisk import stress as STRESS
from quantrisk.experiments.metadata import (
    artifact_manifest,
    environment,
    repo_relative,
    utc_timestamp,
)

RESULTS = Path(__file__).resolve().parent / "results"
REPO_ROOT = Path(__file__).resolve().parents[2]

# The published book, unchanged from `experiments/stress_testing/run.py:run_linearisation`,
# `experiments/linearisation_error_bound/run.py` and `experiments/two_factor_error_bound/run.py`:
# spot 100, three calls at 90/100/110, 5000 each, r = 3 %, no dividend, sigma = 20 %, T = 0.5.
SPOT = 100.0
RATE = 0.03
DIVIDEND_YIELD = 0.0
VOLATILITY = 0.20
MATURITY = 0.5
STRIKES = (90.0, 100.0, 110.0)
QUANTITY = 5000.0

# The same joint grid as Phase 13's bound sweep, so the two experiments describe one book.
DELTAS = (-0.30, -0.20, -0.15, -0.10, -0.05, -0.02, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30)
VOL_MOVES = (-0.10, -0.06, -0.03, -0.01, 0.0, 0.01, 0.03, 0.06, 0.10, 0.15, 0.20)

SEGMENT_GRID = 401
SCALES = (1.0, 0.3, 0.1, 0.03, 0.01, 0.003, 0.001)

# Claim 5 locates zeros of the truncated error (a prediction) and of the priced
# error (a measurement) with one shared bracketing-and-bisecting routine, so the two
# sides cannot differ in what a zero means. The truncation is arithmetic, so it gets a
# finer bracket than the engine, which pays a pricing per point.
PREDICTION_SCAN_POINTS = 2001
MEASURED_SCAN_POINTS = 401
BISECTION_STEPS = 40

# How far a predicted zero may sit from a measured one and still be called the same
# zero: half the coarsest volatility step swept, so a prediction that resolves to the
# neighbouring swept cell of its own zero is still a hit.
CROSSING_MATCH_TOLERANCE = 0.005

# The claim 5 gate only asks the truncation to be right where a third-order expansion of a *joint*
# move is a fair argument: spot moves of at most 5 % of the base, which is also where the published
# scenarios live. Wider moves are measured and reported, not gated.
SMALL_MOVE_LIMIT = 0.05


def market(spot: float = SPOT, sigma: float = VOLATILITY) -> quantrisk.pricing.MarketParams:
    return quantrisk.pricing.MarketParams(
        spot=spot,
        rate=RATE,
        dividend_yield=DIVIDEND_YIELD,
        volatility=sigma,
        maturity=MATURITY,
    )


def option(strike: float) -> quantrisk.pricing.EuropeanOption:
    return quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, strike)


def book_value(spot: float, sigma: float) -> float:
    return (
        sum(
            quantrisk.pricing.black_scholes(option(strike), market(spot, sigma)).price
            for strike in STRIKES
        )
        * QUANTITY
    )


BASE_VALUE = book_value(SPOT, VOLATILITY)

# How many of the narrowest scales the asymptotic fit uses. At that end the leading power is
# essentially the only term left, so its slope answers "what order is this map".
NARROW_END_FITS = 4


def totals(spot: float, sigma: float) -> dict[str, float]:
    """Map exposures and Taylor coefficients of the book, in the units the stress layer quotes.

    Every scaling here uses the `spot` argument rather than the base spot: the variants differ
    precisely in which market the exposures are read at, so a hard-coded 100 would evaluate the
    gamma of the moved book at the base spot, and the two variants would not be one book.
    """
    m = market(spot, sigma)
    readings = {
        "delta": lambda o: quantrisk.pricing.black_scholes_greeks(o, m).delta * spot,
        "gamma": lambda o: 0.5 * quantrisk.pricing.black_scholes_greeks(o, m).gamma * spot * spot,
        "vega": lambda o: quantrisk.pricing.black_scholes_greeks(o, m).vega,
    }
    return {
        name: sum(read(option(strike)) for strike in STRIKES) * QUANTITY
        for name, read in readings.items()
    }


def gamma_sigma_rate(spot: float, sigma: float) -> float:
    r"""The sigma-derivative of the book's gamma exposure, from the core's mixed third partial.

    The exposure is `\frac12 V_{SS} S^2` summed over the book and scaled by quantity, so its
    derivative in sigma is `\frac12 V_{SS\sigma} S^2` -- the half is carried here rather than
    recovered later, because claim 1 compares it with a finite difference of
    `totals()['gamma']`: a factor on one side only breaks the inclusion, not bends it.
    """
    m = market(spot, sigma)
    return (
        sum(
            0.5
            * quantrisk.pricing.black_scholes_mixed_third_derivatives(o, m).spot_spot_sigma
            * spot
            * spot
            for o in (option(strike) for strike in STRIKES)
        )
        * QUANTITY
    )


BASE = totals(SPOT, VOLATILITY)
MAP_KEYS = ("base", "gamma_restrike", "gamma_restrike_at_move", "all_restrike")


def book_expansion_coefficients() -> dict[str, float]:
    r"""Every partial the third-order two-variable expansion needs, summed over the book.

    Raw partials rather than exposures: the gamma exposure already folds in the `\frac12 S^2`, while
    claim 5 asks where the *terms* of the expansion cancel, and a term is a coefficient times the
    powers of the move. Named as in `experiments/two_factor_error_bound/run.py:terms_at_base`, the
    expansion these coefficients belong to.
    """
    m = market(SPOT, VOLATILITY)
    mixed = quantrisk.pricing.black_scholes_mixed_third_derivatives
    cross = quantrisk.pricing.black_scholes_vol_cross_derivatives
    readings = {
        "speed": lambda o: quantrisk.pricing.black_scholes_spot_derivatives(o, m).third,
        "vanna": lambda o: cross(o, m).vanna,
        "volga": lambda o: cross(o, m).volga,
        "gamma_sigma": lambda o: mixed(o, m).spot_spot_sigma,
        "vanna_sigma": lambda o: mixed(o, m).spot_sigma_sigma,
        "volga_sigma": lambda o: mixed(o, m).sigma_sigma_sigma,
    }
    return {
        name: sum(read(option(strike)) for strike in STRIKES) * QUANTITY
        for name, read in readings.items()
    }


COEFFS = book_expansion_coefficients()
SPEED_COEFF = COEFFS["speed"]


def exposures_for(delta: float, vol_move: float, variant: str) -> dict[str, float]:
    """The three map exposures under one variant of where they are evaluated."""
    h = SPOT * delta
    k = vol_move
    at_base = totals(SPOT, VOLATILITY)
    if variant == "base":
        return at_base
    if variant == "gamma_restrike":
        return {**at_base, "gamma": totals(SPOT, VOLATILITY + k)["gamma"]}
    if variant == "gamma_restrike_at_move":
        return {**at_base, "gamma": totals(SPOT + h, VOLATILITY + k)["gamma"]}
    if variant == "all_restrike":
        return totals(SPOT + h, VOLATILITY + k)
    raise RuntimeError(f"unknown variant {variant!r}")


def engine_pnl(delta: float, vol_move: float, exposure: dict[str, float]) -> float:
    """One map evaluation, through the shipped stress engine on the published book."""
    factors = STRESS.FactorSet()
    factors.factors = [
        STRESS.RiskFactor("EQ0", STRESS.FactorClass.equity_index, SPOT, "index points"),
        STRESS.RiskFactor("VOL", STRESS.FactorClass.volatility, VOLATILITY, "annualised vol"),
    ]
    vector = STRESS.ExposureVector()
    # Blocks are indexed by factor position, as `two_factor_error_bound/run.py:engine_map` records:
    # a vega parked on the equity factor is multiplied by zero and disappears silently.
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
    handle.name = "restrike_probe"
    handle.kind = STRESS.ScenarioKind.deterministic
    handle.assumptions = "equity relative move and volatility absolute move, nothing else"
    handle.shocks = [
        STRESS.Shock("EQ0", delta, 0.0),
        STRESS.Shock("VOL", 0.0, vol_move),
    ]
    return float(STRESS.run_scenario(portfolio, handle).pnl_change)


def errors_for(delta: float, vol_move: float, exact: float) -> dict[str, float]:
    return {
        variant: exact - engine_pnl(delta, vol_move, exposures_for(delta, vol_move, variant))
        for variant in MAP_KEYS
    }


def published_scenario(name: str = "risk_off") -> dict[str, float]:
    """The named scenario's moves, read from the stress experiment rather than re-typed here."""
    path = REPO_ROOT / "experiments" / "stress_testing" / "run.py"
    spec = importlib.util.spec_from_file_location("quantrisk_stress_experiment_for_restrike", path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    for handle in module.scenarios():
        if handle.name != name:
            continue
        found = {"equity": None, "volatility": None}
        for shock in handle.shocks:
            if shock.factor_id == "EQ0":
                found["equity"] = float(shock.relative)
            elif shock.factor_id == "VOL":
                found["volatility"] = float(shock.absolute)
        if found["equity"] is None or found["volatility"] is None:  # pragma: no cover
            raise RuntimeError(f"scenario {name} does not move both EQ0 and VOL: {found}")
        return {key: float(value) for key, value in found.items()}
    raise RuntimeError(f"no scenario named {name!r} in the published stress set")


def segment_range_of_gamma_rate(k: float) -> tuple[float, float]:
    """min and max of `d gamma_exposure / d sigma` along the volatility leg of the shock."""
    values = [
        gamma_sigma_rate(SPOT, VOLATILITY + k * step / (SEGMENT_GRID - 1))
        for step in range(SEGMENT_GRID)
    ]
    return min(values), max(values)


def exact_move(delta: float, vol_move: float) -> float:
    """The revalued book PnL for one joint move, against the base value."""
    return book_value(SPOT + SPOT * delta, VOLATILITY + vol_move) - BASE_VALUE


def truncated_column_error(delta: float, k: float) -> float:
    r"""The third-order truncation of the base map error, as a function of the volatility move.

    With `h = S \delta` fixed, the expansion of `exact - map` through third order is

        \frac16 V_{SSS} h^3
        + k \left( V_{S\sigma} h + \frac12 V_{SS\sigma} h^2 \right)
        + k^2 \left( \frac12 V_{\sigma\sigma} + \frac12 V_{S\sigma\sigma} h \right)
        + \frac16 V_{\sigma\sigma\sigma} k^3

    evaluated at the base market. Every coefficient comes from a closed form in the core and none of
    them is fitted to the errors this experiment measures, which is what makes the argument below a
    prediction rather than a description.
    """
    h = SPOT * delta
    return (
        SPEED_COEFF * h**3 / 6.0
        + k * (COEFFS["vanna"] * h + 0.5 * COEFFS["gamma_sigma"] * h * h)
        + k * k * (0.5 * COEFFS["volga"] + 0.5 * COEFFS["vanna_sigma"] * h)
        + COEFFS["volga_sigma"] * k**3 / 6.0
    )


def _sign_change_roots(f, low: float, high: float, points: int) -> list[float]:
    """Every zero of a scalar function in `[low, high]`, found by bracketing then bisecting.

    Deliberately not an analytic root solver: the same routine is run on the third-order truncation
    (where the zeros are a prediction) and on the priced error (where they are the measurement), so
    the two sides of claim 5 cannot differ in how a zero is *defined*, only in where it is.
    """
    moves = [low + (high - low) * index / (points - 1) for index in range(points)]
    values = [f(move) for move in moves]
    roots = []
    for index in range(len(moves) - 1):
        move, value = moves[index], values[index]
        next_move, next_value = moves[index + 1], values[index + 1]
        if value == 0.0:
            roots.append(move)
            continue
        if value * next_value > 0.0:
            continue
        left, right, left_value = move, next_move, value
        for _ in range(BISECTION_STEPS):
            middle = (left + right) / 2.0
            middle_value = f(middle)
            if left_value * middle_value <= 0.0:
                right = middle
            else:
                left, left_value = middle, middle_value
        roots.append((left + right) / 2.0)
    return roots


def measured_error_on_column(delta: float) -> Callable[[float], float]:
    r"""The shipped map error on this `\delta` column, as a function of the volatility move."""
    return lambda k: exact_move(delta, k) - engine_pnl(delta, k, BASE)


def cancellation_row(delta: float, column: list[dict[str, Any]]) -> dict[str, Any]:
    r"""Claim 5 for one `\delta` column: where the shipped map's error is zero, and why.

    The truncation predicts zeros; the priced error has zeros. If the two sets agree, then the
    volatility moves at which the map looks most accurate are the moves where its third-order terms
    cancel -- and the re-strike, which deletes one of the canceling pieces, is measured there rather
    than somewhere convenient.
    """
    predicted = _sign_change_roots(
        lambda move: truncated_column_error(delta, move),
        min(VOL_MOVES),
        max(VOL_MOVES),
        PREDICTION_SCAN_POINTS,
    )
    measured = _sign_change_roots(
        measured_error_on_column(delta),
        min(VOL_MOVES),
        max(VOL_MOVES),
        MEASURED_SCAN_POINTS,
    )
    swept = [
        row["error_base"] for row in column if row["delta"] == delta and row["vol_move"] != 0.0
    ]
    column_median = sorted(abs(value) for value in swept)[len(swept) // 2]
    # The zero the truncation is entitled to predict is the one nearest the base market: a cubic's
    # other roots sit further out along the volatility leg, where a third-order expansion has no
    # right to be an argument. They are counted, not gated.
    nearest_predicted = min(predicted, key=abs, default=None)
    nearest_measured = min(measured, key=abs, default=None)
    zero_distance = (
        abs(nearest_measured - nearest_predicted)
        if nearest_predicted is not None and nearest_measured is not None
        else None
    )
    predicted_offsets = [
        min(abs(measure - move) for measure in measured) if measured else None for move in predicted
    ]
    measured_offsets = [
        min(abs(move - measure) for move in predicted) if predicted else None
        for measure in measured
    ]
    at_nearest = (
        errors_for(delta, nearest_measured, exact_move(delta, nearest_measured))
        if nearest_measured is not None
        else None
    )
    return {
        "delta": delta,
        "predicted_zeros": predicted,
        "measured_zeros": measured,
        "predicted_zero_count": len(predicted),
        "measured_zero_count": len(measured),
        "nearest_predicted_zero": nearest_predicted,
        "nearest_measured_zero": nearest_measured,
        "nearest_zeros_both_absent": not predicted and not measured,
        "nearest_zero_distance": zero_distance,
        "nearest_zero_signed_bias": (
            None if zero_distance is None else nearest_measured - nearest_predicted
        ),
        "base_abs_error_at_nearest_measured_zero": (
            None if at_nearest is None else abs(at_nearest["base"])
        ),
        "restrike_abs_error_at_nearest_measured_zero": (
            None if at_nearest is None else abs(at_nearest["gamma_restrike"])
        ),
        "all_restrike_abs_error_at_nearest_measured_zero": (
            None if at_nearest is None else abs(at_nearest["all_restrike"])
        ),
        "column_median_abs_error_base": column_median,
        "predicted_zeros_without_a_measured_one": sum(
            1 for offset in predicted_offsets if offset is None or offset > CROSSING_MATCH_TOLERANCE
        ),
        "measured_zeros_without_a_predicted_one": sum(
            1 for offset in measured_offsets if offset is None or offset > CROSSING_MATCH_TOLERANCE
        ),
    }


def mechanism_row(delta: float, k: float) -> dict[str, Any]:
    """Claim 1 for one cell: the improvement equals the trapped term, to engine round-off."""
    if k == 0.0:  # a divided difference across no volatility move has no segment to be trapped by
        raise RuntimeError("a mechanism probe needs a non-zero volatility move")
    base = totals(SPOT, VOLATILITY)
    moved = totals(SPOT, VOLATILITY + k)
    difference = moved["gamma"] - base["gamma"]
    # The gamma exposure is quoted in the stress layer's units, which already fold in the one-half
    # and S^2, so the engine multiplies it by the *relative* move squared. Predicting h^2 here
    # re-counts S^2 and lands a factor of 10,000 off.
    observed_map_difference = engine_pnl(delta, k, {**base, "gamma": moved["gamma"]}) - engine_pnl(
        delta, k, base
    )
    low, high = segment_range_of_gamma_rate(k)
    divided = difference / k
    return {
        "delta": delta,
        "vol_move": k,
        "gamma_exposure_difference": difference,
        "divided_difference": divided,
        "segment_min_gamma_rate": low,
        "segment_max_gamma_rate": high,
        "inside_segment_range": low - 1e-9 <= divided <= high + 1e-9,
        "map_difference_observed": observed_map_difference,
        "map_difference_predicted": difference * delta * delta,
        "map_difference_relative_error": (
            abs(observed_map_difference - difference * delta * delta)
            / max(1e-12, abs(difference * delta * delta))
        ),
    }


def _fit_log_log(points: list[dict[str, Any]], field: str) -> tuple[float, float]:
    """Least-squares log-log slope of one error field and its standard error."""
    xs = [math.log(point["size"]) for point in points]
    ys = [math.log(point[field]) for point in points]
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    variance = sum((x - mean_x) ** 2 for x in xs)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / variance
    intercept = mean_y - slope * mean_x
    residuals = [y - (intercept + slope * x) for x, y in zip(xs, ys, strict=True)]
    standard_error = math.sqrt(sum(value * value for value in residuals) / (n - 2) / variance)
    return slope, standard_error


def slope_series(direction: tuple[float, float]) -> list[dict[str, Any]]:
    """log-log slope of each map's absolute error against shock size, shrunk along one ray.

    Two fits rather than one: over the whole ray, which is what the grid sizes actually span, and
    over the narrow end only, where the leading power is the only one left. They disagree by design
    whenever a higher-order term is still visible at the wide end, and the narrow-end fit is the one
    that answers 'what order is this map'.
    """
    delta, k = direction
    points = []
    for scale in reversed(SCALES):
        size = math.hypot(delta, k / SPOT) * scale
        moved_spot = SPOT + SPOT * delta * scale
        moved_vol = VOLATILITY + k * scale
        errors = errors_for(
            delta * scale, k * scale, book_value(moved_spot, moved_vol) - BASE_VALUE
        )
        points.append({"size": size, **{f"error_{name}": abs(errors[name]) for name in MAP_KEYS}})
    out = []
    for name in MAP_KEYS:
        field = f"error_{name}"
        slope, standard_error = _fit_log_log(points, field)
        narrow = points[:NARROW_END_FITS]
        narrow_slope, narrow_error = _fit_log_log(narrow, field)
        out.append(
            {
                "map": name,
                "slope": slope,
                "standard_error": standard_error,
                "observations": len(points),
                "slope_narrow_end": narrow_slope,
                "slope_narrow_end_standard_error": narrow_error,
                "narrow_end_observations": len(narrow),
                # The ratio between the two narrowest scales, with no window and no regression: the
                # order claim is worth most stated this way, because the window fits below still
                # move by a tenth on a term that is not the leading one yet.
                "local_slope_narrowest_pair": (
                    math.log(points[0][field] / points[1][field])
                    / math.log(points[0]["size"] / points[1]["size"])
                ),
                "quadratic_coefficient_at_narrowest": points[0][field] / points[0]["size"] ** 2,
                "error_at_narrowest_shock": points[0][field],
                "sweep": points,
            }
        )
    return out


def sweep_rows() -> list[dict[str, Any]]:
    rows = []
    for delta in DELTAS:
        for vol_move in VOL_MOVES:
            if vol_move == 0.0 and abs(delta) < 1e-12:
                continue
            h = SPOT * delta
            exact = book_value(SPOT + h, VOLATILITY + vol_move) - BASE_VALUE
            errors = errors_for(delta, vol_move, exact)
            rows.append(
                {
                    "delta": delta,
                    "vol_move": vol_move,
                    "exact_pnl": exact,
                    **{
                        f"pnl_{name}": engine_pnl(
                            delta, vol_move, exposures_for(delta, vol_move, name)
                        )
                        for name in MAP_KEYS
                    },
                    **{f"error_{name}": errors[name] for name in MAP_KEYS},
                    "abs_error_base": abs(errors["base"]),
                    "abs_error_gamma_restrike": abs(errors["gamma_restrike"]),
                    "abs_error_all_restrike": abs(errors["all_restrike"]),
                    # The trapped term this map variant removes, as the engine priced it. Claim 1
                    # proves `error_base - error_restrike == removed_term` to round-off, so a cell's
                    # verdict is arithmetic: the restrike helps where the term was part of the error
                    # and hurts where it was cancelling the rest of it.
                    "removed_term": errors["base"] - errors["gamma_restrike"],
                    "base_error_was_smaller_than_removed_term": (
                        abs(errors["base"]) < abs(errors["base"] - errors["gamma_restrike"])
                    ),
                    "restrike_improves": abs(errors["gamma_restrike"])
                    < abs(errors["base"]) - 1e-12,
                    "restrike_factor": (
                        abs(errors["gamma_restrike"]) / abs(errors["base"])
                        if abs(errors["base"]) > 1e-9
                        else None
                    ),
                    "value_at_risk": abs(exact),
                }
            )
    return rows


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    published = published_scenario("risk_off")
    h_published = SPOT * published["equity"]
    exact_published = (
        book_value(SPOT + h_published, VOLATILITY + published["volatility"]) - BASE_VALUE
    )
    published_map_pnl = {
        name: engine_pnl(
            published["equity"],
            published["volatility"],
            exposures_for(published["equity"], published["volatility"], name),
        )
        for name in MAP_KEYS
    }
    published_errors = {name: exact_published - published_map_pnl[name] for name in MAP_KEYS}

    rows = sweep_rows()
    moved = [row for row in rows if row["vol_move"] != 0.0]
    improved = [row for row in moved if row["restrike_improves"]]
    worsened = [row for row in moved if not row["restrike_improves"]]
    weighted_before = sum(row["abs_error_base"] for row in moved)
    weighted_after = sum(row["abs_error_gamma_restrike"] for row in moved)

    # The published cell is probed alongside the synthetic ones so claim 1 covers the one number the
    # documents will quote, not only the cells nobody reads.
    mechanisms = [
        mechanism_row(delta, k)
        for delta, k in (
            (0.05, -0.06),
            (0.05, 0.06),
            (0.05, 0.10),
            (0.15, -0.06),
            (0.15, 0.06),
            (0.15, 0.10),
            (published["equity"], published["volatility"]),
        )
        if k != 0.0
    ]
    outside = [row for row in mechanisms if not row["inside_segment_range"]]
    if outside:
        first = outside[0]
        raise RuntimeError(
            f"the mechanism inclusion fails on {len(outside)} probe cells, first at "
            f"delta={first['delta']} k={first['vol_move']}: divided difference "
            f"{first['divided_difference']:.6e} outside "
            f"[{first['segment_min_gamma_rate']:.6e}, {first['segment_max_gamma_rate']:.6e}]"
        )
    worst_map_match = max(row["map_difference_relative_error"] for row in mechanisms)
    if worst_map_match > 1e-9:
        raise RuntimeError(
            "the map difference is not the trapped term: worst relative mismatch "
            f"{worst_map_match:.3e}"
        )

    control_rows = [row for row in rows if row["vol_move"] == 0.0]
    control_gap = max(abs(row["pnl_base"] - row["pnl_gamma_restrike"]) for row in control_rows)
    if control_gap > 1e-6:
        raise RuntimeError(
            f"k = 0 is not the identity: base and restrike differ by {control_gap:.3e}"
        )

    directions = {
        "crash (equity down, vol up)": (-0.15, 0.06),
        "melt-up (equity up, vol down)": (0.15, -0.06),
        "aligned (equity up, vol up)": (0.15, 0.06),
    }
    slopes = {label: slope_series(direction) for label, direction in directions.items()}

    cancellations = [cancellation_row(delta, rows) for delta in DELTAS]
    small_move = [row for row in cancellations if abs(row["delta"]) <= SMALL_MOVE_LIMIT]
    wide_move = [row for row in cancellations if abs(row["delta"]) > SMALL_MOVE_LIMIT]
    one_sided = [
        row
        for row in small_move
        if not row["nearest_zeros_both_absent"] and row["nearest_zero_distance"] is None
    ]
    drifted = [
        row
        for row in small_move
        if row["nearest_zero_distance"] is not None
        and row["nearest_zero_distance"] > CROSSING_MATCH_TOLERANCE
    ]
    if one_sided or drifted:
        offender = (drifted or one_sided)[0]
        raise RuntimeError(
            f"the truncation's nearest zero is not the priced one inside |delta| <= "
            f"{SMALL_MOVE_LIMIT}: {len(one_sided)} columns with a zero on one side only, "
            f"{len(drifted)} further than {CROSSING_MATCH_TOLERANCE}, first at "
            f"delta={offender['delta']} predicting {offender['nearest_predicted_zero']} "
            f"against a measured {offender['nearest_measured_zero']}"
        )
    # The root finder answers for itself: a measured zero has to be a zero of the priced error, not
    # merely a sign change the bracketing walked past.
    residual = max(
        (row["base_abs_error_at_nearest_measured_zero"] or 0.0 for row in cancellations),
        default=0.0,
    )
    if residual > 1e-6:
        raise RuntimeError(f"a measured zero is not one: the priced error there is {residual:.3e}")
    unexplained = sum(row["predicted_zeros_without_a_measured_one"] for row in cancellations)
    distances = [
        row["nearest_zero_distance"] for row in cancellations if row["nearest_zero_distance"]
    ]
    wide_distances = [
        row["nearest_zero_distance"] for row in wide_move if row["nearest_zero_distance"]
    ]
    restrike_at_zeros = [
        row["restrike_abs_error_at_nearest_measured_zero"]
        for row in cancellations
        if row["restrike_abs_error_at_nearest_measured_zero"] is not None
    ]

    factors = [row["restrike_factor"] for row in moved if row["restrike_factor"] is not None]
    factors.sort()

    # The published cell decomposed against the term v1.3.0 named. The restrike removes a finite
    # difference of gamma across the whole volatility leg; the derivation names the local derivative
    # at the base market, so the ratio below says how much of the named term the recipe actually
    # takes out at published size rather than in the limit.
    published_removed = published_errors["base"] - published_errors["gamma_restrike"]
    published_local_cubic = (
        gamma_sigma_rate(SPOT, VOLATILITY) * published["volatility"] * published["equity"] ** 2
    )
    doubled = [r for r in moved if r["abs_error_gamma_restrike"] > 2.0 * r["abs_error_base"]]
    doubled_without_cancellation = [
        r for r in doubled if not r["base_error_was_smaller_than_removed_term"]
    ]

    grid_csv = RESULTS / "restrike_gamma_map.csv"
    write_csv(grid_csv, rows)
    published_csv = RESULTS / "published_scenario_maps.csv"
    write_csv(
        published_csv,
        [
            {
                "scenario": "risk_off",
                "map": name,
                "delta": published["equity"],
                "vol_move": published["volatility"],
                "revalued_pnl": exact_published,
                "map_pnl": published_map_pnl[name],
                "error": published_errors[name],
                "abs_error": abs(published_errors[name]),
            }
            for name in MAP_KEYS
        ],
    )

    cancellation_csv = RESULTS / "cancellation_columns.csv"
    write_csv(cancellation_csv, cancellations)

    payload = {
        "schema": "quantrisk.restrike_gamma_map.v1",
        "generated_at_utc": utc_timestamp(),
        "command": "uv run python experiments/restrike_gamma_map/run.py",
        "claim": (
            "re-striking gamma at the shocked volatility does remove the term v1.3.0 named as "
            "dominant -- 86% of it at published size, taking the risk_off error to 0.364x -- but "
            "it worsens 45 of the 120 cells swept, and the cells it worsens are exactly those "
            "where the shipped map was accurate because two third-order terms cancelled"
        ),
        "book": {
            "spot": SPOT,
            "rate": RATE,
            "dividend_yield": DIVIDEND_YIELD,
            "volatility": VOLATILITY,
            "maturity": MATURITY,
            "strikes": list(STRIKES),
            "quantity": QUANTITY,
            "base_value": BASE_VALUE,
            "source": "experiments/stress_testing/run.py:run_linearisation",
        },
        "maps": {
            name: {
                "expression": expression,
                "produced_by": "quantrisk.stress.run_scenario",
            }
            for name, expression in (
                ("base", "delta and gamma and vega all at the base market (what ships)"),
                ("gamma_restrike", "gamma at (S, sigma + k); delta and vega at base"),
                ("gamma_restrike_at_move", "gamma at (S + h, sigma + k); delta and vega at base"),
                ("all_restrike", "every exposure at (S + h, sigma + k)"),
            )
        },
        "headline": {
            "joint_shocks_swept": len(rows),
            "cells_with_a_volatility_move": len(moved),
            "cells_where_restrike_reduces_abs_error": len(improved),
            "cells_where_restrike_does_not": len(worsened),
            "share_improved": len(improved) / len(moved),
            "median_error_factor_after_over_before": factors[len(factors) // 2],
            "worst_error_factor_after_over_before": factors[-1],
            "best_error_factor_after_over_before": factors[0],
            "value_weighted_error_before": weighted_before,
            "value_weighted_error_after": weighted_after,
            "value_weighted_reduction": 1.0 - weighted_after / weighted_before,
            "published_scenario": "risk_off",
            "published_error_base": published_errors["base"],
            "published_error_gamma_restrike": published_errors["gamma_restrike"],
            "published_error_all_restrike": published_errors["all_restrike"],
            "published_restrike_factor": (
                abs(published_errors["gamma_restrike"]) / abs(published_errors["base"])
            ),
            "published_removed_term": published_removed,
            "published_local_cubic_gamma_sigma": published_local_cubic,
            "published_fraction_of_local_term_removed": published_removed / published_local_cubic,
            "cells_where_restrike_at_least_doubles_error": len(doubled),
            "of_those_the_base_error_was_smaller_than_the_removed_term": (
                len(doubled) - len(doubled_without_cancellation)
            ),
            "mechanism_probes": len(mechanisms),
            "mechanism_inclusions_violated": len(outside),
            "mechanism_worst_map_difference_relative_error": worst_map_match,
            "zero_vol_control_max_gap": control_gap,
            "slope_of_error_against_shock_size": {
                label: {row["map"]: row["slope"] for row in series}
                for label, series in slopes.items()
            },
            "slope_standard_errors": {
                label: {row["map"]: row["standard_error"] for row in series}
                for label, series in slopes.items()
            },
            "slope_narrow_end_standard_errors": {
                label: {row["map"]: row["slope_narrow_end_standard_error"] for row in series}
                for label, series in slopes.items()
            },
            "slope_of_error_narrow_end": {
                label: {row["map"]: row["slope_narrow_end"] for row in series}
                for label, series in slopes.items()
            },
            "local_slope_narrowest_pair": {
                label: {row["map"]: row["local_slope_narrowest_pair"] for row in series}
                for label, series in slopes.items()
            },
            "local_slope_narrowest_pair_span": [
                min(
                    row["local_slope_narrowest_pair"]
                    for series in slopes.values()
                    for row in series
                ),
                max(
                    row["local_slope_narrowest_pair"]
                    for series in slopes.values()
                    for row in series
                ),
            ],
            "narrow_end_window_slope_span": [
                min(row["slope_narrow_end"] for series in slopes.values() for row in series),
                max(row["slope_narrow_end"] for series in slopes.values() for row in series),
            ],
            "whole_ray_slope_span": [
                min(row["slope"] for series in slopes.values() for row in series),
                max(row["slope"] for series in slopes.values() for row in series),
            ],
            "cells_ranked_against_the_base_map": len(moved),
            "columns_within_the_small_move_limit": len(small_move),
            "predicted_zeros_total": sum(row["predicted_zero_count"] for row in cancellations),
            "measured_zeros_total": sum(row["measured_zero_count"] for row in cancellations),
            "predicted_zeros_without_a_measured_one": unexplained,
            "measured_zeros_without_a_predicted_one": sum(
                row["measured_zeros_without_a_predicted_one"] for row in cancellations
            ),
            "nearest_zero_distance_max": max(distances),
            "nearest_zero_distance_median": sorted(distances)[len(distances) // 2],
            "nearest_zero_distance_max_beyond_the_limit": max(wide_distances, default=None),
            "root_finder_largest_residual_at_a_measured_zero": residual,
            "restrike_error_at_a_measured_zero_largest": max(restrike_at_zeros, default=None),
            "all_restrike_worse_than_gamma_only": sum(
                1
                for row in moved
                if row["abs_error_all_restrike"] > row["abs_error_gamma_restrike"]
            ),
        },
        "asymptotics": slopes,
        "mechanism": mechanisms,
        "cancellation": cancellations,
        "refusals": {
            "improvement_is_not_uniform": (
                "45 of the 120 cells swept are no better under the re-strike, and 20 of those "
                "are at least twice as wrong, worst factor 142; the CSV names every one"
            ),
            "cancellation_is_not_accuracy": (
                "the cells the re-strike damages are the cells whose shipped-map error was already "
                "smaller than the term being removed: the map was not accurate there, two "
                "third-order pieces were opposing, and the re-strike spends the cancellation"
            ),
            "order_not_changed": (
                "the local slope of |error| against shock size between the two narrowest scales is "
                "1.98-2.01 for all four maps: re-striking removes a cubic, not the quadratic vanna "
                "and volga pieces it was competing with. Window regressions spread further "
                "(1.89-2.05 narrow, 1.92-2.34 over the whole ray) and are published so the reader "
                "sees the wobble instead of the tightest number"
            ),
            "truncation_is_valid_only_near_the_base": (
                "the third-order zeros sit 0.0002-0.0024 in vol move from the priced zeros within "
                "|delta| <= 0.05, and drift to 0.093 by |delta| = 0.30 -- where the truncation "
                "predicts a zero the priced error never has. Nothing beyond the small-move "
                "limit is claimed, and the drift is reported rather than gated"
            ),
            "book_specific_ranking": (
                "the shares and factors above are one three-strike ladder at one maturity; they "
                "rank the four maps for this grid and say nothing about a book with different "
                "convexity or a scenario that moves vol more than spot"
            ),
            "counts_are_not_money": (
                "share_improved counts cells; value_weighted_reduction weights each cell by the "
                "same error it is made of, and the two can disagree"
            ),
        },
        "reproduction_policy": {
            "conditioning_limited": [
                "asymptotics",
                "cancellation",
                "headline.slope_of_error_against_shock_size",
                "headline.slope_of_error_narrow_end",
                "headline.slope_standard_errors",
                "headline.slope_narrow_end_standard_errors",
                "headline.local_slope_narrowest_pair",
                "headline.nearest_zero_distance",
                "headline.root_finder_largest_residual_at_a_measured_zero",
                "headline.restrike_error_at_a_measured_zero",
            ],
            "why": (
                "slopes are regressions and the zero locations are roots of a residue that "
                "subtracts book values near 1.09e5, so each reproduces to its conditioning and no "
                "finer; counts, verdicts and the priced PnL differences are exact arithmetic on "
                "the shipped engine"
            ),
            "everything_else": "exact for counts and verdicts, 1e-5 relative for other floats",
        },
        "environment": environment(),
        "artifacts": artifact_manifest([grid_csv, published_csv, cancellation_csv]),
        "csv_rows": len(rows),
    }
    json_path = RESULTS / "restrike_gamma_map.json"
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=False, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload["headline"], indent=2, sort_keys=False))
    print(f"wrote {repo_relative(json_path)}")
    return 0


def _cell(value: Any) -> str:
    """One CSV cell: empty where unmeasured, semicolon list where a set was measured."""
    if value is None:
        return ""
    if isinstance(value, list):
        return ";".join(f"{item!r}" for item in value)
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([_cell(row[column]) for column in columns])


if __name__ == "__main__":
    sys.exit(main())
