# Phase 16 — the fourth order, shipped, measured, and honest about what it does not buy

Date: 2026-10-01 · Files: core + 1 experiment + 2 test files + 8 documents · Suite member 16 · Release: `v1.6.0`

## 1. Completed

1. **The closed forms, corrected.** `docs/phase_reports/phase-15-restrike-gamma.md` §8 published the
   five order-four partials as groundwork, and three of the five carried the wrong power of `T` because
   the `d/dsigma|S` chart operator had been written dividing by `sqrt(T)` where the chain rule multiplies
   by it. The section now states the uniform shape
   `V = P · S^(1-n_spot) · T^(n_sigma/2) · R(d1, v) / v^3`, with `P = e^{-qT} phi(d1)`, `v = sigma sqrt(T)`,
   `d2 = d1 - v`, and the five numerators

   | order | `R(d1, v)` |
   |---|---|
   | (4,0) | `d1^2 + 3 d1 v + 2 v^2 - 1` |
   | (3,1) | `d1 (v^2 + 3 - d1^2)` |
   | (2,2) | `d1^4 - 2 d1^3 v + d1^2 (v^2 - 5) + 5 d1 v - v^2 + 2`  =  `d1^2 d2^2 - 5 d1^2 + 5 d1 v - v^2 + 2` |
   | (1,3) | `-d1^5 + 3 d1^4 v - 3 d1^3 v^2 + 7 d1^3 + d1^2 v^3 - 12 d1^2 v + 6 d1 v^2 - 6 d1 - v^3 + 3 v` |
   | (0,4) | `d1^6 - 3 d1^5 v + 3 d1^4 v^2 - 9 d1^4 - d1^3 v^3 + 18 d1^3 v + 12 d1^2 - 12 d1^2 v^2 + 3 d1 v^3 - 12 d1 v + 3 v^2` |

   They were recovered by solving a 28-coefficient linear system against the exact symbolic fourth
   derivative of the BSM price at 80 decimal digits, then re-tested on 200 fresh points per order with
   non-zero `r` and `q`; worst relative error 4.5e-77. The same run also found that `R(0,4)` had been
   committed with the opposite sign.
2. **`MixedFourthDerivatives` in the core.** `cpp/include/quantrisk/pricing/black_scholes.hpp` carries the
   struct with four fields named for the factors they differentiate, and `black_scholes_mixed_fourth_derivatives`
   implements them in the shape above as Horner in `d1` with coefficients polynomial in `v`. Degenerate
   edges take their limit (zero) rather than dividing by `v^3`.
3. **Bindings, stub and surface.** `py::class_` plus the function registration, `python/quantrisk/pricing.pyi`
   regenerated, and `tests/python/test_extension_surface_parity.py` extended so the newest API in the tree
   has to be visible to the parser that reads the bindings.
4. **Three C++ cases.** Ten finite-difference routes over a nine-rung ladder (worst residual-to-band
   ratio 1.1e-2), two exact relations obtained by differentiating the published `vanna`/`volga` homogeneity
   identities in volatility (worst relative residual 5.5e-16 and 1.2e-15), and bit-exact call/put identity
   with the degenerate limit and the rejection of invalid inputs.
5. **The experiment.** `experiments/fourth_order_crossing_map/run.py` (suite member 16) adds the order-four
   piece to v1.5.0's own column truncation — imported from that experiment, not re-typed — and measures the
   crossing radius, the residual ordering, the zero counts, and the published-scenario amount.
6. **The documents.** Analysis note `docs/analysis/fourth_order_crossing_map.md`, `docs/findings.md` §8,
   `docs/validation_matrix.md` row 19, `docs/limitations.md` #79, this report, the audit addendum
   (findings 40-43), `docs/interview_defense.md` Q26, and `paper/technical_report.tex`
   `\subsection{The fourth order...}` `\label{sec:fourth-order}`.

## 2. Mathematical assumptions

- Model: Black-Scholes-Merton with continuous dividend yield, `S, K, sigma, T > 0`; the stress map is
  `delta_i s_i + gamma_i s_i^2 + vega_i a_i` with `gamma` carrying the one-half and `a` an *absolute* vol
  move, so a column is indexed by the *relative* spot move `delta` and `h = S delta`.
- The two chart operators `d/dS|sigma = (1/(S v)) d/dd1` and `d/dsigma|S = sqrt(T) [(1 - d1/v) d/dd1 + d/dv]`
  hold in the `(d1, v)` coordinate where `S = K exp(d1 v - v^2/2 - (r - q) T)`. Neither `r` nor `K` survives
  a derivative except through `d1`, and `q` only through `e^{-qT}`, which is why the chart's zero-rate
  derivation transfers to the core's dividend-yield model unchanged.
- A partial of total order four with `n_spot` spot derivatives scales as `S^{1 - n_spot}` and carries
  `T^{n_sigma/2}`; all five share the denominator `v^3`. This is what the C++ homogeneity cross-checks
  exploit.
- The truncation of the shipped map's error is a *two-variable Taylor polynomial at the base market*. It
  is an asymptotic series evaluated at finite move: §5 measured that adding the next order can make the
  amount estimate worse on individual rays.
- Root location: a zero is a sign change of a function sampled at 401 points and refined by 40 bisection
  steps. Two nearby sign changes may be one root of the underlying smooth function.

## 3. Files changed

| file | change |
|---|---|
| `docs/phase_reports/phase-15-restrike-gamma.md` | §8 rewritten: five numerators, the corrected shape, the verification method, and an account of what the first version got wrong |
| `cpp/include/quantrisk/pricing/black_scholes.hpp` | `MixedFourthDerivatives` (4 fields) + `black_scholes_mixed_fourth_derivatives` declaration |
| `cpp/src/pricing/black_scholes.cpp` | implementation in the published shape, degenerate limit, per-field derivation notes |
| `bindings/python_bindings.cpp` | class registration + function registration |
| `python/quantrisk/pricing.pyi` | regenerated (2 names) |
| `tests/cpp/test_black_scholes.cpp` | 3 cases, 10 finite-difference routes, 2 exact identities, parity/degenerate/rejection sections, two new tolerance helpers |
| `experiments/fourth_order_crossing_map/run.py` | new experiment (suite member 16) |
| `experiments/fourth_order_crossing_map/results/*` | JSON + two CSVs |
| `tests/python/test_fourth_order_crossing_map.py` | 14 tests: coefficient re-derivation, book sums, polynomial contraction, fit and distance instruments, radius re-derivation, zeros re-measured, slopes re-fitted, scenario re-priced, prose figures, refusals, provenance, temp-tree reproduction |
| `scripts/run_benchmark_suite.py`, `scripts/build_evidence_manifest.py`, `scripts/run_mutation_suite.py` | 16th member; new results directory; refreshed anchors |
| `README.md`, `docs/findings.md`, `docs/validation_matrix.md`, `docs/limitations.md`, `docs/interview_defense.md`, `docs/reproducibility.md`, `docs/analysis/fourth_order_crossing_map.md`, `paper/technical_report.tex`, `docs/integrity_audit.md` | results, counts, and the refreshed volatile performance figures |

## 4. Tests executed

`uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy python/quantrisk`,
`uv run cmake --build --preset dev`, `uv run ctest --preset dev`, `uv run pytest tests/python -q`,
`uv run python scripts/run_benchmark_suite.py --require-all`, `uv run quantrisk validate`,
`uv run python scripts/build_evidence_manifest.py`, `uv run python scripts/verify_evidence_manifest.py`,
`uv run --frozen clang-format --dry-run -Werror` on the four touched C++ files, `uv run latexmk -pdf`,
and `uv run python scripts/run_mutation_suite.py` twice on committed trees — 19/19 on the release
commit, then 20/20 after this phase's producer-docstring guard was given its own planted defect.

## 5. Exact test results

```text
ruff check .                 All checks passed!
ruff format --check .        132 files already formatted
mypy python/quantrisk        Success: no issues found in 23 source files
ctest --preset dev           100% tests passed out of 201        Total Test time (real) = 7.94 sec
quantrisk_tests              All tests passed (548217 assertions in 200 test cases)
pytest tests/python -q       437 passed in 22.04s
run_benchmark_suite --require-all
                             suite: 16/16 executed and passed, 0 aggregated from disk, 0 failed,
                             0 skipped, 76.4s total
quantrisk validate           7/7 checks passed
clang-format --dry-run       exit 0
latexmk -pdf                 Output written on build/technical_report.pdf (42 pages, 998781 bytes)
```

The fourth-order experiment's own summary line:

```text
quartic radius |delta| <= 0.15: worst distance 0.0016 (cubic 0.0189); zeros measured 13, cubic 14,
quartic 14; count disagreements 3 -> 1
residual ratio quartic/cubic: 0.286-1.381 at grid size, 0.0013-0.0476 at scale 0.003;
slopes 3.96-4.37 (cubic) against 4.73-5.01 (quartic)
risk_off: priced base -5320.79, cubic +22.27%, quartic -16.19%; restrike cubic +61.15%, quartic -44.46%
```

## 6. Numerical validation

| quantity | result | how |
|---|---|---|
| five order-four numerators | worst relative error 4.5e-77 over 1000 high-precision checks | exact symbolic fourth derivative of the price, 80-digit linear fit, 200 fresh points per order with `r, q ≠ 0` |
| `V_SSSS` against the shipped core | identical | `SpotDerivatives::fourth` closed form `(Gamma/S^2)(A^2 + A - 1/v^2)` re-derived from the same chart |
| C++ closed forms vs the phase-15 report | ≤ 3e-15 relative | Horner in C++ against powers in Python, seven rungs |
| three of four new partials | ≤ 1e-4 relative | five-point volatility slope of the partial one order below (C++ case, and again from Python) |
| exact homogeneity relations | 5.5e-16 / 1.2e-15 relative | `d(vanna)/dsigma` and `d(volga)/dsigma` differentiated once, no bump |
| call/put identity | bit-exact | parity is affine in `S` and independent of `sigma` |
| degenerate edges | exactly 0.0 | `sigma == 0` and `T == 0`, no `inf` from the `v^3` denominator |
| crossing radius | quartic 0.00162 ≤ 0.005 on all seven in-range columns with a priced zero; cubic 0.01887, failing on the four columns at `|delta|` = 0.10, 0.15 | same bracket-and-bisect on the priced error and on both truncations |
| residual ordering | cubic slope 3.96-4.37, quartic 4.73-5.01, ratio slope 0.62-1.04 | over `1e-3 ≤ scale ≤ 3e-1`; through-the-floor fit (2.46-4.30) published beside it |
| amount at `risk_off` | 22.3 % short → 16.2 % over, sign flipped | priced through `run_scenario`, re-measured in the test file |
| k = 0 control | order-four piece equals `V_SSSS h^4 / 24` to 5.3e-16 relative | and the cubic is untouched, because it is imported |

Level: **L1 plus measurement**. No oracle provides a shipped result here — a truncation is not a second
price — so the validation is identities (parity, homogeneity, degenerate limits, the shape `S^{1-n}
T^{n/2}/v^3`), independent finite-difference routes, and a self-consistency comparison between a
polynomial assembled from closed forms and a revaluation of the same book.

## 7. Remaining limitations

Carried by `docs/limitations.md` #79 and `docs/analysis/fourth_order_crossing_map.md` §7:

- The radius is a statement about the **place** of the crossing. The **amount** at published size is still
  16.2 % off, and on one ray at full shock size the quartic residual is 1.38x the cubic's.
- The ordering law is gated over `1e-3 ≤ scale ≤ 3e-1` because below the floor the residuals are arithmetic
  of a subtraction near 1.09e5. Both fits ship so the window is auditable.
- One book: three strikes, one maturity, one base volatility, and the same grid as v1.5.0. No estimate for
  a book whose fourth-order terms do not share these signs.
- Zero counts agree with the priced error on 11 of 12 columns under the quartic and 9 of 12 under the
  cubic, but neither is a root counter: totals are 14 and 14 against 13.
- `run_scenario` still ships a two-factor delta-gamma-vega map. Nothing in this phase changes it.

## 8. Technical debt

1. **A binding can be half-registered.** Adding the `py::class_` without the `pricing.def` left the struct
   reachable and the function absent, and `test_extension_surface_parity.py` passed because it compares the
   module against what the bindings file *declares*. Nothing derives "every public core entry point is
   reachable from Python". Audit finding 43; the cheapest fix is a guard that every `[[nodiscard]]`
   function declared in `cpp/include/quantrisk/**` appears in the bindings file, which is a source-level
   claim and therefore independent of the built binary.
2. **The v1.5.0 report still describes its own release as current in places §8 contradicts.** Left as
   written, per the convention that a phase report states the revision it describes; §8 carries the
   correction and the account of the error rather than being quietly replaced.
3. **`docs/phase_reports/` has no index** that lists which phase shipped which suite member; the mapping is
   reconstructible from the registry but restated by hand in each report's header.
4. **Prose-figure guards match spellings they know.** The new note's figures are policed against the
   artifact; a restatement phrased in a form the guard does not recognise is still unowned. This is the
   standing rule from #76 and #77, not a new one.
5. **The performance prose is re-synced by script, and the script can bite sideways.** The artifact moved
   on each producer run (`8.12×` → `8.00×` → `7.99×` → `8.26×`), so the three documents quoting it were
   re-synced from it. A blanket token replacement corrupted two unrelated figures on the way — `5.4`
   matched inside `5.45 %`, and `1.17e-4`, the worst analytic-vs-FD delta, matched a speed standard
   deviation — and both were caught by set-differencing numeric tokens against `HEAD` rather than by
   reading the diff. The rule this adds to `CONTRIBUTING.md` §4 step 2 in practice: re-sync per field with
   a length-sorted table, audit the token multiset, then refresh the mutation anchors in the same commit.

## 9. Gate

**Ready for release as `v1.6.0`.** Every gate above ran on this tree and reported its own pass; nothing is
asserted about CI until `commits/<sha>/check-runs` says otherwise. The release order is `CONTRIBUTING.md`
§4: commit, re-freeze the manifest on the committed tree, tag the commit the runner verified, build assets
from `git archive <tag>`, and state in the note what the record cannot contain.
