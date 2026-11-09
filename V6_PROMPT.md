# V6_PROMPT.md — the rails for the V6 series

V6 starts at `bb914624801bbddeee091914bd42bc39ad4f7d9d`, the terminal entry of V5. It inherits V5's
closing state, not its prose: every number below is a reading taken at that tip, and every claim
about an earlier series is a pointer to the ledger that measured it. `V6_LEDGER.md` is the
cross-session state; this file is the rail set.

## 0. Status, premises and termination

**What is closed.** V1 is `PROJECT_SPEC.md` (historical, priced lock). V2 is `REFACTOR_PROMPT.md`
(terminated, `REFACTOR_LEDGER.md`). V3 (`V3_PROMPT.md`, `V3_LEDGER.md`) closed its eight §12
deliverables. V4 (`V4_LEDGER.md`) closed the V3 carryover gaps. V5 (`V5_PROMPT.md`,
`V5_LEDGER.md`) closed F1–F7 and the 195-plant census. None of those files is amended by V6.

**Three premises, measured at `bb91462`.** If a fresh reading contradicts one, stop and write the
contradiction into the Phase 5 report before touching anything.

1. **The published chain is frozen and V6 must not move it silently.** `v1.9.0` is tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`; release `424060629` holds four assets created
   `2026-10-26T09:35:41Z`. `evidence/manifest.json` holds 95 entries and verifies intact. A V6 unit
   that regenerates either must say so in its Phase 0 and again in its Phase 5.
2. **The committed suite artifact's revision is checkable but undecided.**
   `benchmarks/suite/results/suite_run.json` names `17df062040b8`; `artifact_revision` reports
   `gap 0`, `matches_tip false`, 21 attributed paths. The claim is no longer silent, but no unit has
   decided whether the artifact is pinned, regenerated, or permanently attributed. V6 must decide.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** Both are honest at this
   tip because their reasons are printed. V6 must re-read them at its own tip before citing them.

**Termination condition.** V6 ends when every G1–G6 finding is fixed, rejected with evidence or named
in the deliberately-not-done list; when the full plant census has been captured at the final V6 tip
on a clean tree; and when the Phase 5 report and archival confirmation are committed and pushed.
A premise that no longer holds voids the rule built on it; the liveness table says which.

## 1. What V6 inherits, and what it may not re-derive

V5's per-lane table and archival confirmation are the baseline, not a template to copy. V6 re-measures
at its own tip: counts, ceilings, manifest, formatter corpus, pytest nodes, CI steps, platform
assets. An inherited number is a claim until a V6 tool prints it.

The six handoff items in `V5_LEDGER.md` Phase 5 §6 are V6's starting agenda. They are not a queue:
which one a unit takes is decided in that unit's Phase 0, and taking one does not approve the rest
unless the maintainer says so in the same words.

## 2. Facts Protocol

1. **A reading is a command and its output, at a revision.** Nothing enters a ledger entry without
   both.
2. **No outcome before the tool reports it.** A push, a run and a job are `unknown` until the API
   says otherwise; `gh run watch` returning non-zero on a transport error is not a verdict.
3. **Attribute every CI reading to its run, attempt, runner and environment.** A cancelled run is
   named cancelled, never green.
4. **A historical reading is not rewritten.** If a later unit moves a count, the new entry prints
   the delta and the old row keeps its number.
5. **A guard that cannot redden is not a guard.** New readings carry a plant or a forged-input
   proof, and the plant's verdict is captured by a targeted sweep on a clean target.
6. **A document loses to a fresh reading.** Any printed claim that moves is re-derived in the same
   commit, and the re-derivation reading stays at `gap 0`.

## 3. Lanes and policy assets at `bb91462`

| asset | reading |
|---|---|
| registry tasks / suite members | 19 / 19, `registry_parity` mismatch empty |
| plants | **195**; the last full census is `195/195` at `ea8beb4` |
| ceiling keys | **15** — 13 `ok`, 2 `SKIP` |
| manifest | 95 entries, `Evidence is intact.` |
| formatter corpus | **234 / 234**, both differences empty |
| pytest nodes | 560 collected / 491 offline, `collection_errors 0` |
| named CI steps | **34** |
| readings at `gap 0` | `docs_rederivation`, `lanes_documented_vs_executed`, `with_extras_census`, `artifact_revision`, `formatter_census`, `registry_parity` |

The lanes are the ones `.github/lane_contract.md` declares, plus the local static gates, the manifest
verifier, the collector readings, the full `pytest -q` and the mutation sweep. The sweep and the
installed-surface proof are development-only **by permanent decision** (§4); every other lane names
its revision and environment in the Phase 5 table.

## 4. The sweep's vantage is permanently development-only

V5 decided this and V6 makes it permanent: `plants_not_rejected_by_their_guard` stays `SKIP` with
`max 0` and `may_be_unmeasured: true`, and no V6 unit reopens it as an open question. The reason is
mechanical, not budgetary — the sweep rewrites tracked files one at a time and writes gitignored
scratch into the checkout, so a key computed from its summary line could not fail on the runner that
evaluates it. A series that repeats the `SKIP` as "undecided" is the failure mode this section
exists to prevent.

The decision is reversible only by a unit whose Phase 0 states that it is redesigning the harness so
the sweep no longer touches tracked files, and that unit must carry its own approval. Until then,
the 195/195 line is a development-side reading and must be labelled as one wherever it is cited.

## 5. The candidate findings

| id | finding | `check:` |
|---|---|---|
| G1 | No written V6 prompt | this file exists, states premises, lanes, rails and termination; §6's approval rule is written down and was followed by the launch unit |
| G2 | The sweep's vantage was decided but never made permanent | §4 states the decision, and no V6 entry lists it as open; the key's declaration and its reason still agree |
| G3 | The committed suite artifact's revision is checkable but undecided | either the artifact is pinned by a declared re-run, or a ledger entry states the freeze boundary at the artifact level and `artifact_revision` still reports `gap 0`; the decision is written, not implied |
| G4 | The two `SKIP` keys are inherited, not re-read | both are re-read at a V6 tip, their `corpus` and the printed reason agree, and each is either retained with the reading or retired |
| G5 | Development-only counts have no second vantage | every count cited as a gate names the vantage that produced it; a count that has only a development reading is marked as such, not promoted |
| G6 | No silent re-freeze | the manifest and the published assets are re-read at every Phase 5; any regeneration is named in that unit's Phase 0 and Phase 5 |

## 6. One scope unit per approval

- Outward actions — push, PR, release, issue, comment — and edits to `PROJECT_SPEC.md`,
  `REFACTOR_PROMPT.md`, `V3_PROMPT.md` or `V5_PROMPT.md` need the maintainer's approval **for that
  case**, recorded verbatim in that unit's Phase 0 entry.
- A Phase 0 entry states the revision, vantage, re-measured baseline, the finding taken, what the
  unit excludes, the approval verbatim, the number of pushes and what each carries. No reading is
  written before the tool reports it.
- Near the close of every unit except the last, the ledger's terminal entry records the
  implementation tip's CI with its run, attempt, runner and step counts. The terminal commit's own
  CI is read after the second push and reported in the session handoff.
- Editing this prompt is itself a scope unit and needs its own verbatim approval. No unit may amend
  this section to widen its own authority.

## 7. Phase 0, Phase 5, Definition of Done

**Phase 0** re-counts the archive against the tip that is actually pushed, names the vantage and the
platform's tag/release state, re-measures the three premises, chooses one finding, and records the
approval. It ships as its own commit before any source file is touched.

**An implementation unit** ships the change, its guard, its plant and its readings in one named
commit, then the terminal entry attributing that tip's CI. Both pushes are attributed. The counted
pair, the plant total, the ceiling keys and the formatter corpus are re-measured after the change
and their deltas printed.

**Phase 5** delivers the eight `V3_PROMPT.md` §12 items: an evidence ledger; the liveness table
re-evaluated at the final tip; the ceilings file's final state with review notes; an honestly
non-empty deliberately-not-done list; a premises audit; a series handoff; a per-lane verification
table with revision **and** environment for every lane; and an archival confirmation requiring a
clean tree with `HEAD` equal to `origin/main`, every V6 commit proven an ancestor of the remote, CI
attributed for every commit, registers and documents re-counted, tags/releases/assets re-read from
the platform, and no stray instrument tracked or left on disk.

**Definition of Done.** All three premises re-measured; each of G1–G6 fixed, rejected with evidence
or in the deliberately-not-done list; a full sweep's own summary line captured at the final revision
on a clean tree; every document quoting a moved count re-derived in the same commit; the Phase 5
report and archival confirmation committed and pushed; CI read for every commit in the range; and
every ledger entry recording what was run, what it printed and what was decided.

## 8. Size ratchet

`V3_PROMPT.md` §0 caps its prose sections at 431 lines measured by heading span. V6's prose sections
(§1–§3, §6–§8) may not exceed that bound. Growth is allowed only in §5's finding table and §3's lane
inventory. If a future revision needs more prose, it must first show which rule of this version was
never executed.
