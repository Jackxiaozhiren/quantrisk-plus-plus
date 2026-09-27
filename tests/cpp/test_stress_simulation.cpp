#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include <cmath>
#include <vector>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/portfolio/covariance.hpp"
#include "quantrisk/stress/simulation.hpp"

using namespace quantrisk;
using namespace quantrisk::stress;
using Catch::Approx;

namespace {

FactorSet two_factors() {
    return FactorSet{{
        {"SPX", FactorClass::equity_index, 4000.0, "index points"},
        {"UST10Y", FactorClass::rate, 0.04, "decimal p.a."},
    }};
}

/// Relative moves for the equity, absolute for the rate — the units the exposures answer
/// to, and therefore the units every covariance and every observed window below uses.
std::vector<Real> factor_covariance() {
    return {0.01, 0.0, 0.0, 0.0004}; // 10 % equity sd, 200 bp rate sd, independent
}

Portfolio delta_book() {
    Portfolio portfolio;
    portfolio.factors = two_factors();
    portfolio.positions = {
        {"equities", ExposureVector{{1.0e6, 0.0}, {}, {}, {}, {}}},
        {"rates", ExposureVector{{0.0, 0.0}, {}, {0.0, -2.0e7}, {}, {}}},
    };
    return portfolio;
}

Scenario base_scenario(const std::string &name) {
    Scenario scenario;
    scenario.name = name;
    scenario.assumptions = "test fixture";
    return scenario;
}

} // namespace

TEST_CASE("scenario sampling is reproducible by seed and different across seeds") {
    const auto covariance = factor_covariance();
    const auto first = sample_factor_moves(covariance, 2, 500, 42);
    const auto repeat = sample_factor_moves(covariance, 2, 500, 42);
    const auto other = sample_factor_moves(covariance, 2, 500, 43);

    REQUIRE(first.moves.size() == repeat.moves.size());
    CHECK(first.moves == repeat.moves);
    CHECK_FALSE(first.moves == other.moves);
    CHECK(first.seed == 42);
    CHECK(first.paths == 500);
}

TEST_CASE("the sampled dispersion recovers the covariance it was drawn from") {
    const auto covariance = factor_covariance();
    constexpr Count paths = 200'000;
    const auto sample = sample_factor_moves(covariance, 2, paths, 7);

    // Recompute the sample covariance with the library's own estimator, so this checks
    // the draw against an independent path through the same arithmetic.
    const auto estimate = quantrisk::portfolio::sample_covariance(sample.moves, 2, paths);
    const std::vector<Real> recovered = estimate.values;
    CHECK(recovered[0] == Approx(0.01).epsilon(0.02));
    CHECK(recovered[3] == Approx(0.0004).epsilon(0.02));
    CHECK(std::abs(recovered[1]) < 0.02 * std::sqrt(0.01 * 0.0004));
}

TEST_CASE("a covariance with no Cholesky factor is refused, not jittered") {
    // Indefinite: correlation -1.5 on two unit-variance assets.
    const std::vector<Real> broken = {1.0, -1.5, -1.5, 1.0};
    CHECK_THROWS_AS(sample_factor_moves(broken, 2, 10, 1), ValidationError);

    const std::vector<Real> singular = {1.0, 1.0, 1.0, 1.0};
    CHECK_THROWS_AS(sample_factor_moves(singular, 2, 10, 1), ValidationError);

    CHECK_THROWS_AS(sample_factor_moves(factor_covariance(), 2, 0, 1), ValidationError);
    CHECK_THROWS_AS(sample_factor_moves(factor_covariance(), 3, 10, 1), ValidationError);
}

TEST_CASE("replaying one observed row equals the deterministic scenario for that row") {
    const Portfolio portfolio = delta_book();
    // One observed day: equities -3 %, rates +50 bp.
    const std::vector<Real> window = {-0.03, 0.005};
    const ScenarioSetResult replay =
        run_historical_scenarios(portfolio, base_scenario("one day"), window, 1);

    Scenario deterministic = base_scenario("one day");
    deterministic.shocks = {{"SPX", -0.03, 0.0}, {"UST10Y", 0.0, 0.005}};
    const ScenarioResult direct = run_scenario(portfolio, deterministic);

    REQUIRE(replay.pnl.size() == 1);
    CHECK(std::isnan(replay.var.value)); // one outcome is not a distribution
    CHECK_THAT(replay.note, Catch::Matchers::ContainsSubstring("not a distribution"));
    CHECK(replay.pnl[0] == Approx(direct.pnl_change).epsilon(1.0e-12));
    CHECK(replay.mean_pnl == Approx(direct.pnl_change).epsilon(1.0e-12));
    // A single outcome has no dispersion by definition, and the code must say zero
    // rather than emit NaN or a division by n-1 that never happened.
    CHECK(replay.volatility == 0.0);
    CHECK(replay.worst_pnl == replay.best_pnl);
    CHECK(replay.position_attribution_residual == Approx(0.0).margin(1.0e-9));
    CHECK(replay.factor_attribution_residual == Approx(0.0).margin(1.0e-9));
}

TEST_CASE("a historical window of known outcomes gives exactly its own quantiles") {
    const Portfolio portfolio = delta_book();
    // Five observed days, each a pair of (equity relative move, rate absolute move).
    // P&L is -1e6 * equity move, so the +4 % day is the best P&L and the -4 % day the
    // worst.
    const std::vector<Real> window = {-0.01, 0.0, 0.02, 0.0, -0.03, 0.0, 0.04, 0.0, -0.04, 0.0};
    const ScenarioSetResult replay =
        run_historical_scenarios(portfolio, base_scenario("five days"), window, 5);

    CHECK(replay.scenarios == 5);
    CHECK(replay.worst_pnl == Approx(-40000.0).epsilon(1.0e-12));
    CHECK(replay.best_pnl == Approx(40000.0).epsilon(1.0e-12));
    // A +1e6 delta earns +1e6 per 100 % move, so the mean follows the moves' own sign.
    const Real expected_mean = 1.0e6 * (-0.01 + 0.02 - 0.03 + 0.04 - 0.04) / 5.0;
    CHECK(replay.mean_pnl == Approx(expected_mean).epsilon(1.0e-12));
    // Unbiased sd of the five outcomes, computed here rather than by reusing the
    // engine's own summation.
    const std::vector<Real> pnl = {-10000.0, 20000.0, -30000.0, 40000.0, -40000.0};
    Real sum = 0.0;
    for (const Real value : pnl) {
        sum += value;
    }
    Real squares = 0.0;
    for (const Real value : pnl) {
        squares += (value - sum / 5.0) * (value - sum / 5.0);
    }
    CHECK(replay.volatility == Approx(std::sqrt(squares / 4.0)).epsilon(1.0e-12));
    CHECK_THAT(replay.generator, Catch::Matchers::ContainsSubstring("replay of 5"));
}

TEST_CASE("historical attribution adds up two ways over a whole window") {
    const Portfolio portfolio = delta_book();
    std::vector<Real> window;
    for (Count day = 0; day < 250; ++day) {
        window.push_back(0.01 * std::sin(static_cast<Real>(day) / 9.0));
        window.push_back(0.001 * std::cos(static_cast<Real>(day) / 7.0));
    }
    const ScenarioSetResult replay =
        run_historical_scenarios(portfolio, base_scenario("a year"), window, 250);

    Real positions = 0.0;
    for (const PositionContribution &part : replay.by_position) {
        positions += part.pnl;
    }
    CHECK(replay.position_attribution_residual == Approx(0.0).margin(1.0e-8));
    CHECK(positions == Approx(replay.mean_pnl).margin(1.0e-8));

    Real factors = 0.0;
    for (const FactorSummary &part : replay.by_factor) {
        factors += part.mean_contribution;
    }
    CHECK(factors == Approx(replay.mean_pnl).margin(1.0e-8));
    // The worst single day for the equity factor must be a loss, and the rate factor's
    // worst day is a separate day; reporting them per factor is the point of the column.
    CHECK(replay.by_factor[0].worst_contribution < 0.0);
}

TEST_CASE("an empty or misaligned historical window is refused") {
    const Portfolio portfolio = delta_book();
    const std::vector<Real> window = {-0.01, 0.001};
    CHECK_THROWS_AS(run_historical_scenarios(portfolio, base_scenario("x"), window, 0),
                    ValidationError);
    CHECK_THROWS_AS(run_historical_scenarios(portfolio, base_scenario("x"), window, 3),
                    ValidationError); // 3 rows of 2 needs 6 entries
}

TEST_CASE("a Monte Carlo set centres on the deterministic stress") {
    const Portfolio portfolio = delta_book();
    const auto covariance = factor_covariance();

    Scenario stress = base_scenario("equity -20%");
    stress.kind = ScenarioKind::monte_carlo;
    stress.shocks = {{"SPX", -0.20, 0.0}};
    const ScenarioSetResult set =
        run_monte_carlo_scenarios(portfolio, stress, covariance, 200'000, 11, 0.95);

    const ScenarioResult direct = run_scenario(portfolio, stress);
    // The mean of the simulated outcomes is the linearised stress exactly; gamma would
    // bend it, and this book carries none.
    CHECK(set.mean_pnl == Approx(direct.pnl_change).epsilon(0.005));
    CHECK(set.position_attribution_residual == Approx(0.0).margin(1.0e-6));
    CHECK(set.factor_attribution_residual == Approx(0.0).margin(1.0e-6));
}

TEST_CASE("simulated stress VaR converges to the parametric number for a linear book") {
    const Portfolio portfolio = delta_book();
    const auto covariance = factor_covariance();
    Scenario none = base_scenario("no stress");
    none.kind = ScenarioKind::monte_carlo;

    // Parametric route: beta'Sbeta under the Gaussian quantile.
    const ScenarioResult parametric = run_scenario(portfolio, none, covariance, 0.95);
    REQUIRE(parametric.has_risk_metrics);

    // Same seed on both: the sampler draws sequentially, so the 50k set is a prefix of
    // the 400k set and the two errors are comparable rather than independently lucky.
    constexpr Seed convergence_seed = 21;
    const ScenarioSetResult small =
        run_monte_carlo_scenarios(portfolio, none, covariance, 50'000, convergence_seed, 0.95);
    const ScenarioSetResult large =
        run_monte_carlo_scenarios(portfolio, none, covariance, 400'000, convergence_seed, 0.95);

    // Two independent code paths — a Cholesky draw plus an empirical quantile, against a
    // closed form — landing on the same number is the check. The tolerance is set from
    // the sampling error, not from the gap that happened to appear.
    CHECK(std::abs(small.var.value - parametric.base_var) / parametric.base_var < 0.02);
    CHECK(std::abs(large.var.value - parametric.base_var) / parametric.base_var < 0.01);
    // Convergence, not just agreement: the longer run must be the closer one.
    CHECK(std::abs(large.var.value - parametric.base_var) <
          std::abs(small.var.value - parametric.base_var));
    // ES must dominate VaR, which is the definitional ordering and a cheap guard against
    // the two estimators having been swapped.
    CHECK(large.es.value >= large.var.value);
}

TEST_CASE("convexity makes the outcome distribution non-Gaussian, and that is visible") {
    Portfolio portfolio;
    portfolio.factors = two_factors();
    // Long gamma on the equity factor: the P&L is quadratic in a Gaussian move, so it is
    // right-skewed and its mean sits above its median-ish quantile in a way a Gaussian
    // beta'Sbeta number cannot express.
    portfolio.positions = {
        {"convex", ExposureVector{{1.0e6, 0.0}, {5.0e5, 0.0}, {}, {}, {}}},
    };
    const auto covariance = factor_covariance();
    Scenario none = base_scenario("no stress");
    none.kind = ScenarioKind::monte_carlo;
    const ScenarioSetResult simulated =
        run_monte_carlo_scenarios(portfolio, none, covariance, 200'000, 31, 0.95);
    const ScenarioResult parametric = run_scenario(portfolio, none, covariance, 0.95);

    // The parametric number ignores gamma entirely, so it must differ from the simulated
    // distribution's own tail. This is a limitation of the Gaussian map, stated in a test.
    const Real third_moment = [&] {
        Real total = 0.0;
        for (const Real value : simulated.pnl) {
            const Real deviation = value - simulated.mean_pnl;
            total += deviation * deviation * deviation;
        }
        return total / static_cast<Real>(simulated.pnl.size());
    }();
    const Real skew = third_moment / std::pow(simulated.volatility, 3);
    CHECK(skew > 0.05);              // a Gaussian generator must not produce a symmetric P&L here
    CHECK(simulated.mean_pnl > 0.0); // long gamma is positive expected P&L under moves
    CHECK(parametric.base_volatility > 0.0);
}

TEST_CASE("a Monte Carlo set is reproducible and changes with the seed") {
    const Portfolio portfolio = delta_book();
    const auto covariance = factor_covariance();
    Scenario none = base_scenario("no stress");
    none.kind = ScenarioKind::monte_carlo;
    const ScenarioSetResult first =
        run_monte_carlo_scenarios(portfolio, none, covariance, 5'000, 77, 0.95);
    const ScenarioSetResult repeat =
        run_monte_carlo_scenarios(portfolio, none, covariance, 5'000, 77, 0.95);
    const ScenarioSetResult different =
        run_monte_carlo_scenarios(portfolio, none, covariance, 5'000, 78, 0.95);
    CHECK(first.pnl == repeat.pnl);
    CHECK_FALSE(first.pnl == different.pnl);
    CHECK_THAT(first.generator, Catch::Matchers::ContainsSubstring("seed 77"));
}

TEST_CASE("a volatility multiplier raises the simulated dispersion") {
    const Portfolio portfolio = delta_book();
    const auto covariance = factor_covariance();
    Scenario calm = base_scenario("no stress");
    calm.kind = ScenarioKind::monte_carlo;
    Scenario turbulent = calm;
    turbulent.name = "vol x2";
    turbulent.distribution.volatility_multiplier = 2.0;

    const ScenarioSetResult base =
        run_monte_carlo_scenarios(portfolio, calm, covariance, 100'000, 5, 0.95);
    const ScenarioSetResult stressed =
        run_monte_carlo_scenarios(portfolio, turbulent, covariance, 100'000, 5, 0.95);
    // Same seed, so the only difference is the deformation: the ratio should be ~2.
    CHECK(stressed.volatility == Approx(2.0 * base.volatility).epsilon(0.01));
    CHECK(stressed.var.value > base.var.value);
    CHECK_THAT(stressed.note, Catch::Matchers::ContainsSubstring("scaled by 2"));
}
