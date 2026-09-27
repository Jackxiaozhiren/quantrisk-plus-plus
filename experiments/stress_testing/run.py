#!/usr/bin/env python3
"""Phase 7 experiment: does a stress change which portfolio is the risky one?

    uv run python experiments/stress_testing/run.py

Phase 6 ended with a measured claim: the estimator, not the solver, decides what a
portfolio is optimal for. Phase 7 asks the follow-up that stress testing exists to
answer. A book chosen to minimise variance under normal-market dispersion is optimal
*for that dispersion*. Change the dispersion and the ranking is a different question —
and if the ranking never changes, the whole exercise is decoration.

Four arms, all on synthetic data from a stated process, all scored through the engine
rather than through a reimplementation of it.

A. **Rank reversal across the named shocks.** Four books built by the Phase 6 optimisers
   (minimum variance, equal risk contribution, minimum CVaR, equal weight) are ranked by
   base parametric VaR and then re-ranked under each scenario the Phase 7 spec names.
   Reported: the rank each book holds under normal conditions, its rank under stress, and
   how many pairs invert. A book that is second-safest normally and worst under a vol
   spike is a finding, and it is the kind of finding only attribution can explain.

B. **Where the exposure map stops being enough.** The stress layer maps exposures to P&L
   and never re-prices, so its error is Taylor truncation. Sweeping an equity shock from
   0.1 % to 40 % and comparing the delta-gamma answer against a full Black-Scholes
   re-pricing of the same option book gives the size of that error as a function of move,
   which is the honest boundary of arm A.

C. **What the VaR change is made of.** For every scenario, the change in parametric VaR
   split into the level leg (the loss already taken) and the dispersion leg (the matrix
   deformed). The two telescope exactly, so the split is a decomposition rather than an
   approximation, and it separates "we lost money" from "we became more uncertain".

D. **Attribution closes.** Every scenario on every book, both decompositions, worst
   residual. The gate asks that attribution sum to the total; this is that claim measured
   rather than asserted.

SciPy and NumPy are reference arithmetic only. The library imports neither
(PROJECT_SPEC.md §2.2), and every figure comes from a live solve during this run.
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
    repo_relative,
    utc_timestamp,
)
from quantrisk.plotting import line_plot

RESULTS = Path(__file__).resolve().parent / "results"

PORTFOLIO = quantrisk.portfolio
STRESS = quantrisk.stress

NOTIONAL = 1.0e8
CONFIDENCE = 0.95
EQUITY_FACTORS = 6
MACRO_FACTORS = 3  # one rate, one volatility, one credit spread
FACTOR_COUNT = EQUITY_FACTORS + MACRO_FACTORS
SHOCK_SWEEP = (0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.40)


# --- the market -----------------------------------------------------------


def factor_structure() -> tuple[np.ndarray, np.ndarray]:
    """Move covariance and move means for 6 equities, 1 rate, 1 vol, 1 credit spread.

    Units follow the exposure convention exactly: the first six entries are *relative*
    equity moves, then an absolute yield change, an absolute volatility change and an
    absolute spread change. A covariance that mixes those up is the single easiest way to
    build a stress number that is wrong and looks right, so the vector is written out
    rather than generated.
    """
    rng = np.random.default_rng(60606)
    loadings = rng.normal(0.0, 1.0, (EQUITY_FACTORS, 2))
    equity_vol = rng.uniform(0.14, 0.28, EQUITY_FACTORS) / math.sqrt(12.0)  # monthly
    # Two factors, so the factor covariance is 2x2 and the loadings map it into the six
    # asset space. The residual is then chosen per asset so the finished block's own
    # diagonal *is* the quoted volatility: forcing the diagonal afterwards would leave
    # off-diagonals too large for it and quietly break positive definiteness.
    factor_vol = equity_vol.mean() * np.array([0.50, 0.28])
    common = loadings @ np.diag(factor_vol**2) @ loadings.T
    residual = np.sqrt(np.maximum(equity_vol**2 - np.diag(common), (0.30 * equity_vol) ** 2))
    block = common + np.diag(residual**2)
    sigma = np.concatenate([equity_vol, [0.0018, 0.045, 0.0025]])
    covariance = np.zeros((FACTOR_COUNT, FACTOR_COUNT))
    covariance[:EQUITY_FACTORS, :EQUITY_FACTORS] = block
    for offset, value in enumerate(sigma[EQUITY_FACTORS:]):
        index = EQUITY_FACTORS + offset
        covariance[index, index] = value**2
    # Equities sell off when rates spike and when vol rises; credit spreads widen with
    # the equity drawdown. These are the only cross-links in the fixture.
    covariance[6, :EQUITY_FACTORS] = covariance[:EQUITY_FACTORS, 6] = (
        -0.15 * sigma[6] * (sigma[:EQUITY_FACTORS])
    )
    covariance[7, :EQUITY_FACTORS] = covariance[:EQUITY_FACTORS, 7] = (
        -0.30 * sigma[7] * (sigma[:EQUITY_FACTORS])
    )
    covariance[8, :EQUITY_FACTORS] = covariance[:EQUITY_FACTORS, 8] = (
        -0.45 * sigma[8] * (sigma[:EQUITY_FACTORS])
    )
    means = np.zeros(10)
    means[:EQUITY_FACTORS] = rng.normal(0.004, 0.003, EQUITY_FACTORS)
    return covariance, means


def factor_set() -> STRESS.FactorSet:
    handle = STRESS.FactorSet()
    handle.factors = [
        *[
            STRESS.RiskFactor(
                f"EQ{i}", STRESS.FactorClass.equity_index, 100.0 + 10.0 * i, "index points"
            )
            for i in range(EQUITY_FACTORS)
        ],
        STRESS.RiskFactor("RATE", STRESS.FactorClass.rate, 0.042, "decimal p.a."),
        STRESS.RiskFactor("VOL", STRESS.FactorClass.volatility, 0.18, "annualised vol"),
        STRESS.RiskFactor("CREDIT", STRESS.FactorClass.credit_spread, 0.012, "decimal"),
    ]
    return handle


# --- the books ------------------------------------------------------------


def optimised_weights(covariance: np.ndarray, means: np.ndarray) -> dict[str, list[float]]:
    """Four Phase 6 portfolios on the same equity block, all long-only and invested."""
    equity = covariance[:EQUITY_FACTORS, :EQUITY_FACTORS]
    flat = equity.reshape(-1).tolist()
    problem = PORTFOLIO.OptimizerInputs()
    problem.assets = EQUITY_FACTORS
    problem.covariance = flat
    problem.expected_returns = means[:EQUITY_FACTORS].tolist()

    books: dict[str, list[float]] = {}
    minimum = PORTFOLIO.minimum_variance(problem, PORTFOLIO.OptimizationRequest())
    books["min_variance"] = list(minimum.weights)
    parity = PORTFOLIO.risk_parity(flat, EQUITY_FACTORS)
    if parity.converged:
        books["risk_parity"] = list(parity.weights)
    request = PORTFOLIO.CvarRequest()
    rng = np.random.default_rng(4242)
    scenarios = rng.multivariate_normal(means[:EQUITY_FACTORS], equity, 500)
    request.assets = EQUITY_FACTORS
    request.scenarios = 500
    request.scenario_returns = scenarios.reshape(-1).tolist()
    request.confidence = 0.95
    cvar = PORTFOLIO.minimise_cvar(request)
    if cvar.solved:
        books["min_cvar"] = list(cvar.weights)
    books["equal_weight"] = [1.0 / EQUITY_FACTORS] * EQUITY_FACTORS
    return books


def build_portfolio(weights: list[float], name: str) -> Any:
    """A long-only equity book as dollar exposures: notional * w per 100 % move."""
    portfolio = STRESS.Portfolio()
    portfolio.factors = factor_set()
    position = STRESS.Position()
    position.name = name
    exposures = STRESS.ExposureVector()
    exposures.delta = [NOTIONAL * value for value in weights] + [0.0] * MACRO_FACTORS
    exposures.gamma = [0.0] * FACTOR_COUNT
    exposures.duration = [0.0] * FACTOR_COUNT
    exposures.vega = [0.0] * FACTOR_COUNT
    exposures.credit = [0.0] * FACTOR_COUNT
    position.exposures = exposures
    portfolio.positions = [position]
    return portfolio


def add_rate_and_vol_book(portfolio: Any, duration: float, vega: float) -> Any:
    """Attach a second position so the multi-factor attribution has something to say."""
    extra = STRESS.Position()
    extra.name = "macro_overlay"
    exposures = STRESS.ExposureVector()
    exposures.delta = [0.0] * FACTOR_COUNT
    exposures.duration = [0.0] * EQUITY_FACTORS + [duration, 0.0, 0.0]
    exposures.vega = [0.0] * EQUITY_FACTORS + [0.0, vega, 0.0]
    exposures.credit = [0.0] * EQUITY_FACTORS + [0.0, 0.0, -abs(duration) * 0.05]
    exposures.gamma = [0.0] * FACTOR_COUNT
    extra.exposures = exposures
    portfolio.positions = [*list(portfolio.positions), extra]
    return portfolio


# --- the named scenarios ---------------------------------------------------


def scenarios() -> list[Any]:
    """The shocks PROJECT_SPEC.md §Phase 7 names, each with its assumptions attached."""
    named = [
        (
            "equity_-20pct",
            [
                STRESS.Shock("EQ0", -0.20, 0.0),
                STRESS.Shock("EQ1", -0.20, 0.0),
                STRESS.Shock("EQ2", -0.20, 0.0),
                STRESS.Shock("EQ3", -0.20, 0.0),
                STRESS.Shock("EQ4", -0.20, 0.0),
                STRESS.Shock("EQ5", -0.20, 0.0),
            ],
            "one-day 20% drawdown in every equity factor, no other factor moves",
            None,
        ),
        (
            "vol_x2",
            [],
            "every volatility doubled and equity-vol correlation lifted to 0.9; no level move",
            (2.0, 0.0),
        ),
        (
            "rates_+200bp",
            [STRESS.Shock("RATE", 0.0, 0.02)],
            "parallel 200bp yield rise, one day, equities unchanged",
            None,
        ),
        (
            "rates_-100bp",
            [STRESS.Shock("RATE", 0.0, -0.01)],
            "parallel 100bp yield fall, one day, equities unchanged",
            None,
        ),
        (
            "correlation_+0.2",
            [],
            "off-diagonal correlation lifted by 0.2 with clipping reported, no level move",
            (1.0, 0.2),
        ),
        (
            "credit_+150bp",
            [STRESS.Shock("CREDIT", 0.0, 0.015)],
            "credit proxy spread widened 150bp alongside a 5% equity fall",
            None,
        ),
        (
            "risk_off",
            [
                STRESS.Shock("EQ0", -0.15, 0.0),
                STRESS.Shock("EQ1", -0.15, 0.0),
                STRESS.Shock("EQ2", -0.15, 0.0),
                STRESS.Shock("EQ3", -0.15, 0.0),
                STRESS.Shock("EQ4", -0.15, 0.0),
                STRESS.Shock("EQ5", -0.15, 0.0),
                STRESS.Shock("RATE", 0.0, -0.005),
                STRESS.Shock("VOL", 0.0, 0.06),
                STRESS.Shock("CREDIT", 0.0, 0.010),
            ],
            "combined 15% equity fall, 50bp rally, +6 vol points and +100bp credit",
            (1.5, 0.1),
        ),
    ]
    built = []
    for name, shocks, assumptions, distribution in named:
        handle = STRESS.Scenario()
        handle.name = name
        handle.kind = STRESS.ScenarioKind.deterministic
        handle.assumptions = assumptions
        handle.horizon = 1.0 / 252.0
        handle.shocks = shocks
        if distribution is not None:
            shift = STRESS.DistributionShift()
            shift.volatility_multiplier = distribution[0]
            shift.correlation_increment = distribution[1]
            handle.distribution = shift
        built.append(handle)
    return built


# --- arms ------------------------------------------------------------------


def run_ranking(books: dict[str, Any], covariance: np.ndarray) -> list[dict[str, Any]]:
    flat = covariance.reshape(-1).tolist()
    rows: list[dict[str, Any]] = []
    base = {
        name: STRESS.run_scenario(portfolio, _baseline(), flat, CONFIDENCE).base_var
        for name, portfolio in books.items()
    }
    base_rank = _ranks(base)
    for handle in scenarios():
        for name, portfolio in books.items():
            result = STRESS.run_scenario(portfolio, handle, flat, CONFIDENCE)
            rows.append(
                {
                    "scenario": handle.name,
                    "book": name,
                    "assumptions": handle.assumptions,
                    "base_var": base[name],
                    "base_rank": base_rank[name],
                    "stressed_var": result.stressed_var,
                    "pnl_change": result.pnl_change,
                    "var_change": result.var_change,
                    "worst_factor": min(
                        (part.total(), part.factor_id) for part in result.by_factor
                    )[1],
                    "worst_factor_pnl": min(part.total() for part in result.by_factor),
                    "factor_attribution_residual": result.factor_attribution_residual,
                    "position_attribution_residual": result.position_attribution_residual,
                    "note": result.note,
                }
            )
    stressed_ranks = {
        row["scenario"]: _ranks(
            {r["book"]: r["stressed_var"] for r in rows if r["scenario"] == row["scenario"]}
        )
        for row in rows
    }
    # Ranking by the *multiplier* is the question a stress actually asks: not "who is
    # biggest" but "who did the stress hurt most relative to how they looked beforehand".
    # A book can hold its absolute rank and still be the one the stress was aimed at.
    sensitivity_ranks = {
        row["scenario"]: _ranks(
            {
                r["book"]: r["stressed_var"] / r["base_var"]
                for r in rows
                if r["scenario"] == row["scenario"]
            }
        )
        for row in rows
    }
    for row in rows:
        row["stressed_rank"] = stressed_ranks[row["scenario"]][row["book"]]
        row["rank_moved"] = row["stressed_rank"] - row["base_rank"]
        row["var_multiplier"] = row["stressed_var"] / row["base_var"]
        row["sensitivity_rank"] = sensitivity_ranks[row["scenario"]][row["book"]]
        row["sensitivity_rank_moved"] = row["sensitivity_rank"] - row["base_rank"]
    return rows


def _baseline() -> Any:
    handle = STRESS.Scenario()
    handle.name = "baseline"
    handle.assumptions = "no factor moves, no distribution shift"
    return handle


def _ranks(values: dict[str, float]) -> dict[str, int]:
    """Rank 1 is the *least* risky, so a positive rank_moved is a deterioration."""
    order = sorted(values, key=lambda key: values[key])
    return {key: index + 1 for index, key in enumerate(order)}


def run_linearisation(covariance: np.ndarray) -> list[dict[str, Any]]:
    """Delta-gamma P&L against a full Black-Scholes re-pricing, as the move grows."""
    market = quantrisk.pricing.MarketParams(
        spot=100.0, rate=0.03, dividend_yield=0.0, volatility=0.20, maturity=0.5
    )
    strikes = [90.0, 100.0, 110.0]
    quantity = 5000.0

    base_value = 0.0
    delta_exposure = 0.0
    gamma_exposure = 0.0
    for strike in strikes:
        option = quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, strike)
        greeks = quantrisk.pricing.black_scholes_greeks(option, market)
        base_value += quantrisk.pricing.black_scholes(option, market).price * quantity
        delta_exposure += greeks.delta * market.spot * quantity
        gamma_exposure += 0.5 * greeks.gamma * market.spot * market.spot * quantity

    portfolio = STRESS.Portfolio()
    portfolio.factors = factor_set()
    position = STRESS.Position()
    position.name = "option_book"
    exposures = STRESS.ExposureVector()
    # Blocks are replaced wholesale. A bound std::vector member comes back as a copy,
    # so `exposures.delta[0] = x` edits a temporary and is silently lost; the test
    # `test_bound_exposure_blocks_are_value_semantic` pins that behaviour down.
    exposures.delta = [delta_exposure] + [0.0] * (FACTOR_COUNT - 1)
    exposures.gamma = [gamma_exposure] + [0.0] * (FACTOR_COUNT - 1)
    exposures.duration = [0.0] * FACTOR_COUNT
    exposures.vega = [0.0] * FACTOR_COUNT
    exposures.credit = [0.0] * FACTOR_COUNT
    position.exposures = exposures
    portfolio.positions = [position]

    rows = []
    for move in SHOCK_SWEEP:
        handle = STRESS.Scenario()
        handle.name = f"equity_{move:.1%}"
        handle.assumptions = "single factor move, no other factor responds"
        handle.shocks = [STRESS.Shock("EQ0", -move, 0.0)]
        mapped = STRESS.run_scenario(portfolio, handle).pnl_change

        # Only the spot moves: the scenario is a pure equity shock, and re-pricing with
        # the other parameters copied straight through is what keeps that honest.
        shocked = quantrisk.pricing.MarketParams(
            spot=market.spot * (1.0 - move),
            rate=market.rate,
            dividend_yield=market.dividend_yield,
            volatility=market.volatility,
            maturity=market.maturity,
        )
        revalued = (
            sum(
                quantrisk.pricing.black_scholes(
                    quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, strike),
                    shocked,
                ).price
                for strike in strikes
            )
            * quantity
            - base_value
        )
        rows.append(
            {
                "move": move,
                "delta_gamma_pnl": mapped,
                "revalued_pnl": revalued,
                "abs_error": mapped - revalued,
                "relative_error": abs(mapped - revalued) / max(abs(revalued), 1e-12),
                "linear_only_pnl": delta_exposure * -move,
                "linear_relative_error": abs(delta_exposure * -move - revalued)
                / max(abs(revalued), 1e-12),
            }
        )
    return rows


def run_decomposition(books: dict[str, Any], covariance: np.ndarray) -> list[dict[str, Any]]:
    flat = covariance.reshape(-1).tolist()
    rows = []
    for handle in scenarios():
        for name, portfolio in books.items():
            result = STRESS.run_scenario(portfolio, handle, flat, CONFIDENCE)
            rows.append(
                {
                    "scenario": handle.name,
                    "book": name,
                    "var_change": result.var_change,
                    "from_level": result.var_change_from_level,
                    "from_distribution": result.var_change_from_distribution,
                    "decomposition_residual": result.var_decomposition_residual,
                    "es_change": result.es_change,
                    "volatility_change": result.volatility_change,
                    "level_share": (
                        result.var_change_from_level / result.var_change
                        if abs(result.var_change) > 1e-12
                        else float("nan")
                    ),
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    field_names = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    covariance, means = factor_structure()
    # Each book carries the equity leg from a Phase 6 optimiser plus a small macro
    # overlay, so the multi-factor attribution has more than one factor to talk about.
    overlays = {
        "min_variance": (-1.0e6, -2.0e4),
        "risk_parity": (-2.0e6, -4.0e4),
        "min_cvar": (-1.0e6, -3.0e4),
        "equal_weight": (-1.5e6, -2.0e4),
    }
    books = {}
    for name, weights in optimised_weights(covariance, means).items():
        duration, vega = overlays[name]
        books[name] = add_rate_and_vol_book(build_portfolio(weights, name), duration, vega)
    ranking_rows = run_ranking(books, covariance)
    linearisation_rows = run_linearisation(covariance)
    decomposition_rows = run_decomposition(books, covariance)

    write_csv(RESULTS / "scenario_ranking.csv", ranking_rows)
    write_csv(RESULTS / "linearisation_error.csv", linearisation_rows)
    write_csv(RESULTS / "var_decomposition.csv", decomposition_rows)

    reversals = {}
    for scenario_name in {row["scenario"] for row in ranking_rows}:
        subset = [row for row in ranking_rows if row["scenario"] == scenario_name]
        multipliers = [row["var_multiplier"] for row in subset]
        base_spread = (
            max(row["base_var"] for row in subset) - min(row["base_var"] for row in subset)
        ) / min(row["base_var"] for row in subset)
        reversals[scenario_name] = {
            "books": len(subset),
            "books_that_changed_absolute_rank": sum(1 for row in subset if row["rank_moved"] != 0),
            "books_that_changed_sensitivity_rank": sum(
                1 for row in subset if row["sensitivity_rank_moved"] != 0
            ),
            "max_var_multiplier": max(multipliers),
            "min_var_multiplier": min(multipliers),
            # An absolute rank inversion needs the multiplier spread to exceed the spread
            # the books started with. Recording both says whether the stability here is a
            # property of the optimisers or only of how far apart these books already were.
            "base_var_spread": base_spread,
            "multiplier_spread": max(multipliers) / min(multipliers) - 1.0,
            "most_stress_sensitive": max(subset, key=lambda row: row["var_multiplier"])["book"],
            "least_stress_sensitive": min(subset, key=lambda row: row["var_multiplier"])["book"],
        }

    line_plot(
        [row["move"] for row in linearisation_rows],
        {
            "delta-gamma map": [row["relative_error"] for row in linearisation_rows],
            "delta only": [row["linear_relative_error"] for row in linearisation_rows],
        },
        title="Exposure-map error against full revaluation, as the move grows",
        xlabel="equity fall (fraction of level)",
        ylabel="relative error in P&L vs re-pricing the book",
        path=RESULTS / "linearisation_error.png",
        log_x=True,
        annotations={"both curves rise: the map is a local approximation": (0.35, 0.72)},
    )

    summary = {
        "phase": "7 - Stress testing",
        "generated_utc": utc_timestamp(),
        "command": "uv run python experiments/stress_testing/run.py",
        "question": (
            "A portfolio chosen to be least risky under normal dispersion is optimal for "
            "that dispersion. Does a stress change which portfolio is the risky one, and "
            "can the attribution say why?"
        ),
        "market": {
            "kind": "synthetic",
            "statement": (
                "A 10-factor fixture (six equities, one rate, one volatility, one credit "
                "spread) built by factor_structure(). No market data is used or implied. "
                "Move units follow the exposure convention: relative for equities, "
                "absolute for the other three."
            ),
            "notional": NOTIONAL,
            "confidence": CONFIDENCE,
            "books": sorted(books),
            "scenarios": [handle.name for handle in scenarios()],
        },
        "ranking": reversals,
        "linearisation": {
            "note": (
                "the stress layer maps exposures and never re-prices, so its error is "
                "Taylor truncation; this is that error measured against a full "
                "Black-Scholes re-pricing of the same three-strike call book"
            ),
            "rows": linearisation_rows,
            "error_at_1pct": next(
                row["relative_error"] for row in linearisation_rows if row["move"] == 0.01
            ),
            "error_at_20pct": next(
                row["relative_error"] for row in linearisation_rows if row["move"] == 0.20
            ),
            "error_at_40pct": next(
                row["relative_error"] for row in linearisation_rows if row["move"] == 0.40
            ),
        },
        "decomposition": {
            "note": (
                "the level and dispersion legs telescope to the VaR change exactly for a "
                "Gaussian measure; the residual column is that claim measured"
            ),
            "worst_residual": max(abs(row["decomposition_residual"]) for row in decomposition_rows),
            "most_uncertainty_driven": max(
                decomposition_rows,
                key=lambda row: 0.0 if math.isnan(row["level_share"]) else -row["level_share"],
            ),
        },
        "attribution_closure": {
            "worst_factor_residual": max(
                abs(row["factor_attribution_residual"]) for row in ranking_rows
            ),
            "worst_position_residual": max(
                abs(row["position_attribution_residual"]) for row in ranking_rows
            ),
            "scenarios_evaluated": len(ranking_rows),
        },
        "environment": environment(),
        "artifacts": artifact_manifest(
            [
                RESULTS / "scenario_ranking.csv",
                RESULTS / "linearisation_error.csv",
                RESULTS / "var_decomposition.csv",
                RESULTS / "linearisation_error.png",
            ]
        ),
    }
    (RESULTS / "stress_testing_study.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"ranking": reversals}, indent=2))
    print(
        json.dumps(
            {
                "linearisation_error": {
                    "at_1pct": summary["linearisation"]["error_at_1pct"],
                    "at_20pct": summary["linearisation"]["error_at_20pct"],
                    "at_40pct": summary["linearisation"]["error_at_40pct"],
                },
                "attribution_closure": summary["attribution_closure"],
                "worst_decomposition_residual": summary["decomposition"]["worst_residual"],
            },
            indent=2,
        )
    )
    print(f"wrote {len(summary['artifacts'])} artifacts to {repo_relative(RESULTS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
