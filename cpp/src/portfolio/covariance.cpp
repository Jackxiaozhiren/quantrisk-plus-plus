#include "quantrisk/portfolio/covariance.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <string>
#include <utility>

#include <Eigen/Dense>
#include <Eigen/Eigenvalues>

#include "quantrisk/core/validation.hpp"

namespace quantrisk::portfolio {

namespace {

using Matrix = Eigen::Matrix<Real, Eigen::Dynamic, Eigen::Dynamic>;
using Vector = Eigen::Matrix<Real, Eigen::Dynamic, 1>;
using RowMajorMatrix = Eigen::Matrix<Real, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>;

[[nodiscard]] Eigen::Index index(const Count value) { return static_cast<Eigen::Index>(value); }

[[nodiscard]] Matrix to_eigen(const std::span<const Real> flat, const Count size) {
    return Matrix(Eigen::Map<const RowMajorMatrix>(flat.data(), index(size), index(size)));
}

[[nodiscard]] std::vector<Real> to_flat(const Matrix &matrix) {
    RowMajorMatrix row_major = matrix;
    return std::vector<Real>(row_major.data(), row_major.data() + row_major.size());
}

/// Shared input contract: shape, finiteness, and the `observations x assets`
/// layout. Returns the sample as an Eigen matrix with one row per observation.
[[nodiscard]] Matrix read_sample(std::span<const Real> returns_rows, const Count assets,
                                 const Count observations) {
    if (assets <= 0) {
        detail::reject("assets", "a positive count", detail::format_value(assets));
    }
    if (observations <= 0) {
        detail::reject("observations", "a positive count", detail::format_value(observations));
    }
    const auto expected = static_cast<std::size_t>(assets) * static_cast<std::size_t>(observations);
    if (returns_rows.size() != expected) {
        throw ValidationError(
            "quantrisk: a covariance sample needs exactly assets * "
            "observations entries, got " +
            detail::format_value(static_cast<Real>(returns_rows.size())) + " for " +
            detail::format_value(static_cast<Real>(assets)) + " assets and " +
            detail::format_value(static_cast<Real>(observations)) + " observations");
    }
    for (const Real value : returns_rows) {
        require_finite(value, "return");
    }
    return Eigen::Map<const RowMajorMatrix>(returns_rows.data(), index(observations),
                                            index(assets));
}

[[nodiscard]] Real spectral_condition(const Eigen::Matrix<Real, Eigen::Dynamic, 1> &spectrum) {
    const Real largest = std::abs(spectrum.maxCoeff());
    const Real smallest = std::abs(spectrum.minCoeff());
    if (smallest <= 0.0) {
        return std::numeric_limits<Real>::infinity();
    }
    return largest / smallest;
}

/// Fill in the flat matrix and its measured spectrum.
///
/// The triangle is mirrored rather than trusted: Eigen's packed products can leave
/// `(i, j)` and `(j, i)` differing in the last bit, and an asymmetry that small is
/// invisible in the numbers yet breaks the self-adjoint eigensolver's assumption.
/// Calling the result symmetric should be a fact about the arithmetic, not a hope.
void finish(CovarianceEstimate &estimate, const Matrix &raw) {
    Matrix symmetric = raw;
    const Count n = estimate.assets;
    for (Count i = 0; i < n; ++i) {
        for (Count j = i + 1; j < n; ++j) {
            symmetric(index(j), index(i)) = symmetric(index(i), index(j));
        }
    }
    estimate.values = to_flat(symmetric);

    Eigen::SelfAdjointEigenSolver<Matrix> solver(symmetric);
    if (solver.info() != Eigen::Success) {
        throw ValidationError("quantrisk: the covariance eigensolver failed to converge");
    }
    const auto spectrum = solver.eigenvalues();
    estimate.largest_eigenvalue = static_cast<Real>(spectrum.maxCoeff());
    estimate.smallest_eigenvalue = static_cast<Real>(spectrum.minCoeff());
    const Real slack = kPositiveSemidefiniteTolerance * std::abs(estimate.largest_eigenvalue);
    estimate.positive_semidefinite = estimate.smallest_eigenvalue >= -slack;

    // State what the estimate can be used for, in the estimate itself. A caller who
    // never looks at the spectrum still cannot miss that a solve is unsafe here.
    if (!estimate.positive_semidefinite) {
        estimate.note += "; NOT positive semidefinite as estimated (the arithmetic should "
                         "make that impossible, so this is a bug report, not a tolerance)";
    } else if (estimate.smallest_eigenvalue <= slack) {
        estimate.note += "; singular or numerically rank-deficient (smallest eigenvalue "
                         "within tolerance of zero): do not invert this matrix, the "
                         "optimisers report failure rather than guess";
    } else if (spectral_condition(spectrum) > kIllConditionedThreshold) {
        estimate.note += "; condition number " +
                         detail::format_value(spectral_condition(spectrum)) + " exceeds " +
                         detail::format_value(kIllConditionedThreshold) +
                         ", so weights on this estimate are unstable under small "
                         "perturbations of the sample";
    }
}

} // namespace

CovarianceEstimate sample_covariance(std::span<const Real> returns_rows, const Count assets,
                                     const Count observations) {
    if (observations < 2) {
        detail::reject("observations", "at least 2 for an unbiased (divisor n - 1) covariance",
                       detail::format_value(observations));
    }
    const Matrix sample = read_sample(returns_rows, assets, observations);
    const Matrix centred = sample.rowwise() - sample.colwise().mean();
    const Matrix sigma = (centred.transpose() * centred) / static_cast<Real>(observations - 1);

    CovarianceEstimate estimate;
    estimate.assets = assets;
    estimate.observations = observations;
    estimate.estimator = "sample";
    estimate.note = "unbiased sample covariance, divisor n - 1, per-asset means subtracted";
    finish(estimate, sigma);
    return estimate;
}

CovarianceEstimate ewma_covariance(std::span<const Real> returns_rows, const Count assets,
                                   const Count observations, const Real lambda) {
    if (!(lambda > 0.0 && lambda <= 1.0)) {
        detail::reject("lambda", "in (0, 1] (the decay factor)", detail::format_value(lambda));
    }
    const Matrix sample = read_sample(returns_rows, assets, observations);

    // Newest observation is the last row, so its exponent is 0 and its weight is 1.
    Vector weights(index(observations));
    for (Count t = 0; t < observations; ++t) {
        weights(index(t)) = std::pow(lambda, static_cast<Real>(observations - 1 - t));
    }
    const Real total = weights.sum();
    if (!(total > 0.0)) {
        throw ValidationError(
            "quantrisk: the EWMA weight sum underflowed; raise lambda or shorten the sample");
    }
    weights /= total;

    CovarianceEstimate estimate;
    estimate.assets = assets;
    estimate.observations = observations;
    estimate.estimator = "ewma";
    estimate.decay = lambda;
    estimate.half_life =
        lambda == 1.0 ? std::numeric_limits<Real>::infinity() : std::log(0.5) / std::log(lambda);
    estimate.note = "exponentially weighted second moment about zero (no mean subtracted), newest "
                    "observation weight 1, normalised to sum to 1";
    // (X * sqrt(w))^T (X * sqrt(w)) is the weighted outer-product sum; scaling by the
    // square root keeps every partial product a genuine weighted covariance.
    const Matrix scaled = sample.cwiseProduct(weights.replicate(1, assets).cwiseSqrt().eval());
    finish(estimate, scaled.transpose() * scaled);
    return estimate;
}

CovarianceEstimate shrinkage_covariance(std::span<const Real> returns_rows, const Count assets,
                                        const Count observations) {
    if (observations < 2) {
        detail::reject("observations", "at least 2 to estimate a shrinkage intensity",
                       detail::format_value(observations));
    }
    const Matrix sample = read_sample(returns_rows, assets, observations);
    const Matrix centred = sample.rowwise() - sample.colwise().mean();
    const Real divisor = static_cast<Real>(observations);
    const Matrix sigma = (centred.transpose() * centred) / divisor;

    const Real dimension = static_cast<Real>(assets);
    const Real mu = sigma.trace() / dimension; // target scale: tr(S)/p
    const Matrix target = Matrix::Identity(index(assets), index(assets)) * mu;
    const Real d_squared = (sigma - target).squaredNorm() / dimension;

    // b_bar^2 = (1/T^2) sum_t ||x_t x_t^T - S||_F^2 / p, evaluated with
    // ||x x^T||_F^2 = (x^T x)^2 and x^T S x so no T p x p matrices are formed.
    Real b_bar_sum = 0.0;
    const Real sigma_norm = sigma.squaredNorm();
    for (Count t = 0; t < observations; ++t) {
        const Vector row = centred.row(index(t)).transpose();
        const Real fourth = row.squaredNorm();
        const Real quadratic_form = row.dot(sigma * row);
        b_bar_sum += fourth * fourth - 2.0 * quadratic_form + sigma_norm;
    }
    const Real b_bar_squared = b_bar_sum / (divisor * divisor) / dimension;
    const Real b_squared = std::min(b_bar_squared, d_squared);
    const Real delta = d_squared > 0.0 ? std::min<Real>(1.0, b_squared / d_squared) : 0.0;

    CovarianceEstimate estimate;
    estimate.assets = assets;
    estimate.observations = observations;
    estimate.estimator = "ledoit_wolf_shrinkage";
    estimate.shrinkage_intensity = delta;
    estimate.target_scale = static_cast<Real>(mu);
    estimate.note = "Ledoit-Wolf (2004) linear shrinkage toward tr(S)/p * I, divisor T as in the "
                    "paper's own derivation, intensity solved in closed form (not cross-validated)";
    if (d_squared <= 0.0) {
        estimate.note += "; the sample covariance is already exactly the scaled-identity "
                         "target, so the intensity is undefined and 0 is reported";
    }
    finish(estimate, delta * target + (1.0 - delta) * sigma);
    return estimate;
}

std::vector<Real> eigenvalues(const CovarianceEstimate &covariance) {
    return eigenvalues(std::span<const Real>(covariance.values), covariance.assets);
}

std::vector<Real> eigenvalues(std::span<const Real> symmetric, const Count assets) {
    const Matrix matrix = to_eigen(symmetric, assets);
    Eigen::SelfAdjointEigenSolver<Matrix> solver(matrix);
    if (solver.info() != Eigen::Success) {
        throw ValidationError("quantrisk: the eigensolver failed to converge");
    }
    const auto spectrum = solver.eigenvalues();
    return std::vector<Real>(spectrum.data(), spectrum.data() + spectrum.size());
}

Real condition_number(const CovarianceEstimate &covariance) {
    const Matrix matrix = to_eigen(std::span<const Real>(covariance.values), covariance.assets);
    Eigen::SelfAdjointEigenSolver<Matrix> solver(matrix);
    if (solver.info() != Eigen::Success) {
        throw ValidationError("quantrisk: the eigensolver failed to converge");
    }
    return spectral_condition(solver.eigenvalues());
}

LinearSolve solve(std::span<const Real> symmetric, const Count assets,
                  std::span<const Real> right_hand_side) {
    LinearSolve result;
    if (assets <= 0) {
        detail::reject("assets", "a positive count", detail::format_value(assets));
    }
    const Matrix matrix = to_eigen(symmetric, assets);
    if (right_hand_side.size() != static_cast<std::size_t>(assets)) {
        throw ValidationError("quantrisk: the right-hand side must have `assets` entries");
    }
    for (const Real value : right_hand_side) {
        require_finite(value, "right-hand side");
    }
    const Eigen::Map<const Eigen::Vector<Real, Eigen::Dynamic>> rhs(right_hand_side.data(),
                                                                    index(assets));

    // A successful factorisation is not the same thing as a usable one: Eigen's
    // pivot test only catches a non-positive pivot, and a numerically flat matrix
    // has positive pivots of the wrong order of magnitude. The reciprocal-condition
    // estimate is what says whether the answer will contain any accurate digits.
    const auto reject = [&](const std::string &reason) {
        result.values.assign(static_cast<std::size_t>(assets),
                             std::numeric_limits<Real>::quiet_NaN());
        result.note = reason;
        return result;
    };

    // Cholesky first: the cheapest exact route, and it *refuses* to run on a matrix
    // that is not positive definite, which is the failure mode that matters here.
    Eigen::LLT<Matrix> llt(matrix);
    if (llt.info() != Eigen::Success) {
        // Not positive definite. Report it rather than substituting a pseudo-inverse:
        // a least-norm solution to a singular portfolio problem answers a different
        // question, and callers must be able to tell the two apart.
        return reject(
            "not solved: the matrix is singular or indefinite, so no unique solution "
            "exists; the robustness suite covers the alternatives this call refuses to guess");
    }
    if (llt.rcond() < 1.0 / kSolveRefusalThreshold) {
        return reject("not solved: the matrix is numerically singular (condition number above " +
                      detail::format_value(kSolveRefusalThreshold) +
                      "), so a Cholesky solution would be rounding noise presented as an answer; "
                      "shrink the estimate or drop the degenerate asset");
    }
    result.values = to_flat(llt.solve(rhs));
    if (std::any_of(result.values.begin(), result.values.end(),
                    [](const Real value) { return !std::isfinite(value); })) {
        return reject("not solved: Cholesky reported success but produced non-finite values");
    }
    result.solved = true;
    result.note = "solved by Cholesky factorisation (matrix is positive definite)";
    return result;
}

} // namespace quantrisk::portfolio
