"""The drift gate: a frozen reading of the generated site, checked against a rebuild.

`site.py` proves a page is generated from the artifact beside it. It does not prove that two builds
agree, or that an artifact changed without the published page changing with it. Those are different
claims and need a second file: this one freezes what each page hashed to at a named revision, then
rebuilds into a temporary directory and compares. A figure can move in an artifact and in the
manifest's digests — so `verify_evidence_manifest` stays green — while the page a reader would see
still carries the old value. That is the drift this gate exists to catch, and it is the page-level
reading H3 asks for rather than a second opinion on the artifact bytes.

Two commands, both module-path invocations so the CLI's four subcommands stay four:

    uv run python -m quantrisk.interface.drift --lock build/site.lock --freeze --out <dir>
    uv run python -m quantrisk.interface.drift --lock build/site.lock --check --out <dir>

Freeze writes the lock from a build of the current tree. Check rebuilds and compares, printing one
line per page and exiting non-zero if any page's digest, any artifact's digest, or the set of pages
has moved. Both digests are read from the lock or recomputed from files; no figure is typed here.
This module contains no numeric literal, as `site.py` does; each is checked by its own source
guard, so adding one is a visible act rather than a quiet one.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ..checkout import checkout_root
from ..experiments.metadata import sha256_file
from ..experiments.registry import TASKS_BY_ID
from . import site

LOCK_SCHEMA = "quantrisk-site-lock/1"

LAYOUT_NUMBERS: frozenset[int] = frozenset()
"""The allowance is empty, as in `site.py`: this module carries no numeric literal at all.

JSON is written compactly and a failing check exits with a message rather than a typed status, so
neither formatting nor the exit path needs a figure. The guard in the drift test module reads this
source, so widening the allowance is a visible act.
"""


class DriftRefused(RuntimeError):
    """The lock cannot be read as a baseline, so no check can be trusted."""


def _read_lock(lock: Path) -> dict[str, Any]:
    try:
        document = json.loads(lock.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise DriftRefused(f"cannot read the site lock at {lock}: {error}") from error
    if document.get("schema") != LOCK_SCHEMA:
        raise DriftRefused(
            f"{lock} declares schema {document.get('schema')!r}, expected {LOCK_SCHEMA!r}"
        )
    pages = document.get("pages")
    if not isinstance(pages, dict) or not pages:
        raise DriftRefused(f"{lock} holds no frozen pages; refusing an empty baseline")
    return document


def _fingerprint(pages: list[Path], root: Path) -> dict[str, dict[str, str]]:
    """Page digest beside the digest of the artifact that produced it."""
    frozen: dict[str, dict[str, str]] = {}
    for page in pages:
        task = TASKS_BY_ID.get(page.stem)
        source_digest = sha256_file(root / task.artifact) if task is not None else ""
        frozen[page.name] = {
            "page_sha256": sha256_file(page),
            "artifact": task.artifact if task is not None else "",
            "artifact_sha256": source_digest,
        }
    return frozen


def freeze(out: Path, lock: Path, root: Path | None = None) -> dict[str, dict[str, str]]:
    """Build the current tree and write its page fingerprints as the new baseline."""
    base = checkout_root() if root is None else Path(root)
    pages = site.generate(out, base)
    document = {
        "schema": LOCK_SCHEMA,
        "source": site.__name__,
        "pages": _fingerprint(sorted(pages, key=lambda path: path.name), base),
    }
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps(document, sort_keys=True) + "\n", encoding="utf-8")
    return document["pages"]


def check(out: Path, lock: Path, root: Path | None = None) -> list[str]:
    """Rebuild into `out` and return one problem line per drifted page, empty when clean."""
    base = checkout_root() if root is None else Path(root)
    frozen = _read_lock(lock)["pages"]
    pages = site.generate(out, base)
    current = _fingerprint(sorted(pages, key=lambda path: path.name), base)

    problems: list[str] = []
    for name in sorted(set(frozen) | set(current)):
        before = frozen.get(name)
        after = current.get(name)
        if before is None:
            problems.append(f"{name}: page appeared after the lock was frozen")
            continue
        if after is None:
            problems.append(f"{name}: locked page is absent from a rebuild")
            continue
        if before["page_sha256"] != after["page_sha256"]:
            problems.append(
                f"{name}: page hashed {before['page_sha256']} at freeze, now {after['page_sha256']}"
            )
        if before["artifact_sha256"] != after["artifact_sha256"]:
            problems.append(
                f"{name}: source {after['artifact']} hashed {before['artifact_sha256']} "
                f"at freeze, now {after['artifact_sha256']}"
            )
    return problems


def main(argv: Sequence[str] | None = None) -> None:
    """Freeze a baseline or check against one; a check with drift exits non-zero."""
    parser = argparse.ArgumentParser(description="Check the generated site against a frozen lock.")
    parser.add_argument("--lock", required=True, help="path to the site lock")
    parser.add_argument(
        "--out", required=True, help="directory the comparison build is written into"
    )
    parser.add_argument("--root", help="checkout root, defaulting to the one containing the cwd")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze", action="store_true", help="write the lock from the current tree")
    mode.add_argument("--check", action="store_true", help="rebuild and compare against the lock")
    arguments = parser.parse_args(argv)
    base = checkout_root() if arguments.root is None else Path(arguments.root)
    lock = Path(arguments.lock)

    if arguments.freeze:
        pages = freeze(Path(arguments.out), lock, base)
        print(f"froze {len(pages)} page(s) to {lock}")
        return

    problems = check(Path(arguments.out), lock, base)
    if problems:
        for problem in problems:
            print(f"DRIFT {problem}")
        message = f"FAIL: {len(problems)} drift(s) between the rebuilt site and {lock}"
        print(message)
        raise SystemExit(message)
    print(f"PASS: rebuilt site matches {lock}")


if __name__ == "__main__":
    main()
