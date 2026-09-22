# a calibrated camera as a free orbit/pan/zoom view

**Keywords:** camera · pinhole · calibration · frustum · split view

Shows the "free camera" use case: `~pytanga.viz.pinhole_camera` turns
`K`/`R`/`t` into a regular `CameraConfig` pose + projection, so the left
pane still orbits/pans/zooms freely (no lock, no image).  The right pane shows
the same scene with the default camera and draws the camera's
`~pytanga.geometry.Frustum` so its field of view is visible.

## Run

```bash
uv run python py/examples/viz/camera/pinhole_camera.py
```

## Source

[`viz/camera/pinhole_camera.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/camera/pinhole_camera.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pinhole_camera.py — a calibrated camera as a free orbit/pan/zoom view.

Shows the "free camera" use case: :func:`~pytanga.viz.pinhole_camera` turns
``K``/``R``/``t`` into a regular ``CameraConfig`` pose + projection, so the left
pane still orbits/pans/zooms freely (no lock, no image).  The right pane shows
the same scene with the default camera and draws the camera's
:class:`~pytanga.geometry.Frustum` so its field of view is visible.

Run with:  uv run python py/examples/viz/camera/pinhole_camera.py

Keywords: camera, pinhole, calibration, frustum, split view
"""

import numpy as np

from pytanga.geometry import Frustum, Point, Sphere
from pytanga.viz import (
    PointStyle,
    SceneView,
    SphereStyle,
    SplitView,
    Visualizer,
    pinhole_camera,
)

WIDTH, HEIGHT = 640, 480
K = np.array([[500.0, 0.0, 320.0], [0.0, 500.0, 240.0], [0.0, 0.0, 1.0]])
# Upright camera (y up): flip the OpenCV y-down axis and the forward (z) axis.
R = np.diag([1.0, -1.0, -1.0])
T = np.array([0.0, 0.0, 6.0])  # camera centre at (0, 0, 6), looking toward -z


def main() -> None:
    viz = Visualizer(
        title="Tanga — Calibrated Camera (free orbit + frustum)",
        add_default_axes=False,
        add_default_grid=False,
    )
    world = viz.scene("world")

    for xyz in [(0.5, 0.3, 0.2), (-0.4, 0.2, 0.1), (0.2, -0.5, -0.3)]:
        world.new(Point(*xyz), color="#44ff44", style=PointStyle(size=0.08))
    world.new(
        Sphere(Point(0.0, 0.0, 0.0), radius=0.8),
        color="#4488ff",
        opacity=0.4,
        style=SphereStyle(wireframe=True),
    )

    cam = pinhole_camera(K, R, T, image_size=(WIDTH, HEIGHT))
    world.new(Frustum.from_camera(cam, near=0.5, far=6.0), color="#ffcc44")

    left = SceneView("world", camera=cam)  # free orbit/pan/zoom
    right = SceneView("world")  # default camera, shows the frustum

    viz.show(layout=SplitView("horizontal", [left, right]))
    viz.wait()


if __name__ == "__main__":
    main()
````
