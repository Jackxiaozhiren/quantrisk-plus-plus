# QuantRisk++ — Mathematical Specification v0.1 (Phase 0)

Date: 2026-09-25 · Status: **SPEC ONLY — no code implements this yet.**
Conventions here are normative for all later phases. Any deviation must be
documented with reason, evidence, and updated formulas.

## 0. Conventions and notation

- Time `T ≥ 0` in **years** (ACT/365 to be frozen in Phase 8; until then all
  experiments use year fractions directly, no day-count inference).
- Rates `r` (risk-free), dividend yield `q`: continuously compounded, annualized.
- Volatility `σ ≥ 0` annualized. `S > 0` spot, `K > 0` strike.
- `N(·)` = standard normal CDF, `φ(·)` = standard normal PDF.
- Measures: `P` = physical (real-world, used for risk estimation on returns);
  `Q` = risk-neutral (used for pricing). **Never mix them silently.**
  Pricing discounts at `r` under `Q`; risk estimation (VaR/ES) works under `P`
  on observed/simulated return distributions.
- Currency units: prices in same currency as `S, K`; Greeks per unit of the
  underlying unless stated; Theta per **year**; Vega per **unit** volatility
  (1.00 = 100 vol points; implementation must state any 1% rescaling explicitly).
- Precision: core computations in `double`; tolerances per `validation_protocol.md`.

## 1. Market model — Geometric Brownian Motion

Physical measure:

```text
dS_t = μ S_t dt + σ S_t dW_t^P,   S_0 > 0
```

Risk-neutral measure (pricing):

```text
dS_t = r S_t dt + σ S_t dW_t^Q        (with dividend yield: drift (r − q))
```

Exact solution (constant coefficients, transition used by the Phase 3 engine):

```text
S_{t+dt} = S_t · exp[(μ − σ²/2)·dt + σ·√dt·Z],   Z ∼ N(0,1)
```

Risk-neutral simulation sets `μ = r` (resp. `r − q` with dividends).
Assumptions documented as limitations: constant `σ`, constant `r`, continuous
trading, no transaction costs, no jumps, no stochastic volatility (until Heston,
Phase 4), log-returns exactly normal over any horizon.

## 2. Black-Scholes (European, with continuous dividend yield)

For `T > 0, σ > 0`:

```text
d1 = [ln(S/K) + (r − q + σ²/2)·T] / (σ·√T)
d2 = d1 − σ·√T

Call(S,K,T,r,q,σ) = S·e^(−qT)·N(d1) − K·e^(−rT)·N(d2)
Put(S,K,T,r,q,σ)  = K·e^(−rT)·N(−d2) − S·e^(−qT)·N(−d1)
```

Required edge cases (implementation + tests, Phase 2):

- `T = 0`: Call = max(S−K, 0), Put = max(K−S, 0) (discounting collapses).
- `σ = 0`: deterministic forward: Call = max(S·e^(−qT) − K·e^(−rT), 0),
  Put = max(K·e^(−rT) − S·e^(−qT), 0).
- Put-call parity (must hold for every implementation):
  `Call − Put = S·e^(−qT) − K·e^(−rT)`.
- Limiting behavior: deep ITM/OTM → intrinsic/discounted bounds; large `σ` sensitivity.

BS assumptions (listed in every model card; violations are future work, not hidden):
lognormal prices, constant `σ`/`r`, European exercise, frictionless market,
no arbitrage, continuous hedging.

## 3. Greeks (analytic definitions; finite differences cross-check in Phase 2)

With `q` (set `q = 0` for non-dividend case):

```text
Δ_call = e^(−qT)·N(d1)
Δ_put  = e^(−qT)·(N(d1) − 1)
Γ      = e^(−qT)·φ(d1) / (S·σ·√T)            (same for call and put)
Vega   = S·e^(−qT)·φ(d1)·√T                  (per unit σ)
Rho_call =  K·T·e^(−rT)·N(d2)
Rho_put  = −K·T·e^(−rT)·N(−d2)
Theta_call = −S·e^(−qT)·φ(d1)·σ/(2√T) + q·S·e^(−qT)·N(d1) − r·K·e^(−rT)·N(d2)
Theta_put  = −S·e^(−qT)·φ(d1)·σ/(2√T) − q·S·e^(−qT)·N(−d1) + r·K·e^(−rT)·N(−d2)
```

Theta is `∂V/∂T` **negated**? Convention frozen here: Theta = `−∂V/∂τ` where
`τ = T − t` is time to expiry (market convention: decay per calendar year,
typically negative for long options). Finite-difference checks use central
differences with documented step sizes; analytic-vs-bump agreement is a
Level-1 validation.

## 4. Binomial tree — Cox-Ross-Rubinstein (Phase 2 boundary)

Per-step (`N` steps, `dt = T/N`):

```text
u = exp(σ·√dt),  d = 1/u,  p = (exp((r−q)·dt) − d) / (u − d)
```

European rollback = risk-neutral expectation discounted; American = max(exercise,
continuation) at each node. Requirement: European binomial → BS as `N` grows
(convergence study, not a single N). American call on non-dividend stock must
equal European (no-early-exercise theorem) — a built-in sanity test.

## 5. Monte Carlo pricing (Phase 3 boundary)

Risk-neutral pricing identity:

```text
V0 = e^(−rT) · E^Q[payoff(S_T)]        (path-dependent: payoff of full path)
```

Estimator over `N` i.i.d. draws:

```text
V̂_N = e^(−rT) · (1/N)·Σ_{i=1..N} payoff_i
SE(V̂_N) = s / √N,   s = sample std of discounted payoffs
95% CI  = V̂_N ± 1.96·SE   (CLT-based; coverage empirically checked in Phase 3)
```

Defined terms: **bias** = `E[V̂] − V0` (discretization/monitoring bias for
path-dependent and Heston cases; zero for exact-GBM European); **sampling error**
∼ `O(1/√N)`; **standard error** as above. Variance reduction (antithetic `Z/−Z`;
control variate with known expectation) must report variance ratios on identical
seeds, never cherry-picked runs. Convergence experiment fits
`log(error) ≈ a − 0.5·log(N)` and checks slope ≈ −0.5.

## 6. Risk — VaR and Expected Shortfall (Phase 5 boundary)

Loss convention frozen here: `L = −R` for returns (positive = loss).
For confidence level `α ∈ (0,1)` (e.g. 0.95, 0.99):

```text
VaR_α  = inf{l : P(L ≤ l) ≥ α}          (α-quantile of the loss distribution)
ES_α   = E[L | L ≥ VaR_α]               (continuous case; tail mean of losses)
```

Estimators to implement: historical (empirical quantile/tail mean), parametric
Gaussian (closed form from `μ, σ`), Monte Carlo (quantile of simulated losses).
Uncertainty via bootstrap (block bootstrap documented for time dependence).
Backtesting: Kupiec POF (unconditional coverage, H0: violation rate = 1−α) and
Christoffersen (independence + conditional coverage) with statistics, H0,
interpretation, and limitations written in docs. Synthetic-distribution checks
precede any real-data use. VaR is not coherent (not subadditive); ES is — this
limitation is stated, not hidden.

Returns definitions (frozen):

```text
arithmetic: R_t = (P_t − P_{t−1}) / P_{t−1}
log:        r_t = ln(P_t / P_{t−1})
```

## 7. Portfolio — mean-variance (Phase 6 boundary)

With expected returns `μ ∈ R^n`, covariance `Σ ⪰ 0`, weights `w`:

```text
minimize    (1/2)·wᵀΣw            (equivalently wᵀΣw; implementation states which)
subject to  Σ_i w_i = 1
            w_i ≥ 0               (long-only v1; caps/sectors/turnover later)
            μᵀw ≥ target          (for target-return frontier; min-volatility omits it)
```

Max-Sharpe `(μᵀw − rf)/√(wᵀΣw)` is **not** a QP — reformulation or numerical
method must be documented. Covariance estimators: sample, exponentially weighted
(EWMA with documented λ/half-life), shrinkage toward structured target
(Ledoit-Wolf spirit; sklearn only as benchmark). Robustness suite: singular Σ,
near-perfect correlation, zero-variance asset, near-collinearity.

## 8. Portfolio — CVaR optimization (Rockafellar–Uryasev, Phase 6 boundary)

For scenario losses `L_i(w)` (`i = 1..M`), confidence `β`:

```text
min_{w, α, u}   α + 1/((1−β)·M)·Σ_i u_i
s.t.            u_i ≥ L_i(w) − α,   u_i ≥ 0,
                Σ_i w_i = 1,  w ≥ 0   (+ optional target-return constraint)
```

At optimum, `α* ≈ VaR_β`, objective `≈ CVaR_β` (= ES_β). Linear when losses are
linear in `w`; formulation stays convex and solver-friendly.

## 9. Risk parity / ERC (Phase 6 boundary, definition)

Equal-Risk-Contribution target: `w_i·(Σw)_i = (wᵀΣw)/n` for all `i`
(each asset contributes equally to portfolio variance). Solved numerically;
validated against independent implementation, not against itself.

## 10. Heston preview (Phase 4 boundary — NOT validated here)

```text
dS_t = μ·S_t·dt + √v_t·S_t·dW¹_t
dv_t = κ(θ − v_t)·dt + ξ·√v_t·dW²_t,   corr(dW¹,dW²) = ρ
```

Feller condition `2κθ ≥ ξ²` documented; v1 uses full-truncation Euler with
**documented discretization bias**; positivity, parameter-constraint, and
convergence-sensitivity checks required. If no reliable closed-form oracle is
established, docs must state `validation weaker than Black-Scholes section`.

## 11. Out of scope for v0.1 (explicit)

American closed forms, discrete dividends, term-structure rates, stochastic
rates, jumps, transaction-cost-aware hedging, intraday microstructure — all
deferred. Adding any requires extending this spec first (spec-before-code rule).
