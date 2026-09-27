#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include <cmath>
#include <limits>
#include <vector>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/portfolio/covariance.hpp"
#include "quantrisk/portfolio/mean_variance.hpp"
#include "quantrisk/risk/measures.hpp"

using Catch::Approx;
using quantrisk::Count;
using quantrisk::Real;
namespace portfolio = quantrisk::portfolio;

namespace {

[[nodiscard]] portfolio::OptimizerInputs problem(const std::vector<Real> &covariance,
                                                 const std::vector<Real> &expected_returns,
                                                 const Count assets) {
    portfolio::OptimizerInputs inputs;
    inputs.assets = assets;
    inputs.covariance = covariance;
    inputs.expected_returns = expected_returns;
    return inputs;
}

[[nodiscard]] Real variance_of(const portfolio::PortfolioSolution &solution,
                               const std::vector<Real> &covariance) {
    Real total = 0.0;
    for (Count i = 0; i < solution.assets; ++i) {
        for (Count j = 0; j < solution.assets; ++j) {
            total += solution.weights[static_cast<std::size_t>(i)] *
                     solution.weights[static_cast<std::size_t>(j)] *
                     covariance[static_cast<std::size_t>(i * solution.assets + j)];
        }
    }
    return total;
}

} // namespace

TEST_CASE("two-asset minimum variance matches the closed form") {
    // Sigma = [[4,1],[1,1]] gives Sigma^-1 1 proportional to [0,1], so the whole
    // portfolio belongs to the second asset: verifiable without a solver.
    const std::vector<Real> covariance = {4.0, 1.0, 1.0, 1.0};
    const auto solution = portfolio::minimum_variance(problem(covariance, {}, 2), {});
    CHECK(solution.weights[0] == Approx(0.0).margin(1.0e-14));
    CHECK(solution.weights[1] == Approx(1.0).margin(1.0e-14));
    CHECK(solution.variance == Approx(1.0).epsilon(1.0e-12));
    CHECK(solution.volatility == Approx(1.0).epsilon(1.0e-12));
    CHECK(solution.budget_residual < 1.0e-12);
    CHECK(solution.verified_optimal);
    CHECK(solution.feasible);
}

TEST_CASE("uncorrelated equal-variance assets split the budget equally") {
    const Count assets = 5;
    const Real variance = 0.04;
    std::vector<Real> covariance(static_cast<std::size_t>(assets * assets), 0.0);
    for (Count i = 0; i < assets; ++i) {
        covariance[static_cast<std::size_t>(i * assets + i)] = variance;
    }
    const auto solution = portfolio::minimum_variance(problem(covariance, {}, assets), {});
    for (const Real weight : solution.weights) {
        CHECK(weight == Approx(1.0 / 5.0).epsilon(1.0e-12));
    }
    CHECK(solution.variance == Approx(variance / 5.0).epsilon(1.0e-12));
    CHECK(solution.verified_optimal);
}

TEST_CASE("the long-only bound actually binds and the answer is the corner") {
    // Sigma = [[1,0.45],[0.45,0.25]] has an unconstrained minimum-variance weight of
    // about -0.571 on asset 0, so long-only must move fully onto asset 1.
    const std::vector<Real> covariance = {1.0, 0.45, 0.45, 0.25};
    const auto allowed = [&] {
        portfolio::OptimizationRequest request;
        request.long_only = false;
        return portfolio::minimum_variance(problem(covariance, {}, 2), request);
    }();
    const auto constrained = portfolio::minimum_variance(problem(covariance, {}, 2), {});

    REQUIRE(allowed.weights[0] < -0.5);
    CHECK(allowed.weights[0] == Approx(-4.0 / 7.0).epsilon(1.0e-9));
    // With the bound switched off there is no bound to violate, so the reported
    // violation stays zero even though the weight itself is negative.
    CHECK(allowed.weight_bound_violation == Approx(0.0).margin(1.0e-18));

    CHECK(constrained.weights[0] == Approx(0.0).margin(1.0e-14));
    CHECK(constrained.weights[1] == Approx(1.0).margin(1.0e-14));
    CHECK(constrained.weight_bound_violation < 1.0e-14);
    CHECK(constrained.verified_optimal);
    CHECK(constrained.variance > allowed.variance); // a bound can only hurt
}

TEST_CASE("a target return is met exactly when it binds") {
    const std::vector<Real> covariance = {0.04, 0.006, 0.006, 0.09};
    const std::vector<Real> expected_returns = {0.06, 0.12};
    portfolio::OptimizationRequest request;
    request.target_return = 0.10;
    const auto solution =
        portfolio::minimum_variance(problem(covariance, expected_returns, 2), request);
    CHECK(solution.expected_return == Approx(0.10).epsilon(1.0e-9));
    CHECK(solution.target_residual < 1.0e-12);
    CHECK(solution.budget_residual < 1.0e-12);
    CHECK(solution.weights[0] >= -1.0e-12);
    CHECK(solution.weights[1] >= -1.0e-12);
    CHECK_THAT(solution.note, Catch::Matchers::ContainsSubstring("binds"));
    CHECK(solution.verified_optimal);
    // w2 = 0.10/0.12 style split: expected return of the weights must be the target.
    const Real implied =
        expected_returns[0] * solution.weights[0] + expected_returns[1] * solution.weights[1];
    CHECK(implied == Approx(0.10).epsilon(1.0e-9));
}

TEST_CASE("an easily met target is reported inactive, not imposed") {
    const std::vector<Real> covariance = {0.04, 0.006, 0.006, 0.09};
    const std::vector<Real> expected_returns = {0.06, 0.12};
    const auto unconstrained =
        portfolio::minimum_variance(problem(covariance, expected_returns, 2), {});
    portfolio::OptimizationRequest request;
    request.target_return = 0.001; // far below what the free portfolio already earns
    const auto solution =
        portfolio::minimum_variance(problem(covariance, expected_returns, 2), request);
    CHECK_THAT(solution.note, Catch::Matchers::ContainsSubstring("inactive"));
    REQUIRE(solution.weights.size() == unconstrained.weights.size());
    for (std::size_t index = 0; index < solution.weights.size(); ++index) {
        CHECK(solution.weights[index] ==
              Approx(unconstrained.weights[index]).epsilon(1.0e-12).margin(1.0e-18));
    }
    CHECK(solution.verified_optimal);
}

TEST_CASE("a zero-variance asset is held exclusively, and the certificate knows") {
    // Asset 1 never moves: the minimum-variance portfolio is "all of it", with zero
    // variance. A solver that refused to touch a singular matrix could not answer.
    const std::vector<Real> covariance = {0.04, 0.0, 0.0, 0.0};
    const auto solution = portfolio::minimum_variance(problem(covariance, {}, 2), {});
    CHECK(solution.weights[0] == Approx(0.0).margin(1.0e-12));
    CHECK(solution.weights[1] == Approx(1.0).epsilon(1.0e-9));
    CHECK(solution.variance == Approx(0.0).margin(1.0e-16));
    CHECK(solution.feasible);
    // The saddle-point system is nonsingular here, so the flat asset is found
    // exactly and no rank truncation is even needed.
    CHECK(solution.verified_optimal);
}

TEST_CASE("the frontier is monotone in target return") {
    const std::vector<Real> covariance = {0.04, 0.008, 0.008, 0.09};
    const std::vector<Real> expected_returns = {0.05, 0.14};
    const auto inputs = problem(covariance, expected_returns, 2);
    std::vector<Real> targets;
    for (int step = 0; step <= 8; ++step) {
        targets.push_back(0.05 + 0.01 * static_cast<Real>(step));
    }
    portfolio::OptimizationRequest request;
    const auto frontier = portfolio::efficient_frontier(inputs, targets, request);
    REQUIRE(frontier.size() == targets.size());
    Real previous_variance = -1.0;
    Real previous_return = -1.0;
    for (const auto &point : frontier) {
        CAPTURE(point.expected_return);
        CHECK(point.verified_optimal);
        CHECK(point.variance >= previous_variance - 1.0e-14);
        CHECK(point.expected_return >= previous_return - 1.0e-14);
        previous_variance = point.variance;
        previous_return = point.expected_return;
    }
    CHECK(frontier.back().variance > frontier.front().variance);
}

TEST_CASE("maximum Sharpe matches the unconstrained tangency closed form") {
    // Two assets, no binding non-negativity constraint: the tangency portfolio is
    // Sigma^-1 (mu - rf 1) normalised to sum to one.
    const std::vector<Real> covariance = {0.04, 0.006, 0.006, 0.09};
    const std::vector<Real> expected_returns = {0.10, 0.16};
    const Real risk_free = 0.02;
    const Real excess0 = expected_returns[0] - risk_free;
    const Real excess1 = expected_returns[1] - risk_free;
    const Real determinant = 0.04 * 0.09 - 0.006 * 0.006;
    const Real raw0 = (0.09 * excess0 - 0.006 * excess1) / determinant;
    const Real raw1 = (-0.006 * excess0 + 0.04 * excess1) / determinant;
    const Real reference0 = raw0 / (raw0 + raw1);
    const Real reference1 = raw1 / (raw0 + raw1);
    REQUIRE(reference0 > 0.0);
    REQUIRE(reference1 > 0.0);

    portfolio::OptimizationRequest request;
    request.risk_free_rate = risk_free;
    const auto solution =
        portfolio::maximum_sharpe(problem(covariance, expected_returns, 2), request);
    CHECK(solution.weights[0] == Approx(reference0).epsilon(1.0e-6));
    CHECK(solution.weights[1] == Approx(reference1).epsilon(1.0e-6));
    CHECK(solution.budget_residual < 1.0e-9);
    CHECK_THAT(solution.method, Catch::Matchers::ContainsSubstring("frontier search"));
    CHECK(solution.verified_optimal);
}

TEST_CASE("no portfolio can beat the maximum-Sharpe answer") {
    // Sample the simplex at random: nothing may have a strictly better Sharpe. That
    // is the property the search exists to deliver, and it is checked independently
    // of the search itself.
    const std::vector<Real> covariance = {0.05, 0.012, 0.012, 0.08};
    const std::vector<Real> expected_returns = {0.07, 0.15};
    portfolio::OptimizationRequest request;
    request.risk_free_rate = 0.03;
    const auto solution =
        portfolio::maximum_sharpe(problem(covariance, expected_returns, 2), request);
    const auto inputs = problem(covariance, expected_returns, 2);

    portfolio::OptimizationRequest probe = request;
    for (int step = 0; step <= 20; ++step) {
        const Real target = 0.07 + (0.15 - 0.07) * static_cast<Real>(step) / 20.0;
        probe.target_return = target;
        const auto point = portfolio::minimum_variance(inputs, probe);
        if (!point.verified_optimal) {
            continue;
        }
        CHECK(point.sharpe_ratio <= solution.sharpe_ratio + 1.0e-6);
    }
    CHECK(solution.sharpe_ratio > 0.0);
}

TEST_CASE("scenario losses are reported on the chosen weights") {
    const std::vector<Real> covariance = {0.04, 0.006, 0.006, 0.09};
    const std::vector<Real> expected_returns = {0.06, 0.12};
    // Six scenarios, oldest first.
    const std::vector<Real> scenarios = {0.01, 0.02, -0.03, 0.01, 0.00, -0.01,
                                         0.02, 0.01, -0.02, 0.05, 0.01, 0.03};
    auto inputs = problem(covariance, expected_returns, 2);
    inputs.scenario_returns = scenarios;
    inputs.scenario_count = 6;
    portfolio::OptimizationRequest request;
    request.cvar_confidence = 0.95;
    const auto solution = portfolio::minimum_variance(inputs, request);

    std::vector<Real> portfolio_returns;
    for (Count s = 0; s < 6; ++s) {
        portfolio_returns.push_back(
            scenarios[static_cast<std::size_t>(s * 2)] * solution.weights[0] +
            scenarios[static_cast<std::size_t>(s * 2 + 1)] * solution.weights[1]);
    }
    CHECK(solution.value_at_risk ==
          Approx(quantrisk::risk::historical_var(portfolio_returns, 0.95).value).epsilon(1.0e-12));
    CHECK(solution.conditional_var ==
          Approx(quantrisk::risk::historical_es(portfolio_returns, 0.95).value).epsilon(1.0e-12));
    CHECK(solution.conditional_var >= solution.value_at_risk);

    // Without scenarios the fields are NaN rather than a flattering zero.
    const auto bare = portfolio::minimum_variance(inputs, portfolio::OptimizationRequest{});
    inputs.scenario_count = 0;
    inputs.scenario_returns.clear();
    const auto without = portfolio::minimum_variance(inputs, portfolio::OptimizationRequest{});
    CHECK(std::isnan(without.value_at_risk));
    CHECK(std::isnan(without.conditional_var));
    (void)bare;
}

TEST_CASE("the optimiser refuses to invent an answer it cannot certify") {
    const std::vector<Real> covariance = {0.04, 0.006, 0.006, 0.09};
    CHECK_THROWS_AS(portfolio::minimum_variance(problem(covariance, {}, 2),
                                                [&] {
                                                    portfolio::OptimizationRequest request;
                                                    request.target_return = 0.1;
                                                    return request;
                                                }()),
                    quantrisk::ValidationError); // target with no expected returns

    CHECK_THROWS_AS(portfolio::minimum_variance(problem({0.04}, {}, 2), {}),
                    quantrisk::ValidationError); // covariance smaller than assets^2
    CHECK_THROWS_AS(portfolio::minimum_variance(problem(covariance, {0.06, 0.12, 0.2}, 2), {}),
                    quantrisk::ValidationError); // wrong return length
    CHECK_THROWS_AS(
        portfolio::maximum_sharpe(problem(covariance, {}, 2), portfolio::OptimizationRequest{}),
        quantrisk::ValidationError); // no mu, so no Sharpe
}

TEST_CASE("a perfectly collinear pair is solvable and the certificate still holds") {
    // Assets 0 and 1 are identical, so the matrix is singular. Any split between them
    // is equivalent; what must hold is feasibility, a certificate, and no NaN.
    const std::vector<Real> covariance = {0.04, 0.04, 0.00, 0.04, 0.04, 0.00, 0.00, 0.00, 0.09};
    const auto solution = portfolio::minimum_variance(problem(covariance, {}, 3), {});
    REQUIRE(std::isfinite(solution.variance));
    CHECK(solution.budget_residual < 1.0e-9);
    CHECK(solution.weight_bound_violation < 1.0e-9);
    CHECK(solution.feasible);
    // Asset 2 is uncorrelated, so its variance is *diversifying* and the optimum
    // holds it: minimising 0.04 (1 - w2)^2 + 0.09 w2^2 gives w2 = 0.08 / 0.26.
    // Assets 0 and 1 are identical, so only their sum is pinned.
    CHECK(solution.weights[2] == Approx(0.08 / 0.26).epsilon(1.0e-9));
    const Real total = solution.weights[0] + solution.weights[1];
    CHECK(total == Approx(1.0 - 0.08 / 0.26).epsilon(1.0e-9));
    CHECK(solution.variance == Approx(0.04 * (1.0 - 0.08 / 0.26) * (1.0 - 0.08 / 0.26) +
                                      0.09 * (0.08 / 0.26) * (0.08 / 0.26))
                                   .epsilon(1.0e-9));
    CHECK(variance_of(solution, covariance) == Approx(solution.variance).epsilon(1.0e-9));
}

TEST_CASE("an unreachable target is reported as unreachable, not as a portfolio") {
    // Long-only on two assets caps the achievable return at the best single asset.
    // Asking for more has an equality solution - it just requires shorting - and the
    // answer must say so in the fields *and* in the note, because the note is what
    // gets printed in a report while the residual is what gets asserted in a test.
    const std::vector<Real> covariance = {0.0004, 0.0, 0.0, 0.0009};
    portfolio::OptimizationRequest request;
    request.target_return = 0.5;
    const auto solution =
        portfolio::minimum_variance(problem(covariance, {0.001, 0.002}, 2), request);

    CHECK_FALSE(solution.feasible);
    CHECK_FALSE(solution.verified_optimal);
    CHECK(solution.expected_return == Approx(0.5).epsilon(1.0e-6)); // reached, but not
    CHECK(solution.weight_bound_violation > 1.0);                   // by a long portfolio
    CHECK_THAT(solution.note, Catch::Matchers::ContainsSubstring("bounds are violated"));
}

TEST_CASE("a negative opportunity set still returns the least-bad Sharpe") {
    // Every asset below the risk-free rate makes the maximum Sharpe negative, and the
    // maximum is then a corner rather than a tangency. The solver must find the corner
    // and certify it, not refuse: -1.6 beats -2.45, and both are honest answers about
    // a set with no positive excess return in it.
    const std::vector<Real> covariance = {0.0004, 0.0, 0.0, 0.0009};
    portfolio::OptimizationRequest request;
    request.risk_free_rate = 0.05;
    const auto solution =
        portfolio::maximum_sharpe(problem(covariance, {0.001, 0.002}, 2), request);

    CHECK(solution.feasible);
    CHECK(solution.weight_bound_violation < 1.0e-9);
    // w = (0, 1): (0.002 - 0.05) / 0.03 = -1.6, better than (0.001 - 0.05) / 0.02.
    CHECK(solution.sharpe_ratio == Approx(-1.6).epsilon(1.0e-6));
    CHECK(solution.weights[1] == Approx(1.0).epsilon(1.0e-6));
    CHECK(solution.weights[0] == Approx(0.0).margin(1.0e-8));
}
