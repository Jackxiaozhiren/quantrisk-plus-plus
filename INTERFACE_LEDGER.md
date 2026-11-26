# INTERFACE_LEDGER.md

Interface lane ledger. Opened under scope unit X1. This file is the sole cross-session state
holder for the interface lane; conversational history is not a state store.

All readings below are attributed to a revision, an environment, and a producer. A later
session re-runs Phase 0 rather than trusting a stored entry.

## 0. Scope unit and approvals

Scope unit X1, verbatim, as approved:

> 批准作用域单元 X1：只建立界面 lane 的作用域账本、复核 §3 四项前置条件并填满 liveness 表，不建站点、不改 CLI 输出、不加 plant 或 ceiling key、不做任何发布。

Approval original, verbatim, from the maintainer (developer and authorised approver,
2026-11-15): "完全授权打算推进 X1".

Ruling original, verbatim, 2026-11-15: "我不知道应该如何选择，你有没有推荐的选择，我就按照你的推荐执行".
Under the repository's precedent for an approval that answers a scope-bearing statement, this
ruling is bound to the recommendation recorded in section 6. It is a ruling on interpretation
and on scope boundaries; it does not authorise a new scope unit, and it is not a release approval.

Deliberately outside X1: building any surface; changing CLI output; adding a plant or a ceiling
key; moving a tag; replacing a published asset; any push, deploy, or publication. Each requires
its own case-by-case approval recorded verbatim.

### 0.1 External-action approval

Three mutually exclusive options were put to the maintainer for the push step. Option 1 was
"回复批准原话，由我完成闭环（最推荐）"; option 2 was "你自己本地执行，我只提供步骤"; option 3 was
"暂不推送，维持现状".

Approval original, verbatim: `批准，回复批准原话，由我完成闭环（最推荐）`

It answers option 1, whose text is the following sentence, quoted verbatim:

> 批准作用域单元 X1 的外部动作：以非强制快进方式推送本地提交 `254a9f6`，并推送其后为回填该次
> CI 读数而新增的一个账本提交，合计至多两次 ref 更新；读取该次 CI 运行并把 run、attempt、
> runner、environment 记入 `INTERFACE_LEDGER.md`；不移动 tag、不替换已发布资产、不做发布或部署。

Bounded effect, and nothing beyond it: at most two non-forced updates of `refs/heads/main`;
reading the jobs and logs of the CI run those commits produce; writing this ledger. Excluded:
any tag move, any replacement of a published asset, any release, deploy, or publication, any new
secret or account, any change to the controlled plant inventory or to a ceiling key, any new
scope unit. X1b remains unapproved and unstarted under this approval.

Recursion limit, recorded so that it is a named boundary rather than a silent gap: the backfill
commit produced by this approval is itself verified by a CI run of its own, and that run is not
backfilled, because doing so would require a third ref update which the approval does not cover.
The readings recorded in section 1 belong to the run over `21d88a2` and are attributed to it; the
later run is reported as observed-only, with no claim of being verified in this ledger.

### 0.2 X1b approval

Scope unit X1b, as put to the maintainer verbatim:

> 批准作用域单元 X1b：只新增一个具名受控植物，篡改 manifest 中恰好一条命令的字段形式，证明命令
> 形式守卫转红，恢复后证明转绿，并在阶段报告中具名该机制；不建站点、不改 CLI 输出、不做任何
> 发布。

Approval original, verbatim: `我都听你的，请按照你的思路建议进行`

The maintainer delegates the choice and answers the paragraph above, which is the only proposal
that message contained; under the same precedent as section 0, the approval is recorded together
with the sentence it answers. If the maintainer intends a different scope, this entry is void and
the unit stops before any further commit.

Bounded effect, and nothing beyond it: exactly one new controlled plant in
`python/quantrisk/verification/plants.py`; the count claims that the plant list moves are
re-derived in the same commit that moves them; a phase report in this ledger. Excluded: any second
plant, any ceiling key, any change to CLI output or to a frozen contract, any surface, any tag,
release, deploy or publication. A push is a separate external action and is **not** covered here.

## 1. Phase 0 — prerequisite gate (§3 of INTERFACE_ROADMAP.md)

Revision for every local reading: `e60bba5f303cb74803f671e0a9e00e9f05c3c509`.
Environment for every local reading: maintainer workstation, macOS, read-only shell probes,
2026-11-15. Producer: the named probe in the reading column. Platform readings are attributed
separately.

| # | §3 condition | Reading | Producer | Revision / environment |
|---|---|---|---|---|
| 1 | In-package registry is the single source of truth for runnable studies | `python/quantrisk/experiments/registry.py` present; `registry_parity_mismatch` and `with_extras_census_gap` are ceiling keys with `max 0` and `can_fail_because` | local path and ceiling census | `e60bba5`; workstation; plus platform run `43560290106`, attempt 1, ubuntu-latest and macos-15 |
| 2 | Canonical invocations in the manifest are module-path form, runnable from repository root | 95 manifest entries; 95 of 95 commands in module-path form; 21 distinct command strings | local parse of `evidence/manifest.json` | `e60bba5`; workstation |
| 3 | Installed CLI has a `run` subcommand | CLI parser declares exactly four subcommands: `benchmark`, `demo`, `run`, `validate` | local parse of `python/quantrisk/cli.py` | `e60bba5`; workstation |
| 4 | Command-form guard is ACTIVE with a plant proving it can fail | Guard side ACTIVE: `commands_not_module_path` and `commands_unrunnable_from_the_root` both `max 0` with `can_fail_because`; seven-way classifier; pytest negative control; `ok` on both measured vantages. Plant side: 195 controlled plants, zero touching the manifest command field; full-history search found none | local ceiling census, local AST census of `python/quantrisk/verification/plants.py`, platform logs | `e60bba5`; workstation; platform run `43560290106`, attempt 1 |

Verdict on condition 4: **named VOID**, not "closed". The guard can fail and has a negative
control, but §3 asks for a plant proving it can fail, and no named sample is enumerable in the
controlled inventory. `REFACTOR_LEDGER.md` Phase 5's sentence about "the plant that corrupts one
is rejected" is a historical deflection record, not a currently enumerable named sample.

This verdict is the reading at `e60bba5` and stays as one. Section 10 records the scope unit that
added the missing sample and the readings that retire the VOID at `465735d`; the table above is not
rewritten, because a reading that is silently edited to match a later state is the failure this
ledger exists to prevent.

Two document-attribution gaps are registered, not repaired:

| Gap | Location | Nature |
|---|---|---|
| G-A | `REFACTOR_PROMPT.md` §13 liveness table | L4 still recorded VOID, with no post-Phase-5 update table; §3's Check names this file as the authority |
| G-B | `REFACTOR_LEDGER.md` Phase 5 | L4 recorded ACTIVE satisfied in a different file from the one §3's Check designates |

Per §3, until condition 4 holds this lane runs facts and feasibility only and builds no surface.
X1 therefore exits with a named VOID and two named attribution gaps. It does not exit with
"prerequisites satisfied".

### 1.1 Platform verification of the pushed tip

Both commits were appended through the Git Data API with a non-forced fast-forward
(`force: false`). Every blob, tree and commit SHA was verified against its local value before the
ref moved, and the ref moved only after both commits matched exactly. This is the first of the
two ref updates the approval in section 0.1 allows.

| Field | Value |
|---|---|
| Run | `43718835599` |
| Attempt | 1 |
| Head revision | `21d88a2268bd611d0bd75926b9657dacf0233400` |
| Event | `push` |
| Conclusion | `success`; six of six jobs `success`, no failed step |
| Window | 2026-11-15T13:24:24Z to 2026-11-15T13:42:57Z |

| Job | Runner label | Duration | Conclusion |
|---|---|---|---|
| macOS native C++ and Python parity | `macos-15` | 3m50s | success |
| Mutation census in a detached worktree | `ubuntu-latest` | 18m29s | success |
| Installed wheel surface in a clean environment | `ubuntu-latest` | 1m38s | success |
| Benchmark suite against live oracles | `ubuntu-latest` | 8m39s | success |
| Configure, build, C++ tests, Python tests | `ubuntu-latest` | 7m53s | success |
| Format and static checks | `ubuntu-latest` | 1m23s | success |

Readings, each attributed to the job that printed it. No reading is carried over from an earlier
run.

| Reading | Value | Job | Environment |
|---|---|---|---|
| Python test suite | `490 passed, 5 skipped in 238.89s` | build-and-test | `ubuntu-latest`, fully offline |
| Final-tip attestation | `PASS: V9_LEDGER.md attests 5ec3fabe… as a strict ancestor of 21d88a2268bd, 195 caught of 195 declared` | build-and-test | `ubuntu-latest`, `fetch-depth: 0` |
| Benchmark suite | `19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 326.7s total` | benchmark-suite | `ubuntu-latest`, live oracles |
| Installed surface | identity holds; `revision 21d88a2…`, `version 1.9.0`, venv outside the checkout | installed-surface | `ubuntu-latest`, clean venv |
| Mutation census | `195 declared = 194 measurable here + 1 environment-blind` | mutation-census | `ubuntu-latest`, detached worktree |
| Formatter corpus | `252 files already formatted` | lint | `ubuntu-latest` |
| Lane contract | `lanes_documented_vs_executed_gap: 0` | mutation-census | `ubuntu-latest` |
| Docs re-derivation | `gap: 0`; derived 95 manifest artifacts, 195 plants, 19 registry tasks, 19 suite members, over 5 documents | lint and mutation-census | `ubuntu-latest` |
| Artifact revision | `gap: 0`, `pin_holds: true` against the pinned `17df062040b8` | lint and mutation-census | `ubuntu-latest` |

Ceiling adjudication by vantage. This is the exact shape that made `13 ok / 2 SKIP` and
`14 ok / 1 SKIP` look like a contradiction in V12: each of the three jobs prints all fifteen keys
and marks SKIP the ones measured on another runner.

| Vantage | Keys printed | `ok` | `SKIP` |
|---|---|---|---|
| Format and static checks | 15 | 13 | `plants_not_rejected_by_their_guard`, `installed_user_identity_mismatch` |
| Mutation census in a detached worktree | 15 | 14 | `installed_user_identity_mismatch` |
| Installed wheel surface in a clean environment | 15 | 14 | `plants_not_rejected_by_their_guard` |

Two properties of this run are pre-existing vantage facts rather than effects of this approval,
and are checked against run `43560290106` so they cannot be mistaken for regressions:
`artifact_revision` reports `working_tree_dirty: true` with `uncommitted_paths: 21` in both the
shallow and the full-history vantage, identical to the V13 run; and the shallow lint vantage
reports `object_present: false` with a skipped object check, which is why it declares itself
shallow instead of claiming an ancestry it cannot see.

## 2. Liveness table (I-L1 … I-L8)

Filled from readings, not by editing prose. A law without an executable target is VOID and may
not be cited to justify or block work.

| # | State | Predicate or reason it is VOID |
|---|---|---|
| I-L1 | VOID | §3 condition 4 is named VOID; no resolvability reading with a named plant to bind a target to |
| I-L2 | Filled — both halves | `python -m quantrisk.interface.site` builds pages from committed artifacts, and `test_the_generator_source_contains_no_numeric_literal` plus plant `site-source-carries-a-figure-of-its-own` make the source scan falsifiable at `aafb707`. The drift half is filled at `28727f4` by `python -m quantrisk.interface.drift --check` against the committed `build/site.lock`, with guard `test_the_committed_lock_detects_a_figure_that_drifted_in_an_artifact` and plant `site-lock-catches-a-manifest-silent-figure-change` proving it reddens (section 17) |
| I-L3 | Filled | X5 published a static surface; `test_published_pages_carry_no_request_execution_path` scans every generated page for scripts, handlers, fetch/XHR and external URLs (and `test_generated_markup_source_has_no_script_template` scans the source template), with plant `site-page-gains-a-request-execution-path` reddening both by injecting a `<script>` into `DOCUMENT_HEAD` (section 30) |
| I-L4 | Filled (cost basis bounded) | X5 configured the free-tier publish; `test_the_publish_chain_stays_on_the_free_tier` names the no-cost first-party action set and refuses stored secrets, with plant `publish-chain-adds-a-paid-action` reddening on a third-party paid action. The cost basis is CI minutes and Pages free tier only; AI-token cost (O11) is adjudicated at section 53 as a task-side cost outside the project-side basis, so the project side stays at zero monetary and carrying cost with no account or secret (sections 30, 53) |
| I-L5 | Filled | X11 added a lint-job step that enters a fresh network namespace with `sudo unshare -n`, proves the isolation with a negative socket probe that must fail, then rebuilds the site with `quantrisk.interface.drift --check` against the committed `build/site.lock`. Platform run `45027396972` (attempt 1) printed `OFFLINE PROBE PASS` and `OFFLINE BUILD PASS` with the probe intact, so a build with the network actually down now exists; the in-process `test_the_build_opens_no_socket` remains as a second check. The read-only `offline.audit(root)` re-derives the step's markers, the site generator's network-free import closure and the lock digest, guarded by `test_the_offline_build_facts_are_readable_and_falsifiable` and reddened by the plant `offline-step-drops-its-negative-probe` (`ok caught` on the runner census). No OS-level offline claim is made from the macOS host, where the mechanism is unavailable (sections 49–52) |
| I-L6 | Filled (module path, not HTTP) | `python -m quantrisk.interface.provenance --resolve --json` is the machine-readable surface: `test_the_machine_readable_surface_is_module_path_and_keeps_provenance` requires value + command + revision + digest together and an AST check that no HTTP/service framework is imported, with plant `machine-readable-surface-drops-a-provenance-field` reddening when a field is dropped. No service layer was added (section 30) |
| I-L7 | VOID | Claim-inventory guards belong to the refactor lane; this lane has added no README or site claim, so no I-lane target exists |
| I-L8 | Filled | X10 ran the report-wide audit the roadmap line 302 names: `claimmap.audit()` re-derives each H's quoted figure from its committed record (H1 price from the cold-start record, H2 coverage from `provenance.completeness()`, H3 digest from `build/site.lock`, H4 budget line from `cost.audit()`) and checks it is still present in that H's section 3 claim; all four map, none unmapped or refused. Guard `test_every_h_value_claim_maps_to_its_recorded_run` re-derives independently and is reddened by plant `claim-map-drops-a-recorded-figure-from-the-report` (sections 45–46) |

Note: the refactor lane's L4 ACTIVE record and the interface lane's I-L1 … I-L8 are different
rail sets. Neither may be cited as evidence for the other.

## 3. H1–H4 measurement ledger

The maintainer confirmed the measurement environment and producers are available. Availability
is not a measurement. No measurement was run under X1, which contains no measurement phase.

| Hypothesis | Value | Producer | Environment | Status |
|---|---|---|---|---|
| H1 cold-start reproduction | A wheel run by one command: `quantrisk run mc_speed --out cold-start-out`, executed in 0.61 s from an empty working directory outside the checkout, reproducing the published artifact's five deterministic fields (`analytic_reference_price` 11.123761928058133, `measured_prices`, `reported_standard_errors`, `paths_per_run`, `option`) exactly; the benchmark's wall-clock columns are explicitly not compared (X9 §41–§42) | `tools/cold_start.py` builds the wheel, creates a fresh venv and an empty cwd outside the checkout, runs exactly one command, and writes `tools/cold_start_record.json`; the read-only `coldstart.audit()` exposes that record, guarded by `test_the_cold_start_records_one_command_from_an_empty_directory_outside_the_checkout`, which re-derives the equality from the committed artifact and is reddened by plant `cold-start-record-quotes-a-price-the-published-artifact-does-not-hold` | development machine (macOS 27.2.1 arm64, Python 3.12.14); venv and cwd under the system temp directory, both outside the checkout; wheel built from this tree (17.5 s) and installed from the index (210.8 s on a cold cache, 0.1 s warm); the producer reads no network and opens no socket | Measured at X9: fresh venv, neutral cwd, one command, zero repo checkout, zero prior file names, both clocks positive. No runner reading claimed: no CI step runs this tool |
| H2 provenance completeness | Complete over the published-value set: 10/10 headline-bearing registry artifacts resolve with value + command + revision + digest together; 0 named refusals and 0 incomplete tuples (X7 §33–§34) | `provenance.completeness()` read-only producer over the committed manifest and registry (X7), guarded by `test_the_published_value_set_resolves_with_full_provenance`, which declares the ceiling and is reddened by plant `a-published-value-loses-its-digest` erasing one recorded digest; the denominator is the published-value set, not all 95 manifest artifacts — the 9 benchmark/analysis artifacts with no headline are named-refused by `resolve()` by design and are not provenance gaps | development machine, committed checkout at `e48c4f8` (producer reads no network, opens no socket); producer + guard local, plant falsification in the full census | Measured at X7: coverage 10/10, 0 refused, 0 incomplete; the metric is falsifiable (digest erase drops resolved off published). The guard executed on the runner as plant `a-published-value-loses-its-digest`'s target and reddened there (`ok caught`, section 36); the producer's own output is printed by no CI step, so the values above remain development-side |
| H3 zero page drift | Zero: live index SHA-256 `692db228336617a0663446bf4181d47a4b63204d9ff156d92d852b25715d25c4` == committed `build/site.lock` `index.html` `page_sha256`, byte-for-byte | X5 section 28's producer curl + SHA-256 of the live Pages response; `python -m quantrisk.interface.drift --check` + committed `build/site.lock` is the gate behind that URL | development machine over HTTPS (live URL read, not a CI network call); gate local and runner | Mechanism proven falsifiable at `28727f4`; the published-surface value registered from X5 section 28 at `d040872` (section 30) |
| H4 zero cost | Zero: every `uses:` reference across all seven jobs in `ci.yml` is inside the free first-party set (0 paid actions), 0 billed runners, 0 stored secrets; the host is GitHub Pages from `actions/deploy-pages` with `pages: write` / `id-token: write` / the `github-pages` environment and no `CNAME` file; the report asserts `Total monetary cost of building and validating it: $0.` exactly once (`README.md` line 31) (X8 §37–§38) | Read-only `cost.audit()` producer over the committed workflow and README (X8), guarded by `test_the_zero_cost_claim_is_read_from_the_publish_surface_and_the_report`, which declares the ceiling and is reddened by plant `report-drops-its-zero-cost-budget-line` editing the README sentence; the producer returns three evidence blocks, never a computed literal, so the reading cannot be satisfied by repeating the policy — the L12 shape `external_dependencies()` records | development machine, committed checkout (producer reads no network, opens no socket); guard local, plant falsification in the full census | Measured at X8: paid set empty, billed runners empty, stored secret false, free static tier true, custom domain false, budget line exactly once and carrying `$0`. The guard executed on the runner as plant `report-drops-its-zero-cost-budget-line`'s target and reddened there (`ok caught`, section 40); the producer's own output is printed by no CI step, so the values above remain development-side |

A hypothesis that later turns out false is a result and is recorded as one.

## 4. Rulings on the business-scenario conflicts (K1–K3)

These are interpretations, not scope changes. No non-goal is unlocked.

| # | Ruling | Effect |
|---|---|---|
| K1 | AI token consumption is task-side cost, recorded separately; project-side cost stays on the E09 zero-dollar basis; no account or key is introduced into the project | The user's "everything else must be free" is honoured without rewriting the project's cost contract |
| K2 | Target user is recorded as "undefined"; U1–U5 are not cited as an ordering basis for this lane; the exclusion of retail investors remains in force until a measured need exists | No value hypothesis is bound to an unnamed group |
| K3 | "No hard exclusions" means no additional business-side exclusions; it does not repeal A6/A7, IN1–IN5, C1.2, or C1.3; S01–S03 stay pending | The report's hard constraints remain valid rather than being voided |
| K4 | No time constraint; milestones carry no dates and ordering follows prerequisites and falsifiability | No schedule pressure enters the ordering |

## 5. Ruling on S05

S05 asked whether X1 may add one controlled named plant to convert condition 4 from named VOID
to an enumerable falsification proof.

Ruling: **not approved inside X1**. The X1 scope sentence explicitly forbids adding a plant or a
ceiling key, and that sentence is part of the approval. Adding a plant changes the 195-plant
controlled inventory, the runner-side census, the formatter corpus, and the lane-contract
surface; it is a distinct scope unit with its own measurement obligations, not a clause inside
X1.

Deferred unit, not started: X1b — "add exactly one named controlled plant that corrupts one
manifest command field, prove the command-form guard turns red, restore, prove green, and name
the mechanism in a phase report". X1b requires its own scope-bearing approval recorded verbatim.
Until X1b is approved and measured, P03–P05 remain conditional recommendations.

## 6. Recommendation adopted and ordering

The recommendation adopted by the ruling in section 0 is the narrow path: keep X1's original
scope, do not expand scope, do not unlock any non-goal, do not publish, do not measure H1–H4
inside X1, and defer the named plant to X1b. It is the only path that requires no new approval
and can therefore start immediately; expanding X1 would require a further scope-bearing
sentence and would delay all work.

Ordering, by prerequisite and falsifiability only: X1 (this ledger, Phase 0, liveness, named
gaps) → X1b (named plant, separate approval) → later units for the generator, drift gate,
static publish, and read-only machine surface. No date is attached.

## 7. Definition of Done status

| # | DoD item | Status |
|---|---|---|
| 1 | Phase 0 readings recorded; §3 satisfied or lane stopped at Phase 1 with a written reason | Done-lite: readings recorded, §3 condition 4 named VOID, no surface built |
| 1a | Platform verification of the X1 commits | Done: run `43718835599`, attempt 1, six of six jobs success; readings in section 1.1 |
| 1b | X1b: one named plant proving the command-form guard fails, restore proving green, mechanism named in a phase report | Done: plant `manifest-records-a-command-that-is-not-a-module-invocation`; red `1 failed`, green `1 passed`, census `196/196` at `465735d`; runner-side `ok caught` in run `43732028206`; reports in sections 10 and 11.1 |
| 1c | X2: generator emits artifact-bound pages with provenance; source scan has a named falsifying plant; no deploy, drift gate or new key | Done at `aafb707` locally and re-verified at `7971299`; section 13 holds the development-side readings, section 15 the first platform run's failure and its lint fix |
| 1d | X3: a page-level drift gate with a committed baseline and a falsifying plant; no deploy, new key or zero-literal-rule change | Done at `28727f4`: `198/198`, single-plant red/green and all readings in section 17; no platform reading because section 16 excludes a push |
| 1e | X4: G-A/G-B attribution gaps closed in the designated file; read-only provenance surface with a named falsifying plant; no CLI subcommand, deploy or new key | Done at `25aed30`: `199/199`, single-plant red/green and all readings in section 21; no platform reading because section 20 excludes a push |
| 2 | I1 CLI provenance surface | Done as a `-m` module under X4 scope A: `python -m quantrisk.interface.provenance --list/--resolve` answers provenance offline with a guarded output; the literal `quantrisk` subcommand form was declined in X4 option B and stays outside the frozen four-subcommand contract; readings in section 21 |
| 3 | I2 generator, drift gate proven falsifiable, free-tier CI publish, offline build | Filled: generator done at `aafb707` and drift gate proven falsifiable at `28727f4` (sections 13/17); X5's gated CI `deploy` job ran on the runner in run `44292891046` (seven-job success) and published the gate-verified bytes to `https://jackxiaozhiren.github.io/quantrisk-plus-plus/`, with a live-URL reading whose SHA equals the locked `index.html` (section 28); X11 executed the site build with the network actually down in run `45027396972`, printing `OFFLINE PROBE PASS` and `OFFLINE BUILD PASS` against the committed lock, closing the last sub-item (I-L5, section 2, sections 49–52) |
| 4 | I3 value and provenance returned together, refusals name the gap | Done at `25aed30`: `resolve()` returns value + command + revision + digest together and refuses by name on any missing element; plant `provenance-erases-a-recorded-command` proves the guard fails; readings in section 21 |
| 5 | H1–H4 measured, liveness filled, deliberately-not-done list | Filled for the H set and the value-mapping law: H3 registered with a platform live-SHA value (section 28/30), H2 measured complete at X7 (10/10, section 33/34), H4 measured zero at X8 (sections 37/38), H1 measured at X9 (one command, 0.611 s, five published fields reproduced, sections 41/42), so all four H values exist; X10 ran the report-wide claim-to-run audit and all four claims map to their committed records (section 45/46). Liveness I-L3/L4/L6 filled from the published surface (section 30), I-L8 filled at X10, I-L5 filled at X11 with a true network-down build on the runner (sections 49–52); deliberately-not-done list below |

## 8. Deliberately not done

| Item | Reason |
|---|---|
| Any site, generator, drift gate, or deployment | §3 condition 4 is named VOID; X1 scope forbids building a surface |
| Any new plant or ceiling key | X1 scope forbids it; deferred to X1b with its own approval |
| Any edit to `REFACTOR_PROMPT.md` or `REFACTOR_LEDGER.md` | Those belong to the refactor rail set; the two attribution gaps are registered, not repaired |
| Any change to CLI output, public API names, or frozen contracts | X1 scope forbids it |
| Any H1–H4 measurement | No measurement phase in X1; availability is not a reading |
| Any tag, release, or deploy | Case-by-case external approval required; none obtained. The one push performed is recorded in section 0.1 and is bounded to two non-forced ref updates |
| Any rewrite of the V9 historical attestation | Attestation is judged as history; no present-day count comparison is added |

## 9. Review checklist for the next session

1. Re-run Phase 0 on the current tree; do not trust section 1 as stored.
2. Re-check that `.workbuddy/` remains locally ignored; a new untracked Markdown file changes
   the formatter census corpus and must be accompanied by a fresh two-sided census reading.
3. Re-run the formatter census and the claim inventory after any new tracked file.
4. Confirm section 2's VOID entries before citing any law.
5. Attribute every platform reading to run, attempt, runner, and environment.
6. Do not treat a green gate as proof; name the planted sample that made it turn red.

## 10. X1b phase report — the plant that names the command-form guard

Scope, from section 0.2: exactly one named controlled plant that corrupts one manifest command
field, prove the command-form guard turns red, restore, prove green, and name the mechanism here.
Four commits, and nothing outside that shape:

| Commit | Change |
|---|---|
| `1ec1adb` | this ledger: the scope unit and the approval, verbatim |
| `c983da1` | `python/quantrisk/verification/plants.py`: the plant itself |
| `0a426c0` | `docs/interview_defense.md`: the sweep annotation it prints, 195 → 196 |
| `465735d` | `plants.py`: the anchor of `docs-command-comment-counts-superseded-plants`, which is the string `# 196/196 planted defects rejected` |

The last two are not scope creep; they are the count's blast radius, and both were found by a gate
turning red rather than by searching for the number. Adding a plant moves a count that one document
prints and one existing plant anchors on: the docs re-derivation reading went to `gap: 1` until the
document moved, and the anchored plant reported `anchor-not-unique` until its anchor moved with the
count. A green full census over a count that no longer matches its readers is exactly the reading
section 9's sixth line forbids, so both gates were obeyed instead of silenced.

### 10.1 The mechanism, named

| Field | Value |
|---|---|
| Plant | `manifest-records-a-command-that-is-not-a-module-invocation`, `kind` `prose` |
| Target | `evidence/manifest.json`, one `generated_by_command` |
| Anchor | `uv run python -m quantrisk.benchmarks.quantlib.pricing_validation` |
| Replacement | `uv run python python/quantrisk/benchmarks/quantlib/pricing_validation.py` |
| Guard | `tests/python/test_artifact_metadata.py::test_every_manifest_command_resolves_as_a_module_without_being_run` |
| Mechanism | the guard tests the `uv run python -m ` prefix, then resolves the module name with `importlib.util.find_spec` without executing it; the legacy file spelling fails the prefix test, so the entry is reported as "not a module invocation" |
| Ceiling keys | `commands_not_module_path` and `commands_unrunnable_from_the_root`, both `max 0` with `can_fail_because` |

The spelling is the residue condition 4 names. A module name that does not import would also redden,
since the guard resolves rather than runs, but the file form is the shape a reader is most likely to
paste back out of the manifest, and it is the one the two ceiling keys count.

### 10.2 Readings

Every reading below is development-side, revision `465735d63a340c42705257d8f5faf409dd3dd5ef`, on
the maintainer workstation, 2026-11-15. A detached worktree at that revision
(`/tmp/qr-x1b-census`) is the vantage for the sweep; the checkout under evaluation was watched and
never written. No CI run exists for this revision: a push is excluded by the approval in
section 0.2, so nothing here is a platform reading. Section 11.1 later records the platform reading
for the same revision, which is a separate table precisely because it is a different vantage; the
numbers below stay attributed to the workstation that produced them.

| Reading | Value | Producer |
|---|---|---|
| Single-plant red | `FAILED …::test_every_manifest_command_resolves_as_a_module_without_being_run`, `1 failed in 0.49s` | `runner --only manifest-records-a-command-that-is-not-a-module-invocation --verbose` |
| Single-plant green after restore | `1 passed in 0.58s`; verdict `caught`; `1/1 planted defects were rejected by their guard` | the same run |
| Full census | `196/196 planted defects were rejected by their guard` | `runner --all --verdict-out /tmp/sweep_verdict_x1b2.json` |
| Verdict record | `declared 196`, `ran 196`, `caught 196`, `non_caught []`, `unmeasurable []` | `quantrisk-sweep-verdict/1` json |
| The watched checkout | `checkout_status_before: ''`, `checkout_status_after: ''` | the same verdict |
| Plant inventory | `runner --list` prints 196 lines; `plant_liveness` reports `declared_plants: 196` | local |
| Docs re-derivation | `gap: 0`; derived `plants: 196` over 5 documents; `mismatches: []` | `tools.inventory_orphan_code --reading docs_rederivation` |
| Ceiling census, census vantage | 15 keys, 14 `ok`, 1 `SKIP` (`installed_user_identity_mismatch`); `plants_not_rejected_by_their_guard: 0` | `--check-ceilings`, after the verdict is placed where that key reads it |
| Ceiling census, lint vantage | 15 keys, 13 `ok`, 2 `SKIP` (both lane-written verdicts absent) | `--check-ceilings` before the verdict was placed |
| Python tests | `1 failed, 559 passed in 153.91s` | `pytest -q --basetemp=<private>` |

Two notes that belong beside those numbers rather than in a footnote. The `14 ok / 1 SKIP` reading
is not a new claim about the repository: it reproduces the mutation-census vantage in section 1.1's
table, and the same tree reports `13 ok / 2 SKIP` until the verdict is copied to
`build/sweep_verdict.json`, because that key declares its precondition absent where the lane did
not run. Placing the verdict is a vantage restoration, not a second measurement, and the key should
not be read as one: `sweep_gap` checks escapes, the count's reconciliation with `runner --list`, the
ran-equals-declared identity and the two checkout readings, and it does not compare the verdict's
revision with the tip, so what it certifies here is the record it was handed, whose own `revision`
field names `465735d`. The one failing test is
`test_a_restored_plant_cannot_be_read_back_from_a_stale_bytecode_cache`, which needs a `__pycache__`
the sandbox shell does not write (`PYTHONDONTWRITEBYTECODE=1`); it is the same single local failure
V13 recorded, CI's own reading for the previous tip is `490 passed, 5 skipped`, and it is not a
regression from this unit.

### 10.3 What this closes, and what it leaves open

Condition 4 of §3 has two halves. The guard half was already ACTIVE when X1 read it. The plant half
had no enumerable sample, which is why section 1 could only record a **named VOID**. From this
revision that half is an enumerable sample with a red reading and a green reading on the same
command field, so condition 4 is satisfied at `465735d` and no longer names a VOID. Section 1's
table is the `e60bba5` reading and is not rewritten; this section is where the change of state is
recorded.

Deliberately left open:

| Item | Why it stays open |
|---|---|
| The two attribution gaps G-A and G-B | They live in `REFACTOR_PROMPT.md` and `REFACTOR_LEDGER.md`; X1b's scope excludes both files, and a repair belongs to the refactor rail set, not to this lane |
| A platform reading for `465735d` | The approval excludes a push. The census job runs the same sweep, so the runner-side reading arrives with the next push that this lane is authorised to make, without new work |
| §3's other three conditions | Read at `e60bba5` and untouched by this unit; nothing here re-derives them |
| X1's surface decisions | Condition 4 is now satisfied, but building the generator, the drift gate or the publish step is a separate scope unit with its own approval |

## 11. X1b external action — the push that buys a platform reading

Section 0.2 excludes a push, so the five commits X1b produced sat on one workstation and section 10
could only be a development-side reading. The question put to the maintainer, verbatim:

> 本地 main 现领先平台 5 个提交（X1b 的植物 + 账本 §10 阶段报告），全部未推送。平台读数要不要取？
> 1. 推送并回填（最推荐）：用 `build/api_push.py` 非强制快进推送 5 个提交，读 CI 六作业（census
> 作业会在 runner 上跑同一套 196 植物），再把平台读数回填成第二个提交。代价：两次 ref 更新、
> 约 20–30 分钟 CI。
> 2. 只推送不回填：一次 ref 更新，run 会跑完但账本不引用它的读数。
> 3. 暂不推送：维持现状，5 个提交留在本地。

Approval original, verbatim: `推送并回填（最推荐）`

Bounded effect, and nothing beyond it: at most two non-forced updates of `refs/heads/main`;
reading the jobs and logs of the runs those commits produce; writing this ledger. Excluded: any tag
move, any release, deploy or publication, any new secret or account, any change to the plant
inventory or to a ceiling key, any new scope unit.

Recursion limit, recorded for the same reason as section 0.1's: the backfill commit is itself
verified by a run of its own, and that run is not backfilled, because a third ref update is outside
this approval. Section 11.1's readings belong to the run over the six-commit series; the later run
is reported as observed-only.

### 11.1 Platform verification of the X1b commits

Six commits were appended through the Git Data API with a non-forced fast-forward
(`force: false`). Every blob, tree and commit SHA was verified against its local value before the
ref moved, and the ref moved only after all six matched exactly. This is the first of the two ref
updates section 11 allows. No tag moved: `v1.9.0` is still the most recent.

| Field | Value |
|---|---|
| Run | `43732028206` |
| Attempt | 1 |
| Head revision | `e984a55c32632b089f62dbecb9e94ae8e960e2da` |
| Event | `push` |
| Conclusion | `success`; six of six jobs `success`, no failed step |
| Window | 2026-11-15T15:49:36Z to 2026-11-15T16:08:41Z |

| Job | Runner label | Duration | Conclusion |
|---|---|---|---|
| macOS native C++ and Python parity | `macos-15` | 3m56s | success |
| Mutation census in a detached worktree | `ubuntu-latest` | 19m01s | success |
| Installed wheel surface in a clean environment | `ubuntu-latest` | 1m43s | success |
| Benchmark suite against live oracles | `ubuntu-latest` | 10m05s | success |
| Configure, build, C++ tests, Python tests | `ubuntu-latest` | 4m55s | success |
| Format and static checks | `ubuntu-latest` | 1m11s | success |

Readings, each attributed to the job that printed it. No reading is carried over from an earlier
run, and none is carried over from section 10: those are the workstation's.

| Reading | Value | Job | Environment |
|---|---|---|---|
| Python test suite | `490 passed, 5 skipped in 135.19s` | build-and-test | `ubuntu-latest`, fully offline |
| Final-tip attestation | `PASS: V9_LEDGER.md attests 5ec3fabe… as a strict ancestor of e984a55c3263, 195 caught of 195 declared` | build-and-test | `ubuntu-latest`, `fetch-depth: 0` |
| Census declaration | `196 declared = 195 measurable here + 1 environment-blind` | mutation-census | `ubuntu-latest`, detached worktree |
| Census verdict | `195/195 planted defects were rejected by their guard` | mutation-census | `ubuntu-latest`, detached worktree |
| The new plant, on a runner | `ok caught manifest-records-a-command-that-is-not-a-module-invocation` | mutation-census | `ubuntu-latest`, detached worktree |
| Census verdict record | `declared 195`, `ran 195`, `caught 195`, `revision e984a55c3263`, both checkout readings empty | mutation-census | `ubuntu-latest` |
| Benchmark suite | `19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 383.8s` | benchmark-suite | `ubuntu-latest`, live oracles |
| Installed surface | identity holds; `revision e984a55c3263`, `version 1.9.0`, venv at `_temp/installed-venv` | installed-surface | `ubuntu-latest`, clean venv |
| Formatter corpus | `252 files already formatted`; `reported_total 252`, `tracked_formattable 252`, `walked_formattable 252` | lint | `ubuntu-latest` |
| Ceiling census, lint | 15 keys, 13 `ok`, 2 `SKIP`; `commands_not_module_path: 0`, `commands_unrunnable_from_the_root: 0` | lint | `ubuntu-latest` |
| Ceiling census, census | `plants_not_rejected_by_their_guard: 0`, `lanes_documented_vs_executed_gap: 0` | mutation-census | `ubuntu-latest` |
| Docs re-derivation | `gap: 0`; derived 95 manifest artifacts, 196 plants, 19 registry tasks, 19 suite members, over 5 documents | lint and mutation-census | `ubuntu-latest` |
| Evidence manifest | `0 MISSING`; `Evidence is intact.` | lint | `ubuntu-latest` |

Three things this run settles that a workstation cannot.

**The plant is caught by something other than its author's machine.** Section 10's red and green
readings came from a worktree on the same host; the runner reproduced `caught` for the same
identifier with the same guard name in the same log line, so the sample is not an artifact of one
environment.

**The environment-blind plant is named, and it is not the new one.**
`report-source-edited-without-a-rebuild-seen-from-the-render` is the single declared blind sample:
the re-render guard needs the pdfTeX that typeset `paper/technical_report.pdf`, the runner carries
1.40.25 and `paper/technical_report.build.json` records 1.40.29. The census therefore declares 196
and measures 195 there, while the workstation measured 196, which is why section 10.2 has no
environment-blind entry and this table does.

**The historical attestation did not move, by design.** It still prints `195 caught of 195 declared`
at a tip that declares 196 plants. That is V13's ruling holding: the attestation is judged as
history, and a present-day count check bolted onto it would make it a different claim rather than a
stronger one.

### 11.2 What the second ref update will and will not buy

The backfill commit that carries these readings is verified by a run of its own, and that run is
observed-only under section 11's recursion limit: a third ref update is outside the approval. So
section 11's second update closes the platform record for the six-commit series, and the tip that
holds that record has no run of its own that this ledger claims.

## 12. Scope unit X2 — the generator, and nothing around it

X1b's plant satisfies §3 condition 4, so the sentence in section 1 that kept this lane at "facts and
feasibility only" no longer holds and a surface unit is admissible. Phase 3 of
`INTERFACE_ROADMAP.md` is the generator, and Phase 4 (deploy plus the drift gate) is where a
deployed surface would come from; X2 takes Phase 3's mechanism and leaves the deployment alone.

Scope unit X2, as put to the maintainer verbatim, with the alternatives that were declined beside it:

> **方案 A（推荐）** 批准作用域单元 X2：只新增一个包内生成器，以
> `python -m quantrisk.interface.site --out <目录>` 从已提交 artifact 与 `evidence/manifest.json`
> 生成 study 页与一个索引页，每页带 provenance 块（artifact 路径、sha256、记录的 canonical 命令、
> 生成时间），页面上每个数字必须在构建时从 artifact 读入而非写死在源码；同时新增一个守卫扫描生成器
> 源码中的证据型数字字面量（只允许排版常量），并新增一个受控植物证明该守卫会转红；不建部署、不做漂移
> 门禁、不新增天花板键、不改 CLI 子命令、不新增依赖，产物只写被忽略的 `build/site/`。

Approval original, verbatim: `方案 A（推荐）`

The two declined alternatives are recorded so the boundary is a decision rather than an omission:
**B** would have taken Phase 3's whole page set in one unit (study, findings and matrix pages), on
the grounds that a wider surface needs more than one plant to prove; **C** would have added a
`site_pages_without_provenance` ceiling key, on the grounds that a reading CI cannot see is a
reading nobody re-checks, at the cost of moving the ceiling inventory from 15 keys to 16 and every
vantage narration that prints it.

Bounded effect, and nothing beyond it: one new in-package generator reachable as
`python -m quantrisk.interface.site`; the pages it emits under an ignored output directory; one
pytest guard that scans the generator's own source for evidence-shaped numeric literals; one
controlled plant proving that guard can fail; the count claims that plant moves, re-derived in the
same series. Excluded: any deployment or hosting configuration, any drift gate, any new ceiling key,
any change to CLI subcommands or to a frozen contract, any new dependency, any committed build
output, any README or front-page rewrite. A push is a separate external action and is **not**
covered here.

Three constraints are part of the scope because the readings that would break are already measured:

| Constraint | Reading it would break |
|---|---|
| The generator is not a CLI subcommand | §3 condition 3 counts exactly four subcommands: `benchmark`, `demo`, `run`, `validate` |
| The generator is imported by a test | `runtime_reachability_gap` is the residual of files dead to the parser, the import probe and pytest collection |
| `stdlib` only, no new dependency | `external_dependencies_added` sits at `max 0` |

Known blast radius, from X1b's own experience rather than from searching: a 197th plant moves the
`196/196` annotation in `docs/interview_defense.md` and the anchor of
`docs-command-comment-counts-superseded-plants`, and both turn red until re-derived. X2 treats those
as part of its own change, not as surprises.

## 13. X2 phase report — a generator, and the two red censuses it earned

Section 12 holds the scope sentence and the approval original. A push is excluded there, so every
reading in this section is development-side and no platform run is claimed for this tip. Six
commits make the unit: `df0d185` scope and approval; `9dc8c3b` generator, source guard and plant;
`403b346` the no-socket build test; `4fde6d9` the count and layout re-derivation; `2b3b3ab` the
report rebuild and claim-census gold move; `aafb707` the environment-independent form of the
test-count guard.

### 13.1 The mechanism and the sample that can break it

`python -m quantrisk.interface.site --out <dir>` reads the registered studies and
`evidence/manifest.json`, and writes one page per study plus an index into the ignored
`build/site/`. A page is refused when its artifact is absent from the manifest, when its bytes no
longer hash to the frozen digest, or when the manifest records no command; no figure is typed into
the generator, `generated_utc` comes from the artifact rather than the clock, and two builds of one
tree are byte-identical. It is not a CLI subcommand — §3 condition 3 counts exactly four — and it
imports only the standard library, so neither `commands_not_module_path` nor
`external_dependencies_added` moves.

The guard `test_the_generator_source_contains_no_numeric_literal` parses the tracked module with
`ast`, checks that the imported module *is* that tracked file (a plant must not be masked by an
installed copy), verifies a known literal is found by the scan, and requires zero literals in the
source. The declared allowance `LAYOUT_NUMBERS` is empty; widening it is a visible design change
rather than an accident. The plant `site-source-carries-a-figure-of-its-own` types a comfortable
figure into that source: single-plant red `1 failed in 0.49s`, after restore `1 passed in 0.29s` at
`9dc8c3b`, verdict `caught`. `test_the_build_opens_no_socket` replaces three socket entry points
with refusals for a full build, which is narrower than "build with the network down" and is why
I-L5 stays partial.

### 13.2 Two red censuses before the green one

The first full census, at `403b346`, returned `188/197`. All nine non-caught rows were
`tree-did-not-recover`, and all nine named one of three guards whose *inputs* X2 had moved: eight
new tests took the collected pair from 560/491 to 568/499, and the new package
`python/quantrisk/interface/` was missing from `docs/architecture.md` §5. The guard failures were
already present on the restored tree; the plants did not cause them, they revealed them. An
intermediate run at `4fde6d9` was stopped after about thirty plants because the report rebuild
superseded its tip, and no verdict was claimed from it.

The second census, at `2b3b3ab`, returned `195/197`. The two misses were the plants that mutate the
*with-oracles* half of the pair — `report-counts-stale-python-tests` and
`reproducibility-quotes-a-superseded-pytest-total` — now reported as `no-guard-objected`. On a
runner without that extra the count guard compares only the offline half with the collected
total, so the other half had no observer; those plants had passed the earlier censuses only
because the offline half happened to be stale there too. The guard now compares every
restatement of each figure within a document and the pair across all five documents, a comparison
neither environment can be blind to, while keeping the per-environment comparison with the
collected total. Both named plants were re-run singly on the no-oracles worktree and are `caught`.
The final census at `aafb707` is `197/197`; the two red runs are the reason that green sentence is
a measurement at a named tip rather than a property of the code in general.

### 13.3 Readings at the final tip (`aafb707`)

| Reading | Value |
|---|---|
| Full census verdict | `declared 197 / ran 197 / caught 197`, `non_caught []`, `unmeasurable []`; watched checkout empty before and after |
| Runner list and derived counts | `runner --list` 197; `docs_rederivation` `gap: 0` with 197 derived plants across five documents |
| Ceiling census | 15 keys: 14 `ok` / 1 `SKIP` once the verdict sits at `build/sweep_verdict.json` (`plants_not_rejected_by_their_guard: 0`); 13 `ok` / 2 `SKIP` where that key's precondition is absent |
| Evidence and format | `Evidence is intact`, 0 missing; `ruff format --check .` 255 files already formatted |
| Full pytest, this shell | `1 failed, 567 passed in 148.73s`, the known bytecode-cache plant that needs `__pycache__` writes this shell does not make (`PYTHONDONTWRITEBYTECODE=1`); not a regression |
| Single-plant proof | `site-source-carries-a-figure-of-its-own`: red `1 failed in 0.49s` → restored `1 passed in 0.29s` |

The ceiling count is a vantage restoration, not a second measurement: `sweep_gap` does not compare
the verdict's revision with the tip, and placing the verdict where its key reads it changes which
keys declare their precondition present. The site itself is not committed: `build/site/` is
ignored, and the scope's exclusion of committed build output is read as that directory. The one
committed artifact the unit did rebuild is `paper/technical_report.pdf` with its sidecar, because
`technical_report.tex` changed and a separate guard binds the PDF to the source bytes; pdfTeX
1.40.29 on this workstation matches the sidecar's recorded engine, while the runner's 1.40.25 is
exactly the environment-blind plant already registered from X1b.

### 13.4 What X2 did not do

No deployment, hosting, drift gate or new ceiling key; no CLI subcommand, new dependency or frozen
contract change; no README or front-page rewrite. Liveness I-L2 is filled only for generation and
the source scan, with its drift half still VOID; I-L5 is partial as recorded in section 2. DoD
item 3 stays 未完成 because the drift gate and free-tier publish are Phase 4, not this unit. A push
requires its own verbatim approval under section 12; until then this section has no platform
counterpart, as section 11.1 has for X1b.

## 14. Push approval for X2 and its bound

The three-option question asked whether to push the seven commits and backfill the platform
readings, push without backfilling, or leave them local. Approval original, verbatim:
`推送并回填（最推荐）`.

Bounded effect, the same as section 11's for X1b: at most two non-forced ref updates through
`build/api_push.py`, each blob, tree and commit SHA verified before it travels; read the run the
first update produces; write the readings into the ledger as the backfill commit; perform the
second ref update to carry that commit. No tag, release, deploy or publication moves. The
backfill commit's own run is observed-only under the same recursion limit — a third ref update is
outside this approval — so its outcome belongs in the local work log rather than in this ledger,
and no reading in section 15 is a claim about the backfill tip.

## 15. X2's first platform run: a real failure, and what it cost

The first ref update carried the eight commits through `7cbcc7b`, every SHA verified, no tag moved.
Run `43843195255`, attempt 1, 16m09s, concluded **failure**: five of six jobs succeeded and
"Format and static checks" failed in its `ruff check .` step with 17 findings, all in files X2
added or edited. Fourteen were `E501` on prose lines, and the other three were `UP035`
(`Sequence` from `collections.abc`), `I001` (import order) and `SIM300` (a Yoda assertion).
The step ordering matters: the job stopped at `ruff`, so that run has no lint-vantage reading for
formatter, evidence or ceilings, and none is inferred here. The local preparation had run
`ruff format --check .` but not `ruff check .`; those are two separate CI steps, and only the first
had been executed before the push.

The five successful jobs are still readings at that failed tip, attributed to the job that printed
each one:

| Job | Reading |
|---|---|
| Configure, build, C++ tests, Python tests | `498 passed, 5 skipped in 168.95s`; the historical attestation still prints `195 caught of 195 declared` at a 197-plant tip, which is V13's ruling holding |
| Mutation census | `197 declared = 196 measurable here + 1 environment-blind`, `196/196` `caught`; the blind sample is `report-source-edited-without-a-rebuild-seen-from-the-render`, this runner's pdfTeX being 1.40.28 against the sidecar's 1.40.29 |
| Benchmark suite | `19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 410.2s total` |
| Installed wheel surface | revision `7cbcc7b`, version `1.9.0`, clean venv outside the checkout |
| Ceilings adjudication inside the census/installed jobs | `docs_rederivation` `gap: 0` with 197 derived plants; `with_extras_census` `19/19`; `lanes_documented_vs_executed` `gap: 0` |

The 1.40.28 reading differs from X1b run's 1.40.25 because the runner image changed, not because
the report drifted; both are environment-blind declarations against the same recorded 1.40.29.
The job's verdict file declares 196 because that is what ran on that machine, while stdout and
`docs_rederivation` both derive 197; those are two quantities, not a disagreement.

Commit `7971299` fixes the lint findings as source shape only: prose lines wrapped, `Sequence`
imported from `collections.abc`, import order and assertion direction corrected, and the plant's
claim text re-wrapped without moving its anchor, replacement or guard. The generator still contains
no numeric literal and `LAYOUT_NUMBERS` remains empty. Re-measured locally at `7971299`:
`ruff check .` all checks passed, `ruff format --check .` 255 files already formatted,
`docs_rederivation` `gap: 0` at 197 plants, evidence intact, ceilings 14 `ok` / 1 `SKIP` once the
new verdict is placed at `build/sweep_verdict.json`, full census `declared 197 / ran 197 /
caught 197` with both failure rows empty and the watched checkout empty before and after, and
pytest `1 failed, 567 passed` with only the known sandbox bytecode-cache case failing.

The second ref update in this approval carries `7971299` together with this backfill commit. No
platform success is claimed for `7cbcc7b`, and the run over the backfill tip is observed-only.

## 16. Scope unit X3 — the drift gate, and nothing around it

Approval original, verbatim: `方案 A（推荐）`, answering the three scope sentences put to the
maintainer. The chosen sentence, recorded here in the same words it was shown:

> 批准作用域单元 X3：只新增一个站点漂移门禁，以一份提交的 `build/site.lock`（记录每个已生成
> 页面的 sha256 及其来源 artifact 的 sha256）为冻结基准；门禁命令从当前 artifact 重新生成
> 站点到临时目录，逐页比对页面摘要与锁文件，任何不符即非零退出。新增一个 CI step 与一个
> 受控植物——篡改某 artifact 的 headline 数字并同步 manifest 的 `sha256`/`content_sha256`，
> 使摘要门禁不报 CHANGED——证明该门禁独立转红、恢复转绿，机制在阶段报告中具名。不新增
> 天花板键、不改 CLI 子命令、不新增依赖、不做部署或发布。

The two declined alternatives are kept so the boundary is a decision, not an omission. **B** would
have had a reader extract each figure back out of the generated HTML and compare it with the
artifact, with no frozen baseline — declined because the reverse parse is brittle and its plant is
likely to be caught first by X2's zero-numeric-literal guard, so the new gate's own falsifiability
would stay unproven. **C** would have used a plant on the existing `verify_evidence_manifest` —
declined because byte-digest drift was already gated in CI before X3 and H3's page-level
"figure equals artifact value" claim would remain unmeasured.

One fact fixes the boundary: `verify_evidence_manifest` already re-hashes every listed artifact's
bytes and result content in the lint job, and `test_an_artifact_whose_bytes_moved_stops_the_build`
already proves the generator refuses an artifact whose bytes moved off the manifest. A gate that
only re-checks the digest would duplicate both. X3's subject is the *page*: a committed baseline of
what each page hashed to, and a command that rebuilds and compares, so a value can change in an
artifact and in the manifest while the published page still carries the old figure — and the gate
alone objects.

Bounded effect, and nothing beyond it: one committed `build/site.lock` frozen at the current
artifacts; one drift-check command reachable as a module-path invocation, printing a per-page
comparison and exiting non-zero on any mismatch; one CI step calling it; one controlled plant that
keeps the digest gate quiet while moving a figure, with a named red/green proof; the count claims
that plant moves, re-derived in the same series. Excluded: any new ceiling key (the inventory stays
at fifteen), any deployment or publishing configuration, any CLI subcommand, any new dependency,
any committed page under `build/site/`, any change to the generator's zero-literal rule, and any
README or front-page rewrite. A push remains a separate external action and is **not** covered
here; the recursion limit from earlier push approvals is not carried forward by this one.

Two constraints are in scope because the readings they would break are already measured:

| Constraint | Reading it would break |
|---|---|
| The drift command is a module-path invocation, not a CLI subcommand | §3 condition 3 counts exactly four subcommands: `benchmark`, `demo`, `run`, `validate` |
| No new ceiling key | the inventory is fifteen keys; every vantage narration prints that count |

Known blast radius, inherited from two prior units: an additional plant moves the `197/197`
annotation in `docs/interview_defense.md` and the anchor of
`docs-command-comment-counts-superseded-plants`, and both must be re-derived in the same series.
The lock file is committed build output but is not a page: it is a frozen reading, and the scope's
exclusion of committed build output continues to mean the `build/site/` page directory.

## 17. X3 phase report — the page-level drift gate

### 17.1 What the gate checks, and what it does not duplicate

`python -m quantrisk.interface.drift --freeze --lock build/site.lock --out <dir>` froze a baseline of
twenty pages at `4907057`: each page's SHA-256 beside the SHA-256 of the artifact that produced it.
`--check` rebuilds into a temporary directory and compares both digests per page, plus the set of
pages, exiting non-zero on any difference. The lock is committed; the rebuilt pages are not —
`build/site/` stays ignored, so "no committed build output" still names the page directory, not the
baseline.

The subject is deliberately not the artifact bytes. `verify_evidence_manifest` already re-hashes
every artifact's bytes and result content in CI, and the site build already refuses an artifact
whose bytes disagree with the manifest. A figure can move in an artifact while both manifest
digests are recomputed with it — the evidence chain is then internally consistent, so both of those
guards stay green — and the published page still renders the old figure. Only a comparison against
a frozen reading of the *page* sees that. This is H3's "every figure the site renders equals the
value read from the artifact it claims", not a second opinion on the digest.

### 17.2 The named falsification

| Element | Value |
|---|---|
| Plant | `site-lock-catches-a-manifest-silent-figure-change` |
| Target | `experiments/restrike_gamma_map/results/restrike_gamma_map.json`, the figure `0.6924` |
| Guard | `tests/python/test_interface_drift.py::test_the_committed_lock_detects_a_figure_that_drifted_in_an_artifact` |
| Mechanism | the guard reads the committed lock against the tree; changing a locked figure moves its artifact digest away from the frozen one, so the guard objects |

Single-plant proof at `4907057`: planted `1 failed in 0.23s`, restored `1 passed in 0.22s`, verdict
`caught`. The figure was chosen because `0.6924` occurs once in its artifact, is not a plant anchor
elsewhere, and is not printed by any guarded document — so the plant isolates this gate rather
than riding on another guard's objection.

One scope correction is recorded rather than hidden. The first X3 commit widened the generator's
zero-literal guard from `site.py` to the whole interface package; section 16 excludes any change to
that rule, so `28727f4` restored the original guard byte for byte and gave `drift.py` its own
zero-literal test instead. The swap is count-neutral (572/503 before and after) and leaves both
plants' pairings intact. The final census revision is `28727f4`, not `4907057`.

### 17.3 Readings — all development-side at `28727f4`

| Reading | Value |
|---|---|
| Full census | `198/198 planted defects were rejected by their guard`; verdict `declared 198 / ran 198 / caught 198`, `non_caught []`, `unmeasurable []` |
| Watch | checkout porcelain empty before and after the sweep |
| Single plant | `1 failed in 0.23s` planted → `1 passed in 0.22s` restored, `caught` |
| `runner --list` | 198 plants; `docs_rederivation` `gap: 0` at 198 derived plants |
| Ceilings | 15 keys, `14 ok / 1 SKIP` with the verdict placed at `build/sweep_verdict.json` (the `installed_user_identity_mismatch` key reports its precondition absent on this vantage); no `FAIL` |
| Full pytest | `1 failed, 571 passed`; the one failure is the known bytecode-cache plant, which needs `__pycache__` writes this shell does not make under `PYTHONDONTWRITEBYTECODE=1`; not a regression |
| `ruff check .` / `ruff format --check .` | all checks passed / 257 files already formatted |
| Evidence manifest | intact, `0 MISSING`, `0 CHANGED`, `0 on disk but not in the manifest` |
| Drift CLI | `PASS: rebuilt site matches build/site.lock` |

Two red censuses preceded the green one, both recorded as history rather than erased. An earlier
`4907057` census was `198/198` but at a tip whose guard change exceeded the scope; the final
`28727f4` census repeats `198/198` after that correction. Neither is treated as a claim about the
other's revision — a verdict names the revision it measured.

### 17.4 What X3 did not do

No deployment, hosting or free-tier publish; no new ceiling key (the inventory stays at fifteen);
no CLI subcommand (still four); no new dependency; no committed page; no change to the generator's
zero-literal rule after the `28727f4` correction; no README or front-page rewrite. Liveness I-L2's
drift half is now Filled, but H3's zero-drift *value* stays 未测得 because there is no published
surface to measure — the gate is proven able to fail, not yet measuring a deployed page. A push is
a separate external action excluded by section 16; no platform reading is claimed here. DoD item 3
stays 未完成 because free-tier publish and a genuinely network-down offline build remain Phase 4.

## 18. Push approval for X3 and its bound

Section 16 excluded a push, so section 17 could only be a development-side reading. The
three-option question asked whether to push the four commits and backfill the platform readings,
push without backfilling, or leave them local. Approval original, verbatim: `推送并回填（最推荐）`.

Bounded effect, and nothing beyond it: at most two non-forced ref updates through
`build/api_push.py`; read the first run produced by the push and attribute each reading to the job
that printed it; write those readings into a backfill commit in this ledger, including any failure
as a failure rather than omitting it; carry that backfill commit in the second ref update. The
recursion limit is the same one section 11 and section 14 used: the backfill commit's own run is
observed-only, because a third ref update is outside this approval. No tag, release, deployment or
publication is moved. The `site drift gate` step added in X3 is expected to run on the runner as a
new CI step, and its reading belongs to whichever job carries it.

## 19. X3's first platform run: a MyPy-only failure, and the typed repair

The first ref update moved the platform from `3ab651f` to `97cd793` with five commits (the four
X3 commits plus the commit that recorded this approval), non-forced, every blob, tree and commit
SHA verified, no tag moved. Run `44077370395`, attempt 1, head `97cd793d6635`, created
`2026-11-17T11:48:50Z` and updated `12:04:10Z`, concluded **failure**: five of six jobs succeeded
and "Format and static checks" failed. In that job `ruff`, `ruff format` and `clang-format`
succeeded; `mypy` printed:

> `python/quantrisk/interface/drift.py:91: error: Incompatible return value type (got "Collection[str]", expected "dict[str, dict[str, str]]")  [return-value]`
> `Found 1 error in 1 file (checked 78 source files)`

The job stops there. `Docs re-derivation`, `Artifact revision`, `refactor ceilings`,
`evidence manifest` and the new `site drift gate` are `skipped` in this run; no reading is inferred
for them from another job. In particular this run supplies **no runner-side site-drift reading** —
the step never executed. That absence is the reason for the second ref update, not a claim that the
step failed.

The five successful jobs remain readings at `97cd793`, attributed to the job that printed them:

| Job | Reading |
|---|---|
| Configure, build, C++ tests, Python tests | `100% tests passed out of 204`; `502 passed, 5 skipped in 132.37s`; `7/7 checks passed`; `PASS: V9_LEDGER.md attests 5ec3fabe4fa8c83584a50b3ab66b357ae13094e9 as a strict ancestor of 97cd793d6635, 195 caught of 195 declared` |
| Mutation census | `198 declared = 197 measurable here + 1 environment-blind`; `197/197 planted defects were rejected by their guard`; `site-lock-catches-a-manifest-silent-figure-change` printed `ok caught`; verdict `declared 197 / ran 197 / caught 197` at revision `97cd793d6635`, both `git status --porcelain` readings empty |
| Benchmark suite | `19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 246.3s total`; with-extras census `19/19`, `gap: 0` |
| Installed wheel surface | clean venv outside the checkout, revision `97cd793d663547585b93a05b651d878c3565509b`, version `1.9.0`, `7/7` proved checks passed |
| macOS native parity | `100% tests passed out of 204`; `98 passed in 2.08s` |

The blind plant is the registered `report-source-edited-without-a-rebuild-seen-from-the-render`:
this runner's pdfTeX was 1.40.28 against the sidecar's recorded 1.40.29, so it is declared
environment-blind rather than counted as caught. The ceiling adjudication in both the
installed-surface and mutation-census jobs printed 14 `ok` / 1 `SKIP` (`installed_user_identity_mismatch`
precondition absent on each vantage), `docs_rederivation` `gap: 0` with 198 derived plants, and
`lanes_documented_vs_executed` `gap: 0` with `quantrisk.interface.drift` already executed at
`lint :: site drift gate` in the workflow text.

Commit `c59cb62` fixes only the static finding: `freeze()` used to return `document["pages"]`,
which MyPy widened from the declared `dict[str, dict[str, str]]` to `Collection[str]` because the
surrounding document mixes string and dict values. It now binds the fingerprint dict to a typed
local and returns that local. No runtime behaviour, test, plant pairing or lock byte changes, and
the drift module's own zero-literal test still holds. The local gate lesson is repeated from
section 15 with a different step: `ruff check .`, `ruff format --check .` and `mypy <targets>` are
three separate CI steps, and only the first two had been run before the first push. The failed run
is kept here as a failure rather than omitted.

Local re-measurement at `c59cb62`:

| Reading | Value |
|---|---|
| Static trio | `ruff check .` all checks passed; `ruff format --check .` 257 files already formatted; `uv run mypy python/quantrisk tools` `Success: no issues found in 78 source files` |
| Drift-specific | `4 passed in 0.95s` for `tests/python/test_interface_drift.py`; `PASS: rebuilt site matches build/site.lock` |
| Evidence and documents | `95 OK`, `0 CHANGED`, `0 MISSING`, `0 on disk but not in the manifest`; `docs_rederivation` `gap: 0` with 198 derived plants |
| Full census | `198/198 planted defects were rejected by their guard`; verdict `declared 198 / ran 198 / caught 198`, `non_caught []`, `unmeasurable []`, watched checkout empty before and after |
| Ceilings | 15 keys, 14 `ok` / 1 `SKIP` with the new verdict supplied through `QUANTRISK_SWEEP_VERDICT`, no `FAIL` |
| Full pytest | `1 failed, 571 passed in 129.55s` — the known sandbox bytecode-cache plant, named and not silenced; CI reads the runner's result |
| Scope | only `python/quantrisk/interface/drift.py`, four insertions and three deletions; no test, plant, artifact, lock or document changed |

The local census needed its injected `PYTHONPATH` shim removed for that one child process: the
shim's `rmdir` broker cannot delete the harness's empty probe directory, and the first attempt
stopped at the first tree plant without producing a verdict. This is a machine-side file-system
detail, not a project defect; removing the injection changes no guard, plant or source byte, and
the re-run returned the verdict quoted above with the tree clean.

The second ref update in this approval carries `c59cb62` together with this backfill commit. Its
own run is observed-only under section 18's recursion limit — a third ref update is outside the
approval — so its outcome belongs in the local work log and no reading in this section is a claim
about that tip.

## 20. Scope unit X4 — the attribution gaps and the read-only provenance surface

Scope unit X4, as put to the maintainer verbatim, with the alternatives that were declined beside it:

> **方案 A（推荐）** 批准作用域单元 X4：只做两件事。(1) 修复两处文档归属缺口：在
> `REFACTOR_PROMPT.md` §13 新增一张 Phase 5 后 liveness 更新表，把 L4 记为 ACTIVE 并附可复核
> 读数，不改写 "Liveness at authoring" 历史表；(2) 新增一个包内只读模块
> `python -m quantrisk.interface.provenance`，实现 I1/I3 的溯源语义——列举注册任务及其
> canonical command、按 artifact 路径查 manifest 溯源条目、返回值并同时返回
> command/revision/digest、缺任一溯源要素即具名拒绝而非返回裸值——并新增一株受控植物证明
> 该拒绝守卫会转红、恢复转绿，机制在阶段报告中具名。不新增 CLI 子命令、不改冻结的输出
> 指纹与子命令集合守卫、不新增天花板键、不改 CLI 输出或公开 API 名称、不新增依赖、不做
> 部署或发布；入口为 `-m` 模块而非 `quantrisk` 子命令。

Approval original, verbatim: `方案 A（推荐）`.

The two declined alternatives are kept so the boundary is a decision, not an omission. **B** would
have added real `quantrisk` subcommands (`provenance`/`list`/`findings`) and edited the frozen
usage-set assertion and CI-lane guard to accept them — declined because it rewrites the E28/§3
frozen CLI contract, with a larger blast radius. **C** would have repaired G-A/G-B only and left
DoD items 2 and 4 open — declined because the maintainer chose to close the repository-provable
items in this unit.

Bounded effect, and nothing beyond it: one new update table in `REFACTOR_PROMPT.md` §13; one new
in-package module reachable as `python -m quantrisk.interface.provenance`; one new pytest guard
plus one controlled plant proving that guard can fail; the count claims that plant moves,
re-derived in the same series. Excluded: any new CLI subcommand, any change to the frozen output
fingerprints or the four-subcommand set assertion, any new ceiling key, any change to CLI output
or to a frozen public API name, any new dependency, any deploy or publish, any edit to the
"Liveness at authoring" historical table, and any change to the V9 historical attestation. A push
is a separate external action and is **not** covered here.

Two constraints are part of the scope because the readings that would break are already measured:

| Constraint | Reading it would break |
|---|---|
| The provenance surface is a `-m` module, not a CLI subcommand | §3 condition 3 and `test_cli_pre_existing_command_outputs_kept_their_contracts_when_run_landed` count exactly four subcommands |
| The L4 update is a new table, not an edit to the authoring table | section 1's rule that a reading silently edited to match a later state is the failure this ledger exists to prevent |

Known blast radius, from three prior units: a 199th plant moves the `198/198` annotation in
`docs/interview_defense.md` and the derived-plant count behind `docs_rederivation`; both turn red
until re-derived. X4 treats those as part of its own change, not as surprises.

## 21. X4 phase report — the attribution gaps and the read-only provenance surface

Section 20 holds the scope sentence and the approval original. A push is excluded there, so every
reading in this section is development-side at the implementation tip `25aed30`. The commits that
make the unit: `155b947` scope and approval; `25aed30` the update table, the module, the guard, the
plant, the re-derived counts and the rebuilt report.

### 21.1 The two attribution gaps, closed where the Check looks

G-A was that `REFACTOR_PROMPT.md` §13's "Liveness at authoring" table still recorded L4 VOID and
had no Phase-5-after update table, while `INTERFACE_ROADMAP.md` §3's Check names that file as the
authority. G-B was that the matching `ACTIVE, satisfied` row lived in `REFACTOR_LEDGER.md` Phase 5
instead. X4 appends a new "L4 after Phase 5 (updated)" table to §13 that records L4 ACTIVE with an
executable reading — the dry-resolve guard `test_every_manifest_command_resolves_as_a_module_without_being_run`
and its plant — and points to §10 for the run-side evidence. The authoring table is not edited; its
VOID row is a reading at authoring time, and the section states explicitly that the two rows are
readings at different times rather than a contradiction to be silently reconciled. Both gaps are
closed by one act: the ACTIVE reading now exists in the file the Check designates, and the ledger's
Phase 5 row is a report of the same fact, not the authority.

### 21.2 The surface, and the sample that can break it

`python -m quantrisk.interface.provenance --list` prints every registered task with the canonical
command derived from its module path; `--resolve <artifact>` returns one record binding the
artifact's headline value to the command, the manifest's recorded revision and the manifest's frozen
digest. `--json` emits the same record as JSON. If any element cannot be resolved — the artifact is
absent, its command blank, the revision missing, or its headline unreadable — `ProvenanceRefused`
names the specific gap and no value is emitted; the CLI form prints `REFUSED: …` and exits non-zero.
The module reads only; no socket, no write, no study execution. It carries no numeric literal,
checked by its own test rather than by widening `site.py`'s guard (the X3 scope correction).

| Element | Value |
|---|---|
| Plant | `provenance-erases-a-recorded-command` |
| Target | `evidence/manifest.json`, the command `uv run python -m quantrisk.experiments.sixth_book_crossing_map` (unique in the file) |
| Guard | `tests/python/test_interface_provenance.py::test_no_value_is_returned_without_its_command_digest_and_revision` |
| Mechanism | blanking that one command leaves the sample artifact's value unresolvable; the guard, which requires every headline-bearing registered artifact to resolve with command/digest/revision intact, objects; restoring the manifest returns it to green |

Manual red/green at `25aed30`: planted `1 failed` with the refusal naming the blanked
`generated_by_command`; restored `Evidence is intact`, `0 CHANGED`, `0 MISSING`. The full census
then recorded `ok caught` for the plant at revision `25aed30fe4c8b8db9bb7adbd236e08afda3af806`.

### 21.3 Readings — all development-side at `25aed30`

| Reading | Value |
|---|---|
| Full census | `199/199 planted defects were rejected by their guard`; verdict `declared 199 / ran 199 / caught 199`, `non_caught []`, `unmeasurable []`, `checkout_status_before` and `after` both empty |
| Single plant | planted `1 failed` → restored `Evidence is intact`; `ok caught` in the full census |
| `runner --list` | 199 plants; `docs_rederivation` `gap: 0` at 199 derived plants |
| Ceilings | 15 keys, `14 ok / 1 SKIP` with the verdict supplied through `QUANTRISK_SWEEP_VERDICT` (`installed_user_identity_mismatch` precondition absent on this vantage), no `FAIL` |
| Full pytest | `1 failed, 579 passed in 194.30s`; the one failure is the known sandbox bytecode-cache case, which needs `__pycache__` writes this shell does not make under `PYTHONDONTWRITEBYTECODE=1`; not a regression, and the eight new provenance tests all pass |
| Static trio | `ruff check .` all checks passed; `ruff format --check .` 259 files already formatted; `uv run mypy python/quantrisk tools` `Success: no issues found in 79 source files` |
| Evidence manifest | `95 OK`, `0 CHANGED`, `0 MISSING`, `0 on disk but not in the manifest` |
| Drift CLI | `PASS: rebuilt site matches build/site.lock` |
| Provenance CLI | `--resolve` on the sample returns value + command + revision + digest; `--list` enumerates the registry |

The count cascade moved three published numbers and was re-derived, not bypassed: plants `198→199`,
offline-collected tests `503→511`, with-oracles tests `568→572→580`. The living claims in
`docs/interview_defense.md`, `docs/reproducibility.md`, `docs/limitations.md` and
`paper/technical_report.tex`, the five plant anchors that key on those figures, the two gold tuples
in `test_artifact_metadata.py` and the rebuilt report PDF and its sidecar were all updated in the
same implementation commit. The four count guards were re-run green after the cascade; the
committed PDF is bound to the sources that rendered it.

The census again needed the local `PYTHONPATH` shim removed for that one child process: the shim's
`rmdir` broker cannot delete the harness's empty probe directory. This is a machine-side file-system
detail, not a project defect, and removing the injection changes no guard, plant or source byte.

### 21.4 What X4 did not do

No CLI subcommand — the CLI stays at four, and the literal `quantrisk provenance` form declined in
option B remains a separate decision; no deploy or publish; no new ceiling key (the inventory stays
at fifteen); no new dependency; no committed page; no edit to the authoring-time liveness table or
to the V9 historical attestation. §3's four conditions are untouched. DoD item 3 stays 未完成
because free-tier publish and a genuinely network-down offline build remain Phase 4; H1–H4 remain
unmeasured; I-L2's provenance half is still a sentence about a surface whose value-level claim is
now falsifiable but whose deployed-page value remains unmeasured. A push is a separate external
action excluded by section 20; no platform reading is claimed here.

## 22. Push approval for X4 and its bound

Section 20 excluded a push, so section 21 could only be a development-side reading. The closing
question offered push-and-backfill, push-without-backfill, or leave-local. Approval original,
verbatim: `推送并回填（最推荐）`.

Bounded effect, and nothing beyond it: at most two non-forced ref updates through
`build/api_push.py`, carrying the three X4 commits (`155b947`, `25aed30`, `8bb9caa`) together with
the commit that records this approval; read the first run produced by the push and attribute each
reading to the job that printed it; write those readings into a backfill commit in this ledger,
including any failure as a failure rather than omitting it; carry that backfill commit in the second
ref update. The recursion limit is the one sections 11, 14 and 18 used: the backfill commit's own
run is observed-only, because a third ref update is outside this approval. No tag, release,
deployment or publication is moved; the `site drift gate` and the new provenance surface are expected
to be exercised by the runner's existing jobs, and any reading belongs to the job that printed it.

## 23. X4's first platform run: a clean six-job success

The first ref update moved the platform from `11a7a50` to `c3db63e` with four commits (the three
X4 commits plus the commit recording the approval), non-forced, every blob, tree and commit SHA
verified, no tag moved. Run `44101295511`, attempt 1, head `c3db63ef7991`, created
`2026-11-17T14:16:24Z` and updated `14:36:14Z`, concluded **success**: all six jobs succeeded.
Unlike X3's first run, no repair was needed; the readings below are the runner's, each attributed
to the job that printed it. This is the first X-series push that went green on its first run.

| Job | Reading |
|---|---|
| Format and static checks | `ruff` `All checks passed!`; `ruff format` `259 files already formatted`; `clang-format` success; `mypy` `Success: no issues found in 79 source files`; `Docs re-derivation` `19/19 benchmark-suite members executed`, `199/199 planted defects rejected`; `Artifact revision` `gap 0` (shallow clone, pinned historical revision); `refactor ceilings` `14 ok / 1 SKIP` with no FAIL, `docs_rederivation_gap 0`, `lanes_documented_vs_executed_gap 0`, the SKIP being `installed_user_identity_mismatch` (precondition absent in the lint vantage); `evidence manifest` `95 OK`, `0 CHANGED`, `0 MISSING`; **`site drift gate`** `PASS: rebuilt site matches build/site.lock` |
| Installed wheel surface in a clean environment | wheel built from the tree, installed into `$RUNNER_TEMP/installed-venv` only; probe identity module resolved under that venv at version `1.9.0`; `run --list` `tasks 19` / `tally 19`; `validate` `passed 7`, exit 0; offline study `mc_speed` produced `monte_carlo_speed.json`, exit 0; refusal on `pricing_grid` exit 1, `named true`, `empty_directories_left 0`; verdict uploaded, SHA `4baae3895552…` |
| Configure, build, C++ tests, Python tests | `100% tests passed out of 204`; Python `510 passed, 5 skipped in 142.13s` fully offline (the five skips are the four oracle-gated modules and the latexmk re-typeset guard); `7/7 checks passed`; `PASS: V9_LEDGER.md attests 5ec3fabe4fa8 as a strict ancestor of c3db63ef7991, 195 caught of 195 declared` |
| Mutation census in a detached worktree | `199 declared = 198 measurable here + 1 environment-blind`; `198/198 planted defects were rejected by their guard`; the new plant `provenance-erases-a-recorded-command` printed `ok caught`; the one environment-blind case is `report-source-edited-without-a-rebuild-seen-from-the-render` (runner pdfTeX `1.40.28` versus the build sidecar's `1.40.29`); verdict `declared 198 / ran 198 / caught 198` at revision `c3db63ef7991`, both `git status --porcelain` readings empty; `plant_liveness` probe `199`, `docs_rederivation derived plants 199`; ceilings `14 ok / 1 SKIP`, no FAIL |
| macOS native C++ and Python parity | all native C++ tests and the C++/Python parity probe passed on the pinned wheel, success |
| Benchmark suite against live oracles | `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 407.9s total`; with-extras census `19/19`, `gap 0` |

The runner's `198/198` and the development-side `199/199` in section 21 are not a disagreement:
the runner's one environment-blind plant is the re-render guard whose pdfTeX version differs from
the build sidecar, exactly the X3 condition, and the development vantage has the matching pdfTeX.
Both vantages agree on every measurable plant, including the new provenance plant.

This backfill commit is carried in the second and final ref update of the section 22 approval. Its
own run is observed-only under the section 18/22 recursion limit; no third ref update is authorised
and no reading in this section is a claim about that tip.

## 24. Scope unit X5 — CI publication of the artifact-bound site

Scope unit X5, as put to the maintainer verbatim, with the alternatives declined beside it:

> **1. GitHub Pages + CI（推荐）** 在 CI 加 deploy job，用 `actions/upload-pages-artifact` +
> `actions/deploy-pages`，`permissions: pages:write, id-token:write`（GitHub 内置 OIDC token，非
> 新增 secret/账号），站点由 CI 生成并发布、漂移门禁失败即阻断部署——符合 Phase 4 "from CI,
> never from a laptop" 和 "zero cost"。代价：启用 Pages Source。

Approval original, verbatim: `1`.

The declined alternatives are kept so the boundary is a decision, not an omission. **2** would have
published `build/site/` through a hosted one-click link from this machine — declined because it is
"from a laptop", is not bound to the CI drift gate, and so cannot close DoD item 3 even if a URL is
obtained. **3** would have built the offline/H1 producers without any real deploy — declined because
it leaves H3's published-surface value and I-L3/L4/L6 VOID. **4** would have maintained the status
quo.

One execution detail is recorded here rather than in the approval: the option described the Pages
Source being enabled by the maintainer in Settings, but the GitHub REST API can set
`build_type: "workflow"` with a classic token holding `repo` scope plus repository admin rights,
both confirmed present. X5 therefore enables Pages through `POST /repos/{owner}/{repo}/pages`
instead of asking for a manual click. This is the same external effect by a different hand; it is
not a wider authorisation. The OIDC token minted per deployment by `actions/deploy-pages` is a
GitHub-issued, short-lived credential, not a secret added to this repository, and the pre-existing
GitHub account and repository are not a "new account" — so K1 and IN2's "no new secret, no new
credential, no account for a free tier" remain satisfied by the same reasoning that admitted the
CI lane.

Bounded effect, and nothing beyond it: one Pages site enabled with `build_type: workflow`; one new
CI deploy job whose only added permissions are `pages: write` and `id-token: write`, gated on the
existing lint job so that a drift-gate failure blocks publication; one new pytest guard reading the
committed workflow to prove the deploy job is downstream of the drift gate, plus one controlled
plant that breaks that dependency and makes the guard fail; the count claims those additions move,
re-derived in the same series. Excluded: any secret, key or credential stored in the repository; any
paid service; any publish from a laptop; any new CLI subcommand; any new ceiling key; any new
runtime dependency; any change to the frozen four-subcommand contract; any edit to the V9 historical
attestation; any movement of tag `v1.9.0`; and any push (a separate approval, as in X4).

H1–H4 measured values, I-L5's genuine network-down build, and I-L3/L4/L6's move from VOID to
measured are consequences of having a published surface, not claims made by this scope unit. They
are named here as subsequent units so that X5 does not assert a value it has not measured.

## 26. X5 phase report — CI publication of the artifact-bound site

Section 24 holds the scope sentence and the approval original. A push is excluded there, so every
reading in this section is development-side at the implementation tip `fa68b7b`. The commits that
make the unit: `59f2e82` scope and approval; `0b2ae7a` the Pages enablement record, the deploy job,
its guard and plant, the lane/document registration and the re-derived counts; `fa68b7b` the claim-
sample gold re-annotation that the document-byte change required.

### 26.1 The site is published from the bytes the gate verified

`build/site/` is generated from committed artifacts by `python -m quantrisk.interface.site`; the
X3 gate freezes each page's SHA-256 and its source artifact's SHA-256 in `build/site.lock` and
rebuilds to compare. X5 adds a `deploy` job that calls that same gate with
`--out "${RUNNER_TEMP}/site-publish"`, then uploads that directory with
`actions/upload-pages-artifact@v4` and publishes it with `actions/deploy-pages@v4`. Because the
drift check writes the pages it verifies, the uploaded bytes are the checked bytes; there is no
second build whose agreement is assumed. A figure that moved with its digests re-frozen still
reddens the lock, so the gate fails and the job cannot publish.

Three properties make the job a claim rather than a hope, each with a named test in
`tests/python/test_interface_deploy.py`:

| Property | Guard |
|---|---|
| Publication is downstream of the drift gate | `test_publication_is_downstream_of_the_drift_gate` — deploy `needs: [lint]`, and lint runs `site drift gate` |
| The published bytes are the verified bytes | `test_publication_uploads_the_bytes_the_gate_verified` — one drift `--check --out site-publish`, one Pages upload of that path, one deploy |
| No stored secret and a bounded event | `test_publication_adds_no_stored_secret` (permissions exactly contents:read / pages:write / id-token:write, no `secrets.`), `test_publication_runs_only_on_main_pushes`, `test_publication_never_moves_a_tag` |

`permissions` adds only `pages: write` and the short-lived OIDC `id-token: write`; no account, key
or secret is introduced into the repository, so K1 and IN2's "$0, no new secret, no account for a
free tier" hold. The OIDC token is minted per deployment by GitHub, not stored. GitHub Pages was
enabled through `POST /repos/{owner}/{repo}/pages` with `build_type: "workflow"` — the same external
effect the option described as a manual Settings click, performed by API because the token carries
`repo` scope and repository admin rights. The site is `https://jackxiaozhiren.github.io/quantrisk-plus-plus/`,
public, HTTPS-enforced, no CNAME. The `github-pages` environment exists and its branch policy
admits `main`, matching the job's `if`.

### 26.2 The sample that can break it

| Element | Value |
|---|---|
| Plant | `deploy-drops-the-lint-dependency` |
| Target | `.github/workflows/ci.yml`, the unique anchor `needs: [lint]` → `needs: []` |
| Guard | `tests/python/test_interface_deploy.py::test_publication_is_downstream_of_the_drift_gate` |
| Mechanism | dropping the edge makes publication independent of the lint job that runs the drift check; the guard reads the parsed workflow and refuses the disconnected job; restoring the edge returns it to green |

Harness red/green at `fa68b7b`: planted guard `1 failed` with the refusal naming `needs=[]`;
restored `1 passed`; the full census recorded `ok caught` for the plant.

### 26.3 Readings — all development-side at `fa68b7b`

| Reading | Value |
|---|---|
| Full census | `200/200 planted defects were rejected by their guard`; verdict `declared 200 / ran 200 / caught 200`, `non_caught []`, `unmeasurable []`, both `git status --porcelain` readings empty, revision `fa68b7b6e15e` |
| Single plant | planted guard red, restored green; `ok caught` in the full census |
| `runner --list` | 200 plants; `docs_rederivation` `gap: 0` at 200 derived plants |
| Ceilings | 15 keys, `14 ok / 1 SKIP` with the verdict supplied through `QUANTRISK_SWEEP_VERDICT` (`installed_user_identity_mismatch` precondition absent on this vantage), no `FAIL` |
| Full pytest | `585 passed in 151.41s` with `PYTHONDONTWRITEBYTECODE` unset; under this shell's default `PYTHONDONTWRITEBYTECODE=1` the known sandbox bytecode-cache case fails instead (X3/X4's same case) — not a regression |
| Static trio | `ruff check .` all checks passed; `ruff format --check .` 260 files already formatted; `uv run mypy python/quantrisk tools` `Success: no issues found in 79 source files` |
| Evidence manifest | `95 OK`, `0 CHANGED`, `0 MISSING`, `0 on disk but not in the manifest` |
| Drift CLI | `PASS: rebuilt site matches build/site.lock` |
| Deploy guards | `5 passed` in `test_interface_deploy.py` |
| Pages | `build_type=workflow`, `public true`, `https_enforced true`, no cname, branch policy `main` |

The count cascade moved plants `199→200`, offline-collected tests `511→516`, with-oracles tests
`580→585`; the living claims, the five plant anchors, the gold tuples and the rebuilt report PDF
and sidecar were updated in `0b2ae7a`. A new cascade kind appeared: editing document bytes changes
the fixed-stride claim-sample units, so `_CLAIM_SAMPLE_GOLD`'s index 420 and the false-positive
list were re-annotated in `fa68b7b` — the guard's own instruction ("re-annotate the gold, do not
edit this assert") was followed, and neither the stride nor any assertion was changed. A concurrent
census+pytest run was found to produce false failures in the restrike and mutation modules; the
final readings above were taken with the two runs serialised.

### 26.4 What X5 did not do

No push: section 24 excludes it, so the deploy job has never executed on a runner and this section
claims no live-URL reading. DoD item 3 is therefore **Partial**, not Done — the free-tier publish is
enabled and gated in code, but not yet observed from the platform. Offline build stays partial
(I-L5: the in-process no-socket test is narrower than a network-down build, and a subprocess making
a network call escapes the probe). H1–H4 values, I-L3/L4/L6's move from VOID and the genuinely
network-down build remain subsequent units — they are consequences of a published surface, not
claims this unit makes. No new secret, account, dependency, ceiling key or CLI subcommand; no tag
moved; no edit to the V9 historical attestation.

## 27. Push approval for X5 and its bound

Section 24 excluded a push, so section 26 could only be a development-side reading: the deploy job
has never executed on a runner and this ledger claims no live-URL reading. The closing question
offered push-and-backfill, push-without-backfill, and leave-local/maintain-status-quo. Approval
original, verbatim: `推送 X5 并回填（最推荐）` — the push-and-backfill branch, the same authorisation
recorded verbatim as `推送并回填（最推荐）` in sections 11, 14, 18 and 22.

Bounded effect, and nothing beyond it: at most two non-forced ref updates through
`build/api_push.py`, carrying the four X5 commits (`59f2e82`, `0b2ae7a`, `fa68b7b`, `0e6347c`)
together with the commit that records this approval; read the first run produced by the push —
which for the first time in the X series includes a `deploy` job that publishes the gate-verified
bytes to the already-enabled Pages site, an effect bounded inside section 24 and not a wider
authorisation — and attribute each reading to the job that printed it; write those readings into a
backfill commit in this ledger, including any failure as a failure rather than omitting it; carry
that backfill commit in the second ref update. The recursion limit is the one sections 11, 14, 18
and 22 used: the backfill commit's own run is observed-only, because a third ref update is outside
this approval. No tag, release, secret or account is moved or added; the `deploy` job is downstream
of the lint job's `site drift gate` through `needs: [lint]`, so a gate failure blocks publication,
and any reading belongs to the job that printed it.

## 28. X5's first platform run: a seven-job success and a live published surface

The first ref update moved the platform from `7caca79` to `d040872` with five commits (the four X5
commits plus the commit recording the approval), non-forced, every blob, tree and commit SHA
verified, no tag moved. Run `44292891046`, attempt 1, head `d040872923644b9ade515c0e14e3649ad484d563`,
created `2026-11-18T11:14:37Z` and updated `11:40:41Z`, concluded **success**: all seven jobs
succeeded, including `Publish the evidence site`, the first `deploy` job to execute on a runner in
the X series. No repair was needed; this is the first X-series push that went green on its first
run with a real publication attached. The readings below are the runner's, each attributed to the
job that printed it.

| Job | Reading |
|---|---|
| Format and static checks | `ruff` `All checks passed!`; `ruff format` `260 files already formatted`; `clang-format` success; `mypy` `Success: no issues found in 79 source files`; `Docs re-derivation` `200/200 planted defects rejected`, `19/19 benchmark-suite members executed`, `gap 0`; `Artifact revision` `gap 0` (shallow clone, pinned historical revision); `refactor ceilings` `14 ok / 1 SKIP`, no FAIL, `docs_rederivation_gap 0`, `lanes_documented_vs_executed_gap 0`, the SKIP being `installed_user_identity_mismatch` (precondition absent in the lint vantage); `evidence manifest` `95 OK, 0 CHANGED, 0 MISSING`; **`site drift gate`** `PASS: rebuilt site matches build/site.lock` |
| Mutation census in a detached worktree | `200 declared = 199 measurable here + 1 environment-blind`; `199/199 planted defects were rejected by their guard`; the new plant `deploy-drops-the-lint-dependency` printed `ok caught`, as did `provenance-erases-a-recorded-command`, `site-lock-catches-a-manifest-silent-figure-change` and `site-source-carries-a-figure-of-its-own`; the one environment-blind case is `report-source-edited-without-a-rebuild-seen-from-the-render` (runner pdfTeX `1.40.28` versus build sidecar `1.40.29`, the X3/X4 condition); verdict `declared 199 / ran 199 / caught 199` at revision `d040872923644b9ade515c0e14e3649ad484d563`, both `git status --porcelain` readings empty; `plant_liveness` probe `200`, `docs_rederivation derived plants 200`; ceilings `14 ok / 1 SKIP`, no FAIL |
| Configure, build, C++ tests, Python tests | `100% tests passed out of 204` C++; Python `515 passed, 5 skipped in 225.28s` fully offline (the five skips are the oracle-gated modules and the latexmk re-typeset guard, the same runner-only set as X4's `510 passed, 5 skipped`; the runner excludes the with-oracles cases that give the development-side `585`); `7/7 checks passed`; `PASS: V9_LEDGER.md attests 5ec3fabe4fa8c83584a50b3ab66b357ae13094e9 as a strict ancestor of d04087292364, 195 caught of 195 declared` |
| Installed wheel surface in a clean environment | wheel built from the tree, installed into `$RUNNER_TEMP/installed-venv` only; probe identity module resolved under that venv at version `1.9.0`; `run --list` `tasks 19` / `tally 19`; `validate` `passed 7`, exit 0; offline study `mc_speed` produced output, exit 0; refusal on `pricing_grid` exit 1, `named true`, `empty_directories_left 0`; `installed_user_identity_mismatch` ceiling reads `ok ... 0` on this vantage; verdict uploaded, SHA `83e58e6a33b27...` |
| Benchmark suite against live oracles | `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 279.8s total`; with-extras census `19/19`, `gap 0` |
| macOS native C++ and Python parity | `100% tests passed out of 204` native C++; Python parity `98 passed in 3.64s`, success |
| **Publish the evidence site (deploy)** | `drift --check --out "${RUNNER_TEMP}/site-publish"` printed `PASS: rebuilt site matches build/site.lock`; `actions/upload-pages-artifact@v4` archived the two verified pages `two_factor_error_bound.html` and `linearisation_error_bound.html` into artifact `github-pages`, ID `14421859335`, final size `10429` bytes, uploaded ZIP SHA-256 `621d8515d2ad2a70a1de139f52e4f9afb54d3e3e586bc992d77cdf8a26311ee9`; `actions/deploy-pages@v4` created a Pages deployment with `pages_build_version` `d040872923644b9ade515c0e14e3649ad484d563`; evaluated environment URL `https://jackxiaozhiren.github.io/quantrisk-plus-plus/`. The job is downstream of lint through `needs: [lint]`, so the drift gate ran before publication. |

### 28.1 The live URL reading

The published site was fetched independently of the runner, from this development machine, over
HTTPS: `GET https://jackxiaozhiren.github.io/quantrisk-plus-plus/` returned HTTP `200`, TLS verify
result `0`, body `5793` bytes, `<title>QuantRisk++ evidence</title>`, carrying the
`linearisation_error_bound` and `two_factor_error_bound` page markers. The response body's SHA-256
is `692db228336617a0663446bf4181d47a4b63204d9ff156d92d852b25715d25c4`, which equals byte-for-byte
the `page_sha256` of `index.html` in the committed `build/site.lock` that the drift gate verified.
The live surface is therefore the checked bytes, not a second build whose agreement is assumed —
this is the reading X5 section 24 was written to make possible and which section 26 could not claim
before the push.

The runner's `199/199` and the development-side `200/200` in section 26 are not a disagreement:
the runner's one environment-blind plant is the re-render guard whose pdfTeX version differs from
the build sidecar, exactly the X3/X4 condition, and the development vantage has the matching
pdfTeX. Both vantages agree on every measurable plant, including the four newest ones. The runner's
`515 passed` and the development-side `585` differ by the with-oracles cases that the offline
runner skips, the same five-skip set recorded in X4's `510 passed, 5 skipped`.

### 28.2 What this backfill does and does not close

This run closes the free-tier CI publish part of DoD item 3: the site is published from the runner,
the deploy is downstream of the drift gate, and a live-URL reading exists. DoD item 3 stays
**Partial** as a whole because its offline-build part (I-L5) is still partial — the in-process
no-socket test is narrower than a network-down build. I-L3/L4/L6 and the H1–H4 values remain VOID
and 未测得 respectively: section 24 named them as subsequent units, and this backfill records the
published surface they need without claiming their measurements. No new scope unit, ceiling key,
CLI subcommand, tag, release, secret or account is introduced by this backfill.

This backfill commit is carried in the second and final ref update of the section 27 approval. Its
own run is observed-only under the section 11/14/18/22/27 recursion limit; no third ref update is
authorised and no reading in this section is a claim about that tip.

## 29. Scope unit X6 — fill I-L3/L4/L6 and measure H3 on the published surface

Scope unit X6, as put to the maintainer verbatim, with the alternatives declined beside it. X5
created a published surface; I-L3/L4/L6 stayed VOID and H3's value stayed 未测得 only because no
such surface existed. This unit reads that surface. The question put to the maintainer was which
scope sentence to open X6 under, with three options:

- **A**: pure incremental probes — fill I-L3 (a guard scans the generated site for zero
  request-execution paths, with a named plant), I-L4 (verify the CI + Pages free tier, no secret
  and no new account, with the cost basis explicitly bounded to *excluding AI tokens*), and I-L6
  (recognise `provenance --resolve --json` as the machine-readable surface, with a guard and a
  named plant); register H3's zero-drift value from X5 section 28's already-measured live-SHA
  equals locked-`index.html`. No HTTP service, no new CLI subcommand, ceiling key or dependency,
  no lock re-freeze, no tag move.
- **B**: additionally make I-L6 HTTP-reachable by having `site.py` emit a machine-readable JSON
  file published with the Pages site (still a static file, no resident service); declined because
  it rewrites the generator, re-freezes `build/site.lock`, enlarges the drift/PDF cascade and needs
  another push — chosen only if "machine-readable response surface" must be HTTP-reachable.
- **C**: minimal unit registering H3 and filling only I-L3, leaving I-L4 and I-L6 for later;
  declined because it leaves DoD item 5 Partial and I-L4/L6 VOID.

Approval original, verbatim: `方案 A（推荐）：纯增量探针，不建 HTTP 面、不碰 O11`.

Bounded effect, and nothing beyond it: new read-only guard tests plus their named plants that make
I-L3, I-L4 and I-L6 falsifiable from readings; the H3 value registered from the X5 section 28
measurement (producer curl + SHA-256, environment the development machine over HTTPS) without a
new network call in CI; the liveness and H1–H4 tables updated from those readings; and the plant,
test and claim count cascade re-derived in the same series with the report PDF and sidecar rebuilt.
Cost basis for I-L4 is bounded to the publish infrastructure (CI minutes and Pages free tier, no
secret, no new account, no paid service) and explicitly excludes the AI-token cost question O11,
which stays unadjudicated. I-L6 is recognised as the local `provenance --resolve --json` surface —
a module-path invocation, not an HTTP endpoint — so no service layer is introduced (G5/K1).
Excluded: any HTTP endpoint or resident service; any new CLI subcommand (the four-subcommand
contract stays frozen) or ceiling key; any new runtime dependency; any re-freeze of
`build/site.lock` or change to the generated page bytes; any H1/H2/H4 measurement; any tag,
release, secret, account or push (a push needs its own verbatim approval, as in X5 section 27);
any edit to the V9 historical attestation. The plant list, guards and count cascade move only as
this unit's own readings require.

## 30. X6 readings — the three liveness items and the H3 value

All readings in this section belong to the X6 working tree and are attributed to this unit's local
tip; none is a claim about a platform run. X6 makes no push (section 29). Each liveness item is
filled by a guard that reads the published surface on disk and a named plant that turns it red:

| Item | Guard | Plant | Red reading |
|---|---|---|---|
| I-L3 | `tests/python/test_interface_liveness.py::test_published_pages_carry_no_request_execution_path` (plus `test_generated_markup_source_has_no_script_template`) | `site-page-gains-a-request-execution-path` | a `<script>` injected into `DOCUMENT_HEAD` made all 20 generated pages report a request-execution path |
| I-L4 | `...::test_the_publish_chain_stays_on_the_free_tier` | `publish-chain-adds-a-paid-action` | a `vendor/paid-monitor@v1` step in the deploy job was named as outside the no-cost first-party action set |
| I-L6 | `...::test_the_machine_readable_surface_is_module_path_and_keeps_provenance` | `machine-readable-surface-drops-a-provenance-field` | dropping `revision` from the `--json` rendering made the four-field tuple guard refuse the answer |

Each plant was applied by hand in isolation, its target guard observed red, and the source restored
before the guard was re-run green; the manual readings are the mechanism, while the declared list
and the census own the measured count. The attribution pin for I-L3 needed no new entry once the
guard read `SITE_SOURCE` from disk, so the residual set stayed at its two previously named plants.

The H3 value is registered from X5 section 28's live-URL reading, without a new network call: the
live `index.html` SHA-256 `692db228...d25c4` equalled the committed lock's `page_sha256`
byte-for-byte on the publisher commit `d040872`. That reading remains attributed to the X5
runner/deployment and the development machine's HTTPS fetch; X6 only records it in the H table.

### 30.1 Count cascade and verification

- Plants `200 -> 203` (three new named plants), with the superseded-count plant's anchor moved with
  the sweep annotation to `# 203/203 planted defects rejected`.
- Python tests `516 -> 520` offline and `585 -> 589` with oracles (four new guard tests), with the
  five plant anchors, the claim-sample gold tuples, the living documents and the report PDF plus
  its sidecar re-derived from those producers. No CI job count, ceiling key, CLI subcommand, lock
  re-freeze or generated page byte changed.
- Local readings: `ruff check` all passed; `ruff format --check` 261 files (the new guard file is
  the 261st); `mypy` no issues in 79 sources; `pytest` `589 passed in 112.80s`
  (`env -u PYTHONDONTWRITEBYTECODE`, private basetemp); the drift gate printed
  `PASS: rebuilt site matches build/site.lock` with the committed lock untouched; the evidence
  verifier reported `95 OK`, `0 CHANGED`, `0 MISSING`.
- Full census at the implementation tip `e85ca04` (after the commit, because the harness refuses
  target files that differ from HEAD): `203/203 planted defects were rejected by their guard`;
  verdict `declared 203 / ran 203 / caught 203`, `non_caught []`, `unmeasurable []`, revision
  `e85ca043482fe956b352f51b4169c205efcd60e8`, both before/after `git status --porcelain` readings
  empty. The three new plants each printed `ok caught` with their names. This is the development
  vantage (`env -u PYTHONPATH`, detached worktree watching the checkout); no platform run is
  claimed and X6 makes no push (section 29).

H1, H2 and H4 stay 未测得 and I-L5 stays Partial: X6's scope (section 29) excluded them.

## 31. Push approval for X6 and its bound

Section 29 excluded a push, so section 30's liveness readings and 203/203 census are development-side
only; no platform run of the new guards or plants is claimed there. The closing question offered
push-and-backfill, push-and-open-a-new-unit without pushing, and maintain-status-quo. Approval
original, verbatim: `推送 X6 并回填（最推荐）` — the push-and-backfill branch, the same authorisation
recorded verbatim as `推送并回填（最推荐）` in sections 11, 14, 18, 22 and 27.

Bounded effect, and nothing beyond it: at most two non-forced ref updates through
`build/api_push.py`, carrying the three X6 commits (`ebca49d`, `e85ca04`, `51e0029`) together with
the commit that records this approval; read the first run produced by the push and attribute each
reading to the job that printed it — including the deploy job, which re-publishes the same
gate-verified site bytes (section 29 changed no page byte and re-froze no `build/site.lock`), so its
publication is a consequence of the already-approved X5 surface and not a wider authorisation;
write those readings into a backfill commit in this ledger, including any failure as a failure
rather than omitting it; carry that backfill commit in the second ref update. The recursion limit is
the one sections 11, 14, 18, 22 and 27 used: the backfill commit's own run is observed-only,
because a third ref update is outside this approval. No tag, release, secret or account is moved or
added; no new CLI subcommand, ceiling key, dependency or HTTP surface is introduced; the deploy job
stays downstream of the lint job's `site drift gate` through `needs: [lint]`, so a gate failure
blocks publication. H1/H2/H4, I-L5 and O11 stay out of scope.

## 32. X6's first platform run: seven jobs, the three new plants on the runner

The first ref update moved the platform from `3b98e13` to `2aa1dd8` with four commits (the three
X6 commits plus the section 31 approval record). The push needed four `api_push.py` invocations
because three were cut by `SSLEOFError`/`RemoteDisconnected` network drops; each attempt first
re-read the remote tip and found it still `3b98e13`, so no ref moved until the fourth attempt
printed `ref moved to 2aa1dd8 (non-forced fast-forward)`. The three extra invocations were covered
by the maintainer's explicit `再试一次，直到成功（推荐）` after the bounded one-retry rule had been
exhausted; they uploaded objects idempotently and did not add ref updates. The maintainer then
said `我都听你的，请按照你的思路建议进行` for the read-and-backfill stage.

Run `44318958457` (head `2aa1dd8`, push event, attempt 1, created `2026-11-18T13:56:59Z`, updated
`2026-11-18T14:13:47Z`): **success, all seven jobs green on the first attempt**. Per-job readings,
each attributed to the job that printed it:

| Job | Reading |
|---|---|
| Format and static checks | `ruff check` passed; `ruff format --check` `261 files already formatted` (the new guard file is the 261st); `clang-format` over the C++ corpus; `mypy` `Success: no issues found in 79 source files`; `docs_rederivation` `gap 0` with `derived.plants = 203` (X5's was 200); `artifact_revision` `gap 0`, `with_extras_census` `gap 0`, `lanes_documented_vs_executed` `gap 0`; refactor ceilings `13 ok / 2 SKIP`, no FAIL (the two SKIPs are `installed_user_identity_mismatch` and `plants_not_rejected_by_their_guard`, both named preconditions absent in the lint vantage — the same two keys the X5 run's lint log also skipped, so this is not an X6 change); evidence manifest `95 OK, 0 CHANGED, 0 MISSING`; `site drift gate` `PASS: rebuilt site matches build/site.lock` |
| Mutation census in a detached worktree | `203 declared = 202 measurable here + 1 environment-blind`; `202/202 planted defects were rejected by their guard`; `plant_liveness declared_plants: 203`; revision `2aa1dd813`; both `git status --porcelain` readings empty. All three X6 plants printed `ok caught` on the runner: `site-page-gains-a-request-execution-path`, `publish-chain-adds-a-paid-action`, `machine-readable-surface-drops-a-provenance-field`. The one environment-blind plant is unchanged from X3/X4/X5 (`report-source-edited-without-a-rebuild-seen-from-the-render`: runner pdfTeX 1.40.28 vs sidecar 1.40.29), so `202` here versus the development-side `203` is the known environment split, not a regression |
| Configure, build, C++ tests, Python tests | `100% tests passed out of 204` C++; Python `519 passed, 5 skipped in 226.23s` fully offline (X5's runner figure was `515 passed, 5 skipped`; the four added are X6's liveness guards, matching the development-side `585 → 589`); `7/7 checks passed`; `PASS: V9_LEDGER.md attests 5ec3fabe4fa8c83584a50b3ab66b357ae13094e9 as a strict ancestor of 2aa1dd813f02, 195 caught of 195 declared` |
| Benchmark suite against live oracles | `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 313.3s total`; `with_extras_census` `gap 0` |
| Installed wheel surface in a clean environment | wheel version `1.9.0`; `installed surface: identity holds, the list is the registry, one study ran, and the refusal named what it needed`; `tasks 19`, `validate passed 7`, `refusal.named true`; `docs_rederivation` `derived.plants = 203`, `gap 0` |
| macOS native C++ and Python parity | C++ `100% tests passed out of 204`; Python `98 passed in 2.79s` |
| Publish the evidence site (deploy) | `drift --check --out "${RUNNER_TEMP}/site-publish"` printed `PASS: rebuilt site matches build/site.lock`; `actions/upload-pages-artifact@v4` archived the two verified pages into artifact `github-pages`, ID `14433398479`, final size `10428` bytes, ZIP SHA-256 `8cf7cd33980fa45e4c630969f06d6f31226aba737f582dda543e101fc605a28d`; `actions/deploy-pages@v4` created a deployment with `pages_build_version` `2aa1dd813f025d2d72400492ae560a982a2facf0` and evaluated environment URL `https://jackxiaozhiren.github.io/quantrisk-plus-plus/`. The job stays downstream of lint through `needs: [lint]` |

### 32.1 The live-URL reading after X6

Fetched from this development machine over HTTPS, independently of the runner:
`GET https://jackxiaozhiren.github.io/quantrisk-plus-plus/` returned HTTP `200`, TLS verify result
`0`, body `5793` bytes and `<title>QuantRisk++ evidence</title>`. The body SHA-256 is
`692db228336617a0663446bf4181d47a4b63204d9ff156d92d852b25715d25c4`, equal byte-for-byte to the
`page_sha256` of `index.html` in the committed `build/site.lock` — the same value registered for H3
in section 30 and measured first in section 28. X6 changed no page byte and re-froze no lock; the
deploy ZIP's size and digest differ from X5's (`10428`/`8cf7cd33…` here versus `10429`/`621d8515…`
in section 28) because the Pages artifact is a freshly built tar whose header metadata is not the
published page bytes. The published `index.html` is byte-identical across X5 and X6, and both equal
the gate-verified lock page. This is a second platform confirmation of H3's zero-drift value; no new
network call was added to CI.

### 32.2 What this run does and does not close

The runner measured all three X6 liveness plants `ok caught`, so I-L3/L4/L6 now have platform-side
falsification readings in addition to section 30's development-side ones; the census count moved
from 200 to 203 in `docs_rederivation` and `plant_liveness`, and the offline Python count from 515
to 519 on the runner. The publish is a re-publication of the same X5 page bytes, not a new surface.
H1/H2/H4 remain 未测得, I-L5 remains Partial, I-L8 remains VOID, and O11 stays unadjudicated;
section 31 did not put them in scope. No tag, release, secret, account, ceiling key, CLI subcommand
or dependency moved. This backfill commit is carried in the second and final ref update of the
section 31 approval; its own run is observed-only under the same recursion limit, with no third ref
update authorised.

## 33. X7 scope unit — H2 provenance completeness, measured (ledger-first)

Scope unit X7, as put to the maintainer verbatim (the selected option's label):

> X7：H2 溯源完整性单点实测（最推荐）

Approval original, verbatim: `X7：H2 溯源完整性单点实测（最推荐）`

The option bound to that label defined the unit as: verify every registered record answers
`--resolve --json` with its four provenance elements intact and zero named refusals misfiring, add
a named plant that reddens the guarding test, move H2 from 未测得 to a recorded value, and
synchronise the stale section 7 status row; accept the added guard, plant, count cascade and PDF
rebuild; exclude O11, CI network calls and any re-freeze of the site lock.

The measurement口径 is fixed here before code, from `INTERFACE_ROADMAP.md` §"measurement" line for
H2 ("Collector computes the share of manifest artifacts whose recorded command resolves; ceiling is
a policy number, and the metric must be able to fail") and from the measured surface: the manifest
holds 95 artifacts, the registry 19 tasks, of which 10 carry a `headline` — the published values.
The other 9 registry artifacts are benchmark/analysis results with no headline and are named-refused
by `resolve()` by design ("records no headline"), which is not a provenance gap and must not be
counted as one. The H2 denominator is therefore the headline-bearing published-value set (10), not
19 or 95. The reading to be recorded is the share of that set whose `resolve()` returns value +
command + revision + digest together: expected 10/10, zero bare values, zero missing fields. A
named plant erasing one headline artifact's recorded digest must drop that share and redden the
guard, so the metric can fail.

Bounded effect, and nothing beyond it: add a read-only `completeness()` producer to the provenance
module, one guarding test, one named plant, the H2 row value plus the section 7 status correction,
and the mechanical count/PDF cascade those changes require. Excluded: any O11 adjudication, any
AI-token cost basis, any CI network call, any re-freeze of `build/site.lock`, any change to page
bytes, any tag, release, secret, account, ceiling key, CLI subcommand or dependency, and any H1/H4
measurement. No push is authorised by this unit; a push needs its own verbatim approval.

Recursion limit: if a later approval pushes X7, the backfill commit's own CI run is observed-only
and no third ref update is authorised, as in sections 27 and 31. I-L5, H1, H4 and O11 stay out of
scope.

## 34. X7 stage report — H2 measured from the published-value set

**Producer.** `provenance.completeness(root)` is a read-only function over the committed manifest
and registry. Its denominator is the published-value set: registry artifacts whose JSON carries a
`headline` dict — the figures the provenance surface exists to hand back. For each it calls
`resolve()` and counts four disjoint outcomes: `published` (in the set), `resolved` (returned value
+ command + revision + digest together), `refused` (a `ProvenanceRefused` named a gap), and
`incomplete` (an answer missing one element). The 9 benchmark/analysis artifacts with no headline
are named-refused by `resolve()` by design and are excluded from the denominator, so an artifact
that never published a figure is not miscounted as a provenance failure. The producer returns
counts, not a ratio, and carries no numeric literal: the ceiling belongs to the guard, so the
metric can fail.

**Reading (development vantage, committed checkout at `e48c4f8`).** published 10, resolved 10,
refused 0, incomplete 0 — coverage 10/10 over the published-value set, zero bare values, zero named
refusals misfiring. Recorded as H2's value in section 3. This is a development-side reading; a
platform reading is not claimed here.

**Guard and falsification.** `test_the_published_value_set_resolves_with_full_provenance` declares
the ceiling (published non-empty, sample present, refused and incomplete empty, resolved count
equal to published) and reads the manifest from disk directly, so the plant's target is inside the
guard's own reading closure. Plant `a-published-value-loses-its-digest` erases the recorded digest
of the sample headline artifact; the guard then reddens with a named refusal listing that artifact
(verified red, restored green by hand before the plant was registered). The plant's anchor is the
digest string, unique in the manifest. This makes H2's "complete over the published set" a
falsifiable claim rather than an adjective.

**Count cascade.** One new guard test and one new plant move the Python test count 589 → 590 (with
oracles) and 520 → 521 (offline), and the plant count 203 → 204. Five plant count anchors, the
claim-sample gold, four documents and the PDF + sidecar were re-derived from those producers. The
C++ Catch2 count (203 cases, 204 CTest tests) is a different number and was deliberately not
touched. No ceiling key, CLI subcommand, dependency, secret, account, tag or release moved; no
site byte changed and no lock was re-frozen (drift gate still `PASS`).

**Local readings.** Static three gates green (`ruff check`, `ruff format --check` 261 files,
`mypy` 79 sources); full `pytest tests/python/` `590 passed`; drift gate `PASS: rebuilt site matches
build/site.lock`; evidence manifest verified read-only with 0 CHANGED and 0 MISSING.

**Census (development vantage, clean tree at `e5440aa`).** The full sweep reports
`204 declared / 204 ran / 204 caught`, `non_caught []`, `unmeasurable []`, both
`git status --porcelain` readings empty, vantage "detached worktree; the checkout under evaluation
is watched, never written". The new plant `a-published-value-loses-its-digest` printed `ok caught`
on the sweep, so H2's falsification has a census-side reading as well as the hand red/green above.
This is the development-side count; no platform census is claimed here.

H1, H4, I-L5 and O11 stay 未测得 / Partial / unadjudicated: section 33 excluded them. I-L8 stays
VOID because not all of H1–H4 have values.

## 35. Push approval for X7 and its bound

Section 33 excluded a push, so section 34's H2 reading (10/10 over the published-value set) and
204/204 census are development-side only; no platform run of the new guard or plant is claimed
there. The closing question offered push-and-backfill, push-and-open-a-new-unit without pushing,
and maintain-status-quo. Approval original, verbatim: `推送 X7 并回填（推荐）` — the
push-and-backfill branch, the same authorisation recorded as `推送 X5 并回填（最推荐）` and
`推送 X6 并回填（最推荐）` in sections 27 and 31; it differs only in the word `（推荐）` versus
`（最推荐）` and selects the identical branch.

Bounded effect, and nothing beyond it: at most two non-forced ref updates through
`build/api_push.py`, carrying the three X7 commits (`e48c4f8`, `e5440aa`, `29c878b`) together with
the commit that records this approval; read the first run produced by the push and attribute each
reading to the job that printed it — including the deploy job, which re-publishes the same
gate-verified site bytes (section 33 changed no page byte and re-froze no `build/site.lock`), so its
publication is a consequence of the already-approved X5 surface and not a wider authorisation;
write those readings into a backfill commit in this ledger, including any failure as a failure
rather than omitting it; carry that backfill commit in the second ref update. The recursion limit is
the one sections 11, 14, 18, 22, 27 and 31 used: the backfill commit's own run is observed-only,
because a third ref update is outside this approval. No tag, release, secret or account is moved or
added; no new CLI subcommand, ceiling key, dependency or HTTP surface is introduced; the deploy job
stays downstream of the lint job's `site drift gate` through `needs: [lint]`, so a gate failure
blocks publication. H1/H4, I-L5 and O11 stay out of scope.

## 36. X7's first platform run: seven jobs, the new H2 plant on the runner

The first ref update moved the platform from `18ce9e6` to `c61e8d1` with four commits (the three
X7 commits plus the section 35 approval record). A single `api_push.py` invocation succeeded with
no network drop: every blob, tree and commit SHA matched its local object and the ref moved
`18ce9e6 → c61e8d1` as a non-forced fast-forward.

Run `44757857532` (head `c61e8d1`, push event, attempt 1, created `2026-11-20T14:53:47Z`, updated
`2026-11-20T15:13:32Z`): **success, all seven jobs green on the first attempt**. Per-job readings,
each attributed to the job that printed it:

| Job | Reading |
|---|---|
| Format and static checks | `ruff check` `All checks passed!`; `ruff format --check` `261 files already formatted` (unchanged from X5/X6 — X7 added no new source file); `clang-format` over the C++ corpus; `mypy` `Success: no issues found in 79 source files`; `docs_rederivation` `gap 0` with `derived.plants = 204` (X6's was 203), `manifest_artifacts 95`, `registry_tasks 19`; `artifact_revision` `gap 0`, `with_extras_census` `gap 0`, `lanes_documented_vs_executed` `gap 0`; refactor ceilings `13 ok / 2 SKIP`, no FAIL — the two SKIPs are `installed_user_identity_mismatch` and `plants_not_rejected_by_their_guard`, the same two preconditions absent in the lint vantage as X5/X6, so this is not an X7 change; evidence manifest `95 OK, 0 CHANGED, 0 VOLATILE, 0 MISSING, 0 on disk but not in the manifest` (`Evidence is intact.`); `site drift gate` `PASS: rebuilt site matches build/site.lock` |
| Mutation census in a detached worktree | `204 declared = 203 measurable here + 1 environment-blind`; `203/203 planted defects were rejected by their guard`; `plant_liveness declared_plants: 204`; the new plant `a-published-value-loses-its-digest` printed `ok caught` on the runner ("erasing one recorded digest makes that value name a gap and drop out of the resolved set, so the guard over the completeness producer must redden"). The one environment-blind plant is unchanged from X3/X4/X5/X6 (`report-source-edited-without-a-rebuild-seen-from-the-render`: runner pdfTeX 1.40.28 vs sidecar 1.40.29), so `203` here versus the development-side `204` is the known environment split, not a regression. Vantage "detached worktree; the checkout under evaluation is watched, never written" |
| Configure, build, C++ tests, Python tests | `100% tests passed out of 204` C++; Python `520 passed, 5 skipped in 168.05s` fully offline (X6's runner figure was `519 passed, 5 skipped`; the one added is X7's H2 completeness guard, matching the development-side `589 → 590`); `7/7 checks passed`; `PASS: V9_LEDGER.md attests 5ec3fabe4fa8c83584a50b3ab66b357ae13094e9 as a strict ancestor of c61e8d137040, 195 caught of 195 declared` |
| Benchmark suite against live oracles | `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 357.1s total` |
| Installed wheel surface in a clean environment | wheel version `1.9.0`; `installed surface: identity holds, the list is the registry, one study ran, and the refusal named what it needed`; `tasks 19`, `validate passed 7`, `refusal.named true` (task `pricing_grid`, exit 1, no empty directories left), study `mc_speed` exit 0; `docs_rederivation` `derived.plants = 204`, `gap 0` |
| macOS native C++ and Python parity | C++ `100% tests passed out of 204`; Python `98 passed in 2.47s` |
| Publish the evidence site (deploy) | `drift --check --out "${RUNNER_TEMP}/site-publish"` printed `PASS: rebuilt site matches build/site.lock`; `actions/upload-pages-artifact@v4` archived the two verified pages into artifact `github-pages`, ID `14640400978`, final size `10268` bytes, ZIP SHA-256 `36e3ecf703fdd759712371667b3e396551f145a05e59425c6be621b6664e98ed`; `actions/deploy-pages@v4` created a deployment with `pages_build_version` `c61e8d137040401c33f309e40d50eebbf497c8f6` and evaluated environment URL `https://jackxiaozhiren.github.io/quantrisk-plus-plus/`. The job stays downstream of lint through `needs: [lint]` |

### 36.1 The live-URL reading after X7

Fetched from this development machine over HTTPS, independently of the runner:
`GET https://jackxiaozhiren.github.io/quantrisk-plus-plus/` returned HTTP `200`, TLS verify result
`0`, body `5793` bytes and `<title>QuantRisk++ evidence</title>`. The body SHA-256 is
`692db228336617a0663446bf4181d47a4b63204d9ff156d92d852b25715d25c4`, equal byte-for-byte to the
`page_sha256` of `index.html` in the committed `build/site.lock` — the value registered for H3 in
section 30 and confirmed on the platform in sections 28 and 32. X7 changed no page byte and re-froze
no lock, so this is a third platform confirmation of H3's zero-drift value. The deploy ZIP's size
and digest differ from X6's (`10268`/`36e3ecf7…` here versus `10428`/`8cf7cd33…` in section 32)
because the Pages artifact is a freshly built tar whose header metadata is not the published page
bytes; the published `index.html` is byte-identical across X5, X6 and X7. No new network call was
added to CI.

### 36.2 What this run does and does not close

The runner measured the new H2 plant `a-published-value-loses-its-digest` `ok caught`, so H2's
completeness claim now has a platform-side falsification reading in addition to section 34's
development-side one (10/10 resolved, plus the hand red/green). The plant count moved from 203 to
204 in `docs_rederivation` and `plant_liveness`, and the offline Python count from 519 to 520 on the
runner. The publish is a re-publication of the same X5 page bytes, not a new surface. H1/H4 remain
未测得, I-L5 remains Partial, I-L8 remains VOID, and O11 stays unadjudicated; section 35 did not put
them in scope. No tag, release, secret, account, ceiling key, CLI subcommand or dependency moved.
This backfill commit is carried in the second and final ref update of the section 35 approval; its
own run is observed-only under the same recursion limit, with no third ref update authorised.

## 37. X8 scope unit — H4 zero cost, measured (ledger-first)

Scope unit X8, as put to the maintainer verbatim (the selected option's label):

> X8：H4 零成本实测（最推荐）

Approval original, verbatim: `X8：H4 零成本实测（最推荐）`

The option bound to that label defined the unit as: turn H4 from 未测得 into a recorded reading by
binding each of ROADMAP line 146's three assertions to an executable target, add a named plant that
reddens the guarding test, and synchronise the H4 row and the stale section 7 status line; accept
the added producer, guard, plant, count cascade and PDF rebuild; exclude O11, any paid service or
account, any CI network call and any re-freeze of the site lock.

The measurement口径 is fixed here before code, from `INTERFACE_ROADMAP.md` line 146 ("H4 — Cost
stays zero | CI log shows no paid service; hosting is the free static tier; the build's own budget
line is asserted in the report") and from the lesson recorded in
`tools/inventory_orphan_code.py`'s `external_dependencies()`: a policy file asserting a budget and a
collector returning the number it was told to return is the exact shape this repository refuses
(L12). The producer therefore returns evidence, not a zero:

1. the set of `uses:` references across every job in `.github/workflows/ci.yml`, set-differenced
   against the free first-party action set, together with the runners those jobs name and the
   absence of `secrets.` anywhere in the workflow;
2. the hosting verdict read from the deploy job — `actions/deploy-pages`,
   `permissions: pages: write` plus `id-token: write`, the `github-pages` environment, and no
   `CNAME` file in the repository, so the host is the free static tier with no custom domain;
3. the report's budget line, located and returned verbatim from `README.md`
   (`Total monetary cost of building and validating it: $0.`, line 31, unique in the repository).

A reading is those three evidence blocks; `$0` is never returned as a computed number, so the
reading cannot be satisfied by a literal that merely repeats the policy.

Bounded effect, and nothing beyond it: add a read-only `cost.audit(root)` producer to the interface
package (stdlib only, opens no socket, carries no numeric literal — the ceiling lives in the
guard), one guarding test in `tests/python/test_interface_cost.py`, one named plant
`report-drops-its-zero-cost-budget-line` editing the README budget line, the H4 row value plus the
section 7 status correction, and the mechanical count/PDF cascade those changes require. Excluded:
any O11 adjudication, any AI-token cost basis, any paid service, account or secret, any CI network
call, any re-freeze of `build/site.lock`, any change to page bytes, any committed change to
`ci.yml`, any tag, release, ceiling key, CLI subcommand or dependency, and any H1 or I-L5
measurement. No push is authorised by this unit; a push needs its own verbatim approval.

Recursion limit: if a later approval pushes X8, the backfill commit's own CI run is observed-only
and no third ref update is authorised, as in sections 27, 31 and 35. H1, I-L5, I-L8 and O11 stay
out of scope.

## 38. X8 stage report — H4 measured from the publish surface, the host and the report

**Producer.** `cost.audit(root)` is a read-only, stdlib-only function over three committed
surfaces — `.github/workflows/ci.yml`, the repository root (for a `CNAME` file) and `README.md` —
returning three evidence blocks and never a computed zero:

1. `actions` — every `uses:` reference in the workflow, set-differenced against the first-party
   free action set, with the runners the jobs name, the runners outside the free set, and whether
   any step can read a stored secret (`secrets.`);
2. `hosting` — `platform` is `github-pages` only when the deploy job uses `actions/deploy-pages`;
   `free_static_tier` is true only when that deploy also carries `pages: write`,
   `id-token: write` and the `github-pages` environment; `custom_domain` is true iff a `CNAME`
   file exists, so the default free host is asserted by the absence of one;
3. `budget_line` — the report's own budget sentence located in `README.md`, returned verbatim with
   its occurrence count, so a report that stopped asserting it makes the reading empty rather than
   silently satisfied.

The module carries no numeric literal and opens no socket: the ceiling ("paid set empty", "free
static tier", "exactly one budget line") belongs to the guard, so the reading can fail.

**Reading (development vantage, committed checkout at `f6b67b1`).** `actions.paid []`,
`actions.billed []`, `actions.stored_secret false`, runners `["macos-15", "ubuntu-latest"]` (both
GitHub-hosted free images), `hosting.platform github-pages` with `free_static_tier true` and
`custom_domain false`, `budget_line` `README.md` — `Total monetary cost of building and validating
it: $0.` — `occurrences 1`. Recorded as H4's value in section 3: the publish surface names no paid
service, the host is the free static tier with no custom domain, and the build's budget line is
asserted by a producer that reads it rather than by a policy file that declares it. `$0` is never
returned as a number, so the reading cannot be satisfied by a literal that repeats the policy — the
L12 shape this repository refuses.

**Guard and falsification.**
`test_the_zero_cost_claim_is_read_from_the_publish_surface_and_the_report` declares the ceiling
(paid and billed empty, no stored secret, every runner inside the free set, free static tier true
with no custom domain, the budget sentence present, unique and carrying the asserted value) and
reads both `ci.yml` and `README.md` from disk itself, so the plant's target sits inside the guard's
own reading closure. Plant `report-drops-its-zero-cost-budget-line` rewrites the README budget
sentence; the guard reddens on the missing sentence (verified red, restored green by hand before
the plant was registered). The plant's anchor is that sentence, unique in the repository — the
producer's own `occurrences 1` reading is the evidence for the anchor's uniqueness.

**Count cascade.** One new guard test and one new plant move the Python test count 590 → 591 (with
the `oracles` extra) and 521 → 522 (offline), and the plant count 204 → 205. Five plant count
anchors, the claim-sample gold, four documents (`interview_defense`, `limitations`,
`reproducibility`, `technical_report.tex`) and the PDF + sidecar were re-derived from those
producers. The C++ Catch2 count (203 cases, 204 CTest tests) is a different number and was
deliberately not touched. `ruff format --check` now walks 263 files and `mypy` 80 sources — the
mechanical consequence of the two new files, not a re-scoped gate. No ceiling key, CLI subcommand,
dependency, secret, account, tag or release moved; `ci.yml` is unchanged as a file; no site byte
changed and no lock was re-frozen (drift gate still `PASS`).

**Local readings.** Static three gates green (`ruff check`, `ruff format --check` 263 files,
`mypy` 80 sources); full `pytest tests/python/` `591 passed`; drift gate `PASS: rebuilt site
matches build/site.lock`; evidence manifest verified read-only with 0 CHANGED and 0 MISSING.

**Census (development vantage, clean tree at `f6b67b1`).** The full sweep reports
`205 declared / 205 ran / 205 caught`, `non_caught []`, `unmeasurable []`, both
`git status --porcelain` readings empty, vantage "detached worktree; the checkout under evaluation
is watched, never written". The new plant `report-drops-its-zero-cost-budget-line` printed
`ok caught` on the sweep, so H4's falsification has a census-side reading as well as the hand
red/green above. This is the development-side count; no platform census is claimed here.

**Excluded, as section 37 bounded it.** O11 stays unadjudicated — the AI-token question is a
different cost basis that a workflow scan does not answer — and no paid service, account or secret
was added or read, no CI network call was made, `build/site.lock` was not re-frozen, and no push is
authorised by this unit. H1 and I-L5 stay 未测得 / Partial, so I-L8 stays VOID.

## 39. Push approval for X8 and its bound

Section 37 excluded a push, so section 38's H4 reading (paid set empty, free static tier, one
budget line) and the 205/205 census are development-side only; no platform run of the new guard or
plant is claimed there, and section 3's H4 row still carries "No runner reading claimed until a
platform run observes it". The closing question offered push-and-backfill, opening a new unit
without pushing, and maintaining the status quo. Approval original, verbatim:
`推送 X8 并回填（最推荐）` — the push-and-backfill branch, the same authorisation recorded as
`推送 X5 并回填（最推荐）`, `推送 X6 并回填（最推荐）` and `推送 X7 并回填（推荐）` in sections 27,
31 and 35.

Bounded effect, and nothing beyond it: at most two non-forced ref updates through
`build/api_push.py`, carrying the three X8 commits (`71c56f9`, `f6b67b1`, `0dec968`) together with
the commit that records this approval; read the first run produced by the push and attribute each
reading to the job that printed it — including the deploy job, which re-publishes the same
gate-verified site bytes (section 38 changed no page byte and re-froze no `build/site.lock`), so its
publication is a consequence of the already-approved X5 surface and not a wider authorisation;
write those readings into a backfill commit in this ledger, including any failure as a failure
rather than omitting it; carry that backfill commit in the second ref update. The recursion limit
is the one sections 11, 14, 18, 22, 27, 31 and 35 used: the backfill commit's own run is
observed-only, because a third ref update is outside this approval. No tag, release, secret or
account is moved or added; no new CLI subcommand, ceiling key, dependency or HTTP surface is
introduced; the deploy job stays downstream of the lint job's `site drift gate` through
`needs: [lint]`, so a gate failure blocks publication. H1, I-L5, I-L8 and O11 stay out of scope.

## 40. X8's first platform run: seven jobs, the H4 plant on the runner

**Run.** `44861172789`, `run_attempt` 1, `push` event, head `47c41a3`, created 03:26:55Z and
finished 03:53:09Z — seven jobs, all `success`, no rerun. Each reading below is attributed to the
job that printed it.

- **Format and static checks.** `ruff` "All checks passed!", `ruff format` 263 files,
  `clang-format` refusal gate green, `mypy` 80 source files; `refactor ceilings` 13 ok / 2 SKIP —
  the same pair of SKIPs as sections 28, 30, 32 and 36, each reporting the installed-surface
  precondition absent from a vantage that did not run that lane.
- **Configure, build, C++ tests, Python tests.** CTest 204/204; pytest offline lane
  `521 passed, 5 skipped` (X7's runner reading was 520, so the +1 is the H4 guard and nothing
  else); `validate` 7/7. The runner lane's total is not the same number as the development-side
  oracles count and is not made to look like it.
- **macOS native parity.** C++ 204/204 and 98 passed.
- **Installed wheel surface.** `quantrisk-1.9.0-cp312-cp312-linux_x86_64.whl`, identity version
  `1.9.0`, registry parity of `run --list`, `validate` 7/7, one offline study ran, and the refusal
  named what it needed; verdict artifact 580 bytes.
- **Benchmark suite.** `19/19 executed and passed`, 0 aggregated from disk, 0 failed, 0 skipped,
  362.1 s.
- **Mutation census.** `204 measurable + 1 environment-blind` = the 205 declared plants; `204/204`
  caught, `non_caught []`, and the single `unmeasurable` entry is
  `report-source-edited-without-a-rebuild-seen-from-the-render` (runner pdfTeX 1.40.28 against the
  1.40.29 recorded in `paper/technical_report.build.json`), the same environment-blind plant as
  X6 and X7; `git status --porcelain` empty before and after; revision `47c41a3`; verdict artifact
  `mutation-census`, 4361 bytes, ID 14690054593. The new plant
  `report-drops-its-zero-cost-budget-line` printed `ok caught` on the runner, so H4's falsification
  now has a runner-side reading in addition to the hand red/green in section 38. The census job is
  the long pole on this run, which is why the run took 26 minutes against X7's 10.
- **Publish the evidence site.** `python -m quantrisk.interface.drift --check` printed
  `PASS: rebuilt site matches build/site.lock` inside the deploy job as well as in the lint job;
  the verified bytes were uploaded as `github-pages` artifact ID 14688944568 (10265 bytes) and
  deployed with `pages_build_version` = `47c41a3`, environment URL
  `https://jackxiaozhiren.github.io/quantrisk-plus-plus/`.

**Live re-read.** HTTP 200, TLS verify 0, 5793 bytes, SHA-256
`692db228336617a0663446bf4181d47a4b63204d9ff156d92d852b25715d25c4` — byte-for-byte equal to
`build/site.lock`'s `index.html` `page_sha256`. This is the fourth platform confirmation of H3's
zero drift (sections 28, 30, 32 and here). The deploy artifact moved 10268 → 10265 bytes between
X7 and X8 while the page bytes did not move at all: the difference is tar metadata, not content,
which is why the lock check and not the ZIP size is the gate.

**Recorded, not smoothed.** The deploy job emits a Node.js 20 deprecation warning for
`actions/deploy-pages@v4` and `actions/upload-artifact`. It is a runner warning, not a failure, and
it is written here rather than omitted because a warning is the shape of a future break.

**Section 3 corrections carried in this backfill.** The closing clause of the H2 and H4 rows, "No
runner reading claimed until a platform run observes it", is stale as of this section: the guards
those rows name executed on the runner as the plant being falsified and reddened there
(`a-published-value-loses-its-digest` in section 36, `report-drops-its-zero-cost-budget-line`
here), while the producers' own output is printed by no CI step, so each row now says exactly that
instead of claiming more or less.

This backfill commit is carried in the second and final ref update of the section 39 approval; its
own run is observed-only under the same recursion limit, and no third ref update is authorised. H1,
I-L5, I-L8 and O11 stay out of scope.

## 41. X9 scope unit — H1 cold start, measured (ledger-first)

Scope unit X9, as put to the maintainer verbatim (the selected option's label):

> X9：H1 冷启动复现（最推荐）

Approval original, verbatim: `X9：H1 冷启动复现（最推荐）`

The option bound to that label defined the unit as: turn H1 from 未测得 into a recorded reading by
scripting the run `INTERFACE_ROADMAP.md` line 143 defines, add the producer, the guarding test and
a named plant, and synchronise the H1 row and the stale section 7 status line; accept the added
tool, producer, guard, plant, record, count cascade and PDF rebuild; exclude O11, I-L5, any paid
service or account, any CI change, and any push.

**The measurement口径 is fixed here, before code, from line 143 verbatim** — "Scripted run: fresh
venv, neutral cwd, one command from install-listing to artifact; assert the run needs zero repo
checkout and zero prior file names; record wall clock" — and is discharged as follows:

1. **fresh venv** — the environment root is created outside the checkout and its resolved path is
   recorded; the installed package must import from inside that root, and neither the root nor the
   import path may sit under the checkout (the editable-install failure `assert_identity` in
   `tools/verify_installed_surface.py` already names).
2. **neutral cwd** — the working directory is created outside the checkout, empty before the run,
   and its resolved path is recorded.
3. **one command from install-listing to artifact** — exactly one subprocess invocation between
   "the environment is ready" and "the artifact exists": `quantrisk run mc_speed --out
   cold-start-out`, with the CLI resolved inside the venv. The count is recorded and the guard
   holds it to one; a second invocation would be a second command.
4. **zero repo checkout** — no argv element names the checkout or any path inside it, the cwd and
   venv roots lie outside it, and the run consumes no committed artifact from it. The tool refuses
   to write a record if any of those is false.
5. **zero prior file names** — every argv element that names a filesystem path must be absent
   before the run; the record carries the list of argv elements that already existed, and the
   guard requires it to be empty. The task id is the one the installed `run --list` prints, not a
   name copied from a document.
6. **wall clock** — `time.perf_counter` around that single command, recorded as `run.wall_seconds`,
   with the install duration recorded separately as `install.wall_seconds`; the two are never
   conflated, because only the first is "one command".

**Reproduction of a published number, and its limit.** `mc_speed` is the only registered task that
declares no extra, so it is the only one a bare wheel can serve. Its deterministic fields
(`analytic_reference_price`, `measured_prices`) are compared for exact equality against the
committed `benchmarks/performance/results/monte_carlo_speed.json`, and the tool refuses to write a
record if they differ. Its wall-clock fields (`speedup_vs_*`, `results_seconds`) are **explicitly
not compared and not claimed**: they move with machine load, and asserting otherwise would be the
fabrication this ledger exists to prevent. The record states that exclusion rather than leaving it
to be inferred.

Bounded effect, and nothing beyond it: add `tools/cold_start.py` (the scripted run; stdlib plus
`subprocess`, invoking `uv` and the venv's own binaries), a read-only
`coldstart.audit(record)` producer in the interface package (stdlib, no numeric literal, no socket),
one guarding test in `tests/python/test_interface_coldstart.py`, one committed record
`tools/cold_start_record.json` written by an actual run on a clean tree, one named plant, the H1 row
value plus the section 7 status correction, and the mechanical count/PDF cascade those require.
The install step inside the fresh venv may fetch `numpy` and `pandas` from the package index — that
is the user's own install cost and is recorded as such; it is not a CI network call and adds no
service, account or secret. Excluded: any O11 adjudication, any I-L5 work, any change to
`.github/workflows/ci.yml`, any new CLI subcommand, dependency, ceiling key, tag or release, any
re-freeze of `build/site.lock`, any change to a published page byte, any membership change to
`evidence/manifest.json` (the record is a reading, not a manifest artifact), and any assertion about
the wall-clock fields of the benchmark. No push is authorised by this unit; a push needs its own
verbatim approval.

Recursion limit: if a later approval pushes X9, the backfill commit's own CI run is observed-only
and no third ref update is authorised, as in sections 27, 31, 35 and 39. I-L5, I-L8 and O11 stay
out of scope.

## 42. X9 stage report — H1 measured from a wheel, one command, one empty directory

**Tool.** `tools/cold_start.py` performs the run line 143 defines, in the order a reader would meet
it: build a wheel from this tree (`uv build --wheel`, 17.5 s), create a venv on the same
interpreter outside the checkout (`uv venv`, 0.03 s), install that wheel into it (`uv pip install`,
210.8 s on a cold index cache and 0.1 s against a warm one), run two probes — an import-identity
read and `run --list`, which prints `19 registered tasks` — and then execute exactly one command
from an empty working directory. It writes `tools/cold_start_record.json` only after re-deriving
the reproduction, so a run that failed to reproduce cannot produce a record claiming it did.

**Reading (development vantage, clean tree at `485f91a`, record refreshed at `b19321a`).** The one
command is `quantrisk run mc_speed --out cold-start-out`, executed in **0.611 s** (1.354 s on the
first, cold-cache run) from an empty directory; `existing_paths_before []`, `subprocess_invocations
1`, and both the venv root and the cwd lie outside the checkout by resolved path. The artifact
written under that directory is 4218 bytes, SHA-256 `1feb1ee9abd5…`, and its five deterministic
fields equal the committed `benchmarks/performance/results/monte_carlo_speed.json` exactly:
`analytic_reference_price` 11.123761928058133, `measured_prices`, `reported_standard_errors`,
`paths_per_run`, `option`. Recorded as H1's value in section 3.

**What the reading does and does not claim.** It claims a wheel built from this tree, in an
environment outside the checkout, reproduces a published number with one command and no prior file
name. It does **not** compare `results_seconds`, `speedup_vs_numpy`, `speedup_vs_pure_python` or
`speedup_vs_pure_python_using_min`: two runs on the same machine disagree on every one of them, and
the record says so in `reproduction.not_compared_because` rather than leaving a reader to assume
the whole artifact matched. The install was a real index install (`install.mode "index"`, nothing
seeded); the tool also carries a seeded fallback for a machine whose index is unreachable, and
would record that mode with its reason instead of silently passing.

**Guard and falsification.**
`test_the_cold_start_records_one_command_from_an_empty_directory_outside_the_checkout` re-derives
the equality from the committed artifact instead of trusting the record's own `equal` flag, holds
the invocation count to one, requires `existing_paths_before []`, requires both clocks positive,
and requires the install mode to be one of the two named ones — with the seeded case required to
name its reason and to prove `quantrisk` was not among the seeded distributions. Plant
`cold-start-record-quotes-a-price-the-published-artifact-does-not-hold` truncates the recorded price
to `11.1237619`; the guard reddens on the mismatch and greens when restored (verified by hand before
the plant was registered).

**A fact about the plant that is worth recording.** The first attempt moved the recorded price by
one unit in the last decimal place (`…133` → `…134`) and the guard stayed **green**: at magnitude
11.1 the two literals parse to the same float64, so the mutation changed the text without changing
the value. The plant was rewritten to a truncation that is actually distinguishable. A plant whose
edit does not move the parsed value tests nothing, and this is the only place in the repository
where that trap has been observed and written down.

**Count cascade.** One new guard test and one new plant move the Python test count 591 → 592 (with
the `oracles` extra) and 522 → 523 (offline), and the plant count 205 → 206. Five plant count
anchors, the claim-sample gold, four documents (`interview_defense`, `limitations`,
`reproducibility`, `technical_report.tex`) and the PDF + sidecar were re-derived from those
producers. `ruff format --check` now walks 266 files and `mypy` 82 sources — the three new modules.
The C++ Catch2 count (203 cases, 204 CTest tests) is a different number and was deliberately not
touched. No ceiling key, CLI subcommand, dependency, secret, account, tag or release moved; no site
byte changed and no lock was re-frozen; `evidence/manifest.json` is unchanged, because the record is
a reading and not a manifest artifact (asserted by the verifier still reading 95 artifacts, 0
CHANGED, 0 MISSING).

**Local readings.** Static three gates green (`ruff check`, `ruff format --check` 266 files, `mypy`
82 sources); full `pytest tests/python/` `592 passed`; drift gate `PASS: rebuilt site matches
build/site.lock`; evidence manifest verified read-only with 0 CHANGED and 0 MISSING.

**Census (development vantage, clean tree at `b19321a`).** The full sweep reports
`206 declared / 206 ran / 206 caught`, `non_caught []`, `unmeasurable []`, both
`git status --porcelain` readings empty, vantage "detached worktree; the checkout under evaluation
is watched, never written". The new plant
`cold-start-record-quotes-a-price-the-published-artifact-does-not-hold` printed `ok caught`. This is
the development-side count; no platform census is claimed here.

**Two corrections carried, and why one of them is slightly wider than section 41's sentence.**
Filling the H1 row is the first. The second: section 2's I-L8 row read `VOID` with the reason "no
measured H1–H4 value exists to map to a recorded run", and section 7 item 5 said the same. This
unit makes that reason false, so both now read `Partial` with the actual state — the precondition is
met, but the report-wide audit that maps every value claim to a recorded run has not been run, so the
law is not claimed as filled. Rewriting a row the unit itself falsified is a correction, not a scope
expansion; leaving it would be the stale-sentence defect this ledger keeps recording in others.

## 43. Push approval for X9 and its bound

Section 41 excluded a push, so section 42's H1 reading (one command from an empty directory outside
the checkout, five deterministic fields reproduced) and the 206/206 census are development-side
only; no platform run of the new guard or plant is claimed there, section 3's H1 row carries "No
runner reading claimed: no CI step runs this tool", and I-L8 reads `Partial` only because H1–H4 now
all have values. The closing question offered push-and-backfill, opening a new unit without pushing,
and maintaining the status quo. Approval original, verbatim:
`推送 X9 并回填（最推荐）` — the push-and-backfill branch, the same authorisation recorded as
`推送 X5 并回填（最推荐）`, `推送 X6 并回填（最推荐）`, `推送 X7 并回填（推荐）` and
`推送 X8 并回填（最推荐）` in sections 27, 31, 35 and 39.

Bounded effect, and nothing beyond it: at most two non-forced ref updates through
`build/api_push.py`, carrying the four X9 commits (`e81bff3`, `485f91a`, `b19321a`, `244d544`)
together with the commit that records this approval; read the first run produced by the push and
attribute each reading to the job that printed it — including the deploy job, which re-publishes the
same gate-verified site bytes (section 41 changed no page byte and re-froze no `build/site.lock`), so
its publication is a consequence of the already-approved X5 surface and not a wider authorisation;
write those readings into a backfill commit in this ledger, including any failure as a failure
rather than omitting it; carry that backfill commit in the second ref update. The cold-start reading
itself is a development-side measurement: no CI step runs `tools/cold_start.py`, and the two CI-side
facts this push can confirm are that the H1 guard compiles and runs green in the lint lane and that
its paired plant reddens under the mutation census; the producer's numeric reading is not claimed as
a runner reading. The recursion limit is the one sections 11, 14, 18, 22, 27, 31, 35 and 39 used:
the backfill commit's own run is observed-only, because a third ref update is outside this approval.
No tag, release, secret or account is moved or added; no new CLI subcommand, ceiling key, dependency
or HTTP surface is introduced; the deploy job stays downstream of the lint job's `site drift gate`
through `needs: [lint]`, so a gate failure blocks publication. I-L5, I-L8 and O11 stay out of scope.

## 44. X9 platform run and live re-publication (backfill)

First run of the section 43 approval: `44999227131`, head `b202e765ca47`, push event, attempt 1,
seven jobs all `success`, created `2026-11-22T07:39:34Z`, updated `08:04:22Z` (about 25 minutes;
the mutation census is the long pole). Attribution below is to the job that printed each reading.

- **Format and static checks** — `ruff check`: All checks passed; `ruff format --check`: 266 files
  already formatted (X8 was 263, plus X9's three new Python files); `mypy python/quantrisk tools`:
  no issues in 82 source files (X8 was 80). `refactor ceilings`: 13 ok / 2 SKIP, unchanged from
  X5–X8, with `plants_not_rejected_by_their_guard` a deliberate SKIP in this lint vantage (the
  census verdict is not present there) and later `ok ... 0 against a ceiling of 0 due P3.2` in the
  census job. `evidence manifest`: 95 OK, 0 CHANGED, 0 MISSING. `site drift gate`: PASS — rebuilt
  site matches `build/site.lock`. `revision b202e765c`.
- **Configure, build, C++ tests, Python tests** — CTest 100% of 204 passed (X8: 204). Python tests
  fully offline: **522 passed, 5 skipped** (X8: 521 — the +1 is the H1 cold-start guard,
  `test_the_cold_start_records_one_command_from_an_empty_directory_outside_the_checkout`, which
  compiles and runs green in this lane). `Validate installed CLI`: 7/7 checks passed. Final-tip
  census attestation PASS: V9_LEDGER.md attests `5ec3fabe4fa8` as a strict ancestor of
  `b202e765ca47`, 195 caught of 195 declared (the historical, fixed ancestor reading, not today's).
- **Benchmark suite against live oracles** — suite 19/19 executed and passed, 0 aggregated from
  disk, 0 failed, 0 skipped, 278.1 s total.
- **Mutation census in a detached worktree** — `206 declared = 205 measurable here + 1
  environment-blind`, `205/205 planted defects were rejected by their guard`, `non_caught []`,
  the single unmeasurable entry being the recurring pdfTeX-version blind spot (`report-source-edited-
  without-a-rebuild-seen-from-the-render`: this machine's pdfTeX 1.40.28 vs 1.40.29 recorded in
  `paper/technical_report.build.json`). `checkout_status_before` and `after` both empty, verdict
  revision `b202e765ca4735214812eb3570908764505cc03f`, vantage a detached worktree that watches
  the checkout without writing it. **The new plant
  `cold-start-record-quotes-a-price-the-published-artifact-does-not-hold` is `ok caught`** — H1's
  falsifiability has platform-side backing: truncating the recorded price reddens the H1 guard on
  the runner. This is the second of the two CI-side facts section 43 said this push could confirm.
- **Installed wheel surface in a clean environment** — wheel `quantrisk-1.9.0-cp312-cp312-
  linux_x86_64`, installed from this tree outside the checkout; `"version": "1.9.0"`, `"tasks": 19`,
  `validate` passed 7/7, `refusal.named: true`, identity holds (module resolves under the installed
  venv prefix), with-extras census 19/19. No CI step runs `tools/cold_start.py`, so none of the
  cold-start reading's wall-clock numbers are runner readings here.
- **macOS native C++ and Python parity** — CTest 100% of 204 passed; Python 98 passed in 2.84 s.
- **Publish the evidence site** — downstream of lint through `needs: [lint]`; `Rebuild and verify
  the published bytes`: PASS (drift check); github-pages artifact 10264 bytes (artifact ID
  14745157434), `pages_build_version=b202e765ca4735214812eb3570908764505cc03f`, environment URL
  `https://jackxiaozhiren.github.io/quantrisk-plus-plus/`. Section 41 changed no page byte and
  re-froze no `build/site.lock`, so this publication is the already-approved X5 surface rebuilding
  the same gate-verified bytes, not a wider authorisation.

**Live URL, fifth platform confirmation of H3 zero drift** — measured from the development machine
at reading time: HTTP 200, TLS verify 0, 5793 bytes, `<title>QuantRisk++ evidence</title>`, page
SHA256 `692db228336617a0663446bf4181d47a4b63204d9ff156d92d852b25715d25c4` — byte-for-byte equal
to the `index.html` `page_sha256` in the committed `build/site.lock`, unchanged from X5–X8. The
deploy ZIP (10264 bytes here vs 10265 at X8) differs only in tar metadata; the page bytes do not
move.

**H1's own reading stays development-side, by construction.** No CI step runs
`tools/cold_start.py` (section 41 excluded a `.github/workflows/ci.yml` change, and section 43
carried that exclusion forward). What the platform confirms here is narrower and stated as such:
the H1 guard runs green in the lint lane (522 passed, +1 over X8) and its paired plant reddens under
the census (205/205). The producer's numbers — 0.611 s for one command from an empty directory,
the five reproduced fields — remain the development-side reading of sections 41–42, not a runner
claim. I-L5, I-L8 and O11 stay out of scope.

This backfill commit is carried in the second and final ref update of the section 43 approval; its
own run is observed-only under the same recursion limit, and no third ref update is authorised.

## 45. X10 scope unit — report-level claim-to-run mapping audit (ledger-first)

Scope unit X10, as put to the maintainer verbatim (the selected option's label):

> X10：报告级映射审计（最推荐）

Approval original, verbatim: `X10：报告级映射审计（最推荐）`

The option bound to that label defined the unit as: turn I-L8 from `Partial` into `Filled` by running
the report-wide audit the roadmap line 302 acceptance test names — "Every value claim in the report
maps to a recorded run; unmapped claims are deleted" — over the section 3 H1–H4 measurement ledger,
add the read-only producer, the guarding test and a named plant, and fill the I-L8 row and the stale
section 7 status line; accept the added producer module, guard, plant, I-L8 and section 7 corrections
and the mechanical count/PDF cascade. Exclude O11, I-L5, any change to `.github/workflows/ci.yml`,
to `build/site.lock`, to any committed record or artifact, and any push.

**The report face is fixed here, before code.** "The report" for this law is the section 3
H1–H4 measurement ledger's Value column — the four value claims the project publishes about its own
measurements. The claim-inventory guards in `test_artifact_metadata.py` already police the
`<number> <noun>` claims in README, the reproducibility doc and the paper, so this unit does not
re-scan that corpus; it closes the different gap that section 3's four H values have no guard that
binds each claim back to the committed run that produced it. Each of the four claims maps to the
record already committed for it by the unit that measured it:

1. **H1** — the claim's `analytic_reference_price` and the one-command timing map to
   `tools/cold_start_record.json` (`reproduction.produced`, `run.wall_seconds`) and the published
   artifact that record names (`reproduction.published_artifact`).
2. **H2** — the claim's `10/10` coverage and zero refusals map to `provenance.completeness()` over
   the committed manifest and registry.
3. **H3** — the claim's live index SHA-256 maps to the committed `build/site.lock`
   `index.html` `page_sha256`.
4. **H4** — the claim's empty paid set, free static tier and one `$0` budget line map to
   `cost.audit()` over the committed workflow and README.

**The audit is read-only and derives every number.** A new read-only producer
`claimmap.audit(root)`, in the interface package (stdlib, no numeric literal, no socket, no write),
returns for each hypothesis the claim text, the record path it maps to, the reading re-derived from
that committed record, and whether the claim's quoted figure is present in that reading; it returns
the mapped and unmapped sets rather than a bare ratio, and names any claim whose record cannot be
read. The guarding test re-derives those readings independently from the same committed records —
it never trusts a `mapped` flag the producer typed — and declares the ceiling that all four claims
are mapped and none unmapped. A named plant edits one quoted figure in the section 3 H table so the
guard reddens; the guard reads the ledger file itself so the pairing audit's text-link check names
the mutation. An unmapped claim is a defect to fix in the report, not a number to waive.

Bounded effect, and nothing beyond it: add `python/quantrisk/interface/claimmap.py`, one guarding
test module `tests/python/test_interface_claimmap.py`, one named plant, the I-L8 row filled with the
producer/guard/plant triple and the section 7 status correction, and the mechanical count/PDF
cascade those require. Excluded: any O11 adjudication, any I-L5 work, any change to
`.github/workflows/ci.yml`, to `build/site.lock`, to `tools/cold_start_record.json`, to
`evidence/manifest.json` or to any published artifact, any new CLI subcommand, dependency, ceiling
key, tag or release, any re-freeze of the site, any live-URL fetch or socket open, and any push. The
three producer readings reused here were taken by the units that measured H1/H2/H4 and X5's lock
reading for H3; this unit re-reads them from disk and does not re-measure or re-assert them.

Recursion limit: if a later approval pushes X10, the backfill commit's own CI run is observed-only
and no third ref update is authorised, as in sections 27, 31, 35, 39 and 43. I-L5 and O11 stay out
of scope.

## 46. X10 local stage reading — all four H claims map to their records (no push)

Scope section 45 was committed first (`0188239`), then the implementation (`df6ccee`, clean tree).
This section records only readings taken at that commit; section 45 excluded any push, CI run,
live-URL fetch, record rewrite or artifact re-freeze, so nothing below is a platform claim.

**The producer and its four readings.** `claimmap.audit(root)` reads the section 3 H table and the
four committed records afresh. At `df6ccee` it returned `mapped` with all four identifiers and empty
`unmapped`/`refused`: H1's price `11.123761928058133` is present in the H1 claim and comes from
`tools/cold_start_record.json`'s reproduced artifact; H2's `10/10` is rebuilt from
`provenance.completeness()`'s resolved and published sets; H3's index SHA
`692db228336617a0663446bf4181d47a4b63204d9ff156d92d852b25715d25c4` is read from the committed
`build/site.lock`; H4's budget sentence is the line returned by `cost.audit()` from `README.md`.
No figure is typed into the producer: its source is scanned for numeric literals by the guard and
contains none, and an unreadable record is a named refusal rather than a suppressed claim.

**Guard and falsification.** `test_every_h_value_claim_maps_to_its_recorded_run` re-derives all four
figures from disk independently of the producer's own `mapped` list, requires each to appear in the
ledger value it re-reads, then compares the producer's per-claim figures and sets to that derivation.
It names `INTERFACE_LEDGER.md` directly so the pairing audit binds a ledger mutation to this guard.
The plant `claim-map-drops-a-recorded-figure-from-the-report` removes the cold-start price from the
published H1 claim; a red-to-green hand check confirmed the guard reddens before the fix and passes
after. The plant is therefore a falsification of the mapping law, not a restatement of it.

**Mechanical cascade and local gates.** Plant count 206 → 207, collected pytest tests 523 → 524,
generated pytest tests 592 → 593; Catch2's 204 cases do not move. The I-L8 row in section 2 and the
section 7 item 5 status line were filled, the stale H1 wall-clock in section 7 corrected to this
unit's recorded `0.611 s`, four documents and the paper were re-derived, the PDF and its build
sidecar rebuilt, the five plant-count anchors and the claim-gold inventory updated to the new
counts. Locally: `ruff check .`, `ruff format --check .` (268 files) and
`mypy python/quantrisk tools` (83 sources) all pass; pytest reports 593 passed; the drift gate
reports PASS against the unchanged frozen site; the evidence verifier reports 95 OK, 0 CHANGED,
0 MISSING. No workflow, lock, record, manifest or published artifact was changed by this unit.

**Full census at `df6ccee`.** `207 declared = 207 ran = 207 caught`, `non_caught []`,
`unmeasurable []`, checkout porcelain empty before and after, vantage a detached worktree that
watches the checkout without writing it; elapsed 13m58s. The new plant is `ok caught`, so the
report-level mapping guard is falsifiable at the full-sweep vantage as well. Unlike the runner
census in sections 28/32/36/40/44, this development-side sweep has no environment-blind entry:
the pdfTeX version mismatch does not arise here.

**Boundary.** I-L8 is `Filled` on this local reading: every one of the four published H values maps
to the run that recorded it, and the mapping has a named, census-confirmed falsifier. This does not
fill I-L5 (true offline build) and does not adjudicate O11. No CI run is claimed, no live URL was
fetched, no ref was updated, and no push is authorised by section 45; a later push needs its own
verbatim approval and remains subject to that section's recursion limit.

## 47. Push approval for X10 and its bound

Section 45 excluded a push, so section 46's claim-map readings (four H claims mapped to their
records, I-L8 `Filled`, census 207/207) are development-side only; no platform run of the new
guard or plant is claimed there. The closing question offered push-and-backfill, opening a new
local unit without pushing, and maintaining the status quo. Approval original, verbatim:
`推送 X10 并回填（最推荐）` — the push-and-backfill branch, the same authorisation recorded as
`推送 X5 并回填（最推荐）`, `推送 X6 并回填（最推荐）`, `推送 X7 并回填（推荐）`,
`推送 X8 并回填（最推荐）` and `推送 X9 并回填（最推荐）` in sections 27, 31, 35, 39 and 43.

Bounded effect, and nothing beyond it: at most two non-forced ref updates through
`build/api_push.py`, carrying the three X10 commits (`0188239`, `df6ccee`, `bbabef6`) together with
the commit that records this approval; read the first run produced by the push and attribute each
reading to the job that printed it, including the deploy job, which re-publishes the same
gate-verified site bytes (section 45 changed no page byte and re-froze no `build/site.lock` and no
`evidence/manifest.json`), so its publication is a consequence of the already-approved X5 surface
and not a wider authorisation; write those readings into a backfill commit in this ledger, including
any failure as a failure rather than omitting it; carry that backfill commit in the second ref
update. The two CI-side facts this push can confirm are that the new claim-map guard compiles and
runs green in the lint lane (one more pytest than X9) and that its paired plant
`claim-map-drops-a-recorded-figure-from-the-report` reddens under the mutation census; the
producer's four mapped readings themselves remain the development-side disk re-derivations of
section 46, not runner-only measurements. The recursion limit is the one sections 11, 14, 18, 22,
27, 31, 35, 39 and 43 used: the backfill commit's own run is observed-only, because a third ref
update is outside this approval. No tag, release, secret or account is moved or added; no new CLI
subcommand, ceiling key, dependency or HTTP surface is introduced; the deploy job stays downstream
of the lint job's `site drift gate` through `needs: [lint]`, so a gate failure blocks publication.
I-L5 and O11 stay out of scope; this push does not adjudicate either.

## 48. X10 platform run and live re-publication (backfill)

**Run identity** — `45011233588`, attempt 1, head `1a4fc69ad4671db83ca41b02aee7606534d0744e`,
created `2026-11-22T10:11:48Z`, completed `2026-11-22T10:37:54Z`, conclusion `success`. Seven jobs,
all `completed` / `success`, attributed below to the job that printed each reading. This is the
first run of the section 47 push and the only one whose readings are backfilled here. The three
SSL EOFs seen while moving the first ref were transport-level; each time the remote ref was re-read
through the API and still read `e59ece8`, so no partial ref update existed, and the eventual ref
move carried all four commits with local SHA equal to remote SHA.

- **Format and static checks** — `ruff format --check`: 268 files already formatted; `ruff check`
  all checks passed; `mypy python/quantrisk tools`: no issues in 83 source files. `site drift gate`:
  `PASS: rebuilt site matches build/site.lock`. `evidence manifest`: 95 OK, 0 CHANGED, 0 MISSING.
  Reflector ceilings report 13 `ok ... 0 against a ceiling of 0` lines and no unmet ceiling; the
  `plants_not_rejected_by_their_guard` entry is a SKIP in this lint vantage (the census verdict is
  not present there), matching X5–X9, and reads `ok ... 0 against a ceiling of 0 due P3.2` in the
  census job below. `claim-gold` / `docs_rederivation_gap` / `lanes_documented_vs_executed_gap`
  each close at 0, so the new count cascade is attested on the runner as well.
- **Configure, build, C++ tests, Python tests** — CTest 100% of 204 passed; Python tests fully
  offline: **523 passed, 5 skipped** (X9: 522 — the +1 is the new
  `test_every_h_value_claim_maps_to_its_recorded_run`, which compiles and runs green in this lane).
  `Validate installed CLI`: 7/7 checks passed. Final-tip attestation PASS: V9 attests
  `5ec3fabe4fa8` as a strict ancestor of `1a4fc69ad467`, 195 caught of 195 declared (the fixed
  historical reading, not today's).
- **Mutation census in a detached worktree** — `207 declared = 206 measurable here + 1
  environment-blind`, `206/206 planted defects were rejected by their guard`, `non_caught []`, the
  single unmeasurable entry the recurring pdfTeX-version blind spot (`report-source-edited-
  without-a-rebuild-seen-from-the-render`: runner pdfTeX 1.40.28 vs the 1.40.29 recorded in
  `paper/technical_report.build.json`; on this runner the re-render guard is blind to its own
  typesetter). Checkout porcelain empty before
  and after, vantage a detached worktree watching the checkout without writing it. **The new plant
  `claim-map-drops-a-recorded-figure-from-the-report` is `ok caught`** — I-L8's report-level mapping
  has platform-side falsification: removing the figure the cold-start record holds from the H1 claim
  reddens the guard on the runner. Census artifact ID `14750717474` (4400 bytes).
- **Installed wheel surface in a clean environment** — wheel `quantrisk-1.9.0-cp312-cp312-
  linux_x86_64`, installed from this tree outside the checkout; `"version": "1.9.0"`, `"tasks": 19`,
  validate 7/7, `refusal.named: true`, identity holds, with-extras census 19/19. Artifact
  `installed-surface` ID `14750116782` (580 bytes). No CI step runs `tools/cold_start.py`, so no
  cold-start wall-clock number is a runner reading here.
- **Benchmark suite against live oracles** — suite 19/19 executed and passed, 0 aggregated from
  disk, 0 failed, 0 skipped, 247.1 s total. Artifact `benchmark-suite` ID `14750251457`
  (170332 bytes).
- **macOS native C++ and Python parity** — CTest 100% of 204 passed; Python 98 passed in 2.71 s.
- **Publish the evidence site** — downstream of lint through `needs: [lint]`; drift PASS;
  github-pages artifact ID `14750285536`, final size 10266 bytes, `pages_build_version`
  `1a4fc69ad4671db83ca41b02aee7606534d0744e`, environment URL
  `https://jackxiaozhiren.github.io/quantrisk-plus-plus/`. Section 45 changed no page byte and
  re-froze no `build/site.lock` or `evidence/manifest.json`, so this is the already-approved X5
  surface rebuilding gate-verified bytes, not a wider authorisation.

**Live URL, sixth platform confirmation of H3 zero drift** — measured from the development machine
at reading time: HTTP 200, 5793 bytes, `<title>QuantRisk++ evidence</title>`, page SHA256
`692db228336617a0663446bf4181d47a4b63204d9ff156d92d852b25715d25c4` — byte-for-byte equal to the
`index.html` `page_sha256` in the committed `build/site.lock`, unchanged from X5–X9. The deploy ZIP
(10266 bytes here vs 10264 at X9) differs in tar metadata; the page bytes do not move.

**What the platform confirms, and what it does not.** The two CI-side facts section 47 named are
confirmed: the claim-map guard compiles and runs green in the lint lane (523 passed, +1 over X9),
and its paired plant reddens under the mutation census (206/206). The producer's four mapped
figures remain the development-side disk re-derivations of section 46, not runner-only readings.
I-L8 is now `Filled` with both local and platform backing; I-L5 and O11 stay untouched and
unadjudicated. This backfill commit is carried in the second and final ref update of the section 47
approval; its own run is observed-only under the same recursion limit, and no third ref update is
authorised.

## 49. X11 scope unit — I-L5 true offline build (ledger-first)

Scope unit X11, as put to the maintainer verbatim (the selected option's label):

> X11：I-L5 真断网构建（最推荐）

Approval original, verbatim: `X11：I-L5 真断网构建（最推荐）`

The option bound to that label defined the unit as: turn I-L5 from `Partial` into `Filled` against
the roadmap line 299 acceptance test — "A build executed with network disabled; a build that
silently needs network is a High finding" — by running the site build once with the network truly
down and recording the reading; if the build silently needed the network, record and remediate it
as a High finding rather than waiving it. Doing so also closes DoD item 3, whose only remaining
Partial sub-item is the offline build.

**The maintainer was then shown a technical fork, because the offline mechanism is not portable to
this machine.** Measured facts put to them: this macOS host refuses `sandbox-exec` (`sandbox_apply:
Operation not permitted`), has no `unshare`, and its Docker daemon has no prebuilt compiled
extension for the aarch64 site build; the GitHub Ubuntu runner has root and supports
`unshare -n`. They selected the route verbatim:

> CI runner 用 unshare -n（最推荐）

Approval original, verbatim: `CI runner 用 unshare -n（最推荐）`

**What this binds.** The network-down build runs in `.github/workflows/ci.yml`'s lint job, in a
fresh network namespace entered with `sudo unshare -n`, rebuilding the site and comparing it to
the committed `build/site.lock`. The step first proves the isolation is real with a negative
probe — a socket connection that must fail inside the namespace — so a namespace that silently
did not isolate cannot be reported as an offline reading. The reading is attributed to the job
that prints it; no OS-level offline measurement is claimed from this macOS host, where the mechanism
is unavailable. A read-only producer `offline.audit(root)` re-derives the liveness facts from disk
(the CI step's presence and its negative probe, the site generator's network-free import closure,
and the committed lock as the rebuild target); the guarding test re-derives them independently and
is reddened by a named plant. The I-L5 row and the DoD item 3 status line are filled only once the
platform reading exists; until then I-L5 stays `Partial` and this section is scope only.

Bounded effect, and nothing beyond it: add the CI step, the producer module, the guarding test, the
named plant, the I-L5 and DoD item 3 corrections, and the mechanical count/PDF cascade those
require. Excluded: any O11 adjudication, any change to `build/site.lock`, to
`tools/cold_start_record.json`, to `evidence/manifest.json`, to any published artifact, to any tag
or release, any new CLI subcommand, dependency or ceiling key, and any push. The new CI step reads
the same committed bytes as the existing `site drift gate` and re-frozes nothing.

Recursion limit: if a later approval pushes X11, the backfill commit's own run is observed-only and
no third ref update is authorised, as in sections 27, 31, 35, 39, 43 and 47. O11 stays out of scope.

## 50. X11 local stage reading — the offline step is in place, its platform reading is not yet taken

Scope section 49 was committed first (`dcd5b13`); the implementation followed in `9ef3bd1`
(CI step, producer, guard), `2467ef0` (plant-anchor cascade), `9406397` (explicit interpreter path),
and `c817d0f` (a comment corrected after a path-shaped token tripped an existing CI guard). All
five commits are local; section 49 excluded any push, so nothing here is a platform claim and I-L5
remains `Partial` in section 2 until a runner actually executes the network-down build.

**Why the build runs on the runner, not here.** Measured on this macOS host: `sandbox-exec` refuses
with `sandbox_apply: Operation not permitted`; `unshare` is absent; Docker runs aarch64 with no
prebuilt compiled extension for the site build and the PyPI `quantrisk` index returns 404. No
OS-level offline measurement is therefore claimed from this host. The Linux GitHub runner has root
and supports `unshare -n`, so section 49 bound the real build there and the local work below is the
readable, falsifiable half of the law.

**What was added.** The lint job gained a step `offline build (network namespace)`: it resolves the
venv interpreter to an absolute path before elevation, enters `sudo unshare -n`, first runs a
negative probe that must fail to connect an outbound socket (a namespace that silently failed to
isolate cannot count as offline), then rebuilds the site with `quantrisk.interface.drift --check`
against the committed `build/site.lock`, printing `OFFLINE PROBE PASS` and `OFFLINE BUILD PASS` as
named markers. It reads the same committed bytes as the existing `site drift gate` and re-frozes
nothing. `offline.audit(root)` (stdlib, read-only, no socket, no numeric literal) re-derives the
step's markers, the site generator's relative-and-absolute import closure (four modules scanned;
no network module), and the lock's index digest from disk. The guard
`test_the_offline_build_facts_are_readable_and_falsifiable` re-derives each fact independently and
compares the producer, and the plant `offline-step-drops-its-negative-probe` erases the probe's
refusal marker; a red-to-green hand check confirmed the guard reddens before the fix and passes
after.

**A guard interaction found and fixed.** Re-running the full census after the interpreter-path
correction gave `199/208`: nine CI-lane and living-document plants share the guard
`test_the_ci_lane_that_runs_the_guards_fetches_what_they_read`, which reads every path-shaped token
in a step's `run`. A comment phrase containing a slash was parsed as a nonexistent repository path
and put that shared guard red at baseline, so the nine plants could not show a red-to-green delta.
Rewording the comment removed the token; the guard and all nine plants returned to green, and a
final clean-tree census at `c817d0f` reports `208 declared = 208 ran = 208 caught`, `non_caught []`,
`unmeasurable []`, checkout porcelain empty before and after, vantage a detached worktree watching
the checkout without writing it. This is recorded as a finding, not hidden: the guard that reads
CI commands is itself sensitive to how a comment is worded.

**Mechanical cascade and local gates.** Plant count 207 → 208, collected pytest tests 524 → 525,
generated pytest tests 593 → 594; the claim-gold inventory, four living documents, the paper and its
build sidecar, and five plant anchors that quote the old counts were re-derived; the PDF and sidecar
were rebuilt. Locally: `ruff check .`, `ruff format --check .` (270 files) and
`mypy python/quantrisk tools` (84 sources) pass; pytest reports 594 passed; the drift gate reports
PASS; the evidence verifier reports 95 OK, 0 CHANGED, 0 MISSING; `docs_rederivation` reports gap 0
with `derived.plants = 208`. No workflow, lock, record, manifest or published artifact outside the
bounded CI step was changed, and no page byte moved.

**Boundary.** The platform side of I-L5 is not yet a reading: no runner has executed the new step,
so section 2's I-L5 row stays `Partial` and DoD item 3 stays Partial here. A later push, if approved,
can confirm two things and no more: that the offline step prints its PASS markers in the lint lane
with the negative probe intact, and that its paired plant reddens under the mutation census. The
machine-readable producer readings remain development-side disk re-derivations, not runner claims.
O11 is untouched and unadjudicated; no ref was updated and no push is authorised by section 49.

## 51. Push approval for X11 and its bound

Section 49 excluded a push, so section 50's offline-step readings (step in place, local census
208/208, I-L5 still `Partial`) are development-side only; no runner has executed the network-down
build. The maintainer then approved the push. Approval original, verbatim: `批准推送 X11` — the
push-and-backfill authorisation recorded as `推送 X5 并回填（最推荐）`, `推送 X6 并回填（最推荐）`,
`推送 X7 并回填（推荐）`, `推送 X8 并回填（最推荐）`, `推送 X9 并回填（最推荐）` and
`推送 X10 并回填（最推荐）` in sections 27, 31, 35, 39, 43 and 47.

Bounded effect, and nothing beyond it: at most two non-forced ref updates through
`build/api_push.py`, carrying the six X11 commits (`dcd5b13`, `9ef3bd1`, `2467ef0`, `9406397`,
`c817d0f`, `37f0fe7`) together with the commit that records this approval; read the first run
produced by the push and attribute each reading to the job that printed it, including the deploy
job, which re-publishes the same gate-verified site bytes (section 50 changed no page byte and
re-froze no `build/site.lock` and no `evidence/manifest.json`), so its publication is a consequence
of the already-approved X5 surface and not a wider authorisation; write those readings into a
backfill commit in this ledger, including any failure as a failure rather than omitting it. The
platform-side facts this push can confirm, and no more: that the new `offline build (network
namespace)` step runs in the lint lane and prints its named `OFFLINE PROBE PASS` and
`OFFLINE BUILD PASS` markers with the negative probe intact and the rebuilt site matching the
committed lock, and that its paired plant `offline-step-drops-its-negative-probe` reddens under
the mutation census. Only once those readings exist does section 2's I-L5 row become `Filled` and
DoD item 3 `Done`; if the step fails on the runner — for example if `unshare` is unavailable or
denied — the failure is recorded as a failure, I-L5 stays `Partial`, and no offline claim is made.
The producer's disk re-derivations remain development-side, not runner-only measurements. The
recursion limit is the one sections 11, 14, 18, 22, 27, 31, 35, 39, 43 and 47 used: the backfill
commit's own run is observed-only, because a third ref update is outside this approval. No tag,
release, secret or account is moved or added; no new CLI subcommand, ceiling key, dependency or
HTTP surface is introduced; the deploy job stays downstream of the lint lane through `needs:
[lint]`, so a gate failure blocks publication. O11 is untouched and unadjudicated by this push.

## 52. X11 platform run, the network-down reading, and I-L5 filled (backfill)

Run `45027396972` (attempt 1, head `c9df0e76a0a4a28b58e6d22a395e1ca4406da955`, created
13:25:19Z, updated 13:45:54Z) returned `success` on the first attempt with all seven jobs green:
Format and static checks; Benchmark suite against live oracles; Installed wheel surface in a clean
environment; Configure/build/C++/Python tests; macOS native C++ and Python parity; Mutation census
in a detached worktree; Publish the evidence site.

**The I-L5 reading.** The `offline build (network namespace)` step ran in the lint lane and
printed, in order, `OFFLINE PROBE: entering a network namespace with unshare -n`, `OFFLINE PROBE:
inside the namespace`, `OFFLINE PROBE PASS: outbound socket refused inside the namespace`,
`OFFLINE BUILD: rebuilding the site with the network down`, and `OFFLINE BUILD PASS: rebuilt site
matches build/site.lock with no network`. The negative probe failed to connect as required, so the
namespace demonstrably isolated the network; the site rebuilt from the committed bytes and matched
the lock. This is the first site build in the project's history executed with the network actually
down, so section 2's I-L5 row is now `Filled` and DoD item 3 `Filled`; the in-process
`test_the_build_opens_no_socket` remains as a second, narrower check. No OS-level offline claim is
made from the macOS host.

**The paired falsifier.** The mutation census reports `208 declared = 207 measurable here + 1
environment-blind`, verdict `caught 207 / declared 207 / ran 207`, revision
`c9df0e76a0a4a28b58e6d22a395e1ca4406da955`, `checkout_status_before` and `checkout_status_after`
both empty, `malformed` null. The new plant `offline-step-drops-its-negative-probe` is listed
`ok caught`: erasing the probe's refusal marker reddens the guard, so the offline reading is not a
self-certification. `plants_not_rejected_by_their_guard` is `0 against a ceiling of 0`. The single
unmeasurable entry is the recurring pdfTeX-version blind spot
(`report-source-edited-without-a-rebuild-seen-from-the-render`: runner pdfTeX 1.40.28 vs this
build's recorded 1.40.29); it is unchanged by X11.

**Other job readings.** lint lane: ruff 270 files formatted, mypy 84 sources clean, pytest
524 passed + 5 skipped (one more than X10's 523), evidence verifier 95 OK / 0 CHANGED / 0 MISSING,
`docs_rederivation` gap 0 with `derived.plants = 208`, `PASS: rebuilt site matches build/site.lock`
at the existing drift gate. C++ tests 100% of 204 on Ubuntu and 100% of 204 on macOS (macOS lane
also 98 Python tests passed); benchmark suite 19/19 executed and passed, 0 aggregated from disk;
installed wheel reports version 1.9.0 with one study run and the refusal named what it needed.

**Re-publication and live reading.** The `Publish the evidence site` job re-published the same
gate-verified bytes (`pages_build_version=c9df0e76a0a4a28b58e6d22a395e1ca4406da955`, artifact
14756266697, 10268 bytes). A direct read of
`https://jackxiaozhiren.github.io/quantrisk-plus-plus/` returned HTTP 200, 5793 bytes, page
SHA `692db228336617a0663446bf4181d47a4b63204d9ff156d92d852b25715d25c4`, equal to the locked
`index.html` digest — the seventh consecutive zero-drift live reading.

**Boundary.** This backfill commit is carried in the second and final ref update of the section 51
approval; its own run is observed-only and no third ref update is authorised. The platform confirms
exactly two facts: the offline step prints its PASS markers with the negative probe intact, and its
paired plant reddens under the census. All other producer readings remain development-side disk
re-derivations. No page byte moved, no lock or manifest was re-frozen, no tag or release was moved,
and O11 remains untouched and unadjudicated.

## 53. O11 adjudicated — AI-token cost is task-side, outside the project-side zero-cost basis

O11's original form in the R0–R11 report is `AI token 消耗是否计入项目侧成本口径`, and the evidence
it requires is a cost-basis ruling original whose owner is named as the developer themself. The
report's entry K1 records the maintainer's words `成本上限「除了AI的token消耗以外，其余必须使用免费资源」`
but declined to rewrite E09's `$0` claim from that alone, so the item stayed open while H1–H4 were
being measured. Section 4's K1 row already states the same split as an interpretation; what was
missing was the ruling original, not the position. With X11 closing I-L5, O11 was the last open item.

The maintainer was offered the ruling and selected it. Approval original, verbatim — the option
label they replied with: `裁定 O11：不计入（最推荐）`

Ruling text carried by the selected option, verbatim:
`O11 裁定：AI token 消耗单列为任务侧成本，不计入项目侧成本口径；项目侧 monetary cost 与持续携带成本仍为零，不引入账号或密钥。`

**What this settles.** AI-token consumption is a task-side cost, recorded separately and excluded
from the project-side basis. The project-side basis remains zero monetary cost and zero carrying
cost, with no account or secret introduced. This is consistent with four statements already on
disk: the report's K1 quoted maintainer words, Section 4's K1 ruling, `PROJECT_SPEC.md` §3's
`除 AI token 外：` followed by the bolded `整个项目必须 $0 完成。`, and `docs/project_scope.md` §7
`Cost constraint ($0 + AI tokens)`. It is also consistent with H4's measured reading rather than a
replacement for it: `cost.audit()` still reports the paid action set empty, billed runners empty,
stored secrets false, the free static tier true, no custom domain, and the `$0` budget line exactly
once. The README's zero-cost sentence and E09/A5/C3.5 are not rewritten, because the ruling keeps
the project side at zero and only names where the token cost sits.

**Bounded effect, and nothing beyond it:** this section; the cost-basis sentence in Section 2's
I-L4 row, which previously said O11 stays unadjudicated; and the docstring of
`test_the_publish_chain_stays_on_the_free_tier`, which carried the same open-item sentence. No
producer, guard, plant, count, document count, PDF, lock, manifest, workflow or published artifact
is touched, and no H1–H4 reading changes. No push is authorised by this section; it is a local
ruling record. O11 is now closed, and no open item remains in Section 2.

## 54. O11 ruling local stage reading — prose only, so no count moved

Section 53's bounded effect is prose: the ruling record, Section 2's I-L4 cost sentence and the
docstring of `test_the_publish_chain_stays_on_the_free_tier`. No producer, guard, plant, counted
artifact or document figure is touched, so the mechanical cascade is empty. This stage reading
exists to show that rather than assert it, and to leave the ruling attached to a revision a reader
can check out.

Readings at `0cd85c2`, development machine, committed checkout:

- `ruff check .` — `All checks passed!`; `ruff format --check .` — 270 files already formatted;
  `mypy python/quantrisk tools` — no issues in 84 source files. All three through `uv run`, the same
  commands the lint job runs.
- pytest — 594 passed in 126.20 s, with a private `--basetemp` and bytecode writing unset. Because
  the last prose edits landed after that run, the modules that read the ledger's sections or the
  counted documents were rerun: 83 passed in 31.53 s across `test_interface_offline`,
  `test_interface_claimmap`, `test_interface_liveness` and `test_artifact_metadata`.
- `uv run python tools/verify_evidence_manifest.py` — 95 OK, 0 CHANGED, 0 VOLATILE, 0 MISSING,
  0 unlisted; `Evidence is intact.` The manifest is verified read-only, not rebuilt.
- Full census — `208 declared = 208 ran = 208 caught`, `non_caught []`, `unmeasurable []`,
  porcelain empty before and after, revision `0cd85c2`, from the detached worktree that watches
  the checkout and never writes it. No plant lost its anchor and no new plant was needed.

**What did not move.** The plant count stays 208, the pytest count stays 594, and the four
documents, the PDF and its sidecar, `build/site.lock`, `evidence/manifest.json`, the workflow and
every published byte are untouched. No cascade commit is pending and the published site cannot have
drifted, so no live-URL reading is re-taken here.

**Bounded effect, and nothing beyond it:** this section only. No push is authorised and no platform
reading is claimed; section 53 stays a local ruling record that the platform has not yet seen.

## 55. Push approval for the O11 ruling and its bound

Section 53 excluded a push and section 54 recorded the local stage readings, so the ruling exists
only on this host. The maintainer then approved the push. Approval original, verbatim:
`推送 §53/§54 并回填（最推荐）` — the push-and-backfill authorisation recorded the same way as
`推送 X5 并回填（最推荐）`, `推送 X6 并回填（最推荐）`, `推送 X7 并回填（推荐）`,
`推送 X8 并回填（最推荐）`, `推送 X9 并回填（最推荐）` and `推送 X10 并回填（最推荐）`
in sections 27, 31, 35, 39, 43 and 47.

Bounded effect, and nothing beyond it: at most two non-forced ref updates through
`build/api_push.py`, carrying the two O11 commits (`0cd85c2`, `584a065`) together with the commit
that records this approval; read the first run produced by the push and attribute each reading to
the job that printed it, including the deploy job. Because sections 53 and 54 changed no page byte,
no `build/site.lock`, no `evidence/manifest.json` and no workflow, the deploy re-publishes the same
gate-verified bytes, and its publication is a consequence of the already-approved X5 surface rather
than a wider authorisation. Write those readings into a backfill commit in this ledger, including
any failure as a failure rather than omitting it.

**What this push can and cannot confirm.** It can confirm that the seven jobs are green on a tree
whose only change is a ruling record and one test docstring, that the census still declares 208
plants and catches every measurable one, that the counted suite still collects the number the
documents state, and that the published bytes and the live URL do not move. It cannot confirm any
measured value, because none was added: no H reading, no I-L predicate and no O11-dependent quantity
is re-measured here. Section 53's ruling is a decision record, and the only platform fact it needs is
that the record does not break the gates it sits behind. If a job fails, the failure is recorded as
a failure and the ruling stays a local record.

Recursion limit: the one sections 11, 14, 18, 22, 27, 31, 35, 39, 43, 47 and 51 used — the backfill
commit's own run is observed-only, because a third ref update is outside this approval. No tag,
release, secret or account is moved or added; no new CLI subcommand, ceiling key, dependency or HTTP
surface is introduced; the deploy job stays downstream of the lint lane through `needs: [lint]`, so a
gate failure blocks publication. The out-of-tree report
`QuantRisk_reports/QuantRisk++_future_direction_report_v1.1.md` is not touched by this approval or
by this push, and updating it remains a separate unit with its own scope.

## 56. O11 platform run — the ruling carried by seven green gates (backfill)

Run `45143457529` (attempt 1, head `b8772216e54e681724b9ddfd640dcf02b53501cc`, created
09:02:10Z, updated 09:27:55Z) returned `success` on the first attempt with all seven jobs green:
Format and static checks (09:02:13→09:03:33); Configure, build, C++ tests, Python tests
(09:02:13→09:08:12); Benchmark suite against live oracles (09:02:13→09:12:10); Installed wheel
surface in a clean environment (09:02:14→09:04:29); macOS native C++ and Python parity
(09:02:13→09:05:45); Mutation census in a detached worktree (09:02:13→09:27:54); Publish the
evidence site (09:03:38→09:04:49).

**What the run confirms.** The three O11 commits pass every gate they sit behind, so the ruling is
carried by a tree the platform has executed rather than by a claim about one. The lint lane's
`static_check_coverage` records `mypy_exit_code: 0` with two-sided agreement on 84 source files
(70 under `python/quantrisk`, 14 under `tools`), `formatter_census` records 270 of 270 formattable
files already formatted with 0 to reformat, and the four ceiling gaps read 0
(`docs_rederivation`, `lanes_documented_vs_executed`, `runtime_reachability`, `with_extras_census`)
with `external_dependencies` at 9 declared and 9 measured, none added or removed. The evidence
manifest step printed `Evidence is intact.` over its 95 artifacts, the drift gate printed `PASS:
rebuilt site matches build/site.lock`, and the offline step printed `OFFLINE PROBE PASS: outbound
socket refused inside the namespace` followed by `OFFLINE BUILD PASS: rebuilt site matches
build/site.lock with no network` — the same two markers section 52 attributed to I-L5, re-printed
here rather than re-interpreted. The C++ suite reports `100% tests passed out of 204`, pytest
`524 passed, 5 skipped in 170.82 s` (the count section 52 recorded, because no test was added), the
benchmark suite `19/19 executed and passed`, the macOS job `98 passed in 3.40 s` with a
`quantrisk-1.9.0-cp312-cp312-macosx_15_0_arm64.whl`, and the installed-surface job `identity holds,
the list is the registry, one study ran, and the refusal named what it needed` at revision
`b877221`.

**The census.** `208 declared = 207 measurable here + 1 environment-blind`, `207/207 planted defects
were rejected by their guard`, revision `b877221`, checkout status empty before and after. The
environment-blind plant is the same one section 52 named: `report-source-edited-without-a-rebuild`'s
guard needs the pdfTeX that typeset the PDF, and the runner's is 1.40.28 against the recorded
1.40.29. Both plants that touch this unit's claims were caught on the runner —
`claim-map-drops-a-recorded-figure-from-the-report` and
`offline-step-drops-its-negative-probe` each printed `ok caught` — so appending sections 53–55 did
not displace the H1 anchor either plant depends on. The local census at `0cd85c2` read 208/208
measurable because this host's comparison set is not version-blind; the difference is the
environment, not a regression, and it is the same difference section 52 recorded.

**No page byte moved.** The deploy job re-verified the rebuilt site against the lock (`PASS`), then
uploaded artifact `14803950214` and created deployment `b877221` with `pages_build_version`
`b8772216e54e681724b9ddfd640dcf02b53501cc`, reporting success. The live URL returned HTTP 200 with
5793 bytes and SHA-256 `692db228336617a0663446bf4181d47a4b63204d9ff156d92d852b25715d25c4`, which is
`build/site.lock`'s `page_sha256` — the eighth consecutive zero-drift reading. The uploaded zip's
own size (10623 bytes here, 10268 in section 52) is the artifact container, not a page byte; the
checkable reading is the served 5793 bytes and its digest, and those did not move.

**What the run does not confirm.** No measured value. No H reading, no I-L predicate and no
O11-dependent quantity was re-measured, because section 53 added none; its only claim is a decision
and the split it names. O11 stays closed, section 2's I-L4 row keeps the cost-basis sentence section
53 wrote, and no H1–H4 reading changes here.

Recursion limit: this backfill commit's own run is observed-only, and no third ref update is
authorised, as in sections 11, 14, 18, 22, 27, 31, 35, 39, 43, 47 and 51. Bounded effect, and
nothing beyond it: this section. No tag, release, secret, account, ceiling key, dependency or
workflow step is moved or added by the backfill, and the out-of-tree report remains untouched and
still to be updated as its own unit.

## 57. Out-of-tree report v1.2 scope and approval

Sections 53–56 closed O11 in the repository and on the runner, and section 55 explicitly left the
out-of-tree report `QuantRisk_reports/QuantRisk++_future_direction_report_v1.1.md` as a separate
unit. That report states, as its own 2026-11-15 reading at `e60bba5`, that H1–H4 are unmeasured,
that I-L1…I-L8 are all VOID, that `INTERFACE_LEDGER.md` is untracked, that the three publication
approvals are not obtained and that O11 is unadjudicated. Those were true then; they are false at
`983b4a9`. The report is the last surface that would tell a reader the project has not been built.

The maintainer approved this unit. Approval original, verbatim: `把报告更新到 v1.2（最推荐）`

**Scope.** Write a new `QuantRisk++_future_direction_report_v1.2.md` under
`/Users/jackson/QuantRisk_reports/`, leaving v1.1 byte-identical as the dated historical record.
Retain v1.1's R/E/B/N/K numbering and its historical rows; add a current-state section whose
platform readings carry run, attempt, date and producer, add evidence entries and a v1.2 revision
registry, and mark each superseded conclusion where a reader would otherwise take it as current.
No number is transcribed from this ledger without its source in that row.

**Bounded effect, and nothing beyond it:** the tree-external v1.2 file, this scope section and the
stage record that follows. No repository artifact, count, PDF, lock, manifest, workflow, tag,
release or published byte moves, and no push is authorised. K2 and K3 are not treated as maintainer
rulings: only K1/O11 has an approval original on disk, and no capability is unlocked by an
interpretation. No claim is made that S05 was adjudicated under X1 — later units added named plants
under their own approvals instead.

## 58. Out-of-tree report v1.2 local stage reading

`/Users/jackson/QuantRisk_reports/QuantRisk++_future_direction_report_v1.2.md` now exists: 836 lines,
165845 bytes, SHA-256 `aa24947ab0a55acf8df601e9a1292559230c83420f375f4559c015bd20545984`. The v1.1
file is byte-identical to its pre-unit reading, SHA-256
`da3a5b96e67696ef1f8e3ba5bcbde914ae4a72c60560100e03e262da3c9bfa57`, and was never written.

**What v1.2 contains.** The v1.1 body is retained as the dated historical record at `e60bba5`; the
header states the reading rule, so an unmarked "unmeasured / unadjudicated / VOID / not obtained"
sentence is a 2026-11-15 reading and not a claim about the present. R0 was rewritten in place as
eight current-state lines and R0.1 gives the four H values, the liveness state, the true
network-down build, the O11 ruling and the current counts with run attribution. E63–E70 add the
eight new evidence entries with run, attempt, date or revision; R1.5.1 registers C12–C18; R9.1 keeps
its historical columns and adds a current-reading column; R9.2 marks the old "deliberately not done"
list as historical; K1, eight R11.3 rows and fourteen R11.5 rows carry in-place v1.2 annotations.
K2 and K3 remain interpretations, and S05 stays unadjudicated under X1.

**Checks taken.** R0 has exactly eight content lines, satisfying the report's own Section 6 bound;
all contiguous markdown tables have a single column count (zero inconsistent groups); no fenced code
block was introduced; and every named insertion point, including E63–E70 and the O11 ruling text,
was asserted present. No platform run is claimed by this unit: the report is tree-external and has
no CI lane, and its readings are the runs already attributed in sections 30–56.

**Bounded effect, and nothing beyond it:** this section and section 57 in this ledger, plus the new
tree-external file. No repository artifact, count, PDF, lock, manifest, workflow, tag, release or
published byte moved. No push is authorised; local HEAD `9f4b15b` carries sections 57–58 and the
platform remains at `983b4a9`. If a later approval pushes these two bookkeeping commits, the usual
recursion limit applies: that run is observed-only and no third ref update follows from it.

## 59. Push approval for the report unit's ledger sections

Sections 57 and 58 recorded the out-of-tree report v1.2 scope, approval and local stage reading,
and section 58 explicitly excluded a push. The maintainer then approved that push. Approval
original, verbatim: `推送 §57/§58 并回填（推荐）` — the same bounded push-and-backfill form as
`推送 §53/§54 并回填（最推荐）` in section 55 and its earlier counterparts in sections 27, 31,
35, 39, 43, 47 and 51.

Bounded effect, and nothing beyond it: at most two non-forced ref updates through
`build/api_push.py`, carrying the two report-unit ledger commits (`9f4b15b`, `ea02ed7`) together
with the commit recording this approval; read the first run produced by the push and attribute each
reading to the job that printed it, including the deploy job; write those readings into a backfill
commit in this ledger. Because sections 57–59 changed no repository artifact, count, PDF, lock,
manifest, workflow or published byte — the report itself is tree-external and outside the ref —
the deploy re-publishes the same gate-verified bytes, and its publication is a consequence of the
already-approved X5 surface rather than a wider authorisation.

**What this push can and cannot confirm.** It can confirm that the seven jobs stay green on a tree
whose only change is three ledger sections, that the census still declares 208 plants and catches
every measurable one, that the counted suite still collects the number the documents state, and
that the live page keeps the locked SHA. It cannot confirm the report's contents: the report has no
CI lane, and its v1.2 readings are the runs already attributed in sections 30–56. A failure is
recorded as a failure, not omitted.

Recursion limit: the one used in sections 11, 14, 18, 22, 27, 31, 35, 39, 43, 47, 51 and 55 — the
backfill commit's own run is observed-only, because a third ref update is outside this approval. No
tag, release, secret or account is moved or added; no new CLI subcommand, ceiling key, dependency
or HTTP surface is introduced; the deploy job stays downstream of the lint lane through
`needs: [lint]`, so a gate failure blocks publication.

## 60. Report-unit ledger sections on the platform — seven green gates (backfill)

Run `45165920196` (attempt 1, head `3978045b395a81d885cc9471ab86f0dbdf883af1`, created
11:31:04Z, updated 11:51:57Z) returned `success` on the first attempt with all seven jobs green:
Format and static checks (11:31:07→11:32:34); Configure, build, C++ tests, Python tests
(11:31:08→11:37:31); Benchmark suite against live oracles (11:31:08→11:39:35); Installed wheel
surface in a clean environment (11:31:07→11:32:49); macOS native C++ and Python parity
(11:36:49→11:40:20); Mutation census in a detached worktree (11:31:07→11:51:57); Publish the
evidence site (11:32:39→11:33:55).

**What the run confirms.** The three ledger-only commits pass every gate they sit behind, so the
report unit's bookkeeping is carried by a tree the platform has executed. The lint lane printed
`All checks passed!` for ruff, `270 files already formatted`, `Success: no issues found in 84 source
files`, four ceiling gaps at 0 (`artifact_revision`, `docs_rederivation`,
`lanes_documented_vs_executed`, `runtime_reachability`; `with_extras_census` also 0), and
`external_dependencies` 9 declared and 9 measured with none added or removed. The evidence manifest
step printed `Evidence is intact.` over its 95 artifacts, the drift gate printed `PASS: rebuilt site
matches build/site.lock`, and the offline step printed `OFFLINE PROBE PASS: outbound socket refused
inside the namespace` followed by `OFFLINE BUILD PASS: rebuilt site matches build/site.lock with no
network` — the I-L5 markers of section 52, re-printed rather than re-interpreted. The C++ suite
reports `100% tests passed out of 204`, pytest `524 passed, 5 skipped in 168.61s`, the benchmark
suite `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped`, the macOS job
`98 passed in 3.03s` with a `quantrisk-1.9.0-cp312-cp312-macosx_15_0_arm64.whl`, and the
installed-surface job `identity holds, the list is the registry, one study ran, and the refusal
named what it needed` at revision `3978045`.

**The census.** `208 declared = 207 measurable here + 1 environment-blind`, `207/207 planted defects
were rejected by their guard`, revision `3978045`, checkout status empty before and after. The
environment-blind plant is the one sections 52 and 56 named: the re-render guard needs the pdfTeX
that typeset the PDF, and the runner's is 1.40.28 against the recorded 1.40.29. Both plants that
touch report claims were caught on the runner — `claim-map-drops-a-recorded-figure-from-the-report`
and `offline-step-drops-its-negative-probe` each printed `ok caught` — so appending sections 57–59
did not displace the H1 anchor either plant depends on. The census's `docs_rederivation` reading
re-derived 208 plants, 95 manifest artifacts and 19 suite members from their artifacts with gap 0
across the five living documents.

**No page byte moved.** The deploy job re-verified the rebuilt site against the lock, then uploaded
artifact `14814429085` (10267-byte zip container) and created a deployment with `pages_build_version`
`3978045b395a81d885cc9471ab86f0dbdf883af1`, reporting success. The live URL returned HTTP 200 with
5793 bytes and SHA-256 `692db228336617a0663446bf4181d47a4b63204d9ff156d92d852b25715d25c4`, which is
`build/site.lock`'s `page_sha256` — another zero-drift reading of the served bytes. Sections 57–59
changed no repository artifact, so no new page content was available to publish.

**What the run does not confirm.** No report content and no measured value. The v1.2 report is
tree-external, has no CI lane and is not part of this ref; its SHA-256 remains
`aa24947ab0a55acf8df601e9a1292559230c83420f375f4559c015bd20545984` and v1.1 remains byte-identical
to its pre-unit SHA. The run's only claim about the report unit is that the three ledger sections do
not break the gates they sit behind; no H1–H4 reading, I-L predicate or O11-dependent quantity was
re-measured.

Recursion limit: this backfill commit's own run is observed-only, and no third ref update is
authorised, as in sections 11, 14, 18, 22, 27, 31, 35, 39, 43, 47, 51, 55 and 59. Bounded effect,
and nothing beyond it: this section. No tag, release, secret, account, ceiling key, dependency,
report byte or workflow step is moved or added by the backfill.

## 61. Dependabot PR anchor repair — scope and verbatim approval

The maintainer approved this unit. Approval original, verbatim: `授权处理 dependabot PR 45358818696 的 anchor 非唯一问题`

Run `45358818696` (PR #14, head `828f10932e385e40ea1bea46b670c3bfbbfd02e4`, branch
`dependabot/github_actions/actions/deploy-pages-5`) failed its mutation-census job: the plant
`publish-chain-adds-a-paid-action` returned `anchor-not-unique` because its anchor and replacement
hard-code `uses: actions/deploy-pages@v4` while the PR bumps that step to `@v5`. On the PR's
workflow the anchor occurs zero times, so `apply_mutation` refuses to guess and the plant cannot be
planted. This is an anchor-versioning defect in the plant declaration, not a defect in the guard
`test_the_publish_chain_stays_on_the_free_tier`, whose `FREE_ACTIONS` already matches the action
name without its `@` suffix.

**Scope.** Diagnose the mismatch from the PR's own workflow bytes; make the plant's anchor and
replacement version-independent so they match both `actions/deploy-pages@v4` on `main` and `@v5` on
the PR, while still inserting the named paid action immediately before the deploy step; verify
locally that the anchor occurs exactly once on both workflow versions and that the guard reddens
on the mutated tree and greens on the restored one. Record the reading in the section that follows.

**Bounded effect, and nothing beyond it:** this scope section, the plant declaration in
`python/quantrisk/verification/plants.py`, and the local stage reading. The user's sentence
authorises handling the problem; it does **not** name a push, a PR comment, a tag, a release, a
secret, an account, a ceiling key, a dependency, a workflow step or a published byte. Any ref
update needs its own verbatim approval recorded here first, as in sections 55 and 59. No action
version in `.github/workflows/ci.yml` is changed by this repair, and no guard or `FREE_ACTIONS`
entry is widened to make the defect pass.

## 62. Anchor repair local stage reading — v4 and v5 both planted

The repair changes only the two text literals in
`python/quantrisk/verification/plants.py` for plant `publish-chain-adds-a-paid-action`: anchor and
replacement now end at `uses: actions/deploy-pages@`, so the declaration names the step without
freezing its `@v4` or `@v5` suffix. The guard is untouched:
`test_the_publish_chain_stays_on_the_free_tier` already compares action names with the `@` suffix
removed, so a paid third-party action is refused on either workflow version. The anchor was
measured to occur exactly once in both the `main` workflow (`@v4`, line 430) and PR #14's workflow
bytes (`@v5`, line 430) before any run.

**Local readings, 2026-11-26T10:44–10:49+08:00, macOS, uv 0.11.7, CPython 3.12.14, worktree at
`4e64c5e1316a20a912ae9c6554ca7bb00eee9133`:** `ruff check` all passed; `ruff format --check` 270
files already formatted; `mypy python/quantrisk tools` success on 84 source files; full
`pytest -q` with a private basetemp `594 passed in 238.78s`. The single plant was run twice: once in
the main worktree against `@v4` and once in a detached worktree whose workflow bytes were replaced
with PR #14's `@v5` version (the runner's `target-already-modified` guard forbids injecting those
bytes into the main worktree, so the second run used an isolated checkout with the repaired plant
file and the main tree's virtual environment linked in). Both printed `ok caught` and
`1/1 planted defects were rejected by their guard`. The detached worktree was removed afterwards
and `git worktree list` shows only the two pre-existing worktrees.

**The ceiling reading and its vantage.** `tools.inventory_orphan_code --check-ceilings` printed 13
`ok` keys at gap 0, one `SKIP` (`installed_user_identity_mismatch`, precondition absent because the
installed-surface lane did not run on this vantage), and one `VIOLATION`
(`plants_not_rejected_by_their_guard: 1`). That violation reads the local
`build/sweep_verdict.json`, whose revision is `28727f46d286f0da3c225812f81a7c6c73d74663` with
`198 declared = 198 caught` — an earlier revision, not this tree. It is the same dev-vantage
reading already recorded in the planning baseline (EV-M9), not a regression from this repair: the
platform's own sweep at run `45170337984` revision `4e64c5e` reported `208 declared = 207 measurable
here + 1 environment-blind` and `207/207` caught. No full sweep was re-run locally; the repair's
plant-level claim rests on the two single-plant readings above.

## 63. Push approval for the anchor repair and its bound

The maintainer approved one ref update. Approval original, verbatim: `授权推送 main（推荐）`

**Bounded effect, and nothing beyond it:** exactly one non-forced update of `refs/heads/main`,
carrying sections 61–63 of this ledger and the two anchor literals in
`python/quantrisk/verification/plants.py` for `publish-chain-adds-a-paid-action`. The update is
verified against the remote's current SHA before it is sent and is refused if that SHA has moved.
No tag, release, secret, account, ceiling key, dependency, workflow step, version number or
published byte moves; `.github/workflows/ci.yml` is untouched by this push and still pins
`actions/deploy-pages@v4` on `main` — PR #14 carries the `@v5` bump on its own branch. The
maintainer's sentence authorises this one ref update and no backfill: a second update to record the
resulting platform run is **not** authorised here. The backfill commit, if any, would need its own
verbatim approval and its own run would be observed-only, as in sections 55, 59 and 60. Reading the
jobs and logs of the run this update produces is within scope; commenting on, merging or closing
PR #14 is not.

**What this stage does not establish.** It does not establish that PR #14 is green: the PR's own
CI run must re-execute the mutation-census job on its `@v5` tree, and no ref update, PR comment,
tag, release or published byte is authorised by section 61. The stage establishes only that the
plant now anchors on both versions and that the local gates behind the repair are green. The next
section, if any, must carry the verbatim approval for a ref update before the fix can reach the
PR.

## 64. Anchor repair on the platform — main seven green, PR #14 green after a rebase

The maintainer chose the rebase-and-verify option offered for the next step. Choice, verbatim:
`触发 PR #14 rebase 验证（推荐）`

**Bounded effect of that choice, and nothing beyond it:** exactly one comment on pull request #14
carrying the single line `@dependabot rebase`, posted 2026-11-26T03:42:40Z as issue comment
`7181956421` by `Jackxiaozhiren`. It is not a merge, not a close, not a review, not a ref update,
not a tag or release, and it changes no workflow byte and no dependency version on `main`. The
comment asks the bot to move its own branch; the bot, not this session, writes that branch.

**What `main` shows after the repair.** Run `45745373335` (`run_number` 334, attempt 1, head
`c5f330bbec40c649fce75ff9b3462cee468b3505`, push, created 02:53:21Z, updated 03:12:18Z) returned
`success` with all seven jobs green: Format and static checks (02:53:25→02:54:40); Configure, build,
C++ tests, Python tests (02:53:24→03:01:24); Benchmark suite against live oracles
(02:53:25→03:03:33); Installed wheel surface in a clean environment (02:53:24→02:55:14); macOS
native C++ and Python parity (02:53:26→02:57:24); Mutation census in a detached worktree
(02:53:25→03:12:18); Publish the evidence site (02:54:45→02:56:27).

Readings inside that run: ruff `reported_already_formatted: 270` of `reported_total: 270` with
`reported_would_reformat: 0` against `tracked_formattable: 270`; `external_dependencies` 9 declared
and 9 measured with none added or removed; `Evidence is intact.`; `PASS: rebuilt site matches
build/site.lock` printed by the drift step, again by the deploy job and again inside the offline
namespace; `OFFLINE PROBE PASS` and `OFFLINE BUILD PASS`; C++ `100% tests passed out of 204`; pytest
`524 passed, 5 skipped in 224.41s`; macOS `98 passed`; the pages artifact `15083655687` with
`pages_build_version: c5f330bbec40c649fce75ff9b3462cee468b3505`. The census printed
`208 declared = 207 measurable here + 1 environment-blind` and `207/207 planted defects were
rejected by their guard` at revision `c5f330b` with checkout status empty before and after, and the
repaired plant `publish-chain-adds-a-paid-action` appears in that list as `ok caught` — so the
version-independent anchor is exercised by the platform's own sweep, not only by the two local
single-plant runs of section 62.

**What the PR shows after the bot moved it.** The branch head moved from
`828f10932e385e40ea1bea46b670c3bfbbfd02e4` to `a27bc73adb7da0b0fa543d7aedb53882424022f7` with base
`c5f330b`, i.e. exactly the one commit that carries sections 61–63 and the two anchor literals. Run
`45750725114` (`run_number` 335, attempt 1, `pull_request`, created 03:43:29Z, updated 04:04:14Z)
returned `success` on its first attempt: the two jobs that were red on `828f1093` — Mutation census
and Configure/build/C++/Python — are green, and Publish the evidence site is `skipped` because a
pull-request event does not deploy. The census on the `@v5` bytes printed
`208 declared = 207 measurable here + 1 environment-blind`, `207/207`, and
`ok   caught   publish-chain-adds-a-paid-action`; pytest printed `524 passed, 5 skipped in 223.87s`
and macOS `98 passed in 4.46s`. The anchor test that failed before
(`test_every_declared_mutation_names_one_unique_anchor_and_a_guard_that_exists`, reporting `its
anchor occurs 0 times in .github/workflows/ci.yml`) is green on this tree without being edited.

**An observation that is not a conclusion.** The deploy step on `main` prints a deprecation warning
naming `actions/deploy-pages@v4` among the actions "forced to run on Node.js 24" because they target
Node.js 20. That is one reason the bump has value independent of the anchor defect, and it is
recorded here as an observation. Merging PR #14 would change the version of the action that
publishes the site, so it is left to its own unit, with its own approval and its own post-merge
reading of the pages artifact and the live digest. Nothing in this section merges, closes or
approves it.

## 65. Backfill approval for the anchor-repair unit and its bound

The maintainer delegated the remaining steps. Delegation, verbatim:
`我都听你的，请按照你的思路建议进行`

**How that sentence is read, narrowly.** It is read as approval for exactly one thing: a single
non-forced update of `refs/heads/main` carrying sections 64–65 of this ledger, so that the platform
readings above and the approval that produced them sit in the tree the platform executed. It is
**not** read as approval to merge or close PR #14, to move or add a tag, to publish a release, to
change any workflow byte, dependency version or published byte, or to make a second ref update
after this one. The run this update produces is observed only, as in sections 55, 59 and 60; its
readings wait for whichever later unit is separately approved.

**Bounded effect, and nothing beyond it:** one ref update, one commit carrying only
`INTERFACE_LEDGER.md` sections 64–65, verified against the remote's current SHA and refused if that
SHA has moved, with `force` false. The anchor literals in
`python/quantrisk/verification/plants.py` are already on `main` from `c5f330b` and are not touched
here. No tag, release, secret, account, ceiling key, dependency, workflow step, version number or
published byte moves. The repair's evidence chain now has three independent readings — the local
single-plant pair of section 62, the platform census on `main`, and the platform census on the
PR's `@v5` bytes — and none of them is inferred from another.
