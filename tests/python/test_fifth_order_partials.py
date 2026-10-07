"""The six mixed fifth partials, checked the way the core checks its other closed forms.

Nothing here reads the C++ source. Every assertion is either an exact relation the model has to
satisfy -- call/put parity, the degenerate limit, the multinomial contraction -- or a finite
difference of a partial `quantrisk` published *before* this phase, so a slip in a fifth-order
numerator cannot be hidden by the same slip appearing on both sides of a comparison.

The step sizes are the argument, not the numbers. A fifth derivative here is a slope of a fourth
one, so the band a route earns is set by the parent's own curvature over the step: the routes below
take the best of relative steps from 0.2 % to 1 %, the same discipline
`tests/cpp/test_black_scholes.cpp` applies at `1e-5 * S` and `1e-4 * sigma` where the parent
partials are smooth enough to carry it. Measured at the finest rung the ten routes top out at
`1.5e-4` relative (`V_Ssigmasigmasigmasigma` along the spot axis) against the `1e-3` asserted here,
while the volatility-axis routes sit near `1e-9`; the band is sized for the spot routes, whose error
is truncation of the parent rather than round-off and grows with the step (the same routes reach
`1.2e-3` to `9.2e-2` at a 1 % step, which is why the ladder is searched rather than fixed at one
rung, and why the coarse rungs are reported in limitation #82 rather than asserted here).
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import quantrisk

REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVATION = REPO_ROOT / "scripts" / "derive_fifth_order_partials.py"

PRICING = quantrisk.pricing
STEPS = (0.002, 0.005, 0.01)
WEIGHTS = (1.0 / 12.0, -2.0 / 3.0, 0.0, 2.0 / 3.0, -1.0 / 12.0)
OFFSETS = (-2.0, -1.0, 0.0, 1.0, 2.0)

MARKETS: list[dict[str, float]] = [
    {"spot": 100.0, "rate": 0.03, "dividend_yield": 0.0, "volatility": 0.20, "maturity": 0.5},
    {"spot": 150.0, "rate": 0.05, "dividend_yield": 0.01, "volatility": 0.35, "maturity": 2.0},
    {"spot": 95.0, "rate": 0.03, "dividend_yield": 0.0, "volatility": 0.15, "maturity": 0.1},
    {"spot": 100.0, "rate": 0.02, "dividend_yield": 0.02, "volatility": 0.45, "maturity": 0.5},
    {"spot": 100.0, "rate": 0.03, "dividend_yield": 0.0, "volatility": 0.30, "maturity": 0.05},
]

FIELDS = (
    "spot_spot_spot_spot_spot",
    "spot_spot_spot_spot_sigma",
    "spot_spot_spot_sigma_sigma",
    "spot_spot_sigma_sigma_sigma",
    "spot_sigma_sigma_sigma_sigma",
    "sigma_sigma_sigma_sigma_sigma",
)
COEFFICIENTS = (1.0, 5.0, 10.0, 10.0, 5.0, 1.0)


def _market(parameters: dict[str, float], **overrides: float) -> Any:
    return PRICING.MarketParams(**{**parameters, **overrides})


def _option(strike: float = 100.0, put: bool = False) -> Any:
    style = PRICING.OptionType.PUT if put else PRICING.OptionType.CALL
    return PRICING.EuropeanOption(style, strike)


def _fifth(parameters: dict[str, float], put: bool = False) -> Any:
    return PRICING.black_scholes_mixed_fifth_derivatives(_option(put=put), _market(parameters))


def _price(parameters: dict[str, float]) -> float:
    return float(PRICING.black_scholes(_option(), _market(parameters)).price)


def _spot_fourth(parameters: dict[str, float]) -> float:
    return float(PRICING.black_scholes_spot_derivatives(_option(), _market(parameters)).fourth)


def _mixed_fourth(field: str) -> Callable[[dict[str, float]], float]:
    def read(parameters: dict[str, float]) -> float:
        return float(
            getattr(
                PRICING.black_scholes_mixed_fourth_derivatives(_option(), _market(parameters)),
                field,
            )
        )

    return read


PARENTS: tuple[list[tuple[Callable[[dict[str, float]], float], str]], ...] = (
    [(_spot_fourth, "spot")],
    [(_spot_fourth, "volatility"), (_mixed_fourth("spot_spot_spot_sigma"), "spot")],
    [
        (_mixed_fourth("spot_spot_spot_sigma"), "volatility"),
        (_mixed_fourth("spot_spot_sigma_sigma"), "spot"),
    ],
    [
        (_mixed_fourth("spot_spot_sigma_sigma"), "volatility"),
        (_mixed_fourth("spot_sigma_sigma_sigma"), "spot"),
    ],
    [
        (_mixed_fourth("spot_sigma_sigma_sigma"), "volatility"),
        (_mixed_fourth("sigma_sigma_sigma_sigma"), "spot"),
    ],
    [(_mixed_fourth("sigma_sigma_sigma_sigma"), "volatility")],
)


def _slope(
    read: Callable[[dict[str, float]], float], parameters: dict[str, float], axis: str, step: float
) -> float:
    """Five-point central slope of a published partial along one axis, at a relative step."""
    base = parameters[axis]
    total = 0.0
    for offset, weight in zip(OFFSETS, WEIGHTS, strict=True):
        total += weight * read({**parameters, axis: base + offset * base * step})
    return total / (base * step)


def _best_route_error(read, axis, parameters, exact) -> float:
    return min(abs(_slope(read, parameters, axis, step) - exact) for step in STEPS) / max(
        abs(exact), 1.0e-30
    )


def test_every_fifth_partial_is_a_slope_of_a_partial_the_core_already_shipped() -> None:
    """Two independent routes where both axes have a parent, one at each pure end."""
    for field, routes in zip(FIELDS, PARENTS, strict=True):
        worst = 0.0
        for parameters in MARKETS:
            exact = float(getattr(_fifth(parameters), field))
            for read, axis in routes:
                worst = max(worst, _best_route_error(read, axis, parameters, exact))
        assert worst < 1.0e-3, f"{field}: worst route residual {worst:.2e} over five markets"


def test_the_fifth_partials_are_identical_for_a_call_and_a_put() -> None:
    """`C - P = S e^{-qT} - K e^{-rT}` is linear in the spot and flat in the volatility."""
    for parameters in MARKETS:
        call = _fifth(parameters)
        put = _fifth(parameters, put=True)
        for field in FIELDS:
            assert getattr(call, field) == getattr(put, field), (parameters, field)


def test_the_quintic_contraction_is_the_fifth_directional_derivative_of_the_price() -> None:
    """A route that never touches the mixed structs: five nested differences of the price.

    Along the joint shock `(h, k)` the fifth directional derivative of `V` is the contraction
    `V_SSSSS h^5 + 5 V_SSSSsigma h^4 k + 10 V_SSSsigmasigma h^3 k^2 + 10 V_SSsigmasigma h^2 k^3
     + 5 V_Ssigmasigmasigma h k^4 + V_sigmasigmasigmasigma k^5`, and the left side here is the same
    derivative taken by nesting the five-point slope below along the ray in price space. What is
    differentiated is `black_scholes`, validated against QuantLib in Phase 2, so the six numerators
    and the multinomial coefficients are pinned by something sharing no code with them.

    Five nested five-point slopes divide by the scale five times, so this route is round-off
    dominated long before it is truncation dominated: measured at the three rungs tried, the errors
    fall monotonically as the scale grows (0.002 to 0.008 gives 6.7, 8.1e-2 and 4.8e-3 relative on
    the `(0.05, 0.02)` ray), and the `5e-2` band is met by the widest rung alone. That is disclosed
    in limitation #82 rather than papered over by the minimum.
    """

    def along(scale: float, h: float, k: float, parameters: dict[str, float]) -> float:
        def point(t: float) -> float:
            return _price(
                {
                    **parameters,
                    "spot": parameters["spot"] + t * h,
                    "volatility": parameters["volatility"] + t * k,
                }
            )

        value = point
        for _ in range(5):
            previous = value

            def value(t: float, previous=previous) -> float:
                return (
                    sum(
                        weight * previous(t + offset * scale)
                        for weight, offset in zip(WEIGHTS, OFFSETS, strict=True)
                    )
                    / scale
                )

        return value(0.0)

    parameters = MARKETS[0]
    fifth = _fifth(parameters)
    for h, k in ((0.05, 0.02), (0.12, -0.05), (-0.03, 0.08)):
        spot_move = h * parameters["spot"]
        closed = sum(
            coefficient * float(getattr(fifth, field)) * spot_move ** (5 - power) * k**power
            for coefficient, power, field in zip(COEFFICIENTS, range(6), FIELDS, strict=True)
        )
        error = min(
            abs(along(scale, spot_move, k, parameters) - closed) / max(abs(closed), 1.0e-30)
            for scale in (0.002, 0.004, 0.008)
        )
        assert error < 5.0e-2, (
            f"contraction at ({h}, {k}): {error:.2e} against the price difference"
        )


def test_the_degenerate_market_reports_the_limit_rather_than_an_overflow() -> None:
    """`v^4` sits under every field, so `sigma = 0` and `T = 0` are limits, not divisions."""
    for overrides in ({"volatility": 0.0}, {"maturity": 0.0}):
        result = _fifth({**MARKETS[0], **overrides})
        for field in FIELDS:
            assert float(getattr(result, field)) == 0.0, (overrides, field)


def test_an_invalid_instrument_is_refused_before_any_polynomial_is_evaluated() -> None:
    with pytest.raises(quantrisk.ValidationError):
        PRICING.black_scholes_mixed_fifth_derivatives(_option(strike=-1.0), _market(MARKETS[0]))


def test_the_derivation_command_agrees_at_the_precision_floor() -> None:
    """The identity behind the `8.7e-58` claim was a command nobody's gate ran.

    `scripts/derive_fifth_order_partials.py` is what makes "the numerators are derived, not typed"
    a check rather than a sentence: it re-differentiates the price at 60 digits, divides by the
    prefactor the header claims, and meets the result against the polynomial parsed out of
    `cpp/src/pricing/black_scholes.cpp`. Until this phase the only way to exercise it was a human
    typing `uv run --with sympy ...`, so `docs/validation_matrix.md` row 21 and the technical
    report's §Stress Testing could quote its worst residual with nothing able to disagree. `sympy`
    is now a dev-group dependency -- the group `uv sync` installs -- so every lane that sets up the
    development environment runs the identity.

    Part A is asserted against the script's own `1e-40` floor over the six fields. Part B is
    float64 against 60-digit mpmath, so it is banded with the `1e-12` cross-platform slack
    `docs/limitations.md` #63 documents rather than compared digit for digit: finding 54(a) is what
    happens when a last-bit `libm` difference is asserted as equality.
    """
    pytest.importorskip("sympy", reason="the derivation is symbolic and needs sympy")
    completed = subprocess.run(
        [sys.executable, str(DERIVATION)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout[-600:] + completed.stderr[-600:]

    part_a = re.findall(
        r"worst relative disagreement ([0-9.e+-]+) \(values up to", completed.stdout
    )
    assert len(part_a) == 6, f"expected six field lines, read {part_a}"
    worst_a = max(float(value) for value in part_a)
    assert worst_a <= 1.0e-40, (
        f"the parsed numerator diverges from the exact derivative at {worst_a}"
    )

    part_b = re.search(r"worst relative disagreement over the grid: ([0-9.e+-]+)", completed.stdout)
    assert part_b, "part B printed no grid summary line"
    assert float(part_b.group(1)) <= 1.0e-12, (
        f"the extension disagrees with 60-digit nested differentiation at {part_b.group(1)}"
    )

    quoted = _quoted_identity_floor(completed.stdout)
    assert _exponent(quoted) == _exponent(worst_a), (
        f"the documents quote the identity's worst residual as {quoted} while the run reports "
        f"{worst_a}. The mantissa is deliberately not asserted: the last digits of a 60-digit "
        f"residual are not a cross-platform fact. An order of magnitude is, and a numerator that "
        f"stopped matching the exact derivative would move by many more than one"
    )


def _quoted_identity_floor(stdout: str) -> float:
    """The figures the matrix and the report quote, each matched to the thing it counts.

    The matrix row and the report state the same identity's worst residual, a market count, and a
    working precision, and this helper used to compare three groups at once -- the matrix's *market*
    count against the report's *digit* count, because both read 60. That is a guard certifying the
    transcription of two different quantities: it would have stayed green while the report claimed
    the identity was met at a grid the script never evaluated. Each figure is now read against the
    run's own printout, which is the producer of both.
    """
    matrix = (REPO_ROOT / "docs" / "validation_matrix.md").read_text(encoding="utf-8")
    tex = (REPO_ROOT / "paper" / "technical_report.tex").read_text(encoding="utf-8")
    row = [line for line in matrix.splitlines() if line.startswith("| 21 |")]
    assert row, "validation matrix row 21 is gone"
    in_matrix = re.search(r"\(([0-9.]+)e-(\d+) worst relative over (\d+) markets", row[0])
    in_tex = re.search(
        r"\$([0-9.]+) \\times 10\^\{-(\d+)\}\$ relative worst at (\d+) working digits", tex
    )
    tex_markets = re.search(r"meets it at (\d+)\s+markets", tex)
    run_markets = re.search(r"(\d+) markets, realised d1", stdout)
    run_digits = re.search(r"part B: (\d+)-digit nested numerical", stdout)
    assert in_matrix and in_tex and tex_markets and run_markets and run_digits, (
        "one of the three statements of the identity's grid or precision is gone: "
        f"matrix={bool(in_matrix)} report={bool(in_tex)} report_markets={bool(tex_markets)} "
        f"run_markets={bool(run_markets)} run_digits={bool(run_digits)}"
    )
    assert in_matrix.group(3) == run_markets.group(1) == tex_markets.group(1), (
        f"the identity is met at {run_markets.group(1)} markets in the run, while the matrix "
        f"quotes {in_matrix.group(3)} and the report quotes {tex_markets.group(1)}"
    )
    assert in_tex.group(3) == run_digits.group(1), (
        f"the report says {in_tex.group(3)} working digits; the run differentiated at "
        f"{run_digits.group(1)}"
    )
    assert (in_matrix.group(1), in_matrix.group(2)) == (in_tex.group(1), in_tex.group(2)), (
        f"the matrix quotes {in_matrix.groups()[:2]} and the report quotes {in_tex.groups()[:2]}"
    )
    return float(f"{in_matrix.group(1)}e-{in_matrix.group(2)}")


def _exponent(value: float) -> int:
    """The base-10 exponent of a positive float, from its own scientific rendering."""
    assert value > 0.0, value
    return int(f"{value:.0e}".split("e")[1])
