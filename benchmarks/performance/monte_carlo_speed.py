#!/usr/bin/env python3
"""Phase 3 performance benchmark: C++ core vs Python baselines, measured.

    uv run python benchmarks/performance/monte_carlo_speed.py [--paths 200000]

Every speedup number in the README must come from this script's output on the
machine quoted next to it (PROJECT_SPEC.md §4, docs/validation_protocol.md §4).
Three implementations price the identical European call from the identical
number of normals per path:

* ``cpp``     - quantrisk.monte_carlo (C++20, -O3, mt19937_64 + Marsaglia polar)
* ``python``  - a literal pure-Python loop (``random.Random.gauss``), the honest
                baseline a reviewer would write first
* ``numpy``   - vectorised NumPy with PCG64, included because "C++ beats a loop"
                is only interesting relative to the fast Python option too

Nothing is extrapolated: repetitions are timed individually, and mean, standard
deviation and minimum are all reported.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import random
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import quantrisk
from quantrisk.experiments.metadata import environment, utc_timestamp

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "benchmarks" / "performance" / "results"

MATURITY = 1.0
SPOT = 100.0
STRIKE = 100.0
RATE = 0.05
DIVIDEND = 0.02
VOLATILITY = 0.25
DEFAULT_PATHS = 200_000
REPETITIONS = 7
WARMUP = 2


def cpp_price(paths: int, seed: int) -> tuple[float, float]:
    market = quantrisk.pricing.MarketParams(
        spot=SPOT, rate=RATE, dividend_yield=DIVIDEND, volatility=VOLATILITY, maturity=MATURITY
    )
    option = quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, STRIKE)
    result = quantrisk.monte_carlo.MonteCarloEngine(seed).price_european(option, market, paths)
    return float(result.price), float(result.standard_error)


def pure_python_price(paths: int, seed: int) -> tuple[float, float]:
    """The same estimator, written the way a Python-only implementation would be."""
    rng = random.Random(seed)
    drift = (RATE - DIVIDEND - 0.5 * VOLATILITY * VOLATILITY) * MATURITY
    scale = VOLATILITY * math.sqrt(MATURITY)
    discount = math.exp(-RATE * MATURITY)
    exp = math.exp
    gauss = rng.gauss
    strike = STRIKE
    total = 0.0
    total_squares = 0.0
    for _ in range(paths):
        terminal = SPOT * exp(drift + scale * gauss(0.0, 1.0))
        difference = terminal - strike
        payoff = difference if difference > 0.0 else 0.0
        total += payoff
        total_squares += payoff * payoff
    mean = total / paths
    variance = max(total_squares / paths - mean * mean, 0.0) * paths / max(paths - 1, 1)
    return discount * mean, discount * math.sqrt(variance / paths)


def numpy_price(paths: int, seed: int) -> tuple[float, float]:
    drift = (RATE - DIVIDEND - 0.5 * VOLATILITY * VOLATILITY) * MATURITY
    scale = VOLATILITY * math.sqrt(MATURITY)
    generator = np.random.default_rng(seed)
    chunks: list[np.ndarray] = []
    remaining = paths
    block = 1_000_000
    while remaining > 0:
        size = min(block, remaining)
        terminals = SPOT * np.exp(drift + scale * generator.standard_normal(size))
        chunks.append(np.maximum(terminals - STRIKE, 0.0))
        remaining -= size
    payoffs = np.concatenate(chunks)
    discount = math.exp(-RATE * MATURITY)
    return (
        float(discount * payoffs.mean()),
        float(discount * payoffs.std(ddof=1) / math.sqrt(payoffs.size)),
    )


def timed(function, paths: int, seed: int) -> tuple[float, tuple[float, float]]:
    started = time.perf_counter()
    estimate = function(paths, seed)
    return time.perf_counter() - started, estimate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", type=int, default=DEFAULT_PATHS)
    parser.add_argument("--repetitions", type=int, default=REPETITIONS)
    arguments = parser.parse_args()

    implementations = {
        "cpp": cpp_price,
        "python": pure_python_price,
        "numpy": numpy_price,
    }

    results: dict[str, dict[str, float]] = {}
    prices: dict[str, float] = {}
    standard_errors: dict[str, float] = {}
    for label, function in implementations.items():
        for _ in range(WARMUP):
            function(10_000, 1)
        samples: list[float] = []
        price, standard_error = float("nan"), float("nan")
        for repetition in range(arguments.repetitions):
            elapsed, (price, standard_error) = timed(function, arguments.paths, 42 + repetition)
            samples.append(elapsed)
        standard_errors[label] = standard_error
        results[label] = {
            "mean_seconds": statistics.fmean(samples),
            "std_seconds": statistics.stdev(samples) if len(samples) > 1 else 0.0,
            "min_seconds": min(samples),
            "max_seconds": max(samples),
            "paths_per_second_mean": arguments.paths / statistics.fmean(samples),
            "repetitions": len(samples),
        }
        prices[label] = price

    cpp_mean = results["cpp"]["mean_seconds"]
    analytic = quantrisk.pricing.black_scholes(
        quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, STRIKE),
        quantrisk.pricing.MarketParams(
            spot=SPOT, rate=RATE, dividend_yield=DIVIDEND, volatility=VOLATILITY, maturity=MATURITY
        ),
    ).price

    payload = {
        "artifact": "benchmarks/performance/monte_carlo_speed.py",
        "command": f"uv run python {' '.join(Path(sys.argv[0]).parts[-2:])}",
        "paths_per_run": arguments.paths,
        "option": {
            "type": "european_call",
            "spot": SPOT,
            "strike": STRIKE,
            "rate": RATE,
            "dividend_yield": DIVIDEND,
            "volatility": VOLATILITY,
            "maturity": MATURITY,
        },
        "analytic_reference_price": analytic,
        "generated_at_utc": utc_timestamp(),
        "host_environment": environment(),
        "measured_prices": prices,
        "reported_standard_errors": standard_errors,
        "z_score_vs_analytic": {
            key: (value - analytic) / standard_errors[key]
            for key, value in prices.items()
            if standard_errors.get(key)
        },
        "results_seconds": results,
        "speedup_vs_pure_python": results["python"]["mean_seconds"] / cpp_mean,
        "speedup_vs_pure_python_using_min": results["python"]["min_seconds"]
        / results["cpp"]["min_seconds"],
        "speedup_vs_numpy": results["numpy"]["mean_seconds"] / cpp_mean,
        "environment": {
            "quantrisk": quantrisk.build_metadata(),
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "caveats": [
            "Pure-Python baseline uses random.Random(seed).gauss (Mersenne Twister 32-bit "
            "plus pair caching), so its stream differs from the C++ engine; the comparison "
            "is about cost per path, not bit equality of prices.",
            "Single-threaded on both sides: no OpenMP/TBB in the C++ core, no multiprocessing "
            "in the baseline. A multi-core claim would need a different measurement.",
            "Scope of the measured claim: this is a terminal-only draw (one normal per "
            "path). NumPy's vectorised generator wins that regime, so 'C++ is faster than "
            "Python' is NOT claimed here; the C++ core's advantage is per-path state "
            "(running maxima, running averages) in path-dependent pricing, which is "
            "measured separately in Phase 4, and holding O(paths) memory instead of "
            "O(paths x steps).",
            "Time.perf_counter wall clock, one process at a time; other load on the machine "
            "would inflate every column equally.",
        ],
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = RESULTS / "monte_carlo_speed.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "results_seconds": payload["results_seconds"],
                "speedup_vs_pure_python": payload["speedup_vs_pure_python"],
                "speedup_vs_numpy": payload["speedup_vs_numpy"],
                "measured_prices": payload["measured_prices"],
                "analytic_reference_price": analytic,
            },
            indent=2,
            sort_keys=True,
        )
    )
    print(f"wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
