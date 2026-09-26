#include "quantrisk/stochastic/heston.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>

#include "quantrisk/core/statistics.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/math/normal.hpp"
#include "quantrisk/monte_carlo/engine.hpp"

namespace quantrisk {

void HestonParams::validate() const {
    ValidationIssues issues;
    issues.check(std::isfinite(spot) && spot > 0.0,
                 "spot must be finite and > 0, got " + detail::format_value(spot));
    issues.check(std::isfinite(rate), "rate must be finite");
    issues.check(std::isfinite(dividend_yield), "dividend_yield must be finite");
    issues.check(std::isfinite(initial_variance) && initial_variance >= 0.0,
                 "initial_variance must be finite and >= 0, got " +
                     detail::format_value(initial_variance));
    issues.check(std::isfinite(kappa) && kappa >= 0.0,
                 "kappa must be finite and >= 0, got " + detail::format_value(kappa));
    issues.check(std::isfinite(theta) && theta >= 0.0,
                 "theta must be finite and >= 0, got " + detail::format_value(theta));
    issues.check(std::isfinite(xi) && xi >= 0.0,
                 "xi must be finite and >= 0, got " + detail::format_value(xi));
    issues.check(std::isfinite(rho) && rho >= -1.0 && rho <= 1.0,
                 "rho must be in [-1, 1], got " + detail::format_value(rho));
    issues.check(std::isfinite(maturity) && maturity >= 0.0,
                 "maturity must be finite and >= 0, got " + detail::format_value(maturity));
    issues.throw_if_failed("HestonParams");
}

bool HestonParams::feller_condition_satisfied() const { return 2.0 * kappa * theta >= xi * xi; }

Real HestonParams::instantaneous_volatility() const {
    return std::sqrt(std::max(initial_variance, 0.0));
}

HestonSimulation simulate_heston(const HestonParams &parameters, const Count paths,
                                 const Count steps, Rng &rng) {
    parameters.validate();
    require_positive_integer(paths, "paths");
    require_positive_integer(steps, "steps");

    HestonSimulation simulation;
    simulation.paths = paths;
    simulation.steps = steps;
    simulation.seed = rng.seed();
    const auto started = std::chrono::steady_clock::now();

    if (parameters.maturity == 0.0) {
        simulation.terminals.assign(static_cast<std::size_t>(paths), parameters.spot);
        simulation.terminal_variance.assign(static_cast<std::size_t>(paths),
                                            parameters.initial_variance);
        simulation.realised_variance.assign(static_cast<std::size_t>(paths), 0.0);
        simulation.time_step = 0.0;
        simulation.note = "degenerate edge T == 0: S_T is the spot";
        simulation.runtime_seconds =
            std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
        return simulation;
    }

    const Real dt = parameters.maturity / static_cast<Real>(steps);
    const Real root_dt = std::sqrt(dt);
    const Real correlation = parameters.rho;
    const Real independent_weight = std::sqrt(std::max(0.0, 1.0 - correlation * correlation));

    simulation.terminals.resize(static_cast<std::size_t>(paths));
    simulation.terminal_variance.resize(static_cast<std::size_t>(paths));
    simulation.realised_variance.resize(static_cast<std::size_t>(paths));
    Count clamped = 0;

    for (Count p = 0; p < paths; ++p) {
        Real level = parameters.spot;
        Real variance = parameters.initial_variance;
        Real integrated = 0.0;
        Real previous_variance = variance;
        for (Count k = 0; k < steps; ++k) {
            const Real z1 = rng.standard_normal();
            const Real z2 = correlation * z1 + independent_weight * rng.standard_normal();
            // Full truncation: the diffusion coefficient uses max(v, 0).
            const Real effective_variance = std::max(variance, 0.0);
            if (variance < 0.0) {
                ++clamped;
            }
            integrated += 0.5 * (previous_variance + effective_variance) * dt;
            previous_variance = effective_variance;

            level *= std::exp(
                (parameters.rate - parameters.dividend_yield - 0.5 * effective_variance) * dt +
                root_dt * std::sqrt(effective_variance) * z1);
            variance = variance + parameters.kappa * (parameters.theta - variance) * dt +
                       parameters.xi * root_dt * std::sqrt(effective_variance) * z2;
        }
        const std::size_t index = static_cast<std::size_t>(p);
        simulation.terminals[index] = level;
        simulation.terminal_variance[index] = std::max(variance, 0.0);
        simulation.realised_variance[index] = integrated;
    }

    simulation.time_step = dt;
    simulation.negative_variances_clamped = clamped;
    simulation.runtime_seconds =
        std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
    simulation.note = "full-truncation Euler on variance; discretisation bias is present and "
                      "measured by step refinement, this is not an exact simulation";
    return simulation;
}

HestonPriceResult price_heston_european(const HestonParams &parameters,
                                        const EuropeanOption &option, const Count paths,
                                        const Count steps, Rng &rng, const Real confidence_level) {
    option.validate();
    require_confidence_level(confidence_level, "confidence_level");

    HestonSimulation simulation = simulate_heston(parameters, paths, steps, rng);
    std::vector<Real> payoffs(simulation.terminals.size());
    for (std::size_t i = 0; i < simulation.terminals.size(); ++i) {
        payoffs[i] = option.payoff(simulation.terminals[i]);
    }

    const Real discount = std::exp(-parameters.rate * parameters.maturity);
    HestonPriceResult result;
    result.price = discount * stats::mean(payoffs);
    const Real variance = stats::sample_variance(payoffs);
    result.standard_error = discount * std::sqrt(variance / static_cast<Real>(payoffs.size()));
    const Real multiplier = normal_confidence_multiplier(confidence_level);
    result.confidence_low = result.price - multiplier * result.standard_error;
    result.confidence_high = result.price + multiplier * result.standard_error;
    result.paths = paths;
    result.steps = steps;
    result.seed = simulation.seed;
    result.mean_terminal_variance = stats::mean(simulation.terminal_variance);
    result.realised_variance_mean = stats::mean(simulation.realised_variance);
    result.negative_variances_clamped = simulation.negative_variances_clamped;
    result.feller_condition_satisfied = parameters.feller_condition_satisfied();
    result.runtime_seconds = simulation.runtime_seconds;
    result.note = simulation.note;
    return result;
}

Real heston_step_refinement_gap(const HestonParams &parameters, const EuropeanOption &option,
                                const Count paths, const Count steps, const Count reference_steps,
                                const Seed seed) {
    Rng coarse(seed);
    Rng fine(seed);
    const Real coarse_price = price_heston_european(parameters, option, paths, steps, coarse).price;
    const Real fine_price =
        price_heston_european(parameters, option, paths, reference_steps, fine).price;
    return coarse_price - fine_price;
}

} // namespace quantrisk
