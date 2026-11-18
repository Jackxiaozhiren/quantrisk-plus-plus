"""Three liveness readings, each falsifiable, on the surface X5 published.

The liveness table may only be filled "from readings, not by editing prose" (ledger section 2).
I-L3, I-L4 and I-L6 stayed VOID because no published surface existed to bind a target to. X5
created one; these guards bind each claim to an executable target, and a named plant makes each
one able to turn red. Each guard reads the file on disk rather than an imported object, so a
plant that edits that file is visible to the guard in its own pytest process.

- I-L3: the published pages carry no request-execution path — no script, inline handler, fetch,
  XHR, external URL or stylesheet import. A page that needed the browser to do work could differ
  from the artifact it quotes.
- I-L4: the publish infrastructure stays on the free tier — only official, no-cost GitHub actions,
  no stored secret and no new account — so the cost basis excludes AI tokens and stays at zero.
- I-L6: the machine-readable surface is the module-path provenance command; `--json` returns the
  value together with command, revision and digest, never a bare number, and it stays off HTTP.
"""

from __future__ import annotations

import ast
import json
import tempfile
from pathlib import Path

import yaml
from quantrisk.experiments.metadata import REPO_ROOT
from quantrisk.interface import provenance

SITE_SOURCE = REPO_ROOT / "python" / "quantrisk" / "interface" / "site.py"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PROVENANCE_SOURCE = REPO_ROOT / "python" / "quantrisk" / "interface" / "provenance.py"

# Markers that would make a page execute a request or run code in the browser rather than be a
# static rendition of the artifact. Matched case-insensitively in generated markup.
REQUEST_EXECUTION = (
    "<script",
    "onclick=",
    "onload=",
    "onerror=",
    "fetch(",
    "xmlhttprequest",
    "<iframe",
    "@import",
    "javascript:",
    'src="http',
    'href="http',
)

# The whole publish chain is built from these first-party, no-cost actions; none stores a secret
# or needs a paid tier. A new action is a cost and trust decision, so the guard names the set.
FREE_ACTIONS = (
    "actions/checkout@",
    "actions/setup-python@",
    "astral-sh/setup-uv@",
    "actions/upload-artifact@",
    "actions/upload-pages-artifact@",
    "actions/deploy-pages@",
)

SAMPLE_ARTIFACT = "experiments/sixth_book_crossing_map/results/sixth_book_crossing_map.json"


def test_published_pages_carry_no_request_execution_path() -> None:
    """Guard behind plant `site-page-gains-a-request-execution-path`.

    Every published page is a static rendition of its artifact. A script, an inline handler, a
    fetch or an external URL would let the browser do work the build did not verify, so a figure
    on the page could come from somewhere other than the artifact it quotes.
    """
    from quantrisk.interface import site as site_module

    # The template source is part of the published path: read it on disk here as well, so a plant
    # that edits the template is visible to this guard's own reading closure, not only to the
    # generated-page half below.
    source = SITE_SOURCE.read_text(encoding="utf-8").lower()
    for marker in ("<script", "onclick=", "onload=", "fetch(", "xmlhttprequest"):
        assert marker not in source, (
            f"the site generator carries a request-execution template: {marker}"
        )

    with tempfile.TemporaryDirectory() as directory:
        pages = site_module.generate(Path(directory))
        assert pages, "no pages were generated, so this guard certifies nothing"
        rendered = {page.name: page.read_text(encoding="utf-8").lower() for page in pages}

    offenders: list[str] = []
    for name, markup in rendered.items():
        for marker in REQUEST_EXECUTION:
            if marker in markup:
                offenders.append(f"{name}: {marker}")
    assert not offenders, f"published pages contain request-execution paths: {offenders}"


def test_the_publish_chain_stays_on_the_free_tier() -> None:
    """Guard behind plant `publish-chain-adds-a-paid-action`.

    The publish chain uses only first-party, no-cost actions and the short-lived OIDC token; it
    stores no secret and needs no paid account. The cost basis is the publish infrastructure and
    explicitly excludes the AI-token question O11, which stays unadjudicated.
    """
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    publish_jobs = {
        name: job
        for name, job in (workflow.get("jobs") or {}).items()
        if name == "deploy" or job.get("name") == "Publish the evidence site"
    }
    assert publish_jobs, "no publish job exists, so the free-tier guard certifies nothing"

    used: set[str] = set()
    for job in publish_jobs.values():
        for step in job.get("steps") or []:
            uses = str(step.get("uses", ""))
            if not uses:
                continue
            action, _, _ref = uses.partition("@")
            used.add(f"{action}@")
    unknown = sorted(used - set(FREE_ACTIONS))
    assert not unknown, f"publish chain added an action outside the free first-party set: {unknown}"

    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "secrets." not in text and "${{ secrets" not in text, (
        "a stored secret appeared in the publish workflow, "
        "so the chain is no longer credential-free"
    )


def test_the_machine_readable_surface_is_module_path_and_keeps_provenance() -> None:
    """Guard behind plant `machine-readable-surface-drops-a-provenance-field`.

    I-L6's response surface is `provenance --resolve --json`: a module-path invocation (never a new
    CLI subcommand), returning the value together with command, revision and digest. Dropping any
    provenance field from the JSON response would leave a bare number, which the guard refuses.
    """
    source = PROVENANCE_SOURCE.read_text(encoding="utf-8")
    assert "def main(" in source and "__main__" in source, "the module-path entry point vanished"

    record = provenance.resolve(SAMPLE_ARTIFACT)
    rendered = json.loads(provenance._render(record, True))
    for field in ("value", "command", "revision", "sha256"):
        assert rendered.get(field), f"the machine-readable answer omitted {field}"

    # No HTTP surface: the module imports no server/framework/socket library. Read the AST, not
    # the text, because the docstring itself explains that the surface "opens no socket".
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    forbidden = {"socket", "http", "flask", "fastapi", "aiohttp", "uvicorn", "starlette"}
    present = imported & forbidden
    assert not present, (
        f"an HTTP/service surface was imported into the provenance module: {present}"
    )


def test_generated_markup_source_has_no_script_template() -> None:
    """The generator's templates themselves must not contain a script or external request.

    This reads the source on disk so a plant editing the page template is visible. It is the
    source-level half of I-L3, complementing the generated-page reading above.
    """
    source = SITE_SOURCE.read_text(encoding="utf-8")
    lowered = source.lower()
    for marker in ("<script", "onclick=", "onload=", "fetch(", "xmlhttprequest", "@import"):
        assert marker not in lowered, (
            f"the site generator carries a request-execution template: {marker}"
        )
