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
  :class:`~pytanga.viz.ActSceneObject` composites (drag their handles to edit).
  A toolbar drives drag-to-draw on the pane's
  :class:`~pytanga.viz.InteractionSurface` (the ⟂-optical-axis plane at
  ``_DEPTH``);
- **right** — the same scene from an overview camera (read-only), showing the
  camera :class:`~pytanga.geometry.Frustum` and the same shapes in 3D.

Pixel↔world mapping is a :class:`~pytanga.viz.CalibratedPlaneMapper` handed to
:class:`~pytanga.viz.LabelMeStore`, so the labelme JSON round-trips through 3D.
Attribution: T-LESS, Hodan et al., WACV 2017, CC BY 4.0.

Run with:  uv run python py/examples/apps/calibrated_labeling_app.py

Keywords: camera, pinhole, calibration, labelme, image labeling, CalibratedPlaneMapper, frustum, split view, InteractionSurface
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from pytanga.geometry import Frustum, Matrix, OpenCVFrame
from pytanga.viz import (
    ActCircle,
    ActEllipse,
    ActLine,
    ActPoint,
    ActPolygon,
    ActRectangle2D,
    ButtonView,
    CalibratedPlaneMapper,
    CalibratedSurface,
    CameraCalibration,
    CameraConfig3d,
    CameraView,
    CirclePointStyle,
    CircleStyle,
    Color,
    DragBinding,
    DragMode,
    DragPreview,
    EllipseStyle,
    GroupView,
    ImageData,
    LabelMeStore,
    LabelView,
    LineStyle,
    MouseButton,
    PointPathStyle,
    Rectangle2DStyle,
    SceneView,
    Size,
    SplitView,
    SquarePointStyle,
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
    if mode == "ellipse":
        return EllipseStyle(color=fill, fill=True, fill_opacity=0.15)
    if mode == "circle":
        return CircleStyle(color=fill, thickness=2, fill=True, fill_opacity=0.15)
    if mode == "polygon":
        return PointPathStyle(color=fill, line_thickness=2)
    if mode == "point":
        return SquarePointStyle(color=fill, size=6.0, thickness=2, screen_space=True)
    return LineStyle(color=fill, thickness=2)


def _loaded_style(obj: Any) -> Any:
    """The style for a loaded labelme shape (points are screen-space markers)."""
    if isinstance(obj, ActPoint):
        return SquarePointStyle(size=6.0, thickness=2, screen_space=True)
    if isinstance(obj, ActRectangle2D):
        return Rectangle2DStyle(fill=True, fill_opacity=0.15)
    if isinstance(obj, ActEllipse):
        return EllipseStyle(fill=True, fill_opacity=0.15)
    if isinstance(obj, ActCircle):
        return CircleStyle(thickness=2, fill=True, fill_opacity=0.15)
    if isinstance(obj, ActPolygon):
        return PointPathStyle(line_thickness=2)
    return LineStyle(thickness=2)


class _CalibratedLabeler:
    """Draw/select shapes on the calibrated plane, adding them to the world scene."""

    _FACTORIES = {
        "rect": ActRectangle2D,
        "ellipse": ActEllipse,
        "circle": ActCircle,
        "line": ActLine,
        "polygon": ActPolygon,
    }

    def __init__(
        self,
        world: Any,
        calib: CameraCalibration,
        depth: float,
        *,
        fill: str = "#ff4444",
    ) -> None:
        self._world = world
        self._mode: str | None = None
        self.selected: Any = None
        self._styles: dict[str, Any] = {}
        self._previews: dict[str, DragPreview] = {}

        # World units per image pixel, from the mapper (single source).
        self._pixel_scale = CalibratedPlaneMapper(calib, depth).world_units_per_pixel()
        # 0.5 image px minimum half-extent, in world units.
        self._min_half = 0.5 * self._pixel_scale
        self._max_half: float | None = None

        select = self._make_select_handler()
        vertex_style = CirclePointStyle(
            color=Color.RED, size=6.0, thickness=2.0, screen_space=True
        )
        end_style = CirclePointStyle(
            color=Color.GREEN, size=6.0, thickness=2.0, screen_space=True
        )
        for mode, factory in self._FACTORIES.items():
            style = _style_for(mode, fill)
            self._styles[mode] = style
            kwargs = {"on_click": select}
            if mode == "polygon":
                kwargs["handle_style"] = vertex_style
                kwargs["end_handle_style"] = end_style
            self._previews[mode] = DragPreview(
                world,
                factory=factory,
                style=style,
                factory_kwargs=kwargs,
            )

        self._drag_binding = DragBinding(MouseButton.LEFT, self._on_drag, enabled=False)
        self._tool_buttons: dict[str, ButtonView] = {}
        self.surface = CalibratedSurface(
            calib,
            depth,
            on_drag_start=self._on_drag_start,
            on_drag_end=self._on_drag_end,
            on_click=self._on_click,
            drag_bindings=[self._drag_binding],
        )

    def set_mode(self, mode: str | None) -> None:
        self._mode = mode
        self._drag_binding.enabled = mode is not None and mode != "point"
        self.surface.set_enabled(mode is not None)
        self.surface.set_click_enabled(mode == "point")
        self._world.set_cursor("crosshair" if mode is not None else None)
        for cid, button in self._tool_buttons.items():
            button.set_selected(cid == mode)

    def toolbar(self) -> ToolbarView:
        def _button(cid: str, icon: str, tip: str) -> ButtonView:
            async def on_click(_value: Any, _event: Any) -> None:
                self.set_mode(cid if self._mode != cid else None)

            return ButtonView(
                cid, icon=icon, icon_only=True, tooltip=tip, on_click=on_click
            )

        self._tool_buttons = {
            "rect": _button("rect", "material:crop_square", "Add rectangle"),
            "ellipse": _button("ellipse", "material:app_badging", "Add ellipse"),
            "circle": _button("circle", "material:circle", "Add circle"),
            "line": _button("line", "material:diagonal_line", "Add line"),
            "polygon": _button("polygon", "material:gesture", "Add polygon"),
            "point": _button("point", "material:place", "Add point (click)"),
        }
        return ToolbarView(list(self._tool_buttons.values()), border=False)

    async def _on_drag_start(self, event: Any, _surface: Any) -> None:
        preview = self._previews.get(self._mode or "")
        if preview is not None:
            preview.begin(event.world_position)

    async def _on_drag(self, event: Any, _surface: Any) -> bool:
        preview = self._previews.get(self._mode or "")
        if preview is None:
            return False
        if preview.anchor is None:
            preview.begin(event.world_position)
        preview.update(event.world_position)
        return True

    async def _on_drag_end(self, event: Any, _surface: Any) -> None:
        preview = self._previews.get(self._mode or "")
        if preview is None or preview.anchor is None:
            return
        act = preview.finalize(event.world_position)
        self._add_shape(act, self._styles[self._mode or ""])

    async def _on_click(self, event: Any, _surface: Any) -> None:
        if self._mode != "point":
            return
        act = ActPoint(
            event.world_position,
            drag_mode=DragMode.VIEW_PLANE,
            on_click=self._make_select_handler(),
        )
        self._add_shape(act, self._styles["point"])

    # ── Shape management / selection ────────────────────────

    def _make_select_handler(self) -> Any:
        async def on_click(_event: Any, act: Any) -> None:
            self._select(act)

        return on_click

    def _select(self, act: Any) -> None:
        if self.selected is act:
            return
        self._deselect()
        self.selected = act
        self._set_extra_handles(act, True)

    def _deselect(self) -> None:
        if self.selected is None:
            return
        self._set_extra_handles(self.selected, False)
        self.selected = None

    @staticmethod
    def _set_extra_handles(act: Any, visible: bool) -> None:
        """Toggle the optional translate/rotate handles on a composite shape."""
        if hasattr(act, "set_translate_handle_visible"):
            act.set_translate_handle_visible(visible)
        if hasattr(act, "set_rotate_handle_visible"):
            act.set_rotate_handle_visible(visible)

    def _apply_size_limits(self, act: Any) -> None:
        """Clamp resize to the app's pixel-derived limits (half-extent)."""
        act.set_pixel_scale(self._pixel_scale)
        if isinstance(act, ActRectangle2D):
            act.set_size_limits(
                None if self._min_half is None else 2.0 * self._min_half,
                None if self._max_half is None else 2.0 * self._max_half,
            )
        elif isinstance(act, (ActCircle, ActEllipse)):
            act.set_radius_limits(self._min_half, self._max_half)

    def _add_shape(self, act: Any, style: Any) -> None:
        self._world.add(act, style=style)
        self._apply_size_limits(act)
        self._set_extra_handles(act, False)
        self._world.flush()

    def add_loaded_shape(self, act: Any) -> None:
        """Add a loaded labelme shape: style it and wire click-to-select."""
        self._add_shape(act, _loaded_style(act))
        act.set_on_click(self._make_select_handler())


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

    store = LabelMeStore(mapper=CalibratedPlaneMapper(calib, _DEPTH))

    viz = Visualizer(
        title="Tanga — Calibrated Labeling (T-LESS)",
        add_default_axes=False,
        add_default_grid=False,
    )
    world = viz.scene("world")

    labeler = _CalibratedLabeler(world, calib, _DEPTH)

    result = store.load(_LABELS_PATH)
    for message in result.errors:
        print(f"labelme: skipped {message}")
    pairs, errors = store.iter_objects(result.document, active=True)
    for message in errors:
        print(f"labelme: skipped {message}")
    for obj, _label in pairs:
        labeler.add_loaded_shape(obj)

    frustum = Frustum.from_camera(cam, near=0.05, far=0.7)
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
        surface=labeler.surface,
    )
    right = SceneView(
        "world",
        camera_view=CameraView(overview_cam),
        read_only=True,
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
