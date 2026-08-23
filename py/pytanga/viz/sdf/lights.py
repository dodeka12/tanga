# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Light sources for the SDF viewer.

The ray-marcher shades each surface hit with a configurable ambient term plus a
set of directional lights (infinitely distant lights, the only kind the shader
currently supports). Lights are added with :meth:`SdfVisualizer.add`; the
ambient term is set with :meth:`SdfVisualizer.set_ambient_light`.

The built-in default reproduces the historical hardcoded look: a white
directional light from ``(10, 20, 10)`` at intensity ``0.8`` plus a white
``0.45`` ambient term.
"""

from __future__ import annotations

import math
from typing import Any


class Light:
    """Marker base class for SDF light sources."""


def _normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = float(v[0]), float(v[1]), float(v[2])
    length = math.sqrt(x * x + y * y + z * z)
    if length < 1e-12:
        return (0.0, 0.0, 1.0)
    return (x / length, y / length, z / length)


class DirectionalLight(Light):
    """An infinitely distant light shining from ``direction``.

    ``direction`` points from the scene toward the light (equivalently, the
    direction the light comes from); it is normalized on assignment. ``color``
    is a CSS hex string and ``intensity`` scales the light's diffuse
    contribution.
    """

    def __init__(
        self,
        direction: tuple[float, float, float] = (10.0, 20.0, 10.0),
        color: str = "#ffffff",
        intensity: float = 0.8,
    ) -> None:
        self.direction = direction  # normalizes via the property setter
        self.color = color
        self.intensity = float(intensity)

    @property
    def direction(self) -> tuple[float, float, float]:
        return self._direction

    @direction.setter
    def direction(self, value: tuple[float, float, float]) -> None:
        self._direction = _normalize(value)


def serialize_light(light: Light) -> dict[str, Any]:
    """Serialize a light to its wire form (shared with the frontend)."""
    if isinstance(light, DirectionalLight):
        return {
            "kind": "directional",
            "direction": list(light.direction),
            "color": light.color,
            "intensity": light.intensity,
        }
    raise TypeError(f"SDF viewer does not support light {type(light).__name__!r}")
