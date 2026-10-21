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

## 10. Architecture donors — the V2 refactor survey (2026-10-21)

Status: research feeding `REFACTOR_PROMPT.md` §6, recorded **before** that prompt's §9 approval gate, so
its verdicts may amend §5's decisions and after the gate they may not. §1–§8 answered "what do we build
on?" — oracles, build tooling, a test framework. This section answers a different question, which §1–§8
never asked: **whose organisation should this repository copy?** It is about layouts, registries,
invocation conventions and provenance schemas, and it deliberately takes no implementation: §2.2 of
`PROJECT_SPEC.md` is a standing law, so nothing below is a licence to port code.

Method, stated because a survey that cites nothing is a list of impressions. Each candidate was read in
its own repository at a named ref, and every mechanism below is cited to the exact file that carries it —
each URL was opened and its content read, not constructed from a title. Verdicts are per pattern, not per
project: a project can be a donor on one axis and negative evidence on another.

| Candidate | Class | What it demonstrated, in one line | Verdict |
|---|---|---|---|
| `nautechsystems/nautilus_trader` (develop) | event-driven backtesting / trading platform | a registry that *refuses* to capture a type it cannot later decode, and a verifier with distinct exit codes that is tested by corrupting its own input | adopt the framing; adopt "falsify the verifier" |
| `kedro-org/kedro` (main) | research-workflow framework | a project binds its pipeline registry by convention name, discovery raises by default, and its architecture boundaries are declarative config | adopt: convention + fail-loud discovery + declarative boundaries |
| `microsoft/qlib` (main) | AI-oriented quant platform | a run records `sys.argv` verbatim, and dirty state as `git diff` text rather than as a file list | adopt the argv recording; reject the diff-as-artifact for this lane |
| `mlflow/mlflow` (master) | ML lifecycle | repo tooling is a uv workspace of real packages with their own entry points and tests; the workflow YAML is validated against a pinned schema | adopt the shape of `tools/`; adopt "guard the CI file" |
| `stefan-jansen/zipline-reloaded` (main) | event-driven backtesting | one `__main__` object serves both the console script and `python -m`, so the two spellings cannot drift | adopt |
| `treeverse/dvc` (main) | research pipeline / data versioning | the command line is the first field of a stage's lock record and is asserted on both the definition and the lock path | adopt the ordering principle |
| `dcajasn/Riskfolio-Lib` (master) | risk-measurement library | a CI job named `linters` installs requirements and runs no lint; its test step is commented out; no type checker appears in any config | **reject — kept as negative evidence** |

### Patterns adopted, and what each changes here

- **The command is derived from the live invocation, never typed.** kedro's session records
  `"command_path": " ".join(["kedro"] + sys.argv[1:])`
  (`kedro/framework/session/session.py`), qlib's recorder logs `" ".join(sys.argv)`
  (`qlib/workflow/recorder.py`), and DVC puts `cmd` first in a stage's lock record and requires it on both
  the definition and the lock (`dvc/stage/serialize.py`). Read against the census in
  `tools/refactor_ceilings.json` — `commands_unrunnable_from_the_root`, whose `measured_at_baseline` is the
  collector's count over every `evidence/manifest.json` entry — the conclusion is sharper than "use a
  registry": a registry that *templates* the command would erase the arguments that make a study
  reproducible — the `--paths 200000` in one recorded string is exactly such a case. So **D4 is amended
  (D4′)**: the registry owns the canonical *prefix* (`uv run python -m <module>`) and the producer appends
  the argv it actually received; neither half is typed by a human, and the guard of §13 L4 dry-resolves the
  prefix and refuses a suffix that the entry does not declare.
- **One `__main__` object behind both spellings.** zipline's console script is
  `zipline = 'zipline.__main__:main'` (`pyproject.toml`) and the same `main` lives in `src/zipline/__main__.py`,
  so the installed command and `python -m zipline` cannot disagree. That is the shape D1's
  "`run(argv) -> dict` core + thin `__main__`" needs to stay honest, and it is what makes D6's `run`
  subcommand and the module invocation the same code path rather than two.
- **Registry membership is what makes an artifact verifiable.** nautilus's capture registry refuses
  out-of-allow-list types because silent capture would produce entries the verifier cannot decode
  (`crates/event_store/src/capture/registry.rs`). This reframes the registry from "a list of things that
  can run" to "the set of things whose output can be re-derived", which is the argument QuantRisk++ is
  actually making — and it is why the registry must validate its own entries against a declared key set
  (kedro's settings validator does exactly that, `kedro/framework/project/__init__.py`) rather than accept
  arbitrary attributes. **D3 is amended (D3′)**: an entry with an unknown key, an unresolvable module path,
  or an artifact path outside the declared roots is a *build failure*, not a warning.
- **Boundaries as one declarative block.** kedro states its layering in `[tool.importlinter.contracts]`
  (`pyproject.toml`) with an explicit `ignore_imports` list. The refactor creates exactly three boundaries —
  `quantrisk` may import nothing from `tools` or `experiments`' scripts; `tools` may import `quantrisk` but
  never a study's internals; a study module may import `quantrisk` and its declared siblings. Adopting the
  *pattern* here does **not** mean adopting the tool: a new dependency needs maintainer approval and this
  lane's budget rule says no. The pattern is implemented as a hand-written guard test over the same AST walk
  the collector already performs, with the exemptions declared in the ceilings file.
- **Guard the CI file, and prove the verifier can fail.** mlflow validates `.github/workflows/*.yml`
  against a schema pinned by commit; nautilus runs a CI-inputs verification script at named stages and fails
  on any change to the paths that define its jobs; its verifier is tested by flipping a stored payload byte
  and truncating an entry (`crates/event_store/tests/integration/verifier.rs`). This repository already
  falsifies its guards by planting — the declared inventory is `run_mutation_suite.py --list`, and the
  ceilings file carries it — but nothing yet reads `ci.yml` and asserts that every declared task is
  reachable from some job. That closes the gap this lane opens: after a move, a CI step can point at a path
  that no longer exists and the lane stays green because the step never ran.
- **Repo tooling as a real package, with its own tests.** mlflow keeps its dev tooling in a uv workspace of
  separate packages with their own entry points (`pyproject.toml`); nautilus pairs each pre-commit check
  script with a test file. This is the concrete form of `uv run python -m tools.<name>`: `tools/` stays out
  of the wheel, gets `tests/tools/`, and the string in CI is the string in the contributor docs.
- **Non-core code inside the type gate by rule scope, not path exclusion.** nautilus selects `ALL` repo-wide
  with `per-file-ignores` for examples and tests, and its type-check trigger list deliberately includes
  documentation examples and its own launcher script (`scripts/ci/check-python-types.bash`). The alternative
  — excluding a directory — is precisely the debt §13 L9 exists to remove.

### Patterns rejected, with the reason

- **A job named after a check it does not run.** Riskfolio's `linters` job installs requirements and lints
  nothing, its test step is commented out, and no type checker appears in any configuration file
  (`.github/workflows/build.yml`). It is recorded because it is the failure mode this repository's whole
  culture argues against, and it is one token away from this lane's own future: a CI step that names a moved
  path and silently stops asserting anything.
- **Dirty state as patch text or as a file list.** qlib writes `git diff`, `git status` and
  `git diff --cached` as logged artifacts precisely because its backend stores only a commit id, and kedro
  records a `dirty` boolean beside the sha. QuantRisk++ already records `working_tree_dirty` plus
  `uncommitted_paths` in every artifact's `environment` block. Moving to a diff hash would be a real
  improvement in provenance and a *schema change to frozen artifacts* at the same moment — which would move
  the byte hash of every entry for a reason the refactor does not need. Rejected in this lane; recorded as a
  V3 candidate, not as a defect.
- **A manifest with more fields.** nautilus's `RunManifest` carries `binary_hash`, `config_hash`,
  `crate_versions`, `feature_flags`, `schema_version`, `registered_components`, `seed` and a `Quarantined`
  status (`crates/event_store/src/manifest.rs`). The field gap to this repository's manifest is small, and
  each new field is either a claim with no producer (`config_hash` of what?) or a schema change. Rejected;
  the one that earns a follow-up is `seed`, because a determinism claim with no recorded seed is an
  untraceable claim — but that belongs to the validation lanes, not to a move.

### What the survey changes about the decisions it was asked to test

D1 (three destinations) and D2 (artifact paths frozen) survive unchanged; the studies' own coupling
(finding V2-02, in `REFACTOR_LEDGER.md` §6) is the reason D1's module form must be `run(argv) -> dict` plus
`__main__`, not a script with a `main()` at the bottom. D3 becomes D3′ (self-validating entries, fatal
discovery). D4 becomes D4′ (registry owns the prefix, the producer records the argv). D5, D6 and D7 are
adopted as written. The survey proposes no new dependency, and nothing in this section changes a tolerance
or a formula.
