#pragma once

#include <optional>
#include <span>
#include <string>
#include <vector>

#include "quantrisk/core/types.hpp"

namespace quantrisk::portfolio {

/// Problem data for the mean-variance layer.
///
/// `covariance` is a row-major `assets * assets` matrix, normally taken straight
/// from a `CovarianceEstimate`. `scenario_returns` is optional and row-major
/// `scenario_count * assets`: when present, the solution reports what the chosen
/// weights would have suffered on those historical scenarios, so the same object
/// answers "is it optimal" and "what does it cost".
struct OptimizerInputs {
    Count assets = 0;
    std::vector<Real> covariance;
    std::vector<Real> expected_returns; ///< empty => variance-only problems
    std::vector<Real> scenario_returns; ///< empty => no scenario-based reporting
    Count scenario_count = 0;
};

/// What is being asked for. Defaults match `docs/mathematical_specification.md` §7:
/// fully invested, long-only, no target return.
struct OptimizationRequest {
    bool long_only = true;
    std::optional<Real> target_return;  ///< a lower bound on mu^T w
    std::optional<Real> risk_free_rate; ///< needed for a Sharpe number
    Real cvar_confidence = 0.95;        ///< only used when scenarios are supplied
};

/// The answer, plus the evidence that it is one.
///
/// `verified_optimal` is a Karush-Kuhn-Tucker certificate, not a convergence
/// message: primal feasibility, dual feasibility on the assets excluded from the
/// support, and complementarity all hold within `tolerance`. Because the problem
/// is convex, that certificate is a proof of global optimality — which is why the
/// layer can state an answer without borrowing one from a benchmark.
struct PortfolioSolution {
    Count assets = 0;
    std::vector<Real> weights;
    Real expected_return = 0.0;        ///< mu^T w, 0 when no mu was given
    Real variance = 0.0;               ///< w^T Sigma w
    Real volatility = 0.0;             ///< sqrt of the above, per period
    Real sharpe_ratio = 0.0;           ///< NaN unless a risk-free rate was given
    Real value_at_risk = 0.0;          ///< scenario-based, NaN without scenarios
    Real conditional_var = 0.0;        ///< scenario-based expected shortfall, ditto
    Real budget_residual = 0.0;        ///< |sum(w) - 1|
    Real weight_bound_violation = 0.0; ///< max(0, -min(w)), 0 when long-only holds
    Real target_residual = 0.0;        ///< max(0, target - mu^T w), 0 when no target
    Real tolerance = 0.0;              ///< what "holds" meant on this run
    bool feasible = false;
    bool verified_optimal = false;
    std::string method;
    std::string note;
};

/// @name Solvers
/// @{

/// Minimum-variance weights. With `request.target_return` set, the same problem
/// solved subject to `mu^T w >= target`; the bound is tested for inactivity first
/// and imposed as an equality when it binds, which is exact for one linear
/// inequality over a convex objective.
[[nodiscard]] PortfolioSolution minimum_variance(const OptimizerInputs &inputs,
                                                 const OptimizationRequest &request);

/// Portfolios at each requested target return, in the order given.
[[nodiscard]] std::vector<PortfolioSolution>
efficient_frontier(const OptimizerInputs &inputs, std::span<const Real> target_returns,
                   const OptimizationRequest &request);

/// Maximum-Sharpe portfolio.
///
/// Not a quadratic program: maximising `(mu^T w - rf) / sqrt(w^T Sigma w)` is
/// linear-fractional, so it is solved by tracing the efficient frontier and
/// maximising the ratio along it by trisection over attainable target returns.
/// The `note` on the result records that reformulation, as §7 requires.
[[nodiscard]] PortfolioSolution maximum_sharpe(const OptimizerInputs &inputs,
                                               const OptimizationRequest &request);
/// @}

} // namespace quantrisk::portfolio
