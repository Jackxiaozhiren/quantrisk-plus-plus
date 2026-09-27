# Phase 9 Report — Python Research API and CLI

Date: 2026-09-27 · Branch: `main` · Status after this phase: **complete and verified**
Research question answered: *can the C++ core be used through the interface a researcher
actually wants, without Python ever getting a second chance to be wrong?*

## 1. Completed

- **The four import forms PROJECT_SPEC.md names**, all of which failed before this phase
  and all of which now work verbatim:
  `from quantrisk import BlackScholes`, `from quantrisk import MonteCarloEngine`,
  `from quantrisk.portfolio import PortfolioOptimizer`, `from quantrisk.risk import
  RiskEngine`, `from quantrisk.stress import ScenarioEngine`.
- **Five facades** (`python/quantrisk/api.py`): `BlackScholes`, `MonteCarloEngine`,
  `PortfolioOptimizer`, `RiskEngine`, `ScenarioEngine`.
- **Eight Python faces** for the C++ submodules (`stats`, `special`, `stochastic`,
  `monte_carlo`, `pricing`, `risk`, `portfolio`, `stress`) plus `_reexport.py`.
- **The `quantrisk` console script** with exactly the three commands the spec asks for:
  `validate`, `benchmark`, `demo`. No web app.
- **19 new tests**, including one that runs a fresh interpreter to prove `import
  quantrisk` does not pull in the network-dependent data layer.

Suite after this phase: **190 CTest entries, 546,943 assertions in 189 Catch2 cases,
310 pytest tests.**

## 2. Mathematical assumptions

None. This phase introduces no model and computes nothing. Where a default was needed the
facade defers to the core rather than choosing: `finite_difference_greeks` uses the core's
own `BumpPolicy` defaults, and `bootstrap_ci(block_length=0)` means "ask the core for its
`round(n^(1/3))` default", not "assume one here".

## 3. Files changed

| Path | Role |
| --- | --- |
| `python/quantrisk/api.py` | the five facades |
| `python/quantrisk/_reexport.py` | copies a core submodule's public names into its Python face |
| `python/quantrisk/{stats,special,stochastic,monte_carlo,pricing,risk,portfolio,stress}.py` | the Python faces |
| `python/quantrisk/__init__.py` | imports the faces; exports the facades; documents why `data` is not imported |
| `python/quantrisk/cli.py` | `validate` / `benchmark` / `demo` |
| `pyproject.toml` | `[project.scripts] quantrisk = "quantrisk.cli:main"` |
| `tests/python/test_research_api.py` | 19 tests |
| `tests/python/test_cpp_python_consistency.py` | the guard strengthened below |
| `docs/architecture.md` | §2 records the Python-face rule |

## 4. Tests executed

```bash
uv run pytest -q
uv run pytest tests/python/test_research_api.py -q
uv run quantrisk validate && uv run quantrisk validate --json
uv run quantrisk benchmark --iterations 5000
uv run quantrisk demo
uv run cmake --build --preset dev && ./build/dev/quantrisk_tests && ctest --test-dir build/dev
find cpp bindings tests/cpp -name '*.cpp' -o -name '*.hpp' | sort |
  xargs uv run clang-format --dry-run --Werror
uv run ruff check . && uv run ruff format --check .
```

## 5. Exact test results

```
310 passed in 6.83s                                    (pytest, full suite)
19 passed                                              (the research API file)
All tests passed (546943 assertions in 189 test cases)  (C++, unchanged)
100% tests passed out of 190
quantrisk validate -> 7/7 checks passed, exit 0
ruff check .       -> All checks passed!
ruff format --check . -> 80 files already formatted
clang-format       -> clean
```

## 6. Numerical validation

The claim is "Python orchestrates", so validation is about delegation, not agreement:

| Claim | Check | Result |
| --- | --- | --- |
| Facades do not recompute | `BlackScholes.call_price()` vs `pricing.black_scholes(...).price` | **bit-identical**, `==` not `approx` |
| Renaming did not change the maths | `MonteCarloEngine(seed=99).price_european_call(...)` vs the core's `price_call` at the same seed | price, standard error and CI bound all bit-identical |
| Argument reshaping is lossless | flat vs nested covariance through `PortfolioOptimizer` | identical weights and variance |
| Every face is backed by the extension | `module.__core__ is _quantrisk.<name>` for all eight | holds |
| The faces contain no numerics | AST walk rejects `BinOp`, `Compare`, `For`, `While` in each shim | clean |
| `import quantrisk` excludes the data layer | fresh interpreter prints `sys.modules` membership | `False False`; forcing the import gives `True True`, so the probe discriminates |
| The CLI's own claims hold | `validate` exits 0; `--json` parses; `demo` prints all five sections; exit 1 vs 2 distinguished | all pass |

**One guard was replaced, and it was replaced with a stronger one.**
`test_statistics_module_is_not_a_python_reimplementation` used to assert
`quantrisk.stats.__name__.startswith("quantrisk._quantrisk")` and that `__file__` was not a
`.py`. Phase 9 makes both conditions false *by design*, so the test failed. Rather than
delete it, the assertion moved to the invariant it was standing in for: every callable's
`__module__` must be the extension, and the shim's syntax tree must contain no arithmetic or
control flow. That was verified falsifiable — appending `mean_of_sample = sum([1,2]) / 2` to
`stats.py` makes it fail, and the old `__name__` check would have passed that edit.

**One CLI check was rewritten rather than retuned.** The first draft compared analytic and
finite-difference delta against a fixed 5e-5 gap. It failed at 6.39e-5 — which is the
correct truncation error for the core's default 1 % spot bump, so the bound had been
guessed. The replacement asserts that halving the bump shrinks the gap by a factor of four,
measured across two independent halvings: gaps 6.39e-05 → 1.60e-05 → 3.99e-06, ratios 4.00
and 4.00. No magnitude is asserted and there is no constant left to tune.

`validate` is not a pytest duplicate. It runs against an installed wheel, so it checks the
build a user actually has — including that the compiled extension reports the commit it was
configured at, which the header line prints.

## 7. Remaining limitations

Recorded as `docs/limitations.md` entries 53–55.

1. **The facades cover the documented entry points, not the whole core.** Heston, Asian and
   barrier pricing, and the LP solver are reachable only through the submodule functions,
   not through a facade.
2. **`validate` checks seven identities, not the suite.** It is a smoke test for an
   installed build; correctness at breadth is what the 190 CTest entries and 310 pytest
   tests are for.
3. **`benchmark` measures one machine and compares to nothing.** Deliberately: the oracle
   comparisons live in `benchmarks/` with committed artifacts, and a CLI printing a second,
   uncited figure next to them would create two sources of truth for one claim.

## 8. Technical debt

- `_reexport.copy_core_names` copies eagerly at import. Cheap (eight modules, ~130 names)
  but it means `import quantrisk` binds every core symbol into every face whether used or
  not. A `__getattr__` fallback would be lazier and would also let `dir()` stay honest —
  not worth the indirection at this size, so it is noted rather than done.
- `MonteCarloEngine.price_european_put` pops its keyword arguments, which works but is
  less readable than the explicit form used by `price_european_call`. Unifying them means
  a shared `_market_from_kwargs`; deferred until a second caller needs it.
- The shim files are generated-shaped but hand-committed. If a ninth submodule appears,
  someone must remember to add the file; a build-time generation step would remove that.
- Carried forward from Phase 8: `fixtures.available()`'s extension-free naming, and
  `describe_environment()`'s weak `cache_writable` proxy.
- Still open from earlier phases: `-Wall -Wextra -Wpedantic` covers `quantrisk_core` only,
  not tests or bindings.

## 9. Gate

| Requirement (PROJECT_SPEC.md §Phase 9) | Verdict | Evidence |
| --- | --- | --- |
| Clean Python interface over the C++ core | **met** | five facades with the keyword shapes the spec writes out, all examples run verbatim |
| Do not rewrite the C++ algorithms | **met and enforced structurally** | bit-identical delegation tests; an AST walk that rejects arithmetic and control flow in every shim; every callable's `__module__` is the extension |
| Python is the orchestration layer | **met** | `api.py` contains argument marshalling and delegation only |
| `BlackScholes(spot=…, strike=…, rate=…, vol=…, maturity=…)` with `.call_price()` / `.greeks()` | **met** | test runs the snippet as written |
| `MonteCarloEngine(seed=42).price_european_call(...)` | **met** | the core's `price_call` is exposed under the spec's name, bit-identical at the same seed |
| `quantrisk.portfolio.PortfolioOptimizer` | **met** | five solvers behind one constructor |
| `quantrisk.risk.RiskEngine` | **met** | measures, bootstrap interval, backtest; `repr` states the `L = −R` convention |
| `quantrisk.stress.ScenarioEngine` | **met** | deterministic, historical and Monte-Carlo runs; validates the book on construction |
| CLI with `validate` / `benchmark` / `demo` only | **met** | three subcommands, no others |
| No complex web app | **met** | no server, no UI, no new dependency |
| Nothing paid for (§3) | **met** | zero new dependencies; stdlib `argparse` for the CLI |
| No fabricated number (§4) | **met** | `benchmark` prints only live measurements and names the machine; the guessed 5e-5 tolerance was replaced by a convergence ratio rather than relaxed |

**Gate: PASS.** Phase 9 is complete and verified. Next: Phase 10 — the validation matrix,
the benchmark suite run, the evidence manifest, the technical report, and the release.
