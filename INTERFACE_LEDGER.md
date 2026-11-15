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
| I-L2 | VOID | No generator exists; no source scan or drift gate to execute |
| I-L3 | VOID | No deployment exists; no build output to probe for request-execution paths |
| I-L4 | VOID | No deployment configured; no cost diff over a real range |
| I-L5 | VOID | No generator exists; no offline build to execute |
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
| H3 zero page drift | 未测得 | 未取得 | 未取得 | 未测得; the drift gate does not exist, so "not proven effective" applies |
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
| 1b | X1b: one named plant proving the command-form guard fails, restore proving green, mechanism named in a phase report | Done: plant `manifest-records-a-command-that-is-not-a-module-invocation`; red `1 failed`, green `1 passed`, census `196/196` at `465735d`; report in section 10 |
| 2 | I1 CLI provenance surface | 未完成 |
| 3 | I2 generator, drift gate proven falsifiable, free-tier CI publish, offline build | 未完成 |
| 4 | I3 value and provenance returned together, refusals name the gap | 未完成 |
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
section 0.2, so nothing here is a platform reading.

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


