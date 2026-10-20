# Phase 58 — a text link for every plant, and a named residual for the one that has none (#107 closes)

## 1. Completed

#107 asked whether the pairing audit can say that a guard rejected *about* the line the plant moved, when
51 of the 78 plants the shipped census observes redden several guards at once and membership cannot tell
them apart. The answer shipped
inside the existing `--pairing-audit`, and it cost no extra runs: pytest is now invoked with `--tb=line`,
which prints one entry per failure as

```
tests/python/test_artifact_metadata.py:3146: AssertionError: docs/... no longer prints these real counts
```

-- a file, a line and the whole message. The audit takes that line, compares it to the named guard
function's `ast` span, and reads the plant's link from the guard's *reading closure*: the guard's own body,
every same-file binding it references, and nested definitions included, to depth eight. If the closure names
the edited path or a token taken from the anchor, the pairing is attributed; otherwise the plant is named.

| Rule | plants | meaning |
|---|---|---|
| the shipped closure rule attributes the failure to the guard's own line | 77 of 78 | the census `--pairing-audit` printed on `cd0359b` |
| named in `UNATTRIBUTED_PLANTS` | 1 | `release-note-cites-a-digest-its-file-does-not-carry` |
| the narrow rule (function text alone, no closure) | 61 of 72 | the probe sample, before this phase's plants grew the registry to 78 |

The one exception is instructive rather than embarrassing: its anchor is a 40-character commit digest, the
guard reads release notes by globbing them, and no amount of closure walking finds a string the guard never
spells. So the residual is a pinned frozenset, policed both ways -- a plant that loses its link and is not
added, or one that gains a link and stays listed, reddens the guard.

The census the phase shipped is not the one it designed. On `6ddc965` the audit came back
`AUDIT_RC=1`: the pinned-residual guard reported a *second* unlinkable plant,
`claim-modifier-slot-reopened-after-the-census`. That plant's edit deletes the one reference the guard's
closure follows (`... + _MODIFIER_BLOCK`), and the audit had been building the closure from the file
*after* the plant fired -- so it erased the evidence of its own pairing. The offline pin computes the same
rule over the committed file and called the plant linked. The two readers of one rule disagreed because
they read different states, and the pin was the one asking the right question: "does this guard read the
symbol the plant attacks" is a property of the program as written. The audit now reads two texts on
purpose -- the assertion's line against the mutated file, because a traceback indexes what pytest compiled,
and the closure against the pre-plant file -- with the split pinned structurally so neither half can be
quietly unified. Exactly one of the six sampled plants whose guard lives in the file it edits changed
verdict, and it was the one the pin already knew about.

Two traps were measured on the way, both from the same session's probe set. A `-rf` short summary clips the
message at terminal width (`AssertionError: th...`), so message text cannot come from the summary; and a
closure walk that indexes only top-level definitions loses the chain that runs through a helper defined
*inside* the test, which is how 8 of the 72 looked unlinkable before nested names were included. Finding 91
-- a transcript sliced at a fixed-width separator quoting a neighbour's message -- is what the location
rule exists to prevent, and it is now the shape of the instrument rather than a caution in a report.

Register: #107 amended closed, no new entry. 8 plants (162 → 170), 6 guards (532 → 538 tests, 463 → 469
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
- The closure is read from the file as it stood before the plant fired, and the assertion's line from the
  file after. Those are deliberately different states: if they were ever unified in either direction, the
  attribution would either follow a plant's own deletion or index a line number that no longer exists. The
  structural guard refuses both, and its plant swaps them.

## 3. Files changed

- `scripts/run_mutation_suite.py` -- `TRACEBACK_LINE`, `parse_line_tracebacks`, `guard_span`,
  `reading_closure`, `anchor_tokens`, `attribution`, `failing_assertion`, `UNATTRIBUTED_PLANTS`,
  `Harness.module_failures` switched to `--tb=line` and returning the per-assertion entries, the two new
  census fields, and the residual report in `run_pairing_mode`. The audit now reads two texts: the
  assertion's line against the mutated file, because a traceback indexes what pytest compiled, and the
  reading closure against the file as it was before the plant fired, because a plant that deletes the
  reference the closure follows must not be able to erase its own pairing.
- `tests/python/test_mutation_suite.py` -- six new guards; the Phase 57 return-code guard updated for the
  wider return.
- `scripts/mutation_plants.py` -- eight plants attacking the attribution, two anchors re-pointed at the
  rebuilt return line and the closure-source line, and the plant-count annotations moved.
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

**When a guard and the instrument it pins disagree, the disagreement is the finding.** The residual list
reddened on a second plant, and the cheap reading was "there are two exceptions now". The rule both halves
implement is the same one; what differed was the state each read -- committed file versus mutated file. A
plant that removes the name the closure follows then destroys the evidence of its own pairing, and an
instrument that reports that as an exception is teaching the next reader that the registry contains a
limitation it does not contain. Naming the plant would have been the wrong fix, and the pinned set made it
impossible to make silently: that is what a pin is for.

**Recording a residue without queueing it is a real decision, and it needs its cost written down.** The
differential run -- neutralise the mutated line, require green -- is the only instrument that separates
seeing from causing. It doubles a census to two runs per guard -- 78 sampled becomes 156 -- to interrogate
one plant that is already named. The
entry now says that, with the number, so the next reader does not re-propose it as an oversight.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 202 files already formatted, measured on the `git archive` export of `cd0359b` (finding 81's rule), and the runner's own log reports the same 202 |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --test-dir build/dev` | 100% tests passed out of 204 (no C++ change this phase) |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | `Evidence is intact.` -- 95 OK, 0 CHANGED, 0 VOLATILE, 0 MISSING. The report bundle moved to `cd1f36ecebb2` (PDF `36b36ecea15d`) when this phase's cascade landed; no experiment artifact was re-frozen |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | `469 tests collected in 0.76s`, exit 0 |
| Python | `.venv/bin/python -m pytest -q` | 538 passed in 109.35s |
| Falsification, this phase's plants | `run_mutation_suite.py --all --only <the eight>` | 8/8 planted defects rejected by their guard, 34 s |
| Falsification, full sweep | `.venv/bin/python scripts/run_mutation_suite.py --all` | 170/170 planted defects rejected by their guard, 540 s, measured on the committed tree `cd0359b` |
| Pairing audit | `.venv/bin/python scripts/run_mutation_suite.py --pairing-audit` | exit 0 on `cd0359b`: 83 declared guards = 78 sampled + 5 named unreachable; 78/78 observed paired, 27 of them alone; 0 mis-paired, 0 escaped, 0 unrunnable; 77/78 attributed by text, 1 named |
| CI on the pushed head | read from each job's own log | run `39279864968` on `cd0359b`, three jobs from their own logs: `All checks passed!` + `202 files already formatted` + `Success: no issues found in 23 source files`; `100% tests passed out of 204` and `468 passed, 5 skipped in 224.34s`; `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 324.2s total`. The pair reconciles: 468 + 5 = 473 = 469 collected offline + 4 (#91) |

## 6. Numerical validation

| Figure | Value | Producer |
|---|---|---|
| Sampled plants / observed paired / attributed / named | 78 / 78 / 77 / 1 | the census line `--pairing-audit` prints, measured on `cd0359b` |
| Guards declared / sampled / named unreachable | 83 = 78 + 5 | the same line, derived from the records it observed |
| Plants whose named guard was the only one reddened | 27 of 78 | the same line |
| Narrow rule (function text only) | 61 of 72 | `build/phase58-probe.py`, `phase58-probe2.py`, on the probe sample this phase grew |
| Gained by the closure | 10 | the same probes, before and after nested indexing |
| Plants changed verdict when the closure moved to the pre-plant text | 1 of 6 | `build/phase58-flipscan.py`, over the sampled plants whose guard lives in the file they edit |
| New guards / plants | 6 / 8 | the suite and `--list` |
| Register entries | 107, unchanged | `docs/limitations.md` |
| Sweep wall time | 540 s for 170 plants | `SWEEP_RC=0 WALL_SECONDS=540` from the chain log |
| Audit wall time | not published | the chain's own difference, 34,108 s, spans a laptop that slept mid-run; per-run cost is visible instead in the sweep's 540 s and Phase 57's 71-run/57-minute census |

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
