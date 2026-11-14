# V13_LEDGER.md — the cross-session state of the V13 series

V13 is a single-unit series with one finding, D1: the final-tip census attestation is read by a
heredoc in a ledger, and the reading compares a past revision's counts with today's declaration.
`V13_PROMPT.md` is the rail set; where the two disagree, the prompt wins.

---

## Phase 0 — 2026-11-14, the scope unit, its baseline, and what it excludes

### 1. The approval, verbatim

> 好的，继续

It answers the writer's proposal in the preceding turn — *"下一个单元就做 D1；它需要一句新的范围句"* —
so the unit is named by the proposal and assented to by the reply. Both are recorded rather than the
reply alone, because `继续` on its own has never been treated as scope-bearing in this repository.

### 2. Revision and vantage

- **Revision.** `5dfd6bb69924b285114e277a99b51acd583af545`, the V12 terminal entry. `HEAD`,
  `origin/main` and the platform's `main` all read it; `git status --porcelain` is empty.
- **Baseline vantage.** development, deep clone: `git cat-file -e 5ec3fab^{commit}` and
  `git merge-base --is-ancestor 5ec3fab HEAD` both exit 0. The lane that decides D1 must be a
  deep-history lane, because a shallow checkout cannot prove ancestry — which is why the step goes
  in `build-and-test` and not in `lint`.

### 3. Re-measured baseline at `5dfd6bb`

| Reading | Command | Value |
|---|---|---|
| static checks | `ruff check .` | `All checks passed!` |
| formatter | `ruff format --check .` | 248 files already formatted |
| types | `mypy python/quantrisk tools` | `Success: no issues found in 74 source files` |
| ceilings | `--check-ceilings` | 15 keys: 13 `ok`, 2 `SKIP`, 0 `FAIL` (development vantage) |
| plants | `runner --list` | 195 |
| collection | `pytest --collect-only -q` | 560 tests collected |
| lanes | `--reading lanes_documented_vs_executed` | `gap 0`, 9 declared / 9 documented / 7 executed |
| manifest | `tools.verify_evidence_manifest` | `Evidence is intact.`, 95 entries |

`V13_PROMPT.md` measures **83 total / 57 prose** by the heading-span rule.

### 4. What the unit carries, and what it excludes

**Carries.** `tools/verify_final_tip_census.py`; one step in `build-and-test`; the lane-contract row;
a claim in `CONTRIBUTING.md`; one falsification block inside an existing test; this series' two files.

**Excludes.** No plant (195 stays 195), no ceiling key (15 stays 15), no new job, no change to the
attestation, no change to `lint`'s shallow vantage, no tag or release movement, and nothing on C.

**The design decision, stated once.** The V9 heredoc refused a block whose counts disagreed with
`runner --list` at `HEAD`. That comparison is time-dependent: a later unit adding a plant would turn
it red for a reason that says nothing about the attestation, and `V9_LEDGER.md` §6 item 4 forbids
the refresh that would fix it. V13 keeps the ancestry, existence and self-consistency checks and
drops the present-day comparison — the attestation is a claim about `5ec3fab`, and it is judged as
one. The `evidence_limit` field becomes required, because an attestation that stops carrying its
limit claims more than it measured.

### 5. The pushes

1. **First** carries Phase 0, the implementation and the Phase 5 report.
2. **Second** carries the terminal entry only.
3. **Reserved** for repairing a red run of either.

---

## Phase 5 — 2026-11-14, the report and the archival confirmation

### 1. Evidence ledger

| id | verdict | probe | closing commit |
|---|---|---|---|
| D1 — the attestation is read by a heredoc, and against today's count | **fixed** | `tools.verify_final_tip_census` prints `PASS: V9_LEDGER.md attests 5ec3fab… as a strict ancestor of …`; `.github/lane_contract.md` names `build-and-test :: Final-tip census attestation`; `lanes_documented_vs_executed` prints `gap 0` | first push |
| D1a — a malformed or lying block was not falsified in the suite | **fixed** | the eight DoD refusal classes exercised over ten forged inputs with stubbed git calls: schema, revision shape, missing object, self-reference, non-ancestor, counts disagreeing with the summary, non-zero exit, empty evidence limit | first push |
| C — the evidence chain re-run | **rejected** | K5 says `Never.` | — |

### 2. Liveness table, re-evaluated at `5dfd6bb`

| id | claim | verdict | reading |
|---|---|---|---|
| N1 | every ceiling key is measured or honestly skipped | **ACTIVE** | 15 keys; lint/development 13 `ok` / 2 `SKIP` (V12 run `43549438249`, job `132308224171`); both lane vantages measured |
| N2 | the lane contract agrees with both enumerations | **ACTIVE** | `gap 0`; 10 declared / 10 documented / 8 executed |
| N3 | a dev-only row carries a reason | **ACTIVE** | `build_evidence_manifest` and `build_report` keep theirs |
| N4 | no silence by count | **ACTIVE** | `with_extras_census gap 0`; `docs_rederivation gap 0` |
| N5 | the pin is a guard | **ACTIVE** | `pinned_revision 17df062040b8`, `pin_holds true`, `gap 0` |
| N6 | the formatter corpus is two-sided | **ACTIVE** | two-sided empty at 251 / 251 after all three new files (two Markdown, one Python) are tracked |
| L7 | every declared plant is rejected by its guard | **ACTIVE** | V11's `194/194` plus one declared environment-blind |
| L8 | the installed import resolves inside its environment | **ACTIVE** | V12's `installed_user_identity_mismatch: 0` on the installed vantage |

### 3. The ceilings file's final state

15 keys, unchanged. V13 adds no key: the new step's exit code is the gate, and a key would duplicate
it while forcing a count change that the attestation does not need.

### 4. The deliberately-not-done list

1. **The attestation is not refreshed.** `V9_LEDGER.md` is read, never edited.
2. **No plant was added**, so the attestation's `195` keeps agreeing with the declaration.
3. **No new ceiling key, no new job, no new collected test** — 15 keys, six jobs, 560 items.
4. **`lint` stays shallow.** Making it deep would change the `artifact_revision` vantage that V5–V7
   documented; the deep-history job already exists and is the right host.
5. **C is not run.** K5 forbids replacing a published asset.

### 5. Premises audit

1. **The published chain is frozen.** Tag → commit, four assets, 95-entry manifest intact. **Closed.**
2. **Both former `SKIP` keys are measured on a runner.** **Closed** with their vantages named. A
   refinement, not a contradiction: V12's own lint job (run `43549438249`, job `132308224171`)
   prints **13 `ok` / 2 `SKIP`**, because a vantage that ran neither lane reports the absence of
   both verdicts. V12's ledger recorded `14 / 1`; the CI log is the reading, so V13 records `13 / 2`
   and says which vantage took it.
3. **The attestation is readable and ancestral.** `5ec3fab` is a strict ancestor of `5dfd6bb`.
   **Closed.**
4. **The plant list is 195.** **Closed**; V13 does not move it.

### 6. Series handoff — what a V14 must contain

1. **Every railing is now measured on a runner and gated where it runs.** There is no development-only
   key, no heredoc reading, and no lane without a contract row.
2. **The attestation is judged as history.** Do not add a check that compares its counts with the
   current declaration; that is the defect V13 removed.
3. **C remains refused under K5**, and it is the only item the repository has ever refused.
4. **A new unit must justify its scope against `V5_PROMPT.md` §1** rather than invent machinery.

### 7. Per-lane verification table

| Lane | Command | Revision | Environment | Verdict |
|---|---|---|---|---|
| static checks | `ruff check .`, `ruff format --check .`, `mypy` | `5dfd6bb` | development | green; mypy corpus 75 with the new tool |
| formatter census | `--reading formatter_census` | `5dfd6bb` | development | two-sided empty, 251 / 251 after the three new files are staged |
| ceilings | `--check-ceilings` | `5dfd6bb` | development | 15 keys, 13 `ok`, 2 `SKIP`, 0 `FAIL` |
| lane contract | `--reading lanes_documented_vs_executed` | `5dfd6bb` | development | `gap 0` |
| final-tip attestation | `verify_final_tip_census` | `5dfd6bb` | development, deep clone | `PASS`, `5ec3fab` a strict ancestor, 195 of 195 |
| Python tests | `pytest -q` | `5dfd6bb` | development | `1 failed, 559 passed`. The single failure is the known sandbox-only bytecode plant `test_a_restored_plant_cannot_be_read_back_from_a_stale_bytecode_cache`: no `__pycache__` is written beside the module, so its control cannot run. CI reads `490 passed, 5 skipped`. Named, not silenced |
| CI, first push | all six jobs | first push | ubuntu-latest / macos-15 | attributed in the terminal entry |

### 8. Archival confirmation

Filled after the second push: `HEAD` equal to `origin/main` and to the platform's `main`, tree clean,
both runs attributed, and no stray instrument tracked or left on disk.

---

## Terminal entry — 2026-11-14, the first push is green and the series closes

### 1. The first push

`ebd7d84c459e4afc38c75fa1a44c4ec7ebb9374c` is `HEAD`, `origin/main` and the platform's `main`;
`/compare/5dfd6bb...ebd7d84` reads `ahead_by 1 / behind_by 0`. The ref moved non-forced
(`ref moved to ebd7d84c… (non-forced fast-forward)`), and the commit's blob, tree and commit SHAs
matched locally and remotely. One commit carries Phase 0, the implementation and the Phase 5 report;
`git diff --name-only 5dfd6bb..ebd7d84` prints exactly the seven paths Phase 0 §4 names.

### 2. Its CI, read from the API

Run **`43558380084`**, attempt **1**, head `ebd7d84`, event `push`, `status: completed`,
`conclusion: success`, created `2026-11-14T04:47:33Z`, updated `05:06:45Z`. Six jobs, no failed
step; the failed-step query returns an empty list, and the lint job prints no `VIOLATION` or `FAIL`
line.

| job | job id | runner | environment | steps |
|---|---|---|---|---|
| Format and static checks | 132336304218 | 1000011455 | ubuntu-latest | 15 |
| Configure, build, C++ tests, Python tests | 132336304213 | 1000011456 | ubuntu-latest | 15 |
| macOS native C++ and Python parity | 132336304208 | 1000011453 | macos-15 | 14 |
| Benchmark suite against live oracles | 132336304034 | 1000011454 | ubuntu-latest | 15 |
| Mutation census in a detached worktree | 132336304236 | 1000011457 | ubuntu-latest | 14 |
| Installed wheel surface in a clean environment | 132336304317 | 1000011458 | ubuntu-latest | 13 |

`build-and-test` grew from 14 to 15 steps: step 12 is `Final-tip census attestation`, conclusion
`success`. A watcher was interrupted by SIGTERM before the run completed; per `V3_PROMPT.md` §14 the
absence of its report is `unknown`, so the platform state was re-read from the API. Every verdict in
this entry is that API reading, not the watcher's exit code. No run is cancelled and no job has zero
steps.

### 3. What the new step printed

```
PASS: V9_LEDGER.md attests 5ec3fabe4fa8c83584a50b3ab66b357ae13094e9 as a strict ancestor of ebd7d84c459e, 195 caught of 195 declared
```

That is `V13_PROMPT.md` §4 item 2, on `ubuntu-latest` in the job with `fetch-depth: 0`. The same job
printed `490 passed, 5 skipped in 237.92s`; lint printed `All checks passed!`, `251 files already
formatted`, `Success: no issues found in 75 source files` and 15 keys with 13 `ok` / 2 `SKIP` /
0 `FAIL`; the census printed `195 declared = 194 measurable here + 1 environment-blind` and
`ok plants_not_rejected_by_their_guard: 0 against a ceiling of 0 due P3.2`; the installed-surface
job printed `ok installed_user_identity_mismatch: 0 against a ceiling of 0 due P4.1`.

**One figure was corrected before this push.** Phase 0 §3, §2 N1 and §7 now read 13 `ok` / 2 `SKIP`
instead of the 14 / 1 copied from V12's ledger. The evidence is V12's own lint log (run
`43549438249`, job `132308224171`), which prints two `SKIP` lines because that vantage ran neither
lane. `V13_PROMPT.md` §0 premise 2 was reworded in place to name the vantage rather than the count;
the edit kept the prompt at 83 total / 57 prose by the heading-span rule. Only V13's own two files
were corrected; no earlier ledger was amended.

### 4. The second push

Carries this terminal entry only. Its CI is read after the push and attributed in the session
handoff; no outcome is stated here for a run that has not happened. Work resumed on the maintainer's
`继续` (2026-11-14) with the implementation present but uncommitted; no new scope was introduced,
and the unit is still the D1 named by `好的，继续`.

### 5. What is not claimed

No tag moved (`v1.9.0` object `d9deb7f…` → `b2dda33…`), no release asset was replaced
(`424060629` still holds four), the manifest still holds 95 entries and verifies intact,
`V9_LEDGER.md`'s attestation is read but never edited, and no plant (195), ceiling key (15), job (6)
or collected test (560) changed. `lint` stays shallow; the local `pytest -q` keeps its one
sandbox-only bytecode-plant failure, named rather than silenced; C stays refused under K5.

---
