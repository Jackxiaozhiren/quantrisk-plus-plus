# V9_LEDGER.md — cross-session state for the V9 series

Each entry records what was run, what it printed and what was decided, in that order. A number
quoted from an earlier series is named as a historical reading and re-measured before it is used as
a V9 fact. `V9_PROMPT.md` is the rail set; this file is the state.

---

### 2026-11-11, V9 Phase 0 — the single unit that freezes V8's final-tip census

**Why this phase exists.** `V8_LEDGER.md` Phase 5 §7 prints `deferred` on the full-census row, and
its §6 item 1 says the census reading at the literal final tip `5ec3fab` (development-side
vantage; the sweep has no CI lane) is a session reading:
it lives in the handoff and in agent-local memory, not in the repository. V8 could not fix that in
its own file, because a tracked file cannot name the SHA of the commit that contains it without
moving the tip it measures. V9 starts above `5ec3fab`; for V9 that revision is an ancestor, so the
self-reference disappears. That is the entire mechanism, and it is why this unit needs no new
guard, plant, ceiling key, CI step or lane.

**Approval, verbatim.** `启动 V9，只做 D 项` (2026-11-11). This is a **single-unit** approval,
recorded here before any outward action. It covers D1, this Phase 0 entry, the attestation, the
Phase 5 report, the terminal entry, the two named pushes and their CI attribution. The earlier
`全部授权批准，我都听你的，请按照你的思路建议进行` (2026-11-11) was a delegation of judgement, not
a scope-bearing authorisation; acting on it in the preceding turn produced no commit. The V8
series-wide approval is spent and is not reused.

**Not authorised:** items A (repairing `V7_PROMPT.md` §8), B (reopening the sweep vantage) and C
(a declarative re-run of the evidence chain); editing any earlier prompt or ledger; a harness
redesign; a tag movement or release asset replacement; a new census at V9's own tip; a new CI lane,
plant, guard, ceiling key or living document; and a third push.

**Revision and vantage.** `HEAD` = `origin/main` = platform `main` =
`5ec3fabe4fa8c83584a50b3ab66b357ae13094e9`; `git status --porcelain` prints 0 lines. Vantage: the
development checkout, `.venv` Python 3.12, macOS, the same WorkBuddy interpreter shim earlier
series recorded. `.git/info/exclude` still ignores `.workbuddy/`, so agent-local memory does not
enter the formatter census. `git cat-file -e 5ec3fab^{commit}` and
`git merge-base --is-ancestor 5ec3fab HEAD` both exit 0 at this tip. Git smart-HTTP remains
blocked, so both pushes use the Git Data API with `force: false` and per-object SHA verification.

**The three premises, re-measured at this tip.**

1. **The published chain is frozen.** `refs/tags/v1.9.0` is tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`, and that commit is
   an ancestor of `HEAD`. Release `424060629` is `v1.9.0`, published `2026-10-26T09:35:44Z`, with
   `CITATION.cff` 2,978, `manifest.json` 55,780, `quantrisk-suite-results.zip` 145,672 and
   `technical_report.pdf` 1,005,786 bytes, all created `09:35:41Z` and updated
   `09:35:42Z`–`09:35:43Z`. `tools.verify_evidence_manifest` prints `Evidence is intact.` with 95
   entries and `0 on disk but not in the manifest`. No regeneration occurred.
2. **The pin is a guard, not a sentence.** `--reading artifact_revision` prints
   `artifact_revision 17df062040b8`, `pinned_revision 17df062040b8`, `pin_holds true`, `gap 0`,
   `matches_tip false`, `object_check "the revision names a commit in this clone"`. V9 does not
   weaken it; the V7 forged cases are not re-run here because no code moves.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** `--check-ceilings`
   prints **15** keys, 13 `ok`, 2 `SKIP`. `plants_not_rejected_by_their_guard` prints
   `precondition absent` and its `corpus` says the collector measures only the declaration because
   the sweep's gitignored scratch never reaches the runner. `installed_user_identity_mismatch`
   prints `precondition absent` and its `corpus` says the clean-venv probe installs a second
   environment the runner cannot have. Both reasons still agree with their `corpus` and
   `can_fail_because` fields. V9 does not give either a runner-side verdict.

**The archive re-counted at `5ec3fab`.**

| quantity | command that produced the reading | value |
|---|---|---|
| registry tasks / suite members | `--reading registry_parity`; `with_extras_census` | 19 / 19, `mismatch []`; `gap 0`, 19 / 19 |
| plants | `runner --list` | **195** (V8's last full census `195/195` at `5ec3fab` — development-side vantage; the sweep has no CI lane) |
| ceiling keys | `--check-ceilings` | **15** — 13 `ok`, 2 `SKIP`, 0 `FAIL` |
| manifest | `tools.verify_evidence_manifest` | `Evidence is intact.` (95 entries) |
| formatter corpus | `--reading formatter_census` | **240 / 240**, both differences empty |
| pytest nodes | `--collect-only`; `measure_offline_collection` | **560**; offline **491**, `collection_errors 0` |
| named CI steps | the workflow's `- name:` lines | **34** |
| living documents / lane contract | `docs_rederivation`; `lanes_documented_vs_executed` | 5 documents, `gap 0`, `derived {95, 195, 19, 19}`; `gap 0` |
| artifact revision / runtime reachability | two readings | `gap 0`, `pin_holds true`, `matches_tip false`; `reached_by_neither []` |
| static gates | `ruff check .`; `ruff format --check .`; `mypy python/quantrisk tools` | `All checks passed!`; `240 files already formatted`; `Success: no issues found in 74 source files` |
| residual markers | `grep -rnE '\b(TODO|FIXME|XXX|HACK)\b'` over `python/ tools/ tests/ cpp/ bindings/` | **0** |
| latest three CI runs | platform API | `42815355663`, `42813273094`, `42808340869` — all `completed / success` |

**What this unit takes, and what it excludes.** It takes one finding, D1: a named, machine-readable
attestation of V8's literal-final-tip census, with its revision, vantage and evidence limit, and a
verification reading that reddens a forged revision and a forged count. The verification reading
uses only git's own object/ancestry queries and the existing `runner --list`; it is recorded in
this ledger as a command and its output, and it is not a new guard, plant, ceiling key, CI step or
lane. V9 excludes a new census at its own tip: D1 fixes an existing reading, and re-running the
sweep at V9's tip would create another session-only reading and hand the same deferral to a V10.
V9 excludes changing any source, policy asset, living document, artifact, tag or release asset,
and excludes editing `V8_LEDGER.md`, whose `deferred` row is a historical reading.

**Deliberately not done in Phase 0.** No source file, policy asset or document was edited, no
census was run, no attestation was written, no report section was written and no push was made.
Every number above is a reading at `5ec3fab`. The attestation and its forged proofs belong to the
implementation commit; no verdict is claimed before the tool prints it.

**The two pushes.** The first carries Phase 0, the implementation and the Phase 5 report; the
second carries the terminal entry only. No third is implied. Each push's CI is read from the API
after the tool reports it; the first tip's run is attributed in the terminal entry and the second
tip's run in the session handoff.

---
