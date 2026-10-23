# V2 refactor ledger

This file is the refactor lane's working record. It is the first committed artefact of the lane, as
`REFACTOR_PROMPT.md` §7 step 8 requires: a later session resumes by reading it, re-running §7 step 4
first, and treating what is stored here as **history, not ground truth**. Every number below names the
command that produced it; none of them is a restatement of the prompt's prose.

Series status: V1 is `PROJECT_SPEC.md` (executed, locked by K3). This lane is V2, running beside it.

## 1. The revision this baseline was taken on, and the vantage

| Item | Reading | How it was produced |
|---|---|---|
| Revision | `7d4f656` (`Phase 59 record: …`), which descends from the release commit `2441c5c`, the freeze `b2dda33` (tagged `v1.9.0`) and the post-tag accounting commit `58b6c22` | `git rev-parse HEAD` |
| CI verdict on that revision | run `39432183143`, all three jobs `success` | each job's own log, not the workflow badge |
| Working directory | a detached export created by `git worktree add --detach <sibling-directory> 7d4f656` — the path is a parameter of the machine, not a fact of the lane; every measurement below ran inside it, **not** in the development checkout | §7 step 1's isolation procedure and L13's single-vantage rule |
| Tree state at measurement | `git status --porcelain` empty | it stayed empty apart from §7 step 5's documented trap, handled in §3 below |
| Interpreter | `.venv` created inside the export by `uv sync --frozen` (exit 0): Python 3.12.14 | `sys.version` |
| Instrument identity (L8) | `sys.prefix = <export>/.venv`, `quantrisk.__file__ = <export>/python/quantrisk/__init__.py`, extension `<export>/.venv/lib/python3.12/site-packages/quantrisk/_quantrisk.cpython-312-darwin.so`; no path resolves into the development checkout | a `python -c` probe printing `sys.prefix`, `module.__file__` and the `.so` glob, then asserting nothing contains the other root |
| Environment content | `dev` group installed (pytest, ruff, mypy, cmake, ninja, clang-format, pybind11, scipy, matplotlib, sympy, pyyaml); `oracles` extra **absent** — `sklearn`, `QuantLib`, `pypfopt`, `cvxpy` all fail to import | `python -c` import probe per module; this is exactly what CI's second job builds with plain `uv sync` |

The export was chosen over measuring in the development tree for two reasons, both of which are the
prompt's: L13 forbids a baseline over a tree carrying another session's work, and §7 step 4's lane list
*is* CI's lane list, which means the offline lane has to run in an environment where the oracles are
genuinely absent. The development checkout keeps its `oracles` install untouched.

## 2. Exit codes, captured per command

Each line is one command's own status, taken with `"$@" > log; rc=$?` inside a driver
(`build/v2-step4.sh`, gitignored scratch) rather than read off a pipeline's last stage. The commands are
`REFACTOR_PROMPT.md` §7 step 4 verbatim, run with the export as cwd.

| Step 4 lane | Command | rc | Wall | What the tool said |
|---|---|---|---|---|
| Lint | `uv run --frozen ruff check .` | 0 | 1 s | `All checks passed!` |
| Format | `uv run --frozen ruff format --check .` | 0 | 0 s | `204 files already formatted` |
| C++ format | `find cpp bindings tests/cpp … \| xargs uv run clang-format --dry-run --Werror` | 0 | 1 s | silent; corpus reported by the same `find`: **77 files** |
| Types | `uv run --frozen mypy python/quantrisk` | 0 | 5 s | `Success: no issues found in 23 source files` |
| Configure | `uv run --frozen cmake --preset ci` | 0 | 16 s | writes `<export>/build/ci` |
| Build | `uv run --frozen cmake --build --preset ci` | 0 | 48 s | core + tests + bindings + reference tool |
| C++ tests | `uv run --frozen ctest --preset ci` | 0 | 12 s | `100% tests passed out of 204` |
| Install | `uv pip install -e .` | 0 | 25 s | `Prepared 1 package in 21.79s`, `~ quantrisk==1.9.0 (from file://<export>)` |
| Python tests | `QUANTRISK_REFERENCE_TOOL=<export>/build/ci/quantrisk_reference_tool uv run --frozen pytest -q` | 0 | 159 s | `470 passed, 4 skipped in 157.52s` |
| Evidence | `uv run --frozen python scripts/verify_evidence_manifest.py` | 0 | 1 s | `Evidence is intact.` |

| Step 5 / 6 | Command | rc | What happened |
|---|---|---|---|
| Suite binding | `uv run --frozen python scripts/run_benchmark_suite.py --no-run` | 0 | read-only in intent, **not in bytes**: it rewrote three tracked aggregates and printed `suite: 0/19 executed and passed, 19 aggregated from disk, 0 failed, 0 skipped, 0.0s total` |
| Evidence, re-run | `uv run --frozen python scripts/verify_evidence_manifest.py` | **1** | `CHANGED benchmarks/suite/results/suite_run.json expected 072db34187b2… found e828635b7a80…`, `CHANGED …/suite_summary.md expected 6ae00d0d4914… found 56eabe2069a6…`, `Evidence does not match the manifest.` |
| Restore | `git checkout -- ` the three paths `git status --porcelain` named, by name | 0 | tree empty again |
| Evidence, third run | `uv run --frozen python scripts/verify_evidence_manifest.py` | 0 | `Evidence is intact.` |
| Plant inventory | `uv run --frozen python scripts/run_mutation_suite.py --list` | 0 | **172** declared plants; the full sweep is §10 P3.2's proof and will be read from its own summary line |

**The baseline is green.** Nothing in the lane starts from a red lane, so §7's "a red baseline is
information" branch was not exercised — except for the one rc=1 above, which is the prompt's own trap
firing as designed and is the strongest evidence in this section: it proves the manifest verifier can
fail, and that a suite invocation with exit 0 had still corrupted the ledger.

## 3. Environment readings that the prompt says are facts and the tree says are not

Recorded here rather than discovered later, each with the command that read it.

- **`--no-run` dirties three tracked files, not two.** §7 step 5 says "restore exactly the two files it
  rewrites". `git status --porcelain` after the invocation names three:
  `benchmarks/suite/results/suite_headline.csv`, `…/suite_run.json`, `…/suite_summary.md`. The manifest
  verifier only rejects two of them, because the third is byte-identical after re-aggregation — which is
  exactly how a "two" becomes a "three" without anybody noticing. Finding **V2-04**, lane `facts-protocol`.
- **The same revision, two pytest readings, one difference, and it is owned.** Local export:
  `470 passed, 4 skipped`. CI job 2 on `7d4f656`: `469 passed, 5 skipped`. Both sum to 474, which is
  `#91`'s reconciliation against the 470 collected offline. The extra skip is
  `tests/python/test_artifact_metadata.py:4897: latexmk is not installed, so the report cannot be
  re-typeset here` — present on the runner, absent here because this machine has `latexmk`. No lane is
  environment-blind by accident; this one declares its own skip.
- **The formatter count is a census, but not of the corpus anyone assumes.** `ruff format --check .`
  printed **204** in this export and CI's `Format and static checks` job on the same `7d4f656` printed
  **204** — so the two vantages agree, and the first draft of this bullet, which claimed they disagreed,
  was wrong. It is superseded here rather than deleted because the wrong reading is itself the lesson:
  the number was compared across **three different revisions**, not three environments. The 203 belongs
  to `b2dda33`, where `docs/phase_reports/phase-59-v1.9.0.md` does not yet exist (`git cat-file -e
  b2dda33:docs/phase_reports/phase-59-v1.9.0.md` fails), and the 205 the development checkout printed
  later is `7d4f656`'s 204 plus this file. The instrument that answered the question was
  `ruff format --check . -v`, which logs every admission as `Included path via 'include'`; the earlier
  probes (`ruff ls`, and grepping for `Examining`) failed to answer it, and naming a failed probe is not
  a finding.
- **What that census actually counts, and the hazard that survives the correction.** Ruff 0.16.9's
  formatter traverses **Markdown as well as Python**: `ruff format --check docs` reports 103 files where
  `find docs -type f -name '*.py'` reports none, and the verbose log admits `.md` paths by name
  (`Included path via 'include'`). The 204 is therefore exactly the tracked corpus: 86 `.py` + 8 `.pyi` +
  110 `.md` (`git ls-files` for each, and `git status --porcelain --untracked-files=all` empty in this
  export), and the 205 this development tree printed after §7 step 8 is 204 plus this file. So the figure
  *is* a census and *is* stable per revision — it just counts the documentation, which moves at every
  phase. The residual hazard is narrower and still real: a file that is neither tracked nor ignored is
  counted too, so scratch markdown can move the number with no commit — the mechanism `docs/integrity_audit.md`
  62(d) and Phase 30 §4(e) were reaching for when they called the reading "a tool's output for a different
  machine". It is not a different machine; it is a different file set, and the guard that should own it is
  a count of *tracked* documents, not of a formatter's walk. Finding **V2-05**, lane `facts-protocol`.
- **The repository is bigger than the prompt's own size ratchet assumed.** §0 ratchets V2's prose against
  V1's line count; `wc -l PROJECT_SPEC.md REFACTOR_PROMPT.md` reads **1,724** and **683**, so the ratio
  this lane is allowed to grow against is a subtraction away from any reader. Recorded so that no later
  step mistakes the ratchet for permission to grow prose. Not a finding: the ratchet holds.

## 4. The three premises, and why this section is not yet closed

§0 demands all three premises re-derived from a fresh measurement before anything is touched, and §7 step 8
demands the ledger committed **before any instrument or source file is written**. The collector §7 step 3
names is an instrument. The two instructions cannot both be satisfied in the order written, and the lane
resolves it the only way that keeps both: this file is committed first, then `tools/inventory_orphan_code.py`
is written, then the premise readings land as a dated entry in this ledger's §9. Recorded as finding
**V2-01**, lane `facts-protocol`, so the contradiction is the document's defect and not a silent improvisation.

What can be stated without an instrument, because it is a direct filesystem reading of the export:

| Premise | Reading available now | Reading still owed |
|---|---|---|
| P1 — executable Python outside the package reaches it by `sys.path` hacks or by-path loads | 86 tracked `.py`, of which **63 live outside `python/quantrisk`** (`git ls-files '*.py'` and the same list filtered). Whether each reaches the package by bootstrap, by-path load, installed import, or not at all is the collector's classification, not an inference from a count. | the per-file classification, and the bootstrap census with the directory each site injects |
| P2 — recorded reproduction commands are not uniformly executable, and no guard polices their form | **Confirmed, and worse than the premise claims.** The census over all 95 entries: 52 name a file that exists from the root; 16 carry prose inside the command field (verbatim: `uv run python scripts/record_data_fixtures.py (source: FRED fredgraph.csv (live response, current revision))`); 15 give a bare filename that exists only inside a task directory (`uv run python run.py`, `… monte_carlo_validation.py`); 11 are two-token mangles (`uv run python pricing_validation run.py`, `… performance monte_carlo_speed.py`); 1 has no interpreter prefix at all. **43 of 95 cannot be pasted into a shell at the repository root, and 27 of those name no file.** The collector will own this as policy; the reading above is a probe, and its command is in §6's V2-03 row | the executability census per entry (done), and the writer attribution: `scripts/build_evidence_manifest.py:120` copies `command`/`generator_command` straight out of each artifact's own `summary.json`, so 27 unrunnable strings are the studies' own prose re-frozen verbatim at every release. The premise's second half is verified rather than assumed: `grep -rl generated_by_command --include=*.py .` matches **one** file, the builder — no test, no guard and not the verifier reads the key, so nothing in the lane can currently disagree with a command that names no file |
| P3 — static checking covers the package but not the code outside it | `mypy python/quantrisk` reports **23 source files** against a **63-file** corpus outside the package; the gap is 40 files by subtraction, but subtraction is not a census. | the per-file bucket table (mypy-covered / ruff-covered / declared exemption) with each bucket's corpus printed |

**No premise is yet void, and none is yet measured.** If the collector returns an empty bootstrap census,
P1 weakens into a layout complaint and §5's motivation has to be re-scoped with the maintainer before any
move (§0's own instruction).

## 5. Declared scope

**Lanes** — all eight of §8, no lane skipped, no finding outside these lanes fixed without extending this
declaration first: orphan code and import hygiene; reproducibility contract; registry and hand-maintained
lists; test and verification validity; documented claims versus code; artifact reconciliation; packaging and
developer experience; security and CI. Plus the `facts-protocol` lane §4.4 grants for defects in the prompt
itself, which V2-01 and V2-04 already occupy.

**Tasks in scope** — §10's P3.1 registry, P3.2 verification instruments, P3.3 the experiment absorptions
(one commit per task), P3.4 the `tools/` package and the CI step that consumes it, P3.5 the single suite
re-run under L1's digest invariant, P3.6 the CLI `run` subcommand, P3.7 static-check parity; then §11's
installed-user proof, documentation coherence, dead-glue deletion and DX residue; then §12's report.

**Locked, at cost** — K1 `cpp/`, `bindings/`, `CMakeLists.txt`, `CMakePresets.json`; K2 every
`experiments/*/results/**` and `benchmarks/*/results/**` path; K3 `PROJECT_SPEC.md`; K4
`evidence/manifest.json` (builder-only; the rc=1 in §2 is the proof it is not a rubber stamp); K5 every
formula, tolerance, threshold and RNG contract.

**Survey** — §6 runs before the §9 gate, ≥5 maintained candidates across ≥3 classes, scored A1–A4 against
exact files, implementation never absorbed. Its notes are gitignored until the section it produces is
written into `docs/ecosystem_research.md`.

**Budget** — a wall-clock envelope of 12 hours of agent time across sessions, of which Phase 0 consumed
about 45 minutes (the gate suite itself: 4 minutes of tool time in one export). The gate suite is the
dominant cost: every §10 commit pays it in full, so the sequence is committed one finding at a time (L2)
and never bundled to save a run. CI minutes are the repository's existing free hosted allowance; external
spend for this lane is **$0.00** (L12), and the only paid-capable network call in the repository, a FRED
fetch, is not used by anything in scope.

**Outward actions** — pushes to `origin/main` happen because the standing instruction for this lane names
them. Creating the public GitHub Release object for `v1.9.0`, opening a PR, commenting on an issue, or
moving any tag requires its own approval and will not be inferred from this file.

## 6. Findings table

Schema, every field, per §8. `probe` is mandatory: it is what lets a later run re-derive the result
without trusting this ledger's prose. Rows are in **discovery order**, not rank order — §9's gate presents
the same findings ranked by impact × effort × risk, and re-sorting this table before that ranking exists
would put a judgement in the ledger that nothing has made yet.

| ID | lane | severity | evidence | probe | impact | root cause | proposed fix | verification | cost | blast radius | confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| V2-01 | facts-protocol | Low | §7 step 8 requires the ledger committed before any instrument; §7 step 3 requires the collector's premise readings inside that ledger | `sed -n '343,394p' REFACTOR_PROMPT.md` | the ordering is unsatisfiable as written; an executor either writes an instrument first or commits a ledger missing mandated content | the two steps were written against different drafts and neither names the other's dependency | resolve in the order that preserves the harder rule: ledger first, instrument second, premise readings as a dated §9 entry | the ledger's §9 entry cites the collector's own snapshot path and revision | 0 $, one commit | `REFACTOR_PROMPT.md` untouched (a prompt edit needs §4.4's leak test and maintainer approval); this file only | high |
| V2-04 | facts-protocol | Low | §7 step 5 says "restore exactly the two files it rewrites"; the export's `git status --porcelain` after that command named three, and the verifier rejected two of them | `uv run --frozen python scripts/run_benchmark_suite.py --no-run && git status --porcelain` | an executor who restores "the two" by a remembered list leaves one tracked aggregate dirty, and the next lane's green would then certify a dirty tree | the count of rewritten aggregates is a property of the run, not of the prose: whether a re-aggregated file is byte-identical depends on what changed since the last suite execution | the lane's rule is "restore the paths `git status --porcelain` names, by name" — already §14's rail; step 5's "two" is the defect, and the collector records the set rather than its size | §9's entry records the three named paths and the verifier returning to exit 0 after restoring them | 0 $, no file change | prose only | high |
| V2-05 | facts-protocol | Medium | 91 quotations of `… files already formatted` sit in 62 files, and none is in a living front-page document — `grep -r "already formatted"` over `README.md`, `docs/architecture.md`, `docs/reproducibility.md`, `docs/interview_defense.md`, `docs/validation_matrix.md` and `CONTRIBUTING.md` finds nothing, so every quotation is a dated record; the count is a census of `.py` + `.pyi` + **`.md`**, so it moves with the documentation, and a file neither tracked nor ignored moves it with no commit | `ruff format --check docs -v \| grep "Included path via" \| grep '\.md$'`; and `git ls-files '*.py' '*.pyi' '*.md' \| wc -l` = 204 = the printed count, with `git status --porcelain --untracked-files=all` empty | a published verification line can be re-derived only by someone who knows the corpus includes prose; Phase 30 §4(e) mis-attributed a real difference to "a different machine", and `docs/integrity_audit.md` 62(d) records that mis-attribution | Ruff's formatter accepts Markdown by default and nothing in this repository names that corpus; every quotation took the number at face value as a Python-formatting signal | the collector (§4.1 #4) prints the three tracked buckets and the exclusions, so the claim's producer names its own corpus; a future quotation is then traceable to a named file set instead of to a terminal, and `docs/integrity_audit.md` 62(d) gains a dated clause rather than a restatement | the census line and the formatter's own count compared in one command, both directions; a plant that adds a scratch `.md` and must be rejected by the census guard | 0 $ | `tools/inventory_orphan_code.py`, `tools/refactor_ceilings.json`, `docs/integrity_audit.md` (one dated clause), one plant | high |
| V2-03 | reproducibility-contract | **High** | 43 of the 95 frozen artifacts' `generated_by_command` strings cannot be run as written from the repository root, and 27 of those name no file at all: 16 `… (source: …)` prose-in-command, 15 bare filenames (`uv run python run.py`), 11 two-token mangles (`uv run python pricing_validation run.py`), 1 with no interpreter prefix (`benchmarks/quantlib/pricing_validation.py`) | the classifier probe in §4's P2 row, whose input is `evidence/manifest.json` and whose corpus is all 95 entries printed by name; and `grep -rl generated_by_command --include=*.py .` → one file, the writer | the project's central claim is "every published number traces to the command that produced it". For 43 artifacts that command is not runnable, so the trace ends at the ledger rather than at a shell — and the verifier's green proves only that the bytes match, never that the reproduction exists | each study writes its own `command` field into `summary.json`, and `scripts/build_evidence_manifest.py:120` copies it verbatim; no schema constrains the field and no guard parses it | D3/D4: the registry owns the canonical invocation and the builder *derives* `generated_by_command` from it, so the manifest can no longer hold a hand-typed command; the collector's §4.1 #3 census becomes a ceiling that must reach zero, with the fixture-provenance category declared and its annotation moved into a separate field | after P3.5's one re-run, the census prints 95 resolvable commands and a plant that corrupts one is rejected by L4's dry-resolve guard | 0 $ | `python/quantrisk/experiments/registry.py`, `scripts/build_evidence_manifest.py` → `tools/build_evidence_manifest.py`, every `experiments/*/results/summary.json` `command` field (regenerated, not hand-edited), `evidence/manifest.json` (rebuilt by the builder only, K4), one plant | high |
| V2-02 | orphan-code | **High** | 10 `sys.path` sites all inject `<root>/python`, which the editable install already provides — but 6 of the 14 studies load *published sibling studies* by repository path — 7 edges, four of them at module import time (`experiments/fourth_order_crossing_map/run.py:104`, `…/second_book_crossing_map/run.py:102` and `:103`, `…/fifth_order_crossing_map/run.py:64`, `…/sixth_book_crossing_map/run.py:72`, `…/restrike_gamma_map/run.py:295`, `…/two_factor_error_bound/run.py:180`), which no installed wheel can satisfy | `cd / && .venv/bin/python -c "import quantrisk; print(quantrisk.__file__)"` (resolves: the bootstrap adds nothing); and import a bootstrap-stripped copy of `experiments/sixth_book_crossing_map/run.py` from `/` → `FileNotFoundError: …/experiments/fifth_order_crossing_map/run.py` | D1's destination is unreachable by moving files alone: an importable `quantrisk.experiments.<task>` must import its siblings as modules, and the dependency order is a constraint on the whole of P3.3 — restrike_gamma_map before second_book/fourth_order, those before fifth_order, that before sixth_book, and stress_testing before all of them | the studies compose by path because the repository path is the only name they have for each other outside a package; nothing declares the edges, so no tool can see the chain | each absorption converts its sibling loads to `from quantrisk.experiments.<task> import …`, keeping the "load the definition, do not copy it" property that the comment insists on; P3.3's per-task order follows the measured dependency graph, and the registry records the edges | after P3.3, `python -c "import quantrisk.experiments.sixth_book_crossing_map"` from a clean venv with a neutral cwd must succeed, and the study's own guard test must still pass unmodified | 0 $ | the 6 coupled study modules and their 7 edges, the 8 independent studies, the tests that load them by path (`test_fifth_order_crossing_map.py`, `test_fourth_order_crossing_map.py`, `test_restrike_gamma_map.py`, `test_second_book_crossing_map.py`, `test_sixth_book_crossing_map.py`, `test_two_factor_bound.py`), the suite runner's member tuple | high |
| V2-06 | static-check-parity | Medium | the collector's coverage census: 23 files reached by mypy **and** ruff, 63 reached by ruff only, 0 uncovered; mypy's reported 23 equals an independent enumeration of `python/quantrisk`, so the gap is real and measured, not inferred | `uv run python -m tools.inventory_orphan_code` → `static_check_coverage.corpora` (printed with both corpora and `tracked_not_admitted_by_ruff`) | every study, every tool script and the mutation harness is type-checked by nothing, while D7's end state promises exactly one bucket per file | `mypy`'s target list in §7 step 4 and in CI is `python/quantrisk`, written when that was the whole Python surface; the corpus grew around it | D7: extend mypy's targets to the destination modules and `tools/`, and let the collector's per-file bucket table be the artifact the ceiling is read against, printing the corpus in both directions | the census must show each tracked file in exactly one bucket, and `mypy`'s own reported file count must keep agreeing with an independent enumeration — a disagreement is the instrument failing, not the code | 0 $ | `.github/workflows/ci.yml`, the §7 step-4 command in `REFACTOR_PROMPT.md` as quoted by `docs/reproducibility.md`, and whatever type errors the newly-covered 63 files reveal | high |
| V2-07 | reproducibility-contract | **High** | the recorded reproduction command is invisible to the ledger's own invariant: `command` and `command_source` are members of `VOLATILE_KEYS` (`python/quantrisk/experiments/evidence.py:43-61`), `_strip` drops them before the content digest (`:78`), so the verifier files a byte-differing, content-equal artifact as `volatile` (`scripts/verify_evidence_manifest.py:74-79`), counts volatile as a failure **only** under `--strict` (`:112`) and otherwise exits 0 printing "Evidence reproduces: the numbers are identical, only run metadata and timings moved." (`:116`) | `grep -n '"command"' python/quantrisk/experiments/evidence.py`; `sed -n '74,79p;112,122p' scripts/verify_evidence_manifest.py` | a frozen command can be wrong, or become wrong by a move, and both the manifest freeze and L1's digest invariant stay green — which is why §0's P2 and §13's L4 cannot be satisfied by the existing machinery and need a guard that did not exist before | the volatile set was drawn to make *timings and provenance* tolerable in 2026-09 and `command` was put in it because the string moved between machines; nothing then required the string to be executable | L4's guard dry-resolves every entry's command (module importable, or file present) and fails the build otherwise, with one plant corrupting a command; the ceilings file then keeps `commands_unrunnable_from_the_root: 0` honest | the guard rejects a planted command that names a nonexistent module, and `--check-ceilings` returns to exit 0 | 0 $ | one new guard test, `tools/build_evidence_manifest.py`, one plant | high |
| V2-08 | artifact-reconciliation | **High** | 18 of 95 frozen entries have `content_sha256: null` — 17 `.png` plus `benchmarks/suite/results/suite_summary.md` — because `canonical_text` returns None for anything that is not JSON or CSV; for them the verifier's only comparison is raw bytes, so any regeneration is `CHANGED` and exits 1 | the collector's ceilings path; reproduced by `.venv/bin/python -c "…Counter(a['category'] for a in arts if a['content_sha256'] in (None,''))"` → statistical_experiment 16, suite_aggregate 2; extensions png 17, md 1 | **P3.5's single re-run cannot satisfy L1 as written.** `suite_summary.md` carries wall-clock seconds, so re-running the suite necessarily changes its bytes; L1 compares *content* digests, and a null content digest has no content to compare, so the only movement the lane can observe is a byte change on an artifact that holds no number | the digest was designed for the two formats that carry measurements; the aggregate markdown and the plots were folded into the same ledger later, with byte-hash as their only owner | declare the byte-only set in `tools/refactor_ceilings.json` as measurement-of-machine with the reason (which is exactly the escape L1 grants), and keep `sha256` byte comparison for them; then P3.5's expected movement list is derived, not remembered | P3.5's digest report shows content unchanged for every JSON/CSV artifact, and names the 18 byte-only paths as declared movers | 0 $ | `tools/refactor_ceilings.json`, the P3.5 digest comparison | high |
| V2-09 | registry-parity | **High** | the repository's only two-sided enumeration guard gets its independence from the filesystem glob, which D1 deletes: `test_artifact_metadata.py:698` discovers with `glob("experiments/*/run.py")` + `glob("benchmarks/*/*.py")`, asserts `len(on_disk) >= 15` **before** comparing to `MEMBERS`, and loads the suite module by path | `sed -n '698,725p' tests/python/test_artifact_metadata.py` | if the registry becomes the source of truth and the test reads the registry on both sides, L5 passes by construction — the anti-pattern §15 names — and the floor that today catches a narrowed glob disappears with the glob | parity was proved against the one artefact that could disagree with a hand-maintained tuple: the filesystem layout the tuple was written from | keep the sides independent after the move: one side enumerates importable task modules through the package's own module finder, the other enumerates the registry table, neither calls the other, and each prints what it enumerated; a floor statement survives as a corpus print | the test fails when an entry is added to one side only, and the two enumerations are shown to be computed from different sources | 0 $ | that one guard, `python/quantrisk/experiments/registry.py`, the suite runner | high |
| V2-10 | verification-instruments | **High** | 26 of the 172 declared plants edit a file under `scripts/`, and **23 of those anchor on `scripts/run_mutation_suite.py`'s own source lines**; the harness resolves `REPO_ROOT = Path(__file__).resolve().parents[1]` (`:73`) and joins every plant path onto it, so its destination must stay at depth 1 | `grep -c 'path="scripts/' scripts/mutation_plants.py` → 26; `grep -c 'path="scripts/run_mutation_suite.py"' scripts/mutation_plants.py` → 23; `sed -n '73,76p' scripts/run_mutation_suite.py` | moving the harness into `python/quantrisk/verification/` (depth 3) silently repoints `REPO_ROOT` at the package root and invalidates all 172 anchors at once — the failure mode Phase 30 §4(c) recorded six times, here in its largest form and caused by the move itself | plant anchors are literal source text in the file they mutate, which is what makes them precise, and the same property makes them brittle to a relocation | P3.2 re-keys all 23 harness anchors in the commit that moves the harness, then runs the full sweep and reads its own summary line as the proof; `PLANTS_PATH`/`REPO_ROOT` are computed once from a declared root, not from `__file__` depth | `172/172 planted defects were rejected by their guard.` printed by the sweep at the post-move commit, plus the anchor self-test green | 0 $ | `scripts/run_mutation_suite.py` → its destination, `scripts/mutation_plants.py` (23 anchors), 11 `experiments/` anchors | high |
| V2-11 | packaging-dx | **High** | a published study cannot find its own inputs once installed, and fails silently: `FIXTURE_ROOT = Path(__file__).resolve().parents[3] / "data" / "fixtures"` (`python/quantrisk/data/fixtures.py:27`), `available()` returns `[]` when that directory is absent, `data/` is outside `wheel.packages`, and there is no `MANIFEST.in` | `sed -n '27p;54,60p' python/quantrisk/data/fixtures.py`; `git ls-files \| grep -i manifest.in` → empty (second check: `find . -maxdepth 2 -name MANIFEST.in` → empty) | the real-data study is a published artifact whose input the wheel does not carry; the §11 installed-user proof says such a task must **fail loudly naming the missing path** — today it would report "no fixtures" and could be tempted to synthesise, which V1 §4 forbids | the data layer was built as a repo-root convenience with the cache beside the checkout; packaging was never a target for it | `available()` distinguishes "root absent" from "root empty" and raises with the path; the registry entry declares whether its task needs a packaged fixture; Phase 4's proof exercises exactly one offline study and one that must fail loudly | the installed-user proof shows a loud refusal naming the missing path, and never a fabricated dataset | 0 $ | `python/quantrisk/data/fixtures.py`, one new guard test, Phase 4's proof | high |
| V2-12 | packaging-dx | **High** | 10 of 14 studies compute their artifact directory as `Path(__file__).resolve().parent / "results"`; the other 4 pin `REPO_ROOT / "experiments" / <task> / "results"` with `REPO_ROOT = parents[2]` plus a `sys.path` insert — both forms stop meaning anything once the module lives in site-packages | `grep -l 'RESULTS = Path(__file__).resolve().parent / "results"' experiments/*/run.py \| wc -l` → 10; `grep -c 'RESULTS = REPO_ROOT' experiments/*/run.py` → 4 files | K2 freezes the artifact paths while D1 moves the code that derives them; without a fix every moved study would write into site-packages, and the manifest's 66 `statistical_experiment` entries would name files that no longer exist | the studies were written to sit next to their output, which is right for a repo directory and wrong for an installed module | the registry entry carries the artifact path (D3 already says so), the module receives the output root as a parameter, and the default is resolved from the working tree when there is one and from an explicit `--out` when there is not; no study may fall back to its own package directory | P3.3's per-task gate: the task's artifact is still written to the frozen repo path, its bytes' content digest unchanged, and `-m` invocation from a neutral cwd writes only where told | 0 $ | all 14 study modules, the registry, `tools/run_benchmark_suite.py` | high |
| V2-13 | packaging-dx | Medium | an installed user can run nothing: `[project.scripts]` exposes `quantrisk.cli:main`, whose `build_parser()` registers exactly `validate`, `benchmark`, `demo` with `add_subparsers(required=True)`; there is no `run` or `--list`, and no study is importable from the package | `grep -n "add_parser" python/quantrisk/cli.py` → 3 | §2's whole promise — "a user who has installed the package runs one command to list every published study" — is false today, and the README's reproducibility section is written for the maintainer's layout | the CLI was built as a validation harness, not a distribution surface | D6 adds `run` with `--list`, its output asserted against the registry by a test that shares no source with the registry's enumeration (V2-09's discipline), and the three existing subcommands asserted byte-identical | `quantrisk run --list` enumerated in a clean venv equals the registry; the three old subcommands' outputs unchanged | 0 $ | `python/quantrisk/cli.py`, one guard test, `docs/reproducibility.md`, `CONTRIBUTING.md` | high |
| V2-14 | verification-instruments | Medium | a **shipped** module shells out to git: `python/quantrisk/experiments/metadata.py:93-103` runs `["git", *arguments]` with `cwd=REPO_ROOT` and returns `None` silently when the root is not a repository | `sed -n '90,104p' python/quantrisk/experiments/metadata.py` | artifact fields produced by this function describe the checkout, so an installed run records an environment truthfully only where a `.git` exists; the silent `None` is the difference between a missing field and a missing claim | provenance was written when every producer ran in the checkout | keep the behaviour, make the absence declared: the field names the command that could not answer, and the Phase 4 identity proof (`L8`) prints `module.__file__` beside it | the installed-user proof shows the field either populated or declared absent, never silently empty | 0 $ | `python/quantrisk/experiments/metadata.py`, the Phase 4 proof | high |
| V2-15 | documented-claims | Medium | the move's documentation blast radius is ~195 path or command quotations over 8 files (`README.md` 4, `CONTRIBUTING.md` 8, `docs/reproducibility.md` 15, `docs/architecture.md` 6, `docs/validation_matrix.md` 27, `docs/interview_defense.md` 41, `docs/project_scope.md` 16, `paper/technical_report.tex` 80); `CONTRIBUTING.md` is policed by **no** claim inventory, and `docs/architecture.md` is policed only for path existence (`test_artifact_metadata.py:445`) | `grep -cE 'experiments/\|run\.py\|scripts/\|uv run python' <file>` per file; `grep -rn CONTRIBUTING tests/python/*.py` → empty (second pattern: `grep -rln "CONTRIBUTING" tests/` → empty) | P3.3/P3.4 re-derive prose in the same commit as each move, and two of those documents have no guard to tell them they missed one; the architecture document will go red on the first task moved, which is correct but must not be mistaken for a defect | inventories were extended document by document against real reds (the project's own rule), and these two never produced one | each move's commit re-derives the documents it touches and adds any new counted claim to its inventory in the same commit (§13 L10); `docs/architecture.md`'s layout section is re-derived wholesale in P3.4, not patched | the repo's claim-inventory guards green at the final commit, and the architecture document's paths all exist | 0 $ | the 8 documents, `CONTRIBUTING.md`'s first inventory entry, `docs/architecture.md` | high |
| V2-16 | security-ci | Medium | two CI/guard surfaces can certify their own input's absence, both verified by reading them: `clang-format` is invoked through `find … \| sort \| xargs uv run clang-format --dry-run --Werror` with **no `-r`**, so an empty glob runs the formatter with no files and reads stdin; and the offline lane's reference tool resolves through a `pytest.skip` fallback (`tests/python/conftest.py:82-92`), so a missing binary silently removes a whole comparison rather than failing it | `sed -n '37,40p' .github/workflows/ci.yml`; `sed -n '74,92p' tests/python/conftest.py`; `find cpp bindings tests/cpp \\( -name '*.cpp' -o -name '*.hpp' \\) \| wc -l` → 77 today, which is why the first is latent rather than live | the xargs form is one token from being a dead gate the moment a refactor empties a directory, and the skip is honest only while somebody reads the skip count | add `-r`; keep the reference-tool skip's declared sentence and have the collector's ceilings file record the skip set, so a growing skip list is visible rather than silent | the CI step names paths that exist at the final commit; the lane's skip list is printed by name in §12 | 0 $ | `.github/workflows/ci.yml`, `tests/python/conftest.py` | high |
| V2-17 | facts-protocol | Medium | D1's class table assigns only `experiments/<task>/run.py` to the package, but 9 of the 95 frozen commands are produced by `benchmarks/*/*.py`, so five producers would sit outside the registry that owns the command string | classify every `generated_by_command` in `evidence/manifest.json` by its target path and read the prefix — 4 `monte_carlo_validation.py`, 2 `benchmarks/pyportfolioopt/optimisation_validation.py`, 1 `path_dependent_validation.py`, 1 bare `benchmarks/quantlib/pricing_validation.py`, 1 `performance monte_carlo_speed.py` | read literally, the packet's P3.3 (14 commits) leaves `commands_not_module_path` at 9 forever and L4 can never pass; the ceiling would be met only by exempting the five, which is the exemption-hides-the-defect-class trap | apply D1's own instruction — members are "by role, not by count, derive the list in Phase 1". The benchmark validators are published studies by role, so the registry declares 19 tasks and P3.3 is 19 commits | the parity test compares the registry against a filesystem walk that recognises both layouts, and `commands_not_module_path` must reach 0 over all 95 entries in P3.5 | 0 $ | registry (5 extra entries), P3.3's commit count, `docs/architecture.md`'s layout section | high |
| V2-18 | facts-protocol | Medium | §7 step 6 prescribes `uv run --frozen python scripts/run_mutation_suite.py --list`, and §7 step 4's lane list names other pre-refactor paths; after P3.2b those commands exit 2, because the harness is `python/quantrisk/verification/runner.py` | the gate driver ran §7 step 4 verbatim and reported `plant-list rc=2`; re-running the same lane as `uv run python -m quantrisk.verification.runner --list` gives rc 0 and 172 lines | a session resuming from §7 literally will read its own baseline as broken, and the easiest way to "fix" that red is to skip the lane — which is §15's "a gate stopped running while the lane stayed green" | the prompt's command list was written against the tree it was approved on and never scheduled to be re-derived, because editing it needs maintainer approval and §4.4's leak test | the driver's lane list is now the post-move form, and this section's §9 entry records which §7 commands were measured where | 0 $ | `REFACTOR_PROMPT.md` §7 steps 4 and 6, pending approval — not edited in this commit | high |

| V2-20 | artifact-reconciliation | **High** | studies write the **code path that produced a figure** into the artifact body: `experiments/restrike_gamma_map/run.py:777` records `"source": "experiments/stress_testing/run.py:run_linearisation"`, `experiments/two_factor_error_bound/run.py:437,743` do the same, and nothing asserts them — the two
lines first read as assertions are the fake-checkout file sets in
`tests/python/test_second_book_crossing_map.py:371` and `test_fifth_order_crossing_map.py:397`, while
what does compare them is the replay guard `_assert_same_result`, which walks `.source` leaf by leaf | `grep -rn '"source": "experiments/' experiments/*/run.py`; `grep -n "stress_testing/run.py" paper/technical_report.tex` (line 1378 quotes it as the study's prose too) | `source` is **not** in `VOLATILE_KEYS`, so it is hashed into `content_sha256`. The moment the cited file moves, the honest regeneration changes the digest of artifacts in the `statistical_experiment` category — and L1 as written permits movement only in categories declared machine-measurement, so **P3.5's single re-run would halt the lane** on a provenance edit, or the absorb-commits would be forced to leave stale paths that name files which no longer exist | the artifacts conflate "which number" with "which file computed it", and the second half was written when the file was the only name the code had | options and their costs, for adjudication before P3.5: (i) re-express provenance as a registry reference (`stress_testing:run_linearisation`), re-derive once, and declare that named field's movement in the ceilings file with its reason; (ii) add `source` to `VOLATILE_KEYS`, which weakens a gate and needs an explicit yes; (iii) re-run per absorption commit, which breaks D5's one re-run and multiplies volatile-field noise | whatever is chosen, the digest report must enumerate every entry whose content moved and its reason, and the replay guard must normalise the citation to the registry reference — narrowing a comparison, not deleting one | 0 $ | the 2 studies' 3 provenance strings, the shared replay guard in `tests/python/test_two_factor_bound.py`, 3 frozen artifact fields, `evidence/manifest.json` (rebuilt by its builder), `paper/technical_report.tex` line 1378, the ceilings file | high |

| _(the low-severity hygiene from lane 4 — 24 `spec_from_file_location` sites in `tests/python/` that switch to imports as their targets move — is carried in the commit sequence rather than as its own finding; V2-19 is deliberately absent because it would restate V2-04)_ | | | | | | | | | | | |

| V2-21 | citation-resolution | Medium | `paper/technical_report.tex` carries 315 `\src{}` / `\srcin{}` repository-path citations (a brace pass over the tex that skips only the macro's own definition lines) and **no guard proves any of them resolves**. Six named files that do not exist at this commit's parent: four `experiments/<task>/run.py` for studies the lane had already absorbed (lines 1475, 1510, 1539, 1550), this study's own line 1401, and `scripts/derive\_fifth\_order\_partials.py` at 1530 -- the last created by P3.2's own move five commits back. The first four survived because §11 step 9's probe matched the plain spelling while LaTeX writes `fourth\_order\_crossing\_map` | `git show HEAD:paper/technical_report.tex` through the brace pass: 315 read, 6 unresolved; the same pass over this commit's tex reads 315 and resolves 315 | the report is the artifact a reader opens, and a citation to a file that is not there is the defect class V2-20 just declared for `source` fields inside artifacts -- with the difference that nothing here can see it, because what *is* guarded over the paper is numeric, not structural | the claim inventory keys on numbers and counted nouns; path existence is guarded for `docs/architecture.md` alone (`test_every_path_the_architecture_document_declares_exists`), and nothing extended that loop to the paper | extend that same loop-guard to the paper: parse the tex for `\src{}` / `\srcin{}`, un-escape `\_`, drop any `:line` suffix, resolve each against `checkout_root()`, and keep an explicitly named exemption list for dated records (`docs/phase_reports/**`, `docs/release_notes_v1.*.md`, the numbered findings of `docs/integrity_audit.md`) rather than a pattern that silently absorbs them | the guard reddens when one cited path is renamed -- proven by the falsification probe on a single citation, with the enumerated count and the exemption set printed in the failure. The pass that wrote this row already does the resolution half and is the seed for it | 0 $, one commit | `tests/python/test_artifact_metadata.py` plus the fifteen quotations of the test-count pair (the same cascade any added case pays), `paper/technical_report.tex` read-only | high -- measured at absorption 7, where six stale citations were found this way and all six re-derived |

| V2-22 | guard-denominator | **High** | `test_every_registered_experiment_is_named_in_the_report` asks whether the report names every registered experiment, and built its denominator as `{experiments/<dir>/ for member in suite if member.script.startswith("experiments/")}`. P3.3a made `member.script` a property over the registry, so each absorbed task started reporting `python/quantrisk/...` and **fell out of the filter** -- six commits later the guard checked 7 of the 14 studies under `experiments/`, while passing every run and keeping its own plant green | set difference between the registry's artifact directories and the set the guard constructs: `dropped out of the guard: fifth_order, fourth_order, restrike, second_book, sixth_book, stress_testing, two_factor` | a gate that lost half its coverage is the L3 failure this lane is not allowed to have caused, and it caused it without touching a `skip`. The report can now omit any absorbed experiment and stay green -- and the plant that exists to catch exactly that was anchored on the stale citation, so it proved the *old* denominator only | the guard keyed its population on the shape of the pre-refactor path rather than on the registry, and the refactor changed that shape one task at a time -- which is precisely the case V2-09 registered for the disk-to-member guard, where the same trap was avoided by walking both layouts and printing each pattern's count | fixed in absorption 7: the denominator comes from `Task.artifact` parts, and the token carries no trailing slash so `experiments/<dir>/run.py`, `experiments/<dir>/results/...` and `python/quantrisk/experiments/<dir>` all name the study. The plant was re-keyed to the new citation and proved to fire by applying it in-tree (guard rc 1), restoring under a SHA-256 check (`b70cca9ac01e`) and seeing rc 0 again | the two other prefix classifiers -- `tests/python/test_task_registry_parity.py:35` and `tools/inventory_orphan_code.py:332` -- were read and are layout-safe, which is how `filesystem_units` reaches 19 with 7 units in the package | 0 $, carried by absorption 7's commit | this one guard, one plant anchor, `paper/technical_report.tex` read-only | high -- measured, fixed and negative-controlled at absorption 7 |

| V2-23 | artifact-reconciliation | Medium | `content_digest` waives the keys in `VOLATILE_KEYS`, which covers `environment` -- but four committed artifacts record the **package version outside** that block, under `oracles.versions.quantrisk` or `oracle.versions.quantrisk`, and neither container is in the set. The replay guards already know this: `tests/python/test_two_factor_bound.py` waives `oracles` by name in its own comparison list. So an artifact's *content* hash moves when the version moves, with no number in the study changing, and P3.5's L1 digest report would have to explain a difference that is pure release metadata | walk every committed artifact through `strip(VOLATILE_KEYS)` and keep paths ending in `quantrisk`: four hits -- `linearisation_error_bound.json`, `two_factor_bound.json`, `var_backtesting_validation.json` all at 1.8.0, `real_data_risk_study.json` at 1.9.0, each under a `.or…cle.versions.quantrisk` path that survives the waiver | `quantrisk_version` is volatile *information* under an ad-hoc key name, and the two instruments that compare artifacts -- the digest and the replay guard -- disagree about it. That disagreement is the finding, not a residual to caveat: one of the two is wrong about what an artifact's content is | the version block was named study by study in Phases 2 to 13, before `VOLATILE_KEYS` existed, and the set grew by listing what each phase happened to notice rather than by a rule about environment | decide at P3.5 with the other declared movements: either add the two container spellings to `VOLATILE_KEYS` with the reason recorded in `tools/refactor_ceilings.json`, or move the field inside `environment`, where it is already waived. The second is a producer change to four studies and re-derives their artifacts; the first is one line and a declaration. Neither is this lane's call to make silently | whichever is chosen, the digest report must not enumerate these four as "numbers moved", and the waiver must live in one place -- the replay guard's local list is deleted or replaced by the shared set, not duplicated | 0 $ | `python/quantrisk/experiments/evidence.py`'s set, four artifacts, the replay guard's local waiver list, `evidence/manifest.json` digests | medium -- population measured, instrument disagreement read, the fix is a P3.5 decision |

One investigator's claim was **refuted by reading the code** and is not carried: that
`test_artifact_metadata.py:917`/`:927` compare a glob against the README with no floor. They do have one —
`assert listed, "no rows were read out of the experiments table"` and
`assert claim, "README.md no longer states the experiment count"` — so both-sides-empty goes red, not green.
The record of the lanes is `build/v2-phase1-lanes.md`, which marks every row re-run here with `[V]`.

## 7. Liveness of the laws, as of Phase 0

§13's table is produced at the end of Phase 1, after each `check:` has been executed. What Phase 0 can
already settle, and what it cannot:

| Law | Status at Phase 0 | The reading that decided it, or why it cannot be read yet |
|---|---|---|
| L3 no gate weakened | ACTIVE | the §2 table's rc=1 is a gate that fired; nothing in this lane adds a skip, and the skip delta in §3 is the runner's declared `latexmk` skip, not a new one |
| L6 no bootstrap hacks | ACTIVE, unmeasured | the census is the collector's; the 63-file corpus outside the package is the denominator §4.3 demands be printed |
| L10 counted claims owned | ACTIVE | the repository's own inventory guards pass inside the 470-test lane measured here |
| L12 zero external spend | ACTIVE | no dependency added; the export was built with `--frozen` from the committed lock |
| L13 baseline purity | ACTIVE | this file's §1 names the revision **and** the environment per lane, taken from a single export of a CI-verified revision, with no foreign work in it |
| L1, L4, L5, L7, L8, L9 | VOID until their precondition exists | L8 is partially exercised (§1's identity probe) but its check is the Phase 4 wheel proof; L1/L4/L5/L7/L9 require §5's architecture steps |
| L2, L11 | ACTIVE from the next commit | findings now exist |

## 8. How to resume this lane

1. `git fetch && git log --oneline -1` — if `origin/main` moved, re-read this file's §1 against the new
   head before trusting any stored exit code.
2. Re-run §7 step 4 in a fresh detached export, exactly as §1 describes — **except** that two of its
   commands name paths this lane has already moved (V2-18): the plant inventory is
   `uv run python -m quantrisk.verification.runner --list`, and any `scripts/…` invocation in that list
   is the pre-refactor spelling. If a lane is red that this file recorded green, that is a finding, not
   noise, and it is entered in §6 before anything is fixed.
3. Write `tools/inventory_orphan_code.py` (one collector, nothing else), run it, read `§4`'s three
   premises from its snapshot, and append the readings to §9 of this file in the same commit that adds the
   ceilings file `tools/refactor_ceilings.json`.
4. Phase 1 diagnosis in §8's lanes, findings in §6's schema, then **stop at §9's approval gate**: silence
   is not approval.

## 9. Dated entries

### 2026-10-20, the collector and the premise readings (`tools/` + this section)

The instrument is `tools/inventory_orphan_code.py`, invoked as `uv run python -m
tools.inventory_orphan_code`, writing `build/orphan_inventory.json` (gitignored telemetry). The policy
file is `tools/refactor_ceilings.json`, and `--check-ceilings` now *compares* rather than prints: at
this revision it exits **1** with four named violations — bootstrap 10, by-path sites 19,
commands-not-module-path 95, commands-unrunnable-from-the-root 43 — and two oks
(`external_spend_usd` 0, `tracked_python_files_in_no_static_check_bucket` 0). Its two-sided key check was
proven to fire by declaring a key the collector does not compute and reading the failure back:
`FAIL ceilings file declares 'zzz_not_measured' but the collector computes no such metric`, the file
then restored byte-identical (`diff -q` → identical). **It is deliberately not a CI lane yet**: §16
requires the committed suite green at every commit, and a ceiling that measures the debt this lane exists
to remove is red by construction until P3.4/P3.5 clear it. The key that must not rot is the flip — three
ceilings carry `may_be_unmeasured: true` today (registry parity, plant verdict, installed identity), and
each one has to be flipped to measured, in the phase that makes it measurable, or the checker's own
absence rule reports it.

All three premises are **ACTIVE**, and one of them is active for a reason the prompt did not state.

- **P1 — confirmed, with a different cause.** `git ls-files` outside `python/quantrisk` is 63 files:
  10 inject a path into `sys.path`, 12 load a file by naming its path, 35 import the package normally,
  6 reach nothing. Every one of the ten injections adds the same directory, `<root>/python`, and the
  editable install already puts the package there: from `cwd = /`, `.venv/bin/python -c
  "import quantrisk; print(quantrisk.__file__)"` resolves inside the checkout, so those ten lines are
  dead weight — which is what lets L6's ceiling be zero rather than "one declared bootstrap site". The
  live coupling is elsewhere. Deleting the bootstrap line from a scratch copy of
  `experiments/sixth_book_crossing_map/run.py` and importing it from `/` does not fail on `quantrisk`;
  it fails on `FileNotFoundError: …/experiments/fifth_order_crossing_map/run.py`, because that study
  loads a *published sibling study* at import time — and does so on purpose:
  `experiments/fourth_order_crossing_map/run.py:104` says the phase-15 module "is the definition of the
  book… loading it rather than copying four functions out of it is what makes 'the same truncation plus
  the order-four terms' a statement this file cannot quietly break". The graph, read off the 14 studies
  that carry a `run.py`: **7 edges over 6 studies** — `stress_testing ← restrike_gamma_map ←
  fourth_order_crossing_map ← second_book_crossing_map ← fifth_order_crossing_map ←
  sixth_book_crossing_map`, plus `stress_testing ← two_factor_error_bound` — and the other 8 studies are
  independent. Four of the seven loads run at module import time, so an installed package would fail on
  *import*, not on run. The refactor's real problem is therefore not that scripts cannot find the
  package — it is that **studies find each other by repository path**, and a repository path means
  nothing inside a wheel. Finding **V2-02**, High.
- **P2 — confirmed and quantified in §4 and finding V2-03.** The collector's own census is the policy
  now, and it reads 52 resolvable, 16 annotated, 15 bare-filename-does-not-exist, 11 mangled, 1 with no
  interpreter prefix, and **zero** in the canonical `python -m` form.
- **P3 — confirmed, lopsided rather than absent.** The two-sided construction holds: mypy reports 23
  source files and independent enumeration of `python/quantrisk` finds 23, so the instrument is not
  lying about its own corpus. Ruff's resolver log admits all 86 tracked Python files (and 112
  non-Python ones — the markdown that V2-05 is about), and `tracked_not_admitted_by_ruff` prints empty,
  so the zero in the "uncovered" bucket is a measurement, not an absence. But the split is 23 files with
  both tools against 63 with ruff only, and those 63 include every study, every tool script and the
  mutation harness. Finding **V2-06**, Medium.

Two readings this session owes rather than hides. The `--check-ceilings` comparison is enforced only by
the collector's exit code; no test in `tests/python/` runs it yet, so nothing stops it being deleted
from a CI step without anything noticing — that belongs to P3.7's gate, and it is the reason this entry
says *not a CI lane yet* in as many words. And the plant verdict key reports `None` even though the last
full sweep printed `172/172` on `58b6c22`: the sweep's line is the only acceptable evidence and it was
read on a different revision, so the collector refuses to launder it.

### 2026-10-21, Phase 1 complete — the §9 gate packet

The survey §6 requires is written into `docs/ecosystem_research.md` §10: seven candidates read in their own
repositories at a named ref, each mechanism cited to the file that carries it, every cited URL opened
rather than constructed, and the negatives kept as evidence — `Riskfolio-Lib`'s `linters` job installs
requirements and lints nothing, which is the failure mode this lane is one token from. Two §5 decisions
change on that evidence, and both change because of a finding measured here rather than a fashion. **D4′**:
the registry owns the canonical *prefix* and the producer appends the argv it actually received, because a
registry that templates the whole string would erase `--paths 200000`, and a recorded command carries
exactly such a flag. **D3′**: a registry entry validates itself against a declared key set, and discovery
that cannot resolve is a build failure rather than a warning. No new dependency — the boundary contract the
survey admires (kedro's `[tool.importlinter.contracts]`, read at `pyproject.toml:176-222`) is implemented as
a hand-written guard over the AST walk the collector already performs.

**Findings ranked by impact × effort × risk.** "Blocking" means it must be settled before the first Phase 3
commit, not merely during it.

| rank | id | severity | why it ranks here | effort | risk |
|---|---|---|---|---|---|
| 1 | V2-08 | High | **blocking.** L1 cannot be satisfied as written: 18 of 95 entries have a null content digest, so their only owner is a byte hash, and the mandated single re-run necessarily moves `suite_summary.md`. Decide before the run, or the run halts the lane on an artifact that holds no number | declare a set in the ceilings file | cheap to declare, fatal to discover late |
| 2 | V2-07 | High | **blocking.** `command` is a `VOLATILE_KEY`, so no existing gate can disagree with a reproduction command that names nothing; L4 needs a guard that does not exist yet, and premise P2 is exactly this | one guard plus one plant | low |
| 3 | V2-09 | High | **blocking.** If the registry becomes both sides of L5's parity test it passes by construction, and today's guard draws its independence from a glob D1 deletes | shapes P3.1 | high if discovered after the move |
| 4 | V2-10 | High | 23 of 172 plants anchor on the harness's own source lines and `REPO_ROOT` is `parents[1]`; a deeper destination silently disarms every plant | re-key inside the move commit, prove by sweep | high — silent by nature |
| 5 | V2-12 | High | 10 studies take their artifact directory from `__file__` and 4 from `parents[2]`, against a K2 that freezes those paths | per task in P3.3 | medium |
| 6 | V2-02 | High | 7 sibling-study edges over 6 studies, 4 of them at import time; this fixes the absorption order rather than a directory listing choosing it | per task in P3.3 | medium |
| 7 | V2-03 | High | 43 of 95 recorded commands are unrunnable; D4′ plus P3.5's re-derivation closes it | in P3.5 | medium |
| 8 | V2-11 | High | fixtures are not in the wheel and `available()` answers `[]` instead of naming the missing path, so the installed-user proof would otherwise be a lie | code change in P4.1 | medium |
| 9 | V2-13 | Medium | the mission's user-facing claim is false today: three subcommands, no way to run a study | P3.6 | low |
| 10 | V2-15 | Medium | the documentation blast radius, including two living documents no claim inventory covers | per-commit re-derivation | medium |
| 11 | V2-06 | Medium | 63 of 86 files are type-checked by nothing | P3.7 | low |
| 12 | V2-05 | Medium | the formatter census counts prose, and an audit record explains a spread by machine rather than by file set | dated clause plus census | low |
| 13 | V2-16 | Medium | `xargs` without `-r`; a reference-tool skip that can quietly remove a whole comparison | one-token CI change | low |
| 14 | V2-14 | Medium | a shipped module shells out to git and returns `None` silently off-repo | P4.1 | low |
| 15 | V2-04 | Low | §7 step 5's "two files" is three | record | none |
| 16 | V2-01 | Low | the prompt's own step-3/step-8 ordering | record | none |

**Proposed Phase 3 sequence** — one line per commit: finding → change → verification. Each commit's gate is
the full §7 suite plus the named check; `S` marks a commit after which a ceiling key must move.

| # | commit | finding → change | verification |
|---|---|---|---|
| 1 | P3.1a | V2-09/D3′ → `python/quantrisk/experiments/registry.py` with a declared key set, a canonical-prefix builder, artifact path and category; an unresolvable entry raises | L5's two-sided test lands **in this commit**, one side from the module finder and one from the registry table, neither calling the other, each printing what it enumerated; full suite |
| 2 | P3.2a | V2-10 → `scripts/mutation_plants.py` to `python/quantrisk/verification/plants.py`; the harness's `PLANTS_PATH` follows; every by-path loader of the plant module updated | anchor self-test green; full suite; the sweep is not yet run |
| 3 | P3.2b | V2-10 → harness to `python/quantrisk/verification/`, with the root declared rather than inferred from `__file__` depth; re-key its 23 self-anchors in the same commit | `--list` still enumerates 172; full suite |
| 4 | P3.2c | V2-10 → `scripts/derive_fifth_order_partials.py` to verification; re-point the 11 `experiments/` anchors P3.3 invalidates | **the full sweep, once, at this commit**, its own summary line as the proof; L7 recorded |
| 5–18 | P3.3 ×14 | V2-02 and V2-12, **one study per commit in the measured order** `stress_testing`, `restrike_gamma_map`, `fourth_order_crossing_map`, `second_book_crossing_map`, `fifth_order_crossing_map`, `sixth_book_crossing_map`, then the 8 independents | each: registry entry added; `run(argv) -> dict` plus a thin `__main__`; the bootstrap line dies; sibling loads become package imports; its tests switch from path-load to import; command-string assertions become the canonical invocation **declared as an intent change in the message**; the artifact still lands on the frozen repo path; full suite |
| 19 | P3.4a | V2-15 → `tools/` receives the 11 repo scripts; the suite runner consumes the registry; the CI step's path changes in the same commit | the survey's "guard the CI file" test; full suite; `S: bootstrap_sites → 0` |
| 20 | P3.4b | V2-16 → `xargs -r`, the reference-tool skip's declared sentence, ceilings corpus prints | full suite |
| 21 | P3.5 | V2-03, V2-07 and V2-08 → declare the byte-only artifact set; **the one** suite re-run; the builder re-hashes from registry-derived commands; the verifier proves nothing else moved; re-derive every document that quotes a moved path | L1's digest report: which categories moved, which could not, matched against the ceilings file; `S: commands_not_module_path → 0`, `commands_unrunnable_from_the_root → 0` |
| 22 | P3.6 | V2-13 → CLI `run` with `--list`; the three existing subcommands byte-identical | `--list` asserted against the registry by a test sharing no source with its enumeration; old outputs compared byte for byte |
| 23 | P3.7 | V2-06 and V2-05 → mypy targets extended to the destination modules and `tools/`; the census written into the ceilings file; a dated correction to `docs/integrity_audit.md` 62(d) | full suite including the extended `mypy`; the uncovered bucket prints what it counted and stays structurally able to fail |
| 24+ | Phase 4 | V2-11 and V2-14 → wheel, clean venv, neutral cwd, identity asserted; a loud refusal naming the missing fixture; documentation coherence; dead-glue deletion; the canonical invocation in the contributor guide | §11's four items, each with its own reading |

**Declared blast radius**, derived from the findings rather than guessed: 14 study modules and their 14
registry entries; 11 `scripts/*.py` into `tools/`; 3 verification instruments; **21** test files that load
code by path and **9** that assert a command string; **37** plant anchors naming a path that moves (26 under
`scripts/`, 11 under `experiments/`); `.github/workflows/ci.yml`; `pyproject.toml` for mypy targets only;
nine living documents carrying the path or command quotations counted per file in V2-15; the 95 artifact
`command` fields, regenerated by their producers and excluded from content digests by design (V2-07); and
`evidence/manifest.json`, rebuilt by its builder and never hand-edited (K4). **Dated records are outside
this radius deliberately:** `docs/phase_reports/*`, the release notes and the release bodies keep the paths
they were written against, because they are records of a run rather than instructions for one.

**Not proposed:** moving any artifact path (K2), touching `cpp/`, `bindings/`, `CMakeLists.txt` or
`CMakePresets.json` (K1), changing a tolerance or a formula (K5), adding a dependency (L12), or a new
manifest field. `docs/ecosystem_research.md` §10 records the field gaps the survey found — `seed`,
`config_hash`, a quarantined state — as V3 candidates, each with the reason it was declined in this lane.

### 2026-10-21, the §9 gate: approval, one scope correction, and where this lane commits

The maintainer approved the packet in full — the ranking, the ceilings dispositions for V2-08 and V2-07,
the D3′/D4′ amendments, and the flow deviation that runs the 172-plant sweep once after P3.2c rather than
after each of its three moves. That approval is the reason Phase 3 code exists; nothing in Phase 3 was
started on the standing authorization alone.

One scope fact the packet undercounted, found while writing the registry rather than assumed: D1's class
table names only `experiments/<task>/run.py`, but **9 of the 95 frozen commands are produced by
`benchmarks/*/*.py`** (probe: classify every `generated_by_command` and read its prefix — 4
`monte_carlo_validation.py`, 2 `benchmarks/pyportfolioopt/…`, 1 `path_dependent_validation.py`, 1 bare
`benchmarks/quantlib/pricing_validation.py`, 1 `performance monte_carlo_speed.py`). Under the literal
class table, `commands_not_module_path` could never reach zero, because five producers would sit outside
the registry that owns the command. D1's own instruction — *"by role, not by count — derive the list in
Phase 1"* — resolves it: those validators are published studies by role, their outputs are hashed
evidence, so the registry declares **19 tasks** and P3.3 is 19 commits, not 14. Finding **V2-17**; no §5
decision changes, because deriving the list is what §5 asks for.

**Branch decision, recorded because the executing skill's default differs.** This lane commits to `main`.
The repository is trunk-based by practice: 59 phases landed there, CI's three lanes (the oracle-backed
suite, the tag/history Phase 33 gave the runner) trigger on push to `main`, and §16 requires the gate suite
green *on CI for the final commit*, proven from the run's own log. A long-lived branch would make P3.5's
single re-run and L1's digest comparison provable only on a revision that never executed. The maintainer's
approval of the packet, whose verification column reads "full suite" and "CI", covers this.

### 2026-10-21, P3.1a — the registry lands, and its own guard was written first

Red captured before any registry existed: `tests/python/test_task_registry_parity.py` failed 4/4 with
`ModuleNotFoundError`, then 6/6 green with `python/quantrisk/experiments/registry.py` present. Both sides
print their enumeration (`filesystem 19 units`, `registry 19 tasks`), the registry is a literal table and
not a glob, and the ceiling key `registry_parity_mismatch` went from skipped to **measured 0** with its
`may_be_unmeasured` flag removed in the same commit — the rule §9 states for every such key.

Six new tests moved the published pytest pair, and the lane's own count guards refused the stale
quotation, exactly as `REFACTOR_LEDGER.md` §5 predicted: `539/470 → 545/476` across five living documents,
four plant anchors and three census gold lists. The cascade ran from a script that verifies each pair
occurs exactly once before writing, and is resumable — it reports the sixteen already-applied pairs rather
than refusing. The report PDF was rebuilt (`bundle 5fab6f2fb74b`, `pdf 79b30ec30f2c`, 1,005,809 bytes)
because the tex changed, and the two freshness guards then passed. Full §7 suite on the committed tree:
ten lanes, every exit code 0, `545 passed`, offline probe `476 tests collected`.

Two of my own defects are part of this record. The collector imported the registry under the name built
from the **repository** path (`python.quantrisk`), which resolves to a shadowing namespace and dies on the
compiled extension — the import path is `quantrisk`, and the fix is a named constant rather than a
`replace('/', '.')`. And the first version of the canonical-command test used a `task_id` containing a
hyphen, so it tripped the identifier rule and passed while proving nothing about invocations; the id is
now `hand_typed` and the assertion exercises the rule its name claims.

### 2026-10-21, P3.2a–b — the verification instruments are inside the package

`scripts/mutation_plants.py` → `python/quantrisk/verification/plants.py` and
`scripts/run_mutation_suite.py` → `python/quantrisk/verification/runner.py`, invoked as
`uv run python -m quantrisk.verification.runner`. The harness imports the list as a package module, and
so does its test, which is what the census reports: by-path load sites **19 → 17** across the two moves,
files classified `by_path_importlib_load` **12 → 10**, and the harness's own class now
`installed_import`. The 23 plants that anchored on the harness name its new path; the anchor self-test
and the 172-line `--list` are green, and the sweep's own summary line remains the proof and is scheduled
once, at the end of P3.2, per the approved packet.

`REPO_ROOT` is no longer `parents[1]`. It walks up to the first ancestor holding both `pyproject.toml`
and `.git` and raises, naming the path it gave up on, if none exists — the alternative V2-10 warned about
is a silent two-levels-deeper root that points all 172 plants at nonexistent files and reports that as a
sweep of missing targets. mypy's corpus is **27 files** with its two-sided agreement intact, and the new
coverage found one genuine defect rather than a style complaint: at `runner.py:795` the pairing audit
iterated `record["others"]`, typed `object`, so the fix narrows with an assertion naming what it found
instead of letting a `join` over nothing print a clean line.

Nine living command and file quotations moved with the harness (`CONTRIBUTING.md` 3,
`docs/interview_defense.md` 6); the dated rows that record *where the sweep was promoted to* in Phase 14
and the register items that describe that phase keep the old path, because they report an event, not an
instruction. Two things this commit did not do: edit `REFACTOR_PROMPT.md` §7, whose step-6 command is now
stale and is recorded as **V2-18** pending approval, and run the sweep — the gate driver's
`plant-list rc=2` after the move was this lane's own instrument lagging one revision, now repointed and
reading rc=0 with 172 lines.

### 2026-10-21, P3.2's proof — the sweep's own line, read from the sweep

`uv run python -m quantrisk.verification.runner --all`, on the committed tree `32b76d5`, printed:

> `172/172 planted defects were rejected by their guard.`

exit 0, wall 708 s, and no line in its output carries any of the non-caught statuses
(`guard-stayed-green`, `sweep-stopped-early`, `anchor-not-unique`, `mutation-was-a-no-op`,
`target-already-modified`, `restore-mismatch`, `probe-file-already-in-the-tree`); `git status
--porcelain` is empty afterwards with one exception the sweep has always left — the empty
`experiments/_mutation_probe/` directory its two `tree` plants unlink files from but never remove, which
Phase 30 §4(f) recorded and git cannot see.

That is L7 satisfied for the instruments as they now stand, and it is the only acceptable evidence for it.
The collector deliberately does **not** grow a sweep-reading key: the sweep's output is gitignored
scratch that CI never has, and a ceiling satisfiable only on the machine that ran it is §4.3's "never
ratchet a key that cannot fail where it runs". What the collector measures is the declaration (172, by
`--list`), and the repository's own guard already fails any document mis-quoting it;
`plants_not_rejected_by_their_guard` keeps `may_be_unmeasured` with its corpus text naming where the
proof lives.

Two numbers moved as a consequence rather than as prose: mypy's checked corpus **23 → 28** source files,
because the instruments are now inside a checked target — and the newly-covered code produced one real
defect at the pairing audit's print, fixed by narrowing rather than by silencing; and the by-path load
census **19 → 17**. No plant escaped and none lost its anchor across the two moves, because the 23
harness anchors were re-keyed in the commit that moved the harness: that is V2-10's discipline observed,
not a lucky outcome.

### 2026-10-22, P3.3a — the suite stops storing paths the registry owns

Reading `stress_testing`'s dependents for absorption #1 turned up a step §8's lane summaries had not:
`scripts/run_benchmark_suite.py`'s `Member` tuple carried its own `script`, `artifact` and `kind` for all
19 tasks. Those three fields are exactly what D3 gives to the registry, so every absorption commit would
have retyped a path in a second file — V2-03's mechanism, reproduced 19 times — and
`test_every_experiment_and_benchmark_script_on_disk_is_a_suite_member` would have needed rewriting once
per move. It also decides, before the first move, how an absorbed task is *executed*: `[sys.executable,
member.script]` would run a package `__main__.py` as a file, which puts a repository directory on the
subprocess's `sys.path` and is the thing L6 counts.

The member now stores its key and its own claims (title, headline key paths, requires, summary, plot) and
reads the three registry-owned fields through `Member.task`; a key with no entry raises at import rather
than inside a subprocess loop. `execute()` runs `-m <module>` for an absorbed task and the script path for
one not yet absorbed, and that second branch is scheduled to die with the lane's last commit.

**The verification, both directions.** The equivalence claim is that this changes no published number, so
it was measured rather than argued: `--no-run --out build/p33a-before` at `75d6e81` and
`--no-run --out build/p33a-after` at this commit produce `members` arrays that compare equal field for
field, all 19, and a byte-identical `suite_headline.csv`; `suite_summary.md` differs only in its header
block, which names the run's own `--out` path, its timestamp and the dirty-tree banner. The two guards
were shown able to fail before they were believed: hard-coding `Member.script` to a literal reddens the
structural guard *and* the disk-to-registry guard (with its per-pattern print reading
`experiments/*/run.py=14, benchmarks/*/*.py=5, …__main__.py=0, …*.py=0`), and adding a phantom task to the
registry reddens the missing-member guard. Both probes were undone by copying a snapshot taken before
them and verifying the restored file's SHA-256 equals the snapshot's, and the only files the commit
touches are the ones its own `git status` named.

Two counts moved as the cost of adding guards, not as prose: the pytest pair **545 → 547** with the
oracles and **476 → 478** collected without, cascaded through 17 named quotations in five files
(`docs/interview_defense.md`, `docs/limitations.md`, `docs/reproducibility.md`,
`paper/technical_report.tex` and four *plant anchors* that quote those documents, which is V2-10's
re-keying rule applied to a documentation edit), then the report rebuilt and both freshness guards re-run.
Red first was observed: the structural guard failed with `the member list still stores its own ['artifact',
'kind', 'script']` before the runner changed.

### 2026-10-22, P3.3 absorption 1 of 19 — `stress_testing`

`git mv` of the 620-line study into `python/quantrisk/experiments/stress_testing/__init__.py`, with a
`__main__.py` of three lines. Red first was observed twice: the new absorbed-task guard failed with
`cannot import name 'checkout_root'`, and the parity walk could not see the moved file until it was
staged. `git diff --stat -M` reports a rename, not a rewrite, which is the only form of that claim
worth having.

The entry point split into `run(argv) -> dict` and `main(argv) -> int` with no behaviour added between
them: the payload's keys are the artifact's keys, and the print statements moved to the shim. Output
resolution went from `Path(__file__).parent / "results"` to `results_directory(TASK, --out or the
checkout)`, and the refusal was exercised: from `/tmp`, `python -m quantrisk.experiments.stress_testing`
exits with `RuntimeError: /private/tmp is not inside a QuantRisk++ checkout: no ancestor holds
pyproject.toml and .git; refusing to guess at a root`. The replay into a temporary root wrote
`build/stress-replay/experiments/stress_testing/results/` — the published layout under whatever root it
is handed — and every artifact's **content digest matched the committed one**: the three CSVs and the
JSON agree on content (the JSON's bytes differ only in the volatile timestamp/command fields), and the
PNG is byte-identical. That is the move proved as behaviour, not as a file operation; the frozen
artifacts stay frozen until P3.5's single re-run, as D5 requires.

Three things the recipe had listed arrived as larger than they sounded:

* **The two sibling edges.** `restrike_gamma_map` and `two_factor_error_bound` loaded the study by
  repository path; both now import it, and the import stays *inside* `published_scenario()` because
  the stress module needs matplotlib for its figure and the two bound studies must not need it to be
  read. The "load the definition, do not copy it" property survives, and the depth-derived
  `REPO_ROOT = parents[2]` in both files died with the loader that was its only user. The by-path load
  census moved **17 → 14** in one commit: the two study loaders plus the guard in
  `test_two_factor_bound.py:494`, which now imports the package the way the experiment does.
* **V2-20's citation.** The three `"<path>:<symbol>"` provenance strings became
  `stress_testing:<symbol>`. Reading the finding again at the collision, its evidence was wrong about
  half the blast radius: the two test lines it cited are fake-checkout file sets, not assertions, and
  what the change actually lands on is `_assert_same_result` — the shared replay guard compares
  `.source` leaf by leaf, so two of the six replica tests went red on the first move. §6 is corrected
  in place and disclosed here rather than papered over. The guard now normalises a citation to its
  registry reference *prefix only*; that narrowing was shown to be narrow by misspelling the symbol in
  the study, which still fails the replay with
  `as registry references 'stress_testing:run_linearisation' != 'stress_testing:run_linearisatn'`, and
  the probe was undone from a snapshot with the SHA-256 compared afterwards.
* **Two guards that knew only the old layout.** `test_the_readme_experiment_count_agrees_with_the_experiments_on_disk`
  counted `experiments/*/run.py` and read the move as a lost experiment (14 rows against 13 files);
  it now counts study directories in whichever layout each sits, as the disk-to-member guard already
  does after P3.3a. Both are permanent fixes — without them, each of the 18 remaining moves would have
  needed the same rescue.

`checkout_root()` went to a new leaf module, `python/quantrisk/checkout.py`, rather than becoming a
second marker walk beside the harness's: the instruments start from their own file, a study starts from
the working tree, and one list of markers now answers both. `quantrisk.verification.repo_root` is gone,
its two callers repointed; no plant anchored on it and no test imported it.

Numbers the culture demands: the pytest pair **547 → 548** with the oracles and **478 → 479** offline,
cascaded through 17 named quotations in five files including four plant anchors, with the census gold
lists re-keyed beside them and the report rebuilt; mypy's checked corpus **28 → 31** files with its
two-sided agreement intact, and ruff still admitting every tracked Python file. The ceilings gate
stays exit 1 by design, with `by_path_load_sites` now named at 14 rather than 17.

### 2026-10-22, P3.3 absorption 2 of 19 — `restrike_gamma_map`

Moved, split, and re-imported, with three discoveries that were not in the recipe.

The move itself followed §11: `git mv` into `python/quantrisk/experiments/restrike_gamma_map/__init__.py`
plus a three-line `__main__.py`, `run(argv) -> dict` and `main(argv) -> int`, the recorded command now
`TASK.invocation`, and the replay compared by content digest. The two sibling edges it owns --
`fourth_order_crossing_map` and `second_book_crossing_map` both load it at module scope -- became
package imports, while restrike's own import of `stress_testing` stayed inside `published_scenario()`
because that study needs matplotlib for its figure and this one must not need it to be read. The test
that had been loading restrike by path at module scope now imports it, and its replay runs the canonical
`-m … --out tmp_path` instead of copying the file into a fake tree -- the temporary root turned out to
make the whole fake-checkout apparatus unnecessary, which is worth knowing before the remaining twelve.

**Discovery 1: the registry now owns the artifact's filename, not only its directory.** A study writing
`results / "restrike_gamma_map.json"` next to a registry entry naming that file is two declarations that
nothing compares. `artifact_path(task, out)` returns the registry's path and the study writes there, so
the disagreement is impossible rather than policed; `parse_out(argv)` became the shared reader of the
one flag every study accepts, and `stress_testing` was back-ported to both in the same commit so no
second spelling of either survives.

**Discovery 2: V2-20's citations are prose as often as they are fields.** The finding names the
`"source"` strings; `second_book_crossing_map` carries the same citation inside
`procedure.shared_with`, a sentence. A normalisation keyed on the field name `source` would have covered
one artifact and missed the other -- the partial-re-derivation trap, where an exemption list licenses
everything outside it. So `_assert_same_result` now maps a *runnable unit's file path* to its registry id
on every string leaf, in either layout and with or without the `experiments/` prefix, and the same helper
waives the values of `VOLATILE_KEYS` (whose presence it still asserts) because D4-prime makes every
absorbed study re-record its command. The hatch was shown narrow twice over on the committed tree, each
probe undone from a snapshot and the restore verified by SHA-256: citing the wrong task still fails the
replay (`as registry references 'stress_testing:run_linearisation' != 'fourth_order_crossing_map:…'`),
and so does changing two words in an unrelated sentence -- the normalizer touches path forms and nothing
else.

**Discovery 3: the collector mis-read a red type check, and the newly-covered module had two real
defects in it.** mypy's corpus is `python/quantrisk`, so a study only becomes type-checked when it moves
in; this one arrived carrying `found = {"equity": None, …}` inferred as `dict[str, None]` and a
signed-bias field guarded on `zero_distance is None` while subtracting two values that are `float | None`.
Both are annotation/narrowing fixes with no numerical change -- the replay proves it -- and they are the
same class as the pairing-audit defect P3.2's move surfaced. Reading them out of mypy exposed the
instrument's own bug: `mypy_reported_count` scanned for the first `in <n>`, so a failing run printing
`Found 5 errors in 1 file (checked 33 source files)` reported a *one-file* corpus and set
`mypy_two_sided_agreement` false for the wrong reason. It now reads the `(checked N source files)` tail or
the success line's `found in N source files`, carries `mypy_exit_code` beside the count, and requires
exit 0 for agreement. Both branches were exercised: green reads 33 against an enumerated 33 with
agreement true, and a planted type error reads 33 with `mypy_exit_code: 1` and agreement false -- the
failure is now named as a failure rather than as a suspicious number.

Readings and re-derivations: the by-path load census **14 → 12** (two loaders), mypy's checked corpus
**31 → 33**, `registry_parity` 19 against 19, one plant re-keyed with the file it mutates
(`producer-docstring-quotes-a-stale-restdike-share`, whose anchor text moved verbatim with the docstring).
The pytest pair stays **548 / 479** -- this commit added no test, it re-pointed six. Documents re-derived:
the report's `\src{}` for the study, its reproduction line in `docs/analysis/restrike_gamma_map.md`, and
the rehearsal sheet's source list; the PDF rebuilt and both freshness guards re-run.

### 2026-10-22, P3.3 absorption 3 of 19 — `fourth_order_crossing_map`

Third move, and the first that took a `sys.path` bootstrap with it: `fourth_order_crossing_map` was one
of the four studies that pinned their root at `parents[2]` and inserted `<root>/python` so they could
import the package. Inside the package both are dead -- the census drops to **bootstrap 9, by-path 10**
-- and `REPO_ROOT` went with them, its last uses being the results directory and a `relative_to` print
that `repo_relative` already does honestly.

The entry point split like the others, with one wrinkle worth recording: this study's console report is
three narrative lines built from locals (`fits`, `headline`, `published`, the disagreement lists), so
moving them to `main()` meant reading them back out of the payload instead of out of scope. The values
are the same objects the artifact carries -- `headline["fits"]`,
`headline["columns_where_the_cubic_zero_count_disagrees"]`, `payload["published_scenario"]` -- and the
replayed console text matches the published one, so the print moved without inventing a second source.
The digest check then found exactly one non-volatile difference: `.book.source`, the V2-20 citation this
lane re-expresses. Nothing else moved.

`second_book_crossing_map` imports it now, which was that study's last by-path sibling load: its `_load`
helper is deleted rather than left unused, because a dead loader in a published study is the kind of
code that gets copied forward. Its own absorption is next-but-three, and it keeps its own root pinning
until then.

Newly type-checked code produced one more real defect, fixed by annotation rather than by exemption: a
`lambda o, field=name: …` inside a dict comprehension that mypy cannot infer, replaced by a small
`mixed_field(field)` factory that binds the name by argument -- same closure semantics, one less trick.
`mypy_two_sided_agreement` stayed true across it: 35 reported against 35 enumerated.

`test_fourth_order_crossing_map` was the last test in the chain loading its study by path at module
scope; it imports now, and its replay runs `-m … --out tmp_path` like restrike's, so no file is copied
and the fake-tree list for this study is gone. The `second_book` and `fifth_order` fixtures each dropped
one entry from their travelling sets -- 2 files, then 1 -- which is the chain dissolving as intended.
Documents re-derived: the analysis note's reproduction command, the rehearsal sheet's source line, and
one plant re-keyed with the file it mutates. No test was added; the published pair stays **548 / 479**.

### 2026-10-22, P3.3 absorption 4 of 19 — `second_book_crossing_map`

Fourth move. This was the study the chain hangs on: it owns the books, the grid, the tolerance and the
radius rule that v1.9.0's two later studies import, so taking it into the package removes a by-path load
from *each* of them rather than one. Census after this commit: **bootstrap 8** (its `sys.path` insert died
with the move) and **by-path 10 → 8** -- its own loader helper and `fifth_order`'s `_load`, both deleted
rather than left unused, because a dead by-path loader in a published study gets copied forward.

The entry point split like the others, and its console report was already payload-derived, so the shim
took the five per-book lines and the summary line unchanged. One non-volatile difference in the replay,
`.procedure.shared_with`, is the V2-20 citation the P3.5 re-run replaces; the CSV is content-identical.
The print line at the end moved from `json_path.relative_to(REPO_ROOT)` to `repo_relative`, which is the
same claim made by the helper that already knows how to say it.

Two of the six plants in this lane's cross-study set sit on this file
(`radius-reads-one-signed-column-at-a-time`, `sixth-book-grid-bound-claim-reads-a-narrower-grid`) and
were re-keyed with it; both anchors were confirmed present in the moved file before the sweep is re-run
against them.

`fifth_order` and `sixth_book` cite it in artifact prose, not only in `source` fields -- `books`,
`machinery_equality_with_v150_and_v160`, `reused_from` -- which is the second confirmation that a
citation normaliser keyed on a field name would have covered one artifact and silently missed three.
`test_fifth_order_crossing_map:331` asserts the sentence *inside the committed artifact*, so it was
re-pointed through the same `_sibling_reference` the replay uses rather than at a literal spelling: it
must be true against the artifact on disk today and against the one P3.5 writes, without being edited
twice.

Newly type-checked code produced the same defect as its neighbour's: a `lambda o, field=name: …` default
argument carrying a comprehension variable, which mypy cannot infer. Replaced by a `_mixed_field` static
method on the book class that binds the name by parameter -- the comment in the module says plainly why
the trick was dropped. `mypy_two_sided_agreement` held at 37 reported against 37 enumerated.

Documents re-derived: the analysis note's reproduction command, its sixth-book neighbour's prose citation,
two `docs/validation_matrix.md` rows, and the rehearsal sheet's source cell; dated records
(`docs/phase_reports/*`, `docs/integrity_audit.md`) keep the path they were written against, per §11's
rule that a record states the revision it describes. No test added, so the published pair stays
**548 / 479**.

### 2026-10-22, P3.3 absorption 5 of 19 — `fifth_order_crossing_map`

Fifth move, and the last one inside the radius chain: `sixth_book_crossing_map` imports it, so its
`_load` helper went too, which is why the census drops further than one move would suggest --
**bootstrap 8 → 7, by-path 8 → 6**. `fifth_order` also borrows its library namespace from its sibling
(`quantrisk = P18.quantrisk`), a shape that survives this commit untouched: it is not a path problem, and
retyping it here would mix a stylistic change into a move.

The replay's console line -- the claim sentence -- matches what row 22 of the validation matrix publishes
("2 of 5 books, published ladder 0.15 → 0.20, a factor of 1.33, 2 books at the swept grid edge"), and
the six CSVs it writes are content-identical to the committed ones. The JSON carries exactly the two
declared differences from absorption #4's citations (`procedure.books`,
`controls.machinery_equality_with_v150_and_v160`), both waiting on P3.5's re-run, and nothing else.

The entry point split took the one print statement with it rather than leaving it in the computation:
`run(argv)` now returns the payload and `main(argv)` prints the claim, so importing the module for its
numbers stays silent -- which matters because `sixth_book` imports it. mypy found nothing new this time
(39 source files, two-sided agreement holding), and the two plants on this file
(`fifth-order-radius-judged-by-another-orders-range`, `fifth-order-sums-drop-the-book-quantity`) were
re-keyed with anchors confirmed present in the moved file.

One test changed in kind rather than in spelling: `test_fifth_order_crossing_map` asserted the artifact's
recorded command against a literal path. `command` is volatile by declaration, and Phase 3.3 changes it
for every study it absorbs, so the assertion is now an explicit set of the two spellings that both name
this task -- the one the frozen artifact carries today and the registry invocation the code writes --
with the legacy alternative commented for deletion at P3.5. That keeps the guard honest across the re-run
instead of pinning a string that the lane has already decided must move.

Documents re-derived: the analysis note's prose citation and its reproduction command. No test added; the
pair stays **548 / 479**.

### 2026-10-22, P3.3 absorption 6 of 19 — `sixth_book_crossing_map`

Sixth move and the chain's tail: nothing imports it, so this one is a move plus an entry-point split,
with **bootstrap 7 → 6** (its own `sys.path` insert died with it) and **by-path 6 → 5** (its test's
`_load`, deleted rather than left unused). mypy added it to its corpus clean -- 41 source files, nothing
new to fix -- which is the first absorption where the newly-covered module produced no defect.

Two things this file does that the previous five did not, and both needed stating rather than working
around. Its control reads a *published input*: the five prior books' radii come back from
`experiments/fifth_order_crossing_map/results/...json` bit for bit. That read is now
`checkout_root() / CONTROL_TASK.artifact` -- `--out` moves outputs, never the evidence a control is
compared against -- and the `published_artifact` field the payload records is the registry's own
relative string, so it stayed byte-identical while the path constant that produced it disappeared. Its
other quirk is that `main` printed a banner *before* computing and a "wrote" line after, so the split put
the banner and the five narrative lines in the shim with `run(argv)` doing the work -- the order of the
printed lines is unchanged, which is what the frozen `suite_summary.md` and the rehearsal sheet quote.

The replay found a defect I had written into the split: the closing print used
`landed.relative_to(checkout_root())`, which raises when `--out` is a *relative* path -- exactly what I
passed. `repo_relative` is the helper that already handles both spellings, and §11 step 4 now says so,
because the remaining thirteen will each print a line and each may be handed a relative root. The failure
was a nonzero exit on the replay, caught before the gate suite ran, not a red lane afterwards.

Documents re-derived: the analysis note's reproduction command and the citation inside limitation #88,
which names this study as the thing that cannot tell in advance whether its verdict is grid-bounded -- a
register entry states current behaviour, so it follows the file it points at, and the register's count is
unchanged. The same grep turned up two rows of `docs/validation_matrix.md` that still named a `run.py`,
one for this study and one for `restrike_gamma_map` -- the latter is absorption 2's miss, and it sat for
four commits because step 9 looked for command lines while the matrix names the study in prose. Both rows
now cite the module. No test added; the pair stays **548 / 479**. The replay's only non-volatile
differences are the three declared citation spellings (`controls.control`, two `procedure.reused_from`
entries), each waiting on P3.5.

### 2026-10-22, P3.3 absorption 7 of 19 — `two_factor_error_bound`, and the report's citations have no owner

Seventh of 19, and the first move that changes nothing in the two counters the lane has been watching:
bootstrap stays 6, by-path load sites stay 5, because absorption 1 converted this study's sibling loader
and its `sys.path` insert four commits ago. What did move is the checked corpus -- mypy 41 to 43 source
files, ruff's tracked-python denominator 98 to 99 -- and the report, for a reason that is its own finding.

Finding first. `paper/technical_report.tex` carries 315 `\src{}` / `\srcin{}` path citations and nothing
proves any of them resolves. Six named files that do not exist at this commit's parent: four still pointed
at `run.py` for the studies absorbed in commits 3 to 6, this study's own line 1401 pointed here, and line
1530 cited `scripts/derive\_fifth\_order\_partials.py` -- moved into `python/quantrisk/verification/` by
P3.2 five commits back, which means the lane that widened step 9 today had itself made the hole earlier.
The escaped spelling is a second axis of blindness in a probe that had just been widened for a first one:
the tex writes `fourth\_order\_crossing\_map`, so a pattern containing an underscore does not match it.
Step 9 now says to run the probe twice, and the missing owner is registered as **V2-21** with its fix and
its cost named (one loop-guard over the tex, and the fifteen-quotation cascade any added pytest case pays).
All six are re-derived in this commit and the same pass resolves 315 of 315 afterwards. The PDF is rebuilt
after the last of them, not before: the first build of this commit recorded bundle `74d9ca04aa4c` / pdf
`bcc58f914e82` and is superseded; the pair the tree ships is bundle `913dd5752889`, pdf `0e93bd19a0ab`.

The re-derivation is what a guard was for, and the second one it exposed is worse than the citations. The
plant `report-drops-an-experiment-from-its-own-account` anchors the tex citation, so its anchor going stale
was the lane's own signal that `test_every_registered_experiment_is_named_in_the_report` had stopped
covering what its name says: its denominator was built from `member.script` filtered by
`startswith("experiments/")`, and P3.3a had made `member.script` the registry's path -- so every absorbed
task moved
out of the filter, and by this commit the guard checked **7 of the 14** studies under `experiments/` while
passing every run and keeping its plant green. Registered as **V2-22**, because a gate that loses half its
population without a `skip` in sight is the L3 failure this lane is not allowed to have caused; the
denominator now comes from `Task.artifact` parts with no trailing slash, so all three spellings the report
uses name the study. The re-keyed plant was proved to fire rather than assumed: citation removed in-tree,
guard rc 1; file restored, SHA-256 `b70cca9ac01e` equal to the snapshot, guard rc 0. The sweep's own
`--only` for that plant refused to run against a staged tree (`target-already-modified`, rc 2), which is
the harness's precondition working as designed, not a defect -- and the full sweep at the end of P3.3 is
where the re-keyed anchor gets its verdict. The two other prefix classifiers,
`tests/python/test_task_registry_parity.py:35` and `tools/inventory_orphan_code.py:332`, were read and are
layout-safe; that is how `filesystem_units` reaches 19 with 7 units already inside the package.

`figure_status` is new to the lane. This is the first absorbed study that draws a PNG and records where it
landed *inside* the payload, so a replay under `--out` moves a field that `VOLATILE_KEYS` does not name --
which is why the digests differ and why the reproduction guard waives the key by name, a waiver that
predates the move because the tmp-tree copy hit the same thing for the same reason. It is deliberately not
promoted into `VOLATILE_KEYS`: that set decides what `content_digest` certifies for all 95 artifacts, and
widening it is a policy change with a declared reason, belonging to P3.5's ceilings entry, not to a commit
whose only mandate is to move a file.

Two defects surfaced in the newly-covered code, both in `published_scenario()`, and both of the same shape
the lane has now seen four times: `found = {"equity": None, "volatility": None}` infers `dict[str, None]`,
so the assignments at the loop body are rejected, and the guard that proves both legs were found narrows
nothing when it reads through the dict subscript. The fix types the dict and reads the two values into
locals before the check, which is what makes the `return` well-typed; the behaviour is the same bytes, and
the replay plus the study's own 20 guards say so.

The three prose citations this study owned inside `restrike_gamma_map` became registry references --
`two_factor_error_bound:terms_at_base` and `:engine_map`, both confirmed to exist as module-level functions
at lines 253 and 201 -- except the book comment, which now names the `linearisation_error_bound` and
`two_factor_error_bound` studies *without* a symbol, because that one has no `run` function to cite and a
reference that does not resolve is the thing this whole lane is trying to remove.

Absent at HEAD, proved by running it: `python -m quantrisk.experiments.two_factor_error_bound --out build/probe`
exits 1 with `No module named quantrisk.experiments.two_factor_error_bound`. After the move the same
invocation exits 0, and its artifact differs from the committed one in exactly three classes: the two
provenance citations absorption 1 re-expressed (`book.source`, `published_scenario_bound.source`), the
`command` field every absorption rewrites, and `figure_status` naming the temporary root. The analysis
note's reproduction command and the `reproducibility.md` sentence about the conditioning band are
re-derived; no plant targets this file's source (`grep -c` of the path in `plants.py` is 0 before and
after); no test added, so the pair stays **548 / 479**.

### 2026-10-22, P3.3 absorption 8 of 19 — `pricing_grid`, whose module is not named `pricing_grid`

Eighth of 19 and the first from the Phase-2 generation, and it taught the lane something the radius chain
could not: a task id and a directory are different names. `pricing_grid` lives in
`experiments/pricing_validation/`, and `_study` composes the module from the *directory* -- "named by its
directory in both layouts the lane moves between", its own docstring says -- so the destination is
`quantrisk.experiments.pricing_validation`. A package directory named after the task id instead was refused
by the registry itself, on the replay's first run: `ValueError: pricing_grid claims to be absorbed but
quantrisk.experiments.pricing_validation does not resolve`. That is L5's parity check acting as a
precondition rather than a post-hoc test, and it is why the three documents re-derived here say
`-m quantrisk.experiments.pricing_validation` while the suite still calls the member `pricing_grid`. The
same trap is live for `mc_convergence` (monte_carlo_convergence) and `portfolio_estimation_cost`
(portfolio_optimization).

Neither ceiling counter moved: bootstrap stays 6 and by-path load sites stay 5, because this study loads no
sibling and inserts no path. What died instead was an orphan of the V2-01 class -- `REPO_ROOT = parents[2]`,
declared and never read -- and an `import sys` whose only consumer was the command string,
`f"uv run python {' '.join(Path(sys.argv[0]).parts[-2:])}"`. Under `-m` that interpolation yields
`pricing_validation/__main__.py`, which is a file, not an invocation, and was never a command a reader could
type; D4' replaces it with `TASK.invocation`, and the study's self-reference `"artifact"` with `TASK.module`.
That self-reference is a new kind of declared movement: `artifact` is not in `VOLATILE_KEYS`, so P3.5's single
re-run changes this artifact's *content* digest for a reason that must be enumerated -- the first artifact
whose pointer to its own producer moves, not merely its timestamp.

mypy found 14 defects in the newly-covered file, 13 of one shape and 1 of another. The thirteen are
`float(row["steps"])` and its neighbours read out of rows typed `dict[str, object]`; the convention elsewhere
in the package is `dict[str, Any]`, so the row annotations were widened -- annotations only, with identical
CSV and PNG digests on both sides of the replay as the proof. The fourteenth is the one worth reading:
`slopes: dict[str, dict[str, float]]` while its field `deviations_in_standard_errors` is
`abs(...) / fit[1] if ... else None`. The annotation was false rather than merely loose, and false in the
direction that hides a null from every later reader; the slope map is now `dict[str, float | None]`.

Two smaller things this file needed that the previous seven did not. `build_figures` derived its output
directory from the module's own location, so it takes `results` as a parameter now -- the one signature
change, and the only way the destination stops being a function of `__file__`. And its closing print was
`print(f"wrote {json_path}")`: an absolute machine path on stdout where every other study prints
`repo_relative`. §11 step 4's lesson from absorption 6 was applied before the replay this time rather than
caught by it.

Documents re-derived: the interview-defense command block, the CRR model card's Level-3 citation, and the
report's reproduction command -- with the PDF rebuilt after all three, bundle `557da79a185e`, pdf
`f3d11c3cef61`. No plant targets this file (`grep -c pricing_validation` in `plants.py` is 0 before and
after), and no test was added, so the pair stays **548 / 479**. The replay's only volatile-free difference is
the `.artifact` self-reference above; everything else it reports lives under `artifacts`, `environment` or
`command`, each volatile by declaration.

### 2026-10-22, P3.3 absorption 9 of 19 — `mc_convergence`, and the citation shape that cannot survive a move

Ninth of 19. Last commit's rule was applied before the move this time, so the package directory was created
as `monte_carlo_convergence` -- the name the registry composes the module from -- and the absent-at-HEAD
probe ran first as written: `-m quantrisk.experiments.monte_carlo_convergence` exits 1 with `No module
named`, then exits 0 after the move. Bootstrap stays 6 and by-path load sites stay 5 again: this study takes
no sibling path and inserts none. Its dead `REPO_ROOT = parents[2]` is the second one deleted, and its
`import sys` existed only to build `"command": f"uv run python {Path(sys.argv[0]).name}"` -- under `-m` that
interpolation yields `__main__.py`, so the recorded command would have become one that names no file at all.
D4' replaces it with `TASK.invocation`.

mypy found 5 defects, all the class the lane now recognises at once: `float(row["paths"])` read out of rows
annotated `dict[str, object]`. Eight annotations widened to `dict[str, Any]`, no behaviour touched. Unlike
absorption 8 there was no lying annotation here -- this file's slope map really does hold only floats, and
mypy's silence on it is the evidence, not an assumption.

The one thing worth recording is a defect the split introduced and review caught before any run. The old
`main` printed `{"slopes": slopes, ...}` from a *local*, while the payload stores that same dict under
`convergence_slope_fit`; a first cut of the shim printed `summary["slopes"]`, which is a KeyError waiting on
the CLI path the study's guards never exercise -- no test loads this file, and no plant targets it (`grep`
of the path in `tests/` and `plants.py` both return 0), because the Monte Carlo claims are all checked
against the artifact. The shim now reads `summary["convergence_slope_fit"]` and prints it under the key the
banner always used, so stdout is unchanged. A split that moves a print across a function boundary has to
re-find every value that print read from a local, and this is the case where the local was never in the
returned payload under the name the print wanted.

Two documents carried the most fragile citation shape in the repository:
`experiments/monte_carlo_convergence/run.py:60-78` and `run.py:93-95` in the interview defense. A line range
names a file *and* an offset, and a move changes both, with nothing to guard it -- confirmed by grepping the
plant list and the census for those ranges, which is V2-21's hole in a second form. Both are now registry
references to the symbols the ranges enclosed, `monte_carlo_convergence:fit_log_log_slope` and
`monte_carlo_convergence:convergence_rows`, each read in the moved file before being cited. Commands
re-derived in the interview defense and the report; the PDF rebuilt after them, bundle `6bfad07e6505`, pdf
`0b6802d8aced`.

The replay is the lane's strongest determinism evidence so far: this study is seeded at 42, and every fitted
slope, z-score and coverage cell is bit-identical to the committed artifact -- a single volatile-free
difference, the `.artifact` self-reference P3.5 will re-derive. mypy's corpus is 47 source files with the
two-sided agreement holding; no test added, so the pair stays **548 / 479**.

### 2026-10-22, P3.3 absorption 10 of 19 — `variance_reduction`, and a statement written twice

Tenth of 19. Id and directory agree here, so the move is the plain shape, and the ceilings counters stay
where they were (bootstrap 6, by-path 5) -- this study takes no sibling. mypy added it to its corpus, 47 to
49 source files, and found the four familiar `float(row[...])` / `int(row[...])` defects against
`dict[str, object]` rows.

Whether an annotation change is load-bearing was measured rather than assumed: the widening was reverted and
mypy re-run, which produced 4 errors, then restored, which produced none. So four annotations moved because
a check demanded them, not because the file looked inconsistent next to its neighbours -- and the diff says
so.

The finding this file carries is older than the lane. Two adjacent lines read
`worst_reduction = min(reductions.values())` twice. Nothing notices that: ruff has no duplicate-statement
rule, mypy never saw the file until this commit put it in its corpus, and the 548 tests all read the
artifact, where the second assignment produces exactly what the first did. It survived eight phases and six
releases. Removed as part of the split, and the proof it changed nothing is the byte-identical
`realised_error.csv` on both sides.

The replay is the lane's clearest illustration of what "volatile" means in this repository. The JSON differs
from the committed artifact in one volatile-free field -- the `.artifact` self-reference, third of its kind.
The `variance_by_method.csv` differs in bytes, but cell by cell it is only `mean_runtime_seconds` and
`seconds_per_path`, 36 rows of each, while every statistical column matches exactly: variance
11.1237619281, standard error 3.412623e+02, and the rest, identical to the published run. Those two columns
are the wall-clock family `content_digest` already treats as volatile, and the guard
`test_content_digest_treats_wall_clock_csv_columns_as_volatile` is what licenses reading a timing table that
disagrees as the same evidence. `realised_error.csv`, which carries no clock, is byte-identical.

Documents re-derived: the interview-defense reproduction command and, in the same document, the citation
`experiments/variance_reduction/run.py:108-123` -- the second line-range citation, absorbed into
`variance_reduction:run`, the function that now encloses the block it pointed at. The report's command line
moved too; the PDF was rebuilt after both, bundle `4d5b082be827`, pdf `1382159ce6dc`. No plant mentions this
study at all (`grep -c variance_reduction` in `plants.py` is 0), so step 8 had nothing to re-key here, and
the falsification coverage of this study is the artifact's own guards rather than a planted edit. No test
added, so the pair stays **548 / 479**.

### 2026-10-22, P3.3 absorption 11 of 19 — `var_backtesting`, and an instrument disagreement about what "content" is

Eleventh of 19. Id and directory agree, the probe ran first (`-m quantrisk.experiments.var_backtesting`
exits 1 with `No module named`), and the counters stay at bootstrap 6 / by-path 5: this study takes no
sibling path. It is, though, one of the three places the report says optional-oracle imports actually live --
and that sentence, `\srcin{experiments/var_backtesting/run.py}` in the limitations paragraph, was itself a
stale citation of exactly the kind V2-21 registered. Re-derived with the reproduction command two thousand
lines later, along with the VaR/ES model card and the docstring of `tests/python/test_risk_measures.py`,
which names this study as where its quality claims are measured. The PDF was rebuilt after all four: bundle
`8aad76b3d940`, pdf `ccaf730f69ce`.

mypy found 4 defects of a new shape for the lane. `ARMS = {...}` at line 266 mixes a string (`"kind"`) with
floats, so it infers `dict[str, dict[str, object]]` -- and that `object` does not merely sit in a dict: it
flows into `rng.random(BACKTEST_LENGTH) < spec["rate"]`, where numpy has no `__lt__` overload for `object`,
and into two positional `float` parameters of `markov_flags`. The fix is one annotation at the declaration
rather than four casts at the uses, and it is the honest one: the values *are* floats, the inference was the
accident. Two helpers gained a `results` parameter for the same reason `build_figures` did in absorption 8 --
their output paths were derived from `__file__`.

One print needed thought rather than a mechanical split. The old banner read `wrote {len(artifacts)}
artifacts to {repo_relative(RESULTS)}`, and `artifacts` is a local the returned payload does not carry under
that name. Dropping the count would have changed what a reader sees, so the shim reads
`len(summary["artifacts"])` -- the manifest the run just wrote -- and the replay's stdout confirms the line
still says "wrote 5 artifacts to …".

The replay is the lane's cleanest: all three CSVs are **byte-identical** to the committed evidence, and the
JSON has one volatile-free difference, which this commit did not cause. `oracle.versions.quantrisk` says
1.8.0 in the frozen artifact and 1.9.0 in the replay, because this study records the package version
*outside* `environment`, under a container `VOLATILE_KEYS` does not name. `content_digest` therefore treats
release metadata as content while the replay guards waive `oracles` by name in their own comparison lists --
two instruments in this repository disagreeing about what an artifact's content is, and the disagreement is
the finding. Registered as **V2-23** with the population measured (four artifacts, two container spellings,
three still reading 1.8.0) and the decision -- widen the set, or move the field inside `environment` --
deferred to P3.5 with the other declared movements, because neither is a call a move-only commit should make.

mypy's corpus went 49 to 51 source files with the two-sided agreement holding; ruff admits every tracked
file; no plant mentions this study at all (`grep -c var_backtesting` in `plants.py` is 0), so step 8 had
nothing to re-key and the coverage here is the artifact's own guards. No test added, so the pair stays
**548 / 479**.

One ceiling counter moved the wrong way, and the reason is measured rather than assumed:
`commands_unrunnable_from_the_root` went 71 to 77. The census reads one recorded command per **manifest
artifact**, not per study -- the corpus is 95 entries because `evidence/manifest.json` lists 95 files -- so a
move re-classifies one entry per artifact that study publishes. `var_backtesting` publishes six (three CSVs,
two PNGs, the JSON), all carrying the same string, which is why six flipped at once where earlier moves
flipped one to nine each: `fifth_order` 9, `stress_testing` 5, `restrike` 4, `two_factor` 4, `fourth_order`
3, `second_book` 2, `sixth_book` 1, all now `bare-filename-does-not-exist-from-root`. Same declared
staleness as `commands_not_module_path` (flat at 95, because none of these were ever module paths), and it
clears with the single re-run at P3.5.

The three Phase-2/3 studies absorbed at 8, 9 and 10 flip nothing in this counter, and the reason is its own
defect: their recorded commands were *synthesised* at write time as `uv run python run.py` -- the bare
`Path(sys.argv[0]).name`, never a path that resolved from the root -- so they sat in the does-not-exist
bucket before this lane touched them and stayed there. D4' replaces all three with `TASK.invocation`, which
P3.5's re-run will turn into runnable strings; until then the artifacts say a command that no reader could
have typed, and that is a fact about the frozen evidence rather than about the move.

### 2026-10-22, P3.3 absorption 12 of 19 — `portfolio_estimation_cost`, and a replay with nothing to declare

Twelfth of 19. Task id `portfolio_estimation_cost`, directory `portfolio_optimization`, so the module is
`quantrisk.experiments.portfolio_optimization` and the registry's `validate_task` is what makes an
id-named package unshippable: the probe confirmed the absence first (`-m
quantrisk.experiments.portfolio_optimization` exits 1), and after the move it exits 0.

This is the lane's cleanest reproduction -- **zero volatile-free differences** in the JSON, and every artifact
the study publishes, three CSVs and the PNG, byte-identical to the committed evidence. It records no
self-path in its payload, so unlike 8, 9, 10 and 11 there is no `.artifact` movement to declare, while
`commands_unrunnable_from_the_root` moves 77 to 82: five more manifest entries name the file that just moved,
which is this study's artifact count rather than a coincidence, and `commands_not_module_path` stays at 95
because none of them were ever module paths.

mypy found 1 defect, in a loop the type checker had never read. `row` names the dict being built in the first
pass and is then reused for `index.get(...)`, which is `dict | None`, so mypy rejects the assignment because
the variable was already bound to a bare dict. The None *was* guarded -- `if row is None: continue` sits on
the next line -- so nothing was wrong at run time, but the shadowing made a correct guard read like a bug,
and the fix is the rename: the looked-up row is `target`, and the two roles no longer share a name.

The shim needed the container hunt absorption 9 only hinted at. The old `main` printed two blocks from
locals, `by_cell` and `objective_summary`; both are in the payload, but under parents that are not their own
names -- `estimation_cost.by_window_and_estimator` and `objective_comparison.by_objective`. Those paths were
found by walking the committed artifact rather than guessed from the code, and the replay's stdout carries
the same two blocks, so the banner is unchanged.

One mechanical fix worth saying rather than hiding: this file's import block lists `quantrisk` alongside the
third parties, so inserting `from quantrisk.experiments.registry import ...` produced a third block and
`ruff check --fix` folded it back. The insertion was mine, so the disclosure is too.

Documents re-derived: the portfolio model card's reproduction command, its comment column kept aligned, and
the report's; the PDF rebuilt after both, bundle `b1f55b9a149b`, pdf `bd266889182f`. No plant mentions this
study (`grep -c` of either name in `plants.py` is 0), so nothing was re-keyed. mypy's corpus is 51 to 53
source files with the two-sided agreement holding, and no test was added, so the pair stays **548 / 479**.

### 2026-10-22, P3.3 absorption 13 of 19 — `linearisation_error_bound`, and a frozen assertion that had to learn both spellings

Thirteenth of 19, and the first absorption whose *test* had to change in kind rather than spelling.
`tests/python/test_linearisation_bound.py:343` asserted the artifact's recorded command with `==` against
the literal pre-refactor string -- the one command assertion in the suite written as an equality rather than
a membership, and it had been invisible to absorptions 1 to 12 because no study it guards had moved since
Phase 12. Pinning the old string would have failed the moment the artifact was honestly regenerated; pinning
only the new one fails today, because K2 keeps the frozen bytes until P3.5's single re-run. The assertion now
names both spellings and says why, the same shape `test_fifth_order_crossing_map.py:340` has carried since
absorption 5, and it reads the new one from the registry rather than retyping it.

Eight mypy defects, and they are the lane's first lesson in *type* rather than annotation arithmetic. Six of
them were one variable name carrying two roles: `direction` is a str in four dict comprehensions (the sweep's
`"down"`/`"up"`) and then a float in the dense-grid loop at line 392, so mypy reported `str * float`, `str >
int` and an assignment of float to str from one collision; `values` was a dict in the fit loop and a list in
the correction loop. Both were correct at run time -- each loop rebound the name before using it -- and both
were unreadable, so the fixes are renames (`polarity`, `corrections`) rather than casts. The seventh is
`dense_grid` returning `list[float]` while `np.geomspace` yields `np.float64`: the elements are now
explicitly `float(size)`, and the replay's PNG is byte-identical (`78c28e042a52` on both sides), which is the
proof that converting the container changed no number. The eighth is the fit dict that mixes a `list`
(`window`) with floats, annotated at the declaration.

The replay's single volatile-free difference is `.oracles.versions.quantrisk`, 1.8.0 against 1.9.0 -- the
V2-23 finding arriving exactly as registered, in one of the four artifacts it named, and not caused by
anything this commit changed in the study's arithmetic. `linearisation_bound.csv` and the figure are
byte-identical.
`commands_unrunnable_from_the_root` moves 82 to 85 for the three manifest files this study publishes;
bootstrap stays 6 and by-path load sites stay 5.

No LaTeX citation names this study's source: the report cites its results path, which K2 freezes, and the
model-card and analysis-note prose was already on `results/...`. The analysis note's two reproduction
commands are re-derived. No plant targets the moved file (`grep -c` of the path form in `plants.py` is 0).
mypy is 53 to 55 source files; no test added, so the pair stays **548 / 479**.

One measurement to record honestly rather than quietly: the gate wrapper's wall clock for the pytest lane
read 17995s while pytest's own summary on the same tree reads 228.82s. The machine was suspended between
launch and completion, so the wrapper's elapsed includes sleep. The per-lane exit codes are taken from the
commands and stand; the wall column in that log is not a measurement of anything about this commit.

### 2026-10-23, P3.3 absorption 14 of 19 — `real_data_risk_study`, and a test that broke its own stated rule

Fourteenth of 19. No living document had to change: the only three citations of
`experiments/real_data_risk_study/run.py` are dated records -- the phase-11 report twice and the numbered
integrity-audit finding at 190 -- and a dated record says what was true when it was written. Step 9's probe
found nothing else, escaped spelling included.

mypy was clean on the file's first entry into its corpus (55 to 57 source files), the second absorption
where the newly-covered arithmetic held up. `run()` became silent and the shim took all three summary
blocks, whose payload paths were measured by walking the committed artifact --
`A_estimator_validity.per_estimator`, `B_coverage_tests` and the `D_covariance` ranking key -- because the
banner's keys are not the locals' names. The replay's stdout is 2201 bytes with the same 2000-character
truncation the old `main` applied, and all three artifacts -- two CSVs and the PNG -- are byte-identical,
with **zero** differences anywhere in the JSON: this is the one artifact V2-23 listed that already carried
1.9.0, so even the version field agrees.

The finding is the test. `test_a_fresh_run_reproduces_the_committed_artifact_exactly` went red, and the
single field it disagreed on was `command`. Its own docstring has always said it strips "the same rule as
the evidence manifest's content digest", and the list it actually kept was four hand-written keys --
`generated_utc`, `environment`, `oracles`, `artifacts` -- which is not that rule: the digest waives
`command`, this test did not. So the guard was failing on a field the lane had already declared free to
move, and the interesting part is that the divergence pre-dated Phase 3.3 entirely; nothing could see it
until a commit moved the field for real. The waiver list now reads `VOLATILE_KEYS` from the digest's own
module, unioned with `oracles` -- the one key this test waives that the shared set does not, which is
exactly the gap V2-23 registered -- and the comment says so rather than letting a second list drift
silently again. The guard's falsifiability is not an assumption here: it failed minutes earlier for a
reason, and it still compares every number, verdict and ranking of the study.

`commands_unrunnable_from_the_root` moves 85 to 89 for this study's four manifest artifacts; bootstrap
stays 6 and by-path load sites stay 5. No plant targets the study's source. No test added, so the pair
stays **548 / 479**.

### 2026-10-23, P3.3 absorption 15 of 19 — the first benchmark moves, and the layout question answers itself

Fifteenth of 19 and the first of the five benchmarks, which is where D1's "one package" meets a second
layout: a benchmark is a single file in a suite directory, not a task directory with an entry-point pair, so
the destination is `python/quantrisk/benchmarks/quantlib/pricing_validation.py`. The open question was
whether that needs `__init__.py` files, and it was settled by measuring rather than by arguing:

- **import**: `python -m quantrisk.benchmarks.quantlib.pricing_validation` resolves and runs with no
  `__init__.py` anywhere under `benchmarks/` -- PEP 420 makes a directory inside a regular package a
  namespace portion, so `-m`, `importlib.import_module` and the suite runner all work.
- **typing**: mypy checked the file anyway -- 57 to 58 source files -- so no `__init__.py` is needed to keep
  it inside the static-check bucket, which is the ceiling
  `tracked_python_files_in_no_static_check_bucket` guards and which stays ok at 0.
- **parity**: the guard's side A walks `python/quantrisk/benchmarks/*/*.py`. Adding
  `benchmarks/quantlib/__init__.py` would make that glob report a runnable unit the registry does not
  carry, so the parity guard would go red on a *package marker*. No `__init__.py` keeps the glob meaning
  "one file, one unit", which is what the benchmark layout actually is.

Two contracts had to be met rather than bent. `test_an_absorbed_task_is_invocable_and_writes_where_it_is_told`
requires `run(argv) -> dict` of every absorbed task, and the benchmark arrived as a `main()` that computed,
wrote and printed. It is now `run(argv)` returning the summary and `main(argv)` printing it -- the same shape
as the studies -- with `--quick`/`--out` parsed by one `_parse(argv)` helper shared by both, because the
original printed banner names the CSV, the row count and the JSON, and reproducing it from the payload
(`summary["csv"]`, `summary["rows"]`) is what keeps the shim honest without a second parser.

The other one is the interesting failure. `test_the_documents_that_count_python_tests_count_the_ones_that_exist`
went red reading `no test re-executes the published benchmark script` -- not because the test stopped
executing it, but because the claim inventory's own detector looks for the interpreter and the `--quick` flag
*on the same source line*, and wrapping the argument list across eight lines made its count zero. The guard
caught a real thing (it is a spawn, and the sheet counts spawns) and was defeated by formatting. The call
list is one line again, with a comment saying why, so the next person does not reformat it back into
silence.

Behaviour: `command` was `" ".join([sys.argv[0], *sys.argv[1:]])`, which recorded
`benchmarks/quantlib/pricing_validation.py` -- a fragment, no interpreter, and under `-m` it would have
become a full machine path with whatever flags the caller passed. Now `TASK.invocation`. The replay is
byte-identical on the 18 816-row CSV, and the JSON differs in exactly the two declared places: the
`artifact` self-reference, and `csv`, which records where the companion file landed and so moves under
`--out` for the same reason `figure_status` does -- a third in-payload output-path field for P3.5 to weigh
with V2-23.

Documents re-derived: the model card's Level-2 citation, the interview-defense command block, and the
report's; the PDF rebuilt after them, bundle `66c75781bc64`, pdf `ec5d58229bb4`. Both spellings of the
probe were run; the remaining citations of the old path are the phase-02 and phase-10 reports, which are
dated records. `commands_unrunnable_from_the_root` holds at 89 -- a benchmark's recorded command was already
a bare path in the manifest, so it was in the does-not-exist bucket before the move. No test added, so the
pair stays **548 / 479**.

### 2026-10-23, P3.3 absorption 16 of 19 — `monte_carlo_vs_analytic`, and a test that had the old `--out` meaning

Sixteenth of 19, the second benchmark, and it went through §11 step 3's benchmark shape without surprise:
one file at `python/quantrisk/benchmarks/quantlib/monte_carlo_validation.py`, no `__init__.py`, one shared
`_parse(argv)`, `run(argv)` returning the summary and `main(argv)` printing it, mypy 58 to 59 source files.

What was new is that a *test* carried the old `--out` meaning.
`test_published_monte_carlo_benchmark_script_runs_and_reports` spawned the script with `--out <tmp>` and read
`<tmp>/monte_carlo_validation.json` -- the pre-refactor semantics were "this is the results directory". The
registry's `--out` names a repository root, so the first gate run went red exactly there, and the fix was to
re-point the test at `tmp/benchmarks/quantlib/results/...` rather than fork the convention for one caller.
Two absorbed units now share a rule instead of one rule and one exception.

Its recorded command was `f"uv run python {Path(sys.argv[0]).name} --paths {arguments.paths}"` -- the bare
filename with the path count glued on, which under `-m` would have named `__main__.py`. D4' makes it
`TASK.invocation`, and nothing is lost by dropping the parameter from the string because the payload already
records it twice over as `paths_per_run: 200000` and `seeds: 40`; that was checked in the committed artifact
before the change, not assumed from the field names.

The replay's CSV is byte-identical and the JSON differs in the same two declared places as absorption 15 --
the `artifact` self-reference and the `csv` landing path. Everything the third yardstick decided is
unchanged: `quantlib_mc_engine_used` matches, so the run reproduced the same "QuantLib's own MC engine is
unavailable in this build" verdict the published artifact states, including the two `unknown MC traits: sobol`
lines on stderr.

Documents re-derived: the Monte Carlo model card's Level-2 citation, the interview-defense command (which
keeps its `--paths 200000`), and the report's; the PDF rebuilt after them, bundle `b184d7ff272f`, pdf
`9cd5762eaf19`. `bootstrap_sites_outside_package` stays 6, by-path load sites 5,
`commands_unrunnable_from_the_root` 89 and `commands_not_module_path` 95; offline collection is still 479 and
no test was added, so the pair stays **548 / 479**.

### 2026-10-23, P3.3 absorption 17 of 19 — `path_dependent_vs_quantlib`, and a splice the formatter caught

Seventeenth of 19, third benchmark, and the first of the three with **no test that spawns it**: the path
dependent oracle comparison is exercised by the suite and checked through its artifact, so the only test-tree
edit this commit makes is a C++ comment -- `tests/cpp/test_path_dependent.cpp:201` says the barrier
convergence is "checked quantitatively against AnalyticBarrierEngine in" that file, and the file has a new
name. mypy found 1 defect (the familiar `float(row["relative_error"])` against `dict[str, object]` rows; two
annotations widened), and the report, the model card and that comment are re-derived with it, PDF bundle
`92cc6ad1fc15`, pdf `8400d3de3c56`.

The lane's own mistake, recorded because it is the second instance of the same shape. The registry flip was
done by string surgery -- `old[:-5] + "        absorbed=True,\n    ),"` -- which left the new line indented by
nine spaces instead of eight. The first full gate run caught it as `ruff format --check` rc=1, and that was
the only red on the tree; nothing else would have noticed, because the file parses, imports and type-checks
either way. Absorption 16 got away with the identical splice by luck. So: registry flips go through the Edit
tool from here, and `ruff format --check` is what makes the splice safe to attempt at all -- it is a gate on
this lane's own mechanics, not a stylistic one.

The command field read `f"uv run python {Path(sys.argv[0]).name}"`, which under `-m` names `__main__.py`;
D4' makes it `TASK.invocation`, and the run's `--paths` value is not lost because the payload already records
`paths`. The replay was run **again after** the annotation change rather than argued to be unaffected by it:
same result -- the 25-row CSV byte-identical, the JSON differing only in `artifact` and in the `csv` landing
path, the two declared classes of this stretch of the lane.

`bootstrap_sites_outside_package` stays 6, by-path load sites 5, `commands_not_module_path` 95 and
`commands_unrunnable_from_the_root` 89 -- a benchmark recording a bare filename was already in the
does-not-exist bucket, so a move cannot make that counter worse. mypy 59 to 60 source files, offline
collection 479, and no test added, so the pair stays **548 / 479**.

Correction, added later the same day to this same-day entry rather than as a new one. The commit described
above (`ee9bde2`) was pushed **without the rebuilt render**: it carries this absorption's
`paper/technical_report.tex` and the previous absorption's PDF and build record -- bundle `b184d7ff272f` /
pdf `9cd5762eaf19` in the commit against `92cc6ad1fc15` / `8400d3de3c56` in the worktree, and the older PDF's
own digest in the committed blob proves which render landed there. The cause is a command order I wrote:
`git add … && build_report.py`, which re-dirtied the two generated files after the last staging; and the
`git status` I read in the same block as the commit showed both as ` M` and I did not act on it. The gate
suite stayed green because it measures the worktree, which was right -- so only the committed object was
wrong, and that is the exact failure #90's freshness pair exists to catch, one commit after it was used to
catch somebody else's. The fix is forward: the render is committed on its own, the pushed commit is not
rewritten, and CI's verdict on `ee9bde2` is recorded as it turns out rather than as I expect it. Two practice
changes follow, because a lane's own mechanics need gates too: the report is rebuilt *before* the staging
command, and the check after a commit is `git status --porcelain` empty against the file list the commit
needed, not a `--stat` that merely looks plausible.

## 10. Laws as of the end of Phase 1

§13 requires this table when Phase 1 closes. It is the lane's reading, not the prompt's authoring
reading: two laws the prompt recorded as VOID are now ACTIVE, and one it treated as a plan is still
unimplemented, which is what §12's premises audit will cite.

| Law | Status | The reading that decided it |
|---|---|---|
| L1 content-digest invariance | **ACTIVE, with a precondition it cannot yet satisfy** | both manifests exist to compare and the registry is the source of truth for invocations, but 18 of 95 entries have a null content digest (V2-08), so the check would halt the lane on `suite_summary.md` at P3.5 unless the byte-only set is declared first |
| L2 one finding, one commit | **ACTIVE** | every Phase 3 commit so far names its finding in its subject or body, including the one that exists only to complete a claim its predecessor overreached (3f78b2e → 32b76d5) |
| L3 no gate weakened | **ACTIVE** | no tolerance, skip or xfail was added; the two lanes that reddened (count guards, `plant-list rc=2`) were answered by re-deriving the corpus, not by loosening a check |
| L4 canonical invocation | **VOID until its guard exists** | D4 is now D4′ and one command uses the canonical form in a gate (`-m quantrisk.verification.runner` in the derivation's test), but the dry-resolve instrument V2-07 asks for is unwritten, so the check cannot be run and the law cannot be cited as satisfied |
| L5 registry parity, two-sided | **ACTIVE** | implemented and measured: registry 19 sources, filesystem 19 units, mismatch 0, each side printing its enumeration, neither reading the other |
| L6 no bootstrap hacks | **ACTIVE, unmet** | 10 `sys.path` sites and 17 by-path loads remain; both are ceilings due P3.4/P3.3, and the census prints its corpus rather than an empty success |
| L7 plant liveness | **ACTIVE, proven once** | the sweep's own line at `32b76d5`: `172/172 planted defects were rejected by their guard.`, exit 0, no non-caught status — which is also the proof that the two instrument moves did not disarm the 23 anchors they re-keyed |
| L8 instrument identity | **partly exercised, still VOID as a law** | the Phase 0 probe printed `sys.prefix`, the package file and the extension path and refused a foreign root, but the law's check is the Phase 4 wheel, which does not exist yet |
| L9 static-check parity | **ACTIVE, incomplete** | the census places all 91 tracked Python files in exactly one bucket — 28 covered by mypy and ruff, 63 by ruff alone, 0 uncovered — and mypy's reported 28 equals an independent enumeration of its target; the target list still omits `tools/`, which is P3.7 |
| L10 counted claims owned | **ACTIVE** | it fired twice in this lane and each time the corpus moved: `539/470 → 545/476` across five documents, four plant anchors and three census gold lists |
| L11 facts precedence | **ACTIVE** | five findings are the document losing to a reading (V2-01, V2-04, V2-05, V2-17, V2-18), and §3's own first draft was corrected in public when the measurement contradicted it |
| L12 zero external spend | **ACTIVE** | no dependency added; the lane's only network use is read-only GitHub transport, which costs nothing and is currently intermittent |
| L13 baseline purity | **ACTIVE** | the baseline names its revision and its export; two heads (`b8daf28`, and the queued pair behind the current tip) are recorded as never executed rather than as green |

## 11. How to absorb one task (the P3.3 recipe, derived from the first one's dependencies)

`stress_testing` was read end to end before this recipe was written, and the list below is what its
dependencies turned out to be — not what §8's lane summaries assumed. Run it per task, in
`ABSORPTION_ORDER`, one commit per task. Each step names the probe that shows it worked.

One prerequisite came out of reading the dependents rather than out of §8: `scripts/run_benchmark_suite.py`
stored its own copy of every task's source path, artifact path and category, so step 5 would otherwise
leave the suite naming a file that no longer exists and force a rewrite of the disk-to-registry guard once
per task. P3.3a made the member read those three from the registry, and proved the regenerated aggregate
identical in every member field before it moved anything.

1. **Red first.** Add the task's assertion that the module is importable and its artifact is still
   written to the frozen path, then watch it fail: `uv run python -m quantrisk.experiments.<task>` does
   not exist yet. Record the failure in the commit message.
2. **Move the body.** `git mv experiments/<task>/run.py
   python/quantrisk/experiments/<task>/__init__.py`, keep the module docstring verbatim (it is the
   study's claim prose), and re-point only its usage line to `-m quantrisk.experiments.<task>`.
   The `<task>` in the destination is the *directory*, not the task id: `_study` composes `module` from the
   directory, so `pricing_grid` lands in `experiments/pricing_validation/` and `mc_convergence` in
   `experiments/monte_carlo_convergence/`. Guessing from the id is caught, not silent -- `validate_task`
   refuses an absorbed task whose module does not resolve, and the replay exits 1 before anything is
   written. Probe: `git diff --stat -M` shows a rename, not a rewrite.
3. **Split the entry point.** `run(argv) -> dict` holds the work and returns the summary payload;
   `main(argv) -> int` is the CLI shim; `__main__.py` is `raise SystemExit(main())`. No behaviour may
   be added here: the payload's keys are the artifact's keys, byte-comparable except for volatile
   fields. Probe: the task's existing test suite, unchanged in assertion, green.
   Benchmarks take the same split but not the same shape: their destination is one file,
   `python/quantrisk/benchmarks/<suite>/<script>.py`, and `if __name__ == "__main__"` stays in it because
   `-m` executes the module itself -- no `__main__.py`, and no `__init__.py` under `benchmarks/`: the
   namespace import resolves, mypy checks the file regardless, and a package marker would make the parity
   guard's `benchmarks/*/*.py` glob count a unit the registry does not carry. Where a benchmark already
   parses its own flags, keep one parser and share it (`_parse(argv)`), because a shim that re-parses with
   the registry's `parse_out` rejects the study's own arguments.
4. **Output path.** `RESULTS = Path(__file__)...` and `REPO_ROOT = parents[2]` both die. Resolve the
   directory from `TASKS_BY_ID[<task>].artifact` against a root that is either an explicit `--out` or
   `checkout_root()`; refuse, naming the path, when there is neither. Never fall back to a temporary
   directory and never synthesise input data. A published *input* a study reads (a sibling's frozen
   artifact) comes from `checkout_root()` whatever `--out` says -- `--out` moves outputs, not the
   evidence a control is checked against. Probe: `run(["--out", tmp])` writes under `tmp`; `run([])`
   outside a checkout raises. Absorption 5 adds one line the first four did not need to learn: the
   closing print must go through `repo_relative`, because `--out` may be a relative path and
   `Path.relative_to(checkout_root())` raises on one -- the replay caught it before the gate did.
5. **Flip the registry entry** — `absorbed=True`, `source` now the package path. Probe: the parity test's
   two enumerations still agree, because side A already recognises `*/__main__.py`. The suite runner needs
   nothing here: it stopped storing its own copy of those paths in the prerequisite commit, so a member
   follows the entry it names.
6. **Re-point the siblings that load it.** A dependent study's `spec_from_file_location(.../run.py)`
   becomes a package import of the same symbol — the "load the definition, do not copy it" property
   quoted in `experiments/fourth_order_crossing_map/run.py:101-103` must survive the move, so the import
   replaces the loader rather than duplicating functions.
   Probe: `grep -n "spec_from_file_location" experiments/<dependent>/run.py` returns nothing for the
   moved task, and the dependent's guard test still passes.
7. **Re-point the tmp-tree replicas.** Six tests build a fake checkout with hard-coded paths
   (`tests/python/test_second_book_crossing_map.py:368-372` and its neighbours). They are part of this
   commit, not a later cleanup. Probe: the mutation lane green.
8. **Re-key the plants that target the moved file.** `grep -c 'path="experiments/<task>/run.py"'
   python/quantrisk/verification/plants.py` before and after: the count must reach zero with each
   replacement pointing at `python/quantrisk/experiments/<task>/__init__.py`, and anchors that quote
   deleted lines are replaced, not relaxed. Probe: the anchor self-test green, and a full sweep at the
   end of the phase group rather than one per task.
9. **Re-derive the documents that quote the command.** `paper/technical_report.tex` quotes each study's
   invocation (its line 2080 is `stress_testing`'s) and its prose quotes the file path (line 1378);
   `docs/reproducibility.md`, `docs/validation_matrix.md`, `docs/interview_defense.md`,
   `docs/project_scope.md` and `CONTRIBUTING.md` quote commands too. A tex edit forces the PDF rebuild
   and both freshness guards. Probe: the docs lane green and the report build pair consistent.
   Absorption 6 found that probe too narrow, because a document can name a study in prose rather than as
   a command line, so it now ends with `grep -rn "experiments/<task>/run\.py" docs/ paper/ README.md
   CONTRIBUTING.md`. What may remain is a dated record -- `docs/phase_reports/**`,
   `docs/release_notes_v1.*.md`, the numbered findings of `docs/integrity_audit.md`, this ledger's own
   finding text -- because those state what was true when written. Living prose (the validation matrix's
   rows, a limitation entry) states current behaviour and follows the file. Absorption 7 found the same
   probe narrow on a second axis: inside `paper/technical_report.tex` every underscore is written `\_`, so
   a citation to `fourth_order_crossing_map` does not match a pattern containing `fourth_order_crossing_map`
   -- four report citations had sat through four commits that way, and the miss is registered as V2-21.
   Run the probe twice, the second with `\_` substituted, before believing a document tree is clean.
10. **Gate, then commit.** Full §7 suite, `git status` empty, commit staged by path, the committed
    object verified (`git show --stat`) before the message is believed, then push. If a Dependabot or
    other session's commit lands first, rebase — never force.

**Deliberately untouched by these steps:** `experiments/<task>/results/**` (K2 — the directory stays
where it is and holds only results once `run.py` is gone), `evidence/manifest.json` (K4 — it is rebuilt
once, at P3.5), and every provenance string already frozen inside an artifact. V2-20 was adjudicated by
the maintainer on 2026-10-22 as option (i): a study cites a published sibling as a registry reference
(`<task>:<symbol>`), the artifacts re-derive once at P3.5, and that field's movement is declared in
`tools/refactor_ceilings.json` with its reason. The *code* of the citing study changes in the commit that
moves the cited file — a path that no longer resolves is not evidence — while the frozen artifact keeps
the string it was written with until the single re-run replaces it.
