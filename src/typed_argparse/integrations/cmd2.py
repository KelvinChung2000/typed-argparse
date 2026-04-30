"""Optional cmd2 integration for typed-argparse."""

from __future__ import annotations

import enum
import functools
import inspect
import pathlib
from collections.abc import Callable
from typing import Any, Protocol, TypeVar, cast

import cmd2.argparse_completer as argparse_completer
from cmd2 import constants
from cmd2.argparse_custom import DEFAULT_ARGUMENT_PARSER
from cmd2.decorators import _parse_positionals
from cmd2.exceptions import Cmd2ArgparseError

from ..builder import build_parser
from ..unwrap import unwrap

_ORIGINAL_COMPLETE_ARG = argparse_completer.ArgparseCompleter._complete_arg
F = TypeVar("F", bound="_NamedCallable")


class _NamedCallable(Protocol):
    __name__: str

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


def _enum_choice_values(type_hint: Any) -> list[str] | None:
    enum_class = getattr(type_hint, "_cmd2_enum_class", None)
    if enum_class is None and isinstance(type_hint, type) and issubclass(
        type_hint, enum.Enum
    ):
        enum_class = type_hint

    if enum_class is None:
        return None
    return [str(member.value) for member in enum_class]


def _patched_complete_arg(
    self,
    text: str,
    line: str,
    begidx: int,
    endidx: int,
    arg_state: Any,
    consumed_arg_values: dict[str, list[str]],
    *,
    cmd_set: Any | None = None,
) -> list[str]:
    action = arg_state.action
    choices_callable = action.get_choices_callable()  # type: ignore[attr-defined]
    if action.choices is None and choices_callable is None:
        arg_type = getattr(action, "type", None)

        if isinstance(arg_type, type) and issubclass(arg_type, pathlib.Path):
            results = self._cmd2_app.path_complete(text, line, begidx, endidx)
            return self._format_completions(arg_state, results) if results else []

        enum_values = _enum_choice_values(arg_type)
        if enum_values is not None:
            results = self._cmd2_app.basic_complete(
                text, line, begidx, endidx, enum_values
            )
            return self._format_completions(arg_state, results) if results else []

    return _ORIGINAL_COMPLETE_ARG(
        self,
        text,
        line,
        begidx,
        endidx,
        arg_state,
        consumed_arg_values,
        cmd_set=cmd_set,
    )


argparse_completer.ArgparseCompleter._complete_arg = cast(Any, _patched_complete_arg)


def with_annotated(
    func: F | None = None,
    *,
    preserve_quotes: bool = False,
    with_unknown_args: bool = False,
) -> Any:
    """Build a ``Cmd2ArgumentParser`` from a command function's annotations."""

    def decorator(fn: F) -> Callable[..., Any]:
        if with_unknown_args:
            unknown_param = inspect.signature(fn).parameters.get("_unknown")
            if unknown_param is None:
                raise TypeError(
                    "with_annotated(with_unknown_args=True) requires "
                    "a parameter named _unknown"
                )
            if unknown_param.kind is inspect.Parameter.POSITIONAL_ONLY:
                raise TypeError(
                    "Parameter _unknown must be keyword-compatible "
                    "when with_unknown_args=True"
                )

        command_name = fn.__name__[len(constants.COMMAND_FUNC_PREFIX) :]

        @functools.wraps(fn)
        def cmd_wrapper(*args: Any, **kwargs: Any) -> bool | None:
            cmd2_app, statement_arg = _parse_positionals(args)
            _statement, parsed_arglist = cmd2_app.statement_parser.get_command_arg_list(
                command_name, statement_arg, preserve_quotes
            )

            arg_parser = cmd2_app._command_parsers.get(cmd_wrapper)
            if arg_parser is None:
                raise ValueError(f"No argument parser found for {command_name}")

            try:
                if with_unknown_args:
                    ns, unknown = arg_parser.parse_known_args(parsed_arglist)
                else:
                    ns = arg_parser.parse_args(parsed_arglist)
                    unknown = None
            except SystemExit as exc:
                raise Cmd2ArgparseError from exc

            func_kwargs = unwrap(ns)
            if with_unknown_args:
                func_kwargs["_unknown"] = unknown

            return fn(args[0], **func_kwargs, **kwargs)

        setattr(
            cmd_wrapper,
            constants.CMD_ATTR_ARGPARSER,
            lambda: build_parser(fn, parser_factory=DEFAULT_ARGUMENT_PARSER),
        )
        setattr(cmd_wrapper, constants.CMD_ATTR_PRESERVE_QUOTES, preserve_quotes)

        return cmd_wrapper

    if func is not None:
        return decorator(func)
    return decorator
