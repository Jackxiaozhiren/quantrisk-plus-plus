"""Level 2 validation of the distribution helpers against SciPy, run live.

SciPy is an *oracle* here: it is never imported by the library, and its outputs
are compared at run time rather than being pasted into the test as constants
(PROJECT_SPEC.md §4).
"""

from __future__ import annotations

import numpy as np
import pytest

import quantrisk

scipy_stats = pytest.importorskip("scipy.stats")
scipy.special = pytest.importorskip("scipy.special")

# Tolerance rationale: both sides evaluate the same mathematical function with
# a handful of double operations, so agreement at the 1e-12 level is far looser
# than the ~1e-16 rounding floor and still catches any real formula error.
ABS_TOLERANCE = 1e-12


@pytest.mark.oracle
def test_normal_cdf_agrees_with_scipy_over_the_whole_useful_range() -> None:
    xs = np.linspace(-8.0, 8.0, 1601)
    ours = np.array([quantrisk.normal_cdf(float(x)) for x in xs])
    oracle = scipy_stats.norm.cdf(xs)
    max_error = float(np.max(np.abs(ours - oracle)))
    assert max_error < ABS_TOLERANCE, f"max |cdf error| = {max_error:.3e}"


@pytest.mark.oracle
def test_normal_pdf_agrees_with_scipy() -> None:
    xs = np.linspace(-10.0, 10.0, 1601)
    ours = np.array([quantrisk.normal_pdf(float(x)) for x in xs])
    oracle = scipy_stats.norm.pdf(xs)
    max_error = float(np.max(np.abs(ours - oracle)))
    assert max_error < ABS_TOLERANCE, f"max |pdf error| = {max_error:.3e}"


@pytest.mark.oracle
def test_inverse_normal_cdf_agrees_with_scipy_ppf() -> None:
    probabilities = np.concatenate(
        [
            np.logspace(-12, -3, 40),
            np.linspace(1e-3, 1 - 1e-3, 400),
            1.0 - np.logspace(-12, -3, 40)[::-1],
        ]
    )
    ours = np.array([quantrisk.inverse_normal_cdf(float(p)) for p in probabilities])
    oracle = scipy_stats.norm.ppf(probabilities)
    max_error = float(np.max(np.abs(ours - oracle)))
    assert max_error < ABS_TOLERANCE, f"max |ppf error| = {max_error:.3e}"


@pytest.mark.oracle
def test_erfc_identity_holds_for_the_library_definition() -> None:
    xs = np.linspace(-6.0, 6.0, 601)
    ours = np.array([quantrisk.normal_cdf(float(x)) for x in xs])
    oracle = 0.5 * scipy.special.erfc(-xs / np.sqrt(2.0))
    # Cephes' erfc and libm's erfc agree to a few ulps; anything larger would
    # mean the core does not actually implement N(x) = 0.5 * erfc(-x / sqrt 2).
    max_error = float(np.max(np.abs(ours - oracle)))
    assert max_error < 1e-15, f"max |erfc identity residual| = {max_error:.3e}"
