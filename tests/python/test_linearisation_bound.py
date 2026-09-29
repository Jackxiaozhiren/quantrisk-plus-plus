"""The Phase 12 analysis, tested as a claim rather than as a document.

`docs/analysis/delta_gamma_error_bound.md` derives a Lagrange remainder bound for the stress
layer's delta-gamma map and lists four predictions. This module checks all four against the
committed artifact, checks the closed forms for `V'''` and `V''''` independently of the derivation
that produced them, and pins the one empirical statement the phase was actually about: the
published error curve changes sign, and the theory says where.

The assertions read the artifact rather than recomputing the analysis, except where a test exists
precisely to recompute it — a guard that only re-reads its own input proves nothing.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

quantrisk = pytest.importorskip("quantrisk")

if TYPE_CHECKING:
    # mypy cannot see attributes through a name bound by `pytest.importorskip`, so the two types
    # used in the annotations below are imported for the type checker only. Nothing changes at
    # runtime: the annotations are strings, and the module is already required by the skip above.
    from quantrisk.pricing import EuropeanOption, MarketParams

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "experiments" / "linearisation_error_bound" / "results"
ARTIFACT = RESULTS / "linearisation_error_bound.json"
CSV_PATH = RESULTS / "linearisation_bound.csv"

SPOT, RATE, DIVIDEND, VOLATILITY, MATURITY = 100.0, 0.03, 0.0, 0.20, 0.5
STRIKES = (90.0, 100.0, 110.0)
QUANTITY = 5000.0


def _payload() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _rows() -> list[dict[str, str]]:
    with CSV_PATH.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _market(spot: float) -> MarketParams:
    return quantrisk.pricing.MarketParams(
        spot=spot,
        rate=RATE,
        dividend_yield=DIVIDEND,
        volatility=VOLATILITY,
        maturity=MATURITY,
    )


def _option(strike: float, put: bool = False) -> EuropeanOption:
    kind = quantrisk.pricing.OptionType.PUT if put else quantrisk.pricing.OptionType.CALL
    return quantrisk.pricing.EuropeanOption(kind, strike)


def _core_speed(spot: float) -> float:
    return (
        sum(
            quantrisk.pricing.black_scholes_spot_derivatives(_option(strike), _market(spot)).third
            for strike in STRIKES
        )
        * QUANTITY
    )


def _core_quartic(spot: float) -> float:
    return (
        sum(
            quantrisk.pricing.black_scholes_spot_derivatives(_option(strike), _market(spot)).fourth
            for strike in STRIKES
        )
        * QUANTITY
    )


def _book_value(spot: float) -> float:
    return (
        sum(
            quantrisk.pricing.black_scholes(_option(strike), _market(spot)).price
            for strike in STRIKES
        )
        * QUANTITY
    )


def _greeks(spot: float) -> tuple[float, float]:
    deltas, gammas = 0.0, 0.0
    for strike in STRIKES:
        greeks = quantrisk.pricing.black_scholes_greeks(_option(strike), _market(spot))
        deltas += greeks.delta
        gammas += greeks.gamma
    return deltas * QUANTITY, gammas * QUANTITY


def _independent_speed(spot: float, step: float = 2e-3) -> float:
    """V''' as a 5-point central difference of the core's *aggregate* gamma, with no reference
    to (5).

    The derivation of the closed form is `d/dS [e^{-qT} phi(d1) / (S v)]`; if that differentiation
    is wrong every bound in the artifact is still self-consistent, because they are all built from
    the same function. This is the one check that does not share its premises with the claim.

    The step is 2e-3 rather than something smaller: a 5-point stencil truncates at about
    `h^4 f5 / 30` while its round-off floor is about `eps |f| / h`, and 1e-5 sits under the floor
    for a book of this size -- it disagreed with the closed form by 3.6e-9 at spot 90, which is the
    difference scheme failing, not the algebra.
    """
    return (
        _greeks(spot - 2 * step)[1]
        - 8 * _greeks(spot - step)[1]
        + 8 * _greeks(spot + step)[1]
        - _greeks(spot + 2 * step)[1]
    ) / (12 * step)


def test_the_closed_form_for_the_third_derivative_survives_an_independent_difference() -> None:
    """(5)'s `V'''` against a finite difference of gamma, at four spots and both option types."""
    for spot in (70.0, 90.0, 100.0, 130.0):
        closed = _core_speed(spot)
        difference = _independent_speed(spot)
        assert closed == pytest.approx(difference, rel=0.0, abs=1e-9), (
            f"at spot {spot}: closed form {closed!r} vs difference of gamma {difference!r}"
        )
    # Call/put equality is a theorem (put-call parity is affine in S), not a convention.
    for strike in STRIKES:
        call = quantrisk.pricing.black_scholes_spot_derivatives(
            _option(strike), _market(SPOT)
        ).third
        put = quantrisk.pricing.black_scholes_spot_derivatives(
            _option(strike, put=True), _market(SPOT)
        ).third
        assert call == pytest.approx(put, rel=0.0, abs=0.0), (
            f"K={strike}: call V''' {call!r} != put V''' {put!r}; parity says they must be equal"
        )


def test_the_quartic_agrees_with_a_difference_of_the_third_derivative() -> None:
    step = 2e-3
    for spot in (85.0, 100.0, 115.0):
        # Signs as the 5-point first-derivative stencil has them: f'(x) =
        # (f(x-2h) - 8f(x-h) + 8f(x+h) - f(x+2h)) / 12h. The first version of this test flipped
        # every sign, which produced |V''''| with the wrong one and passed the magnitude check
        # nobody wrote -- the closeness of the two numbers was the only clue that the stencil, not
        # the closed form, was at fault.
        difference = (
            _core_speed(spot - 2 * step)
            - 8 * _core_speed(spot - step)
            + 8 * _core_speed(spot + step)
            - _core_speed(spot + 2 * step)
        ) / (12 * step)
        assert _core_quartic(spot) == pytest.approx(difference, rel=0.0, abs=1e-9), (
            f"at spot {spot}: {str(_core_quartic(spot))!r} vs {str(difference)!r}"
        )
        assert _core_quartic(spot) * difference > 0.0, (
            f"at spot {spot}: the stencil and the closed form disagree in sign, so one of the "
            "two is not the fourth derivative"
        )


def test_the_lagrange_coefficient_is_trapped_by_the_paths_speed_range() -> None:
    """Prediction B, straight from the artifact: `c = 6R/h^3` inside `[min, max] V'''`."""
    rows = _payload()["rows"]
    assert rows, "the artifact carries no sweep rows"
    for row in rows:
        assert row["coefficient_inside_segment_range"], (
            f"{row['direction']} {row['move']}: c = {row['lagrange_coefficient']} escaped "
            f"[{row['segment_speed_min']}, {row['segment_speed_max']}]"
        )
    payload = _payload()["headline"]
    assert payload["lagrange_inclusion_violations_swept"] == 0
    assert payload["lagrange_inclusion_violations_dense"] == 0
    assert payload["dense_shocks_tested"] >= 600


def test_the_absolute_bound_holds_and_is_not_vacuous() -> None:
    """The same theorem in its weaker form, plus the tightness the weak form cannot promise.

    Tightness is asserted *away from the remainder's own zero*. At a 20 % down move the signed
    remainder passes through zero while the supremum of |V'''| over the segment does not, so the
    ratio there is small by construction (0.0229) — that is the envelope behaving correctly, not a
    loose bound. Quoting a single min over all rows would either fail on honest data or force the
    test to hide the most interesting point in the sweep.
    """
    rows = _payload()["rows"]
    ratios = [row["remainder_over_bound"] for row in rows]
    assert max(ratios) <= 1.0, f"|R| exceeded the bound: worst ratio {max(ratios)}"

    near_zero = [row for row in rows if row["direction"] == "down" and 0.15 <= row["move"] <= 0.30]
    away = [row["remainder_over_bound"] for row in rows if row not in near_zero]
    assert away, "the sweep no longer has points away from the predicted remainder zero"
    assert min(away) > 0.2, f"the bound is vacuous away from the zero: tightest ratio {min(away)}"
    assert max(ratios) > 0.9, f"the bound is never approached: loosest ratio {max(ratios)}"
    assert near_zero, "the dip this analysis exists to explain is gone from the sweep"


def test_the_remainder_is_cubic_and_its_leading_coefficient_is_the_closed_form() -> None:
    """Prediction A. The evidence is the *convergence* of the slope, not one fitted number.

    At any fixed window the quartic term biases the log-log slope, and the bias is proportional to
    the window's top edge -- so a single slope either fails to reach 3 or succeeds by choosing a
    window. Shrinking the window and requiring the estimate to approach the theory value is the
    statement that survives contact with the higher order, and it is what the artifact records.
    """
    headline = _payload()["headline"]
    windows = _payload()["asymptotics"]["slope_windows"]
    for direction in ("down", "up"):
        series = windows[direction]
        assert len(series) >= 4, f"{direction}: too few windows to show convergence"
        distances = [abs(entry["slope"] - 3.0) for entry in series]
        # The series is ordered widest window first, so approaching the theory value means the
        # distances must strictly DECREASE along it. (Written first as `== sorted(distances)`,
        # which is the opposite ordering and failed on data that was behaving perfectly.)
        assert all(
            later < earlier for earlier, later in zip(distances, distances[1:], strict=False)
        ), f"{direction}: the slope does not approach 3 as the window shrinks: {distances}"
        assert distances[-1] < 0.005, f"{direction}: narrowest window still at {series[-1]}"
        assert all(entry["observations"] > 100 for entry in series)
        assert all(entry["standard_error"] > 0.0 for entry in series)
        assert abs(series[0]["slope"] - 3.0) <= 0.1, direction
    assert headline["leading_term_relative_error_at_smallest_move"] < 0.02
    # Recomputed here rather than trusted from the script: at the smallest swept down move the
    # cubic term must reproduce the remainder to the same tolerance.
    smallest = min(
        (row for row in _payload()["rows"] if row["direction"] == "down"),
        key=lambda row: row["move"],
    )
    assert smallest["remainder_over_cubic_prediction"] == pytest.approx(1.0, abs=0.02)


def test_the_fourth_derivative_shows_up_as_the_predicted_correction_to_the_cubic() -> None:
    """The quartic closed form, confirmed through prices rather than through a difference table.

    Dividing `R = V'''h^3/6 + V''''h^4/24 + O(h^5)` by the cubic term leaves a departure per unit
    of delta tending to `S * V'''' / (4 V''')`. Measuring that departure therefore validates the
    fourth-derivative formula independently of the finite-difference check on it, and the two
    directions must bracket the prediction, because the quartic has a fixed sign and `h^3`
    does not.
    """
    headline = _payload()["headline"]
    predicted = headline["quartic_correction_predicted_S_V4_over_4_V3"]
    assert predicted == pytest.approx(
        SPOT * _core_quartic(SPOT) / (4.0 * _core_speed(SPOT)), rel=0.0, abs=1e-12
    )
    measured = headline["quartic_correction_measured_at_delta_1e-3"]
    for direction, value in measured.items():
        assert value == pytest.approx(predicted, rel=0.02), (
            f"{direction}: departure {value} against the closed forms' {predicted}"
        )
    assert (measured["down"] - predicted) * (measured["up"] - predicted) < 0.0, (
        f"both directions sit on the same side of the prediction: {measured}"
    )


def test_the_theory_predicts_the_sign_change_the_published_curve_already_shows() -> None:
    """Prediction C, and the point of the phase.

    `experiments/stress_testing/results/linearisation_error.csv` -- frozen, hashed, and written a
    phase before this derivation -- contains one sign change in `abs_error`. The bound predicts a
    remainder zero, and that zero has to fall inside the bracket the older artifact already
    contains. Two artifacts made by different code agreeing on a location is the check; the same
    script agreeing with itself is not.
    """
    committed = list(
        csv.DictReader(
            (REPO_ROOT / "experiments" / "stress_testing" / "results" / "linearisation_error.csv")
            .read_text(encoding="utf-8")
            .splitlines()
        )
    )
    signs = [(float(row["move"]), float(row["abs_error"])) for row in committed]
    reversals = [
        (signs[index - 1][0], signs[index][0])
        for index in range(1, len(signs))
        if signs[index - 1][1] * signs[index][1] < 0.0
    ]
    assert len(reversals) == 1, (
        f"the published curve's sign changes are {reversals}; the analysis describes exactly one"
    )
    low, high = reversals[0]

    headline = _payload()["headline"]
    predicted = headline["predicted_remainder_zero_at_move"]
    assert low < predicted < high, (
        f"theory says R = 0 at a down move of {predicted:.4f}; the published data only brackets "
        f"({low}, {high})"
    )
    assert headline["aggregate_speed_crosses_zero_at_move"] < predicted, (
        "the mechanism has to precede the effect: V''' on the path crosses zero before the "
        "remainder does"
    )


def test_up_moves_do_not_cross_and_stay_monotone() -> None:
    """Prediction D: the asymmetry is derived, not sampled."""
    rows = _payload()["rows"]
    up = [row for row in rows if row["direction"] == "up"]
    coefficients = [row["lagrange_coefficient"] for row in up]
    assert all(value < 0.0 for value in coefficients), (
        f"an up-move Lagrange coefficient changed sign: {coefficients}"
    )
    magnitudes = [row["abs_remainder"] for row in up]
    assert magnitudes == sorted(magnitudes), f"up-move |R| is not monotone: {magnitudes}"
    down = [row for row in rows if row["direction"] == "down"]
    assert [row["abs_remainder"] for row in down] != sorted(row["abs_remainder"] for row in down), (
        "the down-move curve became monotone, so the published dip this analysis explains is gone"
    )


def test_the_bound_degenerates_honestly_at_zero_volatility() -> None:
    """The regularity hypotheses are load-bearing, so say what happens without them.

    With `sigma * sqrt(T) -> 0` the core reports zero for every higher spot derivative and the
    bound collapses to `0 <= 0`. That is vacuous rather than violated -- and the map really is
    exact off the strike kink in that limit, so the honest statement is that the proposition stops
    applying, not that it succeeded.
    """
    flat = quantrisk.pricing.MarketParams(
        spot=SPOT, rate=RATE, dividend_yield=DIVIDEND, volatility=0.0, maturity=MATURITY
    )
    derivatives = quantrisk.pricing.black_scholes_spot_derivatives(_option(100.0), flat)
    assert derivatives.third == 0.0
    assert derivatives.fourth == 0.0
    # And the map is exact there: a zero-volatility call is affine in spot away from the strike.
    shifted = quantrisk.pricing.MarketParams(
        spot=110.0, rate=RATE, dividend_yield=DIVIDEND, volatility=0.0, maturity=MATURITY
    )
    moved = quantrisk.pricing.black_scholes(_option(100.0), shifted).price
    held = quantrisk.pricing.black_scholes(_option(100.0), flat).price
    greeks = quantrisk.pricing.black_scholes_greeks(_option(100.0), flat)
    assert moved - held == pytest.approx(greeks.delta * 10.0, rel=0.0, abs=1e-12)


def test_the_experiment_artifact_carries_the_provenance_the_chain_requires() -> None:
    payload = _payload()
    assert payload["command"] == "uv run python experiments/linearisation_error_bound/run.py"
    assert len(payload["refusals"]) == 3
    questions = " ".join(entry["question"] for entry in payload["refusals"])
    for phrase in ("plausible", "multi-factor", "zero-volatility"):
        assert phrase in questions, f"a refusal is missing for {phrase!r}"
    assert "oracles" in payload and "none used" in payload["oracles"]["tool"]
    for key in ("proof", "regularity", "sharp_inclusion", "closed_forms"):
        assert key in payload["proposition"], f"the artifact does not state its own {key}"
    assert str(REPO_ROOT) not in json.dumps(payload), "a machine path leaked into the artifact"
    assert {row["direction"] for row in payload["rows"]} == {"up", "down"}


def test_a_recomputed_remainder_matches_the_frozen_curve() -> None:
    """Recompute the map's error here, from the core, and compare to the committed CSV.

    Without this, every other test in the module could pass while the analysis was bound to a
    different book than the one `experiments/stress_testing` published -- the two scripts share no
    code, so nothing but a re-derivation ties them together.
    """
    committed = (
        {float(row["move"]): row for row in csv.DictReader(CSV_PATH.read_text().splitlines())}
        if CSV_PATH.exists()
        else {}
    )
    assert committed, "the bound experiment's own CSV is missing"
    stress = list(
        csv.DictReader(
            (REPO_ROOT / "experiments" / "stress_testing" / "results" / "linearisation_error.csv")
            .read_text(encoding="utf-8")
            .splitlines()
        )
    )
    for row in stress:
        move = float(row["move"])
        delta = -move
        shift = SPOT * delta
        delta_dollars, gamma_dollars = _greeks(SPOT)
        mapped = delta_dollars * shift + 0.5 * gamma_dollars * shift * shift
        exact = _book_value(SPOT * (1.0 + delta)) - _book_value(SPOT)
        assert mapped - exact == pytest.approx(float(row["abs_error"]), rel=0.0, abs=1e-9), (
            f"at a {move:.1%} down move the recomputed remainder is "
            f"{mapped - exact!r}, not the published {row['abs_error']!r}"
        )
        if move in {float(key) for key in committed}:
            here = float(
                next(
                    r["remainder_signed"]
                    for r in _payload()["rows"]
                    if r["direction"] == "down" and abs(r["move"] - move) < 1e-12
                )
            )
            # The bound artifact reports R = exact - mapped, the sign under which Taylor's theorem
            # reads with a plus; the stress CSV stores mapped - revalued. Negating one side is the
            # whole relationship between the two artifacts, and getting it wrong here would compare
            # the paper against twice the error.
            assert here == pytest.approx(exact - mapped, rel=0.0, abs=1e-9)


NOTE_PATH = REPO_ROOT / "docs" / "analysis" / "delta_gamma_error_bound.md"
STRESS_CSV = REPO_ROOT / "experiments" / "stress_testing" / "results" / "linearisation_error.csv"


def _note_text() -> str:
    """The note, with the two typographic substitutions that are not numbers.

    Prose sets a minus as `U+2212` and an arrow as `U+2192`; the artifact prints ASCII. Normalising
    both keeps this a check on digits, which are the part that can go stale, rather than on type.
    """
    return NOTE_PATH.read_text(encoding="utf-8").replace("\u2212", "-").replace("\u2192", "->")


def test_every_figure_the_note_quotes_is_owned_by_the_artifact() -> None:
    """`docs/analysis/delta_gamma_error_bound.md` states results, so each one needs an owner.

    Until this test existed the note was the only place several of these figures appeared, and that
    is how two defects survived in it: the cubic-crossing spot was quoted as `94.5456` with a
    `5.4544 %` move against the artifact's `94.5487` / `5.4513 %`, and the headline fitted slope was
    quoted as `2.996188` with standard error `0.044006` -- a pooled 6-point fit that the experiment
    does not compute, so nothing in the tree owned it and nothing could notice it going stale. Both
    are recorded in `docs/integrity_audit.md` finding 32 and `docs/limitations.md` #77.

    The assertion is deliberately not "the digit string appears somewhere": each expected value is
    formatted the way the note formats it, so a re-run that moves a figure fails here instead of
    leaving the prose behind.
    """
    payload = _payload()
    headline = payload["headline"]
    windows = payload["asymptotics"]["slope_windows"]
    text = _note_text()

    def fmt(value: float, places: int) -> str:
        return f"{value:.{places}f}"

    expected = {
        "widest down slope": fmt(windows["down"][0]["slope"], 6),
        "widest down standard error": fmt(windows["down"][0]["standard_error"], 6),
        "widest up slope": fmt(windows["up"][0]["slope"], 6),
        "down convergence sequence": " ".join(
            "-> " + fmt(point["slope"], 6) for point in windows["down"][1:]
        ),
        "up convergence sequence": " ".join(
            "-> " + fmt(point["slope"], 6) for point in windows["up"][1:]
        ),
        "crossing spot": fmt(headline["aggregate_speed_crosses_zero_at_spot"], 4),
        "crossing move percent": fmt(100 * headline["aggregate_speed_crosses_zero_at_move"], 4),
        "predicted remainder zero percent": fmt(
            100 * headline["predicted_remainder_zero_at_move"], 4
        ),
        "leading term error percent": fmt(
            100 * headline["leading_term_relative_error_at_smallest_move"], 2
        ),
        "base book speed": fmt(headline["book_speed_at_base_spot"], 4),
        "bound loosest ratio": fmt(headline["bound_loosest_ratio"], 4),
        "bound tightest ratio": fmt(
            headline["bound_tightest_ratio_away_from_the_remainder_zero"], 4
        ),
        "bound collapse ratio": fmt(headline["bound_ratio_collapses_near_the_remainder_zero"], 4),
    }
    for label, value in expected.items():
        assert value in text, f"the note does not print {label} as {value!r}"

    down_sequence = " -> ".join(fmt(point["slope"], 6) for point in windows["down"])
    assert down_sequence in text, (
        f"the note does not print the down window sequence {down_sequence}"
    )

    # The two `abs_error` figures the note quotes come from a different artifact, written a phase
    # earlier by different code, and quoting them is the whole point of the prediction check.
    with STRESS_CSV.open(encoding="utf-8") as handle:
        rows = {float(row["move"]): float(row["abs_error"]) for row in csv.DictReader(handle)}
    assert fmt(-rows[0.2], 4) in text, f"the note does not print the 20 % abs_error {rows[0.2]!r}"
    assert f"{rows[0.3]:,.4f}" in text, f"the note does not print the 30 % abs_error {rows[0.3]!r}"
    assert fmt(abs(rows[0.1]), 1) in text, (
        f"the note does not print the 10 % abs_error {rows[0.1]!r}"
    )


def test_the_note_guard_is_not_vacuous() -> None:
    """The owner check has to fail when a figure moves, or it is decoration.

    Probing the reader rather than the document keeps this honest: the formatted value the note
    prints is found, and the same value one digit apart is not. Finding the perturbed string would
    mean the check is matching a prefix rather than a figure.
    """
    text = _note_text()
    headline = _payload()["headline"]
    spot = headline["aggregate_speed_crosses_zero_at_spot"]
    live = f"{spot:.4f}"
    assert live in text
    assert f"{spot + 1e-4:.4f}" not in text, (
        "the reader matched a value the artifact does not publish"
    )
    sloped = f"{headline['bound_loosest_ratio']:.4f}"
    assert sloped in text
    assert f"{headline['bound_loosest_ratio'] + 1e-4:.4f}" not in text
