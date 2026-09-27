#include "quantrisk/portfolio/risk_parity.hpp"

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

/// Relative gap below which the equal-contribution identity is considered met.
/// Deliberately far above machine epsilon: the iteration is a descent method, so
/// claiming agreement at 1e-16 would report convergence the arithmetic has not
/// actually reached.
constexpr Real kContributionTolerance = 1.0e-9;
constexpr Real kStepTolerance = 1.0e-15;
constexpr Count kMaxCycles = 10'000;

[[nodiscard]] Eigen::Index at(const Count value) { return static_cast<Eigen::Index>(value); }

[[nodiscard]] RiskParitySolution descend(const Matrix &sigma, const Count assets,
                                         const Vector &start, const std::string &origin) {
    RiskParitySolution solution;
    solution.assets = assets;

    Vector marginal = Vector::Zero(assets); // (Sigma w)_i, kept current
    Vector weights = start;
    Real variance = 0.0;
    Real previous_step = std::numeric_limits<Real>::infinity();
    bool zero_variance = false;

    for (Count cycle = 0; cycle <= kMaxCycles; ++cycle) {
        solution.cycles = cycle;
        marginal = sigma * weights;
        variance = static_cast<Real>(weights.transpose() * marginal);
        if (!(variance > 0.0)) {
            zero_variance = true;
            break;
        }
        // At the optimum every asset satisfies w_i (Sigma w)_i = c, and summing
        // over i gives n c = w' Sigma w, so c is refreshed from the current
        // portfolio rather than carried as a parameter of the method.
        const Real budget = variance / static_cast<Real>(assets);
        Real step = 0.0;
        for (Count i = 0; i < assets; ++i) {
            const Real own = sigma(at(i), at(i));
            if (!(own > 0.0)) {
                zero_variance = true;
                break;
            }
            // own * w_i^2 + b_i * w_i - budget = 0, where b_i is the covariance of
            // asset i with everything else. The product of the roots is
            // -budget / own < 0, so exactly one root is positive: the update can
            // never produce a negative weight, and no projection step is needed.
            const Real coupled = marginal(at(i)) - own * weights(at(i));
            const Real disc = coupled * coupled + 4.0 * own * budget;
            const Real updated = (-coupled + std::sqrt(disc)) / (2.0 * own);
            step = std::max(step, std::abs(updated - weights(at(i))));
            marginal += sigma.col(at(i)) * (updated - weights(at(i)));
            weights(at(i)) = updated;
        }
        if (zero_variance) {
            break;
        }
        const Real total = weights.sum();
        if (!(total > 0.0)) {
            break;
        }
        weights /= total;
        if (step <= kStepTolerance * std::max(Real{1.0}, weights.maxCoeff())) {
            previous_step = step;
            ++solution.cycles;
            break;
        }
        previous_step = step;
    }

    marginal = sigma * weights;
    variance = static_cast<Real>(weights.transpose() * marginal);
    Eigen::SelfAdjointEigenSolver<Matrix> spectrum(sigma);
    const Real smallest = spectrum.info() == Eigen::Success
                              ? static_cast<Real>(spectrum.eigenvalues().minCoeff())
                              : std::numeric_limits<Real>::quiet_NaN();

    solution.weights = std::vector<Real>(weights.data(), weights.data() + weights.size());
    solution.variance = variance;
    solution.volatility = std::sqrt(std::max(Real{0.0}, variance));
    solution.contributions.resize(static_cast<std::size_t>(assets));
    solution.max_contribution_gap = 0.0;
    const Real equal = 1.0 / static_cast<Real>(assets);
    for (Count i = 0; i < assets; ++i) {
        const Real share = variance > 0.0
                               ? static_cast<Real>(weights(at(i)) * marginal(at(i))) / variance
                               : std::numeric_limits<Real>::quiet_NaN();
        solution.contributions[static_cast<std::size_t>(i)] = share;
        solution.max_contribution_gap =
            std::max(solution.max_contribution_gap, std::abs(share - equal) / equal);
    }
    solution.converged =
        !zero_variance && variance > 0.0 && solution.max_contribution_gap <= kContributionTolerance;
    solution.positive_definite = smallest > 0.0;
    solution.note = "cyclic coordinate descent on 1/2 w'Sigma w - c sum log(w_i), c refreshed as "
                    "w'Sigma w / n; start = " +
                    origin;
    if (zero_variance) {
        solution.note +=
            "; NOT solved: an asset has zero variance, so log(w_i) is undefined for it "
            "and equal risk contribution is not a meaningful requirement (it would "
            "contribute nothing however large its weight)";
    } else if (solution.converged) {
        solution.note += "; the equal-contribution identity was verified on the result";
    } else {
        solution.note += "; the identity did NOT hold to tolerance within " +
                         std::to_string(kMaxCycles) + " cycles (last step " +
                         detail::format_value(previous_step) +
                         "), so this is reported as unconverged rather than as a solution";
    }
    if (!solution.positive_definite) {
        solution.note += "; the covariance is not positive definite (smallest eigenvalue " +
                         detail::format_value(smallest) +
                         "), which is admissible for risk parity but worth knowing";
    }
    return solution;
}

[[nodiscard]] Matrix read(std::span<const Real> covariance, const Count assets) {
    if (assets <= 0) {
        detail::reject("assets", "a positive count", detail::format_value(assets));
    }
    const auto expected = static_cast<std::size_t>(assets) * static_cast<std::size_t>(assets);
    if (covariance.size() != expected) {
        throw ValidationError("quantrisk: risk parity needs assets * assets covariance entries");
    }
    for (const Real value : covariance) {
        require_finite(value, "covariance entry");
    }
    return Matrix(Eigen::Map<const RowMajorMatrix>(covariance.data(), at(assets), at(assets)));
}

} // namespace

RiskParitySolution risk_parity(const std::span<const Real> covariance, const Count assets) {
    const Matrix sigma = read(covariance, assets);
    // Inverse-volatility start: the classic seeding rule, and cheap.
    Vector start(assets);
    for (Count i = 0; i < assets; ++i) {
        const Real own = sigma(at(i), at(i));
        start(at(i)) = own > 0.0 ? 1.0 / std::sqrt(own) : 1.0;
    }
    start /= start.sum();
    return descend(sigma, assets, start, "inverse volatility");
}

RiskParitySolution risk_parity(const std::span<const Real> covariance, const Count assets,
                               const std::span<const Real> budget) {
    const Matrix sigma = read(covariance, assets);
    if (static_cast<std::size_t>(assets) != budget.size()) {
        throw ValidationError("quantrisk: the starting weights must have `assets` entries");
    }
    for (const Real value : budget) {
        require_finite(value, "starting weight");
    }
    Vector start = Eigen::Map<const Vector>(budget.data(), at(assets));
    if (start.minCoeff() <= 0.0) {
        throw ValidationError(
            "quantrisk: risk parity needs strictly positive starting weights, since the "
            "objective contains log(w_i) for every asset");
    }
    start /= start.sum();
    return descend(sigma, assets, start, "caller supplied");
}

} // namespace quantrisk::portfolio
