"""Reproducibility metadata shared by every experiment and benchmark.

docs/validation_protocol.md §3 requires each artifact to carry the environment
that produced it. Doing that in one place keeps the number honest: a script
that forgets a field cannot silently publish a result that later turns out to
be unreproducible.
"""

from __future__ import annotations

import hashlib
import platform
import subprocess
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


def parse_porcelain_status(stdout: str) -> list[str]:
    """Paths touched in the working tree, from `git status --porcelain` output.

    Kept separate from the Git call so the parsing is testable on its own: every
    line is two status columns, a space, then the path, and a rename reports
    `old -> new` and must contribute only the *new* path.
    """
    paths = []
    for line in stdout.splitlines():
        entry = line[3:] if len(line) > 3 else ""
        if not entry:
            continue
        paths.append(entry.split(" -> ", 1)[1] if " -> " in entry else entry)
    return sorted(paths)


def _git(*arguments: str) -> str | None:
    """Git output, or None when Git cannot answer (no repo, no binary, no perms)."""
    try:
        completed = subprocess.run(  # noqa: S603, S607
            ["git", *arguments],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def working_tree_state() -> dict[str, Any]:
    """Uncommitted changes present at run time, as far as Git will tell us."""
    status = _git("status", "--porcelain")
    if status is None:
        return {"working_tree_dirty": None, "uncommitted_paths": []}
    paths = parse_porcelain_status(status)
    return {"working_tree_dirty": bool(paths), "uncommitted_paths": paths}


def describe_provenance(head: str | None, binary_commit: str, dirty: bool | None) -> str:
    """One sentence saying which commit the numbers actually belong to.

    `build_metadata()["git_commit"]` is captured at *configure* time, so on its own
    it credits whichever commit happened to be checked out when the build ran. A
    clean working tree makes that actively misleading -- the artifact would claim a
    commit that predates the code -- so the run-time HEAD and the binary's stamp are
    reported separately and the difference is stated here.
    """
    if head is None:
        return (
            f"git is unavailable here, so provenance rests on the configure-time "
            f"stamp alone: {binary_commit}"
        )
    if dirty:
        return (
            f"ran from {head} plus the uncommitted changes listed in uncommitted_paths; "
            f"the extension binary was configured at {binary_commit}"
        )
    if head != binary_commit:
        return (
            f"the working tree is clean at {head} but the extension binary was configured "
            f"at {binary_commit}; rebuild (uv pip install -e .) before trusting numbers "
            f"that depend on C++ sources"
        )
    return f"ran from a clean working tree at {head}, which is what the binary was built from"


def environment() -> dict[str, Any]:
    """Host facts that change numerical results or timings."""
    core = quantrisk.build_metadata()
    tree = working_tree_state()
    raw_head = _git("rev-parse", "--short=12", "HEAD")
    head = raw_head.strip() if raw_head else None
    return {
        "generated_at_utc": utc_timestamp(),
        "quantrisk_version": core["version"],
        "git_commit": head or core["git_commit"],
        "binary_git_commit": core["git_commit"],
        **tree,
        "provenance": describe_provenance(head, core["git_commit"], tree["working_tree_dirty"]),
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
                # Repo-relative, not absolute: a committed manifest must read the
                # same on every machine and must not publish a developer's home path.
                "path": repo_relative(resolved),
                "sha256": sha256_file(resolved),
                "bytes": str(resolved.stat().st_size),
            }
        )
    return entries
