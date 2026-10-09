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

**44. A band sized from one machine rejected a machine that is not wrong — twice.** Phase 16 gates the
fourth-order residual's fall on a log-log slope band of 4.6-5.2, derived from four rays measured here
(4.73-5.01). The CI runner, executing the identical committed artifact, measured 5.223 on the crash ray
and the experiment raised. The band was widened to 4.6-5.6 on the theory that the ceiling was the
problem; the next CI round failed on the *floor* instead, with 4.323 on the shallow ray where this
machine measured 4.729. Nothing had drifted in the mathematics either time: the quantity fitted is the
fifth-order remainder, which is small relative to the noise of subtracting book values near 1.09e5, so
its fitted slope carries platform slack of a few tenths — and the slack is largest exactly on the ray
whose residual is smallest, which is why one edge is not enough to fix.

The shape of the gate changed, not just its numbers. A band whose ceiling is one observation plus a
rounding margin is not a band around the integer; it is a copy of a laptop. The absolute bands are now
gross-error checks (cubic 3.5-4.6, quartic 4.0-5.8), and the load-bearing ordering evidence is
scale-free: the quartic residual smaller in magnitude than the cubic's at every scale in the window, its
ratio falling monotonically over the three largest above-floor scales, and the two slopes compared
*within* a run with the sign gated and no margin.

The third CI round is the one that finishes the lesson. What round two left in place — the ratio's own
log-log slope, gated at `>= 0.5` and measured 0.62-1.04 here — came back at 0.381 on the shallow ray, so
the gate became a monotonicity test over `0.3, 0.1, 0.03`, the three largest above-floor scales, where
the residuals sit far enough from the floor for an ordering to mean the same thing on any machine. The
rule this finding actually leaves behind is therefore narrower and harder than "size the band from every
platform": *a gate on a quotient of two subtraction residuals is a magnitude gate wearing a relative
mask.* Ratio, slope and separation are all such quotients; only their signs and orderings travel between
platforms. The measured slopes and ratios are still published, each attributed to the machine that
produced it (`docs/analysis/fourth_order_crossing_map.md` §2), and it is the artifact's own
`reproduction_policy` that tells a re-run which of them it may compare by value. Third time, third shape
(#37, #44, and the `Assert in the measuring environment` rule): a tolerance derived from one measuring
environment is a claim about that environment.

**45. A reproducibility exemption written as a list of field names is a prediction, and the runner
proved it wrong a fourth time.** The committed `reproduction_policy.conditioning_limited` held six leaf
names (`residual_after_cubic`, `residual_after_quartic`, `residual_ratio_quartic_over_cubic`,
`measured_zeros` and the two nearest-zero distances). The runner re-ran the experiment in a temporary tree
and reported twenty differing leaves, every one of them under `rays.<label>` — three fitted slopes, two
standard errors, the ratio's own span statistics, `ratio_smallest`, `ratio_at_the_fit_floor`, and the
per-scale residuals and ratios beneath them. The message is capped at twenty entries, so the real count is
at least that. None of it is drift: each is a quotient of two residuals that are subtraction residue, or a
root located in one, exactly the kind finding 37 and limitation #75 already describe. What was wrong was
the *shape of the declaration* — a list of names can only ever be as complete as the last platform that
went through it.

Closing it by construction instead. The fitted headline numbers are now built into one nested block,
`headline.fits`, beside the counts and published amounts that stay flat in `headline`, and the policy reads
`["rays", "columns", "headline.fits"]`. A new fit joins the exemption by where it is computed rather than
by someone remembering to write it down. The runner's diff also surfaced a verdict in the same case:
`floor_turnaround` asks whether the smallest-scale ratio exceeds the next one up, and both sides of that
comparison *are* the floor, so the answer belongs to the platform. The producer declares that in
`reproduction_policy.noise_decided_verdicts`; the shared comparator honours the declaration only for an
experiment that makes one, so `two_factor_bound` and `restrike_gamma_map` keep every verdict gated, and the
local assertion in `test_fourth_order_crossing_map.py` still pins all four rays in *this* artifact rather
than relaxing the claim.

The guard test is `test_the_declared_families_cover_the_paths_the_runner_disagreed_on` and
`test_the_exemption_does_not_reach_a_count_a_closed_form_or_a_shape_change`: seven perturbed noise leaves
must be tolerated, and five perturbed real values plus a renamed field and a dropped zero must be caught.
Both directions were then mutated to prove they fire. Narrowing the declared families to `["rays",
"columns"]` turned the tolerance guard red on
`.headline.fits.residual_slope_cubic_span[1]: 4.366457010912464 vs 4.466457010912464 differ by more than
4.4e-05`; widening them to cover the whole payload turned the catching guard red on "a zero count inside
`columns` was replaced and the comparison said nothing". The artifact was restored from a byte copy and
verified with `cmp`. `uv run pytest tests/python/test_fourth_order_crossing_map.py` — 16 passed in 0.49 s.

The rule: *an exemption expressed as names predicts which numbers will move; an exemption expressed as
where a number is built states a property of it.* Four CI rounds is the price of the difference, and the
two-directional plant is what stops a fifth.

## Addendum — Phase 17, the check finding 43 said to write (2026-10-02)

Finding 43 was recorded open with the reason: *"the list of what should be reachable is a claim the
repository has not made anywhere."* Phase 17 makes the claim and enforces it.

The claim is keyed on `[[nodiscard]]`, because that attribute is the core already stating `this result is
the point of calling` — a stronger anchor than a list assembled in a test file. `tests/python/
test_extension_surface_parity.py` now reads every header under `cpp/include/quantrisk/`, takes the
namespace-scope declarations carrying it (85 names over 92 declarations), and requires each to be either
registered in `bindings/python_bindings.cpp` or disclaimed at its declaration by a `// python:` marker.
24 declarations are disclaimed, and a disclaimer is a checked fact rather than a sentence: `via X` has to
name a function the bindings really register, `via Class.member` has to name a field of a bound struct, a
marker sitting on a function that *is* bound is stale, and a marker left above a declaration that no
longer exists is orphaned. All four failure modes are planted in tests, and so is finding 43's own shape —
a new core function reaching neither a binding nor a marker — with the differential stated in the same
test: the two-way parity comparison that shipped in Phase 14 stays silent about it, which is exactly why
this third direction was needed.

Two things this does not claim, both recorded rather than glossed. The attribute is not applied uniformly
in the core, so a namespace-scope function *without* it is outside the claim; those are inventoried by a
separate test and pinned to exactly one name (`stats::quantile_linear`), so the residual is a list someone
must extend deliberately instead of a gap. And the markers' reasons are prose: the guard verifies the
route each one names, not that the reason is still the right one. Limitation #80.

Verification, in the tools' own words: `uv run pytest tests/python -q` — 446 passed; the parity file's own
13 tests in 0.27 s; `uv run ctest --preset dev` — 100 % tests passed out of 201 after the header edits;
`uv run --frozen clang-format --dry-run -Werror` on all 29 headers — exit 0; the falsification sweep on the
committed tree — 22/22 planted defects rejected, the new entry
(`core-declares-a-function-nobody-binds`) caught by the guard it names.
## Addendum — Phase 18, the transferability claim, and a radius that contradicted its own evidence
(2026-10-03)

**46. An artifact published a decision and the values it was decided over, and nothing compared them.**
`experiments/second_book_crossing_map/run.py` measures a crossing radius on five books. Its first version
walked the twelve columns in order of `|delta|` and stopped at the first failure — which is nearly the
right rule, and wrong in one respect: a magnitude carries *two* columns, `-x` and `+x`. On the long-dated
book the `-0.15` column passed at 0.00022, so the walk recorded 0.15 before the `+0.15` partner at 0.02347
stopped it. The artifact then carried `radius_cubic = 0.15` and, four fields away,
`worst_distance_inside_cubic_radius.cubic = 0.0235` — a radius containing a column the same file called a
failure, against a tolerance of 0.005. Both fields were published; both were checkable; no guard read them
together. It surfaced by accident, when a note-figure test asked for a value the artifact no longer
carried and the two disagreed.

The fix is in three places rather than one, because one fix would leave the same shape reachable again. The
rule groups by magnitude and requires every crossing column at that magnitude to pass. `check()` refuses
to publish a radius whose widest in-range distance exceeds the tolerance, so the contradiction is now
unrepresentable rather than merely unfashionable. And `tests/python/test_second_book_crossing_map.py`
re-derives every radius from the artifact's own distances — including re-deriving each stored
`*_within_tolerance` verdict, so the radius is built from numbers rather than from the producer's yes/no —
and plants the asymmetric pair in *both* column orders, because the defective walk agreed with itself
whenever the failing sign happened to come second. The negative control ran on a copy of the tree with
`all` replaced by `any`: the run refused to publish, naming the book, the 0.3 radius and the 2.347e-02
distance.

The rule: *a field that is a decision over values another field carries is a second source of truth, and
publishing both without a comparison between them is how a wrong rule survives its own artifact.* The
phase also corrected what the published claim had been: the direction of the order-four widening transfers
to 5 of 5 books and its magnitude to none — `0.05 -> 0.15` is one ladder's pair, the five factors are 1.3
to 3.0 — and the mechanism v1.6.0's note leaned on, the order-four-to-three ratio, does not order the
widening at all. `docs/limitations.md` #81, validation row 20, and a dated correction in
`docs/release_notes_v1.6.0.md` carry that; `docs/analysis/second_book_crossing_map.md` §3 argues it.

**47. The evidence freeze hashes the directories it names, and its verifier cannot see a directory it
was never told about.** `scripts/build_evidence_manifest.py` walks a hand-kept list of result
directories. Phase 18 added `experiments/second_book_crossing_map/results/` and the freeze stayed at 83
artifacts, while `verify_evidence_manifest.py` reported `0 MISSING` and `0 on disk but not in the
manifest` -- both correct about the list it walks, and silent about the one thing outside it. A new
experiment's evidence is therefore invisible to the mechanism whose job is to notice that evidence
changed, which is finding 25's "absence produces no output" one level further down the stack: the guard
there was checking that a *check* ran, this one is that the *population* was enumerated.

Closed by deriving the population from the tree:
`tests/python/test_artifact_metadata.py::test_the_manifest_hashes_every_experiment_results_directory`
compares the frozen manifest's entries against `experiments/*/results` on disk, and the sweep carries
`experiment-results-the-evidence-freeze-never-saw` -- a probe directory no one declared -- so CI re-runs
the proof that an undeclared directory is caught rather than counted as clean. The directory itself is now
declared and the manifest re-frozen at 85 artifacts.

Verification for the phase, in the tools' own words: `uv run pytest tests/python -q` -- 459 passed;
`uv run ctest --preset dev` -- 100 % tests passed out of 201; `uv run ruff check .` and
`uv run ruff format --check .` -- all checks passed, 138 files already formatted; `uv run mypy
python/quantrisk` -- no issues in 23 source files; `uv run clang-format --dry-run -Werror` on the 29
headers -- exit 0; `uv run python scripts/run_benchmark_suite.py --require-all` -- `17/17 executed and
passed, 0 skipped, 226.4s`; `uv run latexmk -pdf` -- 44 pages, 1001529 bytes; and the falsification
sweep on the committed tree (`2e8142a`) -- `27/27 planted defects were rejected by their guard.`


## Addendum — Phase 19, the debt item Phase 17 published about itself (2026-10-03)

**48. An inventory was right for a reason that had nothing to do with the scanner that produced it.**
Phase 17 closed finding 43 with a claim keyed on `[[nodiscard]]`, and a second test whose whole job was
to list what that key missed. The list came out as exactly one name, `stats::quantile_linear`, and the
test pinned it. The scanner that produced it, though, walked back from a declaration's name to the
previous newline to find the statement's start -- and these headers wrap. `[[nodiscard]]
MixedThirdDerivatives` and the function name on the next line are one declaration, and that walk read
the name's line alone, concluded nothing was marked, and reported it. Calling the function directly on
the tree returned 23 names, not one. What made the test correct was an unrelated filter: the residual
dropped any name the attribute scan had already covered or the bindings already registered, and every
false positive happened to satisfy one of those. So the assertion held, the prose figure was right, and
the instrument underneath was wrong -- which is the shape of finding 25 again, one level down: a check
whose passing does not demonstrate what it claims to demonstrate.

Phase 19 removes the ambiguity rather than documenting it. A declaration's statement now begins at the
previous `;`, `}`, `{` or blank line, so a wrapped attribute is seen by both scanners; the population of
the claim is every namespace-scope declaration, marked or not, and the residual is asserted *empty*
instead of inventoried. The parser's own test pins the shapes that used to fool it -- an attribute on the
name's own line, an attribute a line above the name, a struct member (which must NOT count), and one
genuinely unmarked declaration, the only name that may be reported.

The debt item itself closed the same day. Seventeen functions in four headers carried no attribute:
`sum_compensated`, `mean`, `sample_variance`, `sample_stddev`, `quantile`, `mean_of_largest_sorted`,
`autocorrelation`, `standard_error_of_mean` and `quantile_linear` in `core/statistics.hpp`; `version` and
`build_metadata`; `normal_pdf`, `normal_cdf`, `inverse_normal_cdf`; and the three covariance estimators.
Every one returns a value that is the point of calling it, so every one is marked now, and
`quantile_linear` -- the only one that stays unreachable from Python, because it takes data the caller
already sorted -- carries the disclaimer at its own declaration, where the guard tests the route it names
instead of reading the sentence. The surface is 109 namespace-scope declarations, 101 distinct names, 25
disclaimed, and no guard reaches the three things still outside it: class members, the truth of a
disclaimer's reason, and functions declared only in a `.cpp`. Limitation #80 states those; the counts are
policed by `test_the_documents_that_count_the_core_surface_count_it_correctly`, whose own plant edits one
of them in the register.

Verification, in the tools' own words: `uv run pytest tests/python -q` -- 460 passed; the parity file's
own 14 tests; `uv run ctest --preset dev` -- 100 % tests passed out of 201 after the header edits and a
full rebuild; `uv run ruff check .` and `uv run ruff format --check .` -- all checks passed, 139 files
already formatted; `uv run mypy python/quantrisk` -- no issues in 23 source files; `uv run clang-format
--dry-run -Werror` on the 29 headers -- exit 0; the falsification sweep on the committed tree
(`5bb7e12`) -- `29/29 planted defects were rejected by their guard.` No artifact was regenerated, so the
manifest frozen at `2e8142a` still verifies: `85 OK / 0 CHANGED / 0 MISSING / 0 unlisted`.

---

## Addendum — Phase 20, a count three documents repeated and a check that could not fail (2026-10-04)

**49. A guarded fact is not a guarded document.** `test_documents_that_count_the_cpp_tests_agree_with_the_build`
owns the C++ totals by matching one pattern per document — `# (\d+) C\+\+ tests` in the README and the
reproducibility note, `(\d+) C\+\+ tests under CTest` in the interview file. When this phase's three new
`TEST_CASE`s took CTest from 201 to 204, the guard named the three, went red, and the three were fixed. The
same two documents carried four more restatements of the same fact that no pattern reaches: `Today that is
201 C++ tests (548,217 assertions in 200 cases)`, a command line annotated `# 201 C++ tests`, a citation table
reading `201 / 423 now` against a Python count that had moved twice since, and — in the same table row — `docs/limitations.md`
`(66 entries)` while the register held 81 at the phase's start and 82 at its end. Pattern-keyed coverage counts
phrases, not claims, so a document can be simultaneously guarded and wrong about the number it is guarded on; the
stale `66 entries` had outlived two releases without any gate noticing. All seven spots are synced now and the
plant `readme-overcounts-the-cpp-suite` re-keys to the new figure. What is *not* fixed is the assertion and
Catch2-case totals (`548,368` in `203` cases): CTest lists tests, not assertions, so the only cheap owner is a
count of `TEST_CASE` in `tests/cpp/*.cpp` for the case total, and the assertion total has no derived source at all
and stays prose. Phase 19 debt item 3 lists that residue and this phase did not close it.

**50. An assertion that returns True whatever the expression is.** The derivation script this phase added
(`scripts/derive_fifth_order_partials.py`) gated the parsed source numerator with
`expression.is_polynomial(W, V)`. `sp.symbols("w v", real=True)` and the `Symbol("w")` that `sp.sympify`
produces from a bare name are *different sympy objects*, so every parsed `w` was treated as a coefficient and
the check reported True on any expression, including one carrying a stray `sigma` — the counterexample is in
the phase report. Free-symbol containment (`expression.free_symbols <= {W, V}`) is what gave the assertion a
population, and the degree caps that came with it replaced a cap I had written from reasoning rather than
measurement: `total_degree <= 5` is false on this family, whose pure-volatility numerator contains `d1^8`, and
it fired on `q23` before anything shipped. Same class as finding 48 — a check whose stated population is
smaller than the fact it names — and worth the record precisely because the defective check was written by the
phase whose subject was making derivations verifiable.

Verification, in the tools' own words: `uv run ctest --preset dev` -- 100 % tests passed out of 204, and
`./build/dev/quantrisk_tests --verbosity quiet` -- `All tests passed (548368 assertions in 203 test cases)`;
`uv run pytest tests/python -q` -- 465 passed; `uv run quantrisk validate` -- 7/7; `uv run ruff check .` -- all
checks passed; `uv run ruff format --check .` -- 142 files already formatted; `uv run mypy python/quantrisk` --
no issues in 23 source files; `uv run clang-format --dry-run -Werror` on the eight touched C++ files -- exit 0;
`uv run --with sympy python scripts/derive_fifth_order_partials.py` -- exit 0, part A's six worst relative
disagreements between `4.7e-59` and `8.7e-58` over 60 markets and part B's worst `4.619e-15`, and its own
negative control -- planting a one-unit slip in `q32` produced `q32: worst relative disagreement 300.0` and
`FAILED: ['q32']`, with the file restored byte-identically (sha256
`92e8bb61c2527c99768b9d2eef67a0f02865b0f3bf8d09f074d942e6f4bdaf8e` both sides) and exit 0 again. No artifact was
regenerated, so the manifest frozen at `2e8142a` still verifies: `85 OK / 0 CHANGED / 0 VOLATILE / 0 MISSING /
0 unlisted`.

---

## Addendum — Phase 21, the gate that fired on a correct result, and the plants my own sync disarmed (2026-10-04)

**51. A refusal can only be trusted on a case it is aimed at.** `experiments/fifth_order_crossing_map`
publishes, for each order, the contiguous paired-magnitude radius and the worst nearest-zero distance
inside it, and refuses to write an artifact when a radius contains a column outside the tolerance that
defines it. The first version looked each order's worst distance up in the *quartic's* range -- a dict
that already had all three orders keyed by name, so nothing looked wrong about indexing it by order --
and the run died on its own control book: the published ladder's cubic radius of 0.05 was rejected
because a column at 0.15 sat 1.89e-02 away, a column that radius never claimed to cover. The defect is
invisible in the direction a validator is normally tested: it fires, loudly and with a correct-looking
message, on data that is fine, and it would have *passed* an incoherent radius whose own range happened to
be clean. So the gate was proved by aiming it at both cases -- a loose column outside the cubic radius
must not reject it, and identical numbers with the loose column inside it must -- which is what
`test_a_radius_is_judged_only_by_columns_inside_it` now pins, with `fifth-order-radius-judged-by-another-orders-range`
planting the original conflation back into the producer to show the guard can still fail. The same
conflation is what Phase 18 had to fix twice in the radius *rule*; finding it a third time, in the check
that was written to catch it, says the shape is easy to re-enter and worth a named test each time.

**52. Editing the prose silently disarmed the falsification harness.** Eight of the 30 declared plants key
on figures this phase moved -- the matrix row count, the suite count, the Python test totals, the README's
speedup. Re-keying them produced two entries whose `replacement` was identical to the new `anchor`,
because the documents had caught up with what the plant was trying to assert: the sweep would have
reported `33/33 planted defects rejected` while those two planted nothing at all. A harness that
verifies its targets must also police its own list, and `test_every_declared_mutation_names_one_unique_anchor_and_a_guard_that_exists`
did exactly that job -- it refused the identical pair, and separately refused two anchors that no longer
occurred and one whose edit would have overwritten a tracked file under `kind="tree"`, which in this
harness means "a file that must not exist yet".

**53. The sweep caught a plant that proved nothing.** Its own line: `32/33 planted defects were rejected
by their guard`, and the escape was `fifth-order-sums-drop-the-book-quantity`, which replaces the book
quantity in the experiment's `fifth_order_sums` and named
`test_the_core_sums_behind_the_quintic_term_are_the_shipped_ones` as its guard. That guard is a check of
the *artifact against the bindings*: it recomputes the six sums from `black_scholes_mixed_fifth_derivatives`
without calling the producer's helper, deliberately, because a test that imported the producer's own
function would certify only that the file agrees with itself. The consequence is that no edit to the
producer can turn it red, so the plant was aimed at a wire the mutation never touches -- a link error,
not a weak guard, and invisible to every check except running the sweep and reading the one line that
says `guard-stayed-green`. Fixed by pointing the plant at the reproduction test, which does consume the
helper, and adding the counterpart plant the guard actually needed: `artifact-publishes-a-book-sum-the-core-does-not`
perturbs one published sum in the artifact by a digit, which is the only thing that check can see. The
list is now 34 entries, each with a guard that reacts to the edit its identifier describes.

Verification, in the tools' own words: `uv run python scripts/run_benchmark_suite.py --require-all` --
`18/18 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 174.9s total`;
`uv run pytest tests/python -q` -- 477 passed; `uv run ctest --preset dev` -- 100 % tests passed out of
204; `uv run quantrisk validate` -- 7/7; `uv run ruff check .` -- all checks passed;
`uv run ruff format --check .` -- 147 files already formatted; `uv run mypy python/quantrisk` -- no issues
in 23 source files; `uv run latexmk -pdf` -- 44 pages, 1003152 bytes; the manifest rebuilt over the new
results directory and verified at `94 OK / 0 CHANGED / 0 VOLATILE / 0 MISSING / 0 unlisted`, then re-frozen
on the committed tree; `uv run python scripts/run_mutation_suite.py --list` -- 34 plants declared; the sweep on `fb556cd` -- `34/34 planted defects were rejected by their guard` (its first run, on `e5bb43e`, reported 32/33 and named the escape).

---

## Addendum — Phase 22, the runner finding what the laptop could not (2026-10-04)

**54. Two assertions passed on every darwin machine and were wrong, and a third gate described them
badly.** The `v1.7.0` version bump required re-running the whole suite, and the push that carried it also
carried Phase 21's tests to a Linux runner for the first time. It went red twice, for two different
reasons, and green locally each time.

(a) `test_the_core_sums_behind_the_quintic_term_are_the_shipped_ones` compared a published book sum with
one recomputed from the bindings **bit for bit** -- `-78.60804475268505` against
`-78.60804475268517`. The gap is `1.5e-15` of the value: `libm`'s `exp`/`log` differing in the last bits
between the two platforms, which is precisely what `docs/limitations.md` #63 already says the
reproduction comparator handles with `1e-12` relative slack. The assertion was written as the strongest
thing that passed locally, and the strongest thing that passes locally is not the claim the repository
makes. It now asserts the documented slack, and its plant moved with it: a digit flip four places into
the mantissa, which is `1.3e-5` and cannot be confused with a platform difference.

(b) `docs/limitations.md` still said the offline lane collects `396` tests while `README.md`,
`docs/reproducibility.md` and the report had all been moved to `408`. The guard that polices this pair
keys per document, and the sentence in `limitations.md` is phrased a fourth way -- "the same tree
collects 396 tests without it" -- so nothing caught it until CI ran the lane that has no oracles. This
is finding 49's shape again one sentence over: pattern coverage is coverage of phrases, not of claims.

(c) The manifest's own wording overstated. After the bump `verify_evidence_manifest.py` reported `8
CHANGED (result content differs)`, and every one of those eight differed only in a timestamp, the
embedded `quantrisk` version, the `git_commit`/`binary_git_commit` pair, the `uncommitted_paths` list, a
sibling CSV's hash, or a wall-clock column. Checked leaf by leaf: no non-timing leaf moved in any of them,
and the two CSVs were re-parsed with their `runtime_seconds`/`paths_per_second`/`seconds_per_path`
columns dropped -- 24 and 36 rows, identical. The distinction the tool exists to draw (reproduction
versus tampering) is therefore right in its verdict and wrong in its sentence: a freeze that moves for
provenance reasons is described as though a number had moved. Recorded rather than quietly re-labelled,
because the day something real moves, that is the sentence a reader will trust.

Verification, in the tools' own words: `uv run pytest tests/python -q` -- 477 passed; `uv run ctest
--preset dev` -- 100 % out of 204; `uv run quantrisk validate` -- 7/7; `uv run ruff check .` -- all
checks passed; `uv run ruff format --check .` -- 148 files already formatted; `uv run mypy
python/quantrisk` -- no issues in 23 source files; `uv run clang-format --dry-run -Werror` on the four
touched C++ files -- exit 0; `uv run python scripts/run_benchmark_suite.py --require-all` -- 18/18
executed and passed, 158.7 s; `uv run latexmk -pdf` -- 44 pages, 1003118 bytes.

## Addendum — Phase 23, the report that contradicted itself (2026-10-05)

**55. Three present-tense sentences in `paper/technical_report.tex` described a repository that no
longer existed, and the one that mattered shipped in `v1.7.0`.** The completion audit run after the
release read the document rather than the gate output, and found what no guard could: a report whose
guards all compare numbers, in a document whose defects were sentences.

(a) §Limitations opens "The manifest is committed and verified: 69 artifacts, 6,208,835 bytes, of which
8 correctness benchmarks, 1 performance benchmark, 40 statistical experiment files, 4 suite-aggregate
files and 16 offline fixtures". That triple is *exactly* `evidence/manifest.json`'s `totals` at
`v1.1.0` -- 69 / 6208835 / 40, read from the tag -- and the sentence has been shipped in `v1.2.0`,
`v1.3.0`, `v1.4.0`, `v1.5.0`, `v1.6.0` and `v1.7.0`. The same PDF's §1 prints "the frozen manifest hashes
94 artifacts". One document, two statements of one fact, the stale one six releases old, and no reader
between them: `test_the_report_states_the_manifest_the_freeze_produced` now reads all seven numbers out
of the manifest's `totals` block and compares them with the sentence.

(b) §Stress Testing said, in the present tense, that "the experiment that would use these terms was
specified and then deliberately not run" -- written at Phase 20 (`631d7c5`) as a true sentence about
`experiments/fifth_order_crossing_map/`, refuted by Phase 21, which ran it, registered it as member 18
and published `experiments/fifth_order_crossing_map/results/fifth_order_crossing_map.json`. It was still
in the file when `v1.7.0` was tagged, so the released PDF asserts that a delivered experiment was
withheld. Phase 21 synced the documents a guard pushes -- matrix row 22, limitation #83, the suite and
test counts -- and the report's paragraph had no guard, because the claim carried no number. Two guards
close that shape: the report must name the directory of every experiment the suite registers
(`test_every_registered_experiment_is_named_in_the_report`, which would have been red from Phase 21
onward), and the paragraph's five figures are re-derived from the artifact's `headline`, `books` and
`fits` (`test_the_report_states_the_order_five_headline_the_artifact_holds`).

(c) Two smaller restatements of the same kind. §Limitations said the report's own member count was what
`README.md` "quotes for ``twelve members executed''" -- README has not contained that string since the
suite grew past twelve, and the sentence had been rewritten to describe the *kind* of claim rather than
a value it no longer holds. And `docs/interview_defense.md` annotated the sweep's command with
`# 18/18 planted defects rejected`, written at Phase 14 (`74359f9`) when the harness held eighteen
plants, against 38 now: a command comment is an instruction, and an instruction that names a superseded
count teaches the reader that the falsification harness is a third of its size.
`test_a_command_line_that_counts_plants_counts_the_declared_ones` reads the annotation, and the dated
records that quote their own run's verdict stay as they are.

**Falsification, measured rather than asserted.** Each of the three report guards was run against
`paper/technical_report.tex` as committed at `8680d63` -- the document as shipped -- before the fix was
written. (a) reported three violations -- 69 artifacts against the freeze's 94, 6,208,835 bytes against
7,145,018, and 40 statistical experiment files against 65. (b) reported `['experiments/fifth_order_crossing_map/']` as never
named. (c) reported the widening string and the ratio span absent. All four new guards therefore can
fail, and four plants declare the defects they catch:
`report-counts-a-manifest-the-freeze-does-not-have`, `report-drops-an-experiment-from-its-own-account`,
`report-quotes-a-stale-order-five-headline`, `docs-command-comment-counts-superseded-plants`. The
harness grew 34 → 38 declared plants, and two anchors that the count sync disarmed
(`readme-undercounts-the-limitation-register`, `report-counts-stale-python-tests`) were caught by
`test_every_declared_mutation_names_one_unique_anchor_and_a_guard_that_exists` before any of this was
committed -- finding 52's failure mode, firing as designed.

(d) **The same shape repeated inside the phase that fixed it.** Four guards added four tests, the
with-oracles count was synced 477 → 481 on the laptop, and the offline reading in
`docs/limitations.md` #63, `docs/reproducibility.md`, `docs/interview_defense.md` and the report still
said 408 -- the runner, the only environment with no oracles to collapse, collected 412. Finding 54(b)
was this fault at the previous release, so the lesson is not that one document drifted but that the
offline count has no local owner at all; it is registered as Phase 23 §8 item 2 rather than patched in
silence.

**What the released asset cannot be told to do.** `v1.7.0`'s `technical_report.pdf` was built from the
tag, so the sentences above are in it and cannot be removed without moving the tag, which would break
the provenance the release records. `docs/release_notes_v1.7.0.md` carries a dated erratum naming both
sentences instead, and the repository's own `paper/technical_report.pdf` is rebuilt from the corrected
source. `docs/limitations.md` #84 states the residue: the guards own the shapes they name, and a false
sentence with no number and no registered path is still caught only by a reader.

## Addendum — Phase 24, a command nobody ran and a build that lagged its source (2026-10-06)

**56. "Re-runnable" is not "run", and two documents were free to agree on a number nothing produced.**
Phase 20 shipped `scripts/derive_fifth_order_partials.py` as the reason the order-five numerators are
*derived* rather than typed, and the records quoted its output: `docs/validation_matrix.md` row 21 says
"8.7e-58 worst relative over 60 markets, re-runnable", and §Stress Testing of the technical report says
"$8.7 \times 10^{-58}$ relative worst at 60 working digits". Both were true as statements about the file.
Neither was a measurement the repository performed: `sympy` was not a dependency of any group CI installs,
and no test invoked the script, so between Phase 20 and this phase the identity ran only when a human chose
to type `uv run --with sympy ...` -- which after Phase 21 changed the same file's neighbourhood is never.
A committed command with no executor is worse than a sentence, because it reads like an owner.

(a) **The fix has to make the number produced, not available.** `sympy` moved into
`[dependency-groups] dev`, which is the group `uv sync` installs in all three CI jobs (the `oracles` extra
remains opt-in, so the offline lane is still offline), and
`tests/python/test_fifth_order_partials.py::test_the_derivation_command_agrees_at_the_precision_floor`
executes the script in a subprocess and asserts part A's six fields at the script's own `1e-40` floor and
part B's grid summary at the `1e-12` cross-platform slack `docs/limitations.md` #63 documents. Part B is
banded rather than compared digit for digit because finding 54(a) is exactly what happens when a float64
`libm` difference is asserted as equality.

(b) **The two quotations now have to agree with each other and with the run.** The test reads row 21 and the
tex sentence, requires identical `(mantissa, exponent, market count)` triples, and requires the run's worst
residual to sit in the same order of magnitude as the quoted one. The mantissa is deliberately *not*
asserted: the last digits of a 60-digit mpmath residual are not a cross-platform fact, and a guard that
required them would be a false-positive machine. An order of magnitude is portable, and the failure this
catches moves by dozens of orders.

(c) **Falsification, before the commit.** With `v_value**4` changed to `v_value**3` in the derivation's
prefactor quotient -- the shape claim, not a coefficient -- part A reported
`FAILED: ['q50', 'q41', 'q32', 'q23', 'q14', 'q05']`, the script exited 1, and the new test went red on the
first assertion. Restored from a captured copy and hash-verified: `9b2431c47a9a46e067ce1b569e0467b879fea229c734d10e424acea0f3e65375`
before and after. The harness carries it as `derivation-prefactor-exponent-off-by-one` (39 plants declared),
and the routes that check the same numerators by finite difference cannot see it: they are banded at `1e-3`
relative in Python and `1e-8` in C++.

(d) **A second instance of the hole `docs/reproducibility.md` already names.** While writing the release-page
erratum I rebuilt `paper/technical_report.pdf` and found the committed copy had been built *before* the
offline test count moved 408 → 412, so the tree held a PDF quoting a number its own `.tex` no longer
contained. The note says plainly that nothing on the runner verifies PDF-against-tex, and records a Phase 11
instance; this is the second. The PDF is rebuilt here and the rule from now on is that a tex edit rebuilds it
in the same commit, but the *owner* is still missing, because checking it needs a PDF text extractor as a
project dependency, which the repository has declined on purpose.

(e) **The release body and the release note are two documents restating one release.** `gh release view v1.7.0
--json body` returns 92 lines; `docs/release_notes_v1.7.0.md` holds 111 and gains dated corrections the
GitHub page never received. Nothing compares them, and a guard that would have to call the API is a network
test this suite does not run. Registered rather than fixed; the erratum was written into both on 2026-10-06,
and the pre-edit body is committed at `docs/release_bodies/` so the edit is reversible by anyone.

## Addendum — Phase 25, the two numbers CTest cannot see (2026-10-06)

**57. Four documents quoted a C++ total that no C++ check produced, and the phase that fixed it found
its own guard was the fifth such quotation.** `548,368 assertions in 203 test cases` sat in the README,
`docs/reproducibility.md`, `docs/interview_defense.md` twice and `paper/technical_report.tex`. Finding 49
had named this residue three phases ago -- "CTest lists tests, not assertions, so the only cheap owner is
a count of `TEST_CASE` in `tests/cpp/*.cpp` for the case total, and the assertion total has no derived
source at all and stays prose" -- and Phase 25 closed it by taking the second producer seriously as well:

- the assertion total is read from the compiled binary's own summary line
  (`./build/<preset>/quantrisk_tests --verbosity quiet` prints
  `All tests passed (548368 assertions in 203 test cases)`);
- the case total is counted from `tests/cpp/*.cpp` (`203` `TEST_CASE(` blocks) and required to equal the
  binary's, so the documents are quoting a compiled suite that is the source they describe, not one number
  quoted by five files;
- the CTest entry count is left to `test_documents_that_count_the_cpp_tests_agree_with_the_build`, because
  finding 49's other lesson is that a second owner of one number is a second chance to be wrong.

Falsification, both arms. The document arm is declared as `readme-quotes-a-stale-assertion-total`
(39 → 40 plants) and was additionally run live before the commit: `548,368` → `548,000` in the README,
guard red at `tests/python/test_artifact_metadata.py:1037`, README restored to
`f7df438e01206b8a30c515b9efd67ceddc6ac8080cb3e2d5d73a8f26fdecf770`. The source arm cannot be planted
textually without recompiling, so it was exercised in memory: appending one
`TEST_CASE("probe", "[probe]") {}` moved the counter from 203 to 204, which is the difference the guard
compares against the binary.

The residue this leaves is stated in `docs/limitations.md` #85: the guard skips where nothing has been
built, so its coverage is exactly the lanes that compile, and the offline Python test count moved again
with the new test (413 → 414), this time measured by the oracle-free probe rather than waited for --
`docs/reproducibility.md` says which instrument produced which figure.

## Addendum — Phase 26, the number only the runner could see (2026-10-06)

**58. Two findings in a row were caused by a figure that is measurable in exactly one of the two
environments the repository documents.** `docs/limitations.md` #63 states the Python test count as a pair
-- with the `oracles` extra and without it -- and forbids deriving one from the other, because the
oracle-gated modules collapse into module-level skip records whose count is not a constant of the
difference. The consequence nobody faced was that the second half of the pair had one producer: the CI
lane. Phase 23's finding 55(d) and Phase 24's §5 are the same event twice -- a phase adds tests, syncs
the number it can measure, and discovers the other from a red runner one push later.

`scripts/measure_offline_collection.py` is the second producer. It reads the `oracles` extra and the `dev`
group out of `pyproject.toml` and blocks the difference (`QuantLib`, `cvxpy`, `pypfopt`, `sklearn`,
`statsmodels` -- not `scipy`, which the CI lane does install), seeds `sys.modules` so an import fails the
way an absent distribution fails, and collects in a child interpreter. Measured on this tree: 415 items,
four module skips, zero collection errors, against 484 with the oracles installed.

**The guard checks that the probe is the runner's shape, not this machine's.**
`test_the_offline_test_count_is_measurable_before_the_runner` refuses a probe that produced collection
*errors* instead of skips (the first version did, by raising from a finder), requires four skip records,
and requires the blocked set to be non-empty -- a probe blocking nothing would report the online figure
and look correct. It then compares every living quotation of the offline count with the measurement, which
is the assertion the older count guard cannot make in an environment that has the oracles. Falsified before
the commit by the declared plant `report-quotes-a-count-the-offline-probe-refutes` (40 → 41 plants), and
twice incidentally by the phase itself: adding the guard's own test moved the measurement to 415 and the
guard went red against the 414 the documents still said, which is the failure it exists to produce.

**Fidelity, the honest account.** One comparison against the runner exists so far: the probe reported 413
at the revision where the runner's guard message said `pytest collects 413`. A second is in flight (the
Phase 25 head, expected 414) and its reading is recorded in `docs/phase_reports/phase-26-offline-count-owner.md`
§9 when it lands. One agreement does not prove the simulation, so the claim carried here is the
disagreement-detection property -- the probe says a quotation is stale before the runner has to -- and the
runner remains the arbiter of the published pair.

## Addendum — Phase 27, what a document is allowed to say without an owner (2026-10-07)

**59. A guard over a document only reaches the phrasing it was written to match, and the report had
three consequences of that.** The instrument this phase added is
`tests/python/test_artifact_metadata.py::test_every_countable_claim_in_the_report_is_owned_or_declared`:
it inventories every `<number> <countable noun>` claim in `paper/technical_report.tex` and requires each
to be owned by a named guard, inside the span a guard compares as a block, cited to an artifact the
evidence freeze hashes, or declared with a reason. Measured on this tree: 45 claims, 9 owned, 4 inside the
manifest sentence, 19 cited to a frozen artifact, 13 covered by 9 declared exemptions, 0 unowned.

(a) *The abstract and the section stated one fact two ways, and only one was compared.* The abstract
carried `55 recorded limitations` while `docs/limitations.md` had 85 entries at the start of this
phase (86 now) and the report's §Limitations said so in another phrasing that
`test_documents_that_count_the_limitations_agree_with_the_file` did compare. This is finding 55's
mechanism, not finding 55's residue: that finding was closed by comparing the two statements that
existed at the time, and the pattern recurred in a paragraph nobody had keyed. Extending the owner to
both phrasings went red immediately with `paper/technical_report.tex says ['85', '85', '55']` -- the
defect was in the tree, so no synthetic mutant was needed to prove the guard bites.

The released asset was then read rather than inferred, because a claim about what a published PDF
says is not answerable from the repository. `gh release download v1.7.0 -p technical_report.pdf`
(1,003,093 bytes, the digest the release note records) through `pdftotext` puts
`was not established: 55 recorded limitations` on line 27 of the released text, while lines 373 and
2490 of the same file state the register `contains`/`holds` **83** numbered entries -- and
`git show v1.7.0:docs/limitations.md`, counted by the repo's own numbering rule, is 83 contiguous
from 1. So the shipped report carries three statements of one quantity, one of them 28 entries
behind, and the stale one is on the first page. Corrected by dated erratum on the release page and in
`docs/release_notes_v1.7.0.md`; the tag and all four assets are untouched, per the rule the first
correction stated.

(b) *A digit guard can certify the transcription of two different quantities.*
`_quoted_identity_floor` compared `docs/validation_matrix.md` row 21's `(8.7e-58 worst relative over 60
markets)` against the report's `8.7 × 10^{-58} relative worst at 60 working digits` with one `groups() ==
groups()` assertion. Its third group is a *market count* on one side and a *working precision* on the other;
the comparison held because both read 60, and it would have stayed green if the report claimed a grid the
script never evaluated. Meanwhile the report's own market count -- `meets it at 60 markets` -- was read by
nothing at all. The helper now matches each figure to its producer in the run's stdout: markets against
`60 markets, realised d1 from ...`, digits against `part B: 60-digit nested numerical ...`, and the residual
mantissa and exponent across the two documents.

(c) *Two numeric sentences have no producer, and the guard says so.* `200,000 paths over 250 steps` and
`20, 80 and 320 steps` describe Heston probes. No Heston artifact exists under `benchmarks/` or
`experiments/` -- the manifest lists none -- so the only record of those runs is
`docs/model_cards/heston.md`, which is version-controlled but not content-hashed. They are carried as
declared exemptions anchored on the sentences themselves, and the asymmetry is registered as
`docs/limitations.md` #86: a citation makes a number traceable to a producer, a declaration records only
that a human read the sentence.

(d) *A simulation is only faithful in the lever it copies.* Phase 26's probe blocks the
`oracles`-only packages by setting `sys.modules[name] = None` in a child interpreter, and this phase
ran that child as a *test session* instead of a collection to see whether the lane could be predicted
locally. It could not, and the failure was specific:
`test_the_documents_that_count_python_tests_count_the_ones_that_exist` answers "what does this
environment collect" by spawning `pytest --collect-only` in a subprocess of its own -- which does not
inherit the parent's block, because here the distributions are installed and merely unimportable. The
parent therefore read the offline figure, the child collected the online one, and the blocked session
printed `1 failed, 415 passed, 4 skipped` where the CI lane prints no failure. `_collect_in_this_environment`
now hands the same block down, after which the identical session is green: `416 passed, 4 skipped`,
exit code 0, and its collected figure equals the probe's. The residual gap is platform state rather
than instrumentation -- the runner's own tally read `414 passed, 5 skipped` against the 415 items its
probe collected, one item skipping on Linux where it passes here -- and `docs/limitations.md` #63 now
says so instead of leaving the simulation's scope implied.

(e) *Two defects this phase produced itself, recorded because the phase's whole subject is a number
that does not belong to its producer.* First, the dated correction written into
`docs/release_notes_v1.7.0.md` cited sha256 `b0a13681…` for
`docs/release_bodies/v1.7.0-second-correction-block-2026-10-07.md`; the file's own digest is
`229c21a64c6ae190d21665e420e0a449dcfdb62f08eaa8f9bbe023a61ba60c3c`, and the cited value was the hash of
the text before that file was saved with its trailing newline. It was caught only because the file was
hashed a second time on the way to the commit, which is the same position a reader restoring the release
page would be in -- and a snapshot whose digest does not match is a silent failure rather than a loud
one. `test_every_digest_a_release_note_cites_is_its_files_own` now pairs every snapshot under
`docs/release_bodies/` with the digest the note cites for it, and the declared plant
`release-note-cites-a-digest-its-file-does-not-carry` (42 -> 43 plants) is the same edit, run live
first: the guard named both digests side by side, and the file came back to its recorded SHA-256.
Second, that same note's "What is still not here" section says `sympy` "is still not a project
dependency", which Phase 24 made false -- a present-tense bullet in a dated record, decayed in place,
and no guard reads it because dated records are deliberately outside the count guards. Registered as
`docs/limitations.md` #87 with the mitigation actually used (a dated correction line beside the stale
bullet, discoverable but unenforced) rather than resolved.

**Two properties keep the lists from becoming decoration.** An owned pattern must occur verbatim in the
source of the guard named as its owner, so a claim cannot be exempted by a comparison nobody wrote; and
every declared anchor is re-run with itself withheld, and an anchor that exempts nothing the other rules do
not already cover is reported as dead weight. That second check paid for itself during the phase, and
taught the radius lesson with it: three hand-written anchors (`12 of 12 cases`, `492 rows`,
`4 scenarios`) were genuinely redundant once the sentences cited their artifacts and were deleted, while
two incident quotations were flagged redundant *spuriously* -- under a paragraph-wide rule, two anchors
in one paragraph each looked removable because the other still covered the paragraph, and deleting both
broke the guard. Anchoring declarations to 40 characters made each quotation load-bearing again, and the
first version of the exemption rule's paragraph reading -- which had let a claim three sentences away
borrow an exemption -- was replaced by a 40-character radius around the anchor, with the paragraph rule
reserved for artifact citations, because an artifact backs an argument while a declaration is about one
sentence.

**Falsification.** Declared plant `report-adds-an-unowned-numeric-claim` inserts `41 modules` into the
abstract -- a paragraph with no citation and no declaration -- and names the inventory guard as its guard
(41 → 42 plants). The same edit was run live before it was declared: the guard reported
`line 59: '41 modules'`, the file was restored to its recorded SHA-256 (`44c2c1d5…`), and the guard went
green again. Four plant anchors were re-keyed by this phase's own count syncs (85 → 86 limitations, `# 415`
→ `# 416`, `484 pytest tests` → `485`, `# 41/41` → `# 42/42`), and the harness self-test named each one
before it could be counted as coverage.

## Addendum — Phase 28, a producer run that edited five documents, and the figure the ownership sweep had no rule for (2026-10-08)

**60. Re-measuring a volatile artifact is a documentation edit in disguise, and of all the figures that
edit moves, the one no guard owned was the date that names the run.** Phase 28's own work is a radius
experiment (`docs/phase_reports/phase-28-sixth-book.md`), but registering it as the 19th suite member
means the suite now re-writes
`benchmarks/performance/results/monte_carlo_speed.json` on every run, and that single producer pass
made five documents' present-tense sentences false at once: `README.md`, `docs/validation_matrix.md`,
three separate blocks of `docs/interview_defense.md`, `docs/reproducibility.md`, and the report's
timing table plus the sentence under it. Every one was caught, which is the mechanism working; what
the phase is about is the four things the mechanism did *not* cover.

(a) **The caption's run date had no owner.** `paper/technical_report.tex` tabulates the speed run and
its caption says "the run in `\src{...monte_carlo_speed.json}` dated 2026-09-29T08:58:31+00:00". That
timestamp is provenance: it is how a reader tells which of twenty-one measurements the table is. It is
also not a `<number> <noun>` claim, so Phase 27's inventory never looked at it, and
`test_documents_quote_the_performance_figures_the_artifact_actually_holds` compared the ratios and the
means and the z-scores while leaving the date behind — a table that re-freezes silently keeps
asserting it came from a run that is no longer on disk. The guard now carries `generated_at` as a
figure, the caption is required to state the artifact's own timestamp, and
`test_the_performance_guards_are_not_vacuous` plants `2000-01-01T00:00:00+00:00` — a date no run of
this repository has ever produced — and asserts the caption does not contain it. Declared as
`report-cites-a-run-date-the-artifact-does-not-carry` (45 → 46 plants) and run live first: the date in
the committed caption was replaced by the date the *previous* freeze carried, the guard named the
timestamp the artifact actually holds, and the file returned to its recorded SHA-256
(`7bb5733e29094ed6a6a48739b175a053751a1f17f0b55c9d5676acc0c99c9e1c`) before the guard went green
again. The generalised rule: ownership has to cover the fields that *identify* a measurement, not only
the ones it argues from. A second member of the same class turned up in this phase's own new guard:
its scan publishes the candidates the rule priced, and the rule stops at its first acceptance, so the
scan was one row and the "ascending ratio order" assertion had nothing to order. The artifact now also
publishes the 23-row ranking the rule sorted on -- which it always computed, since sorting requires
it -- and the guard re-derives that ranking from the module's own `ratio_of` and refuses a published
order that is not the one the rule produces. Two declared plants:
`report-cites-a-run-date-the-artifact-does-not-carry` and
`sixth-book-ranking-is-not-the-order-the-rule-sorts-in` (45 → 47 plants).

(b) **A band derived from git history cannot be green in the tree that creates its new edge, and two
clean runs of one script can move it twice.**
`test_the_documented_speedup_ranges_match_the_committed_history` requires the pinned `SPEEDUP_BANDS`
to equal the min/max over the artifact's *committed* revisions. A clean re-run measured `0.5656×`,
which made the pinned `0.51` upper edge wrong in both directions at once — too low for the documents,
still right for the history — so the band was widened to `0.57×` and six documents were re-synced to
`8.38×` / `0.566×`. The next clean re-run of the same script, four minutes later and also idle,
measured `8.877×` / `0.4597×`: the `0.57×` edge was wrong again, this time too high, and the
pure-Python edge moved to `8.88×` instead. Both readings are honest and only one of them can be
quoted, because the tree carries a single artifact rather than a sample; the one that is committed is
the one the documents state, and the other is recorded in `docs/reproducibility.md`, in
`docs/limitations.md` #77 and in this note. Two guards were therefore red in the exact tree being
committed — that one, and the manifest guard that refuses to hash a results directory the freeze has
not seen. The temptation was to make the history test also read the working tree. It was not taken,
because the claim being policed is "what this repository has published", and the working tree is not
published. Instead the sequence is recorded as it happened: docs and artifact committed together, band
verified green *on the committed tree*, manifest rebuilt from that commit and verified again. The
guard is unsatisfiable before its own commit by construction, and a phase that does not say so leaves
the next reader to conclude the gate is broken.

(c) **A contended re-run wrote a pair no band can hold, and restoring it was the right call — but the
bands had never said what they mean.** The first suite pass of this phase contended with a second copy
of itself and wrote `speedup_vs_pure_python = 4.007` and `speedup_vs_numpy = 0.3588`, below every edge
this repository has ever printed, and its whole run took 761.5 s against 367.9 s and 288.2 s for the
two clean passes that followed it. That artifact was restored from a pre-run copy rather than
committed, which was right, and left the bands silent about the thing a reader would most want to
know: `7.77×–8.88×` is the range of *committed* measurements from one machine, not a confidence
interval on the engine, and a reading outside it is evidence about the machine. Now stated in
`docs/limitations.md` #77 and `docs/reproducibility.md` with the numbers and the reason the file was
restored. The bands' own edges moved twice inside the phase as well, and the NumPy baseline ranges
from 110M to 46M paths/s across the twenty-one committed readings — the guard doing exactly the job it
was written for: a producer run obliged a documentation edit, twice.

(d) **A derived verdict whose denominator contains the observation it judges can never be wrong.** The
new member's first headline carried `published_ratio_span` over *all six* books and
`sixth_book_is_new_low_of_the_span` alongside it; because the sixth book's ratio was inside the span by
construction, the flag was false whatever the experiment found, and the note under it would have read
"the rule picked a book the published ratio range already covers" for any measurement at all. Split
into `published_ratio_span_of_the_five_prior_books`, `ratio_span_over_six_books`, and
`sixth_book_ratio_over_the_published_minimum` (0.0431, i.e. the new book's ratio is 4.3% of the
previous minimum), the flag now reads `true` and names the rule that decided it. The test is
`test_sixth_book_crossing_map.py::test_the_sixth_book_is_a_new_low_of_the_span_it_was_compared_against`,
and the question that finds this class before the code does is: *what run of this machinery would make
the flag false?* If none, it is decoration. Same discipline caught the note's rounding: the table
prints three decimals, so the guard compares `round(value, 3)`, and a raw-equality version failed on
`1.333` versus `1.3333333333333335` — the document was right and the check was wrong.

(f) **The sweep escaped a plant, and the escape was a sixth member of the same class.**
`readme-quotes-a-stale-speedup` re-keyed to the current point figure should have made
`test_documents_quote_the_performance_figures_the_artifact_actually_holds` red by writing `8.70×` where
the artifact measures `8.88×`. It reported `46/47 planted defects were rejected by their guard`: the
substitution landed, the bytes changed, and the guard stayed green. The reason is that this phase's own
measurement became the widest reading in the file's history, so the README prints `8.88×` twice — once as
the point figure the guard certifies and once as the band's upper edge, which the tamper does not touch.
A substring claim over a document that prints the same digits for two different reasons is satisfied by
the occurrence nobody meant. Fixed by making the claim a phrase rather than a digit
(`` `8.88×` in the artifact now in the tree ``), and the same context was added to the
`interview_defense.md` claim; the guard now fails on the tamper it just survived. This is the
`net`/`network` lesson from finding 59 applied to digits: windowing the cue is only useful if the cue is
the *sentence*, and the discovery mechanism was the sweep, not the reading — a green gate that cannot
fail is invisible from inside it.

(e) **Two dated records had to be corrected rather than edited.** `docs/release_notes_v1.5.0.md` and
`docs/release_notes_v1.7.0.md` are both in `RANGE_DOCUMENTS`, so the band guard reads them, and both
state `0.42×–0.51×` — true on their own dates, false now. Neither paragraph was rewritten; each note
gained a dated correction section (`Correction added 2026-10-08`, and a *third* correction for 1.7.0)
that states the moved band and says plainly why the sentence above it is left alone. This is finding
59's #87 recurring in a new place: the guard's membership list does not distinguish a claim about the
present from a record of the past, so either the dated record carries the current band or the guard
must stop reading it — and dropping it from `RANGE_DOCUMENTS` would hide exactly the class of staleness
the list exists to find.

## Addendum — Phase 29, a number the gate had already checked, in a sentence it never read (2026-10-09)

**61. A presence-only guard cannot see a superseded restatement, and the proof was in the file the
guard was green over.** `docs/reproducibility.md` line 72 annotated the reproduction command with
`# 481 tests here`, while line 110 of the same file said **494 pytest tests with the `oracles`
extra** and line 112 said the offline lane collects 425. Every gate passed. Each count guard compares
a *named spelling* with its producer, `481` matched none of the named spellings, and "the document
contains the right number somewhere" is a claim about presence, not about the absence of a wrong one.
The 481 entered with Phase 23's count sync and survived Phase 26 and Phase 28 -- two phases that
re-synced that very pair -- because the annotation was inside a fenced block no reader looked at. It was
found only by running the report's claim inventory over the two documents it had never read
(`README.md`, `docs/reproducibility.md`), which is Phase 28's §8 item 2 discharged.

Four things the extension settled rather than worked around.

(a) **A markdown citation has to be read through the registry, not through a path.** The findings table
in README keys its rows by member (`fifth_order_crossing_map`) and never prints the artifact path, so
`_cites_frozen_artifact_markdown` resolves the key through `scripts/run_benchmark_suite.py`'s own
members and requires the resolved artifact to be frozen. A pasted path would have made the rule vacuous
in the one place it matters: a row whose key no longer resolves now cites nothing, which is the
declared defect `readme-cites-a-suite-key-the-registry-dropped`. Relatedly, citing
`docs/limitations.md` does *not* excuse a count -- the freeze hashes evidence, not prose -- so the
register's size has to be owned by the guard that counts the file, as it is.

(b) **The extractor needed sentence sense before it needed more nouns.** Applied unchanged to markdown,
the report's rule produced two fake claims per file: `#77. Load moves the timings` (a cross-reference
followed by a sentence beginning with a policed noun) and `on 5 of 5. Two books sit at the grid edge`
(a list/sentence period read as part of the number). Both exclusions were added -- no `#` before the
number, no bare trailing period -- and verified to be inert on the report: 46 claims before, 46 after,
byte-identical classification. The direction matters: an inventory that invents claims trains the reader
to wave it through, and the point of the exercise was that a human had already waved through the real
one in that file.

(c) **One number in those documents had no producer in any environment.** `7 identity checks` appears in
both command annotations and, spelled, in the report; nothing compared any of them with what
`quantrisk validate` runs. The new owner executes the installed entry point in JSON mode -- resolved
beside the running interpreter, so it measures the build under test -- and requires each document to
state that count; a plant (`readme-quotes-an-identity-count-the-cli-does-not-run`) proves it fires. This
is finding 55 and 57's shape a third time, and it reached the two most-read files in the repository.

(d) **The count syncs disarmed four plants, as they now reliably do.** Re-keying `425 → 427`,
`494 → 496` and `88 → 89` broke the anchors of
`interview-doc-overcounts-the-offline-lane`, `report-counts-stale-python-tests`,
`report-quotes-a-count-the-offline-probe-refutes` and
`readme-undercounts-the-limitation-register`; the harness's anchor self-test named each one before it
could be counted as coverage, and each was re-keyed with its replacement still wrong. Finding 49,
fifth occurrence, inside the same phase that extended the mechanism.

(e) **The phase's own tooling damaged the guard file, and the lane is what caught it.** A comment
re-wrapping script applied to `tests/python/test_artifact_metadata.py` dropped a trailing newline and
then split inside words at 18 places (`...against this run's t.` / `otal: each belongs to`), producing
unparseable Python. Nothing was committed with it: the recovery was a snapshot, a restore of that one
file from `HEAD`, and a re-application of the phase's edits against unique anchors -- then a full-lane
run before the commit. The durable rule is the one already written down (a bulk text rewrite must
measure its numeric and structural delta against `HEAD`, and a green lane is not a substitute for
reading the diff), and the reason it held here is that the damaged file never reached a commit.

Register grew to 89 with #89, which records the scope that remains: `docs/interview_defense.md` and
`docs/validation_matrix.md` are still policed per figure rather than inventoried. Four declared plants
(47 → 51), 496 tests passing locally, and the freeze was not rebuilt because no producer re-ran --
`test_the_manifest_hashes_every_experiment_results_directory` and the evidence-integrity guards are
what make that statement checkable rather than optimistic.

## Addendum — Phase 30, the release's own numbers, and the one its note published from the wrong vantage (2026-10-09)

**62. The version string was the last figure in the tree with no producer, and a verification line in
this release's own published note was measured in the wrong environment.**

(a) **`1.8.0` was spelled seven times and compared once.** `pyproject.toml`, `CMakeLists.txt`,
`CITATION.cff` (its `version`, the nested `references[0].version`, and the release-notes URL), `uv.lock`,
`README.md`, `docs/interview_defense.md` and the compiled `quantrisk.version()` all state the version;
`tests/python/test_smoke.py::test_python_package_version_matches_pyproject` paired only the last with the
first. Nothing could have disagreed with a bump that forgot `CITATION.cff` -- and that file is uploaded as
a release asset, so the wrong version would be downloadable and citable while every gate stayed green.
`test_the_version_string_the_project_declares_is_one_number_not_four` reads all seven now, with a pattern
that must match at each site (a renamed field fails rather than vacates), and compares the citation's tag
URL with `v` + the version. It was falsified in the same breath it was written: plant
`\nversion: 1.8.0` → `\nversion: 1.9.9` gives `CITATION.cff states ['1.9.9', '1.8.0'] while the package is
1.8.0`, and restoring the file to sha `061f61aa7958…` returns it to green. The plant
`citation-declares-a-version-the-package-does-not` carries the newline in its anchor because the string
also occurs indented, inside `references`, and a bare anchor would occur twice -- finding 49's shape
anticipated rather than repeated.

(b) **A guard written to protect release snapshots protected one release.** The digest pairing test read
`RELEASE_NOTE = docs/release_notes_v1.7.0.md`, a constant, so the note the repository was writing *now* was
outside its own coverage: `v1.8.0`'s body, and every body after it, would have been uncitable without
consequence. Repointing the constant would have deferred the same defect by one release, so the guard now
iterates `docs/release_notes_v*.md` and keeps both properties it had: a snapshot cited by no note fails,
and a snapshot cited by several must satisfy each citation.

(c) **This phase's count syncs disarmed seven plant anchors -- finding 49's class, sixth occurrence, now
in the phase that has the rule written down most explicitly.** 497 → 498, 428 → 429, 89 → 90, 52 → 53
plants and `7{,}238{,}399` → `7{,}211{,}281` bytes broke
`report-counts-stale-python-tests`, `report-quotes-a-count-the-offline-probe-refutes`,
`report-counts-a-manifest-the-freeze-does-not-have`, `interview-doc-overcounts-the-offline-lane`,
`reproducibility-quotes-a-superseded-pytest-total`,
`docs-command-comment-counts-superseded-plants` and `readme-undercounts-the-limitation-register`. Two of
them (`…stale-python-tests`, `…offline-probe-refutes`) were already disarmed when this segment began -- by
the same phase's earlier regeneration, before any commit: `49dc015` carries `and 496 pytest tests…` and
`oracles installed, 427 collected…` in both the report and the plant list, in agreement, and the counts moved
to 497/428 then 498/429 with the tests this release added. The reason nobody saw it is that
`pytest tests/python/test_mutation_suite.py` reports **one** stale anchor per run, so a phase that fixes the
one it sees and re-runs can still be holding disarmed plants at the end. The durable form of the check is the
one-pass enumeration of every declared anchor against the file it names, recorded in
`docs/phase_reports/phase-30-v1.8.0.md` §4(c) -- including the `sys.modules` registration it needs, without
which loading the harness by path dies inside `dataclasses._is_type` instead of reporting anything useful.

(d) **A verification figure in the published release body was taken from the working tree, and the runner
disagrees with it.** `docs/release_notes_v1.8.0.md` states `ruff format --check .` → "164 files already
formatted". That is what the command printed on this laptop at gate time, and it is not what the same
command prints for the same commit anywhere else: on a `git archive v1.8.0` export it prints **165**, and
CI's `Format and static checks` job on `f181427` printed **165** (`2026-10-09T05:44:43Z`). The tracked tree
holds 82 `.py` files, so neither reading is a file census the reader can reproduce -- the count is this
Ruff version's walk of one environment, and the honest label for the release's own record is the runner's,
not the laptop's. The number is cosmetic; the mechanism is not. Every other line in that block is a tool's
output for the commit that carries it, and this one is a tool's output for a different machine. Corrected
by a dated block appended to the release body, tag and assets untouched, per the rule that an asset
published from a tag is not edited.

(e) **The sweep leaves an empty `experiments/_mutation_probe/` tree behind.** Both `tree`-kind plants
create files that did not exist before and `unlink()` them afterwards, but not the directories, so the
sweep that reported `53/53` with `git status` empty was empty *because git does not track empty
directories*. A later "how many files are in the tree" claim would silently include them. Recorded rather
than fixed here: the cleanup is two `rmdir`s in the harness, and the guard that would catch its absence is
the same file-census guard §8 of the phase report names.

(f) **`date-released` remains unowned by decision.** The guard could have compared it with the tag's commit
date, which exists only after the release -- the same window the report's nine-tag enumeration already
documents, and a second guard with that window would double the pre-tag reds without adding a reader who
could act on them. Registered as debt with the producer named, not quietly proxied.
