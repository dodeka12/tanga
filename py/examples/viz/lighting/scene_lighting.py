# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""scene_lighting.py — One lighting config for mesh, SDF, and depth-surface objects.

Places three objects side by side — a vertex/mesh sphere (standard
``MeshPhongMaterial``), a ray-marched SDF cylinder, and a 2.5D depth surface of
a 2D sine wave (``"plain"`` mode, Blinn-Phong shaded) — and drives them all from
a single per-scene :class:`~pytanga.viz.SceneLighting`.  A lighting-preset
dropdown calls :meth:`~pytanga.viz.Visualizer.set_scene_lighting` at runtime,
re-lighting all three at once from the same configuration.

Run with:  uv run python py/examples/viz/lighting/scene_lighting.py

Keywords: scene lighting, SDF, depth image, sphere, cylinder, mesh
"""

from __future__ import annotations

from typing import Any

import numpy as np
from pytanga.geometry import Cylinder, Direction, Point, Sphere
from pytanga.viz import (
    ControlEvent,
    DepthImage,
    DepthImageData,
    DepthImageStyle,
    DirectionalLightSpec,
    DropdownView,
    GroupView,
    LightSpec,
    SceneLighting,
    SceneView,
    SdfCylinderStyle,
    SplitView,
    Visualizer,
)
from pytanga.viz.sdf import SdfObject


def _sin_depth(width: int, height: int) -> np.ndarray:
    """A normalized ``[0, 1]`` depth map from phase-shifted 2D sines."""
    ys, xs = np.mgrid[0:height, 0:width]
    u = xs / max(width - 1, 1)
    v = ys / max(height - 1, 1)
    return (
        np.sin(2.0 * np.pi * 3.0 * u + 0.3) * np.sin(2.0 * np.pi * 5.0 * v + 1.1) + 1.0
    ) / 2.0


_PRESETS: dict[str, SceneLighting] = {
    "default": SceneLighting(),
    "warm": SceneLighting(
        ambient=LightSpec(color="#ffd9b3", intensity=0.5),
        lights=(
            DirectionalLightSpec(
                direction=(1.0, 1.0, 1.0), color="#ffddbb", intensity=0.9
            ),
            DirectionalLightSpec(
                direction=(-1.0, -0.5, -1.0), color="#88aaff", intensity=0.3
            ),
        ),
    ),
    "cool": SceneLighting(
        ambient=LightSpec(color="#b3c6ff", intensity=0.5),
        lights=(
            DirectionalLightSpec(
                direction=(1.0, 1.0, 1.0), color="#ccddff", intensity=0.9
            ),
            DirectionalLightSpec(
                direction=(-1.0, -0.5, -1.0), color="#ffcc88", intensity=0.3
            ),
        ),
    ),
    "single top": SceneLighting(
        ambient=LightSpec(color="#ffffff", intensity=0.2),
        lights=(
            DirectionalLightSpec(
                direction=(0.0, 1.0, 0.0), color="#ffffff", intensity=1.2
            ),
        ),
    ),
    "dramatic side": SceneLighting(
        ambient=LightSpec(color="#ffffff", intensity=0.1),
        lights=(
            DirectionalLightSpec(
                direction=(1.0, 0.0, 0.2), color="#ffffff", intensity=1.5
            ),
        ),
    ),
}


def main() -> None:
    viz = Visualizer(
        title="Tanga — Scene lighting (mesh / SDF / depth)",
        add_default_grid=False,
    )

    # 1. Mesh sphere — standard vertex/mesh pipeline (MeshPhongMaterial).
    viz.add(Sphere(Point(-3.0, 0.0, 0.0), 1.0), color="#ff8844", label="sphere (mesh)")

    # 2. SDF cylinder — ray-marched solid.
    viz.add(
        SdfObject(
            Cylinder(
                origin=Point(0.0, 0.0, 0.0),
                axis=Direction(0.0, 0.0, 1.0),
                length=2.0,
                radius=0.6,
                align_center=0.5,
            ),
            style=SdfCylinderStyle(color="#44aaff"),
        ),
        label="cylinder (SDF)",
    )

    # 3. Depth surface of a 2D sine wave — plain mode, Blinn-Phong shaded.
    depth = _sin_depth(64, 64).astype(np.float32)
    depth_ref = viz.new(
        DepthImage(DepthImageData(depth=depth)),
        style=DepthImageStyle(
            render_mode="plain",
            color="#66cc99",
            world_scale=0.03,
            depth_scale=1.5,
            shininess=48.0,
            specular="#ffffff",
        ),
        label="depth surface (plain)",
    )
    depth_ref.set_transform(position=(3.0, 0.0, 0.0))

    async def _on_lighting_change(value: Any, _event: ControlEvent) -> None:
        viz.set_scene_lighting(_PRESETS.get(str(value), _PRESETS["default"]))

    lighting = DropdownView(
        "lighting",
        label="Lighting",
        options=list(_PRESETS),
        value="default",
        on_change=_on_lighting_change,
    )

    layout = SplitView(
        orientation="horizontal",
        children=[
            GroupView("Scene lighting", [lighting]),
            SceneView(""),
        ],
    )

    viz.show(layout=layout)
    viz.wait()


if __name__ == "__main__":
    main()
