#include "quantrisk/monte_carlo/engine.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <span>

#include "quantrisk/core/statistics.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/math/normal.hpp"
#include "quantrisk/stochastic/gbm.hpp"

namespace quantrisk {

const char *to_string(const VarianceReduction method) {
    switch (method) {
    case VarianceReduction::None:
        return "plain";
    case VarianceReduction::Antithetic:
        return "antithetic";
    case VarianceReduction::ControlVariate:
        return "control_variate";
    }
    return "unknown";
}

Real normal_confidence_multiplier(const Real confidence_level) {
    require_confidence_level(confidence_level, "confidence_level");
    return inverse_normal_cdf(1.0 - (1.0 - confidence_level) / 2.0);
}

namespace {

struct Adjusted {
    std::vector<Real> units; ///< independent discounted observations
    Real control_beta = std::numeric_limits<Real>::quiet_NaN();
};

void finish(MonteCarloResult &result, std::span<const Real> units, Real discount,
            const Real confidence_multiplier) {
    if (units.empty()) {
        throw ValidationError("quantrisk: no samples to summarise");
    }
    const Real mean = stats::mean(units);
    result.price = discount * mean;
    result.sample_variance = stats::sample_variance(units);
    result.sample_stddev = std::sqrt(result.sample_variance);
    result.iid_units = static_cast<Count>(units.size());
    result.standard_error = result.sample_stddev / std::sqrt(static_cast<Real>(units.size()));
    const Real half = confidence_multiplier * result.standard_error;
    result.confidence_low = result.price - half;
    result.confidence_high = result.price + half;
}

/// Control variate: the terminal price itself, whose risk-neutral expectation
/// is known in closed form (S e^{(r-q)T}), so no extra model is imported.
Adjusted with_control_variate(std::span<const Real> terminals, const TerminalPayoff &payoff,
                              Real expected_terminal) {
    std::vector<Real> payoffs(terminals.size());
    for (std::size_t i = 0; i < terminals.size(); ++i) {
        payoffs[i] = payoff(terminals[i]);
    }
    const Real mean_control = stats::mean(terminals);
    std::vector<Real> control_deviates(terminals.size());
    std::vector<Real> payoff_deviates(terminals.size());
    const Real mean_payoff = stats::mean(payoffs);
    for (std::size_t i = 0; i < terminals.size(); ++i) {
        control_deviates[i] = terminals[i] - mean_control;
        payoff_deviates[i] = payoffs[i] - mean_payoff;
    }
    std::vector<Real> products(terminals.size());
    std::vector<Real> control_squares(terminals.size());
    for (std::size_t i = 0; i < terminals.size(); ++i) {
        products[i] = control_deviates[i] * payoff_deviates[i];
        control_squares[i] = control_deviates[i] * control_deviates[i];
    }
    const Real denominator = stats::sum_compensated(control_squares);
    const Real beta = denominator == 0.0 ? 0.0 : stats::sum_compensated(products) / denominator;

    std::vector<Real> adjusted(terminals.size());
    for (std::size_t i = 0; i < terminals.size(); ++i) {
        adjusted[i] = payoffs[i] - beta * (terminals[i] - expected_terminal);
    }
    return Adjusted{.units = std::move(adjusted), .control_beta = beta};
}

Adjusted antithetic_units(std::span<const Real> payoffs_in_pairs) {
    if (payoffs_in_pairs.size() % 2 != 0) {
        throw ValidationError("quantrisk: antithetic sampling needs an even path count");
    }
    const std::size_t pairs = payoffs_in_pairs.size() / 2;
    std::vector<Real> units(pairs);
    for (std::size_t i = 0; i < pairs; ++i) {
        units[i] = 0.5 * (payoffs_in_pairs[i] + payoffs_in_pairs[i + pairs]);
    }
    return Adjusted{.units = std::move(units)};
}

} // namespace

TerminalPayoff MonteCarloEngine::european_payoff(const EuropeanOption &option) {
    option.validate();
    const OptionType type = option.type;
    const Real strike = option.strike;
    return [type, strike](const Real level) {
        return type == OptionType::Call ? std::max(level - strike, 0.0)
                                        : std::max(strike - level, 0.0);
    };
}

MonteCarloResult MonteCarloEngine::price_european(const EuropeanOption &option,
                                                  const MarketParams &market, const Count paths,
                                                  const VarianceReduction method,
                                                  const Real confidence_level) {
    option.validate();
    return price_terminal_payoff(european_payoff(option), market, paths, method, confidence_level);
}

MonteCarloResult MonteCarloEngine::price_terminal_payoff(const TerminalPayoff &payoff,
                                                         const MarketParams &market,
                                                         const Count paths,
                                                         const VarianceReduction method,
                                                         const Real confidence_level) {
    market.validate();
    require_positive_integer(paths, "paths");
    require_confidence_level(confidence_level, "confidence_level");
    if (!payoff) {
        throw ValidationError("quantrisk: 'payoff' must be provided");
    }

    const Real discount = std::exp(-market.rate * market.maturity);
    const Real multiplier = normal_confidence_multiplier(confidence_level);

    MonteCarloResult result;
    result.paths = paths;
    result.seed = seed_;
    result.confidence_level = confidence_level;
    result.variance_reduction = method;

    const auto started = std::chrono::steady_clock::now();

    if (method == VarianceReduction::Antithetic) {
        if (paths % 2 != 0) {
            throw ValidationError("quantrisk: 'paths' must be even for antithetic sampling");
        }
        const std::vector<Real> terminals = gbm::antithetic_terminal_prices(market, paths, rng_);
        std::vector<Real> payoffs(terminals.size());
        for (std::size_t i = 0; i < terminals.size(); ++i) {
            payoffs[i] = payoff(terminals[i]);
        }
        const Adjusted units = antithetic_units(payoffs);
        finish(result, units.units, discount, multiplier);
        result.note = "exact GBM terminal transition; standard error from pair means, so "
                      "iid_units = paths / 2";
    } else if (method == VarianceReduction::ControlVariate) {
        const std::vector<Real> terminals = gbm::terminal_prices(market, paths, rng_);
        const Real expected_terminal =
            market.spot * std::exp((market.rate - market.dividend_yield) * market.maturity);
        const Adjusted units = with_control_variate(terminals, payoff, expected_terminal);
        finish(result, units.units, discount, multiplier);
        result.control_beta = units.control_beta;
        result.note = "control variate = terminal price with known risk-neutral mean "
                      "S e^{(r-q)T}; beta fitted on this same sample (adaptive), so the "
                      "reported variance is in-sample and slightly optimistic";
    } else {
        const std::vector<Real> terminals = gbm::terminal_prices(market, paths, rng_);
        std::vector<Real> payoffs(terminals.size());
        for (std::size_t i = 0; i < terminals.size(); ++i) {
            payoffs[i] = payoff(terminals[i]);
        }
        finish(result, payoffs, discount, multiplier);
        result.note = "exact GBM terminal transition, no variance reduction";
    }

    result.runtime_seconds =
        std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
    return result;
}

MonteCarloResult MonteCarloEngine::price_path_payoff(const PathPayoff &payoff,
                                                     const MarketParams &market, const Count paths,
                                                     const Count steps, const bool antithetic,
                                                     const Real confidence_level) {
    market.validate();
    require_positive_integer(paths, "paths");
    require_positive_integer(steps, "steps");
    require_confidence_level(confidence_level, "confidence_level");
    if (!payoff) {
        throw ValidationError("quantrisk: 'payoff' must be provided");
    }

    const Real discount = std::exp(-market.rate * market.maturity);
    const Real multiplier = normal_confidence_multiplier(confidence_level);

    MonteCarloResult result;
    result.paths = paths;
    result.seed = seed_;
    result.confidence_level = confidence_level;
    result.variance_reduction =
        antithetic ? VarianceReduction::Antithetic : VarianceReduction::None;
    if (antithetic && paths % 2 != 0) {
        throw ValidationError("quantrisk: 'paths' must be even for antithetic sampling");
    }

    const auto started = std::chrono::steady_clock::now();
    const std::vector<Real> matrix = antithetic
                                         ? gbm::antithetic_paths_matrix(market, paths, steps, rng_)
                                         : gbm::paths_matrix(market, paths, steps, rng_);
    const std::size_t width = static_cast<std::size_t>(steps) + 1;

    std::vector<Real> payoffs(static_cast<std::size_t>(paths));
    for (Count p = 0; p < paths; ++p) {
        payoffs[static_cast<std::size_t>(p)] =
            payoff(matrix.data() + static_cast<std::size_t>(p) * width, width);
    }

    if (antithetic) {
        const Adjusted units = antithetic_units(payoffs);
        finish(result, units.units, discount, multiplier);
    } else {
        finish(result, payoffs, discount, multiplier);
    }
    result.runtime_seconds =
        std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
    result.note = "path payoff over " + std::to_string(steps) +
                  " intervals; discretisation bias must be studied by refining steps";
    return result;
}

} // namespace quantrisk
