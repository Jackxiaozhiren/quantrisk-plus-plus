# V10_LEDGER.md — cross-session state for the V10 series

Each entry records what was run, what it printed and what was decided, in that order. A number
quoted from an earlier series is named as a historical reading and re-measured before it is used as
a V10 fact. `V10_PROMPT.md` is the rail set; this file is the state.

---

### 2026-11-12, V10 Phase 0 — the single unit that repairs `V7_PROMPT.md` §8

**Why this phase exists.** `V9_LEDGER.md` Phase 5 §4 item 1 names A as deliberately not done: V7's
§8 sets a soft cap at V6's 88 prose lines, an escape clause, and a growth clause ("only in §5 and
§3") that the file it governs does not meet. `V7_LEDGER.md` records H6 as **PARTIAL** for exactly
that reason, and V8 §4 item 2 and V9 §1 refused the repair because `V7_PROMPT.md` §6 makes editing
that file its own scope unit needing its own verbatim approval. The maintainer has now given that
approval, so the rule can be repaired without rewriting the finding.

**Approval, verbatim.** `启动 V10，只做 A 项` (2026-11-12). This is a **single-unit** approval,
recorded here before any outward action. It covers A1, this Phase 0 entry, the implementation, the
Phase 5 report, the terminal entry, the two named pushes and their CI attribution. The V9 approval
(`启动 V9，只做 D 项`) is spent and is not reused.

**Not authorised:** items B (reopening the sweep vantage) and C (a declarative re-run of the evidence
chain); editing `V7_PROMPT.md` outside §8; editing any other prompt or ledger; a harness redesign; a
new census; a tag movement or release asset replacement; a new CI lane, plant, guard or ceiling key;
and a third push.

**Revision and vantage.** `HEAD` = `origin/main` = platform `main` =
`ca94a2c153d677e1d6b2f174e105c73efc4d57b2` (before this entry's commit); `git status --porcelain`
prints 0 lines. Vantage: the development checkout, `.venv` Python 3.12, macOS, the same WorkBuddy
interpreter shim earlier series recorded. `.git/info/exclude` still ignores `.workbuddy/`, so
agent-local memory does not enter the formatter census. Git smart-HTTP remains blocked, so both
pushes use the Git Data API with `force: false` and per-object SHA verification.

**The three premises, re-measured at this tip.**

1. **The published chain is frozen.** `refs/tags/v1.9.0` is tag object
   `d9deb7f764b3c16a091dc86effb9d523b1d2c7d0` → commit
   `b2dda33f6726d7f36fbe3491aec7cd7a66184809`, tagger `2026-10-20T12:56:35Z`; release `424060629`
   is `v1.9.0`, published `2026-10-26T09:35:44Z`, with `CITATION.cff` 2,978, `manifest.json`
   55,780, `quantrisk-suite-results.zip` 145,672 and `technical_report.pdf` 1,005,786 bytes, all
   created `09:35:41Z` and updated `09:35:42Z`–`09:35:43Z`. `tools.verify_evidence_manifest` prints
   `Evidence is intact.` with 95 entries and `0 on disk but not in the manifest`. No regeneration
   occurred.
2. **The pin is a guard, not a sentence.** `--reading artifact_revision` prints
   `artifact_revision 17df062040b8`, `pinned_revision 17df062040b8`, `pin_holds true`, `gap 0`,
   `matches_tip false`. V10 does not weaken it and does not re-run the V7 forged cases, because no
   code moves.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** `--check-ceilings`
   prints **15** keys, 13 `ok`, 2 `SKIP`. `plants_not_rejected_by_their_guard` prints
   `precondition absent` and its `corpus` says the collector measures only the declaration because
   the sweep's gitignored scratch never reaches the runner. `installed_user_identity_mismatch`
   prints `precondition absent` and its `corpus` says the clean-venv probe installs a second
   environment the runner cannot have. Both reasons still agree with their `corpus` and
   `can_fail_because` fields. V10 does not give either a runner-side verdict.

**The archive re-counted at `ca94a2c`.**

| quantity | command that produced the reading | value |
|---|---|---|
| registry tasks / suite members | `--reading registry_parity`; `with_extras_census` | 19 / 19, `mismatch []`; `gap 0`, 19 / 19 |
| plants | `runner --list` | **195** (V8's census `195/195` at `5ec3fab` — development-side vantage; the sweep has no CI lane) |
| ceiling keys | `--check-ceilings` | **15** — 13 `ok`, 2 `SKIP`, 0 `FAIL` |
| manifest | `tools.verify_evidence_manifest` | `Evidence is intact.` (95 entries) |
| formatter corpus | `--reading formatter_census` | **242 / 242**, both differences empty |
| pytest nodes | `--collect-only` | **560**; offline **491**, `collection_errors 0` |
| named CI steps | the workflow's `- name:` lines | **34** |
| living documents / lane contract | `docs_rederivation`; `lanes_documented_vs_executed` | 5 documents, `gap 0`, `derived {95, 195, 19, 19}`; `gap 0` |
| artifact revision / runtime reachability | two readings | `gap 0`, `pin_holds true`, `matches_tip false`; `reached_by_neither []` |
| `V7_PROMPT.md` before the repair | heading-span measure over §1–§3, §6–§8 | **154 total / 98 prose** — the same figure `V7_LEDGER.md` H6 reports |
| static gates | `ruff check .`; `ruff format --check .`; `mypy python/quantrisk tools` | `All checks passed!`; `242 files already formatted`; `Success: no issues found in 74 source files` |

**What this unit takes, and what it excludes.** It takes one finding, A1: repair `V7_PROMPT.md` §8
so that it states one hard bound (431) and reports V6–V9's figures as references rather than gates,
while `V7_LEDGER.md`'s H6 verdict and §5's H6 row stay byte-identical. The repair must describe the
old rule and why it failed before stating the new one, so the edit cannot be mistaken for a quiet
reword. V10 excludes B, C, any edit outside §8, any new census, and any change to a source file,
policy asset, test, workflow, manifest, artifact, tag or release asset.

**Deliberately not done in Phase 0.** No file other than `V10_PROMPT.md` and this ledger was
written, no edit to `V7_PROMPT.md` was made, no census was run and no push was made. Every number
above is a reading at `ca94a2c`. The repair and its before/after measurement belong to the
implementation commit; no verdict is claimed before the tool prints it.

**The two pushes.** The first carries Phase 0, the implementation and the Phase 5 report; the second
carries the terminal entry only. No third is implied. Each push's CI is read from the API after the
tool reports it; the first tip's run is attributed in the terminal entry and the second tip's run in
the session handoff.

---

### 2026-11-12, V10 implementation — A1, the §8 repair

**What changed.** One section of `V7_PROMPT.md`, §8, and nothing else. The withdrawn text is quoted
here because the file no longer carries it:

> `V3_PROMPT.md` §0 caps its prose sections at 431 lines measured by heading span. V6's is 146 lines
> with 88 lines of prose. V7's prose sections (§1–§3, §6–§8) may not exceed that 88-line figure
> without the Phase 5 report naming which V6 rule was never executed; the hard bound remains 431.
> Growth is allowed only in §5's finding table and §3's lane inventory. V7 adds no section beyond
> V6's eight.

**What replaced it.** §8 now states 431 as this file's only hard bound, records the old soft cap and
growth clause as withdrawn gates together with the reason, and reports V6–V9's 146 / 88, 154 / 98,
161 / 107 and 164 / 112 as reference figures that a later file may exceed, printing its own
measurement beside them. The reason is stated in the file: V7 met §8's escape clause by naming
`V6_PROMPT.md` §7's never-executed rule, but its added lines sit in §6 as well as §5, so the growth
clause was not met — and a bound whose author must argue an escape clause to stay inside it is not a
bound.

**Why this is a repair, not a rewrite of history.** `V7_LEDGER.md` still records H6 as **PARTIAL**
with its 154 / 98 measurement, and §5's H6 row still prints the V7-era check on line 97, unamended.
Those are readings at V7's tip; what V10 changes is the rule the file states for itself, which was
never a reading. `V8_LEDGER.md` and `V9_LEDGER.md` both say the file was untouched — true at their
tips, and neither ledger is edited. `git diff --stat ca94a2c..HEAD -- V7_LEDGER.md V3_PROMPT.md
V8_PROMPT.md V9_PROMPT.md V8_LEDGER.md V9_LEDGER.md` prints 0 lines.

**Before and after, measured by the same heading-span rule.**

| reading | before (`ca94a2c`) | after | delta |
|---|---|---|---|
| `V7_PROMPT.md` total lines | 154 | **165** | +11 |
| `V7_PROMPT.md` prose lines (§1–§3, §6–§8) | 98 | **109** | +11 |
| withdrawn clauses present (`may not exceed that 88-line`, `Growth is allowed only`) | 2 | **0** | −2 |
| `\| H6 \|` row | line 97 | line 97 | unchanged |
| `V7_LEDGER.md` bytes | — | unchanged | 0 |
| `V7_PROMPT.md` section count | 8 | 8 | 0 |

**Gates and counts after the change, at this commit's tree.** `ruff check .` prints
`All checks passed!`; `ruff format --check .` prints `244 files already formatted`;
`mypy python/quantrisk tools` prints `Success: no issues found in 74 source files`;
`--check-ceilings` prints **15** keys, 13 `ok`, 2 `SKIP`, 0 `FAIL`; `--reading formatter_census`
prints **244 / 244** with both differences empty; `--reading docs_rederivation` prints `gap 0`,
5 documents, `derived {95, 195, 19, 19}`; `tools.verify_evidence_manifest` prints `Evidence is
intact.`; `runner --list` prints **195**; the workflow still has **34** named steps;
`--collect-only` prints **560** collected. No count moved except the formatter corpus, which V10's
two new Markdown files took from 242 to 244.

**What was decided.** A1 is fixed: the file's sizing rule is now one hard bound plus reported
references, and the historical partial verdict is preserved in the ledger and in §5. V10 adds no
guard, plant, ceiling key, CI step, lane, living document or artifact, and no reading was rewritten.
The only changed paths in this commit are `V7_PROMPT.md` and this ledger.

---
