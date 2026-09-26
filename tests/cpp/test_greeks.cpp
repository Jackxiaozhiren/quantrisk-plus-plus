#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <algorithm>
#include <cmath>
#include <vector>

#include "quantrisk/core/constants.hpp"
#include "quantrisk/pricing/black_scholes.hpp"
#include "quantrisk/pricing/finite_differences.hpp"
#include "quantrisk/pricing/instrument.hpp"

using Catch::Approx;
using quantrisk::BumpPolicy;
using quantrisk::EuropeanOption;
using quantrisk::MarketParams;
using quantrisk::OptionType;
using quantrisk::Real;

namespace {

MarketParams params(const Real spot, const Real rate, const Real dividend, const Real volatility,
                    const Real maturity) {
    return MarketParams{.spot = spot,
                        .rate = rate,
                        .dividend_yield = dividend,
                        .volatility = volatility,
                        .maturity = maturity};
}

struct Case {
    OptionType type;
    Real strike;
    MarketParams market;
};

/// A spread of regimes: deep ITM, ATM, deep OTM, short and long dated, high
/// and low volatility, dividend-paying, and a negative-rate case.
const std::vector<Case> &cases() {
    static const std::vector<Case> kCases = {
        {OptionType::Call, 100.0, params(100.0, 0.05, 0.0, 0.2, 1.0)},
        {OptionType::Put, 100.0, params(100.0, 0.05, 0.0, 0.2, 1.0)},
        {OptionType::Call, 100.0, params(150.0, 0.03, 0.02, 0.25, 0.5)},
        {OptionType::Put, 100.0, params(60.0, 0.03, 0.02, 0.35, 2.0)},
        {OptionType::Call, 100.0, params(100.0, -0.02, 0.0, 0.4, 3.0)},
        {OptionType::Put, 100.0, params(100.0, 0.08, 0.06, 0.1, 0.1)},
        {OptionType::Call, 100.0, params(101.0, 0.05, 0.0, 0.9, 1.0)},
    };
    return kCases;
}

Real relative_error(const Real computed, const Real reference) {
    const Real scale = std::max({std::abs(reference), std::abs(computed), 1.0e-8});
    return std::abs(computed - reference) / scale;
}

} // namespace

TEST_CASE("analytic Greeks match finite differences within their own truncation "
          "estimate") {
    /// Rather than fixing a relative band (which is meaningless for a deep
    /// out-of-the-money sensitivity that is legitimately near zero, and too tight
    /// for a near-expiry at-the-money option where curvature scales as
    /// 1/(sigma sqrt(T))^3), the finite-difference error is *estimated* and then
    /// used as the yardstick. For a second-order central difference,
    ///     error(h/2) ~ |FD(h/2) - FD(h)| / (2^2 - 1),
    /// the standard Richardson estimate. Requiring the analytic value to sit
    /// within four times that estimate verifies the formula with no tuned
    /// tolerance, and fails if the discrepancy does not shrink with the bump.
    BumpPolicy coarse;
    coarse.spot_relative = 0.002;
    coarse.volatility_absolute = 0.002;
    coarse.rate_absolute = 2.0e-6;
    coarse.time_absolute = 2.0e-5;
    BumpPolicy fine = coarse;
    fine.spot_relative /= 2.0;
    fine.volatility_absolute /= 2.0;
    fine.rate_absolute /= 2.0;
    fine.time_absolute /= 2.0;

    /// Round-off floors, per Greek, in the natural units of each quantity:
    /// epsilon * premium / h^2 for gamma and epsilon * premium / h for the rest,
    /// evaluated at the smallest bump used here (about 1e-9 in relative terms).
    constexpr Real kDeltaFloor = 1.0e-9;
    constexpr Real kGammaFloor = 1.0e-9;
    constexpr Real kMoneyFloor = 1.0e-7; // vega / theta / rho, currency units

    int verified = 0;
    for (const Case &case_data : cases()) {
        const EuropeanOption option{case_data.type, case_data.strike};
        const quantrisk::Greeks analytic =
            quantrisk::black_scholes_greeks(option, case_data.market);
        const quantrisk::Greeks from_coarse =
            quantrisk::finite_difference_greeks(option, case_data.market, coarse);
        const quantrisk::Greeks from_fine =
            quantrisk::finite_difference_greeks(option, case_data.market, fine);

        struct Item {
            const char *name;
            Real analytic;
            Real coarse;
            Real fine;
            Real floor;
        };
        const Item items[] = {
            {"delta", analytic.delta, from_coarse.delta, from_fine.delta, kDeltaFloor},
            {"gamma", analytic.gamma, from_coarse.gamma, from_fine.gamma, kGammaFloor},
            {"vega", analytic.vega, from_coarse.vega, from_fine.vega, kMoneyFloor},
            {"theta", analytic.theta, from_coarse.theta, from_fine.theta, kMoneyFloor},
            {"rho", analytic.rho, from_coarse.rho, from_fine.rho, kMoneyFloor},
        };

        for (const Item &item : items) {
            CAPTURE(case_data.market.spot, case_data.strike, case_data.market.volatility,
                    case_data.market.maturity, item.name);
            const Real estimated = std::abs(item.fine - item.coarse) / 3.0;
            const Real bound = 4.0 * estimated + item.floor;
            const Real residual = std::abs(item.fine - item.analytic);
            INFO("residual " << residual << " vs estimated-error bound " << bound);
            CHECK(residual <= bound);
            ++verified;
        }
    }
    CHECK(verified == static_cast<int>(cases().size()) * 5);
}

TEST_CASE("shrinking the bump quarters the analytic/finite-difference gap") {
    /// The complementary half of the Richardson test above: truncation must
    /// actually fall with h^2. Measured in absolute units against per-Greek floors
    /// because for a deep out-of-the-money sensitivity the *relative* gap is
    /// dominated by the near-zero denominator, not by the scheme.
    BumpPolicy coarse;
    coarse.spot_relative = 0.002;
    coarse.volatility_absolute = 0.002;
    coarse.rate_absolute = 2.0e-6;
    coarse.time_absolute = 2.0e-5;
    BumpPolicy fine = coarse;
    fine.spot_relative /= 2.0;
    fine.volatility_absolute /= 2.0;
    fine.rate_absolute /= 2.0;
    fine.time_absolute /= 2.0;

    int checked = 0;
    for (const Case &case_data : cases()) {
        const EuropeanOption option{case_data.type, case_data.strike};
        const quantrisk::Greeks analytic =
            quantrisk::black_scholes_greeks(option, case_data.market);
        const quantrisk::Greeks from_coarse =
            quantrisk::finite_difference_greeks(option, case_data.market, coarse);
        const quantrisk::Greeks from_fine =
            quantrisk::finite_difference_greeks(option, case_data.market, fine);

        struct Pair {
            const char *name;
            Real coarse;
            Real fine;
            Real reference;
            Real floor;
        };
        const Pair pairs[] = {
            {"delta", from_coarse.delta, from_fine.delta, analytic.delta, 1.0e-9},
            {"gamma", from_coarse.gamma, from_fine.gamma, analytic.gamma, 1.0e-9},
            {"vega", from_coarse.vega, from_fine.vega, analytic.vega, 1.0e-7},
            {"theta", from_coarse.theta, from_fine.theta, analytic.theta, 1.0e-7},
            {"rho", from_coarse.rho, from_fine.rho, analytic.rho, 1.0e-7},
        };
        for (const Pair &pair : pairs) {
            const Real coarse_error = std::abs(pair.coarse - pair.reference);
            const Real fine_error = std::abs(pair.fine - pair.reference);
            if (coarse_error < 100.0 * pair.floor) {
                continue; // no measurable truncation left to scale
            }
            CAPTURE(case_data.market.volatility, case_data.market.maturity, pair.name);
            CHECK(fine_error < coarse_error);
            CHECK(coarse_error / fine_error > 2.5);
            CHECK(coarse_error / fine_error < 12.0);
            ++checked;
        }
    }
    /// Guard against a vacuous test: the remaining combinations are already
    /// accurate to within the floors (nothing left to scale), so only a subset is
    /// informative - but it must not be none of them.
    CHECK(checked >= 10);
}

TEST_CASE("call and put Greeks obey their structural relations") {
    for (const MarketParams market :
         {params(100.0, 0.05, 0.02, 0.2, 1.0), params(70.0, 0.01, 0.05, 0.4, 0.25),
          params(130.0, 0.08, 0.0, 0.15, 3.0)}) {
        const EuropeanOption call{OptionType::Call, 100.0};
        const EuropeanOption put{OptionType::Put, 100.0};
        const auto call_greeks = quantrisk::black_scholes_greeks(call, market);
        const auto put_greeks = quantrisk::black_scholes_greeks(put, market);
        const Real growth_discount = std::exp(-market.dividend_yield * market.maturity);

        // Gamma and vega are identical for the pair; Delta and Rho differ by the
        // discounted quantities that parity differentiates.
        CHECK(call_greeks.gamma == Approx(put_greeks.gamma).epsilon(1e-14));
        CHECK(call_greeks.vega == Approx(put_greeks.vega).epsilon(1e-14));
        CHECK(call_greeks.delta - put_greeks.delta == Approx(growth_discount).epsilon(1e-12));
        CHECK(call_greeks.rho - put_greeks.rho ==
              Approx(market.maturity * 100.0 * std::exp(-market.rate * market.maturity))
                  .epsilon(1e-12));

        // Theta differs by the carry term of the parity identity.
        const Real expected_theta_difference =
            market.dividend_yield * market.spot * growth_discount -
            market.rate * 100.0 * std::exp(-market.rate * market.maturity);
        CHECK(call_greeks.theta - put_greeks.theta ==
              Approx(expected_theta_difference).epsilon(1e-12));
    }
}

TEST_CASE("Greeks stay inside their theoretical ranges") {
    for (const Case &case_data : cases()) {
        const EuropeanOption option{case_data.type, case_data.strike};
        const Real growth_discount =
            std::exp(-case_data.market.dividend_yield * case_data.market.maturity);
        const auto greeks = quantrisk::black_scholes_greeks(option, case_data.market);
        CAPTURE(case_data.strike);
        CHECK(greeks.gamma >= 0.0);
        CHECK(greeks.vega >= 0.0);
        if (option.type == OptionType::Call) {
            CHECK(greeks.delta >= 0.0);
            CHECK(greeks.delta <= growth_discount + 1.0e-12);
            CHECK(greeks.rho >= 0.0);
        } else {
            CHECK(greeks.delta >= -growth_discount - 1.0e-12);
            CHECK(greeks.delta <= 0.0);
            CHECK(greeks.rho <= 0.0);
        }
    }
}

TEST_CASE("vega is largest near the money and grows with maturity") {
    Real at_the_money = quantrisk::black_scholes_greeks(EuropeanOption{OptionType::Call, 100.0},
                                                        params(100.0, 0.05, 0.0, 0.2, 1.0))
                            .vega;
    Real far_out = quantrisk::black_scholes_greeks(EuropeanOption{OptionType::Call, 200.0},
                                                   params(100.0, 0.05, 0.0, 0.2, 1.0))
                       .vega;
    CHECK(at_the_money > far_out);

    const Real short_vega = quantrisk::black_scholes_greeks(EuropeanOption{OptionType::Call, 100.0},
                                                            params(100.0, 0.05, 0.0, 0.2, 0.25))
                                .vega;
    const Real long_vega = quantrisk::black_scholes_greeks(EuropeanOption{OptionType::Call, 100.0},
                                                           params(100.0, 0.05, 0.0, 0.2, 4.0))
                               .vega;
    CHECK(long_vega > short_vega);
}

TEST_CASE("degenerate edges return limits rather than NaN or inf") {
    SECTION("expired contract keeps only delta") {
        const auto greeks = quantrisk::black_scholes_greeks(EuropeanOption{OptionType::Call, 100.0},
                                                            params(110.0, 0.05, 0.0, 0.2, 0.0));
        CHECK(greeks.delta == Approx(1.0));
        CHECK(greeks.gamma == 0.0);
        CHECK(greeks.vega == 0.0);
        CHECK(greeks.theta == 0.0);
        CHECK(greeks.rho == 0.0);

        const auto otm = quantrisk::black_scholes_greeks(EuropeanOption{OptionType::Call, 100.0},
                                                         params(90.0, 0.05, 0.0, 0.2, 0.0));
        CHECK(otm.delta == Approx(0.0));
    }

    SECTION("zero volatility collapses gamma but keeps delta") {
        const auto greeks = quantrisk::black_scholes_greeks(EuropeanOption{OptionType::Call, 100.0},
                                                            params(110.0, 0.05, 0.0, 0.0, 1.0));
        CHECK(greeks.delta == Approx(1.0));
        CHECK(greeks.gamma == 0.0);
        CHECK(greeks.vega == 0.0);
        const auto put = quantrisk::black_scholes_greeks(EuropeanOption{OptionType::Put, 100.0},
                                                         params(90.0, 0.05, 0.0, 0.0, 1.0));
        CHECK(put.delta == Approx(-1.0));
    }

    SECTION("finite differences abstain where the kink lives") {
        // sigma == 0: vega is not differentiable at the kink, and the helper says
        // so instead of returning a number that depends on the bump.
        const auto value = quantrisk::finite_difference_vega(
            EuropeanOption{OptionType::Call, 100.0}, params(100.0, 0.05, 0.0, 0.0, 1.0));
        CHECK(std::isnan(value));
    }
}

TEST_CASE("bump policy validates itself") {
    BumpPolicy policy;
    CHECK_NOTHROW(policy.validate());
    policy.spot_relative = 0.0;
    CHECK_THROWS_AS(policy.validate(), quantrisk::ValidationError);
    policy.spot_relative = 0.01;
    policy.time_absolute = -1.0;
    CHECK_THROWS_AS(policy.validate(), quantrisk::ValidationError);
    CHECK_THROWS_AS(quantrisk::finite_difference_delta(EuropeanOption{OptionType::Call, 100.0},
                                                       params(100.0, 0.05, 0.0, 0.2, 1.0),
                                                       BumpPolicy{.spot_relative = 2.0}),
                    quantrisk::ValidationError);
}
