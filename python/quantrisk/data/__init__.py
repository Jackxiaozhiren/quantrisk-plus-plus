"""Optional public-data adapters. Nothing in the numerical core imports this package.

The rule that keeps the project honest (§2.1, §Phase 8) is directional: `quantrisk.data`
may use `quantrisk`, and the analysis scripts may use both, but no pricing, risk or
optimisation code may reach in here. A core algorithm that needed a network response could
not be validated offline, and offline validation is the whole claim of the project.

Three sources, all free, all with a documented access policy:

  * `edgar` — SEC XBRL company facts. No key. User-Agent with a contact is required.
  * `fred` — FRED series (public CSV, no key) and ALFRED vintages (`FRED_API_KEY`).
  * `cftc` — Commitments of Traders annual archives. Optional, context only.

Everything reads through `http.fetch`, which caches by URL and rate-limits per host across
processes, and everything records a `Provenance` with source, URL, series id, retrieval
timestamp and the SHA-256 of the bytes as served. `fixtures` holds committed snapshots of
real responses so the test suite needs neither network nor credential.
"""

from __future__ import annotations

from quantrisk.data import cftc, edgar, fixtures, fred, http
from quantrisk.data.provenance import Provenance, read_pair, write_pair

__all__ = [
    "Provenance",
    "cftc",
    "edgar",
    "fixtures",
    "fred",
    "http",
    "read_pair",
    "write_pair",
]
