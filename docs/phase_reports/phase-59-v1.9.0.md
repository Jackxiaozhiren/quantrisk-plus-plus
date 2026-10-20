# Phase 59 — `v1.9.0`: the release that gave two published numbers their missing producers

Date: 2026-10-20. Predecessor: Phase 58 (`docs/phase_reports/phase-58-a-text-link-for-every-plant-and-a-named-residual-for-the-one-that-has-none.md`). This phase cuts a release, so its plan is `CONTRIBUTING.md` §4's fixed order: gates → prose synced last among regenerations → falsification anchors re-keyed in the same commit → commit → sweep re-run on the committed tree → tag the commit the runner verified → assets built from `git archive <tag>` and hashed up and back → state what the record cannot contain.

## 1. Completed

- **`v1.9.0` is tagged at `b2dda33`**, the commit the runner verified from its own three job logs.
  Twenty-eight phases sit between `v1.8.0` and this tag and **not one of them changed a line of the
  engine**: `git diff --stat v1.8.0..HEAD -- cpp include python/quantrisk` prints nothing. The release
  is therefore a release of instrumentation, and the note says that in those words.
- **`CITATION.cff`'s limitation count got an owner, after four releases of shipping a false one.** The
  abstract read "55 numbered limitations" from before `v1.5.0` to this commit while the register passed a
  hundred. The citation file is one of the four assets a release attaches, so the number was
  downloadable, citable, and read by no guard -- `test_documents_that_count_the_limitations_agree_with_the_file`
  had been describing exactly this failure mode in its own docstring since Phase 10 without covering this
  file. It is now in the claim set, with `citation-understates-the-limitation-register` as its plant. The
  file's header comment, which asserted both that no remote existed and that "every other field is true as
  written", was corrected for the same reason: it was a claim about its own truthfulness with no producer.
- **The rehearsal sheet's state line got the producer Phase 30 registered and nobody built.**
  "Phases 0–43 shipped" was current prose, fifty-eight phases deep, and drifted twice.
  `test_the_state_line_of_the_rehearsal_sheet_names_the_phases_the_repository_carries` now derives the
  bound from `docs/phase_reports/`, excluding release records by their file names -- the rule that made
  `v1.8.0`'s own line read `0-29`, stated rather than inferred -- and `sheet-state-line-names-a-superseded-phase`
  is its plant. This closes item 3 of `docs/phase_reports/phase-30-v1.8.0.md` §8, which was never carried
  into the register: the reason the queue looked empty and was not quite empty.
- **Three artifacts were re-provenanced at `1.9.0`, proved not to have moved.** The reference tool's JSON,
  `fourth_order_crossing_map`, `restrike_gamma_map` and `real_data_risk_study` record the package version
  where a guard compares it; each was re-run, and with the environment block, the timestamps and the
  study's duplicated `oracles.versions` mirror removed, every payload compares **equal** to the bytes it
  replaced. The freeze that follows holds 95 artifacts over 7,210,243 bytes.
- **The performance benchmark was deliberately not refreshed**, and the decision is a measurement rather
  than a preference: four runs on unchanged engine code returned 9.60, 7.32, 8.09 and 7.69 for
  `speedup_vs_pure_python` against a published lower edge of 7.77. One point is not evidence about the
  thing measured, so the band this release publishes is the band it inherited, and the note says so.
- **172 plants declared, and the sweep's verdict on the tagged tree is section 5's own line.**

## 2. Assumptions this rests on

- A release may carry artifacts produced by the previous version when nothing in the engine changed,
  because an artifact's `environment` block names the build that produced it. The corollary is the part
  that needs care: the four artifacts whose recorded version a guard *does* compare must be re-run, and
  re-running them is a provenance act whose measurement content has to be checked, not assumed.
- `binary_git_commit` in the freeze says the core was configured at `5dff42a`, the checkout before the
  release commit. The bytes are the release's -- the CMake version moved and the extension was rebuilt --
  and the field reports the checkout it was built from, which is the disclosure Phase 30's artifacts made
  the same way.
- The tag cannot be verified by the commit that plans it, and the sentence naming it cannot be green
  before it: `test_the_report_lists_the_release_tags_the_repository_carries` compares the report's
  enumeration with `git tag --list "v*"`, so between the release commit and the tag it is red, and this
  release's runner happened to be green because the report still named nine tags at the tagged revision.
  The accounting commit that names ten is this file's own commit.
- A formatter file count is one environment's walk. `ruff format --check .` printed 203 locally and 203
  on the runner for this commit, which is agreement, not ownership: finding 62(d) is this repository's
  record of a release note that quoted one from the wrong vantage.

## 3. Files changed

| File | Change |
|---|---|
| `pyproject.toml`, `CMakeLists.txt`, `CITATION.cff`, `uv.lock` | `1.8.0` → `1.9.0`; the citation also moves its release-notes URL and `date-released: 2026-10-20`, and its header comment stops claiming a remote is absent |
| `docs/release_notes_v1.9.0.md` | new; the published body, the re-run policy and its evidence, and the local gate block with its vantage named |
| `tests/python/test_artifact_metadata.py` | the citation file joins the limitation-count claim set; `test_the_state_line_of_the_rehearsal_sheet_names_the_phases_the_repository_carries` added; census gold lists and the manifest byte total moved |
| `scripts/mutation_plants.py` | two plants added (170 → 172), five anchors re-keyed by this phase's own count and date syncs, one stale comment corrected |
| `README.md`, `docs/interview_defense.md`, `docs/reproducibility.md`, `docs/limitations.md` | version spellings, the 539/470 pair, the 172/172 sweep annotation, the sheet's state line |
| `experiments/{fourth_order_crossing_map,restrike_gamma_map,real_data_risk_study}/results/*` | re-provenanced at `1.9.0`; measurement content proved identical to the replaced bytes |
| `paper/technical_report.tex`, `.pdf`, `.build.json` | counts and the manifest block; PDF rebuilt (bundle `30c75955f3ca`, PDF `7d8336f86cfb`), then the tag enumeration after the tag existed |
| `evidence/manifest.json` | rebuilt from the release commit and committed separately, so the freeze describes a revision that exists |

## 4. What the phase learned, including about its own plan

**The release is where an unowned number is guaranteed to be found.** Every other phase adds a number
next to the guard that owns it; a release moves a number that is spelled seven times, and Phase 30 built
the guard for exactly that. Two of this release's three corrections are numbers that had been stale for
releases -- the citation's `55`, the sheet's `0-43 -- and both were found by reading the documents that
carry claims rather than by a gate.

**"The guards are green" is not the same as "the queue is empty", and the difference lived in a phase
report.** Yesterday's completion audit enumerated the register and found nothing actionable; it did not
read §8 of the previous twenty-nine reports. Phase 30's item 3 was there, unregistered and unexecuted.
The generalisation is the project's own, aimed at itself: a debt list that lives in one artefact while
another artefact claims to answer the question is two lists.

**A re-run chosen for tidiness has to be measured, or it is a new result in disguise.** Re-provenancing
three artifacts took two rounds because the first round's environment had drifted -- `uv pip install
--reinstall -e .` resolved `numpy` to `2.5.4`, one patch above the lock -- and the artifacts wrote that
into their provenance. `uv sync --extra oracles` restored the pinned set and they were run again. The
lesson is the one #77 and finding 44 already carry, in a form that bit here: an environment nobody
inspected is not the environment the documents describe, and `--reinstall` is not a no-op.

**Declining to re-measure is a claim that needs the readings, not the reasoning.** It would have been
easy to write "the performance number is volatile, so we left it alone". What makes it a decision rather
than an omission is the four values, one of which -- 7.32 -- would have widened a published band on a
machine that was not idle. Publishing that as `1.9.0`'s measurement would have been the smoothing this
project keeps removing.

**Tagging changed the shape of the sequence, not just its end.** Because Phase 33 gave the runner tags,
the release-tag enumeration now runs there, which means the sentence naming `v1.9.0` cannot live in the
commit the tag points at: it would be red on the very runner that certifies the tag. So the release
commit, the freeze, the tag and the accounting commit are four steps in that order -- and the rebase onto
two Dependabot commits that landed mid-phase is why the freeze had to be taken twice: a manifest naming
a sha that never reached `main` is a provenance record pointing at nothing.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 203 files already formatted, on this tree and on the runner's own log for the tagged commit |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --test-dir build/dev` | 100% tests passed out of 204 |
| Catch2 | `./build/dev/quantrisk_tests` | All tests passed (548368 assertions in 203 test cases) |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | `Evidence is intact.` -- 95 OK, 0 CHANGED, 0 VOLATILE, 0 MISSING |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | `470 tests collected`, exit 0 |
| Python | `.venv/bin/python -m pytest -q` | 538 passed, 1 skipped at the release commit `b2dda33` -- the skip was `test_the_release_date_the_citation_declares_is_the_tags_own`, which cannot check a tag that did not exist yet; on this accounting commit, with `v1.9.0` in the object store, the same command prints `539 passed`, no skips |
| Falsification, this phase's plants | `run_mutation_suite.py --all --only <the three>` | 3/3 planted defects rejected by their guard |
| Falsification, full sweep | `.venv/bin/python scripts/run_mutation_suite.py --all` | pending at the tagged tree -- this row is filled from the run's own line |
| CI on the tagged head | read from each job's own log | run `39410055875` on `b2dda33`: `All checks passed!` + `203 files already formatted` + `Success: no issues found in 23 source files`; `100% tests passed out of 204` and `468 passed, 6 skipped in 131.83s`; `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 422.6s total`. Reconciliation under #91: 468 + 6 = 474 = 470 collected offline + 4 |

## 6. Numerical validation

| Figure | Value | Producer |
|---|---|---|
| Engine diff between `v1.8.0` and this tag | 0 lines in `cpp/`, `include/`, `python/quantrisk` | `git diff --stat v1.8.0..HEAD` |
| Artifacts whose bytes moved | 4 (3 experiments re-provenanced, 1 PDF rebuilt) | the freeze's own `CHANGED` list before the re-freeze |
| Measurement content of the re-run artifacts | identical, key by key | `build/phase59-*` comparison of `git show HEAD:` against the working file |
| Same-day `speedup_vs_pure_python` readings on unchanged code | 9.60, 7.32, 8.09, 7.69 | four runs of the performance benchmark, none committed |
| Published bands, unchanged | `7.77×–10.31×` (32.6 %), `0.42×–0.51×` (20.8 %) | the committed history of the speed artifact |
| Freeze | 95 artifacts, 7,210,243 bytes, 66 statistical experiment files | `scripts/build_evidence_manifest.py` at the release commit |
| Plants / lane | 172 declared, 539 collected and 539 passing at this accounting commit | `--list` and the lane; no skip remains because `v1.9.0` now exists |
| Register entries | 107, unchanged; no item opened by this phase | `docs/limitations.md` |

## 7. Remaining limitations

- The version guard owns seven spellings of the version and now two of the citation's numbers; it does
  not own the *asset* text on the release page, which is corrected the way `v1.7.0`'s was -- by a dated
  erratum on the body, never by moving a tag.
- `docs/limitations.md` #101, #102, #106 and #107 remain what they say they are: boundaries of what a
  guard can check. The seeing-versus-causing gap in the pairing audit is still priced at 156 runs and
  still refused.
- The suite's own artifact at the tagged revision is the runner's, not a laptop's; a reader who wants a
  local `1.9.0` execution gets a different wall time and, for the performance member, a different ratio.
  That is the documented volatility of #77, not a defect of this release.
- Nothing yet checks that a phase report's §8 items are all discharged. This phase found one that was
  not, by reading. The reason no entry is opened for it is the same as #107's: the mechanism would be a
  parse of prose into a queue, and what it would catch is a phase author not finishing a sentence -- which
  the register's own "residue with its cost named" rule is trying to make unnecessary.

## 8. Technical debt registered here

Nothing opened. Two items were *closed* that had never been in the register at all -- Phase 30's §8 item
3 (the state line's missing owner) by building its guard, and the citation file's unpoliced numbers by
joining the claim set that already existed. The register holds 107 limitations, no actionable item, and
this release adds no new claim that a producer cannot disagree with.

## 9. The gate

What a release phase can honestly say about itself is bounded by its own order: the tag cannot be in the
commit that plans it, the freeze cannot hash itself, and the note cannot describe its publication. Three
commits and one tag carry this release -- the release commit, the freeze rebuilt from it, the tag at the
revision the runner verified, and this accounting commit that names the tag the earlier three could not.
`0.00` was spent: the oracles are local wheels, the runners are the repository's own free hosted minutes,
and the one network operation with a cost, a FRED fetch, was not used.
