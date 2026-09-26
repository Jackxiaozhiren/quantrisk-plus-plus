# QuantRisk++ — Research-Grade C++/Python Quantitative Risk Engine

> A Reproducible C++/Python Engine for Stochastic Pricing, Monte Carlo Simulation, Portfolio Risk, Optimization and Stress Testing

**定位：** 真正具有研究生申请价值的、可验证、可复现、具有数学深度的开源项目。
**非目标：** 不是“看起来像量化”的展示项目，不是股票预测 Dashboard。

目标申请方向包括：

- Financial Engineering
- Financial Mathematics
- Quantitative Finance
- Quantitative Risk Management
- Applied Mathematics
- Statistics
- Data Science

最终希望证明：

1. C++ numerical computing ability
2. Python scientific computing ability
3. stochastic modeling understanding
4. Monte Carlo methodology
5. numerical methods
6. statistical risk modeling
7. optimization
8. reproducible research
9. software engineering
10. model validation / benchmarking

---

## 目录

- [1. 身份与任务](#1-身份与任务)
- [2. 项目最高原则](#2-项目最高原则)
- [3. 成本约束](#3-成本约束)
- [4. 禁止事项](#4-禁止事项)
- [5. 技术栈](#5-技术栈)
- [6. 推荐最终项目结构](#6-推荐最终项目结构)
- [7. 每个阶段必须遵守的工作方式](#7-每个阶段必须遵守的工作方式)
- [Phase 0 — 项目研究、数学边界和架构冻结](#phase-0--项目研究数学边界和架构冻结)
- [Phase 1 — 工程骨架、C++ Core 与 Python Packaging](#phase-1--工程骨架c-core-与-python-packaging)
- [Phase 2 — Black-Scholes、Binomial Tree 与 Greeks](#phase-2--black-scholesbinomial-tree-与-greeks)
- [Phase 3 — Monte Carlo Engine](#phase-3--monte-carlo-simulation-engine)
- [Phase 4 — Path-Dependent Options 与 Stochastic Volatility](#phase-4--path-dependent-pricing--stochastic-volatility)
- [Phase 5 — Risk Engine：VaR / Expected Shortfall](#phase-5--market-risk-engine)
- [Phase 6 — Portfolio Risk & Optimization](#phase-6--portfolio-optimization-engine)
- [Phase 7 — Stress Testing & Scenario Engine](#phase-7--stress-testing-framework)
- [Phase 8 — 免费真实数据层](#phase-8--public-data-integration)
- [Phase 9 — Python API、CLI 与研究体验](#phase-9--python-research-api)
- [Phase 10 — Research Validation、Benchmark 与 Release](#phase-10--final-research-validation--public-release)
- [最终申请导向优化](#最终申请导向优化)
- [最终面试准备材料](#最终面试准备材料)
- [最终成功标准](#最终成功标准)

---

## 1. 身份与任务

你现在是本项目的：

- Principal Quantitative Developer
- Numerical Methods Engineer
- Financial Mathematics Researcher
- C++20 Systems Engineer
- Python Scientific Computing Engineer
- Research Software Engineer
- Verification & Reproducibility Engineer

你的任务不是制作一个“看起来像量化”的展示项目，也不是制作股票预测 Dashboard。

你的任务是和我共同从零构建一个真正具有研究生申请价值的、可验证、可复现、具有数学深度的开源项目：**QuantRisk++**。

完整定位：

**A Reproducible C++/Python Engine for Stochastic Pricing, Monte Carlo Simulation, Portfolio Risk, Optimization and Stress Testing**

---

## 2. 项目最高原则

### 2.1 Correctness > Features

不要追求功能数量。

任何新增模型必须能够被验证。

优先：

```text
少量模型
+
数学定义清楚
+
实现正确
+
有 benchmark
+
有测试
+
有实验
+
有 limitation
```

而不是：

```text
大量金融模型
+
没有验证
```

### 2.2 核心算法必须自己实现

以下内容必须拥有我们自己的实现：

- Black-Scholes analytical pricing
- Binomial option pricing
- Monte Carlo engine
- GBM simulation
- Greeks estimation
- variance reduction
- VaR / Expected Shortfall
- VaR backtesting
- covariance estimation
- mean-variance optimization
- CVaR optimization
- scenario/stress framework

QuantLib、PyPortfolioOpt、SciPy、cvxpy 等只能作为：

- correctness oracle
- external benchmark
- cross-validation reference

严禁直接调用：

```python
QuantLib.price(...)
```

然后声称是 QuantRisk++ 的定价引擎。

---

## 3. 成本约束

除 AI token 外：

**整个项目必须 $0 完成。**

禁止使用：

- paid market data
- Bloomberg
- Refinitiv
- WRDS
- Polygon paid
- paid AWS
- paid GCP
- paid Azure
- paid database
- paid API
- proprietary solver

允许：

- local computation
- GitHub
- GitHub Actions 免费额度
- SEC EDGAR
- FRED / ALFRED 免费 API
- CFTC public data
- freely available research datasets
- synthetic data
- QuantLib
- Eigen
- pybind11
- Catch2
- NumPy
- SciPy
- pandas / Polars
- matplotlib
- statsmodels
- scikit-learn
- cvxpy + open-source solver
- PyPortfolioOpt

如果发现某组件需要付费：

**寻找免费替代方案，不要向我建议付费。**

---

## 4. 禁止事项

严禁：

- 编造 benchmark
- 编造 Sharpe ratio
- 编造 performance improvement
- 编造 test coverage
- 编造 speedup
- 编造研究结论
- 编造 market data
- 编造“production ready”
- 编造“institutional grade”
- 把未来工作写成已经完成
- 用 random output 填 README
- 使用未来信息造成 look-ahead bias
- 隐藏失败实验
- 删除失败测试来让 CI 通过
- 偷偷降低 tolerance 让测试通过
- 把 QuantLib 输出 hard-code 成 expected result

任何 README 中的数字必须对应：

```text
script
→ raw result
→ reproducible artifact
```

---

## 5. 技术栈

默认使用：

```text
Core language:
C++20

Python:
Python 3.12+

Build:
CMake
CMakePresets.json
scikit-build-core

Binding:
pybind11

C++ testing:
Catch2

Python testing:
pytest

Linear algebra:
Eigen

Python numerical:
NumPy
SciPy

Data:
Polars / pandas

Optimization:
自己的基础实现
+
cvxpy 作为验证 oracle

Finance benchmark:
QuantLib

Portfolio benchmark:
PyPortfolioOpt

Formatting:
clang-format
ruff

Static checks:
clang-tidy
mypy where practical

CI:
GitHub Actions
```

优先使用 `uv` 管理 Python 环境。

---

## 6. 推荐最终项目结构

目标结构：

```text
quantrisk/
├── CMakeLists.txt
├── CMakePresets.json
├── pyproject.toml
├── README.md
├── LICENSE
├── CITATION.cff
├── CONTRIBUTING.md
│
├── cpp/
│   ├── include/quantrisk/
│   │   ├── core/
│   │   ├── math/
│   │   ├── stochastic/
│   │   ├── pricing/
│   │   ├── monte_carlo/
│   │   ├── risk/
│   │   ├── portfolio/
│   │   └── stress/
│   │
│   └── src/
│
├── bindings/
│   └── python_bindings.cpp
│
├── python/
│   └── quantrisk/
│       ├── __init__.py
│       ├── data/
│       ├── analytics/
│       ├── experiments/
│       └── plotting/
│
├── tests/
│   ├── cpp/
│   └── python/
│
├── benchmarks/
│   ├── quantlib/
│   ├── pyportfolioopt/
│   └── performance/
│
├── experiments/
│   ├── pricing_validation/
│   ├── monte_carlo_convergence/
│   ├── variance_reduction/
│   ├── var_backtesting/
│   ├── portfolio_optimization/
│   └── stress_testing/
│
├── data/
│   ├── README.md
│   └── sample/
│
├── docs/
│   ├── architecture.md
│   ├── mathematical_specification.md
│   ├── validation_protocol.md
│   ├── reproducibility.md
│   ├── limitations.md
│   └── model_cards/
│
├── paper/
│   ├── technical_report.tex
│   └── references.bib
│
├── scripts/
│
└── .github/
    └── workflows/
```

不要一次创建大量空文件。

目录随着阶段逐渐生成。

---

## 7. 每个阶段必须遵守的工作方式

每次收到一个 Phase Prompt 时：

### Step A — Audit

先检查当前 repository。

回答：

- 当前实现了什么？
- 哪些测试已经存在？
- 哪些接口已经冻结？
- 有没有技术债？
- 有没有与本阶段冲突的设计？

禁止假设不存在的代码。

### Step B — Research

需要外部技术信息时，优先查：

1. 官方数学/统计文献
2. QuantLib
3. pybind11
4. Eigen
5. Catch2
6. scikit-build-core
7. PyPortfolioOpt
8. SEC/FRED/CFTC 官方文档
9. 高质量论文或教材

不要根据随机博客设计核心数学。

### Step C — Plan

编码前先给内部实施方案：

```text
Goal
Mathematical definition
API design
Files affected
Tests
Validation oracle
Failure modes
```

然后直接实施。

不需要因为常规技术决定频繁询问我。

### Step D — Implement

保持：

- modular
- deterministic
- documented
- strongly typed
- reproducible

避免 overengineering。

### Step E — Verify

每阶段必须运行实际测试。

至少包括：

```text
build
unit tests
numerical validation
Python tests
regression tests
```

如果失败：修复。

不要宣布成功直到真实通过。

### Step F — Phase Report

每阶段结束必须报告：

```text
1. Completed
2. Mathematical assumptions
3. Files changed
4. Tests executed
5. Exact test results
6. Numerical validation
7. Remaining limitations
8. Technical debt
9. Ready / Not ready for next phase
```

然后停止。

不要未经允许自动进入下一阶段。

---

## Phase 0 — 项目研究、数学边界和架构冻结

> **Prompt：** 现在执行 **Phase 0 — Project Definition & Architecture Freeze**。
>
> 本阶段禁止实现复杂金融算法。
>
> 目标是把整个项目的研究边界和工程架构设计正确。

### 任务 1：研究现有生态

研究：

- QuantLib
- PyPortfolioOpt
- pybind11
- scikit-build-core
- Catch2

总结：

QuantRisk++ 应该自己实现什么，哪些功能只适合用于 benchmark，哪些内容不应该重复造轮子。

### 任务 2：定义项目研究问题

明确项目回答的核心问题：

> Can a compact, reproducible C++/Python quantitative risk engine reproduce analytical financial results, provide statistically valid risk estimates, and expose transparent numerical behavior across pricing, simulation, portfolio risk and stress testing?

形成 `docs/project_scope.md`，包括：

- motivation
- research questions
- intended users
- non-goals
- architecture
- validation philosophy

### 任务 3：编写 Mathematical Specification v0.1

建立 `docs/mathematical_specification.md`，至少定义：

#### Market model

Geometric Brownian Motion：

```text
dS_t = μ S_t dt + σ S_t dW_t
```

Risk-neutral version：

```text
dS_t = r S_t dt + σ S_t dW_t
```

#### Black-Scholes

定义：

- call price
- put price
- d1
- d2
- assumptions

#### Greeks

定义：

- Delta
- Gamma
- Vega
- Theta

#### Monte Carlo

定义：

```text
V0 = exp(-rT) E^Q[payoff]
```

并定义：

- estimator
- bias
- sampling error
- confidence interval

#### VaR

定义：

```text
VaR_alpha
```

#### Expected Shortfall

定义：

```text
ES_alpha
```

#### Mean-Variance Optimization

定义目标和 constraints。

#### CVaR optimization

给出 mathematical optimization formulation。

本阶段只写规范，不实现。

### 任务 4：确定验证体系

建立三层 validation：

```text
Level 1
Analytical oracle

Level 2
Independent open-source oracle

Level 3
Statistical convergence
```

例如：

- Black-Scholes C++ → analytical equation
- Monte Carlo price → analytical Black-Scholes
- 我们的 pricing → QuantLib
- Portfolio optimizer → PyPortfolioOpt / cvxpy

### 任务 5：确定 deterministic policy

规定：

- RNG seed
- tolerance
- floating-point policy
- reproducibility metadata
- compiler metadata

建立 `docs/validation_protocol.md`。

### Phase 0 Gate

进入下一阶段前必须满足：

- project scope 完整
- mathematical specification 存在
- validation protocol 存在
- architecture diagram 存在
- 没有声称任何尚未实现的功能

然后停止。

---

## Phase 1 — 工程骨架、C++ Core 与 Python Packaging

> **Prompt：** 现在执行 **Phase 1 — Engineering Foundation**。
>
> 目标：建立一个最小但专业的 C++20/Python scientific package。
>
> 本阶段不做完整 pricing model。

### 创建

- CMake build
- scikit-build-core packaging
- pybind11 module
- Catch2
- pytest
- basic CI
- formatting

确保：

```bash
uv sync
uv run pytest
cmake --preset ...
cmake --build ...
ctest ...
```

存在稳定开发路径。

### 创建最小 C++ Core

实现：

```cpp
namespace quantrisk
```

基础 components：

- numeric types
- validation helpers
- constants
- RNG abstraction
- statistics helpers

RNG 至少支持：

```text
std::mt19937_64
fixed seed
user configurable seed
```

必须避免全局随机状态。

### Python Binding Smoke Test

提供最小绑定，例如：

```python
import quantrisk

quantrisk.version()
quantrisk.normal_cdf(0.0)
```

验证 `C++ → pybind11 → Python` 完整工作。

### Testing

C++：Catch2

Python：pytest

至少验证：

- normal CDF
- RNG reproducibility
- invalid input
- Python/C++ consistency

### CI

至少完成：

```text
configure
build
C++ test
Python install
pytest
```

不要追求巨大 CI matrix。

### Phase 1 Gate

必须实现：

```text
clean clone
→ install
→ build
→ import
→ test
```

全部成功。

---

## Phase 2 — Black-Scholes、Binomial Tree 与 Greeks

> **Prompt：** 现在执行 **Phase 2 — Deterministic Pricing Foundation**。
>
> 目标：建立第一个真正的 mathematical finance subsystem。

### Instrument API

设计：

```cpp
OptionType
EuropeanOption
MarketParams
PricingResult
```

要求 input validation：

- spot > 0
- strike > 0
- volatility >= 0
- maturity >= 0

### Black-Scholes

从公式独立实现：

- European call
- European put

同时支持连续 dividend yield。

验证：

- put-call parity
- limiting behavior
- zero volatility edge cases
- near-expiry behavior

### Greeks

analytic：

- Delta
- Gamma
- Vega
- Theta
- Rho

再实现 finite difference versions。

测试 analytic vs finite difference。

### Binomial Tree

实现 Cox-Ross-Rubinstein。

支持：

- European Call
- European Put
- American Call
- American Put

验证 European binomial：

```text
N increasing
→ converges toward Black-Scholes
```

### QuantLib Benchmark

建立 `benchmarks/quantlib/pricing_validation.py`。

QuantLib 只作为 oracle。

自动输出：

```text
model
our_price
quantlib_price
absolute_error
relative_error
```

不能 hard-code QuantLib result。

### Experiment

创建 `experiments/pricing_validation/`，至少研究：

1. strikes
2. maturities
3. volatilities
4. interest rates

生成 reproducible CSV + plots。

### Phase 2 Gate

必须证明：

- BS analytical tests pass
- put-call parity pass
- Greeks numerical check pass
- binomial convergence pass
- QuantLib comparison within justified tolerance

---

## Phase 3 — Monte Carlo Simulation Engine

> **Prompt：** 执行 **Phase 3 — Monte Carlo Simulation Engine**。
>
> 这是项目核心阶段。
>
> 不要把 Monte Carlo 写成一个单独的 for-loop notebook。
>
> 建立可复用 simulation framework。

### GBM Path Engine

实现 exact GBM transition：

```text
S_(t+dt) = S_t exp[(μ - σ²/2)dt + σ√dt Z]
```

Risk-neutral simulation 使用：

```text
μ = r
```

支持：

- terminal-only simulation
- full path simulation
- multiple paths
- configurable time steps
- seed

### Monte Carlo Pricing

支持 European call/put。

输出：

```text
price
standard_error
confidence_interval
num_paths
seed
runtime
```

### Variance Reduction

至少实现：

#### Antithetic Variates

Z 和 -Z。

#### Control Variate

使用具有已知 expectation 的 quantity。

比较：

```text
plain MC
vs
antithetic
vs
control variate
```

### Statistical Validation

必须研究 Monte Carlo error 是否大约表现为：

```text
O(1/sqrt(N))
```

实验：

```text
N = 1e3, 3e3, 1e4, 3e4, 1e5, ...
```

不能只画图。

拟合：

```text
log(error) ~ log(N)
```

检查 slope 是否接近理论值。

### Confidence Interval Coverage

重复独立 simulations，研究 95% CI 是否具有合理 empirical coverage。

### Benchmark

与 Black-Scholes analytical price 以及 QuantLib 比较。

### Performance Benchmark

比较：

```text
C++ implementation
vs
pure Python baseline
```

只有真实测量才能声称 speedup。

记录：

- compiler
- CPU architecture
- paths
- repetitions

### Phase 3 Gate

必须得到：

- convergence experiment
- variance reduction experiment
- confidence interval validation
- reproducibility proof
- performance benchmark

---

## Phase 4 — Path-Dependent Pricing & Stochastic Volatility

> **Prompt：** 执行 **Phase 4 — Path-Dependent Pricing & Stochastic Volatility**。

### Asian Options

实现 Arithmetic Asian option Monte Carlo。

研究：

- discretization
- variance
- control variate possibility

### Barrier Options

实现至少：

- up-and-out
- down-and-out

明确说明 discrete monitoring 和 continuous monitoring 的区别。

### Heston Model

实现 Heston dynamics：

```text
dS = μSdt + sqrt(v)S dW1
dv = κ(θ-v)dt + ξ sqrt(v)dW2
```

相关：

```text
corr(dW1,dW2)=ρ
```

第一版允许使用 **full-truncation Euler**，但必须文档化 discretization bias。

不要假装等于 exact simulation。

### Validation

Heston 至少验证：

- parameter constraints
- reproducibility
- limiting sanity
- path positivity behavior
- convergence sensitivity

如果无法建立可靠 closed-form oracle，明确说：

```text
validation weaker than Black-Scholes section
```

不要过度宣称。

### Phase 4 Gate

重点不是模型数量。

重点是 Heston simulation 的 assumptions 和 numerical limitations 写清楚。

---

## Phase 5 — Market Risk Engine

> **Prompt：** 执行 **Phase 5 — Market Risk Engine**。
>
> 目标：从 pricing engine 进入真正的 risk management。

### Returns

支持：

- arithmetic returns
- log returns

明确两者定义。

### VaR

实现：

- Historical VaR
- Parametric Gaussian VaR
- Monte Carlo VaR

### Expected Shortfall

实现对应：

- historical ES
- Gaussian ES
- Monte Carlo ES

### Bootstrap

使用 bootstrap 获得 VaR / ES uncertainty interval。

避免只给 point estimate。

### Backtesting

实现：

#### Kupiec POF Test

检验 exceedance frequency。

#### Christoffersen Test

检验 exceedance independence / conditional coverage。

必须在文档中给出：

- H0
- statistic
- interpretation
- limitations

### Synthetic Tests

先使用 synthetic returns，证明已知 distribution 下估计量行为符合理论，之后再进入真实数据。

### Phase 5 Gate

必须能够输出：

```text
VaR estimate
ES estimate
uncertainty
violations
Kupiec test
Christoffersen test
```

且全部 reproducible。

---

## Phase 6 — Portfolio Optimization Engine

> **Prompt：** 执行 **Phase 6 — Portfolio Optimization Engine**。

### Covariance

至少实现：

- Sample covariance
- Exponentially weighted covariance
- Shrinkage covariance

可以使用统计文献中的 Ledoit-Wolf 思路。

如果直接调用 sklearn，只能用于 benchmark。

### Mean-Variance

实现 minimum variance portfolio，然后支持 target return constraint。

### Maximum Sharpe

实现合理 numerical formulation。

注意 Sharpe maximization 并非简单 quadratic program。

如果转换问题，必须文档化。

### Long-only constraints

第一版至少：

```text
sum(w) = 1
w_i >= 0
```

之后可选：

```text
max position size
sector constraints
turnover constraints
```

### CVaR Optimization

实现 Rockafellar-Uryasev formulation，支持：

```text
min CVaR
```

### Risk Parity

实现 Equal Risk Contribution。

### Benchmark

和 PyPortfolioOpt / cvxpy 比较。

输出：

```text
weights
expected return
volatility
Sharpe
CVaR
constraint residual
```

### Numerical robustness

专门测试：

- singular covariance
- highly correlated assets
- zero variance asset
- near-collinearity

### Phase 6 Gate

必须证明：

- constraints satisfied
- objective sensible
- benchmark一致
- covariance instability 有明确处理

---

## Phase 7 — Stress Testing Framework

> **Prompt：** 执行 **Phase 7 — Stress Testing Framework**。
>
> 建立独立 stress subsystem。
>
> 不要把 stress testing 写成 if/else demo。

### Scenario Object

设计：

```text
Scenario
Shock
Portfolio
RiskFactor
ScenarioResult
```

### 支持 shocks

例如：

```text
equity -20%
volatility × 2
rates +200bp
rates -100bp
correlation +0.2
credit proxy shock
```

### Scenario Types

支持：

- Deterministic scenario：人为冲击
- Historical-style scenario：基于历史因子变化
- Monte Carlo scenario：来自 stochastic simulation

### Outputs

每个 scenario：

```text
portfolio P&L
VaR change
ES change
volatility change
largest contributors
```

### Attribution

建立 risk contribution / loss attribution，避免只给一个总数字。

### Phase 7 Gate

必须做到：

```text
Scenario
→ explicit assumptions
→ reproducible transformation
→ portfolio impact
→ attribution
```

---

## Phase 8 — Public Data Integration

> **Prompt：** 执行 **Phase 8 — Public Data Integration**。
>
> 核心算法不能依赖网络。
>
> 数据 integration 必须是 optional。

### SEC EDGAR

使用 SEC 官方 JSON/XBRL API，不需要 API key。

实现缓存，遵守 SEC request policy 和 User-Agent 要求。

可取得：

- assets
- liabilities
- cash
- debt
- revenue
- earnings

用途：风险和 stress context。

### FRED / ALFRED

支持：

- policy rates
- Treasury rates
- inflation
- unemployment
- credit spreads
- volatility-related macro series

API key 必须用环境变量，绝不能 commit。

如果没有 key，tests 自动使用 fixture。

### CFTC

可选支持 historical COT public dataset，用于：

- derivatives market context
- positioning experiment

### Reproducibility

所有网络下载必须保存 metadata：

```text
source
download timestamp
series identifier
SHA256
```

不要把大型数据直接 commit 到 GitHub。

### Offline Fixtures

CI 必须完全离线运行。

网络 API 不得成为测试依赖。

---

## Phase 9 — Python Research API

> **Prompt：** 执行 **Phase 9 — Python Research API**。
>
> 目标：让 C++ numerical core 拥有干净 Python interface。
>
> 不要重写 C++ 算法。
>
> Python 是 orchestration layer。

### API examples

目标体验类似：

```python
from quantrisk import BlackScholes

model = BlackScholes(
    spot=100,
    strike=100,
    rate=0.04,
    vol=0.20,
    maturity=1.0,
)

model.call_price()
model.greeks()
```

以及：

```python
from quantrisk import MonteCarloEngine

engine = MonteCarloEngine(seed=42)
result = engine.price_european_call(...)
```

Portfolio：

```python
from quantrisk.portfolio import PortfolioOptimizer
```

Risk：

```python
from quantrisk.risk import RiskEngine
```

Stress：

```python
from quantrisk.stress import ScenarioEngine
```

### CLI

只做少量真正有用的命令：

```bash
quantrisk validate
quantrisk benchmark
quantrisk demo
```

不要做复杂 Web app。

这个项目的价值不是 UI。

---

## Phase 10 — Final Research Validation & Public Release

> **Prompt：** 执行 **Phase 10 — Final Research Validation & Public Release**。
>
> 这是最重要的阶段之一。

### Validation Matrix

建立完整表：

```text
Component
Method
Oracle
Tolerance
Status
Evidence artifact
```

覆盖：

- Black-Scholes
- Greeks
- binomial
- Monte Carlo
- variance reduction
- Heston
- VaR
- ES
- backtesting
- covariance
- optimization
- stress engine

### Benchmark Suite

运行：

```text
correctness benchmarks
statistical experiments
performance benchmarks
```

结果保存：

```text
JSON
CSV
Markdown
plots
```

必须由脚本自动生成。

### Frozen Evidence

创建：

```text
evidence/
manifest.json
```

对关键输出生成 SHA256。

保证 README 中的数字能追溯。

### Technical Report

完成 **Design and Validation of a Reproducible C++/Python Stochastic Risk Engine**，建议章节：

```text
1 Introduction
2 Mathematical Background
3 Software Architecture
4 Pricing Models
5 Monte Carlo Methods
6 Market Risk Estimation
7 Portfolio Optimization
8 Stress Testing
9 Numerical Validation
10 Performance Evaluation
11 Limitations
12 Reproducibility
```

### README

README 开头不要堆功能。

结构优先：

```text
What QuantRisk++ is
Why it exists
30-second example
Mathematical scope
Validation
Benchmark
Architecture
Experiments
Reproducibility
Limitations
Installation
```

### GitHub Release

建立 `v1.0.0`，包含：

- tagged source
- release notes
- frozen evidence
- technical report
- CITATION.cff

### Final integrity audit

检查：

#### Code

- no fake implementation
- no dead feature
- no secret
- no hardcoded benchmark

#### Math

- formulas consistent
- assumptions explicit
- units correct
- risk-neutral vs physical measure clearly separated

#### Statistics

- uncertainty reported
- no unjustified causal claims
- no cherry picking

#### Finance

- no claim of guaranteed return
- no trading recommendation
- no misleading backtest

#### Reproducibility

- fresh clone works
- fixed experiment commands work
- README numbers reproducible

---

## 最终申请导向优化

所有核心功能完成以后，再执行一次：**Graduate Admissions Portfolio Audit**

请站在以下项目招生委员会视角审查：

```text
Financial Engineering
Financial Mathematics
Quantitative Finance
Applied Mathematics
Statistics
Data Science
```

回答：

```text
1. 这个项目证明了申请者哪些能力？
2. 哪些部分最有研究生水平？
3. 哪些部分看起来仍像普通本科课程作业？
4. 哪些功能只是工程复杂度，没有学术申请价值？
5. Mathematical depth 是否足够？
6. Statistical rigor 是否足够？
7. C++ 是否真正用于 numerical core？
8. 是否能够证明 reproducibility？
9. README 是否能让 professor 在3分钟内理解价值？
10. 哪3项改进最能提高申请竞争力？
```

根据审计结果进行最后一次精简，而不是继续无止境增加功能。

---

## 最终面试准备材料

完成项目以后，创建 `docs/interview_defense.md`。

我要能够脱离 AI，自行回答至少以下问题：

### Mathematical Finance

- Why does Black-Scholes use risk-neutral pricing?
- What assumptions does GBM make?
- Why does Monte Carlo error decrease approximately as 1/sqrt(N)?
- Why do antithetic variates reduce variance?
- What is the difference between VaR and Expected Shortfall?
- Why can VaR be problematic as a risk measure?
- What does the Heston model add relative to Black-Scholes?

### Numerical Methods

- What is discretization error?
- What is Monte Carlo sampling error?
- How did you choose tolerances?
- How did you validate the implementation?
- Why use C++ instead of pure Python?

### Portfolio Theory

- Why is covariance estimation difficult?
- What is shrinkage?
- What causes an optimizer to produce unstable weights?
- What is CVaR optimization?
- What is risk parity?

### Software Engineering

- Why pybind11?
- Why separate C++ core and Python orchestration?
- How is deterministic reproducibility implemented?
- How do you prevent benchmark leakage?
- How would you scale Monte Carlo to 100× more paths?

每个问题提供：

- 30秒版本
- 2分钟版本
- deeper technical version

但不得背诵 AI 套话。

目标是让我真正理解。

---

## 最终成功标准

本项目不以：

```text
代码行数
feature count
网页漂亮程度
```

作为成功标准。

而以：

```text
数学正确
+
数值验证
+
统计严谨
+
C++实现
+
Python usability
+
benchmark
+
reproducibility
+
technical report
```

作为成功标准。

最终希望一个招生委员会成员看到项目后能够合理形成这样的判断：

> This applicant can move beyond using machine-learning libraries and independently work with mathematical models, numerical algorithms, statistical validation, and research-grade scientific software.

这才是 QuantRisk++ 的最终目的。
