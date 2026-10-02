# Phase 17 — the check audit finding 43 said to write

Date: 2026-10-02. Predecessor: Phase 16 (`phase-16-fourth-order-crossing.md`), whose §8 item 1 proposed
this. No `PROJECT_SPEC.md` phase number: this phase answers a technical-debt entry the repository
published about itself, in the same shape as Phase 14 ("the checks Phase 13 wrote down but did not
enforce"). Repository version is unchanged (`1.6.0`); the tag still names `b4e4bea`, and nothing here is
claimed to be inside that release.

## 1. Completed

1. **The header becomes a witness.** `tests/python/test_extension_surface_parity.py` gained a third
   direction. The file already compared the compiled extension against what
   `bindings/python_bindings.cpp` *declares*, both ways; finding 43's defect — a pybind class registered
   and its function not — is invisible to that pair, because the declaration the binary lacked was absent
   from the source too. Only the header knows the function exists. So the guard now reads every
   `cpp/include/quantrisk/**/*.hpp` (29 headers) and claims that each namespace-scope function marked
   `[[nodiscard]]` is reachable from Python or says otherwise at its own declaration.
2. **The disclaimer convention, with the route checked.** A declaration the core does not intend as a
   Python entry point carries `// python: internal -- <reason>` or `// python: via <target> -- <reason>`
   immediately above it. `via` is not prose: the guard resolves it against the bindings, so
   `via crr_binomial` verifies that `crr_binomial` is really registered and
   `via RiskEstimate.standard_error` verifies the bound struct really has that member. Three rot
   directions are policed besides the missing one — a marker in the wrong shape, a marker on a function
   that is in fact bound, and a marker standing above nothing.
3. **24 declarations disclaimed across 11 headers, all with reasons read from the code.** Five
   `to_string` enum stringifiers (pybind binds the enums themselves), four `crr_*` and two
   `black_scholes_call`/`_put` conveniences over the generic bound form, five single-Greek finite
   differences over `finite_difference_greeks`, two per-path payoff steps over `price_asian`/
   `price_barrier`, three Black-Scholes internals (`is_degenerate`, `d1`, `d2`), two stress-engine steps
   (`resolve_moves`, `contribute`), and `quantile_standard_error`, whose number reaches Python as
   `RiskEstimate.standard_error`.
4. **The residual is an inventory, not a blind spot.** The claim keys on the attribute, and the attribute
   is not applied uniformly across the core, so a namespace-scope function *without* it and without a
   binding would be outside the claim. A second test enumerates exactly those and pins the set to one
   name (`stats::quantile_linear`), with a plant proving the enumerator is not fooled by
   `std::numeric_limits<Real>::epsilon()` (a call in an initialiser) or `require_finite(value, name);`
   (a call inside an inline body).
5. **Falsifiability, three ways.** In-memory: finding 43's own shape (a new core function, neither bound
   nor marked) makes the new claim name it while the Phase 14 two-way comparison stays silent — the
   differential is asserted in the test, not argued in prose. On disk: `scripts/run_mutation_suite.py`
   carries a 22nd plant, `core-declares-a-function-nobody-binds`, which edits a real header and must be
   rejected by this guard's node.
6. **The documents.** Audit addendum closing finding 43 (and the two things the claim does *not* cover),
   limitation #80, the count of numbered limitations carried by the six live documents that quote it,
   `docs/reproducibility.md` and `docs/limitations.md` #79(d)-(e) restored to the family-declared gate
   (an earlier bulk edit had reverted them), `docs/interview_defense.md` Q27 and its citation row, this
   report.

## 2. Mathematical assumptions

None. This phase changes no numerical code path: the header edits are comments, and the extension's
compiled behaviour is the same one `v1.6.0` was tagged with (`ctest` re-run to prove it, §4).

## 3. Files changed

| file | change |
|---|---|
| `tests/python/test_extension_surface_parity.py` | a reading-order comment/literal masker, a namespace view that blanks type and function bodies, the attribute scan, the disclaimer parser, the residual enumerator; 13 tests (7 new), four of them planted failure modes |
| `cpp/include/quantrisk/{monte_carlo,pricing,risk,stress}/*.hpp` | 24 `// python:` markers above the declarations they disclaim (comments only) |
| `scripts/run_mutation_suite.py` | plant `core-declares-a-function-nobody-binds`; two anchors refreshed to the counts this phase moved |
| `docs/integrity_audit.md` | Phase 17 addendum: finding 43 closed, with what remains outside the claim |
| `docs/limitations.md` | #80; #79(d)-(e) restored |
| `docs/reproducibility.md` | `noise_decided_verdicts` documented as producer-declared and empty by default |
| `docs/interview_defense.md` | Q27, one citation row, the two test counts, the limitation count |
| `README.md`, `docs/validation_matrix.md`, `paper/technical_report.tex`, `docs/release_notes_v1.3.0.md`, `docs/release_notes_v1.4.0.md` | the limitation count 79 → 80 where each document states it |

## 4. Tests executed

`uv run cmake --build --preset dev`, `uv run ctest --preset dev`, `uv run pytest tests/python -q`,
`uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy python/quantrisk`,
`uv run --frozen clang-format --dry-run -Werror` on all 29 headers, `uv run quantrisk validate`,
`uv run python scripts/verify_evidence_manifest.py`, and
`uv run python scripts/run_mutation_suite.py` on the committed tree.

The benchmark suite was **not** re-run. Every producer it drives resamples the volatile performance
fields and the prose guards then quote a new number (`CONTRIBUTING.md` §4 step 2 moved those spellings
three times during Phase 16); this phase changes no producer, no numerical code and no artifact, so
re-running it would have churned nine evidence files to prove a null result. The manifest verify step
covers the same ground by checking the committed bytes.

## 5. Exact test results

```text
cmake --build --preset dev     52 steps after touching every header, exit 0, 0 warning lines
ctest --preset dev             100% tests passed out of 201     Total Test time (real) = 10.54 sec
pytest tests/python -q         446 passed in 22.30s
pytest ...tension_surface_parity.py -q
                               13 passed in 0.24s
ruff check .                   All checks passed!
ruff format --check .          134 files already formatted
mypy python/quantrisk          Success: no issues found in 23 source files
clang-format --dry-run -Werror exit 0 (29 headers)
quantrisk validate             7/7 checks passed
verify_evidence_manifest       0 missing, 0 unlisted -- Evidence is intact
```

The attribute scan's own census, printed by the guard's non-vacuity test rather than quoted from here:
92 namespace-scope declarations carrying `[[nodiscard]]`, 85 distinct names, 24 of them disclaimed by a
marker, across 29 headers.

## 6. Numerical validation

Not applicable, and the reason is the point: no number in the repository moved. What this phase validates
is an *interface* claim, and its evidence is the failure modes in §1 item 5 rather than a residual. The
compiled surface is unchanged, which is what `ctest` and the parity file's original two directions confirm
against the rebuilt extension.

## 7. Remaining limitations

- The claim covers what the core marks. An unattributed, unbound namespace-scope function is outside it,
  and the guard's answer is a pinned inventory of one name rather than a complete enumeration
  (limitation #80). Making `[[nodiscard]]` uniform across the pure functions would let the claim drop the
  inventory; that is a C++ change with warning fallout at call sites, deliberately not attempted here.
- The guard verifies a disclaimer's *route*, not its *reason*. `// python: internal -- ...` is prose a
  reviewer reads; nothing here checks that the sentence is still true.
- The header scan is a brace-stack reader of formatted C++, not a compiler. It is honest about that: the
  shapes it must not confuse (`epsilon()` in an initialiser, a call inside an inline body, a struct
  member, an `enum class`) are pinned as tests because a parser that silently matched nothing would make
  the claim green and worthless.
- Registration order and argument names are outside the claim; a function bound under a different Python
  name still counts as reachable, which is intended.

## 8. Technical debt

1. **Two research items remain from Phase 16 §8**, untouched by this phase: the crossing radius on a
   second book (different convexity signs and maturities, to see whether `|delta| <= 0.15` is a property
   of the model or of this ladder), and a fifth-order noise pre-check before anyone ships order-five
   partials — the order-four residual at `1e-3` is already at the subtraction floor of a book near 1.09e5,
   so the fifth order may be measuring arithmetic.
2. **Uniform `[[nodiscard]]`** would retire the inventory test in §1 item 4. Estimated at a few dozen
   declarations plus the call sites the compiler then warns about.
3. **The sweep's count is prose in two places** (`docs/interview_defense.md` names nineteen planted defects
   as a historical statement about `e5daedc`, which stays true; the current number is only in the harness's
   own output). A guard that recomputed the count from `MUTATIONS` and refused a stale sentence would be
   the same class of fix as this phase's limitation-count guard, at the cost of turning a historical claim
   into a live one — which `docs/integrity_audit.md` says not to do to a record.

## 9. Gate

**Not a release, and that is deliberate.** Version stays `1.6.0`, tag stays `b4e4bea`; this lands as
verification engineering after the release, like Phase 14. Every gate above ran on this tree and reported
its own pass. The falsification sweep runs on the committed tree because it refuses a dirty target, so its
verdict is recorded in the commit that follows this one, citing the revision it ran on; this report does
not state a sweep result it has not yet observed.
