"""Provenance records for anything fetched from a public source.

PROJECT_SPEC.md §Phase 8 requires four things be saved with every download: source,
timestamp, series identifier and SHA-256. They are collected here in one immutable record
rather than passed around as loose kwargs, because the failure mode this guards against is
a dataset reaching an analysis with no way to ask where its numbers came from.

The SHA-256 is computed over the exact bytes received, before any parsing. Recording a
digest of the *parsed* form would let a re-parse of the same file produce a different
digest, which defeats the purpose.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Provenance:
    """What was fetched, from where, when, and what it hashed to."""

    source: str
    url: str
    series_id: str
    retrieved_at_utc: str
    sha256: str
    bytes: int
    license: str
    request_policy: str = ""
    note: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def record(
        *,
        source: str,
        url: str,
        series_id: str,
        data: bytes,
        license: str,  # noqa: A002 - the spec's word for this field, and clearer than a rename
        retrieved_at_utc: str | None = None,
        request_policy: str = "",
        note: str = "",
        extra: dict[str, Any] | None = None,
    ) -> Provenance:
        return Provenance(
            source=source,
            url=url,
            series_id=series_id,
            retrieved_at_utc=retrieved_at_utc or utc_now(),
            sha256=sha256_of(data),
            bytes=len(data),
            license=license,
            request_policy=request_policy,
            note=note,
            extra=extra or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(payload: dict[str, Any]) -> Provenance:
        return Provenance(**payload)

    def verify(self, data: bytes) -> bool:
        """Does this record still describe these bytes?

        Returns a bool rather than raising so a caller can use it as a cache-validity
        check; the distinction between "stale" and "corrupt" is in the message the caller
        writes, not here.
        """
        return sha256_of(data) == self.sha256 and len(data) == self.bytes


def write_pair(path: Path, data: bytes, provenance: Provenance) -> Path:
    """Write payload and sidecar, and verify the round trip.

    The digest is re-read from disk rather than trusted from memory: a fixture committed
    with a stale SHA-256 is exactly the kind of thing that looks fine for months and then
    makes every downstream number unexplainable.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    sidecar = path.with_suffix(path.suffix + ".provenance.json")
    sidecar.write_text(json.dumps(provenance.to_dict(), indent=2) + "\n", encoding="utf-8")
    stored = path.read_bytes()
    if not provenance.verify(stored):
        raise ValueError(
            f"written bytes do not match the provenance record for {path}: "
            f"recorded {provenance.sha256}, on disk {sha256_of(stored)}"
        )
    return sidecar


def read_pair(path: Path) -> tuple[bytes, Provenance]:
    """Load a payload with its sidecar, refusing a mismatched digest."""
    sidecar = path.with_suffix(path.suffix + ".provenance.json")
    if not sidecar.exists():
        raise FileNotFoundError(
            f"{path} has no provenance sidecar at {sidecar.name}; a dataset with no "
            "recorded source is not usable as evidence"
        )
    provenance = Provenance.from_dict(json.loads(sidecar.read_text(encoding="utf-8")))
    data = path.read_bytes()
    if not provenance.verify(data):
        raise ValueError(
            f"{path} does not match its provenance record: recorded {provenance.sha256} "
            f"over {provenance.bytes} bytes, found {sha256_of(data)} over {len(data)} bytes"
        )
    return data, provenance
