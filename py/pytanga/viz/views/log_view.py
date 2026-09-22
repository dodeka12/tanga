# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The :class:`LogView` live two-column log pane."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ._base import View
from ._helpers import _log_view_counter
from .._size import Size, SizeSpec


class LogView(View):
    """A live two-column (time | message) log rendered as a scrollable ``View``.

    Lines are appended from the backend via :meth:`log` and pushed to the
    frontend as ``log_update`` messages.  Each line is a dict with a UTC
    ``"time"`` key; string messages are stored under ``"message"`` and dict
    messages have their keys folded in.

    ``id`` is an optional stable identifier (auto-generated as ``"logN"`` when
    omitted); it is the key used to address this view at runtime.  ``max_history``
    caps the retained line count (FIFO drop-oldest); ``None`` keeps everything.

    The first column is formatted from the stored UTC ISO-8601 timestamp,
    converted to the browser's local timezone.  By default only the time-of-day
    with microseconds is shown; ``show_date`` adds the date and
    ``show_utc_offset`` adds the local offset to UTC (e.g. ``+02:00``).
    """

    _node_type = "log_view"

    def __init__(
        self,
        id: str | None = None,
        *,
        max_history: int | None = None,
        show_date: bool = False,
        show_utc_offset: bool = False,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = Size.px(200),
        min_height: SizeSpec = Size.px(120),
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.id = id if id is not None else f"log{next(_log_view_counter)}"
        if max_history is not None and (
            not isinstance(max_history, int) or max_history < 0
        ):
            raise ValueError("max_history must be None or a non-negative integer")
        self.max_history = max_history
        self.show_date = show_date
        self.show_utc_offset = show_utc_offset
        self.lines: list[dict[str, Any]] = []
        self._push = None  # callback slot injected by the Visualizer

    def log(self, message: Any) -> None:
        """Append *message* as a new line (str → ``{"message": …}``; dict → folded)."""
        line: dict[str, Any] = {"time": datetime.now(timezone.utc).isoformat()}
        if isinstance(message, dict):
            line.update(message)
        else:
            line["message"] = str(message)
        self.lines.append(line)
        if self.max_history is not None and len(self.lines) > self.max_history:
            del self.lines[: len(self.lines) - self.max_history]
        if self._push is not None:
            self._push(self.id, "append", [dict(line)])

    def get_log(self) -> list[dict[str, Any]]:
        """Return a copy of the current lines."""
        return [dict(line) for line in self.lines]

    def write_file(self, path: str | Path) -> None:
        """Write the current lines as JSON lines (one dict per line)."""
        Path(path).write_text(
            "".join(json.dumps(line) + "\n" for line in self.lines),
            encoding="utf-8",
        )

    def load_file(self, path: str | Path) -> None:
        """Replace the current lines with those read from a JSON-lines file."""
        raw = Path(path).read_text(encoding="utf-8")
        lines = [json.loads(line) for line in raw.splitlines() if line.strip()]
        if self.max_history is not None:
            lines = lines[-self.max_history :]
        self.lines = lines
        if self._push is not None:
            self._push(self.id, "replace", [dict(line) for line in self.lines])

    def clear(self) -> None:
        """Drop every line."""
        self.lines = []
        if self._push is not None:
            self._push(self.id, "clear")

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["id"] = self.id
        result["max_history"] = self.max_history
        result["show_date"] = self.show_date
        result["show_utc_offset"] = self.show_utc_offset
        result["lines"] = [dict(line) for line in self.lines]
        return result
