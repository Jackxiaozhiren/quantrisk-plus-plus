# V6_LEDGER.md — the cross-session state of the V6 series

V5 closed at `bb914624801bbddeee091914bd42bc39ad4f7d9d` (the terminal entry of its Phase 5 report).
This file starts after that commit and records only tool readings. `V6_PROMPT.md` is delivered by
V6-01, the first unit of this series. A reading in an earlier ledger is an inherited claim until this
file re-measures it.

### 2026-11-09, V6 Phase 0 — the archive re-counted at `bb91462`, and the first unit chosen

**Why this phase exists.** V5 closed with six handoff items, and the first of them is that the sweep's
vantage was *decided* but never written as permanent. A series that starts by citing the decision
without making it durable repeats the state V5 was written to end. So the launch unit delivers the
rail set and records that decision in it, and nothing else.

**Approval, verbatim.** `授权批准，我都听你的，请按照你的思路建议进行` (2026-11-09). This is the
maintainer's case-by-case approval for one scope unit: the V6 launch, its two pushes, and the
permanent decision in §4 of `V6_PROMPT.md`. It does not authorise G3–G6, an edit to any earlier
prompt, a release, or a second V6 unit.

**Revision and vantage.** `HEAD` = `origin/main` =
`bb914624801bbddeee091914bd42bc39ad4f7d9d`; `git status --porcelain` prints 0 lines. Vantage: the
development checkout, `.venv` Python 3.12, macOS, the same WorkBuddy interpreter shim V3 Phase 5, V4
and V5 recorded. Git smart-HTTP remains blocked, so both pushes use the Git Data API.

**Platform readings, not session memory.** `gh api repos/Jackxiaozhiren/quantrisk-plus-plus/commits/main`
returns `bb914624801bbddeee091914bd42bc39ad4f7d9d`; `refs/tags/v1.9.0` points at tag object
`d9deb7f764b3c16a091dc86effb9d523b1d2c7d0`, dereferenced to commit
`b2dda33f6726d7f36fbe3491aec7cd7a66184809` with tagger `2026-10-20T12:56:35Z`; release `424060629`
was published `2026-10-26T09:35:44Z` with four assets (`CITATION.cff` 2,978; `manifest.json` 55,780;
`quantrisk-suite-results.zip` 145,672; `technical_report.pdf` 1,005,786), all created
`2026-10-26T09:35:41Z` and updated `09:35:42Z`–`09:35:43Z`. Terminal V5 run `42612322840` was
re-read as `completed` / `success`, `run_attempt 1`, `head_sha bb9146248`.

**The archive re-counted at this tip.**

| quantity | command that produced the reading | value |
|---|---|---|
| registry tasks | `--reading registry_parity` | `filesystem_units 19`, mismatch empty |
| suite members | `--reading with_extras_census` | `members 19`, `passed 19`, `gap 0`, `revision 17df062040b8` |
| plants | `runner --list` | **195** |
| ceiling keys | `--check-ceilings` | **15** — 13 `ok`, 2 `SKIP` |
| manifest | `tools.verify_evidence_manifest` | `Evidence is intact.` (95 entries) |
| formatter corpus | `--reading formatter_census` | **234 / 234**, both differences empty |
| pytest nodes | `--collect-only`; `measure_offline_collection` | **560** collected; offline `491`, `collection_errors 0` |
| named CI steps | `grep -c '^      - name:' .github/workflows/ci.yml` | **34** |
| living documents | `--reading docs_rederivation` | `documents 5`, `gap 0` |
| lane contract | `--reading lanes_documented_vs_executed` | `gap 0` |
| artifact revision | `--reading artifact_revision` | `gap 0`, `matches_tip false`, 21 attributed paths |

**What this unit takes.** `G1` (a written V6 prompt) and `G2` (the sweep's vantage made permanent).
G1 is delivered by `V6_PROMPT.md`; G2 is §4 of that file, which states the development-only decision,
the mechanical reason, and the one condition under which it may be revisited. Both are closed by
this unit's readings rather than by a new guard: G2 asks for a written decision, not a code change,
and inventing a guard for a sentence would be the "counting a declaration" failure V5 §4 warns
about.

**What this unit excludes.** G3 (the artifact's pin), G4 (re-reading the two `SKIP` keys at a V6 tip),
G5 (a second vantage for development-only counts) and G6 (the no-silent-re-freeze rule in practice)
are named in `V6_PROMPT.md` §5 and left for later units. No source file, guard, plant, ceiling key,
CI step, living document or committed artifact is changed. `V5_PROMPT.md` is not edited.

**Deliberately not done in Phase 0.** No source file was edited, no plant added, no ceiling key
changed, no CI step added, no census run, no report section written and no push made. Every number
above is a reading at `bb91462`; the `17df062040b8` in the with-extras row is the artifact's own
revision, not this tip.

**The two pushes.** The first carries the Phase 0 commit, `V6_PROMPT.md` and the implementation
readings entry; the second carries this unit's terminal entry only. No third is implied.

---
