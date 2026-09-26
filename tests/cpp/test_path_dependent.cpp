#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include <cmath>
#include <vector>

#include "quantrisk/core/rng.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/monte_carlo/path_dependent.hpp"
#include "quantrisk/pricing/black_scholes.hpp"
#include "quantrisk/pricing/instrument.hpp"
#include "quantrisk/pricing/path_dependent.hpp"

using Catch::Approx;
using quantrisk::AsianOption;
using quantrisk::AverageType;
using quantrisk::BarrierOption;
using quantrisk::BarrierType;
using quantrisk::Count;
using quantrisk::EuropeanOption;
using quantrisk::MarketParams;
using quantrisk::MonteCarloEngine;
using quantrisk::OptionType;
using quantrisk::Real;
using quantrisk::Rng;
using quantrisk::Time;
using quantrisk::ValidationError;

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

TEST_CASE("the discretely monitored geometric Asian has the documented moments") {
    const MarketParams market = params();
    for (const Count points : {1, 2, 4, 12, 52}) {
        // M = 1 makes the geometric average the terminal price, so the closed form
        // must coincide with Black-Scholes exactly.
        const AsianOption option{OptionType::Call, 100.0, AverageType::Geometric, points};
        const auto price = quantrisk::geometric_asian_price(option, market);
        CAPTURE(points, price.price);
        CHECK(std::isfinite(price.price));
        CHECK(price.price >= 0.0);
        if (points == 1) {
            const auto vanilla =
                quantrisk::black_scholes(EuropeanOption{OptionType::Call, 100.0}, market);
            CHECK(price.price == Approx(vanilla.price).epsilon(1.0e-12));
            CHECK(price.d1 == Approx(vanilla.d1).epsilon(1.0e-10));
        }
    }

    // Continuous-monitoring limit of the variance of ln G is sigma^2 T / 3, so a
    // fine grid must give a geometric Asian worth less than the M = 1 case
    // (more averaging -> less dispersed average -> lower option value OTM/ATM).
    const AsianOption single{OptionType::Call, 105.0, AverageType::Geometric, 1};
    const AsianOption many{OptionType::Call, 105.0, AverageType::Geometric, 520};
    CHECK(quantrisk::geometric_asian_price(many, market).price <
          quantrisk::geometric_asian_price(single, market).price);
}

TEST_CASE("geometric Asian closed form matches its own simulation") {
    const MarketParams market = params();
    const AsianOption option{OptionType::Call, 100.0, AverageType::Geometric, 24};
    const Real reference = quantrisk::geometric_asian_price(option, market).price;
    MonteCarloEngine engine(42);
    const auto result =
        quantrisk::path_dependent::price_geometric_asian(engine, option, market, 200000);
    CAPTURE(result.price, result.standard_error, reference);
    CHECK(std::abs(result.price - reference) < 4.0 * result.standard_error);
    CHECK(result.iid_units == 200000);
}

TEST_CASE("the geometric control variate cuts arithmetic Asian variance") {
    const MarketParams market = params();
    const AsianOption option{OptionType::Call, 100.0, AverageType::Arithmetic, 24};

    MonteCarloEngine plain(42);
    const auto without =
        quantrisk::path_dependent::price_asian(plain, option, market, 60000, false);
    MonteCarloEngine controlled(42);
    const auto with_control =
        quantrisk::path_dependent::price_asian(controlled, option, market, 60000, true);

    CAPTURE(without.standard_error, with_control.standard_error);
    CHECK(with_control.standard_error < without.standard_error / 2.0);
    CHECK(std::isfinite(with_control.control_beta));
    // The same paths underlie both estimators, so the estimates must be close.
    CHECK(std::abs(with_control.price - without.price) <
          6.0 * std::hypot(with_control.standard_error, without.standard_error));
    CHECK_THAT(with_control.note, Catch::Matchers::ContainsSubstring("control variate"));
}

TEST_CASE("arithmetic average never beats the geometric average downward") {
    // For an increasing convex payoff the arithmetic average dominates the
    // geometric one pathwise (AM-GM), so an arithmetic Asian call is always worth
    // at least the geometric Asian call built on the same dates.
    const MarketParams market = params(100.0, 0.05, 0.0, 0.3, 1.0);
    for (const Count points : {2, 12, 52}) {
        const AsianOption geometric{OptionType::Call, 100.0, AverageType::Geometric, points};
        const AsianOption arithmetic{OptionType::Call, 100.0, AverageType::Arithmetic, points};
        MonteCarloEngine engine(7);
        const auto simulated =
            quantrisk::path_dependent::price_asian(engine, arithmetic, market, 40000, true);
        const Real geometric_value = quantrisk::geometric_asian_price(geometric, market).price;
        CAPTURE(points, simulated.price, simulated.standard_error, geometric_value);
        CHECK(simulated.price + 4.0 * simulated.standard_error >= geometric_value);
    }
}

TEST_CASE("pathwise AM-GM ordering holds for the payoff evaluators") {
    const std::vector<Real> path = {100.0, 90.0, 110.0, 95.0, 120.0};
    // A negligible strike exposes the average itself as the payoff; the domain
    // requires K > 0 (docs/mathematical_specification.md §0).
    const Real negligible = 1.0e-9;
    const AsianOption geometric{OptionType::Call, negligible, AverageType::Geometric, 4};
    const AsianOption arithmetic{OptionType::Call, negligible, AverageType::Arithmetic, 4};
    const Real arithmetic_value =
        quantrisk::path_dependent::asian_payoff_from_path(arithmetic, path.data(), path.size());
    const Real geometric_value =
        quantrisk::path_dependent::asian_payoff_from_path(geometric, path.data(), path.size());
    CHECK(arithmetic_value >= geometric_value);
    CHECK(arithmetic_value ==
          Approx((90.0 + 110.0 + 95.0 + 120.0) / 4.0 - negligible).margin(1e-12));
    const Real geometric_average =
        std::exp((std::log(90.0) + std::log(110.0) + std::log(95.0) + std::log(120.0)) / 4.0);
    CHECK(geometric_value == Approx(geometric_average).margin(negligible));
    CHECK(arithmetic_value == Approx((90.0 + 110.0 + 95.0 + 120.0) / 4.0).margin(negligible));
}

TEST_CASE("barrier options respect their degenerate limits") {
    const MarketParams market = params();
    const Real vanilla =
        quantrisk::black_scholes(EuropeanOption{OptionType::Call, 100.0}, market).price;

    SECTION("an unreachable barrier reduces to the vanilla option") {
        const BarrierOption wide{OptionType::Call, 100.0, BarrierType::UpAndOut, 1.0e12, 0.0};
        MonteCarloEngine engine(42);
        const auto result = quantrisk::path_dependent::price_barrier(engine, wide, market, 100000,
                                                                     24, false, false);
        CHECK(result.price == Approx(vanilla).epsilon(4.0 * result.standard_error / vanilla));
    }

    SECTION("a barrier already breached pays only the rebate") {
        const BarrierOption knocked{OptionType::Call, 100.0, BarrierType::UpAndOut, 90.0, 3.0};
        MonteCarloEngine engine(42);
        const auto result = quantrisk::path_dependent::price_barrier(engine, knocked, market, 20000,
                                                                     5, false, false);
        CHECK(result.price ==
              Approx(3.0 * std::exp(-market.rate * market.maturity)).epsilon(1.0e-9));
    }

    SECTION("knock-out can only reduce value relative to the vanilla") {
        const BarrierOption barrier{OptionType::Call, 100.0, BarrierType::UpAndOut, 130.0, 0.0};
        MonteCarloEngine engine(42);
        const auto result = quantrisk::path_dependent::price_barrier(engine, barrier, market,
                                                                     100000, 24, false, false);
        CHECK(result.price <= vanilla);
    }
}

TEST_CASE("discrete monitoring becomes more expensive as dates are refined") {
    // More monitoring dates make knockout more likely, so a knock-out option must
    // get cheaper; the continuous-monitoring price is the limit from above.
    const MarketParams market = params(100.0, 0.05, 0.0, 0.3, 1.0);
    const BarrierOption barrier{OptionType::Call, 100.0, BarrierType::UpAndOut, 125.0, 0.0};
    Real previous = 1.0e30;
    for (const Count steps : {5, 20, 80, 320}) {
        MonteCarloEngine engine(11);
        const auto result = quantrisk::path_dependent::price_barrier(engine, barrier, market,
                                                                     120000, steps, false, false);
        CAPTURE(steps, result.price, previous);
        CHECK(result.price <= previous + 3.0 * result.standard_error);
        previous = result.price;
    }
}

TEST_CASE("the continuity correction widens the barrier in the right direction") {
    const MarketParams market = params();
    const Real beta = quantrisk::barrier_continuity_constant();
    CHECK(beta == Approx(0.5826).epsilon(1.0e-3));

    const BarrierOption up{OptionType::Call, 100.0, BarrierType::UpAndOut, 130.0, 0.0};
    const BarrierOption down{OptionType::Call, 100.0, BarrierType::DownAndOut, 70.0, 0.0};
    const Time dt = 1.0 / 50.0;
    // Closer to the spot than the contractual barrier, in both directions.
    CHECK(quantrisk::continuity_corrected_barrier(up, market, dt) < 130.0);
    CHECK(quantrisk::continuity_corrected_barrier(down, market, dt) > 70.0);

    // A tighter barrier must knock out more often, so the corrected estimate is
    // strictly cheaper than the raw discrete one and closer to continuous
    // monitoring (checked quantitatively against AnalyticBarrierEngine in
    // benchmarks/quantlib/path_dependent_validation.py).
    MonteCarloEngine plain(5);
    const auto discrete =
        quantrisk::path_dependent::price_barrier(plain, up, market, 60000, 50, false, false);
    MonteCarloEngine corrected(5);
    const auto approximated =
        quantrisk::path_dependent::price_barrier(corrected, up, market, 60000, 50, true, false);
    CHECK(approximated.price < discrete.price);
    CHECK_THAT(approximated.note, Catch::Matchers::ContainsSubstring("approximation"));
}

TEST_CASE("down-and-out puts behave symmetrically") {
    const MarketParams market = params(100.0, 0.05, 0.0, 0.3, 1.0);
    const BarrierOption down{OptionType::Put, 100.0, BarrierType::DownAndOut, 80.0, 1.0};
    MonteCarloEngine engine(99);
    const auto result =
        quantrisk::path_dependent::price_barrier(engine, down, market, 100000, 50, false, true);
    CHECK(result.price > 0.0);
    CHECK(result.iid_units == 50000);
    CHECK(result.standard_error > 0.0);
}

TEST_CASE("path-dependent instruments validate their inputs") {
    const MarketParams market = params();
    Rng rng(1);
    MonteCarloEngine engine(1);

    const AsianOption bad_strike{OptionType::Call, -1.0, AverageType::Arithmetic, 12};
    const AsianOption no_points{OptionType::Call, 100.0, AverageType::Arithmetic, 0};
    const AsianOption ok_asian{OptionType::Call, 100.0, AverageType::Arithmetic, 12};
    const BarrierOption bad_barrier_level{OptionType::Call, 100.0, BarrierType::UpAndOut, 0.0, 0.0};
    const BarrierOption ok_barrier{OptionType::Call, 100.0, BarrierType::UpAndOut, 120.0, 0.0};

    CHECK_THROWS_AS(bad_strike.validate(), ValidationError);
    CHECK_THROWS_AS(no_points.validate(), ValidationError);
    CHECK_THROWS_AS(bad_barrier_level.validate(), ValidationError);
    CHECK_THROWS_AS(quantrisk::geometric_asian_price(ok_asian, params(0.0)), ValidationError);
    CHECK_THROWS_AS(quantrisk::path_dependent::price_asian(engine, ok_asian, market, 0, false),
                    ValidationError);
    CHECK_THROWS_AS(quantrisk::path_dependent::price_barrier(engine, ok_barrier, market, 100, 0),
                    ValidationError);
    CHECK_NOTHROW(rng.standard_normal());
}
