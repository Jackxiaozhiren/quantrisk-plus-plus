"""Offline fixtures, so the test suite never needs a socket or a credential.

PROJECT_SPEC.md §Phase 8 states this twice — "CI must run fully offline" and "network APIs
must not become a test dependency" — and it is the reason the data layer can exist at all
without weakening anything else in the project. Every fixture is a real response from the
source it names, with a provenance sidecar recording the URL, the retrieval timestamp and
the SHA-256 of the bytes on disk.

Two honesty rules follow from that:

  * A fixture's digest covers what is committed. Where the original was a compressed
    archive too large to commit, the sidecar says so and the digest is of the excerpt, not
    of the archive. Claiming a source digest for a truncated copy would make the mismatch
    look like corruption later.
  * A fixture is a snapshot. It does not update, and a test that compares against it is
    testing parsing and plumbing, not the state of the world.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from quantrisk.data.provenance import Provenance

FIXTURE_ROOT = Path(__file__).resolve().parents[3] / "data" / "fixtures"


class FixtureNotFound(FileNotFoundError):
    pass


@dataclass(frozen=True)
class Fixture:
    name: str
    path: Path
    data: bytes
    provenance: Provenance

    def json(self) -> object:
        return json.loads(self.data)

    def text(self) -> str:
        return self.data.decode("utf-8")


def available(root: Path | None = None) -> list[str]:
    """The fixture names, without the payload extension.

    Names are extension-free on purpose: a caller should not have to know whether a
    snapshot landed as `.json` or `.csv`, and that is a detail of what the source served.
    `load` still accepts the extended form so a name copied off the directory listing
    works too.
    """
    directory = root or FIXTURE_ROOT
    if not directory.exists():
        return []
    return sorted(
        path.name[: -len(".provenance.json")].split(".", 1)[0]
        for path in directory.glob("*.provenance.json")
    )


def load(name: str, *, root: Path | None = None) -> Fixture:
    """Read a fixture and verify it still matches its own provenance record."""
    directory = root or FIXTURE_ROOT
    sidecar = directory / f"{name}.provenance.json"
    if not sidecar.exists():
        # Accept the extension-free form too, which is what `available` returns.
        matches = sorted(directory.glob(f"{name}.*.provenance.json"))
        if len(matches) == 1:
            sidecar = matches[0]
    if not sidecar.exists():
        raise FixtureNotFound(
            f"no fixture named {name!r} under {directory}. Available: "
            f"{', '.join(available(directory)) or 'none'}"
        )
    provenance = Provenance.from_dict(json.loads(sidecar.read_text(encoding="utf-8")))
    payload = directory / sidecar.name[: -len(".provenance.json")]
    if not payload.exists():
        raise FixtureNotFound(
            f"{sidecar.name} records a fixture at {payload.name} which is not on disk"
        )
    data = payload.read_bytes()
    if not provenance.verify(data):
        raise ValueError(
            f"fixture {name!r} does not match its provenance record: {provenance.sha256} "
            f"expected over {provenance.bytes} bytes, found the digest of {len(data)} bytes "
            "as something else. The fixture has been edited without being re-recorded."
        )
    return Fixture(name=name, path=payload, data=data, provenance=provenance)
