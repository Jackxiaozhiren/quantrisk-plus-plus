"""I-L5's guard: the site build's offline facts must remain readable and falsifiable.

Section 49 bound the true network-down build to a Linux runner entering `sudo unshare -n`; this
macOS host cannot do that, so no OS-level offline measurement is asserted here. The guard covers
the readable half of the law: the lint job still carries a namespace step with a load-bearing
negative probe, the site generator's import closure contains no network module, and the committed
lock is still the rebuild target. Each fact is re-derived here from the file on disk, independent
of the producer's own result, so a producer that returned a fabricated `offline` flag could not
pass. The runner's printed PASS lines are attributed in the ledger to the CI job that emits them.

The platform side is falsified by the plant `offline-step-drops-its-negative-probe`, which removes
the probe from the workflow; the guard reads that file directly, so reddens.
"""

from __future__ import annotations

import ast

from quantrisk.experiments.metadata import REPO_ROOT
from quantrisk.interface import offline

CLAIMMAP_SOURCE = REPO_ROOT / "python" / "quantrisk" / "interface" / "offline.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
SITE_SOURCE = REPO_ROOT / "python" / "quantrisk" / "interface" / "site.py"
LEDGER = REPO_ROOT / "INTERFACE_LEDGER.md"


def _numeric_literals(source: str) -> list[float]:
    """Every int or float literal in a source string, in source order. Booleans are not numbers."""
    found: list[float] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if isinstance(node.value, bool):
                continue
            found.append(node.value)
    return found


def _workflow_step() -> str:
    """The offline step's block, read straight from ci.yml, independent of the producer."""
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    start = next((i for i, line in enumerate(lines) if offline.STEP_NAME in line), None)
    assert start is not None, f"the lint job lost its offline step {offline.STEP_NAME!r}"
    return "\n".join(lines[start:])


def _site_imports() -> list[str]:
    """Top-level names imported anywhere in the site generator, read from disk here."""
    tree = ast.parse(SITE_SOURCE.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module.split(".")[0])
    return names


def test_the_offline_build_facts_are_readable_and_falsifiable() -> None:
    """Guard behind plant `offline-step-drops-its-negative-probe`.

    Re-derive each offline fact from its own file, require the namespace step to carry both the
    unshare entry and a probe that must fail on an outbound socket, require the site generator to
    import no network module, and require the committed lock to name an index digest as the rebuild
    target. Then compare the producer's reading to the same derivation so a fabricated flag cannot
    pass. The ledger is named here so a plant editing it is bound to this guard's reading closure.
    """
    ledger = LEDGER.read_text(encoding="utf-8")
    assert "## 49." in ledger and "unshare -n" in ledger, (
        "the ledger no longer binds the offline route to a network namespace"
    )

    step = _workflow_step()
    assert offline.UNSHARE_TOKEN in step, "the offline step no longer enters a network namespace"
    assert "socket.create_connection" in step and "OFFLINE PROBE FAILED" in step, (
        "the offline step lost the negative probe that proves the namespace really isolates"
    )
    assert offline.PROBE_MARKER in step and offline.BUILD_MARKER in step, (
        "the offline step no longer prints the named markers the platform reading attributes"
    )
    assert "quantrisk.interface.drift" in step and "build/site.lock" in step, (
        "the offline step no longer rebuilds the site against the committed lock"
    )

    imported = _site_imports()
    offenders = sorted(set(imported) & set(offline.NETWORK_MODULES))
    assert not offenders, f"the site generator imported a network module: {offenders}"

    reading = offline.audit(REPO_ROOT)
    step_reading = reading["namespace_step"]
    for key in (
        "present",
        "unshare",
        "negative_probe",
        "probe_marker",
        "build_marker",
        "drift_check",
    ):
        assert step_reading[key] is True, f"the producer's {key} is not read as present: {reading}"
    assert reading["import_closure"]["network_imports"] == [], reading
    assert reading["import_closure"]["scanned"], "the import closure scanned no module"
    assert reading["lock"]["index_page_sha256"], "the lock named no digest as rebuild target"

    source = CLAIMMAP_SOURCE.read_text(encoding="utf-8")
    assert _numeric_literals("answer = 19\n") == [19], (
        "the scan missed a literal in a string known to contain one, so it would certify any file"
    )
    assert _numeric_literals(source) == [], (
        "the offline producer carries a numeric literal, so a figure could have come from a "
        "constant typed beside it"
    )
