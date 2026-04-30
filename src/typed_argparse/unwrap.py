"""Helpers for converting parsed namespaces into call-friendly values."""

from __future__ import annotations

import argparse
from typing import Any, overload

_INTERNAL_ATTR_PREFIX = "_typed_argparse_"
_HANDLER_ATTR = f"{_INTERNAL_ATTR_PREFIX}handler"
_CMD2_SUBCOMMAND_HANDLER = "__subcmd_handler__"


@overload
def unwrap(namespace: argparse.Namespace, *, as_tuple: bool = False) -> dict[str, Any]:
    ...


@overload
def unwrap(
    namespace: argparse.Namespace, *, as_tuple: bool
) -> dict[str, Any] | tuple[Any, ...]:
    ...


def unwrap(
    namespace: argparse.Namespace,
    *,
    as_tuple: bool = False,
) -> dict[str, Any] | tuple[Any, ...]:
    """Convert a parsed namespace into plain Python values.

    By default this returns a ``dict[str, Any]`` suitable for use with
    ``func(**unwrap(namespace))``.

    When ``as_tuple=True``, this returns the namespace values as a tuple in the
    namespace's insertion order, after filtering internal ``cmd2`` fields.
    """
    values: dict[str, Any] = {}
    for key, value in vars(namespace).items():
        if (
            key.startswith("cmd2_")
            or key.startswith(_INTERNAL_ATTR_PREFIX)
            or key == _CMD2_SUBCOMMAND_HANDLER
        ):
            continue
        values[key] = value

    if as_tuple:
        return tuple(values.values())
    return values
