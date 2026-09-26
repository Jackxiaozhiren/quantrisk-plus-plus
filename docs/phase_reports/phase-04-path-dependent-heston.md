# Phase 4 Report - Path-Dependent Pricing & Stochastic Volatility

Date: 2026-09-26 · Platform as Phase 3 (Apple clang 21.0.0 arm64, CPython 3.12.14,
QuantLib 1.43).

## 1. Completed

- `quantrisk::AsianOption` / `BarrierOption` with monitoring conventions, and
  `geometric_asian_price`: the closed form of a **discretely monitored geometric
  average** (`mu`, `s^2` in `cpp/src/monte_carlo/path_dependent.cpp`, whose
  variance tends to `sigma^2 T / 3`).
- `path_dependent::price_asian` (arithmetic, with the geometric average of the
  same paths as a control variate), `price_geometric_asian`, `price_barrier`
  (discrete monitoring, optional Broadie-Glasserman-Kou continuity correction,
  optional antithetic pairing).
- `quantrisk::HestonParams` + `simulate_heston` + `price_heston_european` +
  `heston_step_refinement_gap`: full-truncation Euler with correlated normals,
  variance clamping counted, Feller condition **reported not enforced**.
- `benchmarks/quantlib/path_dependent_validation.py` (25 rows, 25 with the
  full grid) with four oracle families, each with recorded availability.
- Bindings for all of the above; 13 new Catch2 cases and 17 new pytest checks;
  model cards `path_dependent_options.md` and `heston.md`.
- `docs/interview_defense.md` (22 spec-mandated questions x 3 depth levels) was
  produced in parallel from the frozen specifications and artifacts.

## 2. Mathematical assumptions

As stated in the two model cards. Load-bearing ones: exact GBM between fixings
(the Asian/barrier sections are under Phase 1's market model, Heston replaces
it); monitoring happens at `t_i = i T / M` in year fractions with no calendar
arithmetic; full-truncation Euler for Heston is biased and the bias is measured,
not assumed away; BGK is an `O(sqrt(dt))` asymptotic correction for a single
barrier, not an exact treatment of continuous monitoring.

## 3. Files changed

Added: `cpp/include/quantrisk/pricing/path_dependent.hpp`,
`cpp/include/quantrisk/monte_carlo/path_dependent.hpp`,
`cpp/include/quantrisk/stochastic/heston.hpp`,
`cpp/src/pricing/path_dependent.cpp`, `cpp/src/monte_carlo/path_dependent.cpp`,
`cpp/src/stochastic/heston.cpp`,
`tests/cpp/test_path_dependent.cpp`, `tests/cpp/test_heston.cpp`,
`tests/python/test_path_dependent_and_heston.py`,
`benchmarks/quantlib/path_dependent_validation.py` + results,
`docs/model_cards/{path_dependent_options,heston}.md`, `docs/interview_defense.md`.
Modified: `CMakeLists.txt`, `bindings/python_bindings.cpp`,
`python/quantrisk/plotting/__init__.py` (series length guard), docs and README.

## 4. Tests executed

```bash
cmake --preset dev && cmake --build --preset dev && ctest --preset dev
uv pip install -e . && pytest -q
uv run python benchmarks/quantlib/path_dependent_validation.py
```

## 5. Exact test results

```text
CTest : 100% tests passed out of 90
pytest: 153 passed, 0 failed
ruff / clang-format: clean; no compiler warnings
```

## 6. Numerical validation (all numbers from the committed artifact)

Worst relative error against live QuantLib oracles
(`benchmarks/quantlib/results/path_dependent_vs_quantlib.json`):

| family | worst relative error | reading |
|---|---|---|
| `heston_degenerate` (xi = 0 vs Black-Scholes) | 2.095e-03 | within sampling error at 200k paths |
| `heston_analytic` (vs `AnalyticHestonEngine`) | 4.467e-03 | mixes our `O(dt)` bias with the oracle's quadrature |
| `asian_geometric_closed_form` | 5.545e-04 | residual is calendar-day rounding of fixings |
| `asian_geometric_simulated` | 2.303e-03 | MC noise, inside a few SE |
| `barrier_discrete` (250 dates vs continuous) | 14.028% | the monitoring bias, uncorrected |
| `barrier_bgk_corrected` | 0.997% | same bias reduced ~14x by the correction |

Oracle availability is recorded per family, including the arithmetic Asian case
where the geometric analytic value is reported as `arithmetic_minus_geometric`
(the AM >= GM spread) rather than as a "relative error", because it is not an
oracle for that payoff.

Two defects were found only because an oracle was consulted:

1. **The continuity correction moved the barrier the wrong way.** It is
   implemented as `B_eff` closer to the spot for both directions now; the raw
   discrete estimate was 14.0 % above the continuous analytic value and the
   corrected one 1.0 %.
2. **The benchmark's fixing schedule did not match the closed form's**
   (`t_i = i T / M`, last fixing at expiry), which had produced a spurious 12 %
   disagreement between two correct formulas.

## 7. Remaining limitations

Recorded in `docs/limitations.md` (Phase 4 section) and the two model cards:
no calendar/day-count layer for fixings, monitoring grid == simulation grid,
BGK is asymptotic, Heston validation is weaker than the Black-Scholes section
(the oracle is itself numerical), no Heston Greeks, no smile calibration,
no basket/double-barrier variants.

## 8. Technical debt

- `price_barrier` and `price_asian` materialise the full path matrix
  (`paths x (steps+1)` doubles): 1.6 GB at 200k x 1000 steps. Phase 7's stress
  engine will need a streaming payoff accumulator.
- The Heston result type duplicates `MonteCarloResult` fields instead of
  embedding it; unified when the risk engine needs both.
- `heston_step_refinement_gap` uses two independent streams rather than common
  random numbers, so its value contains MC noise as well as bias; a
  common-random-numbers variant would isolate the bias.

## 9. Gate

The Phase 4 gate is explicitly *not* about model count: the Heston assumptions
(`docs/model_cards/heston.md`), its bias, and the fact that its validation is
weaker than the Black-Scholes section are written down, and the barrier/Asian
sections carry quantitative oracle evidence. **Status: READY for Phase 5.**
