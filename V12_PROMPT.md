# V12_PROMPT.md — the rails for the V12 series

V12 starts at `6eda1fa29ccf537327a0e62bbd6f1afb1a84d325`, the fourth push of V11. It is a
**single-unit series** with one finding, C1: the installed-surface vantage is development-only, so
the last key the ceilings file skips can never fail on a runner. Nothing in this file widens it.
`V12_LEDGER.md` is the cross-session state; this file is the rail set.

## 0. Status, premises and termination

**What is closed.** V1 is `PROJECT_SPEC.md` (historical, priced lock). V2 is `REFACTOR_PROMPT.md`
(terminated, `REFACTOR_LEDGER.md`). V3 closed its eight §12 deliverables, V4 the V3 carryover, V5
F1–F7, V6 G1–G6, V7 H1–H7 with H6 partial and named, V8 H1–H6, V9 D1, V10 A1, and V11 B1 — the
mutation sweep promoted to a runner-side lane. No earlier file is amended by V12 except the files
its finding reaches, named in §5.

**Four premises, measured at `6eda1fa`.** If a fresh reading contradicts one, stop and write the
contradiction into the Phase 5 report before touching anything.

1. **The published chain is frozen.** `v1.9.0` is tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`; release `424060629` holds four assets sized
   2,978 / 55,780 / 145,672 / 1,005,786 bytes; `evidence/manifest.json` holds 95 entries and
   verifies intact.
2. **The pin is a guard, not a sentence.** `artifact_revision_gap` declares
   `pinned_revision 17df062040b8`; `artifact_revision` prints `gap 0`, `pin_holds true`,
   `matches_tip false` on the committed artifact.
3. **One key is still development-only.** `--check-ceilings` prints 15 keys, 14 `ok`, 1 `SKIP`;
   the skip is `installed_user_identity_mismatch`, and its `corpus` names a second environment as
   the missing precondition.
4. **The sweep's vantage is closed and stays closed.** V11 put `quantrisk.verification.runner` in
   the workflow as `mutation-census`; V12 neither reopens nor re-measures it.

**Termination condition.** V12 ends when the installed surface is proved on a runner — a wheel built
from the pushed tree, installed into an environment outside the checkout, probed for identity,
registry parity, one offline study and one refusal — when the ceiling key is measured from that
lane's verdict while the lint vantage still prints `SKIP` with its reason, when the lane contract
names the job and step, and when every push's CI is attributed from the API.

## 1. What V12 inherits, and what it may not re-derive

`V11_LEDGER.md`'s handoff and this file's §5 are the agenda. V12 may not re-derive: 195 plants, 15
keys, 12 changed paths, the tag and release facts, or the census reconciliation. Each is a reading
taken at `6eda1fa`.

## 2. Facts Protocol

- Every number states the command and the revision that produced it.
- A reading is taken once per tip. Re-reading a failed command is allowed; re-reading a green one to
  get a different answer is not.
- A transport failure — TLS, EOF, 429 — is `unknown`, never a verdict. Re-read the platform state,
  then retry once.
- CI is attributed to run, attempt, runner and step counts, read from the API. A watcher's exit code
  is a tool conclusion, not the attribution.
- A verdict that cannot be taken prints as absent with its reason, never as zero.

## 3. Lanes at `6eda1fa`

| Lane | Command | Where |
|---|---|---|
| static checks | `ruff check .`, `ruff format --check .`, `mypy` | `lint` |
| ceilings | `tools.inventory_orphan_code --check-ceilings` | `lint`, `mutation-census` |
| evidence chain | `tools.verify_evidence_manifest` | `lint` |
| Python and C++ tests | `pytest -q`, `ctest` | `build-and-test`, `macos-native` |
| benchmark suite | `tools.run_benchmark_suite` | `benchmark-suite` |
| mutation census | `quantrisk.verification.runner --all` | `mutation-census` |
| installed surface | `tools.verify_installed_surface` | **none** |

The last row is the finding. The probe needs a wheel, an environment outside the checkout, and one
study run; the ceilings file therefore records it as `may_be_unmeasured` and prints `SKIP`.

## 4. What the lane must do, and what it may not do

1. **Build the wheel from the pushed tree**, not from a cache: `uv build --wheel` in the checkout.
2. **Install only that wheel** into a fresh environment under `$RUNNER_TEMP`, with no editable
   install and no checkout on `sys.path`.
3. **Run the probe there** and write its JSON verdict outside the checkout, so the ceiling gate can
   read the five readings it produced.
4. **Adjudicate on the same runner**: `--check-ceilings` with the verdict in the environment prints
   `ok installed_user_identity_mismatch: 0`, and a missing reading, a non-zero exit, or an import
   path naming the checkout reddens it.
5. **Keep the lint vantage honest.** It does not run this lane, so it keeps printing `SKIP` with the
   corpus reason; a `0` there would be a claim about a probe it did not run.

What it may not do: change a plant, an anchor, the census reconciliation, the pin, the tag, the
release assets or the evidence chain; add a plant or a ceiling key; reopen the sweep vantage; or
promote the D1 ancestry reading.

## 5. The finding, and the files it reaches

**C1.** `installed_user_identity_mismatch` is the last key the ceilings file skips. Its corpus says
the probe cannot run on a runner because it installs a second environment. That was true when the
probe was written as a laptop instrument; it is not true of a lane that owns a temporary directory.
Until this unit, a wheel whose import resolves into the checkout — the editable-install shape the
probe exists to catch — would ship green.

The finding reaches: `tools/verify_installed_surface.py` (a `--json-out` verdict), 
`tools/inventory_orphan_code.py` (the reading and the metric), `tools/refactor_ceilings.json` (the
key's corpus and verdict), `.github/workflows/ci.yml` (the lane), `.github/lane_contract.md` (the
declaration), `CONTRIBUTING.md` (the lane-bearing document that claims it),
`tests/python/test_mutation_suite.py` (the falsification), and this series' own two files.

## 6. One scope unit per approval

- **The maintainer's approval, verbatim.** `继续按你此前提出的思路和建议方案执行，我已全部授权，无需再次确认。请持续推进剩余工作，保持与既定方向一致，并在关键节点简要说明已完成的内容、当前进展及下一步计划；如遇需我决策的分歧，再单独提出。`
  (2026-11-14). It points at the handoff V11 left: the installed-surface key is the last
  development-only rail. V12 takes that item and nothing else.
- **Not authorised by that sentence:** item C (a declarative re-run of the evidence chain — K5
  forbids replacing a published asset); promoting the D1 ancestry reading; reopening the sweep
  vantage; a new plant, ceiling key or guard; editing `PROJECT_SPEC.md`, `REFACTOR_PROMPT.md`,
  `V3_PROMPT.md` or any earlier series' files; a tag movement; a release asset replacement.
- Outward actions — push, PR, release, issue, comment — need the maintainer's approval for that
  case. The sentence above is that approval for this unit's pushes; each is named in Phase 0 with
  what it carries, and a red run may be repaired inside the same unit rather than escalated.
- A Phase 0 entry states the revision, vantage, re-measured baseline, the finding taken, what the
  unit excludes, the approval verbatim, the number of pushes and what each carries.
- Editing this prompt is itself a scope unit. No unit may amend this section to widen its own
  authority.

## 7. Phase 0, Phase 5, Definition of Done

**Phase 0** records the revision, the vantage, the re-measured baseline, C1 as the finding taken, the
exclusions, the approval verbatim, and the pushes: the first carrying Phase 0, the implementation and
the Phase 5 report; the second carrying the terminal entry; a third reserved for repairing a red run
of either.

**Phase 5** reports the eight `V3_PROMPT.md` §12 deliverables, the lane's job and steps, the key's
two vantages printed side by side, the probe's five readings as the runner printed them, what moved
and what was deliberately left alone, and the series handoff.

**Definition of Done.**

1. `tools.verify_installed_surface` reads `executed` in `.github/lane_contract.md`, naming the job
   and step the workflow contains.
2. A push runs the probe on a runner and prints all five readings, attributed to run, attempt,
   runner and step counts.
3. `installed_user_identity_mismatch` is measured from that verdict, and the lint vantage still
   prints `SKIP` with its reason.
4. Static gates green; formatter census two-sided empty; the pin, tag, release and manifest unmoved.
5. Every push's CI attributed from the API, with no failed step left unexplained.

## 8. Size ratchet

431 lines is the only hard bound. V11 measured 168 / 119; that is a reference, reported, not a gate.
`V12_PROMPT.md`'s own figures are measured in Phase 0 and reported in Phase 5.
