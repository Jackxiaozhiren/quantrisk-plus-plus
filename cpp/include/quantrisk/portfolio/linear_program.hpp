#pragma once

#include <span>
#include <string>
#include <vector>

#include "quantrisk/core/types.hpp"

namespace quantrisk::portfolio {

/// A dense two-phase primal simplex for
///
///     minimise    c^T x   subject to   A x = b,   x >= 0.
///
/// This is the piece the CVaR optimiser needs: Rockafellar-Uryasev turns a
/// conditional-value-at-risk minimisation into a linear program once the losses
/// are linear in the weights (`docs/mathematical_specification.md` §8), and a
/// linear program needs a linear-programming solver rather than another QP hack.
///
/// Scope, stated rather than discovered by a caller: the tableau is dense and a
/// pivot costs O(rows * columns), so this is a reference implementation for
/// hundreds of scenarios, not a commercial solver for tens of thousands. The
/// measured cost is reported in the Phase 6 report.
enum class LpStatus {
    Optimal,
    Infeasible,
    Unbounded,
    NumericalFailure,
};

struct LinearProgramResult {
    LpStatus status = LpStatus::NumericalFailure;
    std::vector<Real> values;
    Real objective = 0.0;
    Count pivots = 0;
    Real residual = 0.0; ///< max_i |b_i - (A x)_i| / max(1, |b|_inf)
    Real dual_gap = 0.0; ///< reduced costs left on the table at the reported point
    std::string note;
};

/// Solve the equality-form program above. `b` need not be non-negative: rows are
/// flipped internally, and that bookkeeping stays inside the solver.
[[nodiscard]] LinearProgramResult solve_linear_program(std::span<const Real> objective,
                                                       std::span<const Real> constraint_rows,
                                                       std::span<const Real> rhs, Count variables,
                                                       Count constraints);

} // namespace quantrisk::portfolio
