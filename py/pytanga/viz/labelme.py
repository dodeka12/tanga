# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Labelme (https://github.com/wkentaro/labelme) JSON load/store + scene mapping.

Loads/stores the labelme annotation format in dataclasses and maps every shape
type to a plain geometry entity (``Point``, ``Line``, ``Circle``, ``Ellipse``,
``Rectangle2D``, ``PointPath``) via :meth:`LabelMeStore.add_shapes`.  The store
is data-only: it never creates :class:`~pytanga.viz.ActSceneObject` composites
(the labeling apps wrap the entities into interactive acts).  The non-standard
``ellipse`` shape type is an extension gated by ``allow_extensions``.
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
    from ._scene_handle import VizSceneHandle
    from ._styles import ObjVizStyle

_ELLIPSE = "ellipse"

#: Minimum point count per shape type; a non-None exact value must match exactly.
_POINT_COUNTS: dict[str, tuple[int, int | None]] = {
    "rectangle": (2, None),
    "circle": (2, None),
    "polygon": (3, None),
    "linestrip": (2, None),
    "line": (2, None),
    "point": (1, None),
}


@dataclass
class LabelShape:
    """One annotated shape (labelme ``shapes[]`` entry).

    ``mask`` / ``description`` are round-tripped verbatim from labelme JSON.
    ``radius_u`` / ``radius_v`` / ``angle`` carry the scalar ellipse parameters
    (new canonical form; ``None`` for legacy shapes).  ``style`` / ``act`` are
    in-memory back-references used by an editor (e.g. ``ImageLabeler``) and are
    never (de)serialized — labelme has no such concept.
    """

    label: str
    points: list[tuple[float, float]] = field(default_factory=list)
    shape_type: str = ""
    group_id: int | None = None
    description: str | None = None
    flags: dict[str, Any] = field(default_factory=dict)
    mask: str | None = None
    radius_u: float | None = None
    radius_v: float | None = None
    angle: float | None = None
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
                radius_u=s.get("radius_u"),
                radius_v=s.get("radius_v"),
                angle=s.get("angle"),
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
                    **({"radius_u": _round(s.radius_u)} if s.radius_u is not None else {}),
                    **({"radius_v": _round(s.radius_v)} if s.radius_v is not None else {}),
                    **({"angle": _round(s.angle)} if s.angle is not None else {}),
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
        self, handle: "VizSceneHandle", doc: LabelMeDocument
    ) -> tuple[list[object], list[str]]:
        """Add every shape in *doc* to *handle* as a constant geometry entity.

        Returns ``(added, errors)`` — the added objects plus the shapes that were
        skipped (reported, never raised).
        """
        added: list[object] = []
        errors: list[str] = []
        for i, shape in enumerate(doc.shapes):
            try:
                obj = self._entity_from_shape(shape)
            except ValueError as exc:
                errors.append(f"shape {i} ({shape.label!r}): {exc}")
                continue
            handle.add(obj, style=_default_style_for(shape.shape_type))
            added.append(obj)
        return added, errors

    def iter_objects(
        self, doc: LabelMeDocument
    ) -> tuple[list[tuple[object, str]], list[str]]:
        """Map each shape to an ``(entity, label)`` pair without adding it.

        Returns ``(pairs, errors)`` — the mapped pairs plus the shapes that were
        skipped.
        """
        pairs: list[tuple[object, str]] = []
        errors: list[str] = []
        for i, s in enumerate(doc.shapes):
            try:
                obj = self._entity_from_shape(s)
            except ValueError as exc:
                errors.append(f"shape {i} ({s.label!r}): {exc}")
                continue
            pairs.append((obj, s.label))
        return pairs, errors

    def shapes_from_objects(
        self, objects: list[tuple[object, str]]
    ) -> list[LabelShape]:
        """Map ``(entity, label)`` pairs to :class:`LabelShape` entries."""
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
        if shape.shape_type == _ELLIPSE:
            has_ru = shape.radius_u is not None
            has_rv = shape.radius_v is not None
            if has_ru != has_rv:
                return "ellipse needs both radius_u and radius_v (or neither, for the legacy rim form)"
            if has_ru:
                if len(shape.points) != 1:
                    return (
                        f"ellipse (params form) needs exactly 1 point, got "
                        f"{len(shape.points)}"
                    )
                return None
            if len(shape.points) != 3:
                return (
                    f"ellipse (legacy rim form) needs exactly 3 points, got "
                    f"{len(shape.points)}"
                )
            return None
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
            return self._rectangle_entity(pts[0], pts[1])
        if st == "circle":
            center, rim = pts[0], pts[1]
            return Circle(
                center=center,
                radius=math.sqrt(
                    (rim.x - center.x) ** 2
                    + (rim.y - center.y) ** 2
                    + (rim.z - center.z) ** 2
                ),
            )
        if st == _ELLIPSE:
            if shape.radius_u is not None:
                return self._ellipse_from_params(shape, pts[0])
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

    def _rectangle_entity(self, a: Point, b: Point) -> Rectangle2D:
        du, dv = self._mapper.pixel_axes()
        dx = Direction(b.x - a.x, b.y - a.y, b.z - a.z)
        return Rectangle2D(
            center=Point(
                (a.x + b.x) / 2.0, (a.y + b.y) / 2.0, (a.z + b.z) / 2.0
            ),
            size=(abs(dx.dot(du)), abs(dx.dot(dv))),
            normal=du.cross(dv).normalized(),
            angle=0.0,
            dir_u=du,
            dir_v=dv,
        )

    def _ellipse_from_params(self, shape: LabelShape, center: Point) -> Ellipse:
        du, dv = self._mapper.pixel_axes()
        scale = self._mapper.world_units_per_pixel()
        return Ellipse(
            center=center,
            radius_u=float(shape.radius_u or 0.0) * scale,
            radius_v=float(shape.radius_v or 0.0) * scale,
            normal=du.cross(dv).normalized(),
            dir_u=du,
            dir_v=dv,
            angle=0.0 if shape.angle is None else float(shape.angle),
        )

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
        from ._point_path import PointPath

        if isinstance(obj, Rectangle2D):
            return self._shape_from_rectangle(obj, label)
        if isinstance(obj, Circle):
            circle = obj
            du, _ = self._mapper.pixel_axes()
            return LabelShape(
                label=label,
                points=[
                    self._mapper.to_pixel(circle.center),
                    self._mapper.to_pixel(
                        Point(
                            circle.center.x + circle.radius * du.x,
                            circle.center.y + circle.radius * du.y,
                            circle.center.z + circle.radius * du.z,
                        )
                    ),
                ],
                shape_type="circle",
            )
        if isinstance(obj, Ellipse):
            return self._shape_from_ellipse(obj, label)
        if isinstance(obj, PointPath):
            pts = obj.points
            closed = len(pts) > 1 and pts[0] == pts[-1]
            if closed:
                pts = pts[:-1]
            return LabelShape(
                label=label,
                points=[self._mapper.to_pixel(Point(x, y, z)) for x, y, z in pts],
                shape_type="polygon" if closed else "linestrip",
            )
        if isinstance(obj, Line):
            line = obj
            return LabelShape(
                label=label,
                points=[
                    self._mapper.to_pixel(line.start),
                    self._mapper.to_pixel(line.end),
                ],
                shape_type="line",
            )
        if isinstance(obj, Point):
            p = obj
            return LabelShape(
                label=label,
                points=[self._mapper.to_pixel(p)],
                shape_type="point",
            )
        return None

    def _shape_from_ellipse(self, obj: Any, label: str) -> LabelShape | None:
        ellipse = obj
        scale = self._mapper.world_units_per_pixel()
        if not self._allow_extensions:
            if abs(ellipse.radius_u - ellipse.radius_v) < 1e-6:
                du, _ = self._mapper.pixel_axes()
                return LabelShape(
                    label=label,
                    points=[
                        self._mapper.to_pixel(ellipse.center),
                        self._mapper.to_pixel(
                            Point(
                                ellipse.center.x + ellipse.radius_u * du.x,
                                ellipse.center.y + ellipse.radius_u * du.y,
                                ellipse.center.z + ellipse.radius_u * du.z,
                            )
                        ),
                    ],
                    shape_type="circle",
                )
            return self._polygon_from_ellipse(ellipse, label)
        pixel_u, _ = self._mapper.pixel_axes()
        du, dv = self._basis(ellipse.normal, ellipse.dir_u, ellipse.dir_v)
        angle_px = ellipse.angle + _signed_angle(
            pixel_u, du, du.cross(dv).normalized()
        )
        return LabelShape(
            label=label,
            points=[self._mapper.to_pixel(ellipse.center)],
            radius_u=ellipse.radius_u / scale,
            radius_v=ellipse.radius_v / scale,
            angle=angle_px,
            shape_type=_ELLIPSE,
        )

    def _shape_from_rectangle(self, rect: Rectangle2D, label: str) -> LabelShape:
        du, dv = self._rect_axes(rect)
        hw, hh = rect.size[0] / 2.0, rect.size[1] / 2.0
        cx, cy, cz = rect.center.x, rect.center.y, rect.center.z
        corners = [
            self._mapper.to_pixel(
                Point(
                    cx - hw * du.x - hh * dv.x,
                    cy - hw * du.y - hh * dv.y,
                    cz - hw * du.z - hh * dv.z,
                )
            ),
            self._mapper.to_pixel(
                Point(
                    cx + hw * du.x - hh * dv.x,
                    cy + hw * du.y - hh * dv.y,
                    cz + hw * du.z - hh * dv.z,
                )
            ),
            self._mapper.to_pixel(
                Point(
                    cx + hw * du.x + hh * dv.x,
                    cy + hw * du.y + hh * dv.y,
                    cz + hw * du.z + hh * dv.z,
                )
            ),
            self._mapper.to_pixel(
                Point(
                    cx - hw * du.x + hh * dv.x,
                    cy - hw * du.y + hh * dv.y,
                    cz - hw * du.z + hh * dv.z,
                )
            ),
        ]
        if _is_axis_aligned(corners):
            xs = [c[0] for c in corners]
            ys = [c[1] for c in corners]
            return LabelShape(
                label=label,
                points=[(min(xs), min(ys)), (max(xs), max(ys))],
                shape_type="rectangle",
            )
        return LabelShape(label=label, points=corners, shape_type="polygon")

    def _rect_axes(self, rect: Rectangle2D) -> tuple[Direction, Direction]:
        du, dv = self._basis(rect.normal, rect.dir_u, rect.dir_v)
        return _rotated_axes(du, dv, rect.angle)

    def _basis(
        self, normal: Direction, dir_u: Direction | None, dir_v: Direction | None
    ) -> tuple[Direction, Direction]:
        if dir_u is not None and dir_v is not None:
            return dir_u.normalized(), dir_v.normalized()
        from ._active import _plane_basis

        return _plane_basis(normal)

    def to_act(self, entity: Any, **kwargs: Any) -> Any:
        """Wrap a plain geometry entity in its interactive act (lazy import).

        Convenience wrapper over the ``Act*.from_entity`` classmethods; the
        store's load/save API remains data-only.
        """
        from ._active import ActCircle, ActEllipse, ActRectangle2D

        if isinstance(entity, Rectangle2D):
            return ActRectangle2D.from_entity(entity, **kwargs)
        if isinstance(entity, Ellipse):
            return ActEllipse.from_entity(entity, **kwargs)
        if isinstance(entity, Circle):
            return ActCircle.from_entity(entity, **kwargs)
        raise TypeError(f"unsupported entity for to_act: {type(entity).__name__}")

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


def _rotated_axes(
    du: Direction, dv: Direction, angle: float
) -> tuple[Direction, Direction]:
    """Rotate an orthonormal in-plane basis ``(du, dv)`` by ``angle`` about its normal."""
    c, s = math.cos(angle), math.sin(angle)
    return (
        Direction(c * du.x + s * dv.x, c * du.y + s * dv.y, c * du.z + s * dv.z),
        Direction(-s * du.x + c * dv.x, -s * du.y + c * dv.y, -s * du.z + c * dv.z),
    )


def _signed_angle(u: Direction, v: Direction, normal: Direction) -> float:
    """Signed angle from *u* to *v* about *normal* (right-hand rule), radians."""
    return math.atan2(normal.dot(u.cross(v)), u.dot(v))


def _is_axis_aligned(corners: list[tuple[float, float]]) -> bool:
    """Return whether four ordered corners form an axis-aligned pixel rectangle."""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = corners
    tol = 1e-6
    return (
        abs(x0 - x3) < tol
        and abs(x1 - x2) < tol
        and abs(y0 - y1) < tol
        and abs(y2 - y3) < tol
    )


def _ellipse_axes(ellipse: Ellipse) -> tuple[Direction, Direction]:
    """The actual (angle-rotated) semi-axis directions of an ellipse."""
    axes = ellipse.axis_directions()
    if axes is not None:
        return axes
    from ._active import _plane_basis

    du, dv = _plane_basis(ellipse.normal)
    return _rotated_axes(du, dv, ellipse.angle)


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
