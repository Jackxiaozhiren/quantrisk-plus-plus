# Phase 24 — a command that was available, made a command that runs

Date: 2026-10-06. Predecessor: Phase 23 (`phase-23-report-prose.md`), whose §8 item 1 is this debt item;
Phase 22 §8 item 2 is the same item one release older. No `PROJECT_SPEC.md` phase number: this closes a
registered technical-debt entry. Repository version is unchanged (`1.7.0`), the tag still names
`79d536a`, and nothing here is claimed to be inside that release.

## 1. Completed

1. **`sympy` is a dev-group dependency.** `[dependency-groups] dev` gained `sympy>=1.12`; `uv lock`
   resolved 58 packages and added `sympy 1.14.0` and `mpmath 1.3.0`. This is the group `uv sync` installs,
   which is what all three CI jobs run, so the dependency arrives in CI without the `oracles` extra being
   touched — the offline lane stays offline in the sense that matters (no QuantLib, no pypfopt, no cvxpy,
   no sklearn).
2. **The derivation is executed by the gate.**
   `tests/python/test_fifth_order_partials.py::test_the_derivation_command_agrees_at_the_precision_floor`
   runs `scripts/derive_fifth_order_partials.py` in a subprocess and asserts the two floors the documents
   rest on. Measured on this tree: part A's six fields top out at `8.659e-59, 1.091e-58, 8.614e-59,
   8.659e-58, 9.809e-59, 4.653e-59` against the script's own `1e-40` ceiling, and part B's grid summary is
   `4.619e-15` against `1e-12`. Wall clock 3.3 s, which is why it belongs in the pytest lane rather than in
   a nightly job.
3. **The quoted figure now has an owner across three artefacts.** The same test reads
   `docs/validation_matrix.md` row 21 and §Stress Testing of `paper/technical_report.tex`, requires the
   `(mantissa, exponent, market count)` triples to be identical — `('8.7', '58', '60')` on both sides — and
   requires the run's worst residual to share that order of magnitude. Before this phase the two documents
   were free to drift from each other and from the file they describe.
4. **A plant only this gate can catch.** `derivation-prefactor-exponent-off-by-one` rewrites the prefactor
   quotient's `v_value**4` as `v_value**3` — the shape claim, not a coefficient — and the declared list
   moves 38 → 39. The finite-difference routes cannot see it: they are banded at `1e-3` relative in Python
   and `1e-8` in C++, while the identity check runs at 60 working digits.
5. **The build product was refreshed, and the reason it had lagged is written down.** The tex edits in this
   phase rebuild `paper/technical_report.pdf` in the same commit. `docs/reproducibility.md` already named
   the hole and one instance of it; this phase produced a second (the committed PDF still carried 408 after
   the tex moved to 412), which is finding 56(d) rather than a footnote.
6. **The records this moves.** `docs/limitations.md` #82 amended in place with who runs the command now;
   matrix row 21's "re-runnable" replaced by "executed by the gate since Phase 24";
   `docs/reproducibility.md`'s count pair; `docs/interview_defense.md`'s state line, plant annotation and
   test-count table; `docs/project_scope.md` §9; `docs/integrity_audit.md` finding 56. The counts every
   living document repeats move 481 → 482 Python tests and 38 → 39 plants.

## 2. Mathematical assumptions

The identity under test is the one Phase 20 published: each fifth partial is
`V = P · S^(1−n_spot) · T^(n_sigma/2) · R(d1, v) / v⁴` with `P = e^{−qT} φ(d1)` and `v = σ√T`, so
`R(d1, v) = (∂^5 V / ∂S^n_spot ∂σ^n_sigma) · v⁴ / P`. Part A forms that quotient from the price function at
60 digits and compares it with the polynomial parsed out of the C++ source; part B recomputes the fields by
nested numerical differentiation of the price and compares with the compiled extension's float64. Both
assumptions are the shipped ones — no new maths entered this phase, which is why the assertion that the
prefactor exponent is right is the interesting one (§4).

## 3. Files changed

| File | Change |
| --- | --- |
| `pyproject.toml` | `sympy>=1.12` in `[dependency-groups] dev`, with why |
| `uv.lock` | re-resolved: `sympy 1.14.0`, `mpmath 1.3.0` added, 58 packages |
| `tests/python/test_fifth_order_partials.py` | one test plus `_quoted_identity_floor` and `_exponent` helpers |
| `scripts/run_mutation_suite.py` | one plant declared (38 → 39), one anchor re-keyed |
| `docs/limitations.md` | #82 amended in place; the with-oracles count |
| `docs/validation_matrix.md` | row 21's owner wording |
| `docs/reproducibility.md` | the count pair and what `uv sync` now installs |
| `docs/interview_defense.md` | state line, plant annotation, three test-count spots |
| `docs/project_scope.md` | §9 Phase 24 row |
| `docs/integrity_audit.md` | Phase 24 addendum, finding 56 |
| `paper/technical_report.tex` | Python test count |
| `paper/technical_report.pdf` | rebuilt from the rebuilt tex |

## 4. The two ways this could have been decoration

1. **Adding the dependency would have been the whole task, and worth nothing.** The debt line read "put
   `sympy` in the dev extra so the derivation runs in CI". Installing it changes no behaviour: nothing in
   `tests/` or `scripts/run_benchmark_suite.py` invoked the script, so with the dependency present and no
   caller the identity still ran only when a human typed the command. The dependency is the enabler; the
   subprocess test is the change. Checked by `git grep derive_fifth` before writing anything: the only
   executors were the phase reports' quoted command lines.
2. **The assertion that would have been a false-positive machine.** Asserting `8.7e-58` digit for digit is
   the tempting version, and it is a cross-platform claim about the last digits of a 60-digit mpmath
   residual. Finding 54(a) is the same mistake made about float64: a bit difference in a library the tests
   do not control, asserted as equality, red only on the runner. The test therefore compares *orders of
   magnitude* between the documents and the run, and asserts the absolute floors (`1e-40`, `1e-12`) where
   the gap to failure is many orders. The plant confirms the tolerance is not the reason it passes: the
   mutated prefactor puts the residuals near `1e-1`, not near `1e-40`.
3. **The file count in §5 is an inventory echo, and this phase explains it rather than quoting it
   blindly.** `ruff format --check .` reports 149/150/152/153 across the last four phases, which reads like
   a moving codebase and is not: the tool covers `.md` and `.toml` as well as `.py` and `.pyi`, so the
   number is the repository's document inventory (66 `.md`, 79 `.py`, 8 `.pyi`, 1 `.toml` = 154 paths, one
   of them reported as already formatted by a different route). No document asserts it, which is the right
   treatment for a number with no claim attached; it is quoted here because the phase ran the gate.
4. **A count sync disarmed one anchor again.** Moving 481 → 482 in the tex left
   `report-counts-stale-python-tests` anchoring a string that no longer existed; the list self-test caught
   it before commit, which is finding 52's mechanism working as intended rather than a new incident.

## 5. Exact test results

```
uv run pytest tests/python -q                                482 passed in 124.26s (0:02:04)
uv run python scripts/derive_fifth_order_partials.py          exit 0, part A max 8.659e-58, part B 4.619e-15, 3.3 s
uv run ruff check .                                           All checks passed!
uv run ruff format --check .                                  153 files already formatted
uv run mypy python/quantrisk                                  Success: no issues found in 23 source files
uv run ctest --preset dev                                     (unchanged: no C++ file moved this phase)
uv run python scripts/verify_evidence_manifest.py             Evidence is intact.
uv run quantrisk validate                                     7/7 checks passed
latexmk -pdf -g -interaction=nonstopmode technical_report.tex  Output written on technical_report.pdf (44 pages, 1003992 bytes)
```

Falsification of the new test, run before the commit and restored by hash:

```
mutation  v_value**4 -> v_value**3 in the prefactor quotient
result    part A: FAILED: ['q50','q41','q32','q23','q14','q05'], script exit 1, test red
restore   sha256 9b2431c47a9a46e067ce1b569e0467b879fea229c734d10e424acea0f3e65375 identical before and after
```

Two items are open at the time of writing and are recorded rather than smoothed over: the offline lane's
collected count (the documents still say 412 while one test was added, and only the lane without oracles
measures it — §8 item 1), and this commit's own CI verdict (§9).

## 6. Numerical validation

Nothing measured by the engine changed: no C++ file, no artifact, no benchmark output moved, and the frozen
manifest verifies intact with zero regenerated files. What was validated is the *identity* the fifth-order
structs rest on, now executed by the gate at 60 working digits, plus the claim that the two documents
quoting its residual describe the same number the run prints. Part B's `4.619e-15` is the float64 noise
floor of the format and is asserted as a band, not as a value.

## 7. Remaining limitations

`docs/limitations.md` #82 carries the amendment. The standing caveats are unchanged and still true: no
oracle publishes a fifth partial, five of the six fields are anchored by stencils of this project's own
fourth-order family, the contraction route is round-off limited at the finest rung, and the derivation's
part B reaches the numerators through the price at only four markets. What this phase adds to the register
is the boundary of its own instrument: the identity is now executed in every lane that installs the dev
group, but the *PDF* that quotes it is still a hand-built byte stream with no checker, and the release-page
body is a third copy of the release text that nothing compares.

## 8. Technical debt

1. **The offline test count still has no local owner** (Phase 23 §8 item 2, unchanged): this phase added one
   test and the offline figure in four documents is now stale by one, knowable only from the runner. The
   cheap version is unchanged in shape — block the oracle modules in a subprocess, collect, and require the
   published pair to differ by exactly the oracle-gated items — and it is the next phase's first item.
2. **PDF freshness has no owner either**, and `docs/reproducibility.md` now records two instances of it
   (Phase 11 and this phase). Checking it needs a text extractor as a dependency, which the repository has
   declined; the alternative is a committed build recipe the CI runs, which costs a TeX install on every
   push and is a worse trade at $0.
3. **The release body and `docs/release_notes_v1.7.0.md` are two documents with one subject** and no
   comparison between them (finding 56(e)).
4. **`sympy` in the dev group makes the identity cheap but the lane slower by ~4 s**; if a future phase adds
   a second 60-digit check, the pair should run in one process rather than paying the interpreter twice.

## 9. Gate

The gates above are §5's, taken from the tree before the commit that carries this report; the C++ suite was
not re-run because no C++ file moved, which is stated rather than left for a reader to infer from its
absence. The falsification sweep runs on the committed tree after it exists — the harness refuses a dirty
tree — and its verdict line, this commit's CI run and the offline lane's collected count are appended in
the commit that follows, which is the only place they can honestly live.

**Verdicts, read after the commits they describe.** `3acdfe8`'s CI run 37409108820 reports
`Format and static checks: success`, `Benchmark suite against live oracles: success` and
`Configure, build, C++ tests, Python tests: failure`, the last one failing exactly where §5 said it
would: `AssertionError: docs/interview_defense.md says 412 for this environment; pytest collects 413`,
with the lane's own line `1 failed, 411 passed, 5 skipped`. The offline count was then synced from the
runner's message, the technical report's PDF rebuilt, and the sweep re-run: `39/39 planted defects were
rejected by their guard.` on the committed tree with `git status` empty before and after.

One by-product worth recording, because it changes the next phase's shape. Before the runner answered,
a throwaway subprocess that makes `QuantLib`, `pypfopt`, `cvxpy`, `sklearn` and `statsmodels` unimportable
collected **413** items on this tree -- the number the runner then reported. So the collected count is
reproducible locally; what the probe did *not* reproduce is the shape, since the four gated modules
surfaced as collection errors there and as skip records in CI. Phase 26's job is therefore narrower than
"build a simulator": the simulator has to fail the way the runner fails, and the fidelity test is both
the count and the skip shape.
