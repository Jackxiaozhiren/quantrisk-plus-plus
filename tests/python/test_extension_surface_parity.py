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

A third direction was added for audit finding 43, because the two above cannot see its defect. Both
read the bindings file, so a function that was never registered is invisible: source and binary
agree on its absence. The header is the only place that knows the function exists. So the last
section of this file reads `cpp/include/quantrisk/**/*.hpp` and claims that every function the core
marks `[[nodiscard]]` -- the core's own way of saying `this result is the point of calling` -- is
either registered in the bindings or disclaimed at its declaration by a `// python:` marker. A
disclaimer is a checkable claim, not prose: `via X` has to name something the bindings really
declare, a marker left on a function that is in fact bound is stale, and a marker above nothing is
orphaned. Each of those three failure modes is planted in a test, as is the shape finding 43
describes -- a new core function that reaches neither a binding nor a marker.
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


# --- the third direction: what the core declares has to be reachable, or say otherwise --

HEADER_ROOT = REPO_ROOT / "cpp" / "include" / "quantrisk"
MARKER_HEAD = "// python:"
MARKER = re.compile(
    r"^// python: (?:internal|via `?(?P<route>[A-Za-z_][\w.]*)`?) -- (?P<reason>\S.*)$"
)
CLASS_LIKE = re.compile(r"\b(?:class|struct|enum|union)\b")
DECLARATION_STATEMENT = re.compile(r"\b([a-z_][a-z_0-9]*)\s*\([^()]*\)\s*(?:const\s*)?;")
NON_DECLARATIONS = frozenset(
    {
        "static_assert",
        "noexcept",
        "return",
        "if",
        "for",
        "while",
        "switch",
        "sizeof",
        "and",
        "not",
        "or",
    }
)
ATTRIBUTE = "[[nodiscard]]"


def _masked(text: str) -> str:
    """Comments and literals blanked to spaces, newlines and every offset preserved.

    The offsets have to survive because the line number each declaration is reported at is the
    reader's address for fixing it, and this file's own first parser learned that a bracket inside a
    string literal ends a statement early.

    One scanner rather than three regex passes, because the two hide each other. A doc comment
    quoting `("speed")` is prose, and a pass that looks for string literals first pairs that quote
    with the next one several lines down and erases real declarations with it; a pass that looks for
    `//` first does the same to a literal containing `https://`. The scanner takes the decision in
    reading order, which is the only order in which it is well defined.
    """
    out = list(text)
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if text.startswith("//", index):
            end = text.find("\n", index)
            end = length if end == -1 else end
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            end = length if end == -1 else end + 2
        elif char in ('"', "'"):
            end = index + 1
            while end < length:
                if text[end] == "\\":
                    end += 2
                    continue
                if text[end] == char:
                    end += 1
                    break
                end += 1
        else:
            index += 1
            continue
        for position in range(index, min(end, length)):
            if out[position] != "\n":
                out[position] = " "
        index = end
    return "".join(out)


def _marker_above(lines: list[str], attribute_index: int) -> tuple[str | None, int | None]:
    """The `// python:` line governing a declaration, and the line it sits on.

    Doc comments (`///`) are traversed, because a declaration's own documentation always stands
    between the marker and the attribute; a blank line or a line of code ends the walk, so a marker
    cannot drift onto an unrelated declaration below it.
    """
    marker: str | None = None
    at: int | None = None
    cursor = attribute_index - 1
    while cursor >= 0:
        stripped = lines[cursor].strip()
        if not stripped.startswith("//"):
            break
        if stripped.startswith(MARKER_HEAD):
            marker, at = stripped, cursor + 1
        cursor -= 1
    return marker, at


def _namespace_view(text: str) -> str:
    """Comments, literals and every brace-delimited body blanked, offsets and lines intact.

    One owner for the scope question, because two scans have to answer it: the attribute scan below
    must not read a struct's `total()` as an entry point, and the inventory of what the claim does
    NOT cover has to count the same declarations. Both read this view rather than each keeping a
    stack.
    cover has to count the same declarations. Both read this view rather than each keeping a stack.

    A frame is transparent only when `namespace` opened it. A type body, a function body and an
    `if (...) {` are all opaque, which is what keeps `require_finite(value, name);` inside an inline
    definition from being read as a declaration of `require_finite`.
    """
    masked = _masked(text)
    out = list(masked)
    stack: list[str] = []
    pending = ""
    index = 0
    while index < len(masked):
        char = masked[index]
        if char == "{":
            if pending:
                stack.append(pending)
                pending = ""
            elif index and masked[index - 1] == ")":
                stack.append("body")
            else:
                stack.append("block")
            index += 1
            continue
        if char == "}":
            if stack:
                stack.pop()
            index += 1
            continue
        if masked.startswith("namespace", index) and (
            index == 0 or not masked[index - 1].isalnum()
        ):
            after = masked[index + 9 : index + 10]
            if not after.isalnum():
                pending = "ns"
                for position in range(index, index + 9):
                    out[position] = " "
                index += 9
                continue
        keyword = CLASS_LIKE.match(masked, index)
        if keyword and (index == 0 or not masked[index - 1].isalnum()):
            pending = "type"
            for position in range(index, keyword.end()):
                out[position] = " "
            index = keyword.end()
            continue
        if any(frame != "ns" for frame in stack) and char != "\n":
            out[index] = " "
        index += 1
    return "".join(out)


def _declarations(text: str) -> list[tuple[int, str, str | None, int | None]]:
    """`(line, name, marker, marker line)` for namespace-scope `[[nodiscard]]` declarations.

    The attribute is the anchor the core chose for itself -- `this result is the point of calling`
    -- so the claim is keyed on intent already written in the code rather than on a list assembled
    here. A declaration that reaches a `(` with no name, or a member function inside a type body,
    is not found here at all, which is what `_namespace_view` is for.
    """
    view = _namespace_view(text)
    lines = text.split("\n")
    found: list[tuple[int, str, str | None, int | None]] = []
    index = 0
    while True:
        index = view.find(ATTRIBUTE, index)
        if index == -1:
            return found
        head = view[index + len(ATTRIBUTE) : index + len(ATTRIBUTE) + 900]
        stop = len(head)
        for terminator in (";", "{"):
            at = head.find(terminator)
            if at != -1:
                stop = min(stop, at)
        names = re.findall(r"\b([a-z_][a-z_0-9]*)\s*\(", head[:stop])
        if names:
            line = view.count("\n", 0, index) + 1
            marker, marker_line = _marker_above(lines, line - 1)
            found.append((line, names[-1], marker, marker_line))
        index += len(ATTRIBUTE)


def _statement_head(view: str, name_start: int) -> int:
    """The offset a declaration's own statement begins at.

    Walking back to the previous newline is not enough, because these headers wrap: the core writes
    `[[nodiscard]] MixedThirdDerivatives` and the name on the next line, so a scan that started at
    the name's line read that declaration as unmarked. The real boundary is the previous statement
    (`;`, `}`, `{`) or the blank line that ends a comment block.
    """
    start = max(
        view.rfind(";", 0, name_start),
        view.rfind("}", 0, name_start),
        view.rfind("{", 0, name_start),
        view.rfind("\n\n", 0, name_start) + 1,
    )
    return start + 1 if view[start] != "\n" else start


def _unmarked_declarations(text: str) -> list[tuple[int, str, str | None, int | None]]:
    """Namespace-scope declarations the core did NOT mark `[[nodiscard]]`.

    Phase 17 inventoried these because the claim could not see them. Phase 19 marked every one of
    them -- a value returned by a numerical core is always the point of calling it -- so the list is
    now the uniformity check itself: it has to stay empty, and a new function written without the
    attribute lands here rather than in a caveat. Two shapes match a declaration's syntax without
    being one: a call qualified with `::`, and an initialiser, which is how `constexpr Real kEpsilon
    = std::numeric_limits<Real>::epsilon();` would otherwise read as a declaration of `epsilon`.
    """
    view = _namespace_view(text)
    lines = text.split("\n")
    found: list[tuple[int, str, str | None, int | None]] = []
    for match in DECLARATION_STATEMENT.finditer(view):
        name = match.group(1)
        qualified = view[max(0, match.start() - 2) : match.start()] == "::"
        if name in NON_DECLARATIONS or qualified:
            continue
        head = _statement_head(view, match.start())
        if "=" in view[head : match.start()] or ATTRIBUTE in view[head : match.start()]:
            continue
        line = view.count("\n", 0, head) + 1
        marker, marker_line = _marker_above(lines, line - 1)
        found.append((line, name, marker, marker_line))
    return found


def _core_surface() -> list[tuple[str, int, str, str | None, int | None]]:
    """Every namespace-scope function declaration in the core, keyed by the header it came from.

    Two scans, not one: the attribute scan reads what the core marked, and
    `_unmarked_declarations` reads what it did not. Phase 17 keyed the claim on `[[nodiscard]]`
    alone and inventoried the difference; Phase 19 marked the whole surface, so the population here
    is the surface, and an unmarked declaration is caught twice -- unreachable, and unmarked.
    """
    rows = []
    for header in sorted(HEADER_ROOT.rglob("*.hpp")):
        relative = str(header.relative_to(REPO_ROOT))
        text = header.read_text(encoding="utf-8")
        scanned = sorted(list(_declarations(text)) + list(_unmarked_declarations(text)))
        for line, name, marker, marker_line in scanned:
            rows.append((relative, line, name, marker, marker_line))
    return rows


def _route_declared(
    route: str, functions: dict[str, set[str]], classes: dict[str, dict[str, set[str]]]
) -> bool:
    """Whether the route an exemption names is really on the Python surface.

    `via X` claims a function; `via Class.member` claims a field of a bound struct. Either is a
    checkable fact, so the marker is a claim the guard can test rather than a sentence to trust.
    """
    if "." in route:
        class_name, member = route.split(".", 1)
        return any(
            class_name in by_class and member in by_class[class_name]
            for by_class in classes.values()
        )
    return route in set().union(*functions.values()) if functions else False


def _surface_claim(
    rows: list[tuple[str, int, str, str | None, int | None]],
    functions: dict[str, set[str]],
    classes: dict[str, dict[str, set[str]]],
) -> list[str]:
    """The three things that can go wrong between a header, a marker and a registration."""
    registered = set().union(*functions.values()) if functions else set()
    problems: list[str] = []
    for path, line, name, marker, _ in rows:
        parsed = MARKER.match(marker) if marker is not None else None
        if marker is not None and parsed is None:
            problems.append(
                f"{path}:{line} {name}: a `{MARKER_HEAD}` marker in the wrong shape; it reads "
                f"`{MARKER_HEAD} internal -- <reason>` or `{MARKER_HEAD} via <target> -- <reason>`"
            )
            continue
        reachable = name in registered
        if reachable and marker is not None:
            problems.append(
                f"{path}:{line} {name}: the exemption buys nothing any more, the bindings "
                "register it; delete the marker"
            )
            continue
        if reachable:
            continue
        if marker is None:
            problems.append(
                f"{path}:{line} {name}: declared at namespace scope in the core and absent from "
                "the bindings, with no `// python:` marker saying why"
            )
            continue
        route = parsed.group("route") if parsed is not None else None
        if route is not None and not _route_declared(route, functions, classes):
            problems.append(
                f"{path}:{line} {name}: the exemption reaches Python through `{route}`, which the "
                "bindings do not declare"
            )
    return problems


def _orphan_markers(rows: list[tuple[str, int, str, str | None, int | None]]) -> list[str]:
    """Markers standing on disk above nothing the claim covers.

    Kept apart from `_surface_claim` because that function also runs over planted one-row lists, and
    a statement about the whole tree would then contradict every plant. Its own failure mode is the
    third way an exemption rots: the function it disclaimed was deleted, or lost the attribute, and
    the comment stayed to explain a gap nobody can see any more.
    """
    claimed = {(path, line) for path, _, _, _, line in rows if line is not None}
    problems: list[str] = []
    for header in sorted(HEADER_ROOT.rglob("*.hpp")):
        relative = str(header.relative_to(REPO_ROOT))
        for number, text in enumerate(header.read_text(encoding="utf-8").split("\n"), start=1):
            if text.strip().startswith(MARKER_HEAD) and (relative, number) not in claimed:
                problems.append(
                    f"{relative}:{number}: a `// python:` marker above nothing the claim covers: "
                    "the function it disclaimed is gone, or moved off the line the marker sits on"
                )
    return problems


def _declared_surface() -> tuple[dict[str, set[str]], dict[str, dict[str, set[str]]]]:
    """What `bindings/python_bindings.cpp` says the extension should expose."""
    functions, classes, _ = _declared(_statements(BINDINGS.read_text(encoding="utf-8")))
    return functions, classes


def test_the_header_parser_reads_the_surface_it_claims_to_have_read() -> None:
    """A scanner that silently matched nothing would make the guard below vacuously green.

    Three shapes are pinned here because each one is a real declaration pattern in these headers:
    the attribute on the line above a split signature, the same attribute on a struct member (which
    must NOT count), and an `enum class` whose braces the stack has to close before the next free
    function is read. The counts are the newest API in the tree, so the day the file shape moves
    under this parser the test says so.
    """
    rows = _core_surface()
    registered, classes = _declared_surface()
    names = {name for _, _, name, _, _ in rows}
    assert len(rows) >= 80, f"the scan found {len(rows)} namespace-scope declarations"
    assert {
        "black_scholes_mixed_fourth_derivatives",
        "black_scholes_mixed_third_derivatives",
        # Phase 19: these were outside the attribute scan and are in the population now.
        "normal_cdf",
        "mean",
        "quantile_linear",
        "shrinkage_covariance",
    } <= names
    assert {"run_scenario", "historical_var", "price_heston_european"} <= names
    assert len(names & set().union(*registered.values())) >= 50, names

    split = _declarations(
        "[[nodiscard]] std::vector<std::pair<int, double>>\nconvergence_ladder(int steps);\n"
    )
    assert [name for _, name, _, _ in split] == ["convergence_ladder"], split
    member = _declarations(
        "struct Summary {\n    [[nodiscard]] double total() const { return 0.0; }\n};\n"
    )
    assert member == [], member
    after_enum = _declarations(
        "enum class Kind { Call, Put };\n[[nodiscard]] const char *to_string(const Kind kind);\n"
    )
    assert [name for _, name, _, _ in after_enum] == ["to_string"], after_enum
    assert classes, (
        "no bound class was parsed, so a `via Class.member` exemption could not be checked"
    )


def test_every_core_function_the_core_marks_reachable_is_bound_or_disclaimed() -> None:
    """The claim finding 43 said the repository had never made, made.

    `[[nodiscard]]` is the core's own marker for `this result is the point of calling it`, so
    the set is intent already stated in the code rather than a list assembled here. Each member is
    either registered in the bindings or carries a marker at its declaration -- and a marker is a
    testable claim, not prose: `via X` has to name something the bindings really declare, an
    exemption on a function that is in fact bound is stale, and a marker above nothing is orphaned.
    """
    registered, classes = _declared_surface()
    rows = _core_surface()
    problems = _surface_claim(rows, registered, classes) + _orphan_markers(rows)
    assert not problems, "the core surface and the bindings do not agree:\n" + "\n".join(problems)
    disclaimed = [row for row in rows if row[3] is not None]
    assert len(disclaimed) >= 20, f"only {len(disclaimed)} exemptions: the markers were edited away"
    assert len({row[2] for row in disclaimed}) >= 15, "the exemptions collapsed onto a few names"


def test_the_documents_that_count_the_core_surface_count_it_correctly() -> None:
    """Three documents restate how big the core surface is, and the scan owns that number.

    Phase 17 wrote 92 declarations, 85 names and 24 exemptions into the
    limitation register, the interview answer and its citation row. Phase 19
    changed every one of them and no check said so: a count in prose with no
    owner is a count that goes stale twice, the failure this repository has
    now closed in five other files.
    """
    rows = _core_surface()
    totals = {
        "declared": len(rows),
        "names": len({row[2] for row in rows}),
        "disclaimed": sum(1 for row in rows if row[3] is not None),
        "headers": len(list(HEADER_ROOT.rglob("*.hpp"))),
    }
    claims = {
        "docs/limitations.md": (
            r"the surface holds (\d+)\s+namespace-scope\s+declarations\s+and\s+(\d+)\s+distinct"
            r"\s+names,\s+and\s+(\d+)\s+of\s+them\s+are\s+disclaimed",
            ("declared", "names", "disclaimed"),
        ),
        "docs/interview_defense.md": (
            r"\((\d+) declarations, (\d+)\s+names\)",
            ("declared", "names"),
        ),
    }
    for name, (pattern, fields) in claims.items():
        found = re.search(pattern, (REPO_ROOT / name).read_text(encoding="utf-8"))
        assert found, f"{name} no longer states the core-surface counts in the checked form"
        for value, field in zip(found.groups(), fields, strict=True):
            assert int(value) == totals[field], (
                f"{name} says {field} is {value}; the scan reads {totals[field]}"
            )

    citation = re.search(
        r"(\d+) namespace-scope `\[\[nodiscard\]\]` declarations across (\d+) headers, "
        r"(\d+) names, (\d+) disclaimed",
        (REPO_ROOT / "docs" / "interview_defense.md").read_text(encoding="utf-8"),
    )
    assert citation, "interview_defense.md's citation row no longer states the surface counts"
    for value, field in zip(
        citation.groups(), ("declared", "headers", "names", "disclaimed"), strict=True
    ):
        assert int(value) == totals[field], (
            f"the citation row says {field} is {value}, not {totals[field]}"
        )


def test_no_namespace_scope_declaration_is_left_unmarked() -> None:
    """Every function the core declares at namespace scope carries `[[nodiscard]]`.

    Phase 17 keyed its claim on the attribute and inventoried what fell outside it: seventeen
    declarations in four headers -- the statistics primitives, the normal PDF/CDF/quantile, the
    version pair and the three covariance estimators -- carried nothing. Phase 19 marks them,
    because a numerical core that returns a value means it, and re-keys the claim onto the whole
    namespace-scope surface so a new function cannot join a residual by forgetting the attribute.
    `quantile_linear` stays unreachable from Python -- it takes data the caller already sorted --
    and now says so at its own declaration, where the guard tests the sentence rather than reads it.

    The probe is this guard's own negative control, because a scanner that quietly found nothing
    would make the assertion pass for the wrong reason. Five shapes are pinned: a member
    call inside an initialiser, a call inside an inline body, an attribute on the same line as the
    name, a declaration whose attribute sits on the line ABOVE the name -- which a scan starting at
    the name's own line read as unmarked, and did in the version Phase 17 shipped -- and one
    genuinely unmarked declaration, the only name that may be reported.
    """
    unmarked = [
        (str(header.relative_to(REPO_ROOT)), row[1])
        for header in sorted(HEADER_ROOT.rglob("*.hpp"))
        for row in _unmarked_declarations(header.read_text(encoding="utf-8"))
    ]
    assert unmarked == [], f"declarations the core left without `{ATTRIBUTE}`: {unmarked}"
    rows = _core_surface()
    assert len(rows) >= 100, f"the surface scan found {len(rows)} declarations; it lost the thread"
    assert all(row[3] is None or MARKER.match(row[3]) for row in rows if row[3] is not None), (
        "an exemption marker in a shape the claim does not parse"
    )

    probe = _unmarked_declarations(
        "namespace quantrisk {\n"
        "inline constexpr double kEpsilon = std::numeric_limits<double>::epsilon();\n"
        'inline void check(double value) { require_finite(value, "name"); }\n'
        "[[nodiscard]] double marked(double value);\n"
        "[[nodiscard]] long\nsplit_after_the_type(double value);\n"
        "double unmarked(double value);\n"
        "}  // namespace quantrisk\n"
    )
    assert [row[1] for row in probe] == ["unmarked"], probe


def test_a_marker_left_above_nothing_is_caught() -> None:
    """The orphan branch's own negative control: drop a covered row, the marker reports itself.

    Single variable, which is what makes it a control rather than a second assertion: the tree is
    unchanged and only the list the claim is run over loses one declaration, so the marker that was
    standing under it has nothing left to stand under.
    """
    rows = _core_surface()
    marked = [row for row in rows if row[4] is not None]
    assert marked, "no exemption marker in the tree, so the orphan branch has nothing to probe"
    assert not _orphan_markers(rows)
    gone = marked[0]
    without = [row for row in rows if row is not gone]
    problems = _orphan_markers(without)
    assert any(problem.startswith(f"{gone[0]}:{gone[4]}") for problem in problems), (gone, problems)


def test_a_core_function_bound_by_nobody_is_caught() -> None:
    """The negative control, and the differential that says why this guard exists.

    Finding 43's defect was a struct bound and its function never registered, which the two-way
    parity check above cannot see: source and binary agreed, because the registration line was
    absent from both. So the control adds a header declaration and removes nothing, and asserts
    the old comparison stays silent while the new claim names the function.
    """
    registered, classes = _declared_surface()
    baseline = _problems()
    rows = _core_surface()
    assert not _surface_claim(rows, registered, classes), "the tree is not green to begin with"

    planted = ("cpp/include/quantrisk/pricing/black_scholes.hpp", 999, "unbound_probe", None, None)
    problems = _surface_claim([*rows, planted], registered, classes)
    assert any("unbound_probe" in problem for problem in problems), problems
    assert not [problem for problem in problems if "unbound_probe" not in problem], (
        "the plant should be the only thing this changes: " + repr(problems)
    )

    # And the pre-existing guard has nothing to say about it, which is the gap being closed.
    assert all("unbound_probe" not in problem for problem in baseline), baseline


def test_an_exemption_whose_route_does_not_exist_is_caught() -> None:
    """`via X` is a fact claim, so a wrong X has to fail rather than read as a sentence."""
    rows = [
        (
            "cpp/include/quantrisk/risk/measures.hpp",
            5,
            "quantile_standard_error",
            "// python: via `monte_carlo_var_of_record` -- a route nobody registered.",
            None,
        )
    ]
    registered, classes = _declared_surface()
    problems = _surface_claim(rows, registered, classes)
    assert any("monte_carlo_var_of_record" in problem for problem in problems), problems

    field = [
        (
            "cpp/include/quantrisk/risk/measures.hpp",
            5,
            "quantile_standard_error",
            "// python: via `RiskEstimate.standard_error` -- reported as a field.",
            None,
        )
    ]
    assert not _surface_claim(field, registered, classes), (
        "the real route must verify, not just parse"
    )

    wrong_field = [
        (
            "cpp/include/quantrisk/risk/measures.hpp",
            5,
            "quantile_standard_error",
            "// python: via `RiskEstimate.standard_deviation` -- the wrong field.",
            None,
        )
    ]
    assert any(
        "standard_deviation" in problem
        for problem in _surface_claim(wrong_field, registered, classes)
    )


def test_an_exemption_that_the_bindings_made_obsolete_is_caught() -> None:
    """Exemptions rot in one direction only if nothing reads them: the bound case.

    The other direction is a marker left above a declaration that no longer carries the attribute.
    Both are planted here against the real surface, so neither branch of the claim is unwatched.
    """
    registered, classes = _declared_surface()
    bound = [
        (
            "cpp/include/quantrisk/pricing/black_scholes.hpp",
            12,
            "black_scholes",
            "// python: internal -- a reason that has stopped being true.",
            None,
        )
    ]
    problems = _surface_claim(bound, registered, classes)
    assert any("buys nothing any more" in problem for problem in problems), problems

    malformed = [
        (
            "cpp/include/quantrisk/pricing/black_scholes.hpp",
            12,
            "d1",
            "// python: internal because it is internal",
            None,
        )
    ]
    assert any(
        "wrong shape" in problem for problem in _surface_claim(malformed, registered, classes)
    )
