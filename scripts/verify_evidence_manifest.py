#!/usr/bin/env python3
"""Check the frozen evidence against `evidence/manifest.json`.

    uv run python scripts/verify_evidence_manifest.py

The manifest is only useful if something reads it back. This re-hashes every listed
artifact and reports three distinct outcomes rather than a single pass/fail, because they
mean different things to a reader:

  MISSING   the file is gone — the evidence was deleted or moved
  CHANGED   the *result content* differs — the number a README cites is no longer the number
            here. This is the one that matters.
  VOLATILE  the bytes differ but every result field is identical: the artifact was re-run, and
            what moved is its timestamp, its commit, its environment block or a wall-clock
            column. Expected, and reported separately from CHANGED so that a legitimate
            regeneration never masks, or is masked by, a real change.
  OK        the bytes still match

Exits non-zero on any MISSING or CHANGED, so it can gate CI. `--strict` additionally treats
VOLATILE as a failure, which is what you want when the evidence is meant to be byte-frozen
rather than merely reproducible. It also reports artifacts that
exist on disk but are *not* in the manifest, which is the quieter failure: add a benchmark,
forget to re-freeze, and the manifest still "passes" while describing an older state of the
world.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from quantrisk.data.provenance import sha256_of  # noqa: E402
from quantrisk.experiments.evidence import content_digest  # noqa: E402

MANIFEST = ROOT / "evidence" / "manifest.json"


def main() -> int:
    if not MANIFEST.exists():
        print(
            f"no manifest at {MANIFEST.relative_to(ROOT)}; run "
            "scripts/build_evidence_manifest.py first",
            file=sys.stderr,
        )
        return 2
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat a volatile-only regeneration as a failure",
    )
    arguments = parser.parse_args()

    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    listed: set[str] = set()
    ok, changed, volatile, missing = 0, [], [], []

    for entry in payload["artifacts"]:
        relative = entry["path"]
        listed.add(relative)
        path = ROOT / relative
        if not path.exists():
            missing.append(relative)
            continue
        actual = sha256_of(path.read_bytes())
        if actual == entry["sha256"]:
            ok += 1
            continue
        expected_content = entry.get("content_sha256")
        found_content = content_digest(path)
        if expected_content is not None and found_content == expected_content:
            volatile.append(relative)
        else:
            changed.append((relative, entry["sha256"][:12], actual[:12]))

    untracked = sorted(
        str(path.relative_to(ROOT))
        for directory in {str(Path(entry["path"]).parent) for entry in payload["artifacts"]}
        for path in (ROOT / directory).rglob("*")
        if path.is_file()
        and not path.name.endswith(".provenance.json")
        and str(path.relative_to(ROOT)) not in listed
    )

    print(
        f"manifest {payload['schema']} generated {payload['generated_utc']} "
        f"from commit {payload['repository']['git_commit'][:12]}"
    )
    print(f"  {ok:4d} OK")
    print(f"  {len(changed):4d} CHANGED (result content differs)")
    print(f"  {len(volatile):4d} VOLATILE (re-run, results identical)")
    print(f"  {len(missing):4d} MISSING")
    print(f"  {len(untracked):4d} on disk but not in the manifest")
    for relative, expected, actual in changed:
        print(f"  CHANGED  {relative}  expected {expected}… found {actual}…")
    for relative in volatile[:12]:
        print(f"  VOLATILE {relative}")
    if len(volatile) > 12:
        print(f"  ... and {len(volatile) - 12} more VOLATILE")
    for relative in missing:
        print(f"  MISSING  {relative}")
    for relative in untracked:
        print(f"  UNLISTED {relative}")
    if payload["warnings"]:
        print(f"  {len(payload['warnings'])} warning(s) recorded at generation time")

    failures = len(changed) + len(missing) + (len(volatile) if arguments.strict else 0)
    if failures == 0 and not untracked and not volatile:
        verdict = "\nEvidence is intact."
    elif failures == 0 and not untracked:
        verdict = (
            "\nEvidence reproduces: the numbers are identical, only run metadata and timings moved."
        )
    else:
        verdict = "\nEvidence does not match the manifest."
    print(verdict)
    return 1 if failures or untracked else 0


if __name__ == "__main__":
    sys.exit(main())
