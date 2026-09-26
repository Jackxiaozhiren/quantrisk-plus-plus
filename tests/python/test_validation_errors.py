"""Domain validation must fail loudly at the boundary (PROJECT_SPEC.md Phase 1:
'invalid input')."""

from __future__ import annotations

import math

import pytest
import quantrisk


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_normal_cdf_rejects_non_finite_input(bad: float) -> None:
    with pytest.raises(quantrisk.ValidationError, match="'x'"):
        quantrisk.normal_cdf(bad)


@pytest.mark.parametrize("bad", [math.nan, math.inf])
def test_normal_pdf_rejects_non_finite_input(bad: float) -> None:
    with pytest.raises(quantrisk.ValidationError, match="'x'"):
        quantrisk.normal_pdf(bad)


@pytest.mark.parametrize("bad", [0.0, 1.0, -0.5, 1.5, math.nan])
def test_inverse_normal_cdf_rejects_probabilities_outside_the_open_unit_interval(
    bad: float,
) -> None:
    with pytest.raises(quantrisk.ValidationError, match="probability"):
        quantrisk.inverse_normal_cdf(bad)


def test_empty_and_degenerate_samples_are_rejected() -> None:
    with pytest.raises(quantrisk.ValidationError, match="non-empty"):
        quantrisk.stats.mean([])
    with pytest.raises(quantrisk.ValidationError, match="at least 2"):
        quantrisk.stats.sample_variance([1.0])
    with pytest.raises(quantrisk.ValidationError):
        quantrisk.stats.quantile([], 0.5)
    with pytest.raises(quantrisk.ValidationError, match="'k' exceeds the number of observations"):
        quantrisk.stats.mean_of_largest_sorted([1.0, 2.0], 3)


def test_quantile_probability_is_validated() -> None:
    with pytest.raises(quantrisk.ValidationError, match="'p'"):
        quantrisk.stats.quantile([1.0, 2.0, 3.0], 1.5)


def test_validation_error_is_a_value_error_so_callers_can_catch_either() -> None:
    assert issubclass(quantrisk.ValidationError, ValueError)


def test_error_message_names_the_offending_parameter() -> None:
    with pytest.raises(quantrisk.ValidationError) as excinfo:
        quantrisk.stats.mean_of_largest_sorted([1.0, 2.0], 0)
    assert "'k'" in str(excinfo.value)
