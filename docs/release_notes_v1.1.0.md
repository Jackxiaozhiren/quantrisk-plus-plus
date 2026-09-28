# v1.1.0 — The conclusions meet real market data

Released 2026-09-28. Predecessor: `v1.0.0` (`docs/release_notes_v1.0.0.md`). Total monetary cost
of building and validating this release: **$0** — no paid data, solver, cloud service or API key.

## What changed, and why it is the release worth having

`v1.0.0` was a project about *instrumentation*: every published number traced to a script, and the
boundary of each claim written down. Its one structural weakness was that every statistical result
was measured on synthetic data whose truth is known — which is what makes a bias measurable, and
also what keeps each conclusion one step away from an empirical claim.

**v1.1.0 adds the empirical arm and reports what it did to the older conclusions.**
`experiments/real_data_risk_study/` scores three FRED series as risk factors — the 10-year Treasury
par yield, the 10-year breakeven inflation rate, and the CBOE volatility index — against an assumed
book of fixed notional exposures, over 3,177 aligned daily observations from 2014-01-03 to
2026-09-22. Each VaR is calibrated on the 250 observations *preceding* the return it scores, giving
586 out-of-sample days.

| | Result |
|---|---|
| Gaussian 99 % VaR | realised **2.048 %** against 1 % nominal, exact interval **[1.062 %, 3.550 %]** — **excludes** it |
| Historical 99 % VaR | realised **1.365 %**, interval [0.591 %, 2.672 %] — covers it |
| Both at 95 % | Gaussian 5.631 %, historical 6.314 % — both intervals cover 5 % |
| Kupiec / independence / conditional coverage | **p = 0.160 / 0.287 / 0.211 — none rejects** |
| Violation runs test | **z = −1.17** (67 runs against 70.33 expected) — right sign, no power |
| Block over iid bootstrap SE | **1.072** |
| Covariance, realised out-of-sample variance | **ewma < sample < shrinkage** |

The synthetic prediction from Phase 5 — that a Gaussian tail under-states 99 % risk — reproduces on
data nobody generated, with an interval that excludes the nominal rate. The synthetic *ranking* does
not survive: Phase 6's mean forward-variance ratio was shrinkage 1.169 < sample 1.183 < ewma 1.241,
and here the two ends exchange places. Neither number is wrong. Shrinkage wins where a short window
makes the sample covariance unstable, which is the regime the synthetic process was built to create.
The conclusion generalises over the method and not the process, which is the reason Phase 6 reported
a ratio against an informed solver instead of a bare winner.

The coverage tests failing to discriminate on this sample is published rather than dropped, as is
the truth-free version of the same question (the 1.072 standard-error ratio, consistent with mild
clustering). A reviewer should be able to find the negative result without hunting for it.

**Three questions the artifact refuses instead of proxying.** The cost of estimating covariance
against an informed solver needs an observable true forward covariance, which real data does not
have. Block-bootstrap *coverage* needs a truth independent of the series being resampled; an earlier
version measured exactly 1.000 by resampling the full-sample VaR, which is circular, so the figure
was discarded and named as discarded inside `refusals`. Whether the book is profitable needs a
return, and it has none.

## Tooling and evidence changes

- **The suite is twelve members**, the new study registered with its headline metrics read from the
  artifact's own `headline` block — deliberately *derived* references, not retyped figures, because
  a key path into a list ordered by confidence level is a path that silently publishes a 95 % rate
  under a 99 % label.
- **The evidence chain now contains the suite's own roll-up** (58 → 69 artifacts, a fifth category
  `suite_aggregate`). The README's "12/12 members executed" is read out of that file, and nothing
  previously verified it.
- **The roll-up records the command that made it**, rebuilt from parsed flags rather than `argv`, so
  an absolute `--out` cannot be written into a committed artifact.
- **No test may write into frozen evidence.** A session fixture hashes every file under
  `benchmarks/`, `experiments/`, `data/fixtures/` and `evidence/` before the run and fails the
  session if any moved — because until Phase 11, `pytest` itself regenerated a committed artifact on
  every invocation and the verifier reported VOLATILE for self-inflicted drift.
- **FRED and SEC requests must identify a contact.** `python/quantrisk/data/http.py` refuses a
  User-Agent that names nobody. FRED does not reject such a request; it drops it, so the failure
  surfaces as a read timeout and looks like a network fault. Verified with a paired, order-swapped
  A/B run.
- **Six new guards** bind counts that documents restate: suite member total, per-kind breakdown,
  skippable count, limitations total, the Python test count (re-measured in a subprocess), and every
  figure the README and `docs/findings.md` print for the new study, re-derived from the artifact.

## Corrected, in place rather than quietly

- `docs/integrity_audit.md`'s own header named commit `06836d2` as `v1.0.0` (it is five commits
  before the tag) and reported 319 pytest tests for that revision. Re-measured in clean worktrees:
  **316** at `06836d2`, **330** at `v1.0.0`, **353** here.
- `docs/reproducibility.md` said four suite members skip without the `oracles` extra; the registry
  had five, and has six.
- The report's page count, the limitations total, and the README's experiment and matrix counts all
  moved with the work and are now guarded.
- `docs/findings.md`'s "what is *not* a finding" section began "No real market data was used
  anywhere." That sentence is now false and has been replaced with what is actually true: six of
  seven experiments are synthetic, the seventh is real, and its exposures are an assumption.

## Verification at this release

| Check | Result |
|---|---|
| pytest, `oracles` extra installed | **353 passed**, 0 failed, 0 skipped |
| pytest in the CI lane without it | 261 passed / 4 skipped at `v1.0.0`; the split is explained in `docs/limitations.md` #63 |
| CTest | **190 passed** (core unchanged since `v1.0.0`) |
| CTest at the following phase | **194 passed** — `v1.1.0`'s successor added the higher-order spot sensitivities |
| Benchmark suite, `--require-all` | **12/12 executed, 0 failed, 0 skipped**, ~62 s |
| `verify_evidence_manifest.py` | **72 artifacts, 0 CHANGED, 0 VOLATILE, 0 MISSING, 0 unlisted, 0 warnings** |
| `quantrisk validate` | **7/7**, worst residual 2.22e-16 |
| mypy / ruff / ruff format / clang-format | clean |
| Technical report | 12 chapters, **38 pages**, new §5.4 "Do the conclusions survive real data?" |
| Cost | **$0** |

## What is still not here

No expected-return model, no term structure, no live market feed, no re-pricing inside the stress
layer, no multi-period rebalancing, no short positions or leverage, no PyPI package and no DOI.
The real-data arm remains one sample of three factor series with assumed exposures on FRED's current
revision rather than its vintages (`docs/limitations.md` #61–#62). The full boundary is
**66 numbered entries** in `docs/limitations.md`.
