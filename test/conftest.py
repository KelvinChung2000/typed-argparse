"""Test helpers for typed-argparse."""

from __future__ import annotations

import sys
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import cmd2
import cmd2.cmd2 as cmd2_module

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _split_output(buffer) -> list[str]:
    value = buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)
    return [line for line in value.splitlines() if line]


def run_cmd(app, command: str) -> tuple[list[str], list[str]]:
    """Execute a command and capture stdout/stderr lines."""
    if not hasattr(app, "stderr"):
        app.stderr = cmd2.utils.StdSim(sys.stderr)
    stderr_capture = StringIO()
    with redirect_stderr(stderr_capture):
        app.onecmd_plus_hooks(command)

    stderr_lines = _split_output(app.stderr)
    stderr_lines.extend(line for line in stderr_capture.getvalue().splitlines() if line)
    return _split_output(app.stdout), stderr_lines


def complete_cmd(app, line: str, text: str) -> list[str]:
    """Collect all completions for a line using cmd2's readline-style API."""
    begidx = len(line) - len(text)
    endidx = len(line)
    results: list[str] = []

    with (
        patch.object(
            cmd2_module,
            "readline",
            new=SimpleNamespace(
                get_line_buffer=lambda: line,
                get_begidx=lambda: begidx,
                get_endidx=lambda: endidx,
            ),
            create=True,
        ),
        patch.object(cmd2_module, "rl_force_redisplay", return_value=None, create=True),
    ):
        state = 0
        while True:
            completion = app.complete(text, state)
            if completion is None:
                break
            results.append(completion.rstrip())
            state += 1

    return results
