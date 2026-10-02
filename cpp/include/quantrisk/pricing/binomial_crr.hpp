#pragma once

#include "quantrisk/pricing/instrument.hpp"

namespace quantrisk {

/// Cox-Ross-Rubinstein (1979) binomial lattice, implemented from
/// docs/mathematical_specification.md §4.
///
/// Per step with `dt = T / N`:
///   u = exp(sigma sqrt(dt)), d = 1/u,
///   p = (exp((r - q) dt) - d) / (u - d),
///   value = exp(-r dt) * (p * up + (1 - p) * down),
/// with `value = max(value, payoff)` at every node for American exercise.
///
/// Degenerate edges:
/// - `T == 0` -> expiry payoff, `N` irrelevant.
/// - `sigma == 0` -> u = d = 1 makes `p` a 0/0 expression; the lattice is then
///   the deterministic forward path and is evaluated directly (European: the
///   discounted terminal payoff; American: the best exercise date), which is
///   exactly the limit of the lattice as sigma -> 0.
struct BinomialResult {
    Real price = 0.0;
    Count steps = 0;
    Real time_step = 0.0;
    Real up = 0.0;
    Real down = 0.0;
    Real risk_neutral_up_probability = 0.0;
    ExerciseStyle exercise_style = ExerciseStyle::European;
    std::string note;
};

[[nodiscard]] BinomialResult crr_binomial(const EuropeanOption &option, const MarketParams &market,
                                          ExerciseStyle style, Count steps);

/// Convenience wrappers matching the four instruments Phase 2 lists.
// python: via `crr_binomial` -- the option names its style; these four are lattice-test shorthand.
[[nodiscard]] Real crr_european_call(const MarketParams &, Real strike, Count steps);
// python: via `crr_binomial` -- the option names its style; these four are lattice-test shorthand.
[[nodiscard]] Real crr_european_put(const MarketParams &, Real strike, Count steps);
// python: via `crr_binomial` -- the option names its style; these four are lattice-test shorthand.
[[nodiscard]] Real crr_american_call(const MarketParams &, Real strike, Count steps);
// python: via `crr_binomial` -- the option names its style; these four are lattice-test shorthand.
[[nodiscard]] Real crr_american_put(const MarketParams &, Real strike, Count steps);

/// Error of the European lattice against the Black-Scholes value for each of
/// `step_counts`, used by the convergence study (never a single `N`).
[[nodiscard]] std::vector<std::pair<Count, Real>>
crr_convergence_to_black_scholes(const EuropeanOption &option, const MarketParams &market,
                                 const std::vector<Count> &step_counts);

} // namespace quantrisk
