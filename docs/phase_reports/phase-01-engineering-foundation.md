# Phase 1 Report — Engineering Foundation

Date: 2026-09-26 · Revision under test: `1790053d55d1` + this phase's changes
Platform: Apple clang 21.0.0 (clang-2100.3.34.2), arm64, macOS, CMake 4.4.3,
uv 0.11.7, CPython 3.12.14.

## 1. Completed

- Single CMake definition for the C++20 static core, the pybind11 module, the
  reference-value tool and the Catch2/CTest suite (`CMakeLists.txt`,
  `CMakePresets.json` with `dev` / `release` / `ci` presets).
- `scikit-build-core` packaging so `uv pip install -e .` builds the same CMake
  tree (`pyproject.toml`); `uv sync` provisions Python 3.12 plus dev tools
  (pytest, ruff, mypy, cmake, ninja, clang-format, scipy, matplotlib).
- Pinned third-party C++ dependencies fetched at configure time only:
  Catch2 `v3.8.1`, pybind11 `v2.13.6` (with the venv-installed pybind11 taking
  precedence when present).
- Minimal C++ core in `namespace quantrisk`:
  - `core/types.hpp` — `Real` (= `double`), `Time`, `Rate`, `Volatility`,
    `Money`, `Count`, `Seed`.
  - `core/constants.hpp` — `kPi`, `kSqrtTwo`, `kInvSqrtTwoPi`,
    `kMachineEpsilon`, `kAnalyticTolerance = 1e-12`.
  - `core/validation.hpp` — `ValidationError` plus scalar domain checks and a
    `ValidationIssues` accumulator used for multi-field records.
  - `core/rng.hpp` — `Rng`: instance-owned `std::mt19937_64`, fixed/configurable
    seed, `uniform01`, `standard_normal` (Marsaglia polar with cached partner),
    unbiased `uniform_index` by rejection over the 2^64 range. No global state.
  - `core/statistics.hpp` — Neumaier compensated sum, mean, unbiased variance,
    standard error, linear-interpolated quantile, tail mean, autocorrelation.
  - `math/normal.hpp` — `normal_pdf`, `normal_cdf` (`0.5·erfc(-x/√2)`),
    `inverse_normal_cdf` (Acklam rational + one Halley step, lower-half only).
  - `core/version.hpp` — `version()` and `build_metadata()` (compiler, arch, OS,
    build type, C++ standard, flags, git commit) captured at configure time.
- Frozen Phase 1 smoke surface: `quantrisk.version()`, `quantrisk.normal_cdf(0.0)`.
- CI: `.github/workflows/ci.yml` (lint job: ruff + clang-format + mypy;
  build job: configure → build → ctest → install → pytest, offline).
- `.clang-format` applied to every C++ file; `.clang-tidy` configuration added.

## 2. Mathematical assumptions

- All core numerics in `double`; `float` is excluded from numerical paths.
- `mt19937_64` is the C++ standard engine, seeded by a single `uint64` value.
  Normal variates come from our own Marsaglia polar implementation, not
  `std::normal_distribution`, because the latter's output is implementation
  defined (libstdc++ and libc++ differ). Bit-identical replay therefore holds
  for a fixed `(seed, N, code version)` on a given platform, not across
  compilers' `libm` differences in `log`/`sqrt`/`erfc`.
- `normal_cdf` is defined as `0.5·erfc(-x/√2)`, which is the same mathematical
  object as `(1+erf(x/√2))/2` but keeps relative accuracy in the left tail.
- `inverse_normal_cdf` is Acklam's rational approximation refined once by
  Halley. Only the lower half of the distribution is evaluated directly and the
  upper half is obtained from `Q(p) = -Q(1-p)`; see the next section for why.
- Statistics estimators are the textbook ones: `mean`, unbiased
  `sample_variance` (`/(n-1)`), and NumPy's `method="linear"` quantile
  convention (`h = p(n-1)`, linear interpolation between order statistics).
  `autocorrelation` uses the Wallis ("biased") denominator, which is the
  normalisation Christoffersen's test statistic is stated with in Phase 5.

## 3. Files changed

Created: `CMakeLists.txt`, `CMakePresets.json`, `pyproject.toml`,
`cmake/quantrisk_build_config.hpp.in`, `.clang-tidy`,
`.github/workflows/ci.yml`,
`cpp/include/quantrisk/core/{types,constants,validation,rng,statistics,version}.hpp`,
`cpp/include/quantrisk/math/normal.hpp`,
`cpp/src/core/{rng,statistics,version}.cpp`, `cpp/src/math/normal.cpp`,
`cpp/src/tools/dump_reference.cpp`, `bindings/python_bindings.cpp`,
`python/quantrisk/__init__.py`,
`tests/cpp/{test_validation,test_rng,test_statistics,test_normal,test_build_info}.cpp`,
`tests/python/{conftest.py,test_smoke.py,test_validation_errors.py,`
`test_normal_vs_scipy.py,test_rng_contract.py,test_cpp_python_consistency.py}`.
Modified: `README.md`, `docs/project_scope.md`, this report.

## 4. Tests executed

```bash
cmake --preset dev && cmake --build --preset dev && ctest --preset dev   # 31 tests
uv sync && uv pip install -e . && python -m pytest -q                    # 41 tests
uv run ruff check . && uv run ruff format --check .
find cpp bindings tests/cpp -name '*.cpp' -o -name '*.hpp' |
  xargs clang-format --dry-run --Werror
```

## 5. Exact test results

```text
CTest   : 100% tests passed out of 31   (Total test time 0.42 s)
pytest  : 41 passed in 0.43 s
ruff    : All checks passed / 7 files already formatted
clang-format: no diagnostics (tree is formatted)
compiler: no warnings with -Wall -Wextra -Wpedantic
```

## 6. Numerical validation

Level 1 (analytical / identities / limits), in `tests/cpp` and `tests/python`:

- `normal_cdf(0) == 0.5` exactly; reflection `N(x) + N(-x) == 1`; monotonicity
  over `x ∈ [-10, 10]`; closed-form anchors `N(1)`, `N(1.959963984540054)`,
  `N(6)`; `phi(0) = 1/√(2π)`, `phi` even.
- `inverse_normal_cdf` published quantiles at 0.5 / 0.95 / 0.975 / 0.99 / 0.01;
  round-trip `N(Q(p)) ≈ p` and antisymmetry over dyadic probabilities
  `p = 2^-k, k = 2..20` (dyadic so that `1-p` is exact — decimal literals are
  not, and the first version of that test measured its own input rounding).
- Statistics: hand-computed mean/variance (`32/7` on the classic 8-observation
  sample), quantile interpolation table, tail means, `ρ1 = -0.75` on an
  alternating series, and compensated summation on
  `[1e16, 1, -1e16]` where naive addition returns 0 instead of 1.
- RNG: identical seed ⇒ identical stream, engines independent, `uniform01 ∈
  [0,1)`, `uniform_index` coverage, moment checks inside 5 standard errors.

Level 2 (independent open-source oracle, live):

- `tests/python/test_normal_vs_scipy.py` compares `normal_cdf`, `normal_pdf`,
  `inverse_normal_cdf` and the erfc identity against SciPy on dense grids
  (`x ∈ [-8, 8]` 1601 points; `p ∈ logspace(-12, -3) ∪ linspace(1e-3, 1-1e-3)`),
  asserting max absolute error `< 1e-12`. SciPy is imported by the test only,
  never by the library, and no oracle value is pasted into the code.

Level 3 (statistical):

- Kolmogorov–Smirnov of 50 000 `standard_normal()` draws against `N(0,1)`
  through the Python boundary (p-value threshold 1e-4), and an 8-bin chi-square
  test on 80 000 `uniform01()` draws.

Python/C++ consistency:

- `cpp/src/tools/dump_reference.cpp` (compiled C++, no Python) prints 256
  seed-42 normals, 64 uniforms, 2 000 `uniform_index(97)` draws, CDF/PDF over
  81 points, 999 quantiles and four statistics.
  `tests/python/test_cpp_python_consistency.py` requires the pybind11 results to
  match those values **exactly** (`rel=0, abs=0`), so the binding layer cannot
  quietly re-derive or reinterpret anything.

## 7. Remaining limitations

- `Eigen` is not linked yet: the Phase 1 core needs no dense linear algebra, so
  adding it now would be an unused dependency. It arrives with Phase 6
  (covariance and optimizers), which is also where `docs/architecture.md` §4
  intended it. Recorded in `docs/limitations.md`.
- `mypy` runs as a warning-only CI step in Phase 1 because the package exposes
  one untyped compiled extension module; typed facades arrive in Phase 9.
- CI covers `ubuntu-latest` only. The development platform (macOS arm64) is
  exercised locally with the same presets; a macOS CI job was left out to stay
  inside the free quota with margin for the later, heavier phases.
- No `docs/model_cards/` yet: there is no model to describe, only infrastructure.

## 8. Technical debt

- `inverse_normal_cdf` refinement is skipped when `exp(x²/2)` overflows
  (`p < ~1e-315`); the returned value is then the unrefined rational. Relevant
  only far below any risk or pricing confidence level.
- `quantile_linear` requires caller-sorted input for the `_sorted` variants; a
  mistake here is silent. Phase 5's VaR/ES wrappers must own the sort and be
  tested for it.
- `Rng::standard_normal_vector` allocates per call; the Monte Carlo engine will
  need a fill-into-existing-buffer variant to avoid per-path allocation
  (Phase 3).
- The Catch2/pybind11 fetch happens on every fresh build directory; CI caches
  `_deps`, but there is no vendored fallback if the network is unavailable at
  configure time.

## 9. Gate evidence

The Phase 1 gate (`clean clone → install → build → import → test`) is verified
in `docs/phase_reports/phase-01-clean-clone-run.md`, which records the commands
and output of a fresh clone built in a temporary directory.

**Status: READY for Phase 2.**
