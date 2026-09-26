#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <algorithm>
#include <cmath>
#include <limits>
#include <numbers>
#include <vector>

#include "quantrisk/core/constants.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/math/normal.hpp"

using Catch::Approx;
using quantrisk::Real;

namespace {

constexpr Real kNan = std::numeric_limits<Real>::quiet_NaN();
constexpr Real kInf = std::numeric_limits<Real>::infinity();

} // namespace

TEST_CASE("normal_pdf is the analytic density and is even") {
    CHECK(quantrisk::normal_pdf(0.0) == Approx(0.3989422804014327).epsilon(1e-14));
    for (const Real x : {0.0, 0.5, 1.0, 2.0, 3.5, 8.0}) {
        CHECK(quantrisk::normal_pdf(x) == Approx(quantrisk::normal_pdf(-x)));
        CHECK(quantrisk::normal_pdf(x) > 0.0);
    }
    CHECK(quantrisk::normal_pdf(1.0) == Approx(0.24197072451914337).epsilon(1e-14));
    CHECK_THROWS_AS(quantrisk::normal_pdf(kNan), quantrisk::ValidationError);
    CHECK_THROWS_AS(quantrisk::normal_pdf(kInf), quantrisk::ValidationError);
}

TEST_CASE("normal_cdf matches closed-form anchors") {
    // Analytic values (Level 1): N(0) = 1/2 exactly, and the textbook values of
    // N(1), N(1.96) and N(6) to 16 significant digits.
    CHECK(quantrisk::normal_cdf(0.0) == 0.5);
    CHECK(quantrisk::normal_cdf(1.0) == Approx(0.8413447460685429).epsilon(1e-13));
    CHECK(quantrisk::normal_cdf(1.959963984540054) == Approx(0.975).epsilon(1e-13));
    CHECK(quantrisk::normal_cdf(6.0) == Approx(0.9999999990134123).epsilon(1e-12));

    // Reflection identity N(x) + N(-x) = 1.
    for (const Real x : {0.0, 0.25, 1.0, 2.0, 3.0, 4.0, 6.0}) {
        CHECK(quantrisk::normal_cdf(x) + quantrisk::normal_cdf(-x) == Approx(1.0).epsilon(1e-15));
    }

    // Monotonicity on a fixed grid.
    Real previous = -1.0;
    for (int i = -40; i <= 40; ++i) {
        const Real value = quantrisk::normal_cdf(static_cast<Real>(i) / 4.0);
        REQUIRE(value >= previous);
        REQUIRE(value >= 0.0);
        REQUIRE(value <= 1.0);
        previous = value;
    }

    CHECK_THROWS_AS(quantrisk::normal_cdf(kNan), quantrisk::ValidationError);
    CHECK_THROWS_AS(quantrisk::normal_cdf(kInf), quantrisk::ValidationError);
}

TEST_CASE("inverse_normal_cdf matches published quantiles") {
    CHECK(quantrisk::inverse_normal_cdf(0.5) == Approx(0.0).margin(1e-15));
    CHECK(quantrisk::inverse_normal_cdf(0.95) == Approx(1.6448536269514722).epsilon(1e-11));
    CHECK(quantrisk::inverse_normal_cdf(0.975) == Approx(1.959963984540054).epsilon(1e-11));
    CHECK(quantrisk::inverse_normal_cdf(0.99) == Approx(2.3263478740408408).epsilon(1e-11));
    CHECK(quantrisk::inverse_normal_cdf(0.01) == Approx(-2.3263478740408408).epsilon(1e-11));
}

TEST_CASE("inverse_normal_cdf round-trips through normal_cdf") {
    // Probabilities are dyadic (2^-k) so that `1 - p` is exactly representable.
    // Decimal literals such as 0.999999 are not, and comparing ppf(p) with
    // -ppf(1 - p) at 1e-12 would then measure the test's own rounding instead of
    // the implementation's accuracy.
    std::vector<Real> probabilities;
    for (int k = 2; k <= 20; ++k) {
        const Real p = std::ldexp(1.0, -k);
        probabilities.push_back(p);
        probabilities.push_back(1.0 - p);
    }

    for (const Real p : probabilities) {
        const Real x = quantrisk::inverse_normal_cdf(p);
        CAPTURE(p);
        CAPTURE(x);
        CHECK(quantrisk::normal_cdf(x) == Approx(p).epsilon(1e-11));
        CHECK(x == Approx(-quantrisk::inverse_normal_cdf(1.0 - p)).epsilon(1e-12));
    }

    // Strictly increasing in p.
    std::ranges::sort(probabilities);
    Real previous = -std::numeric_limits<Real>::infinity();
    for (const Real p : probabilities) {
        const Real x = quantrisk::inverse_normal_cdf(p);
        REQUIRE(x > previous);
        previous = x;
    }
}

TEST_CASE("inverse_normal_cdf rejects probabilities outside (0, 1)") {
    CHECK_THROWS_AS(quantrisk::inverse_normal_cdf(0.0), quantrisk::ValidationError);
    CHECK_THROWS_AS(quantrisk::inverse_normal_cdf(1.0), quantrisk::ValidationError);
    CHECK_THROWS_AS(quantrisk::inverse_normal_cdf(-0.1), quantrisk::ValidationError);
    CHECK_THROWS_AS(quantrisk::inverse_normal_cdf(1.2), quantrisk::ValidationError);
    CHECK_THROWS_AS(quantrisk::inverse_normal_cdf(kNan), quantrisk::ValidationError);
}

TEST_CASE("constants are consistent with <cmath>") {
    CHECK(quantrisk::kPi == Approx(std::numbers::pi).epsilon(1e-15));
    CHECK(quantrisk::kSqrtTwo == Approx(std::sqrt(2.0)).epsilon(1e-15));
    CHECK(quantrisk::kInvSqrtTwoPi == Approx(1.0 / std::sqrt(2.0 * quantrisk::kPi)).epsilon(1e-15));
    CHECK(quantrisk::kAnalyticTolerance > quantrisk::kMachineEpsilon);
}
