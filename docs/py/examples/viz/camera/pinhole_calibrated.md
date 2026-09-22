# a real calibrated image (BOP T-LESS) + 3D overview

**Keywords:** camera · pinhole · calibration · BOP · OpenCV · image background · frustum · split view · annotation

Loads one bundled real T-LESS training image plus its pinhole calibration
(`K`) and the ground-truth 6D pose of object 1, then shows the same scene in
two panes:

- **left** — the calibrated camera view: a `~pytanga.viz.CameraCalibration`
  built from the OpenCV-style `K`/`R`/`t` with an
  `~pytanga.geometry.OpenCVFrame` axis convention and millimetre→metre
  `units`, in `"2d"` navigation, drawn over the photo as a full-viewport NDC
  background, so the ground-truth bounding box projects pixel-accurately onto the
  image;
- **right** — the same scene from an explicit overview camera, showing the camera
  `~pytanga.geometry.Frustum` and the GT bounding box in 3D, annotated
  with the image/data source and license.

The object's model→camera pose is mapped to the standard right-handed world
with `~pytanga.geometry.Matrix`.  The image, calibration, and pose are
read from `data/tless/` (bundled — no network at run time).  Attribution:
T-LESS, Hodan et al., WACV 2017, CC BY 4.0.

## Run

```bash
uv run python py/examples/viz/camera/pinhole_calibrated.py
```

## Source

[`viz/camera/pinhole_calibrated.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/camera/pinhole_calibrated.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pinhole_calibrated.py — a real calibrated image (BOP T-LESS) + 3D overview.

Loads one bundled real T-LESS training image plus its pinhole calibration
(``K``) and the ground-truth 6D pose of object 1, then shows the same scene in
two panes:

- **left** — the calibrated camera view: a :class:`~pytanga.viz.CameraCalibration`
  built from the OpenCV-style ``K``/``R``/``t`` with an
  :class:`~pytanga.geometry.OpenCVFrame` axis convention and millimetre→metre
  ``units``, in ``"2d"`` navigation, drawn over the photo as a full-viewport NDC
  background, so the ground-truth bounding box projects pixel-accurately onto the
  image;
- **right** — the same scene from an explicit overview camera, showing the camera
  :class:`~pytanga.geometry.Frustum` and the GT bounding box in 3D, annotated
  with the image/data source and license.

The object's model→camera pose is mapped to the standard right-handed world
with :class:`~pytanga.geometry.Matrix`.  The image, calibration, and pose are
read from ``data/tless/`` (bundled — no network at run time).  Attribution:
T-LESS, Hodan et al., WACV 2017, CC BY 4.0.

Run with:  uv run python py/examples/viz/camera/pinhole_calibrated.py

Keywords: camera, pinhole, calibration, BOP, OpenCV, image background, frustum, split view, annotation
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from pytanga.geometry import Frustum, Line, Matrix, OpenCVFrame, Point
from pytanga.viz import (
    CameraCalibration,
    CameraConfig3d,
    CameraView,
    GroupView,
    ImageData,
    LabelView,
    PointStyle,
    SceneView,
    SplitView,
    ViewportConfig,
    Visualizer,
)
from pytanga.viz.image import pil_to_numpy

_DATA_DIR = Path(__file__).resolve().parent / "data" / "tless"

# Shown in the right (world) pane.
_ATTRIBUTION = (
    "Image & data: T-LESS (Hodan et al., WACV 2017), BOP benchmark — "
    "License: CC BY 4.0"
)

# The 12 edges of the unit cube corner indices returned by :func:`_bbox_corners`.
_BOX_EDGES = (
    (0, 1), (0, 2), (1, 3), (2, 3),
    (4, 5), (4, 6), (5, 7), (6, 7),
    (0, 4), (1, 5), (2, 6), (3, 7),
)


def _load_calibration() -> tuple[dict[str, Any], ImageData]:
    """Load the bundled T-LESS image + calibration JSON."""
    data = json.loads((_DATA_DIR / "calibration.json").read_text(encoding="utf-8"))
    img = Image.open(_DATA_DIR / data["image"])
    img.load()
    return data, ImageData("camera", data=pil_to_numpy(img))


def _bbox_corners(data: dict[str, Any], scale: float) -> np.ndarray:
    """Return the 8 GT bounding-box corners as a 4×8 homogeneous matrix.

    Columns are model-space points ``[x, y, z, 1]ᵀ`` (scaled to metres by
    *scale*), ordered to match ``_BOX_EDGES``.
    """
    min_x, min_y, min_z = (v * scale for v in data["bbox_min"])
    sx, sy, sz = (v * scale for v in data["bbox_size"])
    pts = np.asarray(
        [
            (min_x + dx, min_y + dy, min_z + dz)
            for dx in (0.0, sx)
            for dy in (0.0, sy)
            for dz in (0.0, sz)
        ],
        dtype=float,
    )
    return np.vstack([pts.T, np.ones((1, pts.shape[0]))])


def _frustum_corners(frustum: Frustum) -> np.ndarray:
    """Return the 8 corner points of a ``Frustum`` (N×3, metres)."""
    o = np.array([frustum.origin.x, frustum.origin.y, frustum.origin.z], dtype=float)
    axis = np.array([frustum.axis.x, frustum.axis.y, frustum.axis.z], dtype=float)
    horiz = np.array(
        [frustum.horizontal.x, frustum.horizontal.y, frustum.horizontal.z],
        dtype=float,
    )
    vert = np.cross(horiz, axis)  # horizontal × axis

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


def _pt(xyz: np.ndarray) -> Point:
    """Coerce an (x, y, z) array to a :class:`~pytanga.geometry.Point`."""
    return Point(float(xyz[0]), float(xyz[1]), float(xyz[2]))


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
    data, background = _load_calibration()
    width, height = int(data["width"]), int(data["height"])

    # OpenCV-style calibration (K/R/t in millimetres) → a PinholeCamera in the
    # standard right-handed world (metres), via an OpenCVFrame axis convention.
    calib = CameraCalibration(
        K=Matrix(data["K"]),
        R=Matrix(data["R_w2c"]),
        t=data["t_w2c"],
        image_size=(width, height),
        frame=OpenCVFrame(),
        units=0.001,  # T-LESS stores lengths in millimetres
    )
    cam = calib.to_pinhole_camera()

    # Object pose (model→camera, OpenCV/mm) → model→world (standard, m).
    T = calib.world_to_camera().inverse() @ Matrix.from_R_t(
        data["cam_R_m2c"], np.asarray(data["cam_t_m2c"], dtype=float) * calib.units
    )
    corners = (T @ _bbox_corners(data, calib.units))[:3]  # 3×8 Cartesian metres

    viz = Visualizer(
        title="Tanga — Calibrated Camera (T-LESS) + 3D overview",
        add_default_axes=False,
        add_default_grid=False,
    )
    world = viz.scene("world")

    # Ground-truth bounding box: 8 corner points + 12 edges.
    for i in range(corners.shape[1]):
        world.new(_pt(corners[:, i]), color="#44ff44", style=PointStyle(size=0.004))
    for i, j in _BOX_EDGES:
        world.new(
            Line.from_points(_pt(corners[:, i]), _pt(corners[:, j])),
            color="#44ff44",
        )

    # Small coordinate frame at the object centre (model x/y/z axes).
    origin = _pt(T.data[:3, 3])
    for axis, color in enumerate(("#ff4444", "#44ff44", "#4488ff")):
        end = T.data[:3, 3] + T.data[:3, axis] * 0.04
        world.new(Line.from_points(origin, _pt(end)), color=color)

    frustum = Frustum.from_camera(cam, near=0.05, far=0.7)
    frustum_ref = world.new(frustum, color="#ffcc44")

    # Frame the frustum + box together for the overview pane.
    frustum_pts = _frustum_corners(frustum)
    overview_cam = _overview_camera(np.vstack([corners.T, frustum_pts]))

    cam_view = CameraView(
        cam,
        navigation="2d",
        viewport=ViewportConfig(zoom=1.0, pan=(0.0, 0.0)),
        background_image=background,
    )

    left = SceneView("world", camera_view=cam_view, hide={frustum_ref.id})
    right = SceneView(
        "world",
        camera_view=CameraView(overview_cam),
        overlay=[
            GroupView(
                "Data",
                [LabelView("attribution", value=_ATTRIBUTION, font_size=12)],
                position="bottom-left",
            )
        ],
    )

    viz.show(layout=SplitView("horizontal", [left, right]))
    viz.wait()


if __name__ == "__main__":
    main()
````
