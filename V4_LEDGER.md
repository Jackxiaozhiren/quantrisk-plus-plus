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
