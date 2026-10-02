#pragma once

#include <span>
#include <string>
#include <vector>

#include "quantrisk/core/types.hpp"
#include "quantrisk/stress/factor.hpp"
#include "quantrisk/stress/scenario.hpp"

namespace quantrisk::stress {

/// One factor's share of the P&L, which is the unit attribution is demanded in.
struct FactorContribution {
    std::string factor_id;
    FactorClass asset_class = FactorClass::equity_index;
    Real relative_move = 0.0;
    Real absolute_move = 0.0;
    /// Split by order and by sensitivity type, so a large number can be read as
    /// "linear", "convexity", "rate", "vol" or "credit" rather than only as a total.
    Real linear = 0.0;
    Real convexity = 0.0;
    Real rate = 0.0;
    Real volatility = 0.0;
    Real credit = 0.0;

    [[nodiscard]] Real total() const { return linear + convexity + rate + volatility + credit; }
};

/// A position's share of the P&L, on the same additive basis.
struct PositionContribution {
    std::string name;
    Real pnl = 0.0;
};

/// Everything one scenario did to one portfolio.
///
/// The three `*_residual` fields are the point of the structure rather than a detail.
/// Because the mapping is a sum over factors and over positions, each decomposition has
/// to reproduce the total exactly, so the residual is a numerical check on the
/// implementation and not a statement about model error. A non-zero residual means the
/// attribution is broken, and it is reported instead of being absorbed.
struct ScenarioResult {
    std::string scenario_name;
    ScenarioKind kind = ScenarioKind::deterministic;
    std::string assumptions;
    Time horizon = 0.0;

    /// Stressed P&L is reported as a *change*; there is no mark-to-market level here.
    Real pnl_change = 0.0;
    std::vector<FactorContribution> by_factor;
    std::vector<PositionContribution> by_position;
    /// Sum of `by_factor` minus `pnl_change`.
    Real factor_attribution_residual = 0.0;
    /// Sum of `by_position` minus `pnl_change`.
    Real position_attribution_residual = 0.0;

    /// Risk-metric change, populated only when a covariance was supplied to the run.
    bool has_risk_metrics = false;
    Real base_volatility = 0.0;
    Real stressed_volatility = 0.0;
    Real base_var = 0.0;
    Real stressed_var = 0.0;
    Real base_es = 0.0;
    Real stressed_es = 0.0;
    /// The change split into the part caused by the mean moving and the part caused by
    /// the distribution deforming. These two telescope to `var_change` exactly by
    /// construction, which is why the decomposition is usable in a report.
    Real var_change = 0.0;
    Real var_change_from_level = 0.0;
    Real var_change_from_distribution = 0.0;
    Real var_decomposition_residual = 0.0;
    Real es_change = 0.0;
    Real volatility_change = 0.0;
    /// Euler component VaR under the stressed distribution, one per position.
    std::vector<PositionContribution> var_components_stressed;
    Real var_component_residual = 0.0;

    std::string note;
};

namespace detail {

/// A resolved pair of per-factor move vectors: relative and absolute, both aligned to
/// the factor set. Exposed so the scenario-set runners map moves with exactly the same
/// arithmetic as the single-scenario path — two implementations of one formula is how a
/// stress report ends up disagreeing with itself.
struct Moves {
    std::vector<Real> relative;
    std::vector<Real> absolute;
};

// python: via `run_scenario` -- resolving a scenario's moves is a step inside that call.
[[nodiscard]] Moves resolve_moves(const FactorSet &factors, const Scenario &scenario);

// python: via `run_scenario` -- a factor's attribution is accumulated and returned by that call.
[[nodiscard]] FactorContribution contribute(const RiskFactor &factor, std::size_t at, Real relative,
                                            Real absolute, const ExposureVector &exposures);

} // namespace detail

/// Map a scenario onto a portfolio.
///
/// With `factor_move_covariance` empty only the P&L and its attributions are produced;
/// risk metrics need the covariance of the factor *moves* themselves, and the engine
/// declines to invent one. That matrix is quoted in the same units the exposures are:
/// relative moves for equity factors, absolute moves for rate, volatility and credit
/// factors. Passing a covariance of returns instead of moves is a units error the
/// arithmetic will not catch, which is why the parameter is named for moves.
///
/// No position weights are needed. Each position's beta is the same linear map applied
/// to its own exposures, the portfolio beta is their sum, and Euler allocation runs on
/// the positions directly — so there is one fewer input to get out of step with the
/// portfolio.
[[nodiscard]] ScenarioResult run_scenario(const Portfolio &portfolio, const Scenario &scenario,
                                          std::span<const Real> factor_move_covariance = {},
                                          Real confidence = 0.95);

/// Apply a distribution shift to a covariance matrix: rescale the standard deviations,
/// then add `correlation_increment` to every off-diagonal entry.
///
/// Returns the shifted matrix row-major and reports what had to be clipped or projected
/// in `note`. A shift that cannot be made positive semidefinite is *said so* rather than
/// silently fixed, because the amount of clipping is itself a finding about the scenario.
[[nodiscard]] std::vector<Real> shift_covariance(std::span<const Real> covariance, Count assets,
                                                 const DistributionShift &shift, std::string &note);

} // namespace quantrisk::stress
