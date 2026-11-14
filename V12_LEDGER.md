# V12_LEDGER.md — the cross-session state of the V12 series

V12 is a single-unit series with one finding, C1: `installed_user_identity_mismatch` is the last
ceiling key the repository skips, so the installed surface has never been proved on a runner. This
file carries the Phase 0 entry, the implementation record, the Phase 5 report and the terminal entry.
`V12_PROMPT.md` is the rail set; where the two disagree, the prompt wins.

---

## Phase 0 — 2026-11-14, the scope unit, its baseline, and what it excludes

### 1. The approval, verbatim

> 继续按你此前提出的思路和建议方案执行，我已全部授权，无需再次确认。请持续推进剩余工作，保持与既定方向一致，并在关键节点简要说明已完成的内容、当前进展及下一步计划；如遇需我决策的分歧，再单独提出。

It points at the handoff V11 left: of the three items that remained, C is refused by K5 and D1 needs
a full-history checkout in the lane that adjudicates it, so the one item it can name is the last
development-only key. V12 takes that item and nothing else.

### 2. Revision and vantage

- **Revision.** `6eda1fa29ccf537327a0e62bbd6f1afb1a84d325`, the V11 fourth push. `HEAD`,
  `origin/main` and the platform's `main` all read it; `git status --porcelain` is empty.
- **Baseline vantage.** development machine, deep clone, wheel built from the tree and installed
  into `/tmp/qr-v12-venv` — an environment outside the checkout, which is the vantage the key needs
  and the one no runner had.
- **The finding taken.** C1: the ceilings file prints 15 keys, 14 `ok`, 1 `SKIP`, and the skip is
  `installed_user_identity_mismatch`. Its `corpus` names a second environment as the missing
  precondition, so L8 — the import resolving inside the environment it was installed into — has
  never been gated on a runner. A wheel whose import resolved into the working tree would be green.

### 3. Re-measured baseline at `6eda1fa`

| Reading | Command | Value |
|---|---|---|
| static checks | `ruff check .` | `All checks passed!` |
| formatter | `ruff format --check .` | 246 files already formatted |
| types | `mypy python/quantrisk tools` | `Success: no issues found in 74 source files` |
| ceilings | `--check-ceilings` | 15 keys: 14 `ok`, 1 `SKIP`, 0 `FAIL` |
| the skip | same | `installed_user_identity_mismatch`, `precondition absent` |
| plants | `runner --list` | 195 |
| collection | `pytest --collect-only -q` | 560 tests collected |
| lanes | `--reading lanes_documented_vs_executed` | `gap 0`, 8 declared / 8 documented / 6 executed |
| manifest | `tools.verify_evidence_manifest` | `Evidence is intact.`, 95 entries |

`V12_PROMPT.md` measures **144 total / 97 prose** by the heading-span rule; 431 remains the only
hard bound.

### 4. What the unit carries, and what it excludes

**Carries.** An `installed-surface` job that builds the wheel from the pushed tree, creates an
environment under `$RUNNER_TEMP`, installs only that wheel, runs
`tools.verify_installed_surface --json-out`, and adjudicates the key on the same runner; a reading
and a metric in `tools/inventory_orphan_code.py`; the key's `corpus` and `can_fail_because`; the lane
contract's row and the paragraph in `CONTRIBUTING.md`; one falsification block; this
series' two files.

**Excludes, with the reason each is excluded.**

1. **C — the declarative re-run of the evidence chain.** K5 says `Never.` for the release, its tag
   and its four assets; a re-run moves the 95-entry manifest.
2. **D1 promoted to a CI gate.** The ancestry reading stays checkable and ungated; it needs a
   full-history checkout in the lane that adjudicates it, which is its own unit.
3. **The sweep vantage.** V11 closed it; V12 neither reopens nor re-measures it.
4. **A new plant, guard or ceiling key.** The list stays at 195 and the key count stays at 15; the
   falsification is a forged-verdict block inside an existing test, so the collected count stays 560.
5. **Any earlier prompt or ledger.** `V6_PROMPT.md` §4 and `V11_LEDGER.md` are quoted, not amended.
6. **Tag, release, pin, manifest, paper.** Unmoved; the check is that they did not move.

### 5. The pushes

1. **First** carries Phase 0, the implementation and the Phase 5 report; its CI is attributed in the
   terminal entry.
2. **Second** carries the terminal entry only; its CI is attributed in the session handoff.
3. **Reserved** for repairing a red run of either, under the same standing approval. A third push is
   used only if a run is red, and the repair is named in that push's commit.

---

## Phase 5 — 2026-11-14, the report and the archival confirmation

Every reading below was taken at `6eda1fa` unless it names another revision.

### 1. Evidence ledger

| id | verdict | probe | closing commit |
|---|---|---|---|
| C1 — the installed-surface key cannot fail on a runner | **fixed** | `.github/lane_contract.md` reads `executed` for `tools.verify_installed_surface`, naming `installed-surface :: Prove the installed surface`; `--reading lanes_documented_vs_executed` prints `gap 0`, 9 declared / 9 documented / 7 executed | first push |
| C1a — the probe had no machine-readable verdict | **fixed** | `--json-out` writes `quantrisk-installed-surface/1` with the five readings, the environment root and the checkout | first push |
| C1b — the key was hard-coded to `None` | **fixed** | `installed_surface_verdict()` reads the lane's json; `--check-ceilings` with it prints `ok installed_user_identity_mismatch: 0`, while the lint vantage still prints `SKIP` | first push |
| C1c — the new reading had no falsification | **fixed** | three forged verdicts in `test_the_status_table_only_calls_a_case_caught_when_every_step_fired`: a missing reading, an import naming the checkout, and a non-zero exit | first push |
| D1 promoted to a gate | **rejected for this unit** | needs a full-history checkout in the lane that adjudicates it | — |
| C — the evidence chain re-run | **rejected** | K5 says `Never.` | — |

### 2. Liveness table, re-evaluated at `6eda1fa`

| id | claim | verdict | reading |
|---|---|---|---|
| N1 | every ceiling key is measured or honestly skipped | **ACTIVE** | 15 keys; on lint 14 `ok` / 1 `SKIP`; on the installed vantage 15 `ok` / 0 `SKIP` |
| N2 | the lane contract agrees with both enumerations | **ACTIVE** | `gap 0`; 9 declared, 9 documented, 7 executed; every mismatch list empty |
| N3 | a dev-only row carries a reason | **ACTIVE** | `tools.build_evidence_manifest` and `tools.build_report` keep theirs; the probe's row is `executed` |
| N4 | no silence by count | **ACTIVE** | `with_extras_census gap 0`, 19/19 members; `docs_rederivation gap 0` |
| N5 | the pin is a guard | **ACTIVE** | `pinned_revision 17df062040b8`, `pin_holds true`, `gap 0` |
| N6 | the formatter corpus is two-sided | **ACTIVE** | two-sided after the two new Markdown files are tracked |

### 3. The ceilings file's final state

15 keys, unchanged in count. One row moved: `installed_user_identity_mismatch` gained a corpus that
names the lane and a three-way `can_fail_because`, and its `note`-bearing history stays inside that
text. `may_be_unmeasured` stays `true`, because the lint vantage does not run the lane: printing `0`
there would be a claim about a probe it did not run.

### 4. The deliberately-not-done list

1. **C is not run.** K5 forbids replacing a published asset.
2. **D1 is not promoted.** It needs a full-history checkout in the adjudicating lane.
3. **The sweep vantage is not re-measured.** V11 closed it; V12 quotes its census, not re-runs it.
4. **No plant was added.** 195 stays 195; the falsification is a forged-verdict block.
5. **No collected test was added.** 560 stays 560, so no documented count and no paper figure moves.
6. **No earlier file was edited.** `V6_PROMPT.md` §4 and `V11_LEDGER.md` are quoted.
7. **No tag movement, no release asset replacement.**

### 5. Premises audit

1. **The published chain is frozen.** Tag object `d9deb7f…` → `b2dda33…`; release `424060629` four
   assets sized 2,978 / 55,780 / 145,672 / 1,005,786; manifest 95 entries and `Evidence is intact.`
   **Closed.**
2. **The pin is a guard.** `artifact_revision 17df062040b8`, `pin_holds true`, `gap 0`. **Closed.**
3. **One key was development-only.** *Final reading:* it is measured from the lane's verdict and
   still `SKIP` in lint. **Closed**, with the two vantages named.
4. **The sweep vantage stays closed.** `runner --list` still 195 and the reconciliation unchanged.
   **Closed.**

### 6. Series handoff — what a V13 must contain

1. **Two keys now have two vantages.** `plants_not_rejected_by_their_guard` and
   `installed_user_identity_mismatch` are `SKIP` in `lint` and measured in their own lanes; a report
   that quotes one number without the vantage is wrong.
2. **`installed-surface` costs a wheel build and a study run**, and it fails on the wheel, not on the
   checkout — do not move it into `build-and-test`.
3. **D1 remains the only un-gated reading**, and promoting it still needs a full-history checkout in
   the lane that adjudicates it.
4. **C remains refused under K5.**
5. **Every remaining railing is now measured on a runner.** A V13 must justify its scope against
   `V5_PROMPT.md` §1 rather than invent machinery.

### 7. Per-lane verification table

| Lane | Command | Revision | Environment | Verdict |
|---|---|---|---|---|
| static checks | `ruff check .`, `ruff format --check .`, `mypy` | `6eda1fa` | development | green |
| formatter census | `--reading formatter_census` | `6eda1fa` | development | two-sided, counts in §3 |
| ceilings (lint vantage) | `--check-ceilings` | `6eda1fa` | development | 15 keys, 14 `ok`, 1 `SKIP` |
| ceilings (installed vantage) | `--check-ceilings` with the lane verdict | `6eda1fa` | development, wheel in `/tmp/qr-v12-venv` | `installed_user_identity_mismatch: 0` |
| installed surface | `verify_installed_surface --json-out` | `6eda1fa` | clean venv outside the checkout | identity under the environment; `run --list` 19 tasks; `validate` 7 passed; `mc_speed` wrote `monte_carlo_speed.json`; `pricing_grid` refused naming what it needed |
| lane contract | `--reading lanes_documented_vs_executed` | `6eda1fa` | development | `gap 0` |
| Python tests | `pytest -q` | `6eda1fa` | development | `1 failed, 559 passed in 167.95s`; the failure is the sandbox bytecode plant, named and not silenced |
| CI, first push | all six jobs | first push | ubuntu-latest / macos-15 | attributed in the terminal entry |

### 8. Archival confirmation

Filled after the second push: `HEAD` equal to `origin/main` and to the platform's `main`, tree clean,
every commit the series created proven an ancestor of the remote, both runs attributed from the API,
and no stray instrument tracked or left on disk.

---
