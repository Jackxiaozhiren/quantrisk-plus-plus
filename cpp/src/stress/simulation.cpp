#include "quantrisk/stress/simulation.hpp"

#include <Eigen/Dense>
#include <algorithm>
#include <cmath>
#include <limits>

#include "quantrisk/core/rng.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/stress/scenario.hpp"

namespace quantrisk::stress {

namespace {

using detail::contribute;
using detail::Moves;
using detail::resolve_moves;

using Matrix = Eigen::Matrix<Real, Eigen::Dynamic, Eigen::Dynamic>;

/// Neumaier-compensated mean and unbiased standard deviation.
///
/// Scenario P&L vectors are long and can be dominated by a few large outcomes, which is
/// exactly where naive two-pass variance loses digits. The summation rule matches the
/// rest of the core for the same reason.
void mean_and_sd(const std::vector<Real> &values, Real &mean, Real &sd) {
    if (values.empty()) {
        throw ValidationError("quantrisk: no scenarios to summarise");
    }
    Real sum = 0.0;
    Real compensation = 0.0;
    for (const Real value : values) {
        const Real step = sum + value;
        if (std::abs(sum) >= std::abs(value)) {
            compensation += (sum - step) + value;
        } else {
            compensation += (value - step) + sum;
        }
        sum = step;
    }
    mean = (sum + compensation) / static_cast<Real>(values.size());
    Real squares = 0.0;
    for (const Real value : values) {
        const Real deviation = value - mean;
        squares += deviation * deviation;
    }
    sd = values.size() > 1 ? std::sqrt(squares / static_cast<Real>(values.size() - 1)) : 0.0;
}

/// Accumulate the per-factor and per-position breakdown of one scenario set.
struct Accumulator {
    std::vector<Real> factor_mean;
    std::vector<Real> factor_worst;
    std::vector<Real> position_mean;

    Accumulator(const FactorSet &factors, const Portfolio &portfolio)
        : factor_mean(static_cast<std::size_t>(factors.size()), 0.0),
          factor_worst(static_cast<std::size_t>(factors.size()), 0.0),
          position_mean(portfolio.positions.size(), 0.0) {}
};

void accumulate(Accumulator &out, const FactorSet &factors, const Portfolio &portfolio,
                const detail::Moves &moves, Count scenarios) {
    const std::size_t assets = static_cast<std::size_t>(factors.size());
    for (std::size_t i = 0; i < assets; ++i) {
        const Real each = contribute(factors.factors[i], i, moves.relative[i], moves.absolute[i],
                                     portfolio.aggregate())
                              .total();
        out.factor_mean[i] += each / static_cast<Real>(scenarios);
        out.factor_worst[i] = std::min(out.factor_worst[i], each);
    }
    for (std::size_t p = 0; p < portfolio.positions.size(); ++p) {
        Real each = 0.0;
        for (std::size_t i = 0; i < assets; ++i) {
            each += contribute(factors.factors[i], i, moves.relative[i], moves.absolute[i],
                               portfolio.positions[p].exposures)
                        .total();
        }
        out.position_mean[p] += each / static_cast<Real>(scenarios);
    }
}

void finish(ScenarioSetResult &result, const Portfolio &portfolio, const FactorSet &factors,
            const Accumulator &accumulator, Real confidence) {
    Real position_sum = 0.0;
    for (std::size_t p = 0; p < portfolio.positions.size(); ++p) {
        result.by_position.push_back({portfolio.positions[p].name, accumulator.position_mean[p]});
        position_sum += accumulator.position_mean[p];
    }
    Real factor_sum = 0.0;
    for (std::size_t i = 0; i < static_cast<std::size_t>(factors.size()); ++i) {
        result.by_factor.push_back(
            {factors.factors[i].id, accumulator.factor_mean[i], accumulator.factor_worst[i]});
        factor_sum += accumulator.factor_mean[i];
    }
    result.position_attribution_residual = position_sum - result.mean_pnl;
    result.factor_attribution_residual = factor_sum - result.mean_pnl;
    // A single scenario has no distribution, so there is no quantile of it. Reporting
    // NaN with a reason is the honest answer; the estimator would either throw or
    // return the one number it was given dressed up as a risk measure.
    if (result.scenarios < 2) {
        result.var.value = std::numeric_limits<Real>::quiet_NaN();
        result.es.value = std::numeric_limits<Real>::quiet_NaN();
        result.var.confidence_level = confidence;
        result.es.confidence_level = confidence;
        result.var.observations = result.scenarios;
        result.es.observations = result.scenarios;
        result.note += "one scenario is not a distribution, so VaR and ES are NaN rather "
                       "than the single outcome relabelled; ";
    } else {
        result.var = risk::historical_var(result.pnl, confidence);
        result.es = risk::historical_es(result.pnl, confidence);
    }
}

} // namespace

ScenarioSample sample_factor_moves(std::span<const Real> covariance, Count assets, Count paths,
                                   Seed seed) {
    const auto n = static_cast<Eigen::Index>(assets);
    if (assets <= 0 || paths <= 0) {
        throw ValidationError("quantrisk: scenario sampling needs at least one asset and "
                              "one path; got " +
                              std::to_string(assets) + " assets and " + std::to_string(paths) +
                              " paths");
    }
    if (static_cast<std::size_t>(covariance.size()) !=
        static_cast<std::size_t>(assets) * static_cast<std::size_t>(assets)) {
        throw ValidationError("quantrisk: scenario sampling needs assets * assets "
                              "covariance entries");
    }
    Matrix matrix(n, n);
    for (Eigen::Index i = 0; i < n; ++i) {
        for (Eigen::Index j = 0; j < n; ++j) {
            matrix(i, j) = covariance[static_cast<std::size_t>(i * assets + j)];
        }
    }
    const Eigen::LLT<Matrix> factorisation(matrix);
    if (factorisation.info() != Eigen::Success) {
        // Jittering here would change the risk being measured by an amount nobody asked
        // for, so the refusal is the answer and the caller decides what to do about it.
        throw ValidationError("quantrisk: the scenario covariance is not positive "
                              "definite, so it has no Cholesky factor and cannot be "
                              "sampled; shrink it (portfolio::shrinkage_covariance) or "
                              "reduce the asset count");
    }
    const Matrix lower = factorisation.matrixL();

    ScenarioSample out;
    out.paths = paths;
    out.assets = assets;
    out.seed = seed;
    out.moves.resize(static_cast<std::size_t>(paths * assets), 0.0);
    Rng rng(seed);
    for (Count path = 0; path < paths; ++path) {
        const std::vector<Real> draws =
            rng.standard_normal_vector(static_cast<std::size_t>(assets));
        for (std::size_t i = 0; i < static_cast<std::size_t>(assets); ++i) {
            Real value = 0.0;
            for (std::size_t j = 0; j <= i; ++j) {
                value +=
                    lower(static_cast<Eigen::Index>(i), static_cast<Eigen::Index>(j)) * draws[j];
            }
            out.moves[static_cast<std::size_t>(path * assets + static_cast<Count>(i))] = value;
        }
    }
    out.note = "gaussian draws, Cholesky of the supplied covariance, seed " + std::to_string(seed);
    return out;
}

ScenarioSetResult run_historical_scenarios(const Portfolio &portfolio, const Scenario &scenario,
                                           std::span<const Real> observed_moves, Count observations,
                                           Real confidence) {
    if (confidence <= 0.0 || confidence >= 1.0) {
        throw ValidationError("quantrisk: a stress confidence level of " +
                              std::to_string(confidence) + " is outside (0, 1)");
    }
    const FactorSet &factors = portfolio.factors;
    const std::size_t assets = static_cast<std::size_t>(factors.size());
    if (static_cast<std::size_t>(observed_moves.size()) !=
        static_cast<std::size_t>(observations) * assets) {
        throw ValidationError("quantrisk: a historical scenario set needs observations * "
                              "assets = " +
                              std::to_string(static_cast<std::size_t>(observations) * assets) +
                              " moves, got " + std::to_string(observed_moves.size()));
    }
    if (observations <= 0) {
        throw ValidationError("quantrisk: an empty historical window has no scenario in it");
    }
    const ExposureVector aggregate = portfolio.aggregate();

    ScenarioSetResult result;
    result.scenario_name = scenario.name;
    result.kind = scenario.kind;
    result.assumptions = scenario.assumptions;
    result.generator =
        "historical replay of " + std::to_string(observations) + " observed factor-move sets";
    Accumulator accumulator(factors, portfolio);

    result.pnl.reserve(static_cast<std::size_t>(observations));
    for (Count t = 0; t < observations; ++t) {
        detail::Moves moves{std::vector<Real>(assets, 0.0), std::vector<Real>(assets, 0.0)};
        for (std::size_t i = 0; i < assets; ++i) {
            const Real value = observed_moves[static_cast<std::size_t>(t) * assets + i];
            // Equities are quoted relatively and the rest absolutely, so the observed
            // move is filed under whichever unit the factor's class answers to.
            if (factors.factors[i].asset_class == FactorClass::equity_index) {
                moves.relative[i] = value;
                moves.absolute[i] = value * factors.factors[i].level;
            } else {
                moves.absolute[i] = value;
                moves.relative[i] =
                    factors.factors[i].level != 0.0 ? value / factors.factors[i].level : 0.0;
            }
        }
        Real each = 0.0;
        for (std::size_t i = 0; i < assets; ++i) {
            each +=
                contribute(factors.factors[i], i, moves.relative[i], moves.absolute[i], aggregate)
                    .total();
        }
        result.pnl.push_back(each);
        accumulate(accumulator, factors, portfolio, moves, observations);
    }

    result.scenarios = observations;
    result.mean_pnl = 0.0;
    mean_and_sd(result.pnl, result.mean_pnl, result.volatility);
    result.worst_pnl = *std::min_element(result.pnl.begin(), result.pnl.end());
    result.best_pnl = *std::max_element(result.pnl.begin(), result.pnl.end());
    finish(result, portfolio, factors, accumulator, confidence);
    if (scenario.assumptions.empty()) {
        result.note += "the historical window carries no stated assumptions about why it "
                       "is representative; ";
    }
    result.note += "a replay, not a forecast: every outcome below is what this book would "
                   "have earned over the window supplied, and no ordering or forward use "
                   "of that window is implied; ";
    return result;
}

ScenarioSetResult run_monte_carlo_scenarios(const Portfolio &portfolio, const Scenario &scenario,
                                            std::span<const Real> covariance, Count paths,
                                            Seed seed, Real confidence) {
    const FactorSet &factors = portfolio.factors;
    const std::size_t assets = static_cast<std::size_t>(factors.size());
    const ExposureVector aggregate = portfolio.aggregate();
    const detail::Moves centre = resolve_moves(factors, scenario);

    std::string shift_note;
    const std::vector<Real> stressed =
        shift_covariance(covariance, factors.size(), scenario.distribution, shift_note);

    const ScenarioSample sample = sample_factor_moves(stressed, factors.size(), paths, seed);

    ScenarioSetResult result;
    result.scenario_name = scenario.name;
    result.kind = scenario.kind;
    result.assumptions = scenario.assumptions;
    result.generator = "monte carlo, " + std::to_string(paths) + " paths, " + sample.note;
    Accumulator accumulator(factors, portfolio);

    result.pnl.reserve(static_cast<std::size_t>(paths));
    for (Count path = 0; path < paths; ++path) {
        detail::Moves moves{std::vector<Real>(assets, 0.0), std::vector<Real>(assets, 0.0)};
        for (std::size_t i = 0; i < assets; ++i) {
            const Real draw = sample.moves[static_cast<std::size_t>(path * factors.size() + i)];
            const Real total_relative = centre.relative[i] + draw;
            moves.relative[i] = total_relative;
            // The drawn dispersion is in the same units the exposures answer to, so the
            // absolute move is reconstructed through the level rather than assumed equal.
            moves.absolute[i] =
                centre.absolute[i] + (factors.factors[i].asset_class == FactorClass::equity_index
                                          ? draw * factors.factors[i].level
                                          : draw);
        }
        Real each = 0.0;
        for (std::size_t i = 0; i < assets; ++i) {
            each +=
                contribute(factors.factors[i], i, moves.relative[i], moves.absolute[i], aggregate)
                    .total();
        }
        result.pnl.push_back(each);
        accumulate(accumulator, factors, portfolio, moves, paths);
    }

    result.scenarios = paths;
    mean_and_sd(result.pnl, result.mean_pnl, result.volatility);
    result.worst_pnl = *std::min_element(result.pnl.begin(), result.pnl.end());
    result.best_pnl = *std::max_element(result.pnl.begin(), result.pnl.end());
    finish(result, portfolio, factors, accumulator, confidence);
    result.note += shift_note;
    result.note += "the shocks set the centre of the move distribution and the "
                   "distribution field sets its shape, so this set is the outcome "
                   "distribution *around* the stress rather than an extra stress; ";
    return result;
}

} // namespace quantrisk::stress
