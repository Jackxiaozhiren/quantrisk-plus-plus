# Phase 31 — the report render gets an owner: `docs/limitations.md` #90 closed

Date: engineered and committed 2026-10-09 (`772fc42`, 18:50 +0800); recorded 2026-10-11. Predecessor:
Phase 30 (`docs/phase_reports/phase-30-v1.8.0.md`), which registered #90 while cutting `v1.8.0`. This phase
is verification engineering after a release -- no version bump, no new arithmetic -- in the family of
Phases 17, 23–29.

The gap is itself an observation worth keeping: the sweep was started immediately after the commit with its
output in the CLI's task scratch directory under `/var/folders`, and by the time this record was written
that directory had been reaped -- log gone, verdict unrecoverable, no process left. `build/dev/quantrisk_tests`
carried an 18:51 timestamp, so the run had reached its C++ plants before it died. The rerun therefore logs
to `build/mutation-sweep-31.log`, inside the repository's own ignored tree, which is where a proof that a
check can fail belongs (see `docs/integrity_audit.md` finding 63 and the Phase 26 note on instruments
outliving `/tmp`). No number in this file is quoted from the lost run.

## 1. Completed

- **`scripts/build_report.py`** typesets `paper/technical_report.tex` and writes
  `paper/technical_report.build.json`: a digest per source the render consumes, an aggregate digest of that
  set, the PDF's byte digest and size, the PDF's *extracted-text* digest, the engine line, and the timestamp.
  `--if-stale` lets a procedure skip the build when nothing moved.
- **The source set is parsed, not listed.** The report reads `\graphicspath{{../}}` + four
  `\includegraphics{experiments/**/results/*.png}` figures + `references.bib` + its own tex, so a suite
  re-run that redraws a figure is a freshness event. Six entries in the bundle today; the parser derives
  them from the document each run.
- **Two guards.**
  `test_the_committed_report_pdf_is_bound_to_the_sources_that_rendered_it` re-derives the bundle, compares
  every per-file digest, the aggregate, and the PDF's digest and size, and fails if the record is missing,
  names a different producer, or lists a different set of files. It runs in every environment: stdlib only.
  `test_rebuilding_the_report_from_the_committed_source_typesets_the_same_text` copies the bundle to a
  scratch tree, re-typesets it, and compares the extracted text of the two PDFs; it skips with a named
  reason where TeX Live or poppler is absent.
- **A denominator named, after the fact.** Verifying this phase against CI's own log showed the runner
  printing `428 passed, 7 skipped` for the oracle-free lane while every document prints 431. The number was
  right and the noun was not: the probe publishes what an oracle-free interpreter *collects*, and the four
  oracle-gated modules are skipped *items* outside that count (`428 + 7 = 431 + 4 = 435`). Registered as
  `docs/limitations.md` #91, and `docs/interview_defense.md`'s command annotation now reads
  `# 431 tests collected offline`, with the guard's pattern and the plant's anchor relabelled in the same
  commit.
- **Three plants** (`report-source-edited-without-a-rebuild`,
  `…-seen-from-the-render`, `report-record-names-a-digest-the-pdf-does-not-carry`) plus the hand-proved
  forgery control described in §4(c). Declared plants 53 → 56; tests 498 → 500 with the oracles and
  429 → 431 without; register stays at 90 entries with #90 amended in place.

## 2. Assumptions this rests on

- **A render is not reproducible, and the guard does not claim it is.** pdfTeX writes the creation date into
  the object, so `pdf_sha256` changes on every build of an unchanged source. The record therefore *binds*
  bytes to sources; it does not certify that a rebuild would yield those bytes.
- **Text is the stable projection.** `pdftotext` over two builds of one source gave the same digest
  (`c5f09b1a…`), so a text comparison can distinguish "the page says what the source says" from "the page
  was typeset from something else".
- **The input set is whatever the document asks for.** If a future change adds a figure, the bundle grows
  without anyone editing a list; if the parser ever fails to see a figure, an independent count of
  `\includegraphics` statements in the same file turns that into a red gate.
- **Falsifiability constrains the design.** #90's own sketch (compare last-touch commits) keys on git
  history, which no plant can edit; the shipped design keys on working-tree digests, which the harness
  moves at will.

## 3. Files changed

| File | Change |
|---|---|
| `scripts/build_report.py` | new producer |
| `paper/technical_report.build.json` | new record, written by the producer |
| `paper/technical_report.pdf` | re-rendered (1,005,769 bytes, 45 pages; bundle `cd3d0199c1fd`, PDF `e62cb615c386`) |
| `tests/python/test_artifact_metadata.py` | the two guards, `_report_builder()`, `import tempfile` |
| `scripts/run_mutation_suite.py` | three plants (53 → 56); four anchors re-keyed by this phase's count sync |
| `paper/technical_report.tex`, `docs/reproducibility.md`, `docs/interview_defense.md`, `docs/limitations.md` | 498 → 500 and 429 → 431; #90 amended with its dated closure; the reproducibility section rewritten to the present tense of what is and is not checked |
| `CONTRIBUTING.md` | §4 step 2 now says the report is rebuilt *after* the prose sync, and step 1 explains why the render is not among the first gates; step numbering unchanged |
| `docs/integrity_audit.md` | finding 63 |

## 4. What the phase learned, including about its own first design

(a) **The registered fix was un-buildable.** #90 proposed comparing each file's last-touch commit. Written
that way the guard reads commits while every plant in the harness edits working-tree files, so the guard
could be described, shipped, and cited as coverage without ever being shown to fail. The constraint that
decided the design was not elegance but: *can the falsification suite touch the input?*

(b) **The report does not read only its own file.** `\graphicspath{{../}}` hides the dependency on four
PNGs that live inside frozen experiment directories, so the render can go stale from a producer run nobody
edited the tex in response to. Measured by parsing rather than remembered: the bundle is six paths today,
and a guard that hashed only the tex would have closed #90 while leaving half of it open.

(c) **The binding's weakness is the record's honesty, and that is exactly what the second guard buys.**
With the tex edited and the record's digests recomputed to match -- a self-consistent forgery, which no
single plant can express because it needs two coordinated edits -- the binding stays green and only the
re-render notices. The hand experiment was run before the guard was claimed: binding green, re-render red,
then both files restored and their sha256 compared against the pre-experiment snapshots.

(d) **The guard went red on its own author within one sitting.** After it was written, this phase synced the
report's test counts in the tex, and the next lane failed with `paper/technical_report.tex hashes to
2603c97b0b02 while the record … says 3972934ef89d`. The fix was the producer, not the assertion. That is
the strongest evidence in the file that the binding is wired to the thing it claims to watch -- and it
mirrors Phase 30's experience, where the version guard reddened on the first tamper.

(e) **The binding reddened a second time in the same phase, on a second real drift.** Register 90 → 91
moved three sentences in the tex, and the next producer-less run failed on it exactly as designed; the fix
again was the build, not the assertion. Two live catches in one sitting, from two different edits, is the
evidence this guard is not a ceremony -- a plant proves a guard *can* fail, and only a real drift proves it
fails at the right moment.

(f) **Reading the runner's log instead of its badge produced the phase's second finding.** The CI job was
green, and the log line inside it -- `428 passed, 7 skipped` -- disagreed with the published 431. A verdict
alone would have hidden that; the number that reconciles them also confirmed the new guard's skip fired
where predicted (`SKIPPED [1] tests/python/test_artifact_metadata.py:1821: latexmk is not installed, so the
report cannot be re-typeset here`), which is the same line that explains why the previous head reported
six skips and this one seven.

(g) **Anchor choice is a falsification decision, not a formatting one.** `pdf_sha256` changes on every
honest rebuild, so a plant anchored on the record's current digest would disarm itself the first time
anybody re-typesets the report -- the Phase 30 failure mode (seven anchors in one phase) anticipated. The
three new plants anchor on a section heading and a JSON key. Four older anchors keyed on the pytest pair
still had to be re-synced with it, which is the recurring cost of anchoring on figures rather than shapes.

## 5. Exact test results

| Gate | Command | Result |
|---|---|---|
| Python | `uv run pytest tests/python -q` | `500 passed in 90.59s` on the final tree (register 91, render rebuilt) |
| Offline lane | `uv run python scripts/measure_offline_collection.py` | collected 431, 4 module skips, 0 collection errors |
| Docs + harness lanes | `uv run pytest tests/python/test_artifact_metadata.py tests/python/test_mutation_suite.py -q` | 59 passed; the first build of this guard was red before the producer ran (`paper/technical_report.build.json is missing`) |
| C++ | `uv run ctest --test-dir build/dev` | 100% tests passed out of 204 |
| Catch2 | `./build/dev/quantrisk_tests` | All tests passed (548368 assertions in 203 test cases) |
| Identity | `uv run quantrisk validate` | 7/7 checks passed |
| Lint | `uv run ruff check .` / `uv run ruff format --check .` | All checks passed! / "170 files already formatted" -- three consecutive runs on 2026-10-11 all printed 170, and the tracked census is `git ls-files '*.py' \| wc -l` = 83, so the tool's number is quoted as a walk of this machine, not as a count of files (`docs/integrity_audit.md` finding 62(d)) |
| Types | `uv run mypy python/quantrisk` | Success: no issues found in 23 source files |
| Producer | `uv run python scripts/build_report.py` | wrote the record: 6 sources, PDF 1,005,769 bytes |
| Falsification (the lost run) | `uv run python scripts/run_mutation_suite.py` started 2026-10-09 18:50 | log destroyed with the CLI scratch directory; no verdict quoted from it |
| Anchor census | one-pass enumeration of every declared plant against the file it names | 56 declared, 54 "
| file-backed, 0 with a non-unique or missing anchor |
| Render text (register) | `pdftotext paper/technical_report.pdf` | carries `91 recorded limitations` and `register contains 91 numbered entries` |
| Falsification (rerun) | `uv run python scripts/run_mutation_suite.py` on `772fc42`, logged to `build/mutation-sweep-31.log` | `56/56 planted defects were rejected by their guard.`, zero escapes, `git status` empty afterwards; the three new plants each read `ok caught` |
| Render text (counts) | `pdftotext paper/technical_report.pdf` | carries `500 pytest tests with the validation` and `431 collected without them` |

## 6. Numerical validation

No new quantity is published. The figures this phase moves are the two test totals (500 / 431), each
produced by its own collector rather than typed, and the record's digests, which are properties of bytes
rather than measurements. The freeze did not move: no file under `benchmarks/**/results` or
`experiments/*/results` was regenerated, and the evidence-integrity guards are what make that a check
rather than an assertion -- `paper/` is not a hashed directory, so neither the new render nor its record
enters the manifest.

## 7. Remaining limitations

- The runner still cannot re-typeset: on CI the text guard reports a skip and only the byte binding is
  checked. A phase that wants the stronger claim needs a TeX-bearing lane; until then the split is declared
  in the test, and `docs/reproducibility.md` says so in the present tense.
- Nothing ties the probe's collection figure to a runner's `passed, skipped` summary (#91). The
  reconciliation is arithmetic a reader can do but no check can assert, because its right-hand side exists
  only on a machine the repository does not own.
- The binding is trust-able in one direction only: an author who edits the tex *and* recomputes the record
  without rebuilding satisfies Tier 1. Tier 2 catches it where TeX and poppler exist, which is the dev
  machine and not CI -- so the residual risk is a stale PDF committed from an environment with no toolchain.
- Nothing verifies the *content* of the extracted text against the artifacts; that is what the report's own
  numeric guards do, and they read the tex, not the render.

## 8. Technical debt registered here

1. **A lane that can build the PDF.** `date-released` (§Phase 30) and the text guard's skip are both
   symptoms of a runner with no TeX distribution. Adding one to the `lint` job would make Tier 2 run in CI
   and turn #90's closure from local-only into enforced-on-push. Cost: one apt package set, no money.
2. **A census guard for `RANGE_DOCUMENTS`** (Phase 30 §8 item 5) -- unchanged, still open.
3. **`date-released` still has no producer** (Phase 30 §8 item 2).
4. **The rehearsal sheet's "Phases 0–N shipped" line still has no owner** (Phase 30 §8 item 3).
5. **The inventory's two remaining documents** (#89) still policed per figure.

## 9. The gate

The first sweep run was lost with the scratch directory that held its log (§Date), so the verdict below is
from the rerun on `772fc42`, logged to `build/mutation-sweep-31.log`. The push and the runner's three
conclusions are appended in the record commit that follows this file, and what no commit of this phase can
contain is the CI behaviour of
`test_rebuilding_the_report_from_the_committed_source_typesets_the_same_text`, which will report a skip
there by design -- a green CI on this phase therefore evidences the binding, not the re-render, and the
distinction belongs in the report rather than in a footnote nobody reads.

The rerun's own verdict is quotable because the log now lives under `build/`, which the repository ignores
and the session scratch does not own: `56/56` with `git status` empty after the last restore. The lost
first run is kept in this record rather than quietly replaced, because the honest statement is not that the
sweep passed but that one sweep passed and another was destroyed before it could report.
