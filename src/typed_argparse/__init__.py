"""typed-argparse public API."""

from __future__ import annotations

from typing import Any

from .annotated import Argument, Option
from .builder import (
    build_parser,
    build_parser_from_function,
    build_subcommand_parser,
    call,
    parse_and_call,
)
from .unwrap import unwrap

__all__ = [
    "Argument",
    "Option",
    "build_parser",
    "build_parser_from_function",
    "build_subcommand_parser",
    "call",
    "parse_and_call",
    "unwrap",
    "with_annotated",
]

__version__ = "0.0.0"


def with_annotated(*args: Any, **kwargs: Any) -> Any:
    """Lazy cmd2 integration entry point."""
    try:
        from .integrations.cmd2 import with_annotated as impl
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on optional extra
        raise ModuleNotFoundError(
            "typed_argparse.with_annotated requires the optional cmd2 extra. "
            "Install it with `typed-argparse[cmd2]`."
        ) from exc

    return impl(*args, **kwargs)
