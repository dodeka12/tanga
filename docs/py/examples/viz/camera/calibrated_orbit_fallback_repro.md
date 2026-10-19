# repro a calibrated 2d pane falling back to a free 3D orbit view

**Keywords:** camera · pinhole · calibration · split view · background image · navigation · orbit · debugging

Shows one `world` scene in two panes, mirroring the calibration viewer that
first hit the intermittent bug:

- **left** — the calibrated camera view: a synthetic pinhole
  `~pytanga.viz.CameraCalibration` (camera at the origin, looking along
  -z) with a programmatically generated **12 MP** `ImageData` background and
  `navigation="2d"` (zoom/pan only, no rotation);
- **right** — the same scene from a read-only overview camera, showing the
  camera `~pytanga.geometry.Frustum` and a few depth markers in 3D.

The default axes/grid are intentionally left **enabled**: in a correct run the
pinhole camera makes the grid edge-on (invisible), but in the buggy run the left
pane falls back to the scene's default orbit camera and the grid + axes become
visible — the tell-tale sign.

A "Reload view" toolbar button re-pushes the layout (`set_layout`) to exercise
the pane-reuse/reconciliation path; combine it with browser reloads (F5), CPU
throttling, or a stale tab to try to trigger the drop.  With the diagnostic
logging in `templates/viewer.js` (`_routeToScene`) and
`templates/views/three-view.js` (`_applySceneConfig`), the browser console
reports either `[tanga:route] dropped scene_config …` or the pane's
`[tanga:scene-config] override=… nav=… cameraChanged=…` line.

## Run

```bash
uv run python py/examples/viz/camera/calibrated_orbit_fallback_repro.py
```

## Source

[`viz/camera/calibrated_orbit_fallback_repro.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/camera/calibrated_orbit_fallback_repro.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""calibrated_orbit_fallback_repro.py — repro a calibrated ``2d`` pane falling back to a free 3D orbit view.

Shows one ``world`` scene in two panes, mirroring the calibration viewer that
first hit the intermittent bug:

- **left** — the calibrated camera view: a synthetic pinhole
  :class:`~pytanga.viz.CameraCalibration` (camera at the origin, looking along
  -z) with a programmatically generated **12 MP** ``ImageData`` background and
  ``navigation="2d"`` (zoom/pan only, no rotation);
- **right** — the same scene from a read-only overview camera, showing the
  camera :class:`~pytanga.geometry.Frustum` and a few depth markers in 3D.

The default axes/grid are intentionally left **enabled**: in a correct run the
pinhole camera makes the grid edge-on (invisible), but in the buggy run the left
pane falls back to the scene's default orbit camera and the grid + axes become
visible — the tell-tale sign.

A "Reload view" toolbar button re-pushes the layout (``set_layout``) to exercise
the pane-reuse/reconciliation path; combine it with browser reloads (F5), CPU
throttling, or a stale tab to try to trigger the drop.  With the diagnostic
logging in ``templates/viewer.js`` (``_routeToScene``) and
``templates/views/three-view.js`` (``_applySceneConfig``), the browser console
reports either ``[tanga:route] dropped scene_config …`` or the pane's
``[tanga:scene-config] override=… nav=… cameraChanged=…`` line.

Run with:  uv run python py/examples/viz/camera/calibrated_orbit_fallback_repro.py

Keywords: camera, pinhole, calibration, split view, background image, navigation, orbit, debugging
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from pytanga.geometry import Frustum, Matrix, OpenCVFrame, Point
from pytanga.viz import (
    ButtonView,
    CameraCalibration,
    CameraConfig3d,
    CameraView,
    ControlEvent,
    ImageData,
    PointStyle,
    SceneView,
    Size,
    SplitView,
    StackView,
    ToolbarView,
    ViewportConfig,
    Visualizer,
)

#: Synthetic photo resolution — 4056 × 3040 ≈ 12.3 MP (matches the report).
_IMAGE_SIZE = (4056, 3040)
#: Focal length in pixels (matches the real calibration in the report).
_FOCAL_PX = 2298.0


def _make_dummy_photo() -> np.ndarray:
    """Return a synthetic ~12 MP RGB photo (``uint8``, H×W×3) with structure."""
    width, height = _IMAGE_SIZE
    rng = np.random.default_rng(20251019)
    yy, xx = np.mgrid[0:height, 0:width]

    v = (yy / max(1, height - 1)).astype(np.float32)
    img = np.stack(
        (
            0.15 + 0.85 * v,
            0.25 + 0.60 * (1.0 - np.abs(v - 0.5) * 1.2),
            0.55 + 0.45 * (1.0 - v),
        ),
        axis=-1,
    )

    # Checkerboard luminance modulation so the image is not a flat gradient.
    sq = 96
    checker = ((xx // sq + yy // sq) % 2).astype(np.float32)
    img *= 1.0 - 0.06 * checker[..., None]

    # A few bright "calibration" discs.
    for cx, cy, radius, color in (
        (width * 0.25, height * 0.35, 140, (1.0, 0.9, 0.2)),
        (width * 0.75, height * 0.65, 220, (0.2, 0.9, 1.0)),
        (width * 0.5, height * 0.5, 90, (1.0, 0.3, 0.3)),
    ):
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius**2
        img = np.where(mask[..., None], np.asarray(color, dtype=np.float32), img)

    # Light per-pixel noise gives the JPEG encoder some texture to chew on.
    img += rng.normal(0.0, 0.008, size=(height, width, 1)).astype(np.float32)
    return (np.clip(img, 0.0, 1.0) * 255.0).astype(np.uint8)


def _pt(xyz: np.ndarray) -> Point:
    """Coerce an ``(x, y, z)`` array to a :class:`~pytanga.geometry.Point`."""
    return Point(float(xyz[0]), float(xyz[1]), float(xyz[2]))


def _frustum_corners(frustum: Frustum) -> np.ndarray:
    """Return the 8 corner points of a ``Frustum`` (N×3, metres)."""
    o = np.array([frustum.origin.x, frustum.origin.y, frustum.origin.z], dtype=float)
    axis = np.array([frustum.axis.x, frustum.axis.y, frustum.axis.z], dtype=float)
    horiz = np.array(
        [frustum.horizontal.x, frustum.horizontal.y, frustum.horizontal.z],
        dtype=float,
    )
    vert = np.cross(horiz, axis)

    def plane(d: float, hw: float, hh: float) -> list[np.ndarray]:
        center = o + axis * d
        return [
            center + horiz * (sx * hw) + vert * (sy * hh)
            for sx in (-1.0, 1.0)
            for sy in (-1.0, 1.0)
        ]

    if frustum.near <= 0.0:
        near_pts = [o, o, o, o]
    else:
        near_pts = plane(
            frustum.near,
            frustum.far_half_width * frustum.near / frustum.far,
            frustum.far_half_height * frustum.near / frustum.far,
        )
    return np.asarray(
        near_pts + plane(frustum.far, frustum.far_half_width, frustum.far_half_height),
        dtype=float,
    )


def _overview_camera(points: np.ndarray, *, fov: float = 50.0) -> CameraConfig3d:
    """Return a 3D camera that frames *points* (N×3) from a three-quarter view."""
    lo = points.min(axis=0)
    hi = points.max(axis=0)
    center = (lo + hi) / 2.0
    radius = 0.5 * float(np.linalg.norm(hi - lo))
    distance = (radius / math.sin(math.radians(fov) / 2.0)) * 1.1
    direction = np.array([0.6, 0.5, 0.7])
    direction /= np.linalg.norm(direction)
    position = center + direction * distance
    return CameraConfig3d(
        fov=fov,
        position=(float(position[0]), float(position[1]), float(position[2])),
        target=(float(center[0]), float(center[1]), float(center[2])),
        up=(0.0, 1.0, 0.0),
        near=max(0.01, distance * 0.001),
        far=distance * 10.0,
    )


def main() -> None:
    width, height = _IMAGE_SIZE
    background = ImageData("camera", data=_make_dummy_photo())

    # Synthetic OpenCV-style pinhole calibration: camera at the world origin,
    # principal axis along -z (R = identity, t = 0).
    calib = CameraCalibration(
        K=Matrix(
            [
                [_FOCAL_PX, 0.0, width / 2.0],
                [0.0, _FOCAL_PX, height / 2.0],
                [0.0, 0.0, 1.0],
            ]
        ),
        R=Matrix(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ]
        ),
        t=[0.0, 0.0, 0.0],
        image_size=(width, height),
        frame=OpenCVFrame(),
        units=1.0,
    )
    cam = calib.to_pinhole_camera()

    viz = Visualizer(title="Tanga — calibrated pane orbit-fallback repro")
    world = viz.scene("world")

    # A few depth markers so both panes have content besides the frustum.
    for depth, color in ((1.0, "#44ff44"), (2.0, "#ff4444"), (3.0, "#4488ff")):
        world.new(
            Point(0.0, 0.0, -depth),
            color=color,
            style=PointStyle(size=0.02),
        )

    frustum = Frustum.from_camera(cam, near=0.5, far=5.0)
    frustum_ref = world.new(frustum, color="#ffcc44")

    overview_cam = _overview_camera(_frustum_corners(frustum))

    left = SceneView(
        "world",
        camera_view=CameraView(
            cam,
            navigation="2d",
            viewport=ViewportConfig(zoom=1.0, pan=(0.0, 0.0)),
            background_image=background,
        ),
        hide={frustum_ref.id},
    )
    right = SceneView("world", camera_view=CameraView(overview_cam), read_only=True)

    async def _on_reload(_value: Any, _event: ControlEvent) -> None:
        # Re-pushing the same layout exercises pane reuse/reconciliation; the
        # background keeps its version, so the 12 MP frame is not re-sent.
        viz.set_layout(split)

    toolbar = ToolbarView(
        [ButtonView("reload", label="Reload view", on_click=_on_reload)]
    )
    left.preferred_height = Size.fr(1)
    left_stack = StackView("vertical", [toolbar, left], fill=True)
    split = SplitView("horizontal", [left_stack, right])

    print(
        "Open the browser DevTools console and look for:\n"
        "  [tanga:route] dropped scene_config …  (bad — scene_config dropped)\n"
        "  [tanga:scene-config] override=yes nav=2d cameraChanged=true  (good)\n"
        "Add ?log=1 to the URL to forward these lines to the backend log.\n"
        "Press F5 / the toolbar 'Reload view' button to stress the handshake."
    )

    viz.show(layout=split)
    viz.wait()


if __name__ == "__main__":
    main()
````
