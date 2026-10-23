"""The generated stubs must match the live modules, or they are just confident lies.

`python/quantrisk/<submodule>.pyi` exists so that static tools can see names the shims
populate at import time. A stub nobody regenerates is worse than no stub: it reports a
surface that has silently moved. This compares each committed file against freshly generated
text, which makes "added a binding, forgot the stub" a CI failure.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _generator():
    """The generator as the package module it is, imported rather than loaded by path."""
    return importlib.import_module("tools.generate_shim_stubs")


def test_every_shim_has_a_committed_stub() -> None:
    generator = _generator()
    for name in generator.SHIM_MODULES:
        assert (REPO_ROOT / "python" / "quantrisk" / f"{name}.pyi").exists(), (
            f"quantrisk/{name}.pyi is missing; run uv run python -m tools.generate_shim_stubs"
        )


@pytest.mark.parametrize("module_name", tuple(_generator().SHIM_MODULES))
def test_stub_matches_the_live_module(module_name: str) -> None:
    generator = _generator()
    committed = (REPO_ROOT / "python" / "quantrisk" / f"{module_name}.pyi").read_text(
        encoding="utf-8"
    )
    assert committed == generator.stub_text(module_name), (
        f"quantrisk/{module_name}.pyi is stale; regenerate with "
        f"uv run python -m tools.generate_shim_stubs"
    )


def test_stub_declares_no_signature_we_could_not_verify() -> None:
    """Every declaration must be a bare `Any`.

    The point of the stub is to report existence, not shape. A `def` or a typed `->` in here
    would be a claim about the C++ that nothing checks, and the whole reason the stubs are
    generated rather than written is to avoid exactly that.
    """
    generator = _generator()
    for module_name in generator.SHIM_MODULES:
        text = (REPO_ROOT / "python" / "quantrisk" / f"{module_name}.pyi").read_text(
            encoding="utf-8"
        )
        bodies = [line for line in text.splitlines() if not line.startswith("#")]
        declarations = [line for line in bodies if line and not line.startswith("from ")]
        assert declarations, f"{module_name}.pyi declares nothing"
        for line in declarations:
            assert line.endswith(": Any"), f"{module_name}.pyi: {line!r} is not a bare Any"


def test_declared_names_are_importable_from_the_shim() -> None:
    """A stub naming something the module cannot resolve would pass the diff and still lie."""
    generator = _generator()
    for module_name in generator.SHIM_MODULES:
        module = importlib.import_module(f"quantrisk.{module_name}")
        text = (REPO_ROOT / "python" / "quantrisk" / f"{module_name}.pyi").read_text(
            encoding="utf-8"
        )
        declared = [line.split(":")[0] for line in text.splitlines() if line.endswith(": Any")]
        assert declared
        for name in declared:
            assert hasattr(module, name), f"quantrisk.{module_name}.{name} is stubbed but absent"
