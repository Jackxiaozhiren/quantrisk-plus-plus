r"""Build the technical report and record exactly which bytes produced it.

`docs/limitations.md` #90 registered the defect this script closes:
`paper/technical_report.pdf` is a second representation of `paper/technical_report.tex`, one
that a release attaches and a reader opens, and nothing re-derived it from the source. Every
numeric sentence in the tex is owned by a guard that reads the tex, so a phase that edited
the tex and committed the old render published a document quoting the superseded figure with
every gate green. It happened at `v1.7.0` (audit finding 55) and again inside the tree at
Phase 24 §8, and both times a human found it by running `pdftotext`.

The render cannot be made byte-reproducible: pdfTeX writes the creation date into the file,
so two builds of an unchanged source differ (`e72fcfc5…` and `ac7736aa…` for one identical
input measured on 2026-10-09), while the *text* they typeset is identical (`c5f09b1a…` both
times). So this script records a binding, not a reproduction: the digests of the sources
that produced the PDF bytes now in the tree, and the digest of the text those bytes render
to. A guard re-derives the source set from the document itself and reddens when the tree
moves under the record.

The source set is parsed rather than listed because the report does not read only its own
file: ``\graphicspath{{../}}`` plus ``\includegraphics{experiments/…/results/…png}`` means a
suite re-run that redraws a figure makes the committed PDF stale, and a hand-maintained
input list would go stale in exactly the way the phase set out to prevent.

Usage: ``uv run python scripts/build_report.py`` from the repository root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER = REPO_ROOT / "paper"
TEX = PAPER / "technical_report.tex"
PDF = PAPER / "technical_report.pdf"
SIDECAR = PAPER / "technical_report.build.json"
SCHEMA = "quantrisk-report-build/1"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def graphics_inputs(tex_text: str) -> list[str]:
    r"""Every repository-relative path the document pulls into the render.

    ``\graphicspath`` is read because it changes what a bare ``\includegraphics{name}`` resolves
    to; the report writes paths relative to the repository root and sets the path to ``../``, which
    is the same resolution seen from ``paper/``, where the build runs.
    """
    paths: list[str] = []
    for match in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", tex_text):
        for name in match.group(1).split():
            candidate = name.strip()
            if not candidate:
                continue
            if not candidate.endswith((".png", ".pdf", ".jpg", ".jpeg")):
                candidate = f"{candidate}.png"
            paths.append(candidate)
    return sorted(set(paths))


def bibliography_inputs(tex_text: str) -> list[str]:
    """The `.bib` files `\\bibliography{...}` names, resolved against `paper/`."""
    names: list[str] = []
    for match in re.finditer(r"\\bibliography\{([^}]*)\}", tex_text):
        for name in match.group(1).split(","):
            stem = name.strip()
            if stem:
                names.append(stem if stem.endswith(".bib") else f"{stem}.bib")
    return sorted(set(names))


def source_bundle() -> list[dict[str, Any]]:
    """The files the render consumes, each with its digest, sorted by repository-relative path."""
    tex_text = TEX.read_text(encoding="utf-8")
    relative = ["paper/technical_report.tex"]
    for name in bibliography_inputs(tex_text):
        relative.append(f"paper/{name}")
    for name in graphics_inputs(tex_text):
        relative.append(name)
    entries = []
    for item in sorted(set(relative)):
        path = REPO_ROOT / item
        if not path.is_file():
            raise FileNotFoundError(
                f"the report reads {item}, which is not in the tree: the render cannot include it"
            )
        entries.append({"path": item, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return entries


def bundle_digest(entries: list[dict[str, Any]]) -> str:
    """One digest over the input set, so a guard can compare the bundle in one assertion."""
    joined = "\n".join(f"{entry['path']} {entry['sha256']}" for entry in entries)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def run_build(force: bool) -> str:
    """Typeset the report and return the engine's own identification line."""
    if shutil.which("latexmk") is None:
        raise RuntimeError("latexmk is not on PATH; the report cannot be built in this environment")
    command = [
        "latexmk",
        "-pdf",
        "-interaction=nonstopmode",
        "technical_report.tex",
    ]
    if force:
        command.insert(1, "-g")
    completed = subprocess.run(
        command,
        cwd=PAPER,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or not PDF.is_file():
        tail = (completed.stdout + completed.stderr)[-1200:]
        raise RuntimeError(
            f"latexmk exited {completed.returncode}; the PDF was not written. {tail}"
        )
    log = (PAPER / "technical_report.log").read_text(encoding="utf-8", errors="replace")
    engine = next(
        (line.strip() for line in log.splitlines() if line.startswith("This is pdfTeX")), "unknown"
    )
    return engine


def text_digest() -> str | None:
    """The digest of the PDF's extracted text, or None where no poppler is installed.

    Recorded because it is the one property of the render that survives pdfTeX's date stamp, so it
    is the thing a rebuild can be compared against.
    """
    if shutil.which("pdftotext") is None:
        return None
    completed = subprocess.run(
        ["pdftotext", str(PDF), "-"],
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout:
        return None
    return hashlib.sha256(completed.stdout).hexdigest()


def build(force: bool) -> dict[str, Any]:
    entries = source_bundle()
    before = sha256_file(PDF) if PDF.is_file() else None
    engine = run_build(force=force)
    after = sha256_file(PDF) if PDF.is_file() else None
    if before is not None and before == after:
        raise RuntimeError(
            "latexmk reported success but left the PDF byte-identical to the render before it, "
            "cannot happen for a real build because pdfTeX stamps the creation date; refusing to "
            "write a record for bytes it did not produce"
        )
    return {
        "schema": SCHEMA,
        "command": "uv run python scripts/build_report.py",
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "engine": engine,
        "source_bundle": entries,
        "bundle_sha256": bundle_digest(entries),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256_file(PDF),
        "pdf_text_sha256": text_digest(),
        "note": (
            "pdf_sha256 changes on every rebuild because pdfTeX embeds the creation date, so it "
            "binds this record to these bytes rather than reproducing them. pdf_text_sha256 is the "
            "property that survives the stamp and is what a rebuild is compared against."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--if-stale",
        action="store_true",
        help="rebuild only when the record no longer matches the tree, which is what a release "
        "procedure wants",
    )
    arguments = parser.parse_args(argv)
    if arguments.if_stale and SIDECAR.is_file():
        recorded = json.loads(SIDECAR.read_text(encoding="utf-8"))
        if recorded.get("bundle_sha256") == bundle_digest(source_bundle()):
            print(f"report is current: bundle {recorded['bundle_sha256'][:12]} matches the tree")
            return 0
    record = build(force=True)
    SIDECAR.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"bundle": record["bundle_sha256"][:12], "pdf": record["pdf_sha256"][:12]}))
    print(
        f"wrote {SIDECAR.relative_to(REPO_ROOT)}: {len(record['source_bundle'])} sources, "
        f"PDF {record['pdf_bytes']} bytes, engine {record['engine'][:40]}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
