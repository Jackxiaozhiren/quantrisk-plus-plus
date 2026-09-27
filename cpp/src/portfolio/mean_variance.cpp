#include "quantrisk/portfolio/mean_variance.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <set>
#include <vector>

#include <Eigen/Dense>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/risk/measures.hpp"

namespace quantrisk::portfolio {

namespace {

using Matrix = Eigen::Matrix<Real, Eigen::Dynamic, Eigen::Dynamic>;
using RowMajorMatrix = Eigen::Matrix<Real, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>;
using Vector = Eigen::Matrix<Real, Eigen::Dynamic, 1>;
using IndexVector = std::vector<Count>;

/// Relative slack for every "is this constraint satisfied" test, always
/// multiplied by the problem's own scale. Variances near 1e-4 and returns near
/// 1e-2 make an absolute threshold meaningless. 1e-9 is well above single-step
/// rounding (so it does not fire on noise) and far below any error that would
/// change a portfolio.
constexpr Real kKktTolerance = 1.0e-9;

/// Eigenvalues below this fraction of the largest are treated as zero when a
/// covariance block is inverted. Twelve orders is past what double precision can
/// carry through a solve, so a retained direction would add rounding noise rather
/// than information.
constexpr Real kRankTolerance = 1.0e-12;

[[nodiscard]] Eigen::Index at(const Count value) { return static_cast<Eigen::Index>(value); }

[[nodiscard]] Matrix to_matrix(const std::span<const Real> flat, const Count size) {
    return Matrix(Eigen::Map<const RowMajorMatrix>(flat.data(), at(size), at(size)));
}

[[nodiscard]] Vector to_vector(const std::span<const Real> flat) {
    return Eigen::Map<const Vector>(flat.data(), at(static_cast<Count>(flat.size())));
}

[[nodiscard]] Real matrix_scale(const Matrix &sigma) {
    return std::max(Real{1.0}, static_cast<Real>(sigma.lpNorm<Eigen::Infinity>()));
}

[[nodiscard]] Real tolerance_for(const Matrix &sigma) {
    return kKktTolerance * matrix_scale(sigma);
}

/// Symmetric solve with an explicit rank cut.
///
/// Portfolio covariances are regularly singular, and the important case is not a
/// failure: an asset with zero variance has an exactly optimal role (hold only
/// that asset), so refusing to solve would be wrong. Directions whose eigenvalue
/// is negligible against the largest are dropped from the inverse — the standard
/// pseudo-inverse treatment — and the number dropped is reported, so nobody can
/// mistake the result for an exact factorisation. The KKT certificate afterwards
/// is what establishes whether the answer is optimal for the real problem.
struct RankSolve {
    bool ok = false;
    Count dropped = 0;
    Eigen::SelfAdjointEigenSolver<Matrix> spectrum;
    Vector reciprocal; ///< 1/eigenvalue where kept, 0 where dropped

    explicit RankSolve(const Matrix &symmetric) {
        spectrum.compute(symmetric);
        const Vector values = spectrum.eigenvalues();
        reciprocal = Vector::Zero(values.size());
        const Real largest = values.cwiseAbs().maxCoeff();
        if (!(largest > 0.0)) {
            // All-zero block: its pseudo-inverse is exactly the all-zero matrix.
            dropped = static_cast<Count>(values.size());
            ok = true;
            return;
        }
        const Real cut = kRankTolerance * largest;
        for (Count i = 0; i < values.size(); ++i) {
            if (std::abs(values(at(i))) > cut) {
                reciprocal(at(i)) = 1.0 / values(at(i));
            } else {
                ++dropped;
            }
        }
        ok = true;
    }

    [[nodiscard]] Matrix solve(const Matrix &right_hand_side) const {
        // `Matrix`, deliberately not `Vector`: the right-hand side can carry several
        // columns (one per equality constraint), and assigning a multi-column product
        // to Eigen's column-vector type is not a compile error when both extents are
        // dynamic -- it silently writes past the buffer and returns denormal garbage.
        const Matrix rotated = spectrum.eigenvectors().transpose() * right_hand_side;
        return spectrum.eigenvectors() * (reciprocal.asDiagonal() * rotated);
    }
};

/// min 1/2 w'Sigma w subject to A'w = b, with w_i = 0 outside `support`.
///
/// Eliminating the zeroed coordinates makes this a small linear system, so the
/// solution inside a fixed support is exact rather than iterated. The search is
/// only over *which* support is right.
struct SupportSolve {
    Vector weights;     ///< length `assets`, zero outside the support
    Vector multipliers; ///< one entry per equality constraint
    Count truncated_directions = 0;
    bool ok = false;
    std::string reason;
};

[[nodiscard]] SupportSolve solve_on_support(const Matrix &sigma, const Matrix &a, const Vector &b,
                                            const IndexVector &support) {
    SupportSolve result;
    const Count assets = static_cast<Count>(sigma.rows());
    const Count size = static_cast<Count>(support.size());
    const Count constraints = static_cast<Count>(a.cols());
    result.weights = Vector::Zero(assets);
    result.multipliers = Vector::Zero(constraints);
    if (size < constraints) {
        result.reason = "fewer assets in the support than equality constraints, so the constraints "
                        "cannot all be met";
        return result;
    }

    // The saddle-point (KKT) system of the equality-constrained problem:
    //     [Sigma_SS  A_S ] [ w_S ]   [ 0 ]
    //     [ A_S'     0   ] [ lambda ] = [ b ]
    // Solved directly rather than through the normal equations w = Sigma^-1 A lambda,
    // because a singular covariance is exactly the case that matters here. Forming
    // Sigma^-1 would return the minimum-*norm* stationary point and miss the optimum:
    // with a flat asset, the normal equations put everything on the risky one while
    // this system returns the true answer of holding the flat asset at zero variance.
    const Count dimension = size + constraints;
    Matrix kkt = Matrix::Zero(dimension, dimension);
    for (Count i = 0; i < size; ++i) {
        const Count row = support[static_cast<std::size_t>(i)];
        for (Count j = 0; j < size; ++j) {
            kkt(at(i), at(j)) = sigma(at(row), at(support[static_cast<std::size_t>(j)]));
        }
        for (Count k = 0; k < constraints; ++k) {
            kkt(at(i), at(size + k)) = a(at(row), at(k));
            kkt(at(size + k), at(i)) = a(at(row), at(k));
        }
    }
    Vector right_hand_side = Vector::Zero(dimension);
    for (Count k = 0; k < constraints; ++k) {
        right_hand_side(at(size + k)) = b(k);
    }

    const RankSolve factor(kkt);
    result.truncated_directions = factor.dropped;
    const Vector solution = factor.solve(right_hand_side);
    const Vector active_weights = solution.head(size);
    // Sign convention, stated because getting it backwards is invisible in the
    // weights and fatal in the certificate: this system solves
    // Sigma w + A lambda_kkt = 0, while `certify` documents
    // nu = Sigma w - A lambda and needs nu to vanish on the support. So the
    // multipliers handed out are -lambda_kkt.
    result.multipliers = (-solution.tail(constraints)).eval();
    for (Count i = 0; i < size; ++i) {
        result.weights(at(support[static_cast<std::size_t>(i)])) = active_weights(at(i));
    }
    // Rank truncation can leave the equalities unmet (redundant constraints); say so
    // rather than hand back a point that does not solve the problem asked.
    const Real equality_slack = (kkt * solution - right_hand_side).lpNorm<Eigen::Infinity>();
    if (equality_slack >
        kKktTolerance * std::max(Real{1.0}, right_hand_side.lpNorm<Eigen::Infinity>())) {
        result.reason = "the KKT system is degenerate on this support and its equalities cannot be "
                        "met to the working tolerance";
        return result;
    }
    result.ok = true;
    return result;
}

/// Karush-Kuhn-Tucker conditions for
///     min 1/2 w'Sigma w  s.t.  A'w = b,  w >= 0.
///
/// Stationarity gives nu = Sigma w - A lambda, which must vanish on the support
/// (complementarity) and be non-negative outside it. The problem is convex, so
/// these conditions are necessary *and sufficient*: satisfying them proves global
/// optimality, which is why an answer here does not depend on a benchmark to be
/// believed.
struct Certificate {
    /// True when the *equality* constraints hold on this support. A violated bound
    /// is not an infeasibility here: a negative weight is the signal telling the
    /// search which asset to drop next, so the two must not be conflated.
    bool equalities_satisfied = false;
    bool dual_feasible = false;
    Real budget_residual = 0.0;
    Real target_residual = 0.0;
    Real bound_violation = 0.0;
    Real complementarity_residual = 0.0;
    Real tolerance = 0.0;
    Count worst_dual_index = -1;
    Real worst_dual_value = 0.0;
};

[[nodiscard]] Certificate certify(const Matrix &sigma, const Matrix &a, const Vector &b,
                                  const SupportSolve &solve, const std::vector<bool> &in_support,
                                  const bool long_only) {
    Certificate certificate;
    const Count assets = static_cast<Count>(sigma.rows());
    const Count constraints = static_cast<Count>(a.cols());
    const Real tolerance = tolerance_for(sigma);
    certificate.tolerance = tolerance;

    bool feasible = true;
    for (Count k = 0; k < constraints; ++k) {
        const Real residual = std::abs(a.col(k).transpose() * solve.weights - b(k));
        const Real slack = kKktTolerance * std::max(Real{1.0}, std::abs(b(k)));
        if (k == 0) {
            certificate.budget_residual = residual;
        } else {
            certificate.target_residual = std::max(certificate.target_residual, residual);
        }
        feasible = feasible && residual <= slack;
    }
    certificate.bound_violation =
        long_only ? std::max(Real{0.0}, -static_cast<Real>(solve.weights.minCoeff())) : 0.0;
    certificate.equalities_satisfied = feasible;

    const Vector gradient = sigma * solve.weights - a * solve.multipliers;
    certificate.worst_dual_value = 0.0;
    for (Count i = 0; i < assets; ++i) {
        const Real dual = gradient(at(i));
        if (in_support[static_cast<std::size_t>(i)]) {
            certificate.complementarity_residual =
                std::max(certificate.complementarity_residual, std::abs(dual));
        } else if (long_only && dual < -tolerance && dual < certificate.worst_dual_value) {
            certificate.worst_dual_value = dual;
            certificate.worst_dual_index = i;
        }
    }
    certificate.dual_feasible =
        certificate.worst_dual_index < 0 && certificate.complementarity_residual <= tolerance;
    return certificate;
}

struct ActiveSetResult {
    SupportSolve solve;
    Certificate certificate;
    IndexVector support;
    std::string method;
    Count iterations = 0;
    Count diagnostic_constraints = 0;
};

/// Equality solve plus the active-set search over non-negativity.
///
/// Each step either drops the held asset that went most negative (its
/// non-negativity constraint is the one being fought) or admits the excluded asset
/// whose negative multiplier says adding it would lower the objective. Either move
/// is a pivot on the support, and the loop stops when the KKT certificate holds.
/// A visit set detects the cycling that a pivot rule without anti-cycling allows,
/// and a hard iteration cap bounds the work; if neither rescue produces a
/// certificate the caller is told so rather than being handed a quiet answer.
[[nodiscard]] ActiveSetResult minimise(const Matrix &sigma, const Matrix &a, const Vector &b,
                                       const bool long_only) {
    ActiveSetResult result;
    const Count assets = static_cast<Count>(sigma.rows());
    const Count constraints = static_cast<Count>(a.cols());
    result.diagnostic_constraints = constraints;
    const Real tolerance = tolerance_for(sigma);

    IndexVector support(static_cast<std::size_t>(assets));
    std::iota(support.begin(), support.end(), Count{0});
    std::vector<bool> in_support(static_cast<std::size_t>(assets), true);

    std::set<IndexVector> visited;
    const Count cap = 8 * assets + 40;
    for (result.iterations = 0; result.iterations <= cap; ++result.iterations) {
        SupportSolve solve = solve_on_support(sigma, a, b, support);
        if (!solve.ok) {
            result.solve = solve;
            result.support = support;
            result.method = "equality kkt solve (failed)";
            return result;
        }
        Certificate certificate = certify(sigma, a, b, solve, in_support, long_only);
        result.solve = solve;
        result.certificate = certificate;
        result.support = support;

        if (!certificate.equalities_satisfied) {
            result.method = "active set: no support satisfied the equality constraints";
            return result;
        }
        if (!long_only) {
            result.method = "equality kkt solve (no bound constraints)";
            certificate.dual_feasible = true;
            result.certificate = certificate;
            return result;
        }
        if (certificate.dual_feasible && certificate.bound_violation <= tolerance) {
            result.method = "active set with kkt certificate";
            return result;
        }

        IndexVector next = support;
        if (certificate.worst_dual_index >= 0) {
            // Admit the excluded asset that wants to be in.
            next.push_back(certificate.worst_dual_index);
            std::sort(next.begin(), next.end());
        } else {
            Count worst = -1;
            Real worst_value = 0.0;
            for (const Count index : support) {
                const Real value = solve.weights(at(index));
                if (worst < 0 || value < worst_value) {
                    worst_value = value;
                    worst = index;
                }
            }
            if (worst < 0) {
                result.method = "active set: nothing left to drop or admit";
                return result;
            }
            next.erase(std::remove(next.begin(), next.end(), worst), next.end());
        }
        if (static_cast<Count>(next.size()) < constraints) {
            result.method = "active set exhausted: no support of sufficient size remains";
            return result;
        }
        if (!visited.insert(next).second) {
            result.method = "active set cycling detected between supports; the KKT certificate "
                            "reported here is the best point reached, not a proof";
            certificate.dual_feasible = false;
            result.certificate = certificate;
            return result;
        }
        support = next;
        in_support.assign(static_cast<std::size_t>(assets), false);
        for (const Count index : support) {
            in_support[static_cast<std::size_t>(index)] = true;
        }
    }
    result.method = "active set stopped at the iteration cap";
    result.certificate.dual_feasible = false;
    return result;
}

[[nodiscard]] std::pair<Matrix, Vector> validated(const OptimizerInputs &inputs) {
    if (inputs.assets <= 0) {
        detail::reject("assets", "a positive count", detail::format_value(inputs.assets));
    }
    const auto square =
        static_cast<std::size_t>(inputs.assets) * static_cast<std::size_t>(inputs.assets);
    if (inputs.covariance.size() != square) {
        throw ValidationError("quantrisk: the covariance needs assets * assets entries");
    }
    for (const Real value : inputs.covariance) {
        require_finite(value, "covariance entry");
    }
    if (!inputs.expected_returns.empty() &&
        inputs.expected_returns.size() != static_cast<std::size_t>(inputs.assets)) {
        throw ValidationError("quantrisk: expected returns must have exactly `assets` entries");
    }
    if (inputs.scenario_count > 0) {
        const auto expected = static_cast<std::size_t>(inputs.scenario_count) *
                              static_cast<std::size_t>(inputs.assets);
        if (inputs.scenario_returns.size() != expected) {
            throw ValidationError(
                "quantrisk: scenario returns must hold scenario_count * assets entries");
        }
        for (const Real value : inputs.scenario_returns) {
            require_finite(value, "scenario return");
        }
    }
    return {to_matrix(std::span<const Real>(inputs.covariance), inputs.assets),
            inputs.expected_returns.empty() ? Vector::Zero(inputs.assets)
                                            : to_vector(inputs.expected_returns)};
}

[[nodiscard]] PortfolioSolution describe(const OptimizerInputs &inputs,
                                         const OptimizationRequest &request,
                                         const ActiveSetResult &active, const Matrix &sigma,
                                         const Vector &mu, const std::string &extra_note) {
    PortfolioSolution solution;
    solution.assets = inputs.assets;
    solution.weights = std::vector<Real>(active.solve.weights.data(),
                                         active.solve.weights.data() + active.solve.weights.size());

    const Count assets = inputs.assets;
    const Vector weights = to_vector(solution.weights);
    solution.variance = static_cast<Real>(weights.transpose() * sigma * weights);
    solution.volatility = std::sqrt(std::max(Real{0.0}, solution.variance));
    solution.budget_residual = active.certificate.budget_residual;
    solution.weight_bound_violation = active.certificate.bound_violation;
    solution.tolerance = active.certificate.tolerance;
    solution.feasible = active.solve.ok && active.certificate.equalities_satisfied &&
                        active.certificate.bound_violation <= active.certificate.tolerance;
    solution.verified_optimal = solution.feasible && active.certificate.dual_feasible;
    solution.method = active.method;
    solution.sharpe_ratio = std::numeric_limits<Real>::quiet_NaN();
    solution.value_at_risk = std::numeric_limits<Real>::quiet_NaN();
    solution.conditional_var = std::numeric_limits<Real>::quiet_NaN();

    if (!inputs.expected_returns.empty()) {
        solution.expected_return = static_cast<Real>(mu.transpose() * weights);
        if (request.target_return.has_value()) {
            solution.target_residual =
                std::max(Real{0.0}, *request.target_return - solution.expected_return);
            if (solution.target_residual > active.certificate.tolerance) {
                solution.feasible = false;
                solution.verified_optimal = false;
            }
        }
        if (request.risk_free_rate.has_value() && solution.volatility > 0.0) {
            solution.sharpe_ratio =
                (solution.expected_return - *request.risk_free_rate) / solution.volatility;
        }
    }

    if (inputs.scenario_count > 0) {
        std::vector<Real> portfolio_returns;
        portfolio_returns.reserve(static_cast<std::size_t>(inputs.scenario_count));
        for (Count s = 0; s < inputs.scenario_count; ++s) {
            Real total = 0.0;
            for (Count i = 0; i < assets; ++i) {
                total += inputs.scenario_returns[static_cast<std::size_t>(s * assets + i)] *
                         solution.weights[static_cast<std::size_t>(i)];
            }
            portfolio_returns.push_back(total);
        }
        solution.value_at_risk =
            risk::historical_var(portfolio_returns, request.cvar_confidence).value;
        solution.conditional_var =
            risk::historical_es(portfolio_returns, request.cvar_confidence).value;
    }

    std::string note = extra_note;

    if (active.solve.truncated_directions > 0) {
        note += "; the KKT system was rank-truncated by " +
                std::to_string(active.solve.truncated_directions) +
                " direction(s), which is the expected treatment for a singular or "
                "degenerate covariance and is reported rather than hidden";
    }
    if (!active.solve.ok) {
        note = note.empty() ? active.solve.reason : note + "; " + active.solve.reason;
    }
    if (active.solve.ok && !active.certificate.dual_feasible) {
        note += "; the KKT certificate did NOT hold, so this point is reported as "
                "unverified rather than presented as optimal";
    }
    // An unreachable target still has an equality solution — it just needs short
    // positions to get there. `feasible` already says false and the residual already
    // carries the number, but the note is what ends up printed in a report, and a
    // reader of the note alone should not come away thinking they hold a long portfolio.
    if (active.certificate.bound_violation > active.certificate.tolerance) {
        note += "; the weight bounds are violated by " +
                std::to_string(active.certificate.bound_violation) +
                ", so no portfolio satisfying the constraints reaches the requested "
                "target and this answer is not investable as given";
    }
    solution.note = note;
    return solution;
}

} // namespace

PortfolioSolution minimum_variance(const OptimizerInputs &inputs,
                                   const OptimizationRequest &request) {
    auto [sigma, mu] = validated(inputs);
    const Count assets = inputs.assets;

    // Explicit column assignment, never comma-initialisation: Eigen fills a
    // column-major matrix in storage order, so `M << ones, mu` would interleave
    // the two constraints into garbage. That bug is silent except in the residuals.
    const Vector ones = Vector::Ones(assets);
    Matrix a(assets, 1);
    a.col(0) = ones;
    Vector b(1);
    b(0) = 1.0;

    std::string note;
    if (request.target_return.has_value() && inputs.expected_returns.empty()) {
        throw ValidationError(
            "quantrisk: a target return needs expected returns to constrain against");
    }

    ActiveSetResult active = minimise(sigma, a, b, request.long_only);
    note = "target return not requested; the minimum-variance portfolio alone is the answer";

    if (request.target_return.has_value()) {
        const Real free_return = static_cast<Real>(mu.transpose() * active.solve.weights);
        const bool satisfied = free_return >= *request.target_return - tolerance_for(sigma);
        if (satisfied) {
            note = "target return " + detail::format_value(*request.target_return) +
                   " is already met by the unconstrained minimum-variance portfolio at " +
                   detail::format_value(free_return) +
                   ", so the bound is inactive and the multipliers below ignore it";
        } else {
            Matrix with_target(assets, 2);
            with_target.col(0) = ones;
            with_target.col(1) = mu;
            Vector target_b(2);
            target_b(0) = 1.0;
            target_b(1) = *request.target_return;
            active = minimise(sigma, with_target, target_b, request.long_only);
            note = "target return " + detail::format_value(*request.target_return) +
                   " binds (the free portfolio returned " + detail::format_value(free_return) +
                   "), so it is imposed as an equality";
        }
    }
    return describe(inputs, request, active, sigma, mu, note);
}

std::vector<PortfolioSolution> efficient_frontier(const OptimizerInputs &inputs,
                                                  const std::span<const Real> targets,
                                                  const OptimizationRequest &request) {
    std::vector<PortfolioSolution> frontier;
    frontier.reserve(targets.size());
    for (const Real target : targets) {
        OptimizationRequest with_target = request;
        with_target.target_return = target;
        frontier.push_back(minimum_variance(inputs, with_target));
    }
    return frontier;
}

PortfolioSolution maximum_sharpe(const OptimizerInputs &inputs,
                                 const OptimizationRequest &request) {
    if (inputs.expected_returns.empty()) {
        throw ValidationError("quantrisk: maximising a Sharpe ratio needs expected returns");
    }
    const Real risk_free = request.risk_free_rate.value_or(0.0);
    auto [sigma, mu] = validated(inputs);

    // Bracket the frontier segment worth searching. The minimum-variance portfolio
    // is its left end; no long-only portfolio can return more than the best single
    // asset, which bounds the right end.
    OptimizationRequest base = request;
    base.risk_free_rate = risk_free;
    const PortfolioSolution lowest = minimum_variance(inputs, base);
    const Real lower = lowest.expected_return;
    const Real upper =
        *std::max_element(inputs.expected_returns.begin(), inputs.expected_returns.end());
    if (!(upper > lower)) {
        PortfolioSolution collapsed = lowest;
        collapsed.note =
            "every asset has the same expected return, so the frontier is a single point "
            "and the minimum-variance portfolio is trivially the best Sharpe";
        return collapsed;
    }

    // The frontier's variance is convex in the target return, so the Sharpe ratio
    // is unimodal along it and a ternary search narrows the bracket without needing
    // a derivative. Each evaluation is the §7 QP, so the reformulation is "search
    // over target returns", not "one more closed form".
    auto solution_at = [&](const Real target) {
        OptimizationRequest step = base;
        step.target_return = target;
        return minimum_variance(inputs, step);
    };

    PortfolioSolution best = lowest;
    Real lo = lower;
    Real hi = upper;
    Count evaluations = 0;
    for (Count step = 0; step < 60; ++step) {
        if (hi - lo <= 1.0e-12 * std::max(Real{1.0}, std::abs(upper))) {
            break;
        }
        const Real left = lo + (hi - lo) / 3.0;
        const Real right = hi - (hi - lo) / 3.0;
        const PortfolioSolution left_solution = solution_at(left);
        const PortfolioSolution right_solution = solution_at(right);
        evaluations += 2;
        const Real left_sharpe = left_solution.feasible && std::isfinite(left_solution.sharpe_ratio)
                                     ? left_solution.sharpe_ratio
                                     : -std::numeric_limits<Real>::infinity();
        const Real right_sharpe =
            right_solution.feasible && std::isfinite(right_solution.sharpe_ratio)
                ? right_solution.sharpe_ratio
                : -std::numeric_limits<Real>::infinity();
        if (left_sharpe > best.sharpe_ratio || !best.feasible) {
            best = left_solution;
        }
        if (right_sharpe > best.sharpe_ratio) {
            best = right_solution;
        }
        if (left_sharpe < right_sharpe) {
            lo = left;
        } else {
            hi = right;
        }
    }
    const std::string method_note =
        "max-Sharpe by ternary search along the efficient frontier (" +
        std::to_string(evaluations) +
        " QP evaluations). Maximising (mu'w - rf)/sqrt(w'Sigma w) is linear-fractional, "
        "not a quadratic program, so it is solved by searching over the target returns "
        "the §7 QP already produces; docs/mathematical_specification.md §7 requires that "
        "transformation to be stated rather than assumed.";
    best.note = best.note.empty() ? method_note : method_note + " " + best.note;
    best.method = best.method + " | frontier search";
    return best;
}

} // namespace quantrisk::portfolio
