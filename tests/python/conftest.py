"""Shared pytest fixtures.

The C++/Python consistency tests need the reference-value tool built by CMake.
It is discovered either through ``QUANTRISK_REFERENCE_TOOL`` or by looking in
every ``build/<preset>/`` directory, so both the CMake developer path and the
``pip install -e .`` path work.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


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
