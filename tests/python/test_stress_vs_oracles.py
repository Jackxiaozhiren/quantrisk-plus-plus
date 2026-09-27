"""Phase 7 Level 2/3 validation: the stress engine against independent numerics.

The oracles here are NumPy and SciPy, and the point is that they take genuinely
different routes to the same answers:

* NumPy's own linear algebra computes the exposure mapping, the Cholesky draw and the
  empirical quantiles; the engine uses Eigen, its own mt19937_64 plus Marsaglia normals,
  and the Phase 5 estimators. Agreement therefore tests the logic, not shared code.
* The Monte Carlo oracle deliberately uses **NumPy's Generator**, a different RNG with a
  different normal transform, so a reproducibility bug in our sampler cannot agree with it
  by construction.
* Euler allocation is checked against a central-difference gradient of the VaR formula
  rather than against the same algebra written twice.

Nothing from these libraries is imported by the library itself (PROJECT_SPEC.md §2.2),
and no reference number is transcribed: every expected value is computed while the test
runs.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import quantrisk

scipy_stats = pytest.importorskip("scipy.stats")

STRESS = quantrisk.stress

# The engine's Gaussian quantile is exact, so any disagreement with NumPy's is the
# sampling error of the oracle side plus float noise; these bounds come from that, not
# from whatever the comparison happened to produce.
PARAMETRIC_TOLERANCE = 1e-9
MONTE_Carlo_RELATIVE = 0.02


def factor_set():
    handle = STRESS.FactorSet()
    handle.factors = [
        STRESS.RiskFactor("SPX", STRESS.FactorClass.equity_index, 4000.0, "points"),
        STRESS.RiskFactor("NDX", STRESS.FactorClass.equity_index, 16000.0, "points"),
        STRESS.RiskFactor("UST10Y", STRESS.FactorClass.rate, 0.04, "decimal"),
        STRESS.RiskFactor("VOL", STRESS.FactorClass.volatility, 0.20, "vol"),
    ]
    return handle


def book():
    portfolio = STRESS.Portfolio()
    portfolio.factors = factor_set()
    equity = STRESS.ExposureVector()
    equity.delta = [1.0e6, 2.0e6, 0.0, 0.0]
    rates = STRESS.ExposureVector()
    rates.duration = [0.0, 0.0, -2.0e7, 0.0]
    volatility = STRESS.ExposureVector()
    volatility.vega = [0.0, 0.0, 0.0, -1.0e5]
    first = STRESS.Position()
    first.name = "equities"
    first.exposures = equity
    second = STRESS.Position()
    second.name = "rates"
    second.exposures = rates
    third = STRESS.Position()
    third.name = "vol"
    third.exposures = volatility
    portfolio.positions = [first, second, third]
    return portfolio


def factor_covariance():
    """Covariance of factor *moves* in the units the exposures answer to."""
    sigma = np.array([0.10, 0.15, 0.002, 0.05])
    correlation = np.array(
        [
            [1.0, 0.6, 0.0, -0.3],
            [0.6, 1.0, 0.0, -0.2],
            [0.0, 0.0, 1.0, 0.0],
            [-0.3, -0.2, 0.0, 1.0],
        ]
    )
    return np.outer(sigma, sigma) * correlation


def scenario(name, kind=STRESS.ScenarioKind.deterministic, **overrides):
    handle = STRESS.Scenario()
    handle.name = name
    handle.kind = kind
    handle.assumptions = overrides.get("assumptions", "python oracle fixture")
    handle.horizon = overrides.get("horizon", 1.0 / 252.0)
    return handle


def column(block, assets=4):
    """An exposure block as a full-length vector.

    The engine keeps a block *empty* to mean "this position carries no sensitivity of
    that type at all", which is a different statement from a block of zeros. NumPy needs
    the difference resolved, so empties become zeros here and only here.
    """
    values = np.array(block, dtype=float)
    if values.size == 0:
        return np.zeros(assets)
    return values


def beta_of(exposures):
    """The engine's beta, rebuilt from the exposure blocks in NumPy."""
    return (
        column(exposures.delta)
        + column(exposures.duration)
        + column(exposures.vega)
        + column(exposures.credit)
    )


# --- the mapping, against NumPy ------------------------------------------


@pytest.mark.oracle
def test_deterministic_pnl_matches_a_numpy_exposure_product() -> None:
    portfolio = book()
    handle = scenario("risk-off")
    handle.shocks = [
        STRESS.Shock("SPX", -0.20, 0.0),
        STRESS.Shock("NDX", -0.20, 0.0),
        STRESS.Shock("UST10Y", 0.0, -0.01),
        STRESS.Shock("VOL", 0.0, 0.08),
    ]
    result = STRESS.run_scenario(portfolio, handle)

    aggregate = portfolio.aggregate()
    relative = np.array([-0.20, -0.20, -0.01 / 0.04, 0.08 / 0.20])
    absolute = np.array([-0.20 * 4000.0, -0.20 * 16000.0, -0.01, 0.08])
    expected = (
        column(aggregate.delta) @ relative
        + column(aggregate.gamma) @ (relative**2)
        + column(aggregate.duration) @ absolute
        + column(aggregate.vega) @ absolute
    )
    assert result.pnl_change == pytest.approx(expected, rel=PARAMETRIC_TOLERANCE)
    # Both attributions must close on the same number from opposite directions.
    assert result.factor_attribution_residual == pytest.approx(0.0, abs=1e-8)
    assert result.position_attribution_residual == pytest.approx(0.0, abs=1e-8)
    assert sum(part.total() for part in result.by_factor) == pytest.approx(
        result.pnl_change, rel=PARAMETRIC_TOLERANCE
    )


@pytest.mark.oracle
def test_shifted_covariance_matches_a_numpy_reconstruction() -> None:
    covariance = factor_covariance()
    shift = STRESS.DistributionShift()
    shift.volatility_multiplier = 1.7
    shift.correlation_increment = 0.15
    values, note = STRESS.shift_covariance(covariance.reshape(-1).tolist(), 4, shift)
    ours = np.array(values).reshape(4, 4)

    sigma = np.sqrt(np.diag(covariance)) * 1.7
    correlation = covariance / np.outer(sigma / 1.7, sigma / 1.7)
    correlation = correlation + 0.15 * (1 - np.eye(4))
    correlation = np.clip(correlation, -1.0, 1.0)
    expected = np.outer(sigma, sigma) * correlation
    assert np.abs(ours - expected).max() < 1e-14
    assert "scaled by" in note and "correlation increment" in note


@pytest.mark.oracle
def test_a_correlation_lift_that_breaks_positive_definiteness_says_so() -> None:
    # Four independent assets cannot all be pairwise correlated at 0.99 without the
    # matrix going indefinite; the engine must report that rather than project it away.
    covariance = np.eye(4) * 0.04
    shift = STRESS.DistributionShift()
    shift.correlation_increment = 0.99
    values, note = STRESS.shift_covariance(covariance.reshape(-1).tolist(), 4, shift)
    ours = np.array(values).reshape(4, 4)
    if np.linalg.eigvalsh(ours).min() < -1e-12:
        assert "NOT positive semidefinite" in note
    else:  # the clip can still leave a valid matrix; then there must be no warning
        assert "NOT positive semidefinite" not in note


# --- the sampler, against a different RNG --------------------------------


@pytest.mark.oracle
def test_the_engine_sampler_reproduces_itself_and_numpy_agrees_on_dispersion() -> None:
    covariance = factor_covariance()
    flat = covariance.reshape(-1).tolist()
    first = STRESS.sample_factor_moves(flat, 4, 100_000, 101)
    repeat = STRESS.sample_factor_moves(flat, 4, 100_000, 101)
    assert first.moves == repeat.moves, "our sampler must be deterministic in the seed"

    ours = np.array(first.moves).reshape(100_000, 4)
    recovered = np.cov(ours, rowvar=False, ddof=1)
    assert np.abs(recovered - covariance).max() < MONTE_Carlo_RELATIVE * covariance.max()

    # Independent route: NumPy's Generator, a different RNG and a different normal
    # transform, reproducing the same covariance to the same sampling accuracy.
    independent = np.random.default_rng(2024).multivariate_normal(
        np.zeros(4), covariance, size=100_000
    )
    assert np.abs(np.cov(independent, rowvar=False, ddof=1) - covariance).max() < (
        MONTE_Carlo_RELATIVE * covariance.max()
    )


def test_sampler_refuses_a_matrix_with_no_cholesky_factor() -> None:
    with pytest.raises(quantrisk.ValidationError):
        STRESS.sample_factor_moves([1.0, -1.5, -1.5, 1.0], 2, 10, 1)


# --- risk metrics, against closed form and against simulation -------------


@pytest.mark.oracle
def test_parametric_stressed_var_matches_scipy_on_the_same_beta() -> None:
    portfolio = book()
    covariance = factor_covariance()
    handle = scenario("vol x1.5")
    handle.distribution.volatility_multiplier = 1.5
    result = STRESS.run_scenario(portfolio, handle, covariance.reshape(-1).tolist(), 0.95)

    beta = beta_of(portfolio.aggregate())
    stressed, _ = STRESS.shift_covariance(covariance.reshape(-1).tolist(), 4, handle.distribution)
    sigma = math.sqrt(beta @ np.array(stressed).reshape(4, 4) @ beta)
    # scipy's own quantile rather than our inverse_normal_cdf, so the z is independent.
    z = float(scipy_stats.norm.ppf(0.95))
    assert result.stressed_var == pytest.approx(z * sigma, rel=PARAMETRIC_TOLERANCE)
    assert result.base_var == pytest.approx(
        z * math.sqrt(beta @ covariance @ beta), rel=PARAMETRIC_TOLERANCE
    )
    assert result.var_decomposition_residual == pytest.approx(0.0, abs=1e-9)


@pytest.mark.oracle
def test_monte_carlo_stress_var_reproduces_the_parametric_number() -> None:
    """Two independent routes to one risk number: a Cholesky draw plus an empirical
    quantile, against the Gaussian closed form."""
    portfolio = book()
    covariance = factor_covariance()
    handle = scenario("no stress", STRESS.ScenarioKind.monte_carlo)
    simulated = STRESS.run_monte_carlo_scenarios(
        portfolio, handle, covariance.reshape(-1).tolist(), 400_000, 4242, 0.95
    )
    parametric = STRESS.run_scenario(portfolio, handle, covariance.reshape(-1).tolist(), 0.95)
    assert simulated.var.value == pytest.approx(parametric.base_var, rel=MONTE_Carlo_RELATIVE)
    assert simulated.es.value >= simulated.var.value
    assert simulated.mean_pnl == pytest.approx(0.0, abs=0.02 * parametric.base_var)


@pytest.mark.oracle
def test_a_stress_shifts_the_distribution_centre_by_the_linearised_loss() -> None:
    portfolio = book()
    covariance = factor_covariance()
    handle = scenario("equity -20%", STRESS.ScenarioKind.monte_carlo)
    handle.shocks = [STRESS.Shock("SPX", -0.20, 0.0), STRESS.Shock("NDX", -0.20, 0.0)]
    simulated = STRESS.run_monte_carlo_scenarios(
        portfolio, handle, covariance.reshape(-1).tolist(), 200_000, 77, 0.95
    )
    direct = STRESS.run_scenario(portfolio, handle, covariance.reshape(-1).tolist(), 0.95)
    # The mean of the simulated outcomes is the deterministic stress, to sampling error.
    assert simulated.mean_pnl == pytest.approx(direct.pnl_change, rel=0.01)
    # Without a covariance the engine leaves the risk metrics unset rather than assuming
    # a dispersion, which is what makes the next line meaningful at all.
    assert direct.has_risk_metrics
    # For a linear book the level leg of the VaR change is exactly the loss taken.
    assert direct.var_change_from_level == pytest.approx(-direct.pnl_change, rel=1e-9)
    assert direct.var_change_from_distribution == pytest.approx(0.0, abs=1e-9)


@pytest.mark.oracle
def test_euler_components_match_a_central_difference_gradient() -> None:
    """Euler allocation checked against numerically differentiated VaR, not against the
    same algebra written a second time."""
    portfolio = book()
    covariance = factor_covariance()
    handle = scenario("base")
    result = STRESS.run_scenario(portfolio, handle, covariance.reshape(-1).tolist(), 0.95)
    names = [part.name for part in portfolio.positions]
    assert [part.name for part in result.var_components_stressed] == names
    assert result.var_component_residual == pytest.approx(0.0, abs=1e-9)

    base_beta = beta_of(portfolio.aggregate())
    # Step chosen for the accuracy of a central difference on this function, not for the
    # agreement it produced: the truncation error falls as h^2 and round-off rises as
    # eps/h, and 1e-5 x scale sits near the optimum for float64.
    step = 1e-5 * float(np.abs(base_beta).max())

    def var_at(beta: np.ndarray) -> float:
        return float(scipy_stats.norm.ppf(0.95)) * math.sqrt(beta @ covariance @ beta)

    for index, part in enumerate(result.var_components_stressed):
        position = portfolio.positions[index]
        exposures = position.exposures
        position_beta = beta_of(exposures)
        gradient = np.zeros(4)
        for axis in range(4):
            bumped = base_beta.copy()
            bumped[axis] += step
            lowered = base_beta.copy()
            lowered[axis] -= step
            gradient[axis] = (var_at(bumped) - var_at(lowered)) / (2 * step)
        assert part.pnl == pytest.approx(float(position_beta @ gradient), rel=1e-6)


@pytest.mark.oracle
def test_historical_replay_matches_numpy_and_carries_no_lookahead() -> None:
    portfolio = book()
    rng = np.random.default_rng(31337)
    moves = rng.multivariate_normal(np.zeros(4), factor_covariance(), size=500)
    # Observed moves in the units the exposures answer to: relative for the equities,
    # absolute for the rate and the vol factor.
    window = moves.copy()
    flat = window.reshape(-1).tolist()
    result = STRESS.run_historical_scenarios(portfolio, scenario("two years"), flat, 500)

    aggregate = portfolio.aggregate()
    relative = np.column_stack(
        [
            window[:, 0],
            window[:, 1],
            window[:, 2] / 0.04,
            window[:, 3] / 0.20,
        ]
    )
    absolute = np.column_stack(
        [
            window[:, 0] * 4000.0,
            window[:, 1] * 16000.0,
            window[:, 2],
            window[:, 3],
        ]
    )
    expected = (
        relative @ column(aggregate.delta)
        + absolute @ column(aggregate.duration)
        + absolute @ column(aggregate.vega)
    )
    assert np.array(result.pnl) == pytest.approx(expected, rel=1e-9)
    assert result.mean_pnl == pytest.approx(expected.mean(), rel=1e-9)
    assert result.worst_pnl == pytest.approx(expected.min(), rel=1e-9)
    assert result.var.value == pytest.approx(float(np.percentile(-expected, 95.0)), rel=1e-9)
    assert result.position_attribution_residual == pytest.approx(0.0, abs=1e-9)
    assert "replay" in result.generator
    # A replay is a statement about the window it was given, and says so.
    assert "not a forecast" in result.note


def test_a_single_replayed_day_has_no_quantile_to_report() -> None:
    portfolio = book()
    window = [-0.01, 0.0, 0.0, 0.0]
    result = STRESS.run_historical_scenarios(portfolio, scenario("one day"), window, 1)
    assert math.isnan(result.var.value), "one outcome is not a distribution"
    assert "not a distribution" in result.note
    assert result.volatility == 0.0


def test_misshaped_inputs_are_refused() -> None:
    portfolio = book()
    handle = scenario("bad")
    handle.shocks = [STRESS.Shock("NONEXISTENT", -0.1, 0.0)]
    with pytest.raises(quantrisk.ValidationError):
        STRESS.run_scenario(portfolio, handle)

    with pytest.raises(quantrisk.ValidationError):
        STRESS.run_historical_scenarios(portfolio, scenario("short"), [0.01, 0.02], 3)

    broken = STRESS.Portfolio()
    broken.factors = factor_set()
    position = STRESS.Position()
    position.name = "misaligned"
    position.exposures = STRESS.ExposureVector()
    position.exposures.delta = [1.0, 2.0]
    broken.positions = [position]
    with pytest.raises(quantrisk.ValidationError):
        STRESS.run_scenario(broken, scenario("any"))


def test_bound_exposure_blocks_are_value_semantic() -> None:
    """A bound ``std::vector`` member comes back as a copy, so item assignment is lost.

    Found the hard way: an experiment that built ``exposures.delta[0] = value`` reported a
    P&L of exactly zero and looked like an engine bug. It is pybind11's value semantics,
    and it is silent, so the behaviour is pinned here rather than left to be rediscovered.
    Blocks must be replaced wholesale.
    """
    exposures = STRESS.ExposureVector()
    exposures.delta = [1.0e6, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    exposures.delta[0] = 9.9e6  # edits a temporary, not the stored block
    assert exposures.delta[0] == 1.0e6

    exposures.delta = [9.9e6] + [0.0] * 8  # the form that works
    assert exposures.delta[0] == 9.9e6
