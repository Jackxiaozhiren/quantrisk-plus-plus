#pragma once

#include <span>
#include <string>
#include <vector>

#include "quantrisk/core/types.hpp"

namespace quantrisk::portfolio {

/// Equal-risk-contribution (risk parity) portfolio.
///
/// Definition frozen in `docs/mathematical_specification.md` §9: every asset must
/// contribute the same amount to portfolio variance,
///     w_i (Sigma w)_i = (w' Sigma w) / n   for all i,
/// where the contribution is the weight times its covariances with the portfolio.
///
/// Solved by cyclic coordinate descent on
///     f(w) = 1/2 w' Sigma w - c * sum_i log(w_i),
/// whose first-order condition is exactly w_i (Sigma w)_i = c. Each coordinate
/// update has a closed-form positive root, so the iteration cannot wander into
/// negative weights, and `c` is refreshed from the current variance each cycle.
///
/// The result is *verified* against the defining identity rather than assumed:
/// `max_contribution_gap` is the largest relative departure from equal
/// contribution, and `converged` only says it is within tolerance.
struct RiskParitySolution {
    Count assets = 0;
    std::vector<Real> weights;
    Real variance = 0.0;
    Real volatility = 0.0;
    /// Largest relative gap between any asset's risk contribution and 1 / n.
    Real max_contribution_gap = 0.0;
    std::vector<Real> contributions; ///< w_i (Sigma w)_i / (w' Sigma w), sums to 1
    Count cycles = 0;
    bool converged = false;
    bool positive_definite = false;
    std::string note;
};

/// Risk-parity weights for a symmetric covariance matrix (row-major).
///
/// Requires strictly positive variances: a zero-variance asset cannot appear in the
/// log-barrier objective, and inventing a role for it would be a guess. Such cases
/// report `converged == false` with the reason in `note`.
[[nodiscard]] RiskParitySolution risk_parity(std::span<const Real> covariance, Count assets);

/// Same, starting from `budget` weights (for example the minimum-variance
/// portfolio) rather than inverse-volatility weights.
[[nodiscard]] RiskParitySolution risk_parity(std::span<const Real> covariance, Count assets,
                                             std::span<const Real> budget);

} // namespace quantrisk::portfolio
