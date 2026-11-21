"""H4's zero-cost guard: three asserts, each read from a file on disk.

`INTERFACE_ROADMAP.md` line 146 states H4 as three claims -- no paid service in CI, the free static
tier as host, and the report asserting its own budget line. Each is bound here to a target on disk,
so a plant editing that file is visible to this guard in its own pytest process. The reading is
evidence rather than a literal zero: the paid set must be empty, the host must carry the free-tier
markers and no custom domain, and the report must still assert the sentence exactly once. The
producer's own source is scanned for numeric literals, so no figure in the reading can have come
from a constant typed beside it.
"""

from __future__ import annotations

import ast

from quantrisk.experiments.metadata import REPO_ROOT
from quantrisk.interface import cost

COST_SOURCE = REPO_ROOT / "python" / "quantrisk" / "interface" / "cost.py"


def _numeric_literals(source: str) -> list[float]:
    """Every int or float literal in a source string, in source order. Booleans are not numbers."""
    found: list[float] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if isinstance(node.value, bool):
                continue
            found.append(node.value)
    return found


def test_the_zero_cost_claim_is_read_from_the_publish_surface_and_the_report() -> None:
    """Guard behind plant `report-drops-its-zero-cost-budget-line`.

    The three asserts are read together: a workflow that adds a paid action or a billed runner, a
    host that gains a custom domain, or a report that drops its budget line each makes one block of
    the reading move. The budget line is the assert only this guard covers; the paid-action assert
    has its own plant under I-L4, which is a narrower scan of the deploy job alone.
    """
    reading = cost.audit()

    actions = reading["actions"]
    assert actions["used"], "the workflow named no action, so the scan certifies nothing"
    assert actions["paid"] == [], f"the workflow added a paid action: {actions['paid']}"
    assert actions["runners"], "the workflow named no runner, so the scan certifies nothing"
    assert actions["billed"] == [], f"the workflow moved to a billed runner: {actions['billed']}"
    assert actions["stored_secret"] is False, "a stored secret appeared in the workflow"

    hosting = reading["hosting"]
    assert hosting["platform"] == "github-pages", hosting
    assert hosting["free_static_tier"] is True, hosting
    assert hosting["custom_domain"] is False, (
        "a CNAME file appeared, so the host is no longer the default free tier"
    )

    budget = reading["budget_line"]
    assert budget, "the report no longer asserts its zero-cost budget line"
    assert budget["path"] == "README.md", budget
    assert budget["occurrences"] == 1, (
        f"the budget line appears {budget['occurrences']} times, so it is not one assertion"
    )
    assert "$0" in budget["text"], budget

    source = COST_SOURCE.read_text(encoding="utf-8")
    assert _numeric_literals("answer = 19\n") == [19], (
        "the scan missed a literal in a string known to contain one, so it would certify any file"
    )
    assert _numeric_literals(source) == [], (
        "the cost producer carries a numeric literal, so a reading could have come from a constant"
    )
