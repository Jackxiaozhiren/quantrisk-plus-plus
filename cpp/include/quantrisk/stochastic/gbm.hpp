#pragma once

#include <cstddef>
#include <vector>

#include "quantrisk/core/rng.hpp"
#include "quantrisk/core/types.hpp"
#include "quantrisk/pricing/instrument.hpp"

namespace quantrisk {

/// Exact GBM transition under the risk-neutral measure
/// (docs/mathematical_specification.md §1):
///
///   S_(t+dt) = S_t * exp[(r - q - sigma^2/2) dt + sigma sqrt(dt) Z]
///
/// Because the transition is exact, a *terminal-only* draw of `S_T` carries no
/// discretisation error for a European payoff, while a path with `steps`
/// intervals is what path-dependent contracts (Phase 4) need -- there the
/// step count is a bias knob that must be studied, not assumed away.
namespace gbm {

/// `paths` independent draws of S_T.
[[nodiscard]] std::vector<Real> terminal_prices(const MarketParams &market, Count paths, Rng &rng);

/// Flattened `paths` x (`steps` + 1) matrix, row-major; each row starts at S_0.
[[nodiscard]] std::vector<Real> paths_matrix(const MarketParams &market, Count paths, Count steps,
                                             Rng &rng);

/// Same as `paths_matrix` but interleaved so that path `i` and path `i + n/2`
/// are an antithetic pair (Z and -Z), for `n` even.
[[nodiscard]] std::vector<Real> antithetic_paths_matrix(const MarketParams &market, Count paths,
                                                        Count steps, Rng &rng);

/// Terminal prices generated in antithetic pairs: result[2i + 1] is driven by
/// -Z_i. Requires an even `paths` count.
[[nodiscard]] std::vector<Real> antithetic_terminal_prices(const MarketParams &market, Count paths,
                                                           Rng &rng);

/// Physical (real-world) measure terminal draws. `mu` is the **price
/// appreciation** drift, excluding the dividend yield, so the simulated
/// dynamics are `dS = (mu - q) S dt + sigma S dW` and setting `mu = r`
/// reproduces the risk-neutral draws exactly. Used by the risk engine in
/// Phase 5, never by pricing; the two measures are separate entry points so
/// they cannot be mixed silently.
[[nodiscard]] std::vector<Real> terminal_prices_physical(const MarketParams &market, Rate mu,
                                                         Count paths, Rng &rng);

/// Sum of the log-increments that a path generator applies, as a diagnostic for
/// tests: E[ln(S_T/S_0)] should be (r - q - sigma^2/2) T.
[[nodiscard]] Real expected_log_return(const MarketParams &market);

} // namespace gbm
} // namespace quantrisk
