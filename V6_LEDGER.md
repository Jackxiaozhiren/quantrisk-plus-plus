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

### 2026-11-10, V6-02 implementation — four written decisions and one vantage label

**What changed.** Two tracked files, both prose. No source file, guard, plant, ceiling key, CI step,
living-document count or committed artifact changed.

| file | change | why |
|---|---|---|
| `docs/interview_defense.md` | the `195/195` command comment now reads `# 195/195 planted defects rejected (development-side vantage; the sweep has no CI lane)` | G5: the only living document that prints the census verdict labels its vantage on the same line, as `V6_PROMPT.md` §4 requires |
| `V6_LEDGER.md` | this entry | G3–G6 are written decisions, so the ledger is the deliverable |

The edit preserves three exact strings the tree depends on: the plant anchor
`# 195/195 planted defects rejected`, the `docs_rederivation` pattern
`(\d+)/(\d+)\s+planted\s+defects\s+rejected`, and `test_mutation_suite.py`'s
`#\s*(\d+)/(\d+) planted defects` guard. The targeted sweep that proves the anchor still reddens is
run after this commit, on a clean tree, and reported in the Phase 5 entry.

**G3 — the committed artifact is pinned, in writing.** Decision:
`benchmarks/suite/results/suite_run.json` is **pinned to the historical run at `17df062040b8`**
(binary stamp `af7595749188`) and is not regenerated by V6. Its `working_tree_dirty: true` and 21
`uncommitted_paths` describe that run, not this checkout. `N10` admits one suite re-run per series and
V6 triggers none. The benchmark job's fresh artifact is a CI upload from the run tip — run
`42616940263` printed `matches_tip true` at `321e8b337bfc` — and is not written back to the committed
file, so the lint vantage's `matches_tip false` is the expected consequence of the pin rather than
drift. The freeze boundary is therefore: **the committed artifact is frozen at `17df062040b8`; only
the CI upload moves with the tip.** Any future unit that changes the committed artifact must declare
the re-run in its Phase 0, report it in Phase 5 and carry its own approval. The check is met by this
entry plus a re-measured reading: at `1e649f55b144c485df023dddf9b0bcf9e4c017f8`,
`--reading artifact_revision` prints `gap 0`, `matches_tip false`,
`object_check "the revision names a commit in this clone"`, 21 attributed paths, and
`problems []`.

**G4 — both `SKIP` keys are retained with this tip's reading.** Re-read at `321e8b3` and again
after the edit; `--check-ceilings` prints 15 keys, 13 `ok`, 2 `SKIP`.

| key | `corpus` agrees with | printed reason at this tip | decision |
|---|---|---|---|
| `plants_not_rejected_by_their_guard` | `plant_liveness.declared_plants 195`; the collector measures only the declaration, not the sweep verdict | `precondition absent` — the sweep's gitignored scratch never reaches the runner | **retain**, permanently, per `V6_PROMPT.md` §4 |
| `installed_user_identity_mismatch` | the clean-venv wheel probe's identity, `run --list`, `validate`, one study and one refusal | `precondition absent` — the probe installs a second environment, which the runner cannot do | **retain**, with the V5 F5 proof labelled development-only in G5's table |

Neither key is retired. Retiring either would promote a development-only reading into a CI gate,
which is the failure G5 exists to prevent; both `corpus` fields still describe the precondition the
collector actually checks, and both `can_fail_because` fields still name a live non-zero baseline.

**G5 — every development-only count names its vantage.** The Phase 5 per-lane table carries a
`vantage` column for each row. The counts that could be miscited are named here:

| count | vantage that produced it | second vantage | status |
|---|---|---|---|
| **195** declared plants | `runner --list`, development checkout | CI lint `plant_liveness` prints 195 | two vantages; a declaration, not a verdict |
| **195/195 rejected** | the full sweep, development checkout only | none | **labelled development-side** wherever printed; never cited as a CI gate |
| **236 / 236** formatter corpus | `formatter_census`, development checkout | CI lint `236 files already formatted` | two vantages |
| **560 / 491** pytest nodes | `--collect-only` / offline collector, development checkout | CI prints `490 passed, 5 skipped` | different environment and different quantity; **not promoted** to the same count |
| **19 / 19** suite members | committed `suite_run.json`, lint vantage | benchmark job's fresh artifact | two vantages of the same registry comparison |
| **15** ceiling keys | `--check-ceilings`, development checkout | CI lint `refactor ceilings` step | two vantages |
| installed-surface proof | clean venv outside the checkout (V5 F5) | none | **development-only**, named as such |
| tag / release / four assets | GitHub REST API | none needed | platform reading, not a repository count |
| **34** named CI steps | the workflow file | the four jobs' step counts | two enumerations |

The only living document that prints `195/195` is `docs/interview_defense.md`, and the label is on
the same line as the number. Ledger entries from earlier series are historical readings and are not
rewritten (Facts Protocol §2.4); every new V6 entry that cites the census names its vantage.

**G6 — no silent re-freeze.** Phase 0 re-read the 95-entry manifest and the platform's tag, release
and four asset sizes/timestamps; Phase 5 §8 re-reads them again. This unit regenerated none of them
and replaced no release asset. `suite_run.json` still names `17df062040b8`,
`tools.verify_evidence_manifest` still prints `Evidence is intact.`, and no freeze was re-run.

**The counts after the change, and their deltas.**

| quantity | Phase 0 | after the edit | delta |
|---|---|---|---|
| formatter corpus | 236 / 236 | **236 / 236**, both differences empty | 0 |
| plants / ceiling keys | 195 / 15 (13 `ok`, 2 `SKIP`) | **195 / 15 (13 / 2)** | 0 |
| manifest / pytest nodes | 95 intact / 560, 491 | **95 intact / 560, 491** | 0 |
| named CI steps / suite members | 34 / 19 | **34 / 19** | 0 |
| docs / lanes / with-extras / revision | four `gap 0` | **four `gap 0`** | 0 |

`--reading docs_rederivation` prints `documents 5`, `gap 0`, `mismatches []`,
`source_disagreements []` and `derived {manifest_artifacts 95, plants 195, registry_tasks 19,
suite_members 19}`; `ruff format --check .` prints `236 files already formatted`; `ruff check .`
prints `All checks passed!`; the prose guard
`test_a_command_line_that_counts_plants_counts_the_declared_ones` passes on the edited line.

**What this unit deliberately did not do.** It added no guard, plant, ceiling key or CI step; it did
not edit any prompt; it did not regenerate an artifact or manifest; it cut no release; and it did not
run the full census, the targeted sweep or the final local `pytest -q` here — those require a clean
tree after this commit and are attributed in the Phase 5 report.

**The first push.** Phase 0, this implementation and the Phase 5 report ship in the first of the two
pushes named in the Phase 0 entry. No outcome is written here for a push that has not happened.

---

### 2026-11-10, V6 Phase 5 — the report, the liveness table, and the archival confirmation

**How this was assembled.** From this ledger's V6 Phase 0, V6-01 and V6-02 entries plus fresh
readings at `9486c7a39e380f0f2411ab7ce2bfb33f4c7ee6e8` on a clean tree. Where a number appears in
an earlier entry it was re-measured rather than copied; the census line is quoted from
`/tmp/v6_census.log` line 998, not retyped. Every platform figure is a fresh API reading.

#### 1. Evidence ledger

| id | verdict | probe | closing commit |
|---|---|---|---|
| G1 | **fixed** | `V6_PROMPT.md` exists with three premises, the Facts Protocol, the lane inventory, G1–G6 with `check:` predicates, the one-unit-per-approval rule, DoD and the size ratchet; its §6 was followed and the approval recorded verbatim in Phase 0 | `2a902eb` (Phase 0), `1804c86` (delivered) |
| G2 | **fixed** | `V6_PROMPT.md` §4 states the development-only decision permanently, names the mechanical reason and the sole condition for revisiting it; no V6 entry lists it as open; the key's declaration and reason still agree | `1804c86` |
| G3 | **fixed** | the implementation entry pins `suite_run.json` to `17df062040b8` in writing and states the freeze boundary; `--reading artifact_revision` at `9486c7a` prints `gap 0`, `matches_tip false`, `problems []`, 21 attributed paths | `9486c7a` |
| G4 | **fixed** | both `SKIP` keys re-read at `321e8b3` and again after the edit: 15 keys, 13 `ok`, 2 `SKIP`; each `corpus` still agrees with its printed `precondition absent` reason; both retained, neither retired | `1e649f5`, `9486c7a` |
| G5 | **fixed** | the implementation entry names a vantage for every development-only count; the sole living document printing `195/195` labels it on the same line; §7 below carries a `vantage` column; no dev-only count is promoted to a CI gate | `9486c7a` |
| G6 | **fixed** | the 95-entry manifest and the platform's tag/release/four assets were re-read in Phase 0 and again in §8 below; this unit regenerated none and replaced no asset | `1e649f5`, this entry |

#### 2. Liveness table, re-evaluated at `9486c7a`

| # | law | verdict | the reading that decided it |
|---|---|---|---|
| N1 | requirement truth | **ACTIVE** | `registry_parity`: `filesystem_units 19`, `registry_sources 19`, `mismatch []` |
| N2 | advertised surface honesty | **ACTIVE** | the V5 F5 clean-venv wheel proof (19 tasks, 7 validations, one study, one refusal, zero residue); labelled development-only in G5's table, not promoted |
| N3 | lane contract | **ACTIVE** | `lanes_documented_vs_executed gap 0`, both differences empty; **34** named CI steps; five `tools.inventory_orphan_code` steps across two jobs |
| N4 | no silence by count | **ACTIVE** | `with_extras_census` prints `gap 0`, `members 19`, `passed 19`, empty `missing_*` / `duplicate_keys` / `not_passed` / `self_inconsistent` lists; `docs_rederivation` prints `mismatches []` and `source_disagreements []` |
| N5 | declarations are checkable | **ACTIVE** | 15 keys, 13 `ok`, 2 `SKIP` with named preconditions and `may_be_unmeasured: true`; both `SKIP` reasons re-read at this tip |
| N6 | runtime reachability | **ACTIVE** | `runtime_reachability` prints `reached_by_neither []` |
| N7 | one finding, one commit | **ACTIVE** | seven V6 commits map to G1–G2, the terminal entry, Phase 0, G3–G6, the report and the terminal entry; the mapping is §8 below |
| N8 | no gate weakened | **ACTIVE** | the V6 range adds no `skip`/`xfail`, no exemption, no tolerance and deletes no test; the only source-adjacent change is a comment suffix on one printed line |
| N9 | plant liveness | **ACTIVE** | `195/195 planted defects were rejected by their guard.` at `9486c7a`, clean tree, 195 `ok   caught` rows, zero other verdict rows |
| N10 | one re-run | **ACTIVE, not triggered** | no evidence artifact regenerated in V6: `suite_run.json` still names `17df062040b8`, the manifest still holds 95 intact entries, and no freeze was re-run |
| N11 | facts precedence | **ACTIVE** | `docs_rederivation gap 0`, 5 documents, `derived {95, 195, 19, 19}`; the one edited printed claim was re-derived in the same commit |
| N12 | baseline purity and per-lane provenance | **ACTIVE** | §7 names a revision, an environment **and** a vantage for every lane; the baseline was measured at `321e8b3`, which has a CI run of its own (`42616940263`) |

#### 3. The ceilings file's final state

`tools/refactor_ceilings.json` carries **15** keys, unchanged by V6. Thirteen are `ok` at `0`:
`bootstrap_sites_outside_package`, `by_path_load_sites`, `commands_not_module_path`,
`commands_unrunnable_from_the_root`, `tracked_python_files_in_no_static_check_bucket`,
`tracked_files_outside_the_formatter_corpus`, `registry_parity_mismatch`,
`runtime_reachability_gap`, `external_dependencies_added`,
`lanes_documented_vs_executed_gap`, `with_extras_census_gap`, `docs_rederivation_gap` and
`artifact_revision_gap`. Two are `SKIP` with `may_be_unmeasured: true`:
`plants_not_rejected_by_their_guard` and `installed_user_identity_mismatch`.

**Review notes.** V6 added no key and loosened none. G2 made the first `SKIP` permanent in writing;
G4 re-read both at a V6 tip and retained them with their printed reasons. The fifteenth key's
`can_fail_because` still names the shallow-clone repair from V5-02, and the lint vantage's
`object_check "skipped: a shallow clone cannot tell an earlier revision from an absent one"` is the
same repair working on a different vantage. A future series that wants a runner-side verdict must
redesign the harness first; it may not retire either key to make a local reading look like a gate.

#### 4. The deliberately-not-done list

1. **The sweep still has no CI lane.** `plants_not_rejected_by_their_guard` stays `SKIP` permanently;
   `195/195` is a development-side reading. Converting it requires the harness redesign that
   `V6_PROMPT.md` §4 names as the sole condition.
2. **The installed-surface proof is still not a CI lane.** The clean-venv proof remains local; the
   runner cannot install a second environment without changing the job's shape.
3. **The committed `suite_run.json` was not regenerated.** G3 pinned the artifact to
   `17df062040b8` instead. A declared re-run is a future unit with its own approval, not a silent
   refresh that would move `evidence/manifest.json` and the release asset set.
4. **No second vantage was built for `195/195`.** G5 labelled the count rather than promoting it;
   the 195 declared plants have two vantages, the rejection verdict has one.
5. **`V6_PROMPT.md` and every earlier prompt are unedited.** §6 makes a prompt edit its own scope
   unit; the series-wide approval excluded it.
6. **No new guard, plant, ceiling key, CI step or lane.** G3–G6 are written decisions about
   existing readings; adding machinery to police a sentence would be the "counting a declaration"
   failure V5 §4 warns about.
7. **The report PDF was not rebuilt.** `tools.build_report` stays dev-only; the byte-bound PDF and
   `paper/technical_report.tex` were read, not re-rendered.
8. **No V6 release.** The published asset set is unchanged by design; G6's check is that it did not
   move.
9. **The one local pytest failure was not silenced.** `test_a_restored_plant_cannot_be_read_back_from_a_stale_bytecode_cache`
   fails only under this sandbox's bytecode-cache plant; it is named in §7 as a failure with its
   environment, and CI reads `490 passed, 5 skipped`. No marker was added.

#### 5. Premises audit

1. **The published chain is frozen and V6 must not move it silently.** *Final reading at
   `9486c7a`:* tag object `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
   published `2026-10-26T09:35:44Z` with four assets sized 2,978 / 55,780 / 145,672 / 1,005,786
   bytes, created `09:35:41Z`, updated `09:35:42Z`–`09:35:43Z`; manifest 95 entries and
   `Evidence is intact.`. **Closed**; every field matches Phase 0's row.
2. **The committed suite artifact's revision is checkable but undecided.** *Final reading:*
   `--reading artifact_revision` at `9486c7a` prints `artifact_revision 17df062040b8`, `gap 0`,
   `matches_tip false`, `object_check "the revision names a commit in this clone"`, 21 attributed
   paths. The decision is now written in the implementation entry: the artifact is pinned to that
   historical run. **Closed**; the residue is that the pin is prose, not a new guard (item 3 above).
3. **The two `SKIP` keys hold only while their preconditions are re-read.** *Final reading:* 15
   keys, 13 `ok`, 2 `SKIP`; both printed `precondition absent` with their `corpus` describing the
   missing runner precondition; both retained. **Closed**; the residue is that both verdicts remain
   development-only, which G5 labelled rather than hid.

#### 6. Series handoff — what V7 must contain

Derived from this run's evidence, not from the prompt's prose:

1. **The pin is a written decision, not a guard.** If V7 wants a checkable artifact pin, it needs a
   reading with a plant or forged-input proof and its own approval; it must not "fix" the lint
   vantage's `matches_tip false` by regenerating the committed artifact outside a declared re-run.
2. **The sweep's vantage is closed.** `V6_PROMPT.md` §4 permits reopening only through a harness
   redesign whose Phase 0 says so and which carries its own approval. A V7 that lists it as an open
   question has not read §4.
3. **The two `SKIP` keys have no runner vantage.** They were re-read and retained with reasons;
   a second vantage for development-only counts remains an idea, not a gate.
4. **The printed `195/195` line is labelled.** Any new document that quotes the census verdict must
   label it development-side on the same line, and `docs_rederivation` must stay at `gap 0`.
5. **Size ratchet.** `V6_PROMPT.md` is 146 lines with 88 lines of prose; growth is allowed only in
   §5's finding table and §3's lane inventory, and only after showing which V6 rule was never
   executed.
6. **No silent re-freeze remains standing.** The 95-entry manifest and the `v1.9.0` assets are the
   published chain; any regeneration must appear in both Phase 0 and Phase 5.
7. **The local pytest failure is environmental.** Do not weaken a gate to turn
   `1 failed, 559 passed` into green; attribute it to the sandbox and read CI instead.

#### 7. Per-lane verification table

| lane | revision | environment | vantage | verdict |
|---|---|---|---|---|
| `ruff check .` | `9486c7a` | macOS, `.venv` Python 3.12, development checkout | development | `All checks passed!` |
| `ruff format --check .` | `9486c7a` | same | development + CI lint | `236 files already formatted` |
| `mypy python/quantrisk tools` | `9486c7a` | same | development | `Success: no issues found in 74 source files` |
| `pytest -q` (full) | `9486c7a` | same, private `--basetemp=/tmp/qr-v6-final` | development | **1 failed, 559 passed in 120.77s**; the failure is the sandbox-only bytecode-cache plant |
| `pytest --collect-only` / `measure_offline_collection` | `9486c7a` | same | development | 560 / 491, `collection_errors 0` |
| mutation sweep, targeted | `9486c7a` | same, clean tree after the implementation commit | development-only | `1/1 planted defects were rejected by their guard.`, tree 0 dirty |
| mutation sweep, full census | `9486c7a` | same, bulk-delete threshold raised locally | **development-only, labelled** | **195/195**, 195 `ok   caught` rows, 0 other verdict rows, tree 0 dirty, exit 0 |
| `--check-ceilings` | `9486c7a` | same | development + CI lint | 15 keys, 13 `ok`, 2 `SKIP` |
| `--reading docs_rederivation` | `9486c7a` | same | development + CI lint | `gap 0`, 5 documents, `derived {95, 195, 19, 19}` |
| `--reading lanes_documented_vs_executed` | `9486c7a` | same | development + CI lint | `gap 0` |
| `--reading with_extras_census` | `9486c7a` | same | development + CI lint + benchmark-job fresh artifact | `gap 0`, 19/19, `revision 17df062040b8` |
| `--reading artifact_revision` | `9486c7a` | same | development (deep clone) + lint (shallow clone) + benchmark (fresh artifact) | `gap 0`, `matches_tip false` in the committed vantage; `matches_tip true` on the CI upload |
| `--reading formatter_census` / `registry_parity` / `runtime_reachability` | `9486c7a` | same | development + CI lint | 236/236, 19/19, `reached_by_neither []` |
| `tools.verify_evidence_manifest` | `9486c7a` | same | development + CI lint | `Evidence is intact.` |
| `tools.verify_installed_surface` | `3c6092f` | `/tmp/qr-v5-venv`, wheel from that tree, neutral cwd | **development-only, labelled** | identity, 19 tasks, 7 validations, one study, one refusal, 0 residue |
| CI `lint` / `build-and-test` / `macOS parity` / `benchmark-suite` | `1804c86` (run `42615110830`) | `ubuntu-latest` `1000010595`–`1000010597`, `macos-15` `1000010598` | runner | `success`, 15 / 14 / 14 / 15 steps |
| CI four jobs | `321e8b3` (run `42616940263`) | `ubuntu-latest` `1000010606`–`1000010608`, `macos-15` `1000010609` | runner | `success`, 15 / 14 / 14 / 15 steps; `490 passed, 5 skipped`, `19/19`, `matches_tip true` |
| CI four jobs | report tip (first V6-02 push) | runners named in the terminal entry | runner | **not yet read**; no outcome is written for a push that has not happened |
| CI four jobs | terminal tip (second V6-02 push) | runners named in the session handoff | runner | **not yet read** |

No lane is marked green on a mixed vantage. The census's log contains the strings
`tree-did-not-recover` and `ESCAPED` only inside two plants' claim text at lines 991–992; neither is
a verdict row. The one local failure is named as a failure with its cause and environment, not
averaged into the green rows.

#### 8. Archival confirmation

- **Tree and tip.** `git status --porcelain` prints 0 lines; `HEAD` =
  `9486c7a39e380f0f2411ab7ce2bfb33f4c7ee6e8` before this report's commit, with `origin/main` at
  `321e8b3`. The Phase 0, implementation and report commits are pushed in the first V6-02 push; the
  terminal entry follows in the second, and the session handoff records the final tip.
- **Every V6 commit an ancestor of the remote.** Platform `/compare/bb91462...321e8b3` returned
  `ahead_by 3`, `behind_by 0`, with `2a902eb`, `1804c86`, `321e8b3` all ancestors of the then-tip.
  `1e649f5` (V6-02 Phase 0) and `9486c7a` (implementation) are local ancestors of this report's
  commit and ship in the first V6-02 push; each object SHA is checked against the local object
  before the ref moves. The terminal commit is verified after its own push.
- **CI for every commit.** Two V6-01 runs cover its range: `42615110830` (`1804c86`, `success`,
  `run_attempt 1`, 15/15/14/14) and `42616940263` (`321e8b3`, `success`, `run_attempt 1`,
  15/15/14/14). `2a902eb` was carried in the same first push as `1804c86` and is attributed to the
  run whose tree contains it. The two V6-02 push tips are attributed in the terminal entry and the
  session handoff after the API reports them; no run is named green before it is read. No V6 run is
  cancelled and no job has 0 steps.
- **Registers and documents re-counted.** `registry_parity` 19/19; `with_extras_census` 19/19,
  `gap 0`; `plant_liveness` 195 and the census's 195/195; manifest 95 intact;
  `docs_rederivation` 5 documents / `gap 0`; formatter 236/236; nodes 560/491; CI steps 34;
  ceiling keys 15. `artifact_revision gap 0`, `lanes_documented_vs_executed gap 0`,
  `runtime_reachability` `reached_by_neither []`.
- **Tags, releases and assets re-read from the platform.** Tag object
  `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
  `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
  (`v1.9.0`) published `2026-10-26T09:35:44Z` with four assets, sizes 2,978 / 55,780 / 145,672 /
  1,005,786 bytes, created `09:35:41Z`, updated `09:35:42Z`–`09:35:43Z`. All match the Phase 0
  rows; no asset was replaced.
- **No stray instrument tracked or left on disk.** `git ls-files -- tools/derive_requires.py
  build/run_sweep.py build/api_push.py` prints nothing; `git check-ignore` confirms
  `build/api_push.py`, `build/run_sweep.py` and `.workbuddy/` are ignored; the census left 0 dirty
  paths and no `_mutation_probe` directory; the only external log is `/tmp/v6_census.log`, outside
  the repository; no background process remains running.

#### 9. What V6 changed, and what it did not

It added `V6_PROMPT.md`, `V6_LEDGER.md` and one suffix on a printed command comment. It changed no
source file, guard, plant, ceiling key, CI step, manifest entry, committed suite artifact or release
asset. It did not touch `cpp/`, `bindings/`, `CMakeLists.txt`, `PROJECT_SPEC.md`,
`REFACTOR_PROMPT.md`, `V3_PROMPT.md`, `V5_PROMPT.md`, `evidence/manifest.json` or `paper/`, and it
did not move `v1.9.0`.

**The first push.** This report, the Phase 0 commit and the implementation commit are pushed together
in the first of the two pushes authorised in the V6-02 Phase 0 entry. Its CI is read once the tool
reports it and recorded in the terminal entry; no outcome is stated here for a push that has not
happened.

---
