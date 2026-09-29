# Phase 14 — the checks Phase 13 wrote down but did not enforce

Date: 2026-09-29. Predecessor: Phase 13 (`phase-13-two-factor-bound.md`). No `PROJECT_SPEC.md` phase
number: this phase answers the technical-debt list Phase 13 published in its own §8, plus the class of
defect its findings 30 and 31 describe. Repository version is unchanged (`1.3.0`); the tag `v1.3.0`
still names `f4c1e9ef9e23`, and nothing here is claimed to be in that release.

## 1. Completed

1. **Extension-surface parity** — `tests/python/test_extension_surface_parity.py`. The pybind
   registration source is read as a contract and the imported binary as evidence, in both directions:
   a declared name missing from the binary is the stale-build signature that bit Phase 13 twice, and a
   binary name missing from the source is API the repository no longer declares. Six tests, four of
   them negative controls.
2. **Analysis-note figure ownership** — the Phase 12 note had never been read by a test. It now is,
   and the first read found three defects in it (audit finding 32, limitation #77), all corrected:
   a stale crossing figure, a headline fitted slope that no artifact computes, and a sentence that read
   a regression's standard error as a bound on accuracy.
3. **A coverage ratchet** — every file in `docs/analysis/` must be named by a test that reads it, so a
   third worked analysis cannot be born unowned the way the first two were.
4. **The architecture document described a package that never existed.** `docs/architecture.md` named
   `python/quantrisk/analytics/` in its layer table and in its layout block; the facades are one module
   per domain (`pricing.py`, `risk.py`, `portfolio.py`, `stress.py`, …), and no `analytics/` package was
   ever created. The layout is now written as what is there, the three departures from the
   `PROJECT_SPEC.md` §6 target are stated with their reasons, and
   `test_every_path_the_architecture_document_declares_exists` parses the block (expanding brace groups,
   rejoining wrapped ones) and fails on any path missing from the tree.
   `test_documents_that_count_the_paper_chapters_agree_with_the_source` did the same for the chapter
   count, which two release notes gave as thirteen against twelve numbered `\section` commands.
5. **`CONTRIBUTING.md`**, which the §6 target structure listed and this repository never wrote: the
   environment traps, the gate order, the regeneration discipline and the rules that are enforced by
   tests rather than requested in prose.
6. **A rounding inconsistency across seven documents** — the predicted remainder zero printed as
   `21.1446` (truncated) in five and `21.1447` (rounded) in two. All seven now print the rounded value,
   which is what the artifact's `0.21144665599988494` yields at four decimals.

## 2. Mathematical assumptions

None new. The phase changes no model, no formula and no tolerance. It does correct one *statistical*
reading: a fitted slope's standard error quantifies residual scatter, and where the residuals are
dominated by systematic terms (a fourth-order mixture at the top of the fit window, cancellation noise
at the bottom) the estimate can sit many standard errors from theory while converging toward it. The
note now states the claim as the convergence of the published window sequence, which is the field the
experiment actually publishes (`slope_converges_to_theory_as_the_window_shrinks`).

## 3. Files changed

| File | Change |
| --- | --- |
| `tests/python/test_extension_surface_parity.py` | new — bindings-vs-binary parity, six tests |
| `tests/python/test_linearisation_bound.py` | new figure-owner test and its non-vacuity probe |
| `tests/python/test_artifact_metadata.py` | new analysis-note coverage guard, new architecture-path guard, new chapter-count guard; the limitation-count guard already covers the fifth counting document |
| `docs/architecture.md` | §5 rewritten to the actual tree with the three §6 departures named; the phantom `analytics/` removed from the layer table |
| `CONTRIBUTING.md` | new — environment, gate order, regeneration discipline, enforced rules |
| `docs/analysis/delta_gamma_error_bound.md` | P1 rewritten onto published windows; crossing figures corrected |
| `docs/limitations.md` | item 77 |
| `docs/integrity_audit.md` | finding 32 |
| `docs/validation_matrix.md`, `docs/findings.md`, `docs/interview_defense.md`, `README.md`, `docs/release_notes_v1.3.0.md`, `paper/technical_report.tex` | the `21.1446 → 21.1447` standardisation and the limitation count |

## 4. Tests executed

400 pytest with the `oracles` extra (331 collected without it, the same four oracle-gated modules
dropping out at import); 198 CTest, 547,845 assertions in 197 Catch2 cases — unchanged, because no C++
source moved. The benchmark suite is unchanged at 14/14 and no experiment output changed, so
`evidence/manifest.json` needed a re-freeze only for the rebuilt `technical_report.pdf`.

New tests, and how each was shown to be capable of failing:

| Guard | Falsification |
| --- | --- |
| bindings/binary parity | the `black_scholes_vol_cross_derivatives` registration was deleted from `bindings/python_bindings.cpp`; two tests went red, and the file was restored byte-identical (`shasum` compared) |
| stale-binary direction | the live surface was shrunk by one name in-process; the comparator reports "declared, absent from the binary" and not the reverse |
| comparator unit probes | missing-name, extra-name, dunder and enum-`name`/`value` cases — five assertions on synthetic surfaces |
| parser non-vacuity | counts floored (statements, functions, classes, members) and the newest Phase 13 types required by name, so a silent parser cannot pass |
| note figure owner | four perturbations of the note — re-inserting the historic `94.5456`, re-truncating `21.1447`, moving a bound ratio, dropping a sequence item — each caught |
| note coverage ratchet | an unguarded `docs/analysis/_unguarded_probe.md` made the guard fail; removing it restored green |

## 5. Exact test results

Every line is the tool's own output on this commit, not an inference from an earlier run:

```
ruff check .                          All checks passed!
ruff format --check .                 120 files already formatted
mypy python/quantrisk                 Success: no issues found in 23 source files
mypy <the three test files touched>   Success: no issues found in 3 source files
clang-format (bindings/cpp/tests)     clean
pytest -q                             400 passed
ctest --preset dev                    100% tests passed out of 198
verify_evidence_manifest.py           76 OK, 0 CHANGED / 0 VOLATILE / 0 MISSING
```

The benchmark suite was **not** re-run, because no experiment or benchmark source changed: the last
execution is Phase 13's `14/14 executed and passed, 0 failed, 0 skipped`, and `verify_evidence_manifest.py`
above is what says the committed outputs are still the ones the tree produced. `quantrisk validate`
was last run at that revision too, at 7/7.

## 6. Numerical validation

No new numerics. The corrections are: crossing spot `94.5456 → 94.5487` and move `5.4544 % →
5.4513 %`, both read off `headline.aggregate_speed_crosses_zero_at_spot` =
`94.5487358657606` and `…_at_move` = `0.05451264134239392`; and the fitted-slope paragraph, which now
quotes the five published windows (`2.971017 → 2.990908 → 2.996030 → 2.998211 → 2.998785` down,
`3.025281 → 3.008734 → 3.003902 → 3.001776 → 3.001209` up) instead of an unpublished pooled fit. The
deviations from theory are 52.3 and 59.0 standard errors in the widest windows — stated, not smoothed.

## 7. Remaining limitations

Nothing new is claimed and nothing existing is weakened. The limitation register grows by one entry
(#77) recording the class rather than the incident. Phase 13's items 67–76 still describe the bound's
scope, and its §8 list is now down to two unpaid lines.

## 8. Technical debt

Paid here: the CI-mechanical extension-surface check (Phase 13 §8 item 3) and the
artifact-vs-prose guard for `docs/analysis/` (item 1, now covered for both notes by a ratchet rather
than by good intentions).

Still unpaid, deliberately: **promoting the mutation harness into `scripts/`**. It has been hand-rolled
three phases running, and a repo tool version would need its own gate — it compiles deliberately wrong
C++, so it must be excluded from the ordinary build and re-checked each time the core changes, which is
a design problem rather than a chore. Doing it halfway would produce a script that rots exactly like the
prose this phase guarded. It stays on the list with that reason attached.

## 9. Gate

| Check | Result |
| --- | --- |
| Audit → Research → Plan → Implement → Verify → Report, in order | yes; the audit was Phase 13's §8 list, and the plan changed once — the note-owner test was written first and found the defects that the plan then recorded |
| Correctness over features (§2.1) | no new model, no new API; three guards and one corrected derivation |
| Own implementation (§2.2) | untouched |
| Nothing fabricated (§4) | every figure the corrected note prints is re-formatted from the artifact by test, including the two it got wrong |
| Failed experiments kept (§4) | the pooled-fit figure is published as an owner-less number that was removed, with the reason, in finding 32 and #77 |
| Tolerances not lowered (§4) | no tolerance in the tree was touched by this phase |
| Every README number traceable (§4) | improved: `docs/analysis/` is now covered by owner tests and a ratchet |
| Cost $0 (§3) | no dependency, no service |
| Tests pass locally | 400 pytest, 198 CTest, 76 artifacts OK, ruff/format/mypy (both the CI scope and the three files this phase touched) and clang-format clean, each quoted from its own run above |
| Tests pass on the runner | `36536998342` on `10dd8f3` — `completed / success`, all three jobs, the offline lane reading `328 passed, 4 skipped` and confirming the derived collection figure quoted above; `100% tests passed out of 198`; `suite: 14/14 executed and passed` |
| Version and release | `1.3.0` unchanged, `v1.3.0` still at `f4c1e9ef9e23`; a release bump would invalidate every committed artifact's recorded version, so it waits until the next real feature |
