"""Type-unwrapping and converter helpers for parser generation."""

from __future__ import annotations

import argparse
import enum
import types
from collections.abc import Callable, Collection, Sequence
from typing import Annotated, Any, Literal, Union, cast, get_args, get_origin

from .metadata import Argument, Option

_NoneType = type(None)

_BOOL_TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
_BOOL_FALSE_VALUES = {"0", "false", "f", "no", "n", "off"}


def _parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in _BOOL_TRUE_VALUES:
        return True
    if lowered in _BOOL_FALSE_VALUES:
        return False
    valid_values = "1, 0, true, false, yes, no, on, off"
    raise argparse.ArgumentTypeError(
        f"invalid boolean value: {value!r} (choose from: {valid_values})"
    )


def _make_literal_type(literal_values: list[Any]) -> Callable[[str], Any]:
    value_map = {str(value): value for value in literal_values}

    def _convert(value: str) -> Any:
        if value in value_map:
            return value_map[value]
        if value.lower() in _BOOL_TRUE_VALUES:
            bool_value = True
        elif value.lower() in _BOOL_FALSE_VALUES:
            bool_value = False
        else:
            bool_value = None

        if bool_value is not None and bool_value in literal_values:
            return bool_value

        valid = ", ".join(str(v) for v in literal_values)
        raise argparse.ArgumentTypeError(
            f"invalid choice: {value!r} (choose from {valid})"
        )

    converter = cast(Any, _convert)
    converter.__name__ = "literal"
    return cast(Callable[[str], Any], converter)


class _CollectionStoreAction(argparse._StoreAction):
    """Store action that can coerce parsed collection values to a container type."""

    def __init__(
        self,
        *args: Any,
        container_factory: Callable[[list[Any]], Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._container_factory = container_factory

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        result = values
        if self._container_factory is not None and isinstance(values, list):
            result = self._container_factory(values)
        _ = parser, option_string
        setattr(namespace, self.dest, result)


def _make_enum_type(enum_class: type[enum.Enum]) -> Callable[[str], enum.Enum]:
    _value_map = {str(m.value): m for m in enum_class}

    def _convert(value: str) -> enum.Enum:
        member = _value_map.get(value)
        if member is not None:
            return member
        try:
            return enum_class[value]
        except KeyError as err:
            valid = ", ".join(_value_map)
            raise argparse.ArgumentTypeError(
                f"invalid choice: {value!r} (choose from {valid})"
            ) from err

    converter = cast(Any, _convert)
    converter.__name__ = enum_class.__name__
    converter._cmd2_enum_class = enum_class
    return cast(Callable[[str], enum.Enum], converter)


def _unwrap_type(annotation: Any) -> tuple[Any, Argument | Option | None]:
    if get_origin(annotation) is Annotated:
        args = get_args(annotation)
        base_type = args[0]
        for meta in args[1:]:
            if isinstance(meta, (Argument, Option)):
                return base_type, meta
        return base_type, None
    return annotation, None


def _unwrap_annotation(
    annotation: Any,
) -> tuple[Any, Argument | Option | None, bool]:
    metadata: Argument | Option | None = None
    is_optional = False
    current = annotation

    while True:
        unwrapped_type, unwrapped_metadata = _unwrap_type(current)
        if unwrapped_metadata is not None:
            metadata = unwrapped_metadata
            current = unwrapped_type
            continue

        unwrapped_optional, optional = _unwrap_optional(current)
        if optional:
            is_optional = True
            current = unwrapped_optional
            continue

        return current, metadata, is_optional


def _unwrap_optional(tp: Any) -> tuple[Any, bool]:
    origin = get_origin(tp)
    if origin is Union or origin is types.UnionType:
        args = [a for a in get_args(tp) if a is not _NoneType]
        if len(args) == 1:
            return args[0], True
    return tp, False


def _unwrap_collection(tp: Any) -> tuple[Any, str | None]:
    origin = get_origin(tp)
    if origin is list:
        args = get_args(tp)
        if args:
            return args[0], "list"

    if origin is set:
        args = get_args(tp)
        if args:
            return args[0], "set"

    if origin is Collection:
        args = get_args(tp)
        if args:
            return args[0], "collection"

    if origin is tuple:
        args = get_args(tp)
        if len(args) == 2 and args[1] is Ellipsis:
            return args[0], "tuple"
    return tp, None


def _unwrap_literal(tp: Any) -> tuple[Any, list[Any] | None]:
    if get_origin(tp) is Literal:
        literal_values = list(get_args(tp))
        if not literal_values:
            return Any, []
        first_type = type(literal_values[0])
        if all(type(v) is first_type for v in literal_values):
            return first_type, literal_values
        return Any, literal_values
    return tp, None
