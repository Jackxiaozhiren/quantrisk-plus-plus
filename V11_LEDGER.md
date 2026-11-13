# V11_LEDGER.md — the cross-session state of the V11 series

V11 is a single-unit series with one finding, B1: the mutation sweep's vantage is
development-only. This file carries the Phase 0 entry, the implementation record, the Phase 5 report
and the terminal entry. `V11_PROMPT.md` is the rail set; where the two disagree about what V11 may
do, the prompt wins.

---

## Phase 0 — 2026-11-13, the scope unit, its baseline, and what it excludes

### 1. The approval, verbatim

> 启动 V11，只做 B 项

The maintainer selected that sentence from a card that stated its cost before it was chosen:
harness redesign, a new CI lane, and a ~38-minute runner census. It is a **single-unit** approval
and is recorded here before any outward action. It is not reused by any later unit, and `开启 V11`,
`继续` and `全部授权批准` alone were refused as scope-free in the previous session.

### 2. Revision and vantage

- **Revision.** `3725dfa69b3c7180d319ea0c692d2028955d55df`, the V10 terminal entry. `HEAD`,
  `origin/main` and the platform's `main` all read that value; `git status --porcelain` is empty.
- **Baseline vantage.** development machine, deep clone, `git rev-parse --is-shallow-repository`
  false. The census V11 adds runs on `ubuntu-latest`, so the unit carries **two** vantages and
  reports them separately rather than averaging them.
- **The finding taken.** B1: the repository's strongest falsification instrument — 195 plants, each
  required to make a named guard go red — is executed only on a development machine.
  `.github/lane_contract.md` declares `quantrisk.verification.runner` `dev-only`;
  `V6_PROMPT.md` §4 made that permanent; `V10_LEDGER.md` §6 item 4 records the consequence and §6
  item 3 says B stays refused. A push that disarmed a guard would be green.

### 3. Re-measured baseline at `3725dfa`

| Reading | Command | Value |
|---|---|---|
| static checks | `ruff check .` | `All checks passed!` |
| formatter | `ruff format --check .` | `244 files already formatted` |
| types | `mypy python/quantrisk tools` | `Success: no issues found in 74 source files` |
| ceilings | `tools.inventory_orphan_code --check-ceilings` | 15 keys: 13 `ok`, 2 `SKIP`, 0 `FAIL` |
| the two skips | same | `installed_user_identity_mismatch`, `plants_not_rejected_by_their_guard`, each `precondition absent` |
| plants | `quantrisk.verification.runner --list` | **195** (185 `prose`, 4 `core`, 6 `tree`) |
| collection | `pytest --collect-only -q` | `560 tests collected` |
| formatter census | `--reading formatter_census` | `reported_total 244`, both differences `[]` |
| CI steps | `grep -c '^[[:space:]]*- name:' .github/workflows/ci.yml` | **34** |
| manifest | `tools.verify_evidence_manifest` | `Evidence is intact.`, 95 entries |
| tag | API `git/tags/d9deb7f…` | object `d9deb7f…` → `b2dda33…`, tagger `2026-10-20T12:56:35Z` |
| release | API `releases/424060629` | four assets, published `2026-10-26T09:35:44Z` |

`V11_PROMPT.md` measures **168 total / 119 prose** by the heading-span rule V7 §8 uses (prose
counts every non-blank line that is not a heading and not a table row). That is a reference,
reported, not a gate; 431 remains the only hard bound. It exceeds V6–V10's 146 / 88, 154 / 98,
161 / 107, 164 / 112 and 161 / 109, and Phase 5 names the sections that grew.

### 4. What the unit carries, and what it excludes

**Carries.** The harness redesign in `V11_PROMPT.md` §4: the sweep runs in a detached worktree
outside the checkout, writes a machine-readable verdict outside the tree, and the ceiling gate reads
that verdict. One new CI job, its steps, the lane-contract row, the two lane-bearing documents, the
command annotation in `docs/interview_defense.md`, the falsification tests for the new reading, the
ceiling row's corpus and verdict text, and this series' two files.

**Excludes, with the reason each is excluded.**

1. **C — the declarative re-run of the evidence chain.** `V3_PROMPT.md`'s K5 row says `Never.` for
   the release, its tag and its four assets; a re-run would move the 95-entry manifest and the
   release asset set. This is not a question of approval strength, and no unit in this series
   touches it.
2. **D1 promoted to a CI gate.** The ancestry reading stays checkable and ungated. Promoting it
   would need a full-history checkout in the lane that adjudicates it, and `V10_PROMPT.md` §6 item 4
   says not to promote it without solving that; B1 does not require it.
3. **The installed-surface vantage.** `installed_user_identity_mismatch` stays `SKIP`: it needs a
   second environment on the runner, which is a different harness and a different finding. V11
   touches only the sweep.
4. **A new plant, guard or ceiling key.** The plant list stays at 195 and every anchor keeps
   resolving. The falsification of the new reading is a pytest guard with forged verdicts, declared
   in `tests/python/test_mutation_suite.py`, not a plant.
5. **Any earlier prompt or ledger.** `V6_PROMPT.md` §4 is quoted, not amended: the reversal is
   declared here, in Phase 0, which is the form §4 itself requires.
6. **Tag, release, pin, manifest, paper.** Unmoved; the check is that they did not move.
7. **A third push.** Two, named below.

### 5. The two pushes

1. **First push** carries Phase 0, the implementation and the Phase 5 report. Its CI is read from
   the API and attributed in the terminal entry.
2. **Second push** carries the terminal entry only. Its CI is read after the push, attributed in the
   session handoff, and its census line is quoted there.

No outcome is stated here for a push that has not happened.

---

## Phase 5 — 2026-11-13, the report and the archival confirmation

Every reading below was taken at `c9b46d2aad44b043ea2ff4918db62222cc85eb3c` unless it names another
revision. The series is five commits: `825768a` (Phase 0), `b30168b` (the harness, the lane and the reading),
`92e3af8` (the falsification folded into an existing guard so no documented test count moved),
`fa02ec2` (the lane installs the oracles its guards read) and `c9b46d2` (the claim census gold moves
with the fifth CI job).

### 1. Evidence ledger

| id | verdict | probe | closing commit |
|---|---|---|---|
| B1 — the sweep's vantage is development-only | **fixed** | `.github/lane_contract.md` reads `executed` for `quantrisk.verification.runner`, naming `mutation-census :: Run every declared plant in the worktree`; `--reading lanes_documented_vs_executed` prints `gap 0`, `executed 6`, `declared 8`, every mismatch class empty | `b30168b` |
| B1a — the verdict lived only in a transcript | **fixed** | `runner --verdict-out` writes `quantrisk-sweep-verdict/1`; `--check-ceilings` with `QUANTRISK_SWEEP_VERDICT` set prints `ok plants_not_rejected_by_their_guard: 0 against a ceiling of 0` | `b30168b` |
| B1b — "the sweep no longer touches tracked files" was a claim | **fixed** | `--watch-checkout` records the evaluated checkout's `git status --porcelain` before and after; the verdict carries both; a non-empty either side adds one to the key and fails the step with `watched-checkout-was-written` | `b30168b` |
| B1c — the new reading had no falsification | **fixed** | the census block in `test_the_status_table_only_calls_a_case_caught_when_every_step_fired` exercises five forgeries (escaped plant, early stop, drifted declaration, written checkout, malformed json) and one absence | `b30168b`, `92e3af8` |
| B1d — the lane ran in the wrong environment | **fixed** | a plain `uv sync` collects 491 tests in a fresh worktree instead of 560, so 14 plants whose guard counts them could not redden (`181/195` at `92e3af8`); `uv sync --frozen --extra oracles` makes the same tree collect 560 and the same plant `caught` | `fa02ec2` |
| C — the evidence chain re-run | **rejected** | `V3_PROMPT.md`'s K5 row: `Never.` for the release, its tag and its four assets; a re-run moves the 95-entry manifest | — |
| D1 — the ancestry reading as a CI gate | **rejected for this unit** | needs a full-history checkout in the lane that adjudicates it; B1 does not require it | — |
| `installed_user_identity_mismatch` | **rejected for this unit** | needs a second environment on the runner; a different harness and a different finding | — |

### 2. Liveness table, re-evaluated at `c9b46d2`

| id | claim | verdict | reading |
|---|---|---|---|
| N1 | every ceiling key is measured or honestly skipped | **ACTIVE** | 15 keys, 13 `ok`, 2 `SKIP`, 0 `FAIL` on the lint vantage; 14 `ok`, 1 `SKIP` on the census vantage |
| N2 | the lane contract agrees with both enumerations | **ACTIVE** | `gap 0`; `declared 8`, `documented 8`, `executed 6`; every mismatch list empty |
| N3 | a dev-only row carries a reason | **ACTIVE** | the runner row moved to `executed`; `build_evidence_manifest` and `build_report` keep theirs |
| N4 | no silence by count | **ACTIVE** | `with_extras_census gap 0`, 19/19 members; `docs_rederivation gap 0` |
| N5 | the pin is a guard | **ACTIVE** | `pinned_revision 17df062040b8`, `pin_holds true`, `gap 0`, `matches_tip false` |
| N6 | the formatter corpus is two-sided | **ACTIVE** | `reported_total 246`, `tracked_but_not_walked []`, `walked_but_not_tracked []` |
| L7 | every declared plant is rejected by its guard | **ACTIVE, and now runner-side** | `195/195 planted defects were rejected by their guard.` at `c9b46d2`, wall 1449.49 s, exit 0; the verdict records `declared 195 / ran 195 / caught 195 / non_caught []`, every status `caught`, and `checkout_status_before`/`after` both `''` |
| K5 | the published chain is a historical object | **ACTIVE** | tag, release and manifest re-read below with equal values |

### 3. The ceilings file's final state

The file still declares 15 keys. Two changed for this unit: `plants_not_rejected_by_their_guard`
gained a runner-side corpus and a four-way `can_fail_because`, and its `note` records the reopening.
`may_be_unmeasured` stays `true`, because the lint vantage genuinely does not run the lane: printing
`0` there would be a claim about a census it did not take. `installed_user_identity_mismatch` is
untouched, including its `max 0` and its corpus.

### 4. The deliberately-not-done list

1. **C is not run.** K5 forbids replacing a published asset, and a re-run would move the 95-entry
   manifest and the release asset set. This is not an authorisation question.
2. **D1 is not promoted.** The ancestry reading stays checkable and ungated; `V10_PROMPT.md` §6 item
   4 says not to promote it without solving the shallow checkout, and this unit does not.
3. **`installed_user_identity_mismatch` stays `SKIP`.** It needs a second environment on the runner.
4. **No plant was added.** The list stays at 195 and every anchor resolves; the falsification of the
   new reading is the census block in an existing test, which keeps the collected count at 560 and
   the paper's counts unmoved.
5. **No earlier prompt or ledger was edited.** `V6_PROMPT.md` §4 is quoted, not amended: Phase 0 is
   the form that section requires for a reversal.
6. **`docs/reproducibility.md` was not touched.** It never claimed the sweep, so adding it would
   move the lane contract's `claimed_by` set for no reading.
7. **The report PDF was not rebuilt.** `tools.build_report` stays dev-only; no number the paper
   cites moved, because the test count did not.
8. **The lane's environment is part of the reading.** A fresh worktree synced without the `oracles`
   extra collects 491 tests, and 14 plants whose guard counts them cannot redden. The lane installs
   the extra; a V12 that removes it pays those 14 again.
9. **No tag movement, no release asset replacement, no third push.**

### 5. Premises audit

1. **The published chain is frozen.** *Final reading:* tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`; release `424060629` with four assets sized
   2,978 / 55,780 / 145,672 / 1,005,786 bytes; manifest 95 entries and `Evidence is intact.`
   **Closed**; no asset was replaced.
2. **The pin is a guard.** *Final reading:* `artifact_revision 17df062040b8`,
   `pinned_revision 17df062040b8`, `pin_holds true`, `gap 0`, `matches_tip false`. **Closed.**
3. **The two `SKIP` keys hold only while their preconditions are re-read.** *Final reading:* on the
   lint vantage both print `precondition absent` with their corpus; on the census vantage
   `plants_not_rejected_by_their_guard` is measured and `installed_user_identity_mismatch` still
   skips. **Closed, with the residual named.**
4. **No clock is inherited.** `V10_LEDGER.md` §6 item 7 is quoted as a reading at `3725dfa`; V11
   added a lane, not a model.

### 6. Series handoff — what a V12 must contain

1. **The sweep now has a runner-side lane.** Do not describe it as development-only again; the row in
   `.github/lane_contract.md` is `executed` and names the job and step.
2. **Two vantages exist for one key.** `plants_not_rejected_by_their_guard` is `SKIP` in `lint` and
   measured in `mutation-census`; a report that quotes one number without the vantage is wrong.
3. **The census lane costs what it costs.** It configures and builds the C++ test target in the
   worktree before it sweeps; a V12 that adds a plant pays that build and the extra plant.
4. **`installed_user_identity_mismatch` is the last development-only key.** It needs a second
   environment on the runner, which is a harness of its own.
5. **D1 remains checkable and ungated.** Promoting it still needs a full-history checkout in the
   lane that adjudicates it.
6. **C remains refused under K5.**
7. **A new scope unit still needs a new verbatim approval.** `启动 V11，只做 B 项` is spent.

### 7. Per-lane verification table

| Lane | Command | Revision | Environment | Verdict |
|---|---|---|---|---|
| static checks | `ruff check .`, `ruff format --check .`, `mypy` | `92e3af8` | development, deep clone | green |
| formatter census | `--reading formatter_census` | `92e3af8` | development | 246/246, both differences empty |
| ceilings (lint vantage) | `--check-ceilings` | `92e3af8` | development | 15 keys, 13 `ok`, 2 `SKIP`, 0 `FAIL` |
| ceilings (census vantage) | `--check-ceilings` with the lane verdict | `92e3af8` | development, verdict from the isolated worktree | `plants_not_rejected_by_their_guard: 0` |
| mutation census | `runner --all --watch-checkout --verdict-out` | `c9b46d2` | detached worktree, oracles installed, C++ target built there | `195/195`, 1449.49 s, verdict clean, watched checkout clean before and after |
| lane contract | `--reading lanes_documented_vs_executed` | `92e3af8` | development | `gap 0` |
| docs re-derivation | `--reading docs_rederivation` | `92e3af8` | development | `gap 0`, `mismatches []` |
| evidence chain | `tools.verify_evidence_manifest` | `92e3af8` | development | `Evidence is intact.` |
| Python tests | `pytest -q` | `c9b46d2` | development, oracles installed | `1 failed, 559 passed in 131.91s`; the failure is the sandbox bytecode plant, named and not silenced |
| CI, first push | all five jobs | `c9b46d2` | ubuntu-latest / macos-15 | attributed in the terminal entry |

### 8. Archival confirmation

Filled after the second push: `HEAD` equal to `origin/main` and to the platform's `main`, tree clean,
every commit the series created proven an ancestor of the remote, both runs attributed from the API,
registers and documents re-counted against their artifacts, and no stray instrument tracked or left
on disk.

