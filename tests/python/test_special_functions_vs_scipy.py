"""Level 2 validation of the special functions behind the test statistics.

SciPy is an oracle here and is never imported by the library itself; every
expected value is computed at run time rather than pasted in as a constant
(PROJECT_SPEC.md §4). These functions carry the Kupiec and Christoffersen
p-values, so an error in them would silently change a risk conclusion.
"""

from __future__ import annotations

import math
from itertools import combinations, pairwise

import numpy as np
import pytest
import quantrisk

scipy_stats = pytest.importorskip("scipy.stats")
scipy_special = pytest.importorskip("scipy.special")

# Both sides evaluate the same function in double precision with a handful of
# operations, so 1e-11 is ~10^5 times the rounding floor yet still fails on any
# real formula error (the g=7 Lanczos series with one wrong denominator is off
# by orders of magnitude, not by 1e-11).
REL_TOLERANCE = 1e-11


def _rel_err(ours: float, oracle: float) -> float:
    if oracle == 0.0:
        return abs(ours)
    return abs(ours - oracle) / abs(oracle)


@pytest.mark.oracle
def test_log_gamma_agrees_with_scipy_across_the_reflection_boundary() -> None:
    xs = np.concatenate(
        [
            np.linspace(0.02, 0.49, 60),
            np.linspace(0.5, 5.0, 90),
            np.geomspace(5.0, 200.0, 60),
        ]
    )
    errors = [
        _rel_err(quantrisk.special.log_gamma(float(x)), float(scipy_special.gammaln(x))) for x in xs
    ]
    worst = max(errors)
    assert worst < REL_TOLERANCE, f"max relative error = {worst:.3e}"


@pytest.mark.oracle
def test_incomplete_gamma_functions_agree_with_scipy() -> None:
    worst_p = 0.0
    worst_q = 0.0
    for a in (0.25, 0.5, 1.0, 2.5, 5.0, 20.0):
        for x in (0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 12.0, 40.0, 100.0):
            lower = quantrisk.special.regularized_lower_incomplete_gamma(a, x)
            upper = quantrisk.special.regularized_upper_incomplete_gamma(a, x)
            worst_p = max(worst_p, _rel_err(lower, float(scipy_special.gammainc(a, x))))
            worst_q = max(worst_q, _rel_err(upper, float(scipy_special.gammaincc(a, x))))
    assert worst_p < REL_TOLERANCE, f"max P(a,x) relative error = {worst_p:.3e}"
    assert worst_q < REL_TOLERANCE, f"max Q(a,x) relative error = {worst_q:.3e}"


@pytest.mark.oracle
def test_chi_square_survival_agrees_with_scipy_over_a_grid() -> None:
    worst = 0.0
    worst_point = None
    for dof in (1, 2, 3, 4, 5, 10, 25):
        for x in (0.001, 0.05, 0.5, 1.0, 3.0, 9.5, 20.0, 60.0, 100.0):
            ours = quantrisk.special.chi_square_sf(x, dof)
            oracle = float(scipy_stats.chi2.sf(x, dof))
            error = _rel_err(ours, oracle)
            if error > worst:
                worst, worst_point = error, (dof, x, ours, oracle)
    assert worst < 1e-9, f"max relative error {worst:.3e} at dof/x/ours/oracle = {worst_point}"


@pytest.mark.oracle
def test_chi_square_critical_values_agree_with_scipy() -> None:
    # These are the exact numbers a coverage test is judged against: a wrong
    # quantile flips a pass/fail conclusion without producing any error.
    worst = 0.0
    for dof in (1, 2, 3, 5, 10):
        for probability in (0.5, 0.1, 0.05, 0.01, 0.001):
            ours = quantrisk.special.chi_square_isf(probability, dof)
            oracle = float(scipy_stats.chi2.isf(probability, dof))
            worst = max(worst, _rel_err(ours, oracle))
    assert worst < 1e-10, f"max relative error = {worst:.3e}"


@pytest.mark.oracle
def test_chi_square_isf_inverts_the_survival_function_itself() -> None:
    for dof in (1, 2, 5, 10):
        for probability in (0.5, 0.05, 0.01):
            q = quantrisk.special.chi_square_isf(probability, dof)
            assert quantrisk.special.chi_square_sf(q, dof) == pytest.approx(probability, rel=1e-9)


@pytest.mark.oracle
def test_log_binomial_coefficient_agrees_with_exact_integers_and_scipy() -> None:
    for n, k in [(5, 2), (20, 3), (60, 30), (200, 7), (1000, 5), (1000, 500), (5000, 1)]:
        exact = math.log(math.comb(n, k))
        ours = quantrisk.special.log_binomial_coefficient(n, k)
        assert _rel_err(ours, exact) < 1e-12, (n, k, ours, exact)
        oracle = float(
            scipy_special.gammaln(n + 1)
            - scipy_special.gammaln(k + 1)
            - scipy_special.gammaln(n - k + 1)
        )
        assert _rel_err(ours, oracle) < 1e-12


def test_chi_square_and_log_gamma_reject_outside_their_domains() -> None:
    with pytest.raises(quantrisk.ValidationError):
        quantrisk.special.log_gamma(0.0)
    with pytest.raises(quantrisk.ValidationError):
        quantrisk.special.log_gamma(-2.0)
    with pytest.raises(quantrisk.ValidationError):
        quantrisk.special.chi_square_isf(0.0, 1)
    with pytest.raises(quantrisk.ValidationError):
        quantrisk.special.chi_square_isf(1.0, 1)
    with pytest.raises(quantrisk.ValidationError):
        quantrisk.special.chi_square_isf(0.05, 0)
    with pytest.raises(quantrisk.ValidationError):
        quantrisk.special.chi_square_sf(1.0, 0)


def test_monotonicity_that_a_hypothesis_test_depends_on() -> None:
    # A coverage test compares a statistic against a critical value, which is
    # only meaningful while the survival function decreases in x and the
    # quantile increases in dof.
    xs = np.linspace(0.05, 40.0, 400)
    sf = [quantrisk.special.chi_square_sf(float(x), 2) for x in xs]
    assert all(later <= earlier for earlier, later in pairwise(sf))
    critical = [quantrisk.special.chi_square_isf(0.05, dof) for dof in range(1, 40)]
    assert all(later > earlier for earlier, later in pairwise(critical))


def test_every_pair_of_dof_orders_the_same_critical_value_consistently() -> None:
    values = {dof: quantrisk.special.chi_square_isf(0.01, dof) for dof in (1, 2, 4, 8, 16)}
    for small, large in combinations(sorted(values), 2):
        assert values[small] < values[large]
