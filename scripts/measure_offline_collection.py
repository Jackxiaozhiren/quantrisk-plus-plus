#!/usr/bin/env python3
"""Measure what the suite collects with the validation oracles absent.

`docs/limitations.md` #63 says the Python test count is two numbers and that neither may be
derived from the other, which left the oracle-free reading to the CI lane alone: a phase adding
tests had to push, wait, and read the runner's failure to learn its own figure. This script is a
second producer -- it makes the oracle packages unimportable in a child interpreter and collects
there.

Two things it has to get right, both asserted by the guard that calls it rather than assumed:

* the blocked set is derived from `pyproject.toml` -- the `oracles` extra minus what the `dev`
  group also installs, because the CI lane runs a plain `uv sync`, which has scipy and not
  QuantLib; and
* the gated modules must skip the way they do on the runner, not error. Setting
  `sys.modules[name] = None` makes an import fail as an absent distribution fails, which is what
  `pytest.importorskip` catches.

Usage: uv run --frozen python scripts/measure_offline_collection.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"

# Distribution name -> top-level import name. Only the renames need stating.
IMPORT_NAMES = {
    "quantlib": "QuantLib",
    "pypfopt": "pypfopt",
    "pyportfolioopt": "pypfopt",
    "scikit-learn": "sklearn",
    "cvxpy": "cvxpy",
    "statsmodels": "statsmodels",
    "scipy": "scipy",
}


def _names(block: str) -> list[str]:
    """Package specifiers from a `pyproject.toml` array, lowercased and stripped of constraints."""
    found = re.findall(r'"([A-Za-z0-9_.\-]+)\s*(?:[><=!~].*?)?"', block)
    return [name.lower() for name in found]


def blocked_imports() -> list[str]:
    """What `uv sync` does not install: the `oracles` extra, less the `dev` group's own packages."""
    text = PYPROJECT.read_text(encoding="utf-8")
    oracles = re.search(r"oracles = \[(.*?)\]", text, re.S)
    dev = re.search(r"^\[dependency-groups\]\s*\n\s*dev = \[(.*?)\]", text, re.S | re.M)
    assert oracles and dev, "pyproject.toml no longer carries both an oracles extra and a dev group"
    oracle_names = _names(oracles.group(1))
    dev_names = set(_names(dev.group(1)))
    missing = [name for name in oracle_names if name not in dev_names]
    imports = sorted({IMPORT_NAMES[name] for name in missing})
    assert imports, "the probe would block nothing, so its count would be the online one"
    return imports


CHILD = """
import sys
for name in {blocked!r}:
    sys.modules[name] = None
import pytest
raise SystemExit(
    pytest.main(["--collect-only", "-q", "-p", "no:cacheprovider", "tests/python"])
)
"""


def measure() -> dict[str, object]:
    blocked = blocked_imports()
    run = subprocess.run(
        [sys.executable, "-c", CHILD.format(blocked=blocked)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = run.stdout + run.stderr
    collected = re.search(r"^(\d+) tests? collected", output, flags=re.M)
    skips = len(re.findall(r"^SKIPPED \[1\]", output, flags=re.M))
    errors = len(re.findall(r"^ERROR tests/", output, flags=re.M))
    return {
        "blocked_imports": blocked,
        "collected": int(collected.group(1)) if collected else None,
        "module_skips": skips,
        "collection_errors": errors,
        "exit_code": run.returncode,
        "tail": output[-400:],
    }


def main() -> int:
    result = measure()
    print(json.dumps(result, indent=2))
    return 0 if result["collected"] is not None and result["collection_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
