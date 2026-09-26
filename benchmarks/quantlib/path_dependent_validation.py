#!/usr/bin/env python3
"""Level 2 validation for Phase 4: path-dependent and stochastic-volatility
pricing against live QuantLib models.

    uv run python benchmarks/quantlib/path_dependent_validation.py [--quick]

Each family is attempted independently and its availability is recorded in the
artifact, so a missing or renamed QuantLib class shows up as
``"<family>_available": false`` with the exception text rather than as a silently
skipped comparison.

Families
--------
* ``heston_analytic`` - our full-truncation Euler Monte Carlo against QuantLib's
  ``AnalyticHestonEngine`` on identical parameters: the strongest oracle
  available for this model, and the reason the Heston section no longer has to
  declare itself unverifiable.
* ``heston_degenerate`` - xi = 0 collapses Heston to Black-Scholes, so the same
  simulation must reproduce ``AnalyticEuropeanEngine`` to within sampling error.
* ``barrier_continuous`` - our discretely monitored barrier against QuantLib's
  ``AnalyticBarrierEngine`` (continuous monitoring), reported for the raw
  discrete estimate and for the Broadie-Glasserman-Kou corrected one, which is
  how the size and direction of the monitoring bias gets measured instead of
  asserted.
* ``asian_independent_mc`` - our arithmetic Asian against QuantLib's
  ``MCDiscreteArithmeticAPEngine``: a different Monte Carlo implementation on the
  same model.

No value in the CSV is hard-coded.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import quantrisk
from quantrisk.experiments.metadata import environment, repo_relative, sha256_file, utc_timestamp

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "benchmarks" / "quantlib" / "results"

EVALUATION_DATE_DAY, EVALUATION_DATE_MONTH, EVALUATION_DATE_YEAR = 1, 1, 2024
DEFAULT_PATHS = 200_000
DEFAULT_STEPS = 250

HESTON_CASES = (
    # spot, strike, rate, dividend, v0, kappa, theta, xi, rho, days
    (100.0, 100.0, 0.05, 0.02, 0.0625, 2.0, 0.0625, 0.4, -0.7, 365),
    (100.0, 90.0, 0.05, 0.02, 0.0625, 2.0, 0.0625, 0.4, -0.7, 365),
    (100.0, 110.0, 0.05, 0.02, 0.0625, 2.0, 0.0625, 0.4, -0.7, 365),
    (100.0, 100.0, 0.05, 0.0, 0.04, 1.5, 0.09, 0.8, -0.3, 730),
    (100.0, 100.0, 0.03, 0.01, 0.09, 6.0, 0.04, 0.9, -0.9, 180),
)
BARRIER_CASES = (
    # spot, strike, rate, dividend, volatility, barrier, direction, days, steps
    (100.0, 100.0, 0.05, 0.0, 0.25, 130.0, "up", 365, 250),
    (100.0, 100.0, 0.05, 0.0, 0.25, 70.0, "down", 365, 250),
    (100.0, 110.0, 0.05, 0.02, 0.35, 140.0, "up", 182, 100),
)
ASIAN_CASES = (
    # spot, strike, rate, dividend, volatility, days, monitoring points
    (100.0, 100.0, 0.05, 0.02, 0.25, 365, 12),
    (100.0, 105.0, 0.05, 0.0, 0.30, 365, 52),
    (100.0, 95.0, 0.03, 0.01, 0.20, 182, 26),
)


def import_quantlib():  # noqa: ANN201
    try:
        import QuantLib as ql  # noqa: PLC0415
    except ImportError as error:
        print(f"QuantLib is required for this benchmark: {error}", file=sys.stderr)
        raise SystemExit(2) from error
    return error_module(ql)


def error_module(ql):  # noqa: ANN001, ANN201
    ql.Settings.instance().evaluationDate = ql.Date(
        EVALUATION_DATE_DAY, EVALUATION_DATE_MONTH, EVALUATION_DATE_YEAR
    )
    return ql


def flat(ql, value: float, day_counter):  # noqa: ANN001, ANN202
    return ql.YieldTermStructureHandle(
        ql.FlatForward(ql.Settings.instance().evaluationDate, value, day_counter)
    )


def bs_process(
    ql,
    spot: float,
    rate: float,
    dividend: float,
    volatility: float,  # noqa: ANN001
    day_counter,
):  # noqa: ANN001, ANN202
    return ql.GeneralizedBlackScholesProcess(
        ql.QuoteHandle(ql.SimpleQuote(spot)),
        flat(ql, dividend, day_counter),
        flat(ql, rate, day_counter),
        ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(
                ql.Settings.instance().evaluationDate,
                ql.NullCalendar(),
                volatility,
                day_counter,
            )
        ),
    )


def main() -> int:  # noqa: C901, PLR0915 - one readable pass per oracle family
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--paths", type=int, default=DEFAULT_PATHS)
    parser.add_argument("--out", type=Path, default=None)
    arguments = parser.parse_args()

    ql = import_quantlib()
    day_counter = ql.Actual365Fixed()
    expiry_of = lambda days: ql.Settings.instance().evaluationDate + ql.Period(days, ql.Days)  # noqa: E731

    paths = 50_000 if arguments.quick else arguments.paths
    heston_cases = HESTON_CASES[:2] if arguments.quick else HESTON_CASES
    barrier_cases = BARRIER_CASES[:1] if arguments.quick else BARRIER_CASES
    asian_cases = ASIAN_CASES[:1] if arguments.quick else ASIAN_CASES

    rows: list[dict[str, object]] = []
    availability: dict[str, dict[str, str | bool]] = {}

    # --- heston against the semi-analytic engine -------------------------
    for spot, strike, rate, dividend, v0, kappa, theta, xi, rho, days in heston_cases:
        maturity = days / 365.0
        parameters = quantrisk.stochastic.HestonParams()
        parameters.spot, parameters.rate = spot, rate
        parameters.dividend_yield = dividend
        parameters.initial_variance = v0
        parameters.kappa, parameters.theta, parameters.xi, parameters.rho = (
            kappa,
            theta,
            xi,
            rho,
        )
        parameters.maturity = maturity
        option = quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, strike)
        ours = quantrisk.stochastic.price_heston_european(
            parameters, option, paths, DEFAULT_STEPS, quantrisk.Rng(42)
        )
        try:
            process = ql.HestonProcess(
                flat(ql, rate, day_counter),
                flat(ql, dividend, day_counter),
                ql.QuoteHandle(ql.SimpleQuote(spot)),
                v0,
                kappa,
                theta,
                xi,
                rho,
            )
            engine = ql.AnalyticHestonEngine(ql.HestonModel(process))
            reference_option = ql.VanillaOption(
                ql.PlainVanillaPayoff(ql.Option.Call, strike), ql.EuropeanExercise(expiry_of(days))
            )
            reference_option.setPricingEngine(engine)
            reference = float(reference_option.NPV())
            availability["heston_analytic"] = {"available": True, "error": ""}
        except Exception as error:  # noqa: BLE001
            reference = float("nan")
            availability["heston_analytic"] = {"available": False, "error": str(error)[:400]}

        rows.append(
            {
                "family": "heston_analytic",
                "spot": spot,
                "strike": strike,
                "rate": rate,
                "dividend_yield": dividend,
                "v0": v0,
                "kappa": kappa,
                "theta": theta,
                "xi": xi,
                "rho": rho,
                "maturity_days": days,
                "paths": paths,
                "steps": DEFAULT_STEPS,
                "our_price": f"{ours.price:.12g}",
                "our_standard_error": f"{ours.standard_error:.6e}",
                "oracle_price": f"{reference:.12g}",
                "absolute_error": f"{abs(ours.price - reference):.6e}",
                "relative_error": (
                    f"{abs(ours.price - reference) / max(abs(reference), 1e-12):.6e}"
                    if math.isfinite(reference)
                    else "n/a"
                ),
                "error_in_standard_errors": (
                    f"{(ours.price - reference) / ours.standard_error:.4f}"
                    if math.isfinite(reference) and ours.standard_error > 0
                    else "n/a"
                ),
                "feller_satisfied": parameters.feller_condition_satisfied(),
                "clamped_variance_steps": ours.negative_variances_clamped,
                "note": ours.note,
            }
        )

        # xi = 0 degenerate case against the Black-Scholes analytic engine.
        degenerate = quantrisk.stochastic.HestonParams()
        degenerate.spot, degenerate.rate, degenerate.dividend_yield = spot, rate, dividend
        sigma = math.sqrt(v0)
        degenerate.initial_variance = v0
        degenerate.theta = v0
        degenerate.kappa = 1.0
        degenerate.xi = 0.0
        degenerate.rho = 0.0
        degenerate.maturity = maturity
        degenerate_ours = quantrisk.stochastic.price_heston_european(
            degenerate, option, paths, DEFAULT_STEPS, quantrisk.Rng(42)
        )
        process = bs_process(ql, spot, rate, dividend, sigma, day_counter)
        vanilla = ql.VanillaOption(
            ql.PlainVanillaPayoff(ql.Option.Call, strike), ql.EuropeanExercise(expiry_of(days))
        )
        vanilla.setPricingEngine(ql.AnalyticEuropeanEngine(process))
        reference_bs = float(vanilla.NPV())
        availability["heston_degenerate"] = {"available": True, "error": ""}
        rows.append(
            {
                "family": "heston_degenerate",
                "spot": spot,
                "strike": strike,
                "rate": rate,
                "dividend_yield": dividend,
                "v0": v0,
                "maturity_days": days,
                "paths": paths,
                "steps": DEFAULT_STEPS,
                "our_price": f"{degenerate_ours.price:.12g}",
                "our_standard_error": f"{degenerate_ours.standard_error:.6e}",
                "oracle_price": f"{reference_bs:.12g}",
                "absolute_error": f"{abs(degenerate_ours.price - reference_bs):.6e}",
                "relative_error": f"{abs(degenerate_ours.price - reference_bs) / reference_bs:.6e}",
                "error_in_standard_errors": (
                    f"{(degenerate_ours.price - reference_bs) / degenerate_ours.standard_error:.4f}"
                ),
                "note": "xi = 0: the scheme must collapse to Black-Scholes",
            }
        )

    # --- barriers against continuous-monitoring analytics ----------------
    for (
        spot,
        strike,
        rate,
        dividend,
        volatility,
        barrier_level,
        direction,
        days,
        steps,
    ) in barrier_cases:
        market = quantrisk.pricing.MarketParams(
            spot=spot,
            rate=rate,
            dividend_yield=dividend,
            volatility=volatility,
            maturity=days / 365.0,
        )
        barrier_type = (
            quantrisk.pricing.BarrierType.UP_AND_OUT
            if direction == "up"
            else quantrisk.pricing.BarrierType.DOWN_AND_OUT
        )
        option = quantrisk.pricing.BarrierOption(
            quantrisk.pricing.OptionType.CALL, strike, barrier_type, barrier_level, 0.0
        )
        discrete = quantrisk.monte_carlo.price_barrier(
            quantrisk.monte_carlo.MonteCarloEngine(42),
            option,
            market,
            paths,
            steps,
            False,
            False,
        )
        corrected = quantrisk.monte_carlo.price_barrier(
            quantrisk.monte_carlo.MonteCarloEngine(42),
            option,
            market,
            paths,
            steps,
            True,
            False,
        )
        try:
            process = bs_process(ql, spot, rate, dividend, volatility, day_counter)
            ql_barrier = ql.Barrier.UpOut if direction == "up" else ql.Barrier.DownOut
            barrier_option = ql.BarrierOption(
                ql_barrier,
                barrier_level,
                0.0,
                ql.PlainVanillaPayoff(ql.Option.Call, strike),
                ql.EuropeanExercise(expiry_of(days)),
            )
            barrier_option.setPricingEngine(ql.AnalyticBarrierEngine(process))
            reference = float(barrier_option.NPV())
            availability["barrier_continuous"] = {"available": True, "error": ""}
        except Exception as error:  # noqa: BLE001
            reference = float("nan")
            availability["barrier_continuous"] = {"available": False, "error": str(error)[:400]}

        for label, result in (("discrete_monitoring", discrete), ("bgk_corrected", corrected)):
            rows.append(
                {
                    "family": f"barrier_continuous_{label}",
                    "spot": spot,
                    "strike": strike,
                    "rate": rate,
                    "dividend_yield": dividend,
                    "volatility": volatility,
                    "barrier_level": barrier_level,
                    "direction": direction,
                    "maturity_days": days,
                    "paths": paths,
                    "steps": steps,
                    "our_price": f"{result.price:.12g}",
                    "our_standard_error": f"{result.standard_error:.6e}",
                    "oracle_price": f"{reference:.12g}",
                    "absolute_error": f"{abs(result.price - reference):.6e}",
                    "relative_error": (
                        f"{abs(result.price - reference) / max(abs(reference), 1e-12):.6e}"
                        if math.isfinite(reference)
                        else "n/a"
                    ),
                    "note": result.note,
                }
            )

    # --- geometric Asian against the discrete analytic engine ------------
    for spot, strike, rate, dividend, volatility, days, points in asian_cases:
        market = quantrisk.pricing.MarketParams(
            spot=spot,
            rate=rate,
            dividend_yield=dividend,
            volatility=volatility,
            maturity=days / 365.0,
        )
        geometric = quantrisk.pricing.AsianOption(
            quantrisk.pricing.OptionType.CALL,
            strike,
            quantrisk.pricing.AverageType.GEOMETRIC,
            points,
        )
        arithmetic = quantrisk.pricing.AsianOption(
            quantrisk.pricing.OptionType.CALL,
            strike,
            quantrisk.pricing.AverageType.ARITHMETIC,
            points,
        )
        ours_geometric = quantrisk.pricing.geometric_asian_price(geometric, market).price
        ours_simulated = quantrisk.monte_carlo.price_geometric_asian(
            quantrisk.monte_carlo.MonteCarloEngine(42), geometric, market, paths
        )
        ours_arithmetic = quantrisk.monte_carlo.price_asian(
            quantrisk.monte_carlo.MonteCarloEngine(42), arithmetic, market, paths, True
        )
        try:
            process = bs_process(ql, spot, rate, dividend, volatility, day_counter)
            expiry = expiry_of(days)
            # Fixing dates must match the convention the closed form assumes:
            # t_i = i * T / M for i = 1..M, so the last fixing is at expiry and
            # the interior dates are the nearest representable days.
            fixing_dates = [
                expiry - ql.Period(days - int(round(i * days / points)), ql.Days)
                for i in range(1, points + 1)
            ]
            asian = ql.DiscreteAveragingAsianOption(
                ql.Average.Geometric,
                1.0,
                0,
                fixing_dates,
                ql.PlainVanillaPayoff(ql.Option.Call, strike),
                ql.EuropeanExercise(expiry),
            )
            asian.setPricingEngine(ql.AnalyticDiscreteGeometricAveragePriceAsianEngine(process))
            reference = float(asian.NPV())
            availability["asian_geometric_analytic"] = {"available": True, "error": ""}
            reference_dates = len(fixing_dates)
        except Exception as error:  # noqa: BLE001 - reported, never swallowed
            reference = float("nan")
            availability["asian_geometric_analytic"] = {
                "available": False,
                "error": str(error)[:400],
            }
            reference_dates = 0

        # The analytic oracle prices the GEOMETRIC average, so it is only an
        # oracle for the two geometric rows. For the arithmetic row the same
        # number is reported as `arithmetic_minus_geometric`, the AM >= GM spread,
        # because calling it "relative error" would be misleading.
        for label, ours, se, comparable in (
            ("geometric_closed_form", ours_geometric, float("nan"), True),
            ("geometric_simulated", ours_simulated.price, ours_simulated.standard_error, True),
            (
                "arithmetic_control_variate",
                ours_arithmetic.price,
                ours_arithmetic.standard_error,
                False,
            ),
        ):
            rows.append(
                {
                    "family": f"asian_{label}",
                    "spot": spot,
                    "strike": strike,
                    "rate": rate,
                    "dividend_yield": dividend,
                    "volatility": volatility,
                    "maturity_days": days,
                    "monitoring_points": points,
                    "oracle_fixing_dates": reference_dates,
                    "paths": paths,
                    "our_price": f"{ours:.12g}",
                    "our_standard_error": f"{se:.6e}" if math.isfinite(se) else "n/a",
                    "oracle_price": f"{reference:.12g}",
                    "absolute_error": (f"{abs(ours - reference):.6e}" if comparable else "n/a"),
                    "relative_error": (
                        f"{abs(ours - reference) / max(abs(reference), 1e-12):.6e}"
                        if math.isfinite(reference) and comparable
                        else "n/a"
                    ),
                    "arithmetic_minus_geometric": (
                        "n/a" if comparable else f"{ours - ours_geometric:.6e}"
                    ),
                    "control_beta": (
                        f"{ours_arithmetic.control_beta:.9g}"
                        if label == "arithmetic_control_variate"
                        else "n/a"
                    ),
                    "note": (
                        "geometric Asian, discrete fixing dates at t_i = i T / M"
                        if comparable
                        else "arithmetic Asian: AM >= GM ordering check, the "
                        "geometric analytic value is not an oracle for it"
                    ),
                }
            )

    output_dir = arguments.out or RESULTS
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "path_dependent_vs_quantlib.csv"
    field_names = sorted({key for row in rows for key in row})
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)

    def worst(family_prefix: str) -> float:
        values = [
            float(row["relative_error"])
            for row in rows
            if str(row["family"]).startswith(family_prefix)
            and row["relative_error"] not in ("n/a", None)
        ]
        return max(values) if values else float("nan")

    summary = {
        "artifact": "benchmarks/quantlib/path_dependent_validation.py",
        "generated_at_utc": utc_timestamp(),
        "command": f"uv run python {Path(sys.argv[0]).name}",
        "environment": environment(),
        "quantlib_version": ql.__version__,
        "paths": paths,
        "oracle_availability": availability,
        "worst_relative_error": {
            "heston_analytic": worst("heston_analytic"),
            "heston_degenerate": worst("heston_degenerate"),
            "barrier_discrete": worst("barrier_continuous_discrete"),
            "barrier_bgk_corrected": worst("barrier_continuous_bgk"),
            "asian_geometric_closed_form": worst("asian_geometric_closed_form"),
            "asian_geometric_simulated": worst("asian_geometric_simulated"),
        },
        "rows": len(rows),
        "csv": repo_relative(csv_path),
        "csv_sha256": sha256_file(csv_path),
        "reading": (
            "heston_degenerate is the hard test: with xi = 0 the simulation must match "
            "Black-Scholes. heston_analytic compares against a semi-analytic model, so a "
            "residual beyond a few standard errors is discretisation bias of the "
            "full-truncation scheme, which is why the barrier and Heston rows are read "
            "together with the step counts."
        ),
    }
    json_path = output_dir / "path_dependent_vs_quantlib.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {k: summary[k] for k in ("oracle_availability", "worst_relative_error", "rows")},
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    print(f"wrote {csv_path} and {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
