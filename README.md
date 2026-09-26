# QuantRisk++

> A Reproducible C++/Python Engine for Stochastic Pricing, Monte Carlo Simulation,
> Portfolio Risk, Optimization and Stress Testing.

**Current status: Phase 1 — Engineering Foundation (v0.1.0).**
Only the numerical skeleton exists: input validation, RNG discipline, and normal
distribution helpers in a C++20 core with Python bindings. No pricing, simulation,
risk, or optimization models are implemented yet. See `docs/` for the frozen
research scope, mathematical specification, and validation protocol.

## 30-second example

```python
import quantrisk

quantrisk.version()        # '0.1.0'
quantrisk.normal_cdf(0.0)  # 0.5

rng = quantrisk.Rng(seed=42)
rng.uniform01()            # reproducible in [0, 1)
rng.standard_normal()      # reproducible N(0, 1)
```

## Install (developers, $0)

```bash
uv sync                      # create .venv (Python 3.12) + install deps
uv pip install -e .          # build C++ core + bindings (editable)
uv run pytest                # Python tests

cmake --preset dev           # configure C++ (Release-with-debug)
cmake --build --preset dev   # build core + tests
ctest --preset dev           # C++ tests
```

## Validation

Phase 1 validates `normal_cdf`/`normal_pdf` against closed-form identities
(Level 1) and SciPy (Level 2, live oracle), RNG reproducibility across C++/Python,
and input-validation errors. Full protocol: `docs/validation_protocol.md`.

## Limitations

See `docs/project_scope.md` §9–§10. Everything beyond Phase 1 (Black-Scholes,
Monte Carlo, VaR/ES, optimizers, stress, data) is specified but **not built**.
