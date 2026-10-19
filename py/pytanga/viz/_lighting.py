# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Scene lighting model for the Tanga 3D viewer.

Defines a small value-object hierarchy — :class:`LightSpec` (a color +
intensity), :class:`DirectionalLightSpec` (a direction + the shared color and
intensity), and :class:`SceneLighting` (an ambient light plus a tuple of
directional lights) — that serializes into the ``scene_config.lighting`` block
sent to the browser.

Lighting is in **world space** and each directional ``direction`` is a unit
vector pointing **toward** the light (``NdotL = dot(N, direction)``).  The
frontend normalizes non-unit directions, so callers may pass unnormalized
vectors; the canonical :data:`DEFAULT_SCENE_LIGHTING` stores pre-normalized
components that mirror the historical hardcoded lights in
``three-view.js``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: Unit vector toward the first directional light, ``normalize((10, 20, 10))``.
_DEFAULT_LIGHT1_DIR: tuple[float, float, float] = (
    0.408248290463863,
    0.816496580927726,
    0.408248290463863,
)

#: Unit vector toward the second directional light, ``normalize((-5, -2, -8))``.
_DEFAULT_LIGHT2_DIR: tuple[float, float, float] = (
    -0.5184758473652127,
    -0.20739033894608505,
    -0.8295613557843402,
)


@dataclass(frozen=True)
class LightSpec:
    """A light's color and intensity (the shared base for directional lights).

    Attributes:
        color: Hex color string (e.g. ``"#ffffff"``).
        intensity: Unitless multiplier applied to ``color``.
    """

    color: str = "#ffffff"
    intensity: float = 1.0


@dataclass(frozen=True)
class DirectionalLightSpec(LightSpec):
    """A directional light: a direction plus :class:`LightSpec` color/intensity.

    Attributes:
        direction: Unit vector pointing **toward** the light (world space).  May
            be unnormalized; the frontend normalizes it.
    """

    direction: tuple[float, float, float] = (0.0, 0.0, 1.0)


def _default_ambient() -> LightSpec:
    """The canonical ambient light (white @ ``0.5``)."""
    return LightSpec(intensity=0.5)


def _default_lights() -> tuple[DirectionalLightSpec, ...]:
    """The canonical two directional lights (mirroring ``_addDefaultLights``)."""
    return (
        DirectionalLightSpec(direction=_DEFAULT_LIGHT1_DIR, intensity=0.8),
        DirectionalLightSpec(direction=_DEFAULT_LIGHT2_DIR, intensity=0.3),
    )


@dataclass(frozen=True)
class SceneLighting:
    """Per-scene lighting: an ambient light plus directional lights.

    Attributes:
        ambient: Ambient light (default white @ ``0.5``).
        lights: Directional lights (default the two historical default lights).
    """

    ambient: LightSpec = field(default_factory=_default_ambient)
    lights: tuple[DirectionalLightSpec, ...] = field(default_factory=_default_lights)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the ``scene_config.lighting`` wire shape."""
        return {
            "ambient": {
                "color": self.ambient.color,
                "intensity": self.ambient.intensity,
            },
            "lights": [
                {
                    "direction": list(light.direction),
                    "color": light.color,
                    "intensity": light.intensity,
                }
                for light in self.lights
            ],
        }


#: The default scene lighting, mirroring the historical hardcoded frontend lights.
DEFAULT_SCENE_LIGHTING = SceneLighting()
