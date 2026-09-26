# QuantRisk++

> A Reproducible C++/Python Engine for Stochastic Pricing, Monte Carlo Simulation,
> Portfolio Risk, Optimization and Stress Testing.

**Current status: Phase 3 — Monte Carlo Simulation Engine (v0.1.0).**
Implemented and validated: a C++20 numerical core (RNG discipline, statistics,
normal distribution), Black-Scholes-Merton pricing with continuous dividends,
analytic and finite-difference Greeks, a Cox-Ross-Rubinstein lattice for
European and American exercise, and a Monte Carlo framework with antithetic and
control-variate estimators whose convergence rate and interval coverage are
measured rather than asserted. Path-dependent pricing, Heston, risk,
optimisation, stress and data layers are specified in `docs/` but **not built
yet**.

Numbers quoted here come from committed artifacts, regenerate them with the
commands in [Validation](#validation):

| Claim | Value | Artifact |
|---|---|---|
| BS price vs live QuantLib (2 464 comparisons) | worst abs 1.49e-13, rel 3.46e-11 | `benchmarks/quantlib/results/pricing_vs_quantlib.json` |
| Greeks vs QuantLib (delta/gamma/vega/theta/rho) | worst abs 5.12e-13 | same file |
| Put-call parity residual | 8.0e-15 on notionals <= 200 | `experiments/pricing_validation/results/summary.json` |
| CRR lattice order | fitted slopes -0.99 +/- 0.004 vs theory -1 | same file, `crr_convergence_slope` |
| Test suite | 72 C++ (CTest) + 136 Python (pytest) | `docs/phase_reports/phase-03-monte-carlo.md` |
| MC error decay (fitted log-log slope, theory -0.5) | -0.614 ± 0.089, -0.585 ± 0.096, -0.507 ± 0.118 | `experiments/monte_carlo_convergence/results/summary.json` |
| 95 % / 99 % interval coverage vs exact Binomial band | 12/12 combinations inside the band | same artifact |
| MC z-scores vs QuantLib analytic (pooled, 3 methods) | mean ≤ 0.05, std 0.92-1.01, ≥ 96 % within ±2 SE | `benchmarks/quantlib/results/monte_carlo_validation.json` |
| C++ vs pure-Python Monte Carlo (measured, terminal-only) | 8.07x (46,210,785 vs 5,728,661 paths/s) | `benchmarks/performance/results/monte_carlo_speed.json` |

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

Three levels, defined in `docs/validation_protocol.md` and executed per phase:

* **Level 1 - analytical**: parity identities, degenerate limits, `u*d == 1`,
  the no-early-exercise theorem, analytic Greeks vs central differences with a
  Richardson error estimate instead of a tuned tolerance.
* **Level 2 - independent oracles, run live**: QuantLib 1.43
  (`benchmarks/quantlib/pricing_validation.py`) and SciPy's normal
  distribution/quantile. No oracle output is ever pasted into `tests/`.
* **Level 3 - statistical**: lattice convergence fitted on log-log axes with
  standard errors.

```bash
uv run python benchmarks/quantlib/pricing_validation.py   # needs the oracles extra
uv run python experiments/pricing_validation/run.py
```

## Limitations

See `docs/project_scope.md` §9–§10. Everything beyond Phase 1 (Black-Scholes,
Monte Carlo, VaR/ES, optimizers, stress, data) is specified but **not built**.
