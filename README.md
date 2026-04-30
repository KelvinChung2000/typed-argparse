# typed-argparse

[![CI](https://github.com/KelvinChung2000/typed-argparse/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/KelvinChung2000/typed-argparse/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![uv](https://img.shields.io/badge/managed%20with-uv-6A5AF9.svg)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/badge/lint-ruff-D7FF64.svg)](https://github.com/astral-sh/ruff)
[![ty](https://img.shields.io/badge/type%20check-ty-1F6FEB.svg)](https://github.com/astral-sh/ty)
[![SemVer](https://img.shields.io/badge/versioning-semver-3F4551.svg)](https://semver.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](./LICENSE)

`typed-argparse` is a small annotation-driven CLI helper for people who want
typed parser generation without adopting a large framework.

It is aimed at simple command-line tools, scripting utilities, and lightweight
LLM-facing CLIs where you want a small API surface, explicit Python functions,
and standard `argparse` behavior instead of a large abstraction layer.

The core package has no required third-party runtime dependencies. The main API
is `build_parser()`, which converts a typed function signature into an
`argparse`-compatible parser. The package also includes `Argument`, `Option`,
`unwrap()`, `call()`, `parse_and_call()`, and `build_subcommand_parser()`,
plus optional `cmd2` integration through `with_annotated()`.

Why use it:

- small API surface
- typed function signatures instead of command classes or decorators everywhere
- easy `argparse.Namespace -> kwargs` conversion through `unwrap()`
- a good fit for short-lived tools and simple LLM CLI wrappers
- optional `cmd2` integration when you want an interactive shell

## Install

The package is published on PyPI as `typed-argparse-gen` and imported as
`typed_argparse`.

```bash
uv add typed-argparse-gen
```

For `cmd2` integration:

```bash
uv add "typed-argparse-gen[cmd2]"
```

## Main feature: `build_parser()`

Use `build_parser()` when you want annotation-driven parser generation directly.

```python
import argparse
from typing import Annotated

from typed_argparse import Argument, Option, build_parser


def greet(
    name: Annotated[str, Argument(help_text="Who to greet")],
    count: Annotated[int, Option("--count", "-c", help_text="Number of greetings")] = 1,
    loud: bool = False,
) -> None:
    pass


parser = build_parser(greet)
args = parser.parse_args(["Kelvin", "--count", "2", "--loud"])

assert isinstance(parser, argparse.ArgumentParser)
assert args.name == "Kelvin"
assert args.count == 2
assert args.loud is True
```

`build_parser_from_function()` is still available as an alias.

By default:

- parameters without defaults become positional arguments
- parameters with defaults become `--option` flags
- `bool = False` becomes `store_true`
- `bool = True` becomes `store_false` on `--no-name`
- `Annotated[..., Argument(...)]` and `Annotated[..., Option(...)]` override the defaults

## Unwrapping and calling

Use `unwrap()` to convert a parsed `argparse.Namespace` into plain values.
Use `call()` and `parse_and_call()` for the common dispatch path.

```python
from typed_argparse import build_parser, call, parse_and_call, unwrap

parser = build_parser(greet)
namespace = parser.parse_args(["Kelvin", "--count", "2"])

kwargs = unwrap(namespace)
values = unwrap(namespace, as_tuple=True)

assert kwargs == {"name": "Kelvin", "count": 2, "loud": False}
assert values == ("Kelvin", 2, False)

assert call(greet, namespace) == ["Hello Kelvin", "Hello Kelvin"]
assert parse_and_call(greet, ["Kelvin", "--loud"]) == ["HELLO KELVIN"]
```

## Subcommands

Use `build_subcommand_parser()` or `parse_and_call()` with a mapping for
small multi-command CLIs.

```python
from typed_argparse import build_subcommand_parser, parse_and_call

commands = {"greet": greet, "tag": tag}

parser = build_subcommand_parser(commands)
namespace = parser.parse_args(["tag", "release", "--labels", "stable"])

result = parse_and_call(commands, ["tag", "release", "--labels", "stable"])
```

## Optional `cmd2` support

If you are using `cmd2`, you can use the same metadata model with
`with_annotated()`. Install the optional `cmd2` extra first.

For typed code, prefer direct imports:

```python
import cmd2
from typing import Annotated

from typed_argparse import Argument, Option, with_annotated


class App(cmd2.Cmd):
    def sport_choices(self) -> list[str]:
        return ["football", "basketball", "tennis"]

    @with_annotated
    def do_play(
        self,
        sport: Annotated[str, Argument(choices_provider=sport_choices)],
        venue: Annotated[str, Option("--venue", "-v")] = "home",
    ) -> None:
        self.poutput(f"{sport=} {venue=}")
```

## Development

```bash
uv sync --group dev
uv run ruff check .
uv run ty check
uv run pytest
uv build
```

## Release flow

This repo is configured for semantic versioning with conventional commits.

- Push conventional commits to `main`
- GitHub Actions runs tests and lint with `uv`
- `python-semantic-release` determines the next version, updates `CHANGELOG.md`, tags the release, and publishes to PyPI

Expected commit prefixes include `feat:`, `fix:`, and `perf:`. Breaking changes should use `!` or a `BREAKING CHANGE:` footer.
