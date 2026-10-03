# Phase 18 — does the fourth-order crossing radius belong to the model, or to the book?

Date: 2026-10-03. Predecessor: Phase 17 (`phase-17-surface-coverage.md`), whose §9 left this as the next
question; Phase 16's own limitation (#79) is the sentence under test. Repository version is unchanged
(`1.6.0`), the tag still names `b4e4bea`, and nothing here is claimed to be inside that release — the
release note carries a dated correction instead (§5 of this report).

## 1. Completed

1. **A re-derived pipeline proved bit-identical to the shipped machinery before any new book was
   measured.** `experiments/second_book_crossing_map/run.py` cannot import the two published
   experiments' books — they keep theirs in module constants — so it re-derives the third- and
   fourth-order book sums from the core's closed forms, both column truncations, and the map P&L
   through `quantrisk.stress.run_scenario`. The run raises unless all ten coefficients, both truncations
   and the engine P&L over 30 joint moves are bit-equal to `restrike_gamma_map` and
   `fourth_order_crossing_map` on the published ladder, and unless that ladder's two radii recompute to
   exactly 0.05 and 0.15. The four largest differences are published in `control` and are all `0e+00`.
2. **The measurement: five books, twelve `delta` columns each.** Books were fixed before any of them was
   run, chosen for what each does to the terms (§2). Direction transfers; magnitude does not.
3. **Two radius-definition defects found and fixed**, the second of which had made the artifact
   contradict itself (§4), with the producer gate and the re-derivation test that now refuse that shape.
4. **Suite member 17 registered** (`second_book_crossing_map`), headline fields read from the artifact by
   key path, and the whole suite re-run with `--require-all` over all 17 members.
5. **Ten tests** in `tests/python/test_second_book_crossing_map.py`, including a determinism test that
   re-runs the experiment in a temporary tree and compares it to the committed artifact under the
   family-declared reproduction policy introduced in Phase 16.
6. **Documents the result moves:** `docs/analysis/second_book_crossing_map.md` (new note, owned by the
   figure test), `docs/validation_matrix.md` row 20, `docs/limitations.md` #81 and the pointed clause in
   #79, `docs/integrity_audit.md` finding 46 and the Phase 18 addendum, `docs/interview_defense.md` Q28
   plus its citation row, `docs/release_notes_v1.6.0.md` §"Correction, 2026-10-03", README's experiment
   table, and `paper/technical_report.tex` §"Does the radius belong to the model or to the book?".
7. **Three prose counts that had no owner got one.** The report's headline paragraph said fourteen
   suite members while the registry had sixteen, and 411/342 pytest tests where the tree gives 447/378;
   README said "eight experiments" above a table of nine rows, with twelve scripts on disk. Two existing
   guards now read the report, and a new guard
   (`test_the_readme_experiment_count_agrees_with_the_experiments_on_disk`) reads the tree.
8. **A fourth ownerless list turned out to be an evidence hole** (finding 47).
   `scripts/build_evidence_manifest.py` hashes the directories it *names*, and this phase's new
   `experiments/second_book_crossing_map/results/` was not among them: the verifier read back
   `83 OK / 0 MISSING / 0 on disk but not in the manifest`, three true statements about the list it walks
   and blind to the directory that is not in it. The directory is now declared, the manifest re-frozen at
   85 artifacts, and `test_the_manifest_hashes_every_experiment_results_directory` compares the frozen
   manifest against the tree.
9. **Five plants** cover items 7 and 8 and the radius rule (report member count, report test counts,
   README experiment count, undeclared results directory, `-0.15`/`+0.15` read one at a time):
   **27 planted defects** in the sweep.
10. **The README's experiment table is brought current** with the two rows Phase 15 and Phase 16 never
    added, and the Phase 18 row.

## 2. Mathematical assumptions

- Black–Scholes–Merton with continuous dividends; the book is three European calls at a stated quantity,
  and every priced quantity comes from the shipped `stress.run_scenario` or the core's closed forms.
- The truncated column error is v1.5.0's polynomial, `E(k) = error − (1/6)V_SSSS h³ − (mixed third
  partials)`, with the fourth-order piece as v1.6.0 defines it; the cubic and quartic differ by exactly
  that piece. Nothing is refitted: both truncations are closed forms on each book's own partial sums.
- A **zero** is a sign change of a function scanned at 2001 points and refined by 40 bisections, using
  `restrike_gamma_map._sign_change_roots` imported unchanged, so a zero here and a zero in v1.5.0 are
  the same construction on a different book.
- A **radius** is one of twelve `|delta|` grid labels, chosen by comparing each column's nearest-zero
  distance with v1.5.0's own 0.005 tolerance, contiguous outward from the smallest magnitude, a magnitude
  passing only when both of its signed columns do. It is a grid label, not an interpolated crossing, and
  it says nothing between labels.
- `v = sigma sqrt(T)` scales every spot partial by `1/v³` and higher, which is why the five books were
  picked at `v` = 0.047, 0.141, 0.141, 0.318 and 0.495 and at strikes straddling, above and below spot.
- The published gate and this rule agree by construction where both are defined: v1.6.0 gated a
  *declared* range (every column inside 0.15 must pass), so it could never contain the hole that this
  phase's first derivation rule allowed. The equality gate at item 1 is where that is asserted, not
  argued.
- No market data, no look-ahead: five synthetic books whose parameters are written in the file.

## 3. Files changed

| path | change |
|---|---|
| `experiments/second_book_crossing_map/run.py` | new producer: `Book`, five books, per-column verdicts and distances, contiguous paired-magnitude radius, `check()`, `verify_control()`, `control()`, artifact + CSV |
| `experiments/second_book_crossing_map/results/second_book_crossing_map.json` | new artifact: 5 books, 12 columns each, `headline`, `fits`, `control`, `procedure`, `refusals`, `reproduction_policy` |
| `experiments/second_book_crossing_map/results/second_book_columns.csv` | new: the 60 per-column rows, verdicts and distances together |
| `tests/python/test_second_book_crossing_map.py` | new: 10 tests, including the note-figure owner and the signed-pair plant |
| `docs/analysis/second_book_crossing_map.md` | new note, six sections |
| `scripts/run_benchmark_suite.py` | member 17 registered with seven headline fields read by key path |
| `scripts/run_mutation_suite.py` | five plants added (report suite count, report test counts, radius pair rule, README experiment count, undeclared results directory); four anchors refreshed to the values this phase changed |
| `scripts/build_evidence_manifest.py` | the new results directory declared, so its evidence is hashed rather than assumed |
| `evidence/manifest.json` | re-frozen at 85 artifacts on the commit that carries the work |
| `tests/python/test_artifact_metadata.py` | two existing guards extended to the report; one new guard for the README's experiment table |
| `docs/validation_matrix.md` | row 20 added; row and member counts re-derived |
| `docs/limitations.md` | #81 added, #79's closing clause pointed at it; count claims 80 → 81 |
| `docs/integrity_audit.md` | finding 46 and the Phase 18 addendum |
| `docs/interview_defense.md` | Q28, its citation row, and the suite/test counts |
| `docs/release_notes_v1.6.0.md` | dated correction; the speed history extended with this phase's run |
| `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md` | limitation-count claims only (they quote the live register) |
| `README.md` | experiment rows for Phase 15/16/18, the experiment count, validation rows 22 → 23, suite 16 → 17, limitations 80 → 81, performance figures re-synced |
| `paper/technical_report.tex` | the new paragraph, the headline paragraph corrected, performance table re-synced |
| `.github/workflows/ci.yml`, `docs/reproducibility.md` | member and test counts |
| `benchmarks/**`, `experiments/**/results/**` | regenerated by the `--require-all` run; provenance names the revision and the uncommitted paths it ran with |

## 4. The two definitions that were wrong, and the refusal that now catches them

**First pass.** "Some column at this `|delta|` passes." On the in-the-money book that produced a
headline in which order four *shrank* the radius (0.15 to 0.10). It was an artefact: the cubic had
already failed the other sign at 0.10 by 5.97e-3. Under the contiguous rule that book's cubic radius is
0.05 and the quartic widens it. Both superseded numbers are recomputable from the published columns, and
`tests/python/test_second_book_crossing_map.py` states the rule they came from.

**Second pass.** Contiguous, but walking the columns one at a time. A magnitude carries two columns, and
on the long-dated book `-0.15` passed at 0.00022 while `+0.15` sat at 0.02347 — nearly five times the
tolerance. The book published `radius_cubic = 0.15` beside
`worst_distance_inside_cubic_radius.cubic = 0.02347`: a radius and the evidence against it in the same
artifact, in a file that had both fields and compared neither. It surfaced when the note's figure test
asked for a value the artifact no longer carried.

Three defences, not one, because one defence would leave the shape reachable again:

- `contiguous_radius` groups by magnitude and requires every crossing column at it to pass;
- `check()` refuses to publish a radius whose widest in-range distance exceeds the tolerance, so the
  contradiction is unrepresentable rather than merely unfashionable;
- the test re-derives each radius from the artifact's own distances — including re-deriving every stored
  `*_within_tolerance` verdict, so the radius is built from numbers rather than from the producer's
  yes/no — and plants the asymmetric pair in both column orders, because the defective walk agreed with
  itself whenever the failing sign came second.

The producer gate's own teeth were proved before it was trusted: on a copy of the tree with `all`
replaced by `any`, the run answered

```text
RuntimeError: long-dated wide: its cubic radius of 0.3 contains a crossing column 2.347e-02 away,
outside the 0.005 tolerance that defines it
```

and that same twist is now plant `radius-reads-one-signed-column-at-a-time`, executed by CI rather than
by this session.

## 5. Exact test results

The five books, one row each, from `second_book_crossing_map.json`:

| book | `v` | order four / order three at `\|delta\| = 0.15` | cubic radius | quartic radius | widening | worst distance inside the cubic radius, cubic → quartic | columns with a priced crossing |
|---|---|---|---|---|---|---|---|
| published ladder | 0.141 | 0.563 | 0.05 | 0.15 | ×3.0 | 0.00243 → 1.15e-05 | 10 |
| long-dated wide | 0.495 | 0.015 | 0.10 | 0.30 | ×3.0 | 0.00206 → 3.28e-05 | 11 |
| short-dated tight | 0.047 | 3.887 | 0.02 | 0.05 | ×2.5 | 0.00273 → 3.28e-05 | 6 |
| deep out of the money | 0.318 | 0.931 | 0.15 | 0.20 | ×1.3 | 0.00273 → 0.000213 | 12 |
| in the money | 0.141 | 0.224 | 0.05 | 0.10 | ×2.0 | 0.000536 → 2.45e-05 | 9 |

- `headline.books_where_the_quartic_radius_is_at_least_the_cubic` = 5, and
  `books_where_the_quartic_is_closer_inside_the_cubic_radius` = 5.
- `control`: `book_coefficients_largest_absolute_difference`, `engine_pnl_largest_absolute_difference`,
  `cubic_truncation_largest_absolute_difference`, `quartic_truncation_largest_absolute_difference` are all
  exactly `0.0` over `control_moves_compared` = 30.
- The long-dated book's quartic radius is on the swept edge (`radius_quartic_at_grid_edge`: true for that
  book only), so 0.30 is "no column failed up to the last column we swept", which the artifact flags
  rather than rounding down.
- The claim the artifact publishes: *"the order-four widening is a property of the expansion and not of
  v1.6.0's ladder … but the magnitude does not transfer."*

Verification for the phase, in the tools' own words:

```text
uv run pytest tests/python -q                     459 passed in 73.57s (0:01:13)
uv run ctest --preset dev                         100% tests passed out of 201 (11.52 s)
uv run ruff check .                               All checks passed!
uv run ruff format --check .                      138 files already formatted
uv run mypy python/quantrisk                      Success: no issues found in 23 source files
uv run clang-format --dry-run -Werror <29 headers> exit 0
uv run python scripts/run_benchmark_suite.py --require-all
  suite: 17/17 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 226.4s total
uv run latexmk -pdf (paper/)                      Output written on technical_report.pdf (44 pages, 1001529 bytes)
uv run python scripts/build_evidence_manifest.py   wrote evidence/manifest.json: 85 artifacts
uv run python scripts/verify_evidence_manifest.py  85 OK, 0 CHANGED, 0 MISSING, 0 unlisted
```

The suite run is `benchmarks/suite/results/suite_run.json` at `generated_at_utc`
2026-10-03T04:31:43+00:00. Its performance member was measured while the machine carried load averages
of 10.8 at the start and 7.7 at the end, because three other agent sessions were running on this laptop.
The ratios it reports (`8.69×` pure Python, `0.455×` NumPy) sit inside the pinned history bands
`7.77×–8.70×` and `0.42×–0.51×`; the absolute throughputs do not match the previous commit's
(21,130,162 paths/s against 38,284,576) and the documents that quote them say so where they quote them.

## 6. Numerical validation

- **Exactness, not a band.** The control is an equality gate: `verify_control` raises on any nonzero
  difference, so the four extra books are measured with the shipped pipeline rather than an approximation
  of it. This is the only place in the chain where a re-implementation is allowed at all, and it is
  allowed precisely because it is proved identical on the book where the shipped one exists.
- **What is compared by value, and what is not.** The distances in `fits` are roots of subtracting book
  values near `1.09e5`, so they reproduce to their conditioning and the artifact declares them under
  `reproduction_policy.conditioning_limited` (`["fits", "headline.fits"]`) — the family form Phase 16
  established, with no field names and no `noise_decided_verdicts`: every verdict here is gated by design,
  and a test asserts that the second list is empty.
- **A radius has a cross-platform value even though the distance that decided it does not,** because it
  is a grid label chosen by comparison against a fixed tolerance. The reproduction test therefore holds
  radii, counts and verdicts to bit-equality and the distances to shape.
- **Both directions of the new rule are falsifiable:** the plant above for the producer, the paired
  column fixture for the re-derivation, and `test_the_note_figures_are_the_artifacts_own` re-derives
  every figure the analysis note carries — radii to two decimals, worst distances to three significant
  figures, the ratio range's 254-fold span, the crossing-column minimum — from the artifact.

## 7. Remaining limitations

`docs/limitations.md` #81 is the register's entry. In short: the direction of the order-four widening
transfers to five books and its size to none; the mechanism v1.6.0 leaned on — the order-four-to-three
ratio — is measured across a 254-fold span and does not order the widening, so no mechanism is claimed;
a radius is a grid label, decided by the worst column in its range, and a column counts only if the
priced error crosses zero inside it; five books are five points in a seven-parameter space, chosen rather
than sampled; and none of this touches the *amount* of the map's error, still 16.2 % wrong at published
size on the published book (limitation #79).

## 8. Technical debt

1. **`[[nodiscard]]` is still not applied uniformly in the core** (Phase 17, limitation #80). The
   extension-surface claim keys on the attribute, and the residual is an inventory pinned to one name.
2. **Order five.** Phase 17 measured that the quartic residual's local slope reaches 4.70–5.00 about
   2.4e-11 above the arithmetic floor, so the fifth-order term is measurable rather than merely writable.
   This phase adds a reason to want it: on the short-dated book the fourth-order piece is *larger* than
   the third (ratio 3.887), so the expansion is not descending there at published move sizes, and only
   the next order can say whether it ever is.
3. **Post-tag accounting.** `v1.6.0`'s assets are frozen and its note now carries a dated correction;
   the report PDF and the manifest in this tree are newer than the tag. If a `v1.7.0` is ever cut, its
   release note must state the radius per book rather than restating `0.05 -> 0.15` as the model's.
4. **Prose counts and hand-kept lists with no owner.** Four were closed here (the report's member
   count, its two test counts, README's experiment table, the manifest's directory list). Still unowned by
   any guard: the `ruff format --check` file counts quoted in release notes, and the "four documents and
   eleven guards" style self-descriptions. The rule this phase keeps learning is that a count is only as
   alive as the file it was read from -- and that a verifier's silence is a statement about its own list,
   not about the disk.
5. **One decision field, one value field.** Finding 46's rule is not specific to radii: anywhere a
   document or artifact stores both a decision and the quantities the decision was made over, one of the
   two is redundant unless something compares them. The repository has no general instrument for finding
   that shape yet.

## 9. Gate

**Not a release, and that is deliberate.** Version stays `1.6.0`, tag stays `b4e4bea`. The gates above
all ran on this tree; the evidence manifest is re-frozen on the commit that carries this report, and the
falsification sweep runs on a committed tree because it refuses a dirty target — so its verdict is
recorded one commit later, naming the revision it actually ran on, exactly as Phase 16 §"The sweep and
the freeze" and Phase 17 §9 explain. Nothing in this file is claimed to be inside `v1.6.0`.

Order followed, from `CONTRIBUTING.md` §4: gates → one full `--require-all` suite run → prose sync
(counts, figures, and the dated correction to a published claim) → falsification anchors → commit →
sweep and manifest re-freeze on the committed tree → push → CI on the runner.
