# Phase 46 — the sweep stops at the plant that escapes, and the static rule that would have named it is measured and refused

Date: 2026-10-16. Debt item: `docs/limitations.md` #103, opened by this phase from finding 86(b),
mitigated procedurally and left open on the static half.

## 1. Completed

* **#103 registered** with the measurement attached, not the anecdote: a plant's `guard` field is a
  hand-typed string, `check_exists` proves only that the named test is *defined*, and no check before
  the sweep can tell a plant that points at the wrong reader from one that points at nothing.
* **`sweep-stopped-early`.** `scripts/run_mutation_suite.py` stops at the first plant whose guard does
  not reject the mutation, prints the plant's id, and counts the declared plants it never ran. `--all`
  opts back into the full census, which is what a phase record quotes.
* **Three guards, one per way the stop can lie** (`tests/python/test_mutation_suite.py`): it must fire
  on the first non-caught status and name the plant and the skipped count; `--all` must run the whole
  list and print no stop line; and a *clean* sweep must still run every plant and print the census
  unchanged -- the property that keeps `109/109` meaning the declared list rather than the run so far.
* **The registry's own accident promoted to an invariant.**
  `test_the_plant_list_lives_where_a_plant_can_reach_the_harness` asserted `len(pointed) == 1` -- one
  plant may point at the interpreter -- when what #94 actually requires is that each such plant's
  anchor occurs once there. It loops now, and four plants point at the interpreter.
* **4 plants (105 -> 109)**, each mutating a line of the interpreter and naming the assertion that
  reddens: the stop made never-fires, the stop made always-fires, the stop counting `len(results)`
  instead of `len(selected)`, and `--all` inverted to `store_false`.
* **The cascade the phase owes**: register 102 -> 103 across its nine spellings and the plant that
  moves that count; the sweep annotation 105/105 -> 109/109; the test pair 519/450 -> 522/453; the
  artifact index `forty-six report files` -> `forty-seven`; the report re-typeset.

## 2. Assumptions this rests on

* The three new guards replace `run_one` with a fake over synthetic plants, so the loop is what is
  under test and the suite never edits a tracked file. The synthetic plants name a real file and a real
  guard so `check_exists` resolves them the same way a declared plant's would.
* Fail-fast changes what a *red* sweep prints, not what a green one prints. Every `N/N` quoted in the
  documents still denotes the whole declared list, and the third guard is what pins that rather than
  the phase's say-so.
* 522 and 453 are this environment's pair: with the `oracles` extra installed, and the same tree
  collected in a child interpreter with those packages made unimportable. CI quotes its own pair.

## 3. Files changed

`scripts/run_mutation_suite.py` (stop, `--all`, `STOPPED`, the module docstring), `scripts/mutation_plants.py`
(4 plants, and the two anchors that track the register's size), `tests/python/test_mutation_suite.py`
(3 guards, the plant-counting guard generalised), `docs/limitations.md` (#103, and #63's pair),
`README.md`, `docs/reproducibility.md`, `docs/interview_defense.md`, `docs/validation_matrix.md`,
`docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md`, `docs/project_scope.md` §9,
`paper/technical_report.tex` with its rebuilt PDF and `build.json`, and this report.

## 4. What the phase learned, including about its own first design

* **The static rule was tried, measured, and refused.** The candidate -- a plant's anchor must occur
  inside the named guard's reachability closure -- misfired on 7 of the 10 plants that mutate a test
  module. Three ordinary reasons, all found in the probe's own output: the anchor is a fragment of a
  literal the formatter wrapped across lines; the reachability is real but transits a *nested* helper
  the module-level walk never enters; and a guard can read a mutated line by reading the file as text
  instead of referencing the name. A pre-flight that cries wolf on 70 per cent of its inputs is worse
  than the sweep it replaces, because it runs at every registration. So #103(b) records the measurement
  and the entry stays open, and only the procedural half ships.
* **The probe was wrong before the rule was.** My first version joined the plant's repo-relative path
  onto `tests/python/`, so every one of them raised `FileNotFoundError`; a probe that dies on its own
  plumbing reads as "the rule is unsound" if the crash is not read first. The number that mattered came
  from the second run, not the first.
* **A default that only shows up when something is wrong still needs its green path pinned.** The
  obvious two tests are "it stops" and "--all does not", and both were written; the third -- a clean
  sweep runs all three and prints no stop line -- is the one that keeps the published census honest,
  because without it the stop branch could fire on every plant and `109/109` would still be printed by
  the run that reached the end.
* **`--all` was decorative until it had a plant.** The flag's meaning is `store_true`; flipping it to
  `store_false` keeps every assertion about stopping green, because the default path never reads the
  flag. Naming that plant is what makes the flag a behaviour rather than a string in `--help`.
* **The denominator of a stop line is the declared list.** `{skipped} of {len(results)}` reads as a
  count of what ran and is the mistake this project has now made in four different instruments; the
  plant marks it, so the sentence cannot drift back.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 190 files already formatted on this tree; the record commit quotes the `git archive` export (finding 81's rule) |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --preset dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | Evidence is intact -- 0 CHANGED, 0 MISSING, 0 unregistered |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 453 tests collected |
| Python | `.venv/bin/python -m pytest -q` | 522 passed |
| Falsification, full sweep | recorded in the next commit, on the sha it ran on | pending |
| CI on the pushed head | recorded in the next commit, from the runner's own logs | pending |

## 6. Numerical validation

* **109** declared plants; each is proven against its own guard by the sweep named in §5.
* **103** register entries, from the producer that counts the file's numbered entries.
* **3** guards added, **1** generalised; **4** plants added, all four mutating the interpreter.
* **522 / 453** -- this environment's pair after three new tests, each measured by its own producer
  rather than transcribed from §5.

## 7. Remaining limitations

* **#103 stays open.** The registry still accepts a plant whose named guard does not read the line it
  mutates; what changed is the cost of discovering it. The sound static rule needs the nested-scope and
  file-as-text cases handled without inventing false alarms, and the sound dynamic rule costs a suite
  per plant.
* **#99, #101 and #102 stand** -- the citation class still checks existence rather than meaning, the
  spelled reader's precision on prose is still unmeasured, and the recall instrument for what the claim
  rule cannot see still does not exist.

## 8. Technical debt registered here

| Entry | What it records | Why it is a limitation and not a defect |
|---|---|---|
| #103 (opened here, (a) mitigated, open) | a plant's `guard` is unproven before the sweep, and the static pairing rule measured 7 false alarms of 10 | the instrument's failure mode is silence, and the only sound pre-flight costs a suite per plant |
| finding 86 | the mis-named reader, the `104/105` sweep, and the recurrence from Phase 41 | recorded because the class -- a hand-typed pointer to a reader -- is not specific to this harness |
| -- | no other entry opened by this phase | the residual in §7 is #99/#101/#102's, already registered |

## 9. The gate

Closed when the sweep on the committed tree runs to `109/109` with the tree clean afterwards; when a
deliberately mis-pointed plant is shown to stop the run at that plant rather than at the end, which is
`--only` against the guard named in §1; when CI's three jobs are read from their own logs on the pushed
revision; when the register size, the plant count and the test pair each come from their own producer in
every document that quotes them; and when #103's entry states the measured 7-of-10 rather than the
anecdote, since the measurement is what makes the static half a decision instead of an omission. A
record checks the revision it names: the sweep and CI rows land in the commit after this file, on the
sha the runner built.
