# label a calibrated image in 3D

**Keywords:** camera · pinhole · calibration · labelme · image labeling · CalibratedPlaneMapper · frustum · split view

Loads one bundled BOP T-LESS training image plus its pinhole calibration and a
small labelme annotation file, then shows the **same** `world` scene in two
panes:

- **left** — the calibrated camera view (the photo as a `2d`-navigation
  background), where the labelme shapes — mapped from pixel space to a fixed
  depth plane in front of the camera by a
  `~pytanga.viz.CalibratedPlaneMapper` — are drawn as interactive
  `~pytanga.viz.ActSceneObject` composites (drag their handles to edit);
- **right** — the same scene from an overview camera, showing the camera
  `~pytanga.geometry.Frustum` and the same shapes in 3D.

Pixel↔world mapping is a `~pytanga.viz.CalibratedPlaneMapper` handed to
`~pytanga.viz.LabelMeStore`, so the labelme JSON round-trips through 3D.
Attribution: T-LESS, Hodan et al., WACV 2017, CC BY 4.0.

## Run

```bash
uv run python py/examples/apps/calibrated_labeling_app.py
```

## Source

[`apps/calibrated_labeling_app.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/apps/calibrated_labeling_app.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""calibrated_labeling_app.py — label a calibrated image in 3D.

Loads one bundled BOP T-LESS training image plus its pinhole calibration and a
small labelme annotation file, then shows the **same** ``world`` scene in two
panes:

- **left** — the calibrated camera view (the photo as a ``2d``-navigation
  background), where the labelme shapes — mapped from pixel space to a fixed
  depth plane in front of the camera by a
  :class:`~pytanga.viz.CalibratedPlaneMapper` — are drawn as interactive
  :class:`~pytanga.viz.ActSceneObject` composites (drag their handles to edit);
- **right** — the same scene from an overview camera, showing the camera
  :class:`~pytanga.geometry.Frustum` and the same shapes in 3D.

Pixel↔world mapping is a :class:`~pytanga.viz.CalibratedPlaneMapper` handed to
:class:`~pytanga.viz.LabelMeStore`, so the labelme JSON round-trips through 3D.
Attribution: T-LESS, Hodan et al., WACV 2017, CC BY 4.0.

Run with:  uv run python py/examples/apps/calibrated_labeling_app.py

Keywords: camera, pinhole, calibration, labelme, image labeling, CalibratedPlaneMapper, frustum, split view
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from pytanga.geometry import Frustum, Matrix, OpenCVFrame, Plane
from pytanga.viz import (
    ActCircle,
    ActImagePlane,
    ActLine,
    ActRectangle2D,
    ButtonView,
    CalibratedPlaneMapper,
    CameraCalibration,
    CameraConfig3d,
    CameraView,
    CircleStyle,
    DragBinding,
    DragPreview,
    GroupView,
    ImageData,
    LabelMeStore,
    LabelView,
    LineStyle,
    MouseButton,
    Rectangle2DStyle,
    SceneView,
    Size,
    SplitView,
    StackView,
    ToolbarView,
    ViewportConfig,
    Visualizer,
)
from pytanga.viz.image import pil_to_numpy

_DATA_DIR = Path(__file__).resolve().parent.parent / "viz" / "camera" / "data" / "tless"
_LABELS_PATH = _DATA_DIR / "labels.json"

#: Annotation plane distance (metres) in front of the camera.
_DEPTH = 0.6

_ATTRIBUTION = (
    "Image & data: T-LESS (Hodan et al., WACV 2017), BOP benchmark — "
    "License: CC BY 4.0"
)


def _load_calibration() -> tuple[dict[str, Any], ImageData]:
    data = json.loads((_DATA_DIR / "calibration.json").read_text(encoding="utf-8"))
    img = Image.open(_DATA_DIR / data["image"])
    img.load()
    return data, ImageData("camera", data=pil_to_numpy(img))


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
    """Return a 3D camera framing *points* (N×3) from a three-quarter view."""
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


def _style_for(mode: str, fill: str) -> Any:
    if mode == "rect":
        return Rectangle2DStyle(color=fill, fill=True, fill_opacity=0.15)
    if mode == "circle":
        return CircleStyle(color=fill, thickness=2, fill=True, fill_opacity=0.15)
    return LineStyle(color=fill, thickness=2)


class _CalibratedLabeler:
    """Drag-to-draw on the calibrated plane, adding shapes to the world scene."""

    _FACTORIES = {
        "rect": ActRectangle2D,
        "circle": ActCircle,
        "line": ActLine,
    }

    def __init__(
        self, world: Any, mapper: CalibratedPlaneMapper, *, fill: str = "#ff4444"
    ) -> None:
        self._world = world
        self._mode: str | None = None
        self._styles: dict[str, Any] = {}
        self._previews: dict[str, DragPreview] = {}
        for mode, factory in self._FACTORIES.items():
            style = _style_for(mode, fill)
            self._styles[mode] = style
            self._previews[mode] = DragPreview(world, factory=factory, style=style)

        plane_point, plane_normal = mapper.plane()
        self._act_plane = ActImagePlane(
            mapper=mapper,
            entity=Plane(point=plane_point, normal=plane_normal),
            on_drag_start=self._on_drag_start,
            on_drag_end=self._on_drag_end,
            drag_bindings=[DragBinding(MouseButton.LEFT, self._on_drag)],
        )

    def register(self) -> None:
        self._world.add(self._act_plane, opacity=0.0)

    def set_mode(self, mode: str | None) -> None:
        self._mode = mode

    def toolbar(self) -> ToolbarView:
        def _button(cid: str, icon: str, tip: str) -> ButtonView:
            async def on_click(_value: Any, _event: Any) -> None:
                self.set_mode(cid if self._mode != cid else None)

            return ButtonView(
                cid, icon=icon, icon_only=True, tooltip=tip, on_click=on_click
            )

        return ToolbarView(
            [
                _button("rect", "material:crop_square", "Add rectangle"),
                _button("circle", "material:circle", "Add circle"),
                _button("line", "material:diagonal_line", "Add line"),
            ],
            border=False,
        )

    async def _on_drag_start(self, event: Any, _plane: Any) -> None:
        preview = self._previews.get(self._mode or "")
        if preview is not None:
            preview.begin(event.world_position)

    async def _on_drag(self, event: Any, _plane: Any) -> bool:
        preview = self._previews.get(self._mode or "")
        if preview is None:
            return False
        if preview.anchor is None:
            preview.begin(event.world_position)
        preview.update(event.world_position)
        return True

    async def _on_drag_end(self, event: Any, _plane: Any) -> None:
        preview = self._previews.get(self._mode or "")
        if preview is None or preview.anchor is None:
            return
        act = preview.finalize(event.world_position)
        self._world.add(act, style=self._styles[self._mode or ""])
        self._world.flush()


def main() -> None:
    data, background = _load_calibration()
    width, height = int(data["width"]), int(data["height"])

    calib = CameraCalibration(
        K=Matrix(data["K"]),
        R=Matrix(data["R_w2c"]),
        t=data["t_w2c"],
        image_size=(width, height),
        frame=OpenCVFrame(),
        units=0.001,  # T-LESS stores lengths in millimetres
    )
    cam = calib.to_pinhole_camera()

    mapper = CalibratedPlaneMapper(calib, _DEPTH)
    store = LabelMeStore(mapper=mapper)

    viz = Visualizer(
        title="Tanga — Calibrated Labeling (T-LESS)",
        add_default_axes=False,
        add_default_grid=False,
    )
    world = viz.scene("world")

    result = store.load(_LABELS_PATH)
    for message in result.errors:
        print(f"labelme: skipped {message}")
    _, errors = store.add_shapes(world, result.document, active=True)
    for message in errors:
        print(f"labelme: skipped {message}")

    frustum = Frustum.from_camera(cam, near=0.05, far=0.7)
    frustum_ref = world.new(frustum, color="#ffcc44")

    overview_cam = _overview_camera(_frustum_corners(frustum))

    labeler = _CalibratedLabeler(world, mapper)
    labeler.register()

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

    left.preferred_height = Size.fr(1)
    left_pane = StackView("vertical", [labeler.toolbar(), left], fill=True)
    viz.show(layout=SplitView("horizontal", [left_pane, right]))
    viz.wait()


if __name__ == "__main__":
    main()
````
