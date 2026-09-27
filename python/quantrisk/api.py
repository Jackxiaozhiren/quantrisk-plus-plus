"""The research API: small Python facades over the C++ core.

PROJECT_SPEC.md §Phase 9 is explicit that Python is the orchestration layer and must not
reimplement the algorithms, and that constraint shapes everything here. Each method below
does three things and no more: translate a keyword argument into the core's positional
shape, call one core function, and return its result — occasionally renamed. There is no
arithmetic in this module beyond assembling arguments.

That is a real limitation as well as a discipline. A facade that adds no numerics cannot
get them wrong, but it also cannot fix an awkward core signature; where the two disagree
the facade changes the *name* (the core's `price_call` becomes `price_european_call`, which
is what a reader of a research notebook expects) and never the computation.

Every object exposes `__core__` so a test can assert a result came from the extension
rather than from a Python-side approximation.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ._quantrisk import monte_carlo as _mc
from ._quantrisk import portfolio as _portfolio
from ._quantrisk import pricing as _pricing
from ._quantrisk import risk as _risk
from ._quantrisk import stress as _stress

__all__ = [
    "BlackScholes",
    "MonteCarloEngine",
    "PortfolioOptimizer",
    "RiskEngine",
    "ScenarioEngine",
]


class BlackScholes:
    """`BlackScholes(spot=…, strike=…, rate=…, vol=…, maturity=…)`.

    Volatility is annualised and maturity in years, matching the core; theta is per
    calendar year and vega/rho per unit, which is what the QuantLib comparison in Phase 2
    measured rather than assumed.

    A degenerate input (zero maturity, zero spot) is not special-cased here. The core
    already classifies it and reports it through `PricingResult.note`, and a facade that
    pre-empted that would hide the one place the edge cases are described.
    """

    __core__ = _pricing

    def __init__(
        self,
        *,
        spot: float,
        strike: float,
        rate: float,
        vol: float,
        maturity: float,
        dividend_yield: float = 0.0,
    ) -> None:
        self._market = _pricing.MarketParams(
            spot=float(spot),
            rate=float(rate),
            dividend_yield=float(dividend_yield),
            volatility=float(vol),
            maturity=float(maturity),
        )
        self._call = _pricing.EuropeanOption(_pricing.OptionType.CALL, float(strike))
        self._put = _pricing.EuropeanOption(_pricing.OptionType.PUT, float(strike))
        self.strike = float(strike)

    def __repr__(self) -> str:
        return (
            f"BlackScholes(spot={self._market.spot}, strike={self.strike}, "
            f"rate={self._market.rate}, vol={self._market.volatility}, "
            f"maturity={self._market.maturity}, dividend_yield="
            f"{self._market.dividend_yield})"
        )

    @property
    def market(self) -> Any:
        return self._market

    def call_price(self) -> float:
        return _pricing.black_scholes(self._call, self._market).price

    def put_price(self) -> float:
        return _pricing.black_scholes(self._put, self._market).price

    def result(self, *, put: bool = False) -> Any:
        """The full `PricingResult`, including the note on a degenerate edge."""
        return _pricing.black_scholes(self._put if put else self._call, self._market)

    def greeks(self, *, put: bool = False) -> Any:
        return _pricing.black_scholes_greeks(self._put if put else self._call, self._market)

    def finite_difference_greeks(self, *, spot_relative: float | None = None) -> Any:
        """Central-difference Greeks, for checking the analytic ones rather than using them.

        The core's default bump policy is already tuned for accuracy against the analytic
        values, so the only knob exposed is the spot bump; anything finer belongs in the
        core, not in a Python default chosen here.
        """
        policy = _pricing.BumpPolicy()
        if spot_relative is not None:
            policy.spot_relative = float(spot_relative)
        return _pricing.finite_difference_greeks(self._call, self._market, policy)

    def put_call_parity_residual(self) -> float:
        return _pricing.put_call_parity_residual(self._market, self.strike)

    def binomial(self, *, steps: int = 500, american: bool = False, put: bool = False) -> Any:
        style = _pricing.ExerciseStyle.AMERICAN if american else _pricing.ExerciseStyle.EUROPEAN
        option = self._put if put else self._call
        return _pricing.crr_binomial(option, self._market, style, int(steps))


class MonteCarloEngine:
    """`MonteCarloEngine(seed=42)` — one seed, reproducible for a whole session.

    The core owns its `mt19937_64` per instance, so two engines built with the same seed
    produce identical streams and an engine never disturbs another's sequence. The facade
    keeps that property by holding exactly one core engine and never reseeding it.
    """

    __core__ = _mc

    def __init__(self, *, seed: int = 42) -> None:
        self._engine = _mc.MonteCarloEngine(seed=int(seed))

    def __repr__(self) -> str:
        return f"MonteCarloEngine(seed={self._engine.seed})"

    @property
    def seed(self) -> int:
        return int(self._engine.seed)

    @staticmethod
    def _market(spot: float, rate: float, vol: float, maturity: float, dividend_yield: float):
        return _pricing.MarketParams(
            spot=float(spot),
            rate=float(rate),
            dividend_yield=float(dividend_yield),
            volatility=float(vol),
            maturity=float(maturity),
        )

    def price_european_call(
        self,
        *,
        spot: float,
        strike: float,
        rate: float,
        vol: float,
        maturity: float,
        dividend_yield: float = 0.0,
        paths: int = 100_000,
        variance_reduction: Any = _mc.VarianceReduction.NONE,
        confidence_level: float = 0.95,
    ) -> Any:
        """Antithetic and control-variate options live on the core's enum, unchanged."""
        return self._engine.price_call(
            self._market(spot, rate, vol, maturity, dividend_yield),
            float(strike),
            int(paths),
            variance_reduction,
            float(confidence_level),
        )

    def price_european_put(self, **kwargs: Any) -> Any:
        strike = kwargs.pop("strike")
        return self._engine.price_put(
            self._market(
                kwargs.pop("spot"),
                kwargs.pop("rate"),
                kwargs.pop("vol"),
                kwargs.pop("maturity"),
                kwargs.pop("dividend_yield", 0.0),
            ),
            float(strike),
            int(kwargs.pop("paths", 100_000)),
            kwargs.pop("variance_reduction", _mc.VarianceReduction.NONE),
            float(kwargs.pop("confidence_level", 0.95)),
        )

    def price_option(
        self,
        option: Any,
        *,
        market: Any,
        paths: int = 100_000,
        variance_reduction: Any = _mc.VarianceReduction.NONE,
        confidence_level: float = 0.95,
    ) -> Any:
        return self._engine.price_european(
            option, market, int(paths), variance_reduction, float(confidence_level)
        )

    def price_asian(self, **kwargs: Any) -> Any:
        return _mc.price_asian(**kwargs)

    def price_barrier(self, **kwargs: Any) -> Any:
        return _mc.price_barrier(**kwargs)

    def price_geometric_asian(self, **kwargs: Any) -> Any:
        return _mc.price_geometric_asian(**kwargs)


class PortfolioOptimizer:
    """A covariance, an optional expected-return vector, and the five Phase 6 solvers.

    Constructed once, solved many times: the inputs are converted to the core's container
    shape on construction so a caller cannot accidentally solve two different matrices by
    mutating a list between calls.

    Nothing here estimates expected returns. The core does not and neither does this, and
    the Phase 6 experiment measured what happens when a sample mean is used as if it were
    skill — max-Sharpe was the worst of four objectives on every forward metric.
    """

    __core__ = _portfolio

    def __init__(
        self,
        covariance: Sequence[float] | Sequence[Sequence[float]],
        expected_returns: Sequence[float] | None = None,
        *,
        assets: int | None = None,
    ) -> None:
        matrix = _flatten(covariance)
        count = int(assets) if assets is not None else _square_size(matrix)
        self.assets = count
        self._inputs = _portfolio.OptimizerInputs()
        self._inputs.assets = count
        self._inputs.covariance = matrix
        if expected_returns is not None:
            self._inputs.expected_returns = [float(value) for value in expected_returns]

    def _request(self, **overrides: Any) -> Any:
        request = _portfolio.OptimizationRequest()
        for name, value in overrides.items():
            if value is not None:
                setattr(request, name, value)
        return request

    def minimum_variance(
        self, *, target_return: float | None = None, long_only: bool = True
    ) -> Any:
        return _portfolio.minimum_variance(
            self._inputs, self._request(long_only=long_only, target_return=target_return)
        )

    def maximum_sharpe(self, *, risk_free_rate: float = 0.0, long_only: bool = True) -> Any:
        return _portfolio.maximum_sharpe(
            self._inputs, self._request(risk_free_rate=risk_free_rate, long_only=long_only)
        )

    def efficient_frontier(
        self, target_returns: Sequence[float], *, risk_free_rate: float | None = None
    ) -> list:
        return list(
            _portfolio.efficient_frontier(
                self._inputs,
                [float(value) for value in target_returns],
                self._request(risk_free_rate=risk_free_rate),
            )
        )

    def risk_parity(self) -> Any:
        return _portfolio.risk_parity(self._inputs.covariance, self.assets)

    def minimise_cvar(
        self,
        scenario_returns: Sequence[float] | Sequence[Sequence[float]],
        *,
        confidence: float = 0.95,
    ) -> Any:
        """Needs the raw scenario matrix, not the fitted covariance: the LP is on scenarios."""
        scenarios = _flatten(scenario_returns)
        request = _portfolio.CvarRequest()
        request.assets = self.assets
        request.scenario_returns = scenarios
        request.scenarios = len(scenarios) // self.assets
        request.confidence = float(confidence)
        return _portfolio.minimise_cvar(request)


class RiskEngine:
    """One loss-convention-aware entry point to the Phase 5 measures.

    Constructed from a returns sample. The convention is the project's frozen one, `L =
    -R`, so `var()` on a sample of *returns* answers "how much could I lose", and passing
    already-negated losses through here inverts the sign silently. That is the one misuse
    this facade cannot detect, so it says it out loud in the repr.
    """

    __core__ = _risk

    def __init__(self, returns: Sequence[float]) -> None:
        self._returns = [float(value) for value in returns]
        if not self._returns:
            raise ValueError("RiskEngine needs at least one return observation")

    def __repr__(self) -> str:
        return f"RiskEngine(observations={len(self._returns)}, loss convention L = -R)"

    @property
    def observations(self) -> int:
        return len(self._returns)

    def historical_var(self, confidence: float = 0.95) -> Any:
        return _risk.historical_var(self._returns, float(confidence))

    def historical_es(self, confidence: float = 0.95) -> Any:
        return _risk.historical_es(self._returns, float(confidence))

    def gaussian_var(self, confidence: float = 0.95) -> Any:
        return _risk.gaussian_var(self._returns, float(confidence))

    def gaussian_es(self, confidence: float = 0.95) -> Any:
        return _risk.gaussian_es(self._returns, float(confidence))

    def monte_carlo_var(self, simulated_pnl: Sequence[float], confidence: float = 0.95) -> Any:
        return _risk.monte_carlo_var([float(value) for value in simulated_pnl], float(confidence))

    def bootstrap_ci(
        self,
        confidence: float = 0.95,
        *,
        interval_level: float = 0.9,
        block: bool = False,
        block_length: int = 0,
        seed: int = 42,
        replicates: int = 2000,
    ) -> Any:
        """A percentile interval for the VaR at `confidence`.

        `block_length=0` asks the core for its `round(n^(1/3))` default rather than
        having a Python-side guess baked into the facade.
        """
        kind = _risk.BootstrapKind.MOVING_BLOCK if block else _risk.BootstrapKind.IID
        return _risk.bootstrap_var(
            self._returns,
            float(confidence),
            int(replicates),
            float(interval_level),
            kind,
            int(block_length),
            int(seed),
        )

    def backtest(self, var_series: Sequence[float], confidence: float = 0.95) -> Any:
        return _risk.backtest_var(
            self._returns, [float(value) for value in var_series], float(confidence)
        )


class ScenarioEngine:
    """Runs scenarios against a fixed stress portfolio.

    The portfolio is validated on construction, which is when a misaligned exposure vector
    is cheapest to catch: by the time a scenario is running, a length mismatch has already
    been silently zero-filled by nothing at all — the core raises, but the message points
    at the scenario rather than at the book that was wrong.
    """

    __core__ = _stress

    def __init__(self, portfolio: Any) -> None:
        portfolio.aggregate()  # fail here, not inside a scenario loop
        self._portfolio = portfolio

    def run(
        self,
        scenario: Any,
        *,
        factor_move_covariance: Sequence[float] | None = None,
        confidence: float = 0.95,
    ) -> Any:
        covariance = (
            [float(value) for value in factor_move_covariance]
            if factor_move_covariance is not None
            else []
        )
        return _stress.run_scenario(self._portfolio, scenario, covariance, float(confidence))

    def historical(
        self,
        scenario: Any,
        observed_moves: Sequence[float],
        *,
        observations: int | None = None,
        confidence: float = 0.95,
    ) -> Any:
        flat = [float(value) for value in observed_moves]
        assets = int(self._portfolio.factors.size())
        count = int(observations) if observations is not None else len(flat) // assets
        return _stress.run_historical_scenarios(
            self._portfolio, scenario, flat, count, float(confidence)
        )

    def monte_carlo(
        self,
        scenario: Any,
        factor_move_covariance: Sequence[float],
        *,
        paths: int = 100_000,
        seed: int = 42,
        confidence: float = 0.95,
    ) -> Any:
        return _stress.run_monte_carlo_scenarios(
            self._portfolio,
            scenario,
            [float(value) for value in factor_move_covariance],
            int(paths),
            int(seed),
            float(confidence),
        )

    @staticmethod
    def sample_moves(
        factor_move_covariance: Sequence[float], *, assets: int, paths: int, seed: int = 42
    ) -> Any:
        return _stress.sample_factor_moves(
            [float(value) for value in factor_move_covariance], int(assets), int(paths), int(seed)
        )


def _flatten(values: Any) -> list[float]:
    """Accept either a flat row-major sequence or a sequence of rows."""
    if not len(values):
        return []
    first = values[0]
    if isinstance(first, (list, tuple)) or hasattr(first, "__len__"):
        return [float(item) for row in values for item in row]
    return [float(value) for value in values]


def _square_size(flat: Sequence[float]) -> int:
    side = int(round(len(flat) ** 0.5))
    if side * side != len(flat):
        raise ValueError(
            f"{len(flat)} entries do not form a square matrix; pass assets= explicitly "
            "if the covariance is not square, which would itself be a bug"
        )
    return side
