# V11_PROMPT.md — the rails for the V11 series

V11 starts at `3725dfa69b3c7180d319ea0c692d2028955d55df`, the terminal entry of V10. It is a
**single-unit series** with one finding, B1: the mutation sweep's vantage is development-only, so no
runner can fail when a plant stops rejecting its guard. The maintainer named that unit explicitly;
nothing in this file widens it. Every number below is a reading taken at that tip, and every claim
about an earlier series is a pointer to the ledger or handoff that measured it. `V11_LEDGER.md` is
the cross-session state; this file is the rail set.

## 0. Status, premises and termination

**What is closed.** V1 is `PROJECT_SPEC.md` (historical, priced lock). V2 is `REFACTOR_PROMPT.md`
(terminated, `REFACTOR_LEDGER.md`). V3 closed its eight §12 deliverables, V4 the V3 carryover, V5
F1–F7, V6 G1–G6, V7 H1–H7 with H6 partial and named, V8 H1–H6, V9 D1, and V10 A1 — the repair of
`V7_PROMPT.md` §8. No earlier file is amended by V11 except the files its finding reaches, named in
§5. `V10_LEDGER.md` Phase 5 §3 item 3 records that B was not taken and §6 item 3 repeats the
refusal; both are historical readings and are not rewritten.

**Four premises, measured at `3725dfa`.** If a fresh reading contradicts one, stop and write the
contradiction into the Phase 5 report before touching anything.

1. **The published chain is frozen.** `v1.9.0` is tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`; release `424060629` holds four assets created
   `2026-10-26T09:35:41Z`; `evidence/manifest.json` holds 95 entries and verifies intact.
2. **The pin is a guard, not a sentence.** `artifact_revision_gap` declares
   `pinned_revision 17df062040b8`; `artifact_revision` prints `gap 0`, `pin_holds true`,
   `matches_tip false` on the committed artifact and exempts a fresh upload naming the tip.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** At this tip
   `--check-ceilings` prints 15 keys, 13 `ok`, 2 `SKIP`, 0 `FAIL`; both skips name
   `precondition absent` and quote their `corpus`.
4. **No clock is inherited.** `V10_LEDGER.md` §6 item 7 states V3–V10 left no code-level residue;
   V11 quotes that as a reading at `3725dfa`, not as a licence to widen this unit.

**Termination condition.** V11 ends when the sweep runs on a runner as a declared lane, in a
detached worktree, with a machine-readable verdict that the ceiling gate adjudicates; when the
`quantrisk.verification.runner` row in `.github/lane_contract.md` reads `executed` with the job and
step that run it; when the Phase 5 report and terminal entry are committed and pushed, and both
pushes' CI have been attributed from the API; and when a census has been read at the terminal tip,
on the runner, with its run, attempt, runner and step counts quoted.

## 1. What V11 inherits, and what it may not re-derive

`V10_LEDGER.md` Phase 5 §4 (twelve items) and §6 (seven items) are the starting agenda. The
maintainer's approval names one item, and only one: §6 item 3's first sentence. The other items stay
as they are, including the two `SKIP` keys the reversal does not reach.

V11 may not re-derive: the 195 plants, the 15 keys, the 34 CI steps, the 95 manifest entries, the
560 collected nodes, the 244 formatter files, or the tag and release facts. Each is a reading taken
in Phase 0 at `3725dfa` and re-read at each tip it reports.

## 2. Facts Protocol

- Every number states the command and the revision that produced it. A number quoted from an earlier
  ledger names that ledger and its tip.
- A reading is taken once per tip. Re-reading a failed command is allowed; re-reading a green one to
  obtain a different answer is not.
- A transport failure — TLS, EOF, 429, a truncated API body — is `unknown`, never a verdict. Re-read
  the platform state, then retry the same call once.
- CI is attributed to run, attempt, runner and step counts, read from the API. `gh run watch`'s exit
  code is a tool conclusion, not the attribution.
- A verdict that cannot be taken is printed as absent with its reason, never as zero.

## 3. Lanes and policy assets at `3725dfa`

| Lane | Command | Where |
|---|---|---|
| static checks | `ruff check .`, `ruff format --check .`, `mypy python/quantrisk tools` | lint job |
| ceilings | `tools.inventory_orphan_code --check-ceilings` | lint job |
| docs re-derivation | `tools.inventory_orphan_code --reading docs_rederivation` | lint job |
| evidence chain | `tools.verify_evidence_manifest` | lint job |
| Python and C++ tests | `pytest -q`, `ctest` | build-and-test, macos-native |
| benchmark suite | `tools.run_benchmark_suite` | benchmark-suite |
| mutation sweep | `quantrisk.verification.runner` | **none** — `dev-only` in `.github/lane_contract.md` |

The last row is the finding. Its reason in the contract is mechanical: the sweep rewrites tracked
files one at a time and writes gitignored scratch into the checkout, so a key computed from its
summary line cannot fail on the runner that evaluates it.

## 4. What the redesign must do, and what it may not do

`V6_PROMPT.md` §4 made the development-only vantage permanent and named the only way back: a unit
whose Phase 0 states that it is redesigning the harness so the sweep no longer touches tracked files,
carrying its own approval. This section is that statement, in the terms the harness can prove.

1. **The sweep runs in a detached worktree** created at `$RUNNER_TEMP` from the pushed revision. The
   checkout the runner evaluates is never written: its `git status --porcelain` is read before and
   after, both are recorded in the verdict, and a non-empty either side is a failure.
2. **The verdict is machine-readable and lives outside the checkout.** `--verdict-out` writes the
   revision, the plant count, every plant's status, the non-caught ids and both cleanliness readings.
   The ceiling gate reads that file; the sweep no longer needs a human to transcribe a summary line.
3. **The lane is the gate.** A plant that stops rejecting its guard makes the sweep exit non-zero,
   and makes the ceiling key non-zero, on the runner, without a laptop in the loop.
4. **The harness may not be rewritten to look redesigned.** The 25 plants anchored on `runner.py`
   source lines must still resolve; `--all`, `--only`, `--kind`, `--list` and the printed census line
   keep their current text; the 195 declarations do not move.

What it may not do: touch the C++ mathematics, change a plant's anchor or claim, add or remove a
plant, move the pin, move the tag, replace a release asset, reopen the installed-surface vantage,
promote the D1 ancestry reading, or re-run the evidence chain.

## 5. The finding, and the files it reaches

**B1.** The repository's strongest falsification instrument — 195 plants, each required to make a
named guard go red — is executed only on a development machine. `.github/lane_contract.md` declares
it `dev-only`; `V6_PROMPT.md` §4 made that permanent; `V10_LEDGER.md` §6 item 4 records that no
census was captured at V10's tip. A push that disarmed a guard would be green.

The finding reaches exactly these files: `python/quantrisk/verification/runner.py` (the harness),
`tools/inventory_orphan_code.py` (the reading and the metric), `tools/refactor_ceilings.json` (the
key's corpus and verdict), `.github/workflows/ci.yml` (the lane), `.github/lane_contract.md` (the
declaration), `tests/python/test_mutation_suite.py` (the falsification of the new reading),
`CONTRIBUTING.md` (the lane-bearing document that claimed the sweep and called it not a CI step),
`docs/interview_defense.md` (the command annotation that said there was no CI lane), and this
series' own two files. `docs/reproducibility.md` is deliberately untouched: it never claimed the
sweep, so adding it there would move the lane contract's `claimed_by` set for no reading.

## 6. One scope unit per approval

- **The maintainer's approval, verbatim.** `启动 V11，只做 B 项` (2026-11-13). This is a
  **single-unit** approval: it covers B1, the Phase 0 entry, the implementation, the Phase 5 report,
  the terminal entry, the two named pushes and their CI attribution, and the terminal-tip census the
  new lane produces. It is recorded verbatim in the V11 Phase 0 entry before any outward action. The
  V10 single-unit approval is spent and is not reused.
- **Not authorised by that sentence:** item C (a declarative re-run of the evidence chain — K5
  forbids replacing a published asset); promoting the D1 ancestry reading to a CI gate; reopening
  the installed-surface vantage or flipping `installed_user_identity_mismatch`; a new plant, ceiling
  key or guard; editing `V3_PROMPT.md` … `V10_PROMPT.md`, `PROJECT_SPEC.md`, `REFACTOR_PROMPT.md`
  or any earlier ledger; a tag movement; a release asset replacement; a third push.
- Outward actions — push, PR, release, issue, comment — need the maintainer's approval for that
  case, recorded verbatim in this unit's Phase 0 entry. Within V11 the sentence above is that case
  for the two named pushes.
- A Phase 0 entry states the revision, vantage, re-measured baseline, the finding taken, what the
  unit excludes, the approval verbatim, the number of pushes and what each carries.
- The ledger's terminal entry records the implementation tip's CI with its run, attempt, runner and
  step counts. The terminal commit's own CI is read after the second push and reported in the
  session handoff, and its census line is quoted there.
- Editing this prompt is itself a scope unit and needs its own verbatim approval. No unit may amend
  this section to widen its own authority.

## 7. Phase 0, Phase 5, Definition of Done

**Phase 0** records the revision, the vantage, the re-measured baseline, B1 as the finding taken, the
exclusions above, the approval verbatim, and two pushes: the first carrying Phase 0, the
implementation and the Phase 5 report; the second carrying the terminal entry only.

**Phase 5** reports, at minimum: the eight `V3_PROMPT.md` §12 deliverables; the harness change and
why it is a redesign rather than a wrapper; the lane's job, steps and first run; the ceiling key's
two vantages printed side by side; the 25 anchors that had to keep resolving; the census line at the
implementation tip; what moved and what was deliberately left alone; and the series handoff.

**Definition of Done.**

1. `quantrisk.verification.runner` reads `executed` in `.github/lane_contract.md`, naming the job and
   step the workflow actually contains.
2. A push runs the full census on a runner and prints `195/195 planted defects were rejected by
   their guard.`, attributed to run, attempt, runner and step counts.
3. `plants_not_rejected_by_their_guard` is measured from the lane's verdict, and the lint vantage
   still prints `SKIP` with its reason rather than a zero.
4. The checkout the runner evaluates is clean before and after the sweep, and both readings are in
   the verdict.
5. Static gates green; formatter census two-sided empty; the pin, tag, release and manifest unmoved.
6. Both pushes' CI attributed from the API, with no failed step.

## 8. Size ratchet

431 lines is the only hard bound for this file. V9 measured 164 / 112, V10 161 / 109, and the
repaired `V7_PROMPT.md` 165 / 109; those are references, reported, not gates. `V11_PROMPT.md`'s own
figures are measured in Phase 0 and reported in Phase 5.
