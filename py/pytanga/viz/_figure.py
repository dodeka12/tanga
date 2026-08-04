# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Figure-level configuration for exports and live "figure mode".

Provides ``FigureConfig`` — a dataclass that collects all figure-level
parameters (title, target DOM element, annotation, footer, background,
browser window dimensions).  Separate from ``FigureStyle`` which controls
visual presentation (width, height, auto-rotate, overlays, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FigureConfig:
    """Figure-level parameters for exports and live figure mode.

    Separate from ``FigureStyle`` — this holds content and layout
    parameters, while ``FigureStyle`` holds visual presentation
    (canvas size, auto-rotate, overlay visibility, etc.).
    """

    title: str = "Tanga 3D Viewer"
    target: str = "body"  # CSS selector for DOM mount point
    annotation: str | None = None  # markdown text for annotation panel
    footer: str | None = None  # markdown text for footer area
    background: str = "#1a1a2e"  # CSS background for the figure container
    browser_width: int | None = None  # standalone browser window width (px)
    browser_height: int | None = None  # standalone browser window height (px)
    space_dim: int = 3  # 2 or 3

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        result: dict[str, Any] = {
            "title": self.title,
            "target": self.target,
            "background": self.background,
            "space_dim": self.space_dim,
        }
        if self.annotation is not None:
            result["annotation"] = self.annotation
        if self.footer is not None:
            result["footer"] = self.footer
        if self.browser_width is not None:
            result["browser_width"] = self.browser_width
        if self.browser_height is not None:
            result["browser_height"] = self.browser_height
        return result
