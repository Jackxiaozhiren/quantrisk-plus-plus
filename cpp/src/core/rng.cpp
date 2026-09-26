#include "quantrisk/core/rng.hpp"

#include <cmath>

#include "quantrisk/core/constants.hpp"
#include "quantrisk/core/validation.hpp"

namespace quantrisk {

namespace {

// 2^-64 as an exact double: mt19937_64 emits 64-bit words, so mapping the
// integer to [0, 1) by scaling is exact and free of rounding-dependent loops.
constexpr double kInvTwoPow64 = 1.0 / 18446744073709551616.0;

} // namespace

double Rng::uniform01() {
    const std::uint64_t raw = engine_();
    ++uniform_draws_;
    return static_cast<double>(raw) * kInvTwoPow64;
}

std::uint64_t Rng::uniform_index(const std::uint64_t high) {
    if (high == 0) {
        detail::reject("high", "a positive bound for uniform_index", detail::format_value(high));
    }
    // Rejection sampling over the full 64-bit range: unbiased (no modulo bias),
    // and deterministic because the engine state, not the standard library,
    // decides how many rejections occur. `limit` is the largest multiple of
    // `high` not exceeding 2^64 - 1, so accepted values form whole cycles.
    constexpr std::uint64_t kMaxIndex = ~std::uint64_t{0};
    const std::uint64_t limit = kMaxIndex - (kMaxIndex % high);
    std::uint64_t raw = engine_();
    ++uniform_draws_;
    while (raw >= limit) {
        raw = engine_();
        ++uniform_draws_;
    }
    return raw % high;
}

double Rng::standard_normal() {
    if (has_spare_) {
        has_spare_ = false;
        const double value = spare_;
        spare_ = 0.0;
        return value;
    }
    // Marsaglia polar method. Acceptance probability is pi/4, so the expected
    // number of uniform pairs consumed is 4/pi ~= 1.27; the loop terminates
    // almost surely and every rejection is drawn from this instance's stream.
    for (;;) {
        const double u = 2.0 * uniform01() - 1.0;
        const double v = 2.0 * uniform01() - 1.0;
        const double s = u * u + v * v;
        if (s >= 1.0 || s == 0.0) {
            continue;
        }
        const double factor = std::sqrt(-2.0 * std::log(s) / s);
        spare_ = u * factor;
        has_spare_ = true;
        return v * factor;
    }
}

std::vector<double> Rng::standard_normal_vector(const std::size_t n) {
    std::vector<double> out;
    out.reserve(n);
    for (std::size_t i = 0; i < n; ++i) {
        out.push_back(standard_normal());
    }
    return out;
}

} // namespace quantrisk
