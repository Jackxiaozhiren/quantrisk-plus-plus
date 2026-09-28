"""A caching, rate-limited fetcher built on the standard library only.

Two rules shape this module. The first is PROJECT_SPEC.md §3: the data layer adds no
dependency, so this is `urllib.request`, not `httpx` or `requests`. The second is §Phase 8's
"CI must run fully offline": nothing here is import-required for a test to pass, and every
public entry point can be satisfied from a committed fixture instead.

SEC's request policy is a real constraint and is enforced rather than documented:
https://www.sec.gov/os/accessing-edgar-data asks for a `User-Agent` naming the person
making the request and caps traffic at 10 requests per second per IP. Two things follow
that are easy to get wrong:

  * The rate limit is per **host**, and a single-process sleep does not honour it across
    processes. The last-request time is therefore persisted next to the cache, so a loop
    that spawns a new interpreter per request still waits.
  * A missing or placeholder User-Agent should fail loudly. Sending `Mozilla/5.0` to
    data.sec.gov is the kind of thing that works until the day it gets an IP blocked, and
    the block lands on whoever shares that address.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# SEC asks for at most 10 requests per second; one per second is an order of magnitude
# inside that and leaves headroom for a script that retries.
DEFAULT_MIN_INTERVAL_SECONDS = 1.0
DEFAULT_TIMEOUT_SECONDS = 30.0
# Both the SEC and the St. Louis Fed expect a User-Agent that names a contact. The SEC
# publishes that requirement; FRED enforces it silently, which is far worse: a contactless
# UA is dropped without any response, so the request dies as a read timeout instead of a
# 403 and looks like a network fault. Measured on 2026-09-28 -- `QuantRisk/0.1 (research)`
# times out against fredgraph.csv while the same string with a contact returns in 0.7 s,
# order-independent across two paired trials.
CONTACT_REQUIRED_HOSTS = ("sec.gov", "stlouisfed.org")

# Overridable so a user can put their own address in without editing source, and so tests
# can prove the guard fires when it is absent.
USER_AGENT_ENVIRONMENT_VARIABLE = "QUANTRISK_DATA_USER_AGENT"


class RequestPolicyError(RuntimeError):
    """The request would violate the source's own published access policy."""


@dataclass(frozen=True)
class Fetched:
    """One download, whether it came from the network or from the cache."""

    url: str
    path: Path
    data: bytes
    sha256: str
    retrieved_at_utc: str
    from_cache: bool
    status: int

    @property
    def text(self) -> str:
        return self.data.decode("utf-8")


def default_cache_dir() -> Path:
    override = os.environ.get("QUANTRISK_DATA_CACHE")
    if override:
        return Path(override).expanduser()
    return Path(__file__).resolve().parents[3] / "data" / "cache"


def user_agent_for(url: str) -> str:
    """The User-Agent to send, or a refusal.

    A contact address is required for the SEC hosts. The value may come from the
    environment or from the caller; what is not acceptable is a silent default that
    identifies nobody.
    """
    configured = os.environ.get(USER_AGENT_ENVIRONMENT_VARIABLE, "").strip()
    host = urlparse(url).hostname or ""
    requires_contact = any(
        host == suffix or host.endswith("." + suffix) for suffix in CONTACT_REQUIRED_HOSTS
    )
    if configured:
        return configured
    if requires_contact:
        raise RequestPolicyError(
            f"requests to {host} need a User-Agent naming a contact. The SEC states this at "
            "https://www.sec.gov/os/accessing-edgar-data; FRED does not state it but enforces "
            "it silently, dropping the request until it times out. Set "
            f"{USER_AGENT_ENVIRONMENT_VARIABLE} to something like "
            f'"{example_user_agent()}" and retry. '
            "Nothing was sent."
        )
    return _default_user_agent()


def _product_token() -> str:
    # Read from the package rather than writing "0.1" down here, so the string cannot
    # outlive the version it claims to be.
    from .. import version as _version

    return f"QuantRisk/{_version()}"


def example_user_agent() -> str:
    """A well-formed agent with a placeholder contact, for error messages."""
    return f"{_product_token()} (research; contact: you@example.com)"


def _default_user_agent() -> str:
    return f"{_product_token()} (research)"


def _rate_stamp(cache_dir: Path, host: str) -> Path:
    return cache_dir / "ratelimit" / f"{host}.json"


def _respect_rate_limit(
    url: str, cache_dir: Path, min_interval: float, *, now: float | None = None
) -> float:
    """Sleep until this host is due for another request; return the wait in seconds.

    Split out from the fetch so the arithmetic is testable without a socket and without a
    real sleep: the caller injects `now` and reads the returned wait.
    """
    host = urlparse(url).hostname or "unknown"
    stamp = _rate_stamp(cache_dir, host)
    current = time.time() if now is None else now
    waited = 0.0
    if stamp.exists():
        try:
            payload = json.loads(stamp.read_text(encoding="utf-8"))
            last = float(payload.get("last_request", 0.0))
        except (ValueError, json.JSONDecodeError):
            last = 0.0  # a corrupt stamp must not block the tool; it just loses the history
        since = current - last
        if since < min_interval:
            waited = min_interval - since
            time.sleep(waited)
    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.write_text(
        json.dumps({"host": host, "last_request": time.time()}) + "\n", encoding="utf-8"
    )
    return waited


def cache_path(cache_dir: Path, url: str) -> Path:
    """Where this URL's payload belongs, keyed by the URL's own digest.

    Hashing the URL rather than deriving a name from its path avoids collisions between
    two query strings that differ only in characters a filesystem treats specially.
    """
    import hashlib

    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    suffix = Path(urlparse(url).path).suffix or ".bin"
    return cache_dir / "responses" / f"{digest}{suffix}"


def fetch(
    url: str,
    *,
    cache_dir: Path | None = None,
    record_url: str | None = None,
    force: bool = False,
    max_age_seconds: float | None = None,
    min_interval: float = DEFAULT_MIN_INTERVAL_SECONDS,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Fetched:
    """Fetch `url`, serving from cache when it is present and fresh.

    The cache is not optional and is not a performance afterthought: re-downloading a
    dataset changes the timestamp in its provenance, which makes a previously published
    number unreproducible. `force` exists for the case where the source really has
    corrected itself, and the caller has to say so.

    `record_url` is the credential-free form of `url`. Endpoints that take an API key in
    the query string must pass it, or the key ends up inside the cache filename and the
    sidecar that sits next to it.
    """
    directory = cache_dir or default_cache_dir()
    stored_url = record_url or url
    path = cache_path(directory, stored_url)
    sidecar = path.with_suffix(path.suffix + ".meta.json")

    if not force and path.exists() and sidecar.exists():
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
        age = (datetime.now(UTC) - datetime.fromisoformat(meta["retrieved_at_utc"])).total_seconds()
        if max_age_seconds is None or age <= max_age_seconds:
            return Fetched(
                url=stored_url,
                path=path,
                data=path.read_bytes(),
                sha256=meta["sha256"],
                retrieved_at_utc=meta["retrieved_at_utc"],
                from_cache=True,
                status=int(meta.get("status", 200)),
            )

    request = urllib.request.Request(url, headers={"User-Agent": user_agent_for(url)})
    _respect_rate_limit(url, directory, min_interval)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - https URLs from a fixed allow-list of public data hosts
            data = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        if error.code in {401, 403}:
            hint = (
                ". If this is a SEC host the usual cause is a missing or placeholder "
                f"User-Agent; set {USER_AGENT_ENVIRONMENT_VARIABLE}"
            )
        elif error.code == 404:
            hint = " - the identifier or tag is wrong for this filer"
        else:
            hint = ""
        raise RuntimeError(f"{stored_url} returned HTTP {error.code}{hint}.") from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(
            f"{url} could not be reached ({error}). The data layer is optional by design: "
            "load the committed fixture instead, see data/README.md."
        ) from error

    import hashlib

    digest = hashlib.sha256(data).hexdigest()
    retrieved_at = datetime.now(UTC).isoformat(timespec="seconds")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    sidecar.write_text(
        json.dumps(
            {
                "url": stored_url,
                "sha256": digest,
                "retrieved_at_utc": retrieved_at,
                "bytes": len(data),
                "status": status,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return Fetched(
        url=stored_url,
        path=path,
        data=data,
        sha256=digest,
        retrieved_at_utc=retrieved_at,
        from_cache=False,
        status=status,
    )


def decompress(data: bytes, *, hint: str = "") -> bytes:
    """Gunzip or unzip a payload when the source served it compressed.

    Some of these endpoints answer with gzip regardless of what the client asked for, and
    others hand back a zip container. Both are handled so the parsers downstream see plain
    bytes and never have to guess.
    """
    import gzip
    import io
    import zipfile

    if data[:2] == b"\x1f\x8b":
        return gzip.decompress(data)
    if data[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = [name for name in archive.namelist() if not name.endswith("/")]
            if not names:
                raise ValueError(f"zip container from {hint or 'unknown source'} is empty")
            chosen = names[0]
            if len(names) > 1:
                ranked = sorted(names, key=len)
                chosen = ranked[0]
            return archive.read(chosen)
    return data


def _contact_is_named(agent: str) -> bool:
    return bool(re.search(r"[^\s@]+@[^\s@]+\.[^\s@]+", agent))


def describe_environment() -> dict[str, Any]:
    """What the data layer can actually reach right now, for logging and for reports."""
    return {
        "user_agent_configured": bool(os.environ.get(USER_AGENT_ENVIRONMENT_VARIABLE, "").strip()),
        "cache_dir": str(default_cache_dir()),
        "cache_writable": shutil.disk_usage(default_cache_dir().parent).free > 0
        if default_cache_dir().parent.exists()
        else False,
        "fred_api_key_present": bool(os.environ.get("FRED_API_KEY", "").strip()),
    }
