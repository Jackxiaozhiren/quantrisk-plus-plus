#pragma once

#include <cmath>
#include <limits>

#include "quantrisk/core/types.hpp"

namespace quantrisk {

inline constexpr Real kPi = 3.14159265358979323846;
inline constexpr Real kTwoPi = 6.28318530717958647692;
inline constexpr Real kSqrtTwo = 1.41421356237309504880;
inline constexpr Real kInvSqrtTwoPi = 0.39894228040143267794;

/// Smallest representable relative spacing of `double` around 1.0.
inline constexpr Real kMachineEpsilon = std::numeric_limits<Real>::epsilon();

/// Default absolute tolerance for deterministic analytic identities.
/// Frozen in docs/validation_protocol.md §2; justified by rounding of a small
/// number of `double` operations, not by trial and error.
inline constexpr Real kAnalyticTolerance = 1.0e-12;

} // namespace quantrisk
