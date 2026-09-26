#include "quantrisk/risk/bootstrap.hpp"

#include <algorithm>
#include <cmath>
#include <functional>

#include "quantrisk/core/statistics.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/risk/measures.hpp"

namespace quantrisk {

namespace {

using Estimator = std::function<Real(std::span<const Real>, Real)>;

std::vector<Real> resample_iid(std::span<const Real> sample, Rng &rng) {
    const auto n = static_cast<std::uint64_t>(sample.size());
    std::vector<Real> out(sample.size());
    for (std::size_t i = 0; i < out.size(); ++i) {
        out[i] = sample[rng.uniform_index(n)];
    }
    return out;
}

std::vector<Real> resample_block(std::span<const Real> sample, Count block_length, Rng &rng) {
    const auto n = static_cast<std::size_t>(sample.size());
    const auto length = static_cast<std::size_t>(block_length);
    std::vector<Real> out;
    out.reserve(n);
    const auto starts = static_cast<std::uint64_t>(n);
    while (out.size() < n) {
        const std::size_t start = static_cast<std::size_t>(rng.uniform_index(starts));
        for (std::size_t offset = 0; offset < length && out.size() < n; ++offset) {
            out.push_back(sample[(start + offset) % n]);
        }
    }
    return out;
}

} // namespace

Count suggested_block_length(const Count observations) {
    require_positive_integer(observations, "observations");
    const auto length =
        static_cast<Count>(std::llround(std::pow(static_cast<Real>(observations), 1.0 / 3.0)));
    return std::max<Count>(1, std::min(length, observations - 1));
}

namespace {

BootstrapEstimate run_bootstrap(std::span<const Real> returns_sample, const Real confidence_level,
                                const Count replicates, const Real interval_level,
                                const risk::RiskEstimate &point, const Estimator &estimator,
                                const BootstrapKind kind, Count block_length, const Seed seed) {
    require_positive_integer(replicates, "replicates");
    require_confidence_level(confidence_level, "confidence_level");
    require_confidence_level(interval_level, "interval_level");

    if (kind == BootstrapKind::MovingBlock) {
        if (block_length <= 0) {
            block_length = suggested_block_length(static_cast<Count>(returns_sample.size()));
        }
        if (block_length >= static_cast<Count>(returns_sample.size())) {
            throw ValidationError("quantrisk: block_length must be smaller than the sample size");
        }
    } else if (block_length != 0) {
        throw ValidationError(
            "quantrisk: block_length is only meaningful for the moving-block design");
    }

    Rng rng(seed);
    std::vector<Real> values(static_cast<std::size_t>(replicates));
    for (Count replicate = 0; replicate < replicates; ++replicate) {
        const std::vector<Real> sample = kind == BootstrapKind::Iid
                                             ? resample_iid(returns_sample, rng)
                                             : resample_block(returns_sample, block_length, rng);
        values[static_cast<std::size_t>(replicate)] = estimator(sample, confidence_level);
    }
    std::ranges::sort(values);

    BootstrapEstimate result;
    result.point = point.value;
    result.confidence_level = point.confidence_level;
    result.observations = point.observations;
    result.measure = point.method;
    result.note = point.note;
    result.replicates = replicates;
    result.kind = kind;
    result.block_length = block_length;
    result.confidence_level = interval_level;
    result.observations = static_cast<Count>(returns_sample.size());
    result.standard_error = stats::sample_stddev(values);
    const Real tail = (1.0 - interval_level) / 2.0;
    result.ci_low = stats::quantile_linear(values, tail);
    result.ci_high = stats::quantile_linear(values, 1.0 - tail);
    return result;
}

} // namespace

BootstrapEstimate bootstrap_var(std::span<const Real> returns_sample, const Real confidence_level,
                                const Count replicates, const Real interval_level,
                                const BootstrapKind kind, Count block_length, const Seed seed) {
    const risk::RiskEstimate point = risk::historical_var(returns_sample, confidence_level);
    BootstrapEstimate result = run_bootstrap(
        returns_sample, confidence_level, replicates, interval_level, point,
        [](const std::span<const Real> sample, const Real level) {
            return risk::historical_var(sample, level).value;
        },
        kind, block_length, seed);
    result.measure = "historical_var";
    result.note = kind == BootstrapKind::Iid
                      ? "iid bootstrap percentile interval; assumes the return series "
                        "is serially independent"
                      : "moving-block bootstrap percentile interval; keeps within-block "
                        "dependence (volatility clustering) intact";
    return result;
}

BootstrapEstimate bootstrap_es(std::span<const Real> returns_sample, const Real confidence_level,
                               const Count replicates, const Real interval_level,
                               const BootstrapKind kind, Count block_length, const Seed seed) {
    const risk::RiskEstimate point = risk::historical_es(returns_sample, confidence_level);
    BootstrapEstimate result = run_bootstrap(
        returns_sample, confidence_level, replicates, interval_level, point,
        [](const std::span<const Real> sample, const Real level) {
            return risk::historical_es(sample, level).value;
        },
        kind, block_length, seed);
    result.measure = "historical_es";
    result.note = kind == BootstrapKind::Iid
                      ? "iid bootstrap percentile interval for expected shortfall; assumes "
                        "the return series is serially independent"
                      : "moving-block bootstrap percentile interval for expected "
                        "shortfall; keeps within-block dependence (volatility clustering) "
                        "intact";
    return result;
}

} // namespace quantrisk
