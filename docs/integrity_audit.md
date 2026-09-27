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
| No dead feature | Enumerate all 159 public Python symbols and `git grep` each for a use outside the binding that declares it | 4 unmatched: `portfolio.OPTIMAL / INFEASIBLE / UNBOUNDED / NUMERICAL_FAILURE`. All four are produced by `linear_program.cpp` and asserted in `tests/cpp/test_linear_program.cpp`; the binding exposes the complete enum. **Not dead.** |
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
| Model limitations disclosed | 58 numbered entries in `docs/limitations.md`, grouped by phase | Clean; the two `partially validated` matrix rows point into it |

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
| CI lane proven on a runner | **No.** `benchmark-suite` is configured and its YAML parses, but has never executed on GitHub-hosted hardware. Open. |
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

**The pattern is worth naming.** None of these were bugs in the numerical core. Nine of ten
were documents describing a state of the repository that had already changed, or claims whose
scope was wider than the evidence. The code was in better shape than the prose about it — which
is the opposite of what an integrity audit is usually expected to find, and the reason the
fixes went into documents, tests and tooling rather than into `cpp/`.

## Still open, stated plainly

- The `benchmark-suite` CI lane is unproven on a runner.
- No remote, no published release, no DOI.
- Test counts and the limitations count are quoted in dated documents; the living documents no
  longer quote a mutable count, and the limitations figure is now guarded by a test.
- The suite's member registry is hand-maintained: a new benchmark that is never registered is
  simply absent, and absence produces no output to check.
