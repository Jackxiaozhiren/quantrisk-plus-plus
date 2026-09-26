#include "quantrisk/pricing/finite_differences.hpp"

#include <algorithm>
#include <cmath>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/pricing/black_scholes.hpp"

namespace quantrisk {

void BumpPolicy::validate() const {
    ValidationIssues issues;
    issues.check(std::isfinite(spot_relative) && spot_relative > 0.0 && spot_relative < 1.0,
                 "spot_relative must be in (0, 1), got " + detail::format_value(spot_relative));
    issues.check(std::isfinite(volatility_absolute) && volatility_absolute > 0.0,
                 "volatility_absolute must be > 0, got " +
                     detail::format_value(volatility_absolute));
    issues.check(std::isfinite(rate_absolute) && rate_absolute > 0.0,
                 "rate_absolute must be > 0, got " + detail::format_value(rate_absolute));
    issues.check(std::isfinite(time_absolute) && time_absolute > 0.0,
                 "time_absolute must be > 0, got " + detail::format_value(time_absolute));
    issues.throw_if_failed("BumpPolicy");
}

namespace {

Real price_at(const EuropeanOption &option, MarketParams market) {
    market.validate();
    return black_scholes(option, market).price;
}

Real put_call_at(const EuropeanOption &option, const MarketParams &market, const Real spot_shift,
                 const Volatility vol_shift, const Rate rate_shift, const Time maturity_shift) {
    MarketParams bumped = market;
    bumped.spot = market.spot + spot_shift;
    bumped.volatility = market.volatility + vol_shift;
    bumped.rate = market.rate + rate_shift;
    bumped.maturity = market.maturity + maturity_shift;
    return price_at(option, bumped);
}

} // namespace

Real finite_difference_delta(const EuropeanOption &option, const MarketParams &market,
                             const BumpPolicy &policy) {
    market.validate();
    option.validate();
    policy.validate();
    const Real h = policy.spot_relative * market.spot;
    return (put_call_at(option, market, h, 0.0, 0.0, 0.0) -
            put_call_at(option, market, -h, 0.0, 0.0, 0.0)) /
           (2.0 * h);
}

Real finite_difference_gamma(const EuropeanOption &option, const MarketParams &market,
                             const BumpPolicy &policy) {
    market.validate();
    option.validate();
    policy.validate();
    const Real h = policy.spot_relative * market.spot;
    const Real centre = price_at(option, market);
    return (put_call_at(option, market, h, 0.0, 0.0, 0.0) - 2.0 * centre +
            put_call_at(option, market, -h, 0.0, 0.0, 0.0)) /
           (h * h);
}

Real finite_difference_vega(const EuropeanOption &option, const MarketParams &market,
                            const BumpPolicy &policy) {
    market.validate();
    option.validate();
    policy.validate();
    const Real down = std::min(policy.volatility_absolute, market.volatility);
    if (down == 0.0) {
        // sigma == 0: the value is not differentiable in sigma at the kink, and a
        // one-sided bump would mix the degenerate branch into the answer.
        return std::numeric_limits<Real>::quiet_NaN();
    }
    return (put_call_at(option, market, 0.0, down, 0.0, 0.0) -
            put_call_at(option, market, 0.0, -down, 0.0, 0.0)) /
           (2.0 * down);
}

Real finite_difference_theta(const EuropeanOption &option, const MarketParams &market,
                             const BumpPolicy &policy) {
    market.validate();
    option.validate();
    policy.validate();
    // Theta is -dV/dtau, tau being time to expiry, so the difference must straddle
    // tau: pricing at T + dt and T - dt keeps the scheme second order, which a
    // one-sided version is not.
    const Real dt = std::min(policy.time_absolute, market.maturity / 2.0);
    if (dt <= 0.0) {
        return std::numeric_limits<Real>::quiet_NaN();
    }
    const Real longer = put_call_at(option, market, 0.0, 0.0, 0.0, dt);
    const Real shorter = put_call_at(option, market, 0.0, 0.0, 0.0, -dt);
    return -(longer - shorter) / (2.0 * dt);
}

Real finite_difference_rho(const EuropeanOption &option, const MarketParams &market,
                           const BumpPolicy &policy) {
    market.validate();
    option.validate();
    policy.validate();
    const Real h = policy.rate_absolute;
    return (put_call_at(option, market, 0.0, 0.0, h, 0.0) -
            put_call_at(option, market, 0.0, 0.0, -h, 0.0)) /
           (2.0 * h);
}

Greeks finite_difference_greeks(const EuropeanOption &option, const MarketParams &market,
                                const BumpPolicy &policy) {
    return Greeks{
        .delta = finite_difference_delta(option, market, policy),
        .gamma = finite_difference_gamma(option, market, policy),
        .vega = finite_difference_vega(option, market, policy),
        .theta = finite_difference_theta(option, market, policy),
        .rho = finite_difference_rho(option, market, policy),
    };
}

} // namespace quantrisk
