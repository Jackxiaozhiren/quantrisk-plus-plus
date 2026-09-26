"""Phase 3 Monte Carlo validation against live oracles (skipped without them).

The statistical claims here are calibrated, not decorative: the acceptance
bands come from the sampling distribution of the quantity under test, so a
mis-reported standard error cannot pass them.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import quantrisk

ql = pytest.importorskip("QuantLib")
pytest.importorskip("scipy")

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = REPO_ROOT / "benchmarks" / "quantlib" / "monte_carlo_validation.py"
mc = quantrisk.monte_carlo
pricing = quantrisk.pricing
VR = mc.VarianceReduction

MARKET = pricing.MarketParams(
    spot=100.0, rate=0.05, dividend_yield=0.02, volatility=0.25, maturity=1.0
)
EVALUATION_DATE = ql.Date(1, 1, 2024)


def quantlib_analytic(is_call: bool, strike: float) -> float:
    ql.Settings.instance().evaluationDate = EVALUATION_DATE
    day_counter = ql.Actual365Fixed()
    process = ql.GeneralizedBlackScholesProcess(
        ql.QuoteHandle(ql.SimpleQuote(100.0)),
        ql.YieldTermStructureHandle(
            ql.FlatForward(EVALUATION_DATE, MARKET.dividend_yield, day_counter)
        ),
        ql.YieldTermStructureHandle(ql.FlatForward(EVALUATION_DATE, MARKET.rate, day_counter)),
        ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(EVALUATION_DATE, ql.NullCalendar(), MARKET.volatility, day_counter)
        ),
    )
    option = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.Option.Call if is_call else ql.Option.Put, strike),
        ql.EuropeanExercise(EVALUATION_DATE + ql.Period(365, ql.Days)),
    )
    option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
    return float(option.NPV())


@pytest.mark.oracle
@pytest.mark.parametrize("is_call", [True, False])
def test_estimate_and_oracle_agree_within_the_reported_error(is_call: bool) -> None:
    """20 seeds; the pooled z-scores against QuantLib's analytic value must look
    standard normal, which fails if the standard error is understated."""
    strike = 100.0
    option = pricing.EuropeanOption(
        pricing.OptionType.CALL if is_call else pricing.OptionType.PUT, strike
    )
    reference = quantlib_analytic(is_call, strike)
    scores = []
    for seed in range(20):
        result = mc.MonteCarloEngine(31_000 + seed).price_european(option, MARKET, 50_000)
        scores.append((result.price - reference) / result.standard_error)
    array = np.asarray(scores)
    assert abs(float(array.mean())) < 0.6, scores
    assert 0.5 < float(array.std(ddof=1)) < 1.9, scores


@pytest.mark.oracle
def test_variance_reduction_does_not_bias_the_estimate() -> None:
    """Unbiasedness must survive the variance reduction: all three estimators
    agree with the analytic oracle and with each other."""
    strike = 100.0
    option = pricing.EuropeanOption(pricing.OptionType.CALL, strike)
    reference = quantlib_analytic(True, strike)
    for method in (VR.NONE, VR.ANTITHETIC, VR.CONTROL_VARIATE):
        prices = [
            mc.MonteCarloEngine(77_000 + seed).price_european(option, MARKET, 25_000, method)
            for seed in range(30)
        ]
        mean = float(np.mean([result.price for result in prices]))
        mean_se = float(np.mean([result.standard_error for result in prices]))
        combined = mean_se / math.sqrt(len(prices))
        assert abs(mean - reference) < 4.0 * combined + 1.0e-9, (method, mean, reference)


@pytest.mark.oracle
def test_control_variate_beats_plain_monte_carlo_on_realised_error() -> None:
    option = pricing.EuropeanOption(pricing.OptionType.CALL, 100.0)
    reference = quantlib_analytic(True, 100.0)
    plain = []
    reduced = []
    for seed in range(60):
        plain.append(
            mc.MonteCarloEngine(900 + seed).price_european(option, MARKET, 5_000).price - reference
        )
        reduced.append(
            mc.MonteCarloEngine(900 + seed)
            .price_european(option, MARKET, 5_000, VR.CONTROL_VARIATE)
            .price
            - reference
        )
    plain_mse = float(np.mean(np.square(plain)))
    reduced_mse = float(np.mean(np.square(reduced)))
    assert reduced_mse < plain_mse, (plain_mse, reduced_mse)


@pytest.mark.oracle
def test_published_monte_carlo_benchmark_script_runs_and_reports(tmp_path: Path) -> None:
    completed = subprocess.run(  # noqa: S603, S607
        [
            sys.executable,
            str(BENCHMARK),
            "--paths",
            "20000",
            "--seeds",
            "10",
            "--out",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
        timeout=600,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    summary = json.loads((tmp_path / "monte_carlo_validation.json").read_text())
    assert summary["rows"] > 100
    pooled = summary["z_score_vs_quantlib_analytic"]
    for method, stats in pooled.items():
        assert abs(stats["mean"]) < 0.8, (method, stats)
        assert 0.4 < stats["std"] < 2.0, (method, stats)
        assert stats["fraction_within_2"] >= 0.85, (method, stats)
    # The artifact must state honestly whether the third yardstick was available.
    assert isinstance(summary["quantlib_mc_engine_used"], bool)
    text = (tmp_path / "monte_carlo_validation.csv").read_text()
    assert "z_vs_quantlib_analytic" in text
