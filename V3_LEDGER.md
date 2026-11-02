# V3_LEDGER.md — the cross-session state of the V3 series

Companion to `V3_PROMPT.md`. V2's state lives in `REFACTOR_LEDGER.md` and is not amended here. Every session
working V3 writes its baseline capture, findings and liveness table in this file and commits this file before
touching a source file (`V3_PROMPT.md` §0).

---

### 2026-10-26, opening — the prompt was written from evidence, and no V3 phase has run yet

`V3_PROMPT.md` exists. Nothing else in this series does: Phase 0 has not been run, no premises have been
re-derived under V3's own instruments, and no finding is registered. This entry records what the prompt's
claims were built on, so the first V3 session can check them rather than inherit them.

*Superseded in date order, not rewritten.* Phase 0 ran the same day and its entry is at the foot of this file:
eleven lanes read, all three premises re-derived, and one contradiction recorded against a V2 finding's
rationale. The paragraph above stays because it is that session's dated record; the entry below is the state.

**Readings the prompt quotes, and where each came from.**

| Claim in `V3_PROMPT.md` | The reading | Where it is reproducible |
|---|---|---|
| `quantrisk run --list` advertises 19 tasks and 4 run from a wheel | 19 ids enumerated; 4 exit 0, 15 exit 1 (8 `matplotlib`, 2 `scipy`, 1 `cvxpy`, 3 exit-2 QuantLib validators, 1 `RuntimeError` naming the committed-sibling dependency) | the recipe, not a committed file: `git archive HEAD` into a scratch export, `uv build --wheel`, a fresh venv installing the wheel with base dependencies only (numpy, pandas, python-dateutil, six, tzdata), `cd` to a directory outside the checkout, then every id from `run --list` through `quantrisk run <id> --out <scratch>`. The transcript sits in the gitignored `build/` tree, so it is a recipe a later session re-runs rather than an artifact it trusts |
| `quantrisk validate` runs on no CI job | the workflow contains no `validate` step; `[project.scripts]` declares the CLI; the local reading is 7/7 | `REFACTOR_LEDGER.md` §6 row V2-29 and the Phase 5 not-done list |
| V2 terminated with three premises at zero | bootstrap sites 0, by-path loads 0, unfusable commands 0, files in no static-check bucket 0, corpus 46 files outside the package | the collector's `--check-ceilings` output at `32c6355` |
| Nine of thirteen census-"unreachable" files are live | the orphan census names 13, of which 9 are reached by pytest's path convention or by `importlib.import_module` | `REFACTOR_LEDGER.md`, the P4.3 entry "The guard, and the 13 files that are not dead" |
| The size ratchet baseline is 431 prose lines | heading-span sum of `REFACTOR_PROMPT.md` §1–§3 and §6–§15 | the same measurement as V2's Phase 0 note, re-taken at `32c6355` |
| `V3_PROMPT.md` is inside its own ratchet | 248 prose lines against 431, file total 441 lines | `ruff format --check .` 229 files, and the heading-span sum |
| V2's close-out confirmation is the model for §12's last item | push parity across 12 commits; `812caa0` cancelled and `32c6355` success, both named as such; register 28 rows against a 28-row ledger | `REFACTOR_LEDGER.md`, the close-out entry of 2026-10-26 |

**What the first V3 session must do before designing anything.** Run §7 in full: prove the baseline revision
and vantage, capture each lane's own exit code, re-derive the three premises with the §4.1 instruments, and
record all of it here. The 4-of-19 figure above is a `035e797` reading, not a current one — the wheel has been
rebuilt since, and a premise quoted from another session's tree is exactly the kind of inherited claim V2's
Facts Protocol exists to break.

**Deliberately not yet decided.** `run --list`'s widened contract (K6 names it a decision, not a consequence),
the shape of the lane contract file (§5 lists its role, not its schema), and whether runtime reachability
replaces the `ast` census or sits beside it as a diff — §5 currently proposes the diff, and Phase 1 may refute
that.

---

### 2026-10-26, V3 Phase 0 — baseline, eleven lanes, and the three premises re-derived at `4e85539`

**Revision and vantage.** `HEAD` = `4e85539`, tree clean, and the remote says the same thing: `git fetch`
*failed* (`Failed to connect to github.com port 443`), so the parity claim was taken from
`api.github.com` instead of the cached ref — `repos/…/branches/main` → `4e85539…`, and
`git/ref/tags/v1.9.0` → `d9deb7f76…`, the tag V2 recorded, unmoved. `git rev-list --left-right --count
origin/main...HEAD` reads `0 0`, which after a failed fetch only says the *local* remote-tracking ref agrees
with `HEAD`; the API read is what makes it a statement about the server. Newest revision with a CI run of its
own: `4e85539` itself, run `40443705626`, `completed success`. Between the previous green tip `79caa34` and
this baseline there is exactly one commit and ten added lines of `REFACTOR_LEDGER.md`.

Vantage: the development checkout itself — working directory, tests, fixtures and build tree all under
`/Users/jackson/QuantRisk++`, `.venv` Python 3.12.14, AppleClang 21.0.0.21000334, oracles installed. V2's
Phase 0 needed a detached export because the checkout then carried another session's work; this tree is clean
and equal to the remote, so the checkout *is* a single vantage, and the installed-surface premise is measured
in its own export (below) rather than by mixing vantages. One environment fact worth naming: `cmake --preset
ci` discovers Homebrew Python 3.14 as `FindPython`'s interpreter while `.venv` is 3.12, and the preset builds
both `_quantrisk.cpython-314-darwin.so` and `.cpython-312-darwin.so`. What the pytest lane imports is the 3.12
module under `.venv/lib/python3.12/site-packages/`, refreshed by the lane's own `uv pip install -e .` — so the
lane is honest, but the preset's "discovered interpreter" is not the interpreter under test, and a future
reading that assumes it is would be wrong.

#### The eleven lanes of §7.1

| lane | the command's own rc | the reading |
|---|---|---|
| ruff | 0 | `All checks passed!` |
| ruff format | 0 | **230** files already formatted |
| clang-format | 0 | enumerates **77** sources; the empty-corpus refusal is present and did not fire |
| mypy | 0 | `Success: no issues found in 74 source files` |
| `cmake --preset ci` | 0 | configured into `build/ci` |
| `cmake --build --preset ci` | 0 | 25 targets, linking `quantrisk_tests` and both `_quantrisk` modules |
| `ctest --preset ci` | 0 | **100% tests passed out of 204** in 10.3 s |
| `uv pip install -e .` | 0 | `~ quantrisk==1.9.0 (from file:///Users/jackson/QuantRisk++)`, `uv.lock` untouched |
| pytest | 0 | **559 passed** in 206 s, against the `build/ci` reference tool |
| manifest verifier | 0 | `0 on disk but not in the manifest` / `Evidence is intact.` — **95** entries |
| `--check-ceilings` | 0 | 8 keys at their ceiling, 2 declared SKIP with their reasons |

`git status --porcelain` after the whole sequence is empty, so no lane left the tree dirty and no lockfile was
rewritten.

#### Premise 1 — the advertised surface is false for an installed user

**Confirmed, unchanged in kind and in number.** Recipe (recorded rather than trusted from V2's run): `git
archive HEAD` into `/tmp/v3-p0-export`, `uv build --wheel` there, a fresh `uv venv` installing only that wheel
— base dependencies resolve to numpy, pandas, python-dateutil, six, tzdata — then `cd
/Users/jackson/quantrisk-v3p0-neutral` and run every id `run --list` prints. Identity asserted before any
conclusion: `quantrisk.__file__` under the venv's site-packages, `sys.prefix` equal to the venv, `in-checkout:
False`. Reading: **19 ids, 4 exit 0, 15 exit 1, 4 artifacts written** — 8 `No module named 'matplotlib'`, 2
`scipy`, 1 `cvxpy`, 3 `exit 2` inside the QuantLib validators, and `sixth_book_crossing_map` raising the
checkout-dependent `RuntimeError` that names the committed sibling artifact it validates against. The
transcript is `build/v3-p0-surface.out` on a gitignored path, so the *recipe above* is the reference, not the
file.

#### Premise 2 — gates executing where they claim to

**Holds, but narrower than V2-29's rationale reads, and that is a contradiction worth naming.** Three
readings, all from the workflow and the two lane blocks:

- The `-m` invocations documented in `REFACTOR_PROMPT.md` §7 step 4 and `V3_PROMPT.md` §7.1 are
  `tools.inventory_orphan_code` and `tools.verify_evidence_manifest`; both are executed by the `lint` job.
  Documented-but-unexecuted: **empty**. V2-28's fix holds at this revision.
- The CI's own module invocations are `pytest`, `tools.inventory_orphan_code`, `tools.run_benchmark_suite`,
  `tools.verify_evidence_manifest`, and one `quantrisk run --list`. The console script `quantrisk` is invoked
  for `run` only: `validate`, `benchmark` and `demo` appear in **no** step of any job.
- The mitigation V2-29's "why it matters" cell did not weigh: `tests/python/test_research_api.py` calls
  `cli.main(["validate"])`, `["demo"]`, `["benchmark", "--iterations", …]` and pins each one's output by digest
  (`1641f50f239d95da`, `e077aed0cd074780`, `cb18d49dabffd62c`, plus the `--json` form), and that module runs in
  CI. So "a build that breaks `validate` ships green" is **false as written** — an in-process break is caught.
  What is actually unexercised on the runner is the *entry-point path*: `[project.scripts]` resolution, the
  installed distribution, and the packaged environment, which today is proven only by
  `tools.verify_installed_surface.py` in a second venv, and whose ceiling key is declared SKIP on the runner.
  Phase 1 registers that as the finding; V2-29 stays as V2 recorded it, with this reading as its correction.
- Two more gates with no runner home, both currently declared: the mutation sweep (`plants_not_rejected_by_their_guard`
  SKIPs by declaration) and `tools.measure_offline_collection.py`, which produces the oracle-free count that
  documents quote while nothing on the runner executes that producer — the runner's own no-oracle pytest is a
  different instrument reading a different number: 489 passed and 5 skipped in 219 s on run `40443705626`,
  against 490 collected with four named skips here.

#### Premise 3 — the audit instruments read source, not runtime

**Confirmed, and stronger than the way V2 recorded it.** The collector still classifies **13** tracked files
outside `python/quantrisk` as `not_reachable`. Two independent runtime instruments were then run against that
list, and they do not agree with each other:

- `importlib.import_module` on each path as a module name: **12 of 13 import cleanly**; the failure is
  `tests/python/test_second_book_crossing_map.py` → `ModuleNotFoundError: No module named
  'test_two_factor_bound'`, because line 30 of that module does `from test_two_factor_bound import
  _assert_same_result, _noise_decided_verdicts` — a test reaching a *sibling test* by bare top-level name,
  which resolves only under pytest's own path insertion. That line is itself a Phase 1 seed: it is invisible
  to the import census, unchecked by mypy (tests are ruff-only by declaration), and it is why "importable by
  name" is not a sound runtime instrument either.
- pytest's own `--collect-only -q` log names **6** of the 13 as collected modules, including the one that
  failed the import probe.

The union of the two runtime views covers **13 of 13**, and nothing remains that both instruments fail to
reach — so the honest statement is not "nine of thirteen are live" but "the source parser calls all thirteen
dead and every one of them is reached by something at runtime, while the two runtime instruments disagree on
one". A deletion decision made on the census alone would have removed live code today.

**Provisional instruments, deliberately.** No second measurement tool was written: §4.1 permits one collector,
and the readings above were produced by the commands quoted in each section and recorded here, not committed as
scripts. Promoting them — `declared_cli_surface`, `tasks_runnable_from_wheel`, `lanes_documented_vs_executed`,
`runtime_reachability_gap` — into `tools/inventory_orphan_code.py` is Phase 1 work, and it lands with guards
that can disagree with each of them (§13 N5), not before.

**Not done in this phase, on purpose.** No finding is registered — Phase 0 measures and records; Phase 1
diagnoses. The seeds this phase leaves for Phase 1 are: the entry-point gap above (the narrowed V2-29), the
bare sibling import in `test_second_book_crossing_map.py:30`, the runtime-reachability gap of 13/13 against a
census that reports 0, `tools/generate_shim_stubs` being named by no document's `-m` invocation while nothing
imports it statically, and V2-24 carried open as the premise-1 work item.

---

### 2026-11-02, V3 Phase 1 — eight lanes at `ed9db5a`, five findings, and one instrument that answers before it measures

**Revision, vantage, and the parity reading this time is not a cached ref.** `HEAD` = `ed9db5a`, working tree
clean except one untracked file (`tools/derive_requires.py`, finding V3-04), branch `main`. `git fetch` now
*reaches* the network where the Phase 0 session could not: `git ls-remote origin refs/heads/main` returns
`ed9db5aa9c9f64eb9d618cbee5654a73d3ba5322`, equal to `HEAD`, so parity is a statement about the server read
from the server. CI for the tip: run `40445732572`, event `push`, `completed success`. Two facts about the
remote are recorded rather than acted on: three `pull_request` runs (`3f5b28d`, `79f031f`, `7db01e8`) and two
`codex/*` branches exist on the server and none of them is `main`; they are another session's work and this
session did not fetch, check out, or touch them.

**The five findings.** Each is a measurement taken in this checkout at this revision; the probe is quoted so a
later session can re-run it rather than inherit it.

| id | lane | severity | the reading | the probe |
|---|---|---|---|---|
| V3-01 | installed surface | High | the registry declares no requirement for any of its 19 tasks, and `[project.optional-dependencies]` declares two extras (`plot`, `oracles`) that nothing compares with the modules that need them | `Task.__dataclass_fields__` has no `requires`; `run --list` prints three columns, none of them a requirement; `pyproject.toml` §optional-dependencies |
| V3-02 | CI and gates | Medium | `validate`, `benchmark` and `demo` are invoked by no step of any job; the only execution of `validate` is in-process, through `cli.main(["validate"])` in `tests/python/test_research_api.py`, which pins its output by digest | `.github/workflows/ci.yml` parsed as YAML: every `run:` string, searched for the three subcommands — zero hits; the `study-catalogue` step runs `run --list` only |
| V3-03 | runtime reachability | Medium | the `ast` census calls 13 tracked files outside the package unreachable; `importlib.import_module` reaches 12 of them and pytest's collection log reaches 6, and the union is 13 of 13 | Phase 0's two probes, re-read here as a finding rather than a premise: the census prints `not_reachable: 13`, and no runtime reading is emitted by any committed instrument |
| V3-04 | process artifacts | Low | the untracked `tools/derive_requires.py` computes `REPO_ROOT = Path(__file__).parents[2]`, which is `/Users/jackson`, so every source path it builds is absent and it prints `base` for all 19 tasks — including the 14 whose trees import `matplotlib` | `uv run python -m tools.derive_requires --json` → 19 rows, `["base"]` in each; `pathlib.Path('tools/derive_requires.py').resolve().parents[2]` → `/Users/jackson` |
| V3-05 | documentation coherence | Low | three documents describe what `run --list` prints (`README.md` 105, `docs/reproducibility.md` 77, `CONTRIBUTING.md` 39) and all three describe a surface with no requirement column, because that is what the code prints | read at the line cited, not grepped |

**V3-01's measurement, because the remedy is only as good as this table.** The declaration cannot be derived
from the four-way split in a ledger entry; it has to come from each task's own import tree. Two probes were
run, and they disagree in a way worth recording:

1. **Import-time probe** — each task's module imported in a subprocess whose `sys.meta_path` raises
   `ModuleNotFoundError` for a named set of roots. Under `base` (all seven optional roots blocked) seven
   modules fail to import: `pricing_grid`, `mc_convergence`, `variance_reduction`, `portfolio_estimation_cost`,
   `stress_testing` on `matplotlib`; `var_backtesting`, `real_data_risk_study` on `scipy`.
2. **Execution probe** — Phase 0's own transcript (`build/v3-p0-surface.out`, gitignored) records **15**
   failures, eight of them `No module named 'matplotlib'`. The three extras beyond the import probe —
   `fourth_order_crossing_map`, `restrike_gamma_map`, `two_factor_error_bound` — import cleanly without
   matplotlib and fail later, from a plotting helper reached inside a function.

So an import-time-only reading under-declares by three tasks, and the derivation §5 asks for must walk the
whole tree rather than the import-time frontier. The measured union, root-by-root:

| extras | tasks |
|---|---|
| `plot` only | `pricing_grid`, `mc_convergence`, `variance_reduction`, `portfolio_estimation_cost`, `stress_testing`, `linearisation_error_bound`, `two_factor_error_bound`, `restrike_gamma_map`, `fourth_order_crossing_map`, `second_book_crossing_map`, `fifth_order_crossing_map`, `sixth_book_crossing_map` |
| `oracles` only | `pricing_vs_quantlib`, `monte_carlo_vs_analytic`, `path_dependent_vs_quantlib`, `optimisation_vs_oracles`, `real_data_risk_study` |
| `plot` and `oracles` | `var_backtesting` |
| `base` | `mc_speed` |

Fourteen tasks import matplotlib somewhere reachable; eight of them fail on it from a wheel and three of the
remaining six produce a figure of `not generated (matplotlib unavailable)` instead. That gap is the decision
the K6 contract change turns on, and it is recorded below rather than smoothed into the number.

**Decision, K6 — the widened `run --list` (recorded here because §5 calls it a decision, not a consequence).**
`requires` names the extras needed to reproduce a task's published artifact, not the minimum needed to exit 0.
A study whose figure degrades to a string when matplotlib is absent declares `plot`, because its committed
artifact carries a PNG that a bare run cannot reproduce; declaring `base` would make the list honest about
startability and dishonest about the artifact. The consequence is priced and accepted: a bare wheel will refuse
18 of 19 tasks instead of silently under-producing six of them, every refusal names the module and the install
line, and `--list` says which extra buys which task. The alternative — refusing nothing that would have limped
— was considered and rejected because the six would then keep writing artifacts that do not match the ones the
repository publishes.

**Two things this phase did not do, named so Phase 3 cannot inherit them silently.** The eight-lane read did
not touch the evidence chain beyond re-running the Phase 0 verifier reading, and it did not open the cost lane
past `pyproject.toml` (no dependency change is proposed, so the lane has no movement to price). `sixth_book_
crossing_map`'s `RuntimeError` is not a requirement defect and is not filed as one: it names the committed
sibling artifact it validates against, which is the acceptable failure shape of §15 #8, and K2 freezes that
path.

#### The liveness table at Phase 1

| # | law | precondition holds? | state |
|---|---|---|---|
| N1 | requirement truth | no — the declaration does not exist yet | ACTIVE, unexecuted; Phase 3 item 1 is its first run |
| N2 | advertised surface honesty | no — `run --list` prints no requirement | ACTIVE, unexecuted |
| N3 | lane contract | partly — the contract file does not exist; the `validate` gap is V3-02 | ACTIVE, unexecuted |
| N4 | no silence by count | yes — the census prints names, not totals | ACTIVE; `--check-ceilings` read at Phase 0 |
| N5 | declarations are checkable | no — V3-01 and V3-05 are both this shape | ACTIVE, unexecuted |
| N6 | runtime reachability | no — only the `ast` reading is committed | ACTIVE; V3-03 is its first run |
| N7 | plan equals log | yes — the plan rows are the three Phase 3 items | ACTIVE; audited at each close |
| N8 | no gate weakened | yes — the §7.1 suite is green at the tip | ACTIVE |
| N9 | plant liveness | yes — 183 plants declared, last sweep 183/183 per `REFACTOR_LEDGER.md` §9 | ACTIVE; re-run at Phase 5 on a clean tree |
| N10 | one re-run | yes — the evidence chain is frozen at 95 entries | ACTIVE; not run this series |
| N11 | facts precedence | yes — the leak list is a named exclusion in the collector | ACTIVE |
| N12 | baseline purity | yes — one vantage, one revision, one CI run read | ACTIVE |

#### Phase 2 — the approval this session runs under

The maintainer's instruction for this session is the handoff prompt that opened it, and its scope is quoted
rather than paraphrased: *"Execute **Phase 3 targeted fixes first** (three items), then proceed to Phases 4-5"*,
with Fix #1 = V2-24/V3-01 (`requires` derivation, widened `run --list`, declared-vs-actual guard, one plant),
Fix #2 = V2-29/V3-02 (the `validate` step and the CLI-surface guard), Fix #3 = V3-03 (the runtime reading).
Read against §9, that is a blanket approval for those three rows and nothing else: no push, release, PR or
comment is approved by it, and §0's one-scope-unit-per-session rule caps this session at the first of the
three. This entry is committed before any source file is touched, which is the order §0 requires.

**Owner per row, as §9 asks.** All three rows: this session, at the maintainer's direction. Priced locks
expected: K6 only (the widened list, with its own guard updated in the same commit), and K2 not at all —
`sixth_book_crossing_map`'s artifact path stays where it is.

---

### 2026-11-02, V3-01 fixed — the registry declares what each task needs, and a wheel that lacks it says so

**One finding, one commit.** V2-24 carried into V3 as V3-01: nineteen tasks advertised, four runnable from a
wheel, and fifteen failures naming no remedy. This commit adds the declaration, the widened `run --list` (K6's
priced contract change), the preemptive refusal, the guard that re-derives the declaration from each task's
import tree, one plant, and the three documents that described the old three-column list.

**What the declaration is, and what it is not.** `Task.requires` is a `frozenset` of names drawn from
`[project.optional-dependencies]`, and `EXTRA_MODULES` maps each extra to the modules it installs.
`requirement_label` prints `base` rather than a blank column, because the one column that exists to stop a
silent failure must not itself be able to look unmeasured. The semantic is *what reproduces the published
artifact*, not *what exits 0*: a study whose figure degrades to `not generated (matplotlib unavailable)` still
declares `plot`, because the committed artifact holds a PNG a bare run cannot produce. That decision was
priced in the Phase 1 entry and is unchanged here.

**The derivation, measured before it was written.** The corrected walker follows every `quantrisk.*` import
into the package at any nesting depth, and the two probes disagree in a way that mattered: `restrike_gamma_map`,
`fourth_order_crossing_map` and `two_factor_error_bound` import cleanly with matplotlib blocked and fail later,
so an import-time-only walker under-declares by three. The measured table, 19 rows:

| extras | count | tasks |
|---|---|---|
| `plot` only | 12 | `pricing_grid`, `mc_convergence`, `variance_reduction`, `portfolio_estimation_cost`, `linearisation_error_bound`, `two_factor_error_bound`, `stress_testing`, `restrike_gamma_map`, `fourth_order_crossing_map`, `second_book_crossing_map`, `fifth_order_crossing_map`, `sixth_book_crossing_map` |
| `oracles` only | 4 | `pricing_vs_quantlib`, `monte_carlo_vs_analytic`, `path_dependent_vs_quantlib`, `optimisation_vs_oracles` |
| `plot` and `oracles` | 2 | `var_backtesting`, `real_data_risk_study` |
| `base` | 1 | `mc_speed` |

**Correction to the Phase 1 entry's table.** That entry listed `real_data_risk_study` under `oracles` only.
The measurement above says `plot` as well: the task reaches matplotlib through a guarded figure call the first
walker did not follow, and the package's own `quantrisk.plotting` is where most of these studies meet it. The
Phase 1 table is left as written — superseded in date order — and this line is the supersession.

**The guard, and what makes it able to disagree.** `test_the_registry_declared_requirements_match_their_import_trees`
reads each task's module, follows `import`, `from … import …` and relative imports with the package anchor
computed from the file's own position, and compares the resulting extra set with the declaration in
**both** directions: an over-declaration would ask a reader to install what the task never touches, an
under-declaration is V2-24 itself. A third comparison keeps the mapping honest: any non-stdlib root the walk
reaches that is neither a base dependency from `pyproject.toml` nor named by an extra is refused, so a new
import cannot slip in unclassified. Both sides are printed for all nineteen tasks on every run.

**The installed-surface reading, taken on a wheel built from this tree and installed outside the checkout.**
Identity first, because the number means nothing without it: `quantrisk.__file__` =
`/private/tmp/v3-01-venv/lib/python3.12/site-packages/quantrisk/__init__.py`, `sys.prefix` =
`/private/tmp/v3-01-venv`, checkout path absent, version `1.9.0`. Then every id `run --list` printed, from
`/tmp/v3-01-neutral`:

- **1 ran**: `mc_speed`, the one task declaring `base`, writing
  `benchmarks/performance/results/monte_carlo_speed.json` and exiting 0.
- **18 refused**, each naming its declared extras, the absent modules and the install line, each exiting 1:
  `needs the plot extra: No module named 'matplotlib'` / `install it with: pip install 'quantrisk[plot]'`,
  and for the two-extra tasks `needs the oracles, plot extras: …` / `pip install 'quantrisk[oracles,plot]'`.
- **No refusal left anything behind**: `out-plot`, `out-or` and the eighteen `census/` roots do not exist
  after the sweep; only the successful run's directory does.

That is N2's first half measured in full — every advertised id either runs or names the extra it needs — and
its second half is *not* claimed here: no environment with `plot` and `oracles` installed was built in this
session, so "the declaration is sufficient to run each task" is unmeasured and belongs to the Phase 3
acceptance or the runner's own `benchmark-suite` job, which already installs `oracles` and executes all
nineteen.

**The cascade this one case cost, paid in the same commit.** Adding a pytest case moves the counted pair and
the plant count, exactly as §10 warns. Measured after the guard landed: 559 → **560** collected, the
oracle-free probe 490 → **491**, the plant inventory 183 → **184**. That moved twenty-two quotations across
`docs/reproducibility.md`, `docs/interview_defense.md`, `docs/limitations.md` and `paper/technical_report.tex`,
re-keyed the three claim-inventory gold lists in `test_artifact_metadata.py`, and invalidated five existing
plant anchors that pointed at the moved strings (`# 490 tests collected offline`, `and 559 pytest tests with
the validation`, `# 183/183 planted defects rejected`, `oracles installed, 490 collected without them`,
`# 559 pytest tests with the oracles extra here`) — all five re-keyed, and the anchor-uniqueness guard is what
caught them. Editing the `.tex` also broke the report's PDF binding, so `tools.build_report` re-rendered it:
6 sources, 1,005,924 bytes, `{"bundle": "b7f5ccc598b0", "pdf": "f06c296f6b6c"}`, and the three guards that
compare the PDF with its source are green again.

**Two instruments were retired rather than kept.** `tools/derive_requires.py` — the untracked script from the
previous session, V3-04 — is deleted: `REPO_ROOT = Path(__file__).parents[2]` resolved to `/Users/jackson`, so
it printed `base` for all nineteen tasks including the twelve that import matplotlib. A second measurement tool
would also have violated §4.1, which asks for one collector; the derivation lives in the guard, where it can
fail. `tools/verify_installed_surface`'s defaults moved with the contract: the study probe is now `mc_speed`
(the only `base` task, and the only one a bare wheel can still run) and the refusal probe is `pricing_grid`
(whose refusal is the new message rather than an accident of a missing fixture).

**Environment caveat, marked rather than smoothed.** The full suite printed **559 passed, 1 failed** in 221 s.
The failure is `test_a_restored_plant_cannot_be_read_back_from_a_stale_bytecode_cache`, and it is this
sandbox: `uv run python -c "import sys; print(sys.dont_write_bytecode)"` prints `True` here, so the test's own
control — a first import that must leave a `.pyc` beside the module — cannot hold. Nothing in this commit
touches bytecode handling; the lane is **unverified on this machine**, not green, and CI is where it gets its
reading. Everything else in the suite, `--check-ceilings` (184 declared plants, 19 registry sources, 8 keys at
their ceiling, 2 declared SKIP), `ruff`, `ruff format` (230 files) and `mypy` (74 files) is green.

**Not done, and why.** Fix #2 (V3-02, the `validate` step and the CLI-surface guard) and Fix #3 (V3-03, the
runtime-reachability reading) are not started: §0's one-scope-unit rule and the size of this one's cascade put
them past this session's boundary. The `oracles`-and-`plot` installed census is unmeasured, as above. No push
has happened: §14 makes a push an outward action needing per-case approval, and the handoff's "push after each
commit" is a plan, not that approval.

**The sweep, run after the commit on a clean tree** (N9: a plant cannot fire while its target carries
uncommitted edits). `--only registry-declares-a-study-that-needs-no-plot` printed `caught` and the summary
`1/1 planted defects were rejected by their guard.` The five re-keyed anchors were then run the same way, by
id, and printed `5/5 planted defects were rejected by their guard.` — so the re-key preserved what it touched
rather than silencing it, which is the failure mode a moved anchor would otherwise hide. The declaration count
in the Phase 1 liveness table (183) is now 184; the row is left as the reading of its own date.

**One gap this commit leaves open, recorded rather than papered over.** The refusal path itself has no pytest
guard. Its *input* is guarded — the declaration cannot drift from the import tree — but nothing in the suite
would redden if `command_run` stopped calling `unsatisfied_requirements`, because the only instrument that
executes the refusal against a real absence is `tools/verify_installed_surface --refusal pricing_grid`, and
that gate is declared dev-only (its ceiling key SKIPs on the runner by design). Closing it costs a new pytest
case, which costs the counted pair again — 560 → 561, three gold lists, five or six plant anchors, the report
PDF — for a mechanism this session measured on eighteen real tasks. Deferred deliberately, priced, and left
for the session that takes Fix #2, which already pays a count cascade for its own guard.

---

### 2026-11-02, V3-02 fixed — `validate` gets a runner home, and the guard compares the parser's whole surface

**The finding.** V2-29's "why it matters" cell said a build that breaks `validate` ships green. The Phase 0
reading narrowed it and this commit closes the narrowed form: the function was executed in process by a
digest-pinned test, and the *entry point* — `[project.scripts]`, the installed distribution, the packaged
environment — was executed by nothing. `.github/workflows/ci.yml` gains one step after `pytest`, in the job
that already installed the package from this tree:

```
- name: Validate installed CLI
  run: uv run quantrisk validate
```

**The guard, extended rather than added.** A new pytest case would have cost the counted pair again — 560 to
561, three gold lists, six plant anchors, the report PDF — for a reading that belongs inside a guard already
reading this workflow. `test_the_ci_lane_that_runs_the_guards_fetches_what_they_read` gained a clause that
takes the declared set from `quantrisk.cli.subcommands()` (the parser, not a second list), scrapes the
executed set from every `run:` line, and compares them in both directions. Its print on this tree:

```
cli declares ['benchmark', 'demo', 'run', 'validate']; the workflow executes ['run', 'validate']
```

`benchmark` and `demo` are declared in-process-only **with their reasons in the guard**, and the same clause
refuses a declaration that outlives its command, or one that stays behind after a step starts running it.

**The deflection, run before the plant was written.** Replacing the new step's command with
`uv run quantrisk --version` and re-running the guard printed:

```
the parser declares ['benchmark', 'demo', 'run', 'validate'] and the workflow executes ['run'];
declared, expected to run and absent: ['validate']; executed but declared in-process-only: []
```

The file was restored from a copy, and `git diff --stat` confirms the step is the only change on that path.

**The cascade.** Adding a plant moves the inventory 184 → **185**, which moves
`docs/interview_defense.md`'s `# 184/184 planted defects rejected` and re-keys the plant that anchors on that
line. No test-count movement: the guard was extended, not added, so the pair stays at **560/491**. The plant
`ci-lane-stops-validating-the-installed-cli` replaces the step's command with `--version`.

**What this does not prove yet.** The step has executed on no runner at the moment this entry is written; the
commit that carries it is not pushed. Until a run reads it, the lane's own verdict is unknown, and this entry
claims only what the local guard printed.

**The sweep, on a clean tree after that commit.** `--only ci-lane-stops-validating-the-installed-cli`
printed `caught` and `1/1 planted defects were rejected by their guard.`; the re-keyed
`docs-command-comment-counts-superseded-plants` printed the same. Both claims therefore have a guard that
fails without them, and the anchor this commit moved still points at a live defect.

---

### 2026-11-02, the two runs that read it — what each commit's verdict actually is

**Run `41453407921`, event `push`, tip `7007f19`, `completed success`.** Four jobs, all `success`:
`Format and static checks`; `Configure, build, C++ tests, Python tests`; `macOS native C++ and Python
parity`; `Benchmark suite against live oracles`. Three readings from it matter here:

- **The pytest lane printed `490 passed, 5 skipped in 231.94s`.** That is 495 nodes, and the arithmetic now
  closes with the moved numbers: the offline probe collects **491**, the four oracle-gated modules collapse
  into four records, and the fifth skip is the `latexmk` guard the Ubuntu runner cannot satisfy. Before this
  session the same line read `489 passed, 5 skipped` against a probe of 490; the extra case moved both sides.
- **The bytecode-cache plant passed on the runner.** It is the test this session's machine cannot run —
  `sys.dont_write_bytecode` is `True` in that sandbox — and the runner's pass is the confirmation that the
  local failure was the environment's and not the commit's. N12's rule applied: the lane was marked
  unverified here and green only where it ran.
- **The benchmark suite printed `19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped`** in
  a job that installs `--extra oracles` and carries `matplotlib` from the dev group. That is N2's second
  half, which the V3-01 entry explicitly did not claim: with both extras present, every one of the nineteen
  tasks starts and finishes, so the declaration names what is *missing* rather than excusing what is broken.

**Run `41459024242`, event `push`, tip `0e8b900`, `completed success`.** Same four jobs green, and the new
step executed: `Run uv run quantrisk validate` → `7/7 checks passed`. So V3-02's claim is now a reading about
a runner rather than about a guard: the console script that `[project.scripts]` publishes, resolved in the
environment the job installed from this tree, runs the identities and passes.

**What no run covers, stated rather than glossed.** `cancel-in-progress` means a push produces one run on its
tip, so `87207d4`, `6696059`, `1501bde` have no verdict of their own — they are ancestors of a green tip, not
individually verified — and `999af8d` shares `0e8b900`'s run. That is the V2 close-out's "cancelled run named
as cancelled" rule applied forward: a commit carried by a green tip inherits the tip's evidence and nothing
more.

**Where the liveness table stands after these runs.** N1 and N2 are satisfied by readings (the guard's
two-sided output, the bare-wheel census, the 19/19 suite); N3 is satisfied for the `validate` row and remains
open for the contract file §5 describes, which V3 has not written; N6, N7, N8, N9, N11, N12 keep the status
their Phase 1 rows recorded, with N9's plant count now 185. N10 — the one re-run — remains unexecuted in this
series, which is correct: no evidence category has moved.

---

### 2026-11-02, V3-03 fixed — the census keeps its verdict and gains two runtime readers

**The finding, restated as what it is.** `inspect_corpus` classifies a file as `not_reachable` when it
holds no `sys.path` bootstrap, no by-path load and no `quantrisk` import. That is a statement about static
import edges, and it was being read as a statement about liveness: thirteen files, every one of them reached
by something at runtime, and the thirteenth of them the collector that writes the census. The class name is
kept — renaming it would hide that the parser still holds one view — and a second reading is put beside it.

**What shipped.**

- `tools/inventory_orphan_code.py` gains `runtime_reachability`, built from two instruments that are named in
  the snapshot with their own controls: `import_probe` imports every dead file by the name a consumer would
  use, in one child interpreter, with `quantrisk` itself as the control; `pytest_collection` runs
  `pytest --collect-only -q -p no:cacheprovider` once and maps node ids back to files. The reading returns
  `ast_dead`, `import_reachable`, `pytest_collected`, `reached_by_neither`, `ast_dead_but_runtime_reaches`,
  both instruments' commands and both controls.
- `tools/refactor_ceilings.json` gains `runtime_reachability_gap`: the **residual** — files dead by the parser
  *and* by both runtime instruments — with `max: 0` and no `may_be_unmeasured`. A broken instrument yields no
  measurement, and this row does not excuse that, so the gate fails rather than skipping. The other
  direction, `ast_dead_but_runtime_reaches`, is printed and deliberately not counted: it is the finding this
  key exists for, not a budget to stay under. The file now holds eleven keys.
- `by_path_load_sites`' note says why a dynamic load is invisible to this census by construction, which is the
  sentence whose absence let this count reaching zero read as "those thirteen files are dead".
- The guard is a clause inside `test_the_ci_lane_that_runs_the_guards_fetches_what_they_read`, not a new case:
  the counted pair stays at **560/491** and the plant count pays the only movement (185 → **186**). The clause
  asserts the controls first — collection reached something, the probe's control import succeeded, the probe
  reached something — and the residual second, because an instrument that cannot say it measured anything is
  the failure mode, not a zero.

**The reading on this tree, printed by the census itself.**

```
orphan_inventory         {"installed_import": 33, "not_reachable": 13}
runtime_reachability     {"ast_dead": 13, "available": true, "import_reachable": 13,
                          "pytest_collected": 6, "reached_by_neither": 0}
```

Six of the thirteen are test modules pytest collects; `tests/python/conftest.py` is reached by import and
never by a node id, which is why the collection count is 6 and not 7. The six tools are reached by import —
including `tools/inventory_orphan_code.py` itself, whose only execution path is `-m tools.inventory_orphan_code`
and which therefore had no static edge for the census to see.

**Why two instruments and not one.** Import-by-name alone is unsound in the direction that matters: Phase 0
measured `test_second_book_crossing_map.py` failing with `ModuleNotFoundError: No module named
'test_two_factor_bound'`, because it reaches a sibling test by bare name and resolves only under pytest's path
insertion; the probe now inserts `tests/python` and reaches it, but the class of failure is real and silent.
Collection alone is blind to everything pytest does not collect. The union is the reading, and the word it
supports is *reachable*, not *executed* — nothing here proves a tool ran, only that nothing in the repository
is dead by every available reading.

**Two deflections, run before the plant was written.** Replacing the collection command with
`pytest --version` (a command that prints no node ids) reddened the guard with
`["pytest's collection reached no file at all"]`. Adding a tracked `docs/unreached_probe.py` with no importer
reddened it with `these files are called dead by the census and reached by neither runtime instrument, so a
deletion decision would be acting on one reading: ['docs/unreached_probe.py']`. Both were reverted; `git
status` after each showed only the three files this finding touches.

**Cost, measured.** The collector runs in 5.5 s end to end, up from roughly 1.5 s: one child interpreter and
one collect-only pass. `--check-ceilings` prints `ok runtime_reachability_gap: 0 against a ceiling of 0 due V3
Phase 3 item 3` beside the ten existing rows. No evidence category moved, so N10's single re-run stays
unexecuted and stays correct.

**Not done, and why.** No file was deleted: N6 does not say the thirteen are dead, it says a deletion now
needs this reading first, and no deletion is proposed. The `not_reachable` class is not renamed for the reason
above. And the reading is not a liveness claim — a tool that nothing invokes still counts as reachable here,
which is why `tools/generate_shim_stubs.py` remains a Phase 4 question rather than being closed by a zero.

**The sweep, on a clean tree after that commit.** `--only reachability-reading-drops-one-of-its-instruments`
printed `caught` and `1/1 planted defects were rejected by their guard.` — so the clause's residual assertion
has a defect that fires it, not merely a deflection that was seen once. The re-keyed
`docs-command-comment-counts-superseded-plants` printed `caught` as well, and the inventory now declares 186
plants. N6 moves from "ACTIVE, unexecuted" to satisfied by a reading: both instruments exist, the difference is
printed by name, and the ceilings gate refuses a residual above zero.
