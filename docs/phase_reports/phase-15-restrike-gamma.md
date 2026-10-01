# Phase 15 — the recommendation `v1.3.0` published, measured

Date: 2026-09-30. Predecessor: Phase 14 (`phase-14-verification-debt.md`). No `PROJECT_SPEC.md` phase
number: this phase answers the open question Phase 13 left in its own closing paragraph — the
prioritisation "re-strike gamma at the shocked volatility, do not add vanna and volga" was derived but
never measured. Repository version becomes `1.5.0`; nothing here is claimed to be in `v1.4.0`.

## 1. Completed

1. **The measurement.** `experiments/restrike_gamma_map/run.py`, the 15th suite member, builds four
   maps — every exposure at base; gamma alone at `(S, sigma + k)`; gamma at `(S + h, sigma + k)`; all
   three at the shocked market — and prices each through the shipped `stress.run_scenario` against a
   revaluation of the same book, over the same 132-cell joint grid Phase 13 swept. Four artifacts:
   the grid CSV, a per-map table for the published `risk_off`, a per-`delta`-column table of predicted
   and measured error zeros, and the JSON with `headline`, `asymptotics`, `mechanism`, `cancellation`
   and `refusals`.
2. **Five claims, each able to fail, each gated in the run.** (a) the map difference is exactly
   `(gamma(sigma+k) - gamma(sigma)) * delta^2`, with the divided difference trapped by the segment
   range of `d gamma / d sigma` from the core's mixed third partial; (b) how much of the named cubic
   the recipe actually removes; (c) that the map's order is unchanged; (d) the `k = 0` identity control
   and the naive full re-strike priced against both; (e) the truncation's error zeros as a *prediction*
   of where the shipped map looks best.
3. **The answer, including the half that is not a success.** On `risk_off` the recommendation holds —
   the error falls from −5,320.79 to +1,937.72, factor 0.364, removing 86.4 % of the term named. Over
   the 120 swept cells with a volatility move, 45 are no better and 20 at least twice as wrong, worst
   factor 142 — and every one of those 20 is a cell whose shipped-map error was smaller than the term
   being removed. The naive variant is worse than the gamma-only fix on 116 of 120 cells and by a
   factor of 11 on `risk_off`. The order never moves.
4. **A falsified-in-public prediction.** The zeros of the third-order truncation of the base map's
   error — assembled from core closed forms, nothing fitted to the measured errors — are compared with
   the zeros of the priced error by one shared bracket-and-bisect routine. Gated within
   `|delta| <= 0.05`, where the nearest pair agrees to 0.0002-0.0024 against a tolerance of 0.005;
   outside it the drift grows to 0.093 at `|delta| = 0.30` and one column carries a predicted zero the
   map does not have. The gate covers only the regime where a third-order truncation is a fair
   argument, and the drift is recorded rather than caveated.
5. **Cross-artifact agreement, unprompted.** The new experiment's base-map `risk_off` error is
   byte-identical to the number Phase 13's artifact publishes (−5320.792367571179), and its re-derived
   `1/2 V_SSsigma h^2 k` equals Phase 13's published `term_cubic_gamma_sigma` to the last digit. Two
   independent producers, one book, one map — now asserted by
   `test_the_shipped_map_error_is_the_number_the_phase_13_artifact_published`.
6. **Tests that do not reuse the producer.** `tests/python/test_restrike_gamma_map.py`, eleven tests:
   the four variants' exposures rebuilt per-exposure from the pricer and pushed through the engine; the
   committed CSV re-evaluated against that rebuild; the `k = 0` control recounted; the artifact's zeros
   re-found by bisecting the engine; the cancellation cells recounted from the table; the refusals' key
   set; three CSV shapes; the producer docstring's figures; the note, finding 7 and the report's
   figures; and a temp-tree re-run compared field by field with the declared conditioning families.
7. **Two defects in my own tooling, found by the guards and recorded as findings 37 and 38.**
   (a) `SPEEDUP_BANDS` was pinned as the *rounded* envelope of the committed ratios while the
   containment guard compared *raw* values, so a re-frozen run at 0.5104 was reported as outside a band
   whose edge, 0.51, is what that value rounds to. (b) `experiments/two_factor_error_bound/run.py`'s
   `totals(spot, sigma)` scaled three entries by the module-level `SPOT` rather than its own parameter —
   dormant, because only `BASE` is read as an exposure, but found because the Phase 15 experiment started
   from that helper with the same bug. Phase 13's experiment was re-run to prove the fix changes nothing
   published.
8. **Documentation, with owners.** `docs/analysis/restrike_gamma_map.md` (the derivation), `docs/findings.md`
   §7 (leads with the 45 cells), row 18 of `docs/validation_matrix.md`, `docs/limitations.md` #78,
   `docs/integrity_audit.md` findings 37-39, `docs/interview_defense.md` Q25, and a new
   `\subsection` in `paper/technical_report.tex`. The registry, member-count, limitation-count,
   findings-count, matrix-row-count, chapter-count and test-count guards all moved with the content, and
   three mutation anchors had to be refreshed because the prose they key on changed underneath them —
   which is that harness doing its job.

## 2. Decisions, and what they cost

**The map does not change.** `stress.run_scenario` still ships a two-factor delta-gamma-vega map. The
measurement says a re-struck gamma helps on the published scenario and on most of the grid and hurts
badly in a characterised corner; it does not say the shipped contract is wrong, and swapping the
exposure evaluation at the call site would trade a documented approximation for an undocumented one.
Limitation #78 states what a user who needs the joint residual controlled must do instead — re-value
the book.

**The worsening is the finding, not the caveat.** The comfortable version of this phase reports
"0.364× on `risk_off`, recommendation confirmed" and leaves the 45 cells in the CSV. What made the
result worth shipping was converting them into a prediction with a stated radius of validity, and
gating only inside that radius. The cost is a less useful headline: the number a reader can act on is
"helps here, hurts there, here is where", not "improves by 64 %".

**86.4 % is not 100 %, and that is a separate result.** A finite difference of gamma across six
volatility points is smaller than the local derivative the derivation quoted. Stating the fraction,
rather than "removes the dominant term", is what keeps the earlier document's claim checkable.

**One producer's docstring is now a policed surface.** The experiment's own claim block quotes ten
figures, and a guard re-derives each from the artifact. It fired within minutes: my first draft said
the narrow-window slopes spanned 1.94-2.04, and the artifact's aligned-ray base slope is 1.8919.

## 3. Method notes worth keeping

- **Rebuilding a producer's helper independently found a bug in the test, not the artifact.** The first
  draft of `_exposure_points`' predecessor moved all three exposures for `gamma_restrike`, which turned
  it into a fifth map; the two assertions refused to agree and the defect was in the reader. Variants
  that differ by one leg have to be rebuilt one leg at a time.
- **A "minimum" prediction has to be a root.** Locating the minimum of `|error|` from a truncated
  polynomial is tie-broken by scan order when the polynomial has several roots; the sharp,
  tie-free statement is the sign change. Rewriting claim 5 from argmin to zeros changed both its
  behaviour and its honesty.
- **Window regressions of a cancellation residue wobble.** The four-point narrow-end fits spread
  1.89-2.05 while the ratio between the two narrowest scales sits at 1.98-2.01 for all four maps. The
  order claim is quoted on the pairwise number, and both fits are published so the spread is visible.

## 4. Verification, from the tools' own output

Every line below was read out of a command that had already returned; none was written in advance.

| gate | command | what it printed |
| --- | --- | --- |
| C++ | `uv run cmake --preset dev && --build --preset dev`, `uv run ctest --preset dev` | `100% tests passed out of 198`, `Total Test time (real) = 8.32 sec` |
| Python | `uv run --frozen pytest -q` | `423 passed in 23.48s` on the run recorded here; the count, not the seconds, is the claim (411 before the phase, and 354 collected without the `oracles` extra) |
| Suite | `uv run python scripts/run_benchmark_suite.py --require-all` | `suite: 15/15 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 77.7s total` |
| Identities | `uv run quantrisk validate` | `7/7 checks passed` |
| Evidence | `uv run python scripts/build_evidence_manifest.py` then `verify_evidence_manifest.py` | `80 OK`, `0 CHANGED`, `0 VOLATILE`, `0 MISSING`, `0 on disk but not in the manifest`, `Evidence is intact.` |
| Style/types | `ruff format --check .`, `ruff check .`, `mypy python/quantrisk` | `129 files already formatted`, `All checks passed!`, `Success: no issues found in 23 source files` |
| C++ format | `git diff --name-only HEAD -- '*.cpp' '*.hpp'` | empty — the core is untouched this phase, so the clang-format gate has nothing new to check |
| Report | `latexmk -pdf technical_report.tex` in `paper/` | `Output written on technical_report.pdf (43 pages, 970663 bytes)` |

Two things the gate set caught while the phase was still open, both recorded above in §1.7:
the band guard that could reject the measurement it was derived from (audit finding 37), and the
`spot`-ignoring helper that the new experiment inherited and then outgrew (finding 38). A third catch
was quieter: refreshing the volatile speed figures for the second time moved `README.md`'s quoted ratio
from `7.98×` to `8.12×`, and the mutation harness failed its own self-test on the stale anchor
`readme-quotes-a-stale-speedup` before any human could have signed off on a sweep that would have
planted nothing. Anchors over regenerated numbers have to be refreshed in the same commit as the
numbers, which is now part of the release checklist below.

## 5. What the next release cycle owes this one

1. The falsification sweep has to be re-run on a clean tree after committing, because the harness
   refuses to start on a dirty target — the 19 declared defects are then proved against the revision
   the tag will name, not against a work in progress.
2. The falsification sweep ran on the committed tree afterwards, twice — once on `dcc9eaa` and once on
   `e5daedc`, the head whose provenance defect the reproduction test had caught on the runner. Both
   printed `19/19 planted defects were rejected by their guard.` with `git status` empty afterwards. Its
   own list is what those sentences claim, and four of its anchors had to be refreshed during the phase
   because the prose they key on moved under them.

3. `docs/limitations.md` #78 says `stress.run_scenario` is unchanged. If a future phase does ship a
   re-struck variant, #78, matrix row 12 and row 18, `docs/findings.md` §7 and this report all have to
   move together, and the refusal in the artifact (`order_not_changed`) has to be re-derived rather
   than edited.
4. The crossing prediction is gated only inside `|delta| <= 0.05`. Extending that radius needs the
   fourth-order terms, not a wider tolerance; if someone widens the tolerance instead, the gate stops
   meaning what it says.
