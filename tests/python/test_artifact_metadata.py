"""The evidence tooling is project code too, so it gets tested like project code.

Every artifact in `experiments/` and `benchmarks/` carries the output of these
helpers. If `environment()` dropped a field, `sha256_file` disagreed with the
standard hash, or the manifest leaked machine-specific paths, the frozen evidence
chain of Phase 10 would be quietly unverifiable.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import quantrisk
from quantrisk.experiments.metadata import (
    REPO_ROOT,
    artifact_manifest,
    describe_provenance,
    environment,
    package_versions,
    parse_porcelain_status,
    repo_relative,
    sha256_file,
    working_tree_state,
)


def test_parse_porcelain_status_reports_paths_not_status_prefixes() -> None:
    stdout = (
        " M python/quantrisk/__init__.py\n"
        "M  CMakeLists.txt\n"
        "?? cpp/src/risk/measures.cpp\n"
        "R  old/name.hpp -> new/name.hpp\n"
        "D  removed/file.cpp\n"
        "\n"
    )
    assert parse_porcelain_status(stdout) == [
        "CMakeLists.txt",
        "cpp/src/risk/measures.cpp",
        "new/name.hpp",
        "python/quantrisk/__init__.py",
        "removed/file.cpp",
    ]


def test_parse_porcelain_status_is_empty_for_a_clean_tree() -> None:
    assert parse_porcelain_status("") == []
    assert parse_porcelain_status("\n") == []
    assert parse_porcelain_status("  \n") == []


def test_environment_carries_every_fact_the_protocol_requires() -> None:
    facts = environment()
    required = {
        "generated_at_utc",
        "quantrisk_version",
        "git_commit",
        "working_tree_dirty",
        "uncommitted_paths",
        "provenance",
        "cpp_compiler",
        "cpp_arch",
        "cpp_os",
        "cpp_build_type",
        "cpp_standard",
        "cpp_flags",
        "python_platform",
        "python_machine",
        "packages",
    }
    assert required <= set(facts), required - set(facts)
    assert facts["quantrisk_version"] == quantrisk.version()
    assert facts["packages"]["quantrisk"] == quantrisk.version()
    assert facts["packages"]["python"]
    assert "C++20" in facts["cpp_standard"]
    assert facts["provenance"]


def test_provenance_states_which_commit_the_numbers_belong_to() -> None:
    # The configure-time stamp is not the code that ran, so each of the four
    # reachable situations has to be described differently rather than one
    # confident sentence being reused for all of them.
    assert "git is unavailable" in describe_provenance(None, "abc", None)
    dirty = describe_provenance("abc", "abc", True)
    assert "uncommitted" in dirty and "abc" in dirty
    stale = describe_provenance("abc", "xyz", False)
    assert "rebuild" in stale and "xyz" in stale and "abc" in stale
    clean = describe_provenance("abc", "abc", False)
    assert "clean working tree at abc" in clean and "rebuild" not in clean


def test_environment_distinguishes_run_time_head_from_the_binary_stamp() -> None:
    facts = environment()
    assert facts["binary_git_commit"] == quantrisk.build_metadata()["git_commit"]
    # Both are 12-character abbreviations, so a comparison is meaningful.
    assert len(facts["git_commit"]) in (7, 12, len("unknown")) or facts["git_commit"] == "unknown"


def test_uncommitted_paths_are_relative_and_never_escape_the_repository() -> None:
    state = working_tree_state()
    for path in state["uncommitted_paths"]:
        assert not path.startswith("/")
        assert not path.startswith("..")


def test_sha256_file_matches_the_standard_hash_of_the_same_bytes(tmp_path: Path) -> None:
    payload = bytes(range(256)) * 40
    target = tmp_path / "payload.bin"
    target.write_bytes(payload)
    assert sha256_file(target) == hashlib.sha256(payload).hexdigest()
    assert sha256_file(str(target)) == hashlib.sha256(payload).hexdigest()


def test_sha256_file_of_an_empty_file_is_the_empty_digest(tmp_path: Path) -> None:
    empty = tmp_path / "empty.bin"
    empty.write_bytes(b"")
    assert sha256_file(empty) == hashlib.sha256(b"").hexdigest()


def test_sha256_file_reports_a_missing_file_instead_of_hashing_nothing(
    tmp_path: Path,
) -> None:
    with pytest.raises(OSError):
        sha256_file(tmp_path / "absent.bin")


def test_manifest_is_repo_relative_and_carries_sizes(tmp_path: Path) -> None:
    inside = REPO_ROOT / "tests" / "python" / "test_artifact_metadata.py"
    entries = artifact_manifest([inside, tmp_path / "absent.txt"])
    assert len(entries) == 1, "absent files must be skipped, not hashed"
    assert entries[0]["path"] == "tests/python/test_artifact_metadata.py"
    assert not entries[0]["path"].startswith("/")
    assert entries[0]["bytes"] == str(inside.stat().st_size)
    assert entries[0]["sha256"] == hashlib.sha256(inside.read_bytes()).hexdigest()


def test_repo_relative_keeps_repository_paths_short(tmp_path: Path) -> None:
    assert repo_relative(REPO_ROOT / "README.md") == "README.md"
    # Anything outside the repository has no relative form to report, so it is
    # returned as the absolute path rather than a fabricated `../..` climb.
    outside = tmp_path / "elsewhere.csv"
    assert repo_relative(outside) == str(outside.resolve())


def test_package_versions_records_the_running_interpreter() -> None:
    versions = package_versions()
    assert versions["python"] == sys.version.split()[0]
    assert versions["quantrisk"] == quantrisk.version()


SUITE = REPO_ROOT / "scripts" / "run_benchmark_suite.py"


def _aggregate(tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Run the suite in aggregate-only mode, writing outside the tracked tree.

    `--no-run` is what makes this affordable in CI: no benchmark executes, so the test
    costs milliseconds and still covers the whole claim that matters — that every headline
    number the summary publishes can still be found at the key path it names. When a
    benchmark script renames a field, this is what fails, rather than the summary quietly
    losing a row.
    """
    return subprocess.run(
        [sys.executable, str(SUITE), "--no-run", "--out", str(tmp_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_suite_aggregates_every_member_from_the_artifacts_on_disk(tmp_path: Path) -> None:
    completed = _aggregate(tmp_path)
    assert completed.returncode == 0, completed.stderr[-4000:]
    assert "0 failed, 0 skipped" in completed.stdout, completed.stdout
    for name in ("suite_run.json", "suite_headline.csv", "suite_summary.md"):
        assert (tmp_path / name).exists(), f"{name} was not written"
    assert (tmp_path / "validation_envelope.png").stat().st_size > 1000


def test_suite_run_json_records_a_member_for_each_registered_script(tmp_path: Path) -> None:
    completed = _aggregate(tmp_path)
    assert completed.returncode == 0, completed.stderr[-4000:]
    suite = json.loads((tmp_path / "suite_run.json").read_text(encoding="utf-8"))
    keys = [member["key"] for member in suite["members"]]
    assert len(keys) == len(set(keys)) == suite["totals"]["members"]
    kinds = {member["kind"] for member in suite["members"]}
    assert kinds == {"correctness_benchmark", "performance_benchmark", "statistical_experiment"}
    for member in suite["members"]:
        assert Path(REPO_ROOT / member["script"]).exists()
        assert Path(REPO_ROOT / member["artifact"]).exists()
        assert member["metrics"], f"{member['key']} publishes nothing"
        assert member["artifact_sha256"] == sha256_file(REPO_ROOT / member["artifact"])


def test_suite_headline_csv_is_machine_readable_and_points_at_its_source(
    tmp_path: Path,
) -> None:
    completed = _aggregate(tmp_path)
    assert completed.returncode == 0, completed.stderr[-4000:]
    with (tmp_path / "suite_headline.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    for row in rows:
        # Re-walk the key path here, independently of the runner's own `dig`. If the two
        # ever disagree, the published number is not the number the artifact holds.
        node: object = json.loads((REPO_ROOT / row["artifact"]).read_text(encoding="utf-8"))
        for key in row["source_keys"].split(" / "):
            assert isinstance(node, dict) and key in node, f"{row['member']}: {key} missing"
            node = node[key]
        assert json.dumps(node, sort_keys=True) == row["value_json"], row
        assert json.loads(row["value_json"]) == node


def test_unknown_member_is_an_error_rather_than_an_empty_run(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(SUITE), "--no-run", "--only", "not_a_member", "--out", str(tmp_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    assert "unknown member" in completed.stderr
    assert not (tmp_path / "suite_run.json").exists()


def _numbered_limitation_entries() -> int:
    text = (REPO_ROOT / "docs" / "limitations.md").read_text(encoding="utf-8")
    numbers = [int(m.group(1)) for m in re.finditer(r"^(\d+)\. \*\*", text, flags=re.M)]
    assert numbers == list(range(1, len(numbers) + 1)), "limitation numbering has a gap"
    return len(numbers)


def test_documents_that_count_the_limitations_agree_with_the_file() -> None:
    """`docs/limitations.md` is cited by count in five other documents.

    A count repeated by hand in five places is a fact with five chances to go stale, and it
    does: adding Phase 10's entries left every one of them reading "55". This test makes the
    file the single source, so the next entry added without updating the prose fails here
    rather than shipping a wrong number in the README.
    """
    total = _numbered_limitation_entries()
    claims = {
        "README.md": r"carries (\d+) numbered entries",
        "docs/validation_matrix.md": r"The (\d+) numbered limitations",
        "docs/release_notes_v1.0.0.md": r"\*\*(\d+) numbered limitations\*\*",
        "docs/interview_defense.md": r"has all (\d+)\s*\n?numbered entries",
        "paper/technical_report.tex": r"contains (\d+) numbered entries",
    }
    for name, pattern in claims.items():
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        found = re.findall(pattern, text)
        assert found, f"{name} no longer states the limitation count in the expected form"
        assert all(int(value) == total for value in found), (
            f"{name} says {found}, docs/limitations.md has {total}"
        )


def test_no_committed_artifact_leaks_a_machine_specific_path() -> None:
    """Frozen evidence must name its inputs as repository paths, not as this machine's.

    The generating command recorded in each artifact comes from `sys.argv[0]`, so it is
    whatever the caller happened to pass. Running the suite with absolute script paths put
    `/Users/<name>/QuantRisk++/benchmarks/...` into `pricing_vs_quantlib.json` — a username in
    a public artifact, and one the manifest then hashed as if it were evidence.
    """
    home = str(Path.home())
    offenders: list[str] = []
    patterns = (
        "benchmarks/**/*.json",
        "benchmarks/**/*.csv",
        "experiments/**/*.json",
        "experiments/**/*.csv",
        "evidence/**/*.json",
    )
    for pattern in patterns:
        for path in REPO_ROOT.glob(pattern):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if str(REPO_ROOT) in text or home in text or "/Users/" in text or "/home/" in text:
                offenders.append(repo_relative(path))
    assert not offenders, f"machine-specific paths in: {sorted(offenders)}"
