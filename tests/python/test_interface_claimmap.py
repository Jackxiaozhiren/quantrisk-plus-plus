"""I-L8's guard: every published H value must still map to the run that recorded it.

The four H claims in section 3 of `INTERFACE_LEDGER.md` are the project's report of what it
measured. This guard re-derives, from the committed records on disk, the figure each claim quotes,
and requires that figure to still be present in the claim text. It does not trust a `mapped` flag
the producer typed: the ledger, the cold-start record, the site lock, the manifest and the budget
line are all read here again, so a plant that rewrites a claim (or a record) is visible in this
pytest process. A claim whose record cannot be read, or whose quoted figure disappeared, reddens.

The ceiling — all four map, none unmapped, none refused — is declared here, not in the producer.
The producer's source is scanned for numeric literals so no figure in the mapping could have come
from a constant typed beside it.
"""

from __future__ import annotations

import ast

from quantrisk.experiments.metadata import REPO_ROOT
from quantrisk.interface import claimmap, cost, provenance

CLAIMMAP_SOURCE = REPO_ROOT / "python" / "quantrisk" / "interface" / "claimmap.py"
# The ledger is named here, not only through claimmap's constant, so a plant editing it is bound to
# this guard by the pairing audit's text-link check as well as by the reading below.
LEDGER = REPO_ROOT / "INTERFACE_LEDGER.md"


def _numeric_literals(source: str) -> list[float]:
    """Every int or float literal in a source string, in source order. Booleans are not numbers."""
    found: list[float] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if isinstance(node.value, bool):
                continue
            found.append(node.value)
    return found


def _ledger_value_rows() -> dict[str, str]:
    """Re-read section 3's H rows from disk, independent of the producer's own parser."""
    rows: dict[str, str] = {}
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < len(claimmap.HYPOTHESES):
            continue
        first, second, *_rest = cells
        lead, *_tail = first.split()
        if lead in claimmap.HYPOTHESES:
            rows[lead] = second
    return rows


def test_every_h_value_claim_maps_to_its_recorded_run() -> None:
    """Guard behind plant `claim-map-drops-a-recorded-figure-from-the-report`.

    Each figure is re-derived here from its own committed record, then required to be present in
    the ledger text re-read from disk. The producer's aggregate is checked against the same
    independent derivation, so a producer that returned a fabricated `mapped` list could not pass.
    """
    base = REPO_ROOT
    rows = _ledger_value_rows()
    assert set(rows) == set(claimmap.HYPOTHESES), f"the ledger's H rows changed: {sorted(rows)}"

    cold = claimmap._json(base / claimmap.COLD_RECORD)
    price = str(cold["reproduction"]["produced"]["analytic_reference_price"])
    complete = provenance.completeness(base)
    coverage = f"{len(complete['resolved'])}/{len(complete['published'])}"
    lock = claimmap._json(base / claimmap.SITE_LOCK)
    digest = str(lock["pages"]["index.html"]["page_sha256"])
    budget = str(cost.audit(base)["budget_line"]["text"])

    expected = {"H1": price, "H2": coverage, "H3": digest, "H4": budget}
    for hypothesis, figure in expected.items():
        assert figure, f"{hypothesis}'s record carries no figure to map"
        assert figure in rows[hypothesis], (
            f"{hypothesis} quotes no longer carry the figure its record holds: {figure!r} absent "
            f"from the published claim; an unmapped claim must be deleted or corrected"
        )

    reading = claimmap.audit(base)
    assert reading["mapped"] == list(claimmap.HYPOTHESES), reading
    assert reading["unmapped"] == [], reading
    assert reading["refused"] == {}, reading
    for hypothesis in claimmap.HYPOTHESES:
        assert reading["claims"][hypothesis]["figure"] == expected[hypothesis], reading

    source = CLAIMMAP_SOURCE.read_text(encoding="utf-8")
    assert _numeric_literals("answer = 19\n") == [19], (
        "the scan missed a literal in a string known to contain one, so it would certify any file"
    )
    assert _numeric_literals(source) == [], (
        "the claim-map producer carries a numeric literal, so a figure could have come from a "
        "constant typed beside it"
    )
