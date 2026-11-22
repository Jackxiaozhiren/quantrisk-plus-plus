"""H1: a cold user reproduces a published number without reading the repository.

The record is written by `tools/cold_start.py`, which builds a wheel, installs it into a fresh
environment outside the checkout, and runs one command from an empty working directory. The guard
below holds that record to the ceiling `INTERFACE_ROADMAP.md` line 143 states, and it reads the
published artifact from disk rather than trusting the record's own claim of equality: a record
whose number no longer matches the artifact has to redden here.
"""

from __future__ import annotations

import json
from pathlib import Path

from quantrisk.experiments.metadata import REPO_ROOT
from quantrisk.interface import coldstart

SCHEMA = "quantrisk-cold-start/1"


def test_the_cold_start_records_one_command_from_an_empty_directory_outside_the_checkout() -> None:
    reading = coldstart.audit()
    checkout = REPO_ROOT.resolve()
    assert reading["schema"] == SCHEMA
    assert reading["revision"]
    # A fresh environment and a neutral cwd, neither of them inside the repository.
    for named in ("venv_root", "cwd"):
        recorded = Path(reading[named]).resolve()
        assert recorded.is_absolute() and not str(recorded).startswith(f"{checkout}/"), named
    # Exactly one command, and nothing it named existed before it ran.
    assert reading["subprocess_invocations"] == 1
    assert reading["existing_paths_before"] == []
    assert reading["argv"][:3] == ["quantrisk", "run", reading["argv"][2]]
    assert not any(str(checkout) in element for element in reading["argv"])
    # Both clocks are measurements rather than placeholders.
    assert reading["run_wall_seconds"] > 0
    assert reading["install_wall_seconds"] > 0
    # How the environment got its runtime dependencies is recorded, never assumed.
    assert reading["install_mode"] in {"index", "seeded"}
    if reading["install_mode"] == "seeded":
        assert reading["seeded"] and reading["seed_reason"]
        assert "quantrisk" not in {name.lower() for name in reading["seeded"]}
    # The reproduction, re-derived from the published artifact instead of taken on faith.
    published = json.loads((REPO_ROOT / reading["published_artifact"]).read_text(encoding="utf-8"))
    produced = reading["produced"]
    assert {"analytic_reference_price", "measured_prices"} <= set(produced)
    assert {field: published[field] for field in produced} == produced
    # The exclusion is stated, not left for a reader to infer.
    assert reading["not_compared"]
    assert reading["not_compared_because"]
