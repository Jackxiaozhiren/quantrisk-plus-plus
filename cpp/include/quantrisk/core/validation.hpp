#pragma once

#include <cmath>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#include "quantrisk/core/types.hpp"

namespace quantrisk {

/// Thrown when an input violates a documented domain constraint.
class ValidationError : public std::invalid_argument {
public:
  explicit ValidationError(const std::string &message)
      : std::invalid_argument(message) {}
};

namespace detail {

template <typename T>
inline std::string format_value(const T &value) {
  std::ostringstream os;
  os.precision(17);
  os << value;
  return os.str();
}

[[noreturn]] inline void reject(const std::string_view name,
                                const std::string_view rule,
                                const std::string &value) {
  throw ValidationError("quantrisk: '" + std::string(name) + "' must be " +
                        std::string(rule) + ", got " + value);
}

}  // namespace detail

/// @name Scalar domain checks
/// Every pricing / risk entry point validates its inputs with these helpers so
/// that NaN, infinity and out-of-domain parameters fail loudly instead of
/// silently producing NaN results.
/// @{

inline void require_finite(const Real value, const std::string_view name) {
  if (!std::isfinite(value)) {
    detail::reject(name, "finite", detail::format_value(value));
  }
}

inline void require_positive(const Real value, const std::string_view name) {
  require_finite(value, name);
  if (!(value > 0.0)) {
    detail::reject(name, "strictly positive (> 0)",
                   detail::format_value(value));
  }
}

inline void require_non_negative(const Real value, const std::string_view name) {
  require_finite(value, name);
  if (!(value >= 0.0)) {
    detail::reject(name, "non-negative (>= 0)", detail::format_value(value));
  }
}

inline void require_positive_integer(const Count value,
                                     const std::string_view name) {
  if (value <= 0) {
    detail::reject(name, "a positive integer", detail::format_value(value));
  }
}

inline void require_non_negative_integer(const Count value,
                                         const std::string_view name) {
  if (value < 0) {
    detail::reject(name, "a non-negative integer",
                   detail::format_value(value));
  }
}

inline void require_probability(const Real value, const std::string_view name) {
  require_finite(value, name);
  if (!(value >= 0.0 && value <= 1.0)) {
    detail::reject(name, "in [0, 1]", detail::format_value(value));
  }
}

inline void require_confidence_level(const Real value,
                                     const std::string_view name) {
  require_finite(value, name);
  if (!(value > 0.5 && value < 1.0)) {
    detail::reject(name, "in (0.5, 1)", detail::format_value(value));
  }
}

inline void require_in_interval(const Real value, const Real low,
                                const Real high, const std::string_view name) {
  require_finite(value, name);
  if (!(value >= low && value <= high)) {
    detail::reject(name,
                   "in [" + detail::format_value(low) + ", " +
                       detail::format_value(high) + "]",
                   detail::format_value(value));
  }
}

/// @}

/// Collects every violated constraint of one input record so callers see all
/// problems at once instead of one per rebuild.
class ValidationIssues {
public:
  void check(const bool condition, std::string message) {
    if (!condition) {
      problems_.push_back(std::move(message));
    }
  }

  [[nodiscard]] bool empty() const { return problems_.empty(); }
  [[nodiscard]] std::size_t size() const { return problems_.size(); }
  [[nodiscard]] const std::vector<std::string> &problems() const {
    return problems_;
  }

  [[nodiscard]] std::string report(const std::string_view context) const {
    std::string out = "quantrisk: invalid " + std::string(context);
    for (const std::string &problem : problems_) {
      out += "\n  - " + problem;
    }
    return out;
  }

  void throw_if_failed(const std::string_view context) const {
    if (!empty()) {
      throw ValidationError(report(context));
    }
  }

private:
  std::vector<std::string> problems_;
};

}  // namespace quantrisk
