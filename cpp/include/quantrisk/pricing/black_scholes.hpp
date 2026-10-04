#pragma once

#include "quantrisk/pricing/instrument.hpp"

namespace quantrisk {

/// Black-Scholes-Merton (1964/1973) with a continuous dividend yield,
/// implemented from docs/mathematical_specification.md §2 — no external
/// pricing library is consulted anywhere in this file.
///
/// Degenerate edges are handled by their limits, not by clamping epsilon into
/// the denominator:
/// - `T == 0`  -> intrinsic.
/// - `sigma == 0` -> discounted intrinsic of the deterministic forward.
/// @{

/// True when the model collapses to a deterministic forward (`T == 0` or
/// `sigma == 0`). Every pricer and lattice branches on this instead of clamping
/// an epsilon into a denominator.
// python: internal -- pricers and lattices branch on this in C++; Python gets the branch's result.
[[nodiscard]] bool is_degenerate(const MarketParams &market);

/// Lognormal d1 (NaN when `T == 0` or `sigma == 0`).
// python: internal -- the lognormal argument, which reaches Python through the greeks built on it.
[[nodiscard]] Real d1(const EuropeanOption &option, const MarketParams &market);

/// Lognormal d2 = d1 - sigma*sqrt(T) (NaN under the same conditions).
// python: internal -- d2 enters only through vega, vanna and volga, each of which is bound.
[[nodiscard]] Real d2(const EuropeanOption &option, const MarketParams &market);

[[nodiscard]] PricingResult black_scholes(const EuropeanOption &option, const MarketParams &market);

/// Price of a call (`option.type` ignored) and of a put, for symmetry with the
/// specification and for put-call parity tests.
// python: via `black_scholes` -- the option carries its type, so these two exist for parity tests.
[[nodiscard]] Real black_scholes_call(const MarketParams &market, Real strike);
// python: via `black_scholes` -- the option carries its type, so these two exist for parity tests.
[[nodiscard]] Real black_scholes_put(const MarketParams &market, Real strike);

/// Analytic Delta, Gamma, Vega, Theta, Rho (docs/mathematical_specification.md §3).
[[nodiscard]] Greeks black_scholes_greeks(const EuropeanOption &option, const MarketParams &market);

/// The next two spot derivatives after Gamma: `third` = dV/dS^3 ("speed"),
/// `fourth` = dV/dS^4. Units follow §0 — per unit of spot to the corresponding
/// power — and the pair is additive to the frozen `Greeks` surface, which is why
/// they are a separate value struct rather than two more fields on it.
struct SpotDerivatives {
    Real third = 0.0;
    Real fourth = 0.0;
};

/// Third and fourth derivatives of the Black-Scholes price with respect to spot,
/// both identical for a call and a put at the same strike: put-call parity is
/// affine in `S`, so every derivative of order two or higher coincides.
///
/// Derived from the §3 Gamma by two applications of `d d1 / dS = 1 / (S sigma
/// sqrt(T))` and `phi'(x) = -x phi(x)`; with `v = sigma sqrt(T)` and
/// `A = 1 + d1 / v` they are
///     V_SSS  = -(Gamma / S) * A
///     V_SSSS =  (Gamma / S^2) * (A^2 + A - 1 / v^2)
/// The Taylor-remainder bound for the delta-gamma stress map needs both, and it
/// needs the sign structure: `A` vanishes when `d1 = -v`, so `third` changes sign
/// there and the quartic takes over — which is why `fourth` is exposed rather
/// than left to a numerical bump.
[[nodiscard]] SpotDerivatives black_scholes_spot_derivatives(const EuropeanOption &option,
                                                             const MarketParams &market);

/// The two mixed second partials: `vanna` = d2V/dS dsigma, `volga` = d2V/dsigma^2.
/// New value structs rather than more fields on the frozen `Greeks`.
///
/// They exist because of a specific gap in the published evidence. The stress map
/// (`stress/engine.cpp`) is second order in the equity factor and *strictly linear*
/// in the volatility factor — `volatility = vega * absolute_move`, with no convexity
/// term and no cross term — so the delta-gamma-vega map's error under a joint shock
/// is quadratic rather than the cubic error bounded in `docs/analysis/`. Its leading
/// form is exactly `vanna * h * k + 0.5 * volga * k^2` for spot move `h` and vol move
/// `k`, which is why these two numbers, and not merely a larger vega, are what a
/// two-factor scenario costs.
///
/// With `v = sigma sqrt(T)` and `phi` the standard normal density, `d d1 / d sigma =
/// -d2 / sigma` and `d v / d sigma = v / sigma` collapse the whole sigma-dependence
/// onto the density:
///     vanna = -e^{-qT} phi(d1) d2 / sigma = d(vega)/dS
///     volga = vega * d1 * d2 / sigma      = d(vega)/dsigma
/// Both are also pinned without any numerical bump by differentiating the homogeneity
/// relation `vega = gamma S^2 sigma T` (§3) once in each factor:
///     vanna = V_SSS * S^2 sigma T + 2 S sigma T gamma
///     volga = V_SSsigma * S^2 sigma T + gamma S^2 T
/// which is how the Catch2 cases check them against the spot derivatives above.
struct VolCrossDerivatives {
    Real vanna = 0.0;
    Real volga = 0.0;
};

[[nodiscard]] VolCrossDerivatives black_scholes_vol_cross_derivatives(const EuropeanOption &option,
                                                                      const MarketParams &market);

/// The three mixed third partials that complete the two-variable expansion. Paired
/// with `SpotDerivatives::third` they are the four coefficients of the third
/// directional derivative
///     d3V/du3 = V_SSS h^3 + 3 V_SSsigma h^2 k + 3 V_Sssigma h k^2 + V_Sssss k^3
/// along the joint shock `(h, k)`, which is what bounds the residual left after the
/// quadratic cross terms above are subtracted.
///
/// Same regularity as everywhere else in this file: `S, K, sigma, T > 0`, and every
/// formula below divides by `sigma`, so the degenerate case returns the limit rather
/// than an overflow.
struct MixedThirdDerivatives {
    /// V_SSsigma, which is both d(gamma)/dsigma and d(vanna)/dS.
    Real spot_spot_sigma = 0.0;
    /// V_Sssigma, which is both d(volga)/dS and d(vanna)/dsigma.
    Real spot_sigma_sigma = 0.0;
    /// V_Sssss, the third derivative in volatility alone: d(volga)/dsigma.
    Real sigma_sigma_sigma = 0.0;
};

[[nodiscard]] MixedThirdDerivatives
black_scholes_mixed_third_derivatives(const EuropeanOption &option, const MarketParams &market);

/// The four mixed partials of total order four. With `SpotDerivatives::fourth` they
/// are the five coefficients of the fourth directional derivative
///     d4V/du4 = V_SSSS h^4 + 4 V_SSSsigma h^3 k + 6 V_SSsigmasigma h^2 k^2
///               + 4 V_Ssigmasigmasigma h k^3 + V_sigmasigmasigmasigma k^4
/// along the joint shock `(h, k)`, which is the term the third-order remainder leaves
/// behind: the crossing radius measured in `docs/analysis/two_factor_error_bound.md`
/// is set by how far that remainder stays smaller than the terms it corrects, so
/// widening it needs these four numbers rather than a better estimate of the cubic.
///
/// Every partial of total order four has the same shape in the variables `v = sigma
/// sqrt(T)`, `P = e^{-qT} phi(d1)` and `d2 = d1 - v`:
///     V = P * S^(1 - n_spot) * T^(n_vol / 2) * R(d1, v) / v^3
/// for a numerator polynomial `R`, with `v^3` the denominator in all five and neither
/// `r` nor `K` surviving anywhere but inside `d1`. The polynomials themselves, and the
/// two independent ways they were verified, are recorded in
/// docs/phase_reports/phase-15-restrike-gamma.md §8; each field below is the derivative
/// of a partial this file already publishes, which is what makes the Catch2 cross-checks
/// checks rather than restatements.
///
/// Same regularity as the third-order struct: `S, K, sigma, T > 0`, and the `v^3`
/// denominator means the degenerate case returns the limit rather than an overflow.
struct MixedFourthDerivatives {
    /// V_SSSsigma: d(V_SSS)/dsigma, and d(V_SSsigma)/dS.
    Real spot_spot_spot_sigma = 0.0;
    /// V_SSsigmasigma: d(V_SSsigma)/dsigma, and d(V_Ssigmasigma)/dS.
    Real spot_spot_sigma_sigma = 0.0;
    /// V_Ssigmasigmasigma: d(V_Ssigmasigma)/dsigma, and d(V_Ssigmasigmasigma)/dS.
    Real spot_sigma_sigma_sigma = 0.0;
    /// V_sigmasigmasigmasigma: d(V_sigmasigmasigmasigma)/dsigma.
    Real sigma_sigma_sigma_sigma = 0.0;
};

[[nodiscard]] MixedFourthDerivatives
black_scholes_mixed_fourth_derivatives(const EuropeanOption &option, const MarketParams &market);

/// The six mixed partials of total order five, the terms the fourth-order truncation leaves behind.
/// With `MixedFourthDerivatives` they are the six coefficients of the fifth directional derivative
///     d5V/du5 = V_SSSSS h^5 + 5 V_SSSSsigma h^4 k + 10 V_SSSsigmasigma h^3 k^2
///               + 10 V_SSsigmasigmasigma h^2 k^3 + 5 V_Ssigmasigmasigmasigma h k^4
///               + V_sigmasigmasigmasigmasigma k^5
/// along the joint shock `(h, k)`, which is what decides whether the crossing radius of
/// `docs/analysis/fourth_order_crossing_map.md` widens again or has stopped meaning anything.
///
/// The shape is the order-four one with one more `v`: every partial of total order five is
///     V = P * S^(1 - n_spot) * T^(n_vol / 2) * R(d1, v) / v^4
/// for a numerator polynomial `R`, with `v^4` the denominator in all six and neither `r` nor `K`
/// surviving anywhere but inside `d1`. The numerators come from
/// `docs/phase_reports/phase-20-fifth-order-partials.md` §2, derived symbolically from the price
/// function and verified against nested five-point differences by Richardson refinement rather
/// than by transcription;
/// each field below is the derivative of a partial this file already publishes, which is what makes
/// the Catch2 cross-checks checks rather than restatements.
///
/// Same regularity as the fourth-order struct: `S, K, sigma, T > 0`, and the `v^4` denominator
/// means the degenerate case returns the limit rather than an overflow.
struct MixedFifthDerivatives {
    /// V_SSSSS: d(V_SSSS)/dS, the fifth pure-spot partial.
    Real spot_spot_spot_spot_spot = 0.0;
    /// V_SSSSsigma: d(V_SSSS)/dsigma, and d(V_SSSsigma)/dS.
    Real spot_spot_spot_spot_sigma = 0.0;
    /// V_SSSsigmasigma: d(V_SSSsigma)/dsigma, and d(V_SSsigmasigma)/dS.
    Real spot_spot_spot_sigma_sigma = 0.0;
    /// V_SSsigmasigmasigma: d(V_SSsigmasigma)/dsigma, and d(V_Ssigmasigmasigma)/dS.
    Real spot_spot_sigma_sigma_sigma = 0.0;
    /// V_Ssigmasigmasigmasigma: d(V_Ssigmasigmasigma)/dsigma, and d(V_sigmasigmasigma)/dS.
    Real spot_sigma_sigma_sigma_sigma = 0.0;
    /// V_sigmasigmasigmasigmasigma: d(V_sigmasigmasigmasigma)/dsigma.
    Real sigma_sigma_sigma_sigma_sigma = 0.0;
};

[[nodiscard]] MixedFifthDerivatives
black_scholes_mixed_fifth_derivatives(const EuropeanOption &option, const MarketParams &market);

/// Put-call parity residual `C - P - (S e^{-qT} - K e^{-rT})`, which must be
/// zero for any correct implementation of the same model.
[[nodiscard]] Real put_call_parity_residual(const MarketParams &market, Real strike);

/// @}

} // namespace quantrisk
