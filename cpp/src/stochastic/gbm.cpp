#include "quantrisk/stochastic/gbm.hpp"

#include <cmath>

#include "quantrisk/core/validation.hpp"

namespace quantrisk::gbm {

namespace {

struct DriftScale {
    Real drift; // (r - q - sigma^2 / 2) * dt
    Real scale; // sigma * sqrt(dt)
};

DriftScale step_parameters(const MarketParams &market, const Count steps) {
    require_positive_integer(steps, "steps");
    const Real dt = market.maturity / static_cast<Real>(steps);
    return DriftScale{
        .drift =
            (market.rate - market.dividend_yield - 0.5 * market.volatility * market.volatility) *
            dt,
        .scale = market.volatility * std::sqrt(dt),
    };
}

} // namespace

std::vector<Real> terminal_prices(const MarketParams &market, const Count paths, Rng &rng) {
    market.validate();
    require_positive_integer(paths, "paths");
    const Real total_drift =
        (market.rate - market.dividend_yield - 0.5 * market.volatility * market.volatility) *
        market.maturity;
    const Real total_scale = market.volatility * std::sqrt(market.maturity);

    std::vector<Real> out(static_cast<std::size_t>(paths));
    for (Count i = 0; i < paths; ++i) {
        out[static_cast<std::size_t>(i)] =
            market.spot * std::exp(total_drift + total_scale * rng.standard_normal());
    }
    return out;
}

std::vector<Real> paths_matrix(const MarketParams &market, const Count paths, const Count steps,
                               Rng &rng) {
    market.validate();
    require_positive_integer(paths, "paths");
    const auto parameters = step_parameters(market, steps);
    const std::size_t width = static_cast<std::size_t>(steps) + 1;
    std::vector<Real> out(static_cast<std::size_t>(paths) * width);
    for (Count p = 0; p < paths; ++p) {
        Real level = market.spot;
        out[static_cast<std::size_t>(p) * width] = level;
        for (Count k = 1; k <= steps; ++k) {
            level *= std::exp(parameters.drift + parameters.scale * rng.standard_normal());
            out[static_cast<std::size_t>(p) * width + static_cast<std::size_t>(k)] = level;
        }
    }
    return out;
}

std::vector<Real> antithetic_paths_matrix(const MarketParams &market, const Count paths,
                                          const Count steps, Rng &rng) {
    if (paths % 2 != 0) {
        throw ValidationError("quantrisk: 'paths' must be even for antithetic sampling");
    }
    market.validate();
    const auto parameters = step_parameters(market, steps);
    const std::size_t width = static_cast<std::size_t>(steps) + 1;
    const Count half = paths / 2;
    std::vector<Real> out(static_cast<std::size_t>(paths) * width);

    for (Count p = 0; p < half; ++p) {
        Real up = market.spot;
        Real down = market.spot;
        out[static_cast<std::size_t>(p) * width] = up;
        out[static_cast<std::size_t>(p + half) * width] = down;
        for (Count k = 1; k <= steps; ++k) {
            const Real z = rng.standard_normal();
            // The antithetic partner flips the random term only: flipping the drift
            // as well would simulate the reversed dynamics, not the same measure.
            up *= std::exp(parameters.drift + parameters.scale * z);
            down *= std::exp(parameters.drift - parameters.scale * z);
            out[static_cast<std::size_t>(p) * width + static_cast<std::size_t>(k)] = up;
            out[static_cast<std::size_t>(p + half) * width + static_cast<std::size_t>(k)] = down;
        }
    }
    return out;
}

std::vector<Real> antithetic_terminal_prices(const MarketParams &market, const Count paths,
                                             Rng &rng) {
    if (paths % 2 != 0) {
        throw ValidationError("quantrisk: 'paths' must be even for antithetic sampling");
    }
    market.validate();
    const Real total_drift =
        (market.rate - market.dividend_yield - 0.5 * market.volatility * market.volatility) *
        market.maturity;
    const Real total_scale = market.volatility * std::sqrt(market.maturity);
    const Count half = paths / 2;
    std::vector<Real> out(static_cast<std::size_t>(paths));
    for (Count i = 0; i < half; ++i) {
        const Real z = rng.standard_normal();
        out[static_cast<std::size_t>(i)] = market.spot * std::exp(total_drift + total_scale * z);
        out[static_cast<std::size_t>(i + half)] =
            market.spot * std::exp(total_drift - total_scale * z);
    }
    return out;
}

std::vector<Real> terminal_prices_physical(const MarketParams &market, const Rate mu,
                                           const Count paths, Rng &rng) {
    market.validate();
    require_finite(mu, "mu");
    require_positive_integer(paths, "paths");
    const Real drift = (mu - market.dividend_yield - 0.5 * market.volatility * market.volatility) *
                       market.maturity;
    const Real scale = market.volatility * std::sqrt(market.maturity);
    std::vector<Real> out(static_cast<std::size_t>(paths));
    for (Count i = 0; i < paths; ++i) {
        out[static_cast<std::size_t>(i)] =
            market.spot * std::exp(drift + scale * rng.standard_normal());
    }
    return out;
}

Real expected_log_return(const MarketParams &market) {
    market.validate();
    return (market.rate - market.dividend_yield - 0.5 * market.volatility * market.volatility) *
           market.maturity;
}

} // namespace quantrisk::gbm
