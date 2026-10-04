"""The order-five radius map: the artifact's radii must be recomputable, and its refusions provable.

This file owns four things that no other test in the repository reaches:

* the artifact's five books must carry the cubic and quartic radii v1.5.0 and v1.6.0
  published, and the machinery that decided them must be those releases' own -- the
  equality gate is executed here, not described;
* every radius, at all three orders, must come back from the per-column distances printed
  beside it, grouped by magnitude the way the shipped rule groups it, so a headline cannot
  be a transcription of a run that looked at different columns;
* the six book sums the quintic truncation is built on must be recomputable from the core,
  digit for digit, which is what makes "the artifact used the shipped closed forms" a check
  rather than a claim;
* and the run's own refusals must be shown to fire on the shape they name and not on the
  shape they do not. The second half is the point: the first version of `check` judged a
  radius by the worst column inside *another* order's range, and refused the published
  book's cubic radius for a column at 0.15 it never claimed to cover.

`docs/analysis/fifth_order_crossing_map.md` is owned here too, so the note's figures are re-derived
rather than read by nobody.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from test_two_factor_bound import _assert_same_result, _noise_decided_verdicts

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = (
    REPO_ROOT
    / "experiments"
    / "fifth_order_crossing_map"
    / "results"
    / "fifth_order_crossing_map.json"
)
NOTE = REPO_ROOT / "docs" / "analysis" / "fifth_order_crossing_map.md"
PUBLISHED = "published ladder"
ORDERS = ("cubic", "quartic", "quintic")
SUM_FIELDS = (
    "spot_spot_spot_spot_spot",
    "spot_spot_spot_spot_sigma",
    "spot_spot_spot_sigma_sigma",
    "spot_spot_sigma_sigma_sigma",
    "spot_sigma_sigma_sigma_sigma",
    "sigma_sigma_sigma_sigma_sigma",
)


def _load(relative: str, name: str) -> Any:
    path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def experiment() -> Any:
    return _load("experiments/fifth_order_crossing_map/run.py", "fifth_order_experiment")


@pytest.fixture(scope="module")
def payload() -> dict[str, Any]:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _books(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {book["label"]: book for book in payload["books"]}


def _passes(distance: dict[str, Any], order: str, tolerance: float) -> bool:
    value = distance[f"{order}_nearest_zero_distance"]
    return value is not None and value <= tolerance


def _radius_from_rows(
    book: dict[str, Any], distances: list[dict[str, Any]], order: str, tolerance: float
) -> float:
    """The contiguous paired-magnitude radius, recomputed from the printed profile.

    Deliberately not the producer's loop: a magnitude is one candidate and two signed columns, and
    sorting the columns to take them one at a time is the defect this chain already fixed twice.
    """
    columns = list(zip(book["columns"], distances, strict=True))
    widest = 0.0
    for magnitude in sorted({row["abs_delta"] for row, _ in columns}):
        crossing = [
            (row, distance)
            for row, distance in columns
            if row["abs_delta"] == magnitude and row["measured_zero_count"]
        ]
        if not crossing:
            continue
        if not all(_passes(distance, order, tolerance) for _, distance in crossing):
            break
        widest = magnitude
    return widest


def test_the_published_book_still_answers_to_its_own_releases(payload: dict[str, Any]) -> None:
    """The baseline an added order is measured against may not move under it."""
    published = _books(payload)[PUBLISHED]
    control = payload["controls"]["published_radii_reproduced"]
    assert published["radius_cubic"] == control["expected_cubic"] == 0.05
    assert published["radius_quartic"] == control["expected_quartic"] == 0.15
    assert control["cubic"] == published["radius_cubic"]
    assert control["quartic"] == published["radius_quartic"]


def test_the_shipped_equality_gate_actually_holds(experiment: Any) -> None:
    """`verify_control` is the shipped chain's own gate, and this run is not allowed to describe it.

    Re-executed here: the ten third- and fourth-order coefficients, both truncations and the engine
    P&L over 30 joint moves must differ from v1.5.0's and v1.6.0's by exactly zero.
    """
    experiment.P18.verify_control(experiment.BOOKS[0])
    book = experiment.BOOKS[0]
    third, fourth = book.third_order(), book.fourth_order()
    differences = [
        abs(third[name] - value) for name, value in experiment.P18.P15.COEFFS.items()
    ] + [abs(fourth[name] - value) for name, value in experiment.P18.P16.COEFFS4.items()]
    assert differences, "the coefficient tables the gate compares against are empty"
    assert max(differences) == 0.0


def test_the_core_sums_behind_the_quintic_term_are_the_shipped_ones(
    experiment: Any, payload: dict[str, Any]
) -> None:
    """Recomputed from the bindings, not read from the artifact the test is checking."""
    sums = payload["controls"]["fifth_order_book_sums_published_book"]
    market = experiment.BOOKS[0].market()
    partials = experiment.quantrisk.pricing.black_scholes_mixed_fifth_derivatives
    recomputed = {
        field: sum(
            float(getattr(partials(o, market), field)) for o in experiment.BOOKS[0].options()
        )
        * experiment.BOOKS[0].quantity
        for field in SUM_FIELDS
    }
    assert set(sums) == set(SUM_FIELDS), sorted(set(sums) ^ set(SUM_FIELDS))
    for field in SUM_FIELDS:
        # Relative slack, not bit equality. The reproduction comparator's own rule is 1e-12 relative
        # on floats across platforms (docs/limitations.md #63), and the first CI run measured that
        # gap: the published V_SSsigmasigma is -78.60804475268505 on this machine and
        # -78.60804475268517 on the runner, 1.5e-15 of itself, because libm's exp/log differ in the
        # last bits. Exact equality across platforms is not the claim this repository makes; the
        # claim is that the number is the core's own, which a 1e-12 band still pins tightly.
        assert abs(sums[field] - recomputed[field]) <= 1.0e-12 * max(abs(recomputed[field]), 1.0), (
            field,
            sums[field],
            recomputed[field],
        )


def test_every_radius_is_re_computed_from_the_rows_beside_it(payload: dict[str, Any]) -> None:
    """Three orders, five books, fifteen radii, none of them taken on trust from the headline."""
    tolerance = 0.005
    for book in payload["books"]:
        distances = payload["fits"][book["label"]]["columns"]
        for order in ORDERS:
            derived = _radius_from_rows(book, distances, order, tolerance)
            assert derived == book[f"radius_{order}"], (book["label"], order, derived)
        # The producer's verdict flags must agree with the distances they are derived from.
        for row, distance in zip(book["columns"], distances, strict=True):
            for order in ORDERS:
                assert row[f"{order}_within_tolerance"] == _passes(distance, order, tolerance), (
                    book["label"],
                    row["delta"],
                    order,
                )


def _planted_book(failing_sign_index: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """A six-column book whose widest magnitude is a signed pair that disagrees.

    `0.10` passes on both signs, `0.15` passes on one sign and sits at 0.2 on the other. A
    radius rule that reads columns one at a time claims 0.15 from whichever sign came first;
    the shipped rule and the recomputation here must both stop at 0.10.
    """
    magnitudes = (0.05, 0.10, 0.15)
    rows, distances = [], []
    for magnitude in magnitudes:
        for sign in (-1.0, 1.0):
            loose = magnitude == 0.15 and len(rows) == failing_sign_index
            distance = 0.2 if loose else 1.0e-4
            rows.append(
                {
                    "delta": sign * magnitude,
                    "abs_delta": magnitude,
                    "measured_zero_count": 1,
                    "quintic_within_tolerance": distance <= 0.005,
                }
            )
            distances.append({"quintic_nearest_zero_distance": distance})
    return {"columns": rows}, distances


def test_the_signed_pair_counts_as_one_radius_candidate(experiment: Any) -> None:
    """Either failing sign caps the radius, and the cap holds in both column orders.

    Planted in the recomputation and in the producer's own function, so the guard is tested against
    the shape that shipped the bug rather than against a story about it.
    """
    for failing_sign_index in (4, 5):  # the -0.15 column, then its +0.15 partner
        book, distances = _planted_book(failing_sign_index)
        for order_rows, order_distances in (
            (book["columns"], distances),
            (
                list(reversed(book["columns"])),
                list(reversed(distances)),
            ),
        ):
            capped = _radius_from_rows({"columns": order_rows}, order_distances, "quintic", 0.005)
            assert capped == 0.10, (failing_sign_index, capped)
            assert capped < 0.15, "a magnitude whose pair disagrees may not set the radius"
        # The loose rule this replaces would have claimed the failing magnitude.
        naive = max(
            row["abs_delta"]
            for row, distance in zip(book["columns"], distances, strict=True)
            if _passes(distance, "quintic", 0.005)
        )
        assert naive == 0.15, naive
        producer = experiment.contiguous_radius if False else experiment.P18.contiguous_radius
        assert producer([dict(row) for row in book["columns"]], "quintic") == 0.10

    planted_result = {
        "label": "plant",
        "columns_with_a_priced_crossing": 6,
        "columns_swept": 6,
        "radius_cubic": 0.15,
        "radius_quartic": 0.15,
        "radius_quintic": 0.15,
    }
    own = {"cubic": 1.0e-4, "quartic": 1.0e-4, "quintic": 0.2}
    with pytest.raises(RuntimeError, match="contains a crossing column"):
        experiment.check(planted_result, {"worst_distance_inside_own_radius": own})


def test_a_radius_is_judged_only_by_columns_inside_it(experiment: Any) -> None:
    """The refusal's own range, in both directions.

    A loose column outside the cubic radius must not reject it. The first version of `check`
    read the worst distance from the *quartic* range for every order and refused the published
    ladder's cubic radius of 0.05 over a column at 0.15 that radius never claimed.
    """
    result = {"label": "range test", "columns_with_a_priced_crossing": 10, "columns_swept": 12}
    for order, radius in (("cubic", 0.05), ("quartic", 0.15), ("quintic", 0.20)):
        result[f"radius_{order}"] = radius
    inside_cubic = {"cubic": 2.0e-3, "quartic": 1.0e-3, "quintic": 1.0e-3}
    experiment.check(result, {"worst_distance_inside_own_radius": inside_cubic})

    # Same numbers, but the cubic radius now contains a column it failed: the refusal must fire.
    broken = dict(inside_cubic, cubic=6.0e-3)
    with pytest.raises(RuntimeError, match="cubic radius of 0.05"):
        experiment.check(result, {"worst_distance_inside_own_radius": broken})

    thin = dict(result, columns_with_a_priced_crossing=2)
    with pytest.raises(RuntimeError, match="priced crossing"):
        experiment.check(thin, {"worst_distance_inside_own_radius": inside_cubic})


def test_the_contraction_is_re_derived_on_rays_the_run_did_not_choose(experiment: Any) -> None:
    """The multinomial weights, checked on displacements the producer never evaluated.

    Same nested differences of the revalued book, different rays and a different widest rung, so the
    published `rays` list cannot be the reason the control passes.
    """
    book = experiment.BOOKS[0]
    sums = experiment.fifth_order_sums(book)
    for delta, k in ((0.07, -0.03), (-0.18, 0.11), (0.0, 0.05), (0.25, 0.0)):
        closed = 120.0 * experiment.quintic_piece(book, sums, delta, k)
        if abs(closed) < 1.0e-9:
            continue
        error = min(
            abs(experiment.nested_fifth(book, delta, k, scale) - closed) / abs(closed)
            for scale in (0.02, 0.04, 0.06)
        )
        assert error < 5.0e-2, (delta, k, error)


def test_the_headline_counts_are_counted_from_the_rows(payload: dict[str, Any]) -> None:
    """Widened, unchanged, at the grid edge, closer inside: recomputed, not repeated."""
    headline = payload["headline"]
    books = payload["books"]
    assert headline["books_measured"] == len(books) == 5
    assert headline["books_widening_at_order_five"] == sum(
        1 for book in books if book["radius_quintic"] > book["radius_quartic"]
    )
    assert headline["books_unchanged_at_order_five"] == sum(
        1 for book in books if book["radius_quintic"] == book["radius_quartic"]
    )
    assert headline["books_at_grid_edge"] == sum(
        1 for book in books if book["quintic_radius_at_grid_edge"]
    )
    assert headline["books_widening_at_order_five"] + headline[
        "books_unchanged_at_order_five"
    ] <= len(books)
    assert headline["columns_with_a_priced_crossing_total"] == sum(
        book["columns_with_a_priced_crossing"] for book in books
    )
    for book in books:
        assert book["widening_factor_quintic"] == (book["radius_quintic"] / book["radius_quartic"])
    reasons = {book["why_this_book"] for book in books}
    assert len(reasons) == 5, "a transfer claim measured on five copies of one ladder"


def test_the_prose_of_the_artifact_says_what_it_means(payload: dict[str, Any]) -> None:
    """Sentences the run writes about its own procedure, pinned whole.

    Bulk re-wrapping once glued words together inside these strings and the JSON still parsed, so
        the only guard against that is the sentence itself.
    """
    procedure = payload["procedure"]
    assert procedure["radius_definition"].startswith("a |delta| magnitude passes only when")
    assert (
        "the radius is the widest magnitude such that all smaller magnitudes pass"
        in (procedure["radius_definition"])
    )
    assert "Phase 18's five books had already refuted the mechanism" in procedure["not_measured"]
    assert "10 V_SSsigmasigmasigma h^2 k^3" in procedure["quintic_term"]
    assert "imported from experiments/second_book_crossing_map/run.py" in procedure["books"]
    for key, value in list(procedure.items()) + [
        ("why", payload["reproduction_policy"]["why"]),
        ("everything_else", payload["reproduction_policy"]["everything_else"]),
    ]:
        assert "  " not in value, key
        assert " [" not in value and "] " not in value, key
    assert payload["command"] == "uv run python experiments/fifth_order_crossing_map/run.py"


def test_the_declared_families_exist_in_the_payload(payload: dict[str, Any]) -> None:
    """An exemption path that names nothing exempts nothing and announces nothing."""
    paths: list[str] = []

    def walk(node: object, prefix: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{prefix}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{prefix}[{index}]")
        else:
            paths.append(prefix.lstrip("."))

    walk({key: value for key, value in payload.items() if key != "environment"}, "")
    for entry in payload["reproduction_policy"]["conditioning_limited"]:
        assert any(
            path == entry or path.startswith(f"{entry}.") or path.startswith(f"{entry}[")
            for path in paths
        ), f"{entry} names no path in the artifact"


def test_the_note_figures_are_the_artifacts_own(payload: dict[str, Any]) -> None:
    """`docs/analysis/fifth_order_crossing_map.md` restates this artifact, in its own digits."""
    text = NOTE.read_text(encoding="utf-8")
    headline = payload["headline"]
    for label, book in _books(payload).items():
        assert label in text, f"the note never mentions {label}"
        for order in ORDERS:
            assert f"{book[f'radius_{order}']:.2f}" in text, (label, order)
    for figure in (
        f"{headline['published_widening_factor_quartic']:.2f}",
        f"{headline['published_widening_factor_quintic']:.2f}",
        f"{headline['books_widening_at_order_five']} of {headline['books_measured']}",
        f"{headline['columns_with_a_priced_crossing_total']}",
        f"{headline['books_at_grid_edge']}",
    ):
        assert figure in text, f"the note never carries {figure}"
    rays = payload["controls"]["multinomial_contraction_of_the_quintic_piece"]["rays"]
    for ray in rays:
        assert f"{ray['relative_error_widest_rung']:.0e}" in text, ray


def test_rerunning_the_experiment_in_a_temporary_tree_reproduces_the_committed_numbers(
    tmp_path: Path,
) -> None:
    """Determinism, without letting a test write into frozen evidence.

    Five files travel: this experiment and the four it imports transitively. The copy must sit at
        the same depth because each resolves the repository root by walking up.
    """
    tree = {
        "experiments/fifth_order_crossing_map/run.py",
        "experiments/second_book_crossing_map/run.py",
        "experiments/fourth_order_crossing_map/run.py",
        "experiments/restrike_gamma_map/run.py",
        "experiments/stress_testing/run.py",
    }
    for relative in tree:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text((REPO_ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8")

    copy = tmp_path / "experiments" / "fifth_order_crossing_map" / "run.py"
    before = ARTIFACT.read_bytes()
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(copy)], capture_output=True, text=True, check=False, cwd=tmp_path
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    assert ARTIFACT.read_bytes() == before, "the test run modified a committed artifact"

    produced = copy.parent / "results" / "fifth_order_crossing_map.json"
    assert produced.exists(), f"the copy wrote no artifact; stdout: {completed.stdout[-400:]}"
    mine, theirs = (
        json.loads(ARTIFACT.read_text(encoding="utf-8")),
        json.loads(produced.read_text(encoding="utf-8")),
    )
    for key in ("generated_at_utc", "environment"):
        mine.pop(key, None)
        theirs.pop(key, None)
    limited = tuple(theirs["reproduction_policy"]["conditioning_limited"])
    advisory = _noise_decided_verdicts(theirs)
    problems = _assert_same_result(mine, theirs, limited=limited, advisory=advisory)
    assert not problems, "the reproduction differs from the committed artifact:\n" + "\n".join(
        problems[:20]
    )
