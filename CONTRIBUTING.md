# Contributing

Practical notes for working in this repository. The rules below are not style preferences: every one
of them is enforced by a test, a CI job, or a command that fails loudly, because this project's product
is the *traceability* of its numbers rather than the number of its features.

If you are looking for what the project claims and where each claim is checked, read
[`docs/validation_matrix.md`](docs/validation_matrix.md). For the architecture and the layer
boundaries, [`docs/architecture.md`](docs/architecture.md). For the derivations behind specific
results, [`docs/analysis/`](docs/analysis/).

## 1. Environment

```bash
uv sync --extra oracles          # interpreter, dependencies, and the correctness oracles
uv pip install -e . --no-cache   # builds the C++ core and the pybind11 module
```

`--no-cache` is not optional paranoia. A plain `uv pip install -e .` can be served from the wheel
cache in milliseconds and install a binary built *before* your edit, whose only symptom is that a new
binding looks unregistered. Build inside the environment you will test in: configure with
`uv run cmake --preset dev`, not a bare `cmake`, or the extension is built against a different
interpreter. Both traps and their symptoms are in
[`docs/reproducibility.md`](docs/reproducibility.md).

## 2. Verifying a change

Run the gates in this order, and quote each tool's own output rather than summarising it:

```bash
uv run ruff check .                      # lint
uv run ruff format --check .             # format
uv run mypy python/quantrisk             # types (the scope CI enforces)
uv run cmake --build --preset dev
uv run ctest --preset dev                # C++ suite
uv run pytest tests/python -q            # Python suite
uv run python scripts/run_benchmark_suite.py --require-all
uv run quantrisk validate                # seven identities against the build you just made
uv run python scripts/verify_evidence_manifest.py
```

`--require-all` on the suite is what makes the run mean something: without the `oracles` extra some
members *skip*, and a green that skipped is a claim about a measurement that was not made.

Local green is not evidence about the runner. CI is where a change is verified, and a job that passes
here and fails there is the normal case on a project whose numerics depend on `libm`
([`docs/limitations.md`](docs/limitations.md) items 64, 71–77 are that history).

## 3. Regenerating evidence

`experiments/`, `benchmarks/` and `benchmarks/suite/` outputs are **generated**, committed, and hashed.

1. Change the script, then re-run it — never hand-edit a result file, a CSV row or a figure.
2. Re-run the suite so the aggregates match the members.
3. Re-freeze the manifest last: `uv run python scripts/build_evidence_manifest.py`.

Each artifact records the commit and the uncommitted paths it was produced from, so a frozen tree that
lies about its own provenance is visible. `verify_evidence_manifest.py` distinguishes
`OK / VOLATILE / CHANGED / MISSING / unlisted`; only `CHANGED` means a result moved.

Raising the library version invalidates every committed artifact, because each one records
`environment.quantrisk_version`. Bump it deliberately, in one commit, and re-freeze after.

## 4. Rules this repository enforces, not suggests

- **Own implementation.** Black–Scholes, the lattice, Monte Carlo, the Greeks, variance reduction,
  VaR/ES, the backtests, covariance estimation and the optimizers are implemented here.
  QuantLib, PyPortfolioOpt, SciPy and cvxpy are oracles: they check us, they never compute a shipped
  result, and no expected value in a test is a value copied out of them.
- **A number in prose needs an owner in the artifact.** If a figure appears in a README, model card,
  analysis note or phase report, a test re-formats it from the artifact and fails if they diverge
  (`test_every_figure_the_finding_and_the_note_quote_is_in_the_artifact`,
  `test_every_figure_the_note_quotes_is_owned_by_the_artifact`). Ratios must name their denominator
  in the field name — see limitation #76 for why a correct digit in a wrong sentence is still wrong.
- **Every test must be shown capable of failing.** New assertions get a negative control: a mutation
  that must be caught and a benign change that must not be. A green test nobody has falsified is
  decoration (finding 25).
- **Never go green by weakening a check.** No lowering a tolerance, no deleting a failing test, no
  `# noqa`, no adding an exclude to a linter — including in scratch tooling. Fix the thing or record
  the failure; failed experiments are published, not dropped.
- **Nothing is claimed that has not been measured.** No invented benchmarks, speedups, coverage,
  Sharpe ratios or conclusions; no "production ready". An outcome is written down only after the tool
  that produced it has reported it — including CI runs, deployments and release assets.
- **Determinism is a contract.** Same seed and same platform family means bit-identical output. The
  tests assert exact equality for that, and documented relative slack across platforms, and they
  distinguish the two: a fitted statistic estimated from a cancellation residue may have no
  cross-platform *value* to reproduce at all (items 73–75).
- **$0.** Free tools and free data only. If something you want costs money, find the free alternative;
  do not propose the paid one.
- **Look-ahead bias is a defect, not a simplification.** Any series used to make a claim must have been
  knowable at the decision time it is applied to.

## 5. Committing

Conventional Commits, subject line in the imperative, and the body states **why** — what was wrong,
what was measured, and what the evidence says. A commit that records a mistake is worth more than one
that hides it; several of this repository's best guards exist because a commit message claimed
something its tree did not do, and the runner proved it (findings 28–32).

Write the docs in English so the repository reads as one artifact; keep the code comments in English
for the same reason.

## 6. Where the boundaries are

`docs/limitations.md` is the complete list of what is *not* claimed — read it before adding a feature,
because several entries exist precisely to stop a future contributor from "finishing" something that was
deliberately left open. `docs/validation_matrix.md` says what each component is validated against and
at which level. Frozen public surfaces (`Greeks`, the pybind11 module's shape, the CLI's three
subcommands) are listed in `docs/project_scope.md`; extending them means a new type or a new function,
not a new field.
