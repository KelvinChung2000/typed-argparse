"""Signature-to-parser conversion for typed-argparse."""

from __future__ import annotations

import argparse
import decimal
import enum
import inspect
import pathlib
from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeVar, cast, get_type_hints

from .metadata import Argument, Option
from .type_utils import (
    _CollectionStoreAction,
    _make_enum_type,
    _make_literal_type,
    _parse_bool,
    _unwrap_annotation,
    _unwrap_collection,
    _unwrap_literal,
)
from .unwrap import _HANDLER_ATTR

ParserFactory = Callable[..., argparse.ArgumentParser]
F = TypeVar("F", bound=Callable[..., Any])


def _parser_supports_cmd2_keywords(parser: argparse.ArgumentParser) -> bool:
    params = inspect.signature(parser.add_argument).parameters
    return "choices_provider" in params


def _description_from_docstring(func: Callable[..., Any]) -> str | None:
    return inspect.getdoc(func)


def _summary_from_docstring(func: Callable[..., Any]) -> str | None:
    doc = inspect.getdoc(func)
    if not doc:
        return None
    return doc.splitlines()[0]


def _parser_for_function(
    func: Callable[..., Any],
    *,
    parser: argparse.ArgumentParser | None = None,
    parser_factory: ParserFactory | None = None,
) -> argparse.ArgumentParser:
    if parser is not None and parser_factory is not None:
        raise ValueError("Only one of parser and parser_factory may be provided")

    if parser is None:
        factory = parser_factory or argparse.ArgumentParser
        parser = factory(description=_description_from_docstring(func))
    elif parser.description is None:
        parser.description = _description_from_docstring(func)

    return parser


def build_parser(
    func: Callable[..., Any],
    *,
    parser: argparse.ArgumentParser | None = None,
    parser_factory: ParserFactory | None = None,
) -> argparse.ArgumentParser:
    """Inspect a function signature and build a parser from it."""
    parser = _parser_for_function(func, parser=parser, parser_factory=parser_factory)
    supports_cmd2_keywords = _parser_supports_cmd2_keywords(parser)

    sig = inspect.signature(func)
    try:
        hints = get_type_hints(func, include_extras=True)
    except (NameError, AttributeError, TypeError):
        hints = {}

    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        annotation = hints.get(name, param.annotation)
        has_default = param.default is not inspect.Parameter.empty
        default = param.default if has_default else None

        base_type, metadata, is_optional = _unwrap_annotation(annotation)

        inner_type, collection_kind = _unwrap_collection(base_type)
        is_collection = collection_kind is not None
        if is_collection:
            base_type = inner_type

        base_type, literal_choices = _unwrap_literal(base_type)

        if isinstance(metadata, Argument):
            is_positional = True
        elif isinstance(metadata, Option):
            is_positional = False
        elif not has_default and not is_optional:
            is_positional = True
        else:
            is_positional = False

        kwargs: dict[str, Any] = {}

        help_text = metadata.help_text if metadata else None
        if help_text:
            kwargs["help"] = help_text

        metavar = metadata.metavar if metadata else None
        if metavar:
            kwargs["metavar"] = metavar

        if metadata is not None and metadata.has_const:
            kwargs["const"] = metadata.const

        explicit_action = getattr(metadata, "action", None) if metadata else None
        # ``action="append"`` on a list[T] parameter expects per-occurrence
        # single values, not the bulk nargs="+" we infer for ordinary
        # collection parameters. Skipping the collection-nargs branch in that
        # case lets argparse handle each ``--flag value`` invocation correctly,
        # and we forward the action through (later branches only forward
        # ``action`` for bool flags, so do it here for the collection case).
        is_append_collection = is_collection and explicit_action == "append"
        if is_append_collection:
            kwargs["action"] = explicit_action

        explicit_nargs = metadata.nargs if metadata else None
        if explicit_nargs is not None:
            kwargs["nargs"] = explicit_nargs
        elif is_collection and not is_append_collection:
            kwargs["nargs"] = "*" if has_default else "+"
            if collection_kind in ("set", "tuple"):
                kwargs["action"] = _CollectionStoreAction
                kwargs["container_factory"] = set if collection_kind == "set" else tuple
        elif is_positional and has_default:
            # Positional argument with a default value is "optional" in argparse
            # parlance, expressed via ``nargs="?"``. We can infer this whenever the
            # user has explicitly opted into a positional (via ``Argument(...)``) or
            # when the parameter is declared positional with no metadata but does
            # have a default. Without this branch argparse would still treat the
            # argument as required, contradicting the parameter signature.
            kwargs["nargs"] = "?"

        is_bool_flag = False
        if literal_choices is not None:
            kwargs["type"] = _make_literal_type(literal_choices)
            kwargs["choices"] = literal_choices
        elif base_type is bool and not is_collection and not is_positional:
            is_bool_flag = True
            action_str = getattr(metadata, "action", None) if metadata else None
            if action_str:
                kwargs["action"] = action_str
            elif has_default and default is True:
                kwargs["action"] = "store_false"
            else:
                kwargs["action"] = "store_true"
        elif base_type is bool:
            kwargs["type"] = _parse_bool
        elif isinstance(base_type, type) and issubclass(base_type, enum.Enum):
            kwargs["type"] = _make_enum_type(base_type)
        elif base_type is pathlib.Path or (
            isinstance(base_type, type) and issubclass(base_type, pathlib.Path)
        ):
            kwargs["type"] = pathlib.Path
        elif base_type is decimal.Decimal:
            kwargs["type"] = decimal.Decimal
        elif base_type in (int, float, str) and base_type is not str:
            kwargs["type"] = base_type

        if has_default:
            kwargs["default"] = default

        explicit_choices = getattr(metadata, "choices", None)
        if explicit_choices is not None and "choices" not in kwargs:
            kwargs["choices"] = explicit_choices

        if supports_cmd2_keywords:
            choices_provider = getattr(metadata, "choices_provider", None)
            completer_func = getattr(metadata, "completer", None)
            table_columns = getattr(metadata, "table_columns", None)
            suppress_tab_hint = getattr(metadata, "suppress_tab_hint", False)

            if choices_provider:
                kwargs["choices_provider"] = choices_provider
            if completer_func:
                kwargs["completer"] = completer_func
            if table_columns:
                kwargs["descriptive_headers"] = table_columns
            if suppress_tab_hint:
                kwargs["suppress_tab_hint"] = suppress_tab_hint

        if is_positional:
            parser.add_argument(name, **kwargs)
        else:
            option_metadata = metadata if isinstance(metadata, Option) else None
            if option_metadata and option_metadata.names:
                flag_names = list(option_metadata.names)
            else:
                flag_stem = name.replace("_", "-")
                flag_names = [f"--{flag_stem}"]
                if is_bool_flag and has_default and default is True:
                    flag_names = [f"--no-{flag_stem}"]

            if option_metadata and option_metadata.required:
                kwargs["required"] = True

            kwargs["dest"] = name
            parser.add_argument(*flag_names, **kwargs)

    return parser


def build_parser_from_function(
    func: Callable[..., Any],
    *,
    parser: argparse.ArgumentParser | None = None,
    parser_factory: ParserFactory | None = None,
) -> argparse.ArgumentParser:
    """Backward-compatible alias for ``build_parser()``."""
    return build_parser(func, parser=parser, parser_factory=parser_factory)


def build_subcommand_parser(
    commands: Mapping[str, Callable[..., Any]],
    *,
    prog: str | None = None,
    description: str | None = None,
    parser_factory: ParserFactory | None = None,
    dest: str = "command",
) -> argparse.ArgumentParser:
    """Build a subcommand parser from a command-name-to-function mapping."""
    factory = parser_factory or argparse.ArgumentParser
    parser = factory(prog=prog, description=description)
    subparsers = parser.add_subparsers(dest=dest, required=True)

    for name, func in commands.items():
        subparser = subparsers.add_parser(
            name,
            help=_summary_from_docstring(func),
            description=_description_from_docstring(func),
        )
        build_parser(func, parser=subparser)
        subparser.set_defaults(**{_HANDLER_ATTR: func})

    return parser


def call(func: Callable[..., Any], namespace: argparse.Namespace) -> Any:
    """Call a function using keyword arguments extracted from a namespace."""
    from .unwrap import unwrap

    values = unwrap(namespace)
    parameters = inspect.signature(func).parameters

    if any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    ):
        return func(**values)

    accepted_names = {
        name
        for name, parameter in parameters.items()
        if parameter.kind
        in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    }
    filtered_values = {
        name: value for name, value in values.items() if name in accepted_names
    }
    return func(**filtered_values)


def parse_and_call(
    target: Callable[..., Any] | Mapping[str, Callable[..., Any]],
    argv: Sequence[str] | None = None,
    *,
    parser_factory: ParserFactory | None = None,
    prog: str | None = None,
    description: str | None = None,
) -> Any:
    """Parse argv for a function or subcommand mapping and call the result."""
    if callable(target):
        parser = build_parser(
            cast(Callable[..., Any], target),
            parser_factory=parser_factory,
        )
        namespace = parser.parse_args(argv)
        return call(cast(Callable[..., Any], target), namespace)

    parser = build_subcommand_parser(
        target,
        prog=prog,
        description=description,
        parser_factory=parser_factory,
    )
    namespace = parser.parse_args(argv)
    func = getattr(namespace, _HANDLER_ATTR)
    return call(func, namespace)
