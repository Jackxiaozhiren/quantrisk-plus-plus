#!/usr/bin/env python3
"""Run every benchmark, experiment and performance measurement, then aggregate them.

    uv run python scripts/run_benchmark_suite.py            # run everything, then aggregate
    uv run python scripts/run_benchmark_suite.py --no-run   # aggregate what is already on disk
    uv run python scripts/run_benchmark_suite.py --only pricing_vs_quantlib

PROJECT_SPEC.md §Phase 10 asks for a benchmark suite covering correctness benchmarks,
statistical experiments and performance benchmarks, with results saved as JSON, CSV,
Markdown and plots, and it asks for that on a line that says "必须由脚本自动生成" — the
artifacts must come from a script, not from a person copying numbers into a table.

What this runner does and does not do:

  * It executes each member's own script as a subprocess. It never computes a financial
    or statistical result itself, so there is no second implementation here to drift from
    the first.
  * It reads the headline numbers *out of* the JSON each script already writes, by key
    path. A key that has moved or been renamed raises and fails the run, which is the
    point: an aggregation that silently dropped a metric would look exactly like an
    aggregation that passed.
  * It records no tolerance and no expected value of its own. Where a member publishes a
    figure, the figure is the member's; the summary says which artifact it came from.
  * A member whose oracle package is not installed is reported SKIPPED, not passed and
    not failed. The Markdown says so in the same column as the results, so a README
    claim backed by a skipped benchmark cannot survive review unnoticed.

Output goes to `benchmarks/suite/results/`, alongside — not inside — the members' own
result directories, so running the suite cannot overwrite the evidence it summarises.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from quantrisk.experiments.metadata import (  # noqa: E402
    environment,
    repo_relative,
    sha256_file,
)

RESULTS_DIR = ROOT / "benchmarks" / "suite" / "results"


class SuiteError(RuntimeError):
    """The suite could not be aggregated as described. Never swallowed."""


@dataclass(frozen=True)
class Member:
    """One benchmark or experiment, and where its headline numbers live.

    `headline` entries are (label, key path) pairs rather than dotted strings: several
    artifacts key their results by name and those names contain dots and pluses
    (`ranking["correlation_+0.2"]`), which a string path would split in the wrong place.
    """

    key: str
    title: str
    kind: str
    script: str
    artifact: str
    headline: tuple[tuple[str, tuple[str, ...]], ...]
    requires: tuple[str, ...] = ()
    summary: tuple[str, ...] = ()
    plot: tuple[str, ...] = ()


CORRECTNESS = "correctness_benchmark"
PERFORMANCE = "performance_benchmark"
EXPERIMENT = "statistical_experiment"

MEMBERS: tuple[Member, ...] = (
    Member(
        key="pricing_vs_quantlib",
        title="Black-Scholes, Greeks and CRR lattice vs QuantLib (18,816 rows)",
        kind=CORRECTNESS,
        script="benchmarks/quantlib/pricing_validation.py",
        artifact="benchmarks/quantlib/results/pricing_vs_quantlib.json",
        requires=("QuantLib",),
        headline=(
            (
                "worst relative price error",
                ("worst_relative_error_above_floor", "black_scholes_price"),
            ),
            ("worst relative delta error", ("worst_relative_error_above_floor", "greek_delta")),
            ("worst relative gamma error", ("worst_relative_error_above_floor", "greek_gamma")),
            ("worst relative vega error", ("worst_relative_error_above_floor", "greek_vega")),
            ("worst relative rho error", ("worst_relative_error_above_floor", "greek_rho")),
            ("worst relative theta error", ("worst_relative_error_above_floor", "greek_theta")),
            (
                "CRR 800-step gap to the analytic oracle (absolute)",
                ("worst_absolute_error", "lattice[steps=800]"),
            ),
            (
                "worst american call relative error",
                ("worst_relative_error_above_floor", "lattice_american_call"),
            ),
        ),
        plot=(
            "worst relative price error",
            "worst relative delta error",
            "worst relative gamma error",
            "worst relative vega error",
            "worst relative theta error",
            "worst relative rho error",
            "worst american call relative error",
        ),
    ),
    Member(
        key="monte_carlo_vs_analytic",
        title="Monte Carlo, antithetic and control variate vs the analytic oracle",
        kind=CORRECTNESS,
        script="benchmarks/quantlib/monte_carlo_validation.py",
        artifact="benchmarks/quantlib/results/monte_carlo_validation.json",
        requires=("QuantLib",),
        headline=(
            ("plain MC z mean", ("z_score_vs_quantlib_analytic", "plain", "mean")),
            ("plain MC z std dev", ("z_score_vs_quantlib_analytic", "plain", "std")),
            ("antithetic MC z mean", ("z_score_vs_quantlib_analytic", "antithetic", "mean")),
            ("antithetic MC z std dev", ("z_score_vs_quantlib_analytic", "antithetic", "std")),
            (
                "control-variate MC z mean",
                ("z_score_vs_quantlib_analytic", "control_variate", "mean"),
            ),
            (
                "control-variate MC z std dev",
                ("z_score_vs_quantlib_analytic", "control_variate", "std"),
            ),
        ),
        plot=(
            "plain MC z mean",
            "plain MC z std dev",
            "antithetic MC z mean",
            "antithetic MC z std dev",
            "control-variate MC z mean",
            "control-variate MC z std dev",
        ),
    ),
    Member(
        key="path_dependent_vs_quantlib",
        title="Asian and barrier options, and Heston against closed forms and QuantLib",
        kind=CORRECTNESS,
        script="benchmarks/quantlib/path_dependent_validation.py",
        artifact="benchmarks/quantlib/results/path_dependent_vs_quantlib.json",
        requires=("QuantLib",),
        headline=(
            (
                "worst geometric-Asian error",
                ("worst_relative_error", "asian_geometric_closed_form"),
            ),
            (
                "worst arithmetic-Asian error",
                ("worst_relative_error", "asian_geometric_simulated"),
            ),
            ("worst discrete-barrier error", ("worst_relative_error", "barrier_discrete")),
            (
                "worst barrier (Broadie-Glasky-Kou) error",
                ("worst_relative_error", "barrier_bgk_corrected"),
            ),
            ("worst Heston error", ("worst_relative_error", "heston_analytic")),
            (
                "worst Heston xi=0 degenerate error",
                ("worst_relative_error", "heston_degenerate"),
            ),
        ),
        plot=(
            "worst geometric-Asian error",
            "worst arithmetic-Asian error",
            "worst discrete-barrier error",
            "worst barrier (Broadie-Glasky-Kou) error",
            "worst Heston error",
            "worst Heston xi=0 degenerate error",
        ),
    ),
    Member(
        key="optimisation_vs_oracles",
        title="Mean-variance, max-Sharpe, risk parity and CVaR vs PyPortfolioOpt and cvxpy",
        kind=CORRECTNESS,
        script="benchmarks/pyportfolioopt/optimisation_validation.py",
        artifact="benchmarks/pyportfolioopt/results/optimisation_vs_oracles.json",
        requires=("pypfopt", "cvxpy"),
        headline=(
            ("problems solved", ("agreement", "problems_solved")),
            (
                "worst relative objective gap vs PyPortfolioOpt",
                ("agreement", "worst_relative_objective_gap_pypfopt"),
            ),
            (
                "worst relative objective gap vs cvxpy",
                ("agreement", "worst_relative_objective_gap_cvxpy"),
            ),
            ("worst weight difference vs cvxpy", ("agreement", "worst_weight_difference_cvxpy")),
            ("worst budget residual", ("agreement", "worst_budget_residual")),
            ("worst bound violation", ("agreement", "worst_bound_violation")),
        ),
        plot=(
            "worst relative objective gap vs cvxpy",
            "worst weight difference vs cvxpy",
        ),
    ),
    Member(
        key="mc_speed",
        title="C++ Monte Carlo throughput against NumPy and pure Python on one machine",
        kind=PERFORMANCE,
        script="benchmarks/performance/monte_carlo_speed.py",
        artifact="benchmarks/performance/results/monte_carlo_speed.json",
        headline=(
            ("speedup vs pure Python (mean)", ("speedup_vs_pure_python",)),
            ("speedup vs NumPy (mean)", ("speedup_vs_numpy",)),
            ("standard error vs analytic, C++", ("z_score_vs_analytic", "cpp")),
        ),
    ),
    Member(
        key="pricing_grid",
        title="Pricing surface, put-call parity and lattice convergence order",
        kind=EXPERIMENT,
        script="experiments/pricing_validation/run.py",
        artifact="experiments/pricing_validation/results/summary.json",
        headline=(
            ("worst put-call parity residual", ("worst_put_call_parity_residual",)),
            (
                "worst analytic-vs-finite-difference delta",
                ("worst_analytic_vs_finite_difference_delta",),
            ),
            ("CRR convergence slope, ATM call", ("crr_convergence_slope", "atm_call")),
            ("lattice rows", ("lattice_rows",)),
        ),
    ),
    Member(
        key="mc_convergence",
        title="1/sqrt(N) convergence and confidence-interval coverage of the MC engine",
        kind=EXPERIMENT,
        script="experiments/monte_carlo_convergence/run.py",
        artifact="experiments/monte_carlo_convergence/results/summary.json",
        headline=(
            (
                "coverage intervals inside the binomial band",
                ("coverage_intervals_inside_binomial_band",),
            ),
            ("fitted convergence slope, ATM call", ("convergence_slope_fit", "atm_call", "slope")),
            ("coverage rows", ("coverage_rows",)),
            ("convergence rows", ("convergence_rows",)),
        ),
    ),
    Member(
        key="variance_reduction",
        title="Antithetic and control-variate gains on out-of-sample mean squared error",
        kind=EXPERIMENT,
        script="experiments/variance_reduction/run.py",
        artifact="experiments/variance_reduction/results/summary.json",
        headline=(
            (
                "worst MSE reduction among the variance-reduced cells",
                ("worst_mse_reduction_vs_plain",),
            ),
            ("replications per cell", ("seeds",)),
        ),
    ),
    Member(
        key="var_backtesting",
        title="VaR/ES estimator bias, Kupiec and Christoffersen size and power, bootstrap coverage",
        kind=EXPERIMENT,
        script="experiments/var_backtesting/run.py",
        artifact="experiments/var_backtesting/results/var_backtesting_validation.json",
        requires=("statsmodels",),
        headline=(
            ("Kupiec reject rate, calibrated, 95%", ("headline", "calibrated_kupiec_reject_rate")),
            (
                "Kupiec reject rate on clustered data",
                ("headline", "clustered_kupiec_reject_rate"),
            ),
            ("Gaussian 95% VaR bias at n=250", ("headline", "gaussian_95_var_bias_at_n250")),
            (
                "bootstrap coverage, block design on clustered data",
                ("headline", "block_design_clustered_data_coverage"),
            ),
        ),
    ),
    Member(
        key="portfolio_estimation_cost",
        title="Rolling-origin forward variance each covariance estimator costs an optimiser",
        kind=EXPERIMENT,
        script="experiments/portfolio_optimization/run.py",
        artifact="experiments/portfolio_optimization/results/portfolio_optimisation_study.json",
        headline=(
            ("portfolios evaluated", ("data", "portfolios_evaluated")),
            ("windows solved", ("data", "windows_solved")),
            ("worst cell", ("headline", "worst_cell")),
            ("best cell", ("headline", "best_cell")),
        ),
    ),
    Member(
        key="linearisation_error_bound",
        title="Taylor remainder bound for the delta-gamma stress map, and its sign change",
        kind=EXPERIMENT,
        script="experiments/linearisation_error_bound/run.py",
        artifact="experiments/linearisation_error_bound/results/linearisation_error_bound.json",
        # No `plot` labels. This member publishes no error against an oracle, and panel A
        # of the envelope figure is labelled |our value - oracle| / |oracle|. A remainder
        # bound is not such a quantity; adding it would relabel the figure into a lie.
        headline=(
            ("all predictions held", ("headline", "all_predictions_held")),
            (
                "tightest |R|/bound away from the remainder zero",
                ("headline", "bound_tightest_ratio_away_from_the_remainder_zero"),
            ),
            ("loosest |R|/bound", ("headline", "bound_loosest_ratio")),
            ("dense shocks tested", ("headline", "dense_shocks_tested")),
            (
                "Lagrange inclusion violations, dense sweep",
                ("headline", "lagrange_inclusion_violations_dense"),
            ),
            (
                "cubic slope, widest window, down",
                ("headline", "fitted_cubic_slope_widest_window_down"),
            ),
            (
                "cubic slope, narrowest window, down",
                ("headline", "fitted_cubic_slope_narrowest_window_down"),
            ),
            (
                "cubic slope, narrowest window, up",
                ("headline", "fitted_cubic_slope_narrowest_window_up"),
            ),
            (
                "leading-term error at the smallest swept move",
                ("headline", "leading_term_relative_error_at_smallest_move"),
            ),
            (
                "quartic correction predicted by the closed forms",
                ("headline", "quartic_correction_predicted_S_V4_over_4_V3"),
            ),
            ("book third derivative at the base spot", ("headline", "book_speed_at_base_spot")),
            (
                "third derivative crosses zero at down move",
                ("headline", "aggregate_speed_crosses_zero_at_move"),
            ),
            (
                "remainder crosses zero at down move",
                ("headline", "predicted_remainder_zero_at_move"),
            ),
        ),
    ),
    Member(
        key="two_factor_error_bound",
        title="What a joint spot-and-volatility shock costs the delta-gamma-vega stress map",
        kind=EXPERIMENT,
        script="experiments/two_factor_error_bound/run.py",
        artifact="experiments/two_factor_error_bound/results/two_factor_bound.json",
        # No `plot` labels, for the same reason as the member above: this publishes a bound,
        # not a value against an oracle, and panel A of the envelope figure is labelled
        # |our value - oracle| / |oracle|.
        headline=(
            ("joint shocks swept", ("headline", "joint_shocks_swept")),
            ("Lagrange inclusion violations", ("headline", "inclusions_violated")),
            (
                "error-vs-shock-size slope, crash ray, narrowest window",
                ("headline", "slope_of_error_against_shock_size", "crash (equity down, vol up)"),
            ),
            (
                "error-vs-shock-size slope, aligned ray, narrowest window",
                ("headline", "slope_of_error_against_shock_size", "aligned (equity up, vol up)"),
            ),
            ("slope for a pure spot shock", ("headline", "slope_for_a_pure_spot_shock")),
            ("published risk_off error", ("headline", "published_error")),
            ("risk_off interval excludes zero", ("headline", "published_interval_excludes_zero")),
            (
                "largest cubic over the NET quadratic at risk_off",
                ("headline", "largest_cubic_over_net_quadratic"),
            ),
            (
                "largest cubic over the quadratic MAGNITUDES at risk_off",
                ("headline", "largest_cubic_over_quadratic_magnitudes"),
            ),
            ("dominant omitted term", ("headline", "dominant_omitted_term")),
            (
                "error over the closed-form quadratic at risk_off",
                ("headline", "quadratic_prediction_ratio_at_published_size"),
            ),
        ),
    ),
    Member(
        key="stress_testing",
        title="Stress reversals, attribution closure and delta-gamma linearisation error",
        kind=EXPERIMENT,
        script="experiments/stress_testing/run.py",
        artifact="experiments/stress_testing/results/stress_testing_study.json",
        headline=(
            ("worst factor attribution residual", ("attribution_closure", "worst_factor_residual")),
            (
                "worst position attribution residual",
                ("attribution_closure", "worst_position_residual"),
            ),
            (
                "relative linearisation error after a 40% equity fall",
                ("linearisation", "error_at_40pct"),
            ),
            ("worst VaR decomposition residual", ("decomposition", "worst_residual")),
        ),
    ),
    Member(
        key="real_data_risk_study",
        title="Phase 5/6 estimator conclusions re-run on real daily market observations",
        kind=EXPERIMENT,
        script="experiments/real_data_risk_study/run.py",
        artifact="experiments/real_data_risk_study/results/real_data_risk_study.json",
        requires=("scipy",),
        # Aggregated through the artifact's own `headline` block, which the experiment writes
        # as references to the per-estimator rows rather than as paths into a list ordered by
        # confidence level. A path like ("A_estimator_validity", "per_estimator", "gaussian")
        # returns a *list*, `dig` cannot index it, and the first element is the 95 % row — so
        # the suite would print a 95 % rate under a label saying 99 % and nothing would fail.
        # No `plot`: this member publishes no error against an oracle, and panel A of the
        # envelope figure is labelled |our value - oracle| / |oracle|.
        headline=(
            ("out-of-sample evaluation rows", ("headline", "evaluation_rows")),
            (
                "Gaussian 99% realised violation rate",
                ("headline", "gaussian_99_realised_violation_rate"),
            ),
            (
                "Gaussian 99% exact interval excludes nominal",
                ("headline", "gaussian_99_exact_interval_excludes_nominal"),
            ),
            (
                "historical 99% realised violation rate",
                ("headline", "historical_99_realised_violation_rate"),
            ),
            ("violations", ("headline", "violations")),
            ("Kupiec p-value", ("headline", "kupiec_p_value")),
            (
                "Christoffersen independence p-value",
                ("headline", "christoffersen_independence_p_value"),
            ),
            (
                "Christoffersen conditional coverage p-value",
                ("headline", "christoffersen_conditional_coverage_p_value"),
            ),
            ("violation run-test z", ("headline", "run_test_z")),
            ("block/iid bootstrap SE ratio", ("headline", "block_over_iid_bootstrap_se_ratio")),
            (
                "covariance ranking, best to worst",
                ("headline", "covariance_ranking_best_to_worst"),
            ),
        ),
    ),
    Member(
        key="restrike_gamma_map",
        title="What re-striking gamma at the shocked volatility actually buys the stress map",
        kind=EXPERIMENT,
        script="experiments/restrike_gamma_map/run.py",
        artifact="experiments/restrike_gamma_map/results/restrike_gamma_map.json",
        # No `plot`, for the reason the two members above give: this compares approximations against
        # a revaluation rather than against an oracle, and panel A of the envelope figure is
        # labelled |our value - oracle| / |oracle|.
        headline=(
            ("grid cells with a volatility move", ("headline", "cells_with_a_volatility_move")),
            (
                "cells the re-strike improves",
                ("headline", "cells_where_restrike_reduces_abs_error"),
            ),
            ("share of cells improved", ("headline", "share_improved")),
            ("value-weighted error reduction", ("headline", "value_weighted_reduction")),
            (
                "worst error factor after over before",
                ("headline", "worst_error_factor_after_over_before"),
            ),
            ("published risk_off error, shipped map", ("headline", "published_error_base")),
            (
                "published risk_off error, re-struck gamma",
                ("headline", "published_error_gamma_restrike"),
            ),
            (
                "fraction of the named cubic removed",
                ("headline", "published_fraction_of_local_term_removed"),
            ),
            (
                "doubled-error cells explained by cancellation",
                ("headline", "of_those_the_base_error_was_smaller_than_the_removed_term"),
            ),
            (
                "nearest-zero prediction error, worst column",
                ("headline", "nearest_zero_distance_max"),
            ),
            (
                "cells where the naive full re-strike is worse",
                ("headline", "all_restrike_worse_than_gamma_only"),
            ),
        ),
    ),
    Member(
        key="fourth_order_crossing_map",
        title="How far a fourth-order truncation predicts the stress map's crossing",
        kind=EXPERIMENT,
        script="experiments/fourth_order_crossing_map/run.py",
        artifact="experiments/fourth_order_crossing_map/results/fourth_order_crossing_map.json",
        # No `plot`, for the reason the members above give: it compares a truncation against a
        # revaluation rather than against an oracle.
        headline=(
            ("delta columns swept", ("headline", "columns_swept")),
            ("priced zeros across the columns", ("headline", "measured_zeros_total")),
            ("cubic truncation zeros", ("headline", "cubic_zeros_total")),
            ("quartic truncation zeros", ("headline", "quartic_zeros_total")),
            (
                "columns where the cubic mis-counts the crossings",
                ("headline", "columns_where_the_cubic_zero_count_disagrees"),
            ),
            (
                "columns where the quartic mis-counts the crossings",
                ("headline", "columns_where_the_quartic_zero_count_disagrees"),
            ),
            (
                "worst crossing distance, cubic, |delta| <= 0.15",
                (
                    "headline",
                    "fits",
                    "cubic_distance_max_within_the_widened_limit",
                ),
            ),
            (
                "worst crossing distance, quartic, |delta| <= 0.15",
                (
                    "headline",
                    "fits",
                    "quartic_distance_max_within_the_widened_limit",
                ),
            ),
            (
                "radius improvement factor at the widened limit",
                ("headline", "fits", "improvement_factor_at_the_widened_limit"),
            ),
            ("residual slope after the cubic", ("headline", "fits", "residual_slope_cubic_span")),
            (
                "residual slope after the quartic",
                ("headline", "fits", "residual_slope_quartic_span"),
            ),
            (
                "risk_off error, quartic truncation relative",
                ("headline", "published_base_quartic_relative_error"),
            ),
        ),
    ),
    Member(
        key="second_book_crossing_map",
        title="Does the fourth-order crossing radius hold on books other than the published one",
        kind=EXPERIMENT,
        script="experiments/second_book_crossing_map/run.py",
        artifact="experiments/second_book_crossing_map/results/second_book_crossing_map.json",
        # No `plot`, for the reason the members above give: a truncation is compared with a
        # revaluation of the same book, not with an oracle.
        headline=(
            ("books measured", ("headline", "books_measured")),
            ("published ladder, cubic radius", ("headline", "published_control_cubic")),
            ("published ladder, quartic radius", ("headline", "published_control_quartic")),
            (
                "books the quartic widens",
                ("headline", "books_where_the_quartic_radius_is_at_least_the_cubic"),
            ),
            (
                "books the quartic brings closer inside the cubic radius",
                ("headline", "books_where_the_quartic_is_closer_inside_the_cubic_radius"),
            ),
            (
                "radius on the book least like the published one",
                ("headline", "radii_quartic", "short-dated tight"),
            ),
            (
                "fewest columns with a priced crossing",
                ("headline", "columns_with_a_priced_crossing_minimum"),
            ),
            (
                "largest difference from v1.5.0's engine call",
                ("control", "engine_pnl_largest_absolute_difference"),
            ),
            (
                "largest difference from v1.6.0's truncation",
                ("control", "quartic_truncation_largest_absolute_difference"),
            ),
        ),
    ),
)


def dig(payload: dict[str, Any], keys: tuple[str, ...], *, source: str) -> Any:
    """Follow a key path, and fail loudly if the artifact does not have it."""
    node: Any = payload
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            raise SuiteError(f"{source} has no {'.'.join(repr(k) for k in keys)!r}")
        node = node[key]
    return node


def importable(module: str) -> bool:
    try:
        import_module(module)
    except Exception:
        return False
    return True


def execute(member: Member, *, timeout: float) -> dict[str, Any]:
    """Run one member's own script, capturing everything a reviewer would ask for."""
    missing = [name for name in member.requires if not importable(name)]
    if missing:
        return {
            "status": "skipped",
            "reason": f"oracle package(s) not installed: {', '.join(missing)}",
            "seconds": 0.0,
        }
    if not (ROOT / member.script).exists():
        raise SuiteError(f"{member.key}: script {member.script} is missing")
    # The member's own artifact records `sys.argv[0]` as its generating command. Passing an
    # absolute path here would write this machine's directory into frozen evidence, so the
    # script is named relative to the cwd the subprocess actually runs in.
    started = time.monotonic()
    completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, no interpolation
        [sys.executable, member.script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    seconds = time.monotonic() - started
    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout or "").strip().splitlines()[-25:]
        return {
            "status": "failed",
            "reason": f"exit code {completed.returncode}",
            "seconds": round(seconds, 3),
            "output_tail": "\n".join(tail),
        }
    return {"status": "passed", "reason": "", "seconds": round(seconds, 3)}


def read_artefact(member: Member) -> dict[str, Any]:
    path = ROOT / member.artifact
    if not path.exists():
        raise SuiteError(f"{member.key}: expected artifact {member.artifact} was not written")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SuiteError(f"{member.key}: artifact {member.artifact} is not a JSON object")
    return payload


def collect(member: Member, run: dict[str, Any]) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "key": member.key,
        "title": member.title,
        "kind": member.kind,
        "script": member.script,
        "artifact": member.artifact,
        **run,
    }
    if run["status"] == "skipped":
        entry["metrics"] = []
        return entry
    payload = read_artefact(member)
    entry["artifact_sha256"] = sha256_file(ROOT / member.artifact)
    entry["generated_at_utc"] = (
        payload.get("generated_at_utc") or payload.get("generated_utc") or ""
    )
    entry["command"] = payload.get("command", "")
    metrics = []
    for label, keys in member.headline:
        value = dig(payload, keys, source=member.artifact)
        metrics.append(
            {
                "label": label,
                "value": value,
                "source_keys": list(keys),
                "artifact": member.artifact,
            }
        )
    entry["metrics"] = metrics
    entry["plot"] = list(member.plot)
    return entry


def format_value(value: Any) -> str:
    """Render a published number without changing it.

    Several headline fields carry the *location* of a worst case alongside its value, as a
    small object (`{"value": ..., "problem": ..., "seed": ...}`) or a pair. That context is
    the most useful part of the claim, so it is spelled out rather than dumped as JSON.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return _format_number(value)
    if isinstance(value, dict):
        inner = value.get("value")
        if isinstance(inner, (int, float)) and not isinstance(inner, bool):
            context = ", ".join(
                f"{key}={val}" for key, val in sorted(value.items()) if key != "value"
            )
            return f"{_format_number(inner)} ({context})" if context else _format_number(inner)
        numbers = value.values()
        if numbers and all(
            isinstance(val, (int, float)) and not isinstance(val, bool) for val in numbers
        ):
            return ", ".join(f"{key}={_format_number(val)}" for key, val in sorted(value.items()))
        return json.dumps(value, sort_keys=True)
    if isinstance(value, (list, tuple)):
        return " / ".join(format_value(item) for item in value)
    return str(value)


def _format_number(value: float) -> str:
    if isinstance(value, int):
        return f"{value:,}"
    if value == 0.0:
        return "0"
    magnitude = abs(value)
    if magnitude < 1e-3 or magnitude >= 1e5:
        return f"{value:.3e}"
    return f"{value:.6g}"


def headline_rows(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for entry in entries:
        for metric in entry["metrics"]:
            rows.append(
                {
                    "member": entry["key"],
                    "kind": entry["kind"],
                    "metric": metric["label"],
                    "value": format_value(metric["value"]),
                    "value_json": json.dumps(metric["value"], sort_keys=True),
                    "source_keys": " / ".join(metric["source_keys"]),
                    "artifact": metric["artifact"],
                    "artifact_sha256": entry["artifact_sha256"],
                    "generated_at_utc": entry["generated_at_utc"],
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise SuiteError("no headline rows to write; the suite aggregated nothing")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


Z_MEMBER = "monte_carlo_vs_analytic"


def numeric_metric(value: Any) -> float | None:
    """The number inside a published metric.

    Some headline fields are bare floats; the optimiser's are located worst cases shaped
    `{"value": ..., "problem": ..., "assets": ..., "seed": ...}`. Both have to be plottable
    without a second copy of the data.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict) and isinstance(value.get("value"), (int, float)):
        inner = value["value"]
        return None if isinstance(inner, bool) else float(inner)
    return None


def plot_envelope(entries: list[dict[str, Any]], path: Path) -> str:
    """One figure holding every worst-case error the suite publishes, plus the z-scores.

    The bars are drawn from the *same* metrics the summary table prints, not from a second
    pass over the CSVs. A figure built by its own extraction can quietly disagree with the
    table beside it, and that is the one way this artifact would be worse than useless.

    Errors span decades, so panel A is logarithmic; z-scores are already standardised, so
    panel B is linear with the two references that matter drawn in: zero bias, and the
    unit spread a correctly reported standard error produces.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return "not generated (matplotlib unavailable)"

    errors: list[tuple[str, float]] = []
    scores: list[tuple[str, float]] = []
    for entry in entries:
        for label in entry.get("plot", ()):
            metric = next((m for m in entry["metrics"] if m["label"] == label), None)
            if metric is None:
                raise SuiteError(f"{entry['key']}: plot label {label!r} is not a headline metric")
            value = numeric_metric(metric["value"])
            if value is None:
                raise SuiteError(f"{entry['key']}: plot label {label!r} is not numeric")
            if entry["key"] == Z_MEMBER:
                scores.append((label, value))
            elif value > 0.0:
                errors.append((label, value))
    if not errors:
        return "not generated (no positive error metrics to plot)"

    figure, axes = plt.subplots(1, 2, figsize=(12.4, 5.0), gridspec_kw={"width_ratios": [3, 2]})

    def draw(axis, items, title, log_scale):
        labels = [label for label, _ in items]
        values = [value for _, value in items]
        positions = np.arange(len(items))[::-1]
        axis.barh(positions, values, height=0.62, color="#2f6f9f")
        axis.set_yticks(positions)
        axis.set_yticklabels(labels, fontsize=8)
        axis.set_title(title, fontsize=10)
        if log_scale:
            axis.set_xscale("log")
            axis.set_xlim(min(values) / 30.0, max(values) * 30.0)
            for position, value in zip(positions, values, strict=True):
                axis.annotate(
                    f"{value:.1e}",
                    (value, position),
                    textcoords="offset points",
                    xytext=(6, 0),
                    va="center",
                    fontsize=7,
                )
        else:
            axis.axvline(0.0, color="0.55", linewidth=0.9)
            axis.axvline(1.0, color="0.55", linewidth=0.9, linestyle="--")
            axis.set_xlim(-0.35, 1.35)
            for position, value in zip(positions, values, strict=True):
                axis.annotate(
                    f"{value:.3f}",
                    (value, position),
                    textcoords="offset points",
                    xytext=(6, 0),
                    va="center",
                    fontsize=7,
                )
        axis.grid(axis="x", linestyle=":", linewidth=0.6, alpha=0.6)

    draw(
        axes[0],
        errors,
        "Worst case over every validated row, per published metric (log scale)",
        True,
    )
    axes[0].set_xlabel(r"$|\text{our value} - \text{oracle}| \;/\; |\text{oracle}|$")
    if scores:
        draw(
            axes[1],
            scores,
            "Monte Carlo z vs the analytic oracle\nmean (bias) and std dev (reported SE)",
            False,
        )
        axes[1].set_xlabel("solid line: 0 bias   dashed line: std dev of 1")
        axes[1].set_xlim(-0.45, 1.55)
    else:
        axes[1].axis("off")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return "generated"


def markdown(entries: list[dict[str, Any]], suite: dict[str, Any], out_dir: Path) -> str:
    lines = [
        "# Benchmark suite",
        "",
        "Generated by `uv run python scripts/run_benchmark_suite.py`. No number in this",
        "file was typed: each one is read from the JSON the named script writes, and the",
        "key path it came from is recorded in `suite_headline.csv`.",
        "",
        f"- revision: `{suite['repository']['git_commit']}`"
        + (
            " **(working tree was dirty at run time)**"
            if suite["repository"]["working_tree_dirty"]
            else ""
        ),
        f"- command: `{suite['command']}`",
        f"- run: {suite['generated_at_utc']}",
        f"- core build: {suite['environment']['cpp_build_type']}, "
        f"{suite['environment']['cpp_compiler']}, Python {suite['environment']['python']}",
        "",
    ]
    if suite["repository"]["working_tree_dirty"]:
        lines += [
            "> Because the tree was dirty, these artifacts describe uncommitted work.",
            "> Re-run on a clean tree before citing them.",
            "",
        ]

    for kind, heading in (
        (CORRECTNESS, "Correctness benchmarks"),
        (EXPERIMENT, "Statistical experiments"),
        (PERFORMANCE, "Performance benchmarks"),
    ):
        members = [e for e in entries if e["kind"] == kind]
        if not members:
            continue
        lines += [
            f"## {heading}",
            "",
            "| member | status | wall | headline result |",
            "|---|---|---|---|",
        ]
        for entry in members:
            if entry["status"] == "skipped":
                detail = f"*{entry['reason']}*"
            else:
                detail = "; ".join(
                    f"{m['label']}: **{format_value(m['value'])}**" for m in entry["metrics"]
                )
            icon = {
                "passed": "pass",
                "aggregated": "artifact",
                "failed": "**FAIL**",
                "skipped": "skipped",
            }[entry["status"]]
            lines.append(f"| `{entry['key']}` | {icon} | {entry['seconds']:.1f}s | {detail} |")
        lines.append("")
        for entry in members:
            if entry["status"] == "failed":
                lines += [
                    f"### Failure detail: `{entry['key']}`",
                    "",
                    "```",
                    entry.get("output_tail", ""),
                    "```",
                    "",
                ]

    figure_note = suite["outputs"]["figure_status"]
    lines += [
        "## Reading the two numbers that are easiest to over-claim",
        "",
        "- A Monte Carlo z-score with mean near 0 and standard deviation near 1 does not mean",
        "  the price is right; it means the price is right *and* the standard error it reports",
        "  is honest. That is why the suite runs the estimator check separately from the",
        "  convergence check.",
        "- A worst-case relative error is the maximum over every row, not an average, so it is",
        "  the number to compare against a tolerance. The violin in `validation_envelope.png`",
        f"  shows the shape underneath it. Figure: {figure_note}.",
        "",
        "## Plot and artifact index",
        "",
        f"- `{repo_relative(out_dir)}/` — this run: `suite_run.json`, `suite_headline.csv`,"
        "  `suite_summary.md`, `validation_envelope.png`.",
    ]
    seen: set[str] = set()
    for entry in entries:
        if entry["status"] == "skipped":
            continue
        directory = (ROOT / entry["artifact"]).parent
        relative = repo_relative(directory)
        if relative in seen:
            continue
        seen.add(relative)
        listing = sorted(directory.glob("*.png"))
        lines.append(f"- `{relative}/`: {', '.join(p.name for p in listing) or 'no figures'}")
    lines.append("")
    return "\n".join(lines)


def command_line(arguments: argparse.Namespace) -> str:
    """The invocation, spelled so it can be pasted on another machine.

    Every other artifact in the evidence chain names the command that produced it, and the
    manifest now reads the suite's roll-up too, so the aggregate needed one as well. argv is
    not used directly: it would carry `--out /Users/<name>/...` into a committed artifact, and
    a relative `scripts/...` differs from however the caller actually typed it. The flags here
    are the ones that change what the run *claims* — `--require-all` is the difference between
    "12/12 executed" and "12 reported, some of them skipped" — so they are recorded verbatim.
    """
    parts = ["uv run python scripts/run_benchmark_suite.py"]
    for key in sorted(set(arguments.only)):
        parts.append(f"--only {key}")
    if arguments.require_all:
        parts.append("--require-all")
    if arguments.no_run:
        parts.append("--no-run")
    if arguments.out is not None:
        relative = (
            repo_relative(arguments.out.resolve())
            if arguments.out.is_absolute()
            else str(arguments.out)
        )
        parts.append(f"--out {relative}")
    return " ".join(parts)


def build(
    entries: list[dict[str, Any]], *, ran: bool, out_dir: Path, command: str
) -> dict[str, Any]:
    env = environment()
    out_dir.mkdir(parents=True, exist_ok=True)
    figure = out_dir / "validation_envelope.png"
    figure_status = plot_envelope(entries, figure)

    suite = {
        "schema": "quantrisk-benchmark-suite/1",
        "command": command,
        "generated_at_utc": env["generated_at_utc"],
        "trigger": "run" if ran else "aggregate-only",
        "repository": {
            "git_commit": env["git_commit"],
            "binary_git_commit": env["binary_git_commit"],
            "provenance": env["provenance"],
            "working_tree_dirty": env["working_tree_dirty"],
            "uncommitted_paths": env["uncommitted_paths"][:40],
        },
        "environment": {
            "python": env["packages"]["python"],
            "platform": env["python_platform"],
            "machine": env["python_machine"],
            "cpp_build_type": env["cpp_build_type"],
            "cpp_compiler": env["cpp_compiler"],
            "cpp_standard": env["cpp_standard"],
            "packages": env["packages"],
        },
        "members": entries,
        "totals": {
            "members": len(entries),
            "passed": sum(1 for e in entries if e["status"] == "passed"),
            "aggregated_only": sum(1 for e in entries if e["status"] == "aggregated"),
            "failed": sum(1 for e in entries if e["status"] == "failed"),
            "skipped": sum(1 for e in entries if e["status"] == "skipped"),
            "wall_seconds": round(sum(e["seconds"] for e in entries), 1),
        },
        "outputs": {"figure_status": figure_status},
    }
    return suite


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--only", action="append", default=[], help="run/aggregate just these member keys"
    )
    parser.add_argument(
        "--no-run", action="store_true", help="aggregate the artifacts already on disk"
    )
    parser.add_argument("--list", action="store_true", help="print the members and exit")
    parser.add_argument("--timeout", type=float, default=3600.0, help="per-member timeout, seconds")
    parser.add_argument(
        "--require-all",
        action="store_true",
        help="exit non-zero if any member was skipped, i.e. an oracle is missing",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="where to write the aggregated artifacts (default: benchmarks/suite/results)",
    )
    arguments = parser.parse_args()

    if arguments.list:
        for member in MEMBERS:
            print(f"{member.kind:24s} {member.key:28s} {member.script}")
        return 0

    selected = [m for m in MEMBERS if not arguments.only or m.key in arguments.only]
    unknown = sorted(set(arguments.only) - {m.key for m in selected})
    if unknown:
        raise SuiteError(f"unknown member(s): {', '.join(unknown)}")

    out_dir = arguments.out.resolve() if arguments.out else RESULTS_DIR

    entries = []
    for member in selected:
        if arguments.no_run:
            # Not "passed": nothing was executed. The artifact exists and carries every
            # field the summary asks for, which is a weaker claim and has to look weaker.
            run = {"status": "aggregated", "reason": "artifact read from disk", "seconds": 0.0}
            print(f"aggregating {member.key} ...", flush=True)
        else:
            print(f"running {member.key} ...", flush=True)
            run = execute(member, timeout=arguments.timeout)
            print(f"  {member.key}: {run['status']} in {run['seconds']:.1f}s", flush=True)
        entries.append(collect(member, run))

    suite = build(
        entries,
        ran=not arguments.no_run,
        out_dir=out_dir,
        command=command_line(arguments),
    )
    json_path = out_dir / "suite_run.json"
    json_path.write_text(json.dumps(suite, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = headline_rows(entries)
    csv_path = out_dir / "suite_headline.csv"
    write_csv(csv_path, rows)
    md_path = out_dir / "suite_summary.md"
    md_path.write_text(markdown(entries, suite, out_dir), encoding="utf-8")

    for path in (json_path, csv_path, md_path, out_dir / "validation_envelope.png"):
        if path.exists():
            print(f"  {repo_relative(path)}  {path.stat().st_size:,} bytes")

    totals = suite["totals"]
    print(
        f"suite: {totals['passed']}/{totals['members']} executed and passed, "
        f"{totals['aggregated_only']} aggregated from disk, "
        f"{totals['failed']} failed, {totals['skipped']} skipped, "
        f"{totals['wall_seconds']:.1f}s total"
    )
    if totals["failed"]:
        return 1
    if arguments.require_all and totals["skipped"]:
        print(
            f"--require-all: {totals['skipped']} member(s) skipped, so the suite did not "
            "measure what it claims to. Install the `oracles` extra.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SuiteError as error:
        print(f"suite aborted: {error}", file=sys.stderr)
        raise SystemExit(2) from error
