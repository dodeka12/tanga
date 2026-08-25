# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Per-entity label anchor computation.

Each entity type has a function that returns the 3D point (relative to the
entity's mesh origin) where its label attaches, driven by ``LabelStyle.along``
(a scalar or 2-/3-tuple of fractions parameterizing the entity's extent).

The vector helpers are re-implemented here (identical to ``_label_frame.py``)
to avoid a circular import — ``_label_frame.py`` imports
:func:`compute_label_anchor`.
"""

from __future__ import annotations

import math
from typing import Any, Callable

from pytanga.geometry.entities import (
    Circle,
    Direction,
    Line,
    Plane,
    PointPair,
    Sphere,
)
from pytanga.geometry.operators import Inversion, ReflectionLine, ReflectionPlane

EntityLike = Any


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


def _perpendicular(direction: tuple[float, float, float]) -> tuple[float, float, float]:
    dx, dy, dz = direction
    dots = (abs(dx), abs(dy), abs(dz))
    if dots[0] <= dots[1] and dots[0] <= dots[2]:
        ref = (1.0, 0.0, 0.0)
    elif dots[1] <= dots[2]:
        ref = (0.0, 1.0, 0.0)
    else:
        ref = (0.0, 0.0, 1.0)
    return _normalize(_cross(direction, ref))


# ── `along` normalization ───────────────────────────────────


def _normalize_along(along: Any) -> tuple[float, float, float] | None:
    """Normalize ``along`` to a ``(u, v, w)`` 3-vector, or ``None`` if unset."""
    if along is None:
        return None
    if isinstance(along, (int, float)):
        return (float(along), 0.0, 0.0)
    seq = tuple(along)
    if len(seq) == 2:
        return (float(seq[0]), float(seq[1]), 0.0)
    if len(seq) == 3:
        return (float(seq[0]), float(seq[1]), float(seq[2]))
    raise ValueError(f"along must be a scalar or a 2-/3-tuple, got {along!r}")


# ── Per-entity anchor functions (relative to mesh origin) ────


def _anchor_line(line: Line, uvw, line_length) -> tuple[float, float, float]:
    u = uvw[0] if uvw is not None else 0.5
    if line_length is None:
        if line.length is not None and line.length > 0:
            line_length = float(line.length)
        else:
            line_length = 20.0
    d = _normalize((line.direction.x, line.direction.y, line.direction.z))
    return (
        line.origin.x + d[0] * u * line_length,
        line.origin.y + d[1] * u * line_length,
        line.origin.z + d[2] * u * line_length,
    )


def _anchor_reflection_line(rl, uvw, line_length) -> tuple[float, float, float]:
    return _anchor_line(rl.line, uvw, line_length)


def _anchor_direction(direction, uvw, line_length) -> tuple[float, float, float]:
    u = uvw[0] if uvw is not None else 0.0
    d = _normalize((direction.x, direction.y, direction.z))
    return (d[0] * u * 2.0, d[1] * u * 2.0, d[2] * u * 2.0)


def _anchor_point_pair(pp, uvw, line_length) -> tuple[float, float, float]:
    u = uvw[0] if uvw is not None else 0.5
    pa, pb = pp.point_a, pp.point_b
    dx, dy, dz = pb.x - pa.x, pb.y - pa.y, pb.z - pa.z
    return ((u - 0.5) * dx, (u - 0.5) * dy, (u - 0.5) * dz)


def _plane_axes(
    plane: Plane,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    n = _normalize((plane.normal.x, plane.normal.y, plane.normal.z))
    u_axis = _perpendicular(n)
    v_axis = _normalize(_cross(n, u_axis))
    return u_axis, v_axis


def _anchor_plane(plane: Plane, uvw, line_length) -> tuple[float, float, float]:
    u = uvw[0] if uvw is not None else 0.5
    v = uvw[1] if uvw is not None else 0.5
    # The renderer draws a square of half-side `extent` centred on `point`,
    # so fractions map across 2 * extent in each in-plane direction.
    extent = plane.extent if plane.extent is not None else 10.0
    u_axis, v_axis = _plane_axes(plane)
    su = (u_axis[0] * 2 * extent, u_axis[1] * 2 * extent, u_axis[2] * 2 * extent)
    sv = (v_axis[0] * 2 * extent, v_axis[1] * 2 * extent, v_axis[2] * 2 * extent)
    return (
        (u - 0.5) * su[0] + (v - 0.5) * sv[0],
        (u - 0.5) * su[1] + (v - 0.5) * sv[1],
        (u - 0.5) * su[2] + (v - 0.5) * sv[2],
    )


def _anchor_reflection_plane(rp, uvw, line_length) -> tuple[float, float, float]:
    return _anchor_plane(rp.plane, uvw, line_length)


def _circle_normal(circle: Circle) -> tuple[float, float, float]:
    if circle.normal is not None:
        return (circle.normal.x, circle.normal.y, circle.normal.z)
    return (0.0, 0.0, 1.0)


def _anchor_circle(circle: Circle, uvw, line_length) -> tuple[float, float, float]:
    radius_frac = uvw[0] if uvw is not None else 0.0
    angle_frac = uvw[1] if uvw is not None else 0.0
    n = _normalize(_circle_normal(circle))
    x_axis = _perpendicular(n)
    y_axis = _normalize(_cross(n, x_axis))
    r = radius_frac * circle.radius
    angle = angle_frac * math.pi
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return (
        r * cos_a * x_axis[0] + r * sin_a * y_axis[0],
        r * cos_a * x_axis[1] + r * sin_a * y_axis[1],
        r * cos_a * x_axis[2] + r * sin_a * y_axis[2],
    )


def _anchor_sphere(sphere: Sphere, uvw, line_length) -> tuple[float, float, float]:
    radius_frac = uvw[0] if uvw is not None else 0.0
    azimuth_frac = uvw[1] if uvw is not None else 0.0
    polar_frac = uvw[2] if uvw is not None else 0.0
    r = radius_frac * sphere.radius
    theta = azimuth_frac * math.pi  # azimuth (around the polar axis)
    phi = polar_frac * math.pi  # polar (from the +z axis)
    sin_phi = math.sin(phi)
    cos_phi = math.cos(phi)
    sin_theta = math.sin(theta)
    cos_theta = math.cos(theta)
    return (
        r * sin_phi * cos_theta,
        r * sin_phi * sin_theta,
        r * cos_phi,
    )


# ── Registry + dispatch ─────────────────────────────────────

_ANCHOR_FUNCS: dict[type, Callable] = {
    Line: _anchor_line,
    ReflectionLine: _anchor_reflection_line,
    Direction: _anchor_direction,
    PointPair: _anchor_point_pair,
    Plane: _anchor_plane,
    ReflectionPlane: _anchor_reflection_plane,
    Circle: _anchor_circle,
    Sphere: _anchor_sphere,
    Inversion: _anchor_sphere,
}


def compute_label_anchor(
    entity: EntityLike,
    *,
    along: Any = None,
    line_length: float | None = None,
) -> tuple[float, float, float]:
    """Return the label anchor relative to the entity's mesh origin.

    ``along`` is the raw ``LabelStyle.along`` (scalar / 2-tuple / 3-tuple /
    ``None``); ``line_length`` is the resolved line length (used only by
    Line/ReflectionLine).
    """
    uvw = _normalize_along(along)
    for cls, fn in _ANCHOR_FUNCS.items():
        if isinstance(entity, cls):
            return fn(entity, uvw, line_length)
    return (0.0, 0.0, 0.0)
