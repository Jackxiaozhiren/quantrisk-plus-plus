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
