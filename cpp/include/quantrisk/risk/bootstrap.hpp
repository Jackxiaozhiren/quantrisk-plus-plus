#pragma once

#include <span>
#include <string>
#include <vector>

#include "quantrisk/core/rng.hpp"
#include "quantrisk/core/types.hpp"

namespace quantrisk {

/// Uncertainty for tail risk measures (docs/mathematical_specification.md §6).
///
/// A tail quantile estimated from `n` observations is a noisy statistic, so a
/// point estimate alone is not a defensible risk number. Bootstrap replicates
/// give the sampling distribution empirically:
///
/// - `iid_bootstrap_*` resamples single observations: valid when the series is
///   (approximately) independent.
/// - `moving_block_bootstrap_*` resamples contiguous blocks of length `L`,
///   preserving within-block dependence, which is what volatility clustering is.
///
/// Confidence bounds are the percentile method: the `alpha/2` and `1 - alpha/2`
/// empirical quantiles of the replicate distribution. That is deliberately not
/// the normal-theory `estimate +- 1.96 SE`, because a tail quantile's sampling
/// distribution is skewed and the normal version is known to mis-cover.
enum class BootstrapKind { Iid, MovingBlock };

struct BootstrapEstimate {
    Real point = 0.0;          ///< estimate on the original sample
    Real standard_error = 0.0; ///< std of the replicate estimates
    Real ci_low = 0.0;
    Real ci_high = 0.0;
    Real confidence_level = 0.90; ///< interval built from the replicate quantiles
    Count replicates = 0;
    Count block_length = 0; ///< 0 for the iid design
    Count observations = 0;
    BootstrapKind kind = BootstrapKind::Iid;
    std::string measure;
    std::string note;
};

[[nodiscard]] BootstrapEstimate
bootstrap_var(std::span<const Real> returns_sample, Real confidence_level, Count replicates = 2000,
              Real interval_level = 0.90, BootstrapKind kind = BootstrapKind::Iid,
              Count block_length = 0, Seed seed = Rng::kDefaultSeed);

[[nodiscard]] BootstrapEstimate bootstrap_es(std::span<const Real> returns_sample,
                                             Real confidence_level, Count replicates = 2000,
                                             Real interval_level = 0.90,
                                             BootstrapKind kind = BootstrapKind::Iid,
                                             Count block_length = 0, Seed seed = Rng::kDefaultSeed);

/// Rule of thumb used to choose a block length when the caller does not:
/// `round(n^(1/3))`, the standard moving-block choice for a weakly dependent
/// series. Exposed so the choice is documented rather than buried in a caller.
[[nodiscard]] Count suggested_block_length(Count observations);

} // namespace quantrisk
