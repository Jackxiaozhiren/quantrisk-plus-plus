#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include <algorithm>
#include <cmath>
#include <numeric>
#include <vector>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/portfolio/cvar.hpp"
#include "quantrisk/risk/measures.hpp"

using Catch::Approx;
using quantrisk::Count;
using quantrisk::Real;
namespace portfolio = quantrisk::portfolio;

namespace {

/// Expected shortfall of an empirical loss sample, interpolated over the tail
/// fraction. An independent implementation of the same quantity the LP optimises.
[[nodiscard]] Real empirical_es(std::vector<Real> losses, const Real confidence) {
    std::sort(losses.begin(), losses.end(), std::greater<Real>());
    const Real tail = (1.0 - confidence) * static_cast<Real>(losses.size());
    const Count whole = static_cast<Count>(std::floor(tail));
    const Real fraction = tail - static_cast<Real>(whole);
    Real total = 0.0;
    for (Count i = 0; i < whole; ++i) {
        total += losses[static_cast<std::size_t>(i)];
    }
    if (whole < static_cast<Count>(losses.size())) {
        total += fraction * losses[static_cast<std::size_t>(whole)];
    }
    return total / tail;
}

[[nodiscard]] std::vector<Real> losses_for(const std::vector<Real> &scenario_returns,
                                           const std::vector<Real> &weights, const Count assets) {
    const Count scenarios = static_cast<Count>(scenario_returns.size()) / assets;
    std::vector<Real> losses(static_cast<std::size_t>(scenarios));
    for (Count i = 0; i < scenarios; ++i) {
        Real total = 0.0;
        for (Count j = 0; j < assets; ++j) {
            total += scenario_returns[static_cast<std::size_t>(i * assets + j)] *
                     weights[static_cast<std::size_t>(j)];
        }
        losses[static_cast<std::size_t>(i)] = -total;
    }
    return losses;
}

} // namespace

TEST_CASE("CVaR minimisation beats every point of a fine weight grid") {
    // Three assets, six scenarios. The LP's value may not exceed the best value on
    // a dense simplex grid, because the grid is a subset of the feasible set.
    const std::vector<Real> scenarios = {0.02,  -0.01, 0.005, //
                                         -0.05, 0.03,  0.01,  //
                                         0.01,  0.04,  -0.02, //
                                         -0.08, -0.02, 0.06,  //
                                         0.03,  -0.03, 0.00,  //
                                         0.00,  0.01,  -0.06};
    portfolio::CvarRequest request;
    request.assets = 3;
    request.scenarios = 6;
    request.scenario_returns = scenarios;
    request.confidence = 0.9;
    const auto solution = portfolio::minimise_cvar(request);
    REQUIRE(solution.solved);
    CHECK(solution.status == "optimal");
    CHECK(solution.certified);
    CHECK(solution.budget_residual <= 1.0e-9);
    CHECK(solution.weight_bound_violation <= 1.0e-9);
    CHECK(solution.cvar == Approx(solution.recomputed_cvar).epsilon(1.0e-9));
    CHECK(solution.alpha <= solution.cvar + 1.0e-12);

    Real best_grid = std::numeric_limits<Real>::infinity();
    for (Count a = 0; a <= 20; ++a) {
        for (Count b = 0; b + a <= 20; ++b) {
            const Real wa = static_cast<Real>(a) / 20.0;
            const Real wb = static_cast<Real>(b) / 20.0;
            const std::vector<Real> weights = {wa, wb, 1.0 - wa - wb};
            best_grid = std::min(best_grid, empirical_es(losses_for(scenarios, weights, 3), 0.9));
        }
    }
    CHECK(solution.cvar <= best_grid + 1.0e-9);
    // The two conventions for the discrete tail should agree closely on the chosen
    // weights; any gap is a convention difference, not an error, and is measured
    // rather than asserted away.
    const Real own_es = empirical_es(losses_for(scenarios, solution.weights, 3), 0.9);
    CHECK(std::abs(own_es - solution.cvar) < 0.15 * std::abs(own_es));
}

TEST_CASE("a single asset leaves no freedom, so the LP must still answer") {
    const std::vector<Real> scenarios = {0.01, -0.02, 0.03, -0.09, 0.005};
    portfolio::CvarRequest request;
    request.assets = 1;
    request.scenarios = 5;
    request.scenario_returns = scenarios;
    request.confidence = 0.8;
    const auto solution = portfolio::minimise_cvar(request);
    REQUIRE(solution.solved);
    CHECK(solution.weights[0] == Approx(1.0).epsilon(1.0e-9));
    const Real expected = empirical_es(losses_for(scenarios, {1.0}, 1), 0.8);
    CHECK(solution.cvar == Approx(expected).epsilon(1.0e-6));
}

TEST_CASE("an unreachable target return is reported, not quietly dropped") {
    const std::vector<Real> scenarios = {0.02, -0.01, -0.05, 0.03, 0.01, 0.04};
    portfolio::CvarRequest request;
    request.assets = 2;
    request.scenarios = 3;
    request.scenario_returns = scenarios;
    request.expected_returns = {0.01, 0.02};
    request.confidence = 0.9;
    request.target_return = 0.50; // above every asset's return
    const auto solution = portfolio::minimise_cvar(request);
    CHECK_FALSE(solution.solved);
    CHECK(solution.status == "infeasible");
    CHECK(std::isnan(solution.cvar));
}

TEST_CASE("a reachable target tightens the CVaR") {
    const std::vector<Real> scenarios = {0.02,  -0.01, //
                                         -0.05, 0.03,  //
                                         0.01,  0.04,  //
                                         -0.08, -0.02, //
                                         0.03,  -0.03, //
                                         0.00,  0.01};
    portfolio::CvarRequest request;
    request.assets = 2;
    request.scenarios = 6;
    request.scenario_returns = scenarios;
    request.expected_returns = {0.012, 0.009};
    request.confidence = 0.9;
    const auto free_ = portfolio::minimise_cvar(request);
    request.target_return = 0.0115;
    const auto held = portfolio::minimise_cvar(request);
    REQUIRE(free_.solved);
    REQUIRE(held.solved);
    CHECK(held.certified);
    CHECK(held.target_residual <= 1.0e-9);
    CHECK(held.cvar >= free_.cvar - 1.0e-9); // more constraints, never less risk
}

TEST_CASE("CVaR requests validate their shape and inputs") {
    portfolio::CvarRequest request;
    request.assets = 2;
    request.scenarios = 3;
    request.scenario_returns = {0.01, 0.02, 0.03}; // wrong length
    request.confidence = 0.9;
    CHECK_THROWS_AS(portfolio::minimise_cvar(request), quantrisk::ValidationError);

    request.scenario_returns = {0.01, 0.02, 0.03, 0.04, 0.05, 0.06};
    request.confidence = 1.0;
    CHECK_THROWS_AS(portfolio::minimise_cvar(request), quantrisk::ValidationError);
    request.confidence = 0.9;
    request.target_return = 0.01;
    CHECK_THROWS_AS(portfolio::minimise_cvar(request),
                    quantrisk::ValidationError); // target without expected returns
}
