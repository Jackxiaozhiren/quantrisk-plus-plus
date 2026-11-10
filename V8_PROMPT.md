# V8_PROMPT.md — the rails for the V8 series

V8 starts at `4f76337b306ae79aaaf5a07ba4ced545dacc473a`, the terminal entry of V7. It inherits V7's
closing state, not its prose: every number below is a reading taken at that tip, and every claim
about an earlier series is a pointer to the ledger that measured it. `V8_LEDGER.md` is the
cross-session state; this file is the rail set.

## 0. Status, premises and termination

**What is closed.** V1 is `PROJECT_SPEC.md` (historical, priced lock). V2 is `REFACTOR_PROMPT.md`
(terminated, `REFACTOR_LEDGER.md`). V3 closed its eight §12 deliverables, V4 the V3 carryover, V5
F1–F7 and the 195-plant census, V6 G1–G6, and V7 H1–H7 with H6 partial and named. None of those
files is amended by V8.

**Three premises, measured at `4f76337`.** If a fresh reading contradicts one, stop and write the
contradiction into the Phase 5 report before touching anything.

1. **The published chain is frozen and V8 must not move it silently.** `v1.9.0` is tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`; release `424060629` holds four assets created
   `2026-10-26T09:35:41Z`. `evidence/manifest.json` holds 95 entries and verifies intact.
2. **The pin is now a guard, not a sentence.** `artifact_revision_gap` declares
   `pinned_revision 17df062040b8`; `artifact_revision` prints `gap 0`, `pin_holds true`,
   `matches_tip false` on the committed artifact and exempts a fresh upload naming the tip. Four
   forged cases in the existing F4 test redden it in both directions. V8 must not weaken it.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** Both are honest at this
   tip because their reasons are printed. V8 must re-read them at its own tip before citing them.

**Termination condition.** V8 ends when every H1–H6 finding is fixed, rejected with evidence or
named in the deliberately-not-done list; when the full plant census has been captured on the clean
tree at the **literal final tip, after the terminal entry's push**, and quoted in the session
handoff with that revision; and when the Phase 5 report and archival confirmation are committed and
pushed. A premise that no longer holds voids the rule built on it; the liveness table says which.

## 1. What V8 inherits, and what it may not re-derive

V7's per-lane table and archival confirmation are the baseline, not a template to copy. V8
re-measures at its own tip: counts, ceilings, manifest, formatter corpus, pytest nodes, CI steps and
platform assets. An inherited number is a claim until a V8 tool prints it.

The ten deliberately-not-done items in `V7_LEDGER.md` Phase 5 §4 and the eight handoff items in its
§6 are V8's starting agenda. They are not a queue: which one a unit takes is decided in that unit's
Phase 0. V8 is a closing-and-verification series: it adds no guard, plant, ceiling key, CI step,
lane or document count, and its deliverables are one reading taken at the right revision, one rule
that can be satisfied, and an honest handoff.

## 2. Facts Protocol

1. **A reading is a command and its output, at a revision.** Nothing enters a ledger entry without
   both.
2. **No outcome before the tool reports it.** A push, a run and a job are `unknown` until the API
   says otherwise; `gh run watch` returning non-zero on a transport error is not a verdict.
3. **Attribute every CI reading to its run, attempt, runner and environment.** A cancelled run is
   named cancelled, never green.
4. **A historical reading is not rewritten.** If a later unit moves a count, the new entry prints
   the delta and the old row keeps its number.
5. **A guard that cannot redden is not a guard.** A new comparison carries a forged-input or plant
   proof in both directions where two assets declare each other.
6. **A document loses to a fresh reading.** Any printed claim that moves is re-derived in the same
   commit, and the re-derivation reading stays at `gap 0`.
7. **A final-tip census is a reading after the last push.** It runs on the clean tree at the
   terminal commit and its summary line is quoted in the session handoff with that revision. It is
   not written into a ledger file, because a file cannot carry the SHA of the commit that contains
   it without moving the tip it measures.

## 3. Lanes and policy assets at `4f76337`

| asset | reading |
|---|---|
| registry tasks / suite members | 19 / 19, `registry_parity` mismatch empty |
| plants | **195**; the last full census is `195/195` at `0c239c5` (development-side vantage; the sweep has no CI lane) |
| ceiling keys | **15** — 13 `ok`, 2 `SKIP` |
| manifest | 95 entries, `Evidence is intact.` |
| formatter corpus | **238 / 238**, both differences empty |
| pytest nodes | 560 collected / 491 offline, `collection_errors 0` |
| named CI steps | **34** |
| readings at `gap 0` | `docs_rederivation`, `lanes_documented_vs_executed`, `with_extras_census`, `artifact_revision`, `formatter_census`, `registry_parity` |

The lanes are the ones `.github/lane_contract.md` declares, plus the local static gates, the
manifest verifier, the collector readings, the full `pytest -q` and the mutation sweep. The sweep
and the installed-surface proof are development-only by permanent decision (§4); every other lane
names its revision and environment in the Phase 5 table.

## 4. The sweep and installed-surface vantages stay closed

`V6_PROMPT.md` §4 made the sweep's development-only decision permanent and `V7_PROMPT.md` §4 kept
it. V8 performs no harness redesign: it does not change how the sweep writes tracked files, does not
give either `SKIP` a runner-side verdict, does not add a CI lane for the installed-surface proof,
and does not promote `195/195` to a gate. Its Phase 0 states this before any file is touched, which
is the condition V6 §4 sets for not reopening the question. Every citation of the census names its
development-side vantage.

## 5. The candidate findings

| id | finding | `check:` |
|---|---|---|
| H1 | The census has never been captured at a literal final tip | after the terminal entry's push, a full census runs on the clean tree at that commit; its summary line and revision are quoted in the session handoff; the ledger states the plan before the run and does not claim the reading early |
| H2 | V7's size ratchet could not be satisfied by its own series | this file states one hard bound (431) and treats V6's 146 / 88 and V7's 154 / 98 as reported reference figures rather than gates; Phase 5 prints V8's measured total and prose lines beside them |
| H3 | `V7_PROMPT.md` §8's two sentences remain standing | they are recorded as historical fact in the Phase 5 report and handoff; `V7_PROMPT.md` is not edited, because its §6 requires its own approval |
| H4 | The two `SKIP` keys still have no runner vantage | both are re-read at a V8 tip, each `corpus` agrees with its printed `precondition absent` reason, both are retained, and no lane, plant or key is added for them |
| H5 | No silent re-freeze must be re-read every series | the manifest and the platform's tag, release and four assets are re-read in Phase 0 and Phase 5 with equal values; nothing is regenerated and the pin is not moved |
| H6 | The local pytest failure is environmental | the per-lane table names `1 failed, 559 passed` as the sandbox bytecode-cache plant; no `skip`, `xfail`, marker, tolerance or test deletion is added; CI's `490 passed, 5 skipped` is read instead |

## 6. One scope unit per approval

- **The maintainer's approval, verbatim.** `授权启动 V8，按你的建议推进剩余系列` (2026-11-10).
  This is a series-wide approval. It covers H1–H6, the Phase 0 entry, the Phase 5 report, the
  terminal entry, the two named pushes and the final-tip census, and it explicitly overrides the
  case-by-case rule for the V8 series. It is recorded verbatim in the V8 Phase 0 entry before any
  outward action. The V7 series-wide approval is spent and is not reused.
- **Not authorised by that sentence:** editing any earlier prompt (`PROJECT_SPEC.md`,
  `REFACTOR_PROMPT.md`, `V3_PROMPT.md`, `V5_PROMPT.md`, `V6_PROMPT.md` or `V7_PROMPT.md`) or this
  file, a harness redesign that reopens §4, a declared re-run of the evidence chain, a tag movement
  or release asset replacement, a new CI lane, or a third push. Any of those needs a new verbatim
  approval.
- Outward actions — push, PR, release, issue, comment — need the maintainer's approval for that
  case, recorded verbatim in that unit's Phase 0 entry. Within V8 the sentence above is that case
  for the two named pushes.
- A Phase 0 entry states the revision, vantage, re-measured baseline, the finding taken, what the
  unit excludes, the approval verbatim, the number of pushes and what each carries. No reading is
  written before the tool reports it.
- Near the close of every unit except the last, the ledger's terminal entry records the
  implementation tip's CI with its run, attempt, runner and step counts. The terminal commit's own
  CI is read after the second push and reported in the session handoff.
- Editing this prompt is itself a scope unit and needs its own verbatim approval. No unit may amend
  this section to widen its own authority.

## 7. Phase 0, Phase 5, Definition of Done

**Phase 0** re-counts the archive against the tip that is actually pushed, names the vantage and
the platform's tag/release state, re-measures the three premises, chooses the findings, and records
the approval. It ships as its own commit before any other file is touched.

**V8 has no implementation commit**: its only tracked additions are this file and the ledger, so the
first push carries Phase 0 and the Phase 5 report, and the second carries the terminal entry. Both
pushes are attributed from the API.

**Phase 5** delivers the eight `V3_PROMPT.md` §12 items: an evidence ledger; the liveness table
re-evaluated at the report's tip; the ceilings file's final state with review notes; an honestly
non-empty deliberately-not-done list; a premises audit; a series handoff; a per-lane verification
table with revision **and** environment for every lane; and an archival confirmation requiring a
clean tree with `HEAD` equal to `origin/main`, every V8 commit proven an ancestor of the remote, CI
attributed for every commit, registers and documents re-counted, tags/releases/assets re-read from
the platform, and no stray instrument tracked or left on disk.

**Definition of Done.** All three premises re-measured; each of H1–H6 fixed, rejected with evidence
or in the deliberately-not-done list; a full sweep's own summary line captured at the literal final
revision, after the terminal push, on a clean tree; every document quoting a moved count re-derived
in the same commit; the Phase 5 report and archival confirmation committed and pushed; CI read for
every commit in the range; and every ledger entry recording what was run, what it printed and what
was decided.

## 8. Size ratchet

`V3_PROMPT.md` §0 caps its prose sections at 431 lines measured by heading span, and that is V8's
only hard bound. V6 measured 146 / 88 and V7 154 / 98; both are **reported reference figures, not
gates**, because V7's attempt to enforce 88 as a soft cap produced a partial finding rather than a
shorter prompt. V8 adds no section beyond V7's eight, and its Phase 5 report prints the measured
total and prose lines beside those two figures so the growth is attributed rather than hidden. If
V8 exceeds 431 the series has failed its DoD; if it exceeds 98 it says so in the report and names
where the lines went.
