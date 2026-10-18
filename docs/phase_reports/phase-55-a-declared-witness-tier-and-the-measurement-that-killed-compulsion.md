# Phase 55 — a declared witness tier, and the measurement that killed compulsion (#106 closes)

## 1. Completed

The ledger's `document:` kind is split in two and the split is enforced from the path rather than from the
sentence: `card:` cites a file inside `_MEASUREMENT_CORPUS` (a measurement table that can disagree today),
`record:` cites a file inside `_NARRATIVE_RECORDS` (the one place a superseded run's reading was written
down), and a cited path matching neither prefix is refused instead of defaulting into a tier. The 16 rows
that existed as `document:` were assigned by reading what each cited file is: **6 cards** --
`docs/model_cards/crr_binomial.md` and `docs/model_cards/heston.md` (four rows) and
`docs/model_cards/scenario_stress_testing.md` -- and **10 records** (eight in `docs/phase_reports/` -- three
from phase-05, two from phase-09, one each from phase-01 twice and phase-06 -- two in
`docs/release_notes_*`, and none in the register, which lost both of its rows when Phase 54 refiled them).
The published reading is therefore 2 artifact, 6 card, 10 record, 1 granularity, 1 phantom, 26 none --
producer-backed still **19 of 46**, with the 19 now stating what kind of witness each one is.

The twin of the artifact-side forced-candidate rule was written, measured, and shipped in the weaker of its
two forms. `_measurement_candidates()` searches the declared corpus for files printing a claim's number
inside one clause of the noun the claim counts. Of the 26 `none:` rows, the candidate-set sizes are 0 in 9,
1 in **1**, 4 in 11, 5 in 1, 7 in 3 and 8 in 1. The single forced row is
`paper/technical_report.tex`'s `200{,}000 paths` -- a corner of the memory sizing the report labels an
estimate -- and its only corpus match is `docs/model_cards/heston.md`'s `200k paths / 250 steps`, the
xi=0 collapse run. So the rule #106 proposed, *refuse the filing when exactly one exists*, would have
compelled a false attribution at its first firing, and it is not shipped. What ships is disclosure: the
verdict names `docs/model_cards/heston.md` and says why that measurement is not the sentence's, and
`_MEASUREMENT_DISCLOSURES` pins the firing set so the rule cannot be disabled by a search that quietly
stops matching.

The clause window is load-bearing and measured, not assumed. Searching whole files instead of clauses
returns 21 to 51 matching files for a spelled numeral -- `two lattices differ by a convention term`
answering a claim about two columns -- which is the same noise-to-signal ratio that made Phase 49's sample
uninformative. Widening the window is itself a plant, and it reddens on the pin.

Register: #106 amended closed with the measurement that refuted its own proposed fix. `docs/integrity_audit.md`
carries **finding 90** for the two rows that shipped as citations and were copies. Six plants (144 → 150),
four of Phase 54's anchors re-pointed for the new kind names.

## 2. Assumptions this rests on

- A directory's tier is a durable property, decided once with a written reason, and it is weaker than the
  per-claim judgement it replaces: `docs/limitations.md` could legitimately originate a reading some day and
  would then have to be added to `_NARRATIVE_RECORDS`, which the guard treats as a decision because a
  declared prefix nobody cites is refused as dead vocabulary.
- `card:` is treated as able to disagree today. A model card's figures are version-controlled prose, not
  content-hashed artifacts -- #86's asymmetry -- so a card can be edited to match a claim, and the guard
  would read the edit as agreement. That is #86's standing limitation, not a new one.
- The corpus search reads `docs/model_cards/*.md` as folded text. A card that states a configuration in a
  table cell separated by pipes is still one clause, because `|` is a clause break in the splitter and the
  adjacency test is the number and the noun in the same cell.
- `record:` cites the *origin* of a reading. If two phase reports print the same reading, the ledger names
  one; the guard checks that the named one prints it, and nothing checks that it was first.

## 3. Files changed

- `tests/python/test_artifact_metadata.py` -- `_MEASUREMENT_CORPUS`, `_NARRATIVE_RECORDS`,
  `_MEASUREMENT_DISCLOSURES`, `_clause_of()`, `_measurement_files()`, `_measurement_candidates()`, the
  `card:`/`record:` branch with its tier and self-citation refusals, the corpus-disclosure branch, the
  unused-prefix and firing-set pins, and the kind list.
- `scripts/mutation_plants.py` -- six plants; `declaration-verdict-cites-a-quote-the-file-dropped`,
  `declaration-verdict-quotes-a-number-the-quote-omits` and the two Phase 54 disclosure anchors re-pointed
  to the new kind spellings.
- `docs/limitations.md` -- #106 amended closed.
- `docs/integrity_audit.md` -- finding 90.
- `docs/project_scope.md` -- §9 row.
- Count cascade: `docs/interview_defense.md` (the sweep annotation), `paper/technical_report.tex` and the
  rebuilt `paper/technical_report.pdf` with its `technical_report.build.json` pair, plus the census gold
  and the two plant anchors that read those numbers.

## 4. What the phase learned, including about its own first design

**The proposed fix was the thing the entry named as its cost, and measuring it was cheaper than arguing
about it.** #106(c) said the sibling search would "become a candidate corpus for most of the 26" and that
the rule would have to exclude restatements. Written literally, the search produced one forced row out of
26 -- and that row was a false positive, not a missed producer. A phase that had implemented the entry as
written would have shipped a guard that reddens the ledger until an author agrees with it, which is a way
of making the wrong number correct by decree. The disclosure form costs one line in one verdict and keeps
the disagreement visible.

**A tier distinction has to be checkable from something other than the claim.** Phase 54 tried to make
"producer" a property of the row and got two copies filed as producers. Phase 55 makes it a property of the
*path*, which the guard can read: the same two rows would now be refused a `card:` verdict because
`docs/limitations.md` and `docs/phase_reports/` are declared narrative, and the audit's own reason for
refusing a keyword rule -- reasons negate their own words -- is recorded as finding 90(a) so the next phase
does not rebuild it.

**The pin is what makes a narrowing rule falsifiable.** A disclosure that fires on one row can be disabled
either by breaking the search or by widening it, and both directions leave the guard green because the
advice branch simply stops being reached. Pinning the derived firing set against `_MEASUREMENT_DISCLOSURES`
means the row set has to be re-agreed when the search moves; `clause-window-widened-until-every-file-matches`
is the plant that proves it, and it reddens on the pin rather than on the disclosure.

**`caught` proves the guard failed, not that it failed where the plant says.** After the full sweep the
six new plants were re-run one at a time with the mutation applied by hand and the guard's own traceback
read, because the harness's `--verbose` echoes only pytest's summary line. Five matched their claimed
branch. The sixth did not: `clause-window-widened-until-every-file-matches` was written to show that
widening the window dissolves the forced row into "many", and what it actually does is *invent a second
forced row* -- `12 artifacts` becomes forced against
`docs/model_cards/portfolio_covariance_and_optimisation.md`, which says `12 functions, 10 bound types, 81
members`. The guard's in-loop pin caught it and the plant's claim has been rewritten to name that branch.
The correction strengthens the phase's central finding rather than weakening it: an unbounded corpus match
does not merely fail to help a disclosure rule, it manufactures new demands for attributions that are wrong,
which is what compulsion would have enforced.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 199 files already formatted, measured on the `git archive` export of `e548d0e` (finding 81's rule), and the runner reports the same 199 |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --test-dir build/dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | `Evidence is intact.` -- the report bundle moved to `a0c9510ab961` (PDF `4efd9f2c2225`) when this phase report landed, no artifact re-frozen |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 458 tests collected |
| Python | `.venv/bin/python -m pytest -q` | 527 passed in 159.27s (0:02:39) |
| Falsification, full sweep | `.venv/bin/python scripts/run_mutation_suite.py --all` on `e548d0e` | 150/150 planted defects were rejected by their guard, tree clean afterwards, exit 0 |
| CI on the pushed head | run `39095332946` on `e548d0e`, read from each job's own log | lint `All checks passed!`, `199 files already formatted`, mypy `Success: no issues found in 23 source files`; C++ and Python `100% tests passed out of 204` and `457 passed, 5 skipped in 210.13s`, which is #91's reconciliation against the 458 the probe collects (`457 + 5 = 458 + 4 = 462`); benchmark `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 426.6s total` |

## 6. Numerical validation

| Figure | Value | Producer |
|---|---|---|
| Declared pairs | 46 | `_declared_pairs()` |
| Kind split | 2 artifact, 6 card, 10 record, 1 granularity, 1 phantom, 26 none | `_DECLARATION_READING` |
| Producer-backed | 19 of 46 | the same |
| Corpus files searched | 8 (`docs/model_cards/*.md`) | `_measurement_files()` |
| `none:` candidate-set sizes | 0 x9, 1 x1, 4 x11, 5 x1, 7 x3, 8 x1 | `_measurement_candidates()` |
| Forced disclosures | 1 (`200{,}000 paths` -> `docs/model_cards/heston.md`) | `_MEASUREMENT_DISCLOSURES` |
| Whole-file matches for a spelled numeral | 21 to 51 files | the same, window widened |
| Plants | 144 → 150 | `scripts/mutation_plants.py` |

## 7. Remaining limitations

- The guard checks that a named refusal *names* the candidate; it cannot check that the refusal is true.
  That is the definition of a declaration and no instrument closes it.
- `card:` figures are prose in version control, not hashed artifacts (#86). A card edited toward a claim
  would satisfy the check.
- The tier tables have one and two entries. A new source directory is refused until someone classifies it,
  which is the intent, and the cost is that the classification is still a human judgement.
- `_measurement_candidates()` runs over 8 files per `none:` row, so the guard's cost grows with the corpus
  rather than with the ledger.

## 8. Technical debt registered here

Nothing opened. #106 is amended closed by this phase, and the residue it describes -- that the truth of a
named refusal is uncheckable -- is stated in the entry as a boundary rather than queued, because the fix
would be a producer for the meaning of a sentence.

Still open from earlier phases: **#103**, whose static half was measured and rejected and whose dynamic form
costs a suite run per plant, and **#105**, the compound-head placement judgement with its reversal condition
on the table. Related: finding 90, #86, #99, #101.

## 9. The gate

The gate moved from "a human read the sentence" to "the ledger states which kind of source it is trusting,
and the source is read back". That is a smaller claim than #101 originally wanted -- a card is still prose,
and a record is still a copy of a run nobody can re-execute -- but it is a claim the guard can actually
check, and the one place it could check more, the forced corpus candidate, is the place the measurement said
it should check less. Refusing to compel an attribution is the same judgement #104 and #105 made about the
rule, now applied to the ledger: a count that lands on the wrong measurement is worse than a count with no
producer, because it reads as settled.
