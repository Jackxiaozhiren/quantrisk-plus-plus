"""Phase 9: the research API and the CLI.

The claim under test is narrow and worth stating precisely: Python here is orchestration.
Every assertion below either checks that a facade returns *bit-identically* what the core
returns for the same inputs, or that the documented import forms resolve. A facade that
recomputed a price in Python could still match to 1e-12; matching exactly is the point.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import pytest
import quantrisk
from quantrisk import cli

# --- the spec's examples, verbatim -----------------------------------------


def test_the_readme_black_scholes_example_runs_as_written() -> None:
    """The README's printed value must be the value the code produces.

    The expected number is read out of `README.md` rather than duplicated here, because a
    second copy of a literal is a second thing that can go stale — and `docs/
    validation_protocol.md` §2 forbids transcribing an expected value in the first place.

    The comparison is in units of the last place, not bit-exact. Black-Scholes evaluates
    `log`, `exp` and the normal CDF, and those are libm implementations rather than ours:
    the same source gives 9.925053717274434 on macOS/AppleClang and 9.925053717274437 on
    Linux/glibc, 1.7 ULP apart. Demanding bit equality would pin the README to one vendor's
    math library, while demanding nothing at all would let the documented example drift.
    Eight ULP — about 1e-14 — is far tighter than any modelling tolerance and still
    comfortably above the observed platform spread.
    """
    from quantrisk import BlackScholes

    readme = (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8")
    documented = re.search(r"model\.call_price\(\)\s*#\s*([0-9.]+)", readme)
    assert documented, "README.md no longer prints a call_price() value"
    published = float(documented.group(1))

    model = BlackScholes(spot=100, strike=100, rate=0.04, vol=0.20, maturity=1.0)
    computed = model.call_price()
    ulp = math.ulp(published)
    assert abs(computed - published) <= 8.0 * ulp, (
        f"README says {published!r}, the build gives {computed!r} "
        f"({abs(computed - published) / ulp:.1f} ULP apart)"
    )
    greeks = model.greeks()
    assert greeks.delta > 0 and greeks.gamma > 0
    assert repr(model).startswith("BlackScholes(spot=100.0, strike=100.0")


def test_the_readme_monte_carlo_example_runs_as_written() -> None:
    from quantrisk import MonteCarloEngine

    engine = MonteCarloEngine(seed=42)
    result = engine.price_european_call(
        spot=100, strike=100, rate=0.04, vol=0.20, maturity=1.0, paths=50_000
    )
    assert result.price > 0
    assert result.seed == 42
    assert result.paths == 50_000


def test_the_named_module_imports_resolve() -> None:
    # PROJECT_SPEC.md §Phase 9 names these four import forms explicitly.
    from quantrisk.portfolio import PortfolioOptimizer  # noqa: F401
    from quantrisk.pricing import black_scholes  # noqa: F401

    # The re-exported core names must be reachable through the same path.
    from quantrisk.risk import (
        RiskEngine,  # noqa: F401
        historical_var,  # noqa: F401
    )
    from quantrisk.stress import (
        ScenarioEngine,  # noqa: F401
        run_scenario,  # noqa: F401
    )


# --- facades delegate, they do not compute ---------------------------------


def test_black_scholes_facade_is_bit_identical_to_the_core() -> None:
    model = quantrisk.BlackScholes(
        spot=100.0, strike=105.0, rate=0.03, vol=0.25, maturity=0.75, dividend_yield=0.01
    )
    direct = quantrisk.pricing.black_scholes(
        quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, 105.0),
        model.market,
    )
    assert model.call_price() == direct.price  # exactly, not approximately
    assert (
        model.greeks().delta
        == quantrisk.pricing.black_scholes_greeks(
            quantrisk.pricing.EuropeanOption(quantrisk.pricing.OptionType.CALL, 105.0),
            model.market,
        ).delta
    )


def test_monte_carlo_facade_matches_the_core_call_exactly() -> None:
    """`price_european_call` is the spec's name for the core's `price_call`.

    Same seed, same paths, bit-identical result: the facade renamed and reshaped the
    arguments and did nothing else.
    """
    engine = quantrisk.MonteCarloEngine(seed=99)
    via_facade = engine.price_european_call(
        spot=80.0, strike=100.0, rate=0.05, vol=0.30, maturity=0.5, paths=25_000
    )
    via_core = quantrisk.monte_carlo.MonteCarloEngine(seed=99).price_call(
        quantrisk.pricing.MarketParams(spot=80.0, rate=0.05, volatility=0.30, maturity=0.5),
        100.0,
        25_000,
    )
    assert via_facade.price == via_core.price
    assert via_facade.standard_error == via_core.standard_error
    assert via_facade.confidence_low == via_core.confidence_low


def test_portfolio_optimizer_accepts_flat_or_nested_covariance_identically() -> None:
    flat = [0.04, 0.012, 0.012, 0.09]
    nested = [[0.04, 0.012], [0.012, 0.09]]
    first = quantrisk.PortfolioOptimizer(flat, [0.06, 0.09]).minimum_variance()
    second = quantrisk.PortfolioOptimizer(nested, [0.06, 0.09]).minimum_variance()
    assert first.weights == second.weights
    assert first.variance == second.variance


def test_portfolio_optimizer_rejects_a_non_square_flat_covariance() -> None:
    with pytest.raises(ValueError, match="do not form a square matrix"):
        quantrisk.PortfolioOptimizer([0.04, 0.012, 0.012])


def test_risk_engine_reports_the_frozen_loss_convention_in_its_repr() -> None:
    rng = quantrisk.Rng(seed=3)
    engine = quantrisk.RiskEngine([rng.standard_normal() * 0.01 for _ in range(500)])
    assert "L = -R" in repr(engine)
    with pytest.raises(ValueError, match="at least one return"):
        quantrisk.RiskEngine([])


def test_scenario_engine_validates_the_book_on_construction() -> None:
    factors = quantrisk.stress.FactorSet()
    factors.factors = [
        quantrisk.stress.RiskFactor(
            "SPX", quantrisk.stress.FactorClass.equity_index, 100.0, "points"
        ),
        quantrisk.stress.RiskFactor("RATE", quantrisk.stress.FactorClass.rate, 0.05, "decimal"),
    ]
    book = quantrisk.stress.Portfolio()
    book.factors = factors
    position = quantrisk.stress.Position()
    position.name = "broken"
    exposures = quantrisk.stress.ExposureVector()
    exposures.delta = [1.0e6]  # one entry against a two-factor set
    position.exposures = exposures
    book.positions = [position]
    with pytest.raises(quantrisk.ValidationError):
        quantrisk.ScenarioEngine(book)


# --- module surface --------------------------------------------------------


def test_quantrisk_does_not_import_the_optional_data_layer() -> None:
    """`quantrisk.data` reaches the network, so importing the core must not pull it in.

    Checked in a fresh interpreter rather than against the current one: by the time this
    module runs, other tests may already have imported the data layer, and a check that
    passes only because of test ordering is worth nothing.
    """
    import subprocess
    import sys

    probe = (
        "import sys, quantrisk; "
        "print('quantrisk.data' in sys.modules, 'quantrisk.data.http' in sys.modules)"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True, timeout=120
    )
    assert result.stdout.strip() == "False False", (
        "importing quantrisk pulled in the optional data layer: " + result.stdout
    )


def test_every_declared_export_exists() -> None:
    missing = [name for name in quantrisk.__all__ if not hasattr(quantrisk, name)]
    assert not missing, f"__all__ promises {missing}"


def test_each_submodule_names_the_extension_it_re_exports() -> None:
    for name in (
        "stats",
        "special",
        "stochastic",
        "monte_carlo",
        "pricing",
        "risk",
        "portfolio",
        "stress",
    ):
        module = getattr(quantrisk, name)
        core = getattr(quantrisk._quantrisk, name)
        assert module.__core__ is core, f"quantrisk.{name} is not backed by the extension"


# --- CLI -------------------------------------------------------------------


def test_cli_validate_passes_and_exits_zero(capsys) -> None:
    assert cli.main(["validate"]) == 0
    printed = capsys.readouterr().out
    assert "checks passed" in printed
    assert "FAIL" not in printed


def test_cli_validate_json_is_machine_readable(capsys) -> None:
    assert cli.main(["validate", "--json"]) == 0
    printed = capsys.readouterr().out
    payload = json.loads(printed[printed.index("{") :])
    assert payload["command"] == "validate"
    assert payload["version"] == quantrisk.version()
    assert all("passed" in check for check in payload["checks"])
    assert len(payload["checks"]) >= 7


def test_cli_demo_runs_every_documented_example(capsys) -> None:
    assert cli.main(["demo"]) == 0
    printed = capsys.readouterr().out
    for section in ("Black-Scholes", "Monte Carlo", "Portfolio", "Risk", "Stress"):
        assert section in printed
    # The stress section must show attribution, not just a total: that is the spec's gate.
    assert "attribution residual" in printed


def test_cli_benchmark_reports_measured_numbers(capsys) -> None:
    assert cli.main(["benchmark", "--iterations", "200"]) == 0
    printed = capsys.readouterr().out
    assert "us/call" in printed
    # A benchmark that printed a cached or hard-coded figure would not say where it ran.
    assert "measured timings" in printed


_RUN_ROW = re.compile(r"^  (\S+)\s+(\S+)\s+(\S+)$")


def _cli(argv: list[str], capsys) -> tuple[int, str, str]:
    """Run the CLI and hand back its exit code, stdout and stderr as one call.

    Reading both streams here rather than at the call site matters: a test that asked for stdout
    first would leave nothing for the stderr assertion afterwards.
    """
    code = cli.main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_cli_run_lists_every_registered_task_and_the_package_agrees(capsys) -> None:
    """`run --list` and the filesystem are two independent enumerations of one set.

    The listing comes from the registry; the expected modules come from globbing the package for the
    two shapes a runnable unit has -- `experiments/<dir>/__main__.py` and
    `benchmarks/<suite>/<name>.py`. Neither side reads the other, so a registry entry whose module
    was never shipped and a shipped unit the registry forgot both fail here. That is the L5 parity
    question asked through the installed surface, where a missing entry would actually be felt.
    """
    code, printed, _err = _cli(["run", "--list"], capsys)
    assert code == 0
    listed = [
        (match.group(1), match.group(2), match.group(3))
        for line in printed.splitlines()
        if (match := _RUN_ROW.match(line))
    ]
    assert len(listed) >= 19, f"only {len(listed)} rows parsed out of `run --list`"
    assert len(listed) == len({row[0] for row in listed}), "a task id is listed twice"

    root = Path(cli.__file__).resolve().parents[2]
    package = root / "python" / "quantrisk"
    on_disk = sorted(
        {
            # A study is a package whose `__main__.py` is what `-m` executes, so the module is its
            # directory; a benchmark is a single module file.
            f"quantrisk.{'.'.join(path.relative_to(package).parts[:-1])}"
            if path.name == "__main__.py"
            else f"quantrisk.{'.'.join(path.relative_to(package).parts).removesuffix('.py')}"
            for pattern in ("experiments/*/__main__.py", "benchmarks/*/*.py")
            for path in package.glob(pattern)
            if "__pycache__" not in path.parts
        }
    )
    assert on_disk, "the filesystem walk found no runnable unit, so this comparison proves nothing"
    listed_modules = sorted(row[1] for row in listed)
    assert listed_modules == on_disk, (
        f"the registry lists {len(listed_modules)} modules, the package holds {len(on_disk)}; "
        f"they disagree on {sorted(set(listed_modules) ^ set(on_disk))}"
    )
    assert f"{len(listed)} registered tasks" in printed, (
        "the summary line does not count its own rows"
    )


def test_cli_run_executes_a_task_into_the_root_it_is_given(capsys, tmp_path) -> None:
    """D6's other half: a study runs from the installed surface and writes where it is told.

    The module is resolved through the interpreter (`runpy`), not through a file beside the CLI,
    which is the only thing that works against a wheel with no checkout. The artifact's recorded
    command is asserted too: a `run` that executed some other program would still exit 0.
    """
    code, printed, err = _cli(["run", "pricing_grid", "--out", str(tmp_path)], capsys)
    assert code == 0, (printed[-800:], err[-800:])
    assert "PASS  pricing_grid" in printed, printed[-400:]
    landing = tmp_path / "experiments" / "pricing_validation" / "results" / "summary.json"
    assert landing.is_file(), f"the study reported PASS but wrote no {landing}"
    payload = json.loads(landing.read_text(encoding="utf-8"))
    assert payload["command"] == "uv run python -m quantrisk.experiments.pricing_validation", (
        payload["command"]
    )


def test_cli_run_distinguishes_a_typo_from_a_bare_run(capsys) -> None:
    """Both are rejected arguments (exit 2), but they are different facts and say different things.

    Neither may look like a study that failed -- that would be exit 1 -- and a single shared message
    would tell a reader who already passed `--list` to consult `--list`.
    """
    code, _out, err = _cli(["run", "no_such_task_anywhere"], capsys)
    assert code == 2
    assert "no registered task" in err, err

    code, _out, err = _cli(["run"], capsys)
    assert code == 2
    assert "name a task" in err, err


def test_cli_pre_existing_command_outputs_kept_their_contracts_when_run_landed(capsys) -> None:
    """D6 requires the earlier commands to be unchanged; this pins that rather than trusting it.

    Each fingerprint is taken over the printed text with the measured part folded away -- every
    digit run becomes `#`, and runs of spaces become one -- so what is pinned is the contract (every
    line, its wording, its order) and not this machine's arithmetic. The space fold is load-bearing:
    `benchmark` right-aligns its timings, so a number gaining an integer digit shifts a pad space,
    and without the fold the same unchanged build fingerprints twice. The digests were measured when
    `run` was added.

    The command *set* is read out of the parser's own usage line rather than from a list written
    here, so a fifth subcommand can only land by changing the surface the documents describe.
    """
    usage = cli.build_parser().format_usage()
    named = re.search(r"\{([a-z,]+)\}", usage)
    assert named, f"the usage line names no subcommand set: {usage!r}"
    assert set(named.group(1).split(",")) == {"validate", "benchmark", "demo", "run"}, usage
    expected = {
        ("validate",): "82047dafac7aa0a5",
        ("validate", "--json"): "69068e3ccf816cda",
        ("demo",): "2a7bb172d846b2c3",
        ("benchmark", "--iterations", "2"): "64fbd3b57b61a6ab",
    }
    for argv, digest in expected.items():
        code, printed, _err = _cli(list(argv), capsys)
        assert code == 0, f"`quantrisk {' '.join(argv)}` exited {code}"
        folded = re.sub(r"[ \t]+", " ", re.sub(r"\d+(?:\.\d+)?(?:e-?\d+)?", "#", printed))
        assert hashlib.sha256(folded.encode("utf-8")).hexdigest()[:16] == digest, (
            f"`quantrisk {' '.join(argv)}` changed shape; D6 says the pre-existing subcommands "
            "keep their output contracts byte-for-byte, so this needs a stated reason"
        )


def test_cli_requires_a_subcommand() -> None:
    with pytest.raises(SystemExit) as exit_info:
        cli.main([])
    assert exit_info.value.code != 0


def test_cli_distinguishes_a_failed_check_from_a_rejected_input(monkeypatch) -> None:
    # Exit 1 means "a claim about the library did not hold"; exit 2 means "the request
    # itself was invalid". Collapsing them would make a typo look like a regression.
    def reject(_arguments):
        raise quantrisk.ValidationError("bad input")

    monkeypatch.setattr(cli, "command_demo", reject)
    assert cli.main(["demo"]) == 2

    def fail(_arguments):
        return 1

    monkeypatch.setattr(cli, "command_demo", fail)
    assert cli.main(["demo"]) == 1


def test_cli_rejects_an_unparseable_argument() -> None:
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["benchmark", "--iterations", "not-a-number"])
    assert exit_info.value.code == 2


def test_the_readme_quickstart_transcript_is_what_the_build_prints() -> None:
    """Every `#` value in the README's 30-second example is a claim about the imported library.

    The version line was the one that decayed: it read `'1.2.0'` through two releases, because
    nothing executed it. The seeded calls below are our own generator rather than libm, so they
    are compared exactly — no ULP allowance is needed, and asking for one would hide a real change.
    """
    readme = (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8")

    def documented(pattern: str, label: str) -> str:
        found = re.search(pattern, readme)
        assert found, f"README.md no longer prints a {label} value"
        return found.group(1)

    assert documented(r"quantrisk\.version\(\)\s*#\s*'([^']+)'", "version") == quantrisk.version()
    assert documented(r"quantrisk\.normal_cdf\(0\.0\)\s*#\s*([0-9.]+)", "normal_cdf") == repr(
        quantrisk.normal_cdf(0.0)
    )
    rng = quantrisk.Rng(seed=42)
    assert documented(r"rng\.uniform01\(\)\s*#\s*([0-9.]+)", "uniform01") == repr(
        rng.uniform01()
    ), "the seeded uniform in the README is not what seed 42 gives"
    assert documented(r"rng\.standard_normal\(\)\s*#\s*([0-9.]+)", "standard_normal") == repr(
        rng.standard_normal()
    ), "the seeded normal in the README is not what seed 42 gives"
