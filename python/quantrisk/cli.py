"""The `quantrisk` command line: three commands, no more.

PROJECT_SPEC.md §Phase 9 asks for `validate`, `benchmark` and `demo` and explicitly says
not to build a web app, because the project's value is not UI. What each one does:

  validate   run the identities the library claims, and exit non-zero if any fail
  benchmark  time a few core operations on this machine, right now
  demo       execute the documented API examples end to end

`validate` is the one worth having, and the reason it is not just "run pytest" is that
pytest needs the source tree while `validate` needs only an installed wheel. It re-checks
the claims the README makes — put-call parity, MC convergence, attribution closure — against
the library that is actually installed, so a broken install is detectable without a
checkout.

`benchmark` prints numbers measured during the run and nothing cached. It is explicitly not
a comparison against another library, because that comparison lives in `benchmarks/` with
committed artifacts, and a CLI that printed a competing figure next to them would create
two sources of truth for one claim.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from typing import Any

import quantrisk

_CSI = "\033["
_GREEN, _RED, _YELLOW, _RESET = f"{_CSI}32m", f"{_CSI}31m", f"{_CSI}33m", f"{_CSI}0m"


def _supports_colour() -> bool:
    return sys.stdout.isatty() and platform.system() != "Windows"


def _paint(text: str, colour: str) -> str:
    return f"{colour}{text}{_RESET}" if _supports_colour() else text


def _record(name: str, ok: bool, detail: str) -> dict[str, Any]:
    mark = _paint("PASS", _GREEN) if ok else _paint("FAIL", _RED)
    print(f"  {mark}  {name:38s} {detail}")
    return {"name": name, "passed": ok, "detail": detail}


# --- validate --------------------------------------------------------------


def command_validate(arguments: argparse.Namespace) -> int:
    """Check the identities the library claims, on the installed build."""
    print(f"quantrisk {quantrisk.version()} — validation on {platform.platform()}")
    build = quantrisk.build_metadata()
    print(f"  {build['compiler']}, {build['build_type']}, commit {build['git_commit']}")
    results: list[dict[str, Any]] = []

    # 1. Put-call parity: C - P == S e^-qT - K e^-rT, an identity, not a tolerance test.
    model = quantrisk.BlackScholes(
        spot=100.0, strike=100.0, rate=0.04, vol=0.20, maturity=1.0, dividend_yield=0.02
    )
    residual = model.put_call_parity_residual()
    results.append(_record("put-call parity", abs(residual) < 1e-12, f"residual {residual:.3e}"))

    # 2. Analytic Greeks against central differences — two independent code paths.
    #    The absolute gap is not the check: at a 1% spot bump the truncation error is
    #    ~6e-5 by construction, so any fixed tolerance near that is a tuned constant.
    #    What a correct second-order central difference must do is shrink its gap
    #    quadratically as the bump halves, so the check is that the ratio holds across
    #    two independent halvings. No magnitude is asserted, and no constant is tuned.
    greeks = model.greeks()
    gaps = [
        abs(greeks.delta - model.finite_difference_greeks(spot_relative=bump).delta)
        for bump in (0.01, 0.005, 0.0025)
    ]
    ratios = [earlier / later for earlier, later in zip(gaps, gaps[1:], strict=False)]
    results.append(
        _record(
            "finite-difference delta converges at O(h^2)",
            all(3.0 < ratio < 5.0 for ratio in ratios) and all(gap > 0 for gap in gaps),
            f"gaps {' -> '.join(f'{gap:.2e}' for gap in gaps)}, "
            f"ratios {' and '.join(f'{ratio:.2f}' for ratio in ratios)} (theory 4.00)",
        )
    )

    # 3. Monte Carlo convergence: quadrupling paths should halve the standard error.
    engine = quantrisk.MonteCarloEngine(seed=2024)
    coarse = engine.price_european_call(
        spot=100.0, strike=100.0, rate=0.04, vol=0.20, maturity=1.0, paths=20_000
    )
    fine = engine.price_european_call(
        spot=100.0, strike=100.0, rate=0.04, vol=0.20, maturity=1.0, paths=80_000
    )
    ratio = coarse.standard_error / fine.standard_error if fine.standard_error else float("nan")
    results.append(
        _record(
            "MC standard error scales as 1/sqrt(N)",
            1.7 < ratio < 2.3,
            f"ratio {ratio:.3f} (theory 2.0)",
        )
    )

    # 4. Reproducibility: the same seed must give the same number, bit for bit.
    again = quantrisk.MonteCarloEngine(seed=2024).price_european_call(
        spot=100.0, strike=100.0, rate=0.04, vol=0.20, maturity=1.0, paths=20_000
    )
    results.append(
        _record(
            "seeded Monte Carlo is reproducible",
            again.price == coarse.price and again.standard_error == coarse.standard_error,
            f"{coarse.price!r} == {again.price!r}",
        )
    )

    # 5. VaR ordering: ES >= VaR at the same level, by definition of a tail mean.
    rng = quantrisk.Rng(seed=7)
    sample = [rng.standard_normal() * 0.02 for _ in range(2000)]
    risk_engine = quantrisk.RiskEngine(sample)
    var = risk_engine.historical_var(0.95)
    es = risk_engine.historical_es(0.95)
    results.append(
        _record(
            "ES >= VaR at the same level",
            es.value >= var.value,
            f"{es.value:.6f} >= {var.value:.6f}",
        )
    )

    # 6. Optimiser certificate: the answer must satisfy its own constraints.
    covariance = [0.04, 0.012, 0.012, 0.09]
    optimizer = quantrisk.PortfolioOptimizer(covariance, [0.06, 0.09])
    solution = optimizer.minimum_variance()
    closed = (
        abs(solution.budget_residual) < 1e-12
        and abs(solution.weight_bound_violation) < 1e-12
        and solution.verified_optimal
    )
    results.append(
        _record(
            "min-variance constraints and certificate",
            closed,
            f"budget {solution.budget_residual:.2e}, bounds "
            f"{solution.weight_bound_violation:.2e}, certified "
            f"{solution.verified_optimal}",
        )
    )

    # 7. Stress attribution must sum to the total, both ways round.
    factors = quantrisk.stress.FactorSet()
    factors.factors = [
        quantrisk.stress.RiskFactor(
            "SPX", quantrisk.stress.FactorClass.equity_index, 4000.0, "points"
        )
    ]
    book = quantrisk.stress.Portfolio()
    book.factors = factors
    exposures = quantrisk.stress.ExposureVector()
    exposures.delta = [1.0e6]
    position = quantrisk.stress.Position()
    position.name = "equities"
    position.exposures = exposures
    book.positions = [position]
    scenario = quantrisk.stress.Scenario()
    scenario.name = "equity -20%"
    scenario.assumptions = "one-day 20% fall, no other factor moves"
    scenario.shocks = [quantrisk.stress.Shock("SPX", -0.20, 0.0)]
    stress = quantrisk.ScenarioEngine(book).run(scenario)
    results.append(
        _record(
            "stress attribution closes",
            abs(stress.factor_attribution_residual) < 1e-9
            and abs(stress.position_attribution_residual) < 1e-9,
            f"P&L {stress.pnl_change:.2f}, residuals "
            f"{stress.factor_attribution_residual:.1e}/{stress.position_attribution_residual:.1e}",
        )
    )

    failed = [item for item in results if not item["passed"]]
    print(
        f"\n{len(results) - len(failed)}/{len(results)} checks passed"
        + ("" if not failed else f" — {len(failed)} FAILED")
    )
    if arguments.json:
        payload = {
            "command": "validate",
            "version": quantrisk.version(),
            "platform": platform.platform(),
            "build": build,
            "checks": results,
        }
        print(json.dumps(payload, indent=2))
    return 1 if failed else 0


# --- benchmark -------------------------------------------------------------


def _timed(
    label: str, call: Any, iterations: int, rate_unit: str, *, scale: float = 1.0
) -> dict[str, Any]:
    """Time `call` and report throughput measured now, on this machine.

    `scale` converts calls into the unit worth quoting — one Monte Carlo call is 100k
    paths, one tree build is one tree. Without it every line would read "calls/s" and the
    numbers would be comparable to each other but not to anything else.
    """
    start = time.perf_counter()
    for _ in range(iterations):
        call()
    elapsed = time.perf_counter() - start
    per_call = elapsed / iterations
    rate = scale / per_call
    print(f"  {label:38s} {per_call * 1e6:10.2f} us/call   {rate:,.0f} {rate_unit}/s")
    return {
        "label": label,
        "iterations": iterations,
        "seconds": elapsed,
        "microseconds_per_call": per_call * 1e6,
        "rate": rate,
        "rate_unit": f"{rate_unit}/s",
    }


def command_benchmark(arguments: argparse.Namespace) -> int:
    print(f"quantrisk {quantrisk.version()} — measured timings on {platform.platform()}")
    print("  (single machine, no comparison against another library; see benchmarks/)")
    rows: list[dict[str, Any]] = []
    model = quantrisk.BlackScholes(spot=100.0, strike=100.0, rate=0.04, vol=0.20, maturity=1.0)
    rows.append(_timed("black_scholes price", model.call_price, arguments.iterations, "price"))
    rows.append(_timed("black_scholes greeks", model.greeks, arguments.iterations, "greeks"))
    rows.append(
        _timed(
            "crr binomial, 500 steps",
            lambda: model.binomial(steps=500),
            max(1, arguments.iterations // 10),
            "tree",
        )
    )
    paths = 100_000
    engine = quantrisk.MonteCarloEngine(seed=11)
    rows.append(
        _timed(
            f"monte carlo, {paths:,} paths",
            lambda: engine.price_european_call(
                spot=100.0, strike=100.0, rate=0.04, vol=0.20, maturity=1.0, paths=paths
            ),
            max(1, arguments.iterations // 200),
            "path",
            scale=paths,
        )
    )
    covariance = [0.04, 0.012, 0.012, 0.09]
    optimizer = quantrisk.PortfolioOptimizer(covariance, [0.06, 0.09])
    rows.append(
        _timed(
            "min-variance solve (2 assets)",
            optimizer.minimum_variance,
            arguments.iterations,
            "solve",
        )
    )
    wide = quantrisk.PortfolioOptimizer(_scaled_identity(40), None)
    rows.append(
        _timed(
            "min-variance solve (40 assets)",
            wide.minimum_variance,
            max(1, arguments.iterations // 20),
            "solve",
        )
    )
    if arguments.json:
        print(json.dumps({"command": "benchmark", "rows": rows}, indent=2))
    return 0


def _scaled_identity(assets: int) -> list[float]:
    flat: list[float] = []
    for i in range(assets):
        for j in range(assets):
            flat.append(0.04 if i == j else 0.004)
    return flat


# --- demo ------------------------------------------------------------------


def command_demo(_arguments: argparse.Namespace) -> int:
    """Run the README's examples verbatim, so the docs cannot silently drift."""
    print(f"quantrisk {quantrisk.version()} — the documented examples, run live\n")

    print("Black-Scholes")
    model = quantrisk.BlackScholes(spot=100, strike=100, rate=0.04, vol=0.20, maturity=1.0)
    print(f"  {model!r}")
    print(f"  call_price()      {model.call_price():.6f}")
    print(f"  put_price()       {model.put_price():.6f}")
    greeks = model.greeks()
    print(
        f"  greeks()          delta={greeks.delta:.6f} gamma={greeks.gamma:.6f} "
        f"vega={greeks.vega:.6f}"
    )
    print(f"  parity residual   {model.put_call_parity_residual():.3e}\n")

    print("Monte Carlo")
    engine = quantrisk.MonteCarloEngine(seed=42)
    plain = engine.price_european_call(
        spot=100, strike=100, rate=0.04, vol=0.20, maturity=1.0, paths=200_000
    )
    antithetic = engine.price_european_call(
        spot=100,
        strike=100,
        rate=0.04,
        vol=0.20,
        maturity=1.0,
        paths=200_000,
        variance_reduction=quantrisk.monte_carlo.VarianceReduction.ANTITHETIC,
    )
    analytic = model.call_price()
    print(
        f"  plain             {plain.price:.6f}  se {plain.standard_error:.6f}  "
        f"(analytic {analytic:.6f})"
    )
    print(
        f"  antithetic        {antithetic.price:.6f}  se {antithetic.standard_error:.6f}  "
        f"error reduction {plain.standard_error / antithetic.standard_error:.2f}x"
    )
    print(f"  seed reproducible {engine.seed == 42}\n")

    print("Portfolio")
    optimizer = quantrisk.PortfolioOptimizer([0.04, 0.012, 0.012, 0.09], [0.06, 0.09])
    minimum = optimizer.minimum_variance()
    sharpe = optimizer.maximum_sharpe(risk_free_rate=0.01)
    parity = optimizer.risk_parity()
    print(f"  min variance      w={_vector(minimum.weights)} vol={minimum.volatility:.6f}")
    print(f"  max sharpe        w={_vector(sharpe.weights)} sharpe={sharpe.sharpe_ratio:.4f}")
    print(
        f"  risk parity       w={_vector(parity.weights)} "
        f"contribution gap={parity.max_contribution_gap:.2e}"
    )
    print(f"  certified         {minimum.verified_optimal}\n")

    print("Risk")
    rng = quantrisk.Rng(seed=5)
    sample = [rng.standard_normal() * 0.02 for _ in range(1000)]
    risk_engine = quantrisk.RiskEngine(sample)
    print(f"  {risk_engine!r}")
    print(f"  historical VaR95  {risk_engine.historical_var(0.95).value:.6f}")
    print(f"  historical ES95   {risk_engine.historical_es(0.95).value:.6f}")
    interval = risk_engine.bootstrap_ci(0.95, interval_level=0.9, replicates=400, seed=3)
    print(
        f"  bootstrap CI90    [{interval.ci_low:.6f}, {interval.ci_high:.6f}] "
        f"point {interval.point:.6f} (VaR 95%)\n"
    )

    print("Stress")
    factors = quantrisk.stress.FactorSet()
    factors.factors = [
        quantrisk.stress.RiskFactor(
            "SPX", quantrisk.stress.FactorClass.equity_index, 4000.0, "points"
        ),
        quantrisk.stress.RiskFactor("UST10Y", quantrisk.stress.FactorClass.rate, 0.04, "decimal"),
    ]
    book = quantrisk.stress.Portfolio()
    book.factors = factors
    equities = quantrisk.stress.Position()
    equities.name = "equities"
    equity_exposures = quantrisk.stress.ExposureVector()
    equity_exposures.delta = [1.0e6, 0.0]
    equities.exposures = equity_exposures
    bonds = quantrisk.stress.Position()
    bonds.name = "bonds"
    bond_exposures = quantrisk.stress.ExposureVector()
    bond_exposures.duration = [0.0, -2.0e7]
    bonds.exposures = bond_exposures
    book.positions = [equities, bonds]

    scenario = quantrisk.stress.Scenario()
    scenario.name = "risk-off"
    scenario.assumptions = "equities -20%, rates -50bp, one day, no vol response"
    scenario.shocks = [
        quantrisk.stress.Shock("SPX", -0.20, 0.0),
        quantrisk.stress.Shock("UST10Y", 0.0, -0.005),
    ]
    result = quantrisk.ScenarioEngine(book).run(scenario)
    print(f"  {result.scenario_name}: {result.assumptions}")
    print(f"  P&L               {result.pnl_change:,.2f}")
    for part in result.by_position:
        print(f"    {part.name:12s}      {part.pnl:,.2f}")
    print(f"  attribution residual {result.position_attribution_residual:.1e}")
    return 0


def _vector(values: list[float]) -> str:
    return "[" + ", ".join(f"{value:.4f}" for value in values) + "]"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quantrisk",
        description="Validation, benchmarks and a demo for the QuantRisk++ engine.",
    )
    parser.add_argument("--version", action="version", version=f"quantrisk {quantrisk.version()}")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="check the library's own identities")
    validate.add_argument("--json", action="store_true", help="also emit the results as JSON")
    validate.set_defaults(handler=command_validate)

    benchmark = sub.add_parser("benchmark", help="time core operations on this machine")
    benchmark.add_argument("--iterations", type=int, default=20_000)
    benchmark.add_argument("--json", action="store_true")
    benchmark.set_defaults(handler=command_benchmark)

    demo = sub.add_parser("demo", help="run the documented examples")
    demo.set_defaults(handler=command_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        return int(arguments.handler(arguments))
    except quantrisk.ValidationError as error:
        print(_paint(f"input rejected: {error}", _RED), file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
