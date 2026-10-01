"""The compiled extension must expose the surface the bindings declare.

Two defects of this phase are of the kind only a machine keeps catching. An editable reinstall
served from a wheel cache left the *new* functions absent from the imported module, and a stale
in-tree `.so` made a test import a binary older than the source it was checking (limitation #70,
`docs/reproducibility.md`). Both present as an attribute that does not exist, which reads as "the
binding is wrong" rather than "I am importing yesterday's build" -- and no other gate here sees
them, because the C++ tests run against the build directory while pytest imports whatever the
interpreter resolved.

So this file treats `bindings/python_bindings.cpp` as the contract and the imported extension as
the evidence, and compares them in both directions: a declared name missing from the binary means
the binary is stale or the registration never ran, and a binary name missing from the source means
the installed build carries API the repository no longer declares.

The parser is structural rather than a substring scan. The bindings file registers one object per
statement, each statement begins at an indent of exactly four spaces and ends with `;`, and
clang-format enforces that shape -- CI fails a tree without it, which is what makes reading it
safe. Names are collected from inside each statement, so a declaration the formatter split across
lines is still attributed to its object.

Two ways the first version of this parser was wrong are kept as tests below: a section comment at
the same indent as a declaration swallowed the registration after it, and a doc string containing
`[0, 1)` contributed a closing parenthesis that never opened, merging one statement into the next.
"""

from __future__ import annotations

import re
import types
from collections.abc import Iterable
from pathlib import Path

from quantrisk import _quantrisk

REPO_ROOT = Path(__file__).resolve().parents[2]
BINDINGS = REPO_ROOT / "bindings" / "python_bindings.cpp"

CLASS_HEAD = re.compile(r'^py::(?:class_|enum_)<.+?>\(\s*(\w+)\s*,\s*"(\w+)"')
FUNCTION_HEAD = re.compile(r'^(\w+)\s*\.def\(\s*"(\w+)"')
# pybind writes a class's members as a chain of `.def(...)`, `.def_readwrite(...)`,
# `.def_property_readonly(...)` and, for enums, `.value(...)`. Each names one visible attribute.
MEMBER = re.compile(r'\.(?:def(?:_readonly|_readwrite|_property(?:_readonly)?)?|value)\(\s*"(\w+)"')
FUNCTION_DEF = re.compile(r'\.def\(\s*"(\w+)"')
STRING_LITERAL = re.compile(r'"(?:[^"\\]|\\.)*"')
# pybind adds `name` and `value` to every enum, and internals like `_pybind11_conduit_v1_` to
# every class. Neither is API, and neither belongs in a comparison against the source.
ENUM_AUTOATTRS = frozenset({"name", "value"})


def _code_only(text: str) -> str:
    """Drop string literals, whose parentheses are not code.

    `"Next uniform variate in [0, 1)."` is real text in this file. Counting its bracket as a
    closing paren ends one statement early and attributes the next declaration to the wrong class,
    which is how `stats.mean` came to be read as a member of `Rng`.
    """
    return STRING_LITERAL.sub('""', text)


def _statements(source: str) -> list[str]:
    """One entry per top-level registration statement, folded onto a single line."""
    statements: list[str] = []
    current: list[str] = []
    for line in source.splitlines():
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 4 and not current:
            # Section comments sit at the same indent as a declaration. Dropping them here keeps a
            # comment from becoming the head of the statement that follows it, which would hide the
            # registration from `_declared`.
            if stripped.startswith(("//", "/*")):
                continue
            current = [stripped]
        elif not current:
            continue
        else:
            current.append(stripped)
        joined = " ".join(current)
        code = _code_only(joined)
        if code.count("(") == code.count(")") and code.rstrip().endswith(";"):
            statements.append(joined)
            current = []
    return statements


def _declared(
    statements: Iterable[str],
) -> tuple[dict[str, set[str]], dict[str, dict[str, set[str]]], set[tuple[str, str]]]:
    """`(functions, classes, enums)` -- what the source says the binary should expose.

    Enums come back separately because pybind gives every one two attributes, `name` and `value`,
    that no source line declares; treating those as drift would flag the whole enum surface.
    """
    functions: dict[str, set[str]] = {}
    classes: dict[str, dict[str, set[str]]] = {}
    enums: set[tuple[str, str]] = set()
    for statement in statements:
        head = CLASS_HEAD.match(statement)
        if head:
            target, name = head.groups()
            classes.setdefault(target, {})[name] = set(MEMBER.findall(statement))
            if statement.startswith("py::enum_"):
                enums.add((target, name))
            continue
        head = FUNCTION_HEAD.match(statement)
        if head:
            target = head.group(1)
            # One statement can chain several functions onto the same submodule, so its head line
            # names only the first of them.
            functions.setdefault(target, set()).update(FUNCTION_DEF.findall(statement))
    return functions, classes, enums


def _live_modules(root: types.ModuleType) -> dict[str, types.ModuleType]:
    """Every pybind submodule reachable from the extension, keyed by its declared target name."""
    found: dict[str, types.ModuleType] = {"module": root}
    stack: list[types.ModuleType] = [root]
    while stack:
        module = stack.pop()
        for attribute in dir(module):
            if attribute.startswith("_"):
                continue
            value = getattr(module, attribute)
            if isinstance(value, types.ModuleType):
                stack.append(value)
                found[attribute] = value
    return found


def _live_surface() -> tuple[dict[str, set[str]], dict[str, dict[str, set[str]]]]:
    """What the imported extension actually exposes, in the same shape as `_declared`.

    Class members are the unfiltered `dir()`, because a declared `__repr__` has to be findable in
    the binary; the reverse comparison drops leading-underscore names itself.
    """
    functions: dict[str, set[str]] = {}
    classes: dict[str, dict[str, set[str]]] = {}
    for target, module in _live_modules(_quantrisk).items():
        callable_names: set[str] = set()
        class_names: dict[str, set[str]] = {}
        for name in sorted(n for n in dir(module) if not n.startswith("_")):
            value = getattr(module, name)
            if isinstance(value, types.ModuleType):
                continue  # a submodule is addressed under its own target key
            if isinstance(value, type):
                class_names[name] = set(dir(value))
            elif callable(value):
                callable_names.add(name)
        functions[target] = callable_names
        classes[target] = class_names
    return functions, classes


def _compare(
    declared_functions: dict[str, set[str]],
    declared_classes: dict[str, dict[str, set[str]]],
    declared_enums: set[tuple[str, str]],
    live_functions: dict[str, set[str]],
    live_classes: dict[str, dict[str, set[str]]],
) -> list[str]:
    """Differences in both directions as `target.name` strings. Pure, so it can be probed."""
    problems: list[str] = []
    for target, names in declared_functions.items():
        live = live_functions.get(target)
        if live is None:
            problems.append(f"{target} (declared submodule is not in the binary)")
            continue
        problems += [f"{target}.{name} (declared, absent from the binary)" for name in names - live]
    for target, live in live_functions.items():
        problems += [
            f"{target}.{name} (in the binary, not declared by the source)"
            for name in live - declared_functions.get(target, set())
        ]
    for target, by_class in declared_classes.items():
        live_here = live_classes.get(target, {})
        for name, members in by_class.items():
            live_members = live_here.get(name)
            if live_members is None:
                problems.append(f"{target}.{name} (declared, absent from the binary)")
                continue
            problems += [
                f"{target}.{name}.{member} (declared, absent from the binary)"
                for member in members - live_members
            ]
            public = {member for member in live_members if not member.startswith("_")}
            if (target, name) in declared_enums:
                public -= ENUM_AUTOATTRS
            problems += [
                f"{target}.{name}.{member} (in the binary, not declared by the source)"
                for member in public - members
            ]
    return sorted(problems)


def _problems() -> list[str]:
    """The declared surface against the binary's surface, in both directions."""
    functions, classes, enums = _declared(_statements(BINDINGS.read_text(encoding="utf-8")))
    live_functions, live_classes = _live_surface()
    return _compare(functions, classes, enums, live_functions, live_classes)


def test_every_name_the_bindings_declare_is_exposed_by_the_binary() -> None:
    """A stale `.so` is a build fact, so it has to fail a test, not surprise a researcher."""
    problems = [problem for problem in _problems() if "absent from the binary" in problem]
    assert not problems, (
        "the installed extension does not match bindings/python_bindings.cpp -- this is the "
        "stale-build signature of docs/reproducibility.md, not a missing binding:\n"
        + "\n".join(problems)
    )


def test_the_binary_exposes_nothing_the_bindings_do_not_declare() -> None:
    """The other direction: a binary with API the source dropped is not the repository either."""
    problems = [problem for problem in _problems() if "not declared by the source" in problem]
    assert not problems, "the extension carries names the source no longer declares:\n" + "\n".join(
        problems
    )


def test_the_parser_recognises_the_surface_it_claims_to_have_read() -> None:
    """A parser that silently matched nothing would pass both checks above; counts say it did."""
    statements = _statements(BINDINGS.read_text(encoding="utf-8"))
    functions, classes, enums = _declared(statements)
    assert len(statements) > 100, f"the split found {len(statements)} statements, expected ~150"
    assert sum(len(names) for names in functions.values()) >= 60, functions
    members = sum(len(by) for by_class in classes.values() for by in by_class.values())
    assert members >= 250, members
    assert len([name for by_class in classes.values() for name in by_class]) >= 40
    assert enums, "no enum was recognised, so pybind's automatic members would read as drift"

    # The newest API in the tree must be visible, or the extractor has drifted from the file shape.
    assert {"vanna", "volga"} <= classes["pricing"]["VolCrossDerivatives"]
    third = {"spot_spot_sigma", "spot_sigma_sigma", "sigma_sigma_sigma"}
    assert third <= classes["pricing"]["MixedThirdDerivatives"]
    fourth = {
        "spot_spot_spot_sigma",
        "spot_spot_sigma_sigma",
        "spot_sigma_sigma_sigma",
        "sigma_sigma_sigma_sigma",
    }
    assert fourth <= classes["pricing"]["MixedFourthDerivatives"]
    assert "black_scholes_vol_cross_derivatives" in functions["pricing"]
    assert "black_scholes_mixed_third_derivatives" in functions["pricing"]
    assert "black_scholes_mixed_fourth_derivatives" in functions["pricing"]


def test_the_statement_split_follows_a_declaration_the_formatter_broke() -> None:
    """The failure modes this replaces: a wrapped receiver, a comment head, a bracket in prose."""
    source = (
        '    py::module_ stats = module.def_submodule("stats", "Statistics helpers");\n'
        "    // statistics follow\n"
        "    stats\n"
        '        .def("mean_of", &quantrisk::stats::mean_of, py::arg("data"),\n'
        '             "Mean, in units of [0, 1).");\n'
        '    py::class_<quantrisk::Thing>(stats, "Thing")\n'
        "        .def(py::init<>())\n"
        '        .def("value", &quantrisk::Thing::value, "The value.")\n'
        '        .def_readwrite("size", &quantrisk::Thing::size);\n'
    )
    functions, classes, enums = _declared(_statements(source))
    assert functions == {"stats": {"mean_of"}}, functions
    assert classes == {"stats": {"Thing": {"value", "size"}}}, classes
    assert enums == set()


def test_a_stale_binary_reads_as_a_missing_name_not_as_extra_api() -> None:
    """The signature this guard exists for, exercised without waiting for a bad build.

    An editable reinstall served from cache leaves the *newest* registrations absent from the
    imported module while the source declares them (limitation #70). Removing one name from the
    live surface proves the comparator calls that "declared, absent from the binary" rather than
    the reverse drift, which is what makes the first two tests more than a tautology.
    """
    functions, classes, enums = _declared(_statements(BINDINGS.read_text(encoding="utf-8")))
    live_functions, live_classes = _live_surface()
    live_functions["pricing"].discard("black_scholes_vol_cross_derivatives")
    problems = _compare(functions, classes, enums, live_functions, live_classes)
    expected = "pricing.black_scholes_vol_cross_derivatives (declared, absent from the binary)"
    assert expected in problems
    assert not [problem for problem in problems if "not declared by the source" in problem]


def test_the_comparator_reports_a_name_missing_from_either_side() -> None:
    """Negative controls: the diff must fire on both drift directions, and rest on agreement."""
    declared_functions = {"pricing": {"price", "greeks"}}
    declared_classes = {"pricing": {"Greeks": {"delta", "vega"}, "Kind": {"CALL", "PUT"}}}
    enums = {("pricing", "Kind")}
    agreed = {
        "pricing": {
            "Greeks": {"delta", "vega"},
            # `name` and `value` arrive with every enum; they are not API the source forgot.
            "Kind": {"CALL", "PUT", "name", "value"},
        }
    }
    assert _compare(declared_functions, declared_classes, enums, declared_functions, agreed) == []

    missing_binary = _compare(
        declared_functions,
        declared_classes,
        enums,
        {"pricing": {"price"}},
        {"pricing": {"Greeks": {"delta"}, "Kind": {"CALL", "PUT"}}},
    )
    assert "pricing.greeks (declared, absent from the binary)" in missing_binary
    assert "pricing.Greeks.vega (declared, absent from the binary)" in missing_binary

    stale_binary = _compare(
        {"pricing": {"price"}},
        {"pricing": {"Greeks": {"delta"}}},
        set(),
        declared_functions,
        {"pricing": {"Greeks": {"delta", "vanna", "__repr__"}, "Kind": {"CALL", "PUT"}}},
    )
    assert "pricing.greeks (in the binary, not declared by the source)" in stale_binary
    assert "pricing.Greeks.vanna (in the binary, not declared by the source)" in stale_binary
    assert not [problem for problem in stale_binary if "__repr__" in problem], (
        "a dunder is pybind's own, not drift"
    )
