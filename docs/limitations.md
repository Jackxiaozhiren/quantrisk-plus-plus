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

## Phase 5 — market risk estimation and backtesting

28. **The risk layer's *instrumented* validation is on synthetic data whose truth is known.**
    No real return series is used in `experiments/var_backtesting/`, so nothing there licenses
    a claim about realised markets, and non-stationarity is out of reach by construction.
    `experiments/real_data_risk_study/` (Phase 11) is the real-data arm and is where the
    empirical claims come from; it is narrower, because a sample has no independent truth to
    check against — see #61 and #62 and the `refusals` block in that artifact.
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

## Phase 10 — validation matrix, benchmark suite and release

56. **Resolved on first contact: the CI lane is proven on a runner, and the runner disagreed
    with the laptop.** `benchmark-suite` passes on `ubuntu-latest` in ~5m46s with
    `--require-all`, so all nineteen members execute against live oracles and none can be skipped
    silently. What the same runner caught was not in the new lane at all: the pre-existing
    `build-and-test` lane failed on a README assertion that demanded bit-exact agreement with a
    transcribed price, and glibc's libm is 1.7 ULP from Apple's. Local green said nothing about
    that. See limitation #59.
57. **The release is published, but it is a personal-portfolio release, not a distribution.**
    `v1.0.0` is a tag on a public repository with release notes, the technical report and the
    frozen evidence attached, and `CITATION.cff` now names the real URL. There is no package on
    PyPI and no DOI, so nobody can `pip install quantrisk` and a citation cannot be resolved
    through a registry. That is a deliberate boundary: packaging for distribution was not in
    scope, and an unclaimed name on an index is a worse outcome than an honest absence.
58. **The suite's member registry is hand-maintained.** The key-path guard makes a *renamed*
    headline field fail loudly, but a benchmark script that was never registered is simply
    absent from the suite and nothing notices — absence produces no output to check.
    `--list` against `find benchmarks experiments -name 'run.py' -o -name '*.py'` is the
    manual reconciliation.

## Phase 10 — cross-platform numerics

59. **The last one or two digits of a closed-form price are the platform's, not ours.**
    Black-Scholes evaluates `log`, `exp` and the normal CDF through the system `libm`. The
    same source and the same inputs give `9.925053717274434` on macOS/AppleClang and
    `9.925053717274437` on Linux/glibc — 1.7 ULP, about 1e-14. This was found by the CI run,
    not by review: a test that asserted the README's value bit-for-bit passed locally and
    failed on the runner. Any tolerance in this project is therefore set at least an order of
    magnitude above the platform spread, and `test_the_readme_black_scholes_example_runs_as_written`
    compares in units of the last place rather than demanding bit equality. Exact,
    platform-independent equality is claimed only where both sides come from the same binary —
    the Python-to-C++ consistency checks — and nowhere across compilers.

## Phase 10 — typing the extension boundary

60. **The generated stubs declare names, not signatures.** `python/quantrisk/<submodule>.pyi`
    lists all 151 public re-exports as `Any`, because the pybind11 extension publishes no
    callable signatures to Python and a stub asserting one would be an unverifiable claim about
    C++. Static tools therefore confirm that `quantrisk.stress.FactorSet` exists and that it is
    imported from a module that really exports it; they do not check how you call it. Argument
    correctness at that boundary is guarded by the runtime tests and by the C++ validation
    suite, not by the type checker. Real signatures would have to be generated from
    `cpp/include`, which is a larger project and deliberately not claimed here.

## Phase 11 — real-data risk study

61. **The real-data study's book is assumed, not held.** `experiments/real_data_risk_study/`
    scores three FRED series as risk factors against a fixed set of notional exposures that were
    chosen, not traded. The factor *moves* are observations; the *exposures* are an assumption;
    no number in that artifact describes a position anyone carried. Because VaR is positively
    homogeneous, the violation rates are invariant to scaling all three exposures at once — the
    script asserts that rather than claiming it — but they are not invariant to the *mix* of
    factors, and no sensitivity to the mix is published there.
62. **The real-data inputs are FRED's current revision, not the vintage published on each
    date.** The three series were selected because they are prints (a Treasury par yield, a
    breakeven rate, an index level) rather than revised macro aggregates, which removes the
    worst look-ahead exposure available without credentials. It does not remove all of it: a
    correction to a historical print would be invisible to this study, and closing that residue
    needs ALFRED vintages (`fetch_vintage` exists in `python/quantrisk/data/fred.py` and is
    unused by the study). The artifact states this in `look_ahead.residual_exposure`.
63. **The test count is a property of the environment, and a document quoting one number
    without saying which is now wrong. Both are measured now: `uv run pytest -q` gives the first, and
    `scripts/measure_offline_collection.py` gives the second by making the `oracles`-only packages
    unimportable in a child interpreter and collecting there, which is a measurement rather than the
    subtraction this item forbids -- `test_the_offline_test_count_is_measurable_before_the_runner`
    requires the gated modules to skip in that probe, so a probe that merely looked local would not
    pass it.** `uv run pytest -q` at HEAD gives 532 pytest tests with
    the `oracles` extra installed, and the same tree collects 463 tests without it — the CI lane
    runs a plain `uv sync`, and its own collected count for this revision is what the guard below
    compares against, where the earlier 353-test commit reported `284 passed, 4 skipped`. The two
    readings of that older commit are different quantities which happen to coincide:
    `--collect-only` counted 284 test items while the run reported those 284 as passed plus
    four *additional* module-level skip records, so 288 outcomes came from 284 collected items.
    The same shape holds at the 319-item revision — 323 outcomes from those 319 items — which
    is why neither number should be derived by arithmetic on the other. The gap is unchanged at
    69 cases inside four modules that gate on a module-level `pytest.importorskip` (for
    `sklearn`, `QuantLib` twice and `pypfopt`), and a module
    that skips at import reports **one** skip instead of the cases it holds. Those 69 are oracle
    comparisons a no-extra run never attempts. Both counts are honest; neither is "the" count.
    Added 2026-10-07 (Phase 27), because the simulation was finally run end to end rather than
    trusted: it now reproduces the lane -- `416 passed, 4 skipped`, exit code 0. It did not before.
    A guard that answers "what does this environment collect" by spawning
    `pytest --collect-only` in a subprocess escaped the parent's block, since here the distributions
    are installed and merely unimportable, so the parent read the offline figure while the child
    collected the online one (`1 failed, 415 passed, 4 skipped`). `_collect_in_this_environment`
    hands the same block down, which is what makes the probe a *simulation* of the runner instead of
    a parent-only trick. What remains different is platform state, not instrumentation: the runner's
    own tally read `414 passed, 5 skipped` against the 415 items its probe collected, one item
    skipping on Linux where it passes here.
    `v1.0.0`'s own documents quoted 330 and 319 for the same tag with no environment stated; 330 was
    the number that was right, 319 was stale, and the runner printed 261 passed with 4 skipped. The
    guard is `test_the_documents_that_count_python_tests_count_the_ones_that_exist`, and it asks
    which environment it is in before deciding which figure to check — because the first version of
    that guard asserted only the with-oracles number and promptly failed on the runner, which is the
    same mistake this entry describes, made again by the tool written to prevent it.

## Phase 11 — cross-platform evidence

64. **The frozen evidence is a record of one platform's last digits.** `evidence/manifest.json`
    byte-hashes 69 artifacts produced on macOS/AppleClang/arm64, and a fresh run of the real-data
    study on the Linux runner did not reproduce them bit for bit: `mean_realised_variance` came out
    0.0006136533643794436 against the committed 0.0006136533643794354, `mean_effective_assets`
    1.669464392772778 against 1.6694643927727641, the iid bootstrap standard error
    3796.595675506823 against 3796.595675506824 — spreads of about 1e-14 relative, which is
    limitation #59 propagating through 586 chained windows of differences, exponentials and quantile
    interpolation. Every integer, every boolean and the whole covariance ranking matched exactly, so
    no conclusion moved. The consequence is stated rather than smoothed: `verify_evidence_manifest.py`
    is a same-platform tamper check, and running it on a different libm would report CHANGED on
    result fields that are in fact the same result. CI therefore verifies *execution* on Linux (the
    `benchmark-suite` lane runs all nineteen members with `--require-all`) and *byte equality* only on
    the platform that produced the artifacts. `test_a_fresh_run_reproduces_the_committed_artifact_exactly`
    encodes the split: relative slack of 1e-12 on floats, exact equality on everything else. Making
    the chain platform-independent would require storing results at a stated precision rather than at
    full double resolution, which was not done here.

## Phase 12 — the remainder bound

65. **The higher-order sensitivities are closed forms, and the checks that validate them
    validate them against a finite difference of the order below.**
    `black_scholes_spot_derivatives` returns the third and fourth spot derivatives in
    closed form. Each is compared against a five-point central difference of the function
    one order beneath it, which catches a wrong differentiation (the stencil shares no code
    with the formula) but would not catch a wrong gamma, because both sides then inherit
    the same error. The independent anchor for the whole chain remains QuantLib on delta
    and gamma, and the third derivative is additionally checked against a difference of
    QuantLib's delta. What is *not* covered: neither new derivative is compared against an
    oracle that publishes one, because none of the reference libraries in this project's
    dependency set does. `docs/analysis/delta_gamma_error_bound.md` section 5 adds a
    second, independent route -- the fourth derivative is confirmed through its effect on
    the price surface -- but that is a consistency check between two closed forms and one
    price function, not an external reference.

66. **A finite-difference tolerance is a property of the step and the book, not of the
    algebra.** The stencil checks above agree to about 4e-11 at a step of 2e-3 and the
    tests assert 1e-9. At the intuitive smaller step of 1e-5 the *same* comparison
    disagreed by 3.6e-9 at the at-the-money strike, entirely from the stencil's own
    truncation-versus-round-off balance. Two consequences are recorded rather than tuned
    away: the step and the tolerance are justified next to each other in the test, and
    the arithmetic floor of the analysis itself -- near a relative move of 3e-5 for the
    book used there -- scales with the size of the position, so it has to be re-measured
    for any other book rather than reused as a constant.
## Phase 13 — the two-factor bound

67. **The bound covers the factor pair it names.** It bounds the equity-index × volatility-level
    interaction on a Black–Scholes European option book. The published `risk_off` scenario also
    moves rates by −50bp and credit by +100bp, each mapped linearly by a duration and a credit
    sensitivity; the convexity the map omits in *those* factors is a different set of derivatives
    and is not bounded anywhere in this repository. Nor does the result travel to the Heston book:
    the four third partials are closed forms of Black–Scholes, and the same argument there would
    need a numerically differentiated `g'''` and would inherit its error.

68. **"The error is quadratic" is a statement about the limit, and on this book the leading term
    is not the largest term.** The quadratic `vanna*h*k + 0.5*volga*k^2` is what survives division
    by `t^2` as the joint shock shrinks, and the fitted slope confirms it (1.9975 on the narrowest
    crash window). At the size the published scenario actually uses it is a minority: the mixed
    cubic `0.5*V_SSsigma*h^2*k` is 10.7× the net quadratic and 7.4× its absolute contributions and the quadratic alone predicts the
    error with the wrong sign. Worse, the ranking is book-specific for a reason that has nothing to
    do with the algebra: on the 90/100/110 book the K=90 and K=110 legs contribute −5089.09 and
    +5628.57 of vanna and nearly cancel, leaving an aggregate of 192.33, so the quadratic is small
    *here* by coincidence of the strikes. A concentrated book would rank differently, and the
    `dominance_counts` field of the artifact is the only honest guide.

69. **The direction along which the quadratic vanishes is predicted and not verified.** The form
    `k*(vanna*h + 0.5*volga*k)` is zero at `k/h = -2*vanna/volga`, which is a closed-form claim
    about a direction where the map should be unusually accurate. Its empirical counterpart is the
    root of the full error, whose displacement from the prediction is `O(t)` in the shock size: a
    bracket that locates it must have a width that shrinks with the very parameter being sent to
    zero. The scan shipped in `ridge_probe` finds the root at 0.87× the prediction at scale 1, at
    1.81× at scale 0.5, and not at all at scale 0.1 — which says something about the scan and
    nothing about the ridge, so neither agreement nor disagreement is claimed anywhere.

70. **No oracle in this project's dependency set publishes a vanna, a volga or a mixed third
    partial.** QuantLib 1.43 as installed here exposes `delta`, `gamma`, `vega`, `theta`, `rho` and
    `impliedVolatility` on `VanillaOption`, and stops there: `vanna`, `volga` and `speed` are not
    wrapped in its Python surface. The five new closed forms are therefore validated by finite
    differences taken along the *other* factor (Schwarz's theorem makes two such routes
    independent of each other), by exact identities derived from the homogeneity relation
    `vega = gamma*S^2*sigma*T`, and by call/put parity — which is L1 evidence plus a numerical
    route, not an L2 comparison. `docs/validation_matrix.md` row 15 records that distinction rather
    than letting the row read as benchmarked against a library.

71. **The independent check of the third directional derivative works only at published shock
    sizes.** Rebuilding `g'''` as the third derivative of the price along the ray needs a step
    whose round-off is amplified by `1/h^3` against a book value near 1.09e5. At a large ray the
    reconstruction agrees with the closed-form assembly to 3.9e-8 relative; on a ray where the
    third derivative is a handful of units it does not converge at any step, because the quantity
    being resolved is some orders of magnitude below the function it is differentiated from. The
    inclusion is therefore re-checked at four published-size shocks and not along the shrinking
    windows that carry the order claim, and `tests/python/test_two_factor_bound.py` says so beside
    the constant.

72. **Two convergence guards written this phase asserted an ordering that the numbers do not
    support, and the runner — not the laptop — showed it.** The first required each narrower fit
    window to beat the one before it; the second, after the first failed on Linux, required only
    that the narrowest beat the widest. Both passed here. Both failed on the runner, on the
    pure-spot ray, whose slope series was `3.004587 -> 2.991277` there against `3.006067 ->
    3.000915` here — every value within 0.009 of the theory number 3 on both platforms. The
    measurement that settles it is in the artifact's `fit_conditioning`: the error is the residue
    of subtracting book values near 1.09e5, whose double spacing is 2.418e-11, and at the tightest
    fit sample the pure-spot error is 3.098e-08, only **1281×** that floor, while the four joint
    rays' are 1.3e6–1.9e6 times it. So an ordering across the pure-spot windows compares noise,
    and no band was ever in question — the bands stayed at 2 % on the ratio and 0.15 on the
    narrowest slope, untouched. What changed is that an ordering is now asserted only for the rays
    whose conditioning makes it meaningful, and every window is published rather than summarised
    into a boolean. The lesson is not "CI is flaky": a stricter-looking assertion felt more
    rigorous and was in fact testing the platform, and two rounds of weakening it locally would
    have hidden that. Related: #59, #64, #71.

73. **The reproduction test for this experiment was itself the third instance of the cross-platform
    float mistake, and the runner caught it.** It re-ran the experiment in a temporary tree and
    compared the result against the committed artifact with plain equality — which passed here and
    failed on Linux (run `36416691279`) at `1.9998100833` against `1.9998084571`, 8e-7 relative in a
    *fitted slope*.
    The slack that works for the inputs to a regression does not work for its output: the tightest
    sample whose residual is 1281x the double spacing of the values subtracted to produce it
    (#71, #72) drags the fitted exponent around at the 1e-6 level. Fixed by a comparator that gives
    floats `1e-5` relative plus `1e-12` absolute and nothing else any slack at all — counts,
    booleans, strings and structure must match exactly — and calibrated by feeding it both a
    difference below the slack (tolerated) and eight kinds of real change (each rejected). That
    comparator did not hold either, and neither did its replacement; see #74 and #75. Recorded
    because the project already had limitations #64 and #71 saying this, and a freshly written test
    repeated the error anyway: a lesson filed is not a lesson applied to the next file.

74. **A fitted quantity is only reproducible to its own conditioning, and this repository learned
    that in three steps rather than one.** The first fix for the cross-platform failure in #73 gave
    floats `1e-5` relative slack — right for the crash ray's 8e-7 gap, wrong for the pure-spot
    ray's 3.2e-3 one, so the test went red a second time, on the runner again
    (`36417662618`: `.headline.slope_for_a_pure_spot_shock`, 3.000915 against 2.991277). The two
    gaps are not two magnitudes of one effect. The slack was then derived from the artifact's published
    `fit_conditioning` as `1 / sqrt(r)` on the ray whose tightest error sample sits `r` times above
    the double spacing of a book value, which gives 0.028 for the pure-spot ray at `r = 1281`, and
    nothing for any value that a regression did not produce; everything else kept `1e-5`. That too
    was calibrated in both directions — three measured Linux-to-macOS gaps tolerated, eight kinds of
    real change rejected — and the runner still went red twice more on it, because every one of
    those calibrations was a guess about which *fields* are ill-conditioned rather than a statement
    about which ones are (#75). The general form, since it bit three times: when a cross-platform
    difference appears, ask what the quantity's own noise floor is before choosing a tolerance,
    because a slack picked to make one observed gap pass is a guess about the next.
75. **The comparator exempted numbers by name, and names cannot be exhaustive: three further red
    CI runs ended in a check that compares shape, not value.** After #74's derived slack the
    reproduction went red on run `36518357703` at
    `.fit_conditioning.pure spot (k=0).error_at_tightest_sample`, `3.0978e-08` against `3.1182e-08` —
    a 6.6e-3 relative gap on a quantity the `1/sqrt(r)` rule did not cover at all, because it is not
    an output of a regression — and once more on run `36519230799` at
    `.slopes.pure spot (k=0)[0].standard_error`, where the committed `0.000605699476645428` and the
    Linux `0.0008428490503982969` differ by 39% of the committed value. Neither was a mis-tuned
    tolerance. A regression's standard error is the residual scatter of an already ill-conditioned
    fit, so it is a diagnostic *of* the looseness, and no name-based list of "fields whose
    conditioning limits them" can be complete: the one field that measures the looseness was itself
    the same cancellation residue, and `standard_error` does not contain the word `slope`.

    The fix is categorical. The experiment now ships `reproduction_policy.conditioning_limited`
    in the artifact and the test reads it from there, so the declaration lives with the code that
    knows which numbers it fitted; inside those families the reproduction comparison checks
    **shape** — key sets, list lengths, types — and keeps integers, booleans, strings and verdicts
    exact even there. The values are still proved, just not against one laptop: the copy exits 0
    only if every published slope sits in the experiment's own band, because it raises rather than
    writing an artifact, and `test_the_joint_error_is_quadratic_where_the_single_factor_error_is_cubic`
    re-derives the order-2-versus-order-3 claim in the *test's* environment over scale ranges the
    experiment never uses. What is deliberately given up: a slope that is in-band on Linux and
    in-band here need not agree, and this test will not say so. The comparator was falsified in
    both directions again — eleven mutations, and each demanded outcome was the one obtained: two
    family values tolerated, a family key, list length, type and an in-family integer count each
    rejected, and off-family floats rejected at 1e-3 while tolerated at 1e-9. Recorded because the
    durable rule is about *who owns* a reproducibility exemption: a test that decides field by
    field which outputs are comparable is re-guessing the numerics it is supposed to be checking.

76. **A guard that checks a figure appears in the artifact cannot see that the prose paired it with
    the wrong denominator, and this repository shipped that in eleven documents and a published
    release.** The artifact's `headline.largest_cubic_over_quadratic` was 7.408, computed against the
    quadratic's two contributions **summed in absolute value** (`|−173.10| + |961.06| = 1134.15`),
    while every sentence quoting it printed the **net** quadratic `+787.96` — what a correction would
    actually subtract — and said "7.4× the entire quadratic". Against that net the ratio is **10.66**.
    The digits were never wrong and the figure guard was never red: it asserted `"7.4" in artifact and
    "7.4" in prose`, which is true of a sentence whose noun phrase names a different number. The claim
    reached `README.md`, `docs/findings.md`, the analysis note, the validation matrix, a model card, the
    interview notes, the phase report, the release notes, two audit findings, the paper and the body of
    the published `v1.3.0` release. Fixed by removing the ambiguous name: the artifact now publishes
    `largest_cubic_over_net_quadratic` (10.66), `largest_cubic_over_quadratic_magnitudes` (7.41), and
    both denominators as their own fields, and the test recomputes both ratios from the core and
    requires each document to name the denominator beside each figure. The general form: a
    provenance check on *digits* certifies the transcription, not the *reading* — so when a quantity
    is a ratio, the denominator belongs in the field name, not in a sentence someone wrote beside it.
    Related: #58, #66, #75.

77. **A figure whose owner is prose goes stale silently, and a regression's standard error is not a
    bound on accuracy.** `docs/analysis/delta_gamma_error_bound.md` shipped with no test reading it,
    and writing that test in Phase 14 turned up three defects in it. (a) The cubic-crossing spot was
    quoted as `94.5456` with a `5.4544 %` down move; the artifact publishes `94.5487358657606` and
    `0.05451264134239392`, i.e. `94.5487` / `5.4513 %` — and the note's pair was *internally*
    consistent (`100 − 5.4544 = 94.5456`), which is exactly why a reader could not spot it. (b) The
    headline fitted slope `2.996188` with standard error `0.044006` belonged to a pooled 6-point fit
    that the experiment does not compute, so nothing in the tree owned the pair and no change to the
    artifact could ever have flagged it. (c) The sentence built from it — a deviation of
    `−0.087 standard errors` from theory 3, offered as agreement — misreads what a standard error
    measures: the scatter of the residuals, not the accuracy of the estimate. Over a window whose
    residuals carry the `δ⁴` mixture at one end and the cancellation noise of §6 at the other, the
    error is systematic, and the artifact's own widest window sits **52 and 59 standard errors** from
    3 in the down and up directions while still converging monotonically toward it. The note now
    quotes the five published windows as a sequence, which is what the artifact actually claims
    (`slope_converges_to_theory_as_the_window_shrinks`), and says plainly that many-standard-errors
    from theory is a property of the `se`, not a refutation of the cubic. Found while writing the
    guard, not before: the same sweep also caught `21.1446` — a truncation of the predicted zero —
    printed in five documents beside `21.1447` — the rounding — in two, and all seven are now the
    rounded value. Closing the class: `test_every_figure_the_note_quotes_is_owned_by_the_artifact`
    re-formats each figure from the artifact and requires it in the note, and
    `test_every_analysis_note_is_guarded_against_the_numbers_it_quotes` fails if any file in
    `docs/analysis/` has no test that reads it. The same blind spot turned out to exist in the
    present tense for the performance artifact, which is worse: `speedup_vs_pure_python`,
    `speedup_vs_numpy` and `results_seconds` are volatile *by declaration*
    (`quantrisk/experiments/evidence.VOLATILE_KEYS`), so the manifest reads any re-run of that file
    as VOLATILE and certifies nothing about its ratios — while `README.md`,
    `docs/validation_matrix.md`, `docs/interview_defense.md` and the paper all quote those ratios as
    the artifact's own. The freeze behind v1.3.0 measured `7.909×`; the matrix described the same
    file as `8.0–8.4×`, and the README quoted "45.5M vs 5.5M paths/s in the current artifact" for a
    file reading 45.6M and 5.8M. Ranges written from a handful of runs were also too narrow: the
    thirteen committed measurements of that file span `7.77×`–`8.70×` and `0.42×`–`0.51×`, not the
    `5%` and `14%` spreads previously documented, and one re-run taken while another process held a
    core read `7.35×` — outside every range the documents had ever printed. `docs/reproducibility.md`
    now owns the range and prints the command that recomputes it from `git log`; the point figures
    are checked against the artifact by
    `test_documents_quote_the_performance_figures_the_artifact_actually_holds`. The ranges are
    checked two ways, because the first version of that check was itself wrong:
    `test_the_documented_speedup_ranges_contain_the_current_measurement` pins the band and requires
    the current artifact to sit inside it and the documents to state it, while
    `test_the_documented_speedup_ranges_match_the_committed_history` requires the pinned band to
    equal the min/max over the artifact's git history and *declares a skip* when the clone does not
    carry that history — which was the CI case at `actions/checkout` depth 1, where the first
    version derived a `0.45–0.45` spread from the single visible revision and went red for a reason
    that had nothing to do with the documents. **Amended 2026-10-12 by Phase 33:** the pytest lane now
    fetches `fetch-depth: 0` with tags, so that guard, the release-tag enumeration and the citation's
    `date-released` comparison are checked on the runner rather than only on the machine that froze the
    artifact — measured as `429 passed, 8 skipped` at depth 1 against `432 passed, 5 skipped` at depth 0
    on the same tree (`docs/integrity_audit.md` finding 65). The skip is left for a reader's own shallow
    clone, and its wording no longer names CI. `test_the_performance_guards_are_not_vacuous`
    multiplies the artifact by 1.5, narrows one band by hand, and asserts a one-measurement band can
    never equal the pinned one. So a re-run of the speed benchmark now obliges a documentation edit,
    which is the point: the alternative was a green gate over a stale claim. The class then
    reappeared one level up: `docs/interview_defense.md` Q11 restated the Python test counts as
    "386 … and 295 without them" while its own headline two lines above said 410 and 341, because
    the count guard matches the wordings it knows — a restatement phrased a fourth way is a figure
    with no owner inside a sentence that looks checked. Both spellings are policed by that guard now,
    which is the rule restated: policing a number means policing every spelling of it.
    2026-10-08 and the v1.8.0 re-freeze on 2026-10-09 moved the *pure-Python* edge twice more:
    twenty-two committed measurements now span `7.77×`–`10.31×` (32.6%) and `0.42×`–`0.51×` (20.8%).
    Three clean idle runs of the same script wrote `8.378×` / `0.5656×`, `8.877×` / `0.4597×` and
    `10.306×` / `0.4950×` — a 16% swing between the last two, with no contention recorded in either,
    and only the reading that was committed can be what the documents quote, because the tree holds
    one artifact rather than a sample. A third run that contended with a second concurrent copy of the suite
    wrote `4.007×` and `0.3588×`, below every edge this repository has ever printed; that artifact was
    restored rather than committed. The bands are therefore the spread of *committed* runs, and a
    reading outside them is evidence about the machine, not about the engine — which is why
    `docs/reproducibility.md` owns the range and prints the command that recomputes it, and why the
    point figures are quoted from the artifact rather than from memory.
    Related: #63, #76, #71.

78. **The re-struck-gamma recommendation is now measured, and its scope is the grid, not the map.**
    `v1.3.0` closed finding 6 with a priority — re-strike gamma at the shocked volatility rather than
    add vanna and volga — and `experiments/restrike_gamma_map/` measures it against revaluation.
    Three limits travel with the measurement. (a) It is not uniformly safer: 45 of the 120 swept cells
    with a volatility move are no better, and 20 are at least twice as wrong (worst factor 142),
    because those cells' shipped-map error was *smaller than the term the recipe removes* — two
    third-order pieces cancelling, and the correction spending the cancellation. (b) The prediction
    that explains them, the zeros of the third-order truncation of the base map's error, is gated only
    within `|delta| <= 0.05`, where it locates the priced zeros to 0.0002-0.0024 in vol move; past
    that the drift grows to 0.093 at `|delta| = 0.30` and the truncation predicts zeros the map does
    not have. A third-order truncation is an argument near the base market, which is where the
    published scenarios live. (c) Nothing here changes `stress.run_scenario`: it ships a two-factor
    delta-gamma-vega map, row 12 of `docs/validation_matrix.md` says so, and a user who needs the
    joint residual controlled has to re-value the book rather than re-strike exposures at the call
    site. One three-strike ladder, one maturity, one base volatility, and no estimate of how the
    ranking of the four maps changes for a book whose gamma moves the other way in volatility — the
    artifact's `refusals` block is that list, and `docs/analysis/restrike_gamma_map.md` §7 argues it.

79. **The fourth-order crossing radius is a statement about place, not amount, and about this book.**
    `experiments/fourth_order_crossing_map/` extends v1.5.0's column truncation to order four with the
    mixed fourth partials this release ships, and the result has three edges. (a) What widens is the
    *location* of the crossings: worst nearest-zero distance 0.00162 inside `|delta| <= 0.15` against
    the cubic's 0.01887. What does not widen is the accuracy of the *amount* — on `risk_off` the
    quartic estimate is still 16.2 % off, now from the other side, and on the shallow ray at full
    shock size its residual is 1.38x the cubic's. Any reader who wants a predicted P&L still has to
    re-value the book. (b) The ordering law is gated over `1e-3 <= scale <= 3e-1` because below
    `1e-3` the residuals are differences of book values near 1.09e5 at the arithmetic floor, and a fit
    that reaches down there returns 2.46-4.30 instead of 4.73-5.01; both fits are in the artifact so
    the window can be audited. (c) Fourteen zeros are found by both truncations against the priced
    error's thirteen, but the quartic's false crossing is a different one (`k = 0.164` on the
    `delta = +0.10` column), so neither truncation is a root counter. (d) One *verdict* in that
    artifact is decided by noise rather than by the model: the count of rays whose residual-ratio turns
    back upward at the arithmetic floor compares two values that are themselves the floor, so the
    producer declares `headline.fits` and `rays` under
    `reproduction_policy.noise_decided_verdicts` and a fresh platform is not held to the number. The
    committed artifact shows four of four on this machine, and what the documents may carry is the
    floor's effect on the fit, never the count. (e) The exemption is declared as three *families*
    (`rays`, `columns`, `headline.fits`) rather than as field names, after three CI rounds each went red
    on a conditioning-limited field a name list had not named; inside `columns` the counts and labels
    stay compared by value, and a guard test plants both directions — a perturbed fit that must be
    tolerated and a perturbed zero count that must be caught — so the exemption is a checked property
    (audit finding 45). One three-strike ladder, one maturity, one base volatility: limitation #81
    measures the radius on four further books and finds the direction transfers while this ladder's
    `0.05 -> 0.15` does not, and the *amount* at published size stays this book's 16.2 %.

80. **The extension-surface claim covers every namespace-scope function the core declares; the reasons
    inside it are still prose.** `tests/python/test_extension_surface_parity.py` reads
    `cpp/include/quantrisk/**/*.hpp` and requires each namespace-scope function declaration to be
    registered in `bindings/python_bindings.cpp` or disclaimed at its own declaration by a `// python:`
    marker. Phase 17 keyed that claim on `[[nodiscard]]` and then inventoried what the attribute missed:
    seventeen declarations across four headers -- the statistics primitives, the normal
    PDF/CDF/quantile, the version pair, the three covariance estimators and `stats::quantile_linear`.
    Phase 19 marked every one of them, because a numerical core that returns a value means it, so the
    attribute and the population are now the same set: the surface holds 110 namespace-scope
    declarations and 102 distinct names, and 25 of them are disclaimed rather than bound, each
    disclaimer's `via X` route checked against what the bindings really declare and each orphan stale
    exemption caught. Three things stay outside the claim, listed because no guard reaches them: a
    *class member* is not a namespace-scope entry point and is not covered -- the parser blanks type
    bodies for exactly that reason, which is also why `struct Summary::total()` cannot sneak in; the
    reason text of a disclaimer is prose, so the guard verifies the route it names and not whether the
    justification is still the true one; and a function declared only inside a `.cpp` is invisible to a
    header scan, which is finding 43's blind spot one file type over rather than a closed one.

81. **A crossing radius transfers in direction, not in size, and the mechanism this phase assumed
    of it is wrong.** `experiments/second_book_crossing_map/` measures v1.6.0's fourth-order radius
    on five books instead of one, and the answer has three parts. (a) The *direction* transfers: on 5
    of 5 books the quartic's contiguous radius is at least the cubic's, and on 5 of 5 its worst
    nearest-zero distance inside the cubic's own radius is the smaller. The *magnitude* does not: the
    widening factors are 1.3, 2.0, 2.5, 3.0 and 3.0, and the cubic radii themselves are 0.02, 0.05,
    0.05, 0.10 and 0.15. `0.05 -> 0.15` is one ladder's pair of numbers, and `docs/release_notes_v1.6.0.md`
    carries a dated correction so the sentence it published is read as that. (b) The set was built to
    span the order-four-to-three ratio -- 0.015 to 3.887, a factor of 254 -- on the expectation that a
    small fourth-order piece leaves an added order little to remove, and the measurement rejects that
    ordering: the book with the smallest ratio tied the widest factor. Five books is too few to look
    for a better mechanism, so none is claimed; the ratio is published per book so a later book can be
    checked against it. (c) A radius is decided by the worst column in its range, and a column only
    counts if the priced error crosses zero in it. The short-dated book has 6 of its 12 columns with a
    crossing, and the long-dated book's quartic radius sits on the swept edge at 0.30, where "no column
    failed" is weaker than anywhere else; both are flagged in the artifact rather than rounded down.
    What makes the four extra books a measurement rather than a re-tune is the equality gate: the
    re-derived machinery must be bit-identical to the two shipped experiments on the published book --
    ten coefficients, both truncations and the engine P&L over 30 joint moves, all four differences
    exactly zero -- so nothing here was adjusted to make a book cooperate. What remains unproven is
    that any of it is a *bound*: no independent implementation prices a fourth-order column, and the
    transfer claim is self-consistency of one truncation across five books, not agreement with another
    library.

82. **The fifth-order partials are shipped and checked, and nothing about the crossing map at order
    five is.** `pricing.black_scholes_mixed_fifth_derivatives` returns the six mixed partials of
    total order five, the terms the order-four truncation of `docs/analysis/fourth_order_crossing_map.md`
    leaves behind. Three things are true of them and one is deliberately not. What is true: (a) the
    closed forms are *derived*, not typed -- each is `P * S^(1-n_spot) * T^(n_vol/2) * R(d1, v) / v^4`
    for a numerator polynomial obtained by symbolic differentiation of the price function and then
    re-obtained by Richardson refinement at independent precisions, so the six `R` are what the
    algebra produced rather than what a transcription of it looked like, and that derivation is a
    command rather than a sentence: `scripts/derive_fifth_order_partials.py` parses the monomial sums
    out of `cpp/src/pricing/black_scholes.cpp`, forms the quotient of the symbolic derivative by the
    prefactor the header claims at 60 markets spread over the `(d1, v)` plane, and reports a worst
    relative disagreement of 8.7e-58 at 60 digits. Since Phase 24 that command is executed by
    `tests/python/test_fifth_order_partials.py::test_the_derivation_command_agrees_at_the_precision_floor`
    -- `sympy` is a dev-group dependency, so the gate runs the identity instead of offering it to a
    human -- and the same test requires the two documents quoting 8.7e-58 to agree with each other and
    with the run's order of magnitude. No coefficient is adjusted anywhere in that check,
    so an agreement sitting at the working-precision floor is the two sides being one analytic
    function rather than a curve through points; its second
    part recomputes the fields by nested numerical differentiation at 60 digits and meets the
    extension's float64 output at 4.6e-15, the noise floor of the format; (b) the checks reach them
    through quantities the core shipped *before* this phase -- ten five-point slope routes over the
    nine-rung ladder in `tests/cpp/test_black_scholes.cpp`, where the worst of the ninety comparisons
    sits at 1.9e-3 of its own band, and the same ten routes over five markets in
    `tests/python/test_fifth_order_partials.py`, where the loosest is 1.5e-4 relative against a
    `1e-3` band -- plus exact call/put parity and the degenerate limit; and (c) one route touches no
    mixed struct at all: the multinomial contraction of the six partials against five *nested*
    differences of `black_scholes` itself, which QuantLib prices (row 1). What is not: no independent
    library publishes a fifth partial, so five of the six fields are anchored by stencils of this
    project's own fourth-order family, and a slip that lives in that family would be inherited by the
    route meant to catch it -- only the contraction route reaches the numerators through the price
    alone, and it is round-off limited rather than exact, at 6.7 relative on the finest rung tried and
    4.8e-3 on the widest. The derivation script's second part does reach the numerators through the
    price, at high precision, but only at four markets and through the compiled extension, so it is a
    spot check on the shipped pipeline rather than a ladder over the surface. The two `min`-over-rungs assertions are therefore weaker than a fixed-step
    check would be, and the rungs that fall outside the band (the spot routes reach 1.2e-3 to 9.2e-2
    at a 1 % step) are reported here instead of asserted away. Finally, and most consequentially:
    shipping the order-five terms buys no statement about the stress map. The experiment that would
    use them -- whether the crossing radius widens again at order five, on whose answer §4 of
    `docs/analysis/second_book_crossing_map.md` says a sixth book should be checked against the
    published distances rather than retold -- was designed and then deliberately not run this phase,
    because a core capability and the measurement that consumes it are separate claims. The row is
    `validated (L1 only)` and the crossing question stays open in the same sense row 19 left it: this
    phase added the arithmetic, not the answer.

83. **Order five widens the radius on two books of five, and the set that was chosen to explain
    widening explains it no better than before.** `experiments/fifth_order_crossing_map/` adds the six
    mixed fifth partials to the same column truncation, on the same five books, under the same
    contiguous paired-magnitude rule at v1.5.0's own 0.005 tolerance, imported from the Phase 18
    experiment rather than restated. The result has three parts and only the first is a yes. (a) The
    radius grows again on 2 of 5 books -- the published ladder `0.15 -> 0.20`, a factor of 1.33 where its
    own cubic-to-quartic step was 3.00, and the deep out-of-the-money ladder `0.20 -> 0.30` -- and does
    not on the other three. (b) Inside the quartic's radius the quintic is the closest of the three
    orders to the priced crossing on 5 of 5 books, which is the same direction Phase 18 found one order
    earlier. (c) The ratio of the order-five spot piece to the order-four one spans 0.057 to 0.588, and
    it orders the outcome no better than the order-four-to-three ratio did: the smallest ratio in the set
    produced the largest widening, the second smallest produced none, and the largest sits on a book
    whose radius was already at the swept grid edge, so it proves nothing either way. Two of the three
    "unchanged" books are therefore not evidence of anything, and the artifact flags them
    (`quintic_radius_at_grid_edge`) instead of counting them as results; the only book that is both
    resolvable and unmoved is the in-the-money mirror.

    What the measurement is not. It is not a bound and not a statement about size: the amount of the map's
    error at published scale is untouched by this phase, and the base map is still 16.2 % off on
    `risk_off` after the quartic. It is self-consistency of one truncation family measured against a
    revaluation of the same book, with no second implementation on the other side -- the fifth partials
    have no oracle, and limitation #82 keeps their validation caveats. The distance columns, the
    closer-verdict built from them, the contraction errors and the ratio are declared
    `conditioning_limited` because they are roots and quotients of subtractions of book values near 1e5;
    what is gated by value is the counts and the radii, which are grid points. The multinomial
    contraction is checked against five nested differences of the revaluation at `1e-05` to `8e-04`
    relative on the widest rung tried and a `5e-2` band, with finer rungs degrading to `3e-02` on the same
    ray because five nested divisions by the scale are round-off dominated; the run publishes the error at
    every rung rather than keeping the best, and the independent test re-derives it on four rays the
    producer never evaluates. Finally, one defect this phase found was in its own refusal: the first
    version of `check` judged each radius by the worst column inside the *quartic's* range and rejected
    the published ladder's cubic radius of 0.05 for a column at 0.15 that radius never claimed to cover.
    A gate that reads the wrong range rejects correct results and accepts incoherent ones, so it announced
    itself by firing on a book that was fine; `check()` now reads each order against its own radius and the
    test pins both directions (audit finding 51).

84. **The report's prose is guarded figure by figure, and a false sentence that carries no
    figure is caught only where a phase wrote a guard for that sentence.**
    `paper/technical_report.tex` restated the frozen manifest's size as 69 artifacts, 6,208,835
    bytes and 40 statistical experiment files -- exactly `evidence/manifest.json`'s `totals` at
    `v1.1.0` -- and shipped that sentence in six releases, `v1.2.0` through `v1.7.0`, while its own
    headline paragraph two pages earlier printed the current 94. One document contradicting itself,
    because no reader compared the two statements. The same document said, in the present tense, that the fifth-order
    crossing experiment "was specified and then deliberately not run", which Phase 20 wrote as a
    true sentence, Phase 21 refuted by running it, and nothing noticed, because every guard over
    that file compares numbers and a claim that an experiment did not happen is not a number. Three
    guards own the restatements now: the manifest sentence is compared with
    `evidence/manifest.json`'s `totals`, the report must name the directory of every experiment the
    suite registers, and the order-five paragraph's five figures are re-derived from
    `experiments/fifth_order_crossing_map/results/fifth_order_crossing_map.json`. What is *not*
    covered is any narrative claim outside those three shapes -- a sentence that misdescribes a
    method, a scope or a refusal without printing a number or a registered path is still only
    caught by a reader, and the released `v1.7.0` PDF carries the stale sentences this item names
    because the tag predates the fix. Recorded as audit finding 55.

85. **The C++ assertion and case totals have an owner, and it needs a build to read them.**
    `548,368 assertions in 203 test cases` is quoted in the README, `docs/reproducibility.md`,
    `docs/interview_defense.md` in two of its own phrasings and `paper/technical_report.tex`.
    Finding 49 recorded why that pair survived four releases unowned: CTest counts tests, not
    assertions, so no CTest-side guard could see them. `test_documents_that_count_the_cpp_assertions_count_the_binarys_own`
    now runs the compiled Catch2 binary, takes its summary line, requires the `TEST_CASE(` blocks in
    `tests/cpp/*.cpp` to equal the case total the binary reports, and compares each document with
    both numbers — two producers, not one quoted by five. It skips where nothing has been built, which
    is the residue: in a source-only checkout the guard is silent rather than wrong, and the CI lane
    that runs pytest immediately after `cmake --build` is what makes it live. The CTest entry count is
    not asserted there because `test_documents_that_count_the_cpp_tests_agree_with_the_build` already
    owns it, and one number is allowed exactly one owner. Phase 25's finding is audit finding 57.

86. **The Heston probes have no frozen artifact, so two of the report's numeric sentences are
    exempted by hand.** `paper/technical_report.tex` states the ξ=0 collapse check at 200,000 paths
    over 250 steps and the step-refinement check at 20, 80 and 320 steps. Neither number is read
    from anything `evidence/manifest.json` hashes: there is no Heston file under `benchmarks/` or
    `experiments/` at all, and the only record of those runs is `docs/model_cards/heston.md`, which
    is version-controlled but not content-hashed by the freeze. The inventory guard
    `test_every_countable_claim_in_the_report_is_owned_or_declared` therefore carries both as
    declared exemptions anchored on the sentences themselves, with the reason stated next to each.
    That is the weaker of its two mechanisms: a citation to a frozen artifact makes a number
    traceable to a producer, while a declaration records only that a human read the sentence and
    judged it. Closing this means running the Heston comparisons as a registered suite member whose
    results the freeze hashes, which is not done here.

87. **A dated record's present-tense bullets go stale when a later phase changes the world they
    describe, and nothing reads them.** `docs/release_notes_v1.7.0.md`'s "What is still not here"
    section says `sympy` "is still not a project dependency, so the derivation script runs by hand".
    That was true of the tag it describes; Phase 24 added `sympy>=1.12` to the `dev` group, so the
    sentence has been false ever since, in a document a reader reaches from the release page. The
    count guards do not cover it because those documents are deliberately excluded from the
    register-count and test-count comparisons -- they are records of a revision, and forcing them to
    track a moving file would rewrite history to keep a test green, which is what #76 was about. The
    honest mitigation available is the one used here: a dated correction appended beside the stale
    bullet, which is discoverable by a reader but not enforced by a gate. A guard over this class
    would have to decide, per document, which sentences claim to describe the present rather than the
    revision -- and no such decision is made here.

88. **The sixth book's radius verdict is bounded by the swept grid, and the selection rule that found
    it cannot tell that in advance.** `experiments/sixth_book_crossing_map/run.py` picks its book by
    the lowest order-five-to-four piece ratio over a pre-registered candidate grid, measured before any
    radius is read. The candidate it reached -- 3-year maturity, 45 % volatility, 5 % dividend -- has
    its *quartic* radius already at 0.3, the widest move the ladder sweeps, so the quintic radius
    cannot rise inside the grid no matter what the truncation does, and "unchanged" on that book is a
    statement about the ladder rather than about the expansion. What the book does carry is inside the
    artifact and the note: the quintic's worst column inside the quartic's own radius is
    `0.000389` against the quartic's `0.000461`, so the arithmetic improved where the label could not
    follow. A rule that required a non-edge radius as a precondition would have chosen a different,
    less extreme book -- but that precondition is a statement about the outcome's shape, so it was not
    added after the fact here; the scan, the accepted candidate and this limitation are published
    together instead. Three of the six books now sit at the grid edge.

89. **The claim inventory covers three documents; the two it skips still restate producers.**
    `test_every_countable_claim_in_the_report_is_owned_or_declared` reads
    `paper/technical_report.tex` and
    `test_every_countable_claim_in_the_readme_and_reproducibility_is_owned_or_declared` reads
    `README.md` and `docs/reproducibility.md`. `docs/interview_defense.md` and
    `docs/validation_matrix.md` -- which between them restate the suite's member count, the C++ totals
    in four shapes, the crossing-radius book table and the size of this register -- are policed only
    per figure, by each number's own owner. That is a weaker property: an unowned restatement in those
    files is caught only when it happens to match a spelling an owner already reads, which is exactly
    how `docs/reproducibility.md` carried "# 481 tests here" beside a correct 494 for three phases and
    every gate stayed green (Phase 29 found it by widening the inventory, not by reading the file).
    Extending the rule to those two is unwritten work rather than a defect: their prose is denser with
    dated figures, so the value would sit in a per-entry reason list, which should be built against
    real reds rather than by bulk exemption.

    **Closed 2026-10-13 by Phase 35, and the entry's prediction was exact.** Both documents are now in
    `_MARKDOWN_INVENTORY`, and reading them with the rule found three live defects on the first pass,
    none of which any per-figure owner could have seen. (a) The sheet's claim-provenance table said
    `docs/limitations.md` (84 entries)` three phases after the register passed 84, while the prose six
    lines above it said 94 -- the stale twin, in the same file. (b) The sheet's rates in running prose
    (`3,787,943 paths/s`) were policed by one spelling and not by the one actually used, and the same
    sentence quotes a *superseded* rate beside the current one, which is why the new owners read phrases
    (`paths/s in an equivalent pure-Python loop`) rather than number shapes. (c) The entry said the
    value would sit in a per-entry reason list "built against real reds": it was, ten anchors, each
    reported decorative by the guard if it exempts nothing, and one of them was -- the first version of
    the rate exclusion exempted a claim its neighbour already covered. `docs/validation_matrix.md`
    needed no exemption for its densest row: the identity grid in it was already read by
    `test_the_derivation_command_agrees_at_the_precision_floor`, and the inventory's owned list had
    never been told. What the extension did *not* close is #95: the rule still reads digits, so a count
    written in words is invisible to it.

90. **The committed report PDF has no freshness owner, so it can quote digits its own source no
    longer states.** `paper/technical_report.pdf` is generated from `paper/technical_report.tex` and is
    one of the four assets every release attaches. The tex's numeric sentences are each derived or
    declared (#86), but nothing re-derives the PDF from them: a phase that edits the tex and commits the
    old PDF publishes a document quoting the superseded figure, and the guard policing the tex cannot see
    it because it reads the source, not the render. This has now happened twice -- finding 55 (the PDF
    released at `v1.7.0` restated a freeze six releases old) and Phase 24 §8 (the tree's PDF lagged an
    offline test count the tex had already corrected) -- and both times a human found it by running
    `pdftotext`. At this release the rebuild was performed and checked the same way rather than assumed:
    the PDF in the tree reads `498 pytest tests with the validation oracles` and `429 collected without
    them`, extracted from the file. A guard is possible and is not written here. The cheapest form
    compares each file's last-touch commit and requires the PDF not to predate the tex, which is a real
    check locally and silently vacuous on the depth-1 checkout CI used at the time, so it would need the same
    declared-skip discipline #77 and the release-tag guard carry -- a guard that can only fail on one
    machine is a guard whose red must be scheduled, not assumed.

    **Closed 2026-10-09 by Phase 31, and the closure is a binding rather than a reproduction.**
    `scripts/build_report.py` typesets the report and writes `paper/technical_report.build.json`, which
    records the digest of every file the render consumes -- the tex, the bibliography, and each figure
    `\includegraphics` names, parsed from the document rather than listed -- plus the digest of the bytes
    it produced. `test_the_committed_report_pdf_is_bound_to_the_sources_that_rendered_it` re-derives that
    set and runs in every environment, so a source edit not followed by a rebuild is now a red gate: the
    phase's own test-count sync was caught by it within minutes of the guard being written. The
    last-touch-commit form sketched above was not built, because a render is not older or newer than its
    source in any sense the repository can see, and because a history-keyed guard cannot be falsified at
    all -- the harness edits working-tree files, never commits. What stays outside the closure is stated
    in `docs/reproducibility.md`: pdfTeX stamps the creation date, so an honest rebuild always changes the
    bytes and the record binds rather than reproduces (measured: `e72fcfc5…` then `ac7736aa…` for one
    unchanged source, with the extracted text `c5f09b1a…` both times). The stronger check,
    `test_rebuilding_the_report_from_the_committed_source_typesets_the_same_text`, re-typesets and compares
    that text, and needs a TeX distribution and a PDF text extractor, so it reports a skip on the runner.
    Its value is not decorative: a hand-forged record made self-consistent with an edited tex left the
    binding green and this guard red.

91. **The oracle-free pytest figure is a *collection* count, and the runner prints a different
    denominator for the same tree.** `scripts/measure_offline_collection.py` publishes what an
    oracle-free interpreter collects -- at `cbaeffd` it reported `collected: 431`, `module_skips: 4`,
    `collection_errors: 0` -- and every document quoting 431 is quoting that producer. The same commit's
    CI lane (run `38110131841`) printed `428 passed, 7 skipped in 116.75s`. A reader who expects one
    number to be the other will think a document is wrong. They are the same set: of the 431 collected, 3
    skip per-test, and the 4 oracle-gated modules are reported by pytest as skipped *items* that never
    enter `collected`, so `428 + 7 = 431 + 4 = 435`. The reconciliation is only observable from a runner,
    which is why the probe cannot be made to publish it and why no guard ties the two halves together:
    `module_skips` and `collection_errors` are pinned so the probe cannot drift into reporting a lane that
    errored rather than skipped, and the runner's own summary is quoted here with its run id rather than
    asserted from a file. A guard that demanded `428 + 7` would be keyed to a machine this repository does
    not own -- the same environment split item 63 was written about, one level further down.

    Amended 2026-10-11, same rule, one revision later: CI on `4cd9109` (run `38121511275`) printed
    `429 passed, 8 skipped in 200.19s` against the 433 this tree's probe collects. The eighth skip is
    Phase 32's own release-date guard declaring that a depth-1 clone carries no tags, so the arithmetic
    moved with the corpus rather than the reconciliation breaking: `429 + 8 = 433 + 4 = 437`. The skip is
    the guard behaving as designed on the runner, observed in its log rather than inferred from a green
    job.

92. **A band's *pair* has two owners now; its spread percentage has none, and the report's
    performance prose is outside the inventory guard's vocabulary.** The band census
    (`test_every_document_that_prints_a_speedup_band_is_policed_or_declared_dated`) and the membership
    test compare two decimal edges, so the sentences that read "…(32.6% spread)" beside a policed band
    are only half owned: the ratio pair is checked, the percentage beside it is transcribed. It is not
    derivable from the pinned band either -- `SPEEDUP_BANDS` holds rounded edges, and the same arithmetic
    on them gives 32.7% and 21.4% where the committed history gives 32.6% and 20.8% -- so a guard for it
    would have to read git history, which a checkout at depth 1 does not carry. Second half: the report
    inventory guard matches `<number> <countable noun>` over a fixed noun list, and that list has no
    `spread`, `run`, `reading`, `re-freezing` or `path`, so "twenty-two committed re-freezings" and
    "110M to 46M paths per second" are classified by nothing in `paper/technical_report.tex`. What the
    phase did own is the pair inside that sentence; the counts around it were measured by hand for this
    revision (22 readings, min and max as printed in `docs/reproducibility.md`) and are registered here
    as the remaining gap rather than quietly treated as covered.

    **Amended 2026-10-12 by Phase 33 — the first half is closed, and this entry narrowed rather than
    deleted.** The spread percentages now have a producer:
    `test_the_documented_spread_percentages_are_the_committed_historys` recomputes `(max − min) / min`
    over every committed reading and compares it with the pinned `SPEEDUP_SPREADS`, and
    `test_living_documents_quote_the_spread_percentage_the_history_produces` compares each living
    document's band-plus-percentage *block* rather than the bare number, so a document cannot keep the
    pair and change the percentage beside it. The premise that made this unbuildable when #92 was
    written -- that a guard needing history could not run on the runner -- went with the pytest lane's
    `fetch-depth: 0`, and `docs/reproducibility.md` now names the denominator because the same sample
    yields 24.6 % or 30.3 % under other choices. The second half is still open, and Phase 33 produced a
    fresh instance of it: the sentence that explains those alternatives adds two new numbers, and the
    inventory guard's noun list reads neither, because it matches `<number> <countable noun>` and has no
    `%`, `spread`, `reading` or `re-freezing`. Measured: 0 claims from that sentence reach the guard.
    What remains is therefore the vocabulary, not the arithmetic.

    **Amended 2026-10-13 by Phase 35 — the second half is closed for digits, and #95 records the part
    that is not.** The noun list gained `spread`, `run`(plural only), `reading`, `re-freezing` and
    `path`, and the rule now allows a `%` between a number and its noun, which is the shape the entry
    could not see: `32.6% spread` is a countable claim about spreads, and the sentence that explains the
    24.6 %/30.3 % alternatives is now inventoried like the rest. Two precision exclusions came with it,
    because the widened list made them matter: a number that begins inside a longer dotted token is a
    slice of it (`cvxpy 1.9.3 are oracles` read as 9.3 oracles, `quintic factor 1.000, quartic radius`
    as 000 radii), and a number that closes a namespace name is a label (`the Phase 1 consistency test`
    is one test, and `pinned in the Phase 2 test files` names files). The report's declared list lost one
    entry to the label rule -- the exemption became unnecessary when the claim stopped being a claim --
    and the extractor now has a self-test that requires every one of those five judgements to fire on
    this repository's own documents, with a plant on each of the two new ones. `run` stayed out while
    `runs` came in, measured: the singular fires only on `uv run` in a command block.

93. **Cache isolation covers the falsification harness, not the interpreter's habit.** CPython decides
    whether a `.pyc` is current from the source's size and its whole-second mtime, so a file edited to the
    same length and restored within the same clock second is indistinguishable from a file that never
    changed -- the mechanism `docs/integrity_audit.md` finding 66 records as a false sweep escape. The
    harness no longer depends on that: every guard subprocess it spawns runs with `PYTHONPYCACHEPREFIX`
    pointed at a directory created for *that invocation* — a prefix allocated per sweep was the first
    fix and it left the verdict unchanged, because a plant's mutated run and its restored re-run are two
    invocations of one sweep — and
    `test_a_restored_plant_cannot_be_read_back_from_a_stale_bytecode_cache` proves both halves, including
    a control that must show the stale read happening before it credits the isolation. What stays outside
    the closure is everything that is not this harness. A restore performed by another tool, a backup copy
    brought back with its attributes, or two processes touching the same tree inside one second can still
    make a clean file read as its previous contents, and no guard here sees that -- the caches are
    gitignored, so no committed artifact records them and no CI lane can compare against them.

    **Amended 2026-10-12 by Phase 34:** the first sentence is now policed rather than only controlled.
    `test_every_subprocess_the_harness_runs_a_guard_in_is_bytecode_isolated` intercepts the harness's single
    `subprocess.run` and requires every guard step to carry a prefix, and requires two consecutive steps to
    carry different ones -- the property the per-sweep fix lacked. What remains outside is unchanged: other
    tools, and #94's reason this guard cannot have a declared plant. The general
    form of the fault is stated plainly because it is not this repository's to fix: a check that reads
    Python source is a check on whichever copy the interpreter chose.

94. **A plant cannot anchor on the file that holds the plant list, so two guards in this repository are
    proven by demonstration rather than by a declared defect.** `scripts/run_mutation_suite.py` requires
    its anchor to occur exactly once in the target file — that is finding 25's failure mode, an edit that
    lands on nothing and is then counted as caught. A plant whose anchor is a line of that same file
    therefore contains a second copy of the line it is looking for, so the count is always two and the case
    is refused before it runs. One guard sits behind that wall:
    `test_every_subprocess_the_harness_runs_a_guard_in_is_bytecode_isolated`, whose defect is dropping the
    isolation argument in `Harness.uv` -- unlike the plant-count guard, which is planted through the
    annotation in a *document* rather than through the list itself. Phase 34 showed it red the only way
    left: edit the call to pass no environment, run the node, read
    `AssertionError: a guard subprocess was spawned with no environment at all`, restore, run again. That is
    a demonstration rather than an instrument, which means it is not re-run by CI, is not repeated when the
    guard next changes, and can be forgotten. The structural answer would be to move the plant list out of
    the file that interprets it -- `MUTATIONS` into a data module the harness loads -- and nothing here does
    that yet, because it changes the file every future phase edits.

    **Amended 2026-10-14 by Phase 39: the move is done, and the guard behind it has a declared defect.**
    `Mutation` and `MUTATIONS` now live in `scripts/mutation_plants.py`, which the harness loads by file
    path (`PLANTS_PATH`, asserted to be the list's only definition by
    `test_the_plant_list_lives_where_a_plant_can_reach_the_harness`). The unlocked plant is
    `harness-spawns-a-guard-subprocess-without-a-bytecode-prefix`, whose anchor is the single call site in
    `Harness.uv` and whose guard is the isolation check Phase 34 could only demonstrate by hand.
    (a) The boundary moved with the list rather than vanishing: a plant still cannot anchor on a line of
    the file that holds the plant list, because its own entry would be the second copy. What that leaves
    unplantable is a defect *in the list data* -- an entry with a blank claim, a duplicated identifier --
    and those are structural properties the self-test reads off the loaded objects rather than effects a
    tree edit can produce, so the residual is stated, not fixed.
    (b) One measured cost of the split: `--list`, `--kind` and `--only` all resolve through the loaded
    tuple, so the CLI is unchanged, while the file a future phase edits for a plant is now two files and
    the anchor census reads both.

95. **The claim inventory reads digits, so a count written in words is invisible to it, and its two
    exclusion rules can be used to hide a claim as easily as to excuse one.**
    `_REPORT_CLAIM` matches a numeric token, so the shape is `142 rows` and not `one hundred and
    forty-two rows` -- which is fine, because prose does not write counts that way. What prose *does*
    write is the small spoken count: a probe over the five inventoried documents, using the
    repository's own `SPELLED_NUMBERS` table and the widened noun list, finds 112 phrases of that shape
    before any judgement of which are claims -- `twenty-two committed re-freezings` (the exact instance
    #92 registered and Phase 35 did not close), `twenty-six rows`, `four correctness benchmarks`,
    `nineteen members`, `three coverage tests`. Several of those are already owned, per figure, by a
    guard that reads the spelled form (`test_documents_that_count_the_suite_members_agree_with_the_registry`
    resolves `nineteen` through the registry); none of them is *inventoried*, so a spelled restatement in
    an owned document still needs a reader to notice it. The cheaper half of the fix is to give the
    extractor a spelled alternative and let `SPELLED_NUMBERS` decide what counts as a number; the reason
    it has not been done is that the 112 include sentence-openers (`Three scenarios`, `Nine release tags`)
    and idioms (`one test` inside `no more than one test`), so the first run would classify noise as work
    -- which is the failure mode the `#` and trailing-period exclusions were written for, and the reason
    the detector has to be re-validated when its question widens rather than assumed to transfer.
    Second half, stated because it is a cost and not a defect: the label and dotted-token exclusions are
    keyed on the text *around* a number, so `the Phase 507 Python tests` and `v1.9.3 are oracles here`
    would each escape the inventory. Nothing here polices that. What does exist is the self-test's
    requirement that every word in `_LABEL_WORDS` fire on a real document -- it keeps the excuse list
    from growing, which limits the surface a writer can hide behind to one word today.
    **Measured again on 2026-10-13, so the size of this is known rather than guessed:** a spelled-numeral
    variant of the extractor's own shape, run over the five inventoried documents with the noun list as it
    now stands *and* the label rule applied, finds **109** spelled claims -- 45 in the report, 22 in
    `docs/validation_matrix.md`, 18 in `README.md`, 14 in `docs/interview_defense.md`, 10 in
    `docs/reproducibility.md` -- against the 112 phrases above, which is the same corpus before the label
    rule. Of the 109, 19 begin a sentence, which is the group whose number may name rather than count
    (`One implementation rule` names one rule; `Three scenarios` counts three). None is owned today,
    because every owner pattern the inventory lists captures digits, including the ones whose *guards*
    accept a spelled word through `\w+`. The work is therefore two things and not one: let the extractor
    read a numeral spelled, and let the owned list carry the spelled spelling of each owner -- and a first
    run over 109 claims would be a diff nobody can review, so the next phases take it document group by
    document group, each with its own load-bearing declarations and plants, starting with the pair that has
    the fewest (28 across `README.md` and `docs/reproducibility.md`).

    **Amended 2026-10-14 by Phase 38: the first slice is closed and the rest is named rather than
    guessed.** The extractor's number group is now generated from `SPELLED_NUMBERS` -- the table
    `_as_int()` has resolved words through since Phase 22 -- and the widening is switched on per document
    through `_SPELLED_DOCUMENTS`, seeded with that 28-claim pair. All 28 answer for themselves now: 15
    owned by the pattern their owner searches with, 9 cited through the frozen artifact their paragraph
    names, 2 declared with a reason. Reading them found three defects no digit-only inventory could see,
    all of them in living prose: the front page's "Three rows in the full matrix are the ones to
    interrogate" had enumerated four since Phase 12, the same paragraph cited "Row 14" while describing
    the bound the matrix numbers 15, and "quietly skipping four members" was already wrong in the commit
    that first wrote it, which declared five then and six now. What is left is 81 claims in three
    documents -- 45 in `paper/technical_report.tex`, 22 in `docs/validation_matrix.md`, 14 in
    `docs/interview_defense.md` -- and each needs the same two halves: the spelled spelling of every owner
    that already reads the figure, and a stated reason for every claim no owner covers. #97 records why
    the first is bounded by the table's ceiling.

    **Corrected 2026-10-14 by Phase 40, which changed the measuring rule.** Re-run through the shipped
    extractor after #100's hyphen exclusion, the corpus holds **108** spelled-only claims rather than 109:
    45 in the report, 21 in `docs/validation_matrix.md`, 18 in `README.md`, 14 in
    `docs/interview_defense.md`, 10 in `docs/reproducibility.md`. The 28 in the opted-in pair are
    classified, so **80 remain** across the three documents, and the earlier figure counted one phantom the
    rule no longer produces.

    **Amended 2026-10-15 by Phase 41: the rehearsal sheet's 14 are classified, and the shape of the rest
    is now visible.** The sheet joins `_SPELLED_DOCUMENTS`, and its 14 spelled-only claims resolve to 9
    owned and 5 declared, none left cited-and-unchecked. Four of the nine are read from the crossing
    artifacts themselves (`rays_number_of`, `columns_swept`, `books_measured`, the `radii_*` tables), which
    is the half #95 asked for: the words answer to a producer, not to another document. Two are the
    sheet's own inline enumerations -- the two `Xxx route:` labels and the `(1)` / `(2)` sequence -- which
    needed the paragraph as the denominator because `(1)` recurs in a neighbouring answer. One is the
    committed reading history's fourth spelling, and one counts the test modules that carry `--quick`. The
    five declarations are #101's subject rather than this item's: they are counts of families, of rejected
    designs and of a single run's name resolution, and no producer in this tree enumerates them.
    **66 spelled-only claims remain** -- 45 in `paper/technical_report.tex` and 21 in
    `docs/validation_matrix.md` -- and the sheet's group says what each will need: about two thirds an
    owner that already exists in another spelling, about one third a stated reason.

    **Amended 2026-10-15 by Phase 42: the validation matrix is in, and 45 remain.** Its 21 spelled-only
    claims resolve to 5 owned, 5 declared and 11 cited -- none unowned. Two of the five owned are
    counts the table's own guards had read for phases without the inventory being able to see the words
    (`twenty-six rows`, the caveat heading's `Five rows`); the other three are the shape of a study --
    how many rays a slope was fitted along, how many markets a nested differentiation walked, how many
    fields a partials module defines -- counted now from the artifact's own block or from the structure
    with `ast`. Reading that group found the first *false* spelled claim of the rollout: row 21 said
    "the five fields reached by difference routes" where the module defines six fields and reads five
    distinct fourth-order partials, so the sentence carried its denominator from the wrong side of the
    relation, and the corrected prose states both numbers against the structures they name (finding 83).
    #102 records what the rule still cannot see.

    **Amended 2026-10-15 by Phase 43: the report is in, and the rollout is complete.** The report's 45
    spelled-only claims resolve to 18 owned, 10 declared and 17 cited -- none unowned -- and reading them
    found **three more living counts that had gone false**: the fixture sentence said thirteen where the
    directory holds sixteen, the artifact index said ten report files where it holds forty-three, and the
    suite-growth sentence said six members where the registry has grown by seven from the twelve it
    quotes. All three are corrected and owned -- the last as a *relation* (the growth must equal the
    registry minus the sentence's own quoted past), so neither number is ever retyped. #95's open
    residue is now only what #102 records: the rule's recall on prose is bounded by the nouns it lists
    and the modifiers it allows, and the corpus's "complete" means complete-within-the-rule.
96. **A pattern written with a literal space cannot read a claim the document splits across lines, and
    four guards have been taught that; the rest of the corpus still reads raw text.** The falsification
    sweep's one escape was `sheet-states-a-case-gap-the-collected-pair-does-not-give`: the guard compared
    `the (\d+) cases they hold` against `docs/interview_defense.md`, the sheet wraps that sentence as
    `... the 69 cases they` / `hold ...`, so the pattern saw only the twin occurrence two pages later,
    agreed with itself, and stayed green over a planted 70. The same sweep led to the check that found a
    second instance already dormant: `docs/reproducibility.md` states its C++ total twice, and the second
    spelling -- `204 tests under` / `CTest either way` -- had been invisible to
    `test_documents_that_count_the_cpp_tests_agree_with_the_build` since a later edit moved that line
    break, because the guard asserted only that *some* of its patterns matched the file. Measured after the
    fix: mutating the wrapped spelling to 199 reddens the guard, which it did not do before.

    (a) What closed is a reading convention, not a patch: `_folded_document()` gives the count guards the
    same whitespace-folded view the claim inventory already reads, so a span the inventory calls owned is a
    span its owner can see, and the CTest guard now reports a listed spelling that matches nothing instead of
    passing over it.

    (b) What is still open is every guard that reads a document raw. `PROSE_FIGURES` asks whether a
    formatted value occurs *in* a file, the band census matches `--band-shape--` against raw markdown, and
    the analysis-note figure guard searches the note as written; each of them can lose a claim to a line
    break the same way, and none of them is checked for it today. The reason it is registered rather than
    fixed here is that folding changes what those guards can match -- a note whose figure sits at a line end
    may also gain matches -- so each needs its own before/after measurement, which is how #95's spelled
    detector was handled too.

    **Amended 2026-10-13 by Phase 37: the convention now covers every prose-counting guard in the
    repository, and one reader is deliberately left raw.** Folded reading was extended to the chapter
    counts, the suite-member counts (including README's per-kind breakdown and the reproducibility note's
    skippable count), the identity-check counts, the report's own prose figures and the three rate phrases
    `test_documents_quote_the_performance_figures_the_artifact_actually_holds` reads -- each switched only
    after the raw and folded match counts were compared per pattern and found equal, which is the
    before/after this entry asked for. The band census is *not* folded, measured rather than assumed: over
    81 documents folding adds a pair `(10.7, 7.4)` that the tex does not state -- two unrelated numbers at
    the ends of adjacent lines -- because the united shape forbids a newline inside a gap on purpose. Line
    structure is load-bearing there, so a reader that needs it says so in the guard's comment instead of
    being folded for consistency. Still outside: the analysis-note ratchet, which searches test *sources*
    for a filename and would be broken by folding a Python file, and any per-token `x in text` figure check,
    which cannot be split by a wrap because a token has no space in it.
97. **The spelled-numeral table stops at twenty-six, so the rule that now reads words is blind above its
    ceiling, and the owner that reads them raises instead of reporting.** `_SPELLED_WORDS` is generated
    from `SPELLED_NUMBERS`, whose keys run `one`…`twenty-six` because that is what the corpus needed when
    Phase 22 wrote the table. A count above it is not a claim the inventory can see at all, and
    `_as_int()` -- which the *owners* use to resolve the same words -- raises `KeyError` on an unknown
    numeral, so `twenty-seven rows` would leave the inventory silent and the comparison guard erroring
    rather than naming the drift. The trigger is dated and near: `docs/validation_matrix.md` carries
    exactly twenty-six rows today, so the next row either extends the prose to a numeral the table does
    not hold or moves the sentence to digits, and only the second is policed. Extending the table changes
    a fixture every spelled reading resolves through, so it should arrive with the claim that needs it
    rather than as insurance -- and the honest version of that change adds the keys together with a guard
    that every key the table holds is matched by something in the corpus.

    **Amended 2026-10-15 by Phase 44: closed by generation.** The table is built from its parts --
    ones, teens, tens, and the hyphenated compounds the corpus's own style uses -- and covers every
    value below one hundred, with property 7 of the extractor self-test proving the generation
    two-sided: a twenty-seven-count sentence becomes a claim, and withholding one compound key
    silences exactly that claim. The ceiling's first real consumer, Phase 43's report-file count,
    had taken the digits fallback the entry predicted; the fallback is retired and the count is owned
    spelled again. The matrix's row count now disagrees above twenty-six instead of crashing, which
    the plant demonstrates by moving it to twenty-seven and reddening as a comparison.

98. **A claim is credited to its owner because the owner's source contains the pattern string, which is
    transcription rather than application -- and Phase 38 leaned on that five times.** The inventory's
    ownership rule is `assert pattern in holder_source`, so `(\w+)\s+correctness\s+benchmarks` credits
    README's spelled breakdown to
    `test_documents_that_count_the_suite_members_agree_with_the_registry` because that string really does
    sit in the guard -- as a prefix of the longer pattern its `re.search` actually uses. The five fragment
    entries added here are honest for exactly that reason, and the rule cannot tell them from a fragment
    that lives in a comment, or from an owner that later stops searching with it while the text survives.
    What does police the edges: every entry has to match one of the inventoried documents, so a fragment
    that matches nothing is reported as accretion, and every figure the fragments name is separately
    compared with its producer by the guard itself. The structural answer is to resolve the named test's
    own source and require the string inside a `re.search` / `re.findall` / `re.finditer` call rather than
    anywhere in the file -- the AST-not-substring rule this repository already applies elsewhere and has
    not applied here.

    **Amended 2026-10-15 by Phase 45: closed by syntax.** The credit check is `_pattern_is_owned_by`:
    it resolves the named function in the named holder, walks that function's body plus the bodies of
    the same-file helpers it calls, plus the module-level structures the body reads, and demands the
    pattern be a string constant of one of those. Measuring before the change made the mechanism
    concrete: of 84 credits, 68 lived in the owner's body, 8 in a structure it reads -- and 8 failed.
    Four named the wrong reader (Phase 41's own misattributions, invisible for four phases); one --
    `N/N benchmark-suite members executed` -- was searched by **no guard at all**, a credit that
    polices nothing and had passed every gate since it was written, because the table sits in the
    holder's file and a substring check over that file is satisfied by the table itself. The four
    attributions are corrected, the sheet's N/N restatement is owned by the registry guard for real,
    and two plants hold the line: an entry naming a guard that does not exist reddens, and a search
    moved away from its pattern reddens while the dead-pattern check stays green.
99. **A citation that names an existing row is credited even when the sentence around it describes a
    different one.** Phase 38 found the defect while widening the inventory: the front page said "Row 14
    is the other kind of weakness: the bound on the stress map's truncation error", and row 14 is the
    third-and-fourth spot sensitivities -- the bound is row 15. Row 14 exists, so nothing about the
    citation was malformed; the sentence pointed a reader at another row's status while quoting the right
    one. What the new guard proves is that each cited label appears in the matrix's own numbering and that
    the spelled count above the list equals the list. What it does not prove is that the prose matches the
    row: that needs the cited row's validation-status cell read and the backticked status the sentence
    quotes required to appear in it, which is buildable from the same table parse and should be built
    against the next real mis-citation rather than speculatively.

    **Amended 2026-10-16 by Phase 47: closed on the shape that matters, with the boundary counted
    rather than blurred.** The registry guard (`test_every_claim_about_a_validation_matrix_row_describes_
    that_row`) takes a citation as *claiming* when the descriptor sits in apposition to the number
    (`Row 6, the Heston comparison,`), predicates on it (`row 16 is validated by`) or possesses it
    (`row 22's books`), and it requires every content word of that descriptor to appear in the cited row's
    own cells -- folding `ies`/`es`/`s`/`ed` on both sides so `publishes` agrees with a cell that says
    `published`. Nine of the seventeen citations in the inventoried texts are that shape and all nine are
    registered; the other eight are pointers or comparisons and remain unpoliced, because deciding
    "the same truncations as row 19" needs the *comparing* row's cells too, which is a larger instrument
    than a registry. The first design was the obvious one and it was measured before it shipped: giving
    each row the tokens of its own bolded name, keeping those unique to one row, and flagging a citation
    that carries a token unique to a different row produced **6 flags on the 9 citations that carried any
    unique token**, every one of them false -- matrix prose legitimately naming a neighbour's concept, plus
    the un-bolded `9b` label the parser never read -- while the *correct* README citation for row 15 came
    back vacuous because `bound` and `truncation` belong to several rows. Related: #98, whose structural
    credit this reuses; finding 87.

100. **The extractor's number may not be preceded by a letter, a digit, `#` or `.`, and a hyphen is none
    of those, so a hyphenated ordinal's number reads as a quantity.** `the order-four radius transfers` is
    one radius defined at order four; the rule sees `four` followed by whitespace and the noun `radius`, and
    the inventory then asks who owns four radii. Measured on 2026-10-14 across the five inventoried
    documents, replayed through the shipped rules: the *digit* rule already produces two such claims in
    documents it reads today -- `1 identities` twice in `paper/technical_report.tex` and `1 % steps` in
    `docs/validation_matrix.md` -- and the *spelled* rule adds three more wherever it is not yet switched on
    (`four radius` in the rehearsal sheet, `five crossing radius` and `five radius` in the matrix). Two
    things follow, and neither is comfortable. First, the inventory has been classifying phantoms since
    Phase 27 and nothing complained, because a phantom that lands in `cited` costs nothing: the lists are
    audited for staleness and for exemptions that excuse nothing, not for entries that should not exist.
    Second, adding `-` to the lookbehind is the obvious fix and it is not free either -- it must be shown
    not to remove a real claim, which is the same two-sided re-validation #95 asked for when its question
    widened. The digit-rule half of this entry is a pre-existing limit, not a Phase 38 regression: the
    spelled rule inherits the exclusion rather than inventing it.

    **Amended 2026-10-14 by Phase 40: closed, and the measurement came out with one surprise about the
    instrument rather than the corpus.** `-` is excluded now, and the two-sided check is property 6 of
    `test_the_claim_extractor_reads_percentages_and_refuses_labels`, which hands the character back and
    names what returns: three occurrences of two texts under the digit rule -- `1 identities` twice in the
    report (both from `Level-1 identities`) and `1 % steps` in the matrix's `best of 0.2 %-1 % steps` --
    and three more only where the spelled rule is not yet enabled (`four radius` in the rehearsal sheet,
    `five crossing radius` and `five radius` in the matrix). Nothing real was lost, measured: no claim in
    these documents legitimately follows a hyphen.
    (a) The proof the entry had absorbed the phantoms is that deleting them reddened two guards. Both
    declarations that existed for them -- `Level-1 identities` in the report's list, `relative, best of`
    in the markdown's -- failed their own decorative check the moment the exclusion landed, which is the
    designed behaviour of that check and still the first time it has caught an exemption that was paying
    for a phantom rather than excusing a real claim.
    (b) The surprise was in the phase's own instrument. The first version of property 6 loosened the
    exclusion by string-replacing `-` in the assembled class, which also deleted the range dash inside
    `A-Z` and produced a rule that matched nothing anybody had measured -- six phantoms including a
    `2 cases` that no document contains. The two-sided control was the thing that caught it: an
    expectation written as a name rather than a count is what made a broken reconstruction visible at all.
101. **The spelled reader's precision on prose is not measured, only its recall, and a declaration is a
    hand-written reason that nothing tests.** `_REPORT_CLAIM` asks whether a numeral is followed by a
    countable noun; English answers that question with narrative as often as with a quantity. Measured on
    the first prose-heavy document opted in (Phase 41, `docs/interview_defense.md`): of its 14 spelled-only
    claims, 9 have a producer in this tree and 5 are answered by a declaration instead, and the five are
    not one shape. `Two versions of the radius definition were wrong` counts rejected designs, which no
    artifact enumerates. `the two tests specified here` counts *families* while the core declares three
    functions across them -- `kupiec_pof_test`, and Christoffersen's independence and conditional-coverage
    tests -- so a writer who later says "three tests" is excused by the same anchor that excuses this one,
    and the anchor's reason is the only thing distinguishing the two claims. `resolves to exactly one
    test` describes one `ctest -R` run, and `two columns of one magnitude` names the sign pair `-0.15` and
    `+0.15` beside a column count that *is* owned elsewhere.
    (a) What the inventory does check about a declaration is staleness and usefulness -- an anchor that
    appears in no document, or excuses no claim, reddens -- and both checks fired during this phase's
    plants. What it cannot check is whether the sentence's *number* is the one the reason describes,
    because that would require the producer the declaration says does not exist. So the residue is
    explicit: 5 of 14 claims in the document that has been widened so far rest on a prose judgement, and
    the two remaining groups (the report's 45, the matrix's 21) will be judged the same way by whoever
    opens them.
    (b) One candidate rule was measured and rejected. A determiner before the numeral ("the five books",
    "those twenty-two files") looked like a marker of a counting use, and the narrative claims mostly lack
    it; but `The two cases I would be pushed on` and `the two tests specified here` are both determiner-
    led, and both are real claims, so the rule would have excused claims this phase instead turned into
    owners. The exclusion is therefore not written, and the finding stays open as a design question rather
    than a defect: a claim's denominator has to be named by something other than the shape of the words
    around it. Related: #100 recorded the same mechanism on the digit rule, where the fix *was* mechanical.

    **Amended 2026-10-17 by Phase 48: the precision edge got a number, and it is a small one.** The
    corpus guard (`test_the_claim_rule_is_scored_against_sentences_whose_quantities_are_known`) returns
    6 claims over its 15 targeted units and all 6 are real quantities, so phantoms measured **0** on that
    sample -- with two designed negatives in it (a version list, a confidence level), which is why "0 here"
    is not "precise". What this phase did not touch is the entry's main half: a declaration is still a
    hand-written reason whose *number* nothing compares to a producer, because the producer it says does
    not exist is the thing being exempted.

    **Amended 2026-10-17 by Phase 50: precision got a denominator, and it is a document.** Enumerating
    one is cheaper than sampling it: `test_the_claims_a_document_prints_are_a_census_and_not_a_sample`
    reads every distinct phrase the rule prints in a document and requires each to be gold or a named
    phantom. Measured on the first censused document, README.md printed **25** distinct phrases, **24**
    of them counts a reader confirmed and **1** a phantom -- precision **24/25**. Both earlier instruments
    had returned zero phantoms, so the defect was invisible to a targeted corpus *and* to an unbiased
    25-unit sample, and it took the enumeration to show it: the phrase was `0.588 and orders`, and #102's
    modifier slot is where it came from. The queue is a list, not a rumour -- every inventoried document
    must be censused or pending, and the pending backlog is measured in the same units: **19** phrases in
    `docs/reproducibility.md`, **40** in the rehearsal sheet, **31** in the matrix, **84** in the report,
    **198** across the five. (a) The entry's own half is untouched: a declaration is still a hand-written
    reason whose number nothing compares with a producer, and the census judges hits, not exemptions, so
    the report's ten declared claims are as untested as Phase 41 left them. (b) Enumerating also exposed a
    precision failure a phantom list has no word for -- a count attached to the right sentence and the
    wrong noun, which is #104. Related: #102, whose slot produced the phantom, and #103's sibling lesson
    that a measurement instrument reports what it was built to see.

    **Amended 2026-10-17 by Phase 52: three documents censused, and the queue is now measured at 115.**
    `docs/reproducibility.md` prints **19** distinct phrases and all 19 are quantities; the rehearsal sheet
    prints **40** and 39 are, the exception being `two radius` -- #105, which found the shape this entry's
    census was built to expose and which no rule in the tail can refuse without undoing #104. Across the
    three censused texts, **82 of 83** hits are quantities (README's own phantom having been refused in
    Phase 50), and the remaining queue is 31 phrases in `docs/validation_matrix.md` and 84 in the report.
    The entry's headline half is still exactly where it was: a declaration is a hand-written reason whose
    number nothing compares with a producer, and enumerating hits does not touch exemptions at all -- the
    report's ten declared claims remain untested, and the census's value so far is that it finds defects
    in the *rule* rather than auditing the *judgements*.

    **Amended 2026-10-17 by Phase 53: the queue is empty, and the entry's headline is what is left.** All
    five inventoried texts are censused -- **196 of 198** distinct phrases are quantities, and the two that
    are not are one shape (#105): `two radius` and `3 path`, both compound heads whose true noun is off
    `_REPORT_NOUNS`. Nothing about the declarations changed. The distinction the finished census draws is
    the one this entry opened with: enumerating hits found two defects in the *rule* and audited none of the
    *exemptions*, and the report's ten declared claims still rest on a sentence a guard cannot read. What
    would test a declaration is a producer for the thing it says has none, which is a different instrument
    from anything built here. Related: #105 (the shape the census ended on), #102 (reach), #95.

    **Amended 2026-10-18 by Phase 54: closed, and the headline half turned into a ledger.** The exemptions
    are now enumerated per pair -- 46 `(document, anchor, phrase)` rows derived from the shipped
    classification, each carrying a verdict in `_DECLARATION_LEDGER` -- and 19 of the 46 name a producer
    the guard re-reads on every run: 2 frozen artifact fields (both `30 joint moves` readings against
    `control.control_moves_compared`, which holds 30) and 16 quotes in other committed documents, checked
    to be both present and to print the number. One row records a granularity mismatch instead of a
    producer: `two tests` counts families while the stubs declare three functions, so the guard refuses a
    list that would agree, and a wrong symbol in that list is caught by parsing the `.pyi` as a syntax
    tree. One row is #105's `two radius`, filed as the rule's own truncation against the longer phrase the
    document prints. The remaining **26** say nothing in this tree can disagree, in 14 named categories,
    and that residue is not this entry's silence any more -- it is #106, which states what the ledger
    cannot check about them. Two things this closure measured rather than assumed: the report's `seven
    orders of magnitude` cites a phase report that says `seven and a half`, so the rounding is now a quote
    a guard holds rather than a paraphrase; and `0.15 cubic radius` has eleven artifact fields holding
    0.15, all of them other books, which is why the forced-candidate rule stops at *disclosing* the
    candidate instead of compelling an attribution. Related: #106 (what the `none:` rows still owe), #105
    (the phantom the ledger files), #86 (the Heston numbers, now read off the model cards that state them).
102. **The tail of the claim rule allows one word between a numeral and its noun, and that choice is
    unmeasured on the recall side: a real claim phrased with two modifiers is invisible to the
    inventory.** `_CLAIM_TAIL` is `\s*%?\s+(?:[A-Za-z]+\.?\s+)?` plus the noun list, so `twelve columns`
    and `three coverage tests` are claims while `ten five-point slope routes` is not -- the numeral and
    its noun are two words apart, and the hyphenated modifier is not matched by `[A-Za-z]+\.?` anyway.
    (a) Measured both ways on the current corpus with the spelled alternatives and the label rule in
    place, widening the allowance from one modifier to two adds **14 phrases**: 1 in
    `docs/validation_matrix.md` (`ten five-point slope routes`), 1 in the rehearsal sheet (`three FRED
    factor series`), 3 each in README and `docs/reproducibility.md` (`two clean idle runs`, `four in both
    cases`, `one or two digits`), 6 in the report (`five widens the radius`, `one normal per path`,
    `three from both sides`). Of those 14, at most three are claims about an inventoried quantity; the
    rest are the numeral doing another job in the sentence -- `five widens the radius` has *five* as its
    subject, not a count of radii, and `one of those runs` is a pronoun. The rule's one-word allowance is
    therefore a precision choice that was never priced, exactly as #100 and #101 priced two of its other
    edges, and the honest number to carry forward is that the inventory's recall on prose is unknown
    rather than assumed complete.
    (b) It was not widened here because the measurement says the fix trades a known-good guard for a
    queue of non-claims: each extra phrase is a claim somebody must classify, and three quarters of them
    would answer "this is not a quantity", which is #101's declaration pile rebuilt at a larger scale. The
    cheaper half of the same problem is the noun list: `five points`, `two methods` and `six partials` are
    counts of real things in these documents and are missed because the words are not in
    `_REPORT_NOUNS`, and no guard measures how many nouns the list leaves out. What is missing is a
    recall instrument -- a corpus of sentences with known quantities and their spellings, run against the
    rule to count what it fails to see. Until one exists, #95's "66 remain" bounds only what the rule can
    find. Related: #101, whose precision half this mirrors.

    **Amended 2026-10-17 by Phase 48: the instrument exists, and its first output is a named list rather
    than an estimate.** `_CLAIM_CORPUS` scores the shipped rule over 15 units taken from the inventoried
    documents -- each unit is read from the document by a needle, so no sentence in the corpus is
    invented -- with gold written by reading the unit. Measured: **22 gold quantities, 6 the rule sees,
    16 named blind spots, 0 phantoms** among what it returned. The 16 are `shocks`, `arm`, `components`,
    `points`, `families`, `scales`, `maps`, `partials`, `blocks`, `days`, `arms`, `levels`, `benchmark`
    in the singular the list carries only as plural, `experiments` behind a partitive ("Six of the seven
    experiments"), and `two Level-1 identities` -- the last one being the reach #100 gave up when `-`
    left the lookbehind. Both disagreement lists are frozen, so widening the noun list moves the miss
    ratchet on purpose (a plant proves it) and reinstating the dash moves the precision ratchet (another
    plant proves that). The corpus is **targeted** -- units were chosen to contain known blind spots --
    so 6/22 is a list of what the rule cannot see, not a recall estimate for the documents; drawing an
    unbiased sample is the half that keeps this entry open. One correction while measuring: the example
    `two methods` above does not occur in these five documents (the corpus says `3 methods`); `five
    points` and `six partials` do. Related: #101, whose precision half this mirrors.

    **Amended 2026-10-17 by Phase 49: closed, with the estimate the entry asked for and its
    denominator attached.** `test_the_claim_rules_recall_and_precision_are_estimated_on_a_sample` draws
    the unbiased sample: the frame is the **1,016** units across the five inventoried texts longer than
    25 characters that contain a number token, and the sample is **every 42nd of them in document order
    -- 25 units**, with those frame indices frozen so a reworded sentence moves the sample loudly
    instead of quietly scoring stale gold. Reading those 25 units yields **11 countable quantities**, of
    which the shipped rule finds **1**: sampled recall **1/11**, and the 10 misses are named in
    `_CLAIM_SAMPLE_MISSES` -- confidence intervals, lattices, days, shocks, contributions, an elided-noun
    partitive ("116 of 120"), a duration ("2 min"), an order-of-magnitude count, a guarantee, and
    `digit` in the singular the list carries only as plural. **Precision is not estimated by this
    sample**: it produced exactly one extraction, so its denominator is 1 and an empty phantom list
    proves nothing -- which is why #101's untested-declaration half stays open. What closes #102 is the
    instrument plus a number with its n beside it. What follows from the number is the uncomfortable
    part, and is the reason the entry existed: the inventory's reach is bounded by `_REPORT_NOUNS`, not
    by how diligently each phase writes owners, so #95's "66 remain" counted only what that list could
    see. Related: #101, whose precision half this sample cannot settle either, and the register's own
    rule that a published figure names its denominator before anyone quotes it.

    **Amended 2026-10-17 by Phase 50: the slot's generosity was priced on the precision side, and the
    word that showed up is a conjunction.** The entry closed on recall; the census then found the other
    direction in the same slot. README.md's "the order-five-to-four piece ratio spans 0.057 to 0.588 and
    orders the outcome no better" was extracted as `0.588 and orders` -- a claim of 0.588 orders, invented
    because `[A-Za-z]+\.?` cannot tell *and* from *rolling*. The slot now refuses a closed-class word:
    `_CLOSED_CLASS_MODIFIERS` holds **38** conjunctions, prepositions, determiners and relativizers, and
    property 8 of the extractor self-test puts each one into the sentence that first showed the defect and
    requires the shipped rule to read nothing and the reopened rule to read a claim, so no member is
    decoration. Reopening the slot across the corpus gains **exactly two** phrases -- the README one and
    `10% between runs` in the matrix, which the census had not reached because that document is still
    pending -- and nothing else. Two refusals were measured rather than assumed: `further`, `over`, `up`
    and `down` stay outside the block because they classify counted nouns in this register (the report's
    "four further books" is a real claim), and `_CITATION_STOPWORDS` cannot be borrowed for the job
    because that list carries `further`; a plant registers the borrow and the guard reddens on it. What
    this does *not* change is the entry's headline: a two-modifier phrase is still invisible to the rule,
    and `_REPORT_NOUNS` still bounds recall at 1/11 on the unbiased sample. Related: #101, which this
    supplies with a document-sized denominator, and #104, the misattribution the same enumeration found
    beside it.
103. **A falsification plant's `guard` field is a hand-typed string, and nothing before the sweep can
    tell a plant that points at the wrong reader from a plant that points at nothing.** The harness's
    `check_exists` proves the named test is *defined* in the named file and the registry guard re-asserts
    that on every run; neither can see whether that guard is the one that reads the line the plant
    mutates. Finding 86 is the measurement: `owned-credit-loses-the-helper-it-reads-through` named the
    report inventory guard while its pattern is a `_MARKDOWN_OWNED` key, so the sweep ran to completion
    and printed `104/105`, with the one honest line -- `guard-stayed-green` -- sitting in the middle of a
    log nobody re-reads.
    (a) The half fixed here is procedural. The sweep stops at the first plant whose guard does not reject
    the mutation and prints `sweep-stopped-early`, naming the plant and counting the declared plants it
    never ran; `--all` keeps the full census a phase record quotes. That turns a 25-minute discovery into
    the first cycle that fails, which is the cost this entry names. It does not make a mis-pointed plant
    impossible to register, only expensive to leave in.
    (b) The static half was tried and rejected on measurement. The candidate -- the plant's anchor must
    occur inside the named guard's reachability closure (its body, the same-file helpers it calls, the
    module-level structures those read) -- misfired on **7 of the 10 plants that mutate a test module**,
    for three ordinary reasons: the anchor is a fragment of a literal the formatter wrapped across lines;
    the reachability is real but transits a *nested* helper the module-level walk never enters; and a
    guard can read a mutated line by reading the file as text instead of referencing the name. A pre-flight
    that cries wolf on 70 per cent of its inputs is worse than the sweep it would replace, because it runs
    at every registration. What would settle it is dynamic and costs a suite per plant: run the named
    guard *and* its neighbours under one mutation and require that exactly the named one objects. Related:
    #98, whose fix is this same shape applied to a table rather than a list; findings 85 and 86.

    **Amended 2026-10-19 by Phase 57: closed, and closed by the measurement that refuted the criterion this
    entry prescribed.** The dynamic audit shipped as `--pairing-audit` in `scripts/run_mutation_suite.py`:
    one whole-module run per distinct guard, the failing set read from pytest's own summary, and the cost
    named -- 67 module runs, which is why it is a per-phase instrument and not a CI lane. Its first census
    over the registry as shipped is the datum: **67 of 67** observed plants had the guard they name inside
    the failing set, and only **27 of 67** had it alone. The remaining 40 are honest plants whose mutation
    edits a module-level structure several guards read, so "exactly the named one objects" would have
    refused 40 of the 67 plants it was meant to certify. The shipped criterion is therefore *membership*:
    it separates finding 86's defect -- a named guard that stays green while a neighbour takes the blame --
    with no false alarm on the sample, and it is policed by five guards and seven plants. What the audit
    does *not* buy is #107, which the wide-set half of this measurement opened. Related: #98, #107,
    findings 85, 86 and 91.
104. **The claim rule can attach a correct count to the wrong noun, and a phantom list has no shape for
    it.** `_CLAIM_TAIL` reads the word between a numeral and its noun as a modifier, so where two counted
    nouns sit side by side it may take the first for the modifier and the second for the thing counted. In
    `meets it at 60 markets spread over the $(d_1, v)$ plane` (`paper/technical_report.tex`) both
    `markets` and `spread` are on `_REPORT_NOUNS`, the extraction is `60 markets spread`, and the rule
    therefore states a claim of sixty *spreads* about a sentence that counts sixty *markets*. The number
    is right; the object is not.
    (a) Measured on 2026-10-17, this is **1 phrase of the 198** distinct phrases the rule prints across
    the five inventoried documents, and it is not the census's blind spot by accident: `60 markets spread`
    is about a quantity, so the README-style census files it as gold and its phantom list stays honest
    while this defect survives. Precision and misattribution are different failures, and only the first
    has an instrument.
    (b) A fix exists and was left alone. Refusing a modifier that is itself on the noun list would remove
    this phrase and no other -- `markets` is the only such modifier in the corpus, measured by reading the
    slot with the block open. It was not taken because the exclusion would be keyed on a list every phase
    grows: the day `routes`, `moves` or `series` earns a place as a classifier, a true claim vanishes with
    no guard to notice, which is #102's recall bound authored by the noun list instead of the tail. What
    would make it safe is the same denominator the census now supplies -- censusing the report, where the
    phrase lives, before deciding what its hits mean. Related: #101 (precision), #102 (the slot), #100 (the
    last time the tail's generosity was priced).

    **Amended 2026-10-17 by Phase 51: closed, and the fix is in the rule rather than in the census.** The
    modifier slot now refuses a word that is itself on the noun list, and the refusal sits *inside* the
    optional group, which is what makes it a correction instead of a deletion: the engine falls back to
    taking the word as the noun, so `60 markets spread over the plane` is read as `60 markets` -- right
    count, right object -- rather than losing the claim. Measured with the closed-class block held
    constant in both rules, the corpus effect is exactly one phrase moved, in the report, and no other
    document changes. Re-measured after the fix, noun-pair collisions across the 198 distinct phrases
    are **0**.
    (c) The placement is the part worth keeping. Written in front of the optional group the same
    lookahead refuses the noun as well as the modifier, and that variant -- which this phase built first,
    and which reads as a one-character difference -- loses **92** phrases across the corpus, `160 runs`
    and README's other gold counts among them. Property 9 therefore pins both placements by name: the
    frame must land on `60 markets`, and the hoisted rule must be shown to delete claims the shipped rule
    keeps. Two plants register the two directions, plus one that rewords the sentence out of the report so
    the pinned pair cannot go stale unnoticed.
    (d) What is still not covered: the census has no third bucket, and none was needed once the class was
    refused -- a misattribution that does not put a counted noun in the modifier slot would still be
    filed as gold. The 174 phrases in the four pending documents are where the next one would show up,
    and #101's queue is the instrument that would find it. Related: #101 (precision), #102 (the slot),
    #100 (the last time the tail's generosity was priced).

    **Amended 2026-10-17 by Phase 52: the prediction came true, one document later.** Enumerating the
    rehearsal sheet found a hit of exactly that kind -- `two radius`, from "two radius definitions were
    wrong" -- and the census did not file it as gold only because a reader checked the sentence. It is a
    different mechanism from this entry's, and the two cannot both be served by the tail: #105.
105. **The one-word modifier slot cannot tell a compound head from a verb participle, and this corpus
    contains one of each asking for opposite rules.** `two radius definitions were wrong`
    (`docs/interview_defense.md`) counts *definitions*: the head noun is not on `_REPORT_NOUNS`, so the
    rule stops at `radius` and prints a claim of two radii. `meets it at 60 markets spread over the plane`
    (`paper/technical_report.tex`) counts *markets*: there the second word is a participle, and #104's
    refusal exists to stop the rule from taking it as the counted noun. The two are the same position in
    the same pattern, read correctly in opposite directions, and nothing in the pattern distinguishes them.
    (a) Measured both ways rather than argued. Adding `definitions` to the noun list and dropping
    `_COLLISION_BLOCK` reads `two radius definitions` correctly; keeping the collision block -- which is
    what closed #104 -- reads `two radius` again, because the block refuses `radius` as a modifier and the
    engine falls back to it as the noun. So the fix for this entry deletes the fix for that one: on these
    two sentences the slot needs a part-of-speech decision, and the rule has a word list.
    (b) What would settle it is a third list: the words that appear as verbs or participles in this
    corpus's measurement sentences (`spread`, `spanning`, and whatever the next phase writes). Its cost is
    that an unregistered verb produces a phantom silently, and only an enumeration notices -- which is why
    the census names its phantoms per document instead of averaging them, and why this entry carries the
    number **1 hit in the 83 distinct phrases** censused so far. The alternative reading of the evidence is
    that `two radius` is a real claim about radii in a document that also says `two radii` four hits
    earlier; the sentence does not support it, and the phantom list is where that disagreement is settled.

    **Amended 2026-10-17 by Phase 53: a second instance, in the last document censused, and the placement
    question decided on the numbers.** `3 path`, from "40 seeds $\times$ 3 path budgets $\times$ 4 scenarios"
    (`paper/technical_report.tex`), is the same shape with the head noun `budgets`. Both phantoms the census
    ever named are therefore this one, and the conjunction class of #101/#102 is not represented in the
    finished lists at all. The greedy alternative was measured rather than argued: allowing a counted noun
    to modify, with `definitions` and `budgets` added to the list, repairs both truncations and gains two
    further real claims (`two definitions`, `one cmake definition`) but re-creates `60 markets spread` --
    200 phrases against the shipped 198, and one misattribution against two truncations. The block stays,
    on the ground that a phrase attributing a count to a word the sentence uses as a verb is the failure a
    reader cannot see from the extraction, while a truncated compound at least names a word the sentence
    counts something of. That is a judgement, and the number that would overturn it is on the table: a third
    truncation in a document whose head noun *is* on the list, or a misattribution anywhere else. Related:
    #104 (the other half of the slot), #102 (the slot's reach), #101 (whose queue found this).

    **Amended 2026-10-18 by Phase 56: closed, on the condition this entry set for itself.** The refusal no
    longer looks at the modifier; it looks at the head. `_PARTICIPLE_HEAD_BLOCK` reads two words and lets a
    counted noun stand in the modifier slot unless the word after it is in `_PARTICIPLE_HEADS` (`spread`,
    `spanning`), and `definitions` and `budgets` joined the noun list. Measured over the five inventoried
    texts before the change -- 198 phrases, 196 quantities, 2 phantoms -- the variants were: blanket
    refusal, as #104 shipped it, 198 with the two truncations; no refusal at all, 200, with `60 markets
    spread` back; refusal keyed on the head but placed outside the optional group, 197, destroying `one
    spread` and `zero spread`; a head-keyed lookahead in front of the group, 197, which loses `60 markets`
    outright because a failing lookahead before an optional group kills the whole tail at that position;
    and the shipped form, **199 phrases, 199 quantities, 0 phantoms, 0 misattributions**. Both
    truncations are now read whole and the census gold lists them as quantities, so the reversal condition
    -- a truncated compound whose head noun is on the list -- is met, and the misattribution #104 refused
    is still refused. What the entry predicted also holds: the list is vocabulary, not grammar, so a
    participle absent from it produces a phantom silently, and the per-document census is the instrument
    that notices -- which is why the repair was gated on the census rather than on these two sentences.
    Related: #104 (the other half of the slot, still closed), #102 (the slot's reach), #101 (whose queue
    found this), #106 (the ledger's parallel refusal to compel an attribution from digits).
106. **A `none:` verdict is policed for its shape, not for the absence it states.** Phase 54 closed #101 by
    giving every declared number a verdict, and 26 of the 46 verdicts say that nothing in this tree can
    disagree with them. The guard checks a lot about those rows -- the category is in a closed vocabulary of
    14, the vocabulary has no unused member, the partition with the declarations is exact in both
    directions, and when the frozen artifacts hold *exactly one* field whose value equals the claim and whose
    path names the claim's noun, the verdict has to name that field and say why it is not the producer. What
    it cannot check is the case the rule is about: a row filed as having no producer when a producer exists
    somewhere the search does not look.
    (a) The search looks in one place. `_field_candidates` walks the numeric fields of the frozen artifacts
    and matches on value *and* on a word shared between the field path and the claim's noun; there is no
    sibling that searches committed *documents*, because the document search measured in this phase returned
    87 files carrying `2` and 10 carrying `two digits`, so an unforced document match is noise and a forced
    one is luck. The asymmetry is therefore real but bounded: a declared number whose producer is a sentence
    in another file can be filed `none:`, and the ledger's `document:` rows are found by whoever fills the
    row rather than by the guard. Three were caught in that direction during this phase -- `200{,}000
    paths`, `400{,}000 paths` and `20{,}000 paths` all turned out to have model-card producers written in
    abbreviated spellings (`200k paths`, `400k paths`, `20 000 paths`), which the number grammar had to
    learn to read. Two were caught in the other direction, and they are the same entry's real cost: the
    ledger first filed `0.46 reading` against `docs/limitations.md` and `1{,}000 steps` against
    `docs/phase_reports/phase-04-path-dependent-heston.md`, and both citations were to a document that
    *restates* the reading rather than one that produces it -- the register rounds a corner gap the test
    asserts only as a normalised bound, and the phase report does the same sizing arithmetic the report
    paraphrases, whose own anchor reason calls it a hypothetical. Both are now `none:`.
    (b) The second blind spot is the opposite one. `_number_is_printed` accepts the thousand-separator,
    space-separated and `k`/`M` abbreviations of a number, which is what makes those three cards readable as
    producers; the same tolerance lets a `document:` quote match a digit that belongs to a different
    quantity in the same sentence, and only the noun-adjacency the *candidate* search applies is missing
    there. (c) What would close this entry is the sibling search written and priced: enumerate, for each
    `none:` row, the documents that print the number within one clause of the claim's noun, and refuse the
    filing when exactly one exists -- the same forced-disclosure rule the artifacts already have. Its cost is
    known: `docs/limitations.md` alone would become a candidate corpus for most of the 26, so the rule has to
    exclude restatements of the claim's own document family, which is a judgement the ledger would then have
    to record. Related: #101 (what this residue replaced), #86 (the Heston sentences, whose producers are
    model cards the freeze does not hash), #99 (a citation that exists and describes the wrong thing).

    **Amended 2026-10-18 by Phase 55: closed, and closed by the measurement that refuted the fix this entry
    proposed.** The sibling search was written -- `_measurement_candidates()`, restricted to a declared
    measurement corpus and requiring one clause of adjacency -- and it found that of the 26 `none:` rows
    exactly one has a single candidate, and that candidate is the wrong measurement: `200{,}000 paths` is a
    corner of a memory sizing the report labels hypothetical, and the one file matching is
    `docs/model_cards/heston.md`'s `200k paths`, the xi=0 collapse run. Compelling the attribution would
    have manufactured a false producer at its first firing, so the rule ships as a *disclosure*: the forced
    row names the file and says why it is a different measurement, and `_MEASUREMENT_DISCLOSURES` pins the
    firing set so a search that quietly stops matching reddens (finding 89's shape). Widening the window to
    whole files instead returns 21 to 51 clause-less matches for a spelled numeral, which is why "many" is
    not a refusal either. The residue this entry describes did get a mechanism: `document:` split into
    `card:` (6 rows, a prefix in the corpus that can disagree today) and `record:` (10 rows, the one
    narrative file where a discarded reading was written), with an uncited path refused rather than
    defaulted. What is left is not a queue item: the guard checks that a named refusal *names* the
    candidate, never that the refusal is *true*, and a check of that truth is the referent the declaration
    says does not exist. Closing that would need a producer for the meaning of a sentence, which is not an
    instrument. Finding 90 carries the two mis-cited rows this entry's blind spot produced. Related: #101
    (what this residue replaced), #86 (the Heston sentences), #99 (a citation that describes the wrong
    thing), #105 (the same refuse-to-compel judgement on the rule side).
107. **The pairing audit proves a guard objected, not that it objected *about the claim*.** Membership
    separates finding 86's defect -- a named guard that stays green while a neighbour takes the blame -- and
    the census says every plant in the sample passes it. It cannot separate a plant whose named guard rejects
    the mutation for the reason its `claim` gives from one whose guard rejects because the same edit happened
    to move a structure the guard also reads. That is not hypothetical: 40 of the 67 observed plants redden
    more than one guard, so the failing set is the wrong instrument for the question "is this plant about
    this assertion".
    (a) The discriminator exists and was used by hand. Phase 56's branch audit read the *message* inside the
    named guard's own traceback section -- `the participle-head rule reads ['60 markets spread']`, `the
    declared anchor ... is not in the report: it is stale` -- and that is what ties a plant to the assertion
    its claim names. Nothing in the harness does this on a run, so the check exists only in a phase record
    and in the `claim` text a plant hand-wrote beside the anchor.
    (b) Reading it automatically has a trap that has already fired once here (finding 91): pytest pads a
    section header to the terminal width, so a 71-character test name is wrapped in two underscores and a
    transcript sliced at a fixed-width separator runs through the boundary and quotes the *neighbour's*
    message as the plant's. A shipped message check has to match the boundary by pattern, and prove it on
    both paddings, before its output is worth publishing.
    (c) Two smaller reaches belong here too. The audit samples one plant per guard, so the 86 plants behind a
    shared guard get no dynamic check of their own -- the sweep covers their named guard, not their
    neighbours -- and 5 of the 72 guards cannot be reached at all: three CTest cases with no pytest module,
    two probe plants whose target does not exist until they write it. What would close this entry is a
    message-level pairing check over the named guard's own section, with the section boundary proved against
    both header paddings; its cost is the same 67 runs, plus a reason string per plant that the audit can
    compare against the assertion that actually failed. Related: #103 (what this residue replaced), #94 (why
    a plant's list and its interpreter must stay separate files), finding 91.
