# Phase 32 — the list that polices a band, and the release date a citation never had

Date: 2026-10-11. Debt closed: the two items `docs/phase_reports/phase-30-v1.8.0.md` §8 registered
instead of taking on — the completeness of `RANGE_DOCUMENTS`, and a producer for `date-released` in
`CITATION.cff`. Scope agreed with the user before the work: these two items and nothing else.
No experiment, no core file and no frozen artifact moved; the phase's output is two guards, three
plants, two corrected documents and one register entry.

## 1. Completed

1. **A producer for `date-released`.**
   `test_the_release_date_the_citation_declares_is_the_tag_that_cut_it` reads the field out of
   `CITATION.cff` and compares it with `git for-each-ref`'s *tagger* date for the tag of the same
   version. The distinction is the whole content of the guard: the commit's author date records when
   work was written and the tagger date records when it was released, and the field claims the second.
   Measured against the tree: nine annotated tags, `v1.0.0` on 2026-09-28 through `v1.8.0` on
   2026-10-09, and `CITATION.cff:31` says `2026-10-09` — the comparison holds for every tag that exists.
   Two skips, both named in the test: a clone carrying no tags (what `actions/checkout` at depth 1
   produces), and the current version's tag when the release has not been cut yet — the tag is cut
   from the commit that carries this guard, so demanding it would demand the future.
2. **A census over the documents that state a speedup band.**
   `test_every_document_that_prints_a_speedup_band_is_policed_or_declared_dated` enumerates candidates
   from the tree rather than from a list — the README, `paper/technical_report.tex` and `docs/**.md`,
   less two families exempted because every file in them is a dated record — and requires each document
   that prints a spread sharing an edge with a policed band to be either policed
   (`RANGE_DOCUMENTS`, now a dict of what each document owes) or declared dated (`DATED_BAND_RECORDS`,
   each with a reason). Three sides keep it honest: a declaration must still print a *superseded* pair,
   an exempt family must still contain a printer, and the census shares its detector with the membership
   test so the two cannot disagree about what a printed pair is.
3. **The detector was rebuilt before it was trusted.** The gap-wide shape the membership test used
   pairs any two decimals within sixteen characters, which is harmless when the question is "is this
   one pair present" and false when the question is "which documents state a band". `_BAND_SHAPE` now
   requires a multiplication sign on both edges and a range mark between them, and additionally reads
   the one prose spelling the report uses ("between … and …") when it carries the unit.
4. **Two present-tense sentences the census found were corrected.** `paper/technical_report.tex`
   attributed `7.77×`–`8.70×` and "an `11.9%` spread" to "thirteen committed re-freezings"; the tree
   holds twenty-two readings spanning `7.77×`–`10.31×` (32.6%) with the NumPy baseline between 46M and
   110M paths/s, and the paragraph now says so. Living prose, so it was edited in place.
   `docs/release_notes_v1.6.0.md` wrote that both ratios "remain inside the pinned history range"; a
   release note is a record of its own tag, so it received a dated amendment on 2026-10-11 and its
   original sentence is untouched.
5. **Two dated records were declared rather than policed.** `docs/project_scope.md` prints
   `0.42×`–`0.57×` inside the Phase 28 row of §9 — what that phase's re-freeze moved the committed band
   to — and `docs/release_notes_v1.0.0.md` prints `0.42×`–`0.48×` as the spread of the four dated runs
   behind `v1.0.0`. Both are true of their own date and would be falsified by a membership test.
6. **Three plants (56 → 59), one for each new failure mode**: an unpoliced band in a model card no
   guard has ever read, a dated record quietly brought up to date, and a citation naming a date no tag
   was cut on. Each was run individually before the sweep: anchor unique, bytes changed, named guard
   red, sha-verified restore, guard green again.
7. **The cascade the two new guards caused was driven by the guards**, not typed: pytest 500 → 502 and
   the offline collection 431 → 433 across four documents and five plant anchors, and the limitations
   register 91 → 92 across six (README, validation matrix, rehearsal sheet, report in three phrasings,
   and the two release notes the register-count guard treats as living).

## 2. Assumptions this rests on

- An annotated tag's tagger date is the release date. The repository cuts every tag with `git tag -a`
  as part of the release procedure, so the tag exists where the release does; a lightweight tag would
  carry no tagger date and the guard would report the version as untagged.
- The committed history of the speed artifact is the population the documented bands describe. That is
  what `test_the_documented_speedup_ranges_match_the_committed_history` checks wherever history is
  present; the census inherits it.
- A document outside the two exempt families is making a living claim unless it is declared dated. The
  exemptions are asserted to be load-bearing rather than assumed, which is what makes the assumption
  checkable instead of convenient.
- `RANGE_DOCUMENTS` names per document which of the two ratios it is obliged to state, because
  `docs/findings.md` and `docs/portfolio_audit.md` quote only the NumPy one. That shape is the user's
  claim about those documents, inherited from before this phase and unchanged by it.

## 3. Files changed

| File | Change |
|---|---|
| `tests/python/test_artifact_metadata.py` | two new guards, `_BAND_SHAPE`/`_band_pairs`, `RANGE_DOCUMENTS` as a dict with per-kind obligations, `DATED_BAND_RECORDS`, `BAND_EXEMPT_FAMILIES` |
| `scripts/run_mutation_suite.py` | three plants; five anchors re-keyed to the moved counts |
| `paper/technical_report.tex` | the performance paragraph's band, count, spreads and baseline range corrected; test totals and register count synced |
| `paper/technical_report.pdf`, `paper/technical_report.build.json` | rebuilt by the producer after the prose settled |
| `docs/release_notes_v1.6.0.md` | dated correction appended; nothing above it rewritten |
| `docs/project_scope.md` | §9 Phase 32 row, refresh date 2026-10-11 |
| `docs/limitations.md` | #92 opened; the living register count synced |
| `docs/integrity_audit.md` | Phase 32 addendum, finding 64 |
| `docs/interview_defense.md` | state line to Phases 0–32, test counts and sweep annotation synced |
| `README.md`, `docs/reproducibility.md`, `docs/validation_matrix.md`, `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md` | counts the guards moved |

## 4. What the phase learned, including about its own first design

- **A guard's detector has to be as careful as the question it is asked.** The first census run used
  the membership test's loose regex and named four documents, two of them for pairs that do not exist:
  `8.378×` / `0.5656×` is two readings of one run separated by a slash, and `10.31×` … `and 0.495×` is
  one sentence about two ratios. Requiring the unit on both edges and a range mark between them killed
  every false pair and kept every real one, and the pair list then matched the hand-measured census.
- **Edge-sharing, not pair equality, is the right predicate for a census.** A document whose band has
  drifted (`0.42×`–`0.57×`) is precisely the one a name-list guard loses, and a predicate that only
  fires on an exact current pair cannot see it. The cost is that a document quoting an unrelated
  `0.42×`–`0.51×` would be pulled in — accepted, because the census's job is to ask a question of the
  document, not to answer it.
- **Half of what the census found was not a defect.** Two of the four unaccounted printers were honest
  dated records, and the guard's answer to that is a declaration list whose entries have to keep
  printing something superseded. The distinction the phase had to get right is between correcting living
  prose (the report) and amending a record (the release note), which is the same rule finding 55 produced
  for release assets, applied one level down.
- **The rewrap tool had three bugs before it did its job, and the proof was what caught them.**
  `build/rewrap_docstrings.py` normalises docstring line breaks to clear E501 and refuses to write
  unless every docstring's word tuple and the whole file's AST (with docstring whitespace folded) are
  unchanged. Its first version treated every four-space-indented line as a literal block — the docstring
  indent — and did nothing; its second emitted a bullet's hanging indent prefixed with the marker
  character, which *added words* and was refused by the word check; its third merged consecutive bullets
  into one paragraph, also caught by that check. A hand rewrap of nine paragraphs is where a dropped
  word goes unnoticed; the proof is what made the tool usable.
- **The count cascade is the guard working, not noise.** `test_mutation_suite.py` failed on four anchors
  the count sync disarmed, exactly as it did in Phase 21, and the one-pass enumeration over all 59
  declared plants is what shows the remainder sound: 59 declared, 57 file-backed (two create their own
  file at run time), 0 missing or non-unique.

## 5. Exact test results

| Gate | Command | Result |
|---|---|---|
| Python | `uv run pytest tests/python -q` | `502 passed in 133.80s` on the final tree |
| Offline lane | `uv run python scripts/measure_offline_collection.py` | `collected: 433`, `module_skips: 4`, `collection_errors: 0`, exit 0 |
| Docs + harness lanes | `uv run pytest tests/python/test_artifact_metadata.py tests/python/test_mutation_suite.py -q` | 61 passed on the final tree. Before the corrections the same lanes were red in three places, each replayed against `HEAD` content: the census named `docs/project_scope.md` and `docs/release_notes_v1.0.0.md` as unaccounted, and membership rejected `paper/technical_report.tex` (both ratios) and `docs/release_notes_v1.6.0.md` (the Python band) |
| C++ | `uv run ctest --preset dev` | 100% tests passed out of 204 (7.93 s) |
| Catch2 | `./build/dev/quantrisk_tests` | All tests passed (548368 assertions in 203 test cases) |
| Identity | `uv run quantrisk validate` | 7/7 checks passed |
| Lint | `uv run ruff check .` / `uv run ruff format --check .` | All checks passed! / exit 0 both times. This machine's walk printed `171 files already formatted` while the same command on a `git archive HEAD` export printed `170`; the number is quoted as a walk of a directory, not a census of tracked files, per finding 62(d) — the two readings differ by one file and the delta was not chased, which is exactly why no guard compares these figures |
| Types | `uv run mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ format | `uv run clang-format --dry-run -Werror` over all 77 tracked `.cpp/.hpp/.h` | exit 0 |
| Producer | `uv run python scripts/build_report.py` | wrote the record: 6 sources, bundle `49f038ddbd84…`, PDF `fbe44353a5ff…`, 1,005,780 bytes; run twice more as the phase's own edits moved the tex |
| Render text | `pdftotext paper/technical_report.pdf` | carries `502 pytest tests with the validation`, `433 collected without them`, `92 recorded limitations`, `register contains 92 numbered entries`, `7.77×`–`10.31×`, `32.6` and `46M paths` — one occurrence of each |
| Evidence | `uv run python scripts/verify_evidence_manifest.py` | 0 missing, 0 unlisted — Evidence is intact |
| Band history | `test_the_documented_speedup_ranges_match_the_committed_history` | 22 committed measurements, `7.774`–`10.306` and `0.419`–`0.507`, pinned band `(7.77, 10.31)` / `(0.42, 0.51)` |
| Census | `_candidate_band_documents()` / `_speed_band_printers()` measured directly | 38 candidates, 16 printers, 12 policed, 4 dated, 0 unaccounted after the corrections; exempt families hold 5 and 3 printers |
| Anchor census | one-pass enumeration of every declared plant against the file it names | 59 declared, 57 file-backed, 0 stale |
| Falsification, the three new plants | `uv run python scripts/run_mutation_suite.py --only <id>` for each | each printed `caught`: guard red on the mutated tree, green after the sha-verified restore |
| Falsification, full sweep | `uv run python scripts/run_mutation_suite.py` on the committed tree, logged to `build/mutation-sweep-32.log` | pending — the sweep refuses a dirty target, so its verdict is a claim about the commit this report is landed in and is recorded in the follow-up commit, not here |
| CI | `gh api` on `commits/<sha>/check-runs` after the push | pending — not yet run at the time of writing |

## 6. Numerical validation

No new measurement is published. The figures the phase moves are the two test totals (502 / 433), each
produced by its own collector, and the band arithmetic quoted into the report, which was recomputed from
the 22 committed artifact revisions rather than copied from the documents: `7.774`–`10.306` gives the
`32.6 %` spread, `0.419`–`0.507` gives `20.8 %`, and the NumPy baseline's own range over the same
revisions is 46,486,278–110,122,785 paths/s. The freeze did not move: nothing under
`benchmarks/**/results` or `experiments/*/results` was regenerated, and the evidence-integrity guards
are what make that a check rather than an assertion. `paper/` is not a hashed directory, so the new
render and its record do not enter the manifest.

## 7. Remaining limitations

- **A band's percentage has no owner.** Four documents print "(32.6% spread)" beside a policed pair.
  Nothing derives it: the pinned band holds *rounded* edges, and the same arithmetic on them gives
  32.7 % and 21.4 %, so a guard would have to read git history — which the runner does not have.
  Registered as `docs/limitations.md` #92.
- **A band written without its unit is invisible to the census.** "between 0.42 and 0.51" carries no
  multiplication sign, and a detector that accepted bare decimals would report neighbour pairs as
  spreads. The report's own sentence was rewritten into the anchored form as part of the fix, so this
  corpus reads; a future document in the bare form would not be noticed, and the guard's docstring says
  so rather than claiming coverage.
- **The release-date guard cannot check anything on CI.** A checkout at depth 1 carries no tags, so the
  guard skips there with its named reason, and the plant that tests it is only decidable on a full
  clone. The field is owned where the history is.
- **Dated versus living is a judgement the guard cannot make for itself.** `docs/project_scope.md` and
  `docs/release_notes_v1.0.0.md` were declared dated because a reader can see the date each statement
  belongs to; nothing proves a future editor will not declare a present-tense sentence dated to escape
  the membership test. The load-bearing rule limits it — a declaration whose file prints only current
  bands is a failure — which constrains the escape rather than closing it.
- **The census reads markdown and the report only.** `docs/analysis/**.md` is inside `docs/**.md`, but a
  number stated in a figure, a CSV header or Python docstring is outside its corpus.

## 8. Technical debt registered here

- `docs/limitations.md` #92 — a band's spread percentage is transcribed, not derived, and the report
  inventory guard's noun list has no `spread`, `run`, `reading`, `re-freezing` or `path`, so the counts
  in the performance paragraph are classified by nothing.
- The exempt families are exempt by path prefix. A living document placed under `docs/phase_reports/`
  would inherit the exemption; the guard detects a family that has stopped containing any printer, not
  one that has started containing a living claim.
- `build/rewrap_docstrings.py` is scratch in a gitignored directory. It carries a real proof (word
  tuples plus a whitespace-folded AST) and would be worth promoting if another phase has to re-wrap
  prose at scale; promoting it is not this phase's scope.

## 9. The gate

Phase 30's registered debt is closed on both halves: the citation asset's last unowned field now has a
producer, and the list that polices the documented bands is policed by the tree it claims to cover. The
census found four documents outside its own accountings and, once the detector stopped inventing pairs,
named two of them for a present-tense sentence that was no longer true — which is the result this phase
was for: `RANGE_DOCUMENTS` cannot silently omit a document again, and the omission is now red rather
than invisible. What the phase did not close is stated in §7 and #92: the percentage beside the pair, the
unit-less spelling of a band, and the fact that on a shallow clone the release date is checked by nobody.
