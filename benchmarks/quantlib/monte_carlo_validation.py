#!/usr/bin/env python3
"""Level 2/3 validation of the Monte Carlo engine against live oracles.

    uv run python benchmarks/quantlib/monte_carlo_validation.py [--paths 200000]

Three independent yardsticks, in order of strength:

1. **Analytic**: QuantLib's ``AnalyticEuropeanEngine`` is the exact limit of our
   estimator, so the distance between the two must behave like the standard
   error our own engine reports. Each row records that distance divided by the
   combined standard error - a z-score that should be standard normal.
2. **Independent Monte Carlo implementation**: QuantLib's own MC engine, when
   its SWIG signature is available in the installed build. If it is not
   constructible the artifact says so explicitly instead of pretending the
   comparison happened (``quantlib_mc_engine_used`` in the JSON).
3. **Independent path generator**: a NumPy vectorised simulation with PCG64,
   a different algorithm and a different random stream, compared to ours on the
   same market.

No expected value is hard-coded anywhere; all references are computed by this
run.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import quantrisk
from quantrisk.experiments.metadata import environment, repo_relative, sha256_file, utc_timestamp

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "benchmarks" / "quantlib" / "results"

SEEDS = 40
DEFAULT_PATHS = 200_000
MATURITY = 1.0

SCENARIOS = {
    "atm_call": (quantrisk.pricing.OptionType.CALL, 100.0, 0.25, 0.02),
    "atm_put": (quantrisk.pricing.OptionType.PUT, 100.0, 0.25, 0.02),
    "otm_call": (quantrisk.pricing.OptionType.CALL, 120.0, 0.30, 0.0),
    "itm_put_long": (quantrisk.pricing.OptionType.PUT, 90.0, 0.40, 0.04),
}


def import_quantlib():  # noqa: ANN201
    try:
        import QuantLib as ql  # noqa: PLC0415
    except ImportError as error:
        print(f"QuantLib is required for this benchmark: {error}", file=sys.stderr)
        raise SystemExit(2) from error
    return ql


def quantlib_analytic(
    ql,
    spot: float,
    strike: float,
    rate: float,
    dividend: float,
    volatility: float,
    days: int,
    is_call: bool,
) -> float:  # noqa: ANN001
    evaluation_date = ql.Date(1, 1, 2024)
    ql.Settings.instance().evaluationDate = evaluation_date
    day_counter = ql.Actual365Fixed()
    process = ql.GeneralizedBlackScholesProcess(
        ql.QuoteHandle(ql.SimpleQuote(spot)),
        ql.YieldTermStructureHandle(ql.FlatForward(evaluation_date, dividend, day_counter)),
        ql.YieldTermStructureHandle(ql.FlatForward(evaluation_date, rate, day_counter)),
        ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(evaluation_date, ql.NullCalendar(), volatility, day_counter)
        ),
    )
    option = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.Option.Call if is_call else ql.Option.Put, strike),
        ql.EuropeanExercise(evaluation_date + ql.Period(days, ql.Days)),
    )
    option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
    return float(option.NPV())


def quantlib_mc(
    ql,
    spot: float,
    strike: float,
    rate: float,
    dividend: float,  # noqa: ANN001
    volatility: float,
    days: int,
    is_call: bool,
    samples: int,
):  # noqa: ANN201
    """Best-effort QuantLib MC engine comparison.

    The SWIG constructor for the Monte Carlo engines is not stable across
    QuantLib builds, so this returns ``None`` (recorded in the artifact) rather
    than failing the benchmark.
    """
    evaluation_date = ql.Date(1, 1, 2024)
    ql.Settings.instance().evaluationDate = evaluation_date
    day_counter = ql.Actual365Fixed()
    process = ql.GeneralizedBlackScholesProcess(
        ql.QuoteHandle(ql.SimpleQuote(spot)),
        ql.YieldTermStructureHandle(ql.FlatForward(evaluation_date, dividend, day_counter)),
        ql.YieldTermStructureHandle(ql.FlatForward(evaluation_date, rate, day_counter)),
        ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(evaluation_date, ql.NullCalendar(), volatility, day_counter)
        ),
    )
    payoff = ql.PlainVanillaPayoff(ql.Option.Call if is_call else ql.Option.Put, strike)
    exercise = ql.EuropeanExercise(evaluation_date + ql.Period(days, ql.Days))
    last_error: Exception | None = None
    for traits in ("pseudo", "random", "sobol"):
        try:
            engine = ql.MCEuropeanEngine(process, traits, 1, samples, samples, 1.0e-8, False, False)
            option = ql.VanillaOption(payoff, exercise)
            option.setPricingEngine(engine)
            return float(option.NPV())
        except Exception as error:  # noqa: BLE001 - reported, never swallowed
            last_error = error
    print(f"QuantLib MC engine unavailable: {last_error}", file=sys.stderr)
    return None


def numpy_reference(
    spot: float,
    rate: float,
    dividend: float,
    volatility: float,
    strike: float,
    is_call: bool,
    paths: int,
    seed: int,
) -> tuple[float, float]:
    drift = (rate - dividend - 0.5 * volatility * volatility) * MATURITY
    scale = volatility * math.sqrt(MATURITY)
    generator = np.random.default_rng(seed)
    chunks: list[np.ndarray] = []
    remaining = paths
    while remaining > 0:
        size = min(1_000_000, remaining)
        terminals = spot * np.exp(drift + scale * generator.standard_normal(size))
        chunks.append(
            np.maximum(terminals - strike, 0.0) if is_call else np.maximum(strike - terminals, 0.0)
        )
        remaining -= size
    payoffs = np.concatenate(chunks)
    discount = math.exp(-rate * MATURITY)
    return float(discount * payoffs.mean()), float(
        discount * payoffs.std(ddof=1) / math.sqrt(payoffs.size)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", type=int, default=DEFAULT_PATHS)
    parser.add_argument("--seeds", type=int, default=SEEDS)
    parser.add_argument("--out", type=Path, default=None)
    arguments = parser.parse_args()

    ql = import_quantlib()
    rows: list[dict[str, object]] = []
    z_scores: dict[str, list[float]] = {}
    quantlib_mc_available = True

    for name, (option_type, strike, volatility, dividend) in SCENARIOS.items():
        rate = 0.05
        days = int(round(MATURITY * 365))
        is_call = option_type == quantrisk.pricing.OptionType.CALL
        market = quantrisk.pricing.MarketParams(
            spot=100.0,
            rate=rate,
            dividend_yield=dividend,
            volatility=volatility,
            maturity=MATURITY,
        )
        option = quantrisk.pricing.EuropeanOption(option_type, strike)
        analytic_ql = quantlib_analytic(
            ql, 100.0, strike, rate, dividend, volatility, days, is_call
        )
        our_analytic = quantrisk.pricing.black_scholes(option, market).price
        ql_mc = quantlib_mc(
            ql, 100.0, strike, rate, dividend, volatility, days, is_call, arguments.paths
        )
        if ql_mc is None:
            quantlib_mc_available = False

        numpy_price, numpy_se = numpy_reference(
            100.0, rate, dividend, volatility, strike, is_call, arguments.paths, 20260101
        )

        for method_label, method in (
            ("plain", quantrisk.monte_carlo.VarianceReduction.NONE),
            ("antithetic", quantrisk.monte_carlo.VarianceReduction.ANTITHETIC),
            ("control_variate", quantrisk.monte_carlo.VarianceReduction.CONTROL_VARIATE),
        ):
            ours = []
            for seed in range(arguments.seeds):
                result = quantrisk.monte_carlo.MonteCarloEngine(400_000 + seed).price_european(
                    option, market, arguments.paths, method
                )
                ours.append((result.price, result.standard_error))
                rows.append(
                    {
                        "scenario": name,
                        "method": method_label,
                        "seed": 400_000 + seed,
                        "paths": arguments.paths,
                        "our_price": f"{result.price:.12g}",
                        "our_standard_error": f"{result.standard_error:.6e}",
                        "quantlib_analytic": f"{analytic_ql:.12g}",
                        "our_analytic": f"{our_analytic:.12g}",
                        "z_vs_quantlib_analytic": (
                            f"{(result.price - analytic_ql) / result.standard_error:.4f}"
                            if result.standard_error > 0
                            else "exact"
                        ),
                        "quantlib_mc_price": (
                            f"{ql_mc:.12g}" if ql_mc is not None else "unavailable"
                        ),
                        "numpy_mc_price": f"{numpy_price:.12g}",
                        "numpy_mc_standard_error": f"{numpy_se:.6e}",
                    }
                )
            mean_price = float(np.mean([price for price, _ in ours]))
            mean_se = float(np.mean([se for _, se in ours]))
            z_scores.setdefault(method_label, []).extend(
                [(price - analytic_ql) / se for price, se in ours if se > 0]
            )
            combined = math.hypot(mean_se / math.sqrt(arguments.seeds), numpy_se)
            rows.append(
                {
                    "scenario": name,
                    "method": f"{method_label}|summary",
                    "paths": arguments.paths,
                    "seed": "",
                    "our_price": f"{mean_price:.12g}",
                    "our_standard_error": f"{mean_se:.6e}",
                    "quantlib_analytic": f"{analytic_ql:.12g}",
                    "our_analytic": f"{our_analytic:.12g}",
                    "z_vs_quantlib_analytic": f"{(mean_price - analytic_ql) / mean_se:.4f}",
                    "quantlib_mc_price": f"{(mean_price - ql_mc) / combined:.4f}"
                    if ql_mc is not None
                    else "unavailable",
                    "numpy_mc_price": f"{numpy_price:.12g}",
                    "numpy_mc_standard_error": f"{numpy_se:.6e}",
                    "numpy_cross_check_z": f"{(mean_price - numpy_price) / combined:.4f}",
                }
            )

    output_dir = arguments.out or RESULTS
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "monte_carlo_validation.csv"
    field_names = sorted({key for row in rows for key in row})
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)

    pooled = {
        label: {
            "count": len(values),
            "mean": float(np.mean(values)),
            "std": float(np.std(values, ddof=1)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "fraction_within_2": float(np.mean(np.abs(np.asarray(values)) <= 2.0)),
        }
        for label, values in z_scores.items()
    }
    summary = {
        "artifact": "benchmarks/quantlib/monte_carlo_validation.py",
        "generated_at_utc": utc_timestamp(),
        "command": f"uv run python {Path(sys.argv[0]).name} --paths {arguments.paths}",
        "environment": environment(),
        "quantlib_version": ql.__version__,
        "paths_per_run": arguments.paths,
        "seeds": arguments.seeds,
        "scenarios": list(SCENARIOS),
        "quantlib_mc_engine_used": quantlib_mc_available,
        "quantlib_mc_note": (
            "compared"
            if quantlib_mc_available
            else "MCEuropeanEngine could not be constructed with this build's SWIG "
            "signature; the analytic oracle and the NumPy stream still provide "
            "independent references"
        ),
        "z_score_vs_quantlib_analytic": pooled,
        "rows": len(rows),
        "csv": repo_relative(csv_path),
        "csv_sha256": sha256_file(csv_path),
        "reading": (
            "With a correct estimator and a correctly reported standard error, the "
            "pooled z-scores have mean near 0 and standard deviation near 1, and about "
            "95 % of them fall inside +-2. A systematically understated standard error "
            "shows up first as std >> 1."
        ),
    }
    json_path = output_dir / "monte_carlo_validation.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                key: summary[key]
                for key in ("quantlib_mc_engine_used", "z_score_vs_quantlib_analytic", "rows")
            },
            indent=2,
            sort_keys=True,
        )
    )
    print(f"wrote {csv_path} and {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
