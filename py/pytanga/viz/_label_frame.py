# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Local coordinate frame computation for label positioning.

Each entity/operator kind defines a local coordinate system (origin, axes,
scale) so that ``offset_local`` from ``LabelStyle`` is applied in a frame
natural to the entity — e.g. along a line, above a plane, or along the
axis of a point pair.

The computed ``LabelFrame`` can be cached on the entity via its
``SceneObject``, avoiding repeated computation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from pytanga.geometry.entities import (
    Circle,
    Direction,
    HPoint,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
)
from pytanga.geometry.operators import (
    Dilator,
    GeneralDilator,
    GeneralRotor,
    Inversion,
    Motor,
    ReflectionLine,
    ReflectionOrigin,
    ReflectionPlane,
    Rotor,
    Translator,
)

EntityLike = (
    Point
    | Direction
    | HPoint
    | PointPair
    | Line
    | Plane
    | Circle
    | Sphere
    | Space
    | ReflectionLine
    | ReflectionPlane
    | ReflectionOrigin
    | Inversion
    | Rotor
    | Translator
    | Dilator
    | Motor
    | GeneralRotor
    | GeneralDilator
)


@dataclass
class LabelFrame:
    """Local coordinate frame for label positioning.

    The 3D ``offset_local`` from ``LabelStyle`` is applied in this frame.
    The resulting world-offset from the entity origin is:
    ``(ox * x_axis + oy * y_axis + oz * z_axis) * scale``.
    """

    x_axis: tuple[float, float, float]
    y_axis: tuple[float, float, float]
    z_axis: tuple[float, float, float]
    scale: float


# ── Vector helpers ──────────────────────────────────────────


def _normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = v
    length = math.sqrt(x * x + y * y + z * z)
    if length < 1e-15:
        return (0.0, 0.0, 0.0)
    return (x / length, y / length, z / length)


def _cross(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _length(v: tuple[float, float, float]) -> float:
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def _perpendicular(
    direction: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Return a unit vector perpendicular to *direction*.

    Chooses the world axis (X, Y, or Z) that is most perpendicular to
    *direction*, then returns the normalized cross product.
    """
    dx, dy, dz = direction
    dots = (abs(dx), abs(dy), abs(dz))
    if dots[0] <= dots[1] and dots[0] <= dots[2]:
        ref = (1.0, 0.0, 0.0)
    elif dots[1] <= dots[2]:
        ref = (0.0, 1.0, 0.0)
    else:
        ref = (0.0, 0.0, 1.0)
    y = _cross(direction, ref)
    return _normalize(y)


# ── Label frame cache key ───────────────────────────────────

_LABEL_FRAME_KEY = "__label_frame__"


def get_cached_label_frame(entity: EntityLike) -> LabelFrame | None:
    """Return the cached label frame from an entity's ``__dict__``, if present."""
    return getattr(entity, _LABEL_FRAME_KEY, None)


def set_cached_label_frame(entity: EntityLike, frame: LabelFrame) -> None:
    """Store the label frame in the entity's ``__dict__`` for later reuse."""
    object.__setattr__(entity, _LABEL_FRAME_KEY, frame)


# ── Public API ──────────────────────────────────────────────


def get_label_frame(entity: EntityLike) -> LabelFrame:
    """Return the local coordinate frame for label positioning on *entity*.

    The frame is cached on the entity instance after first computation.
    """
    cached = get_cached_label_frame(entity)
    if cached is not None:
        return cached

    frame = _compute_label_frame(entity)
    set_cached_label_frame(entity, frame)
    return frame


def _compute_label_frame(entity: EntityLike) -> LabelFrame:
    """Compute (uncached) the local frame."""

    # ── Entities with no intrinsic orientation ──
    if isinstance(entity, (Point, HPoint)):
        return LabelFrame((1, 0, 0), (0, 1, 0), (0, 0, 1), 1.0)

    if isinstance(entity, Space):
        return LabelFrame((1, 0, 0), (0, 1, 0), (0, 0, 1), entity.scale)

    if isinstance(entity, (Sphere, Inversion)):
        r = getattr(entity, "radius", 1.0)
        return LabelFrame((1, 0, 0), (0, 1, 0), (0, 0, 1), r)

    # ── Direction ──
    if isinstance(entity, Direction):
        d = (entity.x, entity.y, entity.z)
        x = _normalize(d)
        y = _perpendicular(x)
        z = _cross(x, y)
        return LabelFrame(x, y, z, 2.0)

    # ── Translator ──
    if isinstance(entity, Translator):
        d = (entity.vector.x, entity.vector.y, entity.vector.z)
        ln = entity.length if hasattr(entity, "length") else 3.0
        x = _normalize(d)
        y = _perpendicular(x)
        z = _cross(x, y)
        return LabelFrame(x, y, z, ln)

    # ── Line ──
    if isinstance(entity, Line):
        d = (entity.direction.x, entity.direction.y, entity.direction.z)
        x = _normalize(d)
        y = _perpendicular(x)
        z = _cross(x, y)
        return LabelFrame(x, y, z, 20.0)

    # ── ReflectionLine ──
    if isinstance(entity, ReflectionLine):
        d = (entity.direction.x, entity.direction.y, entity.direction.z)
        x = _normalize(d)
        y = _perpendicular(x)
        z = _cross(x, y)
        return LabelFrame(x, y, z, 5.0)

    # ── PointPair ──
    if isinstance(entity, PointPair):
        pa, pb = entity.point_a, entity.point_b
        dx = pb.x - pa.x
        dy = pb.y - pa.y
        dz = pb.z - pa.z
        x = _normalize((dx, dy, dz))
        dist = _length((dx, dy, dz))
        y = _perpendicular(x)
        z = _cross(x, y)
        return LabelFrame(x, y, z, dist / 2)

    # ── Plane ──
    if isinstance(entity, Plane):
        n = (entity.normal.x, entity.normal.y, entity.normal.z)
        z = _normalize(n)
        x = _perpendicular(z)
        y = _cross(z, x)
        return LabelFrame(x, y, z, 10.0)

    # ── ReflectionPlane ──
    if isinstance(entity, ReflectionPlane):
        n = (entity.normal.x, entity.normal.y, entity.normal.z)
        z = _normalize(n)
        x = _perpendicular(z)
        y = _cross(z, x)
        return LabelFrame(x, y, z, 5.0)

    # ── Circle ──
    if isinstance(entity, Circle):
        n = (entity.normal.x, entity.normal.y, entity.normal.z)
        z = _normalize(n)
        x = _perpendicular(z)
        y = _cross(z, x)
        return LabelFrame(x, y, z, entity.radius)

    # ── Rotor ──
    if isinstance(entity, Rotor):
        ax = entity.axis
        z = _normalize((ax.x, ax.y, ax.z))
        x = _perpendicular(z)
        y = _cross(z, x)
        return LabelFrame(x, y, z, 1.5)

    # ── Motor ──
    if isinstance(entity, Motor):
        ax = entity.rotor.axis
        z = _normalize((ax.x, ax.y, ax.z))
        x = _perpendicular(z)
        y = _cross(z, x)
        return LabelFrame(x, y, z, 1.5)

    # ── GeneralRotor ──
    if isinstance(entity, GeneralRotor):
        ax = entity.rotor.axis
        z = _normalize((ax.x, ax.y, ax.z))
        x = _perpendicular(z)
        y = _cross(z, x)
        return LabelFrame(x, y, z, 1.5)

    # ── Dilator / GeneralDilator ──
    if isinstance(entity, (Dilator, GeneralDilator)):
        return LabelFrame((1, 0, 0), (0, 1, 0), (0, 0, 1), 3.0)

    if isinstance(entity, ReflectionOrigin):
        return LabelFrame((1, 0, 0), (0, 1, 0), (0, 0, 1), 1.0)

    # Fallback
    return LabelFrame((1, 0, 0), (0, 1, 0), (0, 0, 1), 1.0)


def compute_label_position(
    entity: EntityLike,
    offset_local: tuple[float, float, float] | None = None,
) -> tuple[float, float, float]:
    """Return the label anchor position relative to the entity's local origin.

    This is what gets serialized as ``position`` for parent-attached labels.
    The CSS2DObject is a child of the entity mesh, so its position is
    relative to the parent's origin.

    Args:
        entity: The geometry entity the label is attached to.
        offset_local: ``(x, y, z)`` in the entity's local frame, scaled
            by the frame's ``scale``.  ``None`` or ``(0, 0, 0)`` means
            the label sits exactly at the entity's local origin.
    """
    frame = get_label_frame(entity)
    ox, oy, oz = offset_local or (0.0, 0.0, 0.0)
    return (
        (ox * frame.x_axis[0] + oy * frame.y_axis[0] + oz * frame.z_axis[0])
        * frame.scale,
        (ox * frame.x_axis[1] + oy * frame.y_axis[1] + oz * frame.z_axis[1])
        * frame.scale,
        (ox * frame.x_axis[2] + oy * frame.y_axis[2] + oz * frame.z_axis[2])
        * frame.scale,
    )
