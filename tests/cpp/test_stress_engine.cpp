#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include <cmath>
#include <string>
#include <vector>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/portfolio/covariance.hpp"
#include "quantrisk/pricing/black_scholes.hpp"
#include "quantrisk/risk/measures.hpp"
#include "quantrisk/stress/engine.hpp"

using namespace quantrisk;
using namespace quantrisk::stress;
using Catch::Approx;

namespace {

/// A four-factor universe: two equities, one rate, one volatility, one credit spread.
/// Levels are chosen so the relative/absolute conversions are exact in binary where
/// possible, because a conversion that lands on 0.19999999999 makes the attribution
/// residual test measure rounding instead of logic.
FactorSet four_factors() {
    return FactorSet{{
        {"SPX", FactorClass::equity_index, 4000.0, "index points"},
        {"NDX", FactorClass::equity_index, 16000.0, "index points"},
        {"UST10Y", FactorClass::rate, 0.04, "decimal p.a."},
        {"VOL", FactorClass::volatility, 0.20, "annualised vol"},
    }};
}

/// Build an exposure block aligned to the four-factor universe.
///
/// A short block is genuinely ambiguous — `{1e6, 2e6}` could mean factors 0-1 or 2-3 —
/// so the engine requires full length and the helper supplies it, padding with zeros.
/// An *empty* block still means "this position carries no sensitivity of that type at
/// all", which is a different statement from "it carries zeros".
ExposureVector block(std::vector<Real> delta, std::vector<Real> gamma = {},
                     std::vector<Real> duration = {}, std::vector<Real> vega = {},
                     std::vector<Real> credit = {}) {
    auto align = [](std::vector<Real> &block_) {
        if (!block_.empty()) {
            block_.resize(4, 0.0);
        }
    };
    align(delta);
    align(gamma);
    align(duration);
    align(vega);
    align(credit);
    return ExposureVector{std::move(delta), std::move(gamma), std::move(duration), std::move(vega),
                          std::move(credit)};
}

Scenario equity_crash() {
    Scenario scenario;
    scenario.name = "equity -20%";
    scenario.kind = ScenarioKind::deterministic;
    scenario.assumptions = "one-day parallel fall in both equity factors, no vol response";
    scenario.horizon = 1.0 / 252.0;
    scenario.shocks = {{"SPX", -0.20, 0.0}, {"NDX", -0.20, 0.0}};
    return scenario;
}

} // namespace

TEST_CASE("factor class and scenario kind print what they are") {
    CHECK(std::string(to_string(FactorClass::equity_index)) == "equity_index");
    CHECK(std::string(to_string(FactorClass::credit_spread)) == "credit_spread");
    CHECK(std::string(to_string(ScenarioKind::monte_carlo)) == "monte_carlo");
}

TEST_CASE("an unknown factor id is refused rather than ignored") {
    const FactorSet factors = four_factors();
    CHECK(factors.index_of("UST10Y") == 2);
    CHECK_THROWS_AS(factors.index_of("VIX"), ValidationError);
}

TEST_CASE("exposure vectors must line up with the factor set") {
    const FactorSet factors = four_factors();
    Portfolio portfolio;
    portfolio.factors = factors;
    // Built directly rather than through block(), which aligns for the other tests.
    portfolio.positions = {{"short book", ExposureVector{{1.0e6, 2.0e6}, {}, {}, {}, {}}}};
    CHECK_THROWS_AS(portfolio.aggregate(), ValidationError);

    portfolio.positions = {
        {"long", ExposureVector{{1.0, 2.0, 3.0, 4.0, 5.0, 6.0}, {}, {}, {}, {}}}};
    CHECK_THROWS_AS(portfolio.aggregate(), ValidationError);

    portfolio.positions = {
        {"ragged", ExposureVector{{1.0, 2.0, 3.0, 4.0}, {1.0, 2.0}, {}, {}, {}}}};
    CHECK_THROWS_AS(portfolio.aggregate(), ValidationError);

    portfolio.positions = {{"nan", ExposureVector{{1.0, std::nan(""), 0.0, 0.0}, {}, {}, {}, {}}}};
    CHECK_THROWS_AS(portfolio.aggregate(), ValidationError);

    portfolio.positions = {};
    CHECK_THROWS_AS(portfolio.aggregate(), ValidationError);
}

TEST_CASE("aggregation is a plain per-factor sum and keeps empty blocks empty") {
    const FactorSet factors = four_factors();
    Portfolio portfolio;
    portfolio.factors = factors;
    portfolio.positions = {
        {"a", block({1.0e6, 2.0e6, 0.0, 0.0}, {}, {0.0, 0.0, -5.0e5, 0.0})},
        {"b", block({-1.0e6, 1.0e6})}, // no duration block at all
    };
    const ExposureVector total = portfolio.aggregate();
    REQUIRE(total.duration.size() == 4);
    CHECK(total.delta[0] == 0.0);
    CHECK(total.delta[1] == 3.0e6);
    CHECK(total.duration[2] == -5.0e5);
    // The gamma block was empty on both positions, so it stays absent rather than
    // becoming a vector of zeros that a caller might read as "measured to be zero".
    CHECK(total.gamma.empty());
}

TEST_CASE("a relative equity shock maps to P&L through delta, exactly") {
    const FactorSet factors = four_factors();
    Portfolio portfolio;
    portfolio.factors = factors;
    // 1e6 currency of delta per 100 % SPX move, 2e6 per 100 % NDX move.
    portfolio.positions = {{"long equities", block({1.0e6, 2.0e6})}};

    const ScenarioResult result = run_scenario(portfolio, equity_crash());
    CHECK(result.pnl_change == Approx(-0.20 * 3.0e6).epsilon(1.0e-12));
    CHECK(result.by_factor.size() == 4);
    CHECK(result.by_factor[0].linear == Approx(-0.2e6).epsilon(1.0e-12));
    CHECK(result.by_factor[2].relative_move == 0.0);
    CHECK(result.factor_attribution_residual == Approx(0.0).margin(1.0e-9));
    CHECK(result.position_attribution_residual == Approx(0.0).margin(1.0e-9));
    CHECK_FALSE(result.has_risk_metrics);
    CHECK_THAT(result.note, Catch::Matchers::ContainsSubstring("no factor-move covariance"));
}

TEST_CASE("an absolute rate shock does not depend on the quoted level") {
    const FactorSet factors = four_factors();
    Portfolio portfolio;
    portfolio.factors = factors;
    portfolio.positions = {{"bonds", block({}, {}, {0.0, 0.0, -2.0e7, 0.0})}};

    Scenario hot;
    hot.name = "rates +200bp";
    hot.assumptions = "parallel 200bp rise, one-day";
    hot.shocks = {{"UST10Y", 0.0, 0.02}};
    const ScenarioResult result = run_scenario(portfolio, hot);

    // DV01-style: -2.0e7 currency per unit yield, times 0.02 = -400k, whatever the
    // 4 % or 6 % starting level was. The relative move is still reported for reading.
    CHECK(result.pnl_change == Approx(-400000.0).epsilon(1.0e-12));
    CHECK(result.by_factor[2].absolute_move == Approx(0.02).epsilon(1.0e-12));
    CHECK(result.by_factor[2].relative_move == Approx(0.5).epsilon(1.0e-12)); // 2%/4%
    CHECK(result.by_factor[2].rate == Approx(-400000.0).epsilon(1.0e-12));
    CHECK(result.by_factor[2].linear == 0.0); // no delta on a rate factor
}

TEST_CASE("convexity is quoted against the relative move squared") {
    const FactorSet factors = four_factors();
    Portfolio portfolio;
    portfolio.factors = factors;
    // gamma already carries the 1/2 by the header's convention.
    portfolio.positions = {{"convex", block({1.0e6, 0.0}, {2.0e6, 0.0})}};

    const ScenarioResult down = run_scenario(portfolio, equity_crash());
    CHECK(down.by_factor[0].linear == Approx(-200000.0).epsilon(1.0e-12));
    CHECK(down.by_factor[0].convexity == Approx(2.0e6 * 0.04).epsilon(1.0e-12));
    // A long-gamma book loses less on the way down than a delta-only book, and the same
    // amount of convexity is gained on the way up: the term is even in the move.
    Scenario up = equity_crash();
    up.shocks = {{"SPX", 0.20, 0.0}, {"NDX", 0.20, 0.0}};
    const ScenarioResult risen = run_scenario(portfolio, up);
    CHECK(risen.by_factor[0].convexity == Approx(down.by_factor[0].convexity).epsilon(1.0e-12));
    // The convexity term is even in the move, so it cancels in the up-minus-down
    // difference and what is left is exactly twice the delta leg: 2 * 1e6 * 0.2.
    CHECK(risen.pnl_change - down.pnl_change == Approx(400000.0).epsilon(1.0e-10));
}

TEST_CASE("a multi-class scenario attributes exactly two ways") {
    const FactorSet factors = four_factors();
    Portfolio portfolio;
    portfolio.factors = factors;
    portfolio.positions = {
        {"equity desk", block({1.0e6, 2.0e6}, {5.0e5, 5.0e5})},
        {"rates desk", block({}, {}, {0.0, 0.0, -2.0e7, 0.0})},
        {"vol book", block({}, {}, {}, {-1.0e5, 0.0, 0.0, 0.0})},
    };
    // NOTE: vega is indexed by factor, so the vol book's vega sits on the VOL factor.
    portfolio.positions[2] = Position{"vol book", block({}, {}, {}, {0.0, 0.0, 0.0, -1.0e5})};

    Scenario mixed;
    mixed.name = "risk-off";
    mixed.assumptions = "equities -20%, rates -100bp, vol +8 vol points, one day";
    mixed.shocks = {
        {"SPX", -0.20, 0.0},
        {"NDX", -0.20, 0.0},
        {"UST10Y", 0.0, -0.01},
        {"VOL", 0.0, 0.08},
    };
    const ScenarioResult result = run_scenario(portfolio, mixed);

    // Read straight off the scenario: delta on both equities, gamma on both, a rate
    // rally of 100bp against a negative duration, and 8 vol points against short vega.
    const Real expected = -0.20 * 3.0e6 + 0.20 * 0.20 * 1.0e6 + 0.01 * 2.0e7 - 0.08 * 1.0e5;
    CHECK(result.pnl_change == Approx(expected).epsilon(1.0e-12));
    CHECK(result.factor_attribution_residual == Approx(0.0).margin(1.0e-9));
    CHECK(result.position_attribution_residual == Approx(0.0).margin(1.0e-9));

    Real by_class = 0.0;
    for (const FactorContribution &part : result.by_factor) {
        by_class += part.total();
    }
    CHECK(by_class == Approx(result.pnl_change).epsilon(1.0e-12));
}

TEST_CASE("no shocks is a zero result, not an empty one") {
    const FactorSet factors = four_factors();
    Portfolio portfolio;
    portfolio.factors = factors;
    portfolio.positions = {{"book", block({1.0e6, 2.0e6})}};
    Scenario none;
    none.name = "base";
    none.assumptions = "no factor moves";
    const ScenarioResult result = run_scenario(portfolio, none);
    CHECK(result.pnl_change == 0.0);
    CHECK(result.by_factor.size() == 4);
    CHECK(result.factor_attribution_residual == 0.0);
    CHECK(result.position_attribution_residual == 0.0);
}

TEST_CASE("contradictory or unconvertible shocks are refused") {
    const FactorSet factors = four_factors();
    Portfolio portfolio;
    portfolio.factors = factors;
    portfolio.positions = {{"book", block({1.0e6, 2.0e6})}};

    Scenario both;
    both.name = "inconsistent";
    both.assumptions = "states -20% and -400 points on a 4000 index, which is -10%";
    both.shocks = {{"SPX", -0.20, -400.0}};
    CHECK_THROWS_AS(run_scenario(portfolio, both), ValidationError);

    FactorSet zeroed = four_factors();
    zeroed.factors[0].level = 0.0;
    Portfolio broken;
    broken.factors = zeroed;
    broken.positions = {{"book", block({1.0e6, 2.0e6})}};
    CHECK_THROWS_AS(run_scenario(broken, equity_crash()), ValidationError);
}

TEST_CASE("a scenario with no stated assumptions says so in the note") {
    const FactorSet factors = four_factors();
    Portfolio portfolio;
    portfolio.factors = factors;
    portfolio.positions = {{"book", block({1.0e6, 2.0e6})}};
    Scenario bare = equity_crash();
    bare.assumptions.clear();
    bare.horizon = 0.0;
    const ScenarioResult result = run_scenario(portfolio, bare);
    CHECK_THAT(result.note, Catch::Matchers::ContainsSubstring("no stated assumptions"));
    CHECK_THAT(result.note, Catch::Matchers::ContainsSubstring("no horizon is set"));
}

// --- distribution shifts --------------------------------------------------

TEST_CASE("a volatility multiplier scales every standard deviation") {
    const std::vector<Real> covariance = {0.04, 0.012, 0.012, 0.09};
    std::string note;
    DistributionShift shift;
    shift.volatility_multiplier = 2.0;
    const auto stressed = shift_covariance(covariance, 2, shift, note);

    CHECK(stressed[0] == Approx(0.16).epsilon(1.0e-12));
    CHECK(stressed[3] == Approx(0.36).epsilon(1.0e-12));
    // Covariance scales by the product of the two sigmas, so 4x not 2x.
    CHECK(stressed[1] == Approx(0.048).epsilon(1.0e-12));
    CHECK_THAT(note, Catch::Matchers::ContainsSubstring("scaled by 2"));
}

TEST_CASE("a correlation lift raises a long-only portfolio's risk and reports clipping") {
    const std::vector<Real> covariance = {0.04, 0.012, 0.012, 0.09};
    std::string note;
    DistributionShift shift;
    shift.correlation_increment = 0.2;
    const auto stressed = shift_covariance(covariance, 2, shift, note);
    const Real base_corr = 0.012 / (0.2 * 0.3);
    const Real moved = stressed[1] / (0.2 * 0.3);
    CHECK(moved == Approx(base_corr + 0.2).epsilon(1.0e-12));
    CHECK_THAT(note, Catch::Matchers::ContainsSubstring("no clipping needed"));

    // Push it past 1 and the clip must be visible in the note, not silent.
    std::string clipped_note;
    DistributionShift extreme;
    extreme.correlation_increment = 0.9;
    const auto clipped = shift_covariance(covariance, 2, extreme, clipped_note);
    CHECK(clipped[1] / (0.2 * 0.3) == Approx(1.0).epsilon(1.0e-12));
    CHECK_THAT(clipped_note, Catch::Matchers::ContainsSubstring("clipped"));
}

TEST_CASE("a dependence structure that cannot exist is announced, not repaired") {
    // Four uncorrelated assets, lift every pair to correlation 1 minus epsilon: the
    // result is rank-deficient at best and indefinite at worst.
    std::vector<Real> covariance(16, 0.0);
    for (std::size_t i = 0; i < 4; ++i) {
        covariance[i * 4 + i] = 0.04;
    }
    std::string note;
    DistributionShift shift;
    shift.correlation_increment = 0.9;
    const auto stressed = shift_covariance(covariance, 4, shift, note);
    const auto spectrum = quantrisk::portfolio::eigenvalues(stressed, 4);
    if (spectrum.front() < -1.0e-12) {
        CHECK_THAT(note, Catch::Matchers::ContainsSubstring("NOT positive semidefinite"));
    } else {
        // Correlation 0.9 on every pair is still PSD, so the honest outcome is no warning.
        CHECK_FALSE(note.find("clipped") != std::string::npos);
    }
}

TEST_CASE("a negative covariance diagonal is refused outright") {
    const std::vector<Real> covariance = {-0.04, 0.0, 0.0, 0.09};
    std::string note;
    DistributionShift shift;
    shift.volatility_multiplier = 2.0;
    CHECK_THROWS_AS(shift_covariance(covariance, 2, shift, note), ValidationError);
}

// --- risk metrics ---------------------------------------------------------

namespace {

/// Diagonal factor-move covariance for the four-factor universe, in the units each
/// factor's exposures are quoted against: relative moves for equities, absolute for the
/// rate and the vol factor.
std::vector<Real> factor_move_covariance() {
    std::vector<Real> covariance(16, 0.0);
    covariance[0 * 4 + 0] = 0.01; // SPX relative move, sd 10 %
    covariance[1 * 4 + 1] = 0.015 * 0.015;
    covariance[2 * 4 + 2] = 0.002 * 0.002; // 20 bp absolute
    covariance[3 * 4 + 3] = 0.05 * 0.05;   // 5 vol points absolute
    covariance[0 * 4 + 1] = covariance[1 * 4 + 0] = 0.5 * 0.1 * 0.015;
    return covariance;
}

} // namespace

TEST_CASE("the stressed VaR is the same Gaussian closed form the risk layer uses") {
    const FactorSet factors = four_factors();
    Portfolio portfolio;
    portfolio.factors = factors;
    portfolio.positions = {{"book", block({1.0e6, 2.0e6})}};
    const std::vector<Real> covariance = factor_move_covariance();

    Scenario none;
    none.name = "base";
    none.assumptions = "no moves";
    const ScenarioResult result = run_scenario(portfolio, none, covariance, 0.95);
    REQUIRE(result.has_risk_metrics);

    // Independent route: hand risk::gaussian_var a sample built to have this exact mean
    // and standard deviation, and compare what it reports. The scaling is computed from
    // the sample rather than hardcoded, so the check tests the formula and not a
    // constant that happened to be close.
    std::vector<Real> unit(2000);
    Real sum_of_squares = 0.0;
    for (std::size_t i = 0; i < unit.size(); ++i) {
        unit[i] = static_cast<Real>(i) - 999.5; // symmetric, so the mean is exactly 0
        sum_of_squares += unit[i] * unit[i];
    }
    const Real unit_sd = std::sqrt(sum_of_squares / static_cast<Real>(unit.size() - 1));
    for (Real &value : unit) {
        value = value / unit_sd * result.base_volatility;
    }
    const risk::RiskEstimate cross_check = risk::gaussian_var(unit, 0.95);
    CHECK(result.base_var == Approx(cross_check.value).epsilon(1.0e-6));
    CHECK(result.base_var > 0.0);
    CHECK(result.var_change == Approx(0.0).margin(1.0e-9));
    CHECK(result.var_decomposition_residual == Approx(0.0).margin(1.0e-9));
}

TEST_CASE("a crash moves the VaR through both the mean and the dispersion") {
    const FactorSet factors = four_factors();
    Portfolio portfolio;
    portfolio.factors = factors;
    portfolio.positions = {{"book", block({1.0e6, 2.0e6})}};
    const std::vector<Real> covariance = factor_move_covariance();

    ScenarioResult result = run_scenario(portfolio, equity_crash(), covariance, 0.95);
    REQUIRE(result.has_risk_metrics);
    // The level leg: a loss already taken raises the loss distribution's mean.
    CHECK(result.var_change_from_level > 0.0);
    CHECK(result.var_change_from_level == Approx(-result.pnl_change).epsilon(1.0e-9));
    CHECK(result.var_decomposition_residual == Approx(0.0).margin(1.0e-9));
    CHECK(result.es_change > 0.0);
    CHECK(result.stressed_es > result.stressed_var);

    // Now deform the distribution with no level move at all, and the split must be pure.
    Scenario vol_only;
    vol_only.name = "vol doubling";
    vol_only.assumptions = "no factor moves, dispersion doubled";
    vol_only.distribution.volatility_multiplier = 2.0;
    result = run_scenario(portfolio, vol_only, covariance, 0.95);
    CHECK(result.pnl_change == 0.0);
    CHECK(result.var_change_from_level == Approx(0.0).margin(1.0e-12));
    CHECK(result.var_change_from_distribution > 0.0);
    CHECK(result.var_change == Approx(result.var_change_from_distribution).epsilon(1.0e-9));
    // Doubling every sigma doubles a zero-mean Gaussian VaR exactly.
    Scenario none;
    none.name = "base";
    none.assumptions = "no moves";
    const ScenarioResult baseline = run_scenario(portfolio, none, covariance, 0.95);
    CHECK(result.stressed_var == Approx(2.0 * baseline.base_var).epsilon(1.0e-9));
}

TEST_CASE("Euler VaR components sum to the stressed VaR") {
    const FactorSet factors = four_factors();
    Portfolio portfolio;
    portfolio.factors = factors;
    portfolio.positions = {
        {"equity", block({1.0e6, 2.0e6})},
        {"rates", block({}, {}, {0.0, 0.0, -2.0e7, 0.0})},
        {"vol", block({}, {}, {}, {0.0, 0.0, 0.0, -1.0e5})},
    };
    const std::vector<Real> covariance = factor_move_covariance();
    Scenario none;
    none.name = "base";
    none.assumptions = "no moves";
    const ScenarioResult result = run_scenario(portfolio, none, covariance, 0.95);

    REQUIRE(result.var_components_stressed.size() == 3);
    CHECK(result.var_component_residual == Approx(0.0).margin(1.0e-9));
    CHECK(result.var_components_stressed[0].pnl > 0.0);
    // The vol position is *short*, and its component is still positive: variance is even
    // in the sign of a beta, and this factor is uncorrelated with the rest, so it adds
    // dispersion whichever way the position sits. A component only goes negative when the
    // position is negatively correlated with what remains, which is the next check.
    CHECK(result.var_components_stressed[2].pnl > 0.0);

    const FactorSet pair{{{"RISK", FactorClass::equity_index, 100.0, "points"},
                          {"HEDGE", FactorClass::equity_index, 100.0, "points"}}};
    std::vector<Real> hedged(4, 0.0);
    hedged[0 * 2 + 0] = 0.01;                       // var(RISK)
    hedged[1 * 2 + 1] = 0.01;                       // var(HEDGE)
    hedged[0 * 2 + 1] = hedged[1 * 2 + 0] = -0.009; // strongly negatively correlated
    Portfolio book;
    book.factors = pair;
    // Built directly at two factors, since block() aligns to the four-factor universe.
    book.positions = {Position{"risky", ExposureVector{{1.0e6, 0.0}, {}, {}, {}, {}}},
                      Position{"hedge", ExposureVector{{0.0, 1.0e6}, {}, {}, {}, {}}}};
    Scenario none2;
    none2.name = "base";
    none2.assumptions = "no moves";
    const ScenarioResult offsetting = run_scenario(book, none2, hedged, 0.95);
    CHECK(offsetting.var_component_residual == Approx(0.0).margin(1.0e-9));
    // The two legs are mirror images, so each takes exactly half — symmetry, not a bug.
    CHECK(offsetting.var_components_stressed[0].pnl ==
          Approx(offsetting.var_components_stressed[1].pnl).epsilon(1.0e-12));
    // What the negative correlation actually buys: held together, the book is worth far
    // less risk than the two legs measured apart. That is the diversification claim, and
    // it is the one worth asserting on a symmetric pair.
    Portfolio alone_first;
    alone_first.factors = pair;
    alone_first.positions = {Position{"risky", ExposureVector{{1.0e6, 0.0}, {}, {}, {}, {}}}};
    Portfolio alone_second;
    alone_second.factors = pair;
    alone_second.positions = {Position{"hedge", ExposureVector{{0.0, 1.0e6}, {}, {}, {}, {}}}};
    const Real standalone_first = run_scenario(alone_first, none2, hedged, 0.95).stressed_var;
    const Real standalone_second = run_scenario(alone_second, none2, hedged, 0.95).stressed_var;
    CHECK(offsetting.stressed_var < standalone_first);
    CHECK(offsetting.stressed_var < standalone_second);
    // With correlation -0.9 on equal vols, combined sigma is sqrt(2(1-0.9)) = 0.447 of a
    // single leg, which is the closed form this doubles as a check of.
    CHECK(offsetting.stressed_var ==
          Approx(standalone_first * std::sqrt(2.0 * (1.0 - 0.9))).epsilon(1.0e-9));
}

TEST_CASE("a correlation lift raises risk for a diversified book and not for a flat one") {
    const FactorSet factors = four_factors();
    Portfolio portfolio;
    portfolio.factors = factors;
    portfolio.positions = {{"both legs", block({1.0e6, 1.0e6})}};
    Scenario diversify;
    diversify.name = "correlation +0.2";
    diversify.assumptions = "no moves, off-diagonal correlation lifted";
    diversify.distribution.correlation_increment = 0.2;
    const std::vector<Real> covariance = factor_move_covariance();

    Scenario none;
    none.name = "base";
    none.assumptions = "no moves";
    const ScenarioResult baseline = run_scenario(portfolio, none, covariance, 0.95);
    const ScenarioResult lifted = run_scenario(portfolio, diversify, covariance, 0.95);
    CHECK(lifted.stressed_volatility > baseline.base_volatility);
    CHECK(lifted.var_change_from_distribution > 0.0);

    // A book exposed to one factor only cannot be diversified, so correlation is inert.
    Portfolio single;
    single.factors = factors;
    single.positions = {{"spx only", block({1.0e6, 0.0})}};
    const ScenarioResult single_baseline = run_scenario(single, none, covariance, 0.95);
    const ScenarioResult single_lifted = run_scenario(single, diversify, covariance, 0.95);
    CHECK(single_lifted.stressed_volatility ==
          Approx(single_baseline.base_volatility).epsilon(1.0e-12));
}

TEST_CASE("the exposure mapping is checked against a full Black-Scholes revaluation") {
    // The stress layer never re-prices, so its accuracy is the Taylor truncation. This
    // measures that truncation instead of asserting it is small: the same option book is
    // shocked through the exposure map and re-priced through the Phase 2 engine.
    const MarketParams market{
        .spot = 4000.0, .rate = 0.03, .dividend_yield = 0.0, .volatility = 0.20, .maturity = 0.5};
    const std::vector<EuropeanOption> book = {
        EuropeanOption(OptionType::Call, 3800.0),
        EuropeanOption(OptionType::Call, 4000.0),
        EuropeanOption(OptionType::Call, 4200.0),
    };
    constexpr Count quantity = 100;

    FactorSet factors{{{"SPX", FactorClass::equity_index, 4000.0, "index points"}}};
    std::vector<Real> delta(1, 0.0);
    std::vector<Real> gamma(1, 0.0);
    Real base_value = 0.0;
    for (const EuropeanOption &option : book) {
        const Greeks greeks = black_scholes_greeks(option, market);
        delta[0] += greeks.delta * market.spot * static_cast<Real>(quantity);
        gamma[0] += 0.5 * greeks.gamma * market.spot * market.spot * static_cast<Real>(quantity);
        base_value += black_scholes(option, market).price * static_cast<Real>(quantity);
    }
    Portfolio portfolio;
    portfolio.factors = factors;
    // One position holding both blocks, so the engine sees delta and gamma together.
    ExposureVector combined;
    combined.delta = delta;
    combined.gamma = gamma;
    portfolio.positions = {{"call spread", combined}};

    Scenario crash = equity_crash();
    crash.shocks = {{"SPX", -0.20, 0.0}};
    const ScenarioResult result = run_scenario(portfolio, crash);

    MarketParams shocked = market;
    shocked.spot = market.spot * 0.80;
    Real stressed_value = 0.0;
    for (const EuropeanOption &option : book) {
        stressed_value += black_scholes(option, shocked).price * static_cast<Real>(quantity);
    }
    const Real exact = stressed_value - base_value;
    const Real gap = result.pnl_change - exact;
    // The delta-gamma map must be close, and the residual must be *reported* rather than
    // absorbed: a 20 % move is exactly where a quadratic map starts to lie.
    CHECK(std::abs(gap) < 0.02 * std::abs(exact));
    CHECK(result.pnl_change < 0.0);
    CHECK(exact < 0.0);

    // A small move must agree far better than a large one, which is what makes the
    // bound above a statement about truncation order rather than about tuning.
    Scenario tick = equity_crash();
    tick.shocks = {{"SPX", -0.001, 0.0}};
    shocked.spot = market.spot * 0.999;
    Real tick_value = 0.0;
    for (const EuropeanOption &option : book) {
        tick_value += black_scholes(option, shocked).price * static_cast<Real>(quantity);
    }
    const Real tick_gap = run_scenario(portfolio, tick).pnl_change - (tick_value - base_value);
    CHECK(std::abs(tick_gap / (tick_value - base_value)) < 0.01 * std::abs(gap / exact));
}
