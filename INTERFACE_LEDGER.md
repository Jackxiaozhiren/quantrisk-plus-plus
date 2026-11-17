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
| I-L3 | VOID | No deployment exists; no build output to probe for request-execution paths |
| I-L4 | VOID | No deployment configured; no cost diff over a real range |
| I-L5 | Partial | `test_the_build_opens_no_socket` refuses `socket.socket`, `create_connection` and `getaddrinfo` for a full build; a build with the network actually down was not run, and a subprocess making a network call would escape this probe |
| I-L6 | VOID | Manifest and registry exist, but no machine-readable response surface exists to inspect |
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
| H2 provenance completeness | 未测得 | 未取得 | 未取得 | 未测得 |
| H3 zero page drift | Mechanism proven at `28727f4`; value 未取得 | `python -m quantrisk.interface.drift --check` + committed `build/site.lock` | local and runner (see section 15's successor when pushed) | The gate exists and is proven falsifiable by a named plant; the zero-drift *value* over a published surface is still 未测得 because no deploy exists |
| H4 zero cost | 未测得 | 未取得 | 未取得 | 未测得 |

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
| 3 | I2 generator, drift gate proven falsifiable, free-tier CI publish, offline build | 未完成 |
| 4 | I3 value and provenance returned together, refusals name the gap | Done at `25aed30`: `resolve()` returns value + command + revision + digest together and refuses by name on any missing element; plant `provenance-erases-a-recorded-command` proves the guard fails; readings in section 21 |
| 5 | H1–H4 measured, liveness filled, deliberately-not-done list | Partial: liveness filled as VOID, H1–H4 unmeasured, deliberately-not-done list below |

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
