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
| _(Phase 1 lanes 1–2 are the collector's and are already in V2-02/03/06; low-severity hygiene from lane 4 — 24 `spec_from_file_location` sites in `tests/python/` that switch to imports as their targets move — is carried in the commit sequence rather than as its own finding)_ | | | | | | | | | | | |

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
2. Re-run §7 step 4 in a fresh detached export, exactly as §1 describes. If a lane is red that this file
   recorded green, that is a finding, not noise, and it is entered in §6 before anything is fixed.
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
