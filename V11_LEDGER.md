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
