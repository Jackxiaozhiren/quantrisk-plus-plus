"""FRED series and ALFRED vintages.

Two access paths with two different rules, and conflating them is the easy mistake:

  * `fredgraph.csv` is the public download endpoint. It needs no key, and is what the
    ordinary "give me this series" call uses.
  * `api.stlouisfed.org` is the JSON API. It needs a key, and it is the **only** way to get
    an ALFRED vintage — the data as it stood on a given publication date rather than as it
    reads today.

The second distinction is the one that matters for this project. A backtest run on today's
revision of a macro series contains information that did not exist on the day it claims to
simulate, which is look-ahead bias by construction (PROJECT_SPEC.md §4). ALFRED exists to
avoid exactly that, so the vintage path is a first-class function here rather than an
afterthought, and it refuses cleanly when no key is configured instead of quietly falling
back to the current revision and producing a biased sample.

The key comes from the `FRED_API_KEY` environment variable and from nowhere else. It is
never written to a fixture, never logged, and never part of a URL that reaches a provenance
record — the record stores the series id and the endpoint, not the credential.
"""

from __future__ import annotations

import csv
import io
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quantrisk.data import http
from quantrisk.data.provenance import Provenance

FRED_API_KEY_ENVIRONMENT_VARIABLE = "FRED_API_KEY"
PUBLIC_CSV_ENDPOINT = "https://fred.stlouisfed.org/graph/fredgraph.csv"
API_JSON_ENDPOINT = "https://api.stlouisfed.org/fred/series/observations"

# The categories PROJECT_SPEC.md §Phase 8 lists, with the series St. Louis Federal Reserve
# publishes them under. These are identifiers, not data: the numbers arrive on fetch.
SERIES_CATALOGUE: dict[str, dict[str, str]] = {
    "policy_rate": {"DFF": "Federal funds effective rate, daily"},
    "treasury_rate": {
        "DGS3MO": "3-month Treasury constant maturity, daily",
        "DGS10": "10-year Treasury constant maturity, daily",
    },
    "inflation": {
        "CPIANSNSA": "CPI, all items, not seasonally adjusted, monthly",
        "PCEPI": "PCE price index, monthly",
    },
    "unemployment": {"UNRATE": "Civilian unemployment rate, monthly"},
    "credit_spread": {
        "BAMLH0A0HYM2": "ICE BofA US high yield option-adjusted spread, weekly",
        "BAMLC0A0CM": "ICE BofA US corporate master option-adjusted spread, weekly",
    },
    "volatility_related": {
        "VIXCLS": "CBOE VIX close, daily",
        "T10Y2Y": "10-year minus 2-year Treasury constant maturity spread, daily",
    },
}


class MissingApiKey(RuntimeError):
    """The requested endpoint needs a credential that is not configured."""


@dataclass(frozen=True)
class SeriesObservation:
    date: str
    value: float | None  # FRED's "." placeholder for a missing print is kept, not dropped
    vintage: str = ""


@dataclass(frozen=True)
class Series:
    series_id: str
    title: str
    observations: list[SeriesObservation]
    provenance: Provenance

    def values(self) -> list[tuple[str, float]]:
        return [(row.date, row.value) for row in self.observations if row.value is not None]


def api_key() -> str:
    return os.environ.get(FRED_API_KEY_ENVIRONMENT_VARIABLE, "").strip()


def graph_url(series_id: str, start: str | None = None, end: str | None = None) -> str:
    parts = [f"id={series_id}"]
    if start:
        parts.append(f"cosd={start}")
    if end:
        parts.append(f"coed={end}")
    return f"{PUBLIC_CSV_ENDPOINT}?{'&'.join(parts)}"


def _parse_graph_csv(data: bytes) -> list[SeriesObservation]:
    text = data.decode("utf-8-sig")
    rows: list[SeriesObservation] = []
    for record in csv.DictReader(io.StringIO(text)):
        keys = list(record)
        if len(keys) < 2:
            continue
        raw = (record[keys[1]] or "").strip()
        value: float | None = None if raw in {"", ".", "NA"} else float(raw)
        rows.append(SeriesObservation(date=str(record[keys[0]]), value=value))
    return rows


def fetch_series(
    series_id: str,
    *,
    start: str | None = None,
    end: str | None = None,
    cache_dir: Path | None = None,
) -> Series:
    """Current-revision observations from the public endpoint (no key required)."""
    url = graph_url(series_id, start, end)
    fetched = http.fetch(url, cache_dir=cache_dir)
    observations = _parse_graph_csv(fetched.data)
    provenance = Provenance.record(
        source="FRED fredgraph.csv (current revision)",
        url=fetched.url,
        series_id=series_id,
        data=fetched.data,
        license="St. Louis Federal Reserve terms of use; attribution requested",
        retrieved_at_utc=fetched.retrieved_at_utc,
        note=(
            "current revision, not the vintage that was known at the observation date; "
            "a backtest on these values can see later revisions"
        ),
        extra={"from_cache": fetched.from_cache, "observations": len(observations)},
    )
    return Series(series_id=series_id, title="", observations=observations, provenance=provenance)


def fetch_vintage(
    series_id: str,
    *,
    vintage_date: str,
    start: str | None = None,
    end: str | None = None,
    cache_dir: Path | None = None,
) -> Series:
    """ALFRED observations as published on `vintage_date`.

    Requires `FRED_API_KEY`. When it is absent this raises rather than substituting the
    current revision: a silently different dataset is worse than no dataset, because the
    result still looks like a backtest.
    """
    key = api_key()
    if not key:
        raise MissingApiKey(
            f"ALFRED vintages need {FRED_API_KEY_ENVIRONMENT_VARIABLE} in the environment. "
            f"Set it, or load the fixture with quantrisk.data.fixtures.load({series_id!r}). "
            "The current-revision endpoint is deliberately not used as a fallback: it would "
            "silently introduce look-ahead bias into a vintage study."
        )
    params = {
        "series_id": series_id,
        "file_type": "json",
        "api_key": key,
        "observation_start": start or "",
        "observation_end": end or "",
        "vintage_dates": vintage_date,
        "limit": "100000",
    }
    query = "&".join(
        f"{name}={value}" for name, value in params.items() if value != "" and name != "api_key"
    )
    # `url` is the credential-free form and is what gets cached and recorded; the key is
    # attached only to the request that leaves the process.
    url = f"{API_JSON_ENDPOINT}?{query}"
    fetched = http.fetch(f"{url}&api_key={key}", cache_dir=cache_dir, record_url=url)
    payload: dict[str, Any] = json.loads(fetched.data)
    rows = payload.get("observations", [])
    observations = [
        SeriesObservation(
            date=str(row.get("date", "")),
            value=None
            if str(row.get("value", ".")).strip() in {".", "", "NA"}
            else float(row["value"]),
            vintage=str(row.get("vintage_date", vintage_date)),
        )
        for row in rows
    ]
    # The stored URL has the credential stripped out; the cache key uses the same stripped
    # form so a key never lands in a filename, a sidecar, or a provenance record.
    provenance = Provenance.record(
        source="FRED ALFRED vintage (api.stlouisfed.org)",
        url=url,
        series_id=series_id,
        data=fetched.data,
        license="St. Louis Federal Reserve terms of use; attribution requested",
        retrieved_at_utc=fetched.retrieved_at_utc,
        note=f"as published on {vintage_date}",
        extra={
            "vintage_date": vintage_date,
            "observations": len(observations),
            "from_cache": fetched.from_cache,
        },
    )
    return Series(
        series_id=series_id,
        title=str(payload.get("title", "")),
        observations=observations,
        provenance=provenance,
    )
