# Phase 45 — Ownership credit is checked in the owner's syntax, and the invented credit dies

Date: 2026-10-15. Predecessor: Phase 44 (`fff4e03`, recorded in `f434a83`, CI run `38755973431` green on
the former). No version was bumped; `v1.8.0` remains the latest release.

## 1. Completed

The claim inventory's credit mechanism -- "this prose claim is owned by that guard" -- is verified
structurally. `_pattern_is_owned_by(pattern, owner, holder)` resolves the named function in the named
holder file, walks that function's body **plus the same-file helpers it calls** plus the module-level
structures the body reads, and requires the pattern to be a string constant of one of those. The old
check, `pattern in holder_source`, is retired, and with it **#98** closes.

The measurement that made the change concrete, run before anything moved: of **84** credits,
**68** lived in the owner's body, **8** in a structure it reads -- and **8 failed**, of two kinds:

| Defect | Entries | What the old check did |
|---|---|---|
| wrong reader named | `re-frozen (\w+) times`, `those (\w+) committed files`, `same (\w+) readings give`, `collects\s+(\d+)\s+tests\s+without\s+it` | passed: the pattern text is in the file, in the *sibling* function that really reads it (Phase 41's own misattribution) |
| no reader at all | `(\d+) benchmark-suite members executed` | passed: the pattern text is in the file *by being in the table itself* |

The four misattributions are corrected. The sheet's `19/19 benchmark-suite members executed` is now
searched by the registry guard itself, both slash halves compared with the registry's size, so the claim
the invented entry gestured at is a checked claim. The derivation entries' patterns live in
`_quoted_identity_floor`, a helper their guard calls; the check follows same-file calls, which is what
keeps those credits real without inlining the helper.

## 2. Assumptions this rests on

* Substring matching in the constant check (`pattern in constant`) is deliberate: the report's table
  deliberately admits fragments of a pattern its owner holds, and `in` covers fragments in either
  direction.
* The call closure is same-file and module-level only. A guard that delegates to a helper in another
  file would still red; no such guard exists in either table, and the check names the file it walked.
* `re.search` with a compiled-pattern variable is not followed -- only `Name` calls into same-file
  functions are. The patterns in the tables are matched against literals by construction.
* No measurement was published and none moved; the report was not re-typeset (the `.tex` is untouched).

## 3. Files changed

* `tests/python/test_artifact_metadata.py` — `_pattern_is_owned_by` with the call closure; both
  inventory guards call it; four owner names corrected; the suite-members guard gains the sheet's `N/N`
  comparison; the benchmark-members entry moves from the report's table to the markdown table, where the
  prose it matches lives.
* `scripts/mutation_plants.py` — 3 plants (102 → 105).
* `docs/limitations.md` — #98 amended closed; `docs/integrity_audit.md` — finding 85;
  `docs/project_scope.md` — §9 rows for Phases 44 and 45 (the 44 row had been omitted from that table
  when the phase landed; added here with its own content, not backdated silently).
* `docs/interview_defense.md` — the sweep annotation.

## 4. What the phase learned, including about its own first design

* **A check over a corpus that contains the checker is vacuous, and this one had been since it was
  written.** The verbatim check's founding comment promised that "an owner invented here fails the
  verbatim check above rather than passing quietly" -- and the mechanism it named could not deliver that
  promise, because the table satisfies a substring test over its own file. Finding 82 found the same
  shape in a producer (`--quick` counted its own searcher); this is the ownership credit's version, and
  the fix is the same principle: structure, not presence.
* **The invented entry was found by measurement, not by reading.** Nobody reading the table would have
  flagged `(\d+) benchmark-suite members executed` -- it looks plausible, it matches real prose, its
  owner name is a real guard. What exposed it was asking each credit *where its pattern lives relative
  to the function that supposedly reads it*, which is the question the old check never asked. The
  register's doctrine -- measure before fixing -- is what turned "tighten the check" into "find the
  four misattributions and the one dead credit".
* **The misattributions were the author's own.** Phase 41 added the three readings spellings and the
  `--quick` count and credited them to the names the *phase report* mentioned, not the functions the
  code put them in. Four phases of green gates passed them, because the check that would have caught
  the error could not fail. That is #98's cost stated as a number: the entries were wrong on the commit
  that wrote them.
* **The plants had to be two-sided against the old mechanism.** Naming a non-existent guard leaves every
  pre-Phase-45 check green -- the pattern is still in the file -- and reddens only the syntax check;
  moving a search away from its pattern leaves the dead-pattern check green for the same reason. Plants
  that merely redden under the new check would not have shown the old one was blind; these show it.

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

* **105** declared plants, from the list; the sheet's annotation and its guard are the two ends.
* **84** credits, each now verified in its owner's syntax: 68 in the body, 8 through the call closure or
  a named structure, 8 corrected by this phase -- and none left that the old check alone would have
  passed.
* **519 / 450** -- unchanged; #91 is checked on the runner's numbers in §5's CI row.
* **102** register entries, unchanged: #98 amended closed in place.
* **Zero** artifacts re-frozen; the report *was* re-typeset, because this phase's own report file moved the artifact index's owned count (`forty-six report files`) -- the same self-referential cascade Phase 43 recorded, one phase later. Its record is now bundle `a46a433521ea`, PDF `882e6ffc5e23`.

## 7. Remaining limitations

* **The call closure is one file deep and name-based.** A guard delegating to a helper in another file,
  or calling through an attribute (`self._read(...)`), falls outside it; the check reds rather than
  guessing, which is the safe direction, and no current credit needs more.
* **#99 and #101 stand**, as does #102's recall boundary. With #95, #97, #98 and #100 closed, the
  remaining register is the recall instrument (#102), the precision question (#101), and the row-citation
  meaning question (#99).
* **The citation class (`cited`) still checks existence, not meaning** -- #99 unchanged by this phase.

## 8. Technical debt registered here

| Entry | What it records | Why it is a limitation and not a defect |
|---|---|---|
| #98 (amended closed) | the vacuous substring credit replaced by a structural one; the four misattributions and the invented entry it exposed | the entry keeps the shape: a check over a corpus containing the checker |
| finding 85 | the invented credit, the misattributions, and the two-sided plants | recorded because the class -- a promise a substring check cannot keep -- generalises to every "is X in Y" gate over a file that contains the gate |
| -- | no new entries opened by this phase | the residual in §7 is #99/#101/#102's, already registered |

## 9. The gate

Closed when the 105-plant sweep runs on the committed tree with no line at any other status and the tree
clean afterwards; when CI's three jobs are read from their own logs on the pushed revision and #91 is
checked on the runner's numbers; when the register, the audit, the scope table and the sheet agree on the
plant count and the test pair, each from its own producer; and when the credit mechanism is shown
two-sided against its own history -- an entry naming a guard that does not exist, and a search moved away
from its pattern, each reddening the syntax check while every pre-Phase-45 check stays green. A record
checks the revision it names: the sweep and CI rows land in the commit after this file, on the sha the
runner built.
