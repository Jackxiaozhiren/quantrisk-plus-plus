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

### 2026-11-09, V6-01 implementation — the rail set, and the sweep's vantage made permanent

**What changed.** Two files. `V6_PROMPT.md` (146 lines; prose sections §1–§3 and §6–§8 span 88
lines against V3's 431-line bound) and this entry. No source file, guard, plant, ceiling key, CI
step, living document or committed artifact was touched.

| file | change | why |
|---|---|---|
| `V6_PROMPT.md` | new: premises, Facts Protocol, lane inventory at `bb91462`, §4's permanent decision, G1–G6, approval rule, DoD, size ratchet | G1: V6 has a written rail set before it takes a code finding |
| `V6_LEDGER.md` | Phase 0 entry (70 lines) and this entry | the cross-session state, written from readings |

**G1 closed.** The file states the three premises with their `bb91462` readings, the six-clause
Facts Protocol, the lane inventory, the six candidate findings each with a `check:` predicate, the
one-unit-per-approval rule, the DoD and the size ratchet. Its §6 was followed by this unit: the
approval is recorded verbatim in the Phase 0 entry, and the unit's two pushes are named there.

**G2 closed by writing, not by a guard.** `V6_PROMPT.md` §4 states that
`plants_not_rejected_by_their_guard` stays `SKIP` permanently, gives the mechanical reason (the
sweep rewrites tracked files and writes gitignored scratch, so a key computed from its summary line
could not fail on the runner that evaluates it), and names the only condition under which the
decision may be revisited: a unit whose Phase 0 says it is redesigning the harness so the sweep no
longer touches tracked files, carrying its own approval. No V6 entry may now list the vantage as
open. The key's declaration in `tools/refactor_ceilings.json` is unchanged and still agrees with
that reason, which is the second half of G2's `check:`.

**The counts after the change, and their deltas.**

| quantity | before (Phase 0) | after (`2a902eb` + this file) | delta |
|---|---|---|---|
| formatter corpus | 234 / 234 | **236 / 236** | +2, the two new tracked `.md` files |
| plants | 195 | **195** | 0 |
| ceiling keys | 15 (13 `ok` / 2 `SKIP`) | **15 (13 / 2)** | 0 |
| manifest entries | 95 | **95** | 0 |
| pytest nodes | 560 / 491 | **560 / 491** | 0 |
| named CI steps | 34 | **34** | 0 |
| registry / suite members | 19 / 19 | **19 / 19** | 0 |

**What the gates print at this tip.** `ruff check .` → `All checks passed!`; `ruff format --check .`
→ `236 files already formatted`; `--check-ceilings` → 15 keys, 13 `ok`, 2 `SKIP`;
`--reading formatter_census` → `tracked_formattable 236`, `walked_formattable 236`,
`reported_already_formatted 236`, both differences empty; `--reading docs_rederivation` → `gap 0`;
`--reading lanes_documented_vs_executed` → `gap 0`; `--reading with_extras_census` → `gap 0`;
`--reading artifact_revision` → `gap 0`, `matches_tip false`; `tools.verify_evidence_manifest` →
`Evidence is intact.`; `pytest --collect-only -q` → `560 tests collected`;
`measure_offline_collection` → `491 tests collected`. No full census and no local `pytest -q` is
claimed for this unit: it changes no code, so the last captured census remains `195/195` at
`ea8beb4`, and the next one belongs to the final V6 tip.

**What this unit deliberately did not do.** G3 (the artifact's pin), G4 (re-reading the two `SKIP`
keys at a V6 tip), G5 (a second vantage for development-only counts) and G6 (the re-freeze rule in
practice) are open and named in `V6_PROMPT.md` §5. No earlier prompt was amended, no release was
cut, and no evidence artifact was regenerated.

**The first push.** This entry and `V6_PROMPT.md` are pushed together in the first of the two
pushes authorised in the Phase 0 entry. Its CI is read once the tool reports it and recorded in the
next entry; this file states no outcome for a push that has not happened.

---

### 2026-11-09, V6-01 terminal entry — the rail set's tip is green

**The tip's CI, attributed.** Run `42615110830` on
`1804c866150ee206571acbfb602836baf6782615` is `completed` / `success`, `run_attempt 1`, created
`12:12:44Z`, updated `12:24:08Z`. Four jobs, all `success`:

| job | steps | runner | labels |
|---|---|---|---|
| `129152922771` Format and static checks | **15** | `1000010597` | `ubuntu-latest` |
| `129152922172` Benchmark suite against live oracles | **15** | `1000010595` | `ubuntu-latest` |
| `129152922596` Configure, build, C++ tests, Python tests | 14 | `1000010596` | `ubuntu-latest` |
| `129152922761` macOS native C++ and Python parity | 14 | `1000010598` | `macos-15` |

No job is cancelled and none has 0 steps. The watch returned 0 on its first attempt; the run and
jobs above were read again from the API before this entry was written.

**What the four logs printed.** Lint: `236 files already formatted` — the formatter corpus moved
from 234 to 236 and the runner agrees with the local census, `declared_plants 195`,
`artifact_revision` `gap 0` with `object_check "skipped: a shallow clone cannot tell an earlier
revision from an absent one"`, `lanes_documented_vs_executed gap 0`, `Evidence is intact.`.
Build-and-test: `100% tests passed out of 204`, `490 passed, 5 skipped in 236.11s`,
`7/7 checks passed`. macOS: `98 passed in 3.37s`. Benchmark: `suite: 19/19 executed and passed, 0
aggregated from disk, 0 failed, 0 skipped, 431.1s total`, and its `Artifact revision at the run tip`
step printed `matches_tip true`.

**Two pushes, as recorded.** The first carried `2a902eb` (Phase 0) and `1804c86` (the rail set and
the readings); each commit SHA and both new blobs' SHAs were checked against the local object before
the ref moved. The second carries this entry only. The terminal commit's own CI is read after that
push and reported in the session handoff, not written into this file.

**What V6-01 closed, and what it left.** G1 (a written V6 prompt) and G2 (the sweep's vantage made
permanent) are closed by `V6_PROMPT.md` and the readings above. G3 (the artifact's pin), G4 (the
two `SKIP` keys re-read at a V6 tip), G5 (a second vantage for development-only counts) and G6 (the
re-freeze rule in practice) stay open in §5 of the prompt. No full census and no local `pytest -q`
is claimed here: the unit changes no code, so the last captured census remains `195/195` at
`ea8beb4`, and the next one belongs to the final V6 tip.

---

### 2026-11-10, V6-02 Phase 0 — the last unit, measured at `321e8b3`

**Why this phase exists.** V6-01 delivered the written rails and made the sweep's vantage permanent.
`V6_PROMPT.md` §0 ends the series only when G1–G6 are each fixed, rejected with evidence or named as
deliberately not done, when the full census is captured at the final V6 tip on a clean tree, and when
the Phase 5 report and archival confirmation are committed and pushed. This is that unit: G3–G6 and
the eight `V3_PROMPT.md` §12 deliverables, taken together as the remaining series.

**Approval, verbatim.** `继续` (2026-11-10), then the selection `整个剩余系列（推荐）` in the same
turn. Per `V6_PROMPT.md` §6 this is the maintainer's case-by-case approval for this scope unit,
recorded here before any outward action. Its scope is G3, G4, G5, G6, the final census, the Phase 5
report, the archival confirmation and the two named pushes. It does **not** authorise a new finding,
a new plant, a new ceiling key, a new CI step, an edit to `V6_PROMPT.md` or any earlier prompt, a
release, a regeneration of the evidence chain, or a third push. The V6-01 approval is spent and is
not reused.

**Revision and vantage.** `HEAD` = `origin/main` =
`321e8b337bfc19f7ee7111f4153ce55d25667d5c`; `git status --porcelain` prints 0 lines. Vantage: the
development checkout, `.venv` Python 3.12, macOS, the same WorkBuddy interpreter shim the earlier
series recorded. Platform `/compare/bb91462...321e8b3` returns `ahead_by 3`, `behind_by 0`, with
`2a902eb`, `1804c86` and `321e8b3` all ancestors of the remote tip. Git smart-HTTP remains blocked,
so both pushes use the Git Data API with `force: false` and per-object SHA verification.

**The three premises, re-measured at this tip.**

1. **The published chain is frozen.** `refs/tags/v1.9.0` is tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
   is `v1.9.0`, published `2026-10-26T09:35:44Z`, with `CITATION.cff` 2,978, `manifest.json`
   55,780, `quantrisk-suite-results.zip` 145,672 and `technical_report.pdf` 1,005,786 bytes, all
   created `09:35:41Z` and updated `09:35:42Z`–`09:35:43Z`. `tools.verify_evidence_manifest`
   prints `Evidence is intact.` with 95 entries and `0 on disk but not in the manifest`. Every field
   matches the V6 Phase 0 row. No regeneration occurred.
2. **The committed suite artifact's revision is checkable but undecided.**
   `benchmarks/suite/results/suite_run.json` names `git_commit 17df062040b8`,
   `binary_git_commit af7595749188`, `working_tree_dirty true` and 21 `uncommitted_paths`;
   `--reading artifact_revision` prints `gap 0`, `matches_tip false`,
   `object_check "the revision names a commit in this clone"`, `repository_is_shallow false`,
   `tip_being_verified 321e8b337bfc`. The claim is checkable and the decision is still absent.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** `--check-ceilings`
   prints **15** keys, 13 `ok`, 2 `SKIP`. `plants_not_rejected_by_their_guard` prints
   `precondition absent` and its `corpus` says the collector measures only the declaration because
   the sweep's gitignored scratch never reaches the runner. `installed_user_identity_mismatch`
   prints `precondition absent` and its `corpus` says the clean-venv probe installs a second
   environment and so cannot run on the runner. Both printed reasons still agree with their `corpus`
   and `can_fail_because` fields in `tools/refactor_ceilings.json`.

**The archive re-counted at `321e8b3`.**

| quantity | command that produced the reading | value |
|---|---|---|
| registry tasks / suite members | `--reading registry_parity`; `with_extras_census` | 19 / 19; `gap 0`, `revision 17df062040b8` |
| plants | `runner --list` | **195** (development-only census last captured `195/195` at `ea8beb4`) |
| ceiling keys | `--check-ceilings` | **15** — 13 `ok`, 2 `SKIP` |
| manifest | `tools.verify_evidence_manifest` | `Evidence is intact.` (95 entries) |
| formatter corpus | `--reading formatter_census` | **236 / 236**, both differences empty |
| pytest nodes | `--collect-only`; `measure_offline_collection` | **560**; offline **491**, `collection_errors 0` |
| named CI steps | the workflow's `- name:` lines | **34** |
| living documents / lane contract | `docs_rederivation`; `lanes_documented_vs_executed` | 5 documents, `gap 0`; `gap 0` |
| artifact revision / runtime reachability | two readings | `gap 0`; `reached_by_neither` empty |
| static gates | `ruff check .`; `ruff format --check .`; `mypy python/quantrisk tools` | `All checks passed!`; `236 files already formatted`; `Success: no issues found in 74 source files` |

**What this unit takes, and what it excludes.** It takes G3 (a written freeze boundary for the
committed artifact, with `artifact_revision` still at `gap 0`), G4 (both `SKIP` keys retained or
retired with this tip's reading), G5 (a named vantage for every development-only count, including the
printed `195/195` line), G6 (manifest and published assets re-read in Phase 0 and again in Phase 5),
and the Phase 5 report. It excludes new code, guards, plants, keys, CI steps and lanes; it excludes
editing any prompt; and it excludes regenerating `suite_run.json`, `evidence/manifest.json` or a
release asset. `V6_PROMPT.md` §4 already supplies the written decision for G2; this unit does not
reopen it.

**Deliberately not done in Phase 0.** No source file or document was edited, no census was run, no
report section was written and no push was made. Every number above is a reading at `321e8b3`. The
full census and the final local `pytest -q` belong to the implementation tip, after the one document
edit this unit makes, on a clean tree.

**The two pushes.** The first carries the Phase 0 commit, the implementation commit and the Phase 5
report; the second carries the terminal entry only. No third is implied. Each push's CI is read from
the API after the tool reports it; the first tip's run is attributed in the terminal entry and the
second tip's run in the session handoff.

---
