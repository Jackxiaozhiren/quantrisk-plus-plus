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

**The push, and how its CI reading is recorded.** This entry is committed after the implementation commit and
pushed with it. The CI reading for the pushed tip is appended in the next entry once `gh` reports it; the
ledger never states an outcome before the tool does.
