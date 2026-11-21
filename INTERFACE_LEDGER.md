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
| I-L4 | Filled (cost basis bounded) | X5 configured the free-tier publish; `test_the_publish_chain_stays_on_the_free_tier` names the no-cost first-party action set and refuses stored secrets, with plant `publish-chain-adds-a-paid-action` reddening on a third-party paid action. The cost basis is CI minutes and Pages free tier only — AI-token cost (O11) stays unadjudicated and out of scope (section 30) |
| I-L5 | Partial | `test_the_build_opens_no_socket` refuses `socket.socket`, `create_connection` and `getaddrinfo` for a full build; a build with the network actually down was not run, and a subprocess making a network call would escape this probe |
| I-L6 | Filled (module path, not HTTP) | `python -m quantrisk.interface.provenance --resolve --json` is the machine-readable surface: `test_the_machine_readable_surface_is_module_path_and_keeps_provenance` requires value + command + revision + digest together and an AST check that no HTTP/service framework is imported, with plant `machine-readable-surface-drops-a-provenance-field` reddening when a field is dropped. No service layer was added (section 30) |
| I-L7 | VOID | Claim-inventory guards belong to the refactor lane; this lane has added no README or site claim, so no I-lane target exists |
| I-L8 | VOID | No measured H1–H4 value exists to map to a recorded run |

Note: the refactor lane's L4 ACTIVE record and the interface lane's I-L1 … I-L8 are different
rail sets. Neither may be cited as evidence for the other.

## 3. H1–H4 measurement ledger

The maintainer confirmed the measurement environment and producers are available. Availability
is not a measurement. No measurement was run under X1, which contains no measurement phase.

| Hypothesis | Value | Producer | Environment | Status |
|---|---|---|---|---|
| H1 cold-start reproduction | 未测得 | 未取得 | 未取得 | 未测得 |
| H2 provenance completeness | Complete over the published-value set: 10/10 headline-bearing registry artifacts resolve with value + command + revision + digest together; 0 named refusals and 0 incomplete tuples (X7 §33–§34) | `provenance.completeness()` read-only producer over the committed manifest and registry (X7), guarded by `test_the_published_value_set_resolves_with_full_provenance`, which declares the ceiling and is reddened by plant `a-published-value-loses-its-digest` erasing one recorded digest; the denominator is the published-value set, not all 95 manifest artifacts — the 9 benchmark/analysis artifacts with no headline are named-refused by `resolve()` by design and are not provenance gaps | development machine, committed checkout at `e48c4f8` (producer reads no network, opens no socket); producer + guard local, plant falsification in the full census | Measured at X7: coverage 10/10, 0 refused, 0 incomplete; the metric is falsifiable (digest erase drops resolved off published). No runner reading claimed until a platform run observes it |
| H3 zero page drift | Zero: live index SHA-256 `692db228336617a0663446bf4181d47a4b63204d9ff156d92d852b25715d25c4` == committed `build/site.lock` `index.html` `page_sha256`, byte-for-byte | X5 section 28's producer curl + SHA-256 of the live Pages response; `python -m quantrisk.interface.drift --check` + committed `build/site.lock` is the gate behind that URL | development machine over HTTPS (live URL read, not a CI network call); gate local and runner | Mechanism proven falsifiable at `28727f4`; the published-surface value registered from X5 section 28 at `d040872` (section 30) |
| H4 zero cost | Zero: every `uses:` reference across all seven jobs in `ci.yml` is inside the free first-party set (0 paid actions), 0 billed runners, 0 stored secrets; the host is GitHub Pages from `actions/deploy-pages` with `pages: write` / `id-token: write` / the `github-pages` environment and no `CNAME` file; the report asserts `Total monetary cost of building and validating it: $0.` exactly once (`README.md` line 31) (X8 §37–§38) | Read-only `cost.audit()` producer over the committed workflow and README (X8), guarded by `test_the_zero_cost_claim_is_read_from_the_publish_surface_and_the_report`, which declares the ceiling and is reddened by plant `report-drops-its-zero-cost-budget-line` editing the README sentence; the producer returns three evidence blocks, never a computed literal, so the reading cannot be satisfied by repeating the policy — the L12 shape `external_dependencies()` records | development machine, committed checkout (producer reads no network, opens no socket); guard local, plant falsification in the full census | Measured at X8: paid set empty, billed runners empty, stored secret false, free static tier true, custom domain false, budget line exactly once and carrying `$0`. No runner reading claimed until a platform run observes it |

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
| 3 | I2 generator, drift gate proven falsifiable, free-tier CI publish, offline build | Partial (publish sub-item now Done): generator done at `aafb707` and drift gate proven falsifiable at `28727f4` (sections 13/17); X5's gated CI `deploy` job ran on the runner in run `44292891046` (seven-job success) and published the gate-verified bytes to `https://jackxiaozhiren.github.io/quantrisk-plus-plus/`, with a live-URL reading whose SHA equals the locked `index.html` (section 28); the offline build stays partial (I-L5, section 2), which keeps item 3 Partial as a whole |
| 4 | I3 value and provenance returned together, refusals name the gap | Done at `25aed30`: `resolve()` returns value + command + revision + digest together and refuses by name on any missing element; plant `provenance-erases-a-recorded-command` proves the guard fails; readings in section 21 |
| 5 | H1–H4 measured, liveness filled, deliberately-not-done list | Partial: H3 registered with a platform live-SHA value (section 28/30), H2 measured complete at X7 (10/10, section 33/34), H4 measured zero at X8 (sections 37/38); H1 remains 未测得. Liveness I-L3/L4/L6 filled from the published surface (section 30), I-L5 Partial, I-L8 still VOID because not all of H1–H4 have values; deliberately-not-done list below |

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
