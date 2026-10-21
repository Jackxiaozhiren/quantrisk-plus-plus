"""The verification instruments: the plants, the harness that fires them, and the derivation.

These are load-bearing claims rather than mere code — `docs/interview_defense.md` quotes what the
sweep rejects — so they live in the installable package, importable and type-checked like the rest
of the surface. The plant list is a separate module from the interpreter on purpose: finding 94
records that a plant anchoring on a line of the file that holds the list finds that line twice, and
the case is then refused before it runs.
"""

from __future__ import annotations

from pathlib import Path

_CHECKOUT_MARKERS = ("pyproject.toml", ".git")


def repo_root(from_file: str | Path) -> Path:
    """The checkout a verification instrument must run inside, found by marker not by depth.

    These instruments read repository files — the C++ source they differentiate, the artifacts they
    plant into — and each of them has already moved once. A root derived from `__file__` depth is
    correct in `scripts/` and silently wrong two levels deeper, which points every plant and every
    market at a path that does not exist and prints that as a clean result. An installed wheel is
    the other case worth naming: no ancestor of it is a checkout, so this raises rather than
    guessing.
    """
    here = Path(from_file).resolve()
    for candidate in here.parents:
        if all((candidate / marker).exists() for marker in _CHECKOUT_MARKERS):
            return candidate
    raise RuntimeError(
        f"{here} is not inside a QuantRisk++ checkout: no ancestor holds "
        f"{' and '.join(_CHECKOUT_MARKERS)}; these instruments read repository source and refuse "
        "to guess at it"
    )
