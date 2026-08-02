# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Base style class and wireframe dash pattern dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class VizStyle:
    """Base class for all visualization styles.  Not instantiated directly."""


@dataclass
class WireframeDashPattern:
    """Dash pattern for wireframe overlays.

    When ``dash_size=0``, a solid line is rendered via ``LineBasicMaterial``.
    When ``dash_size > 0``, ``LineDashedMaterial`` is used with the given
    dash and gap sizes.

    Attributes:
        dash_size: Length of each dash segment.  ``0`` = solid line.
        gap_size: Length of each gap between dashes.
        scale: Overall scale factor applied to the pattern.
    """

    dash_size: float = 0.0
    gap_size: float = 0.0
    scale: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "dash_size": self.dash_size,
            "gap_size": self.gap_size,
            "scale": self.scale,
        }


@dataclass
class SolidWireframe(WireframeDashPattern):
    """Solid (unbroken) wireframe lines — the default when ``wireframe_dash`` is ``None``."""

    dash_size: float = 0.0


@dataclass
class DashedWireframe(WireframeDashPattern):
    """Standard dashed wireframe pattern."""

    dash_size: float = 0.005
    gap_size: float = 0.003


@dataclass
class DottedWireframe(WireframeDashPattern):
    """Dotted wireframe (very short dashes)."""

    dash_size: float = 0.0015
    gap_size: float = 0.005
