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

from .camera import CoordinateMapper, PlanarMapper

if TYPE_CHECKING:
    from ._active import ActSceneObject
    from ._scene_handle import VizSceneHandle
    from ._styles import ObjVizStyle

_ELLIPSE = "ellipse"

#: Minimum point count per shape type; a non-None exact value must match exactly.
_POINT_COUNTS: dict[str, tuple[int, int | None]] = {
    "rectangle": (2, None),
    "circle": (2, None),
    _ELLIPSE: (3, 3),
    "polygon": (3, None),
    "linestrip": (2, None),
    "line": (2, None),
    "point": (1, None),
}


@dataclass
class LabelShape:
    """One annotated shape (labelme ``shapes[]`` entry).

    ``mask`` / ``description`` are round-tripped verbatim from labelme JSON.
    ``style`` / ``act`` are in-memory back-references used by an editor (e.g.
    ``ImageLabeler``) and are never (de)serialized — labelme has no such concept.
    """

    label: str
    points: list[tuple[float, float]] = field(default_factory=list)
    shape_type: str = ""
    group_id: int | None = None
    description: str | None = None
    flags: dict[str, Any] = field(default_factory=dict)
    mask: str | None = None
    style: ObjVizStyle | None = None
    act: Any = field(default=None, repr=False, compare=False)


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


@dataclass
class LabelMeLoadResult:
    """A parsed :class:`LabelMeDocument` plus the shapes that were skipped."""

    document: LabelMeDocument
    errors: list[str]


class LabelMeStore:
    """Load/store labelme JSON and map shapes to entities or act composites."""

    def __init__(
        self,
        *,
        allow_extensions: bool = True,
        mapper: CoordinateMapper | None = None,
        coordinate_precision: int | None = None,
    ) -> None:
        self._allow_extensions = allow_extensions
        self._mapper: CoordinateMapper = mapper if mapper is not None else PlanarMapper()
        self._coordinate_precision = coordinate_precision

    # ── (De)serialization ─────────────────────────────────

    def load(self, path: str | os.PathLike[str]) -> LabelMeLoadResult:
        """Parse a labelme JSON file into a :class:`LabelMeLoadResult`."""
        with open(path, encoding="utf-8") as fh:
            return self.loads(fh.read())

    def loads(self, text: str) -> LabelMeLoadResult:
        """Parse labelme JSON text into a :class:`LabelMeLoadResult`.

        Malformed shapes (wrong point count) are skipped and reported in
        ``errors``; the store never raises for a single bad shape.
        """
        data = json.loads(text)
        shapes: list[LabelShape] = []
        errors: list[str] = []
        for i, s in enumerate(data.get("shapes", [])):
            shape = LabelShape(
                label=s["label"],
                points=[(float(x), float(y)) for x, y in s["points"]],
                shape_type=s["shape_type"],
                group_id=s.get("group_id"),
                description=s.get("description"),
                flags=dict(s.get("flags", {})),
                mask=s.get("mask"),
            )
            err = self._validate_points(shape)
            if err is not None:
                errors.append(f"shape {i} ({shape.label!r}): {err}")
                continue
            shapes.append(shape)
        return LabelMeLoadResult(
            document=LabelMeDocument(
                shapes=shapes,
                image_path=data.get("imagePath", ""),
                image_height=data.get("imageHeight"),
                image_width=data.get("imageWidth"),
                image_data=data.get("imageData"),
                version=data.get("version", "5.0.1"),
                flags=dict(data.get("flags", {})),
            ),
            errors=errors,
        )

    def save(self, doc: LabelMeDocument, path: str | os.PathLike[str]) -> None:
        """Write a :class:`LabelMeDocument` to a labelme JSON file."""
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.dumps(doc))

    def dumps(self, doc: LabelMeDocument) -> str:
        """Serialize a :class:`LabelMeDocument` to labelme JSON text.

        Keys are emitted in labelme's own writer order and coordinates are
        written at full precision unless ``coordinate_precision`` was set.
        """
        precision = self._coordinate_precision

        def _round(v: float) -> float:
            return round(v, precision) if precision is not None else v

        data = {
            "version": doc.version,
            "flags": doc.flags,
            "shapes": [
                {
                    "label": s.label,
                    "points": [[_round(x), _round(y)] for x, y in s.points],
                    "group_id": s.group_id,
                    "shape_type": s.shape_type,
                    "flags": s.flags,
                    **({"description": s.description} if s.description is not None else {}),
                    **({"mask": s.mask} if s.mask is not None else {}),
                }
                for s in doc.shapes
            ],
            "imagePath": doc.image_path,
            "imageData": doc.image_data,
            "imageHeight": doc.image_height,
            "imageWidth": doc.image_width,
        }
        return json.dumps(data, indent=4)

    # ── Mapping helpers ────────────────────────────────────

    def add_shapes(
        self, handle: "VizSceneHandle", doc: LabelMeDocument, *, active: bool = True
    ) -> tuple[list[object], list[str]]:
        """Add every shape in *doc* to *handle* as a constant or act object.

        Returns ``(added, errors)`` — the added objects plus the shapes that were
        skipped (reported, never raised).
        """
        added: list[object] = []
        errors: list[str] = []
        for i, shape in enumerate(doc.shapes):
            try:
                obj = self._act_from_shape(shape) if active else self._entity_from_shape(shape)
            except ValueError as exc:
                errors.append(f"shape {i} ({shape.label!r}): {exc}")
                continue
            handle.add(obj, style=_default_style_for(shape.shape_type))
            added.append(obj)
        return added, errors

    def iter_objects(
        self, doc: LabelMeDocument, *, active: bool = True
    ) -> tuple[list[tuple[object, str]], list[str]]:
        """Map each shape to an ``(obj, label)`` pair without adding it.

        Returns ``(pairs, errors)`` — the mapped pairs plus the shapes that were
        skipped.
        """
        pairs: list[tuple[object, str]] = []
        errors: list[str] = []
        for i, s in enumerate(doc.shapes):
            try:
                obj = self._act_from_shape(s) if active else self._entity_from_shape(s)
            except ValueError as exc:
                errors.append(f"shape {i} ({s.label!r}): {exc}")
                continue
            pairs.append((obj, s.label))
        return pairs, errors

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

    @staticmethod
    def _validate_points(shape: LabelShape) -> str | None:
        """Return an error message if *shape* has an invalid point count."""
        expected_min, expected_exact = _POINT_COUNTS.get(shape.shape_type, (0, None))
        got = len(shape.points)
        if expected_exact is not None:
            if got != expected_exact:
                return (
                    f"{shape.shape_type!r} needs exactly {expected_exact} points, "
                    f"got {got}"
                )
            return None
        if got < expected_min:
            return (
                f"{shape.shape_type!r} needs at least {expected_min} points, got {got}"
            )
        return None

    def _entity_from_shape(self, shape: LabelShape) -> Any:
        err = self._validate_points(shape)
        if err is not None:
            raise ValueError(err)
        pts = [self._mapper.to_world(x, y) for x, y in shape.points]
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

        err = self._validate_points(shape)
        if err is not None:
            raise ValueError(err)
        pts = [self._mapper.to_world(x, y) for x, y in shape.points]
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
            return ActPoint(pts[0], drag_mode=DragMode.VIEW_PLANE)
        raise ValueError(f"Unknown labelme shape_type: {st!r}")

    @staticmethod
    def _ellipse_entity(center: Point, rim_u: Point, rim_v: Point) -> Ellipse:
        du = Direction(rim_u.x - center.x, rim_u.y - center.y, rim_u.z - center.z)
        dv = Direction(rim_v.x - center.x, rim_v.y - center.y, rim_v.z - center.z)
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
                        self._mapper.to_pixel(
                            Point(
                                rect.center.x - hw,
                                rect.center.y - hh,
                                rect.center.z,
                            )
                        ),
                        self._mapper.to_pixel(
                            Point(
                                rect.center.x + hw,
                                rect.center.y + hh,
                                rect.center.z,
                            )
                        ),
                    ],
                    shape_type="rectangle",
                )
            return self._polygon_from_corners(rect, label)
        if isinstance(obj, (ActCircle, Circle)):
            circle = obj.circle if isinstance(obj, ActCircle) else obj
            return LabelShape(
                label=label,
                points=[
                    self._mapper.to_pixel(circle.center),
                    self._mapper.to_pixel(
                        Point(
                            circle.center.x + circle.radius,
                            circle.center.y,
                            circle.center.z,
                        )
                    ),
                ],
                shape_type="circle",
            )
        if isinstance(obj, (ActEllipse, Ellipse)):
            return self._shape_from_ellipse(obj, label)
        if isinstance(obj, ActPolygon):
            return LabelShape(
                label=label,
                points=[self._mapper.to_pixel(p) for p in obj.points],
                shape_type="polygon" if obj.closed else "linestrip",
            )
        if isinstance(obj, (ActLine, Line)):
            line = obj.line if isinstance(obj, ActLine) else obj
            return LabelShape(
                label=label,
                points=[
                    self._mapper.to_pixel(line.start),
                    self._mapper.to_pixel(line.end),
                ],
                shape_type="line",
            )
        if isinstance(obj, (ActPoint, Point)):
            p = obj.point if isinstance(obj, ActPoint) else obj
            return LabelShape(
                label=label,
                points=[self._mapper.to_pixel(p)],
                shape_type="point",
            )
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
                        self._mapper.to_pixel(ellipse.center),
                        self._mapper.to_pixel(
                            Point(
                                ellipse.center.x + ellipse.radius_u,
                                ellipse.center.y,
                                ellipse.center.z,
                            )
                        ),
                    ],
                    shape_type="circle",
                )
            return self._polygon_from_ellipse(ellipse, label)
        return LabelShape(
            label=label,
            points=[
                self._mapper.to_pixel(ellipse.center),
                self._mapper.to_pixel(
                    Point(
                        ellipse.center.x + du.x * ellipse.radius_u,
                        ellipse.center.y + du.y * ellipse.radius_u,
                        ellipse.center.z + du.z * ellipse.radius_u,
                    )
                ),
                self._mapper.to_pixel(
                    Point(
                        ellipse.center.x + dv.x * ellipse.radius_v,
                        ellipse.center.y + dv.y * ellipse.radius_v,
                        ellipse.center.z + dv.z * ellipse.radius_v,
                    )
                ),
            ],
            shape_type=_ELLIPSE,
        )

    def _polygon_from_corners(self, rect: Rectangle2D, label: str) -> LabelShape:
        cx, cy, cz = rect.center.x, rect.center.y, rect.center.z
        hw, hh = rect.size[0] / 2.0, rect.size[1] / 2.0
        cos_a, sin_a = math.cos(rect.angle), math.sin(rect.angle)
        ux, uy = cos_a, sin_a
        vx, vy = -sin_a, cos_a
        corners = [
            self._mapper.to_pixel(
                Point(cx - hw * ux - hh * vx, cy - hw * uy - hh * vy, cz)
            ),
            self._mapper.to_pixel(
                Point(cx + hw * ux - hh * vx, cy + hw * uy - hh * vy, cz)
            ),
            self._mapper.to_pixel(
                Point(cx + hw * ux + hh * vx, cy + hw * uy + hh * vy, cz)
            ),
            self._mapper.to_pixel(
                Point(cx - hw * ux + hh * vx, cy - hw * uy + hh * vy, cz)
            ),
        ]
        return LabelShape(label=label, points=corners, shape_type="polygon")

    def _polygon_from_ellipse(self, ellipse: Ellipse, label: str) -> LabelShape:
        n = 32
        du, dv = _ellipse_axes(ellipse)
        points = [
            self._mapper.to_pixel(
                Point(
                    ellipse.center.x + du.x * ellipse.radius_u * math.cos(t)
                    + dv.x * ellipse.radius_v * math.sin(t),
                    ellipse.center.y + du.y * ellipse.radius_u * math.cos(t)
                    + dv.y * ellipse.radius_v * math.sin(t),
                    ellipse.center.z + du.z * ellipse.radius_u * math.cos(t)
                    + dv.z * ellipse.radius_v * math.sin(t),
                )
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


def _default_style_for(shape_type: str) -> ObjVizStyle:
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
