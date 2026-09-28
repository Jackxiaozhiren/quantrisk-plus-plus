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
[[nodiscard]] bool is_degenerate(const MarketParams &market);

/// Lognormal d1 (NaN when `T == 0` or `sigma == 0`).
[[nodiscard]] Real d1(const EuropeanOption &option, const MarketParams &market);

/// Lognormal d2 = d1 - sigma*sqrt(T) (NaN under the same conditions).
[[nodiscard]] Real d2(const EuropeanOption &option, const MarketParams &market);

[[nodiscard]] PricingResult black_scholes(const EuropeanOption &option, const MarketParams &market);

/// Price of a call (`option.type` ignored) and of a put, for symmetry with the
/// specification and for put-call parity tests.
[[nodiscard]] Real black_scholes_call(const MarketParams &market, Real strike);
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

/// Put-call parity residual `C - P - (S e^{-qT} - K e^{-rT})`, which must be
/// zero for any correct implementation of the same model.
[[nodiscard]] Real put_call_parity_residual(const MarketParams &market, Real strike);

/// @}

} // namespace quantrisk
