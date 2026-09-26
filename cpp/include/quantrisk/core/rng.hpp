#pragma once

#include <cstdint>
#include <random>
#include <vector>

#include "quantrisk/core/types.hpp"

namespace quantrisk {

/// Deterministic RNG abstraction: `std::mt19937_64` owned by the instance.
///
/// Design rules (docs/validation_protocol.md §3):
/// - No global RNG state. Every stochastic entry point constructs or receives
///   an `Rng`, so two engines never share a hidden stream.
/// - Normal variates use the Marsaglia polar method implemented here rather
///   than `std::normal_distribution`, because the latter's output is not
///   specified by the standard and differs between libstdc++ and libc++.
///   A pair of variates is produced per accepted draw and the partner is
///   cached, so a given seed yields the same sequence within one build.
class Rng {
  public:
    /// Default seed used by demos and documented experiment commands.
    static constexpr Seed kDefaultSeed = 42;

    explicit Rng(const Seed seed = kDefaultSeed) : engine_(seed), seed_(seed) {}

    Rng(const Rng &) = delete;
    Rng &operator=(const Rng &) = delete;
    Rng(Rng &&) = default;
    Rng &operator=(Rng &&) = default;

    /// Uniform on [0, 1).
    double uniform01();

    /// Standard normal variate, N(0, 1).
    double standard_normal();

    /// `n` independent N(0, 1) variates in one call (path generation).
    std::vector<double> standard_normal_vector(std::size_t n);

    [[nodiscard]] Seed seed() const { return seed_; }
    [[nodiscard]] std::uint64_t uniform_draws() const { return uniform_draws_; }
    [[nodiscard]] bool has_cached_normal() const { return has_spare_; }

    /// Integer uniform in [0, high) — used by bootstrap resampling.
    std::uint64_t uniform_index(const std::uint64_t high);

  private:
    std::mt19937_64 engine_;
    Seed seed_ = kDefaultSeed;
    std::uint64_t uniform_draws_ = 0;
    bool has_spare_ = false;
    double spare_ = 0.0;
};

} // namespace quantrisk
