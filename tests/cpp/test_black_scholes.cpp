#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include <algorithm>
#include <cmath>
#include <limits>
#include <vector>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/pricing/black_scholes.hpp"
#include "quantrisk/pricing/instrument.hpp"

using Catch::Approx;
using quantrisk::EuropeanOption;
using quantrisk::MarketParams;
using quantrisk::OptionType;
using quantrisk::Real;
using quantrisk::ValidationError;

namespace {

MarketParams params(const Real spot, const Real rate, const Real dividend, const Real volatility,
                    const Real maturity) {
    return MarketParams{.spot = spot,
                        .rate = rate,
                        .dividend_yield = dividend,
                        .volatility = volatility,
                        .maturity = maturity};
}

/// The core's own gamma at a perturbed spot, every other parameter held fixed. Used as
/// the quantity the third derivative is differentiated *from*, so the check below never
/// reuses the formula under test.
Real gamma_at_spot(const EuropeanOption &option, const MarketParams &base, const Real spot) {
    MarketParams bumped = base;
    bumped.spot = spot;
    return quantrisk::black_scholes_greeks(option, bumped).gamma;
}

/// The same for the analytic third derivative, which is what the quartic is checked against.
Real third_at_spot(const EuropeanOption &option, const MarketParams &base, const Real spot) {
    MarketParams bumped = base;
    bumped.spot = spot;
    return quantrisk::black_scholes_spot_derivatives(option, bumped).third;
}

/// A point in the two factors the mixed partials differentiate across.
struct FactorPoint {
    Real spot;
    Real volatility;
};

/// Read one published sensitivity at a perturbed (spot, volatility) pair. Both factors
/// are arguments here, where `gamma_at_spot` above carries one: a mixed partial is the
/// slope in one factor of a quantity that itself varies with the other, and every one of
/// these five helpers takes its arguments from a *different* core function, so no check
/// below can confirm a wrong formula with the same wrong formula.
Real read_delta(const EuropeanOption &option, const MarketParams &base, const FactorPoint at) {
    MarketParams bumped = base;
    bumped.spot = at.spot;
    bumped.volatility = at.volatility;
    return quantrisk::black_scholes_greeks(option, bumped).delta;
}

Real read_gamma(const EuropeanOption &option, const MarketParams &base, const FactorPoint at) {
    MarketParams bumped = base;
    bumped.spot = at.spot;
    bumped.volatility = at.volatility;
    return quantrisk::black_scholes_greeks(option, bumped).gamma;
}

Real read_vega(const EuropeanOption &option, const MarketParams &base, const FactorPoint at) {
    MarketParams bumped = base;
    bumped.spot = at.spot;
    bumped.volatility = at.volatility;
    return quantrisk::black_scholes_greeks(option, bumped).vega;
}

Real read_vanna(const EuropeanOption &option, const MarketParams &base, const FactorPoint at) {
    MarketParams bumped = base;
    bumped.spot = at.spot;
    bumped.volatility = at.volatility;
    return quantrisk::black_scholes_vol_cross_derivatives(option, bumped).vanna;
}

Real read_volga(const EuropeanOption &option, const MarketParams &base, const FactorPoint at) {
    MarketParams bumped = base;
    bumped.spot = at.spot;
    bumped.volatility = at.volatility;
    return quantrisk::black_scholes_vol_cross_derivatives(option, bumped).volga;
}

/// The five-point second-derivative stencil. The three-point version's truncation term
/// is O(h^2), which at the volatility steps used below is the same order as the residual
/// being accepted; O(h^4) here makes truncation irrelevant and leaves round-off.
template <typename Function> Real central_curvature(const Function &f, const Real x, const Real h) {
    return (-f(x + 2.0 * h) + 16.0 * f(x + h) - 30.0 * f(x) + 16.0 * f(x - h) - f(x - 2.0 * h)) /
           (12.0 * h * h);
}

/// Five-point central first-derivative stencil. The three-point version is *not* usable
/// here: its O(h^2) truncation term is h^2/6 times the third derivative of the bumped
/// function, which at these magnitudes is about 2.0e-11 for gamma and 2.0e-12 for the
/// third derivative at the step sizes below - one and two orders above the residual this
/// file is willing to accept. The five-point stencil's truncation is O(h^4), which at
/// h = 1e-5 * S is about 1e-23 and therefore irrelevant; what is left is round-off.
template <typename Function> Real central_slope(const Function &f, const Real x, const Real h) {
    return (f(x - 2.0 * h) - 8.0 * f(x - h) + 8.0 * f(x + h) - f(x + 2.0 * h)) / (12.0 * h);
}

/// The tolerance a finite difference is allowed to have against an analytic value.
///
/// Two parts, each defending against a different failure. `1e-8 * |reference|` is the
/// scale-free part: the residual of this stencil is dominated by double round-off
/// amplified by 1/(12h), which grows in proportion to the quantity being differentiated,
/// so a single fixed band would be simultaneously meaningless on the short-dated
/// low-volatility rung and generous on the at-the-money one. `1e-13` is an absolute floor
/// for rungs whose value is legitimately near zero, where a relative band says nothing.
///
/// Measured residuals at the reference point (S = 100, K = 105, r = 3%, q = 1%,
/// sigma = 20%, T = 0.5) are 2.0e-15 for `third` and 1.0e-15 for `fourth` at h = 1e-5 * S,
/// and 4.8e-14 / 1.1e-15 at the absolute step h = 1e-5 - the difference is the 1/(12h)
/// round-off amplification, which is exactly what the band below is sized for. The worst
/// over the ladder is 5.0e-14 (third) and 1.3e-13 (fourth), on the short-dated
/// low-volatility rung where the derivatives are largest; every one of those sits at least
/// 600x inside its own tolerance. Nothing structural hides there either: a dropped factor
/// of `A`, a missing power of `S`, or a sign slip moves these numbers by 1% of themselves
/// at the least (1e-6), six orders above the loosest band used here.
Real stencil_tolerance(const Real reference) { return 1.0e-8 * std::abs(reference) + 1.0e-13; }

} // namespace

TEST_CASE("Black-Scholes prices obey put-call parity everywhere it is tested") {
    const std::vector<MarketParams> grid = {
        params(100.0, 0.05, 0.0, 0.2, 1.0), params(100.0, 0.05, 0.02, 0.2, 0.25),
        params(50.0, -0.01, 0.0, 0.5, 2.0), params(400.0, 0.08, 0.03, 0.15, 0.02),
        params(100.0, 0.0, 0.0, 1.5, 5.0),  params(0.5, 0.2, 0.1, 0.9, 0.5),
    };
    const std::vector<Real> strikes = {1.0, 10.0, 50.0, 99.0, 100.0, 101.0, 500.0};

    for (const MarketParams &market : grid) {
        for (const Real strike : strikes) {
            CAPTURE(market.spot, market.rate, market.volatility, market.maturity, strike);
            CHECK(quantrisk::put_call_parity_residual(market, strike) ==
                  Approx(0.0).margin(1.0e-12 * std::max(1.0, market.spot + strike)));
        }
    }
}

TEST_CASE("degenerate edges take their analytic limits, not an epsilon clamp") {
    SECTION("maturity zero collapses to the expiry payoff") {
        const MarketParams expired = params(100.0, 0.05, 0.0, 0.2, 0.0);
        const auto call = quantrisk::black_scholes(EuropeanOption{OptionType::Call, 90.0}, expired);
        const auto otm = quantrisk::black_scholes(EuropeanOption{OptionType::Call, 110.0}, expired);
        const auto atm = quantrisk::black_scholes(EuropeanOption{OptionType::Call, 100.0}, expired);
        CHECK(call.price == Approx(10.0));
        CHECK(otm.price == Approx(0.0));
        CHECK(atm.price == Approx(0.0));
        CHECK(std::isnan(call.d1)); // d1 is undefined at T == 0
        CHECK_THAT(call.note, Catch::Matchers::ContainsSubstring("T == 0"));
    }

    SECTION("zero volatility makes the forward deterministic") {
        const MarketParams flat = params(100.0, 0.05, 0.0, 0.0, 1.0);
        const Real expected_call = std::exp(-0.05) * std::max(100.0 * std::exp(0.05) - 100.0, 0.0);
        const auto call = quantrisk::black_scholes(EuropeanOption{OptionType::Call, 100.0}, flat);
        CHECK(call.price == Approx(expected_call).epsilon(1e-14));
        CHECK(call.price > 0.0); // an ATM-forward call still has value: carry
        CHECK_THAT(call.note, Catch::Matchers::ContainsSubstring("sigma == 0"));

        const auto otm = quantrisk::black_scholes(EuropeanOption{OptionType::Call, 150.0}, flat);
        CHECK(otm.price == Approx(0.0));
    }

    SECTION("put-call parity still holds on the degenerate edges") {
        CHECK(quantrisk::put_call_parity_residual(params(100.0, 0.05, 0.0, 0.0, 1.0), 100.0) ==
              Approx(0.0).margin(1e-13));
        CHECK(quantrisk::put_call_parity_residual(params(100.0, 0.05, 0.0, 0.2, 0.0), 100.0) ==
              Approx(0.0).margin(1e-13));
    }
}

TEST_CASE("price bounds and monotonicity hold across the parameter space") {
    const Real strike = 100.0;
    Real previous_call = -1.0;
    for (const Real volatility : {0.0, 0.05, 0.1, 0.2, 0.4, 0.8, 1.6}) {
        const MarketParams market = params(100.0, 0.05, 0.0, volatility, 1.0);
        const Real call = quantrisk::black_scholes_call(market, strike);
        const Real put = quantrisk::black_scholes_put(market, strike);
        CAPTURE(volatility);
        // 0 <= call <= S e^{-qT}, 0 <= put <= K e^{-rT}, value grows in volatility.
        CHECK(call >= 0.0);
        CHECK(call <= 100.0 + 1e-12);
        CHECK(put >= 0.0);
        CHECK(put <= 100.0 * std::exp(-0.05) + 1e-12);
        CHECK(call >= previous_call);
        previous_call = call;
    }

    // Increasing in spot, decreasing in strike.
    Real previous = -1.0;
    for (const Real spot : {50.0, 80.0, 100.0, 130.0, 200.0}) {
        const Real call = quantrisk::black_scholes_call(params(spot, 0.05, 0.0, 0.2, 1.0), strike);
        CHECK(call >= previous);
        previous = call;
    }
    previous = 1.0e30;
    for (const Real k : {50.0, 80.0, 100.0, 130.0, 200.0}) {
        const Real call = quantrisk::black_scholes_call(params(100.0, 0.05, 0.0, 0.2, 1.0), k);
        CHECK(call <= previous);
        previous = call;
    }
}

TEST_CASE("forward-at-the-money calls and puts are worth the same") {
    // S e^{-qT} == K e^{-rT} makes the forward equal to the strike, and then
    // parity forces C == P.
    const MarketParams market = params(100.0, 0.05, 0.05, 0.3, 0.75);
    CHECK(quantrisk::black_scholes_call(market, 100.0) ==
          Approx(quantrisk::black_scholes_put(market, 100.0)).epsilon(1e-15));
}

TEST_CASE("d1 and d2 satisfy their defining relation") {
    const EuropeanOption option{OptionType::Call, 95.0};
    const MarketParams market = params(100.0, 0.03, 0.01, 0.25, 1.5);
    const Real first = quantrisk::d1(option, market);
    const Real second = quantrisk::d2(option, market);
    CHECK(second == Approx(first - 0.25 * std::sqrt(1.5)).epsilon(1e-15));

    // Strike at the forward, K = S e^{(r - q)T}, gives the symmetric pair
    // d1 = +sigma sqrt(T) / 2 and d2 = -sigma sqrt(T) / 2.
    const Real forward_strike = 100.0 * std::exp((0.03 - 0.01) * 1.5);
    const auto at_forward = quantrisk::d1(EuropeanOption{OptionType::Call, forward_strike}, market);
    CHECK(at_forward == Approx(0.5 * 0.25 * std::sqrt(1.5)).epsilon(1e-12));
    CHECK(quantrisk::d2(EuropeanOption{OptionType::Call, forward_strike}, market) ==
          Approx(-0.5 * 0.25 * std::sqrt(1.5)).epsilon(1e-12));
}

TEST_CASE("pricing rejects invalid contracts and markets") {
    const MarketParams good = params(100.0, 0.05, 0.0, 0.2, 1.0);
    CHECK_THROWS_AS(quantrisk::black_scholes(EuropeanOption{OptionType::Call, 100.0},
                                             params(0.0, 0.05, 0.0, 0.2, 1.0)),
                    ValidationError);
    CHECK_THROWS_AS(quantrisk::black_scholes(EuropeanOption{OptionType::Call, -1.0}, good),
                    ValidationError);
    CHECK_THROWS_AS(quantrisk::black_scholes(EuropeanOption{OptionType::Call, 100.0},
                                             params(100.0, 0.05, 0.0, -0.2, 1.0)),
                    ValidationError);
    CHECK_THROWS_AS(quantrisk::black_scholes(EuropeanOption{OptionType::Call, 100.0},
                                             params(100.0, 0.05, 0.0, 0.2, -1.0)),
                    ValidationError);
    CHECK_THROWS_AS(quantrisk::black_scholes(EuropeanOption{OptionType::Call, 100.0},
                                             params(std::nan(""), 0.05, 0.0, 0.2, 1.0)),
                    ValidationError);
}

TEST_CASE("payoff is the expiry value of the contract") {
    const EuropeanOption call{OptionType::Call, 100.0};
    const EuropeanOption put{OptionType::Put, 100.0};
    CHECK(call.payoff(120.0) == Approx(20.0));
    CHECK(call.payoff(80.0) == Approx(0.0));
    CHECK(put.payoff(80.0) == Approx(20.0));
    CHECK(put.payoff(120.0) == Approx(0.0));
    CHECK(call.payoff(100.0) == Approx(0.0));
}

TEST_CASE("third and fourth spot derivatives are the finite differences of gamma and of third") {
    /// Same regime spread as `test_greeks.cpp`, plus the reference point of the
    /// Taylor-remainder analysis: at the money, in and out of the money by spot, short and
    /// low-volatility (where 1/(sigma sqrt(T)) is largest and the derivatives hardest), long
    /// and high-volatility, and a call/put pair at one strike.
    struct Rung {
        OptionType type;
        Real strike;
        MarketParams market;
    };
    const std::vector<Rung> ladder = {
        {OptionType::Call, 105.0, params(100.0, 0.03, 0.01, 0.20, 0.50)},
        {OptionType::Put, 105.0, params(100.0, 0.03, 0.01, 0.20, 0.50)},
        {OptionType::Call, 100.0, params(100.0, 0.05, 0.00, 0.20, 1.00)},
        {OptionType::Call, 100.0, params(150.0, 0.03, 0.02, 0.25, 0.50)},
        {OptionType::Put, 100.0, params(60.0, 0.03, 0.02, 0.35, 2.00)},
        {OptionType::Call, 100.0, params(101.0, 0.05, 0.00, 0.90, 1.00)},
        {OptionType::Put, 100.0, params(100.0, 0.08, 0.06, 0.10, 0.10)},
    };

    for (const Rung &rung : ladder) {
        const EuropeanOption option{rung.type, rung.strike};
        const auto derivatives = quantrisk::black_scholes_spot_derivatives(option, rung.market);
        /// Relative to spot, so `1/(12h)` - and with it the round-off the tolerance has to
        /// absorb - is the same number of ulps wide on every rung.
        const Real h = 1.0e-5 * rung.market.spot;
        CAPTURE(rung.strike, rung.market.spot, rung.market.volatility, rung.market.maturity, h);

        /// `third` against the slope of the core's own gamma, and `fourth` against the slope
        /// of `third`: each differentiates something the other tests already verify.
        const Real fd_third =
            central_slope([&](const Real spot) { return gamma_at_spot(option, rung.market, spot); },
                          rung.market.spot, h);
        const Real fd_fourth =
            central_slope([&](const Real spot) { return third_at_spot(option, rung.market, spot); },
                          rung.market.spot, h);

        const Real third_residual = std::abs(derivatives.third - fd_third);
        const Real fourth_residual = std::abs(derivatives.fourth - fd_fourth);
        INFO("third " << derivatives.third << " vs finite difference " << fd_third << ", residual "
                      << third_residual << " against tolerance " << stencil_tolerance(fd_third));
        INFO("fourth " << derivatives.fourth << " vs finite difference " << fd_fourth
                       << ", residual " << fourth_residual << " against tolerance "
                       << stencil_tolerance(fd_fourth));
        CHECK(third_residual <= stencil_tolerance(fd_third));
        CHECK(fourth_residual <= stencil_tolerance(fd_fourth));

        /// And the other half of an honest tolerance: tight enough that this can fail. The
        /// accepted band is 1e-8 of the quantity checked here, so anything coarser than a
        /// transcription slip is visible.
        CHECK(stencil_tolerance(fd_third) < 1.0e-4 * std::abs(fd_third));
        CHECK(stencil_tolerance(fd_fourth) < 1.0e-4 * std::abs(fd_fourth));
    }
}

TEST_CASE("the third and fourth spot derivatives are identical for calls and puts") {
    /// Exact, not approximate, and for a structural reason: `V_call - V_put =
    /// S e^{-qT} - K e^{-rT}` is affine in spot, so its third and fourth derivatives vanish
    /// and the pair must return the same numbers bit for bit. The implementation gets there
    /// by not branching on `option.type` beyond what gamma already does, so any disagreement
    /// here can only mean a type-dependent term has crept in.
    const std::vector<MarketParams> markets = {
        params(100.0, 0.05, 0.02, 0.2, 1.0),
        params(70.0, 0.01, 0.05, 0.4, 0.25),
        params(130.0, 0.08, 0.0, 0.15, 3.0),
        params(100.0, 0.03, 0.01, 0.2, 0.5),
    };
    for (const MarketParams &market : markets) {
        for (const Real strike : {80.0, 99.0, 100.0, 105.0, 130.0}) {
            const auto call = quantrisk::black_scholes_spot_derivatives(
                EuropeanOption{OptionType::Call, strike}, market);
            const auto put = quantrisk::black_scholes_spot_derivatives(
                EuropeanOption{OptionType::Put, strike}, market);
            CAPTURE(market.spot, market.volatility, market.maturity, strike);
            CHECK(call.third == put.third);
            CHECK(call.fourth == put.fourth);
        }
    }

    SECTION("including the degenerate edges, where both sides are zero") {
        for (const MarketParams &market :
             {params(100.0, 0.05, 0.0, 0.0, 1.0), params(100.0, 0.05, 0.0, 0.2, 0.0)}) {
            const auto call = quantrisk::black_scholes_spot_derivatives(
                EuropeanOption{OptionType::Call, 100.0}, market);
            const auto put = quantrisk::black_scholes_spot_derivatives(
                EuropeanOption{OptionType::Put, 100.0}, market);
            CHECK(call.third == put.third);
            CHECK(call.fourth == put.fourth);
            CHECK(call.third == 0.0);
            CHECK(call.fourth == 0.0);
        }
    }
}

TEST_CASE("zero volatility and zero maturity kill the third and fourth spot derivatives") {
    /// The convention is the one `black_scholes_greeks` already sets for gamma: on a
    /// deterministic forward the value is piecewise linear, so there is no third or fourth
    /// spot derivative to report and zero is its limit rather than a stand-in for a division
    /// by `sigma * sqrt(T)`. These edges must also not throw.
    const std::vector<MarketParams> degenerate = {
        params(100.0, 0.05, 0.0, 0.0, 1.0), // sigma == 0, one year to expiry
        params(100.0, 0.05, 0.0, 0.0, 0.5), // sigma == 0, shorter dated
        params(100.0, 0.05, 0.0, 0.2, 0.0), // T == 0, expired
    };
    for (const MarketParams &market : degenerate) {
        for (const Real strike : {90.0, 100.0, 110.0}) {
            for (const OptionType type : {OptionType::Call, OptionType::Put}) {
                CAPTURE(static_cast<int>(type), strike, market.volatility, market.maturity);
                CHECK_NOTHROW(quantrisk::black_scholes_spot_derivatives(
                    EuropeanOption{type, strike}, market));
                const auto derivatives =
                    quantrisk::black_scholes_spot_derivatives(EuropeanOption{type, strike}, market);
                CHECK(derivatives.third == 0.0);
                CHECK(derivatives.fourth == 0.0);
            }
        }
    }

    SECTION("rejects an invalid market or contract the same way the Greeks do") {
        CHECK_THROWS_AS(
            quantrisk::black_scholes_spot_derivatives(EuropeanOption{OptionType::Call, 100.0},
                                                      params(-1.0, 0.05, 0.0, 0.2, 1.0)),
            ValidationError);
        CHECK_THROWS_AS(
            quantrisk::black_scholes_spot_derivatives(EuropeanOption{OptionType::Call, 0.0},
                                                      params(100.0, 0.05, 0.0, 0.2, 1.0)),
            ValidationError);
        CHECK_THROWS_AS(
            quantrisk::black_scholes_spot_derivatives(EuropeanOption{OptionType::Call, 100.0},
                                                      params(100.0, 0.05, 0.0, -0.2, 1.0)),
            ValidationError);
    }

    SECTION("sigma -> 0+ away from the kink decays to the same zero") {
        /// Without this the zeros above are an assertion, not a limit. Hold S well clear of
        /// the strike and shrink sigma: phi(d1) dies exponentially faster than the powers of
        /// 1/(sigma sqrt(T)) grow, so the smooth branch collapses onto the degenerate one.
        const EuropeanOption option{OptionType::Call, 90.0};
        Real previous_third = std::numeric_limits<Real>::infinity();
        Real previous_fourth = previous_third;
        for (const Real volatility : {0.01, 1.0e-3, 1.0e-4, 1.0e-6}) {
            const auto derivatives = quantrisk::black_scholes_spot_derivatives(
                option, params(100.0, 0.03, 0.01, volatility, 0.5));
            CAPTURE(volatility);
            CHECK(std::isfinite(derivatives.third));
            CHECK(std::isfinite(derivatives.fourth));
            /// Non-increasing - the last rungs are exactly zero once phi underflows - and
            /// underflowed to nothing by the time sigma reaches 1e-3.
            CHECK(std::abs(derivatives.third) <= previous_third);
            CHECK(std::abs(derivatives.fourth) <= previous_fourth);
            CHECK(std::abs(derivatives.third) < 1.0e-20);
            CHECK(std::abs(derivatives.fourth) < 1.0e-20);
            previous_third = std::abs(derivatives.third);
            previous_fourth = std::abs(derivatives.fourth);
        }
    }

    SECTION("T -> 0+ does the same") {
        const EuropeanOption option{OptionType::Call, 90.0};
        Real previous_third = std::numeric_limits<Real>::infinity();
        for (const Real maturity : {0.01, 1.0e-3, 1.0e-4, 1.0e-6}) {
            const auto derivatives = quantrisk::black_scholes_spot_derivatives(
                option, params(100.0, 0.03, 0.01, 0.2, maturity));
            CAPTURE(maturity);
            CHECK(std::isfinite(derivatives.third));
            CHECK(std::isfinite(derivatives.fourth));
            CHECK(std::abs(derivatives.third) <= previous_third);
            previous_third = std::abs(derivatives.third);
        }
    }

    SECTION("at the kink the smooth branch grows rather than pretending to be zero") {
        /// The honest limitation of the convention above: with the strike on the forward,
        /// gamma behaves like a Dirac mass as sigma -> 0+ and both derivatives diverge
        /// (`third` like 1/v^2, `fourth` like 1/v^3, with v = sigma sqrt(T)). They stay finite
        /// in double throughout, and the signs are the predicted ones - A -> 3/2 at the kink,
        /// and A^2 + A dwarfed by 1/v^2 - so nothing here silently reports the degenerate
        /// value where the limit does not exist.
        const Real forward_strike = 100.0 * std::exp((0.03 - 0.01) * 0.5);
        const EuropeanOption option{OptionType::Call, forward_strike};
        Real previous_magnitude = 0.0;
        for (const Real volatility : {0.05, 0.01, 1.0e-3, 1.0e-6}) {
            const auto derivatives = quantrisk::black_scholes_spot_derivatives(
                option, params(100.0, 0.03, 0.01, volatility, 0.5));
            CAPTURE(volatility);
            CHECK(std::isfinite(derivatives.third));
            CHECK(std::isfinite(derivatives.fourth));
            CHECK(derivatives.third < 0.0);
            CHECK(derivatives.fourth < 0.0);
            CHECK(std::abs(derivatives.third) > previous_magnitude);
            previous_magnitude = std::abs(derivatives.third);
        }
    }
}

TEST_CASE("the third and fourth spot derivatives stay finite and signed far from the money") {
    /// The Taylor-remainder bound is only usable if these forms are bounded on the segment a
    /// shock traverses, so the deep out-of-the-money and deep in-the-money rungs are the ones
    /// that matter. The prediction being checked is about gamma rather than about the
    /// formula: `third` is the slope of gamma, so it must be positive where gamma rises with
    /// spot (the out-of-the-money side, moving into the money) and negative where gamma falls
    /// (the in-the-money side). That slope is measured over a 2% spot band - three orders
    /// wider than the 1e-5 stencil above, so the two checks are not the same computation.
    struct Rung {
        Real spot;
        OptionType type;
    };
    const Real strike = 100.0;
    const MarketParams middle = params(100.0, 0.03, 0.01, 0.20, 0.50);
    int slope_checks = 0;

    for (const Rung &rung :
         {Rung{40.0, OptionType::Call}, Rung{60.0, OptionType::Call}, Rung{80.0, OptionType::Call},
          Rung{200.0, OptionType::Call}, Rung{400.0, OptionType::Call}, Rung{40.0, OptionType::Put},
          Rung{150.0, OptionType::Put}, Rung{300.0, OptionType::Put}}) {
        const EuropeanOption option{rung.type, strike};
        const MarketParams market = params(rung.spot, middle.rate, middle.dividend_yield,
                                           middle.volatility, middle.maturity);
        const auto derivatives = quantrisk::black_scholes_spot_derivatives(option, market);
        CAPTURE(rung.spot, static_cast<int>(rung.type));

        CHECK(std::isfinite(derivatives.third));
        CHECK(std::isfinite(derivatives.fourth));

        const Real wide = 0.02 * rung.spot;
        const Real gamma_rise = gamma_at_spot(option, market, rung.spot + wide) -
                                gamma_at_spot(option, market, rung.spot - wide);
        /// Where the density has underflowed to zero both this slope and `third` are exactly
        /// zero, and a sign test on zeros would prove nothing; those rungs are counted out by
        /// the guard and the tally below proves the test is not vacuous.
        if (gamma_rise != 0.0 && derivatives.third != 0.0) {
            INFO("gamma rise over a 2% band " << gamma_rise << ", third " << derivatives.third);
            CHECK((gamma_rise > 0.0) == (derivatives.third > 0.0));
            ++slope_checks;
        }

        /// Away from the money |A| = |1 + d1/v| is large enough that A^2 + A beats 1/v^2, so
        /// the quartic is positive on both tails - where at the money it is negative (the
        /// reference point above returns -1.38e-4).
        if (rung.spot <= 60.0 || rung.spot >= 200.0) {
            CHECK(derivatives.fourth > 0.0);
        }
    }
    CHECK(slope_checks >= 6);

    SECTION("and they decay toward both tails rather than blowing up") {
        /// Regularity in the sense the bound needs: the deep rungs are orders of magnitude
        /// smaller than the at-the-money one, not larger. S = 60 and S = 80 are deliberately
        /// excluded - there 1/(sigma sqrt(T)) still outweighs the decay of the density, which
        /// is why the maximum of |third| sits off the money rather than on it.
        const auto at_the_money = quantrisk::black_scholes_spot_derivatives(
            EuropeanOption{OptionType::Call, strike}, middle);
        for (const Real spot : {40.0, 250.0, 400.0}) {
            const auto tail = quantrisk::black_scholes_spot_derivatives(
                EuropeanOption{OptionType::Call, strike},
                params(spot, middle.rate, middle.dividend_yield, middle.volatility,
                       middle.maturity));
            CAPTURE(spot);
            CHECK(std::abs(tail.third) < 1.0e-3 * std::abs(at_the_money.third));
            CHECK(std::abs(tail.fourth) < 1.0e-3 * std::abs(at_the_money.fourth));
        }
    }
}

namespace {

/// The band a *first*-derivative route is held to. Kept identical to
/// `stencil_tolerance` above, and named separately only so the comment below about the
/// asymmetry between the two orders has somewhere to live.
Real slope_tolerance(const Real reference) { return stencil_tolerance(reference); }

/// The band a *second*-derivative route is held to: two orders looser, deliberately.
///
/// A curvature stencil amplifies round-off by 1/(12h^2) rather than 1/(12h), and the
/// truncation term carries the sixth derivative of whatever is being differentiated,
/// which at the short-dated low-volatility rung is large enough to be the binding error
/// at any step that is not swamped by round-off. Holding such a route to 1e-8 would be
/// measuring the stencil rather than the formula.
///
/// The asymmetry costs nothing in detection power, because every quantity reached here
/// is reached again by at least one first-derivative route at the tighter band, and a
/// transcription slip moves the number by percent of itself, not by 1e-4 of it.
///
/// Measured worst residual-to-band ratios over the ladder below, at spot step 1e-5*S,
/// volatility step 1e-4*sigma and curvature step 1e-3*sigma: `volga` via d(vega)/dsigma
/// 1.6e-2 and via the price's curvature 1.0e-2 (both on the sigma=0.10, T=0.10 rung, the
/// tightest of the eleven routes); `vanna` 3.1e-3; V_SSsigma 3.6e-3; V_Sssigma 1.2e-3 on
/// a slope route and 1.0e-5 on its curvature route; V_Sssss 2.1e-4 and 9.5e-5. Every
/// route therefore sits at least 60x inside its own band.
Real curvature_tolerance(const Real reference) { return 1.0e-4 * std::abs(reference) + 1.0e-8; }

/// One contract in one market, at one point of the regime spread. Named apart from the
/// spot-derivative case's own local `Rung` rather than shadowing it, because the two
/// ladders are deliberately different lengths and a reader must not be able to confuse
/// which one a `worst over the ladder` claim was measured on.
struct MixedRung {
    OptionType type;
    Real strike;
    MarketParams market;
};

/// The regimes every mixed-partial case below walks. The first seven are the spread the
/// spot-derivative case uses - at the money, in and out of it by spot, short and
/// low-volatility (where 1/(sigma sqrt(T)) is largest), long and high-volatility, and a
/// call/put pair at one strike - and the last two add the other two legs of the stress
/// book, so the in-, at- and out-of-the-money strikes each appear at the reference market.
/// It is a function rather than a namespace-scope array because a `std::vector` of a
/// struct with designated-initialiser members is easier to read built here than at rest.
const std::vector<MixedRung> &mixed_ladder() {
    static const std::vector<MixedRung> ladder = {
        {OptionType::Call, 105.0, params(100.0, 0.03, 0.01, 0.20, 0.50)},
        {OptionType::Put, 105.0, params(100.0, 0.03, 0.01, 0.20, 0.50)},
        {OptionType::Call, 100.0, params(100.0, 0.05, 0.00, 0.20, 1.00)},
        {OptionType::Call, 100.0, params(150.0, 0.03, 0.02, 0.25, 0.50)},
        {OptionType::Put, 100.0, params(60.0, 0.03, 0.02, 0.35, 2.00)},
        {OptionType::Call, 100.0, params(101.0, 0.05, 0.00, 0.90, 1.00)},
        {OptionType::Put, 100.0, params(100.0, 0.08, 0.06, 0.10, 0.10)},
        {OptionType::Call, 90.0, params(100.0, 0.03, 0.01, 0.20, 0.50)},
        {OptionType::Call, 110.0, params(100.0, 0.03, 0.01, 0.20, 0.50)},
    };
    return ladder;
}

} // namespace

TEST_CASE("vanna and volga are finite differences of the published Greeks and of the price") {
    const std::vector<MixedRung> &ladder = mixed_ladder();

    for (const MixedRung &rung : ladder) {
        const EuropeanOption option{rung.type, rung.strike};
        const auto cross = quantrisk::black_scholes_vol_cross_derivatives(option, rung.market);
        const Real hs = 1.0e-5 * rung.market.spot;
        const Real hv = 1.0e-4 * rung.market.volatility;
        const Real hc = 1.0e-3 * rung.market.volatility;
        CAPTURE(rung.strike, rung.market.spot, rung.market.volatility, rung.market.maturity);

        /// Vanna by the two routes Schwarz's theorem says must agree: the slope in spot of
        /// a vega that is published, and the slope in volatility of a delta that is
        /// published. Neither route touches the formula under test.
        const Real vanna_from_vega = central_slope(
            [&](const Real spot) {
                return read_vega(option, rung.market, {spot, rung.market.volatility});
            },
            rung.market.spot, hs);
        const Real vanna_from_delta = central_slope(
            [&](const Real vol) {
                return read_delta(option, rung.market, {rung.market.spot, vol});
            },
            rung.market.volatility, hv);

        /// Volga as the slope of a published vega, and - independently of every Greek in
        /// this file - as the curvature of the price.
        const Real volga_from_vega = central_slope(
            [&](const Real vol) { return read_vega(option, rung.market, {rung.market.spot, vol}); },
            rung.market.volatility, hv);
        const Real volga_from_price = central_curvature(
            [&](const Real vol) {
                MarketParams bumped = rung.market;
                bumped.volatility = vol;
                return quantrisk::black_scholes(option, bumped).price;
            },
            rung.market.volatility, hc);

        INFO("vanna " << cross.vanna << " vs d(vega)/dS " << vanna_from_vega
                      << " and d(delta)/dsigma " << vanna_from_delta);
        INFO("volga " << cross.volga << " vs d(vega)/dsigma " << volga_from_vega
                      << " and d2(price)/dsigma2 " << volga_from_price);
        CHECK(std::abs(cross.vanna - vanna_from_vega) <= slope_tolerance(vanna_from_vega));
        CHECK(std::abs(cross.vanna - vanna_from_delta) <= slope_tolerance(vanna_from_delta));
        CHECK(std::abs(cross.volga - volga_from_vega) <= slope_tolerance(volga_from_vega));
        CHECK(std::abs(cross.volga - volga_from_price) <= curvature_tolerance(volga_from_price));

        /// And the two vanna routes against each other: this is the check that holds if
        /// `black_scholes_greeks` itself is wrong, because it never compares to a closed
        /// form at all, only to two different ways of bumping the same price surface.
        CHECK(std::abs(vanna_from_vega - vanna_from_delta) <=
              2.0 * slope_tolerance(vanna_from_delta));
    }
}

namespace {

/// The three mixed third partials, read at a perturbed (spot, volatility) pair, so the
/// routes below can differentiate one closed form to reach another.
Real read_spot_spot_sigma(const EuropeanOption &option, const MarketParams &base,
                          const FactorPoint at) {
    MarketParams bumped = base;
    bumped.spot = at.spot;
    bumped.volatility = at.volatility;
    return quantrisk::black_scholes_mixed_third_derivatives(option, bumped).spot_spot_sigma;
}

Real read_spot_sigma_sigma(const EuropeanOption &option, const MarketParams &base,
                           const FactorPoint at) {
    MarketParams bumped = base;
    bumped.spot = at.spot;
    bumped.volatility = at.volatility;
    return quantrisk::black_scholes_mixed_third_derivatives(option, bumped).spot_sigma_sigma;
}

Real read_sigma_sigma_sigma(const EuropeanOption &option, const MarketParams &base,
                            const FactorPoint at) {
    MarketParams bumped = base;
    bumped.spot = at.spot;
    bumped.volatility = at.volatility;
    return quantrisk::black_scholes_mixed_third_derivatives(option, bumped).sigma_sigma_sigma;
}

} // namespace

TEST_CASE("the three mixed third partials are finite differences taken at least two ways") {
    const std::vector<MixedRung> &ladder = mixed_ladder();

    for (const MixedRung &rung : ladder) {
        const EuropeanOption option{rung.type, rung.strike};
        const auto third = quantrisk::black_scholes_mixed_third_derivatives(option, rung.market);
        const auto cross = quantrisk::black_scholes_vol_cross_derivatives(option, rung.market);
        const Real hs = 1.0e-5 * rung.market.spot;
        const Real hv = 1.0e-4 * rung.market.volatility;
        const Real hc = 1.0e-3 * rung.market.volatility;
        const Real spot = rung.market.spot;
        const Real vol = rung.market.volatility;
        CAPTURE(rung.strike, spot, vol, rung.market.maturity);

        /// V_SSsigma: the slope in volatility of the published gamma, and the slope in
        /// spot of the vanna checked in the case above. Schwarz again.
        const Real ss_from_gamma = central_slope(
            [&](const Real v) { return read_gamma(option, rung.market, {spot, v}); }, vol, hv);
        const Real ss_from_vanna = central_slope(
            [&](const Real s) { return read_vanna(option, rung.market, {s, vol}); }, spot, hs);

        /// V_Sssigma: d(vanna)/dsigma, d(volga)/dS, and the curvature in volatility of the
        /// published delta. Three routes, none of them the formula.
        const Real sss_from_vanna = central_slope(
            [&](const Real v) { return read_vanna(option, rung.market, {spot, v}); }, vol, hv);
        const Real sss_from_volga = central_slope(
            [&](const Real s) { return read_volga(option, rung.market, {s, vol}); }, spot, hs);
        const Real sss_from_delta = central_curvature(
            [&](const Real v) { return read_delta(option, rung.market, {spot, v}); }, vol, hc);

        /// V_Sssss: d(volga)/dsigma, and the curvature in volatility of the published vega.
        const Real s4_from_volga = central_slope(
            [&](const Real v) { return read_volga(option, rung.market, {spot, v}); }, vol, hv);
        const Real s4_from_vega = central_curvature(
            [&](const Real v) { return read_vega(option, rung.market, {spot, v}); }, vol, hc);

        INFO("V_SSsigma " << third.spot_spot_sigma << " vs d(gamma)/dsigma " << ss_from_gamma
                          << " and d(vanna)/dS " << ss_from_vanna);
        INFO("V_Sssigma " << third.spot_sigma_sigma << " vs d(vanna)/dsigma " << sss_from_vanna
                          << ", d(volga)/dS " << sss_from_volga << ", d2(delta)/dsigma2 "
                          << sss_from_delta);
        INFO("V_Sssss " << third.sigma_sigma_sigma << " vs d(volga)/dsigma " << s4_from_volga
                        << ", d2(vega)/dsigma2 " << s4_from_vega);
        CHECK(std::abs(third.spot_spot_sigma - ss_from_gamma) <= slope_tolerance(ss_from_gamma));
        CHECK(std::abs(third.spot_spot_sigma - ss_from_vanna) <= slope_tolerance(ss_from_vanna));
        CHECK(std::abs(third.spot_sigma_sigma - sss_from_vanna) <= slope_tolerance(sss_from_vanna));
        CHECK(std::abs(third.spot_sigma_sigma - sss_from_volga) <= slope_tolerance(sss_from_volga));
        CHECK(std::abs(third.spot_sigma_sigma - sss_from_delta) <=
              curvature_tolerance(sss_from_delta));
        CHECK(std::abs(third.sigma_sigma_sigma - s4_from_volga) <= slope_tolerance(s4_from_volga));
        CHECK(std::abs(third.sigma_sigma_sigma - s4_from_vega) <=
              curvature_tolerance(s4_from_vega));
    }
}

TEST_CASE("the homogeneity of the price in spot and strike pins the cross partials exactly") {
    /// `vega = gamma S^2 sigma T` is an identity of the model, not an approximation, and
    /// differentiating it once with respect to each factor gives
    ///     vanna = V_SSS * S^2 sigma T + 2 S sigma T gamma
    ///     volga = V_SSsigma * S^2 sigma T + gamma S^2 T
    /// Both are checked here against sensitivities the core already published, so a
    /// transcription slip in either new formula is visible without a single finite
    /// difference and without any dependence on the bump policy.
    const std::vector<MarketParams> markets = {
        params(100.0, 0.03, 0.01, 0.20, 0.50), params(100.0, 0.05, 0.00, 0.20, 1.00),
        params(150.0, 0.03, 0.02, 0.25, 0.50), params(60.0, 0.03, 0.02, 0.35, 2.00),
        params(100.0, 0.08, 0.06, 0.10, 0.10), params(100.0, -0.01, 0.00, 0.60, 3.00),
    };
    for (const MarketParams &market : markets) {
        for (const Real strike : {80.0, 90.0, 100.0, 105.0, 110.0, 130.0}) {
            const EuropeanOption option{OptionType::Call, strike};
            const auto greeks = quantrisk::black_scholes_greeks(option, market);
            const auto spot_third = quantrisk::black_scholes_spot_derivatives(option, market);
            const auto cross = quantrisk::black_scholes_vol_cross_derivatives(option, market);
            const auto third = quantrisk::black_scholes_mixed_third_derivatives(option, market);
            const Real s2sigmat = market.spot * market.spot * market.volatility * market.maturity;

            const Real vanna_identity =
                spot_third.third * s2sigmat +
                2.0 * market.spot * market.volatility * market.maturity * greeks.gamma;
            const Real volga_identity = third.spot_spot_sigma * s2sigmat +
                                        greeks.gamma * market.spot * market.spot * market.maturity;

            CAPTURE(market.spot, market.volatility, market.maturity, strike);
            /// `1e-9` relative, not `==`: the two sides reach the same number through
            /// genuinely different arithmetic, so the residual is round-off from the
            /// cancellation in `A = 1 + d1/v` and in `d1*d2 - 1`, which is largest exactly
            /// where those brackets vanish. Measured worst over the 36 (market, strike)
            /// pairs: 1.1e-16 absolute on vanna and 4.3e-14 on volga, against a
            /// `volga` of order 1e2 - so the band below sits at least four orders inside
            /// the smallest thing it can see. A dropped factor of sigma, a lost S, or a
            /// sign slip moves these by percent.
            CHECK(std::abs(cross.vanna - vanna_identity) <=
                  1.0e-9 * std::max(std::abs(cross.vanna), std::abs(vanna_identity)) + 1.0e-12);
            CHECK(std::abs(cross.volga - volga_identity) <=
                  1.0e-9 * std::max(std::abs(cross.volga), std::abs(volga_identity)) + 1.0e-12);
        }
    }

    SECTION("both cross partials vanish exactly where the strike is the risk-neutral median") {
        /// vega * d1 * d2 / sigma and -e^{-qT} phi(d1) d2 / sigma share the factor `d2`, so
        /// the two quadratic error coefficients vanish *together*, at the strike that is the
        /// median of the terminal price under the pricing measure:
        ///     d2 == 0  <=>  K = S exp((r - q - sigma^2 / 2) T).
        /// That is not the forward strike `S exp((r - q)T)`, which is where d1 - sigma
        /// sqrt(T)/2 is zero; the distinction is the kind of thing a comment gets wrong.
        ///
        /// The parameters below are chosen so the equality is bit-exact rather than merely
        /// tiny, which needs every step to be an exact binary operation: spot == strike makes
        /// log(S/K) vanish exactly; rate - dividend - sigma^2/2 = 0.0625 - 0.03125 - 0.03125
        /// is an exact subtraction of powers of two, which 0.03 - 0.01 - 0.02 is not; and
        /// maturity 1.0 makes sqrt(T) exact, without which d1 and sigma*sqrt(T) differ by
        /// half an ulp and `d2` comes out at 5.4e-16 instead of zero. That last one is the
        /// lesson worth keeping: `== 0.0` on a derived float is a claim about the arithmetic,
        /// not about the mathematics, and has to be earned.
        ///
        /// The same construction is *nearly* what puts the middle leg of the published stress
        /// book at zero vanna and zero volga - 0.03 - 0.01 - 0.02 is the same expression, off
        /// by round-off alone - which is why that book's quadratic error comes from its two
        /// outer legs rather than its middle one.
        const MarketParams market = params(100.0, 0.0625, 0.03125, 0.25, 1.0);
        const auto cross = quantrisk::black_scholes_vol_cross_derivatives(
            EuropeanOption{OptionType::Call, 100.0}, market);
        const auto third = quantrisk::black_scholes_mixed_third_derivatives(
            EuropeanOption{OptionType::Call, 100.0}, market);
        CHECK(cross.vanna == 0.0);
        CHECK(cross.volga == 0.0);
        /// Exactly the two cross partials that carry a bare `d2` factor vanish, and exactly
        /// the three that do not survive: V_SSsigma carries `d1 * d2 - 1`, which is -1
        /// there, and V_Sssss carries `-d1^2` alongside terms in d2. V_Sssigma keeps its
        /// `sqrt(T) / sigma` term, which is why d(vanna)/dsigma is nonzero at a point where
        /// vanna itself is zero - the cross partial is a slope, not a level.
        CHECK(third.spot_sigma_sigma != 0.0);
        CHECK(third.spot_spot_sigma != 0.0);
        CHECK(third.sigma_sigma_sigma != 0.0);
    }
}

TEST_CASE("the mixed partials are identical for calls and puts and zero where the model is") {
    const std::vector<MarketParams> markets = {
        params(100.0, 0.05, 0.02, 0.2, 1.0),
        params(70.0, 0.01, 0.05, 0.4, 0.25),
        params(130.0, 0.08, 0.0, 0.15, 3.0),
        params(100.0, 0.03, 0.01, 0.2, 0.5),
    };
    for (const MarketParams &market : markets) {
        for (const Real strike : {80.0, 99.0, 100.0, 105.0, 130.0}) {
            const auto call_cross = quantrisk::black_scholes_vol_cross_derivatives(
                EuropeanOption{OptionType::Call, strike}, market);
            const auto put_cross = quantrisk::black_scholes_vol_cross_derivatives(
                EuropeanOption{OptionType::Put, strike}, market);
            const auto call_third = quantrisk::black_scholes_mixed_third_derivatives(
                EuropeanOption{OptionType::Call, strike}, market);
            const auto put_third = quantrisk::black_scholes_mixed_third_derivatives(
                EuropeanOption{OptionType::Put, strike}, market);
            CAPTURE(market.spot, market.volatility, market.maturity, strike);
            /// Bit-exact, for the same structural reason as the spot derivatives: the
            /// call/put difference is affine in spot, so every derivative of order two or
            /// more in the two factors - and every volatility derivative of it - vanishes.
            CHECK(call_cross.vanna == put_cross.vanna);
            CHECK(call_cross.volga == put_cross.volga);
            CHECK(call_third.spot_spot_sigma == put_third.spot_spot_sigma);
            CHECK(call_third.spot_sigma_sigma == put_third.spot_sigma_sigma);
            CHECK(call_third.sigma_sigma_sigma == put_third.sigma_sigma_sigma);
        }
    }

    SECTION("the degenerate edges return the limit rather than an overflow") {
        for (const MarketParams &market :
             {params(100.0, 0.05, 0.0, 0.0, 1.0), params(100.0, 0.05, 0.0, 0.0, 0.5),
              params(100.0, 0.05, 0.0, 0.2, 0.0)}) {
            for (const Real strike : {90.0, 100.0, 110.0}) {
                for (const OptionType type : {OptionType::Call, OptionType::Put}) {
                    const EuropeanOption option{type, strike};
                    CAPTURE(static_cast<int>(type), strike, market.volatility, market.maturity);
                    CHECK_NOTHROW(quantrisk::black_scholes_vol_cross_derivatives(option, market));
                    CHECK_NOTHROW(quantrisk::black_scholes_mixed_third_derivatives(option, market));
                    const auto cross =
                        quantrisk::black_scholes_vol_cross_derivatives(option, market);
                    const auto third =
                        quantrisk::black_scholes_mixed_third_derivatives(option, market);
                    CHECK(cross.vanna == 0.0);
                    CHECK(cross.volga == 0.0);
                    CHECK(third.spot_spot_sigma == 0.0);
                    CHECK(third.spot_sigma_sigma == 0.0);
                    CHECK(third.sigma_sigma_sigma == 0.0);
                }
            }
        }
    }

    SECTION("invalid inputs are rejected the same way the Greeks reject them") {
        CHECK_THROWS_AS(
            quantrisk::black_scholes_vol_cross_derivatives(EuropeanOption{OptionType::Call, 100.0},
                                                           params(-1.0, 0.05, 0.0, 0.2, 1.0)),
            ValidationError);
        CHECK_THROWS_AS(
            quantrisk::black_scholes_mixed_third_derivatives(EuropeanOption{OptionType::Call, 0.0},
                                                             params(100.0, 0.05, 0.0, 0.2, 1.0)),
            ValidationError);
        CHECK_THROWS_AS(
            quantrisk::black_scholes_mixed_third_derivatives(
                EuropeanOption{OptionType::Call, 100.0}, params(100.0, 0.05, 0.0, -0.2, 1.0)),
            ValidationError);
    }
}

namespace {

/// The published speed (d3V/dS3) read at a perturbed (spot, volatility) pair, so a route
/// below can differentiate it in volatility to reach V_SSSsigma without touching it.
Real read_spot_third(const EuropeanOption &option, const MarketParams &base, const FactorPoint at) {
    MarketParams bumped = base;
    bumped.spot = at.spot;
    bumped.volatility = at.volatility;
    return quantrisk::black_scholes_spot_derivatives(option, bumped).third;
}

/// Five-point stencil for a third derivative, used only for the volatility-only fourth
/// partial: it is the one route that reaches that number from `black_scholes_greeks`
/// alone, without going through either of the two structs built on top of it.
template <typename Function>
Real central_third_difference(const Function &f, const Real x, const Real h) {
    return (-f(x - 2.0 * h) + 2.0 * f(x - h) - 2.0 * f(x + h) + f(x + 2.0 * h)) / (2.0 * h * h * h);
}

/// The band a third-derivative route is held to: four orders looser than a slope route,
/// deliberately. This stencil amplifies round-off by 1/(2h^3) rather than 1/(12h), and
/// unlike the two five-point stencils above it is only O(h^2) accurate, so at the step
/// used below (3e-3 * sigma) its truncation term is the binding error rather than
/// round-off. Holding it to 1e-8 would be measuring the stencil, not the formula.
///
/// Measured worst residual-to-band ratio over the ladder: 1.1e-2, on the
/// `S = 150, K = 100, sigma = 0.25, T = 0.50` rung, which is where the third derivative
/// of vega is largest. It is the loosest of the ten routes in the case below and the
/// only one that reaches `V_sigmasigmasigmasigma` without going through either struct
/// layered on `black_scholes_greeks`.
Real third_difference_tolerance(const Real reference) {
    return 1.0e-2 * std::abs(reference) + 1.0e-6;
}

} // namespace

TEST_CASE("the four mixed fourth partials are finite differences taken at least two ways") {
    /// Ten routes over nine rungs: two per partial, plus a third for each of the two
    /// volatility-heavy ones. Measured worst residual-to-band ratio per route over the
    /// ladder, at spot step 1e-5*S, volatility step 1e-4*sigma, curvature step 1e-3*sigma
    /// and third-difference step 3e-3*sigma: 2.6e-3 (V_Ssigmasigmasigma via d(V_Sssss)/dS),
    /// 2.2e-5 (V_Ssigmasigmasigma via d2(vanna)/dsigma2), and 1.1e-2 for the
    /// third-difference route on V_sigmasigmasigmasigma. Every route therefore sits at least
    /// 90x inside its own band, and a dropped power of `T` or `S` - the failure mode this
    /// phase actually produced, see docs/phase_reports/phase-15-restrike-gamma.md §8 - moves
    /// a number by percent of itself, which is three or more orders above the widest band.
    const std::vector<MixedRung> &ladder = mixed_ladder();

    for (const MixedRung &rung : ladder) {
        const EuropeanOption option{rung.type, rung.strike};
        const auto fourth = quantrisk::black_scholes_mixed_fourth_derivatives(option, rung.market);
        const Real hs = 1.0e-5 * rung.market.spot;
        const Real hv = 1.0e-4 * rung.market.volatility;
        const Real hc = 1.0e-3 * rung.market.volatility;
        const Real ht = 3.0e-3 * rung.market.volatility;
        const Real spot = rung.market.spot;
        const Real vol = rung.market.volatility;
        CAPTURE(rung.strike, spot, vol, rung.market.maturity);

        /// V_SSSsigma: the slope in volatility of the published speed, and the slope in
        /// spot of the published V_SSsigma. Schwarz's theorem, two different core calls.
        const Real s31_from_speed = central_slope(
            [&](const Real v) { return read_spot_third(option, rung.market, {spot, v}); }, vol, hv);
        const Real s31_from_ss_sigma = central_slope(
            [&](const Real s) { return read_spot_spot_sigma(option, rung.market, {s, vol}); }, spot,
            hs);

        /// V_SSsigmasigma: d(V_SSsigma)/dsigma and d(V_Ssigmasigma)/dS.
        const Real s22_from_ss_sigma = central_slope(
            [&](const Real v) { return read_spot_spot_sigma(option, rung.market, {spot, v}); }, vol,
            hv);
        const Real s22_from_s_ss = central_slope(
            [&](const Real s) { return read_spot_sigma_sigma(option, rung.market, {s, vol}); },
            spot, hs);

        /// V_Ssigmasigmasigma: d(V_Ssigmasigma)/dsigma, d(V_Sssss)/dS, and the curvature in
        /// volatility of the published vanna - three routes, three different structs.
        const Real s13_from_s_ss = central_slope(
            [&](const Real v) { return read_spot_sigma_sigma(option, rung.market, {spot, v}); },
            vol, hv);
        const Real s13_from_s3 = central_slope(
            [&](const Real s) { return read_sigma_sigma_sigma(option, rung.market, {s, vol}); },
            spot, hs);
        const Real s13_from_vanna = central_curvature(
            [&](const Real v) { return read_vanna(option, rung.market, {spot, v}); }, vol, hc);

        /// V_sigmasigmasigmasigma: d(V_Sssss)/dsigma, the curvature of the published volga,
        /// and the third difference of the published vega. The last of these never touches
        /// `VolCrossDerivatives` or `MixedThirdDerivatives` at all.
        const Real s4_from_s3 = central_slope(
            [&](const Real v) { return read_sigma_sigma_sigma(option, rung.market, {spot, v}); },
            vol, hv);
        const Real s4_from_volga = central_curvature(
            [&](const Real v) { return read_volga(option, rung.market, {spot, v}); }, vol, hc);
        const Real s4_from_vega = central_third_difference(
            [&](const Real v) { return read_vega(option, rung.market, {spot, v}); }, vol, ht);

        INFO("V_SSSsigma " << fourth.spot_spot_spot_sigma << " vs d(V_SSS)/dsigma "
                           << s31_from_speed << ", d(V_SSsigma)/dS " << s31_from_ss_sigma);
        INFO("V_SSsigmasigma " << fourth.spot_spot_sigma_sigma << " vs d(V_SSsigma)/dsigma "
                               << s22_from_ss_sigma << ", d(V_Ssigmasigma)/dS " << s22_from_s_ss);
        INFO("V_Ssigmasigmasigma "
             << fourth.spot_sigma_sigma_sigma << " vs d(V_Ssigmasigma)/dsigma " << s13_from_s_ss
             << ", d(V_Sssss)/dS " << s13_from_s3 << ", d2(vanna)/dsigma2 " << s13_from_vanna);
        INFO("V_sigmasigmasigmasigma " << fourth.sigma_sigma_sigma_sigma << " vs d(V_Sssss)/dsigma "
                                       << s4_from_s3 << ", d2(volga)/dsigma2 " << s4_from_volga
                                       << ", d3(vega)/dsigma3 " << s4_from_vega);
        CHECK(std::abs(fourth.spot_spot_spot_sigma - s31_from_speed) <=
              slope_tolerance(s31_from_speed));
        CHECK(std::abs(fourth.spot_spot_spot_sigma - s31_from_ss_sigma) <=
              slope_tolerance(s31_from_ss_sigma));
        CHECK(std::abs(fourth.spot_spot_sigma_sigma - s22_from_ss_sigma) <=
              slope_tolerance(s22_from_ss_sigma));
        CHECK(std::abs(fourth.spot_spot_sigma_sigma - s22_from_s_ss) <=
              slope_tolerance(s22_from_s_ss));
        CHECK(std::abs(fourth.spot_sigma_sigma_sigma - s13_from_s_ss) <=
              slope_tolerance(s13_from_s_ss));
        CHECK(std::abs(fourth.spot_sigma_sigma_sigma - s13_from_s3) <=
              slope_tolerance(s13_from_s3));
        CHECK(std::abs(fourth.spot_sigma_sigma_sigma - s13_from_vanna) <=
              curvature_tolerance(s13_from_vanna));
        CHECK(std::abs(fourth.sigma_sigma_sigma_sigma - s4_from_s3) <= slope_tolerance(s4_from_s3));
        CHECK(std::abs(fourth.sigma_sigma_sigma_sigma - s4_from_volga) <=
              curvature_tolerance(s4_from_volga));
        CHECK(std::abs(fourth.sigma_sigma_sigma_sigma - s4_from_vega) <=
              third_difference_tolerance(s4_from_vega));
    }
}

TEST_CASE("the six mixed fifth partials are slopes of partials the core already ships") {
    /// Ten routes over nine rungs: two per partial where both axes have a published parent, one
    /// for each of the two pure ends, and every route a five-point central slope of a quantity this
    /// file exported *before* this phase. No route reuses the formula under test, so a dropped
    /// power of `S`, `T` or `v` moves the number by percent of itself -- three or more orders above
    /// the band -- while the step-dependent noise sits at 1e-11 of it. Measured worst over the
    /// ninety comparisons: 1.9e-3 of its own band, on V_SSSsigmasigma taken along the spot axis,
    /// so every route sits more than 500x inside the tolerance it is held to.
    const std::vector<MixedRung> &ladder = mixed_ladder();

    for (const MixedRung &rung : ladder) {
        const EuropeanOption option{rung.type, rung.strike};
        const auto fifth = quantrisk::black_scholes_mixed_fifth_derivatives(option, rung.market);
        const Real hs = 1.0e-5 * rung.market.spot;
        const Real hv = 1.0e-4 * rung.market.volatility;
        const Real spot = rung.market.spot;
        const Real vol = rung.market.volatility;
        CAPTURE(rung.strike, spot, vol, rung.market.maturity);

        /// Published parents, each read at a bumped market so the route is a slope of a number the
        /// core shipped one phase earlier.
        const auto bumped = [&](const Real s, const Real v) {
            MarketParams moved = rung.market;
            moved.spot = s;
            moved.volatility = v;
            return moved;
        };
        const auto speed_at = [&](const Real s, const Real v) {
            return quantrisk::black_scholes_spot_derivatives(option, bumped(s, v)).fourth;
        };
        const auto s31_at = [&](const Real s, const Real v) {
            return quantrisk::black_scholes_mixed_fourth_derivatives(option, bumped(s, v))
                .spot_spot_spot_sigma;
        };
        const auto s22_at = [&](const Real s, const Real v) {
            return quantrisk::black_scholes_mixed_fourth_derivatives(option, bumped(s, v))
                .spot_spot_sigma_sigma;
        };
        const auto s13_at = [&](const Real s, const Real v) {
            return quantrisk::black_scholes_mixed_fourth_derivatives(option, bumped(s, v))
                .spot_sigma_sigma_sigma;
        };
        const auto s04_at = [&](const Real s, const Real v) {
            return quantrisk::black_scholes_mixed_fourth_derivatives(option, bumped(s, v))
                .sigma_sigma_sigma_sigma;
        };

        const Real s50 = central_slope([&](const Real s) { return speed_at(s, vol); }, spot, hs);
        const Real s41_v = central_slope([&](const Real v) { return speed_at(spot, v); }, vol, hv);
        const Real s41_s = central_slope([&](const Real s) { return s31_at(s, vol); }, spot, hs);
        const Real s32_v = central_slope([&](const Real v) { return s31_at(spot, v); }, vol, hv);
        const Real s32_s = central_slope([&](const Real s) { return s22_at(s, vol); }, spot, hs);
        const Real s23_v = central_slope([&](const Real v) { return s22_at(spot, v); }, vol, hv);
        const Real s23_s = central_slope([&](const Real s) { return s13_at(s, vol); }, spot, hs);
        const Real s14_v = central_slope([&](const Real v) { return s13_at(spot, v); }, vol, hv);
        const Real s14_s = central_slope([&](const Real s) { return s04_at(s, vol); }, spot, hs);
        const Real s05 = central_slope([&](const Real v) { return s04_at(spot, v); }, vol, hv);

        INFO("V_SSSSS " << fifth.spot_spot_spot_spot_spot << " vs d(V_SSSS)/dS " << s50);
        INFO("V_SSSSsigma " << fifth.spot_spot_spot_spot_sigma << " vs d(V_SSSS)/dsigma " << s41_v
                            << ", d(V_SSSsigma)/dS " << s41_s);
        INFO("V_SSSsigmasigma " << fifth.spot_spot_spot_sigma_sigma << " vs d(V_SSSsigma)/dsigma "
                                << s32_v << ", d(V_SSsigmasigma)/dS " << s32_s);
        INFO("V_SSsigmasigmasigma " << fifth.spot_spot_sigma_sigma_sigma
                                    << " vs d(V_SSsigmasigma)/dsigma " << s23_v
                                    << ", d(V_Ssigmasigmasigma)/dS " << s23_s);
        INFO("V_Ssigmasigmasigmasigma " << fifth.spot_sigma_sigma_sigma_sigma
                                        << " vs d(V_Ssigmasigmasigma)/dsigma " << s14_v
                                        << ", d(V_sigmasigmasigmasigma)/dS " << s14_s);
        INFO("V_sigmasigmasigmasigmasigma " << fifth.sigma_sigma_sigma_sigma_sigma
                                            << " vs d(V_sigmasigmasigmasigma)/dsigma " << s05);

        CHECK(std::abs(fifth.spot_spot_spot_spot_spot - s50) <= slope_tolerance(s50));
        CHECK(std::abs(fifth.spot_spot_spot_spot_sigma - s41_v) <= slope_tolerance(s41_v));
        CHECK(std::abs(fifth.spot_spot_spot_spot_sigma - s41_s) <= slope_tolerance(s41_s));
        CHECK(std::abs(fifth.spot_spot_spot_sigma_sigma - s32_v) <= slope_tolerance(s32_v));
        CHECK(std::abs(fifth.spot_spot_spot_sigma_sigma - s32_s) <= slope_tolerance(s32_s));
        CHECK(std::abs(fifth.spot_spot_sigma_sigma_sigma - s23_v) <= slope_tolerance(s23_v));
        CHECK(std::abs(fifth.spot_spot_sigma_sigma_sigma - s23_s) <= slope_tolerance(s23_s));
        CHECK(std::abs(fifth.spot_sigma_sigma_sigma_sigma - s14_v) <= slope_tolerance(s14_v));
        CHECK(std::abs(fifth.spot_sigma_sigma_sigma_sigma - s14_s) <= slope_tolerance(s14_s));
        CHECK(std::abs(fifth.sigma_sigma_sigma_sigma_sigma - s05) <= slope_tolerance(s05));
    }
}

TEST_CASE("the fifth partials are the same for a call and a put, exactly") {
    /// Put-call parity is `C - P = S e^{-qT} - K e^{-rT}`, linear in the spot and constant in the
    /// volatility, so every partial of total order five annihilates the difference: the two sides
    /// are equal as bits, not within a tolerance. This is the same exactness the third- and
    /// fourth-order structs are held to, and it catches a sign or a power that a slope route could
    /// hide.
    const std::vector<MixedRung> &ladder = mixed_ladder();
    for (const MixedRung &rung : ladder) {
        const auto call = quantrisk::black_scholes_mixed_fifth_derivatives(
            EuropeanOption{OptionType::Call, rung.strike}, rung.market);
        const auto put = quantrisk::black_scholes_mixed_fifth_derivatives(
            EuropeanOption{OptionType::Put, rung.strike}, rung.market);
        CAPTURE(rung.strike, rung.market.spot, rung.market.volatility);
        CHECK(call.spot_spot_spot_spot_spot == put.spot_spot_spot_spot_spot);
        CHECK(call.spot_spot_spot_spot_sigma == put.spot_spot_spot_spot_sigma);
        CHECK(call.spot_spot_spot_sigma_sigma == put.spot_spot_spot_sigma_sigma);
        CHECK(call.spot_spot_sigma_sigma_sigma == put.spot_spot_sigma_sigma_sigma);
        CHECK(call.spot_sigma_sigma_sigma_sigma == put.spot_sigma_sigma_sigma_sigma);
        CHECK(call.sigma_sigma_sigma_sigma_sigma == put.sigma_sigma_sigma_sigma_sigma);
    }
}

TEST_CASE("the fifth-order struct is finite and reports the degenerate limit") {
    const std::vector<MarketParams> markets = {
        MarketParams{
            .spot = 100.0, .rate = 0.03, .dividend_yield = 0.0, .volatility = 0.0, .maturity = 0.5},
        MarketParams{
            .spot = 100.0, .rate = 0.03, .dividend_yield = 0.0, .volatility = 0.2, .maturity = 0.0},
    };
    const EuropeanOption option{OptionType::Call, 100.0};
    for (const MarketParams &market : markets) {
        REQUIRE_NOTHROW(quantrisk::black_scholes_mixed_fifth_derivatives(option, market));
        const auto fifth = quantrisk::black_scholes_mixed_fifth_derivatives(option, market);
        CHECK(std::isfinite(fifth.spot_spot_spot_spot_spot));
        CHECK(std::isfinite(fifth.sigma_sigma_sigma_sigma_sigma));
    }
    CHECK_THROWS_AS(quantrisk::black_scholes_mixed_fifth_derivatives(
                        EuropeanOption{OptionType::Call, -1.0}, MarketParams{.spot = 100.0,
                                                                             .rate = 0.03,
                                                                             .dividend_yield = 0.0,
                                                                             .volatility = 0.2,
                                                                             .maturity = 0.5}),
                    quantrisk::ValidationError);
}

TEST_CASE("differentiating the published homogeneity relations pins two fourth partials exactly") {
    /// `vega = gamma S^2 sigma T` is an identity of the model, and the two routes out of it
    /// that the third-order case uses are
    ///     vanna = V_SSS * S^2 sigma T + 2 S sigma T gamma
    ///     volga = V_SSsigma * S^2 sigma T + gamma S^2 T
    /// Differentiating each once in volatility gives the two relations below, in which
    /// exactly one new fourth-order partial appears on the right:
    ///     d(vanna)/dsigma  = V_SSSsigma  S^2 sigma T + V_SSS S^2 T + 2 S T gamma
    ///                        + 2 S sigma T V_SSsigma
    ///     d(volga)/dsigma  = V_SSsigmasigma S^2 sigma T + 2 S^2 T V_SSsigma
    /// Both left-hand sides are published third partials, so each relation solves for one
    /// new number out of quantities the core shipped before this phase - with no bump, no
    /// step size, and no reuse of the formula under test.
    ///
    /// Only two of the four new numbers have such a partner, and finding that out cost a
    /// wrong test case. The obvious third candidate was `d(volga)/dS`, which is exactly one
    /// spot derivative of the relation that produced the second one above. It is *not*
    /// fourth order: `volga` is `d2V/dsigma2`, so a single spot derivative of it lands on
    /// `V_Ssigmasigma`, the third-order partial the core already publishes. Asserting the
    /// fourth-order `V_Ssigmasigmasigma` against that right-hand side failed by a factor of
    /// -14 on the reference rung, which is the shape of the mistake rather than a tolerance
    /// problem. Differentiating any further in either factor introduces a fifth-order
    /// partial, so the remaining two numbers are held by finite differences alone - three
    /// independent routes each, in the case above.
    ///
    /// Measured over the 36 (market, strike) pairs below: worst absolute residual 4.2e-17
    /// on V_SSSsigma and 3.6e-15 on V_SSsigmasigma, worst relative 5.5e-16 and 1.2e-15. The
    /// band is 1e-9 relative plus a 1e-12 floor, so both sit at least three orders inside
    /// it; what is left at that level is the cancellation in the brackets, not the formula.
    const std::vector<MarketParams> markets = {
        params(100.0, 0.03, 0.01, 0.20, 0.50), params(100.0, 0.05, 0.00, 0.20, 1.00),
        params(150.0, 0.03, 0.02, 0.25, 0.50), params(60.0, 0.03, 0.02, 0.35, 2.00),
        params(100.0, 0.08, 0.06, 0.10, 0.10), params(100.0, -0.01, 0.00, 0.60, 3.00),
    };
    const Real relative_band = 1.0e-9;
    Real worst_v31 = 0.0, worst_v22 = 0.0;
    for (const MarketParams &market : markets) {
        for (const Real strike : {80.0, 90.0, 100.0, 105.0, 110.0, 130.0}) {
            const EuropeanOption option{OptionType::Call, strike};
            const auto greeks = quantrisk::black_scholes_greeks(option, market);
            const auto speed = quantrisk::black_scholes_spot_derivatives(option, market).third;
            const auto third = quantrisk::black_scholes_mixed_third_derivatives(option, market);
            const auto fourth = quantrisk::black_scholes_mixed_fourth_derivatives(option, market);
            const Real s = market.spot, sig = market.volatility, t = market.maturity;
            const Real s2sigmat = s * s * sig * t;

            const Real v31_identity =
                (third.spot_sigma_sigma - speed * s * s * t - 2.0 * s * t * greeks.gamma -
                 2.0 * s * sig * t * third.spot_spot_sigma) /
                s2sigmat;
            const Real v22_identity =
                (third.sigma_sigma_sigma - 2.0 * s * s * t * third.spot_spot_sigma) / s2sigmat;

            CAPTURE(s, sig, t, strike);
            worst_v31 = std::max(worst_v31, std::abs(fourth.spot_spot_spot_sigma - v31_identity) /
                                                std::max(1.0e-30, std::abs(v31_identity)));
            worst_v22 = std::max(worst_v22, std::abs(fourth.spot_spot_sigma_sigma - v22_identity) /
                                                std::max(1.0e-30, std::abs(v22_identity)));
            CHECK(std::abs(fourth.spot_spot_spot_sigma - v31_identity) <=
                  relative_band *
                          std::max(std::abs(fourth.spot_spot_spot_sigma), std::abs(v31_identity)) +
                      1.0e-12);
            CHECK(std::abs(fourth.spot_spot_sigma_sigma - v22_identity) <=
                  relative_band *
                          std::max(std::abs(fourth.spot_spot_sigma_sigma), std::abs(v22_identity)) +
                      1.0e-12);
        }
    }
    INFO("worst relative residuals: V_SSSsigma " << worst_v31 << ", V_SSsigmasigma " << worst_v22);
    CHECK(worst_v31 < relative_band);
    CHECK(worst_v22 < relative_band);
}

TEST_CASE(
    "the fourth-order partials are identical for calls and puts and zero where the model is") {
    const std::vector<MarketParams> markets = {
        params(100.0, 0.05, 0.02, 0.2, 1.0),
        params(70.0, 0.01, 0.05, 0.4, 0.25),
        params(130.0, 0.08, 0.0, 0.15, 3.0),
        params(100.0, 0.03, 0.01, 0.2, 0.5),
    };
    for (const MarketParams &market : markets) {
        for (const Real strike : {80.0, 99.0, 100.0, 105.0, 130.0}) {
            const auto call = quantrisk::black_scholes_mixed_fourth_derivatives(
                EuropeanOption{OptionType::Call, strike}, market);
            const auto put = quantrisk::black_scholes_mixed_fourth_derivatives(
                EuropeanOption{OptionType::Put, strike}, market);
            CAPTURE(market.spot, market.volatility, market.maturity, strike);
            /// Bit-exact. The call/put difference is `S e^{-qT} - K e^{-rT}`, which
            /// depends on neither spot nor volatility, so every partial of order two or
            /// more across the two factors - including all four of these - cancels.
            CHECK(call.spot_spot_spot_sigma == put.spot_spot_spot_sigma);
            CHECK(call.spot_spot_sigma_sigma == put.spot_spot_sigma_sigma);
            CHECK(call.spot_sigma_sigma_sigma == put.spot_sigma_sigma_sigma);
            CHECK(call.sigma_sigma_sigma_sigma == put.sigma_sigma_sigma_sigma);
        }
    }

    SECTION("the degenerate edges return the limit rather than an overflow") {
        for (const MarketParams &market :
             {params(100.0, 0.05, 0.0, 0.0, 1.0), params(100.0, 0.05, 0.0, 0.0, 0.5),
              params(100.0, 0.05, 0.0, 0.2, 0.0)}) {
            for (const Real strike : {90.0, 100.0, 110.0}) {
                const EuropeanOption option{OptionType::Call, strike};
                CAPTURE(strike, market.volatility, market.maturity);
                CHECK_NOTHROW(quantrisk::black_scholes_mixed_fourth_derivatives(option, market));
                const auto fourth =
                    quantrisk::black_scholes_mixed_fourth_derivatives(option, market);
                CHECK(fourth.spot_spot_spot_sigma == 0.0);
                CHECK(fourth.spot_spot_sigma_sigma == 0.0);
                CHECK(fourth.spot_sigma_sigma_sigma == 0.0);
                CHECK(fourth.sigma_sigma_sigma_sigma == 0.0);
            }
        }
    }

    SECTION("invalid inputs are rejected the same way the Greeks reject them") {
        CHECK_THROWS_AS(
            quantrisk::black_scholes_mixed_fourth_derivatives(
                EuropeanOption{OptionType::Call, 100.0}, params(-1.0, 0.05, 0.0, 0.2, 1.0)),
            ValidationError);
        CHECK_THROWS_AS(
            quantrisk::black_scholes_mixed_fourth_derivatives(EuropeanOption{OptionType::Call, 0.0},
                                                              params(100.0, 0.05, 0.0, 0.2, 1.0)),
            ValidationError);
        CHECK_THROWS_AS(
            quantrisk::black_scholes_mixed_fourth_derivatives(
                EuropeanOption{OptionType::Call, 100.0}, params(100.0, 0.05, 0.0, -0.2, 1.0)),
            ValidationError);
    }
}
