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
    pass it.** `uv run pytest -q` at HEAD gives 509 pytest tests with
    the `oracles` extra installed, and the same tree collects 440 tests without it — the CI lane
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
    annotation in a *document* rather than through the list itself. Phase 34 showed the first one red the
    first one red the only way left: edit the call to pass no environment, run the node, read
    `AssertionError: a guard subprocess was spawned with no environment at all`, restore, run again. That is
    a demonstration rather than an instrument, which means it is not re-run by CI, is not repeated when the
    guard next changes, and can be forgotten. The structural answer would be to move the plant list out of
    the file that interprets it -- `MUTATIONS` into a data module the harness loads -- and nothing here does
    that yet, because it changes the file every future phase edits.

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
