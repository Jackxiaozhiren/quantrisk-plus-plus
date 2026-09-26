#!/usr/bin/env python3
"""Phase 5 experiment: are the risk estimators and the coverage tests valid?

    uv run python experiments/var_backtesting/run.py

Three questions, each answered with a measured number rather than a claim.

A. **Estimators.** Historical, Gaussian and Monte Carlo VaR/ES run on samples
   whose population value is known in closed form, at several sizes and
   confidence levels, for Gaussian and Student-t(3) returns. Reported: bias,
   Monte Carlo error, and the realised out-of-sample violation rate of a VaR
   calibrated on a separate long block. The t(3) rows are the honest failure
   case of the Gaussian estimator and are reported as such.

B. **Size, power and discrimination of the coverage tests.** Under a correctly
   calibrated VaR the violation indicator is i.i.d. Bernoulli(1 - alpha), so the
   p-values of the Kupiec and Christoffersen tests must be uniform on [0, 1] and
   their 5 % rejection rate must be near 5 %. Three arms separate the tests from
   each other: an under-set level (both must reject), and a *clustered* violation
   process with the correct unconditional rate (Kupiec must accept, the
   independence test must reject). A fourth arm traces power against history
   length.

C. **Bootstrap intervals.** Coverage of the 90 % percentile interval for the
   true unconditional VaR, iid design versus moving-block design, on iid and on
   volatility-clustered returns. The table exists to show the difference, not to
   flatter either method.

SciPy is used only as a reference (population quantiles, the KS test, the exact
binomial interval). The library never imports it; this script needs it and fails
loudly without it, because it is the evidence generator rather than the engine.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import quantrisk
import scipy.stats
from quantrisk.experiments.metadata import (
    artifact_manifest,
    environment,
    package_versions,
    repo_relative,
    utc_timestamp,
)
from quantrisk.plotting import line_plot

RESULTS = Path(__file__).resolve().parent / "results"

SIGMA = 0.02
T_DF = 3.0
CONFIDENCE_LEVELS = (0.95, 0.99)
SAMPLE_SIZES = (250, 1_000, 10_000)
ESTIMATOR_REPLICATIONS = 400
CALIBRATION_BLOCK = 10_000
OUT_OF_SAMPLE = 20_000
CALIBRATION_REPLICATIONS = 200

BACKTEST_REPLICATIONS = 2_000
BACKTEST_LENGTH = 250
POWER_LENGTHS = (250, 500, 1_000, 2_500)
POWER_REPLICATIONS = 500
NOMINAL_RATE = 0.05

BOOTSTRAP_REPLICATIONS = 400
BOOTSTRAP_SAMPLE = 500
BOOTSTRAP_DRAWS = 1_500
BOOTSTRAP_INTERVAL = 0.90
BOOTSTRAP_TRUTH_BLOCK = 2_000_000

LEVEL = 0.95


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    field_names = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)


def simulate(distribution: str, rng: np.random.Generator, size: int) -> np.ndarray:
    """Returns with standard deviation `SIGMA` under either law.

    The t(3) scale is chosen so both laws have the same volatility: the arms then
    differ only in tail shape, which is the thing being tested.
    """
    if distribution == "gaussian":
        return rng.normal(0.0, SIGMA, size)
    scale = SIGMA / math.sqrt(T_DF / (T_DF - 2.0))
    return rng.standard_t(T_DF, size) * scale


def clustered_returns(rng: np.random.Generator, size: int) -> np.ndarray:
    """GARCH(1,1): constant unconditional variance, extremes that arrive in runs.

    omega is set so the unconditional standard deviation equals SIGMA: the two
    bootstrap arms then differ only in dependence, not in volatility level.
    """
    alpha, beta = 0.10, 0.85
    omega = SIGMA**2 * (1.0 - alpha - beta)
    variance = omega / (1.0 - alpha - beta)
    shocks = rng.standard_normal(size)
    returns = np.empty(size)
    for t in range(size):
        if t:
            variance = omega + alpha * returns[t - 1] ** 2 + beta * variance
        returns[t] = math.sqrt(variance) * shocks[t]
    return returns


# --- A: estimators against a known population value ----------------------


def estimator_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for distribution in ("gaussian", "student_t3"):
        scale = SIGMA if distribution == "gaussian" else SIGMA / math.sqrt(T_DF / (T_DF - 2.0))
        for level in CONFIDENCE_LEVELS:
            # Population VaR of the loss L = -R: the alpha-quantile of -R.
            if distribution == "gaussian":
                population = float(scipy.stats.norm.ppf(level, loc=0.0, scale=scale))
            else:
                population = float(scipy.stats.t.ppf(level, T_DF, loc=0.0, scale=scale))
            for size in SAMPLE_SIZES:
                values: dict[str, list[float]] = {
                    "historical_var": [],
                    "historical_es": [],
                    "gaussian_var": [],
                    "gaussian_es": [],
                    "monte_carlo_var": [],
                }
                for replicate in range(ESTIMATOR_REPLICATIONS):
                    rng = np.random.default_rng(7_000 + replicate)
                    sample = simulate(distribution, rng, size)
                    values["historical_var"].append(
                        quantrisk.risk.historical_var(sample, level).value
                    )
                    values["historical_es"].append(
                        quantrisk.risk.historical_es(sample, level).value
                    )
                    values["gaussian_var"].append(quantrisk.risk.gaussian_var(sample, level).value)
                    values["gaussian_es"].append(quantrisk.risk.gaussian_es(sample, level).value)
                    values["monte_carlo_var"].append(
                        quantrisk.risk.monte_carlo_var(sample, level).value
                    )
                for estimator, samples in values.items():
                    array = np.asarray(samples)
                    rows.append(
                        {
                            "block": "A_estimator",
                            "distribution": distribution,
                            "confidence_level": level,
                            "sample_size": size,
                            "estimator": estimator,
                            "population_value": population,
                            "mean_estimate": float(array.mean()),
                            "bias": float(array.mean() - population),
                            "relative_bias": float((array.mean() - population) / population),
                            "mc_standard_error": float(array.std(ddof=1) / math.sqrt(len(array))),
                            "replications": len(array),
                        }
                    )
            # Realised out-of-sample violation rate of a VaR calibrated on a
            # separate block: the number a risk manager actually reads. Averaged
            # over independent calibration blocks, because one block's sigma-hat
            # is itself a draw and a single number would be a fluke.
            for estimator, function in (
                ("historical_var", quantrisk.risk.historical_var),
                ("gaussian_var", quantrisk.risk.gaussian_var),
            ):
                rates: list[float] = []
                levels: list[float] = []
                for replicate in range(CALIBRATION_REPLICATIONS):
                    rng = np.random.default_rng(99_000 + replicate)
                    training = simulate(distribution, rng, CALIBRATION_BLOCK)
                    test = simulate(distribution, rng, OUT_OF_SAMPLE)
                    var_level = function(training, level).value
                    levels.append(var_level)
                    rates.append(float(np.sum(-test > var_level)) / OUT_OF_SAMPLE)
                rates_array = np.asarray(rates)
                rows.append(
                    {
                        "block": "A_out_of_sample",
                        "distribution": distribution,
                        "confidence_level": level,
                        "sample_size": CALIBRATION_BLOCK,
                        "estimator": f"{estimator}_realised",
                        "population_value": population,
                        "mean_estimate": float(np.mean(levels)),
                        "nominal_violation_rate": 1.0 - level,
                        "realised_violation_rate": float(rates_array.mean()),
                        "realised_rate_min": float(rates_array.min()),
                        "realised_rate_max": float(rates_array.max()),
                        "realised_rate_standard_error": float(
                            rates_array.std(ddof=1) / math.sqrt(len(rates_array))
                        ),
                        "replications": len(rates_array),
                        "test_observations_each": OUT_OF_SAMPLE,
                    }
                )
    return rows


# --- B: size, power and discrimination of the coverage tests -------------


def markov_flags(
    rng: np.random.Generator, length: int, stationary: float, persistence: float
) -> np.ndarray:
    """Bernoulli series with the given marginal rate and P(violate | violated)."""
    entry = stationary * (1.0 - persistence) / (1.0 - stationary)
    flags = np.empty(length, dtype=int)
    current = int(rng.random() < stationary)
    flags[0] = current
    for t in range(1, length):
        current = int(rng.random() < (persistence if current else entry))
        flags[t] = current
    return flags


def returns_for_flags(flags: np.ndarray) -> list[float]:
    """A return series whose loss beats the fixed 0.02 level exactly when flagged."""
    return [(-0.05 if flag else 0.01) for flag in flags]


def calibration_summary(p_values: np.ndarray) -> dict[str, Any]:
    """How often each test rejects at several nominal levels, with exact intervals.

    A continuous statistic that is correctly specified has uniform p-values, so
    the rejection rate should equal the nominal level at every cutoff. The KS
    column is kept as a single-number deviation measure, but it is *not* the
    verdict: the Kupiec and Christoffersen statistics are functions of integer
    violation counts, so their p-values are step distributions that cannot be
    uniform in the continuous sense however well the test is calibrated.
    """
    array = np.sort(np.asarray(p_values))
    summary: dict[str, Any] = {
        "replications": len(array),
        "mean_p_value": float(np.mean(array)),
        "ks_statistic": float(scipy.stats.kstest(array, "uniform").statistic),
    }
    for cutoff in (0.01, 0.05, 0.10):
        rejected = int(np.sum(array < cutoff))
        interval = scipy.stats.binomtest(rejected, len(array)).proportion_ci(
            confidence_level=0.95, method="exact"
        )
        summary[f"reject_rate_at_{cutoff:g}"] = rejected / len(array)
        summary[f"reject_rate_at_{cutoff:g}_ci"] = f"{interval.low:.6f}-{interval.high:.6f}"
    return summary


ARMS = {
    "calibrated_iid": {"kind": "iid", "rate": NOMINAL_RATE},
    "over_calibrated_iid": {"kind": "iid", "rate": 0.02},
    "under_set_vaR": {"kind": "iid", "rate": 0.12},
    "clustered_right_marginal": {
        "kind": "markov",
        "rate": NOMINAL_RATE,
        "persistence": 0.25,
    },
}
TESTS = ("kupiec", "independence", "conditional")


def coverage_results(flags: np.ndarray) -> dict[str, Any]:
    series = quantrisk.risk.flag_violations(returns_for_flags(flags), 0.02)
    return {
        "kupiec": quantrisk.risk.kupiec_pof_test(series, LEVEL),
        "independence": quantrisk.risk.christoffersen_independence_test(series),
        "conditional": quantrisk.risk.christoffersen_conditional_coverage_test(series, LEVEL),
    }


def backtest_rows() -> tuple[list[dict[str, Any]], dict[str, np.ndarray]]:
    rows: list[dict[str, Any]] = []
    ecdf: dict[str, np.ndarray] = {}

    for arm_name, spec in ARMS.items():
        collected: dict[str, list[float]] = {name: [] for name in TESTS}
        skipped = dict.fromkeys(TESTS, 0)
        for replicate in range(BACKTEST_REPLICATIONS):
            rng = np.random.default_rng(100_000 + replicate)
            if spec["kind"] == "iid":
                flags = (rng.random(BACKTEST_LENGTH) < spec["rate"]).astype(int)
            else:
                flags = markov_flags(rng, BACKTEST_LENGTH, spec["rate"], spec["persistence"])
            results = coverage_results(flags)
            for name in TESTS:
                result = results[name]
                if result.degenerate or not math.isfinite(result.p_value):
                    skipped[name] += 1
                    continue
                collected[name].append(result.p_value)
        for name in TESTS:
            array = np.asarray(collected[name])
            if len(array) == 0:
                continue
            row: dict[str, Any] = {
                "block": "B_size_power",
                "arm": arm_name,
                "test": name,
                "history_length": BACKTEST_LENGTH,
                "true_violation_rate": spec["rate"],
                "degrees_of_freedom": 2 if name == "conditional" else 1,
                "skipped_degenerate": skipped[name],
                **calibration_summary(array),
            }
            rows.append(row)
            if arm_name == "calibrated_iid":
                ecdf[name] = np.sort(array)

    for length in POWER_LENGTHS:
        for name in ("kupiec", "independence"):
            rejected: list[int] = []
            for replicate in range(POWER_REPLICATIONS):
                rng = np.random.default_rng(500_000 + replicate)
                flags = (rng.random(length) < ARMS["under_set_vaR"]["rate"]).astype(int)
                result = coverage_results(flags)[name]
                rejected.append(int(not result.degenerate and result.rejected_at_5_percent))
            rows.append(
                {
                    "block": "B_specificity_and_power",
                    "arm": "under_set_vaR",
                    "test": name,
                    "history_length": length,
                    "true_violation_rate": ARMS["under_set_vaR"]["rate"],
                    "degrees_of_freedom": 1,
                    "skipped_degenerate": 0,
                    "replications": len(rejected),
                    "reject_rate_at_0.05": float(np.mean(rejected)),
                }
            )
    return rows, ecdf


# --- C: bootstrap coverage ------------------------------------------------


def bootstrap_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    designs = {
        "iid_returns": lambda rng, size: simulate("gaussian", rng, size),
        "clustered_returns": clustered_returns,
    }
    for design_name, generator in designs.items():
        # Target: the unconditional 95 % VaR of the process, from a very long
        # simulation. An interval for a *conditional*, daily re-estimated VaR
        # would need a different definition of "truth" than this one.
        truth = quantrisk.risk.historical_var(
            generator(np.random.default_rng(4_000_000), BOOTSTRAP_TRUTH_BLOCK), LEVEL
        ).value
        for kind_name, kind in (
            ("iid", quantrisk.risk.BootstrapKind.IID),
            ("moving_block", quantrisk.risk.BootstrapKind.MOVING_BLOCK),
        ):
            covered = 0
            widths: list[float] = []
            for replicate in range(BOOTSTRAP_REPLICATIONS):
                sample = generator(np.random.default_rng(200_000 + replicate), BOOTSTRAP_SAMPLE)
                interval = quantrisk.risk.bootstrap_var(
                    sample,
                    LEVEL,
                    BOOTSTRAP_DRAWS,
                    BOOTSTRAP_INTERVAL,
                    kind,
                    0,
                    31_000 + replicate,
                )
                widths.append(interval.ci_high - interval.ci_low)
                covered += int(interval.ci_low <= truth <= interval.ci_high)
            rate = covered / BOOTSTRAP_REPLICATIONS
            interval = scipy.stats.binomtest(covered, BOOTSTRAP_REPLICATIONS).proportion_ci(
                confidence_level=0.95, method="exact"
            )
            rows.append(
                {
                    "block": "C_bootstrap_coverage",
                    "data": design_name,
                    "bootstrap_design": kind_name,
                    "block_length": (
                        quantrisk.risk.suggested_block_length(BOOTSTRAP_SAMPLE)
                        if kind_name == "moving_block"
                        else 0
                    ),
                    "sample_size": BOOTSTRAP_SAMPLE,
                    "bootstrap_draws": BOOTSTRAP_DRAWS,
                    "interval_level": BOOTSTRAP_INTERVAL,
                    "replications": BOOTSTRAP_REPLICATIONS,
                    "true_unconditional_var": truth,
                    "coverage": rate,
                    "coverage_ci_low": float(interval.low),
                    "coverage_ci_high": float(interval.high),
                    "mean_interval_width": float(np.mean(widths)),
                }
            )
    return rows


# --- figures --------------------------------------------------------------


def convergence_figure(rows: list[dict[str, Any]]) -> Path | None:
    selected = [
        row
        for row in rows
        if row["block"] == "A_estimator"
        and row["distribution"] == "student_t3"
        and row["confidence_level"] == 0.99
        and row["estimator"] in {"historical_var", "gaussian_var"}
    ]
    if not selected:
        return None
    xs = [row["sample_size"] for row in selected if row["estimator"] == "historical_var"]
    series = {
        estimator: [row["mean_estimate"] for row in selected if row["estimator"] == estimator]
        for estimator in ("historical_var", "gaussian_var")
    }
    population = selected[0]["population_value"]
    series["population 99 % VaR"] = [population] * len(xs)
    return line_plot(
        xs,
        series,
        title="t(3) returns, 99 % VaR: estimator mean against sample size",
        xlabel="sample size n",
        ylabel="VaR estimate",
        path=str(RESULTS / "estimator_convergence.png"),
        log_x=True,
        annotations={"the normal fit converges to the wrong number": (0.45, 0.18)},
    )


def ecdf_figure(ecdf: dict[str, np.ndarray]) -> Path | None:
    if not ecdf:
        return None
    grid = np.linspace(0.0, 1.0, 101)
    series = {
        f"{name} ECDF": [float(np.searchsorted(curve, x, side="right") / len(curve)) for x in grid]
        for name, curve in ecdf.items()
    }
    series["uniform (H0)"] = [float(x) for x in grid]
    return line_plot(
        [float(x) for x in grid],
        series,
        title="Coverage-test p-values under a correctly calibrated VaR",
        xlabel="p-value",
        ylabel="empirical CDF",
        path=str(RESULTS / "pvalue_uniformity.png"),
    )


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    estimators = estimator_rows()
    backtests, ecdf = backtest_rows()
    bootstraps = bootstrap_rows()

    outputs = [
        RESULTS / "estimator_convergence.csv",
        RESULTS / "coverage_test_size_power.csv",
        RESULTS / "bootstrap_coverage.csv",
    ]
    write_csv(outputs[0], estimators)
    write_csv(outputs[1], backtests)
    write_csv(outputs[2], bootstraps)

    figures = [path for path in (convergence_figure(estimators), ecdf_figure(ecdf)) if path]
    artifacts = outputs + figures

    def cell(block: str, **keys: Any) -> Any:
        for row in [*estimators, *backtests, *bootstraps]:
            if row.get("block") == block and all(row.get(k) == v for k, v in keys.items()):
                return row
        raise KeyError((block, keys))

    summary = {
        "phase": "5 - Market risk: VaR/ES estimators, bootstrap intervals, coverage backtests",
        "generated_utc": utc_timestamp(),
        "command": "uv run python experiments/var_backtesting/run.py",
        "purpose": (
            "Level 1/3 statistical validation of the risk layer: estimator bias and "
            "realised violation rates, size and power of the Kupiec and Christoffersen "
            "tests, and measured bootstrap coverage under dependence."
        ),
        "parameters": {
            "sigma": SIGMA,
            "student_t_df": T_DF,
            "confidence_levels": list(CONFIDENCE_LEVELS),
            "sample_sizes": list(SAMPLE_SIZES),
            "estimator_replications": ESTIMATOR_REPLICATIONS,
            "calibration_block": CALIBRATION_BLOCK,
            "out_of_sample_observations": OUT_OF_SAMPLE,
            "backtest_replications": BACKTEST_REPLICATIONS,
            "backtest_history_length": BACKTEST_LENGTH,
            "power_history_lengths": list(POWER_LENGTHS),
            "power_replications": POWER_REPLICATIONS,
            "bootstrap_replications": BOOTSTRAP_REPLICATIONS,
            "bootstrap_sample_size": BOOTSTRAP_SAMPLE,
            "bootstrap_draws": BOOTSTRAP_DRAWS,
            "bootstrap_interval_level": BOOTSTRAP_INTERVAL,
            "bootstrap_truth_block": BOOTSTRAP_TRUTH_BLOCK,
            "out_of_sample_calibration_replications": CALIBRATION_REPLICATIONS,
        },
        "generators": {
            "student_t3": (
                "standard_t(df=3) scaled so the unconditional standard deviation equals "
                "sigma, matching the Gaussian arm"
            ),
            "clustered_returns": (
                "GARCH(1,1) with alpha=0.10, beta=0.85 and omega chosen so the "
                "unconditional standard deviation equals sigma; started from its "
                "unconditional variance"
            ),
            "clustered_right_marginal": (
                "two-state Markov violation chain with stationary rate 0.05 and "
                "P(violate | violated) = 0.25, so the unconditional count is on target "
                "while the timing is clustered"
            ),
        },
        "seeds": (
            "every stream is seeded explicitly (estimator 7000+r, backtest 100000+r, "
            "power 500000+r, bootstrap 200000+r with resample seed 31000+r), so reruns "
            "reproduce bit for bit"
        ),
        "oracle": {
            "tool": (
                "SciPy, live: population quantiles, KS uniformity test, exact binomial interval"
            ),
            "role": "reference only; the library never imports SciPy",
            "versions": package_versions(),
        },
        "environment": environment(),
        "headline": {
            "gaussian_95_var_bias_at_n250": cell(
                "A_estimator",
                distribution="gaussian",
                confidence_level=0.95,
                sample_size=250,
                estimator="gaussian_var",
            )["bias"],
            "t3_99_var_realised_rate_gaussian": cell(
                "A_out_of_sample",
                distribution="student_t3",
                confidence_level=0.99,
                estimator="gaussian_var_realised",
            )["realised_violation_rate"],
            "t3_99_var_realised_rate_historical": cell(
                "A_out_of_sample",
                distribution="student_t3",
                confidence_level=0.99,
                estimator="historical_var_realised",
            )["realised_violation_rate"],
            "calibrated_kupiec_reject_rate": cell(
                "B_size_power", arm="calibrated_iid", test="kupiec"
            )["reject_rate_at_0.05"],
            "calibrated_kupiec_reject_rate_at_1pct": cell(
                "B_size_power", arm="calibrated_iid", test="kupiec"
            )["reject_rate_at_0.01"],
            "calibrated_kupiec_ks_statistic": cell(
                "B_size_power", arm="calibrated_iid", test="kupiec"
            )["ks_statistic"],
            "clustered_kupiec_reject_rate": cell(
                "B_size_power", arm="clustered_right_marginal", test="kupiec"
            )["reject_rate_at_0.05"],
            "clustered_independence_reject_rate": cell(
                "B_size_power", arm="clustered_right_marginal", test="independence"
            )["reject_rate_at_0.05"],
            "under_set_reject_rate_at_n250": cell(
                "B_specificity_and_power", arm="under_set_vaR", test="kupiec", history_length=250
            )["reject_rate_at_0.05"],
            "under_set_reject_rate_at_n2500": cell(
                "B_specificity_and_power",
                arm="under_set_vaR",
                test="kupiec",
                history_length=2500,
            )["reject_rate_at_0.05"],
            "iid_design_iid_data_coverage": cell(
                "C_bootstrap_coverage", data="iid_returns", bootstrap_design="iid"
            )["coverage"],
            "iid_design_clustered_data_coverage": cell(
                "C_bootstrap_coverage", data="clustered_returns", bootstrap_design="iid"
            )["coverage"],
            "block_design_clustered_data_coverage": cell(
                "C_bootstrap_coverage", data="clustered_returns", bootstrap_design="moving_block"
            )["coverage"],
        },
        "reading": {
            "A_estimator": (
                "bias is the mean estimate minus the population value; the Monte Carlo "
                "standard error over replications says how small it has to be to mean anything."
            ),
            "A_out_of_sample": (
                "realised_violation_rate averaged over independent calibration blocks against "
                "nominal_violation_rate. Above nominal means the published VaR understated the "
                "risk. The t(3) rows are where a normal fit is expected to fail, and the "
                "min/max columns show how much a single block's sigma-hat can move the answer."
            ),
            "B_size_power": (
                "reject_rate_at_0.01/0.05/0.10 with exact binomial intervals: a correctly "
                "specified continuous statistic tracks its nominal level at every cutoff. "
                "The Kupiec and Christoffersen statistics are functions of integer violation "
                "counts, so their p-values are step distributions and the ks_statistic column "
                "measures the residual distance to uniform rather than signalling a defect. "
                "The clustered arm is the discriminator: Kupiec largely accepts a clustered "
                "model while the independence test rejects it."
            ),
            "B_specificity_and_power": (
                "for a purely unconditional error, power for Kupiec rises with history length "
                "while the independence test correctly keeps not rejecting: it is a specificity "
                "trace as much as a power curve."
            ),
            "C_bootstrap_coverage": (
                "coverage of the nominal 90 % interval with its exact binomial interval. Where "
                "the design matches the data it should reach 0.90; the shortfall of the iid "
                "design on clustered data is the documented cost of assuming serial independence."
            ),
        },
        "artifacts": artifact_manifest(artifacts),
    }
    (RESULTS / "var_backtesting_validation.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(summary["headline"], indent=2))
    print(f"wrote {len(artifacts)} artifacts to {repo_relative(RESULTS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
