# V3_LEDGER.md — the cross-session state of the V3 series

Companion to `V3_PROMPT.md`. V2's state lives in `REFACTOR_LEDGER.md` and is not amended here. Every session
working V3 writes its baseline capture, findings and liveness table in this file and commits this file before
touching a source file (`V3_PROMPT.md` §0).

---

### 2026-10-26, opening — the prompt was written from evidence, and no V3 phase has run yet

`V3_PROMPT.md` exists. Nothing else in this series does: Phase 0 has not been run, no premises have been
re-derived under V3's own instruments, and no finding is registered. This entry records what the prompt's
claims were built on, so the first V3 session can check them rather than inherit them.

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
