#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include <cmath>
#include <limits>
#include <vector>

#include "quantrisk/core/rng.hpp"
#include "quantrisk/core/statistics.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/pricing/black_scholes.hpp"
#include "quantrisk/pricing/instrument.hpp"
#include "quantrisk/stochastic/heston.hpp"

using Catch::Approx;
using quantrisk::Count;
using quantrisk::EuropeanOption;
using quantrisk::HestonParams;
using quantrisk::MarketParams;
using quantrisk::OptionType;
using quantrisk::Real;
using quantrisk::Rng;
using quantrisk::ValidationError;

namespace {

HestonParams heston(const Real initial_variance = 0.0625, const Real kappa = 2.0,
                    const Real theta = 0.0625, const Real xi = 0.4, const Real rho = -0.7,
                    const Real maturity = 1.0) {
    HestonParams parameters;
    parameters.spot = 100.0;
    parameters.rate = 0.05;
    parameters.dividend_yield = 0.02;
    parameters.initial_variance = initial_variance;
    parameters.kappa = kappa;
    parameters.theta = theta;
    parameters.xi = xi;
    parameters.rho = rho;
    parameters.maturity = maturity;
    return parameters;
}

const EuropeanOption &atm_call() {
    static const EuropeanOption option{OptionType::Call, 100.0};
    return option;
}

} // namespace

TEST_CASE("Heston collapses to Black-Scholes when the variance is deterministic") {
    // xi == 0 and v0 == sigma^2 make the model exactly GBM, so the simulated
    // price must agree with the analytic Black-Scholes value to within sampling
    // error. This is the strongest oracle available for the scheme and it is
    // parameter-free.
    const Real sigma = 0.25;
    const HestonParams parameters = heston(sigma * sigma, 1.0, sigma * sigma, 0.0, 0.0);
    const MarketParams market{.spot = parameters.spot,
                              .rate = parameters.rate,
                              .dividend_yield = parameters.dividend_yield,
                              .volatility = sigma,
                              .maturity = parameters.maturity};
    const Real reference = quantrisk::black_scholes(atm_call(), market).price;

    for (const Real kappa : {0.5, 5.0, 50.0}) {
        HestonParams frozen = parameters;
        frozen.kappa = kappa;
        Rng rng(42);
        const auto result = quantrisk::price_heston_european(frozen, atm_call(), 200000, 50, rng);
        CAPTURE(kappa, result.price, result.standard_error, reference);
        CHECK(std::abs(result.price - reference) < 4.0 * result.standard_error);
        CHECK(result.feller_condition_satisfied);
    }
}

TEST_CASE("paths stay positive and the variance stays non-negative") {
    // A deliberately Feller-violating parameter set: 2 kappa theta < xi^2, so the
    // exact CIR process would touch zero. Full truncation must still never return
    // a negative variance or a non-positive price level.
    const HestonParams parameters = heston(0.01, 2.0, 0.04, 0.9, -0.8);
    REQUIRE_FALSE(parameters.feller_condition_satisfied());
    Rng rng(7);
    const auto simulation = quantrisk::simulate_heston(parameters, 20000, 100, rng);
    CHECK(simulation.negative_variances_clamped > 0); // the regime really is hit
    for (const Real level : simulation.terminals) {
        REQUIRE(std::isfinite(level));
        REQUIRE(level > 0.0);
    }
    for (const Real variance : simulation.terminal_variance) {
        REQUIRE(variance >= 0.0);
    }
    for (const Real integrated : simulation.realised_variance) {
        REQUIRE(integrated >= 0.0);
    }
    CHECK_THAT(simulation.note, Catch::Matchers::ContainsSubstring("full-truncation"));
}

TEST_CASE("the discounted terminal expectation keeps the risk-neutral drift") {
    const HestonParams parameters = heston();
    Rng rng(21);
    const auto simulation = quantrisk::simulate_heston(parameters, 200000, 64, rng);
    const Real expected = parameters.spot * std::exp((parameters.rate - parameters.dividend_yield) *
                                                     parameters.maturity);
    const Real mean = quantrisk::stats::mean(simulation.terminals);
    const Real se = quantrisk::stats::standard_error_of_mean(simulation.terminals);
    CAPTURE(mean, se, expected);
    CHECK(std::abs(mean - expected) < 4.0 * se);
}

TEST_CASE("estimates are reproducible and seed-dependent") {
    const HestonParams parameters = heston();
    Rng first(1234);
    Rng second(1234);
    const auto a = quantrisk::price_heston_european(parameters, atm_call(), 20000, 20, first);
    const auto b = quantrisk::price_heston_european(parameters, atm_call(), 20000, 20, second);
    CHECK(a.price == b.price);
    CHECK(a.standard_error == b.standard_error);
    CHECK(a.mean_terminal_variance == b.mean_terminal_variance);

    Rng third(1235);
    CHECK(quantrisk::price_heston_european(parameters, atm_call(), 20000, 20, third).price !=
          a.price);
    CHECK(a.seed == 1234);
    CHECK(a.paths == 20000);
    CHECK(a.steps == 20);
    CHECK(a.runtime_seconds > 0.0);
}

TEST_CASE("step refinement: the truncation bias stays inside the noise band") {
    /// Full-truncation Euler is biased, so this must be *measured*, not asserted
    /// away. Different step counts consume different numbers of normals, so the
    /// two estimates are effectively independent draws and their difference has
    /// standard error sqrt(SE1^2 + SE2^2). The claim supported here is therefore
    /// "no bias detectable at four combined standard errors", and the
    /// path-dependent experiment reports the observed differences at larger
    /// sample sizes rather than hiding them.
    const HestonParams parameters = heston(0.09, 1.5, 0.09, 0.6, -0.5);
    struct Sample {
        Count steps;
        Real price;
        Real se;
    };
    std::vector<Sample> samples;
    for (const Count steps : {20, 80, 320}) {
        Rng rng(3);
        const auto result =
            quantrisk::price_heston_european(parameters, atm_call(), 150000, steps, rng);
        samples.push_back(Sample{steps, result.price, result.standard_error});
    }
    const Sample &finest = samples.back();
    for (const Sample &sample : samples) {
        const Real combined = std::hypot(sample.se, finest.se);
        CAPTURE(sample.steps, sample.price, finest.price, sample.se, combined);
        CHECK(std::abs(sample.price - finest.price) < 4.0 * combined);
    }
    CHECK(finest.price > 0.0);
}

TEST_CASE("negative skew: rho drives the implied smile direction") {
    // With rho < 0 the model produces fat left tails; an out-of-the-money put is
    // worth more than with rho > 0 at otherwise identical parameters.
    const HestonParams short_sellers = heston(0.0625, 2.0, 0.0625, 0.5, -0.9);
    const HestonParams buyers = heston(0.0625, 2.0, 0.0625, 0.5, 0.9);
    const EuropeanOption put{OptionType::Put, 90.0};
    Rng a(5);
    Rng b(5);
    const Real low = quantrisk::price_heston_european(short_sellers, put, 200000, 64, a).price;
    const Real high = quantrisk::price_heston_european(buyers, put, 200000, 64, b).price;
    CAPTURE(low, high);
    CHECK(low > high);
}

TEST_CASE("Heston parameters are validated structurally, Feller is only reported") {
    Rng rng(1);
    HestonParams bad = heston();
    bad.rho = 1.5;
    CHECK_THROWS_AS(bad.validate(), ValidationError);
    bad = heston();
    bad.theta = -0.1;
    CHECK_THROWS_AS(bad.validate(), ValidationError);
    bad = heston();
    bad.xi = std::numeric_limits<Real>::quiet_NaN();
    CHECK_THROWS_AS(bad.validate(), ValidationError);
    bad = heston();
    bad.spot = 0.0;
    CHECK_THROWS_AS(quantrisk::simulate_heston(bad, 10, 10, rng), ValidationError);

    // Feller violation is legal input, reported through the result.
    const HestonParams violating = heston(0.01, 1.0, 0.01, 1.0, 0.0);
    CHECK_FALSE(violating.feller_condition_satisfied());
    CHECK_NOTHROW(quantrisk::simulate_heston(violating, 100, 5, rng));
}

TEST_CASE("zero maturity returns the payoff at the spot") {
    const HestonParams parameters = heston(0.0625, 2.0, 0.0625, 0.4, -0.5, 0.0);
    Rng rng(3);
    const auto simulation = quantrisk::simulate_heston(parameters, 500, 10, rng);
    CHECK(simulation.terminals.size() == 500);
    for (const Real level : simulation.terminals) {
        CHECK(level == parameters.spot);
    }
    CHECK_THAT(simulation.note, Catch::Matchers::ContainsSubstring("T == 0"));
}
