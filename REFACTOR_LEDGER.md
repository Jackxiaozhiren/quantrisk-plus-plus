# V2 refactor ledger

This file is the refactor lane's working record. It is the first committed artefact of the lane, as
`REFACTOR_PROMPT.md` §7 step 8 requires: a later session resumes by reading it, re-running §7 step 4
first, and treating what is stored here as **history, not ground truth**. Every number below names the
command that produced it; none of them is a restatement of the prompt's prose.

Series status: V1 is `PROJECT_SPEC.md` (executed, locked by K3). This lane is V2, running beside it.

## 1. The revision this baseline was taken on, and the vantage

| Item | Reading | How it was produced |
|---|---|---|
| Revision | `7d4f656` (`Phase 59 record: …`), which descends from the release commit `2441c5c`, the freeze `b2dda33` (tagged `v1.9.0`) and the post-tag accounting commit `58b6c22` | `git rev-parse HEAD` |
| CI verdict on that revision | run `39432183143`, all three jobs `success` | each job's own log, not the workflow badge |
| Working directory | `git worktree add --detach /Users/jackson/QuantRisk-v2-baseline 7d4f656` — a detached export, **not** the development checkout | §7 step 1's isolation procedure and L13's single-vantage rule |
| Tree state at measurement | `git status --porcelain` empty | it stayed empty apart from §7 step 5's documented trap, handled in §3 below |
| Interpreter | `.venv` created inside the export by `uv sync --frozen` (exit 0): Python 3.12.14 | `sys.version` |
| Instrument identity (L8) | `sys.prefix = <export>/.venv`, `quantrisk.__file__ = <export>/python/quantrisk/__init__.py`, extension `<export>/.venv/lib/python3.12/site-packages/quantrisk/_quantrisk.cpython-312-darwin.so`; no path resolves into the development checkout | a `python -c` probe printing `sys.prefix`, `module.__file__` and the `.so` glob, then asserting nothing contains the other root |
| Environment content | `dev` group installed (pytest, ruff, mypy, cmake, ninja, clang-format, pybind11, scipy, matplotlib, sympy, pyyaml); `oracles` extra **absent** — `sklearn`, `QuantLib`, `pypfopt`, `cvxpy` all fail to import | `python -c` import probe per module; this is exactly what CI's second job builds with plain `uv sync` |

The export was chosen over measuring in the development tree for two reasons, both of which are the
prompt's: L13 forbids a baseline over a tree carrying another session's work, and §7 step 4's lane list
*is* CI's lane list, which means the offline lane has to run in an environment where the oracles are
genuinely absent. The development checkout keeps its `oracles` install untouched.

## 2. Exit codes, captured per command

Each line is one command's own status, taken with `"$@" > log; rc=$?` inside a driver
(`build/v2-step4.sh`, gitignored scratch) rather than read off a pipeline's last stage. The commands are
`REFACTOR_PROMPT.md` §7 step 4 verbatim, run with the export as cwd.

| Step 4 lane | Command | rc | Wall | What the tool said |
|---|---|---|---|---|
| Lint | `uv run --frozen ruff check .` | 0 | 1 s | `All checks passed!` |
| Format | `uv run --frozen ruff format --check .` | 0 | 0 s | `204 files already formatted` |
| C++ format | `find cpp bindings tests/cpp … \| xargs uv run clang-format --dry-run --Werror` | 0 | 1 s | silent; corpus reported by the same `find`: **77 files** |
| Types | `uv run --frozen mypy python/quantrisk` | 0 | 5 s | `Success: no issues found in 23 source files` |
| Configure | `uv run --frozen cmake --preset ci` | 0 | 16 s | writes `<export>/build/ci` |
| Build | `uv run --frozen cmake --build --preset ci` | 0 | 48 s | core + tests + bindings + reference tool |
| C++ tests | `uv run --frozen ctest --preset ci` | 0 | 12 s | `100% tests passed out of 204` |
| Install | `uv pip install -e .` | 0 | 25 s | `Prepared 1 package in 21.79s`, `~ quantrisk==1.9.0 (from file://<export>)` |
| Python tests | `QUANTRISK_REFERENCE_TOOL=<export>/build/ci/quantrisk_reference_tool uv run --frozen pytest -q` | 0 | 159 s | `470 passed, 4 skipped in 157.52s` |
| Evidence | `uv run --frozen python scripts/verify_evidence_manifest.py` | 0 | 1 s | `Evidence is intact.` |

| Step 5 / 6 | Command | rc | What happened |
|---|---|---|---|
| Suite binding | `uv run --frozen python scripts/run_benchmark_suite.py --no-run` | 0 | read-only in intent, **not in bytes**: it rewrote three tracked aggregates and printed `suite: 0/19 executed and passed, 19 aggregated from disk, 0 failed, 0 skipped, 0.0s total` |
| Evidence, re-run | `uv run --frozen python scripts/verify_evidence_manifest.py` | **1** | `CHANGED benchmarks/suite/results/suite_run.json expected 072db34187b2… found e828635b7a80…`, `CHANGED …/suite_summary.md expected 6ae00d0d4914… found 56eabe2069a6…`, `Evidence does not match the manifest.` |
| Restore | `git checkout -- ` the three paths `git status --porcelain` named, by name | 0 | tree empty again |
| Evidence, third run | `uv run --frozen python scripts/verify_evidence_manifest.py` | 0 | `Evidence is intact.` |
| Plant inventory | `uv run --frozen python scripts/run_mutation_suite.py --list` | 0 | **172** declared plants; the full sweep is §10 P3.2's proof and will be read from its own summary line |

**The baseline is green.** Nothing in the lane starts from a red lane, so §7's "a red baseline is
information" branch was not exercised — except for the one rc=1 above, which is the prompt's own trap
firing as designed and is the strongest evidence in this section: it proves the manifest verifier can
fail, and that a suite invocation with exit 0 had still corrupted the ledger.

## 3. Environment readings that the prompt says are facts and the tree says are not

Recorded here rather than discovered later, each with the command that read it.

- **`--no-run` dirties three tracked files, not two.** §7 step 5 says "restore exactly the two files it
  rewrites". `git status --porcelain` after the invocation names three:
  `benchmarks/suite/results/suite_headline.csv`, `…/suite_run.json`, `…/suite_summary.md`. The manifest
  verifier only rejects two of them, because the third is byte-identical after re-aggregation — which is
  exactly how a "two" becomes a "three" without anybody noticing. Finding **V2-04**, lane `facts-protocol`.
- **The same revision, two pytest readings, one difference, and it is owned.** Local export:
  `470 passed, 4 skipped`. CI job 2 on `7d4f656`: `469 passed, 5 skipped`. Both sum to 474, which is
  `#91`'s reconciliation against the 470 collected offline. The extra skip is
  `tests/python/test_artifact_metadata.py:4897: latexmk is not installed, so the report cannot be
  re-typeset here` — present on the runner, absent here because this machine has `latexmk`. No lane is
  environment-blind by accident; this one declares its own skip.
- **The formatter count is not a property of the code.** `ruff format --check .` printed **204** in this
  export, while CI's `Format and static checks` job on the same revision printed **203**, and the
  development checkout prints **203**. The tracked Python corpus is the same 86 files in all three. A
  probe was attempted to enumerate what Ruff traverses (`ruff ls` — not a subcommand in 0.16.9;
  `ruff format --check . -v` emits no `Examining` lines to grep) and **it failed to answer the question**,
  so no cause is claimed here. What is claimed: the number is a walk of one environment, it can differ
  between environments at one revision, and it must not be quoted as a census. The collector's
  static-check census is the instrument that will replace it, because it must print what it counted and
  what it excluded.
- **The repository is bigger than the prompt's own size ratchet assumed.** §0 ratchets V2's prose against
  V1's line count; `wc -l PROJECT_SPEC.md REFACTOR_PROMPT.md` reads **1,724** and **683**, so the ratio
  this lane is allowed to grow against is a subtraction away from any reader. Recorded so that no later
  step mistakes the ratchet for permission to grow prose. Not a finding: the ratchet holds.

## 4. The three premises, and why this section is not yet closed

§0 demands all three premises re-derived from a fresh measurement before anything is touched, and §7 step 8
demands the ledger committed **before any instrument or source file is written**. The collector §7 step 3
names is an instrument. The two instructions cannot both be satisfied in the order written, and the lane
resolves it the only way that keeps both: this file is committed first, then `tools/inventory_orphan_code.py`
is written, then the premise readings land as a dated entry in this ledger's §9. Recorded as finding
**V2-01**, lane `facts-protocol`, so the contradiction is the document's defect and not a silent improvisation.

What can be stated without an instrument, because it is a direct filesystem reading of the export:

| Premise | Reading available now | Reading still owed |
|---|---|---|
| P1 — executable Python outside the package reaches it by `sys.path` hacks or by-path loads | 86 tracked `.py`, of which **63 live outside `python/quantrisk`** (`git ls-files '*.py'` and the same list filtered). Whether each reaches the package by bootstrap, by-path load, installed import, or not at all is the collector's classification, not an inference from a count. | the per-file classification, and the bootstrap census with the directory each site injects |
| P2 — recorded reproduction commands are not uniformly executable, and no guard polices their form | `evidence/manifest.json` holds **95** artifacts (`.venv/bin/python -c` over `artifacts`). The prompt's own collision warning applies: this project has since built producers for other recorded fields, so "no guard reads `generated_by_command` for form" must be **verified, not assumed**. | the executability census per entry, and a grep of `tests/` for any guard that reads that key at all |
| P3 — static checking covers the package but not the code outside it | `mypy python/quantrisk` reports **23 source files** against a **63-file** corpus outside the package; the gap is 40 files by subtraction, but subtraction is not a census. | the per-file bucket table (mypy-covered / ruff-covered / declared exemption) with each bucket's corpus printed |

**No premise is yet void, and none is yet measured.** If the collector returns an empty bootstrap census,
P1 weakens into a layout complaint and §5's motivation has to be re-scoped with the maintainer before any
move (§0's own instruction).

## 5. Declared scope

**Lanes** — all eight of §8, no lane skipped, no finding outside these lanes fixed without extending this
declaration first: orphan code and import hygiene; reproducibility contract; registry and hand-maintained
lists; test and verification validity; documented claims versus code; artifact reconciliation; packaging and
developer experience; security and CI. Plus the `facts-protocol` lane §4.4 grants for defects in the prompt
itself, which V2-01 and V2-04 already occupy.

**Tasks in scope** — §10's P3.1 registry, P3.2 verification instruments, P3.3 the experiment absorptions
(one commit per task), P3.4 the `tools/` package and the CI step that consumes it, P3.5 the single suite
re-run under L1's digest invariant, P3.6 the CLI `run` subcommand, P3.7 static-check parity; then §11's
installed-user proof, documentation coherence, dead-glue deletion and DX residue; then §12's report.

**Locked, at cost** — K1 `cpp/`, `bindings/`, `CMakeLists.txt`, `CMakePresets.json`; K2 every
`experiments/*/results/**` and `benchmarks/*/results/**` path; K3 `PROJECT_SPEC.md`; K4
`evidence/manifest.json` (builder-only; the rc=1 in §2 is the proof it is not a rubber stamp); K5 every
formula, tolerance, threshold and RNG contract.

**Survey** — §6 runs before the §9 gate, ≥5 maintained candidates across ≥3 classes, scored A1–A4 against
exact files, implementation never absorbed. Its notes are gitignored until the section it produces is
written into `docs/ecosystem_research.md`.

**Budget** — a wall-clock envelope of 12 hours of agent time across sessions, of which Phase 0 consumed
about 45 minutes (the gate suite itself: 4 minutes of tool time in one export). The gate suite is the
dominant cost: every §10 commit pays it in full, so the sequence is committed one finding at a time (L2)
and never bundled to save a run. CI minutes are the repository's existing free hosted allowance; external
spend for this lane is **$0.00** (L12), and the only paid-capable network call in the repository, a FRED
fetch, is not used by anything in scope.

**Outward actions** — pushes to `origin/main` happen because the standing instruction for this lane names
them. Creating the public GitHub Release object for `v1.9.0`, opening a PR, commenting on an issue, or
moving any tag requires its own approval and will not be inferred from this file.

## 6. Findings table

Schema, every field, per §8. `probe` is mandatory: it is what lets a later run re-derive the result
without trusting this ledger's prose.

| ID | lane | severity | evidence | probe | impact | root cause | proposed fix | verification | cost | blast radius | confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| V2-01 | facts-protocol | Low | §7 step 8 requires the ledger committed before any instrument; §7 step 3 requires the collector's premise readings inside that ledger | `sed -n '343,394p' REFACTOR_PROMPT.md` | the ordering is unsatisfiable as written; an executor either writes an instrument first or commits a ledger missing mandated content | the two steps were written against different drafts and neither names the other's dependency | resolve in the order that preserves the harder rule: ledger first, instrument second, premise readings as a dated §9 entry | the ledger's §9 entry cites the collector's own snapshot path and revision | 0 $, one commit | `REFACTOR_PROMPT.md` untouched (a prompt edit needs §4.4's leak test and maintainer approval); this file only | high |
| V2-04 | facts-protocol | Low | §7 step 5 says "restore exactly the two files it rewrites"; the export's `git status --porcelain` after that command named three, and the verifier rejected two of them | `uv run --frozen python scripts/run_benchmark_suite.py --no-run && git status --porcelain` | an executor who restores "the two" by a remembered list leaves one tracked aggregate dirty, and the next lane's green would then certify a dirty tree | the count of rewritten aggregates is a property of the run, not of the prose: whether a re-aggregated file is byte-identical depends on what changed since the last suite execution | the lane's rule is "restore the paths `git status --porcelain` names, by name" — already §14's rail; step 5's "two" is the defect, and the collector records the set rather than its size | §9's entry records the three named paths and the verifier returning to exit 0 after restoring them | 0 $, no file change | prose only | high |
| _(P1, P2, P3, and every §8 lane finding follow from the collector; none is entered before its probe exists)_ | | | | | | | | | | | |

Two placeholder ids are reserved so later numbering does not re-use them: **V2-02** (premise P1 findings)
and **V2-03** (the command-form census under P2).

## 7. Liveness of the laws, as of Phase 0

§13's table is produced at the end of Phase 1, after each `check:` has been executed. What Phase 0 can
already settle, and what it cannot:

| Law | Status at Phase 0 | The reading that decided it, or why it cannot be read yet |
|---|---|---|
| L3 no gate weakened | ACTIVE | the §2 table's rc=1 is a gate that fired; nothing in this lane adds a skip, and the skip delta in §3 is the runner's declared `latexmk` skip, not a new one |
| L6 no bootstrap hacks | ACTIVE, unmeasured | the census is the collector's; the 63-file corpus outside the package is the denominator §4.3 demands be printed |
| L10 counted claims owned | ACTIVE | the repository's own inventory guards pass inside the 470-test lane measured here |
| L12 zero external spend | ACTIVE | no dependency added; the export was built with `--frozen` from the committed lock |
| L13 baseline purity | ACTIVE | this file's §1 names the revision **and** the environment per lane, taken from a single export of a CI-verified revision, with no foreign work in it |
| L1, L4, L5, L7, L8, L9 | VOID until their precondition exists | L8 is partially exercised (§1's identity probe) but its check is the Phase 4 wheel proof; L1/L4/L5/L7/L9 require §5's architecture steps |
| L2, L11 | ACTIVE from the next commit | findings now exist |

## 8. How to resume this lane

1. `git fetch && git log --oneline -1` — if `origin/main` moved, re-read this file's §1 against the new
   head before trusting any stored exit code.
2. Re-run §7 step 4 in a fresh detached export, exactly as §1 describes. If a lane is red that this file
   recorded green, that is a finding, not noise, and it is entered in §6 before anything is fixed.
3. Write `tools/inventory_orphan_code.py` (one collector, nothing else), run it, read `§4`'s three
   premises from its snapshot, and append the readings to §9 of this file in the same commit that adds the
   ceilings file `tools/refactor_ceilings.json`.
4. Phase 1 diagnosis in §8's lanes, findings in §6's schema, then **stop at §9's approval gate**: silence
   is not approval.

## 9. Dated entries

_To be appended by the session that writes the collector: the premise readings, the snapshot path, the
revision and environment each was taken on, and every finding that closes or voids one._
