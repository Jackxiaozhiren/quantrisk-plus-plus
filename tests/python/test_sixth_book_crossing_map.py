"""The sixth crossing-radius book: the scan is the result, so the scan has to be checkable.

This file owns four things nothing else in the repository reaches:

* the five books carried beside the new one must return the radii
  `experiments/fifth_order_crossing_map` published, digit for digit, which is what makes "one more
  book" a statement about the same quantity rather than a re-run under different machinery;
* every radius -- six books, three orders -- must come back from the per-column verdicts printed
  beside it, grouped by magnitude the way the shipped rule groups it, so a headline cannot be a
  transcription of a run that looked at other columns;
* the selection rule must be auditable rather than asserted: the candidate scan is published in
  ascending ratio order, the accepted candidate is the first whose radius is defined, and the sixth
  book's ratio is a new low of the span the five prior books span;
* and the verdict's own weakness must be stated by the artifact and recomputable here. The book the
  rule chose has its quartic radius already at the grid edge, so its quintic radius cannot rise
  inside the swept grid no matter what the truncation does. A file that reported "unchanged" without
  that flag beside it would be reporting the grid, not the expansion.

`docs/analysis/sixth_book_crossing_map.md` is owned here too, so the note's figures are re-derived
from the artifact rather than read by nobody.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
from typing import Any

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
ARTIFACT = (
    REPO_ROOT
    / "experiments"
    / "sixth_book_crossing_map"
    / "results"
    / "sixth_book_crossing_map.json"
)
PRIOR_ARTIFACT = (
    REPO_ROOT
    / "experiments"
    / "fifth_order_crossing_map"
    / "results"
    / "fifth_order_crossing_map.json"
)
NOTE = REPO_ROOT / "docs" / "analysis" / "sixth_book_crossing_map.md"
ORDERS = ("cubic", "quartic", "quintic")


def _load(relative: str, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def payload() -> dict[str, Any]:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def prior() -> dict[str, Any]:
    return json.loads(PRIOR_ARTIFACT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def experiment() -> Any:
    return _load("experiments/sixth_book_crossing_map/run.py", "sixth_book_experiment_under_test")


def test_the_five_prior_books_return_the_radii_phase_20_published(
    payload: dict[str, Any], prior: dict[str, Any]
) -> None:
    """Adding a book may not move the books it is compared against."""
    mine = {row["label"]: row for row in payload["books"]}
    theirs = {row["label"]: row for row in prior["books"]}
    assert theirs, "the fifth-order artifact carries no books to compare with"
    for label, row in theirs.items():
        assert label in mine, f"{label} is in the fifth-order artifact but not in this one"
        for order in ORDERS:
            key = f"radius_{order}"
            assert mine[label][key] == row[key], (
                f"{label} {key}: this run says {mine[label][key]}, Phase 20 published {row[key]}"
            )
    assert payload["controls"]["published_books_reproduced_bit_for_bit"] == len(theirs)


def test_every_radius_comes_back_from_the_columns_printed_beside_it(
    payload: dict[str, Any], experiment: Any
) -> None:
    """The shipped rule re-executed on the artifact's own rows, book by book and order by order."""
    radius = experiment.P18.contiguous_radius
    for row in payload["books"]:
        for order in ORDERS:
            recomputed = radius(row["columns"], order)
            assert recomputed == row[f"radius_{order}"], (
                f"{row['label']} {order}: the columns printed beside the verdict give "
                f"{recomputed}, the artifact says {row[f'radius_{order}']}"
            )


def test_the_selection_rule_is_the_order_the_scan_prints(
    payload: dict[str, Any], experiment: Any
) -> None:
    """Ascending ratio, first defined radius wins, and the winner is the book that was measured."""
    scan = payload["candidate_scan"]
    assert scan, "no candidate scan was published, so the rule is only asserted prose"
    ratios = [row["order_five_over_four_at_measure_column"] for row in scan]
    assert ratios == sorted(ratios), f"the scan is not in ascending ratio order: {ratios}"
    needed = experiment.P18.MIN_COLUMNS_WITH_A_CROSSING
    accepted = [index for index, row in enumerate(scan) if row["accepted"]]
    assert accepted == [len(scan) - 1], (
        f"the scan accepts at {accepted} of {len(scan)} rows: a candidate after the accepted one "
        "was examined, or the accepted one is not the first whose radius is defined"
    )
    for row in scan:
        enough = row["columns_with_a_priced_crossing"] >= needed
        assert row["accepted"] is enough, (
            f"{row['label']}: accepted flag disagrees with its columns"
        )
        if not enough:
            assert row["rejected_because"], f"{row['label']} was rejected without a reason"
    winner = scan[-1]
    assert payload["headline"]["sixth_book"] == winner["label"]
    assert winner["order_five_over_four_at_measure_column"] == pytest.approx(
        payload["headline"]["sixth_book_ratio"], rel=0.0, abs=1e-12
    )
    published = {row["label"] for row in payload["books"]} - {winner["label"]}
    assert not published & {row["label"] for row in scan}, "a published book was also scanned"

    # A scan that stops at its first acceptance shows nothing about the candidates it never priced,
    # so the ordering above has as many rows as it has evidence. The ranking is the whole grid the
    # rule sorted, and it is re-derived here from the module's own `ratio_of` rather than trusted:
    # that is the only way to check that the winner was first among 23 rather than first of the
    # rows that were shown.
    ranking = payload["candidate_ranking"]
    declared = payload["procedure"]["candidate_grid"]["candidates_after_removing_published_sets"]
    assert len(ranking) == declared, (
        f"the ranking carries {len(ranking)} candidates while the procedure declares {declared}"
    )
    assert [row["rank"] for row in ranking] == list(range(len(ranking)))
    recomputed = sorted(
        (
            (experiment.ratio_of(book), index, book.label)
            for index, book in enumerate(experiment.candidates())
        ),
        key=lambda row: (row[0], row[1]),
    )
    assert [row["label"] for row in ranking] == [label for _, _, label in recomputed], (
        "the published ranking is not the order the rule's own ratio puts the grid in"
    )
    assert [row["order_five_over_four_at_measure_column"] for row in ranking] == pytest.approx(
        [ratio for ratio, _, _ in recomputed], rel=1e-12
    )
    assert [row["label"] for row in scan] == [row["label"] for row in ranking[: len(scan)]], (
        "the scan is not the prefix of the ranking the rule examined"
    )
    assert not any(row["accepted"] for row in scan[:-1]), (
        "a candidate before the winner was accepted, so the rule examined past its stop"
    )
    assert not published & {row["label"] for row in ranking}, (
        "a published book is inside the candidate grid the rule chose from"
    )


def test_the_sixth_book_is_a_new_low_of_the_span_it_was_compared_against(
    payload: dict[str, Any],
) -> None:
    """The span the note quotes is the five prior books' span, read off the artifact's own fits."""
    head = payload["headline"]
    fits = payload["fits"]
    sixth = head["sixth_book"]
    prior_values = sorted(
        value
        for label, block in fits.items()
        if label != sixth
        for value in [block["order_five_over_four_at_measure_column"]]
        if value is not None
    )
    quoted = head["published_ratio_span_of_the_five_prior_books"]
    assert quoted == [prior_values[0], prior_values[-1]], (
        f"the note's span is {quoted} while the five prior books' ratios span "
        f"{[prior_values[0], prior_values[-1]]}"
    )
    ratio = fits[sixth]["order_five_over_four_at_measure_column"]
    assert head["sixth_book_is_new_low_of_the_published_span"] is (ratio < prior_values[0])
    assert head["sixth_book_ratio_over_the_published_minimum"] == pytest.approx(
        ratio / prior_values[0], rel=1e-12
    )


def test_a_verdict_bounded_by_the_grid_says_so(payload: dict[str, Any], experiment: Any) -> None:
    """The sixth book's `unchanged` is about the swept grid, and the artifact admits it."""
    head = payload["headline"]
    row = next(item for item in payload["books"] if item["label"] == head["sixth_book"])
    edge = experiment.P18.GRID_EDGE
    assert row["quintic_radius_at_grid_edge"] is (row["radius_quintic"] == edge)
    bounded = row["quintic_radius_at_grid_edge"] and row["radius_quartic"] == edge
    assert head["sixth_book_radius_verdict_is_grid_bounded"] is bounded, (
        f"quartic {row['radius_quartic']} and quintic {row['radius_quartic']} against an edge of "
        f"{edge}: the flag must say whether a widening was even expressible on this grid"
    )


def test_the_headline_counts_are_counted_from_the_rows(payload: dict[str, Any]) -> None:
    """Widened, unchanged, thinned and at-edge are counts of the books, not transcriptions."""
    head = payload["headline"]
    rows = [
        row
        for row in payload["books"]
        if row["widening_factor_quintic"] is not None and row["radius_quartic"] > 0.0
    ]
    widened = sum(1 for row in rows if row["radius_quintic"] > row["radius_quartic"])
    unchanged = sum(1 for row in rows if row["radius_quintic"] == row["radius_quartic"])
    thinned = sum(1 for row in rows if row["radius_quintic"] < row["radius_quartic"])
    assert head["books_measured"] == len(payload["books"])
    assert (head["books_widening_at_order_five"], head["books_unchanged_at_order_five"]) == (
        widened,
        unchanged,
    )
    assert head["books_thinning_at_order_five"] == thinned
    assert head["books_at_grid_edge"] == sum(
        1 for row in payload["books"] if row["quintic_radius_at_grid_edge"]
    )
    assert widened + unchanged + thinned == len(rows), (
        f"{widened}+{unchanged}+{thinned} does not account for the {len(rows)} books whose "
        "quintic radius is comparable to the quartic's"
    )


def test_the_declared_conditioning_families_exist_in_the_payload(payload: dict[str, Any]) -> None:
    """A reproduction exemption that names nothing is an exemption from nothing."""
    families = payload["reproduction_policy"]["conditioning_limited"]
    assert families, "no conditioning-limited family is declared, so every float is gated by value"

    def resolve(path: str) -> bool:
        node: Any = payload
        for step in path.split("."):
            if not isinstance(node, dict) or step not in node:
                return False
            node = node[step]
        return True

    missing = [path for path in families if not resolve(path)]
    assert not missing, f"declared families absent from the payload: {missing}"


def test_the_note_figures_are_the_artifacts_own(payload: dict[str, Any]) -> None:
    """Every book row, ratio, widening factor and distance in the note comes from the artifact.

    The note's §2 table is the thing a reader quotes onward, so it is parsed row by row rather than
    spot-checked: a label that is in the artifact must be in the table, and its three radii, its
    widening factor and its grid-edge flag must equal the run's.
    """
    text = NOTE.read_text(encoding="utf-8")
    head = payload["headline"]
    rows = {row["label"]: row for row in payload["books"]}
    table = [
        line
        for line in text.splitlines()
        if line.startswith("| ") and " → " in line and not line.startswith("|---")
    ]
    assert table, "the note carries no radii table, so nothing here can be compared"
    matched = 0
    for line in table:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        label = cells[0]
        if label not in rows:
            continue
        matched += 1
        book = rows[label]
        quoted = [float(value) for value in cells[1].split("→")]
        assert quoted == [
            book["radius_cubic"],
            book["radius_quartic"],
            book["radius_quintic"],
        ], (
            f"{label}: the note prints {quoted}, the artifact has "
            f"{[book[f'radius_{o}'] for o in ORDERS]}"
        )
        # The note rounds: three decimals on the widening factor, four on the ratio. The comparison
        # is against that rounding rather than a tolerance, so a prose edit that changes the fourth
        # decimal is a failure while a re-rounding of the same artifact value is not.
        factor = float(cells[2])
        assert factor == round(book["widening_factor_quintic"], 3), (
            f"{label}: the note says the quintic widened by {factor}, the artifact rounds "
            f"{book['widening_factor_quintic']} to {round(book['widening_factor_quintic'], 3)}"
        )
        assert ("yes" in cells[3].lower()) is book["quintic_radius_at_grid_edge"], (
            f"{label}: the note's grid-edge cell is {cells[3]!r} while the artifact says "
            f"{book['quintic_radius_at_grid_edge']}"
        )
        ratio = float(cells[4])
        exact = payload["fits"][label]["order_five_over_four_at_measure_column"]
        assert ratio == round(exact, 4), (
            f"{label}: the note quotes a ratio of {ratio}, the artifact rounds to {round(exact, 4)}"
        )
    assert matched == len(rows) == head["books_measured"], (
        f"the note carries {matched} of the {len(rows)} measured books"
    )
    words = {2: "Two", 3: "three", 4: "four", 0: "none"}
    for sentence, expected in (
        ("Two of six widen at order five", head["books_widening_at_order_five"]),
        ("four are unchanged", head["books_unchanged_at_order_five"]),
        ("none thin", head["books_thinning_at_order_five"]),
        ("three sit at the grid edge", head["books_at_grid_edge"]),
    ):
        assert sentence in text, f"the note no longer states {sentence!r}"
        assert words[expected] == sentence.split()[0], (
            f"the note says {sentence!r} while the artifact counts {expected}"
        )
    sixth = rows[head["sixth_book"]]
    own = payload["fits"][head["sixth_book"]]["worst_distance_inside_own_radius"]
    inside = payload["fits"][head["sixth_book"]]["worst_distance_inside_quartic_radius"]
    for order in ORDERS:
        for value in (own[order], inside[order]):
            if value is None:
                continue
            assert f"{value:.6f}" in text, (
                f"the note never states the sixth book's {order} distance {value:.6f}"
            )
    assert "grid edge" in text.lower(), (
        "the sixth book's verdict is bounded by the swept grid; a note that omits that reads as a "
        "measurement of the expansion rather than of the grid"
    )
    assert f"{sixth['columns_with_a_priced_crossing']} of " in text, (
        "the note never states how many of the accepted book's columns carried a priced crossing"
    )
