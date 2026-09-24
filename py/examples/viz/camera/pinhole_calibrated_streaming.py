# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pinhole_calibrated_streaming.py — a live-updated camera view + pane swap.

Streams a new random-noise background image into a calibrated 2D camera pane at
4 fps (via ``Visualizer.set_background_image``, which updates only that pane —
no full layout re-push), while a toolbar button above the panes swaps the
left/right panes at runtime.  Because both ``SceneView`` panes are kept as
persistent objects, the swap re-uses (re-attaches) the WebGL panes instead of
tearing them down and rebuilding them.

Layout:

- **top** — a ``ToolbarView`` with a "Swap panes" button;
- **bottom** — a horizontal ``SplitView`` of two panes of one ``"world"`` scene:
  - **left** — the calibrated camera view (``navigation="2d"``) drawn over a
    random-noise full-viewport NDC background, with the frustum hidden;
  - **right** — the same scene with the default camera, showing the camera's
    :class:`~pytanga.geometry.Frustum`.

Run with:  uv run python py/examples/viz/camera/pinhole_calibrated_streaming.py

Keywords: camera, pinhole, calibration, frustum, image background, streaming, split view, pane swap
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
K = np.array([[500.0, 0.0, 320.0], [0.0, 500.0, 240.0], [0.0, 0.0, 1.0]])
# Upright camera (y up): flip the OpenCV y-down axis and the forward (z) axis.
R = np.diag([1.0, -1.0, -1.0])
T = np.array([0.0, 0.0, 6.0])  # camera centre at (0, 0, 6), looking toward -z

# World points near the origin, in front of the camera (6 - z > 0).
_WORLD_POINTS = [
    (0.5, 0.3, 0.2),
    (-0.4, 0.2, 0.1),
    (0.2, -0.5, -0.3),
    (-0.6, -0.3, 0.4),
]


def _noise(rng: np.random.Generator) -> ImageData:
    """A fresh random-noise ``ImageData`` at the camera's native resolution."""
    return ImageData(
        "camera",
        data=rng.integers(0, 256, size=(HEIGHT, WIDTH, 3), dtype=np.uint8),
    )


def main() -> None:
    rng = np.random.default_rng()
    viz = Visualizer(
        title="Tanga — Streaming Calibrated Camera + Pane Swap",
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

    cam = pinhole_camera(K, R, T, image_size=(WIDTH, HEIGHT))
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
    right = SceneView("world")  # default (auto-fit) camera, shows the frustum
    body = SplitView("horizontal", [left, right])

    async def _on_swap(_value: Any, _event: ControlEvent) -> None:
        # Swap the left/right panes and re-push the layout. `left` and `right`
        # are the same persistent objects, so the frontend re-attaches both
        # WebGL panes in the new order instead of recreating them.
        body.children.reverse()
        viz.set_layout(layout)

    toolbar = ToolbarView(
        [ButtonView("btn_swap", label="Swap panes", on_click=_on_swap)]
    )
    layout = SplitView("vertical", [toolbar, body])

    viz.show(layout=layout)
    print("Streaming noise at 4 fps (press q or Ctrl+C to stop).")
    for _ in viz.animate(fps=4):
        viz.set_background_image(left, _noise(rng))


if __name__ == "__main__":
    main()
