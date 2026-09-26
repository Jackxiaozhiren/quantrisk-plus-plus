#pragma once

#include <span>
#include <string>
#include <vector>

#include "quantrisk/core/types.hpp"

namespace quantrisk {

/// Backtesting of risk forecasts (docs/mathematical_specification.md §6).
///
/// A violation is `loss > VaR`, i.e. `return < -VaR`. Under a correctly
/// specified model violations are i.i.d. Bernoulli with probability `1 - alpha`,
/// and the two tests below probe exactly that: the frequency (Kupiec) and the
/// independence of successive violations (Christoffersen), plus their combination
/// (conditional coverage, 2 degrees of freedom).
///
/// Stated H0, statistic and limitations:
///
/// * `kupiec_pof_test`
///   H0: the true violation probability equals the nominal `1 - alpha`.
///   Statistic `LR_po = -2 ln[ (1-p)^(n-x) p^x / ((1-x/n)^(n-x) (x/n)^x) ]`
///   with `p = 1 - alpha`, asymptotically chi-square(1).
///   Limitation: powerful only when many violations are expected. At 99 %
///   confidence and n = 250 the expected count is ~2.5, so the test almost never
///   rejects - an unconditional pass is weak evidence, and the asymptotic
///   chi-square approximation is poor in that regime. Zero or all-observed
///   violations make the likelihood ratio degenerate; the result says so.
///
/// * `christoffersen_independence_test`
///   H0: violations are independent of the previous period's outcome
///   (`pi_01 = pi_11`), tested by a likelihood-ratio on the 2x2 transition
///   counts, chi-square(1).
///   Limitation: needs both states to be observed in the previous period; if
///   there is no transition data (all zeros, or every observation a violation)
///   the statistic is NaN and the `note` explains why rather than reporting a
///   convenient pass.
///
/// * `christoffersen_conditional_coverage_test`
///   H0: independence *and* correct unconditional frequency jointly.
///   Statistic `LR_cc = LR_ind + LR_po`, chi-square(2).
struct ViolationSeries {
    std::vector<int> flags; ///< 1 = violation, 0 = no violation
    Count observations = 0;
    Count exceptions = 0;
    Real violation_rate = 0.0;
};

/// `returns[t] < -var_level[t]` marks a violation. Lengths must match.
[[nodiscard]] ViolationSeries flag_violations(std::span<const Real> returns_sample,
                                              std::span<const Real> var_levels);

/// Convenience: one constant VaR level for the whole sample.
[[nodiscard]] ViolationSeries flag_violations(std::span<const Real> returns_sample, Real var_level);

struct CoverageTestResult {
    Count observations = 0;
    Count exceptions = 0;
    Real nominal_violation_rate = 0.0;
    Real observed_violation_rate = 0.0;
    Real statistic = 0.0;
    Real p_value = 1.0;
    int degrees_of_freedom = 1;
    Real critical_value_95 = 3.841458820694124; ///< chi-square(1) 0.95 quantile
    bool rejected_at_5_percent = false;
    bool degenerate = false;
    std::string test;
    std::string interpretation;
};

[[nodiscard]] CoverageTestResult kupiec_pof_test(const ViolationSeries &series,
                                                 Real confidence_level);

[[nodiscard]] CoverageTestResult christoffersen_independence_test(const ViolationSeries &series);

[[nodiscard]] CoverageTestResult
christoffersen_conditional_coverage_test(const ViolationSeries &series, Real confidence_level);

/// Transition probabilities used by the independence test, exposed so the
/// experiment can report them (`pi_01` / `pi_11` are what clustering shows up in).
struct TransitionCounts {
    Count n00 = 0;
    Count n01 = 0;
    Count n10 = 0;
    Count n11 = 0;
    Real pi01 = std::numeric_limits<Real>::quiet_NaN();
    Real pi11 = std::numeric_limits<Real>::quiet_NaN();
    Real pi0 = std::numeric_limits<Real>::quiet_NaN();
    bool estimable = false;
};

[[nodiscard]] TransitionCounts transition_counts(const ViolationSeries &series);

struct BacktestReport {
    ViolationSeries series;
    CoverageTestResult kupiec;
    CoverageTestResult independence;
    CoverageTestResult conditional;
    std::string note;
};

/// VaR series and returns in, full three-test report out.
[[nodiscard]] BacktestReport backtest_var(std::span<const Real> returns_sample,
                                          std::span<const Real> var_levels, Real confidence_level);

} // namespace quantrisk
