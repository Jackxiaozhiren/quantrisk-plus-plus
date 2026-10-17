# Phase 49 — the claim rule is measured on a sample it did not choose (#102 closes)

Date: 2026-10-17. Debt item: `docs/limitations.md` #102, amended closed; #101 narrowed, not closed.

## 1. Completed

* **`test_the_claim_rules_recall_and_precision_are_estimated_on_a_sample`.** The frame is every unit in
  the five inventoried texts longer than 25 characters that contains a number token -- **1,016** of them
  today -- and the sample is every 42nd in document order: **25 units**, whose frame indices
  (`_CLAIM_SAMPLE_INDICES`) are frozen so a reworded sentence moves the sample loudly rather than
  scoring stale gold.
* **The estimate.** Reading those 25 units yields **11 countable quantities**; the shipped extractor
  finds **1**. Sampled recall **1/11**, with the 10 misses named in `_CLAIM_SAMPLE_MISSES`.
* **What is not claimed.** The sample produced exactly one extraction, so the denominator behind
  precision is 1 and an empty phantom list proves nothing. #101's declaration half stays open for that
  reason, and the guard says so in its own docstring rather than in prose beside the code.
* **3 plants (116 -> 119)**: the frame floor raised until the frame stops covering the documents; the
  single gold hit deleted, which turns it into a phantom; and the sampling step moved, which the frozen
  indices refuse to accept silently.
* **The cascade**: sweep annotation 116/116 -> 119/119, test pair 524/455 -> 525/456 in eleven spellings
  and four plant anchors, `forty-nine report files` -> `fifty`, and the report re-typeset.

## 2. Assumptions this rests on

* A countable quantity is a phrase asserting how many things there are, written as the unit writes it
  ("12/12 confidence intervals", "116 of 120"). Durations ("2 min") count; multipliers ("100x the
  paths"), tolerances ("1e-12 relative"), versions ("interpreter 3.12"), line ranges
  (`test_monte_carlo.cpp:142-168`), limitation references ("(36)") and pronouns ("the one below it") do
  not, and 13 of the 25 units are in the sample precisely because the frame took them, not because they
  were picked.
* The sample is systematic, not random: with a fixed frame order, every 42nd unit is reproducible from
  the documents, which is what lets a later phase re-derive it rather than trust a stored list.
* 25 units is a small n. The number is quoted with its n attached in #102, and no confidence interval is
  claimed for it.

## 3. Files changed

`tests/python/test_artifact_metadata.py` (the guard, `_claim_sample`, `_CLAIM_SAMPLE_NUMBER`,
`_CLAIM_SAMPLE_GOLD`, the frozen index and miss lists), `scripts/mutation_plants.py` (3 plants and the
anchors that track the counts), `docs/limitations.md` (#102 amended closed, and #63's pair),
`docs/reproducibility.md`, `docs/interview_defense.md`, `docs/project_scope.md` §9,
`paper/technical_report.tex` with its rebuilt PDF and `build.json`, and this report.

## 4. What the phase learned, including about its own first design

* **The number this phase produced is an indictment of the instrument, not of the documents.** Recall
  1/11 says the claim inventory has been bounded by `_REPORT_NOUNS` all along: everything #95 counted as
  "66 remaining" and every phase's "all claims classified" was a count over what the noun list could see.
  The fix is not to widen the list until recall reads well -- that trades one blind list for a longer one
  nobody scored -- but to keep quoting the pair (found, gold) wherever the inventory is cited.
* **I wrote a cross-reference to an entry that says something else.** The first draft of #102's
  amendment cited "#48's ceiling doctrine"; #48 is about rank stability on one fixture. Caught by
  grepping the entry I was citing, which is the rule the register already has and which I had just broken
  in the sentence meant to describe it. The citation is gone rather than renumbered, because the point it
  was borrowed for is already made by the numbers beside it.
* **A sample is only unbiased if nothing chose it.** My first pass at the frame matched spelled numerals
  inside words ("one" in "clone") because the alternation lacked a leading boundary; the frame size
  changed when fixed, and the indices had to be re-drawn. A boundary bug in the sampler is a selection
  bias in the result, which is the failure this phase exists to avoid.
* **The three plants are three different lies.** A frame that quietly stops covering the documents, gold
  that silently re-labels the only hit as a phantom, and a step that redraws the sample under stale
  annotations. Only the third is visible in a diff, and it is the one a careless later phase would commit.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 193 files already formatted on this tree; the record commit quotes the `git archive` export (finding 81's rule) |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --preset dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | pending |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 456 tests collected |
| Python | `.venv/bin/python -m pytest -q` | pending |
| Falsification, full sweep | recorded in the next commit, on the sha it ran on | pending |
| CI on the pushed head | recorded in the next commit, from the runner's own logs | pending |

## 6. Numerical validation

* **1,016** frame units, **25** sampled, **11** gold quantities, **1** found, **10** named misses,
  **0** phantoms on a denominator of 1 -- every one derived by the guard from the documents and the rule.
* **119** declared plants; **103** register entries, unchanged (#102 amended in place).
* **525 / 456** -- this environment's pair, from their own producers.

## 7. Remaining limitations

* **#101 stays open**: precision still has no usable sample (one extraction), and a declaration remains a
  hand-written reason whose number nothing compares with a producer.
* **The sample's n is 25 units / 11 quantities.** Enough to say the rule misses most of what the frame
  holds, not enough to put an interval on it.
* **#103's static half** and **#99's eight pointer-shaped citations** are unchanged.

## 8. Technical debt registered here

| Entry | What it records | Why it is a limitation and not a defect |
|---|---|---|
| #102 (amended closed) | the instrument and the sampled 1/11 with its frame, step and n named | closing it costs nothing the entry did not ask for; the residue is named in §7 |
| -- | no entry opened by this phase | the 10 misses are the noun list's boundary, which #102 now carries as its own number |

## 9. The gate

Closed when the sweep runs `119/119` on the committed tree with nothing left dirty; when each of the
three plants is shown to redden the sampling guard rather than any other; when CI's three jobs are read
from their own logs on the pushed revision; when the register, the audit, the scope table and the sheet
agree on the plant count and the test pair from their own producers; and when #102's entry states 1/11
with the frame size and the sample size attached, because the number without its n is the defect the
entry exists to prevent. A record checks the revision it names: the sweep and CI rows land in the commit
after this file, on the sha the runner built.
