# Phase 36 — a band that needed no unit, and the exemptions that stopped being directories

Date: 2026-10-13. Debt closed: the two items on the remaining-debt list that shared one root -- the band
census could not see a spread written without its multiplication unit, and it did not read the two document
families that were exempted by path prefix. Debt taken on from this phase's own measurement: none new; the
deferred cost of the widened shape is stated in the guard and in finding 71 rather than registered, because
it is a consequence of a decision rather than unwritten work.

## 1. Completed

1. **`_band_pairs` reads a band without its unit.** Two new shapes alongside the anchored one: a dash
   between two bare decimals with nothing else in the gap but quotation and spacing (`7.77–10.31`,
   `` `0.42`–`0.51` ``), and the spoken form with its lead word (`between 0.42 and 0.51`). Neither admits a
   unit into the gap, so a band carrying `×` on both edges still belongs to `_BAND_SHAPE`, which is stricter
   about what sits between the units.
2. **The first permissive version was rejected by the repository's own evidence.** It paired
   `10.31× and 0.495×` -- two readings of one run, not a spread -- which is the exact phantom
   `docs/integrity_audit.md` already records an earlier gap-wide detector producing, beside `8.378× / 0.5656×`.
   The counter-example is in the corpus, so the control was measured against it rather than invented.
3. **Measured before written, because a detector's blast radius is the question.** Over the tree's 81
   documents the united shape finds 68 decimal pairs and the two loose shapes find 52 more. Three of those 52
   share an edge with a policed band, and **all three are in this report** -- the document that wrote the rule,
   quoting the bands it had to discuss. The widened census's first catch was its own phase, and the honest
   disposition of that is a declaration with a reason rather than rewording the sentences until the guard stops
   seeing them. Everything else about the widening is latent: a rule a document could previously leave by
   deleting two characters, with a reachable red proved by
   `unlisted-document-states-a-band-without-its-unit`, which writes an unlisted document printing the
   planted `7.77–8.70` -- a spread the old shapes could not see at all, and the reason this report
   itself prints a superseded band.
4. **The prefix exemptions are gone.** `_candidate_band_documents()` no longer excludes anything; the nine
   files in `docs/phase_reports/` (6 printers of 36) and `docs/release_bodies/` (3 of 6) are each named with
   the revision they record, and the census holds every one of them to printing a pair that is *not* today's
   band -- the property that makes a dated exemption expire when the document is brought up to date.
5. **A third kind of dated record, self-terminating by construction.** `TAGGED_BAND_RECORDS` holds the two
   files that print only the current band because the release they record is the one that produced it
   (`docs/phase_reports/phase-30-v1.8.0.md`, `docs/release_bodies/v1.8.0-body-2026-10-09.md`). Their exemption
   is granted while, and only while, they keep printing today's band; the first re-freeze that widens it
   reddens the guard and moves them to the superseded list, which is how the two `v1.7.0` body drafts got
   there. A file cannot sit in both lists, and the guard says so.
6. **Two new plants** on top of Phase 35's six: the unlisted unit-less document, and
   `record-of-todays-band-quietly-states-a-superseded-one`, which rewrites one tagged record to a stale
   spread to prove the new status is checked rather than assumed. Plant count 68 → 70, and the rehearsal
   sheet's command annotation moved with it (`# 70/70 planted defects rejected`).

## 2. Assumptions this rests on

- **Recognition, not enforcement, is most of what the widening buys.** Outside this phase's own report no
  document wrote a band without its unit, so the shape exists so that a future one cannot leave the census by
  deleting two characters. A rule with little current red is only as good as its plant, and this one has one.
- **"Shares an edge with a policed band" stays the predicate that decides whether a pair is a speedup
  claim.** Without it the loose shapes fire 52 times across prose about slopes, percentiles, version
  numbers and radius grids, of which three pairs are a policed band's and all three are quoted by this
  report. The consequence is accepted rather than hidden: an edge that later joins `SPEEDUP_BANDS` can
  recruit pairs that are inert today.
- **A dated record that states today's band is not stale, and that is a fact about the release, not about the
  document.** Encoding it as an expiring exemption rather than as a permanent family rule is what makes the
  list notice its own obsolescence.
- **The census's edge set is the rounded band** (`SPEEDUP_BANDS`), so the raw edges a phase report quotes
  (`7.774`–`10.306`) are read as a pair but do not share an edge and are therefore not claims the census
  polices. `docs/phase_reports/phase-32-…`'s dated reason names that choice.

## 3. Files changed

| File | What moved |
|---|---|
| `tests/python/test_artifact_metadata.py` | `_LOOSE_DASHED`/`_LOOSE_SPOKEN` (new) and the three-shape `_band_pairs`; `_candidate_band_documents()` with no exclusions; `DATED_BAND_RECORDS` 4 → 11 with per-file reasons; `TAGGED_BAND_RECORDS` (new, 2 entries); `BAND_EXEMPT_FAMILIES` deleted and its family loop replaced by the tagged-record property; the census docstring's account of its own reach |
| `scripts/run_mutation_suite.py` | two plants, and the sheet's sweep annotation re-keyed to 70/70 |
| `docs/integrity_audit.md` | the Phase 36 addendum and finding 71 |
| `docs/project_scope.md` | the §9 row |
| `docs/interview_defense.md` | the state line and the sweep annotation |
| this file | the record |

## 4. What the phase learned, including about its own first design

1. **The permissive rule was wrong in a way the repository had already written down.** Reading any
   mark-between-decimals produced `10.31× and 0.495×`, and this audit file carries an earlier phase's finding
   that the same pairing is what a gap-wide detector invents. The correction came from searching my own
   corpus for the counter-example rather than from reasoning that "and" is a common conjunction -- which is
   the difference between a rule that has been tested against the text and one that has been tested against
   intuition.
2. **A widening whose only current catch is its own phase is a promise, and the plant is what keeps it.**
   Measured: 52 pairs the old shapes could not see, three of them policed edges, and all three inside this
   report -- which the census duly reported as a document stating a spread nothing owned. The temptation in a
   documentation phase is to call such a change an improvement in coverage; it is an improvement in
   *reachable* coverage, and the distinction is exactly what the falsification harness is for. Declaring the
   report, rather than rewording its quotations until the guard stops seeing them, is the part worth
   copying.
3. **The two blind spots were one blind spot.** The exempt families were where every unit-less band in the
   corpus lives (`between 0.42 and 0.51`, `7.774`–`10.306`), so a document could have escaped policing by
   being in the wrong directory or by dropping a character, and neither escape would have been visible.
   Closing only the shape would have left the directory rule to swallow the cases the new shape can now read.
4. **Naming the exempt files made a new kind of dated record show up.** Two of the nine print only today's
   band, and the superseded-pair property cannot describe them. Rather than bend the property, the phase gives
   them a status with its own falsifiable condition -- and the condition is what retires it. That is the
   second time in three phases that enumerating a list produced a category the rule had not anticipated
   (Phase 35's rate sentence did the same).

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| C++ | `uv run ctest --preset dev` | 100% tests passed out of 204 |
| Catch2 | `./build/dev/quantrisk_tests` | All tests passed (548368 assertions in 203 test cases) |
| Identity | `uv run quantrisk validate` | 7/7 checks passed |
| Python suite | `uv run pytest -q` | `509 passed in 135.89s (0:02:15)`, no skips |
| Offline lane | `uv run python scripts/measure_offline_collection.py` | `collected: 440`, `module_skips: 4`, `collection_errors: 0` |
| Docs + harness lanes | `uv run pytest tests/python/test_artifact_metadata.py tests/python/test_mutation_suite.py -q` | 68 passed |
| Census, widened | the guard's own unaccounted/dated/tagged checks over 81 documents | 26 printers, all named: 12 in `RANGE_DOCUMENTS`, 12 in `DATED_BAND_RECORDS` (11 from this phase's renaming, one of them this report), 2 in `TAGGED_BAND_RECORDS`. The first run said otherwise: `docs/phase_reports/phase-36-…` was reported as stating a spread nothing owned, which is the renaming doing its job on a file added minutes earlier |
| Loose shapes, measured | enumeration of `_LOOSE_DASHED`/`_LOOSE_SPOKEN` matches over the tree | 44 pairs found, 0 sharing a policed edge; the phantom `(10.31, 0.495)` reproduced by the permissive gap and refused by the shipped one |
| Lint | `uv run ruff check .` / `uv run ruff format --check .` | All checks passed! / 175 files already formatted — a walk of this directory, not a census (finding 62(d)); one docstring re-wrap whose tool proved the change was whitespace-only |
| C++ format | `uv run clang-format --dry-run -Werror` over the 77 tracked `.cpp/.hpp/.h` | 0 diagnostics, exit 0 |
| Types | `uv run mypy python/quantrisk` | Success: no issues found in 23 source files |
| Evidence | `uv run python scripts/verify_evidence_manifest.py` | 0 missing, 0 unlisted — Evidence is intact |
| Report render | not re-run | No render input changed: the tex, its bibliography and its figures are untouched, and `test_the_committed_report_pdf_is_bound_to_the_sources_that_rendered_it` is green in the lane above, which is what makes "unchanged" a measured claim rather than an assertion |
| Anchor census | `test_every_declared_mutation_names_one_unique_anchor_and_a_guard_that_exists` | 70 declared plants, every anchor unique in its file, every guard present in its named file |
| Falsification, full sweep | `uv run python scripts/run_mutation_suite.py` on the committed tree | pending — recorded in the follow-up commit |
| CI on the pushed head | `gh api …/commits/<sha>/check-runs` after the push | pending — recorded in the follow-up commit, which is the only place its run id can come from |

## 6. Numerical validation

No measurement is published. What moves is the plant count (70, from the list) and the census's account of
itself; the bands, spreads, test totals and register size are unchanged from Phase 35 because this phase
changed which documents and spellings a guard can *see*, not what any artifact measures. The figures quoted
in §1 and §5 -- 81 documents, 68 united and 52 loose pairs, 6 of 36 and 3 of 6 printers, 26 printers
accounted for -- are counts taken by the enumerations in this phase's probes
(`build/probe_band_unities_and_exemptions.py` and the shape-by-shape tally), not carried over from prose.

## 7. Remaining limitations

- **The widened shape has no living example.** Its coverage claim is a reachable red, verified by plant. If a
  future phase prefers prose to be uniform, the alternative is to require the unit in documents and reject the
  unit-less spelling outright -- a style rule the census cannot enforce without a rule like this one.
- **`SPEEDUP_BANDS` is a set of four numbers, and the edge predicate is the whole of the classification.**
  A future edge that collides with a common radius or slope value would recruit inert pairs into findings.
  The guard would then demand names, which is the correct outcome but not a cheap one; nothing predicts the
  collision today.
- **Two dated records are exempt because they agree with the present.** That is honest only while it holds,
  and the guard enforces it, but it does mean the census's "every printer is named" property is currently
  satisfied for those two by a different argument than for the other nine.
- **Carried from Phase 35, untouched:** the band census still searches documents as written, so #96's
  folding question applies to it; spelled counts stay outside the inventory (#95); #93's bytecode boundary and
  #94's plant-in-its-own-file wall are unchanged.

## 8. Technical debt registered here

Nothing new. The two deferred consequences -- a future edge collision recruiting dated pairs, and a rule
whose red is reachable only by plant -- are stated in §7 and in finding 71, where a reader of the guard will
meet them, rather than added to a register that counts only work not yet done.

## 9. The gate

Procedure: `CONTRIBUTING.md` §4, run in its fixed order. Gates were executed on the working tree and every
result above is measured output; the report render was not re-run because no render input changed, and the
binding guard's green is the evidence for that rather than this sentence. The falsification sweep runs on the
committed tree, because a plant edits files and restores them.

No release is proposed: `v1.8.0` remains the latest tag, and this phase changes which prose a checker can
read, not what any published artifact reports. The next phase takes the promotion of
`build/rewrap_docstrings.py` into `scripts/` with its own test and plant, and extends the folded reading that
#96 opened to the guards that still search raw text.
