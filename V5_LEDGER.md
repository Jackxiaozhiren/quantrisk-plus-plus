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

### 2026-11-09, V5-01 — the written rails ship, and the corpus is re-counted at 234

**What this commit carries.** `V5_PROMPT.md`, 208 lines in eight numbered sections: three measured
premises and a termination condition (§0), the mission (§1), the priced locks and the no-weakening
rule (§2), a six-clause Facts Protocol (§3), the lane and policy-asset inventory (§4), the F1–F7
candidate findings each with a `check:` predicate (§5), the one-unit-per-approval rule (§6), the
Phase 0 / Phase 5 / Definition-of-Done procedure (§7), and a size ratchet (§8). Its prose sections
(§1–§3 and §6–§8) span **104** lines against `V3_PROMPT.md` §0's **431**-line bound, measured by
heading span: 49 and 55 lines respectively. The prompt is a rule set, not an approval: §6 states
that V5-02 and every later unit, including one that edits the prompt itself, need their own
verbatim case-by-case approval.

**The readings after both new files exist.** These were taken with `V5_LEDGER.md` committed at
`69821a1` and `V5_PROMPT.md` staged, so the formatter census sees both enumerations on the same
side; the 232 → 234 delta is exactly the two new tracked `.md` files, named rather than repainted
(§15 item 7).

| quantity | command | reading |
|---|---|---|
| formatter corpus | `--reading formatter_census` | `tracked_formattable 234`, `walked_formattable 234`, `reported_already_formatted 234`, `reported_would_reformat 0`, `tracked_but_not_walked []`, `walked_but_not_tracked []`, `walked_other_kinds 119` |
| static gates | `ruff check .`; `ruff format --check .`; `mypy python/quantrisk tools` | `All checks passed!`; `234 files already formatted`; `Success: no issues found in 74 source files` |
| ceiling keys | `--check-ceilings` | **14** — **12 `ok` / 2 `SKIP`**; `tracked_files_outside_the_formatter_corpus: 0`, `docs_rederivation_gap: 0`, `with_extras_census_gap: 0`, `lanes_documented_vs_executed_gap: 0` |
| living documents | `--reading docs_rederivation` | `documents 5`, `gap: 0`, `mismatches []`, `source_disagreements []` |
| lane contract | `--reading lanes_documented_vs_executed` | `gap: 0`, `executed_not_documented []`, `undeclared []`; `grep -c '^      - name:' .github/workflows/ci.yml` prints **32** |
| with-extras artifact | `--reading with_extras_census` | `gap: 0`, `members 19`, `passed 19`, `revision 17df062040b8` — unchanged from Phase 0, and still not pinned to HEAD |
| registry / plants | `--reading registry_parity`; `-m quantrisk.verification.runner --list` | `19 / 19`, `mismatch []`; **194** lines |
| manifest | `python -m tools.verify_evidence_manifest` | `95 OK`, `0 CHANGED`, `0 MISSING`, `Evidence is intact.` |
| pytest nodes | `pytest --collect-only -q`; `tools.measure_offline_collection` | `560 tests collected`; offline `491 tests collected`, `collection_errors 0` |
| local full suite | `pytest -q --basetemp=<fresh private TMPDIR>` | **1 failed, 559 passed in 124.32s**; the sole failure is `test_a_restored_plant_cannot_be_read_back_from_a_stale_bytecode_cache`, the sandbox-only plant V3 and V4 recorded. `git status --porcelain` afterwards prints **one** line, `A  V5_PROMPT.md` — this unit's own implementation file, staged before the pytest run, not a plant residue; no probe directory or mutation remains. |
| locks | `git diff --name-only HEAD -- cpp/ bindings/ CMakeLists.txt PROJECT_SPEC.md REFACTOR_PROMPT.md V3_PROMPT.md evidence/manifest.json paper/` | empty |

**F1's `check:` predicate, run at this commit.** The prompt exists; it states premises, lanes,
rails and termination; §6's approval rule was followed by this launch unit's Phase 0 entry, which
records `授权启动` verbatim, names its two pushes and no third, and says V5-02 needs a new
approval. **F1 is the only finding this unit closes.** F2–F7 remain open with their Phase 0
readings; in particular `plants_not_rejected_by_their_guard` still SKIPs, `working_tree_dirty` is
still undiagnosed, `suite_run.json` still carries `17df062040b8`, and neither SKIP key has a
decision.

**Deliberately not done.** No source file, guard, plant, ceiling key, CI step, test node, artifact,
PDF, tag, release asset or locked path was changed. No plant was added, so no targeted sweep is
claimed; the last captured full sweep remains `194/194 planted defects were rejected by their
guard.` at `a74cf9a`, and `V5_PROMPT.md` §4 requires the next full census at the **final** V5 tip,
not at every intermediate one. The two new files are prose: `LIVING_DOCUMENT_CLAIMS` still holds
five documents, and `LANE_DOCUMENTS` still holds `docs/reproducibility.md` and
`CONTRIBUTING.md`, so neither new file enters those two readings. Every number above was printed
by a tool in this unit.

**The first push.** The Phase 0 commit `69821a1` and this implementation-and-readings commit are
pushed together in the first of the two pushes authorised in the Phase 0 entry. Its CI is read
once the tool reports it and recorded in the next entry; this file states no outcome for a push
that has not happened yet.

---

### 2026-11-09, V5-01 — the implementation tip is green, and the run is attributed

**The first push, as read from the platform.** `build/api_push.py` rebuilt both commits through
the GitHub Git Data API and moved `refs/heads/main` from `eb75b3277d28307f29fe9fc16b86e24d3f96ba24`
to `8c787bdee6604f232b67085875e3630bb1bba035` with `force: false`. Every commit SHA matched its
local object (`69821a16bad18e56c6494d1bbc206424fe52abd4`,
`8c787bdee6604f232b67085875e3630bb1bba035`), and the two new blobs matched too:
`V5_LEDGER.md` = `49cbff1980ce92a2a383d6cfc3699acc110eaed0`, `V5_PROMPT.md` =
`148e5fa54c2b363d6cf463d21d283e8b6b475f79` on both sides. `git rev-parse HEAD` equals
`git rev-parse origin/main`; `git status --porcelain` printed 0 lines.

**The CI reading (§16.8).** `gh api repos/.../actions/runs/42553273948` reports `event push`,
`status completed`, `conclusion success`, `run_attempt 1`, `head_sha
8c787bdee6604f232b67085875e3630bb1bba035`, created `2026-11-09T02:52:19Z`, updated
`02:59:34Z`. The four jobs, each with **14** executed steps:

| job | conclusion | runner | labels | completed at |
|---|---|---|---|---|
| `128953337375` Format and static checks | `success` | `1000010493` | `ubuntu-latest` | `02:53:42Z` |
| `128953337425` macOS native C++ and Python parity | `success` | `1000010496` | `macos-15` | `02:55:33Z` |
| `128953337399` Configure, build, C++ tests, Python tests | `success` | `1000010495` | `ubuntu-latest` | `02:58:23Z` |
| `128953337230` Benchmark suite against live oracles | `success` | `1000010494` | `ubuntu-latest` | `02:59:34Z` |

No job is cancelled and none has 0 steps. **An interrupted watch is not a verdict:** the first
`gh run watch 42553273948 --exit-status` returned exit 1 with `failed to get run ... unexpected
EOF` while the run was still `in_progress`. Under §14 that absence is `unknown`, not failure and
not success; the API was re-read (one job `success`, three `in_progress`), the watch was retried
to exit 0, and the run and jobs above were read again from the API before any conclusion was
written here. Two informational annotations accompanied the run — the `ubuntu-latest` image-label
migration notice and a macOS arm64 capacity notice; neither changed a job's conclusion.

**What the four job logs printed.** Lint (`128953337375`): `All checks passed!`,
`234 files already formatted`, `Success: no issues found in 74 source files`,
`declared_plants 194`, `documents 5 / gap 0`, 14 keys with 12 `ok` and 2 `SKIP`,
`Evidence is intact.`. Build-and-test (`128953337399`): `100% tests passed out of 204`,
`490 passed, 5 skipped in 173.42s`, `7/7 checks passed`. macOS (`128953337425`):
`100% tests passed out of 204`, `98 passed in 2.69s`. Benchmark (`128953337230`):
`suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 260.9s total`;
its `With-extras census` step printed `gap: 0`, `members: 19`, `passed: 19`,
`revision: 8c787bdee660` from the freshly generated artifact, while the lint job's committed
artifact still reads `17df062040b8`. The benchmark summary again prints
`- revision: 8c787bdee660 **(working tree was dirty at run time)**`.

**F2, F3 and F4 are still open at this tip.** Two vantages of the same with-extras reading print
two different revisions and both print `gap: 0`, and the dirty marker is still unexplained. These
are recorded as readings, not as diagnoses: V5-01 took F1 only. `plants_not_rejected_by_their_guard`
and `installed_user_identity_mismatch` are the two SKIPs in the lint log above.

**The second push.** This entry is the second of the two pushes authorised in the Phase 0 entry,
and carries this entry only; no third is implied. The terminal commit's own CI is read after that
push and reported in the session handoff, not written into the file whose content is fixed before
that push — the convention V2, V3, V4 and this unit's implementation entry used.

---

### 2026-11-09, V5-02 Phase 0 — the open findings taken together, measured at `9e35c9c`

**Why this phase exists.** V5-01 closed F1 and left F2–F7 open. The maintainer asked for the
remaining work in one request, then chose the series-wide option when asked how far that authority
reached: `帮我完成剩余未完成部分`, followed by `整个剩余系列（推荐）`. Both are recorded verbatim
below because §6 requires the approval for a unit to name its case.

**Approval, verbatim.** `帮我完成剩余未完成部分` (2026-11-09), the selection
`整个剩余系列（推荐）` whose stated plan is *"我按 F4→F3→F2→F5→F6→F7→最终 census→Phase 5 顺序
逐单元连续推进，每单元仍单独写 Phase 0（逐字记录本句授权）、两次推送与两次 CI 归因"*, and the
subsequent `继续`. This entry does not edit §6 and cannot: it records that the maintainer granted
the whole remaining series in one case, which is the explicit override §6 asks the assistant to
request rather than assume. The override is bounded to V5's remaining findings, the final census
and the Phase 5 report. Nothing in it authorises a change to `V5_PROMPT.md`, a new release, or work
outside V5.

**Revision and vantage.** `HEAD` = `origin/main` =
`9e35c9cd6060a89f560b3ab6b5a17a737116cf0a`; `git status --porcelain` prints 0 lines. Vantage: the
development checkout, `.venv` Python 3.12, macOS, the same WorkBuddy interpreter shim V3 Phase 5,
V4 and V5-01 recorded. Git smart-HTTP remains blocked, so both pushes use the Git Data API.

**The archive re-counted at this tip.**

| quantity | reading | value |
|---|---|---|
| registry tasks | `--reading registry_parity` | `filesystem_units 19`, `registry_sources 19`, mismatch empty |
| suite members | `--reading with_extras_census` | `members 19`, `passed 19`, `gap 0`, `revision 17df062040b8` |
| plants | `runner --list` | **194** |
| ceiling keys | `--check-ceilings` | **14** — 12 `ok`, 2 `SKIP` |
| manifest | `tools.verify_evidence_manifest` | `Evidence is intact.` (95 entries) |
| formatter corpus | `--reading formatter_census` | **234 / 234**, both differences empty |
| pytest nodes | `--collect-only`; `measure_offline_collection` | **560** collected; offline `491 tests collected`, `collection_errors 0` |
| named CI steps | `grep -c '^      - name:' .github/workflows/ci.yml` | **32** |
| living documents | `--reading docs_rederivation` | `documents 5`, `gap 0` |
| runtime reachability | `--check-ceilings` | `reached_by_neither 0`, gap 0 |
| static gates | `ruff check`; `ruff format --check`; `mypy python/quantrisk tools` | `All checks passed!`; `234 files already formatted`; `74 source files`, no issues |

**Platform state, re-read rather than remembered.** `refs/tags/v1.9.0` is tag object
`d9deb7f764b3c16a091dc86effb9d523b1d2c7d0`, dereferenced to commit
`b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`. Release `424060629`
was published `2026-10-26T09:35:44Z` with four assets, all created `09:35:41Z` and updated between
`09:35:42Z` and `09:35:43Z`. Runs `42553273948` and `42554133271` re-read as `completed` /
`success`, `run_attempt 1`.

**What this unit takes, and why together.** §5 says the unit's Phase 0 decides which finding it
takes. This unit takes **F2, F3, F4, F5 and F6**, because the maintainer's single case covers the
whole remainder and because only one of the five changes the corpus: F4 needs a reading that can
redden; F2, F5 and F6 are decided or recorded against findings that already carry their evidence;
F3 needs its producer traced. Splitting them into five units would push the same tree five times
and read five more CIs without changing a byte between them, which is the mechanical repetition §6
exists to prevent, not the cross-session drift it exists to catch. F7, the final 194-plant census
and the Phase 5 report stay out of this unit and belong to V5-03, whose Phase 0 records the same
approval again.

**What each finding will be closed by.** F4 gets a new collector reading `artifact_revision` that
compares the suite artifact's `repository.git_commit` with the tip being verified, names which
vantage produced the artifact, refuses a revision that is not a commit in this repository or that
its own `provenance` does not name, and reports the disagreement as a gap a ceiling adjudicates. It
is added to the snapshot, to `metrics()` and to `tools/refactor_ceilings.json` as a fifteenth key
with `max 0`, and both CI jobs that hold an artifact run it: `lint` against the committed file,
`benchmark-suite` against the one the job just wrote. F3's producer is traced from the consumer at
`run_benchmark_suite.py:1068` to `python/quantrisk/experiments/metadata.py`'s
`working_tree_state()`, and the 21 paths the committed artifact lists are checked against the
suite's own output set. F2 is recorded as a decision: the sweep stays development-only and
`plants_not_rejected_by_their_guard` keeps its `SKIP`, with the contract's reason and the key's
declaration agreeing. F5 is attempted as a real clean-venv wheel reading with
`tools/verify_installed_surface`, and carried as a named precondition if the wheel cannot be built
in this environment. F6 decides `tools/generate_shim_stubs.py` and the two `SKIP` keys, and states
the difference between importability and use against `runtime_reachability`'s `reached_by_neither 0`.

**Deliberately not done in Phase 0.** No source file was edited, no reading added, no ceiling key
changed, no plant added, no CI step added, no census run, no report section written and no push
made. F7 is not re-read here beyond the platform rows above, because its `check:` names the final
tip. Every number above is a reading at `9e35c9c`; the `17df062040b8` in the with-extras row is the
artifact's own revision, not this tip.

**The two pushes.** The first carries the Phase 0 commit, the implementation commit with its guard,
plant, ceiling key, CI step and readings, and the entry attributing the implementation tip's CI;
the second carries this unit's terminal entry only. No third is implied.

---

### 2026-11-09, V5-02 implementation — F4's reading, and the four decisions beside it

**What changed.** Six files, +174 / −3, committed as `3c6092f` on a tree that printed 0 lines
before the commit.

| file | change | why |
|---|---|---|
| `tools/inventory_orphan_code.py` | `artifact_revision()`, `revision_exists()`, `_artifact_path()`; one snapshot row; one metric | F4: a reading that compares the artifact's claim with the tip and can redden |
| `tools/refactor_ceilings.json` | fifteenth key `artifact_revision_gap`, `max 0`, no `may_be_unmeasured` | the reading is adjudicated, not printed |
| `tests/python/test_artifact_metadata.py` | extended `test_every_registry_task_is_aggregated_by_exactly_one_member` with two fixtures | the guard reddens on a forged revision; the counted pair stays 560 / 491 |
| `python/quantrisk/verification/plants.py` | one new plant, and one existing anchor re-keyed from `194/194` to `195/195` | the plant that mutates the revision; the existing plant counts the declared list, which moved |
| `.github/workflows/ci.yml` | `Artifact revision` in `lint`, `Artifact revision at the run tip` in `benchmark-suite` | the two vantages are executed, not inferred |
| `docs/interview_defense.md` | `194/194` → `195/195` | the printed claim is re-derived in the same commit (§4) |

**F4: what the reading refuses, and what it deliberately cannot.** A file cannot carry the SHA of
the commit that contains it, so the reading does not demand equality with `HEAD`. It demands that
the claim be checkable: `git_commit` must be a hexadecimal revision, `git cat-file -e
<revision>^{commit}` must find it in this repository, the artifact's own `provenance` sentence must
name the revision and the binary stamp beside it, and a revision other than the tip must be
attributed to `working_tree_dirty: true` with the paths that made it dirty. Those four refusals are
the gap. The reading therefore cannot be satisfied by a typed SHA that nothing holds, which is the
state both vantages were in when both printed `gap: 0`.

**The two vantages, read rather than averaged.** At `3c6092f` the committed artifact prints
`artifact_revision 17df062040b8`, `tip_being_verified 3c6092fbc8f1`, `matches_tip false`,
`uncommitted_paths 21`, `working_tree_dirty true`, `vantage "committed artifact read by the lint
job; it names an earlier revision and attributes the difference to 21 uncommitted paths"`, `gap 0`.
The benchmark job's fresh artifact names its own run tip, so the same reading returns
`matches_tip true` there. The two jobs now run the same reading and the reading says which vantage
it took.

**The targeted sweeps.** Both were captured after the implementation commit, because the runner
refuses a target that differs from `HEAD` — the first attempt printed `target-already-modified:
these mutation targets differ from HEAD -> docs/interview_defense.md` and exited 2, which is the
instrument working rather than a failure. On the clean tree:
`1/1 planted defects were rejected by their guard.` for
`suite-artifact-claims-a-revision-the-repository-does-not-hold` (`caught`), and the same line for
the re-keyed `docs-command-comment-counts-superseded-plants` (`caught`). The tree printed 0 lines
after each. No full census is claimed here; the final one belongs to V5-03.

**F3, traced from the consumer to the producer.** The V5 prompt's `run_benchmark_suite.py:1075`
is the consumer: `"git_commit": env["git_commit"]`. The producer is
`python/quantrisk/experiments/metadata.py`'s `working_tree_state()`, whose
`_git("status", "--porcelain")` sets `working_tree_dirty = bool(paths)`. The trigger is ordering:
`main()` runs all nineteen members first (`for member in selected`, then `execute(member)`), and
`build()` calls `environment()` on its first line — after the members have rewritten their own
tracked artifacts. The committed artifact's 21 paths confirm it: all nineteen members' `artifact`
paths are among them, and the only two others (`monte_carlo_convergence/results/convergence.csv`,
`variance_reduction/results/variance_by_method.csv`) are companion CSVs those same two members
write. `working_tree_dirty` is therefore the suite observing its own output, not an external
contamination; the marker is accurate and the sentence it feeds is the misleading part. This is the
`check:` F3 asks for — traced and explained with a reading, no code change needed.

**F5, re-run in a clean environment.** A wheel was built from this tree
(`quantrisk-1.9.0-cp312-cp312-macosx_27_0_arm64.whl`, 2,811,622 bytes), installed into a fresh
`uv venv` outside the checkout (five packages: `numpy 2.5.4`, `pandas 3.1.1`,
`python-dateutil 4.0.0`, `quantrisk 1.9.0`, `tzdata 2026.6`), and probed by
`tools.verify_installed_surface`. It printed `identity.module
/private/tmp/qr-v5-venv/lib/python3.12/site-packages/quantrisk/__init__.py`, `prefix
/private/tmp/qr-v5-venv`, `version 1.9.0`; `list.tasks 19` with `tally 19`; `validate.passed 7`;
`study mc_speed` exiting 0 and writing `monte_carlo_speed.json`; `refusal pricing_grid` exiting 1,
naming what it needed, with `empty_directories_left 0`. The tool's own sentence:
`installed surface: identity holds, the list is the registry, one study ran, and the refusal named
what it needed`. This is a V5-tip reading with an asserted module identity, which is F5's first
branch. The `installed_user_identity_mismatch` key keeps its `SKIP` because the collector cannot
build a second environment on the runner; its precondition and the reason now sit beside a
verdict rather than replacing one.

**F2 and F6, decided rather than left open.** F2 takes the second branch §5 offers: the sweep stays
development-only, and `plants_not_rejected_by_their_guard` keeps `SKIP` with `max 0` and
`may_be_unmeasured: true`. The declaration and the reason agree — the sweep writes gitignored
scratch into the checkout and rewrites tracked files one at a time, so a key computed from its
summary line could not fail on the runner that evaluates it. F6 decides all three of its subjects.
`tools/generate_shim_stubs.py` stays a dev-only producer: `tests/python/test_shim_stubs.py`
imports it with `importlib.import_module` and compares the regenerated text, so the *guard* is what
CI runs; invoking the producer on the runner would rewrite eight tracked `.pyi` files, the same
shape as the frozen-evidence rule that keeps `tools.build_evidence_manifest` dev-only.
`runtime_reachability` still reports `reached_by_neither 0`, and the difference it does not measure
is stated here: importability is reachability by *something* — an import, a collection — while use
is a consumer that needs the code to act. A dev-only producer can be reachable and still have no
invoking lane; that is a decision, not a zero. Both `SKIP` keys are named in the deliberately-not-done
list of the Phase 5 report with this reason.

**The counts after the change, and their deltas.**

| quantity | before (Phase 0) | after (`3c6092f`) | delta |
|---|---|---|---|
| plants | 194 | **195** | +1, the revision plant; the `194/194` anchor re-keyed to `195/195` |
| ceiling keys | 14 | **15** | +1 `artifact_revision_gap`, `ok` at 0 |
| `ok` / `SKIP` | 12 / 2 | **13 / 2** | +1 `ok` |
| named CI steps | 32 | **34** | +2, one per vantage |
| formatter corpus | 234 / 234 | **234 / 234** | 0; no new tracked `.md` |
| pytest nodes | 560 / 491 | **560 / 491** | 0; the guard gained fixtures, not nodes |
| manifest entries | 95 | **95** | 0 |
| suite members | 19 / 19 | **19 / 19** | 0; `revision 17df062040b8` unchanged |

**What the gates print at this tip.** `ruff check .` → `All checks passed!`; `ruff format --check .`
→ `234 files already formatted`; `mypy python/quantrisk tools` → `Success: no issues found in 74
source files`; `--check-ceilings` → 15 keys, 13 `ok`, 2 `SKIP`; `--reading docs_rederivation` →
`documents 5`, `derived {19, 19, 195, 95}`, `gap 0`; `--reading lanes_documented_vs_executed` →
`gap 0`, with `tools.inventory_orphan_code` now executed at five steps across two jobs;
`--reading with_extras_census` → `gap 0`; `--reading formatter_census` → both differences empty;
`tools.verify_evidence_manifest` → `Evidence is intact.`; `pytest --collect-only -q` → `560 tests
collected`; `measure_offline_collection` → `491 tests collected`, `collection_errors 0`. A full
local `pytest -q` printed `1 failed, 559 passed in 209.95s`; the single failure is the known
sandbox-only bytecode-cache plant, unchanged from V3 through V4-07 and V5-01.

**How the plant total moved after Phase 0.** Phase 0's row says 194, and that row is not rewritten
(§9). The `docs/interview_defense.md` command comment moved with the declaration, and the plant
that polices that comment was re-keyed in the same commit, so the re-derivation reading and the
sweep both hold at 195. The full 195-plant census is not claimed here.

**The first push.** This entry and the implementation commit are pushed together in the first of
the two pushes authorised in the Phase 0 entry. Its CI is read once the tool reports it and recorded
in the next entry; this file states no outcome for a push that has not happened yet.

---
