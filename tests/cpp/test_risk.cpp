#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include <cmath>
#include <limits>
#include <vector>

#include "quantrisk/core/constants.hpp"
#include "quantrisk/core/rng.hpp"
#include "quantrisk/core/statistics.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/math/normal.hpp"
#include "quantrisk/math/special.hpp"
#include "quantrisk/risk/backtest.hpp"
#include "quantrisk/risk/bootstrap.hpp"
#include "quantrisk/risk/measures.hpp"

using Catch::Approx;
using quantrisk::Count;
using quantrisk::Real;
using quantrisk::Rng;
using quantrisk::ValidationError;
namespace risk = quantrisk::risk;

namespace {

std::vector<Real> gaussian_sample(const Count n, const Real mu, const Real sigma,
                                  const quantrisk::Seed seed) {
    Rng rng(seed);
    std::vector<Real> out(static_cast<std::size_t>(n));
    for (Count i = 0; i < n; ++i) {
        out[static_cast<std::size_t>(i)] = mu + sigma * rng.standard_normal();
    }
    return out;
}

} // namespace

TEST_CASE("return definitions are the two distinct formulas") {
    const std::vector<Real> prices = {100.0, 110.0, 99.0};
    const auto arithmetic = quantrisk::returns::arithmetic(prices);
    const auto logarithmic = quantrisk::returns::log_returns(prices);
    REQUIRE(arithmetic.size() == 2);
    REQUIRE(logarithmic.size() == 2);
    CHECK(arithmetic[0] == Approx(0.10).epsilon(1.0e-15));
    CHECK(arithmetic[1] == Approx(-0.10).epsilon(1.0e-15));
    CHECK(logarithmic[0] == Approx(std::log(1.1)).epsilon(1.0e-15));
    CHECK(logarithmic[1] == Approx(std::log(0.9)).epsilon(1.0e-15));
    // Arithmetic returns can reach -1 while a log return is always finite: the
    // definitions differ by more than rounding for large moves.
    const std::vector<Real> crash = {100.0, 1.0};
    CHECK(quantrisk::returns::arithmetic(crash)[0] == Approx(-0.99).epsilon(1.0e-12));
    CHECK(quantrisk::returns::log_returns(crash)[0] == Approx(std::log(0.01)).epsilon(1.0e-12));
    CHECK_THROWS_AS(quantrisk::returns::arithmetic(std::vector<Real>{100.0}), ValidationError);
    CHECK_THROWS_AS(quantrisk::returns::log_returns(std::vector<Real>{0.0, 1.0}), ValidationError);
}

TEST_CASE("historical VaR and ES reproduce hand-computed order statistics") {
    const std::vector<Real> sample = {0.01, -0.02, 0.03, -0.04, 0.05};
    // Losses L = -R sorted: {-0.05, -0.03, -0.01, 0.02, 0.04}
    const auto var = risk::historical_var(sample, 0.95);
    const auto es = risk::historical_es(sample, 0.95);
    CHECK(var.value == Approx(0.036).epsilon(1.0e-12)); // index 0.95 * 4 = 3.8
    CHECK(es.value == Approx(0.04).epsilon(1.0e-12));   // k = ceil(5 * 0.05) = 1
    CHECK(var.method == "historical_var");
    CHECK(var.observations == 5);
    CHECK(es.value >= var.value); // ES is never below VaR

    CHECK(risk::historical_var(sample, 0.99).value >= var.value); // monotone in alpha
    std::vector<Real> shifted(sample.size());
    for (std::size_t i = 0; i < sample.size(); ++i) {
        shifted[i] = sample[i] - 0.01;
    }
    // Translation equivariance: a uniformly worse sample shifts the measure.
    CHECK(risk::historical_var(shifted, 0.95).value == Approx(var.value + 0.01).epsilon(1e-12));
    CHECK(risk::historical_es(shifted, 0.95).value == Approx(es.value + 0.01).epsilon(1e-12));
}

TEST_CASE("Gaussian VaR and ES match their closed forms") {
    const std::vector<Real> sample = {1.0, -1.0}; // mean 0, s = sqrt(2)
    const Real sigma = std::sqrt(2.0);
    const auto var = risk::gaussian_var(sample, 0.95);
    const auto es = risk::gaussian_es(sample, 0.95);
    const Real z = quantrisk::inverse_normal_cdf(0.95);
    CHECK(var.value == Approx(z * sigma).epsilon(1.0e-12));
    CHECK(es.value == Approx(sigma * quantrisk::normal_pdf(z) / 0.05).epsilon(1.0e-10));
    CHECK(es.value > var.value);

    // On a normal sample the historical estimator must converge to the closed
    // form, and the Gaussian one must be stable.
    const std::vector<Real> big = gaussian_sample(100000, 0.0, 0.01, 42);
    const Real analytic_var = quantrisk::inverse_normal_cdf(0.95) * 0.01;
    CHECK(risk::gaussian_var(big, 0.95).value == Approx(analytic_var).epsilon(2.0e-2));
    CHECK(risk::historical_var(big, 0.95).value == Approx(analytic_var).epsilon(3.0e-2));
}

TEST_CASE("Monte Carlo risk measures on simulated P&L") {
    const std::vector<Real> pnl = gaussian_sample(50000, 0.0, 1.0, 7);
    const auto var = risk::monte_carlo_var(pnl, 0.95);
    const auto es = risk::monte_carlo_es(pnl, 0.95);
    CHECK(var.value == Approx(quantrisk::inverse_normal_cdf(0.95)).epsilon(5.0e-2));
    CHECK(es.value > var.value);
    CHECK(var.observations == 50000);
    if (std::isfinite(var.standard_error)) {
        CHECK(var.has_interval);
        CHECK(var.ci_low <= var.value);
        CHECK(var.ci_high >= var.value);
    }
}

TEST_CASE("linear P&L and sample covariance follow the documented row-major layout") {
    // Two assets, three scenarios. The contract is one row per scenario, so
    // (0.01, -0.02) is scenario 0 with asset 0 at +1 % and asset 1 at -2 %.
    const std::vector<Real> weights = {0.6, 0.4};
    const std::vector<Real> rows = {0.01, -0.02, 0.03, 0.00, 0.01, -0.01};
    const auto pnl = risk::linear_pnl(weights, rows, 2, 1000.0);
    REQUIRE(pnl.size() == 3);
    CHECK(pnl[0] == Approx(1000.0 * (0.6 * 0.01 + 0.4 * -0.02)).margin(1.0e-12));
    CHECK(pnl[1] == Approx(1000.0 * (0.6 * 0.03 + 0.4 * 0.00)).margin(1.0e-12));
    CHECK(pnl[2] == Approx(1000.0 * (0.6 * 0.01 + 0.4 * -0.01)).margin(1.0e-12));

    const auto covariance = risk::sample_covariance(rows, 2, 3);
    REQUIRE(covariance.size() == 4);
    const std::vector<Real> asset0 = {0.01, 0.03, 0.01};
    const std::vector<Real> asset1 = {-0.02, 0.00, -0.01};
    CHECK(covariance[0] == Approx(quantrisk::stats::sample_variance(asset0)).epsilon(1.0e-12));
    CHECK(covariance[3] == Approx(quantrisk::stats::sample_variance(asset1)).epsilon(1.0e-12));
    CHECK(covariance[1] == covariance[2]); // symmetric off-diagonal
    // The off-diagonal is recomputed from the definition rather than restating
    // what the implementation returned.
    const Real mean0 = quantrisk::stats::mean(asset0);
    const Real mean1 = quantrisk::stats::mean(asset1);
    Real cross = 0.0;
    for (std::size_t i = 0; i < asset0.size(); ++i) {
        cross += (asset0[i] - mean0) * (asset1[i] - mean1);
    }
    CHECK(covariance[1] == Approx(cross / 2.0).epsilon(1.0e-12));
    CHECK_THROWS_AS(risk::linear_pnl(std::vector<Real>{0.5, 0.5}, rows, 3, 100.0), ValidationError);
    CHECK_THROWS_AS(risk::sample_covariance(rows, 2, 1), ValidationError);
    CHECK_THROWS_AS(risk::linear_pnl(std::vector<Real>{std::nan("")}, rows, 1, 100.0),
                    ValidationError);
}

TEST_CASE("bootstrap intervals are reproducible, contain the point estimate, "
          "and cover the true value") {
    const std::vector<Real> sample = gaussian_sample(1000, 0.0, 0.02, 2024);
    const Real analytic_var = quantrisk::inverse_normal_cdf(0.95) * 0.02;

    const auto first =
        quantrisk::bootstrap_var(sample, 0.95, 1000, 0.90, quantrisk::BootstrapKind::Iid, 0, 42);
    const auto second =
        quantrisk::bootstrap_var(sample, 0.95, 1000, 0.90, quantrisk::BootstrapKind::Iid, 0, 42);
    CHECK(first.point == second.point);
    CHECK(first.ci_low == second.ci_low);
    CHECK(first.ci_high == second.ci_high);
    CHECK(first.replicates == 1000);
    CHECK(first.standard_error > 0.0);
    CHECK(first.ci_low <= first.point);
    CHECK(first.ci_high >= first.point);
    CHECK(first.measure == "historical_var");
    CHECK_THAT(first.note, Catch::Matchers::ContainsSubstring("serially independent"));
    // The interval must be plausible for the true value, not merely self-consistent.
    CHECK(first.ci_low <= analytic_var);
    CHECK(first.ci_high >= analytic_var);

    const auto es = quantrisk::bootstrap_es(sample, 0.95, 800, 0.90,
                                            quantrisk::BootstrapKind::MovingBlock, 0, 42);
    CHECK(es.block_length == quantrisk::suggested_block_length(static_cast<Count>(sample.size())));
    CHECK(es.block_length > 1); // blocks are what distinguishes this design
    CHECK(es.ci_low <= es.point);
    CHECK(es.ci_high >= es.point);
    CHECK_THAT(es.note, Catch::Matchers::ContainsSubstring("volatility clustering"));
}

TEST_CASE("bootstrap settings are validated") {
    const std::vector<Real> sample = gaussian_sample(200, 0.0, 0.01, 5);
    CHECK_THROWS_AS(quantrisk::bootstrap_var(sample, 1.0), ValidationError);
    CHECK_THROWS_AS(quantrisk::bootstrap_var(sample, 0.95, 0), ValidationError);
    CHECK_THROWS_AS(
        quantrisk::bootstrap_var(sample, 0.95, 100, 0.90, quantrisk::BootstrapKind::Iid, 5, 1),
        ValidationError);
    CHECK_THROWS_AS(quantrisk::bootstrap_var(sample, 0.95, 100, 0.90,
                                             quantrisk::BootstrapKind::MovingBlock, 200, 1),
                    ValidationError);
    CHECK_THROWS_AS(quantrisk::bootstrap_var(std::vector<Real>{0.01}, 0.95), ValidationError);
}

TEST_CASE("Kupiec POF test: zero statistic exactly when the rate matches nominal") {
    // 250 observations with 13 violations (5.2 %) against a 5 % nominal rate: the
    // test must be far from rejecting, and the statistic must be small and
    // non-negative. Both anchors are computed independently in Python from the
    // likelihood-ratio definition, not from this implementation.
    std::vector<Real> returns_sample(250, 0.0);
    for (std::size_t i = 0; i < returns_sample.size(); ++i) {
        returns_sample[i] = (i % 20 == 0) ? -0.03 : 0.001;
    }
    const auto series = quantrisk::flag_violations(returns_sample, 0.02);
    CAPTURE(series.exceptions, series.observations);
    CHECK(series.exceptions == 13);
    const auto result = quantrisk::kupiec_pof_test(series, 0.95);
    CHECK(result.statistic == Approx(0.02079191303162986).epsilon(1.0e-9));
    CHECK(result.p_value == Approx(0.8853472694425738).epsilon(1.0e-6));
    CHECK(result.degrees_of_freedom == 1);
    CHECK_FALSE(result.rejected_at_5_percent);

    // Exactly matching count => statistic 0 (the strongest possible check of the
    // likelihood algebra, because any algebraic slip moves it off zero).
    std::vector<int> flags(100, 0);
    for (int i = 0; i < 10; ++i) {
        flags[static_cast<std::size_t>(i * 10)] = 1;
    }
    std::vector<Real> returns2(100, 0.0);
    for (std::size_t i = 0; i < returns2.size(); ++i) {
        returns2[i] = flags[i] ? -0.05 : 0.01;
    }
    const auto matched = quantrisk::flag_violations(returns2, 0.02);
    CHECK(matched.exceptions == 10);
    const auto matched_result = quantrisk::kupiec_pof_test(matched, 0.90);
    CHECK(matched_result.statistic == Approx(0.0).margin(1.0e-12));
    CHECK(matched_result.p_value == Approx(1.0).margin(1.0e-12));
    CHECK_FALSE(matched_result.rejected_at_5_percent);
}

TEST_CASE("Kupiec test rejects over- and under-violation, and says so") {
    // A badly too-low VaR: half the observations violate.
    std::vector<Real> bad(200, 0.005);
    for (std::size_t i = 0; i < 100; ++i) {
        bad[i] = -0.10;
    }
    const auto bad_series = quantrisk::flag_violations(bad, 0.01);
    const auto bad_result = quantrisk::kupiec_pof_test(bad_series, 0.95);
    CHECK(bad_result.rejected_at_5_percent);
    CHECK(bad_result.statistic == Approx(332.14624136433014).epsilon(1.0e-9));
    CHECK(bad_result.p_value == Approx(3.275952863131421e-74).epsilon(1.0e-4));

    // Never violating is also a failure of the forecast, not a clean bill.
    const std::vector<Real> quiet(250, 0.001);
    const auto quiet_series = quantrisk::flag_violations(quiet, 0.01);
    CHECK(quiet_series.exceptions == 0);
    const auto quiet_result = quantrisk::kupiec_pof_test(quiet_series, 0.95);
    CHECK(quiet_result.statistic == Approx(25.64664719377529).epsilon(1.0e-9));
    CHECK(quiet_result.p_value == Approx(4.1000723664166635e-07).epsilon(1.0e-4));
    CHECK(quiet_result.rejected_at_5_percent);
}

TEST_CASE("the likelihood ratio is non-negative across the whole count grid") {
    // A likelihood ratio cannot be negative: the restricted model is a special
    // case of the fitted one. An earlier version dropped the x ln(p) term from the
    // null likelihood, which made the statistic go negative for near-nominal
    // violation counts while still "looking like a p-value of 1". This grid is the
    // regression test for that class of algebraic slip, including both boundaries.
    for (const Count n : {20, 100, 250}) {
        for (Count x = 0; x <= n; ++x) {
            std::vector<Real> returns_sample(static_cast<std::size_t>(n), 0.01);
            for (Count i = 0; i < x; ++i) {
                returns_sample[static_cast<std::size_t>(i)] = -0.05;
            }
            const auto series = quantrisk::flag_violations(returns_sample, 0.02);
            REQUIRE(series.exceptions == x);
            const auto result = quantrisk::kupiec_pof_test(series, 0.95);
            const auto independence = quantrisk::christoffersen_independence_test(series);
            const auto conditional =
                quantrisk::christoffersen_conditional_coverage_test(series, 0.95);
            CAPTURE(n, x);
            CHECK(std::isfinite(result.statistic));
            CHECK(result.statistic >= 0.0);
            CHECK(result.p_value <= 1.0);
            CHECK(result.p_value >= 0.0);
            CHECK(result.rejected_at_5_percent == (result.p_value < 0.05));
            if (!independence.degenerate) {
                CHECK(independence.statistic >= 0.0);
                CHECK(conditional.statistic >= result.statistic);
                CHECK(conditional.statistic ==
                      Approx(independence.statistic + result.statistic).epsilon(1.0e-12));
            } else {
                CHECK(std::isnan(independence.statistic));
                CHECK(conditional.degenerate);
            }
        }
    }
}

TEST_CASE("Christoffersen independence test separates clustering from independence") {
    auto build = [](const std::vector<int> &flags) {
        std::vector<Real> returns_sample(flags.size(), 0.01);
        for (std::size_t i = 0; i < flags.size(); ++i) {
            returns_sample[i] = flags[i] ? -0.05 : 0.01;
        }
        return quantrisk::flag_violations(returns_sample, 0.02);
    };

    // Clustered: ten violations in a row, so a violation predicts another one.
    std::vector<int> clustered(200, 0);
    for (int i = 50; i < 60; ++i) {
        clustered[static_cast<std::size_t>(i)] = 1;
    }
    const auto clustered_series = build(clustered);
    const auto clustered_counts = quantrisk::transition_counts(clustered_series);
    CHECK(clustered_counts.estimable);
    CHECK(clustered_counts.pi11 > clustered_counts.pi01);
    const auto clustered_result = quantrisk::christoffersen_independence_test(clustered_series);
    CHECK(clustered_result.rejected_at_5_percent);
    CHECK(clustered_result.degrees_of_freedom == 1);

    // Genuinely independent violations: Bernoulli(5 %) draws from the core RNG.
    std::vector<int> random_flags(1000, 0);
    Rng rng(11);
    for (int &flag : random_flags) {
        flag = rng.uniform01() < 0.05 ? 1 : 0;
    }
    const auto random_series = build(random_flags);
    const auto random_result = quantrisk::christoffersen_independence_test(random_series);
    CHECK(random_result.statistic < clustered_result.statistic);
    CHECK_FALSE(random_result.rejected_at_5_percent);

    // Perfect alternation is maximal negative dependence, not independence:
    // pi_11 is exactly zero, and the test detects that too.
    std::vector<int> alternating(200, 0);
    for (int i = 0; i < 200; i += 2) {
        alternating[static_cast<std::size_t>(i)] = 1;
    }
    const auto alternating_counts = quantrisk::transition_counts(build(alternating));
    CHECK(alternating_counts.pi11 == Approx(0.0));
    CHECK(alternating_counts.pi01 == Approx(1.0));
}

TEST_CASE("Christoffersen conditional coverage adds the two components") {
    std::vector<Real> returns_sample(200, 0.01);
    for (std::size_t i = 0; i < 30; ++i) {
        returns_sample[i] = -0.05;
    }
    const auto series = quantrisk::flag_violations(returns_sample, 0.02);
    const auto independence = quantrisk::christoffersen_independence_test(series);
    const auto coverage = quantrisk::kupiec_pof_test(series, 0.95);
    const auto conditional = quantrisk::christoffersen_conditional_coverage_test(series, 0.95);
    CHECK(conditional.statistic ==
          Approx(independence.statistic + coverage.statistic).epsilon(1.0e-12));
    CHECK(conditional.degrees_of_freedom == 2);
    CHECK(conditional.critical_value_95 == Approx(5.991464547107982).epsilon(1.0e-9));
    // The reported critical value must be the quantile of the same distribution
    // the p-value came from, not a separately maintained table entry.
    CHECK(quantrisk::chi_square_sf(conditional.critical_value_95, 2) ==
          Approx(0.05).epsilon(1.0e-9));
}

TEST_CASE("a degenerate violation series is reported as not testable") {
    const std::vector<Real> no_violations(100, 0.01);
    const auto series = quantrisk::flag_violations(no_violations, 0.02);
    CHECK(series.exceptions == 0);
    const auto counts = quantrisk::transition_counts(series);
    CHECK_FALSE(counts.estimable);
    const auto independence = quantrisk::christoffersen_independence_test(series);
    CHECK(independence.degenerate);
    CHECK(std::isnan(independence.p_value));
    CHECK_THAT(independence.interpretation, Catch::Matchers::ContainsSubstring("not estimable"));
    const auto conditional = quantrisk::christoffersen_conditional_coverage_test(series, 0.95);
    CHECK(conditional.degenerate);
}

TEST_CASE("backtest_var produces the full Phase 5 output set") {
    const std::vector<Real> returns_sample = gaussian_sample(1000, 0.0, 0.02, 99);
    const Real level = risk::historical_var(returns_sample, 0.95).value;
    std::vector<Real> levels(returns_sample.size(), level);
    const auto report = quantrisk::backtest_var(returns_sample, levels, 0.95);
    CHECK(report.series.observations == 1000);
    CHECK(report.kupiec.test == "kupiec_pof");
    CHECK(report.independence.test == "christoffersen_independence");
    CHECK(report.conditional.test == "christoffersen_conditional_coverage");
    CHECK(report.kupiec.nominal_violation_rate == Approx(0.05));
    CHECK(report.series.violation_rate > 0.0);
    CHECK(report.series.violation_rate < 0.15);
    CHECK_FALSE(report.note.empty());
    CHECK_THROWS_AS(quantrisk::backtest_var(returns_sample, levels, 1.5), ValidationError);
    CHECK_THROWS_AS(quantrisk::flag_violations(returns_sample, std::vector<Real>{0.01}),
                    ValidationError);
}
