# Phase 48 — the claim rule is scored against sentences whose quantities are known (#102 advanced, #101's precision edge measured)

Date: 2026-10-17. Debt items: `docs/limitations.md` #102 (instrument now exists; the entry stays open
on the unbiased-sample half) and #101 (its precision edge measured on a targeted sample).

## 1. Completed

* **`test_the_claim_rule_is_scored_against_sentences_whose_quantities_are_known`.** `_CLAIM_CORPUS` is
  15 (document, needle, gold) triples; the needle's *enclosing unit* is taken from the document, never
  written here, and the shipped extractor runs over that unit. Gold was written by reading each unit and
  listing every quantity it asserts.
* **The measurement.** 22 gold quantities, 6 the rule sees, **16 named blind spots**, and **0 phantoms**
  among the 6 it returns -- recall 6/22 and precision 6/6 on this sample. Both disagreement lists are
  frozen (`_CLAIM_RULE_MISSES`, `_CLAIM_RULE_FALSE_POSITIVES`) so any move in either direction has to be
  deliberate.
* **What the 16 are.** Fifteen are countable nouns the list never carried -- `shocks`, `arm`,
  `components`, `points`, `families`, `scales`, `maps`, `partials`, `blocks`, `days`, `arms`, `levels`,
  `experiments` in a partitive ("Six of the seven experiments"), `benchmark` in the singular the list
  only carries plural -- and one is the hyphen shape #100 traded away: "Two Level-1 identities" is two
  identities, and the tail cannot span a hyphenated modifier.
* **3 plants (113 -> 116).** A needle that no longer names a sentence in its document; the noun list
  widened so the miss ratchet must move; the `-` exclusion removed so a phantom reaches the precision
  ratchet.
* **The cascade**: sweep annotation 113/113 -> 116/116, test pair 523/454 -> 524/455 in thirteen
  spellings and four plant anchors, the artifact index `forty-eight report files` -> `forty-nine`, and
  the report re-typeset.

## 2. Assumptions this rests on

* **The corpus is targeted, so the recall figure is not an estimate of the documents.** Units were chosen
  to include known blind spots, which is why 16 of 22 gold items are misses; a number that describes the
  rule's behaviour across the corpus needs a sample drawn without looking at the rule, and #102 stays
  open for exactly that. Publishing 6/22 as "the rule's recall" would be the kind of unlabelled ratio
  this project has been built to refuse.
* Gold completeness is a reading judgement per unit: an omitted gold item would show up as a phantom and
  a guessed one as a miss, so both errors are visible rather than silent.
* Units split on `.!?` and on `|`, because the matrix's cells are where most of its quantities live and
  a row-wide sentence would merge six unrelated cells into one scoring unit.

## 3. Files changed

`tests/python/test_artifact_metadata.py` (the guard, `_CLAIM_CORPUS`, `_corpus_sentences`, the two
frozen lists), `scripts/mutation_plants.py` (3 plants and the anchors that track the pair and the sweep
count), `docs/limitations.md` (#102 and #101 amended with the measurement, and #102's example corrected),
`docs/reproducibility.md`, `docs/interview_defense.md`, `docs/project_scope.md` §9,
`paper/technical_report.tex` with its rebuilt PDF and `build.json`, and this report.

## 4. What the phase learned, including about its own first design

* **The corpus caught me inventing a sentence.** My first negative entry named a README cross-reference
  that does not exist; the needle assertion failed before any scoring happened. That is the whole
  argument for taking the unit from the document instead of typing it into the test -- the #98/#103
  lesson, that a hand-written pointer to text is a claim until something checks it.
* **My first gold lists were incomplete, and the guard said so as false positives.** The unit that
  "runs all nineteen members" also counts four correctness benchmarks, fourteen statistical experiments
  and one performance benchmark; scoring precision against a gold of one item called two real
  quantities phantoms. Completing gold is what turned a wrong metric into a right one -- the extracted
  side never changed.
* **A dense table cell is a bad scoring unit.** The first pass split markdown only on sentence-final
  punctuation, so one matrix "sentence" spanned six cells and carried eleven quantities; half the
  measured disagreements were artefacts of that merge. Splitting on the cell separator too made each
  unit something a reader could actually score.
* **The hyphen entry is a cost, stated plainly.** #100 removed `-` from the lookbehind because a
  hyphenated ordinal's number read as a quantity, and that was right: it killed five phantoms and lost
  nothing measurable *then*. This corpus finds the bill -- "Two Level-1 identities" is a real count the
  tail now cannot reach. The fix is not to put the dash back; it is to let the tail span a hyphenated
  modifier, which is a rule change that the ratchet will price.
* **Precision came out clean on the sample, which is a weaker claim than it looks.** 6 of 6 returns are
  real quantities, but the sample has only two designed negatives (a version list, a confidence level),
  so the honest reading is "no phantom in this set", not "the rule is precise". #101's declaration pile
  -- a reason written by hand that nothing tests -- is untouched by this phase.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 192 files already formatted on this tree; the record commit quotes the `git archive` export (finding 81's rule) |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --preset dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | Evidence is intact -- the report bundle moved, no artifact re-frozen |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 455 tests collected |
| Python | `.venv/bin/python -m pytest -q` | 524 passed |
| Falsification, full sweep | recorded in the next commit, on the sha it ran on | pending |
| CI on the pushed head | recorded in the next commit, from the runner's own logs | pending |

## 6. Numerical validation

* **15** corpus units, **22** gold quantities, **6** seen, **16** named blind spots, **0** phantoms among
  what was returned -- every one of those counts derived by the guard from the corpus and the rule, none
  transcribed.
* **116** declared plants; **103** register entries, unchanged (#101 and #102 amended in place).
* **524 / 455** -- this environment's pair from their own producers.

## 7. Remaining limitations

* **#102 stays open.** The instrument exists and names its own 16 disagreements; what does not exist is
  an unbiased sample, so no figure describes the rule's recall over the documents.
* **#101's declaration half stands.** Nothing tests whether a written reason for exempting a claim is
  true, and this phase's precision sample is too small to speak for the corpus.
* **#103's static half stands**, and #99's eight pointer-shaped citations remain outside its registry.

## 8. Technical debt registered here

| Entry | What it records | Why it is a limitation and not a defect |
|---|---|---|
| #102 (amended, open) | the scoring instrument now exists; the corpus is targeted so its 6/22 is a named list, not an estimate | an unbiased sample is the part that would make the number a measurement of the documents |
| #101 (amended, open) | precision on a two-negative sample found no phantom; declarations remain untested | "no phantom here" is not "precise", and the entry says which |
| -- | no new entry opened | the residuals in §7 were already registered |

## 9. The gate

Closed for what this phase claims when the sweep runs `116/116` on the committed tree with the tree clean
afterwards; when each of the three new plants is shown to redden the scoring guard rather than any other
-- the widened noun list must move the miss ratchet, and the removed dash must move the precision one;
when CI's three jobs are read from their own logs on the pushed revision; and when #102's entry carries
the 22/6/16/0 counts with the word *targeted* next to them, because the number without that word is the
defect the entry exists to prevent. A record checks the revision it names: the sweep and CI rows land in
the commit after this file, on the sha the runner built.
