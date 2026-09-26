#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include <algorithm>
#include <cmath>
#include <vector>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/pricing/binomial_crr.hpp"
#include "quantrisk/pricing/black_scholes.hpp"
#include "quantrisk/pricing/instrument.hpp"

using Catch::Approx;
using quantrisk::BinomialResult;
using quantrisk::Count;
using quantrisk::EuropeanOption;
using quantrisk::ExerciseStyle;
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

TEST_CASE("CRR lattice parameters satisfy their defining relations") {
    const MarketParams market = params(100.0, 0.05, 0.02, 0.25, 1.0);
    const BinomialResult tree = quantrisk::crr_binomial(EuropeanOption{OptionType::Call, 100.0},
                                                        market, ExerciseStyle::European, 200);

    CHECK(tree.up * tree.down == Approx(1.0).epsilon(1e-14)); // recombining
    CHECK(tree.up > 1.0);
    CHECK(tree.down < 1.0);
    CHECK(tree.time_step == Approx(market.maturity / 200.0).epsilon(1e-15));
    CHECK(tree.risk_neutral_up_probability > 0.0);
    CHECK(tree.risk_neutral_up_probability < 1.0);

    const Real dt = tree.time_step;
    const Real expected =
        (std::exp((market.rate - market.dividend_yield) * dt) - tree.down) / (tree.up - tree.down);
    CHECK(tree.risk_neutral_up_probability == Approx(expected).epsilon(1e-14));
}

TEST_CASE("European binomial converges to Black-Scholes as steps grow") {
    struct Setting {
        MarketParams market;
        Real strike;
    };
    const std::vector<Setting> settings = {
        {params(100.0, 0.05, 0.0, 0.2, 1.0), 100.0},
        {params(100.0, 0.05, 0.03, 0.35, 0.5), 95.0},
        {params(60.0, 0.01, 0.0, 0.5, 2.0), 80.0},
    };
    const std::vector<quantrisk::Count> steps = {50, 100, 200, 400, 800, 1600, 3200};

    for (const Setting &setting : settings) {
        const EuropeanOption option{OptionType::Call, setting.strike};
        const auto errors =
            quantrisk::crr_convergence_to_black_scholes(option, setting.market, steps);
        const Real reference = quantrisk::black_scholes(option, setting.market).price;
        CAPTURE(setting.strike, setting.market.volatility, reference);
        REQUIRE(errors.size() == steps.size());

        // CRR error is O(1/N) but sawtoothed: whether the strike sits on a node
        // oscillates as N doubles, so the assertion is on the envelope of the
        // errors rather than on each consecutive pair.
        // CRR is first order in dt = T/N, so the residual at N = 3200 scales with
        // the error constant of the regime: sigma*sqrt(T) = 0.71 for the long-dated
        // high-volatility setting leaves ~1e-4 relative, which is why the bound is
        // 1e-3 relative rather than a tighter constant. The *rate* claim is the
        // energy comparison below and the slope fit in
        // experiments/pricing_validation/, not this ceiling.
        CHECK(std::abs(errors.back().second) < 1.0e-3 * std::max(1.0, reference));
        const std::size_t tail = errors.size() - 2;
        Real coarse_energy = 0.0;
        Real fine_energy = 0.0;
        for (std::size_t i = 0; i < 2; ++i) {
            coarse_energy += errors[i].second * errors[i].second;
            fine_energy += errors[tail + i].second * errors[tail + i].second;
        }
        CHECK(fine_energy < 0.25 * coarse_energy); // 16x more steps => >=4x less error
    }
}

TEST_CASE("American call on a non-dividend-paying stock equals the European") {
    // The no-early-exercise theorem is a built-in correctness check for the
    // rollback: with q = 0 the American branch must never bind.
    for (const Real volatility : {0.1, 0.3, 0.6}) {
        const MarketParams market = params(100.0, 0.05, 0.0, volatility, 1.0);
        const EuropeanOption option{OptionType::Call, 100.0};
        const Real european =
            quantrisk::crr_binomial(option, market, ExerciseStyle::European, 500).price;
        const Real american =
            quantrisk::crr_binomial(option, market, ExerciseStyle::American, 500).price;
        CAPTURE(volatility);
        CHECK(american == Approx(european).epsilon(1e-12));
    }
}

TEST_CASE("dividends make the American call worth strictly more") {
    const MarketParams market = params(100.0, 0.05, 0.08, 0.3, 1.0);
    const EuropeanOption option{OptionType::Call, 60.0};
    const Real european =
        quantrisk::crr_binomial(option, market, ExerciseStyle::European, 400).price;
    const Real american =
        quantrisk::crr_binomial(option, market, ExerciseStyle::American, 400).price;
    CHECK(american > european);
}

TEST_CASE("American put dominates the European put and respects bounds") {
    const MarketParams market = params(100.0, 0.05, 0.0, 0.25, 1.0);
    const EuropeanOption option{OptionType::Put, 120.0};
    const Real european =
        quantrisk::crr_binomial(option, market, ExerciseStyle::European, 500).price;
    const Real american =
        quantrisk::crr_binomial(option, market, ExerciseStyle::American, 500).price;
    CHECK(american >= european - 1.0e-12);
    CHECK(american <= 120.0 + 1.0e-9);             // can never be worth more than the strike
    CHECK(american >= option.payoff(market.spot)); // immediate exercise is available
}

TEST_CASE("lattice handles the degenerate edges consistently with the formula") {
    const EuropeanOption option{OptionType::Call, 100.0};

    SECTION("zero volatility matches the deterministic-forward value") {
        const MarketParams flat = params(110.0, 0.05, 0.02, 0.0, 1.0);
        const Real lattice =
            quantrisk::crr_binomial(option, flat, ExerciseStyle::European, 100).price;
        const Real analytic = quantrisk::black_scholes(option, flat).price;
        CHECK(lattice == Approx(analytic).epsilon(1e-12));
        CHECK_THAT(quantrisk::crr_binomial(option, flat, ExerciseStyle::European, 100).note,
                   Catch::Matchers::ContainsSubstring("sigma == 0"));
    }

    SECTION("zero maturity matches the expiry payoff") {
        const MarketParams expired = params(110.0, 0.05, 0.0, 0.2, 0.0);
        CHECK(quantrisk::crr_binomial(option, expired, ExerciseStyle::European, 100).price ==
              Approx(10.0));
        CHECK(quantrisk::crr_binomial(option, expired, ExerciseStyle::American, 100).price ==
              Approx(10.0));
    }

    SECTION("an American put on the zero-volatility forward path exercises early") {
        // K above the forward: immediate exercise beats waiting to expiry.
        const MarketParams flat = params(90.0, 0.05, 0.0, 0.0, 1.0);
        const EuropeanOption deep{OptionType::Put, 100.0};
        const Real european =
            quantrisk::crr_binomial(deep, flat, ExerciseStyle::European, 50).price;
        const Real american =
            quantrisk::crr_binomial(deep, flat, ExerciseStyle::American, 50).price;
        CHECK(american > european);
        CHECK(american == Approx(10.0).epsilon(1e-3)); // exercise now: K - S
    }
}

TEST_CASE("the lattice rejects unusable inputs") {
    const MarketParams market = params(100.0, 0.05, 0.0, 0.2, 1.0);
    const EuropeanOption option{OptionType::Call, 100.0};
    CHECK_THROWS_AS(quantrisk::crr_binomial(option, market, ExerciseStyle::European, 0),
                    ValidationError);
    CHECK_THROWS_AS(quantrisk::crr_binomial(option, market, ExerciseStyle::European, -5),
                    ValidationError);
    CHECK_THROWS_AS(quantrisk::crr_binomial(option, params(-1.0, 0.05, 0.0, 0.2, 1.0),
                                            ExerciseStyle::European, 10),
                    ValidationError);
}

TEST_CASE("coarse lattices flag an invalid risk-neutral measure instead of hiding it") {
    // r - q far above sigma^2 / 2 with one step pushes p outside [0, 1]. The
    // rollback still returns the model value, and the note says so.
    const MarketParams market = params(100.0, 0.60, 0.0, 0.05, 1.0);
    const BinomialResult tree = quantrisk::crr_binomial(EuropeanOption{OptionType::Call, 100.0},
                                                        market, ExerciseStyle::European, 1);
    CAPTURE(tree.risk_neutral_up_probability);
    if (tree.risk_neutral_up_probability < 0.0 || tree.risk_neutral_up_probability > 1.0) {
        CHECK_THAT(tree.note, Catch::Matchers::ContainsSubstring("not a valid probability"));
    } else {
        SUCCEED("measure is valid for these parameters");
    }
    CHECK(std::isfinite(tree.price));
}
