#include "quantrisk/monte_carlo/path_dependent.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <span>

#include "quantrisk/core/statistics.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/math/normal.hpp"
#include "quantrisk/stochastic/gbm.hpp"

namespace quantrisk {

namespace {

struct GeometricMoments {
    Real mean_log = 0.0;
    Real variance_log = 0.0;
};

/// Moments of ln of the discretely monitored geometric average.
GeometricMoments geometric_moments(const MarketParams &market, const Count points) {
    const Real h = market.maturity / static_cast<Real>(points);
    const Real drift =
        market.rate - market.dividend_yield - 0.5 * market.volatility * market.volatility;
    // mean of (1/M) sum_i ln S_{t_i} with ln S_t = ln S + drift * t + noise
    const Real mean_times = h * static_cast<Real>(points + 1) / 2.0; // (1/M) sum t_i
    return GeometricMoments{
        .mean_log = std::log(market.spot) + drift * mean_times,
        // (sigma^2 / M^2) * sum_{i,j} min(t_i, t_j) = sigma^2 h (M+1)(2M+1)/(6M)
        .variance_log = market.volatility * market.volatility * h * static_cast<Real>(points + 1) *
                        static_cast<Real>(2 * points + 1) / (6.0 * static_cast<Real>(points)),
    };
}

} // namespace

PricingResult geometric_asian_price(const AsianOption &option, const MarketParams &market) {
    option.validate();
    market.validate();

    PricingResult result;
    result.method = "geometric_asian_closed_form_discrete_monitoring";

    if (market.maturity == 0.0 || option.monitoring_points == 0) {
        result.price = option.payoff_from_average(market.spot);
        result.note = "degenerate edge T == 0: the average collapses to the spot";
        return result;
    }
    if (market.volatility == 0.0) {
        const Real deterministic_average =
            market.forward_at(market.maturity * static_cast<Real>(option.monitoring_points + 1) /
                              (2.0 * static_cast<Real>(option.monitoring_points)));
        result.price = std::exp(-market.rate * market.maturity) *
                       option.payoff_from_average(deterministic_average);
        result.note = "degenerate edge sigma == 0: the average is the forward average";
        return result;
    }

    const GeometricMoments moments = geometric_moments(market, option.monitoring_points);
    const Real sd = std::sqrt(moments.variance_log);
    const Real discount = std::exp(-market.rate * market.maturity);
    const Real forward_of_average = std::exp(moments.mean_log + 0.5 * moments.variance_log);

    const Real d_plus = (moments.mean_log + moments.variance_log - std::log(option.strike)) / sd;
    const Real d_minus = (moments.mean_log - std::log(option.strike)) / sd;
    result.d1 = d_plus;
    result.d2 = d_minus;
    result.price =
        option.type == OptionType::Call
            ? discount *
                  (forward_of_average * normal_cdf(d_plus) - option.strike * normal_cdf(d_minus))
            : discount *
                  (option.strike * normal_cdf(-d_minus) - forward_of_average * normal_cdf(-d_plus));
    return result;
}

namespace path_dependent {

Real asian_payoff_from_path(const AsianOption &option, const Real *data, const std::size_t length) {
    if (length < 2) {
        throw ValidationError("quantrisk: an Asian path needs at least one monitoring point");
    }
    // data[0] is the spot at t = 0 and is deliberately excluded: monitoring is
    // over (0, T], which is what the closed-form moments assume as well.
    const std::size_t points = length - 1;
    if (option.average_type == AverageType::Arithmetic) {
        Real total = 0.0;
        for (std::size_t i = 1; i <= points; ++i) {
            total += data[i];
        }
        return option.payoff_from_average(total / static_cast<Real>(points));
    }
    Real log_total = 0.0;
    for (std::size_t i = 1; i <= points; ++i) {
        log_total += std::log(data[i]);
    }
    return option.payoff_from_average(std::exp(log_total / static_cast<Real>(points)));
}

Real barrier_payoff_from_path(const BarrierOption &option, const Real *data,
                              const std::size_t length, const Real effective_barrier) {
    option.validate();
    BarrierOption adjusted = option;
    adjusted.barrier_level = effective_barrier;
    for (std::size_t i = 0; i < length; ++i) {
        if (!adjusted.survives(data[i])) {
            return adjusted.rebate;
        }
    }
    return adjusted.payoff(data[length - 1]);
}

namespace {

std::vector<Real> monitoring_levels(const MarketParams &market, const Count paths,
                                    const Count points, Rng &rng, const bool antithetic) {
    return antithetic ? gbm::antithetic_paths_matrix(market, paths, points, rng)
                      : gbm::paths_matrix(market, paths, points, rng);
}

MonteCarloResult summarise(std::span<const Real> units, const Real discount, const Count paths,
                           const Seed seed, const Real confidence_level, VarianceReduction method,
                           std::string note, const Real runtime_seconds) {
    MonteCarloResult result;
    result.paths = paths;
    result.seed = seed;
    result.confidence_level = confidence_level;
    result.variance_reduction = method;
    result.note = std::move(note);
    result.runtime_seconds = runtime_seconds;
    const Real multiplier = normal_confidence_multiplier(confidence_level);
    const Real mean = stats::mean(units);
    const Real variance = stats::sample_variance(units);
    result.price = discount * mean;
    result.sample_variance = variance;
    result.sample_stddev = std::sqrt(variance);
    result.iid_units = static_cast<Count>(units.size());
    result.standard_error = std::sqrt(variance / static_cast<Real>(units.size())) * discount;
    const Real half = multiplier * result.standard_error;
    result.confidence_low = result.price - half;
    result.confidence_high = result.price + half;
    return result;
}

} // namespace

MonteCarloResult price_geometric_asian(MonteCarloEngine &engine, const AsianOption &option,
                                       const MarketParams &market, const Count paths,
                                       const Real confidence_level) {
    AsianOption geometric = option;
    geometric.average_type = AverageType::Geometric;
    geometric.validate();
    market.validate();
    require_positive_integer(paths, "paths");

    const auto started = std::chrono::steady_clock::now();
    const std::vector<Real> matrix =
        monitoring_levels(market, paths, geometric.monitoring_points, engine.rng(), false);
    const std::size_t width = static_cast<std::size_t>(geometric.monitoring_points) + 1;
    std::vector<Real> payoffs(static_cast<std::size_t>(paths));
    for (Count p = 0; p < paths; ++p) {
        payoffs[static_cast<std::size_t>(p)] = asian_payoff_from_path(
            geometric, matrix.data() + static_cast<std::size_t>(p) * width, width);
    }
    const Real runtime =
        std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
    const Real discount = std::exp(-market.rate * market.maturity);
    return summarise(payoffs, discount, paths, engine.seed(), confidence_level,
                     VarianceReduction::None,
                     "geometric Asian by simulation; compare with geometric_asian_price", runtime);
}

MonteCarloResult price_asian(MonteCarloEngine &engine, const AsianOption &option,
                             const MarketParams &market, const Count paths,
                             const bool use_control_variate, const Real confidence_level) {
    AsianOption arithmetic = option;
    arithmetic.average_type = AverageType::Arithmetic;
    arithmetic.validate();
    market.validate();
    require_positive_integer(paths, "paths");
    require_confidence_level(confidence_level, "confidence_level");

    const auto started = std::chrono::steady_clock::now();
    const std::vector<Real> matrix =
        monitoring_levels(market, paths, arithmetic.monitoring_points, engine.rng(), false);
    const std::size_t width = static_cast<std::size_t>(arithmetic.monitoring_points) + 1;

    std::vector<Real> payoffs(static_cast<std::size_t>(paths));
    std::vector<Real> controls;
    if (use_control_variate) {
        controls.resize(static_cast<std::size_t>(paths));
    }
    for (Count p = 0; p < paths; ++p) {
        const Real *row = matrix.data() + static_cast<std::size_t>(p) * width;
        payoffs[static_cast<std::size_t>(p)] = asian_payoff_from_path(arithmetic, row, width);
        if (use_control_variate) {
            // Same path, geometric average: its expectation is known in closed form.
            Real log_total = 0.0;
            for (std::size_t i = 1; i < width; ++i) {
                log_total += std::log(row[i]);
            }
            controls[static_cast<std::size_t>(p)] =
                std::exp(log_total / static_cast<Real>(width - 1));
        }
    }

    Real control_beta = std::numeric_limits<Real>::quiet_NaN();
    std::string note = "arithmetic Asian by simulation, no control variate";
    if (use_control_variate) {
        const AsianOption geometric{arithmetic.type, arithmetic.strike, AverageType::Geometric,
                                    arithmetic.monitoring_points};
        const Real expected_control = [&geometric, &market]() {
            const GeometricMoments moments = geometric_moments(market, geometric.monitoring_points);
            // E[G] under Q, undiscounted.
            return std::exp(moments.mean_log + 0.5 * moments.variance_log);
        }();
        const Real mean_control = stats::mean(controls);
        const Real mean_payoff = stats::mean(payoffs);
        std::vector<Real> product(payoffs.size());
        std::vector<Real> control_square(payoffs.size());
        for (std::size_t i = 0; i < payoffs.size(); ++i) {
            product[i] = (payoffs[i] - mean_payoff) * (controls[i] - mean_control);
            control_square[i] = (controls[i] - mean_control) * (controls[i] - mean_control);
        }
        const Real denominator = stats::sum_compensated(control_square);
        control_beta = denominator == 0.0 ? 0.0 : stats::sum_compensated(product) / denominator;
        for (std::size_t i = 0; i < payoffs.size(); ++i) {
            payoffs[i] -= control_beta * (controls[i] - expected_control);
        }
        note = "arithmetic Asian with the discretely monitored geometric average as "
               "control variate (closed-form expectation, beta fitted in-sample)";
    }

    const Real runtime =
        std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
    const Real discount = std::exp(-market.rate * market.maturity);
    MonteCarloResult result =
        summarise(payoffs, discount, paths, engine.seed(), confidence_level,
                  use_control_variate ? VarianceReduction::ControlVariate : VarianceReduction::None,
                  note, runtime);
    result.control_beta = control_beta;
    return result;
}

MonteCarloResult price_barrier(MonteCarloEngine &engine, const BarrierOption &option,
                               const MarketParams &market, const Count paths, const Count steps,
                               const bool continuous_approximation, const bool antithetic,
                               const Real confidence_level) {
    option.validate();
    market.validate();
    require_positive_integer(paths, "paths");
    require_positive_integer(steps, "steps");
    require_confidence_level(confidence_level, "confidence_level");
    if (antithetic && paths % 2 != 0) {
        throw ValidationError("quantrisk: 'paths' must be even for antithetic sampling");
    }

    const Real dt = market.maturity / static_cast<Real>(steps);
    const Real effective_barrier = continuous_approximation
                                       ? continuity_corrected_barrier(option, market, dt)
                                       : option.barrier_level;

    const auto started = std::chrono::steady_clock::now();
    const std::vector<Real> matrix =
        monitoring_levels(market, paths, steps, engine.rng(), antithetic);
    const std::size_t width = static_cast<std::size_t>(steps) + 1;
    std::vector<Real> payoffs(static_cast<std::size_t>(paths));
    for (Count p = 0; p < paths; ++p) {
        payoffs[static_cast<std::size_t>(p)] = barrier_payoff_from_path(
            option, matrix.data() + static_cast<std::size_t>(p) * width, width, effective_barrier);
    }
    if (antithetic) {
        const Count half = paths / 2;
        std::vector<Real> pairs(static_cast<std::size_t>(half));
        for (Count p = 0; p < half; ++p) {
            pairs[static_cast<std::size_t>(p)] =
                0.5 * (payoffs[static_cast<std::size_t>(p)] +
                       payoffs[static_cast<std::size_t>(p + half)]);
        }
        const Real runtime =
            std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
        return summarise(pairs, std::exp(-market.rate * market.maturity), paths, engine.seed(),
                         confidence_level, VarianceReduction::Antithetic,
                         "discrete monitoring over " + std::to_string(steps) + " dates" +
                             (continuous_approximation
                                  ? ", barrier shifted by exp(beta sigma sqrt(dt)) to approximate "
                                    "continuous monitoring (BGK correction, an approximation)"
                                  : "") +
                             "; standard error from pair means",
                         runtime);
    }
    const Real runtime =
        std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
    return summarise(payoffs, std::exp(-market.rate * market.maturity), paths, engine.seed(),
                     confidence_level, VarianceReduction::None,
                     "discrete monitoring over " + std::to_string(steps) + " dates" +
                         (continuous_approximation
                              ? ", barrier shifted by exp(beta sigma sqrt(dt)) to approximate "
                                "continuous monitoring (BGK correction, an approximation)"
                              : ""),
                     runtime);
}

} // namespace path_dependent

} // namespace quantrisk
