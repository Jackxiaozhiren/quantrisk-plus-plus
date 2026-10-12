# Phase 33 — the runner's missing history, and the percentage that had no denominator

Date: 2026-10-12. Debt closed: the first half of `docs/limitations.md` #92 (the speedup-band spread
percentages had no owner), and the premise Phase 32 accepted without testing -- that the runner cannot
carry the history three guards read. The user's question that opened the phase was whether the remaining
debt was work I could finish or work only they could; the answer for these two items was "neither: it
needed a measurement", and the measurement said the checkout was the whole obstacle. The phase then found
a third thing by itself: its own falsification harness printed a false verdict on a clean tree, which is
§1 items 7 and 8 and `docs/limitations.md` #93.

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
6. **The cascade the two new guards caused was driven by the guards**: pytest 502 -> 505 and the offline
   collection 433 -> 436 across four documents and five plant anchors, and the rehearsal sheet's sweep
   annotation 59/59 -> 61/61 in the same commit as the list. The register grew to 93 as the phase's own
   tooling defect was recorded (§1 item 8), and every count above came from a guard naming the sites.
7. **The first sweep on the phase commit printed `60/61` and was wrong about its own tree.**
   `pinned-spread-constant-disagrees-with-the-history` — the plant that edits the guard's own constant —
   came back `tree-did-not-recover` while `git status --porcelain` was empty. Both readings were true: the
   file on disk carried the restored `SPEEDUP_SPREADS = {"python": 32.6, …}`, and the re-run still behaved
   as if it carried `99.9`. CPython validates a `.pyc` on source *size and whole-second mtime*; the plant's
   edit changes two characters of identical length, the restore lands inside the same second, and the
   bytecode written while the defect was in place is still considered current. The cache file's 13:19
   timestamp is the mutated run's, and deleting `__pycache__` made the same node pass.
8. **Two attempts were needed, and the second one's failure is the sharper fact.** The first fix gave each
   *sweep* its own `PYTHONPYCACHEPREFIX`. The sweep re-run printed `60/61` again — same plant, same status,
   clean tree — while that plant run alone printed `caught`. That pair of results located the window
   precisely: a plant's mutated run and its restored re-run are two invocations of one sweep, so a prefix
   shared across the sweep is shared across exactly the two steps that must not see each other's bytecode.
   `Harness.next_environment()` therefore allocates a fresh prefix per invocation, and the isolation test
   gained a third assertion that two consecutive environments differ — the property the first fix lacked.
   Clearing `__pycache__` between steps was the third option and stayed unchosen: it has to be remembered
   everywhere, and it discards the caches that make an ordinary test run fast.

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
| `scripts/run_mutation_suite.py` | two plants; five count anchors and the sweep-count anchor re-keyed; `isolation_environment()` plus `Harness.next_environment()`, which gives every guard subprocess its own `PYTHONPYCACHEPREFIX` |
| `tests/python/test_mutation_suite.py` | the stale-bytecode regression test, with the negative control that must fire before the isolation is credited |
| `docs/reproducibility.md` | the denominator stated; the two living spread blocks; test totals synced |
| `docs/limitations.md` | #92 amended with its dated closure, #77 amended with the runner measurement, #90's premise put in the past tense, #93 opened for the cache boundary, living totals and the register count synced |
| `docs/integrity_audit.md` | Phase 33 addenda, findings 65 and 66 |
| `docs/project_scope.md` | §9 Phase 33 row, refresh date 2026-10-12 |
| `docs/interview_defense.md` | state line to Phases 0–33, totals, register count and sweep annotation synced |
| `README.md`, `docs/validation_matrix.md`, `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md`, `docs/release_notes_v1.6.0.md` | the counts the guards moved |
| `paper/technical_report.tex`, `paper/technical_report.pdf`, `paper/technical_report.build.json` | totals and register count synced, then the render rebuilt by the producer |

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
- **A plant that edits a Python file teaches something about the interpreter, not only the guard.** The
  phase's own plant against `SPEEDUP_SPREADS` produced a false `60/61` because CPython's cache key is
  (size, whole-second mtime) and the edit-and-restore kept both. Two lessons followed. The harness now
  isolates bytecode per invocation rather than trusting a restore, and a *verdict* is not the same
  object as a
  *tree*: `git status` clean plus a red guard is not a contradiction until the input set of the red run is
  known. The first sweep's log is kept at `build/mutation-sweep-33.log` precisely because it is evidence
  about the tool rather than about the code.
- **Writing the isolation test needed its negative control first.** A test that only asserts
  "the isolated run reads the fresh value" would pass on any interpreter that never cached — so it
  reproduces the stale read in an un-isolated subprocess and *requires* that to be stale, then credits the
  fix. Without that order the test would have been a green light rather than a guard.
- **The count cascade moved twice as fast as the phase produced guards** — 502→505 and 433→436 with two
  guards and one test, and each step was named by a guard rather than by grep. Five plant anchors went
  stale in the second cascade; the one-pass enumeration over all 61 declared plants is what made the count
  of them a fact instead of an impression.

- **A new sentence created a new instance of the gap being described.** Naming the alternative denominators
  put 24.6 % and 30.3 % into `docs/reproducibility.md`, and the inventory guard's `<number> <countable noun>`
  matcher reads neither -- measured as zero claims from that sentence -- because its noun list has no `%`,
  `spread`, `reading` or `re-freezing`. #92 was amended, not deleted.

## 5. Exact test results

| Gate | Command | Result |
|---|---|---|
| Python | `uv run pytest tests/python -q` | `505 passed in 101.00s` on the final tree |
| Offline lane | `uv run python scripts/measure_offline_collection.py` | `collected: 436`, `module_skips: 4`, `collection_errors: 0` |
| Docs + harness lanes | `uv run pytest tests/python/test_artifact_metadata.py tests/python/test_mutation_suite.py -q` | 64 passed; the two new spread guards, the extended vacuity control and the new bytecode-isolation test are all in that count |
| C++ | `uv run ctest --preset dev` | 100% tests passed out of 204 |
| Catch2 | `./build/dev/quantrisk_tests` | All tests passed (548368 assertions in 203 test cases) |
| Identity | `uv run quantrisk validate` | 7/7 checks passed |
| Lint | `uv run ruff check .` / `uv run ruff format --check .` | All checks passed! / 172 files already formatted. The same command printed 171 earlier in this phase and 170 on a `git archive HEAD` export of `d054418`, so the number is quoted as a walk of whatever directory it ran in and not as a count of tracked files — and the two readings differing by one for a commit that added no Python file is exactly why no guard compares them (finding 62(d)) |
| Types | `uv run mypy python/quantrisk` | Success: no issues found in 23 source files |
| Producer | `uv run python scripts/build_report.py` | 6 sources, bundle `5a462aecbfdb…`, PDF `ee7179da3d03…`, 1,005,777 bytes; run last, after the prose settled, and it reddened the binding twice on its own before that order was followed |
| Render text | `pdftotext paper/technical_report.pdf` | carries `505 pytest tests with the validation`, `436 collected without them`, `93 recorded limitations` and `register contains 93 numbered entries` |
| Evidence | `uv run python scripts/verify_evidence_manifest.py` | 0 missing, 0 unlisted — Evidence is intact |
| Anchor census | one-pass enumeration of every declared plant against the file it names | 61 declared, 59 file-backed (two create their own probe file), 0 missing or non-unique |
| CI premise, before | run `38149012780` on `466e564`, job `114498318376` | `429 passed, 8 skipped in 202.38s`, checkout step 1.29 s (03:07:05 baseline 14:53:33.155 → 14:53:34.446), three skips naming the missing history |
| CI premise, after | run `38198483490` on branch `ci-prove-full-history`, job `114646369537` | `432 passed, 5 skipped in 149.42s`, checkout 03:07:05.235 → 03:07:07.407 = 2.17 s, and the only remaining `test_artifact_metadata.py` skip is `1821: latexmk is not installed` |
| Falsification, sweep one | `uv run python scripts/run_mutation_suite.py` on `c9f7732`, logged to `build/mutation-sweep-33.log` | `60/61` with `FAIL tree-did-not-recover pinned-spread-constant-disagrees-with-the-history` while `git status --porcelain` was empty — the false verdict of §1 item 7, kept because it is evidence about the tool |
| Falsification, sweep two | same command after the per-sweep prefix, logged to `build/mutation-sweep-33b.log` | `60/61` again, identical status — the insufficient fix of §1 item 8, and the measurement that located the window. The same plant run alone in that state printed `caught 1/1`, which is what made the two-runs-of-one-sweep reading unavoidable |
| Falsification, sweep three | same command on the final commit, logged to `build/mutation-sweep-33c.log` | pending — the harness refuses a dirty target, so this verdict belongs to the commit that carries it and is recorded in the follow-up commit, not here |
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

- **A check that reads Python source is a check on whichever copy the interpreter chose.** The harness now
  isolates its own bytecode, but the mechanism is CPython's: a same-length edit restored inside one clock
  second is invisible to the cache key (size, whole-second mtime), so any *other* route that puts bytes back
  that way -- a restore from a backup, two processes touching one tree, a different tool's plant step -- can
  still make a clean file read as its previous contents. `docs/limitations.md` #93 records that boundary,
  and the caches themselves are gitignored, so no committed artifact and no CI lane can compare against them.
- **The isolation test cannot be planted, only controlled.** No plant removes an environment variable from
  the harness's own subprocesses, so its falsifiability rests on the in-test negative control (the stale
  read that must happen before the isolation is credited). If CPython's validation scheme changed, that
  control would fail loudly rather than quietly -- which is the reason it is written first.
- **The inventory guard's vocabulary is still the open half of #92.** Percentages, spreads, readings and
  re-freezings in the report and the markdown documents are matched by nothing, so an unowned count in that
  class stays invisible. This phase produced a measured instance of its own blind spot (§4).
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

- Nothing asserts that the pytest lane keeps fetching history and tags, so the three guards can be silently
  vacated by an infrastructure edit and the lane would still report success with three more skips. A cheap
  guard exists: read `.github/workflows/ci.yml`, require `fetch-depth: 0` on the job whose steps run
  `pytest tests/python`, and give it a plant -- the same shape as
  `test_a_command_line_that_counts_plants_counts_the_declared_ones`, which reads a config file rather than
  a document.
- The cache isolation is policed by a control, not by a plant: no plant can remove an environment variable
  from the harness's own subprocesses. A phase that wants the stronger proof would need the harness to
  report the environment it used in its log, and a guard to require the prefix to be present -- registered
  here rather than built, because the in-test control already fails loudly if the isolation is dropped.
- `build/rewrap_docstrings.py` stayed scratch (gitignored) but did the docstring work for a second phase
  running, with its word-level and AST proofs; promoting it now has an observed user.

## 9. The gate

Two premises died in this phase, one of them about the tool. The repository had accepted for two releases
that the runner cannot carry history, and the measurement was one dispatched workflow away: the pytest lane
now fetches tags and full history for 0.88 s, and three guards that had been reporting a skip became
checked there. The speedup bands' percentages stopped being transcribed for the same reason -- the formula
needed choosing, `(max - min) / min`, and the alternatives needed measuring before the pinned figures could
be defended rather than repeated. And the sweep that should have certified the work instead reported a
false escape on a clean tree, which turned out to be CPython's cache key rather than the code's, and left
the harness with per-invocation bytecode isolation — after one fix that was not enough — a test whose
first assertion is that the bug is real, and
#93 saying plainly where that boundary does not reach.
