# Phase 23 — the report's own prose, read after the release

Date: 2026-10-05. Predecessor: Phase 22 (`phase-22-v1.7.0.md`), whose §9 is the release record this phase
extends. No `PROJECT_SPEC.md` phase number: the completion audit run after `v1.7.0` read the documents
rather than the gate output and found three present-tense sentences in `paper/technical_report.tex` that
the repository had already refuted. Repository version is unchanged (`1.7.0`); the tag still names
`79d536a`, and nothing here is claimed to be inside that release — the release note carries a dated
erratum instead.

## 1. Completed

1. **The three sentences, each proved stale against a committed artifact.**
   (a) §Limitations opens "The manifest is committed and verified: 69 artifacts, 6,208,835 bytes, of
   which … 40 statistical experiment files". Read from the tags, that triple is `v1.1.0`'s
   `evidence/manifest.json` `totals` exactly (69 / 6,208,835 / 40, verified with
   `git show v1.1.0:evidence/manifest.json`), and the sentence shipped in `v1.2.0` through `v1.7.0`. The
   same PDF's §1 prints "the frozen manifest hashes 94 artifacts".
   (b) §Stress Testing said the fifth-order crossing experiment "was specified and then deliberately not
   run". Phase 20 wrote that (`631d7c5`) as a true sentence; Phase 21 ran the experiment, and
   `git show v1.7.0:paper/technical_report.tex | grep -c 'deliberately not run'` returns 1, so the
   released PDF asserts a delivered measurement was withheld.
   (c) Two smaller ones: the report described `README.md` as quoting "twelve members executed" (a string
   README has not contained since the suite grew), and `docs/interview_defense.md` annotated the
   falsification command with `# 18/18 planted defects rejected` — written at Phase 14 (`74359f9`) when
   the harness held eighteen plants, against 38 now.
2. **Four guards, each derived from the producer rather than from prose.**
   `test_the_report_states_the_manifest_the_freeze_produced` compares the report's seven manifest numbers
   with `totals` and `totals.by_category`; `test_every_registered_experiment_is_named_in_the_report`
   loads the suite registry and requires each experiment's directory to appear in the document;
   `test_the_report_states_the_order_five_headline_the_artifact_holds` re-derives the paragraph's
   widening count, unchanged count, closer-count, two radius pairs and the ratio span from
   `experiments/fifth_order_crossing_map/results/fifth_order_crossing_map.json`, and additionally asserts
   the reading depends on a fact (`min ratio == max widening`) rather than on phrasing;
   `test_a_command_line_that_counts_plants_counts_the_declared_ones` reads the `# N/N planted defects`
   annotations and requires them to equal `len(MUTATIONS)`.
3. **The prose rewritten, not deleted.** §Stress Testing is retitled "The next order exists, and its
   answer is partial" and now states the measurement: 2 of 5 books widen (published ladder 0.15 → 0.20,
   deep out of the money 0.20 → 0.30), 3 unchanged of which 2 sit at the swept grid edge, the quintic
   closest inside the quartic radius on 5 of 5, and the order-five-to-four ratio spanning 0.057 to 0.588
   ordering nothing — with the smallest ratio taking the largest widening. §Limitations states the
   freeze's real size and turns the README sentence into a claim about the *kind* of number, dated to the
   phase that wrote it.
4. **The PDF rebuilt from the corrected source** (`latexmk -pdf -g`, 44 pages, 1,003,992 bytes). The
   release's own asset is untouched and the note says why.
5. **Records the change moves:** `docs/integrity_audit.md` finding 55 with its three parts and the
   falsification evidence, `docs/limitations.md` #84 stating what the guards do not reach, the dated
   erratum appended to `docs/release_notes_v1.7.0.md`, `docs/project_scope.md` §9's Phase 23 row, and the
   counts the four new tests move — 477 → 481 pytest, 83 → 84 limitations, 34 → 38 plants, each in every
   living document that repeats it.

## 2. Mathematical assumptions

None. No core file, binding, artifact or number produced by the engine changed in this phase: the
fifth-order radii, ratios and counts the report now states are read from the artifact Phase 21 froze, and
`scripts/verify_evidence_manifest.py` still reports the freeze intact with nothing regenerated. The one
arithmetic claim this phase touches is the report's own: `min(fits[*].order_five_over_four_at_measure_column)`
is the book with `max(books[*].widening_factor_quintic)`, which is asserted from the artifact rather than
restated from the note.

## 3. Files changed

| File | Change |
| --- | --- |
| `paper/technical_report.tex` | §Stress Testing's order-five paragraph rewritten; §Limitations' manifest sentence and README-quote sentence corrected; pytest and limitation counts synced |
| `paper/technical_report.pdf` | rebuilt from the corrected source |
| `tests/python/test_artifact_metadata.py` | three guards added (`_report_prose`, `_tex_manifest_sentence`, `_MANIFEST_CLAIMS` helpers) |
| `tests/python/test_mutation_suite.py` | one guard added for the command-annotation plant count |
| `scripts/run_mutation_suite.py` | four plants declared (34 → 38), two anchors re-keyed |
| `docs/integrity_audit.md` | Phase 23 addendum, finding 55 |
| `docs/limitations.md` | #84, and the test count it quotes |
| `docs/release_notes_v1.7.0.md` | dated erratum appended |
| `docs/project_scope.md` | §9 Phase 23 row |
| `docs/interview_defense.md` | state line, plant annotation, test and limitation counts |
| `README.md`, `docs/reproducibility.md`, `docs/validation_matrix.md`, `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md` | limitation-count restatements synced |

## 4. The instrument, and the two ways it was nearly decoration

1. **The first guard could not see the defect it was written for.** The obvious instrument was a
   sentence scan: find a sentence containing "not run" that also names a registered
   `experiments/.../run.py`, and refuse. Run against the shipped document it returned *zero* violations —
   the stale sentence says "the experiment that would use these terms", naming no path at all. A guard
   keyed on a shape the defect does not take is green forever. It was deleted and replaced by the
   registry-presence guard, which does fail on the shipped file, and the episode is the reason
   `docs/limitations.md` #84 says what the guards cover by name.
2. **A count sync disarmed two plants before the sweep could.** Moving 83 → 84 limitations and 477 → 481
   tests made `readme-undercounts-the-limitation-register` and `report-counts-stale-python-tests` anchors
   occur zero times. Finding 52's failure mode fired as designed:
   `test_every_declared_mutation_names_one_unique_anchor_and_a_guard_that_exists` went red on the working
   tree, and both anchors were re-keyed in the same commit rather than after a sweep that would have
   printed a lie.
3. **The two numbers the guard set cannot reach.** `docs/limitations.md` #63 forbids deriving one test
   count from the other, so the offline lane's collected count is not computed here: it is 408 in the
   living documents and four tests have been added since, and the number that goes in is the one the CI
   lane prints for this revision (§5). And the PDF's byte size moves between builds that differ in nothing
   but the toolchain's own timestamps, so the report quotes the page count and the tree's file size as
   measurements of this build, not as the release asset's.

## 5. Exact test results

```
uv run pytest tests/python -q                                481 passed in 129.10s (0:02:09)
uv run ctest --preset dev                                    100% tests passed out of 204
uv run ruff check .                                          All checks passed!
uv run ruff format --check .                                 150 files already formatted
uv run mypy python/quantrisk                                 Success: no issues found in 23 source files
uv run python scripts/verify_evidence_manifest.py            Evidence is intact.
uv run quantrisk validate                                    7/7 checks passed
latexmk -pdf -g -interaction=nonstopmode technical_report.tex  Output written on technical_report.pdf (44 pages, 1003992 bytes)
```

Falsification, run before the fix was written, against `paper/technical_report.tex` as committed at
`8680d63` — i.e. the document as released:

```
test_the_report_states_the_manifest_the_freeze_produced        3 violations: 69/94, 6208835/7145018, 40/65
test_every_registered_experiment_is_named_in_the_report        absent: ['experiments/fifth_order_crossing_map/']
test_the_report_states_the_order_five_headline_...             widening string absent, ratio span absent
test_a_command_line_that_counts_plants_counts_the_declared_ones 18/18 annotated, 38 declared
```

The fourth line was obtained by reading `docs/interview_defense.md` as committed at `8680d63` and applying
the same annotation pattern the guard uses, against `len(MUTATIONS)` loaded from the harness.

**The offline count went red on the runner, as §4.3 predicted it would.** `88a4c80`'s CI run
`37258779954` reports `Configure, build, C++ tests, Python tests: failure`, its own line
`1 failed, 410 passed, 5 skipped in 154.08s`, and the guard's words:

```
E  AssertionError: docs/interview_defense.md says 408 for this environment; pytest collects 412.
   oracles present: False
```

So the offline reading for this revision is 412 collected, measured by the lane that has no oracles to
collapse, and the living documents now say 412 (`docs/limitations.md` #63, `docs/reproducibility.md`,
`docs/interview_defense.md` in three of its phrasings, `paper/technical_report.tex`, and the plant anchor
over the command comment). `Format and static checks` and `Benchmark suite against live oracles` were
`success` on that same head. The number was not derived here — #63 forbids deriving one reading from the
other — and the red run is the evidence that deriving it would have been wrong, because a local
subtraction assumes a collapse constant this revision does not have.

## 6. Numerical validation

No measured quantity changed. What was validated is the *correspondence* between the document and the
artifacts: the seven manifest numbers, the five order-five figures and the presence of eighteen
experiment directories were each compared against their producer, and the comparison was then run against
the released document to show it can disagree with it. The manifest reading was taken five releases deep
(`v1.1.0` … `v1.7.0` totals) so the claim "this sentence has been stale since v1.2.0" is a measurement
rather than a recollection.

## 7. Remaining limitations

`docs/limitations.md` #84: the guards own the shapes they name — manifest totals, per-experiment presence,
one paragraph's figures, the sweep annotation. A false sentence that carries no number, names no
registered path and annotates no command line is still caught only by a reader, and this phase found
three of those in one document, so the residue is not hypothetical. The released `v1.7.0` PDF keeps the
sentences it was built with; the erratum is the only instrument available without moving a tag.

## 8. Technical debt

1. **`sympy` in the `dev` extra** so the derivation script's part A runs in CI (Phase 22 §8 item 2, still
   open).
2. **The offline test count needs its own owner.** #63 explains why the two readings cannot be derived
   from each other; nothing yet re-measures the offline lane when the with-oracles count moves, so a
   phase that adds tests must wait for CI or build a second environment. A cheap version: a test that
   counts the oracle-gated modules' collected items and asserts the published pair differs by exactly
   that, with the skip-record shape asserted separately.
3. **The assertion and Catch2-case totals are still prose** (Phase 19 §8, unchanged): `548,368` in `203`
   cases in four documents, with `ctest -N` owning only the 204.
4. **A guard generator over the report's numeric sentences.** This phase wrote three guards for three
   known lies. A `(\d[\d,]*) (artifacts|bytes|entries|…)` sweep over the tex, each classified as owned or
   explicitly historical, would list the unowned ones instead of waiting for a reader.

## 9. Gate

Commands and verdicts are §5's, taken from the working tree before the commit that carries this report.
The falsification sweep runs on the committed tree after it exists — the harness refuses a dirty tree —
and its verdict line, this commit's CI run and the offline lane's collected count are appended in the
commit that follows, which is the only place they can honestly live. `docs/limitations.md` #84, finding
55 and the release note's erratum are in this commit because they describe no measurement that postdates
it.
