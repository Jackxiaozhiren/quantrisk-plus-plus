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

411 pytest with the `oracles` extra (342 collected without it, the same four oracle-gated modules
dropping out at import); 198 CTest, 547,845 assertions in 197 Catch2 cases — unchanged, because no C++
source moved. The version field inside every artifact is what forced the suite re-run and the
manifest re-freeze recorded in the addendum below; no *result* moved.

New tests, and how each was shown to be capable of failing:

| Guard | Falsification |
| --- | --- |
| bindings/binary parity | the `black_scholes_vol_cross_derivatives` registration was deleted from `bindings/python_bindings.cpp`; two tests went red, and the file was restored byte-identical (`shasum` compared) |
| stale-binary direction | the live surface was shrunk by one name in-process; the comparator reports "declared, absent from the binary" and not the reverse |
| comparator unit probes | missing-name, extra-name, dunder and enum-`name`/`value` cases — five assertions on synthetic surfaces |
| parser non-vacuity | counts floored (statements, functions, classes, members) and the newest Phase 13 types required by name, so a silent parser cannot pass |
| note figure owner | four perturbations of the note — re-inserting the historic `94.5456`, re-truncating `21.1447`, moving a bound ratio, dropping a sequence item — each caught |
| note coverage ratchet | an unguarded `docs/analysis/_unguarded_probe.md` made the guard fail; removing it restored green |
| README quickstart transcript | `quantrisk.version()  # '1.2.0'` had decayed through two releases; the seed-42 values were shifted by one digit and the guard rejected both |

## 5. Exact test results

Every line is the tool's own output on this commit, not an inference from an earlier run. These are
the *phase's* verification: the `1.4.0` release re-ran the suite and the whole battery, and the
release-time figures — 124 formatted files, `14/14` suite members in 84.6 s, a re-extracted PDF — are
in the addendum at the end of this file.

```
ruff check .                          All checks passed!
ruff format --check .                 124 files already formatted
mypy python/quantrisk                 Success: no issues found in 23 source files
mypy <the three test files touched>   Success: no issues found in 3 source files
clang-format (bindings/cpp/tests)     clean
pytest -q                             411 passed
ctest --preset dev                    100% tests passed out of 198
verify_evidence_manifest.py           76 OK, 0 CHANGED / 0 VOLATILE / 0 MISSING
```

At this gate the benchmark suite was **not** re-run, because no experiment or benchmark source had
changed then: the execution on record was Phase 13's `14/14 executed and passed, 0 failed, 0 skipped`, and `verify_evidence_manifest.py`
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
scope. Its §8 list had two unpaid lines at that point; the mutation harness was promoted after the
release, and the sentence above records why that was a design question rather than a chore.

## 8. Technical debt

Paid here: the CI-mechanical extension-surface check (Phase 13 §8 item 3) and the
artifact-vs-prose guard for `docs/analysis/` (item 1, now covered for both notes by a ratchet rather
than by good intentions).

Paid after the release, in `scripts/run_mutation_suite.py` and `tests/python/test_mutation_suite.py`:
**promoting the mutation harness into `scripts/`**. The hesitation recorded above was about a real design
problem — the tool recompiles deliberately wrong C++, so it cannot be a step in the ordinary gate — and
it was solved by splitting what the gate can hold from what it cannot. The gate holds the *list*: every
ordinary test run re-checks that each mutation's anchor still occurs exactly once in the file it names,
that each prose guard still defines its named test, that each C++ guard still exists as a `TEST_CASE`,
that identifiers are unique, and that the status function names each way a cycle can lie rather than
calling it `caught`. The operator runs the *sweep*, which edits tracked files and rebuilds
`quantrisk_tests`. That split is what makes the earlier warning true rather than a reason to postpone:
the script cannot rot the way the prose did, because the same phase-14 logic — a claim needs a reader —
is pointed at the harness itself.

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
| Tests pass locally | 411 pytest, 198 CTest, 76 artifacts OK, ruff/format/mypy (both the CI scope and the three files this phase touched) and clang-format clean, each quoted from its own run above |
| Tests pass on the runner | `36663508268` on `f4e8afc13bd7` — `completed / success`, all three jobs, after `36550420085` on the previous head failed on this phase's own guard (finding 35); see the addendum's runner record for the quoted lines |
| Version and release | `1.4.0` in `pyproject.toml`, `CMakeLists.txt`, `CITATION.cff` and `uv.lock`; tagged `v1.4.0` on `f4e8afc13bd7` and published with four assets on 2026-09-30T03:25:10Z. `v1.3.0` stays at `f4c1e9ef9e23` and is not moved. See the release record below |

## Addendum — the release this phase became (2026-09-30)

The phase opened with four classes of unread claim and closed with a fifth, found while regenerating
the evidence for the version bump.

**What the bump itself proved.** Raising the library version rewrites every artifact's recorded
`quantrisk_version`, which is why `docs/limitations.md` #71 exists. Re-running the fourteen suite
members to produce those artifacts also re-ran the performance benchmark — and that is what exposed
finding 34: the artifact's `speedup_vs_pure_python` moved to `7.909×` at the previous freeze while
`docs/validation_matrix.md` still described the file as `8.0–8.4×`, and the README quoted paths/s
that the file did not contain. Because those fields are volatile *by declaration*, the manifest
classified the change as VOLATILE and every gate stayed green over a stale claim.

**What was written in response.** `test_documents_quote_the_performance_figures_the_artifact_actually_holds`
re-derives the artifact's ratios, means, standard errors and paths/s and requires the README,
`docs/interview_defense.md` and the paper's own table to print them;
a range narrowed by memory of a few runs fails
(`test_the_documented_speedup_ranges_contain_the_current_measurement`, plus
`test_the_documented_speedup_ranges_match_the_committed_history` for the history itself); and
`test_the_performance_guards_are_not_vacuous` multiplies the artifact's figures by 1.5 and narrows
one band by hand, asserting the guards reject what they had just accepted. The range itself moved to
`docs/reproducibility.md` as the owner, together with the `git log` command that recomputes it — a
command that was run, not written: it prints thirteen measurements spanning `7.77×`–`8.70×` and
`0.42×`–`0.51×`. Those thirteen are also pinned in the guard, because the first version derived the
band from history alone and `actions/checkout` at depth 1 shows CI one measurement: run
`36550420085` went red demanding that README quote `0.45–0.45`, which is finding 35.

**What was measured, not assumed.** The first suite run of this addendum read `7.35294×` with
`var_backtesting` at 103.4 s; `uptime` showed a load average above 3.6 and another Python process at
103.7 % CPU, so the run was re-taken rather than published: `8.38769×` with `var_backtesting` at
25.2 s. The contended reading is recorded as an observation about load and appears in no headline,
because the artifact that measured it no longer exists — the exact prose-only owner #77 describes.

**Verification at 1.4.0**, each line from its own tool on this machine:

```
ruff check .                  All checks passed!
ruff format --check .         124 files already formatted
mypy python/quantrisk         Success: no issues found in 23 source files
clang-format --dry-run --Werror clean (no diagnostics, in the CI form over cpp/ bindings/ tests/cpp/)
ctest --test-dir build/dev    100% tests passed out of 198        (7.54 sec)
quantrisk_tests               All tests passed (547845 assertions in 197 test cases)
pytest tests/python -q        411 passed (405 / 336 at the tag; the harness gate
                              and the registry-completeness guard account for the difference)
run_benchmark_suite.py        suite: 14/14 executed and passed, 0 aggregated from disk,
                              0 failed, 0 skipped, 84.6s total
verify_evidence_manifest.py   76 OK, 0 CHANGED, 0 VOLATILE, 0 MISSING, 0 unlisted
quantrisk validate            7/7 checks passed
latexmk -pdf -g               Output written on technical_report.pdf (42 pages, 966341 bytes)
```

The rebuilt PDF was re-extracted with `pdftotext` and confirmed to contain `8.39×`, `0.445×`,
`38,642,054`, `7.77×`, `8.70×`, `411 pytest tests` and `342 collected`, so the document ships beside
the artifact it quotes rather than the run before it.

**Runner.** Two runs, and only the second one is a release claim.

`36550420085` on `0b1d1f6` is `failure`: `Format and static checks` and `Benchmark suite against live
oracles` passed, while `Configure, build, C++ tests, Python tests` printed `1 failed, 334 passed,
4 skipped` — the range guard deriving a `0.45–0.45` band from the single revision a depth-1 checkout
can see (finding 35). the watcher's exit code never reached me (the background wrapper's `echo` was the last command, and
it reported 0 for a run the watcher exits 1 on — measured later on the same completed run), so the API's
`commits/<sha>/check-runs` reported the failure, which is why no tag was created from the watcher's
word.

`36663508268` on `f4e8afc13bd7` is `completed / success` on all three jobs. The same API reads
`Configure, build, C++ tests, Python tests` → `success`, `Benchmark suite against live oracles` →
`success`, `Format and static checks` → `success`, with SonarCloud `neutral` as it has been on every
prior head. The runner's own lines: `100% tests passed out of 198`, `335 passed, 5 skipped in
50.26s`, `suite: 14/14 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 194.4s
total`, `Success: no issues found in 23 source files`. The added skip is this phase's history guard
printing `this clone carries 1 revision of the artifact (CI uses actions/checkout at depth 1), so no
spread can be derived; see the command in docs/reproducibility.md` — the precondition declared rather
than assumed.

**Release.** `v1.4.0` is an annotated tag object on `f4e8afc13bd7` (tag `0ca51f4d51f1`), and the
GitHub release is `publishedAt 2026-09-30T03:25:10Z`, `isDraft: false`. Four assets were uploaded
from a `git archive v1.4.0` export and downloaded back, and every digest matched:
`e86af9d7…` `technical_report.pdf`, `4a29b1af…` `manifest.json`, `85113b4f…` `CITATION.cff`,
The two record commits after the tag: `24524ba8423a`'s run `36664649873` was **cancelled** — the
erratum push superseded it, which is what GitHub does to an in-progress run on the same branch — and
`ba3cb377202d`'s run `36664952912` is `completed / success` on all three jobs
(`Format and static checks`, `Configure, build, C++ tests, Python tests`,
`Benchmark suite against live oracles`), with SonarCloud `neutral` as on every prior head. Neither
affects the release: the tagged tree is `f4e8afc13bd7`, the commit `36663508268` verified.

`c24bcf07…` `quantrisk-suite-results.zip`. `manifest.json` records `git_commit: 0b1d1f63482a` with a
dirty tree, because the freeze was taken before the guard-fix commit; it verifies `76 OK, 0 CHANGED,
0 VOLATILE, 0 MISSING` against the tagged tree, and the release notes say so rather than implying the
manifest names the tag.

## Second addendum — the harness, paid after the tag (2026-09-30)

`v1.4.0` was tagged before this existed, so it is not in the released tree; it is recorded here rather
than smuggled into a tag that the runner already verified.

**What was built.** `scripts/run_mutation_suite.py` plants a declared defect, requires the one guard
that should reject it to go red, puts the tree back exactly as it found it — from the snapshot taken
before an edit, or by deletion for a probe it created — and requires the same guard to go green again.
The statuses are `caught`, `anchor-not-unique`, `probe-file-already-in-the-tree`,
`mutation-was-a-no-op`, `mutation-did-not-compile`, `guard-could-not-be-run`, `guard-stayed-green`,
`restore-mismatch`, `tree-did-not-recover`, `target-already-modified` — only the first counts, and
`ctest -R` matching nothing is specifically *not* allowed to look like a catch, because a non-zero exit
from a guard that never ran is the exact shape of finding 25.

**The run.** `uv run python scripts/run_mutation_suite.py` runs only on a clean tree, so its own
closing line is recorded in the commit that follows this one, quoted verbatim from the tool.

What each case planted, in the order the tool reported them (this is my summary of the declared list,
not the tool's output — it prints `ok   caught  <id>  <claim>` per line):

| Mutation | Defect planted | Guard that had to reject it |
| --- | --- | --- |
| `note-prints-a-slope-the-artifact-doesnt` | `1.9975` → `1.9976` in the two-factor note | note-figure owner, `test_two_factor_bound.py` |
| `readme-claims-a-narrower-speedup-band` | README `7.77×` → `8.00×` | documented-range containment |
| `readme-quotes-a-stale-speedup` | README `8.39×` → `8.41×` | derived-figure equality |
| `bindings-declare-a-name-the-binary-cannot-serve` | a pybind registration renamed to a name no binary serves | extension-surface parity |
| `architecture-declares-a-file-that-isn't-there` | a phantom `python/quantrisk/analytics.py` in the layout block | architecture path guard |
| `readme-undercounts-the-limitation-register` | "carries 77 numbered entries" → 76 | limitation-count agreement |
| `readme-overcounts-the-cpp-suite` | `# 198 C++ tests` → 199 | C++ count vs `ctest -N` |
| `reproducibility-overcounts-the-suite` | "all 14 members" → 15 | suite count vs the registry |
| `interview-doc-overcounts-the-offline-lane` | a second spelling of the offline count, `# 342` → 343 | python-count agreement |
| `readme-inflates-the-report-by-a-chapter` | "twelve chapters" → thirteen | chapter count vs `\section` |
| `matrix-heading-overcounts-its-own-paragraphs` | "## Five rows…" → Six | heading counts its own paragraphs |
| `readme-miscounts-the-findings` | "The six results worth reading" → seven | findings counted where counted |
| `readme-miscounts-the-matrix-rows` | "twenty rows over" → twenty-one | matrix row count vs the table |
| `matrix-numbers-two-rows-fourteen` | row `15` renumbered `14`, so two rows share a number | row numbering unique and contiguous |
| `experiment-added-without-a-registry-entry` | an unregistered `experiments/_mutation_probe/run.py`, created and deleted by the sweep | suite registry completeness (the audit's last open line) |
| `volga-uses-its-own-square` | `volga = vega·d₁·d₁` instead of `·d₁·d₂` | CTest "vanna and volga are finite differences…" |
| `vanna-loses-its-sign` | the leading minus dropped from vanna | same CTest case |
| `mixed-partial-drops-a-term` | `V_SSσ = γ·(d₁d₂)` without the `− 1` | CTest "the three mixed third partials…" |

**The harness's own negative control.** A probe mutation in prose that no guard reads — appending a
clause to a README sentence and pointing it at a test that cannot see that file — was reported as
`guard-stayed-green`, not counted, and `git status --porcelain -- README.md` came back empty afterwards.
A tool that can only say "caught" is not evidence; this one was shown saying the other thing.

**Gate.** `tests/python/test_mutation_suite.py` (4 cases) runs every ordinary test pass: it re-asserts
anchor uniqueness per mutation, that prose guards define the named test and C++ guards exist as
`TEST_CASE`s, that identifiers are unique and paths repo-relative, and it drives `decide()` through
each failure mode. The sweep itself stays an operator action — it edits tracked files and recompiles —
so CI checks the list, not the mutations.

**A defect the sweep's own tests did not cover.** Adding the `tree` kind left argparse's
`--kind choices` listing only `prose` and `core`, so the new mutation was unreachable by name while
every function around it — `select`, `run_one`, `decide`, the self-test's set comparison — handled it
correctly. A spot-check of `--kind tree` is what surfaced it; the fix derives the choices from the
declared list, and the self-test now runs `main(["--list", "--kind", k])` for each kind, which is the
surface that had been missed. The lesson is the same one as findings 34 and 36, applied to a tool: a
check on the internals of a thing is not a check on the way anyone actually calls it.

**Scope, stated.** A `core` case rebuilds `quantrisk_tests` only, not the Python extension. It proves
the C++ gate rejects the wrong closed form; the Python-visible consequences of a wrong formula remain
the job of the reproduction comparator and `test_extension_surface_parity.py`. Counts move with the
gate: 411 pytest with the `oracles` extra, 342 collected without it (measured with a meta-path blocker
for `QuantLib`/`pypfopt`/`cvxpy`/`sklearn`, not by subtraction), 198 CTest unchanged.
