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
