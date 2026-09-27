# Public data

Optional adapters for three free public sources, and the offline snapshots that let the
test suite run without any of them.

Nothing in `cpp/` or in the numerical core depends on this directory. The dependency runs
one way: `quantrisk.data` may use `quantrisk`, never the reverse. That is what keeps
"core algorithms must not depend on the network" true as a fact of the build rather than a
promise in a document.

## What is here

| Path | What it is |
| --- | --- |
| `fixtures/` | Committed snapshots of **real** responses, each with a `.provenance.json` sidecar. Safe to clone; ~150 KB total. |
| `cache/` | Live downloads made by you, on your machine. **Git-ignored**, not shared, not part of the repository. |

The Python package is `python/quantrisk/data/`: `http` (caching, rate-limited transport),
`edgar`, `fred`, `cftc` (the adapters), `fixtures` (offline loading), `provenance`
(the record every download must carry).

## Sources

### SEC EDGAR — no key

`https://data.sec.gov/api/xbrl/companyconcept/CIK{10-digit}/{taxonomy}/{tag}.json`

SEC requires a `User-Agent` naming the person or company making the request, and caps
traffic at 10 requests per second per IP
([policy](https://www.sec.gov/os/accessing-edgar-data)). Both are enforced in code, not
just documented: `http.user_agent_for` raises `RequestPolicyError` rather than send an
anonymous request, and the rate limit is persisted per host under `cache/ratelimit/` so it
holds across processes rather than only within one.

Set the identity once:

```bash
export QUANTRISK_DATA_USER_AGENT='Your Name (research; contact: you@example.com)'
```

The six quantities PROJECT_SPEC.md asks for map onto `us-gaap` tags in
`edgar.SPEC_ITEMS`. A tag a filer does not use is reported in `Financials.missing` — an
absent balance is not the same statement as a zero balance.

### FRED — one path with a key, one without

| Need | Endpoint | Key |
| --- | --- | --- |
| Current revision of a series | `fred.stlouisfed.org/graph/fredgraph.csv?id=…` | none |
| **ALFRED vintage** (as published on a date) | `api.stlouisfed.org/fred/series/observations` | `FRED_API_KEY` |

The second one is the reason this section is not just "download the CSV". A backtest run on
today's revision of a macro series can see revisions published after the day it simulates,
which is look-ahead bias by construction. `fred.fetch_vintage` therefore **refuses** when
no key is configured instead of quietly falling back to the current revision: a silently
different dataset still looks like a backtest, which makes it worse than no dataset.

```bash
export FRED_API_KEY='your key from https://fredaccount.stlouisfed.org/apikeys'
```

The key is read from the environment and nowhere else. It is never written to a fixture,
never stored in a provenance record, and never part of a cache filename — `http.fetch`
takes a `record_url` precisely so the credential-free form is what gets persisted. There is
a test that asserts a planted key does not appear anywhere in a vintage record.

### CFTC — no key, optional

`https://www.cftc.gov/files/dea/history/com_disagg_txt_{year}.zip`, one archive per year,
each holding a ~22 MB CSV. Positioning data is market **context**: nothing in the pricing,
risk or optimisation layers consumes it, and no number elsewhere in the project should cite
it as evidence.

The older `/files/debt/history/` paths the reports used to live behind now 404 behind a
redirect. The current ones were read off CFTC's own historical index rather than
remembered.

## Provenance

Every download writes four things, because PROJECT_SPEC.md §Phase 8 asks for exactly four:
`source`, `retrieved_at_utc`, `series_id`, `sha256`. The digest covers the bytes **as
served**, before parsing — a digest of the parsed form would change when the parser changed,
which defeats the point.

`read_pair` refuses a payload whose bytes no longer match its record, so an edited fixture
fails loudly instead of quietly becoming the source of truth.

## Fixtures are real, with two labelled exceptions

| Fixture | Status |
| --- | --- |
| `edgar_*` | Live SEC responses (Apple Inc. CIK 320193, Madison Square Garden CIK 1652044) |
| `fred_*` | Live FRED responses, current revision |
| `cftc_disagg_cot_2024_excerpt.csv` | **Excerpt.** The archive is 2.4 MB compressed, too large to commit. The sidecar says so, records how many of 22 MB of rows were kept, and carries the full archive's digest separately so the excerpt can be traced back to it. |
| `fred_vintage_shape_synthetic.json` | **Not real data.** ALFRED needs a key, so this file is shaped like a vintage response purely to test the parser offline. Its provenance says `NOT REAL DATA` and no number in it describes any economy. |

## Refreshing

```bash
export QUANTRISK_DATA_USER_AGENT='Your Name (research; contact: you@example.com)'
uv run python scripts/record_data_fixtures.py
```

Re-running rewrites every snapshot and re-records every digest, so a fixture's provenance
always describes the file beside it. It respects SEC's rate limit while doing so, and it
refuses any single response over 200 KB rather than letting the repository grow.

## Offline by construction

CI has no network and no credentials. `tests/python/test_data_layer_offline.py` serves the
adapters from `fixtures/` by replacing the transport — so the production parsing paths run
offline rather than being bypassed — and then
`test_no_test_in_this_file_touches_a_socket` installs a real socket guard and re-runs the
pipeline. The offline claim is executed, not asserted.
