"""Phase 6 Level 2 validation: covariance estimators against live oracles.

NumPy, pandas, scikit-learn and PyPortfolioOpt are references only; none of them
is imported by the library, and no expected matrix is pasted in as a constant
(PROJECT_SPEC.md §4). Where a convention differs, the test bridges it explicitly
and asserts the *stated* relationship rather than quietly matching the tolerance
to whatever came out.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import quantrisk

sklearn_covariance = pytest.importorskip("sklearn.covariance")

PORTFOLIO = quantrisk.portfolio

MATRIX_TOLERANCE = 1e-12


def correlated_sample(observations: int, assets: int, seed: int) -> np.ndarray:
    """Returns with a common factor, so the matrix is dense and non-diagonal."""
    rng = np.random.default_rng(seed)
    common = rng.standard_normal((observations, 1))
    return (0.6 * common + 0.4 * rng.standard_normal((observations, assets))) * 0.02


def flat(matrix: np.ndarray) -> np.ndarray:
    return np.asarray(matrix, dtype=float).reshape(-1)


def worst_relative_difference(ours: np.ndarray, oracle: np.ndarray) -> float:
    scale = float(np.abs(oracle).max())
    if scale == 0.0:
        return float(np.abs(ours).max())
    return float(np.abs(ours - oracle).max() / scale)


# --- sample covariance ---------------------------------------------------


@pytest.mark.oracle
@pytest.mark.parametrize(
    ("observations", "assets"),
    [(2, 1), (3, 2), (50, 4), (500, 7), (40, 12)],
)
def test_sample_covariance_matches_numpy(observations: int, assets: int) -> None:
    sample = correlated_sample(observations, assets, seed=observations + assets)
    ours = PORTFOLIO.sample_covariance(flat(sample), assets, observations)
    oracle = np.cov(sample, rowvar=False, ddof=1).reshape(assets, assets)
    assert ours.values == pytest.approx(flat(oracle), rel=MATRIX_TOLERANCE, abs=1e-24)
    assert worst_relative_difference(np.array(ours.values).reshape(assets, assets), oracle) < 1e-12


@pytest.mark.oracle
def test_measured_spectrum_matches_numpy() -> None:
    sample = correlated_sample(400, 6, seed=3)
    ours = PORTFOLIO.sample_covariance(flat(sample), 6, 400)
    oracle = np.sort(np.linalg.eigvalsh(np.array(ours.values).reshape(6, 6)))
    assert PORTFOLIO.eigenvalues(flat(np.array(ours.values)), 6) == pytest.approx(
        list(oracle), rel=1e-10, abs=1e-24
    )
    assert PORTFOLIO.condition_number(ours) == pytest.approx(
        float(np.linalg.cond(np.array(ours.values).reshape(6, 6))), rel=1e-8
    )


def test_sample_covariance_is_symmetric_bit_for_bit() -> None:
    sample = correlated_sample(120, 5, seed=4)
    values = np.array(PORTFOLIO.sample_covariance(flat(sample), 5, 120).values).reshape(5, 5)
    assert (values == values.T).all(), "callers index the flat buffer directly"


# --- Ledoit-Wolf shrinkage -----------------------------------------------


@pytest.mark.oracle
@pytest.mark.parametrize(
    ("observations", "assets"),
    [(300, 5), (40, 8), (5000, 3), (10, 20), (60, 60)],
)
def test_shrinkage_matches_scikit_learn_in_matrix_and_intensity(
    observations: int, assets: int
) -> None:
    """scikit-learn implements the same published estimator, so agreement is exact.

    The p > n rows matter most: there the plain sample covariance is singular and
    the shrunk one must be invertible, which is the whole reason the estimator exists.
    """
    sample = correlated_sample(observations, assets, seed=observations * 7 + assets)
    ours = PORTFOLIO.shrinkage_covariance(flat(sample), assets, observations)
    oracle = sklearn_covariance.LedoitWolf(store_precision=False).fit(sample)

    assert ours.shrinkage_intensity == pytest.approx(float(oracle.shrinkage_), rel=1e-9)
    assert (
        worst_relative_difference(
            np.array(ours.values).reshape(assets, assets), np.asarray(oracle.covariance_)
        )
        < 1e-12
    ), "the intensity matches but the matrix does not"


@pytest.mark.oracle
def test_shrinkage_makes_a_singular_estimate_invertible() -> None:
    sample = correlated_sample(20, 40, seed=6)
    plain = PORTFOLIO.sample_covariance(flat(sample), 40, 20)
    shrunk = PORTFOLIO.shrinkage_covariance(flat(sample), 40, 20)
    assert shrunk.shrinkage_intensity > 0.0
    assert shrunk.smallest_eigenvalue > 0.0
    assert shrunk.positive_semidefinite
    # The condition number improvement is the point of the exercise: the plain
    # estimate is unusable (infinite or astronomically bad), the shrunk one is finite.
    plain_condition = PORTFOLIO.condition_number(plain)
    assert math.isinf(plain_condition) or plain_condition > 1e15
    assert math.isfinite(PORTFOLIO.condition_number(shrunk))
    assert PORTFOLIO.condition_number(shrunk) < 1e6
    rhs = np.ones(40)
    assert PORTFOLIO.solve(shrunk.values, 40, flat(rhs)).solved


# --- EWMA ----------------------------------------------------------------


def numpy_ewma_about_zero(sample: np.ndarray, lam: float) -> np.ndarray:
    """Independent implementation of the documented estimator."""
    observations = sample.shape[0]
    weights = np.array([lam ** (observations - 1 - t) for t in range(observations)])
    weights /= weights.sum()
    return (sample * weights[:, None]).T @ sample


@pytest.mark.oracle
@pytest.mark.parametrize("lam", [0.94, 0.97, 0.5, 1.0])
def test_ewma_matches_an_independent_weighted_second_moment(lam: float) -> None:
    sample = correlated_sample(200, 4, seed=11)
    ours = np.array(PORTFOLIO.ewma_covariance(flat(sample), 4, 200, lam).values).reshape(4, 4)
    oracle = numpy_ewma_about_zero(sample, lam)
    assert worst_relative_difference(ours, oracle) < 1e-13


def test_ewma_half_life_is_the_documented_function_of_lambda() -> None:
    for lam in (0.94, 0.99, 0.5):
        estimate = PORTFOLIO.ewma_covariance(flat(correlated_sample(50, 2, 12)), 2, 50, lam)
        assert estimate.half_life == pytest.approx(math.log(0.5) / math.log(lam), rel=1e-14)
    infimum = PORTFOLIO.ewma_covariance(flat(correlated_sample(50, 2, 12)), 2, 50, 1.0)
    assert math.isinf(infimum.half_life)


@pytest.mark.oracle
def test_ewma_matches_pypfopt_once_its_conventions_are_bridged() -> None:
    """PyPortfolioOpt's `exp_cov` is a *centred* EWMA, annualised and PSD-repaired.

    The bridge is asserted, not assumed:
      * span -> lambda: pandas' `ewm(span, adjust=True)` weights `(1-alpha)^k` with
        `alpha = 2/(span+1)`, so `lambda = (span-1)/(span+1)`;
      * centring: their covariation uses each series' full-sample mean, so the same
        series are demeaned before entering our about-zero estimator;
      * annualisation: their result is multiplied by `frequency`.
    If any of those mappings is wrong the comparison fails, which is the point.
    """
    pypfopt_risk_models = pytest.importorskip("pypfopt.risk_models")
    pd = pytest.importorskip("pandas")

    observations, assets, span, frequency = 400, 4, 60, 252
    sample = correlated_sample(observations, assets, seed=13)
    columns = [f"A{i}" for i in range(assets)]
    frame = pd.DataFrame(sample, columns=columns)

    oracle = np.asarray(
        pypfopt_risk_models.exp_cov(frame, returns_data=True, span=span, frequency=frequency)
    )
    lam = (span - 1) / (span + 1)
    demeaned = sample - sample.mean(axis=0)
    ours = (
        np.array(
            PORTFOLIO.ewma_covariance(flat(demeaned), assets, observations, lam).values
        ).reshape(assets, assets)
        * frequency
    )

    difference = worst_relative_difference(ours, oracle)
    assert difference < 1e-10, f"convention bridge failed, max relative difference {difference:.3e}"


# --- robustness suite (the Phase 6 gate) ---------------------------------


def test_a_zero_variance_asset_is_reported_not_silently_inverted() -> None:
    sample = correlated_sample(200, 3, seed=14)
    sample = np.column_stack([sample, np.full(200, 0.01)])  # fourth asset is flat
    estimate = PORTFOLIO.sample_covariance(flat(sample), 4, 200)
    assert estimate.smallest_eigenvalue == pytest.approx(0.0, abs=1e-20)
    assert estimate.positive_semidefinite
    assert "singular" in estimate.note
    assert math.isinf(PORTFOLIO.condition_number(estimate)) or (
        PORTFOLIO.condition_number(estimate) > 1e14
    )
    refused = PORTFOLIO.solve(estimate.values, 4, [1.0, 1.0, 1.0, 1.0])
    assert not refused.solved
    assert np.isnan(refused.values).all()
    assert refused.note


def test_near_collinear_assets_inflate_the_condition_number_and_shrinkage_fixes_it() -> None:
    rng = np.random.default_rng(15)
    base = rng.standard_normal((500, 1)) * 0.02
    twin = base + rng.standard_normal((500, 1)) * 1e-6  # correlation ~ 1 - eps
    sample = np.column_stack([base, twin, rng.standard_normal((500, 1)) * 0.02])
    plain = PORTFOLIO.sample_covariance(flat(sample), 3, 500)
    shrunk = PORTFOLIO.shrinkage_covariance(flat(sample), 3, 500)
    assert PORTFOLIO.condition_number(plain) > 1e8
    assert PORTFOLIO.condition_number(shrunk) < PORTFOLIO.condition_number(plain)
    assert "condition number" in plain.note and "unstable" in plain.note


def test_highly_correlated_pair_keeps_a_positive_definite_estimate() -> None:
    rng = np.random.default_rng(16)
    common = rng.standard_normal((2000, 1))
    noise = rng.standard_normal((2000, 2)) * 0.05
    # Two near-identical series (independent microstructure noise), not the same
    # column twice: duplication would make it exactly rank-deficient on purpose.
    sample = 0.02 * np.column_stack([common + noise[:, :1], common + noise[:, 1:2]]) / 0.02
    estimate = PORTFOLIO.sample_covariance(flat(sample), 2, 2000)
    assert estimate.smallest_eigenvalue > 0.0
    assert estimate.positive_semidefinite


def test_estimators_validate_shapes_and_finite_inputs() -> None:
    with pytest.raises(quantrisk.ValidationError):
        PORTFOLIO.sample_covariance([0.1, 0.2, 0.3], 2, 2)
    with pytest.raises(quantrisk.ValidationError):
        PORTFOLIO.sample_covariance([0.1, 0.2], 2, 1)
    with pytest.raises(quantrisk.ValidationError):
        PORTFOLIO.ewma_covariance([0.1, 0.2, 0.3, 0.4], 2, 2, 0.0)
    with pytest.raises(quantrisk.ValidationError):
        PORTFOLIO.ewma_covariance([0.1, 0.2, 0.3, 0.4], 2, 2, 1.2)
    with pytest.raises(quantrisk.ValidationError):
        PORTFOLIO.shrinkage_covariance([float("nan"), 0.2, 0.3, 0.4], 2, 2)
    with pytest.raises(quantrisk.ValidationError):
        PORTFOLIO.solve([1.0, 0.0], 2, [1.0])


def test_estimators_accept_a_flat_sequence_from_either_container() -> None:
    # The contract is flat row-major with explicit dimensions; flattening a 2-D
    # frame is the caller's job, and the Phase 9 facades will do it for DataFrames.
    sample = correlated_sample(60, 3, seed=17)
    from_array = PORTFOLIO.sample_covariance(flat(sample), 3, 60)
    from_list = PORTFOLIO.sample_covariance(sample.reshape(-1).tolist(), 3, 60)
    assert from_array.values == from_list.values
    with pytest.raises(quantrisk.ValidationError):
        PORTFOLIO.sample_covariance(flat(sample), 3, 61)  # shape does not fit the data
    with pytest.raises(TypeError):
        PORTFOLIO.sample_covariance(sample, 3, 60)  # a 2-D array is not flat
