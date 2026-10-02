#pragma once

#include "quantrisk/pricing/instrument.hpp"

namespace quantrisk {

/// Finite-difference Greeks, used as the independent cross-check of the
/// analytic ones (docs/validation_protocol.md §1.1, "analytic vs central
/// finite differences").
///
/// Bumps are absolute-or-relative steps with a documented rationale, chosen so
/// that the truncation error (O(h^2) for central differences) and the
/// round-off error (epsilon * V / h^2 for the second difference) are both far
/// below the 1e-6 agreement level the tests assert:
///
/// - spot: 1 % of S,
/// - volatility: 0.01 = one vol point, one-sided if the down-bump would leave
///   the domain sigma >= 0,
/// - rate: 1 bp,
/// - time: one business day (1/252), evaluated as -dV/dtau.
struct BumpPolicy {
    Real spot_relative = 0.01;
    Real volatility_absolute = 0.01;
    Real rate_absolute = 0.0001;
    Real time_absolute = 1.0 / 252.0;

    void validate() const;
};

/// Central-difference Greeks of the Black-Scholes price function.
[[nodiscard]] Greeks finite_difference_greeks(const EuropeanOption &option,
                                              const MarketParams &market,
                                              const BumpPolicy &policy = {});

/// A single Greek by name, for targeted experiments ("how does the analytic
/// value move as the bump shrinks?").
// python: via `finite_difference_greeks` -- one Greek by name is a C++ study convenience.
[[nodiscard]] Real finite_difference_delta(const EuropeanOption &, const MarketParams &,
                                           const BumpPolicy & = {});
// python: via `finite_difference_greeks` -- one Greek by name is a C++ study convenience.
[[nodiscard]] Real finite_difference_gamma(const EuropeanOption &, const MarketParams &,
                                           const BumpPolicy & = {});
// python: via `finite_difference_greeks` -- one Greek by name is a C++ study convenience.
[[nodiscard]] Real finite_difference_vega(const EuropeanOption &, const MarketParams &,
                                          const BumpPolicy & = {});
// python: via `finite_difference_greeks` -- one Greek by name is a C++ study convenience.
[[nodiscard]] Real finite_difference_theta(const EuropeanOption &, const MarketParams &,
                                           const BumpPolicy & = {});
// python: via `finite_difference_greeks` -- one Greek by name is a C++ study convenience.
[[nodiscard]] Real finite_difference_rho(const EuropeanOption &, const MarketParams &,
                                         const BumpPolicy & = {});

} // namespace quantrisk
