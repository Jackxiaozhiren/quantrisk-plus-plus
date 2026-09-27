"""QuantRisk++ — Python research layer.

This package is an orchestration layer. Every number-producing routine lives in
the C++20 core and reaches Python through :mod:`quantrisk._quantrisk`; nothing
here re-implements a formula (docs/architecture.md §2).

`quantrisk.data` is deliberately *not* imported here. It is an optional adapter over
network sources, and pulling it in at package import would make every numerical user of
this library carry that surface — and its failure modes — whether they asked to or not.
"""

from __future__ import annotations

# Importing these registers them as ``quantrisk.<name>`` in sys.modules, which is what
# makes ``from quantrisk.risk import RiskEngine`` resolvable at all: the extension binds
# its submodules only as attributes, so without these files the import machinery finds no
# module to import from. They re-export the extension's names in turn, so the existing
# ``quantrisk.risk.historical_var(...)`` form keeps working unchanged.
from . import monte_carlo, portfolio, pricing, risk, special, stats, stochastic, stress
from ._quantrisk import (
    Rng,
    ValidationError,
    build_metadata,
    inverse_normal_cdf,
    normal_cdf,
    normal_pdf,
    version,
)
from .api import (
    BlackScholes,
    MonteCarloEngine,
    PortfolioOptimizer,
    RiskEngine,
    ScenarioEngine,
)

__version__ = version()

__all__ = [
    "BlackScholes",
    "MonteCarloEngine",
    "PortfolioOptimizer",
    "RiskEngine",
    "Rng",
    "ScenarioEngine",
    "ValidationError",
    "__version__",
    "build_metadata",
    "inverse_normal_cdf",
    "monte_carlo",
    "normal_cdf",
    "normal_pdf",
    "portfolio",
    "pricing",
    "risk",
    "special",
    "stats",
    "stochastic",
    "stress",
    "version",
]
