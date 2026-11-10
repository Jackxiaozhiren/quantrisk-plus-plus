# V8_LEDGER.md — cross-session state for the V8 series

Each entry records what was run, what it printed and what was decided, in that order. A number
quoted from an earlier series is named as a historical reading and re-measured before it is used as
a V8 fact. `V8_PROMPT.md` is the rail set; this file is the state.

---

### 2026-11-10, V8 Phase 0 — the closing series launched at `4f76337`

**Why this phase exists.** V7 closed with ten deliberately-not-done items in `V7_LEDGER.md` Phase 5
§4 and eight handoff items in its §6. The first of those items is the only structural one: the
census has never been captured at a literal final tip, because V6 and V7 both ran it on the
implementation tip and then shipped ledger-only commits. V7 §6 item 6 says a series that wants the
literal reading must plan a census after the terminal entry's own push on a clean tree. This is that
series.

**The recommendation this approval accepts.** V8 is a **closing-and-verification** series, not an
implementation one. It takes H1 — the final-tip census — as a process it actually executes, H2 as a
rule it can satisfy (one hard bound, reference figures reported rather than enforced), and H3–H6 as
evidence-backed retention or refusal. It adds no guard, plant, ceiling key, CI step, lane or
document count. That is deliberate: V7 already made the one substantive change its residue called
for (the pin guard), and `V5_PROMPT.md` §1 forbids manufacturing new machinery to replace gates
that are merely inconvenient. A series that invents work to look busy is the failure this rail set
exists to prevent.

**Approval, verbatim.** `授权启动 V8，按你的建议推进剩余系列` (2026-11-10). Per `V8_PROMPT.md` §6
this is the maintainer's **series-wide** approval, recorded here before any outward action. It
explicitly overrides the case-by-case rule for the V8 series and covers H1–H6, the Phase 0 entry,
the Phase 5 report, the terminal entry, the two named pushes and the final-tip census. It does
**not** authorise editing any earlier prompt or `V8_PROMPT.md`, a harness redesign that reopens §4,
a declared re-run of the evidence chain, a tag movement or release asset replacement, a new CI lane,
or a third push. The V7 series-wide approval (`授权启动 V7，按你的建议推进剩余系列`) is spent and
is not reused.

**Revision and vantage.** `HEAD` = `origin/main` = platform `main` =
`4f76337b306ae79aaaf5a07ba4ced545dacc473a`; `git status --porcelain` prints 0 lines. Vantage: the
development checkout, `.venv` Python 3.12, macOS, the same WorkBuddy interpreter shim earlier
series recorded. `.git/info/exclude` still ignores `.workbuddy/`, so agent-local memory does not
enter the formatter census. Git smart-HTTP remains blocked, so both pushes use the Git Data API
with `force: false` and per-object SHA verification.

**The three premises, re-measured at this tip.**

1. **The published chain is frozen.** `refs/tags/v1.9.0` is tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
   is `v1.9.0`, published `2026-10-26T09:35:44Z`, with `CITATION.cff` 2,978, `manifest.json`
   55,780, `quantrisk-suite-results.zip` 145,672 and `technical_report.pdf` 1,005,786 bytes, all
   created `09:35:41Z` and updated `09:35:42Z`–`09:35:43Z`. `tools.verify_evidence_manifest`
   prints `Evidence is intact.` with 95 entries and `0 on disk but not in the manifest`. Every
   field matches V7 Phase 5 §8. No regeneration occurred.
2. **The pin is a guard, not a sentence.** `--reading artifact_revision` prints
   `artifact_revision 17df062040b8`, `pinned_revision 17df062040b8`, `pin_holds true`,
   `pin_check "the committed artifact names the pinned historical revision"`, `gap 0`,
   `matches_tip false`, `object_check "the revision names a commit in this clone"`,
   `problems []`, `tip_being_verified 4f76337b306a`. The four forged cases in
   `tests/python/test_artifact_metadata.py` still hold: a real-but-different revision and a wrong
   or missing declaration each print `gap 1`; a fresh upload naming the tip prints `gap 0` with
   `pin_holds null`.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** `--check-ceilings`
   prints **15** keys, 13 `ok`, 2 `SKIP`. `plants_not_rejected_by_their_guard` prints
   `precondition absent` and its `corpus` says the collector measures only the declaration because
   the sweep's gitignored scratch never reaches the runner. `installed_user_identity_mismatch`
   prints `precondition absent` and its `corpus` says the clean-venv probe installs a second
   environment the runner cannot have. Both printed reasons still agree with their `corpus` and
   `can_fail_because` fields in `tools/refactor_ceilings.json`.

**The archive re-counted at `4f76337`.**

| quantity | command that produced the reading | value |
|---|---|---|
| registry tasks / suite members | `--reading registry_parity`; `with_extras_census` | 19 / 19; `gap 0` |
| plants | `runner --list` | **195** (last full census `195/195` at `0c239c5` — development-side vantage; the sweep has no CI lane) |
| ceiling keys | `--check-ceilings` | **15** — 13 `ok`, 2 `SKIP` |
| manifest | `tools.verify_evidence_manifest` | `Evidence is intact.` (95 entries) |
| formatter corpus | `--reading formatter_census` | **238 / 238**, both differences empty |
| pytest nodes | `--collect-only`; `measure_offline_collection` | **560**; offline **491**, `collection_errors 0` |
| named CI steps | the workflow's `- name:` lines | **34** |
| living documents / lane contract | `docs_rederivation`; `lanes_documented_vs_executed` | 5 documents, `gap 0`, `derived {95, 195, 19, 19}`; `gap 0` |
| artifact revision / runtime reachability | two readings | `gap 0`, `pin_holds true`; `reached_by_neither` empty |
| static gates | `ruff check .`; `ruff format --check .`; `mypy python/quantrisk tools` | `All checks passed!`; `238 files already formatted`; `Success: no issues found in 74 source files` |

**What this unit takes, and what it excludes.** It takes H1 (a census at the literal final tip,
after the terminal push, quoted in the session handoff), H2 (a size rule V8 can satisfy), H3 (V7's
two standing sentences recorded as historical fact, not edited), H4 (both `SKIP` keys re-read and
retained), H5 (manifest and platform assets re-read twice, nothing regenerated) and H6 (the
environmental pytest failure attributed), together with the Phase 5 report. It excludes new code,
guards, plants, ceiling keys, CI steps and lanes; it excludes editing any prompt; it excludes
regenerating `suite_run.json`, `evidence/manifest.json`, a report or a release asset; and it
excludes a third push. `V6_PROMPT.md` §4 and `V7_PROMPT.md` §4 already close the sweep and
installed-surface vantages; this unit does not reopen them.

**Deliberately not done in Phase 0.** No source file, policy asset or document was edited, no
census was run, no report section was written and no push was made. Every number above is a reading
at `4f76337`. The full census belongs to the final tip, after the terminal entry's own push, per
H1; the Phase 5 liveness table names V7's `195/195` at `0c239c5` as the inherited reading and says
so rather than claiming a V8 verdict before it exists.

**The two pushes.** The first carries this Phase 0 commit and the Phase 5 report; the second carries
the terminal entry only. No third is implied. Each push's CI is read from the API after the tool
reports it; the first tip's run is attributed in the terminal entry and the second tip's run in the
session handoff. The final-tip census runs after the second push, on a clean tree, and is quoted in
the session handoff with its revision.

---
