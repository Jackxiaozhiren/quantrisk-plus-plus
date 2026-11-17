"""The publication job is worth testing only if the gate it depends on can stop it.

X5 publishes the artifact-bound site from CI. Three properties make that a claim rather than a
hope: the job is downstream of the lint gate that runs the drift check, the bytes it uploads are
the ones that check rebuilt and verified, and it adds no stored secret — only GitHub's per-deploy
Pages write and short-lived OIDC token. A workflow is YAML, so a grep can lose a renamed job or a
dropped dependency and still report green; this module reads the parsed structure the same way the
lane contract does.

The first test is the guard behind the controlled plant. Removing the `needs: [lint]` edge makes
publication independent of the drift gate, and the guard must object.
"""

from __future__ import annotations

import yaml
from quantrisk.experiments.metadata import REPO_ROOT

CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

ALLOWED_PERMISSIONS = {"contents", "pages", "id-token"}
REQUIRED_COMMANDS = (
    "quantrisk.interface.drift",
    "actions/upload-pages-artifact",
    "actions/deploy-pages",
)


def _deploy_job() -> dict:
    """Parse the workflow and return the deploy job, refusing an absent or ambiguous one."""
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    jobs = workflow.get("jobs") or {}
    named = [job for key, job in jobs.items() if job.get("name") == "Publish the evidence site"]
    assert len(named) == 1, (
        f"expected exactly one job named 'Publish the evidence site', found {len(named)}"
    )
    return named[0]


def test_publication_is_downstream_of_the_drift_gate() -> None:
    """Guard behind plant `deploy-drops-the-lint-dependency`.

    The lint job runs the drift check; deploy must require it. If the edge is dropped, a figure
    that drifted past the digest gate could be published without anyone checking the page.
    """
    job = _deploy_job()
    needs = job.get("needs") or []
    if isinstance(needs, str):
        needs = [needs]
    assert "lint" in needs, (
        f"the deploy job does not require lint, so the drift gate no longer blocks publication: "
        f"needs={needs}"
    )
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    lint_steps = workflow["jobs"]["lint"].get("steps") or []
    gate_names = [
        str(step.get("name", "")) for step in lint_steps if "drift" in str(step.get("run", ""))
    ]
    assert "site drift gate" in gate_names, (
        f"the lint job no longer runs the drift gate that deploy claims to depend on: {gate_names}"
    )


def test_publication_uploads_the_bytes_the_gate_verified() -> None:
    """The upload directory is the same directory the drift check rebuilt into."""
    job = _deploy_job()
    runs = [str(step.get("run", "")) for step in job.get("steps") or []]
    drift_runs = [run for run in runs if "quantrisk.interface.drift" in run and "--check" in run]
    assert drift_runs, "deploy never rebuilds and verifies the site against its frozen lock"
    assert "--out" in drift_runs[0], "the drift check does not name the directory it verified"
    assert "site-publish" in drift_runs[0], (
        "the verified directory is not the one the upload step publishes"
    )
    uploads = [
        step
        for step in job.get("steps") or []
        if str(step.get("uses", "")).startswith("actions/upload-pages-artifact@")
    ]
    assert len(uploads) == 1, "expected exactly one Pages upload step"
    assert "site-publish" in str(uploads[0].get("with", {}).get("path", "")), (
        "the Pages upload does not publish the bytes the drift check verified"
    )
    deploys = [
        step
        for step in job.get("steps") or []
        if str(step.get("uses", "")).startswith("actions/deploy-pages@")
    ]
    assert len(deploys) == 1, "expected exactly one Pages deploy step"


def test_publication_adds_no_stored_secret() -> None:
    """Only the built-in Pages write and short-lived OIDC token are added."""
    job = _deploy_job()
    permissions = job.get("permissions") or {}
    extra = sorted(set(permissions) ^ ALLOWED_PERMISSIONS)
    assert set(permissions) == ALLOWED_PERMISSIONS, (
        f"deploy permissions beyond the allowed set: {extra}"
    )
    assert permissions.get("pages") == "write", "Pages write is required to publish"
    assert permissions.get("id-token") == "write", "the short-lived OIDC token is required"
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "secrets." not in text, "a stored secret appeared in the workflow"
    assert "${{ secrets" not in text, "a stored secret appeared in the workflow"


def test_publication_runs_only_on_main_pushes() -> None:
    """A publish is a main-branch push event, never a pull request or a tag."""
    job = _deploy_job()
    condition = str(job.get("if", ""))
    assert "refs/heads/main" in condition, f"deploy is not limited to the main branch: {condition}"
    assert "push" in condition, f"deploy is not limited to push events: {condition}"
    assert "pull_request" not in condition, "deploy must not run on a pull request"


def test_publication_never_moves_a_tag() -> None:
    """A publish must not create, move or delete a git tag."""
    job = _deploy_job()
    for step in job.get("steps") or []:
        run = str(step.get("run", "")).lower()
        assert " git tag" not in run and "git push" not in run, (
            f"a deploy step would write to git refs: {step.get('name')}"
        )
