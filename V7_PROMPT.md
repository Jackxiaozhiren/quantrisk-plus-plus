# V7_PROMPT.md — the rails for the V7 series

V7 starts at `d975baa7c9da67de776332b0f0321e27471cef37`, the terminal entry of V6. It inherits V6's
closing state, not its prose: every number below is a reading taken at that tip, and every claim
about an earlier series is a pointer to the ledger that measured it. `V7_LEDGER.md` is the
cross-session state; this file is the rail set.

## 0. Status, premises and termination

**What is closed.** V1 is `PROJECT_SPEC.md` (historical, priced lock). V2 is `REFACTOR_PROMPT.md`
(terminated, `REFACTOR_LEDGER.md`). V3 closed its eight §12 deliverables, V4 closed the V3 carryover,
V5 closed F1–F7 and the 195-plant census, and V6 closed G1–G6 with `V6_PROMPT.md` and
`V6_LEDGER.md`. None of those files is amended by V7.

**Three premises, measured at `d975baa`.** If a fresh reading contradicts one, stop and write the
contradiction into the Phase 5 report before touching anything.

1. **The published chain is frozen and V7 must not move it silently.** `v1.9.0` is tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`; release `424060629` holds four assets created
   `2026-10-26T09:35:41Z`. `evidence/manifest.json` holds 95 entries and verifies intact. A V7 unit
   that regenerates either must say so in its Phase 0 and again in its Phase 5.
2. **The committed suite artifact is pinned in writing but not guarded.**
   `benchmarks/suite/results/suite_run.json` names `17df062040b8`; `artifact_revision` reports
   `gap 0`, `matches_tip false`, 21 attributed paths. It checks that the revision is hexadecimal,
   exists in a deep clone and is named by the artifact's own provenance; it does not compare the
   revision with the pin V6 declared. V7 must decide whether that decision becomes checkable.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** Both are honest at this
   tip because their reasons are printed. V7 must re-read them at its own tip before citing them.

**Termination condition.** V7 ends when every H1–H7 finding is fixed, rejected with evidence or
named in the deliberately-not-done list; when the full plant census has been captured at the final
V7 tip on a clean tree; and when the Phase 5 report and archival confirmation are committed and
pushed. A premise that no longer holds voids the rule built on it; the liveness table says which.

## 1. What V7 inherits, and what it may not re-derive

V6's per-lane table and archival confirmation are the baseline, not a template to copy. V7
re-measures at its own tip: counts, ceilings, manifest, formatter corpus, pytest nodes, CI steps and
platform assets. An inherited number is a claim until a V7 tool prints it.

The seven handoff items in `V6_LEDGER.md` Phase 5 §6 and the nine deliberately-not-done items in its
§4 are V7's starting agenda. They are not a queue: which one a unit takes is decided in that unit's
Phase 0, and taking one does not approve the rest unless the maintainer says so in the same words.

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

## 3. Lanes and policy assets at `d975baa`

| asset | reading |
|---|---|
| registry tasks / suite members | 19 / 19, `registry_parity` mismatch empty |
| plants | **195**; the last full census is `195/195` at `9486c7a` (development-side vantage; the sweep has no CI lane) |
| ceiling keys | **15** — 13 `ok`, 2 `SKIP` |
| manifest | 95 entries, `Evidence is intact.` |
| formatter corpus | **236 / 236**, both differences empty |
| pytest nodes | 560 collected / 491 offline, `collection_errors 0` |
| named CI steps | **34** |
| readings at `gap 0` | `docs_rederivation`, `lanes_documented_vs_executed`, `with_extras_census`, `artifact_revision`, `formatter_census`, `registry_parity` |

The lanes are the ones `.github/lane_contract.md` declares, plus the local static gates, the
manifest verifier, the collector readings, the full `pytest -q` and the mutation sweep. The sweep
and the installed-surface proof are development-only by permanent decision (§4); every other lane
names its revision and environment in the Phase 5 table.

## 4. The sweep's vantage stays closed, and no harness redesign is in scope

V6 §4 made the development-only decision permanent: `plants_not_rejected_by_their_guard` stays
`SKIP` with `max 0` and `may_be_unmeasured: true`, and the installed-surface proof stays local.
V7 performs no harness redesign: it does not change how the sweep writes tracked files, does not
give either `SKIP` a runner-side verdict, and does not promote `195/195` to a CI gate. Its Phase 0
states this before any source file is touched, which is the condition V6 §4 sets for not reopening
the question. Every citation of the census names its development-side vantage.

## 5. The candidate findings

| id | finding | `check:` |
|---|---|---|
| H1 | V6 pinned the committed artifact in prose and left it unguarded | `artifact_revision_gap`'s ceiling row declares `pinned_revision`; `artifact_revision()` refuses a committed artifact whose `git_commit` differs from it while leaving the fresh CI upload alone; two forged-input proofs redden it in both directions (a different real revision in the artifact, and a changed pin in the policy asset); `--check-ceilings` still prints 15 keys with `artifact_revision_gap 0` |
| H2 | The two `SKIP` keys have no runner vantage | both are re-read at a V7 tip, each `corpus` agrees with its printed `precondition absent` reason, both are retained and neither is promoted or retired |
| H3 | The printed census verdict has one vantage | every V7 citation of `195/195` labels it development-side on the same line; `docs_rederivation` stays at `gap 0`; no new document promotes it to a gate |
| H4 | The sole route to reopening §4 is a harness redesign | Phase 0 states V7 performs none; no CI lane, plant, ceiling key or step is added for the sweep; the deliberately-not-done list names the refusal with its reason |
| H5 | No silent re-freeze is only a written rule | H1's pin guard makes an undeclared rewrite of the committed artifact fail; the manifest and the platform's tag, release and four assets are re-read in Phase 0 and Phase 5 with equal values; nothing is regenerated |
| H6 | Size ratchet and prompt edits | this file's prose sections stay within V6's measured 88 lines and V3 §0's 431-line bound; no earlier prompt is edited; editing this file is its own unit |
| H7 | The local pytest failure is environmental | the per-lane table names `1 failed, 559 passed` as the sandbox bytecode-cache plant; no `skip`, `xfail`, marker, tolerance or test deletion is added; CI's `490 passed, 5 skipped` is read instead |

## 6. One scope unit per approval

- **The maintainer's approval, verbatim.** `授权启动 V7，按你的建议推进剩余系列` (2026-11-10).
  This is a series-wide approval. It covers H1–H7, the Phase 0 entry, the implementation, the
  Phase 5 report, the terminal entry and the two named pushes, and it explicitly overrides the
  case-by-case rule for the V7 series. It is recorded verbatim in the V7 Phase 0 entry before any
  outward action. The V6 series-wide approval is spent and is not reused.
- **Not authorised by that sentence:** editing any earlier prompt (`PROJECT_SPEC.md`,
  `REFACTOR_PROMPT.md`, `V3_PROMPT.md`, `V5_PROMPT.md` or `V6_PROMPT.md`) or this file, a harness
  redesign that reopens §4, a declared re-run of the evidence chain, a tag movement or release
  asset replacement, a new CI lane, or a third push. Any of those needs a new verbatim approval.
- Outward actions — push, PR, release, issue, comment — need the maintainer's approval for that
  case, recorded verbatim in that unit's Phase 0 entry. Within V7 the sentence above is that case
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
the approval. It ships as its own commit before any source file is touched.

**An implementation unit** ships the change, its guard, its proofs and its readings in one named
commit, then the terminal entry attributing that tip's CI. Both pushes are attributed. The counted
pair, the plant total, the ceiling keys and the formatter corpus are re-measured after the change
and their deltas printed.

**Phase 5** delivers the eight `V3_PROMPT.md` §12 items: an evidence ledger; the liveness table
re-evaluated at the final tip; the ceilings file's final state with review notes; an honestly
non-empty deliberately-not-done list; a premises audit; a series handoff; a per-lane verification
table with revision **and** environment for every lane; and an archival confirmation requiring a
clean tree with `HEAD` equal to `origin/main`, every V7 commit proven an ancestor of the remote, CI
attributed for every commit, registers and documents re-counted, tags/releases/assets re-read from
the platform, and no stray instrument tracked or left on disk.

**Definition of Done.** All three premises re-measured; each of H1–H7 fixed, rejected with evidence
or in the deliberately-not-done list; a full sweep's own summary line captured at the final revision
on a clean tree; every document quoting a moved count re-derived in the same commit; the Phase 5
report and archival confirmation committed and pushed; CI read for every commit in the range; and
every ledger entry recording what was run, what it printed and what was decided.

## 8. Size ratchet

`V3_PROMPT.md` §0 caps its prose sections at 431 lines measured by heading span, and that is this
file's only hard bound.

**Repair (V10 A1, under the maintainer's `启动 V10，只做 A 项`).** V7 set a soft cap at V6's 88
prose lines, allowed an exceedance only when the Phase 5 report named a V6 rule that was never
executed, and allowed growth only in §5 and §3. V7 measured 154 lines / 98 prose: it named such a
rule — `V6_PROMPT.md` §7's "an implementation unit ships the change, its guard, its plant and its
readings in one named commit", which neither V6 implementation unit did — but its added lines sit in
§6 as well as §5, so the growth clause was not met. `V7_LEDGER.md` records H6 as **partial** for that
reason, and §5's H6 row is left unamended; both are historical readings, not live rules. A bound
whose author must argue an escape clause to stay inside it is not a bound, so the soft cap and the
growth clause are withdrawn as gates. The standing rule: **431 is the only hard bound**; V6–V9
measured 146 / 88, 154 / 98, 161 / 107 and 164 / 112, and those are **reported reference figures, not
gates** — a later file may exceed them, prints its own measurement beside them in Phase 5 and names
the sections that grew. Exceeding a reference is reported, not failed; exceeding 431 fails the
series.
