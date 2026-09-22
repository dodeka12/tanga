# calibrated camera view (image) + default 3D overview

**Keywords:** camera · pinhole · calibration · frustum · image background · lock · split view

Builds a single shared scene shown in two panes:

- **left** — the camera view: a `~pytanga.viz.pinhole_camera` derived
  from `K`/`R`/`t`, in `"2d"` navigation (dolly zoom + screen-space pan,
  no orbit) and drawn over a synthetic camera image as a full-viewport NDC
  background, so world objects project pixel-accurately onto it;
- **right** — the same scene from a different perspective with the **default**
  camera, showing the camera's `~pytanga.geometry.Frustum`.

The camera, lock, and background image are bundled in a
`~pytanga.viz.CameraView`.  The frustum (a scene entity) is hidden in the
left pane via `SceneView.hide`.

## Run

```bash
uv run python py/examples/viz/camera/pinhole_overlay.py
```

## Source

[`viz/camera/pinhole_overlay.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/camera/pinhole_overlay.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pinhole_overlay.py — calibrated camera view (image) + default 3D overview.

Builds a single shared scene shown in two panes:

- **left** — the camera view: a :func:`~pytanga.viz.pinhole_camera` derived
  from ``K``/``R``/``t``, in ``"2d"`` navigation (dolly zoom + screen-space pan,
  no orbit) and drawn over a synthetic camera image as a full-viewport NDC
  background, so world objects project pixel-accurately onto it;
- **right** — the same scene from a different perspective with the **default**
  camera, showing the camera's :class:`~pytanga.geometry.Frustum`.

The camera, lock, and background image are bundled in a
:class:`~pytanga.viz.CameraView`.  The frustum (a scene entity) is hidden in the
left pane via ``SceneView.hide``.

Run with:  uv run python py/examples/viz/camera/pinhole_overlay.py

Keywords: camera, pinhole, calibration, frustum, image background, lock, split view
"""

from typing import Any

import numpy as np

from pytanga.geometry import Frustum, Point, Sphere
from pytanga.viz import (
    ButtonView,
    CameraAction,
    CameraView,
    ControlEvent,
    GroupView,
    ImageData,
    MouseButton,
    PointStyle,
    SceneView,
    SphereStyle,
    SplitView,
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


def _project(xyz: tuple[float, float, float]) -> tuple[int, int]:
    x, y, z = xyz
    zc = 6.0 - z
    u = int(K[0, 0] * x / zc + K[0, 2])
    v = int(K[1, 1] * (-y) / zc + K[1, 2])
    return u, v


def _background_image() -> ImageData:
    """A visible gradient + grid, with the projected world points as markers."""
    ys, xs = np.mgrid[0:HEIGHT, 0:WIDTH]
    img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    img[..., 0] = (ys / (HEIGHT - 1) * 120 + 30).astype(np.uint8)  # blue gradient
    img[..., 2] = (xs / (WIDTH - 1) * 120 + 30).astype(np.uint8)  # red gradient
    img[::40, :, :] += 30  # horizontal grid lines
    img[:, ::40, :] += 30  # vertical grid lines
    for xyz in _WORLD_POINTS:
        u, v = _project(xyz)
        for dy in range(-8, 9):
            for dx in range(-8, 9):
                if dx * dx + dy * dy <= 64 and 0 <= u + dx < WIDTH and 0 <= v + dy < HEIGHT:
                    img[v + dy, u + dx] = [0, 255, 0]
    return ImageData("camera", data=img)


def main() -> None:
    viz = Visualizer(
        title="Tanga — Calibrated Camera View (image + overview)",
        add_default_axes=False,
        add_default_grid=False,
    )
    world = viz.scene("world")

    # Shared 3D objects (visible in both panes).
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
        background_image=_background_image(),
    )

    async def _on_reset(_value: Any, _event: ControlEvent) -> None:
        # Reset the camera pane's 2D viewport (zoom + pan) from Python.
        viz.set_viewport(left, zoom=1.0, pan=(0.0, 0.0))

    left = SceneView(
        "world",
        camera_view=cam_view,
        hide={frustum_ref.id},
        overlay=[
            GroupView(
                "View",
                [ButtonView("btn_reset", label="Reset view", on_click=_on_reset)],
                position="top-left",
            )
        ],
    )
    right = SceneView("world")  # default (auto-fit) camera, shows the frustum

    viz.show(layout=SplitView("horizontal", [left, right]))
    viz.wait()


if __name__ == "__main__":
    main()
````
