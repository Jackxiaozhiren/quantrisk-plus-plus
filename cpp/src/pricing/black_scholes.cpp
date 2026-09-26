#include "quantrisk/pricing/black_scholes.hpp"

#include <cmath>
#include <limits>

#include "quantrisk/core/constants.hpp"
#include "quantrisk/math/normal.hpp"

namespace quantrisk {

const char *to_string(const OptionType type) { return type == OptionType::Call ? "call" : "put"; }

const char *to_string(const ExerciseStyle style) {
    return style == ExerciseStyle::European ? "european" : "american";
}

namespace {

struct Terms {
    Real growth_discount = 0.0;   ///< exp(-q T)
    Real rate_discount = 0.0;     ///< exp(-r T)
    Real forward_spot = 0.0;      ///< S exp(-q T)
    Real discounted_strike = 0.0; ///< K exp(-r T)
    Real forward = 0.0;           ///< S exp((r - q) T)
};

Terms terms_of(const MarketParams &market, const Real strike) {
    const Real tq = market.dividend_yield * market.maturity;
    const Real tr = market.rate * market.maturity;
    return Terms{
        .growth_discount = std::exp(-tq),
        .rate_discount = std::exp(-tr),
        .forward_spot = market.spot * std::exp(-tq),
        .discounted_strike = strike * std::exp(-tr),
        .forward = market.spot * std::exp((market.rate - market.dividend_yield) * market.maturity),
    };
}

/// Indicator of "exercise is worth something", with the symmetric 1/2
/// convention exactly at the kink. This is the sigma -> 0 limit of N(+-d1),
/// under which the Black-Scholes Greeks collapse to step functions.
Real moneyness_indicator(const OptionType type, const Real level, const Real strike) {
    const bool in_the_money = type == OptionType::Call ? level > strike : level < strike;
    const bool at_the_money = level == strike;
    if (in_the_money) {
        return 1.0;
    }
    return at_the_money ? 0.5 : 0.0;
}

} // namespace

bool is_degenerate(const MarketParams &market) {
    return market.maturity == 0.0 || market.volatility == 0.0;
}

Real d1(const EuropeanOption &option, const MarketParams &market) {
    market.validate();
    option.validate();
    if (is_degenerate(market)) {
        return std::numeric_limits<Real>::quiet_NaN();
    }
    const Real sigma_root_t = market.volatility * std::sqrt(market.maturity);
    return (std::log(market.spot / option.strike) +
            (market.rate - market.dividend_yield + 0.5 * market.volatility * market.volatility) *
                market.maturity) /
           sigma_root_t;
}

Real d2(const EuropeanOption &option, const MarketParams &market) {
    const Real first = d1(option, market);
    if (std::isnan(first)) {
        return first;
    }
    return first - market.volatility * std::sqrt(market.maturity);
}

PricingResult black_scholes(const EuropeanOption &option, const MarketParams &market) {
    market.validate();
    option.validate();

    PricingResult result;
    result.method = "black_scholes_analytical";

    if (is_degenerate(market)) {
        const Terms terms = terms_of(market, option.strike);
        result.price = terms.rate_discount * option.payoff(terms.forward);
        result.note = market.maturity == 0.0
                          ? "degenerate edge T == 0: value is the expiry payoff"
                          : "degenerate edge sigma == 0: the forward is deterministic, "
                            "value is the discounted intrinsic of the forward";
        return result;
    }

    const Real first = d1(option, market);
    const Real second = first - market.volatility * std::sqrt(market.maturity);
    const Terms terms = terms_of(market, option.strike);

    result.d1 = first;
    result.d2 = second;
    result.price =
        option.type == OptionType::Call
            ? terms.forward_spot * normal_cdf(first) - terms.discounted_strike * normal_cdf(second)
            : terms.discounted_strike * normal_cdf(-second) -
                  terms.forward_spot * normal_cdf(-first);
    return result;
}

Real black_scholes_call(const MarketParams &market, const Real strike) {
    return black_scholes(EuropeanOption{OptionType::Call, strike}, market).price;
}

Real black_scholes_put(const MarketParams &market, const Real strike) {
    return black_scholes(EuropeanOption{OptionType::Put, strike}, market).price;
}

Greeks black_scholes_greeks(const EuropeanOption &option, const MarketParams &market) {
    market.validate();
    option.validate();

    Greeks greeks;
    const Terms terms = terms_of(market, option.strike);

    if (is_degenerate(market)) {
        /// sigma -> 0+ (and T -> 0+) limits of the analytic formulas below. With
        /// zero volatility the value is piecewise linear in the forward, so Gamma
        /// and Rho-like smoothness is lost: every Greek here is the corresponding
        /// limit, with the 1/2 convention exactly at the kink.
        const Real indicator = moneyness_indicator(option.type, terms.forward, option.strike);
        const bool at_the_money = terms.forward == option.strike;

        if (market.maturity == 0.0) {
            greeks.delta = option.type == OptionType::Call ? indicator : -indicator;
            return greeks; // gamma = vega = theta = rho = 0 for an expired contract
        }

        greeks.delta = option.type == OptionType::Call ? terms.growth_discount * indicator
                                                       : -terms.growth_discount * indicator;
        greeks.gamma = 0.0;
        greeks.vega = at_the_money ? market.spot * terms.growth_discount * normal_pdf(0.0) *
                                         std::sqrt(market.maturity)
                                   : 0.0;
        greeks.rho = option.type == OptionType::Call
                         ? market.maturity * terms.discounted_strike * indicator
                         : -market.maturity * terms.discounted_strike * indicator;
        greeks.theta =
            option.type == OptionType::Call
                ? (market.dividend_yield * terms.forward - market.rate * option.strike) * indicator
                : (market.rate * option.strike - market.dividend_yield * terms.forward) * indicator;
        return greeks;
    }

    const Real first = d1(option, market);
    const Real second = first - market.volatility * std::sqrt(market.maturity);
    const Real root_t = std::sqrt(market.maturity);
    const Real density = normal_pdf(first);

    /// Shared by call and put (docs/mathematical_specification.md §3).
    greeks.gamma = terms.growth_discount * density / (market.spot * market.volatility * root_t);
    greeks.vega = market.spot * terms.growth_discount * density * root_t;

    const Real time_decay =
        -market.spot * terms.growth_discount * density * market.volatility / (2.0 * root_t);

    if (option.type == OptionType::Call) {
        greeks.delta = terms.growth_discount * normal_cdf(first);
        greeks.theta =
            time_decay +
            market.dividend_yield * market.spot * terms.growth_discount * normal_cdf(first) -
            market.rate * terms.discounted_strike * normal_cdf(second);
        greeks.rho = market.maturity * terms.discounted_strike * normal_cdf(second);
    } else {
        greeks.delta = terms.growth_discount * (normal_cdf(first) - 1.0);
        greeks.theta =
            time_decay -
            market.dividend_yield * market.spot * terms.growth_discount * normal_cdf(-first) +
            market.rate * terms.discounted_strike * normal_cdf(-second);
        greeks.rho = -market.maturity * terms.discounted_strike * normal_cdf(-second);
    }
    return greeks;
}

Real put_call_parity_residual(const MarketParams &market, const Real strike) {
    const Terms terms = terms_of(market, strike);
    return black_scholes_call(market, strike) - black_scholes_put(market, strike) -
           (terms.forward_spot - terms.discounted_strike);
}

} // namespace quantrisk
