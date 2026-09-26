#pragma once

#include <cstdint>
#include <limits>

namespace quantrisk {

/// Numerical core precision. `float` is banned in numerical paths
/// (docs/validation_protocol.md §3).
using Real = double;

/// Time to expiry / horizon in **years** (docs/mathematical_specification.md §0).
using Time = Real;

/// Continuously compounded, annualised rate (`r`, `q`, `mu`).
using Rate = Real;

/// Annualised volatility, sigma >= 0.
using Volatility = Real;

/// A quantity of currency (price, payoff, P&L, VaR in currency units).
using Money = Real;

/// Integer count of paths / scenarios / lattice steps.
using Count = std::int64_t;

/// Seed for the reproducible RNG abstraction (core/rng.hpp).
using Seed = std::uint64_t;

inline constexpr Real kHighestReal = std::numeric_limits<Real>::max();

} // namespace quantrisk
