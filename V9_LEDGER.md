# V9_LEDGER.md — cross-session state for the V9 series

Each entry records what was run, what it printed and what was decided, in that order. A number
quoted from an earlier series is named as a historical reading and re-measured before it is used as
a V9 fact. `V9_PROMPT.md` is the rail set; this file is the state.

---

### 2026-11-11, V9 Phase 0 — the single unit that freezes V8's final-tip census

**Why this phase exists.** `V8_LEDGER.md` Phase 5 §7 prints `deferred` on the full-census row, and
its §6 item 1 says the census reading at the literal final tip `5ec3fab` (development-side
vantage; the sweep has no CI lane) is a session reading:
it lives in the handoff and in agent-local memory, not in the repository. V8 could not fix that in
its own file, because a tracked file cannot name the SHA of the commit that contains it without
moving the tip it measures. V9 starts above `5ec3fab`; for V9 that revision is an ancestor, so the
self-reference disappears. That is the entire mechanism, and it is why this unit needs no new
guard, plant, ceiling key, CI step or lane.

**Approval, verbatim.** `启动 V9，只做 D 项` (2026-11-11). This is a **single-unit** approval,
recorded here before any outward action. It covers D1, this Phase 0 entry, the attestation, the
Phase 5 report, the terminal entry, the two named pushes and their CI attribution. The earlier
`全部授权批准，我都听你的，请按照你的思路建议进行` (2026-11-11) was a delegation of judgement, not
a scope-bearing authorisation; acting on it in the preceding turn produced no commit. The V8
series-wide approval is spent and is not reused.

**Not authorised:** items A (repairing `V7_PROMPT.md` §8), B (reopening the sweep vantage) and C
(a declarative re-run of the evidence chain); editing any earlier prompt or ledger; a harness
redesign; a tag movement or release asset replacement; a new census at V9's own tip; a new CI lane,
plant, guard, ceiling key or living document; and a third push.

**Revision and vantage.** `HEAD` = `origin/main` = platform `main` =
`5ec3fabe4fa8c83584a50b3ab66b357ae13094e9`; `git status --porcelain` prints 0 lines. Vantage: the
development checkout, `.venv` Python 3.12, macOS, the same WorkBuddy interpreter shim earlier
series recorded. `.git/info/exclude` still ignores `.workbuddy/`, so agent-local memory does not
enter the formatter census. `git cat-file -e 5ec3fab^{commit}` and
`git merge-base --is-ancestor 5ec3fab HEAD` both exit 0 at this tip. Git smart-HTTP remains
blocked, so both pushes use the Git Data API with `force: false` and per-object SHA verification.

**The three premises, re-measured at this tip.**

1. **The published chain is frozen.** `refs/tags/v1.9.0` is tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`, and that commit is
   an ancestor of `HEAD`. Release `424060629` is `v1.9.0`, published `2026-10-26T09:35:44Z`, with
   `CITATION.cff` 2,978, `manifest.json` 55,780, `quantrisk-suite-results.zip` 145,672 and
   `technical_report.pdf` 1,005,786 bytes, all created `09:35:41Z` and updated
   `09:35:42Z`–`09:35:43Z`. `tools.verify_evidence_manifest` prints `Evidence is intact.` with 95
   entries and `0 on disk but not in the manifest`. No regeneration occurred.
2. **The pin is a guard, not a sentence.** `--reading artifact_revision` prints
   `artifact_revision 17df062040b8`, `pinned_revision 17df062040b8`, `pin_holds true`, `gap 0`,
   `matches_tip false`, `object_check "the revision names a commit in this clone"`. V9 does not
   weaken it; the V7 forged cases are not re-run here because no code moves.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** `--check-ceilings`
   prints **15** keys, 13 `ok`, 2 `SKIP`. `plants_not_rejected_by_their_guard` prints
   `precondition absent` and its `corpus` says the collector measures only the declaration because
   the sweep's gitignored scratch never reaches the runner. `installed_user_identity_mismatch`
   prints `precondition absent` and its `corpus` says the clean-venv probe installs a second
   environment the runner cannot have. Both reasons still agree with their `corpus` and
   `can_fail_because` fields. V9 does not give either a runner-side verdict.

**The archive re-counted at `5ec3fab`.**

| quantity | command that produced the reading | value |
|---|---|---|
| registry tasks / suite members | `--reading registry_parity`; `with_extras_census` | 19 / 19, `mismatch []`; `gap 0`, 19 / 19 |
| plants | `runner --list` | **195** (V8's last full census `195/195` at `5ec3fab` — development-side vantage; the sweep has no CI lane) |
| ceiling keys | `--check-ceilings` | **15** — 13 `ok`, 2 `SKIP`, 0 `FAIL` |
| manifest | `tools.verify_evidence_manifest` | `Evidence is intact.` (95 entries) |
| formatter corpus | `--reading formatter_census` | **240 / 240**, both differences empty |
| pytest nodes | `--collect-only`; `measure_offline_collection` | **560**; offline **491**, `collection_errors 0` |
| named CI steps | the workflow's `- name:` lines | **34** |
| living documents / lane contract | `docs_rederivation`; `lanes_documented_vs_executed` | 5 documents, `gap 0`, `derived {95, 195, 19, 19}`; `gap 0` |
| artifact revision / runtime reachability | two readings | `gap 0`, `pin_holds true`, `matches_tip false`; `reached_by_neither []` |
| static gates | `ruff check .`; `ruff format --check .`; `mypy python/quantrisk tools` | `All checks passed!`; `240 files already formatted`; `Success: no issues found in 74 source files` |
| residual markers | `grep -rnE '\b(TODO|FIXME|XXX|HACK)\b'` over `python/ tools/ tests/ cpp/ bindings/` | **0** |
| latest three CI runs | platform API | `42815355663`, `42813273094`, `42808340869` — all `completed / success` |

**What this unit takes, and what it excludes.** It takes one finding, D1: a named, machine-readable
attestation of V8's literal-final-tip census, with its revision, vantage and evidence limit, and a
verification reading that reddens a forged revision and a forged count. The verification reading
uses only git's own object/ancestry queries and the existing `runner --list`; it is recorded in
this ledger as a command and its output, and it is not a new guard, plant, ceiling key, CI step or
lane. V9 excludes a new census at its own tip: D1 fixes an existing reading, and re-running the
sweep at V9's tip would create another session-only reading and hand the same deferral to a V10.
V9 excludes changing any source, policy asset, living document, artifact, tag or release asset,
and excludes editing `V8_LEDGER.md`, whose `deferred` row is a historical reading.

**Deliberately not done in Phase 0.** No source file, policy asset or document was edited, no
census was run, no attestation was written, no report section was written and no push was made.
Every number above is a reading at `5ec3fab`. The attestation and its forged proofs belong to the
implementation commit; no verdict is claimed before the tool prints it.

**The two pushes.** The first carries Phase 0, the implementation and the Phase 5 report; the
second carries the terminal entry only. No third is implied. Each push's CI is read from the API
after the tool reports it; the first tip's run is attributed in the terminal entry and the second
tip's run in the session handoff.

---

### 2026-11-11, V9 implementation — the attestation and its verification reading

**What D1 adds.** A machine-readable attestation carrying V8's census reading at the literal final
tip, and one named verification reading that can redden it. Both live in this ledger; neither is a
new tracked file, guard, plant, ceiling key, CI step, lane, living document or policy asset. The
mechanism is the absence of self-reference: `5ec3fab` is an ancestor here, so a V9 file can name it
and git can verify the claim. `V8_LEDGER.md` is not edited; its `deferred` row stays as printed.

This is the answer to `V5_PROMPT.md` §1's "every change must leave the repository more checkable
than it found it, with a named reading that can redden it" without manufacturing the machinery
`V8_LEDGER.md` §6 item 8 warns against. The reading uses only git's object and ancestry queries and
the existing `runner --list`; it is recorded here as a command and its output. Before this commit
the census was a session-only sentence that nothing in the repository could check. After it, the
revision is a verifiable object, the count is checked against the harness, and four forged inputs
are refused. The reading is development-side, with the same vantage as the census itself: it is not
a CI gate and does not claim to make the sweep reproducible on a runner.

**The attestation.** The markers delimit exactly one JSON block; the reading below parses it.

<!-- V9_ATTESTATION_BEGIN -->
```json
{
  "schema": "quantrisk.final_tip_census_attestation/v1",
  "subject": "V8 full plant census at its literal final tip",
  "revision": "5ec3fabe4fa8c83584a50b3ab66b357ae13094e9",
  "revision_role": "strict ancestor of the commit that carries this attestation, not a self-reference",
  "command": "CODEBUDDY_SAFE_DELETE_BULK_THRESHOLD=100000 QR_DIAG_FULL=1 uv run --frozen python build/run_sweep.py --all --verbose",
  "exit_code": 0,
  "log_lines": 998,
  "declared_plants": 195,
  "verdict_rows": {"ok_caught": 195, "other": 0},
  "summary": "195/195 planted defects were rejected by their guard.", "vantage": "development-side vantage; the sweep has no CI lane",
  "tree_dirty_paths_after": 0,
  "captured": "2026-11-10, after V8's second push, on the clean tree at the terminal commit",
  "evidence_limit": "The 998-line log was session-local scratch under /tmp and is no longer on disk. This attestation fixes the reading, not the log; the numbers are not re-runnable from a tracked artifact.",
  "inherited_from": "V8_LEDGER.md Phase 5 section 7 mutation-sweep row (printed as deferred) and the V8 session handoff"
}
```
<!-- V9_ATTESTATION_END -->

**The verification reading.** Run in the repository root; an optional argument names a forged
attestation file, so the same function decides the genuine block and each forged input.

```bash
uv run --frozen python - "${1:-}" <<'PY'
import json, re, subprocess, sys
from pathlib import Path

BLOCK = re.search(
    r"<!-- V9_ATTESTATION_BEGIN -->\s*```json\s*(.*?)\s*```\s*<!-- V9_ATTESTATION_END -->",
    Path("V9_LEDGER.md").read_text(), re.S,
)
if not BLOCK:
    sys.exit("REFUSED: exactly one attestation block is required, none found")
a = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 and sys.argv[1] else json.loads(BLOCK.group(1))

def refuse(why):
    sys.exit(f"REFUSED: {why}")

rev = a["revision"]
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
if a["schema"] != "quantrisk.final_tip_census_attestation/v1":
    refuse("wrong schema")
if not re.fullmatch(r"[0-9a-f]{40}", rev):
    refuse("the revision is not a 40-hex object name")
if subprocess.run(["git", "cat-file", "-e", rev + "^{commit}"], capture_output=True).returncode:
    refuse("the named revision is not a commit object in this repository")
if rev == head:
    refuse("the attestation names the commit that contains it (self-reference)")
if subprocess.run(["git", "merge-base", "--is-ancestor", rev, "HEAD"], capture_output=True).returncode:
    refuse("the named revision is not an ancestor of HEAD")
n = len(subprocess.run(
    [sys.executable, "-m", "quantrisk.verification.runner", "--list"],
    capture_output=True, text=True, check=True,
).stdout.splitlines())
rows = a["verdict_rows"]
if rows["ok_caught"] != n or rows["other"] != 0 or a["declared_plants"] != n:
    refuse(f"the attestation's counts disagree with runner --list ({n})")
if a["exit_code"] != 0 or a["tree_dirty_paths_after"] != 0 or a["log_lines"] != 998:
    refuse("the exit code, tree state or log length disagrees")
if "development-side vantage" not in a["vantage"] or "no CI lane" not in a["vantage"]:
    refuse("the vantage is not named")
if "no longer on disk" not in a["evidence_limit"]:
    refuse("the evidence limit is not named")
m = re.fullmatch(r"(\d+)/(\d+) planted defects were rejected by their guard\.", a["summary"])
if not m or m.group(1) != m.group(2) or int(m.group(1)) != n:
    refuse("the summary line is not the verbatim verdict for the declared count")
print(f"PASS: {rev[:12]} is a strict ancestor of {head[:12]}; {n}/{n} ok caught, 0 other verdict rows")
PY
```

**What the reading printed.** The bash block above was extracted from this ledger into
`/tmp/v9_verify_reading.sh` and executed unchanged, so the recorded command is the command that
ran. Five runs: the genuine block and four forged inputs. The forged JSON files are session-local
scratch under `/tmp`, are not tracked, and are removed in the archival confirmation.

| input | invocation | output | exit |
|---|---|---|---|
| genuine block | `bash /tmp/v9_verify_reading.sh` | `PASS: 5ec3fabe4fa8 is a strict ancestor of b77ca0522079; 195/195 ok caught, 0 other verdict rows` — development-side vantage; the sweep has no CI lane | 0 |
| forged revision, not an object | `bash /tmp/v9_verify_reading.sh /tmp/v9_forge_object.json` with `"revision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"` | `REFUSED: the named revision is not a commit object in this repository` | 1 |
| forged revision, object but not ancestor | `bash /tmp/v9_verify_reading.sh /tmp/v9_forge_ancestor.json` with `"revision": "337790c12da086c7bf664f3d3f7da028d3bb157d"` | `REFUSED: the named revision is not an ancestor of HEAD` | 1 |
| forged self-reference | `bash /tmp/v9_verify_reading.sh /tmp/v9_forge_self.json` with `"revision": "b77ca0522079df838d09622210578153f87a33af"` (the then-`HEAD`) | `REFUSED: the attestation names the commit that contains it (self-reference)` | 1 |
| forged count | `bash /tmp/v9_verify_reading.sh /tmp/v9_forge_count.json` with `"ok_caught": 194` | `REFUSED: the attestation's counts disagree with runner --list (195)` | 1 |

The third forged case is the mechanism itself: naming the containing commit is refused, which is
why V8 could not write this attestation and why V9, one commit later, can. The `PASS` line names the
`HEAD` at the time of the run, not the final V9 tip; the reading re-derives ancestry from whatever
`HEAD` the repository has, so it still passes after the report and terminal commits.

**What was decided.** D1 is fixed: the census reading now has a named repository home with a
revision git can verify, a vantage, an evidence limit and a two-direction forged proof. V9 does not
claim the census ran at its own tip, does not make it a gate, and does not re-run it. No source,
policy asset, test, workflow, manifest, artifact, tag or release asset was edited in this commit;
the only changed tracked path is this ledger.

---
