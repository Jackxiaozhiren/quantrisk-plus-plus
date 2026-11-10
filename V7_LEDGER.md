# V7_LEDGER.md — cross-session state for the V7 series

Each entry records what was run, what it printed and what was decided, in that order. A number
quoted from an earlier series is named as a historical reading and re-measured before it is used as
a V7 fact. `V7_PROMPT.md` is the rail set; this file is the state.

---

### 2026-11-10, V7 Phase 0 — the series launched at `d975baa`

**Why this phase exists.** V6 closed G1–G6 and left nine deliberately-not-done items in
`V6_LEDGER.md` Phase 5 §4 and seven handoff items in its §6. Item 1 of that handoff names the one
substantive residue: the committed suite artifact's pin is a written decision, not a guard, and a
future series that wants a checkable pin needs a reading with a forged-input or plant proof and its
own approval. This is that series.

**The recommendation this approval accepts.** V7 takes one substantive change — H1, turning V6's
written artifact pin into a two-direction checkable guard by extending the existing
`artifact_revision` reading and its ceiling row, with forged-input proofs in both directions — and
rejects or retains the rest with evidence. No harness redesign, no new CI lane, no new plant,
ceiling key or CI step, no re-run of the evidence chain, no regeneration of a published asset.
This is the smallest change that leaves the repository more checkable than it found it: `V5_PROMPT.md`
§1 forbids manufacturing new gates to replace inconvenient ones, so V7 extends an existing guard
and an existing ceiling row rather than building machinery to police a sentence. The pin also makes
V6's "no silent re-freeze" rule executable, because an undeclared rewrite of the committed artifact
now fails a reading instead of only contradicting prose.

**Approval, verbatim.** `授权启动 V7，按你的建议推进剩余系列` (2026-11-10). Per `V7_PROMPT.md` §6
this is the maintainer's **series-wide** approval, recorded here before any outward action. It
explicitly overrides the case-by-case rule for the V7 series and covers H1–H7, the Phase 0 entry,
the implementation, the Phase 5 report, the terminal entry and the two named pushes. It does **not**
authorise editing any earlier prompt or `V7_PROMPT.md`, a harness redesign that reopens §4, a
declared re-run of the evidence chain, a tag movement or release asset replacement, a new CI lane,
or a third push. The V6 series-wide approval (`继续` + `整个剩余系列（推荐）`) is spent and is not
reused; the V6-01 approval is likewise spent.

**Revision and vantage.** `HEAD` = `origin/main` = platform `main` =
`d975baa7c9da67de776332b0f0321e27471cef37`; `git status --porcelain` prints 0 lines. Vantage: the
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
   field matches V6 Phase 5 §8. No regeneration occurred.
2. **The committed suite artifact is pinned in writing but not guarded.**
   `benchmarks/suite/results/suite_run.json` names `git_commit 17df062040b8`,
   `binary_git_commit af7595749188`, `working_tree_dirty true` and 21 `uncommitted_paths`; its
   `provenance` begins `ran from 17df062040b8 plus the uncommitted changes ...`. `--reading
   artifact_revision` prints `gap 0`, `matches_tip false`, `object_check "the revision names a
   commit in this clone"`, `repository_is_shallow false`, `tip_being_verified
   d975baa7c9da67de776332b0f0321e27471cef37`. The reading checks format, object presence and
   provenance self-consistency; it never compares `git_commit` with the pin. A forged revision that
   is also a real commit in this repository is therefore still `gap 0`. That is H1.
3. **The two `SKIP` keys hold only while their preconditions are re-read.** `--check-ceilings`
   prints **15** keys, 13 `ok`, 2 `SKIP`. `plants_not_rejected_by_their_guard` prints
   `precondition absent` and its `corpus` says the collector measures only the declaration because
   the sweep's gitignored scratch never reaches the runner. `installed_user_identity_mismatch`
   prints `precondition absent` and its `corpus` says the clean-venv probe installs a second
   environment the runner cannot have. Both printed reasons still agree with their `corpus` and
   `can_fail_because` fields in `tools/refactor_ceilings.json`.

**The archive re-counted at `d975baa`.**

| quantity | command that produced the reading | value |
|---|---|---|
| registry tasks / suite members | `--reading registry_parity`; `with_extras_census` | 19 / 19; `gap 0` |
| plants | `runner --list` | **195** (last full census `195/195` at `9486c7a` — development-side vantage; the sweep has no CI lane) |
| ceiling keys | `--check-ceilings` | **15** — 13 `ok`, 2 `SKIP` |
| manifest | `tools.verify_evidence_manifest` | `Evidence is intact.` (95 entries) |
| formatter corpus | `--reading formatter_census` | **236 / 236**, both differences empty, `reported_would_reformat 0` |
| pytest nodes | `--collect-only`; `measure_offline_collection` | **560**; offline **491**, `collection_errors 0` |
| named CI steps | the workflow's `- name:` lines | **34** |
| living documents / lane contract | `docs_rederivation`; `lanes_documented_vs_executed` | 5 documents, `gap 0`, `derived {95, 195, 19, 19}`; `gap 0` |
| artifact revision / runtime reachability | two readings | `gap 0`; `reached_by_neither` empty |
| static gates | `ruff check .`; `ruff format --check .`; `mypy python/quantrisk tools` | `All checks passed!`; `236 files already formatted`; `Success: no issues found in 74 source files` |

**What this unit takes, and what it excludes.** It takes H1 (a declared `pinned_revision` in the
`artifact_revision_gap` ceiling row and a `pin` check in `artifact_revision()`, with two forged-input
proofs), H2 (both `SKIP` keys re-read and retained), H3 (every census citation labelled
development-side), H4 (no harness redesign, stated here before any source file is touched), H5
(the pin guard plus two platform re-reads), H6 (the size ratchet and no prompt edits) and H7 (the
environmental pytest failure attributed, not silenced), together with the Phase 5 report. It
excludes a new plant, ceiling key, CI step or lane; it excludes editing any prompt, the manifest,
`benchmarks/suite/results/suite_run.json`, `cpp/`, `bindings/`, `CMakeLists.txt`, `paper/` or any
release asset; and it excludes a third push. `V6_PROMPT.md` §4 already closes the sweep's vantage;
this unit does not reopen it.

**Deliberately not done in Phase 0.** No source file, policy asset or document was edited, no
census was run, no report section was written and no push was made. Every number above is a reading
at `d975baa`. The full census and the final local `pytest -q` belong to the implementation tip, on
a clean tree after the H1 commit.

**The two pushes.** The first carries the Phase 0 commit, the implementation commit and the Phase 5
report; the second carries the terminal entry only. No third is implied. Each push's CI is read from
the API after the tool reports it; the first tip's run is attributed in the terminal entry and the
second tip's run in the session handoff.

---
