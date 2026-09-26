#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include <cmath>
#include <vector>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/monte_carlo/engine.hpp"
#include "quantrisk/pricing/black_scholes.hpp"
#include "quantrisk/pricing/instrument.hpp"

using Catch::Approx;
using quantrisk::Count;
using quantrisk::EuropeanOption;
using quantrisk::MarketParams;
using quantrisk::MonteCarloEngine;
using quantrisk::MonteCarloResult;
using quantrisk::OptionType;
using quantrisk::Real;
using quantrisk::VarianceReduction;

namespace {

MarketParams params(const Real spot = 100.0, const Real rate = 0.05, const Real dividend = 0.02,
                    const Real volatility = 0.25, const Real maturity = 1.0) {
    return MarketParams{.spot = spot,
                        .rate = rate,
                        .dividend_yield = dividend,
                        .volatility = volatility,
                        .maturity = maturity};
}

} // namespace

TEST_CASE("Monte Carlo converges to the analytic Black-Scholes value") {
    const MarketParams market = params();
    const EuropeanOption option{OptionType::Call, 100.0};
    const Real analytic = black_scholes(option, market).price;

    // Four independent seeds, four standard errors. With a correct estimator the
    // chance that all four fail is negligible, and one failing seed is reported
    // rather than replaced.
    int failures = 0;
    for (const quantrisk::Seed seed : {42ULL, 1337ULL, 2024ULL, 90210ULL}) {
        MonteCarloEngine engine(seed);
        const MonteCarloResult result = engine.price_european(option, market, 200000);
        CAPTURE(seed, result.price, result.standard_error, analytic);
        if (std::abs(result.price - analytic) > 4.0 * result.standard_error) {
            ++failures;
        }
        CHECK(result.measure == "risk_neutral");
        CHECK(result.seed == seed);
        CHECK(result.paths == 200000);
        CHECK(result.iid_units == 200000);
        CHECK(result.runtime_seconds > 0.0);
    }
    CHECK(failures == 0);
    CHECK(std::abs(analytic - 9.0) < 100.0); // guards against a vacuous reference
}

TEST_CASE("the confidence interval is exactly price plus or minus z times SE") {
    const MarketParams market = params();
    const EuropeanOption option{OptionType::Put, 95.0};
    MonteCarloEngine engine(42);
    const MonteCarloResult result =
        engine.price_european(option, market, 50000, VarianceReduction::None, 0.99);
    const Real z = quantrisk::normal_confidence_multiplier(0.99);
    CHECK(z == Approx(2.5758293035489004).epsilon(1.0e-9));
    const Real half_width = 0.5 * (result.confidence_high - result.confidence_low);
    CHECK(half_width == Approx(z * result.standard_error).epsilon(1.0e-12));
    CHECK(result.price ==
          Approx(0.5 * (result.confidence_low + result.confidence_high)).epsilon(1.0e-15));
    CHECK(result.confidence_level == Approx(0.99));
}

TEST_CASE("identical seeds give bit-identical estimates and different seeds do not") {
    const MarketParams market = params();
    const EuropeanOption option{OptionType::Call, 105.0};
    MonteCarloEngine a(4242);
    MonteCarloEngine b(4242);
    const MonteCarloResult first = a.price_european(option, market, 10000);
    const MonteCarloResult second = b.price_european(option, market, 10000);
    CHECK(first.price == second.price);
    CHECK(first.standard_error == second.standard_error);
    CHECK(first.sample_variance == second.sample_variance);

    MonteCarloEngine c(4243);
    CHECK(c.price_european(option, market, 10000).price != first.price);

    // Continuing the same engine must not restart the stream.
    const MonteCarloResult continued = a.price_european(option, market, 10000);
    CHECK(continued.price != first.price);
}

TEST_CASE("antithetic sampling reports pairs as the independent unit") {
    const MarketParams market = params();
    const EuropeanOption option{OptionType::Call, 100.0};
    MonteCarloEngine engine(42);
    const MonteCarloResult result =
        engine.price_european(option, market, 100000, VarianceReduction::Antithetic);
    CHECK(result.paths == 100000);
    CHECK(result.iid_units == 50000);
    CHECK(result.variance_reduction == VarianceReduction::Antithetic);
    CHECK_THAT(result.note, Catch::Matchers::ContainsSubstring("iid_units = paths / 2"));

    MonteCarloEngine odd(42);
    CHECK_THROWS_AS(odd.price_european(option, market, 10001, VarianceReduction::Antithetic),
                    quantrisk::ValidationError);
}

TEST_CASE("antithetic and control variate both cut the standard error") {
    const MarketParams market = params();
    const EuropeanOption option{OptionType::Call, 100.0};

    MonteCarloEngine plain(77);
    const MonteCarloResult plain_result =
        plain.price_european(option, market, 100000, VarianceReduction::None);

    // Per independent unit the antithetic pair mean is less dispersed than a
    // single path, so the reported SE must fall for the same path budget.
    MonteCarloEngine anti(77);
    const MonteCarloResult antithetic =
        anti.price_european(option, market, 100000, VarianceReduction::Antithetic);
    CHECK(antithetic.standard_error < plain_result.standard_error);
    CHECK(std::abs(antithetic.price - plain_result.price) <
          6.0 * std::hypot(antithetic.standard_error, plain_result.standard_error));

    MonteCarloEngine control(77);
    const MonteCarloResult controlled =
        control.price_european(option, market, 100000, VarianceReduction::ControlVariate);
    CHECK(controlled.standard_error < plain_result.standard_error / 2.0);
    CHECK(std::isfinite(controlled.control_beta));
    CHECK(std::abs(controlled.price - plain_result.price) <
          6.0 * std::hypot(controlled.standard_error, plain_result.standard_error));

    const Real analytic = black_scholes(option, market).price;
    CHECK(antithetic.standard_error > 0.0);
    CHECK(std::abs(controlled.price - analytic) < 4.0 * controlled.standard_error);
}

TEST_CASE("the control variate prices a forward exactly") {
    // payoff(S_T) = S_T and control = S_T with known mean S e^{(r-q)T}: the
    // adjusted sample is a constant, so the estimate must be exact to rounding
    // and the standard error must vanish. If this fails, the control variate is
    // wired up wrongly - no statistical tolerance can excuse it.
    const MarketParams market = params();
    const Real expected_terminal =
        market.spot * std::exp((market.rate - market.dividend_yield) * market.maturity);
    MonteCarloEngine engine(42);
    const MonteCarloResult result = engine.price_terminal_payoff(
        [](const Real level) { return level; }, market, 10000, VarianceReduction::ControlVariate);

    CHECK(result.price ==
          Approx(expected_terminal * std::exp(-market.rate * market.maturity)).epsilon(1.0e-12));
    CHECK(result.standard_error < 1.0e-12);
    CHECK(result.control_beta == Approx(1.0).epsilon(1.0e-10));
    CHECK(result.confidence_low == Approx(result.confidence_high).margin(1.0e-12));
}

TEST_CASE("a static payoff reduces to the discounted risk-neutral expectation") {
    const MarketParams market = params();
    MonteCarloEngine engine(42);
    const MonteCarloResult result = engine.price_terminal_payoff(
        [](const Real) { return 2.0; }, market, 1000, VarianceReduction::None);
    CHECK(result.price == Approx(2.0 * std::exp(-market.rate * market.maturity)).epsilon(1.0e-15));
    CHECK(result.standard_error == Approx(0.0).margin(1.0e-18));
}

TEST_CASE("path payoffs see the whole trajectory") {
    const MarketParams market = params(100.0, 0.05, 0.0, 0.3, 2.0);
    constexpr Count kPaths = 200000;
    constexpr Count kSteps = 20;
    MonteCarloEngine engine(42);

    // Payoff 1 if the path ever exceeded a barrier, else 0; compared against the
    // same estimator with more steps, which is the honest check when no closed
    // form is used here.
    const Real barrier = 130.0;
    const MonteCarloResult coarse = engine.price_path_payoff(
        [barrier](const Real *data, const std::size_t length) {
            for (std::size_t i = 0; i < length; ++i) {
                if (data[i] >= barrier) {
                    return 1.0;
                }
            }
            return 0.0;
        },
        market, kPaths, kSteps);
    CHECK(coarse.price > 0.0);
    CHECK(coarse.price < 1.0);
    CHECK(coarse.iid_units == kPaths);
    CHECK_THAT(coarse.note, Catch::Matchers::ContainsSubstring("intervals"));

    // Continuous monitoring is the limit of finer monitoring: refining steps can
    // only raise the probability of touching the barrier.
    MonteCarloEngine finer(42);
    const MonteCarloResult refined = finer.price_path_payoff(
        [barrier](const Real *data, const std::size_t length) {
            for (std::size_t i = 0; i < length; ++i) {
                if (data[i] >= barrier) {
                    return 1.0;
                }
            }
            return 0.0;
        },
        market, kPaths, kSteps * 10);
    CHECK(refined.price >= coarse.price - 3.0 * std::sqrt(coarse.price * (1.0 - coarse.price) /
                                                          static_cast<Real>(kPaths)));
}

TEST_CASE("engine settings are validated before any simulation runs") {
    const MarketParams market = params();
    const EuropeanOption option{OptionType::Call, 100.0};
    MonteCarloEngine engine(42);
    CHECK_THROWS_AS(engine.price_european(option, market, 0), quantrisk::ValidationError);
    CHECK_THROWS_AS(engine.price_european(option, market, -10), quantrisk::ValidationError);
    CHECK_THROWS_AS(engine.price_european(option, market, 1000, VarianceReduction::None, 1.0),
                    quantrisk::ValidationError);
    CHECK_THROWS_AS(engine.price_european(option, params(0.0), 1000), quantrisk::ValidationError);
    CHECK_THROWS_AS(engine.price_european(EuropeanOption{OptionType::Call, -1.0}, market, 1000),
                    quantrisk::ValidationError);
    CHECK_THROWS_AS(engine.price_terminal_payoff(nullptr, market, 100), quantrisk::ValidationError);
    CHECK_THROWS_AS(engine.price_path_payoff(nullptr, market, 100, 10), quantrisk::ValidationError);
    CHECK_THROWS_AS(engine.price_path_payoff([](const Real *, const std::size_t) { return 1.0; },
                                             market, 100, 0),
                    quantrisk::ValidationError);
}

TEST_CASE("variance reduction names round-trip through the bindings helper") {
    CHECK(std::string(quantrisk::to_string(VarianceReduction::None)) == "plain");
    CHECK(std::string(quantrisk::to_string(VarianceReduction::Antithetic)) == "antithetic");
    CHECK(std::string(quantrisk::to_string(VarianceReduction::ControlVariate)) ==
          "control_variate");
}
