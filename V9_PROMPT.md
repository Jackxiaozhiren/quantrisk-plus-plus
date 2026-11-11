# V9_PROMPT.md — the rails for the V9 series

V9 starts at `5ec3fabe4fa8c83584a50b3ab66b357ae13094e9`, the terminal entry of V8. It is a
**single-unit series** with one finding, D1. The maintainer named that unit explicitly; nothing in
this file widens it. Every number below is a reading taken at that tip, and every claim about an
earlier series is a pointer to the ledger or handoff that measured it. `V9_LEDGER.md` is the
cross-session state; this file is the rail set.

## 0. Status, premises and termination

**What is closed.** V1 is `PROJECT_SPEC.md` (historical, priced lock). V2 is `REFACTOR_PROMPT.md`
(terminated, `REFACTOR_LEDGER.md`). V3 closed its eight §12 deliverables, V4 the V3 carryover, V5
F1–F7, V6 G1–G6, V7 H1–H7 with H6 partial and named, and V8 H1–H6. None of those files is amended
by V9. `V8_LEDGER.md` Phase 5 §7 still prints `deferred` on the census row: that was true when the
report was written and, per the Facts Protocol, is not rewritten.

**Three premises, measured at `5ec3fab`.** If a fresh reading contradicts one, stop and write the
contradiction into the Phase 5 report before touching anything.

1. **The published chain is frozen.** `v1.9.0` is tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`; release `424060629` holds four assets created
   `2026-10-26T09:35:41Z`. `evidence/manifest.json` holds 95 entries and verifies intact.
2. **The pin is a guard, not a sentence.** `artifact_revision_gap` declares
   `pinned_revision 17df062040b8`; `artifact_revision` prints `gap 0`, `pin_holds true`,
   `matches_tip false` on the committed artifact and exempts a fresh upload naming the tip.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** Both are honest at this
   tip because their reasons are printed. V9 re-reads them before citing them.

**Termination condition.** V9 ends when D1 is fixed — a named, machine-readable attestation of
V8's literal-final-tip census is committed to the repository with its revision, vantage and
evidence limit stated, and is shown to redden against a forged revision and a forged count — when
the Phase 5 report and archival confirmation are committed and pushed, and when both pushes' CI
have been attributed from the API. V9 does **not** re-run the census: D1 fixes an existing reading,
and a new census at V9's own tip would reproduce the very deferral V8 §6 item 1 handed on.

## 1. What V9 inherits, and what it may not re-derive

`V8_LEDGER.md` Phase 5 §4 (ten deliberately-not-done items) and §6 (eight handoff items) are the
starting agenda. They are not a queue. The maintainer selected item D — freeze the final-tip census
into the repository — and excluded A (repairing `V7_PROMPT.md` §8), B (reopening the sweep vantage)
and C (a declarative re-run of the evidence chain). V9 takes no other item.

**Why D is possible now and was not in V8.** A file cannot contain the SHA of the commit that
contains it: writing the census result into `V8_LEDGER.md` would have created a new commit, so
`5ec3fab` would stop being the tip the reading names. V9 starts *above* `5ec3fab`. For V9 that
revision is an **ancestor**, not a self-reference, so a V9 file can name it, and git can verify the
claim. This is the whole mechanism; V9 invents no guard to obtain it.

V9 adds no guard, plant, ceiling key, CI step, lane, living document or artifact. It adds exactly
two tracked paths (`V9_PROMPT.md`, `V9_LEDGER.md`), both Markdown. `docs_rederivation` keeps its
five documents and `gap 0`; the formatter corpus moves from 240 to 242 with both differences still
empty, and Phase 5 prints that delta.

## 2. Facts Protocol

1. **A reading is a command and its output, at a revision.** Nothing enters a ledger entry without
   both.
2. **No outcome before the tool reports it.** A push, a run and a job are `unknown` until the API
   says otherwise; `gh run watch` returning 0 on a transport-layer success is not a verdict.
3. **Attribute every CI reading to its run, attempt, runner and environment.**
4. **A historical reading is not rewritten.** `V8_LEDGER.md` §7's `deferred` row stays as printed.
   V9's attestation is a *new* row about a *past* revision, and says so.
5. **A guard that cannot redden is not a guard.** D1 carries a two-direction forged-input proof:
   a revision that is not an object or not an ancestor, and a count that disagrees with the
   runner's own `--list`. Both must be refused.
6. **State the evidence limit.** The 998-line census log was session-local scratch under `/tmp` and
   is no longer on disk. V9 fixes the *reading* (revision, command, exit code, line count, verdict
   distribution, summary line, tree state, vantage), not the log. It must not claim the log is in
   the repository or that the numbers are re-runnable from a tracked artifact. The sweep has no CI
   lane; this remains a development-side vantage.
7. **Every printed census verdict carries its vantage on the same line** (`development-side vantage;
   the sweep has no CI lane`), as `V8_LEDGER.md` §6 item 5 requires of any new document.

## 3. Lanes and policy assets at `5ec3fab`

| asset | reading |
|---|---|
| registry tasks / suite members | 19 / 19, `registry_parity` mismatch empty |
| plants | **195**; the last full census is `195/195` at `5ec3fab` (development-side vantage; the sweep has no CI lane) |
| ceiling keys | **15** — 13 `ok`, 2 `SKIP` |
| manifest | 95 entries, `Evidence is intact.` |
| formatter corpus | **240 / 240**, both differences empty |
| pytest nodes | 560 collected / 491 offline, `collection_errors 0` |
| named CI steps | **34** |
| readings at `gap 0` | `docs_rederivation`, `lanes_documented_vs_executed`, `with_extras_census`, `artifact_revision`, `formatter_census`, `registry_parity` |

The lanes are those `.github/lane_contract.md` declares, plus the local static gates, the manifest
verifier, the collector readings and the full `pytest -q`. The sweep and the installed-surface proof
are development-only by permanent decision (§4). Every lane in the Phase 5 table names its revision
and environment.

## 4. The sweep and installed-surface vantages stay closed

`V6_PROMPT.md` §4 made the sweep's development-only decision permanent; V7 §4 and V8 §4 kept it.
V9 performs no harness redesign, gives neither `SKIP` a runner-side verdict, adds no CI lane for
installed-surface proof, and does not promote the census verdict to a gate. D1 makes a *reading*
checkable against git and the runner's `--list`; it does not make the sweep reproducible on a
runner. Phase 0 states this before any file is touched.

## 5. The candidate finding

| id | finding | `check:` |
|---|---|---|
| D1 | V8's census at the literal final tip exists only in a session handoff and agent-local memory; `V8_LEDGER.md` §7 still says `deferred` | `V9_LEDGER.md` carries a machine-readable attestation naming `5ec3fab` as an ancestor, with the command, exit code, 998 lines, 195 `ok caught`, zero other verdict rows, the summary line verbatim, 0 dirty paths after recovery, the development-side vantage and the evidence limit. `git cat-file -e <rev>^{commit}` and `git merge-base --is-ancestor <rev> HEAD` both hold; the attestation's declared count equals `python -m quantrisk.verification.runner --list \| wc -l`. A forged non-object revision, a forged non-ancestor revision and a forged count are each refused by that same reading. `V8_LEDGER.md` is unchanged. |

Items A, B and C are refused with evidence in Phase 5 §4, not taken as findings. V9 has no D2.

## 6. One scope unit per approval

- **The maintainer's approval, verbatim.** `启动 V9，只做 D 项` (2026-11-11). This is a
  **single-unit** approval: it covers D1, the Phase 0 entry, the attestation, the Phase 5 report,
  the terminal entry, the two named pushes and their CI attribution. It is recorded verbatim in the
  V9 Phase 0 entry before any outward action. The V8 series-wide approval
  (`授权启动 V8，按你的建议推进剩余系列`) is spent and is not reused.
- **Not authorised by that sentence:** items A, B or C; editing any earlier prompt or ledger
  (`PROJECT_SPEC.md`, `REFACTOR_PROMPT.md`, `V3_PROMPT.md` … `V8_PROMPT.md`, `V3_LEDGER.md` …
  `V8_LEDGER.md`) or this file; a harness redesign that reopens §4; a declared re-run of the
  evidence chain; a new census at V9's own tip; a tag movement or release asset replacement; a new
  CI lane, plant, guard or ceiling key; or a third push. Any of those needs a new verbatim approval.
- Outward actions — push, PR, release, issue, comment — need the maintainer's approval for that
  case, recorded verbatim in that unit's Phase 0 entry. Within V9 the sentence above is that case
  for the two named pushes.
- A Phase 0 entry states the revision, vantage, re-measured baseline, the finding taken, what the
  unit excludes, the approval verbatim, the number of pushes and what each carries.
- The ledger's terminal entry records the implementation tip's CI with its run, attempt, runner and
  step counts. The terminal commit's own CI is read after the second push and reported in the
  session handoff.
- Editing this prompt is itself a scope unit and needs its own verbatim approval. No unit may amend
  this section to widen its own authority.

## 7. Phase 0, Phase 5, Definition of Done

**Phase 0** re-counts the archive against the tip that is actually pushed, names the vantage and
the platform's tag/release state, re-measures the three premises, chooses D1, states the exclusions
and records the approval. It ships as its own commit before any other file is touched.

**V9 has one implementation commit**: it carries the attestation and its verification reading; no
source, policy asset, test or workflow file moves. The first push carries that commit together with
Phase 0 and the Phase 5 report; the second carries the terminal entry. Both pushes are attributed
from the API.

**Phase 5** delivers the eight `V3_PROMPT.md` §12 items: an evidence ledger; the liveness table
re-evaluated at the report's tip; the ceilings file's final state with review notes; an honestly
non-empty deliberately-not-done list; a premises audit; a series handoff; a per-lane verification
table with revision **and** environment for every lane; and an archival confirmation requiring a
clean tree with `HEAD` equal to `origin/main`, every V9 commit proven an ancestor of the remote, CI
attributed for every commit, registers and documents re-counted, tags/releases/assets re-read from
the platform, and no stray instrument tracked or left on disk.

**Definition of Done.** All three premises re-measured; D1 fixed with its two-direction forged
proof; every document quoting a moved count re-derived in the same commit; the Phase 5 report and
archival confirmation committed and pushed; CI read for every commit in the range; and every ledger
entry recording what was run, what it printed and what was decided.

## 8. Size ratchet

`V3_PROMPT.md` §0 caps its prose sections at 431 lines measured by heading span, and that is V9's
only hard bound. V6 measured 146 / 88, V7 154 / 98 and V8 161 / 107; all three are **reported
reference figures, not gates**, because V7's attempt to enforce 88 as a soft cap produced a partial
finding rather than a shorter prompt. V9 adds no section beyond V8's eight, and its Phase 5 report
prints the measured total and prose lines beside those three figures so the growth is attributed
rather than hidden. If V9 exceeds 431 the series has failed its DoD; exceeding 107 is reported,
not failed.
