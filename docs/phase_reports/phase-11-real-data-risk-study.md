# Phase 11 — Real-Data Risk Study

Date: 2026-09-28 · Version: 1.0.0 → 1.1.0 · Predecessor: `phase-10-release.md`

Requested by the portfolio audit's top-ranked gap: every statistical conclusion in the project
was measured on synthetic data whose truth is known, which is what makes a bias measurable and
also what keeps each conclusion one step away from an empirical claim (`docs/limitations.md` #28).
This phase pays part of that debt and reports what survived the exchange.

## 1. Completed

- **Real fixtures for the long window.** `scripts/record_data_fixtures.py` gained
  `FRED_HISTORY` and `record_fred_history()`, and committed three 12.7-year daily series as
  offline fixtures with provenance sidecars naming `used_by` and stating that the values are
  FRED's **current revision**, not the vintage published on each date:
  `DGS10` (10-year Treasury par yield), `T10YIE` (10-year Treasury breakeven inflation),
  `VIXCLS` (CBOE volatility index). 3,177 aligned observations, 2014-01-03 through 2026-09-22.
- **`experiments/real_data_risk_study/run.py`** — four answerable questions (A estimator
  validity, B do the coverage tests discriminate, C does the block bootstrap earn its keep,
  D which covariance estimator produces the better book) plus three recorded refusals, twelve
  suite headline scalars, a four-panel figure, and three CSVs.
- **Registered as the suite's twelfth member** in `scripts/run_benchmark_suite.py`, with its
  headline metrics aggregated from the artifact's own `headline` block.
- **`python/quantrisk/data/http.py` contact policy.** `CONTACT_REQUIRED_HOSTS` now refuses
  `sec.gov` and `stlouisfed.org` requests whose User-Agent names no contact, and
  `example_user_agent()` prints a well-formed one. See §6 finding 1 — this was not a nicety.
- **Two new test files, twenty-two new tests.**
  `tests/python/test_real_data_study_offline.py` (11) and
  `tests/python/test_real_data_findings_prose.py` (7); plus 4 in `test_artifact_metadata.py`
  guarding the counts that Phase 11 moved.
- **Evidence chain extended.** `evidence/manifest.json` went from 58 to 69 artifacts, and a
  fifth category `suite_aggregate` now covers `benchmarks/suite/results/` — the roll-up the
  README quotes was itself outside the chain that exists to protect quoted numbers.
- **`docs/validation_matrix.md` gained row 13**, the first row in the matrix whose Oracle column
  reads "none, by construction", and whose Status is therefore `validated (L1 only)`.
- **`docs/findings.md` gained finding 4**, and its opening paragraph was rewritten because the
  first three findings are deterministic and the fourth is not.

## 2. Mathematical assumptions

- **Factor construction.** Three market *prints* are used as risk factors. A level becomes a
  daily move by first difference for the two rate series (in percentage points) and by relative
  change for the index level. No re-estimation, no interpolation, no gap filling: an observation
  that is missing on a date removes that date from all three series, so the alignment is an
  inner join and 3,177 of the ~3,300 calendar days survive.
- **The book is assumed.** Exposures `DGS10 −4.0e5`, `T10YIE −2.0e5`, `VIXCLS −2.5e5` are chosen
  numbers, not positions. P&L is `Σ exposureᵢ × moveᵢ`, i.e. a pure delta map with no gamma, no
  carry and no financing. The artifact says so in `data.book.statement`.
- **Causal calibration.** Every VaR is estimated on the `WINDOW = 250` observations that
  *precede* the return it is scored against, stepping by 5, giving 586 scored days. Backtesting
  an in-sample VaR would have reported the coverage of a fit rather than of a policy.
- **EWMA is `λ = 0.94`**, the RiskMetrics daily default, deliberately untuned. Choosing it after
  seeing the ranking would have made question D circular.
- **Exact intervals are Clopper-Pearson**, obtained from `scipy.stats.binomtest(...).
  proportion_ci(method="exact")`. `scipy` is used for the interval — a published formula — and
  for no risk number; every VaR, ES, covariance and optimisation result comes from the C++ core.
- **Positive homogeneity is used as an invariant, not a sensitivity.** Scaling all three
  exposures by a common factor cannot change a violation rate, so `half_documented` and
  `double_documented` must reproduce `as_documented` exactly. The script raises if they do not,
  for both estimators.
- **No look-ahead claim is made.** Current-revision prints are defensible because market
  observations are corrected only for data errors, unlike revised macro aggregates. That is a
  weaker guarantee than vintage data, and `look_ahead.residual_exposure` states the residue.

## 3. Files changed

| File | Change |
|---|---|
| `scripts/record_data_fixtures.py` | `FRED_HISTORY` series set and `record_fred_history()` |
| `data/fixtures/fred_{DGS10,T10YIE,VIXCLS}_2014-01-01_2026-09-26.csv` (+ sidecars) | new long-window real fixtures |
| `data/fixtures/fred_BAMLH0A0HYM2_2014-01-01_2026-09-26.csv` (+ sidecar) | **removed** — the ICE BofA OAS series was discontinued and its pull truncated at 2023-09 |
| `python/quantrisk/data/http.py` | `CONTACT_REQUIRED_HOSTS`, `_product_token()`, `example_user_agent()`, refusal message |
| `experiments/real_data_risk_study/run.py` | new, ~640 lines |
| `experiments/real_data_risk_study/results/` | JSON, two CSVs, PNG — 4 artifacts |
| `scripts/run_benchmark_suite.py` | twelfth member registered; `command_line()` so the roll-up names its own invocation |
| `scripts/build_evidence_manifest.py` | `real_data_risk_study/results` and a new `suite_aggregate` category |
| `tests/python/test_real_data_study_offline.py` | new, 11 tests |
| `tests/python/test_real_data_findings_prose.py` | new, 7 tests |
| `tests/python/test_artifact_metadata.py` | +4 tests: suite registry counts, generating command, frozen roll-up, test count |
| `docs/limitations.md` | #28 re-scoped; #61–63 added (60 → 63 entries) |
| `docs/validation_matrix.md`, `docs/findings.md`, `README.md`, `docs/reproducibility.md`, `docs/interview_defense.md`, `docs/portfolio_audit.md`, `docs/integrity_audit.md`, `docs/release_notes_v1.0.0.md`, `paper/technical_report.tex` | the results, and the counts the results moved |
| `.github/workflows/ci.yml` | the suite lane's member count |

## 4. Tests executed

```bash
uv run pytest -q                                            # 353 passed with the oracles extra
uv run pytest -q                                            # 284 passed, 4 skipped in the CI lane
uv run pytest tests/python/test_real_data_study_offline.py  # 11 passed
uv run pytest tests/python/test_real_data_findings_prose.py # 7 passed
uv run ctest --test-dir build/dev                           # 190 passed (core unchanged)
uv run python scripts/run_benchmark_suite.py --require-all   # 12/12 executed, 0 skipped
uv run python scripts/build_evidence_manifest.py && uv run python scripts/verify_evidence_manifest.py
uv run mypy python/quantrisk                                # clean, 23 files
uv run ruff check . && uv run ruff format --check .          # clean, 106 files
uv run quantrisk validate                                    # 7/7
```

Every new assertion was **falsified before being trusted**:

- The offline guard was defeated by injecting one `urllib.request.urlopen` call into `main()`;
  the test failed with `a socket was opened`. It blocks `getaddrinfo`, `create_connection` and
  `urlopen` rather than `socket.socket` itself, because `ssl` subclasses `socket` at import time
  and a blunt patch breaks the interpreter's own TLS stack before the script can run.
- The determinism guard was defeated by changing one violation count in the committed artifact.
- The prose guards were defeated by three separate single-digit edits to README.md and
  docs/findings.md (an interval endpoint, a rate, and the sample size), each of which failed the
  corresponding test.
- The label guard was defeated by making `exposure_sensitivity` disagree with question A again,
  which is the bug it exists to catch — see §6 finding 4.
- The count guards were defeated by restoring "eleven" to one README line and "342" to
  limitation #63.

## 5. Exact test results

| Gate | Result |
|---|---|
| pytest, with the `oracles` extra | **353 passed**, 0 failed, 0 skipped |
| pytest in the `build-and-test` CI lane (no `oracles` extra) | **284 passed, 4 skipped** — the four are whole oracle-gated modules, not four cases; see #63 |
| First CI run of this phase | **2 failed** — the two cross-platform assertions in finding 11 |
| Final CI run, on `26110b8` | **all three lanes green** — lint, build + C++ tests + Python tests, and the 12-member suite with `--require-all` (163.4 s on the runner) |
| CTest | **190 passed**, unchanged; the C++ core was not touched this phase |
| `quantrisk validate` | **7/7**, worst residual 2.22e-16 |
| Benchmark suite | **12/12 executed and passed, 0 failed, 0 skipped**, 62–69 s |
| Evidence manifest | **69 artifacts, 6,216,185 bytes, 0 CHANGED, 0 MISSING, 0 unlisted, 0 warnings** |
| mypy / ruff / clang-format | clean |

330 tests existed at the `v1.0.0` tag, 331 at the phase's first commit, 353 at its last. The 22
added are the two new files plus the registry, command and count guards. The session fixture in
`tests/python/conftest.py` is not a test and does not change that count.

## 6. Numerical validation

**1. FRED does not reject a contactless client; it silently drops it.** `http.fetch` hung for the
full 30-second timeout against `fredgraph.csv` while `curl` on the same URL returned in 0.7 s. The
first diagnosis — "transient" — was wrong, and a paired order-swapped A/B settled it: a User-Agent
naming a contact returns, `QuantRisk/0.1 (research)` times out, and the result does not depend on
which is tried first. A silent drop is worse than a 403 because it looks like a network fault.
`http.py` now refuses the request locally with a message containing a well-formed example agent,
so the developer sees a policy instead of a timeout. The SEC publishes the same requirement; FRED
enforces it without saying so.

**2. The high-yield spread series no longer exists.** The first fixture set used `BAMLH0A0HYM2`
(ICE BofA US high yield OAS). The pull succeeded and truncated at 2023-09 without error — the
series was retired — which would have silently dropped three years from the sample. Replaced with
`T10YIE`, and the retired fixture deleted rather than left in the tree as an attractive nuisance.

**3. Bootstrap coverage on real data is not measurable, and the first attempt proved it.** The
Phase 5 arm could ask "does the block bootstrap reach 90% coverage" because the process was known
analytically. On a real sample the only candidate truth is the full-sample VaR, and intervals built
by resampling that same series cover it by construction: the measurement returned **1.000**. That
number is discarded, named as discarded inside `refusals`, and question C was redesigned as the
truth-free ratio of iid to moving-block standard errors.

**4. A label that did not mean the thing.** `exposure_sensitivity` scaled raw factor moves by unit
weights and published the result under the key `as_documented`, while question A scaled the same
moves by `EXPOSURES`. The two disagreed by a factor of two, and the figure appeared to confirm the
headline. Rewritten to scale the documented exposures, with a `RuntimeError` crash guard that now
covers both estimators, plus a test asserting the arm equals question A to the last bit.

**5. A hand-rolled exact interval came out inverted.** The first Clopper-Pearson implementation
returned `[100.000%, 4.484%]` for a rate of 6.3% — the upper bound below the lower, because the
F-inverse calls were swapped. Replaced with `scipy.stats.binomtest().proportion_ci(method="exact")`,
which is already tested in the project, rather than debugging a private reimplementation of a
standard function.

**6. Aggregating by key path into a list is how a 95% number gets published under a 99% label.**
`dig()` walks dicts, so the Gaussian row had to be found by `confidence` inside a list. The suite
now reads the artifact's own `headline` block, whose scalars are *references* to those rows rather
than retyped values, and `test_headline_scalars_are_the_rows_and_blocks_they_cite` re-derives each
one from its source.

**7. The evidence chain did not cover the artifact the README quotes.** The manifest hashed 58
files, none of them `benchmarks/suite/results/` — so "12/12 members executed" was a claim about a
file nothing verified. Added as a fifth category, which then exposed that the suite roll-up
recorded no generating command at all. It now does, and `--out` is repo-relativised so an absolute
path cannot be written into a committed artifact — the same class of leak Phase 10 found in
`sys.argv[0]`.

**8. Three documents disagreed about the same number.** `docs/reproducibility.md` said four suite
members skip without the `oracles` extra when the registry already had five (now six);
`docs/release_notes_v1.0.0.md` said 330 Python tests and `docs/interview_defense.md` said 319 for
the same tag. The tag's real numbers were measured in a clean worktree at `v1.0.0`: **330**, and
CI's own log for that commit prints **261 passed, 4 skipped**. Four guards now bind those counts to
their sources: the registry (`len(MEMBERS)` and the per-kind breakdown), the limitations file, the
frozen roll-up's recorded command, and a `pytest --collect-only` subprocess for the test count.

**9. A test suite that damaged the evidence it was measuring.** The real-data study's offline
tests executed `run.py` with `cwd=REPO_ROOT`, and the script writes to
`Path(__file__).parent / "results"` — so every `pytest` rewrote a committed artifact: new
timestamp, new `environment` block, tree left dirty, and `verify_evidence_manifest.py` answering
VOLATILE for a file nothing had regenerated on purpose. Reproduced deliberately to falsify the new
guard: pointing the reproducibility test back at the in-repo script makes it fail with
`the test run modified a committed artifact`. Fixed by running a *copy* of the script placed in
`tmp_path`, so the results directory it writes is elsewhere, and by adding a session-scoped
autouse fixture in `tests/python/conftest.py` that hashes every file under `benchmarks/`,
`experiments/`, `data/fixtures/` and `evidence/` before the session and asserts at teardown that
none of them moved. Verified: a full `pytest` run now leaves `git status` clean.

**10. Two destructive edits by the author of this phase, both recoverable, both worth recording.**
Mid-phase, `git checkout README.md` — typed as a convenience undo of one experimental edit —
discarded nine uncommitted documentation edits, because in a tree deliberately left dirty for a
whole phase `HEAD` is not where the work is. Later, a `Write` to `tests/python/conftest.py`
overwrote an existing tracked file on the mistaken premise that it did not exist; an earlier `ls`
in the same session had proved it did. Both were recovered (the first from the session transcript,
the second exactly, from `git show HEAD:...`). Neither should have been possible: the rule they
teach is that restoring a file needs a copy made *before* the experiment, and that a whole-file
write requires confirming the path is absent first. Recorded here rather than in the limitations
file because it is a process defect in the tooling that produces the evidence, not a property of
the models.

**11. The runner caught this phase re-committing the exact defect Phase 10 documented.** Two of
the new tests failed on `ubuntu-latest` and both were assertions about equality across platforms:
`test_a_fresh_run_reproduces_the_committed_artifact_exactly` demanded bit-for-bit agreement with an
artifact frozen on macOS, and glibc's libm moved the last digits by ~1e-14 (`0.0006136533643794436`
against the committed `0.0006136533643794354`);
`test_the_documents_that_count_python_tests_count_the_ones_that_exist` asserted the local
with-oracles test count in a CI lane that installs without them. The first test's docstring even
read "the comparison is exact, not approximate: nothing here is sampled from a live source, so there
is no legitimate source of variation left to allow for" — which overlooked the one source of
variation `docs/limitations.md` #59 had already named, and I had written that entry. Fixed by
comparing floats with a documented 1e-12 relative slack (two orders above the observed spread, six
below anything a reader would call a different number) while holding integers, verdicts and the
ranking exact, and by making the count guard ask which environment it is in before choosing which
figure to check. Recorded as limitation #64: **the frozen evidence is a record of one platform's
last digits**, so `verify_evidence_manifest.py` is a same-platform tamper check and CI verifies
*execution* on Linux rather than byte equality there. Ten perturbations of the comparator were run
to confirm it tolerates 1e-14 and rejects a 1e-6 change, a sign flip, a count change, a verdict
flip, a ranking permutation and a zero-against-nonzero comparison.

**The results themselves.**

| Question | Measured | Against |
|---|---|---|
| A — Gaussian 99% VaR | realised **2.048%**, exact CI **[1.062%, 3.550%]**, 12 violations / 586 | 1% nominal — **CI excludes it**: significant miscalibration on real data, reproducing the synthetic t(3) prediction (1.389% vs 1.021%) |
| A — historical 99% VaR | realised **1.365%**, CI **[0.591%, 2.672%]**, 8 violations / 586 | 1% nominal — **CI covers it** |
| A — both at 95% | Gaussian 5.631% [3.908%, 7.818%], historical 6.314% [4.484%, 8.598%] | 5% — both cover; the failure is in the tail, not the body |
| B — coverage tests | Kupiec **p = 0.160**, independence **0.287**, conditional **0.211**; 37 violations | 0.05 — **none rejects.** The synthetic arm's discrimination does not materialise on this sample |
| B — clustering | runs test **z = −1.17** (67 runs against 70.33 expected) | right sign, no power — consistent with B |
| C — bootstrap | block/iid SE ratio **1.072** | 1.0 — the iid interval is 7% too tight, mild and truthful |
| D — covariance | realised variance **ewma < sample < shrinkage** over 582 windows | Phase 6's synthetic mean ratio was **shrinkage 1.169 < sample 1.183 < ewma 1.241** — **the two ends exchange places** |

Question D is the phase's most interesting output because it is a *contradiction*, not a
confirmation: the estimator that won on generated data loses on market data, and the one that lost
wins. Neither result is a bug. Shrinkage wins where a short window makes the sample covariance
unstable, which is the regime the synthetic DGP was built to create. The conclusion generalises over
the method, not the process: an estimator ranking is a property of the process it was measured on.

## 7. Remaining limitations

Recorded as `docs/limitations.md` **#61** (the book is assumed, not held; rates are invariant to
uniform scaling but not to the factor mix), **#62** (current revision, not vintage — `fetch_vintage`
exists and is unused), **#63** (the test count is a property of the environment, and a document
quoting one number without saying which is wrong) and **#64** (the frozen evidence records one
platform's last digits, so byte verification is same-platform only). #28 was **re-scoped rather than deleted**: the
instrumented synthetic validation it describes is still exactly that, and the new arm is narrower
than it, not a replacement for it.

Still open after the phase:

- **One sample, three factors, one exposure set.** Finding 4 is not a market-wide statement and the
  README does not present it as one.
- **Question B is a negative result with no follow-up.** The independence test failing to reject on
  real data while rejecting 55.4% of synthetic clustered series is either a property of this sample
  or a hint that the synthetic clustering was stronger than real volatility clustering. Separating
  those needs more series or a longer record, and neither was fabricated to make the story tidier.
- **The fixture window is frozen at 2026-09-26.** Re-recording changes 3,177 observations, every
  number in the artifact, and every document quoting them. That is why the window is in the
  filename.
- **`experiments/real_data_risk_study` needs no oracle and therefore cannot be promoted.** Row 13
  of the matrix will stay `validated (L1 only)`.

## 8. Technical debt

- **The prose guard is string-matching.** `test_real_data_findings_prose.py` requires the literal
  `2.048%` to appear in README.md, so rewording the sentence to "about 2%" breaks a test for a
  reason the test should not care about. A parser over a structured claims file would be the real
  fix; this is the second-best, and it is at least the direction that catches the actual defect.
- **Two owners remain for the number of tests.** The guard measures with-oracles and documents the
  CI figure from a runner log, because reproducing 261 would mean uninstalling the oracles from
  inside the session that is asserting about them.
- **`MEMBERS` is still hand-registered** (#58). Phase 11 added the key-path, kind-breakdown and
  skippable-count guards, but a benchmark script that was never registered is still simply absent.
- **Author behaviour is part of the harness.** See §6 findings 9 and 10. The evidence chain now
  detects a test that writes into it, but nothing detects an agent that restores the wrong
  revision of a document; that remains a manual discipline.

## 9. Gate

**Phase 11: PASS.** Released as `v1.1.0` on 2026-09-28 at commit `c5b8c5b`, with the 38-page
technical report, `evidence/manifest.json`, `CITATION.cff` and a zip of the four suite artifacts
attached; `v1.0.0` is left untouched and `v1.1.0` is the repository's latest release. Every asset
was downloaded back and compared by SHA-256 against the committed file it claims to be, including
the four inside the zip. All three CI lanes are green on that commit on `ubuntu-latest`: lint, then
build + 190 CTest + the pytest lane (`284 passed, 4 skipped`), then the 12-member suite with
`--require-all` in 163 s.

The audit question was "which of the synthetic conclusions survive real data", and the answer is
recorded with the parts that did not survive intact: one prediction confirmed with a significant
interval, one estimator ranking reversed, one test battery failing to discriminate, three questions
refused rather than proxied, and one negative result published instead of buried.

Everything the phase asserts is executable: `uv run python scripts/run_benchmark_suite.py
--require-all` runs the study as its twelfth member, `uv run python
scripts/verify_evidence_manifest.py` confirms 69 artifacts with nothing changed, missing or
unlisted, and the three prose guards re-derive every number the README and finding 4 print from the
artifact that produced them.

Cost: **$0**. FRED, like SEC EDGAR and CFTC, needs no key and no account for the prints used here;
the only requirement discovered was a User-Agent naming a contact, and the project now supplies one
from `git config user.email` with `QUANTRISK_DATA_USER_AGENT` as the override.
