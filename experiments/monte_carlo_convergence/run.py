#!/usr/bin/env python3
"""Phase 3 experiment: does Monte Carlo error really decay like 1/sqrt(N)?

    uv run python experiments/monte_carlo_convergence/run.py

Not a picture of a downward line - three quantitative claims, each with an
artifact:

1. A log-log OLS fit of |error| on N over 1e3 .. 1e6 paths, reported with its
   standard error against the theoretical slope of -0.5.
2. The *self-consistency* claim: each measured error is inside the standard
   error the estimator itself reports, i.e. |error| / SE behaves like a standard
   normal. Reported as a distribution of z-scores over independent seeds.
3. Empirical coverage of the nominal 95 % interval across seeds and path
   counts, compared with the exact Binomial(n, 0.95) band rather than a
   hand-picked window.
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
from quantrisk.plotting import line_plot, log_log_convergence_plot

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = Path(__file__).resolve().parent / "results"

PATH_COUNTS = [1_000, 3_000, 10_000, 30_000, 100_000, 300_000, 1_000_000, 3_000_000]
BASE_SEED = 42
COVERAGE_SEEDS = 200
COVERAGE_PATHS = [1_000, 10_000]
CONFIDENCE_LEVELS = (0.95, 0.99)

SCENARIOS = {
    "atm_call": (
        quantrisk.pricing.OptionType.CALL,
        100.0,
        {"spot": 100.0, "rate": 0.05, "dividend_yield": 0.02, "volatility": 0.25, "maturity": 1.0},
    ),
    "otm_put": (
        quantrisk.pricing.OptionType.PUT,
        85.0,
        {"spot": 100.0, "rate": 0.05, "dividend_yield": 0.02, "volatility": 0.25, "maturity": 0.5},
    ),
    "deep_itm_call": (
        quantrisk.pricing.OptionType.CALL,
        40.0,
        {"spot": 100.0, "rate": 0.05, "dividend_yield": 0.0, "volatility": 0.4, "maturity": 2.0},
    ),
}


def fit_log_log_slope(xs: list[float], ys: list[float]) -> tuple[float, float] | None:
    points = [
        (math.log(x), math.log(abs(y))) for x, y in zip(xs, ys, strict=True) if x > 0 and abs(y) > 0
    ]
    n = len(points)
    if n < 3:
        return None
    mean_x = sum(p[0] for p in points) / n
    mean_y = sum(p[1] for p in points) / n
    sxx = sum((x - mean_x) ** 2 for x, _ in points)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in points)
    if sxx == 0.0:
        return None
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    sse = sum((y - (intercept + slope * x)) ** 2 for x, y in points)
    if n <= 2:
        return slope, float("nan")
    return slope, math.sqrt(sse / (n - 2) / sxx)


def option_for(scenario: str):  # noqa: ANN201
    option_type, strike, parameters = SCENARIOS[scenario]
    market = quantrisk.pricing.MarketParams(**parameters)
    return quantrisk.pricing.EuropeanOption(option_type, strike), market


def convergence_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        option, market = option_for(scenario)
        reference = quantrisk.pricing.black_scholes(option, market).price
        for paths in PATH_COUNTS:
            # Fresh engine per path count with the same seed: the smaller runs
            # are then initial segments of the larger ones (nesting), which is
            # what makes the fitted slope clean instead of noisy.
            result = quantrisk.monte_carlo.MonteCarloEngine(BASE_SEED).price_european(
                option, market, paths
            )
            error = result.price - reference
            rows.append(
                {
                    "scenario": scenario,
                    "paths": paths,
                    "seed": BASE_SEED,
                    "analytic_price": f"{reference:.15g}",
                    "mc_price": f"{result.price:.15g}",
                    "standard_error": f"{result.standard_error:.6e}",
                    "absolute_error": f"{abs(error):.6e}",
                    "relative_error": f"{abs(error) / max(abs(reference), 1e-12):.6e}",
                    "error_in_standard_errors": f"{error / result.standard_error:.6f}",
                    "runtime_seconds": f"{result.runtime_seconds:.9f}",
                    "paths_per_second": f"{paths / max(result.runtime_seconds, 1e-12):.6g}",
                    "note": result.note,
                }
            )
    return rows


def z_score_rows() -> list[dict[str, object]]:
    """Distribution of error / SE over independent seeds (should be ~N(0,1))."""
    rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        option, market = option_for(scenario)
        reference = quantrisk.pricing.black_scholes(option, market).price
        for paths in (10_000, 100_000):
            scores = []
            for seed in range(200):
                result = quantrisk.monte_carlo.MonteCarloEngine(7_000_000 + seed).price_european(
                    option, market, paths
                )
                scores.append((result.price - reference) / result.standard_error)
            array = np.asarray(scores)
            within = float(np.mean(np.abs(array) <= 1.959963984540054))
            rows.append(
                {
                    "scenario": scenario,
                    "paths": paths,
                    "replications": len(scores),
                    "z_mean": f"{float(array.mean()):.6f}",
                    "z_std": f"{float(array.std(ddof=1)):.6f}",
                    "z_min": f"{float(array.min()):.6f}",
                    "z_max": f"{float(array.max()):.6f}",
                    "fraction_within_1_96": f"""{within:.6f}""",
                }
            )
    return rows


def coverage_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        option, market = option_for(scenario)
        reference = quantrisk.pricing.black_scholes(option, market).price
        for paths in COVERAGE_PATHS:
            for level in CONFIDENCE_LEVELS:
                covered = 0
                for seed in range(COVERAGE_SEEDS):
                    result = quantrisk.monte_carlo.MonteCarloEngine(900_000 + seed).price_european(
                        option,
                        market,
                        paths,
                        quantrisk.monte_carlo.VarianceReduction.NONE,
                        level,
                    )
                    if result.confidence_low <= reference <= result.confidence_high:
                        covered += 1
                lo, hi = _binomial_band(COVERAGE_SEEDS, level)
                rows.append(
                    {
                        "scenario": scenario,
                        "paths": paths,
                        "confidence_level": level,
                        "replications": COVERAGE_SEEDS,
                        "covered": covered,
                        "empirical_coverage": f"{covered / COVERAGE_SEEDS:.4f}",
                        "band_low": lo,
                        "band_high": hi,
                        "inside_band": bool(lo <= covered <= hi),
                    }
                )
    return rows


def _binomial_band(trials: int, level: float) -> tuple[int, int]:
    scipy_stats = __import__("scipy.stats", fromlist=["stats"])
    low = int(scipy_stats.binom.ppf(0.005, trials, level))
    high = int(scipy_stats.binom.ppf(0.995, trials, level))
    return low, high


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    field_names = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    convergence = convergence_rows()
    z_scores = z_score_rows()
    coverage = coverage_rows()

    convergence_path = RESULTS / "convergence.csv"
    z_path = RESULTS / "z_scores.csv"
    coverage_path = RESULTS / "coverage.csv"
    write_csv(convergence_path, convergence)
    write_csv(z_path, z_scores)
    write_csv(coverage_path, coverage)

    slopes: dict[str, dict[str, float]] = {}
    series: dict[str, list[float]] = {}
    xs_for_plot: list[float] = []
    for scenario in SCENARIOS:
        subset = [row for row in convergence if row["scenario"] == scenario]
        xs = [float(row["paths"]) for row in subset]
        errors = [float(row["absolute_error"]) for row in subset]
        fit = fit_log_log_slope(xs, errors)
        if fit is not None:
            slopes[scenario] = {
                "slope": fit[0],
                "standard_error": fit[1],
                "expected": -0.5,
                "deviations_from_theory_in_standard_errors": abs(fit[0] + 0.5) / fit[1]
                if fit[1] > 0
                else float("inf"),
            }
        positive = [(x, e) for x, e in zip(xs, errors, strict=True) if e > 0]
        if positive:
            series[scenario] = [e for _, e in positive]
            if scenario == "atm_call":
                xs_for_plot = [x for x, _ in positive]

    figures = [
        log_log_convergence_plot(
            xs_for_plot,
            series,
            title="Monte Carlo error vs paths (theoretical slope -1/2)",
            xlabel="paths N",
            ylabel="|MC price - analytic|",
            reference_slope=-0.5,
            path=RESULTS / "convergence_slope.png",
        ),
        line_plot(
            [float(row["paths"]) for row in convergence if row["scenario"] == "atm_call"],
            {
                "standard error": [
                    float(row["standard_error"])
                    for row in convergence
                    if row["scenario"] == "atm_call"
                ],
                "absolute error": [
                    float(row["absolute_error"])
                    for row in convergence
                    if row["scenario"] == "atm_call"
                ],
            },
            title="Reported SE tracks the realised error",
            xlabel="paths N",
            ylabel="currency units",
            path=RESULTS / "se_versus_error.png",
            log_x=True,
        ),
    ]

    inside = sum(1 for row in coverage if row["inside_band"])
    summary = {
        "artifact": "experiments/monte_carlo_convergence/run.py",
        "generated_at_utc": utc_timestamp(),
        "command": f"uv run python {Path(sys.argv[0]).name}",
        "environment": environment(),
        "base_seed": BASE_SEED,
        "path_counts": PATH_COUNTS,
        "scenarios": list(SCENARIOS),
        "convergence_rows": len(convergence),
        "convergence_slope_fit": slopes,
        "z_scores": z_scores,
        "coverage_rows": len(coverage),
        "coverage_intervals_inside_binomial_band": f"{inside}/{len(coverage)}",
        "coverage": coverage,
        "reading": (
            "A fitted slope of about -0.5 confirms O(1/sqrt(N)); z-scores with "
            "mean near 0 and standard deviation near 1 confirm that the reported "
            "SE is the right yardstick; coverage counts inside the exact "
            "Binomial(n, level) band confirm the interval is neither optimistic "
            "nor needlessly wide."
        ),
        "artifacts": {
            "csv": [repo_relative(p) for p in (convergence_path, z_path, coverage_path)],
            "figures": [repo_relative(p) for p in figures],
            "sha256": {
                repo_relative(p): sha256_file(p)
                for p in [convergence_path, z_path, coverage_path, *figures]
            },
        },
    }
    json_path = RESULTS / "summary.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "slopes": slopes,
                "coverage_inside_band": summary["coverage_intervals_inside_binomial_band"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    print(f"wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
