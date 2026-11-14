# V13_PROMPT.md — the rails for the V13 series

V13 starts at `5dfd6bb69924b285114e277a99b51acd583af545`, the V12 terminal entry. It is a
**single-unit series** with one finding, D1: the final-tip census attestation is read by a heredoc in
a ledger, and the reading it prints compares a past revision's counts with today's declaration.
`V13_LEDGER.md` is the cross-session state; this file is the rail set.

## 0. Status, premises and termination

**What is closed.** V1 is `PROJECT_SPEC.md`; V2 is `REFACTOR_PROMPT.md`; V3 closed its eight §12
deliverables, V4 the V3 carryover, V5 F1–F7, V6 G1–G6, V7 H1–H7 with H6 partial and named, V8 H1–H6,
V9 D1, V10 A1, V11 B1 and V12 C1. No earlier file is amended by V13 except the files its finding
reaches, named in §5.

**Four premises, measured at `5dfd6bb`.** If a fresh reading contradicts one, stop and write the
contradiction into the Phase 5 report before touching anything.

1. **The published chain is frozen.** Tag `d9deb7f…` → `b2dda33…`; release `424060629` holds four
   assets; `evidence/manifest.json` holds 95 entries and verifies intact.
2. **Both former `SKIP` keys are measured on a runner.** `mutation-census` and `installed-surface`
   are green lanes; `--check-ceilings` prints 15 keys, two `SKIP`s on a vantage that ran neither lane.
3. **The attestation exists and is readable.** `V9_LEDGER.md` carries exactly one marked block,
   `quantrisk.final_tip_census_attestation/v1`, naming `5ec3fab…`, which is a strict ancestor of
   `HEAD`.
4. **The plant list is 195.** V13 adds no plant, so the attestation's count stays consistent with
   the declaration.

**Termination condition.** V13 ends when a tracked reader decides the attestation on a runner whose
checkout carries full history, when the lane contract names that job and step, and when both pushes'
CI are attributed from the API.

## 1. The finding

**D1.** `V9_LEDGER.md` fixes the V8 census at `5ec3fab` and records it between two markers. Its only
reader is a shell heredoc printed in the same ledger. Two defects follow:

1. **No runner can fail on it.** The reading runs where a person pastes it, which is the shape
   `V5_PROMPT.md` §1 forbids: a claim whose falsification depends on somebody remembering.
2. **It decides a past claim with a present count.** The heredoc compares
   `verdict_rows.ok_caught` with `runner --list` **at HEAD**. `V9_LEDGER.md` §6 item 4 forbids
   refreshing the attestation to a newer tip; a reader that requires today's number forces exactly
   that refresh the first time any unit adds a plant. The two rules cannot both hold, so one must go.

V13 keeps the half that is still true — the revision is a real commit, it is a strict ancestor, and
the block agrees with itself — and drops the time-dependent comparison.

## 2. What the unit carries, and what it excludes

**Carries.** `tools/verify_final_tip_census.py`, a step in `build-and-test` (the job with
`fetch-depth: 0`), the lane-contract row, a paragraph in `CONTRIBUTING.md`, one falsification block
inside an existing test, and this series' two files.

**Excludes.** No plant, no ceiling key, no new job, no change to `lint`'s shallow vantage, no change
to the attestation itself (`V9_LEDGER.md` is read, never edited), no tag or release movement, and no
work on C (K5 refuses it).

## 3. One scope unit per approval

- **The maintainer's approval, verbatim.** `好的，继续` (2026-11-14), given in answer to the writer's
  proposal in the preceding turn: *"下一个单元就做 D1；它需要一句新的范围句"*. The proposal names the
  unit; the reply assents to it. Both are recorded here so a reader can see what was approved and by
  reference to what.
- **Not authorised:** C (K5), a new plant or ceiling key, editing `V9_LEDGER.md`'s attestation, any
  earlier prompt or ledger, a tag movement, a release asset replacement.
- Pushes: the first carries Phase 0, the implementation and the Phase 5 report; the second carries
  the terminal entry; a third is reserved for repairing a red run of either, under the same approval.

## 4. Definition of Done

1. `tools.verify_final_tip_census` reads `executed` in `.github/lane_contract.md`, naming
   `build-and-test :: Final-tip census attestation`.
2. A push prints `PASS: V9_LEDGER.md attests 5ec3fab… as a strict ancestor of …`, attributed to run,
   attempt, runner and step counts.
3. The reader refuses a wrong schema, a malformed revision, a missing object, a self-reference, a
   non-ancestor, counts that disagree with the summary, a non-zero exit, and a missing evidence
   limit — each exercised in the suite.
4. Static gates green; formatter census two-sided empty; the pin, tag, release and manifest unmoved.
5. Every push's CI attributed from the API.

## 5. Size ratchet

431 lines is the only hard bound; V12 measured 144 / 97 and that is a reference, not a gate.
`V13_PROMPT.md`'s own figures are measured in Phase 0.
