"""Parser construction tests for typed-argparse."""

import argparse
import decimal
import enum
from collections.abc import Collection
from pathlib import Path
from typing import Annotated, Any, Literal, Protocol, cast

import cmd2
import pytest
from cmd2.argparse_custom import DEFAULT_ARGUMENT_PARSER

from typed_argparse import build_parser
from typed_argparse.annotated import Argument, Option, build_parser_from_function


def _func_positional_str(self, name: str) -> None: ...
def _func_option_with_default(self, count: int = 1) -> None: ...
def _func_bool_false(self, verbose: bool = False) -> None: ...
def _func_bool_true(self, debug: bool = True) -> None: ...


class _Color(str, enum.Enum):
    red = "red"
    green = "green"
    blue = "blue"


def _func_enum(self, color: _Color) -> None: ...
def _func_path(self, path: Path = Path(".")) -> None: ...
def _func_list(self, files: list[str]) -> None: ...
def _func_optional(self, name: str | None = None) -> None: ...
def _func_annotated_arg(
    self, name: Annotated[str, Argument(help_text="Your name")]
) -> None: ...
def _func_annotated_option(
    self, color: Annotated[str, Option("--color", "-c", help_text="Pick")] = "blue"
) -> None: ...
def _func_metavar(self, name: Annotated[str, Argument(metavar="NAME")]) -> None: ...
def _func_explicit_nargs(self, names: Annotated[str, Argument(nargs=2)]) -> None: ...
def _func_explicit_action(
    self, verbose: Annotated[bool, Option(action="count")] = False
) -> None: ...
def _func_unknown_type(self, data: dict | None = None) -> None: ...
def _func_completer(
    self, path: Annotated[str, Argument(completer=cmd2.Cmd.path_complete)]
) -> None: ...
def _func_table_columns(
    self, item: Annotated[str, Argument(table_columns=("ID", "Name"))]
) -> None: ...
def _func_suppress_hint(
    self, item: Annotated[str, Argument(suppress_tab_hint=True)]
) -> None: ...
def _func_required_option(
    self, name: Annotated[str, Option("--name", required=True)]
) -> None: ...
def _func_annotated_no_metadata(self, name: Annotated[str, "some doc"]) -> None: ...
def _func_list_with_default(self, items: list[str] | None = None) -> None: ...
def _func_float_option(self, rate: float = 1.0) -> None: ...
def _func_positional_bool(self, flag: bool) -> None: ...
def _func_enum_with_default(self, color: _Color = _Color.blue) -> None: ...
def _func_positional_path(self, path: Path) -> None: ...
def _func_decimal(self, amount: decimal.Decimal = decimal.Decimal("1.25")) -> None: ...
def _func_collection(self, ids: Collection[int]) -> None: ...
def _func_set_collection(self, tags: set[str]) -> None: ...
def _func_tuple_collection(self, values: tuple[int, ...]) -> None: ...
def _func_literal_option(self, mode: Literal["fast", "slow"] = "fast") -> None: ...
def _func_literal_positional_int(self, level: Literal[1, 2, 3]) -> None: ...


FOOD_ITEMS = ["Pizza", "Ham", "Potato"]


def _func_static_choices(
    self, food: Annotated[str, Argument(choices=FOOD_ITEMS)]
) -> None: ...


def _func_option_choices(
    self, food: Annotated[str, Option("--food", choices=FOOD_ITEMS)] = "Pizza"
) -> None: ...


class _IntColor(enum.IntEnum):
    red = 1
    green = 2
    blue = 3


class _PlainColor(enum.Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


def _find_action(parser: argparse.ArgumentParser, dest: str) -> argparse.Action:
    for action in parser._actions:
        if action.dest == dest:
            return action
    raise ValueError(f"No action with dest={dest!r}")


class _Cmd2Action(Protocol):
    def get_choices_callable(self) -> Any: ...

    def get_descriptive_headers(self) -> tuple[str, ...] | None: ...

    def get_suppress_tab_hint(self) -> bool: ...


class TestBuildParserParams:
    @pytest.mark.parametrize(
        ("func", "param_name", "expected"),
        [
            pytest.param(
                _func_positional_str,
                "name",
                {"option_strings": [], "type": None},
                id="positional_str",
            ),
            pytest.param(
                _func_option_with_default,
                "count",
                {"option_strings": ["--count"], "type": int, "default": 1},
                id="option_with_default",
            ),
            pytest.param(
                _func_bool_false,
                "verbose",
                {"option_strings": ["--verbose"]},
                id="bool_flag_false",
            ),
            pytest.param(
                _func_bool_true,
                "debug",
                {"option_strings": ["--no-debug"]},
                id="bool_flag_true",
            ),
            pytest.param(
                _func_enum, "color", {"option_strings": []}, id="enum_choices"
            ),
            pytest.param(
                _func_path,
                "path",
                {"option_strings": ["--path"], "type": Path},
                id="path_type",
            ),
            pytest.param(
                _func_list,
                "files",
                {"option_strings": [], "nargs": "+"},
                id="list_nargs",
            ),
            pytest.param(
                _func_optional,
                "name",
                {"option_strings": ["--name"], "default": None},
                id="optional_type",
            ),
            pytest.param(
                _func_float_option,
                "rate",
                {"option_strings": ["--rate"], "type": float, "default": 1.0},
                id="float_option",
            ),
            pytest.param(
                _func_positional_bool,
                "flag",
                {"option_strings": []},
                id="positional_bool_parse_rule",
            ),
            pytest.param(
                _func_enum_with_default,
                "color",
                {"option_strings": ["--color"]},
                id="enum_with_default_becomes_option",
            ),
            pytest.param(
                _func_positional_path,
                "path",
                {"option_strings": [], "type": Path},
                id="positional_path_no_default",
            ),
            pytest.param(
                _func_decimal,
                "amount",
                {
                    "option_strings": ["--amount"],
                    "type": decimal.Decimal,
                    "default": decimal.Decimal("1.25"),
                },
                id="decimal_option",
            ),
            pytest.param(
                _func_collection,
                "ids",
                {"option_strings": [], "nargs": "+", "type": int},
                id="collection_positional",
            ),
            pytest.param(
                _func_set_collection,
                "tags",
                {"option_strings": [], "nargs": "+"},
                id="set_collection_positional",
            ),
            pytest.param(
                _func_tuple_collection,
                "values",
                {"option_strings": [], "nargs": "+", "type": int},
                id="tuple_collection_positional",
            ),
            pytest.param(
                _func_literal_option,
                "mode",
                {
                    "option_strings": ["--mode"],
                    "choices": ["fast", "slow"],
                    "default": "fast",
                },
                id="literal_option",
            ),
            pytest.param(
                _func_literal_positional_int,
                "level",
                {"option_strings": [], "choices": [1, 2, 3]},
                id="literal_positional_int",
            ),
            pytest.param(
                _func_static_choices,
                "food",
                {"option_strings": [], "choices": FOOD_ITEMS},
                id="static_choices_positional",
            ),
            pytest.param(
                _func_option_choices,
                "food",
                {
                    "option_strings": ["--food"],
                    "choices": FOOD_ITEMS,
                    "default": "Pizza",
                },
                id="static_choices_option",
            ),
        ],
    )
    def test_build_parser_params(self, func, param_name, expected):
        parser = build_parser_from_function(func)
        action = _find_action(parser, param_name)
        for key, value in expected.items():
            assert getattr(action, key) == value, (
                f"{key}: expected {value!r}, got {getattr(action, key)!r}"
            )


class TestBuildParserEdgeCases:
    @pytest.mark.parametrize(
        ("func", "param_name", "expected"),
        [
            pytest.param(_func_metavar, "name", {"metavar": "NAME"}, id="metavar"),
            pytest.param(
                _func_explicit_nargs, "names", {"nargs": 2}, id="explicit_nargs"
            ),
            pytest.param(
                _func_unknown_type,
                "data",
                {"default": None, "option_strings": ["--data"]},
                id="unknown_type_with_default",
            ),
            pytest.param(
                _func_required_option,
                "name",
                {"required": True, "option_strings": ["--name"]},
                id="required_option",
            ),
            pytest.param(
                _func_annotated_no_metadata,
                "name",
                {"option_strings": []},
                id="annotated_no_arg_option_metadata",
            ),
            pytest.param(
                _func_list_with_default,
                "items",
                {"nargs": "*", "option_strings": ["--items"]},
                id="list_with_default_star_nargs",
            ),
        ],
    )
    def test_edge_cases(self, func, param_name, expected):
        parser = build_parser_from_function(func)
        action = _find_action(parser, param_name)
        for key, value in expected.items():
            assert getattr(action, key) == value, (
                f"{key}: expected {value!r}, got {getattr(action, key)!r}"
            )

    def test_completer_wired(self):
        parser = build_parser(_func_completer, parser_factory=DEFAULT_ARGUMENT_PARSER)
        action = cast(_Cmd2Action, _find_action(parser, "path"))
        cc = action.get_choices_callable()
        assert cc is not None
        assert cc.is_completer is True

    def test_table_columns_wired(self):
        parser = build_parser(
            _func_table_columns, parser_factory=DEFAULT_ARGUMENT_PARSER
        )
        action = cast(_Cmd2Action, _find_action(parser, "item"))
        assert action.get_descriptive_headers() == ("ID", "Name")

    def test_suppress_tab_hint_wired(self):
        parser = build_parser(
            _func_suppress_hint, parser_factory=DEFAULT_ARGUMENT_PARSER
        )
        action = cast(_Cmd2Action, _find_action(parser, "item"))
        assert action.get_suppress_tab_hint() is True

    def test_enum_by_value(self):
        from typed_argparse.annotated import _make_enum_type

        converter = _make_enum_type(_Color)
        assert converter("red") == _Color.red
        assert converter("green") == _Color.green

    def test_enum_by_name_fallback(self):
        from typed_argparse.annotated import _make_enum_type

        converter = _make_enum_type(_IntColor)
        assert converter("red") == _IntColor.red
        assert converter("blue") == _IntColor.blue

    def test_enum_invalid_value(self):
        from typed_argparse.annotated import _make_enum_type

        converter = _make_enum_type(_Color)
        with pytest.raises(argparse.ArgumentTypeError, match="invalid choice"):
            converter("purple")

    def test_explicit_action_in_metadata(self):
        parser = build_parser_from_function(_func_explicit_action)
        action = _find_action(parser, "verbose")
        assert isinstance(action, argparse._CountAction)

    def test_positional_bool_parse_rule(self):
        parser = build_parser_from_function(_func_positional_bool)
        assert parser.parse_args(["true"]).flag is True
        assert parser.parse_args(["0"]).flag is False

        with pytest.raises(SystemExit):
            parser.parse_args(["definitely"])

    def test_literal_int_parses_as_int(self):
        parser = build_parser_from_function(_func_literal_positional_int)
        assert parser.parse_args(["2"]).level == 2

        with pytest.raises(SystemExit):
            parser.parse_args(["7"])

    def test_set_collection_cast(self):
        parser = build_parser_from_function(_func_set_collection)
        parsed = parser.parse_args(["a", "b", "a"])
        assert isinstance(parsed.tags, set)
        assert parsed.tags == {"a", "b"}

    def test_tuple_collection_cast(self):
        parser = build_parser_from_function(_func_tuple_collection)
        parsed = parser.parse_args(["1", "2", "3"])
        assert isinstance(parsed.values, tuple)
        assert parsed.values == (1, 2, 3)

    def test_collection_cast_uses_store_action(self):
        from typed_argparse.annotated import _CollectionStoreAction

        set_parser = build_parser_from_function(_func_set_collection)
        set_action = _find_action(set_parser, "tags")
        assert isinstance(set_action, _CollectionStoreAction)

        tuple_parser = build_parser_from_function(_func_tuple_collection)
        tuple_action = _find_action(tuple_parser, "values")
        assert isinstance(tuple_action, _CollectionStoreAction)

    def test_plain_enum_parses_by_value_and_name(self):
        def _func_plain_enum(self, color: _PlainColor) -> None: ...

        parser = build_parser_from_function(_func_plain_enum)
        assert parser.parse_args(["red"]).color is _PlainColor.RED
        assert parser.parse_args(["green"]).color is _PlainColor.GREEN
        assert parser.parse_args(["BLUE"]).color is _PlainColor.BLUE


class TestPositionalDefaults:
    """Positional arguments with defaults should infer ``nargs="?"``."""

    def test_argument_with_default_becomes_optional_positional(self):
        default_path = Path("default.txt")

        def _func(
            self,
            file: Annotated[Path, Argument(help_text="Input file")] = default_path,
        ) -> None: ...

        parser = build_parser_from_function(_func)
        action = _find_action(parser, "file")
        assert action.option_strings == [], "should be positional"
        assert action.nargs == "?"
        assert action.default == default_path

        assert parser.parse_args([]).file == default_path
        assert parser.parse_args(["custom.txt"]).file == Path("custom.txt")

    def test_argument_with_optional_type_default_none(self):
        def _func(
            self,
            file: Annotated[Path | None, Argument(help_text="Input file")] = None,
        ) -> None: ...

        parser = build_parser_from_function(_func)
        action = _find_action(parser, "file")
        assert action.option_strings == [], "should be positional"
        assert action.nargs == "?"
        assert action.default is None

        assert parser.parse_args([]).file is None
        assert parser.parse_args(["x.txt"]).file == Path("x.txt")

    def test_required_positional_keeps_no_nargs(self):
        # Sanity check: explicit ``Argument(...)`` without a default stays required.
        def _func(
            self,
            name: Annotated[str, Argument(help_text="Your name")],
        ) -> None: ...

        parser = build_parser_from_function(_func)
        action = _find_action(parser, "name")
        assert action.option_strings == []
        assert action.nargs is None
        assert action.required is True

    def test_explicit_nargs_overrides_default_inference(self):
        defaults = ("a", "b")

        def _func(
            self,
            names: Annotated[tuple[str, ...], Argument(nargs=2)] = defaults,
        ) -> None: ...

        parser = build_parser_from_function(_func)
        action = _find_action(parser, "names")
        assert action.nargs == 2


class TestConstMetadata:
    """``Argument`` and ``Option`` should forward ``const`` to argparse."""

    def test_option_const_with_optional_value(self):
        def _func(
            self,
            level: Annotated[
                int | None,
                Option("--level", nargs="?", const=5, help_text="Verbosity level"),
            ] = None,
        ) -> None: ...

        parser = build_parser_from_function(_func)
        action = _find_action(parser, "level")
        assert action.option_strings == ["--level"]
        assert action.nargs == "?"
        assert action.const == 5
        assert action.default is None

        assert parser.parse_args([]).level is None
        assert parser.parse_args(["--level"]).level == 5
        assert parser.parse_args(["--level", "9"]).level == 9

    def test_const_zero_is_preserved(self):
        # Falsy values must still propagate.
        def _func(
            self,
            level: Annotated[int, Option("--level", nargs="?", const=0)] = 1,
        ) -> None: ...

        parser = build_parser_from_function(_func)
        action = _find_action(parser, "level")
        assert action.const == 0

    def test_const_omitted_does_not_pass_kwarg(self):
        # Without ``const``, argparse should keep its own default of ``None``.
        def _func(
            self,
            mode: Annotated[str, Option("--mode")] = "fast",
        ) -> None: ...

        parser = build_parser_from_function(_func)
        action = _find_action(parser, "mode")
        assert action.const is None


class TestAnnotatedMetadata:
    @pytest.mark.parametrize(
        ("func", "param_name", "expected"),
        [
            pytest.param(
                _func_annotated_arg,
                "name",
                {"option_strings": [], "help": "Your name"},
                id="annotated_argument_help",
            ),
            pytest.param(
                _func_annotated_option,
                "color",
                {"option_strings": ["--color", "-c"], "help": "Pick"},
                id="annotated_option_custom_names",
            ),
        ],
    )
    def test_annotated_metadata(self, func, param_name, expected):
        parser = build_parser_from_function(func)
        action = _find_action(parser, param_name)
        for key, value in expected.items():
            assert getattr(action, key) == value, (
                f"{key}: expected {value!r}, got {getattr(action, key)!r}"
            )


class TestBuildParserAlias:
    def test_build_parser_alias(self):
        parser = build_parser(_func_option_with_default)
        action = _find_action(parser, "count")
        assert action.option_strings == ["--count"]

    def test_parser_description_uses_docstring(self):
        def _func_with_doc(name: str) -> None:
            """Sample parser description."""

        parser = build_parser(_func_with_doc)
        assert parser.description == "Sample parser description."


class TestMultiWordFlagNames:
    def test_standalone_parser_dasherizes_underscored_params(self):
        def _f(dry_run: bool = False, max_retries: int = 3) -> None: ...

        parser = build_parser(_f)
        assert _find_action(parser, "dry_run").option_strings == ["--dry-run"]
        assert _find_action(parser, "max_retries").option_strings == ["--max-retries"]

    def test_standalone_dasherizes_no_prefix_for_bool_true_default(self):
        def _f(verbose_mode: bool = True) -> None: ...

        parser = build_parser(_f)
        action = _find_action(parser, "verbose_mode")
        assert action.option_strings == ["--no-verbose-mode"]

    def test_cmd2_parser_also_dasherizes_but_dest_stays_underscored(self):
        def _f(dry_run: bool = False, max_retries: int = 3) -> None: ...

        parser = build_parser(_f, parser_factory=DEFAULT_ARGUMENT_PARSER)
        dry_run_action = _find_action(parser, "dry_run")
        max_retries_action = _find_action(parser, "max_retries")
        assert dry_run_action.option_strings == ["--dry-run"]
        assert dry_run_action.dest == "dry_run"
        assert max_retries_action.option_strings == ["--max-retries"]
        assert max_retries_action.dest == "max_retries"

        ns = parser.parse_args(["--dry-run", "--max-retries", "5"])
        assert ns.dry_run is True
        assert ns.max_retries == 5

    def test_explicit_option_names_are_left_untouched(self):
        def _f(
            dry_run: Annotated[bool, Option("--dry_run")] = False,
        ) -> None: ...

        parser = build_parser(_f)
        assert _find_action(parser, "dry_run").option_strings == ["--dry_run"]


class TestVarArgsAreSkipped:
    def test_var_positional_and_var_keyword_are_skipped(self):
        def _f(name: str, *args, **kwargs) -> None: ...

        parser = build_parser(_f)
        dests = {action.dest for action in parser._actions if action.dest != "help"}
        assert dests == {"name"}

    def test_var_args_function_parses_correctly(self):
        def _f(name: str, count: int = 1, *args, **kwargs) -> tuple:
            return name, count, args, kwargs

        ns = build_parser(_f).parse_args(["kelvin", "--count", "3"])
        assert ns.name == "kelvin"
        assert ns.count == 3
