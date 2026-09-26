#pragma once

#include "quantrisk/core/types.hpp"

namespace quantrisk {

/// Special functions needed by the risk engine's hypothesis tests. Implemented
/// here rather than pulled from a library because the backtest p-values are part
/// of the project's own statistical claims and must be reproducible and testable
/// against SciPy.
///
/// Accuracy strategy, frozen and validated in tests:
/// - `log_gamma`: Lanczos approximation with g = 7 and nine coefficients,
///   reflection formula for the region below 0.5.
/// - `regularized_lower_incomplete_gamma` (P(a, x)): power series for
///   `x < a + 1`, Lentz continued fraction for the complement otherwise, both
///   iterated to machine precision rather than to a fixed term count.
/// @{

/// Logarithm of the Gamma function, defined for `x > 0` and not a pole
/// (the sign of Gamma alternates between the negative poles, so a real
/// logarithm does not exist there).
[[nodiscard]] Real log_gamma(Real x);

/// P(a, x) = gamma(a, x) / Gamma(a), the regularized lower incomplete gamma.
[[nodiscard]] Real regularized_lower_incomplete_gamma(Real a, Real x);

/// Upper regularized incomplete gamma Q(a, x) = 1 - P(a, x), computed without
/// catastrophic cancellation for small tail probabilities.
[[nodiscard]] Real regularized_upper_incomplete_gamma(Real a, Real x);

/// Survival function of the chi-square distribution with `degrees_of_freedom`
/// degrees: `P(X > x) = Q(dof / 2, x / 2)`. Returns NaN for non-finite or
/// negative arguments.
[[nodiscard]] Real chi_square_sf(Real x, int degrees_of_freedom);

/// Upper-tail critical value: the `x` with `chi_square_sf(x, dof) ==
/// probability`, obtained by bracketing and bisecting the survival function
/// itself. Derived rather than tabulated so a test statistic and its critical
/// value can never disagree because one of them was mistyped.
[[nodiscard]] Real chi_square_isf(Real probability, int degrees_of_freedom);

/// Log of the binomial coefficient, evaluated through `log_gamma` so that large
/// sample sizes used in backtesting do not overflow.
[[nodiscard]] Real log_binomial_coefficient(int n, int k);

/// @}

} // namespace quantrisk
