#!/usr/bin/env python3
"""Record the offline data fixtures from the live public sources.

    QUANTRISK_DATA_USER_AGENT="Name (contact: you@example.com)" \\
        uv run python scripts/record_data_fixtures.py

Fixtures are real responses, committed small, each with a provenance sidecar carrying the
URL, the retrieval timestamp and the SHA-256 of the bytes as served. That is what lets the
test suite be offline without being fictional.

Re-running refreshes every snapshot and rewrites every digest, so a fixture's provenance
always describes the file next to it rather than whatever was fetched when someone last
remembered. Anything too large to commit is stored as an excerpt and labelled as one in its
own `note`, because a truncated copy presented with the source's digest would later read as
corruption.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from quantrisk.data import cftc, edgar, fixtures, fred, http  # noqa: E402
from quantrisk.data.provenance import Provenance, write_pair  # noqa: E402

FIXTURES = fixtures.FIXTURE_ROOT
MAX_COMMITTED_BYTES = 200_000

# A handful of filings, chosen for breadth of balance-sheet shape rather than for size.
EDGAR_CONCEPTS = [
    (320193, "Assets", "apple"),
    (320193, "Liabilities", "apple"),
    (320193, "CashAndCashEquivalentsAtCarryingValue", "apple"),
    (320193, "Revenues", "apple"),
    (320193, "NetIncomeLoss", "apple"),
    (1652044, "Assets", "madison_square_garden"),
]

FRED_SERIES = [
    ("DFF", "2024-01-01", "2024-01-31"),
    ("DGS10", "2024-01-01", "2024-03-31"),
    ("VIXCLS", "2024-01-01", "2024-02-15"),
    ("UNRATE", "2023-01-01", "2024-06-30"),
    ("BAMLH0A0HYM2", "2024-01-01", "2024-03-31"),
]

# The real-data risk study needs a decade of daily observations, and it needs them
# committed: the experiment must run offline, so "fetch it live" is not reproducibility,
# it is a dependency on a third party's uptime and revision history.
#
# Only market-observation series are used, and that filter is the whole point. `UNRATE`
# is in FRED_SERIES above because the parser needs a monthly series to test against, but
# it is excluded here deliberately: macro aggregates are revised, sometimes heavily, so a
# current-revision backtest on them would silently trade on information nobody had. A
# Treasury par yield, a CBOE index and an ICE bond index are prints, not estimates, and
# are revised only to correct an error.
FRED_HISTORY = [
    ("DGS10", "2014-01-01", "2026-09-26", "Treasury par yield, market-observed"),
    ("T10YIE", "2014-01-01", "2026-09-26", "TIPS breakeven inflation, market-observed"),
    ("VIXCLS", "2014-01-01", "2026-09-26", "CBOE index, market-observed"),
]


def record(name: str, data: bytes, provenance: Provenance) -> Path:
    if len(data) > MAX_COMMITTED_BYTES:
        raise SystemExit(
            f"{name} came back at {len(data)} bytes, over the {MAX_COMMITTED_BYTES} "
            "commit limit. Narrow the request rather than widening the limit."
        )
    sidecar = write_pair(FIXTURES / name, data, provenance)
    print(f"  wrote {name} ({len(data)} bytes) -> {sidecar.name}")
    return sidecar


def record_edgar() -> None:
    print("SEC EDGAR company concepts")
    for cik, tag, _slug in EDGAR_CONCEPTS:
        url = edgar.concept_url(cik, "us-gaap", tag)
        fetched = http.fetch(url)
        if len(fetched.data) > MAX_COMMITTED_BYTES:
            print(f"  skipped CIK{cik} {tag}: {len(fetched.data)} bytes, too large")
            continue
        payload = json.loads(fetched.data)
        provenance = Provenance.record(
            source="SEC EDGAR companyconcept (live response)",
            url=fetched.url,
            series_id=f"CIK{edgar.normalise_cik(cik)}:us-gaap:{tag}",
            data=fetched.data,
            license=("SEC EDGAR data is disclosed to the public and is not subject to copyright"),
            retrieved_at_utc=fetched.retrieved_at_utc,
            request_policy=(
                "User-Agent naming a contact required; <=10 requests/second per IP, "
                "per https://www.sec.gov/os/accessing-edgar-data"
            ),
            extra={
                "cik": edgar.normalise_cik(cik),
                "tag": tag,
                "entity_name": payload.get("entityName", ""),
                "observations": len(payload.get("units", {}).get("USD", [])),
            },
        )
        record(f"edgar_{edgar.normalise_cik(cik)}_{tag}.json", fetched.data, provenance)


def record_fred() -> None:
    print("FRED current-revision series (public CSV, no key)")
    for series_id, start, end in FRED_SERIES:
        url = fred.graph_url(series_id, start, end)
        fetched = http.fetch(url)
        provenance = Provenance.record(
            source="FRED fredgraph.csv (live response, current revision)",
            url=fetched.url,
            series_id=series_id,
            data=fetched.data,
            license="St. Louis Federal Reserve terms of use; attribution requested",
            retrieved_at_utc=fetched.retrieved_at_utc,
            note=(
                "current revision, not the vintage known at the observation date; a "
                "backtest on these values can see later revisions"
            ),
            extra={"observation_start": start, "observation_end": end},
        )
        record(f"fred_{series_id}_{start}_{end}.csv", fetched.data, provenance)


def record_fred_history() -> None:
    """Long daily windows for the real-data risk study, from the key-free CSV endpoint."""
    print("FRED long daily history (public CSV, no key)")
    for series_id, start, end, observation_kind in FRED_HISTORY:
        url = fred.graph_url(series_id, start, end)
        fetched = http.fetch(url)
        provenance = Provenance.record(
            source="FRED fredgraph.csv (live response, current revision)",
            url=fetched.url,
            series_id=series_id,
            data=fetched.data,
            license="St. Louis Federal Reserve terms of use; attribution requested",
            retrieved_at_utc=fetched.retrieved_at_utc,
            note=(
                f"{observation_kind}. Current revision, not the vintage as published at each "
                "observation date: an ALFRED key would be needed to remove that exposure "
                "entirely. Market observations of this kind are revised to correct data "
                "errors rather than re-estimated, which is why these three and not a macro "
                "aggregate."
            ),
            extra={
                "observation_start": start,
                "observation_end": end,
                "observation_kind": observation_kind,
                "revised_in_place": "unlikely; these are prints, not estimates",
                "used_by": "experiments/real_data_risk_study",
            },
        )
        record(f"fred_{series_id}_{start}_{end}.csv", fetched.data, provenance)


def record_fred_vintage_shape() -> None:
    """A synthetic ALFRED-shaped payload, labelled as synthetic.

    ALFRED needs an API key, so a live capture cannot be recorded here, and the vintage
    parser still has to be tested offline. This file exists to be parsed, not to be
    believed: it is marked synthetic in its own provenance and the test that reads it is a
    parsing test, never a data test.
    """
    print("ALFRED-shaped fixture (synthetic, for parser coverage only)")
    payload = {
        "observations": [
            {
                "date": day,
                "value": f"{5.33 + index * 0.01:.2f}",
                "vintage_date": "2024-02-01",
                "realtime_start": "2024-02-01",
                "realtime_end": "9999-12-31",
                "adj_observation": "1",
            }
            for index, day in enumerate(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"])
        ],
        "limit": 100000,
        "offset": 0,
        "count": 4,
        "series_id": "DFF",
        "title": "Synthetic fixture - not FRED data",
        "units": "lin",
        "observation_start": "2024-01-01",
        "observation_end": "2024-01-31",
        "vintage_date": "2024-02-01",
    }
    data = json.dumps(payload, indent=2).encode("utf-8")
    provenance = Provenance.record(
        source="SYNTHETIC - shaped like a FRED ALFRED API response, authored for this repo",
        url="file://synthetic",
        series_id="DFF:synthetic-vintage-fixture",
        data=data,
        license="Not applicable: contains no third-party data",
        note=(
            "NOT REAL DATA. Shaped like the ALFRED JSON response so the vintage parser can "
            "be tested without an API key. No number in this file describes any economy."
        ),
        extra={"synthetic": True, "vintage_date": "2024-02-01"},
    )
    record("fred_vintage_shape_synthetic.json", data, provenance)


def record_cftc() -> None:
    print("CFTC legacy Commitments of Traders (excerpt)")
    year = 2024
    url = cftc.LEGACY_ANNUAL_TEMPLATE.format(year=year)
    fetched = http.fetch(url)
    print(f"  archive is {len(fetched.data)} bytes compressed")
    payload = http.decompress(fetched.data, hint=url)
    text = payload.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise SystemExit(f"{url} decompressed to nothing")
    header = rows[0]
    # The date column is located by name. Index 0 is the market name, and slicing on it
    # would key the excerpt off the wrong field without any error to show for it.
    named = {name.strip(): index for index, name in enumerate(header)}
    date_name = next(
        (candidate for candidate in cftc.REPORT_DATE_COLUMNS if candidate in named), None
    )
    if date_name is None:
        raise SystemExit(f"{url} has no recognised report-date column in {header[:6]}")
    date_column = named[date_name]
    market_column = named.get(cftc.MARKET_NAME_COLUMNS[0], 0)
    kept = [header]
    seen_dates: list[str] = []
    for row in rows[1:]:
        if len(row) != len(header):
            continue
        stamp = row[date_column]
        if stamp not in seen_dates:
            if len(seen_dates) >= 3:
                break
            seen_dates.append(stamp)
        if stamp in seen_dates:
            kept.append(row)
    markets = {row[market_column] for row in kept[1:]}
    excerpt = "\r\n".join(",".join(field.strip() for field in row) for row in kept) + "\r\n"
    data = excerpt.encode("utf-8")
    provenance = Provenance.record(
        source="CFTC annual Disaggregated COT archive, EXCERPT of the decompressed CSV",
        url=url,
        series_id=f"CFTC_COT_DISAGG_{year}",
        data=data,
        license="CFTC data is a work of the US government and is not copyrighted",
        retrieved_at_utc=fetched.retrieved_at_utc,
        note=(
            f"EXCERPT, not the full archive: {len(kept) - 1} of {len(rows) - 1} rows kept. "
            f"The sha256 covers this excerpt, not the {len(fetched.data)}-byte compressed "
            "source, because the archive is too large to commit; re-run this script against "
            "the URL to reproduce the original bytes."
        ),
        extra={
            "year": year,
            "rows_kept": len(kept) - 1,
            "rows_available": len(rows) - 1,
            "markets_kept": len(markets),
            "report_dates_kept": seen_dates,
            "excerpt": True,
            "archive_bytes": len(fetched.data),
            "archive_sha256": fetched.sha256,
        },
    )
    record(f"cftc_disagg_cot_{year}_excerpt.csv", data, provenance)


def main() -> int:
    if not http.user_agent_for("https://data.sec.gov/"):
        raise SystemExit("a User-Agent is required")
    FIXTURES.mkdir(parents=True, exist_ok=True)
    record_edgar()
    record_fred()
    record_fred_history()
    record_fred_vintage_shape()
    record_cftc()
    print(f"fixtures under {FIXTURES.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
