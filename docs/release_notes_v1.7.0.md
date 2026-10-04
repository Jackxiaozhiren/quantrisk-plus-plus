# v1.7.0 — an added order, and the answer it did not buy

Cut on the revision whose CI this note reports below. A release note cannot describe its own
publication: the tag, the run identifiers and the asset hashes are read from the API afterwards, and
`docs/phase_reports/phase-22-v1.7.0.md` records them once the tools have said them. Three releases of work sit between
`v1.6.0` and this tag: Phase 19 made the core's `[[nodiscard]]` claim cover the whole surface rather
than the part an attribute happened to mark, Phase 20 shipped the mixed fifth partials, and Phase 21
used them to measure whether the crossing radius widens again.

## What this release adds

- **The six mixed fifth partials in the core.** `pricing.black_scholes_mixed_fifth_derivatives`
  returns `V_SSSSS` through `V_sigmasigmasigmasigmasigma` as closed forms in the shape the
  third- and fourth-order structs already keep, `V = P · S^(1−n_spot) · T^(n_vol/2) · R(d1, v) / v⁴`.
  The numerator polynomials reach **d1^8** — the degree in `d1` is `8 − n_spot`, because "order five"
  bounds the derivative, not the polynomial. 204 C++ tests (`548,368` assertions in 203 Catch2 cases),
  477 Python tests.
- **The derivation is now a command, not a sentence.**
  `scripts/derive_fifth_order_partials.py` parses the numerators out of the C++ source, forms the
  quotient of the symbolic derivative of the price by the prefactor the header claims, and compares them
  at 60 markets spread over the `(d1, v)` plane: worst relative disagreement **8.7e-58** at 60 working
  digits, with nothing fitted. Its second part meets the compiled extension against 60-digit nested
  numerical differentiation at **4.6e-15** relative on four markets — float64's own last-digit noise.
- **The order-five crossing measurement.** `experiments/fifth_order_crossing_map/` (suite member 18)
  adds `(1/120)·d⁵V/du⁵` to the column truncation and asks the question on the same five books under the
  same rule, importing the books, the grid, the `0.005` tolerance and the radius rule from the Phase 18
  experiment so nothing about the definition was restated. The result: the radius grows again on
  **2 of 5 books** — the published ladder `0.15 → 0.20` (factor 1.33, against its own cubic-to-quartic
  3.00) and the deep out-of-the-money ladder `0.20 → 0.30` (factor 1.50) — and is unchanged on 3, of
  which 2 sit at the swept grid edge and are flagged as unresolvable rather than counted as negative.
  Inside the quartic's own radius the quintic is the closest of the three orders on **5 of 5**.
- **A core-surface claim with a population.** Every namespace-scope function the core declares now
  carries `[[nodiscard]]` or a disclaimer at its own declaration: 110 declarations, 102 distinct names,
  25 disclaimed, and a guard that reads both directions through the headers so a wrapped declaration
  cannot hide.
- **Counts that had no owner now have one.** The C++ totals four documents repeated are read from
  CTest's own list; the README's experiment table, the manifest's directory list, the report's suite and
  test counts, and the order-five radius table are each derived from the tree or the artifact that owns
  them.

## What this release corrects in itself

`v1.6.0` published "the radius widens from 0.05 to 0.15" as though it were a property of the expansion.
Phase 18 measured it on five books and found the direction transfers while the magnitude does not
(factors 1.3 to 3.0); that release note carries the dated correction and this one repeats the finding at
a second order. The order-five-to-four piece ratio spans 0.057 to 0.588 across the same set and orders
the widening no better than its predecessor did, so **no mechanism is offered** in place of the one that
failed twice.

The performance figures in this note are the run behind the tag: `8.45×` versus a pure Python loop and
`0.471×` versus vectorised NumPy, `44,549,572` paths/s for the core against the `5,271,981` a
pure-Python loop reaches on the same machine. They are not constants — the same binary has measured
`21,130,162` paths/s on a loaded desktop — and the committed history spans `7.77×–8.70×` /
`0.42×–0.51×`.

## Verification at this release

```text
uv run python scripts/run_benchmark_suite.py --require-all   18/18 executed and passed, 0 failed, 0 skipped, 158.7s
uv run pytest tests/python -q                                477 passed
uv run ctest --preset dev                                    100% tests passed out of 204 (9.57 s)
./build/dev/quantrisk_tests                                   All tests passed (548368 assertions in 203 cases)
uv run quantrisk validate                                    7/7 checks passed
uv run ruff check . / ruff format --check .                  all checks passed / 148 files already formatted
uv run mypy python/quantrisk                                 no issues found in 23 source files
uv run clang-format --dry-run -Werror <4 files>              exit 0
uv run latexmk -pdf paper/technical_report.tex               44 pages, 1003093 bytes
uv run python scripts/run_mutation_suite.py --list           34 plants declared
```

Two of this release's fixes exist because CI, not the laptop, was the first place they could be seen:
see `docs/integrity_audit.md` finding 54 for a bit-equality assertion that `libm` broke on Linux and a
test-count sentence in `docs/limitations.md` that no local pattern covered.

## What is still not here

- No bound. A radius is a grid label: the widened region on the published ladder contains a *looser*
  worst column (`3.81e-03` at 0.20 against `1.62e-03` at 0.15), and the amount of the map's error at
  published scale is untouched — still 16.2 % off on `risk_off` after the quartic, with order five not
  evaluated against that figure.
- No oracle for the higher orders. Nothing in this dependency set publishes a third, fourth or fifth
  spot/vol partial, so five of the six fifth-order fields are anchored by stencils of this project's own
  fourth-order family; the price-side checks (the contraction, and the derivation script's part B) are
  what break that circularity, and they are narrower than the routes they complement.
- Five books, twice. Not a family, and no distribution is estimated from it.
- `sympy` is still not a project dependency, so the derivation script runs by hand with `uv run --with
  sympy`; the assertion and Catch2-case totals are prose with no derived owner.
- The rules that were enforced: no PyPI publication, no real market data inside the engine, no
  production-readiness claim, no cost above zero.
