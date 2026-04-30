#!/usr/bin/env python3
"""Standalone typed-argparse example using parse_and_call().

Usage:

    uv run python example/build_parser.py greet Kelvin --count 2 --loud
    uv run python example/build_parser.py tag release --labels stable latest
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from typed_argparse import Argument, Option, parse_and_call


def greet(
    name: Annotated[str, Argument(help_text="Who to greet")],
    count: Annotated[int, Option("--count", "-c", help_text="Number of greetings")] = 1,
    loud: bool = False,
) -> None:
    """Simple typed command."""
    for _ in range(count):
        message = f"Hello {name}"
        print(message.upper() if loud else message)


def tag(
    target: Annotated[Path, Argument(help_text="File or directory to label")],
    labels: Annotated[
        list[str], Option("--labels", "-l", help_text="Labels to apply")
    ]
    | None = None,
) -> None:
    """Example showing Path and collection inference."""
    print(f"target={target}")
    print(f"labels={labels or []}")


COMMANDS = {"greet": greet, "tag": tag}


def main() -> None:
    parse_and_call(COMMANDS)


if __name__ == "__main__":
    main()
