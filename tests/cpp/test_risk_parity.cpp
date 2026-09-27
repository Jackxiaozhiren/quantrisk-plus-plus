#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include <cmath>
#include <numeric>
#include <vector>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/portfolio/risk_parity.hpp"

using Catch::Approx;
using quantrisk::Count;
using quantrisk::Real;
namespace portfolio = quantrisk::portfolio;

TEST_CASE("uncorrelated assets get inverse-volatility weights exactly") {
    const std::vector<Real> covariance = {0.01, 0.0, 0.0, 0.0, 0.04, 0.0, 0.0, 0.0, 0.25};
    const auto solution = portfolio::risk_parity(covariance, 3);
    // Equal contribution means w_i^2 sigma_ii equal, so w is proportional to
    // 1/sigma_i: 10, 5 and 2 over 17.
    CHECK(solution.weights[0] == Approx(10.0 / 17.0).epsilon(1.0e-10));
    CHECK(solution.weights[1] == Approx(5.0 / 17.0).epsilon(1.0e-10));
    CHECK(solution.weights[2] == Approx(2.0 / 17.0).epsilon(1.0e-10));
    CHECK(solution.converged);
    CHECK(solution.max_contribution_gap < 1.0e-9);
    for (const Real share : solution.contributions) {
        CHECK(share == Approx(1.0 / 3.0).epsilon(1.0e-9));
    }
}

TEST_CASE("the contributions really are equal for a correlated pair") {
    const Real sigma1 = 0.10;
    const Real sigma2 = 0.25;
    const Real correlation = 0.35;
    const Real cov = correlation * sigma1 * sigma2;
    const std::vector<Real> covariance = {sigma1 * sigma1, cov, cov, sigma2 * sigma2};
    const auto solution = portfolio::risk_parity(covariance, 2);
    REQUIRE(solution.converged);
    CHECK(solution.contributions[0] == Approx(solution.contributions[1]).epsilon(1.0e-9));
    CHECK(solution.weights[0] > solution.weights[1]); // the less volatile asset holds more
    CHECK(solution.weights[0] + solution.weights[1] == Approx(1.0).margin(1.0e-12));
    // Closed form for n = 2: equating w1 (sigma1^2 w1 + cov w2) and
    // w2 (cov w1 + sigma2^2 w2) cancels the cov terms and leaves
    // sigma1^2 w1^2 = sigma2^2 w2^2, i.e. w1 / w2 = sigma2 / sigma1.
    const Real ratio = sigma2 / sigma1;
    CHECK(solution.weights[0] == Approx(ratio / (1.0 + ratio)).epsilon(1.0e-9));
}

TEST_CASE("risk parity is scale invariant and differs from equal weight") {
    const std::vector<Real> small = {0.0004, 0.0001, 0.0001, 0.0009};
    std::vector<Real> scaled(small.size());
    for (std::size_t i = 0; i < small.size(); ++i) {
        scaled[i] = small[i] * 1.0e6;
    }
    const auto plain = portfolio::risk_parity(small, 2);
    const auto big = portfolio::risk_parity(scaled, 2);
    for (std::size_t i = 0; i < plain.weights.size(); ++i) {
        CHECK(plain.weights[i] == Approx(big.weights[i]).epsilon(1.0e-8));
    }
    CHECK(plain.weights[0] != Approx(0.5).epsilon(1.0e-3));
    // Recompute the variance from the definition, independently of the solver.
    const Real expected = small[0] * plain.weights[0] * plain.weights[0] +
                          2.0 * small[1] * plain.weights[0] * plain.weights[1] +
                          small[3] * plain.weights[1] * plain.weights[1];
    CHECK(plain.variance == Approx(expected).epsilon(1.0e-8));
}

TEST_CASE("the descent converges to the same portfolio from any positive start") {
    const std::vector<Real> covariance = {0.04, 0.006, 0.006, 0.09};
    const auto plain = portfolio::risk_parity(covariance, 2);
    const auto started = portfolio::risk_parity(covariance, 2, std::vector<Real>{0.99, 0.01});
    CHECK(plain.converged);
    CHECK(started.converged);
    CHECK(plain.weights[0] == Approx(started.weights[0]).epsilon(1.0e-9));
    CHECK(plain.weights[1] == Approx(started.weights[1]).epsilon(1.0e-9));
    CHECK_THAT(started.note, Catch::Matchers::ContainsSubstring("caller supplied"));
}

TEST_CASE("a zero-variance asset is refused rather than given a weight") {
    const std::vector<Real> covariance = {0.04, 0.0, 0.0, 0.0};
    const auto solution = portfolio::risk_parity(covariance, 2);
    CHECK_FALSE(solution.converged);
    CHECK_THAT(solution.note, Catch::Matchers::ContainsSubstring("zero variance"));
}

TEST_CASE("risk parity validates its inputs") {
    CHECK_THROWS_AS(portfolio::risk_parity(std::vector<Real>{0.04, 0.0, 0.0}, 2),
                    quantrisk::ValidationError);
    CHECK_THROWS_AS(portfolio::risk_parity(std::vector<Real>{0.04, 0.0, 0.0, 0.0}, 0),
                    quantrisk::ValidationError);
    CHECK_THROWS_AS(portfolio::risk_parity(std::vector<Real>{0.04, 0.0, 0.0, 0.0}, 2,
                                           std::vector<Real>{1.0, 0.0}),
                    quantrisk::ValidationError);
    CHECK_THROWS_AS(
        portfolio::risk_parity(std::vector<Real>{0.04, 0.0, 0.0, 0.0}, 2, std::vector<Real>{0.5}),
        quantrisk::ValidationError);
}
