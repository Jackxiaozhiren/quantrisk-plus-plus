#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include <cmath>
#include <limits>
#include <numeric>
#include <random>
#include <vector>

#include "quantrisk/core/constants.hpp"
#include "quantrisk/core/rng.hpp"
#include "quantrisk/core/statistics.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/portfolio/covariance.hpp"
#include "quantrisk/risk/measures.hpp"

using Catch::Approx;
using quantrisk::Count;
using quantrisk::Real;
using quantrisk::portfolio::CovarianceEstimate;
namespace portfolio = quantrisk::portfolio;

namespace {

/// Row-major `observations x assets` matrix from per-asset series.
[[nodiscard]] std::vector<Real> interleave(const std::vector<std::vector<Real>> &columns) {
    const auto observations = static_cast<Count>(columns.at(0).size());
    const auto assets = static_cast<Count>(columns.size());
    std::vector<Real> flat(static_cast<std::size_t>(observations * assets));
    for (Count t = 0; t < observations; ++t) {
        for (Count i = 0; i < assets; ++i) {
            flat[static_cast<std::size_t>(t * assets + i)] =
                columns[static_cast<std::size_t>(i)][static_cast<std::size_t>(t)];
        }
    }
    return flat;
}

[[nodiscard]] Real at(const CovarianceEstimate &matrix, const Count row, const Count col) {
    return matrix.values[static_cast<std::size_t>(row * matrix.assets + col)];
}

struct Sample {
    std::vector<Real> values;
    Count assets;
    Count observations;
};

/// Deterministic correlated sample: asset 1 is asset 0 plus noise, asset 2 is a
/// scaled copy, so the matrix is well-conditioned but not diagonal.
[[nodiscard]] Sample correlated_sample(const Count observations, const Count assets,
                                       const quantrisk::Seed seed) {
    quantrisk::Rng rng(seed);
    std::vector<std::vector<Real>> columns(static_cast<std::size_t>(assets));
    for (Count t = 0; t < observations; ++t) {
        const Real common = rng.standard_normal();
        for (Count i = 0; i < assets; ++i) {
            const Real mixture = 0.6 * common + 0.4 * rng.standard_normal();
            columns[static_cast<std::size_t>(i)].push_back(mixture *
                                                           (1.0 + 0.2 * static_cast<Real>(i)));
        }
    }
    return Sample{interleave(columns), assets, observations};
}

} // namespace

TEST_CASE("sample covariance matches the definition on a hand-checked matrix") {
    // Three observations, two assets: computed by hand, not by the implementation.
    const std::vector<Real> rows = {0.01, -0.02, 0.03, 0.00, 0.01, -0.01};
    const auto estimate = portfolio::sample_covariance(rows, 2, 3);
    REQUIRE(estimate.assets == 2);
    REQUIRE(estimate.values.size() == 4);

    const std::vector<Real> asset0 = {0.01, 0.03, 0.01};
    const std::vector<Real> asset1 = {-0.02, 0.00, -0.01};
    CHECK(at(estimate, 0, 0) == Approx(quantrisk::stats::sample_variance(asset0)).margin(1.0e-18));
    CHECK(at(estimate, 1, 1) == Approx(quantrisk::stats::sample_variance(asset1)).margin(1.0e-18));

    const Real mean0 = quantrisk::stats::mean(asset0);
    const Real mean1 = quantrisk::stats::mean(asset1);
    Real cross = 0.0;
    for (std::size_t t = 0; t < asset0.size(); ++t) {
        cross += (asset0[t] - mean0) * (asset1[t] - mean1);
    }
    CHECK(at(estimate, 0, 1) == Approx(cross / 2.0).margin(1.0e-18));
    CHECK(at(estimate, 1, 0) == at(estimate, 0, 1)); // exactly, not to a tolerance
    CHECK(estimate.estimator == "sample");
    CHECK(estimate.positive_semidefinite);
}

TEST_CASE("sample covariance is invariant to translation and scales quadratically") {
    const auto base = correlated_sample(400, 4, 7);
    const auto plain = portfolio::sample_covariance(base.values, base.assets, base.observations);

    std::vector<Real> shifted = base.values;
    for (Count i = 0; i < base.assets; ++i) {
        for (Count t = 0; t < base.observations; ++t) {
            shifted[static_cast<std::size_t>(t * base.assets + i)] +=
                0.25 + 0.1 * static_cast<Real>(i);
        }
    }
    const auto moved = portfolio::sample_covariance(shifted, base.assets, base.observations);
    for (std::size_t k = 0; k < plain.values.size(); ++k) {
        CHECK(plain.values[k] == Approx(moved.values[k]).epsilon(1.0e-9));
    }

    std::vector<Real> doubled = base.values;
    for (auto &value : doubled) {
        value *= 2.0;
    }
    const auto scaled = portfolio::sample_covariance(doubled, base.assets, base.observations);
    for (std::size_t k = 0; k < plain.values.size(); ++k) {
        CHECK(scaled.values[k] == Approx(4.0 * plain.values[k]).epsilon(1.0e-9));
    }
}

TEST_CASE("a single asset reduces to the sample variance") {
    const std::vector<Real> one = {0.02, -0.01, 0.03, 0.00};
    const auto estimate = portfolio::sample_covariance(one, 1, 4);
    REQUIRE(estimate.values.size() == 1);
    CHECK(estimate.values[0] == Approx(quantrisk::stats::sample_variance(one)).margin(1.0e-20));
    CHECK(estimate.smallest_eigenvalue == Approx(estimate.values[0]).epsilon(1.0e-12));
}

TEST_CASE("a zero-variance asset gives an exactly zero row and column") {
    // The robustness case the Phase 6 gate asks for: a flat asset.
    const std::vector<Real> rows = {0.01, 0.05, -0.02, 0.05, 0.03, 0.05, 0.00, 0.05};
    const auto estimate = portfolio::sample_covariance(rows, 2, 4);
    CHECK(at(estimate, 1, 1) == Approx(0.0).margin(1.0e-20));
    CHECK(at(estimate, 0, 1) == Approx(0.0).margin(1.0e-20));
    CHECK(at(estimate, 1, 0) == Approx(0.0).margin(1.0e-20));
    // PSD with a zero eigenvalue: singular, so PSD-ness is not the problem, invertibility is.
    CHECK(estimate.positive_semidefinite);
    CHECK(estimate.smallest_eigenvalue == Approx(0.0).margin(1.0e-20));
    CHECK_THAT(estimate.note, Catch::Matchers::ContainsSubstring("singular"));
}

TEST_CASE("EWMA weights the newest observation most and degenerates correctly") {
    // T = 3, lambda = 0.5 -> raw weights (0.25, 0.5, 1) normalised by 1.75.
    const std::vector<Real> rows = {0.01, -0.02, 0.03, 0.00, 0.01, -0.01};
    const auto estimate = portfolio::ewma_covariance(rows, 2, 3, 0.5);
    const std::vector<Real> weight = {0.25 / 1.75, 0.5 / 1.75, 1.0 / 1.75};
    const std::vector<Real> asset0 = {0.01, 0.03, 0.01};
    const std::vector<Real> asset1 = {-0.02, 0.00, -0.01};

    Real expected = 0.0;
    for (std::size_t t = 0; t < weight.size(); ++t) {
        expected += weight[t] * asset0[t] * asset1[t]; // about zero: no mean removed
    }
    CHECK(at(estimate, 0, 1) == Approx(expected).margin(1.0e-18));
    CHECK(estimate.decay == 0.5);
    CHECK(estimate.half_life == Approx(1.0).margin(1.0e-15)); // halves each step
    CHECK(estimate.estimator == "ewma");
}

TEST_CASE("EWMA with lambda = 1 is the plain second moment about zero") {
    const std::vector<Real> rows = {0.01, -0.02, 0.03, 0.00, 0.01, -0.01};
    const auto estimate = portfolio::ewma_covariance(rows, 2, 3, 1.0);
    const std::vector<Real> asset0 = {0.01, 0.03, 0.01};
    const std::vector<Real> asset1 = {-0.02, 0.00, -0.01};
    Real expected = 0.0;
    for (std::size_t t = 0; t < asset0.size(); ++t) {
        expected += asset0[t] * asset1[t] / 3.0;
    }
    CHECK(at(estimate, 0, 1) == Approx(expected).margin(1.0e-18));
    CHECK(std::isinf(estimate.half_life));
    // And it differs from the centred estimator, which is the point of documenting
    // the zero-mean convention rather than leaving it implied.
    const auto centred = portfolio::sample_covariance(rows, 2, 3);
    CHECK(at(estimate, 0, 0) != Approx(at(centred, 0, 0)).margin(1.0e-12));
}

TEST_CASE("EWMA is not symmetric in the observation order") {
    // Reversing the rows must change the estimate: recency carries the weights, so
    // the documented "oldest first" layout is load-bearing and not cosmetic.
    const auto base = correlated_sample(120, 3, 11);
    const auto forward =
        portfolio::ewma_covariance(base.values, base.assets, base.observations, 0.94);
    std::vector<Real> reversed(base.values.size());
    for (Count t = 0; t < base.observations; ++t) {
        for (Count i = 0; i < base.assets; ++i) {
            reversed[static_cast<std::size_t>(t * base.assets + i)] =
                base.values[static_cast<std::size_t>((base.observations - 1 - t) * base.assets +
                                                     i)];
        }
    }
    const auto backward =
        portfolio::ewma_covariance(reversed, base.assets, base.observations, 0.94);
    CHECK(at(forward, 0, 0) != Approx(at(backward, 0, 0)).margin(1.0e-12));
}

TEST_CASE("Ledoit-Wolf shrinkage reproduces its own algebra on an independent base") {
    // The estimate is rebuilt here from the raw sample with plain loops, so the test
    // checks the shrinkage arithmetic rather than restating what Eigen returned.
    // Note the divisor: Ledoit & Wolf derive the intensity against S formed with T,
    // while `sample_covariance` is unbiased with T - 1. That difference is asserted
    // explicitly below instead of being papered over.
    const auto base = correlated_sample(300, 5, 13);
    const Count t_count = base.observations;
    const Count p = base.assets;
    const Real divisor = static_cast<Real>(t_count);

    std::vector<Real> mean(static_cast<std::size_t>(p), 0.0);
    for (Count t = 0; t < t_count; ++t) {
        for (Count i = 0; i < p; ++i) {
            mean[static_cast<std::size_t>(i)] +=
                base.values[static_cast<std::size_t>(t * p + i)] / divisor;
        }
    }
    std::vector<Real> ml(static_cast<std::size_t>(p * p), 0.0);
    for (Count t = 0; t < t_count; ++t) {
        for (Count i = 0; i < p; ++i) {
            for (Count j = 0; j < p; ++j) {
                ml[static_cast<std::size_t>(i * p + j)] +=
                    (base.values[static_cast<std::size_t>(t * p + i)] -
                     mean[static_cast<std::size_t>(i)]) *
                    (base.values[static_cast<std::size_t>(t * p + j)] -
                     mean[static_cast<std::size_t>(j)]) /
                    divisor;
            }
        }
    }
    Real trace = 0.0;
    for (Count i = 0; i < p; ++i) {
        trace += ml[static_cast<std::size_t>(i * p + i)];
    }
    const Real mu = trace / static_cast<Real>(p);

    const auto shrunk = portfolio::shrinkage_covariance(base.values, p, t_count);
    const Real delta = shrunk.shrinkage_intensity;
    REQUIRE(delta >= 0.0);
    REQUIRE(delta <= 1.0);
    REQUIRE(shrunk.estimator == "ledoit_wolf_shrinkage");
    CHECK(shrunk.target_scale == Approx(mu).epsilon(1.0e-12));

    for (Count i = 0; i < p; ++i) {
        for (Count j = 0; j < p; ++j) {
            CAPTURE(i, j);
            const Real expected = delta * (i == j ? mu : 0.0) +
                                  (1.0 - delta) * ml[static_cast<std::size_t>(i * p + j)];
            CHECK(at(shrunk, i, j) == Approx(expected).epsilon(1.0e-10).margin(1.0e-18));
            // Off-diagonals only ever shrink toward the target.
            if (i != j) {
                CHECK(std::abs(at(shrunk, i, j)) <=
                      std::abs(ml[static_cast<std::size_t>(i * p + j)]) + 1.0e-18);
            }
        }
    }
    // Trace of the shrunk matrix equals the trace of *its own* base, and the unbiased
    // estimator's trace differs by exactly the (T - 1) / T divisor factor.
    const auto unbiased = portfolio::sample_covariance(base.values, p, t_count);
    Real unbiased_trace = 0.0;
    Real shrunk_trace = 0.0;
    for (Count i = 0; i < p; ++i) {
        unbiased_trace += at(unbiased, i, i);
        shrunk_trace += at(shrunk, i, i);
    }
    CHECK(shrunk_trace == Approx(unbiased_trace * (divisor - 1.0) / divisor).epsilon(1.0e-10));
}

TEST_CASE("shrinkage repairs a rank-deficient estimate") {
    // 6 assets from 4 observations: the sample covariance cannot be full rank, the
    // shrunk one must be usable. This is the instability the gate asks to handle.
    const auto thin = correlated_sample(4, 6, 17);
    const auto sample = portfolio::sample_covariance(thin.values, thin.assets, thin.observations);
    const auto shrunk =
        portfolio::shrinkage_covariance(thin.values, thin.assets, thin.observations);
    // Rank deficiency shows up as a zero eigenvalue, which the relative PSD
    // tolerance still calls positive semidefinite: singular is not the same as
    // indefinite, and conflating them would hide the real problem.
    CHECK(sample.positive_semidefinite);
    CHECK(sample.smallest_eigenvalue <=
          portfolio::kPositiveSemidefiniteTolerance * sample.largest_eigenvalue);
    // A rank-deficient matrix has an exact zero eigenvalue mathematically, but the
    // measured one lands at ~1e-19 rather than 0, so the condition number is huge
    // and finite. Either answer says the same thing about inverting it.
    const Real conditioning = portfolio::condition_number(sample);
    const bool unusable = !std::isfinite(conditioning) || conditioning > 1.0e12;
    CHECK(unusable);
    CHECK(shrunk.smallest_eigenvalue > 0.0);
    CHECK(shrunk.positive_semidefinite);
    CHECK(shrunk.shrinkage_intensity > 0.0);
}

TEST_CASE("the spectrum and condition number describe the matrix honestly") {
    const std::vector<Real> identity = {1, 0, 0, 1};
    CovarianceEstimate unit;
    unit.assets = 2;
    unit.values = identity;
    unit.note = "hand built";
    CHECK(portfolio::condition_number(unit) == Approx(1.0).epsilon(1.0e-12));

    CovarianceEstimate stretched;
    stretched.assets = 2;
    stretched.values = {1.0, 0.0, 0.0, 1.0e-12};
    stretched.note = "hand built";
    CHECK(portfolio::condition_number(stretched) == Approx(1.0e12).epsilon(1.0e-4));

    CovarianceEstimate singular;
    singular.assets = 2;
    singular.values = {1.0, 1.0, 1.0, 1.0};
    singular.note = "hand built";
    CHECK(std::isinf(portfolio::condition_number(singular)));
    const auto spectrum = portfolio::eigenvalues(std::span<const Real>(singular.values), 2);
    REQUIRE(spectrum.size() == 2);
    CHECK(spectrum[0] == Approx(0.0).margin(1.0e-15));
    CHECK(spectrum[1] == Approx(2.0).epsilon(1.0e-12));
    CHECK(spectrum[0] <= spectrum[1]); // ascending
}

TEST_CASE("solve round-trips and refuses singular systems") {
    const auto base = correlated_sample(200, 3, 23);
    const auto sigma = portfolio::sample_covariance(base.values, base.assets, base.observations);
    const std::vector<Real> rhs = {1.0, 2.0, 3.0};
    const auto solution = portfolio::solve(std::span<const Real>(sigma.values), sigma.assets, rhs);
    REQUIRE(solution.solved);
    REQUIRE(solution.values.size() == 3);
    for (Count i = 0; i < sigma.assets; ++i) {
        Real product = 0.0;
        for (Count j = 0; j < sigma.assets; ++j) {
            product += at(sigma, i, j) * solution.values[static_cast<std::size_t>(j)];
        }
        CHECK(product == Approx(rhs[static_cast<std::size_t>(i)]).epsilon(1.0e-9));
    }

    const std::vector<Real> rows = {0.01, 0.05, -0.02, 0.05, 0.03, 0.05, 0.00, 0.05};
    const auto flat_asset = portfolio::sample_covariance(rows, 2, 4);
    const auto refused =
        portfolio::solve(std::span<const Real>(flat_asset.values), 2, std::vector<Real>{1.0, 1.0});
    CHECK_FALSE(refused.solved);
    CHECK(refused.values.size() == 2);
    CHECK(std::isnan(refused.values[0]));
    CHECK_FALSE(refused.note.empty());
}

TEST_CASE("covariance estimators validate their inputs") {
    const std::vector<Real> rows = {0.01, -0.02, 0.03, 0.00};
    CHECK_THROWS_AS(portfolio::sample_covariance(rows, 0, 2), quantrisk::ValidationError);
    CHECK_THROWS_AS(portfolio::sample_covariance(rows, 2, 1), quantrisk::ValidationError);
    CHECK_THROWS_AS(portfolio::sample_covariance(rows, 3, 2), quantrisk::ValidationError);
    CHECK_THROWS_AS(portfolio::ewma_covariance(rows, 2, 2, 0.0), quantrisk::ValidationError);
    CHECK_THROWS_AS(portfolio::ewma_covariance(rows, 2, 2, 1.5), quantrisk::ValidationError);
    CHECK_THROWS_AS(portfolio::shrinkage_covariance(rows, 2, 1), quantrisk::ValidationError);
    std::vector<Real> broken = rows;
    broken[1] = std::numeric_limits<Real>::quiet_NaN();
    CHECK_THROWS_AS(portfolio::sample_covariance(broken, 2, 2), quantrisk::ValidationError);
    std::vector<Real> unbounded = rows;
    unbounded[3] = std::numeric_limits<Real>::infinity();
    CHECK_THROWS_AS(portfolio::ewma_covariance(unbounded, 2, 2, 0.9), quantrisk::ValidationError);
}

TEST_CASE("the frozen risk::sample_covariance alias returns the same matrix") {
    const auto base = correlated_sample(150, 4, 29);
    const auto canonical =
        portfolio::sample_covariance(base.values, base.assets, base.observations);
    const auto alias =
        quantrisk::risk::sample_covariance(base.values, base.assets, base.observations);
    REQUIRE(alias.size() == canonical.values.size());
    for (std::size_t k = 0; k < alias.size(); ++k) {
        CHECK(alias[k] == Approx(canonical.values[k]).epsilon(1.0e-12));
    }
}

TEST_CASE("estimators are positive semidefinite by construction across seeds") {
    for (const Count assets : {1, 2, 5, 12}) {
        for (const Count observations : {2, 5, 40, 300}) {
            const auto base = correlated_sample(observations, assets, 1000 + observations);
            const std::vector<CovarianceEstimate> estimates = {
                portfolio::sample_covariance(base.values, assets, observations),
                portfolio::ewma_covariance(base.values, assets, observations, 0.94),
                portfolio::shrinkage_covariance(base.values, assets, observations)};
            for (const auto &estimate : estimates) {
                CAPTURE(assets, observations, estimate.estimator);
                CHECK(estimate.positive_semidefinite);
                // Symmetry must hold bit for bit: callers index the flat buffer directly.
                for (Count i = 0; i < assets; ++i) {
                    for (Count j = 0; j < i; ++j) {
                        CHECK(at(estimate, i, j) == at(estimate, j, i));
                    }
                }
            }
        }
    }
}

TEST_CASE("a numerically flat asset is refused rather than solved into nonsense") {
    // 200 identical observations do NOT produce an exactly-zero variance: the sample
    // mean of repeated values is itself rounded, so the entry lands near 1e-35 and
    // Cholesky reports a clean success on a matrix whose inverse is ~1e34. The
    // reciprocal-condition estimate is what stands between that and a reported
    // "optimal portfolio".
    std::vector<Real> rows;
    rows.reserve(400);
    for (Count t = 0; t < 200; ++t) {
        const Real varying = 0.01 + 0.002 * static_cast<Real>(t % 7);
        rows.push_back(varying);
        rows.push_back(0.01); // the flat asset
    }
    const auto estimate = portfolio::sample_covariance(rows, 2, 200);
    CHECK(estimate.positive_semidefinite); // zero eigenvalue, not a negative one
    CHECK(at(estimate, 1, 1) < 1.0e-20);
    CHECK(portfolio::condition_number(estimate) > portfolio::kSolveRefusalThreshold);

    const auto solution =
        portfolio::solve(std::span<const Real>(estimate.values), 2, std::vector<Real>{1.0, 1.0});
    CHECK_FALSE(solution.solved);
    CHECK(std::isnan(solution.values[1]));
    CHECK_THAT(solution.note, Catch::Matchers::ContainsSubstring("numerically singular"));

    // Shrinking the same sample makes it usable again, which is the documented way
    // out rather than a silent regularisation inside the solver.
    const auto shrunk = portfolio::shrinkage_covariance(rows, 2, 200);
    const auto repaired =
        portfolio::solve(std::span<const Real>(shrunk.values), 2, std::vector<Real>{1.0, 1.0});
    CHECK(repaired.solved);
    // No magnitude bound is asserted: a large weight on a near-flat asset is what a
    // shrunk variance legitimately implies. What must hold is that the vector
    // returned actually solves the system it claims to.
    REQUIRE(std::isfinite(repaired.values[0]));
    REQUIRE(std::isfinite(repaired.values[1]));
    const Real residual0 =
        at(shrunk, 0, 0) * repaired.values[0] + at(shrunk, 0, 1) * repaired.values[1];
    const Real residual1 =
        at(shrunk, 1, 0) * repaired.values[0] + at(shrunk, 1, 1) * repaired.values[1];
    CHECK(residual0 == Approx(1.0).epsilon(1.0e-12));
    CHECK(residual1 == Approx(1.0).epsilon(1.0e-12));
}
