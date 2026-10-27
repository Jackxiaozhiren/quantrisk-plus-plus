# V3_PROMPT.md — QuantRisk++ V3: The Advertised Surface, and the Process Lane

> **A prompt for a coding agent.** This repository has already absorbed its scripts into the package,
> already freezes its evidence, already polices its own prose. What it has not done is make the promises it
> publishes true for the person who installs it: `quantrisk run --list` advertises nineteen studies and four
> of them run from a wheel. And the machinery that audits the repository is itself unaudited in one specific
> way — every guard in the project reads the tree, so nothing notices a planned step that never happened, a
> command documented as a lane that no lane runs, or a declaration nobody compares with the measurement it
> declares.
>
> Your job is not to add models and not to rewrite anything that is correct. It is to close the distance
> between what this project says it delivers and what it delivers, in both directions: to the installed user,
> and to its own process.
>
> **Everything here is a law with a `check:` predicate that names the commit at which the predicate gets
> run**, a procedure you must execute, or a decision with a stated rationale. If you cannot verify a claim
> yourself, §4 tells you how to re-measure it; the fresh reading wins, always.
>
> **How to use this document.** Open it from inside a coding agent working in this repository and treat
> §0–§16 as your operating instructions. Do **not** paste it into a chat window: this file is large, the tail
> that gets cut is always the Definition of Done and the rails, and an agent that never received them reports
> success having bypassed them. The file on disk is the source of truth; read it whole.
>
> **One scope unit per session.** The unit is named in the session's opener — a diagnosis pass, or one §10
> step for one task. Continuing "one more lane" past the boundary is what breaks multi-session documents: the
> next session inherits a ledger whose entries match no single baseline. Cross-session state lives in
> `V3_LEDGER.md` at the repository root, never in chat history: every session writes its baseline capture,
> findings and liveness table there and commits that file before touching a source file.

---

## Table of Contents

- [0. Series status, termination, size ratchet](#0-series-status-termination-size-ratchet)
- [1. Role](#1-role)
- [2. Mission](#2-mission)
- [3. Non-goals and priced locks](#3-non-goals-and-priced-locks)
- [4. Facts Protocol](#4-facts-protocol)
- [5. Target architecture](#5-target-architecture)
- [6. Ecosystem survey protocol](#6-ecosystem-survey-protocol)
- [7. Phase 0 — Green baseline](#7-phase-0--green-baseline)
- [8. Phase 1 — Diagnosis](#8-phase-1--diagnosis)
- [9. Phase 2 — Approval gate](#9-phase-2--approval-gate)
- [10. Phase 3 — Targeted fixes](#10-phase-3--targeted-fixes)
- [11. Phase 4 — The process lane](#11-phase-4--the-process-lane)
- [12. Phase 5 — Report and archival confirmation](#12-phase-5--report-and-archival-confirmation)
- [13. Laws and the liveness table](#13-laws-and-the-liveness-table)
- [14. Safety rails](#14-safety-rails)
- [15. Anti-patterns](#15-anti-patterns)
- [16. Definition of Done](#16-definition-of-done)
- [17. Condensed paste version](#17-condensed-paste-version)

---

## 0. Series status, termination, size ratchet

**V1 is `PROJECT_SPEC.md`** — the build prompt that produced this repository. It is a historical record and
a priced lock (§3 K3). **V2 is `REFACTOR_PROMPT.md`** — the refactor lane that terminated at its own Phase 5,
with its three premises measured to zero, recorded in `REFACTOR_LEDGER.md`. V2 is not amended; its register
stays open on exactly two findings, which this document inherits as its first two work items rather than
re-deriving.

**This document is V3.** It inherits no counts and no baselines. Every number you need comes from a §4
instrument, run now, on the tree in front of you.

**Series termination condition.** V3 is justified by three measured premises. Re-derive all three before
touching anything (§7 step 3); if your fresh measurement contradicts one, stop, write the contradiction into
the Phase 5 report, and re-scope with the maintainer. A premise that no longer holds voids the law built on it
— that is the liveness table's job (§13).

1. **The advertised surface is false for an installed user.** `quantrisk run --list` enumerates the registry's
   tasks; a wheel installed outside a checkout runs 4 of them. The rest fail on undeclared optional
   dependencies (`matplotlib`, `scipy`, `cvxpy`, QuantLib) or on a study that validates against a committed
   sibling artifact, and every one of those failures names no remedy.
2. **Some gates the project relies on execute nowhere the project names.** `quantrisk validate` is run by no
   CI job and claimed by no lane; the mutation sweep and the installed-surface proof are dev-only *by
   declaration*; and the lane list in `REFACTOR_PROMPT.md` §7 drifted from the workflow until V2-28 patched
   one command. A gate that lives only in a habit is not a gate.
3. **The audit instruments read source, not runtime.** The orphan census classifies by `ast` parsing, and nine
   of the thirteen files it calls unreachable are live — reached by pytest's path convention or by
   `importlib.import_module`, which the census cannot see. A reachability metric that reports a live module
   as dead will eventually be used to delete it.

**Size ratchet.** V3's prose sections (§1–§3, §6–§15) may not exceed the same sections of
`REFACTOR_PROMPT.md` as measured at the close of V2 — 431 lines, counted by heading span, not by file length.
Growth is allowed only in §5's target lists, §4's instrument and ceiling schemas, and §13's liveness table,
because those scale with the project; prose does not. If a future revision needs more prose, it must first
show which law of this version was never executed.

---

## 1. Role

You are the refactor-and-release engineer of a repository that publishes its own evidence. You read before
you write, you measure before you assert, and you treat a green gate as a claim about one machine until you
have read which machine produced it. You are accountable for three things this project cares about more than
throughput: that no published number loses its provenance, that no gate is weakened to reach green, and that
nothing you assert anywhere in the repository is something you did not personally read.

---

## 2. Mission

Four outcomes, in this order.

1. **Make the wheel honest.** Every task the CLI advertises either runs from an installed wheel or says,
   from a registry-owned declaration, which extra it needs. The declaration is derived and pinned against what
   the task's module tree actually imports — not hand-maintained beside it.
2. **Put every gate where it claims to be.** One contract names each gate and the environments that execute
   it; the contract is compared with the workflow, with the documents, and with `[project.scripts]` in both
   directions, and it can fail.
3. **Make reachability a runtime fact.** Replace the source-parsing census's authority with an instrument that
   reports what Python can actually reach, and keep the source view beside it as a diff, so "dead code" is a
   conclusion with two independent sources rather than one parser's opinion.
4. **Audit the process, not only the product.** A plan's rows get diffed against the commit log; a law whose
   predicate is a diff gets a named commit at which the diff runs. Both rules exist because V2 shipped 66
   commits with a scheduled commit that never ran and a diff-shaped law that was never executed until the
   final audit.

---

## 3. Non-goals and priced locks

| # | Locked | Rule | Bypass |
|---|---|---|---|
| K1 | `cpp/`, `bindings/`, `CMakeLists.txt`, `CMakePresets.json` | Packaging fixes route through the existing pybind surface. If a task cannot import the compiled extension, that is a finding, not a licence to edit C++. | One cycle, with maintainer approval recorded in the Phase 5 report. |
| K2 | The frozen artifact paths under `experiments/` and `benchmarks/` | A study's output location is part of its published evidence. | Never. |
| K3 | `PROJECT_SPEC.md`, `REFACTOR_PROMPT.md` | V1's and V2's prescriptions are historical. Divergences are recorded, not painted over; their dated entries are appended to, never rewritten. | Never; superseded only by writing the next revision. |
| K4 | `evidence/manifest.json` and the 95 entries it freezes | Re-frozen only by the one mandated re-run (§13 N10), and verified by the CI step V2-28 added. | One re-run per series, with the digest report as its evidence. |
| K5 | Release `v1.9.0`, its annotated tag, and its four assets | A published release is a historical object. The tag does not move, assets are not replaced, and the page is corrected only by an appended dated record. | Never. |
| K6 | The three pre-existing CLI subcommands (`validate`, `benchmark`, `demo`) | Their output contracts are byte-identical; V2-P3.6 froze them. `run` and `run --list` are V2-era additions and may be widened deliberately — as a decision named in the commit, not as a side effect. | A recorded contract change with its own guard update in the same commit. |

---

## 4. Facts Protocol

### 4.1 Instruments

Extend **one** collector, `tools/inventory_orphan_code.py`. Do not hand-write a second measurement tool. It
emits a single JSON snapshot; each reading carries the command that produced it and the revision it read. V3
adds these readings to the ones V2 left:

1. **`declared_cli_surface`** — every console script and subcommand `[project.scripts]` and the CLI parser
   declare, each paired with the CI step (if any) whose `run:` invokes it, and with the environment that
   executes it.
2. **`tasks_runnable_from_wheel`** — every registry task id run through the installed CLI inside a clean venv
   outside the checkout, recording exit code, the last line, and the declared requirement set that predicts
   it. This is the only reading in the snapshot that requires a second environment; say so in the line, and
   keep the wheel build and venv paths out of the number.
3. **`lanes_documented_vs_executed`** — the module-path and console invocations the two lane-bearing documents
   claim, against the ones `.github/workflows/ci.yml` executes, printing both enumerations.
4. **`runtime_reachability_gap`** — for tracked Python outside the package, the source-parsing classification
   beside what a runtime import (or pytest collection) actually reaches, with the two sets' difference named.

### 4.2 Snapshot

The collector writes `build/orphan_inventory.json`. That path stays gitignored; the snapshot rewrites every
run and carries its own generation timestamp and revision. **The snapshot is telemetry, never policy.**

### 4.3 Ceilings

`tools/refactor_ceilings.json` is the policy asset the maintainer reviews. Each key names the metric, the
maximum permitted value, the phase that must reach it, and every declared exemption with its justification.
The two structural rules of V2 hold, and a third joins them:

- **Never ratchet a key that cannot fail where it runs.** A key whose verdict needs a second environment, a
  clean tree, or gitignored scratch is declared as a SKIP with its reason, and its verdict lives in the ledger.
- **Counters must not pass by absence.** Each producing command prints what it counted and what it excluded.
- **A declaration must have something that can disagree with it.** V2-27's finding: a policy file asserting a
  set, and no measurement compared to it, is decoration. Every exemption, declared movement, requirement set
  and lane claim added by V3 ships with the comparison that can redden it, in the same commit.

### 4.4 Precedence and the leak test

**Precedence rule:** when any sentence of this document disagrees with a fresh §4.1 reading, the reading wins
and the sentence is a defect of this document. Record it with `lane: facts-protocol`.

**Leak test:** after editing this document, grep it for version strings, commit SHAs, artifact counts, test
counts, and the words "currently", "no longer", "still at". Every hit is deleted, not caveated.

V2 recorded that this test as written cannot tell a leak from the rule that prohibits it — all five of its
hits were sentences stating their own law, so "delete every hit" would delete §0 and §13. V3 fixes the
instrument instead of excusing it: the test's corpus excludes lines that *define* a rule (the sentences
containing the words as quoted terms, and any `check:` predicate), and the exclusion is a named list in the
collector, so a real leak behind an excluded shape reddens the guard rather than hiding in it.

---

## 5. Target architecture

| Component | Now | V3 target |
|---|---|---|
| `python/quantrisk/experiments/registry.py` | 19 tasks: id, module, artifact path, invocation, requires | `requires` becomes a declared, derived-and-pinned dependency set per task, derived from the task's own import tree and asserted to equal the declaration both ways |
| `quantrisk run --list` | id, title, artifact | the extras a task needs, or the word `base` — a widened contract, declared as a decision (K6) |
| `quantrisk run <task>` | traceback naming no remedy | refuses by naming the missing extra and the install line that provides it |
| `.github/workflows/ci.yml` | 4 jobs; `validate` absent | every gate the contract names, executed somewhere the contract names |
| `tools/refactor_ceilings.json` | 10 keys, 8 at zero, 2 declared SKIP, 8 movements, 1 exemption census | plus the lane contract keys, each with the environment where it can fail |
| `tools/inventory_orphan_code.py` | `ast` reachability | `ast` **and** runtime reachability side by side, with the gap as a reading |
| `docs/` | five documents describing the surface | the same five re-derived, never transcribed |

---

## 6. Ecosystem survey protocol

Before designing §5's requirement declaration, survey how three installed ecosystems express the same
problem, from their own shipped metadata rather than from memory: how a package declares optional extras and
how the installer reports a missing one; how a CLI enumerates commands that need an extra it does not have;
how a scientific stack separates "importable" from "runnable". Record per ecosystem: the mechanism, whether
this repository can adopt it without a new dependency, and the one reading that would show adoption is
cosmetic. If the survey cannot be run offline, it is a finding, not a step.

---

## 7. Phase 0 — Green baseline

1. Prove the baseline is the current truth: fetch, measure how far `HEAD` trails its upstream branch, list the
   intervening commits, and record the revision and vantage you are working from. Never diagnose over a tree
   carrying another session's work; leave foreign WIP untouched and choose a single vantage.
2. Run the §7.1 lane suite and capture each command's own exit code, never a pipeline's last stage.
3. Re-derive the three premises with the §4.1 collector and record the readings in `V3_LEDGER.md` — the ledger
   is committed before any instrument is written.
4. Read the V2 close-out: `REFACTOR_LEDGER.md`'s final entries, the two carried-open findings, the ceilings
   file's declared SKIPs. V3 starts from those readings, not from a fresh guess at what V2 left.

### 7.1 The lanes

```bash
uv run --frozen ruff check .
uv run --frozen ruff format --check .
files=$(find cpp bindings tests/cpp -name '*.cpp' -o -name '*.hpp' | sort)
test -n "$files" || { echo "the C++ corpus is empty" >&2; exit 1; }
printf '%s\n' "$files" | xargs -r uv run clang-format --dry-run --Werror
uv run --frozen mypy python/quantrisk tools
uv run --frozen cmake --preset ci
uv run --frozen cmake --build --preset ci
uv run --frozen ctest --preset ci
uv pip install -e .
QUANTRISK_REFERENCE_TOOL="$PWD/build/ci/quantrisk_reference_tool" uv run --frozen pytest -q
uv run --frozen python -m tools.verify_evidence_manifest
uv run --frozen python -m tools.inventory_orphan_code --check-ceilings
```

Restore exactly the paths `git status --porcelain` names after the suite-binding command — never a blanket
restore — and re-run the manifest verifier to confirm the ledger is intact. Record which lanes were verified
where, and mark unverified any lane verified only on a mixed vantage or a tip that never executed.

---

## 8. Phase 1 — Diagnosis

Read eight lanes of the repository and register what you find — no fixes. The lanes: evidence chain, installed
surface, CI and gates, documentation coherence, static checks, runtime reachability, process artifacts (plan
tables, ledgers, registers), and cost. Each finding gets an id, a lane, a severity, the probe that decides it,
the mechanism, the remedy, the `done-when`, the files it touches, and the confidence with the reading that
supports it.

Rules V2 learned the expensive way, binding here:

- A finding is a **measurement**, not a recollection. Before filing anything about a file, open that file at
  the line you cite. If a premise inherited from another session contradicts the tree, the tree wins, and the
  contradiction is recorded rather than smoothed over.
- Check for a **pin** before filing: behaviour that looks wrong is often declared deliberate. Read the
  ceilings file, the register, and the guard source first.
- A finding about a **count** names the producer of that count in the environment that quotes it, and a
  comparison of two counts from different populations is not evidence — it is the V2-27 defect.
- Register rows and report rows must agree: a finding cited in the Phase 5 ledger without a §6 row is a defect
  in the register, found in V2 only because a human counted twice.

---

## 9. Phase 2 — Approval gate

Present the ranked findings, the proposed one-commit-per-finding sequence with a named owner for every row,
the ceilings dispositions, and the priced locks you expect to touch. Then stop and wait. When approval comes
as a blanket, record it in the ledger verbatim — the authorisation's scope is the only thing that distinguishes
a planned change from an unauthorised one.

A queue row is a commitment. V2's sequence table row `P3.4b → V2-16` never ran: the queue moved from P3.4a to
P3.5 and the finding sat registered for 20 commits while every later phase reported a green suite. So every
phase after this one closes with the audit in §11.1, and no phase may close without it.

---

## 10. Phase 3 — Targeted fixes

One finding per commit; the commit subject names the finding id or the phase step that owns it. Each fix
ships with: the change, the guard that now fails when the defect returns, the plant that proves the guard can
fail, the documents re-derived rather than edited to match, and the ledger entry recording the reading.

Sequenced work items carried from V2, to be re-measured before they are accepted:

1. **V2-24 → the installed surface.** Registry-declared requirements, the widened `run --list`, the refusal
   that names its remedy, and the census re-run as acceptance. Expect this to be the largest item; do not
   let it absorb the contract change of its own accord.
2. **V2-29 → `validate` has no lane.** One CI step plus the guard clause that compares the CLI's declared
   surface with what the lane executes, and a plant that drops the step.
3. The runtime-reachability reading (§4.1 #4), because both the requirement declaration and the dead-code
   question depend on it.

Adding a pytest case costs a cascade: the counted pair moves quotations across six files, the plant-count leg
moves separately, and the census-gold entries re-key. Prefer extending an existing guard's loop over adding a
case; when a new case is genuinely required, pay the cascade in the same commit and let the guards find what
you missed — they have been more reliable at that than any grep.

---

## 11. Phase 4 — The process lane

Three audits, each with its own guard and plant, executed on the repository's own artifacts.

1. **Plan versus log.** Enumerate every row of every plan table this series approved, enumerate the commit
   subjects in the range, and assert the difference is empty or every missing row is recorded as deliberately
   not done with its reason. Run this at each phase close and at Phase 5, not only at the end.
2. **Laws versus commits.** For each §13 law whose predicate is a diff or a range count, name the commit at
   which it is run and run it there. A law with an unexecuted predicate is VOID for the session that cited it.
3. **Declarations versus measurements.** Every exemption, declared movement, requirement set and lane claim in
   a policy file gets the comparison that can disagree with it. This is the shape shared by V2-27 (an undeclared
   byte-only exemption inferred from an exit code) and V2-28 (a documented lane no lane executed): both were
   invisible to every gate because the gate checked the tree, and the defect was between two documents.

---

## 12. Phase 5 — Report and archival confirmation

Deliver, as a final ledger entry, assembled from `V3_LEDGER.md` plus a fresh reading of the repository:

- **Evidence Ledger** — per finding: id, verdict (fixed / rejected / deferred), the probe, the closing commit.
- **The liveness table** (§13) with ACTIVE/VOID and the reading that decided each.
- **The ceilings file's final state** with the maintainer's review notes.
- **The deliberately-not-done list** — findings found and not fixed, each with its reason. An honest "not done"
  is required; an empty list is suspect.
- **Premises audit** — §0's three premises restated with final readings, and what each voiding means for V4.
- **Series handoff** — what V4 must contain, derived from this run's evidence, not from this document's prose.
- **Per-lane verification table** (§13 N12) — every lane with the revision *and* the environment it was
  verified on; any lane verified only on a mixed vantage, on a foreign-WIP tree, or on a tip that never
  executed, is marked unverified, not green.
- **Archival confirmation** — before anything after the series starts: tree clean and `HEAD` equal to
  `origin/main`; every commit the series created proven an ancestor of the remote; CI read for each commit,
  with a cancelled run named as cancelled and its content's verification attributed honestly; registers,
  ledgers and documents re-counted against the artifacts they describe; tags, releases and published assets
  re-read from the platform rather than from the session's memory; and no stray instrument tracked or left on
  disk. This item exists because a V2 close-out needed it: three self-counts in the V2 report went stale the
  moment a late finding was registered, and no guard reads the ledger to catch that.

---

## 13. Laws and the liveness table

Every law carries a `check:` predicate **and the commit at which that predicate is run**. A law whose
precondition no longer holds is VOID and may not be cited to justify or block work. Produce the table at the
end of Phase 1 and re-evaluate it at Phase 5.

| # | Law | Precondition | check: | run at |
|---|---|---|---|---|
| N1 | **Requirement truth.** Each task's declared requirement set equals what the installed census shows, in both directions. | Registry owns the declaration. | A guard diffing declaration against census for all 19 tasks, printing each side; a plant that declares `base` for a task needing `plot`. | each fix commit touching `registry.py`; Phase 5 |
| N2 | **Advertised surface honesty.** Every id `run --list` prints either runs from a wheel or names the extra it needs. | The widened list ships. | `tasks_runnable_from_wheel` equals the prediction derived from the declaration, with mismatches named. | Phase 3 acceptance; Phase 5 |
| N3 | **Lane contract.** Every gate a document or policy claims is executed somewhere, and every gate declared dev-only carries its reason in the contract. | The contract file exists. | `lanes_documented_vs_executed` empty on both sides, each side printed; a plant drops a claimed step. | each fix commit touching `ci.yml`; Phase 5 |
| N4 | **No silence by count.** Any reading that counts skips, exemptions or waived artifacts names the population it counted. | The producers emit names, not totals. | Each such guard compares sets both ways and refuses an empty declared set. | Phase 4; Phase 5 |
| N5 | **Declarations are checkable.** Every exemption, movement and requirement set in the ceilings file has a comparison that can redden it. | The file is the policy asset. | A guard per declaration class diffing it against the artifact it declares. | Phase 4; Phase 5 |
| N6 | **Runtime reachability.** No file is asserted dead on the strength of the `ast` census alone. | Both readings exist. | `runtime_reachability_gap` printed with both sets and their difference; deleting a file requires the runtime reading. | Phase 3 item 3; Phase 5 |
| N7 | **One finding, one commit; plan equals log.** Every commit maps to a registered finding or a named step, and every approved row was executed or recorded as deliberately not done. | Rows exist from Phase 2. | §11.1's diff, empty or annotated. | every phase close; Phase 5 |
| N8 | **No gate weakened.** No tolerance loosened, no test deleted, no `skip`/`xfail` added to reach green. | The §7.1 suite defines green. | The diff over the series range for markers and bounds, with each hit carrying a declared intent. | every phase close; Phase 5 |
| N9 | **Plant liveness.** Every declared plant is rejected by its guard, for its declared mechanism. | The sweep runs from the current locations. | The sweep's own summary line, captured, not recalled; a plant that does not fire is High. A plant cannot fire while its target carries uncommitted edits — the post-commit re-run is part of the proof. | Phase 5, clean tree |
| N10 | **One re-run.** The suite re-runs exactly once per series; only declared categories move; nothing else is regenerated. | The evidence chain is frozen. | The digest report before/after, with undeclared movement failing the build. | the one phase that runs it |
| N11 | **Facts precedence.** A document loses to a fresh reading; the leak test excludes the sentences that define the rules it polices, by name. | §4.1 exists. | Re-run the leak test and one collector reading; any mismatch is a finding against the document. | every document edit; Phase 5 |
| N12 | **Baseline purity and per-lane provenance.** The baseline is measured from one vantage against a revision with a CI run of its own, and each lane names the revision **and** environment it was verified on. | The §7.1 lanes exist. | The Phase 5 per-lane table; anything unverified is marked unverified, not green. | Phase 0; Phase 5 |

---

## 14. Safety rails

- Never touch `.env`, credentials, or anything secret-shaped.
- Never weaken a coverage gate, delete a failing test, or add `skip`/`xfail` to reach green.
- Never delete `data/` fixtures, vendored directories, or committed artifacts.
- No `--no-verify`, no force-push, no history rewriting, **no tag movement**, no replacing a published
  release asset (K5).
- Outward actions — push, PR, release, issue or comment — and edits to `PROJECT_SPEC.md`,
  `REFACTOR_PROMPT.md` or this file need the maintainer's approval for that case, recorded verbatim.
- A risky action taken twice with approval is not approved the third time. Ask when the scope changes.
- When a command is interrupted or a background job returns nothing, treat the absence of a report as
  "unknown", not as failure or success: re-run it, or read its log, before you state an outcome.

---

## 15. Anti-patterns

Each of these happened in this repository's history; none was caught by a gate.

1. **Counting as agreement.** A register demands "declare the 18 byte-only artifacts"; a report prints "18
   with content movement" about a different population. Both numbers were true; the match meant nothing.
2. **A plan row nobody ran.** The queue advanced past its own commitment because no artifact recorded that a
   scheduled commit had not happened.
3. **A documented lane nobody executes.** A command sat in a block introduced by "these are the CI lanes" for
   an entire series while the workflow never contained it.
4. **A declaration nobody compares.** A policy file asserted a set; the manifest held a different set; nothing
   read both.
5. **Green read from a cancelled run.** `cancel-in-progress` makes a tip that never executed look merely
   recent; a later run on a different tree is not that tip's verification.
6. **"No X" from a grep that could not see X.** Absence claims that did not enumerate which corpora the query
   walked, including the ones the instrument excludes by construction.
7. **Editing the document to fit the number.** The number is re-derived or the sentence is removed; a document
   is never repainted to match a claim it can no longer support.
8. **A fallback that synthesises what is missing.** A missing fixture yields an empty list, a missing oracle
   yields a skip count, and a study publishes numbers from neither. Refuse by naming the absent thing.

---

## 16. Definition of Done

1. All three §0 premises re-measured; each either closed with a reading or carried open with a reason.
2. Every registered finding fixed, rejected with evidence, or in the deliberately-not-done list — no silence.
3. The installed census run on a wheel built from a HEAD export, in a clean venv outside the checkout, from a
   neutral cwd, with the imported module's identity asserted before any conclusion drawn.
4. The lane contract, the requirement declarations, the runtime reachability reading, and their guards all
   shipped with plants that fired.
5. The sweep's own summary line captured at the final revision on a clean tree, and every plant accounted for.
6. Every document that quotes a moved path, count or command re-derived in the same commit as the move, with
   the counting guards green on the corrected tree.
7. The Phase 5 report, ledger, liveness table, ceilings review, deliberately-not-done list, premises audit,
   handoff, per-lane table, **and the archival confirmation** committed and pushed.
8. CI read for every commit in the range, with each non-success named and its verification attributed to the
   run and environment that actually produced it.
9. `V3_LEDGER.md` records, for each phase: what was run, what it printed, and what was decided — no entry
   written before the tool reported it.

---

## 17. Condensed paste version

> Work V3 from `V3_PROMPT.md`, read whole from disk. Phase 0: prove baseline, re-derive three premises with
> the collector — installed surface false (4 of 19 tasks run), gates executing nowhere named, reachability
> measured from source not runtime. Phase 1: eight-lane diagnosis, measurements not recollections, check for a
> pin before filing. Phase 2: rank and wait for approval. Phase 3: one finding per commit — carried-open
> V2-24 (requirement declaration + widened `run --list`, a deliberate contract change), V2-29 (`validate`'s
> missing lane), and the runtime reachability reading; every guard needs a plant, and a plant fires only on a
> committed target. Phase 4: the process lane — diff the plan's rows against the log, name the commit each
> diff-shaped law runs at, and give every declaration a comparison that can disagree. Phase 5: report, liveness
> table, ceilings review, deliberately-not-done list, premises audit, per-lane table, and the archival
> confirmation. Locks: C++ untouched, frozen artifact paths, V1/V2 documents historical, one re-run, no tag or
> asset movement, outward actions need per-case approval, budget $0. Never weaken a gate, delete a test, or
> write an outcome before the tool reports it.
