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
| No cherry-picking | Compare each headline against the artifact's own worst case, not its mean; check that failed arms are published | Clean and, in two cases, deliberately unflattering: bootstrap coverage 0.693 against 0.900 nominal is published as the finding, and the C++ engine's 0.42×–0.51× loss to NumPy is in the README. |
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
- ~~The suite's member registry is hand-maintained: a new benchmark that is never registered is
  simply absent, and absence produces no output to check.~~ Closed by
  `test_every_experiment_and_benchmark_script_on_disk_is_a_suite_member`, which compares the set of
  `experiments/*/run.py` and `benchmarks/*/*.py` files against the registry in both directions, and by
  `experiment-added-without-a-registry-entry` in `scripts/run_mutation_suite.py`, which creates an
  unregistered probe experiment and requires that guard to reject it.

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
`--require-all`, `verify_evidence_manifest.py` reporting 72 artifacts with 0 CHANGED, 0 MISSING, 0
unlisted and 0 warnings, `quantrisk validate` 7/7, mypy/ruff/clang-format clean.

## Addendum — Phase 12, the analysis the audit asked for (2026-09-28)

`docs/portfolio_audit.md` §10 ranked three improvements. The first became Phase 11; this phase is
the third, "one worked analysis result", and the audit's own warning about it turned out to be the
interesting part: *"the only one that risks being wrong in a way a specialist notices"*. Four things
were found by trying, all recorded here rather than quietly corrected.

**20. A summary sentence in this repository was false of the data beside it, and nobody had
noticed.** The stress layer's prose said the linearisation error "grows with the shock size" while
its own committed CSV shows 649.5 at a 10 % down move, 528.5 at 20 %, and 12,527 at 30 %. The
Taylor remainder explains the shape -- the book's third spot derivative crosses zero at spot 94.55,
so segments past that cancel internally, and the remainder itself has a zero at a 21.1447 % move,
inside the single sign change the older artifact already contains. That prediction was computed
before the bracket was checked, and the check is in
`tests/python/test_linearisation_bound.py`. An audit that only asks "is the code right" misses this
class entirely; the question that finds it is "does the prose say what the artifact shows".

**21. Two of the new tests passed while measuring the wrong thing.** A pooled log-log fit over up
and down moves returned `3.037 +/- 0.003` and passed a `3 +/- 0.1` band: eleven "standard errors"
from theory, where the sigma were computed from three points and the deviation *was* the
up/down separation. And `fit_slope` indexed errors by `abs(move)` instead of by `move`, which made
the two directions identical to sixteen digits -- a duplicate result is far more convincing than a
wrong one. Both were caught only by printing the per-direction numbers and asking whether they
should differ. The guards are now that the slope must *converge* to 3 as the fit window shrinks,
per direction, over hundreds of points.

**22. A finite-difference tolerance was set by hope.** The stencil checks disagreed by 3.6e-9 at a
step of 1e-5 and agree to 4e-11 at 2e-3; the test asserted 1e-9. The step and the tolerance are now
justified next to each other, and the same lesson is limitation #66. Related, and worse: an earlier
draft of the analysis put the arithmetic floor at a relative move of 1e-3, taken from a
single-option test in *absolute* price increments -- wrong unit, wrong scale, stated with four
significant figures that made it look measured. The floor for that book is near 3e-5 and has to be
re-measured per book.

**23. Interface freeze held, and that was worth testing rather than assuming.** The new
sensitivities arrived as a separate struct and function rather than as fields on `Greeks`, because
`Greeks` is a frozen surface and a released version has shipped with it. The added API is therefore
the only kind of change available here, which is worth knowing before someone tries to extend the
Greeks struct and finds the bindings, the shims, the stubs and three documents in the way.

**28. The runner caught two guards that were only true on one libm.** The convergence guard meant to
prove the error is quadratic asserted, on top of the numerical band, that each narrower fit window
beats the one before it. It passed here and failed on `benchmark-suite` at
`3.000121 -> 2.996952` on the pure-spot ray (run `36413144612`; that job's retained log ends at
`running two_factor_error_bound ...`, so the pair is the session's record rather than a retrievable
artifact). The fix I first wrote — compare only the endpoints —
also passed here and also failed there, at `3.004587 -> 2.991277` (run `36415073007`). Every value in
both series is
within 0.009 of the theory number 3, so no band was ever at issue; what was at issue is that the
pure-spot ray's tightest sample is 1281x the double spacing of the 1.09e5 book value it is
subtracted from, against 1.3e6-1.9e6 for the joint rays, which makes an ordering across its windows
a comparison of noise. The guard now asserts convergence only where conditioning makes it
meaningful, publishes every window, and leaves every numerical band exactly where it was — which
matters, because "relax until green" and "stop asserting what the data cannot support" look identical
from here and are not the same thing (limitation #72).

**Verified at this addendum, by execution.** 366 pytest with the `oracles` extra (297 collected
without it), 194 CTest (547,331 assertions in 193 Catch2 cases), 13/13 suite members with
`--require-all`, `verify_evidence_manifest.py` at 72 artifacts with 0 CHANGED / 0 VOLATILE / 0
MISSING / 0 unlisted / 0 warnings, `quantrisk validate` 7/7, mypy/ruff/clang-format clean, and the
40-page report rebuilt and text-verified.

## Addendum — Phase 13, the refusal converted into a result (2026-09-28)

The paragraph above records Phase 12's state and is left as written: it was true of that revision,
and correcting a historical print to match a moving file is how a release note becomes fiction.

**24. The validation matrix had two rows numbered 13, and the guard designed to catch exactly that
could not see it.** Phase 12 added its row without noticing Phase 11's had already taken the number.
`test_documents_that_count_the_validation_matrix_rows_agree_with_the_table` counts *rows*, and two
rows numbered 13 still make eighteen rows, so the count stayed true while the numbering broke -- and
the numbering is what prose cites, so a reader following "row 14" landed on the wrong entry. Fixed by
renumbering, and the class is closed by a new guard that asserts labels are unique, that the numeric
prefixes are contiguous, and that every in-file `row N` citation resolves to a row that exists.
Adjacent to it, a section heading claimed "Four rows that need the prose to be honest" over three
paragraphs, now derived from the body instead of typed.

**25. Two of my own harnesses reported success while doing nothing.** A mutation sweep intended to
prove the new tests can fail printed `NEEDLE NOT FOUND` for two of nine cases because clang-format
had reflowed the expression between the time I read it and the time I patched it -- a mutation that
never applied is a passing test that proves nothing, and the count in the analysis note now says
seven-then-two rather than a single confident number. Separately, a background sweep died part-way
with a mutated source file left in the tree, because I ran other commands against the same virtualenv
while it was reinstalling the extension. Both are recorded as process facts rather than quietly
redone: verify a control actually fired, and do not touch an environment a harness owns.

**26. A `uv pip install -e .` that succeeds can install a stale build.** An editable reinstall after
editing `bindings/python_bindings.cpp` completed in 13 ms and the new functions were simply absent
from the imported module, because uv had cached the wheel built before the edit. The symptom is a
missing attribute, which reads as "my binding is wrong" rather than "I am importing an older binary".
Documented with its fix (`--no-cache`) in `docs/reproducibility.md`, alongside two neighbouring traps
found the same day: configuring outside the venv builds the extension against a different
interpreter, and raising the library version invalidates committed artifacts because each records
`environment.quantrisk_version`.

**27. A correct asymptotic claim, quoted at the size a report uses, pointed the wrong way.** The
headline of this phase was going to be "the map's joint-shock error is quadratic, and here is the
correction". It is quadratic -- the fitted slope converges to 2.0 on four rays while a pure-spot ray
holds at 3.0. And at the published `risk_off` the closed-form quadratic is +787.96 against an actual
error of −5320.79, because a cubic term `½V_{SSσ}h²k` is 10.7× the net quadratic. Had I published the order claim
without the size decomposition, the repository would have shipped a correction with the wrong sign,
in a document whose entire purpose is saying how large the error is. The order statement survives only
bundled with the sentence that names its limits, and the practical recommendation moved from adding
vanna and volga to re-striking gamma.

**29. My own reproduction test repeated the mistake the phase had just documented twice, and then
repeated the fix's mistake three more times.** By the time the third CI run went red the pattern was
unmistakable: the experiment's guards, then their replacement, then a test whose whole job was
checking reproducibility, each in turn asserted something that only holds on the libm that produced
the committed bytes. The first of the four was an 8e-7 relative difference in a *fitted slope*
compared for bit-equality (run `36416691279`, `1.9998100833` against `1.9998084571`). The first fix
gave floats 1e-5 of slack and went red again on the very next run (`36417662618`), on a 3.2e-3 gap in
the pure-spot slope — which is not the same problem one size bigger but a different one: that quantity
cannot be reproduced to better than its conditioning on any platform. The slack then derived from the
artifact's own `fit_conditioning` (`1/sqrt(r)`, 0.028 for the pure-spot ray) was calibrated in both
directions and still went red twice more: on run `36518357703` at
`.fit_conditioning.pure spot (k=0).error_at_tightest_sample`, 6.6e-3 relative on a field the rule does
not cover because no regression produced it, and on run `36519230799` at
`.slopes.pure spot (k=0)[0].standard_error`, where the committed `0.000605699` and the Linux
`0.000842849` differ by 39% of the committed value. That last one is what proved the class: a standard
error is the residual scatter of an ill-conditioned fit, so it *measures* the looseness instead of
being exempt from it, and its name contains nothing resembling "slope" — no list of field names can be
closed. The comparator now asks
the artifact which families are conditioning-limited (`reproduction_policy.conditioning_limited`,
owned by the experiment) and, inside them, compares **shape rather than value**: key sets, list
lengths, types, with integers, booleans, strings and verdicts still exact even there. Value equality
survives at 1e-5 relative everywhere else. What the numbers say, in order: 8e-7, 3.2e-3, 6.6e-3, 39%.
What changes is not the tolerance but which question is being asked, and the honest version of this
finding is that four successive per-field patches were needed to see that a field-by-field patch was
the wrong shape. Limitation #73 is written in the past tense on purpose, and #75 carries the detail.
The lesson is not that cross-platform floats need slack, which the repository already said in #64,
#71 and #72, but that a new file does not inherit the old file's understanding; the check that catches
it is a green run on the machine that is not this one, which `36521846544` finally supplied.

**30. A figure guard proved the digits were transcribed and was blind to the sentence reading them
wrongly.** The headline of this phase was that the mixed cubic term `½V_{SSσ}h²k` dominates the
quadratic "by 7.4×". The artifact's `headline.largest_cubic_over_quadratic` did say 7.408, the note
did print 7.4, and the guard that ties prose to the artifact was green throughout. Both numbers are
correct and the prose was not: 7.408 is the ratio against the quadratic's two contributions **summed
in absolute value** (|-173.10| + |961.06| = 1134.15), while every sentence quoting it printed the
**net** quadratic, +787.96 -- the quantity a correction would actually subtract -- and called it "the
entire quadratic". Against that net the dominance is **10.66×**, so the sentence understated this
phase's own central engineering claim by a third. It reached eleven surfaces: the README,
`docs/findings.md`, the analysis note, the validation matrix, a model card, the interview notes, this
phase's report and gate, the release notes, the two findings above, the technical report, and the body
of the `v1.3.0` release published before the discrepancy was noticed.

Fixed by taking the ambiguity out of the data rather than out of the prose: the key is gone, and the
artifact now publishes `largest_cubic_over_net_quadratic` (10.663),
`largest_cubic_over_quadratic_magnitudes` (7.408) and both denominators as their own fields, so a
ratio's meaning travels with its name. The test recomputes both from the core, asserts that the net
really is the smaller denominator here -- it is, because the two quadratic contributions cancel -- and
requires every document that carries a figure to name the denominator beside it. Written as a
limitation (#76) because the failure mode is general: a provenance check on digits certifies
transcription, never interpretation, and a ratio field whose name does not state its denominator is a
sentence waiting to be misread by the next author, who will be me.

**31. I published a gate claim I had not re-run, and then mis-described the instrument that caught
it.** Commit `897a127` ends "ruff/format/mypy/clang-format clean". Ruff was not clean at that tree:
`E501 Line too long (102 > 100)` at `tests/python/test_two_factor_bound.py:459`, in a comment added
*after* the last lint sweep. The final pass covered pytest, CTest, validate, mypy and clang-format and
simply did not include ruff, so the sentence described the tree as it had been twenty minutes earlier
rather than as it was. Run `36524443614` reported `Format and static checks: failure` with the other two
jobs green -- this phase's seventh red, and the second one caused by a claim rather than a computation.

The correction to the correction is the part worth keeping. That commit's own message asserted that
"`gh run watch --exit-status` exited 0 on that failed run". It did not: the watcher returned **1**, and
the zero belonged to my background-task *wrapper*, whose status comes from the last command in a chain I
had written as `watch; echo exit=$?; gh run view`. Reading the watcher's captured output showed both
facts -- `exit=1` for the failed run, and why an earlier watch had ended while its run was still
`in_progress`: `failed to get run: ... EOF`, the poller losing the API on a run that went on to pass. So
the instrument was unreliable in the *opposite* direction from the one I reported, and I found that only
by going back to the primary output instead of trusting my summary of it. Every CI statement in this
addendum is now quoted from `gh run view --json conclusion,jobs` or from the runner's own log lines.
An unqualified "clean" across four tools is the shape that invites the original error too: the gate rows
in the phase report and the release notes now name the tool that produced each verdict.

**32. The Phase 12 analysis note had no test reading it, and writing one found three defects in it.**
The guard for the Phase 13 note was built in-phase; the Phase 12 note, a whole phase older and the
project's first worked analysis, was never given the same treatment. Given one now, it failed on
contact. The cubic-crossing spot was quoted as `94.5456` with a `5.4544 %` move where the artifact
publishes `94.5487` and `5.4513 %` -- and the note's own arithmetic (`100 - 5.4544`) was internally
consistent, which is why no reader caught it. The paragraph's headline fitted slope, `2.996188` with
standard error `0.044006`, belonged to a pooled six-point fit **that the experiment does not compute**
and that no longer exists anywhere in the tree: a figure with no owner cannot go stale in a test, only
in prose. Third, and the most interesting, the sentence drawn from it -- a deviation of `-0.087
standard errors` from theory 3, offered as evidence of agreement -- misread the statistic. A
regression's standard error measures the scatter of its residuals, not the accuracy of its estimate;
over a window whose residuals carry the fourth-order mixture at one end and §6's cancellation noise at
the other, the error is systematic, and the artifact's own widest window sits 52 and 59 standard
errors from 3 down and up while converging toward it monotonically. The note now quotes the five
published windows as the sequence the artifact actually claims, and says so out loud. The same sweep
also turned up `21.1446` (a truncation of the predicted zero) in five documents beside `21.1447` (the
rounding) in two; all seven print the rounded value now.

Closed by rule, not by repair: `test_every_figure_the_note_quotes_is_owned_by_the_artifact` re-formats
every figure from the artifact and demands it in the prose -- four perturbations, including re-inserting
the historic `94.5456`, are each caught -- and `test_every_analysis_note_is_guarded_against_the_numbers_it_quotes`
fails the suite if any file in `docs/analysis/` has no test that reads it, so a third note cannot be
born unowned the way the first two were. Limitation #77 carries the general form: a number stated in
prose and absent from any artifact is a number that cannot be checked, only re-read.

**Verified at this addendum, by execution.** 388 pytest with the `oracles` extra and 319 collected
without it, 198 CTest (547,845 assertions in 197 Catch2 cases), 14/14 suite members under
`--require-all`, `verify_evidence_manifest.py` at 76 artifacts with 0 CHANGED / 0 VOLATILE / 0
MISSING / 0 unlisted, `quantrisk validate` 7/7, mypy/ruff/clang-format clean, and the 42-page report
rebuilt and text-verified. Nine deliberate formula mutations were compiled and all nine were caught,
and the reproduction comparator was falsified in both directions by eleven mutations that each gave
the demanded outcome, and both were re-checked against tampered inputs: five mutations of the published
ratios and denominators, five caught; four conflations of the two quadratic denominators in prose, four
caught, one positive control passing, and the document restored byte-for-byte. Twelve CI runs landed on
`main` for this phase -- seven red, four green, one cancelled -- and each red is named by run id above:
PyPI 503 on one lane, the convergence guard twice, the reproduction test four times in the same way
(#29), and a fifth guard failure of mine caused by a lint claim I had not re-run (#31). Runs
`36521846544` (`f4c1e9ef9e23`, the tagged commit), `36523154776` (`270eb23`), `36525353886`
(`3938b83`) and `36526049661` (`b9aaa3a`, the head of `main`) are green on all three jobs, the runner's own lines being
`100% tests passed out of 198`, `319 passed, 4 skipped`, `suite: 14/14 executed and passed`.

## Addendum — Phase 14, the checks the debt list said to write (2026-09-29)

**33. The architecture document described a package that has never existed, and nothing read it.**
`docs/architecture.md` listed `python/quantrisk/analytics/` twice — in the table of layers, as
something the Python tier "owns", and in the layout block — and no such package was ever created: the
facades are one module per domain, because `quantrisk.pricing` had to stay the same path in Python and
in the C++ namespace. The file also stated the technical report had thirteen chapters in two release
notes, where `technical_report.tex` has twelve numbered `\section` commands and one unnumbered artifact
index. Neither claim is about a number an experiment produced, so no artifact-vs-prose guard covered
them, and the phase's own answer was to admit it rather than to fix the two sentences and move on:
`test_every_path_the_architecture_document_declares_exists` parses the layout block, expands and
rejoins brace groups, and fails on any declared path absent from the tree;
`test_documents_that_count_the_paper_chapters_agree_with_the_source` counts `\section` in the source and
checks five documents that restate it. Both were falsified — injecting the phantom path into the block
is caught by the parser probe, and the layout guard fails on a synthetic missing path. The general form
is the same as #76 and #77 one level up: a prose file that describes the repository is making claims,
and a claim nothing reads is a claim that quietly stops being true. The §6 departures that were
*deliberate* (`data/fixtures/` rather than `data/sample/`, flat facade modules rather than
`analytics/`, and the runtime-only `data/cache/`) are now written down beside the block that shows them
instead of living in whoever notices the difference first.

**34. The speed artifact regenerates, and four documents quote it in the present tense.**
`benchmarks/performance/results/monte_carlo_speed.json` is re-frozen by every suite run, and its
headline fields — `speedup_vs_pure_python`, `speedup_vs_numpy`, `results_seconds` — are volatile *by
declaration*, listed in `quantrisk/experiments/evidence.VOLATILE_KEYS` because they measure the
machine rather than the model. The consequence was not thought through: the manifest therefore
certifies *nothing* about those ratios, while `README.md`, `docs/validation_matrix.md`,
`docs/interview_defense.md` and §9 of the paper all quote them as the artifact's own current values.
The first re-run of this release caught the drift. The committed artifact behind v1.3.0 measured
`7.909×`, and `docs/validation_matrix.md` described that same file as `8.0–8.4×` — the file it
described was already outside the range printed about it. `README.md` carried "45.5M vs 5.5M paths/s
in the current artifact" for a file reading 45.6M and 5.8M, and `docs/interview_defense.md` quoted
means from a run two freezes gone. Second, the ranges themselves were too narrow because they had
been written from a handful of runs rather than from the artifact's history: the thirteen committed
measurements span `7.77×`–`8.70×` for C++/Python and `0.42×`–`0.51×` for C++/NumPy, against the `5%`
and `14%` spreads the documents claimed — and one re-run taken while another process held a core read
`7.35×`, outside every range this repository has ever printed. That run is deliberately *not* quoted
as a headline anywhere: its artifact was overwritten by the quiet re-run that follows it, and a number
whose artifact no longer exists is exactly the prose-only owner #77 describes. `var_backtesting` took
103.4 s in the same window against 25.2 s in the quiet one, which is how the contention was
identified rather than assumed. Third, `make check`-style gates were green throughout, because no test
read that artifact at all. Closing it: `docs/reproducibility.md` now owns the range and prints the
`git log` command that recomputes it, the other documents point at it or restate it under
`test_the_speedup_ranges_the_documents_quote_are_the_committed_history`, and the point figures in the
README, the interview document and the paper's own table are checked against the file by
`test_documents_quote_the_performance_figures_the_artifact_actually_holds`.
`test_the_performance_guards_are_not_vacuous` shifts the artifact by 1.5× and narrows one band by
hand, and requires both guards to reject the documents they had just accepted. The ordering claim
survives all thirteen measurements — C++ beats an interpreted loop by roughly an order of magnitude
and loses to vectorised NumPy for terminal-only payoffs — so no conclusion moved; what moved was the
honesty of the numbers attached to it.

**35. The guard written to close #34 was verified only in the environment it was written in.**
Its range check derived the documented band from `git log -- benchmarks/performance/results/monte_carlo_speed.json`
and required the documents to state exactly that min/max. Locally that reads thirteen measurements and
passes. The runner does not have thirteen: `.github/workflows/ci.yml` uses `actions/checkout` at its
default depth of 1, so the derivation saw the single revision at the tag and demanded that `README.md`
quote a `0.45–0.45` spread — run `36550420085`, `Configure, build, C++ tests, Python tests` →
`failure`, `1 failed, 334 passed, 4 skipped`. The failure was real and it was mine: a check that reads
history is a check about the *clone*, not about the repository, and I had asserted it was the same
thing. Note also that this file first asserted `gh run watch --exit-status` returned exit code 0 for that
run, and that assertion was **wrong in its own right**: the watcher exits **1** on that run, measured
directly on the completed `36550420085`, and the 0 belonged to the background wrapper whose last command
was an `echo`. The API's `commits/<sha>/check-runs` is what reported the failure, which is why the tag
was not created. See finding 36 for the correction of that sentence.

Two changes make the guard honest about which half is live where.
`test_the_documented_speedup_ranges_contain_the_current_measurement` pins the band and checks two
things that hold in any clone: the current artifact lies inside it, and each document states it.
`test_the_documented_speedup_ranges_match_the_committed_history` keeps the provenance check but
declares its precondition — it skips, naming `actions/checkout` depth 1, when fewer than two revisions
are visible, so a thin clone reports a skip rather than a wrong verdict or a silent pass.
`test_the_performance_guards_are_not_vacuous` gained the case that would have caught this before the
runner did: a band derived from one measurement is zero-width, and the pinned band must never be one.
The rule this leaves behind: any guard that shells out to git has to be run against a depth-1 clone
before it is claimed green, because the clone CI builds is not the clone the guard was written in. The fix was proven where the defect
lived: `36663508268` on `f4e8afc13bd7` is `completed / success` on all three jobs, the offline lane
printing `335 passed, 5 skipped in 50.26s`, and the fifth skip is that guard saying so in its own
words — `this clone carries 1 revision of the artifact (CI uses actions/checkout at depth 1), so no
spread can be derived; see the command in docs/reproducibility.md`. The pinned band is still checked
against the history min/max wherever a clone carries one, so the provenance did not disappear, it
acquired a precondition.

**36. The release notes repeated a claim this same file had already corrected.** Finding 35's first
draft said `gh run watch --exit-status` returned exit code 0 for the failed run. One hundred and
twelve lines earlier in the same document (`docs/integrity_audit.md:389`), the Phase 13 addendum
records that exactly this sentence was already tested and refuted: the watcher returned **1**, and the zero belonged to a background wrapper whose
last command was an `echo`. I wrote the disproved claim again because I reasoned about the tool from
the notification I had seen ("completed (exit code 0)") instead of reading the instrument again — and
nothing in the gate set can catch a sentence about a tool's behavior, since no test executes `gh`.

Measured now, on the completed failed run `36550420085`: `gh run watch … --exit-status` exits **1**.
The finding-35 text is corrected in place, and this entry exists so the correction is attributable
rather than silent. The rule it leaves is narrower than "verify before asserting": when a document in
this repository has already recorded that one of my own claims was wrong, that document is the first
place to read before making a claim of the same kind again.

## Addendum — Phase 15, the recommendation measured and the guards that argued about it (2026-09-30)

**37. A band guard could reject the measurement it was derived from.** `SPEEDUP_BANDS` is pinned in
`tests/python/test_artifact_metadata.py` because CI checks the repository out at depth 1 and a band
recomputed there comes from one revision (finding 35). Its companion guard required the *raw* current
ratio to lie inside the pinned band, while the history guard derives the band from the **rounded** min
and max of the committed ratios. The two conventions met the first time a re-frozen run landed at
`speedup_vs_numpy = 0.5104`: the documents' own upper edge, `0.51`, is what that value rounds to, and
the guard reported a measurement outside the band it was built from. Nothing about the artifact was
wrong; the guard pair disagreed about what a band edge *is*. Fixed by testing containment on the same
rounding the history guard uses, with the reasoning in the test rather than in a comment above it, and
`test_the_performance_guards_are_not_vacuous` still shifts the artifact by 1.5× to prove the band bites.
The general form: two guards that meet at a boundary have to agree about the units of that boundary, not
merely about its value.

**38. A shipped producer's helper ignored its own argument, and nothing could see it.**
`experiments/two_factor_error_bound/run.py:totals(spot, sigma)` scaled its `delta`, `gamma` and `vega`
entries by the module-level `SPOT` instead of the `spot` parameter. It never fired: only `BASE` is read
as an exposure, and the one call site that passes a moved market (`third_directional`) consumes only
the raw-partial entries, which have no spot factor. It was found by accident — the Phase 15 experiment
began as a copy of that helper and had the identical defect, and the first run of the new variant table
produced a gamma re-strike priced at the wrong spot. Both are fixed now, and Phase 13's experiment was
re-run to prove the published numbers are untouched: every field of `two_factor_bound.json` is
byte-identical except `generated_at_utc` and the dirty-tree list its own provenance records, and
`two_factor_bound.csv` is unchanged. A helper whose parameters are decoration is a trap for the next
caller, and the only real defence is that the next caller notices — which here was a copy.

**39. The recommendation this phase existed to test turned out to be half right, and the half that is
wrong is the interesting part.** `v1.3.0` closed with "re-strike gamma, do not add vanna and volga".
Measured on the published `risk_off`, it holds: the error falls to a factor of 0.364. Measured over the
120 swept cells with a volatility move, 45 are no better and 20 at least twice as wrong. The temptation
was to publish the scenario result and file the rest as noise; instead the worsening is characterised
arithmetically — every doubled cell is one whose shipped-map error was smaller than the term the recipe
removes — and then *predicted*: the zeros of a third-order truncation assembled from core closed forms
agree with the zeros of the priced error to 0.0002-0.0024 within `|delta| <= 0.05`, and drift to 0.093
outside it, with one column where the truncation predicts a zero the map does not have. That is a result
about the reach of the analysis rather than about the map, and it is published as such:
`docs/findings.md` §7 leads with the 45 cells, `docs/limitations.md` #78 keeps the scope, and
`stress.run_scenario` ships unchanged.

## Addendum — Phase 16, a closed form that was wrong at the tenor it was tested (2026-10-01)

**40. A published derivation was wrong by a factor that equals one at the point it was checked.**
`docs/phase_reports/phase-15-restrike-gamma.md` §8 recorded the four mixed fourth partials as groundwork
for Phase 16, and three of the five forms carried the wrong power of `T`: `V_SSSsigma` over `S^2 v^2
sigma T` instead of times `sqrt(T) / v^3`, and the same class of error on the two higher ones. The cause
was one operator: `d/dsigma|S` was written dividing by `sqrt(T)` where the chain rule multiplies by it,
because `dv/dsigma = sqrt(T)` with `v = sigma sqrt(T)`. What hid it was the verification, not the
algebra. The probe that should have caught it ran at `T = 1`, the single maturity the re-struck-gamma
experiment uses, and at `T = 1` the missing factor is exactly `1` — the residuals vanished and the check
read as a pass. Re-run across tenors, the residuals were proportional to `(T - 1)` and `(T^2 + 1)`. The
finite-difference form of the probe was then discarded for a second reason: at fourth order the `1/h^4`
amplification of double rounding swamps the signal, worst relative residual 255. What replaced both was
a coefficient *reconstruction*: the exact symbolic fourth derivative of the price, sampled at 80 decimal
digits, solved as a 28-coefficient linear system and re-tested on 200 fresh points per order spanning
`S` 40-160, `sigma` 0.08-0.60, `T` 0.08-3.0 with non-zero `r` and `q`; worst relative error 4.5e-77. Two
rules come out of it. A factor that happens to be 1 at the tenor you test is not a factor you have
verified. And an equality checked at one point is a transcription test, not a reading test.

**41. The same reconstruction found a second, unrelated error in the same block.** `R(0,4)` had been
committed with the opposite sign — no factor-of-one story explains that one, it was simply transcribed
wrong. Because the new method solves for the coefficients rather than copying them from a derivation, the
sign fell out of the linear system with the rest. Both are corrected in §8 of that report, which now
states the uniform shape `V = P S^(1-n_spot) T^(n_sigma/2) R(d1, v) / v^3` — the shared `v^3` denominator
and the fact that neither `r` nor `K` survives outside `d1` are what make the five forms usable in a core
whose model is BSM with a dividend yield rather than the chart's zero-rate case.

**42. A verification test asserted an identity about the wrong order, and only failed because the
arithmetic disagreed.** The core's `MixedFourthDerivatives` is checked, in part, by differentiating the
published homogeneity relations `vanna = V_SSS S^2 sigma T + 2 S sigma T gamma` and
`volga = V_SSsigma S^2 sigma T + gamma S^2 T`. A third relation was written for `V_Ssigmasigmasigma` as
"d(volga)/dS". It is not fourth order: `volga` is `d2V/dsigma2`, so one spot derivative lands on
`V_Ssigmasigma`, the third-order partial the core already publishes. The test failed by a factor of -14
against the number it claimed to check — which is the shape of the mistake rather than a tolerance
problem, and is worth recording because the same slip, had the two orders coincidentally agreed at one
point, would have produced a green test that proved nothing. Two of the four partials have an exact
published partner; the other two have no order-four partner to differentiate into and are held by finite
differences alone (three independent routes for each, worst residual-to-band 1.1e-2).

**43. A struct was bound to Python without its function, and the parity guard could not see it.**
`bindings/python_bindings.cpp` registers a class and a function as two separate statements. Only the
class was added, and `test_extension_surface_parity.py` — which compares the compiled module against
what the bindings file *declares*, in both directions — passed, because the declaration it was missing was
also missing from the source. The detector was not a guard but the new experiment calling the function and
raising `AttributeError`. That is the correct place for it in this case (the API is used by a producer that
would otherwise silently publish a truncation built on nothing), but the gap is real: nothing derives
"every public core entry point is reachable from Python". Recorded here as open rather than fixed, because
the list of what should be reachable is a claim the repository has not made anywhere.

Verification for the phase, in the tools' own words: `100% tests passed out of 201` (548,217 assertions in
200 Catch2 cases), `437 passed` under pytest, `suite: 16/16 executed and passed`, `7/7 checks passed`,
`ruff`/`mypy`/`clang-format` clean, `latexmk` output 42 pages. The fourth-order closed forms were also
re-derived against the shipped price function's exact derivatives before any C++ existed, so §8 of the
Phase 15 report, the core implementation and the three C++ test cases are three independent renderings of
the same five polynomials.

**44. A band sized from one machine rejected a machine that was not wrong.** Phase 16 gates the
fourth-order residual's fall on a log-log slope band of 4.6-5.2, derived from four rays measured here
(4.73-5.01). The CI runner, executing the identical committed artifact, measured 5.223 on the crash ray
and the experiment raised. Nothing had drifted in the mathematics: the quantity being fitted is the
*fifth*-order remainder, which is small relative to the noise of subtracting book values near 1.09e5,
so its fitted slope carries platform-dependent slack of a few hundredths. A band whose ceiling is one
observation plus a rounding margin is not a band around the integer, it is a copy of a laptop. The bands
are now 3.6-4.4 and 4.6-5.6 — clear of each other, and still excluding the orders they are not claiming:
a residual that fell with the third order reads 3.0, and the cubic's own 4.0 is not in the quartic band.
The general form, which this file has now recorded three times in three shapes (#37, #44, and the
`Assert in the measuring environment` rule): a tolerance derived from one measuring environment is a
claim about that environment, and the gate that encodes it has to be sized from every environment the
claim is going to be tested in.
