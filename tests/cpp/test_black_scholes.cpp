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
