#include "quantrisk/portfolio/linear_program.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <vector>

#include <Eigen/Dense>

#include "quantrisk/core/validation.hpp"

namespace quantrisk::portfolio {

namespace {

using Matrix = Eigen::Matrix<Real, Eigen::Dynamic, Eigen::Dynamic>;
using RowMajorMatrix = Eigen::Matrix<Real, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>;
using Vector = Eigen::Matrix<Real, Eigen::Dynamic, 1>;
using IndexVector = std::vector<Count>;

/// Anything below this counts as zero. Tableau entries accumulate the rounding of
/// many Gauss-Jordan updates, so the test must be looser than machine epsilon and
/// still far below any coefficient a real program uses.
constexpr Real kPivotTolerance = 1.0e-10;

/// Tolerance for accepting the reported point as optimal, in units of the
/// problem's own scale. The certificate is checked against the *original*
/// matrices, so this is not the tableau's internal slack.
constexpr Real kCertificateTolerance = 1.0e-7;

struct Tableau {
    Count rows = 0;
    Count cols = 0; ///< structural columns plus one artificial per row
    Matrix data;    ///< (rows + 1) x (cols + 1): last row objective, last column rhs
    IndexVector basis;
};

[[nodiscard]] Eigen::Index at(const Count value) { return static_cast<Eigen::Index>(value); }

/// Recompute the objective row for `cost` given the current basis. The body is kept
/// in canonical form (every basic column is a unit vector), so the reduced costs
/// are `cost_j - sum_i cost[basis_i] * T_ij` and the objective value is the negated
/// right-hand-side entry.
void price(Tableau &table, const Vector &cost) {
    Vector basic_cost(table.rows);
    for (Count i = 0; i < table.rows; ++i) {
        basic_cost(at(i)) = cost(at(table.basis[static_cast<std::size_t>(i)]));
    }
    const Count body = table.rows;
    for (Count j = 0; j <= table.cols; ++j) {
        table.data(at(body), at(j)) = (j < table.cols ? cost(at(j)) : 0.0) -
                                      basic_cost.dot(table.data.col(at(j)).head(at(body)));
    }
}

/// Make column `entering` a unit vector with its 1 in `row`.
void pivot(Tableau &table, const Count entering, const Count row) {
    table.data.row(at(row)) /= table.data(at(row), at(entering));
    for (Count i = 0; i <= table.rows; ++i) {
        if (i == row) {
            continue;
        }
        const Real factor = table.data(at(i), at(entering));
        if (factor != 0.0) {
            table.data.row(at(i)) -= factor * table.data.row(at(row));
        }
    }
    table.basis[static_cast<std::size_t>(row)] = entering;
}

enum class PhaseOutcome {
    Optimal,
    Unbounded,
    PivotBudget,
};

/// Primal simplex with Bland's rule.
///
/// Bland's smallest-index rules for both the entering column and the leaving row
/// are what make this terminate: Dantzig's steepest reduced cost can cycle on
/// degenerate bases, and a cycling solver is worse than a slow one because the
/// wrong answer it eventually prints looks exactly like a right one.
[[nodiscard]] PhaseOutcome run_phase(Tableau &table, const Vector &cost,
                                     const std::vector<bool> &eligible, const Count max_pivots) {
    for (Count step = 0; step <= max_pivots; ++step) {
        price(table, cost);
        Count entering = -1;
        for (Count j = 0; j < table.cols; ++j) {
            if (eligible[static_cast<std::size_t>(j)] &&
                table.data(at(table.rows), at(j)) < -kPivotTolerance) {
                entering = j;
                break; // Bland: the lowest-indexed eligible column
            }
        }
        if (entering < 0) {
            return PhaseOutcome::Optimal;
        }
        Count leaving = -1;
        Real best_ratio = std::numeric_limits<Real>::quiet_NaN();
        for (Count i = 0; i < table.rows; ++i) {
            const Real entry = table.data(at(i), at(entering));
            if (entry <= kPivotTolerance) {
                continue;
            }
            const Real ratio = table.data(at(i), at(table.cols)) / entry;
            if (leaving < 0 || ratio < best_ratio - kPivotTolerance ||
                (std::abs(ratio - best_ratio) <= kPivotTolerance &&
                 table.basis[static_cast<std::size_t>(i)] <
                     table.basis[static_cast<std::size_t>(leaving)])) {
                best_ratio = ratio;
                leaving = i;
            }
        }
        if (leaving < 0) {
            return PhaseOutcome::Unbounded;
        }
        pivot(table, entering, leaving);
    }
    return PhaseOutcome::PivotBudget;
}

[[nodiscard]] const char *phase_note(const PhaseOutcome outcome) {
    switch (outcome) {
    case PhaseOutcome::Optimal:
        return "optimal for this phase";
    case PhaseOutcome::Unbounded:
        return "the objective can be improved without bound along a feasible direction, "
               "so the program has no finite optimum";
    case PhaseOutcome::PivotBudget:
        return "the pivot budget was exhausted, so no optimum was established";
    }
    return "unreachable phase outcome";
}

} // namespace

LinearProgramResult solve_linear_program(const std::span<const Real> objective,
                                         const std::span<const Real> constraint_rows,
                                         const std::span<const Real> rhs, const Count variables,
                                         const Count constraints) {
    LinearProgramResult result;
    if (variables <= 0 || constraints <= 0) {
        detail::reject("variables and constraints", "positive counts",
                       detail::format_value(static_cast<Real>(variables)));
    }
    if (objective.size() != static_cast<std::size_t>(variables)) {
        throw ValidationError("quantrisk: the objective must have `variables` entries");
    }
    if (constraint_rows.size() !=
        static_cast<std::size_t>(variables) * static_cast<std::size_t>(constraints)) {
        throw ValidationError(
            "quantrisk: the constraint matrix must hold constraints * variables entries");
    }
    if (rhs.size() != static_cast<std::size_t>(constraints)) {
        throw ValidationError("quantrisk: the right-hand side must have `constraints` entries");
    }
    for (const Real value : objective) {
        require_finite(value, "objective coefficient");
    }
    for (const Real value : constraint_rows) {
        require_finite(value, "constraint coefficient");
    }
    for (const Real value : rhs) {
        require_finite(value, "constraint right-hand side");
    }

    const Count total = variables + constraints;
    Tableau table;
    table.rows = constraints;
    table.cols = total;
    table.data = Matrix::Zero(constraints + 1, total + 1);
    table.basis.resize(static_cast<std::size_t>(constraints));

    Real rhs_scale = 1.0;
    for (Count i = 0; i < constraints; ++i) {
        for (Count j = 0; j < variables; ++j) {
            table.data(at(i), at(j)) = constraint_rows[static_cast<std::size_t>(i * variables + j)];
        }
        table.data(at(i), at(variables + i)) = 1.0;
        table.data(at(i), at(total)) = rhs[static_cast<std::size_t>(i)];
        table.basis[static_cast<std::size_t>(i)] = variables + i;
        rhs_scale = std::max(rhs_scale, std::abs(rhs[static_cast<std::size_t>(i)]));
        if (rhs[static_cast<std::size_t>(i)] < 0.0) {
            // The artificial basis needs b >= 0. Negating one row is an
            // equivalence, not an approximation: same solution set, same bounds.
            table.data.row(at(i)) *= -1.0;
        }
    }

    Vector phase_one_cost = Vector::Zero(total);
    for (Count i = 0; i < constraints; ++i) {
        phase_one_cost(at(variables + i)) = 1.0;
    }
    std::vector<bool> eligible(static_cast<std::size_t>(total), true);
    const Count budget = 40 * (constraints + total) + 2000;
    const PhaseOutcome first = run_phase(table, phase_one_cost, eligible, budget);
    price(table, phase_one_cost);
    const Real artificials = -table.data(at(table.rows), at(total));
    if (first != PhaseOutcome::Optimal) {
        result.status =
            first == PhaseOutcome::Unbounded ? LpStatus::Unbounded : LpStatus::NumericalFailure;
        result.note = phase_note(first);
        return result;
    }
    if (artificials > kPivotTolerance) {
        result.status = LpStatus::Infeasible;
        result.note = "no non-negative point satisfies the constraints: phase one ended with "
                      "artificial mass " +
                      detail::format_value(artificials);
        return result;
    }

    // An artificial still basic at zero must be pivoted out or its row is
    // redundant (all structural coefficients zero), and a redundant row would let
    // a later ratio test divide by nothing.
    for (Count i = 0; i < constraints; ++i) {
        if (table.basis[static_cast<std::size_t>(i)] < variables) {
            continue;
        }
        bool swapped = false;
        for (Count j = 0; j < variables && !swapped; ++j) {
            if (std::abs(table.data(at(i), at(j))) > kPivotTolerance) {
                pivot(table, j, i);
                swapped = true;
            }
        }
        if (!swapped) {
            table.data.row(at(i)).setZero();
        }
    }
    for (Count j = variables; j < total; ++j) {
        eligible[static_cast<std::size_t>(j)] = false; // artificials never return
    }

    Vector phase_two_cost = Vector::Zero(total);
    for (Count j = 0; j < variables; ++j) {
        phase_two_cost(at(j)) = objective[static_cast<std::size_t>(j)];
    }
    const PhaseOutcome second = run_phase(table, phase_two_cost, eligible, budget);
    if (second != PhaseOutcome::Optimal) {
        result.status =
            second == PhaseOutcome::Unbounded ? LpStatus::Unbounded : LpStatus::NumericalFailure;
        result.note = phase_note(second);
        return result;
    }

    result.values.assign(static_cast<std::size_t>(variables), 0.0);
    for (Count i = 0; i < constraints; ++i) {
        const Count column = table.basis[static_cast<std::size_t>(i)];
        if (column < variables) {
            result.values[static_cast<std::size_t>(column)] = table.data(at(i), at(total));
        }
    }

    // The certificate is checked against the original data, not the tableau: the
    // equalities must reproduce, no variable may be negative, and no reduced cost
    // may be negative. Those three are LP optimality (weak duality closes), so a
    // pass means the point is optimal whatever path the pivots took.
    price(table, phase_two_cost);
    Real worst_reduced_cost = 0.0;
    for (Count j = 0; j < variables; ++j) {
        worst_reduced_cost =
            std::min(worst_reduced_cost, static_cast<Real>(table.data(at(table.rows), at(j))));
    }
    Real residual = 0.0;
    for (Count i = 0; i < constraints; ++i) {
        Real row_value = 0.0;
        for (Count j = 0; j < variables; ++j) {
            row_value += constraint_rows[static_cast<std::size_t>(i * variables + j)] *
                         result.values[static_cast<std::size_t>(j)];
        }
        residual = std::max(residual, std::abs(rhs[static_cast<std::size_t>(i)] - row_value));
    }
    Real lowest = 0.0;
    for (const Real value : result.values) {
        lowest = std::min(lowest, value);
    }
    result.residual = residual / rhs_scale;
    result.dual_gap = std::max(Real{0.0}, -worst_reduced_cost);
    result.objective =
        std::inner_product(objective.begin(), objective.end(), result.values.begin(), 0.0);
    const bool certified = result.residual <= kCertificateTolerance &&
                           result.dual_gap <= kCertificateTolerance &&
                           lowest >= -kCertificateTolerance;
    result.status = certified ? LpStatus::Optimal : LpStatus::NumericalFailure;
    result.note = certified
                      ? "optimum certified against the original data: constraints "
                        "reproduced to " +
                            detail::format_value(result.residual) + ", no reduced cost below " +
                            detail::format_value(-result.dual_gap) + ", no variable below " +
                            detail::format_value(lowest)
                      : "the simplex terminated but the optimality certificate did not hold "
                        "(residual " +
                            detail::format_value(result.residual) + ", reduced cost " +
                            detail::format_value(-result.dual_gap) + ", bound " +
                            detail::format_value(lowest) + ")";
    return result;
}

} // namespace quantrisk::portfolio
