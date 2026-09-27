"""Phase 8 data layer tests. Every one of them runs with no network and no credential.

The transport is injected: `_serve_from_fixtures` replaces `http.fetch` with a lookup
against the committed fixtures, so the *production* parsing code paths are exercised
offline rather than bypassed. A test that called `json.load(open(fixture))` directly would
pass even if the adapter were broken, which is the opposite of what this layer needs.

`test_no_test_in_this_file_touches_a_socket` then closes the loop: it puts a real socket
guard in place and re-runs the fixture-backed paths, so "CI is offline" is something the
suite proves rather than something the README claims.
"""

from __future__ import annotations

import io
import json
import socket
import zipfile

import pytest
import quantrisk
from quantrisk.data import cftc, edgar, fixtures, fred, http
from quantrisk.data.provenance import Provenance, read_pair, sha256_of, write_pair

# --- the injected transport ------------------------------------------------


class NetworkBlocked(RuntimeError):
    pass


def _block_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*_args, **_kwargs):
        raise NetworkBlocked("the data layer must not be a test dependency")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


@pytest.fixture
def served(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Serve `http.fetch` from the committed fixtures, keyed by URL fragment."""

    def install(mapping: dict[str, str]) -> None:
        def fake_fetch(url, *, cache_dir=None, force=False, record_url=None, **_kwargs):
            for fragment, fixture_name in mapping.items():
                if fragment in url:
                    fixture = fixtures.load(fixture_name)
                    return http.Fetched(
                        url=record_url or url,
                        path=fixture.path,
                        data=fixture.data,
                        sha256=fixture.provenance.sha256,
                        retrieved_at_utc=fixture.provenance.retrieved_at_utc,
                        from_cache=True,
                        status=200,
                    )
            # RuntimeError is what http.fetch raises for a 404, and the tag-fallback
            # loop in company_financials keys off exactly that.
            raise RuntimeError(f"{url} returned HTTP 404 - not in the fixture mapping")

        monkeypatch.setattr(http, "fetch", fake_fetch)

    return install


# --- provenance ------------------------------------------------------------


def test_provenance_digest_covers_the_bytes_as_served(tmp_path) -> None:
    payload = b"observation_date,DFF\n2024-01-01,5.33\n"
    provenance = Provenance.record(
        source="unit test",
        url="https://example.invalid/x.csv",
        series_id="DFF",
        data=payload,
        license="none",
    )
    assert provenance.sha256 == sha256_of(payload)
    assert provenance.bytes == len(payload)
    assert provenance.verify(payload)
    assert not provenance.verify(payload + b"extra")


def test_write_and_read_pair_round_trips(tmp_path) -> None:
    payload = b'{"cik": 1}'
    provenance = Provenance.record(
        source="unit test",
        url="https://example.invalid/x.json",
        series_id="X",
        data=payload,
        license="none",
    )
    path = tmp_path / "payload.json"
    write_pair(path, payload, provenance)
    read_back, record = read_pair(path)
    assert read_back == payload
    assert record.sha256 == provenance.sha256


def test_a_payload_edited_without_its_record_is_refused(tmp_path) -> None:
    payload = b"one,two\n1,2\n"
    provenance = Provenance.record(
        source="unit test",
        url="https://example.invalid/x.csv",
        series_id="X",
        data=payload,
        license="none",
    )
    path = tmp_path / "data.csv"
    write_pair(path, payload, provenance)
    path.write_bytes(b"one,two\n1,3\n")  # a quiet edit to the numbers
    with pytest.raises(ValueError, match="does not match its provenance record"):
        read_pair(path)


def test_a_payload_with_no_record_is_refused(tmp_path) -> None:
    path = tmp_path / "orphan.csv"
    path.write_bytes(b"x")
    with pytest.raises(FileNotFoundError, match="no provenance sidecar"):
        read_pair(path)


# --- the fixture corpus ----------------------------------------------------


def test_every_committed_fixture_matches_its_own_provenance() -> None:
    names = fixtures.available()
    assert len(names) >= 10, f"only {len(names)} fixtures committed"
    for name in names:
        fixture = fixtures.load(name)
        assert fixture.provenance.verify(fixture.data), name
        assert fixture.provenance.source, name
        assert fixture.provenance.url, name
        assert fixture.provenance.series_id, name
        assert fixture.provenance.retrieved_at_utc, name
        assert fixture.provenance.license, name


def test_fixtures_carry_the_four_fields_the_spec_requires() -> None:
    # PROJECT_SPEC.md §Phase 8: source, download timestamp, series identifier, SHA-256.
    required = {"source", "retrieved_at_utc", "series_id", "sha256"}
    for name in fixtures.available():
        provenance = fixtures.load(name).provenance.to_dict()
        missing = required - set(provenance)
        assert not missing, f"{name} provenance lacks {missing}"
        assert len(provenance["sha256"]) == 64


def test_a_missing_fixture_names_what_is_available() -> None:
    with pytest.raises(fixtures.FixtureNotFound, match="Available:"):
        fixtures.load("no_such_fixture")


def test_no_fixture_is_large_enough_to_bloat_the_repository() -> None:
    # §Phase 8: "do not commit large datasets directly". The cap is on the payload total,
    # not on any single file, because the failure mode is a slow clone.
    payloads = [
        path
        for path in fixtures.FIXTURE_ROOT.iterdir()
        if not path.name.endswith(".provenance.json")
    ]
    assert payloads, "no fixtures committed"
    total = sum(path.stat().st_size for path in payloads)
    assert total < 400_000, f"fixtures total {total} bytes"
    for path in payloads:
        assert path.stat().st_size < 200_000, f"{path.name} alone is too large"


# --- EDGAR -----------------------------------------------------------------


def test_cik_normalisation_rejects_what_would_silently_change_company() -> None:
    assert edgar.normalise_cik(320193) == "0000320193"
    assert edgar.normalise_cik("0000320193") == "0000320193"
    # Surrounding whitespace is tolerated because it is a copy-paste artefact; anything
    # that would resolve to a *different* filer is not.
    for bad in ("Apple", "CIK320193", "-1", "32019344444", "", "32 0193"):
        with pytest.raises(ValueError):
            edgar.normalise_cik(bad)


def test_concept_url_carries_the_cik_prefix() -> None:
    # Without it EDGAR 404s, and the failure looks like a missing tag rather than a
    # malformed path.
    url = edgar.concept_url(320193, "us-gaap", "Assets")
    assert url.endswith("/CIK0000320193/us-gaap/Assets.json")
    assert url.startswith("https://data.sec.gov/")


def test_company_financials_resolves_the_spec_items_offline(served) -> None:
    served(
        {
            "Assets.json": "edgar_0000320193_Assets",
            "Liabilities.json": "edgar_0000320193_Liabilities",
            "CashAndCashEquivalentsAtCarryingValue.json": (
                "edgar_0000320193_CashAndCashEquivalentsAtCarryingValue"
            ),
            "Revenues.json": "edgar_0000320193_Revenues",
            "NetIncomeLoss.json": "edgar_0000320193_NetIncomeLoss",
        }
    )
    result = edgar.company_financials(320193, entity_name="Apple Inc.")
    assert "debt" in result.missing  # no LongTermDebt fixture, and absence is reported
    assert {"assets", "liabilities", "cash", "revenue", "earnings"} <= set(result.items)
    for item, observations in result.items.items():
        assert observations, item
        assert all(row.end and row.value == row.value for row in observations)
    assert result.provenance["assets"].series_id == "CIK0000320193:us-gaap:Assets"


def test_real_edgar_observations_are_the_size_and_sign_they_should_be(served) -> None:
    served({"Assets.json": "edgar_0000320193_Assets"})
    observations, provenance = edgar.fetch_concept(320193, "Assets")
    assert len(observations) == provenance.extra["observations"]
    assert all(row.value > 0 for row in observations), "assets are a positive carrying value"
    latest = edgar.latest(observations)
    assert latest is not None
    assert latest.form == "10-K"
    # Apple's balance sheet is in the hundreds of billions, not the millions. A units
    # mistake in the XBRL scale factor would move this by three orders.
    assert 1.0e11 < latest.value < 1.0e12


def test_latest_can_widen_to_quarterly_filings(served) -> None:
    served({"Assets.json": "edgar_0000320193_Assets"})
    observations, _ = edgar.fetch_concept(320193, "Assets")
    annual = edgar.latest(observations)
    with_quarters = edgar.latest(observations, annual_only=False)
    assert annual is not None and with_quarters is not None
    assert with_quarters.end >= annual.end


# --- FRED ------------------------------------------------------------------


def test_graph_url_encodes_the_window() -> None:
    url = fred.graph_url("DFF", "2024-01-01", "2024-01-31")
    assert "id=DFF" in url and "cosd=2024-01-01" in url and "coed=2024-01-31" in url
    assert "api_key" not in url


def test_series_parses_offline_and_keeps_missing_prints_as_none(served) -> None:
    served({"id=DFF": "fred_DFF_2024-01-01_2024-01-31"})
    series = fred.fetch_series("DFF", start="2024-01-01", end="2024-01-31")
    assert series.series_id == "DFF"
    assert len(series.observations) >= 20
    assert all(row.value is None or row.value > 0 for row in series.observations)
    assert series.provenance.extra["observations"] == len(series.observations)
    # The provenance must say it is a current revision, because that is the look-ahead
    # caveat a reader needs before using this in a backtest.
    assert "current revision" in series.provenance.note


def test_vintage_needs_a_key_and_says_so_without_touching_the_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    called = []
    monkeypatch.setattr(
        http,
        "fetch",
        lambda *a, **k: called.append(a) or http.Fetched("", None, b"", "", "", True, 200),  # type: ignore[arg-type]
    )
    with pytest.raises(fred.MissingApiKey, match="FRED_API_KEY"):
        fred.fetch_vintage("DFF", vintage_date="2024-02-01")
    assert not called, "the keyless path must not attempt a request"
    assert (
        "look-ahead" in str(fred.fetch_vintage.__doc__) or "vintage" in fred.fetch_vintage.__doc__
    )


def test_vintage_record_never_contains_the_api_key(monkeypatch: pytest.MonkeyPatch, served) -> None:
    monkeypatch.setenv("FRED_API_KEY", "SECRET-NOT-A-REAL-KEY")
    served({"observations": "fred_vintage_shape_synthetic"})
    series = fred.fetch_vintage("DFF", vintage_date="2024-02-01")
    assert "SECRET-NOT-A-REAL-KEY" not in series.provenance.url
    assert "SECRET-NOT-A-REAL-KEY" not in series.provenance.series_id
    assert "SECRET-NOT-A-REAL-KEY" not in json.dumps(series.provenance.to_dict())
    assert len(series.observations) == 4
    assert all(row.vintage == "2024-02-01" for row in series.observations)


def test_the_synthetic_vintage_fixture_is_labelled_as_synthetic() -> None:
    # This file exists for parser coverage. If it ever stopped saying so, a reader could
    # mistake it for a real FRED vintage.
    fixture = fixtures.load("fred_vintage_shape_synthetic")
    assert fixture.provenance.extra["synthetic"] is True
    assert "NOT REAL DATA" in fixture.provenance.note


# --- CFTC ------------------------------------------------------------------


def test_cot_columns_are_matched_by_name_not_position(served) -> None:
    served({"com_disagg_txt_2024": "cftc_disagg_cot_2024_excerpt"})
    table = cftc.fetch_annual_legacy(2024)
    assert table.date_column == "Report_Date_as_YYYY-MM-DD"
    assert table.market_column == "Market_and_Exchange_Names"
    assert "2024-12-31" in table.dates()
    wheat = table.for_market("WHEAT-SRW - CHICAGO BOARD OF TRADE")
    assert wheat
    assert int(wheat[0]["Open_Interest_All"]) > 0


def test_the_cftc_fixture_admits_being_an_excerpt() -> None:
    fixture = fixtures.load("cftc_disagg_cot_2024_excerpt")
    assert fixture.provenance.extra["excerpt"] is True
    assert "EXCERPT" in fixture.provenance.note
    # The archive's own digest is kept alongside, so the excerpt can be traced to it.
    assert len(fixture.provenance.extra["archive_sha256"]) == 64


# --- http policy and caching -----------------------------------------------


def test_sec_requests_refuse_to_identify_nobody(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(http.USER_AGENT_ENVIRONMENT_VARIABLE, raising=False)
    with pytest.raises(http.RequestPolicyError, match="User-Agent"):
        http.user_agent_for("https://data.sec.gov/api/xbrl/companyfacts/CIK1.json")
    # A non-SEC host is not covered by that policy and gets a plain default.
    assert http.user_agent_for("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF")


def test_a_configured_agent_is_used_verbatim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(http.USER_AGENT_ENVIRONMENT_VARIABLE, "Test/1 (contact: t@example.com)")
    assert http.user_agent_for("https://www.sec.gov/x") == "Test/1 (contact: t@example.com)"


def test_rate_limit_waits_for_the_host_and_records_the_request(tmp_path) -> None:
    import time

    url = "https://data.example.invalid/thing.json"
    now = time.time()
    # First ever request to this host: nothing to wait for.
    assert http._respect_rate_limit(url, tmp_path, 1.0, now=now) == 0.0
    stamp = http._rate_stamp(tmp_path, "data.example.invalid")
    assert stamp.exists()
    payload = json.loads(stamp.read_text(encoding="utf-8"))
    assert payload["host"] == "data.example.invalid"
    # The stamp is per host, so a second host in the same cache is not held back by it.
    other = "https://other.example.invalid/thing.json"
    assert http._respect_rate_limit(other, tmp_path, 1.0, now=now) == 0.0
    assert http._rate_stamp(tmp_path, "other.example.invalid").exists()
    # A corrupt stamp loses the history but must not wedge the tool.
    stamp.write_text("not json", encoding="utf-8")
    assert http._respect_rate_limit(url, tmp_path, 1.0, now=now) == 0.0


def test_cache_path_is_stable_and_url_specific(tmp_path) -> None:
    url = "https://data.sec.gov/api/xbrl/companyconcept/CIK1/us-gaap/Assets.json"
    other = url.replace("Assets", "Liabilities")
    assert http.cache_path(tmp_path, url) == http.cache_path(tmp_path, url)
    assert http.cache_path(tmp_path, url) != http.cache_path(tmp_path, other)
    assert http.cache_path(tmp_path, url).suffix == ".json"


def test_decompress_handles_gzip_zip_and_plain_bytes() -> None:
    import gzip

    assert http.decompress(b"plain") == b"plain"
    assert http.decompress(gzip.compress(b"gzipped")) == b"gzipped"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("inner.csv", b"a,b\n1,2\n")
    assert http.decompress(buffer.getvalue()) == b"a,b\n1,2\n"


# --- the offline guarantee ---------------------------------------------------


def test_no_test_in_this_file_touches_a_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove the CI claim rather than assert it.

    With sockets refused, drive the real adapters over the injected fixture transport and
    confirm the pipeline still produces numbers. If any code path reached for the network,
    this fails.
    """
    _block_sockets(monkeypatch)
    monkeypatch.setenv(http.USER_AGENT_ENVIRONMENT_VARIABLE, "Test/1 (contact: t@example.com)")
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    def fake_fetch(url, *, record_url=None, **_kwargs):
        fixture_name = next(
            (
                name
                for name, probe in (
                    ("edgar_0000320193_Assets", "Assets.json"),
                    ("fred_DFF_2024-01-01_2024-01-31", "id=DFF"),
                    ("cftc_disagg_cot_2024_excerpt", "com_disagg_txt_2024"),
                )
                if probe in url
            ),
            None,
        )
        assert fixture_name is not None, f"unexpected URL {url}"
        fixture = fixtures.load(fixture_name)
        return http.Fetched(
            url=record_url or url,
            path=fixture.path,
            data=fixture.data,
            sha256=fixture.provenance.sha256,
            retrieved_at_utc=fixture.provenance.retrieved_at_utc,
            from_cache=True,
            status=200,
        )

    monkeypatch.setattr(http, "fetch", fake_fetch)

    observations, _ = edgar.fetch_concept(320193, "Assets")
    assert observations
    series = fred.fetch_series("DFF", start="2024-01-01", end="2024-01-31")
    assert series.values()
    table = cftc.fetch_annual_legacy(2024)
    assert table.rows
    with pytest.raises(fred.MissingApiKey):
        fred.fetch_vintage("DFF", vintage_date="2024-02-01")
    assert quantrisk.version()
