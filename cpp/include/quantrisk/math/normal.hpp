#pragma once

#include "quantrisk/core/types.hpp"

namespace quantrisk {

/// Standard normal distribution functions, implemented from their definitions
/// (no library call is used as the model itself).
///
/// - `normal_pdf` is phi(x) = exp(-x^2/2) / sqrt(2*pi).
/// - `normal_cdf` is N(x) = 0.5 * erfc(-x / sqrt(2)); the complementary form
///   is used because it keeps relative accuracy deep in the left tail.
/// - `inverse_normal_cdf` is Acklam's rational approximation with one Halley
///   refinement step (source: Acklam 2010, "An improved approximation to the
///   quantile function of the normal distribution"). It is validated against
///   SciPy's `norm.ppf` in tests/python rather than being trusted by citation.
/// @{
Real normal_pdf(Real x);
Real normal_cdf(Real x);
Real inverse_normal_cdf(Real probability);
/// @}

} // namespace quantrisk
