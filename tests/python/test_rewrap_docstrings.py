#!/usr/bin/env python3
"""Tests for `scripts/rewrap_docstrings.py`, the tool four phases ran from a gitignored directory.

A tool that only ever prints "proof: whitespace-only" has not shown anything: the proof is a
function that could return the empty list and the string it prints would not change. So these read
the tool's two promises from the outside -- it refuses a rewrite that loses a word, and it takes its
width from the project's own configuration rather than from a number typed twice -- and each is
paired with the case that must pass, because a refusal test with no accepted rewrite next to it
certifies a tool that refuses everything.

`python/quantrisk/verification/runner.py` carries two declared defects against this file:
`rewrap-tool-writes-anyway-after-losing-words` and `rewrap-tool-hardcodes-a-wider-line`.
"""

from __future__ import annotations

import importlib.util
import subprocess
import tomllib
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "scripts" / "rewrap_docstrings.py"

LONG = (
    "Re-wraps a paragraph that cannot fit the project line length because the sentence is long, "
    "the vocabulary is technical, and no reader would thank a tool that shortened it by dropping a "
    "word, so the only permitted change here is where the lines break."
)


def load_tool() -> Any:
    """The script as a module, by path, without touching `sys.path`."""
    spec = importlib.util.spec_from_file_location("rewrap_docstrings_under_test", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_module() -> str:
    """A file with one over-long docstring, one fine one, and literals that must not move.

    The long text sits in body paragraphs, because the tool keeps the opening line as written --
    a summary line that needs shortening is an editing decision, not a re-wrap, and ruff's own
    gate is what catches one.
    """
    return (
        'def measure():\n    """Measure the sample, and nothing else.\n\n'
        f"    {LONG}\n    {LONG}\n\n    - {'a bullet ' * 12}\n      continuing under itself\n"
        '    """\n\n'
        '    x = "a literal that must survive verbatim: 32.6% spread"\n'
        "    pattern = r'(?<![A-Za-z\\d#.])'\n"
        "    return x, pattern\n\n\n"
        'def fine():\n    """A short docstring the tool has no reason to touch."""\n'
        "    return 1\n"
    )


def test_a_rewrite_that_loses_a_word_is_refused_and_nothing_is_written(tmp_path: Path) -> None:
    """The whole reason the tool exists is this refusal, so it is tested before its success."""
    tool = load_tool()
    path = tmp_path / "sample.py"
    path.write_text(sample_module(), encoding="utf-8")
    original = path.read_text(encoding="utf-8")

    def lossy(source: str, width: int) -> tuple[str, int]:
        """A rewrap that drops a word -- the failure mode the AST proof is against."""
        del width
        return source.replace("the vocabulary is technical", "the vocabulary", 1), 1

    tool.rewrap_source = lossy  # type: ignore[method-assign]
    assert tool.process(path, apply_changes=True) == 1, (
        "the proof accepted a rewrite that deleted words from a docstring"
    )
    assert path.read_text(encoding="utf-8") == original, "a refused rewrite was written anyway"


def test_the_rewrite_moves_line_breaks_and_nothing_else(tmp_path: Path) -> None:
    """The accepted direction: the same file, rewritten, with every other byte intact."""
    tool = load_tool()
    path = tmp_path / "sample.py"
    path.write_text(sample_module(), encoding="utf-8")

    before = path.read_text(encoding="utf-8")
    after, reflowed = tool.rewrap_source(before, tool.line_length())
    assert reflowed == 1, "the over-long docstring was not the one the tool moved"
    assert tool.verify(before, after) == [], tool.verify(before, after)

    width = tool.line_length()
    assert all(len(line) <= width for line in after.split("\n")), [
        (index + 1, len(line)) for index, line in enumerate(after.split("\n")) if len(line) > width
    ]
    words_before = sorted(word for line in before.split("\n") for word in line.split())
    words_after = sorted(word for line in after.split("\n") for word in line.split())
    assert words_before == words_after, "the rewrite changed a token, not only its position"
    for literal in ('"a literal that must survive verbatim: 32.6% spread"', "pattern = r'"):
        assert literal in after, f"the code literal {literal!r} did not survive the rewrap"
    assert tool.signature(after) == tool.signature(before), (
        "the folded parse differs, so something other than docstring line breaks moved"
    )


def test_a_second_run_finds_nothing_left_to_do(tmp_path: Path) -> None:
    """Idempotence, because a formatter that keeps re-wrapping its own output is not finished."""
    tool = load_tool()
    path = tmp_path / "sample.py"
    path.write_text(sample_module(), encoding="utf-8")
    assert tool.process(path, apply_changes=True) == 0
    once = path.read_text(encoding="utf-8")
    assert tool.process(path, apply_changes=True) == 0
    assert path.read_text(encoding="utf-8") == once, "a second run changed the file again"
    assert tool.rewrap_source(once, tool.line_length())[1] == 0, (
        "the run reported success while work remained, so the tally is not the truth"
    )


def test_the_tool_takes_its_width_from_the_configuration_not_from_itself() -> None:
    """One number, one owner: the gate the tool serves is ruff's, and ruff reads `pyproject.toml`.

    `WIDTH = 100` written into a script is a second fact about the same decision, and the copy is
    what goes stale -- the same defect shape this repository keeps meeting in its documents, met
    here in its tooling.
    """
    configured = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"][
        "ruff"
    ]["line-length"]
    tool = load_tool()
    assert tool.line_length() == configured, (
        f"the tool wraps at {tool.line_length()} while ruff enforces {configured}"
    )
    source = TOOL.read_text(encoding="utf-8")
    assert "WIDTH = " not in source, "a literal width is back in the tool next to the reader"


def test_the_tool_is_the_only_copy_and_it_is_tracked() -> None:
    """The debt being closed was a tool that lived in a directory git does not see."""
    listed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "scripts/rewrap_docstrings.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert listed.returncode == 0, (
        f"the promoted tool is not tracked: {listed.stderr.strip()[:120]}"
    )
    assert not (REPO_ROOT / "build" / "rewrap_docstrings.py").exists(), (
        "the ignored scratch copy is still on disk, so the next session can run the stale one"
    )
