"""CFTC Commitments of Traders, optional and read-only.

The spec makes this arm optional, and it is the weakest-evidenced of the three sources:
CFTC publishes plain CSV archives with no schema version and no stability guarantee, and
the report's own category definitions have changed over time. So the parser is deliberately
thin — it returns rows keyed by whatever header CFTC actually sent, rather than a typed
model that would silently drift out of date — and the one thing it guarantees is that the
column names come from the file, not from this module.

Positioning data is market *context*. Nothing in the pricing, risk or optimisation layers
consumes it, and it should not be cited as evidence for a number elsewhere in the project.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quantrisk.data import http
from quantrisk.data.provenance import Provenance

# Annual "Commitments of Traders - Disaggregated" text archives, one per calendar year.
# Discovered from CFTC's own historical index rather than remembered: the older
# /files/debt/history/ paths the reports used to live under now 404 behind a redirect.
LEGACY_ANNUAL_TEMPLATE = "https://www.cftc.gov/files/dea/history/com_disagg_txt_{year}.zip"

# The header CFTC actually ships. Matched by name, never by position, because a column
# that moved would otherwise read as a plausible number from the wrong field.
REPORT_DATE_COLUMNS = ("Report_Date_as_YYYY-MM-DD", "As_of_Date_In_Form_YYMMDD")
MARKET_NAME_COLUMNS = ("Market_and_Exchange_Names", "Market Name")


@dataclass(frozen=True)
class CotTable:
    source_url: str
    rows: list[dict[str, Any]]
    columns: tuple[str, ...]
    provenance: Provenance

    @property
    def date_column(self) -> str | None:
        return next((name for name in REPORT_DATE_COLUMNS if name in self.columns), None)

    @property
    def market_column(self) -> str | None:
        return next((name for name in MARKET_NAME_COLUMNS if name in self.columns), None)

    def dates(self) -> list[str]:
        column = self.date_column
        if column is None:
            return []
        return sorted({str(row[column]) for row in self.rows})

    def for_market(self, market_name: str) -> list[dict[str, Any]]:
        column = self.market_column
        if column is None:
            return []
        return [row for row in self.rows if str(row.get(column, "")) == market_name]


def fetch_annual_legacy(
    year: int, *, cache_dir: Path | None = None, template: str = LEGACY_ANNUAL_TEMPLATE
) -> CotTable:
    """Download and parse one year of legacy COT data.

    The archive holds a single CSV. `http.decompress` picks it out, and the header row is
    taken from the file itself so a rename upstream shows up as a missing column instead of
    a wrong one.
    """
    if not 2000 <= year <= 2100:
        raise ValueError(f"COT year {year} is outside the range CFTC publishes")
    url = template.format(year=year)
    fetched = http.fetch(url, cache_dir=cache_dir)
    payload = http.decompress(fetched.data, hint=url)
    text = payload.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    columns = tuple(reader.fieldnames or ())
    if not columns:
        raise ValueError(
            f"{url} decompressed to something with no CSV header; refusing to guess columns"
        )
    rows = [dict(row) for row in reader]
    provenance = Provenance.record(
        source="CFTC Commitments of Traders, legacy annual archive",
        url=fetched.url,
        series_id=f"CFTC_COT_LEGACY_{year}",
        data=fetched.data,  # the digest covers the archive as served, not the parsed rows
        license="CFTC data is a work of the US government and is not copyrighted",
        retrieved_at_utc=fetched.retrieved_at_utc,
        note="compressed archive; sha256 is of the bytes as served",
        extra={
            "year": year,
            "rows": len(rows),
            "columns": len(columns),
            "from_cache": fetched.from_cache,
        },
    )
    return CotTable(source_url=fetched.url, rows=rows, columns=columns, provenance=provenance)
