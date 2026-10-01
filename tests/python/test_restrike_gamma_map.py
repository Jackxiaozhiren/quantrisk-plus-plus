"""Phase 15: what re-striking gamma buys the map, checked without the experiment's own code.

The producer assembles exposures from the closed-form greeks, prices the book, walks the shipped
stress engine and bisects for zeros. Any of those steps can be wrong in a way its own artifact
cannot show -- a variant that is not what its name says, a root the bracketing walked past, a
documented cell count that disagrees with the table beside it. So this rebuilds the map PnLs from
`quantrisk.stress.run_scenario` and the pricer directly, re-finds the zeros independently and
re-derives every figure the producer's docstring quotes from the committed artifact.

The reproduction comparator is imported from `test_two_factor_bound.py` rather than rewritten. Six
CI runs taught that check what counts as reproducible (regressions and cancellation residues have
shape but no cross-platform value), and a second copy of that lesson is how it gets unlearned.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import quantrisk
from quantrisk import stress as STRESS
from test_two_factor_bound import _assert_same_result

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = REPO_ROOT / "experiments" / "restrike_gamma_map"
ARTIFACT = EXPERIMENT / "results" / "restrike_gamma_map.json"
GRID_CSV = EXPERIMENT / "results" / "restrike_gamma_map.csv"
PUBLISHED_CSV = EXPERIMENT / "results" / "published_scenario_maps.csv"
CANCELLATION_CSV = EXPERIMENT / "results" / "cancellation_columns.csv"

SPOT = 100.0
RATE = 0.03
DIVIDEND_YIELD = 0.0
VOLATILITY = 0.20
MATURITY = 0.5
STRIKES = (90.0, 100.0, 110.0)
QUANTITY = 5000.0
MAP_KEYS = ("base", "gamma_restrike", "gamma_restrike_at_move", "all_restrike")

# The producer's own gates, read from the module rather than restated, so a test that keeps its own
# copy of a tolerance is free to disagree with the run it is checking.
_spec = importlib.util.spec_from_file_location("restrike_gamma_map_run", EXPERIMENT / "run.py")
assert _spec and _spec.loader
harness = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = harness
_spec.loader.exec_module(harness)


def _payload() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _grid_rows() -> list[dict[str, str]]:
    with GRID_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _market(spot: float, sigma: float) -> quantrisk.pricing.MarketParams:
    return quantrisk.pricing.MarketParams(
        spot=spot,
        rate=RATE,
        dividend_yield=DIVIDEND_YIELD,
        volatility=sigma,
        maturity=MATURITY,
    )


def _option(strike: float) -> quantrisk.pricing.EuropeanOption:
    return quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, strike)


def _value(spot: float, sigma: float) -> float:
    return (
        sum(
            quantrisk.pricing.black_scholes(_option(strike), _market(spot, sigma)).price
            for strike in STRIKES
        )
        * QUANTITY
    )


def _gamma_exposure(spot: float, sigma: float) -> float:
    return (
        sum(
            0.5
            * quantrisk.pricing.black_scholes_greeks(_option(strike), _market(spot, sigma)).gamma
            * spot
            * spot
            for strike in STRIKES
        )
        * QUANTITY
    )


def _delta_exposure(spot: float, sigma: float) -> float:
    return (
        sum(
            quantrisk.pricing.black_scholes_greeks(_option(strike), _market(spot, sigma)).delta
            * spot
            for strike in STRIKES
        )
        * QUANTITY
    )


def _vega_exposure(spot: float, sigma: float) -> float:
    return (
        sum(
            quantrisk.pricing.black_scholes_greeks(_option(strike), _market(spot, sigma)).vega
            for strike in STRIKES
        )
        * QUANTITY
    )


def _exposure_points(delta: float, vol_move: float, variant: str) -> dict[str, tuple[float, float]]:
    """Which market each of the three exposures is read at, per published variant.

    Written per exposure rather than per variant on purpose: the variants differ by one leg each,
    and a helper that moves all three together turns `gamma_restrike` into a fifth map nobody
    published.
    That conflation is what the first draft of this test did, and what the two assertions below
    refused to agree with -- which is the reason for rebuilding the variants here at all.
    """
    h = SPOT * delta
    k = vol_move
    at_base = (SPOT, VOLATILITY)
    if variant == "base":
        return {"delta": at_base, "gamma": at_base, "vega": at_base}
    if variant == "gamma_restrike":
        return {"delta": at_base, "gamma": (SPOT, VOLATILITY + k), "vega": at_base}
    if variant == "gamma_restrike_at_move":
        return {"delta": at_base, "gamma": (SPOT + h, VOLATILITY + k), "vega": at_base}
    if variant == "all_restrike":
        moved = (SPOT + h, VOLATILITY + k)
        return {"delta": moved, "gamma": moved, "vega": moved}
    raise AssertionError(f"unknown variant {variant!r}")


def _engine_pnl(delta: float, vol_move: float, points: dict[str, tuple[float, float]]) -> float:
    """One map evaluation through the shipped stress engine, with the exposures read as told."""
    factors = STRESS.FactorSet()
    factors.factors = [
        STRESS.RiskFactor("EQ0", STRESS.FactorClass.equity_index, SPOT, "index points"),
        STRESS.RiskFactor("VOL", STRESS.FactorClass.volatility, VOLATILITY, "annualised vol"),
    ]
    vector = STRESS.ExposureVector()
    vector.delta = [_delta_exposure(*points["delta"]), 0.0]
    vector.gamma = [_gamma_exposure(*points["gamma"]), 0.0]
    vector.duration = [0.0, 0.0]
    vector.vega = [0.0, _vega_exposure(*points["vega"])]
    vector.credit = [0.0, 0.0]
    position = STRESS.Position()
    position.name = "option_book"
    position.exposures = vector
    portfolio = STRESS.Portfolio()
    portfolio.factors = factors
    portfolio.positions = [position]
    handle = STRESS.Scenario()
    handle.name = "restrike_check"
    handle.kind = STRESS.ScenarioKind.deterministic
    handle.assumptions = "equity relative move and volatility absolute move"
    handle.shocks = [STRESS.Shock("EQ0", delta, 0.0), STRESS.Shock("VOL", 0.0, vol_move)]
    return float(STRESS.run_scenario(portfolio, handle).pnl_change)


def _priced_error(delta: float, vol_move: float) -> dict[str, float]:
    """The error of each map, rebuilt from the engine and the pricer."""
    exact = _value(SPOT + SPOT * delta, VOLATILITY + vol_move) - _value(SPOT, VOLATILITY)
    return {
        key: exact - _engine_pnl(delta, vol_move, _exposure_points(delta, vol_move, key))
        for key in MAP_KEYS
    }


def test_the_shipped_map_error_is_the_number_the_phase_13_artifact_published() -> None:
    """Two experiments, one book: the base map's `risk_off` error must be the same number."""
    mine = _payload()["headline"]
    phase_13_dir = REPO_ROOT / "experiments" / "two_factor_error_bound" / "results"
    theirs = json.loads((phase_13_dir / "two_factor_bound.json").read_text(encoding="utf-8"))[
        "headline"
    ]
    published_row = next(
        iter(csv.DictReader((phase_13_dir / "published_scenario_bound.csv").open()))
    )
    assert mine["published_error_base"] == theirs["published_error"], (
        f"{mine['published_error_base']!r} vs {theirs['published_error']!r}"
    )
    assert mine["joint_shocks_swept"] == theirs["joint_shocks_swept"]
    # The cubic v1.3.0 named, re-derived here from the book's own mixed third partial, is the
    # term the re-strike is priced against. Disagreement makes claim 2 about nothing.
    assert mine["published_local_cubic_gamma_sigma"] == float(
        published_row["term_cubic_gamma_sigma"]
    )


def test_the_engine_columns_are_what_the_shipped_engine_returns_now() -> None:
    """The committed table is re-evaluated, not re-read: a stale artifact is caught here."""
    rows = _grid_rows()
    sampled = [
        row
        for row in rows
        if float(row["delta"]) in (-0.15, 0.05, 0.20) and float(row["vol_move"]) in (-0.06, 0.06)
    ]
    assert len(sampled) == 6, f"sampled {len(sampled)} cells, expected 6"
    for row in sampled:
        delta, vol_move = float(row["delta"]), float(row["vol_move"])
        for variant in MAP_KEYS:
            expected = _engine_pnl(delta, vol_move, _exposure_points(delta, vol_move, variant))
            assert float(row[f"pnl_{variant}"]) == pytest.approx(expected, abs=1e-9), (
                f"delta={delta} k={vol_move} {variant}"
            )
            assert float(row[f"error_{variant}"]) == pytest.approx(
                float(row["exact_pnl"]) - float(row[f"pnl_{variant}"]), abs=1e-9
            )


def test_the_restrike_moves_only_the_gamma_exposure() -> None:
    """`gamma_restrike` differs from `base` by the moved gamma and nothing else, per cell."""
    for delta, vol_move in ((0.05, -0.06), (-0.15, 0.06), (0.20, 0.03), (-0.30, -0.10)):
        errors = _priced_error(delta, vol_move)
        removed = _gamma_exposure(SPOT, VOLATILITY + vol_move) - _gamma_exposure(SPOT, VOLATILITY)
        assert errors["base"] - errors["gamma_restrike"] == pytest.approx(
            removed * delta * delta, abs=1e-8
        ), f"delta={delta} k={vol_move}: the restrike is not only the gamma move"
        # Delta and vega stay at the base market, which is what separates variant 2 from variant 4.
        assert errors["gamma_restrike"] != pytest.approx(errors["all_restrike"], rel=1e-6)


def test_the_zero_volatility_column_leaves_the_first_two_maps_identical() -> None:
    """Claim 3's control: with no vol move the restrike is the identity, in the committed table."""
    rows = [row for row in _grid_rows() if float(row["vol_move"]) == 0.0]
    assert len(rows) == 12, f"expected one row per delta column, got {len(rows)}"
    for row in rows:
        assert abs(float(row["pnl_base"]) - float(row["pnl_gamma_restrike"])) < 1e-9


def test_the_measured_zeros_are_zeros_of_the_priced_error() -> None:
    """The root finder is checked against the engine, not against itself."""
    located = [
        row for row in _payload()["cancellation"] if row["nearest_measured_zero"] is not None
    ]
    assert len(located) >= 8, f"only {len(located)} columns report a measured zero"
    for row in located:
        delta, zero = float(row["delta"]), float(row["nearest_measured_zero"])
        errors = _priced_error(delta, zero)
        assert abs(errors["base"]) < 1e-6, f"delta={delta}: {errors['base']!r} is not a zero"
        either_side = [abs(_priced_error(delta, zero + shift)["base"]) for shift in (-5e-4, 5e-4)]
        assert max(either_side) > 100.0 * abs(errors["base"]), (
            f"delta={delta}: the error does not change sign across its reported zero "
            f"({either_side} vs {abs(errors['base'])})"
        )


def test_the_cancellation_explanation_covers_every_doubled_cell() -> None:
    """Recounted from the table: a cell that gets twice as wrong was cancelling the term removed."""
    rows = [row for row in _grid_rows() if float(row["vol_move"]) != 0.0]
    doubled = [
        row
        for row in rows
        if float(row["abs_error_gamma_restrike"]) > 2.0 * float(row["abs_error_base"])
    ]
    unexplained = [
        row for row in doubled if float(row["abs_error_base"]) >= abs(float(row["removed_term"]))
    ]
    assert doubled, "no cell gets worse, so the claim being guarded would be vacuous"
    assert not unexplained, f"{len(unexplained)} doubled cells have no cancellation to blame"
    headline = _payload()["headline"]
    assert len(rows) == headline["cells_with_a_volatility_move"]
    assert len(doubled) == headline["cells_where_restrike_at_least_doubles_error"]
    assert headline["of_those_the_base_error_was_smaller_than_the_removed_term"] == len(doubled), (
        "the headline count and the table disagree about which cells were cancelling"
    )


def test_the_docstring_figures_and_counts_are_the_ones_the_artifact_holds() -> None:
    """Every number the producer's own docstring quotes, re-derived from the artifact."""
    headline = _payload()["headline"]
    asymptotics = _payload()["asymptotics"]
    doc = (EXPERIMENT / "run.py").read_text(encoding="utf-8")
    phase_13 = json.loads(
        (REPO_ROOT / "experiments/two_factor_error_bound/results/two_factor_bound.json").read_text(
            encoding="utf-8"
        )
    )["headline"]

    pair = [row["local_slope_narrowest_pair"] for series in asymptotics.values() for row in series]
    window = [row["slope_narrow_end"] for series in asymptotics.values() for row in series]
    whole = [row["slope"] for series in asymptotics.values() for row in series]
    small = [
        row["nearest_zero_distance"]
        for row in _payload()["cancellation"]
        if abs(row["delta"]) <= harness.SMALL_MOVE_LIMIT
        and row["nearest_zero_distance"] is not None
    ]
    wide = [
        row
        for row in _payload()["cancellation"]
        if abs(row["delta"]) > harness.SMALL_MOVE_LIMIT and row["nearest_zero_distance"] is not None
    ]
    expected = [
        f"{phase_13['largest_cubic_over_net_quadratic']:.1f}×",
        f"{round(100 * headline['published_fraction_of_local_term_removed'])} %",
        f"{headline['published_error_base']:,.2f}",
        f"{headline['published_error_gamma_restrike']:+,.2f}",
        f"{headline['published_restrike_factor']:.3f}",
        f"{min(pair):.2f}-{max(pair):.2f}",
        f"{min(window):.2f}-{max(window):.2f}",
        f"{min(whole):.2f}-{max(whole):.2f}",
        f"{headline['zero_vol_control_max_gap']:.1f}",
        f"{headline['all_restrike_worse_than_gamma_only']} of the "
        f"{headline['cells_with_a_volatility_move']} cells",
        f"{headline['cells_where_restrike_does_not']} of "
        f"{headline['cells_with_a_volatility_move']} cells",
        f"{headline['cells_where_restrike_at_least_doubles_error']} of those",
        f"{round(headline['worst_error_factor_after_over_before'])}",
        f"{min(small):.4f}-{max(small):.4f}",
        f"{harness.CROSSING_MATCH_TOLERANCE:.3f}",
        f"{max(row['nearest_zero_distance'] for row in wide):.3f}",
    ]
    naive = abs(headline["published_error_all_restrike"]) / abs(headline["published_error_base"])
    expected.append(f"factor of {round(naive)}")
    missing = [figure for figure in expected if figure not in doc]
    assert not missing, f"docstring does not carry the artifact's own {missing}"
    widest = max(wide, key=lambda row: row["nearest_zero_distance"])
    assert widest["delta"] == -0.30, (
        "the worst drift is no longer on the column the docstring names"
    )
    at_edge = [
        row
        for row in _payload()["cancellation"]
        if row["predicted_zero_count"] and not row["measured_zero_count"]
    ]
    assert [row["delta"] for row in at_edge] == [0.30], (
        "the column where the truncation predicts a zero the map never has is not the one quoted"
    )


def test_the_refusals_name_the_limits_the_grid_shows() -> None:
    """The limits are part of the artifact, so a document cannot quote a blanket improvement."""
    refusals = _payload()["refusals"]
    assert set(refusals) == {
        "improvement_is_not_uniform",
        "cancellation_is_not_accuracy",
        "order_not_changed",
        "truncation_is_valid_only_near_the_base",
        "book_specific_ranking",
        "counts_are_not_money",
    }, sorted(refusals)
    assert all(text.strip() for text in refusals.values())
    headline = _payload()["headline"]
    assert headline["cells_where_restrike_does_not"] > 0, (
        "the grid no longer contains a cell the re-strike fails to help, so "
        "`improvement_is_not_uniform` is a refusal nobody needs"
    )


def test_the_published_tables_have_the_columns_the_documents_read() -> None:
    assert list(_grid_rows()[0]) == [
        "delta",
        "vol_move",
        "exact_pnl",
        *(f"pnl_{name}" for name in MAP_KEYS),
        *(f"error_{name}" for name in MAP_KEYS),
        "abs_error_base",
        "abs_error_gamma_restrike",
        "abs_error_all_restrike",
        "removed_term",
        "base_error_was_smaller_than_removed_term",
        "restrike_improves",
        "restrike_factor",
        "value_at_risk",
    ]
    assert {row["map"] for row in csv.DictReader(PUBLISHED_CSV.open(encoding="utf-8"))} == {
        *MAP_KEYS
    }
    cancellation = list(csv.DictReader(CANCELLATION_CSV.open(encoding="utf-8")))
    assert {"nearest_predicted_zero", "nearest_measured_zero", "nearest_zero_distance"} <= set(
        cancellation[0]
    )
    assert len(cancellation) == 12


def test_rerunning_the_experiment_in_a_temporary_tree_reproduces_the_committed_numbers(
    tmp_path: Path,
) -> None:
    """Determinism, without letting the test write into frozen evidence.

    The copy has to sit at the same depth: the experiment reads the published scenario by walking up
    to the repository root, and a bare copy in `tmp_path` would resolve that root to a temp dir.
    """
    destination = tmp_path / "experiments" / "restrike_gamma_map" / "run.py"
    destination.parent.mkdir(parents=True)
    destination.write_text((EXPERIMENT / "run.py").read_text(encoding="utf-8"), encoding="utf-8")
    upstream = tmp_path / "experiments" / "stress_testing"
    upstream.mkdir(parents=True)
    (upstream / "run.py").write_text(
        (REPO_ROOT / "experiments" / "stress_testing" / "run.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    before = ARTIFACT.read_bytes()
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(destination)],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    assert ARTIFACT.read_bytes() == before, "the test run modified a committed artifact"

    produced = destination.parent / "results" / "restrike_gamma_map.json"
    assert produced.exists(), f"the copy wrote no artifact; stdout: {completed.stdout[-400:]}"
    mine, theirs = _payload(), json.loads(produced.read_text(encoding="utf-8"))
    for key in ("generated_at_utc", "environment", "artifacts"):
        mine.pop(key, None)
        theirs.pop(key, None)
    limited = tuple(theirs["reproduction_policy"]["conditioning_limited"])
    problems = _assert_same_result(mine, theirs, limited=limited)
    assert not problems, "the reproduction differs from the committed artifact:\n" + "\n".join(
        problems[:20]
    )


def test_every_figure_the_note_and_the_finding_quote_is_in_the_artifact() -> None:
    """`docs/analysis/restrike_gamma_map.md`, finding 7 and the report restate this experiment.

    `docs/limitations.md` #77 is the record of what happens otherwise: a note's headline
    slope had no owner in the tree at all. So each figure the two documents print is
    re-derived here from the artifact, formatted the way the prose formats it, and a note
    without a reader fails this rather than shipping a number nothing computes.
    """
    payload = _payload()
    headline = payload["headline"]
    asymptotics = payload["asymptotics"]
    phase_13 = json.loads(
        (REPO_ROOT / "experiments/two_factor_error_bound/results/two_factor_bound.json").read_text(
            encoding="utf-8"
        )
    )["headline"]
    pair = [row["local_slope_narrowest_pair"] for s in asymptotics.values() for row in s]
    window = [row["slope_narrow_end"] for s in asymptotics.values() for row in s]
    whole = [row["slope"] for s in asymptotics.values() for row in s]
    small = [
        row["nearest_zero_distance"]
        for row in payload["cancellation"]
        if abs(row["delta"]) <= harness.SMALL_MOVE_LIMIT
        and row["nearest_zero_distance"] is not None
    ]
    wide = [
        row["nearest_zero_distance"]
        for row in payload["cancellation"]
        if abs(row["delta"]) > harness.SMALL_MOVE_LIMIT and row["nearest_zero_distance"] is not None
    ]
    shared = {
        "fraction_of_term": f"{100 * headline['published_fraction_of_local_term_removed']:.1f}",
        "removed_term": f"{abs(headline['published_removed_term']):,.2f}",
        "local_cubic": f"{abs(headline['published_local_cubic_gamma_sigma']):,.2f}",
        "error_base": f"{headline['published_error_base']:,.2f}",
        "error_restrike": f"{headline['published_error_gamma_restrike']:+,.2f}",
        "restrike_factor": f"{headline['published_restrike_factor']:.3f}",
        "naive_error": f"{abs(headline['published_error_all_restrike']):,.2f}",
        "cells_not_improved": f"{headline['cells_where_restrike_does_not']} of "
        f"{headline['cells_with_a_volatility_move']}",
        "doubling_cells": str(headline["cells_where_restrike_at_least_doubles_error"]),
        "worst_factor": str(round(headline["worst_error_factor_after_over_before"])),
        "value_weighted": f"{headline['value_weighted_reduction']:.4f}",
        "naive_worse_cells": f"{headline['all_restrike_worse_than_gamma_only']} of the "
        f"{headline['cells_with_a_volatility_move']}",
        "naive_over_shipped": str(
            round(
                abs(headline["published_error_all_restrike"])
                / abs(headline["published_error_base"])
            )
        ),
        "pair_span": f"{min(pair):.2f}-{max(pair):.2f}",
        "small_move_distance_span": f"{min(small):.4f}-{max(small):.4f}",
        "tolerance": f"{harness.CROSSING_MATCH_TOLERANCE:.3f}",
        "wide_drift": f"{max(wide):.3f}",
        "predicted_zeros": str(headline["predicted_zeros_total"]),
        "measured_zeros": str(headline["measured_zeros_total"]),
    }
    documents = {
        "docs/analysis/restrike_gamma_map.md": shared
        | {
            "net_quadratic_ratio": f"{phase_13['largest_cubic_over_net_quadratic']:.1f}",
            "mechanism_probes": str(headline["mechanism_probes"]),
            "mechanism_mismatch": (
                f"{headline['mechanism_worst_map_difference_relative_error']:.1e}"
            ),
            "window_span": f"{min(window):.2f}-{max(window):.2f}",
            "whole_ray_span": f"{min(whole):.2f}-{max(whole):.2f}",
        },
        "paper/technical_report.tex": {
            label: value.replace(",", "") for label, value in shared.items()
        }
        | {"mechanism_probes": str(headline["mechanism_probes"])},
        "docs/findings.md": shared
        | {
            "share_improved": f"{100 * headline['share_improved']:.1f}",
            "worst_cell_base_error": "1.11",
            "worst_cell_restrike_error": "158.05",
        },
    }
    worst_cell = max(
        (
            row
            for row in _grid_rows()
            if float(row["vol_move"]) != 0.0
            and float(row["abs_error_gamma_restrike"]) > 2 * float(row["abs_error_base"])
        ),
        key=lambda row: float(row["abs_error_gamma_restrike"]) / float(row["abs_error_base"]),
    )
    assert f"{float(worst_cell['abs_error_base']):.2f}" == "1.11"
    assert f"{float(worst_cell['abs_error_gamma_restrike']):.2f}" == "158.05"
    for name, claims in documents.items():
        # The documents set their numbers in running prose with a typographic minus and, in the
        # report, with en-dashes for ranges; the artifact formats in ASCII. Normalising the
        # typography keeps this a check on the digits, which are the part that can go stale.
        text = (
            (REPO_ROOT / name).read_text(encoding="utf-8").replace("\u2212", "-").replace("--", "-")
        )
        for label, value in claims.items():
            assert value in text, f"{name} does not print {label} as {value!r}"
