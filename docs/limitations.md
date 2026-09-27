# Limitations

Everything this project does **not** do, does not prove, or does with a known
loss of accuracy. Entries are grouped by the phase that introduced them and are
never removed just because a later phase shipped.

## Phase 1 — engineering foundation

1. **Reproducibility is per-platform, not cross-platform.** `mt19937_64` and
   our Marsaglia polar transform are fully specified, but `log`, `sqrt` and
   `erfc` are not required to be bit-identical between libms. A recorded
   `(seed, N, parameters, git commit, compiler)` tuple reproduces bit-exactly on
   the platform family that produced it and to within floating-point noise
   elsewhere. Every artifact therefore carries `build_metadata()`.
2. **`inverse_normal_cdf` degrades in the extreme tail.** Above
   `|x| ≈ 37` (`p < ~1e-315`) the Halley correction overflows and the
   unrefined Acklam rational value is returned. Far beyond any confidence level
   used for VaR, ES or option pricing.
3. **Sorted-input helpers trust the caller.** `quantile_linear` and
   `mean_of_largest_sorted` take ascending-sorted data without re-checking the
   order (a full check would cost an `O(n log n)` sort per call in the hot
   paths). Higher layers must own the sort and are responsible for testing it.
4. **`Rng::standard_normal_vector` allocates.** Adequate for Phase 1's
   validation; the Monte Carlo engine needs a fill-into-buffer API before any
   performance claim is made (Phase 3).
5. **Build-time network dependency.** Catch2 `v3.8.1` and pybind11 `v2.13.6`
   are fetched by CMake at configure time. Tests and benchmarks are offline, but
   a fresh build needs the network once; there is no vendored copy.
6. **CI runs on `ubuntu-latest` only.** The development machine is macOS arm64
   and uses the same presets, but no CI job executes on macOS.
7. **`mypy` is advisory.** It is invoked in CI and its findings are reported as
   a warning, not a failure, until the typed Python facades exist (Phase 9).
8. **Eigen is not linked yet.** The Phase 1 core has no dense linear algebra to
   do; it is introduced where it is first needed (Phase 6) rather than scaffolded
   in advance.
9. **No model cards yet.** `docs/model_cards/` starts in Phase 2, when the first
   financial model exists.

## Phase 2 — deterministic pricing

10. **No term structure.** One flat `r` and one flat continuous `q`. Forward
    curves, discrete dividends and borrow costs are out of scope
    (`docs/mathematical_specification.md` §11); pricing them with this code would
    be a modelling error, not a rounding one.
11. **Lattice values are `O(dt)` approximations.** No Richardson extrapolation is
    applied, so a CRR price at N = 200 carries an error of the same order as the
    difference between two lattice parameterisations.
12. **Comparing two different lattices needs care.** QuantLib's
    `BinomialVanillaEngine(..., "crr", N)` is a different discretisation of the
    same dynamics. In the extreme corners of the benchmark grid (100 % volatility
    over five years on a coarse tree) the mutual absolute gap reaches ~0.46 on
    options worth tens of currency units, which is *smaller than each lattice's
    own error against Black-Scholes* — the honest reading of that row, and the
    reason `tests/python/test_pricing_vs_quantlib.py` asserts the normalised
    property instead of a raw threshold.
13. **Summary keys `lattice_error_ratio_*` are only informative away from
    cancellation points**, where one implementation's error against the analytic
    limit happens to be near zero (observed ratio range 1.2e-8 .. 766).
14. **Early exercise is biased low on a coarse tree** and the σ = 0 American
    value is found by searching 1001 exercise dates rather than solving exactly.
15. **`MarketParams.validate()` guards the domain, not the economics.** Negative
    rates and `r - q` far from zero are accepted because they are expressible;
    the lattice then reports a `p` outside `[0, 1]` in `note` instead of refusing.

## Phase 3 — Monte Carlo engine

16. **Single-threaded, and no variance-reduction technique beyond antithetic and
    control variates.** No quasi-Monte Carlo (Sobol / lattice rules), no Brownian
    bridge, no stratification or moment matching. A `1e6`-path run is a
    wall-clock measurement away from being slow, and the speedup claims are
    explicitly scoped to one thread.
17. **Intervals are normal (CLT) approximations**, not exact. Their empirical
    coverage is measured (12/12 combinations inside the exact Binomial band at
    95 % and 99 %), which is the justification - but for heavy-tailed payoff
    distributions the same reporting would need re-examination.
18. **Path-dependent pricing is memory bound**: `price_path_payoff`
    materialises `paths x (steps + 1)` doubles. There is no streaming buffer yet.
19. **Control-variate `beta` is fitted in-sample**, so the engine's own reported
    variance is mildly optimistic. Out-of-sample MSE ratios are reported in
    `experiments/variance_reduction/results/realised_error.csv` instead.
20. **No independent Monte Carlo implementation from QuantLib**: its
    `MCEuropeanEngine` could not be constructed with the installed SWIG bindings
    (every traits string rejected), recorded as `quantlib_mc_engine_used: false`
    in the benchmark artifact. The independent yardsticks that *are* used are
    QuantLib's analytic price (the exact limit) and a NumPy/PCG64 simulation.
21. **Performance baseline uses a different random stream** (`random.gauss`),
    so it measures cost per path, not equality of estimates.

## Phase 4 — path-dependent pricing and Heston

22. **Fixing and monitoring dates are year-fraction arithmetic only.** No
    calendar, business-day or month-end convention (`t_i = i T / M`), so the
    oracle residual for the geometric Asian is 5.5e-4 from day rounding rather
    than a pricing difference.
23. **Discrete barrier monitoring is biased upward** relative to continuous
    monitoring: measured 14.0 % at 250 dates on a 30-vol at-the-money up-and-out
    call. The Broadie-Glasserman-Kou correction reduces that to 1.0 % but is an
    `O(sqrt(dt))` asymptotic result for a single barrier on a lognormal diffusion,
    not an exact treatment.
24. **The monitoring grid and the diffusion grid are the same grid**, so `steps`
    cannot be refined for one purpose without the other.
25. **Heston validation is weaker than the Black-Scholes section.** The oracle is
    QuantLib's semi-analytic `AnalyticHestonEngine`, itself a quadrature, so the
    measured 4.5e-3 combines our discretisation bias with the oracle's
    integration tolerance.
26. **Full-truncation Euler is biased**; no moment-matched, QE/bilinear or exact
    CIR-transition scheme is implemented. The only exactness claimed is the
    `xi = 0` collapse to Black-Scholes.
27. **No Heston Greeks, no smile calibration, no path-dependent payoff under
    Heston**, and terminal/realised variance inherit the step discretisation.
28. **The risk layer is validated on synthetic data whose truth is known.** No
    real return series is used in `experiments/var_backtesting/`, so nothing there
    licenses a claim about realised markets, and non-stationarity is out of reach
    by construction.
29. **Empirical 99 % VaR at 250 observations averages two or three order
    statistics.** The estimate is dominated by which days happen to be in the
    sample; `quantile_standard_error` returns NaN rather than a plausible zero
    when the loss distribution has a tie (flat spot) at that level.
30. **The Gaussian VaR/ES estimators are wrong by construction for fat tails, and
    wrong in opposite directions at different levels**: measured realised rates on
    t(3) returns were 3.29 % at a 5 % nominal level (over-stated) and 1.39 % at a
    1 % nominal level (under-stated). They are kept as the reference case, not as a
    defensible production choice.
31. **Percentile bootstrap intervals are neither bias-corrected nor accelerated**,
    so coverage sits under nominal even where the design matches the data (87.3 %
    against a 90 % level at n = 500).
32. **Under GARCH-type clustering neither bootstrap design reaches nominal
    coverage** at n = 500: 62.5 % iid versus 69.3 % moving-block (exact intervals
    that do not overlap, so the block design genuinely helps and still falls
    ~21 points short). The `round(n^(1/3))` block default is a general-purpose rule
    and was not tuned for tail quantiles; a stationary bootstrap or a conditional
    model is not implemented.
33. **The bootstrap estimand is the unconditional quantile**, taken from a
    2 000 000-draw simulation. A daily re-estimated (conditional) VaR is a
    different estimand and its coverage is untested here.
34. **Coverage tests are marginal-frequency tests on a given VaR series.** They
    cannot validate the model that produced it, have no power against an error that
    preserves both the violation rate and its timing, are asymptotic (Kupiec is
    conservative at the 1 % cutoff because the statistic is a function of an integer
    count), and carry no multiple-comparison correction across the three tests. The
    clustered-simulation result shows the practical consequence: an iid-frequency
    test accepts a clustered model 88 % of the time.
35. **No Cornish-Fisher expansion, extreme-value tail fit, filtered historical
    simulation, or expected-shortfall backtest** (Bellini-Frittelli / Acerbi-Tasche
    style) is implemented.

## Phase 6 — portfolio covariance and optimisation

36. **Long-only and fully invested, and nothing else.** `sum(w) = 1`, `w ≥ 0` are the
    only constraints implemented. The max-position, sector and turnover constraints
    PROJECT_SPEC.md lists as later options are absent, so nothing here can express a
    realistic mandate.
37. **No expected-return model exists in this project.** `expected_returns` is an input
    the caller supplies. The Phase 6 experiment measures the consequence of the only
    available substitute — a window's sample mean — and it is not flattering: max-Sharpe
    is the worst of the four objectives on every forward metric (0.0186 against 0.0117
    forward volatility). Any use that treats a sample mean as skill inherits that.
38. **Single-period.** There is no multi-period rebalancing policy, and the turnover
    column in `estimator_out_of_sample.csv` is descriptive. No transaction cost is
    netted against return anywhere, so nothing in this phase is a P&L claim.
39. **EWMA is filtered about zero, not about the sample mean.** That is the RiskMetrics
    convention and it is asserted in the oracle test as a bridge rather than derived;
    the two definitions disagree whenever the mean is material, which for daily returns
    or a trending window it is not.
40. **The estimator ranking is a property of the tested process.** The Phase 6 DGP has a
    step change in factor volatility and *no* volatility clustering, which is precisely
    the case an EWMA filter is built for and did not get. `ewma` placing last on every
    window is evidence about this process, not a verdict against RiskMetrics.
41. **The simplex is dense, two-phase, and exponential in the worst case.** It was
    validated at ≤12 assets and 250 scenarios (a few thousand pivots, sub-millisecond).
    It is not a production LP and has no refactorisation, no sparsity and no warm start.
42. **Covariance instability is detected, refused and measured — not solved.** `solve`
    refuses below `rcond 1e-12`, and shrinkage measurably costs less forward than the
    singular answer it replaces (0.0086 against 0.0111 volatility on a 5-observation
    window of 8 assets). But the binding failure in the experiment is non-stationarity,
    which no estimator here addresses: forward slices crossing the regime break cost
    1.57–1.60x for all three estimators, against 1.07–1.22x inside a single regime.

## Phase 7 — scenario and stress testing

43. **Delta-gamma only, and its error is not monotone in the size of the move.** The
    stress layer maps exposures and never re-prices. Measured against a full Black-Scholes
    re-pricing of a three-strike call book, the relative error is 1.35e-6 at a 0.1 % fall,
    1.33e-4 at 1 %, then **falls** from 9.75e-3 at 10 % to 5.37e-3 at 20 % before exploding
    to 0.49 at 40 % — the cubic term changes sign through the strike region and partially
    cancels. A bound read off one point of that curve is wrong at another, so no single
    "validity range" is claimed.
44. **Scenario moves are gaussian.** No t-copula, jump component or stochastic volatility
    in the sampler. A convex book drawn through gaussian moves produces a right-skewed P&L
    — which the test suite measures and requires — and the engine models no further of it.
45. **The level/dispersion split of the VaR change telescopes only for a gaussian
    measure.** It is exact because the Gaussian quantile is affine in (mean, sigma). For a
    historical or Cornish-Fisher estimator the two legs would not add back to the total, and
    no such estimator is wired into the decomposition.
46. **No term structure.** One factor per asset class, so a rate shock is parallel by
    construction and a butterfly or steepener cannot be expressed. Credit is a single
    spread, not a curve or a ladder of seniorities.
47. **No reverse stress testing.** The engine answers "what does this shock do to the
    book"; it does not solve "what shock would produce this loss", which is the direction
    most supervisory use of the word actually means.
48. **The rank-stability result is a property of this fixture.** Across seven scenarios no
    book changed its absolute risk rank — but the four books started 20.8 % apart in base
    VaR while the largest stress-induced multiplier spread was 16.8 %, so the stability is a
    near miss, not evidence that optimiser rankings are robust to stress. Ranked by
    multiplier rather than by level, all four books do change rank under an equity crash.

## Phase 8 — optional public data

49. **No analysis in this project consumes the data layer yet.** The adapters deliver
    observations with provenance; no number in `docs/`, `experiments/` or `benchmarks/`
    cites EDGAR, FRED or CFTC. Wiring real data into a real study is not done, and nothing
    here implies it was.
50. **One filer per concept is exercised.** The ordered tag fallback in `SPEC_ITEMS` is
    tested against Apple (CIK 320193) and Madison Square Garden (CIK 1652044). A filer using
    an unusual tag lands in `Financials.missing`, which is the correct behaviour but is not
    tested across industries, foreign private issuers, or banks.
51. **`companyconcept` per tag, not `companyfacts`.** Six quantities means six requests per
    company, and there is no multi-company or industry screen. The bulk endpoint is not
    wrapped, so a broad fundamental study would need it.
52. **The CFTC fixture is a three-report-date excerpt**, enough to exercise date and market
    handling and nothing more. It is labelled as an excerpt in its own provenance, with the
    full archive's digest recorded separately, but it is not a positioning dataset and must
    not be used as one.

## Phase 9 — Python research API and CLI

53. **The facades cover the documented entry points, not the whole core.** Heston, Asian
    and barrier pricing and the generic LP solver are reachable only through the submodule
    functions (`quantrisk.monte_carlo.price_asian`, `quantrisk.stress.solve_linear_program`
    and friends), not through a facade with its own defaults.
54. **`quantrisk validate` checks seven identities, not the suite.** It is a smoke test that
    an *installed wheel* is wired up correctly — including that the compiled extension
    reports the commit it was configured at. Correctness at breadth is what the 190 CTest
    entries and 310 pytest tests are for, and `validate` passing does not imply they would.
55. **`quantrisk benchmark` measures one machine and compares against nothing.** Deliberate:
    the oracle comparisons live in `benchmarks/` with committed artifacts and provenance,
    and a CLI printing a second uncited figure beside them would create two sources of truth
    for one claim. The numbers it prints are valid only for the machine and moment it ran.
