# v1.0.0 — Design and Validation of a Reproducible C++/Python Stochastic Risk Engine

Released 2026-09-27. Total monetary cost of building and validating this release: **$0** —
no paid data, solver, cloud service or API key is used anywhere.

## What this release is

A C++20 numerical core with Python facades, covering twelve components across pricing,
simulation, market risk, portfolio optimisation and stress testing. The product is not the
model list — QuantLib and PyPortfolioOpt already have longer ones. The product is that every
published number traces to a script, and that the boundary of each claim is written down.

Concretely, in this release:

- **190 C++ tests** (546,943 assertions in 189 Catch2 cases) and **319 Python tests**, all
  green, all offline by default.
- **11 benchmark and experiment members** that re-execute end to end in ~60 seconds via
  `scripts/run_benchmark_suite.py`, emitting JSON, CSV, Markdown and figures.
- **`evidence/manifest.json`** hashing every artifact with its generating command, the
  repository revision, whether the tree was dirty, and the full compiler and package
  environment. `scripts/verify_evidence_manifest.py` reports OK / VOLATILE / CHANGED / MISSING /
  unlisted separately and fails on the last three, where VOLATILE means the bytes moved and the
  results did not.
- **`docs/validation_matrix.md`** — the twelve-component table: method, oracle, the bound the
  test asserts, the error actually measured, and the artifact. Two components are marked
  `partially validated` and say why.
- **60 numbered limitations** in `docs/limitations.md`, grouped by phase.
- **A 12-chapter technical report** (`paper/technical_report.pdf`) and **`CITATION.cff`**.

## Headline validation results

All worst-case, over every row of each benchmark, measured against a live oracle.

| Component | Worst measured | Oracle |
|---|---|---|
| Black-Scholes price, 2,464 comparisons | 3.46e-11 rel, 1.49e-13 abs | QuantLib 1.43 |
| Greeks (delta, gamma, vega, theta) | 5.12e-13 abs | QuantLib 1.43 |
| Put-call parity | 7.99e-15 | analytic identity |
| CRR convergence order | slope −0.99405 ± 0.00313 vs theory −1 | analytic BS limit |
| Monte Carlo z, pooled over 160 runs | mean ≤ 0.05, std 0.92–1.01 | analytic BS |
| CI coverage vs exact binomial band | 12/12 inside | combinatorial |
| Covariance estimators | 7.2e-16 rel / 7e-19 abs | NumPy, scikit-learn |
| Six portfolio solvers, 75 problems | objective 4.48e-9, weights 4.66e-7, budget 1.45e-12, bound violation exactly 0 | cvxpy, PyPortfolioOpt |
| Stress attribution and VaR decomposition | residual exactly 0.0 over 28 scenario-book pairs | accounting identity |

## What the release does not claim

- **No real-market result.** Every statistical claim runs on synthetic data whose truth is
  known. Nothing here licenses a statement about realised markets (#28).
- **No return forecast, no trading recommendation.** There is no expected-return model in the
  library; `expected_returns` is an input, and the optimiser is only as honest as the person
  who supplies it (#37).
- **Not faster than everything.** The C++ Monte Carlo engine is ≈8× a pure Python loop (four
  dated runs: 7.99×, 8.07×, 8.20×, 8.37×) and **0.42×–0.48× vectorised NumPy** for terminal-only
  payoffs — slower than NumPy, on the workload
  where NumPy is built to win. The artifact says so and the four recorded caveats explain why
  that is not the interesting case.
- **Two components are only partially validated.** Heston (our discretisation bias and the
  oracle's integration tolerance are not separable at 4.5e-3) and the bootstrap interval under
  clustering (0.693 coverage against 0.900 nominal — a real failure of the method, published
  as the finding rather than smoothed over).
- **Three CI lanes now run on `ubuntu-latest` on every push**, and the first real run earned
  its keep: the new benchmark lane passes with `--require-all` (no member may be skipped), and
  the long-standing build lane failed on a test that demanded bit-exact agreement with a
  transcribed price — glibc's libm is 1.7 ULP from Apple's. That was fixed, and is now
  limitation #59.

## Findings worth reading before the code

1. **Optimiser rankings do not invert under stress — but only because the books started far
   apart.** The two books were 20.8% apart in normal-times risk and the stress-induced spread
   is 16.8%, so no reversal was available. The *stress-sensitivity* ranking inverts completely:
   the minimum-variance book is the most stress-sensitive (6.11× against 5.23× for equal
   weight). That is Phase 6's conclusion seen from the other end.
2. **Estimating the covariance, not choosing the optimiser, is the dominant cost** — 1.13–1.26×
   the forward variance an informed solver would carry. A regime break costs 1.57–1.60× for
   every estimator, which is more than any estimator choice.
3. **A quantile is not a distribution.** A single-scenario stress set returns NaN for VaR and
   ES with a note, rather than reporting the one number as if it were a tail.
4. **Two silent bugs were caught by checks, not by review**: a beta vector sized from the
   delta block, which allocated exactly zero risk to a vega-only position (Euler residual
   −21,451 against a 355k VaR, no error raised); and a volatility multiplier that rescaled only
   the diagonal, silently halving every correlation when it doubled every sigma.

## Assets in this release

| Artifact | Contents |
|---|---|
| Source | full repository at this tag |
| `paper/technical_report.pdf` | 12 chapters, 37 pages, with an artifact index |
| `evidence/manifest.json` | SHA-256, generating command, revision and environment for every artifact |
| `benchmarks/suite/results/` | `suite_run.json`, `suite_headline.csv`, `suite_summary.md`, `validation_envelope.png` |
| `CITATION.cff` | software citation metadata |
| `docs/` | validation matrix, protocol, limitations, reproducibility, findings, integrity audit, 8 model cards, 11 phase reports |

## Reproducing this release

```bash
git clone https://github.com/Jackxiaozhiren/quantrisk-plus-plus && cd quantrisk-plus-plus && git checkout v1.0.0
uv sync --extra oracles && uv pip install -e .
uv run pytest -q && uv run ctest --preset dev
uv run python scripts/run_benchmark_suite.py --require-all
uv run python scripts/verify_evidence_manifest.py
```

See `docs/reproducibility.md` for what is guaranteed, what varies, and why.
