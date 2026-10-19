# Phase 58 — a text link for every plant, and a named residual for the one that has none (#107 closes)

## 1. Completed

#107 asked whether the pairing audit can say that a guard rejected *about* the line the plant moved, when
44 of 72 plants redden several guards at once and membership cannot tell them apart. The answer shipped
inside the existing `--pairing-audit`, and it cost no extra runs: pytest is now invoked with `--tb=line`,
which prints one entry per failure as

```
tests/python/test_artifact_metadata.py:3146: AssertionError: docs/... no longer prints these real counts
```

-- a file, a line and the whole message. The audit takes that line, compares it to the named guard
function's `ast` span, and reads the plant's link from the guard's *reading closure*: the guard's own body,
every same-file binding it references, and nested definitions included, to depth eight. If the closure names
the edited path or a token taken from the anchor, the pairing is attributed; otherwise the plant is named.

| Rule | plants of 72 | meaning |
|---|---|---|
| the guard function's own text names the path or an anchor token | 61 | the narrow rule |
| plus the reading closure (nested defs indexed, depth 8) | 71 | the shipped rule |
| named in `UNATTRIBUTED_PLANTS` | 1 | `release-note-cites-a-digest-its-file-does-not-carry` |

The one exception is instructive rather than embarrassing: its anchor is a 40-character commit digest, the
guard reads release notes by globbing them, and no amount of closure walking finds a string the guard never
spells. So the residual is a pinned frozenset, policed both ways -- a plant that loses its link and is not
added, or one that gains a link and stays listed, reddens the guard.

Two traps were measured on the way, both from the same session's probe set. A `-rf` short summary clips the
message at terminal width (`AssertionError: th...`), so message text cannot come from the summary; and a
closure walk that indexes only top-level definitions loses the chain that runs through a helper defined
*inside* the test, which is how 8 of the 72 looked unlinkable before nested names were included. Finding 91
-- a transcript sliced at a fixed-width separator quoting a neighbour's message -- is what the location
rule exists to prevent, and it is now the shape of the instrument rather than a caution in a report.

Register: #107 amended closed, no new entry. 7 plants (162 → 169), 5 guards (532 → 537 tests, 463 → 468
collected offline).

## 2. Assumptions this rests on

- `--tb=line` keeps the message whole. Verified on a 250-character assertion message and on a 71-character
  test name; if a future pytest clips it, the attribution degrades to "line known, message absent" rather
  than to a wrong quote.
- The file name in a traceback entry is matched by basename, because pytest prints the path relative to the
  invocation directory. Two modules sharing a basename in one run would collide; the suite has none, and the
  attribution test would notice if that changed.
- A text link is not a cause. The claim this phase can make is that the guard could see what changed, which
  is the strongest claim the artifact supports without a differential run.
- Closure depth eight is a bound, not a proof of exhaustion. Deeper chains resolve today; the guard that
  pins it (`reading-closure-stops-at-one-hop` as a plant) fires the moment the bound becomes the reason for
  a miss.

## 3. Files changed

- `scripts/run_mutation_suite.py` -- `TRACEBACK_LINE`, `parse_line_tracebacks`, `guard_span`,
  `reading_closure`, `anchor_tokens`, `attribution`, `failing_assertion`, `UNATTRIBUTED_PLANTS`,
  `Harness.module_failures` switched to `--tb=line` and returning the per-assertion entries, the two new
  census fields, and the residual report in `run_pairing_mode`.
- `tests/python/test_mutation_suite.py` -- five new guards; the Phase 57 return-code guard updated for the
  wider return.
- `scripts/mutation_plants.py` -- seven plants attacking the attribution, one anchor re-pointed at the
  rebuilt return line, and the plant-count annotations moved.
- `docs/limitations.md` -- #107 amended closed, its residue recorded with its cost and the reason it is
  not taken.
- `docs/project_scope.md` -- §9 row.
- Count cascade: `README.md`, `docs/reproducibility.md`, `docs/interview_defense.md`,
  `docs/validation_matrix.md`, `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md`,
  `paper/technical_report.tex` and the rebuilt `paper/technical_report.pdf` with its digest pair.

## 4. What the phase learned, including about its own first design

**The cheapest instrument is usually a flag on one that already runs.** #107 priced itself as "a second
census", because #103 had taught that dynamic pairing costs a suite per plant. It did not: the audit already
runs each module, and `--tb=line` costs nothing relative to `--tb=no`. The thing that looked like doubling
was a report-format change.

**A derived rule is worth more than a declared one, and the proof is in what it refuses to say.** The
alternative was a `signal=` field on each plant naming the message its guard should raise -- 169 more
hand-typed strings, which is precisely the disease #103 was about: a string a guard can agree with while
nothing disagrees. The closure rule needs no new strings, and when it cannot attribute, it says so and names
the case, instead of accepting a claim nobody can check.

**Two of the three designs were wrong before measurement said so.** The first closure walk indexed only
module-level definitions and used a depth cap of three: 61 + 8 of 72, with the eight looking like the
#103-shaped residue. Indexing nested definitions -- the same blind spot #103's static half blamed for
missing a nested helper -- turned eight misses into hits. The lesson is not "widen until green" but that a
reachability rule's failure has to be traced to *why* it fails before it is accepted as an exception.

**Recording a residue without queueing it is a real decision, and it needs its cost written down.** The
differential run -- neutralise the mutated line, require green -- is the only instrument that separates
seeing from causing. It doubles a 72-run census to 144 to interrogate one plant that is already named. The
entry now says that, with the number, so the next reader does not re-propose it as an oversight.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | pending |
| Format | `.venv/bin/ruff format --check .` | pending |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --test-dir build/dev` | 100% tests passed out of 204 (no C++ change this phase) |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | pending |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | pending |
| Python | `.venv/bin/python -m pytest -q` | pending |
| Falsification, full sweep | `.venv/bin/python scripts/run_mutation_suite.py --all` | pending, on the committed tree |
| Pairing audit | `.venv/bin/python scripts/run_mutation_suite.py --pairing-audit` | pending, on the committed tree |
| CI on the pushed head | read from each job's own log | pending |

## 6. Numerical validation

| Figure | Value | Producer |
|---|---|---|
| Sampled plants / attributed / named | 72 / 71 / 1 | the static closure rule, run by the guard |
| Narrow rule (function text only) | 61 of 72 | `build/phase58-probe.py`, `phase58-probe2.py` |
| Gained by the closure | 10 | the same probes, before and after nested indexing |
| New guards / plants | 5 / 7 | the suite and `--list` |
| Register entries | 107, unchanged | `docs/limitations.md` |
| Audit wall time | pending, on the committed tree | the same run |

## 7. Remaining limitations

- A text link is not causality. The only instrument that separates them is the differential run priced in
  #107's closing clause, and this phase decided not to build it.
- The closure is same-file only. A guard that reads a mutated name through an imported helper in another
  module would be reported as unlinked and would have to be named, not guessed around.
- Basename matching of traceback paths assumes no two modules in one run share a file name.
- Attribution is computed over the *sampled* plant per guard, so a second plant behind the same guard gets
  no attribution of its own -- the same reach limit #107 states for membership.

## 8. Technical debt registered here

Nothing opened. #107 is amended closed, and the residue it leaves -- the seeing/causing gap, with the
differential's 144-run cost and the reason it is refused -- is recorded inside that entry rather than
queueed, on the precedent of #105's closing clause. With #103 and #107 closed, the register holds 107
limitations and no item that this queue still treats as actionable; what remains are the instrument limits
#101, #102, #106 and now #107 state as boundaries of what a guard can check.

## 9. The gate

The gate this phase moves is the one that decides when a queue is empty. #107 named an instrument, so it was
built -- cheaply, because the run already existed. What it did not name, and what the measurement showed to
be a doubling for one already-named plant, is written into the entry with its cost instead of opening
another phase. That is the difference between a limitation register that converges and one that manufactures
work: an item closes when the mechanism it asked for exists and the residue is priced, not when every
possible further check has been built.
