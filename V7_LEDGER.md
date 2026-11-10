# V7_LEDGER.md — cross-session state for the V7 series

Each entry records what was run, what it printed and what was decided, in that order. A number
quoted from an earlier series is named as a historical reading and re-measured before it is used as
a V7 fact. `V7_PROMPT.md` is the rail set; this file is the state.

---

### 2026-11-10, V7 Phase 0 — the series launched at `d975baa`

**Why this phase exists.** V6 closed G1–G6 and left nine deliberately-not-done items in
`V6_LEDGER.md` Phase 5 §4 and seven handoff items in its §6. Item 1 of that handoff names the one
substantive residue: the committed suite artifact's pin is a written decision, not a guard, and a
future series that wants a checkable pin needs a reading with a forged-input or plant proof and its
own approval. This is that series.

**The recommendation this approval accepts.** V7 takes one substantive change — H1, turning V6's
written artifact pin into a two-direction checkable guard by extending the existing
`artifact_revision` reading and its ceiling row, with forged-input proofs in both directions — and
rejects or retains the rest with evidence. No harness redesign, no new CI lane, no new plant,
ceiling key or CI step, no re-run of the evidence chain, no regeneration of a published asset.
This is the smallest change that leaves the repository more checkable than it found it: `V5_PROMPT.md`
§1 forbids manufacturing new gates to replace inconvenient ones, so V7 extends an existing guard
and an existing ceiling row rather than building machinery to police a sentence. The pin also makes
V6's "no silent re-freeze" rule executable, because an undeclared rewrite of the committed artifact
now fails a reading instead of only contradicting prose.

**Approval, verbatim.** `授权启动 V7，按你的建议推进剩余系列` (2026-11-10). Per `V7_PROMPT.md` §6
this is the maintainer's **series-wide** approval, recorded here before any outward action. It
explicitly overrides the case-by-case rule for the V7 series and covers H1–H7, the Phase 0 entry,
the implementation, the Phase 5 report, the terminal entry and the two named pushes. It does **not**
authorise editing any earlier prompt or `V7_PROMPT.md`, a harness redesign that reopens §4, a
declared re-run of the evidence chain, a tag movement or release asset replacement, a new CI lane,
or a third push. The V6 series-wide approval (`继续` + `整个剩余系列（推荐）`) is spent and is not
reused; the V6-01 approval is likewise spent.

**Revision and vantage.** `HEAD` = `origin/main` = platform `main` =
`d975baa7c9da67de776332b0f0321e27471cef37`; `git status --porcelain` prints 0 lines. Vantage: the
development checkout, `.venv` Python 3.12, macOS, the same WorkBuddy interpreter shim earlier
series recorded. `.git/info/exclude` still ignores `.workbuddy/`, so agent-local memory does not
enter the formatter census. Git smart-HTTP remains blocked, so both pushes use the Git Data API
with `force: false` and per-object SHA verification.

**The three premises, re-measured at this tip.**

1. **The published chain is frozen.** `refs/tags/v1.9.0` is tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
   is `v1.9.0`, published `2026-10-26T09:35:44Z`, with `CITATION.cff` 2,978, `manifest.json`
   55,780, `quantrisk-suite-results.zip` 145,672 and `technical_report.pdf` 1,005,786 bytes, all
   created `09:35:41Z` and updated `09:35:42Z`–`09:35:43Z`. `tools.verify_evidence_manifest`
   prints `Evidence is intact.` with 95 entries and `0 on disk but not in the manifest`. Every
   field matches V6 Phase 5 §8. No regeneration occurred.
2. **The committed suite artifact is pinned in writing but not guarded.**
   `benchmarks/suite/results/suite_run.json` names `git_commit 17df062040b8`,
   `binary_git_commit af7595749188`, `working_tree_dirty true` and 21 `uncommitted_paths`; its
   `provenance` begins `ran from 17df062040b8 plus the uncommitted changes ...`. `--reading
   artifact_revision` prints `gap 0`, `matches_tip false`, `object_check "the revision names a
   commit in this clone"`, `repository_is_shallow false`, `tip_being_verified
   d975baa7c9da67de776332b0f0321e27471cef37`. The reading checks format, object presence and
   provenance self-consistency; it never compares `git_commit` with the pin. A forged revision that
   is also a real commit in this repository is therefore still `gap 0`. That is H1.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** `--check-ceilings`
   prints **15** keys, 13 `ok`, 2 `SKIP`. `plants_not_rejected_by_their_guard` prints
   `precondition absent` and its `corpus` says the collector measures only the declaration because
   the sweep's gitignored scratch never reaches the runner. `installed_user_identity_mismatch`
   prints `precondition absent` and its `corpus` says the clean-venv probe installs a second
   environment the runner cannot have. Both printed reasons still agree with their `corpus` and
   `can_fail_because` fields in `tools/refactor_ceilings.json`.

**The archive re-counted at `d975baa`.**

| quantity | command that produced the reading | value |
|---|---|---|
| registry tasks / suite members | `--reading registry_parity`; `with_extras_census` | 19 / 19; `gap 0` |
| plants | `runner --list` | **195** (last full census `195/195` at `9486c7a` — development-side vantage; the sweep has no CI lane) |
| ceiling keys | `--check-ceilings` | **15** — 13 `ok`, 2 `SKIP` |
| manifest | `tools.verify_evidence_manifest` | `Evidence is intact.` (95 entries) |
| formatter corpus | `--reading formatter_census` | **236 / 236**, both differences empty, `reported_would_reformat 0` |
| pytest nodes | `--collect-only`; `measure_offline_collection` | **560**; offline **491**, `collection_errors 0` |
| named CI steps | the workflow's `- name:` lines | **34** |
| living documents / lane contract | `docs_rederivation`; `lanes_documented_vs_executed` | 5 documents, `gap 0`, `derived {95, 195, 19, 19}`; `gap 0` |
| artifact revision / runtime reachability | two readings | `gap 0`; `reached_by_neither` empty |
| static gates | `ruff check .`; `ruff format --check .`; `mypy python/quantrisk tools` | `All checks passed!`; `236 files already formatted`; `Success: no issues found in 74 source files` |

**What this unit takes, and what it excludes.** It takes H1 (a declared `pinned_revision` in the
`artifact_revision_gap` ceiling row and a `pin` check in `artifact_revision()`, with two forged-input
proofs), H2 (both `SKIP` keys re-read and retained), H3 (every census citation labelled
development-side), H4 (no harness redesign, stated here before any source file is touched), H5
(the pin guard plus two platform re-reads), H6 (the size ratchet and no prompt edits) and H7 (the
environmental pytest failure attributed, not silenced), together with the Phase 5 report. It
excludes a new plant, ceiling key, CI step or lane; it excludes editing any prompt, the manifest,
`benchmarks/suite/results/suite_run.json`, `cpp/`, `bindings/`, `CMakeLists.txt`, `paper/` or any
release asset; and it excludes a third push. `V6_PROMPT.md` §4 already closes the sweep's vantage;
this unit does not reopen it.

**Deliberately not done in Phase 0.** No source file, policy asset or document was edited, no
census was run, no report section was written and no push was made. Every number above is a reading
at `d975baa`. The full census and the final local `pytest -q` belong to the implementation tip, on
a clean tree after the H1 commit.

**The two pushes.** The first carries the Phase 0 commit, the implementation commit and the Phase 5
report; the second carries the terminal entry only. No third is implied. Each push's CI is read from
the API after the tool reports it; the first tip's run is attributed in the terminal entry and the
second tip's run in the session handoff.

---

### 2026-11-10, V7-01 implementation — the pin becomes a guard, and six findings are decided

**What changed.** Three tracked source/policy files and this ledger. No new plant, ceiling key, CI
step, lane or living-document count; no committed artifact, manifest entry or release asset moved;
no prompt was edited.

| file | change | why |
|---|---|---|
| `tools/refactor_ceilings.json` | `artifact_revision_gap` now declares `pinned_revision: "17df062040b8"` with `pinned_revision_why`; `law`, `metric`, `corpus`, `can_fail_because` and `reach_by_phase` extended to describe the new refusal; still one key | the pin is a declaration in the policy asset, so both sides can be forged and compared (N5) |
| `tools/inventory_orphan_code.py` | new `pinned_suite_revision()`; `artifact_revision()` refuses a committed artifact whose `git_commit` differs from the declared pin, and a policy asset with no usable declaration; returns `pinned_revision`, `pin_holds` and `pin_check` | extends the existing V5 F4 guard and ceiling row rather than building machinery to police a sentence |
| `tests/python/test_artifact_metadata.py` | the existing V4-06 / V5-02 F4 test now carries four V7 forged-input cases, all inside the same function | the guard reddens in both directions, and the exempt fresh vantage stays green; the counted pair stays 560 / 491 |
| `V7_LEDGER.md` | this entry | one finding, one named commit, one ledger entry |

**Why the committed vantage can be required without failing the benchmark job.** A file cannot carry
the SHA of the commit that contains it, so the committed `suite_run.json` necessarily has
`matches_tip false`; the fresh artifact the benchmark job writes names the tip of the run that wrote
it and therefore `matches_tip true`. The pin check applies only in the former case. This is the
distinction V6 G3 drew in prose, now executable.

**H1 — the readings.** `--reading artifact_revision` on this tree prints `gap 0`,
`pinned_revision 17df062040b8`, `pin_holds true`,
`pin_check "the committed artifact names the pinned historical revision"`, `matches_tip false`,
`object_check "the revision names a commit in this clone"`, `problems []`,
`tip_being_verified 14fde09f64025593fbfbb0163a3bf72e2b1793ac`. The four forged cases:

| forged input | reading | verdict |
|---|---|---|
| committed artifact's `git_commit` changed to `bb914624801b…`, a real commit, with its `provenance` rewritten to name it | `gap 1`, `pin_holds false`, exactly one problem: `the committed artifact names bb914624801b but the policy asset pins it to 17df062040b8; an undeclared re-freeze would otherwise pass the object and provenance checks` | every V5 check still holds; **only the pin refuses** |
| policy asset's `pinned_revision` changed to `deadbeefdead` | `gap 1`, `pin_holds false` | the declaration side reddens |
| `pinned_revision` deleted from the policy asset | `gap 1`, `pinned_revision None`, `pin_check "unavailable: the policy asset declares no usable pinned_revision"` | a missing declaration is a refusal, not a zero |
| fresh artifact naming `tip_being_verified`, with a matching provenance | `matches_tip true`, `gap 0`, `pin_holds None`, `pin_check "not applicable: the fresh artifact names the tip of the run that wrote it"` | the benchmark job's CI upload stays green |
| true shallow-clone vantage (`repository_is_shallow true`, `revision_exists false`) | `gap 0`, `object_check "skipped: a shallow clone cannot tell an earlier revision from an absent one"`, `pin_holds true`, `problems []` | the V5-02 repair and the pin check coexist |

The extended F4 guard prints `1 passed in 0.92s`. Full local `pytest -q --basetemp=/tmp/qr-v7-pre`
prints `1 failed, 559 passed in 117.21s`: the sole failure is
`test_a_restored_plant_cannot_be_read_back_from_a_stale_bytecode_cache`, which says the sandbox
wrote no bytecode beside the module and so cannot reproduce the defect. No marker, tolerance or
test deletion was added. Static gates print `238 files already formatted`, `All checks passed!` and
`Success: no issues found in 74 source files`; `--check-ceilings` prints 15 keys, 13 `ok`, 2
`SKIP`, `artifact_revision_gap 0`.

**H2 — both `SKIP` keys re-read and retained.** At this tip both still print
`precondition absent`: the sweep's gitignored scratch never reaches the runner, and the clean-venv
probe installs a second environment the runner cannot have. Each `corpus` agrees with the printed
reason. Neither was retired, promoted, given a `may_be_unmeasured` flag it did not have, or given a
runner-side verdict.

**H3 — the census verdict stays labelled.** `docs_rederivation` prints `documents 5`, `gap 0`,
`derived {manifest_artifacts 95, plants 195, registry_tasks 19, suite_members 19}`, `mismatches []`
and `source_disagreements []`. Every V7 citation of `195/195` carries
`(development-side vantage; the sweep has no CI lane)` on the same line, including
`V7_PROMPT.md` §3 and the Phase 0 row above. No new document promotes it.

**H4 — no harness redesign.** Phase 0 stated this before any source file was touched, which is the
condition `V6_PROMPT.md` §4 sets for not reopening the question. No sweep lane, plant, ceiling key
or CI step was added; `plants_not_rejected_by_their_guard` and
`installed_user_identity_mismatch` remain `SKIP`, and the installed-surface proof remains a V5
development-only reading.

**H5 — no silent re-freeze is now executable.** An undeclared rewrite of the committed
`suite_run.json` moves `git_commit` off `17df062040b8`; since the rewritten file still cannot name
the commit that contains it, `matches_tip` stays false and the pin check refuses it. The manifest
(95 entries, `Evidence is intact.`) and the platform's tag, release and four assets were re-read in
Phase 0 and are re-read again in Phase 5; this unit regenerated none.

**H6 — the size ratchet, reported rather than repaired.** `V7_PROMPT.md` is 154 lines with **98**
lines in the prose sections (§1–§3, §6–§8), measured by the same heading-span rule that gives
`V6_PROMPT.md` 146 / 88. `V3_PROMPT.md` §0's hard bound of 431 holds with margin, but this
prompt's §8 soft figure of 88 is exceeded by 10 lines. §8 permits that only when the report names a
V6 rule that was never executed, and there is one: `V6_PROMPT.md` §7 says an implementation unit
"ships the change, its guard, its plant and its readings in one named commit", yet both V6
implementation units shipped written decisions only and `V6_LEDGER.md` §9 records that V6 changed
no source file, guard, plant, ceiling key or CI step. V7 H1 is the first unit to actually ship a
guard and its proofs. The added lines sit in §6's series-wide approval clause and §5's finding
table; §8's "growth only in §5 and §3" is the one sentence of the prompt V7 does not satisfy.
Editing the prompt is excluded from the series-wide approval by §6, so the sentence is left
standing and named here and in the Phase 5 report instead of being quietly reworded. H6 is
therefore **not fully fixed** and appears in the deliberately-not-done list.

**H7 — the local failure is environmental.** The `1 failed, 559 passed` reading is attributed to
the sandbox bytecode-cache plant above; CI's own pytest verdict is read in the Phase 5 per-lane
table rather than substituted by a marker.

**The counts after the change, and their deltas against Phase 0.**

| quantity | Phase 0 at `d975baa` | after this edit | delta |
|---|---|---|---|
| formatter corpus | 236 / 236 | **238 / 238**, both differences empty | **+2**, the two new tracked V7 `.md` files |
| plants / ceiling keys | 195 / 15 (13 `ok`, 2 `SKIP`) | **195 / 15** (13 / 2) | 0 |
| pytest nodes | 560 / 491, `collection_errors 0` | **560 / 491**, `collection_errors 0` | 0 |
| named CI steps / suite members | 34 / 19 | **34 / 19** | 0 |
| manifest / docs / lanes / with-extras / revision / runtime | 95 intact; five gaps at 0 | **95 intact; five gaps at 0** | 0 |
| printed derived values | `{95, 195, 19, 19}` | **`{95, 195, 19, 19}`** | 0 |

**What this unit deliberately did not do.** It added no plant, ceiling key, CI step or lane; it did
not edit a prompt; it did not regenerate `suite_run.json`, the manifest, a report or a release
asset; it did not move `v1.9.0`; and it did not run the full census or the targeted sweep here —
those require a clean tree after this commit and are attributed in the Phase 5 report.

**The first push.** This entry, the Phase 0 commit and the Phase 5 report ship together in the
first of the two pushes. No outcome is written here for a push that has not happened.

---

### 2026-11-10, V7 Phase 5 — the report, the liveness table, and the archival confirmation

**How this was assembled.** From this ledger's Phase 0 and V7-01 entries plus fresh readings at
`0c239c589c0804e53b4a9da10814bb713518141f` on a clean tree. Where a number appeared in an earlier
entry it was re-measured rather than copied; the census line is quoted from `/tmp/v7_census.log`
line 998, not retyped. Every platform figure is a fresh API reading.

#### 1. Evidence ledger

| id | verdict | probe | closing commit |
|---|---|---|---|
| H1 | **fixed** | `artifact_revision_gap` declares `pinned_revision`, `artifact_revision()` compares it with the committed artifact and refuses a missing declaration; four forged-input cases in the extended F4 test redden both sides while the fresh vantage stays at `gap 0`; `--check-ceilings` prints 15 keys with `artifact_revision_gap 0` | `0c239c5` |
| H2 | **fixed** | both `SKIP` keys re-read at a V7 tip, each `corpus` agreeing with its printed `precondition absent` reason; both retained, neither promoted, retired or given a new flag | `0c239c5` |
| H3 | **fixed** | every V7 citation of `195/195` carries the development-side label on the same line; `docs_rederivation gap 0`, `documents 5`, `derived {95, 195, 19, 19}` | `14fde09`, `0c239c5` |
| H4 | **fixed** | Phase 0 states no harness redesign before any source file was touched; V7 added no sweep lane, plant, ceiling key or CI step; §4's decision is not reopened | `14fde09`, `0c239c5` |
| H5 | **fixed** | an undeclared rewrite of the committed artifact now has `matches_tip false` and `git_commit != 17df062040b8`, so the pin check refuses it; manifest (95 intact) and platform tag/release/four assets re-read in Phase 0 and §8 below; nothing regenerated | `0c239c5`, this entry |
| H6 | **PARTIAL — named in §4** | `V3_PROMPT.md` §0's 431-line bound holds (154 total / 98 prose lines); this prompt's §8 soft figure of 88 is exceeded by 10, §8's stated condition is met by naming `V6_PROMPT.md` §7's never-executed "implementation unit ships a guard and a plant" rule, but §8's "growth only in §5 and §3" is not satisfied and the prompt is not edited because §6 excludes that from the series-wide approval | `14fde09`, reported here |
| H7 | **fixed** | `1 failed, 559 passed in 224.11s` attributed to the sandbox bytecode-cache plant in §7 below; no marker, tolerance or test deletion added; CI's pytest verdict is read instead | `0c239c5` |

#### 2. Liveness table, re-evaluated at `0c239c5`

| # | law | verdict | the reading that decided it |
|---|---|---|---|
| N1 | requirement truth | **ACTIVE** | `registry_parity`: `filesystem_units 19`, `registry_sources 19`, `mismatch []` |
| N2 | advertised surface honesty | **ACTIVE** | the V5 F5 clean-venv wheel proof (19 tasks, 7 validations, one study, one refusal, zero residue); labelled development-only in §7, not promoted |
| N3 | lane contract | **ACTIVE** | `lanes_documented_vs_executed gap 0`; **34** named CI steps; the five `tools.inventory_orphan_code` steps are unchanged |
| N4 | no silence by count | **ACTIVE** | `with_extras_census gap 0`, `members 19`, `passed 19`; `docs_rederivation gap 0`, `mismatches []`, `source_disagreements []` |
| N5 | declarations are checkable | **ACTIVE** | 15 keys, 13 `ok`, 2 `SKIP` with named preconditions; the new `pinned_revision` declaration is compared in **both** directions — a drifted artifact and a wrong or missing declaration each print `gap 1` |
| N6 | runtime reachability | **ACTIVE** | `runtime_reachability` prints `reached_by_neither []` |
| N7 | one finding, one commit | **ACTIVE** | Phase 0, V7-01 implementation, this report and the terminal entry map to H1–H7 and the two named pushes; §8 below carries the mapping |
| N8 | no gate weakened | **ACTIVE** | the V7 range adds no `skip`/`xfail`, no exemption, no tolerance and deletes no test; the ceilings change strengthens one existing key and adds none |
| N9 | plant liveness | **ACTIVE** | `195/195 planted defects were rejected by their guard.` at `0c239c5`, clean tree, 195 `ok   caught` rows, zero other verdict rows (development-side vantage; the sweep has no CI lane) |
| N10 | one re-run | **ACTIVE, not triggered** | no evidence artifact regenerated in V7: `suite_run.json` still names `17df062040b8`, the manifest still holds 95 intact entries, and no freeze was re-run |
| N11 | facts precedence | **ACTIVE** | `docs_rederivation gap 0`, 5 documents, `derived {95, 195, 19, 19}`; no printed count moved, so no document required re-derivation |
| N12 | baseline purity and per-lane provenance | **ACTIVE** | §7 names a revision, an environment **and** a vantage for every lane; the baseline was measured at `d975baa`, whose own CI run `42761772828` is `completed / success`, attempt 1 |

#### 3. The ceilings file's final state

`tools/refactor_ceilings.json` carries **15** keys, unchanged in count by V7. Thirteen are `ok` at
`0`; two are `SKIP` with `may_be_unmeasured: true`:
`plants_not_rejected_by_their_guard` and `installed_user_identity_mismatch`.

**Review notes.** V7 added no key, loosened no `max`, retired no `SKIP` and added no
`may_be_unmeasured`. Its only change is inside `artifact_revision_gap`: a new `pinned_revision`
declaration (`17df062040b8`), a matching `pinned_revision_why`, and `law`, `metric`, `corpus`,
`can_fail_because` and `reach_by_phase` extended to describe the new refusal. The declaration is
read by `pinned_suite_revision()` rather than duplicated as a literal in the collector, so a forged
policy asset reddens the reading. `can_fail_because` now names four live failure modes instead of
three, and the V5-02 shallow-clone repair is unchanged: the lint vantage's `object_check` still
reads `skipped`, and the pin check does not depend on object presence. A future series that wants a
runner-side verdict for either `SKIP` must redesign the harness first; it may not retire a key to
make a local reading look like a gate.

#### 4. The deliberately-not-done list

1. **The sweep still has no CI lane.** `plants_not_rejected_by_their_guard` stays `SKIP`
   permanently; `195/195` is a development-side reading. Converting it requires the harness
   redesign `V6_PROMPT.md` §4 names as the sole condition, excluded by V7's Phase 0.
2. **The installed-surface proof is still not a CI lane.** The V5 F5 clean-venv proof remains
   local; the runner cannot install a second environment without changing the job's shape.
3. **The committed `suite_run.json` was not regenerated.** V7 guarded its pin rather than
   refreshing it. A declared re-run remains a future unit with its own approval, because it would
   move `evidence/manifest.json` and the release asset set.
4. **No second vantage was built for `195/195`.** The 195 declared plants have two vantages; the
   rejection verdict has one. V7 labelled it rather than promoting it.
5. **`V7_PROMPT.md` §8's 88-line soft figure is exceeded** (154 total / 98 prose lines). §8's
   "growth only in §5 and §3" is not satisfied: the extra lines sit in §6's series-wide approval
   clause as well. §6 excludes editing this prompt from the series-wide approval, so the sentence
   is named rather than reworded; H6 is partial, not fixed.
6. **The full census was captured at the implementation tip, not the literal final tip.** It ran
   on `0c239c5` on a clean tree; the report and terminal commits that follow are ledger-only.
   `V7_PROMPT.md` §0 says "final V7 tip" and V6 §7 made the same claim about `9486c7a`. This is
   the same structural gap named in H6's evidence row, carried to V8 rather than disguised.
7. **No new plant, ceiling key, CI step or lane.** H1 extends an existing guard, ceiling row and
   pytest guard; adding machinery to police a sentence is the failure V5 §1 warns about.
8. **The report PDF was not rebuilt.** `tools.build_report` stays dev-only; the byte-bound PDF and
   `paper/technical_report.tex` were read, not re-rendered.
9. **No V7 release.** The published asset set is unchanged by design; H5's check is that it did
   not move.
10. **The one local pytest failure was not silenced.**
    `test_a_restored_plant_cannot_be_read_back_from_a_stale_bytecode_cache` fails only under this
    sandbox's bytecode-cache plant; it is named in §7 as a failure with its environment, and CI's
    `490 passed, 5 skipped` is read instead. No marker was added.

#### 5. Premises audit

1. **The published chain is frozen and V7 must not move it silently.** *Final reading:* tag
   object `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
   published `2026-10-26T09:35:44Z` with four assets sized 2,978 / 55,780 / 145,672 / 1,005,786
   bytes, created `09:35:41Z`, updated `09:35:42Z`–`09:35:43Z`; manifest 95 entries and
   `Evidence is intact.`. **Closed**; every field matches Phase 0's row.
2. **The committed suite artifact is pinned in writing but not guarded.** *Final reading:*
   `--reading artifact_revision` at `0c239c5` prints `artifact_revision 17df062040b8`,
   `pinned_revision 17df062040b8`, `pin_holds true`, `gap 0`, `matches_tip false`,
   `object_check "the revision names a commit in this clone"`, `problems []`. **Closed**: the
   residue named in premise 2 is now a guard, and the four forged cases in the implementation
   entry prove it reddens.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** *Final reading:* 15
   keys, 13 `ok`, 2 `SKIP`; both printed `precondition absent` with their `corpus` describing the
   missing runner precondition; both retained. **Closed**; the residue is that both verdicts
   remain development-only, which H2 labelled rather than hid.

#### 6. Series handoff — what V8 must contain

Derived from this run's evidence, not from the prompt's prose:

1. **The pin is now a guard with a declared owner.** Changing `pinned_revision` is a policy
   decision, not a code edit; a V8 unit that regenerates `suite_run.json` must change both the
   artifact and the declaration in its Phase 0 and Phase 5, and must carry its own approval.
2. **The sweep's vantage is still closed.** `V6_PROMPT.md` §4 and `V7_PROMPT.md` §4 permit
   reopening only through a harness redesign whose Phase 0 says so. A V8 that lists it as an open
   question has read neither.
3. **The two `SKIP` keys still have no runner vantage.** They were re-read twice more and retained
   with reasons; a second vantage for development-only counts remains an idea, not a gate.
4. **The printed `195/195` line is labelled.** Any new document quoting the census verdict must
   label it development-side on the same line, and `docs_rederivation` must stay at `gap 0`.
5. **Two size-ratchet sentences are standing and unsatisfied.** `V7_PROMPT.md` §8's 88-line soft
   figure and "growth only in §5 and §3" were reported as partial rather than reworded. A V8 unit
   that edits that prompt needs its own verbatim approval; §6 forbids widening authority.
6. **The census-at-final-tip gap is structural.** V6 and V7 both captured the census on the
   implementation tip, then shipped ledger-only commits. If V8 wants the literal reading, its
   Phase 0 must plan a census after the terminal entry's own push on a clean tree.
7. **No silent re-freeze remains standing.** The 95-entry manifest and the `v1.9.0` assets are
   the published chain; any regeneration must appear in both Phase 0 and Phase 5.
8. **The local pytest failure is environmental.** Do not weaken a gate to turn
   `1 failed, 559 passed` into green; attribute it to the sandbox and read CI instead.

#### 7. Per-lane verification table

| lane | revision | environment | vantage | verdict |
|---|---|---|---|---|
| `ruff check .` | `0c239c5` | macOS, `.venv` Python 3.12, development checkout | development | `All checks passed!` |
| `ruff format --check .` | `0c239c5` | same | development + CI lint | `238 files already formatted` |
| `mypy python/quantrisk tools` | `0c239c5` | same | development | `Success: no issues found in 74 source files` |
| `pytest -q` (full) | `0c239c5` | same, private `--basetemp=/tmp/qr-v7-final` | development | **1 failed, 559 passed in 224.11s**; the failure is the sandbox-only bytecode-cache plant |
| `pytest --collect-only` / `measure_offline_collection` | `0c239c5` | same | development | 560 / 491, `collection_errors 0` |
| mutation sweep, targeted (2 plants) | `0c239c5` | same, clean tree after the implementation commit | development-only | two `1/1 planted defects were rejected by their guard.`, tree 0 dirty |
| mutation sweep, full census | `0c239c5` | same, bulk-delete threshold raised locally | **development-only, labelled** | **195/195**, 195 `ok   caught` rows, 0 other verdict rows, tree 0 dirty, exit 0, 998-line log |
| `--check-ceilings` | `0c239c5` | same | development + CI lint | 15 keys, 13 `ok`, 2 `SKIP`, no `FAIL` |
| `--reading docs_rederivation` | `0c239c5` | same | development + CI lint | `gap 0`, 5 documents, `derived {95, 195, 19, 19}` |
| `--reading lanes_documented_vs_executed` | `0c239c5` | same | development + CI lint | `gap 0` |
| `--reading with_extras_census` | `0c239c5` | same | development + CI lint + benchmark-job fresh artifact | `gap 0`, 19/19 |
| `--reading artifact_revision` | `0c239c5` | same | development (deep clone) + lint (shallow clone) + benchmark (fresh artifact) | `gap 0`, `pin_holds true`, `matches_tip false` in the committed vantage; fresh vantage `matches_tip true` and pin-exempt |
| `--reading formatter_census` / `registry_parity` / `runtime_reachability` | `0c239c5` | same | development + CI lint | 238/238 (both differences empty), 19/19, `reached_by_neither []` |
| `tools.verify_evidence_manifest` | `0c239c5` | same | development + CI lint | `Evidence is intact.` |
| `tools.verify_installed_surface` | `3c6092f` | `/tmp/qr-v5-venv`, wheel from that tree, neutral cwd | **development-only, labelled** | identity, 19 tasks, 7 validations, one study, one refusal, 0 residue |
| CI four jobs | `d975baa` (run `42761772828`) | `ubuntu-latest` `1000010672`–`1000010675`, `macos-15` `1000010673` | runner | `completed / success`, attempt 1, 15 / 14 / 14 / 15 steps; re-read from the API for this report |
| CI four jobs | report tip (first V7 push) | runners named in the terminal entry | runner | **not yet read**; no outcome is written for a push that has not happened |
| CI four jobs | terminal tip (second V7 push) | runners named in the session handoff | runner | **not yet read** |

No lane is marked green on a mixed vantage. The census log contains `tree-did-not-recover` and
`ESCAPED` only inside two plants' claim text at lines 991–992; neither is a verdict row. The one
local failure is named as a failure with its cause and environment, not averaged into the green
rows.

#### 8. Archival confirmation

- **Tree and tip.** `git status --porcelain` prints 0 lines; `HEAD` =
  `0c239c589c0804e53b4a9da10814bb713518141f` before this report's commit, with `origin/main` at
  `d975baa`. The Phase 0, implementation and report commits are pushed in the first V7 push; the
  terminal entry follows in the second, and the session handoff records the final tip.
- **Every V7 commit an ancestor of the remote.** `14fde09` (Phase 0), `0c239c5` (implementation)
  and this report are local ancestors of the terminal commit and ship in the first push; each
  object SHA is checked against the local object before the ref moves. The platform `/compare`
  reading for the pushed range is taken after the push and recorded in the terminal entry; the
  terminal commit is verified after its own push. No reading is written before the tool reports it.
- **CI for every commit.** The baseline `d975baa` has its own run `42761772828`
  (`completed / success`, `run_attempt 1`, four jobs 15 / 14 / 14 / 15, runners
  `1000010672`–`1000010675`, created `05:22:55Z`, updated `05:33:58Z`). The two V7 push tips are
  attributed in the terminal entry and the session handoff after the API reports them; no run is
  named green before it is read. No V7 run is cancelled and no job has 0 steps.
- **Registers and documents re-counted.** `registry_parity` 19/19; `with_extras_census` 19/19,
  `gap 0`; `plant_liveness` 195 and the census's 195/195 (development-side vantage); manifest 95
  intact; `docs_rederivation` 5 documents / `gap 0`; formatter 238/238; nodes 560/491; CI steps
  34; ceiling keys 15. `artifact_revision gap 0` with `pin_holds true`,
  `lanes_documented_vs_executed gap 0`, `runtime_reachability` `reached_by_neither []`.
- **Tags, releases and assets re-read from the platform.** Tag object
  `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
  `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
  (`v1.9.0`) published `2026-10-26T09:35:44Z` with four assets, sizes 2,978 / 55,780 / 145,672 /
  1,005,786 bytes, created `09:35:41Z`, updated `09:35:42Z`–`09:35:43Z`. All match the Phase 0
  rows; no asset was replaced.
- **No stray instrument tracked or left on disk.** `git ls-files -- tools/derive_requires.py
  build/run_sweep.py build/api_push.py` prints nothing; `git check-ignore` confirms
  `build/api_push.py`, `build/run_sweep.py` and `.workbuddy/` are ignored; the census left 0 dirty
  paths and no `_mutation_probe` directory; the only external log is `/tmp/v7_census.log`, outside
  the repository; no background process remains running.

#### 9. What V7 changed, and what it did not

It added `V7_PROMPT.md` and `V7_LEDGER.md`, declared `pinned_revision` inside one existing ceiling
row, extended `artifact_revision()` with a pin check and one helper, and extended one existing
pytest guard with four forged cases. `git diff --name-only d975baa..0c239c5` prints exactly five
paths. It changed no plant total, ceiling-key count, CI step, manifest entry, committed suite
artifact, document count or release asset. It did not touch `cpp/`, `bindings/`,
`CMakeLists.txt`, `PROJECT_SPEC.md`, `REFACTOR_PROMPT.md`, `V3_PROMPT.md`, `V5_PROMPT.md`,
`V6_PROMPT.md`, `evidence/manifest.json` or `paper/`, and it did not move `v1.9.0`.

**The first push.** This report, the Phase 0 commit and the implementation commit are pushed
together in the first of the two pushes authorised in the V7 Phase 0 entry. Its CI is read once the
tool reports it and recorded in the terminal entry; no outcome is stated here for a push that has
not happened.

---
