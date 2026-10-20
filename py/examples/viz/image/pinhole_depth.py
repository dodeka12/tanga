# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pinhole_depth.py — a calibrated depth surface with a grazing-angle filter.

Shows one calibrated scene in three panes:

- **left** — the calibrated camera view (``navigation="2d"``) with the synthetic
  test image as a full-viewport background.
- **middle** — a control pane with a **Max grazing angle** slider that changes
  the :class:`~pytanga.viz.DepthImage` depth-jump filter live via
  ``ref.set_uniform("u_max_stretch", …)`` (no rebuild, no pixel re-send).
- **right** — the same scene from a 3D overview camera, showing the depth
  surface textured with that image (plus the camera frustum for reference).

The depth map is a central box at ``Z = 1.5`` in front of a plane that undulates
with the sine pattern's depth (``[2, 3]``); the sharp box/plane border produces
the stretched triangles the grazing-angle filter removes, while the sine
undulation (a legitimate slant) stays.  The test image is a 2D sine pattern
whose spatial frequency
increases toward the bottom-right corner, so both left/right and top/bottom
orientation are unambiguous.  The depth surface is added with
``visible_in={right.id}`` so it is only constructed in the 3D pane; the left
calibrated camera pane never builds it (and therefore never consumes its binary
frames).

Run with:  uv run python py/examples/viz/image/pinhole_depth.py

Keywords: depth image, pinhole, camera calibration, depth jump filter, grazing angle, slider, uniform, split view
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from pytanga.geometry import Frustum, Matrix, OpenCVFrame
from pytanga.viz import (
    CameraCalibration,
    CameraConfig3d,
    CameraView,
    ControlEvent,
    DepthImage,
    DepthImageData,
    DepthImageStyle,
    GroupView,
    ImageData,
    SceneView,
    SliderView,
    SplitView,
    ViewportConfig,
    Visualizer,
)

#: Color image / reference-frame resolution (the intrinsics refer to this).
_IMAGE_W, _IMAGE_H = 512, 384
#: Depth-map resolution (downscaled to the mesh independently of the image).
_DEPTH_W, _DEPTH_H = 128, 96

#: Axial depth range: the top row is near, the bottom row is far.
_NEAR, _FAR = 1.0, 3.0
#: Axial depth of the box front, in front of the background plane (``_FAR``).
_BOX_Z = 1.5
#: Minimum axial depth of the undulating background plane (max is ``_FAR``).
_BG_DEPTH_MIN = 2.0


def _calibration() -> CameraCalibration:
    """An OpenCV pinhole camera at the world origin looking along ``-z``."""
    return CameraCalibration(
        K=Matrix(
            [
                [400.0, 0.0, _IMAGE_W / 2.0],
                [0.0, 400.0, _IMAGE_H / 2.0],
                [0.0, 0.0, 1.0],
            ]
        ),
        R=Matrix.identity(3),
        t=(0.0, 0.0, 0.0),
        image_size=(_IMAGE_W, _IMAGE_H),
        frame=OpenCVFrame(),
        units=1.0,
    )


def _sine_pattern(height: int, width: int) -> np.ndarray:
    """A 2D sine pattern in ``[0, 1]`` whose frequency grows toward bottom-right.

    The carrier frequency increases with both ``u`` and ``v``, so left/right and
    top/bottom are unambiguous; ``0.5 + 0.5·sin(...)`` maps the signed amplitude
    ``[-1, 1]`` into ``[0, 1]``.
    """
    ys, xs = np.mgrid[0:height, 0:width]
    u = xs / max(width - 1, 1)
    v = ys / max(height - 1, 1)
    fx = 3.0 + 9.0 * u
    fy = 2.0 + 7.0 * v
    return 0.5 + 0.5 * np.sin(2.0 * np.pi * (fx * u + fy * v))


def _image(height: int, width: int) -> np.ndarray:
    """The sine pattern tinted red (top-left) → blue (bottom-right)."""
    s = _sine_pattern(height, width)
    ys, xs = np.mgrid[0:height, 0:width]
    u = xs / max(width - 1, 1)
    v = ys / max(height - 1, 1)
    r = s * (1.0 - u) * (1.0 - v)
    g = s * 0.25
    b = s * u * v
    return np.clip(np.stack([r, g, b], axis=-1) * 255.0, 0.0, 255.0).astype(np.uint8)


def _depth(height: int, width: int) -> np.ndarray:
    """A central box in front of a gently undulating (sine-wave) plane.

    The background plane carries the sine pattern's depth in ``[_BG_DEPTH_MIN,
    _FAR]``; the flat box front at ``_BOX_Z`` creates the sharp border whose
    stretched triangles the grazing-angle filter removes, while the sine
    undulation (a legitimate slant) is kept.
    """
    depth = _BG_DEPTH_MIN + (_FAR - _BG_DEPTH_MIN) * _sine_pattern(height, width)
    lo_h, hi_h = height // 4, 3 * height // 4
    lo_w, hi_w = width // 4, 3 * width // 4
    depth[lo_h:hi_h, lo_w:hi_w] = _BOX_Z
    return depth.astype(np.float32)


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


def _surface_corners(calib: CameraCalibration) -> np.ndarray:
    """World-space corners of the depth surface (4 reference-frame corners)."""
    fx, fy = calib.K.data[0, 0], calib.K.data[1, 1]
    cx, cy = calib.K.data[0, 2], calib.K.data[1, 2]
    c2w = calib.camera_to_world().data
    corners = []
    for v, z in ((0.0, _NEAR), (_IMAGE_H - 1.0, _FAR)):
        for u in (0.0, _IMAGE_W - 1.0):
            cam = np.array([(u - cx) / fx * z, (v - cy) / fy * z, z, 1.0])
            corners.append((c2w @ cam)[:3])
    return np.asarray(corners, dtype=float)


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
    calib = _calibration()
    cam = calib.to_pinhole_camera()
    background = ImageData("camera", data=_image(_IMAGE_H, _IMAGE_W))
    depth = _depth(_DEPTH_H, _DEPTH_W)

    viz = Visualizer(
        reuse_existing=False,
        title="Tanga — pinhole depth image (image vs 3D surface)",
    )
    world = viz.scene("world")

    frustum = Frustum.from_camera(cam, near=0.5, far=4.0)
    frustum_ref = world.new(frustum, color="#ffcc44")

    overview_cam = _overview_camera(
        np.vstack([_frustum_corners(frustum), _surface_corners(calib)])
    )

    left = SceneView(
        "world",
        camera_view=CameraView(
            cam,
            navigation="2d",
            viewport=ViewportConfig(zoom=1.0, pan=(0.0, 0.0)),
            background_image=background,
        ),
    )
    right = SceneView("world", id="3d", camera_view=CameraView(overview_cam))

    # Add the depth surface only to the 3D pane via `visible_in`, so the left
    # calibrated camera pane never constructs (or consumes) it.  Start with the
    # grazing-angle filter on, so the box/plane border is already cleaned up.
    depth_ref = world.new(
        DepthImage(DepthImageData(image=_image(_IMAGE_H, _IMAGE_W), depth=depth)),
        style=DepthImageStyle(
            camera=calib,
            depth_kind="axial",
            apply_pose=True,
            render_mode="image",
            depth_min=_NEAR,
            depth_max=_FAR,
            max_grazing_angle=85,
        ),
        visible_in={right.id},
    )

    left.set_visible(frustum_ref.id, False)

    async def _on_grazing_angle(value: Any, _event: ControlEvent) -> None:
        # Live uniform update: 0 = off (tan(0) == 0), 89° ≈ edge-on (tan → large).
        depth_ref.set_uniform("u_max_stretch", math.tan(math.radians(value)))

    grazing_slider = SliderView(
        "max_grazing_angle",
        label="Max grazing angle",
        min=0.0,
        max=89.0,
        step=1.0,
        value=85.0,
        on_change=_on_grazing_angle,
    )
    controls = GroupView("Depth-jump filter", [grazing_slider])

    viz.show(layout=SplitView("horizontal", [controls, left, right]))
    viz.wait()


if __name__ == "__main__":
    main()
