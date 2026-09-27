#pragma once

#include <span>
#include <string>
#include <vector>

#include "quantrisk/core/types.hpp"
#include "quantrisk/risk/measures.hpp"
#include "quantrisk/stress/engine.hpp"
#include "quantrisk/stress/factor.hpp"

namespace quantrisk::stress {

/// A drawn set of factor moves.
struct ScenarioSample {
    std::vector<Real> moves; ///< row-major, `paths` rows of `assets` moves
    Count paths = 0;
    Count assets = 0;
    Seed seed = 0;
    std::string note;
};

/// Draw zero-mean factor moves with the supplied covariance, by Cholesky factorisation
/// of the matrix and the project's own `Rng`.
///
/// The covariance must be positive definite for the factorisation to exist. Rather than
/// silently jittering it — which would change the risk being measured by an amount the
/// caller never asked for — the draw refuses and says what the smallest eigenvalue was.
/// The caller's options are then explicit: shrink the matrix with the Phase 6 estimator,
/// or accept a smaller scenario set.
[[nodiscard]] ScenarioSample sample_factor_moves(std::span<const Real> covariance, Count assets,
                                                 Count paths, Seed seed);

/// One factor's behaviour across a whole scenario set.
struct FactorSummary {
    std::string factor_id;
    Real mean_contribution = 0.0;
    Real worst_contribution = 0.0; ///< the most negative single-scenario P&L
};

/// The distribution of outcomes a stress produced, and where each outcome came from.
///
/// `pnl` is kept in full so a caller can take any quantile of it; the summary fields are
/// conveniences over that vector and are checked against it, not computed separately.
struct ScenarioSetResult {
    std::string scenario_name;
    ScenarioKind kind = ScenarioKind::deterministic;
    std::string assumptions;
    std::string generator; ///< what produced the moves, with the seed if there was one

    Count scenarios = 0;
    std::vector<Real> pnl;
    Real mean_pnl = 0.0;
    Real volatility = 0.0; ///< unbiased sd across the scenario P&Ls
    Real worst_pnl = 0.0;
    Real best_pnl = 0.0;
    risk::RiskEstimate var;
    risk::RiskEstimate es;

    std::vector<PositionContribution> by_position; ///< mean P&L per position
    std::vector<FactorSummary> by_factor;
    Real position_attribution_residual = 0.0;
    Real factor_attribution_residual = 0.0;
    std::string note;
};

/// Replay every row of `observed_moves` through the portfolio's exposures.
///
/// Each row is one realised set of factor moves, in the same units the exposures are
/// quoted against. Nothing here forecasts and nothing here looks forward: the window is
/// exactly what it was handed, which is the only sense in which a historical scenario is
/// evidence. The result is a distribution of *what would have happened to this book*, not
/// a prediction of what will.
[[nodiscard]] ScenarioSetResult run_historical_scenarios(const Portfolio &portfolio,
                                                         const Scenario &scenario,
                                                         std::span<const Real> observed_moves,
                                                         Count observations,
                                                         Real confidence = 0.95);

/// Simulate the outcome distribution around a stressed mean.
///
/// The scenario's shocks set the *centre* of the move distribution and its
/// `distribution` field deforms the covariance, so a Monte-Carlo set nests the
/// deterministic result: with the shocks removed and the dispersion left alone this
/// measures the book's ordinary risk, and with the dispersion collapsed it converges to
/// the deterministic P&L. Both limits are tested.
[[nodiscard]] ScenarioSetResult run_monte_carlo_scenarios(const Portfolio &portfolio,
                                                          const Scenario &scenario,
                                                          std::span<const Real> covariance,
                                                          Count paths, Seed seed,
                                                          Real confidence = 0.95);

} // namespace quantrisk::stress
