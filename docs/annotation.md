## typed-argparse

`typed-argparse` is a small annotation-driven CLI helper built around typed
functions and `argparse`-compatible parsers.

The core package has no required third-party runtime dependencies.

The main entry point is `build_parser()`. For `cmd2` users, the same inference
rules are also available through `with_annotated()` when the optional `cmd2`
extra is installed. Parsed namespaces can be converted back into plain call
arguments with `unwrap()`.

It is a good fit for simple CLIs, scripting tools, and lightweight LLM-facing
command-line wrappers where you want less framework overhead and more direct
Python code.

## Main API: build_parser

`build_parser()` inspects a typed function signature and creates a configured
parser from it.

```py
import argparse
from typing import Annotated

from typed_argparse import Argument, Option, build_parser


def greet(
    name: Annotated[str, Argument(help_text="Who to greet")],
    count: Annotated[int, Option("--count", "-c")] = 1,
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

The returned parser is a normal `argparse.ArgumentParser` by default.

`build_parser_from_function()` remains available as a compatibility alias.

## Type inference rules

These mappings are implemented and covered by the test suite.

| Type annotation                                          | Generated argparse behavior                         |
| -------------------------------------------------------- | --------------------------------------------------- |
| `str`                                                    | default string argument                             |
| `int`, `float`                                           | `type=int` / `type=float`                           |
| `bool` with default `False`                              | `--flag` with `action='store_true'`                 |
| `bool` with default `True`                               | `--no-flag` with `action='store_false'`             |
| positional `bool`                                        | parses `true/false`, `yes/no`, `on/off`, `1/0`      |
| `Path`                                                   | `type=Path`                                         |
| `Enum` subclass                                          | enum converter with value/name support              |
| `decimal.Decimal`                                        | `type=decimal.Decimal`                              |
| `Literal[...]`                                           | literal converter plus `choices`                    |
| `Collection[T]` / `list[T]` / `set[T]` / `tuple[T, ...]` | `nargs='+'` or `'*'` if a default is present        |
| `T | None` or `Optional[T]`                              | unwrapped to `T` and treated as optional            |

Collection parsing behavior:

- `list[T]` and `Collection[T]` produce a `list`
- `set[T]` produces a `set`
- `tuple[T, ...]` produces a `tuple`

## Argument and Option metadata

For finer control, use `typing.Annotated` with `Argument` or `Option`.

```py
from typing import Annotated

from typed_argparse import Argument, Option, build_parser


def play(
    sport: Annotated[str, Argument(help_text="Sport to play")],
    venue: Annotated[str, Option("--venue", "-v", help_text="Where to play")] = "home",
) -> None:
    pass


parser = build_parser(play)
```

Shared metadata fields:

- `help_text`
- `metavar`
- `nargs`
- `choices`

`cmd2`-specific metadata fields:

- `choices_provider`
- `completer`
- `table_columns`
- `suppress_tab_hint`

`Option` additionally supports:

- custom flag names via positional `*names`
- `action`
- `required`

## Unwrapping parsed namespaces

Use `unwrap()` when you want to feed parsed values back into a normal Python
call.

```py
from typed_argparse import unwrap

namespace = parser.parse_args(["Kelvin", "--count", "2"])

kwargs = unwrap(namespace)
values = unwrap(namespace, as_tuple=True)

assert kwargs == {"name": "Kelvin", "count": 2, "loud": False}
assert values == ("Kelvin", 2, False)
```

This helper reuses the same namespace filtering behavior used internally by
`with_annotated()`, including filtering internal `cmd2_*` fields.

## Calling helpers

For small CLIs, you can skip manual dispatch code.

```py
from typed_argparse import call, parse_and_call

namespace = parser.parse_args(["Kelvin", "--count", "2"])
call(greet, namespace)
parse_and_call(greet, ["Kelvin", "--loud"])
```

## Subcommands

For small multi-command tools, use `build_subcommand_parser()` or
`parse_and_call()` with a mapping.

```py
from typed_argparse import build_subcommand_parser, parse_and_call

commands = {"greet": greet, "tag": tag}

parser = build_subcommand_parser(commands)
namespace = parser.parse_args(["tag", "release", "--labels", "stable"])

result = parse_and_call(commands, ["tag", "release", "--labels", "stable"])
```

## cmd2 integration

If you are writing `cmd2` commands, use `with_annotated()` to apply the same
signature-driven parser generation directly to `do_*` methods.

Install the optional extra first:

```bash
uv add "typed-argparse[cmd2]"
```

```py
from typing import Annotated

import cmd2
from typed_argparse import Argument, Option, with_annotated


class MyApp(cmd2.Cmd):
    def sport_choices(self) -> list[str]:
        return ["football", "basketball"]

    @with_annotated
    def do_play(
        self,
        sport: Annotated[str, Argument(choices_provider=sport_choices)],
        venue: Annotated[str, Option("--venue", "-v")] = "home",
    ) -> None:
        self.poutput(f"Playing {sport} at {venue}")
```

Supported `cmd2`-specific behavior includes:

- `choices_provider`
- `completer`
- descriptive headers from `table_columns`
- `suppress_tab_hint`
- `preserve_quotes=True`
- `with_unknown_args=True`
- `CommandSet` integration

## Automatic completion from types

Type-based completion is implemented for released `cmd2` by the package itself.

- `Path` arguments get filesystem path completion
- `Enum` arguments complete from enum member values
- this works for both `@with_annotated` and manual `@with_argparser` parsers

## Verified status

The current test suite covers:

- parser generation for positional and option arguments
- metadata handling for `Argument` and `Option`
- namespace unwrapping to dict and tuple forms
- enum, literal, decimal, path, optional, and collection parsing
- command execution through `with_annotated`
- `cmd2` tab completion behavior
- `preserve_quotes`
- `with_unknown_args`
- `CommandSet` support
- wheel import smoke tests

Current verified commands:

```bash
uv run ruff check .
uv run pytest -q
uv build
```
