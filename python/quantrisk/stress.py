"""Python face of the `stress` C++ submodule, plus its research-API facade.

Re-exports the extension's public names so `from quantrisk.stress import X` works — the
extension only binds them as attributes, which leaves `sys.modules["quantrisk.stress"]`
unpopulated. ScenarioEngine is layered on top; it delegates to these
same functions and adds no arithmetic of its own.
no arithmetic of its own.
"""

from __future__ import annotations

from ._quantrisk import stress as __core__
from ._reexport import copy_core_names as _copy
from .api import ScenarioEngine

__all__ = [*_copy(__import__("sys").modules[__name__], __core__), "ScenarioEngine"]

del _copy
