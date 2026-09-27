"""Python face of the `monte_carlo` C++ submodule.

Re-exports the extension's public names so `from quantrisk.monte_carlo import X` works — the
extension only binds them as attributes, which leaves `sys.modules["quantrisk.monte_carlo"]`
unpopulated. No numerics are added here; see `_reexport.py`.
"""

from __future__ import annotations

from ._quantrisk import monte_carlo as __core__
from ._reexport import copy_core_names as _copy

__all__ = list(_copy(__import__("sys").modules[__name__], __core__))

del _copy
