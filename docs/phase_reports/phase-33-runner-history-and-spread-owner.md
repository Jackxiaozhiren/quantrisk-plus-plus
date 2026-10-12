# Phase 33 — the runner's missing history, and the percentage that had no denominator

Date: 2026-10-12. Debt closed: the first half of `docs/limitations.md` #92 (the speedup-band spread
percentages had no owner), and the premise Phase 32 accepted without testing -- that the runner cannot
carry the history three guards read. The user's question that opened the phase was whether the remaining
debt was work I could finish or work only they could; the answer for these two items was "neither: it
needed a measurement", and the measurement said the checkout was the whole obstacle.

## 1. Completed

1. **The pytest lane now fetches history and tags.** `.github/workflows/ci.yml`'s `build-and-test` job
   runs `actions/checkout@v7` with `fetch-depth: 0` and `fetch-tags: true`. Three guards that had always
   skipped there -- `test_the_report_lists_the_release_tags_the_repository_carries`,
   `test_the_release_date_the_citation_declares_is_the_tag_that_cut_it`, and
   `test_the_documented_speedup_ranges_match_the_committed_history` -- are now checked on the runner.
   Measured on a throwaway branch (`ci-prove-full-history`, dispatched through `workflow_dispatch`), the
   lane went from `429 passed, 8 skipped in 202.38s` at `466e564` to `432 passed, 5 skipped in 149.42s`
   on identical code: the three guards moved from skip to pass and the other five skips are the four
   oracle-import module skips plus `latexmk is not installed`. The checkout step cost 1.29 s at depth 1
   and 2.17 s at depth 0, for a 7.93 MiB pack over 180 commits.
2. **The spread percentages gained a producer and a formula.**
   `SPEEDUP_SPREADS = {"python": 32.6, "numpy": 20.8}` is pinned the way the bands are, and
   `test_the_documented_spread_percentages_are_the_committed_historys` recomputes `(max - min) / min` to
   one decimal over every committed reading and compares it with the pin: 32.572 and 20.778 on the 22
   readings now in history. Choosing the denominator was the work -- `(max - min) / max` gives 24.569 and
   17.203, `(max - min) / mean` gives 30.327 and 19.374, and neither is what any document prints.
   `docs/reproducibility.md` now states the formula next to the figures, because a number that can be
   formed several ways has to say which.
3. **Four living documents are compared as band-plus-percentage blocks.** `SPREAD_CLAIMS` pairs each with
   its own wording -- `docs/reproducibility.md` (two blocks), `docs/limitations.md`, the `v1.8.0` note and
   `paper/technical_report.tex` (two blocks) -- and the guard builds the string from the pinned values, so
   a document cannot keep the ratio pair and quietly change the percentage beside it.
4. **Two plants (59 -> 61).** `living-document-quotes-a-superseded-spread` puts the superseded 11.9 % into
   the living sentence -- a true number from the wrong revision, which is finding 55's mechanism.
   `pinned-spread-constant-disagrees-with-the-history` edits the guard's own pinned constant, because that
   is the only defect the derivation guard can be handed.
   `test_the_performance_guards_are_not_vacuous` gained the in-memory control for both.
5. **Eight living sentences that stated the old premise were corrected** -- six in
   `tests/python/test_artifact_metadata.py`, two in `docs/limitations.md` -- and the skip messages now name
   the clone ("a clone fetched without tags carries none") instead of the infrastructure, so a future
   change to the workflow cannot silently invalidate them.
6. **The cascade the two new guards caused was driven by the guards**: pytest 502 -> 504 and the offline
   collection 433 -> 435 across four documents and four plant anchors, and the rehearsal sheet's sweep
   annotation 59/59 -> 61/61 in the same commit as the list.

## 2. Assumptions this rests on

- The committed history of the speed artifact is the population its documented spreads describe -- the
  same assumption the pinned bands already make, and the same one `test_the_documented_speedup_ranges_match_the_committed_history`
  checks wherever a clone carries history.
- A runner fetching full history is safe and affordable here. The repository is public, the pack is
  measured rather than assumed, and no guard's input set includes anything a fetch could inject: the
  guards read `refs/tags` and blob contents of the checked-out revision's own ancestry.
- `pull_request` events still get the same lane, so an outside contribution is checked against real tags.
  This project has no other contributors, which is a fact about the repository rather than a protection.
- The five remaining CI skips are the expected five. This is read from the job log each time it is
  claimed, not derived from the count.

## 3. Files changed

| File | Change |
|---|---|
| `.github/workflows/ci.yml` | `fetch-depth: 0` and `fetch-tags: true` on the pytest lane, with the measured cost recorded in the comment |
| `tests/python/test_artifact_metadata.py` | `SPEEDUP_SPREADS`, `SPREAD_CLAIMS`, `_spread_fields()`, two new guards, the vacuity control extended, six premise sentences rewritten |
| `scripts/run_mutation_suite.py` | two plants; four count anchors and the sweep-count anchor re-keyed |
| `docs/reproducibility.md` | the denominator stated; the two living spread blocks; test totals synced |
| `docs/limitations.md` | #92 amended with its dated closure, #77 amended with the runner measurement, #90's premise put in the past tense, living totals synced |
| `docs/integrity_audit.md` | Phase 33 addendum, finding 65 |
| `docs/project_scope.md` | §9 Phase 33 row, refresh date 2026-10-12 |
| `docs/interview_defense.md` | state line to Phases 0–33, totals and sweep annotation synced |
| `paper/technical_report.tex`, `paper/technical_report.pdf`, `paper/technical_report.build.json` | totals synced, then the render rebuilt by the producer |

## 4. What the phase learned, including about its own first design

- **An accepted premise is an unrun measurement.** Phase 32 wrote "the runner does not have history" into a
  register entry and a guard docstring and shipped it. Both were true of the *default* checkout, not of the
  workflow, and the cost of finding out was one dispatched run. A limitation that names infrastructure should
  carry the number that measured it, because infrastructure is a line in a file someone can change.
- **The percentage could not be policed until its formula was chosen.** Writing a guard that recomputed
  "the spread" would have been a free choice disguised as a check: three defensible denominators exist and
  only one matches the printed figures. The phase's real content was deciding `(max - min) / min` and
  publishing that choice where a reader meets the number.
- **Block comparison is the only shape that survives a file holding both a living and a dated figure.**
  `docs/limitations.md` carries the current spreads and a superseded 11.9 % several entries apart, so a
  presence test on `32.6` would be satisfied by either. The templates name the sentence, not the digit --
  the lesson finding 61 recorded for `# 481 tests here`, applied here before it could recur.
- **One plant had to edit the guard itself, and that says something about the guard.** A derivation check
  compares a literal in its own file with a git object; nothing in the corpus can make it red except the
  literal or the history. So its falsification is a plant against the test file, which the harness supports
  (it refuses a dirty target and restores by hash) but which is a weaker proof than a document-side plant:
  it shows the comparison runs, not that the pinned value is right. The in-memory control in
  `test_the_performance_guards_are_not_vacuous` is the stronger half -- it recomputes from an extended
  sample and requires the number to move.
- **A new sentence created a new instance of the gap being described.** Naming the alternative denominators
  put 24.6 % and 30.3 % into `docs/reproducibility.md`, and the inventory guard's `<number> <countable noun>`
  matcher reads neither -- measured as zero claims from that sentence -- because its noun list has no `%`,
  `spread`, `reading` or `re-freezing`. #92 was amended, not deleted.

## 5. Exact test results

| Gate | Command | Result |
|---|---|---|
| Python | `uv run pytest tests/python -q` | `504 passed in 161.43s` on the final tree |
| Offline lane | `uv run python scripts/measure_offline_collection.py` | `collected: 435`, `module_skips: 4`, `collection_errors: 0` |
| Docs + harness lanes | `uv run pytest tests/python/test_artifact_metadata.py tests/python/test_mutation_suite.py -q` | 63 passed; the two new guards passed against the pinned values, and the rewrap sweep after writing them reflowed the docstrings with a word-level proof |
| C++ | `uv run ctest --preset dev` | 100% tests passed out of 204 |
| Catch2 | `./build/dev/quantrisk_tests` | All tests passed (548368 assertions in 203 test cases) |
| Identity | `uv run quantrisk validate` | 7/7 checks passed |
| Lint | `uv run ruff check .` / `uv run ruff format --check .` | All checks passed! / 171 files already formatted. The same command on a `git archive HEAD` export printed 170 for `d054418` and 171 for `466e564`, so the number is quoted as a walk of whatever directory it ran in and not as a count of tracked files — and the two readings differing by one for a commit that added no Python file is exactly why no guard compares them (finding 62(d)) |
| Types | `uv run mypy python/quantrisk` | Success: no issues found in 23 source files |
| Producer | `uv run python scripts/build_report.py` | 6 sources, bundle `ff7f77a19d85…`, PDF `08de2f963bc1…`, 1,005,780 bytes; run after the prose settled |
| Render text | `pdftotext paper/technical_report.pdf` | carries `504 pytest tests with the validation`, `435 collected without them`, `92 recorded limitations`, `32.6` and `20.8` |
| Evidence | `uv run python scripts/verify_evidence_manifest.py` | 0 missing, 0 unlisted — Evidence is intact |
| Anchor census | one-pass enumeration of every declared plant against the file it names | 61 declared, 59 file-backed (two create their own probe file), 0 missing or non-unique |
| CI premise, before | run `38149012780` on `466e564`, job `114498318376` | `429 passed, 8 skipped in 202.38s`, checkout step 1.29 s (03:07:05 baseline 14:53:33.155 → 14:53:34.446), three skips naming the missing history |
| CI premise, after | run `38198483490` on branch `ci-prove-full-history`, job `114646369537` | `432 passed, 5 skipped in 149.42s`, checkout 03:07:05.235 → 03:07:07.407 = 2.17 s, and the only remaining `test_artifact_metadata.py` skip is `1821: latexmk is not installed` |
| Falsification, full sweep | `uv run python scripts/run_mutation_suite.py` on the committed tree, logged to `build/mutation-sweep-33.log` | pending — the harness refuses a dirty target, so the verdict belongs to the commit this report lands in and is recorded in the follow-up commit |
| CI on the pushed record | `gh api …/commits/<sha>/check-runs` after the push | pending — not yet run at the time of writing |

## 6. Numerical validation

One new published quantity per kind, and both derived rather than typed: the spread percentages
`(max - min) / min` = 32.572 % and 20.778 % over the 22 committed readings, printed as 32.6 % and 20.8 %,
with the rejected alternatives measured too (24.569 / 17.203 against the maximum, 30.327 / 19.374 against
the mean). The CI figures are counts of test outcomes read from job logs, named by run id. The freeze did
not move: no file under `benchmarks/**/results` or `experiments/*/results` was regenerated, and
`verify_evidence_manifest.py` reports the freeze intact, which is what makes "it did not move" a check
rather than an assertion.

## 7. Remaining limitations

- **The inventory guard's vocabulary is still the open half of #92.** Percentages, spreads, readings and
  re-freezings in the report and the markdown documents are matched by nothing, so an unowned count in that
  class stays invisible. This phase produced a measured instance of its own blind spot (§4, §d).
- **The new guards run on the runner, but only because a workflow line says so.** If a future change
  restores a depth-limited checkout, the guards skip again and the lane still passes -- the CI summary is
  now load-bearing evidence for them, so the five-skip reading is worth checking whenever the workflow is
  touched. Nothing in the repository asserts "the pytest lane fetches history"; a guard for that is
  unwritten.
- **A dated record quoting a stale skip message is still quoting it.** `docs/release_notes_v1.4.0.md` and
  this audit's finding 49 entry print the old `(CI uses actions/checkout at depth 1)` wording verbatim; they
  are records of their revisions and were left alone, so the string no longer exists in the code.
- **Spread percentages remain unpinned at the document level for superseded pairs.** `v1.4.0`'s 11.9 % sits
  beside a stale band and is exempt as a dated record, which is the same declaration the band census
  already relies on; nothing checks that a *new* stale percentage is dated rather than accidental.
- **`docs/model_cards/**` and `docs/analysis/**` are policed for band pairs, and for nothing else.** The
  spread blocks list four documents; a model card quoting a spread would need adding.

## 8. Technical debt registered here

- Nothing asserted in CI checks that the pytest lane fetches history and tags, so the three guards can be
  silently vacated by an infrastructure edit. A cheap guard exists: read `.github/workflows/ci.yml`,
  require the `fetch-depth: 0` input on the job whose steps run `pytest tests/python`, and give it a plant.
- `build/rewrap_docstrings.py` stayed scratch (gitignored) but did the docstring work for the second phase
  running, with its word-level and AST proofs; promoting it now has an observed user.
- The `date-released`, release-tag and band-history guards now depend on tag *names* matching versions. A
  tag like `release-1.9` would read as "no tag for this version" and skip rather than fail; the skip names
  the version it looked for, so the log is the evidence, but no guard asserts the tag-naming rule itself.

## 9. The gate

The runner now sees what the guards read, and the numbers beside the documented bands are recomputed
instead of copied: 32.6 % and 20.8 % are the committed history's own arithmetic under a denominator the
reproducibility document states. What this phase proved about itself is in §4 -- a premise carried for two
releases was one dispatched run away from being falsified, and the sentence that fixed it created a fresh
example of the one gap it did not close, which #92 now records with the measurement attached.
