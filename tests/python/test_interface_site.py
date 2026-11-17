"""The generated site is only worth its provenance, so the provenance is what gets tested.

Eight properties, each one chosen because its opposite is the failure a static site makes easy.

The source scan is the strongest form of "generated, never retyped" available without running
the build: the generator file may contain no numeric literal at all, which is a stricter claim
than the law's "no evidence-shaped literal" and therefore needs no evidence set to interpret.
It is checked with a negative control in the same test, because a scan that cannot fail would
pass over an empty file.

The other four are about the build: a page quotes the manifest's digest and command, two builds
of one tree are byte-identical, a regenerated artifact changes the page that renders it, and an
artifact that disagrees with the manifest — missing from it, or changed under it — stops the
build instead of producing a page that looks checkable and is not. Three more bound the edges:
an absent artifact is listed rather than described, no build opens a socket, and the source scan
has a negative control.
"""

from __future__ import annotations

import ast
import hashlib
import json
import shutil
import socket
from pathlib import Path

import pytest
from quantrisk.experiments.metadata import REPO_ROOT
from quantrisk.experiments.registry import TASKS, TASKS_BY_ID
from quantrisk.interface import site

GENERATOR = REPO_ROOT / "python" / "quantrisk" / "interface" / "site.py"

# A task whose artifact records a claim and a headline, so a page has figures to move.
RENDERED_TASK = "fourth_order_crossing_map"

# Chosen so a page cannot contain it by coincidence: primes, no zero, seven digits.
MUTATED_FIGURE = 999983


def _numeric_literals(source: str) -> list[float]:
    """Every int or float literal in a source string, in source order. Booleans are not numbers."""
    found: list[float] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if isinstance(node.value, bool):
                continue
            found.append(node.value)
    return found


def _temp_root(
    destination: Path, *, omit: str | None = None, drop_entry: str | None = None
) -> Path:
    """A copy of the evidence a build needs: the manifest, and each task's artifact."""
    (destination / "evidence").mkdir(parents=True, exist_ok=True)
    manifest = json.loads((REPO_ROOT / site.MANIFEST).read_text(encoding="utf-8"))
    if drop_entry is not None:
        manifest["artifacts"] = [
            entry for entry in manifest["artifacts"] if entry["path"] != drop_entry
        ]
    (destination / site.MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for task in TASKS:
        if task.task_id == omit:
            continue
        target = destination / task.artifact
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / task.artifact, target)
    return destination


def _snapshot(directory: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(directory.glob("*.html"))}


def test_the_generator_source_contains_no_numeric_literal() -> None:
    """No figure is carried in the module, so none on a page can have come from a literal."""
    assert Path(site.__file__).resolve() == GENERATOR.resolve(), (
        f"the imported generator is {site.__file__}, not {GENERATOR}: the scan below would certify "
        f"an installed copy while a plant edited the tracked one"
    )
    source = GENERATOR.read_text(encoding="utf-8")

    assert frozenset() == site.LAYOUT_NUMBERS, (
        "a layout constant was added to the generator; that is a design change, and this test is "
        "where it has to be argued for rather than absorbed"
    )
    assert _numeric_literals("answer = 19\n") == [19], (
        "the scan missed a literal in a string known to contain one, so it would certify any file"
    )
    assert _numeric_literals(source) == []


def test_every_interface_module_carries_no_numeric_literal() -> None:
    """The zero-literal law covers the whole package, so a new module cannot hide a figure."""
    package = GENERATOR.parent
    modules = sorted(package.glob("*.py"))
    assert "drift.py" in {module.name for module in modules}, (
        "the drift gate module is missing from the interface package"
    )
    for module in modules:
        assert _numeric_literals(module.read_text(encoding="utf-8")) == [], module.name


def test_every_page_quotes_the_provenance_the_manifest_records(tmp_path: Path) -> None:
    """A page is checkable or it is not published: path, digest and recorded command, per page."""
    root = _temp_root(tmp_path / "tree")
    out = tmp_path / "site"
    site.generate(out, root)

    entries = {
        entry["path"]: entry
        for entry in json.loads((root / site.MANIFEST).read_text(encoding="utf-8"))["artifacts"]
    }
    for task in TASKS:
        page = (out / f"{task.task_id}.html").read_text(encoding="utf-8")
        entry = entries[task.artifact]
        assert entry["generated_by_command"] in page, task.task_id
        assert entry["sha256"] in page, task.task_id
        assert task.artifact in page, task.task_id


def test_two_builds_of_one_tree_are_byte_identical(tmp_path: Path) -> None:
    """Nothing on a page comes from the clock: a differing rebuild is a difference in evidence."""
    root = _temp_root(tmp_path / "tree")
    first = tmp_path / "first"
    second = tmp_path / "second"
    site.generate(first, root)
    site.generate(second, root)

    assert _snapshot(first) == _snapshot(second)


def test_a_figure_moves_when_its_artifact_is_regenerated(tmp_path: Path) -> None:
    """The page reads the artifact during the build; it does not remember what the artifact said."""
    task = TASKS_BY_ID[RENDERED_TASK]
    root = _temp_root(tmp_path / "tree")
    out = tmp_path / "site"
    site.generate(out, root)
    before = (out / f"{task.task_id}.html").read_text(encoding="utf-8")
    assert str(MUTATED_FIGURE) not in before

    artifact = root / task.artifact
    document = json.loads(artifact.read_text(encoding="utf-8"))
    document["headline"]["columns_swept"] = MUTATED_FIGURE
    artifact.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest_path = root / site.MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["artifacts"]:
        if entry["path"] == task.artifact:
            entry["sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    site.generate(out, root)
    after = (out / f"{task.task_id}.html").read_text(encoding="utf-8")
    assert str(MUTATED_FIGURE) in after


def test_an_artifact_outside_the_manifest_stops_the_build(tmp_path: Path) -> None:
    """A page with no recorded command is a number nobody can run, so the build names the gap."""
    task = TASKS_BY_ID[RENDERED_TASK]
    root = _temp_root(tmp_path / "tree", drop_entry=task.artifact)
    out = tmp_path / "site"

    with pytest.raises(site.SiteRefused) as refusal:
        site.generate(out, root)

    assert task.artifact in str(refusal.value)
    assert not (out / f"{task.task_id}.html").exists()


def test_an_artifact_whose_bytes_moved_stops_the_build(tmp_path: Path) -> None:
    """The digest a page prints is recomputed, so a stale page cannot claim a digest it lacks."""
    task = TASKS_BY_ID[RENDERED_TASK]
    root = _temp_root(tmp_path / "tree")
    artifact = root / task.artifact
    artifact.write_text(artifact.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    out = tmp_path / "site"

    with pytest.raises(site.SiteRefused) as refusal:
        site.generate(out, root)

    assert "hashes to" in str(refusal.value)
    assert not (out / f"{task.task_id}.html").exists()


def test_a_study_without_an_artifact_is_listed_rather_than_described(tmp_path: Path) -> None:
    """An absent artifact gets a row that says so, never a page with an empty provenance block."""
    omitted = TASKS_BY_ID[RENDERED_TASK]
    root = _temp_root(tmp_path / "tree", omit=omitted.task_id)
    out = tmp_path / "site"
    site.generate(out, root)

    assert not (out / f"{omitted.task_id}.html").exists()
    index = (out / "index.html").read_text(encoding="utf-8")
    assert "artifact not present in this tree" in index
    assert omitted.artifact in index


def test_the_build_opens_no_socket(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Offline is a property of the build, not a wish about it: a socket request fails the test."""

    def refuse(*arguments: object, **keywords: object) -> None:
        raise AssertionError(
            "the generator asked for a socket during a build; a page that needs the network is a "
            "page whose figures can differ from the artifact it claims"
        )

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)

    root = _temp_root(tmp_path / "tree")
    out = tmp_path / "site"
    site.generate(out, root)

    assert (out / "index.html").is_file()
