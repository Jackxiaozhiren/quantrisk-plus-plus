#pragma once

#include <cstddef>
#include <vector>

#include "quantrisk/core/types.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/pricing/instrument.hpp"

namespace quantrisk {

/// Path-dependent contracts priced by simulation (Phase 4). Payoffs are
/// evaluated over a monitored subsequence of a simulated path, so the
/// monitoring convention is part of the instrument definition, not a detail of
/// the engine.

/// Averaging convention for the payoff of an Asian option.
enum class AverageType { Arithmetic, Geometric };

/// A set of monitoring dates expressed as year fractions in [0, T], ascending.
using MonitoringTimes = std::vector<Time>;

struct AsianOption {
    OptionType type = OptionType::Call;
    Real strike = 0.0;
    AverageType average_type = AverageType::Arithmetic;
    Count monitoring_points = 0; ///< equally spaced over (0, T], >= 1

    AsianOption() = default;
    AsianOption(const OptionType option_type, const Real option_strike, const AverageType averaging,
                const Count points)
        : type(option_type), strike(option_strike), average_type(averaging),
          monitoring_points(points) {}

    void validate() const {
        ValidationIssues issues;
        issues.check(std::isfinite(strike) && strike > 0.0,
                     "strike must be finite and > 0, got " + detail::format_value(strike));
        issues.check(monitoring_points >= 1, "monitoring_points must be >= 1, got " +
                                                 detail::format_value(monitoring_points));
        issues.throw_if_failed("AsianOption");
    }

    /// Payoff from the sampled levels at the monitoring dates.
    [[nodiscard]] Real payoff(const std::vector<Real> &sampled) const;

    /// Payoff from the running sum (arithmetic) or sum of logs (geometric).
    [[nodiscard]] Real payoff_from_average(const Real average) const;
};

/// Barrier direction and instrument.
enum class BarrierType { UpAndOut, DownAndOut };

struct BarrierOption {
    OptionType type = OptionType::Call;
    Real strike = 0.0;
    BarrierType barrier = BarrierType::UpAndOut;
    Real barrier_level = 0.0;
    Real rebate = 0.0; ///< paid at expiry if knocked out

    BarrierOption() = default;
    BarrierOption(const OptionType option_type, const Real option_strike,
                  const BarrierType barrier_type, const Real level, const Real rebate_amount)
        : type(option_type), strike(option_strike), barrier(barrier_type), barrier_level(level),
          rebate(rebate_amount) {}

    void validate() const {
        ValidationIssues issues;
        issues.check(std::isfinite(strike) && strike > 0.0,
                     "strike must be finite and > 0, got " + detail::format_value(strike));
        issues.check(std::isfinite(rebate), "rebate must be finite");
        issues.check(std::isfinite(barrier_level) && barrier_level > 0.0,
                     "barrier_level must be finite and > 0, got " +
                         detail::format_value(barrier_level));
        issues.throw_if_failed("BarrierOption");
    }

    /// True when the path is still alive after observing `level` on a monitoring
    /// date (discrete monitoring; see the Phase 4 model card for the difference
    /// from continuous monitoring).
    [[nodiscard]] bool survives(const Real level) const {
        return barrier == BarrierType::UpAndOut ? level < barrier_level : level > barrier_level;
    }

    [[nodiscard]] Real payoff(const Real terminal) const {
        return type == OptionType::Call ? std::max(terminal - strike, 0.0)
                                        : std::max(strike - terminal, 0.0);
    }
};

/// Broadie-Glasserman-Kou continuity correction factor: shifting the barrier
/// by `exp(-+beta sigma sqrt(dt))` approximates a continuously monitored
/// barrier from a discretely monitored one. `beta = -zeta(1/2)/sqrt(2 pi)`.
[[nodiscard]] Real barrier_continuity_constant();

/// Barrier level adjusted for continuous monitoring, given the discrete step
/// `dt`. The sign of the shift depends on the barrier direction.
[[nodiscard]] Real continuity_corrected_barrier(const BarrierOption &option,
                                                const MarketParams &market, const Time dt);

} // namespace quantrisk
