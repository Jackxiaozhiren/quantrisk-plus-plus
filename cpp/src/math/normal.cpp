#include "quantrisk/math/normal.hpp"

#include <cmath>

#include "quantrisk/core/constants.hpp"
#include "quantrisk/core/validation.hpp"

namespace quantrisk {

Real normal_pdf(const Real x) {
    require_finite(x, "x");
    return kInvSqrtTwoPi * std::exp(-0.5 * x * x);
}

Real normal_cdf(const Real x) {
    require_finite(x, "x");
    // N(x) = 0.5 * erfc(-x / sqrt(2)). Using erfc rather than erf keeps
    // relative accuracy deep in the left tail, which matters for deep-OTM option
    // probabilities and for Gaussian tail risk measures.
    return 0.5 * std::erfc(-x / kSqrtTwo);
}

namespace detail {

/// Acklam's rational approximation with one Halley refinement, evaluated only
/// for `0 < probability <= 0.5` (the lower half of the distribution).
///
/// Coefficients are the published double-precision values from Acklam (2010),
/// "An improved approximation to the quantile function of the normal
/// distribution". Accuracy is not taken on citation: it is checked against
/// SciPy in tests/python/test_normal_vs_scipy.py.
///
/// Restricting the branch to the lower half is a numerical requirement, not a
/// simplification. In the upper half the refinement residual would be computed
/// as `N(x) - p` with both operands within 1e-6 of 1.0; that cancellation
/// costs roughly 1e-16 / phi(4.76) ~= 6e-12 of absolute accuracy in x, and it
/// breaks the exact odd symmetry Q(p) = -Q(1-p) that the upper branch is
/// supposed to satisfy.
Real inverse_normal_cdf_lower_half(const Real probability) {
    constexpr Real a1 = -3.969683028665376e+01;
    constexpr Real a2 = 2.209460984245205e+02;
    constexpr Real a3 = -2.759285104469687e+02;
    constexpr Real a4 = 1.383577518672690e+02;
    constexpr Real a5 = -3.066479806614716e+01;
    constexpr Real a6 = 2.506628277459239e+00;

    constexpr Real b1 = -5.447609879822406e+01;
    constexpr Real b2 = 1.615858368580409e+02;
    constexpr Real b3 = -1.556989798598866e+02;
    constexpr Real b4 = 6.680131188771972e+01;
    constexpr Real b5 = -1.328068155288572e+01;

    constexpr Real c1 = -7.784894002430293e-03;
    constexpr Real c2 = -3.223964580411365e-01;
    constexpr Real c3 = -2.400758277161838e+00;
    constexpr Real c4 = -2.549732539343734e+00;
    constexpr Real c5 = 4.374664141464968e+00;
    constexpr Real c6 = 2.938163982698783e+00;

    constexpr Real d1 = 7.784695709041462e-03;
    constexpr Real d2 = 3.224671290700398e-01;
    constexpr Real d3 = 2.445134137142996e+00;
    constexpr Real d4 = 3.754408661907416e+00;

    constexpr Real p_low = 0.02425;

    Real x = 0.0;
    if (probability < p_low) {
        const Real q = std::sqrt(-2.0 * std::log(probability));
        x = (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
            ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0);
    } else {
        const Real q = probability - 0.5;
        const Real r = q * q;
        x = (((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6) * q /
            (((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1.0);
    }

    // One Halley correction: x <- x - (N(x) - p) / phi(x) evaluated with the
    // Halley denominator. If exp(x^2 / 2) overflows (p below ~1e-315) the
    // unrefined rational value is the best double available.
    const Real e = normal_cdf(x) - probability;
    const Real u = e * std::sqrt(kTwoPi) * std::exp(0.5 * x * x); // e / phi(x)
    if (!std::isfinite(u)) {
        return x;
    }
    return x - u / (1.0 + 0.5 * x * u);
}

} // namespace detail

Real inverse_normal_cdf(const Real probability) {
    if (!(probability > 0.0 && probability < 1.0)) {
        detail::reject("probability", "strictly inside (0, 1)", detail::format_value(probability));
    }
    // Q is odd about p = 1/2: mirror the upper half into the lower one so the
    // refinement never suffers cancellation near 1.0.
    if (probability > 0.5) {
        return -detail::inverse_normal_cdf_lower_half(1.0 - probability);
    }
    return detail::inverse_normal_cdf_lower_half(probability);
}

} // namespace quantrisk
