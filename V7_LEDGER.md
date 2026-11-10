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
