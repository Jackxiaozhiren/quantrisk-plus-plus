"""Phase 1 smoke surface: `import quantrisk` must prove the whole
C++ -> pybind11 -> Python path exists, and the package metadata must agree with
the C++ build it loaded.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
import quantrisk

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_METADATA_KEYS = {
    "version",
    "git_commit",
    "compiler",
    "arch",
    "os",
    "build_type",
    "cxx_standard",
    "cxx_flags",
}


def test_version_is_a_semver_string() -> None:
    version = quantrisk.version()
    parts = version.split(".")
    assert len(parts) == 3, version
    assert all(part.isdigit() for part in parts), version


def test_python_package_version_matches_pyproject() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    assert quantrisk.__version__ == pyproject["project"]["version"]
    assert quantrisk.version() == pyproject["project"]["version"]


def test_normal_cdf_smoke_contract() -> None:
    assert quantrisk.normal_cdf(0.0) == 0.5
    assert quantrisk.normal_pdf(0.0) == pytest.approx(0.3989422804014327)
    assert quantrisk.inverse_normal_cdf(0.5) == pytest.approx(0.0, abs=1e-15)


def test_build_metadata_reports_the_environment_that_produced_the_numbers() -> None:
    metadata = quantrisk.build_metadata()
    assert set(metadata) >= REQUIRED_METADATA_KEYS, sorted(metadata)
    assert metadata["cxx_standard"] == "C++20"
    assert metadata["version"] == quantrisk.version()
    # A release artifact must not be built from a dirty/unknown tree.
    assert metadata["git_commit"] not in {"", "unknown"}
    assert metadata["build_type"] in {"Release", "RelWithDebInfo", "Debug"}


def test_rng_is_constructible_with_the_documented_default_seed() -> None:
    rng = quantrisk.Rng()
    assert rng.seed == 42
    assert 0.0 <= rng.uniform01() < 1.0
    assert len(rng.standard_normal_vector(10)) == 10


def test_public_api_surface_is_exported() -> None:
    for name in ("Rng", "ValidationError", "normal_cdf", "stats", "build_metadata"):
        assert hasattr(quantrisk, name), name
    assert "version" in quantrisk.__all__
