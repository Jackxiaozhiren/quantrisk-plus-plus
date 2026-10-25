#!/usr/bin/env python3
"""Re-wrap over-long docstring prose in one file without changing a single word.

Why a script rather than hand edits: the gate is E501, the fix is only line breaks, and a hand
re-wrap of nine paragraphs drops or reorders a word now and then -- which is a documentation
defect smuggled in through a formatting repair, in a repository whose whole subject is that a
transcribed figure must be checkable. So this refuses to write unless it can prove, per file,
that the change was whitespace: the whitespace-split word tuple of every docstring is identical
before and after, and the parsed tree with docstring whitespace folded is byte-identical, so no
other literal -- an assert message, a regex, a path -- can have moved.

It lived in `build/` for four phases, which is gitignored. That made it invisible to the next
session: a tool that survives by being re-typed from conversation is a tool that will be re-typed
wrong, and its proof is the kind of thing worth having once rather than re-deriving.

Usage: `uv run python -m tools.rewrap_docstrings <path.py> [--apply]`

`tests/python/test_rewrap_docstrings.py` holds the proof to the tool: a lossy rewrite is refused,
the output respects the project's own line-length, code outside docstrings is untouched, and a
second run finds nothing to do.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

QUOTE = '"""'


def line_length() -> int:
    """The project's own E501 limit, read from `pyproject.toml` rather than copied here.

    A width typed twice is two facts, and the one that goes stale is the one that lets the tool
    write lines a gate rejects.
    """
    config = Path(__file__).resolve().parent.parent / "pyproject.toml"
    for line in config.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("line-length"):
            return int(line.split("=", 1)[1].strip())
    raise AssertionError(f"{config.name} declares no line-length for the tool to respect")


def docstrings(tree: ast.AST) -> list[tuple[str, int, int, str]]:
    """Every literal docstring in the tree as (owner name, start, end, its text).

    The text comes from `ast`, not from the source lines, because a line-joined proxy would carry
    the wrapping in its own value: re-wrapping alone would then look like a word change.
    """
    found: list[tuple[str, int, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        text = ast.get_docstring(node, clean=False)
        if text is None:
            continue
        statement = node.body[0]
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Constant):
            continue
        literal = statement.value
        # A parsed tree always positions a literal it can print; the guard is what lets the tuple be
        # typed, since a docstring without a line range could not be re-wrapped into one either.
        if literal.lineno is None or literal.end_lineno is None:
            continue
        name = str(getattr(node, "name", "<module>"))
        found.append((name, literal.lineno, literal.end_lineno, text))
    return sorted(found, key=lambda item: item[1])


def words(text: str) -> tuple[str, ...]:
    return tuple(text.split())


def wrap_run(run: list[str], indent: str, continued: str, width: int) -> list[str]:
    """Greedily fill `run` (a list of stripped lines) into one paragraph at `width`.

    `continued` is the indent used after the first line, so a bullet's text hangs under its own
    marker instead of starting a new bullet.
    """
    out: list[str] = []
    line = ""
    first = True
    for chunk in " ".join(run).split(" "):
        pad = indent if first else continued
        candidate = f"{line} {chunk}" if line.strip() else f"{pad}{chunk}"
        if len(candidate) > width and line.strip():
            out.append(line)
            line = f"{continued}{chunk}"
        else:
            line = candidate
        first = False
    if line.strip():
        out.append(line)
    return out


def rewrap(paragraph: list[str], indent: str, width: int) -> list[str]:
    """Re-wrap one paragraph. Only the item's own first line carries its bullet marker."""
    lines = [line.rstrip() for line in paragraph]
    marker = ""
    if lines[0].lstrip().startswith("- "):
        marker = "- "
    elif lines[0].lstrip().startswith("* "):
        marker = "* "
    if marker:
        head = f"{indent}{marker}"
        chunks = [lines[0].strip()[2:]] + [line.strip() for line in lines[1:]]
        return wrap_run(chunks, head, indent + " " * len(marker), width)
    if any(len(line) > width for line in lines):
        return wrap_run([line.strip() for line in lines], indent, indent, width)
    return lines


def base_indent(body: list[str]) -> str:
    """The docstring's own indentation, so a deeper line means a literal block.

    Hard-coding four spaces instead made every prose line of a four-space-indented docstring look
    like an indented example, and the sweep quietly did nothing.
    """
    indents = [len(line) - len(line.lstrip()) for line in body if line.strip()]
    return " " * min(indents) if indents else "    "


def split_paragraphs(body: list[str], indent: str) -> list[tuple[list[str], bool]]:
    """Group body lines into (paragraph, literal) pairs.

    A run indented deeper than the docstring is a literal block and keeps its own line breaks. A
    bullet's continuation hangs two spaces under the marker, which is deeper than the block but
    not a literal block, so it joins its item instead of splitting it.
    """
    deeper = len(indent)
    groups: list[tuple[list[str], bool]] = []
    current: list[str] = []
    for line in body:
        stripped = line.strip()
        line_indent = len(line) - len(line.lstrip())
        if not stripped:
            if current:
                groups.append((current, False))
                current = []
            groups.append(([line], True))
            continue
        in_bullet = bool(current) and current[0].lstrip().startswith(("- ", "* "))
        if in_bullet and stripped.startswith(("- ", "* ")):
            groups.append((current, False))
            current = []
        hanging = in_bullet and line_indent == deeper + 2
        is_literal = stripped.startswith(">>>") or (line_indent > deeper and not hanging)
        if is_literal:
            if current:
                groups.append((current, False))
                current = []
            groups.append(([line], True))
            continue
        current.append(line)
    if current:
        groups.append((current, False))
    return groups


def collapse_blanks(lines: list[str]) -> list[str]:
    """One blank line between paragraphs, whatever the wrapping produced."""
    out: list[str] = []
    for line in lines:
        if not line.strip() and out and not out[-1].strip():
            continue
        out.append(line)
    while out and not out[-1].strip():
        out.pop()
    return out


def rewrap_block_group(groups: list[list[str]], indent: str, width: int) -> list[str]:
    out: list[str] = []
    for group in groups:
        out.extend(rewrap(group, indent, width))
        out.append("")
    while out and out[-1] == "":
        out.pop()
    return out


def flatten(groups: list[tuple[list[str], bool]], indent: str, width: int) -> list[str]:
    """Re-join, but a literal block keeps its own lines instead of being reflowed."""
    out: list[str] = []
    pending: list[list[str]] = []
    for lines, literal in groups:
        if literal:
            if pending:
                out.extend(rewrap_block_group(pending, indent, width))
                pending = []
            out.extend(lines)
        else:
            pending.append(lines)
    if pending:
        out.extend(rewrap_block_group(pending, indent, width))
    return collapse_blanks(out)


def non_space(text: str) -> str:
    return "".join(text.split())


def signature(source: str) -> str:
    """The parsed tree with every docstring's whitespace folded, and no positions.

    This is the proof the sweep needs: a re-wrap may only ever change how a docstring is broken
    across lines, so with docstrings normalised the dumps must be identical. Every other literal
    in the file -- an assert message, a regex, a path -- is compared verbatim, and a code edit
    would show up as a structural difference.
    """
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if ast.get_docstring(node, clean=False) is None:
            continue
        statement = node.body[0]
        if (
            not isinstance(statement, ast.Expr)
            or not isinstance(statement.value, ast.Constant)
            or not isinstance(statement.value.value, str)
        ):
            continue
        statement.value.value = non_space(statement.value.value)
    return ast.dump(tree, include_attributes=False)


def rewrap_source(source: str, width: int) -> tuple[str, int]:
    """The rewrapped file and how many docstrings it moved, with the proof unchecked here."""
    lines = source.split("\n")
    blocks = docstrings(ast.parse(source))
    reflowed = 0
    for _name, start, end, _text in reversed(blocks):
        block = lines[start - 1 : end]
        if all(len(line) <= width for line in block) or len(block) < 3:
            continue
        tail = block[-1]
        if tail.strip() != QUOTE:
            continue
        rebuilt = [block[0]]
        indent = base_indent(block[1:-1])
        rebuilt.extend(flatten(split_paragraphs(block[1:-1], indent), indent, width))
        rebuilt.append(tail)
        lines[start - 1 : end] = rebuilt
        reflowed += 1
    return "\n".join(lines), reflowed


def verify(source: str, after: str) -> list[str]:
    """Every way the rewrite is allowed to differ from the input, and the ones it is not."""
    problems: list[str] = []
    before_blocks = docstrings(ast.parse(source))
    after_blocks = docstrings(ast.parse(after))
    if len(after_blocks) != len(before_blocks):
        problems.append(f"docstring count {len(before_blocks)} -> {len(after_blocks)}")
    if sorted(words(text) for _, _, _, text in after_blocks) != sorted(
        words(text) for _, _, _, text in before_blocks
    ):
        problems.append("a docstring's words changed")
    if signature(after) != signature(source):
        problems.append("something other than docstring whitespace changed")
    return problems


def process(path: Path, apply_changes: bool, width: int | None = None) -> int:
    """Rewrap one file, print the tally and the proof, and write only if the proof holds."""
    limit = width if width is not None else line_length()
    source = path.read_text(encoding="utf-8")
    after, reflowed = rewrap_source(source, limit)
    problems = verify(source, after)
    over = [(i + 1, len(line)) for i, line in enumerate(after.split("\n")) if len(line) > limit]
    print(f"docstrings reflowed: {reflowed}")
    print(f"lines still longer than {limit}: {over}")
    print(f"proof: {'FAIL: ' + '; '.join(problems[:8]) if problems else 'whitespace-only'}")
    if problems:
        return 1
    if apply_changes:
        path.write_text(after, encoding="utf-8")
        print(f"applied to {path}")
    else:
        # The tally above describes the rewrite this run *would* make. Without this line a dry run
        # reads as a completed one, and the file stays exactly as ruff last saw it.
        print(f"dry run: {path} not written; pass --apply to write the rewrite")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Re-wrap docstring prose to the project width.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    return process(args.path, args.apply)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
