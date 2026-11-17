"""The drift gate is worth testing only if it objects to the failure the digest gate cannot see.

The distinction is the whole point. `verify_evidence_manifest` re-hashes the frozen artifacts, and
the site build already refuses an artifact whose bytes disagree with the manifest. Both stay green
when a figure is edited in the artifact *and the manifest's two digests are recomputed with it* —
the evidence chain is internally consistent again. What has drifted is the published page, which
still renders the old figure. One test below constructs exactly that state in a temporary tree and
requires the drift gate to object while the digest gate stays green.

The first test is the guard behind the controlled plant. It checks the current tree against the
*committed* lock, so a plant that changes an artifact's figure without re-freezing the lock makes
it fail, and restoring the figure makes it pass. The lock is a baseline at a named revision, not a
computed-in-test quantity; that is what makes the plant meaningful.
"""

from __future__ import annotations

import json
from pathlib import Path

from quantrisk.experiments.evidence import content_digest
from quantrisk.experiments.metadata import REPO_ROOT, sha256_file
from quantrisk.experiments.registry import TASKS_BY_ID
from quantrisk.interface import drift, site

from tests.python.test_interface_site import _temp_root

# A rendered study whose headline holds a figure unique inside its own artifact and absent from
# every plant anchor and every claim the documents print, so the plant isolates this one gate.
DRIFT_TASK = "restrike_gamma_map"
DRIFT_ARTIFACT = "experiments/restrike_gamma_map/results/restrike_gamma_map.json"
DRIFT_FIGURE = "0.6924"
DRIFT_REPLACEMENT = "0.6934"
FROZEN_LOCK = REPO_ROOT / "build" / "site.lock"


def test_the_committed_lock_detects_a_figure_that_drifted_in_an_artifact(tmp_path: Path) -> None:
    """Guard behind plant `site-lock-catches-a-manifest-silent-figure-change`.

    The baseline is the committed lock, and the subject is the artifact bytes themselves: a plant
    that edits a figure in a tracked artifact changes its digest away from the frozen one. Reading
    the digest directly, rather than through a build the manifest could refuse, keeps this guard
    about the lock's claim and not about manifest consistency — the two jobs are separate.
    """
    assert FROZEN_LOCK.is_file(), "the committed site lock is missing; there is no baseline"
    # Naming the locked artifact keeps this guard's reading closure tied to the plant's target.
    assert TASKS_BY_ID[DRIFT_TASK].artifact == DRIFT_ARTIFACT
    document = drift._read_lock(FROZEN_LOCK)["pages"]
    for name, frozen in document.items():
        task_id = Path(name).stem
        task = TASKS_BY_ID.get(task_id)
        if task is None:
            # The index page has no source artifact; its digest is checked by the rebuild test.
            continue
        actual = sha256_file(REPO_ROOT / task.artifact)
        assert frozen["artifact_sha256"] == actual, (
            f"{task_id}: source {task.artifact} hashed {frozen['artifact_sha256']} at freeze, "
            f"but the tree now holds {actual}; the page's provenance has drifted"
        )


def test_a_manifest_silent_figure_change_leaves_the_digest_gate_green(tmp_path: Path) -> None:
    """A figure can move with both digests in sync; only the page-level gate sees the stale page."""
    root = _temp_root(tmp_path / "tree")
    task = TASKS_BY_ID[DRIFT_TASK]
    artifact = root / task.artifact
    original = artifact.read_text(encoding="utf-8")
    assert original.count(DRIFT_FIGURE) == 1, "the anchor is no longer unique in its artifact"

    # Freeze the baseline while the tree is still intact.
    lock = tmp_path / "site.lock"
    drift.freeze(tmp_path / "frozen", lock, root)

    # Now move one figure and re-freeze both digests, as a legitimate regeneration would.
    artifact.write_text(original.replace(DRIFT_FIGURE, DRIFT_REPLACEMENT), encoding="utf-8")
    manifest_path = root / site.MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = next(e for e in manifest["artifacts"] if e["path"] == task.artifact)
    original_digests = (entry["sha256"], entry["content_sha256"])
    entry["sha256"] = sha256_file(artifact)
    entry["content_sha256"] = content_digest(artifact)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # The digest gate's own criterion — both frozen digests match the moved artifact — stays green.
    assert entry["sha256"] == sha256_file(artifact)
    assert entry["content_sha256"] == content_digest(artifact)

    problems = drift.check(tmp_path / "rebuilt", lock, root)
    assert problems, "the rebuilt page still matched the lock after the figure moved"
    assert any(f"{task.task_id}.html" in line for line in problems), problems

    # Restore both the artifact and its digests, as rolling back a bad regeneration would.
    artifact.write_text(original, encoding="utf-8")
    entry["sha256"], entry["content_sha256"] = original_digests
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    assert drift.check(tmp_path / "restored", lock, root) == [], (
        "restoring the figure did not bring the page back to the frozen baseline"
    )


def test_a_drifted_page_is_named_and_a_bad_lock_is_refused(tmp_path: Path) -> None:
    """Every drifted page is reported by name, and a lock that cannot be read refuses the check."""
    root = _temp_root(tmp_path / "tree")
    lock = tmp_path / "site.lock"
    drift.freeze(tmp_path / "frozen", lock, root)

    task = TASKS_BY_ID[DRIFT_TASK]
    artifact = root / task.artifact
    artifact.write_text(
        artifact.read_text(encoding="utf-8").replace(DRIFT_FIGURE, DRIFT_REPLACEMENT),
        encoding="utf-8",
    )
    manifest_path = root / site.MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = next(e for e in manifest["artifacts"] if e["path"] == task.artifact)
    entry["sha256"] = sha256_file(artifact)
    entry["content_sha256"] = content_digest(artifact)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    problems = drift.check(tmp_path / "rebuilt", lock, root)
    assert any(f"{task.task_id}.html" in line for line in problems), problems

    lock.write_text('{"schema": "something-else", "pages": {}}', encoding="utf-8")
    try:
        drift.check(tmp_path / "again", lock, root)
    except drift.DriftRefused:
        pass
    else:
        raise AssertionError("a lock with the wrong schema was accepted as a baseline")
