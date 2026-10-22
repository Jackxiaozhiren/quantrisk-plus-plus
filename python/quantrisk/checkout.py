"""The one way this repository finds the checkout it is running inside.

Two surfaces need it and they start from different places. A verification instrument reads
repository files — the C++ source it differentiates, the artifacts it plants into — so it starts
from its own file. A published study writes repository files, so it starts from the working tree
and lets the caller name a different root with `--out`. Both questions are the same walk, and the
answer is either a directory that holds the markers or a refusal: a root derived from `__file__`
depth is correct in `scripts/` and silently wrong two levels deeper, which points every plant and
every study at a path that does not exist and prints that as a clean result.

An installed wheel is the other case worth naming. No ancestor of site-packages is a checkout, so
this raises rather than guessing, and nothing in the shipped surface may fall back to writing beside
itself.
"""

from __future__ import annotations

from pathlib import Path

CHECKOUT_MARKERS = ("pyproject.toml", ".git")


def checkout_root(start: Path | None = None) -> Path:
    """The nearest ancestor of `start` (the working directory by default) that is this checkout.

    Raises with the directory it searched when there is none, because the callers of this function
    are about to read or write files and a guessed root is how a check passes on nothing.
    """
    here = (Path.cwd() if start is None else Path(start)).resolve()
    for candidate in (here, *here.parents):
        if all((candidate / marker).exists() for marker in CHECKOUT_MARKERS):
            return candidate
    raise RuntimeError(
        f"{here} is not inside a QuantRisk++ checkout: no ancestor holds "
        f"{' and '.join(CHECKOUT_MARKERS)}; refusing to guess at a root"
    )
