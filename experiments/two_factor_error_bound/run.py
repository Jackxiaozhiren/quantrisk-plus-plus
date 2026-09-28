#!/usr/bin/env python3
"""Phase 13 experiment: what a joint spot-and-volatility shock costs the delta-gamma-vega map.

    uv run python experiments/two_factor_error_bound/run.py
    uv run python scripts/run_benchmark_suite.py --only two_factor_error_bound

Phase 12 bounded the error of the stress map when *only* the equity factor moves, and refused
the multi-factor case on the ground that the map is linear in the volatility move. This
experiment takes that refusal apart. The map (`cpp/src/stress/engine.cpp:116`) is

    pnl = delta_i * s_i + gamma_i * s_i**2 + vega_i * a_i,

with `gamma_i` already carrying the one-half and `a_i` an *absolute* vol move, so along the ray
`(h, k) = (S*delta, volatility_move)` from the base market the re-priced book value obeys

    V(S+h, sigma+k) - V(S, sigma)
        = V_S h + 1/2 V_SS h**2 + V_sigma k          <- what the map keeps
        + V_Ssigma h k + 1/2 V_sigsigma k**2         <- order 2, newly omitted
        + 1/6 * g'''(xi)                             <- order 3 in the ray parameter

for some `xi` in (0, 1), where `g'''(t)` is the third directional derivative

    g'''(t) = V_SSS h**3 + 3 V_SSsigma h**2 k + 3 V_Sssigma h k**2 + V_Sssss k**3

evaluated at the market point `(S + t h, sigma + t k)`. Four claims, each of which could have
failed and all of which are checked against `stress.run_scenario` rather than a re-typed map:

  A. Holding `h/k` fixed, the ratio of the map's error to the closed-form quadratic tends to 1
     as the shock shrinks. The map's error is therefore **quadratic** in the joint small
     parameter, where the single-factor case was cubic.
  B. `6 * (error - quadratic)` is trapped between the minimum and maximum of `g'''` along the
     segment - the sharp form of the bound, so a wrong closed form refutes it immediately.
     Checked on a dense grid at and beyond published shock sizes, where the *ratio* in A is
     nowhere near 1: the inclusion holds where the asymptotics stop helping.
  C. At published sizes the largest single omitted piece is neither quadratic term. For the
     repo's own named `risk_off` scenario it is `1/2 V_SSsigma h**2 k` - gamma applied at the
     wrong volatility - which exceeds the whole quadratic by an order of magnitude. That ranks
     what a future map improvement is worth, from closed forms and without re-pricing.
  D. Because the trapped interval excludes zero at that scenario, the *sign* of the map's error
     on the published scenario set is proved rather than estimated: the map is reported too
     high there, by an amount inside a stated interval.

What is deliberately not claimed is in `refusals` below. The sharpest of them is the
direction in which the quadratic vanishes: it is a closed-form prediction, but locating the full
error's counterpart needs a bracket whose useful width shrinks with the shock, and the scan
recorded under `ridge_probe` shows exactly that failure - the root is found at 0.87x the
prediction at one scale, 1.81x at another, and not at all at a third. That is reported as what a
coarse scan can say, and nothing more is claimed from it.

No oracle is called: a bound is not a second implementation of a price. The book, the factor set
and the scenario are the published ones.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import quantrisk
from quantrisk import stress as STRESS
from quantrisk.experiments.metadata import (
    artifact_manifest,
    environment,
    package_versions,
    repo_relative,
    utc_timestamp,
)

RESULTS = Path(__file__).resolve().parent / "results"
REPO_ROOT = Path(__file__).resolve().parents[2]

# The same book as `experiments/stress_testing/run.py:run_linearisation` and
# `experiments/linearisation_error_bound/run.py`: spot 100, three calls at 90/100/110, 5000 each,
# r = 3%, no dividend, sigma = 20%, T = 0.5. Reusing it is the point -- the error bounded here is
# the error of the published map on the published book, not a fresh example chosen to look good.
SPOT = 100.0
RATE = 0.03
DIVIDEND_YIELD = 0.0
VOLATILITY = 0.20
MATURITY = 0.5
STRIKES = (90.0, 100.0, 110.0)
QUANTITY = 5000.0

# Equity shocks and volatility shocks swept on the joint grid. The vol arm spans a rate-of-change
# of 50% of the 20% level, which is a large but not unprecedented equity vol move; the published
# `risk_off` scenario's +6 points sits inside it.
DELTAS = (-0.30, -0.20, -0.15, -0.10, -0.05, -0.02, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30)
VOL_MOVES = (-0.10, -0.06, -0.03, -0.01, 0.0, 0.01, 0.03, 0.06, 0.10, 0.15, 0.20)

# Shrink factors applied to a fixed direction to test the asymptotic ratio. The smallest is chosen
# so the error is still ~1e4 times the double spacing of a book value near 1.09e5; below that the
# ratio measures subtraction noise rather than the Taylor order.
SCALES = (1.0, 0.3, 0.1, 0.03, 0.01, 0.003, 0.001)

SEGMENT_GRID = 601

# Windows over which the log-log slope of the error is fitted, per direction. Reported as a
# convergence series rather than one number, for the reason Phase 12 learned: a single fitted
# slope over a wide window is evidence about the window, not about the order.
SLOPE_WINDOWS = ((1e-4, 0.02), (1e-4, 0.005), (1e-5, 0.001), (1e-6, 2e-4))


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


def totals(spot: float, sigma: float) -> dict[str, float]:
    """Every sensitivity the two-factor expansion needs, summed over the book.

    Each entry is in the units the stress layer quotes exposures in: per unit *relative* move for
    `delta` and per unit *absolute* move for `vega`, so the map and the expansion consume the same
    numbers.
    """
    m = market(spot, sigma)
    out: dict[str, float] = {}
    readings = {
        "delta": lambda o: quantrisk.pricing.black_scholes_greeks(o, m).delta * SPOT,
        "gamma": lambda o: 0.5 * quantrisk.pricing.black_scholes_greeks(o, m).gamma * SPOT * SPOT,
        "vega": lambda o: quantrisk.pricing.black_scholes_greeks(o, m).vega,
        "speed": lambda o: quantrisk.pricing.black_scholes_spot_derivatives(o, m).third,
        "vanna": lambda o: quantrisk.pricing.black_scholes_vol_cross_derivatives(o, m).vanna,
        "volga": lambda o: quantrisk.pricing.black_scholes_vol_cross_derivatives(o, m).volga,
        "gamma_sigma": lambda o: (
            quantrisk.pricing.black_scholes_mixed_third_derivatives(o, m).spot_spot_sigma
        ),
        "vanna_sigma": lambda o: (
            quantrisk.pricing.black_scholes_mixed_third_derivatives(o, m).spot_sigma_sigma
        ),
        "volga_sigma": lambda o: (
            quantrisk.pricing.black_scholes_mixed_third_derivatives(o, m).sigma_sigma_sigma
        ),
    }
    for name, read in readings.items():
        out[name] = sum(read(option(strike)) for strike in STRIKES) * QUANTITY
    return out


BASE = totals(SPOT, VOLATILITY)


def published_scenario(name: str = "risk_off") -> dict[str, float]:
    """The named scenario's equity and volatility moves, read from the stress experiment itself.

    Imported rather than re-typed: the bound in claim D is a statement about the scenario the
    repository actually publishes, and a copy of its numbers here could go stale against it
    silently.
    """
    path = REPO_ROOT / "experiments" / "stress_testing" / "run.py"
    spec = importlib.util.spec_from_file_location("quantrisk_stress_experiment_for_bound", path)
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


def engine_map(delta: float, vol_move: float) -> tuple[float, Any]:
    """The map as the shipped engine produces it, on the published book."""
    factors = STRESS.FactorSet()
    factors.factors = [
        STRESS.RiskFactor("EQ0", STRESS.FactorClass.equity_index, SPOT, "index points"),
        STRESS.RiskFactor("VOL", STRESS.FactorClass.volatility, VOLATILITY, "annualised vol"),
    ]
    exposures = STRESS.ExposureVector()
    # Every block is indexed by FACTOR POSITION, so each sensitivity sits on the factor that
    # carries it -- see the NOTE at tests/cpp/test_stress_engine.cpp:191. A vega parked on the
    # equity factor is multiplied by that factor's absolute move, which is zero, and vanishes
    # without a word.
    exposures.delta = [BASE["delta"], 0.0]
    exposures.gamma = [BASE["gamma"], 0.0]
    exposures.duration = [0.0, 0.0]
    exposures.vega = [0.0, BASE["vega"]]
    exposures.credit = [0.0, 0.0]
    position = STRESS.Position()
    position.name = "option_book"
    position.exposures = exposures
    portfolio = STRESS.Portfolio()
    portfolio.factors = factors
    portfolio.positions = [position]

    handle = STRESS.Scenario()
    handle.name = "joint_probe"
    handle.kind = STRESS.ScenarioKind.deterministic
    handle.assumptions = "equity relative move and volatility absolute move, nothing else"
    handle.shocks = [
        STRESS.Shock("EQ0", delta, 0.0),
        STRESS.Shock("VOL", 0.0, vol_move),
    ]
    result = STRESS.run_scenario(portfolio, handle)
    return float(result.pnl_change), result


def third_directional(h: float, k: float, t: float) -> float:
    """`g'''(t)` for the ray `(S + t h, sigma + t k)`, from the closed forms."""
    at = totals(SPOT + t * h, VOLATILITY + t * k)
    return (
        at["speed"] * h**3
        + 3.0 * at["gamma_sigma"] * h * h * k
        + 3.0 * at["vanna_sigma"] * h * k * k
        + at["volga_sigma"] * k**3
    )


def segment_extremes(h: float, k: float) -> tuple[float, float]:
    values = [third_directional(h, k, index / (SEGMENT_GRID - 1)) for index in range(SEGMENT_GRID)]
    return min(values), max(values)


def terms_at_base(h: float, k: float) -> dict[str, float]:
    """Each omitted piece, evaluated at the base market.

    These are not an approximation of the error being fitted for; they are the quantities the
    bound is assembled from, and claim C reads its ranking off them.
    """
    return {
        "quadratic_vanna": BASE["vanna"] * h * k,
        "quadratic_volga": 0.5 * BASE["volga"] * k * k,
        "cubic_speed": BASE["speed"] * h**3 / 6.0,
        "cubic_gamma_sigma": BASE["gamma_sigma"] * h * h * k / 2.0,
        "cubic_vanna_sigma": BASE["vanna_sigma"] * h * k * k / 2.0,
        "cubic_volga_sigma": BASE["volga_sigma"] * k**3 / 6.0,
    }


def probe(delta: float, vol_move: float) -> dict[str, Any]:
    """The map's error on one joint shock, without the segment scan.

    `bound` is the full statement and costs a 601-point walk of the third directional derivative;
    the ratio and slope series below evaluate the error at hundreds of points, where only the
    error itself varies. Calling `bound` there would multiply the runtime by the grid size to
    compute a number the claim does not use.
    """
    h = SPOT * delta
    k = vol_move
    mapped, _ = engine_map(delta, k)
    true = book_value(SPOT + h, VOLATILITY + k) - book_value(SPOT, VOLATILITY)
    error = true - mapped
    quadratic = BASE["vanna"] * h * k + 0.5 * BASE["volga"] * k * k
    return {
        "delta": delta,
        "vol_move": k,
        "error": error,
        "quadratic_term": quadratic,
        "error_over_quadratic": error / quadratic if quadratic else None,
    }


def bound(delta: float, vol_move: float, *, with_interval: bool = True) -> dict[str, Any]:
    """The map's error on one joint shock, optionally with its rigorous interval.

    The interval costs a 601-point walk of the third directional derivative. The ratio and slope
    series evaluate the error at hundreds of shock sizes where only the error itself varies, so
    they pass `with_interval=False`; running them with the walk would multiply the runtime by the
    grid size to compute a number those claims do not use.
    """
    h = SPOT * delta
    k = vol_move
    mapped, result = engine_map(delta, k)
    true = book_value(SPOT + h, VOLATILITY + k) - book_value(SPOT, VOLATILITY)
    error = true - mapped
    quadratic = BASE["vanna"] * h * k + 0.5 * BASE["volga"] * k * k
    residual = error - quadratic
    terms = terms_at_base(h, k)
    if not with_interval:
        return {
            "delta": delta,
            "vol_move": k,
            "error": error,
            "quadratic_term": quadratic,
            "error_over_quadratic": error / quadratic if quadratic else None,
            "residual_after_quadratic": residual,
        }
    low, high = segment_extremes(h, k)
    # Lagrange's form puts 6*residual *exactly* on g'''(xi) for some xi in (0,1), so the interval
    # for the error is the segment's own range translated by the quadratic.
    return {
        "delta": delta,
        "vol_move": k,
        "spot_move_absolute": h,
        "revalued_pnl": true,
        "engine_pnl": mapped,
        "error": error,
        "relative_error": error / abs(true) if true else None,
        "quadratic_term": quadratic,
        "error_over_quadratic": error / quadratic if quadratic else None,
        "residual_after_quadratic": residual,
        "trapped_coefficient": 6.0 * residual,
        "segment_min_third_directional": low,
        "segment_max_third_directional": high,
        "coefficient_inside_segment_range": bool(low - 1e-8 <= 6.0 * residual <= high + 1e-8),
        "error_interval_low": quadratic + low / 6.0,
        "error_interval_high": quadratic + high / 6.0,
        "interval_excludes_zero": bool(
            (quadratic + low / 6.0 > 0.0) or (quadratic + high / 6.0 < 0.0)
        ),
        "interval_width": (high - low) / 6.0,
        "interval_width_over_error": ((high - low) / 6.0) / abs(error) if error else None,
        "omitted_terms_at_base": terms,
        "dominant_omitted_term": max(terms, key=lambda name: abs(terms[name])),
        "volatility_attribution": float(result.by_factor[1].volatility),
    }


def ratio_series(direction: tuple[float, float]) -> list[dict[str, Any]]:
    """Claim A: shrink a fixed joint ray and watch the error become the closed-form quadratic.

    `direction` is a point on the ray at scale 1, so the ratio `h/k` is held fixed while both
    shrink together. Shrinking only one of them is a different claim and gives a different order.
    """
    unit_delta, unit_vol = direction
    rows = []
    for scale in SCALES:
        row = bound(unit_delta * scale, unit_vol * scale, with_interval=False)
        rows.append(
            {
                "direction_equity": unit_delta,
                "direction_volatility": unit_vol,
                "scale": scale,
                "error": row["error"],
                "quadratic_term": row["quadratic_term"],
                "ratio": row["error_over_quadratic"],
            }
        )
    return rows


def fit_slope(points: list[tuple[float, float]], label: str) -> dict[str, Any]:
    """Least-squares log-log slope, with its standard error.

    Points are `(norm, |error|)` pairs on one ray. A zero or negative error is a hard failure
    rather than a dropped point: dropping it would silently shorten the window the claim was
    fitted over.
    """
    if len(points) < 3:
        raise RuntimeError(f"{label}: only {len(points)} points to fit a slope over")
    xs, ys = [], []
    for norm, magnitude in points:
        if norm <= 0.0 or magnitude <= 0.0:
            raise RuntimeError(f"{label}: cannot take a log of {norm} / {magnitude}")
        xs.append(math.log(norm))
        ys.append(math.log(magnitude))
    n = float(len(xs))
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0.0:
        raise RuntimeError(f"{label}: degenerate fit window")
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / denominator
    intercept = mean_y - slope * mean_x
    residual_sum = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys, strict=True))
    standard_error = math.sqrt(residual_sum / (n - 2.0) / denominator) if n > 2 else None
    return {
        "slope": slope,
        "standard_error": standard_error,
        "points": len(points),
        "window_low": min(norm for norm, _ in points),
        "window_high": max(norm for norm, _ in points),
    }


def slope_series(direction: tuple[float, float]) -> list[dict[str, Any]]:
    """The log-log slope of the map's error along one ray, over successively narrower windows."""
    unit_delta, unit_vol = direction
    points: list[tuple[float, float]] = []
    for magnitude in [10.0 ** (-4.0 + index / 20.0) for index in range(81)]:
        delta = unit_delta * magnitude
        vol_move = unit_vol * magnitude
        row = bound(delta, vol_move, with_interval=False)
        points.append((math.hypot(delta, vol_move), abs(row["error"])))
    out = []
    for ceiling in (0.02, 0.005, 0.001, 2e-4):
        window = [point for point in points if point[0] <= ceiling]
        values = fit_slope(window, f"direction {direction} ceiling {ceiling}")
        values["window_ceiling"] = ceiling
        out.append(values)
    return out


def sweep_rows() -> list[dict[str, Any]]:
    rows = []
    for delta in DELTAS:
        for vol_move in VOL_MOVES:
            if vol_move == 0.0 and abs(delta) < 1e-12:
                continue
            rows.append(bound(delta, vol_move))
    return rows


def risk_off_row() -> dict[str, Any]:
    published = published_scenario("risk_off")
    row = bound(published["equity"], published["volatility"])
    row["scenario"] = "risk_off"
    row["source"] = "experiments/stress_testing/run.py:scenarios()"
    return row


def ridge_probe() -> dict[str, Any]:
    """What a coarse scan can and cannot say about the quadratic's zero direction.

    Recorded because the temptation to claim the ridge is *verified* is the sharpest wrong turn
    available in this experiment. The closed forms predict a direction where the joint error is
    smaller than its neighbours; measuring where the full error's root sits requires a bracket
    whose useful width shrinks with the shock, so a fixed scan finds it at one scale and not at
    another, and that difference is an artefact of the scan.
    """
    predicted = -2.0 * BASE["vanna"] / BASE["volga"]
    h0 = -15.0
    grid = sorted(predicted * factor / 2.0 for factor in range(1, 40))

    def error_at(scale: float, ratio: float) -> float:
        h = scale * h0
        return bound(h / SPOT, ratio * h, with_interval=False)["error"]

    found: dict[str, Any] = {}
    for scale in (1.0, 0.5, 0.1):
        values = [(ratio, error_at(scale, ratio)) for ratio in grid]
        root = None
        for (left, left_error), (right, right_error) in zip(values, values[1:], strict=False):
            if left_error == 0.0 or left_error * right_error < 0.0:
                low, high, low_error = left, right, left_error
                for _ in range(70):
                    middle = 0.5 * (low + high)
                    middle_error = error_at(scale, middle)
                    if low_error * middle_error <= 0.0:
                        high = middle
                    else:
                        low, low_error = middle, middle_error
                root = 0.5 * (low + high)
                break
        found[f"scale {scale:g}"] = (
            None if root is None else {"root_over_predicted": root / predicted}
        )
    return {
        "predicted_k_over_h": predicted,
        "predicted_vol_move_at_published_spot_leg": predicted * h0,
        "coarse_scan_root_as_multiple_of_prediction": found,
        "grid_points": len(grid),
    }


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    ridge = ridge_probe()
    located = [
        value["root_over_predicted"]
        for value in ridge["coarse_scan_root_as_multiple_of_prediction"].values()
        if value is not None
    ]

    rows = sweep_rows()
    violations = [row for row in rows if not row["coefficient_inside_segment_range"]]
    if violations:
        first = violations[0]
        raise RuntimeError(
            f"the Lagrange inclusion fails on {len(violations)} of {len(rows)} joint shocks, "
            f"first at delta={first['delta']:.4f} k={first['vol_move']:.4f}: 6*residual "
            f"{first['trapped_coefficient']:.6e} outside "
            f"[{first['segment_min_third_directional']:.6e}, "
            f"{first['segment_max_third_directional']:.6e}]"
        )

    # A. the error is quadratic in the joint parameter, per direction.
    directions = {
        "crash (equity down, vol up)": (-0.15, 0.06),
        "melt-up (equity up, vol down)": (0.15, -0.06),
        "aligned (equity up, vol up)": (0.15, 0.06),
        "pure volatility": (0.0, 0.06),
    }
    asymptotics: dict[str, list[dict[str, Any]]] = {}
    slopes: dict[str, list[dict[str, Any]]] = {}
    # The rays are used exactly as quoted, not rescaled to unit length: a log-log slope is
    # invariant to a constant factor on the horizontal axis, and normalising "melt-up" to a unit
    # vector pushed its volatility leg to -0.17, which is not a market.
    for label, direction in directions.items():
        asymptotics[label] = ratio_series(direction)
        slopes[label] = slope_series(direction)

    # `SCALES` runs from the widest shock to the narrowest, so `series[-1]` is the limit and each
    # step inward must land closer to 1. A single window would only show that the window happens
    # to be small -- Phase 12 learned that the hard way.
    for label, series in asymptotics.items():
        narrowest = series[-1]
        if narrowest["ratio"] is None:
            raise RuntimeError(f"{label}: the quadratic term vanished, so the ratio is undefined")
        if abs(narrowest["ratio"] - 1.0) > 0.02:
            raise RuntimeError(
                f"{label}: at scale {narrowest['scale']} the error is "
                f"{narrowest['ratio']:.6f} of the closed-form quadratic, not ~1, so the map is "
                "not losing a second-order term along this direction"
            )
        previous = None
        for values in series:
            ratio = values["ratio"]
            if ratio is None:
                continue
            if previous is not None and abs(ratio - 1.0) > abs(previous - 1.0) + 1e-12:
                raise RuntimeError(
                    f"{label}: the ratio moved *away* from 1 as the shock shrank "
                    f"({previous:.8f} -> {ratio:.8f}), so what dominates at the small end is not "
                    "the second-order term"
                )
            previous = ratio

    # The order itself: the joint directions must fit 2, and the pure-spot ray must still fit 3.
    pure_spot = slope_series((0.15, 0.0))
    joint_expected = {
        "crash (equity down, vol up)": 2.0,
        "melt-up (equity up, vol down)": 2.0,
        "aligned (equity up, vol up)": 2.0,
        "pure volatility": 2.0,
    }
    for label, expected in joint_expected.items():
        narrowest = slopes[label][-1]
        if abs(narrowest["slope"] - expected) > 0.15:
            raise RuntimeError(
                f"{label}: the fitted log-log slope is {narrowest['slope']:.5f}, not {expected}, "
                f"over a window ending at {narrowest['window_ceiling']}"
            )
        # One window that happens to read 2 is evidence about the window, not about the order:
        # each narrower window has to land closer to the theory value than the one before it.
        previous = None
        for values in slopes[label]:
            if previous is not None and abs(values["slope"] - expected) >= abs(previous - expected):
                raise RuntimeError(
                    f"{label}: narrowing the fit window did not bring the slope closer to "
                    f"{expected} ({previous:.6f} -> {values['slope']:.6f}), so the reading is not "
                    "the second-order term dominating"
                )
            previous = values["slope"]
    if abs(pure_spot[-1]["slope"] - 3.0) > 0.15:
        raise RuntimeError(
            f"the pure-spot ray's slope is {pure_spot[-1]['slope']:.5f}, not 3: Phase 12's cubic "
            "result and this one disagree, so one of them is wrong"
        )
    previous = None
    for values in pure_spot:
        if previous is not None and abs(values["slope"] - 3.0) >= abs(previous - 3.0):
            raise RuntimeError(
                "the pure-spot ray's slope did not converge toward 3 as the window narrowed "
                f"({previous:.6f} -> {values['slope']:.6f})"
            )
        previous = values["slope"]

    # C. what actually dominates at published sizes. The quadratic is the *leading* term in the
    # limit and a minority term at the sizes a stress report contains, and both halves of that
    # sentence are load-bearing, so each is a guard rather than a comment.
    published = risk_off_row()
    terms = published["omitted_terms_at_base"]
    quadratic_total = abs(terms["quadratic_vanna"]) + abs(terms["quadratic_volga"])
    dominant = published["dominant_omitted_term"]
    if quadratic_total == 0.0:
        raise RuntimeError("the quadratic term is zero for the published scenario")
    largest_cubic = max(abs(value) for name, value in terms.items() if name.startswith("cubic_"))
    if largest_cubic <= quadratic_total:
        raise RuntimeError(
            "the prose claims a cubic term dominates the quadratic at the published risk_off "
            f"scenario, and it does not: largest cubic {largest_cubic:.6e} vs quadratic "
            f"{quadratic_total:.6e}"
        )
    if dominant != "cubic_gamma_sigma":
        raise RuntimeError(
            f"the dominant omitted term on risk_off is {dominant!r}, not the gamma-at-the-wrong-"
            "volatility piece the analysis note names"
        )

    # D. the interval's sign, on the published scenario.
    if not published["interval_excludes_zero"]:
        raise RuntimeError(
            "the prose claims the map's error on risk_off has a proved sign, and the Lagrange "
            f"interval [{published['error_interval_low']:.4f}, "
            f"{published['error_interval_high']:.4f}] straddles zero"
        )

    # Which term dominates, across the whole joint grid: the geography claim, counted rather than
    # asserted from one cell.
    dominance: dict[str, int] = {}
    for row in rows:
        dominance[row["dominant_omitted_term"]] = dominance.get(row["dominant_omitted_term"], 0) + 1

    scope = [
        {
            "question": "is the scenario plausible?",
            "refused": "a bound on the map says how much of a stress number is Taylor truncation "
            "and nothing about how much is choice. The scenario set has no oracle and this "
            "experiment does not manufacture one (docs/validation_matrix.md row 12).",
        },
        {
            "question": "does the quadratic term locate the direction where the map is exact?",
            "refused": "the quadratic form k*(vanna*h + 0.5*volga*k) does have a non-trivial zero "
            "at k/h = -2*vanna/volga = "
            f"{-2.0 * BASE['vanna'] / BASE['volga']:.8f}, which is a closed-form prediction of a "
            "direction along which the joint error is smaller than its neighbours. Its measured "
            "counterpart is not located here: as the ray shrinks, the window in which the full "
            "error dips below zero narrows in proportion to the shock size, so bracketing it needs "
            "a resolution that scales with the very parameter being sent to zero. A coarse scan "
            f"locates it at {str(sorted(located)) if located else 'nowhere'} of the predicted "
            "ratio across three scales, which is a fact about the scan and not about the ridge. "
            "Claiming the agreement, or its absence, from that would be the sloppiest move "
            "available here, so neither is claimed.",
        },
        {
            "question": "does the bound cover the rate and credit legs?",
            "refused": "no. Two factors are in scope - the equity index and the volatility level - "
            "and the book is the equity option book. The published risk_off scenario also moves "
            "rates by -50bp and credit by +100bp, mapped linearly by duration and credit "
            "sensitivity; the omitted convexity in those factors is a different pair of "
            "derivatives and is not bounded here.",
        },
        {
            "question": "does the bound hold in the zero-volatility limit?",
            "refused": "it degenerates, for the same reason Phase 12's does: the core returns zero "
            "for every higher derivative when sigma*sqrt(T) -> 0, so the inclusion reads 0 <= 0.",
        },
    ]

    payload = {
        "schema": "quantrisk.two_factor_error_bound.v1",
        "generated_at_utc": utc_timestamp(),
        "command": "uv run python experiments/two_factor_error_bound/run.py",
        "claim": (
            "the delta-gamma-vega stress map loses a quadratic term under a joint spot and "
            "volatility shock, that term is closed-form, and the residual left by subtracting it "
            "is trapped by the third directional derivative along the shock ray"
        ),
        "book": {
            "spot": SPOT,
            "rate": RATE,
            "dividend_yield": DIVIDEND_YIELD,
            "volatility": VOLATILITY,
            "maturity": MATURITY,
            "strikes": list(STRIKES),
            "quantity": QUANTITY,
            "base_value": book_value(SPOT, VOLATILITY),
            "source": "experiments/stress_testing/run.py:run_linearisation",
        },
        "base_exposures": {
            **BASE,
            "convention": (
                "delta per unit relative move, gamma carries the one-half, vega per unit absolute "
                "vol move; the rest are the Taylor coefficients of the same book value"
            ),
        },
        "map": {
            "implemented_in": "cpp/src/stress/engine.cpp",
            "expression": "delta_i * s_i + gamma_i * s_i^2 + vega_i * a_i",
            "volatility_term_is_linear": True,
            "produced_by": "quantrisk.stress.run_scenario",
        },
        "headline": {
            # Measured values, not `all(...)` booleans: every claim here is also a guard that
            # raises, so a boolean would be a fact about the control flow rather than about the
            # market. The numbers are what a reader and the prose-coupling test can both check.
            "joint_shocks_swept": len(rows),
            "inclusions_violated": len(violations),
            "slope_of_error_against_shock_size": {
                label: series[-1]["slope"] for label, series in slopes.items()
            },
            "slope_for_a_pure_spot_shock": pure_spot[-1]["slope"],
            "ratio_of_error_to_closed_form_quadratic": {
                label: series[-1]["ratio"] for label, series in asymptotics.items()
            },
            "published_scenario": published["scenario"],
            "published_error": published["error"],
            "published_error_interval": [
                published["error_interval_low"],
                published["error_interval_high"],
            ],
            "published_interval_excludes_zero": published["interval_excludes_zero"],
            "published_interval_width_over_error": published["interval_width_over_error"],
            "dominant_omitted_term": dominant,
            "largest_cubic_over_quadratic": largest_cubic / quadratic_total,
            "quadratic_prediction_ratio_at_published_size": published["error_over_quadratic"],
        },
        "asymptotics": asymptotics,
        "slopes": {**slopes, "pure spot (k=0)": pure_spot},
        "dominance_counts": dominance,
        "published_scenario_bound": published,
        "ridge_probe": ridge,
        "refusals": scope,
        "provenance": {
            "no_oracle_called": True,
            "reason": "a bound is not a second implementation of a price",
            "closed_forms": [
                "black_scholes_spot_derivatives",
                "black_scholes_vol_cross_derivatives",
                "black_scholes_mixed_third_derivatives",
            ],
        },
        "rows": rows,
        "environment": environment(),
        "oracles": {
            "tool": "none used; a bound is not a second implementation of a price",
            "versions": package_versions(),
            "closed_forms supplying the bound": [
                "black_scholes_spot_derivatives",
                "black_scholes_vol_cross_derivatives",
                "black_scholes_mixed_third_derivatives",
            ],
        },
    }

    csv_path = RESULTS / "two_factor_bound.csv"
    write_csv(
        csv_path,
        [
            {key: value for key, value in row.items() if key != "omitted_terms_at_base"}
            | {f"term_{name}": value for name, value in row["omitted_terms_at_base"].items()}
            for row in rows
        ],
    )
    published_csv_path = RESULTS / "published_scenario_bound.csv"
    write_csv(
        published_csv_path,
        [
            {
                "scenario": row["scenario"],
                "delta": row["delta"],
                "vol_move": row["vol_move"],
                "revalued_pnl": row["revalued_pnl"],
                "engine_pnl": row["engine_pnl"],
                "error": row["error"],
                "error_interval_low": row["error_interval_low"],
                "error_interval_high": row["error_interval_high"],
                "interval_excludes_zero": row["interval_excludes_zero"],
                "quadratic_term": row["quadratic_term"],
                "dominant_omitted_term": row["dominant_omitted_term"],
                **{f"term_{name}": value for name, value in row["omitted_terms_at_base"].items()},
            }
            for row in (published,)
        ],
    )
    figure_path = RESULTS / "two_factor_bound.png"
    payload["figure_status"] = make_figure(asymptotics, rows, published, figure_path)
    payload["artifacts"] = artifact_manifest([csv_path, published_csv_path, figure_path])

    json_path = RESULTS / "two_factor_bound.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(json.dumps(payload["headline"], indent=2))
    print(f"wrote {repo_relative(json_path)}")
    return 0


def make_figure(
    asymptotics: dict[str, list[dict[str, Any]]],
    rows: list[dict[str, Any]],
    published: dict[str, Any],
    path: Path,
) -> str:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return "not generated (matplotlib unavailable)"

    figure, axes = plt.subplots(1, 2, figsize=(11.4, 4.4))

    axis = axes[0]
    for label, series in asymptotics.items():
        scales = [values["scale"] for values in series]
        axis.loglog(scales, [abs(values["error"]) for values in series], marker="o", label=label)
        axis.loglog(
            scales,
            [abs(values["quadratic_term"]) for values in series],
            ls=":",
            lw=1.0,
            color=axis.lines[-1].get_color(),
        )
    axis.set_xlabel("shock scale (both legs shrink together)")
    axis.set_ylabel("|map error|")
    axis.set_title("Errors (solid) against the closed-form quadratic (dotted)")
    axis.legend(fontsize=7)
    axis.grid(True, which="both", alpha=0.25)

    axis = axes[1]
    leg = [
        row
        for row in rows
        if math.isclose(row["delta"], published["delta"], rel_tol=0.0, abs_tol=1e-12)
    ]
    if not leg:
        return "not generated (no swept row matches the published scenario's equity leg)"
    leg.sort(key=lambda row: row["vol_move"])
    axis.axhline(0.0, color="black", lw=0.8)
    axis.plot(
        [row["vol_move"] for row in leg],
        [row["error"] for row in leg],
        marker="o",
        label="re-pricing minus map",
    )
    axis.fill_between(
        [row["vol_move"] for row in leg],
        [row["error_interval_low"] for row in leg],
        [row["error_interval_high"] for row in leg],
        alpha=0.25,
        label="Lagrange interval",
    )
    axis.axvline(published["vol_move"], color="tab:red", ls="--", lw=1.0)
    axis.set_xlabel("volatility move (absolute)")
    axis.set_ylabel("P&L error")
    axis.set_title(
        f"equity {published['delta']:+.0%}; risk_off at the red line,\n"
        f"interval [{published['error_interval_low']:.0f}, "
        f"{published['error_interval_high']:.0f}] excludes zero"
    )
    axis.legend(fontsize=7)
    axis.grid(True, alpha=0.25)

    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return f"wrote {repo_relative(path)}"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    field_names = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
