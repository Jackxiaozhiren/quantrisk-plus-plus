# Phase 37 — a tool promoted out of the ignored directory, and a folding question answered per reader

Date: 2026-10-13. Debt closed: the last two items of the list Phase 35 left -- `build/rewrap_docstrings.py`
was a gitignored scratch tool four phases had run from conversation memory, and #96's folded reading covered
only the four prose-counting guards Phase 35 had needed. Debt amended: #96, whose remaining half is now
decided reader by reader with a measurement each way, including one reader deliberately left raw.

## 1. Completed

1. **`scripts/rewrap_docstrings.py`, tracked.** The tool re-wraps over-long docstring prose and refuses to
   write unless it can prove the change was whitespace: every docstring's whitespace-split word tuple is
   identical, and the parsed tree with docstring whitespace folded is identical, so no other literal -- an
   assert message, a regex, a path -- can have moved. Promoted, it gained a shebang, type hints, the house
   docstring form, and one behavioural change: the width comes from `line_length()`, which reads
   `line-length` out of `pyproject.toml`, replacing the script's own `WIDTH = 100`.
2. **`tests/python/test_rewrap_docstrings.py`, five tests.** A refusal is tested by attempting it: a rewrite
   that deletes three words from a docstring must exit 1 and leave the file byte-identical. The accepted
   direction is tested too -- a genuinely over-long docstring is reflowed (one, not zero, so the tally means
   something), no line exceeds the configured width, the token multiset is unchanged, both code literals
   survive verbatim, and the folded parse is identical. A second run reports no work left. The width test
   reads the configuration through `tomllib` rather than through the tool, so the two cannot agree by sharing
   a mistake. And the scratch copy is gone: `build/rewrap_docstrings.py` no longer exists, and the script is
   tracked in git.
3. **Two plants on the tool itself.**
   `rewrap-tool-accepts-the-rewrite-it-exists-to-refuse` inverts `verify()`'s parse comparison, which reddens
   on the honest rewrite as well as on the lossy one -- a proof turned around cannot pass in either
   direction; `rewrap-tool-hardcodes-a-wider-line` adds 20 to the configured width, the edit that leaves the
   tool's own report tidy (`lines still longer than 120: []`) while every file it writes breaks E501. Plant
   count 70 → 72.
4. **#96's folding question, answered per reader with a count each way.** Six more readers go through
   `_folded_document()`: the chapter counts, the suite-member counts with README's per-kind breakdown and the
   reproducibility note's skippable count, the identity-check counts, the report's `PROSE_FIGURES` templates,
   and the three `_RATE_PHRASES`. Before each switch the raw and folded match counts were compared pattern by
   pattern; all nine came out equal, so the change buys future immunity to a re-wrap and nothing else.
5. **One reader deliberately still raw, and the measurement that says why.** Folding all 81 census documents
   adds the pair `(10.7, 7.4)` inside `paper/technical_report.tex` -- two unrelated numbers at the ends of
   adjacent lines -- because `_BAND_SHAPE`'s gap forbids a newline on purpose. So the band census keeps
   reading text as written, and the reason is in the guard's comment rather than in a general rule about
   consistency. The analysis-note ratchet is excluded for a different reason: it searches *test sources* for
   a filename, and folding a Python file is neither helpful nor harmless.
6. **The count cascade the phase caused, again driven by assertions.** pytest 509 → 514 and the offline
   collection 440 → 445 -- five tests added to a suite whose pair difference is still 69, which the Phase 35
   subtraction check re-verifies -- plus the plant annotation 70/70 → 72/72, and three plant anchors re-keyed
   because the prose they point at moved.

## 2. Assumptions this rests on

- **A tool that cannot be run by the next session does not exist.** Four phases re-wrapped docstrings with a
  script recreated from conversation; each re-derivation was a chance to write the proof weaker. Being inside
  the repository makes it a gate's subject: ruff checks it, the harness can plant in it, and a test can call
  it.
- **The width belongs to the gate.** `line_length()` reads `pyproject.toml`; the test reads the same file
  with a different parser. A disagreement between them is a finding, and the plant proves a fudge factor in
  either is caught.
- **Folding is not free and was not applied as if it were.** Where the fold manufactures a claim the document
  does not make -- `(10.7, 7.4)` -- the raw reading is the correct one. The general form, which #96 now says
  plainly: a document's line structure is information, and a normaliser throws some of it away every time.
- **The scratch directory is not evidence.** The probes written for this phase live in `build/` and stay
  there on purpose: they are measurements taken, not claims published. The tool moved because it is used,
  not because it was interesting.

## 3. Files changed

| File | What moved |
|---|---|
| `scripts/rewrap_docstrings.py` | the promoted tool: shebang, annotations, `line_length()` replacing `WIDTH`, `verify()`/`rewrap_source()` split out so a test can call the proof directly, and the scratch copy under `build/` deleted |
| `tests/python/test_rewrap_docstrings.py` | new: refusal, accepted rewrite, idempotence, width-from-config, tracked-and-only-copy |
| `tests/python/test_artifact_metadata.py` | six readers switched to `_folded_document()`; the band census gains the comment recording why it stays raw |
| `scripts/run_mutation_suite.py` | two plants, the sheet annotation re-keyed to 72/72, and three anchors re-keyed for the count cascade |
| `docs/interview_defense.md` | state line to Phases 0–37, the two collected totals and the sweep annotation |
| `docs/limitations.md` | #96 amended with the per-reader decision and the raw-reading exception |
| `docs/reproducibility.md`, `docs/limitations.md`, `paper/technical_report.tex` (+ `.pdf`, `.build.json`) | the collected pair 509/440 → 514/445 in every spelling the guards read |
| `docs/integrity_audit.md`, `docs/project_scope.md`, this file | findings 72 and 73, the §9 row, the record |

## 4. What the phase learned, including about its own first design

1. **A proof has to be tested by attempting the thing it refuses.** The tool had run four times in anger and
   had never been shown failing. Writing the refusal test meant monkeypatching its own rewrite step to delete
   a word -- which is also the shape of the plant, and the reason both exist: a self-test can attempt the
   defect, a plant can prove a *guard* notices it, and those are different claims about different objects.
2. **Folding prose is not a free normalisation, and finding that out required only asking.** The band census
   is line-aware by design -- the gap `[^\d\n]` is what stops two decimals on adjacent lines from becoming a
   spread -- and the fold manufactures `(10.7, 7.4)` in the report within one measurement pass. Consistency
   with the other guards would have been the wrong answer; the raw reading is the one that matches what the
   repository means by a claim, and the comment now says so with the number attached.
3. **The token-multiset check caught a wrong assertion in the test before it shipped.** The first version
   compared `ast.dump` of the whole file before and after, which is not equal after any docstring rewrap --
   the docstring's *value* changes when its newlines move. That is the folded-parse proof's whole reason to
   exist, and reaching for the stricter-looking assertion first was the mistake a repository with 96
   limitations about stricter-looking assertions should expect. The token check and the folded parse
   together are what actually says "line breaks only".
4. **The count cascade is now boring, which is the point.** Five tests added, two totals moved across eight
   spellings, three plant anchors re-keyed, all of it surfaced by failing assertions naming their site, and
   the `69 cases` subtraction stayed correct without being touched because it is derived rather than
   repeated.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| C++ | `uv run ctest --preset dev` | 100% tests passed out of 204 |
| Catch2 | `./build/dev/quantrisk_tests` | All tests passed (548368 assertions in 203 test cases) |
| Identity | `uv run quantrisk validate` | 7/7 checks passed |
| Python suite | `uv run pytest -q` | `514 passed in 155.41s (0:02:35)`, no skips |
| Offline lane | `uv run python scripts/measure_offline_collection.py` | `collected: 445`, `module_skips: 4`, `collection_errors: 0` |
| Docs + harness + tool lanes | `uv run pytest tests/python/test_artifact_metadata.py tests/python/test_mutation_suite.py tests/python/test_rewrap_docstrings.py -q` | 73 passed (60 docs, 8 harness, 5 tool) |
| Fold effect, measured | raw vs folded match counts per pattern, 9 patterns in 5 newly folded readers | equal on every one; and on the census, folding 81 documents adds exactly one phantom pair `(10.7, 7.4)`, which is why it stays raw |
| Tool, run in-repo | `uv run python scripts/rewrap_docstrings.py` on its own test file and on itself | `docstrings reflowed: 0`, `lines still longer than 100: []`, `proof: whitespace-only` both times, tree unchanged afterwards -- the files conform, which is the gate's claim, not the tool's |
| Lint | `uv run ruff check .` / `uv run ruff format --check .` | All checks passed! / 177 files already formatted — a walk of this directory, not a census (finding 62(d)) |
| C++ format | `uv run clang-format --dry-run -Werror` over the 77 tracked `.cpp/.hpp/.h` | 0 diagnostics, exit 0 |
| Types | `uv run mypy python/quantrisk` | Success: no issues found in 23 source files |
| Producer | `uv run python scripts/build_report.py` | 6 sources, bundle `338d51fb2e50…`, PDF `b821d3315650…`, 1,005,796 bytes — re-run because the tex's collected-test sentence moved |
| Evidence | `uv run python scripts/verify_evidence_manifest.py` | 0 missing, 0 unlisted — Evidence is intact |
| Anchor census | `test_every_declared_mutation_names_one_unique_anchor_and_a_guard_that_exists` | 72 declared plants, every anchor unique in its file, every guard present in its named file |
| Falsification, full sweep | `uv run python scripts/run_mutation_suite.py` on the committed tree | pending — recorded in the follow-up commit |
| CI on the pushed head | `gh api …/commits/<sha>/check-runs` after the push | pending — recorded in the follow-up commit, which is the only place its run id can come from |

## 6. Numerical validation

No measurement is published. What moves: the two Python totals (514 with the `oracles` extra, 445 collected
without) and their difference, which the guard recomputes as 69 from the document's own pair and did not need
to be told; the plant count (72, from the list); and the fold tallies quoted in §1 and §5, which are counts
of matches taken by this phase's probes rather than carried over from prose. The evidence freeze did not move
-- no experiment or benchmark input changed -- and `verify_evidence_manifest.py` is what says so.

The promoted tool publishes nothing: its numbers (`docstrings reflowed`, the over-long line list) describe
one file at one moment and are read from its own run, so the test asserts its *behaviour* on a fixture whose
shape it controls, not its output on this repository's current formatting.

## 7. Remaining limitations

- **The tool's coverage is one file at a time, by invocation.** Nothing runs it across the tree or fails a
  phase for un-wrapped prose; ruff's E501 is the gate and the tool is the repair. A file whose docstrings fit
  at 100 columns but read badly is not the tool's problem and is nobody's finding.
- **`verify()` compares structure, not intent.** It proves no token was lost and no code literal moved; it
  cannot notice a re-wrap that turned a list into a paragraph by deleting a blank line -- which the tool does
  not do, but the proof would not say so. The idempotence test is the nearer guard and is itself an
  observation about this implementation, not a theorem.
- **The fold decision is per reader, so it can be re-litigated.** A future phase could fold the band census
  for consistency and reintroduce phantom pairs; the defence is the measured example in the comment, not a
  gate. Nothing asserts "this reader must stay raw".
- **Carried forward:** #95's spelled counts, #94's plant-cannot-anchor-in-its-own-file wall (the structural
  answer is still to move `MUTATIONS` into a data module), and #93's boundary outside this harness.

## 8. Technical debt registered here

Nothing new. #96 is amended rather than closed: the convention now covers the prose-counting guards and the
band census is recorded as a deliberate exception, which is the whole of what that entry asked for; the two
readers still outside it -- the analysis-note ratchet and per-token figure checks -- are named there with the
reason each is out of scope, so the entry reads as decided rather than as pending.

## 9. The gate

Procedure: `CONTRIBUTING.md` §4, in its fixed order. The report render was rebuilt after the prose sync,
because the tex's collected-test sentence moved; §5 shows the binding guard green afterwards rather than this
sentence claiming it. The falsification sweep runs on the committed tree, since a plant edits and restores
files, and a sweep over a dirty tree is refused rather than guessed.

No release. `v1.8.0` remains the latest tag. The next phase takes #95 -- the spelled-count detector, whose
first run will classify 112 phrases and has to be measured for false positives before it is trusted to
generate work.
