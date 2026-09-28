"""Shared pytest fixtures.

The C++/Python consistency tests need the reference-value tool built by CMake.
It is discovered either through ``QUANTRISK_REFERENCE_TOOL`` or by looking in
every ``build/<preset>/`` directory, so both the CMake developer path and the
``pip install -e .`` path work.

The session-scoped autouse fixture at the bottom protects something else: the frozen
evidence. ``scripts/build_evidence_manifest.py`` hashes 69 artifacts and
``verify_evidence_manifest.py`` answers "did anything move since", but neither mechanism can
see a test that moves one *during* the run — and one did, when the real-data study's offline
tests executed ``run.py`` in place. Every ``pytest`` then rewrote a committed artifact: new
timestamp, new provenance block, tree left dirty, and the manifest reporting VOLATILE for a
file nobody had deliberately regenerated.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Directories whose contents are evidence. A test may read them; none may write them.
FROZEN_EVIDENCE_ROOTS = (
    REPO_ROOT / "benchmarks",
    REPO_ROOT / "experiments",
    REPO_ROOT / "data" / "fixtures",
    REPO_ROOT / "evidence",
)

#: Build products and caches that live inside those trees and are not evidence.
EVIDENCE_IGNORED_PARTS = ("__pycache__", ".pytest_cache")


def _frozen_evidence_digest() -> dict[str, str]:
    """sha256 of every evidence file, keyed by repository path."""
    digest: dict[str, str] = {}
    for root in FROZEN_EVIDENCE_ROOTS:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or any(part in EVIDENCE_IGNORED_PARTS for part in path.parts):
                continue
            digest[str(path.relative_to(REPO_ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


@pytest.fixture(scope="session", autouse=True)
def no_test_writes_into_frozen_evidence() -> object:
    """Fail the whole session if running the suite changed an artifact.

    Asserted at teardown rather than watched continuously, because the point is not to catch a
    write in the act — it is to make a test that mutates the evidence it is supposed to verify
    impossible to merge quietly.
    """
    before = _frozen_evidence_digest()
    yield before
    after = _frozen_evidence_digest()
    changed = sorted(path for path in set(before) & set(after) if before[path] != after[path])
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    assert not (changed or added or removed), (
        f"the test run modified frozen evidence — changed: {changed}, added: {added}, "
        "removed: "
        f"{removed}. Scripts that write under `Path(__file__).parent / 'results'` resolve "
        "inside the repository; run a copy placed in a tmp_path directory instead."
    )


def _candidate_tools() -> list[Path]:
    from_env = os.environ.get("QUANTRISK_REFERENCE_TOOL")
    if from_env:
        return [Path(from_env)]
    return sorted((REPO_ROOT / "build").glob("*/quantrisk_reference_tool"))


@pytest.fixture(scope="session")
def reference_tool_path() -> Path:
    for candidate in _candidate_tools():
        if candidate.is_file():
            return candidate
    pytest.skip(
        "C++ reference tool not found; build it first with "
        "`cmake --preset dev && cmake --build --preset dev` "
        "or set QUANTRISK_REFERENCE_TOOL"
    )
    raise AssertionError  # pragma: no cover


@pytest.fixture(scope="session")
def cpp_reference(reference_tool_path: Path) -> dict:
    completed = subprocess.run(  # noqa: S603
        [str(reference_tool_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)
