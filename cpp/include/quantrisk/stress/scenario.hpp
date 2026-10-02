#pragma once

#include <string>
#include <vector>

#include "quantrisk/core/types.hpp"
#include "quantrisk/stress/factor.hpp"

namespace quantrisk::stress {

/// A move applied to one factor, in whichever of the two units fits the factor.
///
/// Both fields default to zero and both are additive, so a rate factor can be shocked
/// absolutely (`absolute = 0.02` for +200 bp) and an equity factor relatively
/// (`relative = -0.20`) with no mode flag to get out of sync with the data. A shock
/// that sets `relative` on a factor whose class is not equity-like is rejected rather
/// than silently reinterpreted, because the two readings differ by the factor level and
/// the wrong one is invisible in the output.
struct Shock {
    std::string factor_id;
    Real relative = 0.0; ///< fraction of the level: -0.20 is a 20 % fall
    Real absolute = 0.0; ///< units of the factor: 0.02 is +200 bp

    [[nodiscard]] Real relative_from_absolute(Real level) const;
};

/// How a covariance matrix is deformed, as opposed to how levels move.
///
/// Kept separate from `Shock` because it is a different object entirely: shocks move
/// the *mean* of the return distribution and this moves its *shape*. Conflating them is
/// how a stress report ends up attributing a volatility effect to a direction.
struct DistributionShift {
    /// Every standard deviation multiplied by this; 1.0 leaves the scale alone.
    Real volatility_multiplier = 1.0;
    /// Added to every off-diagonal correlation, then clipped into [-1, 1] with the
    /// matrix projected back to positive semidefinite if the clip broke it. The clip
    /// and projection are reported in the result note rather than applied quietly.
    Real correlation_increment = 0.0;
};

/// Where the numbers in a `Scenario` came from, which decides how much of the result
/// is measurement and how much is judgement.
enum class ScenarioKind {
    deterministic, ///< hand-set factor moves: pure judgement, fully explicit
    historical,    ///< factor moves read off a recorded window: measurement, one asset
    monte_carlo,   ///< moves drawn from a shifted distribution: model plus seed
};

// python: internal -- enum spelling for C++ diagnostics and messages; pybind binds ScenarioKind.
[[nodiscard]] const char *to_string(ScenarioKind kind);

/// One named stress: factor moves, a distribution deformation, and the assumptions
/// that make both meaningful.
///
/// `assumptions` is required, not optional commentary. PROJECT_SPEC.md §Phase 7 puts
/// "explicit assumptions" between the scenario and the impact in the gate chain, and a
/// scenario whose provenance cannot be stated is a number without a meaning — a −20 %
/// equity move with no horizon attached is neither a one-day crash nor a bear market,
/// and the P&L is correct for neither.
struct Scenario {
    std::string name;
    ScenarioKind kind = ScenarioKind::deterministic;
    std::string assumptions;
    std::vector<Shock> shocks;
    DistributionShift distribution;
    /// Only meaningful for `monte_carlo`; recorded so a run can be re-executed.
    Seed seed = 0;
    Count paths = 0;
    /// The horizon the moves and the distribution describe, in years. Zero means the
    /// scenario does not define one, which the engine reports rather than assumes.
    Time horizon = 0.0;
};

} // namespace quantrisk::stress
