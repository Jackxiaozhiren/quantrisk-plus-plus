#!/usr/bin/env python3
"""Phase 3 experiment: measured variance reduction, on identical seeds.

    uv run python experiments/variance_reduction/run.py

Plain Monte Carlo, antithetic variates and a control variate are run on the same
market and the same seed family, and three things are reported per method:

* variance of the estimator's independent unit (single path vs antithetic pair
  mean), so the comparison is not smuggled through differing unit counts;
* the effective sample size `paths / (SE^2)` ratio relative to plain Monte
  Carlo, which folds the pairing cost in;
* realised mean-square error against the analytic price over many seeds, which
  is the number that actually matters and cannot be inflated by an optimistic
  in-sample control-variate variance.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import quantrisk
from quantrisk.experiments.metadata import environment, repo_relative, sha256_file, utc_timestamp
from quantrisk.plotting import line_plot

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = Path(__file__).resolve().parent / "results"

VR = quantrisk.monte_carlo.VarianceReduction
METHODS = {
    "plain": VR.NONE,
    "antithetic": VR.ANTITHETIC,
    "control_variate": VR.CONTROL_VARIATE,
}
PATH_COUNTS = [1_000, 10_000, 100_000]
SEEDS = 40
SCENARIOS = {
    "atm_call": (quantrisk.pricing.OptionType.CALL, 100.0, 0.25, 1.0, 0.02),
    "atm_put": (quantrisk.pricing.OptionType.PUT, 100.0, 0.25, 1.0, 0.02),
    "otm_call_short": (quantrisk.pricing.OptionType.CALL, 115.0, 0.30, 0.25, 0.0),
    "itm_call_long": (quantrisk.pricing.OptionType.CALL, 70.0, 0.40, 3.0, 0.03),
}


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    field_names = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    realised: list[dict[str, object]] = []

    for name, (option_type, strike, volatility, maturity, dividend) in SCENARIOS.items():
        market = quantrisk.pricing.MarketParams(
            spot=100.0,
            rate=0.05,
            dividend_yield=dividend,
            volatility=volatility,
            maturity=maturity,
        )
        option = quantrisk.pricing.EuropeanOption(option_type, strike)
        reference = quantrisk.pricing.black_scholes(option, market).price

        for paths in PATH_COUNTS:
            per_method: dict[str, list[float]] = {label: [] for label in METHODS}
            for label, method in METHODS.items():
                se_values = []
                variance_values = []
                units_values = []
                runtimes = []
                for seed in range(SEEDS):
                    engine = quantrisk.monte_carlo.MonteCarloEngine(50_000 + seed)
                    result = engine.price_european(option, market, paths, method)
                    se_values.append(result.standard_error)
                    variance_values.append(result.sample_variance)
                    units_values.append(result.iid_units)
                    runtimes.append(result.runtime_seconds)
                    per_method[label].append(result.price - reference)

                se_array = np.asarray(se_values)
                variance_array = np.asarray(variance_values)
                plain_key = f"{name}|{paths}|plain"
                rows.append(
                    {
                        "scenario": name,
                        "paths": paths,
                        "method": label,
                        "mean_standard_error": f"{float(se_array.mean()):.6e}",
                        "mean_sample_variance_per_unit": f"{float(variance_array.mean()):.6e}",
                        "mean_iid_units": f"{float(np.mean(units_values)):.1f}",
                        "mean_runtime_seconds": f"{float(np.mean(runtimes)):.9f}",
                        "seconds_per_path": f"{float(np.mean(runtimes)) / paths:.3e}",
                        "analytic_price": f"{reference:.12g}",
                    }
                )
                del plain_key

            for label in METHODS:
                errors = np.asarray(per_method[label])
                plain_errors = np.asarray(per_method["plain"])
                mse = float(np.mean(errors**2))
                plain_mse = float(np.mean(plain_errors**2))
                realised.append(
                    {
                        "scenario": name,
                        "paths": paths,
                        "method": label,
                        "mean_signed_error": f"{float(errors.mean()):.6e}",
                        "root_mean_square_error": f"{math.sqrt(mse):.6e}",
                        "mse_reduction_vs_plain": (f"{plain_mse / mse:.4f}" if mse > 0 else "inf"),
                        "plain_root_mean_square_error": f"{math.sqrt(plain_mse):.6e}",
                    }
                )

    variance_path = RESULTS / "variance_by_method.csv"
    realised_path = RESULTS / "realised_error.csv"
    write_csv(variance_path, rows)
    write_csv(realised_path, realised)

    atm = [row for row in rows if row["scenario"] == "atm_call"]
    xs = [float(row["paths"]) for row in atm if row["method"] == "plain"]
    figure = line_plot(
        xs,
        {
            label: [float(row["mean_standard_error"]) for row in atm if row["method"] == label]
            for label in METHODS
        },
        title="ATM call: reported standard error by variance-reduction method",
        xlabel="paths N",
        ylabel="standard error",
        path=RESULTS / "standard_error_by_method.png",
        log_x=True,
    )

    reductions = {
        f"{row['scenario']}|{int(row['paths'])}|{row['method']}": float(
            row["mse_reduction_vs_plain"]
        )
        for row in realised
    }
    worst_reduction = min(reductions.values())
    summary = {
        "artifact": "experiments/variance_reduction/run.py",
        "generated_at_utc": utc_timestamp(),
        "command": f"uv run python {Path(sys.argv[0]).name}",
        "environment": environment(),
        "seeds": SEEDS,
        "path_counts": PATH_COUNTS,
        "scenarios": list(SCENARIOS),
        "rows": len(rows),
        "realised_rows": len(realised),
        "mse_reduction_vs_plain": dict(sorted(reductions.items())),
        "worst_mse_reduction_vs_plain": worst_reduction,
        "reading": (
            "mse_reduction_vs_plain > 1 means the method beat plain Monte Carlo on "
            "out-of-sample mean squared error across the seed ensemble, which is the "
            "claim worth making; the in-sample control-variate variance alone would "
            "overstate it because beta is fitted on the same sample."
        ),
        "caveat": (
            "Antithetic reporting divides by pair count, so its standard error is per "
            "pair; the comparison here is on realised MSE at equal path budget."
        ),
        "artifacts": {
            "csv": [repo_relative(p) for p in (variance_path, realised_path)],
            "figures": [repo_relative(figure)],
            "sha256": {
                repo_relative(p): sha256_file(p) for p in (variance_path, realised_path, figure)
            },
        },
    }
    json_path = RESULTS / "summary.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"mse_reduction_vs_plain": summary["mse_reduction_vs_plain"], "worst": worst_reduction},
            indent=2,
            sort_keys=True,
        )
    )
    print(f"wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
