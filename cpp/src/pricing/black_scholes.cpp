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

MixedFourthDerivatives black_scholes_mixed_fourth_derivatives(const EuropeanOption &option,
                                                              const MarketParams &market) {
    market.validate();
    option.validate();

    MixedFourthDerivatives mixed;
    if (is_degenerate(market)) {
        /// The same limit again, one order further in: with no volatility the value is
        /// piecewise linear in the forward and flat in the volatility, so there is no
        /// fourth-order cross term to report. Every line below divides by `v^3`, which at
        /// `sigma == 0` or `T == 0` would be an inf rather than the limit.
        return mixed;
    }

    const Terms terms = terms_of(market, option.strike);
    const Real first = d1(option, market);
    const Real root_t = std::sqrt(market.maturity);
    const Real sigma = market.volatility;
    const Real v = sigma * root_t;
    const Real second = first - v;
    const Real spot = market.spot;

    /// `P = e^{-qT} phi(d1)`, the prefactor the §8 shape puts in front of all five; and
    /// `v^3`, the denominator all five share.
    const Real prefactor = terms.growth_discount * normal_pdf(first);
    const Real inv_v3 = 1.0 / (v * v * v);

    /// Each line is the §8 shape `P S^(1 - n_spot) T^(n_vol / 2) R(d1, v) / v^3` for one
    /// of the four mixed numerators, written as Horner in `d1` with each coefficient a
    /// polynomial in `v`. The numerators are the ones the report records and re-derives;
    /// they are not restated here so that a slip has exactly one place to be fixed.
    const Real r31 = first * (v * v + 3.0 - first * first);
    const Real r22 =
        first * first * second * second - 5.0 * first * first + 5.0 * first * v - v * v + 2.0;

    const Real v2 = v * v;
    const Real v3 = v2 * v;
    const Real r13 =
        ((((-first + 3.0 * v) * first + (7.0 - 3.0 * v2)) * first + (v3 - 12.0 * v)) * first +
         6.0 * (v2 - 1.0)) *
            first +
        (3.0 * v - v3);
    const Real r04 =
        (((((first - 3.0 * v) * first + (3.0 * v2 - 9.0)) * first + (18.0 * v - v3)) * first +
          12.0 * (1.0 - v2)) *
             first +
         3.0 * v * (v2 - 4.0)) *
            first +
        3.0 * v2;

    mixed.spot_spot_spot_sigma = prefactor * r31 * root_t / (spot * spot) * inv_v3;
    mixed.spot_spot_sigma_sigma = prefactor * r22 * market.maturity / spot * inv_v3;
    mixed.spot_sigma_sigma_sigma = prefactor * r13 * (market.maturity * root_t) * inv_v3;
    mixed.sigma_sigma_sigma_sigma =
        prefactor * spot * r04 * (market.maturity * market.maturity) * inv_v3;
    return mixed;
}

MixedFifthDerivatives black_scholes_mixed_fifth_derivatives(const EuropeanOption &option,
                                                            const MarketParams &market) {
    market.validate();
    option.validate();

    MixedFifthDerivatives mixed;
    if (is_degenerate(market)) {
        /// The same limit one order further in: with no volatility the value is piecewise linear in
        /// the forward and flat in the volatility, so there is no fifth-order cross term to report.
        /// Every line below divides by `v^4`, which at `sigma == 0` or `T == 0` would be an inf
        /// rather than the limit.
        return mixed;
    }

    const Terms terms = terms_of(market, option.strike);
    const Real first = d1(option, market);
    const Real root_t = std::sqrt(market.maturity);
    const Real sigma = market.volatility;
    const Real v = sigma * root_t;
    const Real spot = market.spot;

    /// `P = e^{-qT} phi(d1)`, the prefactor the §2 shape puts in front of all six, and `v^4`, the
    /// denominator all six share -- one more power of `v` than the fourth-order family, which is
    /// what differentiating `P / (S v)` once more has to produce.
    const Real prefactor = terms.growth_discount * normal_pdf(first);
    const Real inv_v4 = 1.0 / (v * v * v * v);

    /// Each numerator is the polynomial `R(d1, v)` of §2, written as an explicit sum of monomials
    /// rather than Horner so that the emitted text is the polynomial the derivation produced, term
    /// for term. The derivation and its verification are in
    /// `docs/phase_reports/phase-20-fifth-order-partials.md` §2; the Catch2 cross-checks below are
    /// the reason a slip here cannot survive, since each of these six is the derivative of a
    /// partial this file already publishes.
    const Real q50 = -first * first * first - 6.0 * first * first * v - 11.0 * first * v * v +
                     3.0 * first - 6.0 * v * v * v + 6.0 * v;
    const Real q41 = first * first * first * first + 2.0 * first * first * first * v -
                     first * first * v * v - 6.0 * first * first - 2.0 * first * v * v * v -
                     6.0 * first * v + v * v + 3.0;
    const Real q32 = -first * first * first * first * first + first * first * first * first * v +
                     first * first * first * v * v + 9.0 * first * first * first -
                     first * first * v * v * v - 6.0 * first * first * v - 2.0 * first * v * v -
                     12.0 * first + v * v * v + 3.0 * v;
    const Real q23 = first * first * first * first * first * first -
                     3.0 * first * first * first * first * first * v +
                     3.0 * first * first * first * first * v * v -
                     12.0 * first * first * first * first - first * first * first * v * v * v +
                     24.0 * first * first * first * v - 15.0 * first * first * v * v +
                     27.0 * first * first + 3.0 * first * v * v * v - 27.0 * first * v +
                     6.0 * v * v - 6.0;
    const Real q14 = -first * first * first * first * first * first * first +
                     4.0 * first * first * first * first * first * first * v -
                     6.0 * first * first * first * first * first * v * v +
                     15.0 * first * first * first * first * first +
                     4.0 * first * first * first * first * v * v * v -
                     42.0 * first * first * first * first * v -
                     first * first * first * v * v * v * v + 42.0 * first * first * first * v * v -
                     48.0 * first * first * first - 18.0 * first * first * v * v * v +
                     78.0 * first * first * v + 3.0 * first * v * v * v * v - 39.0 * first * v * v +
                     24.0 * first + 6.0 * v * v * v - 12.0 * v;
    const Real q05 =
        first * first * first * first * first * first * first * first -
        4.0 * first * first * first * first * first * first * first * v +
        6.0 * first * first * first * first * first * first * v * v -
        18.0 * first * first * first * first * first * first -
        4.0 * first * first * first * first * first * v * v * v +
        54.0 * first * first * first * first * first * v +
        first * first * first * first * v * v * v * v -
        60.0 * first * first * first * first * v * v + 75.0 * first * first * first * first +
        30.0 * first * first * first * v * v * v - 150.0 * first * first * first * v -
        6.0 * first * first * v * v * v * v + 105.0 * first * first * v * v - 60.0 * first * first -
        30.0 * first * v * v * v + 60.0 * first * v + 3.0 * v * v * v * v - 15.0 * v * v;

    const Real t2 = market.maturity * market.maturity;
    mixed.spot_spot_spot_spot_spot = prefactor * q50 * inv_v4 / (spot * spot * spot * spot);
    mixed.spot_spot_spot_spot_sigma = prefactor * q41 * root_t * inv_v4 / (spot * spot * spot);
    mixed.spot_spot_spot_sigma_sigma = prefactor * q32 * market.maturity * inv_v4 / (spot * spot);
    mixed.spot_spot_sigma_sigma_sigma =
        prefactor * q23 * (market.maturity * root_t) * inv_v4 / spot;
    mixed.spot_sigma_sigma_sigma_sigma = prefactor * q14 * t2 * inv_v4;
    mixed.sigma_sigma_sigma_sigma_sigma = prefactor * spot * q05 * (t2 * root_t) * inv_v4;
    return mixed;
}

Real put_call_parity_residual(const MarketParams &market, const Real strike) {
    const Terms terms = terms_of(market, strike);
    return black_scholes_call(market, strike) - black_scholes_put(market, strike) -
           (terms.forward_spot - terms.discounted_strike);
}

} // namespace quantrisk
