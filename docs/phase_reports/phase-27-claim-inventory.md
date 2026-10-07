# Phase 27 — every countable claim in the report is owned, cited, or declared

Date: 2026-10-07. Post-tag work on `main`, after `v1.7.0` (`79d536a`). Objective: item (4) of the
registered debt list -- `paper/technical_report.tex` states numbers, and until this phase nothing
asked what each of them belongs to.

## 1. Completed

`tests/python/test_artifact_metadata.py::test_every_countable_claim_in_the_report_is_owned_or_declared`
inventories every `<number> <countable noun>` claim in the report's prose and requires each to be
accounted for by one of four mechanisms:

| Mechanism | What it means | Claims this way (measured) |
|---|---|---|
| owned | A named guard searches the report for the pattern and compares the figure with its producer. The pattern must occur verbatim in that guard's source. | 9 |
| region | The manifest sentence's span, compared as a block by `test_the_report_states_the_manifest_the_freeze_produced`, and owned only while it still holds exactly the seven numbers that guard reads. | 4 |
| cited | The enclosing paragraph names a file or directory that `evidence/manifest.json` hashes, so the number is traceable to a frozen producer. | 19 |
| declared | A literal phrase from the sentence plus the reason its numbers are not a living quantity. Re-checked with the anchor withheld: an exemption that exempts nothing is a failure. | 13 (9 anchors) |
| unowned | -- | 0 |

Measured on this tree with 1,948 non-empty prose lines read: 45 claims, distribution above.

Three defects were found by the instrument on its first run, and all three were in the shipped
document:

1. **`55 recorded limitations` in the abstract.** `docs/limitations.md` had 85 entries at the start of
   this phase (86 now) and the report's §Limitations said so in another phrasing that
   `test_documents_that_count_the_limitations_agree_with_the_file` did compare. Finding 55's mechanism
   -- one document, one fact, two statements, only one guarded -- had recurred in a paragraph nobody
   had keyed. The owner now reads both phrasings; extending it went red immediately with
   `paper/technical_report.tex says ['85', '85', '55']`, which is the defect proving the guard, not a
   mutant.
2. **A digit guard comparing two different quantities.** `_quoted_identity_floor` matched the
   validation matrix's `over 60 markets` against the report's `at 60 working digits` with a single
   `groups() == groups()` assertion. Its third group meant a market count on one side and a precision
   on the other, and the guard was green because both happened to read 60. Each figure is now read
   against the producer in the derivation run's own stdout (`60 markets, realised d1 from ...` and
   `part B: 60-digit nested numerical ...`), and the report's market count -- which nothing had read
   -- is one of the two patterns the inventory now marks owned.
3. **Two sentences with no producer at all.** The Heston probes' `200,000 paths over 250 steps` and
   `20, 80 and 320 steps` are not in any frozen artifact; the manifest lists no Heston file under
   `benchmarks/` or `experiments/`, so the only record is `docs/model_cards/heston.md`, which is not
   content-hashed. Registered as `docs/limitations.md` #86 rather than papered over.

Prose changes the guard required: the abstract's limitation count, three artifact citations added
(`real_data_risk_study.json` for the 582 scored windows, `optimisation_vs_oracles.json` for the LP's
250 scenarios, `pricing_vs_quantlib.json` for the `1.82` gap at 50 steps), and the test-count and
limitation-count syncs the new test and the new entry moved.

A fourth defect came from testing the *instrument of the previous phase* rather than this one. Running
`scripts/measure_offline_collection.py`'s blocked child as a test session instead of a collection -- to
ask whether the oracle-free lane can be predicted locally at all -- produced
`1 failed, 415 passed, 4 skipped`: `test_the_documents_that_count_python_tests_count_the_ones_that_exist`
judges the environment by `importlib.util.find_spec` in the parent and measures by spawning
`pytest --collect-only` in a grandchild, which does not inherit the block. `_collect_in_this_environment`
now hands the same block down, and the identical session reads `416 passed, 4 skipped`, exit code 0 --
the lane's shape, reproduced here for the first time (§5). And the released asset was read, not
inferred: the PDF attached to `v1.7.0` puts `55 recorded limitations` on its first page while two
later statements in the same file say 83, which is what `docs/limitations.md` held at that tag
(83, contiguous from 1, counted by the repo's own numbering rule). The release page and
`docs/release_notes_v1.7.0.md` carry a dated second correction; the tag and all four assets are
untouched.

Two guards and one limitation joined the phase for the same reason the inventory did. `test_every_digest_a_release_note_cites_is_its_files_own` pairs every snapshot under `docs/release_bodies/` with the digest the release note cites, because this phase cited `b0a13681…` for a file whose own hash is `229c21a6…` -- the cited value was the text before its trailing newline -- and only a second hashing caught it. `docs/limitations.md` #87 records that the v1.7.0 note's "What is still not here" bullet still says `sympy` is not a project dependency, which Phase 24 falsified: a present-tense bullet in a dated record, decayed in place, unpoliced by design because dated records are deliberately excluded from the count guards. The register is at 87 entries and the suite at 486 with the oracles / 417 without, each re-synced by its guard rather than by hand; the report PDF was rebuilt at 45 pages, 1,004,622 bytes.

## 2. Mathematical assumptions

None introduced. This phase changes no numerical code path: the closed forms, the crossing maps and
the benchmarks are untouched. The one mathematical statement examined is the fifth-order identity's
grid and precision, and it was already established in Phase 20 and 24 -- the change is to *which
quantity a comparison asserts about it*, replacing a group-wise equality that conflated a market
count with a working precision.

## 3. Files changed

| File | Change |
|---|---|
| `tests/python/test_artifact_metadata.py` | the inventory guard, `_tex_inventory_text`, `_tex_line`, `_paragraph_span`, `_cites_frozen_artifact`, `_is_declared`, `_frozen_artifact_paths`, `_REPORT_NOUNS`, `_REPORT_CLAIM`, `_REPORT_OWNED`, `_MANIFEST_REGION`, `_REPORT_SRC`, `_REPORT_DECLARED`; the limitations owner extended to two tex phrasings and its loop to a list of patterns |
| `tests/python/test_artifact_metadata.py` | `_collect_in_this_environment`, which hands the parent's oracle block to the collection subprocess so the guard's lever and its measurement agree |
| `tests/python/test_fifth_order_partials.py` | `_quoted_identity_floor(stdout)` reads the market count and the working precision from the run and matches each document's figure to it |
| `paper/technical_report.tex` / `.pdf` | abstract count, three citations, counts synced; PDF rebuilt: 45 pages, 1,004,623 bytes |
| `docs/limitations.md` | #86 appended (Heston probes have no frozen producer) |
| `README.md`, `docs/reproducibility.md`, `docs/interview_defense.md`, `docs/validation_matrix.md`, `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md` | limitation count 85 → 86, test counts 484 → 485 and 415 → 416, plant annotation 41/41 → 42/42 |
| `scripts/run_mutation_suite.py` | plant `report-adds-an-unowned-numeric-claim` declared; four anchors re-keyed by this phase's own count syncs |
| `tests/python/conftest.py` | the unowned `hashes 69 artifacts` figure in the module docstring replaced by the structural description of what the script covers |
| `docs/integrity_audit.md` | Phase 27 addendum, finding 59 (a)-(e) and the two list-honesty properties |
| `docs/release_notes_v1.7.0.md`, `docs/release_bodies/v1.7.0-*-2026-10-07.md` | second dated correction on the register's size, the digest identity `before + newline + block == published body`, and a dated line against the stale `sympy` bullet |
| `docs/project_scope.md` | §9 Phase 27 row |

## 4. The instrument, and the two design errors it took to get right

The first version read the report line by line. That silently dropped every claim LaTeX had reflowed
across a break -- including `8 correctness\nbenchmarks`, one of the seven numbers the manifest guard
compares -- so an inventory built that way would have reported the document as quieter than it is.
The text is now held in two aligned strings: comments blanked in place, and the same bytes with
newlines turned into spaces. Matching happens in the flat text, line numbers are computed from the
masked one, and offsets never shift.

The second error was scoping. Declared exemptions initially covered the whole *paragraph*, which had
two consequences: a number three sentences from an anchor borrowed its exemption, and two anchors in
one paragraph made each other look decorative, because removing either still left the paragraph
covered. The fix separates the two rules by what they are about: a declaration is a claim about one
sentence, so it reaches 40 characters around its anchor; an artifact citation backs an argument, so it
reads the paragraph. With the radius tightened, the "individually load-bearing" test became sound, and
it named three hand-written anchors that the citation rule already covered -- `12 of 12 cases`,
`492 rows`, `4 scenarios` -- which were deleted rather than kept as insurance, and it wrongly named
the two incident quotations, because two anchors in one paragraph each looked removable while the
other still covered the paragraph. Deleting both made the guard red, which is how the scoping bug
above was found: the check was sound only after the radius was tightened.

Ownership is verified rather than asserted: each pattern in `_REPORT_OWNED` must appear verbatim in
the source of the guard named as its owner, and the manifest region's anchors must appear in the guard
that reads them. A claim therefore cannot be exempted by a comparison nobody wrote, and the region is
owned only while it still contains exactly as many numbers as that guard compares -- so an eighth
number smuggled into the manifest sentence is a failure, not a silent pass.

## 5. Exact test results

Quoted from the runs, on this tree, before the commit:

- `uv run --frozen ruff format --check .` -- `156 files already formatted`
- `uv run --frozen ruff check .` -- `All checks passed!`
- `uv run --frozen mypy python/quantrisk` -- `Success: no issues found in 23 source files`
- clang-format over every tracked `cpp/**` and `tests/cpp/*.cpp` file -- exit 0, no diffs
- `uv run --frozen cmake --build --preset dev` then `uv run --frozen ctest --preset dev` --
  `100% tests passed out of 204`, `Total Test time (real) =  17.67 sec`
- `uv run --frozen pytest tests/python/test_artifact_metadata.py tests/python/test_mutation_suite.py -q`
  -- `52 passed in 21.42s`
- `uv run --frozen pytest -q` -- `485 passed in 195.03s (0:03:15)`
- `uv run --frozen python scripts/verify_evidence_manifest.py` -- `0 MISSING`,
  `0 on disk but not in the manifest`, `Evidence is intact.`
- `uv run --frozen pytest tests/python/test_artifact_metadata.py tests/python/test_mutation_suite.py -q` after the register and test-count syncs -- `53 passed`
- Digest guard falsification, run live before being declared: with the cited sha256 replaced by 64 zeros the guard named both values side by side, the file was restored byte-verified and the guard went green again
- Runner, `gh run view 37570134469 --log`, at this head: `415 passed, 5 skipped in 147.91s` on the
  fully-offline lane and `100% tests passed out of 204` on CTest, with the lane green against the
  documents' 416. Read as items rather than records that is 415 passed + 1 skipped item = 416, the
  same item count this machine ran -- the extra skip is one test that skips on Linux and passes on
  macOS. Third revision at which the probe's figure and the runner's agree.
- The oracle-free simulation, run as a session rather than a collection. Before the lever fix:
  `1 failed, 415 passed, 4 skipped in 186.91s`, the one failure
  `test_the_documents_that_count_python_tests_count_the_ones_that_exist`. After it:
  `416 passed, 4 skipped in 123.34s`, exit code 0, collected figure equal to the probe's 416.
- `uv run --frozen python scripts/measure_offline_collection.py` -- `collected: 416`,
  `module_skips: 4`, `collection_errors: 0`.

## 6. Numerical validation

No new measurement. The figures this phase touches are quotations of existing producers, and each was
re-read from that producer rather than derived: the identity's market count and working precision come
from `scripts/derive_fifth_order_partials.py`'s own stdout (60 and 60, matching the documents); the
582 scored windows come from `"windows": 582` in
`experiments/real_data_risk_study/results/real_data_risk_study.json`; the `1.82` at 50 steps comes from
`"lattice[steps=50]": 1.8199092433696649` in `benchmarks/quantlib/results/pricing_vs_quantlib.json`;
the LP's 250 scenarios from `"scenarios": 250` in
`benchmarks/pyportfolioopt/results/optimisation_vs_oracles.json`. Before citing each number the field
was grepped in the artifact, so a citation names a producer that holds the figure rather than a file
that happens to exist.

## 7. Remaining limitations

- `docs/limitations.md` #86: the Heston probes have no frozen artifact, so two numeric sentences in the
  report are carried as declarations. Closing it means running the Heston comparisons as a registered
  suite member whose results the freeze hashes.
- `docs/limitations.md` #85 still applies to the C++ totals: the guard needs a build, and a source-only
  checkout skips it rather than failing.
- The simulation reproduces the lane's *shape*, not every outcome on it: the runner's own tally read
  `414 passed, 5 skipped` against the 415 items its probe collected at that revision, one item
  skipping on Linux where it passes on macOS. No document quotes an executed tally, and #63 now
  states which quantity each figure is.
- The inventory's noun list is its own scope: a claim whose noun is not in `_REPORT_NOUNS` is not read.
  The list covers the quantity classes that have gone stale in this project (artifacts, bytes, tests,
  cases, entries, assertions, limitations, markets, digits, scenarios, observations, windows, ...), and
  the plant proves the mechanism bites within it, not outside.
- A declared anchor's 40-character radius is a chosen compromise: tight enough that a neighbouring
  sentence cannot borrow it, loose enough to cover a claim that wraps. It is not derived from anything.

## 8. Technical debt

Registered here, not scheduled:

1. Run the Heston comparisons as a suite member so #86's two sentences become citations (item (5) of
   the debt list is a larger experiment; this is the smaller, older gap).
2. Widen `_REPORT_NOUNS` and re-run the inventory, since each new noun is a class of claim that
   becomes auditable; the cost is new declarations, which is the point.
3. `run_mutation_suite.py` does not sweep the oracle-free lane, so the plant list is exercised only
   with the oracles installed; the simulation built this phase makes a lane-shaped sweep possible.
4. The same inventory has not been applied to the README or `docs/reproducibility.md`, which quote the
   same producers in their own phrasings. This phase proved the mechanism finds real defects; the other
   documents are the obvious next readers.

## 9. Gate

Locally, before the commit: §5's lint/format/type/clang-format/CTest/pytest/freeze lines, all green,
and the inventory guard's own falsification run live (plant edit applied, `line 59: '41 modules'`
reported, file restored to its recorded SHA-256 `44c2c1d5…`, guard green again).

After the commit, on `9117403`:

- `uv run --frozen python scripts/run_mutation_suite.py` --
  `42/42 planted defects were rejected by their guard.`, exit code 0, working tree restored. This
  includes the phase's new plant `report-adds-an-unowned-numeric-claim` and the four anchors the
  phase's own count syncs re-keyed.
- `git push origin main` -- `64d39a4..9117403 main -> main`.
- CI run `37570134469` -- `completed` / `success`, all three jobs:
  `Format and static checks`, `Configure, build, C++ tests, Python tests`,
  `Benchmark suite against live oracles`. The offline lane's own tallies are quoted in §5.
- Release page: the second correction is published on `v1.7.0` (body 11,604 characters,
  sha256 `8122e06b62437d15…`, verified to be the saved 2026-10-06 body plus the saved block), and
  the four assets and the tag are unchanged.

Two things this phase did NOT prove, stated rather than smoothed. The inventory's noun list bounds
what is read, so a claim whose noun is absent is invisible (§7). And the simulation now reproduces
the lane's item count and green-ness, not its platform-conditional skips: one test skips on Linux and
passes here, so a locally green offline run still is not the runner's verdict (§5).
