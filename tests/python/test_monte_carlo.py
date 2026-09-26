"""Phase 3 Python-side checks of the Monte Carlo engine.

Everything here is about the *estimator and the binding*, not about hoping a
random number comes out right: the exactness tests are deterministic
identities, and the statistical tests use fixed seeds with significance levels
chosen from theory.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import quantrisk

scipy_stats = pytest.importorskip("scipy.stats")

mc = quantrisk.monte_carlo
pricing = quantrisk.pricing
VR = mc.VarianceReduction

MARKET = pricing.MarketParams(
    spot=100.0, rate=0.05, dividend_yield=0.02, volatility=0.25, maturity=1.0
)


def analytic(option_type: pricing.OptionType, strike: float) -> float:
    return pricing.black_scholes(pricing.EuropeanOption(option_type, strike), MARKET).price


def test_engine_reports_the_documented_defaults() -> None:
    engine = mc.MonteCarloEngine()
    assert engine.seed == 42
    result = engine.price_european(
        pricing.EuropeanOption(pricing.OptionType.CALL, 100.0), MARKET, 10_000
    )
    assert result.seed == 42
    assert result.paths == 10_000
    assert result.iid_units == 10_000
    assert result.confidence_level == pytest.approx(0.95)
    assert result.measure == "risk_neutral"
    assert result.runtime_seconds > 0.0
    assert "MonteCarloResult" in repr(result)


def test_same_seed_reproduces_every_field_bit_for_bit() -> None:
    option = pricing.EuropeanOption(pricing.OptionType.PUT, 95.0)
    first = mc.MonteCarloEngine(2026).price_european(option, MARKET, 40_000)
    second = mc.MonteCarloEngine(2026).price_european(option, MARKET, 40_000)
    assert first.price == second.price
    assert first.standard_error == second.standard_error
    assert first.sample_variance == second.sample_variance
    assert first.confidence_low == second.confidence_low
    third = mc.MonteCarloEngine(2027).price_european(option, MARKET, 40_000)
    assert third.price != first.price


@pytest.mark.parametrize("option_type", [pricing.OptionType.CALL, pricing.OptionType.PUT])
@pytest.mark.parametrize("seed", [42, 1337, 2024, 90210])
def test_estimate_sits_within_four_standard_errors_of_the_analytic_price(
    option_type: pricing.OptionType, seed: int
) -> None:
    strike = 100.0
    reference = analytic(option_type, strike)
    result = mc.MonteCarloEngine(seed).price_european(
        pricing.EuropeanOption(option_type, strike), MARKET, 200_000
    )
    assert abs(result.price - reference) <= 4.0 * result.standard_error, (
        seed,
        result.price,
        result.standard_error,
        reference,
    )


def test_confidence_interval_is_centred_and_scaled_as_documented() -> None:
    result = mc.MonteCarloEngine(5).price_call(MARKET, 100.0, 60_000, VR.NONE, 0.90)
    z = mc.normal_confidence_multiplier(0.90)
    assert z == pytest.approx(1.6448536269514722, rel=1.0e-10)
    centre = 0.5 * (result.confidence_low + result.confidence_high)
    half = 0.5 * (result.confidence_high - result.confidence_low)
    assert centre == pytest.approx(result.price, rel=1.0e-14)
    assert half == pytest.approx(z * result.standard_error, rel=1.0e-10)


def test_emprical_coverage_of_the_95_percent_interval_is_in_range() -> None:
    """100 independent seeds, one interval each; count how often the analytic
    price falls inside. Under a correct estimator the count is Binomial(100,
    0.95), so the acceptance band is that distribution's 0.1 % - 99.9 % range
    rather than a hand-picked window."""
    option = pricing.EuropeanOption(pricing.OptionType.CALL, 100.0)
    reference = analytic(pricing.OptionType.CALL, 100.0)
    covered = 0
    trials = 100
    for seed in range(trials):
        result = mc.MonteCarloEngine(1000 + seed).price_european(option, MARKET, 4000)
        if result.confidence_low <= reference <= result.confidence_high:
            covered += 1
    low = int(scipy_stats.binom.ppf(0.001, trials, 0.95))
    high = int(scipy_stats.binom.ppf(0.999, trials, 0.95))
    assert low <= covered <= high, f"{covered} of {trials} covered, band [{low}, {high}]"


def test_control_variate_is_exact_for_a_deep_in_the_money_call() -> None:
    """A call struck at 1.0 on a 100-spot asset never finishes out of the money,
    so its payoff is the affine function S_T - K of the control variable. The
    control-variate estimator then reproduces the analytic value to rounding and
    its standard error collapses; if the control were wired up wrongly this
    would fail loudly instead of hiding inside a tolerance."""
    strike = 1.0
    option = pricing.EuropeanOption(pricing.OptionType.CALL, strike)
    reference = analytic(pricing.OptionType.CALL, strike)
    result = mc.MonteCarloEngine(42).price_european(option, MARKET, 20_000, VR.CONTROL_VARIATE)
    assert result.price == pytest.approx(reference, rel=1.0e-12, abs=1.0e-12)
    assert result.standard_error < 1.0e-10
    assert result.control_beta == pytest.approx(1.0, rel=1.0e-10)
    assert result.confidence_high - result.confidence_low < 1.0e-9


def test_variance_reduction_lowers_the_standard_error() -> None:
    option = pricing.EuropeanOption(pricing.OptionType.CALL, 100.0)
    plain = mc.MonteCarloEngine(77).price_european(option, MARKET, 100_000, VR.NONE)
    antithetic = mc.MonteCarloEngine(77).price_european(option, MARKET, 100_000, VR.ANTITHETIC)
    control = mc.MonteCarloEngine(77).price_european(option, MARKET, 100_000, VR.CONTROL_VARIATE)
    assert antithetic.iid_units == 50_000
    assert antithetic.standard_error < plain.standard_error
    assert control.standard_error < plain.standard_error / 2.0
    # Same path budget, so the estimates must still agree within noise.
    for reduced in (antithetic, control):
        combined = math.hypot(reduced.standard_error, plain.standard_error)
        assert abs(reduced.price - plain.price) <= 6.0 * combined


def test_antithetic_requires_an_even_path_count() -> None:
    with pytest.raises(quantrisk.ValidationError, match="even"):
        mc.MonteCarloEngine(1).price_call(MARKET, 100.0, 10_001, VR.ANTITHETIC)


def test_engine_validates_paths_confidence_and_inputs() -> None:
    engine = mc.MonteCarloEngine(1)
    option = pricing.EuropeanOption(pricing.OptionType.CALL, 100.0)
    for bad_paths in (0, -5):
        with pytest.raises(quantrisk.ValidationError, match="paths"):
            engine.price_european(option, MARKET, bad_paths)
    with pytest.raises(quantrisk.ValidationError, match="confidence_level"):
        engine.price_european(option, MARKET, 1000, VR.NONE, 1.0)
    with pytest.raises(quantrisk.ValidationError, match="spot"):
        engine.price_european(option, pricing.MarketParams(0.0, 0.05, 0.0, 0.2, 1.0), 1000)


def test_gbm_draws_are_exposable_and_reproducible_through_bindings() -> None:
    rng = quantrisk.Rng(9)
    first = quantrisk.stochastic.terminal_prices(MARKET, 1000, rng)
    rng2 = quantrisk.Rng(9)
    second = quantrisk.stochastic.terminal_prices(MARKET, 1000, rng2)
    assert list(first) == list(second)
    assert all(level > 0 for level in first)

    array = np.asarray(first)
    expected = 100.0 * math.exp((MARKET.rate - MARKET.dividend_yield) * MARKET.maturity)
    se = float(array.std(ddof=1) / math.sqrt(array.size))
    assert abs(float(array.mean()) - expected) < 5.0 * se

    log_returns = np.log(array / MARKET.forward_at(0.0))
    assert float(log_returns.mean()) == pytest.approx(
        quantrisk.stochastic.expected_log_return(MARKET),
        abs=5.0 * float(log_returns.std(ddof=1)) / math.sqrt(array.size),
    )


def test_paths_matrix_shape_and_antithetic_pairing() -> None:
    rng = quantrisk.Rng(3)
    flat = quantrisk.stochastic.paths_matrix(MARKET, 12, 5, rng)
    assert len(flat) == 12 * 6
    rows = np.asarray(flat).reshape(12, 6)
    assert np.allclose(rows[:, 0], MARKET.spot, rtol=0.0, atol=0.0)

    rng = quantrisk.Rng(3)
    anti = np.asarray(quantrisk.stochastic.antithetic_terminal_prices(MARKET, 200, rng))
    half = 100
    exponent = (
        2.0 * (MARKET.rate - MARKET.dividend_yield - 0.5 * MARKET.volatility**2) * MARKET.maturity
    )
    expected_product = MARKET.spot**2 * math.exp(exponent)
    assert np.allclose(anti[:half] * anti[half:], expected_product, rtol=1.0e-12)


def test_variance_reduction_names_are_exposed() -> None:
    assert mc.variance_reduction_name(VR.NONE) == "plain"
    assert mc.variance_reduction_name(VR.ANTITHETIC) == "antithetic"
    assert mc.variance_reduction_name(VR.CONTROL_VARIATE) == "control_variate"
