# Phase 20 — the order-five terms shipped as arithmetic, and the answer they would buy withheld

Phase 17 measured that the fifth-order term of the stress-map column error sits above the subtraction
noise, and Phase 18 found the expansion is not descending at all on the short-dated book. Both said the
same thing about the same missing piece: the core could not express order five, so no experiment could
use it. This phase ships the six mixed fifth partials, derives them rather than typing them, and then
stops before the measurement — deliberately, because a capability and the claim that consumes it are
separate things and only the first one was earned here.

## 1. Completed

- **`MixedFifthDerivatives` in the core.** `black_scholes_mixed_fifth_derivatives` returns the six
  mixed partials of total order five: `V_SSSSS`, `V_SSSSsigma`, `V_SSSsigmasigma`,
  `V_SSsigmasigmasigma`, `V_Ssigmasigmasigmasigma`, `V_sigmasigmasigmasigmasigma`. Closed forms, no
  differencing at call time, `[[nodiscard]]`, degenerate-market limits, and validation raised before
  any polynomial is evaluated — the same contract the third- and fourth-order structs keep.
- **The derivation is a committed command.** `scripts/derive_fifth_order_partials.py` parses the
  monomial numerators out of `cpp/src/pricing/black_scholes.cpp` and checks them against the symbolic
  derivative of the price function, then checks the compiled extension against 60-digit nested
  numerical differentiation. It exits non-zero on disagreement. Before this phase the claim "the closed
  forms were derived, not transcribed" was a sentence in a header comment; it is now a script a reader
  can run.
- **Tests.** Three new Catch2 `TEST_CASE`s (ten slope routes over the nine-rung mixed ladder, exact
  call/put parity, finiteness plus the degenerate limit) and five new pytest tests over the bindings
  (two routes per mixed field where both axes have a parent, the multinomial contraction against five
  nested differences of the price, parity, degenerate, invalid instrument). The C++ suite is 204 tests
  under CTest, 548,368 assertions in 203 Catch2 cases; the Python suite is 465 tests.
- **The counts and claims this moves were synced, and their owners extended.** `docs/limitations.md`
  gained item 82, `docs/validation_matrix.md` gained row 21 (24 rows), and the C++ totals are now read
  from the build by `test_documents_that_count_the_cpp_tests_agree_with_the_build` rather than from a
  remembered number in four documents.
- **Not done, and named here rather than buried.** The fifth-order crossing experiment does not exist.
  No radius claim, no widening factor, no analysis note at order five. §8 records the design so the
  next phase starts from a specification rather than from a blank file.

## 2. Mathematical assumptions

With `v = sigma sqrt(T)`, `P = e^{-qT} phi(d1)` and `d1 = (ln(S/K) + (r - q + sigma^2/2)T)/v`, every
partial of total order five has the shape the order-four family has, one power of `v` further:

```text
V_(a,b) = P * S^(1-a) * T^(b/2) * R_ab(d1, v) / v^4,      a + b = 5
```

with the six numerator polynomials as they stand in the source:

```text
q50 = -d1^3 - 6 d1^2 v - 11 d1 v^2 + 3 d1 - 6 v^3 + 6 v
q41 = d1^4 + 2 d1^3 v - d1^2 v^2 - 6 d1^2 - 2 d1 v^3 - 6 d1 v + v^2 + 3
q32 = -d1^5 + d1^4 v + d1^3 v^2 + 9 d1^3 - d1^2 v^3 - 6 d1^2 v - 2 d1 v^2 - 12 d1 + v^3 + 3 v
q23 = d1^6 - 3 d1^5 v + 3 d1^4 v^2 - 12 d1^4 - d1^3 v^3 + 24 d1^3 v - 15 d1^2 v^2 + 27 d1^2
      + 3 d1 v^3 - 27 d1 v + 6 v^2 - 6
q14 = -d1^7 + 4 d1^6 v - 6 d1^5 v^2 + 15 d1^5 + 4 d1^4 v^3 - 42 d1^4 v - d1^3 v^4 + 42 d1^3 v^2
      - 48 d1^3 - 18 d1^2 v^3 + 78 d1^2 v + 3 d1 v^4 - 39 d1 v^2 + 24 d1 + 6 v^3 - 12 v
q05 = d1^8 - 4 d1^7 v + 6 d1^6 v^2 - 18 d1^6 - 4 d1^5 v^3 + 54 d1^5 v + d1^4 v^4 - 60 d1^4 v^2
      + 75 d1^4 + 30 d1^3 v^3 - 150 d1^3 v - 6 d1^2 v^4 + 105 d1^2 v^2 - 60 d1^2 - 30 d1 v^3
      + 60 d1 v + 3 v^4 - 15 v^2
```

Three facts a reader should not have to guess. First, **the degree in `d1` is `8 - a`, not `5 - a`**:
differentiating the price five times in total reaches `d1^8` in the pure-volatility field, because
every `sigma` derivative brings down another `d1`. "Order five" bounds the *order* of the derivative,
not the degree of the polynomial, and §4 records the cost of confusing the two. Second, `v^4` sits
under all six fields, so `sigma = 0` and `T = 0` are limits rather than divisions, and the
implementation returns the limit (every field zero) instead of an overflow. Third, neither `r` nor `K`
survives anywhere except inside `d1`, which is what makes the difference routes along the two axes
independent checks of the same polynomial rather than two halves of one formula.

The contraction the order-five term enters the Taylor polynomial through is the fifth directional
derivative along a joint shock `(h, k)`:

```text
d5V/du5 = V_SSSSS h^5 + 5 V_SSSSsigma h^4 k + 10 V_SSSsigmasigma h^3 k^2
          + 10 V_SSsigmasigmasigma h^2 k^3 + 5 V_Ssigmasigmasigmasigma h k^4
          + V_sigmasigmasigmasigmasigma k^5
```

with the multinomial coefficients `(1, 5, 10, 10, 5, 1)`, and `h` the absolute spot move and `k` the
volatility move — the same convention `docs/analysis/two_factor_error_bound.md` uses, so a future
order-five truncation composes with the published cubic and quartic ones without a rescaling step.

Regularity: `S, K, sigma, T > 0`, continuous dividend yield, one strike, no early exercise — the
European Black–Scholes–Merton setting of every other partial in this file. Nothing in this phase
extends the model class.

## 3. Files changed

| File | Change |
|---|---|
| `cpp/include/quantrisk/pricing/black_scholes.hpp` | `MixedFifthDerivatives` struct, per-field derivative identities, the shape claim, `[[nodiscard]]` declaration |
| `cpp/src/pricing/black_scholes.cpp` | the six monomial numerators `q50…q05`, the shared `P/v^4` prefactor, the degenerate limit |
| `bindings/python_bindings.cpp`, `python/quantrisk/pricing.pyi` | struct and function registered, stub added |
| `tests/cpp/test_black_scholes.cpp` | three `TEST_CASE`s: ten slope routes over nine rungs, exact parity, finite + degenerate + validation error |
| `tests/python/test_fifth_order_partials.py` | new, 5 tests over the bindings |
| `scripts/derive_fifth_order_partials.py` | new, the re-derivation and the 60-digit spot check |
| `docs/limitations.md` | item 82 |
| `docs/validation_matrix.md` | row 21, count 23 → 24 |
| `README.md`, `docs/interview_defense.md`, `docs/reproducibility.md`, `paper/technical_report.tex` | C++ totals 201 → 204, assertions 548,217 → 548,368, Catch2 cases 200 → 203, matrix rows, limitation count |
| `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md` | the row-count citations those notes restate |
| `docs/integrity_audit.md` | the Phase 20 addendum, findings 49 and 50 |
| `paper/technical_report.tex`, `paper/technical_report.pdf` | the order-five paragraph in \`sec:fourth-order\`, headline counts, rebuilt PDF |
| `scripts/run_mutation_suite.py` | `fifth-order-numerator-drops-a-cube` plant, and the anchors of nine plants that key on figures this phase moved |

## 4. The three ways this derivation went wrong before it went right

Recording these is not throat-clearing: each one would have produced a confident wrong claim had it
been stopped at the first green.

**The `d1` that omitted the dividend yield.** The first symbolic setup defined
`d1 = (ln(S/K) + (r + sigma^2/2)T)/v`, which is the no-dividend formula, and then differentiated a
price function that was not internally consistent. The shape assertion caught it by reporting a
residual proportional to `exp(T q)`: with a `q` in the discount and no `q` in `d1`, the quotient cannot
be a function of `(d1, v)` alone. The core's own `d1` was read from `black_scholes.cpp:57` and the two
were made to agree.

**Fitting coefficients into a basis too small for them.** Having a numerical target, the next attempt
solved a least-squares problem for the coefficients of a polynomial of *total degree at most five* in
`(d1, v)` — the reasoning being that a fifth derivative cannot produce more than five powers. It
returned twenty-one nonzero coefficients that were not integers and a residual of order one. The
premise was wrong rather than the arithmetic: `q05` contains `d1^8`. Any basis truncated at total
degree five is a model that cannot represent the truth, and a fit under it will report the shortfall
as noise. The same confusion went into an assertion I had just added (`total_degree <= 5`), which fired
on `q23` and was replaced by the caps the data supports — degree at most eight in `d1`, at most four in
`v` — with the observed degrees per field printed by the script's own header comment rather than
asserted as law.

**Assumed symbols make a shape check pass vacuously.** `sp.symbols("w v", real=True)` and the `w` that
`sp.sympify` produces from a bare name are different sympy objects, so `is_polynomial(W, V)` treated
the parsed source's `w` as a *coefficient* and returned True whatever the expression was. The check was
decorative until `expression.free_symbols <= {W, V}` was added next to it; a stray `sigma` demonstrates
the difference — `is_polynomial` says True, the subset test says False. This is finding 48's shape
(fourth time) one language over: a guard that cannot fail is worse than no guard, because it is cited.

The approach that worked needed no fitting: form the quotient of the exact symbolic derivative by the
prefactor the header claims, evaluate it at 60 markets spread over the `(d1, v)` plane, and compare it
with the polynomial parsed from the source. Nothing is adjusted, so agreement at the working-precision
floor means the two sides are one function.

## 5. Exact test results

```text
uv run cmake --build --preset dev -j 4             core, tests, reference tool, extension: built
uv run ctest --preset dev                          100% tests passed out of 204 (10.24 s)
./build/dev/quantrisk_tests --verbosity quiet      All tests passed (548368 assertions in 203 cases)
uv run quantrisk validate                          7/7 checks passed
uv run pytest tests/python -q                      465 passed in 49.50s
uv run ruff check .                                All checks passed!
uv run ruff format --check .                       142 files already formatted
uv run mypy python/quantrisk                       Success: no issues found in 23 source files
uv run clang-format --dry-run -Werror <8 files>     exit 0
uv run python scripts/verify_evidence_manifest.py  85 OK, 0 CHANGED, 0 VOLATILE, 0 MISSING, 0 unlisted
uv run latexmk -pdf paper/technical_report.tex    44 pages, 1003090 bytes (1001529 before the
                                                  order-five paragraph; 44 pages unchanged)
uv run python scripts/run_mutation_suite.py --list  30 plants declared
uv run --with sympy python scripts/derive_fifth_order_partials.py
      part A: worst relative disagreement 8.856e-59 / 1.091e-58 / 8.614e-59 / 8.659e-58
              / 9.809e-59 / 4.653e-59 over 60 markets (q50, q41, q32, q23, q14, q05)
      part B: worst relative disagreement over the grid: 4.619e-15
      exit 0
```

The machine was busy during these runs (load average 8.1 at the start, a desktop session and another
agent active), which affects timings and would affect any throughput figure. No throughput figure was
re-measured in this phase and no committed artifact changed, so the load affects the wall-clock numbers
above and nothing else.

Two guards' own falsification, both run by hand because the sweep refuses a dirty tree:

- **the derivation script.** Changing `q32`'s `9.0 * first * first * first` to `10.0 *` made part A
  report `q32: worst relative disagreement 300.0` and `FAILED: ['q32']`; restoring the file
  byte-identically (sha256 `92e8bb61c2527c99768b9d2eef67a0f02865b0f3bf8d09f074d942e6f4bdaf8e` on both
  sides, `cmp` silent) returned exit 0. Part A reads the source, so it is the part a source edit
  tests; part B reads the compiled extension and was not rebuilt for the control.
- **the C++ routes.** `fifth-order-numerator-drops-a-cube` is in the sweep's list and names the new
  `TEST_CASE` as its guard, so the compiled form is checked on a committed tree by CI-executed machinery.

## 6. Numerical validation

- **Identity against the price function.** At 60 markets spanning `d1` from -3 to 3 and `v` from 0.10
  to 1.20, with `K`, `r`, `q` and `T` varied, each shipped numerator agrees with the quotient of the
  exact symbolic derivative to `8.7e-58` relative or better — at 60 working digits that is the floor,
  not a tolerance that was picked.
- **The compiled pipeline against high-precision differentiation.** At four markets (including a deep
  out-of-the-money put-like strike at 60 and a two-year tenor) all six fields agree with nested
  60-digit numerical differentiation to `4.6e-15` relative worst, which is float64's own last-digit
  noise. This is the check that reaches the prefactor, the `S` and `T` powers and the `v^4` division,
  not just the numerators.
- **Difference routes.** C++: ten routes over nine rungs, worst residual `1.9e-3` of its own band
  (`1e-8 * |reference| + 1e-13`), so every route sits more than 500x inside its tolerance; step noise
  sits at about `1e-11` of the value. Python: ten routes over five markets, loosest `1.5e-4` relative
  at the finest of three steps, volatility-axis routes near `1e-9`, against a `1e-3` band.
- **Contraction against the price.** The multinomial contraction of the six fields agrees with five
  nested five-point differences of `black_scholes` itself to `4.8e-3`, `1.0e-4` and `5.5e-4` relative
  on the three rays, against a `5e-2` band, at the widest rung; the same rays at finer rungs degrade to
  `8.1e-2` and `6.7` because five nested divisions by the scale are round-off dominated. Reported in
  the test and in limitation #82 rather than hidden by the minimum the test takes.
- **Exactness where exactness is available.** Call and put agree on all six fields bit for bit (the
  parity residual is linear in spot and flat in volatility), and the degenerate market returns zero in
  every field.

## 7. Remaining limitations

Limitation #82, in short. No library in this dependency set publishes a fifth partial, so five of the
six fields are anchored by stencils of the project's own fourth-order family — a slip living in that
family would be inherited by the route meant to catch it, and only the price-side checks (the
contraction, and part B of the derivation script at four markets) break that circularity. The
`min`-over-rungs assertions are weaker than fixed-step ones and the rungs that fall outside the band
are published next to them. And nothing here says anything about the stress map: the order-five terms
are arithmetic the core can now perform, not a claim that the crossing radius widens again.

## 8. Technical debt

1. **The order-five crossing experiment (the item this phase chose not to spend).** The design, so it
   does not have to be re-derived: reuse `experiments/second_book_crossing_map/run.py`'s re-derivation
   harness and its equality gate, add a quintic truncation built from
   `black_scholes_mixed_fifth_derivatives` contracted with `(1, 5, 10, 10, 5, 1)` along each column's
   `(h, k)`, and ask whether the contiguous paired-magnitude radius grows again from the quartic's. Four
   controls are mandatory before it publishes: the quartic and cubic truncations must come back
   bit-identical to the two shipped experiments and to the five-book run on the published book; the
   cubic and quartic radii must come back at 0.05 and 0.15; the order-five piece must reproduce the
   documented contraction coefficient-for-coefficient; and the radius rule must stay the paired
   contiguous one, since Phase 18 shipped two refusals against looser variants. The honest prior is not
   optimistic: Phase 18's five books show the *mechanism* (a small order-four piece leaving little for
   order five to remove) already refuted, so a widening is a measurement, not a prediction.
2. **The derivation script is not in CI.** `sympy` is not a project dependency and this phase did not
   add one, so the script runs by hand with `uv run --with sympy`. Either sympy joins the `dev` extra
   and a thin pytest wrapper skips when it is absent (the pattern the four oracle-gated modules
   already use), or part A's comparison moves to exact rational arithmetic in pure Python. Until one of
   those happens its verdict belongs to the phase report that records it, not to a gate.
3. **Post-tag accounting and `v1.7.0`.** `v1.6.0`'s assets are frozen; this tree carries a corrected
   radius claim, a whole-surface `[[nodiscard]]` statement, and a fifth-order API newer than the tag.
   A `v1.7.0` must state the radius per book, carry the surface counts the way item 80 does, and note
   that order five is available without an attached crossing result.
4. **Unowned counts still in prose.** The `ruff format --check` file count (142 now) and the
   "eleven routes over nine rungs" style self-descriptions are read by no guard; Phase 19 item 3
   already lists this residue and this phase did not shrink it — it did move the C++ totals onto
   CTest's own list, which is where the four documents that quote them now read from.

## 9. Gate

**Not a release, and no artifact moved.** Version stays `1.6.0`, tag stays `b4e4bea`. No experiment or
benchmark input changed — the fifth partials are consumed by nothing in the tree — so no artifact was
regenerated, the suite roll-up was not re-run, and `verify_evidence_manifest.py` still reports
`85 OK / 0 CHANGED / 0 VOLATILE / 0 MISSING / 0 unlisted` with "Evidence is intact." The performance
prose therefore carries the numbers the previous freeze measured, and this phase adds no throughput
claim of its own.

The falsification sweep refuses a dirty target, so its verdict is a claim about a revision rather than
about a working tree: it runs on the commit this report ships in, and the paragraph recording it is
appended in the commit after that — the ordering `CONTRIBUTING.md` §4 and Phases 17, 18 and 19 all
describe.

The sweep ran on `631d7c5`, the commit that carries the fifth-order core, its tests and the re-keyed
anchors, with `git status` empty before and after it. Its own line: `30/30 planted defects were rejected
by their guard.` The plant this phase added fired --- `fifth-order-numerator-drops-a-cube` removes a
`d1^3` term from `q32`, the harness rebuilds `quantrisk_tests`, and the new `TEST_CASE` names it --- and
so did the one Phase 18 left behind for the radius rule (`radius-reads-one-signed-column-at-a-time`),
which is the check that a fifth-order experiment would still have to pass. Nine other plants key on
figures this phase moved (the C++ totals, the limitation count, the matrix rows, the experiment table,
the report counts) and their anchors were refreshed in the same commit that moved the figures, which is
what makes `tests/python/test_mutation_suite.py` the thing that notices a stale anchor rather than a
later reader.
