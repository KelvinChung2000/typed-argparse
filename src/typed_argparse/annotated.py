"""Compatibility exports for the typed-argparse public surface."""

from __future__ import annotations

from . import type_utils as _type_utils
from .builder import build_parser, build_parser_from_function
from .metadata import Argument, Option

_CollectionStoreAction = _type_utils._CollectionStoreAction
_make_enum_type = _type_utils._make_enum_type
_unwrap_optional = _type_utils._unwrap_optional

__all__ = [
    "Argument",
    "Option",
    "build_parser",
    "build_parser_from_function",
]
