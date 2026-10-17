# Phase 50 — a document's claims are censused, and the census finds the conjunction (#101 narrowed, #104 opened)

Date: 2026-10-17. Debt items: `docs/limitations.md` #101 amended with a measured precision, #102 amended
on the side that closed it, #104 opened from the same enumeration.

## 1. Completed

* **`test_the_claims_a_document_prints_are_a_census_and_not_a_sample`.** Every distinct phrase the claim
  rule prints in an inventoried document is either gold (a count a reader confirmed in the document) or a
  named phantom, both lists frozen, and every inventoried document must be censused or pending -- so a
  document cannot leave the queue by being deleted from it. `README.md` is the first census: **24 real
  counts and 1 phantom out of 25**, precision **24/25**, and after the fix below **24 of 24**.
* **The phantom, and what it was made of.** `0.588 and orders`, from "the order-five-to-four piece ratio
  spans 0.057 to 0.588 **and orders** the outcome no better than its predecessor did". `_CLAIM_TAIL`
  allows one word between a numeral and its noun, and `[A-Za-z]+\.?` cannot tell *and* from *rolling*, so
  a clause-final decimal was glued to the verb that follows its conjunction and read as a count of 0.588
  orders.
* **The fix is a class, not a word.** `_CLOSED_CLASS_MODIFIERS` holds **38** conjunctions, prepositions,
  determiners and relativizers, and the slot now refuses them. Property 8 of the extractor self-test puts
  **each member** into the sentence that first showed the defect and requires the shipped rule to read
  nothing there and the reopened rule to read a claim, so no member is decoration; measured across the
  corpus, reopening the slot gains **exactly 2** of the **200** distinct phrases the open slot prints --
  the README one and `10% between runs` in the matrix, which the census had not reached because that
  document is pending.
* **`_CITATION_STOPWORDS` measured and refused.** The tidy refactor was to reuse the row-citation stop
  list (117 words). It contains `further`, `over`, `up`, `down`, `used`, `many`, `like`, and running the
  borrow over the corpus deletes exactly **1** real claim: `four further books` in the report. So the
  block is its own list, `further` stays out of it, and one plant registers the borrow to prove the
  guard objects.
* **#104 opened** on the failure the census cannot express: `60 markets spread` (report) attaches a
  correct count to the wrong noun because both words are on the noun list. 1 phrase in 198, and a
  phantom list files it as gold.
* **4 plants (119 -> 123)**: reopen the slot; borrow a stop word from the citation list; recast a gold
  count as a phrase the document does not print; delete a document from the pending queue.
* **The cascade**: register 103 -> 104, test pair 525/456 -> 526/457 in twelve spellings and eight plant
  anchors, sweep annotation 119/119 -> 123/123, `fifty report files` -> `fifty-one`, and the report
  re-typeset.

## 2. Assumptions this rests on

* A census denominates over **distinct phrases**, not over occurrences: `525 pytest tests` printed twice
  in one document is one entry. The choice is stated because the first probe of this phase counted
  occurrences (231 across the five documents) and the numbers quoted here are the set counts (200 with
  the slot open, 198 closed); a rate that does not name its counting basis is not the same measurement
  twice over.
* A phrase is real when it asserts how many of a countable thing the sentence is about, read in context.
  Durations, tolerances, versions and multipliers are not; the census's gold list is those readings, and
  the guard re-derives the hits from the documents on every run so a reworded sentence reddens it rather
  than scoring stale gold.
* The block's class is drawn at words that cannot modify a noun from in front *in this register*.
  Direction words (`up`, `down`, `over`, `under`) and `further` are left out because they do classify
  counted nouns here; that is a judgement about English, and the two measurements above are what make it
  checkable rather than merely stated.

## 3. Files changed

`tests/python/test_artifact_metadata.py` (the census guard, `_census_hits`, `_PRECISION_CENSUS`,
`_PRECISION_PENDING`, `_CLOSED_CLASS_MODIFIERS`, `_MODIFIER_BLOCK`, property 8),
`scripts/mutation_plants.py` (4 plants and the anchors that track the counts), `docs/limitations.md`
(#101 and #102 amended, #104 opened, #63's pair), `README.md`, `docs/reproducibility.md`,
`docs/interview_defense.md`, `docs/validation_matrix.md`, `docs/release_notes_v1.3.0.md`,
`docs/release_notes_v1.4.0.md`, `docs/project_scope.md` §9, `paper/technical_report.tex` with its rebuilt
PDF and `build.json`, and this report.

## 4. What the phase learned, including about its own first design

* **Both instruments that already existed said "no phantoms", and they were both right and both
  useless.** The targeted corpus (Phase 48) scores units chosen to contain known blind spots and
  returned 0; the systematic 25-unit sample (Phase 49) returned 0 because it extracted exactly one hit
  and the README sentence that holds the defect was not one of the 25 drawn. A design built to answer
  "what does the rule miss" has, in the same question, a denominator for "what should it not have said"
  only by accident. The census is not a better sample -- it is a different question, and enumerating it
  is affordable at the size of one document.
* **The rule's generosity was priced twice before it was priced on this side.** #100 measured the
  lookbehind and #102 measured the slot's reach on recall; the slot's *precision* is what this phase
  paid for, and the defect it found is the cheapest kind: one character class, `[A-Za-z]+`, standing in
  for "an adjective" in a language that does not mark adjectives.
* **The tempting refactor had to be measured, not argued.** Reusing `_CITATION_STOPWORDS` reads as
  deduplication and would have deleted a real count. The counterexample was found by reading the list
  before borrowing it (`further` is a stop word for citation purposes and a classifier for this rule) and
  confirmed by running the borrow over the corpus. Recording the number -- 1 claim lost -- is what keeps
  the next reader from "tidying" it back, which is why the plant exists.
* **A probe counted the wrong thing first.** The first measurement of this phase counted matches rather
  than distinct phrases, because the extractor returns a list; the census guard compares sets, so the
  two denominators differ by 33 across the corpus. Caught by writing the ratio before publishing it and
  asking what its denominator counts.
* **The misattribution is not a bigger phantom.** `60 markets spread` has the right number and the wrong
  noun, so no gold/phantom dichotomy can file it; #104 registers it with the measurement and the reason
  the obvious fix (refuse a modifier that is itself counted) is keyed on a list every phase grows.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 194 files already formatted, measured on the `git archive` export of `d40c282` (finding 81's rule), and the runner reports the same 194 |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --test-dir build/dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | Evidence is intact -- the report bundle moved, no artifact re-frozen |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 457 tests collected |
| Python | `.venv/bin/python -m pytest -q` | 526 passed in 153.65s |
| Falsification, full sweep | `.venv/bin/python scripts/run_mutation_suite.py --all` on `d40c282` | 123/123 planted defects were rejected by their guard, tree clean afterwards, exit 0 |
| CI on the pushed head | run on `d40c282`, read from each job's own log | lint `All checks passed!`, `194 files already formatted`, mypy `Success: no issues found in 23 source files`; C++ and Python `100% tests passed out of 204` and `456 passed, 5 skipped in 132.96s`, which is #91's reconciliation against the 457 the probe collects (`456 + 5 = 457 + 4 = 461`); benchmark `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 258.6s total` |

## 6. Numerical validation

| Figure | Value | Producer |
|---|---|---|
| README hits, slot open / closed | 25 / 24 | `_census_hits("README.md")` under both tails |
| README precision before the fix | 24/25 | the census guard's own gold and phantom lists |
| Distinct phrases, five documents, open / closed | 200 / 198 | the same rule over `_ROW_CITATION_DOCUMENTS` |
| Phantoms the block refuses | `0.588 and orders`, `10% between runs` | property 8's reopened-slot set |
| Block size / citation stop list size | 38 / 117 | `len(_CLOSED_CLASS_MODIFIERS)`, `len(_CITATION_STOPWORDS)` |
| Claims a `_CITATION_STOPWORDS` borrow deletes | 1 (`four further books`) | measured by running the borrowed rule |
| Pending backlog | 19 / 40 / 31 / 84 | `_census_hits` per document |
| Misattributed phrases | 1 of 198 (`60 markets spread`) | read from the closed-rule hits |
| Register entries | 103 -> 104 | `_numbered_limitation_entries()` |
| Plants | 119 -> 123 | `run_mutation_suite.py --list` |
| pytest with / without `oracles` | 526 / 457 | the runner, and `measure_offline_collection.py` |
| Phase report files | 50 -> 51 | `docs/phase_reports/*.md` |

## 7. Remaining limitations

* The census covers one of five documents. The pending 198-24 = 174 phrases are unjudged, and the
  misattribution shape shows that judging them will need a category the gold/phantom split does not
  have.
* `docs/limitations.md` #101's own half -- a declaration being a hand-written reason whose number
  nothing compares with a producer -- is untouched: the census classifies hits, not exemptions.
* The class boundary is English, not logic. `up`, `down`, `over`, `under` and `further` are excluded
  from the block on a reading of this register, and a sentence that uses one as a relational word
  (rather than a classifier) would still produce a phantom.
* Nothing measures the rule's precision on a document whose claims are mostly cited artifacts (the
  report, 84 phrases), because the census has not been done there.

## 8. Technical debt registered here

* **#104** (new): a count attached to the wrong noun where two counted nouns are adjacent, 1 phrase of
  198, with the candidate fix measured and refused because the exclusion would key on `_REPORT_NOUNS`.
  The census needs a third category -- *real count, wrong object* -- before the report is censused.
* **#101** stays open on its declaration half, and its precision half is now measured per document,
  which makes the remaining work enumerated (174 phrases) rather than conceptual.
* **#103**'s static half is untouched by this phase.

## 9. The gate

Nothing here is a release. The phase's claim is a measurement with its denominator named: on the first
document censused, the claim rule prints 25 phrases, 24 of them about a quantity, and the 25th was a
conjunction doing the work of an adjective. The fix is a 38-word class, each member shown to be able to
fail, and the two phantoms it refuses are pinned by name so that reopening the slot costs a red guard
instead of a stale document.
