# Phase 8 Report — Optional Public Data Integration

Date: 2026-09-27 · Branch: `main` · Status after this phase: **complete and verified**
Research question answered: *can this project touch real market and filing data without the
core depending on it, without spending anything, and without the test suite ever needing a
network?*

## 1. Completed

- **`quantrisk.data`** — a Python-only package of seven modules, built entirely on the
  standard library. No dependency was added to `pyproject.toml`, which keeps §3 at $0 and
  keeps the install surface unchanged.
- **A policy-enforcing transport** (`http.py`): per-host rate limiting persisted to disk so
  it holds across processes, a URL-keyed cache, and a `User-Agent` guard that **refuses to
  send** an anonymous request to a SEC host rather than sending one and hoping.
- **SEC EDGAR adapter** (`edgar.py`): the six quantities the spec names — assets,
  liabilities, cash, debt, revenue, earnings — mapped onto `us-gaap` tags with ordered
  fallbacks, and unresolved items reported in `Financials.missing`.
- **FRED adapter** (`fred.py`): two paths with genuinely different semantics. The
  keyless `fredgraph.csv` for current revisions; the API endpoint for **ALFRED vintages**,
  which is the only one that can answer "what did the data look like on that date".
- **CFTC adapter** (`cftc.py`): annual Disaggregated COT archives, columns matched by name
  from the file's own header rather than by position.
- **Provenance** (`provenance.py`): the four fields §Phase 8 requires — source, download
  timestamp, series identifier, SHA-256 — as one immutable record, digest taken over the
  bytes as served, with `read_pair` refusing a payload that no longer matches.
- **A committed fixture corpus**: 13 files, ~150 KB, of **real** responses from live
  sources, each with its sidecar.
- **`scripts/record_data_fixtures.py`**: re-runnable, rate-limit-respecting, refuses any
  single response over 200 KB rather than letting the repository grow.
- **`data/README.md`**: sources, keys, what is real, what is an excerpt, what is synthetic.

Suite after this phase: **190 CTest entries, 546,943 assertions in 189 Catch2 cases,
291 pytest tests** (26 new).

## 2. Mathematical assumptions

No numerical model is introduced. The assumptions that matter here are about data semantics:

- An XBRL fact is a *carrying amount as reported by the filer on the filing date*. Restated
  figures appear as additional observations under the same `end` date, so "latest" is
  defined as max over `(end, filed)` and the annual/quarterly split is by `form`, not by
  period length.
- A missing tag is not a zero. `SPEC_ITEMS` tries an ordered list of tags and reports the
  item as missing if none resolve; conflating the two would turn an absent balance sheet
  line into a solvency statement.
- FRED's `"."` placeholder is kept as `None`, not dropped and not zero-filled. Dropping it
  silently shortens a series; zero-filling a missing unemployment print invents a recovery.
- A **current revision** and a **vintage** are different datasets. The current revision of a
  macro series contains information published after the observation date, so a backtest on
  it can see the future. That is why the vintage path exists and why it refuses rather than
  degrading.
- SHA-256 is taken over the bytes as served. The CFTC archive is 2.4 MB compressed and
  22 MB decompressed; the committed fixture is an excerpt whose sidecar records that it is
  an excerpt, how many rows were kept, and the full archive's digest separately.

## 3. Files changed

| Path | Role |
| --- | --- |
| `python/quantrisk/data/__init__.py` | package surface and the one-way dependency rule |
| `python/quantrisk/data/http.py` | caching, per-host rate limiting, User-Agent policy |
| `python/quantrisk/data/provenance.py` | the four required fields, write/read with verification |
| `python/quantrisk/data/edgar.py` | CIK handling, tag map, observation parsing |
| `python/quantrisk/data/fred.py` | current-revision CSV and ALFRED vintages |
| `python/quantrisk/data/cftc.py` | annual COT archives |
| `python/quantrisk/data/fixtures.py` | offline loading |
| `data/fixtures/*` (13 + 13 sidecars) | real committed responses |
| `data/README.md` | sources, keys, honesty labels |
| `scripts/record_data_fixtures.py` | fixture recorder |
| `tests/python/test_data_layer_offline.py` | 26 offline tests |
| `.gitignore` | `data/cache/` excluded |

## 4. Tests executed

```bash
uv run pytest tests/python/test_data_layer_offline.py -q
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
```

No C++ test, benchmark or experiment was touched, and the C++ suite still passes unchanged:
this phase adds nothing to the numerical core, which is the point.

## 5. Exact test results

```
26 passed in 0.05s        (the data layer, with no network and no credentials)
291 passed in 7.11s       (full Python suite)
All tests passed (546943 assertions in 189 test cases)   (C++, unchanged)
ruff check .              All checks passed!
ruff format --check .     67 files already formatted
```

`test_no_test_in_this_file_touches_a_socket` replaces `socket.socket` and
`socket.create_connection` with raisers and then drives all three adapters over the
fixture-backed transport. It passes, and it fails the moment any code path reaches for the
network — so the CI-offline requirement is executed rather than asserted.

## 6. Numerical validation

There is no numerical claim in this phase, so validation is about **provenance integrity
and refusal behaviour** — the failure modes that would actually corrupt later work:

| Claim | How it was checked | Result |
| --- | --- | --- |
| Every committed fixture still matches its own record | recompute the digest of all 13 and compare | all match |
| The four required provenance fields exist on every fixture | field-presence check over the corpus | complete |
| An edited payload is refused | write, silently change one number, read back | raises with both digests named |
| A payload with no record is refused | orphan file | raises, naming the missing sidecar |
| SEC requests cannot go out anonymous | `user_agent_for` on a `sec.gov` URL with the env var cleared | `RequestPolicyError`, nothing sent |
| A keyless vintage call makes no request | transport instrumented, key removed | raises, zero calls recorded |
| **An API key cannot leak** | a planted key, then assert it is absent from the provenance URL, series id and the whole serialised record | absent |
| Real EDGAR facts are the right magnitude | Apple's latest 10-K assets must sit between 1e11 and 1e12 | passes: 359,241,000,000 for FY ending 2025-09-27, filed 2025-10-31, out of 36 annual and 146 total observations |
| Missing XBRL fields do not crash the parser | live response has `"fy": null` on 2 of 146 observations | fixed, see below |
| CFTC columns are matched by name | assert `date_column == "Report_Date_as_YYYY-MM-DD"` | passes; index 0 is the market name |
| The synthetic fixture admits being synthetic | provenance flag and note | `synthetic: True`, `"NOT REAL DATA"` |
| Nothing large is committed | fixture payloads total < 400 KB, each file < 200 KB | 232 KB of fixtures; 304 KB for the whole commit |

Two defects surfaced only because the fixtures are real rather than hand-written:

- **EDGAR sends `"fy": null`.** `row.get("fy", 0)` returns `None` when the key is present
  with a JSON null, so `int(None)` raised `TypeError` on live Apple data and would have
  raised on most large filers. A hand-authored sample would not have had a null in it.
- **The CFTC paths everyone remembers are dead.** `/files/debt/history/BOTFC*.zip` returns
  301 → 404. The working path was read off CFTC's own historical index. A guessed URL that
  404s is obvious; a guessed URL that serves a *different* report would not be, which is
  why the parser keys off the header.

## 7. Remaining limitations

Recorded as `docs/limitations.md` entries 49–52.

1. **No new analysis consumes this data yet.** The adapters deliver observations; no
   project number in `docs/` or `experiments/` cites EDGAR, FRED or CFTC. Wiring real data
   into a real study is not done here and no result implies it was.
2. **Only one filer is exercised per concept.** The tag-fallback ordering is tested against
   Apple and Madison Square Garden. A filer using an unusual tag will land in `missing`,
   which is correct behaviour but untested at breadth.
3. **No industry or multi-period screens.** `companyfacts` (all tags at once) is not
   wrapped; only `companyconcept` per tag, which costs one request per item per company.
4. **The CFTC excerpt is 3 report dates.** Enough to exercise date and market handling; not
   a positioning study.

## 8. Technical debt

- `fixtures.available()` returns extension-free names while `load()` accepts either form.
  The leniency is deliberate but it means two spellings resolve to one fixture; a canonical
  accessor would be cleaner in Phase 9's facade work.
- `http.fetch` is the only place `urllib` is used, but `decompress` and
  `describe_environment` import `gzip`/`zipfile`/`shutil` lazily inside functions. Fine,
  just inconsistent with the module's other imports.
- No retry with backoff. A transient 5xx from EDGAR surfaces as a `RuntimeError`; the
  caller can re-run. Given the cache, a retry loop would mostly add complexity, not
  reliability — but a 429/503-aware single retry is worth revisiting if the data layer ever
  becomes load-bearing.
- `describe_environment()`'s `cache_writable` uses disk-free as a proxy for writability,
  which is wrong in the interesting case (a read-only mount with free space). It is unused
  by any test or report; either fix it or delete it in Phase 9.
- The recorder hard-codes two CIKs and five FRED windows. Adding breadth means editing the
  script rather than passing arguments.

## 9. Gate

| Requirement (PROJECT_SPEC.md §Phase 8) | Verdict | Evidence |
| --- | --- | --- |
| Core algorithms must not depend on the network | **met structurally** | the data layer is Python-only and lives outside the extension; `cpp/` and `_quantrisk` gained nothing, and the C++ suite is byte-for-byte unchanged at 546,943 assertions |
| Integration must be optional | **met** | `quantrisk.data` is a separate subpackage; importing `quantrisk` does not pull it, and every test path is satisfiable from `fixtures/` |
| SEC EDGAR via official JSON, no key, cached, policy-compliant | **met** | `companyconcept` endpoints; URL-keyed cache; per-host rate limit persisted across processes; `RequestPolicyError` rather than an anonymous request |
| The six financial quantities | **met, with absence reported** | five of six resolve from live fixtures; `debt` correctly lands in `missing` when no tag resolves, and the test asserts that rather than hiding it |
| FRED/ALFRED key via environment, never committed | **met and tested** | read from `FRED_API_KEY` only; a planted key is asserted absent from the URL, series id and serialised record; no key exists in this environment and nothing broke |
| Tests use fixtures when there is no key | **met** | `fetch_vintage` raises `MissingApiKey` and the vintage *parser* is exercised against a labelled synthetic response shape |
| Optional CFTC support | **met** | annual Disaggregated COT fetched, decompressed and parsed by header name |
| Metadata: source, timestamp, series id, SHA-256 | **met** | `Provenance` dataclass; all four present on all 13 fixtures, checked by test |
| Do not commit large datasets | **met** | 304 KB staged in total; recorder refuses >200 KB per response; CFTC's 2.4 MB archive kept as a labelled excerpt |
| CI fully offline; network APIs not a test dependency | **met and proved** | a socket-blocking test drives all three adapters end to end and passes |
| Nothing paid for (§3) | **met** | zero new dependencies; stdlib only |
| No fabricated data (§4) | **met with two explicit labels** | fixtures are live responses; the one synthetic file and the one excerpt each say what they are in their own provenance |

**Gate: PASS.** Phase 8 is complete and verified. Next: Phase 9 — the Python research API
facades and the CLI, which is where the exact `BlackScholes(spot=…, strike=…)` surface the
spec asks for gets built on top of Phases 2–8.
