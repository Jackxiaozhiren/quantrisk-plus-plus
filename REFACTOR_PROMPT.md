# REFACTOR_PROMPT.md — QuantRisk++ V2: Package Absorption & the Reproducibility Contract

> **A prompt for a coding agent.** You are given a repository that already works, already
> proves itself, and already publishes its evidence. Your job is not to add models and not
> to rewrite anything that is correct. Your job is to dissolve one structural debt — the
> standalone scripts and experiments that live outside the installable package — without
> letting a single published number lose its provenance.
>
> Everything in this document is a law with a `check:` predicate, a procedure you must run,
> or a decision with a stated rationale. If you cannot verify a claim in this document
> yourself, the Facts Protocol (§4) tells you how to re-measure it; the fresh reading wins.
>
> **How to use this document.** Open it from inside a coding agent working in this
> repository and treat §0–§16 as your operating instructions. Do **not** paste it into a
> chat window — this file is tens of kilobytes, the tail that gets cut is always the
> Definition of Done and the rails, and an agent that never received them reports success
> having bypassed them. The file on disk is the source of truth; read it whole.
>
> **One scope unit per session.** The unit is named in the session's opener (a diagnosis
> pass, or Phase 3's step P3.x for a single task). Continuing "one more lane" past the
> boundary is what breaks multi-session documents: the next session inherits a ledger whose
> entries no longer match any one baseline. Cross-session state lives in `REFACTOR_LEDGER.md`
> at the repository root, never in chat history — every session writes its baseline capture,
> findings, and liveness table there and commits that file before touching a source file.

---

## 目录 / Table of Contents

- [0. Series status, termination, size ratchet](#0-series-status-termination-size-ratchet)
- [1. Role](#1-role)
- [2. Mission](#2-mission)
- [3. Non-goals and priced locks](#3-non-goals-and-priced-locks)
- [4. Facts Protocol](#4-facts-protocol)
- [5. Target architecture](#5-target-architecture)
- [6. Ecosystem survey protocol](#6-ecosystem-survey-protocol)
- [7. Phase 0 — Green baseline](#7-phase-0--green-baseline)
- [8. Phase 1 — Diagnosis](#8-phase-1--diagnosis)
- [9. Phase 2 — Approval gate](#9-phase-2--approval-gate)
- [10. Phase 3 — Targeted fixes](#10-phase-3--targeted-fixes)
- [11. Phase 4 — Holistic uplift](#11-phase-4--holistic-uplift)
- [12. Phase 5 — Report](#12-phase-5--report)
- [13. Laws and the liveness table](#13-laws-and-the-liveness-table)
- [14. Safety rails](#14-safety-rails)
- [15. Anti-patterns](#15-anti-patterns)
- [16. Definition of Done](#16-definition-of-done)
- [17. Condensed paste version](#17-condensed-paste-version)

---

## 0. Series status, termination, size ratchet

**V1 is `PROJECT_SPEC.md`.** It is the build prompt that produced this repository, and it
has been executed — the repository itself, its phase reports, and its release notes are the
proof. V1 is not amended, not rewritten, and not deleted; it becomes a historical record
under a priced lock (§3).

**This document is V2.** It runs beside V1 as a refactor lane. It does not inherit V1's
facts, counts, or baselines. Every number you need comes from a command in §4, run now, on
the tree in front of you.

**Series termination condition.** V2 is justified by three measured premises, each of which
you must re-derive before touching anything (§7 Phase 0 step 3):

1. Executable Python lives outside the installable package and reaches it only through
   `sys.path` bootstrap hacks and by-path loading.
2. The evidence manifest's recorded reproduction commands are not uniformly executable from
   the repository root, and no guard polices their form.
3. Static type checking covers the package but not the code outside it.

If your fresh measurement contradicts any premise, stop, write the contradiction into the
Phase 5 report, and re-scope with the maintainer. **A premise that no longer holds voids
the law built on it** — that is the liveness table's job (§13).

**Size ratchet.** V1's total line count is the ceiling for this document's prose sections
(§1–§3, §6–§15). Growth is allowed only in §5's target lists, §4's instrument/ceiling
schemas, and §13's liveness table — those scale with the project; prose does not. If a
future revision of this prompt needs more prose, it must first show which law of this
version was never executed.

---

## 1. Role

You are, simultaneously:

- **Research Software Engineer** — you move code without changing what it computes.
- **Verification & Reproducibility Engineer** — the project's entire argument is that every
  published number traces to a command that actually runs. You are extending that argument
  to the code that produces the numbers, and you are its most sceptical auditor.
- **Packaging Engineer** — `scikit-build-core` + `pybind11` + a C++20 core compiled through
  CMake presets. You know what an editable install does and does not put on `sys.path`.
- **Evidence Custodian** — `evidence/manifest.json` is a ledger, not a cache. You never
  hand-edit it, and you never let a move invalidate a hash you did not re-derive.

You are not a feature developer. You do not add models, do not tune tolerances, and do not
touch the mathematics. Any finding that tempts you to change a number is a finding to
report, not a licence to fix (§14).

---

## 2. Mission

**One sentence:** every executable unit of this project becomes importable, invocable as a
module, declared in one registry, and reproducible by a command that runs from the
repository root — with the published evidence chain byte-stable or re-derived in the same
commit.

**Why a user cares.** Today, reproducing a published study means knowing which directory to
`cd` into and which file to name. After this refactor, a user who has installed the package
runs one command to list every published study and one command to reproduce any study the
package can run offline. That is the whole point: the project's claim — "every number can
be traced back to the script that produced it" — becomes true *for the user*, not just for
the maintainer who knows the layout.

**What "done" means** is enumerated in §16. Nothing in Phase 3 or Phase 4 is complete until
the full local gate suite of §7 is green on the final commit and the maintainer has run the
approval gate of §9 for each new commit batch.

---

## 3. Non-goals and priced locks

Every lock below states the user-visible cost of leaving it locked. A lock entry without a
cost is void; if you find one, record it as a finding.

| # | Locked | Cost of the lock | Bypass |
|---|--------|------------------|--------|
| K1 | `cpp/`, `bindings/`, `CMakeLists.txt`, `CMakePresets.json` | Packaging-level fixes must route through the existing pybind surface. If a migrated task cannot import the compiled extension, that is a finding, not a licence to edit C++. | One cycle, with maintainer approval recorded in the Phase 5 report. |
| K2 | `experiments/*/results/**` and `benchmarks/*/results/**` — the artifact *paths* | Every doc quote, matrix row, and manifest entry keys on these paths; moving them re-opens the entire evidence ledger and contradicts the release-erratum rule (published artifacts are corrected by dated erratum, never by moving what a tag names). | One cycle, maintainer approval, and a written erratum plan. |
| K3 | `PROJECT_SPEC.md` (V1) | Divergences between V1's prescription and reality are recorded in the Phase 5 report, not papered over by editing history. | Never bypassed; superseded only by writing V3. |
| K4 | `evidence/manifest.json` | Hand edits forge the ledger. Only the manifest builder rewrites it. | Never. |
| K5 | The mathematics: formulas, tolerances, statistical thresholds, RNG contracts | A refactor that shifts a tolerance has destroyed the thing the repository argues for. | Never in this lane. |

**Non-goals.** No new financial models. No new experiments. No dashboard, no web UI, no
service layer. No dependency additions beyond what the dev group already carries (any
exception needs maintainer approval per §14). No renaming of public API functions in
`python/quantrisk` — the package's public surface is contract; this lane moves *unshipped*
code, not shipped names.

---

## 4. Facts Protocol

### 4.1 Instruments

Phase 0 creates **one** collector script, `tools/inventory_orphan_code.py`, and only one.
It emits a single JSON snapshot. Do not hand-write a second measurement tool; do not paste
readings into documents. The collector reports, one line per reading, each carrying the
command that produced it and the git revision it read:

1. **Orphan inventory** — every tracked `*.py` outside `python/quantrisk`, classified by
   how it reaches the package: `sys.path` bootstrap, by-path `importlib` load, installed
   import, or not reachable at all.
2. **Bootstrap census** — every `sys.path.insert`/`sys.path.append` site, with the
   directory it injects and the file it lives in.
3. **Command executability** — for every entry in `evidence/manifest.json`, whether
   `generated_by_command` parses as an invocation that could run from the repository root:
   module path resolves, bare filename, mangled token, or no command recorded.
4. **Static-check coverage** — per tracked Python file, whether `mypy` and `ruff` reach it
   under the commands in §7.
5. **Registry parity** — after Phase 3.1, the declared registry versus the filesystem's
   declared tasks, from two independent sources (§13, L5).
6. **Plant liveness** — after Phase 3.2, the mutation sweep's declared plants versus the
   sweep's own summary line, read from the sweep, not from memory.

### 4.2 Snapshot

The collector writes `build/orphan_inventory.json`. That path is gitignored (the `build/`
tree already is); the snapshot rewrites every run and carries a generation timestamp, the
git revision, and the command per line. **The snapshot is telemetry, never policy.**

### 4.3 Ceilings

Committed at `tools/refactor_ceilings.json`. This file is the policy asset the maintainer
reviews; the snapshot is compared against it. Each ceiling names: the metric, the maximum
permitted value, the phase at which it must be reached, and every declared exemption with
its justification. Two structural rules:

- **Never ratchet a key that cannot fail where it runs.** A count of dirty working-tree
  files is always zero on a clean checkout and guards nothing. Every key must be able to
  fail on the runner that evaluates it.
- **Counters must not pass by absence.** An empty-string grep, a zero returned because the
  corpus was empty, a census that excludes its own directory — these are the classic false
  greens. Each ceiling's producing command must prove its corpus was non-empty (print what
  it counted, and what it excluded, and why).

### 4.4 Precedence and the leak test

**Precedence rule:** when any sentence of this document disagrees with a fresh reading
from §4.1, the reading wins and the sentence is a defect of this document. Record it as a
finding with lane `facts-protocol`.

**Leak test:** after you edit this document (you may, with maintainer approval, to fix a
defect), grep it for version strings, commit SHAs, artifact counts, test counts, and state
claims of the form "currently", "no longer", "still at". Every hit is deleted, not
caveated. A number belongs in the ceilings file or the snapshot; never in prose.

---

## 5. Target architecture

These are decisions, made by the maintainer with this document's author. You may amend a
decision only through the §6 survey's evidence, before the §9 approval gate freezes the
architecture. After the gate, a decision change is a new finding with a new approval round.

**D1 — Three classes of executable code, three destinations.**

| Class | Members (by role, not by count — derive the list in Phase 1) | Destination |
|-------|--------------------------------------------------------------|-------------|
| Published studies — the project's own research output; their artifacts are the majority of the evidence ledger | every `experiments/<task>/run.py` | `python/quantrisk/experiments/<task>/` as importable modules (`run(argv) -> dict` core + thin `__main__`), artifact writing through the existing `quantrisk.experiments` metadata helpers |
| Verification instruments — the project's argument, not just its code | mutation plant list, mutation harness, the fifth-order symbolic derivation | `python/quantrisk/verification/` |
| Repository operations — build, hash, verify, typeset, format, fixture recording | evidence manifest builder and verifier, benchmark suite runner, offline-collection meter, data-fixture recorder, shim-stub generator, docstring rewrapper, report builder | a `tools/` package at the repository root, dev-only: never packaged into the wheel (`wheel.packages` stays `python/quantrisk`), invoked as `uv run python -m tools.<name>` |

Rationale for splitting rather than bulk-moving: shipping repository build tooling to
end users widens the package's attack and maintenance surface for zero user value; while
the verification instruments are load-bearing *claims* (the interview-defense document
quotes them) and must be importable and type-checked like the rest of the package.

**D2 — Artifact paths do not move.** `experiments/<task>/results/` stays exactly where it
is. Code moves; evidence paths are frozen (K2). The `run.py` files are deleted after
absorption, leaving each task directory holding only its results. This is what keeps the
doc blast radius at the level of "quotes of script paths" instead of "every artifact
reference in every document".

**D3 — One registry is the source of truth for what runs.** A declarative task registry
lives in the package (`quantrisk.experiments.registry`): each entry carries the task id,
module path, artifact path, evidence category, and the **canonical invocation string**.
The benchmark suite runner (in `tools/`) consumes the registry instead of maintaining its
own hand-written member tuple — the same defect class the existing parity guard already
polices for the suite alone, extended to everything. Third-party or future tasks may
register through the package's entry-point group **in addition** to the static registry,
so extensibility does not force import-time filesystem magic. Both sources are enumerated
by the two-sided test (§13 L5): registry list versus filesystem declaration, each computed
from an independent source, neither derived from the other.

**D4 — Canonical invocations are module paths.** Every task's recorded reproduction
command becomes `uv run python -m <module>` (or, for repo tools, `uv run python -m
tools.<name>`). The manifest builder derives `generated_by_command` from the registry —
never hand-typed. This extends the principle already stated in `pyproject.toml`'s
`[project.scripts]` comment: the CLI checks the installed build, not a source checkout.
The same principle now covers every experiment and tool.

**D5 — The evidence chain is re-derived in one ordered run, not by editing JSON.** Sequence,
exactly once, in Phase 3.5: registry lands → one full suite re-run regenerates the
artifacts (their volatile fields may move; their mathematics may not) → the manifest
builder re-hashes → the verifier proves nothing else changed → the content-digest
invariant (L1) is asserted across categories → every document that quoted a script path or
a command is re-derived in the same commit. If the invariant fails, **stop**: a changed
result is a mathematics finding, and the refactor halts until the maintainer adjudicates
it.

**D6 — CLI surface.** `quantrisk` gains one subcommand (`run`, with a list mode) over the
registry, so an installed user can enumerate and execute every runnable study. The three
existing subcommands keep their behaviour and their output contracts byte-for-byte.

**D7 — Static checks follow the code.** `mypy`'s target list extends to the migrated
modules and to `tools/`; `ruff` already reaches the whole tree and must stay that way.
The end state: every tracked Python file is covered by exactly one of (a checked target,
a declared exemption in the ceilings file) — nothing silently uncovered, nothing
double-counted.

---

## 6. Ecosystem survey protocol

V1's ecosystem research covered **oracles and infrastructure** (pricing libraries,
portfolio optimisers, build tooling). It evaluated no *architecture donor* — no project
whose organisation this repository could learn from. A name-collision search on public
forges for this project's own name returns only small, student-scale repositories; none
carries an architecture worth absorbing wholesale. **Therefore:**

1. Survey at least five real, maintained projects, chosen by you, spanning at least three
   of these classes: AI-oriented quant platforms; event-driven backtesting frameworks;
   risk-measurement libraries; research-workflow/pipeline frameworks.
2. Score every candidate on four axes, and write the scores down with a link to the exact
   file or directory that demonstrates each score:
   - **A1 Component registration and discovery** — how third parties (or new internal
     modules) declare themselves without editing a central hand-maintained list.
   - **A2 Reproducibility/provenance contract** — how a published result records the
     command, revision, and environment that produced it, and whether that record is
     policed.
   - **A3 Packaging of runnable analyses** — how "a study a user can run" is shipped,
     discovered, and invoked on an installed package.
   - **A4 Static-check and CI coverage of non-core code** — whether scripts/tools get the
     same gates as the core.
3. **Absorb organisation, never implementation.** V1 §2.2 (core algorithms must be own
   implementations) is a standing law of this repository; copying code from a survey
   candidate violates it. What you may take: layouts, registries, naming, invocation
   conventions, provenance schemas.
4. Write the survey as a new numbered section of the existing ecosystem research document
   (which already owns the "what we build on" decision record), with a decision table and
   a verdict per candidate: *adopt pattern / reject with reason*.
5. The survey may amend §5's decisions **only before** the §9 gate. After the gate, the
   architecture is frozen for this run.

---

## 7. Phase 0 — Green baseline

Nothing is edited before this phase is fully green. Every command below was executed on the
authoring machine and its exit code captured; if one fails for you, stop and diagnose
before proceeding — a red baseline is information, not an obstacle.

**Step 1 — Clean tree, and a tree that is only yours.**

```bash
git status --porcelain        # must print nothing
```

If the tree shows modifications you did not author — another session's work in progress —
do **not** restore them and do **not** measure on them: a baseline taken over someone
else's WIP certifies nothing and the suite's lanes will report that session's half-finished
guards as your baseline. Instead, re-verify every red lane against HEAD in an isolated
export, which disturbs nobody's work:

```bash
git worktree add --detach <tmp-dir> HEAD
# run the red lane against <tmp-dir>'s tests, with this tree's built extension and venv
git worktree remove <tmp-dir>
```

If HEAD itself is red on any lane, that is a real baseline failure: stop and diagnose
before anything else. Record in the Phase 5 report which lanes were verified where, and
that the working tree's dirt belonged to another session and was left untouched.

**Measure the baseline on the newest revision that has a CI run of its own.** A record or
amendment commit can land without its own run — a run covers the tip it was invoked on,
not every commit after it — and a tip whose lanes have never executed is a hypothesis, not
a baseline. If HEAD is past the newest CI-verified revision (the revision the latest green
run's log names), measure on that revision via the worktree procedure above, and treat the
HEAD-only delta as findings to hand to the session that owns it — never as your licence to
fix concurrent work. A lane that cannot be verified on any revision that has executed is
marked **unverified**, never green.

**Step 2 — Environment, frozen.** CI runs plain `uv sync`; on a development machine always
`--frozen` so a verification run can never rewrite the lockfile:

```bash
uv sync --frozen
```

**Step 3 — Re-derive the three premises** (§0) with the §4 collector (write it first), and
record the readings into the first snapshot.

**Step 4 — The full local gate suite.** These are the CI lanes, runnable offline on a
development machine (capture each command's own exit code; never a pipeline's last stage):

```bash
uv run --frozen ruff check .
uv run --frozen ruff format --check .
find cpp bindings tests/cpp \( -name '*.cpp' -o -name '*.hpp' \) | sort \
  | xargs uv run clang-format --dry-run --Werror
uv run --frozen mypy python/quantrisk
uv run --frozen cmake --preset ci
uv run --frozen cmake --build --preset ci
uv run --frozen ctest --preset ci
uv pip install -e .
QUANTRISK_REFERENCE_TOOL="$PWD/build/ci/quantrisk_reference_tool" uv run --frozen pytest -q
uv run --frozen python scripts/verify_evidence_manifest.py
```

**Step 5 — The suite binding check, and its trap.**

```bash
uv run --frozen python scripts/run_benchmark_suite.py --no-run
```

This command is *read-only in intent but not in bytes*: it re-aggregates the suite's two
tracked summary artifacts on disk. After running it, restore exactly the two files it
rewrote (name them from `git status --porcelain` — never a blanket restore) and re-run the
manifest verifier to confirm the ledger is intact. Record this trap in the ceilings file's
exemption notes; it is the reason Step 4 runs the verifier *after* any suite invocation.

**Step 6 — Mutation instrumentation check.**

```bash
uv run --frozen python scripts/run_mutation_suite.py --list
```

Record the declared plant inventory in the snapshot. The full sweep (every plant must be
rejected by its guard) is Phase 3.2's proof, and its summary line — read from the sweep
itself, not from memory — is the only acceptable evidence.

**Step 7 — Declare scope and timebox.** Write into the ledger: the findings lanes you will
run (§8), the tasks in scope, and a wall-clock budget. No finding outside the declared
lanes may be fixed without extending the declaration first.

**Step 8 — Open the ledger.** Create `REFACTOR_LEDGER.md` at the repository root carrying:
the Step 4–6 exit codes as captured, the premise readings from Step 3 with the revision and
environment each was taken on, the declared scope, and an empty findings table. Commit that
file **before** any instrument or source file is written. Every later session resumes from
it, re-runs Step 4 first, and marks the stored baseline history — not ground truth.

---

## 8. Phase 1 — Diagnosis

Run every lane below against the current tree. Produce findings in exactly one schema —
all fields, every finding:

```
ID | lane | severity | evidence (file:symbol or command output)
   | probe (the command that produced it) | impact | root cause
   | proposed fix | verification | cost | blast radius | confidence
```

The `probe` field is mandatory: it is what lets a later run re-derive your result without
trusting your summary.

**Lanes:**

1. **Orphan code and import hygiene** — the bootstrap census (§4.1 #1–2); by-path loads in
   tests and harnesses; duplicated helpers between scripts and package.
2. **Reproducibility contract** — command executability census (§4.1 #3); which writer
   produces each bad command; whether any guard reads `generated_by_command` for form
   (expect: none — verify, do not assume).
3. **Registry and hand-maintained lists** — the suite's member tuple versus the existing
   filesystem parity guard; what the guard covers, what it does not (repo tools, plants,
   fixtures).
4. **Test and verification validity** — every test that loads code by path; every test
   that asserts a command string; every plant's mechanism: does the guard reject the
   planted defect for the *declared reason*, or does it fail for an incidental one?
5. **Documented claims versus code** — every doc reference to a script path, a run.py, or
   a reproduction command; ownership: which artifact or producer owns each counted claim.
6. **Artifact reconciliation** — manifest entries versus files on disk versus the registry
   (after 3.1); categories; content-digest behaviour on re-run.
7. **Packaging and developer experience** — what a wheel installs; whether an installed
   user can reach any published study; `-m` runnability of every destination module.
8. **Security and CI** — subprocess surfaces in the moved code; CI step paths that break
   when scripts move; anything that would leave a lane green while a gate stopped running.

Severity: **High** = a published claim is false or untraceable; **Medium** = real defect
with contained blast radius; **Low** = hygiene. A finding without a reproducible probe is
not reported.

---

## 9. Phase 2 — Approval gate

**Nothing touches disk before this gate.** Write into the ledger, then present to the
maintainer, in one message:

- the findings table, ranked by impact × effort × risk;
- the proposed Phase 3 commit sequence (one line per commit: finding ID → change →
  verification);
- the ceilings file content for review;
- any §5 decision you propose to amend, with §6 evidence;
- the declared blast radius: every tracked file your sequence will touch, derived from the
  findings, not guessed.

The gate is explicit approval. Silence is not approval. A rejected finding is recorded as
`verdict: rejected, reason: …` and its probe is archived — rejected findings are evidence
too.

---

## 10. Phase 3 — Targeted fixes

**One finding = one minimal change = one commit.** Write the failing check first (a test,
a guard, or a ceiling breach — something that is red before your change and green only
because of it); verify immediately after the change; revert on failure; never bundle.

Run in this order — each step's verification depends on the previous step's:

**P3.1 Registry first, nothing moves.** Add the registry and the parity test (two-sided,
independent sources). Add the canonical-invocation field to every existing member *without
changing where anything lives*. The suite still runs from its old paths; the registry
agrees with it. Gate: full §7 suite green; parity test proves both directions.

**P3.2 Verification instruments.** Move the mutation plant list, harness, and the symbolic
derivation into `quantrisk/verification/`. Update every by-path load; re-point every plant
that edits a file by path. Then run the full sweep and require: every plant rejected, each
for its declared mechanism. **The sweep is load-bearing instrumentation — its move must be
proven by its own output, not by a green import.** Plants whose mechanism changed are new
findings, not silent edits.

**P3.3 Experiments, one task per commit.** For each task: absorb `run.py` into
`python/quantrisk/experiments/<task>/`, registry entry gains the module path, the task's
`sys.path` bootstrap and its root-level file die, the tests that loaded it by path switch
to importing the module, and the tests that assert command strings switch to the canonical
invocation **as a declared intent change** (the assertion's meaning changed; say so in the
commit message). Artifact paths do not move (D2). Gate per task: full §7 suite green.

**P3.4 Repository tools.** Create the `tools/` package; move the repo operations; every
invocation becomes `uv run python -m tools.<name>`; the suite runner consumes the registry
(D3); the CI step that invokes the suite is updated to the new path in the same commit.
Kill every `sys.path` bootstrap in the moved code — with an editable install, the package
is importable and the hacks are dead weight. Gate: CI workflow's steps all point at paths
that exist; §7 suite green.

**P3.5 The one re-run and the evidence chain.** Execute D5's sequence exactly once. The
content-digest invariant (L1) decides success: results must move *only* in the categories
whose content is machine measurement, declared in the ceilings file with the reason. Then
re-derive, in the same commit, every document that quoted a script path or command. If any
correctness-category digest moved: stop, report, adjudicate (§14).

**P3.6 CLI.** Add `run` (D6). Its `--list` output is asserted against the registry by a
test that shares no source with the registry's enumeration (two-sided again). Existing
subcommands' outputs byte-identical: assert, don't assume.

**P3.7 Static-check parity.** Extend `mypy`'s targets per D7; the collector's coverage
census must show every tracked Python file in exactly one bucket; write the census into
the ceilings file. Gate: §7 suite green including the extended `mypy` command, and the
ceiling "uncovered files" must be able to fail (it counts a real, non-empty corpus — print
what it counted).

---

## 11. Phase 4 — Holistic uplift

Enter only when Phase 3 is fully green. Order matters; do not parallelise with Phase 3.

1. **Installed-user proof.** Build the wheel; in a clean virtual environment, from a
   neutral working directory, install it and assert *identity* (the imported package's
   file resolves inside the venv, not the checkout); then `run --list` must enumerate every
   registry task, and one offline study must execute end-to-end writing its artifact to an
   explicitly requested output directory. A task that needs a fixture that is not packaged
   must fail loudly naming the missing path — it must never synthesise data (V1 §4 forbids
   fabricated market data; a "convenient" fallback is the same defect wearing a smile).
2. **Documentation coherence.** The architecture document's layout section, the
   reproducibility document's command examples, the front page's claims about how to run
   things — all re-derived from the tree as it now is. Every counted claim traces to its
   owning artifact; the existing inventory guards are the mechanism, not a formality.
3. **Dead glue deletion.** With the registry as source of truth, the hand-maintained member
   tuple, the bootstrap hacks, and any by-path loader that no longer has a caller are
   deleted — completely, not commented out.
4. **DX residue.** Contributor documentation's "how to run an experiment" becomes the
   canonical invocation, and a CI lane (or ceiling key) proves at least one documented
   command is executable as written.

---

## 12. Phase 5 — Report

Deliver, assembled from `REFACTOR_LEDGER.md` plus the repository state, as a final ledger
entry:

- **Evidence Ledger** — for every finding: ID, verdict (fixed / rejected / deferred), the
  probe, and the commit that closed it.
- **The liveness table** (§13) filled with ACTIVE/VOID and the reading that decided each.
- **Ceilings file final state** with the maintainer's review notes.
- **The `deliberately not done` list** — findings you found but did not fix, with reasons.
  An honest "not done" is required; an empty list is suspect.
- **Premises audit** — re-state §0's three premises with your final readings; if any
  premise's law ended VOID, say what that means for the next revision of this prompt.
- **Series handoff** — what V3 must contain, derived from this run's evidence (not from
  this document's prose).

---

## 13. Laws and the liveness table

Every law carries a `check:` predicate and the precondition it assumes. A law whose
precondition no longer holds is VOID and may not be cited to justify or block work. At
Phase 1's end, produce the table in the ledger: law | status (ACTIVE/VOID) | the reading
that decided it.

| # | Law | Precondition | check: |
|---|-----|--------------|--------|
| L1 | **Content-digest invariance.** After the one re-run (D5), every artifact's content digest is unchanged except in categories declared measurement-of-machine in the ceilings file. | Registry is the source of truth for commands; categories in the manifest are trusted as declared. | Compare the pre-run and post-run manifests' content digests per category; any correctness-category movement fails the build. |
| L2 | **One finding, one commit.** No mega-commits; every commit's subject maps to a finding ID. | Findings exist from Phase 1. | `git log` of the refactor range: every subject references its finding; every finding appears at most once as a fix. |
| L3 | **No gate weakened.** No tolerance loosened, no test deleted, no skip/xfail added to get green. | The §7 suite defines "green". | Diff the refactor range for skip/xfail markers and tolerance literals; each hit needs a declared intent and maintainer approval. |
| L4 | **Canonical invocation.** Every manifest entry's `generated_by_command` parses as a module-path invocation executable from the repository root. | D4 implemented; registry derives commands. | A guard that dry-resolves every command's module; a mutation plant corrupts one command and must be rejected. |
| L5 | **Registry parity, two-sided.** The registry enumerates exactly the declared tasks; the list and the filesystem are computed from independent sources. | Tasks declare themselves in one canonical way. | A test computing the filesystem declaration and the registry enumeration separately and asserting set equality; each source must print what it enumerated. |
| L6 | **No bootstrap hacks in shipped or repo code.** Zero `sys.path` insertions outside the single declared test-bootstrap site (if any), named in the ceilings file. | Editable install provides the package. | Census grep over `python/ tools/ tests/` with the corpus printed; ceiling: zero. |
| L7 | **Plant liveness.** Every declared plant is rejected by its guard, for its declared mechanism. | The sweep is runnable from the new locations. | The sweep's own summary line, captured by the collector; a plant not firing is a High finding. |
| L8 | **Instrument identity.** Any probe that runs the installed package asserts which file it imported. | A wheel or editable install exists. | The Phase 4 proof records `module.__file__` before drawing conclusions. |
| L9 | **Static-check parity.** Every tracked Python file is in exactly one of: mypy-covered, ruff-covered-already, or a declared exemption. | D7 implemented. | The collector's census against the ceilings file; the uncovered bucket must be structurally capable of being non-empty. |
| L10 | **Counted claims are owned.** Every number in front-page documents traces to an artifact or producer that runs in the environment quoting it. | The repo's existing claim-inventory guards are ACTIVE. | Run those guards; add any new counted claim to the inventory in the same commit. |
| L11 | **Facts precedence.** Document loses to fresh reading. | The §4 instruments exist. | Re-run the leak test and one collector reading; any mismatch is a finding against this document. |
| L12 | **Budget.** Total external spend of this refactor is zero; no new paid dependency; any new dependency needs approval. | The dev dependency group is the only allowed source. | Diff of `pyproject.toml` dependency sections over the range. |
| L13 | **Baseline purity.** The Phase 0 baseline is measured against the newest revision with a CI run of its own, from a single vantage (working directory, tests, and fixtures all inside one export), never over a working tree carrying another session's work; foreign WIP is left untouched. | The §7 gate suite defines the lanes. | The Phase 5 report names, per lane, the revision **and the environment** it was verified on; any lane verified only on a foreign-WIP tree, on a mixed vantage, or on a tip that has never executed is marked unverified, not green. |

### Liveness at authoring

The mechanism is proven by production, not by requirement. Evaluated against the tree this
document was written on (each `check:` executed, its exit code captured):

| Law | Status | The reading that decided it |
|-----|--------|-----------------------------|
| L3, L6, L12, L13 | **ACTIVE** | L6's census ran and its corpus was non-empty — bootstrap sites exist outside the package today, the exact defect class the ceiling will drive to zero (the exact reading is owned by the Phase 0 snapshot, not by this table); L12's diff is trivially empty before work starts; L3's and L13's range/rail predicates hold now. |
| L7, L10 | **ACTIVE** | The mutation inventory listing and the claim-ownership guard tests both ran green against HEAD (via the isolated-worktree procedure of L13, after a concurrent session's WIP turned the working tree's run red — which is why L13 exists). |
| L2, L11 | **VOID** | L2 needs Phase 1 findings; L11 needs the §4 instruments — neither exists yet. They activate when their preconditions do. |
| L1, L4, L5, L8, L9 | **VOID** | Each requires an architecture step from §5 (registry, canonical commands, wheel proof, coverage extension). Activating one before its step is a violation, not diligence. |

---

## 14. Safety rails

- Never touch `.env`, credentials, or anything secret-shaped. Nothing in this refactor
  needs network access except the survey (§6, read-only) and the oracle-backed suite run
  (already a CI lane; run it in CI, not by hand, if your machine lacks the oracles).
- Never weaken a coverage gate, delete a failing test, or add `skip`/`xfail` to get green.
  If the baseline is red, the red is the finding.
- Never delete `data/` fixtures, caches of live responses, or vendored directories to
  "clean up". Fixtures are regenerated only by their recorder tool.
- No `--no-verify`, no force-push, no history rewriting, no tag movement. Published
  artifacts are corrected by dated erratum, never by moving what a tag names.
- Outward actions (push, PR, release, issue/comment) require per-action approval; a general
  "go ahead" does not authorize them.
- When the working tree may be shared with another session, stage at hunk level, use
  `git commit -- <path>` to pin ownership, and verify the committed object — not the
  working file — before claiming the commit landed.
- A red command after your change is not noise: capture its exit code from the command
  itself, diff the failure against the previous failure set, and name the cause before
  touching anything.
- Restore operations after a gate that rewrites tracked aggregates must name the exact
  paths from `git status --porcelain`, never a blanket restore — a shared tree may hold
  in-progress work that a blanket restore would destroy.

---

## 15. Anti-patterns

- Substituting generic pain points for measured ones; writing a count into prose.
- A registry built by globbing the filesystem — that is a hand-maintained list with extra
  steps and it defeats the two-sided test by construction.
- Green by absence: a counter that passes because the corpus was empty, an exemption list
  that quietly contains the thing being counted, a census that excludes its own directory.
- Trusting a pipeline's exit code, a subagent's summary, or any "N tests passed"-style
  number read through a pipe.
- Bundling the registry, the move, the manifest, and the docs into one commit "because
  they change together" — they change together *because* each commit's gate says so.
- Editing `evidence/manifest.json` by hand, or "fixing" a bad recorded command by editing
  the JSON instead of re-deriving from the registry.
- Moving `results/` directories "for consistency".
- A migration commit whose message does not declare the intent change when an assertion's
  meaning changed (path-form → module-form command assertions).
- Adding a ceiling that structurally cannot fail on the runner that evaluates it.
- Writing V3 longer than V2 without showing V2 was executed.

---

## 16. Definition of Done

All of the following, evidenced:

1. §7's full gate suite green on the final commit, each exit code captured from its own
   command; and green on CI for that commit (prove from the CI run's own log, not from a
   green badge).
2. The §4 collector's final snapshot shows: bootstrap census at its ceiling (zero outside
   declared exemptions), command executability at its ceiling, static-check coverage per
   L9, registry parity per L5, plant liveness per L7.
3. L1's digest comparison recorded: which categories moved, which could not, and why that
   matches the ceilings file.
4. The Phase 4 installed-user proof: clean venv, neutral cwd, identity asserted, list
   complete, one offline study reproduced end-to-end.
5. Every document that quotes a moved path or command re-derived in the commit that moved
   it; the repo's own claim-inventory guards green.
6. The Phase 5 report, ledger, liveness table, ceilings review, and "deliberately not
   done" list, all on disk and referenced from the final summary.

---

## 17. Condensed paste version

> You are refactoring QuantRisk++ (a C++20/pybind11/scikit-build-core quant risk engine
> with an evidence-manifest verification culture). Goal: absorb the standalone
> `experiments/*/run.py` studies and the verification scripts into the installable package
> (`python/quantrisk/`), move repo tooling to a dev-only `tools/` package, delete every
> `sys.path` bootstrap, and make one registry the source of truth for task discovery and
> for every recorded reproduction command (`uv run python -m <module>` form). Do NOT move
> artifact `results/` paths, do NOT touch `cpp/`/`bindings/`, do NOT edit
> `evidence/manifest.json` by hand, do NOT change any mathematical tolerance.
> Workflow: Phase 0 green baseline (ruff, ruff format, clang-format, mypy, cmake build,
> ctest, pytest with `QUANTRISK_REFERENCE_TOOL` set, evidence verify — all `--frozen`);
> write one collector (`tools/inventory_orphan_code.py`) emitting a gitignored snapshot,
> compared against a committed ceilings file. Phase 1: diagnose (orphan code,
> reproducibility commands, registry parity, plant liveness, doc claims, artifact
> reconciliation, packaging, CI), findings in the mandated schema with probes. Phase 2:
> hard approval gate before any edit. Phase 3: registry → verification instruments (prove
> the mutation sweep by its own output) → experiments one task per commit → tools + CI
> step → one suite re-run with content-digest invariance → CLI `run` subcommand → mypy
> parity. Phase 4: clean-venv wheel proof with identity assertion, doc re-derivation, dead
> glue deletion. Phase 5: report + evidence ledger + deliberately-not-done list.
> Rules: one finding = one commit with the failing check written first; full gate suite
> green before every commit; facts live in the snapshot and ceilings, never in prose; two
> independent sources for every enumeration; a plant that does not fire is a High finding;
> `uv --frozen` always locally; per-action approval for anything that leaves the machine;
> if the tree carries another session's WIP, verify red lanes in an isolated worktree with a
> single vantage, and measure the baseline on the newest revision that has a CI run of its
> own — leave that work untouched.
