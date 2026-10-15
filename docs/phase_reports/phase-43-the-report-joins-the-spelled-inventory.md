# Phase 43 — The report joins the spelled inventory, and the rollout closes on three false counts

Date: 2026-10-15. Predecessor: Phase 42 (`8138275` + two fixes, recorded in `e4b3409`, CI run
`38738596549` green on the amended head). No version was bumped; `v1.8.0` remains the latest release.

## 1. Completed

`paper/technical_report.tex` is switched on for spelled claims in
`test_every_countable_claim_in_the_report_is_owned_or_declared`, and #95's staged rollout is **complete**:
every text the inventory reads now answers for counts written in words. The report's **45** spelled-only
claims resolve to **18 owned, 10 declared and 17 cited -- none unowned**. Reading them found the
rollout's largest haul of false prose: **three living counts that were wrong**.

| Claim | Was | Is | Producer it now answers to |
|---|---|---|---|
| `Thirteen committed fixtures… roughly 150 KB` | 13 | 16 fixtures, ~300 KB | the directory listing, payloads counted and summed |
| `ten report files covering phases 1 to 9` | 10 | **43** report files, one per phase | `docs/phase_reports/*.md`, owned in digits because `forty-three` is past the numeral table's ceiling (#97's first forced fallback) |
| `the suite has grown by six members since` (from a quoted twelve) | 6 | 7 | **a relation**: the guard reads both spelled numbers from the sentence and requires the second to equal the registry minus the first |

The other owners: the release-tag count (its guard has resolved the spelled form since Phase 21 -- what
was missing was the inventory's credit), the restrike study's three rays, the two-factor bound's four
joint rays, the crossing map's twelve columns, the five-book study's two radii and five books, the four
further books derived as `books_measured - 1`, the order-five map's five books, the stress artifact's
four books and seven named scenarios, the four stress data artifacts the manifest hashes, the four
provenance cases counted from `describe_provenance`'s return branches, the validate gate's seven checks
counted from `command_validate`'s `_record` calls, the sixteen fixtures, the forty-three report files,
and the three refused questions the real-data artifact records in its own `refusals` block.

The ten declarations are the narrative numerals: two orders of magnitude (twice), the fixture's
composition, the one-factor assumption, the two-factor section heading, the roadmap "two checks", the
precision-floor "two sides", the register's "one spread", and the platform incident's "eight float
fields" -- each with the reason no structure in the tree enumerates it.

## 2. Assumptions this rests on

* The Python-source producers are read with `ast`, per finding 82: a substring count of `_record(` or of
  a return statement would also count the file doing the counting.
* The members relation is the only claim owned without a constant: `grown == registry - quoted`. If the
  registry shrinks, the sentence goes red until the prose is rewritten -- which is the point, because a
  shrinkage is exactly when the sentence would otherwise lie quietly.
* The report-file count is written in digits. Owning `forty-three` spelled would fail as `KeyError`
  (#97), not as a disagreement; the fallback is recorded in the guard and in the audit finding.
* No experiment was re-run and no artifact re-frozen. The report was re-typeset because the `.tex`
  moved; `verify_evidence_manifest.py` is the instrument that says nothing else did.

## 3. Files changed

* `tests/python/test_artifact_metadata.py` — the report guard reads spelled claims; one new guard
  (`test_the_report_counts_what_the_studies_and_the_gates_have`) with eighteen owners; one registered
  under the existing tags guard; ten declared anchors; property 5's staging pin inverted to keep the
  completed rollout on.
* `scripts/mutation_plants.py` — 7 plants added and the staging plant replaced by its inverse
  (`report-stops-reading-spelled-claims`), 92 → 99.
* `paper/technical_report.tex` (+ `.pdf`, `.build.json`) — three corrected counts, the sync'd test pair,
  the register size.
* `README.md`, `docs/reproducibility.md`, `docs/interview_defense.md`, `docs/limitations.md`,
  `docs/project_scope.md`, `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md`,
  `docs/validation_matrix.md` — the counts this phase moved.
* `docs/integrity_audit.md` — finding 84.

## 4. What the phase learned, including about its own first design

* **The last document was the worst offender.** Phase 38 found one stale spelled count, Phase 42 found
  one false claim, Phase 43 found three. The pattern is not chance: the report is the oldest prose
  surface, it restates the most quantities, and until this phase nothing could read counts written in
  words anywhere in it. The rollout's ordering (smallest group first) was a review decision, and it
  saved the hardest document for when the classification machinery was most practiced.
* **A relation beats two constants.** "The suite has grown by N members since M" states an arithmetic
  claim whose inputs are both in the sentence and whose check is one subtraction away. Owning it as
  `grown == registry - quoted` means the sentence can never be singly stale again; owning it as two
  numbers would have made this phase's correction the next phase's stale twin.
* **The ceiling became load-bearing.** #97 registered that `SPELLED_NUMBERS` stops at twenty-six and
  guessed the failure would be a matrix row. It arrived instead as a report count the phase itself was
  writing: `forty-three` cannot be owned spelled, so the count went to digits and the fallback is now
  documented in both the guard and the audit finding. The first real consumer of the ceiling decided the
  design question #97 left open.
* **The staging plant's death was the completion signal.** A plant whose mutation is the shipped state
  is not a defect, it is a finished step: the plant became `report-stops-reading-spelled-claims`, whose
  mutation *narrows* the inventory and whose only witness is property 5's pin. The pin's assertion
  flipped from "the report does not read spelled claims yet" to "the report's spelled reading stays on"
  -- the same structural check, inverted to guard the completed state rather than the pending one.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | measured on the committed tree in the record commit (finding 81's rule) |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --preset dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | Evidence is intact -- zero artifacts re-frozen |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 450 tests collected |
| Python | `.venv/bin/python -m pytest -q` | 519 passed |
| Falsification, full sweep | recorded in the next commit, on the sha it ran on | pending |
| CI on the pushed head | recorded in the next commit, from the runner's own logs | pending |

## 6. Numerical validation

No measurement is published and none moved.

* **99** declared plants, from the list; the sheet's annotation and its guard are the two ends.
* **519 / 450** -- the runner's pytest step and the offline probe. #91 is checked on the runner's own
  numbers in §5's CI row.
* **103** register entries; #95 is amended closed: the rollout is complete and the residue is #102's
  recall boundary.
* **Zero** artifacts re-frozen; the report's record is now bundle `ec60f84dd5b1`, PDF `5e29cb181315`.
* The venv lost its oracle packages mid-phase (a parallel `uv sync` without the extra) and was restored
  with `uv sync --frozen --extra oracles`; `uv.lock` is untouched, which is the instrument that says the
  tree's declared dependency set did not move.

## 7. Remaining limitations

* **#95 is closed within the rule.** #102 stands: the inventory's recall on prose is bounded by the
  nouns it lists and the modifiers it allows, and finding 84(c) names where that bites next -- an
  artifact index is the document whose job is counting, and its unlisted nouns (`eight cards`) are the
  likeliest home of the next stale number.
* **#97 is no longer hypothetical.** The ceiling has one consumer, the digits fallback is one decision,
  and the next prose count above twenty-six will have to make it again -- or the table gets extended,
  which is the open entry's subject.
* **#98 and #99 stand.** Eighteen of this phase's owners are credited by source-presence, the mechanism
  #98 describes; the relation-owned growth sentence narrows the exposure for one claim but fixes
  nothing general.
* **The ten declarations are hand-judged**, as #101 recorded for the sheet's five. The report's prose is
  older and more idiomatic; a reader who disagrees with any of the ten can promote it to an owner, but
  nothing forces the question again.

## 8. Technical debt registered here

| Entry | What it records | Why it is a limitation and not a defect |
|---|---|---|
| #95 (amended closed) | the rollout complete: 63 markdown + 45 report claims classified 5/5/11, 18/10/17 | the residue is #102's recall boundary, not an unclassified claim |
| finding 84 | three false counts in the report, the relation-shaped fix, and the ceiling's first forced fallback | recorded because the class -- prose that restates a derivation -- was invisible until the spelled reader existed |
| #97 (sharpened) | the ceiling's first consumer chose digits over a table extension | the design question the entry left open now has one data point |

## 9. The gate

Closed when the 99-plant sweep runs on the committed tree with no line at any other status and the tree
clean afterwards; when CI's three jobs are read from their own logs on the pushed revision and #91 is
checked on the runner's numbers; when the register, the audit, the scope table, the matrix, the sheet
and the report agree on the plant count, the register size and the test pair, each from its own
producer; and when each of the three corrected counts is shown load-bearing by a plant that reintroduces
the false value. A record checks the revision it names: the sweep and CI rows land in the commit after
this file, on the sha the runner built.
