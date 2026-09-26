#pragma once

#include <span>
#include <string>
#include <vector>

#include "quantrisk/core/types.hpp"

namespace quantrisk {

/// Return definitions, frozen in docs/mathematical_specification.md §6:
///
///   arithmetic: R_t = (P_t - P_{t-1}) / P_{t-1}
///   log:        r_t = ln(P_t / P_{t-1})
///
/// They are *not* interchangeable: log returns are additive across time and
/// arithmetic returns are additive across assets. Which one feeds a risk number
/// is recorded in `RiskEstimate::note`.
namespace returns {

[[nodiscard]] std::vector<Real> arithmetic(std::span<const Real> prices);
[[nodiscard]] std::vector<Real> log_returns(std::span<const Real> prices);

} // namespace returns

namespace risk {

/// Loss convention (frozen): `L = -R`, so a positive number is a loss and
/// larger is worse.
///
/// VaR_alpha is the alpha-quantile of the loss distribution; ES_alpha is the
/// mean loss conditional on being at or beyond VaR. The quantile used for the
/// historical estimator is the linear-interpolated order statistic
/// (`stats::quantile_linear`); ES averages the `k = ceil(n (1 - alpha))` worst
/// observations, which is the estimator documented in `RiskEstimate::note` and
/// what the synthetic-data tests check against.
struct RiskEstimate {
    Real value = 0.0;
    Real confidence_level = 0.95;
    Count observations = 0;
    Real standard_error = 0.0; ///< 0 for point estimators; see the bootstrap module
    Real ci_low = 0.0;
    Real ci_high = 0.0;
    bool has_interval = false;
    std::string method;
    std::string note;
};

/// @name Point estimators from an observed return sample
/// @{
[[nodiscard]] RiskEstimate historical_var(std::span<const Real> returns_sample,
                                          Real confidence_level);
[[nodiscard]] RiskEstimate historical_es(std::span<const Real> returns_sample,
                                         Real confidence_level);
/// Gaussian (variance-covariance) closed forms:
/// `VaR = -mu + z_alpha sigma`, `ES = -mu + sigma phi(z_alpha) / (1 - alpha)`.
[[nodiscard]] RiskEstimate gaussian_var(std::span<const Real> returns_sample,
                                        Real confidence_level);
[[nodiscard]] RiskEstimate gaussian_es(std::span<const Real> returns_sample, Real confidence_level);
/// @}

/// @name Simulated profit and loss
/// Monte Carlo risk measures take a vector of simulated portfolio P&L (negative
/// = loss), produced for example by `gbm::terminal_prices_physical`.
/// @{
[[nodiscard]] RiskEstimate monte_carlo_var(std::span<const Real> simulated_pnl,
                                           Real confidence_level);
[[nodiscard]] RiskEstimate monte_carlo_es(std::span<const Real> simulated_pnl,
                                          Real confidence_level);
/// Standard error of a Monte Carlo quantile estimate through its density,
/// `sqrt(alpha (1 - alpha) / n) / f(x_alpha)`, estimated by finite differences
/// on the empirical CDF. Reported by the Monte Carlo estimators.
[[nodiscard]] Real quantile_standard_error(std::vector<Real> losses_sorted, Real confidence_level);
/// @}

/// Currency P&L of a weight vector against per-asset returns, one row per
/// scenario: `pnl_s = capital * sum_i w_i R_{s,i}`. Used by the risk and stress
/// engines; the covariance and optimisation algebra lives in `portfolio/`.
[[nodiscard]] std::vector<Real> linear_pnl(std::span<const Real> weights,
                                           std::span<const Real> returns_rows, Count assets,
                                           Real capital);

/// Sample covariance of a row-major `observations x assets` matrix, unbiased.
[[nodiscard]] std::vector<Real> sample_covariance(std::span<const Real> returns_rows, Count assets,
                                                  Count observations);

} // namespace risk
} // namespace quantrisk
