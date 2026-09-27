#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <cmath>
#include <vector>

#include "quantrisk/core/validation.hpp"
#include "quantrisk/portfolio/linear_program.hpp"

using Catch::Approx;
using quantrisk::Count;
using quantrisk::Real;
namespace lp = quantrisk::portfolio;

TEST_CASE("the simplex reproduces the textbook product-mix optimum") {
    // max 3x + 5y s.t. x <= 4, 2y <= 12, 3x + 2y <= 18, solved as
    // min -3x - 5y with slacks; the known optimum is (x, y) = (2, 6), value 36.
    const std::vector<Real> objective = {-3.0, -5.0, 0.0, 0.0, 0.0};
    const std::vector<Real> rows = {
        1.0, 0.0, 1.0, 0.0, 0.0, //
        0.0, 2.0, 0.0, 1.0, 0.0, //
        3.0, 2.0, 0.0, 0.0, 1.0, //
    };
    const std::vector<Real> rhs = {4.0, 12.0, 18.0};
    const auto result = lp::solve_linear_program(objective, rows, rhs, 5, 3);
    REQUIRE(result.status == lp::LpStatus::Optimal);
    CHECK(result.values[0] == Approx(2.0).epsilon(1.0e-9));
    CHECK(result.values[1] == Approx(6.0).epsilon(1.0e-9));
    CHECK(result.objective == Approx(-36.0).epsilon(1.0e-9));
    CHECK(result.residual <= 1.0e-9);
    CHECK(result.dual_gap <= 1.0e-9);
}

TEST_CASE("an infeasible program says so instead of returning a point") {
    const std::vector<Real> objective = {1.0};
    const std::vector<Real> rows = {1.0, 1.0};
    const std::vector<Real> rhs = {1.0, 2.0};
    const auto result = lp::solve_linear_program(objective, rows, rhs, 1, 2);
    CHECK(result.status == lp::LpStatus::Infeasible);
    CHECK_FALSE(result.note.empty());
}

TEST_CASE("an unbounded program is identified by its feasible ray") {
    // x - s = 1 with min -x: s can grow forever, so there is no optimum.
    const std::vector<Real> objective = {-1.0, 0.0};
    const std::vector<Real> rows = {1.0, -1.0};
    const std::vector<Real> rhs = {1.0};
    const auto result = lp::solve_linear_program(objective, rows, rhs, 2, 1);
    CHECK(result.status == lp::LpStatus::Unbounded);
}

TEST_CASE("a duplicated constraint is handled as redundant, not as a contradiction") {
    // min -x s.t. x + y = 1 stated twice. Bland's rule has to survive the
    // degenerate basis the duplicate creates, and the answer is x = 1.
    const std::vector<Real> objective = {-1.0, 0.0};
    const std::vector<Real> rows = {1.0, 1.0, 1.0, 1.0};
    const std::vector<Real> rhs = {1.0, 1.0};
    const auto result = lp::solve_linear_program(objective, rows, rhs, 2, 2);
    REQUIRE(result.status == lp::LpStatus::Optimal);
    CHECK(result.values[0] == Approx(1.0).epsilon(1.0e-9));
    CHECK(result.values[1] == Approx(0.0).margin(1.0e-9));
    CHECK(result.residual <= 1.0e-9);
}

TEST_CASE("negative right-hand sides are flipped, not dropped") {
    // -x = -2 is x = 2; a solver that treated the negative row as infeasible
    // would fail here.
    const std::vector<Real> objective = {1.0};
    const std::vector<Real> rows = {-1.0};
    const std::vector<Real> rhs = {-2.0};
    const auto result = lp::solve_linear_program(objective, rows, rhs, 1, 1);
    REQUIRE(result.status == lp::LpStatus::Optimal);
    CHECK(result.values[0] == Approx(2.0).epsilon(1.0e-9));
    CHECK(result.objective == Approx(2.0).epsilon(1.0e-9));
}

TEST_CASE("the reported point satisfies the original data, not just the tableau") {
    // A three-variable program whose optimum is known: min -x - y - z with
    // x + y + z <= 3 and x, y, z >= 0 gives any corner with value -3.
    const std::vector<Real> objective = {-1.0, -1.0, -1.0, 0.0};
    const std::vector<Real> rows = {1.0, 1.0, 1.0, 1.0};
    const std::vector<Real> rhs = {3.0};
    const auto result = lp::solve_linear_program(objective, rows, rhs, 4, 1);
    REQUIRE(result.status == lp::LpStatus::Optimal);
    const Real total = result.values[0] + result.values[1] + result.values[2];
    CHECK(total == Approx(3.0).epsilon(1.0e-9));
    CHECK(result.objective == Approx(-3.0).epsilon(1.0e-9));
    for (const Real value : result.values) {
        CHECK(value >= -1.0e-9);
    }
    CHECK(result.residual <= 1.0e-9);
    CHECK(result.dual_gap <= 1.0e-9);
}

TEST_CASE("the linear program validates its own input shape") {
    const std::vector<Real> one = {1.0};
    const std::vector<Real> two_rows = {1.0, 1.0};
    const std::vector<Real> two_objective = {1.0, 2.0};
    const std::vector<Real> not_a_number = {std::nan("")};
    CHECK_THROWS_AS(lp::solve_linear_program(one, two_rows, one, 1, 2), quantrisk::ValidationError);
    CHECK_THROWS_AS(lp::solve_linear_program(one, one, one, 0, 1), quantrisk::ValidationError);
    CHECK_THROWS_AS(lp::solve_linear_program(two_objective, one, one, 2, 1),
                    quantrisk::ValidationError);
    CHECK_THROWS_AS(lp::solve_linear_program(not_a_number, one, one, 1, 1),
                    quantrisk::ValidationError);
}
