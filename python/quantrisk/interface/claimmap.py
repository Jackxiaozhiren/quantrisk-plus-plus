"""I-L8's report-level audit: every H value must map back to a recorded run.

`INTERFACE_ROADMAP.md` line 302 states I-L8 as "Every value claim in the report maps to a recorded
run; unmapped claims are deleted". The claim-inventory guards in `test_artifact_metadata.py` already
police the `<number> <noun>` claims in the README, the reproducibility doc and the paper. They do
not cover section 3 of `INTERFACE_LEDGER.md`, where the four H measurements are published; that
table had no guard binding each value back to the committed record that produced it. This module
closes that gap in the reverse direction the four producers do not take: it starts from each
published H claim and asks whether the figure it quotes is still present in the record it names.

Four claims, four committed records, each read afresh:

- H1's `analytic_reference_price` is checked against the price in `tools/cold_start_record.json`'s
  reproduction, the record written by the cold-start run;
- H2's coverage fraction is rebuilt from `provenance.completeness()`'s resolved and published sets;
- H3's index digest is read from the committed `build/site.lock` page entry;
- H4's budget sentence is read from `cost.audit()`'s budget-line block.

A claim maps only when the figure derived from its record appears verbatim in the claim text; if a
record cannot be read, or a quoted figure disappears from it, the claim lands in `unmapped` and is
named. The producer returns sets rather than a ratio and carries no ceiling: a guarding test owns
the policy that all four map, so an unmapped claim can redden it. Read-only, no socket, no numeric
literal — the numbers it handles are all derived from files on disk.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..checkout import checkout_root
from . import cost, provenance

LEDGER = Path("INTERFACE_LEDGER.md")
COLD_RECORD = Path("tools") / "cold_start_record.json"
SITE_LOCK = Path("build") / "site.lock"

SCHEMA = "quantrisk-claim-map/1"

# The four hypothesis identifiers are the rows this audit reads from section 3. A row is named by
# its first cell; the value claim is the second. Both are read from the ledger, never typed here as
# a number, so a rewritten claim is visible to the guard that reads the same file.
HYPOTHESES = ("H1", "H2", "H3", "H4")


class ClaimMapRefused(RuntimeError):
    """A record named by a claim could not be read or parsed, so the claim cannot be mapped."""


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise ClaimMapRefused(f"cannot read {path.as_posix()}: {error}") from error


def _json(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(_read(path))
    except ValueError as error:
        raise ClaimMapRefused(f"cannot parse {path.as_posix()}: {error}") from error
    if not isinstance(document, dict):
        raise ClaimMapRefused(f"{path.as_posix()} is not a JSON object")
    return document


def _claims(base: Path) -> dict[str, str]:
    """The section 3 Value column for each H row, verbatim from the ledger on disk."""
    claims: dict[str, str] = {}
    for line in _read(base / LEDGER).splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < len(HYPOTHESES):
            continue
        first, second, *_rest = cells
        lead, *_tail = first.split()
        if lead in HYPOTHESES:
            claims[lead] = second
    return claims


def _h1_figure(base: Path) -> str:
    record = _json(base / COLD_RECORD)
    try:
        return str(record["reproduction"]["produced"]["analytic_reference_price"])
    except (KeyError, TypeError) as error:
        raise ClaimMapRefused(
            f"the cold-start record carries no reproduced price: {error}"
        ) from error


def _h2_figure(base: Path) -> str:
    try:
        reading = provenance.completeness(base)
    except Exception as error:  # a refusal names the unreadable manifest as the gap
        raise ClaimMapRefused(f"provenance completeness is unreadable: {error}") from error
    resolved = len(reading["resolved"])
    published = len(reading["published"])
    return f"{resolved}/{published}"


def _h3_figure(base: Path) -> str:
    lock = _json(base / SITE_LOCK)
    try:
        return str(lock["pages"]["index.html"]["page_sha256"])
    except (KeyError, TypeError) as error:
        raise ClaimMapRefused(f"the site lock carries no index page digest: {error}") from error


def _h4_figure(base: Path) -> str:
    try:
        reading = cost.audit(base)
    except Exception as error:
        raise ClaimMapRefused(f"the cost audit is unreadable: {error}") from error
    line = reading.get("budget_line", {})
    text = line.get("text", "") if isinstance(line, dict) else ""
    if not text:
        raise ClaimMapRefused("the cost audit reports no budget line to map H4 to")
    return str(text)


_FIGURES = {"H1": _h1_figure, "H2": _h2_figure, "H3": _h3_figure, "H4": _h4_figure}


def audit(root: Path | None = None) -> dict[str, Any]:
    """Map each section 3 H claim to its recorded run and report which figures still match.

    Returns the claim text, the record path and the derived figure for every H, plus the mapped and
    unmapped identifier sets and the refused records named by their gaps. No figure is reduced to a
    ratio and no ceiling is asserted here: a guard owns both.
    """
    base = checkout_root() if root is None else Path(root)
    claims = _claims(base)
    records = {
        "H1": COLD_RECORD.as_posix(),
        "H2": "provenance.completeness() over the manifest and registry",
        "H3": SITE_LOCK.as_posix(),
        "H4": (Path("README.md")).as_posix(),
    }
    mapped: list[str] = []
    unmapped: list[str] = []
    refused: dict[str, str] = {}
    details: dict[str, dict[str, str | bool]] = {}
    for hypothesis in HYPOTHESES:
        claim = claims.get(hypothesis, "")
        try:
            figure = _FIGURES[hypothesis](base)
        except ClaimMapRefused as error:
            refused[hypothesis] = str(error)
            unmapped.append(hypothesis)
            details[hypothesis] = {
                "claim": claim,
                "record": records[hypothesis],
                "figure": "",
                "mapped": False,
            }
            continue
        present = bool(figure) and bool(claim) and figure in claim
        (mapped if present else unmapped).append(hypothesis)
        details[hypothesis] = {
            "claim": claim,
            "record": records[hypothesis],
            "figure": figure,
            "mapped": present,
        }
    return {
        "schema": SCHEMA,
        "claims": details,
        "mapped": mapped,
        "unmapped": unmapped,
        "refused": refused,
    }
