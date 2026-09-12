# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Analytic ray-rendering style marker for the standard viewer.

:class:`RayStyle` is a *marker* style: applying it to an entity opts that
entity into analytic ray rendering in the standard viewer (emitted as
``kind:"ray"`` on the wire) instead of the normal mesh or SDF pipeline.

``color``/``opacity`` still resolve through the normal priority chain
(per-entity props > style > canonical > builtin); ``bound_padding`` inflates
the proxy AABB so the analytic surface always stays inside the proxy volume.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import VizStyle


@dataclass
class RayStyle(VizStyle):
    """Opt an entity into analytic ray rendering in the standard viewer.

    Attributes:
        color: Optional override color (CSS hex string or tuple).  ``None``
            uses the normal priority chain.
        opacity: Optional override opacity (0..1).  ``None`` uses the normal
            priority chain.
        bound_padding: Inflate the proxy AABB by this absolute amount so the
            bounding volume always covers the analytic surface (any
            over-estimate is safe; under-estimates clip the surface).
    """

    color: str | None = None
    opacity: float | None = None
    bound_padding: float = 0.05

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "style_type": type(self).__name__,
            "bound_padding": self.bound_padding,
        }
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        return result


@dataclass
class RayQuadricStyle(RayStyle):
    """Ray style for :class:`~pytanga.geometry.Quadric3D` (no extra knobs)."""
