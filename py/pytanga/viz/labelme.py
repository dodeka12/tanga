# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Labelme (https://github.com/wkentaro/labelme) JSON load/store + scene mapping.

Loads/stores the labelme annotation format in dataclasses and maps every shape
type to a constant geometry entity or an active composite via
:meth:`LabelMeStore.add_shapes`.  The non-standard ``ellipse`` shape type is an
extension gated by ``allow_extensions``.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pytanga.geometry import Circle, Direction, Ellipse, Line, Point, Rectangle2D

if TYPE_CHECKING:
    from ._active import ActSceneObject
    from ._scene_handle import VizSceneHandle

_ELLIPSE = "ellipse"


@dataclass
class LabelShape:
    """One annotated shape (labelme ``shapes[]`` entry)."""

    label: str
    points: list[tuple[float, float]]
    shape_type: str
    group_id: int | None = None
    description: str = ""
    flags: dict[str, Any] = field(default_factory=dict)


@dataclass
class LabelMeDocument:
    """A labelme annotation document."""

    shapes: list[LabelShape]
    image_path: str = ""
    image_height: int | None = None
    image_width: int | None = None
    image_data: str | None = None
    version: str = "5.0.1"
    flags: dict[str, Any] = field(default_factory=dict)


class LabelMeStore:
    """Load/store labelme JSON and map shapes to entities or act composites."""

    def __init__(self, *, allow_extensions: bool = True) -> None:
        self._allow_extensions = allow_extensions

    # ── (De)serialization ─────────────────────────────────

    def load(self, path: str | os.PathLike[str]) -> LabelMeDocument:
        """Parse a labelme JSON file into a :class:`LabelMeDocument`."""
        with open(path, encoding="utf-8") as fh:
            return self.loads(fh.read())

    def loads(self, text: str) -> LabelMeDocument:
        """Parse labelme JSON text into a :class:`LabelMeDocument`."""
        data = json.loads(text)
        shapes = [
            LabelShape(
                label=s["label"],
                points=[(float(x), float(y)) for x, y in s["points"]],
                shape_type=s["shape_type"],
                group_id=s.get("group_id"),
                description=s.get("description", ""),
                flags=dict(s.get("flags", {})),
            )
            for s in data.get("shapes", [])
        ]
        return LabelMeDocument(
            shapes=shapes,
            image_path=data.get("imagePath", ""),
            image_height=data.get("imageHeight"),
            image_width=data.get("imageWidth"),
            image_data=data.get("imageData"),
            version=data.get("version", "5.0.1"),
            flags=dict(data.get("flags", {})),
        )

    def save(self, doc: LabelMeDocument, path: str | os.PathLike[str]) -> None:
        """Write a :class:`LabelMeDocument` to a labelme JSON file."""
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.dumps(doc))

    def dumps(self, doc: LabelMeDocument) -> str:
        """Serialize a :class:`LabelMeDocument` to labelme JSON text."""
        data = {
            "version": doc.version,
            "flags": doc.flags,
            "shapes": [
                {
                    "label": s.label,
                    "points": [[round(x, 2), round(y, 2)] for x, y in s.points],
                    "group_id": s.group_id,
                    "shape_type": s.shape_type,
                    "flags": s.flags,
                    "description": s.description,
                }
                for s in doc.shapes
            ],
            "imagePath": doc.image_path,
            "imageData": doc.image_data,
            "imageHeight": doc.image_height,
            "imageWidth": doc.image_width,
        }
        return json.dumps(data, indent=2, sort_keys=True)

    # ── Mapping helpers ────────────────────────────────────

    def add_shapes(
        self, handle: "VizSceneHandle", doc: LabelMeDocument, *, active: bool = True
    ) -> list[object]:
        """Add every shape in *doc* to *handle* as a constant or act object.

        Returns the list of added objects (callers can track/select them).
        """
        added: list[object] = []
        for shape in doc.shapes:
            obj = self._act_from_shape(shape) if active else self._entity_from_shape(shape)
            handle.add(obj, style=_default_style_for(shape.shape_type))
            added.append(obj)
        return added

    def iter_objects(
        self, doc: LabelMeDocument, *, active: bool = True
    ) -> list[tuple[object, str]]:
        """Map each shape to an ``(obj, label)`` pair without adding it."""
        return [
            (self._act_from_shape(s) if active else self._entity_from_shape(s), s.label)
            for s in doc.shapes
        ]

    def shapes_from_objects(
        self, objects: list[tuple[object, str]]
    ) -> list[LabelShape]:
        """Map ``(act-or-entity, label)`` pairs to :class:`LabelShape` entries."""
        result: list[LabelShape] = []
        for obj, label in objects:
            shape = self._shape_from_object(obj, label)
            if shape is not None:
                result.append(shape)
        return result

    # ── Entity builders ────────────────────────────────────

    def _entity_from_shape(self, shape: LabelShape) -> Any:
        pts = [Point(x, y, 0.0) for x, y in shape.points]
        st = shape.shape_type
        if st == "rectangle":
            return Rectangle2D.between(pts[0], pts[1])
        if st == "circle":
            center, rim = pts[0], pts[1]
            return Circle(
                center=center, radius=math.hypot(rim.x - center.x, rim.y - center.y)
            )
        if st == _ELLIPSE:
            return self._ellipse_entity(pts[0], pts[1], pts[2])
        if st == "polygon":
            return _path(pts, closed=True)
        if st == "linestrip":
            return _path(pts, closed=False)
        if st == "line":
            return Line.from_points(pts[0], pts[1])
        if st == "point":
            return pts[0]
        raise ValueError(f"Unknown labelme shape_type: {st!r}")

    def _act_from_shape(self, shape: LabelShape) -> "ActSceneObject":
        from ._active import (
            ActCircle,
            ActEllipse,
            ActLine,
            ActPoint,
            ActPolygon,
            ActRectangle2D,
        )
        from ._interaction import DragMode

        pts = [Point(x, y, 0.0) for x, y in shape.points]
        st = shape.shape_type
        if st == "rectangle":
            return ActRectangle2D.create_from_points(pts[0], pts[1])
        if st == "circle":
            return ActCircle.create_from_points(pts[0], pts[1])
        if st == _ELLIPSE:
            ellipse = self._ellipse_entity(pts[0], pts[1], pts[2])
            du, _dv = _ellipse_axes(ellipse)
            angle = math.atan2(du.y, du.x)
            return ActEllipse(
                center=ellipse.center,
                radius_u=ellipse.radius_u,
                radius_v=ellipse.radius_v,
                angle=angle,
            )
        if st == "polygon":
            return ActPolygon(pts, closed=True)
        if st == "linestrip":
            return ActPolygon(pts, closed=False)
        if st == "line":
            return ActLine.create_from_points(pts[0], pts[1])
        if st == "point":
            return ActPoint(pts[0], drag_mode=DragMode.XY_PLANE)
        raise ValueError(f"Unknown labelme shape_type: {st!r}")

    @staticmethod
    def _ellipse_entity(center: Point, rim_u: Point, rim_v: Point) -> Ellipse:
        du = Direction(rim_u.x - center.x, rim_u.y - center.y, 0.0)
        dv = Direction(rim_v.x - center.x, rim_v.y - center.y, 0.0)
        return Ellipse(
            center=center,
            radius_u=du.mag(),
            radius_v=dv.mag(),
            dir_u=du.normalized(),
            dir_v=dv.normalized(),
        )

    # ── Inverse (object → shape) ───────────────────────────

    def _shape_from_object(self, obj: Any, label: str) -> LabelShape | None:
        from ._active import (
            ActCircle,
            ActEllipse,
            ActLine,
            ActPoint,
            ActPolygon,
            ActRectangle2D,
        )

        if isinstance(obj, (ActRectangle2D, Rectangle2D)):
            rect = obj.rectangle if isinstance(obj, ActRectangle2D) else obj
            if abs(rect.angle) < 1e-9:
                hw, hh = rect.size[0] / 2.0, rect.size[1] / 2.0
                return LabelShape(
                    label=label,
                    points=[
                        (rect.center.x - hw, rect.center.y - hh),
                        (rect.center.x + hw, rect.center.y + hh),
                    ],
                    shape_type="rectangle",
                )
            return self._polygon_from_corners(rect, label)
        if isinstance(obj, (ActCircle, Circle)):
            circle = obj.circle if isinstance(obj, ActCircle) else obj
            return LabelShape(
                label=label,
                points=[
                    (circle.center.x, circle.center.y),
                    (circle.center.x + circle.radius, circle.center.y),
                ],
                shape_type="circle",
            )
        if isinstance(obj, (ActEllipse, Ellipse)):
            return self._shape_from_ellipse(obj, label)
        if isinstance(obj, ActPolygon):
            return LabelShape(
                label=label,
                points=[(p.x, p.y) for p in obj.points],
                shape_type="polygon" if obj.closed else "linestrip",
            )
        if isinstance(obj, (ActLine, Line)):
            line = obj.line if isinstance(obj, ActLine) else obj
            return LabelShape(
                label=label,
                points=[(line.start.x, line.start.y), (line.end.x, line.end.y)],
                shape_type="line",
            )
        if isinstance(obj, (ActPoint, Point)):
            p = obj.point if isinstance(obj, ActPoint) else obj
            return LabelShape(label=label, points=[(p.x, p.y)], shape_type="point")
        return None

    def _shape_from_ellipse(self, obj: Any, label: str) -> LabelShape | None:
        from ._active import ActEllipse

        ellipse = obj.ellipse if isinstance(obj, ActEllipse) else obj
        du, dv = _ellipse_axes(ellipse)
        if not self._allow_extensions:
            if abs(ellipse.radius_u - ellipse.radius_v) < 1e-6:
                return LabelShape(
                    label=label,
                    points=[
                        (ellipse.center.x, ellipse.center.y),
                        (ellipse.center.x + ellipse.radius_u, ellipse.center.y),
                    ],
                    shape_type="circle",
                )
            return self._polygon_from_ellipse(ellipse, label)
        return LabelShape(
            label=label,
            points=[
                (ellipse.center.x, ellipse.center.y),
                (ellipse.center.x + du.x * ellipse.radius_u,
                 ellipse.center.y + du.y * ellipse.radius_u),
                (ellipse.center.x + dv.x * ellipse.radius_v,
                 ellipse.center.y + dv.y * ellipse.radius_v),
            ],
            shape_type=_ELLIPSE,
        )

    @staticmethod
    def _polygon_from_corners(rect: Rectangle2D, label: str) -> LabelShape:
        cx, cy = rect.center.x, rect.center.y
        hw, hh = rect.size[0] / 2.0, rect.size[1] / 2.0
        cos_a, sin_a = math.cos(rect.angle), math.sin(rect.angle)
        ux, uy = cos_a, sin_a
        vx, vy = -sin_a, cos_a
        corners = [
            (cx - hw * ux - hh * vx, cy - hw * uy - hh * vy),
            (cx + hw * ux - hh * vx, cy + hw * uy - hh * vy),
            (cx + hw * ux + hh * vx, cy + hw * uy + hh * vy),
            (cx - hw * ux + hh * vx, cy - hw * uy + hh * vy),
        ]
        return LabelShape(label=label, points=corners, shape_type="polygon")

    @staticmethod
    def _polygon_from_ellipse(ellipse: Ellipse, label: str) -> LabelShape:
        n = 32
        du, dv = _ellipse_axes(ellipse)
        points = [
            (
                ellipse.center.x + du.x * ellipse.radius_u * math.cos(t)
                + dv.x * ellipse.radius_v * math.sin(t),
                ellipse.center.y + du.y * ellipse.radius_u * math.cos(t)
                + dv.y * ellipse.radius_v * math.sin(t),
            )
            for t in (2.0 * math.pi * i / n for i in range(n))
        ]
        return LabelShape(label=label, points=points, shape_type="polygon")


def _path(pts: list[Point], *, closed: bool) -> object:
    from ._point_path import PointPath

    path = PointPath()
    for p in pts:
        path.add((p.x, p.y, p.z))
    if closed and pts:
        path.add((pts[0].x, pts[0].y, pts[0].z))
    return path


def _ellipse_axes(ellipse: Ellipse) -> tuple[Direction, Direction]:
    """The (possibly axis-aligned) semi-axis directions of an ellipse."""
    if ellipse.dir_u is None or ellipse.dir_v is None:
        return Direction(1.0, 0.0, 0.0), Direction(0.0, 1.0, 0.0)
    return ellipse.dir_u, ellipse.dir_v


def _default_style_for(shape_type: str) -> object:
    from ._styles._entity_styles import (
        CircleStyle,
        EllipseStyle,
        LineStyle,
        PointPathStyle,
        PointStyle,
        Rectangle2DStyle,
    )

    if shape_type == "rectangle":
        return Rectangle2DStyle()
    if shape_type == "circle":
        return CircleStyle()
    if shape_type == _ELLIPSE:
        return EllipseStyle()
    if shape_type in ("polygon", "linestrip"):
        return PointPathStyle()
    if shape_type == "line":
        return LineStyle()
    return PointStyle()
