# V10_LEDGER.md — cross-session state for the V10 series

Each entry records what was run, what it printed and what was decided, in that order. A number
quoted from an earlier series is named as a historical reading and re-measured before it is used as
a V10 fact. `V10_PROMPT.md` is the rail set; this file is the state.

---

### 2026-11-12, V10 Phase 0 — the single unit that repairs `V7_PROMPT.md` §8

**Why this phase exists.** `V9_LEDGER.md` Phase 5 §4 item 1 names A as deliberately not done: V7's
§8 sets a soft cap at V6's 88 prose lines, an escape clause, and a growth clause ("only in §5 and
§3") that the file it governs does not meet. `V7_LEDGER.md` records H6 as **PARTIAL** for exactly
that reason, and V8 §4 item 2 and V9 §1 refused the repair because `V7_PROMPT.md` §6 makes editing
that file its own scope unit needing its own verbatim approval. The maintainer has now given that
approval, so the rule can be repaired without rewriting the finding.

**Approval, verbatim.** `启动 V10，只做 A 项` (2026-11-12). This is a **single-unit** approval,
recorded here before any outward action. It covers A1, this Phase 0 entry, the implementation, the
Phase 5 report, the terminal entry, the two named pushes and their CI attribution. The V9 approval
(`启动 V9，只做 D 项`) is spent and is not reused.

**Not authorised:** items B (reopening the sweep vantage) and C (a declarative re-run of the evidence
chain); editing `V7_PROMPT.md` outside §8; editing any other prompt or ledger; a harness redesign; a
new census; a tag movement or release asset replacement; a new CI lane, plant, guard or ceiling key;
and a third push.

**Revision and vantage.** `HEAD` = `origin/main` = platform `main` =
`ca94a2c153d677e1d6b2f174e105c73efc4d57b2` (before this entry's commit); `git status --porcelain`
prints 0 lines. Vantage: the development checkout, `.venv` Python 3.12, macOS, the same WorkBuddy
interpreter shim earlier series recorded. `.git/info/exclude` still ignores `.workbuddy/`, so
agent-local memory does not enter the formatter census. Git smart-HTTP remains blocked, so both
pushes use the Git Data API with `force: false` and per-object SHA verification.

**The three premises, re-measured at this tip.**

1. **The published chain is frozen.** `refs/tags/v1.9.0` is tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
   is `v1.9.0`, published `2026-10-26T09:35:44Z`, with `CITATION.cff` 2,978, `manifest.json`
   55,780, `quantrisk-suite-results.zip` 145,672 and `technical_report.pdf` 1,005,786 bytes, all
   created `09:35:41Z` and updated `09:35:42Z`–`09:35:43Z`. `tools.verify_evidence_manifest` prints
   `Evidence is intact.` with 95 entries and `0 on disk but not in the manifest`. No regeneration
   occurred.
2. **The pin is a guard, not a sentence.** `--reading artifact_revision` prints
   `artifact_revision 17df062040b8`, `pinned_revision 17df062040b8`, `pin_holds true`, `gap 0`,
   `matches_tip false`. V10 does not weaken it and does not re-run the V7 forged cases, because no
   code moves.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** `--check-ceilings`
   prints **15** keys, 13 `ok`, 2 `SKIP`. `plants_not_rejected_by_their_guard` prints
   `precondition absent` and its `corpus` says the collector measures only the declaration because
   the sweep's gitignored scratch never reaches the runner. `installed_user_identity_mismatch`
   prints `precondition absent` and its `corpus` says the clean-venv probe installs a second
   environment the runner cannot have. Both reasons still agree with their `corpus` and
   `can_fail_because` fields. V10 does not give either a runner-side verdict.

**The archive re-counted at `ca94a2c`.**

| quantity | command that produced the reading | value |
|---|---|---|
| registry tasks / suite members | `--reading registry_parity`; `with_extras_census` | 19 / 19, `mismatch []`; `gap 0`, 19 / 19 |
| plants | `runner --list` | **195** (V8's census `195/195` at `5ec3fab` — development-side vantage; the sweep has no CI lane) |
| ceiling keys | `--check-ceilings` | **15** — 13 `ok`, 2 `SKIP`, 0 `FAIL` |
| manifest | `tools.verify_evidence_manifest` | `Evidence is intact.` (95 entries) |
| formatter corpus | `--reading formatter_census` | **242 / 242**, both differences empty |
| pytest nodes | `--collect-only` | **560**; offline **491**, `collection_errors 0` |
| named CI steps | the workflow's `- name:` lines | **34** |
| living documents / lane contract | `docs_rederivation`; `lanes_documented_vs_executed` | 5 documents, `gap 0`, `derived {95, 195, 19, 19}`; `gap 0` |
| artifact revision / runtime reachability | two readings | `gap 0`, `pin_holds true`, `matches_tip false`; `reached_by_neither []` |
| `V7_PROMPT.md` before the repair | heading-span measure over §1–§3, §6–§8 | **154 total / 98 prose** — the same figure `V7_LEDGER.md` H6 reports |
| static gates | `ruff check .`; `ruff format --check .`; `mypy python/quantrisk tools` | `All checks passed!`; `242 files already formatted`; `Success: no issues found in 74 source files` |

**What this unit takes, and what it excludes.** It takes one finding, A1: repair `V7_PROMPT.md` §8
so that it states one hard bound (431) and reports V6–V9's figures as references rather than gates,
while `V7_LEDGER.md`'s H6 verdict and §5's H6 row stay byte-identical. The repair must describe the
old rule and why it failed before stating the new one, so the edit cannot be mistaken for a quiet
reword. V10 excludes B, C, any edit outside §8, any new census, and any change to a source file,
policy asset, test, workflow, manifest, artifact, tag or release asset.

**Deliberately not done in Phase 0.** No file other than `V10_PROMPT.md` and this ledger was
written, no edit to `V7_PROMPT.md` was made, no census was run and no push was made. Every number
above is a reading at `ca94a2c`. The repair and its before/after measurement belong to the
implementation commit; no verdict is claimed before the tool prints it.

**The two pushes.** The first carries Phase 0, the implementation and the Phase 5 report; the second
carries the terminal entry only. No third is implied. Each push's CI is read from the API after the
tool reports it; the first tip's run is attributed in the terminal entry and the second tip's run in
the session handoff.

---

### 2026-11-12, V10 implementation — A1, the §8 repair

**What changed.** One section of `V7_PROMPT.md`, §8, and nothing else. The withdrawn text is quoted
here because the file no longer carries it:

> `V3_PROMPT.md` §0 caps its prose sections at 431 lines measured by heading span. V6's is 146 lines
> with 88 lines of prose. V7's prose sections (§1–§3, §6–§8) may not exceed that 88-line figure
> without the Phase 5 report naming which V6 rule was never executed; the hard bound remains 431.
> Growth is allowed only in §5's finding table and §3's lane inventory. V7 adds no section beyond
> V6's eight.

**What replaced it.** §8 now states 431 as this file's only hard bound, records the old soft cap and
growth clause as withdrawn gates together with the reason, and reports V6–V9's 146 / 88, 154 / 98,
161 / 107 and 164 / 112 as reference figures that a later file may exceed, printing its own
measurement beside them. The reason is stated in the file: V7 met §8's escape clause by naming
`V6_PROMPT.md` §7's never-executed rule, but its added lines sit in §6 as well as §5, so the growth
clause was not met — and a bound whose author must argue an escape clause to stay inside it is not a
bound.

**Why this is a repair, not a rewrite of history.** `V7_LEDGER.md` still records H6 as **PARTIAL**
with its 154 / 98 measurement, and §5's H6 row still prints the V7-era check on line 97, unamended.
Those are readings at V7's tip; what V10 changes is the rule the file states for itself, which was
never a reading. `V8_LEDGER.md` and `V9_LEDGER.md` both say the file was untouched — true at their
tips, and neither ledger is edited. `git diff --stat ca94a2c..HEAD -- V7_LEDGER.md V3_PROMPT.md
V8_PROMPT.md V9_PROMPT.md V8_LEDGER.md V9_LEDGER.md` prints 0 lines.

**Before and after, measured by the same heading-span rule.**

| reading | before (`ca94a2c`) | after | delta |
|---|---|---|---|
| `V7_PROMPT.md` total lines | 154 | **165** | +11 |
| `V7_PROMPT.md` prose lines (§1–§3, §6–§8) | 98 | **109** | +11 |
| withdrawn clauses present (`may not exceed that 88-line`, `Growth is allowed only`) | 2 | **0** | −2 |
| `\| H6 \|` row | line 97 | line 97 | unchanged |
| `V7_LEDGER.md` bytes | — | unchanged | 0 |
| `V7_PROMPT.md` section count | 8 | 8 | 0 |

**Gates and counts after the change, at this commit's tree.** `ruff check .` prints
`All checks passed!`; `ruff format --check .` prints `244 files already formatted`;
`mypy python/quantrisk tools` prints `Success: no issues found in 74 source files`;
`--check-ceilings` prints **15** keys, 13 `ok`, 2 `SKIP`, 0 `FAIL`; `--reading formatter_census`
prints **244 / 244** with both differences empty; `--reading docs_rederivation` prints `gap 0`,
5 documents, `derived {95, 195, 19, 19}`; `tools.verify_evidence_manifest` prints `Evidence is
intact.`; `runner --list` prints **195**; the workflow still has **34** named steps;
`--collect-only` prints **560** collected. No count moved except the formatter corpus, which V10's
two new Markdown files took from 242 to 244.

**What was decided.** A1 is fixed: the file's sizing rule is now one hard bound plus reported
references, and the historical partial verdict is preserved in the ledger and in §5. V10 adds no
guard, plant, ceiling key, CI step, lane, living document or artifact, and no reading was rewritten.
The only changed paths in this commit are `V7_PROMPT.md` and this ledger.

---

### 2026-11-12, V10 Phase 5 — the report, the liveness table and the archival confirmation

**How this was assembled.** From the two entries above plus fresh readings at
`9118c5c4535a15c757226da3628af2d57ce989f2` on a clean tree. The implementation commit is `9118c5c`;
the series adds two tracked paths (`V10_PROMPT.md`, `V10_LEDGER.md`) and edits one section of a third
(`V7_PROMPT.md` §8). The only count that moved is the formatter corpus, 242 → **244**, because the
two added paths are Markdown; both differences are still empty.

#### 1. Evidence ledger

| id | verdict | probe | closing commit |
|---|---|---|---|
| A1 | **fixed** | `V7_PROMPT.md` §8 now states 431 as the only hard bound and reports V6–V9's figures as references; the two withdrawn clauses are absent from the file, §5's H6 row and `V7_LEDGER.md`'s `partial` verdict are byte-identical to `ca94a2c`, and every gate and count is unchanged | `9118c5c` |

**The probe in detail.** The changed section was measured before and after with the same heading-span
rule V6–V9 used: 154 total / 98 prose at `ca94a2c`, **165 / 109** at `9118c5c`. A `grep` for the two
withdrawn sentences (`may not exceed that 88-line`, `Growth is allowed only`) returns nothing in the
edited file, while `| H6 |` is still line 97 and still quotes the V7-era check. `git diff --stat
ca94a2c..HEAD -- V7_LEDGER.md V3_PROMPT.md V8_PROMPT.md V9_PROMPT.md V8_LEDGER.md V9_LEDGER.md`
prints 0 lines, so the repair changed no historical ledger and no other prompt.

#### 2. Liveness table, re-evaluated at `9118c5c`

| # | law | verdict | the reading that decided it |
|---|---|---|---|
| N1 | requirement truth | **ACTIVE** | `registry_parity`: `filesystem_units 19`, `registry_sources 19`, `mismatch []` |
| N2 | advertised surface honesty | **ACTIVE, inherited** | `with_extras_census gap 0`, `members 19`, `passed 19`; the V5 F5 clean-venv proof stays development-only |
| N3 | lane contract | **ACTIVE** | `lanes_documented_vs_executed gap 0`; **34** named CI steps, unchanged by a prose repair |
| N4 | no silence by count | **ACTIVE** | `with_extras_census gap 0`; `docs_rederivation gap 0`, 5 documents, `derived {95, 195, 19, 19}` |
| N5 | declarations are checkable | **ACTIVE** | 15 keys, 13 `ok`, 2 `SKIP`, 0 `FAIL`; `pinned_revision` compared in both directions, `pin_holds true` |
| N6 | runtime reachability | **ACTIVE** | `runtime_reachability` prints `reached_by_neither []` |
| N7 | one finding, one commit | **ACTIVE** | Phase 0, `9118c5c`, this report and the terminal entry map to A1 alone; V10 has no A2 |
| N8 | no gate weakened | **ACTIVE** | the diff over `ca94a2c..9118c5c` is three Markdown paths: no `skip`/`xfail`, no tolerance, no test deleted, no `max` raised, no `may_be_unmeasured` added |
| N9 | plant liveness | **ACTIVE, inherited** | V8's census `195/195` at `5ec3fab` (development-side vantage; the sweep has no CI lane); V10 changes no plant, guard or target file, so no re-run is implied |
| N10 | one re-run | **ACTIVE, not triggered** | nothing regenerated: `suite_run.json` still names `17df062040b8`, the manifest still holds 95 intact entries |
| N11 | facts precedence | **ACTIVE** | `docs_rederivation gap 0`; the repair is a rule change recorded beside the reading it supersedes, not a rewrite of any reading |
| N12 | baseline purity and per-lane provenance | **ACTIVE** | §7 names a revision and an environment for every lane; the baseline `ca94a2c` has its own CI run `43034777310` (`completed / success`, attempt 1) |

#### 3. The ceilings file's final state

`tools/refactor_ceilings.json` carries **15** keys, untouched by V10: thirteen `ok` at `0`, two
`SKIP` with `may_be_unmeasured: true` — `plants_not_rejected_by_their_guard` and
`installed_user_identity_mismatch`.

**Review notes.** The 88-line figure was never a ceiling key; it was prose in a prompt, which is why
it could drift from the file it governed. V10 adds no key, no `max` change, no exemption and no
`may_be_unmeasured`: the repair removes an unsatisfiable sentence rather than adding a sixteenth
declaration to police prose, which is the declaration-counting failure `V5_PROMPT.md` §1 names.

#### 4. The deliberately-not-done list

1. **B — the sweep vantage is not reopened.** `V6_PROMPT.md` §4 made the development-only decision
   permanent; reopening needs a harness redesign that adds a CI lane and puts a ~38-minute census on
   a runner. V10 Phase 0 excluded it.
2. **C — the evidence chain is not re-run.** A declarative re-run would move the 95-entry manifest
   and the release asset set, and `quantrisk-suite-results.zip` cannot be replaced under K5.
3. **No census at V10's own tip.** V10 changes no plant target; a census here would produce another
   session reading rather than a checkable one.
4. **`V7_LEDGER.md` is not edited.** H6 stays **PARTIAL** with 154 / 98; the ledger is a historical
   record and the repair does not retroactively close a finding that was true at V7's tip.
5. **§5's H6 row is not amended.** It still quotes the V7-era check on line 97; §8's new text says
   the row is left unamended and is a historical reading, not a live rule.
6. **`V8_LEDGER.md` and `V9_LEDGER.md` are not edited.** Their sentences that `V7_PROMPT.md` was
   untouched were readings at their own tips; V10's ledger records the change and neither earlier
   ledger is rewritten.
7. **No new plant, guard, ceiling key, CI step, lane, living document or artifact.** The formatter
   corpus moved 242 → 244 only because two Markdown files were added.
8. **No tag movement, no release asset replacement, no V10 release.** The published chain is a
   premise, and the check is that it did not move.
9. **The one local pytest failure was not silenced.** `1 failed, 559 passed in 113.69s` at
   `9118c5c` is the sandbox bytecode-cache plant; no marker, tolerance or deletion was added, and
   CI's `490 passed, 5 skipped` is read instead.
10. **The report PDF was not rebuilt.** `tools.build_report` stays dev-only; no number the paper
    cites has moved.
11. **The repair makes `V7_PROMPT.md` longer, not shorter.** It grows by 11 lines (154 → 165). That
    is reported and attributed: the added text is the history of the old rule plus the standing rule
    that replaces it, and the alternative — silently deleting the sentence — is what V8 and V9
    refused to do.
12. **`V10_PROMPT.md` measures 161 total / 109 prose**, below V9's 112 reference and far below the
    431 hard bound; §8 says a reference is reported, not enforced.

#### 5. Premises audit

1. **The published chain is frozen.** *Final reading:* tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
   published `2026-10-26T09:35:44Z` with four assets sized 2,978 / 55,780 / 145,672 / 1,005,786
   bytes, created `09:35:41Z`, updated `09:35:42Z`–`09:35:43Z`; manifest 95 entries and
   `Evidence is intact.`. **Closed**; every field matches Phase 0's row and no asset was replaced.
2. **The pin is a guard, not a sentence.** *Final reading:* `artifact_revision 17df062040b8`,
   `pinned_revision 17df062040b8`, `pin_holds true`, `gap 0`, `matches_tip false`,
   `object_check "the revision names a commit in this clone"`. **Closed**; V10 changed no guard.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** *Final reading:* 15
   keys, 13 `ok`, 2 `SKIP`; both print `precondition absent` and their `corpus` still describes the
   missing runner precondition. **Closed**; the residue is that both verdicts remain
   development-only, which §4 keeps rather than hides.

#### 6. Series handoff — what a V11 must contain

Derived from this run's evidence, not from the prompt's prose:

1. **A is closed, and the 88 figure is history.** Do not reintroduce it as a gate; the withdrawn
   sentences are quoted in this ledger and the `partial` verdict stays in `V7_LEDGER.md`.
2. **431 is the only hard bound for these prompts.** V6–V10 measure 146 / 88, 154 / 98, 161 / 107,
   164 / 112 and 161 / 109 (V10's own file), and the repaired `V7_PROMPT.md` now measures 165 / 109.
   All are references; exceeding one is reported, not failed.
3. **B and C remain refused with evidence.** A harness redesign or a declarative re-run needs a new
   scope unit that says so in Phase 0; K5 still forbids replacing a published asset.
4. **The D1 reading is checkable but not gated.** CI's checkout is shallow, so an ancestry check
   there would have to skip — a guard that cannot redden. Do not promote it without solving that.
5. **No census was captured at V10's tip.** The last full census remains `195/195` at `5ec3fab` (development-side vantage; the sweep has no CI lane).
6. **The two `SKIP` keys and the sweep/installed-surface vantages stay development-only** under
   `V6_PROMPT.md` §4.
7. **There is no remaining code-level residue from V3–V10.** A V11 must justify its scope against
   `V5_PROMPT.md` §1 rather than invent machinery to look busy.

#### 7. Per-lane verification table

| lane | revision | environment | vantage | verdict |
|---|---|---|---|---|
| `ruff check .` | `9118c5c` | macOS, `.venv` Python 3.12, development checkout | development | `All checks passed!` |
| `ruff format --check .` | `9118c5c` | same | development + CI lint | `244 files already formatted` |
| `mypy python/quantrisk tools` | `9118c5c` | same | development | `Success: no issues found in 74 source files` |
| `pytest -q` (full) | `9118c5c` | same, private `--basetemp=/tmp/qr-v10-final` | development | **not green**: `1 failed, 559 passed in 113.69s` — the sandbox bytecode-cache plant, named not silenced |
| `pytest --collect-only` / `measure_offline_collection` | `9118c5c` | same | development | 560 collected / 491 offline, `collection_errors 0` |
| `--check-ceilings` | `9118c5c` | same | development + CI lint | 15 keys, 13 `ok`, 2 `SKIP`, 0 `FAIL` |
| `--reading docs_rederivation` | `9118c5c` | same | development + CI lint | `gap 0`, 5 documents, `derived {95, 195, 19, 19}` |
| `--reading lanes_documented_vs_executed` | `9118c5c` | same | development + CI lint | `gap 0` |
| `--reading with_extras_census` | `9118c5c` | same | development + CI lint + benchmark-job fresh artifact | `gap 0`, 19/19 |
| `--reading artifact_revision` | `9118c5c` | same | development (deep clone) + lint (shallow clone) + benchmark (fresh artifact) | `gap 0`, `pin_holds true`, `matches_tip false` on the committed vantage |
| `--reading formatter_census` / `registry_parity` / `runtime_reachability` | `9118c5c` | same | development + CI lint | 244/244 (both differences empty), 19/19, `reached_by_neither []` |
| `tools.verify_evidence_manifest` | `9118c5c` | same | development + CI lint | `Evidence is intact.` (95 entries) |
| heading-span measurement of `V7_PROMPT.md` | `ca94a2c` → `9118c5c` | same | development | 154 / 98 → **165 / 109**, delta +11 / +11 |
| mutation sweep, full census | inherited only | same | **development-only, labelled** | `195/195` at `5ec3fab` (development-side vantage; the sweep has no CI lane); **not re-run by V10** |
| `tools.verify_installed_surface` | `3c6092f` | `/tmp/qr-v5-venv`, wheel from that tree, neutral cwd | **development-only, labelled** | identity, 19 tasks, 7 validations, one study, one refusal, 0 residue |
| CI four jobs | `ca94a2c` (run `43034777310`) | `ubuntu-latest` `1000010919`/`1000010920`/`1000010921`, `macos-15` `1000010918` | runner | `completed / success`, attempt 1, 15 / 14 / 15 / 14 steps; re-read from the API for this report |
| CI four jobs | report tip (first V10 push) | runners named in the terminal entry | runner | **not yet read**; no outcome is written for a push that has not happened |
| CI four jobs | terminal tip (second V10 push) | runners named in the session handoff | runner | **not yet read** |

No lane is marked green on a mixed vantage. The census row is inherited and labelled, not claimed as
V10's own. The local failure is named as a failure with its cause and environment.

#### 8. Archival confirmation

- **Tree and tip.** `git status --porcelain` prints 0 lines; `HEAD` is
  `9118c5c4535a15c757226da3628af2d57ce989f2` before this report's commit, with `origin/main` at
  `ca94a2c`. Phase 0, the implementation and this report ship in the first V10 push; the terminal
  entry follows in the second.
- **Every V10 commit an ancestor of the remote.** `ceec03e` (Phase 0) and `9118c5c`
  (implementation) are local ancestors of the terminal commit; this report and the terminal entry
  follow them. Each object SHA is checked against the local object before the ref moves, and the
  platform `/compare` reading is taken after each push.
- **CI for every commit.** The baseline `ca94a2c` has its own run `43034777310`
  (`completed / success`, `run_attempt 1`, created `2026-11-11T14:03:18Z`, updated `14:11:58Z`,
  four jobs 15 / 15 / 14 / 14, runners `1000010918`–`1000010921`). The two V10 push tips are
  attributed after the API reports them; no run is named green before it is read.
- **Registers and documents re-counted.** `registry_parity` 19/19, `with_extras_census` 19/19 /
  `gap 0`; plants 195; ceiling keys 15; manifest 95 intact; `docs_rederivation` 5 documents /
  `gap 0`; formatter 244/244 with both differences empty; nodes 560 / 491 offline; CI steps 34;
  seven prompts and eight ledgers for V3–V10, all present; `artifact_revision gap 0` with
  `pin_holds true`, `lanes_documented_vs_executed gap 0`, `runtime_reachability
  reached_by_neither []`.
- **Tags, releases and assets re-read from the platform.** Tag object
  `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
  `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
  (`v1.9.0`) published `2026-10-26T09:35:44Z` with the same four assets and byte sizes as Phase 0.
  No asset was replaced and no tag moved.
- **No stray instrument tracked or left on disk.** `git ls-files -- tools/derive_requires.py
  build/run_sweep.py build/api_push.py` prints nothing; `git check-ignore` confirms
  `build/api_push.py`, `build/run_sweep.py` and `.workbuddy/` are ignored; no `_mutation_probe`
  directory exists.

#### 9. What V10 changed, and what it did not

It added `V10_PROMPT.md` and `V10_LEDGER.md` and edited one section of `V7_PROMPT.md`. `git diff
--name-only ca94a2c..HEAD` prints exactly those three paths. It changed no source file, guard,
plant, ceiling key, CI step, lane, manifest entry, committed suite artifact, document count or
release asset, and it did not touch `cpp/`, `bindings/`, `CMakeLists.txt`, `PROJECT_SPEC.md`,
`REFACTOR_PROMPT.md`, `V3_PROMPT.md`, `V5_PROMPT.md`, `V6_PROMPT.md`, `V8_PROMPT.md`,
`V9_PROMPT.md`, `V7_LEDGER.md`, `V8_LEDGER.md`, `V9_LEDGER.md`, `evidence/manifest.json` or
`paper/`. The only measurement that moved is the formatter corpus, 242 → 244, because the two added
paths are Markdown.

**The first push.** This report, the Phase 0 commit and the implementation commit are pushed
together in the first of the two pushes authorised in the V10 Phase 0 entry. Its CI is read once the
tool reports it and recorded in the terminal entry; no outcome is stated here for a push that has
not happened.

---
