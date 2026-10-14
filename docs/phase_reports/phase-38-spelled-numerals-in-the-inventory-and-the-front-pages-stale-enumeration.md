# Phase 38 — a count written in words, and the three defects it was hiding

Closed the first slice of `docs/limitations.md` #95: the claim inventory can now read a numeral spelled
out, and the two documents with the fewest such claims are policed by it. The widening paid for itself on
its first pass -- the front page had been stating three where it listed four, pointing a reader at the
wrong validation-matrix row, and naming four benchmark members where its own registry declared five. None
of the three was visible to any reader that existed, because all three numbers are words.

## 1. Completed

* **The extractor reads words now, and reads them from the table the guards already use.**
  `_SPELLED_WORDS` is generated from `SPELLED_NUMBERS` -- the same mapping `_as_int()` has resolved
  `nineteen` and `twenty-two` through since Phase 22 -- so the rule and the readers cannot drift into
  disagreeing about what counts as a spelled numeral. The digit rule and the spelled rule share their
  lookbehind, their number shape and their noun tail as three module constants, because two copies of an
  exclusion is one place for the two rules to diverge.
* **The widening is switched on per document, and the staging is asserted.** `_SPELLED_DOCUMENTS` starts
  as `("README.md", "docs/reproducibility.md")`. The inventory reads a document under the spelled rule
  only if it is listed, the self-test refuses a listing that gains no claim over the digit rule (so a
  document cannot be added as decoration), and it refuses a listing that covers the whole corpus while the
  register still records the rollout as staged.
* **All 28 spelled claims in the pair answer for themselves**: 15 owned, 9 cited, 2 declared, measured by
  replaying the guard's own classification (`build/probe_spelled_verdicts.py`). Nothing is unowned, and the
  inventory's two honesty checks -- an owner pattern that matches no document, an exemption that exempts
  nothing -- both pass on the spelled entries too.
* **Three documentation defects found and fixed**, each one in living prose:
  * `README.md` said "Three rows in the full matrix are the ones to interrogate" and enumerated four.
    Phase 11 wrote the sentence over three; Phase 12 appended the fourth (`git log -S "the other kind
    of"` dates it to `dc15846`) and nobody recounted. It is four now, as a list, under a count the guard
    produces by counting the list.
  * The same paragraph cited "Row 14" for the stress-map truncation bound. Row 14 is the third-and-fourth
    spot sensitivities; the bound is row 15, whose status cell is the one saying
    ``validated (L1 only)``. The label existed, so the matrix's own citation rule had nothing to flag.
  * `README.md`'s argument for `--require-all` said the benchmark suite "quietly skipping four members".
    The registry in the commit that first wrote that sentence (`216839c`) declared five members with a
    `requires` clause; today it declares six. The figure is now compared with the registry, in the guard
    that already resolves `six of the nineteen members` from the same field.
* **One new guard, five existing guards given a spelled spelling.**
  `test_documents_that_count_their_own_enumerations_agree_with_their_lists` derives three enumerations --
  the row bullets, the limitations bullets, and the artifact paths the timing paragraph names -- checks
  every cited row label against the matrix's own numbering, and compares README's two restatements of the
  wall-clock count with that derivation rather than with each other. The CI job count, the gated-module
  count, the re-frozen reading count, the suite-member count and the matrix row count each gained the
  pattern their guard searches with, so a spelled restatement is credited to a real comparison instead of
  resting in the cited tier.
* **Two declarations, both honest about what they are**: `six releases` (the gap finding 55 counted on the
  revision graph, a property of a superseded PDF) and `two digits` (an idiom for agreement in the last
  place or two). Each is load-bearing -- withholding it leaves its claim unowned, which the inventory
  reports.
* **Four plants, 72 → 76**, one per new failure mode: a spelled member count restored to its stale value,
  an enumeration count changed under the list it counts, the alternation narrowed by deleting one table
  key, and the spelled rule switched on corpus-wide.
* **The count cascade the phase's own work caused**: one new test moved the Python pair to 515 with the
  `oracles` extra and 446 collected without (their difference is still 69, recomputed by the guard from
  the documents' own pair), and three new register entries moved every living citation of this file's size
  from 96 to 99.

## 2. Assumptions this rests on

* A spelled numeral and the same numeral in digits are one claim about one quantity. That is what makes
  `nineteen members` and `19 members` disagree exactly as often, and it is why the owner patterns gained
  spellings rather than a second ownership mechanism being invented.
* `README.md` and `docs/reproducibility.md` were chosen as the first pair because #95 measured them as the
  smallest group (28 of 109). The other three documents keep their current, weaker property -- policed per
  figure by each number's own owner -- until a phase classifies them.
* A claim's paragraph naming a frozen artifact is a real, if weaker, answer for the figure. Nine of the 28
  sit there (the radius counts, the coverage tests, the band readings), and upgrading them to owned is
  work for whoever next reads those sentences, not a defect this phase invented.
* The environment matters for two of the new comparisons: the CI job count reads `.github/workflows/ci.yml`
  and the gated-module count reads the offline probe, which collects and so runs only where pytest can
  spawn a child interpreter. Both guards were already read in those environments.

## 3. Files changed

| File | What moved |
|---|---|
| `tests/python/test_artifact_metadata.py` | `_CLAIM_EXCLUDE` / `_CLAIM_DIGITS` / `_CLAIM_TAIL` shared by both rules, `_SPELLED_WORDS` and `_SPELLED_REPORT_CLAIM`, `_SPELLED_DOCUMENTS`, `_extract_claims(flat, spelled=)`, one new enumeration guard, spelled comparisons added to five existing guards, 17 new owner entries, 2 new declarations, property 5 of the extractor self-test |
| `README.md` | the interrogate-rows paragraph rewritten as a four-bullet list with correct row labels; `quietly skipping four members` → six; register size 96 → 99 |
| `docs/reproducibility.md` | one line re-wrapped so `is four modules that gate` reads as one phrase in the folded view; the two Python counts |
| `docs/interview_defense.md` | the two Python counts in four spellings, the register size in two spellings, the state line to Phases 0–38, the sweep annotation |
| `docs/validation_matrix.md` | the register size |
| `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md` | the register size in the sentences that point at the current file, which is the policy `test_documents_that_count_the_limitations_agree_with_the_file` states rather than a rewrite of those revisions |
| `docs/limitations.md` | #95 amended with the closed slice and the remaining 81; #97, #98, #99 added |
| `paper/technical_report.tex` (+ `.pdf`, `.build.json`) | the two Python counts, the register size in two places, re-typeset |
| `scripts/run_mutation_suite.py` | four plants added, three anchors re-keyed by the count cascade |
| `docs/integrity_audit.md` | findings 74–78 |
| `docs/project_scope.md` | the §9 row, the refresh date |

## 4. What the phase learned, including about its own first design

1. **A comment asserted a property of the rule, and the measurement said the opposite.** The first draft
   of this phase's rule carried the standard justification for ordering an alternation longest-first: that
   `twenty-two committed files` would otherwise be read as two files. Rebuilding the rule shortest-first
   and running it over the corpus's own sentence still returns `twenty-two`, because the tail demands
   whitespace after the numeral -- the short branch cannot complete, and backtracking reaches the long
   one. The plant written from the comment (`spelled-rule-orders-the-table-longest-first`) would have been
   a *defect that no guard can catch*, and the sweep would have reported it as an escape of something that
   was never a defect. What survives is the claim measurement supports: the alternation is *generated*
   from the table, and deleting one key really does change `twenty-two committed files` into a claim about
   two of them -- which is the property the self-test asserts and the plant now attacks.
2. **Ownership by source-presence is transcription, and this phase leaned on it harder than any before.**
   Five of the new owner entries are fragments or lead phrases of a pattern their owner's `re.search`
   uses, because the guard's regex is written as one literal that does not fit in 100 columns and so is
   not reproducible verbatim. The check proves the string is in the file, not that the guard applies it,
   and a fragment parked in a comment would credit the same way. That boundary is #98, with the AST fix
   named, rather than a claim that the mechanism is stronger than it is.

(a) **Choosing fragments over an exemption list was the cheaper honest option, and it is not free.** The
    alternative was declaring 15 claims the guards already police -- which the inventory would accept, and
    which would have hidden the fact that they *are* policed. Fragments keep the credit traceable to a line
    of code a reader can open.

3. **The register's own measurement was the reason the slice is 28 and not 109.** #95 was amended with a
   count before this phase opened, so the phase could take the smallest group and leave the other three
   named instead of discovering mid-flight that the diff had no end. The staging is now encoded in
   `_SPELLED_DOCUMENTS`, and the self-test refuses the list growing without the classification arriving
   with it -- one of the four plants is exactly that edit.
4. **A spelled count is not a rarer defect, it is an invisible one.** All three findings were ordinary
   documentation rot of a kind this repository has fixed many times; the difference is that each had
   survived to today *because* the number was a word: 25 phases for the row count, 25 for the row label,
   and a figure wrong in the commit that wrote it. The register's fear that spelled restatements "are
   caught only when they happen to match a spelling an owner already reads" was exactly right, and it was
   wrong in the direction that matters -- a stale spelled figure never matched anything, so nothing noticed.
5. **A guard's premise can be a property of the caller's shell.** The sweep's bytecode-isolation self-test
   reddened on a clean tree because the first subprocess inherited `PYTHONPYCACHEPREFIX` while the control
   stripped it, so the two looked in different places and the control's stale cache did not exist. Fixed in
   `d1306a4`, with the premise asserted where it is established and shown to fire by sending the cache away
   deliberately (finding 78). The general form -- *a test that inherits an environment variable its own
   subject is about* -- is worth checking in every guard that spawns an interpreter.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 178 files already formatted -- a walk of this directory, not a census (finding 62(d)) |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ format | `.venv/bin/clang-format --dry-run -Werror` over the tracked `.cpp/.hpp/.h` | no diagnostics, exit 0 |
| C++ suite | `.venv/bin/cmake --build --preset dev` then `ctest --preset dev` | 100% tests passed out of 204 |
| Identity | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Benchmark suite | `.venv/bin/python scripts/run_benchmark_suite.py --require-all` | `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 368.3s total` |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | 0 CHANGED, 0 VOLATILE, 0 MISSING, 0 unlisted -- "Evidence is intact". The re-run above rewrote 22 artifacts with identical result content; because no experiment or benchmark *input* changed in this phase those bytes were discarded rather than re-frozen, and the diff is preserved at `build/accidental-rerun-38.patch` so the decision can be undone |
| Python suite | `env -u PYTHONPYCACHEPREFIX .venv/bin/python -m pytest tests/python -q` | `515 passed in 116.93s (0:01:56)`, no skips |
| Docs + harness lanes | `.venv/bin/python -m pytest tests/python/test_artifact_metadata.py tests/python/test_mutation_suite.py -q` | 68 passed (60 docs, 8 harness) |
| Spelled inventory, measured | verdicts replayed through the guard's own classification (`build/probe_spelled_verdicts.py`) | 28 spelled claims: 15 owned, 9 cited, 2 declared, 0 unowned |
| Table-derivedness, measured | shipped rule vs the same rule with `twenty-two` deleted, on the corpus's own sentence | shipped reads `twenty-two`, narrowed reads `two` -- the difference this phase's plant attacks |
| Producer | `.venv/bin/python scripts/build_report.py` | 6 sources, bundle `febf7cf7d384…`, PDF `3b5e4c401974…`, 1,005,797 bytes; `--if-stale` afterwards prints "report is current", which is the record the freshness guard reads |
| Anchor census | `test_every_declared_mutation_names_one_unique_anchor_and_a_guard_that_exists` | 76 declared plants, every anchor unique in its file, every guard present in its named file |
| Falsification, full sweep | `.venv/bin/python scripts/run_mutation_suite.py` on `7cbb287`, logged to `build/mutation-sweep-38.log` | **`76/76 planted defects were rejected by their guard.`**, no line with any other status, tree clean afterwards. All four new plants are in that count. The record revision is swept again below, because four of the files the count cascade touched are themselves plant targets |
| Falsification, re-run on the record revision | same command, logged to `build/mutation-sweep-38b.log` | recorded in the next row added after this file, since a sweep cannot testify about the commit that contains its own record |
| CI on the pushed head | `gh api …/commits/<sha>/check-runs`, job logs read rather than inferred | recorded after the push, in the commit that carries the runner's own numbers |

## 6. Numerical validation

No measurement is published. What moves and why:

* **515 / 446** -- the two Python totals, up one each because this phase adds one test file entry to
  `tests/python/test_artifact_metadata.py`. Their difference, 69, is not retyped anywhere: the guard
  recomputes it from the pair the document states, and did not need to be told.
* **99** -- the register's size, up from 96 with #97, #98 and #99. Six living citations move with it
  (README, the report in two places, the matrix, the rehearsal sheet in two), and the dated release notes
  are left alone on purpose: they state the revision they describe.
* **76** -- the plant count, from the list rather than from prose, and the rehearsal sheet's annotation now
  agrees with `len(MUTATIONS)`, which is the guard that exists to make the two agree.
* **4 rows / row 15 / six members** -- three figures that were wrong and are now correct. Each is derived:
  the first from the bullets under it, the second from the matrix's own numbering, the third from the
  registry's `requires` field.
* **The evidence freeze does not move.** `verify_evidence_manifest.py` reports the tree's artifacts
  identical to the manifest after the accidental re-run was discarded, which is the only honest reading of
  a phase that changed no experiment: a 23rd committed reading of the speed artifact would have moved the
  `twenty-two committed files` and `twenty-two readings` sentences this phase just gave owners, and the
  band would have gained a sample from a machine under no benchmark load.

## 7. Remaining limitations

* **81 spelled claims in three documents are still invisible** -- 45 in the report, 22 in the matrix, 14 in
  the rehearsal sheet (#95, amended). Each needs both halves this phase did: the spelled spelling of every
  owner that already reads the figure, and a stated reason for every claim no owner covers.
* **The spelled table stops at twenty-six** (#97). `docs/validation_matrix.md` currently has exactly
  twenty-six rows, so the next one either needs the table extended or the sentence moved to digits, and the
  failure mode is a silent inventory plus a `KeyError` in the owner rather than a named red.
* **Ownership is credited by a string found in the owner's source** (#98), which cannot distinguish a
  pattern the guard searches with from one it merely contains. The fix is an AST read of the named test.
* **Row citations are checked for existence, not for meaning** (#99): the guard that fixed "Row 14" proves
  the label is in the matrix and the count matches the list, not that the sentence describes the row it
  names.
* **Nine of the 28 spelled claims sit in the cited tier** -- their paragraph names a producer the freeze
  carries, which is weaker than an owner comparing them with it. This phase left them as they are rather
  than pretending otherwise; the same boundary #89 recorded for whole documents now has a per-claim version.
* **`_SPELLED_DOCUMENTS` can only grow one document at a time by the same argument this phase used** -- the
  self-test refuses a full-corpus listing while the register calls the rollout staged, which means the
  final widening must delete that assertion deliberately rather than discover it.

## 8. Technical debt registered here

| Entry | What it records | Why it is a limitation and not a defect |
|---|---|---|
| #95 (amended) | the first slice closed, the remaining 81 claims named per document | the rollout is staged by measurement, not by convenience |
| #97 | the numeral table's ceiling at twenty-six, with the matrix at exactly twenty-six rows | fixing it means changing a fixture every spelled reading resolves through |
| #98 | ownership credited by source-presence; five fragment entries lean on it | the AST fix is a rule change to how every owner list is checked |
| #99 | a cited row label is checked to exist, not to be the row described | the status-cell comparison is buildable and should arrive with the next mis-citation |

## 9. The gate

The phase is closed when: the spelled rule reads only what the table resolves and the corpus's own
sentences prove it; every spelled claim in the two opted-in documents is owned, cited or declared with a
reason that stops being load-bearing if it stops excusing something; a count written in words is produced
by the list it counts rather than retyped above it; four new failure modes each have a plant that reddens
a named guard; the falsification sweep runs on the committed tree and its verdict is quoted from its own
log; and CI's three jobs are read from their job logs rather than from a badge, with the Python pair
reconciled against the offline probe the way #91 requires.
