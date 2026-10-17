# Phase 51 — a counted noun cannot also be the modifier (#104 closes)

Date: 2026-10-17. Debt item: `docs/limitations.md` #104, opened by Phase 50 and closed here; finding 89
registered against this phase's own instrument.

## 1. Completed

* **Property 9 of the extractor self-test, and the rule it tests.** The modifier slot now refuses a word
  that is itself on the noun list, and the refusal sits *inside* the optional group so the engine falls
  back to reading that word as the noun. `meets it at 60 markets spread over the $(d_1, v)$ plane` was
  extracted as `60 markets spread` -- a claim of sixty *spreads* about a sentence counting sixty
  *markets* -- and is now extracted as `60 markets`: right count, right object, nothing deleted.
* **The corpus effect is one phrase, pinned by name.** With the closed-class block held constant on both
  sides, the collision half moves exactly `("paper/technical_report.tex", "60 markets spread")` to
  `("paper/technical_report.tex", "60 markets")` and touches no other document. Distinct-phrase counts
  are unchanged (24 / 19 / 40 / 31 / 84 = **198**), because the report trades one phrase for another.
* **Collisions re-measured after the fix: 0 of 198.** The probe that found the instance is the same probe
  that now reports the class empty, so the entry closes on the measurement rather than on the assertion.
* **Placement proved destructively, because the wrong placement was built first.** The same lookahead
  hoisted in front of the optional group refuses the noun as well as the modifier and loses **92** phrases
  across the corpus -- 15 of them README's gold, `160 runs` among them, which is what makes the census,
  not the property, the guard that sees it. Both constructions are asserted, and both directions have a
  plant.
* **Finding 89**: one of the assertions written for this property could not fail. See §4.
* **3 plants (123 -> 126)**: drop the collision block (the spreads reading returns); hoist it over the
  noun (README's real counts vanish, caught by the census); reword the report's sentence so the pinned
  pair goes stale.
* **The cascade**: plants 123 -> 126 in the rehearsal sheet's annotated command line and its plant
  anchor, `fifty-one report files` -> `fifty-two` in the report and in the plant that owns it, and the
  report re-typeset. The register stays at 104 entries -- #104 was amended closed, not replaced -- and
  the test pair stays 526/457 because the property joined an existing guard instead of opening a new one.

## 2. Assumptions this rests on

* A noun-list word in front of another noun-list word is ambiguous in exactly one direction in this
  register: the first is the counted thing and the second is doing verb or participle work
  (`markets spread over`, `observations spanning`). Refusing the modifier reading therefore *adds*
  information rather than dropping the claim, and the measurement says so: 1 phrase moved, 0 lost.
* The refusal is generated from `_REPORT_NOUN_BODY` rather than from a copied list, so growing the noun
  list grows the collision rule with it. That is also #104(b)'s reason the fix was not taken in Phase 50:
  the guard's blast radius then moves whenever a phase adds a noun, and property 9's pinned pair is what
  makes such a move loud instead of silent.
* The census still has no third bucket. With the class refused, the only known misattribution is gone; a
  future document's enumeration may find a shape the noun-pair rule cannot catch, and #104(d) records
  that the queue is where it would show up.

## 3. Files changed

`tests/python/test_artifact_metadata.py` (`_REPORT_NOUN_BODY`, `_COLLISION_BLOCK`, the new
`_CLAIM_TAIL`, property 9 and its `rule_hits` helper), `scripts/mutation_plants.py` (3 plants and the two
anchors that track the counts), `docs/limitations.md` (#104 amended closed),
`docs/integrity_audit.md` (finding 89), `docs/interview_defense.md`, `docs/project_scope.md` §9,
`paper/technical_report.tex` with its rebuilt PDF and `build.json`, and this report.

## 4. What the phase learned, including about its own first design

* **A vacuous assertion in the instrument that polices vacuity.** The last control of property 9 was
  written as `assert (doc, phrase) not in {text for _, text in hoisted_lost}`. Projecting a set of pairs
  to phrases leaves a set of `str`, so a tuple is never a member, and the `not in` turned that into a
  permanent pass. It ran green on the tree that contained it. Nothing in the repository can catch this
  shape -- a passing test is not evidence about an assertion that cannot fail -- and what caught it was
  re-reading the assertion's *types* while writing the register amendment and asking whether its
  direction matched the measurement. It did not: the hoisted rule deletes the markets phrase too, so the
  corrected assertion is `... in hoisted_lost`, which is both true and falsifiable. Finding 89 records
  the rule adopted here: assert against the pair set, and if a projection is wanted, project the needle
  as well.
* **The reconstruction error was the lesson, not an aside.** Placing the lookahead outside the optional
  group is a one-character difference from the correct form and it silently deletes 92 real counts. Had
  the phase asserted only "the fix removes `60 markets spread`", both placements would have passed. What
  distinguished them was writing the *wrong* construction into the test as a comparison object, which is
  the same move as #100's `loosened()` and Phase 45's helper-closure plant: the control is the other
  program, not a comment about it.
* **The guard that sees a deletion is not the guard that wrote the rule.** The hoisted placement is
  detected by README's census, because 15 of its 24 gold phrases disappear from a document the collision
  rule never touches. A rule change whose only corpus evidence lives in one sentence of one pending
  document needs a second surface with a denominator, and Phase 50's census happened to be that surface.
* **Phase 50's §8 said the third bucket had to be built before the report was censused.** Measurement
  reversed the order: the misattribution was refused by the rule, so the bucket has nothing to hold and
  censusing became the way to look for shapes the class rule cannot express. Registering a mechanism as
  debt is a hypothesis about the next failure, and the next failure did not repeat it.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 195 files already formatted on this tree; the record commit quotes the `git archive` export (finding 81's rule) |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --test-dir build/dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | Evidence is intact -- the report bundle moved, no artifact re-frozen |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 457 tests collected |
| Python | `.venv/bin/python -m pytest -q` | 526 passed in 185.02s |
| Falsification, full sweep | recorded in the next commit, on the sha it ran on | pending |
| CI on the pushed head | recorded in the next commit, from the runner's own logs | pending |

## 6. Numerical validation

| Figure | Value | Producer |
|---|---|---|
| Phrases the collision rule moves | 2 (one removed, one read in its place) | property 9's `shifted` set |
| Documents the rule touches | 1 of 5 (`paper/technical_report.tex`) | the same set |
| Distinct phrases, five documents | 198, unchanged | `_census_hits` per document |
| Noun-pair collisions after the fix | 0 of 198 | the collision probe re-run over the corpus |
| Phrases the hoisted placement loses | 92, of which 15 in README.md | property 9's `hoisted_lost` |
| Closed-class words in the slot | 2 fired, both refused (`and`, `between`) | property 8's blast radius |
| Plants | 123 -> 126 | `run_mutation_suite.py --list` |
| Register entries | 104, unchanged | `_numbered_limitation_entries()` |
| pytest with / without `oracles` | 526 / 457, unchanged | the runner, and `measure_offline_collection.py` |
| Phase report files | 51 -> 52 | `docs/phase_reports/*.md` |

## 7. Remaining limitations

* The census covers one of five documents; 174 phrases remain pending, and #104(d) is the reason that
  queue is now a search for shapes the class rule cannot refuse rather than a formality.
* Nothing measures whether a noun-list word *elsewhere* in the tail can do verb work; the refusal is on
  the modifier slot only, because that is the position the defect was observed in.
* The class rule's blast radius moves with `_REPORT_NOUNS`. A future noun could make a phrase collide
  that today does not, and the pinned pair then reddens -- correctly, but the phase that adds the noun
  has to re-read the report sentence to know why.

## 8. Technical debt registered here

* **Finding 89** is a habit rather than a queue item, and it is written where the reader of the next
  projection will meet it: an assertion whose needle is a tuple and whose haystack is a projection to
  strings cannot fail.
* No new limitation entry. #104 closed on the measurement; #101 and #103 stay open with the debts they
  already name (174 pending phrases and the untested declarations; the static plant-guard pairing).

## 9. The gate

Nothing here is a release. The claim is bounded and measured: one phrase moved, 0 collateral, the wrong
placement of the same lookahead shown to delete 92 real counts, and the instrument that polices that
deletion is a guard that was written for a different document. The phase's own defect -- an assertion that
could not fail -- is recorded as finding 89 with the two-line probe that proved it, and the corrected
assertion is both true on the data and able to fail.
