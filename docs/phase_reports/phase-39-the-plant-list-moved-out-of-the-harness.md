# Phase 39 — the plant list moved out of the harness, and the guard behind it got a declared defect

Closed `docs/limitations.md` #94. The entry had said the fix was unbuilt "because it changes the file
every future phase edits"; this phase changed it, and the reason it was worth changing is that the
alternative on record for one guard was a human editing the harness, running a test node, reading the
failure, and putting the file back -- a demonstration that nothing re-runs.

## 1. Completed

* **`Mutation` and `MUTATIONS` now live in `scripts/mutation_plants.py`.** 77 entries, one type, and a
  module docstring that says why the split exists. The harness loads it by file path -- `PLANTS_PATH`,
  `importlib.util.spec_from_file_location` -- because `scripts/` is not a package, which is the same way
  `tests/python/test_mutation_suite.py` loads the harness. Nothing else imports it.
* **`scripts/run_mutation_suite.py` is 441 lines instead of 1076 of code plus list**, and its behaviour
  is unchanged: `--list`, `--kind` and `--only` all resolve through the loaded tuple (smoke-tested:
  `--list` prints the new plant, and `--only` refused to sweep a dirty target, which is the guard doing
  its job rather than the refactor breaking it).
* **The plant the split unlocked:**
  `harness-spawns-a-guard-subprocess-without-a-bytecode-prefix` -- `kind="prose"`, path
  `scripts/run_mutation_suite.py`, anchor the single call site in `Harness.uv`, replacement the same call
  with the isolation argument dropped, guard
  `test_every_subprocess_the_harness_runs_a_guard_in_is_bytecode_isolated`. That is the defect Phase 34
  demonstrated by hand, now declared, re-planted on every sweep, and counted in the annotation.
* **The split itself is policed, not assumed.** New guard
  `test_the_plant_list_lives_where_a_plant_can_reach_the_harness` asserts four things: the data module
  defines the list, no `MUTATIONS = (` has crept back into the interpreter, the harness's loaded entries
  are instances of the harness's loaded `Mutation` (so it is one list, not a pasted copy), and exactly one
  plant points at the interpreter with an anchor that occurs there once.
* **One documentation defect found by the cascade**: the rehearsal sheet's Q24 said "Nineteen are
  declared" -- present tense, of a list that is 77 strong now -- two lines above a quotation of
  `19/19` from the revision it actually describes. It now names its revision and points at the sweep
  annotation as the living figure, which the count guard compares with the declared list. The count was
  spelled, which is #95's remaining group: the sheet carries 14 spelled claims and is the next document in
  that rollout.
* **Register #94 amended** with the closure, the residual, and one measured cost. The register's own text
  also carried a duplicated phrase in that entry ("showed the first one red the first one red the only way
  left"), which was corrected while reading it.
* **The count cascade this phase caused**, in the order the guards named it: plants 76 → 77 (the sheet's
  annotation, and the plant anchoring on it); one new test moved the Python pair 515 / 446 → 516 / 447
  across twelve spellings in four documents and the tex; four plant anchors re-keyed to the new figures;
  the report re-typeset.

## 2. Assumptions this rests on

* An anchor-based falsifier cannot target the file holding its own anchor data. Moving the data moved the
  boundary rather than removing it, and #94(a) says so: a defect in the *list data* (blank claim,
  duplicate identifier, a guard node that does not exist) is still unplantable -- and is instead a
  structural property read off the loaded objects.
* The CLI and the sweep verdict are about a revision, so the full sweep is re-run on the committed tree
  after the split, not inherited from before it. The 77 count in the annotation is the declared denominator;
  the verdict it claims is the sweep log's.
* Loading by path keeps `scripts/` a directory of tools rather than making the library import a tool. A
  `sys.path` insertion at import time would have been shorter and would have tripped the lint rule about
  imports after code.

## 3. Files changed

| File | What moved |
|---|---|
| `scripts/mutation_plants.py` | new: the `Mutation` type, 77 plant entries, and the reason in its docstring |
| `scripts/run_mutation_suite.py` | list and type removed; `PLANTS_PATH`, `_load_plants()`, `importlib.util` added; statuses, restore logic, `Harness`, and the CLI untouched |
| `tests/python/test_mutation_suite.py` | the boundary guard, and one docstring re-wrapped by `scripts/rewrap_docstrings.py` |
| `docs/interview_defense.md` | the sweep annotation 76/76 → 77/77, the two Python counts, the provenance row, Q24's tense, the state line to Phases 0–39 |
| `docs/reproducibility.md`, `docs/limitations.md`, `paper/technical_report.tex` (+ `.pdf`, `.build.json`) | the two Python counts; #94 amended and its duplicated phrase corrected; the report re-typeset |
| `docs/integrity_audit.md` | finding 79 with (a) the fix, (b) the boundary that moved, (c) the wrong-tense count |
| `docs/project_scope.md` | the §9 row |

## 4. What the phase learned, including about its own first design

1. **A demonstration is not an instrument, and the cost is silent.** #94 said the hand proof "is not
   re-run by CI, is not repeated when the guard next changes, and can be forgotten". Measured against the
   history: the per-invocation prefix dates from `a4d8742` (Phase 33) and the guard from `8760b5a`
   (Phase 34), and neither has been touched since -- which is exactly why the missing instrument looked
   harmless. Nothing in the repository could tell a reader whether the isolation argument was still there;
   the reason it was still there was that nobody had deleted it, and that is not a check. The plant makes
   the plumbing's invariant a claim the sweep tests.
2. **The interesting constraint turned out to be self-reference, not file ownership.** The first reading
   of #94 was procedural ("a plant cannot edit the file that lists plants"), and the second is the real
   one: any tool that locates a defect by a unique string cannot target the file containing its own
   strings. That is why the residual is stated in #94(a) instead of being fixed by another move -- moving
   the list again would just relocate the same wall.
3. **Refusing to run on a dirty tree is worth more than a convenient override.** `--only` on a plant whose
   target was mid-edit returned `target-already-modified: these mutation targets differ from HEAD ->
   scripts/run_mutation_suite.py` and stopped. The temptation in a refactor phase is to let it sweep
   anyway; the reason it must not is that its verdict is a claim about a committed revision.
4. **The count cascade is how the repository finds stale prose, and it found some.** Four anchors and
   twelve spellings moved for one added test and one added plant -- expected. Unexpected and useful:
   rewriting the sheet's Q24 to check whether its plant count was living prose surfaced the wrong tense.
   A spelled count of a historical list, stated in the present, is the same defect class #95 describes,
   and it is the third instance found by *cascading* rather than by reading.
5. **The promoted tool did its first ordinary job.** `scripts/rewrap_docstrings.py` reflowed the new
   guard's docstring and printed `docstrings reflowed: 1 / lines still longer than 100: [(70, 102)] /
   proof: whitespace-only`; the residual line was a nested f-string, not prose, and was fixed by hoisting
   the count into a local -- which also stopped the guard computing the same count twice inside its own
   assertion message.
6. **What this phase deliberately did not touch:** #93's boundary outside this harness (CPython's cache
   key, not this repository's to fix), and the evidence freeze -- no experiment or benchmark input
   changed, so `run_benchmark_suite.py` was not run at all, and `verify_evidence_manifest.py` reports the
   tree's bytes identical to the manifest.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 180 files already formatted (one new module in the walk) |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `.venv/bin/cmake --build --preset dev` then `ctest --preset dev` | 100% tests passed out of 204 |
| Identity | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | "Evidence is intact" -- 0 changed, 0 volatile, 0 missing, 0 unlisted |
| Python suite | `env -u PYTHONPYCACHEPREFIX .venv/bin/python -m pytest tests/python -q` | `516 passed in 84.61s (0:01:24)`, no skips |
| Harness lane | `.venv/bin/python -m pytest tests/python/test_mutation_suite.py -q` | 9 passed (8 before the split, plus the boundary guard) |
| CLI, smoke | `.venv/bin/python scripts/run_mutation_suite.py --list` | 77 rows, the new plant among them, exit 0 |
| CLI, refusal | the same with `--only harness-spawns-a-...` on the in-progress tree | `target-already-modified: ... -> scripts/run_mutation_suite.py`, no file touched |
| Producer | `.venv/bin/python scripts/build_report.py` | 6 sources, bundle `e4b80aa00ac7…`, PDF `3dc1dcea6c97…`, 1,005,797 bytes |
| Falsification, full sweep | logged to `build/mutation-sweep-39.log` | recorded below, measured on the committed tree |
| CI on the pushed head | `gh api …/commits/<sha>/check-runs` and the job logs | recorded below, after the push |

## 6. Numerical validation

No measurement is published. What moves and why:

* **77** -- the declared plant count, from the list rather than from prose. The sheet's annotation carries
  it, and the guard that compares the two is the reason the annotation cannot fall behind.
* **516 / 447** -- the Python pair, up one test. Their difference stays 69, recomputed by the guard from
  each document's own pair.
* **180** -- ruff's file walk, up one module: a directory count, environment-relative, quoted because the
  gate printed it and not because it is a fact about the project.
* **Zero** artifacts re-frozen and **zero** benchmarks re-run: no experiment input changed, so the
  performance bands, their 22 committed readings and every quoted ratio are untouched -- which is the
  point of not running the suite on a phase like this one.

## 7. Remaining limitations

* **#94's residual, stated in #94(a):** no plant can anchor in the file that holds the plant list, so a
  defect *in the list data* remains unplantable; it is covered by structural reads of the loaded objects
  instead.
* **#93** stays open and out of scope: CPython's cache key is the interpreter's, and the harness's
  mitigation is now falsifiable while the underlying behaviour is not this repository's to fix.
* **The rehearsal sheet still holds 14 spelled claims** (#95's remaining group, along with 22 in the
  matrix and 45 in the report), and Q24's neighbour counts are exactly the kind the next slice will sort.
* **One historical count remains unpoliced by design:** the sheet's `19/19` quotation is a record of
  `e5daedc`. Nothing compares it with the current list, and nothing should -- that is the dated-record
  rule, not a gap.

## 8. Technical debt registered here

| Entry | What it records |
|---|---|
| #94 (amended) | closed by the split; (a) the self-reference boundary moved with the list, (b) the CLI is unaffected while the anchor census now reads two files |
| -- | no new entries: the wrong-tense count found here was fixed in the same change rather than registered |

## 9. The gate

Closed when the sweep runs 77 declared plants on the committed tree with no line at any other status and
the tree clean afterwards; when CI's three jobs are read from their own logs on the pushed revision; when
the #91 reconciliation holds for the new pair; and when the register, the audit, the scope table and the
sheet all state the same plant count and the same Python pair, each from its own producer. As in every
phase before it, the commit that carries these rows cannot contain the verdict of its own run -- a record
checks the revision it names.
