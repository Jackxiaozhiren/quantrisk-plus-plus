"""Level 3 validation of the RNG abstraction: reproducibility, independence and
distributional goodness-of-fit, all through the Python boundary.

The thresholds below are theory-based significance levels, not tuned values: a
correct stream fails a single test with probability ~1e-4, so the fixed seeds
here give a stable but meaningful check.
"""

from __future__ import annotations

import numpy as np
import pytest

import quantrisk

scipy_stats = pytest.importorskip("scipy.stats")

SAMPLE = 50_000


def test_same_seed_reproduces_the_identical_stream() -> None:
    first = quantrisk.Rng(2026).standard_normal_vector(SAMPLE)
    second = quantrisk.Rng(2026).standard_normal_vector(SAMPLE)
    assert first == second


def test_default_seed_is_the_documented_one() -> None:
    assert quantrisk.Rng().standard_normal_vector(5) == quantrisk.Rng(42).standard_normal_vector(5)


def test_different_seeds_do_not_reuse_a_stream() -> None:
    a = quantrisk.Rng(1).standard_normal_vector(1000)
    b = quantrisk.Rng(2).standard_normal_vector(1000)
    assert a != b


def test_consuming_one_engine_leaves_another_untouched() -> None:
    shared_seed = 99
    busy = quantrisk.Rng(shared_seed)
    busy.standard_normal_vector(500)
    busy.uniform01()
    idle = quantrisk.Rng(shared_seed)
    assert idle.standard_normal_vector(3) == quantrisk.Rng(shared_seed).standard_normal_vector(3)


def test_normal_sample_matches_scipy_by_ks_test() -> None:
    sample = np.array(quantrisk.Rng(7).standard_normal_vector(SAMPLE))
    result = scipy_stats.kstest(sample, "norm")
    assert result.pvalue > 1e-4, f"KS p-value {result.pvalue:.3e} for N=1e5 normals"


@pytest.mark.oracle
def test_normal_sample_matches_theory_within_five_standard_errors() -> None:
    sample = np.array(quantrisk.Rng(11).standard_normal_vector(SAMPLE))
    standard_error = 1.0 / np.sqrt(SAMPLE)
    assert abs(float(np.mean(sample))) < 5.0 * standard_error
    # Var(sample) has an approximate SE of sqrt(2/N) for a normal population.
    assert abs(float(np.var(sample, ddof=1)) - 1.0) < 5.0 * np.sqrt(2.0 / SAMPLE)


@pytest.mark.oracle
def test_uniform_sample_is_consistent_with_a_finite_eight_bin_chi_square_test() -> None:
    rng = quantrisk.Rng(13)
    draws = np.array([rng.uniform01() for _ in range(80_000)])
    assert draws.min() >= 0.0 and draws.max() < 1.0
    counts, _ = np.histogram(draws, bins=8, range=(0.0, 1.0))
    result = scipy_stats.chisquare(counts)
    assert result.pvalue > 1e-4, f"chi-square p-value {result.pvalue:.3e}"


def test_uniform_index_is_bounded_and_covers_its_range() -> None:
    rng = quantrisk.Rng(17)
    values = [rng.uniform_index(365) for _ in range(20_000)]
    assert min(values) >= 0
    assert max(values) < 365
    assert len(set(values)) == 365


def test_draw_counter_advances_only_when_the_engine_is_used() -> None:
    rng = quantrisk.Rng(5)
    assert rng.uniform_draws == 0
    rng.standard_normal_vector(10)
    after = rng.uniform_draws
    assert after > 0
    rng.standard_normal()
    assert rng.uniform_draws >= after


def test_numpy_arrays_convert_into_the_cpp_statistics_helpers() -> None:
    data = np.array([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert quantrisk.stats.mean(data) == pytest.approx(5.0, abs=0.0)
    assert quantrisk.stats.sample_variance(data) == pytest.approx(32.0 / 7.0)
