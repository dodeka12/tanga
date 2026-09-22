# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Entity → ``(Transform, shape)`` placement decomposition.

Maps an entity's placement (``center``/``origin``/``vertex``/``point`` +
``normal``/``axis``/``direction`` (+ a second axis where one is needed) or a
``rotation``) into a :class:`pytanga.geometry.Transform` and its remaining
parameters into a canonical shape dict.  The scene-graph node uses this to
initialize/refresh its per-entity transform and to diff shape vs placement in
``set_entity``.

Canonical frames (three.js defaults): linear primitives along **+Y** (origin at
the node position), planar primitives in **XY** (normal **+Z**, centred at the
node position), volumes centred at the node position.

Out-of-scope kinds (``PointPath``/``Curve``/``PointSet``, point/plane pairs,
operators, axes/grid, SDF/ray/image) return ``(Transform(), {})``.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from pytanga.geometry.entities import (
    Arc,
    Box,
    Circle,
    Cone,
    Cylinder,
    Direction,
    Disk,
    Ellipse,
    Ellipsoid,
    Frustum,
    HPoint,
    Hyperbola,
    Line,
    Parabola,
    PartialDisk,
    Plane,
    Point,
    Rectangle2D,
    RegularPolygon,
    Sphere,
)
from pytanga.geometry.transform import Transform, _as_quaternion
from pytanga.geometry.transforms import matrix_to_quat, quat_from_vectors

#: Default epsilon for shape-vs-placement diffing in ``set_entity``.
DEFAULT_DIFF_EPSILON = 1e-9

_CANONICAL_Y = (0.0, 1.0, 0.0)
_CANONICAL_Z = (0.0, 0.0, 1.0)


def _to_array(v: Any) -> np.ndarray:
    """Return *v* (a Point/Direction or 3-sequence) as a float64 array."""
    if hasattr(v, "x") and hasattr(v, "y") and hasattr(v, "z"):
        return np.array([v.x, v.y, v.z], dtype=np.float64)
    return np.array(v, dtype=np.float64)


def _unit(v: Any) -> np.ndarray:
    """Return *v* normalized; a zero vector is returned unchanged."""
    a = _to_array(v)
    n = float(np.linalg.norm(a))
    if n < 1e-12:
        return a
    return a / n


def _frame_quaternion(
    x_world: Any, z_world: Any
) -> tuple[float, float, float, float]:
    """Rotation mapping canonical +X/+Y/+Z onto an orthonormal world frame.

    ``x_world`` and ``z_world`` are the world axes the canonical +X and +Z map
    to; +Y is derived right-handed (``z × x``).  ``x_world`` is orthogonalized
    against ``z_world``.
    """
    z = _unit(z_world)
    x = _unit(x_world)
    x = x - z * float(np.dot(x, z))
    nx = float(np.linalg.norm(x))
    if nx < 1e-12:
        aux = np.array([1.0, 0.0, 0.0]) if abs(z[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        x = _unit(np.cross(z, aux))
    else:
        x = x / nx
    y = np.cross(z, x)
    return matrix_to_quat(np.column_stack([x, y, z]))


def _frame_from_xy(
    x_world: Any, y_world: Any
) -> tuple[float, float, float, float]:
    """Rotation mapping canonical +X/+Y onto an orthonormal world frame.

    ``x_world`` and ``y_world`` are the world axes the canonical +X and +Y map
    to; +Z is derived right-handed (``x × y``).  ``y_world`` is orthogonalized
    against ``x_world``.
    """
    x = _unit(x_world)
    y = _unit(y_world)
    y = y - x * float(np.dot(x, y))
    ny = float(np.linalg.norm(y))
    if ny < 1e-12:
        aux = np.array([0.0, 1.0, 0.0]) if abs(x[1]) < 0.9 else np.array([0.0, 0.0, 1.0])
        y = _unit(np.cross(aux, x))
    else:
        y = y / ny
    z = np.cross(x, y)
    return matrix_to_quat(np.column_stack([x, y, z]))


def _pos(p: Point) -> tuple[float, float, float]:
    return (float(p.x), float(p.y), float(p.z))


def _dir(d: Direction) -> tuple[float, float, float]:
    return (float(d.x), float(d.y), float(d.z))


def _entity_decompose(entity: Any) -> tuple[Transform, dict[str, Any]]:
    """Decompose *entity* into ``(Transform, shape)``.

    Placement (position + quaternion) goes into the :class:`Transform`; the
    remaining parameters go into the shape dict.  Out-of-scope kinds return
    ``(Transform(), {})``.
    """
    if isinstance(entity, Point):
        return Transform(position=_pos(entity)), {}

    if isinstance(entity, HPoint):
        return Transform(position=_pos(entity.point)), {"weight": float(entity.weight)}

    if isinstance(entity, Direction):
        q = quat_from_vectors(_CANONICAL_Y, _dir(entity))
        return Transform(rotation=q), {}

    if isinstance(entity, Line):
        q = quat_from_vectors(_CANONICAL_Y, _dir(entity.direction))
        return Transform(position=_pos(entity.origin), rotation=q), {
            "length": entity.length,
        }

    if isinstance(entity, Cylinder):
        axis = _unit(entity.axis)
        offset = float(entity.length) * (0.5 - float(entity.align_center))
        center = _to_array(entity.origin) + axis * offset
        q = quat_from_vectors(_CANONICAL_Y, axis)
        position = (float(center[0]), float(center[1]), float(center[2]))
        return Transform(position=position, rotation=q), {
            "length": float(entity.length),
            "radius": float(entity.radius),
        }

    if isinstance(entity, Cone):
        q = quat_from_vectors(_CANONICAL_Y, _dir(entity.axis))
        return Transform(position=_pos(entity.vertex), rotation=q), {
            "halfAngle": float(entity.half_angle),
        }

    if isinstance(entity, Parabola):
        q = quat_from_vectors(_CANONICAL_Y, _dir(entity.direction))
        return Transform(position=_pos(entity.vertex), rotation=q), {
            "p": float(entity.p),
        }

    if isinstance(entity, Hyperbola):
        z = np.cross(_to_array(entity.dir1), _to_array(entity.dir2))
        q = _frame_quaternion(entity.dir1, z)
        return Transform(position=_pos(entity.center), rotation=q), {
            "a": float(entity.a),
            "b": float(entity.b),
        }

    if isinstance(entity, Circle):
        q = quat_from_vectors(_CANONICAL_Z, _dir(entity.normal))
        return Transform(position=_pos(entity.center), rotation=q), {
            "radius": float(entity.radius),
            "isImaginary": bool(entity.is_imaginary),
        }

    if isinstance(entity, Sphere):
        return Transform(position=_pos(entity.center)), {
            "radius": float(entity.radius),
            "isImaginary": bool(entity.is_imaginary),
        }

    if isinstance(entity, Arc):
        q = _frame_quaternion(entity.start_direction, entity.axis)
        return Transform(position=_pos(entity.origin), rotation=q), {
            "radius": float(entity.radius),
            "tubeRadius": float(entity.tube_radius),
            "angle": float(entity.angle),
            "showArrow": bool(entity.show_arrow),
            "arrowLength": entity.arrow_length,
            "arrowRadius": entity.arrow_radius,
        }

    if isinstance(entity, Disk):
        q = quat_from_vectors(_CANONICAL_Z, _dir(entity.normal))
        return Transform(position=_pos(entity.center), rotation=q), {
            "radius": float(entity.radius),
        }

    if isinstance(entity, PartialDisk):
        q = _frame_quaternion(entity.start_direction, entity.normal)
        return Transform(position=_pos(entity.center), rotation=q), {
            "radius": float(entity.radius),
            "angle": float(entity.angle),
        }

    if isinstance(entity, Ellipse):
        if entity.dir_u is not None:
            q = _frame_quaternion(entity.dir_u, entity.normal)
        else:
            q = quat_from_vectors(_CANONICAL_Z, _dir(entity.normal))
        return Transform(position=_pos(entity.center), rotation=q), {
            "radiusU": float(entity.radius_u),
            "radiusV": float(entity.radius_v),
        }

    if isinstance(entity, RegularPolygon):
        q = quat_from_vectors(_CANONICAL_Z, _dir(entity.normal))
        return Transform(position=_pos(entity.center), rotation=q), {
            "radius": float(entity.radius),
            "sides": int(entity.sides),
            "angle": float(entity.angle),
        }

    if isinstance(entity, Rectangle2D):
        q = quat_from_vectors(_CANONICAL_Z, _dir(entity.normal))
        return Transform(position=_pos(entity.center), rotation=q), {
            "size": (float(entity.size[0]), float(entity.size[1])),
            "angle": float(entity.angle),
        }

    if isinstance(entity, Plane):
        if entity.span_u is not None and entity.span_v is not None:
            # The span vectors are world-space edge vectors: the parallelogram
            # is baked into the shape (no rotation), positioned at ``point``.
            shape: dict[str, Any] = {
                "spanU": list(_dir(entity.span_u)),
                "spanV": list(_dir(entity.span_v)),
            }
            return Transform(position=_pos(entity.point)), shape
        q = quat_from_vectors(_CANONICAL_Z, _dir(entity.normal))
        return Transform(position=_pos(entity.point), rotation=q), {
            "extent": entity.extent,
        }

    if isinstance(entity, Box):
        t = Transform(position=_pos(entity.center))
        if entity.rotation is not None:
            t.rotation = _as_quaternion(entity.rotation)
        return t, {"size": tuple(float(c) for c in entity.size)}

    if isinstance(entity, Ellipsoid):
        t = Transform(position=_pos(entity.center))
        if entity.rotation is not None:
            t.rotation = _as_quaternion(entity.rotation)
        return t, {"radii": tuple(float(c) for c in entity.radii)}

    if isinstance(entity, Frustum):
        q = _frame_from_xy(entity.horizontal, entity.axis)
        return Transform(position=_pos(entity.origin), rotation=q), {
            "near": float(entity.near),
            "far": float(entity.far),
            "halfWidth": float(entity.far_half_width),
            "halfHeight": float(entity.far_half_height),
        }

    # Out of scope: no placement to extract (rebuild on any change).
    return Transform(), {}


#: Types whose placement ``_entity_decompose`` extracts.
_PLACEMENT_TYPES = (
    Point,
    HPoint,
    Direction,
    Line,
    Cylinder,
    Cone,
    Parabola,
    Hyperbola,
    Circle,
    Sphere,
    Arc,
    Disk,
    PartialDisk,
    Ellipse,
    RegularPolygon,
    Rectangle2D,
    Plane,
    Box,
    Ellipsoid,
    Frustum,
)


def is_placement_entity(entity: Any) -> bool:
    """Return whether *entity* has a placement that ``_entity_decompose`` extracts."""
    return isinstance(entity, _PLACEMENT_TYPES)


def _values_close(a: Any, b: Any, eps: float) -> bool:
    """Return whether *a* and *b* are within *eps* (scalars/arrays/None)."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b or bool(a) == bool(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= eps
    if isinstance(a, (tuple, list, np.ndarray)) and isinstance(
        b, (tuple, list, np.ndarray)
    ):
        return bool(
            np.allclose(np.asarray(a, dtype=float), np.asarray(b, dtype=float), atol=eps)
        )
    return a == b


def transforms_differ(
    a: Transform, b: Transform, eps: float = DEFAULT_DIFF_EPSILON
) -> bool:
    """Return whether two placement transforms differ beyond *eps*."""
    return (
        not _values_close(a.position, b.position, eps)
        or not _values_close(a.rotation, b.rotation, eps)
        or not _values_close(a.scale, b.scale, eps)
    )


def shapes_differ(
    a: dict[str, Any], b: dict[str, Any], eps: float = DEFAULT_DIFF_EPSILON
) -> bool:
    """Return whether two shape dicts differ beyond *eps*."""
    if set(a) != set(b):
        return True
    for key, value in a.items():
        if not _values_close(value, b[key], eps):
            return True
    return False
