# V4_LEDGER.md — the cross-session state of the V4 series

V3 closed at `487bd19` (report) and `9e0bf03` (post-report addendum). This file starts after both, at the
final tip, and records only tool readings. It is **not** a V4 prompt: the maintainer has not written one, so the
rails below are the ones inherited from `V3_PROMPT.md` §14–§16 and applied to one scope unit at a time. A future
session with a written V4 prompt supersedes this paragraph rather than editing it.

### 2026-11-05, V4 Phase 0 — the archive re-counted at `9e0bf03`, and the first unit chosen

**Why this phase exists.** N11 says facts take precedence over inherited claims. `V3_LEDGER.md` §8's archival
confirmation was written at `d502a61`, before the report commit and before the addendum. Nothing had re-counted
its six numbers at the tip that is actually pushed. Every number below was read at `9e0bf03` with
`git status --porcelain` printing 0 lines.

| claim in §8 | command that produced the reading at `9e0bf03` | value |
|---|---|---|
| 19 registry tasks | `uv run --frozen quantrisk run --list`; `registry_parity` reading | 19 rows; `filesystem_units 19`, `registry_sources 19`, `mismatch` empty |
| 187 plants | `uv run --frozen python -m quantrisk.verification.runner --list` | 187 lines |
| 11 ceiling keys | `uv run --frozen python -m tools.inventory_orphan_code --check-ceilings` | 9 `ok`, 2 `SKIP` = 11 |
| 95 manifest entries | `uv run --frozen python -m tools.verify_evidence_manifest` | `95 OK`, `0 CHANGED`, `0 MISSING`, `Evidence is intact.` |
| 230 formatter files | `formatter_census` reading | `tracked_formattable 230`, `walked_formattable 230`, both differences empty |
| 560 / 491 pytest nodes | `uv run --frozen pytest --collect-only -q`; `uv run --frozen python -m tools.measure_offline_collection` | `560 tests collected`; offline tail `491 tests collected in 4.37s`, `collection_errors 0` |

Difference: **empty**. The V3 archive describes the tip that is pushed, not only the tip it was written at.

**The five V4 gaps, re-measured rather than quoted.**

1. **The lane-contract file does not exist.** `find . -maxdepth 3 -iname '*lane*contract*'` outside `build/` and
   `.venv/` returns nothing; `.github/` holds only `dependabot.yml` and `workflows/`. `V3_PROMPT.md` §5 and N3
   name a contract file, and §16 item 4 asks for it with a plant that fired. This is the only unshipped item in
   V3's own Definition of Done, which is why it is first.
2. **The mutation harness cannot tell a crash from an objection.** `runner.decide()` (line 117) branches on
   `guard_returncode == 0` → `ESCAPED` and accepts every other non-zero code as a rejection; it has no field for
   "the guard never completed". V3 §4 named eleven `tree-did-not-recover` results in the first census and left
   the five full-census failures undiagnosed (N9 VOID at 182/187).
3. **The with-extras installed census is not its own reading.** `tools/verify_installed_surface.py` exists and is
   declared dev-only (the ceiling key SKIPs on the runner by design); the `19/19 executed and passed` line is a
   by-product of the benchmark job, not an instrument with its own output.
4. **The refusal path has no pytest guard.** `grep -rn "unsatisfied_requirements|command_run|refusal"
   tests/python/` returns nothing. The declaration is guarded; the consumer is not.
5. **`docs/` re-derivation is not a lane.** `grep -n "name:" .github/workflows/ci.yml` lists 29 steps across the
   four jobs; none reads the documents it re-derives.

**The decision, and what it excludes.** V4-01 takes gap 1. It ships the contract as a file, the
`lanes_documented_vs_executed` reading in the one collector §4.1 permits, a ceiling key that can fail, an
extension of the existing lane guard (so the counted pair 560/491 does not move), and one plant that fires. It
does **not** take gaps 2–5. In particular it does not change `decide()`, does not re-run the full sweep, does not
add a second environment, and does not touch `cpp/`, `bindings/`, CMake, `PROJECT_SPEC.md`,
`REFACTOR_PROMPT.md`, `V3_PROMPT.md`, `evidence/manifest.json`, the `v1.9.0` tag or any published asset.

**The approval for this case, recorded verbatim (§14).** The maintainer's instruction that opened the session is
`我都听你的，请按照你的思路建议进行`, given after the V3 close-out enumerated the five gaps above. Read against
§14, that is a direction to choose and execute one scope unit, not a standing approval for every outward action:
this unit takes **one** push, attributed below, and no second one is implied by it. The V3 §9 addendum was
approved separately as `补记并推送（推荐）`; it is not the authority for this one.

**Two enumerations that decided the design**, read at `9e0bf03` over `-m (tools|quantrisk).*` and the four
console subcommands in `docs/reproducibility.md` + `CONTRIBUTING.md`, against the `run:` lines of
`.github/workflows/ci.yml`:

- documented: `quantrisk run`, `quantrisk validate`, `quantrisk.verification.runner`,
  `tools.build_evidence_manifest`, `tools.build_report`, `tools.run_benchmark_suite`,
  `tools.verify_evidence_manifest`;
- executed: `quantrisk run`, `quantrisk validate`, `tools.inventory_orphan_code`,
  `tools.run_benchmark_suite`, `tools.verify_evidence_manifest`;
- documented but never executed: `quantrisk.verification.runner`, `tools.build_evidence_manifest`,
  `tools.build_report` — the three dev-only rows the contract must justify;
- executed but documented nowhere: `tools.inventory_orphan_code` — the ceilings gate V3 added to the lint job
  without a line in either document. It is repaired by declaring the command in `docs/reproducibility.md`, not
  by deleting the step or by widening the contract to excuse it.

### 2026-11-05, V4-01 — the lane contract is a file, and its reading has two sides

**What shipped.** `.github/lane_contract.md` (new): eight rows — five `executed`, three `dev-only`, the latter
with reasons. `lanes_documented_vs_executed()` in `tools/inventory_orphan_code.py`: one reading, both
enumerations printed, every mismatch class named. `lanes_documented_vs_executed_gap` in
`tools/refactor_ceilings.json`: `max 0`, **no `may_be_unmeasured`**, so an instrument that reads nothing fails
the gate instead of skipping. The existing pytest guard
`test_the_ci_lane_that_runs_the_guards_fetches_what_they_read` was **extended**, not duplicated, so the counted
pair did not move. One plant added and one anchor re-keyed. `docs/reproducibility.md` gained the one command
line that was executing in CI with no document claiming it; `docs/interview_defense.md` moved `187/187` to
`188/188`.

**The reading at this commit**, printed by `uv run --frozen python -c "…lanes_documented_vs_executed()"`:

```
documented 8: quantrisk run, quantrisk validate, quantrisk.verification.runner,
             tools.build_evidence_manifest, tools.build_report, tools.inventory_orphan_code,
             tools.run_benchmark_suite, tools.verify_evidence_manifest
executed   5: quantrisk run, quantrisk validate, tools.inventory_orphan_code,
             tools.run_benchmark_suite, tools.verify_evidence_manifest
documented_not_executed 3: quantrisk.verification.runner, tools.build_evidence_manifest, tools.build_report
executed_not_documented 0
undeclared 0; declared_not_present 0; status_mismatch 0; dev_only_without_reason 0;
ci_reference_mismatch 0; claimed_by_mismatch 0; duplicate_rows 0; gap 0
```

Each of the five executed rows names the pair the parsed workflow actually contains: `build-and-test ::
study-catalogue`, `build-and-test :: Validate installed CLI`, `lint :: refactor ceilings`,
`benchmark-suite :: Run every benchmark and experiment`, `lint :: evidence manifest`. The reading is not a
count of rows: a row whose pair is absent lands in `ci_reference_mismatch`, and a command in either enumeration
with no row lands in `undeclared`.

**The plant, and the neighbours it did not disturb.** `lane-contract-claims-a-step-the-workflow-dropped`
replaces the evidence-manifest step's `run:` line with `true`; the guard then reads a contract that claims a
step the workflow no longer contains. Sweep at `d5408f4`, clean tree:

```
caught  lane-contract-claims-a-step-the-workflow-dropped
1/1 planted defects were rejected by their guard.
```

Because the guard was extended, the three plants that already target it were re-run rather than assumed:
`docs-command-comment-counts-superseded-plants` (its anchor moved to `188/188`),
`ci-lane-stops-validating-the-installed-cli`, and `reachability-reading-drops-one-of-its-instruments` printed
`3/3 planted defects were rejected by their guard.` on the same clean tree.

**Counts that moved, and the one that did not.**

| quantity | before | after | why |
|---|---|---|---|
| declared plants | 187 | 188 | the new plant; one anchor re-keyed in the same commit |
| ceiling keys | 11 | 12 | `lanes_documented_vs_executed_gap`, `max 0`, no `may_be_unmeasured` |
| formatter-tracked files | 230 | 232 | `V4_LEDGER.md` and `.github/lane_contract.md`; both sides equal, difference 0 |
| pytest nodes | 560 / 491 | **560 / 491** | the guard was extended; `--collect-only` printed `560`, the offline probe `491` |

**Local gates at `d5408f4`.** `ruff check .` → `All checks passed!`; `ruff format --check .` → `232 files
already formatted`; `mypy python/quantrisk tools` → `74 source files`, no issues; `--check-ceilings` → 12 keys,
10 `ok`, 2 `SKIP`; `verify_evidence_manifest` → `Evidence is intact.`; `pytest -q` → **559 passed, 1 failed**,
the bytecode-cache plant this sandbox cannot run (`sys.dont_write_bytecode`), the same single failure V3
recorded. The runner's reading is the one that decides that lane.

**Deliberately not done, and why each is named rather than omitted.**

1. **The full mutation sweep was not re-run.** N9 remains VOID for the full-census form from V3 (182/187), and
   this unit proves its own plant and the three neighbours its guard touches, not 188. Re-running the census
   would spend the N9 question without changing it.
2. **Gaps 2–5 are untouched**: `decide()` still cannot distinguish a crash from an objection, the with-extras
   census is still a by-product, the refusal path still has no pytest guard, and `docs/` is still not a lane.
3. **The report PDF was not re-rendered.** `paper/technical_report.tex` quotes `560` and `491`, neither moved;
   it does not quote the plant count, the ceiling-key count or the formatter count. Re-rendering without a
   source change would rewrite a byte-only artifact for nothing.
4. **`quantrisk benchmark` and `quantrisk demo` are not contract rows.** They are declared in-process-only in the
   guard, with reasons; no document claims them as a lane and no step invokes them. The contract's prose says
   so, which keeps the row set equal to the two enumerations rather than to every subcommand that exists.

**The push that did not happen.** `0b84a51`, `d5408f4` and `0a72b61` are local only. Two `git push origin
main` attempts failed at the transport, both with `CONNECT tunnel failed, response 502`. The failure is not
credentials or permission: `gh api rate_limit` answered on the same machine with 4990 requests remaining, and a
read-only `git ls-remote origin -h refs/heads/main` failed with the identical 502, so the git-over-HTTPS tunnel
is what is down. The push was not attempted a third time. `origin/main` stands at `9e0bf03`, and these three
commits have **no runner verdict** — they are not green by inheritance, and this paragraph is the reason a later
session must not assume otherwise.

Everything those commits claim was measured locally, on a clean tree, at `d5408f4` / `0a72b61`: the lane
reading at `gap 0` with all eight mismatch classes empty and both enumerations printed; the new plant `caught`
`1/1` and the three plants its guard already owned `3/3`; `--check-ceilings` at 12 keys, 10 `ok`, 2 `SKIP`;
`232` formatter files on both sides with a difference of `0`; `560` collected and `491` offline; `Evidence is
intact.`; and the suite at `559 passed, 1 failed` — the bytecode-cache plant this sandbox cannot run, which is
the one lane only the runner can decide. **The CI reading for these commits is unknown, not green**, and the
next session's first act is to read it after the transport recovers rather than to re-run the work.

**Pre-flight in a clean clone, while the transport stayed down.** A later probe at 22:54 on the same day found
`github.com` still answering `CONNECT tunnel failed, response 502` through the proxy while `api.github.com`
answered `200`, so the push remained impossible and was not attempted again. Instead the reading was re-run
from `git clone --no-hardlinks . /tmp/qr-v4-clone`, at `0be2c5b`, with `git status --porcelain` printing 0
lines and both new files tracked:

```
lanes_documented_vs_executed: available True, gap 0, documented 8, executed 5, declared 8,
                              documented_not_executed 3, every mismatch class empty
formatter_census:             exit 0, reported 232, walked 232, tracked 232,
                              walked_but_not_tracked [], tracked_but_not_walked []
```

That is the corpus CI checks out — no `.workbuddy`, no untracked scratch — so the lint lane's two new inputs
are consistent there and the local `.git/info/exclude` was not hiding a tracked-file defect. The same run also
showed the collector failing closed when `ruff` is absent from both the clone's `.venv` and `PATH`
(`AssertionError: … the census has no instrument`) rather than reporting zero, which is the behaviour the new
ceiling key depends on.

### 2026-11-05, V4-01 — the runner read the contract, and the tip is green

**The push.** The transport recovered at 23:10: `git ls-remote origin -h refs/heads/main` answered and
`curl https://github.com` returned `200`. `git push origin main` was then accepted on the first attempt,
`9e0bf03..8ffcb32`. The two earlier `502` failures and the read-only probe that confirmed them stay recorded
above rather than being erased by the success.

**Run `42052330523`, event `push`, tip `8ffcb32`, attempt 1, `completed success`** at
`2026-11-05T15:21:28Z`. Four jobs, all `success`, each on its own runner:

| lane | runner | window (UTC) | reading |
|---|---|---|---|
| Format and static checks | `ubuntu-latest` / `GitHub Actions 1000010048` | 15:10:57–15:11:53 | `All checks passed!`; `232 files already formatted`; `74 source files`, no issues; 12 ceiling keys, 10 `ok`, 2 `SKIP`; `Evidence is intact.` |
| Configure, build, C++ tests, Python tests | `ubuntu-latest` / `GitHub Actions 1000010049` | 15:10:57–15:18:37 | `100% tests passed out of 204`; `490 passed, 5 skipped in 231.99s`; `7/7 checks passed` |
| Benchmark suite against live oracles | `ubuntu-latest` / `GitHub Actions 1000010047` | 15:10:57–15:21:27 | `19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 407.1s total` |
| macOS native C++ and Python parity | `macos-15` / `GitHub Actions 1000010050` | 15:11:46–15:14:51 | `100% tests passed out of 204`; `98 passed in 2.48s` |

**The new reading, on a runner rather than on this laptop.** The lint job printed
`lanes_documented_vs_executed {"available": true, …, "gap": 0, "unavailable_because": ""}` followed by
`ok      lanes_documented_vs_executed_gap: 0 against a ceiling of 0 due V4-01`. Its `executed_at` map names the
same five pairs the local reading named — `build-and-test :: study-catalogue`,
`build-and-test :: Validate installed CLI`, `lint :: refactor ceilings`,
`benchmark-suite :: Run every benchmark and experiment`, `lint :: evidence manifest` — and
`documented_by_file` resolves the same two documents. Two operating systems, two interpreters, one answer:
the contract describes the workflow, not this checkout.

**The counted pair did not move on the runner either.** `490 passed, 5 skipped` is identical to V3's reading
in `41858982944` (`d502a61`), which is the fact the "extend the guard, do not add a case" decision was made
for. A V4 unit that had added a test would have printed 491 here and moved three gold lists, five plant
anchors and the report PDF for one assertion.

**One caveat, repeated rather than newly found.** The benchmark summary again prints
`revision: 8ffcb32c23e1 (working tree was dirty at run time)` and "Re-run on a clean tree before citing them."
V3 §9 named the same line at `487bd19` and did not diagnose it; this entry does not claim a cause either. The
`19/19` line is a count of executions, and no number from that job's generated artifacts is cited in this
ledger.

**Archival state after the push.** Local `HEAD` = `origin/main` = `8ffcb32c23e10a3ad8e30fd364f4250baaaab643`;
`git status --porcelain` printed 0 lines; `v1.9.0` = `d9deb7f`, unmoved; `evidence/manifest.json` intact at 95
entries and re-verified by the lint job.

**The terminal commit.** This entry is itself a commit. Its own CI is read after the push and reported in the
session handoff rather than written into the file whose content is fixed before that push — the same
terminal-commit convention V2 and V3 used, named here so a reader does not mistake the absence for an
unread run.

### 2026-11-06, V4 Phase 0 for V4-02 — `decide()` cannot tell a crash from an objection

**The reading that decides the finding.** `quantrisk.verification.runner.decide()` is a pure function of
eight steps. Called with every other step satisfied and only the guard's exit code varied, it prints:

```
rc 0 -> no-guard-objected
rc 1 -> caught
rc 2 -> caught
rc 3 -> caught
rc 4 -> caught
rc 5 -> caught
```

pytest's documented meanings are `0` all passed, `1` tests failed, `2` interrupted, `3` internal error, `4`
usage error, `5` no tests collected. Four of those five non-zero codes are the harness failing to run the
guard, not the guard rejecting the defect — and `decide()` scores all four as `caught`. V3 §7 item 2 named
this and V3 §4 recorded eleven `tree-did-not-recover` results from the first census; the second half of that
item (per-plant isolation across 187 consecutive runs) is **not** this unit.

**The principle already exists one function away, which is why this is a defect rather than a design choice.**
`Harness.module_failures()` carries the table in its own docstring: "0 is everything passed and 1 is some
tests failed, while 2, 3, 4 and 5 are collection, internal, usage and no-tests-collected errors. Folding
those into an empty failing set would report a broken run as a plant that escaped every guard, which is the
confusion this instrument exists to remove." The pairing audit applies it; `decide()` — the function the
default sweep uses — does not. The fix is therefore to apply an existing rule, not to invent one.

**What the unit will and will not change.** It adds one outcome for "the guard process errored without
objecting", keeps pytest `1` as the only objection code, leaves CTest's non-zero convention alone (its
failures and its usage errors are not separable from the exit code alone, and the `green_again` step already
catches a CTest that errors on both trees), extends the existing status-table test rather than adding a case
(the counted pair stays 560/491), and adds one plant whose mutation removes the new branch. It does **not**
add per-plant isolation, does not diagnose the five full-census failures, and does not re-run N9.

**A named observation, deliberately not fixed here.** `runner.py` assigns `ESCAPED` twice: line 84
`"guard-stayed-green"` and line 93 `"no-guard-objected"`, the pairing audit's vocabulary reusing the sweep's
name. The module-level value is therefore the second one, while `docs/interview_defense.md` line 873 still
tells the reader a guard that cannot see a defect comes back `guard-stayed-green`. Repairing it changes a
verdict string that dated phase reports quote, so it needs its own unit and its own guard; recording it here
is this unit's obligation under "no silence", and fixing it is not.

**The approval for this case, recorded verbatim (§14).** The maintainer's instruction is
`我都听你的，请按照你的思路建议进行`, given after the V4-01 handoff proposed this unit by name. As with
V4-01, that is a direction to choose and execute one scope unit, not a standing approval for every outward
action: this unit takes **one** push, attributed below, and no second one is implied.

### 2026-11-06, V4-02 — a guard that errors before it objects is its own verdict

**What shipped.** `GUARD_ERRORED = "guard-errored-without-objecting"` in `runner.py`;
`decide()` gains `guard_protocol` and applies pytest's own table (`1` is the only objection code, `2`–`5` are
the guard failing to run); `run_one()` passes `"ctest"` for core plants and `"pytest"` otherwise;
`run_one_probe()` passes `"pytest"` explicitly. The status-table test was **extended**, not duplicated. One
plant was added and one anchor re-keyed.

**The reading after the change**, same call shape as the Phase 0 reading:

```
pytest rc 0 -> no-guard-objected
pytest rc 1 -> caught
pytest rc 2 -> guard-errored-without-objecting
pytest rc 3 -> guard-errored-without-objecting
pytest rc 4 -> guard-errored-without-objecting
pytest rc 5 -> guard-errored-without-objecting
ctest  rc 1 -> caught
```

**The plant, and the anchor it moved.** `pytest-error-code-is-counted-as-an-objection` inverts the new
condition (`!= 1` → `== 0`), so the branch can never fire; the extended status-table test then reads `caught`
where it requires `GUARD_ERRORED`. Sweep at `501dd3e`, clean tree:

```
caught  docs-command-comment-counts-superseded-plants   (anchor re-keyed to 189/189)
caught  pytest-error-code-is-counted-as-an-objection
2/2 planted defects were rejected by their guard.
```

`git status --porcelain` printed 0 lines afterwards, so both targets were restored byte-for-byte.

**Counts that moved, and the ones that did not.**

| quantity | before | after | why |
|---|---|---|---|
| declared plants | 188 | 189 | the new plant; one anchor re-keyed in the same commit |
| pytest nodes | 560 / 491 | **560 / 491** | the test was extended, not added |
| ceiling keys | 12 | **12** | no new policy row; the change is inside an existing guard |
| formatter-tracked files | 232 | **232** | no new document |

**Local gates at `501dd3e`.** `ruff check .` → `All checks passed!`; `ruff format --check .` → `232 files
already formatted`; `mypy python/quantrisk tools` → `74 source files`, no issues; `--check-ceilings` → 12 keys,
10 `ok`, 2 `SKIP`; `verify_evidence_manifest` → `Evidence is intact.`; `pytest -q` → **559 passed, 1 failed**,
the bytecode-cache plant this sandbox cannot run — the same single failure V3 recorded, and the lane the
runner decides.

**Deliberately not done, named rather than omitted.**

1. **Per-plant isolation was not added.** V3 §7 item 2 has two halves; this unit takes the crash-versus-
   objection half only. The five `tree-did-not-recover` results from the full census are still undiagnosed, and
   N9 remains VOID at 182/187 until a sweep runs clean.
2. **The `ESCAPED` collision is recorded, not repaired** — see the Phase 0 entry. It changes a verdict string
   that dated reports quote, and needs its own unit.
3. **No CTest code table was invented.** CTest's exit code does not separate a failing case from a usage error,
   so the coarse convention stands; a CTest that errors on the restored tree is already refused by
   `green_again`, and the extended test pins that.

**The push, and how its CI reading is recorded.** This entry is committed after the implementation commit and
pushed with it. The CI reading for the pushed tip is appended in the next entry once `gh` reports it; the
ledger never states an outcome before the tool does.

### 2026-11-06, V4-02 — the runner read the new verdict, and the tip is green

**The push.** `git push origin main` accepted on the first attempt, `4c2b144..adf9918`, carrying
`d06f998` (Phase 0 entry), `501dd3e` (implementation) and `adf9918` (the readings entry).

**Run `42061987436`, event `push`, tip `adf9918`, attempt 1, `completed success`** at
`2026-11-05T16:19:33Z`. Four jobs, all `success`:

| lane | runner | window (UTC) | reading |
|---|---|---|---|
| Format and static checks | `ubuntu-latest` / `GitHub Actions 1000010099` | 16:11:36–16:12:50 | `232 files already formatted`; `74 source files`, no issues; 12 keys, 10 `ok`, 2 `SKIP`; `lanes_documented_vs_executed_gap: 0`; `Evidence is intact.` |
| Configure, build, C++ tests, Python tests | `ubuntu-latest` / `GitHub Actions 1000010101` | 16:11:36–16:19:32 | `100% tests passed out of 204`; **`490 passed, 5 skipped in 232.77s`**; `7/7 checks passed` |
| Benchmark suite against live oracles | `ubuntu-latest` / `GitHub Actions 1000010100` | 16:11:36–16:18:46 | `19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 272.9s total` |
| macOS native C++ and Python parity | `macos-15` / `GitHub Actions 1000010102` | 16:11:52–16:15:29 | `100% tests passed out of 204`; `98 passed in 3.27s` |

**The count that mattered did not move.** `490 passed, 5 skipped` is identical to the readings at `8ffcb32`
and at V3's `41858982944`/`d502a61`. The new assertions live inside an existing test, so the counted pair is
still 560/491 and no gold list, plant anchor or report PDF had to move for this unit.

**One caveat, unchanged and still not diagnosed.** The benchmark summary prints
`revision: adf9918abfd2 (working tree was dirty at run time)` for the third consecutive run. It is the same
line V3 §9 named; this unit neither explains it nor cites any number from that job's generated artifacts.

**Archival state after the push.** Local `HEAD` = `origin/main` =
`adf9918abfd219d6cbf5eb578e9ae3cbb22f13b4`; `git status --porcelain` printed 0 lines; `v1.9.0` = `d9deb7f`,
unmoved; `evidence/manifest.json` intact at 95 entries and re-verified by the lint job.

**The terminal commit.** This entry is itself a commit; its own CI is read after the push and reported in the
session handoff rather than written into the file whose content is fixed before that push, the same convention
V2, V3 and V4-01 used.

---

### 2026-11-06, V4 Phase 0 for V4-03 — the full census, measured again at `b5db84f`

**Revision and vantage.** `HEAD` = `origin/main` = `b5db84f88f5cf2c848223a8ee797046d1464f163`,
`git status --porcelain` 0 lines, `v1.9.0` = `d9deb7f` unmoved. Vantage: the development checkout,
`.venv` Python 3.12, macOS, the same WorkBuddy interpreter shim V3 Phase 5 recorded. The declared
counts were re-measured, not inherited: 189 plants, 12 ceiling keys (10 `ok` / 2 `SKIP`), 95 manifest
entries, 232 formatter-tracked files, 560/491 pytest nodes.

**Reading A — the unwrapped sweep.** `uv run --frozen python -m quantrisk.verification.runner --all
--verbose` printed 19 `caught`, then aborted at plant 20 (`experiment-added-without-a-registry-entry`,
the first `tree` case) with `OSError: [Errno 5] Path is a directory: rm returned EISDIR` from
`run_one_probe`'s `parent.rmdir()`. The shim replaces both `pathlib.Path.rmdir` and `os.rmdir` with a
broker that answers `EISDIR` for a directory inside the workspace; outside it (`/tmp`) the same call
succeeds. The probe file itself was already unlinked, so `git status --porcelain` was 0 lines. This is
a property of the local test environment, not a repository defect, and no source change is made to
accommodate it.

**Reading B — the full census under V3's wrapper.** `build/run_sweep.py` (gitignored scratch) swallowed
that `OSError` so the sweep could finish. Its own summary line, captured:

```
176/189 planted defects were rejected by their guard.
```

13 non-`caught` rows, all `tree-did-not-recover`, exit 1, tree clean afterwards. The first plant's
mutated and restored guard tails are both `FAILED ... / 1 failed` — the restored tree stayed red
because the wrapper left `experiments/_mutation_probe/results/` behind, and
`test_the_manifest_hashes_every_experiment_results_directory` walks `experiments/*/results`. Six more
carry `ERROR ... / 1 error` on **both** runs, from guards that use `tmp_path` (the temporary-tree
reproduction tests, `test_an_absent_git_reports_which_kind_of_absence_it_is`, the manifest-hash and
rewrap tests): a pytest temp-root error, not an objection, and not cured by restoring the bytes. The
last six, from `project-adds-a-dependency-the-declaration-does-not-name` onward, print the same
`uv` tail on both runs — `hint: This usually indicates a problem with the package or the build /
environment.` — so from that point every `uv run --frozen pytest` in the sweep failed to start.

**Controls, so the three shapes are not conflated.** Running
`project-adds-a-dependency-the-declaration-does-not-name` alone printed `caught`, `1/1`. Re-applying
its exact `pyproject.toml` mutation by hand and running its guard produced `rc = 1` with the expected
assertion (`dependencies measured 10; declared 9; added ['requests']`) and a clean `uv` build, then
restored the file. A 40-invocation compressed `uv run --frozen pytest` loop printed `invocation 10 ok`
and was then killed by the command timeout (`SIGTERM`, exit 137); that partial run is **unknown**, not
a verdict about the loop. So none of the 13 is a plant whose guard failed to understand its own defect:
they are states one invocation left for the next.

**The three leaks this unit will close, named from those readings.**

1. **Probe-directory residue.** V3's wrapper skipped the removal, so one plant's empty directory made
   the next plant's restored tree red. The local wrapper is rewritten to call the unpatched C entry
   point `posix.rmdir`, which does remove an empty workspace directory here; this is a change to
   gitignored scratch only, and `git status` remains the proof the tree is clean.
2. **A shared pytest temp root.** `Harness.isolation_environment()` isolates the bytecode cache per
   invocation but leaves pytest's `tmp_path` root shared across the whole sweep. Each guard invocation
   gets its own `--basetemp`, derived from the same per-invocation directory as its bytecode prefix.
3. **A shared `TMPDIR`.** `uv run --frozen` rebuilds the editable package on every guard call here;
   its build scratch and pytest's default temp root both live under one shared `TMPDIR`. Each
   invocation gets a private one.

**The approval for this case, recorded verbatim (§14).** The maintainer's instruction is
`我都听你的，请按照你的思路建议进行`, given after the V4-02 handoff named this unit first and proposed
per-plant isolation by name. As in V4-01 and V4-02, that is a direction to choose and execute one
scope unit, not a standing approval: this unit takes two pushes — the implementation-and-readings tip,
and the entry recording that tip's CI — both attributed below, and no third is implied.

**Deliberately not done in Phase 0.** No source file was edited, no ceiling key added, no plant added,
and no claim was carried forward from V3 §4's "undiagnosed" wording: every number above comes from a
reading taken at this tip. The `ESCAPED` collision named in V4-02's Phase 0 entry stays open.

---

### 2026-11-07, V4-03 — every guard invocation owns its temp roots, and the census is green

**Revision and vantage.** `HEAD` = `f5fe7ae2ef71d907816543ca19b3d807346dda21`,
`git status --porcelain` 0 lines, `origin/main` = `b5db84f88f5cf2c848223a8ee797046d1464f163`,
`v1.9.0` = `d9deb7f` unmoved. Vantage: the development checkout, `.venv` Python 3.12, macOS, the same
WorkBuddy interpreter shim (`PYTHONPATH` → `.../cli/vendor/shim/sitecustomize.py`) V3 Phase 5 recorded.
All readings below are from this tip unless named otherwise.

**What shipped.** `runner.py` names three per-invocation environment variables instead of one:
`BYTECODE_PREFIX`, `TEMP_ROOT` (`TMPDIR`) and `PYTEST_OPTIONS` (`PYTEST_ADDOPTS`). `pytest_basetemp()`
derives one `--basetemp` from the same `cache_dir` as the bytecode prefix; an inherited `--basetemp` is
replaced, not doubled. `isolation_environment()` now creates both private directories, so a plant's
mutated guard and its restored guard each get their own bytecode prefix, `TMPDIR` and pytest temp root.
The existing isolation test was **extended**, not duplicated: its spy now checks all three variables on
every guard invocation and requires them to be unique between invocations. One plant was added,
`guard-invocations-share-one-pytest-temp-root`, whose anchor is the new `pytest_basetemp` return line;
`docs/interview_defense.md:1037` was re-keyed to `190/190`. No ceiling key was added and no locked file
was touched.

**The reading that closes N9.** The single-process census, run on the committed tip with a clean tree
(the post-commit re-run N9 requires), printed its own summary line at line 973 of
`/tmp/qr-v4-03-census-final-1794019837.log` (created 10:50:37, last written 11:33:30, 98,853 bytes):

```
190/190 planted defects were rejected by their guard.
```

Exit 0; the status histogram is `190 caught`, with zero non-`caught` rows and zero `FAIL` rows;
`git status --porcelain` printed 0 lines afterwards and no `*mutation_probe*` directory remained under
`experiments/`, `docs/`, `python/` or `tests/`. So N9, VOID at 182/187 in V3 and at 176/189 in this
unit's Phase 0, has a captured summary line for all 190 declared plants. The ceiling key
`plants_not_rejected_by_their_guard` remains `SKIP` on the runner by design — it measures the
declaration only and cannot read a sweep that writes gitignored scratch — so this proof is a
development-vantage reading, not a CI lane, and is not attributed to one.

**Why the first two full censuses were not green, and what the last seven rows were.** The readings,
in order, at the same plant count unless named otherwise:

| reading | environment | result |
|---|---|---|
| Phase 0, V3 wrapper | `b5db84f`, shared `TMPDIR` | `176/189`, 13 `tree-did-not-recover` |
| after the isolation fix | `f5fe7ae`, private `TMPDIR` | `183/190`, 7 `tree-did-not-recover` |
| diagnostic replay | `f5fe7ae`, shared `TMPDIR`, full output | same 7 rows, 14 error blocks |
| escalated shell | `f5fe7ae`, private `TMPDIR` | `183/190`, still 7 rows |
| this reading | `f5fe7ae`, private `TMPDIR`, raised delete threshold | `190/190`, 0 rows |

The diagnostic replay printed the real `uv` text that the shipped `_run` truncates to its last two
lines. All 14 blocks (7 plants × 2 guard runs) carry the same marker:

```
[safe-delete][SAFE_DELETE_BULK_CONFIRM_REQUIRED]
{"count":50,"threshold":50,"scope":"turn","targets":[".../build/wheel/CMakeFiles"],"targetCount":1}
```

`safe-delete-bulk-guard.cjs` counts deletions **per tool call** against
`CODEBUDDY_SAFE_DELETE_BULK_THRESHOLD` (50 here) and refuses the bulk delete that
`scikit-build-core` performs while reconfiguring `build/wheel/CMakeFiles`. That is why the failure
always began at the same 184th plant in two runs of very different duration (26 and 172 minutes),
why a 3-plant and a 7-plant sequence containing the `pyproject.toml` plant were both fully `caught`,
and why escalating the shell did not help: the shim is injected into every Python child via
`PYTHONPATH`, not into the shell. The remaining seven rows were therefore **not** a fourth state leak
between plants; they were a session-level deletion policy in the local development environment. CI
has no such shim. Raising that one environment variable for this census only — no repository file,
ceiling, guard or wrapper verdict was changed — produced 0 guard refusals and the clean sweep above.
Two shorter diagnostic censuses are recorded as incomplete, not green: one stopped at 106/190 when
the session was interrupted (it left one un-restored `docs/validation_matrix.md` mutation, restored
before any further command), and one was the truncated-tail replay whose only purpose was the error
text.

**Counts that moved, and the ones that did not.**

| quantity | before | after | why |
|---|---|---|---|
| declared plants | 189 | **190** | the new plant; one anchor re-keyed in the same commit |
| pytest nodes | 560 / 491 | **560 / 491** | the test was extended, not added |
| ceiling keys | 12 | **12** | no new policy row; the change is inside an existing guard |
| formatter-tracked files | 232 | **232** | no new document |

**Local gates at `f5fe7ae`.** `ruff check .` → `All checks passed!`; `ruff format --check .` →
`232 files already formatted`; `mypy python/quantrisk tools` → `Success: no issues found in 74 source
files`; `--check-ceilings` → 12 keys, 10 `ok`, 2 `SKIP`, with `declared_plants: 190`,
`lanes_documented_vs_executed_gap: 0` and `tracked_files_outside_the_formatter_corpus: 0`;
`verify_evidence_manifest` → `Evidence is intact.`. An unqualified `pytest -q` in this shell read
`517 passed, 43 errors in 119.76s`: every error is `FileExistsError` from `sitecustomize.py:507`
trying to `mkdir` an existing `/private/var/.../T/pytest-of-unknown`, a pytest cache directory dated
2026-11-02 that has nothing to do with this tip. No non-project directory was deleted. Re-running with
a fresh private `--basetemp` (the same isolation this unit ships) read **`559 passed, 1 failed in
351.66s`**, the single failure being the bytecode-cache plant this sandbox cannot run, identical to
V3's and V4-02's local reading. The runner, not this shell, decides that lane.

**Deliberately not done, named rather than omitted.**

1. **The `ESCAPED` double assignment is still open** — `V4_LEDGER.md` line 84 overwritten by line 93
   while `docs/interview_defense.md:873` still quotes the former. It changes a verdict string dated
   reports cite and needs its own unit.
2. **The with-extras census is not its own reading**, the refusal path still has no pytest guard, and
   `docs/` re-derivation is not yet a declared lane. These are V3 §4/§7 gaps, unchanged here.
3. **No CI lane was added for the sweep.** N9's proof stays a development-vantage reading with a
   captured summary line; the runner's ceiling key is unchanged and still `SKIP`.
4. **The local delete-threshold override is an environment condition, not a shipped change.** No
   repository file records it as a requirement, and no CI step depends on it.

**The push, and how its CI reading is recorded.** The approval for this case is the one recorded
verbatim in the Phase 0 entry above: `我都听你的，请按照你的思路建议进行`, covering this unit's two
pushes. This entry is committed after the implementation commit and pushed with it; the CI reading for
the pushed tip is appended in the next entry once `gh` reports it. The ledger states no outcome before
the tool does.

---

### 2026-11-07, V4-03 — the push is blocked, and the CI reading is unknown

**This entry corrects the tense of the preceding one.** Its last paragraph describes the intended
sequence, not a completed push. No push has reached the remote for this unit. The `190/190` reading
above is a development-vantage sweep summary and stands on its own; nothing in it is claimed as CI.

**Local state.** `HEAD` = `af3949d7ff4725de9c99aaae89e7487876e2defe`, `git status --porcelain` 0
lines, `origin/main` = `b5db84f88f5cf2c848223a8ee797046d1464f163`. Four local commits are ahead of
the remote tip: `91535b6` (Phase 0), `f5fe7ae` (implementation), `af3949d` (readings), and this
entry's commit.

**The readings that make the push unknown, in order.**

| attempt | channel | tool reading |
|---|---|---|
| 1 | `git push origin main`, HTTPS via `127.0.0.1:56037` | `fatal: ... CONNECT tunnel failed, response 502`, exit 128 |
| 2 | same, plus `git ls-remote origin` | same 502; no remote ref obtained |
| 3 | retry, same channel | same 502, exit 128 |
| 4 | SSH `git@github.com`, key `id_ed25519_interve` | `Hi Jackxiaozhiren/Interve-AI! ... successfully authenticated` on the auth probe, then `ERROR: Permission to Jackxiaozhiren/quantrisk-plus-plus.git denied to deploy key`, exit 128 |
| 5 | `git -c http.proxy= -c https.proxy= push` | `Failed to connect to github.com port 443 after 75003 ms`, exit 128 |

**Controls, so the failure is not misread as a repository or credential problem.**

- `gh api repos/Jackxiaozhiren/quantrisk-plus-plus --jq ...` → `Jackxiaozhiren/quantrisk-plus-plus main`,
  exit 0; `curl -w '%{http_code}' https://api.github.com` → `200`; `curl ... https://github.com` → `000`.
  The failure is specific to the git host behind the local HTTP proxy, not to GitHub's API.
- `gh api repos/.../commits/main --jq .sha` → `b5db84f88f5cf2c848223a8ee797046d1464f163` after
  every attempt, so no push arrived. `gh run list --limit 5` still shows `42063687017` at `b5db84f`
  as the newest run; there is no run for `af3949d`.
- `nc -z github.com 22` and `nc -z ssh.github.com 443` both succeeded, so SSH transport is reachable;
  the blocker is the deploy key's authorization, not the port. `~/.ssh/` holds only
  `id_ed25519_interve`, and `ssh-add -l` reports no agent identities.
- `HTTP_PROXY`/`HTTPS_PROXY` = `http://127.0.0.1:56037`, no `git config http.proxy`. Removing the
  proxy (attempt 5) produced a 75-second connect timeout, so there is no working direct route.

**Verdict.** The V4-03 CI reading is **unknown**. No cancelled, partial, API-only or escalated-shell
result is recorded as green, and §15.5's cancelled-run rule is not relaxed. Attempt 4 is an
authentication success but an authorization failure; it is not a push and creates no run. No further
push is attempted here: V3 §9 set the precedent of stopping after repeated tunnel 502s and resuming
only when the maintainer asks or the channel is measured to be restored.

**What remains for this unit.** One push carrying the four local commits, then a `gh run view` reading
attributed to that run's attempt, runner and environment (§16.8), then this unit's second push with
the entry recording that CI reading, and a final CI read reported in the session handoff. The two
pushes authorised verbatim in the Phase 0 entry are both still outstanding: no push has reached the
remote, so neither has been consumed. The `ESCAPED` collision, the with-extras census, the
refusal-path pytest guard and the `docs/` re-derivation lane remain open, unchanged by this entry.

---

### 2026-11-07, V4-03 — a partial host recovery is not a restored git channel

**Reading.** `curl -w '%{http_code}' https://github.com` → `200` (it was `000` during attempts 1–5),
but `curl ... /Jackxiaozhiren/quantrisk-plus-plus.git/info/refs?service=git-upload-pack` → `000`,
and a sixth `git push origin main` → `fatal: ... CONNECT tunnel failed, response 502`, exit 128.
`gh api repos/.../commits/main --jq .sha` still → `b5db84f88f5cf2c848223a8ee797046d1464f163`, and
`origin/main` is unchanged. The local proxy therefore serves the web host but not the repository's
git smart-HTTP endpoint. Under the criterion written in the preceding entry, the channel is **not**
measured as restored, the V4-03 CI reading remains **unknown**, and no further push is attempted.
Five local commits now sit ahead of the remote tip: the four named above and this entry's commit.
Nothing in this entry changes the `190/190` sweep reading, which is a development-vantage proof and
never depended on a push.

---

### 2026-11-07, V4-03 — the implementation-and-readings tip is green

**The push, by a different transport.** The git smart-HTTP host stayed blocked (`CONNECT tunnel
failed, response 502`) while `api.github.com` remained reachable and `gh auth status` reported a
`gho_` token with `repo`, `workflow`, `read:org`, `gist` scopes. The five local commits were therefore
appended through the GitHub Git Data API by `build/api_push.py`, a gitignored scratch script that is
**not** a shipped repository dependency. For each commit the script uploaded every changed blob,
rebuilt the tree from its parent tree, and created the commit object with the local author, committer
and message; each object's SHA was compared with the local one **before** the next object was made.
All five matched exactly:

```
91535b67840cde707acd7d9d426601018c27bcd5
f5fe7ae2ef71d907816543ca19b3d807346dda21
af3949d7ff4725de9c99aaae89e7487876e2defe
3c3c2648ba147ad2e51c8f0aae0adbbfe642f7e3
8b57cd2ad0d09d5d577104ecf4100b654ca148e7
```

Only then was `refs/heads/main` moved with `{"sha": <last>, "force": false}` — a non-forced
fast-forward from `b5db84f88f5cf2c848223a8ee797046d1464f163`, with no history rewriting, no tag
movement and no release asset change. `gh api repos/.../commits/main --jq .sha` →
`8b57cd2ad0d09d5d577104ecf4100b654ca148e7`. The local `origin/main` was then synced with
`git update-ref` (a local remote-tracking cache, not a commit), because `git fetch` cannot traverse
the same blocked host; `git rev-list --count origin/main..HEAD` → 0. This is the first of the two
pushes authorised verbatim in the Phase 0 entry; it is attributed here rather than left implicit.

**Run `42337259111`, event `push`, tip `8b57cd2`, attempt 1, `completed success`**, created
`2026-11-07T04:10:28Z`, updated `04:19:02Z`. Four jobs, all `success`, each with 13–14 steps — no
cancelled job and no zero-step runner, so §15.5's cancelled-run rule is not engaged:

| lane | runner | window (UTC) | reading |
|---|---|---|---|
| Format and static checks | `ubuntu-latest` / `GitHub Actions 1000010254` | 04:10:31–04:11:52 | `All checks passed!`; `232 files already formatted`; `Success: no issues found in 74 source files`; 12 keys, 10 `ok`, 2 `SKIP`; `declared_plants: 190`; `lanes_documented_vs_executed_gap: 0`; `Evidence is intact.` |
| macOS native C++ and Python parity | `macos-15` / `GitHub Actions 1000010255` | 04:10:31–04:13:18 | `100% tests passed out of 204`; `98 passed in 2.27s` |
| Benchmark suite against live oracles | `ubuntu-latest` / `GitHub Actions 1000010256` | 04:10:31–04:19:02 | `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 327.1s total` |
| Configure, build, C++ tests, Python tests | `ubuntu-latest` / `GitHub Actions 1000010257` | 04:10:31–04:17:25 | `100% tests passed out of 204`; **`490 passed, 5 skipped in 201.70s`** |

**The count that mattered did not move.** `490 passed, 5 skipped` is identical to the readings at
`8ffcb32`, `adf9918` and `b5db84f`. The new assertions live inside an existing test, so the counted
pair stays 560/491 and no gold list, plant anchor or report PDF moved for this unit.

**One caveat, unchanged and still not diagnosed.** The benchmark summary prints
`revision: 8b57cd2ad0d0 (working tree was dirty at run time)` for the fourth consecutive run. It is
the same line V3 §9 named; this unit neither explains it nor cites any number from that job's
generated artifacts.

**N9 is a development-vantage proof, not a CI lane.** The `190/190` sweep summary stands on its own
reading. `plants_not_rejected_by_their_guard` remains `SKIP` on the runner by design, so no CI job
is claimed to have run the sweep and no CI result is written into that key.

**Archival state after the push.** Local `HEAD` = `origin/main` =
`8b57cd2ad0d09d5d577104ecf4100b654ca148e7`; `git status --porcelain` 0 lines; `v1.9.0` = `d9deb7f`,
unmoved; `evidence/manifest.json` intact at 95 entries and re-verified by the lint job.

**The terminal commit.** This entry is itself a commit; its own CI is read after the second push and
reported in the session handoff rather than written into the file whose content is fixed before that
push — the same convention V2, V3, V4-01 and V4-02 used. The second push authorised verbatim in the
Phase 0 entry carries this entry only; no third is implied.

---

### 2026-11-07, V4 Phase 0 for V4-04 — the status name assigned twice, measured at `e4ec510`

**Revision and vantage.** `HEAD` = `origin/main` = `e4ec51036ddb578c84508610bf2b8052059d7ed8`,
`git status --porcelain` 0 lines, `v1.9.0` tag object `d9deb7f` unmoved. Vantage: the development
checkout, `.venv` Python 3.12, macOS. The declared counts were re-measured, not inherited: **190**
plants (`declared_plants: 190` from the ceilings reading), **12** ceiling keys (10 `ok` / 2 `SKIP`),
**95** manifest `artifacts`, **232** formatter-tracked files, **560** collected pytest nodes.

**The gap, as a reading rather than a recollection.** `runner.py` assigns `ESCAPED` twice:

```
85: ESCAPED = "guard-stayed-green"
94: ESCAPED = "no-guard-objected"
```

`decide()` returns `ESCAPED` when `guard_returncode == 0`, so a sweep can only ever print the
**second** value; the first is unreachable code that reads like a live status. `docs/interview_defense.md:873`
still says a probe defect "comes back `guard-stayed-green`", i.e. it quotes the string this harness
can no longer produce. That is the V4-02 Phase 0 residue named as "the `ESCAPED` double assignment",
carried here as its own unit.

**The reference census, so the repair stays scoped.** `git grep` finds **25** occurrences of
`guard-stayed-green` in tracked files. They fall into three classes, and only the first two move:

| class | occurrences | disposition |
|---|---|---|
| the dead assignment | `runner.py:85` | deleted; the live value moves up into the status block |
| current-behaviour prose | `docs/interview_defense.md:873` | re-keyed to `no-guard-objected` |
| historical readings and substring hits | 23, including `runner.py:93`'s `MIS_PAIRED = "named-guard-stayed-green"` (a different status, matched as a substring), `V4_LEDGER.md`'s own two records of this gap, `tests/python/test_mutation_suite.py:284`'s comment about finding 86, and the phase reports / `integrity_audit.md` / `limitations.md` / `release_notes_v1.4.0.md` / `project_scope.md` / `REFACTOR_LEDGER.md` records | **not rewritten** (§9: a reading is not retro-edited because a later tip renamed a string) |

**What the unit will change, and how it is falsified.** One deletion and one move in `runner.py`
(behaviour unchanged: `ESCAPED` still equals `"no-guard-objected"`); one string in
`docs/interview_defense.md`; an **extension** of the existing status-table test, not a new node, so
the counted pair stays 560/491. The extension parses `runner.py` and refuses any module-level
upper-case name assigned more than once, then pins `ESCAPED` to `"no-guard-objected"`. One plant
(`status-name-assigned-twice-keeps-the-last-value`) re-inserts a second `ESCAPED` assignment after
`MIS_PAIRED`, which both reddens the duplicate-assignment reading and flips the runtime value back to
the stale string; `docs/interview_defense.md:1037`'s `190/190` is re-keyed to `191/191` in the same
commit. Targeted sweep: the new plant plus the re-keyed anchor, expected `2/2`.

**The approval for this case, recorded verbatim (§14).** The maintainer's instruction is
`我都听你的，请按照你的思路建议进行，如果有什么是需要我来完成的，请告诉我具体的操作流程`, given after the
V4-03 handoff named this unit as the next one. As in V4-01…V4-03, that is a direction to choose and
execute one scope unit, not a standing approval: this unit takes **two** pushes — the
implementation-and-readings tip, and the entry recording that tip's CI — both attributed below, and no
third is implied.

**Deliberately not done in Phase 0.** No source file was edited, no plant added, no ceiling key
changed, and no historical document rewritten. The full 191-plant census is **not** claimed here: the
most recent full sweep summary is `190/190` at `f5fe7ae`, and this unit's new plant is verified by a
targeted run, exactly as V4-02's 189th plant was.

---

### 2026-11-07, V4-04 — one status name, one assignment, and a string the documents can quote

**What shipped.** `runner.py` loses the dead `ESCAPED = "guard-stayed-green"` and keeps a single
definition in the status block, `ESCAPED = "no-guard-objected"`. Behaviour is unchanged: the deleted
line was already overwritten by the surviving one, so `decide()` returns the same string it returned
before the change. `docs/interview_defense.md:873` is re-keyed to `no-guard-objected`, and line
1037's `190/190` to `191/191`. The status-table test is **extended**, not duplicated: it parses
`runner.py`'s own source, refuses any module-level upper-case name assigned more than once, and pins
`ESCAPED` to the documented string. One plant added, one anchor re-keyed.

**The targeted reading at `622b9f1`, clean tree.** The two cases were run through the gitignored
wrapper with `CODEBUDDY_SAFE_DELETE_BULK_THRESHOLD` raised for this local sweep only — the same
session-level deletion guard V4-03 diagnosed, which exists in this development environment and in no
CI step:

```
caught  docs-command-comment-counts-superseded-plants
caught  status-name-assigned-twice-keeps-the-last-value
2/2 planted defects were rejected by their guard.
```

exit 0; `git status --porcelain` printed 0 lines afterwards, so both targets were restored
byte-for-byte.

**Why the new plant is falsifiable, not merely different.** Its anchor is
`MIS_PAIRED = "named-guard-stayed-green"`; the replacement inserts a second
`ESCAPED = "guard-stayed-green"` after it. That does two things at once: the module-level
duplicate-assignment reading fails, and the stale string becomes the **runtime** value again, so the
`ESCAPED` pin fails as well. A plant that looked like the old defect without changing the reachable
value would leave the second assertion green and would be a no-op for half the guard.

**Counts that moved, and the ones that did not.**

| quantity | before | after | why |
|---|---|---|---|
| declared plants | 190 | **191** | the new plant; one anchor re-keyed in the same commit |
| pytest nodes | 560 / 491 | **560 / 491** | the test was extended, not added |
| ceiling keys | 12 | **12** | no new policy row; the change is inside an existing guard |
| formatter-tracked files | 232 | **232** | no new document |

**Local gates at `622b9f1`.** `ruff check .` → `All checks passed!`; `ruff format --check .` →
`232 files already formatted`; `mypy python/quantrisk tools` → `Success: no issues found in 74 source
files`; `--check-ceilings` → 12 keys, 10 `ok`, 2 `SKIP`, `declared_plants: 191`,
`tracked_files_outside_the_formatter_corpus: 0`; `verify_evidence_manifest` → `Evidence is intact.`;
`pytest -q --basetemp=<fresh>` → **`559 passed, 1 failed in 148.22s`**, the single failure being the
bytecode-cache plant this sandbox cannot run — the same one V3, V4-02 and V4-03 recorded.

**The census this unit does not claim.** The most recent full sweep summary is `190/190` at
`f5fe7ae`. The 191st plant is verified by the targeted `2/2` above, **not** by a 191-plant full
sweep, and this entry does not write a `191/191` summary line it has not captured. Recording the
difference is the point.

**Deliberately not done, named rather than omitted.**

1. **The 23 historical `guard-stayed-green` occurrences are not rewritten.** They are readings taken
   at other tips (§9), including `V4_LEDGER.md`'s own two records of this gap and
   `tests/python/test_mutation_suite.py:284`'s comment about finding 86. `MIS_PAIRED =
   "named-guard-stayed-green"` is a different status and stays.
2. **The with-extras census, the refusal-path pytest guard and the `docs/` re-derivation lane**
   remain open, unchanged by this unit.
3. **No ceiling key was added for "no name assigned twice".** The reading lives inside the existing
   status-table test; a policy row would need its own instrument and its own failure mode.

**The push.** This entry is committed after the implementation commit and pushed with it; the CI
reading for the pushed tip is appended in the next entry once `gh` reports it, and the ledger states
no outcome before the tool does. Both pushes authorised verbatim in the Phase 0 entry are consumed by
this unit's implementation-and-readings tip and the entry recording its CI.






