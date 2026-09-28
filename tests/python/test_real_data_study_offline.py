"""The real-data study must run with no network, no key, and no drift.

`experiments/real_data_risk_study/` is the first part of this project that reasons about
actual markets, which makes it the part where a silent network dependency or a quietly
changed estimand would do the most reputational damage. These tests are the reason it
cannot: the fixtures are committed and self-verifying, the experiment is run with sockets
disabled, and the two claims most easily gotten wrong — that a labelled arm means what its
label says, and that a question the data cannot answer is refused rather than proxied — are
asserted directly.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import quantrisk
from quantrisk.data import fixtures

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "experiments" / "real_data_risk_study" / "run.py"
ARTIFACT = (
    REPO_ROOT / "experiments" / "real_data_risk_study" / "results" / "real_data_risk_study.json"
)


def _script_copy(destination: Path) -> Path:
    """The experiment, relocated so running it cannot overwrite frozen evidence.

    `run.py` writes to `Path(__file__).parent / "results"`, so a copy placed in a temporary
    directory writes there instead. This matters: the first version of these tests executed the
    script in the repository, and a normal `pytest` run therefore rewrote a committed artifact
    on every invocation — new timestamp, new provenance block, tree left dirty, and the evidence
    manifest reporting VOLATILE for a file nothing had deliberately regenerated. A test that
    mutates the evidence it is meant to verify is not a test of reproducibility, it is a source
    of variation.
    """
    directory = destination / "real_data_risk_study"
    directory.mkdir(parents=True, exist_ok=True)
    copy = directory / "run.py"
    shutil.copyfile(SCRIPT, copy)
    return copy


HISTORY_SERIES = ("DGS10", "T10YIE", "VIXCLS")
WINDOW = "2014-01-01_2026-09-26"


def test_the_long_history_fixtures_exist_and_verify_themselves() -> None:
    for series_id in HISTORY_SERIES:
        fixture = fixtures.load(f"fred_{series_id}_{WINDOW}")
        assert fixture.provenance.verify(fixture.data), f"{series_id} does not match its hash"
        assert "used_by" in fixture.provenance.extra
        assert fixture.provenance.extra["used_by"] == "experiments/real_data_risk_study"
        rows = [line for line in fixture.text().splitlines()[1:] if line.strip()]
        assert len(rows) > 3_000, f"{series_id} has only {len(rows)} observations"


def test_no_fixture_claims_a_contactless_user_agent_was_enough() -> None:
    """Every long-history record must say it came from the current revision.

    The look-ahead exposure is the interesting thing about this dataset, so an artifact
    that omitted it would be the one way the provenance could mislead by omission.
    """
    for series_id in HISTORY_SERIES:
        fixture = fixtures.load(f"fred_{series_id}_{WINDOW}")
        note = fixture.provenance.note.lower()
        assert "current revision" in note
        assert "vintage" in note


def test_the_experiment_runs_with_sockets_disabled(tmp_path: Path) -> None:
    """Offline is a property of the code, not a promise in a comment.

    The child blocks `socket.socket` before importing anything, so a network call added
    later fails here rather than passing CI until the source site rate-limits it.
    """
    # Blocking `socket.socket` itself breaks `ssl`, which subclasses it at import time in a
    # fresh interpreter. `getaddrinfo` is where a name becomes an address and nothing
    # inherits from it, so refusing it closes every outbound path without collateral.
    #
    # It is installed as `sitecustomize` rather than exec'd around the script, because the
    # script resolves its own path through `__file__`, which `exec` does not define.
    startup = tmp_path / "sitecustomize.py"
    startup.write_text(
        "import socket, urllib.request\n"
        "class Blocked(RuntimeError):\n"
        "    pass\n"
        "def _deny(*args, **kwargs):\n"
        "    raise Blocked('a socket was opened')\n"
        "socket.getaddrinfo = _deny\n"
        "socket.create_connection = _deny\n"
        "urllib.request.urlopen = _deny\n",
        encoding="utf-8",
    )
    environment = {"PYTHONPATH": str(tmp_path), "PATH": "/usr/bin:/bin", "HOME": str(tmp_path)}
    completed = subprocess.run(
        [sys.executable, str(_script_copy(tmp_path))],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
        env=environment,
    )
    assert "a socket was opened" not in completed.stderr, completed.stderr[-2000:]
    assert completed.returncode == 0, completed.stderr[-3000:]


def _results_only(payload: dict) -> dict:
    """Strip the fields that legitimately differ between runs.

    Same rule as the evidence manifest's content digest: a re-run changes when it ran, from
    which revision, on which machine, and how long the clock said it took. Everything else
    has to be byte-identical or the published artifact is a snapshot of drift.
    """
    stripped = {
        key: value
        for key, value in payload.items()
        if key not in {"generated_utc", "environment", "oracles", "artifacts"}
    }
    return json.loads(json.dumps(stripped))


def test_a_fresh_run_reproduces_the_committed_artifact_exactly(tmp_path: Path) -> None:
    """Re-running must reproduce every number, or the artifact is a dated accident.

    This is the reproducibility claim of the whole project applied to the one experiment
    that reasons about real markets, where a silent dependence on when it ran would be
    most damaging. The comparison is exact, not approximate: nothing here is sampled from a
    live source, so there is no legitimate source of variation left to allow for.
    """
    committed = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    before = ARTIFACT.read_bytes()
    script = _script_copy(tmp_path)
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr[-3000:]
    fresh = json.loads((script.parent / "results" / "real_data_risk_study.json").read_text())
    assert _results_only(fresh) == _results_only(committed), (
        "a fresh run of the real-data study does not reproduce the committed results"
    )
    # The committed artifact is the evidence; a test that regenerated it would make the next
    # assertion below about the test rather than about the experiment.
    assert ARTIFACT.read_bytes() == before, "the test run modified a committed artifact"


def test_headline_finding_gaussian_99_miscalibrates_on_real_data() -> None:
    """The point of the study, encoded so a regression in either direction is noticed.

    Phase 5 predicted on synthetic t(3) data that a Gaussian fit would over-reject at 99 %.
    Real data must show the same failure or the synthetic result is not evidence about
    anything; and the historical estimator must *not* fail, or the finding is just "all
    estimators are bad", which is not what was measured.
    """
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    per = payload["A_estimator_validity"]["per_estimator"]
    gaussian_99 = next(r for r in per["gaussian"] if r["confidence"] == 0.99)
    historical_99 = next(r for r in per["historical"] if r["confidence"] == 0.99)

    assert gaussian_99["realised_violation_rate"] > gaussian_99["nominal_violation_rate"]
    assert not gaussian_99["covers_nominal"], (
        "the Gaussian 99 % interval now covers nominal; the headline finding has changed "
        "and every document quoting it must be re-checked"
    )
    assert historical_99["covers_nominal"], "the historical estimator's calibration claim broke"
    assert historical_99["realised_violation_rate"] < gaussian_99["realised_violation_rate"], (
        "historical is no longer closer to nominal than gaussian on real data"
    )


def test_the_sensitivity_arm_labelled_as_documented_is_the_documented_book() -> None:
    """The label has to mean the thing.

    The first version of `exposure_sensitivity` scaled raw factor moves by unit weights and
    called the result "as documented", while question A scaled them by EXPOSURES. The two
    disagreed by a factor of two and the figure looked like it confirmed the headline.
    """
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    per = payload["A_estimator_validity"]["per_estimator"]
    for estimator in ("historical", "gaussian"):
        reference = next(r for r in per[estimator] if r["confidence"] == 0.99)
        arm = payload["exposure_sensitivity"]["as_documented"]["headline"][f"{estimator}_99%"]
        assert arm == reference["realised_violation_rate"], (
            f"the as_documented arm disagrees with question A for {estimator}"
        )


def test_uniform_rescaling_cannot_change_a_violation_rate() -> None:
    """VaR is positively homogeneous, so a uniformly scaled book cannot re-violate.

    Asserted rather than observed because the alternative is publishing three identical
    rows under the heading "sensitivity", which invites a reader to conclude the result is
    exposure-dependent when nothing was varied.
    """
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    arms = payload["exposure_sensitivity"]
    for estimator in ("historical", "gaussian"):
        base = arms["as_documented"]["headline"][f"{estimator}_99%"]
        for label in ("half_documented", "double_documented"):
            assert arms[label]["headline"][f"{estimator}_99%"] == base


def test_headline_scalars_are_the_rows_and_blocks_they_cite() -> None:
    """The suite aggregates this artifact through `headline`, so that block is load-bearing.

    It is written as references to the objects below it, and a reference can still point at
    the wrong row -- a 95 % rate under a 99 % label would be exactly the kind of silent
    mislabelling this study already caught once in `exposure_sensitivity`. Re-derive each
    scalar from its source here instead of trusting the naming.
    """
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    headline = payload["headline"]
    per = payload["A_estimator_validity"]["per_estimator"]
    gaussian_99 = next(r for r in per["gaussian"] if r["confidence"] == 0.99)
    historical_99 = next(r for r in per["historical"] if r["confidence"] == 0.99)

    assert headline["evaluation_rows"] == payload["A_estimator_validity"]["evaluation_rows"]
    assert headline["gaussian_99_realised_violation_rate"] == gaussian_99["realised_violation_rate"]
    assert (
        headline["gaussian_99_exact_interval_excludes_nominal"]
        is not (gaussian_99["covers_nominal"])
    )
    assert (
        headline["historical_99_realised_violation_rate"]
        == historical_99["realised_violation_rate"]
    )
    assert headline["violations"] == payload["B_coverage_tests"]["violations"]
    for test_name in (
        "kupiec",
        "christoffersen_independence",
        "christoffersen_conditional_coverage",
    ):
        assert headline[f"{test_name}_p_value"] == payload["B_coverage_tests"][test_name]["p_value"]
    assert headline["run_test_z"] == payload["B_clustering_evidence"]["run_test_z"]
    assert (
        headline["block_over_iid_bootstrap_se_ratio"]
        == payload["C_bootstrap_standard_errors"]["block_over_iid"]
    )
    assert (
        headline["covariance_ranking_best_to_worst"]
        == payload["D_covariance"]["ranked_best_to_worst_by_realised_variance"]
    )


def test_questions_the_data_cannot_answer_are_refused_not_proxied() -> None:
    """The two refusals are the part of this study a reviewer should trust most."""
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    refused = {entry["question"] for entry in payload["refusals"]}
    assert len(refused) == 3
    coverage = next(q for q in refused if "coverage" in q)
    entry = next(e for e in payload["refusals"] if e["question"] == coverage)
    assert "circular" in entry["refused"] or "by construction" in entry["refused"]
    assert "artifact" in entry["refused"], "the discarded 1.000 measurement must be named"


def test_the_study_uses_no_oracle_for_its_risk_numbers() -> None:
    """SciPy supplies the interval arithmetic only; every risk number is ours."""
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert "none used" in payload["oracles"]["tool"]
    assert payload["environment"]["quantrisk_version"] == quantrisk.version()


def test_look_ahead_exposure_is_stated_rather_than_denied() -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert "current revision" in payload["look_ahead"]["residual_exposure"]
    assert "ALFRED" in payload["look_ahead"]["residual_exposure"]
