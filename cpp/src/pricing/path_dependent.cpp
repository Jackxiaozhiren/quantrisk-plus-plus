#include "quantrisk/pricing/path_dependent.hpp"

#include <cmath>

#include "quantrisk/core/constants.hpp"

namespace quantrisk {

namespace {

const char *average_name(const AverageType type) {
    return type == AverageType::Arithmetic ? "arithmetic" : "geometric";
}

} // namespace

Real AsianOption::payoff(const std::vector<Real> &sampled) const {
    validate();
    if (sampled.empty()) {
        throw ValidationError("quantrisk: Asian payoff needs at least one sample");
    }
    if (average_type == AverageType::Arithmetic) {
        Real total = 0.0;
        for (const Real level : sampled) {
            total += level;
        }
        return payoff_from_average(total / static_cast<Real>(sampled.size()));
    }
    Real log_total = 0.0;
    for (const Real level : sampled) {
        log_total += std::log(level);
    }
    return payoff_from_average(std::exp(log_total / static_cast<Real>(sampled.size())));
}

Real AsianOption::payoff_from_average(const Real average) const {
    return type == OptionType::Call ? std::max(average - strike, 0.0)
                                    : std::max(strike - average, 0.0);
}

Real barrier_continuity_constant() {
    // exp(zeta(1/2)) = 0.411049337... with zeta(1/2) = -1.4603545088095868, so
    // beta = -zeta(1/2)/sqrt(2 pi) = 0.5826. Hard-coded as a mathematical
    // constant, not a fitted parameter.
    constexpr Real kZetaHalf = -1.46035450880958681288;
    return -kZetaHalf / std::sqrt(kTwoPi);
}

Real continuity_corrected_barrier(const BarrierOption &option, const MarketParams &market,
                                  const Time dt) {
    option.validate();
    market.validate();
    require_positive(dt, "dt");
    const Real shift = std::exp(barrier_continuity_constant() * market.volatility * std::sqrt(dt));
    // Discrete monitoring under-detects knockout, so a discretely monitored
    // barrier is worth more than the continuously monitored one. The Broadie-
    // Glasserman-Kou correction therefore moves the effective barrier *closer to
    // the spot* - down for an up-and-out barrier, up for a down-and-out one -
    // making knockout more likely and pulling the discrete estimate back toward
    // the continuous value.
    return option.barrier == BarrierType::UpAndOut ? option.barrier_level / shift
                                                   : option.barrier_level * shift;
}

const char *average_type_name(const AverageType type) { return average_name(type); }

} // namespace quantrisk
