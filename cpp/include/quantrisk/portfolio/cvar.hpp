#pragma once

#include <optional>
#include <span>
#include <string>
#include <vector>

#include "quantrisk/core/types.hpp"

namespace quantrisk::portfolio {

/// Rockafellar-Uryasev CVaR minimisation, `docs/mathematical_specification.md` §8.
///
/// For scenario losses `L_i(w) = -r_i^T w` and confidence `beta`:
///
///     minimise    alpha + 1/((1 - beta) M) * sum_i u_i
///     s.t.        u_i >= L_i(w) - alpha,  u_i >= 0,
///                 sum_j w_j = 1,  w >= 0,   (optionally mu^T w >= target)
///
/// which is a *linear* program because the losses are linear in the weights. It is
/// solved by the two-phase simplex in `linear_program.hpp`, not by a general-purpose
/// modelling library; cvxpy and PyPortfolioOpt appear only as benchmarks.
struct CvarRequest {
    Count assets = 0;
    Count scenarios = 0;
    std::vector<Real> scenario_returns; ///< row-major `scenarios * assets`
    std::vector<Real> expected_returns; ///< needed only with a target
    Real confidence = 0.95;
    std::optional<Real> target_return;
};

struct CvarSolution {
    std::vector<Real> weights;
    Real alpha = 0.0;           ///< the optimised VaR level
    Real cvar = 0.0;            ///< the LP objective: the optimised CVaR
    Real recomputed_cvar = 0.0; ///< the same quantity evaluated from the definition
    Real budget_residual = 0.0;
    Real weight_bound_violation = 0.0;
    Real target_residual = 0.0;
    Count pivots = 0;
    /// "optimal" | "infeasible" | "unbounded" | "numerical failure", so a caller
    /// can branch on the outcome instead of reading the note.
    std::string status;
    bool solved = false;
    bool certified = false;
    std::string note;
};

/// Minimise CVaR over the long-only fully invested set.
[[nodiscard]] CvarSolution minimise_cvar(const CvarRequest &request);

} // namespace quantrisk::portfolio
