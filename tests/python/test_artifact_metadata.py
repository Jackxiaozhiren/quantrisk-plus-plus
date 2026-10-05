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
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import quantrisk
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
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    collected = re.search(r"^(\d+) tests? collected", completed.stdout, flags=re.M)
    assert collected, f"could not read a test count out of pytest: {completed.stdout[-500:]}"
    total = int(collected.group(1))

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
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
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
        "docs/interview_defense.md": r"has all (\d+)\s*\n?numbered entries",
        "paper/technical_report.tex": r"(?:contains|holds) (\d+) numbered entries",
        # A release note is a living document about the current file, not a record of a past
        # revision: it quoted the count while the count moved. #76 was found by exactly that lag.
        "docs/release_notes_v1.3.0.md": r"all \*\*(\d+) entries\*\*",
        # ... and the same holds for the note that records #77's third case.
        "docs/release_notes_v1.4.0.md": r"carries (\d+) numbered entries",
    }
    for name, pattern in claims.items():
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        found = re.findall(pattern, text)
        assert found, f"{name} no longer states the limitation count in the expected form"
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
        "docs/interview_defense.md": r"(\d+) C\+\+ tests under CTest",
        "docs/reproducibility.md": r"# (\d+) C\+\+ tests",
    }
    for name, pattern in claims.items():
        found = re.findall(pattern, (REPO_ROOT / name).read_text(encoding="utf-8"))
        assert found, f"{name} no longer states the C++ test count"
        assert all(int(value) == total for value in found), (
            f"{name} says {found}, CTest lists {total}"
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
        "{python_ratio}×",
        "{numpy_ratio}×",
        "{mega_cpp}M vs {mega_python}M paths/s",
    ),
    "docs/interview_defense.md": (
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
        "{mean_cpp} & {std6_cpp} & {tex_pps_cpp} & {estimate_cpp} & {tex_z_cpp}",
        "{mean_python} & {std6_python} & {tex_pps_python} & {estimate_python} & {tex_z_python}",
        "{mean_numpy} & {std6_numpy} & {tex_pps_numpy} & {estimate_numpy} & {tex_z_numpy}",
    ),
}

RANGE_DOCUMENTS = (
    "README.md",
    "docs/validation_matrix.md",
    "docs/interview_defense.md",
    "docs/reproducibility.md",
    "docs/release_notes_v1.5.0.md",
    "docs/release_notes_v1.7.0.md",
)

# The spread of the speed benchmark's two ratios over every committed measurement of the artifact —
# fourteen at the 1.5.0 freeze, recomputable with the command printed in docs/reproducibility.md.
# Both edges are the *rounded* min and max, which is what the history guard derives, so a raw value
# of 0.5104 belongs to the documented band edge 0.51 rather than falling outside it.
SPEEDUP_BANDS = {"python": (7.77, 8.7), "numpy": (0.42, 0.51)}


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


def test_the_documented_speedup_ranges_contain_the_current_measurement() -> None:
    """The ranges are claims about a sample, and the current artifact has to be inside them.

    `SPEEDUP_BANDS` is written down rather than derived because CI checks the repository out at
    depth 1: a guard that recomputes the band from history sees one measurement there and demands
    that the documents quote `0.45-0.45`, which is how this release's first runner attempt went
    red. The history is still checked, in the test below, wherever a clone carries it.
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
    for name in RANGE_DOCUMENTS:
        documented = _documented_ranges((REPO_ROOT / name).read_text(encoding="utf-8"))
        for low, high in SPEEDUP_BANDS.values():
            assert (low, high) in documented, (
                f"{name} states no `{low}-{high}` range for a speedup ratio"
            )


def test_the_documented_speedup_ranges_match_the_committed_history() -> None:
    """Where the clone carries history, the band above must equal its actual min and max."""
    revisions = _committed_speed_ratios()
    if len(revisions) < 2:
        pytest.skip(
            "this clone carries "
            f"{len(revisions)} revision of the artifact (CI uses actions/checkout at depth 1), "
            "so no spread can be derived; see the command in docs/reproducibility.md"
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

    matrix = (REPO_ROOT / "docs/validation_matrix.md").read_text(encoding="utf-8")
    assert (7.77, 8.7) in _documented_ranges(matrix)

    # A depth-1 clone sees one measurement, so it can only derive a zero-width band. That is what
    # made this release's first runner attempt red; the pinned band must never be one.
    one = float(figures["python_ratio"])
    assert (one, one) not in SPEEDUP_BANDS.values(), (
        "a single measurement cannot support the documented spread"
    )
    narrowed = matrix.replace("7.77", "8.00").replace("8.70", "8.40")
    assert narrowed != matrix, "the substitution did not land, so it proved nothing"
    assert (7.77, 8.7) not in _documented_ranges(narrowed)
