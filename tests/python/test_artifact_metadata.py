"""The evidence tooling is project code too, so it gets tested like project code.

Every artifact in `experiments/` and `benchmarks/` carries the output of these
helpers. If `environment()` dropped a field, `sha256_file` disagreed with the
standard hash, or the manifest leaked machine-specific paths, the frozen evidence
chain of Phase 10 would be quietly unverifiable.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

import pytest
import quantrisk
import yaml
from quantrisk.experiments.evidence import content_digest
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


def _folded_document(relative: str) -> str:
    """A document with its line breaks folded to single spaces.

    Prose re-wraps and a claim is one statement, so a pattern written with a literal space is blind
    to the occurrence the file happens to split. The claim inventory reads this view, and a spelling
    it marks owned has to be a spelling its owner guard can actually see --
    `docs/reproducibility.md` carried `204 tests under` / `CTest either way` unpoliced since a later
    edit moved that break.
    """
    return " ".join((REPO_ROOT / relative).read_text(encoding="utf-8").split())


def test_the_documents_that_count_python_tests_count_the_ones_that_exist() -> None:
    """A test count is the third number this repository restates in prose and gets stale.

    `docs/integrity_audit.md` records `v1.0.0` quoting both 330 and 319 for the same tag while
    the runner printed a third number, so this closes it the way the limitation count was
    closed: re-collect the suite in a subprocess and compare. Collect-only, because the
    subprocess must not run the 342 benchmarks it would otherwise be counting.

    The CI figure is not asserted here — reproducing it would mean uninstalling the oracles
    from inside the test session — but it is quoted from the runner's own log, and
    `docs/limitations.md` #63 explains why the two numbers differ.
    """
    total = _collect_in_this_environment()

    # Both environments are documented, and each one checks its own figure. The CI
    # `build-and-test` lane installs without the `oracles` extra, four oracle-gated modules
    # collapse into four skip records instead of the 69 cases they hold, and the run collects
    # 284 rather than 353 -- so a guard that asserted only the with-oracles number would either
    # fail on the runner or have to be told to ignore it, which is how the two figures drifted
    # apart in the first place.
    with_oracles = r"(\d+)\s+pytest\s+tests\s+with\s+the\s+`oracles`\s+extra"
    without_oracles = r"collects\s+(\d+)\s+tests\s+without\s+it"
    # Two further forms restate the same pair -- a then/now table row and a comment on the offline
    # reproduction command -- and neither used to be checked, which is how `388` and `319` survived
    # in `docs/interview_defense.md` after the headline above them had moved. They are checked
    # against the document's own two figures rather than against this run's total: each belongs to
    # one environment, so comparing either to `total` would go red on the CI lane for the right
    # reason.
    #
    # A third round of the same lesson: Q11 restates the pair as "386 Python tests with the
    # validation oracles installed — 295 without them", which no pattern above matched, so the
    # sentence kept a count two releases behind while its own document's headline was current. A
    # restatement guards only in the wording it recognises, so these two phrasings are now policed
    # too rather than left to whichever reader notices the disagreement between two sentences.
    table_pair = r"198\s*/\s*(\d+)\s+now"
    command_count = r"python -m pytest -q\s+#\s+(\d+)\s+Python tests"
    oracle_prose = r"(\d+)\s+Python tests with the validation oracles installed"
    offline_prose = r"[—-]\s*(\d+)\s+without them"
    documents = ("docs/interview_defense.md", "docs/limitations.md", "docs/reproducibility.md")
    for name in documents:
        # Fold the document's line breaks before searching it. A claim is one statement and prose
        # re-wraps it: `... the 69 cases they` / `hold ...` is invisible to a pattern written with a
        # literal space, and the reading of `docs/reproducibility.md`'s C++ count had been silently
        # unpoliced since a later edit moved that break (finding 70). The claim inventory reads the
        # same folded view, so a span it calls owned is a span these comparisons actually see.
        text = _folded_document(name)
        high = re.search(with_oracles, text)
        low = re.search(without_oracles, text)
        assert high and low, f"{name} does not state both Python test counts"
        for pattern, expected, label in (
            (table_pair, high.group(1), "the with-oracles table row"),
            (command_count, low.group(1), "the offline command comment"),
            (oracle_prose, high.group(1), "the with-oracles prose figure"),
            (offline_prose, low.group(1), "the without-oracles prose figure"),
        ):
            for value in re.findall(pattern, text):
                assert value == expected, (
                    f"{name} states {label} as {value} while its headline says {expected}"
                )
        # Two more restatements of the same pair, both found by the inventory rather than by
        # reading. The rehearsal sheet gives the difference the four oracle-gated modules make
        # ("the 69 cases they hold") and the right-hand half of its own provenance row
        # ("`v1.0.0`, 204 / 507 now"), and neither pattern above reaches either, so a re-freeze
        # that moves 507 would leave both behind beside a headline that had been synced.
        case_gap = r"(?:instead of|rather than) the (\d+) cases they\s+hold"
        now_pair = r"`v1\.0\.0`, \d+ / (\d+) now"
        for pattern, expected, label in (
            (
                case_gap,
                int(high.group(1)) - int(low.group(1)),
                "the cases the four oracle-gated modules hold",
            ),
            (now_pair, high.group(1), "the with-oracles half of the provenance row"),
        ):
            for value in re.findall(pattern, text):
                assert int(value) == int(expected), (
                    f"{name} states {label} as {value}, while its own headline pair is "
                    f"{high.group(1)} with the oracles and {low.group(1)} without "
                    f"(the difference is {expected})"
                )
        documented = int(high.group(1)) if _oracles_present() else int(low.group(1))
        assert documented == total, (
            f"{name} says {documented} for this environment; pytest collects {total}. "
            f"oracles present: {_oracles_present()}"
        )

    # The report gives the same pair in LaTeX prose -- "460 pytest tests with the validation oracles
    # installed, 391 collected without them" -- where none of the patterns above reaches it. It said
    # 411 and 342 until this phase read it, two releases after both numbers stopped being true.
    report = (REPO_ROOT / "paper" / "technical_report.tex").read_text(encoding="utf-8")
    tex_high = re.search(
        r"(\d+)\s+pytest\s+tests\s+with\s+the\s+validation\s+oracles\s+installed", report
    )
    tex_low = re.search(r"(\d+)\s+collected\s+without\s+them", report)
    assert tex_high and tex_low, "the report no longer states both Python test counts"
    tex_documented = int(tex_high.group(1)) if _oracles_present() else int(tex_low.group(1))
    assert tex_documented == total, (
        f"the report says {tex_documented} for this environment; pytest collects {total}. "
        f"oracles present: {_oracles_present()}"
    )


def _declared_layout(text: str) -> list[str]:
    """The paths named in `docs/architecture.md` §5's fenced block, brace groups expanded."""
    block = re.search(r"## 5\..*?```text\n(.*?)```", text, flags=re.S)
    assert block, "architecture.md no longer carries the §5 layout block in the expected form"
    paths: list[str] = []
    # Newlines separate items in the block; the middot separates the items written on one line. A
    # brace group may itself be wrapped across lines, so those continuations are rejoined first.
    lines: list[str] = []
    for raw in block.group(1).splitlines():
        if lines and lines[-1].count("{") > lines[-1].count("}"):
            lines[-1] = f"{lines[-1]} {raw.strip()}"
        else:
            lines.append(raw.strip())
    for line in lines:
        for token in line.split("\u00b7"):
            token = token.split("(")[0].strip()  # prose aside, not a path
            if not token:
                continue
            brace = re.match(r"^(.*)\{([^}]*)\}(.*)$", token)
            if brace:
                head, choices, tail = brace.groups()
                # A wrapped brace list gains a space at the join, so each member is trimmed.
                paths += [f"{head}{choice.strip()}{tail}" for choice in choices.split(",")]
            else:
                paths.append(token)
    return [path.strip().rstrip("/") for path in paths if path.strip()]


def test_documents_that_count_the_paper_chapters_agree_with_the_source() -> None:
    r"""The technical report's chapter count is restated in six documents, and two had it wrong.

    `paper/technical_report.tex` has twelve numbered `\section` commands plus an unnumbered
    artifact index, and the index is the kind of thing a person counts as a chapter: two release
    notes claimed thirteen. A count of a document's own structure is the same class of claim as a
    count of the limitations register, so it is derived rather than typed.
    """
    source = (REPO_ROOT / "paper" / "technical_report.tex").read_text(encoding="utf-8")
    total = len(re.findall(r"^\\section\{", source, flags=re.M))
    claims = {
        "README.md": r"(\d+|\w+)\s+chapters",
        "docs/release_notes_v1.0.0.md": r"(\d+|\w+) chapters",
        "docs/release_notes_v1.1.0.md": r"(\d+|\w+) chapters",
        "docs/release_notes_v1.2.0.md": r"(\d+|\w+) chapters",
        "docs/release_notes_v1.3.0.md": r"(\d+|\w+) chapters",
        "docs/release_notes_v1.4.0.md": r"(\d+|\w+) chapters",
    }
    for name, pattern in claims.items():
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        found = re.findall(pattern, text)
        assert found, f"{name} no longer states a chapter count"
        values = [int(word) if word.isdigit() else SPELLED_NUMBERS[word.lower()] for word in found]
        assert all(value == total for value in values), (
            f"{name} says {values}; technical_report.tex has {total} numbered sections"
        )


def test_every_path_the_architecture_document_declares_exists() -> None:
    """`docs/architecture.md` describes the tree, so every path it prints has to be in it.

    The document claimed a `python/quantrisk/analytics/` package for several phases. Nothing like
    that ever existed: the facades are one module per domain, and the layer table named the same
    phantom directory. A prose file that lists paths makes claims of the kind an artifact does,
    and this is the check that was missing when the layout drifted from the target.
    """
    text = (REPO_ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    declared = _declared_layout(text)
    assert len(declared) >= 25, (
        f"the parser found only {len(declared)} paths; the block changed shape"
    )
    missing = [path for path in declared if not (REPO_ROOT / path).exists()]
    assert not missing, f"architecture.md §5 declares paths that are not in the tree: {missing}"
    assert "python/quantrisk/analytics" not in " ".join(declared), (
        "the phantom package is back in the layout the document presents as fact"
    )


def test_the_layout_parser_does_not_pass_on_nothing() -> None:
    """Negative control: a bogus path inside the block has to be reported, not skipped.

    Without this the guard could go quiet on a parsing change -- which is how a stale path
    survived in the document in the first place.
    """
    text = (REPO_ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    needle = "pyproject.toml \u00b7 README.md"
    assert text.count(needle) == 1, (
        "the \u00a75 block changed shape and this probe needs a new anchor"
    )
    tampered = text.replace(
        needle, "pyproject.toml \u00b7 python/quantrisk/analytics/ \u00b7 README.md", 1
    )
    declared = _declared_layout(tampered)
    assert "python/quantrisk/analytics" in declared, "the parser did not expand the injected path"
    assert not (REPO_ROOT / "python/quantrisk/analytics").exists()


def test_every_analysis_note_is_guarded_against_the_numbers_it_quotes() -> None:
    """`docs/analysis/` is where this repository states results, so it needs an owner per figure.

    Phase 12 shipped its note without one and Phase 13 shipped its note *with* one; the difference
    showed. When the guard for the second note was written, the first note's crossing figures turned
    out to be stale by four decimals, and a headline fitted slope in the same paragraph was not
    computed by anything in the tree at all (audit finding 32, limitation #77). A new note therefore
    has to appear in the source of a test that reads it, which is what this ratchet enforces: the
    named file is the contract, and adding prose without a reader fails here rather than in review.
    """
    notes = sorted(path.name for path in (REPO_ROOT / "docs" / "analysis").glob("*.md"))
    assert len(notes) >= 2, f"expected the two worked analyses, found {notes}"
    sources = {
        path.name: path.read_text(encoding="utf-8")
        for path in (REPO_ROOT / "tests" / "python").glob("test_*.py")
    }
    unguarded = [name for name in notes if not any(name in source for source in sources.values())]
    assert not unguarded, f"analysis notes with no test that reads them: {unguarded}"


def test_documents_that_count_the_limitations_agree_with_the_file() -> None:
    """`docs/limitations.md` is cited by count in six other documents.

    A count repeated by hand in five places is a fact with five chances to go stale, and it
    does: adding Phase 10's entries left every one of them reading "55". This test makes the
    file the single source, so the next entry added without updating the prose fails here
    rather than shipping a wrong number in the README.

    `docs/release_notes_v1.0.0.md` and `docs/integrity_audit.md` are deliberately *not* in
    this set. They are records of a revision, and their counts were true of `v1.0.0`; forcing
    them to track a moving file would rewrite the historical claim to keep a test green, which
    is the opposite of what an evidence document is for. They state the revision they describe.
    """
    total = _numbered_limitation_entries()
    claims = {
        "README.md": r"carries (\d+) numbered entries",
        "docs/validation_matrix.md": r"The (\d+) numbered limitations",
        "docs/interview_defense.md": [
            r"has all (\d+)\s*\n?numbered entries",
            # The sheet's own claim-provenance table repeats the register's size as a parenthetical,
            # and it was three phases behind the sentence above it: the prose read 94 while the cell
            # read 84. Found by the inventory, not by reading (limitation #89's prediction).
            r"docs/limitations\.md` \((\d+) entries\)",
        ],
        "paper/technical_report.tex": [
            r"(?:contains|holds) (\d+) numbered entries",
            # The abstract states the same register's size in its own words, four pages from the
            # section that cites it. Finding 55's mechanism, one phrasing at a time: the guard
            # compared the section sentence while the abstract kept shipping `v1.0.0`'s number.
            r"(\d+)\s+recorded\s+limitations",
        ],
        # A release note is a living document about the current file, not a record of a past
        # revision: it quoted the count while the count moved. #76 was found by exactly that lag.
        "docs/release_notes_v1.3.0.md": r"all \*\*(\d+) entries\*\*",
        # ... and the same holds for the note that records #77's third case.
        "docs/release_notes_v1.4.0.md": r"carries (\d+) numbered entries",
    }
    for name, expected in claims.items():
        text = _folded_document(name)
        patterns = expected if isinstance(expected, list) else [expected]
        found = [value for pattern in patterns for value in re.findall(pattern, text)]
        assert found, f"{name} no longer states the limitation count in the expected form"
        for pattern in patterns:
            assert re.search(pattern, text), f"{name} no longer matches {pattern!r}"
        assert all(int(value) == total for value in found), (
            f"{name} says {found}, docs/limitations.md has {total}"
        )


SPELLED_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "twenty-one": 21,
    "twenty-two": 22,
    "twenty-three": 23,
    "twenty-four": 24,
    "twenty-five": 25,
    "twenty-six": 26,
}


def _as_int(token: str) -> int:
    """`12` and `twelve` are the same claim about the same registry."""
    if token.isdigit():
        return int(token)
    return SPELLED_NUMBERS[token.lower()]


ORACLE_MODULES = ("QuantLib", "pypfopt", "cvxpy", "sklearn")


def _oracles_present() -> bool:
    """Whether this environment installed the `oracles` extra.

    The test count is a property of the environment (limitation #63), so a guard about that
    number has to know which environment it is running in. Importing the optional packages is
    the only honest way to ask.
    """
    import importlib.util

    return all(importlib.util.find_spec(module) is not None for module in ORACLE_MODULES)


def _collect_in_this_environment() -> int:
    """What pytest collects here, measured by a child that shares this process's oracle lever.

    The guard compares a document's figure for *this* environment with a collection run, and the
    collection happens in a subprocess because the parent must not execute the suite. A bare
    subprocess sees site-packages rather than the parent's import state, so under
    `scripts/measure_offline_collection.py`'s simulation the parent correctly concluded the oracles
    were missing while the child collected the with-oracles figure -- measured on 2026-10-07 as
    `1 failed, 415 passed, 4 skipped` in a blocked child, where the CI lane prints no failure. The
    block is therefore handed down: absent modules are absent in the child too, which is what the
    runner's lane actually looks like.
    """
    import importlib.util

    blocked = [
        module
        for module in ORACLE_MODULES
        if importlib.util.find_spec(module) is None  # absent, or blocked by a probe
    ]
    argv = (
        ["-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"]
        if not blocked
        else [
            "-c",
            "import sys\n"
            + "".join(f"sys.modules[{name!r}] = None\n" for name in blocked)
            + "import pytest\n"
            + "raise SystemExit(pytest.main(['--collect-only', '-q',"
            + " '-p', 'no:cacheprovider']))",
        ]
    )
    completed = subprocess.run(
        [sys.executable, *argv],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    collected = re.search(r"^(\d+) tests? collected", completed.stdout, flags=re.M)
    assert collected, (
        f"could not read a test count out of pytest: {(completed.stdout + completed.stderr)[-500:]}"
    )
    return int(collected.group(1))


def _load_suite_members() -> list[Any]:
    """The suite's own registry, so a document can be checked against it rather than a guess.

    Loaded by path because `scripts/` is not an importable package, and loaded rather than
    grepped because the thing being asserted is the count of Python objects the runner holds.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_benchmark_suite", REPO_ROOT / "scripts" / "run_benchmark_suite.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # `@dataclass` resolves the module of a class through `sys.modules`, and a module created
    # by `module_from_spec` is not in there until it is put there. Without this the load dies
    # inside dataclasses, on the Member definition, with an AttributeError about None.
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        del sys.modules[spec.name]
    return list(module.MEMBERS)


def test_every_experiment_and_benchmark_script_on_disk_is_a_suite_member() -> None:
    """A script nobody registers is invisible, so absence itself has to be an assertion.

    `docs/integrity_audit.md` keeps this on its open list for one reason: the registry in
    `scripts/run_benchmark_suite.py` is hand-maintained, so an `experiments/*/run.py` that arrives
    without a member entry produces no output anywhere. Nothing disagrees with anything: the
    fourteen published numbers stay as true as they were before the fifteenth experiment existed.
    The other direction is already policed, by
    `test_suite_run_json_records_a_member_for_each_registered_script`, which fails on a member whose
    file is gone; the unprovable half was this one, disk to registry.

    The floor is part of the check, not decoration. Discovery is by the layout the repository
    actually uses, and a glob that silently narrowed would compare two shortlists and pass.
    """
    on_disk = {
        str(path.relative_to(REPO_ROOT))
        for pattern in ("experiments/*/run.py", "benchmarks/*/*.py")
        for path in REPO_ROOT.glob(pattern)
        if path.is_file()
    }
    registered = {member.script for member in _load_suite_members()}
    assert len(on_disk) >= 15, f"discovery found only {len(on_disk)}: {sorted(on_disk)}"
    assert on_disk == registered, (
        f"on disk but not registered: {sorted(on_disk - registered)}; "
        f"registered but not on disk: {sorted(registered - on_disk)}"
    )


def test_the_suite_records_a_pasteable_command_with_no_machine_path(tmp_path: Path) -> None:
    """The roll-up is evidence now, so it names its own invocation like the others do.

    `--out` is the argument that would break this: argv is the caller's, and a caller who
    passed an absolute output directory would have their own path written into a committed
    artifact and hashed by the manifest as if it were part of the evidence. The recorded
    command is rebuilt from the parsed flags instead, with the output directory made
    repo-relative. Both directions are asserted, because the safe case (an in-repo `--out`,
    which is the only one that can ever be committed) and the harmless-but-still-absolute case
    (an out-of-repo `--out`, which `repo_relative` necessarily leaves alone) are different
    branches, and a test that only exercised the second would pass while the first leaked.
    """
    in_repo = REPO_ROOT / "build" / "suite-command-test"
    first = subprocess.run(
        [sys.executable, str(SUITE), "--no-run", "--require-all", "--out", str(in_repo)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert first.returncode == 0, first.stderr[-4000:]
    command = json.loads((in_repo / "suite_run.json").read_text(encoding="utf-8"))["command"]

    assert command.startswith("uv run python scripts/run_benchmark_suite.py")
    assert "--no-run" in command and "--require-all" in command
    assert f"--out {repo_relative(in_repo)}" in command, (
        f"--out was not made repo-relative: {command}"
    )
    assert str(Path.home()) not in command
    assert (in_repo / "suite_summary.md").read_text(encoding="utf-8").count(f"`{command}`") == 1
    shutil.rmtree(in_repo)

    outside = _aggregate(tmp_path)
    assert outside.returncode == 0, outside.stderr[-4000:]
    outside_command = json.loads((tmp_path / "suite_run.json").read_text(encoding="utf-8"))[
        "command"
    ]
    # An output directory outside the repository cannot be expressed relative to it, so the
    # path stays absolute. That is not a leak: nothing under /private/var is ever committed.
    assert str(Path.home()) not in outside_command


def test_the_manifest_hashes_every_experiment_results_directory() -> None:
    """A new experiment escapes the evidence freeze silently, because the list is kept by hand.

    `scripts/build_evidence_manifest.py` walks the directories it names, and Phase 18 added
    `experiments/second_book_crossing_map/` without naming it there. The verifier then read back
    `83 OK / 0 MISSING / 0 on disk but not in the manifest` -- three true statements about the list
    it walks, and blind to the directory that is not in it. Every README, matrix and paper number
    traces to files like these, so the tree owns the list and the frozen manifest has to cover it.
    """
    manifest = json.loads((REPO_ROOT / "evidence" / "manifest.json").read_text(encoding="utf-8"))
    covered = {str(Path(entry["path"]).parent) for entry in manifest["artifacts"]}
    on_disk = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "experiments").glob("*/results")
        if path.is_dir()
    )
    assert on_disk, "no experiment results directories found; the tree's shape changed"
    missing = [directory for directory in on_disk if directory not in covered]
    assert not missing, f"evidence/manifest.json hashes none of: {missing}"


def test_the_frozen_suite_roll_up_records_the_command_that_made_it() -> None:
    """The committed aggregate must describe itself the way the README quotes it.

    `docs/reproducibility.md` says the frozen suite ran with `--require-all`, and that flag is
    the difference between "12/12 executed" and "12 rows, some of them skipped". If the
    artifact on disk was made without it, the document is describing a run that did not happen.
    """
    suite = json.loads(
        (REPO_ROOT / "benchmarks" / "suite" / "results" / "suite_run.json").read_text(
            encoding="utf-8"
        )
    )
    command = suite["command"]
    assert "--require-all" in command, f"the frozen suite was run without it: {command!r}"
    assert "--out" not in command, (
        "the frozen aggregate was written somewhere other than RESULTS_DIR"
    )
    assert "--no-run" not in command, "the frozen aggregate was read off disk, not executed"
    assert suite["totals"]["members"] == len(_load_suite_members())
    assert suite["totals"]["skipped"] == 0


def test_documents_that_count_the_suite_members_agree_with_the_registry() -> None:
    """The suite's member count is quoted in six documents, and the registry owns it.

    `scripts/run_benchmark_suite.py` registers members by hand (limitation #58), so the only
    thing that turns "we run everything" into a checkable claim is a reader counting the
    registry. Six documents count it for that reader, and a count repeated by hand is a fact
    with six chances to go stale — which is how `docs/reproducibility.md` came to say that
    four members skip without the `oracles` extra when the registry already had five with a
    `requires` clause. Assert against the registry itself, including the per-kind breakdown
    the README prints and the skippable count the reproducibility note prints.
    """
    members = _load_suite_members()
    total = len(members)
    by_kind = {
        "correctness benchmarks": sum(1 for m in members if m.kind == "correctness_benchmark"),
        "statistical experiments": sum(1 for m in members if m.kind == "statistical_experiment"),
        "performance benchmark": sum(1 for m in members if m.kind == "performance_benchmark"),
    }
    skippable = sum(1 for m in members if m.requires)

    claims = {
        "README.md": r"runs\s+all\s+(\w+)\s+members",
        "docs/limitations.md": r"so\s+all\s+(\w+)\s+members\s+execute\s+against\s+live\s+oracles",
        "docs/reproducibility.md": r"all\s+(\d+)\s+members",
        "docs/validation_matrix.md": r"all\s+(\d+)\s+members",
        ".github/workflows/ci.yml": r"re-executes\s+all\s+(\w+)\s+members",
    }
    for name, pattern in claims.items():
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        found = re.search(pattern, text)
        assert found, f"{name} no longer states the suite member count in the expected form"
        assert _as_int(found.group(1)) == total, (
            f"{name} says {found.group(1)!r}, the registry has {total} members"
        )

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    breakdown = re.search(
        r"(\w+)\s+correctness\s+benchmarks,\s+(\w+)\s+statistical\s+experiments,\s+"
        r"(\w+)\s+performance\s+benchmark",
        readme,
    )
    assert breakdown, "README no longer breaks the suite down by kind"
    assert _as_int(breakdown.group(1)) == by_kind["correctness benchmarks"]
    assert _as_int(breakdown.group(2)) == by_kind["statistical experiments"]
    assert _as_int(breakdown.group(3)) == by_kind["performance benchmark"]
    assert sum(by_kind.values()) == total, "a member kind is not one of the three the suite claims"

    reproducibility = (REPO_ROOT / "docs" / "reproducibility.md").read_text(encoding="utf-8")
    skips = re.search(r"(\w+)\s+of\s+the\s+(\w+)\s+members\s+report\s+`skipped`", reproducibility)
    assert skips, "docs/reproducibility.md no longer states how many members need oracles"
    assert _as_int(skips.group(1)) == skippable, (
        f"the note says {skips.group(1)} members skip without the extra; "
        f"{skippable} have a `requires` clause"
    )
    assert _as_int(skips.group(2)) == total

    defense = (REPO_ROOT / "docs" / "interview_defense.md").read_text(encoding="utf-8")
    executed = re.search(r"(\d+)/(\d+)\s+benchmark-suite\s+members\s+executed", defense)
    assert executed and int(executed.group(2)) == total, (
        "interview_defense.md counts a different suite than the registry has"
    )

    # The report's headline paragraph states the same number in its own words, and had drifted to
    # fourteen while the registry was already at sixteen: a count the prose owns but no reader
    # compares is a count that goes stale twice.
    report = (REPO_ROOT / "paper" / "technical_report.tex").read_text(encoding="utf-8")
    tex_members = re.search(r"(\d+)\s+benchmark-suite\s+members\s+execute", report)
    assert tex_members, "the report no longer states the suite member count"
    assert int(tex_members.group(1)) == total, (
        f"technical_report.tex says {tex_members.group(1)} members, the registry has {total}"
    )


def test_the_readme_experiment_count_agrees_with_the_experiments_on_disk() -> None:
    """The front page's list of what was measured is a count of directories, not of sentences.

    It had fallen three rows behind: the prose said eight experiments while the table under it
    listed nine, and twelve scripts existed. Two documents restating one fact and neither owning it
    is the failure this file exists to close, so both the sentence and the rows are derived from
    `experiments/*/run.py`.
    """
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    section = re.search(r"^## Experiments$(.*?)^## ", readme, flags=re.M | re.S)
    assert section, "README.md no longer carries the experiments section in the counted form"
    listed = re.findall(r"^\| `([a-z0-9_]+)` \|", section.group(1), flags=re.M)
    assert listed, "no rows were read out of the experiments table"
    assert len(set(listed)) == len(listed), f"a row is listed twice: {listed}"
    on_disk = sorted(path.parent.name for path in (REPO_ROOT / "experiments").glob("*/run.py"))
    assert sorted(listed) == on_disk, (
        f"README lists {len(listed)} experiments and the tree has {len(on_disk)}; "
        f"only one side names {sorted(set(listed) ^ set(on_disk))}"
    )
    claim = re.search(r"(\w+) experiments, each answering", section.group(1))
    assert claim, "README.md no longer states the experiment count"
    assert _as_int(claim.group(1)) == len(on_disk), (
        f"README.md says {claim.group(1)!r} experiments, the tree has {len(on_disk)} scripts"
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


def test_content_digest_ignores_run_metadata_but_not_results(tmp_path: Path) -> None:
    """The whole point of the content hash is that the two kinds of change are not confused.

    A re-run must not look like tampering, and tampering must not look like a re-run. Both
    directions are asserted here, because a filter that strips too much would pass the first
    test and silently fail the second.
    """
    original = {
        "generated_at_utc": "2026-09-27T00:00:00+00:00",
        "git_commit": "abcdef123456",
        "environment": {"cpp_compiler": "AppleClang 21.0.0"},
        "worst_relative_error": 3.46e-11,
        "rows": [{"scenario": "atm_call", "error": 1e-13}, {"scenario": "otm", "error": 2e-13}],
    }
    rerun = {
        **original,
        "generated_at_utc": "2026-09-27T09:30:00+00:00",
        "git_commit": "999999ffff00",
        "environment": {"cpp_compiler": "GNU 14.2.0"},
    }
    tampered = {**original, "worst_relative_error": 1.0}

    def digest(payload: dict[str, object], name: str) -> str | None:
        path = tmp_path / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return content_digest(path)

    base = digest(original, "a.json")
    assert base == digest(rerun, "b.json"), "a re-run must not read as a content change"
    assert base != digest(tampered, "c.json"), "a changed result must not read as a re-run"


def test_content_digest_treats_wall_clock_csv_columns_as_volatile(tmp_path: Path) -> None:
    header = "scenario,error,mean_runtime_seconds\n"
    kept = tmp_path / "kept.csv"
    moved = tmp_path / "moved.csv"
    tampered = tmp_path / "tampered.csv"
    kept.write_text(header + "atm_call,1e-13,0.004322\n", encoding="utf-8")
    moved.write_text(header + "atm_call,1e-13,0.036184\n", encoding="utf-8")
    tampered.write_text(header + "atm_call,9.99,0.004322\n", encoding="utf-8")
    assert content_digest(kept) == content_digest(moved)
    assert content_digest(kept) != content_digest(tampered)


def test_manifest_records_both_a_byte_hash_and_a_content_hash(tmp_path: Path) -> None:
    """`--strict` is only meaningful if the manifest carries the content digest to compare to."""
    payload = json.loads((REPO_ROOT / "evidence" / "manifest.json").read_text(encoding="utf-8"))
    assert payload["artifacts"], "the manifest lists nothing"
    for entry in payload["artifacts"]:
        assert "sha256" in entry
        path = REPO_ROOT / entry["path"]
        if path.suffix in {".json", ".csv"}:
            assert entry["content_sha256"], f"{entry['path']} has no content digest"
        else:
            assert entry["content_sha256"] is None, "binary evidence has no canonical form"


MATRIX_DOCUMENTS = {
    "README.md": r"is the full table . (\w+(?:-\w+)?) rows over",
    "docs/validation_matrix.md": r"It has (\w+(?:-\w+)?) rows rather than twelve",
}


def test_documents_that_count_the_validation_matrix_rows_agree_with_the_table() -> None:
    """The matrix is the project's answer to "what is validated", and two documents count it.

    Rows are counted from the table itself rather than from any summary, because a row is a
    component-and-oracle pairing rather than a component: twelve components produce more rows than
    twelve, and the difference is precisely the content (a component validated two ways gets two
    rows so that one row can admit it has no oracle). Prose that repeats the row count is repeating
    a fact about the file, so the file owns it.
    """
    table = (REPO_ROOT / "docs" / "validation_matrix.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| \d+[a-z]? \|", table, flags=re.M)
    for name, pattern in MATRIX_DOCUMENTS.items():
        found = re.search(pattern, (REPO_ROOT / name).read_text(encoding="utf-8"))
        assert found, f"{name} no longer states the validation-matrix row count"
        assert _as_int(found.group(1)) == len(rows), (
            f"{name} says {found.group(1)!r} rows, docs/validation_matrix.md has {len(rows)}"
        )


def test_the_validation_matrix_numbers_its_rows_once_and_in_order() -> None:
    """Row *labels* are cited by other documents, so a duplicated number is a broken pointer.

    The sibling test above counts rows, and counting cannot see a duplicate: two rows numbered 13
    still make eighteen rows, and the phase that shipped that pair also shipped a prose reference
    to "row 14" that pointed at the wrong table entry. Uniqueness and an unbroken sequence are
    therefore separate facts, and the sequence has to be checked on the numeric prefix because
    lettered sub-rows (`4b`, `9b`) are deliberate: they exist so a component can carry one row with
    an oracle and one that admits it has none.
    """
    table = (REPO_ROOT / "docs" / "validation_matrix.md").read_text(encoding="utf-8")
    labels = [match.group(1) for match in re.finditer(r"^\| (\d+[a-z]?) \|", table, flags=re.M)]
    assert labels, "no rows found; the table's shape changed"
    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    assert not duplicates, f"validation_matrix.md numbers more than one row {duplicates}"
    bases = sorted({int(label.rstrip("abcdefghijklmnopqrstuvwxyz")) for label in labels})
    assert bases == list(range(1, len(bases) + 1)), f"row numbers skip: {bases}"
    for reference in re.finditer(r"row (\d+)\b", table):
        target = reference.group(1)
        assert any(label.rstrip("abcdefghijklmnopqrstuvwxyz") == target for label in labels), (
            f"the matrix cites row {target}, which it does not contain"
        )


def test_the_validation_matrix_heading_counts_its_own_caveat_paragraphs() -> None:
    """ "N rows that need the prose to be honest" is a count of the paragraphs under it.

    A heading like that is the same kind of fact as a row total, and it rotted once already: the
    section carried three paragraphs under a heading that said four. Deriving it from the body is
    the only way the number stays true without someone remembering to recount.
    """
    table = (REPO_ROOT / "docs" / "validation_matrix.md").read_text(encoding="utf-8")
    match = re.search(
        r"^## (\w+) rows that need the prose to be honest$(.*?)^## ", table, flags=re.M | re.S
    )
    assert match, "the caveat section's heading no longer matches the counted form"
    paragraphs = len(re.findall(r"^\*\*[^*\n]+\*\*", match.group(2), flags=re.M))
    assert _as_int(match.group(1)) == paragraphs, (
        f"the heading says {match.group(1)} rows and the section has {paragraphs} paragraphs"
    )


def test_documents_that_count_the_cpp_tests_agree_with_the_build() -> None:
    """The C++ totals are quoted in six places and changed under everyone this phase.

    Counted from CTest's own list rather than from a document, and skipped only where nothing
    has been built: in CI the lane that runs pytest runs immediately after the build, so the check
    is live there, which is where a stale count would otherwise survive. Only living documents are
    checked -- `docs/release_notes_v1.0.0.md` and the phase reports record the count at their own
    revision, and forcing them to track a moving binary would rewrite history to keep a test green.
    """
    build_dirs = sorted((REPO_ROOT / "build").glob("*")) if (REPO_ROOT / "build").is_dir() else []
    ctest = next(
        (
            directory / "CTestTestfile.cmake"
            for directory in build_dirs
            if (directory / "CTestTestfile.cmake").is_file()
        ),
        None,
    )
    if ctest is None:  # pragma: no cover - depends on whether the tree has been built
        pytest.skip("no CMake build directory; the C++ totals cannot be counted")
    listed = subprocess.run(
        ["ctest", "--test-dir", str(ctest.parent), "-N"],
        capture_output=True,
        text=True,
        check=False,
    )
    counted = re.findall(r"^\s*Test +#", listed.stdout, flags=re.M)
    assert counted, f"ctest -N produced no test list: {listed.stdout[:300]!r}"
    total = len(counted)

    claims = {
        "README.md": r"# (\d+) C\+\+ tests",
        "docs/interview_defense.md": [
            r"(\d+) C\+\+ tests under CTest",
            # The same total in the slash pair of the sheet's provenance row, "`v1.0.0`, 204 / 507
            # now", which the spelling above does not reach. Found by the inventory (#89).
            r"`v1\.0\.0`, (\d+) / \d+ now",
        ],
        "docs/reproducibility.md": [
            r"# (\d+) C\+\+ tests",
            # The same file states the count a second way, three paragraphs below the command that
            # annotates it -- "204 tests under CTest either way" -- and only the first spelling was
            # compared. That is Phase 27's abstract defect inside a document this phase began
            # inventorying, found by the inventory rather than by reading.
            r"(\d+) tests under CTest",
        ],
        # The report's headline paragraph stated its own CTest total for four releases beside a
        # section that stated a different one, and no pattern above reached it.
        "paper/technical_report.tex": r"The suite is (\d+) CTest entries",
    }
    for name, expected in claims.items():
        patterns = expected if isinstance(expected, list) else [expected]
        text = _folded_document(name)
        for pattern in patterns:
            assert re.search(pattern, text), (
                f"{name} no longer states the C++ test count as {pattern!r}, so that spelling "
                f"is unpoliced while still sitting in this guard's list"
            )
        found = [value for pattern in patterns for value in re.findall(pattern, text)]
        assert found, f"{name} no longer states the C++ test count"
        assert all(int(value) == total for value in found), (
            f"{name} says {found}, CTest lists {total}"
        )


def _cpp_test_binary() -> Path | None:
    """The built Catch2 binary, or None where nothing has been compiled.

    Located by glob rather than by preset name, because `dev` locally and `ci` on the runner are
    the same artifact under different directories, and the CTest guard already finds its build
    tree the same way.
    """
    builds = sorted((REPO_ROOT / "build").glob("*")) if (REPO_ROOT / "build").is_dir() else []
    for directory in builds:
        candidate = directory / "quantrisk_tests"
        if candidate.is_file():
            return candidate
    return None


def _source_test_case_count() -> int:
    """`TEST_CASE(` at the start of a line in `tests/cpp/*.cpp`.

    Line-anchored, because a `TEST_CASE` inside a comment or a string would otherwise be counted;
    the count exists to be compared with the binary's own, so a disagreement is a clue rather than
    a verdict about the source style.
    """
    total = 0
    for path in sorted((REPO_ROOT / "tests" / "cpp").glob("*.cpp")):
        total += len(re.findall(r"^\s*TEST_CASE\(", path.read_text(encoding="utf-8"), flags=re.M))
    return total


def test_documents_that_count_the_cpp_assertions_count_the_binarys_own() -> None:
    """`548,368 assertions in 203 test cases` was prose with no owner in four places.

    Finding 49 named this residue: CTest lists tests, not assertions, and the C++ count guard
    already owns the 204 entries, so the two numbers no guard reached were the assertion total
    and the Catch2-case total. This reads both producers. The binary runs `--verbosity quiet` and
    prints `All tests passed (N assertions in M test cases)`; the source is counted by its own
    `TEST_CASE(` blocks and required to agree with the binary's M, which is what turns "the
    documents quote the compiled suite" into "the documents quote the compiled suite, and the
    compiled suite is the source they describe".

    The CTest entry count is deliberately not asserted here -- finding 49's one-number-one-owner
    rule -- and skipping happens only where nothing has been built. In CI the lane that runs pytest
    runs immediately after `cmake --build`, so the check is live there, which is where a stale
    total would otherwise survive.
    """
    binary = _cpp_test_binary()
    if binary is None:  # pragma: no cover - depends on whether the tree has been built
        pytest.skip("no built Catch2 binary; the assertion total cannot be measured")
    run = subprocess.run(
        [str(binary), "--verbosity", "quiet"], capture_output=True, text=True, check=False
    )
    assert run.returncode == 0, run.stdout[-400:] + run.stderr[-400:]
    summary = re.search(r"All tests passed \(([\d,]+) assertions in (\d+) test cases\)", run.stdout)
    assert summary, f"no Catch2 summary line in {run.stdout[-400:]!r}"
    assertions = int(summary.group(1).replace(",", ""))
    cases = int(summary.group(2))

    sourced = _source_test_case_count()
    assert sourced == cases, (
        f"tests/cpp declares {sourced} TEST_CASE blocks and the binary reports {cases}; the two "
        f"producers disagree, so neither number is quotable by a document yet"
    )

    claims = {
        "README.md": r"C\+\+ tests, ([\d,]+) assertions",
        "docs/reproducibility.md": r"C\+\+ tests, ([\d,]+) assertions",
        "docs/interview_defense.md": [
            r"CTest \(([\d,]+) assertions in (\d+) Catch2",
            r"Today that is \d+ C\+\+ tests \(([\d,]+) assertions in (\d+) cases\)",
        ],
        "paper/technical_report.tex": r"([\d{},]+) assertions in (\d+) Catch2 cases",
    }
    for name, patterns in claims.items():
        text = _folded_document(name)
        groups = patterns if isinstance(patterns, list) else [patterns]
        for pattern in groups:
            found = re.findall(pattern, text)
            assert found, f"{name} no longer states the C++ assertion total as {pattern!r}"
            for row in found:
                cells = row if isinstance(row, tuple) else (row, str(cases))
                quoted = int(cells[0].replace("{,}", "").replace(",", ""))
                assert quoted == assertions, (
                    f"{name} quotes {cells[0]} assertions, binary {assertions}"
                )
                assert int(cells[1]) == cases, f"{name} quotes {cells[1]} cases, binary {cases}"


# ---------------------------------------------------------------------------------------------
# The rehearsal brief's question set, counted from `PROJECT_SPEC.md`.
#
# #89 predicted exactly this finding: a document outside the inventory restates a producer in its
# own spelling and nothing asks it. The sheet's opening line says its question set is "22 questions
# in four groups, reproduced here one for one and in order. Nothing added, nothing dropped." The
# brief's section carries 22 question bullets -- 25 bullets, three of which give the answer's shape
# rather than asking anything -- and the sheet has 28 `### Q` headings, because six were added as
# the work itself raised them. So the count needed a producer and the last clause was simply wrong;
# both are fixed here, in that order.

BRIEF_SECTION = "最终面试准备材料"


def _brief_question_groups() -> list[tuple[str, list[str]]]:
    """The brief's question set as (group, titles), in the order `PROJECT_SPEC.md` writes them.

    A bullet is a question when it ends in a question mark. That is the rule the section itself
    follows: its three non-question bullets -- `30秒版本`, `2分钟版本`,
    `deeper technical version` -- describe the shape of an answer, and every other bullet asks
    something.
    """
    text = (REPO_ROOT / "PROJECT_SPEC.md").read_text(encoding="utf-8")
    start = text.index(f"## {BRIEF_SECTION}")
    following = re.search(r"^## ", text[start + 3 :], re.M)
    end = start + 3 + following.start() if following else len(text)
    section = text[start + 3 : end]
    groups: list[tuple[str, list[str]]] = []
    for line in section.splitlines():
        if line.startswith("### "):
            groups.append((line[4:].strip(), []))
        elif line.startswith("- ") and line.rstrip().endswith("?") and groups:
            groups[-1][1].append(line[2:].strip())
    return groups


def test_the_rehearsal_sheet_reproduces_the_question_set_it_cites() -> None:
    """The sheet counts a question set, claims to reproduce it in order, and adds six of its own.

    Three claims in one sentence, none of them read by anything: the size of the brief's set, that
    the sheet reproduces it "one for one and in order", and that nothing was added. Counting is the
    cheap half; the order is the half that matters for a rehearsal sheet, because the numbering is
    how the answers get cited from the brief during an interview.

    The sixth, unclaimed property here is that the sheet's *added* questions never reuse a briefed
    title: a duplicate would let the same question carry two answers, one policed by this guard and
    one not.
    """
    groups = _brief_question_groups()
    briefed = [title for _, titles in groups for title in titles]
    assert briefed, "PROJECT_SPEC.md states no question bullets, so this guard checks nothing"

    text = (REPO_ROOT / "docs/interview_defense.md").read_text(encoding="utf-8")
    stated = re.search(r"(\d+) questions in four groups", text)
    assert stated, "the sheet no longer states the size of the question set it reproduces"
    assert int(stated.group(1)) == len(briefed), (
        f"the sheet cites {stated.group(1)} questions; PROJECT_SPEC.md's {BRIEF_SECTION} "
        f"section asks {len(briefed)}"
    )
    assert len(groups) == 4, f"the brief has {len(groups)} groups, not the four the sheet cites"

    sheet_groups = re.findall(r"^## \d+\. (.+)$", text, re.M)
    assert sheet_groups[: len(groups)] == [name for name, _ in groups], (
        f"the sheet's groups {sheet_groups[: len(groups)]} are not the brief's "
        f"{[name for name, _ in groups]}"
    )

    headings = re.findall(r"^### (Q(\d+))\. (.+)$", text, re.M)
    numbers = [int(row[1]) for row in headings]
    assert numbers == list(range(1, len(numbers) + 1)), (
        f"the sheet's Q labels are not consecutive from 1: {numbers}"
    )
    titles = [row[2].strip() for row in headings]
    assert titles[: len(briefed)] == briefed, (
        "the sheet does not reproduce the brief's questions one for one and in order:\n"
        + "\n".join(
            f"  Q{i + 1}: {title!r} where the brief asks {expected!r}"
            for i, (title, expected) in enumerate(zip(titles, briefed, strict=False))
            if title != expected
        )
    )
    added = titles[len(briefed) :]
    assert added, "the sheet adds no questions, so its 'plus six' clause needs rewriting"
    overlap = sorted(set(added) & set(briefed))
    assert not overlap, f"an added question repeats a briefed title: {overlap}"


# ---------------------------------------------------------------------------------------------
# The report's countable claims: every one is either compared with a producer by a named guard,
# or declared here with the reason it is a statement about the past or about a figure whose
# producer is the artifact named in the same sentence.
# ---------------------------------------------------------------------------------------------


def test_the_identity_checks_the_cli_runs_are_the_ones_the_documents_count() -> None:
    """`7 identity checks` was a shipped number no producer printed.

    README and `docs/reproducibility.md` annotate the `validate` command with its check count, and
    the report states the same quantity spelled ("it runs seven identity checks"), while nothing
    compared any of the three with the checks the CLI actually runs. That is the class findings 55
    and 57 registered for the C++ totals -- a figure several documents repeat and no producer
    prints -- and it survived here because the report's inventory read only the report.

    The producer is the entry point itself, in its JSON mode, resolved beside the running
    interpreter so the guard measures the build under test rather than a source checkout. Every
    document is then required to state what that run reports, which makes a fifth check in the CLI
    oblige three documentation edits. That is the point: the alternative is three documents
    agreeing with each other about a number nothing was asked.
    """
    script = Path(sys.executable).with_name("quantrisk")
    argv = ([str(script)] if script.exists() else [sys.executable, "-m", "quantrisk.cli"]) + [
        "validate",
        "--json",
    ]
    run = subprocess.run(argv, capture_output=True, text=True, check=False)
    assert run.returncode == 0, run.stdout[-400:] + run.stderr[-400:]
    checks = json.loads(run.stdout[run.stdout.index("{") :])["checks"]
    assert checks, "the CLI reported no checks at all, so the count compared below would be vacuous"
    count = len(checks)

    spellings = {
        "README.md": r"(\d+) identity checks",
        "docs/reproducibility.md": r"(\d+) identity checks",
        "paper/technical_report.tex": r"runs (\w+) identity checks",
    }
    for name, pattern in spellings.items():
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        found = re.findall(pattern, text)
        assert found, f"{name} states no identity-check count, so nothing pins it to {count}"
        for token in found:
            assert _as_int(token) == count, (
                f"{name} says {token} identity checks while the installed CLI runs {count}: {found}"
            )


_REPORT_NOUNS = (
    r"(artifacts?|bytes|tests?|cases|entries|rows|members|experiments|limitations|assertions"
    r"|markets|digits|checks|commands|sections|figures|pages|questions|jobs|assets|files"
    r"|modules|routes|rays|rungs|columns|books|releases|scenarios|fields|identities|steps|series"
    r"|windows|benchmarks|fixtures|oracles|versions|tags|presets|packages|observations|sides"
    r"|claims|models|criteria|radii|radius|moves|factors|orders|edges|candidates|ladders"
    r"|stencils|spreads?|runs|readings?|re-freezings?|paths?)"
)
# A number that is part of a word is not a claim: `(?<![A-Za-z\d])` keeps `Catch2 cases` and
# `sklearn2011}. Oracle versions` out of the inventory, which a bare lookbehind on digits let in.
# Three more exclusions, each from reading a real document with this rule (Phase 29 for the first
# two, Phase 35 for the third):
#   `#` -- a cross-reference (`docs/limitations.md` #77) is not a quantity;
#   a bare trailing period -- a list marker or the end of a sentence;
#   `.` -- a number that starts inside a longer dotted token is a slice of it, not a claim.
# Without them the inventory called "#77. Load moves the timings" and "on 5 of 5. Two books sit at
# the grid edge" countable claims, and read `cvxpy 1.9.3 are oracles` as 9.3 oracles and
# `quintic factor 1.000, quartic radius` as 000 radii -- an extractor that invents work for itself,
# and trains the reader to distrust the list it prints. Measured on this repository's seven
# documents, the `.` exclusion removes those two and no other claim.
# The number group keeps `{,}` (LaTeX thousands separators) and allows a decimal tail, so a bare
# trailing period is the only shape excluded.
# A percentage is a spelling of the quantity rather than a new claim kind: `32.6% spread` is a
# countable claim about spreads and the rule missed it because `%` is neither a digit nor a letter.
# Allowing `%` there does not sweep in `99 % VaR` or `100% volatility`, which have no countable
# noun after them and stay outside the inventory.
# `run` is deliberately absent while `runs` is present: in this corpus the singular fires only on
# `uv run` inside a command block, which the extractor would then report as paths-per-second
# claims (measured: `200000 uv run`), while `67 runs` and `160 runs` are real.
_REPORT_CLAIM = re.compile(
    r"(?<![A-Za-z\d#.])"
    r"(\d[\d{},]*(?:\.\d+)?)\s*%?\s+(?:[A-Za-z]+\.?\s+)?" + _REPORT_NOUNS + r"\b",
    re.I,
)

# `the Phase 1 consistency test` is one test named by the phase that wrote it, and `pinned in the
# Phase 2 test files` names files rather than counting them, so the number after the word is a
# label. One word, measured: across the five inventoried documents `Finding`, `Limitation`,
# `Section`, `Figure`, `Table` and bare `Q` produce no claim at all -- their numbers are either
# reached by `#` or sit before a noun that is not in the list -- so adding them here would be an
# exemption with nothing to exempt. The extractor self-test requires every entry to fire.
_LABEL_WORDS = ("Phase",)
_LABEL_BEFORE = re.compile(
    r"(?:^|\W)(?:" + "|".join(_LABEL_WORDS) + r")\s*$",
    re.I,
)


def _is_labelled(flat: str, at: int) -> bool:
    """Whether this number is the last element of a name rather than a quantity.

    Only the words before the number can matter and the pattern is anchored at its end, so the
    window is the last 60 characters rather than the prefix: scanning the prefix instead made this
    quadratic in the document's length, which the extractor self-test measured at 30 seconds.
    """
    return bool(_LABEL_BEFORE.search(flat[max(0, at - 60) : at]))


def _extract_claims(flat: str) -> list[re.Match[str]]:
    """Every countable claim the rule finds, with the label shapes removed.

    Both inventories go through here, so a document cannot be read by a looser rule than the report.
    """
    return [
        match for match in _REPORT_CLAIM.finditer(flat) if not _is_labelled(flat, match.start(1))
    ]


# Pattern -> (owning test, file that holds it). Each pattern is required to occur verbatim in that
# file, so this list cannot claim an ownership some guard does not implement.
_REPORT_OWNED = {
    r"The suite is (\d+) CTest entries": (
        "test_documents_that_count_the_cpp_tests_agree_with_the_build",
        "tests/python/test_artifact_metadata.py",
    ),
    r"(\d+)\s+pytest\s+tests\s+with\s+the\s+validation": (
        "test_the_documents_that_count_python_tests_count_the_ones_that_exist",
        "tests/python/test_artifact_metadata.py",
    ),
    r"(\d+) collected without them": (
        "test_the_offline_test_count_is_measurable_before_the_runner",
        "tests/python/test_artifact_metadata.py",
    ),
    r"([\d{},]+) assertions in (\d+) Catch2 cases": (
        "test_documents_that_count_the_cpp_assertions_count_the_binarys_own",
        "tests/python/test_artifact_metadata.py",
    ),
    r"the frozen manifest hashes (\d+) artifacts": (
        "test_the_report_states_the_manifest_the_freeze_produced",
        "tests/python/test_artifact_metadata.py",
    ),
    r"(?:contains|holds) (\d+) numbered entries": (
        "test_documents_that_count_the_limitations_agree_with_the_file",
        "tests/python/test_artifact_metadata.py",
    ),
    r"(\d+)\s+recorded\s+limitations": (
        "test_documents_that_count_the_limitations_agree_with_the_file",
        "tests/python/test_artifact_metadata.py",
    ),
    r"(\d+) benchmark-suite members execute": (
        "test_documents_that_count_the_suite_members_agree_with_the_registry",
        "tests/python/test_artifact_metadata.py",
    ),
    r"meets it at (\d+)\s+markets": (
        "test_the_derivation_command_agrees_at_the_precision_floor",
        "tests/python/test_fifth_order_partials.py",
    ),
    r"relative worst at (\d+) working digits": (
        "test_the_derivation_command_agrees_at_the_precision_floor",
        "tests/python/test_fifth_order_partials.py",
    ),
}

# One span the owner guard compares as a block: the manifest sentence, whose seven numbers are
# checked by `test_the_report_states_the_manifest_the_freeze_produced` against
# `evidence/manifest.json`. Both anchors and every pattern are required verbatim in that guard, and
# the span is owned only while it still holds exactly as many numbers as that guard compares.
_MANIFEST_REGION = {
    "anchor": "The manifest is committed and verified:",
    "close": "offline fixtures",
    "owner": "test_the_report_states_the_manifest_the_freeze_produced",
    "holder": "tests/python/test_artifact_metadata.py",
}

_REPORT_SRC = re.compile(r"\\src\{([^}]*)\}")

# Everything else, each entry a literal phrase in the report's prose and what its numbers are a
# statement about. The guard checks each entry twice: an anchor that stops matching the document is
# stale, and an anchor that exempts nothing the other rules do not already cover is dead weight, so
# this list can neither accrete nor be padded to make a paragraph pass.
_REPORT_DECLARED: dict[str, str] = {
    "over 30 joint moves": (
        "the equality control's own move count, published in the artifact's control block and "
        "re-executed by the run rather than restated from prose"
    ),
    "at 200{,}000 paths over 250 steps": (
        "the Heston xi=0 collapse probe's path and step configuration, recorded in the model card "
        "the paragraph cites; no frozen artifact carries a Heston result (docs/limitations.md #86)"
    ),
    "combined standard errors for 20, 80 and 320 steps": (
        "the Heston step-refinement probe's rung configuration, recorded in the model card the "
        "paragraph cites; no frozen artifact carries a Heston result (docs/limitations.md #86)"
    ),
    "and variance value over": (
        "the Heston positivity probe's path configuration, in the same card as the two entries "
        "above and for the same reason (docs/limitations.md #86)"
    ),
    "Monte Carlo stress VaR at": (
        "the path count of the stress sampler's cross-check, recorded in the phase report the "
        "sentence cites; the frozen stress artifact carries the ranking and multipliers, not the "
        "Monte Carlo configuration"
    ),
    "Level-1 identities": "names a validation level, not a count of anything",
    "16 later cases had never": (
        "quoted from the incident this report recounts, in that printout's own words"
    ),
    "exposed 6 failing cases": "quoted from the incident this report recounts",
    # `pinned in the Phase 2 test files` was declared here until this phase's label rule made the
    # extractor refuse it: `Phase 2` names the files rather than counting them, so the claim the
    # exemption existed for is no longer a claim. The guard reported the entry as exempting nothing.
    "310 pytest tests with no release tag": (
        "end-of-Phase-9 baseline, recorded in the phase report it cites"
    ),
    "31 CTest entries": "a past CI run quoted as history in the sentence that names it",
    "1{,}000 steps is about 1.6 GB": "a sizing estimate for a hypothetical, labelled as one",
}


# A declared anchor reaches only the words around it, because an exemption is a claim about one
# sentence. The citation rule is the one that reads a whole paragraph, since an artifact backs the
# argument rather than a single clause.
_DECLARE_RADIUS = 40


def _is_declared(flat: str, at: int, anchors: list[str]) -> bool:
    """Whether one of `anchors` sits within `_DECLARE_RADIUS` characters of this claim."""
    return any(
        found.start() - _DECLARE_RADIUS <= at < found.end() + _DECLARE_RADIUS
        for anchor in anchors
        for found in re.finditer(re.escape(anchor), flat)
    )


def _tex_inventory_text() -> tuple[str, str]:
    """The report in two aligned strings, comments blanked and soft breaks turned into spaces.

    Both are the same length, so an offset found in the flat text is an offset in the file, which is
    how the guard reports a claim's line. LaTeX reflows a sentence across physical lines, so an
    inventory read line by line would miss `8 correctness\\nbenchmarks` -- one of the seven numbers
    the manifest guard compares -- and would report the document as quieter than it is.
    """
    source = (REPO_ROOT / "paper" / "technical_report.tex").read_text(encoding="utf-8")
    masked = "\n".join(
        re.sub(r"\S", " ", line) if line.lstrip().startswith("%") else line
        for line in source.splitlines()
    )
    return masked, masked.replace("\n", " ")


def _tex_line(masked: str, offset: int) -> int:
    return 1 + masked.count("\n", 0, offset)


def _paragraph_span(masked: str, offset: int) -> tuple[int, int]:
    """The paragraph around an offset: LaTeX's own unit of one continuing argument.

    A citation belongs to the paragraph, not to a radius in characters. Reading only the nearest
    hundred characters would have called the backtesting design unowned while the sentence four
    lines later named the artifact the design was run to produce.
    """
    before = masked.rfind("\n\n", 0, offset)
    after = masked.find("\n\n", offset)
    return (0 if before < 0 else before + 2), (len(masked) if after < 0 else after)


def _cites_frozen_artifact(window: str, frozen: set[str]) -> bool:
    """Whether the paragraph names a file or directory the evidence freeze hashes.

    A citation ending in `/` names the experiment, and the freeze carries its result files, so a
    directory citation counts only when at least one frozen path lives under it.
    """
    for path in _REPORT_SRC.findall(window):
        clean = path.replace("\\_", "_")
        if clean.endswith("/"):
            if any(frozen_path.startswith(clean) for frozen_path in frozen):
                return True
        elif clean in frozen:
            return True
    return False


def _frozen_artifact_paths() -> set[str]:
    """The repo-relative paths `evidence/manifest.json` hashes -- the producers a sentence can cite.

    A number read out of one of these is not a number the report invented: the freeze carries the
    bytes it was read from, and `test_the_manifest_hashes_every_experiment_results_directory` keeps
    the freeze honest about which directories it covers.
    """
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {str(entry["path"]) for entry in manifest["artifacts"]}


def test_every_countable_claim_in_the_report_is_owned_or_declared() -> None:
    """The report stated one fact two ways, six releases apart, nothing asked what it owns.

    Finding 55 is the mechanism: `paper/technical_report.tex` printed the current artifact count in
    one paragraph and the `v1.1.0` count in another, and every guard over the document compares one
    phrasing each, so neither paragraph was compared with the other. The general form is to
    inventory each `<number> <countable noun>` claim and require each to be either (a) inside a span
    a named guard compares with its producer or (b) declared, with the reason it is not a living
    quantity. Classifying a new numeric sentence is the step missing when the stale count shipped.

    Two things keep the lists honest rather than decorative. An owned pattern must occur verbatim in
    the source of the guard named, so a claim cannot be exempted by a comparison nobody wrote. And a
    list entry that stops matching the document is reported stale, so neither list can accrete.
    """
    masked, flat = _tex_inventory_text()
    assert len(masked) == len(flat), "the inventory lost its offset alignment"
    claims = _extract_claims(flat)
    assert claims, "the extractor matches nothing in the report, so this guard proves nothing"

    owned: list[tuple[int, int]] = []
    for pattern, (owner, holder) in _REPORT_OWNED.items():
        holder_source = (REPO_ROOT / holder).read_text(encoding="utf-8")
        assert pattern in holder_source, (
            f"{pattern!r} is claimed as owned by {owner}, whose source does not contain it"
        )
        hits = list(re.finditer(pattern, flat))
        assert hits, f"the owned pattern {pattern!r} matches nothing in the report any more"
        for hit in hits:
            for group in range(1, hit.lastindex + 1):
                owned.append(hit.span(group))

    region_source = (REPO_ROOT / _MANIFEST_REGION["holder"]).read_text(encoding="utf-8")
    for key in ("anchor", "close"):
        assert _MANIFEST_REGION[key] in region_source, (
            f"the manifest region is keyed on {_MANIFEST_REGION[key]!r}, which its owner "
            f"{_MANIFEST_REGION['owner']} no longer searches for"
        )
    start = flat.find(_MANIFEST_REGION["anchor"])
    assert start >= 0, "the report no longer states the manifest's size in its own words"
    close = start + flat[start:].index(_MANIFEST_REGION["close"]) + len(_MANIFEST_REGION["close"])
    # The owner reads the sentence the same way it does in its own guard: `{,}` becomes `,` before
    # the patterns are applied, because LaTeX writes the thousands separators inside braces.
    region = flat[start:close].replace("{,}", ",")
    patterns = tuple(pattern for pattern, _ in _MANIFEST_CLAIMS)
    for pattern in patterns:
        assert pattern in region_source, f"the manifest guard no longer uses {pattern!r}"
        assert re.search(pattern, region), f"the manifest sentence no longer matches {pattern!r}"
    numbers = re.findall(r"(?<![A-Za-z\d])\d[\d{},]*", region)
    assert len(numbers) == len(patterns), (
        f"the manifest sentence holds {len(numbers)} numbers but the guard compares "
        f"{len(patterns)}; the span is no longer owned as a block"
    )

    for anchor in _REPORT_DECLARED:
        assert anchor in flat, f"the declared anchor {anchor!r} is not in the report: it is stale"

    frozen = _frozen_artifact_paths()
    assert frozen, "the evidence manifest lists no artifacts, so a citation could not be matched"

    def classify(match: re.Match[str], without_anchor: str | None = None) -> str:
        """How this claim is accounted for: `region`, `owned`, `cited`, `declared`, or `unowned`.

        `without_anchor` re-runs the classification with one declared exemption withheld, which is
        how the guard knows an anchor is load-bearing rather than decorative.
        """
        at = match.start(1)
        if start <= at < close:
            return "region"
        if any(lo <= at < hi for lo, hi in owned):
            return "owned"
        anchors = [a for a in _REPORT_DECLARED if a != without_anchor]
        if _is_declared(flat, at, anchors):
            return "declared"
        low, high = _paragraph_span(masked, at)
        return "cited" if _cites_frozen_artifact(flat[low:high], frozen) else "unowned"

    verdicts = [classify(match) for match in claims]
    unowned = [
        (_tex_line(masked, m.start(1)), m.group(0), " ".join(flat[: m.start(1)].split()[-90:]))
        for m, verdict in zip(claims, verdicts, strict=True)
        if verdict == "unowned"
    ]
    assert not unowned, "the report makes countable claims nobody owns:\n" + "\n".join(
        f"  line {line}: {claim!r} near ...{context}" for line, claim, context in unowned
    )

    # A declared anchor has to be the reason at least one claim is accounted for. An exemption that
    # the citation rule or another anchor already covers is dead weight, and dead weight in an
    # exemption list is how a guard stops being able to fail.
    decorative = []
    for anchor, reason in _REPORT_DECLARED.items():
        if not any(
            verdict == "declared" and classify(match, without_anchor=anchor) == "unowned"
            for match, verdict in zip(claims, verdicts, strict=True)
        ):
            decorative.append(f"  {anchor!r}: {reason}")
    assert not decorative, "declared exemptions that exempt nothing:\n" + "\n".join(decorative)


# ---------------------------------------------------------------------------------------------
# The same inventory over the two documents that route a reader to those producers.
#
# Phase 28 registered this debt. The report's claims were inventoried while `README.md` and
# `docs/reproducibility.md` restated the same producers in their own spellings, and reading those
# two files with the rule found a stale twin on the first pass: `docs/reproducibility.md` carried
# "# 481 tests here" three lines above its own correct "494 pytest tests with the `oracles` extra",
# where the prose had been synced in Phase 23 and the command annotation had not been synced at all.
# A guard that requires the right number to be *present* cannot see a wrong number beside it; an
# inventory that requires every number to be *accounted for* can. That is the difference between the
# count guards this repository already has and this one.

_MARKDOWN_INVENTORY = (
    "README.md",
    "docs/reproducibility.md",
    "docs/interview_defense.md",
    "docs/validation_matrix.md",
)


_MD_BACKTICK = re.compile(r"`([^`\n]+)`")


def _markdown_inventory_text(relative: str) -> tuple[str, str]:
    """A markdown document as (masked, flat), offset-aligned the way the tex inventory is.

    Only HTML comments are blanked. A fenced code block is not a comment: the command annotations in
    these two documents are where most of their countable claims live, and skipping the blocks would
    read the files as quieter than they are -- which is how the stale count survived a decade of
    green gates.
    """
    source = (REPO_ROOT / relative).read_text(encoding="utf-8")
    masked = re.sub(r"<!--.*?-->", lambda match: " " * len(match.group(0)), source, flags=re.S)
    return masked, masked.replace("\n", " ")


def _markdown_claim_window(masked: str, at: int) -> tuple[int, int]:
    """The paragraph around a claim, except inside a table, where a row is the unit.

    Markdown reflows a paragraph across physical lines the way LaTeX does, so `_paragraph_span`
    carries over. A table does not: each row describes a different artifact, and letting one row's
    citation excuse the block would rate a findings table as safely as repeating the path in every
    row -- and the findings table is exactly where these documents put their result numbers.
    """
    line_start = masked.rfind("\n", 0, at) + 1
    if masked[line_start : line_start + 1] == "|":
        line_end = masked.find("\n", at)
        return line_start, len(masked) if line_end < 0 else line_end
    return _paragraph_span(masked, at)


def _suite_key_artifacts(frozen: set[str]) -> set[str]:
    """The suite's member keys whose artifact the evidence freeze hashes.

    README's findings table keys its rows by member name rather than by path. The registry is the
    only thing that says which artifact a row describes, so a row counts as cited when its key
    resolves to a frozen file -- and a key the registry has dropped resolves to nothing, which is
    why the citation is read through the registry instead of by pasting a path into the prose.
    """
    return {member.key for member in _load_suite_members() if str(member.artifact) in frozen}


def _cites_frozen_artifact_markdown(window: str, frozen: set[str], keys: set[str]) -> bool:
    """Whether this claim's paragraph or row names a producer the freeze carries."""
    for token in _MD_BACKTICK.findall(window):
        clean = token.strip()
        if clean in frozen or clean in keys:
            return True
        if clean.endswith("/") and any(frozen_path.startswith(clean) for frozen_path in frozen):
            return True
        if any(frozen_path.startswith(clean + "/") for frozen_path in frozen):
            return True
    return False


# Each pattern has to occur verbatim in the guard named as its owner, exactly as in the report's
# list, so a claim here cannot be exempted by a comparison nobody wrote.
_MARKDOWN_OWNED: dict[str, tuple[str, str]] = {
    r"(\d+) identity checks": (
        "test_the_identity_checks_the_cli_runs_are_the_ones_the_documents_count",
        "tests/python/test_artifact_metadata.py",
    ),
    r"all\s+(\d+)\s+members": (
        "test_documents_that_count_the_suite_members_agree_with_the_registry",
        "tests/python/test_artifact_metadata.py",
    ),
    r"(\d+) tests under CTest": (
        "test_documents_that_count_the_cpp_tests_agree_with_the_build",
        "tests/python/test_artifact_metadata.py",
    ),
    r"C\+\+ tests, ([\d,]+) assertions": (
        "test_documents_that_count_the_cpp_assertions_count_the_binarys_own",
        "tests/python/test_artifact_metadata.py",
    ),
    r"carries (\d+) numbered entries": (
        "test_documents_that_count_the_limitations_agree_with_the_file",
        "tests/python/test_artifact_metadata.py",
    ),
    r"(\d+)\s+pytest\s+tests\s+with\s+the\s+`oracles`\s+extra": (
        "test_the_documents_that_count_python_tests_count_the_ones_that_exist",
        "tests/python/test_artifact_metadata.py",
    ),
    r"collects\s+(\d+)\s+tests\s+without\s+it": (
        "test_the_offline_test_count_is_measurable_before_the_runner",
        "tests/python/test_artifact_metadata.py",
    ),
    # The rehearsal sheet's and the matrix's own spellings, added with the inventory extension
    # (#89). Each is the literal pattern the named guard searches with, which is what the verbatim
    # check below enforces: the sheet does not become exempt because a guard *could* read it.
    r"collects (\d+) tests without": (
        "test_the_offline_test_count_is_measurable_before_the_runner",
        "tests/python/test_artifact_metadata.py",
    ),
    r"python -m pytest -q\s+# (\d+) tests collected offline": (
        "test_the_offline_test_count_is_measurable_before_the_runner",
        "tests/python/test_artifact_metadata.py",
    ),
    r"has all (\d+)\s*\n?numbered entries": (
        "test_documents_that_count_the_limitations_agree_with_the_file",
        "tests/python/test_artifact_metadata.py",
    ),
    r"docs/limitations\.md` \((\d+) entries\)": (
        "test_documents_that_count_the_limitations_agree_with_the_file",
        "tests/python/test_artifact_metadata.py",
    ),
    r"(\d+) C\+\+ tests under CTest": (
        "test_documents_that_count_the_cpp_tests_agree_with_the_build",
        "tests/python/test_artifact_metadata.py",
    ),
    r"`v1\.0\.0`, (\d+) / \d+ now": (
        "test_documents_that_count_the_cpp_tests_agree_with_the_build",
        "tests/python/test_artifact_metadata.py",
    ),
    r"CTest \(([\d,]+) assertions in (\d+) Catch2": (
        "test_documents_that_count_the_cpp_assertions_count_the_binarys_own",
        "tests/python/test_artifact_metadata.py",
    ),
    r"Today that is \d+ C\+\+ tests \(([\d,]+) assertions in (\d+) cases\)": (
        "test_documents_that_count_the_cpp_assertions_count_the_binarys_own",
        "tests/python/test_artifact_metadata.py",
    ),
    r"(\d+)\s+Python tests with the validation oracles installed": (
        "test_the_documents_that_count_python_tests_count_the_ones_that_exist",
        "tests/python/test_artifact_metadata.py",
    ),
    r"(?:instead of|rather than) the (\d+) cases they\s+hold": (
        "test_the_documents_that_count_python_tests_count_the_ones_that_exist",
        "tests/python/test_artifact_metadata.py",
    ),
    r"`v1\.0\.0`, \d+ / (\d+) now": (
        "test_the_documents_that_count_python_tests_count_the_ones_that_exist",
        "tests/python/test_artifact_metadata.py",
    ),
    r"(\d+) questions in four groups": (
        "test_the_rehearsal_sheet_reproduces_the_question_set_it_cites",
        "tests/python/test_artifact_metadata.py",
    ),
    r"(\d[\d,]{5,}) paths/s in the C\+\+ core": (
        "test_documents_quote_the_performance_figures_the_artifact_actually_holds",
        "tests/python/test_artifact_metadata.py",
    ),
    r"versus (\d[\d,]{5,}) paths/s in an equivalent pure-Python loop": (
        "test_documents_quote_the_performance_figures_the_artifact_actually_holds",
        "tests/python/test_artifact_metadata.py",
    ),
    r"vectorised NumPy (\d[\d,]{5,}) paths/s": (
        "test_documents_quote_the_performance_figures_the_artifact_actually_holds",
        "tests/python/test_artifact_metadata.py",
    ),
    r"\(([0-9.]+)e-(\d+) worst relative over (\d+) markets": (
        "test_the_derivation_command_agrees_at_the_precision_floor",
        "tests/python/test_fifth_order_partials.py",
    ),
}

# Literal phrases whose numbers are not living quantities, and why. Checked twice, as the report's
# list is: an anchor in neither document is stale, and an anchor that excuses nothing anywhere is
# dead weight -- so this list cannot be padded to make a paragraph pass, and an owner invented here
# fails the verbatim check above rather than passing quietly.
_MARKDOWN_DECLARED: dict[str, str] = {
    "12 artifacts reported VOLATILE": (
        "a dated end-to-end verification of one suite re-run in one fresh clone, recorded in the "
        "paragraph that names that clone; the freeze carries the artifacts, not the tally of a run "
        "whose tree was discarded"
    ),
    # Added with the two documents this phase brings in (#89). Each is load-bearing: the inventory
    # re-runs its own classification with one anchor withheld and reports an exemption that then
    # exempts nothing.
    "on this machine, between the": (
        "a rate from an earlier committed run, quoted as the low of the range the sentence is "
        "describing; the sheet's current readings are owned, this one is history"
    ),
    "memory-light; at the": (
        "another committed reading, in the sentence that says its own workload arithmetic is "
        "arithmetic"
    ),
    "of the same loop": (
        "a workload size chosen to make the division legible, not a measurement of anything"
    ),
    "moved one mutation's anchor from": (
        "quoted from the incident the answer recounts, in the printout's own words -- the same "
        "class as the report's `16 later cases had never`"
    ),
    "let the long-dated book publish a": (
        "the radius a superseded definition of the measure published, named in the sentence that "
        "refutes it"
    ),
    "tests at `v1.0.0`": (
        "the suite's size at that tag, stated by docs/release_notes_v1.0.0.md, which is the "
        "revision the row is about"
    ),
    "corner gaps 1.819909 / 0.456807 /": (
        "the third corner gap rounded to two decimals, printed beside the value it rounds"
    ),
    "the equality control is bit-identity over": (
        "the move count of the equality control, the same figure the report declares and the "
        "artifact's control block publishes"
    ),
    "relative, best of": (
        "the step sizes the Python route tries, a configuration of the test the row names"
    ),
    "A CRR lattice at": (
        "the lattice depth docs/model_cards/crr_binomial.md states beside its measured error; "
        "the frozen artifact carries the slopes and final errors, not the depth"
    ),
}


def test_every_countable_claim_in_the_readme_and_reproducibility_is_owned_or_declared() -> None:
    """Every `<number> <countable noun>` these two documents print has to answer for itself."""
    frozen = _frozen_artifact_paths()
    assert frozen, "the evidence manifest lists no artifacts, so a citation could not be matched"
    keys = _suite_key_artifacts(frozen)
    assert keys, "no suite member's artifact is frozen, so a table row could not cite one"

    documents = {name: _markdown_inventory_text(name) for name in _MARKDOWN_INVENTORY}
    for name, (masked, flat) in documents.items():
        assert len(masked) == len(flat), f"{name}: the inventory lost its offset alignment"

    for pattern, (owner, holder) in _MARKDOWN_OWNED.items():
        assert pattern in (REPO_ROOT / holder).read_text(encoding="utf-8"), (
            f"{pattern!r} is claimed as owned by {owner}, whose source does not contain it"
        )
    dead = [
        pattern
        for pattern in _MARKDOWN_OWNED
        if not any(re.search(pattern, flat) for _, flat in documents.values())
    ]
    assert not dead, f"owned patterns neither document states, so the list has accreted: {dead}"

    # The exemption list is shared by two documents here, where the report's is not, so presence is
    # a property of the set and load-bearing is a property of the verdicts: an anchor only has to be
    # in one of the files, but it has to excuse a claim in at least one of them.
    for anchor in _MARKDOWN_DECLARED:
        assert any(anchor in flat for _, flat in documents.values()), (
            f"the declared anchor {anchor!r} is in neither document: it is stale"
        )

    classified: dict[str, tuple[list, list, object]] = {}
    for name, (masked, flat) in documents.items():
        claims = _extract_claims(flat)
        assert claims, f"{name} yields no countable claims, so this guard proves nothing about it"

        owned: list[tuple[int, int]] = []
        for pattern in _MARKDOWN_OWNED:
            for hit in re.finditer(pattern, flat):
                for group in range(1, (hit.lastindex or 0) + 1):
                    owned.append(hit.span(group))

        def classify(
            match: re.Match[str],
            *,
            skip_anchor: str | None = None,
            flat: str = flat,
            masked: str = masked,
            owned: list[tuple[int, int]] = owned,
        ) -> str:
            at = match.start(1)
            if any(lo <= at < hi for lo, hi in owned):
                return "owned"
            anchors = [a for a in _MARKDOWN_DECLARED if a != skip_anchor]
            if _is_declared(flat, at, anchors):
                return "declared"
            low, high = _markdown_claim_window(masked, at)
            return (
                "cited"
                if _cites_frozen_artifact_markdown(flat[low:high], frozen, keys)
                else "unowned"
            )

        verdicts = [classify(match) for match in claims]
        unowned = [
            (
                1 + masked.count("\n", 0, match.start(1)),
                match.group(0),
                " ".join(flat[: match.start(1)].split()[-70:]),
            )
            for match, verdict in zip(claims, verdicts, strict=True)
            if verdict == "unowned"
        ]
        assert not unowned, f"{name} makes countable claims nobody owns:\n" + "\n".join(
            f"  line {line}: {claim!r} near ...{context}" for line, claim, context in unowned
        )
        classified[name] = (claims, verdicts, classify)

    decorative = [
        anchor
        for anchor in _MARKDOWN_DECLARED
        if not any(
            verdict == "declared" and classify(match, skip_anchor=anchor) == "unowned"
            for claims, verdicts, classify in classified.values()
            for match, verdict in zip(claims, verdicts, strict=True)
        )
    ]
    assert not decorative, f"declared exemptions that exempt nothing: {decorative}"


def test_the_claim_extractor_reads_percentages_and_refuses_labels() -> None:
    """Four shapes of the extractor were stated in comments, and a comment cannot fail.

    Phase 29 wrote the `#` and trailing-period exclusions into the rule and recorded why in the
    block above it; nothing asked whether they fire. This phase added three more shapes -- a `%`
    allowance, a dotted-token exclusion and a label filter -- and one deletion (`run` stays out of
    the noun list while `runs` is in it), so the rule now has five judgements embedded in it and no
    reader. Each property below is two-sided on this repository's own documents: the rule must find
    what it is meant to find and refuse what it is meant to refuse, and the refusal has to be
    demonstrated by the looser rule finding something the shipped one does not.
    """
    corpus = {
        "paper/technical_report.tex": _tex_inventory_text()[1],
        **{name: _markdown_inventory_text(name)[1] for name in _MARKDOWN_INVENTORY},
    }

    # 1. The label filter fires, and no word sits in its list without firing.
    assert _LABEL_WORDS, "the label list is empty, so property 1 below cannot fail"
    refused: list[tuple[str, str]] = []
    for word in _LABEL_WORDS:
        marker = re.compile(rf"(?:^|\W){word}\s*$", re.I)
        rows = [
            (name, match.group(0))
            for name, flat in corpus.items()
            for match in _REPORT_CLAIM.finditer(flat)
            if marker.search(flat[max(0, match.start(1) - 60) : match.start(1)])
        ]
        assert rows, f"`{word}` labels nothing in the inventoried documents; drop it from the list"
        refused += rows
    for name, text in refused:
        assert text not in {m.group(0) for m in _extract_claims(corpus[name])}, (
            f"the label filter did not refuse {text!r}, so property 1 checks nothing"
        )

    # 2. A percentage written beside its noun is a claim about that noun.
    assert r"\s*%?\s+" in _REPORT_CLAIM.pattern, "the `%` allowance is no longer in the rule"
    unpercent = re.compile(_REPORT_CLAIM.pattern.replace(r"\s*%?\s+", r"\s+"), re.I)
    percentages = [
        (name, match.group(0))
        for name, flat in corpus.items()
        for match in _REPORT_CLAIM.finditer(flat)
        if "%" in match.group(0)
    ]
    assert percentages, "no inventoried document states a percentage beside a countable noun"
    for name, text in percentages:
        assert not any(hit.group(0) == text for hit in unpercent.finditer(corpus[name])), (
            f"{text!r} was already a claim without the `%` allowance, so it proves nothing"
        )

    # 3. A number that begins inside a longer dotted token is a slice of it, not a quantity -- the
    #    shape that read `cvxpy 1.9.3 are oracles` as 9.3 oracles.
    undotted = re.compile(
        _REPORT_CLAIM.pattern.replace("(?<![A-Za-z\\d#.])", "(?<![A-Za-z\\d#])"), re.I
    )
    assert undotted.pattern != _REPORT_CLAIM.pattern, "the reconstruction did not loosen the rule"
    sliced = [
        (name, match.group(0))
        for name, flat in corpus.items()
        for match in undotted.finditer(flat)
        if match.group(0) not in {m.group(0) for m in _extract_claims(flat)}
        and not _is_labelled(flat, match.start(1))
    ]
    assert sliced, "the dotted-token exclusion removes nothing from this corpus, so it is untested"

    # 4. `runs` is a countable noun and `run` is a verb in this repository's own command blocks.
    assert "|runs|" in _REPORT_CLAIM.pattern, "the noun list no longer carries `runs` on its own"
    singular = re.compile(_REPORT_CLAIM.pattern.replace("|runs|", "|run|"), re.I)
    commands = [
        match.group(0)
        for flat in corpus.values()
        for match in singular.finditer(flat)
        if match.group(0) not in {m.group(0) for m in _extract_claims(flat)}
    ]
    assert commands, (
        "no `uv run` shape survives the singular noun, so the exclusion of `run` is unmeasured"
    )
    assert any(
        match.group(0).endswith("runs")
        for flat in corpus.values()
        for match in _extract_claims(flat)
    ), "the plural earns nothing either, so the noun list has accreted"


def _repository_release_tags() -> list[str]:
    """Every `vX.Y.Z` tag this clone carries, sorted."""
    listed = subprocess.run(
        ["git", "tag", "--list", "v*", "--sort=v:refname"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if listed.returncode != 0:
        raise RuntimeError(f"`git tag` failed: {listed.stderr[:200]}")
    return sorted(listed.stdout.split())


def test_the_report_lists_the_release_tags_the_repository_carries() -> None:
    r"""The report enumerated its own releases and nothing compared the enumeration with git.

    "Eight release tags exist, \code{v1.0.0} ... and \code{v1.7.0}" is a claim about the object
    store, and the sentence was written by a phase that had just made the eighth tag -- so it was
    true by luck and uncheckable by design. `git tag` is the producer; the report is the quotation;
    between Phase 21
    and this one no guard read either. The spelled count goes through the same producer, because the
    digits and the words are two spellings of one number and policing one spelling is how the stale
    twin survived in `docs/reproducibility.md` (finding 61).

    Like the performance band, this compares history rather than content, so a clone fetched without
    tags has none to compare and the guard says so instead of asserting nothing. That used to
    describe the runner: the pytest lane checked out at depth 1 until Phase 33 gave it `fetch-depth:
    0` with tags, which is what moved its summary from `429 passed, 8 skipped` to `432 passed, 5
    skipped` on an unchanged tree. The skip is left for a reader's own shallow clone. It also means
    the sentence about a release being made cannot be verified before the tag exists: the window in
    which the guard is red while the report names a tag that is not yet in the object store is a
    property of tagging, not a defect, and the phase record names it.
    """
    tags = _repository_release_tags()
    if len(tags) < 2:
        pytest.skip(
            f"this clone carries {len(tags)} release tag(s) (a clone fetched without tags "
            "carries none), so the enumeration cannot be compared; recompute with "
            "`git tag --list 'v*' --sort=v:refname`"
        )

    report = (REPO_ROOT / "paper" / "technical_report.tex").read_text(encoding="utf-8")
    flat = " ".join(report.split())
    start = flat.find("release tags exist,")
    assert start >= 0, "the report no longer enumerates its release tags in its own words"
    end = flat.find("each with the report", start)
    assert end > start, "the release-tag sentence no longer closes with its assets clause"
    sentence = flat[start:end]
    listed = re.findall(r"\\code\{(v\d+\.\d+\.\d+)\}", sentence)
    assert listed == tags, f"the report enumerates {listed} while the object store carries {tags}"

    # The count word sits immediately before the enumeration, so it is read out of the run-in to the
    # sentence rather than out of the sentence itself.
    spelled = re.search(r"(\w+)\s+release tags exist", flat[max(0, start - 60) : end])
    assert spelled, "the count word in the release-tag sentence is unreadable"
    assert _as_int(spelled.group(1)) == len(tags), (
        f"the report says {spelled.group(1)!r} release tags and lists {len(listed)}; "
        f"the repository carries {len(tags)}"
    )


def _report_builder() -> Any:
    """The build script as a module, so the guard reads the same parser the producer uses.

    `spec_from_file_location` alone is not enough: a `@dataclass` in the loaded module raises
    `AttributeError: 'NoneType' object has no attribute '__dict__'` from inside
    `dataclasses._is_type` unless the module is registered in `sys.modules` before `exec_module`.
    """
    path = REPO_ROOT / "scripts" / "build_report.py"
    spec = importlib.util.spec_from_file_location("build_report", path)
    assert spec and spec.loader, f"{path} is not importable"
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_report"] = module
    spec.loader.exec_module(module)
    return module


def test_the_committed_report_pdf_is_bound_to_the_sources_that_rendered_it() -> None:
    r"""`docs/limitations.md` #90, closed: the render now has to name the bytes that made it.

    The report exists twice -- as `paper/technical_report.tex`, which every numeric guard
    reads, and as `paper/technical_report.pdf`, which is what a reader opens and what a
    release attaches. Nothing re-derived the second from the first, so a phase could edit
    the tex, commit the old PDF, and ship a document quoting the superseded figure while the
    whole lane stayed green. It did: `v1.7.0`'s attached PDF restated a freeze six releases
    old (finding 55), and the tree's own PDF lagged an offline test count the tex had
    already corrected (Phase 24 §8). Both were found by a human running `pdftotext`.

    The binding is `paper/technical_report.build.json`, written by
    `scripts/build_report.py`. It records the digest of every source the render consumes,
    plus the digest of the bytes now in the tree. A reproduction is impossible and is not
    claimed: pdfTeX stamps the creation date, so two builds of an unchanged source differ
    (`e72fcfc5…` then `ac7736aa…`, measured 2026-10-09) while the text they typeset is
    identical. So this guard asks the weaker, answerable question -- is the record still
    true of the tree? -- and the moment any input moves without a rebuild, it is not.

    The input set is *parsed* from the document rather than listed, because the report does
    not read only its own file: `\graphicspath{{../}}` plus
    `\includegraphics{experiments/…}` means a suite re-run that redraws one figure makes the
    committed PDF stale, and a hand-maintained list would itself go stale -- the defect this
    closes. The bundle is then cross-checked against a second, cruder count of the same
    statements in the tex, so a parser that silently stopped seeing the figures could not
    shrink the bundle to "the tex alone" and keep passing.
    """
    builder = _report_builder()
    sidecar = REPO_ROOT / "paper" / "technical_report.build.json"
    assert sidecar.is_file(), (
        f"{sidecar.relative_to(REPO_ROOT)} is missing; run `uv run python scripts/build_report.py`"
    )
    record = json.loads(sidecar.read_text(encoding="utf-8"))

    assert record["command"] == "uv run python scripts/build_report.py", (
        f"the record names {record['command']!r}, which is not this script's own command"
    )
    derived = builder.source_bundle()
    recorded = {entry["path"]: entry for entry in record["source_bundle"]}
    assert set(recorded) == {entry["path"] for entry in derived}, (
        f"the record lists {sorted(recorded)} sources while the document now reads "
        f"{[entry['path'] for entry in derived]}"
    )
    for entry in derived:
        path = REPO_ROOT / entry["path"]
        stated = recorded[entry["path"]]
        assert stated["sha256"] == entry["sha256"], (
            f"{entry['path']} hashes to {entry['sha256'][:12]} while the record, written when the "
            f"PDF was built, says {stated['sha256'][:12]}: the tree's render came from other bytes"
        )
        assert stated["bytes"] == entry["bytes"] == path.stat().st_size

    assert record["bundle_sha256"] == builder.bundle_digest(derived), (
        "the bundle digest in the record is not the digest of the sources the document reads now"
    )

    pdf = REPO_ROOT / "paper" / "technical_report.pdf"
    assert record["pdf_sha256"] == sha256_file(pdf), (
        "the record does not describe the PDF in the tree: either the render was replaced without "
        "rewriting the record, or the record was written for bytes that are no longer here"
    )
    assert record["pdf_bytes"] == pdf.stat().st_size

    kinds = {"tex": 0, "bib": 0, "image": 0}
    for entry in derived:
        if entry["path"].endswith(".tex"):
            kinds["tex"] += 1
        elif entry["path"].endswith(".bib"):
            kinds["bib"] += 1
        else:
            kinds["image"] += 1
    assert kinds["tex"] == 1 and kinds["bib"] >= 1 and kinds["image"] >= 1, (
        f"the parsed bundle is {kinds}; a render needs the tex, the bibliography and at least one "
        "at least one figure, so a bundle missing a kind means the parser stopped seeing it"
    )
    tex_text = (REPO_ROOT / "paper" / "technical_report.tex").read_text(encoding="utf-8")
    included = len(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{", tex_text))
    assert included == kinds["image"], (
        f"the document contains {included} \\includegraphics statements and the bundle carries "
        f"{kinds['image']} images"
    )


def test_rebuilding_the_report_from_the_committed_source_typesets_the_same_text() -> None:
    r"""The record is one author's word; a second render is the check on it.

    `test_the_committed_report_pdf_is_bound_to_the_sources_that_rendered_it` can be
    satisfied by editing the record along with the tex, because both are files in the tree.
    This guard takes the committed sources, typesets them again in a scratch copy, and
    compares the *text* the two PDFs render. Text is the right comparator: pdfTeX's date
    stamp makes the bytes differ on every build, so a byte comparison would fail on an
    honest rebuild -- and the measured text digest of two builds of one unchanged source is
    identical (`c5f09b1a…`, 2026-10-09).

    It is also the guard that reproduces finding 55's *shape* rather than its mechanism: put
    the `v1.7.0` PDF back in the tree with a self-consistent record and the binding stays
    green, because the record is true of those bytes. Only the re-render notices that the
    document no longer says what the source says.

    Skipped where no TeX or poppler is installed, which includes CI -- an environment-blind
    guard, declared rather than quietly vacuous, in the same family as the band-history
    guard and the release-tag enumeration. Where it does run, it is by a wide margin the
    slowest test in the lane.
    """
    for tool in ("latexmk", "pdftotext"):
        if shutil.which(tool) is None:  # pragma: no cover - depends on the machine
            pytest.skip(f"{tool} is not installed, so the report cannot be re-typeset here")

    builder = _report_builder()
    committed_pdf = REPO_ROOT / "paper" / "technical_report.pdf"
    committed_text = subprocess.run(
        ["pdftotext", str(committed_pdf), "-"], capture_output=True, check=False
    )
    assert committed_text.returncode == 0, "pdftotext refused the committed PDF"
    assert committed_text.stdout, "the committed PDF extracted to nothing"

    with tempfile.TemporaryDirectory(prefix="quantrisk-report-rebuild-") as scratch:
        root = Path(scratch)
        for entry in builder.source_bundle():
            target = root / entry["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / entry["path"], target)
        completed = subprocess.run(
            ["latexmk", "-pdf", "-g", "-interaction=nonstopmode", "technical_report.tex"],
            cwd=root / "paper",
            capture_output=True,
            text=True,
            check=False,
        )
        rebuilt = root / "paper" / "technical_report.pdf"
        assert completed.returncode == 0 and rebuilt.is_file(), (
            f"the committed source does not build: {completed.stdout[-800:]}"
        )
        rebuilt_text = subprocess.run(
            ["pdftotext", str(rebuilt), "-"], capture_output=True, check=False
        )
    assert rebuilt_text.stdout, "the rebuild produced an extractable-but-empty PDF"

    rendered = hashlib.sha256(rebuilt_text.stdout).hexdigest()
    shipped = hashlib.sha256(committed_text.stdout).hexdigest()
    assert rendered == shipped, (
        "re-typesetting the committed source yields text the PDF in the tree does not "
        "shipped render is not what this source says: rebuild with "
        "`uv run python scripts/build_report.py`"
    )
    # Two truncated extractions would compare equal too, so the control is that the render says
    # something a reader of this document expects to find in it.
    assert b"release tags exist" in rebuilt_text.stdout, (
        "the re-rendered text lacks a sentence a whole document of this report is expected to hold"
    )


def test_the_version_string_the_project_declares_is_one_number_not_four() -> None:
    r"""Seven places spell this release's version; one pair was the only thing compared.

    `pyproject.toml`, `CMakeLists.txt`, `CITATION.cff` (twice, plus the URL of its
    release-notes page), `uv.lock`, `README.md`, `docs/interview_defense.md` and the compiled
    `quantrisk.version()` all carry `1.8.0`. The owner that existed --
    `test_python_package_version_matches_pyproject` in `tests/python/test_smoke.py` -- pairs the
    interpreter's build with the packaging file and nothing else, so a bump that forgot a site
    shipped silently. `CITATION.cff` is one of the four assets attached to every release: a
    citation naming the previous version would be downloadable, citable by a reader, and
    uncheckable by this repository. That is finding 55's mechanism -- one fact, several
    spellings, one spelling compared -- applied to the release's own metadata.

    Every site is read with a pattern that has to match, so a renamed or deleted field fails
    the guard instead of vacating it, and the document quotations are matched as phrases rather
    than as bare digits: `1.8.0` also occurs inside tag names and file paths, and a substring
    test would pass a sentence that never states the version. `date-released` is deliberately
    not asserted against anything -- the only producer of a release date is the release, and
    `docs/limitations.md` plus `docs/release_notes_v1.8.0.md` record that window instead of
    dressing the field up as verified.
    """
    version = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]

    cmake = re.search(
        r"project\(quantrisk\s+VERSION\s+(\d+\.\d+\.\d+)",
        (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8"),
    )
    assert cmake, "CMakeLists.txt no longer declares a version where this guard reads it"

    citation = (REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    cited = re.findall(r"^[ ]*version:[ ]*(\d+\.\d+\.\d+)[ ]*$", citation, re.M)
    assert len(cited) == 2, f"CITATION.cff states the version {len(cited)} times, expected 2"
    tag_url = re.search(r"releases/tag/(v\d+\.\d+\.\d+)", citation)
    assert tag_url, "CITATION.cff no longer carries a release-notes URL to compare"

    lock = re.search(
        r'name = "quantrisk"\nversion = "(\d+\.\d+\.\d+)"',
        (REPO_ROOT / "uv.lock").read_text(encoding="utf-8"),
    )
    assert lock, "uv.lock no longer pins quantrisk's own version where this guard reads it"

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    defence = (REPO_ROOT / "docs" / "interview_defense.md").read_text(encoding="utf-8")

    assert version == cmake.group(1) == lock.group(1) == quantrisk.version(), (
        f"the version disagrees across its declarations: pyproject {version}, "
        f"cmake {cmake.group(1)}, lock {lock.group(1)}, compiled {quantrisk.version()}"
    )
    assert set(cited) == {version}, f"CITATION.cff states {cited} while the package is {version}"
    assert tag_url.group(1) == f"v{version}", (
        f"CITATION.cff points its release-notes URL at {tag_url.group(1)}, "
        f"not the tag this version's release makes"
    )
    assert f"quantrisk.version()  # '{version}'" in readme, (
        f"README's 30-second example does not print version() for {version}"
    )
    assert f"`quantrisk` {version}, released as the tag `v{version}`" in defence, (
        f"the state line of docs/interview_defense.md does not name version {version}"
    )


def _band_edges() -> set[float]:
    return {value for pair in SPEEDUP_BANDS.values() for value in pair}


def _speed_band_printers(paths: list[Path]) -> dict[str, set[tuple[float, float]]]:
    """Which of these documents print a pair that shares an edge with a policed speedup band.

    The predicate is edge-based, not pair-based, on purpose: a document whose band has *drifted*
    (`0.42×`–`0.52×`) still shares an edge with the policed pair, and it is exactly such a document
    that a name-list guard loses track of.
    """
    edges = _band_edges()
    printers: dict[str, set[tuple[float, float]]] = {}
    for path in paths:
        found = _band_pairs(path.read_text(encoding="utf-8"))
        sharing = {pair for pair in found if pair[0] in edges or pair[1] in edges}
        if sharing:
            printers[str(path.relative_to(REPO_ROOT))] = sharing
    return printers


def _candidate_band_documents() -> list[Path]:
    """Every tracked document that could hold a living band claim.

    That is the README, the technical report and `docs/**.md` -- all of it. Enumerated from the tree
    rather than listed, because the whole point of the census is that a document nobody thought to
    list is where the stale spread lived. Nothing is exempted by path any more: the two families
    that used to be (`docs/phase_reports/`, `docs/release_bodies/`) are named file by file in the
    two dated lists, so a new report that prints a band has to be looked at rather than waved
    through by the directory it happens to sit in.
    """
    files = [REPO_ROOT / "README.md", REPO_ROOT / "paper" / "technical_report.tex"]
    files += sorted((REPO_ROOT / "docs").rglob("*.md"))
    return [path for path in files if path.is_file()]


def test_every_document_that_prints_a_speedup_band_is_policed_or_declared_dated() -> None:
    r"""A hand-maintained list of policed documents does not notice what it omits.

    `RANGE_DOCUMENTS` is a literal, so a document printing a stale spread today is simply absent
    from it and no gate reads the sentence. Writing `v1.8.0` made that concrete: the list has to be
    edited at the one moment nobody is looking at it, which is why Phase 30 registered it as debt
    and Phase 32 went looking. Measured with this guard's own predicate, over the 38 documents the
    census reads, 16 state a spread sharing an edge with a policed band -- and four of those sixteen
    were wrong in two different ways, which is why the rule has two halves.

    Nothing owned two of them, and both turned out to be honest dated records:
    `docs/project_scope.md` quotes `0.42×`–`0.57×` inside the Phase 28 row of §9, which is what that
    phase's re-freeze moved the committed band to, and `docs/release_notes_v1.0.0.md` quotes
    `0.42×`–`0.48×` as the spread of the four dated runs behind that release. They are declared, not
    policed.

    Two more were owned by the membership test and red on it, because they speak in the present
    tense of a range the history had already widened. `paper/technical_report.tex` attributed
    `7.77×`–`8.70×`, "an `11.9%` spread", to "thirteen committed re-freezings" -- a prefix of the
    sample presented as the sample, in the document a reviewer opens; the tree holds twenty-two
    readings spanning `7.77×`–`10.31×` (32.6%). `docs/release_notes_v1.6.0.md` wrote that both
    ratios "remain inside the pinned history range". The report was corrected in place, being living
    prose; the release note received a dated amendment, being a record of its own tag.

    The rule is therefore two-sided, and its reach is `_band_pairs`: a spread counts when both of
    its edges carry the multiplication sign, or when a dash or a spoken lead joins two bare
    decimals. The second half is Phase 36's addition -- the report used to write "between
    $0.42\times$ and $0.51\times$", which the anchored form reads, and nothing in the tree wrote the
    band without its unit at all, which it now also reads. Measured: the loose shapes fire 44 times
    over 80 documents and none of those pairs is a policed band's, so this widening changes no
    verdict today; it closes the door a document could leave by deleting two characters, and the
    plant (`living-document-drops-the-multiplication-unit`) is what proves the new shape is not
    decoration. A declaration has to stay load-bearing in both of its kinds -- a dated record ever
    brought up to date stops qualifying as superseded and has to join the policed set, and a record
    exempted because it states *today's* band stops being exempt the moment the band moves. And the
    census shares `_band_pairs` with the membership test so the two cannot disagree about what a
    printed pair is.
    """
    printers = _speed_band_printers(_candidate_band_documents())
    assert printers, "no document prints a speedup band, so this census would prove nothing"

    declared = set(DATED_BAND_RECORDS) | set(TAGGED_BAND_RECORDS)
    unaccounted = sorted(set(printers) - set(RANGE_DOCUMENTS) - declared)
    assert not unaccounted, (
        "these documents state a speedup spread that nothing owns and nothing declares dated: "
        f"{unaccounted}; either add them to RANGE_DOCUMENTS with the spreads they claim, or "
        "declare them in DATED_BAND_RECORDS with the reason they are dated"
    )

    current = set(SPEEDUP_BANDS.values())
    for name, reason in DATED_BAND_RECORDS.items():
        assert reason.strip(), f"{name} is declared dated without a reason"
        assert name in printers, (
            f"{name} is declared as a dated band record but prints no speedup spread any more"
        )
        stale = {pair for pair in printers[name] if pair not in current}
        assert stale, (
            f"{name} is exempt as a dated record yet prints only the current band ({reason}); a "
            "living claim belongs in RANGE_DOCUMENTS"
        )

    # The other dated kind: a record whose band happens to be today's, so there is nothing stale to
    # hold the exemption up. Its exemption is therefore self-terminating -- the first re-freeze that
    # moves the band turns it into a superseded record, and this is the assertion that says so. A
    # A file cannot sit in both lists: one asks for a non-current pair and the other forbids it, so
    # an overlap would let a record choose whichever property it already satisfies.
    for name, reason in TAGGED_BAND_RECORDS.items():
        assert reason.strip(), f"{name} is declared as a record of today's band without a reason"
        assert name not in DATED_BAND_RECORDS, f"{name} is declared both superseded and current"
        assert name in printers, (
            f"{name} is declared as printing the current band but prints no speedup spread"
        )
        assert printers[name] <= current, (
            f"{name} prints {sorted(printers[name] - current)}, which is no longer the band "
            f"the tree carries ({reason}); move it to DATED_BAND_RECORDS with its revision"
        )


def test_the_release_date_the_citation_declares_is_the_tag_that_cut_it() -> None:
    r"""`date-released` was the last unowned field in a downloadable release asset.

    Phase 30 owned the version string and left this field alone on purpose: the only event that
    produces a release date is the release. That event has now happened nine times, and every
    annotated tag knows when it was cut, so the date the citation publishes is checkable against the
    release it names -- `v1.8.0` was tagged on 2026-10-09 and `CITATION.cff` says `2026-10-09`.

    The producer is the tag's *tagger* date, not the commit's author date. The commit date records
    when work was written; the tagger date records when the release was made, and the field claims
    the second. Reading the wrong one would certify a date the repository never released on.

    Two skips, both named rather than silent. A clone carrying no tags has nothing to compare
    against -- what a `--depth 1` clone looks like, and what the runner looked like until Phase 33
    gave the pytest lane its tags and history. And the current version's tag may not exist
    yet, because the tag is cut from the commit that carries this guard -- a release in progress is
    exactly when the field is being written, and no check may demand the future.
    """
    citation = (REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    declared = re.search(r"^date-released:[ \t]*(\d{4}-\d{2}-\d{2})[ \t]*$", citation, re.M)
    assert declared, "CITATION.cff no longer states a date-released this guard can read"

    version = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    listed = subprocess.run(
        [
            "git",
            "for-each-ref",
            "--format=%(refname:lstrip=2) %(taggerdate:format:%Y-%m-%d)",
            "refs/tags",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert listed.returncode == 0, f"git could not list tags: {listed.stderr[:200]}"
    tagged = dict(line.split() for line in listed.stdout.splitlines() if line.strip())
    if not tagged:
        pytest.skip("this clone carries no tags, so no release date has a producer to compare")

    tag = f"v{version}"
    if tag not in tagged:
        pytest.skip(f"{tag} does not exist yet, so this release's date cannot be checked")

    assert declared.group(1) == tagged[tag], (
        f"CITATION.cff dates the release to {declared.group(1)} while {tag} was tagged on "
        f"{tagged[tag]}"
    )


RELEASE_NOTES = sorted((REPO_ROOT / "docs").glob("release_notes_v*.md"))
RELEASE_BODIES = REPO_ROOT / "docs" / "release_bodies"


def test_every_digest_a_release_note_cites_is_its_files_own() -> None:
    """A snapshot whose cited hash is not its own is worse than no snapshot at all.

    This phase wrote `b0a13681…` for the saved second-correction block -- the hash of the text
    before that file was saved with its trailing newline -- and only noticed because the file was
    hashed a second time on the way to the commit. The erratum rule makes those digests the entire
    reason a saved body counts as evidence: a reader restoring a release page from a snapshot whose
    number does not belong to it gets silence where they should get a mismatch.

    Pairing is by proximity rather than by one sentence shape, because the note cites some snapshots
    as "(`sha256 <hex>`)" right after the path and others as "bytes, sha256 `<hex>`". A path with no
    digest inside the window is a failure, so the list cannot accrete uncited files.

    Every release note is read, not one named file. The guard used to point at a hardcoded
    path, which meant the note the repository is writing *now* was outside it: the first snapshot
    attached to a future release would have been policed only if someone remembered to repoint the
    constant, and a forgotten repointing is invisible from inside a green lane. A snapshot cited by
    no note still fails, and one cited by several must satisfy each of them.
    """
    notes = {
        path.name: " ".join(path.read_text(encoding="utf-8").split()) for path in RELEASE_NOTES
    }
    assert notes, "no release notes exist, so this guard would prove nothing"
    paths = sorted(RELEASE_BODIES.glob("*.md"))
    assert paths, "no release-body snapshots exist, so this guard would prove nothing"
    for path in paths:
        cited = f"`docs/release_bodies/{path.name}`"
        naming = [name for name, text in notes.items() if cited in text]
        assert naming, f"{path.name} is named by no release note, so nothing pins its digest"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        for name in naming:
            at = notes[name].find(cited)
            window = notes[name][at : at + 240]
            found = re.search(r"(?:sha256 )?`?([0-9a-f]{64})`?", window)
            assert found, f"{path.name} is cited without a 64-hex digest within 240 characters"
            assert found.group(1) == digest, (
                f"{path.name} hashes to {digest} while {name} cites it as {found.group(1)}"
            )


OFFLINE_PROBE_SCRIPT = REPO_ROOT / "scripts" / "measure_offline_collection.py"

# Every phrasing in which a living document states the oracle-free count. The older guard
# `test_the_documents_that_count_python_tests_count_the_ones_that_exist` compares each document's
# two figures with each other and with the environment it runs in, and the oracle-free half of
# that comparison has only ever been possible on the runner.
_OFFLINE_CLAIMS = {
    "docs/limitations.md": [r"collects (\d+) tests without it"],
    "docs/reproducibility.md": [r"collects (\d+) tests without it"],
    "docs/interview_defense.md": [
        r"collects (\d+) tests without",
        r"— (\d+) without them",
        r"python -m pytest -q\s+# (\d+) tests collected offline",
    ],
    "paper/technical_report.tex": [r"(\d+) collected without them"],
}


def _offline_probe() -> dict[str, Any]:
    """The measurement, taken by calling the script's own function rather than parsing stdout."""
    spec = importlib.util.spec_from_file_location(
        "measure_offline_collection", OFFLINE_PROBE_SCRIPT
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        result = module.measure()
    finally:
        del sys.modules[spec.name]
    return result


def test_the_offline_test_count_is_measurable_before_the_runner() -> None:
    """#63 forbade deriving the offline count, so this measures it instead of waiting.

    The pair of Python test counts has been checkable in only one of its two environments: the
    with-oracles half on any development machine, the oracle-free half on the CI lane that installs
    without the extra. That asymmetry produced findings 54(b) and 55(d) -- a phase adds tests, syncs
    the figure it can see, and learns the other from a red runner one push later.
    `scripts/measure_offline_collection.py` is the second producer, so a document can be compared
    with an oracle-free measurement in the same command that reads the other one.

    Three assertions make `collected` mean the runner's number rather than this machine's: nothing
    may error during collection, the four oracle-gated modules have to appear as skip records, and
    the blocked set has to be non-empty. Without them a probe that blocked nothing would report the
    with-oracles total and look green.
    """
    probe = _offline_probe()
    assert len(probe["blocked_imports"]) >= 4, probe
    assert probe["collection_errors"] == 0, (
        f"gated modules became collection errors, which is not the runner's shape: {probe['tail']}"
    )
    assert probe["module_skips"] == 4, probe
    assert probe["collected"] is not None, probe["tail"]
    collected = int(probe["collected"])

    for name, patterns in _OFFLINE_CLAIMS.items():
        text = _folded_document(name)
        for pattern in patterns:
            found = re.findall(pattern, text)
            assert found, f"{name} no longer states the offline count as {pattern!r}"
            for value in found:
                assert int(value) == collected, (
                    f"{name} quotes {value} tests without the oracles; the probe collects "
                    f"{collected}"
                )


MANIFEST = REPO_ROOT / "evidence" / "manifest.json"

# The report's own sentence, in the order it writes it. `evidence/manifest.json`'s
# `totals` block is the producer of all seven of these numbers, so the comparison is between a
# document and the artifact it claims to describe -- not between two documents restating each other.
_MANIFEST_CLAIMS = (
    (r"(\d+) artifacts", ("artifacts",)),
    (r"([\d,]+) bytes", ("bytes",)),
    (r"(\d+) correctness\s+benchmarks", ("by_category", "correctness_benchmark")),
    (r"(\d+) performance benchmark", ("by_category", "performance_benchmark")),
    (r"(\d+) statistical experiment files", ("by_category", "statistical_experiment")),
    (r"(\d+) suite-aggregate files", ("by_category", "suite_aggregate")),
    (r"(\d+)\s+offline fixtures", ("by_category", "offline_fixture")),
)


def _tex_manifest_sentence(source: str) -> str:
    """The window of the report that states the manifest's size, or fail for its absence.

    Anchored on the sentence's own opening words rather than a line number, because the paragraph
    reflows whenever LaTeX re-breaks it.
    """
    start = source.find("The manifest is committed and verified:")
    assert start >= 0, "the report no longer states the manifest's size in its own words"
    window = source[start : start + 700].replace("{,}", ",")
    assert "offline fixtures" in window, "the report's manifest sentence has been cut short"
    return window


def test_the_report_states_the_manifest_the_freeze_produced() -> None:
    """`paper/technical_report.tex` restated the freeze as it was at `v1.1.0`, for six releases.

    69 artifacts, 6,208,835 bytes and 40 statistical experiment files are exactly
    `evidence/manifest.json`'s `totals` at the `v1.1.0` tag, and the same document's headline
    paragraph prints the current 94. One fact, two statements in one PDF, and the stale one survived
    `v1.2.0` through `v1.7.0` because no reader compared them -- which is what a count with no owner
    costs.
    """
    totals = json.loads(MANIFEST.read_text(encoding="utf-8"))["totals"]
    window = _tex_manifest_sentence(
        (REPO_ROOT / "paper" / "technical_report.tex").read_text(encoding="utf-8")
    )
    for pattern, key_path in _MANIFEST_CLAIMS:
        found = re.search(pattern, window)
        assert found, f"the report's manifest sentence no longer matches {pattern!r}"
        expected = totals
        for step in key_path:
            expected = expected[step]
        assert int(found.group(1).replace(",", "")) == expected, (
            f"the report says {found.group(1)} where the manifest totals say {expected} "
            f"for {'/'.join(key_path)}"
        )

    # The headline paragraph, two pages from the sentence above, states the same artifact count in
    # its own words. Finding 55(a) is what happens when only one of the two is compared:
    # shipped contradicting itself, with the stale copy six releases old.
    headline = re.search(
        r"the frozen manifest hashes (\d+) artifacts",
        (REPO_ROOT / "paper" / "technical_report.tex").read_text(encoding="utf-8"),
    )
    assert headline, "the report's headline no longer states the manifest's artifact count"
    assert int(headline.group(1)) == totals["artifacts"], (
        f"the report's headline says {headline.group(1)} artifacts, the freeze "
        f"holds {totals['artifacts']}"
    )


FIFTH_ORDER_ARTIFACT = (
    REPO_ROOT
    / "experiments"
    / "fifth_order_crossing_map"
    / "results"
    / "fifth_order_crossing_map.json"
)


def _report_prose() -> str:
    """The report's text with LaTeX comments dropped and its escapes for `_` undone.

    Comments are dropped because the source carries commented-out prose no reader sees, and a
    guard that matches them can be satisfied by a paragraph that is not in the PDF.
    """
    source = (REPO_ROOT / "paper" / "technical_report.tex").read_text(encoding="utf-8")
    lines = [line for line in source.splitlines() if not line.lstrip().startswith("%")]
    return " ".join(lines).replace("\\_", "_")


def test_every_registered_experiment_is_named_in_the_report() -> None:
    """The report omitted the experiment that answered its own open question.

    Phase 20's paragraph in `paper/technical_report.tex` ended "the experiment that would use these
    terms was specified and then deliberately not run". Phase 21 ran it, published the answer, and
    left the sentence standing, because every guard over this document compares numbers and none of
    them asked whether the document still describes each member of the suite. An experiment that
    ran, is registered, and appears nowhere in the report is the same evidence hole as a number
    nobody owns.

    Keyed on the directory rather than the script path, because the report cites most members by
    their results file (`experiments/real_data_risk_study/results/...`), which the path form would
    miss while the directory form matches.
    """
    prose = _report_prose()
    directories = {
        f"experiments/{Path(member.script).parent.name}/"
        for member in _load_suite_members()
        if member.script.startswith("experiments/")
    }
    absent = sorted(directory for directory in directories if directory not in prose)
    assert not absent, f"the report never names these registered experiments: {absent}"


def test_the_report_states_the_order_five_headline_the_artifact_holds() -> None:
    """Each figure in the report's order-five paragraph is read from the field that produced it.

    The widening count, the unchanged count, how many books the quintic sits closest on, the two
    books that widened with their quartic and quintic radii, and the span of the order-five-to-four
    ratio are all re-derived here. A re-run that moves any of them reddens the document that quotes
    it, which is the only way a paragraph written from an artifact stays true to it.
    """
    payload = json.loads(FIFTH_ORDER_ARTIFACT.read_text(encoding="utf-8"))
    headline = payload["headline"]
    books = {book["label"]: book for book in payload["books"]}
    prose = _report_prose()

    widening = (
        f"widens the radius on {headline['books_widening_at_order_five']} of the "
        f"{headline['books_measured']}"
    )
    assert widening in prose, "the report no longer states the widening count as the artifact's"
    assert f"leaves {headline['books_unchanged_at_order_five']} unchanged" in prose, (
        "the report no longer states the unchanged count"
    )
    assert f"the closest of the three truncations on all {headline['books_measured']}" in prose, (
        "the report no longer states how many books the quintic sits closest on"
    )

    for label in ("published ladder", "deep out of the money"):
        book = books[label]
        claimed = f"from ${book['radius_quartic']:.2f}$ to ${book['radius_quintic']:.2f}$"
        assert claimed in prose, (
            f"the report does not state {label}'s quartic-to-quintic radius as {claimed!r} "
            f"(artifact: {book['radius_quartic']} -> {book['radius_quintic']})"
        )

    ratios = [entry["order_five_over_four_at_measure_column"] for entry in payload["fits"].values()]
    span = f"{min(ratios):.3f} to {max(ratios):.3f}"
    assert span in prose, f"the report does not state the ratio span the artifact gives ({span})"

    smallest = min(
        payload["fits"],
        key=lambda label: payload["fits"][label]["order_five_over_four_at_measure_column"],
    )
    widest = max(books, key=lambda label: books[label]["widening_factor_quintic"])
    assert smallest == widest, (
        f"the report's mechanism-free reading depends on the smallest ratio ({smallest}) being the "
        f"largest widening ({widest}); the paragraph has to be rewritten if that changes"
    )


SPEED_ARTIFACT = REPO_ROOT / "benchmarks/performance/results/monte_carlo_speed.json"


# The speed artifact's headline fields are volatile *by declaration* — `speedup_vs_pure_python`,
# `speedup_vs_numpy` and `results_seconds` sit in `VOLATILE_KEYS` — so the manifest reads any re-run
# of it as VOLATILE and certifies nothing about its ratios. Four documents nevertheless quote those
# ratios in the present tense, and that combination is where the digits went stale: the freeze
# behind v1.3.0 measured 7.909× while docs/validation_matrix.md described the same file as
# `8.0–8.4×`, and
# README.md quoted "45.5M vs 5.5M paths/s in the current artifact". A figure with no checker is a
# figure nobody reads, so the prose is required to carry what the artifact says.
def _speed_figures(payload: dict[str, Any]) -> dict[str, str]:
    """The artifact's own timing fields, formatted the way each document quotes them."""
    timing = payload["results_seconds"]

    def scientific(value: float) -> str:
        mantissa, exponent = format(value, ".2e").split("e")
        return f"{mantissa}e{int(exponent)}"

    figures = {
        "python_ratio": f"{payload['speedup_vs_pure_python']:.2f}",
        "numpy_ratio": f"{payload['speedup_vs_numpy']:.3f}",
        "generated_at": payload["generated_at_utc"],
    }
    for side in ("cpp", "python", "numpy"):
        row = timing[side]
        figures[f"mean_{side}"] = f"{row['mean_seconds']:.6f}"
        figures[f"std_{side}"] = scientific(row["std_seconds"])
        figures[f"std6_{side}"] = f"{row['std_seconds']:.6f}"
        figures[f"pps_{side}"] = format(round(row["paths_per_second_mean"]), ",")
        figures[f"tex_pps_{side}"] = format(round(row["paths_per_second_mean"]), ",").replace(
            ",", "{,}"
        )
        figures[f"mega_{side}"] = f"{row['paths_per_second_mean'] / 1e6:.1f}"
        figures[f"estimate_{side}"] = f"{payload['measured_prices'][side]:.5f}"
        figures[f"z_{side}"] = f"{payload['z_score_vs_analytic'][side]:+.3f}"
        figures[f"tex_z_{side}"] = f"${payload['z_score_vs_analytic'][side]:+.3f}$"
    return figures


PROSE_FIGURES = {
    "README.md": (
        # A claim, not a digit: the committed run is also the widest measurement the band has, so a
        # bare `8.88×` survives a tamper of the point figure because the band's own upper edge still
        # prints it. The 47-plant sweep found this by escaping -- the substitution landed, the bytes
        # changed, and the guard stayed green reading the other occurrence.
        "`{python_ratio}×` in the artifact now in the tree",
        "{numpy_ratio}×",
        "{mega_cpp}M vs {mega_python}M paths/s",
    ),
    "docs/interview_defense.md": (
        "{python_ratio}× on this machine",
        "{pps_cpp} paths/s",
        "{pps_python} paths/s",
        "{pps_numpy} paths/s",
        "{python_ratio}×",
        "{numpy_ratio}×",
        "{mean_cpp} s",
        "{mean_python} s",
        "{mean_numpy} s",
        "{std_cpp}",
        "{std_python}",
        "{std_numpy}",
    ),
    "paper/technical_report.tex": (
        "${python_ratio}\\times$",
        "${numpy_ratio}\\times$",
        "{generated_at}",
        "{mean_cpp} & {std6_cpp} & {tex_pps_cpp} & {estimate_cpp} & {tex_z_cpp}",
        "{mean_python} & {std6_python} & {tex_pps_python} & {estimate_python} & {tex_z_python}",
        "{mean_numpy} & {std6_numpy} & {tex_pps_numpy} & {estimate_numpy} & {tex_z_numpy}",
    ),
}

# The rehearsal sheet quotes the artifact's three rates in running prose, where a formatted
# substring proves only that the digits appear *somewhere* in the file. These phrases bind each
# number to the implementation named beside it, and the claim inventory reads exactly these
# patterns -- so `21,130,162 paths/s a loaded desktop has shown`, a superseded reading, cannot
# borrow the current value's ownership.
_RATE_PHRASES = {
    r"(\d[\d,]{5,}) paths/s in the C\+\+ core": "cpp",
    r"versus (\d[\d,]{5,}) paths/s in an equivalent pure-Python loop": "python",
    r"vectorised NumPy (\d[\d,]{5,}) paths/s": "numpy",
}

# Each policed document names the spreads it is required to state. `docs/findings.md` and
# `docs/portfolio_audit.md` make a NumPy-only claim and are not obliged to print the Python spread;
# everything else carries both. The census guard below stops this dict shrinking silently.
RANGE_DOCUMENTS: dict[str, tuple[str, ...]] = {
    "README.md": ("python", "numpy"),
    "docs/validation_matrix.md": ("python", "numpy"),
    "docs/interview_defense.md": ("python", "numpy"),
    "docs/reproducibility.md": ("python", "numpy"),
    "docs/limitations.md": ("python", "numpy"),
    "paper/technical_report.tex": ("python", "numpy"),
    "docs/findings.md": ("numpy",),
    "docs/portfolio_audit.md": ("numpy",),
    "docs/release_notes_v1.5.0.md": ("python", "numpy"),
    "docs/release_notes_v1.6.0.md": ("python", "numpy"),
    "docs/release_notes_v1.7.0.md": ("python", "numpy"),
    "docs/release_notes_v1.8.0.md": ("python", "numpy"),
}

# Dated records that print a superseded spread on purpose. Each reason has to be load-bearing: the
# census requires the file to still print a pair that is *not* the current band, so a record that is
# ever brought up to date stops qualifying as dated and must be policed like the others.
DATED_BAND_RECORDS: dict[str, str] = {
    "docs/release_notes_v1.4.0.md": (
        "scopes its span to `the thirteen committed measurements of that file`, a prefix of history"
    ),
    "docs/integrity_audit.md": "finding entries state the revision each audited",
    "docs/release_notes_v1.0.0.md": (
        "quotes the four dated runs behind `v1.0.0` and their spread, `0.42×`–`0.48×`"
    ),
    "docs/project_scope.md": (
        "§9 carries one row per phase, and the Phase 28 row's `0.42×`–`0.57×` is what that phase's "
        "re-freeze moved the committed band to"
    ),
    # Named file by file from Phase 36. These nine were exempted by path prefix -- the two families
    # `docs/phase_reports/` and `docs/release_bodies/` -- so the census never read them and a report
    # writing a band in the present tense was invisible. Each reason states the revision the file
    # records, and the guard requires it to still print a pair that is NOT today's band: a dated
    # record brought up to date stops qualifying here and joins the policed set instead.
    "docs/phase_reports/phase-14-verification-debt.md": (
        "records the run whose committed band was `7.77×`–`8.70×`, beside the `0.42×`–`0.51×` "
        "of its own date and the gap it found"
    ),
    "docs/phase_reports/phase-18-five-book-radius.md": (
        "the five-book phase's band reading, `7.77×`–`8.70×`, before two re-freezings widened it"
    ),
    "docs/phase_reports/phase-22-v1.7.0.md": (
        "states the band as `v1.7.0` shipped it, which is the revision this report is about"
    ),
    "docs/phase_reports/phase-28-sixth-book.md": (
        "records `7.77×`–`8.88×`, the band the sixth book's re-freeze produced before Phase 30"
    ),
    "docs/phase_reports/phase-32-band-census-and-release-date.md": (
        "quotes the superseded `0.42×`–`0.48×` and `7.77×`–`8.70×` as the bands the census "
        "it records found stale, and the raw `7.774`–`10.306` edges it chose to round"
    ),
    "docs/release_bodies/v1.7.0-body-before-2026-10-06.md": (
        "a superseded draft of the `v1.7.0` asset body, kept as the revision history of a "
        "published release note; its band predates the next re-freeze"
    ),
    "docs/release_bodies/v1.7.0-body-before-2026-10-07.md": (
        "the second superseded `v1.7.0` body draft, same reason; neither is the tagged asset"
    ),
    # The first document the renamed census caught was the phase that renamed it: this report
    # quotes the planted and the superseded bands while discussing the rule, so it prints a
    # spread. The honest disposition of a dated record printing a superseded spread is to be
    # declared -- not reworded until the guard stops seeing it.
    "docs/phase_reports/phase-36-band-census-without-its-unit.md": (
        "quotes planted and superseded spellings while describing the census that had to "
        "declare this file"
    ),
}

# Dated records that state TODAY's band, and are exempt from tracking it only while they do.
#
# These two are the release's own documents, written at the revision whose artifact produced the
# current band, so nothing in them is stale yet -- and the point of listing them is that the status
# is self-terminating: the moment the band moves, the guard below reports them as printing a pair
# that is no longer today's and they belong in `DATED_BAND_RECORDS`, with a reason naming the
# revision they record -- which is exactly how the two `v1.7.0` bodies got there.
TAGGED_BAND_RECORDS: dict[str, str] = {
    "docs/phase_reports/phase-30-v1.8.0.md": (
        "the release report for `v1.8.0`, whose re-freeze produced the band the tree carries now"
    ),
    "docs/release_bodies/v1.8.0-body-2026-10-09.md": (
        "the body of the published `v1.8.0` asset, which states the band as that release shipped it"
    ),
}

# The spread of the speed benchmark's two ratios over every committed measurement of the artifact —
# fourteen at the 1.5.0 freeze, recomputable with the command printed in docs/reproducibility.md.
# Both edges are the *rounded* min and max, which is what the history guard derives, so a raw value
# of 0.5104 belongs to the documented band edge 0.51 rather than falling outside it.
SPEEDUP_BANDS = {"python": (7.77, 10.31), "numpy": (0.42, 0.51)}

# The spread each band is printed with, in percent: (max - min) / min over the committed readings,
# to one decimal. Pinned for the same reason the bands are pinned: a guard that could only read
# the one revision a shallow clone carries would derive a zero-width spread. Phase 33 gives the
# runner a full clone, so this constant is compared with the history on CI too.
SPEEDUP_SPREADS = {"python": 32.6, "numpy": 20.8}

# The living documents that state those spreads, written in their own words. Each entry is compared
# as a block, band edges and all, so a document cannot keep the pair and quietly change the number
# beside it -- the half of `docs/limitations.md` #92 that this phase closes.
SPREAD_CLAIMS: dict[str, tuple[str, ...]] = {
    "docs/reproducibility.md": (
        "`{py_lo}×`–`{py_hi}×` against a pure Python loop ({py_spread}% spread)",
        "`{np_lo}×`–`{np_hi}×` against vectorised NumPy ({np_spread}% spread)",
    ),
    "docs/limitations.md": (
        "`{py_lo}×`–`{py_hi}×` ({py_spread}%) and `{np_lo}×`–`{np_hi}×` ({np_spread}%)",
    ),
    "docs/release_notes_v1.8.0.md": (
        "`{py_lo}×–{py_hi}×` / `{np_lo}×–{np_hi}×` ({py_spread}% and {np_spread}%)",
    ),
    "paper/technical_report.tex": (
        "${py_lo}\\times$--${py_hi}\\times$ --- a ${py_spread}\\%$ spread",
        "${np_lo}\\times$--${np_hi}\\times$, a ${np_spread}\\%$ spread",
    ),
}


def _spread_fields() -> dict[str, str]:
    """The pinned band and spread, rendered the way the documents write them."""
    (py_lo, py_hi), (np_lo, np_hi) = SPEEDUP_BANDS["python"], SPEEDUP_BANDS["numpy"]
    return {
        "py_lo": f"{py_lo:.2f}",
        "py_hi": f"{py_hi:.2f}",
        "np_lo": f"{np_lo:.2f}",
        "np_hi": f"{np_hi:.2f}",
        "py_spread": f"{SPEEDUP_SPREADS['python']:.1f}",
        "np_spread": f"{SPEEDUP_SPREADS['numpy']:.1f}",
    }


def _committed_speed_ratios() -> list[tuple[float, float]]:
    """The ratio of every version of the artifact in this repository's history."""
    relative = str(SPEED_ARTIFACT.relative_to(REPO_ROOT))
    history = subprocess.run(
        ["git", "log", "--format=%H", "--", relative],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if history.returncode != 0:
        raise RuntimeError(f"`git log` could not read {relative}: {history.stderr[:200]}")
    revisions = []
    for sha in history.stdout.split():
        shown = subprocess.run(
            ["git", "show", f"{sha}:{relative}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if shown.returncode != 0:
            continue
        payload = json.loads(shown.stdout)
        revisions.append((payload["speedup_vs_pure_python"], payload["speedup_vs_numpy"]))
    return revisions


def _documented_ranges(text: str) -> set[tuple[float, float]]:
    """Every `low–high` decimal pair the document states, whatever it is a range of."""
    return {
        (float(low), float(high))
        for low, high in re.findall(r"(\d+\.\d+)[^\d\n]{1,4}(\d+\.\d+)", text)
    }


# A gap-wide detector would have to be trusted, and the census cannot trust one: the
# `(\d+\.\d+)[^\d\n]{1,16}?` form pairs any two decimals that happen to sit near each other, so a
# document reading "at 0.15 the residual is 0.42" would be reported as printing the band 0.15-0.42.
# Under a membership test that only ever asks for one specific pair that sloppiness was harmless;
# under a census that names the documents holding a stale spread it fabricates findings. So the
# shape is anchored twice: both numbers carry a multiplication sign, and the gap between them
# carries a range mark. `7.77×–10.31×` and `$7.77\times$--$10.31\times$` qualify, as does
# "between $0.42\times$ and $0.51\times$", which is how the report words two of its own bands. A
# neighbour pair like `8.378×` / `0.5656×` -- two readings of one run, not a spread -- does not.
_BAND_SHAPE = re.compile(
    r"(between|from)?[\s$]{0,4}(\d+\.\d+)[\s`'”‘\"]*(?:×|\\times)"
    r"([^\d\n]{0,16}?)(\d+\.\d+)[\s`'”‘\"]*(?:×|\\times)",
    re.IGNORECASE,
)

# The marks the corpus really uses between a band's two edges.
_RANGE_MARKS = ("–", "—", "--")

# Two unit-less spellings of the same claim, each with a gap the corpus cannot use by accident.
#
# `7.77–10.31` and "`0.42`–`0.51`": a dash between two decimals with nothing between them but
# quotation and spacing. `between 0.42 and 0.51`: the spoken form, which requires its lead word --
# because the corpus contains the counter-example twice. `10.31× and 0.495×` is two readings of one
# run, not a spread, and `docs/integrity_audit.md` records that an earlier gap-wide detector paired
# exactly those numbers; the audit's lesson is that a mark alone does not make a range. Neither
# shape allows a unit inside the gap: a band carrying `×` on both edges belongs to `_BAND_SHAPE`,
# which is stricter about what may sit between the two units.
#
# What this costs and what it buys is measured, not assumed: over the tree's 81 documents the united
# shape finds 68 decimal pairs and these two find 52 more. Three of the 52 share an edge with a
# policed band, and all three are in `docs/phase_reports/phase-36-…md` -- the report that wrote the
# rule, quoting the bands it had to discuss. So the first document the widened census caught was the
# phase's own, which is the cleanest available evidence that the shape reads rather than decorates:
# that file would have been invisible to the old rule, and it is now declared like every other dated
# record. The rest of the widening is latent -- a rule a document used to be able to leave by
# deleting two characters -- and its reachable red is a plant
# (`unlisted-document-states-a-band-without-its-unit`). The deferred cost is stated plainly: pairs
# like `(0.05, 0.15)` and `(1.07, 1.22)` sit unclaimed in dated records today and would read as band
# claims the day a radius edge joins `SPEEDUP_BANDS`.
_LOOSE_DASHED = re.compile(
    r"(?<![\d.])(\d+\.\d+)[\s`'\"”‘]*(?:[–—]|--)[\s`'\"”‘]*(\d+\.\d+)(?![\d.])"
)
_LOOSE_SPOKEN = re.compile(
    r"\b(?:between|from)\s+(\d+\.\d+)\s+(?:to|and)\s+(\d+\.\d+)",
    re.I,
)


def _band_pairs(text: str) -> set[tuple[float, float]]:
    """Every speedup spread the document states, with its unit or without one.

    Three shapes, one predicate each. The anchored form needs the multiplication unit on both edges;
    the two loose forms read a dash or a spoken lead between bare decimals. A pair only becomes a
    claim once the census's edge test recognises it, so a loose match between two unrelated decimals
    costs the census nothing.
    """
    pairs = {(float(low), float(high)) for low, high in _LOOSE_DASHED.findall(text)}
    pairs |= {(float(low), float(high)) for low, high in _LOOSE_SPOKEN.findall(text)}
    for lead, low, gap, high in _BAND_SHAPE.findall(text):
        marked = any(mark in gap for mark in _RANGE_MARKS)
        spoken = " and " in gap.lower() and (lead or "").lower() in ("between", "from")
        if marked or spoken:
            pairs.add((float(low), float(high)))
    return pairs


def test_documents_quote_the_performance_figures_the_artifact_actually_holds() -> None:
    """A ratio that regenerates on every run still has to match the file it claims to quote."""
    figures = _speed_figures(json.loads(SPEED_ARTIFACT.read_text(encoding="utf-8")))
    for name, claims in PROSE_FIGURES.items():
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        for claim in claims:
            expected = claim.format(**figures)
            assert expected in text, (
                f"{name} does not carry {expected!r}, which is what "
                f"{SPEED_ARTIFACT.relative_to(REPO_ROOT)} measures"
            )

    sheet = (REPO_ROOT / "docs/interview_defense.md").read_text(encoding="utf-8")
    for pattern, side in _RATE_PHRASES.items():
        found = re.findall(pattern, sheet)
        assert found == [figures[f"pps_{side}"]], (
            f"the sheet's {pattern!r} carries {found} where the artifact measures "
            f"{figures[f'pps_{side}']} paths/s for {side}"
        )


def test_the_documented_speedup_ranges_contain_the_current_measurement() -> None:
    """The ranges are claims about a sample, and the current artifact has to be inside them.

    `SPEEDUP_BANDS` is written down rather than derived because a clone fetched with a depth limit
    sees one measurement: a guard that recomputes the band from history there demands
    that the documents quote `0.45-0.45`, which is how this release's first runner attempt went
    red -- on the runner, which checked out at depth 1 until Phase 33. The history is still checked,
    in the test below, wherever a clone carries it.
    """
    payload = json.loads(SPEED_ARTIFACT.read_text(encoding="utf-8"))
    current = {
        "python": payload["speedup_vs_pure_python"],
        "numpy": payload["speedup_vs_numpy"],
    }
    for kind, (low, high) in SPEEDUP_BANDS.items():
        # The band is the *rounded* envelope of the committed measurements, because that is what the
        # history test below derives it from. Containment has to be tested on the same rounding:
        # comparing raw values made a measurement of 0.5104 fail the band whose upper edge, 0.51, is
        # what that very measurement rounds to -- a guard able to reject the number it was built on.
        rounded = round(current[kind], 2)
        assert low <= rounded <= high, (
            f"the artifact measures {current[kind]:.3f}, which rounds to {rounded} and falls "
            f"outside the documented {low}-{high}; widen the band where the range is owned"
        )
    for name, required in RANGE_DOCUMENTS.items():
        documented = _band_pairs((REPO_ROOT / name).read_text(encoding="utf-8"))
        for kind in required:
            low, high = SPEEDUP_BANDS[kind]
            assert (low, high) in documented, (
                f"{name} states no `{low}-{high}` range for the {kind} speedup ratio"
            )


def test_the_documented_speedup_ranges_match_the_committed_history() -> None:
    """Where the clone carries history, the band above must equal its actual min and max."""
    revisions = _committed_speed_ratios()
    if len(revisions) < 2:
        pytest.skip(
            "this clone carries "
            f"{len(revisions)} revision of the artifact (a clone fetched with a depth limit "
            "carries one), so no spread can be derived; see the command in docs/reproducibility.md"
        )
    python = [pair[0] for pair in revisions]
    numpy = [pair[1] for pair in revisions]
    derived = {
        "python": (round(min(python), 2), round(max(python), 2)),
        "numpy": (round(min(numpy), 2), round(max(numpy), 2)),
    }
    assert derived == SPEEDUP_BANDS, (
        f"the {len(revisions)} committed measurements span {derived}, but the documents and "
        "the guard claim SPEEDUP_BANDS"
    )


def test_the_documented_spread_percentages_are_the_committed_historys() -> None:
    """A percentage beside a band is a second claim about the sample, and it gets its own owner.

    Phase 32 gave every documented speedup *pair* a producer and registered what it left open: the
    documents also print "(32.6% spread)" next to those pairs, and nothing recomputed it -- a
    transcribed digit in four documents with no way to disagree, which is finding 55's mechanism one
    character further along the sentence.

    The population is the band's own: every committed reading of the speed artifact. The formula is
    the one the documents mean by "spread", `(max - min) / min`, to one decimal, and fixing that
    denominator was this phase's actual work rather than its code -- measured over the same 22
    readings, `(max - min) / max` gives 24.6 % and `(max - min) / mean` gives 30.3 %, and neither is
    what any document prints. A guard written without choosing the denominator would have had to
    accept either number.
    """
    revisions = _committed_speed_ratios()
    if len(revisions) < 2:
        pytest.skip(
            "this clone carries "
            f"{len(revisions)} revision of the artifact, so no spread can be recomputed; "
            "see the command in docs/reproducibility.md"
        )
    derived = {}
    for index, kind in ((0, "python"), (1, "numpy")):
        values = [pair[index] for pair in revisions]
        low, high = min(values), max(values)
        derived[kind] = round(100 * (high - low) / low, 1)
    assert derived == SPEEDUP_SPREADS, (
        f"the {len(revisions)} committed measurements spread {derived} by (max - min) / min, but "
        "the documents and the guard claim SPEEDUP_SPREADS"
    )


def test_living_documents_quote_the_spread_percentage_the_history_produces() -> None:
    """Each document that quotes a spread has to quote the one the committed readings produce.

    Presence-per-file is not enough and was the trap Phase 29 recorded: `docs/limitations.md` and
    `docs/reproducibility.md` carry both a living figure and a dated one, so a guard that only asked
    "does this file contain 32.6%?" would stay green while the living sentence drifted. The
    comparison is therefore a block -- the band's two edges and the percentage in one string --
    built from the pinned values rather than searched for as an isolated number.

    Dated records are absent on purpose: `docs/release_notes_v1.4.0.md` prints 11.9 % beside
    `7.77×`–`8.70×` and that pair of figures belongs to the revision it records, so policing it as
    living prose would rewrite history to keep a test green. The boundary this leaves is stated
    rather than papered over: a new document that quotes a spread has to be added here, and until it
    is, its percentage is read by nobody -- which is what `docs/limitations.md` #92 keeps open after
    this phase narrows it.
    """
    fields = _spread_fields()
    policed = 0
    for name, claims in SPREAD_CLAIMS.items():
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        for claim in claims:
            expected = claim.format(**fields)
            assert expected in text, (
                f"{name} no longer states {expected!r}, which is what the committed speedup "
                "history spreads"
            )
            policed += 1
    assert policed >= 4, (
        f"only {policed} spread statements are policed, so this guard has narrowed into a stub"
    )


def test_the_performance_guards_are_not_vacuous() -> None:
    """Each guard has to be able to fail, and say so: positive control first, then the shift."""
    payload = json.loads(SPEED_ARTIFACT.read_text(encoding="utf-8"))
    figures = _speed_figures(payload)
    payload["speedup_vs_pure_python"] *= 1.5
    payload["results_seconds"]["cpp"]["mean_seconds"] *= 1.5
    shifted = _speed_figures(payload)
    assert shifted["python_ratio"] != figures["python_ratio"]

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert f"{figures['python_ratio']}×" in readme
    assert f"{shifted['python_ratio']}×" not in readme

    tex = (REPO_ROOT / "paper/technical_report.tex").read_text(encoding="utf-8")
    cell = f"{figures['mean_cpp']} & {figures['std6_cpp']} & {figures['tex_pps_cpp']}"
    assert cell in tex
    assert cell.replace(figures["mean_cpp"], shifted["mean_cpp"]) not in tex

    # The caption names the run by its own timestamp, so a re-frozen artifact strands that date the
    # same way it strands the ratios. It is owned now, and the control is a date no run carries.
    dated = dict(json.loads(SPEED_ARTIFACT.read_text(encoding="utf-8")))
    dated["generated_at_utc"] = "2000-01-01T00:00:00+00:00"
    assert _speed_figures(dated)["generated_at"] not in tex, (
        "the caption's run date is not checked against the artifact"
    )

    matrix = (REPO_ROOT / "docs/validation_matrix.md").read_text(encoding="utf-8")
    # The edges are read from the pinned band rather than typed here: this test's job is to show the
    # band guard can fail, and an anchor that only exists while the band says `8.70` is a plant that
    # disarms itself the first time the band moves -- finding 49's failure mode, new numbers.
    low, high = SPEEDUP_BANDS["python"]
    low_text, high_text = f"{low:.2f}", f"{high:.2f}"
    assert (low, high) in _documented_ranges(matrix)

    # A clone fetched with a depth limit sees one measurement, so it can only derive a zero-width
    # band. That is what made this release's first runner attempt red; the pinned band must never be
    # one.
    one = float(figures["python_ratio"])
    assert (one, one) not in SPEEDUP_BANDS.values(), (
        "a single measurement cannot support the documented spread"
    )
    narrowed = matrix.replace(low_text, "7.00").replace(high_text, "8.40")
    assert narrowed != matrix, "the substitution did not land, so it proved nothing"
    assert (low, high) not in _documented_ranges(narrowed)

    # The spread guards, with the same two-sided control. The derivation is shown to move when the
    # sample moves -- a guard that would print the pinned number whatever the history said is not
    # watching anything -- and the block comparison is shown to reject a stale percentage placed in
    # the sentence that carries the current one.
    fields = _spread_fields()
    readings = _committed_speed_ratios()
    if len(readings) > 1:
        values = [pair[0] for pair in readings]
        pinned = round(100 * (max(values) - min(values)) / min(values), 1)
        widened = values + [max(values) * 1.2]
        shifted = round(100 * (max(widened) - min(widened)) / min(widened), 1)
        assert pinned != shifted, (
            "one more reading does not change the computed spread, so the derivation is not reading"
        )
        assert f"{pinned:.1f}" == fields["py_spread"], (
            "the guard's own arithmetic disagrees with the pinned spread it polices"
        )
    block = SPREAD_CLAIMS["docs/reproducibility.md"][0].format(**fields)
    doc = (REPO_ROOT / "docs/reproducibility.md").read_text(encoding="utf-8")
    assert block in doc
    stale = block.replace(fields["py_spread"], "11.9")
    assert stale not in doc, "a superseded percentage already sits in the living sentence"
    edited = doc.replace(block, stale)
    assert edited != doc, "the substitution did not land, so it proved nothing"
    assert block not in edited, "the sentence still carries the policed block after its edit"


CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_the_ci_lane_that_runs_the_guards_fetches_what_they_read() -> None:
    """A guard that reads commits is a claim about the checkout, and nothing checked the checkout.

    Phase 33 gave the pytest lane its history and tags, which turned three skipping guards into
    three checked ones. That made the workflow load-bearing in a new way: with the fetch settings
    removed the guards do not fail, they *skip with a named reason*, and a green job is then the
    colour of an absent test. The repository has met the other direction of the same divorce --
    `docs/integrity_audit.md` finding 35 is a guard that derived a band from `git log`, saw one
    revision on the depth-1 runner and reddened run `36550420085` -- but nothing tied a guard's
    input set to the step that provides it.

    So this reads the workflow as the structure it is. It is the first guard to: the only other
    thing CI is compared against is one phrase about suite members, matched by regex. YAML folds,
    comments and block sequences are exactly where a grep loses a step, and a check that silently
    examines fewer jobs than the file contains would report this guard green while the lane it cares
    about went unconfigured.
    """
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    lanes = []
    for name, job in sorted((workflow.get("jobs") or {}).items()):
        steps = job.get("steps") or []
        runs = [index for index, step in enumerate(steps) if "pytest" in str(step.get("run", ""))]
        if runs:
            lanes.append((name, steps, min(runs)))
    assert lanes, "no CI job runs pytest, so this guard would certify an empty set"

    for name, steps, first_run in lanes:
        checks_out = [
            step
            for step in steps[:first_run]
            if str(step.get("uses", "")).startswith("actions/checkout@")
        ]
        assert checks_out, (
            f"the {name} job runs the guards before any checkout, so they can read no "
            "history at all"
        )
        settings = checks_out[-1].get("with") or {}
        depth = str(settings.get("fetch-depth", "1"))
        assert depth == "0", (
            f"the {name} job fetches depth {depth!r}, which silently vacates every guard that "
            "reads commits: the ones needing the artifact's history and the ones needing its tags"
        )
        assert settings.get("fetch-tags") is True, (
            f"the {name} job does not fetch tags, so the release-date and release-tag guards skip "
            "there and the lane still passes"
        )
