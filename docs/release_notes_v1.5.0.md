# v1.5.0 — The release that measured the advice it gave

Released 2026-09-30. Predecessors: `v1.0.0`, `v1.1.0`, `v1.2.0`, `v1.3.0`, `v1.4.0`. Total monetary
cost of building and validating this release: **$0**.

`v1.3.0` finished a two-factor error analysis of the stress map with a recommendation — re-strike gamma
at the shocked volatility rather than add vanna and volga. `v1.4.0` added readers, not results. This
release takes the recommendation itself apart: it measures it, publishes where it holds, and publishes
where it makes things worse. The core is unchanged; the suite grows from fourteen members to fifteen,
and the count of C++ tests, identities and validated components does not move.

## What this release adds

**A measured answer, with the negative half first.**
`experiments/restrike_gamma_map/run.py` rebuilds the published map four ways — every exposure at the
base market (what ships), gamma alone at `(S, sigma + k)`, gamma at `(S + h, sigma + k)`, and all three
at the shocked market — and prices each through `stress.run_scenario` against a revaluation of the same
book over the 132-cell joint grid. On the repository's own `risk_off` the recommendation holds: the
error falls from `-5320.79` to `+1937.72`, a factor of `0.364`. Across the 120 swept cells with a
volatility move, 45 are no better and 20 are at least twice as wrong, worst factor 142 — and every one
of those 20 is a cell whose shipped-map error was *smaller than the term the recipe removes*, which is
a mechanism rather than a list: along a `delta` column the map's error contains a volatility-independent
piece `1/6 V_SSS h^3` and pieces proportional to `k`, and where they cancel the map is exact by
arithmetic, not by merit. `docs/findings.md` §7 leads with the 45; the artifact's `refusals` block names
the limits.

**A prediction with a stated radius.** The truncation of the base map's error, assembled from core
closed forms with nothing fitted to the measured errors, predicts where each `delta` column looks most
accurate — its zeros. Compared against the zeros of the priced error by one shared
bracket-and-bisect routine, the nearest pair agrees to `0.0002-0.0024` in vol move within
`|delta| <= 0.05` against a gated tolerance of `0.005`. Beyond that the prediction drifts monotonically,
to `0.093` at `|delta| = 0.30`, and at `delta = +0.30` the truncation predicts a zero the priced map
does not have. The gate covers only the regime where a third-order truncation is a fair argument, which
is where the published scenarios live; the drift is published in `cancellation_columns.csv` rather than
argued away.

**The naive fix, priced.** Re-striking *every* sensitivity at the shocked market — what "use the new
greeks" suggests — is worse than the gamma-only variant on 116 of the 120 cells and worse than the
shipped map by a factor of 11 on `risk_off`. The specificity of the original phrasing turns out to have
been the load-bearing part.

**Two numbers a reader needs before repeating the recommendation.** The recipe removes `7258.51` of the
`8402.16` term the derivation named — 86.4 % of it, the shortfall being a finite difference across six
volatility points rather than the local derivative — and the order of the map is untouched: between the
two narrowest scales of three rays the error of all four maps falls with a local slope of `1.98-2.01`.

**Twelve tests that refuse to reuse the producer.** `tests/python/test_restrike_gamma_map.py` rebuilds
the four variants' exposures one leg at a time from the pricer, re-evaluates the committed CSV against
the shipped engine, re-finds the artifact's zeros by bisecting the engine, recounts the cancellation
cells from the table, re-derives every figure the experiment's own docstring, the analysis note, finding
7 and the technical report print, and asserts that the interpreter and the optional extras have exactly
one home in the artifact. It also asserts, against Phase 13's artifact, that the base
map's `risk_off` error is the same number both producers compute — it is, to the last digit.

**A note, a matrix row, and a limitation.** `docs/analysis/restrike_gamma_map.md` owns the derivation;
row 18 of `docs/validation_matrix.md` pairs the four maps with what they are checked against
(no oracle, an identity and a grid measurement); `docs/limitations.md` #78 states the scope, including
that `stress.run_scenario` ships unchanged and a user needing the joint residual controlled must
re-value rather than re-strike.

## What this release corrected in itself

**A band guard that could reject the measurement it was built from.** The pinned speedup band is the
*rounded* envelope of the artifact's committed history, but the containment check compared raw values: a
re-frozen run at `0.5104` was reported as outside a band whose upper edge, `0.51`, is what that value
rounds to. Both guards now use the same rounding, with the reason in the test. Audit finding 37.

**A shipped producer's helper ignoring its own argument.** `experiments/two_factor_error_bound/run.py`
scaled three exposure entries by the module-level base spot rather than by its `spot` parameter. It was
dormant — only `BASE` is read as an exposure, and the moved-market call site consumes raw partials with
no spot factor — but the Phase 15 experiment began as a copy of that helper and reproduced the defect
before it was caught. Fixed in both, and Phase 13's experiment was re-run to prove every published field
byte-identical apart from its timestamp and dirty-tree list. Audit finding 38.

**A range my own draft got wrong.** The experiment's claim block first said the narrow-window slopes
spanned `1.94-2.04`. The artifact's aligned-ray base slope is `1.8919`. The guard written to police
producer-docstring figures caught it on the run that introduced it, and the prose now quotes the
pairwise slope, which needs no window.

## Verification at this release

Read out of the commands, on the working tree that becomes this tag:

```text
uv run ctest --preset dev          100% tests passed out of 198
uv run --frozen pytest -q          423 passed (wall-clock quoted in the phase report,
                                   because it is a per-run measurement, not a result)
uv run python scripts/run_benchmark_suite.py --require-all
                                   suite: 15/15 executed and passed, 0 aggregated from disk,
                                   0 failed, 0 skipped, 77.7s total
uv run quantrisk validate          7/7 checks passed
uv run python scripts/verify_evidence_manifest.py
                                   80 OK, 0 CHANGED, 0 VOLATILE, 0 MISSING,
                                   0 on disk but not in the manifest -- Evidence is intact.
uv run ruff check .                All checks passed!
uv run mypy python/quantrisk       Success: no issues found in 23 source files
latexmk -pdf technical_report.tex  Output written on technical_report.pdf (43 pages, 970663 bytes)
```

`git diff --name-only HEAD -- '*.cpp' '*.hpp'` is empty: the core does not change in this release, so
the C++ gate re-verifies the same 198 tests it did at `v1.4.0`. The manifest's own `git_commit` names
the revision it was generated *from*, which is necessarily the commit before this file's, and the
working tree it saw was the one being committed — `evidence/manifest.json` cannot contain its own hash.

## Release record

The tag `v1.5.0` points at `2ad54059ae288d5cc14dcba954f014fefeb29160` — the commit the runner had
just verified, not a later documentation head. GitHub Actions reports it directly:

```text
run 36811258118   status=completed  conclusion=success
  Format and static checks                    success
  Configure, build, C++ tests, Python tests    success   353 passed, 5 skipped in 47.82s
  Benchmark suite against live oracles         success
```

The five skips are the four oracle-gated modules, which drop out at import on a lane without the
`oracles` extra, plus this release's own history guard saying so in its words (audit finding 35). The
`353 passed` is the CI collection the documents quote as "354 collected without it": the four module
skips are reported by the run and never collected, which is why the two numbers differ by five and not
by four.

The release is `publishedAt 2026-10-01T03:46:09Z` at
`https://github.com/Jackxiaozhiren/quantrisk-plus-plus/releases/tag/v1.5.0`. Its four assets were
built from `git archive v1.5.0` — not from a working tree — and each was downloaded back and hashed:

| asset | sha256, computed on the export and again on the download | size |
| --- | --- | --- |
| `technical_report.pdf` | `706d4075b58aa9bb29807977c9812f90e3dc1c11a8e2340fa4018525cca69e8d` | 970,663 |
| `manifest.json` | `81f42f1c4bef74389dcdcfef14ce81bc07e161d786b3425bc684cfd93deb2988` | 48,434 |
| `CITATION.cff` | `4f6665120196280aaa7f5f73ca7cbfff43b389a980b9501db00f3f859f6ce54a` | 2,493 |
| `quantrisk-suite-results.zip` | `601be2e6d0d922dae896cc8e29cd772406761044e04183ae49542aea58404b45` | 141,702 |

Two provenance facts are stated rather than smoothed. This file is a **post-tag** commit: the copy of
`docs/release_notes_v1.5.0.md` inside the tag ends before this section, because a release note cannot
record its own publication. And `evidence/manifest.json` names `cf053f1f42fd` with
`working_tree_dirty: true` in its own `repository` block — the manifest records the revision it was
generated *from*, which is necessarily the commit before the one that contains it.

## What is still not here

- `stress.run_scenario` still maps volatility to first order. This release measures a *hypothetical*
  correction; it does not ship one, and #78 says what to do if the residual has to be controlled.
- One book, one maturity, one base volatility, one scenario set. No estimate of how the ranking of the
  four maps moves for a book whose gamma behaves the other way in volatility.
- The `all_restrike` variant is priced, not recommended; and the `gamma_restrike_at_move` variant is
  published without being claimed better than either neighbour.
- No market data, no forward-looking claim, no performance claim over any library: the C++ core remains
  roughly 8× an interpreted loop and slower than vectorised NumPy on the benchmarked workload, within
  the committed bands `7.77×–8.70×` and `0.42×–0.51×`.
