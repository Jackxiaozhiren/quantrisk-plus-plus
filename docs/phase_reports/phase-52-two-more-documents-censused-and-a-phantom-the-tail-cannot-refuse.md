# Phase 52 — two more documents are censused, and the second phantom is a shape the tail cannot refuse (#105 opened)

Date: 2026-10-17. Debt items: `docs/limitations.md` #101 amended with the widened census, #105 opened from
the enumeration, #104 amended because its own prediction arrived.

## 1. Completed

* **`docs/reproducibility.md` censused: 19 distinct phrases, 19 quantities, 0 phantoms.** Read in context,
  each measures the noun it names -- `12 artifacts` that reported VOLATILE, `four modules` that gate on an
  import, `twenty-two readings` behind the band percentages, `six releases` between a freeze and a restated
  PDF.
* **`docs/interview_defense.md` censused: 40 distinct phrases, 39 quantities, 1 phantom.** The phantom is
  `two radius`, from "two radius definitions were wrong": the number counts *definitions*, and the rule
  stopped at `radius` because `definitions` is not on the noun list. It is filed as a phantom rather than
  deleted from the document, because the sentence is correct English and the rule is what is wrong.
* **The criterion is now written down.** A hit is gold when the number measures the noun the phrase names,
  as a count (`19 members`, `two radii`) or as a value (`32.6% spread`, `0.15 cubic radius`,
  `39,040,079 paths/s`); it is a phantom when the noun is not what the number measures at all. Two of the
  forty-one judgements turned on this: the radius *value* `0.15` stays gold while `two radius` does not,
  and `paths/s` is read as one noun with a unit rather than as a second thing counted.
* **#105 opened with the measured conflict, not with a complaint.** Adding `definitions` to the noun list
  and dropping `_COLLISION_BLOCK` reads `two radius definitions` correctly; keeping the collision block --
  the thing that closed #104 one phase ago -- reads `two radius` again. The two corpus instances want
  opposite placements of the same lookahead, and the pattern cannot tell a compound head from a participle.
  The number this entry carries is **1 phantom in the 83 distinct phrases censused so far**.
* **The queue is measured at 115**: 31 phrases in `docs/validation_matrix.md`, 84 in the report. That is the
  whole of #101's enumerable half, and the phase after this one takes it.
* **3 plants (126 -> 129)**: reclassify the sheet's phantom as gold, which the guard sees because the rule
  still prints it; make gold quote a phrase the file never prints; and put a document back into the queue it
  has already left.
* **The cascade**: register 104 -> 105 in eleven spellings across six documents and three plant anchors,
  plants 126 -> 129, `fifty-two report files` -> `fifty-three`, and the report re-typeset. One existing
  plant had to be re-pointed: Phase 50's `precision-queue-drops-a-document` anchored the pending list's
  first entry, and censusing that entry moved it.

## 2. Assumptions this rests on

* The gold lists are transcriptions, not derivations: every entry is the extracted spelling, lowercased, of
  a phrase the document prints. The guard re-derives the hits from the documents each run, so a reworded
  sentence reddens the census rather than scoring stale gold.
* Occurrences collapse to distinct phrases. The rehearsal sheet prints 50 matches and 40 phrases, with ten
  phrases repeated (`548,368 assertions`, `457 tests`, `69 cases`, `492 rows`, `18,816 rows`,
  `39,040,079 paths`, `200,000 paths`, `one test`, `five books`, `30 joint moves`); the denominator quoted
  anywhere in this phase is the set, and the docstring says so.
* A declared claim (an exemption with a hand-written reason) is not the same object as a phantom: the
  census judges whether the rule printed a quantity, and #101's untested-declaration half is about whether
  a human's reason for excusing one is true. This phase touches only the first.

## 3. Files changed

`tests/python/test_artifact_metadata.py` (`_CENSUS_REPRO_GOLD`, `_CENSUS_REPRO_PHANTOMS`,
`_CENSUS_SHEET_GOLD`, `_CENSUS_SHEET_PHANTOMS`, the two new census entries, the shrunken
`_PRECISION_PENDING`, the criterion in the guard's docstring, and the register-count spellings),
`scripts/mutation_plants.py` (3 plants, one re-pointed anchor, the count-tracking anchors),
`docs/limitations.md` (#101 and #104 amended, #105 opened), `README.md`, `docs/interview_defense.md`,
`docs/validation_matrix.md`, `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md`,
`docs/project_scope.md` §9, `paper/technical_report.tex` with its rebuilt PDF and `build.json`, and this
report.

## 4. What the phase learned, including about its own first design

* **The census earned its keep on the second document, not the first.** README's phantom was a glued
  clause, and Phase 50 could plausibly have claimed the class was done. The sheet's is a compound head, and
  no rule in the tail can refuse it without bringing back the thing #104 was closed by. Enumerating the next
  document is what produced that, and it is the first time this project's debt queue has been shortened by
  finding out that two of its entries are the same mechanism pulling opposite ways.
* **Writing the criterion down changed two verdicts.** Before stating "the number measures the noun", the
  obvious instinct was to reject anything that is not a count -- which would have filed `0.15 cubic radius`
  and `32.6% spread` as phantoms, and both are owned by producers (the crossing map's radius, the band
  percentages). Stating the rule made the two accepted and one refused, and the sentence now lives in the
  guard's docstring where the next censuser has to meet it.
* **An arithmetic slip caught before publishing.** The first draft of the docstring said "82 of 84"; the
  three censused documents print 24 + 19 + 40 = 83 distinct phrases, and 82 are quantities. The count that
  goes into a register entry has to come from the same addition the guard performs, not from a memory of
  the hit lists.
* **A plant can be orphaned by the mechanism it polices.** Phase 50's plant deleted the first entry of
  `_PRECISION_PENDING`; this phase censused that document, so the anchor described a list that no longer
  starts that way and the registry guard refused it. The general form is worth keeping: a plant that anchors
  on the *head* of a queue breaks when the queue is worked off, so a re-reading of the plant list belongs in
  the phase that empties a list, not in the one that adds to it.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 196 files already formatted, measured on the `git archive` export of `1989bc4` (finding 81's rule), and the runner reports the same 196 |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --test-dir build/dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | Evidence is intact -- the report bundle moved, no artifact re-frozen |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 457 tests collected |
| Python | `.venv/bin/python -m pytest -q` | 526 passed in 90.02s |
| Falsification, full sweep | `.venv/bin/python scripts/run_mutation_suite.py --all` on `1989bc4` | 129/129 planted defects were rejected by their guard, tree clean afterwards, exit 0 |
| CI on the pushed head | run on `1989bc4`, read from each job's own log | lint `All checks passed!`, `196 files already formatted`, mypy `Success: no issues found in 23 source files`; C++ and Python `100% tests passed out of 204` and `456 passed, 5 skipped in 208.17s`, which is #91's reconciliation against the 457 the probe collects (`456 + 5 = 457 + 4 = 461`); benchmark `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 429.8s total` |

## 6. Numerical validation

| Figure | Value | Producer |
|---|---|---|
| `docs/reproducibility.md` hits / gold / phantoms | 19 / 19 / 0 | `_census_hits` and the guard's lists |
| `docs/interview_defense.md` hits / gold / phantoms | 40 / 39 / 1 | the same |
| Matches vs distinct phrases in the sheet | 50 / 40 | the extractor's list versus the set |
| Censused so far | 3 of 5 documents, 83 phrases, 82 quantities | `_PRECISION_CENSUS` |
| Pending backlog | 115 (31 matrix + 84 report) | `_census_hits` per pending document |
| The phantom | `two radius` from "two radius definitions were wrong" | read from the sentence |
| Noun-list growth with the collision block dropped | reads `two radius definitions` | measured on the sentence |
| Noun-list growth with the block kept | reads `two radius` | the same measurement |
| Register entries | 104 -> 105 | `_numbered_limitation_entries()` |
| Plants | 126 -> 129 | `run_mutation_suite.py --list` |
| Phase report files | 52 -> 53 | `docs/phase_reports/*.md` |
| pytest with / without `oracles` | 526 / 457, unchanged | the runner, and `measure_offline_collection.py` |

## 7. Remaining limitations

* Two documents are still uncensused (115 phrases), so precision is a per-document fact and not yet a
  property of the corpus.
* #105 has no fix. The tail needs to know which words are verbs in this register, and the alternative --
  a third list of measurement verbs -- is unregistered work that an unlisted verb defeats silently.
* #101's declaration half is untouched by any of this, and the report's ten declared claims are still
  answered by prose a guard cannot read.
* The census collapses occurrences, so a document that prints a wrong number twice is censused once; the
  ownership inventory, not the census, is what polices repeated figures.

## 8. Technical debt registered here

* **#105** (new): the compound-head phantom, with the measured conflict against #104's refusal and the
  number 1 in 83.
* **#101** amended: the census now covers three of five texts, the queue is 115 phrases, and the entry's
  headline half (untested declarations) is explicitly unaffected by this mechanism.
* A habit rather than a queue item: when a phase empties a list, re-read the plant list, because a plant
  anchored on a list's head is a plant about its contents.

## 9. The gate

Nothing here is a release. The claim is bounded and measured: two documents enumerated, 59 phrases read in
their sentences, one phantom named, and the finding that the two phantoms this project has ever named need
opposite rules in the same slot. The census is now three fifths of the corpus by document count and 83 of
198 by phrase count, and the remaining queue is a number rather than an intention.
