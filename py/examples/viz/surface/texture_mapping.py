# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""texture_mapping.py — Switch between standard and custom surface texture mapping.

Shows a sphere, a plane, a box, and a cylinder side by side, all textured with
the same surface material.  A dropdown switches, at runtime, between the
**standard** texture map (the first texture, lit by the global scene lighting)
and a **custom** GLSL shader that twirls a second texture — visibly different
from a straight texture sample.  A slider (enabled only for the custom shader)
controls the twirl amount.  Both paths share the scene-lighting uniforms
documented in :mod:`pytanga.viz.surface`.

Run with:  uv run python py/examples/viz/surface/texture_mapping.py

Keywords: surface, texture mapping, shader, checkerboard, gradient, lighting
"""

from __future__ import annotations

from typing import Any

import numpy as np

from pytanga.geometry import Box, Cylinder, Direction, Plane, Point, Sphere
from pytanga.viz import (
    ControlEvent,
    DropdownView,
    GroupView,
    ImageData,
    SceneView,
    SliderView,
    SplitView,
    SurfaceMaterial,
    SurfaceShader,
    SurfaceTexture,
    Visualizer,
    VizObjectRef,
)


def _gradient(size: int = 256) -> np.ndarray:
    """A ``size×size×3`` uint8 red→green→blue diagonal gradient."""
    ys, xs = np.mgrid[0:size, 0:size]
    u = (xs + ys) / (2.0 * max(size - 1, 1))
    r = (u * 255).astype(np.uint8)
    g = ((1.0 - abs(u - 0.5) * 2.0) * 255).astype(np.uint8)
    b = ((1.0 - u) * 255).astype(np.uint8)
    return np.stack([r, g, b], axis=-1)


def _checker(size: int = 256, cells: int = 8) -> np.ndarray:
    """A ``size×size×3`` uint8 black/white checkerboard."""
    ys, xs = np.mgrid[0:size, 0:size]
    c = ((xs // (size // cells)) + (ys // (size // cells))) % 2
    val = (c * 255).astype(np.uint8)
    return np.stack([val, val, val], axis=-1)


# The custom fragment must define `surfaceColor` and may reference the host
# varyings/lighting (`vUv`, `tangaLight`, …).  Samplers are declared by the host
# from each `SurfaceTexture.uniform`; do not redeclare them here.  The twirl
# distorts the texture in a way the standard texture map cannot.
_CUSTOM_FRAGMENT = """
uniform vec3 u_tint;
uniform float u_twirl;

vec3 surfaceColor(vec3 baseColor, vec3 n, vec3 p) {
    vec2 uv = vUv - 0.5;
    float radius = length(uv);
    float angle = atan(uv.y, uv.x) + (0.5 - radius) * u_twirl;
    vec2 twirled = 0.5 + vec2(cos(angle), sin(angle)) * radius;
    vec3 albedo = texture2D(uTexture, twirled).rgb * u_tint;
    return tangaLight(albedo, n, p);
}
"""


def main() -> None:
    viz = Visualizer(title="Tanga — Surface texture mapping")

    gradient = ImageData("surface.gradient", data=_gradient())
    checker = ImageData("surface.checker", data=_checker())

    standard = SurfaceMaterial(textures=[SurfaceTexture(image=gradient)])
    mode = "standard"
    twirl = 4.0

    def _custom_material() -> SurfaceMaterial:
        return SurfaceMaterial(
            shader=SurfaceShader(
                "twirl",
                _CUSTOM_FRAGMENT,
                uniforms={"u_tint": [0.7, 0.9, 1.3], "u_twirl": twirl},
            ),
            textures=[SurfaceTexture(image=checker, uniform="uTexture")],
        )

    def _current_material() -> SurfaceMaterial:
        return _custom_material() if mode == "custom" else standard

    entities: list[tuple[str, Any]] = [
        ("sphere", Sphere(Point(-4.5, 0.0, 0.0), 1.2)),
        ("plane", Plane(Point(-1.5, 0.0, 0.0), Direction(0.0, 0.0, 1.0), extent=1.4)),
        ("box", Box(Point(1.5, 0.0, 0.0), size=(1.6, 1.6, 1.6))),
        (
            "cylinder",
            Cylinder(
                origin=Point(4.5, 0.0, 0.0),
                axis=Direction(0.0, 1.0, 0.0),
                length=2.4,
                radius=0.9,
                align_center=0.5,
            ),
        ),
    ]

    refs: dict[str, VizObjectRef] = {}

    def _apply() -> None:
        material = _current_material()
        for name, entity in entities:
            refs[name] = viz.new(
                entity, entity_id=f"surface_{name}", surface=material, label=name
            )

    _apply()

    async def _on_mode_change(value: Any, _event: ControlEvent) -> None:
        nonlocal mode
        mode = str(value)
        viz.set_control_enabled("twirl", mode == "custom")
        _apply()
        await viz.flush_async()

    async def _on_twirl(value: Any, _event: ControlEvent) -> None:
        nonlocal twirl
        twirl = float(value)
        if mode == "custom":
            # Queue the shader parameter changes, then flush them together.
            for name, _entity in entities:
                refs[name].set_surface_uniform("u_twirl", twirl)
            await viz.flush_async()

    mode_control = DropdownView(
        "surface_mode",
        label="Surface",
        options=["standard", "custom"],
        value="standard",
        on_change=_on_mode_change,
    )
    twirl_control = SliderView(
        "twirl",
        label="Twirl",
        min=0.0,
        max=8.0,
        step=0.1,
        value=twirl,
        on_change=_on_twirl,
    )
    twirl_control.control.enabled = False  # disabled until "custom" is selected

    layout = SplitView(
        orientation="horizontal",
        children=[GroupView("Surface", [mode_control, twirl_control]), SceneView("")],
    )

    viz.show(layout=layout)
    viz.wait()


if __name__ == "__main__":
    main()
