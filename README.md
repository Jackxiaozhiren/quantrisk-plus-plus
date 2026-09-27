# QuantRisk++

> A reproducible C++/Python engine for stochastic pricing, Monte Carlo simulation,
> portfolio risk, optimization and stress testing.

## What QuantRisk++ is

A numerical core for quantitative finance, written from scratch in C++20 and exposed to
Python, where the interesting claim is not how many models it contains but that every
number in it can be traced back to the script that produced it.

It holds twelve things: a Black-Scholes-Merton pricer, analytic and finite-difference
Greeks, a Cox-Ross-Rubinstein lattice, a Monte Carlo framework with antithetic and
control-variate estimators, Asian and barrier payoffs, a Heston simulation, three VaR/ES
estimators with bootstrap intervals, Kupiec and Christoffersen coverage tests, three
covariance estimators, six portfolio solvers, a scenario and stress layer with attribution,
and an optional public-data layer that never touches the core.

The three results worth reading are in [`docs/findings.md`](docs/findings.md).

It is not a trading system, not a market-data product, and not a forecast. It ships no
expected-return model, makes no recommendation, and has never been run against live prices.
Total monetary cost of building and validating it: $0.

## Why it exists

QuantLib, PyPortfolioOpt and SciPy already price options and solve portfolios well. What
they do not do is show their work: a library returns a number, and the question "how do you
know that is right, and where does it stop being right?" has no answer inside the library.

This project is an exercise in answering that question for a small surface area, and the
answer turned out to be more interesting than the models. Building it meant finding, and
writing down, the specific ways a plausible number goes wrong:

- A benchmark that agreed with PyPortfolioOpt to 5e-6 until it was noticed the comparison
  was measuring `clean_weights()`, which *rounds* to five decimals — so both sides were
  agreeing about rounding, not about optimisation. Against the raw weights the real
  agreement is 4.5e-9.
- A documentation line claiming the sample and Ledoit-Wolf estimators matched scikit-learn
  to 2e-15. scikit-learn's `EmpiricalCovariance` divides by `T`, not `T-1`, so the honest
  gap was 6.1e-6; against `numpy.cov(ddof=1)` it is 7.2e-16.
- A stress engine that allocated exactly zero risk to a position holding only a vega block
  (sensitivity to volatility, with no equity delta), because the beta vector was sized from
  the delta block and so came out empty. The Euler attribution still summed to a number and
  reported a residual of −21,451 against a 355k VaR. Nothing raised an error; the identity
  check did.
- A Monte Carlo path payoff that appeared to have a 100% linearisation error, which would have
  been an engine bug if it were real. It was not: a bound `std::vector` member returns a copy
  to Python, so `exposures.delta[0] = x` edits a temporary that is immediately discarded, and
  the exposure never reached the engine at all.

Each of those was caught by a check, not by reading the code. That is the argument for the
project: correctness in numerical finance is a property of your instrumentation, and the
instrumentation is the hard part.

## 30-second example

```python
import quantrisk

quantrisk.version()  # '1.0.0'
quantrisk.normal_cdf(0.0)  # 0.5

rng = quantrisk.Rng(seed=42)
rng.uniform01()  # 0.755155532954539   — reproducible, same seed, every run
rng.standard_normal()  # 1.3010803566749882
```

The research API is keyword-argument shaped, and every method delegates to the C++ core:

```python
from quantrisk import BlackScholes, MonteCarloEngine

model = BlackScholes(spot=100, strike=100, rate=0.04, vol=0.20, maturity=1.0)
model.call_price()  # 9.925053717274434
model.greeks().delta  # 0.6179114221889526

engine = MonteCarloEngine(seed=42)
result = engine.price_european_call(
    spot=100, strike=100, rate=0.04, vol=0.20, maturity=1.0, paths=200_000
)
result.price  # 9.990522972178022
result.standard_error  # 0.03372491930330562   — the analytic value is 1.94 SE away
```

The trailing digits of `call_price()` are the last place a library, not this project, decides:
`log`, `exp` and the normal CDF come from the platform's `libm`, so Linux/glibc prints
`9.925053717274437` where macOS/AppleClang prints `9.925053717274434`. That is 1.7 ULP — about
1e-14, and far below any tolerance that matters in finance. The test that guards this example
compares against the README in units of the last place rather than demanding bit equality, so
the documentation cannot silently pin itself to one vendor's math library.

```bash
quantrisk validate    # 7 identity checks against the installed build
quantrisk benchmark   # timings measured on this machine, now
quantrisk demo        # the examples above, run end to end
```

## Mathematical scope

The models, their assumptions and their measure are specified in
[`docs/mathematical_specification.md`](docs/mathematical_specification.md) and summarised per
subsystem in [`docs/model_cards/`](docs/model_cards/).

| Area | What is implemented | Measure |
|---|---|---|
| Pricing | Black-Scholes-Merton with continuous dividend yield; CRR lattice, European and American; geometric and arithmetic Asians; up-and-out / down-and-out barriers with Broadie-Glasserman-Kou continuity correction | risk-neutral |
| Simulation | GBM (exact log-normal transition), antithetic pairs, control variate with in-sample fitted beta; Heston with full-truncation Euler | risk-neutral by default, physical measure as a separate explicit call |
| Market risk | historical, Gaussian and Monte Carlo VaR and ES; iid and moving-block bootstrap intervals; Kupiec POF, Christoffersen independence and conditional coverage | physical, over a stated horizon |
| Portfolio | sample, EWMA-about-zero (RiskMetrics) and Ledoit-Wolf 2004 covariance; minimum variance, efficient frontier, max-Sharpe, equal-risk-contribution, Rockafellar-Uryasev CVaR | single period, long-only, fully invested |
| Stress | factor shocks in relative and absolute units, deformed covariances, delta-gamma P&L map, Euler attribution, level/dispersion VaR decomposition | either, declared per scenario |

The risk-neutral / physical separation is enforced in the code, not just the docs: pricing
and risk use different entry points, and `terminal_prices_physical` is a distinct function
precisely so a backtest cannot accidentally price under the simulation measure.

## Validation

Three levels, defined in [`docs/validation_protocol.md`](docs/validation_protocol.md):

* **Level 1 — analytical.** Put-call parity, `T→0` and `σ→0` limits, `u·d = 1`, the
  no-early-exercise theorem, the Euler attribution identity.
* **Level 2 — independent oracles, run live.** QuantLib 1.43, SciPy 1.18.1, scikit-learn
  1.9.1, NumPy 2.5.3, PyPortfolioOpt 1.6.0, cvxpy 1.9.3. No oracle output is ever pasted
  into a test as an expected value.
* **Level 3 — statistical.** Convergence rates fitted on log-log axes with standard errors;
  coverage against exact binomial bands; backtest size and power over thousands of
  replications on synthetic data whose truth is known.

[`docs/validation_matrix.md`](docs/validation_matrix.md) is the full twelve-component table:
method, oracle, the bound the test asserts, the error actually measured, and the artifact.
The four that carry a first reading:

| Component | Bound asserted | Worst measured |
|---|---|---|
| Black-Scholes vs QuantLib, 2,464 price comparisons | 1.0e-10 rel | 3.46e-11 rel, 1.49e-13 abs |
| CRR convergence order | slope −1 | −0.99405 ± 0.00313 (1.90 SE) |
| Monte Carlo z, pooled over 160 runs | mean 0, std 1 | mean ≤ 0.05, std 0.92–1.01 |
| Six solvers vs cvxpy + PyPortfolioOpt, 75 problems | per-problem 1e-11 to 1e-5 | objective 4.48e-9, bound violation exactly 0 |

Two rows in the full matrix are the ones to interrogate, because they are where a weaker project
would have stopped. The Heston comparison reaches 4.5e-3 relative, and that number is *our
discretisation bias plus the oracle's own integration tolerance* — recorded as
`partially validated` rather than rounded into a pass. The bootstrap interval coverage on
clustered data is 0.693 against a nominal 0.900, which is a real failure of the method and
not of the implementation; it is published as the finding.

## Benchmark

`uv run python scripts/run_benchmark_suite.py` runs all eleven members — four correctness
benchmarks, six statistical experiments, one performance benchmark — in about 60 seconds, and
writes JSON, CSV, Markdown and a figure under `benchmarks/suite/results/`.

The runner holds no number of its own. It executes each member's script, reads the headline
figures out of the JSON that script writes, by key path, and aborts if a path has moved. The
figure is drawn from those same extracted metrics rather than a second pass over the CSVs, so
the plot and the table cannot disagree.

The performance result is deliberately unflattering. On 200,000 terminal-only paths, one
normal per path:

- **≈8× a pure Python loop** — four dated runs gave 7.99×, 8.07×, 8.20× and 8.37×
  (45.5M vs 5.5M paths/s in the current artifact), and
- **0.42×–0.48× vectorised NumPy** — that is, the C++ core is *slower* than a NumPy
  `standard_normal` draw for this workload, on every run.

Both are in the artifact, and the second is the honest one: this benchmark exercises exactly
the case a vectorised generator is built for. The core's advantage is per-path state (running
maxima and averages for barrier and Asian payoffs) and `O(paths)` memory instead of
`O(paths × steps)`, neither of which the benchmark measures. The C++-to-Python ratio moves about 5%
between runs and the NumPy ratio about 14%, because the NumPy baseline itself ranged from
110M to 95M paths/s — so the ordering is the reproducible finding and the digits are not.
No single speedup figure here should be read as a constant.

## Architecture

```
cpp/       C++20 static library, namespace quantrisk, Eigen, Catch2
bindings/  pybind11 module `_quantrisk` with eight submodules
python/    quantrisk — facades, shims and the CLI; no formula is reimplemented here
```

Every number-producing routine lives in C++ and reaches Python through the bindings. The
Python layer is tested for this rather than trusted: a test asserts that each re-exported
callable's `__module__` is the extension, and an AST walk rejects any arithmetic, comparison
or loop in a shim module. A test that was originally "this module is not a `.py` file" — which
Phase 9's design made false — was replaced by that stronger structural check, not deleted.

Details in [`docs/architecture.md`](docs/architecture.md); the frozen public surface per phase
in [`docs/project_scope.md`](docs/project_scope.md) §10.

## Experiments

Six experiments, each answering one question with a distribution rather than a point. Each
writes its own JSON, CSV and figures, and each reports its own caveats in the artifact.

| Experiment | Finding |
|---|---|
| `pricing_validation` | CRR converges at the theoretical first order: slope −0.994 ± 0.003 against −1. |
| `monte_carlo_convergence` | Error decays at `O(1/√N)` (fitted −0.614 ± 0.089 against −0.5) and 12/12 confidence intervals land inside the exact binomial band. |
| `variance_reduction` | Antithetic and control-variate gains measured *out of sample*: MSE ratios 1.12× to 40.5× over 40 seeds, so the in-sample `beta` fit cannot flatter the result. |
| `var_backtesting` | Kupiec rejects at 5.05% under a correct model and 12.0% on clustered data, where the independence test rejects 55.4% — the discriminator works, and the unconditional test's blindness is quantified. |
| `portfolio_optimization` | Estimating the covariance costs 1.13–1.26× the forward variance an informed solver would carry; a regime break costs more than any estimator choice (1.57–1.60× for all three). |
| `stress_testing` | Optimiser rankings do not invert under stress — but only because the books started 20.8% apart and the stress spread is 16.8%. The *stress-sensitivity* ranking inverts completely: the minimum-variance book is the most stress-sensitive (6.11× against 5.23× for equal weight). |

## Reproducibility

```bash
uv run python scripts/run_benchmark_suite.py         # regenerate every artifact, ~60 s
uv run python scripts/build_evidence_manifest.py     # SHA-256 everything into evidence/manifest.json
uv run python scripts/verify_evidence_manifest.py    # prove nothing changed since
```

`evidence/manifest.json` records, for each artifact, its SHA-256, the command that generated
it (recovered from the artifact itself, not retyped), the repository revision, whether the
working tree was dirty, and the full environment — compiler, build type, and the version of
every oracle package. The verify script reports OK, VOLATILE, CHANGED, MISSING and UNLISTED
separately and exits non-zero on the last three. VOLATILE is the distinction that makes the
tool worth writing: a re-run changes an artifact's bytes — its timestamp, its commit, its
environment block, and for three files its wall-clock columns — without changing a single
result, and reporting that as CHANGED would make legitimate reproduction indistinguishable
from tampering.

Determinism is checked by measurement, not by eye: re-running the whole suite and diffing every
numeric leaf of the new artifacts against the committed ones returns zero differences, and the
C++ core is tested against a different RNG entirely. The three artifacts that do move are the
ones carrying wall-clock columns, and `docs/reproducibility.md` names them.

Everything is free. No paid data, solver, cloud service or API key is used anywhere; the
public-data layer needs only `FRED_API_KEY` if you choose to call FRED, and it reads from
committed real-response fixtures otherwise. A test asserts that no test in the data suite
touches a socket, by blocking `socket.socket` and running anyway.

## Limitations

[`docs/limitations.md`](docs/limitations.md) carries 59 numbered entries grouped by phase.
That file is the honest boundary of this project, and three entries matter more than the rest:

- **Nothing here has been tested against real markets.** Every statistical claim runs on
  synthetic data whose truth is known. No number in this repository licenses a statement
  about realised markets, and non-stationarity is out of reach by construction (#28).
- **The portfolio layer is long-only, single-period, and has no expected-return model.**
  `expected_returns` is an input, and the optimiser is only as honest as the person who
  supplied it (#36–37).
- **The stress layer maps exposures; it never re-prices an instrument.** Its error is Taylor
  truncation — 1.3e-4 at a 1% shock, 0.49 at 40% — and the scenario set itself has no oracle,
  because a management assumption is not a computable quantity (#43–48).

## Install (developers, $0)

```bash
git clone https://github.com/Jackxiaozhiren/quantrisk-plus-plus && cd quantrisk-plus-plus
```

Configure through `uv run` so CMake finds the same interpreter the tests use: a bare
`cmake --preset dev` with no active virtualenv silently builds the extension against system
Python.

```bash
uv sync                      # create .venv (Python 3.12) + install deps
uv pip install -e .          # build C++ core + bindings (editable)
uv run pytest                # the full Python suite (see docs/reproducibility.md)
uv run pytest -m oracle      # live-oracle tests only (needs `uv sync --extra oracles`)

uv run cmake --preset dev           # configure C++
uv run cmake --build --preset dev   # build core + tests
uv run ctest --preset dev           # 190 C++ tests, 546,943 assertions
```

Three CI jobs run on every push: lint and format, the full build with both test suites, and
the benchmark suite against live oracles with `--require-all` so a missing oracle fails the
job rather than quietly skipping four members. The third job is new and has not yet completed
on a GitHub-hosted runner; see `docs/reproducibility.md`.

---

<sub>Technical report: [`paper/technical_report.pdf`](paper/technical_report.pdf) — *Design
and Validation of a Reproducible C++/Python Stochastic Risk Engine*, twelve chapters.
Cite with `CITATION.cff`. Phase-by-phase reasoning in [`docs/phase_reports/`](docs/phase_reports/).</sub>
