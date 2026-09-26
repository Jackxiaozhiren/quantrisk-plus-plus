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
  // relative accuracy in the far tails, which matters for deep-OTM option
  // probabilities and for Gaussian tail risk measures.
  return 0.5 * std::erfc(-x / kSqrtTwo);
}

Real inverse_normal_cdf(const Real probability) {
  if (!(probability > 0.0 && probability < 1.0)) {
    detail::reject("probability", "strictly inside (0, 1)",
                   detail::format_value(probability));
  }

  // Acklam's rational approximation. Coefficients are the published ones for
  // double precision; the accuracy claim is checked against SciPy in
  // tests/python/test_normal_vs_scipy.py rather than assumed here.
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
  constexpr Real p_high = 1.0 - p_low;

  Real x = 0.0;
  if (probability < p_low) {
    const Real q = std::sqrt(-2.0 * std::log(probability));
    x = (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
        ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0);
  } else if (probability <= p_high) {
    const Real q = probability - 0.5;
    const Real r = q * q;
    x = (((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6) * q /
        (((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1.0);
  } else {
    const Real q = std::sqrt(-2.0 * std::log(1.0 - probability));
    x = -(((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
        ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0);
  }

  // One Halley correction using the residual of the forward CDF. This is what
  // makes Acklam's approximation usable at double precision. For extreme
  // probabilities (|x| beyond ~37) exp(x^2/2) overflows; there the unrefined
  // rational value is returned, which is still the best double available.
  const Real e = normal_cdf(x) - probability;
  const Real u = e * std::sqrt(kTwoPi) * std::exp(0.5 * x * x);  // e / phi(x)
  if (!std::isfinite(u)) {
    return x;
  }
  const Real correction = u / (1.0 + 0.5 * x * u);
  return x - correction;
}

}  // namespace quantrisk
