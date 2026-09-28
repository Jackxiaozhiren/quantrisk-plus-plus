# Phase 12 — A worked analysis result: the stress map's remainder bound

Date: 2026-09-28 · Version: 1.1.0 → **1.2.0** · Predecessor: `phase-11-real-data-risk-study.md`

Ranked third in `docs/portfolio_audit.md` §10, and the only item on that list the audit itself
flagged as risky: *"the slowest option and the only one that risks being wrong in a way a specialist
notices — which is exactly why it is worth doing."* Phases 1–11 verified this repository's numbers
against other implementations. This phase adds a claim that no implementation can verify — an
inequality with a proof — and the phase report is therefore also an account of how four
plausible-looking analysis results turned out to be wrong before any of them was published.

## 1. Completed

- **The core gained its higher-order spot sensitivities**, as a new struct and function rather
  than as fields on the frozen `Greeks`: `black_scholes_spot_derivatives` returns
  `V^{(3)} = -(Γ/S)(1 + d₁/v)` and `V^{(4)} = (Γ/S²)(A² + A - v^{-2})`, degenerate limits included.
  Four new Catch2 cases, pybind11 bindings, regenerated stubs.
- **`docs/analysis/delta_gamma_error_bound.md`** — the project's first derivation file: the map
  stated exactly, the regularity hypotheses, the proposition with its proof, five predictions
  written down before being compared, the results, and four places where the analysis stops being
  useful.
- **`experiments/linearisation_error_bound/run.py`** — the thirteenth suite member. 18 swept shocks
  and 600 dense ones, in both directions; the Lagrange coefficient trapped between the extremes of
  the third derivative along the segment; per-direction slope convergence over five shrinking fit
  windows; the quartic's fingerprint on the departure from cubic behaviour; three recorded refusals.
- **Finding 5** in `docs/findings.md`, **rows 13 and 14** of `docs/validation_matrix.md`, a
  **§6.3 subsection with the proposition, its proof and a results table** in the technical report,
  and the counts those moved across README, `docs/interview_defense.md`,
  `docs/reproducibility.md`, `docs/limitations.md`, `docs/portfolio_audit.md`,
  `docs/integrity_audit.md` and `paper/technical_report.tex`.
- **Limitations #65 and #66**, and **three new count guards** — validation-matrix rows, C++ test
  totals read from `ctest -N`, and the suite registry — joining the guards that bind the Python
  test count and the limitations total to their sources.
- **`evidence/manifest.json`** re-frozen over 72 artifacts, with the new experiment directory added
  to the manifest's scope.

## 2. Mathematical assumptions

- **The map is (1), exactly.** `m(δ) = ΔSδ + ½ΓS²δ²` with both sensitivities at the *unshocked*
  market, which is what `detail::contribute()` in `cpp/src/stress/engine.cpp` computes once the `½`
  and the powers of `S` are folded into the exposure blocks the caller supplies.
- **`S, K, σ, T > 0`, `δ > -1`, and the segment bounded away from `S = 0`.** Under those, `V` is
  `C^∞` in spot on a compact segment and Taylor's theorem with the Lagrange remainder applies. The
  two excluded cases are stated rather than absorbed: `S = 0` where `Γ ~ 1/S` diverges, and
  `σ√T = 0` where the core returns zero for every higher derivative and the bound reads `0 ≤ 0`.
- **Call/put equality for every order ≥ 2** is not a convention but a corollary of put–call parity
  being affine in `S`, and it is asserted bitwise in the C++ tests rather than assumed.
- **`R := [V(S+h) - V(S)] - m(δ)`**, chosen so the theorem reads with a plus. The committed stress
  CSV stores the negative of this; magnitudes, ratios and zeros are unaffected, and the sign is
  stated in three places because getting it wrong silently doubles an error rather than flipping a
  conclusion.
- **The book is the published one.** Spot 100, strikes 90/100/110, 5,000 each, `σ = 20 %`,
  `T = 0.5`, `r = 3 %`, zero dividend, copied from `experiments/stress_testing/` so the remainder
  measured here *is* the frozen error curve and not a fresh derivation of it.
- **Single factor, vol held.** That is what makes the remainder cubic. Tie a vol bump to the spot
  move and the omitted mixed partials enter at order `δ²`, and every number here is the wrong shape.

## 3. Files changed

| File | Change |
|---|---|
| `cpp/include/quantrisk/pricing/black_scholes.hpp`, `cpp/src/pricing/black_scholes.cpp` | new `SpotDerivatives` and `black_scholes_spot_derivatives`, additive |
| `bindings/python_bindings.cpp` | both bound in the `pricing` submodule |
| `python/quantrisk/pricing.pyi` | regenerated declarations |
| `tests/cpp/test_black_scholes.cpp` | 4 new cases: stencil agreement, put/parity, degenerate limits, deep-OTM/ITM behaviour |
| `experiments/linearisation_error_bound/run.py` + `results/` | new, 3 artifacts |
| `tests/python/test_linearisation_bound.py` | new, 11 tests |
| `docs/analysis/delta_gamma_error_bound.md` | new — the derivation directory starts here |
| `scripts/run_benchmark_suite.py`, `scripts/build_evidence_manifest.py` | thirteenth member; new results directory |
| `tests/python/test_artifact_metadata.py` | 2 new guards; `SPELLED_NUMBERS` extended to twenty |
| `README.md`, `docs/*.md`, `paper/technical_report.tex` + `.pdf` | the result, and every count it moved |
| `docs/limitations.md` | #65, #66 (66 entries) |

## 4. Tests executed

```bash
uv run cmake --build --preset dev && uv run pip install -e .   # the .so the tests import
uv run ctest --test-dir build/dev                              # 194 passed
uv run pytest -q                                               # 366 passed, oracles installed
uv run pytest tests/python/test_linearisation_bound.py -q       # 11 passed
uv run python scripts/run_benchmark_suite.py --require-all       # 13/13 executed, 0 skipped
uv run python scripts/build_evidence_manifest.py && uv run python scripts/verify_evidence_manifest.py
uv run mypy python/quantrisk && uv run ruff check . && uv run ruff format --check .
(cd paper && latexmk -pdf technical_report.tex)                 # 40 pages, 0 undefined refs
```

Every new assertion was falsified, and four of them failed first — which is the only evidence that
the falsification was real:

- The **key-path guard** aborted the suite on registration, because the headline field I named in
  the registry did not exist in the artifact. That is the guard's entire purpose working on me.
- The **slope guard** failed at first with `3.037 ± 0.003`: eleven standard errors from theory. The
  defect was mine twice over — up and down moves pooled into one fit, and `fit_slope` indexing
  errors by `abs(move)` so both directions silently fit the same curve and reported identical slopes
  to sixteen digits.
- The **finite-difference tolerance** `1e-9` failed at a step of `1e-5` by `3.6e-9` at the
  at-the-money strike: the stencil's own truncation, not the algebra.
- A **quartic stencil written with flipped signs** agreed in magnitude to 4e-11 and disagreed in
  sign, and only passed once an explicit sign assertion was added. A magnitude-only test would have
  been green and wrong.
- The **`converges to 3`** assertion was first written as `== sorted(distances)`, i.e. the opposite
  ordering, and failed on data that was behaving perfectly.
- The offline/`no_test_writes_into_frozen_evidence` session guard from Phase 11 caught nothing here
  because it worked: the new experiment writes only into its own directory.

## 5. Exact test results

| Gate | Result |
|---|---|
| CTest | **194 passed** (547,331 assertions in 193 Catch2 cases), up from 190 |
| pytest, `oracles` extra installed | **366 passed**, 0 failed, 0 skipped |
| pytest without it | **297 collected** (the guard checks this figure on the runner, not locally) |
| Benchmark suite, `--require-all` | **13/13 executed and passed**, 0 failed, 0 skipped |
| Evidence manifest | **72 artifacts, 6,488,904 bytes, 0 CHANGED / 0 VOLATILE / 0 MISSING / 0 unlisted / 0 warnings** |
| `quantrisk validate` | 7/7 |
| mypy / ruff / clang-format | clean |
| Technical report | 40 pages, `\ref` all resolved, `V^{(3)}` table and proof included |

## 6. Numerical validation

**1. The bound is a trap, not an envelope, and it holds everywhere.** `c(δ) = 6R/h³` lies inside the
segment's range of `V^{(3)}` at all 618 shocks tested in both directions — 0 violations. The weaker
absolute form is also satisfied with `|R|/bound` from **0.9962** to **0.2842**, so it is not vacuous;
and it collapses to **0.0229** at a 20 % down move, which is exactly where prediction 3 puts the
remainder's zero. Both facts are in the artifact, separately named, rather than averaged into one
"tightness" number.

**2. The published curve's non-monotonicity is a predicted sign change.** The ladder's
`V^{(3)}` crosses zero at spot **94.5487**, a 5.4513 % down move, and solving `R(δ) = 0` puts the
remainder's zero at a **21.1447 %** down move — inside the single 20 %→30 % bracket where the
*older, already-frozen* artifact changes sign. Two artifacts, different code, agreeing on a
location. The prose that shipped with the old one said the error grows with the shock size, and it
was wrong.

**3. Order three, shown as a limit rather than as a number.** Per direction, over five shrinking fit
windows: down `2.971017 → 2.998785`, up `3.025281 → 3.001209`, against theory 3. A single fitted
slope at a single window is not evidence — at any fixed window the quartic biases it, and pooling the
directions manufactures false precision (see §4).

**4. The fourth derivative is confirmed twice.** Once against a five-point difference of the closed
third derivative (agreement `1.3e-13` worst over the ladder), and once — independently — through
prices: the departure from cubic behaviour per unit of `δ` tends to `S·V^{(4)}/(4V^{(3)}) =
3.7523607`, measured `3.7592892` down and `3.7453790` up at a 0.1 % shock. The two directions
bracket the prediction, which they can only do if the sign of the closed form is right.

**5. Two self-corrections worth recording, because both looked like results.**
*The arithmetic floor.* An earlier draft placed it at `δ ≈ 10⁻³` and quoted a detach sequence with
four significant figures. It came from a single-option test using absolute price increments, so both
the unit and the scale were wrong; measured on this book the floor sits near `δ ≈ 3·10⁻⁵`. The
lesson generalises: a floating-point floor is a property of the magnitude being subtracted, so it
must be re-measured per book and never lifted from a similar-looking experiment. Limitation #66.
*The grid that was quietly 5× too fine.* The supremum along the segment used 2,001 points and cost
36 s of suite runtime; 601 points gives agreement to the seventh decimal and costs 7.5 s. The
coarser choice is in the file with its reason.

**6. What is refused.** Whether the scenario is plausible (a truncation bound says nothing about
choice, and the scenario set has no oracle); whether the cubic bound covers multi-factor shocks
(it does not — mixed partials make the leading remainder quadratic); and whether the bound holds in
the zero-volatility limit (it degenerates to `0 ≤ 0` and the map is exact off the kink).

## 7. Remaining limitations

New: **#65** — the higher-order sensitivities are validated against finite differences of the order
below and against a shared gamma, not against any oracle that publishes a third derivative, so a
systematic error in gamma would propagate invisibly. **#66** — a finite-difference tolerance belongs
to its step and its book, and the analysis's arithmetic floor belongs to the book's magnitude.

Still open from before, unchanged by this phase: no PyPI package and no DOI (#57); the suite registry
is hand-maintained, though its counts are now guarded (#58); cross-platform byte equality of the
frozen evidence remains unavailable, and this phase added 3 more artifacts to that record (#64).

## 8. Technical debt

- **`docs/analysis/` has no structural check that its prose matches its artifact**, other than the
  assertions inside the experiment itself. `tests/python/test_real_data_findings_prose.py` does that
  job for the README and `docs/findings.md`; nothing does it for the derivation file, whose numbers
  were hand-propagated from the artifact in this phase. The right fix is the same pattern applied
  again, and it is not done.
- **The proposition is proved for one factor.** The mixed-partial version is the same style of
  algebra on the two-variable Taylor formula and is recorded as a refusal rather than attempted.
- **A patch script of my own destroyed a LaTeX table.** The Phase 12 counting script built a
  replacement with `str.replace` and a `partition`, and produced
  `\begin{tabular}\begin{tabular}\end{tabular}` — silently, because it "ran successfully". Caught
  only by `latexmk` exiting 12. Scripts that edit prose files should print a diff or be avoided;
  the tool that reports success without the change landing is a known trap and this is the same
  failure class wearing a different hat.
- **Timing claims were deleted rather than maintained.** The suite's wall-clock moved twice this
  phase; the README now points at `wall_seconds` in the artifact instead of quoting a number.
- **Process, again.** Two `git checkout` restores and one whole-file `Write` over tracked content
  occurred while this phase was in flight in a deliberately dirty tree. Each was recoverable; none
  was cheap. See the Phase 11 report §8.

## 9. Gate

**Phase 12: PASS.**

The audit's third ranked item is delivered: a derivation with a statement, hypotheses, proof and
consequences, checked by execution, with the failure of the naive version — a pooled slope eleven
sigma from theory, a floor quoted in the wrong unit — recorded instead of edited away. The claim is
stronger than a benchmark in one specific way worth naming: nothing in the repository can be
substituted for the inequality, and the test that would refute it is a finite difference of a
function the same code computes.

The result also does the thing this project exists to do: it caught a published sentence that was
false of published data, in this repository, written by this author, and nobody had noticed across
two prior audits of exactly that kind.
