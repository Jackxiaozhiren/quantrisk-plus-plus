#pragma once

#include <algorithm>
#include <cmath>
#include <limits>
#include <string>

#include "quantrisk/core/types.hpp"
#include "quantrisk/core/validation.hpp"

namespace quantrisk {

/// Freeze surface introduced in Phase 2 (docs/project_scope.md §10).
enum class OptionType { Call, Put };

enum class ExerciseStyle { European, American };

[[nodiscard]] const char *to_string(const OptionType type);
[[nodiscard]] const char *to_string(const ExerciseStyle style);

/// Market environment shared by every deterministic pricer.
///
/// Domain (docs/mathematical_specification.md §0, §2): `S > 0`, `K > 0`,
/// `sigma >= 0`, `T >= 0`, and `r`, `q` finite (sign unrestricted, so negative
/// rates and negative carry are expressible).
struct MarketParams {
    Real spot = 0.0;
    Rate rate = 0.0;
    Rate dividend_yield = 0.0;
    Volatility volatility = 0.0;
    Time maturity = 0.0;

    /// Collects every violated constraint so a bad record produces one readable
    /// error instead of one per rebuild.
    void validate() const {
        ValidationIssues issues;
        issues.check(std::isfinite(spot) && spot > 0.0,
                     "spot must be finite and > 0, got " + detail::format_value(spot));
        issues.check(std::isfinite(rate), "rate must be finite, got " + detail::format_value(rate));
        issues.check(std::isfinite(dividend_yield),
                     "dividend_yield must be finite, got " + detail::format_value(dividend_yield));
        issues.check(std::isfinite(volatility) && volatility >= 0.0,
                     "volatility must be finite and >= 0, got " + detail::format_value(volatility));
        issues.check(std::isfinite(maturity) && maturity >= 0.0,
                     "maturity must be finite and >= 0, got " + detail::format_value(maturity));
        issues.throw_if_failed("MarketParams");
    }

    /// Carrying the underlying to `time` under the risk-neutral measure.
    [[nodiscard]] Real forward_at(const Time time) const {
        return spot * std::exp((rate - dividend_yield) * time);
    }
};

/// A single-option contract. Combination payoffs are built in Python from
/// these primitives, not by extending this type.
struct EuropeanOption {
    OptionType type = OptionType::Call;
    Real strike = 0.0;

    EuropeanOption() = default;
    constexpr EuropeanOption(const OptionType option_type, const Real option_strike)
        : type(option_type), strike(option_strike) {}

    void validate() const {
        ValidationIssues issues;
        issues.check(std::isfinite(strike) && strike > 0.0,
                     "strike must be finite and > 0, got " + detail::format_value(strike));
        issues.throw_if_failed("EuropeanOption");
    }

    /// Payoff at expiry as a function of the observed underlying level.
    [[nodiscard]] Real payoff(const Real underlying) const {
        return type == OptionType::Call ? std::max(underlying - strike, 0.0)
                                        : std::max(strike - underlying, 0.0);
    }
};

/// Price plus the intermediates that make a result auditable.
struct PricingResult {
    Real price = 0.0;
    /// d1/d2 are undefined for the degenerate edges; NaN marks them as such
    /// rather than reporting a number that came from a division by zero.
    Real d1 = std::numeric_limits<Real>::quiet_NaN();
    Real d2 = std::numeric_limits<Real>::quiet_NaN();
    std::string method;
    std::string note;
};

/// Analytic Greeks, units frozen in docs/mathematical_specification.md §3:
/// vega per unit volatility, theta per year, rho per unit rate.
struct Greeks {
    Real delta = 0.0;
    Real gamma = 0.0;
    Real vega = 0.0;
    Real theta = 0.0;
    Real rho = 0.0;
};

} // namespace quantrisk
