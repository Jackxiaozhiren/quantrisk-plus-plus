"""The five-book radius map: the artifact's numbers must be the ones the code re-derives.

Four of the claims in `experiments/second_book_crossing_map/` are arithmetic the repository already
knows how to check, and the fifth is the one that needs a new instrument:

* the published book must come back at v1.5.0's and v1.6.0's radii, and its re-derived machinery
  must differ from the shipped one by exactly zero -- asserted from the artifact's own `control`;
* every radius must be re-computable from the per-column profile that sits beside it, so a headline
  cannot be a transcription of a run that produced different columns;
* the set must actually be five books, because a claim about transferability that was measured on
  five copies of one ladder would pass every test above;
* and the sentence that reports how many books widen must be re-counted from the rows, not from the
  prose that counted it last time.

The instrument for the last one is deliberately dull: recount, compare, and refuse a claim string
whose count moved. This is also the file that owns `docs/analysis/second_book_crossing_map.md`, so
the note's figures are re-derived here rather than read by nobody.
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
SCRIPT = REPO_ROOT / "experiments" / "second_book_crossing_map" / "run.py"
ARTIFACT = (
    REPO_ROOT
    / "experiments"
    / "second_book_crossing_map"
    / "results"
    / "second_book_crossing_map.json"
)
NOTE = REPO_ROOT / "docs" / "analysis" / "second_book_crossing_map.md"
PUBLISHED = "published ladder"


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
    return _load("experiments/second_book_crossing_map/run.py", "second_book_experiment")


@pytest.fixture(scope="module")
def payload() -> dict[str, Any]:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _books(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {book["label"]: book for book in payload["books"]}


def _passes(row: dict[str, Any], distance: dict[str, Any], order: str, tolerance: float) -> bool:
    """Whether a column passes, recomputed from the distance beside it.

    The artifact stores a `*_within_tolerance` verdict per column and a nearest-zero distance in a
    parallel list. Re-deriving the verdict from the distance is what keeps the radius below a claim
    about the numbers rather than about the producer's own yes/no.
    """
    value = distance[f"{order}_nearest_zero_distance"]
    return value is not None and value <= tolerance


def _radius_from_rows(
    book: dict[str, Any], distances: list[dict[str, Any]], order: str, tolerance: float
) -> float:
    """The contiguous radius, recomputed from the profile the artifact publishes.

    Grouped by magnitude rather than walked column by column, and deliberately not a copy of the
    producer's loop: `delta = -0.15` and `+0.15` are one candidate and two rows, so a candidate is
    proved only when every row that shares its magnitude and has a priced crossing passes. Sorting
    the columns and taking them one at a time lets whichever sign came first set the radius, which
    is what the first version of this experiment did on the long-dated book.
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
        if not all(_passes(row, distance, order, tolerance) for row, distance in crossing):
            break
        widest = magnitude
    return widest


def test_the_re_derived_machinery_is_the_shipped_one(payload: dict[str, Any]) -> None:
    """Zero is the only acceptable answer, and the run already refuses anything else.

    The four differences are the published book's coefficients, its engine P&L over 30 joint moves,
    and both truncations. They are published rather than only gated so that a reader of the artifact
    can see the control was run on this file's book, and a test can refuse a nonzero without
    re-implementing the comparison.
    """
    control = payload["control"]
    exact = {
        "book_coefficients_largest_absolute_difference": None,
        "engine_pnl_largest_absolute_difference": None,
        "cubic_truncation_largest_absolute_difference": None,
        "quartic_truncation_largest_absolute_difference": None,
    }
    for name in exact:
        assert control[name] == 0.0, f"{name} is {control[name]!r}, not the zero the gate demands"
    assert control["control_moves_compared"] == 30, control["control_moves_compared"]


def test_the_published_book_still_answers_to_its_own_releases(
    payload: dict[str, Any], experiment: Any
) -> None:
    """The ladder v1.5.0 and v1.6.0 measured has to come back at their numbers.

    `PUBLISHED` here is not a re-typed constant: the limits are read from the two shipped
    experiments, so a radius that drifted in either of them fails this test rather than agreeing
    with a stale copy in a third file.
    """
    published = _books(payload)[PUBLISHED]
    assert published["radius_cubic"] == experiment.P15.SMALL_MOVE_LIMIT
    assert published["radius_quartic"] == experiment.P16.WIDENED_LIMIT
    headline = payload["headline"]
    assert headline["published_control_cubic"] == published["radius_cubic"]
    assert headline["published_control_quartic"] == published["radius_quartic"]


def test_every_radius_is_re_computed_from_the_rows_beside_it(payload: dict[str, Any]) -> None:
    """Claim 2 is twelve columns per book; the headline is what they add up to.

    Both radii are recomputed from `books[].columns` and the distances in `fits[].columns` -- the
    same contiguous rule, the same tolerance the artifact states -- and compared to what the block
    and the headline claim. Every stored verdict is first re-derived from its own distance, so a
    radius is built from the artifact's numbers rather than from a yes/no the producer wrote. A
    profile that was edited after the radius, or a radius carried over from an earlier sweep, is
    caught here.
    """
    tolerance = payload["procedure"]["tolerance"]
    headline = payload["headline"]
    for label, book in _books(payload).items():
        distances = payload["fits"][label]["columns"]
        assert len(distances) == len(book["columns"]), label
        for row, distance in zip(book["columns"], distances, strict=True):
            for order in ("cubic", "quartic"):
                stored = row[f"{order}_within_tolerance"]
                assert stored == _passes(row, distance, order, tolerance), (
                    label,
                    row["delta"],
                    order,
                )
        cubic = _radius_from_rows(book, distances, "cubic", tolerance)
        quartic = _radius_from_rows(book, distances, "quartic", tolerance)
        assert cubic == book["radius_cubic"], (label, cubic, book["radius_cubic"])
        assert quartic == book["radius_quartic"], (label, quartic, book["radius_quartic"])
        assert cubic == headline["radii_cubic"][label], label
        assert quartic == headline["radii_quartic"][label], label
        expected = quartic / cubic if cubic > 0.0 else None
        assert book["widening_factor"] == expected, label
        assert book["radius_quartic_at_grid_edge"] == (quartic == headline["grid_edge"]), label


def test_the_signed_pair_counts_as_one_radius_candidate(payload: dict[str, Any]) -> None:
    """The plant the producer's docstring promises: one sign passing is not a magnitude passing.

    Rows are built by hand rather than read from the artifact, because the shape to test is the one
    the real data produced: on the long-dated book `-0.15` passed at 0.00022 while its `+0.15`
    partner sat at 0.02347, nearly five times outside the tolerance, both columns priced and both
    with a crossing. The re-derivation must refuse 0.15 in *both* row orders: the column-by-column
    walk agreed with itself only when the failing sign happened to come first, so the order of the
    columns is the variable that shows the guard has teeth.
    """
    tolerance = payload["procedure"]["tolerance"]

    def column(delta: float, distance: float) -> tuple[dict[str, Any], dict[str, Any]]:
        passes = distance <= tolerance
        verdict = {
            "delta": delta,
            "abs_delta": abs(delta),
            "measured_zero_count": 2,
            "cubic_zero_count": 2,
            "quartic_zero_count": 2,
            "cubic_within_tolerance": passes,
            "quartic_within_tolerance": passes,
        }
        return verdict, {
            "cubic_nearest_zero_distance": distance,
            "quartic_nearest_zero_distance": distance,
        }

    def radius(
        columns: list[tuple[dict[str, Any], dict[str, Any]]],
    ) -> float:
        return _radius_from_rows(
            {"columns": [verdict for verdict, _ in columns]},
            [distance for _, distance in columns],
            "cubic",
            tolerance,
        )

    near = [column(-0.05, 1.0e-4), column(0.05, 2.0e-4)]
    failing_pair = near + [column(-0.15, 0.00022), column(0.15, 0.02347)]
    assert radius(failing_pair) == 0.05
    assert radius(list(reversed(failing_pair))) == 0.05
    passing_pair = near + [column(-0.15, 0.00022), column(0.15, 0.00024)]
    assert radius(passing_pair) == 0.15, "the rule must not simply refuse"


def test_the_widening_is_counted_from_the_rows_not_from_the_sentence(
    payload: dict[str, Any],
) -> None:
    """The claim string carries a count, so the count is re-derived and the sentence checked.

    A headline that says "5 of 5" after a sixth book was added -- or after one of the five stopped
    widening -- would otherwise keep shipping a sentence the data no longer supports.
    """
    books = list(_books(payload).values())
    widened = sum(1 for book in books if book["radius_quartic"] >= book["radius_cubic"])
    tolerance = payload["procedure"]["tolerance"]
    closer = 0
    for book in books:
        radius = book["radius_cubic"]
        worst = {"cubic": None, "quartic": None}
        for row, distance in zip(
            book["columns"], payload["fits"][book["label"]]["columns"], strict=True
        ):
            if not row["measured_zero_count"] or row["abs_delta"] > radius:
                continue
            for order in ("cubic", "quartic"):
                value = distance[f"{order}_nearest_zero_distance"]
                if value is not None:
                    worst[order] = value if worst[order] is None else max(worst[order], value)
        if worst["cubic"] is not None and worst["quartic"] is not None:
            closer += int(worst["quartic"] <= worst["cubic"])
    headline = payload["headline"]
    assert len(books) == headline["books_measured"]
    assert widened == headline["books_where_the_quartic_radius_is_at_least_the_cubic"]
    assert closer == headline["books_where_the_quartic_is_closer_inside_the_cubic_radius"]
    assert f"on {widened} of {len(books)} books" in payload["claim"], payload["claim"]
    assert tolerance == 0.005


def test_five_books_are_five_books_and_not_five_copies(payload: dict[str, Any]) -> None:
    """The anti-vacuity check on the *design*: transferability needs books that differ.

    A claim that a result transfers, measured on five identical ladders, would satisfy every other
    test in this file. So the set is required to differ where the claim says it might matter --
    market parameters, the order-four-to-three ratio and the cubic's own radius -- and to keep at
    least one book that is not the published one.
    """
    books = _books(payload)
    assert len(books) == 5
    markets = {json.dumps(book["market"], sort_keys=True) for book in books.values()}
    assert len(markets) == 5, "two books in the set are the same book"
    radii = {book["radius_cubic"] for book in books.values()}
    assert len(radii) >= 3, f"every book starts at the same radius: {radii}"
    ratios = [payload["fits"][label]["order_four_over_three_at_measure_column"] for label in books]
    assert max(ratios) / min(ratios) > 50.0, (min(ratios), max(ratios))
    assert any(label != PUBLISHED for label in books)


def test_the_note_figures_are_the_artifacts_own(payload: dict[str, Any]) -> None:
    """`docs/analysis/second_book_crossing_map.md` restates this artifact.

    Every figure in the note is re-derived here: the coverage ratchet needs a reader for the note,
    and the reader also catches the failure mode this repository has been bitten by -- a number
    copied into prose and left behind by the next run.
    """
    text = NOTE.read_text(encoding="utf-8")
    headline = payload["headline"]
    books = _books(payload)
    for label, book in books.items():
        assert label in text, f"the note never mentions {label}"
        assert f"{book['radius_cubic']:.2f}" in text, (label, "cubic radius")
        assert f"{book['radius_quartic']:.2f}" in text, (label, "quartic radius")
    low, high = headline["fits"]["order_four_over_three_range"]
    for figure in (
        f"{headline['widening_factor_published_book']:.1f}",
        f"{headline['columns_with_a_priced_crossing_minimum']}",
        f"{high / low:.0f}",
    ):
        assert figure in text, f"the note does not carry {figure}"
    for label in _books(payload):
        for key, value in payload["fits"][label]["worst_distance_inside_cubic_radius"].items():
            assert f"{value:.3g}" in text, (label, key, value)
    short = payload["fits"]["short-dated tight"]
    assert f"{short['v_sigma_root_T']:.3f}" in text, short["v_sigma_root_T"]
    assert f"{short['order_four_over_three_at_measure_column']:.3f}" in text
    long_book = payload["fits"]["long-dated wide"]
    assert f"{long_book['order_four_over_three_at_measure_column']:.3f}" in text
    assert "16.2 %" in text, "the note dropped the amount it is not about"


def test_the_refusals_name_the_limits_the_run_ships(payload: dict[str, Any]) -> None:
    """The scope statements have to stay attached to facts the artifact still shows."""
    refusals = payload["refusals"]
    assert set(refusals) >= {
        "five_books_are_not_a_family",
        "radius_is_not_accuracy",
        "grid_point_not_crossing",
        "no_gate_on_the_finding",
        "zeros_are_sign_changes",
    }
    headline = payload["headline"]
    edge = headline["books_with_a_radius_at_the_grid_edge"]
    assert edge, "the refusal about the swept edge needs a book that is sitting on it"
    for label in edge:
        assert _books(payload)[label]["radius_quartic_at_grid_edge"], label
    published = _books(payload)[PUBLISHED]
    assert published["radius_cubic"] < headline["grid_edge"], "the control book is at the edge too"


def test_the_declared_families_exist_in_the_payload(payload: dict[str, Any]) -> None:
    """A family that names nothing is a silent hole in the reproduction gate.

    Phase 16 learned that exemptions belong to families rather than field names; the same lesson in
    the other direction is that a family string which no path starts with exempts nothing and
    announces nothing. Both declared lists are checked against the paths the payload really has.
    """
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

    walk({key: value for key, value in payload.items() if key not in ("environment",)}, "")
    policy = payload["reproduction_policy"]
    for entry in policy["conditioning_limited"]:
        assert any(
            path == entry or path.startswith(f"{entry}.") or path.startswith(f"{entry}[")
            for path in paths
        ), f"{entry} names no path in the artifact"
    assert policy.get("noise_decided_verdicts", []) == [], "verdicts are all gated here by design"


def test_rerunning_the_experiment_in_a_temporary_tree_reproduces_the_committed_numbers(
    tmp_path: Path,
) -> None:
    """Determinism, without letting the test write into frozen evidence.

    Four files travel: this experiment and the two shipped experiments it imports, plus the stress
    experiment that owns the published scenario those two read. The copy has to sit at the same
    depth, because each of them resolves the repository root by walking up.
    """
    tree = {
        "experiments/second_book_crossing_map/run.py",
        "experiments/fourth_order_crossing_map/run.py",
        "experiments/restrike_gamma_map/run.py",
        "experiments/stress_testing/run.py",
    }
    for relative in tree:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text((REPO_ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8")

    copy = tmp_path / "experiments" / "second_book_crossing_map" / "run.py"
    before = ARTIFACT.read_bytes()
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(copy)], capture_output=True, text=True, check=False, cwd=tmp_path
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    assert ARTIFACT.read_bytes() == before, "the test run modified a committed artifact"

    produced = copy.parent / "results" / "second_book_crossing_map.json"
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
