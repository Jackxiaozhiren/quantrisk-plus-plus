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
