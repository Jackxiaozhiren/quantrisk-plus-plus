# v1.9.0 — twenty-eight phases of instrumentation, and the release that re-measured nothing

Cut on the revision whose CI this note reports below. A release note cannot describe its own
publication: the tag, the run identifiers and the asset hashes are read from the API afterwards, and
`docs/phase_reports/phase-59-v1.9.0.md` records them once the tools have said them. Twenty-eight phases
sit between `v1.8.0` and this tag, and **none of them changes a line of the engine**: `git diff --stat
v1.8.0..HEAD -- cpp include python/quantrisk` is empty, which is the fact this note's most surprising
sentence rests on.

Phases 31–58 built producers. The release therefore carries the same numbers `v1.8.0` published, and the
honest question a reviewer should ask is not "what got faster" but "what can now be disagreed with".

## What this release adds

- **A binding between the report and the sources that rendered it.** `paper/technical_report.pdf` used to
  be a file a phase could forget: Phase 24 found it lagging an engine change, finding 55 found it quoting
  digits its own source no longer printed. `test_the_committed_report_pdf_is_bound_to_the_sources_that_rendered_it`
  now compares the PDF's recorded build digest with a recomputation from the committed `.tex` and its
  inputs, so a stale PDF fails the lane rather than shipping (#90 closed).
- **A producer for `date-released`, and a completeness rule for the band census.** The release date is
  derived from the tag's own commit date, with the declared skip that a clone fetched without tags has to
  take (`scripts/build_evidence_manifest.py`, Phase 32). Every document that prints a speedup band is now
  enumerated -- policed, or declared dated with a reason -- so a note that quotes `7.77×`-style edges
  cannot escape by not being in a hand-maintained list.
- **A CI lane that can see history, and a spread with an owner.** The pytest lane fetches
  `fetch-depth: 0` with tags (Phase 33), which is what turned two guards that had always skipped on the
  runner into checks that run there; the band *percentages* moved from laptop-derived claims to figures
  derived from committed history, pinned so a shallow clone cannot certify a zero-width spread.
- **The claim inventory finished its corpus.** The rehearsal sheet, the validation matrix and the report
  itself joined the owned-or-declared rule (Phases 35, 41–43), the spelled-numeral table was generated to
  one hundred instead of stopping at twenty-six (Phase 44), and ownership credit is checked in the owner's
  own syntax rather than by a substring beside it (Phase 45, #98 closed). A claim that names row N now has
  to describe row N (Phase 47, #99 closed).
- **A falsification harness that proves its own pairings.** A mis-named plant's `guard` field stops the
  sweep at the plant instead of letting another guard take the blame (#103, Phases 46 and 57); the pairing
  audit reads membership of the failing set -- its prescribed "exactly one guard objects" criterion was
  refuted by measuring it, 27 of 78 plants redden one guard and the rest redden several (Phase 57); and
  every plant now carries a text link to the assertion it attacks, derived from the failing line and the
  named guard's reading closure rather than from a hand-typed reason string (Phase 58, #107 closed). The
  last of those caught a defect in itself: the audit had been reading the closure from the *mutated* file,
  so a plant that deletes the reference the closure follows erased the evidence of its own pairing.
- **A declaration ledger, so `none:` means something.** A declared number now has to name the producer
  that could disagree, or record that none exists, and the recorded "none" is checked against a
  measurement corpus rather than taken on trust (#101, #106 closed by Phases 54 and 55).

## What this release corrects in itself

Three current claims in this repository were false, unowned, and shipped:

- **`CITATION.cff`'s abstract said "55 numbered limitations" for four releases while the register passed a
  hundred.** The citation file is uploaded as a release asset, so the stale number was downloadable and
  citable. It joins `test_documents_that_count_the_limitations_agree_with_the_file`, whose docstring has
  described this exact failure since Phase 10, and the plant
  `citation-understates-the-limitation-register` proves the new spelling can redden.
- **The rehearsal sheet's state line said "Phases 0–43 shipped" with fifty-eight shipped.** Phase 30
  registered that this line had no producer; nothing on disk could disagree with it, and it had drifted
  twice since. `docs/phase_reports/` is the producer -- the shipped bound is the newest *content* phase
  report, with release records excluded by their own file names, which is why `v1.8.0`'s line read
  `0-29`. `test_the_state_line_of_the_rehearsal_sheet_names_the_phases_the_repository_carries` reads it
  now, with `sheet-state-line-names-a-superseded-phase` as its plant.
- **The version's own spellings are re-checked against the new release.** `pyproject.toml`,
  `CMakeLists.txt`, `CITATION.cff` (two version fields plus the release-notes URL), `uv.lock`, `README.md`
  and the compiled `quantrisk.version()` are one fact with seven spellings; Phase 30 built the guard, and
  this release is the first exercise of it at a version change.

## What was re-run, and what was deliberately not

The obvious release chore is to re-run every measurement so the artifacts "belong to" the new version.
This release re-runs only the artifacts whose provenance the lane actually binds to the running version,
and says why for the rest.

No engine or algorithm file changed between `v1.8.0` and this tag -- the diff quoted above is empty, and
Phases 31–58 touched CMake, CI, docs, tests and `scripts/`. Four things record the version as a fact the
lane compares: the C++ reference tool's JSON (bound by `test_version_matches_the_compiled_core`, so the
dev build was reconfigured and rebuilt), and the artifacts of `experiments/fourth_order_crossing_map/`,
`experiments/restrike_gamma_map/` and `experiments/real_data_risk_study/` (bound by
`test_the_provenance_is_recorded_once` and by the study's own oracle-isolation test, both of which require
the recorded `quantrisk` package version to equal the interpreter's). Those were re-run at `1.9.0`, and
the re-run is a re-provenancing rather than a new result, proved rather than asserted: with the
`environment` block, the `generated_*_utc` stamps and the study's duplicated `oracles.versions` mirror
removed, each of the three payloads compares **equal** to the bytes it replaced.

One thing about that re-run belongs in the record rather than being smoothed over. Getting the extension
rebuilt with `uv pip install --reinstall -e .` silently resolved `numpy` to `2.5.4`, one patch above the
`2.5.3` that `uv.lock` pins -- so the first artifacts written at `1.9.0` carried a package set the lock
does not describe. `uv sync --extra oracles` restored the pinned environment and the three artifacts were
run a second time; every number above comes from that second set. The general point is this repository's
own: an environment that drifted is a provenance fact, and a release that does not say so has published a
measurement whose producing environment cannot be re-derived.

What was *not* re-run is the performance measurement, and that is the part a reviewer should test. The
speed benchmark is volatile by declaration -- the freeze certifies nothing about it, and its 22 committed
readings exist precisely because it moves -- so re-running it would replace a published number with one
fresh reading of the same computation. During the preparation of this release the benchmark was in fact run
four times on unchanged engine code, and `speedup_vs_pure_python` returned 9.60, then 7.32, then 8.09, then
7.69 from a complete suite run; the published band's lower edge is 7.77. Three of those four were taken
while `numpy` had drifted to `2.5.4` (next paragraph), which is a further reason not to treat any single
one as *the* `1.9.0` measurement. Committing one of them would widen or move a band edge with no change in
the thing measured, so the instrument's published numbers stay as `v1.8.0` produced and the freeze
certified them, and the band this release publishes is the band it inherited. A reader who wants a `1.9.0`
performance measurement can take one -- §5 of `docs/reproducibility.md` prints the command -- and should
expect it to land inside the spread already documented, not to improve it. The evidence manifest was
rebuilt for the three re-provenanced artifacts, which is all the freeze can honestly say about a release
that measured nothing new.

## Verification at this release

Each line is the tool's own output for the revision this note ships with, run on one macOS/AppleClang
laptop; the runner's numbers are its own and are quoted in `docs/phase_reports/phase-59-v1.9.0.md`.

```text
.venv/bin/python -m pytest -q                            538 passed, 1 skipped in 178.76s
scripts/measure_offline_collection.py                    470 collected with the oracles-only packages blocked
ctest --test-dir build/dev                               100% tests passed out of 204
./build/dev/quantrisk_tests                              All tests passed (548368 assertions in 203 test cases)
.venv/bin/quantrisk validate                             7/7 checks passed
.venv/bin/ruff check .                                   All checks passed!
.venv/bin/ruff format --check .                          203 files already formatted  (one environment's walk; see the note below)
.venv/bin/mypy python/quantrisk                          Success: no issues found in 23 source files
clang-format --dry-run --Werror on cpp/                  exit 0
.venv/bin/python scripts/run_mutation_suite.py --list    172 plants declared
.venv/bin/python scripts/build_evidence_manifest.py      95 artifacts, 7,210,243 bytes
```

Two things that line does not say, and a third the formatter count hides:

- The skip is `test_the_release_date_the_citation_declares_is_the_tags_own`, which cannot check a tag that
  does not exist yet; it runs on the tagged tree. And the whole count pair -- 538 passing, 470 offline --
  is what the guards compare against, so the two numbers in "Counts" above are produced here, not typed.
- **The suite was not executed locally at this revision.** The benchmark lane is the CI job's, which runs
  `scripts/run_benchmark_suite.py --require-all` live on the runner, and the local `suite_run.json` is
  deliberately the one `v1.8.0` produced: re-running the suite would re-measure the performance benchmark,
  which is the number this release declines to refresh. The runner's line is quoted from its own job log in
  the phase report, not asserted here.
- A formatter file count is a walk of one environment at one moment, and finding 62(d) is this project's own
  record of a release note that published one from the wrong vantage. It is given here with its vantage
  named, and the release's gate evidence is the runner's own log for the same commit.

## Counts this release publishes

- 204 CTest entries, 548,368 assertions in 203 Catch2 cases, unchanged from `v1.8.0` because the core is
  unchanged.
- 539 pytest tests with the `oracles` extra installed and 470 collected without them; the four
  oracle-gated modules account for the difference as four skip records against the cases they hold.
- 19 benchmark-suite members, each executed against a live oracle under `--require-all`; at this revision
  that execution is the CI lane's, and its own summary line is quoted in the phase report. The frozen
  evidence manifest holds 95 artifacts, 7,210,243 bytes and 66 statistical experiment files.
- 107 numbered limitations in `docs/limitations.md`, 172 falsification plants, 7 identity checks, and
  204 / 539 as the sheet's own growth row against `v1.0.0`'s 190 / 330.

## Boundaries this release does not cross

No DOI and no PyPI publication, both deliberate. No claim of production readiness. The engine still has
no market data inside it. The limitations register is a statement of where the claims stop, not a queue:
every item in it carries the mechanism it asked for or the reason the mechanism was refused with its cost
named, and the two remaining steps that are not this project's to take -- minting a DOI, and publishing to
PyPI -- need the repository owner, not a phase.

## Publication record, appended 2026-10-26

The tag existed for six days before the release page did: Phase 59 cut `v1.9.0` and recorded the release
window as debt item 1, and it was published at the close of the V2 refactor lane. This section is the
post-publication record the note's own first paragraph said it could not contain, and it is appended rather
than folded into the sections above for that reason.

- **What was published.** `https://github.com/Jackxiaozhiren/quantrisk-plus-plus/releases/tag/v1.9.0`,
  release id `424060629`, published `2026-10-26T09:35:44Z`, not draft, not prerelease. The tag is annotated:
  the ref `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` peels to the commit `b2dda33f6726d7f36fbe3491aec7cd7a66184809`,
  which CI run `39410055875` verified `success`. The release commit `2441c5c` itself has no run -- it is the
  post-tag bookkeeping commit, and saying so is the point of this bullet rather than a caveat.
- **The body is the tag's own note, byte for byte.** `git show v1.9.0:docs/release_notes_v1.9.0.md` is
  12,473 bytes, sha256 `2e0101ca64a14fec2234d0f7c2ed27fcbe3a9c05f9a3b82fde09ea8afd09d14a`; GitHub stores it
  with one further trailing newline, 12,474 bytes. That published text is saved as
  `docs/release_bodies/v1.9.0-body-2026-10-26.md` (12,474 bytes, sha256
  `4b3da82fa4232a27aa5cb15970c8915224628cc0957a1206c40c5eacece73ccf`), which is the bytes a reader would
  need to restore this page to what it is now.
- **Assets, built from the tag and proved up and back.** Each of the four was extracted with
  `git archive v1.9.0` into a scratch directory, and every extracted file's `git hash-object` was first
  compared with `git rev-parse v1.9.0:<path>` -- seven files, all equal, so what went up is the tag's own
  bytes and not this laptop's working tree. They were hashed on the way up, and GitHub's own recorded
  `sha256:` digest for each asset matches that hash; all four were then downloaded back and re-hashed to the
  same values.

  | Asset | Bytes | sha256 |
  |---|---|---|
  | `CITATION.cff` | 2,978 | `1b9aee9fc9229ce11e9676b8b49de820b6250801314f1f7f3b36a69aea0fca5b` |
  | `manifest.json` | 55,780 | `97aa659e78df2893b3125aebe8b39308f17112aa7f9d20180f9d4fd975c392ca` |
  | `technical_report.pdf` | 1,005,786 | `7d8336f86cfb55c6d8856799cf9b60766f89cad49ad58004d807696f6cb138d6` |
  | `quantrisk-suite-results.zip` | 145,672 | `c96e6053402ff00e0f0193ea01fbacb3ea050dd10b77d25a1009d3d4835e5569` |

  The zip holds the four suite roll-up files, as every release since `v1.4.0` has, written with the tag
  commit's own timestamp so two builds of it produce the same bytes.
- **What the assets are not.** `technical_report.pdf` here is the PDF the tag carries, not the one the
  current head renders: the refactor lane has re-rendered the report seven times since `v1.9.0` was cut, and
  its head-of-tree copy hashes differently. A reader who wants the report that describes the refactor should
  build it from the tree, which `docs/reproducibility.md` explains; this page is the release of the revision
  the tag names, and nothing here pretends to be later than that.
