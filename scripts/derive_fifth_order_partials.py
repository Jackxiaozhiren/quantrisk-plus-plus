"""Re-derive the six mixed fifth partials from the price function and check the shipped source.

This is the derivation behind `docs/phase_reports/phase-20-fifth-order-partials.md` §2. It exists so
the claim "the closed forms were derived rather than typed" is a command, not a sentence:

* part A differentiates `black_scholes` symbolically, forms the quotient
  `R = V_(a,b) * v^4 * S^(a-1) / (e^{-qT} phi(d1) T^(b/2))` at 60 markets spread over the `(d1, v)`
  plane, and compares it with the monomial sum the C++ file *actually contains*, parsed out of
  `cpp/src/pricing/black_scholes.cpp`. Two polynomials of total degree at most five agreeing at 60
  points in general position are the same polynomial, so agreement is identity, not a fit;
* part B computes each field by nested numerical differentiation at 60 digits and compares it with
  the extension's float64 answer, which is the part that checks the prefactor, the powers and the
  degenerate handling rather than only the numerator.

Neither part takes a closed form as an input. Exits non-zero if any check fails.

    uv run --with sympy python scripts/derive_fifth_order_partials.py

`sympy` is not a project dependency and is not added by this command; it is fetched into an
ephemeral overlay by `--with`, so the environment the release ships is unchanged.
"""

from __future__ import annotations

import argparse
import pathlib
import re

import mpmath as mp
import sympy as sp

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "cpp" / "src" / "pricing" / "black_scholes.cpp"

S, K, r, q, sig, T = sp.symbols("S K r q sigma T", positive=True)
# Deliberately assumption-free: `sp.sympify` resolves a bare `w` to `Symbol("w")` with no
# assumptions, and sympy treats a symbol with `real=True` as a different object. Assumed here, the
# parsed source expression would carry a third symbol and `is_polynomial(W, V)` below would pass
# vacuously -- a guard that cannot fail, which is what makes this line worth a comment.
W, V = sp.symbols("w v")


def normal_cdf(z):
    return sp.Rational(1, 2) * (1 + sp.erf(z / sp.sqrt(2)))


D1 = (sp.log(S / K) + (r - q + sig**2 / 2) * T) / (sig * sp.sqrt(T))
D2 = D1 - sig * sp.sqrt(T)
PRICE = S * sp.exp(-q * T) * normal_cdf(D1) - K * sp.exp(-r * T) * normal_cdf(D2)

FIELDS = ("q50", "q41", "q32", "q23", "q14", "q05")
PY_FIELDS = (
    "spot_spot_spot_spot_spot",
    "spot_spot_spot_spot_sigma",
    "spot_spot_spot_sigma_sigma",
    "spot_spot_sigma_sigma_sigma",
    "spot_sigma_sigma_sigma_sigma",
    "sigma_sigma_sigma_sigma_sigma",
)


def shipped_numerators():
    """The monomial sums as sympy expressions, read out of the C++ source text."""
    text = SOURCE.read_text(encoding="utf-8")
    expressions = {}
    for field in FIELDS:
        match = re.search(rf"const Real {field} =(.*?);\n", text, flags=re.S)
        assert match, f"{field} is not an explicit monomial sum in {SOURCE}"
        body = re.sub(r"\s+", " ", match.group(1)).strip()
        for pattern, replacement in (
            ("v * v * v * v", "v**4"),
            ("v * v * v", "v**3"),
            ("v * v", "v**2"),
            ("first", "w"),
        ):
            body = body.replace(pattern, replacement)
        expression = sp.expand(sp.sympify(body))
        # Both halves are needed. `is_polynomial(W, V)` alone passes on a stray symbol, because a
        # symbol it was not given simply becomes a coefficient.
        assert expression.free_symbols <= {W, V}, f"{field}: carries a symbol beyond (d1, v)"
        assert expression.is_polynomial(W, V), f"{field}: not a polynomial in (d1, v)"
        poly = sp.Poly(expression, W, V)
        assert poly.degree(W) <= 8, f"{field}: above degree eight in d1"
        assert poly.degree(V) <= 4, f"{field}: above degree four in v"
        expressions[field] = expression
    return expressions


def grid():
    """60 markets spread over the `(d1, v)` plane, with `K`, `r`, `q` and `T` varied as well.

    The spot realises the target `d1` exactly through `S = K exp(d1 v - (r - q) T - v^2 / 2)`, and
    the row reports the `d1` that comes back out of the market, so the comparison is against the
    realised value rather than the intended one.
    """
    rows = []
    for index, v_target in enumerate(("0.10", "0.35", "0.70", "1.20")):
        for index2, d1_target in enumerate((-3, -1.5, 0, 1.5, 3)):
            for index3, maturity in enumerate(("0.25", "1.0", "0.5")):
                key = (index * 12 + index2 * 4 + index3) % 4
                v_value = mp.mpf(v_target)
                mat = mp.mpf(maturity)
                rate = mp.mpf(("0.01", "0.03", "0.06", "0.08")[key])
                dividend = mp.mpf(("0.0", "0.02", "0.05", "0.01")[key])
                strike = mp.mpf((80, 100, 120, 150)[key])
                vol = v_value / mp.sqrt(mat)
                spot = strike * mp.exp(
                    mp.mpf(d1_target) * v_value - (rate - dividend) * mat - v_value**2 / 2
                )
                realised = (mp.log(spot / strike) + (rate - dividend + vol**2 / 2) * mat) / (
                    vol * mp.sqrt(mat)
                )
                rows.append((spot, strike, rate, dividend, vol, mat, realised, v_value))
    return rows


def price_callable(strike, rate, dividend, maturity):
    """The Merton price as an mpmath function of `(spot, sigma)`, for numerical differentiation."""

    def value(spot_value, sigma_value):
        root_2t = sigma_value * mp.sqrt(2 * maturity)  # d1 / sqrt(2) below, to match erf
        carry = (rate - dividend) * maturity
        first = (mp.log(spot_value / strike) + carry + sigma_value**2 * maturity / 2) / root_2t
        second = first - sigma_value * mp.sqrt(maturity / 2)
        return spot_value * mp.exp(-dividend * maturity) * 0.5 * (
            1 + mp.erf(first)
        ) - strike * mp.exp(-rate * maturity) * 0.5 * (1 + mp.erf(second))

    return value


def part_a():
    print("part A: the shipped numerator vs the quotient of the exact derivative")
    shipped = shipped_numerators()
    rows = grid()
    print(
        f"  {len(rows)} markets, realised d1 from {mp.nstr(rows[0][6], 6)} "
        f"to {mp.nstr(rows[-1][6], 6)}, v from 0.10 to 1.20"
    )
    failures = []
    for index, field in enumerate(FIELDS):
        n_spot, n_vol = 5 - index, index
        exact = sp.diff(PRICE, S, n_spot, sig, n_vol)
        evaluate = sp.lambdify((S, K, r, q, sig, T), exact, modules="mpmath")
        polynomial = sp.lambdify((W, V), shipped[field], modules="mpmath")
        worst = mp.mpf(0)
        largest = mp.mpf(0)
        for spot, strike, rate, dividend, vol, mat, d1_value, v_value in rows:
            value = evaluate(spot, strike, rate, dividend, vol, mat)
            prefactor = (
                mp.exp(-dividend * mat)
                * mp.exp(-(d1_value**2) / 2)
                / mp.sqrt(2 * mp.pi)
                * spot ** (1 - n_spot)
                * mat ** (mp.mpf(n_vol) / 2)
            )
            quotient = value * v_value**4 / prefactor
            reference = polynomial(d1_value, v_value)
            magnitude = max(abs(reference), mp.mpf("1e-12"))
            worst = max(worst, abs(quotient - reference) / magnitude)
            largest = max(largest, magnitude)
        print(
            f"  {field} = d^{n_spot}/dS^{n_spot} d^{n_vol}/dsigma^{n_vol}: worst relative "
            f"disagreement {mp.nstr(worst, 4)} (values up to {mp.nstr(largest, 10)})"
        )
        if worst > mp.mpf("1e-40"):
            failures.append(field)
    return failures


def part_b():
    print("part B: 60-digit nested numerical differentiation vs the extension's float64")
    import quantrisk

    failures = []
    worst = mp.mpf(0)
    for spot, strike, rate, dividend, vol, mat in (
        (100.0, 105.0, 0.03, 0.01, 0.20, 0.50),
        (100.0, 100.0, 0.05, 0.00, 0.20, 1.00),
        (150.0, 100.0, 0.03, 0.02, 0.25, 0.50),
        (60.0, 100.0, 0.03, 0.02, 0.35, 2.00),
    ):
        params = quantrisk.pricing.MarketParams(
            spot=spot, rate=rate, dividend_yield=dividend, volatility=vol, maturity=mat
        )
        option = quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, strike)
        fifth = quantrisk.pricing.black_scholes_mixed_fifth_derivatives(option, params)
        price = price_callable(mp.mpf(strike), mp.mpf(rate), mp.mpf(dividend), mat)
        for index, field in enumerate(PY_FIELDS):
            n_spot, n_vol = 5 - index, index

            def along_spot(sigma_value, n_spot=n_spot, price=price, spot=spot):
                return mp.diff(
                    lambda s: price(mp.mpf(s), sigma_value), mp.mpf(spot), n=n_spot, method="step"
                )

            exact = (
                along_spot(mp.mpf(vol))
                if n_vol == 0
                else mp.diff(along_spot, mp.mpf(vol), n=n_vol, method="step")
            )
            got = mp.mpf(repr(float(getattr(fifth, field))))
            relative = abs(got - exact) / max(abs(exact), mp.mpf("1e-30"))
            worst = max(worst, relative)
            flag = "ok" if relative < mp.mpf("1e-12") else "FAIL"
            if flag == "FAIL":
                failures.append(f"{field} at S={spot}")
            print(
                f"  {field} at S={spot} v={vol}: mpmath {mp.nstr(exact, 12)} / extension "
                f"{mp.nstr(got, 12)} rel {mp.nstr(relative, 3)} {flag}"
            )
    print(f"  worst relative disagreement over the grid: {mp.nstr(worst, 4)}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--precision", type=int, default=60, help="mpmath working digits")
    arguments = parser.parse_args()
    mp.mp.dps = arguments.precision
    failures = part_a() + part_b()
    if failures:
        print(f"FAILED: {failures}")
        return 1
    print(f"both parts agree at {arguments.precision} digits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
