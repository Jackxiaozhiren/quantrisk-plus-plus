#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <cmath>
#include <numeric>
#include <vector>

#include "quantrisk/core/rng.hpp"
#include "quantrisk/core/statistics.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/pricing/instrument.hpp"
#include "quantrisk/stochastic/gbm.hpp"

using Catch::Approx;
using quantrisk::Count;
using quantrisk::EuropeanOption;
using quantrisk::MarketParams;
using quantrisk::Rate;
using quantrisk::Real;
using quantrisk::Rng;
using quantrisk::ValidationError;
using quantrisk::gbm::antithetic_paths_matrix;
using quantrisk::gbm::antithetic_terminal_prices;
using quantrisk::gbm::expected_log_return;
using quantrisk::gbm::paths_matrix;
using quantrisk::gbm::terminal_prices;
using quantrisk::gbm::terminal_prices_physical;

namespace {

MarketParams params(const Real spot = 100.0, const Real rate = 0.05, const Real dividend = 0.02,
                    const Real volatility = 0.25, const Real maturity = 1.0) {
    return MarketParams{.spot = spot,
                        .rate = rate,
                        .dividend_yield = dividend,
                        .volatility = volatility,
                        .maturity = maturity};
}

Real sample_mean(const std::vector<Real> &values) { return quantrisk::stats::mean(values); }

Real standard_error(const std::vector<Real> &values) {
    return quantrisk::stats::standard_error_of_mean(values);
}

} // namespace

TEST_CASE("terminal draws reproduce the risk-neutral mean within sampling error") {
    const MarketParams market = params();
    Rng rng(42);
    const std::vector<Real> terminals = terminal_prices(market, 200000, rng);
    REQUIRE(static_cast<Count>(terminals.size()) == 200000);

    const Real expected =
        market.spot * std::exp((market.rate - market.dividend_yield) * market.maturity);
    const Real error = std::abs(sample_mean(terminals) - expected);
    const Real se = standard_error(terminals);
    CAPTURE(error, se, sample_mean(terminals));
    CHECK(error < 5.0 * se);

    for (const Real level : terminals) {
        REQUIRE(std::isfinite(level));
        REQUIRE(level > 0.0);
    }
}

TEST_CASE("log-increments have the drift the exact transition promises") {
    const MarketParams market = params();
    Rng rng(7);
    const std::vector<Real> terminals = terminal_prices(market, 100000, rng);
    std::vector<Real> logs(terminals.size());
    for (std::size_t i = 0; i < terminals.size(); ++i) {
        logs[i] = std::log(terminals[i] / market.spot);
    }
    const Real expected = expected_log_return(market);
    CHECK(sample_mean(logs) == Approx(expected).margin(5.0 * standard_error(logs)));
    // Var[ln(S_T/S_0)] = sigma^2 T.
    CHECK(quantrisk::stats::sample_variance(logs) ==
          Approx(market.volatility * market.volatility * market.maturity).epsilon(0.02));
}

TEST_CASE("the same seed regenerates the identical path set") {
    const MarketParams market = params();
    Rng first(2024);
    Rng second(2024);
    CHECK(terminal_prices(market, 5000, first) == terminal_prices(market, 5000, second));

    Rng third(2024);
    const std::vector<Real> paths = paths_matrix(market, 100, 10, third);
    Rng fourth(2024);
    CHECK(paths == paths_matrix(market, 100, 10, fourth));
}

TEST_CASE("path matrix has the documented shape and starts every row at spot") {
    const MarketParams market = params();
    Rng rng(11);
    constexpr Count kPaths = 37;
    constexpr Count kSteps = 8;
    const std::vector<Real> matrix = paths_matrix(market, kPaths, kSteps, rng);
    REQUIRE(static_cast<Count>(matrix.size()) == kPaths * (kSteps + 1));
    const std::size_t width = static_cast<std::size_t>(kSteps) + 1;
    for (Count p = 0; p < kPaths; ++p) {
        CHECK(matrix[static_cast<std::size_t>(p) * width] == market.spot);
        for (std::size_t k = 0; k < width; ++k) {
            REQUIRE(matrix[static_cast<std::size_t>(p) * width + k] > 0.0);
        }
    }
}

TEST_CASE("refining steps leaves the terminal distribution unbiased") {
    const MarketParams market = params();
    const Real expected =
        market.spot * std::exp((market.rate - market.dividend_yield) * market.maturity);
    for (const Count steps : {1, 5, 50, 500}) {
        Rng rng(99);
        const std::vector<Real> matrix = paths_matrix(market, 20000, steps, rng);
        const std::size_t width = static_cast<std::size_t>(steps) + 1;
        std::vector<Real> terminals(20000);
        for (Count p = 0; p < 20000; ++p) {
            terminals[static_cast<std::size_t>(p)] =
                matrix[static_cast<std::size_t>(p) * width + width - 1];
        }
        CAPTURE(steps, sample_mean(terminals));
        CHECK(std::abs(sample_mean(terminals) - expected) < 5.0 * standard_error(terminals));
    }
}

TEST_CASE("antithetic terminal pairs satisfy the exact product identity") {
    const MarketParams market = params();
    Rng rng(5);
    constexpr Count kPaths = 2000;
    const std::vector<Real> paired = antithetic_terminal_prices(market, kPaths, rng);
    REQUIRE(static_cast<Count>(paired.size()) == kPaths);

    // S+ * S- = S^2 exp(2 (r - q - sigma^2/2) T) for every pair, exactly: the two
    // paths share one Z with opposite signs, so the noise cancels in the product.
    const Real exponent =
        2.0 * (market.rate - market.dividend_yield - 0.5 * market.volatility * market.volatility) *
        market.maturity;
    const Real expected_product = market.spot * market.spot * std::exp(exponent);
    const Count half = kPaths / 2;
    for (Count i = 0; i < half; i += 137) {
        const Real product =
            paired[static_cast<std::size_t>(i)] * paired[static_cast<std::size_t>(i + half)];
        CHECK(product == Approx(expected_product).epsilon(1.0e-12));
    }
}

TEST_CASE("antithetic paths keep the drift and flip only the noise") {
    const MarketParams market = params();
    Rng rng(3);
    const std::vector<Real> matrix = antithetic_paths_matrix(market, 200, 6, rng);
    const std::size_t width = 7;
    const Count half = 100;
    // Pair members must both start at spot and end either side of the drift path.
    for (Count p = 0; p < 10; ++p) {
        CHECK(matrix[static_cast<std::size_t>(p) * width] == market.spot);
        CHECK(matrix[static_cast<std::size_t>(p + half) * width] == market.spot);
        const Real up = matrix[static_cast<std::size_t>(p) * width + width - 1];
        const Real down = matrix[static_cast<std::size_t>(p + half) * width + width - 1];
        const Real product = up * down;
        const Real exponent =
            2.0 *
            (market.rate - market.dividend_yield - 0.5 * market.volatility * market.volatility) *
            market.maturity;
        CHECK(product == Approx(market.spot * market.spot * std::exp(exponent)).epsilon(1.0e-10));
    }
}

TEST_CASE("the physical measure is a separate, explicit code path") {
    const MarketParams market = params();
    const Rate mu = 0.12;
    Rng rng(21);
    const std::vector<Real> physical = terminal_prices_physical(market, mu, 100000, rng);
    // `mu` excludes the dividend yield, so the price drift is (mu - q).
    const Real expected_physical =
        market.spot * std::exp((mu - market.dividend_yield) * market.maturity);
    CHECK(std::abs(sample_mean(physical) - expected_physical) < 5.0 * standard_error(physical));

    // Setting mu = r must coincide with the risk-neutral draws for one seed.
    Rng a(31);
    Rng b(31);
    const std::vector<Real> neutral = terminal_prices(market, 1000, a);
    const std::vector<Real> physical_at_r = terminal_prices_physical(market, market.rate, 1000, b);
    CHECK(neutral == physical_at_r);
}

TEST_CASE("simulation helpers validate their inputs") {
    Rng rng(1);
    CHECK_THROWS_AS(terminal_prices(params(), 0, rng), ValidationError);
    CHECK_THROWS_AS(terminal_prices(params(), -5, rng), ValidationError);
    CHECK_THROWS_AS(paths_matrix(params(), 10, 0, rng), ValidationError);
    CHECK_THROWS_AS(antithetic_terminal_prices(params(), 101, rng), ValidationError);
    CHECK_THROWS_AS(antithetic_paths_matrix(params(), 101, 5, rng), ValidationError);
    CHECK_THROWS_AS(terminal_prices_physical(params(), std::nan(""), 10, rng), ValidationError);
    CHECK_THROWS_AS(terminal_prices(params(0.0), 10, rng), ValidationError);
}
