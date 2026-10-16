# Phase 47 — a sentence that says what a row is must say it in that row's words (#99 closes)

Date: 2026-10-16. Debt item: `docs/limitations.md` #99, opened by Phase 38, closed here.

## 1. Completed

* **`test_every_claim_about_a_validation_matrix_row_describes_that_row`.** A citation is *claiming* when
  it puts a descriptor in apposition to the number (`Row 6, the Heston comparison,`), predicates on it
  (`row 16 is validated by`), or possesses it (`row 22's books`). Each such citation must be registered,
  and every content word of the registered phrase must appear in the cited row's own cells.
* **`_ROW_CLAIMS`, the registry**: 9 entries over the 5 documents the inventory reads plus the report --
  4 in `README.md`, 5 in `docs/validation_matrix.md`. Both directions are checked: an entry whose phrase
  no citation carries is stale, and a citation no entry describes is unclassified, so the list can
  neither fall behind the prose nor run ahead of it.
* **Morphology folded on both sides, not one.** `publishes` against a cell that says `published`,
  `identities` against `identity`: the fold (`ies`→`y`, `-es`, `-s`, `-ed`) is applied to the citation
  *and* to the row, which is what makes it a comparison rather than a spelling test. It is four lines
  and a comment, not a stemmer.
* **3 plants (110 -> 113)**: a citation moved to an adjacent row that exists -- the #99 defect itself,
  which every existence check passes; a registry entry deleted; and the claim shape blinded so the
  guard would compare nothing, which its own denominator assertion refuses.
* **The cascade the phase owes**: the sweep annotation 110/110 -> 113/113, the test pair 522/453 ->
  523/454 in eight spellings and four plant anchors, the artifact index `forty-seven report files` ->
  `forty-eight`, and the report re-typeset.

## 2. Assumptions this rests on

* A descriptor before the number ("the same column truncations as row 19") is not this shape and is out
  of scope: deciding whether a comparison holds needs the *comparing* row's cells too, and which row is
  doing the comparing is not recoverable from a window. #99's amendment records that boundary instead of
  claiming the rule is total.
* The registry's phrases are the curator's choice of which words carry the claim. What is not a choice:
  that the phrase must occur inside its own citation, and that its words must occur in the cited row.
* Rows are keyed by the label the table gives them, including the lettered sub-rows (`9b`, `4b`), whose
  names are not bolded -- the parse takes the label cell, not a bold span.

## 3. Files changed

`tests/python/test_artifact_metadata.py` (the guard, `_CLAIMING_ROW`, `_CITATION_STOPWORDS`,
`_citation_terms`, `_matrix_row_cells`, `_ROW_CLAIMS`), `scripts/mutation_plants.py` (3 plants and the
anchors that track the pair and the sweep count), `README.md`, `docs/reproducibility.md`,
`docs/interview_defense.md`, `docs/limitations.md` (#99 amended closed, and #63's pair),
`docs/project_scope.md` §9, `docs/integrity_audit.md` (finding 87), and `paper/technical_report.tex`
with its rebuilt PDF and `build.json`.

## 4. What the phase learned, including about its own first design

* **The obvious instrument was measured before it was shipped, and it failed.** The first design was a
  token-overlap rule: give each row the tokens of its own bolded name, keep those unique to one row, and
  flag a citation that carries a token unique to a different row while carrying none unique to its own.
  Run over the inventoried texts it produced **6 flags on the 9 citations that carried any unique token**
  -- all false: the matrix's prose legitimately mentions a neighbour's concepts (`the same truncations as
  row 19`), and the lettered sub-row `9b` is not even parsed because its name is not bolded. Meanwhile
  the *correct* README citation for row 15 came back vacuous, because `bound`/`truncation` belong to
  several rows and so are not unique to any. The refused design is recorded with its number, since
  "a gate that cries wolf" is a decision, not an omission.
* **Existence checks could not have seen this, and saying so is the entry's point.** Row 14 exists, is
  numbered once, and is contiguous with its neighbours; #99's sentence described row 15. The three
  guards that policed the matrix's numbering all stayed green while the front page pointed a reader at
  the wrong row, which is the shape of every finding in this file: a check that validates the *form* of
  a pointer is not a check on its content.
* **A registry is only safe when both directions fail.** Coverage alone (every citation registered)
  would let the list grow stale the moment a sentence was reworded, and staleness alone would let a new
  citation slip past unregistered. Asserting containment in both directions is what makes the
  hand-written part -- which words carry the claim -- into something that can be wrong.
* **My own first cut of the guard was wrong in the ordinary way.** The staleness comparison unpacked the
  citation triple as `cited, _, window` and then tested `cited == (document, row)`, so a string was
  compared to a tuple, no citation ever matched, and all nine entries were reported dead. The failure
  was loud and the cause was three characters -- which is the argument for writing the guard against an
  empty registry first: it enumerated the nine real citations before it could pretend to agree with
  anything.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 191 files already formatted on this tree; the record commit quotes the `git archive` export (finding 81's rule) |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --preset dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | Evidence is intact -- the report bundle moved, no artifact re-frozen |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 454 tests collected |
| Python | `.venv/bin/python -m pytest -q` | 523 passed |
| Falsification, full sweep | recorded in the next commit, on the sha it ran on | pending |
| CI on the pushed head | recorded in the next commit, from the runner's own logs | pending |

## 6. Numerical validation

* **113** declared plants, from the harness's own list; **9** registered row claims; **17** citations
  found in the inventoried texts, of which 9 are claim-shaped.
* **103** register entries, unchanged: #99 was already in the file and is amended closed in place.
* **523 / 454** -- this environment's pair, each from its own producer.

## 7. Remaining limitations

* **The comparative-before-the-number shape is unpoliced** and now carries its own boundary in #99's
  amendment: 8 of the 17 citations are pointers or comparisons, and a wrong number in one of those would
  still pass. Deciding them means reading the comparing row as well, which is a larger instrument than
  this phase's registry.
* **The phrase granularity is curated.** A citation that describes its row only in words the table never
  uses -- a synonym, a paraphrase -- cannot be registered without editing the table's prose, which is
  the honest direction for the disagreement to surface but is still a human decision per entry.
* **#101, #102 and #103 stand**: the spelled reader's precision on prose, the missing recall instrument
  for the claim rule, and the plant registry's unproven `guard` field.

## 8. Technical debt registered here

| Entry | What it records | Why it is a limitation and not a defect |
|---|---|---|
| #99 (amended closed) | the citation class policed existence only; the registry now polices meaning for the claim shape, and the comparative shape is named as out of scope | the residual is a scope boundary with a count, not a silently unfixed case |
| finding 87 | the token-overlap design measured at 6 false flags on 9 citations, and the un-bolded `9b` label its parser missed | recorded because "run the plausible instrument and count its false alarms" is the step that generalises |
| -- | no new entry opened by this phase | the residuals in §7 are #101/#102/#103's, already registered |

## 9. The gate

Closed when the sweep runs `113/113` on the committed tree with the tree clean afterwards; when the
moved-citation plant is shown to redden the new guard while the numbering guards stay green -- that
pair is #99's claim in one sentence, and the plant is the half that proves it; when CI's three jobs are
read from their own logs on the pushed revision; when the plant count, the register size and the test
pair each come from their own producer in every document that quotes them; and when #99's entry states
the measured 6-of-9 for the refused design and names the 8 citations that remain out of scope. A record
checks the revision it names: the sweep and CI rows land in the commit after this file, on the sha the
runner built.
