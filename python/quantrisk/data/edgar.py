"""SEC EDGAR XBRL company facts.

No API key is required and none should be invented: EDGAR's JSON endpoints are public, and
the only condition SEC attaches is the User-Agent and rate limit enforced in `http.py`.

The layer maps the six items PROJECT_SPEC.md §Phase 8 names onto their us-gaap tags. The
mapping is explicit and small rather than "download every fact and grep", because company
facts payloads run to megabytes and because a tag that silently changed name in a filing
standard should produce a missing value with a note, not a wrong number.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quantrisk.data import http
from quantrisk.data.provenance import Provenance

# The spec's six quantities, in the order a report should show them. Each maps to the
# us-gaap tags tried in order: a filer that uses a more specific tag still resolves.
SPEC_ITEMS: dict[str, tuple[str, ...]] = {
    "assets": ("Assets", "AssetsCurrent"),
    "liabilities": ("Liabilities", "LiabilitiesCurrent"),
    "cash": (
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ),
    "debt": (
        "LongTermDebtNoncurrent",
        "LongTermDebt",
        "LongTermDebtMaturitiesRepaymentsOfPrincipalAfterYearTwo",
    ),
    "revenue": ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"),
    "earnings": ("NetIncomeLoss",),
}

CIK_PATTERN = re.compile(r"^(\d{1,10})$")


@dataclass(frozen=True)
class Observation:
    """One reported value for one tag at one period end."""

    end: str
    value: float
    form: str
    fiscal_year: int
    fiscal_period: str
    filed: str
    frame: str = ""

    @staticmethod
    def from_edgar(row: dict[str, Any]) -> Observation:
        # `.get(key, default)` returns None when the key is present with a JSON null,
        # which EDGAR really does send: `fy` and `fp` are absent for some restated and
        # frame-derived facts. Found against live data, not against a hand-written sample.
        fiscal_year = row.get("fy")
        return Observation(
            end=str(row.get("end", "")),
            value=float(row["val"]),
            form=str(row.get("form", "")),
            fiscal_year=int(fiscal_year) if fiscal_year is not None else 0,
            fiscal_period=str(row.get("fp") or ""),
            filed=str(row.get("filed", "")),
            frame=str(row["frame"]) if row.get("frame") else "",
        )


@dataclass(frozen=True)
class Financials:
    cik: str
    entity_name: str
    items: dict[str, list[Observation]]
    provenance: dict[str, Provenance]
    missing: tuple[str, ...] = ()


def normalise_cik(value: str | int) -> str:
    text = str(value).strip()
    match = CIK_PATTERN.match(text)
    if not match:
        raise ValueError(
            f"CIC {value!r} is not a 1-10 digit identifier; EDGAR paths are built from the "
            "zero-padded CIK and a wrong one silently returns another company's numbers"
        )
    return match.group(1).zfill(10)


def concept_url(cik: str | int, taxonomy: str, tag: str) -> str:
    return (
        "https://data.sec.gov/api/xbrl/companyconcept/"
        f"CIK{normalise_cik(cik)}/{taxonomy}/{tag}.json"
    )


def fetch_concept(
    cik: str | int, tag: str, *, taxonomy: str = "us-gaap", cache_dir: Path | None = None
) -> tuple[list[Observation], Provenance]:
    url = concept_url(cik, taxonomy, tag)
    fetched = http.fetch(url, cache_dir=cache_dir)
    payload = json.loads(fetched.data)
    observations = [Observation.from_edgar(row) for row in payload.get("units", {}).get("USD", [])]
    provenance = Provenance.record(
        source="SEC EDGAR companyconcept",
        url=fetched.url,
        series_id=f"CIK{normalise_cik(cik)}:{taxonomy}:{tag}",
        data=fetched.data,
        license=(
            "SEC EDGAR data is disclosed to the public and is not subject to copyright; "
            "see https://www.sec.gov/edgar/searchedgar/accessing-edgar-data"
        ),
        retrieved_at_utc=fetched.retrieved_at_utc,
        request_policy="User-Agent with contact required; <=10 requests/second per IP",
        extra={
            "cik": normalise_cik(cik),
            "taxonomy": taxonomy,
            "tag": tag,
            "observations": len(observations),
            "from_cache": fetched.from_cache,
        },
    )
    return observations, provenance


def company_financials(
    cik: str | int,
    *,
    items: Iterable[str] | None = None,
    cache_dir: Path | None = None,
    entity_name: str = "",
) -> Financials:
    """Resolve the requested spec items for one company.

    A tag that no filer in the sample uses is reported in `missing` rather than dropped:
    an absent balance is different from a zero balance, and a caller computing leverage
    needs to know which one it is holding.
    """
    wanted = list(items) if items else list(SPEC_ITEMS)
    resolved: dict[str, list[Observation]] = {}
    provenance: dict[str, Provenance] = {}
    missing: list[str] = []
    for item in wanted:
        tags = SPEC_ITEMS.get(item, (item,))
        found: list[Observation] | None = None
        for tag in tags:
            try:
                observations, record = fetch_concept(cik, tag, cache_dir=cache_dir)
            except (RuntimeError, http.RequestPolicyError, KeyError, ValueError):
                continue
            if observations:
                found = observations
                provenance[item] = record
                break
        if found is None:
            missing.append(item)
        else:
            resolved[item] = found
    return Financials(
        cik=normalise_cik(cik),
        entity_name=entity_name,
        items=resolved,
        provenance=provenance,
        missing=tuple(missing),
    )


def latest(observations: list[Observation], *, annual_only: bool = True) -> Observation | None:
    """The most recent period end, optionally restricted to 10-K filings."""
    pool = [
        row
        for row in observations
        if (row.form == "10-K") or (not annual_only and row.form in {"10-K", "10-Q"})
    ]
    if not pool:
        return None
    return max(pool, key=lambda row: (row.end, row.filed))
