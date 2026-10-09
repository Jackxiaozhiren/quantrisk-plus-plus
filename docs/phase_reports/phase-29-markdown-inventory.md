# Phase 29 — the claim inventory leaves the paper: README and the reproduction guide, read the same way

Phase 28 closed the sixth book and registered one item of its own debt in §8: Phase 27's inventory read
`paper/technical_report.tex` and nothing else, while `README.md` and `docs/reproducibility.md` restate the
same producers in their own words. This phase discharges that item. It found what an inventory finds —
one stale number neither document's owners could see, and one number no producer printed anywhere.

The guards were written on 2026-10-08; the records carry 2026-10-09, the day they were committed, so a
dated citation to this phase names one day rather than a session.

## 1. Completed

`tests/python/test_artifact_metadata.py` gained two guards:

- `test_the_identity_checks_the_cli_runs_are_the_ones_the_documents_count` — runs the installed
  `quantrisk validate` in JSON mode and requires `README.md`, `docs/reproducibility.md` and the report to
  state the count that run reports (7). The console script is resolved beside the running interpreter, so
  the guard measures the build under test rather than a source checkout.
- `test_every_countable_claim_in_the_readme_and_reproducibility_is_owned_or_declared` — the report's
  owned-or-declared rule applied to both markdown documents, with `_MARKDOWN_OWNED` (7 patterns, each
  required verbatim inside the guard named as its owner) and `_MARKDOWN_DECLARED` (currently one anchor,
  load-bearing-checked by withholding it).

Supporting changes: the claim extractor gained two exclusions (§4), the CTest count guard learned the
prose spelling `"204 tests under CTest"`, `docs/limitations.md` #89 records the scope that remains, and
finding 61 records what the extension caught. Four declared defects joined the harness (47 → 51).

The stale number itself: `docs/reproducibility.md` line 72 annotated the reproduction command with
`# 481 tests here` while line 110 of the same file said **494 pytest tests with the `oracles` extra** and
line 112 said the offline lane collects 425. It entered with Phase 23's sync and survived two later phases
that re-synced that exact pair.

## 2. Mathematical assumptions

No new mathematics. The claim this phase rests on is an accounting rule rather than a numerical one, and
it is worth stating precisely because the two documents' owners already disagreed with it in practice:

- A *producer* owns a figure if it can be re-derived in the environment that quotes it. The Python test
  pair is environment-relative by design (#63), so a document carries both halves and each guard compares
  the half its environment measures; the extension keeps that discipline rather than flattening it to one
  number.
- A *citation* is only a citation if the thing named is evidence. `docs/limitations.md` is prose, so
  naming it does not exempt a count inside its paragraph; the freeze hashes evidence, which is why the
  register's size is owned by the guard that counts the file instead.
- A *countable claim* is a quantity the document asserts about the repository's own state. A list marker
  and a cross-reference are not, which is what §4's exclusions encode.

## 3. Files changed

| File | Change |
|---|---|
| `tests/python/test_artifact_metadata.py` | two new guards, `_MARKDOWN_OWNED` / `_MARKDOWN_DECLARED`, the markdown readers (`_markdown_inventory_text`, `_markdown_claim_window`, `_suite_key_artifacts`, `_cites_frozen_artifact_markdown`), the extractor exclusions, the CTest prose spelling |
| `docs/reproducibility.md` | `# 481 tests here` → the owned spelling at 496; offline pair re-synced by its guard to 427 |
| `README.md` | register size 88 → 89 |
| `docs/interview_defense.md` | both halves of the test pair (496 / 427) and the register size; the sweep annotation re-keyed to 51/51 |
| `docs/limitations.md` | #89 registered; its own count synced where quoted |
| `docs/validation_matrix.md`, `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md` | register size 88 → 89 where the count guards read them |
| `paper/technical_report.tex` / `.pdf` | abstract and §limitations counts (496 / 427 / 89), PDF rebuilt in the same commit |
| `scripts/run_mutation_suite.py` | four new plants, four anchors re-keyed by this phase's own count syncs |

## 4. Presence versus accounting, and what that difference cost

The count guards this repository already had ask: *does the document contain the number my producer
prints?* The answer was yes for `docs/reproducibility.md` — at line 110 — and the file shipped a second,
wrong one at line 72 for three phases. The inventory asks the other question: *for every number the
document prints, which producer owns it, or what is the stated reason it needs none?* Under that question
the 481 is an unowned claim and the document is red. That is the whole of the finding, and it is the
difference between a check and a census.

Three design points fell out of applying the rule to markdown rather than to LaTeX.

**A markdown citation goes through the registry.** README's findings table keys rows by member
(`fifth_order_crossing_map`) and prints no path. `_cites_frozen_artifact_markdown` therefore resolves a
backticked token three ways — a frozen file, a directory prefix of one, or a suite key whose registered
artifact is frozen — so a row is cited by the evidence its own member produces, and a key the registry has
dropped cites nothing. Pasting paths into the table would have satisfied the letter of the rule and lost
that property.

**A table row, not a table, is the paragraph.** `_paragraph_span` carries over from the report because
markdown reflows paragraphs the way LaTeX does; inside a `|`-delimited block the unit shrinks to the line,
otherwise one row's citation would excuse every other row's numbers — and the findings table is exactly
where these documents put their result figures.

**The extractor needed sentence sense before it needed nouns.** Unchanged, the report's rule produced two
fake claims per file: `#77. Load moves the timings` (a cross-reference, then a sentence opening on the
policed noun *moves*) and `on 5 of 5. Two books sit at the grid edge` (a period read as part of the
number). Excluding a `#` before a number and a bare trailing period after one removes both, and is
measurably inert on the report: 46 claims before, 46 after, no classification changed. The direction
matters more than the mechanism — an inventory that invents claims is one readers learn to wave through,
and a human had already waved through the real one in that file.

## 5. Exact test results

Each line is what the named command printed on this tree.

| Lane | Command | Its own words |
|---|---|---|
| Lint | `uv run ruff check .` | `All checks passed!` |
| Format | `uv run ruff format --check .` | `163 files already formatted` |
| Types | `uv run mypy python/quantrisk` | `Success: no issues found in 23 source files` |
| C++ | `uv run ctest --test-dir build/dev` | `100% tests passed out of 204`, 7.54 s |
| Python | `uv run pytest tests/python -q` | `496 passed in 115.21s` |
| Offline lane | `uv run python scripts/measure_offline_collection.py` | `"collected": 427`, 4 module skips, 0 collection errors |
| CLI owner | `quantrisk validate --json` (inside the new guard) | 7 checks, all passing |
| Harness | `uv run python scripts/run_mutation_suite.py --list` | 51 declared plants |

The benchmark suite was **not** re-run: this phase changed no producer, so every frozen artifact is
Phase 28's, and `test_the_manifest_hashes_every_experiment_results_directory` plus the evidence-integrity
guards are what make "the freeze still matches the tree" a checked statement rather than an assertion.
The runner's own benchmark job re-executes all nineteen members on the pushed head, and §9 quotes what it
prints.

## 6. Numerical validation

Every figure the two new guards compare is read from a producer, not restated: the identity-check count
from the CLI's JSON payload, the test pair from a real collection in this environment and from the probe's
child interpreter, the C++ totals from CTest and the Catch2 binary, the suite's member count from the
registry's Python objects (`_load_suite_members`, loaded rather than grepped), the register size from
numbered entries counted in the file.

The inventory's owned list is itself validated twice before it can exempt anything: each pattern must
appear verbatim in the source of the guard named as its owner, and a pattern neither document still states
is reported as accretion. The single declared anchor is re-run with itself withheld, so it has to be the
reason at least one claim passes; an anchor that excuses nothing fails the guard. That machinery earned
its keep during the phase in the negative direction — an owner invented for a VOLATILE tally
(`test_the_volatility_of_the_volatile_fields_is_measured_not_assumed`, no such guard exists) was rejected
by the verbatim check and converted into the declaration it should have been, which is exactly the failure
the check is there to make loud.

## 7. Remaining limitations

- #89: `docs/interview_defense.md` and `docs/validation_matrix.md` are still policed figure by figure, not
  inventoried. Their prose is denser with dated numbers, so their value would sit in a per-entry reason
  list and should be built against real reds rather than by bulk exemption.
- The inventory reads the two documents' *present-tense* claims as claims. A command annotation inside a
  fenced block is now policed, which is the point, but nothing yet distinguishes "as of v1.3.0" from
  "now" in markdown the way the report's declarations do — the difference is carried by the anchor list,
  which is hand-maintained by design.
- Presence of a frozen path is a sufficient citation, not a proof that the number came from it. A row that
  cites the right artifact and quotes a wrong figure from it is caught only by the artifact's own owner, as
  before this phase.

## 8. Technical debt

Registered here, not scheduled:

1. Extend the inventory to `docs/interview_defense.md` and `docs/validation_matrix.md` (#89), starting from
   the reds the rule produces rather than from a declaration list written in advance.
2. Nothing bounds how far the freeze's recorded revision may lag `HEAD`. This phase is honest about not
   re-freezing because no producer ran, but the repo has no gate that says "the freeze must be within N
   commits of the head quoting it", so the convention is carried by the phase report rather than by a check.
3. `_MARKDOWN_INVENTORY` is a tuple a guard reads; a third living document joins by editing that tuple,
   and nothing yet reports a living document that has quietly never been added to any inventory.
4. The carried-forward items each phase registers and this one did not touch: a radius ladder beyond the
   grid edge (#88), a frozen Heston producer (#86), and a mechanism that tells an author which volatile
   reading to sync to (Phase 28 §8).

## 9. The gate

Run in this order, quoted as each tool printed.

On the working tree, before the commit:

- `readme-quotes-an-identity-count-the-cli-does-not-run` run through the harness: planted, bytes changed,
  the new CLI guard named `9 identity checks` against a run of 7, the file restored, `1/1 planted defects
  were rejected by their guard`.
- The identity guard's own report half proven live: `seven` → `eight` in the tex, guard red naming the
  artifact's number, file restored to `190d45b2…` by hash, guard green.
- The lanes in §5, all green, including the full Python suite at 496.
- Four plants' anchors re-keyed by this phase's own count syncs, each named by the harness self-test before
  it could be mistaken for coverage — finding 49's fifth occurrence.
- One self-inflicted defect recorded rather than hidden: a bulk comment re-wrapper damaged the guard file
  (a dropped newline, then 18 word-internal splits). Nothing was committed in that state; the file was
  restored from `HEAD` and the phase's edits re-applied against unique anchors, then the lane re-run.
  Finding 61(e).

The remaining gates ran after the commit, and each is quoted below with the head it was produced on.

Recorded as the tools printed them, each line naming the head it was produced on:

| Verdict | Head | The tool's own words |
|---|---|---|
| Commit | `7adc535` | 14 files, the two guards, #89, finding 61, four plants (47 → 51) |
| Sweep | `7adc535` | `51/51 planted defects were rejected by their guard.` (exit 0), 51 `ok caught` lines, `git status` empty after — this covers the three plants not run live before the commit |
| CI, three jobs | `7adc535` | run `37882178468` — `success` in 10m37s: `Format and static checks`, `Configure, build, C++ tests, Python tests`, `Benchmark suite against live oracles` |
| CI lane lines | `7adc535` | `100% tests passed out of 204`, `426 passed, 5 skipped in 201.40s`, `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 424.8s total` |

The runner's offline lane reports `426 passed, 5 skipped` where this machine's probe collects `427`:
the two are different measurements — one a run's pass/skip tally, the other a collection count — and #63
is the register that says so rather than a guard bridging them. The documented offline figure is the
collection count, and the guard that compares it with every document's claim is green on both machines,
which is what establishes that the runner's probe also measured 427 rather than inferring it from the
document.

The guard file itself went through one damage and one recovery inside the phase (§9's last bullet,
finding 61(e)), so the version the sweep certified is a re-application of the phase's edits against
unique anchors rather than the first draft — which is worth recording because the lane could not tell
those two apart, and only reading the diff did.

One of my own mistakes is recorded rather than erased: the commit that carries this record, `f7d897b`,
has Phase 28's subject line — pasted from the previous record — while its body and its diff are this
phase's. The head was already pushed, and the discipline the release errata follow says a published
record is answered by the next one rather than rewritten, so the mismatch stays visible in `git log` and
is named here instead of being amended away. The substance it mislabels — `51/51`, run
`37882178468`, #89 — is correct in the body and in the table above.

