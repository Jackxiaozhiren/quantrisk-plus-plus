"""Read the V9 final-tip census attestation where a lane can fail on it.

`V9_LEDGER.md` fixes a census taken at `5ec3fab`, the literal final tip of V8, between two comment
markers. Until V13 its only reader was a shell heredoc printed in that same ledger. Two things were
wrong with that. It ran where a person remembered to paste it, so no runner could object; and it
compared the attestation's counts with `runner --list` **at HEAD**, which decides a claim about a
past revision using a present-day count — the shape that goes red the first time an unrelated unit
adds a plant, and therefore a guard nobody would keep.

This tool keeps the half that is still true and checkable: the revision is a real commit, it is a
strict ancestor of `HEAD`, and the block is internally consistent with itself. It deliberately does
not compare the historical count with today's declaration. `V9_LEDGER.md` §6 item 4 forbids
refreshing the attestation to a newer tip; a reader that requires today's number would force exactly
that refresh, so the two rules cannot both hold and this one drops.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "quantrisk.final_tip_census_attestation/v1"
BLOCK = re.compile(
    r"<!-- V9_ATTESTATION_BEGIN -->\s*```json\s*(.*?)\s*```\s*<!-- V9_ATTESTATION_END -->",
    re.S,
)
LEDGER_GLOB = "V*_LEDGER.md"


def attestation_blocks(root: Path) -> list[tuple[str, str]]:
    """Every marked attestation in the series ledgers, as `(file, json text)`."""
    found: list[tuple[str, str]] = []
    for path in sorted(root.glob(LEDGER_GLOB)):
        for match in BLOCK.finditer(path.read_text(encoding="utf-8")):
            found.append((path.name, match.group(1)))
    return found


def _git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )


def verify(attestation: dict[str, Any], head: str, root: Path = REPO_ROOT) -> list[str]:
    """Why this attestation is refused, or an empty list when every check holds.

    Each check is one way the block can lie: the wrong schema, a revision that is not an object
    name, a revision this clone does not hold, the commit that carries the block naming itself,
    a revision that is not an ancestor, and counts that disagree with the summary the block also
    prints. The evidence limit is required too, because an attestation without it claims more than
    it measured.
    """
    reasons: list[str] = []
    if attestation.get("schema") != SCHEMA:
        reasons.append(f"the schema is {attestation.get('schema')!r}, not {SCHEMA!r}")
    revision = attestation.get("revision")
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        reasons.append("`revision` is not a 40-character lowercase hex object name")
        return reasons
    if _git("cat-file", "-e", f"{revision}^{{commit}}").returncode != 0:
        reasons.append(f"{revision} is not a commit object in this clone")
        return reasons
    if revision == head:
        reasons.append("the attestation names the commit that carries it (self-reference)")
    if _git("merge-base", "--is-ancestor", revision, head).returncode != 0:
        reasons.append(f"{revision} is not an ancestor of HEAD")
    rows = attestation.get("verdict_rows")
    declared = attestation.get("declared_plants")
    if not isinstance(rows, dict):
        reasons.append("`verdict_rows` is not an object")
        return reasons
    caught = rows.get("ok_caught")
    other = rows.get("other")
    if not isinstance(caught, int) or not isinstance(other, int) or not isinstance(declared, int):
        reasons.append(
            "`verdict_rows.ok_caught`, `verdict_rows.other` and `declared_plants` must be integers"
        )
        return reasons
    if other != 0:
        reasons.append(f"the attestation records {other} non-caught rows")
    if caught + other != declared:
        reasons.append(f"the rows sum to {caught + other}, not the {declared} it declares")
    summary = attestation.get("summary")
    printed = (
        re.search(r"(\d+)/(\d+) planted defects", summary) if isinstance(summary, str) else None
    )
    if printed is None:
        reasons.append("`summary` does not print a caught/declared pair")
    elif (int(printed.group(1)), int(printed.group(2))) != (caught, declared):
        reasons.append(f"`summary` prints {printed.group(0)!r}, which the rows do not support")
    log_lines = attestation.get("log_lines")
    if not isinstance(log_lines, int) or log_lines < declared:
        reasons.append("`log_lines` is not an integer at least as large as the declared count")
    if attestation.get("exit_code") != 0:
        reasons.append("`exit_code` is not 0")
    if attestation.get("tree_dirty_paths_after") != 0:
        reasons.append("`tree_dirty_paths_after` is not 0")
    if not str(attestation.get("evidence_limit") or "").strip():
        reasons.append("the attestation carries no `evidence_limit`")
    return reasons


def main(argv: list[str]) -> int:
    """The lane's entry point: exactly one block, and every check above it."""
    head = _git("rev-parse", "HEAD").stdout.strip()
    blocks = attestation_blocks(REPO_ROOT)
    if len(blocks) != 1:
        print(
            f"REFUSED: expected exactly one attestation block, found {len(blocks)}", file=sys.stderr
        )
        return 1
    name, text = blocks[0]
    try:
        attestation = json.loads(text)
    except json.JSONDecodeError as error:
        print(f"REFUSED: {name}'s block does not parse: {error}", file=sys.stderr)
        return 1
    if not isinstance(attestation, dict):
        print(f"REFUSED: {name}'s block holds no json object", file=sys.stderr)
        return 1
    reasons = verify(attestation, head)
    if reasons:
        for reason in reasons:
            print(f"REFUSED: {reason}", file=sys.stderr)
        return 1
    print(
        f"PASS: {name} attests {attestation['revision']} as a strict ancestor of {head[:12]}, "
        f"{attestation['verdict_rows']['ok_caught']} caught of "
        f"{attestation['declared_plants']} declared"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
