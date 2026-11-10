# V8_LEDGER.md — cross-session state for the V8 series

Each entry records what was run, what it printed and what was decided, in that order. A number
quoted from an earlier series is named as a historical reading and re-measured before it is used as
a V8 fact. `V8_PROMPT.md` is the rail set; this file is the state.

---

### 2026-11-10, V8 Phase 0 — the closing series launched at `4f76337`

**Why this phase exists.** V7 closed with ten deliberately-not-done items in `V7_LEDGER.md` Phase 5
§4 and eight handoff items in its §6. The first of those items is the only structural one: the
census has never been captured at a literal final tip, because V6 and V7 both ran it on the
implementation tip and then shipped ledger-only commits. V7 §6 item 6 says a series that wants the
literal reading must plan a census after the terminal entry's own push on a clean tree. This is that
series.

**The recommendation this approval accepts.** V8 is a **closing-and-verification** series, not an
implementation one. It takes H1 — the final-tip census — as a process it actually executes, H2 as a
rule it can satisfy (one hard bound, reference figures reported rather than enforced), and H3–H6 as
evidence-backed retention or refusal. It adds no guard, plant, ceiling key, CI step, lane or
document count. That is deliberate: V7 already made the one substantive change its residue called
for (the pin guard), and `V5_PROMPT.md` §1 forbids manufacturing new machinery to replace gates
that are merely inconvenient. A series that invents work to look busy is the failure this rail set
exists to prevent.

**Approval, verbatim.** `授权启动 V8，按你的建议推进剩余系列` (2026-11-10). Per `V8_PROMPT.md` §6
this is the maintainer's **series-wide** approval, recorded here before any outward action. It
explicitly overrides the case-by-case rule for the V8 series and covers H1–H6, the Phase 0 entry,
the Phase 5 report, the terminal entry, the two named pushes and the final-tip census. It does
**not** authorise editing any earlier prompt or `V8_PROMPT.md`, a harness redesign that reopens §4,
a declared re-run of the evidence chain, a tag movement or release asset replacement, a new CI lane,
or a third push. The V7 series-wide approval (`授权启动 V7，按你的建议推进剩余系列`) is spent and
is not reused.

**Revision and vantage.** `HEAD` = `origin/main` = platform `main` =
`4f76337b306ae79aaaf5a07ba4ced545dacc473a`; `git status --porcelain` prints 0 lines. Vantage: the
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
   field matches V7 Phase 5 §8. No regeneration occurred.
2. **The pin is a guard, not a sentence.** `--reading artifact_revision` prints
   `artifact_revision 17df062040b8`, `pinned_revision 17df062040b8`, `pin_holds true`,
   `pin_check "the committed artifact names the pinned historical revision"`, `gap 0`,
   `matches_tip false`, `object_check "the revision names a commit in this clone"`,
   `problems []`, `tip_being_verified 4f76337b306a`. The four forged cases in
   `tests/python/test_artifact_metadata.py` still hold: a real-but-different revision and a wrong
   or missing declaration each print `gap 1`; a fresh upload naming the tip prints `gap 0` with
   `pin_holds null`.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** `--check-ceilings`
   prints **15** keys, 13 `ok`, 2 `SKIP`. `plants_not_rejected_by_their_guard` prints
   `precondition absent` and its `corpus` says the collector measures only the declaration because
   the sweep's gitignored scratch never reaches the runner. `installed_user_identity_mismatch`
   prints `precondition absent` and its `corpus` says the clean-venv probe installs a second
   environment the runner cannot have. Both printed reasons still agree with their `corpus` and
   `can_fail_because` fields in `tools/refactor_ceilings.json`.

**The archive re-counted at `4f76337`.**

| quantity | command that produced the reading | value |
|---|---|---|
| registry tasks / suite members | `--reading registry_parity`; `with_extras_census` | 19 / 19; `gap 0` |
| plants | `runner --list` | **195** (last full census `195/195` at `0c239c5` — development-side vantage; the sweep has no CI lane) |
| ceiling keys | `--check-ceilings` | **15** — 13 `ok`, 2 `SKIP` |
| manifest | `tools.verify_evidence_manifest` | `Evidence is intact.` (95 entries) |
| formatter corpus | `--reading formatter_census` | **238 / 238**, both differences empty |
| pytest nodes | `--collect-only`; `measure_offline_collection` | **560**; offline **491**, `collection_errors 0` |
| named CI steps | the workflow's `- name:` lines | **34** |
| living documents / lane contract | `docs_rederivation`; `lanes_documented_vs_executed` | 5 documents, `gap 0`, `derived {95, 195, 19, 19}`; `gap 0` |
| artifact revision / runtime reachability | two readings | `gap 0`, `pin_holds true`; `reached_by_neither` empty |
| static gates | `ruff check .`; `ruff format --check .`; `mypy python/quantrisk tools` | `All checks passed!`; `238 files already formatted`; `Success: no issues found in 74 source files` |

**What this unit takes, and what it excludes.** It takes H1 (a census at the literal final tip,
after the terminal push, quoted in the session handoff), H2 (a size rule V8 can satisfy), H3 (V7's
two standing sentences recorded as historical fact, not edited), H4 (both `SKIP` keys re-read and
retained), H5 (manifest and platform assets re-read twice, nothing regenerated) and H6 (the
environmental pytest failure attributed), together with the Phase 5 report. It excludes new code,
guards, plants, ceiling keys, CI steps and lanes; it excludes editing any prompt; it excludes
regenerating `suite_run.json`, `evidence/manifest.json`, a report or a release asset; and it
excludes a third push. `V6_PROMPT.md` §4 and `V7_PROMPT.md` §4 already close the sweep and
installed-surface vantages; this unit does not reopen them.

**Deliberately not done in Phase 0.** No source file, policy asset or document was edited, no
census was run, no report section was written and no push was made. Every number above is a reading
at `4f76337`. The full census belongs to the final tip, after the terminal entry's own push, per
H1; the Phase 5 liveness table names V7's `195/195` at `0c239c5` as the inherited reading and says
so rather than claiming a V8 verdict before it exists.

**The two pushes.** The first carries this Phase 0 commit and the Phase 5 report; the second carries
the terminal entry only. No third is implied. Each push's CI is read from the API after the tool
reports it; the first tip's run is attributed in the terminal entry and the second tip's run in the
session handoff. The final-tip census runs after the second push, on a clean tree, and is quoted in
the session handoff with its revision.

---

### 2026-11-10, V8 Phase 5 — the report, the liveness table, and the plan for the final-tip census

**How this was assembled.** From this ledger's Phase 0 entry plus fresh readings at
`13814489906daa750451b4484db0711b3de11090` on a clean tree. V8 has no implementation commit: its
only tracked additions are `V8_PROMPT.md` and this file, so no guard, plant, ceiling key, CI step,
lane or document count can move. The census is the one reading V8 does not take here, by design —
H1 puts it after the terminal push, at the literal final tip.

#### 1. Evidence ledger

| id | verdict | probe | closing commit |
|---|---|---|---|
| H1 | **deferred to the final tip** | Phase 0 states the rule, this report states the plan, and the census runs on the clean tree at the terminal commit after the second push; its summary line and revision are quoted in the session handoff, and the series is not declared closed until that line exists | this report + the terminal entry |
| H2 | **fixed** | `V8_PROMPT.md` §8 states one hard bound (431) and reports V6's 146 / 88 and V7's 154 / 98 as reference figures; V8 measures **161 total / 107 prose**, which is inside 431 and is reported here with its growth attributed | `13814489` |
| H3 | **fixed, recorded not edited** | `V7_PROMPT.md` §8's 88-line soft figure and "growth only in §5 and §3" are named in §4 item 2 below and in §6 item 2; the file is untouched, as its §6 requires | `13814489` |
| H4 | **fixed** | both `SKIP` keys re-read at `4f76337`, each `corpus` agreeing with its printed `precondition absent` reason; no lane, plant, key or flag added for either | `13814489` |
| H5 | **fixed** | manifest (95 intact) and the platform's tag, release and four assets re-read in Phase 0 and again in §8 below with equal values; nothing regenerated and the pin not moved | `13814489`, this entry |
| H6 | **fixed** | the local `1 failed, 559 passed` reading is named in §7 as the sandbox bytecode-cache plant; no marker, tolerance or deletion added; CI's `490 passed, 5 skipped` is read instead | `13814489` |

#### 2. Liveness table, re-evaluated at `13814489`

| # | law | verdict | the reading that decided it |
|---|---|---|---|
| N1 | requirement truth | **ACTIVE** | `registry_parity`: `filesystem_units 19`, `registry_sources 19`, `mismatch []` |
| N2 | advertised surface honesty | **ACTIVE** | the V5 F5 clean-venv wheel proof (19 tasks, 7 validations, one study, one refusal, zero residue); development-only in §7, not promoted |
| N3 | lane contract | **ACTIVE** | `lanes_documented_vs_executed gap 0`; **34** named CI steps, unchanged by a series that adds no step |
| N4 | no silence by count | **ACTIVE** | `with_extras_census gap 0`, `members 19`, `passed 19`; `docs_rederivation gap 0`, `mismatches []`, `source_disagreements []` |
| N5 | declarations are checkable | **ACTIVE** | 15 keys, 13 `ok`, 2 `SKIP`; `pinned_revision` is compared in both directions and `pin_holds true` on the committed artifact |
| N6 | runtime reachability | **ACTIVE** | `runtime_reachability` prints `reached_by_neither []` |
| N7 | one finding, one commit | **ACTIVE** | Phase 0, this report and the terminal entry map to H1–H6; no commit spans two findings |
| N8 | no gate weakened | **ACTIVE** | V8's diff is two `.md` files: no `skip`/`xfail`, no tolerance, no test deleted, no `max` raised, no `may_be_unmeasured` added |
| N9 | plant liveness | **ACTIVE, inherited reading** | last captured census `195/195` at `0c239c5` (development-side vantage; the sweep has no CI lane); no V8 path can move a plant verdict, and H1's reading is taken at the final tip |
| N10 | one re-run | **ACTIVE, not triggered** | no evidence artifact regenerated: `suite_run.json` still names `17df062040b8`, the manifest still holds 95 intact entries, no freeze re-run |
| N11 | facts precedence | **ACTIVE** | `docs_rederivation gap 0`, 5 documents, `derived {95, 195, 19, 19}`; no printed count moved |
| N12 | baseline purity and per-lane provenance | **ACTIVE** | §7 names a revision, an environment **and** a vantage for every lane; the baseline `4f76337` has its own CI run `42808340869` (`completed / success`, attempt 1) |

#### 3. The ceilings file's final state

`tools/refactor_ceilings.json` carries **15** keys, untouched by V8. Thirteen are `ok` at `0`; two
are `SKIP` with `may_be_unmeasured: true`: `plants_not_rejected_by_their_guard` and
`installed_user_identity_mismatch`.

**Review notes.** V8 added no key, no `max` change, no exemption and no `may_be_unmeasured`. The
`pinned_revision` declaration V7 added is unchanged and still read by `pinned_suite_revision()`. A
series that adds no policy asset is the right shape here: every key already has a live reading and a
named reason, and adding a sixteenth to record "V8 checked them" would be the declaration-counting
failure `V5_PROMPT.md` §1 warns about.

#### 4. The deliberately-not-done list

1. **H1's census is not run in this report.** It belongs to the literal final tip by construction:
   a file cannot carry the SHA of the commit that contains it. The plan is stated here and in the
   terminal entry; the reading lands in the session handoff.
2. **`V7_PROMPT.md` §8 is not edited.** Its two standing sentences are historical fact; editing it
   needs its own verbatim approval under V7 §6, which the V8 series-wide sentence does not supply.
3. **The sweep still has no CI lane.** `plants_not_rejected_by_their_guard` stays `SKIP`
   permanently; converting it needs the harness redesign V6 §4 names, excluded by V8 Phase 0.
4. **The installed-surface proof is still not a CI lane.** The clean-venv probe needs a second
   environment the runner does not have.
5. **The committed `suite_run.json` was not regenerated.** A declared re-run would move the
   manifest and the release asset set, and the published zip cannot be replaced under K5.
6. **No second vantage was built for `195/195`.** The census verdict remains development-side and
   is labelled wherever cited.
7. **No new plant, ceiling key, CI step or lane.** V8 adds two Markdown files and nothing else.
8. **The report PDF was not rebuilt.** `tools.build_report` stays dev-only; no number moved, so no
   re-render was called for.
9. **No V8 release.** The published chain is unchanged by design; H5's check is that it did not
   move.
10. **The one local pytest failure was not silenced.** It is named with its environment in §7; CI's
    verdict is read instead.

#### 5. Premises audit

1. **The published chain is frozen and V8 must not move it silently.** *Final reading:* tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
   published `2026-10-26T09:35:44Z` with four assets sized 2,978 / 55,780 / 145,672 / 1,005,786
   bytes, created `09:35:41Z`, updated `09:35:42Z`–`09:35:43Z`; manifest 95 entries and
   `Evidence is intact.`. **Closed**; every field matches Phase 0's row.
2. **The pin is a guard, not a sentence.** *Final reading:*
   `--reading artifact_revision` at `13814489` prints `artifact_revision 17df062040b8`,
   `pinned_revision 17df062040b8`, `pin_holds true`, `gap 0`, `matches_tip false`, `problems []`.
   **Closed**; V8 changed nothing in the guard, and the four forged cases remain in the F4 test.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** *Final reading:* 15
   keys, 13 `ok`, 2 `SKIP`; both printed `precondition absent` with their `corpus` describing the
   missing runner precondition; both retained. **Closed**; the residue is that both verdicts remain
   development-only, which H4 labelled rather than hid.

#### 6. Series handoff — what V9 must contain

Derived from this run's evidence, not from the prompt's prose:

1. **The final-tip census is a session reading.** V9 inherits the line quoted in the handoff at
   `4f76337`'s successor; a later series that wants another literal final-tip reading must plan it
   the same way, after its own terminal push.
2. **`V8_PROMPT.md` §8 is satisfiable and satisfied.** The 431 bound holds; the 107 prose lines are
   reported, not enforced. A V9 prompt may copy this shape rather than V7's unsatisfiable 88.
3. **The sweep and installed-surface vantages are closed.** `V6_PROMPT.md` §4 and `V7_PROMPT.md`
   §4 permit reopening only through a harness redesign whose Phase 0 says so. A V9 that lists them
   as open questions has read neither.
4. **The two `SKIP` keys still have no runner vantage.** They were re-read twice more and retained
   with reasons; a second vantage remains an idea, not a gate.
5. **The printed `195/195` line stays labelled.** Any new document quoting it must carry the
   development-side label on the same line, and `docs_rederivation` must stay at `gap 0`.
6. **No silent re-freeze remains standing.** The 95-entry manifest and the `v1.9.0` assets are the
   published chain; the pin guard makes an undeclared rewrite fail a reading.
7. **The local pytest failure is environmental.** Do not weaken a gate to turn `1 failed, 559
   passed` into green; attribute it and read CI.
8. **There is no remaining code-level residue from V3–V8.** The pin, the readings, the ceilings,
   the lanes and the census vantage are each either guarded or named. A V9 must justify its scope
   against `V5_PROMPT.md` §1 — a series that invents machinery to look busy is the failure mode
   this handoff exists to prevent.

#### 7. Per-lane verification table

| lane | revision | environment | vantage | verdict |
|---|---|---|---|---|
| `ruff check .` | `13814489` | macOS, `.venv` Python 3.12, development checkout | development | `All checks passed!` |
| `ruff format --check .` | `13814489` | same | development + CI lint | `240 files already formatted` |
| `mypy python/quantrisk tools` | `13814489` | same | development | `Success: no issues found in 74 source files` |
| `pytest -q` (full) | `13814489` | same, private `--basetemp` | development | **not re-run in this report**; the last reading is `1 failed, 559 passed` at `0c239c5`, and V8 changes no test or source file |
| `pytest --collect-only` / `measure_offline_collection` | `13814489` | same | development | 560 / 491, `collection_errors 0` |
| mutation sweep, full census | **final tip, after the second push** | same, bulk-delete threshold raised locally | **development-only, labelled** | **deferred** — H1's reading; quoted in the session handoff |
| `--check-ceilings` | `13814489` | same | development + CI lint | 15 keys, 13 `ok`, 2 `SKIP`, no `FAIL` |
| `--reading docs_rederivation` | `13814489` | same | development + CI lint | `gap 0`, 5 documents, `derived {95, 195, 19, 19}` |
| `--reading lanes_documented_vs_executed` | `13814489` | same | development + CI lint | `gap 0` |
| `--reading with_extras_census` | `13814489` | same | development + CI lint + benchmark-job fresh artifact | `gap 0`, 19/19 |
| `--reading artifact_revision` | `13814489` | same | development (deep clone) + lint (shallow clone) + benchmark (fresh artifact) | `gap 0`, `pin_holds true`, `matches_tip false` on the committed vantage |
| `--reading formatter_census` / `registry_parity` / `runtime_reachability` | `13814489` | same | development + CI lint | 240/240 (both differences empty), 19/19, `reached_by_neither []` |
| `tools.verify_evidence_manifest` | `13814489` | same | development + CI lint | `Evidence is intact.` |
| `tools.verify_installed_surface` | `3c6092f` | `/tmp/qr-v5-venv`, wheel from that tree, neutral cwd | **development-only, labelled** | identity, 19 tasks, 7 validations, one study, one refusal, 0 residue |
| CI four jobs | `4f76337` (run `42808340869`) | `ubuntu-latest` `1000010732`/`1000010734`/`1000010735`, `macos-15` `1000010733` | runner | `completed / success`, attempt 1, 15 / 14 / 14 / 15 steps; re-read from the API for this report |
| CI four jobs | report tip (first V8 push) | runners named in the terminal entry | runner | **not yet read**; no outcome is written for a push that has not happened |
| CI four jobs | terminal tip (second V8 push) | runners named in the session handoff | runner | **not yet read** |

No lane is marked green on a mixed vantage. The census row is deferred rather than inherited into a
green: V7's `195/195` at `0c239c5` is named as a historical reading, not as V8's verdict. The one
local failure is named as a failure with its cause and environment.

#### 8. Archival confirmation

- **Tree and tip.** `git status --porcelain` prints 0 lines; `HEAD` =
  `13814489906daa750451b4484db0711b3de11090` before this report's commit, with `origin/main` at
  `4f76337`. Phase 0 and this report ship in the first V8 push; the terminal entry follows in the
  second, and the session handoff records the final tip.
- **Every V8 commit an ancestor of the remote.** `13814489` (Phase 0), this report and the terminal
  entry are local ancestors of the terminal commit and ship in the two pushes; each object SHA is
  checked against the local object before the ref moves. The platform `/compare` reading for the
  pushed range is taken after the push and recorded in the terminal entry; the terminal commit is
  verified after its own push.
- **CI for every commit.** The baseline `4f76337` has its own run `42808340869`
  (`completed / success`, `run_attempt 1`, four jobs 15 / 14 / 14 / 15, runners
  `1000010732`–`1000010735`, created `11:32:46Z`, updated `11:40:44Z`). The two V8 push tips are
  attributed in the terminal entry and the session handoff after the API reports them; no run is
  named green before it is read.
- **Registers and documents re-counted.** `registry_parity` 19/19; `with_extras_census` 19/19,
  `gap 0`; `plant_liveness` 195 and the inherited census `195/195` at `0c239c5` (development-side
  vantage); manifest 95 intact; `docs_rederivation` 5 documents / `gap 0`; formatter 240/240; nodes
  560/491; CI steps 34; ceiling keys 15. `artifact_revision gap 0` with `pin_holds true`,
  `lanes_documented_vs_executed gap 0`, `runtime_reachability` `reached_by_neither []`.
- **Tags, releases and assets re-read from the platform.** Tag object
  `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
  `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
  (`v1.9.0`) published `2026-10-26T09:35:44Z` with four assets, sizes 2,978 / 55,780 / 145,672 /
  1,005,786 bytes, created `09:35:41Z`, updated `09:35:42Z`–`09:35:43Z`. All match Phase 0's rows;
  no asset was replaced.
- **No stray instrument tracked or left on disk.** `git ls-files -- tools/derive_requires.py
  build/run_sweep.py build/api_push.py` prints nothing; `git check-ignore` confirms
  `build/api_push.py`, `build/run_sweep.py` and `.workbuddy/` are ignored; no `_mutation_probe`
  directory exists; the census log will be `/tmp/v8_census.log`, outside the repository.

#### 9. What V8 changed, and what it did not

It added `V8_PROMPT.md` and `V8_LEDGER.md` and nothing else. `git diff --name-only 4f76337..13814489`
prints exactly those two paths. It changed no source file, guard, plant, ceiling key, CI step,
lane, manifest entry, committed suite artifact, document count or release asset. It did not touch
`cpp/`, `bindings/`, `CMakeLists.txt`, `PROJECT_SPEC.md`, `REFACTOR_PROMPT.md`, `V3_PROMPT.md`,
`V5_PROMPT.md`, `V6_PROMPT.md`, `V7_PROMPT.md`, `evidence/manifest.json` or `paper/`, and it did
not move `v1.9.0`.

**The first push.** This report and the Phase 0 commit are pushed together in the first of the two
pushes authorised in the V8 Phase 0 entry. Its CI is read once the tool reports it and recorded in
the terminal entry; no outcome is stated here for a push that has not happened.

---

### 2026-11-10, V8 terminal entry — the report tip is green, and the census moves to the final tip

**The report tip's CI, attributed.** Run `42813273094` on
`04df4ffceac6a84e55dac970fb4d9016cd2bcee0` is `completed` / `success`, `run_attempt 1`, created
`12:08:52Z`, updated `12:19:58Z`. `gh run watch` returned 0 after 10m50s; the run and jobs below
were read again from the API before this entry was written. Four jobs, all `success`:

| job | steps | runner | labels |
|---|---|---|---|
| `129819820949` Format and static checks | **15** | `1000010753` | `ubuntu-latest` |
| `129819821164` Benchmark suite against live oracles | **15** | `1000010755` | `ubuntu-latest` |
| `129819821232` Configure, build, C++ tests, Python tests | 14 | `1000010754` | `ubuntu-latest` |
| `129819821857` macOS native C++ and Python parity | 14 | `1000010756` | `macos-15` |

No job is cancelled, none has 0 steps and no step failed. The only annotations are GitHub's
`ubuntu-latest` migration notice and a macOS capacity notice, neither a failure.

**What the four logs printed.** Lint: `240 files already formatted`, `declared_plants 195`,
`artifact_revision_gap 0 ... due V5-02 / V7-01`, `docs_rederivation_gap 0`,
`with_extras_census_gap 0`, `lanes_documented_vs_executed_gap 0` and `Evidence is intact.`; its
`Artifact revision` step printed `matches_tip false`, `pinned_revision 17df062040b8`,
`pin_holds true` and `pin_check "the committed artifact names the pinned historical revision"`.
Build-and-test: `100% tests passed out of 204`, `490 passed, 5 skipped in 128.70s`, `7/7 checks
passed`. macOS: `100% tests passed out of 204`, `98 passed in 3.73s`. Benchmark: `suite: 19/19
executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 425.7s total`; its
`Artifact revision at the run tip` step printed `matches_tip true`, `pin_holds null` and
`pin_check "not applicable: the fresh artifact names the tip of the run that wrote it"`. The pin's
two vantages therefore still behave as V7's implementation predicted, with no V8 file involved.

**The series' commit count, final.** Three commits in `4f76337..` — `13814489` (V8 Phase 0),
`04df4ff` (this report's predecessor) and this terminal entry. Platform `/compare/4f76337...04df4ff`
returned `ahead_by 2`, `behind_by 0`, with both as ancestors of the then-tip; the two commits of
the first push were each reconstructed through the Git Data API with their blob, tree and commit
SHAs checked against the local objects before the ref moved. `git diff --name-only` over the range
prints exactly two paths: `V8_PROMPT.md` and `V8_LEDGER.md`. The terminal commit is pushed after
this file's content is fixed, and its own CI is read in the session handoff rather than written
here.

**Two pushes, as recorded in the V8 Phase 0 entry.** The first carried `13814489` and `04df4ff`;
the second carries this entry only. No repair was needed: the CI was green on the first attempt and
V8 changes no source, guard, plant, ceiling key or CI step.

**V8 is closed with one reading still owed by construction.** H2–H6 are fixed or recorded; H1 is
**deferred to the literal final tip**, which is this commit. The plan is now executed: after this
entry's push, `build/run_sweep.py --all` runs on the clean tree at that commit, and its summary
line and revision are quoted in the session handoff. The series is not declared closed in speech
until that line exists; the ledger deliberately does not claim it early, because a file cannot
carry the SHA of the commit that contains it without moving the tip it measures. The eight
`V3_PROMPT.md` §12 deliverables are in the preceding section; the platform's tag, release and four
asset timestamps were re-read in Phase 0, Phase 5 and again before this entry and match. What
remains open is named in the report's §4 and §6 and belongs to V9. No third push is implied.

---
