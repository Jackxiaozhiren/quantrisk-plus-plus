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

`verify` reports `OK`, `VOLATILE`, `CHANGED`, `MISSING` and unlisted-but-present separately, and
exits non-zero on the last three. Each class answers a different question:

| Verdict | Question it answers |
|---|---|
| OK | are the bytes exactly what was frozen? |
| VOLATILE | was the file re-run, with every result field unchanged? |
| CHANGED | did a **number** move? |
| MISSING | did evidence disappear? |
| unlisted | does the manifest simply describe an older world? |

The VOLATILE/CHANGED split is what makes the tool usable rather than merely strict. A manifest
of byte hashes reports CHANGED on every re-run, which trains the reader to ignore it; and
collapsing the two would let a real regression hide among the noise of a legitimate
reproduction. `content_sha256` is therefore a second hash over the artifact with run metadata
(`generated_at_utc`, `git_commit`, `environment`, nested digests) and wall-clock CSV columns
removed, while result fields — including seeded Monte Carlo prices in the timing benchmark —
stay under it. `--strict` promotes VOLATILE back to a failure for when the evidence is meant to
be byte-frozen rather than reproducible.

The volatile set is a judgement, so it is a tested one: `test_content_digest_ignores_run_
metadata_but_not_results` and its CSV counterpart assert **both** directions, because a filter
that strips too eagerly would pass the re-run test and silently rubber-stamp a changed number.

## How to reproduce from a fresh clone

```bash
git clone https://github.com/Jackxiaozhiren/quantrisk-plus-plus && cd quantrisk-plus-plus
uv sync --extra oracles          # interpreter 3.12, deps, and the validation oracles
uv pip install -e .              # builds the C++ core and the pybind11 module
uv run pytest -q                 # 496 pytest tests with the `oracles` extra here — the count is not one number, see below
uv run cmake --preset dev && uv run cmake --build --preset dev
uv run ctest --preset dev        # 204 C++ tests, 548,368 assertions
uv run python scripts/run_benchmark_suite.py --require-all   # all 19 members
uv run quantrisk validate        # 7 identity checks against the build you just made
```

Three things in that sequence are load-bearing and easy to get wrong.

Configure through `uv run`, not a bare `cmake --preset dev`. With no active virtualenv,
CMake finds system Python and builds the extension against an interpreter the tests do not
use — silently, and successfully. This bites on a *re*configure too, not only a first one: after
`rm -rf build/dev` outside the venv the tree builds a `cpython-314` module while `.venv` is 3.12,
every import still works because the installed copy is separate, and the C++ you just changed is
not the C++ the tests are running.

**`uv pip install -e .` can be served from uv's wheel cache, and then it installs a stale
extension.** An editable reinstall after editing `bindings/python_bindings.cpp` completed in 13 ms,
`import quantrisk` still worked, and the new functions were simply absent — the wheel had been
built before the edit and cached. `--no-cache` (or `--refresh`) is what makes an editable reinstall
mean it. The symptom is not an error but a missing attribute, so it reads as "my binding was never
registered" rather than "I am importing an older build".

**Raising the library version invalidates committed artifacts, not just the package metadata.**
Every experiment records `environment.quantrisk_version`, and
`test_the_study_uses_no_oracle_for_its_risk_numbers` asserts that the committed record equals the
imported library. So a version bump is: bump `pyproject.toml`, `CMakeLists.txt` and `CITATION.cff`,
run `uv lock` (the lockfile carries the project version too), rebuild, reinstall, re-run the whole
suite with `--require-all`, then re-freeze `evidence/manifest.json` — in that order, because the
manifest records the commit and the artifacts record the version.

`--require-all` on the suite is what stops the run meaning anything. Without the `oracles`
extra installed, six of the nineteen members report `skipped` and the suite still exits 0,
because skipping is the honest status for a missing dependency. A CI job that reported green
in that state would be claiming a measurement it did not make. The flag turns that state into
a failure.

**The pytest count depends on which extras you installed, and a document that prints one number
without saying which is wrong.** The sequence above yields **496 pytest tests with the `oracles`
extra** installed. Run the same tree after a plain `uv sync` — which installs the `dev` group, now including `sympy`, but no `oracles` extra — and the same
tree collects 427 tests without it, the four oracle-gated modules dropping out at import. The
figure for this revision comes from `scripts/measure_offline_collection.py`, which makes the
`oracles`-only packages unimportable in a child interpreter and collects there -- 427 now against 496
with the oracles installed. That is a second *measurement*, not the subtraction #63 forbids, and it is
guarded: `test_the_offline_test_count_is_measurable_before_the_runner` refuses the probe unless the
gated modules skip rather than error, so the number it publishes is the runner's shape and not merely a
local one. The probe has reproduced the runner's own reading at each revision it has been compared with. Passed plus skipped exceeds collected by four in both cases, because the
four module-level skips are records reported *in addition to* the items that ran -- which is why
`docs/limitations.md` #63 forbids deriving either figure from the other.
Both figures are read off the machine that produces them, and the difference of 69 is four modules that gate on
a module-level `pytest.importorskip` (for `sklearn`, `QuantLib` twice and `pypfopt`). 69 oracle
comparison cases go unattempted there, and nothing is broken when they do — what would be broken is
quoting either figure as "the" test count. At `v1.0.0` the pair was 330 and 261-passed-4-skipped.

Both numbers are guarded now.
`test_the_documents_that_count_python_tests_count_the_ones_that_exist` re-collects the suite in a
subprocess, asks whether the optional oracle packages are importable, and checks the figure that
belongs to *that* environment — so the runner validates its own 284 instead of being asked to agree
with a laptop. The first version of that guard asserted only the local number and failed on CI,
which is the same class of error as the one it was written to prevent. The C++ side has no such split: 204 tests under
CTest either way, because the C++ suite has no optional dependencies.

## What is *not* reproducible
**The PDF of the technical report is built by hand, and CI does not check it.** `paper/technical_report.pdf`
is committed as a release asset because a reviewer should not have to install a TeX distribution to read
the work, and it is regenerated with `latexmk -pdf technical_report.tex` in `paper/`. Nothing on the
runner verifies that the committed PDF matches the committed `.tex`: doing so needs a PDF text extractor,
which is not a project dependency, and installing one to satisfy a documentation check would be the wrong
trade. The consequence is real and happened once during Phase 11 — a failed `latexmk` invocation left a
PDF asserting the old limitations count for one commit — so the rule the phase adopted is that the PDF is
rebuilt in the same commit that changes any number the report quotes. The `.tex` itself is the source of
truth, and every figure inside it is a reference to an artifact path, not a retyped value.


**Timings, and only timings.** Three artifacts carry wall-clock columns and therefore change on
every run: `benchmarks/performance/results/monte_carlo_speed.json` entirely, and the
`mean_runtime_seconds` / `seconds_per_path` columns of
`experiments/variance_reduction/results/variance_by_method.csv` and
`experiments/monte_carlo_convergence/results/convergence.csv`. The speed benchmark has been
re-frozen twenty-one times, and the ratios of those twenty-one committed files are the honest measure of
how much these digits mean: `7.77×`–`8.88×` against a pure Python loop (14.2% spread) and
`0.42×`–`0.51×` against vectorised NumPy (20.8% spread), because the NumPy baseline itself ranged
from 110M to 46M paths/s. Any document quoting a single one of those ratios is quoting one dated
run, which is why the claims are written as ranges and why the point figures in `README.md` and
`docs/interview_defense.md` are checked against the artifact on disk. Recompute the range with:

```bash
git log --format=%H -- benchmarks/performance/results/monte_carlo_speed.json |
  while read -r sha; do
    git show "$sha:benchmarks/performance/results/monte_carlo_speed.json" |
      python3 -c 'import json,sys; p=json.load(sys.stdin); print("%.3f %.3f" % (p["speedup_vs_pure_python"], p["speedup_vs_numpy"]))'
  done
```

On different hardware expect different numbers; the *ordering* — C++ beats an interpreted loop by
roughly an order of magnitude, and loses to vectorised NumPy for terminal-only payoffs — is the
reproducible part, and it held on every run. One further observation, recorded here rather than in
a README because no artifact keeps it: a suite re-run taken on this machine while another process
held a core read 12% below the C++/Python ratio of the quiet re-run that follows it, and
`var_backtesting` took 103 s instead of 25 s in the same window. The same thing happened on
2026-10-08 and much larger: a full-suite run that contended with a second concurrent run of itself
wrote `4.01×` against pure Python and `0.36×` against NumPy — both outside the committed bands
above, which is why that artifact was restored rather than committed. Two clean idle re-runs of the
same script four minutes apart then wrote `8.38×` / `0.566×` and `8.88×` / `0.460×`, and the second
is what the tree carries: a 6% move on the pure-Python ratio and a 19% move on the NumPy one with no
contention at all, which is why the NumPy band's upper edge is `0.51×` and not the `0.57×` the first
of those two readings would have set. Neither discarded reading is in the history the bands derive
from, because no committed artifact carries it; the contended pair is reported here and in
`docs/limitations.md` #77. Load moves the timings, and the
ratios with them — and so does the absence of load.

**Metadata.** Every artifact records its own `generated_at_utc` and the running `git_commit`, so
a re-run always rewrites them. The manifest carries a content hash alongside the byte hash
precisely so that this reads as VOLATILE — regenerated, results identical — and not as CHANGED,
which is reserved for a number that actually moved. Verified end to end: after a full suite
re-run in a fresh clone, 12 artifacts reported VOLATILE with zero canonical differences and the
rest reported OK.

**Compiler and platform.** The core is C++20 and builds with the toolchain above, and three CI
lanes now compile and test it on `ubuntu-latest` with GCC on every push. That runner is where
the first genuine cross-platform difference surfaced: `black_scholes(spot=100, strike=100,
rate=0.04, vol=0.20, maturity=1.0)` returns `9.925053717274434` on Apple's libm and
`9.925053717274437` on glibc — 1.7 ULP, about 1e-14, and a difference in the system's
transcendentals rather than in this code.

So: floating-point results are reproducible on a given platform, and agree across platforms to
within the last one or two digits wherever a `libm` function is on the path. This is why every
oracle tolerance in `docs/validation_matrix.md` has margin rather than sitting on the measured
value, why `test_the_readme_black_scholes_example_runs_as_written` compares in units of the
last place, and why bit-exact equality is claimed only between two views of the *same* binary —
the Python-to-C++ consistency checks — and never between compilers. See limitation #59.

**Fitted statistics, one level worse.** A number that is *estimated from* floating-point results can
be less reproducible than any of its inputs. The two-factor study fits log-log slopes to errors that
are themselves cancellation residues, and across libms those fits moved by 8e-7, 3.2e-3 and 6.6e-3
relative, and by 39% in one regression's standard error — the last figure not a tolerance set wrong but
a statistic with no cross-platform value to reproduce. The mechanism is the same 1.7 ULP above,
amplified: a fit distributes the difference across every one of its samples, and a standard error
measures how much scatter it saw. Such a quantity is reproducible only as a *member of a band*, and the
band is the experiment's own: `experiments/two_factor_error_bound/run.py` raises rather than writing an
artifact whose slope leaves its declared range, and it publishes
`reproduction_policy.conditioning_limited` naming the families this applies to. The reproduction test
reads that list from the artifact and, inside those families, compares key sets, list lengths and types
rather than values — integers, booleans, strings and verdicts stay exact even there, unless the
producer also declares the family under `reproduction_policy.noise_decided_verdicts`. That second list
is for the rarer case where a *verdict* is decided by comparing two values that are themselves at the
subtraction floor (`fourth_order_crossing_map`'s count of rays whose residual-ratio turns back upward
below `scale = 1e-3` is the example, and limitation #79(d) keeps the scope); it is empty by default, so
an experiment that does not declare it keeps every verdict gated, which is why `two_factor_bound` and
`restrike_gamma_map` are unchanged by its existence. Everything outside the families keeps 1e-5
relative. The declaration belongs to the experiment, not the test: a
test that decides field by field which outputs are comparable is re-guessing the numerics it is
supposed to be checking. See limitations #73–#75, #79(d)-(e).

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
