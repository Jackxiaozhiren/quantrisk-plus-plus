"""Phase 6 Level 2 validation: the portfolio layer against live solvers.

PyPortfolioOpt (SciPy SLSQP), cvxpy (OSQP / SCS) and scikit-learn appear here as
independent implementations of the *same* problems the C++ core solves with its
own active-set, coordinate-descent and simplex methods. Nothing from them is
imported by the library, and no reference vector is pasted in as a constant.

Tolerances are per problem, and the two kinds of number are kept apart on purpose.

The *objective* gap is the strong claim. On a strictly convex quadratic the achieved
value is pinned by the oracle's own stopping tolerance plus the curvature, so relative
bounds of 1e-13 (variance) and 1e-12 (Sharpe) are derived rather than observed - and
they sit far above the ~1e-16 actually measured, which means they test the solvers and
not the floating-point arithmetic.

The *weight* gap has no theoretical bound in two of the five problems, and so is not
pretended to anywhere. Near the tangency portfolio the frontier is flat: a 1e-12
bracket on the target return costs nothing in objective while moving coordinates by
~1e-9. And a linear program's optimum can be a face, so CVaR weights are only as sharp
as the vertex the solver happened to choose. Those two bounds are empirical - measured
worst case, rounded up, labelled as measured - and always reported beside the
objective gap instead of in place of it.

PyPortfolioOpt's `clean_weights()` is deliberately not used as the reference. It rounds
to five decimals and zeroes anything under 1e-4, which floors every comparison at ~5e-6
regardless of how tightly the optimiser converged; the test would then be measuring
that rounding rather than the optimisation.
"""

from __future__ import annotations

import itertools
import math

import numpy as np
import pytest
import quantrisk

pypfopt = pytest.importorskip("pypfopt")
cvxpy = pytest.importorskip("cvxpy")
pd = pytest.importorskip("pandas")

PORTFOLIO = quantrisk.portfolio

# Measured agreement against the raw solver output, bound rounded up:
#   min_variance / efficient_return  4.3e-13 (weights), 4.7e-16 (variance)
#   maximum_sharpe                   4.2e-09 (weights), 1.6e-16 (Sharpe)
#   risk_parity vs Spinu             1.8e-11 (weights), 2.0e-11 (variance)
#   min_cvar                         4.2e-07 (weights), 2.0e-08 (CVaR)
QUADRATIC_WEIGHT_TOLERANCE = 1e-11
QUADRATIC_VALUE_TOLERANCE = 1e-13
SHARPE_WEIGHT_TOLERANCE = 1e-7
SHARPE_VALUE_TOLERANCE = 1e-12
ERC_WEIGHT_TOLERANCE = 1e-9
CVAR_WEIGHT_TOLERANCE = 1e-5
CVAR_VALUE_TOLERANCE = 1e-6


def random_problem(assets: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed * 31 + assets)
    factor = rng.normal(0, 1, (assets, 1))
    loadings = rng.normal(0, 1, (assets, 2))
    covariance = (
        0.0009 * (factor @ factor.T) + 0.0004 * (loadings @ loadings.T) + 0.0004 * np.eye(assets)
    )
    expected_returns = rng.normal(0.06, 0.04, assets) / 12.0
    return covariance, expected_returns


def inputs(covariance: np.ndarray, expected_returns: np.ndarray | None = None) -> object:
    assets = covariance.shape[0]
    problem = PORTFOLIO.OptimizerInputs()
    problem.assets = assets
    problem.covariance = np.asarray(covariance, dtype=float).reshape(-1).tolist()
    if expected_returns is not None:
        problem.expected_returns = np.asarray(expected_returns, dtype=float).tolist()
    return problem


def reference_weights(optimizer: object, assets: int) -> np.ndarray:
    """The optimiser's raw answer, before PyPortfolioOpt rounds it to 5 decimals."""
    raw = getattr(optimizer, "weights", None)
    assert raw is not None, "the reference solve produced no weights to compare against"
    return np.asarray(raw, dtype=float).reshape(assets)


# --- minimum variance ----------------------------------------------------


@pytest.mark.oracle
@pytest.mark.parametrize("assets", [2, 3, 5, 8])
def test_minimum_variance_matches_pypfopt(assets: int) -> None:
    covariance, _ = random_problem(assets, seed=7)
    ours = PORTFOLIO.minimum_variance(inputs(covariance), PORTFOLIO.OptimizationRequest())
    assert ours.verified_optimal, ours.note

    frontier = pypfopt.EfficientFrontier(
        np.arange(assets) / assets, covariance, weight_bounds=(0, 1)
    )
    frontier.min_volatility()
    theirs = reference_weights(frontier, assets)
    our_weights = np.array(ours.weights)

    assert np.abs(our_weights - theirs).max() < QUADRATIC_WEIGHT_TOLERANCE
    their_variance = float(theirs @ covariance @ theirs)
    # One-sided on purpose. SLSQP stops at its own tolerance and can land slightly
    # above the optimum; our point carries a KKT certificate, so the honest claim
    # is "at least as good, and within the oracle's slack of its answer".
    assert ours.variance <= their_variance * (1.0 + QUADRATIC_VALUE_TOLERANCE)
    assert ours.variance == pytest.approx(their_variance, rel=QUADRATIC_VALUE_TOLERANCE)
    # The certificate is the part a benchmark cannot supply: sum to one, no
    # negative weight, no negative reduced cost.
    assert ours.budget_residual < 1e-12
    assert ours.weight_bound_violation < 1e-12


@pytest.mark.oracle
@pytest.mark.parametrize("assets", [3, 6])
def test_target_return_portfolio_matches_pypfopt(assets: int) -> None:
    covariance, expected_returns = random_problem(assets, seed=11)
    unconstrained = PORTFOLIO.minimum_variance(
        inputs(covariance, expected_returns), PORTFOLIO.OptimizationRequest()
    )
    target = float(expected_returns.max()) * 0.9

    request = PORTFOLIO.OptimizationRequest()
    request.target_return = target
    ours = PORTFOLIO.minimum_variance(inputs(covariance, expected_returns), request)
    assert ours.verified_optimal, ours.note
    assert ours.expected_return >= target - 1e-10
    assert ours.target_residual < 1e-10
    # A binding target cannot lower the variance.
    assert ours.variance >= unconstrained.variance - 1e-12

    frontier = pypfopt.EfficientFrontier(expected_returns, covariance, weight_bounds=(0, 1))
    frontier.efficient_return(target)
    theirs = reference_weights(frontier, assets)
    our_weights = np.array(ours.weights)
    assert np.abs(our_weights - theirs).max() < QUADRATIC_WEIGHT_TOLERANCE
    their_variance = float(theirs @ covariance @ theirs)
    assert ours.variance == pytest.approx(their_variance, rel=QUADRATIC_VALUE_TOLERANCE)


@pytest.mark.oracle
@pytest.mark.parametrize("assets", [3, 5, 7])
def test_maximum_sharpe_matches_pypfopt(assets: int) -> None:
    covariance, expected_returns = random_problem(assets, seed=13)
    risk_free = 0.002
    request = PORTFOLIO.OptimizationRequest()
    request.risk_free_rate = risk_free
    ours = PORTFOLIO.maximum_sharpe(inputs(covariance, expected_returns), request)
    assert ours.verified_optimal, ours.note

    frontier = pypfopt.EfficientFrontier(expected_returns, covariance, weight_bounds=(0, 1))
    frontier.max_sharpe(risk_free_rate=risk_free)
    theirs = reference_weights(frontier, assets)
    our_weights = np.array(ours.weights)
    # The weight bound here is loose *relative to what is measured* (4.2e-9 achieved,
    # 1e-7 asserted) because the frontier is flat at the tangency point: coordinates
    # are not identified by the objective to better than the target-return bracket.
    # The claim that carries the weight is the Sharpe comparison underneath this one.
    assert np.abs(our_weights - theirs).max() < SHARPE_WEIGHT_TOLERANCE

    def achieved(weights: np.ndarray) -> float:
        return (float(weights @ expected_returns) - risk_free) / math.sqrt(
            float(weights @ covariance @ weights)
        )

    assert achieved(our_weights) == pytest.approx(achieved(theirs), rel=SHARPE_VALUE_TOLERANCE)

    # No frontier point may beat the reported Sharpe: this checks the search over
    # target returns rather than trusting either solver.
    probe = PORTFOLIO.OptimizationRequest()
    probe.risk_free_rate = risk_free
    grid = np.linspace(float(expected_returns.min()), float(expected_returns.max()), 25)
    for point in PORTFOLIO.efficient_frontier(inputs(covariance, expected_returns), grid, probe):
        if point.verified_optimal:
            assert point.sharpe_ratio <= ours.sharpe_ratio + 1e-6


# --- risk parity ---------------------------------------------------------


@pytest.mark.oracle
@pytest.mark.parametrize("assets", [2, 3, 5, 8])
def test_risk_parity_matches_the_convex_log_formulation(assets: int) -> None:
    covariance, _ = random_problem(assets, seed=17)
    ours = PORTFOLIO.risk_parity(np.asarray(covariance).reshape(-1).tolist(), assets)
    assert ours.converged, ours.note
    assert ours.max_contribution_gap < 1e-8
    assert sum(ours.contributions) == pytest.approx(1.0, abs=1e-12)

    # Spinu's problem: max sum(log x) s.t. x' Sigma x <= 1. Its solution is the
    # ERC portfolio, and cvxpy reaches it by a completely different route.
    variables = cvxpy.Variable(assets)
    problem = cvxpy.Problem(
        cvxpy.Maximize(cvxpy.sum(cvxpy.log(variables))),
        [cvxpy.quad_form(variables, cvxpy.psd_wrap(covariance)) <= 1.0],
    )
    problem.solve(solver=cvxpy.SCS, eps=1e-11)
    reference = np.asarray(variables.value).flatten()
    reference /= reference.sum()
    assert np.abs(np.array(ours.weights) - reference).max() < ERC_WEIGHT_TOLERANCE


# --- CVaR ----------------------------------------------------------------


@pytest.mark.oracle
@pytest.mark.parametrize(("assets", "scenarios"), [(2, 12), (3, 40), (5, 60)])
def test_min_cvar_matches_pypfopt_and_cvxpy(assets: int, scenarios: int) -> None:
    covariance, expected_returns = random_problem(assets, seed=19)
    rng = np.random.default_rng(23)
    returns = rng.multivariate_normal(expected_returns, covariance, size=scenarios)
    beta = 0.9

    request = PORTFOLIO.CvarRequest()
    request.assets = assets
    request.scenarios = scenarios
    request.scenario_returns = returns.reshape(-1).tolist()
    request.confidence = beta
    ours = PORTFOLIO.minimise_cvar(request)
    assert ours.solved and ours.certified, ours.note
    assert ours.budget_residual < 1e-9
    assert ours.weight_bound_violation < 1e-9
    assert ours.alpha <= ours.cvar + 1e-9
    assert ours.recomputed_cvar == pytest.approx(ours.cvar, rel=1e-9)

    columns = [f"a{i}" for i in range(assets)]
    frame = pd.DataFrame(returns, columns=columns)
    frontier = pypfopt.EfficientCVaR(expected_returns, frame, beta=beta)
    frontier.min_cvar()
    theirs = reference_weights(frontier, assets)
    our_weights = np.array(ours.weights)
    # Measured 4.2e-7 against a 1e-5 bound: an LP optimum can be a whole face, so the
    # simplex and OSQP's interior-point path need not report the same vertex. The
    # objective comparison below is the one that cannot be explained away that way.
    assert np.abs(our_weights - theirs).max() < CVAR_WEIGHT_TOLERANCE

    # Our objective must be no worse than the oracle's when both are evaluated on
    # the same definition, which is the direction that matters for a minimisation.
    def empirical_tail_mean(weights: np.ndarray) -> float:
        losses = np.sort(-(returns @ weights))[::-1]
        tail = (1.0 - beta) * scenarios
        whole = int(math.floor(tail))
        fraction = tail - whole
        total = losses[:whole].sum()
        if whole < scenarios:
            total += fraction * losses[whole]
        return float(total / tail)

    ours_tail = empirical_tail_mean(np.array(ours.weights))
    theirs_tail = empirical_tail_mean(theirs)
    # One-sided first: our answer must not be worse on the shared definition.
    assert ours_tail <= theirs_tail + 1e-12
    # Then the magnitude of the difference, so "no worse" cannot be satisfied by two
    # answers that are both far from the optimum.
    assert ours_tail == pytest.approx(theirs_tail, rel=CVAR_VALUE_TOLERANCE)


# --- robustness: the four cases the Phase 6 gate names -------------------


def test_a_zero_variance_asset_is_handled_by_every_route() -> None:
    # Asset 1 never moves, so it is the minimum-variance portfolio outright.
    covariance = np.array([[0.04, 0.0], [0.0, 0.0]])
    flat = np.asarray(covariance).reshape(-1).tolist()
    minimum = PORTFOLIO.minimum_variance(inputs(covariance), PORTFOLIO.OptimizationRequest())
    assert minimum.verified_optimal, minimum.note
    assert minimum.weights[0] == pytest.approx(0.0, abs=1e-9)
    assert minimum.weights[1] == pytest.approx(1.0, abs=1e-9)
    assert minimum.variance == pytest.approx(0.0, abs=1e-18)

    parity = PORTFOLIO.risk_parity(flat, 2)
    assert not parity.converged
    assert "zero variance" in parity.note

    solve = PORTFOLIO.solve(flat, 2, [1.0, 1.0])
    assert not solve.solved
    assert math.isnan(solve.values[0])


def test_highly_correlated_assets_keep_the_solution_meaningful() -> None:
    rng = np.random.default_rng(29)
    base = rng.normal(0, 0.02, (500, 1))
    twin = base + rng.normal(0, 2e-6, (500, 1))
    returns = np.column_stack([base, twin, rng.normal(0, 0.02, (500, 1))])
    covariance = PORTFOLIO.sample_covariance(returns.reshape(-1).tolist(), 3, 500)
    assert PORTFOLIO.condition_number(covariance) > 1e8
    minimum = PORTFOLIO.minimum_variance(
        inputs(np.array(covariance.values).reshape(3, 3)), PORTFOLIO.OptimizationRequest()
    )
    assert minimum.feasible
    assert minimum.budget_residual < 1e-9
    assert min(minimum.weights) > -1e-9
    assert "ill-conditioned" in covariance.note or "condition number" in covariance.note


def test_a_singular_sample_is_shrunk_before_being_used() -> None:
    # 6 assets, 5 observations: the sample covariance cannot be inverted, and the
    # documented route is the shrinkage estimator, not a hidden regulariser.
    covariance, _ = random_problem(6, seed=31)
    rng = np.random.default_rng(37)
    returns = rng.normal(0, 0.02, (5, 6))
    thin = PORTFOLIO.sample_covariance(returns.reshape(-1).tolist(), 6, 5)
    shrunk = PORTFOLIO.shrinkage_covariance(returns.reshape(-1).tolist(), 6, 5)
    assert thin.smallest_eigenvalue <= 1e-18
    assert shrunk.smallest_eigenvalue > 0.0

    problem = inputs(np.array(shrunk.values).reshape(6, 6))
    solution = PORTFOLIO.minimum_variance(problem, PORTFOLIO.OptimizationRequest())
    assert solution.verified_optimal, solution.note
    assert np.all(np.array(solution.weights) > -1e-9)
    del covariance


def test_near_collinearity_is_reported_not_swallowed() -> None:
    returns = np.column_stack([np.linspace(-0.02, 0.02, 50), np.linspace(-0.02, 0.0200001, 50)])
    estimate = PORTFOLIO.sample_covariance(returns.reshape(-1).tolist(), 2, 50)
    assert PORTFOLIO.condition_number(estimate) > 1e8
    # Almost-identical columns are singular to within the relative tolerance, so
    # the estimate says "rank-deficient"; a merely ill-conditioned pair says
    # "condition number". Either is the point: the estimate names its own defect.
    assert "singular" in estimate.note or "condition number" in estimate.note


# --- the optimisers keep the caller informed ----------------------------


def test_optimisers_reject_impossible_requests() -> None:
    covariance = np.array([[0.04, 0.006], [0.006, 0.09]])
    with pytest.raises(quantrisk.ValidationError):
        PORTFOLIO.minimum_variance(inputs(covariance, None), _with_target(0.05))
    mismatched = PORTFOLIO.OptimizerInputs()
    mismatched.assets = 3  # but the matrix below is 2 x 2
    mismatched.covariance = covariance.reshape(-1).tolist()
    with pytest.raises(quantrisk.ValidationError):
        PORTFOLIO.minimum_variance(mismatched, _empty())
    with pytest.raises(quantrisk.ValidationError):
        PORTFOLIO.risk_parity(np.array([[0.04, 0.0], [0.0, 0.0]]).reshape(-1).tolist(), 3)
    with pytest.raises(quantrisk.ValidationError):
        PORTFOLIO.risk_parity(
            np.array([[0.04, 0.0], [0.0, 0.0]]).reshape(-1).tolist(), 2, [1.0, 0.0]
        )
    request = PORTFOLIO.CvarRequest()
    request.assets = 2
    request.scenarios = 3
    request.scenario_returns = [0.01, 0.02, 0.03]
    request.confidence = 0.9
    with pytest.raises(quantrisk.ValidationError):
        PORTFOLIO.minimise_cvar(request)


def test_scenario_losses_are_reported_on_the_chosen_weights() -> None:
    rng = np.random.default_rng(41)
    covariance, expected_returns = random_problem(3, seed=43)
    scenarios = rng.multivariate_normal(expected_returns, covariance, size=200)
    problem = inputs(covariance, expected_returns)
    problem.scenario_returns = scenarios.reshape(-1).tolist()
    problem.scenario_count = 200
    request = PORTFOLIO.OptimizationRequest()
    request.cvar_confidence = 0.95
    solution = PORTFOLIO.minimum_variance(problem, request)
    weights = np.array(solution.weights)
    losses = np.sort(-(scenarios @ weights))[::-1]
    tail = 0.05 * 200
    whole = int(math.floor(tail))
    expected = float(losses[:whole].sum() / tail)
    assert solution.conditional_var == pytest.approx(expected, rel=1e-9)
    assert math.isfinite(solution.value_at_risk)
    assert solution.conditional_var >= solution.value_at_risk


def _empty() -> object:
    return PORTFOLIO.OptimizationRequest()


def _with_target(target: float) -> object:
    request = PORTFOLIO.OptimizationRequest()
    request.target_return = target
    return request


def test_every_solution_reports_the_six_benchmark_quantities() -> None:
    """The Phase 6 gate names them; a caller must not have to derive them."""
    covariance, expected_returns = random_problem(4, seed=47)
    solution = PORTFOLIO.minimum_variance(inputs(covariance, expected_returns), _empty())
    for field in (
        "weights",
        "expected_return",
        "volatility",
        "sharpe_ratio",
        "value_at_risk",
        "budget_residual",
        "verified_optimal",
        "note",
    ):
        assert hasattr(solution, field), field
    assert len(solution.weights) == 4
    assert solution.volatility > 0.0
    assert math.isnan(solution.sharpe_ratio), "no risk-free rate was supplied"
    for pair in itertools.combinations(range(4), 2):
        assert solution.weights[pair[0]] * solution.weights[pair[1]] >= -1e-12
