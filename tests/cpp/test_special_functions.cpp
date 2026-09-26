#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <cmath>
#include <limits>
#include <vector>

#include "quantrisk/core/constants.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/math/special.hpp"

using Catch::Approx;
using quantrisk::Real;

TEST_CASE("log_gamma matches known exact values and the recurrence") {
    CHECK(quantrisk::log_gamma(1.0) == Approx(0.0).margin(1.0e-13));
    CHECK(quantrisk::log_gamma(2.0) == Approx(0.0).margin(1.0e-13));
    CHECK(quantrisk::log_gamma(0.5) ==
          Approx(std::log(std::sqrt(quantrisk::kPi))).epsilon(1.0e-13));
    CHECK(quantrisk::log_gamma(1.5) ==
          Approx(std::log(0.5 * std::sqrt(quantrisk::kPi))).epsilon(1.0e-13));
    // Gamma(n + 1) = n! for small integers.
    CHECK(quantrisk::log_gamma(6.0) == Approx(std::log(120.0)).epsilon(1.0e-13));
    CHECK(quantrisk::log_gamma(13.0) == Approx(std::log(479001600.0)).epsilon(1.0e-13));
    // Reflection branch (x < 0.5) against a published value: Gamma(1/4) is
    // 3.6256099082219083119..., so log Gamma(1/4) = 1.28802252469801286...
    CHECK(quantrisk::log_gamma(0.25) == Approx(1.28802252469801286).epsilon(1.0e-13));
    // Log-convexity sanity: log Gamma grows between 1 and 3.
    CHECK(quantrisk::log_gamma(3.0) > quantrisk::log_gamma(2.0));
    CHECK_THROWS_AS(quantrisk::log_gamma(0.0), quantrisk::ValidationError);
    CHECK_THROWS_AS(quantrisk::log_gamma(-0.5), quantrisk::ValidationError);
}

TEST_CASE("incomplete gamma functions are complements and monotone") {
    for (const Real a : {0.5, 1.0, 2.5, 10.0}) {
        for (const Real x : {0.001, 0.1, 1.0, 5.0, 20.0, 60.0}) {
            const Real p = quantrisk::regularized_lower_incomplete_gamma(a, x);
            const Real q = quantrisk::regularized_upper_incomplete_gamma(a, x);
            CAPTURE(a, x);
            CHECK(p + q == Approx(1.0).epsilon(1.0e-12));
            CHECK(p >= 0.0);
            CHECK(p <= 1.0);
        }
    }
    // Monotone increasing in x for fixed a.
    Real previous = -1.0;
    for (const Real x : {0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0}) {
        const Real p = quantrisk::regularized_lower_incomplete_gamma(2.0, x);
        REQUIRE(p > previous);
        previous = p;
    }
    CHECK(quantrisk::regularized_upper_incomplete_gamma(1.0, 0.0) == Approx(1.0));
    // The lower branch must not obtain a tiny P as `1 - (1 - P)`: for a = 20 and
    // x = 0.01 the true value is ~4.1e-59, representable in double, and the
    // earlier formulation returned exactly 0. Live agreement with SciPy's digit
    // count is checked in tests/python/test_special_functions_vs_scipy.py.
    const Real tiny_p = quantrisk::regularized_lower_incomplete_gamma(20.0, 0.01);
    CHECK(tiny_p > 0.0);
    CHECK(tiny_p < 1.0e-50);
    CHECK(quantrisk::regularized_upper_incomplete_gamma(20.0, 0.01) == Approx(1.0));
}

TEST_CASE("chi-square survival function reproduces textbook critical values") {
    // Upper 5 % points and medians, generated live from scipy.stats.chi2.isf
    // (see tests/python/test_special_functions_vs_scipy.py for the same table as an
    // independent oracle check). A wrong dof in this table is exactly the kind
    // of transcription error the Python oracle test exists to catch.
    struct Point {
        int dof;
        Real x;
        Real sf;
    };
    const Point points[] = {
        {1, 3.8414588206941263, 0.05}, {2, 5.991464547107982, 0.05},
        {3, 7.814727903251182, 0.05},  {4, 9.487729036781158, 0.05},
        {5, 11.070497693516353, 0.05}, {10, 18.307038053275143, 0.05},
        {1, 0.4549364231195724, 0.5},  {2, 1.386294361119891, 0.5},
        {4, 3.3566939800333224, 0.5},  {5, 4.351460191095527, 0.5},
        {10, 9.341817765591967, 0.5},
    };
    for (const auto &point : points) {
        CAPTURE(point.dof, point.x, point.sf);
        CHECK(quantrisk::chi_square_sf(point.x, point.dof) == Approx(point.sf).epsilon(1.0e-6));
    }
    CHECK(quantrisk::chi_square_sf(0.0, 1) == Approx(1.0));
    CHECK(std::isnan(quantrisk::chi_square_sf(std::numeric_limits<Real>::quiet_NaN(), 1)));
    CHECK(quantrisk::chi_square_sf(100.0, 1) < 1.0e-20); // far tail, no underflow-to-1
}

TEST_CASE("chi_square_isf inverts the survival function") {
    for (const int dof : {1, 2, 3, 5, 10}) {
        for (const Real p : {0.5, 0.1, 0.05, 0.01}) {
            const Real q = quantrisk::chi_square_isf(p, dof);
            CAPTURE(dof, p);
            CHECK(quantrisk::chi_square_sf(q, dof) == Approx(p).epsilon(1.0e-8));
        }
    }
    // External anchors, from scipy.stats.chi2.isf.
    CHECK(quantrisk::chi_square_isf(0.05, 2) == Approx(5.991464547107982).epsilon(1.0e-10));
    CHECK(quantrisk::chi_square_isf(0.05, 5) == Approx(11.070497693516353).epsilon(1.0e-10));
    CHECK(quantrisk::chi_square_isf(0.01, 1) == Approx(6.634896601021214).epsilon(1.0e-10));
    CHECK_THROWS_AS(quantrisk::chi_square_isf(0.0, 1), quantrisk::ValidationError);
    CHECK_THROWS_AS(quantrisk::chi_square_isf(1.0, 1), quantrisk::ValidationError);
    CHECK_THROWS_AS(quantrisk::chi_square_isf(0.05, 0), quantrisk::ValidationError);
}

TEST_CASE("chi-square tail stays accurate far into the tail") {
    // A backtest can produce an extreme statistic; the p-value must not round to
    // zero (which would claim certainty) nor to one (which would hide the signal).
    // With 2 dof the survival function is exactly exp(-x/2), so the first row is a
    // closed-form anchor; the others are live scipy.stats.chi2.sf values and are
    // re-checked from Python in tests/python/test_special_functions_vs_scipy.py.
    const Real p = quantrisk::chi_square_sf(30.0, 2);
    CHECK(p > 0.0);
    CHECK(p == Approx(std::exp(-15.0)).epsilon(1.0e-12));
    CHECK(quantrisk::chi_square_sf(60.0, 2) == Approx(9.3576229688401635e-14).epsilon(1.0e-9));
    CHECK(quantrisk::chi_square_sf(100.0, 1) == Approx(1.5239706048320995e-23).epsilon(1.0e-9));
    CHECK(quantrisk::chi_square_sf(20.0, 10) == Approx(0.0292526880769611).epsilon(1.0e-9));
}

TEST_CASE("log binomial coefficient agrees with direct computation") {
    CHECK(quantrisk::log_binomial_coefficient(5, 2) == Approx(std::log(10.0)).epsilon(1.0e-13));
    // C(1000, 5) = 8250291250200 exactly (verified against Python's math.comb), so
    // this pins the path at a size where the factorials themselves would overflow.
    CHECK(quantrisk::log_binomial_coefficient(1000, 5) ==
          Approx(std::log(8250291250200.0)).epsilon(1.0e-12));
    // C(1000, 500) is the hardest case: ~300 digits, log = 689.4672615678512.
    CHECK(quantrisk::log_binomial_coefficient(1000, 500) ==
          Approx(689.4672615678512).epsilon(1.0e-13));
    CHECK(quantrisk::log_binomial_coefficient(50, 0) == Approx(0.0).margin(1.0e-13));
    CHECK(quantrisk::log_binomial_coefficient(50, 50) == Approx(0.0).margin(1.0e-13));
    CHECK_THROWS_AS(quantrisk::log_binomial_coefficient(5, 6), quantrisk::ValidationError);
}
