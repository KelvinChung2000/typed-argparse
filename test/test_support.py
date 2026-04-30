"""Support and helper behavior tests."""

import argparse

import cmd2
import pytest

from typed_argparse import unwrap, with_annotated

from .conftest import run_cmd


class TestGetTypeHintsFailure:
    def test_bad_annotation_falls_back(self):
        exec_globals: dict = {}
        exec(
            "from typed_argparse import build_parser_from_function\n"
            "def func(self, name: 'NonExistentType' = 'default'): ...\n"
            "result = build_parser_from_function(func)\n",
            exec_globals,
        )
        parser = exec_globals["result"]
        assert parser is not None


class TestParsePositionalsError:
    def test_raises_on_bad_args(self):
        from cmd2.decorators import _parse_positionals

        with pytest.raises(TypeError, match="Expected arguments"):
            _parse_positionals(("not_a_cmd", "not_a_statement"))


class SubcmdApp(cmd2.Cmd):
    @with_annotated
    def do_echo(self, msg: str) -> None:
        self.poutput(msg)


@pytest.fixture
def subcmd_app() -> SubcmdApp:
    app = SubcmdApp()
    app.stdout = cmd2.utils.StdSim(app.stdout)
    return app


class TestNamespaceFiltering:
    def test_subcmd_handler_filtered(self, subcmd_app):
        out, _ = run_cmd(subcmd_app, "echo hello")
        assert out == ["hello"]

    def test_typing_union_optional(self):
        from typed_argparse.annotated import _unwrap_optional

        ns: dict = {}
        exec("import typing; t = typing.Union[str, None]", ns)
        union_type = ns["t"]
        inner, is_opt = _unwrap_optional(union_type)
        assert inner is str
        assert is_opt is True

        inner2, is_opt2 = _unwrap_optional(str)
        assert inner2 is str
        assert is_opt2 is False

    def test_namespace_filtering_directly(self):
        from cmd2 import constants

        ns = argparse.Namespace(
            msg="hello", cmd2_statement="x", **{constants.NS_ATTR_SUBCMD_HANDLER: None}
        )
        assert unwrap(ns) == {"msg": "hello"}

    def test_unwrap_as_tuple(self):
        ns = argparse.Namespace(name="Kelvin", count=2, loud=True)
        assert unwrap(ns, as_tuple=True) == ("Kelvin", 2, True)

    def test_unwrap_exported_from_package(self):
        ns = argparse.Namespace(name="Kelvin")
        assert unwrap(ns) == {"name": "Kelvin"}
