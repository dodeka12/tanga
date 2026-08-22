# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Entity → SDF primitive-tree serialization (the analytic path).

Maps the initially-supported geometric entities to compositions of the Phase 1
SDF primitive library. The result is a nested, JSON-ready tree consumed by
``templates/sdf/scene-builder.js``, which dispatches on the node ``kind`` to
emit the GLSL expression (mirroring ``renderers/factory.js``).

Supported kinds (others raise :class:`TypeError`):
    Point, Line, Plane, Sphere, Circle, PointPair

Style scope is minimal per kind — ``color``/``opacity`` on all kinds, ``size``
for ``Point`` (sphere radius), and ``thickness`` for ``Line``/``Circle`` (and
the ``PointPair`` connecting segment) as the cylinder/tube radius. Other flags
(``wireframe``, …) are ignored for now.

Reuses :func:`pytanga.viz.serializer._apply_defaults` so color/opacity and the
per-kind size/thickness parameters resolve with exactly the same priority as the
standard viewer (per-entity props > style > canonical > builtin).
"""

from __future__ import annotations

import math
from typing import Any

from pytanga.geometry.entities import (
    Circle,
    Entity,
    Line,
    Plane,
    Point,
    PointPair,
    Sphere,
)

from .primitives import combine, primitive

# ── Public API ─────────────────────────────────────────────


def serialize_entity(
    entity: Entity | Any,
    entity_id: str,
    properties: dict[str, Any] | None = None,
    *,
    styles_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Serialize a supported geometry entity to an SDF scene object.

    Raises :class:`TypeError` for unsupported kinds (operators, ``Direction``,
    ``Space``, …).

    Returns a dict carrying the id, the SDF ``tree``, the resolved ``color`` /
    ``opacity``, and the per-object ``combine``/``polarity`` mode.
    """
    props = dict(properties) if properties else {}
    tree, resolved = _dispatch_tree(entity, props, styles_map)

    result: dict[str, Any] = {
        "id": entity_id,
        "layer": "scene",
        "kind": "sdf",
        "sdfKind": type(entity).__name__,
        "tree": tree.to_dict(),
    }

    # color / opacity (resolved alongside the per-kind params).
    color = resolved.get("color")
    if color is not None:
        result["color"] = color
    opacity = resolved.get("opacity")
    if opacity is not None:
        result["opacity"] = opacity

    # per-object combine / polarity. Both representations are forwarded; the
    # compositor (Phase 5) folds a negative/signed mode with max + negation.
    combine_mode = _normalize_combine(props)
    result["combine"] = combine_mode["combine"]
    result["polarity"] = combine_mode["polarity"]

    return result


def _normalize_combine(props: dict[str, Any]) -> dict[str, str]:
    """Resolve the per-object ``combine`` and ``polarity`` (default union/+).

    Accepts ``combine`` (``union``/``intersection``/``subtract``) and/or
    ``polarity`` (``positive``/``negative``). When only ``polarity`` is set,
    ``negative`` maps to ``combine="subtract"``; when only ``combine`` is set,
    ``subtract`` maps to ``polarity="negative"``. Unknown values fall back to
    the defaults.
    """
    combine_value = props.get("combine")
    polarity_value = props.get("polarity")

    valid_combine = {"union", "intersection", "subtract"}
    valid_polarity = {"positive", "negative"}

    combine = combine_value if combine_value in valid_combine else "union"
    polarity = polarity_value if polarity_value in valid_polarity else "positive"

    if combine_value is None and polarity_value == "negative":
        combine = "subtract"
    if polarity_value is None and combine_value == "subtract":
        polarity = "negative"

    return {"combine": combine, "polarity": polarity}


# ── Tree dispatch ──────────────────────────────────────────


def _dispatch_tree(
    entity: Entity,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    if isinstance(entity, Point):
        return _point_tree(entity, props, styles_map)
    if isinstance(entity, Line):
        return _line_tree(entity, props, styles_map, infinite=entity.length is None)
    if isinstance(entity, Circle):
        return _circle_tree(entity, props, styles_map)
    if isinstance(entity, Sphere):
        return _sphere_tree(entity, props, styles_map)
    if isinstance(entity, Plane):
        return _plane_tree(entity, props, styles_map)
    if isinstance(entity, PointPair):
        return _point_pair_tree(entity, props, styles_map)
    raise TypeError(
        f"SDF viewer does not support {type(entity).__name__!r}; supported "
        f"kinds are Point, Line, Plane, Sphere, Circle, PointPair"
    )


# ── Style resolution ───────────────────────────────────────


def _resolve(props: dict[str, Any], kind: str, builtin: dict[str, Any], styles_map: dict[str, Any] | None) -> dict[str, Any]:
    from pytanga.viz.serializer import _apply_defaults

    return _apply_defaults(dict(props), kind, builtin, styles_map=styles_map)


# ── Transform helpers ──────────────────────────────────────


def _rotation_align(
    from_axis: tuple[float, float, float],
    to_dir: tuple[float, float, float],
) -> tuple[tuple[float, float, float], float] | None:
    """Axis-angle rotation aligning ``from_axis`` onto unit ``to_dir``."""
    ax, ay, az = from_axis
    dx, dy, dz = to_dir
    dot = ax * dx + ay * dy + az * dz
    # Clamp for floating point.
    dot = max(-1.0, min(1.0, dot))
    if dot > 1.0 - 1e-9:
        return None  # already aligned
    if dot < -1.0 + 1e-9:
        # Antiparallel: pick any perpendicular axis.
        perp = (1.0, 0.0, 0.0) if abs(ax) < 0.9 else (0.0, 1.0, 0.0)
        return (perp, math.pi)
    axis = (
        ay * dz - az * dy,
        az * dx - ax * dz,
        ax * dy - ay * dx,
    )
    axis = _normalize(axis)
    return (axis, math.acos(dot))


def _normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = v
    length = math.sqrt(x * x + y * y + z * z)
    if length < 1e-12:
        return (0.0, 0.0, 0.0)
    return (x / length, y / length, z / length)


_Y = (0.0, 1.0, 0.0)
_Z = (0.0, 0.0, 1.0)


# ── Per-kind tree builders ─────────────────────────────────


def _point_tree(
    ent: Point,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Point", {"size": 0.08}, styles_map)
    size = float(resolved.get("size", 0.08))
    tree = primitive("sphere", {"radius": size}, position=(ent.x, ent.y, ent.z))
    return tree, resolved


def _sphere_tree(
    ent: Sphere,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Sphere", {}, styles_map)
    tree = primitive(
        "sphere",
        {"radius": ent.radius},
        position=(ent.center.x, ent.center.y, ent.center.z),
    )
    return tree, resolved


def _line_tree(
    ent: Line,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
    *,
    infinite: bool,
) -> tuple[Any, dict[str, Any]]:
    from pytanga.viz.serializer import resolve_line_length

    resolved = _resolve(props, "Line", {"thickness": 1.0}, styles_map)
    thickness = float(resolved.get("thickness", 1.0))

    length = resolve_line_length(ent, styles_map=styles_map, props=props)
    direction = _normalize((ent.direction.x, ent.direction.y, ent.direction.z))
    if direction == (0.0, 0.0, 0.0):
        direction = _Z
    half_length = length / 2.0

    midpoint = (
        ent.origin.x + direction[0] * half_length,
        ent.origin.y + direction[1] * half_length,
        ent.origin.z + direction[2] * half_length,
    )
    rotation = _rotation_align(_Y, direction)

    cylinder = primitive(
        "cappedCylinder",
        {"halfHeight": half_length, "radius": thickness},
        position=midpoint,
        rotation=rotation,
    )

    if not infinite:
        return cylinder, resolved

    # Infinite line: add an explicit bound region (a finite clip box).
    bound = primitive(
        "box",
        {
            "halfExtents": [
                half_length,
                half_length,
                half_length,
            ]
        },
        position=midpoint,
        rotation=rotation,
    )
    return combine("intersect", cylinder, bound), resolved


def _circle_tree(
    ent: Circle,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    # The existing style key is `tube_radius`; the SDF plan calls it
    # `thickness`. Resolve via the standard key for consistency, so a
    # `CircleStyle(tube_radius=…)` keeps working.
    resolved = _resolve(props, "Circle", {"tube_radius": 0.03}, styles_map)
    thickness = float(
        props.get("thickness", resolved.get("tube_radius", 0.03))
    )
    normal = _normalize((ent.normal.x, ent.normal.y, ent.normal.z))
    if normal == (0.0, 0.0, 0.0):
        normal = _Z
    rotation = _rotation_align(_Y, normal)
    tree = primitive(
        "torus",
        {"mainRadius": ent.radius, "tubeRadius": thickness},
        position=(ent.center.x, ent.center.y, ent.center.z),
        rotation=rotation,
    )
    return tree, resolved


def _plane_tree(
    ent: Plane,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    # Honor the entity's own extent (mirrors the standard serializer), so a
    # `Plane(..., extent=5)` wins over the canonical `PlaneStyle.extent`.
    local_props = dict(props)
    if ent.extent is not None:
        local_props["extent"] = ent.extent

    resolved = _resolve(local_props, "Plane", {"extent": 10.0}, styles_map)
    extent = float(resolved.get("extent", 10.0))

    # Footprint half-extents from explicit spans or the square extent. The
    # standard viewer draws `PlaneGeometry(extent*2, …)`, i.e. the full side is
    # `2·extent`, so the box half-extent is exactly `extent`.
    if ent.span_u is not None and ent.span_v is not None:
        hu = ent.span_u.mag() / 2.0
        hv = ent.span_v.mag() / 2.0
    else:
        hu = extent
        hv = extent

    eps = max(0.02, min(hu, hv) * 0.01)
    normal = _normalize((ent.normal.x, ent.normal.y, ent.normal.z))
    if normal == (0.0, 0.0, 0.0):
        normal = _Z
    rotation = _rotation_align(_Z, normal)

    # A bounded slab: a thin box whose thin axis (local +Z) aligns to normal.
    slab = primitive(
        "box",
        {"halfExtents": [hu, hv, eps]},
        position=(ent.point.x, ent.point.y, ent.point.z),
        rotation=rotation,
    )
    return slab, resolved


def _point_pair_tree(
    ent: PointPair,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(
        props,
        "PointPair",
        {"point_size": 0.06, "line_thickness": 1.0},
        styles_map,
    )
    # Plan vocabulary: `size` (point spheres) + `thickness` (connecting
    # segment). Fall back to the standard `point_size`/`line_thickness`.
    size = float(props.get("size", resolved.get("point_size", 0.06)))
    thickness = float(props.get("thickness", resolved.get("line_thickness", 1.0)))

    a = (ent.point_a.x, ent.point_a.y, ent.point_a.z)
    b = (ent.point_b.x, ent.point_b.y, ent.point_b.z)
    direction = _normalize((b[0] - a[0], b[1] - a[1], b[2] - a[2]))
    length = math.dist(a, b)
    if direction == (0.0, 0.0, 0.0):
        direction = _Z
    half_length = length / 2.0
    midpoint = (
        a[0] + direction[0] * half_length,
        a[1] + direction[1] * half_length,
        a[2] + direction[2] * half_length,
    )
    rotation = _rotation_align(_Y, direction)

    sphere_a = primitive("sphere", {"radius": size}, position=a)
    sphere_b = primitive("sphere", {"radius": size}, position=b)
    segment = primitive(
        "cappedCylinder",
        {"halfHeight": half_length, "radius": thickness},
        position=midpoint,
        rotation=rotation,
    )
    tree = combine("union", sphere_a, sphere_b, segment)
    return tree, resolved