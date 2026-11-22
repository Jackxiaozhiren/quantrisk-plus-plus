"""H1's cold-start reading: what a scripted run left behind, checked rather than asserted.

`INTERFACE_ROADMAP.md` line 143 states H1 as a scripted run with a fresh venv, a neutral cwd, one
command from install-listing to artifact, no repository checkout, no file name known in advance,
and a wall clock. `tools/cold_start.py` performs that run and writes the record this module reads;
the module exists so the reading is a value a guard can hold to a ceiling, not a paragraph.

It returns the evidence and decides nothing: the paths the run used, the command it typed, the
names that already existed, the invocation count, both wall clocks, the fields the run reproduced
and the fields it deliberately did not. It carries no numeric literal and no threshold -- "one
command", "nothing existed before", "the wall clock is positive", "the price equals the published
one" all belong to the guarding test, so the reading can fail. It opens no socket and starts no
process: the run happened once in the tool, and this is the record of it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..checkout import checkout_root

RECORD = Path("tools") / "cold_start_record.json"


def audit(record: Path | None = None, root: Path | None = None) -> dict[str, Any]:
    """Return the cold-start evidence as recorded, without judging whether it is good enough."""
    base = checkout_root() if root is None else Path(root)
    path = base / RECORD if record is None else Path(record)
    if not path.is_file():
        raise FileNotFoundError(f"no cold-start record at {path}; run tools.cold_start first")
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    environment = data.get("environment") or {}
    run = data.get("run") or {}
    reproduction = data.get("reproduction") or {}
    return {
        "schema": data.get("schema"),
        "revision": data.get("revision"),
        "checkout": data.get("checkout"),
        "venv_root": environment.get("venv_root"),
        "cwd": run.get("cwd"),
        "argv": run.get("argv") or [],
        "existing_paths_before": run.get("existing_paths_before") or [],
        "subprocess_invocations": run.get("subprocess_invocations"),
        "run_wall_seconds": run.get("wall_seconds"),
        "install_wall_seconds": (data.get("install") or {}).get("wall_seconds"),
        "install_mode": (data.get("install") or {}).get("mode"),
        "seeded": (data.get("install") or {}).get("seeded") or {},
        "seed_reason": (data.get("install") or {}).get("seed_reason") or "",
        "produced": reproduction.get("produced") or {},
        "published_artifact": reproduction.get("published_artifact"),
        "not_compared": reproduction.get("not_compared") or [],
        "not_compared_because": reproduction.get("not_compared_because"),
    }
