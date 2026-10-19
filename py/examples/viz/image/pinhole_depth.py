# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pinhole_depth.py — switch the interpretation of one depth map, live.

Places a calibrated pinhole camera at the world origin (OpenCV convention:
x right, y down, z forward) with its optical axis along the normalized world
direction ``(1, 1, 1)/√3``, using the default pytanga world axes and grid for
orientation.  A single, constant depth map (value ``2.0``)
is rendered through :class:`~pytanga.viz.DepthImage` with the **same**
``camera=calib``.  The surface is therefore always placed automatically
**relative to the camera** — the intrinsics give the ray through each pixel,
the depth gives the distance along it, and the calibration pose places it in
the world — so it needs no manual placement regardless of the calibration's
rotation/translation.

A control pane on the left switches ``depth_kind`` so the **same raw depth
values** produce three different 3D surfaces, all sitting along the camera's
optical axis:

- ``axial``   — depth along the optical axis → a flat wall at ``Z = 2 m``,
  centered at ``2·(1,1,1)/√3 ≈ (1.15, 1.15, 1.15)``.
- ``radial``  — depth along the projection ray → a dome of radius ``2 m``
  (every pixel is 2 m from the camera, so the surface is a sphere).
- ``inverse`` — inverse depth ``1/Z`` → a flat wall at ``Z = 1/2 = 0.5 m``.

The camera frustum and the camera center are drawn for reference.
``depth_min``/``depth_max`` are always axial metres.

Run with:  uv run python py/examples/viz/image/pinhole_depth.py

Keywords: depth image, pinhole, camera calibration, depth kind, frustum, surface, axes
"""

from __future__ import annotations

from typing import Any

import numpy as np

from pytanga.geometry import Frustum, Matrix, OpenCVFrame, Point
from pytanga.geometry.transforms import look_at_matrix
from pytanga.viz import (
    CameraCalibration,
    ControlEvent,
    DepthImage,
    DepthImageData,
    DepthImageStyle,
    DropdownView,
    GroupView,
    LabelView,
    SceneView,
    SplitView,
    Visualizer,
)

#: Reference-frame resolution the intrinsics refer to (pixels).
_FRAME_W, _FRAME_H = 160, 120

#: The constant raw depth value (its meaning depends on ``depth_kind``).
_DEPTH = 2.0


def _calibration() -> CameraCalibration:
    """A pinhole camera at the world origin looking along (1, 1, 1)/√3.

    ``fx = fy = 100`` px on a 160×120 frame gives a ~62° vertical field of view,
    wide enough that the radial ("range") surface curves visibly.
    """
    forward = np.asarray([1.0, 1.0, 1.0], dtype=float)
    forward = forward / np.linalg.norm(forward)
    # Camera→world rotation (standard frame) looking along ``forward``; convert
    # to the OpenCV world→camera basis (x right, y down, z forward) for K/R/t.
    r_c2w = look_at_matrix(forward)
    opencv = OpenCVFrame().to_matrix()[:3, :3]
    R = Matrix((r_c2w[:3, :3].T @ opencv).tolist())
    return CameraCalibration(
        K=Matrix([[100.0, 0.0, 80.0], [0.0, 100.0, 60.0], [0.0, 0.0, 1.0]]),
        R=R,
        t=(0.0, 0.0, 0.0),
        image_size=(_FRAME_W, _FRAME_H),
        frame=OpenCVFrame(),
        units=1.0,
    )


def _depth(height: int, width: int) -> np.ndarray:
    """A constant depth map: the value ``2.0`` in the selected ``depth_kind`` units."""
    return np.full((height, width), _DEPTH, dtype=np.float32)


def main() -> None:
    calib = _calibration()
    cam = calib.to_pinhole_camera()
    depth = _depth(_FRAME_H, _FRAME_W)

    viz = Visualizer(
        title="Tanga — pinhole depth kind",
    )
    world = viz.scene("world")

    # Reference objects: camera frustum + camera center.
    world.new(Frustum.from_camera(cam, near=0.2, far=3.0), color="#ffcc44")
    world.new(Point(*calib.camera_center()), color="#ff4444")

    surface_ref: Any = None

    def _add_surface(kind: str) -> None:
        """Remove the previous surface, then add one with the given ``depth_kind``.

        Each ``new()`` call generates a fresh entity id, so ``remove()`` on the
        previous reference and the new add never collide.
        """
        nonlocal surface_ref
        if surface_ref is not None:
            surface_ref.remove()
        surface_ref = world.new(
            DepthImage(DepthImageData(depth=depth)),
            style=DepthImageStyle(
                camera=calib,
                depth_kind=kind,
                render_mode="depth",
                colormap="turbo",
                depth_min=0.0,
                depth_max=3.0,
            ),
        )

    _add_surface("axial")

    async def _on_kind(value: Any, _event: ControlEvent) -> None:
        _add_surface(str(value))
        viz.flush()

    kind = DropdownView(
        "depth_kind",
        label="Depth kind",
        options=["axial", "radial", "inverse"],
        value="axial",
        on_change=_on_kind,
    )

    layout = SplitView(
        orientation="horizontal",
        children=[
            GroupView(
                "Pinhole depth",
                [
                    kind,
                    LabelView(
                        "hint",
                        value=(
                            "Camera looks along (1,1,1)/√3.\n"
                            "Same depth map (constant 2.0), three interpretations:\n"
                            "  axial   → flat wall at 2 m\n"
                            "  radial  → dome of radius 2 m\n"
                            "  inverse → flat wall at 0.5 m"
                        ),
                    ),
                ],
            ),
            SceneView("world"),
        ],
    )

    viz.show(layout=layout)
    viz.wait()


if __name__ == "__main__":
    main()

