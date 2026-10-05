# Phase 22 — `v1.7.0`: the release, and the two things only the runner could see

The last registered debt item. Everything it needed was already true of the tree — order five shipped and
measured, the whole core surface marked, the counts owned — so this phase is mostly the release procedure
itself: version, provenance, the frozen evidence, the assets, and the accounting a tag cannot carry in its
own note. It went red twice on the way, both times only on CI, and both of those are in
`docs/integrity_audit.md` finding 54 rather than being smoothed over here.

## 1. Completed

- **Version moved to `1.7.0`** in the three places that carry it (`CMakeLists.txt`, `pyproject.toml`,
  `CITATION.cff`, including its `date-released` and release-notes URL), with `uv lock` refreshed so
  the lock file's own project entry agrees. The Python/C++ consistency test is what proves the two sides
  still say the same thing: `quantrisk.version()` == the reference tool's compiled string.
- **The whole suite re-executed on the new version** (`--require-all`, 18/18), because the artifacts
  record the version that produced them and the manifest compares against the installed one. That is the
  second full-suite run since Phase 21's, and its `8 CHANGED` result is examined in §6 rather than
  assumed.
- **Prose that quotes a moving number was re-synced last**, in the same commit as the plant re-keys: the
  performance figures (`8.45×` / `0.471×`, `44,549,572` paths/s against the loaded desktop's
  `21,130,162`), the README quick-start transcript (`quantrisk.version()  # '1.7.0'`, which is a guard,
  not a comment), the offline-lane test count in `docs/limitations.md`, and the report's tag list (eight).
- **`docs/release_notes_v1.7.0.md`** — what the release adds, what it corrects in itself, verification in
  the tools' own words, and what is still not here.
- **Finding 54** recorded, with the leaf-by-leaf evidence that no statistical result moved.

## 2. Mathematical assumptions

None added. This phase changes no numerics: the artifacts re-run under the same seeds and the same
kernels, and the claim being verified is exactly that — see §6.

## 3. Files changed

| File | Change |
|---|---|
| `CMakeLists.txt`, `pyproject.toml`, `uv.lock`, `CITATION.cff` | version 1.6.0 → 1.7.0, lock entry, citation date and release-notes URL |
| `docs/release_notes_v1.7.0.md` | new release note |
| `benchmarks/**/results/*`, `experiments/**/results/*` | re-executed by the authoritative `--require-all` run on 1.7.0 |
| `README.md` | quick-start version transcript, the current performance figures |
| `docs/interview_defense.md`, `docs/reproducibility.md` | the same performance figures and totals, the offline-lane count |
| `docs/limitations.md` | the offline-lane sentence no local guard reached (408) |
| `docs/integrity_audit.md` | the Phase 22 addendum, finding 54 |
| `paper/technical_report.tex`, `paper/technical_report.pdf` | eight tags, the 1.7.0 speed table; PDF rebuilt at 44 pages, 1003093 bytes |
| `tests/python/test_fifth_order_crossing_map.py` | bit equality → the documented 1e-12 cross-platform slack, with the measured Linux/darwin gap named |
| `scripts/run_mutation_suite.py` | the speedup plant re-keyed, and the sums plant widened so the slack cannot absorb it |

## 4. The release procedure, and where it is easy to lie

`CONTRIBUTING.md` §4 fixes the order because each step invalidates the one before it. Two parts of it are
worth restating here because this phase is where they bite:

- **The tag must be the revision CI verified, not a later one.** So the release commit, the sweep on it,
  the CI verdict, and then the tag — in that order, with the tag pointing at a commit whose run the API
  has described. `gh run watch` is not the verdict (finding 36).
- **Assets come from `git archive <tag>`, not from a working tree**, and each one is hashed on the way up
  and again after being downloaded back. A working tree can contain a file the commit does not; the
  archive cannot.

And one thing the procedure cannot contain, which is why §7 exists: a release note cannot describe its own
publication, the manifest cannot carry its own hash, and a table of post-tag runs cannot hold the verdict
of the commit that adds the table.

## 5. Exact test results

```text
uv run python scripts/run_benchmark_suite.py --require-all   18/18 executed and passed, 0 failed,
                                                             0 skipped, 158.7 s total
uv run pytest tests/python -q                                477 passed in 70.43s
uv run ctest --preset dev                                    100% tests passed out of 204 (9.57 s)
./build/dev/quantrisk_tests                                   All tests passed (548368 assertions in 203 cases)
uv run quantrisk validate                                    7/7 checks passed
uv run ruff check .                                          All checks passed!
uv run ruff format --check .                                 148 files already formatted
uv run mypy python/quantrisk                                 Success: no issues found in 23 source files
uv run clang-format --dry-run -Werror <4 files>               exit 0
uv run latexmk -pdf paper/technical_report.tex               44 pages, 1003093 bytes
uv run python scripts/run_mutation_suite.py --list           34 plants declared
```

The CI lane that runs without the `oracles` extra is where two of the three defects below surfaced; its
own lines are quoted in §9 once the run has reported them.

## 6. Numerical validation

The question this phase has to answer is whether a release that changes no numerics actually changed no
numerics. After the bump, `verify_evidence_manifest.py` reported `71 OK / 8 CHANGED / 15 VOLATILE / 0
MISSING / 0 unlisted`, and "result content differs" is a sentence worth checking rather than accepting:

- every differing leaf in all eight files was enumerated: timestamps, `quantrisk_version`,
  `git_commit`/`binary_git_commit`, `uncommitted_paths`, the `provenance` sentence, one sibling CSV's
  hash, and wall-clock columns;
- the two CSVs whose hash moved were re-parsed with `runtime_seconds`, `paths_per_second` and
  `seconds_per_path` removed — 24 and 36 rows respectively, identical to the committed ones;
- the `VOLATILE` bucket is the tool's own word for "re-ran, results identical", and 15 files landed there
  without a result leaf moving.

So the release is numerically inert, and finding 54(c) records that the verifier's `CHANGED` label
overstates a provenance-only move.

**Two real defects, both CI-only, both now fixed.** A bit-for-bit comparison of a book sum against one
recomputed from the bindings held on darwin and failed on Linux by `1.5e-15` relative — the last bits of
`libm`, which this repository's own reproduction rule already handles with `1e-12` slack; the test now
asserts the slack it documents, and the plant aimed at it was widened so the slack cannot swallow a real
error. And `docs/limitations.md` carried a fourth phrasing of the offline test count that no pattern
matched, so it said `396` while three other documents had been moved to `408`; the offline lane on CI is
the only environment that could notice.

## 7. Remaining limitations

Unchanged by this phase in substance, restated where a reader of a release note will look: no oracle for
the higher orders, a radius is a grid label, five books twice over, the amount of the map's error
untouched (16.2 % off at published scale after the quartic), the derivation script outside CI because
`sympy` is not a dependency, and the assertion/case totals owned by prose rather than by a build query.

## 8. Technical debt

1. **`verify_evidence_manifest.py` should separate provenance from result.** It already classifies
   VOLATILE; the `CHANGED` bucket mixes "a number moved" with "the commit this ran on moved", and the fix
   is a third bucket or a per-file leaf report, not a re-label.
2. **`sympy` in the `dev` extra** so the derivation script's part A runs in CI — the same shape as the
   four oracle-gated modules, with a skip when absent.
3. **A sixth book** for the radius, checked against the published per-column distances rather than retold.
4. **Cross-platform assertions need the slack in the assertion.** Finding 54(a) is the first time this
   repository's own `1e-12` rule was violated by a test written in the phase that documents it; a cheap
   guard could be a test that greps for `== ` between two floats computed on different sides of the
   bindings, though the false-positive risk is real and it is not obvious the guard would pay for itself.

## 9. Gate

The release commit carries the version, the re-executed artifacts, the synced prose and this report. The
falsification sweep runs on it after it exists — the harness refuses a dirty tree — and the paragraph
recording its verdict, the CI run identifiers, the tag and the asset hashes are appended in the commit
that follows, which is the only place they can honestly live.

The sweep ran on `e86c29f`, the commit that carries the version, the re-executed artifacts and the
frozen manifest, with `git status` empty before and after it. Its own line:
`34/34 planted defects were rejected by their guard.` The plant this phase widened fired ---
`artifact-publishes-a-book-sum-the-core-does-not`, a digit flipped four places into a mantissa, which the
`1e-12` slack of finding 54(a) leaves far outside tolerance --- and so did the two the previous phase
retargeted.

**The tagged revision, read from the API after the fact.** `v1.7.0` is an annotated tag object
`5ef9e125980607db65c91b9b118506a432098739` on commit `79d536a16eeb`, and that commit's check-run table
says `{"jobs": 3, "all_success": true}` for the three CI jobs (`Format and static checks`,
`Configure, build, C++ tests, Python tests`, `Benchmark suite against live oracles`), with SonarCloud
`neutral` as on every prior head. The GitHub release is `publishedAt 2026-10-04T06:46:51Z`,
`isDraft: false`, `isPrerelease: false`, with four assets whose sizes the API reports as
`1003093 / 55188 / 2493 / 144544` bytes.

**Assets were built from the tag, and the digests match in both directions.** `git archive v1.7.0`
exported into a clean directory and the four files were hashed there, then downloaded back from the
release and hashed again; all four agree: `technical_report.pdf` `99d1c108…`, `manifest.json`
`e3f7418d…`, `CITATION.cff` `f6ccac70…`, `quantrisk-suite-results.zip` `84675cb5…`. The zip carries the
four suite-roll-up files, as every release since `v1.4.0` has.

**What the record still cannot contain.** This commit is after the tag, so the tag does not carry it: the
release note cannot describe its own publication, the manifest cannot hash itself, and the four commits
between `v1.6.0` and this tag were frozen before the tag existed. The CI run that verified `79d536a` is
the release's evidence; the runs on the post-tag record commits are reported in the next paragraph, and
nothing in this file asserts a run it has not read.

`RANGE_DOCUMENTS` gained `docs/release_notes_v1.7.0.md` in this commit, which is the guard that makes
the note's `7.77×–8.70×` / `0.42×–0.51×` claim an owned one rather than a remembered number.

**The heads after the tag, read from the API on 2026-10-05.** This is the paragraph §9's penultimate
sentence promised and did not write -- a record that says a verdict appears next and then does not print
it is the same defect class Phase 23 found in the report, caught here in this file. Each head's own
check-run table, all three CI jobs, with SonarCloud `neutral` as on every prior head:

| head | what it changed | run | verdict |
| --- | --- | --- | --- |
| `3193e6d` | the release's own facts: tag object, asset digests, publication time | 37185206784 | `success` — three jobs |
| `dca2907` | `docs/project_scope.md` §9 and the interview state line brought from Phase 14 to Phase 22 | 37189251814 | `success` — three jobs |
| `8680d63` | Phase 15's report reconciled to the nine mandated headings | 37256005548 | `success` — three jobs |
| `88a4c80` | Phase 23: the report's prose corrected, four guards, finding 55, limitation #84 | 37258779954 | `failure` — `Configure, build, C++ tests, Python tests`; the other two `success` |
| `4fb43c2` | the offline test count taken from that red lane's own message (408 → 412) | 37259933573 | `success` — three jobs, offline line `411 passed, 5 skipped` |

`88a4c80`'s failure is the substance of finding 55(d) and Phase 23 §5: four added tests moved the
with-oracles count and the offline reading in four documents did not move with it, and only the lane
without the oracles could say so. The head this paragraph is committed under is the sixth head after the
tag, and its own run cannot be recorded in the file that records it; read it with
`gh api repos/Jackxiaozhiren/quantrisk-plus-plus/commits/$(git rev-parse HEAD)/check-runs`, which is the
same command that produced every row above.
