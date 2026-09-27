"""Canonical hashing of evidence: separating "the numbers changed" from "the file was rewritten".

    from quantrisk.experiments.evidence import content_digest

A benchmark artifact records, alongside its results, the UTC minute it ran, the commit it was
built from, the environment it ran in, and — for anything measuring time — the times
themselves. Re-running it therefore changes the bytes while changing none of the mathematics,
so a plain SHA-256 comparison cannot answer the question anyone actually asks:

    "did the evidence move, or was it just regenerated?"

`content_digest` answers that. It hashes the artifact with the volatile fields removed, so
`evidence/manifest.json` can carry both digests: the byte hash for tamper detection, and the
content hash for reproducibility. When they disagree in different directions, the two
disagreements mean different things and are reported separately.

What counts as volatile is a judgement, so it is stated rather than buried:

* **Timestamps and revisions** (`generated_at_utc`, `git_commit`, `binary_git_commit`,
  `provenance`) identify *when and from what* the run happened. They are the most valuable
  fields in the artifact and the least stable.
* **Environment blocks** (`environment`, `host_environment`) record compiler, platform and
  package versions. Reproducing on another machine legitimately changes them.
* **Nested digests** (`artifacts`, `csv_sha256`, `sha256`, `bytes`) are hashes of *other*
  files; including them would make one drift cascade into every parent, which measures
  nothing.
* **Wall-clock columns** in CSVs — anything naming seconds, elapsed time or throughput. These
  are measurements of the machine, not of the model, and three artifacts are entirely about
  them.

Anything not on those lists is result data, and a change to it is a real change.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

VOLATILE_KEYS = frozenset(
    {
        "generated_at_utc",
        "generated_utc",
        "git_commit",
        "binary_git_commit",
        "provenance",
        "environment",
        "host_environment",
        "artifacts",
        "csv_sha256",
        "sha256",
        "bytes",
        "command",
        "command_source",
        "artifact_sha256",
        "retrieved_at_utc",
        "archive_sha256",
        "path",
        # The performance benchmark's own headline fields are ratios of wall-clock times, so
        # they are measurements of the machine. Its `measured_prices` and `z_score_vs_analytic`
        # are *not* — those are seeded model output, and they stay under the content hash.
        "results_seconds",
        "speedup_vs_pure_python",
        "speedup_vs_pure_python_using_min",
        "speedup_vs_numpy",
    }
)

# Substrings that mark a CSV column as a measurement of the machine rather than of the model.
VOLATILE_CSV_COLUMNS = ("second", "elapsed", "runtime", "duration", "throughput", "paths_per_s")


def _strip(node: Any) -> Any:
    if isinstance(node, dict):
        return {key: _strip(value) for key, value in node.items() if key not in VOLATILE_KEYS}
    if isinstance(node, list):
        return [_strip(item) for item in node]
    return node


def canonical_text(path: Path) -> str | None:
    """The volatile-free view of an artifact, or None if it has no meaningful canonical form.

    Binary files and plain text returns have no field structure to reason about, so every byte
    of them is content and the byte hash is the only honest check.
    """
    if path.suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return None
        return json.dumps(_strip(payload), sort_keys=True, separators=(",", ":"))
    if path.suffix == ".csv":
        text = path.read_text(encoding="utf-8")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return ""
        keep = [
            index
            for index, name in enumerate(rows[0])
            if not any(marker in name.lower() for marker in VOLATILE_CSV_COLUMNS)
        ]
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="\n").writerows(
            [row[index] for index in keep] for row in rows
        )
        return buffer.getvalue()
    return None


def content_digest(path: Path) -> str | None:
    """SHA-256 over the artifact's result content, or None when it is not canonicalisable."""
    canonical = canonical_text(path)
    if canonical is None:
        return None
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
