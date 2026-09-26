"""Python/C++ consistency (PROJECT_SPEC.md Phase 1 'Testing').

The compiled C++ reference tool prints the core's own results for a fixed seed
and grid. Every value returned through pybind11 must equal the C++ value
*exactly* — not approximately — otherwise the binding layer is transforming
data (a copy, a cast, a re-derivation) and the "one implementation" rule of
docs/architecture.md §2 is already broken.
"""

from __future__ import annotations

import pytest
import quantrisk


def test_version_matches_the_compiled_core(cpp_reference: dict) -> None:
    assert quantrisk.version() == cpp_reference["version"]


def test_normal_stream_is_transport_by_binding_bit_for_bit(cpp_reference: dict) -> None:
    assert quantrisk.Rng(42).standard_normal_vector(len(cpp_reference["normals"])) == pytest.approx(
        cpp_reference["normals"], rel=0.0, abs=0.0
    )


def test_uniform_stream_matches_the_cpp_side_exactly(cpp_reference: dict) -> None:
    assert quantrisk.Rng(42).standard_normal_vector(0) == []
    rng = quantrisk.Rng(42)
    assert [rng.uniform01() for _ in cpp_reference["uniform01"]] == pytest.approx(
        cpp_reference["uniform01"], rel=0.0, abs=0.0
    )


def test_index_stream_matches_the_cpp_side_exactly(cpp_reference: dict) -> None:
    rng = quantrisk.Rng(42)
    ours = [float(rng.uniform_index(97)) for _ in cpp_reference["uniform_index_97"]]
    assert ours == pytest.approx(cpp_reference["uniform_index_97"], rel=0.0, abs=0.0)


def test_distribution_functions_match_the_cpp_side_exactly(cpp_reference: dict) -> None:
    xs = cpp_reference["xs"]
    assert [quantrisk.normal_cdf(x) for x in xs] == pytest.approx(
        cpp_reference["normal_cdf"], rel=0.0, abs=0.0
    )
    assert [quantrisk.normal_pdf(x) for x in xs] == pytest.approx(
        cpp_reference["normal_pdf"], rel=0.0, abs=0.0
    )
    probabilities = cpp_reference["probabilities"]
    assert [quantrisk.inverse_normal_cdf(p) for p in probabilities] == pytest.approx(
        cpp_reference["inverse_normal_cdf"], rel=0.0, abs=0.0
    )


def test_statistics_helpers_match_the_cpp_side_exactly(cpp_reference: dict) -> None:
    sample = cpp_reference["sample"]
    assert quantrisk.stats.mean(sample) == cpp_reference["sample_mean"]
    assert quantrisk.stats.sample_variance(sample) == cpp_reference["sample_variance"]
    assert quantrisk.stats.quantile(sample, 0.0) == cpp_reference["sample_quantiles"][0]
    for expected, probability in zip(
        cpp_reference["sample_quantiles"],
        [0.0, 0.1, 0.25, 0.5, 0.6, 0.75, 0.9, 1.0],
        strict=True,
    ):
        assert quantrisk.stats.quantile(sample, probability) == expected


def test_statistics_module_is_not_a_python_reimplementation() -> None:
    # The submodule lives inside the compiled extension; if a pure-Python copy
    # ever appeared in python/quantrisk this import path would change.
    assert quantrisk.stats.__name__.startswith("quantrisk._quantrisk")
    origin = getattr(quantrisk.stats, "__file__", "") or ""
    assert not origin.endswith(".py"), f"stats resolved to a Python file: {origin}"
