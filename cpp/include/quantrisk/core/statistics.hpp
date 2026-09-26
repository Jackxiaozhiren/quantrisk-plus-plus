#pragma once

#include <cstddef>
#include <span>
#include <vector>

#include "quantrisk/core/types.hpp"

namespace quantrisk {

/// Statistics helpers shared by Monte Carlo error estimation and the risk
/// engine. All estimators use compensated summation and a documented,
/// fixed order so that repeated runs are bit-reproducible.
namespace stats {

/// Neumaier compensated sum, evaluated in index order.
Real sum_compensated(std::span<const Real> data);

/// Arithmetic mean: `sum_compensated(data) / n`.
/// Throws `ValidationError` on empty input.
Real mean(std::span<const Real> data);

/// Unbiased sample variance (`/(n-1)`), two-pass around `mean`.
/// Throws `ValidationError` if `n < 2`.
Real sample_variance(std::span<const Real> data);

/// Square root of `sample_variance`.
Real sample_stddev(std::span<const Real> data);

/// Linear-interpolated quantile (matches NumPy's default `method="linear"`)
/// of data that the caller has already sorted ascending.
/// `p` is in [0, 1]; requires `n >= 1`.
Real quantile_linear(std::span<const Real> sorted_ascending, Real p);

/// Convenience: sort a copy and return the linear-interpolated quantile.
Real quantile(std::vector<Real> data, Real p);

/// Mean of the `k` largest entries of ascending-sorted data (`k >= 1`),
/// used by expected shortfall / CVaR tail averaging.
Real mean_of_largest_sorted(std::span<const Real> sorted_ascending, Count k);

/// Lag-`lag` autocorrelation with the mean subtracted and the full-sample
/// variance used as denominator (the "biased"/Wallis estimator, which is the
/// one Christoffersen's independence test is stated for).
/// Requires `n >= 2` and `1 <= lag < n`.
Real autocorrelation(std::span<const Real> data, Count lag);

/// Standard error of a mean over `n` i.i.d. sample values: `s / sqrt(n)`.
Real standard_error_of_mean(std::span<const Real> data);

}  // namespace stats
}  // namespace quantrisk
