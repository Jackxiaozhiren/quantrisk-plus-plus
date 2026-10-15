# Phase 41 — The rehearsal sheet joins the spelled inventory, and a producer that counted itself

Date: 2026-10-15. Predecessor: Phase 40 (`99c69bb`, recorded in `87dd109`). No version was bumped;
`v1.8.0` remains the latest release.

## 1. Completed

`docs/interview_defense.md` is the third document opted into `_SPELLED_DOCUMENTS`, so the claim
inventory now reads counts written in words as well as digits in the rehearsal sheet, and all **14** of
its spelled-only claims answer for themselves: **9 owned, 5 declared, none left unowned or resting on a
citation alone.** The owners are the substance of the phase.

| Claim | Spelling in the sheet | Producer it now answers to |
|---|---|---|
| four rays | `along four rays scaled down` | `fourth_order_crossing_map.json` → `headline.rays_number_of` = 4 |
| twelve columns | `across the twelve columns, the cubic finds` | the same artifact → `headline.columns_swept` = 12 |
| five books (twice) | `the same quantity on five books`, `The five books were chosen to span` | `second_book_crossing_map.json` → `headline.books_measured` = 5 |
| two radii | `that book's two radii come back at 0.05 and 0.15` | the count of `radii_*` tables in that artifact's headline, **and** the quoted pair against `published_control_cubic` / `published_control_quartic` |
| twenty-two re-freezings | `across the twenty-two re-freezings` | the committed speed-reading history, the same sample the reproducibility note counts three times over |
| one test | `one test re-executes the published benchmark script` | the suite itself: modules whose spawn line carries both the interpreter and the flag |
| two routes | `Two equivalent routes to the same statement` | the `Xxx route:` labels inside the paragraph that makes the claim |
| two cases | `The two cases I would be pushed on` | the `(1)` / `(2)` markers inside that paragraph |

The radii sentence is read twice on purpose. A stale **value** sitting in a sentence about how many
values there are would otherwise pass as prose, so the guard compares `0.05 and 0.15` with the control
block the artifact publishes; the rehearsal sheet had been quoting them correctly and nothing had ever
checked it.

## 2. Assumptions this rests on

* `ruff format --check .`, `ruff check` and `mypy` are run on this tree and the report is re-typeset
  from the committed source, so no figure in §5 is inherited from an earlier revision -- the rule
  `docs/integrity_audit.md` finding 81 wrote into `CONTRIBUTING.md` §4 step 4.
* The crossing artifacts are read as frozen files, not re-run. `run_benchmark_suite.py` was not invoked:
  a docs-and-guards phase has no reason to resample the volatile fields, and the manifest is the
  instrument that says the bytes are the ones the published bands were measured from.
* Paragraph scope is the denominator for the inline enumerations. `(1)` and `(2)` recur in a
  neighbouring answer on the same page, so a document-wide marker count would have credited the sheet's
  claim from a paragraph two answers down.
* The register-size count keeps cascading into `docs/release_notes_v1.3.0.md` and
  `docs/release_notes_v1.4.0.md` because `test_documents_that_count_the_limitations_agree_with_the_file`
  says those two are living documents -- a pinned decision recorded there, not an oversight this phase
  re-litigates.

## 3. Files changed

* `tests/python/test_artifact_metadata.py` — `_SPELLED_DOCUMENTS` gains the sheet; one new guard
  (`test_documents_that_count_the_crossing_maps_shape_agree_with_the_frozen_artifacts`); two inline
  enumerations and a spawn-shape count added to the existing enumeration and Python-test-count guards;
  the committed-reading loop gains the sheet's fourth spelling; 10 owned patterns and 5 declared
  anchors; the inventory guard's own docstring corrected (it said "these two documents" of a
  four-document corpus).
* `scripts/mutation_plants.py` — 8 plants added (78 → 86), and the staged-rollout plant's anchor re-keyed
  onto the three-document tuple.
* `docs/interview_defense.md`, `docs/reproducibility.md`, `docs/validation_matrix.md`, `README.md`,
  `docs/limitations.md`, `docs/project_scope.md`, `docs/release_notes_v1.3.0.md`,
  `docs/release_notes_v1.4.0.md`, `paper/technical_report.tex` (+ `.pdf`, `.build.json`) — the counts
  this phase moved: 516 → 517, 447 → 448, 78/78 → 86/86, register 100 → 101, and the sheet's state line.
* `docs/integrity_audit.md` — finding 82.

## 4. What the phase learned, including about its own first design

* **A count over the test corpus is not blind to the file doing the counting.** The first version of the
  `--quick` producer asked whether each test module's text contains the flag; it found two modules, the
  second being the guard itself, which had to write the flag down to search for it. The sheet's claim was
  refuted by a string literal in the file refuting it, and the failure looked like stale prose. The
  predicate is now the spawn shape -- a line carrying both the interpreter and the flag -- which is also
  what makes the sentence mean something. This is #94's trap reached from the other side: there, a plant
  could not anchor on the line holding the plant list; here, a counter could not exclude its own source.
  Recorded as finding 82.
* **The spelled rule's precision on prose is measurable and is not one.** Of the 14 claims, 5 have no
  producer in this tree, and they are five different shapes: a count of *families* where the core declares
  three functions (`the two tests specified here` -- `kupiec_pof_test`, plus Christoffersen's independence
  and conditional-coverage tests), a count of rejected designs, a property of one `ctest -R` run, a
  sign-symmetric pair quoted beside a column count that is owned elsewhere, and a matrix row repeating the
  sheet's own answer. The digit rule never had this at this rate: `2 tests` is always a count. That is
  #101, and it is a design question rather than a defect because the alternative -- a rule that decides
  which English numerals are quantities -- was measured and rejected: a determiner before the numeral
  looked like the marker, but `The two cases I would be pushed on` and `the two tests specified here` are
  both determiner-led and both real claims, so that rule would have excused two of the nine owners.
* **A declaration is only as good as the sentence beside it, and the plant proves it.** The new plant
  `declaration-anchor-for-the-backtest-families-stops-matching` moves the words `specified here` to
  `specified below` without touching the list. Nothing about the claim changes; the anchor goes stale,
  and the inventory guard reports an exemption that no longer excuses anything. That is the same check
  that caught #100's two phantom exemptions in Phase 40, now shown to fire on a *real* claim's wording.
* **Citation is weaker than ownership, and four claims were only cited.** `the same quantity on five
  books`, `that book's two radii`, `twenty-two re-freezings` and `two cases` passed the inventory before
  this phase because their paragraph names a frozen artifact -- which proves the paragraph is about
  something measurable, not that its number is right. They are owned now.
* **The staging assertion did its job on arrival.** `test_the_claim_extractor_reads_percentages_and_refuses_labels`
  property 5 requires `_SPELLED_DOCUMENTS` to stay a *strict* subset of the inventoried corpus, so
  bringing in the sheet is allowed and switching the rule on corpus-wide is not: that is the plant
  `spelled-rule-widened-to-a-document-nobody-classified`, whose anchor this phase had to re-key because
  the tuple it points at is the thing being widened.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 183 files already formatted. The walk includes markdown, so this report is itself one of the files counted -- finding 81's mechanism, caught the same phase that wrote the rule about it |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --preset dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | Evidence is intact -- zero artifacts re-frozen |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 448 tests collected |
| Python | `.venv/bin/python -m pytest -q` | 517 passed in 275.09s |
| Docs + harness lanes | `.venv/bin/python -m pytest tests/python/test_artifact_metadata.py tests/python/test_mutation_suite.py -q` | 71 passed (62 docs, 9 harness) |
| Anchor census | `test_every_declared_mutation_names_one_unique_anchor_and_a_guard_that_exists` | 86 declared plants, every anchor unique in its file, every guard present in its named file |
| Falsification, full sweep | recorded in the next commit, on the sha the sweep ran on | pending |
| CI on the pushed head | recorded in the next commit, from the runner's own logs | pending |

## 6. Numerical validation

No measurement is published and none moved.

* **86** declared plants, from the list itself; the sheet's annotation and the guard that compares them
  are the two ends of that claim.
* **517 / 448** -- the Python counts with and without the `oracles` extra, produced by the runner and by
  the offline probe rather than retyped. The #91 reconciliation still holds offline: four oracle-gated
  modules are skipped *items*, so `448 + 4 = 517` in this environment.
* **101** register entries; **10** new owned patterns and **5** new declared anchors, each checked for
  staleness and for usefulness by the inventory guard.
* **66** spelled-only claims remain -- 45 in `paper/technical_report.tex`, 21 in
  `docs/validation_matrix.md` -- re-measured through the shipped extractor, not carried over from prose.
* **Zero** artifacts re-frozen, **zero** benchmarks re-run, bands and their 22 committed readings
  unchanged; `paper/technical_report.pdf` was re-typeset because the `.tex` counts moved, and its record
  is now bundle `5f9719efba27`, PDF `40d1456aa27a`.

## 7. Remaining limitations

* **#101's five declarations are hand-judged**, and the judgement is recorded per claim rather than
  derived. A reader who disagrees with one can turn it into an owner, but nothing forces the question
  again.
* **#95's remaining 66** claims sit in two documents with different shapes: the matrix is tables whose
  numerals mostly already have owners in the row they cite, and the report is prose with LaTeX spellings
  the sheet has not exercised.
* **#97, #98 and #99 stand as registered** -- the numeral table's ceiling at twenty-six, ownership
  credited by source-presence, and row citations checked for existence rather than meaning. Finding 82
  makes #98 sharper rather than closing it: the credit mechanism cannot see that a pattern's *predicate*
  reaches its own source.
* The inline-enumeration reader handles `Xxx route:` labels and `(1) / (2)` markers because those are
  what this document uses. A third inline shape elsewhere will need its own marker pattern; the guard
  fails loudly (it asserts the paragraph named *some* items) rather than scoring zero items as agreement.

## 8. Technical debt registered here

| Entry | What it records | Why it is a limitation and not a defect |
|---|---|---|
| #95 (amended) | the sheet's 14 classified 9/5, 66 remaining, and what each remaining group will need | the rollout is deliberate; a first run over 108 claims would be a diff nobody can review |
| #101 (opened) | the spelled rule's measured precision on prose, the five declaration shapes, and the determiner rule that was tried and rejected | the rule cannot tell a quantity from a narrative count; only a producer can, and the producer is named per claim |
| finding 82 | a producer over the test corpus counting the file doing the counting | fixed here by the spawn-shape predicate; recorded because the mechanism generalises to every grep-shaped owner |

## 9. The gate

Closed when the 86-plant sweep runs on the committed tree with no line at any other status and the tree
clean afterwards; when CI's three jobs are read from their own logs on the pushed revision and the
offline reconciliation is checked on the runner's numbers; when the register, the audit, the scope table
and the sheet agree on the plant count and the spelled totals, each from its own producer; and when each
of the nine new owner patterns is shown to be load-bearing by a plant that changes the sentence it reads
rather than the code that reads it. A record checks the revision it names: the sweep and CI rows land in
the commit after this file, on the sha the runner built.
