# QuantRisk++ — Validation Protocol (Phase 0, frozen v0.1)

Date: 2026-09-25 · Status: **PROTOCOL ONLY — no test results exist yet.**
Every later phase must execute this protocol and report real outputs.
Fabricating, hard-coding, cherry-picking, or tolerance-tuning to force passes
is banned (PROJECT_SPEC.md §4).

## 1. Three validation levels

```text
Level 1 — Analytical oracle (closed form / identity / limiting behavior)
Level 2 — Independent open-source oracle (live QuantLib / PyPortfolioOpt / cvxpy / SciPy)
Level 3 — Statistical convergence (rates, coverage, uncertainty, backtests)
```

### 1.1 Component → levels matrix (frozen)

| Component | L1 analytical | L2 independent oracle | L3 statistical |
|---|---|---|---|
| Black-Scholes call/put | formula recomputation, put-call parity, T→0 / σ→0 edges, ITM/OTM bounds | live QuantLib repricing, version recorded | n/a (deterministic) |
| Greeks | analytic vs central finite differences, put-call Greek consistency | QuantLib Greeks where available | bump-size sensitivity study |
| CRR binomial | N→∞ → BS convergence; American-call == European (q=0) | QuantLib lattices | convergence-order plot, not a single N |
| Monte Carlo European | → BS as N grows; seed reproducibility (identical seed ⇒ bit-identical output) | QuantLib + BS | O(1/√N) slope fit ≈ −0.5; 95% CI empirical coverage; variance-reduction ratios |
| Asian / Barrier MC | monitoring-convention tests; degenerate-barrier limits | QuantLib where feasible, else documented weaker validation | discretization refinement; control-variate study |
| Heston simulation | parameter-constraint rejection; positivity; κ/θ/ξ/ρ sanity | stated as weaker if no closed form | step-size refinement; moment/positivity diagnostics |
| VaR / ES | Gaussian closed-form agreement on synthetic N(μ,σ²) | SciPy distributions as reference | bootstrap CIs; Kupiec POF + Christoffersen backtests |
| Covariance | PSD checks; shrinkage target sanity | sklearn Ledoit-Wolf as reference only | conditioning/singularity suite |
| Optimizers | constraint residuals (Σw−1, w≥0, target); objective sanity | PyPortfolioOpt + cvxpy on identical inputs | near-collinear / singular robustness |
| Stress engine | scenario accounting identity (attribution sums to total) | n/a (our framework) | MC-scenario seed stability |

## 2. Tolerance policy (how tolerances are set — values frozen per test, not tuned)

- Report **both** absolute and relative error for every comparison.
- Tiers: deterministic analytic checks (tight, e.g. `1e-10`–`1e-12` relative on
  BS/parity — exact values pinned in Phase 2 test files, justified by `double`
  rounding, not by trial and error); lattice/MC (looser, justified by theory:
  binomial truncation, `SE ≈ s/√N`); statistical checks (hypothesis-test based:
  coverage within binomial CI, backtest p-values, slope tolerance bands).
- Forbidden: lowering a tolerance or deleting a failing test to make CI green.
  A failing validation ⇒ fix code, widen tolerance **with written statistical
  justification**, or downgrade the claim — recorded in the Phase Report.

## 3. Deterministic policy (reproducibility)

- RNG: `std::mt19937_64` only; **no global RNG state** — engines own their
  generator instance; every stochastic entry point takes an explicit seed.
- Seeds: defaults fixed (e.g. `42` for demos) and recorded; experiments sweep
  documented seed lists; identical `(seed, N, params, code version)` ⇒
  bit-identical output on the same platform.
- Floating point: `double` throughout the core (`float` banned in numerical
  paths); no `-ffast-math` or equivalent reassociation flags; summation order
  documented where it matters (e.g. payoff accumulation).
- Metadata recorded with every experiment/benchmark artifact: seed(s), `N`,
  parameter grid, git commit, compiler + flags, OS + CPU arch, library versions
  (Eigen/pybind11/QuantLib/PyPortfolioOpt/cvxpy/SciPy), UTC timestamp,
  input-data SHA256 where applicable.
- Compiler metadata: Apple clang / GCC / Clang versions + `-O` level + C++20
  standard flag are part of the result, especially for performance claims.

## 4. Benchmark-integrity rules

1. Oracles run **live** in the benchmark script; outputs are computed, never pasted.
2. No hard-coded oracle numbers in `tests/` or `benchmarks/`.
3. Oracle version + configuration printed into the artifact (CSV/JSON header).
4. Performance claims require: compiler, CPU arch, paths count, repetitions,
   mean ± std, and a pure-Python baseline measured on the same machine.
5. Failed experiments are kept and reported (a `limitations.md` entry beats a
   deleted script).

## 5. Artifact chain (README numbers must trace)

```text
script (fixed command + seed)
  → raw result (CSV/JSON, committed or hashed)
    → figure/table (generated, never hand-edited)
      → README/report number (with link to artifact + manifest entry)
```

Phase 10 freezes this into `evidence/manifest.json` (SHA256 per key artifact).
Until then, every phase stores its raw outputs under `experiments/<topic>/`.

## 6. Offline-CI rule

- `ctest` + `pytest` run fully offline. Network APIs (Phase 8) are optional,
  cached, and fixture-backed: missing key/connection ⇒ tests use fixtures,
  never fail on network, never phone home during validation.
- Dependency fetching at configure time (Catch2/Eigen/pinned tags) is the only
  network touch in build; CI caches it and records tags.

## 7. Phase-gate checklist (reused every phase)

```text
[ ] build clean (warnings documented)
[ ] C++ tests pass (ctest), Python tests pass (pytest)
[ ] numerical validation vs L1/L2/L3 executed with real output
[ ] no invented numbers; artifacts stored
[ ] limitations + tech debt updated
[ ] Phase Report written; STOP before next phase
```
