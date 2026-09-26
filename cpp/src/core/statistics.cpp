#include "quantrisk/core/statistics.hpp"

#include <algorithm>
#include <cmath>

#include "quantrisk/core/validation.hpp"

namespace quantrisk::stats {

Real sum_compensated(std::span<const Real> data) {
  // Neumaier (KBN) compensated summation; index order is fixed so results do
  // not depend on container iteration order.
  Real sum = 0.0;
  Real compensation = 0.0;
  for (const Real value : data) {
    const Real t = sum + value;
    if (std::abs(sum) >= std::abs(value)) {
      compensation += (sum - t) + value;
    } else {
      compensation += (value - t) + sum;
    }
    sum = t;
  }
  return sum + compensation;
}

Real mean(std::span<const Real> data) {
  if (data.empty()) {
    throw ValidationError("quantrisk: 'data' must be non-empty for mean()");
  }
  return sum_compensated(data) / static_cast<Real>(data.size());
}

Real sample_variance(std::span<const Real> data) {
  if (data.size() < 2) {
    throw ValidationError(
        "quantrisk: 'data' must contain at least 2 observations for "
        "sample_variance()");
  }
  const Real mu = mean(data);
  std::vector<Real> deviations(data.size());
  for (std::size_t i = 0; i < data.size(); ++i) {
    const Real d = data[i] - mu;
    deviations[i] = d * d;
  }
  return sum_compensated(deviations) / static_cast<Real>(data.size() - 1);
}

Real sample_stddev(std::span<const Real> data) {
  return std::sqrt(sample_variance(data));
}

Real quantile_linear(std::span<const Real> sorted_ascending, const Real p) {
  if (sorted_ascending.empty()) {
    throw ValidationError("quantrisk: 'sorted_ascending' must be non-empty");
  }
  require_probability(p, "p");
  const Real index = p * static_cast<Real>(sorted_ascending.size() - 1);
  const auto low = static_cast<std::size_t>(std::floor(index));
  const auto high = static_cast<std::size_t>(std::ceil(index));
  if (low == high) {
    return sorted_ascending[low];
  }
  const Real weight = index - static_cast<Real>(low);
  return sorted_ascending[low] * (1.0 - weight) +
         sorted_ascending[high] * weight;
}

Real quantile(std::vector<Real> data, const Real p) {
  std::ranges::sort(data);
  return quantile_linear(data, p);
}

Real mean_of_largest_sorted(std::span<const Real> sorted_ascending,
                            const Count k) {
  if (k <= 0) {
    detail::reject("k", "a positive count", detail::format_value(k));
  }
  if (static_cast<std::size_t>(k) > sorted_ascending.size()) {
    throw ValidationError(
        "quantrisk: 'k' exceeds the number of observations available");
  }
  const std::size_t start = sorted_ascending.size() - static_cast<std::size_t>(k);
  return mean(sorted_ascending.subspan(start, static_cast<std::size_t>(k)));
}

Real autocorrelation(std::span<const Real> data, const Count lag) {
  if (data.size() < 2) {
    throw ValidationError(
        "quantrisk: 'data' must contain at least 2 observations for "
        "autocorrelation()");
  }
  if (lag < 1 || lag >= static_cast<Count>(data.size())) {
    detail::reject("lag", "in [1, n-1]", detail::format_value(lag));
  }
  const Real mu = mean(data);
  std::vector<Real> numerator_terms(static_cast<std::size_t>(data.size() - lag));
  std::vector<Real> denominator_terms(data.size());
  for (std::size_t i = 0; i < data.size(); ++i) {
    denominator_terms[i] = (data[i] - mu) * (data[i] - mu);
  }
  for (std::size_t i = static_cast<std::size_t>(lag); i < data.size(); ++i) {
    numerator_terms[i - static_cast<std::size_t>(lag)] =
        (data[i] - mu) * (data[i - static_cast<std::size_t>(lag)] - mu);
  }
  const Real denominator = sum_compensated(denominator_terms);
  if (denominator == 0.0) {
    return 0.0;  // constant series: no correlation defined, report 0 not NaN
  }
  return sum_compensated(numerator_terms) / denominator;
}

Real standard_error_of_mean(std::span<const Real> data) {
  return sample_stddev(data) / std::sqrt(static_cast<Real>(data.size()));
}

}  // namespace quantrisk::stats
