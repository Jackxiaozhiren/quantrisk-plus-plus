#include "quantrisk/stress/engine.hpp"

#include <algorithm>
#include <cmath>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/math/normal.hpp"
#include "quantrisk/portfolio/covariance.hpp"

namespace quantrisk::stress {

namespace {

/// Currency P&L per unit move, summed across every sensitivity that responds to a
/// move in the factor's own quoted units. This is the vector the variance is computed
/// against, and it is deliberately first order: gamma is a convexity correction to the
/// *mean*, and folding a squared term into a covariance would make the second moment
/// depend on the direction of the scenario, which is not what a covariance is.
///
/// The length comes from the factor count, not from any one block: a book whose only
/// sensitivity is vega has an empty `delta` vector, and sizing off it would return an
/// empty beta and quietly allocate zero risk to a position that carries real risk.
std::vector<Real> beta_of(const ExposureVector &exposures, std::size_t assets) {
    std::vector<Real> beta(assets, 0.0);
    auto add = [&beta](const std::vector<Real> &block) {
        for (std::size_t i = 0; i < block.size() && i < beta.size(); ++i) {
            beta[i] += block[i];
        }
    };
    add(exposures.delta);
    add(exposures.duration);
    add(exposures.vega);
    add(exposures.credit);
    return beta;
}

Real quadratic_form(const std::vector<Real> &beta, std::span<const Real> covariance) {
    const std::size_t assets = beta.size();
    Real total = 0.0;
    for (std::size_t i = 0; i < assets; ++i) {
        for (std::size_t j = 0; j < assets; ++j) {
            total += beta[i] * covariance[i * assets + j] * beta[j];
        }
    }
    return total;
}

/// Gaussian VaR under the project's frozen loss convention, `L = -P&L`:
///     VaR_alpha = E[L] + z_alpha * sigma = -mean_pnl + z_alpha * sigma.
/// The same closed form `risk::gaussian_var` derives from a sample, which the tests use
/// as the cross-check rather than trusting this one line.
Real gaussian_var_from(Real mean_pnl, Real sigma, Real confidence) {
    return -mean_pnl + inverse_normal_cdf(confidence) * sigma;
}

Real gaussian_es_from(Real mean_pnl, Real sigma, Real confidence) {
    const Real z = inverse_normal_cdf(confidence);
    return -mean_pnl + sigma * (normal_pdf(z) / (1.0 - confidence));
}

} // namespace

namespace detail {

Moves resolve_moves(const FactorSet &factors, const Scenario &scenario) {
    const std::size_t assets = static_cast<std::size_t>(factors.size());
    Moves moves{std::vector<Real>(assets, 0.0), std::vector<Real>(assets, 0.0)};
    for (const Shock &shock : scenario.shocks) {
        const std::size_t at = static_cast<std::size_t>(factors.index_of(shock.factor_id));
        const RiskFactor &factor = factors.factors[at];
        Real relative = shock.relative;
        Real absolute = shock.absolute;
        if (relative != 0.0 && absolute == 0.0) {
            if (factor.level == 0.0) {
                throw ValidationError("quantrisk: shock '" + shock.factor_id +
                                      "' is quoted relatively but the factor level is 0, "
                                      "so no absolute move can be derived for it");
            }
            absolute = relative * factor.level;
        } else if (absolute != 0.0 && relative == 0.0) {
            if (factor.level == 0.0) {
                throw ValidationError("quantrisk: shock '" + shock.factor_id +
                                      "' is quoted absolutely but the factor level is 0, "
                                      "so no relative move can be derived for it");
            }
            relative = absolute / factor.level;
        } else if (absolute != 0.0 && relative != 0.0) {
            const Real implied = relative * factor.level;
            if (std::abs(implied - absolute) > 1.0e-8 * std::max(Real{1.0}, std::abs(absolute))) {
                throw ValidationError("quantrisk: shock '" + shock.factor_id +
                                      "' states both units and they disagree (relative " +
                                      std::to_string(relative) + " implies absolute " +
                                      std::to_string(implied) + ", given " +
                                      std::to_string(absolute) + ")");
            }
        }
        moves.relative[at] += relative;
        moves.absolute[at] += absolute;
    }
    return moves;
}

FactorContribution contribute(const RiskFactor &factor, std::size_t at, Real relative,
                              Real absolute, const ExposureVector &exposures) {
    FactorContribution out;
    out.factor_id = factor.id;
    out.asset_class = factor.asset_class;
    out.relative_move = relative;
    out.absolute_move = absolute;
    const auto term = [&](const std::vector<Real> &block) -> Real {
        return at < block.size() ? block[at] : 0.0;
    };
    out.linear = term(exposures.delta) * relative;
    out.convexity = term(exposures.gamma) * relative * relative;
    out.rate = term(exposures.duration) * absolute;
    out.volatility = term(exposures.vega) * absolute;
    out.credit = term(exposures.credit) * absolute;
    return out;
}

} // namespace detail

namespace {

using detail::contribute;
using detail::Moves;
using detail::resolve_moves;

} // namespace

std::vector<Real> shift_covariance(std::span<const Real> covariance, Count assets,
                                   const DistributionShift &shift, std::string &note) {
    const std::size_t n = static_cast<std::size_t>(assets);
    if (static_cast<std::size_t>(covariance.size()) != n * n) {
        throw ValidationError("quantrisk: shift_covariance needs assets * assets entries");
    }
    std::vector<Real> sigma(covariance.begin(), covariance.end());
    std::vector<Real> deviation(n, 0.0);
    for (std::size_t i = 0; i < n; ++i) {
        const Real variance = sigma[i * n + i];
        if (variance < 0.0) {
            throw ValidationError("quantrisk: a covariance diagonal of " +
                                  std::to_string(variance) +
                                  " cannot be rescaled; the input is not a covariance");
        }
        deviation[i] = std::sqrt(variance);
    }
    if (shift.volatility_multiplier != 1.0) {
        if (shift.volatility_multiplier < 0.0) {
            throw ValidationError("quantrisk: a negative volatility multiplier rescales "
                                  "the scale but not the sign of reality");
        }
        // Every entry carries both standard deviations, so the whole matrix scales by
        // m^2 — leaving the off-diagonals alone would silently change the correlations
        // at the same time as the volatilities, which is a different scenario entirely.
        const Real squared = shift.volatility_multiplier * shift.volatility_multiplier;
        for (Real &entry : sigma) {
            entry *= squared;
        }
        for (Real &value : deviation) {
            value *= shift.volatility_multiplier;
        }
        note += "volatilities scaled by " + std::to_string(shift.volatility_multiplier) +
                " (every covariance entry by the square of that); ";
    }
    if (shift.correlation_increment != 0.0) {
        std::size_t clipped = 0;
        for (std::size_t i = 0; i < n; ++i) {
            for (std::size_t j = 0; j < n; ++j) {
                if (i == j || deviation[i] == 0.0 || deviation[j] == 0.0) {
                    continue;
                }
                Real correlation = sigma[i * n + j] / (deviation[i] * deviation[j]);
                correlation += shift.correlation_increment;
                if (correlation > 1.0 || correlation < -1.0) {
                    ++clipped;
                    correlation = std::clamp(correlation, -1.0, 1.0);
                }
                sigma[i * n + j] = correlation * deviation[i] * deviation[j];
            }
        }
        note += "correlation increment " + std::to_string(shift.correlation_increment) +
                " applied to off-diagonals" +
                (clipped > 0 ? " with " + std::to_string(clipped) + " pair(s) clipped"
                             : ", no clipping needed") +
                "; ";
        // Clipping restores the unit diagonal but does not guarantee a valid correlation
        // matrix: enough pairwise lift makes the nearest correlation matrix further away.
        // The smallest eigenvalue is reported rather than repaired, because how far the
        // scenario went invalid is itself the finding.
        const auto spectrum = portfolio::eigenvalues(sigma, assets);
        if (!spectrum.empty() && spectrum.front() < -1.0e-12) {
            note += "WARNING the shifted matrix is NOT positive semidefinite (smallest "
                    "eigenvalue " +
                    std::to_string(spectrum.front()) +
                    "); the scenario asks for a dependence structure that cannot exist, "
                    "and no projection has been applied to hide it; ";
        }
    }
    if (note.empty()) {
        note = "no distribution shift requested; ";
    }
    return sigma;
}

ScenarioResult run_scenario(const Portfolio &portfolio, const Scenario &scenario,
                            std::span<const Real> factor_move_covariance, Real confidence) {
    if (confidence <= 0.0 || confidence >= 1.0) {
        throw ValidationError("quantrisk: a stress confidence level of " +
                              std::to_string(confidence) + " is outside (0, 1)");
    }
    const ExposureVector aggregate = portfolio.aggregate();
    const Moves moves = resolve_moves(portfolio.factors, scenario);
    const std::size_t assets = static_cast<std::size_t>(portfolio.factors.size());

    ScenarioResult result;
    result.scenario_name = scenario.name;
    result.kind = scenario.kind;
    result.assumptions = scenario.assumptions;
    result.horizon = scenario.horizon;
    if (scenario.assumptions.empty()) {
        result.note += "the scenario carries no stated assumptions, so its horizon and "
                       "provenance are unknown and the P&L should not be read as either; ";
    }
    if (scenario.horizon <= 0.0) {
        result.note += "no horizon is set on the scenario; ";
    }

    result.by_factor.reserve(assets);
    for (std::size_t i = 0; i < assets; ++i) {
        const FactorContribution part = contribute(portfolio.factors.factors[i], i,
                                                   moves.relative[i], moves.absolute[i], aggregate);
        result.pnl_change += part.total();
        result.by_factor.push_back(part);
    }

    result.by_position.reserve(portfolio.positions.size());
    for (const Position &position : portfolio.positions) {
        Real each = 0.0;
        for (std::size_t i = 0; i < assets; ++i) {
            each += contribute(portfolio.factors.factors[i], i, moves.relative[i],
                               moves.absolute[i], position.exposures)
                        .total();
        }
        result.by_position.push_back(PositionContribution{position.name, each});
    }

    // Both decompositions are sums of the same terms in a different order, so any
    // non-zero residual is an implementation error, never model error.
    Real factor_sum = 0.0;
    for (const FactorContribution &part : result.by_factor) {
        factor_sum += part.total();
    }
    Real position_sum = 0.0;
    for (const PositionContribution &part : result.by_position) {
        position_sum += part.pnl;
    }
    result.factor_attribution_residual = factor_sum - result.pnl_change;
    result.position_attribution_residual = position_sum - result.pnl_change;

    if (factor_move_covariance.empty()) {
        result.note += "no factor-move covariance supplied, so VaR/ES/volatility are not "
                       "reported rather than assumed to be unchanged; ";
        return result;
    }

    std::string shift_note;
    const std::vector<Real> stressed = shift_covariance(
        factor_move_covariance, portfolio.factors.size(), scenario.distribution, shift_note);
    result.note += shift_note;

    const std::vector<Real> beta = beta_of(aggregate, assets);
    const Real base_variance = quadratic_form(beta, factor_move_covariance);
    const Real stressed_variance = quadratic_form(beta, stressed);
    if (base_variance < 0.0 || stressed_variance < 0.0) {
        result.note += "a supplied covariance produced a negative portfolio variance, so "
                       "the risk metrics are left unset instead of being reported from a "
                       "negative standard deviation; ";
        return result;
    }
    const Real base_sigma = std::sqrt(std::max(Real{0.0}, base_variance));
    const Real stressed_sigma = std::sqrt(std::max(Real{0.0}, stressed_variance));

    result.has_risk_metrics = true;
    result.base_volatility = base_sigma;
    result.stressed_volatility = stressed_sigma;
    result.volatility_change = stressed_sigma - base_sigma;
    result.base_var = gaussian_var_from(0.0, base_sigma, confidence);
    result.stressed_var = gaussian_var_from(result.pnl_change, stressed_sigma, confidence);
    result.base_es = gaussian_es_from(0.0, base_sigma, confidence);
    result.stressed_es = gaussian_es_from(result.pnl_change, stressed_sigma, confidence);
    result.var_change = result.stressed_var - result.base_var;
    result.es_change = result.stressed_es - result.base_es;
    // The telescoping split: the level leg holds the base dispersion and moves the mean,
    // the distribution leg holds the shocked mean and moves the dispersion. Exact because
    // the Gaussian quantile is affine in (mean, sigma) — it would not telescope for a
    // historical or Cornish-Fisher estimator, and this is stated rather than glossed.
    result.var_change_from_level =
        gaussian_var_from(result.pnl_change, base_sigma, confidence) - result.base_var;
    result.var_change_from_distribution =
        result.stressed_var - gaussian_var_from(result.pnl_change, base_sigma, confidence);
    result.var_decomposition_residual =
        result.var_change_from_level + result.var_change_from_distribution - result.var_change;

    // Euler allocation of the stressed VaR across positions: with VaR = z * sqrt(b'Sb)
    // and b = sum of the position betas, c_p = b_p'(Sb) / (b'Sb) * VaR sums to VaR.
    if (stressed_sigma > 0.0) {
        std::vector<Real> stressed_beta_times_sigma(assets, 0.0);
        for (std::size_t i = 0; i < assets; ++i) {
            for (std::size_t j = 0; j < assets; ++j) {
                stressed_beta_times_sigma[i] += stressed[i * assets + j] * beta[j];
            }
        }
        const Real denominator = stressed_variance;
        Real allocated = 0.0;
        for (const Position &position : portfolio.positions) {
            const std::vector<Real> position_beta = beta_of(position.exposures, assets);
            Real inner = 0.0;
            for (std::size_t i = 0; i < assets; ++i) {
                inner += position_beta[i] * stressed_beta_times_sigma[i];
            }
            const Real component = inner / denominator * result.stressed_var;
            allocated += component;
            result.var_components_stressed.push_back({position.name, component});
        }
        result.var_component_residual = allocated - result.stressed_var;
    }
    return result;
}

} // namespace quantrisk::stress
