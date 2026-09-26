# Phase 3 Report - Monte Carlo Simulation Engine

Date: 2026-09-26 · Platform: Apple clang 21.0.0, arm64, macOS, CMake 4.4.3,
CPython 3.12.14, QuantLib 1.43 (oracle), NumPy 2.5.3.

## 1. Completed

- `quantrisk::gbm`: exact risk-neutral GBM transition for terminal draws and full
  paths, antithetic pairing, and an explicitly separate physical-measure
  generator (`terminal_prices_physical`, where `mu` is price appreciation
  excluding the dividend yield).
- `quantrisk::MonteCarloEngine`: instance-owned stream, European pricing with
  plain / antithetic / control-variate estimators, generic terminal-payoff and
  path-payoff entry points, and per-estimate reporting of price, standard error,
  confidence interval, path count, independent-unit count, seed, sample variance,
  fitted control-variate beta and wall-clock runtime.
- `benchmarks/quantlib/monte_carlo_validation.py` (492 rows),
  `benchmarks/performance/monte_carlo_speed.py`,
  `experiments/monte_carlo_convergence/`, `experiments/variance_reduction/`.
- Bindings (`quantrisk.monte_carlo`, `quantrisk.stochastic`), 19 + 4 new pytest
  modules, 19 new Catch2 cases, model card `docs/model_cards/monte_carlo_gbm.md`.

## 2. Mathematical assumptions

`V0 = e^{-rT} E^Q[payoff]` under GBM with constant `r, q, sigma`; exact terminal
transition means zero discretisation bias for European payoffs; the normal
(CLT) interval is used and its coverage is measured rather than assumed;
antithetic pairs share one `Z` (drift is not negated); control-variate `beta` is
fitted in-sample and therefore optimistic, so the experiments also report
out-of-sample mean squared error over seed ensembles.

## 3. Files changed

Added: `cpp/include/quantrisk/{stochastic/gbm,monte_carlo/engine}.hpp`,
`cpp/src/stochastic/gbm.cpp`, `cpp/src/monte_carlo/engine.cpp`,
`tests/cpp/{test_gbm,test_monte_carlo}.cpp`,
`tests/python/{test_monte_carlo,test_monte_carlo_vs_oracles}.py`,
`benchmarks/quantlib/monte_carlo_validation.py`,
`benchmarks/performance/monte_carlo_speed.py`,
`experiments/{monte_carlo_convergence,variance_reduction}/run.py` + `results/`,
`docs/model_cards/monte_carlo_gbm.md`.
Modified: `CMakeLists.txt`, `bindings/python_bindings.cpp`,
`python/quantrisk/__init__.py`, `python/quantrisk/plotting/__init__.py`
(series-length guard), `docs/limitations.md`, `docs/project_scope.md`, `README.md`.

## 4. Tests executed

```bash
cmake --preset dev && cmake --build --preset dev && ctest --preset dev
uv pip install -e . && pytest -q                      # oracles present
uv run python experiments/monte_carlo_convergence/run.py
uv run python experiments/variance_reduction/run.py
uv run python benchmarks/quantlib/monte_carlo_validation.py
uv run python benchmarks/performance/monte_carlo_speed.py
```

## 5. Exact test results

```text
CTest : 100% tests passed out of 72
pytest: 136 passed, 0 failed, 0 skipped (QuantLib + SciPy installed)
ruff / clang-format: clean; compiler warning-free with -Wall -Wextra -Wpedantic
```

## 6. Numerical validation

**Level 3 - convergence rate** (fitted log-log slope of |MC error| on N,
expected -0.5, `experiments/monte_carlo_convergence/results/summary.json`):

| scenario | fitted slope | standard error | deviations from theory |
|---|---|---|---|
| atm_call | -0.6141 | 0.0888 | 1.28 |
| deep_itm_call | -0.5855 | 0.0963 | 0.89 |
| otm_put | -0.5066 | 0.1184 | 0.06 |

Empirical coverage of nominal 95 % / 99 % intervals over
12 seed x path-count x level combinations:
**12/12** fell inside the exact
Binomial band.

**Level 2 - live oracle** (`benchmarks/quantlib/results/monte_carlo_validation.json`):
z-scores of our estimate against QuantLib's analytic price, pooled over 4 scenarios:

| method | n | mean | std | range | within 2 SE |
|---|---|---|---|---|---|
| antithetic | 160 | -0.023 | 1.014 | -2.04 .. +2.06 | 98.8 % |
| control_variate | 160 | +0.050 | 0.923 | -2.11 .. +1.78 | 98.1 % |
| plain | 160 | +0.031 | 0.930 | -2.40 .. +2.10 | 96.2 % |

QuantLib's own MC engine was **not** usable in this build
(`quantlib_mc_engine_used: false` - every
traits string was rejected); the analytic oracle plus an independent
NumPy/PCG64 simulation carry the comparison, and the artifact states this.

**Level 3 - variance reduction** (realised out-of-sample MSE ratio vs plain
Monte Carlo, 40 seeds x 3 path budgets x 4 scenarios):
antithetic 1.12x - 2.77x, control variate 1.93x - 40.47x.

**Level 1 - exactness identities** (deterministic, no tolerance to hide behind):
control variate on a payoff affine in the control reproduces the analytic price
to ~1e-12 with standard error < 1e-10 and beta = 1; constant payoff returns the
discount factor exactly; antithetic pairs satisfy
`S+ * S- = S^2 exp(2(r-q-sigma^2/2)T)` to 1e-12 relative.

**Performance** (measured, 200,000 paths, 7 repetitions,
single-threaded, terminal-only European):

| implementation | mean seconds | paths / second |
|---|---|---|
| C++ core | 0.004328 | 46,210,785 |
| pure Python loop | 0.034912 | 5,728,661 |
| vectorised NumPy | 0.001816 | 110,122,785 |

Speedup C++ vs pure Python: **8.07x**;
vs NumPy: 0.42x (NumPy is faster in this regime).
The README quotes only these measured figures, with the scope caveat recorded in
the artifact: for one-normal-per-path work vectorised NumPy wins, and the C++
core's advantage is per-path state and memory layout, which Phase 4 exercises.

## 7. Remaining limitations

See `docs/limitations.md` (Phase 3 section): single-threaded, no quasi-Monte
Carlo / Brownian bridge / stratification, `O(paths x steps)` path memory,
normal-approximation intervals, in-sample `beta` optimism, and no QuantLib MC
engine cross-check available in this build.

## 8. Technical debt

- `price_path_payoff` allocates the full path matrix; Phase 4's Asian/barrier
  work should stream paths (fixed buffer) to allow larger `paths x steps`.
- No batched multi-option pricing from one simulation (Phase 7's stress engine
  will want it).
- The pure-Python baseline uses `random.gauss`, so its stream differs from the
  C++ engine's; the comparison is cost-per-path, not bit equality (documented).
- `Rng::standard_normal_vector` still allocates per call.

## 9. Gate

Convergence experiment (slope within 1.3 SE of -0.5), variance reduction
experiment (measured out-of-sample MSE gains), confidence-interval validation
(12/12 inside the exact binomial band), reproducibility proof (bit-identical
estimates for a fixed seed, asserted in both C++ and Python) and the performance
benchmark are all present with artifacts. **Status: READY for Phase 4.**
