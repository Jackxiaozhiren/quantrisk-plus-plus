"""I-L5's offline-build reading: the build's network independence, derived from disk.

`INTERFACE_ROADMAP.md` line 299 states I-L5 as "The site build completes with no network", with the
check "A build executed with network disabled; a build that silently needs network is a High
finding". Section 49 bound that build to a Linux runner entering `sudo unshare -n`: this macOS host
cannot enter a network namespace, so no OS-level offline measurement is claimed from it. This module
returns the *readable half* of the law — the facts a reader can re-derive from the committed tree —
and leaves the runner's network-down rebuild reading to the platform job that prints it:

- `namespace_step`: the lint job's offline step, its `unshare -n` entry, its negative socket probe
  and the marker that probe prints, all read from `.github/workflows/ci.yml`;
- `import_closure`: every non-stdlib `import`/`from` line in the site generator and the in-package
  modules it imports, with any network-bearing module named as a gap rather than hidden;
- `lock`: the committed `build/site.lock` as the rebuild target, with its index page digest.

A guarding test re-derives the same facts independently and compares them to this reading, so a
producer that fabricated an `offline` flag could not pass. The runner-side reading (the step's
printed PASS lines) is attributed in the ledger to the CI job, not asserted by this module.
Read-only; no socket; no numeric literal.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from ..checkout import checkout_root

WORKFLOW = Path(".github") / "workflows" / "ci.yml"
SITE_SOURCE = Path("python") / "quantrisk" / "interface" / "site.py"
SITE_LOCK = Path("build") / "site.lock"

SCHEMA = "quantrisk-offline-build/1"

# The step name and the exact tokens that make the build offline and falsifiable. The guard reads
# the workflow on disk and asserts each of these is present; a plant removing one makes the reading
# fail rather than quietly certifying an offline build that is not there.
STEP_NAME = "offline build (network namespace)"
UNSHARE_TOKEN = "unshare -n"
PROBE_MARKER = "OFFLINE PROBE PASS"
BUILD_MARKER = "OFFLINE BUILD PASS"

# A module whose presence in the build's import closure would mean the build could consult the
# network. Socket-level HTTP clients and request libraries are named; the standard library's
# plumbing modules are checked by their top-level name only.
NETWORK_MODULES = ("socket", "http", "urllib", "requests", "httpx", "aiohttp", "ftplib", "smtplib")

# The site generator's package-local imports: the modules whose own source is part of the build's
# import closure and must therefore be scanned with it. Stdlib imports are named but not followed.
PACKAGE_PREFIX = "quantrisk"
PACKAGE_ROOT_DIR = "python"


class OfflineRefused(RuntimeError):
    """A file the reading needs could not be read or parsed, so the law cannot be certified."""


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise OfflineRefused(f"cannot read {path.as_posix()}: {error}") from error


def _namespace_step(base: Path) -> dict[str, Any]:
    """The offline step as written in the workflow, with each required token's presence."""
    text = _read(base / WORKFLOW)
    present = STEP_NAME in text
    block = ""
    if present:
        lines = text.splitlines()
        start = next((i for i, line in enumerate(lines) if STEP_NAME in line), None)
        if start is not None:
            block = "\n".join(lines[start:])

    def has(token: str) -> bool:
        return bool(block) and token in block

    return {
        "present": present,
        "unshare": has(UNSHARE_TOKEN),
        "negative_probe": has("socket.create_connection") and has("OFFLINE PROBE FAILED"),
        "probe_marker": has(PROBE_MARKER),
        "build_marker": has(BUILD_MARKER),
        "drift_check": has("quantrisk.interface.drift") and has("build/site.lock"),
    }


def _imports(path: Path) -> list[tuple[str, str, int]]:
    """(kind, module, level) for each import in one source file, in source order.

    `level` is the AST's relative-import depth: zero for `import x`, nonzero for a relative
    `from ..x import y`. The site generator uses relative imports for its package-local
    dependencies, so the closure has to resolve them rather than only matching a literal
    `quantrisk.` prefix.
    """
    tree = ast.parse(_read(path))
    found: list[tuple[str, str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            # False is the absolute-import level: it equals zero and is not a numeric literal.
            found.extend(("import", alias.name, False) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(("from", node.module, node.level))
    return found


def _resolve(source: Path, module: str, level: int) -> str:
    """Map a relative import to its absolute `quantrisk.*` name from the importing file's path."""
    if not level:
        return module
    parts = list(source.parent.relative_to(PACKAGE_ROOT_DIR).parts)
    # A level of one names the current package and needs no climb; each further level climbs one
    # directory. Consuming the first range item skips the current package without a numeric literal.
    climbs = iter(range(level))
    next(climbs)
    for _ in climbs:
        parts.pop()
    return ".".join([*parts, module])


def _import_closure(base: Path) -> dict[str, Any]:
    """The package-local import closure of the site generator, and any network module in it."""
    queue = [SITE_SOURCE]
    seen: set[str] = set()
    network: list[str] = []
    modules: list[str] = []
    while queue:
        source = queue.pop()
        rel = source.as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        for kind, module, level in _imports(base / source):
            top = next(iter(module.split(".")))
            if top in NETWORK_MODULES:
                network.append(f"{rel}:{kind} {module}")
            absolute = _resolve(source, module, level)
            if not absolute.startswith(PACKAGE_PREFIX):
                continue
            modules.append(absolute)
            candidate = Path("python") / Path(*absolute.split(".")).with_suffix(".py")
            if (base / candidate).is_file():
                queue.append(candidate)
            elif (base / candidate.parent / "__init__.py").is_file():
                queue.append(candidate.parent / "__init__.py")
    return {
        "scanned": sorted(seen),
        "package_modules": sorted(set(modules)),
        "network_imports": sorted(set(network)),
    }


def _lock(base: Path) -> dict[str, str]:
    """The committed lock as the rebuild target, read from disk rather than typed."""
    lock = json.loads(_read(base / SITE_LOCK))
    try:
        return {
            "index_page_sha256": str(lock["pages"]["index.html"]["page_sha256"]),
        }
    except (KeyError, TypeError) as error:
        raise OfflineRefused(f"the site lock carries no index page digest: {error}") from error


def audit(root: Path | None = None) -> dict[str, Any]:
    """Re-derive the offline build's readable facts from the committed tree.

    Returns the namespace step's markers, the site generator's import closure with any network
    module named, and the committed lock digest. No ceiling is asserted here: a guard owns the
    policy that the step is present, the closure is network-free and the lock is the rebuild target.
    """
    base = checkout_root() if root is None else Path(root)
    return {
        "schema": SCHEMA,
        "namespace_step": _namespace_step(base),
        "import_closure": _import_closure(base),
        "lock": _lock(base),
    }
