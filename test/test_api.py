"""High-level API tests for typed-argparse."""

from __future__ import annotations

from typing import Annotated

from typed_argparse import (
    Argument,
    Option,
    build_parser,
    build_subcommand_parser,
    call,
    parse_and_call,
)


def greet(
    name: Annotated[str, Argument(help_text="Who to greet")],
    count: Annotated[int, Option("--count", "-c")] = 1,
    loud: bool = False,
) -> list[str]:
    message = f"Hello {name}"
    line = message.upper() if loud else message
    return [line for _ in range(count)]


def tag(
    target: str,
    labels: Annotated[list[str], Option("--labels", "-l")] | None = None,
) -> tuple[str, list[str]]:
    return target, labels or []


class TestCallHelpers:
    def test_call(self):
        namespace = build_parser(greet).parse_args(["Kelvin", "--count", "2"])
        assert call(greet, namespace) == ["Hello Kelvin", "Hello Kelvin"]

    def test_parse_and_call_single_function(self):
        assert parse_and_call(greet, ["Kelvin", "--loud"]) == ["HELLO KELVIN"]


class TestSubcommands:
    def test_build_subcommand_parser(self):
        parser = build_subcommand_parser({"greet": greet, "tag": tag})
        namespace = parser.parse_args(
            ["tag", "release", "--labels", "stable", "latest"]
        )
        assert namespace.command == "tag"

    def test_parse_and_call_subcommands(self):
        result = parse_and_call(
            {"greet": greet, "tag": tag},
            ["tag", "release", "--labels", "stable", "latest"],
        )
        assert result == ("release", ["stable", "latest"])
