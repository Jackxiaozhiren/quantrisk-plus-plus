# Reproducibility

This document states what "reproducible" means in this repository, how to check it, and
where it breaks. The third part is the point of writing it down at all: a reproducibility
claim with no stated failure mode is a marketing claim.

## The contract

Three things are guaranteed.

**1. Every published number comes from a script.** No figure in `README.md`,
`docs/validation_matrix.md`, `docs/model_cards/` or `paper/technical_report.tex` was typed
from memory. Each one is written by a script under `benchmarks/`, `experiments/` or
`scripts/`, into an artifact, and the document cites the artifact. `PROJECT_SPEC.md` §4
forbids the alternative, and the rule has already earned its keep twice: a README line
claiming covariance agreement to 2e-15 was wrong by six orders of magnitude because
scikit-learn's `EmpiricalCovariance` divides by `T`, and a benchmark that appeared to agree
with PyPortfolioOpt to 5e-6 was measuring that library's five-decimal weight rounding.

**2. Determinism, checked by byte-comparison where the claim is about a number.** Given the
same build and the same seed, every *result* in every artifact is identical across runs. This
is asserted in tests, not assumed: the RNG contract is pinned in
`tests/python/test_rng_contract.cpp`, seeded Monte Carlo output is compared to itself, and the
C++ core is additionally checked against a different generator so that "reproducible" cannot
mean "reproducible only for the one stream we tested".

Measured, not hoped for: re-running the entire suite and diffing every numeric leaf of the
new artifacts against the committed ones returns **zero differences** in
`pricing_vs_quantlib.json`, `monte_carlo_convergence/summary.json`,
`variance_reduction/summary.json` and every other result file. What does move is recorded
below, and it is only ever wall-clock.

**3. The evidence is frozen and verifiable.** `evidence/manifest.json` records a SHA-256 for
every artifact, the command that generated it, the repository revision, whether the working
tree was dirty at the time, and the full build and package environment.

```bash
uv run python scripts/build_evidence_manifest.py    # write the manifest
uv run python scripts/verify_evidence_manifest.py   # check the tree against it
```

`verify` reports `OK`, `CHANGED`, `MISSING` and unlisted-but-present separately and exits
non-zero on any of the last three. Conflating them would let a *deleted* artifact pass a
check that was only ever asking "is everything listed still correct?".

## How to reproduce from a fresh clone

```bash
git clone <repository> && cd QuantRisk++
uv sync --extra oracles          # interpreter 3.12, deps, and the validation oracles
uv pip install -e .              # builds the C++ core and the pybind11 module
uv run pytest -q                 # the full Python suite
uv run cmake --preset dev && uv run cmake --build --preset dev
uv run ctest --preset dev        # 190 C++ tests, 546,943 assertions
uv run python scripts/run_benchmark_suite.py --require-all   # all 11 members, ~60 s
uv run quantrisk validate        # 7 identity checks against the build you just made
```

Two things in that sequence are load-bearing and easy to get wrong.

Configure through `uv run`, not a bare `cmake --preset dev`. With no active virtualenv,
CMake finds system Python and builds the extension against an interpreter the tests do not
use — silently, and successfully.

`--require-all` on the suite is what stops the run meaning anything. Without the `oracles`
extra installed, four of the eleven members report `skipped` and the suite still exits 0,
because skipping is the honest status for a missing dependency. A CI job that reported green
in that state would be claiming a measurement it did not make. The flag turns that state into
a failure.

## What is *not* reproducible

**Timings, and only timings.** Three artifacts carry wall-clock columns and therefore change on
every run: `benchmarks/performance/results/monte_carlo_speed.json` entirely, and the
`mean_runtime_seconds` / `seconds_per_path` columns of
`experiments/variance_reduction/results/variance_by_method.csv` and
`experiments/monte_carlo_convergence/results/convergence.csv`. Four dated runs of the speed
benchmark returned 7.99×, 8.07×, 8.20× and 8.37× against a pure Python loop (5% spread) and
0.42, 0.42, 0.43 and 0.48 against vectorised NumPy (14% spread, because the NumPy baseline
itself moved from 110M to 95M paths/s). Documents quote those as ranges for that reason. On
different hardware expect different numbers; the *ordering* — C++ beats an interpreted loop by
roughly an order of magnitude, and loses to vectorised NumPy for terminal-only payoffs — is the
reproducible part, and it held on every run.

**Metadata.** Every artifact records its own `generated_at_utc` and the running `git_commit`, so
a re-run always produces a `CHANGED` entry in the manifest even when the mathematics is
bit-identical. That is the check working: it says "this file was rewritten at this time from
this revision", which is a different claim from "the result changed", and the two are not
conflated anywhere in this repository.

**Compiler and platform.** The core is C++20 and builds with the toolchain above. Nothing
here has been compiled by CI on a runner yet — the `benchmark-suite` job in
`.github/workflows/ci.yml` is new and unproven on GitHub-hosted hardware, which is recorded
as open technical debt rather than assumed away. Floating-point results are reproducible on a
given platform; across platforms, the last one or two digits of an iterative solve may differ,
which is why the oracle tolerances in `docs/validation_matrix.md` have margin rather than
sitting on the measured value.

**Network data.** `data/fixtures/` holds real, committed SEC EDGAR, FRED and CFTC responses,
so the offline path is deterministic. Anything fetched live is not: EDGAR and FRED revise
their series, and ALFRED vintages exist precisely because the revision is the interesting
part. A fixture records its `retrieved_at_utc` and source URL, and
`tests/python/test_data_layer_offline.py` blocks `socket.socket` to prove no test reaches the
network — the guarantee is executed, not asserted in a comment.

**Random streams outside the core.** The NumPy and pure-Python baselines in the performance
benchmark use their own generators (`numpy.random.default_rng`, `random.Random.gauss`) with
different streams from the C++ `Rng`. That is deliberate — the comparison is cost per path,
not equality of estimates, and `docs/limitations.md` #21 says so — but it means those
baselines' *prices* are not the core's prices to the last digit.

## The artifact chain

```
script (benchmarks/…/run.py, experiments/…/run.py)
  └─ writes results/*.json  ← records command, environment, git commit, UTC time
       └─ hashed into evidence/manifest.json with its generating command
            └─ cited by README.md / docs/validation_matrix.md / paper/technical_report.tex
```

Each link names the one below it. The manifest recovers the command *from the artifact*
rather than from a list maintained beside it, because a list maintained by hand is a list
that drifts. For the committed data fixtures, where the correct provenance is a source URL
and a retrieval time rather than a command, the manifest reads those from the
`.provenance.json` sidecar instead of warning that no command was recorded.

`scripts/run_benchmark_suite.py` closes the loop one step further: it reads headline numbers
out of the artifacts by key path and aborts if a path has moved, so renaming a field in a
benchmark breaks the suite instead of silently dropping a row from the summary. The figure
`benchmarks/suite/results/validation_envelope.png` is drawn from those same extracted
metrics, not from a second pass over the CSVs, so the plot cannot disagree with the table
printed beside it.

## Checking this document

```bash
uv run python scripts/verify_evidence_manifest.py
uv run pytest tests/python/test_artifact_metadata.py -q   # the suite's own bindings
```

If either fails, the numbers in the README are no longer traceable, and the correct response
is to re-run the suite and rebuild the manifest — not to edit the document to match.
