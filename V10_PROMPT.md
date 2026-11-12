# V10_PROMPT.md — the rails for the V10 series

V10 starts at `ca94a2c153d677e1d6b2f174e105c73efc4d57b2`, the terminal entry of V9. It is a
**single-unit series** with one finding, A1: the repair of `V7_PROMPT.md` §8. The maintainer named
that unit explicitly; nothing in this file widens it. Every number below is a reading taken at that
tip, and every claim about an earlier series is a pointer to the ledger or handoff that measured it.
`V10_LEDGER.md` is the cross-session state; this file is the rail set.

## 0. Status, premises and termination

**What is closed.** V1 is `PROJECT_SPEC.md` (historical, priced lock). V2 is `REFACTOR_PROMPT.md`
(terminated, `REFACTOR_LEDGER.md`). V3 closed its eight §12 deliverables, V4 the V3 carryover, V5
F1–F7, V6 G1–G6, V7 H1–H7 with H6 partial and named, V8 H1–H6, and V9 D1 — the final-tip census
frozen as a verifiable ancestor attestation. No earlier file is amended by V10 except the one
section named in §5. `V9_LEDGER.md` Phase 5 §4 item 1 records that A was not taken and §6 item 7
records that V3–V9 left no code-level residue; both are historical readings and are not rewritten.

**Three premises, measured at `ca94a2c`.** If a fresh reading contradicts one, stop and write the
contradiction into the Phase 5 report before touching anything.

1. **The published chain is frozen.** `v1.9.0` is tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`; release `424060629` holds four assets created
   `2026-10-26T09:35:41Z`; `evidence/manifest.json` holds 95 entries and verifies intact.
2. **The pin is a guard, not a sentence.** `artifact_revision_gap` declares
   `pinned_revision 17df062040b8`; `artifact_revision` prints `gap 0`, `pin_holds true`,
   `matches_tip false` on the committed artifact and exempts a fresh upload naming the tip.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** Both are honest at this
   tip because their reasons are printed. V10 re-reads them before citing them.

**Termination condition.** V10 ends when A1 is fixed — `V7_PROMPT.md` §8 states 431 as the only hard
bound, reports V6–V9's figures as references rather than gates, and leaves `V7_LEDGER.md`'s H6
verdict and §5's H6 row unamended — when the Phase 5 report and archival confirmation are committed
and pushed, and when both pushes' CI have been attributed from the API. V10 runs no census: it
changes no plant target, and a census here would produce another session reading rather than a
checkable one.

## 1. What V10 inherits, and what it may not re-derive

`V9_LEDGER.md` Phase 5 §4 (twelve items) and §6 (seven items) are the starting agenda. The maintainer
selected **A** — repairing `V7_PROMPT.md` §8 — and excluded B (reopening the sweep vantage) and C
(a declarative re-run of the evidence chain). V10 takes no other item.

**Why A is possible now.** `V7_PROMPT.md` §6 makes editing that file its own scope unit needing its
own verbatim approval, and V8 §4 item 2 and V9 §1 refused it partly because rewriting the rule could
erase the partial finding. The maintainer's sentence is that approval. The repair therefore keeps
the finding: `V7_LEDGER.md` H6 stays `partial`, §5's H6 row stays unamended, and §8's new text states
what the old rule was and why it failed before stating the standing rule.

V10 adds exactly two tracked paths (`V10_PROMPT.md`, `V10_LEDGER.md`) and edits one section of a
third (`V7_PROMPT.md` §8). No source, policy asset, test, workflow, manifest, artifact, tag or
release asset moves. The formatter corpus moves from 242 to 244 with both differences empty, and
Phase 5 prints that delta.

## 2. Facts Protocol

1. **A reading is a command and its output, at a revision.** Nothing enters a ledger entry without
   both.
2. **No outcome before the tool reports it.** A push, a run and a job are `unknown` until the API
   says otherwise; `gh run watch` returning 0 on a transport-layer success is not a verdict.
3. **Attribute every CI reading to its run, attempt, runner and environment.**
4. **A historical reading is not rewritten.** `V7_LEDGER.md`'s H6 `partial` verdict and its 154 / 98
   measurement stay as printed; so do `V9_LEDGER.md` §4 item 1 and the two earlier ledgers' sentence
   that `V7_PROMPT.md` was untouched — those were readings at their tips, not standing claims. V10
   changes the *rule*, not the reading, and §8's new text says so.
5. **A rule that cannot be satisfied is not a bound.** A1's proof is not an assertion that the new
   text is better: it is a fresh measurement of `V7_PROMPT.md` before and after, the whole gate set
   on both sides, and the deltas printed.
6. **State the evidence limit.** V10 changes prose only. It does not make the census re-runnable,
   does not gate the D1 reading, and does not reopen any vantage; none of those is claimed.
7. **Every printed census verdict carries its vantage on the same line** (`development-side vantage;
   the sweep has no CI lane`), as `V8_LEDGER.md` §6 item 5 requires of any new document.

## 3. Lanes and policy assets at `ca94a2c`

| asset | reading |
|---|---|
| registry tasks / suite members | 19 / 19, `registry_parity` mismatch empty |
| plants | **195**; the last full census is `195/195` at `5ec3fab` (development-side vantage; the sweep has no CI lane) |
| ceiling keys | **15** — 13 `ok`, 2 `SKIP` |
| manifest | 95 entries, `Evidence is intact.` |
| formatter corpus | **242 / 242**, both differences empty |
| pytest nodes | 560 collected / 491 offline, `collection_errors 0` |
| named CI steps | **34** |
| readings at `gap 0` | `docs_rederivation`, `lanes_documented_vs_executed`, `with_extras_census`, `artifact_revision`, `formatter_census`, `registry_parity` |

The lanes are those `.github/lane_contract.md` declares, plus the local static gates, the manifest
verifier, the collector readings and the full `pytest -q`. The sweep and the installed-surface proof
are development-only by permanent decision (§4). Every lane in the Phase 5 table names its revision
and environment.

## 4. The sweep and installed-surface vantages stay closed

`V6_PROMPT.md` §4 made the sweep's development-only decision permanent; V7 §4, V8 §4 and V9 §4 kept
it. V10 performs no harness redesign, gives neither `SKIP` a runner-side verdict, adds no CI lane for
the installed-surface proof, and does not promote the census verdict to a gate. A prose repair is not
an occasion to reopen any of them.

## 5. The candidate finding

| id | finding | `check:` |
|---|---|---|
| A1 | `V7_PROMPT.md` §8 sets a soft cap at V6's 88 prose lines, an escape clause requiring the Phase 5 report to name a V6 rule that was never executed, and a growth clause ("only in §5's finding table and §3's lane inventory") that the file it governs does not satisfy; V7 measured 154 / 98 and recorded H6 as **partial** rather than repair it | `V7_PROMPT.md` §8 states 431 as the only hard bound, names the old soft cap and growth clause as withdrawn gates with the reason, and reports V6–V9's 146 / 88, 154 / 98, 161 / 107 and 164 / 112 as reference figures; `V7_LEDGER.md`'s H6 `partial` verdict and §5's H6 row are byte-identical to `ca94a2c`; the V10 diff touches only `V7_PROMPT.md` §8 plus the two V10 files; `--check-ceilings` still prints 15 keys, `runner --list` 195, the workflow 34 named steps, and `docs_rederivation gap 0` |

Items B and C are refused with evidence in Phase 5 §4, not taken as findings. V10 has no A2.

## 6. One scope unit per approval

- **The maintainer's approval, verbatim.** `启动 V10，只做 A 项` (2026-11-12). This is a
  **single-unit** approval: it covers A1, the Phase 0 entry, the implementation, the Phase 5 report,
  the terminal entry, the two named pushes and their CI attribution. It is recorded verbatim in the
  V10 Phase 0 entry before any outward action. The V9 single-unit approval is spent and is not
  reused.
- **Not authorised by that sentence:** items B and C; editing `V7_PROMPT.md` outside §8; editing any
  other prompt or ledger (`PROJECT_SPEC.md`, `REFACTOR_PROMPT.md`, `V3_PROMPT.md` … `V9_PROMPT.md`,
  `V3_LEDGER.md` … `V9_LEDGER.md`); a harness redesign that reopens §4; a declared re-run of the
  evidence chain; a new census; a tag movement or release asset replacement; a new CI lane, plant,
  guard or ceiling key; or a third push. Any of those needs a new verbatim approval.
- Outward actions — push, PR, release, issue, comment — need the maintainer's approval for that
  case, recorded verbatim in that unit's Phase 0 entry. Within V10 the sentence above is that case
  for the two named pushes.
- A Phase 0 entry states the revision, vantage, re-measured baseline, the finding taken, what the
  unit excludes, the approval verbatim, the number of pushes and what each carries.
- The ledger's terminal entry records the implementation tip's CI with its run, attempt, runner and
  step counts. The terminal commit's own CI is read after the second push and reported in the
  session handoff.
- Editing this prompt is itself a scope unit and needs its own verbatim approval. No unit may amend
  this section to widen its own authority.

## 7. Phase 0, Phase 5, Definition of Done

**Phase 0** re-counts the archive against the tip that is actually pushed, names the vantage and the
platform's tag/release state, re-measures the three premises, chooses A1, states the exclusions and
records the approval. It ships as its own commit before any other file is touched.

**V10 has one implementation commit**: it carries the repaired §8, the before/after measurements and
the note that no reading was rewritten; no source, policy asset, test or workflow file moves. The
first push carries that commit together with Phase 0 and the Phase 5 report; the second carries the
terminal entry. Both pushes are attributed from the API.

**Phase 5** delivers the eight `V3_PROMPT.md` §12 items: an evidence ledger; the liveness table
re-evaluated at the report's tip; the ceilings file's final state with review notes; an honestly
non-empty deliberately-not-done list; a premises audit; a series handoff; a per-lane verification
table with revision **and** environment for every lane; and an archival confirmation requiring a
clean tree with `HEAD` equal to `origin/main`, every V10 commit proven an ancestor of the remote, CI
attributed for every commit, registers and documents re-counted, tags/releases/assets re-read from
the platform, and no stray instrument tracked or left on disk.

**Definition of Done.** All three premises re-measured; A1 fixed with the before/after measurement
printed; `V7_LEDGER.md` and §5's H6 row unchanged; every document quoting a moved count re-derived in
the same commit; the Phase 5 report and archival confirmation committed and pushed; CI read for
every commit in the range; and every ledger entry recording what was run, what it printed and what
was decided.

## 8. Size ratchet

`V3_PROMPT.md` §0 caps its prose sections at 431 lines measured by heading span, and that is V10's
only hard bound. V6 measured 146 / 88, V7 154 / 98, V8 161 / 107 and V9 164 / 112; all four are
**reported reference figures, not gates**, for the reason A1 repairs. V10 adds no section beyond
V9's eight, and its Phase 5 report prints its own total and prose lines beside those four figures.
Exceeding 112 is reported, not failed; exceeding 431 fails the series.
