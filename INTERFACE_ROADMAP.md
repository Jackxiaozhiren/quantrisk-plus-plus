# INTERFACE_ROADMAP.md — QuantRisk++ Interface Decision & User-Value Contract

> **A decision record and an executable prompt.** This document answers one question the
> repository has deferred: what interface, if any, should QuantRisk++ present to a wide
> audience — web, app, CLI, or something else — and what value that interface is supposed
> to deliver, stated so that a later run can check whether it did.
>
> It is a sibling of `REFACTOR_PROMPT.md`, not a rival: that document fixes the
> reproducibility contract; this one decides what should sit on top of it, and explicitly
> refuses to build anything on top of a broken one. §3 carries the dependency in both
> directions.
>
> The same discipline applies as in `REFACTOR_PROMPT.md`: **no current-state numbers are
> transcribed into this body.** Every quantity is produced by a named command at run time
> and compared against a ceiling. If a sentence here disagrees with a fresh reading, the
> reading wins and this sentence is a defect.
>
> **How to use this document.** Open it from inside a coding agent working in this
> repository and treat §1–§14 as your operating instructions. Do **not** paste it into a
> chat window — the tail that truncates is the Definition of Done and the rails, and an
> agent that never received them reports success having bypassed them. The file on disk is
> the source of truth; read it whole. Cross-session state lives in `INTERFACE_LEDGER.md` at
> the repository root, never in chat history; one scope unit per session, named in the
> opener, and the ledger is committed before any file is built.

---

## 目录 / Table of Contents

- [1. Role](#1-role)
- [2. The question, and the answer](#2-the-question-and-the-answer)
- [3. Dependency on the refactor](#3-dependency-on-the-refactor)
- [4. Who the users are, and what they are actually trying to do](#4-who-the-users-are-and-what-they-are-actually-trying-to-do)
- [5. The value ledger — and the anti-fabrication rule](#5-the-value-ledger--the-anti-fabrication-rule)
- [6. Interface candidates, scored](#6-interface-candidates-scored)
- [7. Decision record](#7-decision-record)
- [8. Facts Protocol for this lane](#8-facts-protocol-for-this-lane)
- [9. Phase plan](#9-phase-plan)
- [10. Laws and the liveness table](#10-laws-and-the-liveness-table)
- [11. Non-goals and priced locks](#11-non-goals-and-priced-locks)
- [12. Safety rails](#12-safety-rails)
- [13. Anti-patterns](#13-anti-patterns)
- [14. Definition of Done](#14-definition-of-done)
- [15. Condensed paste version](#15-condensed-paste-version)

---

## 1. Role

You are simultaneously:

- **Product engineer for a research artifact** — the thing being productised is not a model
  and not a service; it is *a chain of evidence a stranger can walk*.
- **Interface architect** — you decide the surface, and you defend it against the gravity
  pull toward a dashboard.
- **Verification engineer** — every rendered figure, every reproduced number, every claim
  this lane adds to the front page must have a producer that runs in the environment that
  quotes it.

You are not a marketing writer. You do not assert adoption, time saved, or user counts
without a measurement (§5).

---

## 2. The question, and the answer

**Question:** should this project get a front end, and if so — web, app, CLI, or other?

**Answer, in one line:** **CLI as the primary surface (it already half-exists), plus a
static read-only evidence site as the reach surface, plus an agent-facing (MCP) surface as
the differentiated one; no compute dashboard, no native app, no accounts.**

The reasoning is in §6 and the commitments in §7. The part that is easy to miss: the
honest answer is *sequenced*, not *rejected*. A UI built on top of recorded reproduction
commands that do not run from the repository root would automate a broken provenance claim
and make it look authoritative. That is the one outcome worse than having no UI.

**Why the repository's own prior answer was incomplete.** `docs/project_scope.md` states
"no Web App / dashboard as the core value (a minimal CLI/demo only)" and `PROJECT_SPEC.md`
§1 names a stock-prediction dashboard as an anti-goal. Both are correct as rejections of a
*junk* interface. Neither ever asked the real question — what surface would make the
existing claim ("every number traces to the command that produced it") reachable to
someone who is not the maintainer. This document asks it.

---

## 3. Dependency on the refactor

This lane **enters only after** `REFACTOR_PROMPT.md` has landed:

1. the in-package registry that is the single source of truth for runnable studies,
2. canonical invocations derived into the evidence manifest (module-path form, executable
   from the repository root),
3. the `run` subcommand on the installed CLI,
4. the command-form guard active with a plant proving it can fail.

**Check (this is testable, not aspirational):** the manifest's recorded commands all
resolve as runnable invocations, and the guard over that property is ACTIVE in
`REFACTOR_PROMPT.md`'s liveness table. Until that holds, this lane runs Phase 8 (facts) and
Phase 9.0 (feasibility probe) only, and reports; it builds no surface.

**Why the order is not conservatism.** Every interface below is a *projection of the
provenance chain*. A projection of a chain with holes renders the holes beautifully and
permanently — a published web page is subject to the erratum rule, not a fix-forward.

---

## 4. Who the users are, and what they are actually trying to do

Ranked by how much of the project's real value each can extract from the *current* code
base, not from an imagined audience.

| # | Audience | Job to be done | What they need from the interface |
|---|----------|----------------|-----------------------------------|
| U1 | **Numerical / quant reviewers** — a thesis examiner, an interview panel, a colleague who suspects a number | Walk from a published claim to the command that produced it and *run it themselves* | Provenance-first reading: claim → artifact → canonical command → digest. Terminal-capable. |
| U2 | **Practitioners auditing model-assisted decisions** — the actual research thread this project sits in | Reuse the *method* (frozen protocol, false-discovery control, declared evidence boundary) on their own problem | The pattern, spelled out with its guards, plus a place to see which checks exist and what each one refuses |
| U3 | **Contributors / future maintainers (including a future agent)** | Extend or re-verify without learning an oral tradition | Discoverable tasks, one invocation shape, gates that fail loudly |
| U4 | **Students and self-taught quant readers** | Learn what "verified" costs, by reading a small real case | Narrative reading surface: findings first, math behind it, limitations not hidden |
| U5 | **AI agents** (this is not hypothetical for this repository) | Fetch a number and its provenance without parsing markdown | A structured, read-only tool surface — the only audience for which the CLI is *worse* than something else |

**Deliberately absent, and why:** retail investors seeking signals. The engine ships no
expected-return model, makes no recommendation, and has never touched live prices; an
interface that implies otherwise is a misrepresentation, and the anti-goal line in the
scope document exists to keep that from happening by degrees.

---

## 5. The value ledger — and the anti-fabrication rule

The project's value to its users and to the public is **auditability, not convenience**.
Concretely, what a user gets that they cannot get from QuantLib or PyPortfolioOpt:

- an answer to "how do you know that is right, and where does it stop being right?";
- a corpus of *documented failure modes of plausible numbers*, each caught by an executed
  check rather than by reading;
- a worked example that verification is a first-class engineering object.

**Efficiency and time value are real but must be measured, not asserted.** State each as a
hypothesis with a producer, and let the ceilings file hold the numbers:

| Hypothesis | Measurement (free, no human subjects required) |
|------------|-----------------------------------------------|
| H1 — A cold user reproduces a published number without reading the repository | Scripted run: fresh venv, neutral cwd, one command from install-listing to artifact; assert the run needs zero repo checkout and zero prior file names; record wall clock |
| H2 — Provenance is complete over the published set | Collector computes the share of manifest artifacts whose recorded command resolves; ceiling is a policy number, and the metric must be able to fail |
| H3 — The reading surface never drifts from the evidence | Build-time diff: every figure the site renders equals the value read from the artifact it claims; the site is generated, and a re-run against a mutated artifact turns the gate red |
| H4 — Cost stays zero | CI log shows no paid service; hosting is the free static tier; the build's own budget line is asserted in the report |

**Anti-fabrication rule (inherited from V1 §4 and non-negotiable here):** no user counts,
no "saves N hours", no adoption percentages, no testimonials, no screenshot of a page that
the build cannot produce. A number with no producer is deleted from this lane, not
caveated. This is the same law that already governs the repository's documents; extending
it to a website is the whole difference between an evidence site and a brochure.

---

## 6. Interface candidates, scored

Axes, chosen because they decide *this* artifact's success, not a generic product's:

- **Fidelity** — can it express the provenance chain as the primary object?
- **Reach** — how much of §4 can it actually serve, at what cost of entry?
- **Cost** — build + carry cost under the project's $0 constraint, including maintenance.
- **Failure risk** — what does it do when the underlying chain has a hole?

| Candidate | Fidelity | Reach | Cost | Failure risk | Verdict |
|-----------|----------|-------|------|--------------|---------|
| **CLI (installed, offline)** | Highest — the command *is* the provenance object | U1, U3, partly U5 | Lowest: it exists; three subcommands already ship | Low: a wrong CLI output is caught by the same gates as the library | **Adopt as primary (I1)** |
| **Static read-only evidence site** | High if and only if generated from artifacts | U1, U2, U4 — the only surface that reaches a non-installer | Low: generator + free static hosting; no server, no DB, no auth | Medium: renders holes beautifully → strictly gated on §3 | **Adopt as reach surface (I2)** |
| **Agent-facing read-only tool surface (MCP)** | Highest for machine consumers: number + command + digest as structured output | U5, and U1 when they work inside an agent | Low-medium: a thin projection over the registry; no new computation | Medium: an agent can *cite* the site without walking it → must return provenance, not just values | **Adopt as the differentiated surface (I3)** |
| **Notebook / reproducible-example gallery** | Medium: notebooks drift from code | U4 | Medium: each cell is a claim needing a producer, and notebook outputs are exactly the kind of stale artifact this project exists to avoid | High: silently stale | **Reject for now (N1)**; the site's per-study page serves the same need with generated content |
| **Interactive compute web app (Streamlit-class)** | Low: a form over a model hides the chain | U4 in appearance only | High: hosting a runtime, data upload, session state, secrets | High: invites "what does it predict?", which the project refuses to answer | **Reject (N2)** — this is the anti-goal with better typography |
| **Native desktop / mobile app** | Low | Marginal over a website | Highest: platform packaging, updates, signing | High: a stale binary quoting a moved repository | **Reject (N3)** |
| **Trading / portfolio dashboard** | Contradicts the artifact's claim | Would maximize U5-adjacent retail traffic | High | Fatal: implies advice the engine does not support | **Never (N4)** |

**Read the table honestly:** the interesting decision is not web-versus-CLI. It is that
*this project's* natural wide-audience surface is a **generated reading of evidence**, and
its most novel one is an **agent-facing provenance query** — because the audience that most
needs "show me the command" is increasingly an agent quoting the number to a human.

---

## 7. Decision record

**I1 — CLI is the primary interface; extend it into a provenance browser.**
Add to the installed CLI, beside the existing validation/benchmark/demo subcommands and
the `run` subcommand the refactor brings: task listing with each task's canonical
invocation; a provenance query that takes an artifact id or path and prints its manifest
entry (command, revision, category, byte digest, content digest) in both human and `--json`
form; and a findings index that names the artifact behind each published finding.
*Rationale:* zero new runtime, zero hosting, zero secrets, works offline, and every output
is checkable by the same gates as the library. *Consequence:* the CLI becomes part of the
published contract; its output format needs a guard, like everything else here.

**I2 — A static, generated, read-only evidence site.**
One page per published study: the claim, the figure, the recorded command that produced it,
its digest, and its limitations cross-reference; plus findings-first navigation, and a
page for the validation matrix as it is actually stored. Generated entirely from the tree
by a repo tool at build time; deployed as free-tier static hosting from CI; no server, no
database, no accounts, no computation in the browser, no network calls from the page.
*Rationale:* reach for U1/U2/U4 without a Python install, while the object being displayed
stays the chain rather than a chart. *Acceptance spine:* H3 (drift gate) and the
no-literal-numbers law (L2 below).

**I3 — An agent-facing read-only surface over the registry.**
Expose exactly two kinds of query — enumerate studies; resolve a number to its provenance —
returning the canonical invocation alongside the value. No write, no execute, no network
fetch of live prices.
*Rationale:* U5 is the fastest-growing consumer of artifacts like this, and an agent that
quotes a number without its provenance is precisely the failure mode this repository exists
to make visible. This is the interface a dashboard project cannot have, because it has
nothing to answer with.

**N1–N4 — Rejections**, with the reason kept so a future revision can re-open them on
evidence rather than mood. Re-opening requires: a measured user need from §4's list, a
producer for every new number it would display, and a cost line that survives the $0
constraint.

---

## 8. Facts Protocol for this lane

Same instrument discipline as `REFACTOR_PROMPT.md`; do not hand-write a second probe family.

- **Reuse the refactor's collector** (`tools/inventory_orphan_code.py`) for coverage and
  registry facts; add to it — do not duplicate — the interface-specific readings:
  1. *Provenance resolvability*: the share of manifest artifacts whose recorded command
     resolves, and the list that does not.
  2. *Rendered-value equivalence*: for the site build, every figure emitted versus the
     value read from the artifact it claims to render.
  3. *Cold-start reproduction*: H1's scripted run, with its wall clock and its dependency
     on file names (the assertion is that the latter is empty).
- **Snapshot:** `build/interface_inventory.json` (gitignored, regenerates, carries the
  revision and the producing command per line).
- **Ceilings:** extend the committed ceilings file with this lane's policy numbers. Never
  a key that structurally cannot fail where it runs; never a counter that passes because
  its corpus was empty — each prints what it counted and what it excluded.

---

## 9. Phase plan

**Ledger first.** Open `INTERFACE_LEDGER.md` at the repository root, commit it before
building anything, and record in it: the Phase 0 readings with the revision and environment
each was taken on, the declared scope unit, and the H1–H4 measurements as they are produced.
A later session re-runs Phase 0 rather than trusting the stored entry.

**Phase 0 — Prerequisite gate (§3).** Verify the refactor's four conditions on the current
tree and record the readings. If they do not hold: run only Phase 1 below, report, stop.
Do not build a surface on an unverified chain.

**Phase 1 — Feasibility probe, read-only.** Build nothing permanent. Answer with commands:
can a site page be generated such that every displayed figure is *read* from an artifact in
the same process? Can the CLI print an artifact's provenance without touching the network?
Print the smallest version of each output and its failure mode. This phase exists to kill
the plan cheaply if the answer is no.

**Phase 2 — I1: CLI provenance surface.** Subcommands, `--json` shapes, and the output
contract guard. Write the failing test first for every printed field. Existing subcommand
outputs stay byte-stable; assert, do not assume.

**Phase 3 — I2: generator.** A repo tool that emits the static site from the tree: study
pages, findings pages, matrix page, figure references resolved from committed artifacts,
per-page provenance block. Two hard rules inside the design: the generator's source
contains no numeric literals from the evidence set (format and layout constants are the
only allowed numbers, and the law's check names that boundary), and the build succeeds
with the network unavailable.

**Phase 4 — I2: publishing + the drift gate.** Free-tier static deploy from CI, never from
a laptop; the drift gate runs as a build step and fails the deploy on any mismatch;
a plant proves the gate is not decorative — mutate an artifact copy, show the gate red,
restore, show it green, and name the mechanism in the report.

**Phase 5 — I3: agent-facing read-only surface.** Thin projection over the registry and
manifest. Acceptance: the value and the provenance are returned together, always; a query
that cannot resolve provenance returns a refusal naming the gap, never a bare number.

**Phase 6 — Front page and coherence.** README's entry path rewritten so the first thing a
non-maintainer sees is *how to walk a number*, with the reproduction surface as the example.
Every counted claim this adds is owned by a producer in the same commit, per the
repository's existing inventory guards.

**Phase 7 — Measurement and report.** H1–H4 values, the liveness table, the deliberately
not done list, and an explicit statement of which hypotheses failed — a value claim that
turned out false is a result, and it is recorded as one.

---

## 10. Laws and the liveness table

Each law: predicate to execute, plus the precondition it assumes. No predicate = VOID, and
a VOID law may not be cited to justify or block work.

| # | Law | Precondition | check: |
|---|-----|--------------|--------|
| I-L1 | **Chain before surface.** No interface artifact is built while any recorded reproduction command fails to resolve. | §3's conditions are measurable. | Provenance-resolvability reading, from the collector, not from this document. |
| I-L2 | **Generated, never retyped.** Every figure on a rendered page is read from its artifact at build time. | The generator exists. | Source scan for evidence-shaped numeric literals, plus the drift gate on a rebuilt site; a planted stale artifact must turn the gate red. |
| I-L3 | **No compute in the reader.** The site and the agent surface are read-only. | Deployment exists. | Build output contains no request-execution path; a probe attempting computation is refused by design, not by omission. |
| I-L4 | **$0 carried cost.** Hosting, build, and the agent surface run inside free tiers and existing CI. | Deploy configured. | Diff over the range: no paid service, no new secret, no key; the report quotes the plan's own budget line, not an assertion. |
| I-L5 | **Offline build.** The site build completes with no network. | Generator exists. | A build executed with network disabled; a build that silently needs network is a High finding. |
| I-L6 | **Provenance is returned with the value, always.** | The manifest and registry exist. | Every machine-readable response carries the command, revision, and digest; one response without them fails the gate. |
| I-L7 | **Front-page claims have owners.** Any count or figure added to README or the site names its producer in the same commit. | The repository's claim-inventory guards are ACTIVE. | Run those guards; a new unowned claim turns them red — verify the mechanism can fail before citing green. |
| I-L8 | **No fabricated value.** H1–H4 are measured or reported unmeasured. | A report exists. | Every value claim in the report maps to a recorded run; unmapped claims are deleted. |

Liveness at authoring: **all VOID.** None of these laws has an executable target until
Phase 0 passes and the generator exists; a law cited now to justify building something is
being misused. The table is filled by the executor from readings, not by editing prose.

---

## 11. Non-goals and priced locks

| # | Locked / excluded | Cost of the lock | Bypass |
|---|-------------------|------------------|--------|
| IN1 | No compute dashboard, no forecasting or recommendation UI | The project stays un-marketable to the audience that would misuse it; reach (U4) is served by reading, not by forms | Only with a written scope amendment and the maintainer's explicit decision |
| IN2 | No accounts, no server-side state, no database | No personalisation, no saved portfolios | Never in this lane |
| IN3 | No live market data | The site cannot show "today"; published evidence is historical by design, and that limitation is published, not hidden | Never — the engine has never been run against live prices |
| IN4 | Native app | No offline mobile story | Only on evidence of a need §4 cannot otherwise serve |
| IN5 | `python/quantrisk`'s public API names | Interface work must not rename the shipped surface | A separate, approved phase |

---

## 12. Safety rails

- Everything from `REFACTOR_PROMPT.md` §14 applies unchanged; this lane inherits it.
- Publishing is an outward action: **each deploy needs explicit per-action approval.**
- No new paid service, no new secret, no new credentials — including "free tier" services
  that require an account.
- The site must not quote a released tag's evidence while rendering a different working
  tree; the build names the revision it renders, and the gate compares.
- Screenshots and demo assets are generated by the build, never placed by hand; a hand-
  placed image is a claim with no producer.

---

## 13. Anti-patterns

- Building the pretty layer first because it demonstrates progress to an audience.
- Rendering a number the generator did not read.
- A "provenance" label attached to a timestamp — provenance is command + revision + digest.
- Using the agent surface to make the engine sound advisory.
- Treating a green drift gate as proof until it has been shown to go red.
- Letting the reader become the maintenance burden the library was carefully not.

---

## 14. Definition of Done

1. Phase 0's readings recorded and §3's dependency actually satisfied (or the lane stopped
   at Phase 1 with a written reason — a stopped lane that reports honestly is Done-lite,
   not a failure).
2. I1 shipped: installed CLI answers "what produced this number" offline, with the output
   contract guarded.
3. I2 shipped: site generated from the tree, drift gate ACTIVE *and proven falsifiable by a
   plant*, deployed from CI at zero cost, building offline.
4. I3 shipped: value and provenance always returned together; refusals name the gap.
5. H1–H4 measured with numbers that exist only in the snapshot and the report, plus a
   filled liveness table and a "deliberately not done" list.

---

## 15. Condensed paste version

> Read `INTERFACE_ROADMAP.md` (QuantRisk++ interface lane) and execute it in order. It
> decides: **CLI primary, static generated read-only evidence site for reach, agent-facing
> provenance queries as the differentiated surface; no dashboard, no app, no accounts, no
> live data.** Phase 0 first: verify `REFACTOR_PROMPT.md` landed the registry, the canonical
> module-path reproduction commands, the `run` subcommand, and an ACTIVE command-form guard —
> if any is missing, run only Phase 1 (feasibility probe) and report; never build a surface
> over a chain with holes. Then: CLI provenance commands with guarded output contracts →
> a site generator that *reads* every figure from its artifact (no evidence-shaped numeric
> literals in generator source, build must succeed offline) → free static deploy from CI
> with a drift gate you have proven can fail via a planted stale artifact → a read-only
> agent surface that always returns value together with command, revision, and digest, and
> refuses with a named gap otherwise. Facts live in the collector's snapshot and the
> committed ceilings file, never in prose. Value claims (cold-start reproduction, provenance
> coverage, zero drift, zero cost) are measured as hypotheses H1–H4 or reported unmeasured —
> no user counts, no "hours saved", no hand-placed screenshots. Publishing needs per-action
> approval; carried cost stays $0; no new secret or account.
