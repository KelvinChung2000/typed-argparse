"""Metadata classes for annotation-driven parser generation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class _BaseArgMetadata:
    """Shared fields for ``Argument`` and ``Option`` metadata."""

    def __init__(
        self,
        *,
        help_text: str | None = None,
        metavar: str | None = None,
        nargs: int | str | tuple[int, ...] | None = None,
        choices: list[Any] | None = None,
        choices_provider: Callable[..., Any] | None = None,
        completer: Callable[..., Any] | None = None,
        table_columns: tuple[str, ...] | None = None,
        suppress_tab_hint: bool = False,
    ) -> None:
        self.help_text = help_text
        self.metavar = metavar
        self.nargs = nargs
        self.choices = choices
        self.choices_provider = choices_provider
        self.completer = completer
        self.table_columns = table_columns
        self.suppress_tab_hint = suppress_tab_hint


class Argument(_BaseArgMetadata):
    """Metadata for a positional argument in an ``Annotated`` type hint."""


class Option(_BaseArgMetadata):
    """Metadata for an optional/flag argument in an ``Annotated`` type hint."""

    def __init__(
        self,
        *names: str,
        action: str | None = None,
        required: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.names = names
        self.action = action
        self.required = required
