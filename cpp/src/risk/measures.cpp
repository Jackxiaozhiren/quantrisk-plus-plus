#include "quantrisk/risk/measures.hpp"

#include <algorithm>
#include <cmath>
#include <numeric>

#include "quantrisk/core/constants.hpp"
#include "quantrisk/core/statistics.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/math/normal.hpp"
#include "quantrisk/portfolio/covariance.hpp"

namespace quantrisk::returns {

std::vector<Real> arithmetic(const std::span<const Real> prices) {
    if (prices.size() < 2) {
        throw ValidationError("quantrisk: arithmetic returns need at least 2 prices, got " +
                              detail::format_value(static_cast<Real>(prices.size())));
    }
    std::vector<Real> out(prices.size() - 1);
    for (std::size_t i = 1; i < prices.size(); ++i) {
        require_finite(prices[i], "price");
        require_finite(prices[i - 1], "previous price");
        require_positive(prices[i - 1], "previous price");
        out[i - 1] = (prices[i] - prices[i - 1]) / prices[i - 1];
    }
    return out;
}

std::vector<Real> log_returns(const std::span<const Real> prices) {
    if (prices.size() < 2) {
        throw ValidationError("quantrisk: log returns need at least 2 prices, got " +
                              detail::format_value(static_cast<Real>(prices.size())));
    }
    std::vector<Real> out(prices.size() - 1);
    for (std::size_t i = 1; i < prices.size(); ++i) {
        require_finite(prices[i], "price");
        require_finite(prices[i - 1], "previous price");
        require_positive(prices[i], "price");
        require_positive(prices[i - 1], "previous price");
        out[i - 1] = std::log(prices[i] / prices[i - 1]);
    }
    return out;
}

} // namespace quantrisk::returns

namespace quantrisk::risk {

namespace {

std::vector<Real> to_losses(std::span<const Real> returns_sample) {
    if (returns_sample.size() < 2) {
        throw ValidationError("quantrisk: a risk estimate needs at least 2 return observations");
    }
    std::vector<Real> losses(returns_sample.size());
    for (std::size_t i = 0; i < returns_sample.size(); ++i) {
        losses[i] = -returns_sample[i];
    }
    std::ranges::sort(losses);
    return losses;
}

Count tail_count(const Count observations, const Real confidence_level) {
    const Real expected = static_cast<Real>(observations) * (1.0 - confidence_level);
    return std::max<Count>(1, static_cast<Count>(std::ceil(expected - 1.0e-12)));
}

} // namespace

RiskEstimate historical_var(std::span<const Real> returns_sample, const Real confidence_level) {
    require_confidence_level(confidence_level, "confidence_level");
    const std::vector<Real> losses = to_losses(returns_sample);
    return RiskEstimate{
        .value = stats::quantile_linear(losses, confidence_level),
        .confidence_level = confidence_level,
        .observations = static_cast<Count>(losses.size()),
        .method = "historical_var",
        .note = "linear-interpolated empirical quantile of losses L = -R; no "
                "distributional assumption, no smoothing of the tail",
    };
}

RiskEstimate historical_es(std::span<const Real> returns_sample, const Real confidence_level) {
    require_confidence_level(confidence_level, "confidence_level");
    const std::vector<Real> losses = to_losses(returns_sample);
    const Count k = tail_count(static_cast<Count>(losses.size()), confidence_level);
    return RiskEstimate{
        .value = stats::mean_of_largest_sorted(losses, k),
        .confidence_level = confidence_level,
        .observations = static_cast<Count>(losses.size()),
        .method = "historical_es",
        .note = "mean of the ceil(n (1 - alpha)) worst losses; discrete tail, so the "
                "estimator is slightly upward-biased for small n",
    };
}

RiskEstimate gaussian_var(std::span<const Real> returns_sample, const Real confidence_level) {
    require_confidence_level(confidence_level, "confidence_level");
    if (returns_sample.size() < 2) {
        throw ValidationError("quantrisk: a risk estimate needs at least 2 return observations");
    }
    const Real mu = stats::mean(returns_sample);
    const Real sigma = stats::sample_stddev(returns_sample);
    const Real z = inverse_normal_cdf(confidence_level);
    return RiskEstimate{
        .value = -mu + z * sigma,
        .confidence_level = confidence_level,
        .observations = static_cast<Count>(returns_sample.size()),
        .method = "gaussian_var",
        .note = "-mu + z_alpha * s with sample mean and unbiased s; assumes "
                "normality, which the synthetic tests in Phase 5 quantify",
    };
}

RiskEstimate gaussian_es(std::span<const Real> returns_sample, const Real confidence_level) {
    require_confidence_level(confidence_level, "confidence_level");
    if (returns_sample.size() < 2) {
        throw ValidationError("quantrisk: a risk estimate needs at least 2 return observations");
    }
    const Real mu = stats::mean(returns_sample);
    const Real sigma = stats::sample_stddev(returns_sample);
    const Real z = inverse_normal_cdf(confidence_level);
    return RiskEstimate{
        .value = -mu + sigma * normal_pdf(z) / (1.0 - confidence_level),
        .confidence_level = confidence_level,
        .observations = static_cast<Count>(returns_sample.size()),
        .method = "gaussian_es",
        .note = "closed form -mu + s phi(z_alpha)/(1-alpha) for the normal tail",
    };
}

Real quantile_standard_error(std::vector<Real> losses_sorted, const Real confidence_level) {
    require_confidence_level(confidence_level, "confidence_level");
    require_positive_integer(static_cast<Count>(losses_sorted.size()), "losses_sorted");
    std::ranges::sort(losses_sorted); // caller may not have sorted
    const auto n = static_cast<Real>(losses_sorted.size());
    const Real index = confidence_level * (n - 1.0);
    const auto low = static_cast<std::size_t>(std::floor(index));
    const auto high = static_cast<std::size_t>(std::ceil(index));
    const Real quantile = low == high
                              ? losses_sorted[low]
                              : losses_sorted[low] * (1.0 - (index - static_cast<Real>(low))) +
                                    losses_sorted[high] * (index - static_cast<Real>(low));
    // Density at the quantile from the two neighbouring order statistics,
    // f(x) ~ (1/n) / (x_{i+1} - x_i); degenerate spacing (ties, e.g. many zeros in
    // an option P&L distribution) has no finite density and reports NaN instead of
    // a plausible-looking zero.
    const std::size_t j =
        std::min<std::size_t>(static_cast<std::size_t>(std::ceil(index)), losses_sorted.size() - 1);
    const std::size_t left = j == 0 ? 0 : j - 1;
    const std::size_t right = j + 1 >= losses_sorted.size() ? losses_sorted.size() - 1 : j + 1;
    const Real spacing =
        (losses_sorted[right] - losses_sorted[left]) / static_cast<Real>(right - left);
    if (spacing <= 0.0) {
        return std::numeric_limits<Real>::quiet_NaN();
    }
    const Real density = (1.0 / n) / spacing;
    (void)quantile;
    return std::sqrt(confidence_level * (1.0 - confidence_level) / n) / density;
}

RiskEstimate monte_carlo_var(std::span<const Real> simulated_pnl, const Real confidence_level) {
    require_confidence_level(confidence_level, "confidence_level");
    std::vector<Real> losses(simulated_pnl.size());
    for (std::size_t i = 0; i < simulated_pnl.size(); ++i) {
        losses[i] = -simulated_pnl[i];
    }
    // quantile_linear requires sorted input; without this the "quantile" was an
    // arbitrary element of the unsorted sample.
    std::ranges::sort(losses);
    const Real value = stats::quantile_linear(losses, confidence_level);
    const Real se = quantile_standard_error(losses, confidence_level);
    const Real z = inverse_normal_cdf(confidence_level);
    return RiskEstimate{
        .value = value,
        .confidence_level = confidence_level,
        .observations = static_cast<Count>(losses.size()),
        .standard_error = se,
        .ci_low = std::isfinite(se) ? value - z * se : 0.0,
        .ci_high = std::isfinite(se) ? value + z * se : 0.0,
        .has_interval = std::isfinite(se),
        .method = "monte_carlo_var",
        .note = std::isfinite(se) ? "empirical quantile of simulated losses; SE from the density "
                                    "at the quantile, sqrt(alpha(1-alpha)/n)/f(x_alpha)"
                                  : "empirical quantile of simulated losses; quantile SE "
                                    "undefined because the loss distribution has a flat spot at "
                                    "this level (ties), so no interval is reported",
    };
}

RiskEstimate monte_carlo_es(std::span<const Real> simulated_pnl, const Real confidence_level) {
    require_confidence_level(confidence_level, "confidence_level");
    std::vector<Real> losses(simulated_pnl.size());
    for (std::size_t i = 0; i < simulated_pnl.size(); ++i) {
        losses[i] = -simulated_pnl[i];
    }
    std::ranges::sort(losses);
    const Count k = tail_count(static_cast<Count>(losses.size()), confidence_level);
    return RiskEstimate{
        .value = stats::mean_of_largest_sorted(losses, k),
        .confidence_level = confidence_level,
        .observations = static_cast<Count>(losses.size()),
        .method = "monte_carlo_es",
        .note = "tail mean of simulated losses; the averaging over the worst "
                "ceil(n(1-alpha)) makes it far better conditioned than the quantile",
    };
}

std::vector<Real> linear_pnl(std::span<const Real> weights, std::span<const Real> returns_rows,
                             const Count assets, const Real capital) {
    if (assets <= 0) {
        detail::reject("assets", "a positive count", detail::format_value(assets));
    }
    if (static_cast<Count>(weights.size()) != assets) {
        throw ValidationError("quantrisk: weights must have exactly `assets` entries");
    }
    if (returns_rows.size() % static_cast<std::size_t>(assets) != 0) {
        throw ValidationError("quantrisk: the returns matrix must have as many columns as assets");
    }
    require_finite(capital, "capital");
    for (const Real weight : weights) {
        require_finite(weight, "weight");
    }
    const Count scenarios =
        static_cast<Count>(returns_rows.size() / static_cast<std::size_t>(assets));
    std::vector<Real> pnl(static_cast<std::size_t>(scenarios));
    for (Count s = 0; s < scenarios; ++s) {
        Real total = 0.0;
        for (Count i = 0; i < assets; ++i) {
            total += weights[static_cast<std::size_t>(i)] *
                     returns_rows[static_cast<std::size_t>(s * assets + i)];
        }
        pnl[static_cast<std::size_t>(s)] = capital * total;
    }
    return pnl;
}

std::vector<Real> sample_covariance(std::span<const Real> returns_rows, const Count assets,
                                    const Count observations) {
    // The canonical implementation lives in portfolio/covariance.cpp and is
    // Eigen-backed. This is the frozen Phase 5 entry point, kept as a thin view of
    // the same matrix so no formula exists twice in the core.
    return portfolio::sample_covariance(returns_rows, assets, observations).values;
}

} // namespace quantrisk::risk
