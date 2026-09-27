# QuantRisk++

> A Reproducible C++/Python Engine for Stochastic Pricing, Monte Carlo Simulation,
> Portfolio Risk, Optimization and Stress Testing.

**Current status: Phase 9 — Python Research API and CLI (v0.1.0).**
Implemented and validated: a C++20 numerical core (RNG discipline, statistics,
normal distribution), Black-Scholes-Merton pricing with continuous dividends,
analytic and finite-difference Greeks, a Cox-Ross-Rubinstein lattice for
European and American exercise, a Monte Carlo framework with antithetic and
control-variate estimators whose convergence rate and interval coverage are
measured rather than asserted, arithmetic/geometric Asian and barrier pricing
with a closed-form geometric-Asian oracle, a full-truncation Euler Heston
simulation validated against a semi-analytic engine, a market-risk layer
(historical/Gaussian/Monte Carlo VaR and ES, iid and moving-block bootstrap
intervals, Kupiec and Christoffersen coverage tests) whose size, power and
coverage are measured on synthetic data with known truth, a portfolio layer
(sample/EWMA/Ledoit-Wolf covariance, mean-variance with target return, max-Sharpe,
equal-risk-contribution and Rockafellar-Uryasev CVaR) where every solver carries a
certificate checked against its own inputs, and a stress layer that maps factor
shocks and deformed covariances onto those books, attributes the result per factor
and per position with residuals that must close, and measures its own linearisation
error against a full Black-Scholes re-pricing. The public data layer, research API
facades and CLI are specified in `docs/` but **not built yet**. An optional public-data layer (SEC EDGAR,
FRED/ALFRED, CFTC) is implemented in `quantrisk.data` with real committed fixtures, so the
core never depends on a network.

Numbers quoted here come from committed artifacts, regenerate them with the
commands in [Validation](#validation):

| Claim | Value | Artifact |
|---|---|---|
| BS price vs live QuantLib (2 464 comparisons) | worst abs 1.49e-13, rel 3.46e-11 | `benchmarks/quantlib/results/pricing_vs_quantlib.json` |
| Greeks vs QuantLib (delta/gamma/vega/theta/rho) | worst abs 5.12e-13 | same file |
| Put-call parity residual | 8.0e-15 on notionals <= 200 | `experiments/pricing_validation/results/summary.json` |
| CRR lattice order | fitted slopes -0.99 +/- 0.004 vs theory -1 | same file, `crr_convergence_slope` |
| Test suite | 190 C++ (CTest) + 310 Python (pytest) | `docs/phase_reports/phase-09-research-api.md` |
| Geometric Asian closed form vs QuantLib analytic engine | worst rel. error 5.5e-4 | `benchmarks/quantlib/results/path_dependent_vs_quantlib.json` |
| Barrier monitoring bias and its correction | 14.0 % raw discrete -> 1.0 % with BGK | same artifact |
| Heston (xi = 0) collapse to Black-Scholes | worst rel. error 2.1e-3 | same artifact |
| Heston vs `AnalyticHestonEngine` | worst rel. error 4.5e-3 (validation weaker than BS) | same artifact |
| MC error decay (fitted log-log slope, theory -0.5) | -0.614 ± 0.089, -0.585 ± 0.096, -0.507 ± 0.118 | `experiments/monte_carlo_convergence/results/summary.json` |
| 95 % / 99 % interval coverage vs exact Binomial band | 12/12 combinations inside the band | same artifact |
| MC z-scores vs QuantLib analytic (pooled, 3 methods) | mean ≤ 0.05, std 0.92-1.01, ≥ 96 % within ±2 SE | `benchmarks/quantlib/results/monte_carlo_validation.json` |
| C++ vs pure-Python Monte Carlo (measured, terminal-only) | 8.07x (46,210,785 vs 5,728,661 paths/s) | `benchmarks/performance/results/monte_carlo_speed.json` |
| Empirical VaR realised violation rate (synthetic, 200 blocks) | 5.014 % / 1.021 % against 5 % / 1 % nominal on t(3) data | `experiments/var_backtesting/results/estimator_convergence.csv` |
| Gaussian-fit VaR on the same t(3) data | wrong in opposite directions: 3.29 % at 95 %, 1.39 % at 99 % | same artifact |
| Kupiec size under a correct model (2 000 x 250 days) | 5.05 % rejection at the 5 % level, exact CI [4.13, 6.10] % | `experiments/var_backtesting/results/coverage_test_size_power.csv` |
| Clustered violations with correct frequency | Kupiec rejects 12.0 %, independence test 55.4 % | same artifact |
| Bootstrap coverage of the true VaR (nominal 90 %) | iid design 87.3 % on iid data; 62.5 % vs 69.3 % block design on GARCH data | `experiments/var_backtesting/results/bootstrap_coverage.csv` |
| Covariance estimators vs independent implementations | sample ≤7.2e-16 rel vs `numpy.cov(ddof=1)`; Ledoit-Wolf ≤7e-19 abs vs scikit-learn | `tests/python/test_covariance_vs_oracles.py` |
| Portfolio solvers vs cvxpy + PyPortfolioOpt (75 problems) | quadratic weights ≤2.4e-12, objective ≤6.5e-14 rel; CVaR objective ≤4.5e-9 rel | `benchmarks/pyportfolioopt/results/optimisation_vs_oracles.json` |
| Constraints on every solution returned | worst budget residual 1.4e-12, worst long-only violation exactly 0 | same artifact |
| Cost of estimating the covariance (synthetic, truth known) | 1.13x-1.26x the forward variance an informed solver would carry | `experiments/portfolio_optimization/results/portfolio_optimisation_study.json` |
| Shrinkage vs raw sample at a 40-observation window | variance ratio 1.218 -> 1.169, turnover 0.207 -> 0.138 | same artifact |
| Non-stationarity vs estimation error | windows crossing the regime break cost 1.57-1.60x for every estimator | same artifact |
| Stress attribution closes exactly | worst factor / position / decomposition residual 0.0 across 28 scenario-book pairs | `experiments/stress_testing/results/scenario_ranking.csv` |
| Euler VaR components vs a central-difference gradient | agree to 3e-10 against a 1e-6 bound | `tests/python/test_stress_vs_oracles.py` |
| Delta-gamma map vs full Black-Scholes revaluation | rel. error 1.3e-4 at -1 %, 5.4e-3 at -20 %, 0.49 at -40 % (non-monotone) | `experiments/stress_testing/results/linearisation_error.csv` |
| Stress sensitivity inverts the safety ranking | the min-variance book is the most stress-sensitive (6.11x against 5.23x for equal weight) | `experiments/stress_testing/results/stress_testing_study.json` |

## 30-second example

```python
import quantrisk

quantrisk.version()  # '0.1.0'
quantrisk.normal_cdf(0.0)  # 0.5

rng = quantrisk.Rng(seed=42)
rng.uniform01()  # reproducible in [0, 1)
rng.standard_normal()  # reproducible N(0, 1)
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
result.price, result.standard_error

from quantrisk.portfolio import PortfolioOptimizer
from quantrisk.risk import RiskEngine
from quantrisk.stress import ScenarioEngine
```

```bash
quantrisk validate    # 7 identity checks against the installed build
quantrisk benchmark   # timings measured on this machine, now
quantrisk demo        # the examples above, run end to end
```

## Install (developers, $0)

Configure through `uv run` so CMake finds the same interpreter the tests use:
a bare `cmake --preset dev` with no active virtualenv silently builds the
extension against system Python.

```bash
uv sync                      # create .venv (Python 3.12) + install deps
uv pip install -e .          # build C++ core + bindings (editable)
uv run pytest                # Python tests

uv run cmake --preset dev           # configure C++ (Release-with-debug)
uv run cmake --build --preset dev   # build core + tests
uv run ctest --preset dev           # C++ tests
```

## Validation

Three levels, defined in `docs/validation_protocol.md` and executed per phase:

* **Level 1 - analytical**: parity identities, degenerate limits, `u*d == 1`,
  the no-early-exercise theorem, analytic Greeks vs central differences with a
  Richardson error estimate instead of a tuned tolerance.
* **Level 2 - independent oracles, run live**: QuantLib 1.43, SciPy's normal
  distribution/quantile, and for the portfolio layer PyPortfolioOpt (SciPy SLSQP),
  cvxpy (OSQP/SCS) and scikit-learn. No oracle output is ever pasted into `tests/`.
* **Level 3 - statistical**: lattice convergence fitted on log-log axes with
  standard errors; rolling-origin portfolio cost measured against a forward
  covariance known in closed form.

```bash
uv run python benchmarks/quantlib/pricing_validation.py         # needs the oracles extra
uv run python experiments/pricing_validation/run.py
uv run python experiments/var_backtesting/run.py                # needs the oracles extra
uv run python benchmarks/pyportfolioopt/optimisation_validation.py
uv run python experiments/portfolio_optimization/run.py
uv run python experiments/stress_testing/run.py
uv run pytest -m oracle                                         # live-oracle tests only
```

## Limitations

`docs/limitations.md` carries 55 entries grouped by phase, and
`docs/project_scope.md` §9-§10 records status and the frozen public surface.
Release engineering — validation matrix, evidence manifest, technical report and tag — is specified but **not done**; the portfolio layer is long-only, single-period and ships no expected-return
model of its own, and the stress layer maps exposures rather than re-pricing
instruments.
