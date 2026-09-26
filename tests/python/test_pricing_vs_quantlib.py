"""Level 2 validation against QuantLib, live in the test run.

Two things are checked here:

1. The core's prices and Greeks against QuantLib's ``AnalyticEuropeanEngine``
   on the same inputs, computed at run time. Nothing from a previous run or from
   documentation is embedded as an expected value (PROJECT_SPEC.md §4).
2. That ``benchmarks/quantlib/pricing_validation.py`` still executes and still
   reports a negligible worst-case error, so the published artifact cannot rot
   into something the test suite no longer covers.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest
import quantrisk

ql = pytest.importorskip("QuantLib")
pytest.importorskip("scipy")

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = REPO_ROOT / "benchmarks" / "quantlib" / "pricing_validation.py"
EVALUATION_DATE = ql.Date(1, 1, 2024)
PRICE_TOLERANCE = 1.0e-10
GREEK_TOLERANCE = 1.0e-8

CASES = [
    (100.0, 100.0, 0.05, 0.0, 0.20, 365),
    (100.0, 90.0, 0.05, 0.02, 0.35, 91),
    (100.0, 110.0, -0.01, 0.0, 0.60, 730),
    (85.0, 100.0, 0.08, 0.04, 0.15, 30),
    (150.0, 100.0, 0.0, 0.0, 1.00, 182),
]


def build_oracle_option(
    spot: float,
    strike: float,
    rate: float,
    dividend_yield: float,
    volatility: float,
    days: int,
    is_call: bool,
):  # noqa: ANN201
    """QuantLib's own analytic European engine on identical inputs."""
    ql.Settings.instance().evaluationDate = EVALUATION_DATE
    day_counter = ql.Actual365Fixed()
    quote = ql.QuoteHandle(ql.SimpleQuote(spot))
    process = ql.GeneralizedBlackScholesProcess(
        quote,
        ql.YieldTermStructureHandle(ql.FlatForward(EVALUATION_DATE, dividend_yield, day_counter)),
        ql.YieldTermStructureHandle(ql.FlatForward(EVALUATION_DATE, rate, day_counter)),
        ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(EVALUATION_DATE, ql.NullCalendar(), volatility, day_counter)
        ),
    )
    expiry = EVALUATION_DATE + ql.Period(days, ql.Days)
    option = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.Option.Call if is_call else ql.Option.Put, strike),
        ql.EuropeanExercise(expiry),
    )
    option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
    return option


def ours(
    spot: float,
    strike: float,
    rate: float,
    dividend_yield: float,
    volatility: float,
    days: int,
    is_call: bool,
) -> quantrisk.pricing.PricingResult:
    market = quantrisk.pricing.MarketParams(
        spot=spot,
        rate=rate,
        dividend_yield=dividend_yield,
        volatility=volatility,
        maturity=days / 365.0,
    )
    option_type = quantrisk.pricing.OptionType.CALL if is_call else quantrisk.pricing.OptionType.PUT
    return quantrisk.pricing.black_scholes(
        quantrisk.pricing.EuropeanOption(option_type, strike), market
    )


@pytest.mark.oracle
@pytest.mark.parametrize("spot,strike,rate,dividend_yield,volatility,days", CASES)
@pytest.mark.parametrize("is_call", [True, False])
def test_price_matches_quantlib(
    spot: float,
    strike: float,
    rate: float,
    dividend_yield: float,
    volatility: float,
    days: int,
    is_call: bool,
) -> None:
    reference = build_oracle_option(spot, strike, rate, dividend_yield, volatility, days, is_call)
    oracle_price = float(reference.NPV())
    our_price = float(ours(spot, strike, rate, dividend_yield, volatility, days, is_call).price)
    assert our_price == pytest.approx(oracle_price, rel=PRICE_TOLERANCE, abs=1.0e-12), (
        spot,
        strike,
        rate,
        dividend_yield,
        volatility,
        days,
        is_call,
        our_price,
        oracle_price,
    )


@pytest.mark.oracle
@pytest.mark.parametrize("spot,strike,rate,dividend_yield,volatility,days", CASES)
def test_greeks_match_quantlib(
    spot: float, strike: float, rate: float, dividend_yield: float, volatility: float, days: int
) -> None:
    reference = build_oracle_option(spot, strike, rate, dividend_yield, volatility, days, True)
    market = quantrisk.pricing.MarketParams(
        spot=spot,
        rate=rate,
        dividend_yield=dividend_yield,
        volatility=volatility,
        maturity=days / 365.0,
    )
    analytic = quantrisk.pricing.black_scholes_greeks(
        quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, strike), market
    )
    # Units were verified by measurement, not assumed: this build reports vega
    # and rho per unit of vol / rate, exactly as docs/mathematical_specification.md
    # §0 freezes them. See benchmarks/quantlib/pricing_validation.py docstring.
    for greek in ("delta", "gamma", "vega", "theta", "rho"):
        oracle_value = float(getattr(reference, greek)())
        our_value = float(getattr(analytic, greek))
        assert our_value == pytest.approx(oracle_value, rel=GREEK_TOLERANCE, abs=1.0e-9), (
            greek,
            our_value,
            oracle_value,
        )


@pytest.mark.oracle
def test_crr_lattice_is_within_its_own_discretisation_error_of_quantlib(
    tmp_path: Path,
) -> None:
    """Textbook CRR and QuantLib's binomial are different O(dt) schemes.

    The meaningful statement is not "they agree to 1e-12" but "they agree with
    each other far more closely than either agrees with the Black-Scholes
    limit", i.e. the residual is the shared discretisation error and not a
    modelling disagreement.
    """
    del tmp_path
    market = quantrisk.pricing.MarketParams(
        spot=100.0, rate=0.05, dividend_yield=0.02, volatility=0.25, maturity=1.0
    )
    option = quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, 100.0)
    analytic = quantrisk.pricing.black_scholes(option, market).price
    ql.Settings.instance().evaluationDate = EVALUATION_DATE
    day_counter = ql.Actual365Fixed()
    expiry = EVALUATION_DATE + ql.Period(365, ql.Days)
    process = ql.GeneralizedBlackScholesProcess(
        ql.QuoteHandle(ql.SimpleQuote(100.0)),
        ql.YieldTermStructureHandle(ql.FlatForward(EVALUATION_DATE, 0.02, day_counter)),
        ql.YieldTermStructureHandle(ql.FlatForward(EVALUATION_DATE, 0.05, day_counter)),
        ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(EVALUATION_DATE, ql.NullCalendar(), 0.25, day_counter)
        ),
    )
    for steps in (100, 400):
        reference_option = ql.VanillaOption(
            ql.PlainVanillaPayoff(ql.Option.Call, 100.0), ql.EuropeanExercise(expiry)
        )
        reference_option.setPricingEngine(ql.BinomialVanillaEngine(process, "crr", steps))
        oracle_lattice = float(reference_option.NPV())
        ours_lattice = quantrisk.pricing.crr_binomial(
            option, market, quantrisk.pricing.ExerciseStyle.EUROPEAN, steps
        ).price
        mutual = abs(ours_lattice - oracle_lattice)
        our_error = abs(ours_lattice - analytic)
        assert our_error > 0.0
        assert mutual < 0.2 * our_error, (steps, ours_lattice, oracle_lattice, analytic)


@pytest.mark.oracle
def test_published_benchmark_script_still_runs_and_still_passes(tmp_path: Path) -> None:
    output = tmp_path / "results"
    completed = subprocess.run(  # noqa: S603, S607
        [sys.executable, str(BENCHMARK), "--quick", "--out", str(output)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
        timeout=600,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    summary = json.loads((output / "pricing_vs_quantlib.json").read_text())
    # quick grid: 3 strikes x 2 types x (1 price + 5 greeks) + 12 lattice rows
    assert summary["rows"] == 48
    absolute = summary["worst_absolute_error"]
    assert absolute["black_scholes_price"] < 1.0e-9
    for greek in ("delta", "gamma", "vega", "theta", "rho"):
        assert absolute[f"greek_{greek}"] < 1.0e-9
    # The lattice rows must be present and close in the well-resolved regime.
    assert "lattice[sigma*sqrt(dt)<=0.25]" in absolute
    assert absolute["lattice[sigma*sqrt(dt)<=0.25]"] < 1.0e-2
    assert summary["quantlib_version"]
    assert math.isfinite(summary["price_floor"])
    csv_text = (output / "pricing_vs_quantlib.csv").read_text()
    assert "our_price" in csv_text and "quantlib_price" in csv_text
