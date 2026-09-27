# Graduate Admissions Portfolio Audit

Written from the perspective of six admissions committees, against the repository as of
`v1.0.0` (commit `06836d2`). Every claim below cites a file or a measurement, including the
unflattering ones — an audit that only lists strengths is advertising.

The committee lenses: **Financial Engineering · Financial Mathematics · Quantitative
Finance · Applied Mathematics · Statistics · Data Science**.

Measurements used throughout:

| Quantity | Value |
|---|---|
| C++ implementation (`cpp/src` + `cpp/include`) | 6,946 lines |
| C++ tests (`tests/cpp`) | 4,508 lines |
| Python tests (`tests/python`) | 4,167 lines |
| Benchmarks, experiments, scripts | 6,331 lines |
| Documentation | 5,016 lines + 37-page report |
| Public Python API symbols | 159 across 8 modules |
| Test totals | 190 CTest / 546,943 C++ assertions / 316 pytest |
| Frozen artifacts | 58, hashed, with generating commands |

**The ratio that matters: 8,675 lines of test against 6,946 lines of implementation.** More
than half the C++ in this repository is proof about the other half.

---

## 1. What abilities does this project demonstrate?

**Demonstrated, with evidence a committee can check:**

- *Numerical analysis, not just numerics.* Convergence orders are fitted with standard errors
  and compared to theory (CRR −0.99405 ± 0.00313 vs −1; MC −0.614 ± 0.089 vs −0.5). A student
  who can report a slope *with its uncertainty* has done the exercise; one who reports a
  table of errors has not.
- *Numerical linear algebra under real conditions.* The portfolio layer solves KKT systems by
  saddle-point reduction with an active set and a certificate, never by inverting Σ — and
  `docs/limitations.md` and the model card explain that `Σ⁻¹` returns the minimum-norm
  stationary point, which is a different answer. Applied-mathematics committees read for
  exactly this kind of choice.
- *Measure discipline.* Risk-neutral pricing and physical-measure simulation are different
  entry points, and `terminal_prices_physical(mu=r)` with the same seed returns the identical
  stream — the separation is tested, not asserted in prose.
- *Statistical validation of a risk model.* Backtest size, power and specificity; p-value
  uniformity; bootstrap coverage against exact binomial bands; the clustered-data arm where
  the unconditional test misses what the independence test catches.
- *Reproducibility engineering.* An evidence manifest binding each artifact to a hash, a
  command, a revision and an environment; a verifier that distinguishes CHANGED from MISSING
  from unlisted.
- *Judgement about one's own work.* This is the rarest and most legible signal. The project
  records that its own benchmark was measuring PyPortfolioOpt's rounding rather than its
  optimiser, that a documented precision claim was six orders of magnitude wrong, and that a
  headline "worst MSE reduction = 1.0" was true but vacuous. Candidates rarely publish
  evidence of catching themselves.

**Claimed but not demonstrated:**

- Original research. Every model here is textbook. The contribution is verification and
  engineering, not new mathematics — and no MFE/FinMath committee expects a new theorem from
  an applicant. Worth stating plainly rather than dressing up.
- Any empirical finance. There is no real-market result in the repository at all.

## 2. Which parts are genuinely graduate-level?

Ranked by how much a specialist would respect them:

1. **The optimisation certificate** (`cpp/src/portfolio/mean_variance.cpp`). An active-set
   solve with a residual and a bound-violation report, where an unreachable target is
   returned as *unreachable* rather than as a portfolio. Framing "the refusal is the point"
   is graduate-level epistemics, and the max-Sharpe ternary search being documented as
   needing 1e-12 bracketing to get 1e-9 coordinates on a flat frontier is the kind of detail
   only someone who measured it would write.
2. **The stress result** (`experiments/stress_testing/`). "Rankings do not invert — but only
   because the books started 20.8% apart and the stress spread is 16.8%; the *sensitivity*
   ranking inverts completely, and the minimum-variance book is the most stress-sensitive at
   6.11× vs 5.23×." A negative result, correctly diagnosed, with the confound identified.
3. **The estimation-cost experiment** (`experiments/portfolio_optimization/`). Rolling-origin,
   with the forward covariance known in closed form so the truth is analytic. The finding —
   estimation dominates optimiser choice, and non-stationarity dominates estimation — is the
   standard academic conclusion, and this reproduces it rather than asserting it.
4. **Backtest size and power** (`experiments/var_backtesting/`). 2,000 replications, exact
   binomial intervals, a clustered arm as the specificity discriminator.
5. **The two silent engine bugs.** A beta vector sized from the wrong block allocating zero
   risk to a vega-only position; a volatility multiplier rescaling only the diagonal and
   halving every correlation. Both were caught by checks, not by reading. This is what
   "tested" means.

## 3. Which parts still read like ordinary undergraduate coursework?

Answering honestly, because a committee will find these whether or not I list them:

- **Black-Scholes, Greeks and the CRR lattice.** The models are Week 1 of any derivatives
  course. What lifts them above the coursework is the 2,464-comparison live QuantLib sweep
  and the fitted convergence order — but a reviewer skimming the file list sees
  "options pricer" first. The README's ordering has to do the work of disambiguating, and
  mostly does.
- **The Monte Carlo engine and variance reduction.** Standard material. The out-of-sample MSE
  framing (fitting `beta` in-sample and scoring it out-of-sample, so the control variate
  cannot flatter itself) is the part that isn't coursework.
- **`docs/ecosystem_research.md` and the Phase 0 planning documents.** Literature-review
  shaped, and a committee that has read fifty of them will recognise the genre. They earn
  their place as process evidence, not as intellectual content.
- **The public-data layer's HTTP plumbing.** Rate limiting, caching, gzip and provenance
  hashing are real software engineering but carry little academic signal for MFE or FinMath
  readers; they matter to a Data Science committee and are close to invisible to the others.
- **The CLI.** Three commands. Fine, forgettable.

## 4. Which features are engineering complexity without application value?

The question to ask of each is "does a committee member's estimate of my judgement rise or
fall?" — complexity that looks like *self-imposed* difficulty can read as poor prioritisation.

**Low value for the stated goal:**
- The two-phase dense primal simplex with Bland's rule. Mathematically respectable, and it is
  genuinely ours — but a reviewer cannot tell in ninety seconds whether it matters more than
  calling a solver, and §2.2's "must implement it ourselves" is a project constraint, not an
  argument to an outside reader. It needs the one-sentence justification on its front page,
  not buried in a model card.
- The data layer's per-host rate limiter persisted to disk so it binds across processes.
  Correct, careful, and irrelevant to a financial-engineering committee.
- The eight Python shim modules with an AST walk rejecting arithmetic in them. The *test* is
  excellent evidence; the shims themselves are 400 lines of plumbing.
- `quantrisk demo`. Nobody learns anything from it.

**High value, and worth the line count:** the evidence manifest, the benchmark suite runner,
the certificate, the attribution identity, and the limitations file.

## 5. Is the mathematical depth sufficient?

**For MFE / Quantitative Finance / Financial Mathematics: yes, and above the typical
applicant.** The surface covers Itô integration and the Itô correction, Girsanov and measure
change, the martingale representation argument for completeness, Taylor expansion with an
explicit remainder (the delta-gamma map and its measured 1.3e-4 → 0.488 error curve),
Rockafellar-Uryasev convex duality, KKT conditions with active-set identification, the
Euler/radial decomposition of a homogeneous risk measure, and the Ledoit-Wolf shrinkage
derivation. That is a first-year MFE reading list, implemented rather than summarised.

**For a Financial *Mathematics* or Applied Mathematics programme: adequate but not deep.**
There is no proof of anything. No convergence proof for the simplex, no error bound for the
truncation scheme, no measure-theoretic construction. A pure-mathematics committee will read
the fitted slope −0.994 ± 0.003 as empirical, which it is. If the target list includes
programmes that are mathematics departments rather than schools of engineering, one worked
analysis result — even a proof of the `O(Δt)` CRR bound under the paper's own regularity
assumptions — would be the highest-value addition. That is a *document*, not a feature.

**The gap a sharp reviewer will find:** Heston is validated numerically only. There is no
closed-form characteristic function of our own, so the Feller-condition treatment is
"reported, not enforced" and the ξ=0 collapse is the only exactness claimed. That is
honestly documented (#25–27) and honestly scoped, but it is the thinnest mathematical seam.

## 6. Is the statistical rigour sufficient?

**Yes — this is the strongest dimension, and it is the one a Statistics committee weights
most.**

- Uncertainty is attached to the estimates that matter: convergence slopes with standard
  errors, coverage with exact binomial intervals, backtest rejection rates at three nominal
  levels, MC comparisons judged at 4× the combined standard error rather than against a
  made-up epsilon.
- The p-value machinery is honest about its own discreteness: the artifact states that
  Kupiec and Christoffersen statistics are functions of integer counts, so their p-values are
  step distributions, and the KS statistic is reported as residual distance rather than
  misread as a defect.
- Negative controls exist: planted violations, a degenerate series reported as untestable, a
  mirrored book where a naive diversification claim is false by symmetry.
- No causal claim is made anywhere that the design could not support. The estimation-cost
  result is the *only* kind of causal statement available here — the DGP is known — and the
  caveats say so.

**Two honest weaknesses.** First, everything is synthetic, so the statistics are about
estimators rather than about markets; a Statistics committee will want one real dataset and
will note that the data layer exists but is never used for inference. Second, there is no
multiple-comparisons control across the many hypothesis tests — with a dozen nominal levels
and several arms, a reviewer may ask, and the answer ("these are confirmatory checks of
specified properties, not a search for a significant result") is defensible but is not
currently written down.

## 7. Is C++ genuinely used as the numerical core?

**Yes, and this is verifiable in one command rather than asserted.**

- 6,946 lines of C++20 hold every number-producing routine; the Python layer holds 2,415
  lines of facades, plumbing and experiment drivers.
- A test enforces the direction of dependency: each re-exported callable's `__module__` is
  the extension, and an AST walk rejects any arithmetic, comparison or loop inside a shim
  module. That guard was *strengthened* when Phase 9's design invalidated its original form,
  rather than deleted.
- `quantrisk validate` runs seven identities against the installed binary, including a finite
  difference convergence ratio of 4.00 and 4.00 — a property of the compiled code, not of a
  Python reimplementation.
- Eigen is used for the linear algebra; `Real = double` and `Count = int64_t` are frozen
  types; the RNG is instance-owned `std::mt19937_64` with our own Marsaglia polar normals.

**The counter-evidence a reviewer should be given before they find it:** the C++ engine is
*slower* than vectorised NumPy (0.42×–0.48×) on the benchmarked terminal-only workload, and
the project says so in the README, the release notes and the report. Handled well, this reads
as calibration; hidden, it would have read as either naivety or dishonesty.

## 8. Can reproducibility be demonstrated?

**Yes, by artifact and by execution — the strongest claim in the portfolio.**

- `evidence/manifest.json`: 58 artifacts, each with a SHA-256, the generating command
  recovered *from the artifact itself*, the repository revision, the dirty flag, and the full
  compiler and package environment.
- `verify_evidence_manifest.py` reports OK / CHANGED / MISSING / unlisted separately and exits
  non-zero on any of the last three.
- One command regenerates everything in ~60 s; a CI job runs it with `--require-all` so a
  missing oracle fails the build instead of skipping quietly.
- The suite runner holds no number of its own and aborts if a key path moves, so a renamed
  field breaks the summary rather than silently shrinking it.
- The scope is stated precisely: result values are bit-identical across runs (verified by
  diffing every numeric leaf); three artifacts carrying wall-clock columns are named as the
  exceptions, with the observed 5% and 14% spreads quoted.

**Not yet demonstrated:** a second person has never reproduced it, and the new CI lane has
never run on a real runner. Both are recorded as open, which is the correct treatment.

## 9. Does the README let a professor understand the value in three minutes?

Structurally yes: it opens with what the project is and why it exists, not a feature list, and
the mandated eleven sections are in order.

The first three minutes in practice:

| | |
|---|---|
| 0:00–0:25 | "What it is" — 12 components, and the sentence that the interesting claim is traceability, not model count. Clear. |
| 0:25–1:20 | "Why it exists" — four concrete bugs found in *this* project, including one where a benchmark was measuring the oracle's rounding. This is the section that works hardest, and it is the reason to keep the README long. |
| 1:20–1:50 | 30-second example with real output values. Fast, credible. |
| 1:50–3:00 | The validation table: bound asserted vs worst measured, per component. |

**Where a tired reader stalls:** the "Why it exists" bullets assume the reader knows what
`clean_weights()`, `EmpiricalCovariance` and a "bound `std::vector` member" are. Two of the
four land without background; the third and fourth need a sentence of context each. The
Validation table is also 10 rows deep at the point where 4 would carry a first reading and
the matrix exists for the rest.

**Length:** ~250 lines is long for a README and short for what it is arguing. The right
answer is not shorter — it is a four-row table where there are ten, and one clause of
context on each of the two opaque bullets.

## 10. Which three improvements would most raise competitiveness?

Ranked by signal-per-hour, and deliberately *not* by feature count:

1. **One real-data empirical study, using the data layer that already exists.**
   The whole repository proves things about estimators on synthetic DGPs. A single honest
   application — VaR backtests on a decade of FRED-derived index returns with ALFRED vintages
   to avoid look-ahead, or an out-of-sample covariance comparison on real series — converts
   "well-engineered coursework" into "someone who has done the thing". It closes the
   limitation #28 gap that a Financial Engineering or Statistics committee will look for
   first, and it reuses code that is already written, tested and committed. *Highest value,
   moderate effort, no new model.*

2. **A one-page "findings" document, written for a reader with ninety seconds.**
   The best three results in this project — the stress-sensitivity inversion, estimation
   dominating optimiser choice, and the two silent bugs — are currently distributed across a
   37-page PDF, six experiment artifacts and a 250-line README. A professor deciding whether
   to interview will not assemble them. Extracting them into `docs/findings.md`, each with
   its number, its confound and its artifact path, costs an hour and changes how everything
   else is read.

3. **One worked analysis result.** A proof of the `O(Δt)` CRR convergence bound under the
   regularity assumptions the model card already states, or an error bound for the
   delta-gamma Taylor map that predicts the 1.3e-4 → 0.488 curve actually measured. This is
   the only thing separating this portfolio from "excellent engineer, unclear mathematician"
   for Financial *Mathematics* and Applied Mathematics programmes. It is also the slowest
   option and the only one that risks being wrong in a way a specialist notices — which is
   exactly why it is worth doing.

**Explicitly not on this list:** more models (Ornstein-Uhlenbeck, jump diffusion, GARCH,
multi-factor Heston calibration), a web dashboard, more solvers, or a live data feed. Each
would add surface without adding signal, and §2.1 of the project's own spec says so. The
marginal value of a thirteenth component is negative: it dilutes the claim that this project
is about verification rather than volume.

---

## Simplification decision

The audit's answer to "what should change before shipping" is *subtraction and extraction, not
addition*. Concretely, and applied in this same pass:

1. Trim the README's Validation table from 10 rows to the 4 that a first-time reader can
   hold, pointing at `docs/validation_matrix.md` for the rest.
2. Add one clause of context to each of the two opaque "Why it exists" bullets.
3. Extract `docs/findings.md` — three results, each with its number, confound and artifact —
   and link it from the README's opening.
4. Delete `quantrisk demo`'s promotional framing rather than the command itself: it is the
   documented smoke test for the facades, and removing a command from a released CLI is a
   breaking change with no gain.

Improvements 1 and 3 from the ranked list above are *not* applied here. They are the next
phase of work, not a simplification, and the instruction was explicitly to stop adding.
