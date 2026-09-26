#pragma once

#include <cstdint>
#include <functional>
#include <string>
#include <vector>

#include "quantrisk/core/rng.hpp"
#include "quantrisk/core/types.hpp"
#include "quantrisk/pricing/instrument.hpp"

namespace quantrisk {

/// Payoff of a terminal state, and of a whole path (`data` holds
/// `steps + 1` levels starting at the spot).
using TerminalPayoff = std::function<Real(Real)>;
using PathPayoff = std::function<Real(const Real *data, std::size_t length)>;

enum class VarianceReduction { None, Antithetic, ControlVariate };

[[nodiscard]] const char *to_string(const VarianceReduction method);

/// Everything a reader needs to judge and reproduce one Monte Carlo estimate.
///
/// `standard_error` is always computed from the *independent* units of the
/// estimator used: single paths for plain Monte Carlo and the control variate,
/// and antithetic pair means for the antithetic estimator. Mixing those up is
/// the classic way to understate Monte Carlo error by sqrt(2).
struct MonteCarloResult {
    Real price = 0.0;
    Real standard_error = 0.0;
    Real confidence_level = 0.95;
    Real confidence_low = 0.0;
    Real confidence_high = 0.0;
    Count paths = 0;     ///< simulated terminal states / paths
    Count iid_units = 0; ///< independent samples behind `standard_error`
    Seed seed = 0;
    Real sample_variance = 0.0;
    Real sample_stddev = 0.0;
    Real control_beta = std::numeric_limits<Real>::quiet_NaN();
    Real runtime_seconds = 0.0;
    VarianceReduction variance_reduction = VarianceReduction::None;
    std::string measure = "risk_neutral";
    std::string note;
};

/// Reusable simulation framework (PROJECT_SPEC.md Phase 3): one engine owns one
/// reproducible stream, and every estimator reports its own uncertainty.
class MonteCarloEngine {
  public:
    explicit MonteCarloEngine(const Seed seed = Rng::kDefaultSeed) : rng_(seed), seed_(seed) {}

    MonteCarloEngine(const MonteCarloEngine &) = delete;
    MonteCarloEngine &operator=(const MonteCarloEngine &) = delete;

    [[nodiscard]] Seed seed() const { return seed_; }
    [[nodiscard]] std::uint64_t uniform_draws() const { return rng_.uniform_draws(); }
    [[nodiscard]] Rng &rng() { return rng_; }

    /// European vanilla priced from exact terminal draws (no discretisation bias).
    [[nodiscard]] MonteCarloResult
    price_european(const EuropeanOption &option, const MarketParams &market, Count paths,
                   VarianceReduction method = VarianceReduction::None,
                   Real confidence_level = 0.95);

    /// Arbitrary function of S_T.
    [[nodiscard]] MonteCarloResult
    price_terminal_payoff(const TerminalPayoff &payoff, const MarketParams &market, Count paths,
                          VarianceReduction method = VarianceReduction::None,
                          Real confidence_level = 0.95);

    /// Path-dependent payoff with `steps` intervals per path. `steps` is a bias
    /// knob to be studied, never a constant to be trusted.
    [[nodiscard]] MonteCarloResult price_path_payoff(const PathPayoff &payoff,
                                                     const MarketParams &market, Count paths,
                                                     Count steps, bool antithetic = false,
                                                     Real confidence_level = 0.95);

    [[nodiscard]] static TerminalPayoff european_payoff(const EuropeanOption &option);

  private:
    Rng rng_;
    Seed seed_ = Rng::kDefaultSeed;
};

/// Normal-approximation interval half-width, i.e. N^-1(1 - alpha / 2).
[[nodiscard]] Real normal_confidence_multiplier(Real confidence_level);

} // namespace quantrisk
