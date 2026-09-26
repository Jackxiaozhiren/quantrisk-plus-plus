"""Phase 2 Python-side validation of the deterministic pricing core.

The strongest check here is ``test_black_scholes_matches_an_independent_recomputation``:
the price is recomputed in the test from the formulas in
docs/mathematical_specification.md §2 using SciPy's normal CDF, which is a
different code path from the C++ core. A transcription error in the core - a
swapped ``d1``/``d2``, a missing ``e^{-qT}`` - cannot survive it, and no
QuantLib number is pasted in anywhere.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import quantrisk

pricing = quantrisk.pricing

scipy_stats = pytest.importorskip("scipy.stats")

MARKETS = [
    {"spot": 100.0, "rate": 0.05, "dividend_yield": 0.0, "volatility": 0.2, "maturity": 1.0},
    {"spot": 100.0, "rate": 0.05, "dividend_yield": 0.02, "volatility": 0.35, "maturity": 0.25},
    {"spot": 45.0, "rate": -0.01, "dividend_yield": 0.04, "volatility": 0.6, "maturity": 3.0},
    {"spot": 400.0, "rate": 0.08, "dividend_yield": 0.03, "volatility": 0.15, "maturity": 0.02},
    {"spot": 1.0, "rate": 0.2, "dividend_yield": 0.1, "volatility": 0.9, "maturity": 0.5},
]
STRIKES = [1.0, 10.0, 45.0, 99.0, 100.0, 101.0, 400.0, 1000.0]


def make_market(**overrides) -> pricing.MarketParams:
    parameters = {
        "spot": 100.0,
        "rate": 0.05,
        "dividend_yield": 0.0,
        "volatility": 0.2,
        "maturity": 1.0,
        **overrides,
    }
    return pricing.MarketParams(**parameters)


def reference_black_scholes(is_call: bool, market: dict[str, float], strike: float) -> float:
    """Independent recomputation of docs/mathematical_specification.md §2."""
    if market["maturity"] == 0.0 or market["volatility"] == 0.0:
        forward = market["spot"] * math.exp(
            (market["rate"] - market["dividend_yield"]) * market["maturity"]
        )
        discount = math.exp(-market["rate"] * market["maturity"])
        payoff = max(forward - strike, 0.0) if is_call else max(strike - forward, 0.0)
        return discount * payoff
    root_t = math.sqrt(market["maturity"])
    sigma = market["volatility"]
    first = (
        math.log(market["spot"] / strike)
        + (market["rate"] - market["dividend_yield"] + 0.5 * sigma * sigma) * market["maturity"]
    ) / (sigma * root_t)
    second = first - sigma * root_t
    growth_discount = math.exp(-market["dividend_yield"] * market["maturity"])
    rate_discount = math.exp(-market["rate"] * market["maturity"])
    norm = scipy_stats.norm
    if is_call:
        return market["spot"] * growth_discount * norm.cdf(
            first
        ) - strike * rate_discount * norm.cdf(second)
    return strike * rate_discount * norm.cdf(-second) - market["spot"] * growth_discount * norm.cdf(
        -first
    )


@pytest.mark.parametrize("parameters", MARKETS)
@pytest.mark.parametrize("strike", STRIKES)
def test_black_scholes_matches_an_independent_recomputation(
    parameters: dict[str, float], strike: float
) -> None:
    market = make_market(**parameters)
    for is_call, option_type in (
        (True, pricing.OptionType.CALL),
        (False, pricing.OptionType.PUT),
    ):
        ours = pricing.black_scholes(pricing.EuropeanOption(option_type, strike), market).price
        expected = reference_black_scholes(is_call, parameters, strike)
        scale = max(abs(expected), 1.0e-8)
        assert abs(ours - expected) <= 1.0e-10 * scale + 1.0e-12, (
            f"{parameters} K={strike} call={is_call}: {ours} vs {expected}"
        )


def test_put_call_parity_holds_to_rounding() -> None:
    for parameters in MARKETS:
        market = make_market(**parameters)
        for strike in STRIKES:
            residual = pricing.put_call_parity_residual(market, strike)
            scale = max(market.spot + strike, 1.0)
            assert abs(residual) < 1.0e-12 * scale, (parameters, strike, residual)


def test_degenerate_edges_use_their_limits() -> None:
    expired = make_market(maturity=0.0, volatility=0.2)
    assert pricing.black_scholes(
        pricing.EuropeanOption(pricing.OptionType.CALL, 90.0), expired
    ).price == pytest.approx(10.0, abs=1.0e-14)
    result = pricing.black_scholes(pricing.EuropeanOption(pricing.OptionType.CALL, 100.0), expired)
    assert "T == 0" in result.note
    assert math.isnan(result.d1) and math.isnan(result.d2)

    flat = make_market(volatility=0.0, rate=0.05, dividend_yield=0.02, maturity=1.0)
    forward = 100.0 * math.exp(0.03)
    expected = math.exp(-0.05) * max(forward - 100.0, 0.0)
    assert pricing.black_scholes(
        pricing.EuropeanOption(pricing.OptionType.CALL, 100.0), flat
    ).price == pytest.approx(expected, rel=1.0e-14)


@pytest.mark.parametrize("option_type", [pricing.OptionType.CALL, pricing.OptionType.PUT])
def test_price_bounds_and_monotonicity(option_type: pricing.OptionType) -> None:
    previous = -1.0
    for volatility in (0.0, 0.05, 0.1, 0.25, 0.5, 1.0):
        value = pricing.black_scholes(
            pricing.EuropeanOption(option_type, 100.0), make_market(volatility=volatility)
        ).price
        assert value >= 0.0
        assert value >= previous - 1.0e-12  # value never falls as volatility rises
        previous = value

    call_cap = 100.0  # S e^{-qT} with q = 0
    put_cap = 100.0 * math.exp(-0.05)
    for maturity in (0.05, 0.5, 1.0, 5.0):
        market = make_market(maturity=maturity, volatility=0.4)
        call = pricing.black_scholes(
            pricing.EuropeanOption(pricing.OptionType.CALL, 100.0), market
        ).price
        put = pricing.black_scholes(
            pricing.EuropeanOption(pricing.OptionType.PUT, 100.0), market
        ).price
        assert call <= call_cap + 1.0e-12
        assert put <= put_cap + 1.0e-12


def test_greeks_have_the_right_signs_ranges_and_pair_relations() -> None:
    for parameters in MARKETS:
        market = make_market(**parameters)
        strike = float(parameters["spot"])
        call = pricing.black_scholes_greeks(
            pricing.EuropeanOption(pricing.OptionType.CALL, strike), market
        )
        put = pricing.black_scholes_greeks(
            pricing.EuropeanOption(pricing.OptionType.PUT, strike), market
        )
        growth_discount = math.exp(-market.dividend_yield * market.maturity)
        assert call.gamma == pytest.approx(put.gamma, rel=1.0e-13)
        assert call.vega == pytest.approx(put.vega, rel=1.0e-13)
        assert call.delta - put.delta == pytest.approx(growth_discount, rel=1.0e-11)
        assert 0.0 <= call.delta <= growth_discount + 1.0e-12
        assert -growth_discount - 1.0e-12 <= put.delta <= 0.0
        assert call.gamma >= 0.0 and call.vega >= 0.0


def test_finite_differences_reproduce_the_analytic_greeks() -> None:
    market = make_market(spot=100.0, rate=0.05, dividend_yield=0.02, volatility=0.25, maturity=1.5)
    option = pricing.EuropeanOption(pricing.OptionType.CALL, 100.0)
    analytic = pricing.black_scholes_greeks(option, market)
    policy = pricing.BumpPolicy()
    policy.spot_relative = 0.001
    policy.volatility_absolute = 0.001
    policy.rate_absolute = 1.0e-6
    policy.time_absolute = 1.0e-5
    numeric = pricing.finite_difference_greeks(option, market, policy)
    for greek in ("delta", "gamma", "vega", "theta", "rho"):
        ours = getattr(analytic, greek)
        finite = getattr(numeric, greek)
        # O(h^2) truncation with the bumps above is <= 1e-6 relative; the
        # absolute floors cover the deep out-of-the-money cases where the
        # Greek itself is ~0 and a ratio would be meaningless.
        assert abs(ours - finite) <= max(1.0e-6 * abs(ours), 1.0e-7), (greek, ours, finite)


def test_bump_policy_is_validated_before_it_is_used() -> None:
    policy = pricing.BumpPolicy()
    policy.validate()
    policy.spot_relative = 0.0
    with pytest.raises(quantrisk.ValidationError, match="spot_relative"):
        policy.validate()
    with pytest.raises(quantrisk.ValidationError, match="spot_relative"):
        pricing.finite_difference_greeks(
            pricing.EuropeanOption(pricing.OptionType.CALL, 100.0),
            make_market(),
            policy,
        )


def test_crr_lattice_converges_towards_the_analytic_price() -> None:
    market = make_market(spot=100.0, rate=0.05, dividend_yield=0.02, volatility=0.25, maturity=1.0)
    option = pricing.EuropeanOption(pricing.OptionType.CALL, 100.0)
    analytic = pricing.black_scholes(option, market).price
    errors = []
    for steps in (25, 100, 400, 1600):
        lattice = pricing.crr_binomial(option, market, pricing.ExerciseStyle.EUROPEAN, steps)
        assert lattice.up * lattice.down == pytest.approx(1.0, rel=1.0e-14)
        assert 0.0 < lattice.risk_neutral_up_probability < 1.0
        errors.append(abs(lattice.price - analytic))
    assert errors[-1] < errors[0] / 10.0
    assert errors[-2] < errors[-3]
    # First order in dt: a 4x finer lattice cuts the error by about 4.
    assert errors[-1] < errors[-2] / 2.0


def test_american_exercise_rules() -> None:
    no_dividends = make_market(
        spot=100.0, rate=0.05, dividend_yield=0.0, volatility=0.25, maturity=1.0
    )
    option = pricing.EuropeanOption(pricing.OptionType.CALL, 100.0)
    european = pricing.crr_binomial(option, no_dividends, pricing.ExerciseStyle.EUROPEAN, 400).price
    american = pricing.crr_binomial(option, no_dividends, pricing.ExerciseStyle.AMERICAN, 400).price
    # No-early-exercise theorem: identical when the stock pays nothing.
    assert american == pytest.approx(european, rel=1.0e-12)

    with_dividends = make_market(dividend_yield=0.09, volatility=0.3, maturity=1.0)
    deep_itm = pricing.EuropeanOption(pricing.OptionType.CALL, 60.0)
    european_div = pricing.crr_binomial(
        deep_itm, with_dividends, pricing.ExerciseStyle.EUROPEAN, 400
    ).price
    american_div = pricing.crr_binomial(
        deep_itm, with_dividends, pricing.ExerciseStyle.AMERICAN, 400
    ).price
    assert american_div > european_div

    put = pricing.EuropeanOption(pricing.OptionType.PUT, 120.0)
    european_put = pricing.crr_binomial(
        put, no_dividends, pricing.ExerciseStyle.EUROPEAN, 400
    ).price
    american_put = pricing.crr_binomial(
        put, no_dividends, pricing.ExerciseStyle.AMERICAN, 400
    ).price
    assert american_put >= european_put - 1.0e-12
    assert american_put <= 120.0 + 1.0e-9
    assert american_put >= put.payoff(no_dividends.spot)


def test_lattice_matches_the_formula_on_the_degenerate_edges() -> None:
    flat = make_market(spot=110.0, rate=0.05, dividend_yield=0.02, volatility=0.0, maturity=1.0)
    option = pricing.EuropeanOption(pricing.OptionType.CALL, 100.0)
    lattice = pricing.crr_binomial(option, flat, pricing.ExerciseStyle.EUROPEAN, 100)
    assert "sigma == 0" in lattice.note
    assert lattice.price == pytest.approx(pricing.black_scholes(option, flat).price, rel=1.0e-12)


def test_lattice_and_option_constructors_validate_their_inputs() -> None:
    market = make_market()
    option = pricing.EuropeanOption(pricing.OptionType.CALL, 100.0)
    with pytest.raises(quantrisk.ValidationError, match="steps"):
        pricing.crr_binomial(option, market, pricing.ExerciseStyle.EUROPEAN, 0)
    with pytest.raises(quantrisk.ValidationError, match="steps"):
        pricing.crr_binomial(option, market, pricing.ExerciseStyle.EUROPEAN, -3)
    for bad in (0.0, -1.0, math.nan, math.inf):
        with pytest.raises(quantrisk.ValidationError, match="spot"):
            pricing.black_scholes(option, make_market(spot=bad))
    with pytest.raises(quantrisk.ValidationError, match="strike"):
        pricing.EuropeanOption(pricing.OptionType.CALL, 0.0).validate()
    with pytest.raises(quantrisk.ValidationError, match="volatility"):
        make_market(volatility=-0.1).validate()
    with pytest.raises(quantrisk.ValidationError, match="maturity"):
        make_market(maturity=-1.0).validate()


def test_multiple_constraint_violations_are_reported_together() -> None:
    bad = pricing.MarketParams(
        spot=-1.0, rate=float("nan"), dividend_yield=0.0, volatility=-0.2, maturity=-1.0
    )
    with pytest.raises(quantrisk.ValidationError) as raised:
        bad.validate()
    message = str(raised.value)
    for field in ("spot", "rate", "volatility", "maturity"):
        assert field in message, message


def test_payoff_and_option_metadata() -> None:
    call = pricing.EuropeanOption(pricing.OptionType.CALL, 100.0)
    put = pricing.EuropeanOption(pricing.OptionType.PUT, 100.0)
    assert call.payoff(120.0) == 20.0 and call.payoff(80.0) == 0.0
    assert put.payoff(80.0) == 20.0 and put.payoff(120.0) == 0.0


def test_pricing_results_do_not_leak_nan_into_valid_cases() -> None:
    values = np.linspace(0.01, 300.0, 60)
    for spot in values:
        result = pricing.black_scholes(
            pricing.EuropeanOption(pricing.OptionType.CALL, 100.0),
            make_market(spot=float(spot)),
        )
        assert math.isfinite(result.price)
        assert 0.0 <= result.price <= float(spot) + 1.0e-12
