# Phase 10 — Final Research Validation and Public Release

Date: 2026-09-27 · Version: 0.1.0 → **1.0.0** · Predecessor: `phase-09-research-api.md`

## 1. Completed

- **`docs/validation_matrix.md`** — the twelve-component table PROJECT_SPEC.md §Phase 10
  specifies (Component · Method · Oracle · Tolerance · Status · Evidence), with the bound each
  test asserts *and* the error actually measured beside it. Two components are marked
  `partially validated` rather than rounded up.
- **`scripts/run_benchmark_suite.py`** — one command that executes all eleven members (4
  correctness benchmarks, 6 statistical experiments, 1 performance benchmark) and writes
  JSON, CSV, Markdown and a figure. Satisfies §Phase 10's "必须由脚本自动生成".
- **`evidence/manifest.json`** — SHA-256 over every artifact with its generating command
  recovered from the artifact, the repository revision, the dirty flag, and the full build and
  package environment. Plus `scripts/verify_evidence_manifest.py`, which reports
  OK / CHANGED / MISSING / unlisted separately and fails on the last three.
- **`paper/technical_report.tex` + `references.bib`** — 12 chapters in the mandated order,
  building to a 37-page PDF.
- **README restructured** into the mandated eleven sections in the mandated order, with the
  feature-dump opening replaced by "What it is / Why it exists".
- **`CITATION.cff`**, **`docs/reproducibility.md`**, **`docs/release_notes_v1.0.0.md`**.
- **Version 0.1.0 → 1.0.0** in both declarations (`pyproject.toml`, `CMakeLists.txt`), which
  `test_smoke.py` requires to agree.
- **A third CI job** running the whole suite with `--require-all`.
- **Final integrity audit** across code, mathematics, statistics, finance and reproducibility
  (§7 below).

## 2. Mathematical assumptions

Phase 10 adds no model. It adds one claim that is not inherited from an earlier phase: that a
**worst-case error is the maximum over every row of a sweep, not an average**, and is therefore
the number comparable to a tolerance. Everything else in the matrix is a restatement, with its
source, of a claim already made in Phases 1–9.

Two conventions had to be pinned down to make the matrix honest:

- *Relative error where the denominator can vanish.* Rho passes through zero on the wide
  benchmark grid, so a `5.12e-13` absolute error becomes `1.07e-7` relative. The matrix reports
  both and names the floor (`greek_floor = 1e-06`) that separates "relative error is
  meaningful" from "it is not".
- *A convergence rate is not a tolerance.* The CRR row asserts a fitted slope
  (−0.99405 ± 0.00313 against theory −1), not an error bound, because a 50-step lattice
  legitimately disagrees with the analytic price by 1.82 on the worst row of the sweep.

## 3. Files changed

| File | Change |
|---|---|
| `scripts/run_benchmark_suite.py` | new, 832 lines: member registry, subprocess execution, key-path extraction, JSON/CSV/Markdown/figure emission |
| `scripts/build_evidence_manifest.py` | new: hash, command recovery, revision and environment capture |
| `scripts/verify_evidence_manifest.py` | new: four-way verification with distinct failure classes |
| `docs/validation_matrix.md` | new: 12 components × 6 columns, plus three prose caveats and a non-coverage list |
| `docs/reproducibility.md` | new: the contract, the commands, and four named ways it breaks |
| `docs/release_notes_v1.0.0.md` | new |
| `CITATION.cff` | new |
| `paper/technical_report.tex`, `references.bib` | new (12 chapters); 4 numeric corrections applied during audit |
| `README.md` | rewritten into the mandated 11-section order |
| `docs/interview_defense.md` | new (22 questions × 3 depths); 14 stale "not built" statements corrected during audit |
| `experiments/variance_reduction/run.py` | `worst_mse_reduction_vs_plain` was `1.0` because it included each plain-MC cell's self-ratio; now scoped to the variance-reduced cells, with the trivial all-rows minimum kept as a separate field |
| `docs/limitations.md` | Phase 5's entries 28–35 were filed under the Phase 4 header; header added, numbering untouched |
| `pyproject.toml`, `CMakeLists.txt` | version 1.0.0 |
| `.github/workflows/ci.yml` | `benchmark-suite` job |
| `tests/python/test_artifact_metadata.py` | 4 new tests covering the suite runner |
| `docs/project_scope.md` | §9 Phase 10 row, §10 frozen surface |

## 4. Tests executed

```bash
uv run ruff check . && uv run ruff format --check .      # 88 files
find cpp bindings tests/cpp -name '*.cpp' -o -name '*.hpp' \
  | sort | xargs uv run clang-format --dry-run --Werror
uv run cmake --build --preset dev                        # zero warnings
uv run ctest --preset dev
uv run pytest -q
uv run quantrisk validate
uv run python scripts/run_benchmark_suite.py --require-all
uv run python scripts/build_evidence_manifest.py
uv run python scripts/verify_evidence_manifest.py
```

## 5. Exact test results

- ruff: `All checks passed!`; format: `88 files already formatted`.
- clang-format: clean. Build: no compiler warnings.
- CTest: **190/190 passed**, 7.4 s. Direct Catch2 run: **546,943 assertions in 189 test
  cases**, all passed.
- pytest: **316 passed** in 8.7 s (was 310: +4 suite runner, +1 limitations-count guard,
  +1 machine-path guard).
- `quantrisk validate`: **7/7**.
- Benchmark suite: **11/11 executed and passed, 0 failed, 0 skipped**, 64.8 s wall.
- Evidence manifest: **58 artifacts, 5,420,396 bytes**; verify reports `58 OK, 0 CHANGED,
  0 MISSING, 0 unlisted`, exit 0.

## 6. Numerical validation

The matrix's headline row, each value read from a committed artifact by the suite runner:

| Component | Bound asserted | Worst measured |
|---|---|---|
| Black-Scholes vs QuantLib (2,464 prices) | 1.0e-10 rel | 3.46e-11 rel, 1.49e-13 abs |
| Greeks vs QuantLib | 1.0e-8 rel | 5.12e-13 abs |
| Put-call parity | identity | 7.99e-15 |
| Analytic vs FD delta | `O(h²)` | ratios 4.00 and 4.00 |
| CRR order | slope −1 | −0.99405 ± 0.00313 |
| MC z (160 runs) | mean 0, sd 1 | ≤0.05, 0.92–1.01 |
| Coverage | binomial band | 12/12 |
| Variance reduction | MSE ratio > 1 | 1.1155–40.468 |
| Covariance | 1.0e-12 rel | 7.2e-16 / 7e-19 |
| Six solvers (75 problems) | per-problem 1e-11…1e-5 | objective 4.48e-9, weights 4.66e-7, budget 1.45e-12, bound violation 0 |
| Stress attribution | residual 0 | 0.0 over 28 pairs |

**Falsification performed, not assumed.** Each new guard was run against the state it is
meant to reject:

- The suite's key-path lookup was pointed at a renamed field; it aborted with
  `has no "'worst_relative_error_above_floor'.'lattice[steps=800]'"` — which is how the one
  genuinely wrong pointer in the first draft was found.
- The same mutation, applied to `worst_mse_reduction_vs_plain`, failed 3 of the 4 new pytest
  guards and passed after revert.
- The plot-label guard was called with a non-existent label and raised
  `plot label 'not a real label' is not a headline metric`.

**Errors found in this phase's own deliverables, by checking before publishing.** These are
worth recording because they are exactly the failure mode the project exists to avoid:

1. The technical report's estimation-cost table had three wrong cells — `1.1326` copied into
   the shrinkage column at window 125 (true value `1.1331`), and `1.2450`/`1.2260` where the
   artifact says `1.2453`/`1.2265`. Found by extracting every `\times 10^n` and high-precision
   decimal from the `.tex` and re-deriving each against the JSON. All 64 scientific notations
   traced correctly; the errors were in the four-decimal table.
2. The report's performance table had drifted: it was written against an earlier
   `monte_carlo_speed.json`, and the suite run replaced that artifact. Four dated runs give
   7.99×, 8.07×, 8.20× and 8.37× against the Python baseline, and 0.42/0.42/0.43/0.48 against
   NumPy — a 14% spread, because the NumPy baseline itself moved from 110M to 95M paths/s.
   The table now cites one dated run, and the prose states the spread. The README and release
   notes quote ranges rather than any single ratio, because a point estimate here is a claim
   the next run will contradict.
3. `docs/interview_defense.md` described the repository as "Phases 0–3 shipped" and called
   Heston, VaR/ES, CVaR, risk parity and path-dependent pricing **"not built"** — fourteen
   statements that were true when drafted and are false now. Corrected throughout, including
   the test counts (72/136 → 190/316).
4. `docs/limitations.md` filed Phase 5's entries 28–35 under the Phase 4 header. A reader
   looking for the risk layer's limitations could not find them, and the Phase 4 header
   over-claimed. Fixed by adding the missing header; no entry renumbered, so existing `#n`
   citations still resolve.
5. `experiments/variance_reduction/run.py` published `worst_mse_reduction_vs_plain = 1.0`.
   Technically true and informationally empty: every plain-MC cell divides by itself, so the
   minimum over all rows is 1.0 no matter how the reduced methods performed. The real worst
   reduced-method ratio is 1.1155. Fixed at the source rather than annotated around in the doc.
6. The first draft of the matrix named methods that do not exist (`pricing::greeks`,
   `risk::bootstrap_ci`, `portfolio::ledoit_wolf_covariance`, `stress::apply_scenarios`).
   Caught by listing the actual bound names from the module and correcting all thirteen.
7. The suite's first figure was a violin plot of 16,260 relative errors on a log axis, which
   spanned 280 orders of magnitude and was unreadable. Replaced by a bar chart of the published
   worst-case metrics — which also removed a second, independent extraction of the same data,
   so the figure can no longer disagree with the table beside it.

8. **The suite runner leaked a machine-specific path into frozen evidence.** It invoked each
   member with an absolute script path, so `sys.argv[0]` — which `pricing_validation.py`
   records as its own generating command — became
   `/Users/<name>/QuantRisk++/benchmarks/quantlib/pricing_validation.py`, and the manifest then
   hashed that as evidence. Found while writing a *different* test, fixed by passing the path
   relative to the subprocess's own cwd, and now guarded by
   `test_no_committed_artifact_leaks_a_machine_specific_path`, which scans every committed
   artifact for the repository root, the home directory and `/Users/`/`/home/` prefixes. The
   guard failed on three files before the fix and passes after.

9. **The determinism claim was too broad, and measurement narrowed it.** "Every artifact is
   bit-identical across runs" is false: three artifacts carry wall-clock columns. Diffing every
   numeric leaf of a full re-run against the committed artifacts gives **zero** differences in
   the results, and non-zero only in timing columns plus each file's own `generated_at_utc` and
   `git_commit`. `docs/reproducibility.md` and the README now say exactly that, and name the
   three files.

## 7. Remaining limitations

New entries are recorded in `docs/limitations.md` #56–#58. The phase's own boundaries:

- **The `benchmark-suite` CI job has never run on a GitHub-hosted runner.** It is configured
  and its YAML parses, and locally it passes in 60 s, but a runner is a different machine:
  cvxpy/OSQP and QuantLib wheels, `uv sync --extra oracles` resolution order, and the
  `ubuntu-latest` toolchain are all unverified. Local green is not evidence about CI.
- **No GitHub release exists.** The repository has no remote configured, so the tag is local
  and the release notes are a file. Publishing requires a remote and explicit approval.
- **`CITATION.cff` has no `repository-code` or DOI**, because neither exists yet. A citation
  file pointing at an unpublished URL is worse than one that says the URL is pending.
- **The suite's member registry is hand-maintained.** Adding a benchmark does not add it to the
  suite; the key-path guard makes a *renamed* field fail loudly, but an *unregistered* member is
  simply absent. The `--list` output and the artifact index in the summary are the check.
- **Timing artifacts are not reproducible across machines**, and the manifest hashes them
  anyway. Re-running the suite on different hardware produces a CHANGED entry for
  `monte_carlo_speed.json` by design; that is the check working, not a broken build.
- **The report cites 37 pages and specific table values as of this commit.** Any later
  regeneration of an artifact will drift them, which is why the report is generated last and the
  manifest hashes it.

## 8. Technical debt

Carried forward from earlier phases, unchanged by this one:

- Rewrite max-Sharpe via the unit-excess reformulation so it stops being a ternary search over
  a frontier whose flatness forces a 1e-7 weight tolerance.
- Extend `-Wall -Wextra -Wpedantic` to `tests/` and `bindings/`.
- A canonical fixture-name accessor, and a lazy `__getattr__` for the shim re-exports.
- Fix or delete `describe_environment()`'s weak `cache_writable` proxy.
- Scenario-set-level attribution of the quantile rather than the mean.

Added by this phase:

- **Single-source the version.** It is declared in `pyproject.toml` and `CMakeLists.txt`; the
  smoke test asserts they agree, which catches drift but not the maintenance cost. scikit-build-core
  can pass the Python-project version into CMake, which would remove the second declaration.
- **The suite runner duplicates `Member` metadata** that also exists in each script's own
  docstring (command, purpose). A shared registry — each script declaring its own headline
  key paths — would make an unregistered member impossible rather than unobserved.
- **Test counts were quoted by hand in five documents, and adding tests during this phase
  moved the figure twice (310 → 314 → 315 → 316).** The two living documents — README and
  `docs/reproducibility.md` — no longer quote a count at all; they point at the command. The
  dated records (phase report, release notes, interview sheet) keep theirs, since a number
  tied to a named revision is a fact rather than a maintenance burden. The limitation count
  is the same class of claim and is now guarded by
  `test_documents_that_count_the_limitations_agree_with_the_file`; the test counts cannot be,
  because pytest cannot cheaply be asked inside a test how many tests it will collect.
- **`validation_envelope.png` covers only correctness benchmarks.** The statistical
  experiments' headline metrics (coverage, reject rates, MSE ratios) are on different scales and
  are not plotted; a second panel per scale would be the fix.

## 9. Gate

**Phase 10: PASS, with the CI lane and the remote release explicitly open.**

Everything PROJECT_SPEC.md §Phase 10 asks for exists and was verified by execution rather than
assertion: the twelve-component validation matrix, an auto-generated benchmark suite in four
formats, a frozen and independently verifiable evidence manifest, a twelve-chapter technical
report, the README in the mandated order, `CITATION.cff`, and release notes.

Two deliverables are gated on things this session cannot do: the GitHub release needs a remote
and explicit approval, and the new CI lane needs one run on a runner before "runs in CI" is a
fact rather than a configuration. Both are stated in the README and the release notes rather
than quietly assumed.

The integrity audit's five passes are recorded in §6 and in `docs/reproducibility.md`. The
most consequential finding was not in the code: two documents written this cycle described an
older repository, and would have been believed.
