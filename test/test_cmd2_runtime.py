"""cmd2 integration and runtime behavior tests."""

import argparse
import enum
from pathlib import Path
from typing import Annotated

import cmd2
import pytest
from cmd2 import Cmd2ArgumentParser

from typed_argparse import Argument, Option, with_annotated

from .conftest import complete_cmd, run_cmd


class _Color(str, enum.Enum):
    red = "red"
    green = "green"
    blue = "blue"


class _Sport(str, enum.Enum):
    football = "football"
    basketball = "basketball"
    tennis = "tennis"


class AnnotatedApp(cmd2.Cmd):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._items = ["apple", "banana", "cherry"]

    def item_choices(self) -> list[str]:
        return self._items

    @with_annotated
    def do_greet(self, name: str, count: int = 1) -> None:
        for _ in range(count):
            self.poutput(f"Hello {name}")

    @with_annotated
    def do_add(self, a: int, b: int = 0) -> None:
        self.poutput(str(a + b))

    @with_annotated
    def do_paint(
        self,
        item: str,
        color: Annotated[
            _Color, Option("--color", "-c", help_text="Color")
        ] = _Color.blue,
        verbose: bool = False,
    ) -> None:
        msg = f"Painting {item} {color.value}"
        if verbose:
            msg += " (verbose)"
        self.poutput(msg)

    @with_annotated
    def do_pick(
        self, item: Annotated[str, Argument(choices_provider=item_choices)]
    ) -> None:
        self.poutput(f"Picked: {item}")

    @with_annotated
    def do_open(self, path: Path) -> None:
        self.poutput(f"Opening: {path}")

    @with_annotated
    def do_sport(self, sport: _Sport) -> None:
        self.poutput(f"Playing: {sport.value}")

    @with_annotated(preserve_quotes=True)
    def do_raw(self, text: str) -> None:
        self.poutput(f"raw: {text}")


@pytest.fixture
def ann_app() -> AnnotatedApp:
    app = AnnotatedApp()
    app.stdout = cmd2.utils.StdSim(app.stdout)
    return app


class TestCommandExecution:
    @pytest.mark.parametrize(
        ("command", "expected"),
        [
            pytest.param("greet Alice", ["Hello Alice"], id="greet_basic"),
            pytest.param(
                "greet Alice --count 3",
                ["Hello Alice", "Hello Alice", "Hello Alice"],
                id="greet_count",
            ),
            pytest.param("add 2 --b 3", ["5"], id="add"),
            pytest.param("add 10", ["10"], id="add_default"),
            pytest.param(
                "paint wall", ["Painting wall blue"], id="paint_default_color"
            ),
            pytest.param(
                "paint wall --color red", ["Painting wall red"], id="paint_color"
            ),
            pytest.param(
                "paint wall --verbose",
                ["Painting wall blue (verbose)"],
                id="paint_verbose",
            ),
            pytest.param("sport football", ["Playing: football"], id="sport_enum"),
        ],
    )
    def test_command_execution(self, ann_app, command, expected):
        out, _err = run_cmd(ann_app, command)
        assert out == expected


class TestTabCompletion:
    def test_enum_completion(self, ann_app):
        assert sorted(complete_cmd(ann_app, "paint wall --color ", "")) == [
            "blue",
            "green",
            "red",
        ]

    def test_enum_completion_partial(self, ann_app):
        assert complete_cmd(ann_app, "paint wall --color r", "r") == ["red"]

    def test_choices_provider_completion(self, ann_app):
        assert sorted(complete_cmd(ann_app, "pick ", "")) == [
            "apple",
            "banana",
            "cherry",
        ]

    def test_positional_enum_completion(self, ann_app):
        assert complete_cmd(ann_app, "sport foot", "foot") == ["football"]


class _InferColor(str, enum.Enum):
    red = "red"
    green = "green"


class TypeInferenceApp(cmd2.Cmd):
    path_parser = Cmd2ArgumentParser()
    path_parser.add_argument("filepath", type=Path)

    @cmd2.with_argparser(path_parser)
    def do_read(self, args: argparse.Namespace) -> None:
        self.poutput(str(args.filepath))

    enum_parser = Cmd2ArgumentParser()
    enum_parser.add_argument("color", type=_InferColor)

    @cmd2.with_argparser(enum_parser)
    def do_pick_color(self, args: argparse.Namespace) -> None:
        self.poutput(args.color.value)


@pytest.fixture
def infer_app() -> TypeInferenceApp:
    app = TypeInferenceApp()
    app.stdout = cmd2.utils.StdSim(app.stdout)
    return app


class TestTypeInference:
    def test_enum_type_inference(self, infer_app):
        assert sorted(complete_cmd(infer_app, "pick_color ", "")) == ["green", "red"]

    def test_path_type_inference(self, infer_app, tmp_path):
        test_file = tmp_path / "testfile.txt"
        test_file.touch()
        text = str(tmp_path) + "/"
        result_strings = complete_cmd(infer_app, f"read {text}", text)
        assert len(result_strings) > 0
        assert any("testfile.txt" in s for s in result_strings)


class TestHelpOutput:
    def test_help_shows_arguments(self, ann_app):
        out, _ = run_cmd(ann_app, "help greet")
        assert "name" in "\n".join(out).lower()

    def test_help_shows_option_help(self, ann_app):
        out, _ = run_cmd(ann_app, "help paint")
        help_text = "\n".join(out)
        assert "Color" in help_text or "color" in help_text


class TestPreserveQuotes:
    def test_preserve_quotes(self, ann_app):
        out, _ = run_cmd(ann_app, 'raw "hello world"')
        assert out == ['raw: "hello world"']


class UnknownArgsApp(cmd2.Cmd):
    @with_annotated(with_unknown_args=True)
    def do_flex(self, name: str, _unknown: list[str] | None = None) -> None:
        self.poutput(f"name={name}")
        if _unknown:
            self.poutput(f"unknown={_unknown}")


@pytest.fixture
def unknown_app() -> UnknownArgsApp:
    app = UnknownArgsApp()
    app.stdout = cmd2.utils.StdSim(app.stdout)
    return app


class TestUnknownArgs:
    def test_with_unknown_args(self, unknown_app):
        out, _ = run_cmd(unknown_app, "flex Alice --extra stuff")
        assert out[0] == "name=Alice"
        assert "unknown=" in out[1]

    def test_with_unknown_args_requires_unknown_parameter(self):
        with pytest.raises(TypeError, match="requires a parameter named _unknown"):

            class _BadUnknownArgsApp(cmd2.Cmd):
                @with_annotated(with_unknown_args=True)
                def do_bad(self, name: str) -> None:
                    self.poutput(name)


class TestArgparseError:
    def test_invalid_args_raise_error(self, ann_app):
        _out, err = run_cmd(ann_app, "add")
        err_text = "\n".join(err)
        assert (
            "required" in err_text.lower()
            or "error" in err_text.lower()
            or "usage" in err_text.lower()
        )


class AnnotatedCommandSet(cmd2.CommandSet):
    def __init__(self) -> None:
        super().__init__()
        self._sports = ["football", "baseball"]

    def sport_choices(self) -> list[str]:
        return self._sports

    @with_annotated
    def do_play(
        self, sport: Annotated[str, Argument(choices_provider=sport_choices)]
    ) -> None:
        self._cmd.poutput(f"Playing {sport}")


@pytest.fixture
def cmdset_app() -> cmd2.Cmd:
    cmdset = AnnotatedCommandSet()
    app = cmd2.Cmd(command_sets=[cmdset])
    app.stdout = cmd2.utils.StdSim(app.stdout)
    return app


class TestCommandSet:
    def test_command_set_execution(self, cmdset_app):
        out, _err = run_cmd(cmdset_app, "play football")
        assert out == ["Playing football"]

    def test_command_set_completion(self, cmdset_app):
        assert sorted(complete_cmd(cmdset_app, "play ", "")) == ["baseball", "football"]
