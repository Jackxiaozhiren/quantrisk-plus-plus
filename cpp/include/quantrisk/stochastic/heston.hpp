#pragma once

#include <string>
#include <vector>

#include "quantrisk/core/rng.hpp"
#include "quantrisk/core/types.hpp"
#include "quantrisk/pricing/instrument.hpp"

namespace quantrisk {

/// Heston (1993) stochastic-volatility dynamics, simulated by **full-truncation
/// Euler** on the variance (docs/mathematical_specification.md §10):
///
///   dS = (r - q) S dt + sqrt(v) S dW1
///   dv = kappa (theta - v) dt + xi sqrt(v) dW2,   corr(dW1, dW2) = rho
///
/// Full truncation replaces `v` by `max(v, 0)` inside the diffusion coefficient
/// and clamps the next variance to zero, which keeps the variance non-negative
/// and the price strictly positive, but is a *biased* discretisation: the
/// returned `note` says so, and `heston_bias_study` measures it against step
/// refinement instead of pretending it is exact.
struct HestonParams {
    Real spot = 0.0;
    Rate rate = 0.0;
    Rate dividend_yield = 0.0;
    Volatility initial_variance = 0.0; ///< v_0
    Real kappa = 0.0;                  ///< mean-reversion speed
    Real theta = 0.0;                  ///< long-run variance
    Real xi = 0.0;                     ///< vol-of-vol
    Real rho = 0.0;                    ///< correlation, in [-1, 1]
    Time maturity = 0.0;

    /// Structural constraints only (`theta >= 0`, `kappa >= 0`, `rho` in range).
    /// The Feller condition is *reported*, not enforced: violating it is an
    /// admissible, interesting parameter choice, not an input error.
    void validate() const;

    /// 2 kappa theta >= xi^2: variance stays strictly positive under exact
    /// CIR dynamics. Full truncation keeps it non-negative even when this fails.
    [[nodiscard]] bool feller_condition_satisfied() const;

    /// Effective Black-Scholes volatility of the model's short-time limit, used
    /// by the degenerate-parameter tests.
    [[nodiscard]] Real instantaneous_volatility() const;
};

struct HestonSimulation {
    std::vector<Real> terminals;         ///< S_T per path
    std::vector<Real> terminal_variance; ///< v_T per path
    std::vector<Real> realised_variance; ///< integral of v dt per path (trapezoid)
    Count paths = 0;
    Count steps = 0;
    Seed seed = 0;
    Real time_step = 0.0;
    Count negative_variances_clamped = 0;
    Real runtime_seconds = 0.0;
    std::string note;
};

/// Simulate `paths` Heston trajectories with `steps` Euler intervals.
[[nodiscard]] HestonSimulation simulate_heston(const HestonParams &parameters, Count paths,
                                               Count steps, Rng &rng);

/// European price under Heston dynamics with the given variance path
/// discretisation, plus the sampling error of the estimate.
struct HestonPriceResult {
    Real price = 0.0;
    Real standard_error = 0.0;
    Real confidence_low = 0.0;
    Real confidence_high = 0.0;
    Count paths = 0;
    Count steps = 0;
    Seed seed = 0;
    Real mean_terminal_variance = 0.0;
    Real realised_variance_mean = 0.0;
    Count negative_variances_clamped = 0;
    bool feller_condition_satisfied = false;
    Real runtime_seconds = 0.0;
    std::string note;
};

[[nodiscard]] HestonPriceResult price_heston_european(const HestonParams &parameters,
                                                      const EuropeanOption &option, Count paths,
                                                      Count steps, Rng &rng,
                                                      Real confidence_level = 0.95);

/// Price difference between `steps` and `reference_steps` simulations on the
/// same seed - the discretisation-bias probe requested by the Phase 4 gate.
[[nodiscard]] Real heston_step_refinement_gap(const HestonParams &parameters,
                                              const EuropeanOption &option, Count paths,
                                              Count steps, Count reference_steps, Seed seed);

} // namespace quantrisk
