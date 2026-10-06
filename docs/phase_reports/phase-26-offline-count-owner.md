# Phase 26 — the second producer for a number the runner used to own

Date: 2026-10-06. Predecessor: Phase 25 (`phase-25-cpp-total-owners.md`), whose §8 item 1 is this debt
item; `docs/limitations.md` #63 is the rule it operates under. No `PROJECT_SPEC.md` phase number: it closes
a registered technical-debt entry. Repository version is unchanged (`1.7.0`), the tag still names
`79d536a`, and nothing here is claimed to be inside that release.

## 1. Completed

1. **A script that measures the oracle-free collection.**
   `scripts/measure_offline_collection.py` reads the `oracles` extra and the `dev` group out of
   `pyproject.toml` and blocks the difference — `QuantLib`, `cvxpy`, `pypfopt`, `sklearn`,
   `statsmodels`; **not** `scipy`, which a plain `uv sync` installs — by seeding `sys.modules` in a child
   interpreter, then collects. Measured here: **415 items, four module skips, zero collection errors**,
   against 484 collected with the oracles installed.
2. **A guard that refuses a probe which is not the runner's shape.**
   `test_the_offline_test_count_is_measurable_before_the_runner` requires non-empty block list, zero
   collection *errors*, exactly four skip records, and then compares every living quotation of the
   offline figure — `docs/limitations.md` #63, `docs/reproducibility.md`, `docs/interview_defense.md` in
   three of its own phrasings, `paper/technical_report.tex` — with the measurement.
3. **Both count guards now cover both environments.** The older guard compares a document's two figures
   with each other and with the environment it runs in, which means its oracle-free half has only ever
   been exercised by the runner. The new guard is that half, locally. Neither derives one number from the
   other, which is what #63 forbids: the difference between the two readings is not a constant, and this
   phase measured it twice rather than assuming it.
4. **The falsification is declared and it is also true by accident.** The plant
   `report-quotes-a-count-the-offline-probe-refutes` rewrites the report's `415 collected without them`
   as `400` (40 → 41 declared plants) and is caught by the new guard alone: with the oracles installed the
   older count guard cannot see an oracle-free staleness. Separately, writing the guard moved the
   measurement to 415 while the documents still said 414, and it went red — the failure mode it exists to
   produce, arriving on its own first.
5. **Fidelity, stated as comparisons rather than as proof.** Two exist. The probe reported 413 for the
   corpus whose CI guard message was `pytest collects 413`, and 414 for Phase 25's corpus, where the lane
   then ran green against the published 414 and printed `413 passed, 5 skipped` in its own line. Two
   agreements do not make the simulation the runner, so what is claimed here is disagreement detection
   *before* the push; the runner stays the arbiter of the published pair.
6. **Records moved:** finding 58, `docs/limitations.md` #63 amended in place with the new producer,
   `docs/reproducibility.md`'s instrument sentence, the pair 483 → 484 and 414 → 415 in every living
   document that repeats them, the plant-count annotation and its anchor (40 → 41), `docs/project_scope.md`
   §9, and `docs/interview_defense.md`'s state line.

## 2. Mathematical assumptions

None, and no numeric path was touched. The phase's only quantitative premise is structural: an
oracle-free collection differs from an oracle-bearing one by the items inside the gated modules, offset by
the module-level skip records they leave behind, and that offset was 69 in both of this phase's readings —
measured, not applied.

## 3. Files changed

| File | Change |
| --- | --- |
| `scripts/measure_offline_collection.py` | new: derived block-list, child-interpreter collection, JSON result |
| `tests/python/test_artifact_metadata.py` | one guard, `_offline_probe`, `_OFFLINE_CLAIMS` |
| `scripts/run_mutation_suite.py` | one plant declared (40 → 41), three anchors re-keyed |
| `docs/integrity_audit.md` | Phase 26 addendum, finding 58 |
| `docs/limitations.md` | #63 amended; the counts it quotes |
| `docs/reproducibility.md` | the instrument that produces the offline figure |
| `docs/interview_defense.md` | the pair 483 → 484 and 414 → 415 in its three phrasings, the plant annotation 40 → 41, and the state line |
| `docs/project_scope.md` | §9 Phase 26 row |
| `paper/technical_report.tex`, `paper/technical_report.pdf` | both counts; PDF rebuilt |

## 4. The probe, and the two ways it was wrong before it was right

1. **A finder that raised produced errors, not skips.** The first probe installed a `MetaPathFinder` whose
   `find_spec` raised `ImportError`. Collection then reported `413 tests collected, 4 errors`, which is the
   right *number* and the wrong *shape*: the runner reports four skip records, and a guard cannot tell a
   faithful simulation from one that happens to coincide. Seeding `sys.modules[name] = None` makes the
   import fail the way an absent distribution fails, `pytest.importorskip` catches it, and the shape
   matched: four skips, zero errors.
2. **Blocking the extra verbatim would have simulated a lane that does not exist.** The `oracles` extra
   lists `scipy`, but `scipy` is also in the `dev` group, and CI's plain `uv sync` installs the dev group.
   Blocking it would understate the offline count by however many `scipy`-gated cases exist. The block list
   is therefore `oracles − dev`, derived from `pyproject.toml`, so it tracks the lane instead of the label.
3. **The guard checked its own premise before being trusted.** Without the error/skip assertion a probe
   that blocked nothing at all would report the online figure, the documents would disagree with it, and
   the failure would look like the documents being wrong. That is why `blocked_imports`, `collection_errors`
   and `module_skips` are asserted in the guard rather than printed by the script alone.

## 5. Exact test results

```
uv run pytest tests/python -q                                 484 passed in 215.36s (0:03:35)
uv run python scripts/measure_offline_collection.py           collected 415, module_skips 4,
                                                              collection_errors 0, exit 0
uv run ruff check .                                           All checks passed!
uv run ruff format --check .                                  156 files already formatted
uv run python scripts/verify_evidence_manifest.py             Evidence is intact.
latexmk -pdf -g -interaction=nonstopmode technical_report.tex  Output written on technical_report.pdf (44 pages, 1003992 bytes)
```

Falsification:

```
declared plant    `oracles installed, 415 collected without them` -> `... 400 ...`:
                  `test_the_offline_test_count_is_measurable_before_the_runner` red, and
                  `test_the_documents_that_count_python_tests_count_the_ones_that_exist` passed on the
                  same mutation -- the uniqueness the plant exists to demonstrate. Tex restored to
                  829cff01d794e8421a7cd1b5daa53c36a3a973aecb63ce1756972c8fad41d62c, hash-verified.
incidental        adding this guard moved the measurement 414 -> 415 while the documents still
                  said 414: red against all four documents' phrasings at once, before any plant ran
fidelity (1)      probe 413 == runner's guard message `pytest collects 413`, same corpus
fidelity (2)      probe 414 == Phase 25's lane, which ran green on the published 414 and printed
                  `413 passed, 5 skipped in 143.13s`
```

## 6. Numerical validation

Nothing the engine measures changed and the frozen manifest verifies untouched. What was validated is an
instrument: the probe's collected count against the runner's own reported count at one revision (equal),
its skip shape against the runner's (four records, no errors), and the two readings of the same tree
against each other (415 with `oracles` absent, 484 present, difference 69 in this phase as measured).

## 7. Remaining limitations

The simulation is faithful at the shape and count level for the current set of gated modules; it is still a
simulation. A future test that gates on something *not* in the `oracles` extra — a missing binary, an
absent network, a platform without `libm`'s `erf` — would be skipped in CI and counted here, and the guard
would then report a mismatch that is real but not about the extras. #63 remains the place that says the two
figures are different quantities; this phase added the instrument, not an entitlement to compute one from
the other.

## 8. Technical debt

1. **Confirm the probe against the runner once more per change to the gated set**, not per phase: the guard
   can compare its own block list with the modules that actually skip, and a mismatch there is the signal
   that the simulation drifted.
2. **Carried forward:** PDF freshness (finding 56(d)), the release body versus the release note
   (finding 56(e)), the second 60-digit check's runtime (Phase 24 §8 item 4), and the sixth book for the
   radius.

## 9. Gate

§5's commands were run against the working tree before the commit that carries this report; the C++ suites
were not re-run because no C++ file moved. The sweep runs on the committed tree afterwards and its verdict,
this head's CI run, and the runner's reading of the offline count for the Phase 25 head (the second
fidelity datapoint) are appended in the commit that follows.
