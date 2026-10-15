# Phase 42 — The validation matrix joins the spelled inventory, and the first false claim it found

Date: 2026-10-15. Predecessor: Phase 41 (`8713a59`, recorded in `ee374d3`, CI run `38686832039` green on
the former). No version was bumped; `v1.8.0` remains the latest release.

## 1. Completed

`docs/validation_matrix.md` is the fourth and last markdown document opted into `_SPELLED_DOCUMENTS`. Its
**21** spelled-only claims resolve to **5 owned, 5 declared and 11 cited -- none unowned**, and reading
them found the rollout's first claim that was not merely unsupervised but **wrong**.

| Claim | Spelling | Verdict and producer |
|---|---|---|
| twenty-six rows | `It has twenty-six rows rather than twelve` | owned -- the table's own row labels, already counted by the guard that reads README's restatement |
| five rows (caveat) | `## Five rows that need the prose to be honest` | owned -- the paragraphs under that heading, counted by the guard that already compared them |
| four rays | `2.0 on four rays, 3.0 on a pure-spot ray` | owned -- `two_factor_bound.json` → `asymptotics`, 4 keys |
| four markets | `nested differentiation at 4.6e-15 on four markets` | owned -- the derivation script's part-B loop, read as syntax: 4 tuples |
| six fields | `the six fields reached by difference routes` | owned -- `FIELDS` in the derivation script; **corrected prose**, see §4 |
| five partials | `taken across five fourth-order partials` | owned -- the distinct call arguments in the route table `PARENTS` |
| two rows | `a component validated two ways gets two rows` | declared -- the table's layout rule |
| two vanna routes (twice) | `Schwarz makes the two vanna routes…`, `the two vanna routes agree to 1.4e-7` | declared -- routes of a derivative, which no artifact enumerates |
| two factors | `and nothing second-order in two factors` | declared -- the axes a missing oracle would have spanned |
| two routes | `the two routes to vanna share no formula` | declared -- a property of the derivation, recorded by its phase report |

The other eleven pass as cited: their row names the frozen artifact the sentence is about. Phase 41
promoted two such claims to owned where a producer was already read; these eleven were left alone because
each already answers to a guard outside the inventory (the book counts, the ray counts and the identity
grids of rows 19 to 23), and promoting a citation to an owner is worth the diff only when the guard is new.

## 2. Assumptions this rests on

* The two producers that live in Python source are read with `ast`, not with a substring search. Finding
  82 -- a `--quick` count that included the file doing the counting -- is the reason: a pattern that names
  a literal also appears in the file that names it, and a count of the corpus counts the counter.
* The spelled rollout's remaining step is the report, and that is now pinned structurally: property 5 of
  the extractor self-test asserts `_SPELLED_DOCUMENTS == _MARKDOWN_INVENTORY` and reads the *report
  guard's own call keywords* to prove it does not yet pass `spelled=True`. When Phase 43 switches the
  report on, that assertion is retired deliberately rather than discovered by a failure.
* No experiment was re-run and no artifact re-frozen. The producers this phase reads are frozen files and
  committed source; `run_benchmark_suite.py` was not invoked, and `verify_evidence_manifest.py` is the
  instrument that says the bytes did not move.
* `twenty-six` is the largest numeral `SPELLED_NUMBERS` resolves (#97). The row-count owner therefore
  sits exactly on the ceiling: a twenty-seventh row makes the guard raise `KeyError` rather than report a
  disagreement. That is #97's live case, and it is why this phase's plant moves the count *down*.

## 3. Files changed

* `tests/python/test_artifact_metadata.py` — the matrix joins `_SPELLED_DOCUMENTS`; one new guard
  (`test_documents_that_count_the_studies_grids_agree_with_their_producers`) with four `ast` helpers; six
  owned patterns registered (two of them spellings of patterns their guards already searched); five
  declared anchors; property 5's staging assertion rewritten for the completed markdown half.
* `scripts/mutation_plants.py` — 6 plants added (86 → 92); the staged-rollout plant's anchor moved from the
  document tuple to the report's extractor call.
* `docs/validation_matrix.md` — row 21's field sentence corrected to name both numbers; 102-entry register
  and 518/449 test spellings.
* `README.md`, `docs/reproducibility.md`, `docs/interview_defense.md`, `docs/limitations.md`,
  `docs/project_scope.md`, `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md`,
  `paper/technical_report.tex` (+ `.pdf`, `.build.json`) — the counts this phase moved.
* `docs/integrity_audit.md` — findings 82's continuation and 83.

## 4. What the phase learned, including about its own first design

* **The first false spelled claim, and its number came from the other side of the relation.** Row 21
  said "the five fields reached by difference routes". The module defines **six** fields and reads
  **five** distinct fourth-order partials; the sentence attached the smaller quantity to the noun in
  front of it. No digit twin exists anywhere in the corpus -- nothing prints `6 fields` -- so this was
  invisible to every gate until the spelled reader reached the document that carries it (finding 83).
  The corrected prose states both numbers and each is compared with the structure it names, which is the
  shape the register has been asking for: a claim with two quantities in it needs two producers.
* **`ast` where a substring would have counted itself.** `_literal_list` had to learn annotated
  assignments on its second run: `PARENTS: tuple[...] = (...)` is an `AnnAssign`, and the first version
  reported that a file which had not changed "is no longer a module-level list or tuple literal". A false
  statement about the tree, produced by the instrument. The failure was loud because the helper raises by
  name rather than returning zero, which is the same property that made #101's decorative-exemption check
  useful: an absence has to announce itself.
* **The recall half of the rule is now measured too (#102).** Allowing two modifiers between numeral and
  noun instead of one adds 14 phrases across the corpus, of which at most three are claims about an
  inventoried quantity (`ten five-point slope routes` is one). Widening would convert the guard into a
  queue of sentences whose honest answer is "this is not a quantity" -- #101's declaration pile at larger
  scale -- so the rule was left as it is and the limit was registered instead. The consequence is stated
  plainly: #95's "45 remain" bounds what the rule can find, not what the documents assert.
* **Two counts had producers and no spelling.** `twenty-six rows` and the caveat heading's `Five rows`
  were each compared on every gate by a guard that reads the words, and each was invisible to the
  inventory because the owned list keys on a pattern the extractor can match. They are registered now, so
  the inventory credits the same fact its guard already checked -- which is what #98 says should not be
  possible (credit is by source-presence), and what makes it safe here: the pattern is the guard's literal,
  verbatim-checked, not a new claim about the document.
* **The staging plant had to move, and moving it was the point.** Phase 41's plant widened
  `_SPELLED_DOCUMENTS` to the whole markdown corpus. After this phase that replacement is the shipped
  state, so the plant would have been a no-op; the anchor is now the report's own extractor call. A
  falsification plant whose target becomes true is not a broken plant, it is a phase that finished a step.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | measured on the committed tree in the record commit (finding 81's rule) |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --preset dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | Evidence is intact -- zero artifacts re-frozen |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 449 tests collected |
| Python | `.venv/bin/python -m pytest -q` | 518 passed |
| Falsification, full sweep | recorded in the next commit, on the sha it ran on | pending |
| CI on the pushed head | recorded in the next commit, from the runner's own logs | pending |

## 6. Numerical validation

No measurement is published and none moved.

* **92** declared plants, read from the list by the guard that compares it with the sheet's annotation.
* **518 / 449** -- produced by the runner's own pytest step and by the offline probe, on this tree. #91
  relates them across the two vantages: `passed + skipped = collected + 4`, because four oracle-gated
  modules skip as items rather than as collected records. On the local full run that is `518 + 0`; on the
  runner it is read from its log and recorded in §5's CI row, which is the only place the rule can be
  checked rather than asserted.
* **102** register entries; **6** new owned patterns, **5** new declared anchors, each checked stale and
  decorative by the inventory guard.
* **45** spelled-only claims remain, all in `paper/technical_report.tex`.
* **Zero** artifacts re-frozen; the report was re-typeset because its `.tex` counts moved, and its record
  is now bundle `db744d6395a5`, PDF `6536e07c69db`.

## 7. Remaining limitations

* **#97 is now live.** The matrix's row count is owned through the spelled table whose ceiling is
  `twenty-six`, and the table has exactly twenty-six rows. The next row turns the guard into a `KeyError`
  instead of a disagreement.
* **The recall instrument #102 asks for does not exist.** Nothing enumerates the quantities the rule
  fails to see, so the rollout's "complete" state means complete-within-the-rule.
* **#98 and #99 stand.** Registering two spellings of patterns their guards already searched is exactly
  the credit-by-source-presence mechanism #98 describes; this phase relies on it rather than fixing it.
* **The cited eleven** are unverified as to number. Their rows are about artifacts the sentence names, and
  the numbers themselves are checked only where a guard outside the inventory reads them.

## 8. Technical debt registered here

| Entry | What it records | Why it is a limitation and not a defect |
|---|---|---|
| #95 (amended) | the matrix's 21 classified 5/5/11; 45 remain in the report | the rollout is staged by review, and the report is the last step |
| #102 (opened) | the tail rule's one-modifier allowance, measured both ways: 14 phrases gained, at most 3 claims | widening trades a working guard for a queue of non-claims; the honest residue is that recall is bounded by the rule |
| finding 82 (Phase 41) extended | a `ast.Assign`-only helper reported a changed file unchanged | the helper now reads annotated assignments, and the failure it prevented was its own message |
| finding 83 | the false `five fields` claim, its denominator from the parents, and the `ast` choice that made counting it safe | recorded because the class -- a sentence with two quantities and one noun -- is not detectable by any rule |

## 9. The gate

Closed when the 92-plant sweep runs on the committed tree with no line at any other status and the tree
clean afterwards; when CI's three jobs are read from their own logs on the pushed revision and #91 is
checked on the runner's numbers; when the register, the audit, the scope table, the matrix and the sheet
agree on the plant count, the register size and the test pair, each from its own producer; and when the
corrected field sentence is shown to be load-bearing by plants on *both* of its numbers. A record checks
the revision it names: the sweep and CI rows land in the commit after this file, on the sha the runner
built.
