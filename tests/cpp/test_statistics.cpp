#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <cmath>
#include <vector>

#include "quantrisk/core/statistics.hpp"
#include "quantrisk/core/validation.hpp"

using Catch::Approx;
using quantrisk::Real;
using namespace quantrisk;

TEST_CASE("compensated summation keeps small terms that naive addition loses") {
  const std::vector<Real> data = {1.0e16, 1.0, -1.0e16};
  // Plain left-to-right addition gives 0 here; Neumaier compensation keeps 1.
  CHECK(stats::sum_compensated(data) == 1.0);

  Real naive = 0.0;
  for (const Real value : data) {
    naive += value;
  }
  INFO("naive sum = " << naive);
  CHECK(naive != 1.0);
}

TEST_CASE("mean and unbiased variance match hand-computed values") {
  const std::vector<Real> data = {2, 4, 4, 4, 5, 5, 7, 9};
  CHECK(stats::mean(data) == Approx(5.0));
  // Sum of squared deviations = 32, divided by n - 1 = 7.
  CHECK(stats::sample_variance(data) == Approx(32.0 / 7.0));
  CHECK(stats::sample_stddev(data) == Approx(std::sqrt(32.0 / 7.0)));
  CHECK(stats::standard_error_of_mean(data) ==
        Approx(std::sqrt(32.0 / 7.0) / std::sqrt(8.0)));
}

TEST_CASE("quantile uses the linear interpolation convention") {
  const std::vector<Real> sorted = {1, 2, 3, 4};
  CHECK(stats::quantile_linear(sorted, 0.0) == Approx(1.0));
  CHECK(stats::quantile_linear(sorted, 0.25) == Approx(1.75));
  CHECK(stats::quantile_linear(sorted, 0.5) == Approx(2.5));
  CHECK(stats::quantile_linear(sorted, 0.6) == Approx(2.8));
  CHECK(stats::quantile_linear(sorted, 1.0) == Approx(4.0));

  // quantile() sorts a copy, so unsorted input is allowed and unchanged.
  std::vector<Real> unsorted = {4, 1, 3, 2};
  CHECK(stats::quantile(unsorted, 0.5) == Approx(2.5));
  CHECK(unsorted == std::vector<Real>{4, 1, 3, 2});

  const std::vector<Real> single = {3.5};
  CHECK(stats::quantile_linear(single, 0.9) == Approx(3.5));
}

TEST_CASE("tail averaging over the largest observations") {
  const std::vector<Real> sorted = {1, 2, 3, 4};
  CHECK(stats::mean_of_largest_sorted(sorted, 1) == Approx(4.0));
  CHECK(stats::mean_of_largest_sorted(sorted, 2) == Approx(3.5));
  CHECK(stats::mean_of_largest_sorted(sorted, 4) == Approx(2.5));
  CHECK_THROWS_AS(stats::mean_of_largest_sorted(sorted, 5), ValidationError);
  CHECK_THROWS_AS(stats::mean_of_largest_sorted(sorted, 0), ValidationError);
}

TEST_CASE("autocorrelation of an alternating series is negative at lag 1") {
  const std::vector<Real> data = {-1, 1, -1, 1};
  // Wallis denominator: sum x_t x_{t-1} = -3 over sum x_t^2 = 4.
  CHECK(stats::autocorrelation(data, 1) == Approx(-0.75));
  CHECK(stats::autocorrelation(data, 2) == Approx(0.5));

  const std::vector<Real> constant = {2, 2, 2, 2};
  CHECK(stats::autocorrelation(constant, 1) == Approx(0.0));
}

TEST_CASE("statistics helpers reject empty or underspecified samples") {
  const std::vector<Real> empty;
  const std::vector<Real> one = {1.0};

  CHECK(stats::sum_compensated(empty) == 0.0);
  CHECK_THROWS_AS(stats::mean(empty), ValidationError);
  CHECK_THROWS_AS(stats::sample_variance(one), ValidationError);
  CHECK_THROWS_AS(stats::quantile_linear(empty, 0.5), ValidationError);
  CHECK_THROWS_AS(stats::quantile_linear(one, 1.5), ValidationError);
  CHECK_THROWS_AS(stats::autocorrelation(one, 1), ValidationError);
}
