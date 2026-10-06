# Phase 25 — the two numbers CTest cannot see

Date: 2026-10-06. Predecessor: Phase 24 (`phase-24-dependencies-and-build-products.md`), whose §8 item 1
is this debt item; the residue itself is named by Phase 20's finding 49 and re-named by Phase 21's §8. No
`PROJECT_SPEC.md` phase number: it closes a registered technical-debt entry. Repository version is
unchanged (`1.7.0`), the tag still names `79d536a`, and nothing here is claimed to be inside that release.

## 1. Completed

1. **The assertion total has a producer.**
   `test_documents_that_count_the_cpp_assertions_count_the_binarys_own` runs the compiled Catch2 binary
   with `--verbosity quiet` and reads its summary line — measured here:
   `All tests passed (548368 assertions in 203 test cases)`. Finding 49's reason the number had no owner was
   structural: CTest enumerates tests, not assertions, so every C++ guard that existed was blind to it.
2. **The case total has two producers, and they must agree.** The same test counts `TEST_CASE(` blocks at
   the start of a line across `tests/cpp/*.cpp` — measured: 203 — and requires that to equal the binary's
   case count. That is what turns "the documents quote the compiled suite" into "the documents quote the
   compiled suite, and the compiled suite is the source they describe".
3. **Five quotations across four documents now hang off those producers**: `README.md`,
   `docs/reproducibility.md`, `docs/interview_defense.md` (the state line and the Q&A row, which phrase it
   differently enough that no shared pattern reached it — finding 49's shape again), and
   `paper/technical_report.tex`, whose `548{,}368` LaTeX comma had to be normalised before `int()` could
   read it. The CTest entry count is deliberately *not* asserted here:
   `test_documents_that_count_the_cpp_tests_agree_with_the_build` already owns 204, and one number is
   allowed exactly one owner.
4. **A plant for the document arm** — `readme-quotes-a-stale-assertion-total`, declared list 39 → 40 —
   and a live falsification of the source arm, which cannot be planted without recompiling: appending one
   `TEST_CASE("probe", "[probe]") {}` in memory moved the count 203 → 204, which is the disagreement the
   guard compares against the binary.
5. **The offline Python count moved with the new test and was measured rather than waited for.** The
   oracle-free probe (a subprocess in which `QuantLib`, `pypfopt`, `cvxpy`, `sklearn` and `statsmodels` are
   unimportable) collects 414 here against 483 with the oracles; the same probe reproduced the runner's own
   413 at the previous revision, which is why this phase quotes it and says so in `docs/reproducibility.md`.
   Phase 26 turns that probe into a guard.
6. **Records moved:** finding 57, `docs/limitations.md` #85 (and the 84 → 85 count in every living document
   that repeats it, plus the plant anchor over the README phrasing), the `482 → 483` and `413 → 414` test
   counts, `docs/project_scope.md` §9, `docs/interview_defense.md`'s state line, and the rebuilt
   `paper/technical_report.pdf`.

## 2. Mathematical assumptions

None. No numerics changed: the C++ sources, the bindings, the artifacts and the manifest are untouched,
which the verifier confirms. The two quantities under ownership are structural counts of test cases and of
executed assertions. The one assumption worth stating is that an assertion *count* is deterministic given
fixed seeds and fixed grids — it is a count of statements executed, not of values compared, so a
platform's `libm` cannot move it. If a future test made a check conditional on a floating-point outcome,
that assumption breaks and this guard would show it as a cross-platform disagreement rather than hide it.

## 3. Files changed

| File | Change |
| --- | --- |
| `tests/python/test_artifact_metadata.py` | one guard plus `_cpp_test_binary` and `_source_test_case_count` |
| `scripts/run_mutation_suite.py` | one plant declared (39 → 40), three anchors re-keyed |
| `docs/integrity_audit.md` | Phase 25 addendum, finding 57 |
| `docs/limitations.md` | #85, and the two counts it quotes |
| `docs/project_scope.md` | §9 Phase 25 row |
| `docs/interview_defense.md` | state line, plant annotation, three test-count spots, limitation count |
| `README.md`, `docs/reproducibility.md`, `docs/validation_matrix.md`, `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md` | limitation count; reproducibility also the offline pair and its instrument |
| `paper/technical_report.tex`, `paper/technical_report.pdf` | both counts, PDF rebuilt from the corrected source |

## 4. Tests executed, and the one that had to be re-thought

1. **First draft asserted the CTest entry count too**, in the same guard, because the documents quote
   "204 C++ tests, 548,368 assertions" as one phrase. That made a second owner of a number the C++ guard
   already owns — the exact condition finding 49 exists to prevent — so the entry count was dropped from
   the assertions and the pattern narrowed to the assertion/case pair. The documents' `204` remains owned
   where it was owned before.
2. **The LaTeX comma was parsed the wrong way round**, which produced a `ValueError` rather than a
   failure: `.replace(",", "")` first turns `548{,}368` into `548{}368`, so the `{,}` pattern no longer
   matches. Order matters, and the test now normalises `{,}` before `,`.
3. **The tex pattern was written against memory of the sentence rather than the file**, matched nothing,
   and the guard reported that plainly (`paper/technical_report.tex no longer states the C++ assertion
   total as ...`). Reading the source line, the case count sits *after* the phrase `assertions in`, on the
   following physical line; the pattern now matches the text as it is.

## 5. Exact test results

```
uv run pytest tests/python -q                                 483 passed in 150.96s (0:02:30)
./build/dev/quantrisk_tests --verbosity quiet                 All tests passed (548368 assertions in 203 test cases)
grep -c '^\s*TEST_CASE(' tests/cpp/*.cpp                      203 across the sources
uv run ruff check .                                           All checks passed!
uv run ruff format --check .                                  153 files already formatted
uv run python scripts/verify_evidence_manifest.py             Evidence is intact. (94 OK, 0 CHANGED, 0 MISSING)
latexmk -pdf -g technical_report.tex                          Output written on technical_report.pdf (44 pages, 1003992 bytes)
```

Falsification, before the commit:

```
document arm  README 548,368 -> 548,000, guard red at test_artifact_metadata.py:1037,
              README restored to f7df438e01206b8a30c515b9efd67ceddc6ac8080cb3e2d5d73a8f26fdecf770
source arm    one TEST_CASE appended in memory: counter 203 -> 204 (binary unchanged at 203)
probe         oracle-free collection 414 items, oracle-on collection 483, difference 69
```

The open item is this commit's CI verdict and the runner's reading of 414 (§9).

## 6. Numerical validation

Nothing measured by the engine changed, and the frozen manifest verifies with zero regenerated files. What
was validated is a correspondence: five quoted totals against two producers of those totals, with the
producers also compared with each other. The guard's own premise — that a binary present only after a build
is a legitimate source of truth in the lane that runs tests — is stated in #85 rather than assumed, and the
skip path is the one place the guard cannot bite.

## 7. Remaining limitations

`docs/limitations.md` #85. Two edges: the guard skips where nothing has been built, so a source-only
checkout can still carry a wrong assertion total, and the assertion count is assumed platform-stable because
it counts executed statements rather than compared values — a future conditional check would break that
assumption, and the cross-check against the source count is what would surface it.

## 8. Technical debt

1. **The offline probe is not yet a guard** (Phase 26's whole subject): this phase used it as an
   instrument, and it has now reproduced a runner-reported count once. It must also fail the way the runner
   fails — four skips, not four collection errors — before it can police anything.
2. **The assertion/case totals are guarded for quotations, not for the count itself moving legitimately.**
   Adding a `TEST_CASE` requires a rebuild to keep the guard green, which is correct but means the guard
   cannot run in a lane without a build directory.
3. Carried forward: the release body versus `docs/release_notes_v1.7.0.md` (finding 56(e)), the PDF's
   missing freshness owner (finding 56(d)), `sympy`-style runtime cost of two 60-digit checks in one lane
   (Phase 24 §8 item 4), and the sixth book for the radius.

## 9. Gate

Commands and verdicts are §5's, taken from the working tree before the commit that carries this report; the
C++ suite was not re-run because no C++ file moved, and the manifest verifier reports the freeze untouched
rather than re-frozen. The falsification sweep runs on the committed tree after it exists and its verdict,
this head's CI run and the runner's offline reading are appended in the commit that follows.

**Verdicts, read after the commit they describe.** `413e199`'s CI run 37411531441 is `success` on all
three jobs — `Format and static checks`, `Configure, build, C++ tests, Python tests`, and `Benchmark suite
against live oracles` — with the suite lane's own line `suite: 18/18 executed and passed`. Its offline lane
printed `413 passed, 5 skipped in 143.13s`, and the count guard that ran there accepted the published 414,
which is the runner's own confirmation of this phase's offline figure: 414 collected, four module-level skip
records on top, 418 outcomes. The falsification sweep ran on `413e199`, the head that carries the phase, with `git
status` empty before and after, and printed `40/40 planted defects were rejected by their guard.` — the
fortieth being `readme-quotes-a-stale-assertion-total`, which fired on the README quotation as declared.
This record commit has no sweep line of its own yet: the harness refuses a tree whose mutation targets
differ from HEAD, and the next phase's work is uncommitted here, so its verdict is appended in the
accounting commit that follows. The head
carrying this paragraph is a record commit, so its own run is read the same way as the two above:
`gh api repos/Jackxiaozhiren/quantrisk-plus-plus/commits/$(git rev-parse HEAD)/check-runs`.
