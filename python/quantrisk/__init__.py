"""QuantRisk++ — Python research layer.

This package is an orchestration layer. Every number-producing routine lives in
the C++20 core and reaches Python through :mod:`quantrisk._quantrisk`; nothing
here re-implements a formula (docs/architecture.md §2).
"""

from __future__ import annotations

from ._quantrisk import (
    Rng,
    ValidationError,
    build_metadata,
    inverse_normal_cdf,
    normal_cdf,
    normal_pdf,
    stats,
    version,
)

__version__ = version()

__all__ = [
    "Rng",
    "ValidationError",
    "__version__",
    "build_metadata",
    "inverse_normal_cdf",
    "normal_cdf",
    "normal_pdf",
    "stats",
    "version",
]
