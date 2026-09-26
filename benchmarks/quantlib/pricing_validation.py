#!/usr/bin/env python3
"""Level 2 validation: the deterministic pricing core against live QuantLib.

QuantLib is an oracle only (PROJECT_SPEC.md §2.2). Every reference number in the
output is computed by this run; nothing is pasted from documentation or from an
earlier execution, and the QuantLib version is recorded in the artifact.

    uv run python benchmarks/quantlib/pricing_validation.py [--quick]

Two conventions were established by *measurement* rather than assumption, and
both are recorded in the JSON summary:

1. Greek units. QuantLib's ``vega()``/``rho()`` on this build are per unit of
   volatility / rate - identical to our convention
   (docs/mathematical_specification.md §0). The first version of this script
   assumed the per-1-percentage-point convention and reported a 0.99 relative
   error, which is what exposed the assumption. Measured agreement is ~1e-15.
2. Lattice parameterisation. ``BinomialVanillaEngine(process, "crr", N)`` is a
   different O(dt) discretisation of the same risk-neutral dynamics from the
   textbook Cox-Ross-Rubinstein tree in the core (where ``u * d == 1`` holds
   exactly). The two lattices differ by a convention term of order ``1/N`` -
   measured at ~1.3e-4 relative for N = 50 - while both converge to the same
   Black-Scholes limit. The lattice criterion is therefore "same convergence
   order against the analytic oracle", not "agree with each other to 1e-12".
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import quantrisk
from quantrisk.experiments.metadata import (
    environment,
    repo_relative,
    sha256_file,
    utc_timestamp,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "quantlib" / "results"

#: Maturities are given in days so both engines see the same year fraction.
MATURITY_DAYS = (7, 30, 91, 182, 365, 730, 1825)
SPOT = 100.0
STRIKES = (60.0, 80.0, 90.0, 95.0, 99.0, 100.0, 101.0, 105.0, 110.0, 120.0, 140.0)
VOLATILITIES = (0.05, 0.20, 0.50, 1.00)
RATES = (0.0, 0.05)
DIVIDEND_YIELDS = (0.0, 0.03)
LATTICE_STEP_COUNTS = (50, 200, 800)
LATTICE_STRIKES = (90.0, 100.0, 110.0)
GREEKS = ("delta", "gamma", "vega", "theta", "rho")


def import_quantlib():  # noqa: ANN201
    try:
        import QuantLib as ql  # noqa: PLC0415
    except ImportError as error:
        print(f"QuantLib is required for this benchmark: {error}", file=sys.stderr)
        raise SystemExit(2) from error
    return ql


class QuantLibReference:
    """Builds the oracle side of one market scenario."""

    def __init__(self, ql_module) -> None:  # noqa: ANN001
        self.ql = ql_module
        ql_module.Settings.instance().evaluationDate = ql_module.Date(1, 1, 2024)
        self.day_counter = ql_module.Actual365Fixed()

    @property
    def evaluation_date(self):  # noqa: ANN201
        return self.ql.Settings.instance().evaluationDate

    def process(self, rate: float, dividend_yield: float, volatility: float):  # noqa: ANN201
        ql = self.ql
        return ql.GeneralizedBlackScholesProcess(
            ql.QuoteHandle(ql.SimpleQuote(SPOT)),
            ql.YieldTermStructureHandle(
                ql.FlatForward(self.evaluation_date, dividend_yield, self.day_counter)
            ),
            ql.YieldTermStructureHandle(
                ql.FlatForward(self.evaluation_date, rate, self.day_counter)
            ),
            ql.BlackVolTermStructureHandle(
                ql.BlackConstantVol(
                    self.evaluation_date, ql.NullCalendar(), volatility, self.day_counter
                )
            ),
        )

    def expiry(self, maturity_days: int):  # noqa: ANN201
        ql = self.ql
        return self.evaluation_date + ql.Period(maturity_days, ql.Days)

    def _european(self, process, expiry, is_call: bool, strike: float):  # noqa: ANN001, ANN202
        ql = self.ql
        option = ql.VanillaOption(
            ql.PlainVanillaPayoff(ql.Option.Call if is_call else ql.Option.Put, strike),
            ql.EuropeanExercise(expiry),
        )
        option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
        return option

    def european_price(self, process, expiry, is_call: bool, strike: float) -> float:  # noqa: ANN001
        return float(self._european(process, expiry, is_call, strike).NPV())

    def european_greeks(self, process, expiry, is_call: bool, strike: float) -> dict[str, float]:  # noqa: ANN001
        option = self._european(process, expiry, is_call, strike)
        return {greek: float(getattr(option, greek)()) for greek in GREEKS}

    def lattice_price(
        self,
        process,
        expiry,
        is_call: bool,
        strike: float,
        steps: int,
        american: bool,  # noqa: ANN001
    ) -> float:
        ql = self.ql
        exercise = (
            ql.AmericanExercise(ql.Date(1, 1, 2000), expiry)
            if american
            else ql.EuropeanExercise(expiry)
        )
        option = ql.VanillaOption(
            ql.PlainVanillaPayoff(ql.Option.Call if is_call else ql.Option.Put, strike),
            exercise,
        )
        option.setPricingEngine(ql.BinomialVanillaEngine(process, "crr", steps))
        return float(option.NPV())


def sci(value: float) -> str:
    """Full precision for values, exponential notation for errors."""
    return f"{value:.15g}"


def err(value: float) -> str:
    return f"{value:.6e}"


#: A deep out-of-the-money option can legitimately be worth 1e-9; a relative
#: error against such a reference is noise, not signal. The summary reports the
#: absolute error always and the relative error only for rows whose reference
#: value clears these notionals.
PRICE_FLOOR = 1.0e-6 * SPOT
GREEK_FLOOR = 1.0e-6


def relative(actual: float, reference: float) -> float:
    return abs(actual - reference) / max(abs(reference), 1.0e-12)


class Worst:
    """Running maximum of absolute and (floor-gated) relative deviations."""

    def __init__(self) -> None:
        self.abs: dict[str, float] = {}
        self.rel: dict[str, float] = {}

    def record(self, key: str, actual: float, reference: float, floor: float) -> None:
        absolute = abs(actual - reference)
        self.abs[key] = max(self.abs.get(key, 0.0), absolute)
        if abs(reference) >= floor:
            self.rel[key] = max(self.rel.get(key, 0.0), absolute / abs(reference))

    def record_lattice(
        self,
        *,
        steps: int,
        ours: float,
        oracle: float,
        analytic: float,
        sigma_root_dt: float,
    ) -> None:
        """Bucket the lattice comparison where it is meaningful.

        A coarse lattice over a year of 100 % volatility (sigma*sqrt(dt) ~ 1.4)
        is a different discretisation of the same SDE in a regime where neither
        implementation claims accuracy, so the gap is reported per step count
        and per regime instead of one alarming maximum.
        """
        gap = abs(ours - oracle)
        self.abs[f"lattice[steps={steps}]"] = max(self.abs.get(f"lattice[steps={steps}]", 0.0), gap)
        if sigma_root_dt <= 0.25:
            self.abs["lattice[sigma*sqrt(dt)<=0.25]"] = max(
                self.abs.get("lattice[sigma*sqrt(dt)<=0.25]", 0.0), gap
            )
        ours_error = abs(ours - analytic)
        oracle_error = abs(oracle - analytic)
        if oracle_error > 1.0e-9:
            ratio = ours_error / oracle_error
            self.rel["lattice_error_ratio_vs_analytic"] = max(
                self.rel.get("lattice_error_ratio_vs_analytic", 0.0), ratio
            )
            self.rel.setdefault("lattice_error_ratio_minimum_vs_analytic", 1.0)
            self.rel["lattice_error_ratio_minimum_vs_analytic"] = min(
                self.rel["lattice_error_ratio_minimum_vs_analytic"], ratio
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="small grid, used by the smoke test")
    parser.add_argument("--out", type=Path, default=None)
    arguments = parser.parse_args()

    oracle = QuantLibReference(import_quantlib())

    maturities = (365,) if arguments.quick else MATURITY_DAYS
    strikes = (90.0, 100.0, 110.0) if arguments.quick else STRIKES
    volatilities = (0.20,) if arguments.quick else VOLATILITIES
    rates = (0.05,) if arguments.quick else RATES
    dividends = (0.0,) if arguments.quick else DIVIDEND_YIELDS
    step_counts = (200,) if arguments.quick else LATTICE_STEP_COUNTS

    rows: list[dict[str, object]] = []
    worst = Worst()

    for maturity_days in maturities:
        maturity = maturity_days / 365.0
        for rate in rates:
            for dividend_yield in dividends:
                for volatility in volatilities:
                    process = oracle.process(rate, dividend_yield, volatility)
                    expiry = oracle.expiry(maturity_days)
                    market = quantrisk.pricing.MarketParams(
                        spot=SPOT,
                        rate=rate,
                        dividend_yield=dividend_yield,
                        volatility=volatility,
                        maturity=maturity,
                    )
                    base = {
                        "spot": SPOT,
                        "rate": rate,
                        "dividend_yield": dividend_yield,
                        "volatility": volatility,
                        "maturity_days": maturity_days,
                        "maturity_years": f"{maturity:.12f}",
                    }

                    for strike in strikes:
                        for is_call, type_label in ((True, "call"), (False, "put")):
                            option = quantrisk.pricing.EuropeanOption(
                                quantrisk.pricing.OptionType.CALL
                                if is_call
                                else quantrisk.pricing.OptionType.PUT,
                                strike,
                            )
                            ours = quantrisk.pricing.black_scholes(option, market)
                            reference = oracle.european_price(process, expiry, is_call, strike)
                            error = relative(ours.price, reference)
                            worst.record("black_scholes_price", ours.price, reference, PRICE_FLOOR)
                            rows.append(
                                {
                                    **base,
                                    "model": f"black_scholes_{type_label}",
                                    "strike": strike,
                                    "our_price": f"{ours.price:.15g}",
                                    "quantlib_price": f"{reference:.15g}",
                                    "absolute_error": f"{abs(ours.price - reference):.6e}",
                                    "relative_error": f"{error:.6e}",
                                    "our_d1": f"{ours.d1:.15g}",
                                    "our_d2": f"{ours.d2:.15g}",
                                    "note": ours.note,
                                }
                            )

                            analytic = quantrisk.pricing.black_scholes_greeks(option, market)
                            numeric = quantrisk.pricing.finite_difference_greeks(option, market)
                            reference_greeks = oracle.european_greeks(
                                process, expiry, is_call, strike
                            )
                            for greek in GREEKS:
                                ours_value = getattr(analytic, greek)
                                reference_value = reference_greeks[greek]
                                error = relative(ours_value, reference_value)
                                worst.record(
                                    f"greek_{greek}",
                                    ours_value,
                                    reference_value,
                                    GREEK_FLOOR,
                                )
                                rows.append(
                                    {
                                        **base,
                                        "model": f"greek_{greek}_{type_label}",
                                        "strike": strike,
                                        "our_price": sci(ours_value),
                                        "quantlib_price": sci(reference_value),
                                        "absolute_error": err(abs(ours_value - reference_value)),
                                        "relative_error": err(error),
                                        "fd_value": sci(getattr(numeric, greek)),
                                        "note": "units identical (measured, see module docstring)",
                                    }
                                )

                    for steps in step_counts:
                        for strike in LATTICE_STRIKES:
                            for american, style_label in (
                                (False, "european"),
                                (True, "american"),
                            ):
                                for is_call, type_label in ((True, "call"), (False, "put")):
                                    option = quantrisk.pricing.EuropeanOption(
                                        quantrisk.pricing.OptionType.CALL
                                        if is_call
                                        else quantrisk.pricing.OptionType.PUT,
                                        strike,
                                    )
                                    style = (
                                        quantrisk.pricing.ExerciseStyle.AMERICAN
                                        if american
                                        else quantrisk.pricing.ExerciseStyle.EUROPEAN
                                    )
                                    lattice = quantrisk.pricing.crr_binomial(
                                        option, market, style, steps
                                    )
                                    analytic_price = quantrisk.pricing.black_scholes(
                                        option, market
                                    ).price
                                    reference_lattice = oracle.lattice_price(
                                        process,
                                        oracle.expiry(maturity_days),
                                        is_call,
                                        strike,
                                        steps,
                                        american,
                                    )
                                    mutual = relative(lattice.price, reference_lattice)
                                    worst.record(
                                        f"lattice_{style_label}_{type_label}",
                                        lattice.price,
                                        reference_lattice,
                                        PRICE_FLOOR,
                                    )
                                    if not american:
                                        worst.record(
                                            "lattice_vs_analytic_oracle",
                                            analytic_price,
                                            reference_lattice,
                                            PRICE_FLOOR,
                                        )
                                        worst.record_lattice(
                                            steps=steps,
                                            ours=float(lattice.price),
                                            oracle=float(reference_lattice),
                                            analytic=float(analytic_price),
                                            sigma_root_dt=volatility * math.sqrt(maturity / steps),
                                        )
                                    default_note = (
                                        "textbook CRR (u*d==1) vs QuantLib's "
                                        "drift-corrected binomial"
                                    )
                                    rows.append(
                                        {
                                            **base,
                                            "model": f"crr_{style_label}_{type_label}",
                                            "strike": strike,
                                            "steps": steps,
                                            "our_price": sci(lattice.price),
                                            "quantlib_price": sci(reference_lattice),
                                            "absolute_error": err(
                                                abs(lattice.price - reference_lattice)
                                            ),
                                            "relative_error": err(mutual),
                                            "our_analytic_price": sci(analytic_price),
                                            "lattice_vs_analytic": err(
                                                relative(lattice.price, analytic_price)
                                            ),
                                            "oracle_vs_analytic": err(
                                                relative(reference_lattice, analytic_price)
                                            ),
                                            "our_up_times_down": sci(lattice.up * lattice.down),
                                            "our_up_probability": sci(
                                                lattice.risk_neutral_up_probability
                                            ),
                                            "note": lattice.note or default_note,
                                        }
                                    )

    output_dir = arguments.out or OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "pricing_vs_quantlib.csv"
    field_names = sorted({key for row in rows for key in row})
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "artifact": "benchmarks/quantlib/pricing_validation.py",
        "command": " ".join([sys.argv[0], *sys.argv[1:]]),
        "generated_at_utc": utc_timestamp(),
        "environment": environment(),
        "quantlib_version": oracle.ql.__version__,
        "oracle_configuration": {
            "day_counter": "Actual365Fixed",
            "european_engine": "AnalyticEuropeanEngine",
            "lattice_engine": 'BinomialVanillaEngine(process, "crr", N)',
            "american_exercise_window": "Date(1,1,2000) .. expiry (whole life)",
        },
        "conventions_measured_not_assumed": {
            "vega_rho": "per unit, not per 1 percentage point: agreement ~1e-15 once measured",
            "theta": "per calendar year in both engines",
            "lattice": "O(1/N) convention difference between textbook CRR and QuantLib's binomial",
        },
        "rows": len(rows),
        "price_floor": PRICE_FLOOR,
        "greek_floor": GREEK_FLOOR,
        "worst_absolute_error": dict(sorted(worst.abs.items())),
        "worst_relative_error_above_floor": dict(sorted(worst.rel.items())),
        "csv": repo_relative(csv_path),
        "csv_sha256": sha256_file(csv_path),
    }
    json_path = output_dir / "pricing_vs_quantlib.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "worst_absolute_error": summary["worst_absolute_error"],
                "worst_relative_error_above_floor": summary["worst_relative_error_above_floor"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    print(f"wrote {csv_path} ({len(rows)} rows) and {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
