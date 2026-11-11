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

### 2026-11-11, V9 Phase 5 — the report, the liveness table and the archival confirmation

**How this was assembled.** From the two entries above plus fresh readings at
`df3f9affa6b0c248687219b427649767fe4e6db0` on a clean tree. The implementation commit is `df3f9af`;
the series adds exactly two tracked paths, `V9_PROMPT.md` and this ledger, so no source, policy
asset, test, workflow, manifest entry or artifact can move. The one count that moves is the
formatter corpus, 240 → **242**, because both added paths are Markdown; both differences are still
empty.

#### 1. Evidence ledger

| id | verdict | probe | closing commit |
|---|---|---|---|
| D1 | **fixed** | a machine-readable attestation of V8's literal-final-tip census, read by one named command that checks the revision against git's objects and ancestry and the count against `runner --list`; five runs at `df3f9af` — the genuine block passes, four forged inputs are refused | `df3f9af` |

**The probe in detail.** `git cat-file -e 5ec3fab^{commit}` and
`git merge-base --is-ancestor 5ec3fab HEAD` both exit 0, so the named revision is a real commit and
a strict ancestor rather than a self-reference. The genuine run prints
`PASS: 5ec3fabe4fa8 is a strict ancestor of df3f9affa6b0; 195/195 ok caught, 0 other verdict rows` — development-side vantage; the sweep has no CI lane. The four forged inputs are refused with
distinct reasons: a revision that is not an object, a real commit that is not an ancestor, the
containing commit itself, and a declared count of 194 against the runner's 195. The reading was
re-run after the implementation commit — the self-reference case rebuilt against the new `HEAD` —
so the proof is a post-commit reading, not a recalled one. A targeted sweep at this tip re-runs the
prose plant that guards the printed claim: `1/1 planted defects were rejected by their guard.`

#### 2. Liveness table, re-evaluated at `df3f9af`

| # | law | verdict | the reading that decided it |
|---|---|---|---|
| N1 | requirement truth | **ACTIVE** | `registry_parity`: `filesystem_units 19`, `registry_sources 19`, `mismatch []` |
| N2 | advertised surface honesty | **ACTIVE, inherited** | `with_extras_census gap 0`, `members 19`, `passed 19`; the V5 F5 clean-venv wheel proof stays development-only and is not promoted |
| N3 | lane contract | **ACTIVE** | `lanes_documented_vs_executed gap 0`; **34** named CI steps, unchanged by a series that adds no step |
| N4 | no silence by count | **ACTIVE** | `with_extras_census gap 0`; `docs_rederivation gap 0`, 5 documents, `derived {95, 195, 19, 19}`, no mismatches |
| N5 | declarations are checkable | **ACTIVE** | 15 keys, 13 `ok`, 2 `SKIP`, 0 `FAIL`; `pinned_revision` compared in both directions, `pin_holds true` |
| N6 | runtime reachability | **ACTIVE** | `runtime_reachability` prints `reached_by_neither []` |
| N7 | one finding, one commit | **ACTIVE** | Phase 0, `df3f9af`, this report and the terminal entry map to D1 alone; no commit spans two findings and V9 has no D2 |
| N8 | no gate weakened | **ACTIVE** | the diff over `5ec3fab..df3f9af` is two `.md` files: no `skip`/`xfail`, no tolerance, no test deleted, no `max` raised, no `may_be_unmeasured` added |
| N9 | plant liveness | **ACTIVE, inherited plus one re-run** | V8's census `195/195` at `5ec3fab` (development-side vantage; the sweep has no CI lane) plus a targeted re-run at `df3f9af` of the prose plant, `1/1 caught`; V9 moves no plant, guard or target file |
| N10 | one re-run | **ACTIVE, not triggered** | nothing regenerated: `suite_run.json` still names `17df062040b8`, the manifest still holds 95 intact entries |
| N11 | facts precedence | **ACTIVE** | `docs_rederivation gap 0` across 5 documents; every census verdict printed in this ledger carries its vantage on the same line |
| N12 | baseline purity and per-lane provenance | **ACTIVE** | §7 names a revision and an environment for every lane; the baseline `5ec3fab` has its own CI run `42815355663` (`completed / success`, attempt 1) |

#### 3. The ceilings file's final state

`tools/refactor_ceilings.json` carries **15** keys, untouched by V9: thirteen `ok` at `0`, two
`SKIP` with `may_be_unmeasured: true` — `plants_not_rejected_by_their_guard` and
`installed_user_identity_mismatch`.

**Review notes.** V9 adds no key, no `max` change, no exemption and no `may_be_unmeasured`. The
`pinned_revision` declaration V7 added is read unchanged and still prints `pin_holds true`. The
attestation is a ledger row, not a policy asset, and deliberately has no ceiling key of its own:
adding a sixteenth key to record "the attestation was checked" would be the declaration-counting
failure `V5_PROMPT.md` §1 names, and the reading already reddens on its own.

#### 4. The deliberately-not-done list

1. **A — `V7_PROMPT.md` §8 is not repaired.** Its 88-line soft cap and its "growth only in §5 and
   §3" sentence are historical fact; V7 §6 requires its own verbatim approval to edit, and V8 §4
   item 2 records the same refusal. Rewriting it would erase the partial finding rather than fix it.
2. **B — the sweep vantage is not reopened.** `V6_PROMPT.md` §4 made the development-only decision
   permanent; reopening needs a harness redesign that adds a CI lane and puts a ~38-minute census on
   a runner. V9 Phase 0 excluded it and §4 keeps it closed.
3. **C — the evidence chain is not re-run.** A declarative re-run would move the 95-entry manifest
   and the release asset set, and `quantrisk-suite-results.zip` cannot be replaced under K5. The
   repository would end less consistent than it started.
4. **No census at V9's own tip.** §0's termination condition: D1 fixes an existing reading, and a
   fresh census would reproduce the deferral V8 handed on while making the attestation stale on
   arrival. Any future claim about V9's tip must say no census was captured there.
5. **The attestation is not a gate.** No CI lane executes the verification reading; it is a
   development-side check, which §4 requires and which the reading itself states.
6. **The 998-line log is not in the repository.** §2.6's evidence limit: the attestation fixes the
   reading — revision, command, exit code, line count, verdict distribution, summary line, tree
   state, vantage — not the log, and does not claim the numbers are re-runnable from a tracked
   artifact.
7. **`V8_LEDGER.md` is not edited.** Its `deferred` row stays as printed; D1 is a new row about a
   past revision, not a correction of V8's report.
8. **No new plant, guard, ceiling key, CI step, lane, living document or artifact.** The formatter
   corpus moved 240 → 242 only because two Markdown files were added; both differences are empty.
9. **No tag movement, no release asset replacement, no V9 release.** The published chain is a
   premise, and the check is that it did not move.
10. **The one local pytest failure was not silenced.** `1 failed, 559 passed in 166.24s` at
    `df3f9af` is the sandbox bytecode-cache plant; no marker, tolerance or deletion was added, and
    CI's `490 passed, 5 skipped` is read instead.
11. **The report PDF was not rebuilt.** `tools.build_report` stays dev-only; no number the paper
    cites has moved.
12. **`V9_PROMPT.md` exceeds the 107-prose reference figure.** It measures **164 total / 112
    prose**, five above V8's figure; §8 says that is reported, not failed, and the 431-line hard
    bound holds.

#### 5. Premises audit

1. **The published chain is frozen.** *Final reading:* tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
   (`v1.9.0`) published `2026-10-26T09:35:44Z`, four assets sized 2,978 / 55,780 / 145,672 /
   1,005,786 bytes, created `2026-10-26T09:35:41Z`, updated `09:35:42Z`–`09:35:43Z`; manifest 95
   entries, `Evidence is intact.`. **Closed**; every field matches Phase 0's row and no asset was
   replaced. Voiding it would mean the published chain moved, which no V9 commit can cause.
2. **The pin is a guard, not a sentence.** *Final reading:* `artifact_revision 17df062040b8`,
   `pinned_revision 17df062040b8`, `pin_holds true`, `gap 0`, `matches_tip false`, `object_check
   "the revision names a commit in this clone"`, `problems []`. **Closed**; V9 touched no guard, and
   V7's four forged cases remain in the F4 test. Voiding it would mean an artifact could name any
   well-formed revision, and D1's own reading would lose its model.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** *Final reading:* 15
   keys, 13 `ok`, 2 `SKIP`; both print `precondition absent` and their `corpus` still describes the
   missing runner precondition. **Closed**; the residue is that both verdicts remain
   development-only, which §4 keeps rather than hides.

#### 6. Series handoff — what a V10 must contain

Derived from this run's evidence, not from the prompt's prose:

1. **D1's reading is checkable but not gated.** No CI lane runs it. Promoting it needs a new scope
   unit that says so in Phase 0; a V10 that assumes it is already enforced has read neither this
   ledger nor §4.
2. **The evidence limit travels with the attestation.** The log is not tracked, so the numbers are
   not re-runnable from a tracked artifact. A future series that wants re-runnability must plan a
   tracked log and its evidence budget explicitly.
3. **No census was captured at V9's own tip.** That was deliberate (§0). Any future claim about
   `5ec3fab`'s successors must say that V9 captured no census there.
4. **The attestation is a row about a past revision.** Do not "refresh" it to a newer tip; a new
   reading needs a new attestation written by a series that starts above the tip it names.
5. **The sweep, installed-surface and `SKIP` vantages stay closed and development-only** under
   `V6_PROMPT.md` §4, `V7_PROMPT.md` §4 and `V8_PROMPT.md` §4. Reopening any of them needs a
   harness redesign named in Phase 0.
6. **107 is a reference figure, not a gate.** V9 measures 164 / 112; the only hard bound is 431.
7. **There is no remaining code-level residue from V3–V9.** The pin, the readings, the ceilings,
   the lanes and the census reading are each either guarded, gated or named with an evidence limit.
   A V10 must justify its scope against `V5_PROMPT.md` §1 rather than invent machinery to look busy.

#### 7. Per-lane verification table

| lane | revision | environment | vantage | verdict |
|---|---|---|---|---|
| `ruff check .` | `df3f9af` | macOS, `.venv` Python 3.12, development checkout | development | `All checks passed!` |
| `ruff format --check .` | `df3f9af` | same | development + CI lint | `242 files already formatted` |
| `mypy python/quantrisk tools` | `df3f9af` | same | development | `Success: no issues found in 74 source files` |
| `pytest -q` (full) | `df3f9af` | same, private `--basetemp=/tmp/qr-v9-post` | development | **not green**: `1 failed, 559 passed in 166.24s` — the sandbox bytecode-cache plant, named not silenced |
| `pytest --collect-only` / `measure_offline_collection` | `df3f9af` | same | development | 560 collected / 491 offline, `collection_errors 0` |
| `--check-ceilings` | `df3f9af` | same | development + CI lint | 15 keys, 13 `ok`, 2 `SKIP`, 0 `FAIL` |
| `--reading docs_rederivation` | `df3f9af` | same | development + CI lint | `gap 0`, 5 documents, `derived {95, 195, 19, 19}` |
| `--reading lanes_documented_vs_executed` | `df3f9af` | same | development + CI lint | `gap 0` |
| `--reading with_extras_census` | `df3f9af` | same | development + CI lint + benchmark-job fresh artifact | `gap 0`, 19/19 |
| `--reading artifact_revision` | `df3f9af` | same | development (deep clone) + lint (shallow clone) + benchmark (fresh artifact) | `gap 0`, `pin_holds true`, `matches_tip false` on the committed vantage |
| `--reading formatter_census` / `registry_parity` / `runtime_reachability` | `df3f9af` | same | development + CI lint | 242/242 (both differences empty), 19/19, `reached_by_neither []` |
| `tools.verify_evidence_manifest` | `df3f9af` | same | development + CI lint | `Evidence is intact.` (95 entries) |
| D1 verification reading, five inputs | `df3f9af` | same, scratch under `/tmp` | **development-only, labelled** | 1 `PASS`, 4 `REFUSED`, as §1 records |
| targeted sweep, prose plant | `df3f9af` | same, bulk-delete threshold raised locally | **development-only, labelled** | `1/1 planted defects were rejected by their guard.` |
| mutation sweep, full census | inherited only | same | **development-only, labelled** | `195/195` at `5ec3fab` (development-side vantage; the sweep has no CI lane); **not re-run by V9**, by design |
| `tools.verify_installed_surface` | `3c6092f` | `/tmp/qr-v5-venv`, wheel from that tree, neutral cwd | **development-only, labelled** | identity, 19 tasks, 7 validations, one study, one refusal, 0 residue |
| CI four jobs | `5ec3fab` (run `42815355663`) | `ubuntu-latest` `1000010767`/`1000010768`/`1000010769`, `macos-15` `1000010770` | runner | `completed / success`, attempt 1, 15 / 14 / 15 / 14 steps; re-read from the API for this report |
| CI four jobs | report tip (first V9 push) | runners named in the terminal entry | runner | **not yet read**; no outcome is written for a push that has not happened |
| CI four jobs | terminal tip (second V9 push) | runners named in the session handoff | runner | **not yet read** |

No lane is marked green on a mixed vantage. The census row is inherited and labelled, not claimed
as V9's own. The local failure is named as a failure with its cause and environment.

#### 8. Archival confirmation

- **Tree and tip.** `git status --porcelain` prints 0 lines; `HEAD` is
  `df3f9affa6b0c248687219b427649767fe4e6db0` before this report's commit, with `origin/main` at
  `5ec3fab`. Phase 0, the implementation and this report ship in the first V9 push; the terminal
  entry follows in the second, and the session handoff records the final tip.
- **Every V9 commit an ancestor of the remote.** `b77ca05` (Phase 0) and `df3f9af` (implementation)
  are local ancestors of the terminal commit; this report and the terminal entry follow them. Each
  object SHA is checked against the local object before the ref moves, and the platform `/compare`
  reading for the pushed range is taken after each push.
- **CI for every commit.** The baseline `5ec3fab` has its own run `42815355663`
  (`completed / success`, `run_attempt 1`, created `2026-11-10T12:23:35Z`, updated `12:30:33Z`,
  four jobs 15 / 14 / 15 / 14, runners `1000010767`–`1000010770`). The two V9 push tips are
  attributed after the API reports them; no run is named green before it is read.
- **Registers and documents re-counted.** `registry_parity` 19/19, `with_extras_census` 19/19 /
  `gap 0`; plants 195; ceiling keys 15; manifest 95 intact; `docs_rederivation` 5 documents /
  `gap 0`; formatter 242/242 with both differences empty; nodes 560 / 491 offline; CI steps 34;
  six prompts and seven ledgers for V3–V9, all present; `artifact_revision gap 0` with
  `pin_holds true`, `lanes_documented_vs_executed gap 0`, `runtime_reachability
  reached_by_neither []`.
- **Tags, releases and assets re-read from the platform.** Tag object
  `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
  `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
  (`v1.9.0`) published `2026-10-26T09:35:44Z` with the same four assets and byte sizes as Phase 0.
  No asset was replaced and no tag moved.
- **No stray instrument tracked or left on disk.** `git ls-files -- tools/derive_requires.py
  build/run_sweep.py build/api_push.py` prints nothing; `git check-ignore` confirms
  `build/api_push.py`, `build/run_sweep.py` and `.workbuddy/` are ignored; no `_mutation_probe`
  directory exists; the forged attestations and the extracted reading live under `/tmp` and are
  removed after the session.

#### 9. What V9 changed, and what it did not

It added `V9_PROMPT.md` and `V9_LEDGER.md`, and nothing else. `git diff --name-only 5ec3fab..HEAD`
prints exactly those two paths. It changed no source file, guard, plant, ceiling key, CI step,
lane, manifest entry, committed suite artifact, document count or release asset, and it did not
touch `cpp/`, `bindings/`, `CMakeLists.txt`, `PROJECT_SPEC.md`, `REFACTOR_PROMPT.md`,
`V3_PROMPT.md`, `V5_PROMPT.md`, `V6_PROMPT.md`, `V7_PROMPT.md`, `V8_PROMPT.md`,
`V8_LEDGER.md`, `evidence/manifest.json` or `paper/`. The only measurement that moved is the
formatter corpus, 240 → 242, because the two added paths are Markdown.

**The first push.** This report, the Phase 0 commit and the implementation commit are pushed
together in the first of the two pushes authorised in the V9 Phase 0 entry. Its CI is read once the
tool reports it and recorded in the terminal entry; no outcome is stated here for a push that has
not happened.

---

### 2026-11-11, V9 terminal entry — the first push is green, and the series closes

**The first push.** `9716cf041abbdd638b9475576781e0136a5b9e8d`, a non-forced fast-forward from
`5ec3fab`: the tool printed `ref moved to 9716cf041abbdd638b9475576781e0136a5b9e8d (non-forced
fast-forward)` after checking each object, and the platform then printed `main` = `9716cf0` with
`/compare` `status ahead`, `ahead_by 3`, `behind_by 0` and the three commits `b77ca05`, `df3f9af`,
`9716cf0`.

**Its CI, read from the API after the tool reported it.** Run `43033065357`,
`completed / success`, `run_attempt 1`, `head_sha 9716cf041abbdd638b9475576781e0136a5b9e8d`,
created `2026-11-11T13:52:20Z`, updated `14:01:16Z`. No cancelled job, no zero-step job and no
failed step.

| job | job id | runner | environment | steps |
|---|---|---|---|---|
| Benchmark suite against live oracles | `130564783009` | `1000010906` | ubuntu-latest | 15 |
| Format and static checks | `130564783397` | `1000010907` | ubuntu-latest | 15 |
| macOS native C++ and Python parity | `130564783439` | `1000010910` | macos-15 | 14 |
| Configure, build, C++ tests, Python tests | `130564783488` | `1000010909` | ubuntu-latest | 14 |

**What the log printed.** `242 files already formatted`; `declared_plants 195`; `Evidence is
intact.`; `artifact_revision_gap: 0 against a ceiling of 0 due V5-02 / V7-01` beside
`docs_rederivation_gap: 0`, `lanes_documented_vs_executed_gap: 0` and `with_extras_census_gap: 0`;
the committed artifact's vantage prints `matches_tip false`, `pin_holds true`,
`pin_check "the committed artifact names the pinned historical revision"`, while the benchmark's
fresh upload prints `matches_tip true`, `pin_holds null`, `pin_check "not applicable: the fresh
artifact names the tip of the run that wrote it"`; `490 passed, 5 skipped in 176.29s (0:02:56)`;
`7/7 checks passed`; `100% tests passed out of 204`; `98 passed in 3.28s`; and
`suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 327.0s total`.

**Which commit this run covers.** The implementation commit `df3f9af` has no run of its own: it
first reached the remote inside this push. The run headed at `9716cf0` therefore covers all three
commits — Phase 0, the implementation and this report — and the terminal entry records it as the
implementation tip's CI rather than claiming a separate run that does not exist.

**What the terminal entry records.** D1 is fixed and its reading was re-verified after the report
commit (`PASS: 5ec3fabe4fa8 is a strict ancestor of 9716cf041abb; 195/195 ok caught, 0 other verdict rows` — development-side vantage; the sweep has no CI lane). The series closes when this
entry is pushed and its own run is attributed in the session handoff. No new finding is raised
here, and none is left unnamed.

**The second push.** This entry alone. No third is implied.

---
