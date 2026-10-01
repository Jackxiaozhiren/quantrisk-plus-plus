"""The fourth-order crossing map: the artifact's numbers must be the ones the code re-derives.

This experiment publishes four claims, and three of them are arithmetic on quantities the repository
already holds: the order-four coefficients are core closed forms, the truncation is the phase-15
truncation plus a published polynomial, and the zeros are roots of a function any reader can
re-evaluate. So the tests here do not restate the claims; they rebuild the inputs independently and
compare.

Three of them check the *instruments* rather than the result. The ordering claim (a cubic residual
falling with slope 4 and a quartic residual with slope 5) is a statement about a log-log fit, and a
fit that silently returned a constant would let every number in the artifact agree with itself while
saying nothing. The crossing claim is a statement about a distance, and a distance that answered
`0.0` for an empty column would have turned the four columns the cubic misses into a vacuous pass.
And the coefficient sums are re-added strike by strike, because a partial read off one leg rather
than three still draws a plausible curve.

A further test pins every figure the module docstring quotes to the artifact field it came from:
the docstring is what a reader copies, the artifact is what the run produced, and that pair drifted
apart
once already, in v1.4.0.

The reproduction test reuses the shared comparison helper rather than writing its own, and passes it
the conditioning families this artifact declares. Six CI runs of an earlier phase established that
the exemption has to be by kind rather than by field name.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import quantrisk
from test_two_factor_bound import _assert_same_result

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "experiments" / "fourth_order_crossing_map" / "run.py"
ARTIFACT = (
    REPO_ROOT
    / "experiments"
    / "fourth_order_crossing_map"
    / "results"
    / "fourth_order_crossing_map.json"
)
SHALLOW = "shallow (equity down, vol up, a third of the size)"
STRIKES = (90.0, 100.0, 110.0)
QUANTITY = 5000.0


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def experiment():
    return _load(SCRIPT, "quantrisk_fourth_order_crossing_map_under_test")


@pytest.fixture(scope="module")
def payload() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _market(volatility: float = 0.20) -> quantrisk.pricing.MarketParams:
    return quantrisk.pricing.MarketParams(
        spot=100.0, rate=0.03, dividend_yield=0.0, volatility=volatility, maturity=0.5
    )


def _option(strike: float):
    return quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, strike)


def test_the_order_four_coefficients_are_slopes_of_the_published_third_order() -> None:
    """Three of the new coefficients are finite differences of partials shipped before this phase.

    The artifact's coefficients come from `black_scholes_mixed_fourth_derivatives`. Recomputing them
    as one volatility derivative of the partial below it reaches the same number through different
    code, so a transcription slip in the core's Horner form - a `6 d1 v^2` where the polynomial says
    `3 d1 v^2`, say - cannot confirm itself. Two different core calls supply the four sources,
    so the route never reads the struct it is checking.
    """
    market = _market()
    third = quantrisk.pricing.black_scholes_mixed_third_derivatives
    speed = quantrisk.pricing.black_scholes_spot_derivatives
    fourth = quantrisk.pricing.black_scholes_mixed_fourth_derivatives
    step = 1.0e-4 * market.volatility

    def slope(option, read) -> float:
        """Five-point central slope, in volatility, of one published partial."""

        def value(k: float) -> float:
            return float(read(option, _market(market.volatility + k)))

        return (value(-2 * step) - 8 * value(-step) + 8 * value(step) - value(2 * step)) / (
            12 * step
        )

    # One volatility derivative of the partial one order below: the Schwarz route the core's own
    # field documentation names for each of the four.
    routes = {
        "spot_spot_spot_sigma": lambda option, at: speed(option, at).third,
        "spot_spot_sigma_sigma": lambda option, at: third(option, at).spot_spot_sigma,
        "spot_sigma_sigma_sigma": lambda option, at: third(option, at).spot_sigma_sigma,
        "sigma_sigma_sigma_sigma": lambda option, at: third(option, at).sigma_sigma_sigma,
    }
    worst = 0.0
    for strike in STRIKES:
        option = _option(strike)
        got = fourth(option, market)
        for field, read in routes.items():
            reference = slope(option, read)
            value = float(getattr(got, field))
            worst = max(worst, abs(value - reference) / max(1e-12, abs(reference)))
    assert worst < 1e-4, worst


def test_the_artifact_coefficients_are_the_book_sums_the_code_computes(experiment, payload) -> None:
    """Each published sum is the three strikes added by hand, at the position size the book uses.

    A coefficient entered twice, or read off one leg rather than three, still draws a plausible
    truncation; only this kind of check makes the factor visible.
    """
    market = _market()
    fourth = quantrisk.pricing.black_scholes_mixed_fourth_derivatives
    spot = quantrisk.pricing.black_scholes_spot_derivatives
    for field in (*experiment.FOURTH_FIELDS, "spot_x4"):
        expected = 0.0
        for strike in STRIKES:
            option = _option(strike)
            source = spot(option, market) if field == "spot_x4" else fourth(option, market)
            expected += float(getattr(source, "fourth" if field == "spot_x4" else field)) * QUANTITY
        assert payload["coefficients"]["fourth_order"][field] == pytest.approx(
            expected, rel=1e-12, abs=0.0
        )


def test_the_quartic_is_the_cubic_plus_the_published_polynomial(experiment, payload) -> None:
    """The order-four piece is exactly the documented contraction, at the moves the claims quote.

    Rebuilt from the artifact's own stored coefficients, so the binomial weights (`1, 4, 6, 4, 1`
    over 24) are tested rather than asserted; a `k` where an `h` belongs moves it by percent.
    """
    coefficients = payload["coefficients"]["fourth_order"]
    for delta, move in ((-0.15, 0.06), (-0.30, 0.20), (0.10, -0.03), (0.05, 0.0), (0.0, 0.06)):
        h = experiment.SPOT * delta
        expected = (
            coefficients["spot_x4"] * h**4
            + 4.0 * coefficients["spot_spot_spot_sigma"] * h**3 * move
            + 6.0 * coefficients["spot_spot_sigma_sigma"] * h * h * move * move
            + 4.0 * coefficients["spot_sigma_sigma_sigma"] * h * move**3
            + coefficients["sigma_sigma_sigma_sigma"] * move**4
        ) / 24.0
        got = experiment.quartic_column_term(delta, move)
        assert abs(got - expected) <= 1e-9 * max(1e-9, abs(expected)), (delta, move, got, expected)
    for delta, move in ((-0.15, 0.06), (0.20, -0.10)):
        total = experiment.quartic_column_error(delta, move)
        pieces = experiment.cubic_column_error(delta, move) + experiment.quartic_column_term(
            delta, move
        )
        assert total == pieces, (delta, move, total, pieces)


def test_the_log_log_fit_measures_the_order_it_claims(experiment) -> None:
    """The instrument behind claim 1: a fit that could not see x^5 would pass its bands vacuously.

    Three synthetic series - x^4, x^5, a constant - go through the helper the artifact uses. The
    first two must return 4.0 and 5.0; the third must return 0.0, which is what separates a slope
    from a subtraction of two nearly equal numbers.
    """
    scales = [0.03, 0.01, 0.003, 0.001]
    for power, expected in ((4, 4.0), (5, 5.0), (0, 0.0)):
        values = [scale**power for scale in scales]
        slope, standard_error = experiment._log_log_of(scales, values)
        assert abs(slope - expected) < 1e-9, (power, slope)
        assert standard_error < 1e-9, (power, standard_error)


def test_the_distance_function_answers_for_empty_columns(experiment) -> None:
    """The instrument behind claim 2: `None` on an empty side is a report, not a pass.

    Four columns of the swept grid have no priced zero at all. Had `nearest` returned 0.0 for those,
    the widened gate would have counted them as agreement, and the claim would have been about eight
    columns while reading as twelve.
    """
    assert experiment.nearest([], [0.01]) is None
    assert experiment.nearest([0.01], []) is None
    assert experiment.nearest([], []) is None
    assert experiment.nearest([0.0, 0.1], [0.09]) == pytest.approx(0.01)
    assert experiment.nearest([-0.05], [-0.05]) == 0.0


def test_the_widening_is_a_fact_about_both_truncations(experiment, payload) -> None:
    """Claim 2, re-derived from the artifact's per-column rows rather than from its headline.

    The worst distances are recomputed from `columns`, and the columns the cubic misses between the
    two limits are required to be the ones the headline names - so a headline that quietly counted a
    different set is caught rather than quoted.
    """
    columns = payload["columns"]
    limit = experiment.WIDENED_LIMIT
    tolerance = payload["headline"]["tolerance"]
    inside = [row for row in columns if abs(row["delta"]) <= limit and row["measured_zero_count"]]
    # Eight columns sit inside |delta| <= 0.15; `delta = -0.02` has no priced crossing at all,
    # which is why the widened gate counts seven rather than eight. An earlier draft of this check
    # asserted eight and so would have silently passed if that column had grown a zero.
    assert len(inside) == 7
    quartic = [row["quartic_nearest_zero_distance"] for row in inside]
    cubic = [row["cubic_nearest_zero_distance"] for row in inside]
    assert max(quartic) == pytest.approx(
        payload["headline"]["quartic_distance_max_within_the_widened_limit"]
    )
    assert max(cubic) == pytest.approx(
        payload["headline"]["cubic_distance_max_within_the_widened_limit"]
    )
    assert max(quartic) <= tolerance
    between = {
        abs(row["delta"]) for row in inside if abs(row["delta"]) > experiment.P15.SMALL_MOVE_LIMIT
    }
    assert between == {
        abs(value)
        for value in payload["headline"]["columns_the_cubic_misses_between_the_two_limits"]
    }
    for row in inside:
        if abs(row["delta"]) in between:
            assert row["cubic_nearest_zero_distance"] > tolerance, row["delta"]
            assert row["quartic_nearest_zero_distance"] <= tolerance, row["delta"]


def test_the_measured_zeros_are_sign_changes_of_the_priced_error(experiment, payload) -> None:
    """A root the engine does not have is not a measurement.

    Re-evaluated through `run_scenario` at every zero the artifact publishes, over the whole swept
    grid rather than only the nearest per column. Two things are asserted, because one is not
    enough:
    the value at the root must be small in absolute terms, and the priced error must actually change
    sign across it. The second is the one that survives a steep column - a crossing where the error
    runs at 1e8 per vol point leaves a residual of 1.6e-5 there even when the *location* is right to
    one part in 1e12, so a magnitude bound alone would reject a genuine zero.
    """
    probe = 1.0e-4
    worst_value, worst_relative = 0.0, 0.0
    for row in payload["columns"]:
        for move in row["measured_zeros"]:
            here = experiment.priced_column_error(row["delta"], move)
            before = experiment.priced_column_error(row["delta"], move - probe)
            after = experiment.priced_column_error(row["delta"], move + probe)
            assert before * after <= 0.0, (row["delta"], move, before, after)
            worst_value = max(worst_value, abs(here))
            step = abs(after - before)
            worst_relative = max(worst_relative, abs(here) / step if step else 0.0)
    assert worst_value <= 1e-6, worst_value
    assert worst_relative <= 1e-3, worst_relative
    # The nearest zero per column, which is what the run gates, is held to the stricter band.
    nearest_residual = max(
        row["priced_error_at_nearest_measured_zero"] or 0.0
        for row in payload["columns"]
        if row["measured_zeros"]
    )
    assert nearest_residual <= 1e-6, nearest_residual


def test_the_ray_residuals_reproduce_the_stated_slopes(experiment, payload) -> None:
    """Claim 1's slopes are re-fitted from the artifact's own per-scale rows.

    The window is asserted as well as the number: five scales between the arithmetic floor and a
    third of the published shock. The through-the-floor fit is re-derived too and must be worse,
    because that is the evidence the window is a measurement choice rather than a favour.
    """
    floor, ceiling = experiment.FIT_FLOOR, experiment.ORDERING_CEILING
    for label, block in payload["rays"].items():
        rows = block["rows"]
        for name, field in (
            ("cubic", "residual_after_cubic"),
            ("quartic", "residual_after_quartic"),
        ):
            window = [
                (row["scale"], row[field]) for row in rows if floor <= row["scale"] <= ceiling
            ]
            assert len(window) == 5, (label, name, len(window))
            slope, _ = experiment._log_log_of([s for s, _ in window], [v for _, v in window])
            stored = block[f"residual_slope_after_{name}"]
            assert abs(slope - stored) < 1e-9, (label, name, slope, stored)
        through = [
            (row["scale"], row["residual_after_quartic"]) for row in rows if row["scale"] <= 0.03
        ]
        loose, _ = experiment._log_log_of([s for s, _ in through], [v for _, v in through])
        assert loose < block["residual_slope_after_quartic"], (label, loose)
        assert abs(loose - block["residual_slope_quartic_through_the_floor"]) < 1e-9, label


def test_the_published_scenario_side_is_the_engine_not_the_algebra(experiment, payload) -> None:
    """Claim 4's priced errors are re-measured through `run_scenario`, not read from the artifact.

    The two relative errors must also carry opposite signs, which is the substance of the claim: the
    quartic does not narrow the gap, it crosses it.
    """
    block = payload["published_scenario"]
    delta, move = block["delta"], block["vol_move"]
    assert (
        abs(experiment.priced_column_error(delta, move) - block["base_map"]["priced_error"]) < 1e-6
    )
    restrike = {
        **experiment.P15.BASE,
        "gamma": experiment.P15.totals(experiment.SPOT, experiment.VOLATILITY + move)["gamma"],
    }
    priced_restrike = experiment.P15.exact_move(delta, move) - experiment.P15.engine_pnl(
        delta, move, restrike
    )
    assert abs(priced_restrike - block["gamma_restrike_map"]["priced_error"]) < 1e-6
    assert block["base_map"]["cubic_relative_error"] > 0.0
    assert block["base_map"]["quartic_relative_error"] < 0.0
    assert block["gamma_restrike_map"]["cubic_relative_error"] > 0.0
    assert block["gamma_restrike_map"]["quartic_relative_error"] < 0.0


def test_the_module_docstring_figures_are_the_ones_the_artifact_holds(payload) -> None:
    """Every figure the module docstring quotes is the artifact's own, at its own precision.

    The docstring is what a reader copies and the artifact is what the run produced. A figure that
    survives an edit to one of them and not the other is how v1.4.0 shipped a stale share.
    """
    docstring = SCRIPT.read_text(encoding="utf-8").split('"""')[1]
    headline = payload["headline"]
    published = payload["published_scenario"]

    def assert_figure(figure: str, value: float, decimals: int) -> None:
        assert figure in docstring, figure
        assert abs(value - float(figure.replace(",", ""))) <= 0.5 * 10**-decimals, (figure, value)

    for figure, (low, high) in {
        "3.96-4.37": headline["residual_slope_cubic_span"],
        "4.73-5.01": headline["residual_slope_quartic_span"],
        "2.46-4.30": headline["residual_slope_quartic_through_floor_span"],
        "0.0013-0.048": headline["residual_ratio_at_the_fit_floor_span"],
        "0.62-1.04": headline["ratio_slope_span"],
    }.items():
        assert figure in docstring, figure
        for quoted, value in zip(figure.split("-"), (low, high), strict=True):
            decimals = len(quoted.split(".")[1])
            assert abs(value - float(quoted)) <= 0.5 * 10**-decimals, (figure, quoted, value)

    assert_figure("0.00162", headline["quartic_distance_max_within_the_widened_limit"], 5)
    assert_figure("0.01887", headline["cubic_distance_max_within_the_widened_limit"], 5)
    assert_figure("0.0323", headline["quartic_distance_max_beyond_the_widened_limit"], 4)
    assert_figure("0.0934", headline["cubic_distance_max_beyond_the_widened_limit"], 4)
    assert_figure("0.00243", headline["cubic_distance_max_within_the_published_limit"], 5)
    assert_figure("11.6", headline["improvement_factor_at_the_widened_limit"], 1)
    assert_figure(
        "211.6",
        headline["cubic_distance_max_within_the_published_limit"]
        / headline["quartic_distance_max_within_the_published_limit"],
        1,
    )
    assert_figure("-5,320.79", published["base_map"]["priced_error"], 2)
    assert_figure("-4,135.87", published["base_map"]["cubic_truncation"], 2)
    assert_figure("-6,182.27", published["base_map"]["quartic_truncation"], 2)
    assert_figure("-2,046.40", published["order_four_piece"], 2)
    assert_figure(
        "1,184.92",
        abs(published["base_map"]["priced_error"] - published["base_map"]["cubic_truncation"]),
        2,
    )
    assert abs(headline["quartic_distance_max_within_the_published_limit"] - 1.15e-5) <= 0.005e-5
    assert "1.15e-5" in docstring

    for figure, value in (
        ("22.3 %", published["base_map"]["cubic_relative_error"]),
        ("16.2 %", published["base_map"]["quartic_relative_error"]),
        ("61.2 %", published["gamma_restrike_map"]["cubic_relative_error"]),
        ("44.5 %", published["gamma_restrike_map"]["quartic_relative_error"]),
    ):
        assert figure in docstring, figure
        assert abs(abs(value) * 100.0 - float(figure.split(" %")[0])) < 0.05, (figure, value)

    assert headline["measured_zeros_total"] == 13
    assert headline["cubic_zeros_total"] == headline["quartic_zeros_total"] == 14
    assert len(headline["cubic_count_disagreements"]) == 3
    assert len(headline["quartic_count_disagreements"]) == 1
    assert headline["rays_where_the_quartic_is_worse_at_grid_size"] == [SHALLOW]
    shallow = payload["rays"][SHALLOW]
    third_size = next(
        row["residual_ratio_quartic_over_cubic"] for row in shallow["rows"] if row["scale"] == 0.3
    )
    assert abs(abs(shallow["ratio_at_grid_size"]) - 1.38) < 0.005, shallow["ratio_at_grid_size"]
    assert abs(abs(third_size) - 0.23) < 0.005, third_size


def test_every_figure_the_note_and_the_finding_quote_is_in_the_artifact(payload) -> None:
    """`docs/analysis/fourth_order_crossing_map.md` and finding 8 restate this experiment.

    Each figure the two documents print is re-derived here from the artifact and formatted the way
    the prose formats it. `docs/limitations.md` #77 records what happens otherwise: a note's
    headline slope had no owner in the tree at all. The guard that reads every note catches the
    missing reader; this is the reader.
    """
    headline = payload["headline"]
    published = payload["published_scenario"]
    base = published["base_map"]
    struck = published["gamma_restrike_map"]
    cubic_span = headline["residual_slope_cubic_span"]
    quartic_span = headline["residual_slope_quartic_span"]
    floor_span = headline["residual_slope_quartic_through_floor_span"]
    ratio_span = headline["ratio_slope_span"]
    floor_ratio = headline["residual_ratio_at_the_fit_floor_span"]
    inside = headline["quartic_distance_max_within_the_published_limit"]
    inside_cubic = headline["cubic_distance_max_within_the_published_limit"]
    overshoot = abs(payload["rays"][SHALLOW]["ratio_at_grid_size"])

    shared = {
        "cubic_slope": f"{cubic_span[0]:.2f}-{cubic_span[1]:.2f}",
        "quartic_slope": f"{quartic_span[0]:.2f}-{quartic_span[1]:.2f}",
        "floor_slope": f"{floor_span[0]:.2f}-{floor_span[1]:.2f}",
        "ratio_slope": f"{ratio_span[0]:.2f}-{ratio_span[1]:.2f}",
        "floor_ratio": f"{floor_ratio[0]:.4f}-{floor_ratio[1]:.3f}",
        "quartic_distance": f"{headline['quartic_distance_max_within_the_widened_limit']:.5f}",
        "cubic_distance": f"{headline['cubic_distance_max_within_the_widened_limit']:.5f}",
        "radius_factor": f"{headline['improvement_factor_at_the_widened_limit']:.1f}",
        "published_quartic": f"{inside:.2e}".replace("e-05", "e-5"),
        "published_cubic": f"{inside_cubic:.5f}",
        "published_factor": f"{inside_cubic / inside:.1f}",
        "beyond_quartic": f"{headline['quartic_distance_max_beyond_the_widened_limit']:.4f}",
        "beyond_cubic": f"{headline['cubic_distance_max_beyond_the_widened_limit']:.4f}",
        "measured_zeros": str(headline["measured_zeros_total"]),
        "cubic_zeros": str(headline["cubic_zeros_total"]),
        "quartic_zeros": str(headline["quartic_zeros_total"]),
        "cubic_amount_error": f"{100 * abs(base['cubic_relative_error']):.1f} %",
        "quartic_amount_error": f"{100 * abs(base['quartic_relative_error']):.1f} %",
        "restrike_cubic": f"{100 * abs(struck['cubic_relative_error']):.1f} %",
        "restrike_quartic": f"{100 * abs(struck['quartic_relative_error']):.1f} %",
        "order_four_piece": f"{published['order_four_piece']:,.2f}",
        "correction_needed": f"{abs(base['priced_error'] - base['cubic_truncation']):,.2f}",
        "priced_error": f"{base['priced_error']:,.2f}",
        "cubic_truncation": f"{base['cubic_truncation']:,.2f}",
        "quartic_truncation": f"{base['quartic_truncation']:,.2f}",
        "overshoot": f"{overshoot:.2f}x",
    }
    documents = {
        "docs/analysis/fourth_order_crossing_map.md": shared,
        # The report sets its numbers without thousands separators and its ranges with en-dashes.
        "paper/technical_report.tex": {
            key: value.replace(",", "") for key, value in shared.items()
        },
        "docs/findings.md": {
            key: shared[key]
            for key in (
                "cubic_slope",
                "quartic_slope",
                "ratio_slope",
                "quartic_distance",
                "cubic_distance",
                "radius_factor",
                "published_factor",
                "measured_zeros",
                "cubic_zeros",
                "quartic_zeros",
                "order_four_piece",
                "correction_needed",
                "overshoot",
            )
        },
    }
    for name, claims in documents.items():
        # The prose sets some numbers with a typographic minus, ranges with en-dashes, and (in the
        # report) thin spaces before percents; the artifact formats in ASCII. Normalising the
        # typography keeps this a check on the digits, which are the part that can go stale.
        text = (
            (REPO_ROOT / name)
            .read_text(encoding="utf-8")
            .replace("\u2212", "-")
            .replace("--", "-")
            .replace("\\,", " ")
            .replace("\\%", "%")
            .replace("  ", " ")
        )
        for label, value in claims.items():
            assert value in text, f"{name} does not print {label} as {value!r}"


def test_the_refusals_name_the_limits_the_run_shows(payload) -> None:
    """The refusals must cover the failures this experiment actually measured, not generic ones."""
    assert set(payload["refusals"]) >= {
        "radius_is_not_accuracy",
        "one_book",
        "zeros_are_sign_changes",
        "floor_is_not_a_term",
        "ordering_is_not_a_grid_size_claim",
        "counts_are_not_money",
    }
    headline = payload["headline"]
    assert headline["rays_where_the_quartic_is_worse_at_grid_size"], (
        "the ordering_is_not_a_grid_size_claim refusal describes a reversal this run must show"
    )
    assert headline["rays_with_a_floor_turnaround"] == headline["rays_number_of"]
    assert headline["improvement_factor_at_the_widened_limit"] > 1.0


def test_the_provenance_is_recorded_once(payload) -> None:
    """One owner for the environment block, the guard that caught the duplicated provenance."""
    assert "package_versions" not in payload
    assert payload["environment"]["packages"]["quantrisk"] == quantrisk.version()


def test_rerunning_the_experiment_in_a_temporary_tree_reproduces_the_committed_numbers(
    tmp_path: Path,
) -> None:
    """Determinism, without letting the test write into frozen evidence.

    The copy has to sit at the same depth: this experiment walks up to the repository root both to
    load the phase-15 module it extends and to read the published scenario, and a bare copy in
    `tmp_path` would resolve that root to a temp dir. Three files travel: this one, the phase-15
    module whose truncation it reuses, and the stress experiment that names `risk_off`.
    """
    tree = {
        "experiments/fourth_order_crossing_map/run.py",
        "experiments/restrike_gamma_map/run.py",
        "experiments/stress_testing/run.py",
    }
    for relative in tree:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text((REPO_ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8")

    copy = tmp_path / "experiments" / "fourth_order_crossing_map" / "run.py"
    before = ARTIFACT.read_bytes()
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(copy)],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    assert ARTIFACT.read_bytes() == before, "the test run modified a committed artifact"

    produced = copy.parent / "results" / "fourth_order_crossing_map.json"
    assert produced.exists(), f"the copy wrote no artifact; stdout: {completed.stdout[-400:]}"
    mine, theirs = (
        json.loads(ARTIFACT.read_text(encoding="utf-8")),
        json.loads(produced.read_text(encoding="utf-8")),
    )
    for key in ("generated_at_utc", "environment"):
        mine.pop(key, None)
        theirs.pop(key, None)
    limited = tuple(theirs["reproduction_policy"]["conditioning_limited"])
    problems = _assert_same_result(mine, theirs, limited=limited)
    assert not problems, "the reproduction differs from the committed artifact:\n" + "\n".join(
        problems[:20]
    )
