# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Style dataclasses for active scene objects.

Provides :class:`ActObjectStyle` (base) and :class:`ActPointStyle`
for controlling the interactive visual feedback of active entities
such as :class:`~pytanga.viz._active.ActPoint`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ActObjectStyle:
    """Base style for all active scene objects.

    Controls hover highlighting and visual emphasis during pointer
    interaction.  All fields default to ``None``; when ``None`` the
    active object uses its own built-in defaults.

    Attributes:
        hover_emissive: CSS colour string for the emissive glow on hover
            (e.g. ``"#ffff44"``).  ``None`` = use per-class default.
        hover_scale: Uniform scale multiplier on hover
            (e.g. ``1.5``).  ``None`` = use per-class default.
    """

    hover_emissive: str | None = None
    hover_scale: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize non-``None`` fields to a JSON-ready dict."""
        result: dict[str, Any] = {}
        if self.hover_emissive is not None:
            result["hover_emissive"] = self.hover_emissive
        if self.hover_scale is not None:
            result["hover_scale"] = self.hover_scale
        return result


@dataclass
class ActPointStyle(ActObjectStyle):
    """Style for :class:`~pytanga.viz._active.ActPoint`.

    Inherits ``hover_emissive`` and ``hover_scale`` from
    :class:`ActObjectStyle`.  Additional point-specific interactive
    style fields can be added here.
    """