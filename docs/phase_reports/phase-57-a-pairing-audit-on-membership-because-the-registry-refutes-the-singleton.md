# Phase 57 — a pairing audit on membership, because the registry refutes the singleton (#103 closes, #107 opens)

## 1. Completed

#103 prescribed a dynamic pairing audit and named its criterion: "run the named guard *and* its neighbours
under one mutation and require that exactly the named one objects". The audit is shipped --
`scripts/run_mutation_suite.py --pairing-audit` -- and the criterion it shipped with is not the one the entry
wrote, because the registry says that criterion is wrong.

| Quantity | Measured | Meaning |
|---|---|---|
| plants in the registry | 153 → 160 | 7 plants added, each attacking the audit itself |
| distinct guards | 72 | the audit's real denominator |
| observable by a module run | 67 | one plant per guard whose guard is a pytest node |
| unreachable, named | 5 | 3 CTest cases, 2 probe plants that create their own target |
| plants whose named guard was in the failing set | **67 of 67** | membership separates finding 86's defect with no false alarm |
| plants whose named guard was the *only* one | **27 of 67** | the prescribed equality test would refuse the other 40 |

The failing-set histogram is `1: 27, 2: 20, 3: 11, 4: 7, 6: 1, 7: 1`. Forty honest plants edit a
module-level structure that several guards read, and all of those guards object at once. Requiring a
singleton would have flagged every one of them, which is the same mistake #103's static half made when it
cried wolf on 7 of 10 plants -- this time measured before shipping rather than after.

So the shipped verdict function is `audit_verdict(ran, failing, named)`: `paired` when the name is in the
set whatever its size, `named-guard-stayed-green` when the set is non-empty without it, `no-guard-objected`
when the set is empty, and `module-could-not-be-run` when pytest never collected. The last one is not
cosmetic: `pytest` answers 1 for failures and 2, 3, 4, 5 for runs that never happened, and folding those
into an empty set turns a broken module into a plant that escaped every guard.

The sampler is by guard and decided by what can run, not by who registered first -- a guard shared between a
probe plant and a prose plant is observable, and registry order would hand it to the unreachable list. The
census divides by what it observed: the probe that produced this measurement printed `0 of 72` while five
samples never ran, and the difference between 67 and 72 is the difference between a measurement and a guess.

Five guards in `tests/python/test_mutation_suite.py` hold the mechanism, one of them forcing its own premise
with synthetic plants because the shipped registry happens to order every shared guard favourably. #107
records what membership does not buy: with 40 of 67 plants reddening several guards, the audit cannot show
that the named guard rejected *for the reason the plant's claim gives*, and that needs the message inside the
named guard's own traceback section -- which is exactly where finding 91 bit Phase 56.

Register: 106 → 107 (#103 amended closed on the measurement that refuted its prescription, #107 opened),
finding 91 recorded, 7 plants (153 → 160), 5 guards (527 → 532 tests, 458 → 463 collected offline).

## 2. Assumptions this rests on

- Running a guard's whole module observes that guard and its neighbours. It does not observe a guard in a
  different module, which is why the sample is one plant per guard and not one per module.
- The failing set is read from pytest's own `FAILED` summary lines. A summary format change would surface as
  every plant reading `no-guard-objected`, and the census's `observed` denominator would go to zero.
- Cost is 67 module runs, roughly 35 minutes on this laptop, dominated by the 42 plants whose guard lives in
  `tests/python/test_artifact_metadata.py`. That is why the audit is a per-phase instrument and the CI lane
  keeps the sweep.
- Both instruments write to tracked files, so the clean-at-`HEAD` preflight that guards the sweep guards the
  audit too, and the two must never be in flight together.

## 3. Files changed

- `scripts/run_mutation_suite.py` -- `--pairing-audit`, `parse_failures`, `audit_verdict`, `_audit_blocker`,
  `pairing_sample`, `audit_counts`, `audit_census`, `run_pairing_audit`, `run_pairing_mode`,
  `Harness.module_failures`, and the signal-restore machinery extracted into `restore_on_signal` with
  `tree_of` so the audit and the sweep share one rule about what to put back.
- `tests/python/test_mutation_suite.py` -- five new guards over the verdict, the reader, the sample, the
  census and the return-code boundary.
- `scripts/mutation_plants.py` -- seven plants attacking the audit, one re-pointed count anchor per cascade
  site.
- `docs/limitations.md` -- #103 amended closed, #107 opened.
- `docs/integrity_audit.md` -- finding 91.
- `docs/project_scope.md` -- §9 row.
- Count cascade: `README.md`, `docs/reproducibility.md`, `docs/interview_defense.md`,
  `docs/validation_matrix.md`, `docs/release_notes_v1.3.0.md`, `paper/technical_report.tex` and the rebuilt
  `paper/technical_report.pdf` with its `technical_report.build.json` pair.

## 4. What the phase learned, including about its own first design

**A registered fix is a hypothesis, and this one arrived with its criterion already written.** #103 did not
say "measure what the failing sets look like"; it said "require that exactly the named one objects". Had the
phase implemented that sentence, the audit's first run would have printed 40 failures against plants whose
guards do exactly what they claim, and the tempting repair would have been to narrow the sample. The
criterion was measured against the registry before it was coded, and the measurement is the reason the
shipped rule differs from the prescription. This is the fourth phase in a row where the entry's own proposed
mechanism died on a probe (#103's static half, #106's compelled attribution, #105's greedy alternative, and
now #103's dynamic criterion).

**The denominator of a measurement has to be produced by the measurement.** `0 of 72` was not a wrong
division of a right number: five plants never ran, so 72 was never the sample. The census now derives every
figure from the records it observed and prints `declared = sampled + unreachable` as an arithmetic the reader
can check, which is also what makes the `not-run` bucket visible instead of silently shrinking the
denominator.

**Order-independence in a sampler is worth forcing rather than inheriting.** The registry today puts a
runnable plant first for every shared guard, so a sampler keyed on registry order passes a census over the
real list. The premise was forced with two synthetic plants in both orders instead -- an absence in current
data is not a mechanism, and the plant that breaks this fires on the forced test and not on the census.

**An instrument that quotes evidence needs a producer for the quotation too.** The Phase 56 record's
branch-audit paragraph cited a message that belonged to a neighbour guard, because pytest pads a header to
the terminal width and the cutter assumed a fixed one. The counts in the paragraph were unaffected, so
nothing numeric argued with it. That is finding 91, and it is why #107 asks for the message-level check to
arrive with its boundary proved against both paddings.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | pending |
| Format | `.venv/bin/ruff format --check .` | pending |
| Types | `.venv/bin/mypy python/quantrisk` | pending |
| C++ | `ctest --test-dir build/dev` | pending |
| Validate | `.venv/bin/quantrisk validate` | pending |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | pending |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | pending |
| Python | `.venv/bin/python -m pytest -q` | pending |
| Falsification, full sweep | `.venv/bin/python scripts/run_mutation_suite.py --all` | pending, on the committed tree |
| Pairing audit | `.venv/bin/python scripts/run_mutation_suite.py --pairing-audit` | pending, on the committed tree |
| CI on the pushed head | read from each job's own log | pending |

## 6. Numerical validation

| Figure | Value | Producer |
|---|---|---|
| Distinct guards / observable / unreachable | 72 / 67 / 5 | `pairing_sample()` |
| Named guard in the failing set | 67 of 67 | `--pairing-audit` census |
| Named guard alone | 27 of 67 | the same census |
| Failing-set histogram | 1: 27, 2: 20, 3: 11, 4: 7, 6: 1, 7: 1 | the same census |
| New guards / plants | 5 / 7 | the suite and `--list` |
| Register entries | 106 → 107 | `docs/limitations.md` |
| Audit wall time | pending | measured on the committed tree |

## 7. Remaining limitations

- Membership says a guard objected, not that it objected about the claim. #107 carries that, with the
  message-level check and its padding trap named as the way through.
- Five guards have no plant this shape can run, and 86 plants share a guard with a sampled one, so the audit
  is a census of guards rather than of plants.
- The audit reads pytest's `FAILED` lines. It is a consumer of one reporter's format, and a format change
  shows up as a mass `no-guard-objected` rather than as an error.
- Cost keeps it out of CI: 67 module runs per pass. CI keeps the sweep, which runs one node per plant and
  still proves every named guard rejects.

## 8. Technical debt registered here

- **#107** opened: the audit cannot show that the named guard rejected for the reason the plant's claim
  gives, 40 of 67 plants redden several guards so the failing set is the wrong instrument for that question,
  and reading the named guard's own traceback section has a padding trap that already fired once (finding
  91). Named with the message-level check and the boundary proof that would close it.
- **#103** amended closed. Its (a) half shipped in Phase 46; its (b) half shipped here as membership, with
  the entry's own singleton criterion refuted by measurement.

With #103 closed, the items earlier phases left as actionable are all settled: #95, #97, #98, #99, #101,
#102, #104, #105 and #106 each carry a closing clause, and what they leave behind they state as a limit of
the instrument rather than a queue item -- #101's and #106's refusal to check the *truth* of a declared
reason, and #102's recall bound of 1/11 on the unbiased sample. **#107 is the queue head this phase created**:
it names its own instrument, so it is debt, and it is Phase 58's work.

## 9. The gate

The gate this phase moves is the one that had no instrument at all: #103 said a hand-typed `guard` field
cannot be distinguished from a hand-typed reader that never reads it, except by paying a suite. The payment
was made once, and the receipt changed the purchase -- the audit that shipped answers "did the guard you
name object", and the registry's own answer of 67 of 67 says that is the question finding 86 was asking. The
question it does not answer, whether the guard objected *because* of the line the plant moved, is now #107
with a named instrument and a named trap, which is the same shape every phase in this queue has been closing
with: not a smaller worry, but a narrower one that has a measurement attached.
