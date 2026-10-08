# v1.7.0 — an added order, and the answer it did not buy

Cut on the revision whose CI this note reports below. A release note cannot describe its own
publication: the tag, the run identifiers and the asset hashes are read from the API afterwards, and
`docs/phase_reports/phase-22-v1.7.0.md` records them once the tools have said them. Three releases of work sit between
`v1.6.0` and this tag: Phase 19 made the core's `[[nodiscard]]` claim cover the whole surface rather
than the part an attribute happened to mark, Phase 20 shipped the mixed fifth partials, and Phase 21
used them to measure whether the crossing radius widens again.

## What this release adds

- **The six mixed fifth partials in the core.** `pricing.black_scholes_mixed_fifth_derivatives`
  returns `V_SSSSS` through `V_sigmasigmasigmasigmasigma` as closed forms in the shape the
  third- and fourth-order structs already keep, `V = P · S^(1−n_spot) · T^(n_vol/2) · R(d1, v) / v⁴`.
  The numerator polynomials reach **d1^8** — the degree in `d1` is `8 − n_spot`, because "order five"
  bounds the derivative, not the polynomial. 204 C++ tests (`548,368` assertions in 203 Catch2 cases),
  477 Python tests.
- **The derivation is now a command, not a sentence.**
  `scripts/derive_fifth_order_partials.py` parses the numerators out of the C++ source, forms the
  quotient of the symbolic derivative of the price by the prefactor the header claims, and compares them
  at 60 markets spread over the `(d1, v)` plane: worst relative disagreement **8.7e-58** at 60 working
  digits, with nothing fitted. Its second part meets the compiled extension against 60-digit nested
  numerical differentiation at **4.6e-15** relative on four markets — float64's own last-digit noise.
- **The order-five crossing measurement.** `experiments/fifth_order_crossing_map/` (suite member 18)
  adds `(1/120)·d⁵V/du⁵` to the column truncation and asks the question on the same five books under the
  same rule, importing the books, the grid, the `0.005` tolerance and the radius rule from the Phase 18
  experiment so nothing about the definition was restated. The result: the radius grows again on
  **2 of 5 books** — the published ladder `0.15 → 0.20` (factor 1.33, against its own cubic-to-quartic
  3.00) and the deep out-of-the-money ladder `0.20 → 0.30` (factor 1.50) — and is unchanged on 3, of
  which 2 sit at the swept grid edge and are flagged as unresolvable rather than counted as negative.
  Inside the quartic's own radius the quintic is the closest of the three orders on **5 of 5**.
- **A core-surface claim with a population.** Every namespace-scope function the core declares now
  carries `[[nodiscard]]` or a disclaimer at its own declaration: 110 declarations, 102 distinct names,
  25 disclaimed, and a guard that reads both directions through the headers so a wrapped declaration
  cannot hide.
- **Counts that had no owner now have one.** The C++ totals four documents repeated are read from
  CTest's own list; the README's experiment table, the manifest's directory list, the report's suite and
  test counts, and the order-five radius table are each derived from the tree or the artifact that owns
  them.

## What this release corrects in itself

`v1.6.0` published "the radius widens from 0.05 to 0.15" as though it were a property of the expansion.
Phase 18 measured it on five books and found the direction transfers while the magnitude does not
(factors 1.3 to 3.0); that release note carries the dated correction and this one repeats the finding at
a second order. The order-five-to-four piece ratio spans 0.057 to 0.588 across the same set and orders
the widening no better than its predecessor did, so **no mechanism is offered** in place of the one that
failed twice.

The performance figures in this note are the run behind the tag: `8.45×` versus a pure Python loop and
`0.471×` versus vectorised NumPy, `44,549,572` paths/s for the core against the `5,271,981` a
pure-Python loop reaches on the same machine. They are not constants — the same binary has measured
`21,130,162` paths/s on a loaded desktop — and the committed history spans `7.77×–8.70×` /
`0.42×–0.51×`.

## Verification at this release

```text
uv run python scripts/run_benchmark_suite.py --require-all   18/18 executed and passed, 0 failed, 0 skipped, 158.7s
uv run pytest tests/python -q                                477 passed
uv run ctest --preset dev                                    100% tests passed out of 204 (9.57 s)
./build/dev/quantrisk_tests                                   All tests passed (548368 assertions in 203 cases)
uv run quantrisk validate                                    7/7 checks passed
uv run ruff check . / ruff format --check .                  all checks passed / 148 files already formatted
uv run mypy python/quantrisk                                 no issues found in 23 source files
uv run clang-format --dry-run -Werror <4 files>              exit 0
uv run latexmk -pdf paper/technical_report.tex               44 pages, 1003093 bytes
uv run python scripts/run_mutation_suite.py --list           34 plants declared
```

Two of this release's fixes exist because CI, not the laptop, was the first place they could be seen:
see `docs/integrity_audit.md` finding 54 for a bit-equality assertion that `libm` broke on Linux and a
test-count sentence in `docs/limitations.md` that no local pattern covered.

## What is still not here

- No bound. A radius is a grid label: the widened region on the published ladder contains a *looser*
  worst column (`3.81e-03` at 0.20 against `1.62e-03` at 0.15), and the amount of the map's error at
  published scale is untouched — still 16.2 % off on `risk_off` after the quartic, with order five not
  evaluated against that figure.
- No oracle for the higher orders. Nothing in this dependency set publishes a third, fourth or fifth
  spot/vol partial, so five of the six fifth-order fields are anchored by stencils of this project's own
  fourth-order family; the price-side checks (the contraction, and the derivation script's part B) are
  what break that circularity, and they are narrower than the routes they complement.
- Five books, twice. Not a family, and no distribution is estimated from it.
- `sympy` is still not a project dependency, so the derivation script runs by hand with `uv run --with
  sympy`; the assertion and Catch2-case totals are prose with no derived owner.
- The rules that were enforced: no PyPI publication, no real market data inside the engine, no
  production-readiness claim, no cost above zero.

## Correction added 2026-10-05 — the attached report contradicts this release

`technical_report.pdf`, one of the four assets on this release, was built from `v1.7.0` and carries two
present-tense statements the repository had already refuted:

- §Limitations describes the frozen evidence as "69 artifacts, 6,208,835 bytes, of which … 40
  statistical experiment files". `evidence/manifest.json`, which the same section cites, holds 94
  artifacts of 7,145,018 bytes with 65 statistical experiment files, and §1 of the same PDF prints
  the 94. The stale triple is exactly the freeze's `totals` at `v1.1.0`, so the sentence has been true of
  one release and shipped in six.
- §Stress Testing says the fifth-order crossing experiment "was specified and then deliberately not
  run". Phase 21 ran it: `experiments/fifth_order_crossing_map/` is suite member 18, and its artifact
  is row 22 of `docs/validation_matrix.md`.

The PDF attached to the release is the PDF the tag produced, so it has not been replaced; a release
asset that was published from a tag is not editable without moving the tag, and moving the tag would
break the provenance this note records. The tree is fixed instead — `paper/technical_report.tex` with
three derived guards over it (`docs/phase_reports/phase-23-report-prose.md`), the regenerated PDF in
the repository, and `docs/limitations.md` #84 stating what the guards do not reach. Anyone reading the
released PDF should read this section as its erratum; anyone reading the repository is reading the
corrected text. `docs/integrity_audit.md` finding 55 records how both sentences survived a release.

## The erratum was published on the release page itself — 2026-10-06

The section above lives in the repository, which a reader of the release page does not necessarily open.
So the GitHub release body was amended on 2026-10-06 to carry the same correction at the top, where the
two false sentences' reader actually looks.

What changed and what did not, verified against the API afterwards:

- **Body:** the original 7,091 bytes are preserved verbatim as the tail of the new 9,577-byte body (one
  trailing newline added by the concatenation, and nothing else: the read-back equals
  `prefix + original + "\n"`). Both halves of the edit are committed rather than left in a shell
  temp -- `docs/release_bodies/v1.7.0-body-before-2026-10-06.md`
  (`sha256 58a6d5e3a08d86f009841e8ba72b5787713a55437f919ff9e68cb5529d65e90f`) and
  `docs/release_bodies/v1.7.0-erratum-block-2026-10-06.md`
  (`sha256 474ad8676fc8cfc0f6ba4ed8519cc4a2addc3e1c0de252ad2ce7435d80436812`) -- so the edit is reversible
  byte for byte by anyone, not only by whoever held the file.
- **Assets: none touched.** All four still report the sizes and digests recorded under
  "Verification at this release" above -- `technical_report.pdf` `1003093` /
  `99d1c108347544e1d96695a1d3db27b9a6890f97b516783fa001cf6a40ce9a5d`, `manifest.json` `55188` /
  `e3f7418da0bea4e3c96463433df5eda26ab6966b556f63078939930ebb9336b6`, `CITATION.cff` `2493` /
  `f6ccac700e3d7603ea6a496a9fbc9182e63547f920cde39f32f7a58cf77628df`, `quantrisk-suite-results.zip`
  `144544` / `84675cb5d0ae03a326ccbd8fb2f999d60924c0acdc2a8d0e3f68fcd67dde1f76`. The tag is unchanged.
- **The repository's copy of the report was rebuilt while writing this.** `paper/technical_report.pdf` in
  the tree turned out to lag `paper/technical_report.tex`: it had been built before the offline test count
  moved 408 → 412, so the tree carried a PDF quoting a number the tex no longer states. Nothing owns that
  freshness, which is the same class of defect finding 55 records one level up; the PDF is rebuilt here and
  the missing owner is registered as `docs/phase_reports/phase-24-dependencies-and-build-products.md` §8
  rather than left as an anecdote.

## Second correction added 2026-10-07 — the attached report contradicts itself on the register's size

The first correction above covered the two sentences Phase 23 found. Phase 27 added an
inventory guard over `paper/technical_report.tex` -- every `<number> <countable noun>` claim
must be owned by a named guard, sit inside a span a guard compares, cite an artifact the
freeze hashes, or be declared with a reason -- and its first run found a third stale
statement in the same document. Verified against the **released asset**, not the repository:

- `technical_report.pdf` at this release (1,003,093 bytes, digest recorded under
  "Verification at this release"; unchanged) states on its first page
  `was not established: 55 recorded limitations` -- pdftotext line 27.
- The same file states twice that the register `contains 83 numbered entries` and
  `holds 83 numbered entries` -- pdftotext lines 373 and 2490.
- `git show v1.7.0:docs/limitations.md` counted with the repo's own numbering rule gives
  **83**, contiguous from 1, so the section sentences were true at the tag and the abstract's
  was 28 entries behind. `main` carries 86 as of this correction.

Why no existing guard saw it: `test_documents_that_count_the_limitations_agree_with_the_file`
compares the phrasings `carries/contains/holds N numbered entries`, and the abstract writes
the same fact as `N recorded limitations`. That is finding 55's mechanism -- one document, one
fact, several phrasings, one of them compared -- recurring in a paragraph no guard had been
keyed to. The owner now reads both phrasings, and it went red the moment the second was added
(`paper/technical_report.tex says ['85', '85', '55']` against a file holding 85 at that moment),
which is the defect rather than a mutant. Finding 59(a) is the audit entry;
`docs/phase_reports/phase-27-claim-inventory.md` is the phase record.

- **Assets: none touched, tag unchanged.** Same rule as the first correction: the tag anchors
  the provenance of the bytes it carries, so replacing an asset under a released tag would make
  this page point at bytes that no longer match that anchor. The repository's
  `paper/technical_report.tex` and the rebuilt `paper/technical_report.pdf` on `main` at
  `9117403` carry the derived figure, and the inventory guard plus its declared plant
  `report-adds-an-unowned-numeric-claim` keep a new numeric sentence from arriving unclassified.
- **Release page:** the block appended to the release body is saved verbatim as
  `docs/release_bodies/v1.7.0-second-correction-block-2026-10-07.md`
  (2,027 bytes, sha256 `229c21a64c6ae190d21665e420e0a449dcfdb62f08eaa8f9bbe023a61ba60c3c`), the body
  as it stood before this edit as
  `docs/release_bodies/v1.7.0-body-before-2026-10-07.md` (9,639 bytes, sha256
  `35a39c0d625b0ae67cc1a5c87ac68bc899f8fb75c788a53671df9bd8710b75bf`), and the
  published body afterwards is exactly the saved-before text plus the saved block -- 11,604
  characters, sha256 `8122e06b62437d156eb91c3d1c4166df0721c6d50087ac45527d4b71dac3b8a1` over its
  UTF-8 bytes -- which is the check that the first correction was appended to rather than replaced.
  The identity is exact as files: `saved-before text + one newline + saved block file == published
  body`, verified by constructing the published text from the two files. Citing these digests is how
  this phase found its own slip: the note first named `b0a13681…` for the block, which was the hash of
  the text before the file was saved with its trailing newline.
  `test_every_digest_a_release_note_cites_is_its_files_own` now reads every 64-hex digest this note
  cites for a file under `docs/release_bodies/` and requires that file's own hash.
- **A present-tense bullet of this note has since moved.** "What is still not here" says
  `sympy` "is still not a project dependency, so the derivation script runs by hand"; that was true at
  the tag. Phase 24 added `sympy>=1.12` to the `dev` dependency group, so every lane that runs
  `uv sync` now executes the identity, and
  `tests/python/test_fifth_order_partials.py::test_the_derivation_command_agrees_at_the_precision_floor`
  is gated on it. The bullet is left standing as what this revision said; this line is the dated
  correction, per the rule that records of a revision are appended to rather than rewritten.

## Third correction added 2026-10-08 — the performance figures this note quotes have moved again

The paragraph above this note's "Verification" section quotes the figures of the run that was behind
the tag (`8.45×`, `0.471×`, `44,549,572` and `5,271,981` paths/s) and states the committed history as
`7.77×–8.70×` / `0.42×–0.51×`. Both halves have moved since, and this note is one of the six documents
the band guard reads, so they are corrected here rather than left to decay:

- The point figures are what the artifact on disk measures now — `8.88×` versus a pure Python loop and
  `0.460×` versus vectorised NumPy, `39,944,978` paths/s for the core against `4,500,031` for the
  interpreted loop. Same script, same machine, same workload; the run behind the tag is three
  re-freezings old.
- Over the twenty-one committed measurements the history now spans `7.77×–8.88×` / `0.42×–0.51×`: the
  pure-Python upper edge rose by 0.18, the NumPy band did not move at all, and the spreads are 14.2%
  and 20.8%. The NumPy baseline ranges from 110M to 46M paths/s across those twenty-one runs, which is
  why its ratio is the noisier of the two per unit of load.
- Two clean idle runs of that script four minutes apart on 2026-10-08 wrote `8.378×` / `0.5656×` and
  `8.877×` / `0.4597×`. Only one of them can ever be quotable, because the tree carries one artifact
  rather than a sample; the second is what is committed, and the first is recorded here so the 19%
  swing between them is not lost. A third run, contending with a second concurrent copy of the suite,
  wrote `4.01×` and `0.36×` — below every edge this repository has printed — and was restored rather
  than committed.

The paragraph above is left as written because it is dated to the tag. `docs/reproducibility.md` owns
the range and prints the command that recomputes it;
`test_documents_quote_the_performance_figures_the_artifact_actually_holds`,
`test_the_documented_speedup_ranges_contain_the_current_measurement` and
`test_the_documented_speedup_ranges_match_the_committed_history` are what make leaving a stale figure
in a present-tense sentence impossible.
