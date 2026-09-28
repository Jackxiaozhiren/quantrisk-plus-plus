# Final Integrity Audit

PROJECT_SPEC.md §Phase 10 requires a last pass over five dimensions — Code, Math, Statistics,
Finance, Reproducibility — before the release is called done. This is the record of what was
actually run, what it found, and what is still open. Every "clean" below names the command
that produced it; nothing here is a judgement dressed as a result.

Revision audited: `v1.0.0` → `9aef2d2`. Date: 2026-09-27.

---

## 1. Code

| Check | How it was tested | Result |
|---|---|---|
| No fake implementation | Scan `*.py`, `*.cpp`, `*.hpp` for `TODO`, `FIXME`, `NotImplementedError`, `placeholder` outside tests | 3 hits, all prose in comments explaining a deliberate design choice; no stubbed routine |
| No dead feature | Enumerate the public Python symbols and `git grep` each for a use outside the binding that declares it | 4 unmatched enum members, all produced by `linear_program.cpp` and asserted in C++ — part of a complete enum, legitimately. **But this row originally read "clean" and was wrong.** The check asked only whether anything calls a symbol; `PortfolioOptimizer.sample_covariance` has no callers *and* raises on every documented input, so it satisfied a check designed to catch the first half only. See finding 12. |
| No secret | Scan every tracked file for key-shaped literals, `password=`, `AKIA…`, PEM headers | 8 files match on the word `api_key`; all are `FRED_API_KEY` **documentation or an `os.environ` read**. `fred.py:87` is the only accessor. No value is committed, cached or logged — enforced by the planted-key test in `test_data_layer_offline.py`. |
| No hardcoded benchmark | Search tests for a comparison against a long float literal | Zero matches. Oracle tests call the oracle at run time; `test_pricing_vs_quantlib.py` additionally runs the published benchmark script so the artifact cannot rot out of coverage. |
| No machine path in evidence | `test_no_committed_artifact_leaks_a_machine_specific_path` | **Failed initially.** The suite runner passed absolute script paths, so `sys.argv[0]` — recorded by `pricing_validation.py` as its own generating command — wrote a username into a frozen artifact and the manifest hashed it. Fixed in the runner; guard now green. |
| Gates | `ruff check .`, `ruff format --check .`, `clang-format --dry-run --Werror`, build with `-Wall -Wextra -Wpedantic` | All clean; 92 files formatted; zero compiler warnings |

## 2. Math

| Check | How it was tested | Result |
|---|---|---|
| Formulas consistent | Identities asserted independently of any oracle: put-call parity (worst residual 7.99e-15), `d₁ = d₂ + σ√T`, `u·d = 1`, forward-ATM call ≡ put, Euler attribution summing to the total (residual exactly 0.0 over 28 scenario-book pairs), level/dispersion VaR telescoping (residual 0.0) | Clean |
| Assumptions explicit | Every component has a model card in `docs/model_cards/` (8 of them) stating its assumptions as claims that can fail | Clean |
| Units correct | The benchmark records the conventions it **measured** rather than assumed: `theta` per calendar year in both engines; `vega`/`rho` per unit, not per percentage point, agreeing to ~1e-15 once measured; the `O(1/N)` CRR convention difference from QuantLib's lattice | Clean, and recorded in the artifact rather than in prose |
| Risk-neutral vs physical separated | `terminal_prices_physical` exists as a distinct entry point in `cpp/src/stochastic/gbm.cpp`, is bound separately, and `tests/cpp/test_gbm.cpp` asserts both that its mean follows `(mu − q)` and that `mu = r` with the same seed reproduces the risk-neutral stream exactly | Clean — enforced by code and test, not by convention |
| Sign conventions | Loss is `L = −R` throughout §6 of the mathematical specification; violation flagging tested against that convention | Clean |

## 3. Statistics

| Check | How it was tested | Result |
|---|---|---|
| Uncertainty reported | Convergence slopes carry standard errors (−0.99405 ± 0.00313; −0.614 ± 0.089); coverage and reject rates carry exact binomial intervals; Monte Carlo agreement is judged at 4× the combined standard error rather than against a tuned epsilon | Clean in the matrix and artifacts. **One gap found and fixed:** `docs/findings.md` quoted ratios with no uncertainty marker; it now states which numbers are deterministic functions of a seeded DGP and which are sampled, and why the ranges quoted are the substantive spread rather than noise. |
| No unjustified causal claims | Read every `findings` block in the six experiment artifacts | Clean. The only causal-shaped claim available (estimation cost) is on a DGP whose truth is analytic, and the caveats say the design is what licenses it. |
| No cherry-picking | Compare each headline against the artifact's own worst case, not its mean; check that failed arms are published | Clean and, in two cases, deliberately unflattering: bootstrap coverage 0.693 against 0.900 nominal is published as the finding, and the C++ engine's 0.42×–0.48× loss to NumPy is in the README. |
| Multiple comparisons | Look for a correction across the many nominal levels and arms | **Not present, and defensible** — these are confirmatory checks of pre-specified properties, not a search for significance. Recorded here because a Statistics committee will ask, and the answer was not written down anywhere before this document. |
| Determinism | Diff every numeric leaf of a full suite re-run against the committed artifacts | Zero result differences; 12 artifacts VOLATILE (timestamp, commit, environment, wall-clock columns), 46 OK |

## 4. Finance

| Check | How it was tested | Result |
|---|---|---|
| No claim of guaranteed return | Grep all `*.md` and `*.tex` for `guaranteed return`, `production ready`, `institutional grade`, `will outperform`, `best-in-class`, `state of the art` | Zero matches outside `PROJECT_SPEC.md`, which is the instruction file listing them as forbidden |
| No trading recommendation | Same scan for `we recommend`, `should buy`, plus check that no expected-return model ships | Clean. `expected_returns` is an input; limitation #37 states that any use treating a sample mean as skill inherits the consequence. |
| No misleading backtest | Check every VaR backtest for a stated data-generating process and a disclosure that it is synthetic | Clean. Limitation #28 is explicit: no real return series is used, so nothing licenses a claim about realised markets. Look-ahead is refused rather than degraded — `fred.fetch_vintage` raises when `FRED_API_KEY` is absent instead of substituting a current-revision series, "because the result still looks like a backtest" (`python/quantrisk/data/fred.py:149-151`), pinned by `test_vintage_needs_a_key_and_says_so_without_touching_the_network` |
| Measure used for risk | Confirm VaR/ES run on the physical measure | Clean, per §2 above |
| Model limitations disclosed | 60 numbered entries in `docs/limitations.md`, grouped by phase | Clean; the two `partially validated` matrix rows point into it |

## 5. Reproducibility

The strongest pass, because it was executed rather than inspected.

```
fresh clone at v1.0.0 (git clone --shared, checkout tag)
  uv sync --extra oracles        → ok
  uv pip install -e .            → built, 160 CMake targets, zero warnings
  uv run pytest -q               → 319 passed, exit 0
  uv run ctest --preset dev      → 190/190 passed, exit 0
  run_benchmark_suite --require-all → 11/11 executed, 0 skipped, ~62 s
  verify_evidence_manifest.py    → see below
```

`verify` on the freshly regenerated artifacts initially reported **10 CHANGED**. That was the
audit finding, not a failure of the evidence: byte hashes cannot distinguish tampering from a
legitimate re-run, so a check that cries wolf on every reproduction is a check that gets
ignored. Fixed by adding a content hash over each artifact with run metadata and wall-clock
columns stripped, and a fifth verdict `VOLATILE`. After the fix the same re-run reports
12 VOLATILE / 0 CHANGED, and a direct diff of the canonical forms confirms zero result
differences.

| Check | Result |
|---|---|
| Fresh clone builds and tests clean | Yes — executed above, on macOS/arm64 |
| Fixed experiment commands work | Yes — every command in README, `docs/reproducibility.md` and the matrix was run as written |
| README numbers reproducible | Yes — the suite reads them from artifacts by key path and aborts if a path moves; 319 tests cover the bindings |
| Evidence verifiable by a third party | Yes — `evidence/manifest.json`, 58 artifacts, byte + content digests, built from a clean tree at `146058c` |
| CI lane proven on a runner | **Yes.** `benchmark-suite` passed on `ubuntu-latest` in 4m10s with `--require-all` (11/11 executed, 0 skipped). The `build-and-test` lane failed on its first run — a README assertion that pinned one vendor's libm to the last bit, found and fixed. See finding 11 in §6 of the phase report and limitation #59. |
| Published release | **No.** No remote is configured; the tag is local and `CITATION.cff` has no URL or DOI. Open. |

---

## What the audit changed

Ten defects were found and fixed during this pass. Ordered by how much damage they would have
done if published as-is:

1. `docs/interview_defense.md` called five shipped components "not built" and dated the
   repository to Phase 3 — 14 corrections. A candidate repeating that in an interview would
   undercut the whole project.
2. The technical report's estimation-cost table had three wrong cells, and its performance
   table had drifted out of agreement with the artifact it cited.
3. The suite runner wrote a username into a frozen evidence artifact, and the manifest hashed
   it as if it were proof.
4. `verify_evidence_manifest.py` could not distinguish a re-run from a change, which made the
   reproducibility claim operationally meaningless.
5. `experiments/variance_reduction` published `worst_mse_reduction_vs_plain = 1.0` — true, and
   vacuous, because each plain-MC cell divides by itself.
6. `docs/limitations.md` filed the Phase 5 risk-layer limitations under the Phase 4 header.
7. The README claimed every artifact is byte-identical across runs; three carry wall-clock
   columns.
8. The README quoted a single speedup ratio that four runs had already disagreed about by 5%.
9. `docs/findings.md` made comparative claims with no uncertainty disclosure.
10. The validation matrix's first draft named thirteen API symbols that do not exist.
11. A test asserted the README's Black-Scholes price bit-for-bit and failed on the first Linux runner, 1.7 ULP out — the platform's libm, not our arithmetic.
12. **`PortfolioOptimizer.sample_covariance` raised on both documented input forms** — `TypeError` on nested rows, `ValueError` on flat — and its error message told the caller to pass `assets=`, a parameter the method does not accept. It shipped in v1.0.0. Found only by finally running the `mypy` step that had been advisory since Phase 1, which also invalidated this audit's own row 1.2: the dead-feature check asked "does anything call this?" and never "does this work if something does?". Deleted rather than fixed, since the tested module-level function is its working equivalent and nothing called the wrapper.

**The pattern is worth naming.** None of these were bugs in the numerical core. Ten of the
twelve were documents describing a state of the repository that had already changed, or claims
whose scope was wider than the evidence. The eleventh was a tool that could not tell a re-run
from a change, and the twelfth was a defect that a gate nobody had enabled was the only thing
between the project and a user. The code was in better shape than the prose about it — which is
the opposite of what an integrity audit usually expects to find, and the reason the fixes went
into documents, tests and tooling rather than into `cpp/`.

Finding 12 indicts the audit itself, and is recorded here rather than quietly corrected in
place: a negative check that has never been observed to fail is not evidence, and "no dead
features" was reported on the strength of a query that could only ever answer half the question.

## Still open, stated plainly

- The `benchmark-suite` CI lane is now proven: it passed on `ubuntu-latest` on its first run.
  What that first run instead caught was a cross-platform floating-point assumption in a test,
  which is the outcome the lane exists to produce.
- `mypy` is now a blocking gate, and it is what surfaced finding 12. The generalisable part is
  that a check which cannot fail a build is decoration; it sat configured-and-warning for nine
  phases while holding three real defects.
- The release is published at `github.com/Jackxiaozhiren/quantrisk-plus-plus` with the report,
  manifest and suite results attached. There is still no DOI and no PyPI publication, which is
  a deliberate boundary rather than an omission.
- Test counts and the limitations count are quoted in dated documents; the living documents no
  longer quote a mutable count, and the limitations figure is now guarded by a test.
- The suite's member registry is hand-maintained: a new benchmark that is never registered is
  simply absent, and absence produces no output to check.

---

## Addendum — the phase this audit prompted (2026-09-28)

The audit above found twelve defects and recommended one substantive change: a real-data empirical
study (`docs/portfolio_audit.md` §10, ranked first). Phase 11 built it, and the audit's own
method — run the check the document claims, rather than read the document — kept finding things
after the study itself was finished. Five are worth recording, because three of them were defects
*in this audit's own numbers*.

**13. This document's central measurement was not reproducible from the revision it names.** §4
reports a fresh clone at `v1.0.0` giving "319 passed". Re-measured in a clean worktree at the tag
with the `oracles` extra, `pytest --collect-only -q` collects **330**; at `06836d2` — the commit
this audit's header names, which is five commits *before* the tag — it collects **316**. Neither is
319. The header also calls `06836d2` "`v1.0.0`", which it is not. Nothing about the audit's
conclusions changes, and that is precisely the problem: a reader who tried to reproduce the number
would have concluded the repository was broken rather than that the note was imprecise. Fixed by
naming both measurements and deleting the commit equivalence. The generalisable part: a *passed*
count and a *collected* count are different quantities, and a document that prints one where the
other is meant cannot be checked by a reader who does not know which it is.

**14. `docs/reproducibility.md` said four suite members skip without the `oracles` extra; the
registry had five, and Phase 11 made it six.** Counted from `requires=` clauses rather than
remembered. Guarded now by `test_documents_that_count_the_suite_members_agree_with_the_registry`,
which loads the registry as Python objects and checks the total, the three-way kind breakdown the
README prints, and the skippable count — so this class of drift fails a test instead of shipping a
paragraph.

**15. The evidence chain did not contain the artifact the README's headline count comes from.**
`evidence/manifest.json` hashed 58 files, none of them `benchmarks/suite/results/`, while
"11/11 benchmark-suite members executed" is read out of `suite_run.json`. The aggregate the project
quotes was outside the mechanism that protects quoted numbers. Added as a fifth category, which
then exposed **16**: the roll-up recorded no generating command at all, so it could not be
reproduced from itself. `command_line()` now rebuilds it from the parsed flags — not from `argv`,
which would have written the caller's absolute `--out` path into a committed artifact and had the
manifest hash it as evidence, exactly the Phase 10 `sys.argv[0]` leak in a new place.

**17. A `git checkout` in the middle of this phase destroyed nine uncommitted documentation edits
to `README.md`.** They were recovered from the session transcript, which is not a method. The
command was typed as a convenience undo of one experimental edit made seconds earlier, in a working
tree that had been deliberately left dirty for the whole phase — where `HEAD` is not where the work
is, and "restore the file" silently means "restore the file as it was five commits ago". The
falsification run that needed it should have used the copy it already had in `/tmp`. Recorded
because the audit's subject is the reliability of what this repository asserts, and an agent that
loses a day of documentation and notices only afterwards is part of that subject.

**18. The test suite wrote into the frozen evidence on every run.** The real-data study's offline
tests executed `experiments/real_data_risk_study/run.py` in place, and the script writes beside
itself, so `pytest` regenerated a committed artifact — new timestamp, new provenance block, dirty
tree — and `verify_evidence_manifest.py` then reported it VOLATILE for a change nothing had
deliberately made. A check that cries wolf because the *test runner* moved a file is the same
failure this audit already documented in §4, where byte hashes could not distinguish a re-run from
tampering; this time the re-run was coming from inside the verification suite. Fixed by running a
copy of the script in `tmp_path`, and structurally by a session fixture in
`tests/python/conftest.py` that hashes every file under `benchmarks/`, `experiments/`,
`data/fixtures/` and `evidence/` at session start and fails the session if any of them moved.
Falsified by planting a test that appends a newline to a stress artifact: the session assertion
fires. A full run now leaves `git status` clean, which it did not before.

**19. The runner caught the new phase repeating the defect this audit was written about.** Two
Phase 11 assertions failed on `ubuntu-latest`: one demanded bit-for-bit agreement between a
macOS-frozen artifact and a Linux re-run (glibc moved the last digits by ~1e-14 — precisely
`docs/limitations.md` #59, which the same author had written), and the other asserted a
with-oracles test count inside a CI lane that installs without them. Both were fixed by encoding the
boundary instead of the wish: relative slack of 1e-12 on floats with exact equality on integers,
verdicts and rankings, and a count guard that asks which environment it is running in. Ten
perturbations confirm the comparator rejects a 1e-6 change, a sign flip, a count change and a
verdict flip while tolerating 1e-14. See `docs/limitations.md` #64 and §6 finding 11 of the Phase 11
report. The lesson is the one this audit keeps re-learning: a check written on one machine is a
claim about that machine, and the only way to find out is to run it somewhere else.

**What the new study itself established.** `experiments/real_data_risk_study/` is the twelfth suite
member; its artifact refuses three questions rather than proxying them; and finding 4 in
`docs/findings.md` now carries the project's first empirical result *and* its first result that
contradicts an earlier phase — the covariance ranking whose two ends exchange places between
synthetic and real data. §6 of `docs/phase_reports/phase-11-real-data-risk-study.md` lists seven
defects the phase found on the way, including a hand-rolled exact interval that came out inverted
and a figure panel labelled "as documented" that was not.

**Verified at this addendum, by execution:** 353 pytest with the `oracles` extra (261 passed / 4
skipped in the CI lane without it), 190 CTest unchanged, 12/12 suite members executed with
`--require-all`, `verify_evidence_manifest.py` reporting 69 artifacts with 0 CHANGED, 0 MISSING, 0
unlisted and 0 warnings, `quantrisk validate` 7/7, mypy/ruff/clang-format clean.
