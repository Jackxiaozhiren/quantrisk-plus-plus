# Phase 44 — The numeral table generates to ninety-nine, and the ceiling's fallback retires

Date: 2026-10-15. Predecessor: Phase 43 (`d5b51d4`, recorded in `5d01391`, CI run `38750480153` green on
the former). No version was bumped; `v1.8.0` remains the latest release.

## 1. Completed

`SPELLED_NUMBERS` is generated from its parts -- ones, teens, tens, and the hyphenated compounds the
corpus's own style uses -- and covers **every value below one hundred**, replacing the flat dict that
stopped at twenty-six. That closes **#97**, the register's oldest open entry, and retires the digits
fallback its first real consumer took: the artifact index's report-file count is spelled again
(`forty-five report files`, the directory's count as of this phase), owned by the directory listing
through the same pattern that owned the digits.

The closure is demonstrated rather than asserted. Property 7 of the extractor self-test proves the
generation two-sided -- a twenty-seven-count sentence becomes a claim, and withholding one compound key
silences exactly that claim -- and a new plant moves the validation matrix's row count to `twenty-seven`,
which now **disagrees** instead of raising the `KeyError` #97 predicted.

| What moved | Was | Is |
|---|---|---|
| the numeral table | a flat dict, 26 entries, ending at the matrix's own row count | generated, 100 entries, every compound below one hundred |
| the report's file count | `44 report files` (the Phase 43 fallback) | `forty-four report files`, owned spelled |
| a count above twenty-six | invisible to the inventory; `KeyError` to a guard | a claim, and a disagreement |
| plants | 99 | 102, including the hyphen-removal plant that proves the compounds are the generation's product |

## 2. Assumptions this rests on

* The compounds are hyphenated because that is this corpus's spelling (`twenty-two committed files`,
  `twenty-six rows`); a document that writes `twenty two` unhyphenated is still invisible, and that is
  #102's modifier question, not this entry's.
* The generation's keys are exactly the values 0--99 with no gaps and no duplicates, checked by the
  self-test; `one hundred` itself is out of range and a count that large goes back to digits, which is
  the same fallback but now bounded and named rather than discovered mid-phase.
* The longer alternation in the spelled rule is ordered longest-first, so `sixty-six` cannot be read as
  `six`; the existing property 5 checks that ordering for `twenty-two` and property 7 extends the idea to
  the compounds.
* No measurement was published and none moved; the report was re-typeset because one word in it changed.

## 3. Files changed

* `tests/python/test_artifact_metadata.py` — the generated table (three part-tuples and a dict
  comprehension replace 27 literal lines); property 7 added to the extractor self-test; the report-file
  owner pattern widened to the spelled form.
* `scripts/mutation_plants.py` — 3 plants (99 → 102); the sheet's annotation and its own anchor carry the
  count.
* `paper/technical_report.tex` (+ `.pdf`, `.build.json`) — `forty-four report files`; re-typeset.
* `docs/interview_defense.md` — the sweep annotation.
* `docs/limitations.md` — #97 amended closed.

## 4. What the phase learned, including about its own first design

* **The ceiling's exposure was future blindness, not present loss.** Before writing the generation, the
  phase measured what extending the table to one hundred would add to today's corpus: **zero claims**.
  #97's subject was therefore never a stale number sitting unread -- it was the guarantee that the *next*
  count above twenty-six would be invisible, which Phase 43 then hit in its own report sentence. A debt
  entry whose measured present cost is zero and whose future cost is certain is exactly the kind the
  register exists to hold open.
* **The fallback was a promise, and the phase kept it.** Finding 84(b) recorded that the report-file
  count went to digits because `forty-three` could not be owned spelled; #97's amendment predicted the
  next prose count above twenty-six would have to choose again. Generating the table instead of
  re-deciding per count converts a recurring judgement call into a structure, which is the difference
  between the two entries: #97 was a design question, and the design answer removed the question.
* **The plant had to be chosen against the failure mode it proves.** The obvious generation plant --
  truncating the tens range -- would have removed only compounds nobody's control withholds, and the
  guard would have stayed green. Dropping the hyphen from the compound f-string removes exactly the keys
  property 7 withholds, so the sentence stops being two claims and the failure names the mechanism. This
  is the `guard-stayed-green` lesson in miniature: a plant must mutate the thing the assertion reads.
* **Three appends to the plant list broke the file the same way three times.** Each string-surgery append
  consumed the previous entry's closing `),` and left the tuple unterminated; each was caught by import
  failing, and the third was fixed without re-diagnosing because the mechanism was already known. The
  durable rule is now in memory: append to a data tuple with an anchored edit on the final `)`, not by
  trimming the tail.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 186 files already formatted on the `fff4e03` export and in CI -- see the note below the table |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --preset dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | Evidence is intact -- zero artifacts re-frozen |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 450 tests collected |
| Python | `.venv/bin/python -m pytest -q` | 519 passed |
| Falsification, full sweep | `.venv/bin/python scripts/run_mutation_suite.py` on `fff4e03`, logged to `build/mutation-sweep-44.log` | **`102/102 planted defects were rejected by their guard.`** -- 102 rows carrying that status and none other; tree clean afterwards. The ceiling-closure plants are among them: `matrix-row-count-survives-the-old-ceiling ... ok caught` (a twenty-seventh row now *disagrees*) and `numeral-table-loses-its-hyphenated-compounds ... ok caught` |
| CI on the pushed head | `gh api …/commits/fff4e03/check-runs`, polled until the last job concluded | run `38755973431`, three jobs `completed/success` (SonarCloud `neutral`, as ever) |
| CI's own lane numbers | the job log, read rather than inferred from the green | `All checks passed!`, `186 files already formatted`, `Success: no issues found in 23 source files`; `100% tests passed out of 204`; `449 passed, 5 skipped in 204.76s (0:03:24)`; `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 416.4s total`. The #91 reconciliation holds on the runner's numbers: `449 + 5 = 454 = 450 + 4` |

The format count is `186` in two agreeing vantages -- CI's lane and the `git archive` export of `fff4e03`.
This tree's own walk reports `187`, and the extra file is again `REFACTOR_PROMPT.md`, the parallel
session's untracked V2 prompt; finding 81's rule keeps it out of the record, as it did in Phase 43.

## 6. Numerical validation

No measurement is published and none moved.

* **102** declared plants, from the list; the sheet's annotation and its guard are the two ends.
* **519 / 450** -- unchanged by this phase: the generation added assertions inside an existing test, not
  a new one, and the offline pair moves only when a test is added. #91 is checked on the runner's numbers
  in §5's CI row.
* **102** register entries, unchanged: #97 amended closed, no entry opened.
* **Zero** artifacts re-frozen; the report's record is now bundle `4b06b482de37`, PDF `5af578d4f384`.

## 7. Remaining limitations

* **#102 stands.** The noun list and the one-modifier tail are the recall boundary that remains; the
  numeral table was the only part of the rule whose blindness had a *ceiling*, and that part is gone.
* **One hundred is a new ceiling, chosen not derived.** A corpus count of `one hundred forty-seven`
  things would need hundreds compounds; the self-test names the bound, so the next extension is a
  measured decision rather than a KeyError.
* **#98, #99 and #101 stand** as registered.

## 8. Technical debt registered here

| Entry | What it records | Why it is a limitation and not a defect |
|---|---|---|
| #97 (amended closed) | the ceiling generated away, the fallback retired, the disagreement demonstrated | the entry keeps the shape of the failure: a table that stops where its author's corpus stopped |
| -- | no new entries opened by this phase | the residual in §7 is #102's, already registered |

## 9. The gate

Closed when the 102-plant sweep runs on the committed tree with no line at any other status and the tree
clean afterwards; when CI's three jobs are read from their own logs on the pushed revision and #91 is
checked on the runner's numbers; when the register, the audit, the scope table and the sheet agree on the
plant count and the test pair, each from its own producer; and when the ceiling's closure is shown twice
-- a count above twenty-six that disagrees instead of crashing, and a compound whose withholding silences
exactly its own claim. A record checks the revision it names: the sweep and CI rows land in the commit
after this file, on the sha the runner built.
