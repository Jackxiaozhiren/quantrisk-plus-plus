#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

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
