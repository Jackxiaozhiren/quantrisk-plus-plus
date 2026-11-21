"""H4's zero-cost reading: three blocks of evidence, never a typed zero.

`INTERFACE_ROADMAP.md` line 146 states H4 as three asserts: the CI log shows no paid service, the
host is the free static tier, and the build's own budget line is asserted in the report. A producer
that returned `0` would repeat the policy rather than measure it -- the L12 shape that
`tools/inventory_orphan_code.py` records, where a policy file asserted a budget and the collector
returned the number it was told to return. So this module returns what it read:

- `actions`: every `uses:` reference in `.github/workflows/ci.yml`, set-differenced against the
  free first-party set, plus the runners the jobs name and whether a stored secret appears;
- `hosting`: the deploy job's own markers -- `actions/deploy-pages`, `pages: write`,
  `id-token: write`, the `github-pages` environment -- and whether a `CNAME` file exists, which
  would mean a custom domain rather than the default free host;
- `budget_line`: the sentence `README.md` asserts, located verbatim and counted, so a report that
  stopped asserting it makes the reading empty rather than silently satisfied.

Read-only; opens no socket; carries no numeric literal. The ceiling ("empty paid set", "free
hosting", "exactly one budget line") belongs to the guarding test, so the reading can fail.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..checkout import checkout_root

WORKFLOW = Path(".github") / "workflows" / "ci.yml"
REPORT = Path("README.md")
CNAME = Path("CNAME")

SCHEMA = "quantrisk-cost-audit/1"

# First-party actions that cost nothing and store no credential. A new entry here is a cost and
# trust decision, so the guard names the set rather than accepting any `uses:` line.
FREE_ACTIONS = (
    "actions/checkout@",
    "actions/setup-python@",
    "astral-sh/setup-uv@",
    "actions/upload-artifact@",
    "actions/upload-pages-artifact@",
    "actions/deploy-pages@",
)

# GitHub-hosted runners; the repository uses no larger or self-hosted runner, which would be billed.
FREE_RUNNERS = ("ubuntu-latest", "macos-15")

BUDGET_SENTENCE = "Total monetary cost of building and validating it:"

_USES = re.compile(r"^\s*(?:-\s*)?uses:\s*(?P<action>\S+)", re.MULTILINE)
_RUNS_ON = re.compile(r"^\s*runs-on:\s*(?P<runner>\S+)", re.MULTILINE)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _actions(text: str) -> dict[str, Any]:
    """Every action the workflow names, the ones outside the free set, and the runners."""
    used = sorted({match.group("action") for match in _USES.finditer(text)})
    paid = sorted(
        name for name in used if not any(name.startswith(prefix) for prefix in FREE_ACTIONS)
    )
    runners = sorted({match.group("runner") for match in _RUNS_ON.finditer(text)})
    billed = sorted(name for name in runners if name not in FREE_RUNNERS)
    return {
        "used": used,
        "paid": paid,
        "runners": runners,
        "billed": billed,
        "stored_secret": "secrets." in text or "${{ secrets" in text,
    }


def _hosting(text: str, base: Path) -> dict[str, Any]:
    """The deploy job's own markers, and whether a custom domain file exists."""
    deploy_pages = "actions/deploy-pages@" in text
    return {
        "platform": "github-pages" if deploy_pages else "",
        "free_static_tier": (
            deploy_pages
            and "pages: write" in text
            and "id-token: write" in text
            and "name: github-pages" in text
        ),
        "custom_domain": (base / CNAME).exists(),
    }


def _budget_line(path: Path) -> dict[str, Any]:
    """The report's own cost sentence, verbatim, with how many times it appears."""
    if not path.is_file():
        return {}
    matches = [line.strip() for line in _read(path).splitlines() if BUDGET_SENTENCE in line]
    if not matches:
        return {}
    return {"path": path.name, "text": next(iter(matches)), "occurrences": len(matches)}


def audit(root: Path | None = None) -> dict[str, Any]:
    """Read H4's three asserts from the committed workflow and report, and return the evidence."""
    base = checkout_root() if root is None else Path(root)
    workflow = _read(base / WORKFLOW)
    return {
        "schema": SCHEMA,
        "actions": _actions(workflow),
        "hosting": _hosting(workflow, base),
        "budget_line": _budget_line(base / REPORT),
    }
