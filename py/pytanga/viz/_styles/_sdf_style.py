# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""SDF rendering style marker for the standard viewer.

:class:`SdfStyle` is a *marker* style: applying it to an entity opts that
entity into smooth ray-marched signed-distance-field rendering in the standard
viewer (emitted as ``kind:"sdf"`` on the wire) instead of the normal
vertex/mesh pipeline.

``color``/``opacity`` still resolve through the normal priority chain
(per-entity props > style > canonical > builtin); the remaining fields are
SDF-specific knobs with concrete defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import VizStyle


@dataclass
class SdfStyle(VizStyle):
    """Opt an entity into ray-marched SDF rendering in the standard viewer.

    Attributes:
        color: Optional override color (CSS hex string or tuple).  ``None``
            uses the normal priority chain.
        opacity: Optional override opacity (0..1).  ``None`` uses the normal
            priority chain.
        soft_shadows: Enable soft self-shadowing in the ray-marcher.
        max_steps: Ray-march step budget.
        bound_padding: Inflate the proxy AABB by this absolute amount so the
            marching volume always covers the surface (any over-estimate is
            safe; under-estimates clip the surface).
    """

    color: str | None = None
    opacity: float | None = None
    soft_shadows: bool = True
    max_steps: int = 256
    bound_padding: float = 0.05

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "style_type": "SdfStyle",
            "soft_shadows": self.soft_shadows,
            "max_steps": self.max_steps,
            "bound_padding": self.bound_padding,
        }
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        return result
