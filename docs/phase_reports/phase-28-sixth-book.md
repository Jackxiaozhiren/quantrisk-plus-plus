# Phase 28 — the sixth crossing-radius book, chosen by a rule written before it was measured

Date: 2026-10-08. Post-tag work on `main`, after `v1.7.0` (`79d536a`). Objective item (5): the
radius chain's fifth-order measurement rests on five books, and `docs/analysis/fifth_order_crossing_map.md`
§3 left the licence to extend it — "the ratio is published per book so a sixth book can be checked
against it rather than retold".

## 1. Completed

`experiments/sixth_book_crossing_map/run.py`, registered as the nineteenth suite member, adds one book
to the cubic → quartic → quintic radius measurement, and the book is chosen by a rule fixed before any
new radius is read:

- candidates are maturity $\{0.25, 0.5, 1.0, 3.0\}$ years $\times$ volatility $\{0.15, 0.25, 0.45\}$
  $\times$ dividend yield $\{0.0, 0.05\}$ at spot 100.0, rate 0.03, strikes (80, 100, 120) and quantity
  5000 — 23 sets after removing the one a published book already uses;
- each candidate's order-five-to-four piece ratio is computed at Phase 20's own measure column, which
  costs six closed forms and a price and cannot see the outcome;
- examined in ascending ratio order, ties by iteration order, and the first candidate whose radius is
  *defined* — at least three swept columns carrying a priced crossing, Phase 18's precondition — is the
  sixth book.

Measured: `candidate T=3y sig=0.45 q=0.05`, ratio `0.0024490`, which is `0.043` of the published
minimum `0.056857` — a new low of an axis that spanned 0.0569 to 0.5876 across five books and now spans
240-fold. It qualified on the first examination (12 of 12 columns carried a priced crossing), so the
published scan is one row and nothing was rejected.

Its radii are `0.2 → 0.3 → 0.3`, a quintic factor of exactly `1.000`. And that `unchanged` is bounded by
the grid rather than earned: its **quartic** radius already sits at `0.3`, the widest move swept, so the
quintic could not rise on this ladder whatever the truncation does. What the book does say is inside the
artifact — worst column inside the quartic's own radius `0.000389` for the quintic against `0.000461`
for the quartic, a 16 % improvement the label cannot follow — and across six books the quintic now widens
2, leaves 4 unchanged, thins none, with 3 of the 6 at the grid edge.

The five earlier books return Phase 20's radii digit for digit, checked by the guard rather than
asserted, so "one more book" cannot quietly move the five it is compared against. The run also executes
`second_book_crossing_map`'s own equality control on the published ladder, which requires the shipped
machinery to agree with v1.5.0's and v1.6.0's bit for bit.

`docs/limitations.md` #88 records what this buys and what it does not: a rule that selects on the ratio
alone cannot tell in advance that the book it reaches will be a grid-edge case, and the alternative — a
precondition requiring a non-edge radius — is a statement about the outcome's shape and was not added
after the measurement.

## 2. Mathematical assumptions

Nothing new. The truncations, the multinomial weights `(1, 5, 10, 10, 5, 1)` with `1/120`, the
`v = σ√T` measure, the `0.005` tolerance, the delta ladder `±(0.02 … 0.30)` and the contiguous
paired-magnitude radius rule are all imported from `experiments/fifth_order_crossing_map/run.py`, which
imports `experiments/second_book_crossing_map/run.py`, which imports the two shipped releases' own files.
The only new mathematical statement is a selection score — the ratio of two piece magnitudes at the
measure column — which is used to order candidates and never enters a radius.

## 3. Files changed

| File | Change |
|---|---|
| `experiments/sixth_book_crossing_map/run.py` | new: the candidate grid, the ranking, the acceptance test, the six-book measurement, the control against Phase 20's artifact, and the payload including the published scan |
| `experiments/sixth_book_crossing_map/results/sixth_book_crossing_map.json` | the artifact: 6 book blocks with per-column verdicts, 6 fit blocks, the 1-row candidate scan, the control block, and a reproduction policy that exempts the ratio families by kind |
| `tests/python/test_sixth_book_crossing_map.py` | new: eight guards — the five prior radii re-checked against Phase 20, every radius re-computed from the rows beside it, the scan's order and acceptance audited, the new-low and ratio-quotient fields re-derived, the grid-bound flag re-derived, the headline counts re-counted, the declared conditioning families resolved, and the note's table parsed row by row against the artifact |
| `docs/analysis/sixth_book_crossing_map.md` | new note: the rule, the six-book table, the distances the sixth book does carry, and four refusals |
| `scripts/run_benchmark_suite.py` | nineteenth `Member`, with the grid-bound flag in its headline so a reader cannot see "unchanged" without it |
| `scripts/run_mutation_suite.py` | two plants: `sixth-book-note-quotes-a-radius-the-run-did-not-produce` and `sixth-book-grid-bound-claim-reads-a-narrower-grid` (43 → 45 declared defects) |
| `docs/limitations.md` | #88: a ratio-only rule can reach a grid-edge book, and the scan is published because the rule was written first |
| `paper/technical_report.tex` / `.pdf` | new `\paragraph{A sixth book, and what a rule can reach.}`, citing the run and the artifact |
| `README.md`, `docs/validation_matrix.md`, `docs/reproducibility.md`, `docs/interview_defense.md`, `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md` | members eighteen → nineteen, matrix rows twenty-five → twenty-six, experiments thirteen → fourteen plus the new table row, register 87 → 88 entries, suite 494 with oracles / 425 without |
| `docs/project_scope.md`, `docs/integrity_audit.md` | the Phase 28 row and finding 60 |

## 4. The rule, the grid, and the shape of an uninformative result

The interesting failure here is not a wrong number; it is a correct number that cannot mean much, and
the phase nearly shipped it without saying so.

Selecting on the ratio minimum is defensible because the ratio is a property of the truncation's
coefficients at one column, cheap to compute, and printed per book by the previous phase — but it is
orthogonal to whether the resulting book's radius can move. A 3-year, 45 %-volatility, 5 %-dividend book
has a wide crossing region: its cubic radius is already 0.2 and its quartic reaches the swept edge at
0.3. The lower the added term relative to its predecessor, the more history the map's error needs before
it crosses tolerance — so the rule that seeks the smallest fifth-order piece systematically finds books
whose radii sit at the boundary. Phase 20's largest-ratio book (`long-dated wide`, 0.588) was already at
the edge for the opposite reason; this phase produced the same silence from the other end of the axis.

The artifact says so in fields rather than prose: `sixth_book_quintic_radius_at_grid_edge` and
`sixth_book_radius_verdict_is_grid_bounded`, both re-derived by a guard from the radii and the ladder,
and both carried into the suite's headline block. The rule was not amended afterwards; #88 records that
a non-edge precondition would have chosen a different book, and that adding it now would be selecting on
the outcome.

The second design point is the note guard. `docs/analysis/sixth_book_crossing_map.md` prints one row per
book with radii, factor, grid-edge flag and ratio; the guard parses those rows and compares each cell
with the artifact, and it failed on first run because the note wrote `1.333` where the artifact holds
`1.3333333333333335`. Rather than loosen to a tolerance, the comparison is against the note's own
stated rounding (`round(value, 3)` and `round(value, 4)`), so a fourth decimal typed into prose is a
failure while re-rounding the artifact's value is not.

## 5. Exact test results

Each line is what the named command printed on this tree, not a restatement of an earlier run.

| Lane | Command | Its own words |
|---|---|---|
| Lint | `uv run ruff check .` | `All checks passed!` |
| Format | `uv run ruff format --check .` | `163 files already formatted` |
| Types | `uv run mypy python/quantrisk` | `Success: no issues found in 23 source files` |
| C++ | `uv run ctest --test-dir build/dev` | `100% tests passed out of 204`, 9.72 s |
| Suite | `uv run python scripts/run_benchmark_suite.py --require-all` | `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 288.2s total` |
| Python | `uv run pytest tests/python -q` | `2 failed, 492 passed in 120.66s` — the two failures are §9's known pre-commit pair, and both are green on the committed tree |

Three of the suite's own timings are evidence about the suite rather than about the engine: 761.5 s
while it contended with a second copy of itself, 367.9 s clean, 288.2 s clean. The middle one is the
reading §6 describes.

## 6. Numerical validation

Every figure in the artifact, the note and the documents was read from a producer, not derived by
arithmetic: the six books' radii and factors from the run, the ratio fields from `fits`, the distances
from the same block, the counts from the book rows. The prior five radii are compared with
`experiments/fifth_order_crossing_map/results/fifth_order_crossing_map.json` for exact equality; the
published ladder additionally goes through v1.5.0's and v1.6.0's own bit-identity control inside the
run. The 16 % improvement quoted in the note is `(1 - 0.000389 / 0.000461)` computed from the artifact's
own printed distances, and the 240-fold and `0.043` figures are the ratio fields divided by the
published span, which the guard recomputes.

One number in this section is not reproducible, and saying so is part of the validation. Registering
the experiment as the 19th suite member means every `--require-all` pass re-writes
`benchmarks/performance/results/monte_carlo_speed.json`, and that file's ratios are volatile by
declaration. This phase saw three readings of it: a contended pass at `4.007×` / `0.3588×`, a clean
pass at `8.378×` / `0.5656×`, and the clean pass that is committed at `8.877×` / `0.4597×`. The first
was restored from a pre-run copy rather than committed; the second was overwritten by the third, four
minutes later, with no contention in either. What survives is one artifact and the twenty-one
committed readings around it, so the documents quote `8.88×` and `0.460×` and the band `7.77×`–`8.88×`
/ `0.42×`–`0.51×` — 14.2% and 20.8% spreads — and `docs/reproducibility.md` prints the command that
recomputes those edges from `git log`. The sixth book's own numbers are not in that class: the ratio
field came back bit-identical (`0.002449039099104238`) across every re-run of the experiment, because
it is a closed form, not a timing.

## 7. Remaining limitations

- #88: the sixth book's radius verdict is bounded by the swept grid, and a rule that selects on the
  ratio alone cannot know that in advance. Widening the ladder would answer it, and would also change
  the scale every published radius in this chain is quoted on — a different experiment.
- A radius is still a grid label (#81), six books are still not a family, and the ratio axis is still
  not a mechanism: the three lowest-ratio books read `0.0024 → 1.000`, `0.0569 → 1.500`,
  `0.0603 → 1.000`.
- Phase 27's inventory guard reads numbers that stand as their own token followed by a countable noun.
  This phase added the nouns its own prose needed (`radii`, `radius`, `moves`, `factors`, `orders`,
  `edges`, `candidates`) and classified what that surfaced; the list remains the guard's scope, stated
  rather than implied.
- The note's book rows are compared at the note's rounding. A note that rounded to one decimal would
  pass with a coarser claim; the guard checks equality against that rounding, not the rounding itself.
- The committed bands describe *committed* runs of one script on one machine. The intermediate
  `8.378×` / `0.5656×` reading this phase measured, discarded, and then had to un-quote from six
  documents is not recoverable from the repository at all except from §6 of this report and the
  correction paragraphs in the two release notes — no artifact carries it. A volatile reading that is
  not committed leaves no evidence behind, which is the honest limit of what `git log` can restore.

## 8. Technical debt

Registered here, not scheduled:

1. A ladder sweep that reaches beyond the widest radius any candidate can produce — the precondition
   #88's book needed — is a redesign of the radius chain's published scale, not an increment.
2. Phase 27's inventory has not been extended to `README.md` and `docs/reproducibility.md`, which restate
   the same producers in their own phrasings; this phase widened the noun list for the report only.
3. The Heston probes still have no frozen artifact (#86).
4. Nothing tells an author *which* of several clean readings to sync the documents to. The rule is by
   convention — the last producer run before the commit, and no run after it — and the phase had to
   rediscover it when a second clean run overwrote the first. A guard that compares the artifact's
   `generated_at_utc` against the commit time, or a suite flag that refreshes every member except the
   volatile benchmark, would turn the convention into a mechanism.

## 9. The gate

Recorded as the tools report it, in the order the gates were run.

Done on the working tree, before the commit:

- The lanes in §5, with two exceptions that are unsatisfiable *by construction* before the commit:
  `test_the_documented_speedup_ranges_match_the_committed_history` (the pinned `8.88×` edge cannot
  equal the min/max over committed history until the artifact that produced it is committed) and
  `test_the_manifest_hashes_every_experiment_results_directory` (the freeze cannot hash
  `experiments/sixth_book_crossing_map/results` before that directory exists in a commit). Both are
  named here rather than worked around; the band guard's scope is deliberately git history, because
  the claim it polices is about what has been published.
- `report-cites-a-run-date-the-artifact-does-not-carry` run live: the caption's date was replaced by
  the date the previous freeze carried, the guard named the timestamp the artifact actually holds, the
  file was restored to `7bb5733e…` (verified by hash) and the guard went green again. The vacuity
  guard now carries that date as its own negative control.
- `readme-quotes-a-stale-speedup` re-keyed by this phase's own figure sync, and
  `docs-command-comment-counts-superseded-plants` re-keyed from `45/45` to `47/47` — the second
  re-keying was forced by the anchor guard going red *on my own count sync*, which is finding 49's
  failure mode recurring exactly as documented.

Pending, and not quoted until each tool has printed it: the 47-plant sweep on the committed tree, and
CI's three jobs on the pushed head.

Two things the committed tree itself reported, in order:

- Re-running the whole lane on the commit (`uv run pytest tests/python -q`) found
  `test_the_manifest_hashes_every_experiment_results_directory` still red after a rebuild, because the
  manifest builder's experiment inventory is a hand-maintained tuple that no new experiment knows to
  append itself to. Fixed in the inventory (`experiments/sixth_book_crossing_map/results` joins the
  crossing-map family), and the freeze re-run covers 95 artifacts and 7,238,399 bytes — figures the
  report's manifest sentence then had to be synced to, with the PDF rebuilt in the same commit.
- That sync disarmed one of its own plants. `report-counts-a-manifest-the-freeze-does-not-have` keyed
  its anchor to `94 artifacts, 7{,}145{,}018 bytes`, so editing the report to the true totals left the
  anchor occurring zero times, and
  `test_every_declared_mutation_names_one_unique_anchor_and_a_guard_that_exists` went red on the
  committed tree: `1 failed, 493 passed`. The plant is re-keyed to the new totals, with the count in
  its replacement still wrong so it still proves the guard can fail. This is finding 49's third
  occurrence — prose edits and plant anchors are the same file read two ways — and it is worth noting
  that the harness caught it rather than passing silently: the disarm is only invisible if nobody runs
  the anchor self-test, and the sweep runs it first.

- `uv run pytest tests/python -q` on the committed tree `8779e6e`: `494 passed in 119.85s`, exit 0.
- `uv run python scripts/run_mutation_suite.py` on `8779e6e`: **`46/47 planted defects were rejected by
  their guard`**, exit 1. The escape was `readme-quotes-a-stale-speedup`, and it was not a broken plant:
  the substitution landed and the bytes changed, but the README prints `8.88×` twice — as the point
  figure and as the band's upper edge, because this phase's reading is the widest in the artifact's
  history — so the guard was green on the occurrence the plant never touched. Finding 60(f). The claim
  is now a phrase (`` `8.88×` in the artifact now in the tree ``) rather than a digit, and the plant is
  being re-run against that.
