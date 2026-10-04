# Phase 21 — order five measured: two books widen, three do not, and the mechanism stays dead

Phase 20 shipped the six mixed fifth partials and explicitly did not use them. This phase uses them:
`experiments/fifth_order_crossing_map/` asks whether the crossing radius widens *again* when the
quintic term joins the cubic and quartic truncations, on the same five books, under the same rule. It
also closes the last substantive technical-debt item before the release, and it does so with a result
that is partly negative and partly unresolvable rather than a clean win.

## 1. Completed

- **The experiment.** `experiments/fifth_order_crossing_map/run.py` adds `(1/120)` times the fifth
  directional derivative to the column truncation and finds the contiguous paired-magnitude radius for
  cubic, quartic and quintic on five books. It publishes 1 JSON, 1 radii CSV and 5 per-column CSVs.
- **Nothing about the rule was re-typed.** The books, the delta grid, the `0.005` tolerance, the root
  finder, the radius rule and the worst-distance helper are imported from
  `experiments/second_book_crossing_map/run.py`, which itself imports v1.5.0's and v1.6.0's files. That
  import chain also means the shipped equality gate (`verify_control`) runs inside this experiment: the
  cubic and quartic coefficients, both lower truncations and the engine P&L over 30 joint moves must be
  bit-identical to the two releases' before anything is written.
- **Four controls, all executed:** machinery equality (above); the published book's radii returning at
  0.05 and 0.15; the multinomial contraction `(1,5,10,10,5,1)` and the `1/120` checked against five
  nested differences of the *revalued book*, which contains no partial at all; and the radius rule
  staying the paired contiguous one, which Phase 18's plant still proves from the other side.
- **The result.** Order five widens the radius on 2 of 5 books (published ladder `0.15 -> 0.20`, factor
  1.33 against its own cubic-to-quartic 3.00; deep out of the money `0.20 -> 0.30`, factor 1.50) and
  leaves it unchanged on 3. Inside the quartic's radius the quintic is the closest of the three orders
  on 5 of 5. Two of the three "unchanged" books sit at the swept grid edge and are flagged as
  unresolvable rather than counted as negative results.
- **Registered and frozen as evidence:** suite member 18 (`18/18 executed and passed`), the manifest
  directory declared and re-frozen at 94 artifacts, `docs/analysis/fifth_order_crossing_map.md`,
  validation-matrix row 22, limitation #83, and the counts every document repeats (13 experiments,
  25 matrix rows, 83 limitations, 477 Python tests, 18 suite members, the new performance figures).
- **Falsification:** 4 new plants (34 declared) — the own-radius refusal, the producer's book sums,
  a published sum that is not the core's, and the note's headline count. The second of those was aimed
  wrong at first and the sweep said so; see §4(e).

## 2. Mathematical assumptions

The added term is the order-five Taylor contribution along the joint column move `(h, k)`, `h` the
absolute spot displacement and `k` the volatility displacement:

```text
quintic piece = (1/120) * sum_j C(5,j) V_(5-j, j) h^(5-j) k^j
```

with the six `V_(a,b)` read from `pricing.black_scholes_mixed_fifth_derivatives` and summed over the
book at the base market, then scaled by the position quantity. The cubic and quartic truncations are the
shipped ones, so the three orders compose: `quintic_error = quartic_error + quintic piece`, and
`quart_error = cubic_error + quartic piece` is what v1.6.0 published.

Assumptions inherited unchanged from that chain, and the reason the result is a grid label: the map's
column error is measured against a *revaluation of the same Black–Scholes book*, so the only model
error is the truncation of the expansion, not the model's fit to a market; the crossing is a sign change
of a subtraction of two book values near 1e5, which is why the distances are declared
`conditioning_limited` while the counts and radii that decide the claim are gated by value.

## 3. Files changed

| File | Change |
|---|---|
| `experiments/fifth_order_crossing_map/run.py` | new experiment: fifth-order book sums, quintic piece, three-order radius, four controls, refusals, reproduction policy |
| `experiments/fifth_order_crossing_map/results/` | 7 artifacts (1 JSON, 1 radii CSV, 5 column CSVs) |
| `docs/analysis/fifth_order_crossing_map.md` | new note: the table, the two-order comparison, the refuted mechanism, the refusal's own bug |
| `tests/python/test_fifth_order_crossing_map.py` | new, 12 tests: shipped gate, core sums, fifteen radii re-derived, signed-pair plant, both refusal directions, contraction on other rays, headline re-counts, prose pins, family paths, note figures, temp-tree reproduction |
| `scripts/run_benchmark_suite.py` | member 18 registered with its headline paths |
| `scripts/build_evidence_manifest.py` | the new results directory declared |
| `scripts/run_mutation_suite.py` | 4 plants added (34 declared); 8 anchors re-keyed to the figures this phase moved |
| `docs/limitations.md` | item 83 |
| `docs/validation_matrix.md` | row 22, count 24 → 25 |
| `README.md` | experiment row and count, suite breakdown, matrix and limitation counts, performance figures |
| `docs/interview_defense.md`, `docs/reproducibility.md`, `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md`, `.github/workflows/ci.yml` | the counts and digits those documents repeat |
| `paper/technical_report.tex`, `paper/technical_report.pdf` | headline counts, the rebuilt speed table |
| `benchmarks/performance/results/monte_carlo_speed.json`, `benchmarks/suite/results/*` | regenerated by the authoritative `--require-all` run |

## 4. The three ways this measurement nearly lied

**(a) A refusal that judged a radius by the wrong range.** The run refuses to publish a radius whose
widest in-range distance exceeds the tolerance that defines it. The first version read each order's
worst distance from the *quartic's* range, and it immediately rejected the published ladder's cubic
radius of 0.05 because a column at `0.15` sat `1.89e-02` away — a column that radius never claimed to
cover. The bug was found by the gate firing on a result that was correct, which is the only way this
class announces itself: a range conflation in a validator rejects good data and accepts incoherent data,
so it is invisible until it is aimed at something right. `check()` now reads each order against its own
radius, and the test pins both directions — the loose column outside must not reject, the same numbers
inside must.

**(b) Bulk re-wrapping words into each other.** Reformatting the producer to satisfy the line-length rule
glued words together *inside string literals* — `"five booksalready refutedthe mechanism"` — and the JSON
still parsed, still printed, and still satisfied every figure guard, because the guards check digits and
these were sentences. Two of them reached the artifact before I read the payload back. The durable
response is `test_the_prose_of_the_artifact_says_what_it_means`, which pins the whole sentences the run
writes about its own procedure rather than trusting that a paragraph is a paragraph.

**(c) Anchors that my own doc sync silently disarmed.** Eight plants key on figures this phase moved.
Re-keying them produced two pairs where `anchor == replacement` — the matrix-rows and suite-members
plants would have "planted" a defect that was the correct text, so the sweep would have reported
`33/33 caught` while three of the plants proved nothing. `tests/python/test_mutation_suite.py` refuses
an identical pair, which is the mechanism that caught it; the same test caught two anchors that no longer
existed at all. A falsification harness needs its *list* policed as strictly as its targets.

**(e) A plant aimed at a wire the mutation never touches.** `fifth-order-sums-drop-the-book-quantity`
named the sums test as its guard, and the sweep reported it `guard-stayed-green`: that test compares
the artifact against the bindings and never calls the producer's helper, on purpose, so no edit to
the producer can reach it. The plant now names the reproduction test, which does consume the helper,
and the sums test got the plant it can actually react to -- a digit changed in the published sums.
Audit finding 53 is the general shape: a guard's power is a property of the path from mutation to
assertion, and only running the list discovers whether that path exists.

**(d) One more, in the other direction.** `kind="tree"` in this harness means "write a file that must not
exist" (that is how the two manifest probes work). I declared two producer edits as `tree`, and the
guard rightly refused to let the sweep overwrite a tracked file. Both are `prose` now.

## 5. Exact test results

```text
uv run python scripts/run_benchmark_suite.py --require-all   18/18 executed and passed, 0 aggregated,
                                                             0 failed, 0 skipped, 174.9s total
uv run pytest tests/python -q                                477 passed
uv run quantrisk validate                                    7/7 checks passed
uv run ctest --preset dev                                    100% tests passed out of 204
uv run ruff check .                                          All checks passed!
uv run ruff format --check .                                 147 files already formatted
uv run mypy python/quantrisk                                 Success: no issues found in 23 source files
uv run python scripts/run_mutation_suite.py --list           34 plants declared
uv run python scripts/build_evidence_manifest.py + verify    94 OK / 0 CHANGED / 0 VOLATILE / 0 MISSING / 0 unlisted
uv run latexmk -pdf paper/technical_report.tex               44 pages, 1003152 bytes
                                                            (1003090 before this phase's counts moved)
```

The measured result, from the artifact rather than from memory:

```text
published ladder        v=0.141  cubic 0.05  quartic 0.15  quintic 0.20  x1.33   10/12 columns
long-dated wide         v=0.495  cubic 0.10  quartic 0.30  quintic 0.30  x1.00   11/12   (at grid edge)
short-dated tight       v=0.047  cubic 0.02  quartic 0.05  quintic 0.05  x1.00    6/12
deep out of the money   v=0.318  cubic 0.15  quartic 0.20  quintic 0.30  x1.50   12/12   (at grid edge)
in the money            v=0.141  cubic 0.05  quartic 0.10  quintic 0.10  x1.00    9/12
closer inside the quartic radius, quintic smallest: 5 of 5
contraction vs nested differences of the revaluation, widest rung: 1e-05, 8e-04, 3e-06, 5e-05, 6e-04
order-five / order-four piece at the measure column: 0.057 to 0.588
```

## 6. Numerical validation

- **Against the releases themselves.** `verify_control` executed: the ten third- and fourth-order
  coefficients, both truncations and the engine P&L over 30 joint moves are exactly equal to v1.5.0's
  and v1.6.0's on the published book, and the published radii come back at 0.05 and 0.15. An added order
  that moved the baseline would have stopped the run here.
- **Fifteen radii recomputed.** Every book at every order re-derives from the printed per-column
  distances under the magnitude-grouped rule, and every stored verdict flag re-derives from the distance
  beside it. The headline counts re-derive from the rows.
- **The contraction is not self-certifying.** Five rays in the artifact, each at three rungs with every
  rung published; the test re-derives the same identity on four rays the producer never evaluates, and
  the weights `(1,5,10,10,5,1)` are pinned by the two pure-end rays alone.
- **The sums come from the core.** The test recomputes the six published book sums from
  `black_scholes_mixed_fifth_derivatives` and requires bit equality with the artifact.
- **Reproduction.** Re-running the experiment in a temporary tree, with the four files of its import
  chain, produces an artifact that differs from the committed one only in the declared
  `conditioning_limited` paths.

## 7. Remaining limitations

Limitation #83 in full. The short version: a radius is a grid label, and the widened region contains a
*looser* worst column than the narrower one did (the published ladder's quintic radius holds a column at
`3.81e-03` where its quartic radius held `1.62e-03`); two books are unresolvable because they sit at the
swept edge; the mechanism the set was built to test is refuted a second time rather than replaced; the
amount of the map's error is untouched (16.2 % off at published scale after the quartic, and order five
is not evaluated against that figure); and no second implementation prices a fifth-order column, so the
whole chain remains self-consistency of a truncation against a revaluation of the same book.

## 8. Technical debt

1. **`v1.7.0` and the post-tag accounting.** The only objective item still open. The release has to state
   the radius per book rather than as one ladder's pair, carry the whole-surface `[[nodiscard]]` counts
   the way #80 does, say that order five is available with no attached amount claim, and be cut on the
   revision CI actually verified, with assets built from `git archive <tag>` and hashed both ways.
2. **A sixth book.** Five books is not a family and the widening factors (1.33, 1.50, 1.00, 1.00, 1.00)
   have no distribution behind them. The artifact publishes the per-column distances, so a new book can
   be checked against them rather than retold — which is what §4 of the five-book note has said since
   Phase 18, now at a second order.
3. **The grid edge is a real limit on this design.** Two of five books cannot show a widening at all
   because the swept `|delta|` stops at 0.30. Extending the grid is not free: the priced crossings get
   sparser and the tolerance was set on the published ladder's own scale. Worth recording as a design
   constraint of the next measurement, not an oversight of this one.
4. **`sympy` is still not in CI**, so the Phase 20 derivation script remains a hand run (its own debt
   item 2), and the assertion/case totals (`548,368` in `203` cases) are still prose with no owner.

## 9. Gate

**Not a release.** Version stays `1.6.0`; the tag stays `b4e4bea`. The artifacts this phase regenerated
are the performance JSON and the three suite roll-up files, all produced by one authoritative
`--require-all` run rather than by `--no-run` aggregation, and the prose was synced last, in the same
commit as the plant re-keys, as `CONTRIBUTING.md` §4 requires.

The falsification sweep refuses a dirty tree, so its verdict is a claim about a revision. It runs on the
commit this report ships in; the paragraph recording its own line is appended in the commit after that,
which is how Phases 17, 18, 19 and 20 all recorded it.
