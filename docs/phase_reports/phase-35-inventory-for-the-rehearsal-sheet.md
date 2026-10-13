# Phase 35 — the two documents outside the inventory, and the rule that had to learn to read them

Date: 2026-10-13. Debt closed: `docs/limitations.md` #89 (the claim inventory read three documents while
the rehearsal sheet and the validation matrix restated the same producers) and the second half of #92 (the
report's performance prose was outside the inventory's vocabulary). Debt opened: #95, because the widened
rule still reads digits and a count spelled in words is invisible to it, and #96, because the falsification
sweep escaped on a pattern that could not read a claim the document had split across two lines -- and the
check that found it turned up a second, older instance that had been dormant since Phase 27.

## 1. Completed

1. **Both documents are inside the inventory.** `_MARKDOWN_INVENTORY` is now
   `README.md`, `docs/reproducibility.md`, `docs/interview_defense.md`, `docs/validation_matrix.md`, so every
   `<number> <countable noun>` they print has to be owned by a named guard, cited to a frozen artifact, or
   declared with a reason. The extension found three live defects on its first pass, none of which any
   per-figure owner could have seen (§4 item 1).
2. **Two new guards.** `test_the_rehearsal_sheet_reproduces_the_question_set_it_cites` reads
   `PROJECT_SPEC.md`'s question section -- bullets that end in a question mark, which is how the section
   separates its 22 questions from the three bullets describing an answer's shape -- and requires the sheet's
   stated count, its four group names, and its first 22 `### Q` titles to match it, one for one and in
   order, with consecutive labels and no added title repeating a briefed one.
   `test_the_claim_extractor_reads_percentages_and_refuses_labels` reads the extractor's five judgements,
   each twice: the shipped rule must refuse something a reconstructed looser rule finds, and must keep the
   claims it is supposed to see.
3. **The extractor's vocabulary widened and its precision with it.** The noun list gained `spreads?`,
   `runs`, `readings?`, `re-freezings?`, `paths?`; a `%` is allowed between a number and its noun, which is
   the shape #92 recorded as invisible (`32.6% spread`); a number that begins inside a longer dotted token is
   no longer a claim (`cvxpy 1.9.3 are oracles` had become 9.3 oracles); and a number that closes a namespace
   name is a label (`the Phase 1 consistency test` is one test, `pinned in the Phase 2 test files` names
   files). `run` stayed out while `runs` came in, measured: in this corpus the singular fires only on
   `uv run` inside a command block.
4. **Ownership moved from digits to phrases where the digits were ambiguous.** The sheet quotes three
   current path rates and one superseded rate in the same sentence.
   `test_documents_quote_the_performance_figures_the_artifact_actually_holds` already required the
   artifact's formatted values to *appear* in the file; it now also reads `_RATE_PHRASES`, three patterns
   that bind each number to the implementation named beside it, and the inventory's owned list points at
   exactly those patterns. The superseded reading is declared instead, with the reason naming it as history.
5. **Six restatements in the sheet and the matrix became owned rather than newly exempt.** The limitations
   count's table parenthetical, the `204 / 507 now` pair, the `69 cases` subtraction, the three
   `paths/s in the C++ core` shapes, `collects 438 tests without`, the `# 438 tests collected offline`
   command comment and the identity grid's `60 markets` are each read by the guard named in
   `_MARKDOWN_OWNED`, whose verbatim-in-holder check is what stops a claim being exempted by a comparison
   nobody wrote. Ten declared anchors carry the rest, each reported decorative by the guard if it exempts
   nothing -- and one of the first versions was.
6. **What the extension found was corrected, not excused.** The sheet's provenance table said
   `(84 entries)` under a correct 94 (six phases of drift in one file); its opening line said "Nothing added,
   nothing dropped" while carrying six questions the brief does not ask; and four sentences quoted a frozen
   artifact's figure without naming it in the paragraph the citation rule can see. Now:
   `benchmarks/quantlib/results/pricing_vs_quantlib.json` is cited in the sheet's L2 answer and in the
   matrix's rho paragraph, `…/monte_carlo_validation.json` in README's Monte Carlo z row, and
   `…/real_data_risk_study.json` in the report's runs-test sentence.
7. **The count cascade the phase caused was driven by the guards, not by reading.** Register 94 → 95 → 96,
   pytest 507 → 509 and the offline pair 438 → 440 across seven documents and five dated-record spellings,
   the plant annotation 62/62 → 68/68, and five plant anchors re-keyed -- seven edits, because the register
   moved twice inside one phase and two anchors moved with it twice
   (`readme-undercounts-the-limitation-register`, `sheet-provenance-cell-quotes-a-stale-register-count`,
   `interview-doc-overcounts-the-offline-lane`, `report-counts-stale-python-tests`,
   `report-quotes-a-count-the-offline-probe-refutes`). Every one of those came out of a failing assertion
   naming its site.
8. **Six new plants** (`sheet-restates-the-question-set-at-the-wrong-size`,
   `sheet-provenance-cell-quotes-a-stale-register-count`,
   `sheet-quotes-a-path-rate-the-artifact-does-not-measure`,
   `sheet-states-a-case-gap-the-collected-pair-does-not-give`,
   `extractor-accepts-a-phase-label-as-a-countable-claim`,
   `extractor-slices-a-number-out-of-a-dotted-token`) -- the last two are the only way to show an exclusion
   filter is load-bearing, because a self-test that re-runs the filter's own logic would pass on an empty one.
9. **The first sweep escaped on one of them, and the escape was the phase's most useful measurement.**
   `sheet-states-a-case-gap-the-collected-pair-does-not-give` came back `guard-stayed-green`: the guard's
   pattern was `the (\d+) cases they hold` with a literal space, and the sheet wraps that sentence as
   `... the 69 cases they` / `hold ...`, so the comparison saw only the occurrence two pages later and agreed
   with itself over a planted 70. Auditing every owned pattern for the same blind spot found a second, older
   one: `(\d+) tests under CTest` in `docs/reproducibility.md`, recorded by Phase 27 precisely because the
   file states its C++ total twice, had matched nothing since a later edit moved a line break inside it -- and
   `test_documents_that_count_the_cpp_tests_agree_with_the_build` stayed green because it asserted only that
   *some* of its patterns matched. Both are fixed: `_folded_document()` gives the four prose-counting guards
   the same whitespace-folded view the inventory reads, the CTest guard now reports a listed spelling that
   matches nothing, and the wrapped total mutated to 199 reddens it (§5). #96 registers where the convention
   has not been applied yet.

## 2. Assumptions this rests on

- **A bullet that ends in a question mark is a question.** That is the rule `PROJECT_SPEC.md`'s own section
  follows: 25 bullets, of which three (`30秒版本`, `2分钟版本`, `deeper technical version`) describe an
  answer's shape. The guard asserts the count it derives, not the 22 it was told.
- **A label rule keyed on surrounding text is a heuristic with a cost.** `the Phase 507 Python tests` would
  escape the inventory. The mitigation is that the word list cannot grow without firing on real text, which
  bounds the surface to one word today; #95 states the exposure rather than treating it as closed.
- **Owning a number means owning its phrase.** `3,787,943` is the artifact's Python rate today; the digits
  alone would certify the stale `21,130,162` in the same sentence. `paths/s in the C++ core` is the claim
  shape the guard can compare, and the inventory's owned patterns must appear verbatim in it.
- **The evidence freeze is untouched.** Nothing in `experiments/`, `benchmarks/` or `data/` changed; the
  report PDF is not a manifest artifact, so its rebuild moves `paper/technical_report.build.json` and no
  digest the freeze carries. §5 shows the verifier agreeing rather than this sentence asserting it.

## 3. Files changed

| File | What moved |
|---|---|
| `tests/python/test_artifact_metadata.py` | `_REPORT_NOUNS`, `_REPORT_CLAIM`, `_LABEL_WORDS`/`_LABEL_BEFORE`/`_is_labelled`/`_extract_claims` (new), the two inventories reading four documents, `_MARKDOWN_OWNED` +17 patterns, `_MARKDOWN_DECLARED` +10 anchors, `_REPORT_DECLARED` +2 −1, `_RATE_PHRASES` (new), the two new guards, and the limitations/python-test/C++-test count guards each learning a spelling |
| `scripts/run_mutation_suite.py` | six plants added, four anchors re-keyed for the cascade |
| `docs/interview_defense.md` | the false "nothing added" clause rewritten, `(84 entries)` → the register's figure, the rate sentence left as prose with its superseded reading declared, citations added, counts and state line synced, sweep annotation 68/68 |
| `docs/validation_matrix.md` | the artifact named in the rho paragraph, register count, 50-step lattice depth and the `%`-step range declared |
| `README.md` | the Monte Carlo z row cites `benchmarks/quantlib/results/monte_carlo_validation.json`; register count |
| `docs/reproducibility.md` | the two collected figures, and the `32.6%`/`20.8%` spread sentences are now inventoried claims |
| `docs/limitations.md` | #89 and #92 amended with their closures, #95 opened, the collected pair in #63's body |
| `paper/technical_report.tex` (+ `.pdf`, `.build.json`) | the runs-test sentence cites the artifact that carries 67; register 94 → 95 in abstract and §11; collected pair 507/438 → 509/440; two Heston/stress path configurations declared, one stale declaration deleted |
| `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md` | the register count those notes quote in the present tense |
| `docs/integrity_audit.md`, `docs/project_scope.md`, this file | findings 68 and 69, the §9 row, the status date |

## 4. What the phase learned, including about its own first design

1. **The register's own prediction was exact and its warning about the fix was the part that mattered.**
   #89 said the value of extending the inventory "would sit in a per-entry reason list, which should be built
   against real reds rather than by bulk exemption". Building it against reds is what made ten anchors
   credible -- and the guard immediately used them: one of the first versions exempted a claim its neighbour
   already covered, and the decorative-anchor assertion reported it, which is the same mechanism catching a
   stale number, turned on the exemption list itself.
2. **Widening a detector's question invalidates its exclusions.** Phase 29's two exclusions were written
   against a noun list that had no `oracles`-adjacent risk... it had `oracles` already, but no `%`, so the
   version-number shape was unreachable. Adding `spreads?` and the `%` allowance made `cvxpy 1.9.3 are
   oracles` a claim within one edit. A presence check enumerates junk the moment it asks a wider question;
   the fix had to be re-measured on the corpus, not reasoned about.
3. **A filter that is only tested by its own logic can be deleted into vacuity.** The first version of the
   extractor self-test looped over `_LABEL_WORDS` and asserted each entry fires -- which passes trivially
   when the list is empty. The plant (`extractor-accepts-a-phase-label-as-a-countable-claim`) is what found
   that, and the fix is one line: the test asserts the list is non-empty before it asks the list to earn its
   keep. A demonstration would have missed it; a plant cannot.
4. **Substring presence is not quotation.** `PROSE_FIGURES` requires `3,787,943 paths/s` to appear
   *somewhere* in a 1,078-line document. For the inventory to call that span owned, the comparison has to bind
   the number to the phrase beside it; that is the difference between "these digits are in the file" and "this
   sentence is quoting the artifact".
5. **Two exclusions retired one declaration and one whole claim class.** `pinned in the Phase 2 test files`
   had been declared as "names files by phase rather than counting them" -- once the label rule refused the
   claim, the exemption covered nothing and the guard said so. Deleting it is the clearest evidence in the
   phase that the exemption list and the extractor are one mechanism.
6. **The cascade was small because the corpus was already policed, and invisible where it was not.** Every
   prose spelling that had to move was named by a failing assertion, in the same run that showed the figure
   was wrong -- no count was found by reading. What no guard could see was the falsification list itself: five
   of its anchors point at prose this phase renumbered, and they surfaced only through the harness's own
   uniqueness check, which is the third time this repository has found that a falsification instrument needs
   its own list policed.
7. **A plant that stays green is a measurement of the guard, not of the plant.** The instinct after
   `guard-stayed-green` is to widen the plant's edit until something reddens. Here the right reading was the
   opposite: the plant landed, the bytes changed, the document said 70 and the guard was supposed to disagree
   with it -- so the guard had stopped reading the sentence. Following that back found a pattern with a literal
   space in it, then an audit of every owned pattern for the same shape, then a spelling that had been dead
   since Phase 27 because the guard checked its aggregate rather than each of its spellings. Both instances
   were fixed in the reading convention rather than in the two patterns, which is why #96 also names where the
   convention has not been applied: `PROSE_FIGURES` and the band census are still raw-text searchers, and one
   of them certified the very rates this phase bound to their phrases.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| C++ | `uv run ctest --preset dev` | 100% tests passed out of 204 |
| Catch2 | `./build/dev/quantrisk_tests` | All tests passed (548368 assertions in 203 test cases) |
| Identity | `uv run quantrisk validate` | 7/7 checks passed |
| Python suite | `uv run pytest -q` | `509 passed in 85.80s (0:01:25)`, no skips — re-run after the fold, which is where the two new restatement checks live |
| Offline lane | `uv run python scripts/measure_offline_collection.py` | `collected: 440`, `module_skips: 4`, `collection_errors: 0` |
| Docs + harness lanes | `uv run pytest tests/python/test_artifact_metadata.py tests/python/test_mutation_suite.py -q` | 68 passed -- 60 in the docs file (two new guards), 8 in the harness file |
| New guard, red on arrival | `uv run pytest -k rehearsal_sheet_reproduces` before the prose was corrected | it did not go red: the sheet's "Nothing added, nothing dropped" clause is prose the guard does not read, and the count it checks (22) was already right. The clause was corrected by reading the heading list the guard now enumerates, and the finding is recorded as such rather than as a catch |
| Falsification, per plant | `uv run python scripts/run_mutation_suite.py --only <id>` for each of the six | refused while the tree was dirty (`target-already-modified`), as designed -- which is what forced the fix into its own commit and the verdict into this one |
| Falsification, first full sweep | `uv run python scripts/run_mutation_suite.py` on `dee2d6d`, logged to `build/mutation-sweep-35.log` | **`67/68 planted defects were rejected`, exit 1** -- `sheet-states-a-case-gap-the-collected-pair-does-not-give` came back `guard-stayed-green`, which is §1 item 9 and finding 70 |
| Falsification, full sweep after the fix | `uv run python scripts/run_mutation_suite.py` on `8af6190`, logged to `build/mutation-sweep-35b.log` | **`68/68 planted defects were rejected by their guard.` exit 0**, every line `caught`, no other status, and `git status --porcelain` empty afterwards. One earlier attempt was interrupted by the session at plant 33 of 68; the tree came back clean, and the re-run was started detached rather than session-owned so that an interrupt could not land between a plant's mutation and its restore |
| The escape, reproduced | hand-mutate `docs/reproducibility.md`'s wrapped `204 tests under` / `CTest` spelling to 199, run the CTest guard, restore from the copy taken first | `AssertionError: docs/reproducibility.md says ['204', '199'], CTest lists 204` -- red where it had been green before the fix; the file restored to its committed bytes (`git diff --stat` empty afterwards) |
| Lint | `uv run ruff check .` / `uv run ruff format --check .` | All checks passed! / 174 files already formatted — a walk of this directory, not a census (finding 62(d)), after one reformat of the new code and a docstring re-wrap whose tool proved the change was whitespace-only |
| C++ format | `uv run clang-format --dry-run -Werror` over the 77 tracked `.cpp/.hpp/.h` | 0 diagnostics, exit 0 |
| Types | `uv run mypy python/quantrisk` | Success: no issues found in 23 source files |
| Producer | `uv run python scripts/build_report.py` | 6 sources, bundle `dbb73c704ea0…`, PDF `3965281a4e08…`, 1,005,797 bytes — run once after the prose sync, which is the order §9 requires, and the register's second bump made it necessary again |
| Evidence | `uv run python scripts/verify_evidence_manifest.py` | 0 missing, 0 unlisted — Evidence is intact |
| Anchor census | the harness's own `test_every_declared_mutation_names_one_unique_anchor_and_a_guard_that_exists` | 68 declared plants, every anchor unique in its file, every guard present in its named file |
| CI on the pushed head | `gh api …/commits/f437644/check-runs` after the push | run `38387224491`, all three jobs `completed/success` (SonarCloud `neutral`, as in every prior run) |
| CI's own pytest summary | `gh api …/actions/jobs/115261877855/logs`, read rather than inferred from the green | `439 passed, 5 skipped in 149.76s`; the five skips are the four oracle-gated modules plus `latexmk is not installed`. No history- or tag-keyed guard appears in the skip list, so Phase 33's fetch settings were still doing their job on this head. The pair reconciles the way #91 says it must: `439 + 5 = 444 = 440 collected + 4 module records`, with 440 the figure this tree's probe publishes |

## 6. Numerical validation

No new measurement is published. The figures this phase moves are: the two Python totals (509 with the
`oracles` extra, 440 collected without), each from its own collector and their difference (69) now asserted as
the sheet's own subtraction; the register count (96, counted from the file by the guard that compares it, and
read in three spellings it had never read); the plant count (68, counted from the list by the guard that
annotates the command); and the question set (22 briefed and 28 headings, both counted from their sources).
The report's re-render moved its bundle and PDF digests and nothing else: the evidence freeze still hashes the
same 95 artifacts, which `verify_evidence_manifest.py` reports rather than this sentence claiming.

The extractor changes certify transcription, not arithmetic: `32.6% spread` being an inventoried claim does not
make 32.6 right -- that figure's owner is Phase 33's derivation over the committed readings, unchanged here.

## 7. Remaining limitations

- **The inventory still reads five documents of a much larger corpus.** `docs/limitations.md`,
  `docs/project_scope.md`, `docs/findings.md`, the model cards and the phase-report family are outside it,
  policed per figure. Phase 36 takes the exempt *families* -- `docs/phase_reports/` and
  `docs/release_bodies/` are excused by prefix today, where the band census should name each file and its
  reason.
- **A count written in words is invisible to the rule** (#95). Measured: 112 phrases of the shape across the
  five inventoried documents, including #92's own `twenty-two committed re-freezings`. Several are owned
  elsewhere; none is inventoried.
- **Four guards read a folded document; the rest still read raw text** (#96). The escape that found the
  dormant spelling fixed the reading convention where the sweep proved it mattered -- the Python totals,
  CTest entries, Catch2 assertions and the limitation register. `PROSE_FIGURES`, the band census and the
  analysis-note figure guard still search files as written and can lose a claim to a line break the same way;
  folding them changes what they can match, so each needs its own before/after measurement rather than a
  sweep-wide sed.
- **The label and dotted-token exclusions can hide a claim as easily as excuse one** (#95, second half). What
  limits the surface is that `_LABEL_WORDS` cannot grow without firing, not any check on what a writer chose.
- **The citation rule sees a paragraph, and a paragraph is not an argument.** A claim is `cited` when its
  paragraph names a frozen artifact. Three of this phase's citations were added by putting the path in the
  sentence that needed it; a document can still satisfy the rule with an artifact that does not carry the
  figure in question, and nothing here reads a quoted number against the key inside the file it cites.
- **The offline pair is checkable on the runner only for the half the runner can see.** The `69 cases`
  subtraction is asserted against the document's own pair in both environments, and the with-oracles half of
  that pair is verified where the oracles are installed; on CI it is quoted, not measured, exactly as #91
  registers.

## 8. Technical debt registered here

- **#96** -- a pattern written with a literal space cannot read a claim the document splits across lines. Two
  instances were found by auditing the sweep's escape: the case-gap pattern this phase wrote, and
  `(\d+) tests under CTest`, dormant in `docs/reproducibility.md` since Phase 27's spelling was re-wrapped by
  a later edit. Closed for the four prose-counting guards by `_folded_document()` plus a per-spelling presence
  assertion; opened for the guards that still search raw text, because folding them needs its own measurement.
- **#95** -- the claim inventory reads digits, so a spelled count is invisible (112 instances measured), and
  its two exclusion rules are keyed on surrounding text and so can excuse a real claim by accident. Opened by
  this phase, deliberately not taken on: the first run of a spelled detector classifies sentence-openers and
  idioms as work, so it needs its own false-positive measurement before it needs a rule.
- Carried forward, unchanged in shape: **#92**'s first half was closed by Phase 33 and its second half is
  closed here for digits; **#93**'s outside-the-harness boundary and **#94**'s plant-in-its-own-file wall are
  untouched, and #94's structural answer (moving `MUTATIONS` into a data module the harness loads) is still the
  one item that would give Phase 34's isolation guard a declared plant.

## 9. The gate

Procedure: `CONTRIBUTING.md` §4, run in its fixed order. Gates were executed on the working tree and every
result above is the measured output; the report render was rebuilt after the prose sync, so the PDF carries the
figures the tex carries. The full falsification sweep runs on the committed tree, because a plant edits files
and restores them, and a sweep over an already-dirty tree is refused rather than guessed.

No release is proposed. `v1.8.0` carries Phases 23–29 and the two tags since it has been the practice to open a
release when a phase changes what a reader of the published artifacts would see; this phase changes how the
documents are checked, not what they report. The next phase takes #64's items -- a band written without its
unit, the prefix-exempt families named file by file, and the rewrap tool promoted out of `build/`.
