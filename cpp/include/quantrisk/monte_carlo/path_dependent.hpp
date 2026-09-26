#pragma once

#include <vector>

#include "quantrisk/core/rng.hpp"
#include "quantrisk/core/types.hpp"
#include "quantrisk/monte_carlo/engine.hpp"
#include "quantrisk/pricing/instrument.hpp"
#include "quantrisk/pricing/path_dependent.hpp"

namespace quantrisk {

/// Analytic value of a *geometric* average European option with `monitoring_points`
/// equally spaced monitoring dates over (0, T] under GBM.
///
/// With h = T / M the log-average is normal with
///   mean = ln S + (r - q - sigma^2 / 2) * h * (M + 1) / 2
///   var  = sigma^2 * h * (M + 1)(2M + 1) / (6 M)
/// which tends to sigma^2 T / 3 as M -> infinity (continuous averaging).
///
/// This is the closed-form oracle used to validate the geometric Monte Carlo
/// estimator and the control variate for the arithmetic one.
[[nodiscard]] PricingResult geometric_asian_price(const AsianOption &option,
                                                  const MarketParams &market);

/// Monte Carlo pricing of path-dependent payoffs on a monitoring grid.
namespace path_dependent {

/// Arithmetic-average Asian option. When `use_control_variate` is set, the
/// geometric average of the same samples (whose expectation is known in closed
/// form) is used as the control.
[[nodiscard]] MonteCarloResult price_asian(MonteCarloEngine &engine, const AsianOption &option,
                                           const MarketParams &market, Count paths,
                                           bool use_control_variate, Real confidence_level = 0.95);

/// Geometric-average Asian option, priced by simulation to be compared against
/// `geometric_asian_price`.
[[nodiscard]] MonteCarloResult price_geometric_asian(MonteCarloEngine &engine,
                                                     const AsianOption &option,
                                                     const MarketParams &market, Count paths,
                                                     Real confidence_level = 0.95);

/// Discretely monitored barrier option. `continuous_approximation` applies the
/// Broadie-Glasserman-Kou barrier shift, which approximates continuous
/// monitoring from the same discrete paths; it is an approximation and is
/// labelled as such in the result note.
[[nodiscard]] MonteCarloResult price_barrier(MonteCarloEngine &engine, const BarrierOption &option,
                                             const MarketParams &market, Count paths, Count steps,
                                             bool continuous_approximation = false,
                                             bool antithetic = false, Real confidence_level = 0.95);

/// Payoff of an Asian option evaluated from a simulated path (all monitoring
/// dates are the path's interior and final levels).
[[nodiscard]] Real asian_payoff_from_path(const AsianOption &option, const Real *data,
                                          std::size_t length);

/// Knocked-out test plus terminal payoff of a barrier option on one path.
[[nodiscard]] Real barrier_payoff_from_path(const BarrierOption &option, const Real *data,
                                            std::size_t length, Real effective_barrier);

} // namespace path_dependent
} // namespace quantrisk
