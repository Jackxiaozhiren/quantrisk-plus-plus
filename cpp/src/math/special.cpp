#include "quantrisk/math/special.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <limits>

#include "quantrisk/core/constants.hpp"
#include "quantrisk/core/validation.hpp"

namespace quantrisk {

namespace {

constexpr Real kLanczosG = 7.0;

[[nodiscard]] const std::array<Real, 9> &lanczos_coefficients() {
    static const std::array<Real, 9> kCoefficients = {
        0.99999999999980993,  676.5203681218851,     -1259.1392167224028,
        771.32342877765313,   -176.61502916214059,   12.507343278686905,
        -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7};
    return kCoefficients;
}

/// Lanczos g = 7, n = 9 series A(z) for Gamma(z + 1); z > -1 is reachable here
/// because the reflection branch below only recurses to 1 - x with x >= 0.5.
[[nodiscard]] Real lanczos_sum(const Real z) {
    const auto &coefficient = lanczos_coefficients();
    Real sum = coefficient[0];
    for (std::size_t i = 1; i < coefficient.size(); ++i) {
        sum += coefficient[i] / (z + static_cast<Real>(i));
    }
    return sum;
}

/// Series representation of P(a, x), used when x < a + 1.
[[nodiscard]] Real gamma_series(Real a, Real x) {
    const Real tolerance = 3.0 * kMachineEpsilon;
    Real term = 1.0 / a;
    Real sum = term;
    for (int step = 0; step < 20000 && std::abs(term) > std::abs(sum) * tolerance; ++step) {
        term *= x / (a + static_cast<Real>(step + 1));
        sum += term;
    }
    return sum * std::exp(-x + a * std::log(x) - log_gamma(a));
}

/// Lentz continued fraction for Q(a, x), used when x >= a + 1.
[[nodiscard]] Real gamma_continued_fraction(Real a, Real x) {
    const Real tiny = std::numeric_limits<Real>::min();
    const Real tolerance = 3.0 * kMachineEpsilon;
    Real b = x + 1.0 - a;
    Real c = 1.0 / tiny;
    Real d = 1.0 / b;
    Real h = d;
    for (int step = 1; step <= 20000; ++step) {
        const Real an = -static_cast<Real>(step) * (static_cast<Real>(step) - a);
        b += 2.0;
        d = an * d + b;
        if (std::abs(d) < tiny) {
            d = tiny;
        }
        c = b + an / c;
        if (std::abs(c) < tiny) {
            c = tiny;
        }
        d = 1.0 / d;
        const Real delta = d * c;
        h *= delta;
        if (std::abs(delta - 1.0) < tolerance) {
            break;
        }
    }
    return std::exp(-x + a * std::log(x) - log_gamma(a)) * h;
}

/// Shared domain checks: Gamma(a) needs a > 0, and the integration range of the
/// incomplete gamma integral is [0, inf).
void require_gamma_domain(const Real a, const Real x) {
    if (!(a > 0.0)) {
        detail::reject("a", "strictly positive", detail::format_value(a));
    }
    if (std::isnan(x) || x < 0.0) {
        detail::reject("x", "non-negative", detail::format_value(x));
    }
}

} // namespace

Real log_gamma(const Real x) {
    require_finite(x, "x");
    if (!(x > 0.0)) {
        detail::reject("x",
                       "strictly positive (Gamma changes sign between its "
                       "negative poles, so log Gamma is not real there)",
                       detail::format_value(x));
    }
    if (x < 0.5) {
        // Reflection: Gamma(x) Gamma(1-x) = pi / sin(pi x), positive on (0, 1).
        return std::log(kPi / std::sin(kPi * x)) - log_gamma(1.0 - x);
    }
    // Standard g = 7 Lanczos form: Gamma(x) = sqrt(2 pi) * t^(x-1/2) e^-t * A(z)
    // with z = x - 1, t = z + g + 1/2 and A the coefficient series below.
    const Real z = x - 1.0;
    const Real t = z + kLanczosG + 0.5;
    return 0.5 * std::log(kTwoPi) + (z + 0.5) * std::log(t) - t + std::log(lanczos_sum(z));
}

/// P and Q are each evaluated from the representation that is *not* sitting at
/// one, so neither returns a small number as the difference of two values that
/// are already 1.0 in double precision. Defining one as `1 - other` reintroduces
/// exactly that cancellation: P(20, 0.01) = 4.0714e-59 came back as 0.0.
Real regularized_upper_incomplete_gamma(const Real a, const Real x) {
    require_gamma_domain(a, x);
    if (x == 0.0) {
        return 1.0;
    }
    if (x < a + 1.0) {
        return 1.0 - gamma_series(a, x);
    }
    return gamma_continued_fraction(a, x);
}

Real regularized_lower_incomplete_gamma(const Real a, const Real x) {
    require_gamma_domain(a, x);
    if (x == 0.0) {
        return 0.0;
    }
    if (x < a + 1.0) {
        return gamma_series(a, x);
    }
    return 1.0 - gamma_continued_fraction(a, x);
}

Real chi_square_sf(const Real x, const int degrees_of_freedom) {
    if (degrees_of_freedom <= 0) {
        detail::reject("degrees_of_freedom", "a positive integer",
                       detail::format_value(static_cast<Real>(degrees_of_freedom)));
    }
    if (std::isnan(x)) {
        return std::numeric_limits<Real>::quiet_NaN();
    }
    if (x <= 0.0) {
        return 1.0;
    }
    return regularized_upper_incomplete_gamma(0.5 * static_cast<Real>(degrees_of_freedom), 0.5 * x);
}

Real chi_square_isf(const Real probability, const int degrees_of_freedom) {
    if (degrees_of_freedom <= 0) {
        detail::reject("degrees_of_freedom", "a positive integer",
                       detail::format_value(static_cast<Real>(degrees_of_freedom)));
    }
    if (!(probability > 0.0 && probability < 1.0)) {
        detail::reject("probability", "strictly inside (0, 1)", detail::format_value(probability));
    }
    // The survival function is strictly decreasing, so grow the upper bracket
    // until it dips below the target and then bisect.
    Real low = 0.0;
    Real high = std::max(1.0, static_cast<Real>(degrees_of_freedom));
    for (int step = 0; step < 200 && chi_square_sf(high, degrees_of_freedom) >= probability;
         ++step) {
        low = high;
        high *= 2.0;
    }
    for (int step = 0; step < 400; ++step) {
        const Real mid = 0.5 * (low + high);
        if (mid <= low || mid >= high) {
            return mid; // No representable point left between the brackets.
        }
        if (chi_square_sf(mid, degrees_of_freedom) > probability) {
            low = mid;
        } else {
            high = mid;
        }
    }
    return 0.5 * (low + high);
}

Real log_binomial_coefficient(const int n, const int k) {
    if (n < 0 || k < 0 || k > n) {
        detail::reject("k", "satisfy 0 <= k <= n with n >= 0",
                       detail::format_value(static_cast<Real>(k)));
    }
    return log_gamma(static_cast<Real>(n) + 1.0) - log_gamma(static_cast<Real>(k) + 1.0) -
           log_gamma(static_cast<Real>(n - k) + 1.0);
}

} // namespace quantrisk
