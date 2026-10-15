# Phase 40 — a hyphen-preceded number is not a quantity, and two exemptions were paying for phantoms

Closed `docs/limitations.md` #100, the limit the spelled rollout found in its own rule, and with it a
defect class the register had never named: an exemption whose entire job was to excuse a claim the
extractor invented.

## 1. Completed

* **The claim's number may no longer be preceded by a hyphen.** `_CLAIM_EXCLUDE_CHARS` gained `-`, so the
  exclusion built from it refuses a number after a dash -- which is where the second half of a compound
  lives: `Level-1 identities` was read as one identity and `best of 0.2 %-1 % steps` as one step. Both
  rules share the constant, so the digit reader and the spelled reader tightened together; that is what
  the shared exclusion, number shape and noun tail have been for since Phase 38.
* **Measured in both directions before the change, as #95 asks of any widened detector.** Handing the
  hyphen back and enumerating every match over the six inventoried texts: three occurrences of two phantom
  texts under the digit rule (`1 identities` twice in `paper/technical_report.tex`, `1 % steps` in
  `docs/validation_matrix.md`), and three more under the spelled rule where it is not yet enabled
  (`four radius` in the rehearsal sheet, `five crossing radius` and `five radius` in the matrix). Nothing
  is lost: no real claim in this corpus legitimately follows a hyphen.
  `build/probe_hyphen_exclusion.py` and `build/probe_spelled_only_counts.py` are the measurements.
* **Two declarations deleted, and the check that deleted them is the finding.** `"Level-1 identities"` in
  the report's list and `"relative, best of"` in the markdown's each excused one of those phantoms; with
  the claims gone, both failed the inventory's own decorative test -- *an exemption that excuses nothing
  is dead weight*. That check has run since Phase 27, and this is the first time it has caught an entry
  whose purpose was a phantom rather than a real figure the project declines to own.
* **The two-sided control is property 6** of
  `test_the_claim_extractor_reads_percentages_and_refuses_labels`: it asserts the shipped rule refuses the
  two named texts, then hands the character back and requires the returned set to be exactly those two.
  Written as names rather than a count, so a corpus that stops holding them reddens it -- and so does a
  real claim that moves next to a hyphen.
* **One plant, 77 → 78:** `extractor-reads-a-hyphenated-compound-tail-as-a-quantity`, narrowing the class
  and read by property 6. The pre-existing `extractor-slices-a-number-out-of-a-dotted-token` was re-keyed
  onto the same constant, because the assembled lookbehind literal it used to name is now generated.
* **#95's scope corrected by measurement, not by drift:** the shipped rule sees **108** spelled-only
  claims rather than the 109 the entry recorded -- 45 in the report, 21 in the matrix, 18 in README, 14 in
  the rehearsal sheet, 10 in the reproducibility note. With the 28 classified in Phase 38, 80 remain.

## 2. Assumptions this rests on

* A hyphen joins, it does not separate: in this corpus a `-` before a digit is always inside a compound
  (`Level-1`, `order-four`, `0.2 %-1 %`), never a numeric claim preceded by punctuation such as a range.
  That is an empirical claim about six documents, and property 6 is what keeps it an assertion the corpus
  can refute rather than a belief.
* The phantom's two victims were *declarations*, not owners: removing a phantom removes a reason to
  explain a number, and the decorative check turns that into a red. The rival reading -- that the
  documents really do state those figures and should stay declared -- fails on the text, where `Level-1`
  names a validation tier and `best of 0.2 %-1 %` names a step-size range.
* #95's staged rollout is untouched: no document was opted into the spelled rule here, so the 80 remaining
  claims are still the next phases' work.

## 3. Files changed

| File | What moved |
|---|---|
| `tests/python/test_artifact_metadata.py` | `-` in `_CLAIM_EXCLUDE_CHARS` and the comment that measures it; `loosened()` as a shared helper that slices the trailing dash; property 3 re-pointed at it; property 6 added; the two phantom-absorbing declarations deleted; the spelled-generation comment corrected to what measurement supports |
| `scripts/mutation_plants.py` | one plant added, one re-keyed onto the constant, and the spelled-generation plant's rationale rewritten for the post-#100 failure shape |
| `docs/limitations.md` | #100 closed with (a) the two exemptions and (b) the control's own bug; #95's counts corrected to 108/80 |
| `docs/integrity_audit.md` | finding 80 |
| `docs/interview_defense.md` | the sweep annotation to 78/78, the state line to Phases 0–40 |
| `docs/project_scope.md` | the §9 row |

## 4. What the phase learned, including about its own first design

1. **An inventory that over-reads is silent, because over-reads are cheap.** A phantom claim can be
   *cited* (its paragraph names a frozen artifact) or declared, and either way no guard complains -- so the
   extractor has been reading `Level-1 identities` since Phase 27, and the only trace was two exemptions
   nobody would look at twice. Under-inclusion is what a register worries about; this is the symmetric
   failure, and it needed a check with teeth on the *exemption* side to surface.
2. **The control caught a bug in the control.** The first `loosened()` rebuilt the class by
   `.replace(character, "")`. For `-` that also deleted the range dash inside `A-Z`, producing a rule that
   matched a `2 cases` no sentence contains, and the property would have quietly widened its own
   expectation to fit. Naming the expected set (`{"1 identities", "1 % steps"}`) instead of counting it is
   what turned that into a red. The helper now slices the trailing dash, and the constant says why the dash
   lives last.
3. **Property 3 was only accidentally safe.** The dotted-token reconstruction had used the same
   replace-a-literal trick since Phase 35 and worked because `.` is not load-bearing inside `A-Z`. A check
   that passes by coincidence of punctuation is not a check; both properties now go through one helper.
4. **The spelled rule's own rationale moved.** Phase 38 recorded that dropping a table key would turn
   `twenty-two committed files` into a claim about *two* of them. With the hyphen excluded, the narrowed
   rule states *no* claim instead -- the same drift, quieter -- so the plant's rationale and property 5's
   assertion were rewritten in this commit rather than left describing a shape that can no longer occur.
5. **No measurement was re-frozen and no experiment was touched.** `run_benchmark_suite.py` was not run;
   `verify_evidence_manifest.py` reports the tree's bytes identical to the manifest, which is the point of
   not running a generator a phase has no reason to consult.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 181 files already formatted -- a walk of this directory, not a census (finding 62(d)) |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| Docs + harness lanes | `.venv/bin/python -m pytest tests/python/test_artifact_metadata.py tests/python/test_mutation_suite.py -q` | 70 passed (61 docs, 9 harness) |
| Anchor census | `test_every_declared_mutation_names_one_unique_anchor_and_a_guard_that_exists` | 78 declared plants, every anchor unique in its file, every guard present in its named file |
| Falsification, full sweep | recorded below from `build/mutation-sweep-40.log` | measured on the committed tree, in the row this file cannot carry about itself |
| CI on the pushed head | `gh api …/commits/<sha>/check-runs` and the job logs | recorded after the push, from the runner's own logs |

## 6. Numerical validation

No measurement is published. What moves and why:

* **78** -- the declared plant count, from the list. The rehearsal sheet's annotation carries it and the
  guard that compares the two is what keeps the prose from lagging.
* **108 / 80** -- the spelled-only claims in the corpus and the remainder after the pair classified in
  Phase 38, both re-measured through the shipped extractor rather than carried over from prose. The
  difference from the register's earlier 109/81 is one phantom shape the tightened rule no longer
  produces, and #95 now says so with its date on it.
* **Zero** artifacts re-frozen, **zero** benchmarks re-run, **unchanged** bands and their 22 committed
  readings: a regex change touches no measurement, and the manifest is the instrument that says so.

## 7. Remaining limitations

* **Over-inclusion was found once and is not systematically hunted.** The corpus is now known to contain
  three phantom readings under the digit rule and three more waiting under the spelled rule; nothing
  enumerates *future* phantoms except the decorative-exemption check, which sees them only when somebody
  writes an exemption for one.
* **#95's 80 claims across three documents stay unclassified**, and the sheet's group now carries the
  extra wrinkle that its own spelled counts include the shapes #100 refused.
* **#97, #98 and #99 stand as registered** -- the numeral table's ceiling, ownership credited by
  source-presence, and row citations checked for existence rather than meaning.
* **`cited` remains the tier where a wrong claim is cheapest to carry.** Both phantoms landed there or in
  `declared`; a phase that wants to tighten the inventory further has to make `cited` cost something, which
  is a design question this phase deliberately did not answer.

## 8. Technical debt registered here

| Entry | What it records | Why it is a limitation and not a defect |
|---|---|---|
| #100 (closed) | the hyphen exclusion, the six phantoms measured, the two exemptions that fell | fixed here; the entry keeps the shape of the failure on the record |
| #95 (corrected) | 108 spelled-only claims under the shipped rule, 80 remaining | the counts are measurements of a rule, so a rule change re-measures them |
| -- | no new entries opened by this phase | the residual in §7 is stated rather than numbered because it is the same mechanism as #100's, now fixed |

## 9. The gate

Closed when the 78-plant sweep runs on the committed tree with no line at any other status and the tree
clean afterwards; when CI's three jobs are read from their own logs on the pushed revision; when the
register, the audit, the scope table and the sheet agree on the plant count and the spelled totals, each
from its own producer; and when the tightened exclusion is shown to be load-bearing by a named control
rather than by the comment that claims it. A record checks the revision it names: the sweep and CI rows
land in the commit after this file, on the sha the runner built.
