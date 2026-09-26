#include "quantrisk/pricing/binomial_crr.hpp"

#include <algorithm>
#include <cmath>
#include <vector>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/pricing/black_scholes.hpp"

namespace quantrisk {

namespace {

/// Node level at time layer `k`, state `j` (j up-moves, k - j down-moves):
/// S * u^j * d^(k-j) = S * exp((2j - k) * log u), computed directly from the
/// exponent so that no multiplicative drift accumulates as the layer widens.
Real node_level(const MarketParams &market, const Real log_up, const Count k, const Count j) {
    return market.spot * std::exp((2.0 * static_cast<Real>(j) - static_cast<Real>(k)) * log_up);
}

/// Zero-volatility (or zero-maturity) lattice limit. With sigma == 0 the
/// up/down factors coincide and `p` becomes 0/0, so the tree is evaluated as
/// the deterministic risk-neutral forward path it degenerates to.
Real degenerate_lattice_value(const EuropeanOption &option, const MarketParams &market,
                              const ExerciseStyle style, BinomialResult &result) {
    if (market.maturity == 0.0) {
        result.note = "degenerate edge T == 0: expiry payoff";
        return option.payoff(market.spot);
    }
    const Real discount = std::exp(-market.rate * market.maturity);
    const Real forward = market.forward_at(market.maturity);
    if (style == ExerciseStyle::European) {
        result.note = "degenerate edge sigma == 0: deterministic forward, European payoff";
        return discount * option.payoff(forward);
    }
    result.note = "degenerate edge sigma == 0: American value taken as the best exercise "
                  "date along the deterministic forward path, searched on 1001 points "
                  "(documented approximation, not an exact optimisation)";
    Real best = 0.0;
    constexpr Count kGrid = 1000;
    for (Count k = 0; k <= kGrid; ++k) {
        const Time time = market.maturity * static_cast<Real>(k) / static_cast<Real>(kGrid);
        best =
            std::max(best, std::exp(-market.rate * time) * option.payoff(market.forward_at(time)));
    }
    return best;
}

} // namespace

BinomialResult crr_binomial(const EuropeanOption &option, const MarketParams &market,
                            const ExerciseStyle style, const Count steps) {
    market.validate();
    option.validate();
    require_positive_integer(steps, "steps");

    BinomialResult result;
    result.steps = steps;
    result.exercise_style = style;
    result.time_step = market.maturity / static_cast<Real>(steps);

    if (is_degenerate(market)) {
        result.price = degenerate_lattice_value(option, market, style, result);
        return result;
    }

    const Real dt = result.time_step;
    const Real up = std::exp(market.volatility * std::sqrt(dt));
    const Real down = 1.0 / up;
    const Real log_up = std::log(up);
    const Real probability =
        (std::exp((market.rate - market.dividend_yield) * dt) - down) / (up - down);
    const Real discount = std::exp(-market.rate * dt);

    result.up = up;
    result.down = down;
    result.risk_neutral_up_probability = probability;

    if (probability < 0.0 || probability > 1.0) {
        result.note = "risk-neutral up-probability outside [0, 1]: this coarse lattice is not "
                      "a valid probability measure for these (r - q, sigma, dt) values; the "
                      "rollback still returns the model value, refine steps before reading it";
    }

    std::vector<Real> values(static_cast<std::size_t>(steps) + 1, 0.0);
    for (Count j = 0; j <= steps; ++j) {
        values[static_cast<std::size_t>(j)] = option.payoff(node_level(market, log_up, steps, j));
    }

    for (Count k = steps - 1; k >= 0; --k) {
        for (Count j = 0; j <= k; ++j) {
            const Real continuation =
                discount * (probability * values[static_cast<std::size_t>(j + 1)] +
                            (1.0 - probability) * values[static_cast<std::size_t>(j)]);
            if (style == ExerciseStyle::American) {
                values[static_cast<std::size_t>(j)] =
                    std::max(continuation, option.payoff(node_level(market, log_up, k, j)));
            } else {
                values[static_cast<std::size_t>(j)] = continuation;
            }
        }
    }

    result.price = values.front();
    return result;
}

Real crr_european_call(const MarketParams &market, const Real strike, const Count steps) {
    return crr_binomial(EuropeanOption{OptionType::Call, strike}, market, ExerciseStyle::European,
                        steps)
        .price;
}

Real crr_european_put(const MarketParams &market, const Real strike, const Count steps) {
    return crr_binomial(EuropeanOption{OptionType::Put, strike}, market, ExerciseStyle::European,
                        steps)
        .price;
}

Real crr_american_call(const MarketParams &market, const Real strike, const Count steps) {
    return crr_binomial(EuropeanOption{OptionType::Call, strike}, market, ExerciseStyle::American,
                        steps)
        .price;
}

Real crr_american_put(const MarketParams &market, const Real strike, const Count steps) {
    return crr_binomial(EuropeanOption{OptionType::Put, strike}, market, ExerciseStyle::American,
                        steps)
        .price;
}

std::vector<std::pair<Count, Real>>
crr_convergence_to_black_scholes(const EuropeanOption &option, const MarketParams &market,
                                 const std::vector<Count> &step_counts) {
    const Real reference = black_scholes(option, market).price;
    std::vector<std::pair<Count, Real>> out;
    out.reserve(step_counts.size());
    for (Count steps : step_counts) {
        steps = std::max<Count>(steps, 1);
        const Real price = crr_binomial(option, market, ExerciseStyle::European, steps).price;
        out.emplace_back(steps, price - reference);
    }
    return out;
}

} // namespace quantrisk
