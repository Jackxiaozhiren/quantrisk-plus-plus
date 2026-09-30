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
uv run ruff format --check .   124 files already formatted
uv run mypy python/quantrisk   Success: no issues found in 23 source files
find cpp bindings tests/cpp ... | xargs uv run clang-format --dry-run --Werror
                               clean (no diagnostics)
uv run ctest --test-dir build/dev   100% tests passed out of 198   (Total Test time = 7.54 sec)
quantrisk_tests                All tests passed (547845 assertions in 197 test cases)
uv run pytest tests/python -q  411 passed
uv run python scripts/run_benchmark_suite.py --require-all
                               suite: 14/14 executed and passed, 0 aggregated from disk,
                               0 failed, 0 skipped, 84.6s total
uv run python scripts/verify_evidence_manifest.py
                               76 OK, 0 CHANGED, 0 VOLATILE, 0 MISSING, 0 unlisted
                               Evidence is intact.
uv run quantrisk validate      7/7 checks passed   (parity, O(h^2) delta, 1/sqrt(N), seeded MC,
                               ES >= VaR, optimiser constraints + certificate, attribution)
latexmk -pdf -g technical_report.tex
                               Output written on technical_report.pdf (42 pages, 966341 bytes)
```

The PDF was re-extracted, not assumed: `pdftotext` on the rebuilt file returns `8.39×`, `0.445×`,
`38,642,054`, `7.77×`, `8.70×`, `411 pytest tests` and `342 collected`, i.e. the document carries the
artifact it ships beside rather than the run before it.

The runner's own lines on the tagged head, `f4e8afc13bd7`, run `36663508268`:
`100% tests passed out of 198`; `335 passed, 5 skipped in 50.26s` offline;
`suite: 14/14 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 194.4s total` on the
oracle lane; `Success: no issues found in 23 source files` and a silent clang-format step. The fifth
offline skip is this release's history guard printing its precondition —
`this clone carries 1 revision of the artifact (CI uses actions/checkout at depth 1), so no spread
can be derived; see the command in docs/reproducibility.md` — which is finding 35 resolved in the
environment that found it, rather than in the one that wrote it.

The suite count moved `388 → 411` with the `oracles` extra and `319 → 342` without it — twenty-three
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
and the pinned band must never be one. the background wrapper around `gh run watch --exit-status` reported 0 for the failed run while
the watcher itself exits 1 — measured directly on `36550420085` after the fact — so the tag was created
only after `commits/<sha>/check-runs` reported success (see
`docs/integrity_audit.md` finding 35).

The fix was verified where the defect appeared. `36663508268` on `f4e8afc13bd7` — the revision the
tag names — is `completed / success` on all three jobs, and the API's `commits/<sha>/check-runs` is
what said so: `100% tests passed out of 198`, `335 passed, 5 skipped in 50.26s`,
`suite: 14/14 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 194.4s total`,
`Success: no issues found in 23 source files`. The fifth offline skip is the history guard printing
its own precondition, which is the point: a check that needs history declares it rather than
inventing a band from one measurement. The pinned band is still compared against the history min/max
in every clone that carries one, so the provenance did not disappear — it acquired a precondition.

## After this tag — the mutation harness became a repo tool

This section postdates `v1.4.0`. The harness landed on `main` at `ee9db87`, after the tag was cut on
`f4e8afc13bd7`, so it is **not** in the released tree and the GitHub release says as much; it is written
here because these notes are the living account of the release, and leaving the debt bullet in place
would describe `main` falsely.

Phase 13 §8, Phase 14 §8 and these notes' own debt list all said the same thing: the sweep that proves
a guard can fail was hand-rolled in `/tmp`, three phases running. It is now
`scripts/run_mutation_suite.py`, and it exists because finding 25 recorded what the hand-rolled version
did — two of nine mutations never applied, because clang-format had reflowed the expression between the
read and the patch, and the sweep still printed "nine mutations caught".

Each case proves four things in order, and a failure at any step gets its own status rather than being
tallied as a catch: the anchor occurred exactly once; the file bytes actually changed; the named guard
went red; the bytes restored to the recorded SHA-256 and the same guard went green again. Eighteen
defects are declared in three kinds — fourteen `prose` edits in documents or bindings (a shifted analysis-note
slope, a narrowed README band, a stale README ratio, a pybind registration the installed binary cannot
serve, a phantom path in the architecture block, and one off-by-one in each documented figure: the
limitation register, the C++ count, the suite's member count, the offline test count in a second spelling,
the report's chapter count, the matrix's row count, the caveat heading and the findings count, plus a
duplicated matrix row number), one `tree` case that *creates* an unregistered
`experiments/_mutation_probe/run.py` for the registry-completeness guard and then deletes it, and three
`core` edits in the C++ closed forms (volga using its own square, vanna losing its sign, `V_SSsigma`
dropping a term), each rebuilt into the Catch2 target and rejected by its CTest case. The sweep runs on a
clean tree — it refuses to start if any target differs from `HEAD` — and its own line is quoted in
`docs/phase_reports/phase-14-verification-debt.md`.

The harness is also shown able to say *no*. A probe mutation in text no guard reads, aimed at a guard
that cannot see it, was reported as `guard-stayed-green` rather than counted — finding 25's failure mode
made visible instead of silent. Two safety properties are enforced rather than trusted: it refuses to
start if any target file differs from `HEAD`, so it cannot overwrite work in progress, and it restores
each file from the snapshot taken before its own edit, hashes the restore, and finishes with a sweep
that prints `restore-mismatch` and exits non-zero if anything is left modified.

The tree case exists because of the audit's last open line — "the suite's member registry is
hand-maintained: a new benchmark that is never registered is simply absent, and absence produces no
output to check" — and it is closed by `test_every_experiment_and_benchmark_script_on_disk_is_a_suite_member`,
which enumerates every `experiments/*/run.py` and `benchmarks/*/*.py` and compares the set against the
registry in both directions. That guard is what the probe plants: an experiment that runs but is not a
member.

Its gate is `tests/python/test_mutation_suite.py` (five cases), which is what keeps the tool from
rotting the way the prose did: on every ordinary test run it re-checks that each anchor still occurs
exactly once in the file it names, that each prose guard still defines the named test, that each C++
guard still exists as a `TEST_CASE`, that the identifiers are unique, that the status function names
each way a cycle can lie instead of calling it `caught`, and — the ratchet that makes the list itself
checked — that *every* documented-figure guard in `tests/python/test_artifact_metadata.py` is named by
some mutation, so a twelfth count guard cannot arrive with no defect planted for it. That ratchet has
already earned its keep: mid-cascade an edit moved a guard's anchor from `# 341 Python tests` to 342 and
the self-test failed on the now-stale anchor, which is the finding-25 failure mode caught before it could
report a clean sweep. Running the harness itself remains an operator action — it edits tracked files and
recompiles — so it is not a CI step; what CI checks is the list.

One scope limit stated rather than implied: a `core` case rebuilds only `quantrisk_tests`, not the
Python extension, so it proves the C++ gate rejects the wrong formula. The Python-visible consequences
of a wrong formula are carried by the reproduction comparator and the extension-surface parity guard,
not by the harness.

## What is still not here

- **No new validated component.** The matrix gained no row; what gained coverage was documentation
  and the compiled surface.
- **The guards read claims, not mathematics.** A note whose figures match its artifact can still be
  wrong about what the figures mean; #77's third defect is that failure mode and only prose review
  catches it.
- **Volatile fields still have no cross-platform meaning.** `docs/reproducibility.md` now states the
  history band and the command that recomputes it; it does not make a laptop's ratio meaningful on
  Linux, and no gate pretends otherwise.
- Nothing here is a trading recommendation, an expected return, or a statement about realised
  markets. `docs/limitations.md` is the complete list of what is not claimed.
