#!/usr/bin/env python3
"""Phase 11 experiment: do the Phase 5 and Phase 6 conclusions survive real data?

    uv run python scripts/run_benchmark_suite.py --only real_data_risk_study
    uv run python experiments/real_data_risk_study/run.py

Everything else in `experiments/` runs on synthetic data whose truth is known, which is what
makes a bias measurable but also what keeps every conclusion one step away from an empirical
claim. `docs/limitations.md` #28 says so plainly. This script exists to pay part of that debt:
it re-runs the same estimators and the same coverage tests on **real daily market
observations**, and reports where they hold and where they do not.

The data is real; the book is not. Three FRED series are used as risk factors — the 10-year
Treasury par yield, the 10-year Treasury inflation-protected breakeven, and the CBOE volatility
index — and the portfolio is a fixed set of notional exposures to those factors. That is the
honest framing: the factor moves are observations, the exposures are assumptions, and no
number here describes a trade that happened.

Why these three series and not others: they are *prints*, not estimates. FRED also carries
macro aggregates like `UNRATE`, which are revised after publication, and a backtest on the
current revision of a revised series silently trades on information nobody had at the time.
Market-observed rates and indices are corrected only for data errors. That removes the worst
look-ahead exposure available without an ALFRED key; it does not remove all of it, and
`refusals` records what remains.

Four questions, each answerable, plus one that is not:

A. **Estimator validity.** Historical versus Gaussian VaR and ES, calibrated on a trailing
   window and scored out of sample on real factor moves. The synthetic t(3) arm predicted the
   Gaussian estimator would over-reject at 99 %. Does it, on data nobody generated?

B. **Do the coverage tests discriminate?** Kupiec and Christoffersen on the resulting violation
   series. Volatility clustering is the standard empirical claim about returns; if the
   independence test does not reject materially more often than its nominal size here, that is
   evidence against the machinery, not for it.

C. **Does the block bootstrap earn its keep?** iid versus moving-block coverage of the 90 %
   interval for the sample VaR, on real returns. The synthetic arm showed the iid design
   collapsing under clustering; real data is where that matters.

D. **Which covariance estimator produces the better book?** Rolling minimum-variance weights
   from each estimator, scored on realised portfolio variance over the following window. This
   is a *relative* comparison and is reported as one.

E. **Refused: the informed-solver cost ratio.** Phase 6 could say "estimating the covariance
   costs 1.13x-1.26x what an informed solver would carry" only because the forward covariance
   was known in closed form. Real data has no such object. The honest output is the statement
   that the question cannot be answered here, not a proxy dressed up as one.

Every number is produced by the C++ core. NumPy is used to align dates and to compute the
exact binomial interval, which is a published formula and not a risk estimate.
"""

from __future__ import annotations

import csv
import io
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import quantrisk
import scipy.stats
from quantrisk.data import fixtures
from quantrisk.experiments.metadata import (
    artifact_manifest,
    environment,
    package_versions,
    repo_relative,
    sha256_file,
    utc_timestamp,
)

RESULTS = Path(__file__).resolve().parent / "results"

# (fixture series id, human name, how a level becomes a factor move, factor class)
FACTORS = (
    ("DGS10", "10y treasury nominal yield", "level difference in percentage points", "rate"),
    (
        "T10YIE",
        "10y TIPS breakeven inflation",
        "level difference in percentage points",
        "inflation",
    ),
    ("VIXCLS", "CBOE volatility index", "log difference", "volatility"),
)

# Exposures per unit of factor move, in P&L currency. The nominal yield and the breakeven
# are both Treasury quotes and move together, which makes the covariance genuinely
# ill-conditioned -- that is not a nuisance to be cleaned up but part of the point, since
# near-collinearity is exactly where the estimators disagree. Chosen to be a plausible
# mixed book rather than fitted to produce a result; `exposure_sensitivity` re-runs the
# headline claims under three other exposure sets.
EXPOSURES = {"DGS10": -4.0e5, "T10YIE": -2.0e5, "VIXCLS": -2.5e5}

WINDOW = 250
STEP = 5
CONFIDENCE_LEVELS = (0.95, 0.99)
BOOTSTRAP_DRAWS = 1_000
BOOTSTRAP_STUDIES = 60
BOOTSTRAP_SAMPLE = 500
BLOCK_LENGTH = 10
BOOTSTRAP_INTERVAL_LEVEL = 0.90
FORWARD_WINDOW = 20
EWMA_LAMBDA = 0.94  # the RiskMetrics daily default, not tuned
SEED = 20260928


def load_series(series_id: str, start: str, end: str) -> list[tuple[str, float]]:
    """Read one committed fixture, verifying its own provenance on the way in."""
    name = f"fred_{series_id}_{start}_{end}"
    fixture = fixtures.load(name)
    if not fixture.provenance.verify(fixture.data):
        raise RuntimeError(f"fixture {name} does not match its recorded sha256")
    rows = list(csv.reader(io.StringIO(fixture.text())))
    out: list[tuple[str, float]] = []
    for row in rows[1:]:
        if len(row) < 2 or row[1].strip() in ("", "."):
            continue  # FRED's placeholder for a missing print; never a zero
        out.append((row[0], float(row[1])))
    return out


def factor_moves() -> dict[str, list[tuple[str, float]]]:
    """Aligned daily factor moves, keyed by series id."""
    levels = {
        series_id: load_series(series_id, "2014-01-01", "2026-09-26") for series_id, *_ in FACTORS
    }
    dated: dict[str, dict[str, float]] = {key: dict(value) for key, value in levels.items()}
    common = set.intersection(*(set(mapping) for mapping in dated.values()))
    calendar = sorted(common)
    moves: dict[str, list[tuple[str, float]]] = {series_id: [] for series_id in dated}
    for previous, current in zip(calendar, calendar[1:], strict=False):
        for series_id, mapping in dated.items():
            if series_id == "VIXCLS":
                move = math.log(mapping[current] / mapping[previous])
            else:
                move = mapping[current] - mapping[previous]
            moves[series_id].append((current, move))
    return moves


def _gaussian_quoted(moves: list[float], level: float) -> list[float]:
    """The Gaussian VaR each trailing window would have quoted for the day after it."""
    return [
        quantrisk.risk.gaussian_var(moves[start : start + WINDOW], level).value
        for start in range(0, len(moves) - WINDOW - 1, STEP)
    ]


def rolling_var_scores(moves: list[float]) -> dict[str, Any]:
    """Out-of-sample violation rates for the historical and Gaussian estimators.

    Both estimators are scored against the same causally calibrated returns, so a
    difference between them is a difference in the estimator and not in the evaluation
    set. The interval is SciPy's exact Clopper-Pearson, used as a reference rather than
    reimplemented: an earlier hand-rolled bisection here inverted the bounds, which is a
    failure mode a published closed form does not have.
    """
    scored: dict[str, Any] = {}
    evaluated_count = 0
    for level in CONFIDENCE_LEVELS:
        evaluated, historical = rolling_var_series(moves, level)
        evaluated_count = len(evaluated)
        quoted = {"historical": historical, "gaussian": _gaussian_quoted(moves, level)}
        for name, var_series in quoted.items():
            hits = sum(1 for value, var in zip(evaluated, var_series, strict=True) if -value > var)
            trials = len(evaluated)
            nominal = 1.0 - level
            interval = scipy.stats.binomtest(hits, trials).proportion_ci(
                confidence_level=0.95, method="exact"
            )
            scored.setdefault(name, []).append(
                {
                    "confidence": level,
                    "nominal_violation_rate": nominal,
                    "realised_violation_rate": hits / trials,
                    "violations": hits,
                    "exact_95_interval_low": float(interval.low),
                    "exact_95_interval_high": float(interval.high),
                    "covers_nominal": float(interval.low) <= nominal <= float(interval.high),
                    "trials": trials,
                }
            )
    for rows in scored.values():
        rows.sort(key=lambda row: row["confidence"])
    return {"per_estimator": scored, "evaluation_rows": evaluated_count}


def rolling_var_series(moves: list[float], level: float) -> tuple[list[float], list[float]]:
    """Out-of-sample pairs of (return actually observed, VaR quoted for it).

    Each VaR is calibrated on the `WINDOW` observations that precede the return it is
    scored against, so nothing looks forward. Backtesting an in-sample VaR instead would
    report coverage of a fit, not of a policy.
    """
    returns_evaluated: list[float] = []
    var_series: list[float] = []
    for start in range(0, len(moves) - WINDOW - 1, STEP):
        sample = moves[start : start + WINDOW]
        var_series.append(quantrisk.risk.historical_var(sample, level).value)
        returns_evaluated.append(moves[start + WINDOW])
    return returns_evaluated, var_series


def coverage_tests(moves: list[float]) -> dict[str, Any]:
    """Kupiec and Christoffersen on a real, causally calibrated 95 % VaR series."""
    evaluated, var_series = rolling_var_series(moves, 0.95)
    report = quantrisk.risk.backtest_var(evaluated, var_series, 0.95)
    kupiec = report.kupiec
    independence = report.independence
    conditional = report.conditional
    return {
        "observations": len(evaluated),
        "violations": int(kupiec.exceptions),
        "kupiec": {
            "statistic": kupiec.statistic,
            "p_value": kupiec.p_value,
            "reject_at_5_percent": bool(kupiec.p_value < 0.05),
        },
        "christoffersen_independence": {
            "statistic": independence.statistic,
            "p_value": independence.p_value,
            "reject_at_5_percent": bool(independence.p_value < 0.05),
        },
        "christoffersen_conditional_coverage": {
            "statistic": conditional.statistic,
            "p_value": conditional.p_value,
            "reject_at_5_percent": bool(conditional.p_value < 0.05),
        },
    }


def clustered_violation_evidence(moves: list[float]) -> dict[str, Any]:
    """How much of the violation series is bunched, independent of any test.

    A test can fail to reject for two reasons: the process really is independent, or the
    history is too short. This separates them by counting runs directly, on the same
    causally calibrated series the coverage tests use.
    """
    evaluated, var_series = rolling_var_series(moves, 0.95)
    flags = [1 if -value > level else 0 for value, level in zip(evaluated, var_series, strict=True)]
    hits = sum(flags)
    trials = len(flags)
    runs = 1 + sum(1 for earlier, later in zip(flags, flags[1:], strict=False) if earlier != later)
    expected_runs = 1.0 + (2.0 * hits * (trials - hits)) / trials
    variance = (
        2.0
        * hits
        * (trials - hits)
        * (2.0 * hits * (trials - hits) - trials)
        / (trials**2 * (trials - 1.0))
    )
    z = (runs - expected_runs) / math.sqrt(variance) if variance > 0 else float("nan")
    return {
        "violations": hits,
        "observations": trials,
        "runs": runs,
        "expected_runs_if_independent": expected_runs,
        "run_test_z": z,
        "reading": (
            "fewer runs than expected means violations arrive in bursts, which is what the "
            "Christoffersen independence test looks for; the run count is a direct measure "
            "and does not depend on the sample being large"
        ),
    }


def bootstrap_standard_errors(moves: list[float]) -> dict[str, Any]:
    """iid versus moving-block standard error of a real-data VaR estimate.

    The synthetic arm in Phase 5 could measure *coverage*, because it knew the process and
    could compute the true VaR from a two-million-observation block. Real data offers no
    independent truth: the only candidate is the full-sample VaR, and resampling the same
    series to test an interval for it is circular -- the intervals cover by construction and
    a 100 % result would be an artifact, not a finding. That question is therefore refused
    (see `refusals`) and replaced by one that needs no truth.

    If daily P&L is clustered, an iid resample destroys the clustering and the resulting
    bootstrap distribution is too narrow, so its standard error understates the sampling
    variability of the estimate. The moving-block design keeps runs of consecutive days
    intact and does not. The ratio of the two is a direct, truth-free measure of how much
    the iid assumption costs here, and it is the same phenomenon the synthetic arm isolated
    with a design it could actually score.
    """
    out: dict[str, Any] = {"subsample": BOOTSTRAP_SAMPLE, "replicate_studies": BOOTSTRAP_STUDIES}
    per_design: dict[str, list[float]] = {"iid": [], "moving_block": []}
    rng = np.random.default_rng(SEED)
    for study in range(BOOTSTRAP_STUDIES):
        picks = rng.choice(len(moves), size=BOOTSTRAP_SAMPLE, replace=False)
        sample = [moves[index] for index in sorted(picks)]
        for label, kind, block_length in (
            ("iid", quantrisk.risk.BootstrapKind.IID, 0),
            ("moving_block", quantrisk.risk.BootstrapKind.MOVING_BLOCK, BLOCK_LENGTH),
        ):
            estimate = quantrisk.risk.bootstrap_var(
                sample,
                0.95,
                BOOTSTRAP_DRAWS,
                BOOTSTRAP_INTERVAL_LEVEL,
                kind,
                block_length,
                SEED + study,
            )
            per_design[label].append(estimate.standard_error)
    iid_mean = float(np.mean(per_design["iid"]))
    block_mean = float(np.mean(per_design["moving_block"]))
    out["iid"] = {"mean_standard_error": iid_mean}
    out["moving_block"] = {"mean_standard_error": block_mean, "block_length": BLOCK_LENGTH}
    out["block_over_iid"] = block_mean / iid_mean if iid_mean > 0 else float("nan")
    out["reading"] = (
        "a ratio above 1 means the iid design reports a tighter interval than the block "
        "design on the same data; how far above 1 is how much the iid assumption understates "
        "the uncertainty of a real VaR estimate"
    )
    return out


def covariance_out_of_sample(moves_by_factor: dict[str, list[float]]) -> dict[str, Any]:
    """Which covariance estimator produces the better book, scored on realised variance."""
    ids = list(moves_by_factor)
    matrix = np.column_stack([moves_by_factor[key] for key in ids])
    estimators = {
        "sample": lambda flat, assets, observations: quantrisk.portfolio.sample_covariance(
            flat, assets, observations
        ),
        "ewma": lambda flat, assets, observations: quantrisk.portfolio.ewma_covariance(
            flat, assets, observations, EWMA_LAMBDA
        ),
        "shrinkage": lambda flat, assets, observations: quantrisk.portfolio.shrinkage_covariance(
            flat, assets, observations
        ),
    }
    rows: list[dict[str, Any]] = []
    for start in range(0, len(matrix) - WINDOW - FORWARD_WINDOW, STEP):
        history = matrix[start : start + WINDOW]
        forward = matrix[start + WINDOW : start + WINDOW + FORWARD_WINDOW]
        flat = history.reshape(-1).tolist()
        for name, estimator in estimators.items():
            estimate = estimator(flat, len(ids), WINDOW)
            # The core returns the matrix row-major and flat, which is what the solver
            # wants; the diagnostics below need the square form.
            flat_covariance = np.asarray(estimate.values, dtype=float)
            covariance = flat_covariance.reshape(len(ids), len(ids))
            solution = quantrisk.PortfolioOptimizer(
                covariance.reshape(-1).tolist(), assets=len(ids)
            ).minimum_variance()
            weights = np.asarray(solution.weights, dtype=float)
            realised = forward @ weights
            rows.append(
                {
                    "window_start": start,
                    "estimator": name,
                    "realised_portfolio_variance": float(np.mean(realised**2)),
                    "predicted_variance": float(weights @ covariance @ weights),
                    # 1 / sum(w^2) is a property of the weight vector, not a risk estimate,
                    # so it is computed here rather than expected from the solver.
                    "effective_assets": float(1.0 / np.sum(weights**2)),
                }
            )
    summary: dict[str, Any] = {}
    for name in estimators:
        chosen = [row for row in rows if row["estimator"] == name]
        realised = np.array([row["realised_portfolio_variance"] for row in chosen])
        predicted = np.array([row["predicted_variance"] for row in chosen])
        summary[name] = {
            "windows": len(chosen),
            "mean_realised_variance": float(realised.mean()),
            "median_realised_variance": float(np.median(realised)),
            "mean_prediction_error": float(np.mean(predicted - realised)),
            "mean_effective_assets": float(np.mean([row["effective_assets"] for row in chosen])),
        }
    ranked = sorted(summary, key=lambda name: summary[name]["mean_realised_variance"])
    return {
        "per_estimator": summary,
        "ranked_best_to_worst_by_realised_variance": ranked,
        "note": (
            "lower realised portfolio variance is better. This is a relative ranking of the "
            "estimators as inputs to one objective; it is not a claim that any of them is "
            "close to a true covariance, because no such object is observable."
        ),
    }


def exposure_sensitivity(moves_by_factor: dict[str, list[float]]) -> dict[str, Any]:
    """Do the headline claims depend on the exposures, which are an assumption?

    The factor moves are observed; the book is invented. Every arm below therefore scales
    the *documented* exposures rather than replacing them, so `as_documented` reproduces
    the headline numbers exactly and any arm that does not is a real sensitivity rather
    than a different book. The first version of this function multiplied the raw factor
    moves by unit weights and labelled the result "as documented", which made it disagree
    with question A by a factor of two while appearing to confirm it.
    """
    ordered = list(moves_by_factor)
    base = np.column_stack([moves_by_factor[key] for key in ordered])
    documented = np.array([EXPOSURES[key] for key in ordered], dtype=float)
    scales = {
        "as_documented": documented,
        "half_documented": 0.5 * documented,
        "double_documented": 2.0 * documented,
        "rate_only": documented * np.array([1.0, 0.0, 0.0]),
        "inflation_only": documented * np.array([0.0, 1.0, 0.0]),
        "volatility_only": documented * np.array([0.0, 0.0, 1.0]),
        "sign_flipped": -documented,
    }
    # Uniform scaling cannot change a violation rate at all: VaR is positively homogeneous,
    # so halving every exposure halves both the quoted VaR and the P&L it is compared
    # against. Those arms are therefore kept as an invariance check on real data rather than
    # presented as a sensitivity, which is what three identical rows would otherwise look like.
    out: dict[str, Any] = {}
    for label, loadings in scales.items():
        pnl = (base * loadings).sum(axis=1).tolist()
        if not any(loadings):
            out[label] = {"note": "all exposures zero, no risk to measure"}
            continue
        scored = rolling_var_scores(pnl)["per_estimator"]
        out[label] = {
            "per_estimator": scored,
            "headline": {
                f"{name}_{row['confidence']:.0%}": row["realised_violation_rate"]
                for name in ("historical", "gaussian")
                for row in scored.get(name, [])
            },
        }
    return out


def make_figure(scored: dict[str, Any], sensitivity: dict[str, Any], path: Path) -> str:
    """Violation rate against nominal, with the exact interval that decides the claim.

    The point of the figure is the interval, not the point estimate: the Gaussian 99 % bar
    is only a finding because its interval misses the nominal line. A bar chart without the
    intervals would show a difference and hide whether anything rules out none.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return "not generated (matplotlib unavailable)"

    panels = (
        ("the documented three-factor book (question A)", scored),
        ("each factor alone, same estimator and level", sensitivity),
    )
    figure, axes = plt.subplots(1, 2, figsize=(12.0, 4.8))
    for axis, (title, source) in zip(axes, panels, strict=True):
        positions: list[float] = []
        labels: list[str] = []
        rates: list[float] = []
        lows: list[float] = []
        highs: list[float] = []
        nominals: list[float] = []
        index = 0
        for name in ("historical", "gaussian"):
            rows = source.get(name, []) if isinstance(source, dict) else []
            for row in rows:
                if "realised_violation_rate" not in row:
                    continue
                positions.append(index)
                factor = row.get("factor", "")
                suffix = f"\n{factor}" if factor else ""
                labels.append(f"{name} {row['confidence']:.0%}{suffix}")
                rates.append(row["realised_violation_rate"])
                lows.append(row["exact_95_interval_low"])
                highs.append(row["exact_95_interval_high"])
                nominals.append(row["nominal_violation_rate"])
                index += 1
        if not positions:
            axis.set_axis_off()
            continue
        error_low = [rate - low for rate, low in zip(rates, lows, strict=True)]
        error_high = [high - rate for rate, high in zip(rates, highs, strict=True)]
        axis.bar(positions, rates, width=0.55, color="#2f6f9f", alpha=0.85)
        axis.errorbar(
            positions,
            rates,
            yerr=[error_low, error_high],
            fmt="none",
            ecolor="black",
            elinewidth=1.2,
            capsize=4,
        )
        for position, nominal in zip(positions, nominals, strict=True):
            axis.hlines(nominal, position - 0.3, position + 0.3, color="crimson", linewidth=1.4)
        axis.set_xticks(positions)
        axis.set_xticklabels(labels, fontsize=7, rotation=30, ha="right")
        axis.set_yscale("log")
        axis.set_ylabel("realised violation rate")
        axis.set_title(title, fontsize=10)
    for axis in axes:
        axis.margins(y=0.15)
    figure.text(
        0.5,
        0.015,
        "red tick = nominal violation rate; black bar = 95 % exact Clopper-Pearson interval. "
        "A bar whose interval misses its tick is a significant miscalibration.",
        ha="center",
        fontsize=7.5,
    )
    figure.tight_layout(rect=(0.0, 0.045, 1.0, 1.0))
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return "generated"


def _score_row(
    estimator_scores: dict[str, Any], estimator: str, confidence: float
) -> dict[str, Any]:
    """One row of question A's table, selected by estimator and confidence level.

    The rows are a list ordered by confidence, so an index of `1` means "99%" only for as
    long as nobody adds a 97.5% arm. Selecting on the recorded `confidence` keeps a headline
    that says 99 attached to a row that is one.
    """
    rows = estimator_scores["per_estimator"][estimator]
    return next(row for row in rows if row["confidence"] == confidence)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    moves = factor_moves()
    aligned_dates = moves["DGS10"]
    print(
        f"aligned factor moves: {len(aligned_dates)} daily observations "
        f"({aligned_dates[0][0]} .. {aligned_dates[-1][0]})"
    )

    by_factor = {key: [value for _, value in moves[key]] for key, *_ in FACTORS}
    ordered = list(by_factor)
    stacked = np.column_stack([by_factor[key] for key in ordered])
    loadings = np.array([EXPOSURES[key] for key in ordered], dtype=float)
    book = (stacked * loadings).sum(axis=1).tolist()
    dates = [date for date, _ in moves[ordered[0]]]

    estimator_scores = rolling_var_scores(book)
    coverage = coverage_tests(book)
    clustering = clustered_violation_evidence(book)
    bootstrap = bootstrap_standard_errors(book)
    covariance = covariance_out_of_sample(by_factor)
    sensitivity = exposure_sensitivity(by_factor)
    # The sensitivity block claims `as_documented` is the same book question A scored. If
    # it ever stops being so, the labels are lying again, so make that a crash.
    published = {
        "historical": _score_row(estimator_scores, "historical", 0.99),
        "gaussian": _score_row(estimator_scores, "gaussian", 0.99),
    }
    for name, row in published.items():
        if (
            sensitivity["as_documented"]["headline"][f"{name}_99%"]
            != row["realised_violation_rate"]
        ):
            raise RuntimeError(
                f"exposure_sensitivity(as_documented) no longer reproduces question A for "
                f"the {name} estimator: "
                f"{sensitivity['as_documented']['headline'][f'{name}_99%']} != "
                f"{row['realised_violation_rate']}"
            )
    historical_99 = published["historical"]
    gaussian_99 = published["gaussian"]
    for uniform in ("half_documented", "double_documented"):
        for name, row in published.items():
            if sensitivity[uniform]["headline"][f"{name}_99%"] != row["realised_violation_rate"]:
                raise RuntimeError(
                    f"positive homogeneity of VaR broken on real data: {uniform} differs from "
                    f"as_documented for the {name} estimator, which cannot happen for a "
                    "uniformly scaled book"
                )

    payload: dict[str, Any] = {
        "phase": "11 - real-data risk study",
        "generated_utc": utc_timestamp(),
        "command": "uv run python experiments/real_data_risk_study/run.py",
        "question": (
            "The Phase 5 and Phase 6 conclusions were measured on synthetic data whose truth "
            "is known. Which of them survive on real daily market observations?"
        ),
        # The suite aggregates headline numbers by key path, and a path into a list ordered
        # by confidence level is a path that breaks silently. Every scalar here is therefore
        # a *reference* to the object below it, not a rounded copy: the artifact manifest
        # lists them under `derived_from`, and `test_real_data_study_offline.py` re-digs each
        # one and asserts equality, so a headline that drifts from its source fails the run
        # rather than just the reading.
        "headline": {
            "evaluation_rows": estimator_scores["evaluation_rows"],
            "gaussian_99_realised_violation_rate": gaussian_99["realised_violation_rate"],
            "gaussian_99_exact_interval_excludes_nominal": not gaussian_99["covers_nominal"],
            "historical_99_realised_violation_rate": historical_99["realised_violation_rate"],
            "violations": coverage["violations"],
            "kupiec_p_value": coverage["kupiec"]["p_value"],
            "christoffersen_independence_p_value": coverage["christoffersen_independence"][
                "p_value"
            ],
            "christoffersen_conditional_coverage_p_value": coverage[
                "christoffersen_conditional_coverage"
            ]["p_value"],
            "run_test_z": clustering["run_test_z"],
            "block_over_iid_bootstrap_se_ratio": bootstrap["block_over_iid"],
            "covariance_ranking_best_to_worst": covariance[
                "ranked_best_to_worst_by_realised_variance"
            ],
            "derived_from": [
                "A_estimator_validity.per_estimator.<estimator>[confidence=0.99]",
                "B_coverage_tests",
                "B_clustering_evidence.run_test_z",
                "C_bootstrap_standard_errors.block_over_iid",
                "D_covariance.ranked_best_to_worst_by_realised_variance",
            ],
        },
        "data": {
            "kind": "real, market-observed, current revision",
            "factors": [
                {"series_id": sid, "name": nm, "move_definition": mv, "class": cls}
                for sid, nm, mv, cls in FACTORS
            ],
            "observations": len(dates),
            "first_date": dates[0],
            "last_date": dates[-1],
            "window": WINDOW,
            "step": STEP,
            "book": {
                "exposures": EXPOSURES,
                "statement": (
                    "the factor moves are observations; the exposures are an assumption. No "
                    "number in this artifact describes a trade that happened"
                ),
            },
            "fixture_sha256": {
                f"fred_{sid}_2014-01-01_2026-09-26.csv": sha256_file(
                    fixtures.FIXTURE_ROOT / f"fred_{sid}_2014-01-01_2026-09-26.csv"
                )
                for sid, *_ in FACTORS
            },
        },
        "look_ahead": {
            "mitigation": (
                "series chosen because they are prints rather than estimates: FRED revises "
                "macro aggregates, which would let a current-revision backtest see the future"
            ),
            "residual_exposure": (
                "values are the current revision, not the vintage published on each date. A "
                "correction to a historical print would be invisible here; removing that "
                "residue needs an ALFRED key and fetch_vintage"
            ),
        },
        "A_estimator_validity": estimator_scores,
        "B_coverage_tests": coverage,
        "B_clustering_evidence": clustering,
        "C_bootstrap_standard_errors": bootstrap,
        "D_covariance": covariance,
        "exposure_sensitivity": sensitivity,
        "refusals": [
            {
                "question": (
                    "how much does estimating the covariance cost versus an informed solver?"
                ),
                "refused": (
                    "Phase 6 could answer this because the forward covariance was known in "
                    "closed form. Real data has no observable true covariance, and substituting "
                    "the full-sample estimate would smuggle the future into the comparison. "
                    "Question D reports a relative ranking instead, and says it is one."
                ),
            },
            {
                "question": (
                    "does the block bootstrap reach its nominal coverage on real data, as it "
                    "was shown not to on clustered synthetic data?"
                ),
                "refused": (
                    "coverage needs a truth independent of the sample being resampled. The "
                    "Phase 5 arm had one because the process was known analytically. Here the "
                    "only candidate is the full-sample VaR, and intervals built by resampling "
                    "that same series cover it by construction -- a measured 1.000 coverage "
                    "was produced this way and discarded as an artifact. Question C compares "
                    "the two designs' standard errors instead, which needs no truth."
                ),
            },
            {
                "question": "is this portfolio profitable?",
                "refused": (
                    "there is no return here. The exposures are assumed, not traded, and the "
                    "project makes no profitability claim anywhere (PROJECT_SPEC.md §4)."
                ),
            },
        ],
        "environment": environment(),
        "oracles": {
            "tool": "none used; every number comes from the C++ core",
            "versions": package_versions(),
        },
    }

    csv_path = RESULTS / "real_data_violations.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "factor", "move"])
        for factor in by_factor:
            for date, value in zip(dates, by_factor[factor], strict=True):
                writer.writerow([date, factor, f"{value:.10g}"])

    book_path = RESULTS / "real_data_book_pnl.csv"
    with book_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "pnl"])
        for date, value in zip(dates, book, strict=True):
            writer.writerow([date, f"{value:.6f}"])

    figure_path = RESULTS / "real_data_violation_coverage.png"
    single_factor_rows = {
        name: [
            {**row, "factor": arm.replace("_only", "")}
            for arm in ("rate_only", "inflation_only", "volatility_only")
            for row in sensitivity[arm]["per_estimator"][name]
            if row["confidence"] == 0.99
        ]
        for name in ("historical", "gaussian")
    }
    figure_status = make_figure(estimator_scores["per_estimator"], single_factor_rows, figure_path)
    payload["figure_status"] = figure_status
    payload["artifacts"] = artifact_manifest([csv_path, book_path, figure_path])
    json_path = RESULTS / "real_data_risk_study.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"A": estimator_scores["per_estimator"], "B": coverage}, indent=2)[:2000])
    print(
        json.dumps({"D_ranking": covariance["ranked_best_to_worst_by_realised_variance"]}, indent=2)
    )
    print(f"wrote {repo_relative(json_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
