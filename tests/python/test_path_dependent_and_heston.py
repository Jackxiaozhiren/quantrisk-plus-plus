"""Phase 4 Python checks: Asian, barrier and Heston components.

Oracle-free by design (QuantLib comparisons live in the benchmark): the exactness
tests here are algebraic identities, and the statistical ones use fixed seeds with
theory-derived bands.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import quantrisk

mc = quantrisk.monte_carlo
pricing = quantrisk.pricing
VR = mc.VarianceReduction

MARKET = pricing.MarketParams(
    spot=100.0, rate=0.05, dividend_yield=0.02, volatility=0.25, maturity=1.0
)


def heston_parameters(**overrides):  # noqa: ANN201
    parameters = quantrisk.stochastic.HestonParams()
    parameters.spot = 100.0
    parameters.rate = 0.05
    parameters.dividend_yield = 0.02
    parameters.initial_variance = 0.0625
    parameters.kappa = 2.0
    parameters.theta = 0.0625
    parameters.xi = 0.4
    parameters.rho = -0.7
    parameters.maturity = 1.0
    for name, value in overrides.items():
        setattr(parameters, name, value)
    return parameters


# --- Asian -----------------------------------------------------------------


def test_geometric_asian_closed_form_matches_its_own_simulation() -> None:
    option = pricing.AsianOption(pricing.OptionType.CALL, 100.0, pricing.AverageType.GEOMETRIC, 24)
    reference = pricing.geometric_asian_price(option, MARKET).price
    engine = mc.MonteCarloEngine(42)
    result = mc.price_geometric_asian(engine, option, MARKET, 100_000)
    assert abs(result.price - reference) < 4.0 * result.standard_error, (
        result.price,
        reference,
        result.standard_error,
    )


def test_single_monitoring_date_geometric_asian_equals_black_scholes() -> None:
    """M = 1 makes the geometric average the terminal price."""
    option = pricing.AsianOption(pricing.OptionType.CALL, 100.0, pricing.AverageType.GEOMETRIC, 1)
    geometric = pricing.geometric_asian_price(option, MARKET)
    vanilla = pricing.black_scholes(pricing.EuropeanOption(pricing.OptionType.CALL, 100.0), MARKET)
    assert geometric.price == pytest.approx(vanilla.price, rel=1.0e-12)
    assert geometric.d1 == pytest.approx(vanilla.d1, rel=1.0e-10)


def test_control_variate_reduces_asian_variance_and_keeps_the_estimate() -> None:
    option = pricing.AsianOption(pricing.OptionType.CALL, 100.0, pricing.AverageType.ARITHMETIC, 24)
    plain = mc.price_asian(mc.MonteCarloEngine(42), option, MARKET, 60_000, False)
    controlled = mc.price_asian(mc.MonteCarloEngine(42), option, MARKET, 60_000, True)
    assert controlled.standard_error < plain.standard_error / 2.0
    assert math.isfinite(controlled.control_beta)
    combined = math.hypot(plain.standard_error, controlled.standard_error)
    assert abs(controlled.price - plain.price) < 6.0 * combined
    assert "control variate" in controlled.note


def test_arithmetic_average_dominates_geometric_average_pathwise() -> None:
    """AM >= GM, so the arithmetic Asian call is never worth less."""
    for points in (2, 12, 52):
        arithmetic = pricing.AsianOption(
            pricing.OptionType.CALL, 100.0, pricing.AverageType.ARITHMETIC, points
        )
        geometric = pricing.AsianOption(
            pricing.OptionType.CALL, 100.0, pricing.AverageType.GEOMETRIC, points
        )
        simulated = mc.price_asian(mc.MonteCarloEngine(7), arithmetic, MARKET, 40_000, True)
        reference = pricing.geometric_asian_price(geometric, MARKET).price
        assert simulated.price + 4.0 * simulated.standard_error >= reference, (
            points,
            simulated.price,
            reference,
        )


def test_averaging_payoffs_evaluate_as_documented() -> None:
    samples = [90.0, 110.0, 95.0, 120.0]
    # The domain requires a strictly positive strike (mathematical
    # specification §0), so a negligible strike exposes the average itself.
    negligible = 1.0e-9
    arithmetic = pricing.AsianOption(
        pricing.OptionType.CALL, negligible, pricing.AverageType.ARITHMETIC, 4
    )
    geometric = pricing.AsianOption(
        pricing.OptionType.CALL, negligible, pricing.AverageType.GEOMETRIC, 4
    )
    assert arithmetic.payoff(samples) == pytest.approx(
        np.mean(samples) - negligible, rel=0, abs=1e-12
    )
    assert geometric.payoff(samples) == pytest.approx(
        float(np.exp(np.mean(np.log(samples)))) - negligible, rel=0, abs=1e-12
    )
    assert arithmetic.payoff_from_average(105.0) == pytest.approx(105.0, abs=1.0e-8)
    assert arithmetic.payoff_from_average(0.0) == 0.0


# --- barrier ---------------------------------------------------------------


def test_barrier_degenerate_limits() -> None:
    vanilla = pricing.black_scholes(
        pricing.EuropeanOption(pricing.OptionType.CALL, 100.0), MARKET
    ).price
    unreachable = pricing.BarrierOption(
        pricing.OptionType.CALL, 100.0, pricing.BarrierType.UP_AND_OUT, 1.0e12, 0.0
    )
    result = mc.price_barrier(
        mc.MonteCarloEngine(42), unreachable, MARKET, 100_000, 24, False, False
    )
    assert result.price == pytest.approx(vanilla, rel=4.0 * result.standard_error / vanilla)

    breached = pricing.BarrierOption(
        pricing.OptionType.CALL, 100.0, pricing.BarrierType.UP_AND_OUT, 90.0, 3.0
    )
    rebate_only = mc.price_barrier(
        mc.MonteCarloEngine(42), breached, MARKET, 20_000, 5, False, False
    )
    assert rebate_only.price == pytest.approx(3.0 * math.exp(-MARKET.rate), rel=1.0e-12)


def test_more_monitoring_dates_cannot_make_a_knock_out_cheaper_than_fewer() -> None:
    option = pricing.BarrierOption(
        pricing.OptionType.CALL, 100.0, pricing.BarrierType.UP_AND_OUT, 125.0, 0.0
    )
    market = pricing.MarketParams(
        spot=100.0, rate=0.05, dividend_yield=0.0, volatility=0.3, maturity=1.0
    )
    prices = []
    for steps in (5, 20, 80, 320):
        result = mc.price_barrier(
            mc.MonteCarloEngine(11), option, market, 120_000, steps, False, False
        )
        prices.append((result.price, result.standard_error))
    for (coarse, coarse_se), (fine, fine_se) in zip(prices[:-1], prices[1:], strict=True):
        assert fine <= coarse + 3.0 * math.hypot(coarse_se, fine_se), (coarse, fine)


def test_continuity_correction_moves_the_barrier_the_right_way() -> None:
    beta = pricing.barrier_continuity_constant()
    assert beta == pytest.approx(0.5826, abs=1.0e-3)
    up = pricing.BarrierOption(
        pricing.OptionType.CALL, 100.0, pricing.BarrierType.UP_AND_OUT, 130.0, 0.0
    )
    down = pricing.BarrierOption(
        pricing.OptionType.CALL, 100.0, pricing.BarrierType.DOWN_AND_OUT, 70.0, 0.0
    )
    dt = 1.0 / 50.0
    # The corrected barrier sits closer to the spot than the contractual one.
    assert pricing.continuity_corrected_barrier(up, MARKET, dt) < 130.0
    assert pricing.continuity_corrected_barrier(down, MARKET, dt) > 70.0

    discrete = mc.price_barrier(mc.MonteCarloEngine(5), up, MARKET, 60_000, 50, False, False)
    corrected = mc.price_barrier(mc.MonteCarloEngine(5), up, MARKET, 60_000, 50, True, False)
    assert corrected.price < discrete.price
    assert "approximation" in corrected.note


def test_barrier_survives_predicate_and_antithetic_unit_count() -> None:
    up = pricing.BarrierOption(
        pricing.OptionType.CALL, 100.0, pricing.BarrierType.UP_AND_OUT, 120.0, 0.0
    )
    assert up.survives(119.999)
    assert not up.survives(120.5)
    result = mc.price_barrier(mc.MonteCarloEngine(99), up, MARKET, 100_000, 50, False, True)
    assert result.iid_units == 50_000
    assert result.variance_reduction == VR.ANTITHETIC


# --- Heston ----------------------------------------------------------------


def test_heston_degenerates_to_black_scholes() -> None:
    sigma = 0.25
    parameters = heston_parameters(
        initial_variance=sigma * sigma, kappa=1.0, theta=sigma * sigma, xi=0.0, rho=0.0
    )
    reference = pricing.black_scholes(
        pricing.EuropeanOption(pricing.OptionType.CALL, 100.0), MARKET
    ).price
    result = quantrisk.stochastic.price_heston_european(
        parameters,
        pricing.EuropeanOption(pricing.OptionType.CALL, 100.0),
        200_000,
        50,
        quantrisk.Rng(42),
    )
    assert abs(result.price - reference) < 4.0 * result.standard_error, (
        result.price,
        reference,
        result.standard_error,
    )


def test_heston_paths_are_positive_and_reproducible() -> None:
    parameters = heston_parameters(initial_variance=0.01, theta=0.04, xi=0.9)
    assert not parameters.feller_condition_satisfied()
    simulation = quantrisk.stochastic.simulate_heston(parameters, 20_000, 100, quantrisk.Rng(7))
    assert len(simulation.terminals) == 20_000
    assert all(level > 0 for level in simulation.terminals)
    assert all(variance >= 0 for variance in simulation.terminal_variance)
    assert all(variance >= 0 for variance in simulation.realised_variance)
    assert simulation.negative_variances_clamped > 0

    again = quantrisk.stochastic.simulate_heston(parameters, 20_000, 100, quantrisk.Rng(7))
    assert list(simulation.terminals) == list(again.terminals)
    assert "full-truncation" in simulation.note


def test_heston_preserves_the_risk_neutral_forward() -> None:
    parameters = heston_parameters()
    simulation = quantrisk.stochastic.simulate_heston(parameters, 200_000, 64, quantrisk.Rng(21))
    array = np.asarray(simulation.terminals)
    expected = parameters.spot * math.exp(
        (parameters.rate - parameters.dividend_yield) * parameters.maturity
    )
    se = float(array.std(ddof=1) / math.sqrt(array.size))
    assert abs(float(array.mean()) - expected) < 4.0 * se, (float(array.mean()), expected, se)


def test_negative_correlation_raises_out_of_the_money_put_value() -> None:
    put = pricing.EuropeanOption(pricing.OptionType.PUT, 90.0)
    low_rho = quantrisk.stochastic.price_heston_european(
        heston_parameters(xi=0.5, rho=-0.9), put, 200_000, 64, quantrisk.Rng(5)
    )
    high_rho = quantrisk.stochastic.price_heston_european(
        heston_parameters(xi=0.5, rho=0.9), put, 200_000, 64, quantrisk.Rng(5)
    )
    assert low_rho.price > high_rho.price, (low_rho.price, high_rho.price)


def test_heston_step_refinement_difference_is_within_noise() -> None:
    parameters = heston_parameters(initial_variance=0.09, kappa=1.5, theta=0.09, xi=0.6, rho=-0.5)
    put = pricing.EuropeanOption(pricing.OptionType.CALL, 100.0)
    samples = []
    for steps in (20, 80, 320):
        result = quantrisk.stochastic.price_heston_european(
            parameters, put, 150_000, steps, quantrisk.Rng(3)
        )
        samples.append((steps, result.price, result.standard_error))
    finest = samples[-1]
    for steps, price, se in samples:
        combined = math.hypot(se, finest[2])
        assert abs(price - finest[1]) < 4.0 * combined, (steps, price, finest)


def test_heston_parameters_are_validated_structurally() -> None:
    parameters = heston_parameters()
    parameters.rho = 1.5
    with pytest.raises(quantrisk.ValidationError, match="rho"):
        parameters.validate()
    parameters = heston_parameters()
    parameters.theta = -0.1
    with pytest.raises(quantrisk.ValidationError, match="theta"):
        parameters.validate()

    # Feller violation is legal input, reported rather than rejected.
    legal = heston_parameters(initial_variance=0.01, kappa=1.0, theta=0.01, xi=1.0)
    assert not legal.feller_condition_satisfied()
    result = quantrisk.stochastic.price_heston_european(
        legal,
        pricing.EuropeanOption(pricing.OptionType.CALL, 100.0),
        5_000,
        10,
        quantrisk.Rng(1),
    )
    assert math.isfinite(result.price)
    assert result.feller_condition_satisfied is False


def test_zero_maturity_heston_returns_the_spot() -> None:
    parameters = heston_parameters(maturity=0.0)
    simulation = quantrisk.stochastic.simulate_heston(parameters, 500, 10, quantrisk.Rng(3))
    assert set(simulation.terminals) == {100.0}
    assert "T == 0" in simulation.note


# --- validation ------------------------------------------------------------


def test_path_dependent_instruments_validate_inputs() -> None:
    with pytest.raises(quantrisk.ValidationError, match="strike"):
        pricing.AsianOption(
            pricing.OptionType.CALL, -1.0, pricing.AverageType.ARITHMETIC, 12
        ).validate()
    with pytest.raises(quantrisk.ValidationError, match="monitoring_points"):
        pricing.AsianOption(
            pricing.OptionType.CALL, 100.0, pricing.AverageType.ARITHMETIC, 0
        ).validate()
    with pytest.raises(quantrisk.ValidationError, match="barrier_level"):
        pricing.BarrierOption(
            pricing.OptionType.CALL, 100.0, pricing.BarrierType.UP_AND_OUT, 0.0, 0.0
        ).validate()
    good = pricing.AsianOption(pricing.OptionType.CALL, 100.0, pricing.AverageType.ARITHMETIC, 12)
    with pytest.raises(quantrisk.ValidationError, match="paths"):
        mc.price_asian(mc.MonteCarloEngine(1), good, MARKET, 0, False)
    with pytest.raises(quantrisk.ValidationError, match="steps"):
        mc.price_barrier(
            mc.MonteCarloEngine(1),
            pricing.BarrierOption(
                pricing.OptionType.CALL, 100.0, pricing.BarrierType.UP_AND_OUT, 120.0, 0.0
            ),
            MARKET,
            100,
            0,
        )
    with pytest.raises(quantrisk.ValidationError, match="spot"):
        pricing.geometric_asian_price(good, pricing.MarketParams(0.0, 0.05, 0.0, 0.2, 1.0))
