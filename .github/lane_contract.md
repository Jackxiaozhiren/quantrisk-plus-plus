# The lane contract

`V3_PROMPT.md` §5 and N3 ask for a contract a reader can open: every gate a document or a policy file
claims is executed somewhere the contract names, and every gate that is deliberately *not* executed
carries its reason here. V3 shipped the `validate` row inside a pytest guard instead of as a file, and
closed with N3 marked PARTIAL. This file is the declaration; the reading that checks it is
`lanes_documented_vs_executed` in `tools/inventory_orphan_code.py`, and the gate that can redden it is
`lanes_documented_vs_executed_gap` in `tools/refactor_ceilings.json`.

**What a lane is here.** A module-path invocation (`-m tools.*` or `-m quantrisk.*`) or a console
subcommand (`quantrisk <subcommand>`) that appears in either of the two lane-bearing documents —
`docs/reproducibility.md` and `CONTRIBUTING.md` — or in a `run:` line of
`.github/workflows/ci.yml`. Nothing else counts: `cmake`, `ctest`, `ruff`, `mypy` and `clang-format`
are steps of jobs, not lanes with a separate declaration, and they are already policed by the
static-check and formatter censuses.

**The two enumerations are printed, never assumed empty.** The reading prints the documented set, the
executed set, and both differences. A difference is allowed only in the direction
`documented → dev-only`, and only when the row below names a reason. The other direction — a command
the workflow runs that neither document claims — is a defect, repaired by documenting the command
rather than by adding an exemption. An executed row must name the job and the step that actually
contain it, and the comparison checks that pair against the parsed workflow. A dev-only row must not
appear in the executed set.

`quantrisk benchmark` and `quantrisk demo` are not lanes in this contract. They are declared
in-process-only, with reasons, in
`tests/python/test_artifact_metadata.py::test_the_ci_lane_that_runs_the_guards_fetches_what_they_read`;
no document claims them as a command to run and no CI step invokes them.

```json
{
  "schema": "quantrisk-lane-contract/1",
  "lanes": [
    {
      "command": "quantrisk run",
      "status": "executed",
      "claimed_by": ["docs/reproducibility.md", "CONTRIBUTING.md"],
      "ci_job": "build-and-test",
      "ci_step": "study-catalogue",
      "environment": "ubuntu-latest",
      "reason": ""
    },
    {
      "command": "quantrisk validate",
      "status": "executed",
      "claimed_by": ["docs/reproducibility.md", "CONTRIBUTING.md"],
      "ci_job": "build-and-test",
      "ci_step": "Validate installed CLI",
      "environment": "ubuntu-latest",
      "reason": ""
    },
    {
      "command": "tools.run_benchmark_suite",
      "status": "executed",
      "claimed_by": ["docs/reproducibility.md", "CONTRIBUTING.md"],
      "ci_job": "benchmark-suite",
      "ci_step": "Run every benchmark and experiment",
      "environment": "ubuntu-latest",
      "reason": ""
    },
    {
      "command": "tools.verify_evidence_manifest",
      "status": "executed",
      "claimed_by": ["docs/reproducibility.md", "CONTRIBUTING.md"],
      "ci_job": "lint",
      "ci_step": "evidence manifest",
      "environment": "ubuntu-latest",
      "reason": ""
    },
    {
      "command": "tools.inventory_orphan_code",
      "status": "executed",
      "claimed_by": ["docs/reproducibility.md"],
      "ci_job": "lint",
      "ci_step": "refactor ceilings",
      "environment": "ubuntu-latest",
      "reason": ""
    },
    {
      "command": "quantrisk.verification.runner",
      "status": "dev-only",
      "claimed_by": ["CONTRIBUTING.md"],
      "ci_job": null,
      "ci_step": null,
      "environment": "local",
      "reason": "the mutation sweep writes gitignored scratch into the checkout and rewrites tracked files one at a time; a runner that evaluated its own ceiling key could not fail on the scratch it never has, so the verdict is the sweep's own summary line recorded in the ledger"
    },
    {
      "command": "tools.build_evidence_manifest",
      "status": "dev-only",
      "claimed_by": ["docs/reproducibility.md", "CONTRIBUTING.md"],
      "ci_job": null,
      "ci_step": null,
      "environment": "local",
      "reason": "K4 freezes the 95-entry evidence chain with one re-run per series; running the producer on every push would rewrite frozen artifacts rather than verify them, so CI executes the verifier instead"
    },
    {
      "command": "tools.build_report",
      "status": "dev-only",
      "claimed_by": ["docs/reproducibility.md", "CONTRIBUTING.md"],
      "ci_job": null,
      "ci_step": null,
      "environment": "local",
      "reason": "re-rendering paper/technical_report.pdf needs a TeX distribution the runners do not install and changes a published byte-only artifact; the PDF source binding is checked by the report guards instead"
    }
  ]
}
```
