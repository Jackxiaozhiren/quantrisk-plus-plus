# Phase 53 — the census queue is worked off, and it ends on one shape (#105 gets its second instance)

Date: 2026-10-17. Debt items: `docs/limitations.md` #101 amended with the finished census (its headline
half untouched), #105 amended with its second instance and the measured placement decision.

## 1. Completed

* **`docs/validation_matrix.md` censused: 31 distinct phrases, 31 quantities, 0 phantoms.** Among them
  `60 markets` -- the reading Phase 51's collision refusal produced. That is the first time a fix in this
  project has been checked by a later enumeration rather than by the guard that shipped it, and it passed.
* **`paper/technical_report.tex` censused: 84 distinct phrases, 83 quantities, 1 phantom.** The phantom is
  `3 path`, from "Over 40 seeds $\times$ 3 path budgets $\times$ 4 scenarios": the head noun is `budgets`,
  which is not on `_REPORT_NOUNS`, so the rule stopped at `path` exactly as it stopped at `radius` in the
  rehearsal sheet one phase ago.
* **The census is now complete over the inventoried corpus.** README 24/24, reproducibility 19/19, the
  rehearsal sheet 39/40, the matrix 31/31, the report 83/84: **196 of 198** distinct phrases are
  quantities. Both failures are one shape (#105), and the conjunction class #102 named is not represented
  in the finished lists at all -- it was refused mechanically and never reappeared.
* **#105's placement question decided on numbers rather than taste.** The greedy alternative (allow a
  counted noun to modify, with `definitions` and `budgets` on the list) was measured over the corpus: it
  repairs both truncations, gains two further real claims (`two definitions`, `one cmake definition`) and
  re-creates `60 markets spread` -- 200 phrases against the shipped 198, one misattribution against two
  truncations. The block stays, on the stated ground that attributing a count to a word the sentence uses
  as a verb is the failure invisible from the extraction alone. The entry names the number that would
  overturn it.
* **2 plants moved and 3 added (129 -> 132)**: two Phase 52 plants had anchored the pending list, which
  this phase emptied, so they were re-pointed at the census entries they now have to break; the new ones
  forget the report's phantom, make the matrix quote a phrase the table never prints, and file one phrase
  as both a quantity and a phantom.
* **The cascade**: plants 129 -> 132 in the rehearsal sheet's annotated command line and its plant anchor,
  `fifty-three report files` -> `fifty-four`, and the report re-typeset. The register stays at 105 entries
  and the test pair at 526/457, because no entry was opened and no test function added.

## 2. Assumptions this rests on

* The two judgement calls that decided the report's list are the criterion's, not new ones: `zero spread`
  (a multiplier with zero dispersion) and `one factor moves` (a bound that holds while one factor moves)
  are readings in which the number measures the named noun, so they are gold; `3 path` is the case where it
  does not, because the sentence counts budgets.
* A completed census is a partition, not a score: `_PRECISION_PENDING` is empty by choice and the guard's
  partition assert is what makes a sixth inventoried document a decision rather than an omission. The
  pending loop now has nothing to iterate, which is the correct state of an instrument with no backlog, and
  is why the plants that used to break it had to be re-aimed.
* The alternative placement was measured with `definitions` and `budgets` added, because testing the greedy
  rule without them would only have proved that the head nouns matter, not which placement wins.

## 3. Files changed

`tests/python/test_artifact_metadata.py` (`_CENSUS_MATRIX_GOLD`, `_CENSUS_MATRIX_PHANTOMS`,
`_CENSUS_REPORT_GOLD`, `_CENSUS_REPORT_PHANTOMS`, the two census entries, the now-empty
`_PRECISION_PENDING` with its annotation, and the guard's docstring), `scripts/mutation_plants.py`
(3 plants, 2 anchors re-pointed, the count-tracking anchors), `docs/limitations.md` (#101 and #105
amended), `docs/interview_defense.md`, `docs/project_scope.md` §9, `paper/technical_report.tex` with its
rebuilt PDF and `build.json`, and this report.

## 4. What the phase learned, including about its own first design

* **A finished instrument shows you what the earlier instruments were for.** Three phases of recall work
  (#100, #102, #102's sample) never produced this shape, because a miss list cannot contain a phrase the
  rule did print. The census found it twice in two documents, and both are the same mechanism, which turns
  #105 from a curiosity into the rule's remaining precision story.
* **The empty list is the part that needed thinking about.** Deleting `_PRECISION_PENDING`'s contents was
  trivial; noticing that two falsification plants were anchored on its *first entry* is not. The registry
  guard caught it -- that is what it is for -- and the generalisation went into `docs/project_scope.md`:
  a plant anchored on the head of a queue is a plant about its contents, so the phase that empties a list
  owns the job of re-aiming it. The same trap recurred twice in three phases (Phase 51 reformatted a tail
  an anchor named, Phase 52 moved a queue head, Phase 53 emptied it).
* **`60 markets` passing the matrix census is the strongest evidence in the phase**, and it was not
  designed as a test: Phase 51 fixed a phrase in the report and the matrix happened to quote the same
  measurement. An instrument that covers more of the corpus than the fix that fed it is how a change gets
  audited by later work rather than by its own author.
* **The census caught this phase's own cascade.** The report's gold list was generated from the tex while
  it still said `fifty-three report files`, and the cascade for this very phase then moved that phrase to
  `fifty-four`. The guard failed with the missing phrase named, which is the mechanism working: a frozen
  transcription that a later edit in the same commit has invalidated is exactly what an owner-less number
  looks like before someone owns it. The fix was to follow the cascade in the gold list, not to relax the
  assert -- and the order of operations is the lesson: generate a census *after* the counts it quotes.
* **The decision I did not make.** Adding `budgets` and `definitions` to the noun list would raise recall
  by two claims under either placement, and was not done, because under the shipped block it changes
  nothing for those two phrases (measured: `3 path` stays) and under the greedy one it re-creates the
  misattribution. A recall gain that only pays out in the configuration you rejected is not a gain.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 197 files already formatted on this tree; the record commit quotes the `git archive` export (finding 81's rule) |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --test-dir build/dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | Evidence is intact -- the report bundle moved, no artifact re-frozen |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 457 tests collected |
| Python | `.venv/bin/python -m pytest -q` | 526 passed in 94.71s |
| Falsification, full sweep | recorded in the next commit, on the sha it ran on | pending |
| CI on the pushed head | recorded in the next commit, from the runner's own logs | pending |

## 6. Numerical validation

| Figure | Value | Producer |
|---|---|---|
| Matrix hits / gold / phantoms | 31 / 31 / 0 | `_census_hits`, guard lists |
| Report matches / distinct / gold / phantoms | 99 / 84 / 83 / 1 | the same, plus the extractor's list |
| Census totals, five documents | 198 phrases, 196 quantities, 2 phantoms | `_PRECISION_CENSUS` |
| Phantom shapes | 1 (compound head off the list) | the two named entries |
| Greedy alternative across the corpus | 200 phrases, +2 real, 1 misattribution, 2 truncations repaired | measured with `definitions`/`budgets` added |
| Pending queue | 0 documents | `_PRECISION_PENDING` |
| Plants | 129 -> 132 | `run_mutation_suite.py --list` |
| Register entries | 105, unchanged | `_numbered_limitation_entries()` |
| pytest with / without `oracles` | 526 / 457, unchanged | the runner, `measure_offline_collection.py` |
| Phase report files | 53 -> 54 | `docs/phase_reports/*.md` |

## 7. Remaining limitations

* The census is a snapshot of five documents; a sixth inventoried text is a decision the partition assert
  will force, not a line of code to write.
* #101's declaration half is untouched and is now the entry's whole content: ten report claims rest on a
  hand-written reason, and no instrument here reads reasons.
* #105's placement judgement is corpus-relative: two truncations versus one misattribution on 198 phrases.
  A document with more compound heads would flip the arithmetic, and the entry names that as the condition
  for re-deciding.
* Nothing checks that a gold entry is *correctly* judged rather than present: the census pins that a
  phrase is printed and classified, not that the classification was wise. The named phantoms are where a
  reader can disagree.

## 8. Technical debt registered here

* No new entry. #101 amended (queue finished, headline half explicitly unaffected), #105 amended with its
  second instance, the measured trade-off and the reversal condition.
* Still open after this phase: **#101** (declarations), **#103** (the static plant-guard pairing, whose
  dynamic form costs a suite per plant), **#105** (the compound-head placement, now with numbers on both
  sides). Those three are the whole of the register's open debt, and they are different kinds of work --
  one needs a producer, one an instrument, one a decision -- so the next phase should pick by kind rather
  than by number.

## 9. The gate

Nothing here is a release. The claim is a completed instrument with its totals named: five documents, 198
distinct phrases, 196 quantities, 2 phantoms of one shape, and a placement decision made on the measured
cost of both sides instead of on preference. The census can no longer be widened within the corpus, so what
it leaves behind is the queue it could not touch -- a declaration's reason, a plant's reader, and a head
noun off a list.
