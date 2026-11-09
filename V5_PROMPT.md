# V5_PROMPT.md — QuantRisk++ V5: Vantage, Provenance, and the Written Rails

> **A prompt for a coding agent.** V1 is `PROJECT_SPEC.md`, V2 is `REFACTOR_PROMPT.md`, V3 is
> `V3_PROMPT.md` and V4 has no written prompt: it ran on inherited rails with one approval per
> unit, recorded in `V4_LEDGER.md`. V5 exists because V4's Phase 5 report named seven things a
> gate cannot yet see. Two of them are the same problem seen from two sides — a proof produced in
> one vantage being cited as though it verified another. This document is the written rail set V4
> lacked. It is not a licence to start work: §6 requires a fresh, verbatim, case-by-case approval
> for every scope unit, including the one that edits this file.
>
> **How to use it.** Read it whole from disk. `V5_LEDGER.md` holds the readings; this file holds the
> rules. A number here is a reading at `eb75b32` and is re-measured in every Phase 0 (§7). Where
> this file and a fresh reading disagree, the reading wins and the disagreement is registered as a
> finding against this document.

- [0. Series status, premises and termination](#0-series-status-premises-and-termination)
- [1. Role and mission](#1-role-and-mission)
- [2. Non-goals and priced locks](#2-non-goals-and-priced-locks)
- [3. Facts Protocol](#3-facts-protocol)
- [4. Lanes and policy assets](#4-lanes-and-policy-assets)
- [5. The seven candidate findings](#5-the-seven-candidate-findings)
- [6. One scope unit per approval](#6-one-scope-unit-per-approval)
- [7. Phase 0, Phase 5, Definition of Done](#7-phase-0-phase-5-definition-of-done)
- [8. Size ratchet](#8-size-ratchet)

---

## 0. Series status, premises and termination

V1–V3 are closed and are historical records, not instructions to be re-executed. V4 closed at
`eb75b3277d28307f29fe9fc16b86e24d3f96ba24` with `194/194 planted defects were rejected by their
guard.` captured at `a74cf9a`, fourteen ceiling keys (twelve `ok`, two `SKIP`) and four green CI
jobs per tip. V5 inherits that state and changes none of it in its launch unit.

**Series termination condition.** V5 is justified by three measured premises, each re-derived from
the Phase 0 readings in `V5_LEDGER.md`. Re-measure all three before touching anything in §7; if a
fresh measurement contradicts one, stop, write the contradiction into the ledger, and re-scope with
the maintainer. A premise that no longer holds voids the finding built on it.

1. **Two declared gates have a precondition the runner cannot supply.**
   `plants_not_rejected_by_their_guard` and `installed_user_identity_mismatch` both print
   `SKIP / precondition absent`. The first has a real proof (`194/194`, clean tree, captured
   summary) that lives only in the development vantage; the second has a proof inherited from V3
   §6 at `d502a61` that V4 did not re-run. A key that cannot fail on the runner that evaluates it
   is a declaration, not a gate.
2. **Two artifacts describe a vantage other than the tip being verified.**
   `--reading with_extras_census` reads a committed `suite_run.json` at revision
   `17df062040b8`; the benchmark job reads a freshly generated one and prints `revision:
   ad03b890da5b **(working tree was dirty at run time)**`. Both print `gap: 0`, because neither
   reading checks the artifact's age or the dirty condition. `working_tree_dirty` is set at
   `tools/run_benchmark_suite.py:1075` and consumed at lines 943 and 952, with the producer
   undiagnosed.
3. **The process has no written rail set of its own.** V4 admitted as much in §4 item 7: seven
   case-by-case approvals, no prompt, inherited §14–§16. A series that changes a policy asset
   again should state its premises, lanes and termination condition in a file.

**Termination** requires: all three premises closed with a reading or carried open with a named
reason; each of the seven §5 findings fixed, rejected with evidence, or in the deliberately-not-done
list; a Phase 5 report with its eight deliverables and archival confirmation; and CI attributed for
every commit in the V5 range. V5 does not terminate by dissolving a premise into prose: a SKIP
that stays SKIP must be named and its vantage stated.

## 1. Role and mission

Close the distance between what a proof verifies and what a report says it verifies, in two
directions: toward the runner that must be able to fail, and toward the revision a committed
artifact claims to describe. Do not add models, do not rewrite correct code, do not manufacture
new gates to replace ones that are merely inconvenient. Every change must leave the repository more
checkable than it found it, with a named reading that can redden it.

## 2. Non-goals and priced locks

- **K5 holds.** No tag movement, no force-push, no history rewriting, no replacing a published
  `v1.9.0` release asset. If the report is regenerated it is a new artifact inside the repository.
- **Locked paths.** `cpp/`, `bindings/`, `CMakeLists.txt`, `PROJECT_SPEC.md`,
  `REFACTOR_PROMPT.md`, `V3_PROMPT.md`, `evidence/manifest.json` and `paper/` are not edited
  without a separate approval recorded verbatim; `PROJECT_SPEC.md`, `REFACTOR_PROMPT.md` and
  `V3_PROMPT.md` need one under `V3_PROMPT.md` §14 as well.
- **No gate weakened.** No tolerance raised, no test deleted, no `skip`/`xfail` added to reach
  green, no `may_be_unmeasured` added to a key that currently has none. A new ceiling key may be
  an **addition** with `max: 0` and no `may_be_unmeasured`, so a broken instrument fails instead
  of skipping (N5, N8).
- **No fabricated fallback.** A missing artifact yields `available: False`, not zero. A missing
  proof is named, not replaced by a proxy (§15 item 8).
- **No document repainting.** A figure is re-derived or the sentence is removed; a document is
  never edited to match a claim it cannot support (§15 item 7). The five living documents are
  re-derived by `--reading docs_rederivation` in the same commit as any move.

## 3. Facts Protocol

1. **Fresh reading wins.** Every number in a ledger entry comes from a tool run in that unit, at
   the revision named in the entry. A reading quoted from an earlier entry without being
   re-measured is an inherited claim and must be labelled as such.
2. **Unknown is not green.** An interrupted command, a background job that returns nothing, a
   `steps: 0` metadata response or a cancelled run is `unknown`: re-run it, read its log, or name
   it as unverified. `cancel-in-progress` makes a tip that never executed look recent; a later run
   on a different tree is not that tip's verification (`V3_PROMPT.md` §15 item 5, §14 last
   bullet).
3. **Attribute every CI reading to the run, attempt, runner and environment that produced it.**
   Name the four jobs, their step counts and their conclusions. A run with a cancelled or 0-step
   job is not a green verification of that job's lanes (§16.8).
4. **Name the vantage.** A development-vantage sweep, a locally installed wheel, a runner job and
   a committed artifact are four different environments. No reading from one is described as
   verification on another. Any per-lane table names revision **and** environment (N12).
5. **Name the population of every count.** "No X" from a grep must enumerate which corpora the
   query walked, including the ones the instrument excludes by construction (§15 item 6, N4).
   Every declaration is compared with the artifact it declares, in both directions (N5).
6. **No entry before the tool reports it.** The ledger records what was run, what it printed and
   what was decided — in that order. An intended reading is not a result (`V3_PROMPT.md` §16
   item 9).

## 4. Lanes and policy assets

The Phase 0 readings at `eb75b32` are: 19 registry tasks, 19 suite members, 194 declared plants,
14 ceiling keys, 95 manifest entries, 232 formatter-tracked files, 560 / 491 pytest nodes, 32
named CI steps, five living documents with seven printed claims, and four CI jobs per tip. These
numbers are a baseline, not a constant: adding `V5_LEDGER.md` and this file moves the formatter
corpus to 234, and the implementation entry re-measures it with both differences empty.

The lanes are the ones `.github/lane_contract.md` declares and `--reading
lanes_documented_vs_executed` compares: `quantrisk run`, `quantrisk validate`,
`tools.inventory_orphan_code` (three steps), `tools.run_benchmark_suite` and
`tools.verify_evidence_manifest`. The three dev-only commands carry reasons in the contract. The
local static gates (`ruff check`, `ruff format --check`, `mypy`), the manifest verifier, the
collector readings, the full `pytest -q` and the full mutation sweep are real lanes with a vantage
that must be named in any per-lane table.

Every V5 change to a guard, policy asset or lane must, in the same commit: extend an existing pytest
guard rather than duplicate it where the counted pair can stay 560 / 491 (a change to that pair is
allowed only with the delta and its reason printed in the Phase 0 and Phase 5 entries); add or
re-key a plant whose guard is behavioural or textual as appropriate, with the plant's verdict
captured by a targeted sweep; re-derive any printed claim that moved; and leave
`--check-ceilings`, `--reading docs_rederivation`, `--reading lanes_documented_vs_executed`,
`--reading with_extras_census` and the manifest verifier at their declared ceilings. A full
194-plant census is required at the final V5 tip on a clean tree (`V3_PROMPT.md` §16 item 5), not
at every intermediate one.

## 5. The seven candidate findings

These are V4 §7's handoff items, re-measured in `V5_LEDGER.md`'s Phase 0 entry. Each carries a
`check:` predicate that must be run at the commit that closes it. They are candidates, not a queue:
which one a unit takes is decided in that unit's Phase 0, and taking one does not approve the rest.

| id | finding | `check:` |
|---|---|---|
| F1 | No written V5 prompt | this file exists, states premises, lanes, rails and termination; §6's approval rule is written down and was followed by the launch unit |
| F2 | The sweep's vantage is undecided | either a runner-executable sweep makes `plants_not_rejected_by_their_guard` stop SKIPping without weakening `194/194`, or a ledger entry records explicitly that the proof stays development-only; the key's declaration and its reason agree |
| F3 | `working_tree_dirty` is undiagnosed | the producer at `tools/run_benchmark_suite.py:1075` is traced and the line's appearance at the V5 tip is explained with a reading, or the item is named in the deliberately-not-done list with its reason |
| F4 | The committed `suite_run.json` is not pinned to HEAD | a reading compares the artifact's `revision` with the tip being verified and can redden on mismatch; both the lint job's committed artifact and the benchmark job's fresh one are attributed to their own vantages |
| F5 | The installed-surface proof was not re-run | a clean-venv wheel reading with an asserted module identity exists at a V5 tip, or the SKIP is carried with its precondition named and the inherited V3 §6 reading marked unverified |
| F6 | `tools/generate_shim_stubs.py` and the two SKIP keys have no decision | each is fixed, rejected with evidence, or named in the deliberately-not-done list; `runtime_reachability` still reports `reached_by_neither 0` and the difference between importability and use is stated |
| F7 | No change to the published asset set | the platform's tag object, dereferenced commit, release timestamp and four asset timestamps are re-read at the final tip and match `V5_LEDGER.md`'s Phase 0 readings |

## 6. One scope unit per approval

The unit is named in the session's opener. Continuing "one more lane" past its boundary is what
breaks multi-session documents: the next session inherits a ledger whose entries match no single
baseline. Cross-session state lives in `V5_LEDGER.md`, never in chat history.

- Outward actions — push, PR, release, issue, comment — and edits to `PROJECT_SPEC.md`,
  `REFACTOR_PROMPT.md` or `V3_PROMPT.md` need the maintainer's approval **for that case**,
  recorded verbatim in that unit's Phase 0 entry (`V3_PROMPT.md` §14). An approval for this launch
  unit covered its two pushes and no third; it is not the authority for V5-02. A risky action taken
  twice with approval is not approved the third time; ask when the scope changes.
- A Phase 0 entry states the revision, vantage, re-measured baseline, the finding taken, what the
  unit excludes, the approval verbatim, the number of pushes and what each carries. No reading is
  written before the tool reports it.
- Near the close of every unit except the last, the ledger's terminal entry records the
  implementation tip's CI with its run, attempt, runner and step counts. The terminal commit's own
  CI is read after the second push and reported in the session handoff, not written into the file
  whose content is fixed before that push.
- Editing this prompt is itself a scope unit and needs its own verbatim approval. No unit may
  amend this section to widen its own authority.

## 7. Phase 0, Phase 5, Definition of Done

**Phase 0** re-counts the archive against the tip that is actually pushed, names the vantage and
the platform's tag/release state, re-measures the three premises, chooses one finding, and records
the approval. It ships as its own commit before any source file is touched.

**An implementation unit** ships the change, its guard, its plant and its readings in one named
commit, then the terminal entry attributing that tip's CI. Both pushes are attributed. The counted
pair, the plant total, the ceiling keys and the formatter corpus are re-measured after the change
and their deltas printed.

**Phase 5** delivers, assembled from `V5_LEDGER.md` plus a fresh reading of the repository, the
eight `V3_PROMPT.md` §12 deliverables: an evidence ledger; the liveness table re-evaluated at the
final tip; the ceilings file's final state with review notes; an honestly non-empty
deliberately-not-done list; a premises audit; a series handoff; a per-lane verification table with
revision **and** environment for every lane; and an archival confirmation. That confirmation
requires a clean tree with `HEAD` equal to `origin/main`, every V5 commit proven an ancestor of the
remote, CI attributed for every commit in the range with cancelled runs named as cancelled,
registers and documents re-counted against their artifacts, tags/releases/assets re-read from the
platform, and no stray instrument tracked or left on disk.

**Definition of Done.** All three premises re-measured; each of F1–F7 fixed, rejected with evidence
or in the deliberately-not-done list; a full sweep's own summary line captured at the final
revision on a clean tree; every document quoting a moved count re-derived in the same commit; the
Phase 5 report and archival confirmation committed and pushed; CI read for every commit in the
range; and every ledger entry recording what was run, what it printed and what was decided.

## 8. Size ratchet

`V3_PROMPT.md` §0 caps its prose sections (§1–§3, §6–§15) at 431 lines measured by heading span.
V5's prose sections (§1–§3, §6–§8) may not exceed that bound; this file is deliberately far below
it. Growth is allowed only in §5's finding table and §4's lane inventory, both of which scale
with the project. If a future revision needs more prose, it must first show which rule of this
version was never executed.
