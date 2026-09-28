"""Phase 13: what the two-factor bound claims, checked without the experiment's own code.

The experiment builds its bound from closed forms in the C++ core. These tests rebuild the
same quantities from finite differences of the *price* and from the shipped stress engine, so a
wrong closed form cannot confirm itself, and re-read every published figure out of the committed
artifact so the prose cannot drift from the evidence.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import pytest
import quantrisk
from quantrisk import stress as STRESS

REPO_ROOT = Path(__file__).resolve().parents[2]

SPELLIED = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}


def _word_to_int(word: str) -> int:
    try:
        return SPELLIED[word.lower()]
    except KeyError:  # a digits spelling is also a spelling of a number
        return int(word)


EXPERIMENT = REPO_ROOT / "experiments" / "two_factor_error_bound"
RESULTS = EXPERIMENT / "results"
ARTIFACT = RESULTS / "two_factor_bound.json"
CSV_PATH = RESULTS / "two_factor_bound.csv"

SPOT = 100.0
RATE = 0.03
DIVIDEND_YIELD = 0.0
VOLATILITY = 0.20
MATURITY = 0.5
STRIKES = (90.0, 100.0, 110.0)
QUANTITY = 5000.0

# Step and tolerance are chosen together, not one after the other. Reaching a *third* derivative
# of the price amplifies round-off by 1/h^3 against a book value near 1.09e5, while truncation
# falls as h^2; 0.01 in the ray parameter is where the two cross, and Richardson's combination of
# it with its half is what buys the agreement quoted below.
#
# Measured at the three published-size rays and three points along each segment: worst relative
# difference between this and the closed-form assembly is 3.9e-8, against the 1e-6 band here - so
# the band sits 25x outside the largest residual seen, and a partial dropped from the directional
# derivative (which moves these by percent) is not something the slack could hide.
#
# On a small ray the third derivative is a handful of units against that same 1e5 and no step
# recovers it, which is why the inclusion is re-checked at published shock sizes rather than at
# the asymptotic ones the experiment uses for its order claim.
RAY_STEP = 0.01
THIRD_DERIVATIVE_TOLERANCE = 1.0e-6

FIRST_DERIVATIVE_TOLERANCE = 1.0e-6


def _payload() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _csv_rows() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _market(spot: float, sigma: float) -> quantrisk.pricing.MarketParams:
    return quantrisk.pricing.MarketParams(
        spot=spot,
        rate=RATE,
        dividend_yield=DIVIDEND_YIELD,
        volatility=sigma,
        maturity=MATURITY,
    )


def _option(strike: float) -> quantrisk.pricing.EuropeanOption:
    return quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, strike)


def _book_value(spot: float, sigma: float) -> float:
    return (
        sum(
            quantrisk.pricing.black_scholes(_option(strike), _market(spot, sigma)).price
            for strike in STRIKES
        )
        * QUANTITY
    )


def _summed(spot: float, sigma: float, read) -> float:
    return sum(read(_option(strike), _market(spot, sigma)) for strike in STRIKES) * QUANTITY


def _vega(spot: float, sigma: float) -> float:
    return _summed(spot, sigma, lambda o, m: quantrisk.pricing.black_scholes_greeks(o, m).vega)


def _delta_per_relative_move(spot: float, sigma: float) -> float:
    return (
        _summed(spot, sigma, lambda o, m: quantrisk.pricing.black_scholes_greeks(o, m).delta) * spot
    )


def _gamma_map(spot: float, sigma: float) -> float:
    return (
        _summed(spot, sigma, lambda o, m: quantrisk.pricing.black_scholes_greeks(o, m).gamma)
        * 0.5
        * spot
        * spot
    )


def _core_greeks(spot: float, sigma: float) -> tuple[float, float]:
    return (
        _summed(
            spot,
            sigma,
            lambda o, m: quantrisk.pricing.black_scholes_vol_cross_derivatives(o, m).vanna,
        ),
        _summed(
            spot,
            sigma,
            lambda o, m: quantrisk.pricing.black_scholes_vol_cross_derivatives(o, m).volga,
        ),
    )


def _core_thirds(spot: float, sigma: float) -> tuple[float, float, float]:
    return (
        _summed(
            spot,
            sigma,
            lambda o, m: (
                quantrisk.pricing.black_scholes_mixed_third_derivatives(o, m).spot_spot_sigma
            ),
        ),
        _summed(
            spot,
            sigma,
            lambda o, m: (
                quantrisk.pricing.black_scholes_mixed_third_derivatives(o, m).spot_sigma_sigma
            ),
        ),
        _summed(
            spot,
            sigma,
            lambda o, m: (
                quantrisk.pricing.black_scholes_mixed_third_derivatives(o, m).sigma_sigma_sigma
            ),
        ),
    )


def _core_speed(spot: float, sigma: float) -> float:
    return _summed(
        spot, sigma, lambda o, m: quantrisk.pricing.black_scholes_spot_derivatives(o, m).third
    )


def _slope(function, centre: float, step: float) -> float:
    return (
        function(centre - 2 * step)
        - 8.0 * function(centre - step)
        + 8.0 * function(centre + step)
        - function(centre + 2 * step)
    ) / (12.0 * step)


def _third_derivative(function, centre: float, step: float) -> float:
    """Central fifth-point third derivative.

    The coefficient set is derived, not recalled: requiring the stencil to annihilate 1, x, x^2
    and to return 3! = 6 on x^3 gives (-1/2, 1, 0, -1, 1/2) / h^3 in ascending-offset order. The
    more common-looking (1, -2, 0, 2, -1) / (2h^3) returns -*exactly* minus the third derivative,
    which is how it first appeared in this file: same magnitudes, wrong sign, and a comparison
    against a closed form is the only reason it was caught.
    """
    return (
        -0.5 * function(centre - 2 * step)
        + function(centre - step)
        - function(centre + step)
        + 0.5 * function(centre + 2 * step)
    ) / step**3


def _third_derivative_along_ray(h: float, k: float, t: float) -> float:
    """`g'''(t)` for `t -> V(S + t h, sigma + t k)`, from the price alone."""

    def along(offset: float) -> float:
        return _book_value(SPOT + (t + offset) * h, VOLATILITY + (t + offset) * k)

    coarse = _third_derivative(along, 0.0, RAY_STEP)
    fine = _third_derivative(along, 0.0, RAY_STEP / 2.0)
    # The stencil is second order, so the leading error term halves in amplitude when the step
    # halves squared: the combination that cancels it weights `fine` by 4 and divides by 3.
    return (4.0 * fine - coarse) / 3.0


def _directional_third(h: float, k: float, t: float) -> float:
    """The same `g'''(t)`, assembled from the core's closed forms."""
    spot, sigma = SPOT + t * h, VOLATILITY + t * k
    gamma_sigma, vanna_sigma, volga_sigma = _core_thirds(spot, sigma)
    return (
        _core_speed(spot, sigma) * h**3
        + 3.0 * gamma_sigma * h * h * k
        + 3.0 * vanna_sigma * h * k * k
        + volga_sigma * k**3
    )


def _engine_map(delta: float, vol_move: float) -> float:
    """The published map, produced by the shipped engine rather than re-typed here."""
    factors = STRESS.FactorSet()
    factors.factors = [
        STRESS.RiskFactor("EQ0", STRESS.FactorClass.equity_index, SPOT, "index points"),
        STRESS.RiskFactor("VOL", STRESS.FactorClass.volatility, VOLATILITY, "annualised vol"),
    ]
    exposures = STRESS.ExposureVector()
    # Positional by factor: a vega parked on the equity factor is multiplied by that factor's
    # absolute move, which is zero, and disappears without complaint.
    exposures.delta = [_delta_per_relative_move(SPOT, VOLATILITY), 0.0]
    exposures.gamma = [_gamma_map(SPOT, VOLATILITY), 0.0]
    exposures.duration = [0.0, 0.0]
    exposures.vega = [0.0, _vega(SPOT, VOLATILITY)]
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
    handle.shocks = [STRESS.Shock("EQ0", delta, 0.0), STRESS.Shock("VOL", 0.0, vol_move)]
    return float(STRESS.run_scenario(portfolio, handle).pnl_change)


def _true_pnl(delta: float, vol_move: float) -> float:
    return _book_value(SPOT + SPOT * delta, VOLATILITY + vol_move) - _book_value(SPOT, VOLATILITY)


def _error(delta: float, vol_move: float) -> float:
    return _true_pnl(delta, vol_move) - _engine_map(delta, vol_move)


def _quadratic(h: float, k: float) -> float:
    vanna, volga = _core_greeks(SPOT, VOLATILITY)
    return vanna * h * k + 0.5 * volga * k * k


def _log_log_slope(points: list[tuple[float, float]]) -> float:
    xs = [math.log(lead) for lead, _ in points]
    ys = [math.log(magnitude) for _, magnitude in points]
    count = float(len(xs))
    mean_x, mean_y = sum(xs) / count, sum(ys) / count
    denominator = sum((value - mean_x) ** 2 for value in xs)
    return sum((a - mean_x) * (b - mean_y) for a, b in zip(xs, ys, strict=True)) / denominator


def test_the_third_derivative_stencil_recovers_a_known_function() -> None:
    """Before trusting a stencil on the price, prove it on a function whose answer is known.

    Every derivative below is built from this operator, so an error here would otherwise show up
    as a 'wrong closed form' conclusion about the core.
    """
    for centre in (0.0, 0.3, 1.0):
        assert _third_derivative(lambda x: x**3, centre, 1e-2) == pytest.approx(6.0, rel=1e-9)
        assert _third_derivative(lambda x: x**4, centre, 1e-2) == pytest.approx(
            24.0 * centre, rel=1e-6
        )
        # d3/dx3 of sin is -cos, which is the third thing this test caught by being written
        # down rather than derived: the stencil is right and the expectation was not.
        assert _third_derivative(lambda x: math.sin(x), centre, 1e-2) == pytest.approx(
            -math.cos(centre), rel=1e-4
        )


def test_vanna_and_volga_survive_differences_of_the_published_vega() -> None:
    """The quadratic term the whole bound rests on, verified against vega and delta alone."""
    core_vanna, core_volga = _core_greeks(SPOT, VOLATILITY)
    vanna_by_vega = _slope(lambda spot: _vega(spot, VOLATILITY), SPOT, 1.0e-3)
    vanna_by_delta = _slope(lambda sigma: _delta_per_relative_move(SPOT, sigma), VOLATILITY, 1.0e-3)
    volga_by_vega = _slope(lambda sigma: _vega(SPOT, sigma), VOLATILITY, 1.0e-3)

    assert vanna_by_vega == pytest.approx(core_vanna, rel=FIRST_DERIVATIVE_TOLERANCE)
    # Reached through delta, which is a different published Greek, so this route shares no
    # arithmetic with the one above: it is Schwarz's theorem doing the checking.
    assert vanna_by_delta == pytest.approx(core_vanna * SPOT, rel=FIRST_DERIVATIVE_TOLERANCE)
    assert volga_by_vega == pytest.approx(core_volga, rel=FIRST_DERIVATIVE_TOLERANCE)
    assert vanna_by_vega == pytest.approx(
        vanna_by_delta / SPOT, rel=10.0 * FIRST_DERIVATIVE_TOLERANCE
    )


def test_the_mixed_third_partials_survive_differences_taken_the_other_way() -> None:
    """Each third partial reached by differentiating a *second* partial across the other factor."""
    gamma_sigma, vanna_sigma, volga_sigma = _core_thirds(SPOT, VOLATILITY)

    def gamma(spot: float, sigma: float) -> float:
        return _summed(spot, sigma, lambda o, m: quantrisk.pricing.black_scholes_greeks(o, m).gamma)

    step_sigma = 1.0e-4 * VOLATILITY
    step_spot = 1.0e-5 * SPOT
    assert _slope(lambda sigma: gamma(SPOT, sigma), VOLATILITY, step_sigma) == pytest.approx(
        gamma_sigma, rel=10.0 * FIRST_DERIVATIVE_TOLERANCE
    )
    assert _slope(lambda spot: _core_greeks(spot, VOLATILITY)[0], SPOT, step_spot) == pytest.approx(
        gamma_sigma, rel=10.0 * FIRST_DERIVATIVE_TOLERANCE
    )
    assert _slope(
        lambda sigma: _core_greeks(SPOT, sigma)[0], VOLATILITY, step_sigma
    ) == pytest.approx(vanna_sigma, rel=10.0 * FIRST_DERIVATIVE_TOLERANCE)
    assert _slope(lambda spot: _core_greeks(spot, VOLATILITY)[1], SPOT, step_spot) == pytest.approx(
        vanna_sigma, rel=10.0 * FIRST_DERIVATIVE_TOLERANCE
    )
    assert _slope(
        lambda sigma: _core_greeks(SPOT, sigma)[1], VOLATILITY, step_sigma
    ) == pytest.approx(volga_sigma, rel=10.0 * FIRST_DERIVATIVE_TOLERANCE)


def test_the_engine_map_is_the_three_term_formula_the_bound_subtracts() -> None:
    """The algebra in the analysis note has to be the algebra the engine actually runs."""
    for delta, vol_move in ((-0.15, 0.06), (0.15, -0.06), (-0.30, 0.20), (0.02, 0.001)):
        mapped = _engine_map(delta, vol_move)
        hand_built = (
            _delta_per_relative_move(SPOT, VOLATILITY) * delta
            + _gamma_map(SPOT, VOLATILITY) * delta * delta
            + _vega(SPOT, VOLATILITY) * vol_move
        )
        assert mapped == pytest.approx(hand_built, rel=0.0, abs=1.0e-9), (
            "the engine's joint-shock P&L is not delta*s + gamma_map*s^2 + vega*k, so the "
            "quadratic term being subtracted is not the term the map omits"
        )


def test_the_joint_error_is_quadratic_where_the_single_factor_error_is_cubic() -> None:
    """Order 2 against order 3, fitted over scales the experiment does not use."""
    joint_scales = [10.0 ** (-3.0 - index / 8.0) for index in range(9)]
    for direction in ((-0.15, 0.06), (0.15, -0.06), (0.15, 0.06), (0.0, 0.06)):
        points = [
            (scale, abs(_error(direction[0] * scale, direction[1] * scale)))
            for scale in joint_scales
        ]
        slope = _log_log_slope(points)
        assert abs(slope - 2.0) < 0.05, f"{direction}: joint slope {slope:.5f}, not 2"

    spot_scales = [10.0 ** (-2.5 - index / 8.0) for index in range(9)]
    points = [(scale, abs(_error(0.15 * scale, 0.0))) for scale in spot_scales]
    slope = _log_log_slope(points)
    assert abs(slope - 3.0) < 0.05, f"pure-spot slope {slope:.5f}, not 3"


@pytest.mark.parametrize(
    ("delta", "vol_move"),
    [(-0.15, 0.06), (0.15, 0.06), (-0.20, 0.10), (0.15, -0.06)],
)
def test_the_trapped_coefficient_lies_inside_the_price_derived_segment_range(
    delta: float, vol_move: float
) -> None:
    """Claim B, with the bounding function rebuilt from the price rather than the closed forms."""
    h, k = SPOT * delta, vol_move
    samples = [index / 20.0 for index in range(21)]
    from_price = [_third_derivative_along_ray(h, k, t) for t in samples]
    assembled = [_directional_third(h, k, t) for t in samples]
    for actual, expected in zip(from_price, assembled, strict=True):
        assert actual == pytest.approx(
            expected, rel=THIRD_DERIVATIVE_TOLERANCE, abs=THIRD_DERIVATIVE_TOLERANCE * abs(expected)
        ), "the mixed partials are not the third derivative of the price along the same ray"

    low, high = min(from_price), max(from_price)
    residual = _error(delta, vol_move) - _quadratic(h, k)
    trapped = 6.0 * residual
    slack = 10.0 * THIRD_DERIVATIVE_TOLERANCE * max(abs(low), abs(high))
    assert low - slack <= trapped <= high + slack, (
        f"Lagrange's form fails at delta={delta} k={vol_move}: 6*residual {trapped:.6e} outside "
        f"[{low:.6e}, {high:.6e}]"
    )


def test_the_quadratic_leads_only_in_the_limit_and_is_the_wrong_sign_at_published_size() -> None:
    """The honest half of claim A: at report sizes the closed form points the other way."""
    headline = _payload()["headline"]
    for label, ratio in headline["ratio_of_error_to_closed_form_quadratic"].items():
        assert abs(ratio - 1.0) < 0.02, f"{label}: ratio {ratio} is not the leading term"
    published = headline["quadratic_prediction_ratio_at_published_size"]
    assert published < 0.0, (
        f"the closed-form quadratic predicts {published:.4f} x the error on risk_off; the "
        "analysis note says it points the other way at that size, and that is a claim about the "
        "number, not a mood"
    )


def test_the_dominant_omitted_piece_on_risk_off_is_gamma_at_the_wrong_volatility() -> None:
    """Claim C, re-derived from the core rather than read out of the artifact."""
    delta, vol_move = -0.15, 0.06
    h, k = SPOT * delta, vol_move
    core_vanna, core_volga = _core_greeks(SPOT, VOLATILITY)
    gamma_sigma, vanna_sigma, volga_sigma = _core_thirds(SPOT, VOLATILITY)
    terms = {
        "quadratic_vanna": core_vanna * h * k,
        "quadratic_volga": 0.5 * core_volga * k * k,
        "cubic_speed": _core_speed(SPOT, VOLATILITY) * h**3 / 6.0,
        "cubic_gamma_sigma": gamma_sigma * h * h * k / 2.0,
        "cubic_vanna_sigma": vanna_sigma * h * k * k / 2.0,
        "cubic_volga_sigma": volga_sigma * k**3 / 6.0,
    }
    published = _payload()["published_scenario_bound"]
    for name, value in published["omitted_terms_at_base"].items():
        assert terms[name] == pytest.approx(value, rel=0.0, abs=1.0e-9), name
    quadratic = abs(terms["quadratic_vanna"]) + abs(terms["quadratic_volga"])
    assert abs(terms["cubic_gamma_sigma"]) > quadratic, (
        "the ranking the analysis note publishes has reversed"
    )
    assert max(terms, key=lambda name: abs(terms[name])) == "cubic_gamma_sigma"
    ratio = abs(terms["cubic_gamma_sigma"]) / quadratic
    assert ratio == pytest.approx(_payload()["headline"]["largest_cubic_over_quadratic"], rel=1e-9)


def test_the_published_scenario_bounds_the_error_with_a_sign_that_is_proved() -> None:
    """Claim D on the scenario the repository actually ships."""
    published = _payload()["published_scenario_bound"]
    low, high = published["error_interval_low"], published["error_interval_high"]
    assert low < published["error"] < high, "the measured error escaped its own interval"
    assert published["interval_excludes_zero"] and high < 0.0, (
        "the analysis note states the map is reported too high on risk_off; that needs the whole "
        "interval to be negative, not just the point estimate"
    )
    # An interval wider than the quantity it bounds proves nothing about it.
    assert 0.0 < published["interval_width"] < 2.0 * abs(published["error"])


def test_the_scenario_being_bounded_is_the_one_the_stress_experiment_publishes() -> None:
    """The bound is about `risk_off`, so `risk_off`'s numbers cannot move unnoticed."""
    path = REPO_ROOT / "experiments" / "stress_testing" / "run.py"
    spec = importlib.util.spec_from_file_location("stress_experiment_for_bound_check", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    scenario = next(handle for handle in module.scenarios() if handle.name == "risk_off")
    equity = next(shock for shock in scenario.shocks if shock.factor_id == "EQ0")
    volatility = next(shock for shock in scenario.shocks if shock.factor_id == "VOL")

    published = _payload()["published_scenario_bound"]
    assert equity.relative == pytest.approx(published["delta"], rel=0.0, abs=1.0e-15)
    assert volatility.absolute == pytest.approx(published["vol_move"], rel=0.0, abs=1.0e-15)
    assert published["scenario"] == "risk_off"


@pytest.mark.parametrize("label", ["crash (equity down, vol up)", "aligned (equity up, vol up)"])
def test_the_documented_convergence_series_actually_converges(label: str) -> None:
    """A single window reading 2.0 is evidence about the window, not about the order.

    The endpoint pair is asserted, not a per-step ordering. Ordering each step is a comparison of
    ~1e-4 gaps against fit noise of the same size, and the Linux runner is observed to fail it on a
    series every point of which sits within 0.003 of the theory value -- a red CI on a claim that
    was never sound. The whole series is published in the artifact so the trend is visible.
    """
    series = _payload()["slopes"][label]
    distances = [abs(values["slope"] - 2.0) for values in series]
    assert distances[-1] < distances[0], (
        f"{label}: the narrowest window is no closer to 2 than the widest: {distances}"
    )
    assert distances[-1] < 0.15, f"{label}: the limit reading is {distances[-1]}"
    assert len(series) == len({values["window_ceiling"] for values in series})
    assert series[0]["window_ceiling"] > series[-1]["window_ceiling"], "windows are out of order"


def test_the_swept_grid_and_the_published_rows_agree_cell_by_cell() -> None:
    """The CSV is a view of the JSON, not a second copy that is free to disagree."""
    by_cell = {(float(row["delta"]), float(row["vol_move"])): row for row in _csv_rows()}
    payload = _payload()
    assert len(by_cell) == len(payload["rows"]) == payload["headline"]["joint_shocks_swept"]
    assert payload["headline"]["inclusions_violated"] == sum(
        1 for row in payload["rows"] if not row["coefficient_inside_segment_range"]
    )
    for row in payload["rows"]:
        cell = by_cell[(row["delta"], row["vol_move"])]
        assert float(cell["error"]) == pytest.approx(row["error"], rel=0.0, abs=0.0)
        assert cell["dominant_omitted_term"] == row["dominant_omitted_term"]


def test_rerunning_the_experiment_in_a_temporary_tree_reproduces_the_committed_numbers(
    tmp_path: Path,
) -> None:
    """Determinism, without letting the test write into frozen evidence.

    The copy has to sit at the same depth as the original: the experiment locates the published
    scenario by walking up to the repository root, and a bare copy in `tmp_path` would resolve
    that root to a temporary directory.
    """
    destination = tmp_path / "experiments" / "two_factor_error_bound" / "run.py"
    destination.parent.mkdir(parents=True)
    destination.write_text((EXPERIMENT / "run.py").read_text(encoding="utf-8"), encoding="utf-8")
    upstream = tmp_path / "experiments" / "stress_testing"
    upstream.mkdir(parents=True)
    (upstream / "run.py").write_text(
        (REPO_ROOT / "experiments" / "stress_testing" / "run.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    before = ARTIFACT.read_bytes()
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(destination)],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    assert ARTIFACT.read_bytes() == before, "the test run modified a committed artifact"

    produced = destination.parent / "results" / "two_factor_bound.json"
    assert produced.exists(), f"the copy wrote no artifact; stdout: {completed.stdout[-400:]}"
    mine = _payload()
    theirs = json.loads(produced.read_text(encoding="utf-8"))
    volatile = ("generated_at_utc", "environment", "oracles", "artifacts", "figure_status")
    for key in volatile:
        mine.pop(key, None)
        theirs.pop(key, None)
    assert mine == theirs, "the reproduction differs from the committed artifact"


def test_the_refusals_say_what_the_experiment_did_not_estimate() -> None:
    """The scope statements carry the ridge numbers, so they cannot rot into fiction."""
    payload = _payload()
    refusals = {entry["question"]: entry["refused"] for entry in payload["refusals"]}
    assert set(refusals) == {
        "is the scenario plausible?",
        "does the quadratic term locate the direction where the map is exact?",
        "does the bound cover the rate and credit legs?",
        "does the bound hold in the zero-volatility limit?",
    }
    ridge = refusals["does the quadratic term locate the direction where the map is exact?"]
    probe = payload["ridge_probe"]["coarse_scan_root_as_multiple_of_prediction"]
    quoted = [values["root_over_predicted"] for values in probe.values() if values is not None]
    assert quoted, "the probe found the root at no scale, yet the refusal quotes values"
    for value in quoted:
        assert f"{value:.2f}" in ridge, f"the refusal does not quote the measured {value:.4f}"
    assert None in probe.values() or len(quoted) == len(probe), (
        "the refusal says the scan missed at some scale; nothing in the probe shows that"
    )


def test_every_figure_the_finding_and_the_note_quote_is_in_the_artifact() -> None:
    """`docs/findings.md` and the analysis note restate this experiment in prose.

    A number repeated in prose is a number with one more chance to go stale, and this phase
    shipped a documentation defect of exactly that shape in the neighbouring matrix (two rows
    numbered 13). So each figure the two documents print is re-derived here from the artifact,
    formatted the way the prose formats it.
    """
    payload = _payload()
    headline = payload["headline"]
    published = payload["published_scenario_bound"]
    documents = {
        "docs/findings.md": (REPO_ROOT / "docs" / "findings.md").read_text(encoding="utf-8"),
        "docs/analysis/two_factor_error_bound.md": (
            REPO_ROOT / "docs" / "analysis" / "two_factor_error_bound.md"
        ).read_text(encoding="utf-8"),
    }
    crash = headline["slope_of_error_against_shock_size"]["crash (equity down, vol up)"]
    pure_spot = headline["slope_for_a_pure_spot_shock"]
    quadratic = (
        published["omitted_terms_at_base"]["quadratic_vanna"]
        + published["omitted_terms_at_base"]["quadratic_volga"]
    )
    mixed_cubic = published["omitted_terms_at_base"]["cubic_gamma_sigma"]
    expected = {
        "error": f"{published['error']:,.2f}".replace(",", ""),
        "interval_low": f"{published['error_interval_low']:.2f}",
        "interval_high": f"{published['error_interval_high']:.2f}",
        "quadratic_sum": f"{quadratic:.2f}",
        "mixed_cubic": f"{mixed_cubic:.2f}",
        "ratio_of_cubic_to_quadratic": f"{headline['largest_cubic_over_quadratic']:.1f}",
        "crash_slope_narrowest": f"{crash:.4f}",
        "pure_spot_slope": f"{pure_spot:.4f}",
        "joint_shocks": str(headline["joint_shocks_swept"]),
    }
    for name, raw in documents.items():
        # The documents set their numbers in running prose with a typographic minus; the artifact
        # formats one in ASCII. Normalising the sign keeps this a check on the digits rather than
        # on the typography, which is the part that can actually go stale.
        text = raw.replace("\u2212", "-")
        for label, value in expected.items():
            assert value in text, f"{name} does not print {label} as {value!r}"
        for term, count in sorted(payload["dominance_counts"].items()):
            assert str(count) in text, f"{name} omits the {term} dominance count {count}"


def test_the_findings_are_counted_wherever_they_are_counted() -> None:
    """ "N results worth reading" is a fact about `docs/findings.md`, and two files repeat it."""
    text = (REPO_ROOT / "docs" / "findings.md").read_text(encoding="utf-8")
    sections = re.findall(r"^## (\d+)\. ", text, flags=re.M)
    numbers = [int(number) for number in sections]
    assert numbers == list(range(1, len(numbers) + 1)), (
        f"the findings are not numbered 1..N: {numbers}"
    )
    intro = re.search(r"^# Findings\n\n(\w+) results worth", text, flags=re.M)
    assert intro, "docs/findings.md no longer opens with a counted lead-in"
    assert _word_to_int(intro.group(1)) == len(numbers), (
        f"the lead-in says {intro.group(1)} results and the file has {len(numbers)}"
    )
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    claim = re.search(r"The (\w+) results worth reading are in", readme)
    assert claim, "README no longer states how many findings there are"
    assert _word_to_int(claim.group(1)) == len(numbers), (
        f"README says {claim.group(1)}, docs/findings.md has {len(numbers)}"
    )
