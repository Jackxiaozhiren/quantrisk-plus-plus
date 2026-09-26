"""Reproducibility metadata shared by every experiment and benchmark.

docs/validation_protocol.md §3 requires each artifact to carry the environment
that produced it. Doing that in one place keeps the number honest: a script
that forgets a field cannot silently publish a result that later turns out to
be unreproducible.
"""

from __future__ import annotations

import hashlib
import platform
import sys
from datetime import UTC, datetime
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

import quantrisk

#: python/quantrisk/experiments/metadata.py -> repository root
REPO_ROOT = Path(__file__).resolve().parents[3]


def repo_relative(path: str | Path) -> str:
    """Path as seen from the repository, or absolute when it is outside it."""
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


#: Optional oracles; only the ones actually importable are recorded.
ORACLE_PACKAGES = (
    "numpy",
    "scipy",
    "pandas",
    "matplotlib",
    "QuantLib",
    "PyPortfolioOpt",
    "cvxpy",
    "osqp",
    "scikit-learn",
    "statsmodels",
)


def package_versions() -> dict[str, str]:
    """Versions of every numerical library that took part in a run."""
    versions: dict[str, str] = {
        "python": sys.version.split()[0],
        "quantrisk": quantrisk.version(),
    }
    for name in ORACLE_PACKAGES:
        try:
            versions[name] = importlib_metadata.version(name)
        except importlib_metadata.PackageNotFoundError:
            continue
    return versions


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def environment() -> dict[str, Any]:
    """Host facts that change numerical results or timings."""
    core = quantrisk.build_metadata()
    return {
        "generated_at_utc": utc_timestamp(),
        "quantrisk_version": core["version"],
        "git_commit": core["git_commit"],
        "cpp_compiler": core["compiler"],
        "cpp_arch": core["arch"],
        "cpp_os": core["os"],
        "cpp_build_type": core["build_type"],
        "cpp_standard": core["cxx_standard"],
        "cpp_flags": core["cxx_flags"],
        "python_platform": platform.platform(),
        "python_machine": platform.machine(),
        "packages": package_versions(),
    }


def artifact_manifest(paths: list[Path]) -> list[dict[str, str]]:
    """Hashes of the artifacts a script just wrote, for the evidence chain."""
    entries: list[dict[str, str]] = []
    for path in paths:
        resolved = Path(path)
        if not resolved.exists():
            continue
        entries.append(
            {
                "path": str(resolved),
                "sha256": sha256_file(resolved),
                "bytes": str(resolved.stat().st_size),
            }
        )
    return entries
