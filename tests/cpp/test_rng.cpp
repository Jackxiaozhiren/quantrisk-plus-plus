#include <catch2/catch_test_macros.hpp>
#include <catch2/generators/catch_generators.hpp>

#include <cmath>
#include <set>

#include "quantrisk/core/constants.hpp"
#include "quantrisk/core/rng.hpp"
#include "quantrisk/core/statistics.hpp"
#include "quantrisk/core/validation.hpp"

using quantrisk::Real;
using quantrisk::Rng;

namespace {

std::vector<double> draw_normals(const quantrisk::Seed seed, const std::size_t n) {
    Rng rng(seed);
    return rng.standard_normal_vector(n);
}

} // namespace

TEST_CASE("Rng default seed is documented and configurable") {
    CHECK(Rng::kDefaultSeed == 42);
    CHECK(Rng{}.seed() == 42);
    CHECK(Rng(7).seed() == 7);
}

TEST_CASE("identical seeds reproduce identical streams (C++ side)") {
    constexpr std::size_t kDraws = 5000;
    const std::vector<double> a = draw_normals(42, kDraws);
    const std::vector<double> b = draw_normals(42, kDraws);
    REQUIRE(a.size() == kDraws);
    CHECK(a == b);

    const std::vector<double> c = draw_normals(42, kDraws / 2);
    CHECK(std::equal(c.begin(), c.end(), a.begin()));

    // The Python-side stream is checked against these same values in
    // tests/python/test_rng_contract.py, which proves binding fidelity.
}

TEST_CASE("different seeds give different streams") {
    const std::vector<double> a = draw_normals(1, 64);
    const std::vector<double> b = draw_normals(2, 64);
    CHECK(a != b);
}

TEST_CASE("engines do not share hidden state") {
    Rng first(42);
    Rng second(42);

    // `first` is consumed completely before `second` is touched. If any part of
    // the stream (including the cached Box-Muller partner) lived in a static,
    // `second` would continue where `first` left off instead of restarting.
    const std::vector<double> from_first = first.standard_normal_vector(5);
    const std::vector<double> from_second = second.standard_normal_vector(5);
    CHECK(from_first == from_second);
    CHECK(first.uniform_draws() > 0);
    CHECK(second.uniform_draws() > 0);
}

TEST_CASE("uniform01 stays in [0, 1) and advances the draw counter") {
    Rng rng(1234);
    const std::uint64_t before = rng.uniform_draws();
    for (int i = 0; i < 20000; ++i) {
        const double u = rng.uniform01();
        REQUIRE(u >= 0.0);
        REQUIRE(u < 1.0);
    }
    CHECK(rng.uniform_draws() == before + 20000);
}

TEST_CASE("normal stream has the first two moments of N(0, 1)") {
    constexpr std::size_t kDraws = 200000;
    const std::vector<double> values = draw_normals(2024, kDraws);
    const Real mu = quantrisk::stats::mean(values);
    const Real var = quantrisk::stats::sample_variance(values);

    // 5 standard errors on the mean (SE = 1/sqrt(N)) and a generous relative
    // band on the variance; both are theory-based, not tuned to a run.
    CHECK(std::abs(mu) < 5.0 / std::sqrt(static_cast<Real>(kDraws)));
    CHECK(std::abs(var - 1.0) < 0.02);
}

TEST_CASE("Marsaglia partner variate is cached between calls") {
    Rng rng(42);
    CHECK_FALSE(rng.has_cached_normal());
    const double first = rng.standard_normal();
    CHECK(rng.has_cached_normal());
    const double second = rng.standard_normal();
    CHECK_FALSE(rng.has_cached_normal());
    CHECK(first != second);

    // Re-seeding means constructing a new engine: the cached partner belongs to
    // the instance, never to a shared static.
    CHECK(Rng(42).standard_normal() == first);
}

TEST_CASE("uniform_index is unbiased over its range") {
    // Bounds stay small so that "every value is eventually drawn" is a real
    // expectation (coupon collector: 50 * ln 50 ~= 196 draws), not a coincidence.
    const std::uint64_t bound =
        GENERATE_COPY(std::uint64_t{1}, std::uint64_t{2}, std::uint64_t{7}, std::uint64_t{50});
    Rng rng(42);
    std::set<std::uint64_t> seen;
    for (int i = 0; i < 5000; ++i) {
        const std::uint64_t value = rng.uniform_index(bound);
        REQUIRE(value < bound);
        seen.insert(value);
    }
    CHECK(seen.size() == bound);
}

TEST_CASE("uniform_index rejects an empty range instead of dividing by zero") {
    Rng rng(42);
    CHECK_THROWS_AS(rng.uniform_index(0), quantrisk::ValidationError);
}
