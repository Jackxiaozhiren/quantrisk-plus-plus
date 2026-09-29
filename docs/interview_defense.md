# Interview defense — self-test sheet

Date: 2026-09-27 · Repository state: **Phases 0–10 shipped, `quantrisk` 1.0.0** — the full
surface this sheet describes is implemented, validated and frozen in `evidence/manifest.json`.
Question set: `PROJECT_SPEC.md`, section 最终面试准备材料 — 22 questions in four groups,
reproduced here one for one and in order. Nothing added, nothing dropped.

**What this file is for.** It is a rehearsal sheet, not a script. Every number and every
"we did X because Y" below is traceable to a source file or a committed artifact; the last
section maps each claim to the path or the command that regenerates it. If you cannot
regenerate a figure, do not say the figure — say the property instead. Answers that survive
only as memorised prose are the ones that fail first.

**Status boundary (state this before any risk or portfolio answer).**
`docs/project_scope.md` §9 is the authority. Built and validated: the C++ core
(instance-owned `std::mt19937_64` with our own Marsaglia polar normals, normal
PDF/CDF/quantile, Neumaier compensated statistics), Black-Scholes-Merton with continuous
dividends plus five analytic Greeks and central-difference Greeks, the CRR lattice for
European and American exercise, exact-GBM terminal and path generation, a Monte Carlo engine
with antithetic and control-variate estimators, geometric and arithmetic Asians and barrier
payoffs with the Broadie-Glasserman-Kou correction, full-truncation Euler Heston, the
market-risk layer (historical / Gaussian / Monte Carlo VaR and ES, iid and moving-block
bootstrap, Kupiec and Christoffersen tests), three covariance estimators, six portfolio
solvers each carrying a certificate checked against its own inputs, the stress engine with
Euler attribution, the optional public-data layer with real committed fixtures, the typed
Python facades and the three-command CLI.

**What is genuinely not here** — and this is the list to reach for under pressure, not a list
of unbuilt phases: no expected-return model, no term structure, no Heston Greeks or smile
calibration, no multi-period rebalancing, no short positions or leverage, no reverse stress
testing, and no re-pricing inside the stress layer. `docs/limitations.md` has all 75
numbered entries; `docs/validation_matrix.md` marks two components `partially validated` and
says why.

The one item that changed is the empirical claim. Until Phase 11 every statistical result ran
on synthetic data whose truth is known. `experiments/real_data_risk_study/` is now the
real-data arm: 586 out-of-sample days of three FRED factor series, and it both confirmed the
synthetic prediction (Gaussian 99 % VaR over-rejects; the exact interval excludes nominal) and
contradicted it (the shrinkage covariance that won on synthetic data ranks *worst* here). What
it cannot do is answer the questions that needed a known truth — those are recorded as
`refusals` inside the artifact rather than proxied.

Current suite as measured at HEAD: 198 C++ tests under CTest (547,845 assertions in 197 Catch2
cases), 388 pytest tests with the `oracles` extra and the same tree collects 319 tests without it
— the runner printed `284 passed, 4 skipped` at the 353-test commit, and the guard checks this one's figure on the runner rather than trusting arithmetic here). 14/14 benchmark-suite members executed, `quantrisk validate` 7/7. The gap is structural, not a quality
difference: four oracle-gated modules collapse into four skip records instead of the 69 cases they
hold (limitation #63). At the `v1.0.0` tag the same commands gave 330 and 261-passed-4-skipped, and
the suite was 11/11. A guard asserts both figures and asks which environment it is running in
before choosing — because two documents used to quote two different numbers for one tag, and the
first version of the guard itself failed on the runner for asserting only the local one.

---

## 1. Mathematical Finance

### Q1. Why does Black-Scholes use risk-neutral pricing?

**30 s.** Because the delta-hedged portfolio is locally riskless, so no-arbitrage forces it
to earn `r`, and the stock's own drift `μ` cancels out of the pricing equation. The
consequence is that the price is a discounted expectation under the risk-neutral measure `Q`
in which the discounted underlying is a martingale — no investor preferences needed. In this
repository that separation is enforced in code: every price uses drift `(r − q − σ²/2)`, and
the physical measure only exists in a different function with an explicit `mu`.

**2 min.** Two equivalent routes to the same statement. Hedging route: for `V(S,t)`, the
portfolio `Π = V − ΔS` satisfies `dΠ = (∂V/∂t + ½σ²S²∂²V/∂S²)dt` once `Δ = ∂V/∂S` kills the
`μS ∂V/∂S` term; a riskless self-financing position must grow at `r`, which gives the
Black-Scholes PDE — an equation that contains `r` and `σ` but never `μ`. Martingale route:
Girsanov absorbs the risk premium `(μ − r)/σ` into the Brownian motion, and because one risky
asset continuously rebalanced makes the market complete, that measure `Q` is unique, so
`V₀ = e^{−rT} E^Q[payoff]` is the only arbitrage-free price. The trap this creates, and the
one I have seen most often in code reviews: `Q` is for prices, `P` is for risk. VaR and ES
must be estimated on the physical distribution or on realised returns. A shared drift
parameter between a pricer and a risk engine is a modelling error, not a rounding error.

**Deeper.** The transition actually simulated is
`S_T = S·exp[(r − q − σ²/2)T + σ√T·Z]` (`cpp/src/stochastic/gbm.cpp:32-35`); the `−σ²/2` is
the Itô correction, and it is the reason `E^Q[S_T] = S e^{(r−q)T}` while the median path ends
lower. That closed-form mean of the control is exactly what makes the terminal price usable as
a control variate (`cpp/src/monte_carlo/engine.cpp:157-158`). The price itself is
`S e^{−qT}N(d₁) − K e^{−rT}N(d₂)` with
`d₁ = [ln(S/K) + (r − q + σ²/2)T]/(σ√T)` (`cpp/src/pricing/black_scholes.cpp:63-67,101-105`).
Measure discipline is testable, not rhetorical: `tests/cpp/test_gbm.cpp:170-186` checks that
`terminal_prices_physical(market, mu=0.12)` has mean `S e^{(mu−q)T}`, and that feeding it
`mu = r` with the same seed returns a vector identical to the risk-neutral draws. Convention
frozen in `docs/project_scope.md` §10: `mu` denotes price appreciation *excluding* the
dividend yield, so `mu = r` reproduces the risk-neutral stream. Measured agreement of the
analytic price with live QuantLib 1.43: worst absolute error 1.49e-13.

### Q2. What assumptions does GBM make?

**30 s.** Continuous paths with independent, stationary, normal log-increments; constant
annualised `σ`; constant `r` and `q`; a frictionless market with continuous trading, no jumps,
no transaction costs, no arbitrage; dividends as a continuous yield. The consequence this
project exploits: because the exact transition is lognormal, a European Monte Carlo estimate
here carries zero discretisation bias, so all remaining error is sampling error and the Phase 3
statistics are interpretable.

**2 min.** Each assumption has a specific way of being wrong, and the model card states them as
claims that can fail rather than as background. (1) Lognormality: realised returns are skewed
and fat-tailed; the implied-volatility smile is the market's testimony against it. (2) Constant
`σ`: volatility clusters and mean-reverts — which is what the Phase 4 Heston implementation
adds, at a measured cost of 4.5e-3 worst-case relative error against a semi-analytic oracle.
(3) Constant `r`: no term structure, one flat rate and one flat `q` (limitation #10), so
pricing a forward curve with this code is a modelling error. (4) Continuous trading: no price
gaps, which is why a barrier is only exactly defined under continuous monitoring and discrete
monitoring needs its own convention. (5) No jumps: a jump makes the market incomplete, so `Q`
is no longer unique and there is no single arbitrage-free price. (6) Continuous dividend yield
only — discrete dividends are out of scope (spec §11). (7) Time enters as year fractions
supplied by the caller; no day-count inference happens in the core, and the benchmark maps
days → `days/365` explicitly.

**Deeper.** Assumptions are encoded in the domain, the limits and the failures that are written
down rather than hidden. `MarketParams::validate()` enforces `S > 0`, `K > 0`, `σ ≥ 0`, `T ≥ 0`,
`r` and `q` finite with free sign, so negative rates are expressible; `docs/limitations.md` #15
records plainly that this guards the domain, not the economics — a coarse lattice can still
report `p ∉ [0,1]`, which `BinomialResult::note` says instead of refusing
(`cpp/src/pricing/binomial_crr.cpp:79-83`). The degenerate edges are implemented as limits: at
`T = 0` the value is the expiry payoff, at `σ = 0` it is the discounted intrinsic of the
forward, and `d₁`/`d₂` return NaN deliberately because "a number from a `0/0` would be a lie"
(`cpp/src/pricing/black_scholes.cpp:60-62`, `cpp/include/quantrisk/pricing/instrument.hpp:82-85`).
The exact-transition claim is tested rather than asserted:
`tests/cpp/test_gbm.cpp:110-126` regenerates the path matrix at steps ∈ {1, 5, 50, 500} and
requires the terminal sample mean to sit within 5 standard errors of `S e^{(r−q)T}` at every
resolution.

### Q3. Why does Monte Carlo error decrease approximately as 1/sqrt(N)?

**30 s.** The estimator is a mean of i.i.d. discounted payoffs, so its variance is
`Var(payoff)/N` and its standard deviation falls like `1/√N`; the CLT fixes the shape of the
residual. It is theory, not an empirical coincidence, and the practical price is brutal: one
extra digit of accuracy costs 100× the paths. Measured here, log-log slopes of |error| on `N`
are −0.614 ± 0.089, −0.585 ± 0.096 and −0.507 ± 0.118 against the theoretical −0.5.

**2 min.** Three conditions have to hold for the rate to be observable: finite variance of the
discounted payoff, genuinely independent draws, and a standard error computed over the actual
independent units. Where those hold, the rate is dimension-free — that is the whole reason
Monte Carlo beats grids for path-dependent or multi-factor claims, where a mesh costs
`mesh^d`. Where the observed decay deviates, the usual culprits are a bias floor (a discretised
path-dependent payoff stops improving once bias dominates), reused or correlated streams, or an
unstable variance for a heavy-tailed payoff, where the `√N` scaling is asymptotic and the
asymptote has not arrived. Variance reduction changes the constant, not the exponent. This is
why the project fits a slope with a standard error instead of plotting a curve and calling it
convincing.

**Deeper.** `SE(V̂_N) = s/√N` is spec §5, and the implementation is
`cpp/src/monte_carlo/engine.cpp:49` — `sample_stddev / sqrt(units.size())`, where `units` are
single paths for plain and control-variate estimators and pair means for the antithetic one.
The fit is an OLS of `log|error|` on `log N` with
`SE(slope) = sqrt(SSE/(n−2)/Sxx)` (`experiments/monte_carlo_convergence/run.py:60-78`), over
path counts 1,000 → 3,000,000 at `base_seed = 42`. One design detail I would be asked about and
would defend: each path count uses a *fresh* engine with the same seed, so the smaller runs are
initial segments of the larger ones (nesting, documented at `run.py:93-95`), which is what makes
the fitted slope clean rather than noisy. Deviations from theory in standard errors: 1.28, 0.89,
0.06. The companion check is that the yardstick itself is right: `error/SE` over 200 seeds per
scenario has standard deviation 0.875–0.999 in the same artifact.

### Q4. Why do antithetic variates reduce variance?

**30 s.** Because the payoff is monotone in the driving normal, so `f(Z)` and `f(−Z)` are
negatively correlated, and the pair mean has variance `½Var(1 + ρ)`, which is below `Var` as
soon as `ρ < 0`. It is a coupling of two draws, not a new model — the estimator stays unbiased
because `E[f(Z)] = E[f(−Z)]`. Measured here on out-of-sample MSE at equal path budget: 1.12× to
2.77× better than plain Monte Carlo.

**2 min.** The gain is largest for payoffs monotone in the noise — most vanilla options and
many path-dependent ones — and small or absent when the payoff is symmetric in `Z`; deep
out-of-money structures over a very short horizon get the least. Two conventions matter more
than the idea. First, pairing must share one `Z` per pair and flip only the *noise* term:
negating the drift as well simulates reversed dynamics under a different measure, and the
product identity then fails. Second, after pairing the independent unit is the pair mean, so
`N` paths are `N/2` samples; dividing the pair variance by `N` instead understates the error by
`√2`, which is precisely the mistake that turns a validated estimator into an overconfident one.
We assert the convention instead of trusting it.

**Deeper.** Construction: `cpp/src/stochastic/gbm.cpp:104-109` (terminal) and `:74-88` (paths,
with the "flip the random term only" comment); pair means:
`cpp/src/monte_carlo/engine.cpp:87-97`, and `result.note` states
"iid_units = paths / 2". Assertions: 100,000 antithetic paths give `iid_units == 50000`, and an
odd path count throws (`tests/cpp/test_monte_carlo.cpp:96-110`). The algebraic check is exact
and not tolerant: `S⁺ · S⁻ = S² exp(2(r − q − σ²/2)T)` for every pair to 1e-12 relative,
because the noise cancels in the product (`tests/cpp/test_gbm.cpp:128-146`). Measured
realised-MSE ratios from the 40-seed ensemble
(`experiments/variance_reduction/results/summary.json`): minimum 1.1155×
(`otm_call_short` @ 10,000 paths), maximum 2.7741× (`atm_put` @ 100,000). The artifact's own
`caveat` field records that antithetic SE is per pair, so the comparison is made on realised MSE
at equal path budget rather than on reported SE.

### Q5. What is the difference between VaR and Expected Shortfall?

**30 s.** `VaR_α` is the `α`-quantile of the loss distribution — a threshold. `ES_α` is the
mean loss given that the threshold is breached — a tail average. VaR answers "how bad is it at
confidence level α"; ES answers "how bad is it in the states worse than that". ES is a coherent
measure, VaR is not. Both are implemented here, three ways each — historical, Gaussian and
Monte Carlo (`risk.historical_var` / `_es`, `risk.gaussian_var` / `_es`,
`risk.monte_carlo_var` / `_es`) — with bootstrap intervals and coverage backtests.

**2 min.** The estimation behaviour differs, and that matters more than the definitional
difference. A quantile is one order statistic: it is jumpy as weights move, high-variance in the
tail, and it depends on how the tail is interpolated. A tail mean averages several order
statistics, so it is smoother and more stable under resampling, though it uses fewer effective
observations and inherits whatever the tail model says. Both depend on conventions that must be
stated next to the number: loss sign (`L = −R`, frozen in spec §6), horizon, sampling frequency,
currency, measure (physical, not risk-neutral), and the data window. Reporting rule in this
project: never a bare point estimate — bootstrap interval plus a backtest, which is exactly what
Phase 5 specifies.

**Deeper.** Spec §6: `VaR_α = inf{l : P(L ≤ l) ≥ α}`, `ES_α = E[L | L ≥ VaR_α]`, with three
estimator families planned — historical (empirical quantile and tail mean), parametric Gaussian
(closed form from `μ, σ`), and Monte Carlo (quantile of simulated losses). The two numeric
primitives that already exist are precisely the historical estimators' building blocks:
`stats::quantile_linear`, which uses NumPy's `method="linear"` convention `h = p(n−1)` with
linear interpolation between order statistics, and `stats::mean_of_largest_sorted`, which is a
historical ES given ascending-sorted losses (`cpp/src/core/statistics.cpp:50-79`). The known
sharp edge is documented rather than buried: the `_sorted` helpers trust the caller's sort order
because re-checking would cost an `O(n log n)` sort in a hot path, so Phase 5's VaR/ES wrapper
must own the sort and be tested for it (`docs/limitations.md` #3). The Gaussian forms would call
`inverse_normal_cdf(α)`, and limitation #2 bounds that: the quantile only degrades above
`|x| ≈ 37`, i.e. `p < ~1e-315`, far beyond any 95 % or 99 % level.

### Q6. Why can VaR be problematic as a risk measure?

**30 s.** Three independent reasons. It is not coherent — subadditivity can fail, so a
portfolio's VaR can exceed the sum of its components and "diversification" can be invisible to
it. It carries no information about the size of the breach, which is the part of the tail that
actually destroys capital. And it is a single order statistic, so it is both unstable to estimate
and easy to flatter by choosing α or a window. ES is the fix for the first two; honest reporting
is the fix for the third. The measurement that makes this concrete is in
`experiments/var_backtesting/`: on t(3) data a Gaussian 99% VaR realises 1.389% violations
against 1% nominal, where the historical estimator lands at 1.021%. The misfit is 39%, and it
is invisible unless you backtest.

**2 min.** Add the consequences that show up in practice. Non-convexity in weights means a
VaR-minimising optimiser can sit in local minima, so "optimal" portfolios are path-dependent
starting points. Threshold-only reporting hides exactly the states that matter, and it
encourages tail-thinning trades that move mass below the cutoff without reducing risk. Estimation
at 99 % needs many observations to say anything, which is why a backtest is the only real check
and why the two tests specified here — Kupiec for unconditional coverage and Christoffersen for
independence and conditional coverage — are the right instruments. VaR is also procyclical: it
rises after a shock because the estimator is fed the shock, which is a property of the estimator,
not of the position. Finally, the number is meaningless without its convention set: horizon,
sign, measure, window, and interpolation method.

**Deeper.** `docs/mathematical_specification.md` §6 closes with the sentence that governs how I
would answer this under challenge: "VaR is not coherent (not subadditive); ES is — this
limitation is stated, not hidden." The subadditivity axiom at issue is `ρ(X+Y) ≤ ρ(X)+ρ(Y)`;
historical VaR violates it for non-elliptical or discrete loss distributions. What the current
tree contributes to the eventual answer is already visible in the primitives:
`stats::autocorrelation` uses the Wallis ("biased") denominator, chosen because that is the
normalisation Christoffersen's statistic is stated with (`docs/phase_reports/phase-01-engineering-foundation.md`
§2, `cpp/src/core/statistics.cpp:81-104`), and `Rng::uniform_index` is an unbiased rejection
integer draw intended for bootstrap resampling (`cpp/src/core/rng.cpp:24-41`). What is not true:
that any VaR, ES, bootstrap interval or backtest p-value exists today. `docs/project_scope.md` §9
lists the risk engine as NOT IMPLEMENTED.

### Q7. What does the Heston model add relative to Black-Scholes?

**30 s.** A second state variable: variance follows a mean-reverting CIR process, and its
correlation `ρ` with the asset drives a leverage effect. That gives stochastic volatility,
skew in the implied surface, fat tails from volatility clustering, and surface dynamics that a
constant-`σ` GBM cannot represent at any calibration. This repository implements Heston
(`stochastic.simulate_heston`, full-truncation Euler) and validates it two ways: against
QuantLib's `AnalyticHestonEngine` to 4.5e-3 worst-case relative, and against the exact `ξ = 0`
collapse to Black-Scholes at 2.1e-3 — the second is the sharper test, because there the oracle
is a closed form rather than another numerical scheme.

**2 min.** Under GBM the risk-neutral terminal density is exactly lognormal, which implies a
flat implied-volatility surface; observed surfaces have a put skew and a level that moves with
spot, and no constant `σ` reproduces both. Heston: `dS = μS dt + √v_t S dW¹`,
`dv = κ(θ − v) dt + ξ√v dW²`, `corr(dW¹, dW²) = ρ`. `κ, θ` set mean reversion and the long-run
variance level, `ξ` is vol-of-vol and controls tail mass and ATM curvature, `ρ` controls skew —
negative `ρ` makes downside moves raise volatility, which is what markets price. Numerically the
model adds two problems that are engineering, not finance: keeping `v ≥ 0` under discretisation,
and quantifying the discretisation bias when the scheme is not exact.

**Deeper.** The plan is written down before the code, and the constraints are strict: v1 may use
full-truncation Euler but must document the discretisation bias rather than claim an exact
simulation; Feller condition `2κθ ≥ ξ²` must be documented; parameter-constraint rejection,
positivity behaviour, limiting sanity and convergence sensitivity are required checks; and if no
reliable closed-form oracle can be established, the model card must state "validation weaker than
Black-Scholes section" (`docs/mathematical_specification.md` §10,
`docs/project_scope.md` §4). The contrast with what BS has today is the point of the sentence:
BS carries L1 identities plus a live QuantLib 1.43 comparison whose worst absolute price error on
the benchmark grid is 1.49e-13 and worst relative error above the notional floor 3.46e-11
(`benchmarks/quantlib/results/pricing_vs_quantlib.json`). Heston has no artifact, no number and
no code in this tree.

---

## 2. Numerical Methods

### Q8. What is discretization error?

**30 s.** The error from solving a nearby problem: a lattice with `N` steps approximates
continuous dynamics, and a path sampled at `steps` points approximates a continuous barrier.
What you claim is an *order*, not a value. Here the CRR lattice is `O(dt)`, so halving `dt`
halves the error; the measured fitted log-log slopes are −0.99 to −1.01 against the theoretical
−1.

**2 min.** Discretisation error is one of three distinct errors, and mixing them up is how
validation becomes theatre. Discretisation: a modelling-side approximation whose size is set by
a step count you chose. Round-off: floating-point representation and reassociation, bounded here
by keeping the core in `double` with compensated summation and no `-ffast-math`. Statistical:
Monte Carlo sampling error, which shrinks as `1/√N` and is reported as an SE rather than bounded
by a tolerance. Three concrete sites in this repository: the lattice (only the `N → ∞` limit is
Black-Scholes), the `steps` argument of `price_path_payoff` (a bias knob, because a barrier
checked at 20 points is a different contract from one monitored continuously), and
finite-difference Greeks (truncation `O(h²)` competing with round-off `εV/h²`).

**Deeper.** Numbers. Lattice convergence fitted over `N = 25…3200` in four regimes: slopes
−0.99405 (SE 0.00313), −1.00544 (SE 0.16209), −0.99244 (SE 0.00405), −0.999674 (SE 0.000157);
relative lattice error at `N = 3200`: 6.58e-05 ATM call, 1.97e-04 OTM call, 7.34e-05 high-vol
call, 8.31e-05 short-dated ATM put (`experiments/pricing_validation/results/summary.json`). The
short-dated put's deviation from −1 is 2.08 of its own standard errors *because its standard
error is tiny* — the residual is the next term of the expansion, and it is reported rather than
smoothed away (`docs/model_cards/crr_binomial.md`). Implementation choices that keep the error
honest: node levels computed as `S·exp((2j − k)·log u)` rather than by repeated multiplication,
so no multiplicative drift accumulates as the tree widens
(`cpp/src/pricing/binomial_crr.cpp:15-19`), and no Richardson extrapolation is applied, so the
`O(dt)` error is reported as-is instead of being hidden (`docs/limitations.md` #11). The barrier
case is validated as a monotone-refinement property, not a value: a 20-step and a 200-step
discrete monitor are compared against each other, with the test comment stating that continuous
monitoring is the limit of finer monitoring and that refining can only raise the touch
probability (`tests/cpp/test_monte_carlo.cpp:170-208`).

### Q9. What is Monte Carlo sampling error?

**30 s.** The error from estimating an expectation with finitely many draws:
`SE = s/√N`, approximately normal by the CLT. It is a standard deviation, not a bias, and it is
the only error a European estimate carries here because the exact GBM terminal transition has no
discretisation bias. Three obligations: report the SE and CI with the price, compute them over
the true independent units, and validate the interval empirically rather than assume it.

**2 min.** The estimator's own variance is not the same object as the payoff's variance: the SE
belongs to the mean of the *independent units*, which is `N` for plain and control-variate
estimators and `N/2` for antithetic pairs. Getting that wrong is the classic way to understate
error by `√2`, and it survives every code review unless something asserts it. Second point: the
interval used here is `V̂ ± z·SE` with `z = N⁻¹(1 − α/2)`, a normal approximation, so its
legitimacy is an empirical question — which is why the coverage study exists. Third: a
mis-stated SE announces itself as a z-score distribution whose standard deviation is far from 1,
so the benchmark reports pooled z-scores, not just prices.

**Deeper.** `cpp/src/monte_carlo/engine.cpp:39-53`: `finish()` computes mean, sample variance,
`iid_units`, SE, and the half-width from `normal_confidence_multiplier`, which is
`inverse_normal_cdf(1 − (1−α)/2)` (`:27-30`). The result struct carries price, SE, confidence
level and bounds, `paths`, `iid_units`, `seed`, sample variance and stddev, fitted
`control_beta`, `runtime_seconds`, method, `measure = "risk_neutral"` and a `note`
(`cpp/include/quantrisk/monte_carlo/engine.hpp:29-45`) — the auditable-estimate requirement from
the Phase 3 prompt. Assertions: half-width equals `z·SE` to 1e-12 relative and the CI midpoint
equals the price to 1e-15, with `z(0.99)` pinned at 2.5758293035489004
(`tests/cpp/test_monte_carlo.cpp:62-75`). Measured validation: nominal 95 %/99 % intervals landed
inside the exact `Binomial(200, level)` 0.5–99.5 % percentile band in 12/12 scenario × path ×
level combinations (example cell: ATM call, 1,000 paths, 95 % — 191 of 200 covered, band
[181, 197]); z-scores of our estimate against QuantLib's analytic price over 492 rows pool to
mean −0.023 / std 1.0139 for antithetic, +0.0503 / std 0.9232 for control variate, +0.0310 /
std 0.9304 for plain, with 96.25 %–98.75 % inside ±2
(`experiments/monte_carlo_convergence/results/summary.json`,
`benchmarks/quantlib/results/monte_carlo_validation.json`). Limitation #17 states the honest
boundary: these are CLT approximations, defensible for a mean of i.i.d. finite-variance payoffs,
not exact, and they would need re-examination for heavy-tailed payoff structures.

### Q10. How did you choose tolerances?

**30 s.** By tier and by theory, before the test was written. Deterministic analytic identities
get rounding-scale bands — the frozen default is `kAnalyticTolerance = 1e-12`. Oracle comparisons
get bands justified by the quantity's own noise floor. Lattice and Monte Carlo checks get theory
bands (`O(dt)`, `n·SE`). Statistical checks get hypothesis-test bands, an exact binomial coverage
window and slope ± k standard errors. What is forbidden is the shortcut: lowering a tolerance or
deleting a failing test to make CI green.

**2 min.** The tiers, as frozen in `docs/validation_protocol.md` §2: analytic 1e-10–1e-12
relative on BS and parity, pinned in the test files with `double` rounding as the justification;
lattice and MC looser and derived from truncation order or `SE ≈ s/√N`; statistical checks
expressed as tests, e.g. coverage inside a binomial band. Both absolute and relative error are
reported for every comparison, because relative error on a deep-OTM option worth 1e-9 is noise.
When a check fails there are exactly three admissible responses, and all three are recorded in
the Phase Report: fix the code, widen the tolerance with a written statistical justification, or
downgrade the claim.

**Deeper.** The two cases I would be pushed on. (1) The finite-difference agreement test: the
first version asserted a 1e-6 relative band; the observed residual for a 1 % spot bump was
1.3e-4, which is not a bug but the correct `O(h²)` truncation term. The fix was to replace the
constant with a Richardson error estimate and to check that the gap falls about 4× when the bump
halves — same discipline then required for MC-vs-analytic comparisons
(`docs/phase_reports/phase-02-deterministic-pricing.md` §8). The measured worst analytic-vs-FD
delta is 1.17e-4 in `experiments/pricing_validation/results/summary.json`, consistent with the
`O(h²)` reading rather than a tolerance failure. (2) Bump sizes carry their own rationale rather
than defaults: spot 1 % of `S`, volatility 0.01 (one vol point) going one-sided if the down-bump
would leave `σ ≥ 0`, rate 1 bp, time 1/252 (one business day) evaluated as `−∂V/∂τ`, chosen so
truncation `O(h²)` and round-off `εV/h²` both sit far below the asserted agreement level
(`cpp/include/quantrisk/pricing/finite_differences.hpp:11-26`). Concrete pinned values in the
suite: `kAnalyticTolerance = 1e-12` (`cpp/include/quantrisk/core/constants.hpp:21`);
QuantLib price check `rel=1e-10, abs=1e-12`, Greeks `rel=1e-8, abs=1e-9`
(`tests/python/test_pricing_vs_quantlib.py:30-31,109,144`); SciPy distribution comparison max
absolute error `< 1e-12` on `x ∈ [-8, 8]` with 1,601 points; MC convergence test uses
"within 4·SE for each of four seeds, zero failures allowed", and one failing seed is reported
rather than replaced.

### Q11. How did you validate the implementation?

**30 s.** Three levels per component, specified in `docs/validation_protocol.md` before any code
existed. L1: analytic identities and limits — parity, `u·d = 1`, `d₂ = d₁ − σ√T`, degenerate
edges, the no-early-exercise theorem. L2: a live independent oracle — QuantLib 1.43 and SciPy,
never pasted. L3: statistical behaviour — convergence rate, interval coverage, measured
variance reduction. Today that is 198 C++ tests (547,845 assertions in 197 cases) and 386
Python tests with the validation oracles installed — 295 without them, because four oracle-gated modules then skip as four records rather than the 69 cases they hold. Every published number has a committed artifact, and a manifest hashes them.

**2 min.** Each level catches a different class of error, which is why all three are run. L1
catches structural mistakes: a sign error breaks put-call parity on every grid point. L2 catches
convention errors that identities are blind to: vega and rho units, day-count mapping, dividend
treatment. L3 catches error-accounting mistakes that no deterministic test can see: an
understated SE looks perfect until you check coverage. Where L2 was not available it is documented
rather than papered over: QuantLib's own `MCEuropeanEngine` could not be constructed with the
installed SWIG bindings, so the artifact records `quantlib_mc_engine_used: false` with the reason,
and the independent yardsticks that *are* used are QuantLib's analytic price (the exact limit)
plus a NumPy/PCG64 simulation.

**Deeper.** L2 for Black-Scholes: 18,816 rows over 7 maturities × 11 strikes × 4 volatilities ×
2 rates × 2 dividend yields, both option types, plus all five Greeks (2,464 price comparisons) —
worst absolute errors: price 1.49e-13, delta 7.97e-15, gamma 1.90e-14, vega 1.75e-13, theta
5.12e-13, rho 5.12e-13; worst relative above the recorded floors (1e-4 price, 1e-6 Greek): price
3.46e-11, rho 1.07e-07. A second oracle path with no QuantLib anywhere: independent
recomputation of the spec formulas using SciPy's normal CDF agrees with the core to ≤ 1e-10
relative over 80 parameter combinations (`tests/python/test_pricing.py`). L1 for the MC engine is
deterministic and has no tolerance to hide behind: pricing `payoff(S_T) = S_T` with the terminal
price as its own control variate must reproduce `e^{−rT}S e^{(r−q)T}` to 1e-12 relative with
`SE < 1e-12` and `beta ≈ 1` to 1e-10, and a constant payoff of 2.0 must return the discount
factor to 1e-15 with zero SE (`tests/cpp/test_monte_carlo.cpp:142-168`). L1 across the boundary:
`cpp/src/tools/dump_reference.cpp` prints compiled-C++ values for seed 42 (256 normals, 64
uniforms, 2,000 `uniform_index(97)` draws, CDF/PDF over 81 points, 999 quantiles, four
statistics) and `tests/python/test_cpp_python_consistency.py` requires the pybind11 results to
match with `rel=0.0, abs=0.0` — the binding cannot quietly re-derive anything. Phase gates and
raw outputs live in `docs/phase_reports/`, and the Phase 1 gate was re-executed on a fresh clone
in `/tmp` with the commit and the full command list recorded.

### Q12. Why use C++ instead of pure Python?

**30 s.** For the hot loops and the memory layout, with a measured number rather than a belief:
46,210,785 paths/s in the C++ core versus 5,728,661 paths/s in an equivalent pure-Python loop —
8.07× on this machine. The same measurement gives vectorised NumPy 110,122,785 paths/s, i.e.
C++ is 0.42× of NumPy for one-normal-per-path work, so the honest claim is narrower than "C++ is
faster than Python".

**2 min.** Three reasons the boundary is where it is. (1) The regime where C++ genuinely wins is
per-path state and `O(paths)` memory: a path-dependent payoff carries a running maximum or
running average per path — which is exactly what `monte_carlo.price_barrier` and
`monte_carlo.price_asian` carry — and NumPy either materialises `paths × steps` doubles or loses
that state entirely. (2) Determinism and typing:
our own Marsaglia polar normal generator, frozen numeric types with `Real = double`, and
domain-validation on the way in — none of which depends on a library whose output can differ
between builds. (3) Python stays the research layer: experiment drivers, CSV/JSON artifacts,
plots, metadata, and later the CLI. The costs are real and recorded: the engine is
single-threaded, there is no quasi-Monte Carlo or Brownian bridge, and every new C++ API needs a
binding plus tests in both suites.

**Deeper.** Measurement conditions, all inside
`benchmarks/performance/results/monte_carlo_speed.json`: terminal-only European call
(`S = K = 100`, `r = 5 %`, `q = 2 %`, `σ = 25 %`, `T = 1`), 200,000 paths per run, 7
repetitions, single-threaded, `CMAKE_BUILD_TYPE=Release`, AppleClang 21.0.0.21000334, arm64.
Means: C++ 0.004328 s (std 1.10e-4), pure Python 0.034912 s (std 2.77e-4), NumPy 0.001816 s
(std 9.89e-5); speedups 8.07× versus pure Python, 0.42× versus NumPy. Three caveats shipped in
the same artifact: the pure-Python baseline uses `random.Random(seed).gauss`, so its stream
differs — the comparison is cost per path, not equality of estimates; the claim is scoped to one
thread; and the artifact prints the three estimates (C++ 11.145962, NumPy 11.114297, Python
11.112294 against the analytic reference 11.123761928058133) with z-scores 0.537, −0.242, −0.292,
so a reader can see three statistically identical answers produced at different cost. A concrete
example of the numerical-softwareness argument: `std::normal_distribution` was rejected because
its output is implementation-defined and libstdc++ and libc++ differ, which is a reproducibility
property no Python-level fix can recover.

---

## 3. Portfolio Theory

Everything in this section is definition plus plan. `docs/project_scope.md` §9 lists portfolio
optimisation as NOT IMPLEMENTED: there are no weights, no shrinkage intensities, no Sharpe
ratios and no frontiers in this repository, and I will not quote any.

### Q13. Why is covariance estimation difficult?

**30 s.** Because the parameter count grows quadratically while the data does not: `n` assets
require `n(n+1)/2` covariances, and estimating them from `T` observations means that as `n`
approaches `T` the sample covariance becomes noisy and eventually near-singular. Then the
optimiser inverts it, which amplifies precisely the eigen-directions where the estimate is
worst.

**2 min.** The specific failure modes worth naming: sampling error concentrated in the small
eigenvalues; non-stationarity, so a sample covariance averages regimes that never coexisted;
correlation instability, which rises exactly in stressed markets; degenerate inputs — a
zero-variance asset, a duplicated asset, near-collinearity; and finite-sample rank deficiency,
where `S` has rank `min(T−1, n)` whatever the true covariance looks like. Phase 6's answer, per
the frozen spec: implement sample, EWMA and shrinkage estimators ourselves; PSD checks; a
conditioning and singularity robustness suite; and scikit-learn's Ledoit-Wolf used only as a
benchmark, never as the engine.

**Deeper.** What is already specified and what is already built are deliberately different
things. Spec §7 freezes the estimator set: sample covariance; exponentially weighted with a
documented `λ`/half-life; shrinkage toward a structured target "in the Ledoit-Wolf spirit".
`docs/validation_protocol.md` §1.1 assigns levels: L1 "PSD checks; shrinkage target sanity", L2
"sklearn Ledoit-Wolf as reference only", L3 "conditioning/singularity suite". Built today: only
scalar statistics — compensated sums, unbiased variance (`/(n−1)`), linear-interpolated quantiles,
tail means and autocorrelation (`cpp/src/core/statistics.cpp`). Eigen is *deliberately* not linked
before Phase 6, because the Phase 1 core had no dense linear algebra to do and an unused
dependency is debt (`docs/project_scope.md` §10, `docs/limitations.md` #8) — so there is no
hand-rolled matrix inverse quietly sitting in the tree.

### Q14. What is shrinkage?

**30 s.** A convex blend of the noisy sample covariance with a structured, better-conditioned
target: `Σ̂ = δF + (1−δ)S`, `δ ∈ [0,1]`. `δ` trades bias — `F` is definitely wrong in some
directions — against variance — `S` is definitely noisy. Ledoit-Wolf's contribution is that `δ`
can be estimated from the data itself, so it is not a knob you tune against the optimiser's
in-sample output.

**2 min.** Candidate targets and what each assumes: scaled identity (no correlation
information, robust), constant-correlation (one shared pairwise correlation), single-factor or
a structured prior such as a diagonal-plus-low-rank form, and time weighting (EWMA) as shrinkage
toward the recent past rather than toward a structure. Why it helps mechanically: the optimiser
applies `Σ⁻¹`, so an eigenvalue floored near zero produces an unbounded position along a
direction the data never identified; blending in `F` raises the floor. Honest limits: shrinkage
repairs `Σ`, not `μ̂`, and the max-Sharpe instability mostly comes from `μ̂`; a `δ` chosen by
looking at in-sample portfolio quality is data snooping.

**Deeper.** Spec §7 records the family — sample, EWMA with documented `λ`/half-life, shrinkage
toward a structured target — and `docs/ecosystem_research.md` §1 keeps sklearn's Ledoit-Wolf on
the benchmark side of the line. Nothing is implemented, so there is no `δ` to report. The
methodological precedent this project already has for the "never score an estimator on the data
that produced it" rule is the control variate: `beta` is fitted on the same sample, so the
engine's own reported variance is mildly optimistic, and the experiment compensates by reporting
*out-of-sample* MSE across a 40-seed ensemble (`docs/limitations.md` #19,
`experiments/variance_reduction/run.py:108-123`, worst realised reduction 1.0 = the plain
baseline by construction, best 40.468×). Same logic, same remedy, one phase earlier.

### Q15. What causes an optimizer to produce unstable weights?

**30 s.** Return estimation error, ill-conditioned covariance, and missing constraints. Max-Sharpe
is `(μ̂ᵀw − r_f)/√(wᵀΣ̂w)`, so assets whose `μ̂` happens to be over-estimated win the objective —
that is error maximisation, and it is the dominant term. Small data changes flip the ranking,
`Σ̂⁻¹μ̂` amplifies the smallest eigendirection, and the result is corner solutions and turnover
rather than a portfolio.

**2 min.** Mechanism paired with mitigation: error maximisation in `μ̂` → shrink the returns or
drop them (min-variance, risk parity, Black-Litterman with an honest prior); ill-conditioning
from near-duplicate assets → shrinkage or ridge on `Σ`, plus eigendirection diagnostics reported
alongside weights; no position limits → the v1 baseline constraints `Σᵢ wᵢ = 1`, `wᵢ ≥ 0`, then
caps and sector/turnover constraints later; single-point fragility → report the frontier and the
constraint residuals, not one "optimal" vector. The caution from PyPortfolioOpt's own
documentation — MVO concentrates weights and min-volatility often beats max-Sharpe out of sample
because of return-estimation error — is recorded in our ecosystem note, not invented here.

**Deeper.** What is frozen for Phase 6 (spec §7): minimise `½ wᵀΣw` subject to `Σw = 1`, `w ≥ 0`,
and `μᵀw ≥ target` for the frontier variant; and the explicit warning that max-Sharpe is **not**
a QP, so any reformulation — e.g. the Charnes-Cooper change of variables that turns the
fractional program into a convex program with a normalisation constraint — has to be documented
before it is used. Validation is residual-based, because "the solver returned" is not "the
constraints hold": protocol §1.1 requires constraint residuals (`Σw − 1`, `w ≥ 0`, target) at L1,
agreement with PyPortfolioOpt *and* cvxpy on identical inputs at L2, and a near-collinear /
singular robustness suite at L3. Status: no optimiser exists in this tree, so there is no weight
vector and no in-sample Sharpe to discuss.

### Q16. What is CVaR optimization?

**30 s.** Minimising Conditional Value-at-Risk — the expected loss in the worst `(1−β)` of
scenarios — over the portfolio weights. Rockafellar-Uryasev makes it tractable: introduce a level
`α` and non-negative auxiliaries `uᵢ`, and the problem becomes linear in them, so CVaR
minimisation is a convex program, unlike VaR minimisation. It is implemented here as
`portfolio.minimise_cvar`, solved by our own two-phase dense primal simplex with Bland's rule
(Phase 6) — no external solver in the library.

**2 min.** Why bother: VaR is a single order statistic, so minimising it is non-convex and can be
gamed by thinning the tail below the cutoff; CVaR averages past the cutoff, so it is convex in
`w` for linear loss maps and it is coherent. Intuition for the formulation: `α` *is* the VaR at
the optimum, and the `uᵢ` are the linearised positive parts `(Lᵢ(w) − α)⁺`; the `1/((1−β)M)`
weighting turns their sum into the conditional tail mean. Whatever is hard about the problem is
the scenario count `M` and the loss model `L(w)` — including the fact that scenario construction is supplied by the stress layer (Phase 7)
rather than inferred, which is why the LP is validated against cvxpy and PyPortfolioOpt on
75 problems rather than against a market outcome: worst relative objective gap 4.48e-9.

**Deeper.** The exact program, as frozen in spec §8 for scenario losses `Lᵢ(w)`, `i = 1..M`, and
confidence `β`:
`min_{w, α, u} α + (1/((1−β)M)) Σᵢ uᵢ` subject to `uᵢ ≥ Lᵢ(w) − α`, `uᵢ ≥ 0`, `Σᵢ wᵢ = 1`, `w ≥ 0`
(plus an optional `μᵀw ≥ target`). At the optimum `α* ≈ VaR_β` and the objective `≈ CVaR_β`, which
equals `ES_β` from spec §6 — so the same tail functional that ES defines is what the optimiser
minimises, and that identity is the reason risk-measure reporting and risk-measure optimisation
must share code. When losses are linear in `w` the whole thing is an LP, which is why it is the
first tail measure worth implementing rather than a solver problem. Benchmark plan:
PyPortfolioOpt's `EfficientCVaR` plus an independent cvxpy formulation on identical scenario
matrices, comparing weights, objective, expected return, volatility, Sharpe, CVaR and constraint
residuals (`docs/ecosystem_research.md` §3, PROJECT_SPEC.md Phase 6).

### Q17. What is risk parity?

**30 s.** Allocation by risk contribution rather than by capital: every asset contributes the
same share of portfolio variance, `wᵢ(Σw)ᵢ = (wᵀΣw)/n` for all `i`. It needs only `Σ`, so it is
immune to the return-estimation error that destabilises mean-variance; the trade-off is that it
trusts volatility and correlation completely and ignores expected return entirely. Defined in
spec §9 for Phase 6; not built.

**2 min.** Consequences worth stating before anyone asks: high-volatility assets get small
weights and low-volatility assets get large ones, so the natural leverage differs per sleeve and
a 60/40 comparison is not meaningful without adjusting for it. Implemented as
`portfolio.risk_parity` by cyclic coordinate descent. Because `μ̂` is absent there is no
error maximisation, which is the main empirical argument for the approach — and the reason it
agrees with the Spinu log formulation to 1.4e-11 on weights, the same order as plain
minimum-variance, while max-Sharpe only reaches 7e-9 because its frontier is flat.
Its failure modes:
assets with low volatility and negative real carry attract large weights; the solution is highly
sensitive to the correlation estimate, and correlations rise in exactly the regimes risk parity is
supposed to defend; and "equal risk contribution" is defined with respect to a variance model, so
shrinkage choices leak into the weights. Solving it: the equal-contribution equations are
non-linear but convex-programming-friendly in log-weights, otherwise fixed-point iteration on
`wᵢ ∝ 1/(Σw)ᵢ`.

**Deeper.** Spec §9 is two sentences and the second one is the standard I would be held to:
`wᵢ(Σw)ᵢ = (wᵀΣw)/n` for all `i`, "Solved numerically; validated against independent
implementation, not against itself." So L1 is the per-asset residual of those equations, L2 is an
independent ERC solve (PyPortfolioOpt's hierarchical/Herfindahl machinery is a relative, not an
exact oracle — the difference has to be documented rather than smoothed), and there is no closed
form to fall back on. Eigen, arriving with Phase 6, is where the log-barrier Newton step would
live. Honest status sentence: nothing in this repository computes a portfolio weight today; the
only risk-shaped code is the pricing lattice/Monte Carlo and the scalar statistics module.

---

## 4. Software Engineering

### Q18. Why pybind11?

**30 s.** Header-only, mature, and its CMake helper does the fiddly extension-module part —
interpreter flags, extension suffix, visibility/LTO — in one line:
`pybind11_add_module(_quantrisk bindings/python_bindings.cpp)`. It exposes the frozen C++ API
directly, which is what keeps the binding thin enough that a formula cannot hide in it. nanobind
is lighter; we chose documented maturity and would revisit only with measured evidence.

**2 min.** Three practical properties. Object semantics: `Rng` and `MonteCarloEngine` are
move-only C++ types holding their own stream, pybind11 exposes them as Python objects whose
lifetime *is* the C++ lifetime, and `py::init<Seed>()` makes the seed an explicit constructor
argument with the documented default. Error semantics: `quantrisk::ValidationError` is registered
with `PyExc_ValueError` as its base, so misuse raises the exception Python users expect while the
C++ tests still catch the typed one. Build integration: the pinned dependency (v2.13.6) is
preferred from the active venv and falls back to a pinned fetch, so scikit-build-core's isolated
build and a bare `cmake --preset dev` resolve the same way.

**Deeper.** The load-bearing decision is what the binding refuses to do. Its header states the
policy — expose frozen C++ APIs and convert containers, never reimplement a formula, add
validation logic, or hold state the core does not own
(`bindings/python_bindings.cpp:1-5`), and `docs/architecture.md` §2 puts the same rule in the
"Must NOT" column for both the bindings and the Python layer. Two guardrails make it enforceable.
(1) Every result field is exposed with `def_readonly`, including `price`, `standard_error`,
`iid_units`, `control_beta`, `runtime_seconds`, `measure` and `note`, so Python cannot mutate an
estimate after the fact, and `price_european` is a pass-through lambda with the identical
signature. (2) `tests/python/test_cpp_python_consistency.py` compares pybind11 output against the
compiled reference tool's own printed values with `pytest.approx(rel=0.0, abs=0.0)`, and a second
test asserts `quantrisk.stats.__name__` starts with `quantrisk._quantrisk` and does not resolve to
a `.py` file — so a Python-side re-implementation would fail the suite, not just the code review.

### Q19. Why separate C++ core and Python orchestration?

**30 s.** Because the jobs are different and one-way. C++ owns everything that produces a
number: one implementation, one precision, one stream. Python owns research ergonomics:
experiment drivers, CSV/JSON artifacts, figures, environment metadata, and later facades and CLI.
The dependency direction is enforced, so Python can be deleted without losing any numerics —
and the C++ core builds and tests without it.

**2 min.** Three reasons this is not ceremony. (1) One-implementation rule: a formula duplicated
in Python and C++ drifts, and the drift surfaces as a benchmark mismatch nobody can attribute;
the layer table in `docs/architecture.md` §2 states the rule and the Phase 1 consistency test
tests it. (2) Testability and offline CI: `ctest` and `pytest` run with no network, and the
optional oracles are absent in CI, where the oracle-marked tests skip rather than fake a pass.
(3) The research layer genuinely needs Python — QuantLib, SciPy, PyPortfolioOpt, cvxpy and
matplotlib are the oracles and the plotting stack, and experiments need file IO plus environment
capture, which belong outside a numerical core. The cost is honest: each new C++ API needs a
binding plus tests in both suites, and the frozen-surface policy in `docs/project_scope.md` §10
means changing one requires a written migration note.

**Deeper.** How the boundary is actually drawn in code. Python: `python/quantrisk/__init__.py`
only re-exports submodules of the compiled extension (`pricing`, `stochastic`, `monte_carlo`,
`stats`) under a docstring stating that every number-producing routine lives in C++;
`python/quantrisk/experiments/metadata.py` supplies `environment()` (compiler, commit, flags,
platform, package versions via `importlib.metadata`), `utc_timestamp()`, `sha256_file()` and
`artifact_manifest()`; `python/quantrisk/plotting/` produces the figures, one of which gained a
series-length guard in Phase 3. C++: no Python header, no network call, no file IO on any numerics
path (`docs/architecture.md` §2, `docs/project_scope.md` §5 rule 3), and oracles "never become
dependencies of the core" (§3). The wheel and the developer path are the same CMake tree, which
is what makes `uv pip install -e .` and `cmake --build --preset dev` build one library rather
than two.

### Q20. How is deterministic reproducibility implemented?

**30 s.** Four things together. Instance-owned streams — `std::mt19937_64` inside `Rng`, no
global state, every stochastic entry point taking an explicit seed. A fully specified normal
generator — our own Marsaglia polar, because `std::normal_distribution`'s output is
implementation-defined. Deterministic arithmetic — `double` only, Neumaier compensated sums in
fixed index order, no `-ffast-math`. And metadata — `build_metadata()` bakes compiler, commit,
architecture, build type and flags into the library, and every artifact carries it plus SHA256
per output file.

**2 min.** Then the boundary of the claim, which I would state before anyone found it:
reproducibility is *per-platform*, not cross-platform. `mt19937_64` and the polar transform are
fully specified, but `log`, `sqrt` and `erfc` are not required to be bit-identical between
libms, so a recorded `(seed, N, parameters, commit, compiler)` tuple replays bit-exactly on the
platform family that produced it and to floating-point noise elsewhere — which is precisely why
`build_metadata()` travels with every artifact. Seeds are values, not ambient state: results
carry `seed`, and the three Phase 3 studies use explicit seed families (`base_seed = 42`;
`50,000 + seed`; `900,000 + seed`; `7,000,000 + seed`) recorded in their summaries.

**Deeper.** Choices with numerical consequences. `uniform01()` is a 64-bit word times the
exactly representable `1/18446744073709551616.0` — no rounding-dependent loop
(`cpp/src/core/rng.cpp:12-22`). `uniform_index(high)` rejects above
`limit = (2⁶⁴−1) − ((2⁶⁴−1) mod high)` so accepted values form whole cycles: unbiased where `%`
alone would bias, and deterministic because the *instance's* state decides the rejection count
(`:24-41`). `standard_normal()` is Marsaglia polar with the partner cached; acceptance
probability `π/4` means the expected uniform pairs per normal is `4/π ≈ 1.27` (`:43-65`), and
`has_cached_normal()` plus `uniform_draws()` are exposed so a caller can see where the stream is.
`inverse_normal_cdf` is Acklam's rational approximation with one Halley refinement — its
`normal_cdf` is `0.5·erfc(−x/√2)`, which keeps relative accuracy deep in the left tail, unlike
`(1+erf(x/√2))/2`. Summation is Neumaier compensated with a fixed index order
(`cpp/src/core/statistics.cpp:10-25`), justified by the Phase 1 test on `[1e16, 1, −1e16]`, where
naive addition returns 0 instead of 1. Reproducibility is asserted, not assumed: same seed ⇒
identical price, SE and sample variance bit-for-bit; different seed ⇒ different price; and
continuing the same engine must *not* restart the stream
(`tests/cpp/test_monte_carlo.cpp:77-95`, mirrored in Python, plus
`tests/cpp/test_gbm.cpp:82-93`). Build-time capture is in `CMakeLists.txt:32-60`, which writes
`git rev-parse --short=12 HEAD` and the compiler/flags into a generated `build_config.hpp`; the
clean-clone gate shows the value in the wild, `git_commit: bcadd60756b4`, `compiler: AppleClang
21.0.0.21000334`, `cxx_flags: (none)` with `Release` supplying `-O3` per configuration.

### Q21. How do you prevent benchmark leakage?

**30 s.** An oracle may be compared against, never consumed. The rules from
`docs/validation_protocol.md` §4, written before Phase 2: oracles run live inside the benchmark
script and outputs are computed, not pasted; no hard-coded oracle number anywhere in `tests/` or
`benchmarks/`; oracle version and configuration go into the artifact; performance claims need
compiler, CPU, path count, repetitions, mean ± std and a baseline on the same machine; failed
experiments are kept and reported. Operationally, CI does not install QuantLib or SciPy, so those
tests skip rather than pretend.

**2 min.** The three leakage modes I am guarding against: pasting a QuantLib price into a test as
the expected value, which makes the test pass forever and validate nothing; tuning a tolerance
until an oracle agrees; and importing an oracle into the core so it silently becomes a
dependency. Counter-measures: oracles live in a separate pip extra and are absent from the
runtime dependencies (`numpy`, `pandas` only); oracle tests use `pytest.importorskip` plus an
`oracle` marker under `--strict-markers`; the dependency graph is one-way with "Oracles never
become dependencies of the core"; and the only reference values pinned in the test suite come
from our own compiled tool, not from an oracle. Negative results are published, not deleted —
the clearest case is that QuantLib's MC engine could not be built here, and the artifact says so
in a field.

**Deeper.** The sharpest example, because the tempting claim was the false one. Textbook CRR and
QuantLib's `BinomialVanillaEngine(process, "crr", N)` are *different* `O(dt)` discretisations of
the same dynamics: at `N = 50` the mutual absolute gap for the ATM case is about 1.3e-4 (model
card), the JSON's worst row bucketed at `steps = 50` is 1.819909 while the well-resolved
`sigma*sqrt(dt) <= 0.25` bucket is 0.456807, and `docs/limitations.md` #12 reads the extreme
corner — 100 % volatility over five years on a coarse tree, gap ~0.46 — honestly: that gap is
*smaller than each lattice's own error against Black-Scholes*. Saying "they agree to 1e-12"
would be false, and asserting a raw threshold on the gap would be arbitrary. So
`tests/python/test_pricing_vs_quantlib.py:151-191` asserts the meaningful property: mutual gap <
0.2 × our own error against the analytic Black-Scholes limit, i.e. the two lattices are far
closer to each other than either is to the limit, which identifies the residual as shared
discretisation error rather than a modelling disagreement. Two related guards. Units were
measured, not assumed: the first benchmark version assumed QuantLib's `vega()`/`rho()` were per
1 percentage point, the measured 0.99 relative error exposed the assumption, and the conventions
are now recorded as measured, agreement ~1e-15 with no rescaling. And one test re-executes the
published benchmark script with `--quick` in a subprocess, asserting `rows == 48`, worst price
and Greek absolute errors `< 1e-9`, the presence of the lattice subset row, a non-empty
`quantlib_version`, and that the CSV still carries `our_price` and `quantlib_price` — so a shipped
artifact cannot rot into something the suite no longer covers. The `lattice_error_ratio_*`
summary keys are explicitly flagged as informative only away from cancellation points (observed
range 1.2e-8 to 766) rather than being quietly dropped from the JSON.

### Q22. How would you scale Monte Carlo to 100× more paths?

**30 s.** Three levers, cheapest first. Parallel streams: each worker owns its own `Rng` with a
distinct seed, accumulates its own sum and sum of squares, and partial results combine in a fixed
order — the no-global-state rule makes this correct by construction. Memory: stop materialising
paths and stream them through a fixed per-worker buffer, because `price_path_payoff` currently
allocates `paths × (steps + 1)` doubles. And buy accuracy before cores: control variate measured
1.93×–40.47× and antithetic 1.12×–2.77× realised-MSE improvement at equal path budget.

**2 min.** Terminal-only European work is embarrassingly parallel and memory-light; at the
measured 46,210,785 paths/s single-threaded, 20,000,000 terminal paths is 0.43 s of the same loop
(arithmetic on the measured rate, which I would re-measure rather than claim). Path-dependent
work is the memory-bound case — the model card bounds path counts at about 1e6 × 250 on a laptop,
so a per-worker buffer plus a running payoff is the first real change, and it is already listed
as Phase 4 technical debt. Reproducibility needs a definition change under parallelism: with
per-thread seeds a run is reproducible as a set of streams plus a fixed reduction order, not as
one interleaved sequence, so both the seed list and the combine order go into the artifact. If
the goal is accuracy rather than throughput, the ranking is variance reduction first, more paths
second.

**Deeper.** What the current code already supports: `Rng` is move-only and instance-owned
(`cpp/include/quantrisk/core/rng.hpp:26-31`), the engine holds it by value, and
`MonteCarloResult` carries `iid_units` alongside `sample_variance`, so combining `k` estimators
with `n_j` units each is arithmetic on reported quantities rather than a re-derivation. What is
explicitly missing, and is in `docs/limitations.md` rather than in a roadmap slide: threads
(#16 — "the speedup claims are explicitly scoped to one thread"), a fill-into-existing-buffer
normal API (#4, still allocating per call in `standard_normal_vector`), batched multi-option
pricing from one simulation, streaming path payoffs (#18), and quasi-Monte Carlo, Brownian
bridge, stratification or moment matching — all deferred, all named. Sobol would change the
convergence story to roughly `O((log N)^d / N)` for well-behaved integrands in low dimension, and
that claim would need its own measured artifact, not a citation. Any 100× statement I make must
satisfy protocol §4 rule 4: compiler, CPU architecture, path count, repetitions, mean ± std and a
pure-Python baseline on the same machine — the exact shape of the JSON the Phase 3 benchmark
already writes.

### Q23. What is the hardest thing the stress layer gets wrong?

**30 s.** The map carries volatility to first order only — `out.volatility = vega * absolute` — so
the moment a scenario moves equity *and* volatility its error stops being cubic and becomes
quadratic. Phase 12 recorded that as a refusal. Phase 13 turned the refusal into a measured bound:
the omitted second-order piece is `vanna·h·k + ½·volga·k²` in closed form, and what remains is
`⅙·g‴(ξ)` along the shock ray, which must lie inside the segment's own range of `g‴`. That
inclusion holds on 132 of 132 joint shocks, out to −30 % equity with +20 volatility points.

**2 min.** The interesting part is what the order argument gets wrong in practice. "Second order"
describes the limit. At the size the repo's own `risk_off` scenario uses, the quadratic term is
+787.96 while the error is −5320.79 — the leading term has the *opposite sign*. What dominates is
`½·V_{SSσ}·h²·k`: gamma evaluated at the base volatility and applied across a move that has already
changed the volatility gamma depends on. It is 7.4× the whole quadratic. Across the grid the largest
omitted piece is that term in 64 cells, the pure-spot cubic in 36 and volga in 32, while the mixed
`vanna·h·k` the order argument singles out is largest *nowhere*. So the cheap fix to this map is
re-striking gamma, not adding vanna and volga — a prioritisation you only get by deriving the terms.

**Deeper.** What I would defend: the interval for `risk_off` is [−6063.95, −4135.87], which excludes
zero, so the *sign* of the published error is proved rather than estimated, and the scenario's
shocks are imported from the stress experiment rather than re-typed so the bound cannot drift from
the thing it bounds. What I would not: the near-cancellation that makes the quadratic small here is
a property of this three-strike ladder — K=90 and K=110 carry vanna of −5089.09 and +5628.57,
leaving 192.33 — so a concentrated book ranks differently. And the direction where the quadratic
vanishes is predicted in closed form but deliberately not verified: locating its empirical
counterpart needs a bracket whose useful width shrinks with the shock, and the shipped scan found
the root at 0.87× the prediction at one scale, 1.81× at another and not at all at a third, which is
a fact about the scan. The probe is in the artifact so the refusal can be checked, not trusted.
Sources: `docs/analysis/two_factor_error_bound.md`, `docs/limitations.md` #67–71,
`experiments/two_factor_error_bound/results/two_factor_bound.json`.

---

## How to verify each claim in this file

Regenerate, then compare. Commands are the ones recorded in the phase reports.

```bash
cmake --preset dev && cmake --build --preset dev && ctest --preset dev   # 198 C++ tests
uv pip install -e . && QUANTRISK_REFERENCE_TOOL=$PWD/build/dev/quantrisk_reference_tool \
  .venv/bin/python -m pytest -q                                          # 319 Python tests
uv run python experiments/pricing_validation/run.py
uv run python experiments/monte_carlo_convergence/run.py
uv run python experiments/variance_reduction/run.py
uv run python benchmarks/quantlib/pricing_validation.py
uv run python benchmarks/quantlib/monte_carlo_validation.py --paths 200000
uv run python benchmarks/performance/monte_carlo_speed.py
```

| Claim in this file | Source to check |
|---|---|
| What exists, and what is deliberately not claimed | `docs/project_scope.md` §9 status table; `docs/validation_matrix.md`; `docs/limitations.md` (66 entries) |
| 190 C++ / 330 Python tests at `v1.0.0`, 198 / 388 now; 53/112 at Phase 2; 31/41 at Phase 1 | `docs/phase_reports/phase-03-monte-carlo.md` §5; `phase-02-deterministic-pricing.md` §5; `phase-01-engineering-foundation.md` §5 |
| BS worst abs 1.49e-13 / rel 3.46e-11; Greeks abs 7.97e-15 … 5.12e-13; rel rho 1.07e-07; 18,816 rows; floors 1e-4 / 1e-6; oracle config (AnalyticEuropeanEngine, Actual365Fixed, day → `days/365`) | `benchmarks/quantlib/results/pricing_vs_quantlib.json` |
| Put-call parity worst residual 7.99e-15; worst analytic-vs-FD delta 1.17e-4 | `experiments/pricing_validation/results/summary.json` (`worst_*` keys) |
| CRR slopes −0.99405 / −1.00544 / −0.99244 / −0.999674 with SEs; relative errors at N = 3200 | `experiments/pricing_validation/results/summary.json` (`crr_convergence_slope`, `final_lattice_relative_error`) |
| Lattice mutual-gap property (`mutual < 0.2 * our_error`); ~1.3e-4 at N = 50; corner gaps 1.819909 / 0.456807 / 0.46 reading | `tests/python/test_pricing_vs_quantlib.py:151-191`; `docs/limitations.md` #12; `docs/model_cards/crr_binomial.md` |
| SciPy agreement `< 1e-12` on `x ∈ [-8, 8]`, 1,601 points; KS on 50,000 normals; chi-square on 80,000 uniforms | `tests/python/test_normal_vs_scipy.py`; `docs/phase_reports/phase-01-engineering-foundation.md` §6 |
| MC log-log slopes −0.6141 ± 0.0888, −0.5855 ± 0.0963, −0.5066 ± 0.1184; path counts 1e3…3e6; `base_seed = 42`; nesting comment | `experiments/monte_carlo_convergence/results/summary.json`; `experiments/monte_carlo_convergence/run.py:60-78,93-95` |
| Coverage 12/12 inside the exact `Binomial(200, level)` band; example cell 191/200 in [181, 197] | `experiments/monte_carlo_convergence/results/summary.json` (`coverage`, `coverage_intervals_inside_binomial_band`); band construction `run.py:184-188` |
| Pooled z-scores vs QuantLib analytic (492 rows, 4 scenarios × 3 methods × 40 seeds, 200,000 paths): means −0.0228 / +0.0503 / +0.0310, stds 1.0139 / 0.9232 / 0.9304, 96.25 %–98.75 % inside ±2; `quantlib_mc_engine_used: false` | `benchmarks/quantlib/results/monte_carlo_validation.json` |
| Out-of-sample MSE reductions: antithetic 1.1155×–2.7741×, control variate 1.9313×–40.468×; 40 seeds; in-sample-`beta` caveat | `experiments/variance_reduction/results/summary.json` (+ `realised_error.csv`); `docs/limitations.md` #19 |
| Speed: C++ 0.004328 s / 46,210,785 paths/s, pure Python 0.034912 s / 5,728,661, NumPy 0.001816 s / 110,122,785; 8.07× and 0.42×; 7 repetitions; three estimates and z-scores; caveats list | `benchmarks/performance/results/monte_carlo_speed.json` |
| Antithetic `iid_units = paths / 2`; odd path count throws; pair product identity to 1e-12; drift not negated | `cpp/src/monte_carlo/engine.cpp:87-97,142-154`; `cpp/src/stochastic/gbm.cpp:74-88,104-109`; `tests/cpp/test_monte_carlo.cpp:96-110`; `tests/cpp/test_gbm.cpp:128-167` |
| Control-variate exactness identity (price to 1e-12, SE < 1e-12, `beta ≈ 1`) and constant-payoff discount factor to 1e-15 | `tests/cpp/test_monte_carlo.cpp:142-168`; `cpp/src/monte_carlo/engine.cpp:57-85` |
| Physical measure is a separate code path, and `mu = r` reproduces the risk-neutral stream bit-for-bit | `cpp/src/stochastic/gbm.cpp:113-127`; `tests/cpp/test_gbm.cpp:170-186`; convention in `docs/project_scope.md` §10 |
| `normal_cdf = 0.5·erfc(-x/√2)`; quantile on the lower half only with the ~6e-12 cancellation argument; tail cutoff `\|x\| ≈ 37` | `cpp/src/math/normal.cpp:15-21,25-38,92-102`; `docs/limitations.md` #2 |
| Own Marsaglia polar instead of `std::normal_distribution` (implementation-defined output); `4/π ≈ 1.27`; `uniform01` = word × 2⁻⁶⁴; `uniform_index` rejection bound; no global RNG state | `cpp/include/quantrisk/core/rng.hpp:11-31`; `cpp/src/core/rng.cpp:12-65`; `docs/phase_reports/phase-01-engineering-foundation.md` §2 |
| Neumaier compensated summation, fixed index order, `[1e16, 1, -1e16]` test; Wallis autocorrelation denominator | `cpp/src/core/statistics.cpp:10-25,81-104`; `docs/phase_reports/phase-01-engineering-foundation.md` §2, §6 |
| `kAnalyticTolerance = 1e-12`; oracle tiers `rel 1e-10 / abs 1e-12` (price) and `rel 1e-8 / abs 1e-9` (Greeks); tolerance rules and the "no tuning to pass" ban | `cpp/include/quantrisk/core/constants.hpp:18-21`; `tests/python/test_pricing_vs_quantlib.py:30-31`; `docs/validation_protocol.md` §2; `PROJECT_SPEC.md` §4 |
| Bump policy (1 % spot, 1 vol point, 1 bp, 1/252, one-sided at σ = 0) and the Richardson replacement of the 1e-6 band | `cpp/include/quantrisk/pricing/finite_differences.hpp:11-26`; `docs/phase_reports/phase-02-deterministic-pricing.md` §8 |
| Binding policy (thin, no formula reimplementation) and exact C++/Python consistency at `rel=0, abs=0` | `bindings/python_bindings.cpp:1-5,215-236`; `tests/python/test_cpp_python_consistency.py` |
| pybind11 v2.13.6 and Catch2 v3.8.1 pinned; `pybind11_add_module`; no `-ffast-math`, `double` core, `-Wall -Wextra -Wpedantic`; presets `dev`/`release`/`ci`; `Release` = `-O3` | `CMakeLists.txt:10-13,82-86,107-110,163-171`; `CMakePresets.json`; `docs/validation_protocol.md` §3 |
| Build metadata baked at configure time (`bcadd60756b4`, AppleClang 21.0.0.21000334, `cxx_flags: (none)`) and the clean-clone gate commands | `CMakeLists.txt:32-60`; `docs/phase_reports/phase-01-clean-clone-run.md` |
| Oracles are an optional extra, CI is offline, oracle tests skip when absent | `pyproject.toml:16-26,51-56`; `.github/workflows/ci.yml`; `docs/validation_protocol.md` §6 |
| VaR / ES definitions, loss convention `L = −R`, Kupiec and Christoffersen requirements, "VaR not coherent" statement | `docs/mathematical_specification.md` §6; `docs/validation_protocol.md` §1.1 |
| Historical-quantile and tail-mean primitives that exist (`quantile_linear`, `mean_of_largest_sorted`) and the sorted-input caveat | `cpp/src/core/statistics.cpp:50-79`; `docs/limitations.md` #3 |
| Mean-variance program, "max-Sharpe is not a QP", covariance estimator list, robustness suite | `docs/mathematical_specification.md` §7; `docs/validation_protocol.md` §1.1 |
| Rockafellar–Uryasev CVaR formulation and `α* ≈ VaR_β` | `docs/mathematical_specification.md` §8 |
| ERC condition `wᵢ(Σw)ᵢ = (wᵀΣw)/n` and "validated against independent implementation" | `docs/mathematical_specification.md` §9 |
| Heston dynamics, Feller condition, full-truncation Euler bias, "validation weaker than Black-Scholes section" | `docs/mathematical_specification.md` §10; `docs/project_scope.md` §4 |
| Eigen arrives in Phase 6, not before; single-thread and no-QMC limits; path-matrix memory bound | `docs/limitations.md` #8, #16, #18; `docs/model_cards/monte_carlo_gbm.md` |

Anything in this file that is not in that table is an opinion about a method, not a result of
this repository — answer it as an opinion.
