#include <catch2/catch_test_macros.hpp>

#include <limits>
#include <string>

#include "quantrisk/core/validation.hpp"

using quantrisk::Count;
using quantrisk::Real;
using quantrisk::ValidationError;
using quantrisk::ValidationIssues;

namespace {

template <typename Check>
bool throws(Check check) {
  try {
    check();
    return false;
  } catch (const ValidationError &) {
    return true;
  }
}

constexpr Real kNan = std::numeric_limits<Real>::quiet_NaN();
constexpr Real kInf = std::numeric_limits<Real>::infinity();

}  // namespace

TEST_CASE("require_positive accepts only finite values above zero") {
  REQUIRE_FALSE(throws([] { quantrisk::require_positive(1.0e-300, "x"); }));
  REQUIRE(throws([] { quantrisk::require_positive(0.0, "x"); }));
  REQUIRE(throws([] { quantrisk::require_positive(-1.0, "x"); }));
  REQUIRE(throws([] { quantrisk::require_positive(kNan, "x"); }));
  REQUIRE(throws([] { quantrisk::require_positive(kInf, "x"); }));
}

TEST_CASE("require_non_negative keeps zero but rejects below-zero") {
  REQUIRE_FALSE(throws([] { quantrisk::require_non_negative(0.0, "sigma"); }));
  REQUIRE_FALSE(throws([] { quantrisk::require_non_negative(2.0, "sigma"); }));
  REQUIRE(throws([] { quantrisk::require_non_negative(-1.0e-16, "sigma"); }));
  REQUIRE(throws([] { quantrisk::require_non_negative(kNan, "sigma"); }));
}

TEST_CASE("integer checks reject non-positive counts") {
  REQUIRE_FALSE(throws([] { quantrisk::require_positive_integer(1, "steps"); }));
  REQUIRE(throws([] { quantrisk::require_positive_integer(0, "steps"); }));
  REQUIRE(throws([] { quantrisk::require_positive_integer(-3, "steps"); }));
  REQUIRE_FALSE(
      throws([] { quantrisk::require_non_negative_integer(0, "lag"); }));
  REQUIRE(throws([] { quantrisk::require_non_negative_integer(-1, "lag"); }));
}

TEST_CASE("probability and confidence-range checks") {
  REQUIRE_FALSE(throws([] { quantrisk::require_probability(0.0, "p"); }));
  REQUIRE_FALSE(throws([] { quantrisk::require_probability(1.0, "p"); }));
  REQUIRE(throws([] { quantrisk::require_probability(1.0 + 1.0e-15, "p"); }));

  // A 50 % confidence level is meaningless for VaR, so it is rejected.
  REQUIRE_FALSE(
      throws([] { quantrisk::require_confidence_level(0.95, "alpha"); }));
  REQUIRE(throws([] { quantrisk::require_confidence_level(0.5, "alpha"); }));
  REQUIRE(throws([] { quantrisk::require_confidence_level(1.0, "alpha"); }));

  REQUIRE_FALSE(throws([] { quantrisk::require_in_interval(0.5, 0.0, 1.0, "x"); }));
  REQUIRE(throws([] { quantrisk::require_in_interval(1.5, 0.0, 1.0, "x"); }));
}

TEST_CASE("messages name the offending parameter and its value") {
  try {
    quantrisk::require_positive(-2.5, "spot");
    FAIL("expected ValidationError");
  } catch (const ValidationError &error) {
    const std::string message = error.what();
    CHECK(message.find("'spot'") != std::string::npos);
    CHECK(message.find("strictly positive") != std::string::npos);
    CHECK(message.find("-2.5") != std::string::npos);
  }
}

TEST_CASE("ValidationIssues reports every violated constraint at once") {
  ValidationIssues issues;
  issues.check(false, "maturity must be >= 0, got -1");
  issues.check(true, "not reported");
  issues.check(false, "volatility must be finite, got NaN");

  REQUIRE(issues.size() == 2);
  CHECK_FALSE(issues.empty());
  CHECK(issues.report("MarketParams").find("maturity") != std::string::npos);
  CHECK(issues.report("MarketParams").find("volatility") != std::string::npos);

  const std::string combined = [&issues] {
    try {
      issues.throw_if_failed("MarketParams");
      return std::string("no throw");
    } catch (const ValidationError &error) {
      return std::string(error.what());
    }
  }();
  CHECK(combined.find("invalid MarketParams") != std::string::npos);
  CHECK(combined.find("2") == std::string::npos ||
        combined.find("-  maturity") != std::string::npos);

  ValidationIssues clean;
  clean.check(true, "anything satisfied");
  CHECK(clean.empty());
  CHECK_NOTHROW(clean.throw_if_failed("MarketParams"));
}
