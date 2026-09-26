# QuantRisk++ — Ecosystem Research (Phase 0)

Date: 2026-09-25
Status: research only — no implementation decisions beyond scope freeze.
Sources checked: official docs/repos via Context7 + web search (see §6).

## 1. Decision summary

| Library | Role in QuantRisk++ | Verdict |
|---|---|---|
| QuantLib (C++, + QuantLib-SWIG Python) | correctness oracle / external benchmark only | NEVER call it as our pricing engine; compare against it with live runs, never hard-coded outputs |
| PyPortfolioOpt (+ cvxpy, scikit-learn) | correctness oracle for portfolio optimization | We implement sample/EWMA/shrinkage covariance, min-variance, max-Sharpe, CVaR (Rockafellar–Uryasev), risk parity ourselves; cross-check weights/objectives vs PyPortfolioOpt/cvxpy |
| pybind11 | infrastructure: C++ ↔ Python bindings | Adopt; header-only, `pybind11_add_module`, CMake 3.15+ |
| scikit-build-core | infrastructure: Python packaging via CMake | Adopt as `build-backend` in `pyproject.toml`; CMake builds the extension |
| Catch2 v3 | infrastructure: C++ testing, CTest integration | Adopt; `FetchContent` + `Catch2::Catch2WithMain` + `catch_discover_tests` |
| Eigen | infrastructure: C++ linear algebra | Adopt (header-only); do NOT duplicate dense linear algebra by hand |
| SciPy / NumPy / statsmodels | oracle + research tooling (Python) | SciPy stats/optimize only as reference; distributions and solvers in core are our own unless spec says otherwise |
| SEC EDGAR / FRED / CFTC public data | optional data layer (Phase 8) | Core algorithms must never depend on network; CI fully offline with fixtures |

Core rule (from PROJECT_SPEC.md §2.2, frozen here):
QuantLib, PyPortfolioOpt, SciPy, cvxpy are **benchmark/validation oracles**.
They must not substitute our implementations of Black-Scholes, binomial trees,
Monte Carlo/GBM, Greeks, variance reduction, VaR/ES, backtests, covariance
estimation, mean-variance/CVaR optimization, or the stress framework.

## 2. QuantLib

- What: free/open-source C++ library for quantitative finance (modeling, trading, risk).
- Python access: QuantLib-SWIG bindings (separate package).
- What we use it for (Phase 2+): independent repricing of European/American options;
  outputs `(model, our_price, quantlib_price, abs_err, rel_err)` generated at run time.
- What we do NOT do: `import QuantLib; QuantLib.price(...)` presented as our engine;
  hard-coding QuantLib numbers as expected values; hiding QuantLib version/config.
- Cost: open source, $0. Heavy to build; benchmark scripts must record QuantLib
  version and run live so results are reproducible, not copy-pasted.
- References checked: `lballabio/quantlib` repo (Examples/EquityOption, exercise types),
  `lballabio/quantlib-swig` bindings.

## 3. PyPortfolioOpt

- What: Python portfolio-optimization library built on cvxpy; covers
  `EfficientFrontier` (min volatility, max Sharpe, efficient risk/return),
  `EfficientSemivariance`, `EfficientCVaR` (Rockafellar–Uryasev), HRP, Black-Litterman,
  expected-return and risk-model helpers (incl. Ledoit-Wolf shrinkage).
- What we use it for (Phase 6): oracle for weights, expected return, volatility,
  Sharpe, CVaR, and constraint residuals on identical inputs.
- What we implement ourselves: sample / EWMA / shrinkage covariance estimators,
  min-variance with target-return constraint, max-Sharpe formulation (documented),
  long-only constraints, CVaR optimization, equal-risk-contribution risk parity,
  singular/near-collinear robustness tests.
- Caution from its own docs: MVO concentrates weights; min-volatility often beats
  max-Sharpe out of sample due to return-estimation error. We document this; we do
  not present in-sample optima as tradable performance.
- Cost: open source ($0), depends on open-source solvers via cvxpy. No paid solver.

## 4. pybind11

- What: header-only C++11 library exposing C++ types in Python and vice versa.
- Why chosen over alternatives (e.g. nanobind): maturity, docs coverage, CMake helper
  (`pybind11_add_module` handles Python flags/extensions/LTO), stable ABI story for a
  teaching/research codebase. Revisit only with measured evidence.
- Minimal pattern (from official `docs/compiling.md`, verified 2026-09-25):
  `cmake_minimum_required(VERSION 3.15...4.2)`, `find_package(pybind11 REQUIRED)`,
  `pybind11_add_module(example example.cpp)`.
- Phase 1 smoke test (frozen): `import quantrisk; quantrisk.version();
  quantrisk.normal_cdf(0.0)` proving C++ → pybind11 → Python works.

## 5. scikit-build-core

- What: PEP 517 build backend that drives CMake to build extension modules from
  `pyproject.toml` static config.
- Minimal pattern (from official README, verified 2026-09-25):
  `[build-system] requires = ["scikit-build-core"]; build-backend = "scikit_build_core.build"`,
  with `CMakeLists.txt` using `find_package(Python COMPONENTS Interpreter Development.Module)`
  and installing the extension into the package directory.
- Why: single `uv sync / pip install` path builds C++ core + Python package;
  keeps CMake as the one true build definition (also used for Catch2/CTest).
- Constraint: no paid build services; local + GitHub Actions free tier only.

## 6. Catch2

- What: C++-native test framework (v3 line, C++14+; supports C++20).
- Integration (from official `docs/cmake-integration.md`, verified 2026-09-25):
  `FetchContent_Declare(Catch2 GIT_REPOSITORY https://github.com/catchorg/Catch2.git
  GIT_TAG v3.8.1)`, `FetchContent_MakeAvailable(Catch2)`,
  `target_link_libraries(tests PRIVATE Catch2::Catch2WithMain)`,
  `catch_discover_tests(tests)` with `CMAKE_MODULE_PATH` extended to `extras/`.
- Policy: prefer pinned `GIT_TAG` (reproducible); `find_package` fallback allowed
  only if documented. C++ tests run under CTest; Python tests under pytest.
  No network in tests beyond the pinned fetch at configure time.

## 7. Eigen (linear algebra — do not reinvent)

- Header-only C++ linear algebra; owns all dense matrix/vector work in `cpp/` core
  (covariance, decompositions, solvers). Hand-rolled linear algebra is a
  correctness risk and is banned for production paths; small utilities may exist
  only where they aid teaching AND are validated against Eigen.
- To be pinned in Phase 1 (system package or FetchContent — decision deferred to
  Phase 1, recorded here as open item, not as a claim).

## 8. What we explicitly do NOT build on

- No Bloomberg/Refinitiv/WRDS/paid Polygon, no paid cloud/database/API,
  no proprietary solvers. Data layer (Phase 8) uses SEC EDGAR (no key),
  FRED/ALFRED (env-var key, fixtures fallback), CFTC public files — all optional,
  cached with source/timestamp/identifier/SHA256, never committed at scale.

## 9. Sources consulted (2026-09-25)

1. pybind11 `docs/compiling.md` via Context7 (`/pybind/pybind11`).
2. QuantLib repo (`/lballabio/quantlib`, `/lballabio/quantlib-swig`) via Context7.
3. scikit-build-core README + docs via Context7 (`/scikit-build/scikit-build-core`).
4. Catch2 `docs/cmake-integration.md` + CMake `FetchContent` docs via web search.
5. PyPortfolioOpt `MeanVariance`, `UserGuide`, `GeneralEfficientFrontier` docs via web search.
6. PROJECT_SPEC.md (this repo) as normative constraint.
