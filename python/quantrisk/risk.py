"""Python face of the `risk` C++ submodule, plus its research-API facade.

Re-exports the extension's public names so `from quantrisk.risk import X` works — the
extension only binds them as attributes, which leaves `sys.modules["quantrisk.risk"]`
unpopulated. RiskEngine is layered on top; it delegates to these
same functions and adds no arithmetic of its own.
no arithmetic of its own.
"""

from __future__ import annotations

from ._quantrisk import risk as __core__
from ._reexport import copy_core_names as _copy
from .api import RiskEngine

__all__ = [*_copy(__import__("sys").modules[__name__], __core__), "RiskEngine"]

del _copy
