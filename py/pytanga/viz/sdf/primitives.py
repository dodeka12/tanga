# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""SDF primitive/combinator descriptor model for the SDF viewer.

These dataclasses describe an SDF tree in a JSON-friendly, frontend-consumable
form. The frontend ``scene-builder.js`` dispatches on ``kind`` to emit the
matching GLSL expression (mirroring the existing ``renderers/factory.js``
layout). Primitives take their point in *local* space; a ``transform`` places
them in world space (or clips an infinite entity via an explicit ``bound``).

The ``kind`` strings are the shared vocabulary between Python and the GLSL
library in ``templates/sdf/shaders/primitives.glsl``:

    sphere, ellipsoid, box, roundBox, cylinder, cappedCylinder, cone,
    cappedCone, torus, capsule, segment, plane  (+ ``bound`` = a clip box)

Combinators fold child trees with IQ sign-preserving min/max:

    union, intersect, subtract

plus ``group``, which folds its children in order using each child's own
``combine`` mode (``union`` / ``intersection`` / ``subtract``). A node's
``combine`` field is meaningful only when the node is a child of a ``group``;
it is how :class:`~pytanga.viz.sdf.composed.Composed` objects express
per-constituent boolean composition.

The module also exposes ergonomic named constructors (``sphere``, ``box``,
``cylinder``, …) over :func:`primitive` for building the fundamental
distance-function object library directly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from pytanga.viz._types import Rotation, Vec3, _as_vec3

#: A position argument for the constructors: a Point/Direction entity or a
#: ``(x, y, z)`` 3-sequence.
Position = Vec3


@dataclass
class SdfNode:
    """One SDF tree node (a primitive or a combinator).

    Attributes:
        kind: The node kind (primitive or combinator name).
        params: Typed parameters for the primitive (radius, halfExtents, …).
        transform: Optional ``{"position": [x,y,z], "rotation": {"axis":
            [x,y,z], "angle": float}}`` world transform.
        children: Child nodes for combinators (``None`` for primitives).
        combine: Optional fold mode (``union``/``intersection``/``subtract``)
            used when this node is a child of a ``group`` node. ``None`` means
            the default (``union``).
        id: Optional name, so a node (e.g. an :class:`SdfGroup` member) can be
            referenced by string instead of by index.
        smoothness: Optional blend radius for smooth combinators (used only when
            this node is a child folded by a ``smooth_*`` combine mode).
    """

    kind: str
    params: dict[str, Any] = field(default_factory=dict)
    transform: dict[str, Any] | None = None
    children: list["SdfNode"] | None = None
    combine: str | None = None
    id: str | None = None
    smoothness: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-ready dict, omitting empty sections."""
        result: dict[str, Any] = {"kind": self.kind}
        if self.params:
            result["params"] = self.params
        if self.transform:
            result["transform"] = self.transform
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        if self.combine:
            result["combine"] = self.combine
        if self.id:
            result["id"] = self.id
        if self.smoothness is not None:
            result["smoothness"] = self.smoothness
        return result


def primitive(
    kind: str,
    params: dict[str, Any] | None = None,
    *,
    id: str | None = None,
    position: Position = None,
    rotation: Rotation = None,
    **extra_params: Any,
) -> SdfNode:
    """Build a primitive node with an optional world transform.

    Args:
        kind: The primitive kind (see module docstring).
        params: Typed primitive parameters.
        id: Optional name for the node (e.g. to reference an ``SdfGroup``
            member by string instead of by index).
        position: World-space translation — a Point/Direction entity or a
            ``(x, y, z)`` 3-sequence.
        rotation: World-space rotation — a ``Rotor`` entity or an
            ``(axis, angle_radians)`` pair (aligns the primitive's canonical
            axis onto the target direction).
        **extra_params: Additional typed parameters folded into ``params``.
    """
    merged: dict[str, Any] = dict(params or {})
    merged.update(extra_params)
    transform = _make_transform(position=position, rotation=rotation)
    return SdfNode(kind=kind, params=merged, transform=transform, id=id)


def combine(
    op: str,
    *children: SdfNode,
    id: str | None = None,
    smoothness: float | None = None,
) -> SdfNode:
    """Build a combinator node folding the child trees.

    ``smoothness`` is the blend radius for ``smooth_*`` ops and is ignored
    otherwise.
    """
    return SdfNode(kind=op, children=list(children), id=id, smoothness=smoothness)


def group(
    children: list[SdfNode] | tuple[SdfNode, ...],
    *,
    id: str | None = None,
) -> SdfNode:
    """Build a ``group`` node folding its children in order.

    Unlike :func:`combine` (one op for every child), a ``group`` folds each
    child using that child's own ``combine`` mode (``union`` / ``intersection``
    / ``subtract``). Children are tagged by setting ``SdfNode.combine``.
    """
    return SdfNode(kind="group", children=list(children), id=id)


def bound_box(
    half_extents: tuple[float, float, float],
    *,
    id: str | None = None,
    position: Position = None,
    rotation: Rotation = None,
) -> SdfNode:
    """Build a finite clip box (``bound``) for an infinite entity."""
    transform = _make_transform(position=position, rotation=rotation)
    return SdfNode(
        kind="bound",
        params={"halfExtents": list(half_extents)},
        transform=transform,
        id=id,
    )


def _make_transform(
    *,
    position: Position = None,
    rotation: Rotation = None,
) -> dict[str, Any] | None:
    """Build a transform dict, omitting identity components (returns ``None``
    when both position and rotation are absent/identity)."""
    if position is None and rotation is None:
        return None
    transform: dict[str, Any] = {}
    if position is not None:
        transform["position"] = list(_as_vec3(position))
    if rotation is not None:
        axis, angle = _as_rotation(rotation)
        transform["rotation"] = {"axis": list(axis), "angle": float(angle)}
    return transform or None


# ── Named primitive constructors ────────────────────────────
#
# Ergonomic wrappers over :func:`primitive` so callers can build the
# fundamental distance-function object library without spelling ``kind``
# strings by hand. Parameter names match the GLSL library in
# ``templates/sdf/shaders/primitives.glsl`` and the emitters in
# ``templates/sdf/objects/primitives.js``.


def sphere(
    radius: float,
    *,
    id: str | None = None,
    position: Position = None,
) -> SdfNode:
    """Filled sphere of ``radius`` centred at ``position``."""
    return primitive("sphere", {"radius": float(radius)}, id=id, position=position)


def ellipsoid(
    radii: tuple[float, float, float],
    *,
    id: str | None = None,
    position: Position = None,
    rotation: Rotation = None,
) -> SdfNode:
    """Ellipsoid with per-axis half radii ``radii`` = (x, y, z)."""
    return primitive(
        "ellipsoid",
        {"radii": [float(v) for v in radii]},
        id=id,
        position=position,
        rotation=rotation,
    )


def box(
    half_extents: tuple[float, float, float],
    *,
    id: str | None = None,
    position: Position = None,
    rotation: Rotation = None,
) -> SdfNode:
    """Axis-aligned box with half extents ``half_extents`` = (x, y, z)."""
    return primitive(
        "box",
        {"halfExtents": [float(v) for v in half_extents]},
        id=id,
        position=position,
        rotation=rotation,
    )


def round_box(
    half_extents: tuple[float, float, float],
    radius: float,
    *,
    id: str | None = None,
    position: Position = None,
    rotation: Rotation = None,
) -> SdfNode:
    """Rounded box with half extents ``half_extents`` and corner rounding ``radius``."""
    return primitive(
        "roundBox",
        {"halfExtents": [float(v) for v in half_extents], "radius": float(radius)},
        id=id,
        position=position,
        rotation=rotation,
    )


def cylinder(
    radius: float,
    *,
    id: str | None = None,
    position: Position = None,
    rotation: Rotation = None,
) -> SdfNode:
    """Infinite cylinder along +Y of ``radius`` (clip with an explicit ``bound``)."""
    return primitive(
        "cylinder",
        {"radius": float(radius)},
        id=id,
        position=position,
        rotation=rotation,
    )


def capped_cylinder(
    half_height: float,
    radius: float,
    *,
    id: str | None = None,
    position: Position = None,
    rotation: Rotation = None,
) -> SdfNode:
    """Capped cylinder along +Y with half height ``half_height`` and ``radius``."""
    return primitive(
        "cappedCylinder",
        {"halfHeight": float(half_height), "radius": float(radius)},
        id=id,
        position=position,
        rotation=rotation,
    )


def cone(
    angle: float,
    *,
    id: str | None = None,
    position: Position = None,
    rotation: Rotation = None,
) -> SdfNode:
    """Infinite cone around +Y with opening half-angle ``angle`` (radians)."""
    return primitive(
        "cone",
        {"angle": float(angle)},
        id=id,
        position=position,
        rotation=rotation,
    )


def capped_cone(
    half_height: float,
    radius1: float,
    radius2: float,
    *,
    id: str | None = None,
    position: Position = None,
    rotation: Rotation = None,
) -> SdfNode:
    """Capped cone along +Y: apex radius ``radius1``, base radius ``radius2``."""
    return primitive(
        "cappedCone",
        {
            "halfHeight": float(half_height),
            "radius1": float(radius1),
            "radius2": float(radius2),
        },
        id=id,
        position=position,
        rotation=rotation,
    )


def torus(
    main_radius: float,
    tube_radius: float,
    *,
    id: str | None = None,
    position: Position = None,
    rotation: Rotation = None,
) -> SdfNode:
    """Torus in the XZ plane with major radius ``main_radius`` and tube ``tube_radius``."""
    return primitive(
        "torus",
        {"mainRadius": float(main_radius), "tubeRadius": float(tube_radius)},
        id=id,
        position=position,
        rotation=rotation,
    )


def partial_disk(
    radius: float,
    angle: float = 2.0 * math.pi,
    *,
    half_height: float = 0.01,
    id: str | None = None,
    position: Position = None,
    rotation: Rotation = None,
) -> SdfNode:
    """Capped sector (partial disk) in the XZ plane, symmetric about +Z.

    ``radius`` is the disk radius, ``angle`` the total sweep in radians
    (``0 < angle < 2π``; use :func:`capped_cylinder` for a full disk), and
    ``half_height`` the slab half-thickness along +Y.
    """
    return primitive(
        "partialDisk",
        {
            "radius": float(radius),
            "halfHeight": float(half_height),
            "angle": float(angle),
        },
        id=id,
        position=position,
        rotation=rotation,
    )


def regular_polygon(
    radius: float,
    sides: int,
    *,
    half_height: float = 0.01,
    id: str | None = None,
    position: Position = None,
    rotation: Rotation = None,
) -> SdfNode:
    """Regular polygon slab in the XZ plane with a vertex on +Z.

    ``radius`` is the circumradius, ``sides`` the number of sides (``>= 3``),
    and ``half_height`` the slab half-thickness along +Y.
    """
    return primitive(
        "regularPolygon",
        {
            "radius": float(radius),
            "halfHeight": float(half_height),
            "sides": int(sides),
        },
        id=id,
        position=position,
        rotation=rotation,
    )


def plane(
    normal: tuple[float, float, float],
    offset: float = 0.0,
    *,
    id: str | None = None,
    position: Position = None,
    rotation: Rotation = None,
) -> SdfNode:
    """Infinite plane with unit ``normal`` and signed ``offset`` (needs a bound).

    The plane satisfies ``dot(p, normal) = -offset``; combine with
    :func:`bound_box` for a finite drawable region.
    """
    return primitive(
        "plane",
        {"normal": [float(v) for v in normal], "offset": float(offset)},
        id=id,
        position=position,
        rotation=rotation,
    )


def capsule(
    point_a: Any,
    point_b: Any,
    radius_a: float = 0.0,
    radius_b: float = 0.0,
    *,
    id: str | None = None,
) -> SdfNode:
    """Two-point capsule between ``point_a``/``point_b`` with per-end radii."""
    midpoint, rotation, half = _two_point_frame(point_a, point_b)
    return primitive(
        "capsule",
        {
            "a": [0.0, -half, 0.0],
            "b": [0.0, half, 0.0],
            "radiusA": float(radius_a),
            "radiusB": float(radius_b),
        },
        id=id,
        position=midpoint,
        rotation=rotation,
    )


def segment(point_a: Any, point_b: Any, *, id: str | None = None) -> SdfNode:
    """Round-edged line segment between ``point_a`` and ``point_b``."""
    midpoint, rotation, half = _two_point_frame(point_a, point_b)
    return primitive(
        "segment",
        {"a": [0.0, -half, 0.0], "b": [0.0, half, 0.0]},
        id=id,
        position=midpoint,
        rotation=rotation,
    )


# ── Internal helpers ────────────────────────────────────────


def _two_point_frame(
    point_a: Any,
    point_b: Any,
) -> tuple[
    tuple[float, float, float],
    tuple[tuple[float, float, float], float] | None,
    float,
]:
    """Compute the world transform + local half-length for a two-point shape.

    Returns ``(midpoint, rotation, half_length)`` such that the two endpoints
    land on the local +Y axis at ``(0, ±half_length, 0)``.
    """
    a = _as_vec3(point_a)
    b = _as_vec3(point_b)
    direction = _normalize((b[0] - a[0], b[1] - a[1], b[2] - a[2]))
    if direction == (0.0, 0.0, 0.0):
        direction = (0.0, 0.0, 1.0)
    half = _dist(a, b) / 2.0
    midpoint = (
        a[0] + direction[0] * half,
        a[1] + direction[1] * half,
        a[2] + direction[2] * half,
    )
    rotation = _rotation_align((0.0, 1.0, 0.0), direction)
    return midpoint, rotation, half


def _as_rotation(value: Any) -> tuple[tuple[float, float, float], float]:
    """Coerce a rotation to an ``(axis, angle_radians)`` tuple.

    Accepts a :class:`~pytanga.geometry.Rotor` (``angle`` + ``axis``) or an
    ``(axis, angle)`` pair (the axis may be a 3-sequence or a Direction/Point).
    A :class:`~pytanga.geometry.GeneralRotor` with a displaced rotation centre
    cannot be represented by a single axis-angle transform and raises.
    """
    angle = getattr(value, "angle", None)
    axis = getattr(value, "axis", None)
    if angle is not None and axis is not None:
        # Rotor-like (Rotor / GeneralRotor).
        origin = getattr(value, "origin", None)
        if origin is not None:
            ox, oy, oz = _as_vec3(origin)
            if abs(ox) > 1e-12 or abs(oy) > 1e-12 or abs(oz) > 1e-12:
                raise TypeError(
                    "A rotation with a displaced origin (GeneralRotor) cannot be "
                    "used as an SDF transform; pass a Rotor or an (axis, angle) pair"
                )
        return (_as_vec3(axis), float(angle))
    axis, angle = value
    return (_as_vec3(axis), float(angle))


def _normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = v
    length = math.sqrt(x * x + y * y + z * z)
    if length < 1e-12:
        return (0.0, 0.0, 0.0)
    return (x / length, y / length, z / length)


def _dist(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2)


def _rotation_align(
    from_axis: tuple[float, float, float],
    to_dir: tuple[float, float, float],
) -> tuple[tuple[float, float, float], float] | None:
    """Axis-angle rotation aligning ``from_axis`` onto unit ``to_dir``."""
    ax, ay, az = from_axis
    dx, dy, dz = to_dir
    dot = max(-1.0, min(1.0, ax * dx + ay * dy + az * dz))
    if dot > 1.0 - 1e-9:
        return None  # already aligned
    if dot < -1.0 + 1e-9:
        perp = (1.0, 0.0, 0.0) if abs(ax) < 0.9 else (0.0, 1.0, 0.0)
        return (perp, math.pi)
    axis = (ay * dz - az * dy, az * dx - ax * dz, ax * dy - ay * dx)
    axis = _normalize(axis)
    return (axis, math.acos(dot))


def _basis_rotation(
    y_dir: tuple[float, float, float],
    z_dir: tuple[float, float, float],
) -> tuple[tuple[float, float, float], float] | None:
    """Axis-angle rotation mapping local ``+Y`` → ``y_dir`` and ``+Z`` → ``z_dir``.

    ``y_dir`` and ``z_dir`` are assumed (near-)perpendicular.  Returns ``None``
    for the identity rotation.
    """
    y = _normalize(y_dir)
    z = _normalize(z_dir)
    x = _normalize(
        (y[1] * z[2] - y[2] * z[1], y[2] * z[0] - y[0] * z[2], y[0] * z[1] - y[1] * z[0])
    )
    # Re-orthonormalize z against x, y (right-handed).
    z = (
        x[1] * y[2] - x[2] * y[1],
        x[2] * y[0] - x[0] * y[2],
        x[0] * y[1] - x[1] * y[0],
    )

    # Rotation matrix R has columns x, y, z.
    trace = x[0] + y[1] + z[2]
    cos_angle = max(-1.0, min(1.0, (trace - 1.0) / 2.0))
    angle = math.acos(cos_angle)
    if angle < 1e-9:
        return None

    sin_angle = math.sin(angle)
    if sin_angle < 1e-9:
        # 180° rotation: recover the axis from the largest diagonal entry.
        diag = (x[0], y[1], z[2])
        i = max(range(3), key=lambda k: diag[k])
        axis = [0.0, 0.0, 0.0]
        axis[i] = math.sqrt(max((diag[i] + 1.0) / 2.0, 0.0))
        if i == 0:
            axis[1] = (y[0] + x[1]) / (4.0 * axis[0]) if axis[0] > 1e-12 else 0.0
            axis[2] = (z[0] + x[2]) / (4.0 * axis[0]) if axis[0] > 1e-12 else 0.0
        elif i == 1:
            axis[0] = (y[0] + x[1]) / (4.0 * axis[1]) if axis[1] > 1e-12 else 0.0
            axis[2] = (z[1] + y[2]) / (4.0 * axis[1]) if axis[1] > 1e-12 else 0.0
        else:
            axis[0] = (z[0] + x[2]) / (4.0 * axis[2]) if axis[2] > 1e-12 else 0.0
            axis[1] = (z[1] + y[2]) / (4.0 * axis[2]) if axis[2] > 1e-12 else 0.0
        return (_normalize(tuple(axis)), math.pi)

    axis = _normalize(
        (
            (y[2] - z[1]) / (2.0 * sin_angle),
            (z[0] - x[2]) / (2.0 * sin_angle),
            (x[1] - y[0]) / (2.0 * sin_angle),
        )
    )
    return (axis, angle)


def _rotate_about(
    v: tuple[float, float, float],
    axis: tuple[float, float, float],
    angle: float,
) -> tuple[float, float, float]:
    """Rotate vector *v* by *angle* radians about *axis* (right-hand rule)."""
    ax, ay, az = _normalize(axis)
    vx, vy, vz = v
    c = math.cos(angle)
    s = math.sin(angle)
    cx = ay * vz - az * vy
    cy = az * vx - ax * vz
    cz = ax * vy - ay * vx
    dot = ax * vx + ay * vy + az * vz
    return (
        vx * c + cx * s + ax * dot * (1.0 - c),
        vy * c + cy * s + ay * dot * (1.0 - c),
        vz * c + cz * s + az * dot * (1.0 - c),
    )