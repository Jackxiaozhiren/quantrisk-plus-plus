"""The real-data numbers are quoted in prose, so prose is where they will go wrong.

`experiments/real_data_risk_study/results/real_data_risk_study.json` is the source of truth for
finding 4. README.md and docs/findings.md restate it in sentences, and a restated figure is a
second owner of the same fact — the failure mode this project has already been bitten by repeatedly
(docs/integrity_audit.md). Rather than trust the prose, each figure it prints is parsed back out of
the text and compared with the artifact, so a stale digit in a paragraph fails the suite the same
way a renamed key does.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = (
    REPO_ROOT / "experiments" / "real_data_risk_study" / "results" / "real_data_risk_study.json"
)
README = REPO_ROOT / "README.md"
FINDINGS = REPO_ROOT / "docs" / "findings.md"
PHASE_6_ARTIFACT = (
    REPO_ROOT
    / "experiments"
    / "portfolio_optimization"
    / "results"
    / "portfolio_optimisation_study.json"
)


def _payload() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_the_real_data_headline_rates_are_quoted_as_the_artifact_computes_them() -> None:
    """The Gaussian rate is quoted twice, so it is checked twice; the rest lives in finding 4.

    README.md carries only the headline arm — one rate and its interval — because a table row is
    not a results section. docs/findings.md carries both arms. Asserting the full set against the
    README would force prose into the table just to satisfy a test, which is the wrong direction.
    """
    headline = _payload()["headline"]
    gaussian = headline["gaussian_99_realised_violation_rate"]
    historical = headline["historical_99_realised_violation_rate"]

    readme = README.read_text(encoding="utf-8")
    assert f"{gaussian:.3%}" in readme, "README.md does not print the Gaussian 99 % rate"
    findings = FINDINGS.read_text(encoding="utf-8")
    for name, value in (("Gaussian", gaussian), ("historical", historical)):
        assert f"{value:.3%}" in findings, f"docs/findings.md does not print the {name} rate"


def test_the_exact_interval_endpoints_in_prose_are_the_ones_the_artifact_reports() -> None:
    """The interval *is* the claim, so a rounded endpoint is a changed claim.

    These are the third decimal of a Clopper-Pearson interval computed by `scipy.stats.binomtest`,
    and rounding to two would sometimes move the lower bound across the 1 % nominal rate — which
    is the entire finding.
    """
    payload = _payload()
    rows = payload["A_estimator_validity"]["per_estimator"]
    gaussian_99 = next(row for row in rows["gaussian"] if row["confidence"] == 0.99)
    historical_99 = next(row for row in rows["historical"] if row["confidence"] == 0.99)
    assert not gaussian_99["covers_nominal"], "the Gaussian arm now covers nominal"
    assert historical_99["covers_nominal"], "the historical arm no longer covers nominal"

    gaussian_pair = (
        f"{gaussian_99['exact_95_interval_low']:.3%}",
        f"{gaussian_99['exact_95_interval_high']:.3%}",
    )
    historical_pair = (
        f"{historical_99['exact_95_interval_low']:.3%}",
        f"{historical_99['exact_95_interval_high']:.3%}",
    )
    readme = README.read_text(encoding="utf-8")
    assert f"[{gaussian_pair[0]}, {gaussian_pair[1]}]" in readme, (
        "README omits the Gaussian interval"
    )
    findings = FINDINGS.read_text(encoding="utf-8")
    for low, high in (gaussian_pair, historical_pair):
        assert f"[{low}, {high}]" in findings, (
            f"docs/findings.md omits the interval [{low}, {high}]"
        )


def test_the_test_statistics_quoted_in_prose_match_the_artifact() -> None:
    payload = _payload()
    coverage = payload["B_coverage_tests"]
    clustering = payload["B_clustering_evidence"]
    bootstrap = payload["C_bootstrap_standard_errors"]

    assert not coverage["kupiec"]["reject_at_5_percent"]
    assert not coverage["christoffersen_independence"]["reject_at_5_percent"]
    assert not coverage["christoffersen_conditional_coverage"]["reject_at_5_percent"]

    quoted = {
        "Kupiec": f"{coverage['kupiec']['p_value']:.3f}",
        "independence": f"{coverage['christoffersen_independence']['p_value']:.3f}",
        "conditional coverage": f"{coverage['christoffersen_conditional_coverage']['p_value']:.3f}",
        "runs test z": f"{abs(clustering['run_test_z']):.2f}",
        "block/iid ratio": f"{bootstrap['block_over_iid']:.3f}",
    }
    text = FINDINGS.read_text(encoding="utf-8")
    for name, value in quoted.items():
        assert value in text, f"docs/findings.md does not print the {name} as {value}"
    # A negative result has to be called one. "none rejects" is the sentence the finding rests on.
    assert re.search(r"none rejects|no test rejects", text), "the non-rejection is not stated"


def test_the_covariance_ranking_quoted_in_prose_is_the_one_the_artifact_reports() -> None:
    ranking = _payload()["D_covariance"]["ranked_best_to_worst_by_realised_variance"]
    assert ranking == ["ewma", "sample", "shrinkage"], (
        "the real-data ranking changed; every paragraph about the synthetic winner is now wrong"
    )
    rendered = " < ".join(ranking)
    for document in (README, FINDINGS):
        assert rendered in document.read_text(encoding="utf-8"), (
            f"{document.name} does not state the ranking as {rendered}"
        )

    # The prose claims this *contradicts* the Phase 6 synthetic arm, and quotes Phase 6's mean
    # variance ratio per estimator. Recompute both: the means, and the ordering they imply.
    # Asserting on `headline.best_cell` instead would be wrong in a way a reader would not
    # notice — the single best cell is `window_125/sample`, because shrinkage wins the short
    # windows and loses the long ones, which is Phase 6's own finding.
    synthetic = json.loads(PHASE_6_ARTIFACT.read_text(encoding="utf-8"))
    by_estimator: dict[str, list[float]] = {}
    for cell, fields in synthetic["estimation_cost"]["by_window_and_estimator"].items():
        estimator = cell.split("/", 1)[1]
        by_estimator.setdefault(estimator, []).append(fields["variance_ratio_vs_informed"])
    means = {name: sum(values) / len(values) for name, values in by_estimator.items()}
    assert (
        len(by_estimator["shrinkage"]) == len(by_estimator["sample"]) == len(by_estimator["ewma"])
    ), "the synthetic grid is not balanced, so a mean over windows is not a comparison"
    synthetic_ranking = sorted(means, key=means.get)
    assert synthetic_ranking == ["shrinkage", "sample", "ewma"], (
        "Phase 6's mean ranking is now "
        f"{synthetic_ranking}; the 'ends trade places' sentence breaks"
    )
    for estimator, value in means.items():
        assert f"{value:.3f}" in FINDINGS.read_text(encoding="utf-8"), (
            f"docs/findings.md does not print Phase 6's mean ratio for {estimator} as {value:.3f}"
        )
    # The claim that makes the finding interesting: same middle, opposite ends.
    assert synthetic_ranking[0] == ranking[-1] and synthetic_ranking[-1] == ranking[0]
    assert synthetic_ranking[1] == ranking[1] == "sample"


def test_the_refused_questions_are_named_in_prose_as_the_artifact_records_them() -> None:
    refusals = _payload()["refusals"]
    assert len(refusals) == 3
    text = FINDINGS.read_text(encoding="utf-8")
    for phrase in ("informed solver", "truth independent", "profitable"):
        assert phrase in text, f"docs/findings.md does not name the refusal behind {phrase!r}"
    # The discarded circular coverage figure is a confession. If the prose drops it, the artifact
    # is the only place recording that a 1.000 was measured and thrown away.
    assert "1.000" in text


def test_the_sample_size_quoted_in_prose_is_the_scored_days_not_the_history() -> None:
    """3,177 daily observations produce 586 scored out-of-sample days; mixing them is a 5x error."""
    payload = _payload()
    scored = payload["A_estimator_validity"]["evaluation_rows"]
    assert scored == payload["B_coverage_tests"]["observations"]
    assert scored != payload["data"]["observations"]
    for document in (README, FINDINGS):
        text = document.read_text(encoding="utf-8")
        assert f"{scored} out-of-sample days" in text, (
            f"{document.name} does not say {scored} scored days"
        )

    # The window is only stated once, in findings.md, and it is stated as a span of years — so it
    # has to be derived from the dates the artifact reports rather than repeated from memory.
    data = payload["data"]
    years = (
        int(data["last_date"][:4])
        - int(data["first_date"][:4])
        + (int(data["last_date"][5:7]) - int(data["first_date"][5:7])) / 12
    )
    claimed = re.search(r"(\d+\.\d+)-year sample", FINDINGS.read_text(encoding="utf-8"))
    assert claimed, "docs/findings.md no longer states the observation window"
    assert abs(float(claimed.group(1)) - years) < 0.25, (
        f"prose says {claimed.group(1)} years, the fixture spans {years:.2f}"
    )
    assert payload["D_covariance"]["per_estimator"]["sample"]["windows"] == 582
    assert "582 rolling windows" in FINDINGS.read_text(encoding="utf-8")


def test_the_factor_series_named_in_prose_are_the_ones_the_artifact_loaded() -> None:
    payload = _payload()
    series = {entry["series_id"] for entry in payload["data"]["factors"]}
    assert series == {"DGS10", "T10YIE", "VIXCLS"}, (
        f"the study loads {sorted(series)}; the prose names par yield, breakeven and VIX"
    )
    # Named in the finding, where a reader decides whether the three factors are a sensible
    # risk-factor set; the README points here rather than duplicating the list.
    text = FINDINGS.read_text(encoding="utf-8")
    for phrase in ("par yield", "breakeven", "VIX"):
        assert phrase in text, f"docs/findings.md does not name the {phrase} series"
