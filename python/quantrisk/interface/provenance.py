"""A read-only provenance surface: a number is never handed back alone.

`site.py` publishes numbers onto a page beside the command and digest that produced them; `drift.py`
keeps that page honest. Both address a reader looking at HTML. This module addresses the other
consumer — an agent that wants the value directly — and closes the gap a JSON response would open:
a bare number, detached from how it was made, is the exact failure this repository exists to make
visible. So the two are returned in one record, or nothing is returned at all.

The record carries four things together: the value read from the artifact, the command that
produced it, the revision of the tree that froze it, and the digest the manifest recorded. If any
one cannot be resolved, `ProvenanceRefused` names the specific gap and no value is emitted. This is
the acceptance test in `INTERFACE_ROADMAP.md` §7 for I3, stated as code: a query that cannot resolve
provenance returns a refusal naming the gap, never a bare number.

Two invocations, both module-path so the CLI's four subcommands stay four:

    uv run python -m quantrisk.interface.provenance --list
    uv run python -m quantrisk.interface.provenance --resolve <artifact path> [--json]

`--list` enumerates registered tasks with the canonical command derived from each module path.
`--resolve` takes the artifact path a manifest entry names and returns value plus provenance. The
surface reads; it never writes, executes a study, opens a socket or fetches anything. Like the other
two interface modules it carries no numeric literal, checked by its own test module rather than by
widening `site.py`'s guard.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ..checkout import checkout_root
from ..experiments.registry import TASKS

MANIFEST = Path("evidence") / "manifest.json"

SCHEMA = "quantrisk-provenance/1"


class ProvenanceRefused(RuntimeError):
    """A value was asked for but one element of its provenance could not be resolved."""


def _manifest_document(root: Path) -> dict[str, Any]:
    path = root / MANIFEST
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ProvenanceRefused(f"cannot read {MANIFEST.as_posix()} at {root}: {error}") from error
    if not isinstance(document.get("artifacts"), list):
        raise ProvenanceRefused(f"{MANIFEST.as_posix()} lists no artifacts array")
    return document


def _entry_for(artifact: str, document: dict[str, Any]) -> dict[str, Any]:
    for entry in document["artifacts"]:
        if isinstance(entry, dict) and entry.get("path") == artifact:
            return entry
    raise ProvenanceRefused(
        f"{artifact} is absent from {MANIFEST.as_posix()}, so no command or digest can be "
        f"attached to its value; refusing to return a bare number"
    )


def _field(entry: dict[str, Any], name: str, artifact: str) -> str:
    value = entry.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ProvenanceRefused(
            f"{artifact} has no {name} in {MANIFEST.as_posix()}, so its value cannot be "
            f"returned with the provenance that makes it checkable; refusing"
        )
    return value


def resolve(artifact: str, root: Path | None = None) -> dict[str, Any]:
    """Return the value and its full provenance together, or refuse by naming the gap.

    The four fields are read from the committed manifest and the artifact it names; none is typed
    here. The revision is the tree revision the manifest records, not the current checkout, because
    a provenance claim says which tree produced the number, not which tree is asking about it.
    """
    base = checkout_root() if root is None else Path(root)
    document = _manifest_document(base)
    entry = _entry_for(artifact, document)

    command = _field(entry, "generated_by_command", artifact)
    digest = _field(entry, "sha256", artifact)
    revision = str(document.get("repository", {}).get("git_commit") or "")
    if not revision.strip():
        raise ProvenanceRefused(
            f"{MANIFEST.as_posix()} records no revision, so {artifact} cannot say which tree "
            f"produced its value; refusing"
        )

    source = base / artifact
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ProvenanceRefused(f"cannot read the artifact {artifact}: {error}") from error
    if not isinstance(payload, dict) or "headline" not in payload:
        raise ProvenanceRefused(
            f"{artifact} records no headline, so there is no published value to return with "
            f"its provenance"
        )

    return {
        "schema": SCHEMA,
        "artifact": artifact,
        "value": payload["headline"],
        "command": command,
        "revision": revision,
        "sha256": digest,
    }


def list_tasks() -> list[dict[str, str]]:
    """Every registered task with the canonical command derived from its module path."""
    return [
        {
            "task_id": task.task_id,
            "artifact": task.artifact,
            "command": task.invocation,
        }
        for task in TASKS
    ]


def _render(record: dict[str, Any], as_json: bool) -> str:
    if as_json:
        return json.dumps(record, ensure_ascii=False, sort_keys=True)
    lines = [
        f"artifact: {record['artifact']}",
        f"value: {json.dumps(record['value'], ensure_ascii=False, sort_keys=True)}",
        f"command: {record['command']}",
        f"revision: {record['revision']}",
        f"sha256: {record['sha256']}",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> None:
    """List tasks, or resolve one artifact; a refusal names its gap and exits non-zero."""
    parser = argparse.ArgumentParser(description="Read a published value with its provenance.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true", help="list tasks and canonical commands")
    mode.add_argument("--resolve", metavar="ARTIFACT", help="artifact path to resolve")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--root", help="checkout root, defaulting to the one containing the cwd")
    arguments = parser.parse_args(argv)

    if arguments.list:
        print(json.dumps(list_tasks(), ensure_ascii=False, sort_keys=True))
        return

    base = checkout_root() if arguments.root is None else Path(arguments.root)
    try:
        record = resolve(arguments.resolve, base)
    except ProvenanceRefused as refusal:
        message = f"REFUSED: {refusal}"
        print(message)
        raise SystemExit(message) from refusal
    print(_render(record, arguments.json))


if __name__ == "__main__":
    main()
