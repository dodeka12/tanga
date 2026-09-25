# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""serve-smoke.py — headless Tanga server for the Playwright reconciliation smoke.

Builds a two-``SceneView("world")`` layout (a calibrated 2D camera view with a
random-noise background image + a default 3D overview) and a toolbar with "Swap
panes" and "New noise" buttons, then serves it on a free port **without opening
a browser**.  Run this first, then:

    node js/dev/tests/reconcile-smoke.mjs <printed-url>

Run with:  uv run python js/dev/tests/serve-smoke.py
"""

from typing import Any

import numpy as np

from pytanga.geometry import Frustum, Point, Sphere
from pytanga.viz import (
    ButtonView,
    CameraAction,
    CameraView,
    ControlEvent,
    ImageData,
    MouseButton,
    PointStyle,
    SceneView,
    SphereStyle,
    SplitView,
    ToolbarView,
    ViewportConfig,
    Visualizer,
    pinhole_camera,
)

WIDTH, HEIGHT = 640, 480
_K = np.array([[500.0, 0.0, 320.0], [0.0, 500.0, 240.0], [0.0, 0.0, 1.0]])
_R = np.diag([1.0, -1.0, -1.0])
_T = np.array([0.0, 0.0, 6.0])
_WORLD_POINTS = [
    (0.5, 0.3, 0.2),
    (-0.4, 0.2, 0.1),
    (0.2, -0.5, -0.3),
    (-0.6, -0.3, 0.4),
]


def _noise(rng: np.random.Generator) -> ImageData:
    return ImageData(
        "camera",
        data=rng.integers(0, 256, size=(HEIGHT, WIDTH, 3), dtype=np.uint8),
    )


def main() -> None:
    rng = np.random.default_rng()
    viz = Visualizer(
        title="Tanga — reconcile smoke",
        add_default_axes=False,
        add_default_grid=False,
    )
    world = viz.scene("world")

    for xyz in _WORLD_POINTS:
        world.new(Point(*xyz), color="#44ff44", style=PointStyle(size=0.08))
    world.new(
        Sphere(Point(0.0, 0.0, 0.0), radius=0.8),
        color="#4488ff",
        opacity=0.4,
        style=SphereStyle(wireframe=True),
    )

    cam = pinhole_camera(_K, _R, _T, image_size=(WIDTH, HEIGHT))
    frustum_ref = world.new(
        Frustum.from_camera(cam, near=0.5, far=6.0), color="#ffcc44"
    )

    cam_view = CameraView(
        cam,
        navigation="2d",
        controls={MouseButton.LEFT: CameraAction.PAN},
        viewport=ViewportConfig(zoom=1.0, pan=(0.0, 0.0)),
        background_image=_noise(rng),
    )
    left = SceneView("world", camera_view=cam_view, hide={frustum_ref.id})
    right = SceneView("world")
    body = SplitView("horizontal", [left, right])

    async def _on_swap(_value: Any, _event: ControlEvent) -> None:
        body.children.reverse()
        viz.set_layout(layout)

    async def _on_noise(_value: Any, _event: ControlEvent) -> None:
        viz.set_background_image(left, _noise(rng))

    toolbar = ToolbarView(
        [
            ButtonView("btn_swap", label="Swap panes", on_click=_on_swap),
            ButtonView("btn_noise", label="New noise", on_click=_on_noise),
        ]
    )
    layout = SplitView("vertical", [toolbar, body])

    viz.set_layout(layout, name="demo")
    viz.start_server(host="localhost", port=0)
    print(f"SMOKE_URL={viz.url}", flush=True)
    viz.wait()


if __name__ == "__main__":
    main()
