"""Re-export helper for the Python faces of the C++ submodules.

`_quantrisk` registers its submodules as attributes of the extension module, which makes
`quantrisk.risk.historical_var(...)` work but leaves `sys.modules["quantrisk.risk"]`
unpopulated — so `from quantrisk.risk import RiskEngine` raises `ModuleNotFoundError` no
matter what attributes exist. PROJECT_SPEC.md §Phase 9 asks for that import form, so each
submodule gets a real Python file that re-exports the core names and carries the facades.

This helper is the only machinery those files need. It copies public names across rather
than wrapping them, because a wrapper would be a second surface to keep in sync and would
add nothing: the rule for this whole layer is that Python orchestrates and C++ computes.

The `__core__` attribute each module exposes names which object the names came from, so a
reader (or a test) can confirm a facade delegated rather than reimplemented.
"""

from __future__ import annotations

import types

_SKIP = {"__doc__", "__name__", "__package__", "__loader__", "__spec__", "__path__"}


def copy_core_names(target: types.ModuleType, core: types.ModuleType) -> tuple[str, ...]:
    """Bind every public name of `core` into `target`, returning what was copied."""
    copied: list[str] = []
    for name in dir(core):
        if name.startswith("_") or name in _SKIP:
            continue
        setattr(target, name, getattr(core, name))
        copied.append(name)
    return tuple(copied)
