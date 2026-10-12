# Phase 34 — the settings a green job cannot testify about

Date: 2026-10-12. Debt closed: the two items `docs/phase_reports/phase-33-…` §8 registered rather than
took on — nothing asserted that the pytest lane keeps fetching history and tags, and the sweep's bytecode
isolation was policed by an in-test control with no way to notice a bypass. Also delivered: the boundary
those two runs into, registered as `docs/limitations.md` #94.

## 1. Completed

1. **The CI configuration is now read by a guard.**
   `test_the_ci_lane_that_runs_the_guards_fetches_what_they_read` parses `.github/workflows/ci.yml`,
   selects the jobs whose steps run `pytest`, and requires the `actions/checkout` step ahead of that to
   carry `fetch-depth: 0` and `fetch-tags: true`. Without those settings the three history- and tag-keyed
   guards do not fail, they skip with a named reason, so the job's colour is not evidence that anything was
   checked -- and this is the first guard in the repository to read the workflow as structure.
2. **`pyyaml` joined the `dev` dependency group** so a guard can parse YAML in every lane that runs the
   suite, rather than in the one where a human remembers `uv run --with pyyaml`. Phase 24 set the precedent
   with `sympy`; `docs/reproducibility.md` now names both where it tells a reader what `uv sync` installs.
3. **The harness's plumbing is policed, not just its helper.**
   `test_every_subprocess_the_harness_runs_a_guard_in_is_bytecode_isolated` replaces the harness module's
   `subprocess.run` with a recorder, drives two guard steps through `Harness.pytest`, and asserts every
   recorded call carries `PYTHONPYCACHEPREFIX` — and that two consecutive calls carry different prefixes.
   Phase 33 proved the environment builder returns isolated environments; this proves nothing walks past it.
   The constant `BYTECODE_PREFIX` is shared by the setter and the policer so the two cannot drift.
4. **A plant was attempted, refused, and turned into a registered boundary.** The natural falsification of
   item 3 anchors on the line in `Harness.uv` that passes the environment. The harness requires an anchor to
   occur exactly once in its target file — finding 25's failure mode is an edit that lands on nothing and is
   then counted as caught — and a plant written into the file that holds the plant list always sees two
   copies: the code and the plant's own anchor string. So the case is refused before it runs, and no plant
   for a defect *inside* `scripts/run_mutation_suite.py` can exist in its present shape.
5. **The guard's red state was still produced, by demonstration.** Dropping the argument to `None` and
   running the node printed `AssertionError: a guard subprocess was spawned with no environment at all`; the
   file was restored and the node passed. That is a demonstration, not an instrument, and #94 says what
   that costs.
6. **Register count and totals moved under guard direction** — 505 → 507 tests, 436 → 438 collected
   offline, register 93 → 94, plants 61 → 62 — with six plant anchors re-keyed in the same commit as the
   figures they name.

## 2. Assumptions this rests on

- A job that runs pytest is a job whose checkout the guards depend on; a future lane that runs them from a
  different job is covered by the loop rather than by a name, and a lane that never checks the repository
  out is reported as a failure rather than assumed.
- `fetch-depth: 0` implies tags in `actions/checkout@v7`. Both settings are asserted anyway, because the
  implication is a property of an action's documentation and the guard should not depend on remembering it.
- The CI-parity guard is checked on the runner it describes: the lint and build jobs both run pytest, and
  the parse happens in the ordinary lane, so a workflow edit that breaks it reddens CI rather than only a
  laptop.
- The demonstration in item 5 is reproducible by the steps written here; it is not re-run automatically,
  which is exactly the gap #94 records.

## 3. Files changed

| File | Change |
|---|---|
| `.github/workflows/ci.yml` | unchanged this phase; now asserted |
| `pyproject.toml`, `uv.lock` | `pyyaml>=6.0` in the `dev` group |
| `tests/python/test_artifact_metadata.py` | the CI-configuration guard, register and test counts |
| `tests/python/test_mutation_suite.py` | the subprocess-accounting guard, `BYTECODE_PREFIX` asserted by name |
| `scripts/run_mutation_suite.py` | `BYTECODE_PREFIX` constant; one plant added (`ci-lane-drops-the-history-its-guards-read`); six anchors re-keyed |
| `docs/limitations.md` | #93 amended with its closure, #94 opened, living totals synced |
| `docs/integrity_audit.md` | Phase 34 addendum, finding 67 |
| `docs/reproducibility.md` | the dev-group sentence names `pyyaml`; totals synced |
| `docs/project_scope.md` | §9 Phase 34 row, refresh date 2026-10-12 |
| `docs/interview_defense.md` | state line to Phases 0–34, totals, register count, sweep annotation |
| `README.md`, `docs/validation_matrix.md`, `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md` | the register count the guard moved |
| `paper/technical_report.tex`, `.pdf`, `.build.json` | counts and register synced, then the render rebuilt by the producer |

## 4. What the phase learned, including about its own first design

- **A guard's input set can be a config file, and then the config file needs a guard.** Phase 33 changed a
  workflow to make three checks real and registered that nothing kept it true. A skipped guard is not a
  failed guard: it reports a reason, the lane passes, and the only artefact saying "this was checked" is the
  setting itself.
- **The plant list and its own file cannot be the same file.** Every anchor-based tool has this limit; the
  interesting part is that the harness *caught itself* — it refused the case rather than guessing, which is
  the behaviour finding 25 bought. Registering it (#94) is better than working around it: the tempting
  workaround was to loosen the uniqueness rule, which would reintroduce the silent no-op edit.
- **A demonstration is weaker than an instrument, and saying so is the fix.** The red in item 5 is real and
  repeatable, but nothing re-runs it. #94 states that plainly, and names the structural answer (move
  `MUTATIONS` into a data module) together with the reason it was not done here: it rewrites the file every
  phase edits, which is a change worth its own phase rather than a side effect.
- **`--frozen` kept the dependency honest.** `uv add` rewrote `pyproject.toml` and `uv.lock` together; the
  guard subprocesses then ran under `uv run --frozen`, so a lock drift would surface as a failure rather
  than a silent re-resolve (`docs/integrity_audit.md` finding 62's environment lesson, used deliberately).

## 5. Exact test results

| Gate | Command | Result |
|---|---|---|
| Python | `uv run pytest tests/python -q` | `507 passed in 87.60s` on the final tree |
| Offline lane | `uv run python scripts/measure_offline_collection.py` | `collected: 438`, `module_skips: 4`, `collection_errors: 0` |
| Docs + harness lanes | `uv run pytest tests/python/test_artifact_metadata.py tests/python/test_mutation_suite.py -q` | 66 passed; the CI guard and the accounting guard are both in that count |
| New guard, red on demand | hand-edit `Harness.uv` to pass `None`, run the node, restore | `AssertionError: a guard subprocess was spawned with no environment at all`, then `1 passed` after restore — recorded as a demonstration, not a plant |
| Falsification, the new plant | `uv run python scripts/run_mutation_suite.py --only ci-lane-drops-the-history-its-guards-read --verbose` | `caught`: anchor unique, bytes changed, guard red, sha-verified restore, guard green |
| C++ | `uv run ctest --preset dev` | 100% tests passed out of 204 — re-run even though no C++ input changed, because "unchanged" is a claim about the tree and the gate is the measurement |
| Catch2 | `./build/dev/quantrisk_tests` | All tests passed (548368 assertions in 203 test cases) |
| Identity | `uv run quantrisk validate` | 7/7 checks passed |
| Lint | `uv run ruff check .` / `uv run ruff format --check .` | All checks passed! / 172 files already formatted — a walk of this directory, not a census (finding 62(d)) |
| C++ format | `uv run clang-format --dry-run -Werror` over all 77 tracked `.cpp/.hpp/.h` | 0 diagnostics, exit 0 |
| Types | `uv run mypy python/quantrisk` | Success: no issues found in 23 source files |
| Producer | `uv run python scripts/build_report.py` | 6 sources, bundle `9d21b877d8ac…`, PDF `eff4cf0335ae…`, 1,005,777 bytes |
| Evidence | `uv run python scripts/verify_evidence_manifest.py` | 0 missing, 0 unlisted — Evidence is intact |
| Anchor census | one-pass enumeration of every declared plant against the file it names | 62 declared, 60 file-backed, 0 missing or non-unique |
| Falsification, full sweep | `uv run python scripts/run_mutation_suite.py` on `8760b5a`, logged to `build/mutation-sweep-34.log` | `62/62 planted defects were rejected by their guard.` exit 0, 62 lines of `ok caught`, no other status, and `git status --porcelain` empty afterwards |
| CI on the pushed record | `gh api …/commits/<sha>/check-runs` after the push | pending — recorded in the follow-up commit, which is the only place its run id can come from |

## 6. Numerical validation

No new measurement is published. The figures the phase moves are the two test totals (507 / 438), each from
its own collector, the register count (94, counted from the file by the guard that compares it) and the plant
count (62, counted from the list). The dependency addition changes no result: `pyyaml` is used only by a
guard that reads a configuration file. The freeze did not move — no producer was re-run, and
`verify_evidence_manifest.py` reports it intact, which is what makes that a check rather than an assertion.

## 7. Remaining limitations

- **The CI guard checks the fetch settings, not the guards' behaviour.** If the checkout keeps its settings
  and a guard's skip reason changes shape, the lane still passes with the same number of skips. The runner's
  own summary is read by a human per phase; nothing asserts "exactly these five tests skip on CI", and
  #89's per-document inventory does not cover test sources.
- **A defect inside the harness file has no plant.** #94: the anchor-uniqueness rule and the plant list
  living in one file make it unplantable, so the accounting guard is backed by a demonstration whose
  repetition is not scheduled.
- **The structural fix is unbuilt by choice.** Moving `MUTATIONS` into a data module the harness imports
  would restore plant-ability for harness defects. It touches the file every phase edits, so it needs its own
  phase rather than arriving as a side effect.
- **`fetch-depth: 0` on every lane is still one setting, not a contract.** Only the job that runs pytest is
  asserted; the benchmark and lint lanes remain at the default, which is correct for them and unremarked
  here.

## 8. Technical debt registered here

- `docs/limitations.md` #94 — a plant cannot anchor inside `scripts/run_mutation_suite.py`, so guards about
  the harness's own plumbing are demonstrated rather than declared; the fix is to move the plant list into a
  module the harness loads.
- Nothing asserts the *shape* of CI's skip set, only the configuration that produces it (§7 item 1).
- `build/rewrap_docstrings.py` remains scratch with three phases of use behind it (carried from Phase 33).

## 9. The gate

Phase 33 made three guards depend on a workflow setting and said so in its own §8; this phase made that
dependence checked, and in doing so found the limit of the mechanism that checks everything else — a plant
cannot point at the file that lists plants. Both halves are now explicit: the lane's fetch settings are
asserted and planted, the harness's isolation is asserted and demonstrated, and #94 keeps the difference
between those two kinds of proof visible to whoever reads the register next.
