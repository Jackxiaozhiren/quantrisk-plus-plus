# Phase 30 — `v1.8.0`: the release, and the last number in the tree with no producer

Date: 2026-10-09. Predecessor: Phase 29 (`docs/phase_reports/phase-29-markdown-inventory.md`).
This phase cuts a release, so its plan is `CONTRIBUTING.md` §4's fixed order rather than an experiment
design: gates → sync prose last among regenerations → re-key the falsification anchors in the same commit
→ commit → re-run the sweep on the committed tree → tag the commit the runner verified → build the assets
from `git archive <tag>` and hash each one on the way up and again after downloading it back → state what
the record cannot contain.

## 1. Completed

- **The version string gained the ownership every other figure in this tree already has.** `v1.8.0` is
  spelled in `pyproject.toml`, `CMakeLists.txt`, `CITATION.cff` (twice, plus the URL of its release-notes
  page), `uv.lock`, `README.md`, `docs/interview_defense.md` and the compiled `quantrisk.version()`. The
  only guard that existed paired the interpreter with the packaging file.
  `test_the_version_string_the_project_declares_is_one_number_not_four` now reads all seven with patterns
  that must match, requires the citation's tag URL to name `v` + the version, and matches the two prose
  quotations as *phrases* (`quantrisk.version()  # '1.8.0'`, `` `quantrisk` 1.8.0, released as the tag
  `v1.8.0` ``) because `1.8.0` also occurs inside tag names and paths. Its plant is
  `citation-declares-a-version-the-package-does-not`.
- **The release-body digest guard stopped pointing at one hardcoded file.** `RELEASE_NOTE` named
  `docs/release_notes_v1.7.0.md`, which put the note being written *now* outside its own protection; the
  guard reads every `docs/release_notes_v*.md`, so a snapshot cited by no note fails and one cited by
  several must satisfy each.
- **The release was cut.** Version moved in the four declaration sites and the lock; every producer
  re-ran (the bump invalidates every artifact through `environment.quantrisk_version`); the prose synced
  after the producers, not before; the phase committed as `cb5157a`, the freeze rebuilt from that commit
  and committed as `f181427`; CI verified `f181427`; the annotated tag `v1.8.0` points at it; the four
  assets were built from `git archive v1.8.0`; the release is published.
- **A falsification sweep of 53 plants runs green on the tagged tree**, with `git status` empty after it.

## 2. Mathematical assumptions

Nothing in this phase changes an assumption. The release carries Phase 28's crossing-radius rule and its
grid bound (#88) unchanged, and the order-five identity Phase 24 gated (`8.7e-58` at 60 working digits) is
re-executed by the lane rather than re-quoted. Two facts about *verification* are worth stating because
the release procedure depends on them:

- A release's own tag sentence cannot be verified by the commit that makes it. The report now enumerates
  nine tags including `v1.8.0`; `test_the_report_lists_the_release_tags_the_repository_carries` compares
  that enumeration with `git tag --list "v*"`, so it is red between the prose edit and the tag, and it
  *skips* (not passes) on the runner, whose checkout is depth 1 and carries no tags at all.
- A re-frozen volatile artifact is a documentation edit in disguise. `speedup_vs_pure_python`,
  `speedup_vs_numpy` and `results_seconds` are volatile by declaration, so the freeze certifies nothing
  about them and the seven documents that print them are checked against the file, not against each other.

## 3. Files changed

| File | Change |
|---|---|
| `pyproject.toml`, `CMakeLists.txt`, `CITATION.cff`, `uv.lock` | `1.7.0` → `1.8.0`; `CITATION.cff` also `date-released: 2026-10-09` and `release-notes: …/tag/v1.8.0` |
| `docs/release_notes_v1.8.0.md` | new; the published body, and now a `RANGE_DOCUMENTS` member, so the band it prints is policed |
| `tests/python/test_artifact_metadata.py` | the version guard; the digest guard reads every release note; `import tomllib`; `RANGE_DOCUMENTS += docs/release_notes_v1.8.0.md` |
| `scripts/run_mutation_suite.py` | plant `citation-declares-a-version-the-package-does-not` (52 → 53 declared); five anchors re-keyed by this phase's own count syncs |
| `README.md`, `docs/reproducibility.md`, `docs/interview_defense.md`, `docs/validation_matrix.md` | pytest pair 497/428 → 498/429, register 89 → 90, sweep annotation 52/52 → 53/53, point figures and bands |
| `docs/limitations.md` | #90 added (the committed report PDF has no freshness owner) |
| `docs/release_notes_v1.3.0.md`, `v1.4.0.md` | register count re-synced — both are living quotations of the file's size, per the guard that reads them |
| `docs/release_notes_v1.5.0.md`, `v1.7.0.md` | the twenty-two-measurement band and its point figures, carried forward from the producers that ran before this commit |
| `paper/technical_report.tex`, `paper/technical_report.pdf` | counts, register size, the nine-tag enumeration; PDF rebuilt at 45 pages, 1,005,768 bytes |
| `benchmarks/**/results/*`, `experiments/*/results/*` | regenerated by the version bump; `suite_run.json` totals 19/19 in 238.4 s |
| `evidence/manifest.json` | rebuilt from `cb5157a` and committed separately, so the freeze describes a revision that exists |

## 4. The last unowned number, and the guards that were themselves one release behind

(a) **The release's own headline figure had no owner.** Ask "who can disagree with `1.8.0`?" and the
answer, until this phase, was "a human comparing files". The mechanism is the one finding 55 records --
one fact, several spellings, one spelling compared -- and it survived here because the version is the
rare number that changes only at a release, which is the one moment nobody is reading the guards. The
asset side makes it concrete: `CITATION.cff` is uploaded to the release page, so a citation naming the
previous version would be downloadable and citable by a reader while every gate stayed green.

(b) **The guard that polices release-body digests was pinned to one release note.** A constant pointing
at `v1.7.0` protected `v1.7.0`'s snapshots forever and the note being written now never. The fix is not
to repoint the constant -- that just defers the same defect to `v1.9.0` -- but to read the set.

(c) **Three plant anchors were disarmed by this phase's own regeneration, and a fourth was already
disarmed at `HEAD`.** The count syncs (497 → 498, 428 → 429, 89 → 90, 52 → 53 plants) and the re-freeze
(`7{,}238{,}399` → `7{,}211{,}281` bytes) broke the anchors of
`report-counts-stale-python-tests`, `report-quotes-a-count-the-offline-probe-refutes`,
`report-counts-a-manifest-the-freeze-does-not-have`, `interview-doc-overcounts-the-offline-lane`,
`reproducibility-quotes-a-superseded-pytest-total`,
`docs-command-comment-counts-superseded-plants` and `readme-undercounts-the-limitation-register`. That is
finding 49's class, sixth occurrence, and the phase that has the most explicit rule about it. Two of them
were already disarmed when this segment began -- by the same phase's earlier regeneration, before any commit:
`49dc015` carries the report's `and 496 pytest tests…` and `oracles installed, 427 collected…` in agreement
with the plant list, and the counts moved to 497/428 then 498/429 with the tests this release added. The
reason nobody saw it is that `pytest tests/python/test_mutation_suite.py` asserts on **one** stale anchor
per run, so a phase that fixes the one it sees can still be holding disarmed plants at the end -- which is
how the enumeration, run in one pass, found the rest:

```bash
uv run python - <<'PY'   # every declared anchor, exactly once, in the file it names
import importlib.util, pathlib, sys
spec = importlib.util.spec_from_file_location("rms", "scripts/run_mutation_suite.py")
m = importlib.util.module_from_spec(spec); sys.modules["rms"] = m; spec.loader.exec_module(m)
for mut in m.MUTATIONS:
    p = pathlib.Path(mut.path)
    if not p.is_file():
        print("MISSING", mut.identifier, mut.path); continue        # the two tree probes write theirs
    n = p.read_text(encoding="utf-8", errors="replace").count(mut.anchor)
    if n != 1:
        print("STALE", mut.identifier, n, repr(mut.anchor[:60]))
PY
```

The `sys.modules` line is not decoration: loading the harness by path without registering it makes
`@dataclass` fail inside `dataclasses._is_type` on both 3.12 and 3.14, which is a confusing error for a
one-line inspection tool.

(d) **A `sha256` the note cites is only comparable because the asset came from the archive.** The phase
hashed the staged `CITATION.cff` asset and the repository file with `shasum -a 256`; both read
`061f61aa7958…`, and that agreement is *evidence*, not coincidence: `git archive v1.8.0` was extracted to a
scratch directory and each archived file's `git hash-object` was compared with `git rev-parse v1.8.0:<path>`
before anything was uploaded. A working-tree build of the same name would have proved nothing about the tag.

(e) **The release note published a formatter count from the laptop, and the runner disagrees -- and the
laptop disagrees with itself.** Its verification block says `ruff format --check .` → "164 files already
formatted". The same command on a `git archive v1.8.0` export prints **165**, and CI's `Format and static
checks` job on `f181427` printed **165** at `2026-10-09T05:44:43Z`. This working tree printed **166**
minutes later, with the tracked file set unchanged at 82 `.py` files. So the figure is neither a census nor
a stable property of the code: it is this Ruff version's walk of one environment at one moment, and the
moment included the sweep's leftovers. Every other line in that block is a tool's output for the commit that
carries it, and this one is a tool's output for a different machine, so `docs/integrity_audit.md` finding
62(d) records it and a dated correction goes on the release. The number is cosmetic; the mechanism --
quoting a gate from the vantage nearest the typist -- is the one this project has been closing since
Phase 14.

(f) **The sweep leaves empty probe directories behind, and `git status` cannot see them.** Both `tree`
plants `unlink()` the files they create but not the directories, so after `53/53` the tree still holds
`experiments/_mutation_probe/results/`. `git status` reports clean because git does not track empty
directories. Recorded rather than patched here: the fix is two `rmdir`s in the harness, and the guard that
would notice its absence is the file-census item in §8.

(g) **`date-released` is a claim with no producer, and the phase says so instead of inventing one.** The
only event that can own a release date is the release. It is listed in §8 as reachable debt (the tag's own
commit date is the candidate producer, with the shallow-clone caveat the enumeration guard already carries)
rather than guarded by a proxy that would certify the wrong thing.

## 5. Exact test results

Every line below is the tool's own output, quoted from the run named.

| Gate | Command | Result |
|---|---|---|
| Python | `uv run pytest tests/python -q` | `498 passed in 82.08 s` on the tagged tree |
| Docs lane | `uv run pytest tests/python/test_artifact_metadata.py -q` | 51 passed on the tagged tree (`f181427` + `v1.8.0`); 1 failed / 50 passed on `cb5157a`, the failure being the pre-tag release-tag guard; 2 failed / 496 passed before the freeze commit, the second being the band-history guard waiting for the artifact to be in history |
| Offline lane | `uv run python scripts/measure_offline_collection.py` | `collected: 429`, `module_skips: 4`, `collection_errors: 0`, exit 0 |
| C++ tests | `uv run ctest --test-dir build/dev` | `100% tests passed out of 204` |
| Catch2 | `./build/dev/quantrisk_tests` | `All tests passed (548368 assertions in 203 test cases)` |
| Identity | `uv run quantrisk validate` | `7/7 checks passed` |
| Suite | `uv run python scripts/run_benchmark_suite.py --require-all` | `suite_run.json` totals: 19 members, 19 passed, 0 failed, 0 skipped, 238.4 s |
| Lint | `uv run ruff check .` / `uv run ruff format --check .` | `All checks passed!` / 164 files already formatted |
| Types | `uv run mypy python/quantrisk` | `Success: no issues found in 23 source files` |
| Format (C++) | `find cpp … \| xargs uv run clang-format --dry-run --Werror` | exit 0 |
| Report | `uv run latexmk -pdf paper/technical_report.tex` | 45 pages, 1,005,768 bytes; `pdftotext` reads `498 pytest tests with the validation oracles`, `429 collected without them`, `90 recorded limitations` |
| Freeze | `uv run python scripts/build_evidence_manifest.py` | 95 artifacts, 7,211,281 bytes, 66 statistical experiment files |
| Falsification | `uv run python scripts/run_mutation_suite.py` | `53/53 planted defects were rejected by their guard.`, `git status` empty afterwards |
| New guard's own red | plant `\nversion: 1.8.0` → `\nversion: 1.9.9` | `CITATION.cff states ['1.9.9', '1.8.0'] while the package is 1.8.0`; restored to sha `061f61aa7958…`, `1 passed` |

**CI on the pushed head.** Run `37889960064` on `f1814275453c2cb0bc69d1c86938ded6b5b5b9a5`:
`Format and static checks` success, `Configure, build, C++ tests, Python tests` success, `Benchmark suite
against live oracles` success, workflow conclusion `success`. A fourth check, `SonarCloud Code Analysis`,
reports `neutral` -- it is a third-party app that does not analyse this repository, and the honest verb is
"did not report", not "passed".

**Tag and release.** Annotated tag `v1.8.0` → `f1814275453c2cb0bc69d1c86938ded6b5b5b9a5`, pushed. Release
id `407572247`, published `2026-10-09T06:00:29Z`, not draft, not prerelease,
`https://github.com/Jackxiaozhiren/quantrisk-plus-plus/releases/tag/v1.8.0`. Its body is
`git show v1.8.0:docs/release_notes_v1.8.0.md` -- 11,163 bytes, sha256 `9407c4e3102e…`; the read-back is
11,164 bytes whose first 11,163 are identical, GitHub appending one newline, which is the same behaviour
Phase 27 recorded for `v1.7.0`.

**Assets, up and back.** Built from `git archive v1.8.0` into a scratch directory, with each archived blob
first proved equal to the tag's tree by `git rev-parse`/`git hash-object`:

| Asset | Bytes | sha256 on the way up | sha256 after downloading back |
|---|---|---|---|
| `technical_report.pdf` | 1,005,768 | `9ec5189ee029…` | `9ec5189ee029…` |
| `manifest.json` | 55,766 | `05b4d75b3da9…` | `05b4d75b3da9…` |
| `CITATION.cff` | 2,493 | `061f61aa7958…` | `061f61aa7958…` |
| `quantrisk-suite-results.zip` | 145,448 | `701f24346758…` | `701f24346758…` |

## 6. Numerical validation

- The speed artifact behind the tag reads `10.31×` versus a pure Python loop and `0.495×` versus
  vectorised NumPy (`39,040,079` vs `3,787,943` paths/s; NumPy `78,860,106`), generated
  `2026-10-09T04:54:37+00:00`. The committed history now holds 22 measurements, whose rounded min/max the
  band guard derives: `7.77×–10.31×` (32.6%) and `0.42×–0.51×` (20.8%). Three clean idle runs wrote
  `8.378×`, `8.877×` and `10.306×`; a fourth, contending with a second copy of the suite on 2026-10-08,
  wrote `4.01×` / `0.36×` and was restored rather than committed. All of that is in
  `docs/reproducibility.md` and #77 rather than smoothed into the headline.
- Counts: 204 CTest entries / 548,368 assertions / 203 Catch2 cases (identical to `v1.7.0`, which is what
  seven phases of prose plus one Python-side experiment should produce), 498 pytest tests with the
  `oracles` extra, 429 collected without, 7 identity checks, 19 suite members, 90 register entries, 53
  declared plants, 95 frozen artifacts.
- No new statistical claim is published. The release's measurement content is Phase 28's sixth book, whose
  artifact already carries the ratio (`0.002449039099104238`), the span it extends
  (`0.002449039099104238`–`0.5875865567378914` over six books), the radii (`0.2`/`0.3`/`0.3`), and the
  23-row ranking a guard re-derives.

## 7. Remaining limitations

- `docs/limitations.md` #90: the committed report PDF has no freshness owner. This phase rebuilt it and
  *read it back* with `pdftotext`, which is a human act; the class has now recurred twice (finding 55,
  Phase 24 §8).
- #89 stands: the claim inventory covers `paper/technical_report.tex`, `README.md` and
  `docs/reproducibility.md`. `docs/interview_defense.md` and `docs/validation_matrix.md` remain policed per
  figure.
- Release notes are dated records: their point figures are the run behind their own tag and no guard
  re-derives them. `docs/release_notes_v1.8.0.md` is therefore in `RANGE_DOCUMENTS` (the band is a claim
  about history, so it must move) but deliberately not in `PROSE_FIGURES` (the point figures must be
  allowed to age).
- Two guards are environment-blind on the runner and can only be proven where the clone carries history or
  tags: the band-history guard and the release-tag enumeration guard. CI's depth-1 checkout turns both
  into skips, so a plant keyed to the tag guard (`report-counts-release-tags-the-object-store-does-not-carry`)
  is meaningful only locally -- and CI does not run the sweep at all.
- `date-released` in `CITATION.cff` has no producer.
- The rules that held: no PyPI publication, no market data inside the engine, no production-readiness
  claim, no cost above zero, no failing test deleted, no tolerance quietly lowered, no contended or failed
  run removed from the record.

## 8. Technical debt this phase registers

1. **A freshness guard for `paper/technical_report.pdf`.** The cheapest implementable form compares each
   file's last-touch commit and requires the PDF not to predate the tex. It is real locally and vacuous on
   a depth-1 clone, so it must carry the declared-skip sentence the #77 and tag guards use, and its plant
   must be proven on a full clone. Do it against a real red (edit the tex, commit without the PDF) rather
   than by inspection.
2. **A producer for `date-released`.** `git log -1 --format=%ad --date=format:%Y-%m-%d v1.8.0^{}` is the
   release's own date; the guard would then compare the citation with the tag, and skip on a clone without
   tags. Same window as the enumeration guard, so it belongs with it, not in a separate lane.
3. **The state line of `docs/interview_defense.md` ("Phases 0–30 shipped") has no owner.** Nothing in the
   tree can disagree with it; the phase-report directory listing is the obvious producer.
4. **The inventory's two remaining documents** (#89) -- to be built against real reds, not by bulk
   exemption.
5. **`RANGE_DOCUMENTS` grows by one file every release that prints a band.** That is intended, but the
   list is hand-maintained; a release that forgets to add its note would leave that note's band claim
   unpoliced. A guard over "every document that prints a `×`-band is in the list" is the closure, and it
   needs the same enumeration discipline as §4(c).

## 9. The gate

The release is published and its record is this file. What the record *cannot* contain, stated because
CONTRIBUTING §4 requires it:

- The note's verification block is a snapshot of the run behind `f181427`. It cannot describe the act of
  publishing itself; the tag, the run id, the release id and the asset digests live here because the tools
  had said them before this file was written, and nowhere in the tagged bytes.
- The report's nine-tag sentence was red in `cb5157a` and green only after the tag. A reader who checks out
  the commit and runs the lane without tags sees a skip, not a pass. Both facts are in the guard's own
  docstring.
- The sweep ran on the tagged tree (`53/53`), not between the commit and the tag, because one plant is
  keyed to a guard that cannot be green before its tag exists. The sweep restores every file it edits and
  verifies each restore by sha, so the tree it ran on is the tree that was tagged; `git status` was empty
  both before and after.
- `0.00` dollars was spent. Nothing in this phase called a paid API: `gh` reads and writes GitHub, the
  oracles are local wheels, and the one network operation with a cost -- the FRED fetches -- was not used.
