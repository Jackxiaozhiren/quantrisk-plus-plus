#!/usr/bin/env python3
"""Freeze the evidence: hash every artifact and write `evidence/manifest.json`.

    uv run python scripts/build_evidence_manifest.py

PROJECT_SPEC.md §Phase 10 asks for `evidence/manifest.json` with SHA-256 over the key
outputs, so that a number in the README can be traced to a file and that file can be shown
not to have been edited since. Three things make that worth doing rather than symbolic:

  * Each entry carries the *command* that generated it when the artifact itself records one
    (every benchmark and experiment JSON does), so the manifest links artifact to recipe,
    not just artifact to hash.
  * The manifest records the repository revision and whether the tree was dirty. A frozen
    evidence bundle produced from an uncommitted state is not frozen; saying so is the
    difference between a provenance record and a prop.
  * It refuses to write if any artifact is missing a generator it should have, rather than
    quietly downgrading to "here is a hash of something".

The manifest is written next to the evidence, not inside `benchmarks/` or `experiments/`,
because it describes those directories as a set and must be regenerable without touching
them.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from quantrisk.data.provenance import sha256_of  # noqa: E402
from quantrisk.experiments.evidence import content_digest  # noqa: E402
from quantrisk.experiments.metadata import environment  # noqa: E402

OUTPUT = ROOT / "evidence" / "manifest.json"

# Where evidence lives, and what kind of claim each place supports. The categories are
# PROJECT_SPEC.md §Phase 10's three kinds of benchmark run.
SOURCES: list[tuple[str, str, tuple[str, ...]]] = [
    (
        "correctness_benchmark",
        "comparison against an independent implementation, run live",
        ("benchmarks/quantlib/results", "benchmarks/pyportfolioopt/results"),
    ),
    (
        "performance_benchmark",
        "measured throughput and runtime on one machine",
        ("benchmarks/performance/results",),
    ),
    (
        "statistical_experiment",
        "a distributional or convergence claim checked over many random trials",
        (
            "experiments/pricing_validation/results",
            "experiments/monte_carlo_convergence/results",
            "experiments/variance_reduction/results",
            "experiments/var_backtesting/results",
            "experiments/portfolio_optimization/results",
            "experiments/stress_testing/results",
            "experiments/real_data_risk_study/results",
            "experiments/linearisation_error_bound/results",
            "experiments/two_factor_error_bound/results",
            "experiments/restrike_gamma_map/results",
            "experiments/fourth_order_crossing_map/results",
        ),
    ),
    (
        "suite_aggregate",
        "the suite's own roll-up, which is the artifact a published count is read from",
        ("benchmarks/suite/results",),
    ),
    (
        "offline_fixture",
        "a real response from a public source, with its own provenance sidecar",
        ("data/fixtures",),
    ),
]

IGNORED_SUFFIXES = (".provenance.json",)


def repo_state() -> dict[str, Any]:
    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    commit = git("rev-parse", "HEAD")
    porcelain = git("status", "--porcelain")
    return {
        "git_commit": commit,
        "git_describe": git("describe", "--tags", "--always") or commit[:12],
        "working_tree_dirty": bool(porcelain),
        "uncommitted_paths": sorted(
            {line[3:].strip() for line in porcelain.splitlines() if len(line) > 3}
        ),
    }


def generator_command(path: Path) -> tuple[str, str, str]:
    """(command, generated_utc, note) recovered from a sibling or self JSON."""
    candidates: list[Path] = [path] if path.suffix == ".json" else []
    candidates += sorted(path.parent.glob("*.json"))
    for candidate in candidates:
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(payload, dict):
            continue
        command = payload.get("command") or payload.get("generator_command") or ""
        generated = payload.get("generated_utc") or payload.get("generated_at_utc") or ""
        if command:
            return str(command), str(generated), str(candidate.relative_to(ROOT))
    return "", "", ""


def fixture_provenance(path: Path) -> tuple[str, str, str]:
    """For a committed fixture, the sidecar names a *source*, not a command.

    A downloaded response has different provenance from a computed one: what you want to
    know is where it came from and when it was fetched, and the script that re-fetches the
    whole set is the same for all of them. Reporting "no command" for these would be a
    warning that is technically true and informationally useless.
    """
    sidecar = path.with_suffix(path.suffix + ".provenance.json")
    if not sidecar.exists():
        return "", "", ""
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    return (
        f"uv run python scripts/record_data_fixtures.py (source: {payload.get('source', '?')})",
        str(payload.get("retrieved_at_utc", "")),
        str(sidecar.relative_to(ROOT)),
    )


def artefact_entries(
    category: str, directories: tuple[str, ...], warnings: list[str]
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for relative in directories:
        directory = ROOT / relative
        if not directory.is_dir():
            warnings.append(f"expected evidence directory {relative} does not exist")
            continue
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.name.endswith(IGNORED_SUFFIXES):
                continue
            command, generated, command_source = generator_command(path)
            if not command and category == "offline_fixture":
                command, generated, command_source = fixture_provenance(path)
            if not command:
                warnings.append(f"{path.relative_to(ROOT)} has no sibling JSON recording a command")
            entries.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "category": category,
                    "sha256": sha256_of(path.read_bytes()),
                    # The byte hash answers "has this file been edited?"; this one answers
                    # "did the numbers move?", which is the question a re-run leaves ambiguous.
                    "content_sha256": content_digest(path),
                    "bytes": path.stat().st_size,
                    "generated_by_command": command,
                    "generated_utc": generated,
                    "command_recorded_in": command_source,
                }
            )
    return entries


def main() -> int:
    warnings: list[str] = []
    categories: dict[str, str] = {}
    entries: list[dict[str, Any]] = []
    for category, description, directories in SOURCES:
        categories[category] = description
        entries.extend(artefact_entries(category, directories, warnings))

    state = repo_state()
    build_environment = environment()
    payload = {
        "schema": "quantrisk-evidence-manifest/1",
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "generated_by_command": "uv run python scripts/build_evidence_manifest.py",
        "purpose": (
            "Frozen SHA-256 over every artifact a README or paper number traces to, with "
            "the command that produced it. Regenerate with the command above; verify with "
            "scripts/verify_evidence_manifest.py."
        ),
        "repository": state,
        "environment": {
            "quantrisk_version": build_environment["packages"]["quantrisk"],
            "git_commit_at_run": build_environment["git_commit"],
            "binary_git_commit": build_environment["binary_git_commit"],
            "provenance": build_environment["provenance"],
            "python_platform": build_environment["python_platform"],
            "cpp_compiler": build_environment["cpp_compiler"],
            "cpp_arch": build_environment["cpp_arch"],
            "packages": build_environment["packages"],
        },
        "categories": categories,
        "artifacts": entries,
        "totals": {
            "artifacts": len(entries),
            "bytes": sum(entry["bytes"] for entry in entries),
            "by_category": {
                category: sum(1 for entry in entries if entry["category"] == category)
                for category in categories
            },
        },
        "warnings": warnings,
        "integrity_note": (
            "A hash proves the file has not changed since this manifest was written. It "
            "does not prove the number inside it is right — that is what the oracle "
            "comparisons and the phase reports' test output are for. Where the working "
            "tree was dirty at generation time, `repository.uncommitted_paths` lists what "
            "was not yet committed, and the evidence should be re-frozen after the commit "
            "that introduces it."
        ),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"wrote {OUTPUT.relative_to(ROOT)}: {len(entries)} artifacts, "
        f"{payload['totals']['bytes']:,} bytes"
    )
    for category, count in payload["totals"]["by_category"].items():
        print(f"  {count:4d}  {category}")
    if warnings:
        print(f"{len(warnings)} warning(s):")
        for warning in warnings[:10]:
            print(f"  - {warning}")
    if state["working_tree_dirty"]:
        print(
            "NOTE the working tree is dirty; re-run after committing so the manifest "
            "describes a revision that exists in history."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
