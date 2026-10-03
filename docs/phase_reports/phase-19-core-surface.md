# Phase 19 — the whole core surface, not the part an attribute happens to mark

Date: 2026-10-03. Predecessor: Phase 18 (`phase-18-five-book-radius.md`), whose §8 item 1 is this debt
item; the finding it closes is Phase 17's own published caveat (limitation #80). Repository version is
unchanged (`1.6.0`), the tag still names `b4e4bea`, and Phase 18's CI run (`37098769856`) is the last
verified revision: `389 passed, 5 skipped` offline on the runner, `suite: 17/17 executed and passed`,
three jobs `success`.

## 1. Completed

1. **Seventeen namespace-scope declarations that carried no `[[nodiscard]]` now carry it**, across four
   headers: the nine statistics primitives (`sum_compensated`, `mean`, `sample_variance`,
   `sample_stddev`, `quantile`, `quantile_linear`, `mean_of_largest_sorted`, `autocorrelation`,
   `standard_error_of_mean`), the two version accessors, the three normal functions, and the three
   covariance estimators. Each returns a value that is the point of calling it, which is exactly what the
   attribute means; nothing was marked to satisfy a test.
2. **The extension-surface claim was re-keyed from the attribute to the surface.** Phase 17's population
   was "what carries `[[nodiscard]]`", so a function written without the attribute fell outside the claim
   and had to be inventoried. Phase 19's population is every namespace-scope function declaration in
   `cpp/include/quantrisk/**/*.hpp` -- 109 declarations, 101 distinct names -- each of which must be
   registered in the bindings or disclaimed at its own declaration, and each of which must also carry the
   attribute. The residual is asserted empty rather than listed.
3. **`stats::quantile_linear` got the disclaimer Phase 17 said it needed**, at its declaration and in the
   checked form: `// python: internal -- ...`, naming the reason the guard can test -- it takes data the
   caller already sorted ascending, an invariant no Python caller can be verified for.
4. **A latent defect in the Phase 17 scanner is fixed** (audit finding 48). Its statement-boundary walk
   stopped at the previous newline, so a declaration whose attribute sat on the line *above* the name --
   the shape `black_scholes.hpp` uses for its wrapped signatures -- was reported as unmarked: a direct
   call returned 23 names where the register published one. The test stayed correct only because an
   unrelated filter dropped anything the attribute scan or the bindings already covered. The walk now
   stops at `;`, `}`, `{` or a blank line, and the parser's own test pins all five shapes.
5. **One new guard, two new plants.**
   `test_the_documents_that_count_the_core_surface_count_it_correctly` reads 109/101/25 out of the scan
   and compares them with the limitation register, the interview answer and its citation row -- three
   places that had carried 92/85/24 with no owner. Two plants back it: strip `[[nodiscard]]` from
   `normal_cdf` (bound, so only the uniformity guard can fire) and edit the declaration count in the
   register. The sweep is at **29 planted defects**.
6. **Documents the change moves:** limitation #80 rewritten from "the claim is keyed on an attribute that
   is not universal" to the three things that genuinely stay outside it, `docs/integrity_audit.md`
   finding 48 and the Phase 19 addendum, `docs/interview_defense.md` Q27 and its citation row, and the
   test-count figures in four documents (460 with the oracles, 391 in the offline lane).

## 2. Mathematical assumptions

None. This phase changes no numerical code path: `[[nodiscard]]` is a compile-time attribute on
declarations, and the only semantic decision in it is that a numerical core's returned value is always
the point of calling. Every published artifact is byte-identical to the ones frozen in Phase 18, and no
regeneration was run -- the C++ rebuild and the 201 CTest cases are the proof that nothing moved.

## 3. Files changed

| path | change |
|---|---|
| `cpp/include/quantrisk/core/statistics.hpp` | nine declarations marked; `quantile_linear` disclaimed at its declaration |
| `cpp/include/quantrisk/core/version.hpp` | `version`, `build_metadata` marked |
| `cpp/include/quantrisk/math/normal.hpp` | PDF, CDF and inverse CDF marked |
| `cpp/include/quantrisk/portfolio/covariance.hpp` | the three estimators marked, re-wrapped by clang-format |
| `tests/python/test_extension_surface_parity.py` | `_statement_head` added; `_unattributed_declarations` → `_unmarked_declarations` returning rows with markers; `_core_surface` re-keyed to the union of both scans; the inventory test replaced by the uniformity test; the surface-count guard added |
| `scripts/run_mutation_suite.py` | two plants (unmarked declaration, stale surface count) and four count anchors refreshed |
| `docs/limitations.md` | #80 rewritten; the test counts it states |
| `docs/integrity_audit.md` | finding 48 and the Phase 19 addendum |
| `docs/interview_defense.md` | Q27, its citation row, the test counts |
| `docs/reproducibility.md`, `paper/technical_report.tex` | the two test-count figures |

## 4. Tests executed

`uv run cmake --build --preset dev` rebuilt core, tests, reference tool and the Python extension after
the header edits; `uv run ctest --preset dev` ran the C++ suite; `uv run pytest tests/python -q` ran the
Python suite; the parity file was also run alone, and a hand-planted defect proved the new guard before
it was trusted.

## 5. Exact test results

```text
uv run pytest tests/python -q                     460 passed in 46.57s
uv run pytest tests/python/test_extension_surface_parity.py -q   14 passed in 0.45s
uv run ctest --preset dev                         100% tests passed out of 201 (8.42 s)
uv run ruff check .                               All checks passed!
uv run ruff format --check .                      139 files already formatted
uv run mypy python/quantrisk                      Success: no issues found in 23 source files
uv run clang-format --dry-run -Werror <29 headers> exit 0
uv run python scripts/run_mutation_suite.py --list   29 plants declared
```

The surface, read by the guard itself: 109 namespace-scope declarations in 29 headers, 101 distinct
names, 25 disclaimed by `// python:` markers, 0 left without `[[nodiscard]]`.

The uniformity guard's negative control, run by hand because the sweep refuses a dirty tree: removing
`[[nodiscard]]` from `Real normal_cdf(Real x);` made
`test_no_namespace_scope_declaration_is_left_unmarked` fail while the other 12 tests in the file stayed
green -- the two guards are independent, which is the point of having both -- and the header was restored
byte-identically (`shasum` `1aae1f87ec3a02be` on both sides, `cmp` silent) and the file passed again.

## 6. Numerical validation

No number in the repository moved. Validation here means the claim about the *API* is now
- measured from the tree rather than from a list, with the population derived by scanning
  `cpp/include/quantrisk/**/*.hpp` in two directions (attribute-forward and statement-backward) that
  must agree;
- falsifiable in both of its new halves, by the two plants and the hand control above;
- and stated where a reader meets it, with three documents' counts policed against the scan rather than
  against each other.

## 7. Remaining limitations

Limitation #80 as rewritten. In short: class members are not namespace-scope entry points and are not
covered; a disclaimer's *reason* is prose, so the guard verifies the route it names and not whether the
justification still holds; and a function declared only inside a `.cpp` is invisible to a header scan --
finding 43's blind spot one file type over, not a closed one. Nothing in this phase claims otherwise.

## 8. Technical debt

1. **Order five.** Phase 17 measured the fifth-order term to be above the subtraction noise, and Phase 18
   found the expansion is not descending at all on the short-dated book (fourth-order piece 3.9× the
   third), so the next order answers a question the published chain now has. This is the largest remaining
   item: six mixed fifth partials in the core, their own difference-scheme validation, an experiment, a
   note, and the release that would carry them.
2. **Post-tag accounting.** `v1.6.0`'s assets are frozen; this tree carries a corrected radius claim, a
   re-frozen 85-artifact manifest, and headers newer than the tag. If a `v1.7.0` is cut it must state the
   radius per book, and its release note should carry the surface counts the way #80 now does.
3. **Unowned counts still in prose.** The `ruff format --check` file count and the "four documents and
   eleven guards" style self-descriptions in release notes are not read by any guard. Phase 18 and Phase
   19 closed five such counts between them; the residue is small and each one needs the same treatment:
   pick the owner, extend a guard, plant the defect.
4. **Two scanners, one population.** The surface is now the union of an attribute-forward and a
   statement-backward scan. They agree on today's tree -- the guard asserts the counts -- and a future
   declaration shape could make them disagree in either direction. A real C++ parser would retire that
   risk rather than test around it.

## 9. Gate

**Not a release.** Version stays `1.6.0`, tag stays `b4e4bea`. No artifact, suite roll-up or manifest
changed, so nothing is re-frozen: the manifest committed at `2e8142a` still hashes the evidence this tree
produces, and `verify_evidence_manifest.py` reports `0 CHANGED / 0 MISSING / 0 unlisted`. The falsification
sweep runs on a committed tree because it refuses a dirty target, so its verdict is recorded one commit
later, naming the revision it ran on -- the ordering `CONTRIBUTING.md` §4 and Phase 17 §9 both describe.
