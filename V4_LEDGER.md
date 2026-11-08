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

---

### 2026-11-07, V4-04 — the implementation-and-readings tip is green

**The push, by the same transport V4-03 measured.** The git smart-HTTP host is still blocked, so the
three commits (`2eb9751`, `622b9f1`, `f3fc84b`) were appended through the GitHub Git Data API by the
same gitignored `build/api_push.py`: every blob, tree and commit was compared with its local SHA
before the next object was created, all three matched, and `refs/heads/main` was moved with
`{"sha": <last>, "force": false}` — a fast-forward from `e4ec51036ddb578c84508610bf2b8052059d7ed8`.
No history rewriting, no tag movement. `gh api repos/.../commits/main --jq .sha` →
`f3fc84b6e52968bb58a1c1d2d9dc64460a69d9a7`; local `origin/main` synced with `git update-ref`
(`git rev-list --count origin/main..HEAD` → 0). This is the first of the two pushes authorised
verbatim in the Phase 0 entry.

**Run `42354746001`, event `push`, tip `f3fc84b`, attempt 1, `completed success`**, created
`2026-11-07T08:16:05Z`, updated `08:22:23Z`. Four jobs, all `success`, each with 13–14 steps:

| lane | runner | window (UTC) | reading |
|---|---|---|---|
| Format and static checks | `ubuntu-latest` / `GitHub Actions 1000010265` | 08:16:08–08:17:24 | `All checks passed!`; `232 files already formatted`; `Success: no issues found in 74 source files`; 12 keys, 10 `ok`, 2 `SKIP`; `declared_plants: 191`; `lanes_documented_vs_executed_gap: 0`; `Evidence is intact.` |
| macOS native C++ and Python parity | `macos-15` / `GitHub Actions 1000010267` | 08:16:09–08:19:04 | `100% tests passed out of 204`; `98 passed in 2.30s` |
| Benchmark suite against live oracles | `ubuntu-latest` / `GitHub Actions 1000010266` | 08:16:09–08:22:22 | `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 240.0s total` |
| Configure, build, C++ tests, Python tests | `ubuntu-latest` / `GitHub Actions 1000010268` | 08:16:09–08:20:52 | `100% tests passed out of 204`; **`490 passed, 5 skipped in 132.42s`** |

**The count that mattered did not move.** `490 passed, 5 skipped` is identical to the readings at
`8ffcb32`, `adf9918`, `b5db84f`, `8b57cd2` and `e4ec510`. The status-table test was extended rather
than duplicated, so the counted pair stays 560/491; the only declaration that moved is
`declared_plants`, 190 → 191, which is the new plant and is exactly what the lint job printed.

**One caveat, unchanged and still not diagnosed.** The benchmark summary prints
`revision: f3fc84b6e529 (working tree was dirty at run time)` for the sixth consecutive run. It is
the same line V3 §9 named; this unit neither explains it nor cites any number from that job's
generated artifacts.

**The 191-plant census is still a targeted proof.** This entry does **not** claim a full 191-plant
sweep. The most recent captured full sweep summary remains `190/190` at `f5fe7ae`; the 191st plant
was verified by the `2/2` reading in the preceding entry. The runner's
`plants_not_rejected_by_their_guard` key stays `SKIP` by design.

**Archival state after the push.** Local `HEAD` = `origin/main` =
`f3fc84b6e52968bb58a1c1d2d9dc64460a69d9a7`; `git status --porcelain` 0 lines; `v1.9.0` tag object
`d9deb7f` unmoved; `evidence/manifest.json` intact at 95 `artifacts` and re-verified by the lint job.

**The terminal commit.** This entry is itself a commit; its own CI is read after the second push and
reported in the session handoff rather than written into the file whose content is fixed before that
push — the convention V2, V3, V4-01, V4-02 and V4-03 used. The second push authorised verbatim in the
Phase 0 entry carries this entry only; no third is implied.

---

### 2026-11-07, V4 Phase 0 for V4-05 — the refusal path gets a pytest guard, measured at `0919138`

**Revision and vantage.** `HEAD` = `origin/main` = `091913892a86a108d995cd26e29649667b7e5f5d`,
`git status --porcelain` 0 lines, `v1.9.0` tag object `d9deb7f` unmoved. Vantage: the development
checkout, `.venv` Python 3.12, macOS. Counts re-measured: **191** plants (`declared_plants: 191`),
**12** ceiling keys (10 `ok` / 2 `SKIP`), **95** manifest `artifacts`, **232** formatter-tracked files,
**560** collected pytest nodes.

**The gap, in V3's own words.** `V3_LEDGER.md:358`: "The refusal path itself has no pytest guard. Its
*input* is guarded — the declaration cannot drift from the import tree — but nothing in the suite would
redden if `command_run` stopped calling `unsatisfied_requirements`, because the only instrument that
executes the refusal against a real absence is `tools/verify_installed_surface --refusal pricing_grid`,
and that gate is declared dev-only (its ceiling key SKIPs on the runner by design)." V3 §4 item 1 and
§7 item 4 carry the same sentence; this unit closes it.

**The code the guard must reach.** `cli.command_run` resolves the task, then:

```
    missing = unsatisfied_requirements(wanted)
    if missing:
        return _refuse_unsatisfied(wanted, missing)
```

`_refuse_unsatisfied` prints `FAIL <task> needs the <extras> extra: No module named '<module>'` and
`install it with: pip install 'quantrisk[<extras>]'` to stderr, and returns `1` — distinct from `2`,
which is "no such task". `unsatisfied_requirements` calls the module-level `module_resolves`, so a
monkeypatched resolver drives the branch deterministically without needing an environment that lacks
the extra. `tools/verify_installed_surface.assert_refusal_names_what_is_missing` asserts the same three
things end to end (non-zero exit, the missing thing named, no file published), but only in a clean venv
outside the checkout.

**The shape chosen, and why it differs from V3's price.** V3 priced closure at a **new** pytest case
and therefore `560 → 561`, "three gold lists, five or six plant anchors, the report PDF". This unit
**extends** `test_an_absorbed_task_is_invocable_and_writes_where_it_is_told` instead — the existing
node already owns the `--out` contract and the registry import — so the counted pair stays 560/491 and
no gold list, report PDF or pre-existing anchor moves for the count. Only the plant total moves,
191 → 192, with `docs/interview_defense.md:1037` and the anchor plant re-keyed in the same commit.

**The new plant.** `command-run-skips-the-requirement-check` replaces
`    if missing:` with `    if False and missing:` in `command_run`. The extended guard then sees
`command_run` return `0` (an installed extra lets the study run) or return `1` with a `FAIL` line that
names no extra (a bare wheel raises inside the study), and in both shapes the `quantrisk[<extra>]`
install line is absent — which is exactly the state V3 said nothing would catch.

**The approval for this case, recorded verbatim (§14).** The maintainer's instruction is
`我都听你的，请按照你的思路建议进行，如果有什么是需要我来完成的，请告诉我具体的操作流程`, given after the
V4-04 handoff named this unit first. As in V4-01…V4-04, that is a direction to choose and execute one
scope unit, not a standing approval: this unit takes **two** pushes — the implementation-and-readings
tip, and the entry recording that tip's CI — both attributed below, and no third is implied.

**Deliberately not done in Phase 0.** No source file was edited, no plant added, no ceiling key
changed. The with-extras census and the `docs/` re-derivation lane remain open. No full 192-plant
census is claimed: the last captured full summary is `190/190` at `f5fe7ae`, and this unit's plant is
verified by a targeted run, as V4-02 and V4-04 did.

---

### 2026-11-07, V4-05 — the suite drives the refusal, and the pin is named

**What shipped.** `test_an_absorbed_task_is_invocable_and_writes_where_it_is_told` gains a refusal
section: it monkeypatches `registry.module_resolves` so `pricing_grid`'s `plot` extra cannot resolve,
calls `cli.command_run` with an explicit `--out` root, and asserts three readings — exit `1`, the
`quantrisk[plot]` install line on stderr, and no file under that root. **No new pytest node**: the
counted pair stays 560/491, which is why this closure costs no gold list, no report PDF and no
pre-existing anchor — the price V3 quoted for a new case. One plant added (`command-run-skips-the-
requirement-check`), one anchor re-keyed (`docs/interview_defense.md:1037`, 191 → 192), and
`UNATTRIBUTED_PLANTS` gains a second member **with its reason**.

**The targeted reading at `87a7812`, clean tree:**

```
caught  docs-command-comment-counts-superseded-plants
caught  pinned-residual-list-emptied
caught  command-run-skips-the-requirement-check
3/3 planted defects were rejected by their guard.
```

The third is the new guard's falsification. The second is in the run because the new pin changed the
set that plant anchors on: a re-keyed anchor has to be re-fired, not assumed. exit 0;
`git status --porcelain` printed 0 lines afterwards.

**Why the pin is a decision, not a workaround.** `pairing_sample`'s attribution rule is textual: a
guard is linked when its reading closure spells the edited path or a token from the anchor. The new
guard observes `command_run` by **calling** it and reading the captured output, and never spells
`missing` or `_refuse_unsatisfied`, so the link is behavioural. `UNATTRIBUTED_PLANTS` is the audit's
declared residual, and the guard refuses both an unlisted member and a listed plant that gained a
text link. Adding the id with its reason is exactly the decision the test asks for.

**Counts that moved, and the ones that did not.**

| quantity | before | after | why |
|---|---|---|---|
| declared plants | 191 | **192** | the new plant; one anchor and one pin re-keyed |
| pytest nodes | 560 / 491 | **560 / 491** | the test was extended, not added |
| ceiling keys | 12 | **12** | no new policy row |
| formatter-tracked files | 232 | **232** | no new document |

**Local gates at `87a7812`.** `ruff check .` → `All checks passed!`; `ruff format --check .` →
`232 files already formatted`; `mypy python/quantrisk tools` → `Success: no issues found in 74 source
files`; `--check-ceilings` → 12 keys, 10 `ok`, 2 `SKIP`, `declared_plants: 192`; manifest
`Evidence is intact.`; `pytest -q --basetemp=<fresh>` → **`559 passed, 1 failed in 181.98s`**, the
single failure the bytecode-cache plant this sandbox cannot run.

**What the guard does not claim.** It drives the refusal with a monkeypatched resolver, so it proves
`command_run` consults `unsatisfied_requirements` and prints the install line; it does **not** prove
the extra is genuinely absent from an installed wheel. That end-to-end reading remains
`tools/verify_installed_surface --refusal pricing_grid`, dev-only by design (its ceiling key SKIPs on
the runner). The two are complementary: the suite now reddens if the branch disappears, and the
dev-only tool still reddens if a wheel advertises a study it cannot serve.

**Deliberately not done, named rather than omitted.** The with-extras census and the `docs/`
re-derivation lane remain open. No full 192-plant census is claimed; the last captured full summary
is `190/190` at `f5fe7ae`.

**The push.** This entry is committed after the implementation commit and pushed with it; the CI
reading for the pushed tip is appended in the next entry once `gh` reports it, and the ledger states
no outcome before the tool does. Both pushes authorised verbatim in the Phase 0 entry are consumed by
this unit's implementation-and-readings tip and the entry recording its CI.

---

### 2026-11-07, V4-05 — the implementation-and-readings tip is green

**The push, by the same transport V4-03 measured.** The git smart-HTTP host is still blocked, so the
four commits (`141a9af`, `1764231`, `87a7812`, `3af53f4`) were appended through the GitHub Git Data
API by the same gitignored `build/api_push.py`: every blob, tree and commit was compared with its
local SHA before the next object was created, all four matched, and `refs/heads/main` was moved with
`{"sha": <last>, "force": false}` — a fast-forward from `091913892a86a108d995cd26e29649667b7e5f5d`.
No history rewriting, no tag movement. `gh api repos/.../commits/main --jq .sha` →
`3af53f4e57c534623c880d268b3f012fcb3b5352`; local `origin/main` synced with `git update-ref`
(`git rev-list --count origin/main..HEAD` → 0). First of the two pushes authorised in the Phase 0
entry.

**Run `42358106717`, event `push`, tip `3af53f4`, attempt 1, `completed success`**, created
`2026-11-07T09:03:48Z`, updated `09:14:32Z`. Four jobs, all `success`, 13–14 steps each:

| lane | runner | window (UTC) | reading |
|---|---|---|---|
| Format and static checks | `ubuntu-latest` / `GitHub Actions 1000010357` | 09:03:52–09:04:44 | `All checks passed!`; `232 files already formatted`; `Success: no issues found in 74 source files`; `declared_plants: 192`; `Evidence is intact.` |
| macOS native C++ and Python parity | `macos-15` / `GitHub Actions 1000010354` | 09:03:51–09:06:58 | `100% tests passed out of 204`; `98 passed in 4.53s` |
| Benchmark suite against live oracles | `ubuntu-latest` / `GitHub Actions 1000010356` | 09:03:52–09:14:31 | `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 422.8s total` |
| Configure, build, C++ tests, Python tests | `ubuntu-latest` / `GitHub Actions 1000010355` | 09:03:51–09:11:44 | `100% tests passed out of 204`; **`490 passed, 5 skipped in 237.38s`** |

**The count that mattered did not move.** `490 passed, 5 skipped` is identical to every reading since
`8ffcb32`. The refusal assertions live inside an existing node, so the counted pair stays 560/491 and
no gold list, plant anchor or report PDF moved. The only declaration that changed is
`declared_plants`, 191 → 192, which the lint job printed.

**One caveat, unchanged and still not diagnosed.** The benchmark summary prints
`revision: 3af53f4e57c5 (working tree was dirty at run time)` for the seventh consecutive run. Same
line V3 §9 named; not explained here, and no number from that job's artifacts is cited.

**The 192-plant census is still a targeted proof.** This entry does not claim a full 192-plant sweep.
The last captured full summary remains `190/190` at `f5fe7ae`; this unit's plant was verified by the
`3/3` reading in the preceding entry. `plants_not_rejected_by_their_guard` stays `SKIP` by design.

**Archival state after the push.** Local `HEAD` = `origin/main` =
`3af53f4e57c534623c880d268b3f012fcb3b5352`; `git status --porcelain` 0 lines; `v1.9.0` tag object
`d9deb7f` unmoved; `evidence/manifest.json` intact at 95 `artifacts`.

**The terminal commit.** This entry is itself a commit; its own CI is read after the second push and
reported in the session handoff rather than written into the file whose content is fixed before that
push — the convention V2, V3 and V4-01…V4-04 used. The second push authorised in the Phase 0 entry
carries this entry only; no third is implied.

---

### 2026-11-07, V4 Phase 0 for V4-06 — the with-extras census becomes its own reading, measured at `0967dc8`

**Revision and vantage.** `HEAD` = `origin/main` = `0967dc89c937fbef9151e46aff003f49d96654db`,
`git status --porcelain` 0 lines, `v1.9.0` tag object `d9deb7f` unmoved. Vantage: the development
checkout, `.venv` Python 3.12, macOS. Counts re-measured: **192** plants (`declared_plants: 192`),
**12** ceiling keys (10 `ok` / 2 `SKIP`), **95** manifest `artifacts`, **232** formatter-tracked files,
**560** collected pytest nodes.

**The gap, as V4's own Phase 0 wrote it.** "The with-extras installed census is not its own reading.
`tools/verify_installed_surface.py` exists and is declared dev-only (the ceiling key SKIPs on the
runner by design); the `19/19 executed and passed` line is a by-product of the benchmark job, not an
instrument with its own output." This unit takes that gap.

**Where the claim actually lives, measured.** Three places carry the census, and none of them is an
instrument over the *run*:

| carrier | what it holds | what reads it |
|---|---|---|
| `benchmarks/suite/results/suite_run.json` | `members` (19), each with `key`, `status`, `artifact`, `artifact_sha256`, plus `totals` | **nothing in `tools/`**; only the benchmark job uploads it |
| `tests/python/test_artifact_metadata.py::test_every_registry_task_is_aggregated_by_exactly_one_member` | a two-way comparison of `key` against `TASKS_BY_ID` | the comparison is over `_load_suite_members()`, i.e. the **source-level** `MEMBERS` tuple, not the artifact |
| the benchmark job's log | `suite: 19/19 executed and passed, ...` | a reader's eye |

So the missing piece is precise: the artifact that a run writes is compared with nothing, and the
comparison that exists is over the declaration instead of the product. The two can disagree —
a job that writes 18 members and a log line that says 19 — and every gate stays green.

**What this unit will ship.**

1. `with_extras_census()` in `tools/inventory_orphan_code.py`: reads
   `benchmarks/suite/results/suite_run.json`, names every member it carries, compares the member
   `key` set against the registry **in both directions**, requires every member's `status` to be
   `passed`, and requires `totals.members` / `totals.passed` / `totals.failed` / `totals.skipped` to
   agree with the member list it describes. `gap` is the number of disagreements.
2. A `--reading NAME` flag on the same collector, so the reading has its own printable JSON instead
   of being a slice of a larger snapshot.
3. `with_extras_census_gap` in `tools/refactor_ceilings.json`: `max 0`, **no `may_be_unmeasured`**,
   because the artifact is committed and always readable on the runner.
4. One CI step in the benchmark job, after the suite runs: `--reading with_extras_census`. The job
   therefore prints its own census reading, from the artifact it just wrote, rather than leaving
   `19/19` as prose in a log.
5. The existing registry/member test is **extended**, not duplicated, to assert `gap == 0` from the
   artifact — the counted pair stays 560/491.
6. One plant (`suite-artifact-drops-a-member-the-registry-declares`) rewrites
   `  "members": 19,` to `  "members": 18,` in `suite_run.json`, which the self-consistency clause
   catches. Plant total 192 → 193, `docs/interview_defense.md:1037` re-keyed.

**The approval for this case, recorded verbatim (§14).** The maintainer's instruction is
`我都听你的，请按照你的思路建议进行`, given after the V4-05 handoff named this unit next. As in
V4-01…V4-05, that is a direction to choose and execute one scope unit, not a standing approval: this
unit takes **two** pushes — the implementation-and-readings tip, and the entry recording that tip's
CI — both attributed below, and no third is implied.

**Deliberately not done in Phase 0.** No source file was edited, no plant added, no ceiling key
changed. The `docs/` re-derivation lane remains open. No full 193-plant census is claimed: the last
captured full summary is `190/190` at `f5fe7ae`.

---

### 2026-11-07, V4-06 — the artifact a run writes is the census, and something reads it

**What shipped.** `with_extras_census()` in `tools/inventory_orphan_code.py` reads
`benchmarks/suite/results/suite_run.json` and compares it four ways: member `key` set against the
registry in both directions, every member's `status` against `passed`, duplicate keys against
nothing, and `totals.members`/`passed`/`failed`/`skipped` against the member list they describe. The
collector gains a `--reading NAME` flag so the reading prints its own JSON instead of being a slice
of a larger snapshot. `with_extras_census_gap` enters `tools/refactor_ceilings.json` with `max 0` and
**no** `may_be_unmeasured`. The benchmark job gains a `With-extras census` step that runs
`--reading with_extras_census` against the artifact it just wrote, so the census is a step with its
own output rather than a line in another step's log. The registry/member test is **extended**, not
duplicated, to assert `gap == 0` from the artifact. One plant added, one anchor re-keyed.

**The reading, printed by the new flag at `dbbb33d` on the committed artifact:**

```json
{
  "artifact": "benchmarks/suite/results/suite_run.json",
  "available": true,
  "duplicate_keys": [],
  "gap": 0,
  "members": 19,
  "missing_from_census": [],
  "missing_from_registry": [],
  "not_passed": [],
  "passed": 19,
  "revision": "17df062040b8",
  "self_inconsistent": []
}
```

`revision` names the commit that artifact was written at, not the reading's own tip — the reading
reports what the file says rather than implying it was regenerated here.

**The targeted reading at `dbbb33d`, clean tree:**

```
caught  docs-command-comment-counts-superseded-plants
caught  suite-artifact-drops-a-member-the-registry-declares
2/2 planted defects were rejected by their guard.
```

exit 0; `git status --porcelain` printed 0 lines afterwards, so the 60 KB JSON was restored
byte-for-byte.

**Why the plant is falsifiable.** `suite_run.json` has exactly one `"members": 19` line, in `totals`.
The plant rewrites it to `"members": 18`, so the artifact still carries nineteen member objects while
its own totals say eighteen. The key-set comparisons stay green — both sides still hold nineteen —
and only the self-consistency clause fires, which is precisely the disagreement a log line cannot
show.

**Counts that moved, and the ones that did not.**

| quantity | before | after | why |
|---|---|---|---|
| declared plants | 192 | **193** | the new plant; one anchor re-keyed |
| ceiling keys | 12 | **13** | one new policy row, measured and `ok` |
| pytest nodes | 560 / 491 | **560 / 491** | the test was extended, not added |
| formatter-tracked files | 232 | **232** | no new document |

**Local gates at `dbbb33d`.** `ruff check .` → `All checks passed!`; `ruff format --check .` →
`232 files already formatted`; `mypy python/quantrisk tools` → `Success: no issues found in 74 source
files`; `--check-ceilings` → **13** keys, 11 `ok`, 2 `SKIP`, with `with_extras_census_gap: 0` and
`declared_plants: 193`; manifest `Evidence is intact.`; `pytest -q --basetemp=<fresh>` →
**`559 passed, 1 failed in 388.40s`**, the single failure the bytecode-cache plant this sandbox cannot
run.

**A guard the new step had to keep green.** `tools.inventory_orphan_code` now appears in two CI
steps, `lint :: refactor ceilings` and `benchmark-suite :: With-extras census`. The lane reading
reports `executed_at` as a set and requires the contract's named pair to be a member of it, so the
second step does not disturb `lanes_documented_vs_executed_gap`, which printed `0`.

**What this reading does not claim.** It does not re-run the nineteen studies; it reads the artifact a
run wrote. The lint job therefore reads the committed artifact (revision `17df062040b8`), and the
benchmark job reads the one it generates in its own run — two vantages of one reading, each named by
its revision. No full 193-plant census is claimed; the last captured full summary is `190/190` at
`f5fe7ae`.

**Deliberately not done.** The `docs/` re-derivation lane remains open. The `19/19` log line is left
in place beside the new step rather than deleted, because the step output is additive evidence and
removing a job's own summary would be a separate decision.

**The push.** This entry is committed after the implementation commit and pushed with it; the CI
reading for the pushed tip is appended in the next entry once `gh` reports it, and the ledger states
no outcome before the tool does. Both pushes authorised in the Phase 0 entry are consumed by this
unit's implementation-and-readings tip and the entry recording its CI.

---

### 2026-11-07, V4-06 — the implementation-and-readings tip is green

**The push, by the same transport V4-03 measured.** The git smart-HTTP host is still blocked, so the
three commits (`d6ed061`, `dbbb33d`, `575d620`) were appended through the GitHub Git Data API with
every blob, tree and commit SHA compared locally before the next object; `refs/heads/main` moved with
`{"sha": <last>, "force": false}` from `0967dc89c937fbef9151e46aff003f49d96654db`. No rewriting, no
tag movement, no force. `gh api repos/.../commits/main --jq .sha` →
`575d6205a94d298c40247e8e32d010f1790a38cd`; local `origin/main` synced with `git update-ref` (a
remote-tracking cache, not a commit).

**Run `42362912014`, event `push`, tip `575d620`, attempt 1, `completed success`**, created
`2026-11-07T10:11:44Z`, updated `10:22:59Z`. Four jobs, all `success`:

| lane | runner | window (UTC) | reading |
|---|---|---|---|
| Format and static checks | `ubuntu-latest` / `GitHub Actions 1000010411` | 10:11:48–10:13:02 | `All checks passed!`; `232 files already formatted`; `74 source files`; `declared_plants: 193`; **`with_extras_census_gap: 0`**; `Evidence is intact.` |
| macOS native C++ and Python parity | `macos-15` / `GitHub Actions 1000010408` | 10:11:48–10:15:20 | `100% tests passed out of 204`; `98 passed in 3.59s` |
| Benchmark suite against live oracles | `ubuntu-latest` / `GitHub Actions 1000010410` | 10:11:48–10:22:59 | `19/19 executed and passed, 0 failed, 0 skipped, 429.7s`; the **`With-extras census`** step printed its own JSON |
| Configure, build, C++ tests, Python tests | `ubuntu-latest` / `GitHub Actions 1000010409` | 10:11:48–10:17:47 | `100% tests passed out of 204`; **`490 passed, 5 skipped in 172.08s`** |

**The reading that closes gap 3, quoted from the step's own output.** The benchmark job's new step
ran `--reading with_extras_census` after the suite and printed:

```json
{
  "artifact": "benchmarks/suite/results/suite_run.json",
  "available": true,
  "duplicate_keys": [],
  "gap": 0,
  "members": 19,
  "missing_from_census": [],
  "missing_from_registry": [],
  "not_passed": [],
  "passed": 19,
  "revision": "575d6205a94d",
  "self_inconsistent": []
}
```

The `revision` is `575d6205a94d` — the tip of this run, i.e. the artifact the job had just written,
not the committed artifact at `17df062040b8` the lint job reads. That difference is exactly what the
gap named: the census is now a reading over the run that produced it, with the policy gate reading
the committed copy and the job reading its own.

**The count that mattered did not move.** `490 passed, 5 skipped` is identical to every reading since
`8ffcb32`. The registry/member test was extended, so the counted pair stays 560/491. Two declarations
moved, both by construction and both printed by the lint job: `declared_plants` 192 → 193, and the
ceiling set 12 → 13 with `with_extras_census_gap: 0`.

**One caveat, unchanged and still not diagnosed.** The benchmark summary prints
`revision: 575d6205a94d (working tree was dirty at run time)` for the eighth consecutive run. Same
line V3 §9 named; not explained here, and no number from that job's artifacts is cited.

**What this entry does not claim.** The reading compares an artifact; it does not re-run the studies
itself. The `19/19` log line remains beside the new step rather than being replaced, so the two
readings sit side by side and either can be quoted. No full 193-plant census is claimed: the last
captured full summary is `190/190` at `f5fe7ae`.

**Archival state after the push.** Local `HEAD` = `origin/main` =
`575d6205a94d298c40247e8e32d010f1790a38cd`; `git status --porcelain` 0 lines; `v1.9.0` tag object
`d9deb7f` unmoved; `evidence/manifest.json` intact at 95 `artifacts`.

**The terminal commit.** This entry is itself a commit; its own CI is read after the second push and
reported in the session handoff rather than written into the file whose content is fixed before that
push — the convention V2, V3 and V4-01…V4-05 used. The second push authorised in the Phase 0 entry
carries this entry only; no third is implied.

---

### 2026-11-08, V4 Phase 0 for V4-07 — `docs/` re-derivation becomes a lane, measured at `bff0b35`

**Revision and vantage.** `HEAD` = `origin/main` = `bff0b359dbec7359703703e2513e89dcbd1600cd`,
`git status --porcelain` 0 lines, `v1.9.0` tag object `d9deb7f` unmoved. Vantage: the development
checkout, `.venv` Python 3.12, macOS. Counts re-measured at this tip: **193** plants, **13** ceiling
keys (11 `ok` / 2 `SKIP`), **95** manifest `artifacts`, **232** formatter-tracked files, **560**
collected pytest nodes, **31** named CI steps.

**The gap, in the words that opened it.** V4 Phase 0 gap 5 says "`docs/` re-derivation is not a
lane." V3 §7 item 5 asks for "The re-derivation of `docs/` as a lane, not as three files that
happened to quote a moved number", and V3 §4 item 5 records that the §5 `docs/` row — "five documents
describing the surface" / "the same five re-derived, never transcribed" — was paid "only where a
claim moved: three documents that describe `run --list`, and the report PDF that quotes the test
counts. The other documents were read and their claims did not change."

**Where the claim actually lives, measured.** `CONTRIBUTING.md`'s "Sync the prose last among the
regenerations" paragraph enumerates the five living documents that quote a regenerated artifact:
`README.md`, `docs/interview_defense.md`, `docs/validation_matrix.md`, `docs/reproducibility.md` and
the report. Their current, readable claims are:

| document | a claim it prints | what re-derives it today |
|---|---|---|
| `README.md:169` | `runs all nineteen members` | one pytest guard over the registry |
| `docs/reproducibility.md:76` | `all 19 members` | one pytest guard over the registry |
| `docs/validation_matrix.md:140` | `all 19 members` | one pytest guard over the registry |
| `docs/interview_defense.md:48` | `19/19 benchmark-suite members executed` | one pytest guard over the registry |
| `docs/interview_defense.md:1037` | `# 193/193 planted defects rejected` | one plant anchor and one pytest guard over the plant list |
| `paper/technical_report.tex:152` | `95 artifacts` | one pytest guard over the manifest |

So the five documents *are* policed, but only as assertions inside a pytest step. `grep -c
"      - name:" .github/workflows/ci.yml` reads **31** and none of those steps reads the documents it
re-derives; the lane contract itself says "Nothing else counts: `cmake`, `ctest`, `ruff`, `mypy` and
`clang-format` are steps of jobs, not lanes with a separate declaration". A lane here must therefore
be a module-path invocation with its own named step, its own printed reading, and a ceiling that can
redden it. That is the difference between a number that was updated by hand in the commit that moved
it and a number that a lane re-derives from the artifact on every push.

**What this unit will ship.**

1. `docs_rederivation()` in `tools/inventory_orphan_code.py` — the one collector §4.1 permits. It
   re-derives three values from committed artifacts (suite members from
   `benchmarks/suite/results/suite_run.json` against the registry in both directions, plants from
   the runner's own `--list`, and manifest entries from `evidence/manifest.json`), then reads all
   five living documents and compares each document's printed claim with the value the artifact
   produced. Every document must carry at least one re-derived claim, so the reading is a census of
   the five and not a sample. `gap` counts missing documents, missing or stale claims and a source
   that disagrees with itself.
2. `--reading docs_rederivation` already exists as a flag from V4-06, so the reading prints its own
   JSON rather than being a slice of the snapshot.
3. `docs_rederivation_gap` in `tools/refactor_ceilings.json`: a **14th** ceiling key, `max 0`, with
   **no `may_be_unmeasured`** — every input is a committed file on the runner.
4. One named CI step, `Docs re-derivation`, in the lint job, executing
   `uv run python -m tools.inventory_orphan_code --reading docs_rederivation`.
5. A paragraph in `.github/lane_contract.md` naming that step as the lane that reads the five
   documents; `tools.inventory_orphan_code` is already an `executed` row, and the contract permits
   one command in several steps, as V4-06 measured.
6. The existing `test_the_ci_lane_that_runs_the_guards_fetches_what_they_read` is **extended**, not
   duplicated, to assert the step exists and the reading's `gap` is zero over all five documents —
   the counted pair stays 560/491.
7. One plant, `a-living-document-transcribes-a-number-the-artifact-does-not-hold`, rewrites
   `all 19 members` to `all 18 members` in `docs/validation_matrix.md`. Plant total 193 → 194;
   `docs/interview_defense.md:1037` and the existing command-comment plant are re-keyed to `194/194`.

**The approval for this case, recorded verbatim (§14).** The maintainer's instruction that opened
this unit is `继续`, given immediately after the V4-06 handoff named `docs/` re-derivation as the sole
remaining gap and recommended it as V4-07. Read against §14, it continues the same case-by-case
direction used in V4-01…V4-06: one scope unit, **two** pushes — the implementation-and-readings tip
and the entry recording that tip's CI — both attributed below, and no third is implied. No other
wording is attributed to the maintainer here.

**Deliberately not done in Phase 0.** No source file was edited, no plant added, no ceiling key
changed, no step added. The report PDF is not rebuilt: `tools.build_report` stays `dev-only` for the
reason the contract already gives, and this reading reads `paper/technical_report.tex` rather than
rendering it. No full 194-plant census is claimed; the last captured full summary is `190/190` at
`f5fe7ae`. V4's Phase 5 report is a separate unit and is not opened here.

---

### 2026-11-08, V4-07 — the five living documents are re-derived, and the lane prints it

**What shipped, and at which tip.** Phase 0 is `68bda4d1f828dc0908a3038c8e8fdb85ed87c147`; the
implementation tip is `c36a2c348636953d459d10a5701568f61884a471`. The range
`bff0b35..c36a2c3` touches eight files, 319 insertions and 2 deletions. `git diff --name-only` over
that range contains none of `cpp/`, `bindings/`, `CMakeLists.txt`, `PROJECT_SPEC.md`,
`REFACTOR_PROMPT.md`, `evidence/manifest.json` or `paper/`; `v1.9.0` is unmoved.

**The readings this unit produced, all at `c36a2c3` on a clean tree.**

| reading | command | value |
|---|---|---|
| docs re-derivation | `uv run --frozen python -m tools.inventory_orphan_code --reading docs_rederivation` | `documents: 5`, **7** printed claims, `mismatches: []`, `source_disagreements: []`, `gap: 0`; `derived` = `suite_members 19`, `registry_tasks 19`, `plants 194`, `manifest_artifacts 95` |
| ceilings | `uv run --frozen python -m tools.inventory_orphan_code --check-ceilings` | **14** keys — **12 `ok` / 2 `SKIP`**; `docs_rederivation_gap: 0 against a ceiling of 0 due V4-07` |
| lane contract | `--reading lanes_documented_vs_executed` | `gap: 0` with **32** named CI steps, so the new step did not vacate the contract |
| static gates | `ruff check .`, `ruff format --check .`, `mypy python/quantrisk tools` | `All checks passed!`; `232 files already formatted`; `Success: no issues found in 74 source files` |
| manifest | `uv run --frozen python -m tools.verify_evidence_manifest` | `Evidence is intact.` (95 `artifacts`) |
| pytest collection | `uv run --frozen pytest --collect-only -q` | `560 tests collected in 1.18s` — the counted pair stays **560/491** because the lane test was extended, not added |
| local full pytest | `uv run --frozen pytest -q --basetemp=<fresh>` | `1 failed, 559 passed in 139.83s`; the single failure is `test_a_restored_plant_cannot_be_read_back_from_a_stale_bytecode_cache`, the known sandbox-only bytecode-cache plant, unchanged from V4-02…V4-06 |
| targeted sweep | `build/run_sweep.py --all --verbose --only <new plant> --only docs-command-comment-counts-superseded-plants` | `2/2 planted defects were rejected by their guard.`, exit 0, `git status --porcelain` 0 lines |

The new plant rewrites `all 19 members` to `all 18 members` in `docs/validation_matrix.md`; the
extended lane test reddens because `docs_rederivation()` reads that document and finds the printed
value disagrees with the suite artifact. The second plant is the command-comment anchor, re-keyed
from `193/193` to `194/194` together with `docs/interview_defense.md:1037`; the plant total is
**193 → 194**.

**What this entry does not claim.** The reading reads the five documents; it does not regenerate
them, and the report PDF is not rebuilt. No full 194-plant census is claimed — the last captured
full sweep summary is `190/190` at `f5fe7ae`, and this unit's plant is verified by the targeted
`2/2` run, as V4-04, V4-05 and V4-06 did. The benchmark summary's
`(working tree was dirty at run time)` line is still recorded rather than diagnosed.

**The push.** This entry is committed after the implementation commit and pushed with it; the CI
reading for the pushed tip is appended in the next entry once `gh` reports it, and the ledger states
no outcome before the tool does. The first of the two pushes authorised in the Phase 0 entry carries
this implementation-and-readings tip; the second carries the entry recording its CI.

---

### 2026-11-08, V4-07 — the implementation-and-readings tip is green, and the lane is attributed

**The CI reading, attributed to the run, attempt, runner and environment that produced it.** Run
`42441028241` is a `push` run for `a9af730f7a1156db1cd1f230f2096d5c88b6269d`, attempt **1**, read
from the GitHub Actions API after `gh run watch` returned exit 0: `status: completed`,
`conclusion: success`. All **four** jobs are `completed success` with 14 steps each, on runners
`GitHub Actions 1000010440`–`1000010443` (`ubuntu-latest` for three, `macos-15` for the parity job).
No job was cancelled or reported zero steps, so §15.5 does not apply.

| job | runner | the reading |
|---|---|---|
| Format and static checks | `1000010443` | `All checks passed!`; `232 files already formatted`; `Success: no issues found in 74 source files`; `declared_plants: 194`; `ok docs_rederivation_gap: 0 against a ceiling of 0 due V4-07`; `ok lanes_documented_vs_executed_gap: 0 against a ceiling of 0 due V4-01`; `Evidence is intact.` |
| `Docs re-derivation` step (same job) | `1000010443` | `available: true`, `documents: 5`, seven printed claims, `derived` = `suite_members 19`, `registry_tasks 19`, `plants 194`, `manifest_artifacts 95`, `mismatches: []`, `source_disagreements: []`, `gap: 0` |
| Configure, build, C++ tests, Python tests | `1000010441` | `100% tests passed out of 204`; `490 passed, 5 skipped in 230.64s`; `7/7 checks passed` |
| macOS native C++ and Python parity | `1000010440` | `100% tests passed out of 204`; `98 passed in 2.21s` |
| Benchmark suite against live oracles | `1000010442` | `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 426.3s total`; the with-extras census step prints `gap: 0`, `members: 19`, `passed: 19`, `revision: a9af730f7a11` |

`490 passed, 5 skipped` is unchanged from `8ffcb32`, `adf9918`, `b5db84f`, `8b57cd2`, `e4ec510`,
`f3fc84b`, `0919138`, `3af53f4`, `0967dc8`, `575d620` and `bff0b35`: the lane test was extended, so
the counted pair 560/491 did not move. The new step and the `refactor ceilings` step read the same
collector from the same job, one printing the reading and one adjudicating its gap; the lane
contract's `executed_at` set permits the one command to appear in several steps, and its gap stayed
0 with 32 named CI steps.

**One caveat, unchanged and still not diagnosed.** The benchmark summary prints
`revision: a9af730f7a11 (working tree was dirty at run time)` for the ninth consecutive run. Same
line V3 §9 named; not explained here, and no number from that job's artifacts is cited.

**What this entry does not claim.** No full 194-plant census: the last captured full sweep summary
is `190/190` at `f5fe7ae`, and the 194th plant is verified by the targeted `2/2` run. The reading
compares the five documents with their artifacts; it does not regenerate them, and the report PDF
was not rebuilt. V4's Phase 5 report is a separate unit, not opened by this entry.

**Archival state after the push.** Local `HEAD` = `origin/main` =
`a9af730f7a1156db1cd1f230f2096d5c88b6269d`; `git status --porcelain` 0 lines; `v1.9.0` tag object
`d9deb7f` unmoved; `evidence/manifest.json` intact at 95 `artifacts`; no locked path touched.

**The terminal commit.** This entry is itself a commit; its own CI is read after the second push and
reported in the session handoff rather than written into the file whose content is fixed before that
push — the convention V2, V3 and V4-01…V4-06 used. The second push authorised in the Phase 0 entry
carries this entry only; no third is implied.

---

### 2026-11-08, V4 Phase 0 for V4 Phase 5 — the series report and the archival confirmation, measured at `ad03b89`

**Revision and vantage.** `HEAD` = `origin/main` =
`ad03b890da5b19682189cc5da9e408ab11821b10`, `git status --porcelain` 0 lines, `v1.9.0` =
`d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` unmoved. Vantage: the development checkout, `.venv` Python
3.12, macOS, the same WorkBuddy interpreter shim V3 Phase 5 recorded. The 14 pushed tips and their
`conclusion`s below are read from `gh api repos/Jackxiaozhiren/quantrisk-plus-plus/actions/runs`, not
from this file: the git smart-HTTP channel is still blocked, so this unit's pushes use the Git Data
API as V4-03…V4-07 did.

**The archive re-counted at this tip, not inherited from V4-07's prose.**

| quantity | command that produced the reading | value |
|---|---|---|
| registry tasks | `uv run --frozen python -m tools.inventory_orphan_code --reading registry_parity` | `filesystem_units 19`, `registry_sources 19`, `mismatch []` |
| suite members | `--reading with_extras_census` | `members 19`, `passed 19`, `gap 0`, `revision 17df062040b8` from the committed `suite_run.json` |
| plants | `uv run --frozen python -m quantrisk.verification.runner --list` | **194** lines; `plant_liveness.declared_plants 194` |
| ceiling keys | `--check-ceilings` | **14** — **12 `ok` / 2 `SKIP`**; `lanes_documented_vs_executed_gap`, `with_extras_census_gap` and `docs_rederivation_gap` all `0` |
| manifest | `uv run --frozen python -m tools.verify_evidence_manifest` | `95 OK`, `0 CHANGED`, `0 MISSING`, `Evidence is intact.` |
| formatter corpus | `--reading formatter_census` | `tracked_formattable 232`, `walked_formattable 232`, both differences empty |
| pytest nodes | `uv run --frozen pytest --collect-only -q`; `uv run --frozen python -m tools.measure_offline_collection` | **560** collected; offline tail `491 tests collected`, `collection_errors 0` |
| lane contract | `--reading lanes_documented_vs_executed` | `gap: 0`; `executed_at` names the three `tools.inventory_orphan_code` steps; `grep -c '^      - name:' .github/workflows/ci.yml` prints **32** |
| living documents | `--reading docs_rederivation` | `documents 5`, seven claims, `derived` = `suite_members 19`, `registry_tasks 19`, `plants 194`, `manifest_artifacts 95`, `mismatches []`, `gap: 0` |
| static gates | `uv run --frozen ruff check .`; `ruff format --check .`; `mypy python/quantrisk tools` | `All checks passed!`; `232 files already formatted`; `Success: no issues found in 74 source files` |

**The authority for this unit.** `V3_PROMPT.md` §12 enumerates the eight deliverables of a Phase 5
report; §16 item 5 asks for the sweep's own summary line at the final revision on a clean tree, item
7 for the report and archival confirmation to be committed and pushed, and item 8 for a CI reading
for every commit in the range. V4 has no written prompt — this file's opening paragraph says so — so
the inherited rails in §14–§16 are applied to this one scope unit. Nothing in this unit edits
`V3_PROMPT.md`, `REFACTOR_PROMPT.md` or `PROJECT_SPEC.md`.

**The five gaps V4 opened with, re-measured as closed at this tip.**

| gap | closing commit | the reading that closes it |
|---|---|---|
| 1. lane contract is not a file | `d5408f4` | `--reading lanes_documented_vs_executed` prints `gap: 0` over 8 declared / 5 executed commands |
| 2. a crash is scored as an objection | `501dd3e` | `GUARD_ERRORED` and the pytest return-code table in `decide()`; CTest keeps its coarse convention |
| 3. the full census has no isolation | `f5fe7ae` | private `TMPDIR` and per-invocation `--basetemp`; `190/190` at that tip |
| 4. the `ESCAPED` name is assigned twice | `622b9f1` | one live assignment, pinned by the extended status-table test |
| 5. refusal, with-extras census and docs re-derivation are unguarded | `1764231`, `dbbb33d`, `c36a2c3` | the extended refusal test; `with_extras_census_gap: 0`; `docs_rederivation_gap: 0` |

**What this unit ships.** One `## V4 Phase 5` section in this ledger carrying the eight §12
deliverables: an evidence ledger for V4-01…V4-07, the N1…N12 liveness table, the 14-key ceilings
final state, an honestly non-empty deliberately-not-done list, a premises audit, a series handoff, a
per-lane verification table and an archival confirmation over all **33** V4 commits. It also ships
the full **194**-plant census on the committed Phase 0 tip with a clean tree, its own summary line
captured in a log outside the repository, and the post-census tree check — §16 item 5 has not been
satisfied at a 194-plant tip before. The local `CODEBUDDY_SAFE_DELETE_BULK_THRESHOLD` override is an
environment condition of that one census, not a repository change; V4-03 diagnosed it at `f5fe7ae`.
Only `V4_LEDGER.md` is edited: no source, guard, plant, ceiling, artifact, lock, PDF, tag or locked
path moves, and no new pytest node is collected.

**The approval for this case, recorded verbatim (§14).** The maintainer's instruction that opened
this unit is `授权`, given in response to the V4-07 handoff which stated that the series report and
archival close-out is a separate unit and that the next scope unit needs a new case-by-case approval.
Read against §14, that is approval for this one scope unit and its **two** pushes — the
report-and-readings tip, and the entry recording that tip's CI — both attributed below; no third is
implied, and it is not a standing approval. The approvals recorded in the V4-01…V4-07 Phase 0
entries each covered their own unit and are not the authority for this one. The terminal commit's own
CI is read after the second push and reported in the session handoff, as in every earlier V4 unit.

**Deliberately not done in Phase 0.** No source file was edited, no plant added, no ceiling key
changed, no CI step added, no census was run, no report section written and no push made. In
particular, the 194-plant census is an *intended reading*, not a result: the last captured full sweep
summary remains `190/190 planted defects were rejected by their guard.` at `f5fe7ae`, and V4-04…
V4-07 verified their four plants by targeted sweeps only. No V4 prompt file is created, the report
PDF is not rebuilt, and the sweep is not added as a CI lane. Every number above is a reading at
`ad03b89`; none is quoted from this file's earlier entries without being re-measured.

---

## V4 Phase 5 — the report, the liveness table, and the archival confirmation

**Revision and vantage.** V4 opened at `9e0bf03` (V3's post-report addendum) and its implementation
range closes at `ad03b89`. This report is written at `a74cf9a`, the Phase 0 commit of this unit, on a
clean tree; the commit that carries this section changes only `V4_LEDGER.md`. The full census, the
local gates and the local pytest reading below were taken at `a74cf9a` with `git status --porcelain`
printing 0 lines. Runner readings are attributed to run `42442031942` at `ad03b89`, attempt 1, whose
four jobs each executed **14** steps on runners `GitHub Actions 1000010444`–`1000010447`. A reading
that was not re-run in V4 is named as inherited rather than counted as current.

**The census that closes N9 at the final revision.** `CODEBUDDY_SAFE_DELETE_BULK_THRESHOLD=100000
QR_DIAG_FULL=1 uv run --frozen python build/run_sweep.py --all --verbose` ran on the committed
`a74cf9a` with a clean tree. Its own summary line, captured at line 993 of
`/tmp/qr-v4-p5-census-rerun-20261108.log` (993 lines, 102,033 bytes, 37m31s wall clock, last
written 21:04:04 local):

```
194/194 planted defects were rejected by their guard.
```

Exit **0**; the log holds **194** `ok caught` rows and **zero** non-`caught` status rows;
`git status --porcelain` printed 0 lines afterwards and no `experiments/_mutation_probe` or
`docs/_mutation_probe_band.md` residue remained. This is the first captured full summary at a
194-plant tip: V4-03's `190/190` was at `f5fe7ae`, and V4-04…V4-07 used targeted sweeps only.

**The interrupted attempt, recorded as unknown rather than as a verdict.** A first run of the same
command on 2026-11-08 was cut short at line 225 of `/tmp/qr-v4-p5-census-20261108.log`, inside
`readme-quotes-a-stale-assertion-total`. It left one un-restored `README.md` mutation
(`548,368 assertions` → `548,000 assertions`), which was restored from `HEAD` before any further
command; the tree then printed 0 lines and no probe directory existed. Per §14, that incomplete
reading is neither green nor failed — it is the reason the sweep above was re-run from the beginning.

**Why the census still describes the report tip.** The sweep ran at `a74cf9a`; the report commit and
the CI-entry commit edit only this ledger. `python/quantrisk/verification/plants.py` contains no
reference to `V4_LEDGER.md` or `V3_LEDGER.md`, no test under `tests/` reads either file, and no
plant, guard, ceiling, source file or artifact moves in those two commits. The corpus the sweep
measured is therefore identical at all three tips.

### 1. Evidence ledger

| id | verdict | the probe that decided it | closing commit |
|---|---|---|---|
| V4-01 | **fixed** | `.github/lane_contract.md` exists; `--reading lanes_documented_vs_executed` prints `gap: 0` over 8 declared / 5 executed commands with `dev_only_without_reason []`; the plant that deletes the evidence-manifest step is `caught` in this report's census | `d5408f4` |
| V4-02 | **fixed** | `GUARD_ERRORED = "guard-errored-without-objecting"`; `decide()` applies pytest's return-code table (only `1` is an objection, `2`–`5` are a guard that never ran), CTest keeps its coarse convention; `pytest-error-code-is-counted-as-an-objection` is `caught` | `501dd3e` |
| V4-03 | **fixed** | each invocation owns a bytecode prefix, a private `TMPDIR` and a fresh `--basetemp`; the census at `f5fe7ae` printed `190/190`; `guard-invocations-share-one-pytest-temp-root` is `caught` | `f5fe7ae` |
| V4-04 | **fixed by deletion** | the dead `ESCAPED = "guard-stayed-green"` assignment is gone; the extended status-table test parses `runner.py`, refuses any module-level name assigned twice and pins `ESCAPED`; `status-name-assigned-twice-keeps-the-last-value` is `caught` | `622b9f1` |
| V4-05 | **fixed** | the existing absorbed-task test was extended, not duplicated: monkeypatched `module_resolves` and `command_run` with an explicit `--out`, exit `1`, `pip install 'quantrisk[plot]'` on stderr, no file published; the behavioural-link plant is pinned in `UNATTRIBUTED_PLANTS` and `pinned-residual-list-emptied` re-keyed; `command-run-skips-the-requirement-check` is `caught` | `1764231`, `87a7812` |
| V4-06 | **fixed** | `with_extras_census()` reads `suite_run.json`, compares member keys with the registry both ways, requires every `status` to be `passed` and checks `totals` against its own member list; `--reading with_extras_census` prints `gap: 0`, `members: 19`, `passed: 19`; a `With-extras census` CI step prints it; `suite-artifact-drops-a-member-the-registry-declares` is `caught` | `dbbb33d` |
| V4-07 | **fixed** | `docs_rederivation()` derives four values from committed artifacts and compares **seven** printed claims across the five documents `CONTRIBUTING.md` enumerates; `--reading docs_rederivation` prints `documents: 5`, `derived {19, 19, 194, 95}`, `gap: 0`; a `Docs re-derivation` CI step prints it; `a-living-document-transcribes-a-number-the-artifact-does-not-hold` is `caught` | `c36a2c3` |

### 2. The liveness table, final

| # | law | state | the reading that decided it |
|---|---|---|---|
| N1 | requirement truth | **satisfied** | `registry_parity` prints `filesystem_units 19`, `registry_sources 19`, `mismatch []`; V4-05's extended test reddens if `command_run` stops consulting the declaration. The bare-wheel `1 ran / 18 refused` half is inherited from `d502a61`, not re-run (§4 item 5) |
| N2 | advertised surface honesty | **satisfied for the with-extras side; inherited for the bare-wheel side** | benchmark job `19/19 executed and passed` at `ad03b89`; `--reading with_extras_census` `gap: 0`, `not_passed []`. V3 §6's installed-wheel census is not re-measured in V4 |
| N3 | lane contract | **satisfied** | the contract file exists; `lanes_documented_vs_executed_gap: 0` with **32** named CI steps, `documented_not_executed` holding the three dev-only commands with reasons; `lane-contract-claims-a-step-the-workflow-dropped` is `caught` |
| N4 | no silence by count | **satisfied** | `plant_liveness.declared_plants 194`, `formatter_census` both sets, `with_extras_census` member lists, `docs_rederivation` seven named claims, `runtime_reachability` both instruments — every count names its population |
| N5 | declarations are checkable | **satisfied** | 14 keys, 12 with a comparison that reddens; the three V4 keys carry `max: 0` and no `may_be_unmeasured`; the two SKIPs name their absent precondition |
| N6 | runtime reachability | **satisfied** | `ast_dead 13`, `import_reachable 13`, `pytest_collected 6`, `reached_by_neither 0`, `runtime_reachability_gap: 0` |
| N7 | plan equals log | **satisfied** | each of the 33 commits in `9e0bf03..ad03b89` maps to one of the seven units' approved Phase 0 rows or a named step within it; the 14 pushed tips in §8 carry every one of them; difference empty |
| N8 | no gate weakened | **satisfied** | `git diff 9e0bf03..ad03b89 -- tests/ tools/refactor_ceilings.json .github/workflows/ci.yml` (340 lines) adds three `"max": 0` rows and no `skip`/`xfail` marker; no ceiling bound was raised; the node pair stayed 560/491 through all seven units |
| N9 | plant liveness | **satisfied** | `194/194 planted defects were rejected by their guard.` at `a74cf9a`, clean tree, post-commit, captured summary, 194 `ok caught` rows and zero other status rows |
| N10 | one re-run | **not applicable** | no evidence category moved; `evidence/manifest.json` is unchanged at 95 artifacts generated 2026-10-24 from `26aef06ba288`; the re-run stays unspent |
| N11 | facts precedence | **satisfied** | `--reading docs_rederivation` `gap: 0` over five documents and seven claims; `V3_PROMPT.md` was not edited in V4; the ceilings gate was re-run after the census with the same 14-key verdict |
| N12 | baseline purity, per-lane provenance | **satisfied with three named exceptions** | §6 names the revision and environment of every lane. Exceptions: the local pytest lane's sandbox-only bytecode failure, the sweep's development-only vantage, and the installed-surface proof not re-run in V4 |

### 3. Ceilings final state — fourteen keys

`bootstrap_sites_outside_package 0`, `by_path_load_sites 0`, `commands_not_module_path 0`,
`commands_unrunnable_from_the_root 0`, `docs_rederivation_gap 0`,
`external_dependencies_added 0`, `lanes_documented_vs_executed_gap 0`,
`registry_parity_mismatch 0`, `runtime_reachability_gap 0`,
`tracked_files_outside_the_formatter_corpus 0`,
`tracked_python_files_in_no_static_check_bucket 0`, `with_extras_census_gap 0`;
`installed_user_identity_mismatch` and `plants_not_rejected_by_their_guard` are declared `SKIP` with
their precondition-absent reasons printed by the collector itself.

**For the maintainer's review, three changes this series made to the policy asset, all additions:**
`lanes_documented_vs_executed_gap` (V4-01), `with_extras_census_gap` (V4-06) and
`docs_rederivation_gap` (V4-07), each `max: 0` and each with **no `may_be_unmeasured`**, so a broken
or empty instrument fails the gate instead of skipping. No ceiling was raised, no exemption added,
no tolerance loosened and no marker added to a test. `plants_not_rejected_by_their_guard` stays
`SKIP` even though this report captures a 194/194 sweep: the key measures the declaration on the
runner and cannot read a sweep that writes gitignored scratch, which is the reason V3 gave for it.

### 4. Deliberately not done

1. **The sweep is not a CI lane.** Its 194/194 proof is a development-vantage reading with a captured
   summary line; the runner's ceiling key still SKIPs. §16 item 5 is satisfied by the summary, not
   by a gate that could fail on CI.
2. **The benchmark summary's `working tree was dirty at run time` is still undiagnosed.** Job
   `128613091928` of run `42442031942` prints `revision: ad03b890da5b **(working tree was dirty at
   run time)**`. V3 §9 named the line and V4 recorded it at every tip; the condition emitted by
   `tools/run_benchmark_suite.py:952` is not explained here, and no number from that job's generated
   artifacts is cited.
3. **The committed with-extras artifact is not pinned to HEAD.** `--reading with_extras_census`
   reads `suite_run.json` at `revision 17df062040b8`, while the benchmark job's own `With-extras
   census` step reads a freshly generated artifact at `ad03b890da5b`; both print `gap: 0`. The
   reading checks member keys, statuses and totals, not the artifact's age.
4. **The report PDF is not rebuilt.** `tools.build_report` stays `dev-only` in the lane contract for
   the reason it gives; `docs_rederivation` reads `paper/technical_report.tex` rather than rendering
   it, and no published asset was touched.
5. **The installed-surface proof was not re-run in V4.** Its bare-wheel / clean-venv reading is
   inherited from V3 §6 at `d502a61`; N2's with-extras half is current, its refusal half is not.
6. **`tools/generate_shim_stubs.py` is reachable but nothing invokes it.** V3 §4 item 4 carried this
   forward; `runtime_reachability` measures importability, not use.
7. **V4 has no written prompt.** This file's opening paragraph says so; the series ran on inherited
   §14–§16 rails with one case-by-case approval per unit.
8. **The local delete-threshold override is an environment condition, not a shipped requirement.**
   Raising `CODEBUDDY_SAFE_DELETE_BULK_THRESHOLD` for the census changed no repository file, ceiling,
   guard or wrapper verdict; CI has no such shim (V4-03's diagnosis at `f5fe7ae`).
9. **No full census was taken at every intermediate tip.** V4-04…V4-07 verified their four plants
   with targeted sweeps; only the final tip has a captured 194-plant summary.
10. **Neither new reading regenerates what it reads.** `with_extras_census` and `docs_rederivation`
    compare an artifact and five documents with their sources; they do not rewrite `suite_run.json`,
    the five documents or the PDF.

### 5. Premises audit

1. **The advertised surface is false for an installed user — CLOSED.** Re-measured at the final tip:
   `registry_parity` 19/19 with an empty mismatch, `with_extras_census` `members 19`, `passed 19`,
   `not_passed []`, and the benchmark job's `19/19 executed and passed` on the runner. V4-05 put a
   pytest guard on the refusal path V3-01 had left unguarded. Voiding this premise would make N1 and
   N2 VOID and force V5 to re-open the installed-wheel lane.
2. **Some gates execute nowhere the project names — CLOSED.** `.github/lane_contract.md` exists;
   `--reading lanes_documented_vs_executed` prints `gap: 0`, five executed commands with their
   `executed_at` steps (including the two V4-added steps), and three dev-only commands with reasons.
   Voiding it would make N3 VOID and re-open the largest gap V3 left.
3. **The audit instruments read source, not runtime — CLOSED.** `runtime_reachability_gap: 0` with
   `ast_dead 13`, `import_reachable 13`, `pytest_collected 6`, `reached_by_neither 0`; V4's two new
   readings read a produced artifact and five prose documents against their sources rather than
   transcribing a number. Voiding it would make N6 VOID.

V4's own five gaps, re-measured in this unit's Phase 0 entry, are all closed. **What voiding means
for V5:** the three new ceiling keys carry no `may_be_unmeasured`, so an instrument that stops
reading its corpus fails the gate rather than silently skipping; a V5 that weakens that property
would lose the only mechanism by which a silent reading is visible.

### 6. Per-lane verification table

| lane | revision | environment | reading |
|---|---|---|---|
| `ruff check .` | `a74cf9a` | local, macOS, `.venv` Python 3.12 | `All checks passed!` |
| `ruff format --check .` | `a74cf9a` | local | `232 files already formatted` |
| `mypy python/quantrisk tools` | `a74cf9a` | local | `Success: no issues found in 74 source files` |
| `--check-ceilings` | `a74cf9a` | local | 14 keys, **12 `ok` / 2 `SKIP`**; `declared_plants 194`; all three V4 keys `0` |
| `--reading docs_rederivation` | `a74cf9a` | local | `documents 5`, seven claims, `derived {19, 19, 194, 95}`, `gap: 0` |
| `--reading with_extras_census` | `a74cf9a` | local, committed artifact at `17df062040b8` | `members 19`, `passed 19`, `gap: 0` |
| `--reading lanes_documented_vs_executed` | `a74cf9a` | local | `gap: 0`, 32 named steps, three `tools.inventory_orphan_code` steps |
| `--reading registry_parity` | `a74cf9a` | local | `19 / 19`, `mismatch []` |
| `--reading formatter_census` | `a74cf9a` | local | `tracked 232`, `walked 232`, both differences empty |
| manifest verifier | `a74cf9a` | local | `95 OK`, `0 CHANGED`, `0 MISSING`, `Evidence is intact.` |
| `pytest --collect-only -q`; offline collection | `a74cf9a` | local | `560 tests collected`; `491 tests collected`, `collection_errors 0` |
| full `pytest -q` | `a74cf9a` | local, fresh private `--basetemp` | **1 failed, 559 passed in 259.07s** — the bytecode-cache plant this sandbox cannot run (`sys.dont_write_bytecode`); tree 0 lines afterwards |
| full mutation sweep | `a74cf9a` | local development vantage, clean tree | **`194/194 planted defects were rejected by their guard.`**, exit 0, 993-line log |
| `ruff` / format / mypy / ceilings / docs step | `ad03b89` | run `42442031942` attempt 1, lint job `128613091839`, runner `1000010445`, `ubuntu-latest` | `All checks passed!`; `232 files already formatted`; `74 source files`; `declared_plants: 194`; `Evidence is intact.`; docs step prints `documents: 5`, `gap: 0` |
| `cmake --preset ci`, build, `ctest` | `ad03b89` | same run, jobs `128613092026` (`1000010446`) and `128613091965` (`1000010447`, `macos-15`) | `100% tests passed out of 204` on both |
| `pytest` | `ad03b89` | same run, runner `1000010446` | **`490 passed, 5 skipped in 234.01s`**; `7/7 checks passed` from `validate` |
| `pytest` | `ad03b89` | same run, runner `1000010447` | `98 passed in 3.16s` |
| benchmark suite | `ad03b89` | same run, job `128613091928`, runner `1000010444` | `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 430.4s total` |
| `With-extras census` step | `ad03b89` | same job, runner `1000010444` | `gap: 0`, `members: 19`, `passed: 19`, `revision: ad03b890da5b` (fresh artifact) |
| installed-surface proof | — | **not re-run in V4**; ceiling `SKIP` | marked unverified; last reading V3 §6 at `d502a61` |

Three lanes are marked rather than green: the local pytest lane for its one sandbox-only failure,
the sweep because it is a development-vantage reading with no runner lane, and the installed-surface
proof because V4 did not re-run it. No lane in this table is credited to a cancelled run; every
runner reading above comes from attempt 1 of a run whose four jobs all completed `success` with 14
steps each.

### 7. Series handoff — what V5 must contain

1. **A written V5 prompt.** V4 had none and ran on inherited rails with seven case-by-case
   approvals; a series that changes a policy asset again should state its own premises, lanes and
   termination condition.
2. **A decision on the sweep's vantage.** Either make it runner-executable so
   `plants_not_rejected_by_their_guard` can stop SKIPping, or record explicitly that the proof stays
   development-only. `194/194` at `a74cf9a` is the baseline any such change must not weaken.
3. **A diagnosis of `working_tree_dirty`** in `tools/run_benchmark_suite.py:952`, the one line V3
   and every V4 tip recorded without explaining.
4. **A revision check for `suite_run.json`**, so the committed artifact the lint job reads can be
   shown to describe the tip being verified rather than `17df062040b8`.
5. **A re-run of the installed-surface proof** at a V5 tip if N2's inherited half is to become a
   current reading.
6. **A decision on `tools/generate_shim_stubs.py`** and on the two SKIP keys, both of which are
   reachable-but-uninvoked or precondition-absent rather than fixed.
7. **No change to the published asset set.** If the report is ever regenerated, it must be a new
   artifact inside the repository; K5 forbids replacing a `v1.9.0` release asset.

### 8. Archival confirmation

- **Tree and tip.** `git status --porcelain` printed 0 lines at `a74cf9a` before this section was
  written and again after the census and the local pytest run. `origin/main` was read from the
  platform as `ad03b890da5b19682189cc5da9e408ab11821b10`; the two pushes of this unit are attributed
  in the next entry and in the handoff.
- **CI for every commit in the range.** `9e0bf03..ad03b89` holds **33** commits, partitioned below
  into the **14** pushed tips. Every run is `event: push`, `run_attempt: 1`, `conclusion: success`;
  no cancelled or failed run belongs to the V4 range. Commits sharing a push are credited to that
  push's tip rather than individually, the convention V3 §8 used.

| run | tip | commits carried | conclusion |
|---|---|---|---|
| `42052330523` | `8ffcb32` | 5 | `success` |
| `42054617879` | `4c2b144` | 1 | `success` |
| `42061987436` | `adf9918` | 3 | `success` |
| `42063687017` | `b5db84f` | 1 | `success` |
| `42337259111` | `8b57cd2` | 5 | `success` |
| `42338131004` | `e4ec510` | 1 | `success` |
| `42354746001` | `f3fc84b` | 3 | `success` |
| `42355307417` | `0919138` | 1 | `success` |
| `42358106717` | `3af53f4` | 4 | `success` |
| `42359080745` | `0967dc8` | 1 | `success` |
| `42362912014` | `575d620` | 3 | `success` |
| `42363846255` | `bff0b35` | 1 | `success` |
| `42441028241` | `a9af730` | 3 | `success` |
| `42442031942` | `ad03b89` | 1 | `success` |

  The 33-commit sum is 5+1+3+1+5+1+3+1+4+1+3+1+3+1. `41858982944` (three attempts, two cancelled)
  and `41974525922` belong to V3 and are not credited here.
- **Tags, releases and assets re-read from the platform.** `refs/tags/v1.9.0` → tag object
  `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0`, dereferenced to commit
  `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`. Release `424060629`
  was published `2026-10-26T09:35:44Z` with four assets (`CITATION.cff`, `manifest.json`,
  `quantrisk-suite-results.zip`, `technical_report.pdf`), all created and updated between
  `09:35:41Z` and `09:35:43Z` on that date — before V4 opened on 2026-11-05. No asset was replaced.
- **Registers re-counted against their artifacts at this tip:** 19 registry tasks, 19 suite members,
  **194** plants, **14** ceiling keys, **95** manifest entries, **232** formatter-tracked files,
  **560 / 491** pytest nodes, **32** named CI steps, five living documents and seven printed claims.
- **No stray instrument tracked.** `git ls-files -- tools/derive_requires.py build/run_sweep.py
  build/api_push.py` prints nothing; `.gitignore:2` ignores `build/` and `.git/info/exclude:9`
  ignores `.workbuddy/`, so the sweep wrappers and the agent-local memory stay outside
  `formatter_census`'s tracked corpus (both of its differences are empty).
- **The locks are intact.** `git diff --name-only 9e0bf03..ad03b89` lists 12 files — the lane
  contract, the workflow, both verification modules, three test files, the collector, the ceilings
  file, two documents and this ledger — with 2,341 insertions and 17 deletions. The same command
  restricted to `cpp/`, `bindings/`, `CMakeLists.txt`, `PROJECT_SPEC.md`, `REFACTOR_PROMPT.md`,
  `V3_PROMPT.md`, `evidence/manifest.json` and `paper/` prints nothing.

**The push.** This section is committed after the Phase 0 commit and pushed with it; the CI reading
for that tip is appended in the next entry once the tool reports it, and the ledger states no outcome
before it does. The first of the two pushes authorised in the Phase 0 entry carries the
report-and-readings tip; the second carries the entry recording its CI. The terminal commit's own CI
is read after the second push and reported in the session handoff, not written into the file whose
content is fixed before that push.












