#pragma once

#include <span>
#include <string>
#include <vector>

#include "quantrisk/core/types.hpp"

namespace quantrisk::portfolio {

/// Covariance estimate plus the provenance of that estimate.
///
/// Every estimator here builds the matrix from outer products, so symmetry is a
/// property of the arithmetic rather than something a caller has to trust. The
/// matrix travels as a flat row-major vector instead of an Eigen type: the public
/// surface, and therefore the Python bindings, must not depend on which
/// linear-algebra library the core happens to use.
struct CovarianceEstimate {
    Count assets = 0;
    Count observations = 0;
    std::vector<Real> values;       ///< row-major, `assets * assets`
    std::string estimator;          ///< "sample" | "ewma" | "ledoit_wolf_shrinkage"
    Real decay = 0.0;               ///< EWMA lambda, else 0
    Real half_life = 0.0;           ///< EWMA half-life in observations, else 0
    Real shrinkage_intensity = 0.0; ///< delta of the shrinkage estimator, else 0
    Real target_scale = 0.0;        ///< mu in the "mu * I" shrinkage target, else 0
    /// Measured spectrum, used to state what the matrix can actually be used for.
    Real largest_eigenvalue = 0.0;
    Real smallest_eigenvalue = 0.0;
    bool positive_semidefinite = false; ///< smallest >= -kPositiveSemidefiniteTolerance * largest
    std::string note;
};

/// Relative tolerance for calling a measured spectrum non-negative. An absolute
/// threshold would be meaningless across matrices whose scale spans orders of
/// magnitude, which is exactly what portfolio covariances do.
inline constexpr Real kPositiveSemidefiniteTolerance = 1.0e-12;

/// Condition number above which an estimate is labelled ill-conditioned. Eight
/// orders of magnitude already costs half of double precision's ~16 digits, so
/// this is the point where a warning is owed rather than a judgement call.
inline constexpr Real kIllConditionedThreshold = 1.0e8;

/// Condition number above which a linear solve is *refused*. Labeling and refusing
/// are deliberately different bars: a badly conditioned but usable matrix should
/// still solve, while one this ill-conditioned leaves too few accurate digits for
/// its answer to mean anything. A "flat" asset is the trigger case — its variance
/// comes out around 1e-35 rather than exactly zero, because the sample mean of
/// repeated identical values is not itself exact, so an Eigen pivot test alone
/// happily reports success and returns weights of order 1e34.
inline constexpr Real kSolveRefusalThreshold = 1.0e12;

/// @name Estimators
/// Input is always a row-major `observations * assets` return matrix, one row per
/// observation with the **oldest first** — the layout `risk::linear_pnl` already
/// documents. EWMA weights decay with recency, so the ordering is part of the
/// contract, not a detail.
/// @{

/// Unbiased (divisor `n - 1`) sample covariance. This is the canonical
/// implementation; `risk::sample_covariance` is the frozen Phase 5 entry point and
/// returns this matrix's flat values.
[[nodiscard]] CovarianceEstimate sample_covariance(std::span<const Real> returns_rows, Count assets,
                                                   Count observations);

/// RiskMetrics-style exponentially weighted covariance, **about zero**:
/// weights proportional to `lambda^(T-1-t)` on observation `t` (newest gets 1),
/// normalised to sum to one, applied to `x_t x_t^T`. No mean is subtracted, because
/// the estimator is meant for short windows and daily returns whose weighted mean
/// is mostly sampling noise. `half_life = ln(0.5) / ln(lambda)`; `lambda = 1`
/// degenerates to equal weights and reports an infinite half-life.
[[nodiscard]] CovarianceEstimate ewma_covariance(std::span<const Real> returns_rows, Count assets,
                                                 Count observations, Real lambda);

/// Ledoit & Wolf (2004) linear shrinkage toward `mu * I`, `mu = tr(S) / p`, with the
/// closed-form optimal intensity `delta = min(b^2, d^2) / d^2`. Follows the paper's
/// own normalisation, which forms `S` with divisor `T` rather than `T - 1`: mixing an
/// unbiased `S` into that derivation would change the estimator being validated.
[[nodiscard]] CovarianceEstimate shrinkage_covariance(std::span<const Real> returns_rows,
                                                      Count assets, Count observations);

/// @}

/// @name Matrix helpers used by the optimisers and the robustness suite
/// @{

/// Eigenvalues of a symmetric matrix, ascending.
[[nodiscard]] std::vector<Real> eigenvalues(const CovarianceEstimate &covariance);

/// Same spectrum from a flat row-major matrix, for callers holding a Σ directly.
[[nodiscard]] std::vector<Real> eigenvalues(std::span<const Real> symmetric, Count assets);

/// `largest / smallest` of the absolute spectrum, so it is infinite only when a
/// zero eigenvalue is measured exactly — a rank-deficient sample typically returns
/// 1e18 rather than infinity, which says the same practical thing. The number that
/// predicts how badly a solve will amplify input error.
[[nodiscard]] Real condition_number(const CovarianceEstimate &covariance);

/// Solve `Sigma x = b` for a symmetric positive-definite Σ.
///
/// Returns `solved == false` with NaN weights, rather than a plausible answer, when
/// Σ is not positive definite: a zero-variance asset makes it singular, and a solver
/// that "worked" on such a matrix would be reporting noise as an optimal portfolio.
struct LinearSolve {
    std::vector<Real> values;
    bool solved = false;
    std::string note;
};

[[nodiscard]] LinearSolve solve(std::span<const Real> symmetric, Count assets,
                                std::span<const Real> right_hand_side);

/// @}

} // namespace quantrisk::portfolio
