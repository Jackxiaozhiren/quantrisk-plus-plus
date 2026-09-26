#include "quantrisk/risk/backtest.hpp"

#include <cmath>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/math/special.hpp"

namespace quantrisk {

namespace {

/// `count * log(base)` with the convention that an unobserved state contributes
/// zero: `0 * log(0)` is a limit of the likelihood, not an arithmetic product,
/// and evaluating it naively produces NaN which silently destroys the statistic.
Real x_log(const Real count, const Real base) {
    return count <= 0.0 ? 0.0 : count * std::log(base);
}

/// A likelihood ratio is non-negative by construction (the restricted model is a
/// special case of the fitted one), so a tiny negative is rounding at the
/// exact-fit point and is snapped to the true zero. A larger negative would be
/// an algebra error and is deliberately left visible.
Real snap_rounding(Real statistic) {
    if (statistic < 0.0 && statistic > -1.0e-10) {
        return 0.0;
    }
    return statistic;
}

Real critical_value(const int degrees_of_freedom) {
    // Solved from the same survival function the p-value is reported from, so the
    // two can never disagree through a mistyped or mismatched table entry.
    return chi_square_isf(0.05, degrees_of_freedom);
}

CoverageTestResult make_result(std::string test, const ViolationSeries &series, const Real nominal,
                               const Real statistic, const int dof, std::string interpretation) {
    CoverageTestResult result;
    result.test = std::move(test);
    result.observations = series.observations;
    result.exceptions = series.exceptions;
    result.nominal_violation_rate = nominal;
    result.observed_violation_rate = series.violation_rate;
    result.degrees_of_freedom = dof;
    result.statistic = statistic;
    result.interpretation = std::move(interpretation);
    if (std::isfinite(statistic)) {
        result.p_value = chi_square_sf(statistic, dof);
        result.critical_value_95 = critical_value(dof);
        result.rejected_at_5_percent = result.p_value < 0.05;
    } else {
        result.p_value = std::numeric_limits<Real>::quiet_NaN();
        result.critical_value_95 = critical_value(dof);
        result.rejected_at_5_percent = false;
        result.degenerate = true;
    }
    return result;
}

} // namespace

ViolationSeries flag_violations(std::span<const Real> returns_sample,
                                std::span<const Real> var_levels) {
    if (returns_sample.size() != var_levels.size()) {
        throw ValidationError(
            "quantrisk: the return sample and the VaR series must be the same length");
    }
    if (returns_sample.empty()) {
        throw ValidationError("quantrisk: cannot backtest an empty sample");
    }
    ViolationSeries series;
    series.flags.resize(returns_sample.size());
    for (std::size_t i = 0; i < returns_sample.size(); ++i) {
        require_finite(returns_sample[i], "return");
        require_finite(var_levels[i], "var_level");
        const bool violated = -returns_sample[i] > var_levels[i];
        series.flags[i] = violated ? 1 : 0;
        series.exceptions += violated ? 1 : 0;
    }
    series.observations = static_cast<Count>(returns_sample.size());
    series.violation_rate =
        static_cast<Real>(series.exceptions) / static_cast<Real>(series.observations);
    return series;
}

ViolationSeries flag_violations(std::span<const Real> returns_sample, const Real var_level) {
    std::vector<Real> levels(returns_sample.size(), var_level);
    return flag_violations(returns_sample, levels);
}

TransitionCounts transition_counts(const ViolationSeries &series) {
    TransitionCounts counts;
    for (std::size_t i = 1; i < series.flags.size(); ++i) {
        const int previous = series.flags[i - 1];
        const int current = series.flags[i];
        if (previous == 0 && current == 0) {
            ++counts.n00;
        } else if (previous == 0) {
            ++counts.n01;
        } else if (current == 0) {
            ++counts.n10;
        } else {
            ++counts.n11;
        }
    }
    const Real from_zero = static_cast<Real>(counts.n00 + counts.n01);
    const Real from_one = static_cast<Real>(counts.n10 + counts.n11);
    const Real total = static_cast<Real>(counts.n00 + counts.n01 + counts.n10 + counts.n11);
    counts.estimable = from_zero > 0.0 && from_one > 0.0 && total > 0.0;
    if (counts.estimable) {
        counts.pi01 = static_cast<Real>(counts.n01) / from_zero;
        counts.pi11 = static_cast<Real>(counts.n11) / from_one;
        counts.pi0 = static_cast<Real>(counts.n01 + counts.n11) / total;
    }
    return counts;
}

CoverageTestResult kupiec_pof_test(const ViolationSeries &series, const Real confidence_level) {
    require_confidence_level(confidence_level, "confidence_level");
    const Real n = static_cast<Real>(series.observations);
    const Real x = static_cast<Real>(series.exceptions);
    const Real p = 1.0 - confidence_level;

    // LR_po = -2 ln[ ((1-p)^(n-x) p^x) / ((1-x_hat)^(n-x) x_hat^x) ]. Both
    // likelihoods are binomial without the coefficient, which cancels.
    const Real log_likelihood_null = x_log(n - x, 1.0 - p) + x_log(x, p);
    const Real x_hat = x / n;
    const Real log_likelihood_fitted = x_log(n - x, 1.0 - x_hat) + x_log(x, x_hat);
    const Real statistic = snap_rounding(-2.0 * (log_likelihood_null - log_likelihood_fitted));

    const Real nominal = p;
    std::string interpretation;
    if (series.exceptions == 0) {
        interpretation = "no violations observed: the ratio collapses to the boundary, so a pass "
                         "here is uninformative about model quality";
    } else if (series.exceptions == series.observations) {
        interpretation = "every observation violated; the model is wrong, not borderline";
    } else {
        interpretation = "LR_po against chi-square(1); expected violations at this confidence "
                         "level are n(1-alpha) = " +
                         std::to_string(n * nominal).substr(0, 6);
    }
    return make_result("kupiec_pof", series, nominal, statistic, 1, std::move(interpretation));
}

CoverageTestResult christoffersen_independence_test(const ViolationSeries &series) {
    const TransitionCounts counts = transition_counts(series);
    if (!counts.estimable) {
        CoverageTestResult result =
            make_result("christoffersen_independence", series, series.violation_rate,
                        std::numeric_limits<Real>::quiet_NaN(), 1,
                        "not estimable: the sample has no transitions out of one of the "
                        "two states, so independence cannot be tested");
        result.degenerate = true;
        result.observed_violation_rate = series.violation_rate;
        return result;
    }
    const Real n00 = static_cast<Real>(counts.n00);
    const Real n01 = static_cast<Real>(counts.n01);
    const Real n10 = static_cast<Real>(counts.n10);
    const Real n11 = static_cast<Real>(counts.n11);

    // H0 (pi_01 == pi_11 == pi_0) versus the unrestricted two-state Markov fit,
    // both as products over the four observed transitions.
    const Real unrestricted = x_log(n00, 1.0 - counts.pi01) + x_log(n01, counts.pi01) +
                              x_log(n10, 1.0 - counts.pi11) + x_log(n11, counts.pi11);
    const Real restricted = x_log(n00 + n10, 1.0 - counts.pi0) + x_log(n01 + n11, counts.pi0);
    const Real statistic = snap_rounding(-2.0 * (restricted - unrestricted));

    const std::string interpretation =
        "H0: pi_01 == pi_11 (a violation does not change the next day's violation "
        "probability). Estimated pi_01 = " +
        std::to_string(counts.pi01).substr(0, 8) +
        ", pi_11 = " + std::to_string(counts.pi11).substr(0, 8);
    return make_result("christoffersen_independence", series, series.violation_rate, statistic, 1,
                       interpretation);
}

CoverageTestResult christoffersen_conditional_coverage_test(const ViolationSeries &series,
                                                            const Real confidence_level) {
    const CoverageTestResult independence = christoffersen_independence_test(series);
    const CoverageTestResult coverage = kupiec_pof_test(series, confidence_level);
    if (!std::isfinite(independence.statistic)) {
        CoverageTestResult result =
            make_result("christoffersen_conditional_coverage", series, 1.0 - confidence_level,
                        std::numeric_limits<Real>::quiet_NaN(), 2,
                        "not estimable: the independence component is undefined, so the joint "
                        "test cannot be performed");
        result.degenerate = true;
        return result;
    }
    const Real statistic = independence.statistic + coverage.statistic;
    return make_result("christoffersen_conditional_coverage", series, 1.0 - confidence_level,
                       statistic, 2,
                       "H0: independence and correct unconditional frequency jointly; "
                       "LR_cc = LR_ind + LR_po against chi-square(2)");
}

BacktestReport backtest_var(std::span<const Real> returns_sample, std::span<const Real> var_levels,
                            const Real confidence_level) {
    BacktestReport report;
    report.series = flag_violations(returns_sample, var_levels);
    report.kupiec = kupiec_pof_test(report.series, confidence_level);
    report.independence = christoffersen_independence_test(report.series);
    report.conditional = christoffersen_conditional_coverage_test(report.series, confidence_level);
    report.note = "violation := loss > VaR level; tests are asymptotic chi-square results and "
                  "lose power when few violations are expected";
    return report;
}

} // namespace quantrisk
