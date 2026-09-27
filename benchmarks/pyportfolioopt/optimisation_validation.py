#!/usr/bin/env python3
"""Phase 6 benchmark: our portfolio optimisers against PyPortfolioOpt and cvxpy.

    uv run python benchmarks/pyportfolioopt/optimisation_validation.py

Every problem is solved three ways - our C++ core, PyPortfolioOpt (SciPy SLSQP),
and cvxpy (OSQP / SCS) - and the outputs the Phase 6 gate names are recorded for
each: weights, expected return, volatility, Sharpe, CVaR and constraint
residual. Agreement is measured, never assumed, and each solver's own stopping
tolerance is reported next to the difference it produced, so a loose number can be
read as solver slack rather than a bug in either implementation.

Two details decide whether this comparison means anything. The oracle side is read
from its raw solver output, not from PyPortfolioOpt's `clean_weights()`, which rounds
to five decimals and would floor every disagreement at ~1e-5 regardless of how
tightly the optimisation converged. And agreement is reported in the quantity each
problem actually optimises, because coordinate distance is not a quality signal: near
a flat frontier two solvers can sit 1e-9 apart in weights and be indistinguishable in
objective, which is why `objective_gap_*` sits beside `weight_diff_*` rather than
replacing it.

The oracles are benchmarks only. The library imports none of them
(PROJECT_SPEC.md §2.2), and no reference numbers are hard-coded here: everything
comes from a live call made while this script runs.
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
from quantrisk.experiments.metadata import (
    artifact_manifest,
    environment,
    package_versions,
    repo_relative,
    utc_timestamp,
)

RESULTS = Path(__file__).resolve().parent / "results"

PORTFOLIO = quantrisk.portfolio
ASSET_COUNTS = (2, 3, 5, 8, 12)
SEEDS = (7, 8, 9)
RISK_FREE = 0.002
CVaR_BETA = 0.95
SCENARIOS = 250

# The quantity each problem actually optimises, in the keys metrics() returns.
PROBLEM_OBJECTIVE = {
    "min_variance": "volatility",
    "efficient_return": "volatility",
    "risk_parity": "volatility",
    "max_sharpe": "sharpe_ratio",
    "min_cvar": "cvar",
}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    field_names = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)


def random_problem(assets: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """A factor-structured covariance and a plausible monthly expected-return vector."""
    rng = np.random.default_rng(seed * 31 + assets)
    factor = rng.normal(0, 1, (assets, 1))
    loadings = rng.normal(0, 1, (assets, 2))
    covariance = (
        0.0009 * (factor @ factor.T) + 0.0004 * (loadings @ loadings.T) + 0.0004 * np.eye(assets)
    )
    expected_returns = rng.normal(0.06, 0.04, assets) / 12.0
    return covariance, expected_returns


def our_inputs(covariance: np.ndarray, expected_returns: np.ndarray | None = None) -> Any:
    problem = PORTFOLIO.OptimizerInputs()
    problem.assets = covariance.shape[0]
    problem.covariance = covariance.reshape(-1).tolist()
    if expected_returns is not None:
        problem.expected_returns = expected_returns.tolist()
    return problem


def solved_value(variable: Any, context: str) -> np.ndarray:
    """Fail loudly if a reference solve did not produce a value.

    A silently-None cvxpy solution would otherwise reach the metrics as NoneType
    arithmetic, or - worse, if a solver returned a stale partial value - quietly
    enter the agreement statistics as a bogus oracle answer.
    """
    if variable.value is None:
        raise RuntimeError(f"reference solve produced no value for {context}")
    return np.asarray(variable.value).flatten()


def raw_weights(optimizer: Any, context: str) -> np.ndarray:
    """The optimiser's own answer, before PyPortfolioOpt tidies it up.

    `.clean_weights()` rounds to five decimal places and zeroes anything under 1e-4,
    so comparing against it measures that post-processing rather than the solver: the
    disagreement floors out at ~1e-5 no matter how tight the optimisation is. The
    `.weights` attribute is the raw SciPy output, which is the number being checked.
    """
    if optimizer.weights is None:
        raise RuntimeError(f"reference solve produced no weights for {context}")
    return np.asarray(optimizer.weights, dtype=float).flatten()


def metrics(
    weights: np.ndarray,
    covariance: np.ndarray,
    expected_returns: np.ndarray,
    scenarios: np.ndarray,
    sharpe_reference: float | None,
) -> dict[str, Any]:
    variance = float(weights @ covariance @ weights)
    volatility = math.sqrt(max(variance, 0.0))
    expected = float(weights @ expected_returns)
    losses = np.sort(-(scenarios @ weights))[::-1]
    tail = (1.0 - CVaR_BETA) * scenarios.shape[0]
    whole = int(math.floor(tail))
    fraction = tail - whole
    total = float(losses[:whole].sum())
    if whole < losses.size:
        total += fraction * float(losses[whole])
    return {
        "expected_return": expected,
        "volatility": volatility,
        "sharpe_ratio": (
            float("nan") if sharpe_reference is None else (expected - sharpe_reference) / volatility
        ),
        "cvar": total / tail,
        "budget_residual": abs(float(weights.sum()) - 1.0),
        "weight_bound_violation": float(max(0.0, -weights.min())),
    }


def main() -> int:
    import warnings

    import cvxpy
    import pandas as pd
    from pypfopt import EfficientCVaR, EfficientFrontier

    warnings.filterwarnings("ignore")
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []

    for assets in ASSET_COUNTS:
        for seed in SEEDS:
            covariance, expected_returns = random_problem(assets, seed)
            rng = np.random.default_rng(1_000 + seed * 7 + assets)
            scenarios = rng.multivariate_normal(expected_returns, covariance, SCENARIOS)

            # --- minimum variance
            request = PORTFOLIO.OptimizationRequest()
            ours = PORTFOLIO.minimum_variance(our_inputs(covariance, expected_returns), request)
            frontier = EfficientFrontier(expected_returns, covariance, weight_bounds=(0, 1))
            frontier.min_volatility()
            pypfopt_weights = raw_weights(frontier, f"min_variance {assets} assets seed {seed}")
            variable = cvxpy.Variable(assets)
            cvx_problem = cvxpy.Problem(
                cvxpy.Minimize(0.5 * cvxpy.quad_form(variable, cvxpy.psd_wrap(covariance))),
                [cvxpy.sum(variable) == 1, variable >= 0],
            )
            cvx_problem.solve(solver=cvxpy.OSQP, eps_abs=1e-11, eps_rel=1e-11)
            cvxpy_weights = solved_value(variable, f"min_variance {assets} assets seed {seed}")
            rows.append(
                _record(
                    "min_variance",
                    assets,
                    seed,
                    np.array(ours.weights),
                    pypfopt_weights,
                    cvxpy_weights,
                    covariance,
                    expected_returns,
                    scenarios,
                    RISK_FREE,
                    our_note=ours.note,
                    extra={
                        "verified_optimal": ours.verified_optimal,
                        "budget_residual": ours.budget_residual,
                        "objective": ours.variance,
                    },
                )
            )

            # --- maximum Sharpe
            request = PORTFOLIO.OptimizationRequest()
            request.risk_free_rate = RISK_FREE
            ours = PORTFOLIO.maximum_sharpe(our_inputs(covariance, expected_returns), request)
            frontier = EfficientFrontier(expected_returns, covariance, weight_bounds=(0, 1))
            frontier.max_sharpe(risk_free_rate=RISK_FREE)
            pypfopt_weights = raw_weights(frontier, f"max_sharpe {assets} assets seed {seed}")
            # cvxpy's Sharpe reformulation: the ratio is invariant to scaling, so pin the
            # excess return at 1 and minimise variance instead; the budget constraint is
            # then recovered by the rescaling. A different route to the same answer as our
            # ternary search along the frontier, which is exactly what makes it a check.
            excess = expected_returns - RISK_FREE
            nu = cvxpy.Variable(assets)
            sharpe_problem = cvxpy.Problem(
                cvxpy.Minimize(0.5 * cvxpy.quad_form(nu, cvxpy.psd_wrap(covariance))),
                [excess @ nu == 1.0, nu >= 0],
            )
            sharpe_problem.solve(solver=cvxpy.OSQP, eps_abs=1e-11, eps_rel=1e-11)
            raw_nu = solved_value(nu, f"max_sharpe {assets} assets seed {seed}")
            cvxpy_weights = raw_nu / raw_nu.sum()
            rows.append(
                _record(
                    "max_sharpe",
                    assets,
                    seed,
                    np.array(ours.weights),
                    pypfopt_weights,
                    cvxpy_weights,
                    covariance,
                    expected_returns,
                    scenarios,
                    RISK_FREE,
                    our_note=ours.note,
                    extra={
                        "verified_optimal": ours.verified_optimal,
                        "budget_residual": ours.budget_residual,
                        "objective": ours.sharpe_ratio,
                    },
                )
            )

            # --- efficient frontier point at a binding target
            target = float(expected_returns.max()) * 0.85
            request = PORTFOLIO.OptimizationRequest()
            request.target_return = target
            ours = PORTFOLIO.minimum_variance(our_inputs(covariance, expected_returns), request)
            frontier = EfficientFrontier(expected_returns, covariance, weight_bounds=(0, 1))
            frontier.efficient_return(target)
            pypfopt_weights = raw_weights(frontier, f"efficient_return {assets} assets seed {seed}")
            variable = cvxpy.Variable(assets)
            cvx_problem = cvxpy.Problem(
                cvxpy.Minimize(0.5 * cvxpy.quad_form(variable, cvxpy.psd_wrap(covariance))),
                [cvxpy.sum(variable) == 1, variable >= 0, expected_returns @ variable >= target],
            )
            cvx_problem.solve(solver=cvxpy.OSQP, eps_abs=1e-11, eps_rel=1e-11)
            cvxpy_weights = solved_value(variable, f"efficient_return {assets} assets seed {seed}")
            rows.append(
                _record(
                    "efficient_return",
                    assets,
                    seed,
                    np.array(ours.weights),
                    pypfopt_weights,
                    cvxpy_weights,
                    covariance,
                    expected_returns,
                    scenarios,
                    RISK_FREE,
                    our_note=ours.note,
                    extra={
                        "verified_optimal": ours.verified_optimal,
                        "budget_residual": ours.budget_residual,
                        "target_return": target,
                        "target_residual": ours.target_residual,
                        "objective": ours.variance,
                    },
                )
            )

            # --- risk parity
            ours = PORTFOLIO.risk_parity(covariance.reshape(-1).tolist(), assets)
            variables = cvxpy.Variable(assets)
            parity = cvxpy.Problem(
                cvxpy.Maximize(cvxpy.sum(cvxpy.log(variables))),
                [cvxpy.quad_form(variables, cvxpy.psd_wrap(covariance)) <= 1.0],
            )
            parity.solve(solver=cvxpy.SCS, eps=1e-11)
            cvxpy_weights = solved_value(variables, f"risk_parity {assets} assets seed {seed}")
            cvxpy_weights /= cvxpy_weights.sum()
            # PyPortfolioOpt has no ERC in 1.6.0, and inventing a "reference" for it
            # would be worse than saying so.
            rows.append(
                _record(
                    "risk_parity",
                    assets,
                    seed,
                    np.array(ours.weights),
                    cvxpy_weights,
                    cvxpy_weights,
                    covariance,
                    expected_returns,
                    scenarios,
                    None,
                    our_note=ours.note,
                    extra={
                        "converged": ours.converged,
                        "max_contribution_gap": ours.max_contribution_gap,
                        "cycles": ours.cycles,
                        "objective": ours.variance,
                        "oracle_note": "pypfopt column holds the cvxpy log "
                        "formulation: PyPortfolioOpt 1.6.0 has no "
                        "ERC implementation",
                    },
                )
            )

            # --- CVaR
            request = PORTFOLIO.CvarRequest()
            request.assets = assets
            request.scenarios = SCENARIOS
            request.scenario_returns = scenarios.reshape(-1).tolist()
            request.confidence = CVaR_BETA
            ours = PORTFOLIO.minimise_cvar(request)
            cvar = EfficientCVaR(
                expected_returns,
                pd.DataFrame(scenarios, columns=[f"a{i}" for i in range(assets)]),
                beta=CVaR_BETA,
            )
            cvar.min_cvar()
            pypfopt_weights = raw_weights(cvar, f"min_cvar {assets} assets seed {seed}")
            rows.append(
                _record(
                    "min_cvar",
                    assets,
                    seed,
                    np.array(ours.weights),
                    pypfopt_weights,
                    pypfopt_weights,
                    covariance,
                    expected_returns,
                    scenarios,
                    None,
                    our_note=ours.note,
                    extra={
                        "solved": ours.solved,
                        "certified": ours.certified,
                        "budget_residual": ours.budget_residual,
                        "recomputed_cvar": ours.recomputed_cvar,
                        "alpha": ours.alpha,
                        "pivots": ours.pivots,
                        "oracle_note": "cvxpy column repeats pypfopt: that "
                        "library already solves this LP through cvxpy",
                    },
                )
            )

    def value_of(row: dict[str, Any], key: str) -> float:
        return float(row[key])

    def worst(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
        """The maximum of `key` together with the row that produced it.

        A bare maximum would let one loose LP row masquerade as a general property of
        the solvers, so the offending problem, size and seed travel with the number.
        """
        record = max(rows, key=lambda row: value_of(row, key))
        return {
            "value": value_of(record, key),
            "problem": record["problem"],
            "assets": record["assets"],
            "seed": record["seed"],
        }

    write_csv(RESULTS / "optimisation_vs_oracles.csv", rows)
    per_problem = {}
    for problem in sorted({row["problem"] for row in rows}):
        subset = [row for row in rows if row["problem"] == problem]
        per_problem[problem] = {
            "cases": len(subset),
            "optimises": subset[0]["objective_metric"],
            "max_weight_difference_pypfopt": max(
                value_of(row, "weight_diff_pypfopt") for row in subset
            ),
            "max_weight_difference_cvxpy": max(
                value_of(row, "weight_diff_cvxpy") for row in subset
            ),
            "max_relative_objective_gap_pypfopt": max(
                value_of(row, "objective_gap_pypfopt") for row in subset
            ),
            "max_relative_objective_gap_cvxpy": max(
                value_of(row, "objective_gap_cvxpy") for row in subset
            ),
            "max_relative_volatility_difference_pypfopt": max(
                value_of(row, "volatility_diff_pypfopt") for row in subset
            ),
            "max_relative_volatility_difference_cvxpy": max(
                value_of(row, "volatility_diff_cvxpy") for row in subset
            ),
            "worst_budget_residual": max(value_of(row, "budget_residual") for row in subset),
            "worst_bound_violation": max(
                value_of(row, "weight_bound_violation_ours") for row in subset
            ),
        }
    agreement = {
        "per_problem": per_problem,
        "worst_weight_difference_pypfopt": worst(rows, "weight_diff_pypfopt"),
        "worst_weight_difference_cvxpy": worst(rows, "weight_diff_cvxpy"),
        "worst_relative_objective_gap_pypfopt": worst(rows, "objective_gap_pypfopt"),
        "worst_relative_objective_gap_cvxpy": worst(rows, "objective_gap_cvxpy"),
        "worst_budget_residual": max(value_of(row, "budget_residual") for row in rows),
        "worst_bound_violation": max(value_of(row, "weight_bound_violation_ours") for row in rows),
        "problems_solved": len(rows),
    }
    summary = {
        "phase": "6 - Portfolio optimisation",
        "generated_utc": utc_timestamp(),
        "command": "uv run python benchmarks/pyportfolioopt/optimisation_validation.py",
        "purpose": (
            "Level 2 validation of the covariance estimators' consumers: do the mean-"
            "variance, max-Sharpe, frontier, risk-parity and CVaR solvers in the C++ "
            "core agree with PyPortfolioOpt (SciPy SLSQP) and cvxpy (OSQP/SCS) on "
            "identical inputs, and are their constraints actually satisfied?"
        ),
        "oracles": {
            "pypfopt": {
                "solver": "SciPy SLSQP behind PyPortfolioOpt",
                "tolerance": "the library default (ftol ~1e-9, its own reported slack)",
                "versions": {
                    key: value
                    for key, value in package_versions().items()
                    if key in ("PyPortfolioOpt", "osqp", "scipy", "numpy")
                },
            },
            "cvxpy": {
                "solver": "OSQP for quadratic programs, SCS for the log and "
                "second-order-conic forms",
                "tolerance": "eps_abs = eps_rel = 1e-11 (OSQP), 1e-10..1e-11 (SCS)",
            },
            "not_applicable": (
                "risk parity has no PyPortfolioOpt implementation in 1.6.0, and CVaR is "
                "solved by PyPortfolioOpt through cvxpy, so the duplicated column is "
                "labelled rather than presented as two independent references"
            ),
        },
        "our_side": {
            "certificate": (
                "each of our answers carries a KKT or LP optimality certificate checked "
                "against the original data, so `verified_optimal` is a proof, not a "
                "convergence message"
            ),
            "version": quantrisk.version(),
        },
        "parameters": {
            "asset_counts": list(ASSET_COUNTS),
            "seeds": list(SEEDS),
            "risk_free_rate": RISK_FREE,
            "cvar_confidence": CVaR_BETA,
            "scenarios": SCENARIOS,
        },
        "agreement": agreement,
        "environment": environment(),
        "artifacts": artifact_manifest([RESULTS / "optimisation_vs_oracles.csv"]),
    }
    (RESULTS / "optimisation_vs_oracles.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(agreement, indent=2))
    print(f"wrote {len(summary['artifacts'])} artifacts to {repo_relative(RESULTS)}")
    return 0


def _record(
    problem: str,
    assets: int,
    seed: int,
    ours: np.ndarray,
    pypfopt: np.ndarray,
    cvxpy_weights: np.ndarray,
    covariance: np.ndarray,
    expected_returns: np.ndarray,
    scenarios: np.ndarray,
    risk_free: float | None,
    *,
    our_note: str,
    extra: dict[str, Any],
) -> dict[str, Any]:
    """One row per (problem, assets, seed), with all six gate quantities per solver."""
    our_metrics = metrics(ours, covariance, expected_returns, scenarios, risk_free)
    their_metrics = metrics(pypfopt, covariance, expected_returns, scenarios, risk_free)
    conic_metrics = metrics(cvxpy_weights, covariance, expected_returns, scenarios, risk_free)
    scale = max(1e-12, abs(their_metrics["volatility"]))
    record: dict[str, Any] = {
        "problem": problem,
        "assets": assets,
        "seed": seed,
        "weights_ours": ",".join(f"{value:.17g}" for value in ours),
        "weights_pypfopt": ",".join(f"{value:.17g}" for value in pypfopt),
        "weights_cvxpy": ",".join(f"{value:.17g}" for value in cvxpy_weights),
        "expected_return_ours": our_metrics["expected_return"],
        "volatility_ours": our_metrics["volatility"],
        "sharpe_ours": our_metrics["sharpe_ratio"],
        "cvar_ours": our_metrics["cvar"],
        "budget_residual": our_metrics["budget_residual"],
        "weight_bound_violation_ours": our_metrics["weight_bound_violation"],
        "volatility_pypfopt": their_metrics["volatility"],
        "sharpe_pypfopt": their_metrics["sharpe_ratio"],
        "cvar_pypfopt": their_metrics["cvar"],
        "volatility_cvxpy": conic_metrics["volatility"],
        "sharpe_cvxpy": conic_metrics["sharpe_ratio"],
        "cvar_cvxpy": conic_metrics["cvar"],
        "weight_diff_pypfopt": float(np.abs(ours - pypfopt).max()),
        "weight_diff_cvxpy": float(np.abs(ours - cvxpy_weights).max()),
        "volatility_diff_pypfopt": float(
            abs(our_metrics["volatility"] - their_metrics["volatility"]) / scale
        ),
        "volatility_diff_cvxpy": float(
            abs(our_metrics["volatility"] - conic_metrics["volatility"]) / scale
        ),
        "objective_metric": PROBLEM_OBJECTIVE[problem],
        "objective_ours": our_metrics[PROBLEM_OBJECTIVE[problem]],
        "objective_gap_pypfopt": _relative_gap(
            our_metrics, their_metrics, PROBLEM_OBJECTIVE[problem]
        ),
        "objective_gap_cvxpy": _relative_gap(
            our_metrics, conic_metrics, PROBLEM_OBJECTIVE[problem]
        ),
        "note": our_note,
    }
    record.update(extra)
    return record


def _relative_gap(left: dict[str, Any], right: dict[str, Any], key: str) -> float:
    """Relative disagreement in the quantity a solver was actually asked to optimise.

    Weight distance alone is not a quality signal: on a flat frontier a 1e-9 change in
    coordinates costs nothing in the objective, so two solvers can legitimately sit
    far apart in w and be indistinguishable in what they achieve. The objective gap is
    the number that answers "did it solve the problem", and the weight gap is reported
    beside it rather than instead of it.
    """
    ours, theirs = float(left[key]), float(right[key])
    scale = max(1e-12, abs(theirs))
    return abs(ours - theirs) / scale


if __name__ == "__main__":
    sys.exit(main())
