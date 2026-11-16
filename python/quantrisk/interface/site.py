"""A surface generated from the evidence chain, so that no page can disagree with the artifact beside it.

The interface lane's one law about surfaces is "generated, never retyped", and this module is the
smallest thing that can honour it: it reads committed artifacts, reads the manifest that froze them,
and writes pages whose every figure came from those files during the build. The failure it exists to
prevent is a comfortable one — typing "every registered study" into a template, then discovering a
year later that the sentence and the registry parted company.

Three rules constrain the code rather than the output.

The build reads, and refuses to guess. A task whose artifact is present but missing from
`evidence/manifest.json`, or whose bytes no longer hash to the digest the manifest froze, raises
`SiteRefused` and writes nothing: a page quoting a digest its own bytes do not have is worse than no
page, because it looks checkable.

The build never consults the clock or the network. Every page carries the artifact's own
`generated_utc`, never the moment of the build, so two builds of one tree are byte-identical and a
difference between them is a difference in the evidence.

This file contains no numeric literal, and `LAYOUT_NUMBERS` names the allowance that makes that
statement mechanically checkable. It is empty because an unstyled document needs no width, no padding
and no precision constant; styling belongs to the unit that adds the drift gate, where a rendered
surface can be policed. The guard in `tests/python/test_interface_site.py` reads this set, so
widening it is a visible act rather than an accident, and a page that wants a number has to get it
from the artifact.

The invocation is `python -m quantrisk.interface.site --out <directory>`, deliberately not a CLI
subcommand: the roadmap's third prerequisite counts exactly four subcommands, and a generator is not
one of them.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any, Sequence

from ..checkout import checkout_root
from ..experiments.metadata import sha256_file
from ..experiments.registry import TASKS, Task

MANIFEST = Path("evidence") / "manifest.json"

DOCUMENT_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
</head>
<body>
"""

DOCUMENT_TAIL = """</body>
</html>
"""

LAYOUT_NUMBERS: frozenset[int] = frozenset()
"""Every numeric literal this module may contain, declared so the rule can be enforced.

Empty on purpose. A generator that needs a layout constant is no longer the module described above,
and the guard would rather fail than let the allowance grow quietly.
"""

SAFE_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")


class SiteRefused(RuntimeError):
    """A page would have to be written without the provenance that makes it checkable."""


def _text(value: Any) -> str:
    """A value as the page shows it: strings as themselves, everything else as canonical JSON."""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _escaped(value: Any) -> str:
    return html.escape(_text(value), quote=True)


def _manifest_entries(root: Path) -> dict[str, dict[str, Any]]:
    document = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    return {str(entry["path"]): entry for entry in document["artifacts"]}


def _provenance(task: Task, root: Path, entries: dict[str, dict[str, Any]]) -> dict[str, str]:
    """The four fields a page may not be written without, or a refusal naming the missing one."""
    entry = entries.get(task.artifact)
    if entry is None:
        raise SiteRefused(
            f"{task.task_id}: {task.artifact} is absent from {MANIFEST.as_posix()}, so the page "
            f"would carry no recorded command and no digest; refusing to write it"
        )
    digest = sha256_file(root / task.artifact)
    frozen = str(entry.get("sha256") or "")
    if digest != frozen:
        raise SiteRefused(
            f"{task.task_id}: {task.artifact} hashes to {digest}, the manifest froze {frozen}; "
            f"refusing to publish a digest the artifact's own bytes do not have"
        )
    command = str(entry.get("generated_by_command") or "")
    if not command:
        raise SiteRefused(
            f"{task.task_id}: {MANIFEST.as_posix()} records no command for {task.artifact}, so the "
            f"page would show a number nobody could run; refusing to write it"
        )
    return {
        "path": task.artifact,
        "sha256": digest,
        "command": command,
        "generated": str(entry.get("generated_utc") or ""),
    }


def _definition_list(fields: dict[str, str]) -> str:
    return "\n".join(
        f"    <dt>{_escaped(name)}</dt><dd><code>{_escaped(value)}</code></dd>"
        for name, value in fields.items()
    )


def _headline_table(headline: Any) -> str:
    if not isinstance(headline, dict) or not headline:
        return "  <p>this artifact records no headline</p>"
    rows = "\n".join(
        f"      <tr><th>{_escaped(name)}</th><td>{_escaped(value)}</td></tr>"
        for name, value in headline.items()
    )
    return f"  <table>\n{rows}\n  </table>"


def _study_page(task: Task, artifact: dict[str, Any], provenance: dict[str, str]) -> str:
    claim = artifact.get("claim")
    claim_html = _escaped(claim) if claim else "this artifact records no claim"
    body = f"""{DOCUMENT_HEAD.format(title=_escaped(task.task_id))}  <h1>{_escaped(task.task_id)}</h1>
  <p>category: {_escaped(task.category)}</p>
  <h2>Claim</h2>
  <p>{claim_html}</p>
  <h2>Headline</h2>
{_headline_table(artifact.get("headline"))}
  <h2>Provenance</h2>
  <dl>
{_definition_list(provenance)}
  </dl>
  <p>This page is generated from the artifact named above by
  <code>python -m quantrisk.interface.site</code>. No figure on it is typed by hand.</p>
{DOCUMENT_TAIL}"""
    return body


def _index_row(task: Task, provenance: dict[str, str] | None) -> str:
    if provenance is None:
        return (
            f"      <tr><th>{_escaped(task.task_id)}</th><td>{_escaped(task.category)}</td>"
            f"<td>{_escaped(task.artifact)}</td><td>artifact not present in this tree</td></tr>"
        )
    return (
        f'      <tr><th><a href="{_escaped(task.task_id)}.html">{_escaped(task.task_id)}</a></th>'
        f"<td>{_escaped(task.category)}</td><td>{_escaped(provenance['path'])}</td>"
        f"<td><code>{_escaped(provenance['sha256'])}</code></td></tr>"
    )


def _index_page(rows: list[str]) -> str:
    joined = "\n".join(rows)
    return f"""{DOCUMENT_HEAD.format(title="QuantRisk++ evidence")}  <h1>QuantRisk++ evidence</h1>
  <p>Every page below is generated from a committed artifact by
  <code>python -m quantrisk.interface.site</code>. Each one shows the artifact it was read from, that
  artifact's digest, and the command the manifest records for it; a task whose artifact is not in this
  tree is listed as absent rather than described.</p>
  <table>
    <tr><th>study</th><th>category</th><th>artifact</th><th>sha256</th></tr>
{joined}
  </table>
{DOCUMENT_TAIL}"""


def generate(out: Path, root: Path | None = None) -> list[Path]:
    """Write one page per registered study plus an index, and return the files written."""
    base = checkout_root() if root is None else Path(root)
    entries = _manifest_entries(base)
    out.mkdir(parents=True, exist_ok=True)
    pages: list[Path] = []
    rows: list[str] = []
    for task in TASKS:
        if not SAFE_IDENTIFIER.match(task.task_id):
            raise SiteRefused(
                f"{task.task_id!r} is not a safe file name: this generator will not write a page "
                f"whose name a registry entry could aim outside the output directory"
            )
        artifact_path = base / task.artifact
        if not artifact_path.is_file():
            rows.append(_index_row(task, None))
            continue
        provenance = _provenance(task, base, entries)
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        page = out / f"{task.task_id}.html"
        page.write_text(_study_page(task, artifact, provenance), encoding="utf-8")
        pages.append(page)
        rows.append(_index_row(task, provenance))
    index = out / "index.html"
    index.write_text(_index_page(rows), encoding="utf-8")
    pages.append(index)
    return pages


def main(argv: Sequence[str] | None = None) -> None:
    """Write the pages, and say how many. Returns nothing so that no exit code literal is needed."""
    parser = argparse.ArgumentParser(
        description="Generate the evidence site from committed artifacts."
    )
    parser.add_argument("--out", required=True, help="directory the pages are written into")
    arguments = parser.parse_args(argv)
    pages = generate(Path(arguments.out))
    print(f"wrote {len(pages)} file(s) to {arguments.out}")


if __name__ == "__main__":
    main()
