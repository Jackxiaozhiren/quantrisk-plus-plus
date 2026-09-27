# Phase 7 Report — Scenario and Stress Testing

Date: 2026-09-27 · Branch: `main` · Status after this phase: **complete and verified**
Research question answered: *a portfolio is optimal for the covariance it was given —
does a stress change which portfolio is the risky one, and can attribution say why?*

## 1. Completed

- **The five objects the spec names** (`cpp/include/quantrisk/stress/`): `RiskFactor` /
  `FactorSet`, `Shock` / `DistributionShift`, `Scenario`, `Portfolio` / `Position` /
  `ExposureVector`, `ScenarioResult` (plus `ScenarioSetResult` and `ScenarioSample`).
  1,152 lines across four headers and four sources. No if/else demo: the scenario is data,
  the transformation is a single documented map, and the result carries its own proof that
  the decomposition added up.
- **Factor-class-aware shock resolution.** Equity factors are shocked relatively, rate /
  volatility / credit factors absolutely, both units resolved wherever the quoted level
  permits, and a shock that states both and disagrees rejected outright.
- **Deterministic mapping** `ΔP&L = Σᵢ δsᵢ + γᵢsᵢ² + dᵢaᵢ + vᵢaᵢ + cᵢa` with per-factor
  and per-position attribution, each with its own residual field.
- **Distribution deformation** (`shift_covariance`): sigma scaling and an off-diagonal
  correlation lift, with clipping counted and reported, and a non-positive-semidefinite
  result announced rather than projected away.
- **Risk metrics under stress**: parametric VaR/ES/volatility from the shocked beta and
  covariance, the VaR change split into telescoping level and dispersion legs, and Euler
  component VaR allocated across positions.
- **Historical replay and Monte-Carlo scenario sets** (`simulation.cpp`): Cholesky sampling
  on the project `Rng`, reproducible by seed, and a replay path that needs no covariance at
  all.
- **Python surface**: `quantrisk.stress` — 5 functions, 16 bound types.
- **Evidence**: `experiments/stress_testing/` (3 CSVs, 1 PNG, 1 JSON) and
  `tests/python/test_stress_vs_oracles.py`.

Suite after this phase: **190 CTest entries, 546,943 assertions in 189 Catch2 cases,
265 pytest tests.**

## 2. Mathematical assumptions

- The book is described by factor exposures, not instruments. P&L is a delta-gamma Taylor
  expansion in the factor moves; the truncation is measured, not assumed away.
- `gamma` is quoted with the ½ absorbed, so the mapping reads `γᵢs²`. This is stated
  because the Black-Scholes gamma a caller would derive it from does not carry the ½, and
  the revaluation test depends on the convention.
- Portfolio dispersion uses the **first-order** beta `δ + duration + vega + credit`.
  Convexity moves the mean, not the variance; folding a squared term into a covariance
  would make the second moment depend on the scenario's direction.
- Gaussian VaR/ES under the frozen loss convention `L = −P&L`:
  `VaR_α = −μ_P&L + z_ασ`, `ES_α = −μ_P&L + σ φ(z_α)/(1−α)`.
- The level/dispersion split of `ΔVaR` is exact **only because** the Gaussian quantile is
  affine in (mean, sigma). It does not telescope for a historical or Cornish-Fisher
  estimator, and that boundary is in the code comment where the split is computed.
- Euler allocation `c_p = β_p'(Σβ)/(β'Σβ) · VaR` sums to VaR because the portfolio beta is
  the sum of the position betas — a theorem, not an approximation.
- Monte-Carlo scenarios are drawn from a **gaussian** covariance. The scenario's shocks set
  the centre and its distribution field sets the shape, so the set is the outcome
  distribution *around* the stress rather than an additional stress.
- Factor-move covariances are quoted in the units the exposures answer to (relative for
  equities, absolute for the rest). Passing a covariance of returns instead is a units
  error the arithmetic will not catch — which is why the parameter is named for moves.

## 3. Files changed

| Path | Lines | Role |
| --- | --- | --- |
| `cpp/include/quantrisk/stress/factor.hpp` | 96 | factors, exposures, portfolio |
| `cpp/include/quantrisk/stress/scenario.hpp` | 73 | shocks, distribution shift, scenario |
| `cpp/include/quantrisk/stress/engine.hpp` | 126 | result types, `run_scenario`, `shift_covariance` |
| `cpp/include/quantrisk/stress/simulation.hpp` | 93 | sampling, scenario sets |
| `cpp/src/stress/factor.cpp` | 105 | validation and aggregation |
| `cpp/src/stress/scenario.cpp` | 28 | shock conversion |
| `cpp/src/stress/engine.cpp` | 331 | mapping, attribution, risk metrics, shift |
| `cpp/src/stress/simulation.cpp` | 300 | Cholesky sampler, historical and MC sets |

Also changed: `bindings/python_bindings.cpp` (the `stress` submodule),
`python/quantrisk/__init__.py` (re-export), `CMakeLists.txt` (four sources, two test
files). New tests: `tests/cpp/test_stress_engine.cpp` (20 cases),
`tests/cpp/test_stress_simulation.cpp` (12 cases),
`tests/python/test_stress_vs_oracles.py` (13 tests). New evidence and docs:
`experiments/stress_testing/`, `docs/model_cards/scenario_stress_testing.md`, this report.

## 4. Tests executed

```bash
uv run cmake --preset dev && uv run cmake --build --preset dev
uv pip install -e .                       # the editable install carries its own copy of the .so
./build/dev/quantrisk_tests
ctest --test-dir build/dev
uv run pytest -q
uv run pytest -m oracle tests/python/test_stress_vs_oracles.py
uv run python experiments/stress_testing/run.py
find cpp bindings tests/cpp -name '*.cpp' -o -name '*.hpp' | sort |
  xargs uv run clang-format --dry-run --Werror
uv run ruff check . && uv run ruff format --check .
```

## 5. Exact test results

```
All tests passed (546943 assertions in 189 test cases)
100% tests passed out of 190
265 passed in 7.16s
13 passed                              (the stress oracle file)
clang-format --dry-run --Werror        clean
ruff check .                           All checks passed!
build                                  zero compiler warnings
```

All four experiment artifacts are byte-identical across independent runs.

## 6. Numerical validation

**L1 — identities.** 28 scenario/book combinations: worst factor-attribution residual
**0.0**, worst position-attribution residual **0.0**, worst level/dispersion decomposition
residual **0.0**. A one-day replay equals the deterministic scenario for that day to
1e-12. A single scenario returns NaN for VaR/ES rather than a relabelled outcome.

**L2 — independent numerics.** P&L mapping, covariance shift, historical replay and its
quantile recomputed in NumPy: agreement to 1e-9 relative. Stressed VaR against SciPy's own
normal quantile: 1e-9. Euler allocation against a central-difference gradient of the VaR
formula: **3e-10** relative against a bound set at 1e-6, i.e. ~3000× inside its tolerance,
so the check discriminates rather than accommodates.

**L2 — against full revaluation.** A three-strike call book shocked through the exposure
map and re-priced through the Phase 2 Black-Scholes engine:

| equity fall | delta-gamma relative error | delta only |
| --- | --- | --- |
| 0.1 % | 1.35e-6 | 2.10e-3 |
| 1 % | 1.33e-4 | 2.15e-2 |
| 10 % | 9.75e-3 | 2.77e-1 |
| 20 % | 5.37e-3 | 7.28e-1 |
| 40 % | 4.88e-1 | 2.13e+0 |

Convexity buys two orders of magnitude at a 1 % move and the delta-only map is already
wrong by more than a fifth of the P&L there. The delta-gamma column is **not monotone** —
it improves between 10 % and 20 % because the cubic term changes sign through the strike
region. That is reported rather than smoothed, and it means a bound read off one point of
this curve would be wrong at another.

**L3 — simulation against closed form.** A 400k-path Monte-Carlo stress VaR reproduces the
parametric number within 1 %, and the longer run is the closer one (convergence, not
luck). The sampler's realised dispersion recovers the supplied covariance to within 2 %,
cross-checked against NumPy's Generator — a different RNG and a different normal transform,
so a reproducibility defect in our path could not agree with it by construction.

**The finding.** Four books built by the Phase 6 optimisers, ranked by base parametric VaR
and re-ranked under each of the seven named scenarios:

- **No book changes its absolute risk rank in any scenario.** But the artifact records why,
  and it is not a reassuring why: the books started 20.8 % apart in base VaR while the
  largest stress-induced multiplier spread was 16.8 %. The stability is a near-miss, not a
  property of the optimisers.
- **Ranked by multiplier, the order inverts completely** — 4 of 4 books change rank under
  the equity crash. `min_variance`, the safest book under normal dispersion, is the *most*
  stress-sensitive (6.11×) and `equal_weight`, the riskiest normally, is the least (5.23×).
  This is the Phase 6 result seen from the other end: optimising for an estimated covariance
  concentrates a book, and concentration is exactly what an equity stress amplifies.
- `vol_x2` gives every book a multiplier of exactly 2.000 with zero spread — a pure scale
  change moves sigma and nothing else, which is the decomposition working as designed.
- The most uncertainty-driven scenario is `vol_x2` with `level_share` exactly 0.0: all of
  its VaR increase is dispersion, none of it is loss already taken.

## 7. Remaining limitations

Recorded as `docs/limitations.md` entries 43–48.

1. **Delta-gamma only.** No higher-order terms, no full revaluation, and the error is
   non-monotone in move size.
2. **Gaussian scenario moves.** No t-copula, no jump component, no stochastic volatility in
   the sampler; a convex book under gaussian moves produces a skewed P&L, which is measured
   in a test and not modelled further.
3. **The decomposition only telescopes for Gaussian measures.** Historical and
   Cornish-Fisher estimators would need a different, non-additive treatment.
4. **No term structure.** One factor per asset class, so a rate shock is parallel by
   construction; butterfly and steepener scenarios are not expressible.
5. **Reverse stress testing is absent.** The engine answers "what does this shock do"; it
   does not solve for "what shock produces this loss".
6. **Every number is from a fixture chosen by the author.** The rank-stability result in
   particular is a property of how far apart these four books happened to start.

## 8. Technical debt

- **pybind11 value semantics on vector members.** `exposures.delta[0] = x` edits a copy and
  is silently lost — it cost an hour of chasing a "engine returns zero" bug. Pinned by
  `test_bound_exposure_blocks_are_value_semantic`, but the real fix is a typed builder or a
  `__setitem__`-aware proxy, which belongs with Phase 9's facade work.
- `Portfolio::aggregate()` is recomputed inside the per-position attribution loop, so a
  book with *p* positions does *p*+1 aggregations. Linear in positions, invisible at the
  sizes tested, wasteful at scale.
- The stress layer has no `LpStatus`-style machine-readable outcome field; `note` and
  `has_risk_metrics` carry what a status enum should.
- `beta_of` and the Gaussian helpers live in `engine.cpp`'s anonymous namespace with a
  `detail::` bridge for the two functions `simulation.cpp` needs. If Phase 10's validation
  matrix adds more scenario kinds, that bridge wants its own header.
- No scenario-set-level attribution of the *quantile* (only of the mean): `by_factor`
  reports mean and worst contribution, not "which factor drove the 95th-percentile loss".
  Euler allocation across factors, not positions, is the missing piece.
- `-Wall -Wextra -Wpedantic` still covers `quantrisk_core` only.

## 9. Gate

PROJECT_SPEC.md §Phase 7 requires the chain
`Scenario → explicit assumptions → reproducible transformation → portfolio impact → attribution`.

| Link | Verdict | Evidence |
| --- | --- | --- |
| Scenario | **met** | `Scenario` object with kind, shocks, distribution shift, horizon, seed; three kinds implemented and each validated against the others |
| Explicit assumptions | **met, and enforced** | `assumptions` is a field the engine reads: an empty one and a missing horizon are both reported in the result note, so a scenario cannot silently present a number without provenance |
| Reproducible transformation | **met** | one documented map from exposures to P&L; the sampler is reproducible by seed (identical vectors across runs) and all four artifacts are byte-identical between executions |
| Portfolio impact | **met** | P&L, VaR/ES/volatility change, and the level/dispersion split, plus a full outcome distribution for historical and Monte-Carlo sets |
| Attribution | **met, not a single total** | per-factor (split linear / convexity / rate / vol / credit), per-position, Euler VaR components, and worst-contribution per factor — with residuals of exactly 0.0 across all 28 combinations |
| Own implementation (§2.2) | **met** | the map, the shift, the Cholesky sampler and the decomposition are ours; NumPy/SciPy appear only as oracles and are imported by no library code |
| Nothing paid for (§3) | **met** | no new dependency of any kind |
| No fabricated number (§4) | **met** | the rank-stability result is reported together with the base spread that made it possible; the non-monotone truncation error is published rather than the flattering point alone |

**Gate: PASS.** Phase 7 is complete and verified. Next: Phase 8 — the free public data
layer (SEC EDGAR, FRED) with an offline fixture cache, which is where these scenarios get
inputs that are not authored by me.
