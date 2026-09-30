# v1.4.0 — The release that adds readers, not results

Released 2026-09-30. Predecessors: `v1.0.0`, `v1.1.0`, `v1.2.0`, `v1.3.0`. Total monetary cost of
building and validating this release: **$0**.

`v1.3.0` ended with a list of checks the project owed itself. `v1.4.0` pays that debt and adds no
new financial result: the core, the experiments, the suite's fourteen members and the validation
matrix are unchanged in count. What changed is that four classes of claim now have a reader, and
each reader found something the repository had been asserting without knowing it.

## What this release adds

**A reader for the compiled surface.** `tests/python/test_extension_surface_parity.py` treats
`bindings/python_bindings.cpp` as the contract and the imported extension as the evidence, and
differs them in both directions: a declared name absent from the binary is the stale-`.so`
signature (limitation #70), and a binary name absent from the source is API the repository no
longer declares. The parser is structural — one registration statement per four-space-indented,
semicolon-terminated block, with string literals stripped before parentheses are counted — because
the substring version it replaced attributed `stats.mean` to the `Rng` class on account of a
documented range written `"[0, 1)"`. Six cases, including a formatter-reflow fixture, a stale-binary
probe, and a non-vacuity floor on how much surface the parser claims to have read.

**A reader for the analysis notes.** `test_every_figure_the_note_quotes_is_owned_by_the_artifact`
re-formats every figure a note prints from the artifact it cites and requires the note to carry that
exact string; `test_every_analysis_note_is_guarded_against_the_numbers_it_quotes` fails if any file
in `docs/analysis/` has no test that reads it at all. Writing them found three defects in the Phase
12 note, recorded as limitation #77 and audit finding 32: a crossing spot quoted as `94.5456` where
the artifact publishes `94.5487358657606` (and internally consistent, which is why nobody caught
it); a headline slope/standard-error pair belonging to a pooled fit the experiment does not compute;
and a sentence that read a regression's standard error as a bound on accuracy.

**A reader for how the repository describes itself.**
`test_every_path_the_architecture_document_declares_exists` parses the layout block, expands brace
groups, and fails on any declared path that is not in the tree — which is how
`python/quantrisk/analytics/` was found: a package `docs/architecture.md` had described in two
places and that had never existed (finding 33). `test_documents_that_count_the_paper_chapters_agree_with_the_source`
counts `\section` in the LaTeX and checks the six documents that restate it; the report has
twelve chapters and one unnumbered artifact index, not the thirteen that two earlier release notes
claimed.

**A reader for the numbers that regenerate.** `docs/limitations.md` #77 was written about prose
figures; this release found the same blind spot in the *present tense*, about a file that every
suite run rewrites. `speedup_vs_pure_python`, `speedup_vs_numpy` and `results_seconds` are volatile
by declaration, so the manifest certifies nothing about them — while the README, the validation
matrix, the interview document and §9 of the paper all quote them as the artifact's own. Now
`test_documents_quote_the_performance_figures_the_artifact_actually_holds` re-derives those figures
from the file and demands them of the prose. The ranges are checked twice over:
`test_the_documented_speedup_ranges_contain_the_current_measurement` pins the band, requires the
current measurement to sit inside it and the documents to state it;
`test_the_documented_speedup_ranges_match_the_committed_history` requires the pinned band to equal
the min/max read out of the artifact's git history, and declares a skip where the clone has no
history to read. `test_the_performance_guards_are_not_vacuous` shifts the artifact by 1.5× and
narrows a band by hand to prove the guards can fail. See the two sections below: this one corrected
the release's own documentation, and the runner then corrected the correction.

## What this release corrected in itself

**The performance claim was a present-tense claim about a moving file** (finding 34). The artifact
behind `v1.3.0` measured `7.909×` against a pure Python loop while `docs/validation_matrix.md`
described that same file as living in `8.0–8.4×`, and `README.md` quoted "45.5M vs 5.5M paths/s in
the current artifact" for a file reading 45.6M and 5.8M. Worse, the *ranges* had been written from a
handful of runs rather than from history: the thirteen committed measurements of that file span
`7.77×`–`8.70×` (11.9% spread) and `0.42×`–`0.51×` (20.8%), against the 5% and 14% spreads the
documents claimed. The NumPy baseline is the reason it moves: itself ranging from 110M to 70M
paths/s, so any ratio against it inherits that movement rather than measuring the core. One
re-run, taken while another process held a core, read `7.35×` with `var_backtesting` at 103.4 s
against 25.2 s in the quiet run that follows it; that figure is recorded in
`docs/reproducibility.md` as an observation and is deliberately not headlined anywhere, because the
artifact that measured it was overwritten. What survived all thirteen measurements is the ordering:
C++ beats an interpreted loop by roughly an order of magnitude and loses to vectorised NumPy for
terminal-only payoffs. No conclusion moved; the honesty of the digits attached to it did.

**Every gate was green while this was true**, which is the actual finding: the artifact re-froze, its
ratios moved by 6%, and nothing in `make check` noticed, because nothing read that file.

## Verification at this release

Each line is quoted from the tool that produced it, on the arm64 laptop, at 1.4.0, extension built
from `f526171eac4c` and reinstalled with `--no-cache`:

```
uv run ruff check .            All checks passed!
uv run ruff format --check .   122 files already formatted
uv run mypy python/quantrisk   Success: no issues found in 23 source files
find cpp bindings tests/cpp ... | xargs uv run clang-format --dry-run --Werror
                               clean (no diagnostics)
uv run ctest --test-dir build/dev   100% tests passed out of 198   (Total Test time = 7.54 sec)
quantrisk_tests                All tests passed (547845 assertions in 197 test cases)
uv run pytest tests/python -q  405 passed in 24.06s
uv run python scripts/run_benchmark_suite.py --require-all
                               suite: 14/14 executed and passed, 0 aggregated from disk,
                               0 failed, 0 skipped, 84.6s total
uv run python scripts/verify_evidence_manifest.py
                               76 OK, 0 CHANGED, 0 VOLATILE, 0 MISSING, 0 unlisted
                               Evidence is intact.
uv run quantrisk validate      7/7 checks passed   (parity, O(h^2) delta, 1/sqrt(N), seeded MC,
                               ES >= VaR, optimiser constraints + certificate, attribution)
latexmk -pdf -g technical_report.tex
                               Output written on technical_report.pdf (42 pages, 966335 bytes)
```

The PDF was re-extracted, not assumed: `pdftotext` on the rebuilt file returns `8.39×`, `0.445×`,
`38,642,054`, `7.77×`, `8.70×`, `405 pytest tests` and `336 collected`, i.e. the document carries the
artifact it ships beside rather than the run before it.

The suite count moved `388 → 405` with the `oracles` extra and `319 → 336` without it — seventeen
cases on each side, none of them oracle-gated, which is why the two numbers move together.
`docs/limitations.md` carries 77 numbered entries.

## The runner corrected the correction

`36550420085` is `failure`, and the failure was in the new guard rather than in the mathematics. The
range check derived its band from `git log -- benchmarks/performance/results/monte_carlo_speed.json`,
which locally reads thirteen measurements; `.github/workflows/ci.yml` uses `actions/checkout` at its
default depth of 1, so the runner saw one revision and demanded that `README.md` quote a `0.45–0.45`
spread. The job printed `1 failed, 334 passed, 4 skipped`. A check that reads history is a claim about
the *clone*, and I had asserted the two were the same thing.

The invariant was split accordingly. What is checked in every clone: the current artifact lies inside
the pinned band, and every document states that band. What is checked where history exists: the pinned
band equals the min/max over the artifact's committed revisions — and when it cannot be derived, the
test says so in its own skip reason instead of passing quietly. The vacuity test now carries the case
that would have caught this before the runner did: a band derived from one measurement is zero-width,
and the pinned band must never be one. `gh run watch --exit-status` returned 0 for the failed run, so
the tag was created only after `commits/<sha>/check-runs` reported success (see
`docs/integrity_audit.md` finding 35).

## What is still not here

- **No new validated component.** The matrix gained no row; what gained coverage was documentation
  and the compiled surface.
- **The guards read claims, not mathematics.** A note whose figures match its artifact can still be
  wrong about what the figures mean; #77's third defect is that failure mode and only prose review
  catches it.
- **Volatile fields still have no cross-platform meaning.** `docs/reproducibility.md` now states the
  history band and the command that recomputes it; it does not make a laptop's ratio meaningful on
  Linux, and no gate pretends otherwise.
- **The mutation harness is still not in `scripts/`** — the debt item that would prove these guards
  kill a planted defect rather than a deleted one.
- Nothing here is a trading recommendation, an expected return, or a statement about realised
  markets. `docs/limitations.md` is the complete list of what is not claimed.
