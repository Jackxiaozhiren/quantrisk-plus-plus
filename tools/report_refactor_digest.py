#!/usr/bin/env python3
"""L1: the content-digest report across one re-run of the evidence chain.

    uv run python -m tools.report_refactor_digest [--from REV]

D5 re-runs every published task exactly once, and L1 decides whether that re-run was a refactor or a
result change. "Did the bytes move" is the wrong question -- a timestamp moved, and the freeze
commit is recorded in them -- so the comparison uses the same view the manifest's `content_sha256`
is taken from: the artifact with `VOLATILE_KEYS` stripped. For each entry this reads the artifact as
it was at `--from` (default `HEAD`, the pre-run state while the re-run is still uncommitted) and as
it is in the working tree, and reports every leaf that differs, classified against the categories
declared in `tools/refactor_ceilings.json`.

The exit code is the answer that matters: 0 when nothing moved outside a declared category, 1 when
something moved that no declaration covers. A moved number is a mathematics finding and the refactor
stops until it is adjudicated (REFACTOR_PROMPT.md §14), so an undeclared leaf is printed with both
of its values rather than counted. Files with no canonical form -- figures -- are reported as byte
movement and declared separately, because a redrawn PNG is not a content digest that moved.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from quantrisk.experiments.evidence import _strip, content_digest
from quantrisk.experiments.metadata import REPO_ROOT

CEILINGS = REPO_ROOT / "tools" / "refactor_ceilings.json"
MANIFEST = "evidence/manifest.json"


def _git(revision: str, path: str) -> bytes:
    """One tracked file as `revision` holds it, with the failure named rather than swallowed."""
    completed = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(
            f"{revision}:{path} is not readable from git: {completed.stderr.decode()[:200]}"
        )
    return completed.stdout


def _leaves(node: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(node, dict):
        found: dict[str, Any] = {}
        for key, value in node.items():
            found.update(_leaves(value, f"{prefix}.{key}" if prefix else key))
        return found
    if isinstance(node, list):
        found = {}
        for index, item in enumerate(node):
            found.update(_leaves(item, f"{prefix}[{index}]"))
        return found
    return {prefix: node}


def _materialise(payload: bytes, path: str) -> Path:
    """The old bytes at a real path, so `canonical_text` runs in its production shape."""
    handle, name = tempfile.mkstemp(suffix=Path(path).suffix)
    with open(handle, "wb") as written:
        written.write(payload)
    return Path(name)


def _declared(
    declarations: list[dict[str, Any]], leaf: str, category: str
) -> dict[str, Any] | None:
    for declaration in declarations:
        categories = declaration.get("categories") or []
        if categories and category not in categories:
            continue
        if re.search(declaration["leaf_pattern"], leaf):
            return declaration
    return None


def compare(revision: str) -> tuple[int, list[str]]:
    declarations = json.loads(CEILINGS.read_text(encoding="utf-8")).get("declared_movements", [])
    old_manifest = json.loads(_git(revision, MANIFEST))
    lines: list[str] = []
    undeclared: list[str] = []
    moved = identical = 0
    byte_moved = 0
    temp_files: list[Path] = []
    try:
        for entry in old_manifest["artifacts"]:
            path, category = entry["path"], entry.get("category", "?")
            live = REPO_ROOT / path
            if not live.is_file():
                undeclared.append(f"{path}: present in the manifest, missing from the tree")
                continue
            old_bytes = _git(revision, path)
            snapshot = _materialise(old_bytes, path)
            temp_files.append(snapshot)
            before = content_digest(snapshot)
            after = content_digest(live)
            if before is None or after is None:
                if old_bytes == live.read_bytes():
                    continue
                cover = _declared(declarations, "<bytes>", category)
                byte_moved += 1
                if cover is None:
                    # No canonical form and the bytes differ: for a figure that is data movement,
                    # and it is adjudicated rather than absorbed.
                    undeclared.append(f"{path} :: bytes differ, no canonical form")
                    lines.append(f"UNDECLARED {category:24s} {path} :: <bytes>")
                else:
                    lines.append(f"declared   {category:24s} {path} :: <bytes> [{cover['id']}]")
                continue
            if before == after:
                identical += 1
                continue
            moved += 1
            if Path(path).suffix != ".json":
                # A CSV has columns, not leaves, and a Markdown aggregate has neither. The whole
                # file is one leaf named `<file>`, so a category-level declaration can cover it --
                # which is only safe because the numbers an aggregate quotes are compared leaf by
                # leaf in the member artifacts above it.
                cover = _declared(declarations, "<file>", category)
                if cover is None:
                    undeclared.append(f"{path} :: whole-file content moved")
                    lines.append(f"UNDECLARED {category:24s} {path} :: <file>")
                else:
                    lines.append(f"declared   {category:24s} {path} :: <file> [{cover['id']}]")
                continue
            old_leaves = _leaves(_strip(json.loads(old_bytes.decode("utf-8"))))
            new_leaves = _leaves(_strip(json.loads(live.read_text(encoding="utf-8"))))
            for leaf in sorted(set(old_leaves) | set(new_leaves)):
                was, now = old_leaves.get(leaf, "<absent>"), new_leaves.get(leaf, "<absent>")
                if was == now:
                    continue
                cover = _declared(declarations, leaf, category)
                if cover is None:
                    undeclared.append(f"{path} :: {leaf}")
                    lines.append(
                        f"UNDECLARED {category:24s} {path} :: {leaf} "
                        f"= {str(was)[:48]!r} -> {str(now)[:48]!r}"
                    )
                else:
                    lines.append(f"declared   {category:24s} {path} :: {leaf} [{cover['id']}]")
    finally:
        for temporary in temp_files:
            temporary.unlink(missing_ok=True)
    header = (
        f"L1 report {revision} -> working tree: {len(old_manifest['artifacts'])} manifest entries, "
        f"{identical} unchanged, {moved} with content movement, {byte_moved} files with no "
        f"canonical form whose bytes differ, {len(undeclared)} undeclared"
    )
    return (1 if undeclared else 0), [header, *lines]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from", dest="revision", default="HEAD", help="the pre-run revision (default: HEAD)"
    )
    code, lines = compare(parser.parse_args(argv).revision)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
