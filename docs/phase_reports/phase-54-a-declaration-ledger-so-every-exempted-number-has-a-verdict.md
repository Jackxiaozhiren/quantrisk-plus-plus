# Phase 54 — a declaration ledger, so every exempted number has a verdict (#101 closes, #106 opens)

## 1. Completed

`_DECLARATION_LEDGER` in `tests/python/test_artifact_metadata.py` gives every number the claim
inventory exempts by declaration a verdict, and
`test_every_declared_number_names_a_producer_or_records_that_none_exists` reads the verdict against the
tree. The pairs are not typed by hand: `_declared_pairs()` derives them from the shipped classification
(the claim's own span skipped when an owned pattern covers it, otherwise within `_DECLARE_RADIUS` of a
declaration anchor), so a reworded sentence or a newly inventoried document changes the pair set and the
partition assert says which row has to be written.

Measured as the rows were filled: **46** declared pairs -- 3 in `docs/reproducibility.md`, 13 in the
rehearsal sheet, 6 in `docs/validation_matrix.md`, 24 in `paper/technical_report.tex`, none in README.md,
which declares no anchor of its own. Their verdicts:

| Kind | Rows | What the guard re-reads |
|---|---|---|
| `artifact:` | 2 | the named dotted field in the frozen artifact, and that it still holds the claim's number |
| `document:` | 18 | the named file exists, prints the cited quote, and the quote itself prints the number |
| `granularity:` | 1 | every named member resolves in the typed stubs, and their count is *not* the claim's |
| `phantom:` | 1 | the longer phrase the rule truncated is in the document that carries the claim |
| `none:` | 24 | a category from a closed vocabulary of 14, plus a forced-candidate disclosure |

So **21 of the 46** exempted numbers now have something in this tree that can disagree with them, and
the distribution is pinned in `_DECLARATION_READING` rather than restated in prose.

Three verdicts found their producer while the rows were being written, and the grammar had to learn to
read it. `paper/technical_report.tex` states the Heston collapse at `200{,}000 paths`, the positivity
check over `20{,}000 paths`, and the stress VaR at `400{,}000 paths`; `docs/model_cards/heston.md` writes
`200k paths / 250 steps` and `over 20 000 paths`, and `docs/model_cards/scenario_stress_testing.md`
writes `at 400k paths`. A digit search that only knew `200,000` would have filed all three as having no
producer, which is what #86 and #101 had been recording. `_number_spellings` now accepts the
thousands-separator, space-separated and `k`/`M` forms, and the three rows read as `document:` verdicts.

`seven orders of magnitude` (`paper/technical_report.tex`) cites
`docs/phase_reports/phase-06-portfolio-optimisation.md`, which says `seven and a half orders of
magnitude`. The ledger now names that sentence, so the rounding is a quote a guard holds rather than a
paraphrase a reader has to trust.

`two tests` is the entry's design case, and it is filed as a granularity mismatch rather than as an
agreement: the sheet counts *families* while `python/quantrisk/risk.pyi` declares three functions across
them (`kupiec_pof_test`, `christoffersen_independence_test`,
`christoffersen_conditional_coverage_test`). The guard parses the stubs with `ast` and refuses the row if
a listed name is not declared -- and refuses it in the other direction too, because a list that happens
to contain exactly two members is not recording a mismatch, it is an accident that would read as a
measurement.

The forced-candidate rule was written as a refusal and shipped as a disclosure, because measuring the
candidates said the refusal would compel false attributions. `0.15 cubic radius` has eleven artifact
fields holding 0.15, and the long-dated book's own shipped cubic radius lives in a field holding a
different number -- so naming any of the eleven would attribute the count to a measurement the sentence
does not make. Where exactly one field matches, the verdict has to name it and say why it is not the
producer; two rows do so (`two factors` in the matrix and `two factors` in the report's section heading,
both against `widening_factors`).

Register: #101 amended closed, and **#106** opened for what the ledger still cannot check -- a `none:`
row's absence claim is policed for shape and for the artifact-side search only, so a declared number
whose producer is a sentence in another file can still be filed as having none. Twelve plants
(132 → 144).

## 2. Assumptions this rests on

- A frozen artifact's field is a producer for a document's number only when a human said so. The guard
  checks that the named field still holds the value; it cannot check that the field is what the sentence
  was about. That is why `artifact:` rows are two and not twenty.
- The `.pyi` stubs are the published surface. `_declared_core_surface()` reads them as syntax, so a
  symbol declared only in C++ and not in the stub is invisible to the granularity row.
- `document:` quotes are matched case-insensitively in the folded text the inventories already use, so a
  rewrap does not break a citation and a rewording does.
- The number grammar is a spelling rule, not a unit rule. `200k` is read as 200000 because a model card
  writes it that way beside `paths`; a card that wrote `0.2M paths` would need `M` and the guard would
  not find it, and the row would have to be refiled rather than silently lost.

## 3. Files changed

- `tests/python/test_artifact_metadata.py` -- `_DECLARATION_LEDGER`, `_DECLARATION_KINDS`,
  `_DECLARATION_CATEGORIES`, `_DECLARATION_READING`, `_declared_pairs()`, `_number_spellings()`,
  `_number_is_printed()`, `_declared_core_surface()`, `_artifact_numeric_fields()`, `_artifact_field()`,
  `_field_candidates()`, `_inventory_flat()`, and the new guard.
- `scripts/mutation_plants.py` -- twelve plants; two pre-existing anchors re-pointed to the numbers this
  phase moved (`# 144/144 planted defects rejected`, `fifty-five report files, one per phase`).
- `docs/limitations.md` -- #101's Phase 54 clause, #106 opened.
- `docs/project_scope.md` -- §9 row.
- Count cascade: `README.md`, `docs/interview_defense.md`, `docs/reproducibility.md`,
  `docs/validation_matrix.md`, `paper/technical_report.tex` and the rebuilt `paper/technical_report.pdf`
  plus its `technical_report.build.json` digest pair.

## 4. What the phase learned, including about its own first design

**A guard that crashes is not a guard that fails.** `_field_candidates()` walked
`_frozen_artifact_paths()` and json-parsed every entry; the manifest carries CSVs, so the first run died
with a `JSONDecodeError` inside the helper rather than an assertion. A test error and a test failure look
the same at a glance in a short terminal, and only the traceback says which one happened. The corpus
filter went in before anything else was concluded from the run.

**The name a disclosure rule asks for is a design decision, not an obvious one.** The first version took
the *last* segment of the candidate's dotted path. For
`headline.fits.widening_factors.in the money` that is the book label, so the guard demanded the verdict
say `in the money` -- a phrase in the reason, not a field. The rule now takes the longest segment that is
an identifier, which names `widening_factors` and follows a rename. Neither version was wrong about the
candidate; the first was wrong about what "name it" means, and only a firing plant-style probe of the
real path showed it.

**A substitution script that aborts partway leaves the tree half-cascaded and still green.** One of the
Phase 54 edits carried five replacements in a loop with an assertion per pair; the first failed on
whitespace and the script exited before writing, so three verdicts kept the short field name they were
supposed to have widened. Nothing noticed, because the guard accepts the short name too. What surfaced it
was a plant anchor that no longer matched -- the anchor-check pass reading `anchor=0` for a row that had
been written against the intended text. A cascade that can half-land needs its own verification step, and
`grep -c` on the anchor after the format pass is that step; the assertion in the script proved only that
the *pattern* was absent, not that the file was in the state the plants assumed.

**An empty ledger is the cheapest way to get the row list right.** Writing the guard with
`_DECLARATION_LEDGER = {}` and letting the partition assert print all 46 keys took one run and removed
the entire class of errors where a hand-typed key differs from the derived one by a comma or a lowercase
letter. The census queue in Phase 50-53 was built the same way and this phase confirmed the habit: when
the instrument can name its own rows, do not name them for it.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | pending the record commit's measurement on the `git archive` export (finding 81's rule) |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --test-dir build/dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | pending the rebuild |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 458 tests collected |
| Python | `.venv/bin/python -m pytest -q` | pending the report rebuild |
| Falsification, full sweep | `.venv/bin/python scripts/run_mutation_suite.py --all` | pending, on the committed tree |
| CI on the pushed head | read from each job's own log | pending |

## 6. Numerical validation

| Figure | Value | Producer |
|---|---|---|
| Declared pairs | 46 | `_declared_pairs()` |
| Per document | reproducibility 3, sheet 13, matrix 6, report 24, README 0 | the same |
| Producer-backed rows | 21 (2 artifact + 18 document + 1 granularity) | `_DECLARATION_READING` |
| Rows with no producer | 24, in 14 categories | the same, plus the vocabulary assert |
| Artifact field behind `30 joint moves` | `control.control_moves_compared` = 30 | `_artifact_field()` |
| Functions declared behind `two tests` | 3 | `_declared_core_surface()` over `risk.pyi` |
| Field candidates for `0.15 cubic radius` | 11, none of them this sentence's book | `_field_candidates()` |
| Plants | 132 → 144 | `scripts/mutation_plants.py` |

## 7. Remaining limitations

- A `none:` verdict is checked for its category, its partition, and its disclosure when the artifacts hold
  exactly one matching field. A producer that exists as a sentence in another document, and a field whose
  path does not share a word with the claim's noun, both pass unnoticed. #106.
- `artifact:` and `document:` verdicts are authored, not enumerated: the guard can refuse a stale one, but
  it cannot insist that a row be upgraded from `none:` to a producer.
- The granularity kind has one instance. A second mismatch would have to invent its own grouping word, and
  nothing yet checks that the grouping is the one the sentence means.
- `_field_candidates()` reads every frozen artifact on every `none:` row. The guard costs a second and the
  corpus grows with the freeze, so the instrument's own price is a slow accretion rather than a defect.

## 8. Technical debt registered here

**#106** -- a `none:` verdict is policed for its shape, not for the absence it states. The artifact-side
forced-candidate rule has no document sibling, and `docs/limitations.md` alone is a corpus a declared
number can match by accident, so writing the sibling search means deciding what counts as a restatement.
The entry carries the three cases this phase found by hand (`200k`, `400k`, `20 000` paths) as evidence
that the blind spot is not hypothetical, and the shape of the fix (forced-disclosure extended to
documents, restatements excluded) with its cost.

No new plant-guard debt; #103's static half and #105 stay as they were left.

## 9. The gate

The gate this phase moves is the one #101 has named since Phase 41: a declared exemption used to end the
argument. It now ends with a verdict, and the verdict is read against the tree -- so a renamed artifact
field, a reworded model card, a stub that stops declaring a symbol, and a category invented at the
keyboard all redden rather than age quietly. What the gate does *not* yet do is insist that a number has
a producer; it insists that whoever exempted it says which kind of answer they gave, and that the answer
survives being re-read. #106 is the residue, and it is the first version of that residue with a measured
size: 24 of 46.
