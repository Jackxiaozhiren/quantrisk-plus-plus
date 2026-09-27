#include "quantrisk/portfolio/cvar.hpp"

#include <cmath>
#include <limits>
#include <numeric>
#include <vector>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/portfolio/linear_program.hpp"

namespace quantrisk::portfolio {

CvarSolution minimise_cvar(const CvarRequest &request) {
    CvarSolution solution;
    const Count assets = request.assets;
    const Count scenarios = request.scenarios;
    if (assets <= 0 || scenarios <= 0) {
        detail::reject("assets and scenarios", "positive counts",
                       detail::format_value(static_cast<Real>(assets)));
    }
    const auto expected = static_cast<std::size_t>(scenarios) * static_cast<std::size_t>(assets);
    if (request.scenario_returns.size() != expected) {
        throw ValidationError(
            "quantrisk: CVaR needs scenario_returns to hold scenarios * assets entries");
    }
    for (const Real value : request.scenario_returns) {
        require_finite(value, "scenario return");
    }
    if (!(request.confidence > 0.0 && request.confidence < 1.0)) {
        detail::reject("confidence", "strictly inside (0, 1)",
                       detail::format_value(request.confidence));
    }
    if (request.target_return.has_value()) {
        if (request.expected_returns.size() != static_cast<std::size_t>(assets)) {
            throw ValidationError(
                "quantrisk: a CVaR target return needs expected_returns of `assets` entries");
        }
        for (const Real value : request.expected_returns) {
            require_finite(value, "expected return");
        }
    }
    if (scenarios < 2) {
        throw ValidationError(
            "quantrisk: CVaR over a single scenario is just that scenario's loss");
    }

    // x = [ w (assets) | a+ | a- | u (scenarios) | s (scenarios) | t-slack? ]
    const bool has_target = request.target_return.has_value();
    const Count alpha_column = assets;
    const Count alpha_minus_column = assets + 1;
    const Count u_column = assets + 2;
    const Count s_column = u_column + scenarios;
    const Count v_column = s_column + scenarios;
    const Count variables = v_column + (has_target ? 1 : 0);

    Count rows = 1 + scenarios + (has_target ? 1 : 0);
    std::vector<Real> objective(static_cast<std::size_t>(variables), 0.0);
    objective[static_cast<std::size_t>(alpha_column)] = 1.0;
    objective[static_cast<std::size_t>(alpha_minus_column)] = -1.0;
    const Real tail_weight = 1.0 / ((1.0 - request.confidence) * static_cast<Real>(scenarios));
    for (Count i = 0; i < scenarios; ++i) {
        objective[static_cast<std::size_t>(u_column + i)] = tail_weight;
    }

    std::vector<Real> matrix(static_cast<std::size_t>(rows * variables), 0.0);
    auto set_at = [&](const Count row, const Count column, const Real value) {
        matrix[static_cast<std::size_t>(row * variables + column)] = value;
    };
    std::vector<Real> rhs(static_cast<std::size_t>(rows), 0.0);

    for (Count j = 0; j < assets; ++j) {
        set_at(0, j, 1.0);
    }
    rhs[0] = 1.0;

    for (Count i = 0; i < scenarios; ++i) {
        const Count row = 1 + i;
        for (Count j = 0; j < assets; ++j) {
            set_at(row, j, request.scenario_returns[static_cast<std::size_t>(i * assets + j)]);
        }
        set_at(row, alpha_column, 1.0);
        set_at(row, alpha_minus_column, -1.0);
        set_at(row, u_column + i, 1.0);
        set_at(row, s_column + i, -1.0);
    }

    if (has_target) {
        const Count row = 1 + scenarios;
        for (Count j = 0; j < assets; ++j) {
            set_at(row, j, request.expected_returns[static_cast<std::size_t>(j)]);
        }
        set_at(row, v_column, -1.0);
        rhs[static_cast<std::size_t>(row)] = *request.target_return;
    }

    const LinearProgramResult lp = solve_linear_program(objective, matrix, rhs, variables, rows);
    solution.pivots = lp.pivots;
    solution.solved = lp.status == LpStatus::Optimal;
    solution.status = lp.status == LpStatus::Optimal      ? "optimal"
                      : lp.status == LpStatus::Infeasible ? "infeasible"
                      : lp.status == LpStatus::Unbounded  ? "unbounded"
                                                          : "numerical failure";
    if (!solution.solved) {
        solution.note = "linear program did not reach a certified optimum (" + lp.note + ")";
        solution.weights.assign(static_cast<std::size_t>(assets),
                                std::numeric_limits<Real>::quiet_NaN());
        solution.alpha = std::numeric_limits<Real>::quiet_NaN();
        solution.cvar = std::numeric_limits<Real>::quiet_NaN();
        solution.recomputed_cvar = solution.cvar;
        return solution;
    }

    solution.weights.assign(lp.values.begin(), lp.values.begin() + assets);
    solution.alpha = lp.values[static_cast<std::size_t>(alpha_column)] -
                     lp.values[static_cast<std::size_t>(alpha_minus_column)];

    // Evaluate the objective from its definition, from the weights and alpha alone.
    // The simplex's own tableau is not consulted, so agreement is a check on the
    // formulation as well as on the arithmetic.
    Real tail_total = 0.0;
    for (Count i = 0; i < scenarios; ++i) {
        Real loss = 0.0;
        for (Count j = 0; j < assets; ++j) {
            loss -= request.scenario_returns[static_cast<std::size_t>(i * assets + j)] *
                    solution.weights[static_cast<std::size_t>(j)];
        }
        tail_total += std::max(Real{0.0}, loss - solution.alpha);
    }
    solution.recomputed_cvar = solution.alpha + tail_weight * tail_total;
    solution.cvar = lp.objective;

    solution.budget_residual =
        std::abs(std::accumulate(solution.weights.begin(), solution.weights.end(), 0.0) - 1.0);
    solution.weight_bound_violation = 0.0;
    for (const Real weight : solution.weights) {
        solution.weight_bound_violation = std::max(solution.weight_bound_violation, -weight);
    }
    if (has_target) {
        Real expected = 0.0;
        for (Count j = 0; j < assets; ++j) {
            expected += request.expected_returns[static_cast<std::size_t>(j)] *
                        solution.weights[static_cast<std::size_t>(j)];
        }
        solution.target_residual = std::max(Real{0.0}, *request.target_return - expected);
    }
    const Real definition_gap = std::abs(solution.cvar - solution.recomputed_cvar);
    solution.certified = lp.status == LpStatus::Optimal && solution.budget_residual <= 1.0e-9 &&
                         solution.weight_bound_violation <= 1.0e-9 &&
                         solution.target_residual <= 1.0e-9 &&
                         definition_gap <= 1.0e-9 * std::max(1.0, std::abs(solution.cvar));
    solution.note = "Rockafellar-Uryasev linear program, confidence " +
                    detail::format_value(request.confidence) + ", " + std::to_string(scenarios) +
                    " scenarios, alpha reported as the optimised VaR level; " + lp.note +
                    (solution.certified
                         ? "; the objective was re-evaluated from the definition and agrees to " +
                               detail::format_value(definition_gap)
                         : "; the re-evaluated objective did NOT agree, so this is not certified");
    return solution;
}

} // namespace quantrisk::portfolio
