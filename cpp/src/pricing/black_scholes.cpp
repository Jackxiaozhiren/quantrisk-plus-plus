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

SpotDerivatives black_scholes_spot_derivatives(const EuropeanOption &option,
                                               const MarketParams &market) {
    market.validate();
    option.validate();

    SpotDerivatives derivatives;
    if (is_degenerate(market)) {
        /// The same sigma -> 0+ / T -> 0+ limit the Greeks take above, where Gamma is
        /// set to zero: with no volatility the value is piecewise linear in the
        /// forward, so it has no third or fourth spot derivative away from the strike
        /// kink, and an expired contract has none anywhere. Zero is the limit, not a
        /// stand-in for a division by `sigma * sqrt(T)` that would report inf.
        return derivatives;
    }

    const Terms terms = terms_of(market, option.strike);
    const Real first = d1(option, market);
    const Real sigma_root_t = market.volatility * std::sqrt(market.maturity);

    /// Gamma exactly as §3 and `black_scholes_greeks` define it, so the two
    /// derivatives below are the derivative of the published number rather than a
    /// second implementation of the same density.
    const Real gamma = terms.growth_discount * normal_pdf(first) / (market.spot * sigma_root_t);
    const Real a = 1.0 + first / sigma_root_t;

    derivatives.third = -(gamma / market.spot) * a;
    derivatives.fourth =
        (gamma / (market.spot * market.spot)) * (a * a + a - 1.0 / (sigma_root_t * sigma_root_t));
    return derivatives;
}

VolCrossDerivatives black_scholes_vol_cross_derivatives(const EuropeanOption &option,
                                                        const MarketParams &market) {
    market.validate();
    option.validate();

    VolCrossDerivatives cross;
    if (is_degenerate(market)) {
        /// Zero is the sigma -> 0+ limit of both, for the same reason Gamma is set to
        /// zero there: with no volatility the value has no curvature in either factor to
        /// cross. Anything else here would be the `sigma` in each denominator reporting
        /// inf rather than a statement about the model.
        return cross;
    }

    const Terms terms = terms_of(market, option.strike);
    const Real first = d1(option, market);
    const Real root_t = std::sqrt(market.maturity);
    const Real sigma_root_t = market.volatility * root_t;
    const Real second = first - sigma_root_t;
    const Real density = normal_pdf(first);

    /// Vega exactly as §3 and `black_scholes_greeks` define it, so volga below is the
    /// derivative of the published number and not a second implementation of the density.
    const Real vega = market.spot * terms.growth_discount * density * root_t;

    cross.vanna = -terms.growth_discount * density * second / market.volatility;
    cross.volga = vega * first * second / market.volatility;
    return cross;
}

MixedThirdDerivatives black_scholes_mixed_third_derivatives(const EuropeanOption &option,
                                                            const MarketParams &market) {
    market.validate();
    option.validate();

    MixedThirdDerivatives mixed;
    if (is_degenerate(market)) {
        /// The same limit as above, one order further in.
        return mixed;
    }

    const Terms terms = terms_of(market, option.strike);
    const Real first = d1(option, market);
    const Real root_t = std::sqrt(market.maturity);
    const Real sigma = market.volatility;
    const Real sigma_root_t = sigma * root_t;
    const Real second = first - sigma_root_t;
    const Real density = normal_pdf(first);

    const Real gamma = terms.growth_discount * density / (market.spot * sigma_root_t);
    const Real vega = market.spot * terms.growth_discount * density * root_t;

    /// Each line is the derivative of the published Gamma, Vega or Vanna in one of the
    /// two factors, which is what makes the homogeneity identities asserted in
    /// `tests/cpp/test_black_scholes.cpp` cross-checks rather than restatements.
    mixed.spot_spot_sigma = gamma * (first * second - 1.0) / sigma;
    mixed.spot_sigma_sigma = terms.growth_discount * density *
                             (second * (2.0 - first * second) / (sigma * sigma) + root_t / sigma);
    mixed.sigma_sigma_sigma = (vega / (sigma * sigma)) * (second * second * (first * first - 1.0) -
                                                          first * second - first * first);
    return mixed;
}

Real put_call_parity_residual(const MarketParams &market, const Real strike) {

    const Terms terms = terms_of(market, strike);
    return black_scholes_call(market, strike) - black_scholes_put(market, strike) -
           (terms.forward_spot - terms.discounted_strike);
}

} // namespace quantrisk
