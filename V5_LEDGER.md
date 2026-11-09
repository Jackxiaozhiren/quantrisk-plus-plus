# V5_LEDGER.md — the cross-session state of the V5 series

V4 closed at `eb75b3277d28307f29fe9fc16b86e24d3f96ba24` (the terminal entry of its Phase 5
report). This file starts after that commit and records only tool readings. Unlike V4, V5 has a
written prompt: `V5_PROMPT.md` is delivered by V5-01, the first unit of this series. The prompt
states the premises, the lanes, the inherited rails and the termination condition; this ledger
states what the tools printed, at which revision, and what was decided from it. A reading in the
prompt or in `V4_LEDGER.md` §7 is an inherited claim until this file re-measures it.

### 2026-11-09, V5 Phase 0 — the archive re-counted at `eb75b32`, and the first unit chosen

**Why this phase exists.** `V4_LEDGER.md` §8's archival confirmation was written at `a74cf9a`,
before the report commit `821d9bc` and the terminal entry `eb75b32`. Its six numbers describe
`ad03b89`, not the tip that is actually pushed. §14 says a fresh reading wins over an inherited
claim, so every number below was re-measured at `eb75b32` with `git status --porcelain` printing
0 lines, before this file existed.

**Revision and vantage.** `HEAD` = `origin/main` =
`eb75b3277d28307f29fe9fc16b86e24d3f96ba24`; `v1.9.0` =
`d9deb7f764b3c16a091dc86effb9d523b1d2c7d0`. Vantage: the development checkout, `.venv` Python
3.12, macOS, the same WorkBuddy interpreter shim V3 Phase 5 and V4 recorded. The git smart-HTTP
channel is still blocked, so this unit's pushes use the Git Data API as V4-03…V4 Phase 5 did.

**Platform readings, not session memory.** `gh api repos/Jackxiaozhiren/quantrisk-plus-plus/commits/main`
returns `eb75b3277d28307f29fe9fc16b86e24d3f96ba24`; `refs/tags/v1.9.0` points at tag object
`d9deb7f764b3c16a091dc86effb9d523b1d2c7d0`, dereferenced to commit
`b2dda33f6726d7f36fbe3491aec7cd7a66184809` with tagger `2026-10-20T12:56:35Z`; release
`424060629` was published `2026-10-26T09:35:44Z` with four assets (`CITATION.cff`,
`manifest.json`, `quantrisk-suite-results.zip`, `technical_report.pdf`), all created
`2026-10-26T09:35:41Z` and last updated between `09:35:42Z` and `09:35:43Z`. Terminal run
`42547406106` was re-read as `completed` / `success`, `run_attempt 1`, `head_sha eb75b3277d28`.
One assets call returned `EOF`; per §14 that absence is unknown, and the reading above is the
re-run that returned four rows.

**The archive re-counted at this tip.**

| quantity | command that produced the reading | value |
|---|---|---|
| registry tasks | `uv run --frozen python -m tools.inventory_orphan_code --reading registry_parity` | `filesystem_units 19`, `registry_sources 19`, `mismatch []` |
| suite members | `--reading with_extras_census` | `members 19`, `passed 19`, `gap 0`, `revision 17df062040b8` from the committed `suite_run.json` |
| plants | `uv run --frozen python -m quantrisk.verification.runner --list` | **194** lines; `plant_liveness.declared_plants 194` |
| ceiling keys | `--check-ceilings` | **14** — **12 `ok` / 2 `SKIP`**; the three V4 keys all `0` |
| manifest | `uv run --frozen python -m tools.verify_evidence_manifest` | `95 OK`, `0 CHANGED`, `0 MISSING`, `Evidence is intact.` |
| formatter corpus | `--reading formatter_census` | `tracked_formattable 232`, `walked_formattable 232`, `reported_already_formatted 232`, both differences empty |
| pytest nodes | `uv run --frozen pytest --collect-only -q`; `uv run --frozen python -m tools.measure_offline_collection` | **560** collected; offline tail `491 tests collected`, `collection_errors 0` |
| lane contract | `--reading lanes_documented_vs_executed` | `gap: 0`; `executed_not_documented []`, `undeclared []`, `status_mismatch []`; `grep -c '^      - name:' .github/workflows/ci.yml` prints **32** |
| living documents | `--reading docs_rederivation` | `documents 5`, seven claims, `derived {19, 19, 194, 95}`, `mismatches []`, `gap: 0` |
| runtime reachability | `--check-ceilings` (the printed reading) | `ast_dead 13`, `import_reachable 13`, `pytest_collected 6`, `reached_by_neither 0`, `runtime_reachability_gap: 0` |
| static gates | `uv run --frozen ruff check .`; `ruff format --check .`; `mypy python/quantrisk tools` | `All checks passed!`; `232 files already formatted`; `Success: no issues found in 74 source files` |

Difference against `V4_LEDGER.md` §8's six numbers: **empty**. The 232 in this table is a reading
taken *before* this file was created. Adding this ledger is itself a tracked `.md`; the
implementation entry re-measures the corpus after both new files exist and names the delta rather
than repainting this row (§15 item 7).

**The seven handoff items, re-measured rather than quoted.** `V4_LEDGER.md` §7 lists what V5 must
contain. Each row below is this session's own reading at `eb75b32`, not a restatement of that
section.

1. **No written V5 prompt.** `ls V5_PROMPT.md V5_LEDGER.md` prints `No such file or directory` for
   both; `ls -1 *PROMPT.md *SPEC.md` prints `PROJECT_SPEC.md`, `REFACTOR_PROMPT.md`,
   `V3_PROMPT.md`. V4 §4 item 7 says V4 ran on inherited rails without one.
2. **The sweep's vantage is undecided.** `--check-ceilings` prints
   `SKIP plants_not_rejected_by_their_guard: precondition absent`, with the reason that the sweep
   writes gitignored scratch CI never has. The `194/194 planted defects were rejected by their
   guard.` summary captured at `a74cf9a` is a development-vantage reading, not a runner gate.
3. **`working_tree_dirty` is still undiagnosed.** `grep -n working_tree_dirty
   tools/run_benchmark_suite.py` prints three sites: `943` (the printed `(working tree was dirty
   at run time)` marker), `952` (the warning that the artifacts describe uncommitted work) and
   `1075` (`"working_tree_dirty": env["working_tree_dirty"]`, the value's origin). V4 §4 item 2
   recorded the line at every tip without explaining the condition. This Phase 0 names the three
   sites; it does not diagnose the producer.
4. **The committed suite artifact is not pinned to HEAD.** `--reading with_extras_census` prints
   `revision 17df062040b8` while `HEAD` is `eb75b3277d28`. The reading checks member keys,
   statuses and totals, not the artifact's age; both it and the benchmark job's fresh artifact
   print `gap: 0`.
5. **The installed-surface proof was not re-run.** `--check-ceilings` prints
   `SKIP installed_user_identity_mismatch: precondition absent`, with the reason that it installs
   a second environment outside the checkout. V4 §6 marks that lane unverified; the last reading
   is V3 §6 at `d502a61`.
6. **`tools/generate_shim_stubs.py` is reachable but has no invoking lane.** `grep -rn
   generate_shim_stubs --include='*.py' --include='*.md' --include='*.yml' .` outside `build/`
   finds the file's own docstring, `tests/python/test_shim_stubs.py` importing it with
   `importlib.import_module`, historical phase reports and ledger prose, and no `run:` line in
   `.github/workflows/ci.yml` and no `-m` invocation in either lane-bearing document.
   `runtime_reachability` reports `reached_by_neither 0` because importability is not use.
7. **The published asset set is unchanged, and the two SKIP keys remain.** The platform readings
   above show four assets with 2026-10-26 timestamps; `--check-ceilings` prints both SKIPs. V4 §7
   item 7 asks that K5 continue to hold; no decision about the two keys has been taken yet.

**The decision, and what it excludes.** V5-01 takes handoff item 1: it delivers `V5_PROMPT.md` with
the premises, the lane inventory, the inherited rails, the case-by-case approval rule and the
termination condition, plus this ledger's implementation-and-readings entry. It takes **none** of
items 2–7 as a fix. It does not make the sweep a CI lane, does not diagnose
`working_tree_dirty`, does not add a revision check to `suite_run.json`, does not re-run the
installed-surface proof, does not change either SKIP key, and does not decide
`generate_shim_stubs.py`. No source file, guard, plant, ceiling key, CI step, test node, artifact,
PDF, tag, release asset or locked path moves: `cpp/`, `bindings/`, `CMakeLists.txt`,
`PROJECT_SPEC.md`, `REFACTOR_PROMPT.md`, `V3_PROMPT.md`, `evidence/manifest.json` and `paper/`
are untouched. No census is claimed in this unit; the last captured full sweep is `194/194` at
`a74cf9a`, and a documentation-only unit does not re-run it.

**The approval for this case, recorded verbatim (§14).** The maintainer's instruction that opened
this unit is `授权启动`, given in response to the V4 Phase 5 handoff which stated that starting V5
is a new scope unit and needs a new case-by-case approval. Read against §14, that is approval for
this one scope unit — the series launch, comprising the Phase 0 commit, the written prompt and its
readings, and two pushes: the implementation-and-readings tip, and the entry recording that tip's
CI. Both are attributed below; no third is implied, and this is not a standing approval. V5-02 and
every later unit each require their own verbatim approval in their own Phase 0 entry. Editing
`V5_PROMPT.md` itself after it ships also requires one. The terminal commit's own CI is read after
the second push and reported in the session handoff, as in every V4 unit.

**Deliberately not done in Phase 0.** No prompt was written, no source or policy file was edited,
no plant added, no ceiling key changed, no CI step added, no census run, no report section written
and no push made. The seven items above are *measurements*, not verdicts. Every number in this
entry is a reading at `eb75b32`; none is quoted from `V4_LEDGER.md` without being re-measured.

---
