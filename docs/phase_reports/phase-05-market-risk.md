# Phase 5 Report — Market Risk: VaR/ES, Bootstrap Intervals, Coverage Backtests

Date: 2026-09-26 · Branch: `main` · Status after this phase: **complete and verified**
Research question answered: *are the VaR/ES estimators and the Kupiec/Christoffersen
backtests statistically valid on synthetic distributions whose truth is known?*

## 1. Completed

- **Loss convention and return definitions** (`risk::returns`): arithmetic and log
  returns, with the reason they are not interchangeable recorded in the header.
- **Six point estimators** (`cpp/src/risk/measures.cpp`): historical VaR (linear-interpolated
  empirical quantile of losses), historical ES (mean of the `ceil(n(1-alpha))` worst
  losses), Gaussian VaR/ES (variance-covariance closed forms), Monte Carlo VaR/ES for
  simulated P&L, plus `quantile_standard_error` from the tail density.
- **Uncertainty by resampling** (`cpp/src/risk/bootstrap.cpp`): iid and moving-block
  percentile intervals, `n^(1/3)` default block length, seed-owned RNG, all four
  quantities (point, SE, interval, design) reported together.
- **Coverage backtests** (`cpp/src/risk/backtest.cpp`): violation flagging against a
  constant or a time-varying VaR series, transition counting, Kupiec POF, Christoffersen
  independence and conditional coverage, and `backtest_var` returning the whole set.
- **Special functions the tests depend on** (`cpp/src/math/special.cpp`): Lanczos
  `log_gamma` with reflection, regularized incomplete gamma in both directions, the
  chi-square survival function, and `chi_square_isf` obtained by inverting that survival
  function rather than by a tabulated critical-value table.
- **Python surface**: `quantrisk.special`, `quantrisk.risk`, `quantrisk.risk.returns`,
  all 24 bound entry points taking `std::vector<double>` adapters so NumPy arrays and
  lists both work.
- **Evidence**: `experiments/var_backtesting/` (3 CSVs, 2 PNGs, 1 JSON), 51 new pytest tests
  (two of them live-SciPy oracle files plus one for the evidence tooling itself), and
  21 new C++ test cases. Suite: 111 CTest entries, 205 pytest tests.

## 2. Mathematical assumptions

- `L = -R` (loss convention). VaR_alpha is the alpha-quantile of the loss distribution;
  ES_alpha is `E[L | L >= VaR_alpha]` estimated as a tail mean.
- Quantile convention is NumPy `method="linear"`: `x[floor(h)] + (h - floor(h)) (x[ceil(h)] - x[floor(h)])`, `h = p (n - 1)`.
- Gaussian estimators assume the return sample is an iid draw from one normal law with
  the mean and unbiased standard deviation estimated from that same sample.
- Kupiec: violations iid Bernoulli(`1 - alpha`), LR against chi-square(1).
  Christoffersen independence: violations follow a two-state Markov chain, `H0: pi_01 = pi_11`,
  chi-square(1). Conditional coverage: `LR_cc = LR_ind + LR_po` on chi-square(2), which is
  valid only because the two are asymptotically orthogonal.
- Moving-block bootstrap assumes stationary, weakly dependent data and preserves
  within-block dependence only up to the block length.
- All chi-square tail probabilities come from the project's own incomplete-gamma
  implementation, cross-checked against SciPy at run time.

## 3. Files changed

| File | Change |
| --- | --- |
| `cpp/include/quantrisk/math/special.hpp`, `cpp/src/math/special.cpp` | new; `chi_square_isf` added during validation |
| `cpp/include/quantrisk/risk/{measures,bootstrap,backtest}.hpp`, `cpp/src/risk/*.cpp` | new |
| `cpp/src/core/statistics.cpp` | `require_sorted` precondition on the `*_sorted` primitives |
| `bindings/python_bindings.cpp` | `special` + `risk` submodules, container adapters |
| `python/quantrisk/__init__.py` | re-exports `risk`, `special` |
| `tests/cpp/test_{special_functions,risk,statistics}.cpp` | 6 + 14 new cases, plus 1 in the statistics file |
| `tests/python/test_special_functions_vs_scipy.py`, `test_risk_measures.py` | new (9 + 31 tests) |
| `experiments/var_backtesting/run.py` + `results/*` | new evidence chain |
| `docs/model_cards/var_es.md`, this report | new |
| `docs/limitations.md` (items 28–35), `docs/project_scope.md` (§9 status, §10 Phase 5 frozen surface), `README.md` (status, claims table) | status updated |
| `docs/validation_protocol.md` | two frozen rules: expected values are derived, never transcribed; artifacts carry run-time provenance |
| `python/quantrisk/experiments/metadata.py` | `working_tree_state` / `parse_porcelain_status`, repo-relative `artifact_manifest` |
| `tests/python/test_artifact_metadata.py` | new (11 tests) |

## 4. Tests executed

- `rm -rf build/dev && uv run cmake --preset dev && uv run cmake --build --preset dev`
  — full clean rebuild (144 build steps), **0 warnings**. The core and reference-tool
  targets are the only ones compiled with `-Wall -Wextra -Wpedantic`; the test and
  binding targets are not, which is recorded as debt.
- The clean reconfigure also surfaced a **workflow defect**: bare `cmake --preset dev`
  with no active virtualenv silently built the extension for system Python 3.14 while
  `uv run pytest` imports the 3.12 one. CI already used `uv run cmake`; the README did
  not tell anyone to. Fixed by switching the documented commands to `uv run cmake` and
  by printing `bindings: Python <version> at <executable>` at configure time so the
  mismatch announces itself instead of producing a stale-looking module.
- `ctest --preset dev` — **111 / 111 passed** (110 Catch2 cases + the reference-tool
  case). Cross-checked against `./build/dev/quantrisk_tests --list-tests` (110 cases,
  545,465 assertions) so a partial run cannot be mistaken for a full one.
- `uv run pytest -q` — **205 passed** (52 of them new in this phase).
- `uv run ruff check .` / `ruff format --check .` — clean.
- `uv run python experiments/var_backtesting/run.py` — 5 artifacts regenerated.
- `clang-format` applied to every touched C++ file, and the CI gate
  (`find cpp bindings tests/cpp ... | xargs clang-format --dry-run --Werror`) run
  locally: clean. It had been failing — the Phase 5 edits were not formatted.

## 5. Exact test results

The honest part of this phase is what was broken when it was first run to completion.
`ctest --preset dev` uses `stopOnFailure: true`, and the Phase 5 cases are numbered
after the earlier ones, so a run that halted at test 94 printed "99 % tests passed,
1 failed out of 94" while 16 later cases had never executed. Running the Catch2 binary
directly (it executes every case in one process) exposed 6 failing cases and 11
failing assertions:

| Defect | Where | Symptom | Fix |
| --- | --- | --- | --- |
| Lanczos series denominator off by one (`z + i - 1` instead of `z + i`) | `special.cpp` | `log_gamma(13) = 20.078` vs 19.987; `log_gamma(0.25) = NaN` (log of a negative sum) | corrected denominator, verified against `math.lgamma` (max abs err 1.8e-15) |
| Kupiec likelihood dropped `x ln p` and used `x ln x` in **both** likelihoods | `backtest.cpp` | LR statistic reduced to its first term: `-0.9989` for 13 violations in 250 (a likelihood ratio cannot be negative), p-value pinned at 1.0, so a badly under-set VaR was reported as a pass | both binomial likelihoods written from the definition; a `0 * log(0)` limit helper replaces the term that hid the bug |
| `monte_carlo_var` read its quantile from an **unsorted** loss array | `measures.cpp` | VaR of a standard-normal P&L sample reported `-0.41` instead of `1.64`; the CI was computed on the same garbage | sort first; the `*_sorted` primitives now refuse unsorted or NaN input rather than returning a plausible number |
| Lower incomplete gamma computed as `1 - (1 - P)` | `special.cpp` | `P(20, 0.01) = 4.07e-59` came out as exactly `0.0` | P and Q each evaluated from the representation that is not sitting at one |
| Tabulated chi-square critical values | `backtest.cpp` | a 5 % point for 4 dof had been recorded under 5 dof in a test | `chi_square_isf` solves the quantile from the same survival function as the p-value |
| Binding signatures took `std::span` directly | `python_bindings.cpp` | `historical_var(np.array)` raised `incompatible function arguments`; the module also lacked the `risk`/`special` re-exports | vector adapters + re-export list |

Three more defects came from the evidence tooling itself, found while writing its
first tests (`tests/python/test_artifact_metadata.py`):

| Defect | Effect | Fix |
| --- | --- | --- |
| `artifact_manifest` stored absolute paths | every committed artifact published the host's absolute path prefix and differed per machine | repo-relative paths |
| `git_commit` was captured at configure time | every artifact from Phases 1–4 names the *previous* phase's commit while the real code was uncommitted, and a clean tree made that read as a confident false statement | run-time `git_commit` plus `binary_git_commit`, `working_tree_dirty`, `uncommitted_paths`, and a `provenance` sentence that differs for the four reachable cases |
| a `!!`-prefix check applied to the path instead of the status column | dead branch written from a wrong model of `git status --porcelain`; the new parser test caught it before it shipped | removed, and the format documented in the parser |

Two of the six C++ failures were **wrong expectations in my own tests**, not library bugs
(row-major layout of `linear_pnl`/`sample_covariance` assumed asset-major; a
`zip(..., strict=True)` misuse), and were corrected against the documented contract
rather than by changing the contract.

After the fixes: 111/111 CTest, 205/205 pytest, clang-format and ruff gates clean, a
zero-warning clean rebuild, and all artifacts regenerated from the fixed code.

## 6. Numerical validation

All values below are from `experiments/var_backtesting/results/` regenerated on 2026-09-26
(build metadata and SHA256 in `var_backtesting_validation.json`).

**Estimators against a known population value** (400 replications per cell, 200
independent calibration blocks of 10 000 observations, 20 000 out-of-sample days each):

| Data | Level | Population VaR | realised rate, historical | realised rate, Gaussian |
| --- | --- | --- | --- | --- |
| Gaussian, sigma 2 % | 95 % | 0.032897 | 0.050335 | 0.050208 |
| Gaussian, sigma 2 % | 99 % | 0.046527 | 0.010144 | 0.010092 |
| t(3), same volatility | 95 % | 0.027174 | 0.050140 | **0.032909** |
| t(3), same volatility | 99 % | 0.052432 | 0.010212 | **0.013888** |

The empirical estimator tracks nominal at both levels. The normal fit misses in
**opposite directions** — 21 % too high a level at 95 % (under-violating), 11 % too low
at 99 % (over-violating) — because the normal and t quantile spacings differ. Bias of the
Gaussian estimator at n = 250, 95 %, Gaussian data: `-8.23e-05` (0.25 % relative).

**Size, power and discrimination of the coverage tests** (2 000 replications of 250 days):

| Arm | Kupiec reject @5 % | Independence reject @5 % | Conditional |
| --- | --- | --- | --- |
| correctly calibrated iid (5 % true rate) | 0.0505 | 0.0235 | 0.0380 |
| over-calibrated iid (2 % true rate) | 0.7525 | 0.0206 | 0.6136 |
| under-set level (12 % true rate) | 0.9860 | 0.0600 | 0.9620 |
| clustered, correct marginal (persistence 0.25) | 0.1200 | **0.5540** | 0.5345 |

Kupiec has its nominal size (0.0505 against 0.05, exact binomial interval [0.0413, 0.0610])
and is conservative at the 1 % cutoff (0.0075) because the statistic is a function of an
integer count. The clustered row is the result that matters most: a model whose violations
arrive in runs passes an unconditional-frequency check 88 % of the time while the
independence test catches it in 55 % of samples — and the reverse also holds, since a pure
frequency error draws a spurious clustering signal only 5–6.8 % of the time. Power against
an under-set level reaches 1.000 by 500 days.

**Bootstrap coverage** of the 95 % VaR, nominal 90 % interval, 400 replications of n = 500,
1 500 draws, target = unconditional VaR from a 2 000 000-draw simulation:

| Data | iid design | moving-block design (length 8) |
| --- | --- | --- |
| iid Gaussian | 0.8725 [0.8357, 0.9035] | 0.8700 [0.8330, 0.9013] |
| GARCH(1,1) clustered | **0.6250 [0.5755, 0.6726]** | **0.6925 [0.6447, 0.7374]** |

On iid data the percentile interval is slightly under nominal and the block design costs
nothing. Under clustering the iid design loses almost 28 percentage points of coverage;
the block design recovers about 7 of them (non-overlapping intervals) and still falls
roughly 21 points short. Reported as a limitation, not fixed by tuning.

## 7. Remaining limitations

Recorded as items 28–35 of `docs/limitations.md` and in `docs/model_cards/var_es.md`.
In short: synthetic data only; empirical 99 % VaR at 250 observations averages two or
three order statistics; the Gaussian estimators are demonstrably wrong for fat tails and
in both directions; percentile bootstrap intervals are not bias-corrected; **neither**
bootstrap design reaches nominal coverage under GARCH clustering at n = 500; the estimand
is the unconditional quantile, not a conditional one; coverage tests cannot validate the
model that produced the VaR series and carry no multiple-comparison correction; no
Cornish-Fisher, EVT, filtered historical simulation, or ES backtest.

## 8. Technical debt

- **`ctest --preset dev` stops at the first failure**, so a "99 % passed out of N" line
  can describe a partial run. Every phase report from here quotes the Catch2 case count
  and the CTest total together, and the discrepancy is what to look for. Consider adding
  a full-run invocation in CI once the installed CTest supports it (this CTest rejects
  `--no-stop-on-failure`), or by running the Catch2 binary directly, which reports every
  case in one process.
- `quantile_standard_error` estimates the tail density from neighbouring order
  statistics. It is honest about ties (NaN) but noisy for small `n`; a smooth density
  estimate would be better and is not implemented.
- The moving-block default `round(n^(1/3))` is a general-purpose rule. The measured
  coverage shortfall on clustered data suggests a longer block or a stationary bootstrap;
  no experiment has yet swept block length against coverage.
- `linear_pnl` and `sample_covariance` live in `risk/` but are portfolio algebra; they
  move to `portfolio/` in Phase 6 when that module needs them.
- The Python facades the specification asks for (`quantrisk.risk.RiskEngine`, ...) are
  Phase 9 work. `quantrisk.risk` is currently the pybind submodule, so the facade has to
  be attached to it rather than shadow it; that choice is still open.
- `historical_var`/`gaussian_var`/`monte_carlo_var` share their whole body apart from the
  estimator and the note. A strategy-object refactor would remove the triplication but is
  not worth it at three call shapes.
- The test and pybind targets are compiled without `-Wall -Wextra -Wpedantic`, so
  warnings in `tests/cpp/` and `bindings/` are invisible. Either extend the flags there
  or state why they stay off.
- **Earlier phases' artifacts are stale in exactly the two ways fixed above**: they
  carry absolute paths and a `git_commit` that predates their own code. They must be
  regenerated during the Phase 10 evidence freeze.
- Provenance is only fully clean when the artifact is generated from a committed tree
  *after* the binary was rebuilt from it, which needs the ordering
  "commit code → rebuild → regenerate evidence → commit evidence". The Phase 5
  artifacts now record `git_commit == binary_git_commit == 44f14fd` with only
  themselves listed as uncommitted; the Phase 10 freeze should finish that loop so
  `working_tree_dirty` reads `false`.
- `docs/interview_defense.md` predates this phase and cites Phase 1–4 evidence only;
  it needs a Phase 5 pass before the portfolio audit.

## 9. Gate

**Ready for Phase 6.** The Phase 5 requirement — output VaR estimate, ES estimate,
uncertainty, violations, Kupiec test, Christoffersen test, all reproducible — is met:
every one of those quantities is produced by a named C++ function, reached from Python
through a thin binding, covered by a test that checks it against a definition or a live
SciPy oracle, and reported with its measured statistical behaviour in a hashed artifact.
The two defects that validation found in itself (a negative likelihood ratio and an
unsorted quantile read) are the strongest evidence in the phase that the tests are doing
their job.
