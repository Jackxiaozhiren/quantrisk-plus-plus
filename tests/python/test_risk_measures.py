"""Phase 5 validation of the market-risk layer: estimators, bootstrap, backtests.

Three kinds of check, kept deliberately separate:

* **Level 1 (analytical / definitional):** the estimator equals the formula the
  model card and `docs/mathematical_specification.md` §6 claim it implements,
  recomputed here in NumPy from the definition.
* **Level 2 (live oracle):** SciPy supplies the Gaussian quantiles, the
  chi-square tail probabilities and a numerically integrated expected shortfall.
  Nothing from SciPy is pasted into the library.
* **Structural invariants:** monotonicity in the confidence level, ES >= VaR,
  reproducibility at fixed seeds, and non-negativity of a likelihood ratio.

Statistical *quality* claims (p-value uniformity, bootstrap coverage under
clustering) are measured over many replications in
`experiments/var_backtesting/run.py` and land in artifacts, not here.
"""

from __future__ import annotations

import math
from itertools import pairwise

import numpy as np
import pytest
import quantrisk

scipy_stats = pytest.importorskip("scipy.stats")
scipy_integrate = pytest.importorskip("scipy.integrate")

RISK = quantrisk.risk

TOLERANCE = 1e-12


def gaussian_sample(size: int, mean: float, sigma: float, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).normal(mean, sigma, size)


def _x_log(count: float, base: float) -> float:
    """count * log(base) with the 0 * log(0) = 0 limit the LR needs."""
    return 0.0 if count <= 0.0 else count * math.log(base)


def _integrated_expected_shortfall(mean: float, sigma: float, var_level: float) -> float:
    """ES of L = -R ~ N(-mean, sigma), integrated rather than taken in closed form."""
    density = scipy_stats.norm(loc=-mean, scale=sigma)
    tail_mass, _ = scipy_integrate.quad(density.pdf, var_level, math.inf, limit=400)
    tail_mean, _ = scipy_integrate.quad(
        lambda x: x * density.pdf(x), var_level, math.inf, limit=400
    )
    return tail_mean / tail_mass


def kupiec_reference(observations: int, exceptions: int, nominal: float) -> float:
    """LR_po written straight from the binomial likelihood ratio definition."""
    n, x = float(observations), float(exceptions)
    fitted = x / n
    null = _x_log(n - x, 1.0 - nominal) + _x_log(x, nominal)
    alt = _x_log(n - x, 1.0 - fitted) + _x_log(x, fitted)
    return max(0.0, -2.0 * (null - alt))


# --- return definitions --------------------------------------------------


@pytest.mark.parametrize("function", ["arithmetic", "log_returns"])
def test_return_definitions_match_their_formulas(function: str) -> None:
    prices = np.array([100.0, 101.0, 99.5, 100.25, 98.0])
    ours = np.array(getattr(RISK.returns, function)(prices))
    assert len(ours) == len(prices) - 1
    if function == "arithmetic":
        oracle = prices[1:] / prices[:-1] - 1.0
    else:
        oracle = np.log(prices[1:] / prices[:-1])
    assert np.max(np.abs(ours - oracle)) < TOLERANCE


def test_log_returns_never_exceed_arithmetic_returns() -> None:
    # Level 1 anchor: log(1 + x) <= x for x > -1, with equality nowhere, so the
    # two definitions must order every single-period move the same way.
    prices = np.array([100.0, 90.0, 110.0, 110.5, 87.25, 100.0])
    arithmetic = np.array(RISK.returns.arithmetic(prices))
    log = np.array(RISK.returns.log_returns(prices))
    assert np.all(log < arithmetic)
    assert not np.allclose(arithmetic, log)


def test_a_price_that_hits_zero_is_a_loss_of_everything_not_an_error() -> None:
    # Arithmetic returns only need the *previous* price to be positive: -100 % is
    # a legitimate observation. The log return of the same move is undefined.
    assert RISK.returns.arithmetic([100.0, 0.0]) == pytest.approx([-1.0])
    with pytest.raises(quantrisk.ValidationError):
        RISK.returns.log_returns([100.0, 0.0])
    with pytest.raises(quantrisk.ValidationError):
        RISK.returns.arithmetic([100.0])


# --- point estimators ----------------------------------------------------


def test_historical_var_is_the_linear_quantile_of_losses() -> None:
    sample = gaussian_sample(4001, 0.0002, 0.012, 11)
    for level in (0.90, 0.95, 0.99):
        ours = RISK.historical_var(sample, level).value
        oracle = float(np.quantile(-sample, level))
        assert ours == pytest.approx(oracle, rel=1e-12), level


def test_historical_es_is_the_mean_of_the_worst_tail() -> None:
    sample = gaussian_sample(4001, 0.0002, 0.012, 12)
    for level in (0.90, 0.95, 0.99):
        losses = np.sort(-sample)
        k = max(1, math.ceil(len(losses) * (1.0 - level)))
        oracle = float(np.mean(losses[-k:]))
        assert RISK.historical_es(sample, level).value == pytest.approx(oracle, rel=1e-12)


@pytest.mark.oracle
def test_gaussian_var_agrees_with_scipy_and_es_with_numeric_integration() -> None:
    sample = gaussian_sample(20000, 0.0005, 0.018, 13)
    mean, sigma = float(np.mean(sample)), float(np.std(sample, ddof=1))
    for level in (0.90, 0.95, 0.99):
        ours = RISK.gaussian_var(sample, level).value
        # Loss L = -R ~ N(-mean, sigma); its level-quantile is the VaR.
        oracle = float(scipy_stats.norm.ppf(level, loc=-mean, scale=sigma))
        assert ours == pytest.approx(oracle, rel=1e-9), level

        # Quadrature rather than the closed form the implementation uses, and
        # normalised by the integrated tail mass rather than by 1 - alpha.
        es = RISK.gaussian_es(sample, level).value
        assert es == pytest.approx(_integrated_expected_shortfall(mean, sigma, oracle), rel=1e-6), (
            level
        )


def test_es_at_least_var_and_both_grow_with_the_confidence_level() -> None:
    sample = gaussian_sample(5000, 0.0, 0.02, 14)
    levels = [0.80, 0.90, 0.95, 0.975, 0.99]
    var = [RISK.historical_var(sample, level).value for level in levels]
    es = [RISK.historical_es(sample, level).value for level in levels]
    assert all(earlier < later for earlier, later in pairwise(var))
    assert all(earlier < later for earlier, later in pairwise(es))
    assert all(v <= e for v, e in zip(var, es, strict=True))


def test_a_heavy_tailed_sample_has_es_strictly_above_var() -> None:
    # Student-t(3) has finite mean but a real tail gap between VaR and ES; a
    # Gaussian-fit estimator would understate both.
    sample = scipy_stats.t.rvs(df=3, scale=0.02, size=200000, random_state=5)
    var = RISK.historical_var(sample, 0.99).value
    es = RISK.historical_es(sample, 0.99).value
    gaussian = RISK.gaussian_var(sample, 0.99).value
    assert es > var
    assert gaussian < var, "a normal fit must understate the t(3) tail"


def test_monte_carlo_measures_read_simulated_pnl_not_returns() -> None:
    pnl = gaussian_sample(20001, 0.0, 1.0, 15)
    var = RISK.monte_carlo_var(pnl, 0.95)
    es = RISK.monte_carlo_es(pnl, 0.95)
    assert var.value == pytest.approx(float(np.quantile(-pnl, 0.95)), rel=1e-12)
    losses = np.sort(-pnl)
    tail = losses[-math.ceil(len(losses) * 0.05) :]
    assert es.value == pytest.approx(float(np.mean(tail)), rel=1e-12)
    # P&L and returns reach the same estimator because both are negated into
    # losses; the Monte Carlo pair only adds the quantile standard error.
    assert es.value == pytest.approx(RISK.historical_es(pnl, 0.95).value, rel=1e-12)
    assert var.value > 1.5 and var.value < 1.8
    # The interval must come from the quantile density, and be a real interval.
    assert var.has_interval
    assert var.ci_low <= var.value <= var.ci_high
    assert var.standard_error > 0.0
    assert var.observations == 20001


def test_monte_carlo_var_is_the_sorted_quantile_not_an_arbitrary_element() -> None:
    # Regression test: the estimator once read the quantile off an *unsorted*
    # loss array, which produced a plausible number in the middle of the
    # distribution instead of the 95th percentile of the tail.
    rng = np.random.default_rng(16)
    pnl = rng.normal(0.0, 1.0, 5000)
    shuffled = pnl.copy()
    rng.shuffle(shuffled)
    assert RISK.monte_carlo_var(pnl, 0.95).value == pytest.approx(
        RISK.monte_carlo_var(shuffled, 0.95).value, rel=1e-12
    )
    assert RISK.monte_carlo_var(pnl, 0.95).value > 1.5


# --- portfolio algebra ---------------------------------------------------


def test_linear_pnl_and_covariance_match_numpy() -> None:
    rows = np.array([[0.01, -0.02], [0.03, 0.00], [0.01, -0.01], [-0.04, 0.02]])
    weights = np.array([0.6, 0.4])
    ours = np.array(RISK.linear_pnl(weights, rows.reshape(-1), 2, 1000.0))
    assert ours == pytest.approx(1000.0 * rows @ weights, abs=1e-9)

    cov = np.array(RISK.sample_covariance(rows.reshape(-1), 2, 4))
    assert cov == pytest.approx(np.cov(rows, rowvar=False, ddof=1).reshape(-1), rel=1e-12)


def test_sample_covariance_of_independent_assets_is_diagonal_in_expectation() -> None:
    rng = np.random.default_rng(17)
    rows = rng.normal(0.0, 0.01, (20000, 3))
    cov = np.array(RISK.sample_covariance(rows.reshape(-1), 3, 20000)).reshape(3, 3)
    assert np.max(np.abs(np.diag(cov) - np.var(rows, axis=0, ddof=1))) < 1e-14
    off_diagonal = np.abs(cov - np.diag(np.diag(cov)))
    assert off_diagonal.max() < 0.05 * np.diag(cov).mean()


# --- bootstrap -----------------------------------------------------------


def test_bootstrap_intervals_are_reproducible_and_bracket_the_point_estimate() -> None:
    sample = gaussian_sample(1500, 0.0, 0.02, 18)
    for kind, block in (
        (RISK.BootstrapKind.IID, 0),
        (RISK.BootstrapKind.MOVING_BLOCK, 8),
    ):
        first = RISK.bootstrap_var(sample, 0.95, 600, 0.90, kind, block, 99)
        again = RISK.bootstrap_var(sample, 0.95, 600, 0.90, kind, block, 99)
        assert (first.point, first.ci_low, first.ci_high) == (
            again.point,
            again.ci_low,
            again.ci_high,
        )
        other = RISK.bootstrap_var(sample, 0.95, 600, 0.90, kind, block, 100)
        assert other.ci_high != first.ci_high, "the seed must actually drive the draws"
        assert first.ci_low <= first.point <= first.ci_high
        assert first.replicates == 600
        assert first.measure == "historical_var"


def test_wider_interval_level_gives_a_wider_interval() -> None:
    sample = gaussian_sample(1200, 0.0, 0.02, 19)
    narrow = RISK.bootstrap_var(sample, 0.95, 800, 0.80, RISK.BootstrapKind.IID, 0, 7)
    wide = RISK.bootstrap_var(sample, 0.95, 800, 0.95, RISK.BootstrapKind.IID, 0, 7)
    assert wide.ci_high - wide.ci_low > narrow.ci_high - narrow.ci_low


def test_block_bootstrap_is_the_only_one_claiming_to_see_clustering() -> None:
    # Volatility clustering: sign-independent, but large moves come in runs.
    shocks = np.random.default_rng(20).standard_normal(1500)
    sigma = np.empty_like(shocks)
    sigma[0] = 0.01
    for i in range(1, len(shocks)):
        sigma[i] = math.sqrt(0.90 * sigma[i - 1] ** 2 + 0.10 * 0.01**2)
    sample = shocks * sigma

    iid = RISK.bootstrap_var(sample, 0.95, 800, 0.90, RISK.BootstrapKind.IID, 0, 21)
    block = RISK.bootstrap_var(sample, 0.95, 800, 0.90, RISK.BootstrapKind.MOVING_BLOCK, 0, 21)
    assert block.block_length == RISK.suggested_block_length(len(sample)) > 1
    assert iid.note != block.note
    assert "serially independent" in iid.note
    assert "volatility clustering" in block.note
    # The two designs disagree; that disagreement is the point of the block one.
    assert abs(block.ci_high - block.ci_low) != pytest.approx(iid.ci_high - iid.ci_low, rel=1e-6)


def test_suggested_block_length_follows_the_cubic_root_rule() -> None:
    for n in (27, 125, 250, 1000, 250000):
        assert RISK.suggested_block_length(n) == round(n ** (1.0 / 3.0))


def test_bootstrap_rejects_impossible_settings() -> None:
    sample = gaussian_sample(200, 0.0, 0.01, 22)
    with pytest.raises(quantrisk.ValidationError):
        RISK.bootstrap_var(sample, 1.0)
    with pytest.raises(quantrisk.ValidationError):
        RISK.bootstrap_var(sample, 0.95, 0)
    with pytest.raises(quantrisk.ValidationError):
        RISK.bootstrap_var(sample, 0.95, 100, 0.9, RISK.BootstrapKind.IID, 5, 1)
    with pytest.raises(quantrisk.ValidationError):
        RISK.bootstrap_var(sample, 0.95, 100, 0.9, RISK.BootstrapKind.MOVING_BLOCK, 200, 1)


# --- coverage backtests --------------------------------------------------


def clustered_flags(observations: int, cluster_start: int, length: int) -> np.ndarray:
    flags = np.zeros(observations, dtype=int)
    flags[cluster_start : cluster_start + length] = 1
    return flags


def flags_to_returns(flags: np.ndarray) -> np.ndarray:
    return np.where(flags == 1, -0.05, 0.01)


@pytest.mark.parametrize(
    ("observations", "exceptions", "confidence_level"),
    [
        (250, 13, 0.95),
        (250, 0, 0.95),
        (250, 250, 0.95),
        (100, 10, 0.90),
        (2000, 100, 0.95),
        (250, 1, 0.99),
        (500, 499, 0.99),
    ],
)
@pytest.mark.oracle
def test_kupiec_matches_an_independent_implementation_and_scipy(
    observations: int, exceptions: int, confidence_level: int
) -> None:
    flags = np.zeros(observations, dtype=int)
    flags[:exceptions] = 1
    series = RISK.flag_violations(flags_to_returns(flags), 0.02)
    assert series.exceptions == exceptions
    result = RISK.kupiec_pof_test(series, confidence_level)
    reference = kupiec_reference(observations, exceptions, 1.0 - confidence_level)
    assert result.statistic == pytest.approx(reference, rel=1e-9, abs=1e-14)
    assert result.p_value == pytest.approx(float(scipy_stats.chi2.sf(reference, 1)), rel=1e-6)
    assert result.statistic >= 0.0
    assert result.rejected_at_5_percent == (result.p_value < 0.05)


def test_violation_flagging_uses_the_loss_convention() -> None:
    returns = np.array([-0.03, -0.02, -0.019, 0.0, 0.05])
    series = RISK.flag_violations(returns, 0.02)
    # A loss strictly greater than the VaR level is the violation; equal is not.
    assert series.flags == [1, 0, 0, 0, 0]
    assert series.observations == 5
    assert series.violation_rate == pytest.approx(0.2)


def test_a_single_violation_level_may_be_replaced_by_a_time_varying_series() -> None:
    returns = np.array([-0.03, 0.01, -0.03, 0.01])
    flat = RISK.flag_violations(returns, 0.02)
    varying = RISK.flag_violations(returns, [0.02, 0.02, 0.04, 0.02])
    assert flat.exceptions == 2
    assert varying.exceptions == 1, "a higher level that day must absorb the loss"
    with pytest.raises(quantrisk.ValidationError):
        RISK.flag_violations(returns, [0.02, 0.02])


@pytest.mark.oracle
def test_independence_test_separates_clustering_from_randomness() -> None:
    clustered = RISK.flag_violations(flags_to_returns(clustered_flags(250, 100, 12)), 0.02)
    evenly_spaced = (np.arange(250) % 20 == 0).astype(int)
    spread = RISK.flag_violations(flags_to_returns(evenly_spaced), 0.02)
    clustered_result = RISK.christoffersen_independence_test(clustered)
    spread_result = RISK.christoffersen_independence_test(spread)
    assert clustered_result.degrees_of_freedom == 1
    assert clustered_result.statistic > spread_result.statistic
    assert clustered_result.rejected_at_5_percent
    assert not spread_result.rejected_at_5_percent
    for result in (clustered_result, spread_result):
        assert result.p_value == pytest.approx(
            float(scipy_stats.chi2.sf(result.statistic, 1)), rel=1e-6
        )


@pytest.mark.oracle
def test_conditional_coverage_adds_the_components() -> None:
    series = RISK.flag_violations(flags_to_returns(clustered_flags(250, 60, 9)), 0.02)
    independence = RISK.christoffersen_independence_test(series)
    coverage = RISK.kupiec_pof_test(series, 0.95)
    conditional = RISK.christoffersen_conditional_coverage_test(series, 0.95)
    assert conditional.degrees_of_freedom == 2
    assert conditional.statistic == pytest.approx(
        independence.statistic + coverage.statistic, rel=1e-12
    )
    assert conditional.p_value == pytest.approx(
        float(scipy_stats.chi2.sf(conditional.statistic, 2)), rel=1e-6
    )
    assert conditional.critical_value_95 == pytest.approx(
        float(scipy_stats.chi2.isf(0.05, 2)), rel=1e-9
    )
    # Solving the critical value from the same distribution the p-value uses is
    # the reason the two cannot disagree about a verdict.
    assert (conditional.statistic > conditional.critical_value_95) == (
        conditional.rejected_at_5_percent
    )


def test_degenerate_series_are_reported_as_untestable() -> None:
    never = RISK.flag_violations(np.full(250, 0.01), 0.02)
    independence = RISK.christoffersen_independence_test(never)
    assert independence.degenerate
    assert math.isnan(independence.statistic)
    assert not independence.rejected_at_5_percent
    conditional = RISK.christoffersen_conditional_coverage_test(never, 0.95)
    assert conditional.degenerate and math.isnan(conditional.statistic)
    # Kupiec is still defined at zero violations, and correctly rejects.
    coverage = RISK.kupiec_pof_test(never, 0.95)
    assert not coverage.degenerate
    assert coverage.statistic > 0.0

    always = RISK.flag_violations(np.full(250, -0.05), 0.02)
    assert always.exceptions == 250
    assert RISK.kupiec_pof_test(always, 0.95).statistic > 0.0


def test_backtest_report_carries_the_full_phase_5_output_set() -> None:
    returns = gaussian_sample(1200, 0.0, 0.01, 23)
    level = RISK.gaussian_var(returns, 0.95).value
    # Re-price the VaR each day from the trailing window, as a real backtest does.
    levels = np.array(
        [
            RISK.gaussian_var(returns[max(i - 300, 0) : i], 0.95).value if i >= 300 else level
            for i in range(len(returns))
        ]
    )
    report = RISK.backtest_var(returns, levels, 0.95)
    assert report.series.observations == 1200
    assert report.kupiec.test == "kupiec_pof"
    assert report.independence.test == "christoffersen_independence"
    assert report.conditional.test == "christoffersen_conditional_coverage"
    assert report.kupiec.observations == report.series.observations
    assert report.kupiec.exceptions == report.series.exceptions
    assert "asymptotic" in report.note
    for result in (report.kupiec, report.independence, report.conditional):
        assert 0.0 <= result.p_value <= 1.0 or math.isnan(result.p_value)
        assert result.interpretation
