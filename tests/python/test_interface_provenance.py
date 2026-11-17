"""The agent-facing surface is only a bundle of value plus provenance, so the bundle is tested.

The guard behind the controlled plant is the first functional test: it reads the committed manifest
and requires every registered artifact that carries a published headline to resolve with its four
provenance elements intact. A plant that erases one recorded command makes that artifact's value
unresolvable, so the guard reddens — the concrete claim that a number cannot escape its provenance.

The rest are the reasons that guard means what it says. Each missing element is refused by name and
the refusal carries no bare value; the task list is the registry's own commands, not a retyped set;
the source carries no numeric figure; and neither path opens a socket. The guards use temporary
copies of the evidence so a negative control never edits the frozen tree.
"""

from __future__ import annotations

import ast
import json
import shutil
import socket
from pathlib import Path

import pytest
from quantrisk.experiments.metadata import REPO_ROOT
from quantrisk.experiments.registry import TASKS
from quantrisk.interface import provenance

PROVENANCE_SOURCE = REPO_ROOT / "python" / "quantrisk" / "interface" / "provenance.py"

# A registered task whose artifact carries a headline, used as the value-bearing sample.
SAMPLE_ARTIFACT = "experiments/sixth_book_crossing_map/results/sixth_book_crossing_map.json"


def _numeric_literals(source: str) -> list[float]:
    found: list[float] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if isinstance(node.value, bool):
                continue
            found.append(node.value)
    return found


def _headline_artifacts() -> list[str]:
    """Registered artifacts holding a headline, computed so the corpus cannot be empty."""
    found: list[str] = []
    for task in TASKS:
        path = REPO_ROOT / task.artifact
        if path.suffix != ".json" or not path.is_file():
            continue
        document = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(document, dict) and isinstance(document.get("headline"), dict):
            found.append(task.artifact)
    return found


def _temp_root(destination: Path, *, blank: str | None = None, drop_revision: bool = False) -> Path:
    """A copy of the evidence, with one provenance field optionally removed."""
    (destination / "evidence").mkdir(parents=True, exist_ok=True)
    manifest = json.loads((REPO_ROOT / provenance.MANIFEST).read_text(encoding="utf-8"))
    if blank is not None:
        for entry in manifest["artifacts"]:
            if entry["path"] == blank:
                entry["generated_by_command"] = ""
    if drop_revision:
        manifest["repository"]["git_commit"] = ""
    (destination / provenance.MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for artifact in _headline_artifacts():
        target = destination / artifact
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / artifact, target)
    return destination


def test_no_value_is_returned_without_its_command_digest_and_revision() -> None:
    """Guard behind plant `provenance-erases-a-recorded-command`.

    Every published value the registry names must resolve with its command, digest, revision and
    value together. The reading is the committed manifest, not a copy built in the test: a plant
    that blanks one recorded command removes that artifact's provenance, and this guard objects.
    """
    artifacts = _headline_artifacts()
    assert artifacts, "no registered artifact carries a headline, so this guard certifies nothing"
    assert SAMPLE_ARTIFACT in artifacts, "the plant's sample is no longer a value-bearing artifact"
    for artifact in artifacts:
        record = provenance.resolve(artifact)
        assert record["value"], f"{artifact} resolved with no value"
        for field in ("command", "sha256", "revision"):
            assert record[field].strip(), f"{artifact} resolved with no {field}"


def test_a_missing_command_is_refused_by_name(tmp_path: Path) -> None:
    """A value whose command was erased is refused, and the refusal does not leak the value."""
    root = _temp_root(tmp_path / "tree", blank=SAMPLE_ARTIFACT)
    with pytest.raises(provenance.ProvenanceRefused) as refusal:
        provenance.resolve(SAMPLE_ARTIFACT, root)

    message = str(refusal.value)
    assert "generated_by_command" in message
    assert SAMPLE_ARTIFACT in message
    headline = json.loads((REPO_ROOT / SAMPLE_ARTIFACT).read_text(encoding="utf-8"))["headline"]
    assert json.dumps(headline, sort_keys=True) not in message, "the refusal printed a bare value"


def test_a_missing_revision_is_refused_by_name(tmp_path: Path) -> None:
    """Without the tree revision the record cannot say which tree produced the value."""
    root = _temp_root(tmp_path / "tree", drop_revision=True)
    with pytest.raises(provenance.ProvenanceRefused) as refusal:
        provenance.resolve(SAMPLE_ARTIFACT, root)
    assert "revision" in str(refusal.value)


def test_an_absent_artifact_is_refused_by_name(tmp_path: Path) -> None:
    """An artifact with no manifest entry is named as the gap, never answered with a value."""
    root = _temp_root(tmp_path / "tree")
    missing = "experiments/not_in_the_manifest.json"
    with pytest.raises(provenance.ProvenanceRefused) as refusal:
        provenance.resolve(missing, root)
    assert missing in str(refusal.value)


def test_list_tasks_matches_the_registry_commands() -> None:
    """The enumerated commands are derived from module paths, not retyped into this surface."""
    listed = provenance.list_tasks()
    assert {row["task_id"] for row in listed} == {task.task_id for task in TASKS}
    for row in listed:
        assert row["command"].startswith("uv run python -m ")
        assert row["artifact"]


def test_the_provenance_module_carries_no_numeric_literal() -> None:
    """No figure is carried in the module, so none in a response can have come from a literal."""
    assert Path(provenance.__file__).resolve() == PROVENANCE_SOURCE.resolve()
    source = PROVENANCE_SOURCE.read_text(encoding="utf-8")
    assert _numeric_literals("answer = 19\n") == [19], "the scan would certify any file"
    assert _numeric_literals(source) == []


def test_the_surface_opens_no_socket(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Offline is a property of the surface, not a wish: a socket request fails the test."""

    def refuse(*arguments: object, **keywords: object) -> None:
        raise AssertionError("the provenance surface asked for a socket")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)

    root = _temp_root(tmp_path / "tree")
    provenance.list_tasks()
    assert provenance.resolve(SAMPLE_ARTIFACT, root)["value"]


def test_a_refusal_exits_nonzero_and_names_the_gap(tmp_path: Path) -> None:
    """The command form prints a named refusal and does not exit as if it had answered."""
    root = _temp_root(tmp_path / "tree", blank=SAMPLE_ARTIFACT)
    with pytest.raises(SystemExit) as exit_info:
        provenance.main(["--resolve", SAMPLE_ARTIFACT, "--root", str(root)])
    assert exit_info.value.code
    assert "generated_by_command" in str(exit_info.value.code)
