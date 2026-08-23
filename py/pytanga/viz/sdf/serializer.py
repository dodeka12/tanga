# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Entity → SDF primitive-tree serialization (the analytic path).

Maps the initially-supported geometric entities to compositions of the Phase 1
SDF primitive library. The result is a nested, JSON-ready tree consumed by
``templates/sdf/scene-builder.js``, which dispatches on the node ``kind`` to
emit the GLSL expression (mirroring ``renderers/factory.js``).

Supported kinds (others raise :class:`TypeError`):

    Entities: Point, HPoint, Direction, HDirection, Line, Plane, Circle,
    Sphere, PointPair, Space (imaginary variants use their base mapping).

    Operators: ReflectionLine, ReflectionPlane, ReflectionPoint, Inversion,
    Rotor, Translator, Dilator, Motor, GeneralRotor. ``TripleReflection`` and
    ``VersorFactors`` are deferred.

Style scope is minimal per kind — ``color``/``opacity`` on all kinds, ``size``
for ``Point``/``HPoint`` (sphere radius), ``thickness`` for ``Line``/``Circle``
(and the ``PointPair`` connecting segment), and per-kind length/extent/radius
parameters. A ``CrossHairPointStyle`` draws a 3-axis crosshair. ``wireframe``
is not honoured by the SDF path (a true wireframe cage is a 1D structure the
ray-marcher cannot express as a solid; deferred).

Reuses :func:`pytanga.viz.serializer._apply_defaults` so color/opacity and the
per-kind size/thickness parameters resolve with exactly the same priority as the
standard viewer (per-entity props > style > canonical > builtin).
"""

from __future__ import annotations

import copy
import math
from typing import Any

from pytanga.geometry.entities import (
    Circle,
    Direction,
    Entity,
    HDirection,
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
    GeneralRotor,
    Inversion,
    Motor,
    ReflectionLine,
    ReflectionPlane,
    ReflectionPoint,
    Rotor,
    Translator,
)
from pytanga.algebra import MV

from .algebra_embedding import embed_entity_mv
from .composed import Composed
from .primitives import SdfNode, combine, group, primitive

# ── Public API ─────────────────────────────────────────────


def serialize_entity(
    entity: Entity | Any,
    entity_id: str,
    properties: dict[str, Any] | None = None,
    *,
    styles_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Serialize an SDF scene object (entity, :class:`SdfNode`, or :class:`Composed`).

    Raises :class:`TypeError` for unsupported kinds (operators, ``Direction``,
    ``Space``, …).

    Returns a dict carrying the id, the SDF ``tree``, the resolved ``color`` /
    ``opacity``, and the per-object ``combine``/``polarity`` mode.
    """
    props = dict(properties) if properties else {}
    if isinstance(entity, MV):
        return serialize_mv(entity, entity_id, props, styles_map)

    tree, resolved, sdf_kind = _dispatch_object(entity, props, styles_map)

    result: dict[str, Any] = {
        "id": entity_id,
        "layer": "scene",
        "kind": "sdf",
        "sdfKind": sdf_kind,
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


def serialize_mv(
    mv: MV,
    entity_id: str,
    properties: dict[str, Any] | None = None,
    styles_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Serialize a raw MV to an ``mv_sdf`` scene object (the algebra path).

    Unlike the analytic path, the MV is *not* routed through
    ``geometry.analyze()``; it is reduced directly to its product matrix via
    :func:`~pytanga.viz.sdf.algebra_embedding.embed_entity_mv`. The result
    carries ``sdfKind: "mv_sdf"`` plus the wire fields (``algebra``, ``M``,
    ``point_ids``, …), the resolved ``color``/``opacity``, and the per-object
    ``combine``/``polarity`` mode.
    """
    props = dict(properties) if properties else {}

    wire = embed_entity_mv(
        mv,
        normalize=props.get("normalize", True),
        bound=props.get("bound"),
        calibrate=bool(props.get("calibrate", False)),
    )

    result: dict[str, Any] = {
        "id": entity_id,
        "layer": "scene",
        "kind": "sdf",
        "sdfKind": "mv_sdf",
        **wire,
    }

    color = props.get("color")
    if color is not None:
        result["color"] = color
    opacity = props.get("opacity")
    if opacity is not None:
        result["opacity"] = opacity

    combine_mode = _normalize_combine(props)
    result["combine"] = combine_mode["combine"]
    result["polarity"] = combine_mode["polarity"]

    return result


def _dispatch_object(
    entity: Any,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any], str]:
    """Route an SDF object to an SDF tree + resolved style + ``sdfKind``.

    ``SdfNode`` (a bare primitive/combinator tree) and ``Composed`` (a grouped
    tree with per-constituent combine modes) are already SDF descriptions, so
    they pass through without entity dispatch; geometry entities go through the
    per-kind :func:`_dispatch_tree`.
    """
    if isinstance(entity, SdfNode):
        return entity, dict(props), entity.kind
    if isinstance(entity, Composed):
        return _composed_tree(entity, styles_map), dict(props), "Composed"
    tree, resolved = _dispatch_tree(entity, props, styles_map)
    return tree, resolved, type(entity).__name__


def _composed_tree(composed: Composed, styles_map: dict[str, Any] | None) -> SdfNode:
    """Build a ``group`` node from a :class:`Composed`'s constituents.

    Each constituent is serialized independently (so it may be an entity, an
    ``SdfNode``, or a nested ``Composed``) and tagged with its own ``combine``
    mode for the ordered group fold.
    """
    children: list[SdfNode] = []
    for part_obj, combine_mode in composed.parts:
        child, _, _ = _dispatch_object(part_obj, {}, styles_map)
        child = copy.copy(child)
        child.combine = combine_mode
        children.append(child)
    return group(children)


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
    entity: Any,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    # Entities
    if isinstance(entity, Point):
        return _point_tree(entity, props, styles_map)
    if isinstance(entity, HPoint):
        return _hpoint_tree(entity, props, styles_map)
    if isinstance(entity, Direction):
        return _direction_tree(entity, props, styles_map)
    if isinstance(entity, HDirection):
        return _hdirection_tree(entity, props, styles_map)
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
    if isinstance(entity, Space):
        return _space_tree(entity, props, styles_map)
    # Operators
    if isinstance(entity, ReflectionLine):
        return _reflection_line_tree(entity, props, styles_map)
    if isinstance(entity, ReflectionPlane):
        return _reflection_plane_tree(entity, props, styles_map)
    if isinstance(entity, ReflectionPoint):
        return _reflection_point_tree(entity, props, styles_map)
    if isinstance(entity, Inversion):
        return _inversion_tree(entity, props, styles_map)
    if isinstance(entity, Rotor):
        return _rotor_tree(entity, props, styles_map)
    if isinstance(entity, Translator):
        return _translator_tree(entity, props, styles_map)
    if isinstance(entity, Dilator):
        return _dilator_tree(entity, props, styles_map)
    if isinstance(entity, Motor):
        return _motor_tree(entity, props, styles_map)
    if isinstance(entity, GeneralRotor):
        return _general_rotor_tree(entity, props, styles_map)
    raise TypeError(f"SDF viewer does not support {type(entity).__name__!r}")


# ── Style resolution ───────────────────────────────────────


def _resolve(props: dict[str, Any], kind: str, builtin: dict[str, Any], styles_map: dict[str, Any] | None) -> dict[str, Any]:
    from pytanga.viz.serializer import _apply_defaults

    return _apply_defaults(dict(props), kind, builtin, styles_map=styles_map)


def _param(resolved: dict[str, Any], key: str, default: Any) -> Any:
    """Read a resolved style parameter (merged style first, then top-level)."""
    style = resolved.get("style", {})
    value = style.get(key)
    if value is None:
        value = resolved.get(key)
    return default if value is None else value


def _style_type(resolved: dict[str, Any]) -> str | None:
    """Return the effective draw-style type string (e.g. ``"CrossHairPointStyle"``)."""
    return resolved.get("style", {}).get("style_type")


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


def _along(
    origin: tuple[float, float, float],
    direction: tuple[float, float, float],
    t: float,
) -> tuple[float, float, float]:
    """Point at distance ``t`` along ``direction`` from ``origin``."""
    return (
        origin[0] + direction[0] * t,
        origin[1] + direction[1] * t,
        origin[2] + direction[2] * t,
    )


def _tube(
    origin: tuple[float, float, float],
    direction: tuple[float, float, float],
    half_height: float,
    radius: float,
) -> SdfNode:
    """Capped cylinder centred ``half_height`` along ``direction`` from ``origin``."""
    direction = _normalize(direction)
    if direction == (0.0, 0.0, 0.0):
        direction = _Z
    midpoint = _along(origin, direction, half_height)
    rotation = _rotation_align(_Y, direction)
    return primitive(
        "cappedCylinder",
        {"halfHeight": half_height, "radius": radius},
        position=midpoint,
        rotation=rotation,
    )


def _disc_node(
    center: tuple[float, float, float],
    axis: tuple[float, float, float],
    radius: float,
) -> SdfNode:
    """Thin disc perpendicular to ``axis`` (a rotor/de-rotation glyph)."""
    axis = _normalize(axis)
    if axis == (0.0, 0.0, 0.0):
        axis = _Z
    rotation = _rotation_align(_Y, axis)
    thickness = max(0.005, radius * 0.015)
    return primitive(
        "cappedCylinder",
        {"halfHeight": thickness, "radius": radius},
        position=center,
        rotation=rotation,
    )


def _ring_node(
    center: tuple[float, float, float],
    axis: tuple[float, float, float],
    main_radius: float,
    tube_radius: float,
) -> SdfNode:
    """Torus ring in the plane perpendicular to ``axis`` (an orbit outline)."""
    axis = _normalize(axis)
    if axis == (0.0, 0.0, 0.0):
        axis = _Z
    rotation = _rotation_align(_Y, axis)
    return primitive(
        "torus",
        {"mainRadius": main_radius, "tubeRadius": tube_radius},
        position=center,
        rotation=rotation,
    )


def _sector(
    center: tuple[float, float, float],
    axis: tuple[float, float, float],
    base: SdfNode,
    angle: float,
) -> SdfNode:
    """Clip ``base`` (an SDF in the plane ⟂ ``axis``) to the sector ``[0, angle]``.

    The sector spans ``[0, min(|angle|, π)]`` measured counter-clockwise from
    the local +X axis; angles beyond π are clamped to a half-plane.
    """
    a = min(abs(angle), math.pi)
    if a < 1e-6:
        return base
    axis = _normalize(axis)
    if axis == (0.0, 0.0, 0.0):
        axis = _Z
    rotation = _rotation_align(_Y, axis)
    # Sector θ ∈ [0, a] in the local XZ plane (θ from +X toward +Z):
    #   · θ ≥ 0  ⇔ keep z ≥ 0                 → plane normal (0, 0, −1)
    #   · θ ≤ a  ⇔ keep cos a·z − sin a·x ≤ 0 → plane normal (−sin a, 0, cos a)
    plane_lo = primitive(
        "plane",
        {"normal": [0.0, 0.0, -1.0], "offset": 0.0},
        position=center,
        rotation=rotation,
    )
    if a >= math.pi - 1e-6:
        return combine("intersect", base, plane_lo)
    plane_hi = primitive(
        "plane",
        {"normal": [-math.sin(a), 0.0, math.cos(a)], "offset": 0.0},
        position=center,
        rotation=rotation,
    )
    return combine("intersect", base, plane_lo, plane_hi)


def _arrow_node(
    origin: tuple[float, float, float],
    direction: tuple[float, float, float],
    length: float,
    shaft_radius: float,
) -> SdfNode:
    """Arrow (capped-cylinder shaft + conical tip) along ``direction``."""
    direction = _normalize(direction)
    if direction == (0.0, 0.0, 0.0):
        direction = _Z
    rotation = _rotation_align(_Y, direction)
    tip_height = min(length * 0.3, 0.5)
    tip_radius = max(shaft_radius * 2.5, 0.05)
    shaft_length = max(length - tip_height, 0.0)
    shaft = primitive(
        "cappedCylinder",
        {"halfHeight": shaft_length / 2.0, "radius": shaft_radius},
        position=_along(origin, direction, shaft_length / 2.0),
        rotation=rotation,
    )
    tip = primitive(
        "cappedCone",
        {"halfHeight": tip_height / 2.0, "radius1": tip_radius, "radius2": 0.0},
        position=_along(origin, direction, shaft_length + tip_height / 2.0),
        rotation=rotation,
    )
    return combine("union", shaft, tip)


def _axis_arrow_node(
    center: tuple[float, float, float],
    axis: tuple[float, float, float],
    length: float,
) -> SdfNode:
    """Axis arrow along +``axis`` (the dual of the rotor bivector).

    The shaft runs from ``center`` to ``center + axis·length``; the arrowhead's
    base sits at the shaft end and its apex points further along +``axis``.
    """
    axis = _normalize(axis)
    if axis == (0.0, 0.0, 0.0):
        axis = _Z
    rotation = _rotation_align(_Y, axis)
    shaft_radius = max(0.006, length * 0.02)
    tip_height = length * 0.3
    tip_radius = max(shaft_radius * 2.5, 0.05)
    shaft_length = max(length - tip_height, 0.0)
    shaft = primitive(
        "cappedCylinder",
        {"halfHeight": shaft_length / 2.0, "radius": shaft_radius},
        position=_along(center, axis, shaft_length / 2.0),
        rotation=rotation,
    )
    tip = primitive(
        "cappedCone",
        {"halfHeight": tip_height / 2.0, "radius1": tip_radius, "radius2": 0.0},
        position=_along(center, axis, shaft_length + tip_height / 2.0),
        rotation=rotation,
    )
    return combine("union", shaft, tip)


def _rotor_glyph(
    center: tuple[float, float, float],
    axis: tuple[float, float, float],
    radius: float,
    angle: float,
) -> SdfNode:
    """Rotor glyph: sector disc (filled to the angle) + full rim ring + axis arrow."""
    axis = _normalize(axis)
    if axis == (0.0, 0.0, 0.0):
        axis = _Z
    disc = _sector(center, axis, _disc_node(center, axis, radius), angle)
    tube_radius = max(0.015, radius * 0.02)
    ring_radius = radius + tube_radius + max(0.02, radius * 0.02)
    ring = _ring_node(center, axis, ring_radius, tube_radius)
    axis_arrow = _axis_arrow_node(center, axis, radius * 2.5)
    return combine("union", disc, ring, axis_arrow)


# ── Per-kind tree builders ─────────────────────────────────


def _point_tree(
    ent: Point,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Point", {"size": 0.08}, styles_map)
    size = float(_param(resolved, "size", 0.08))
    if _style_type(resolved) == "CrossHairPointStyle":
        tree = _crosshair_node((ent.x, ent.y, ent.z), size, resolved)
    else:
        tree = primitive("sphere", {"radius": size}, position=(ent.x, ent.y, ent.z))
    return tree, resolved


def _crosshair_node(
    position: tuple[float, float, float],
    size: float,
    resolved: dict[str, Any],
) -> SdfNode:
    """A 3-axis crosshair (three thin boxes) for ``CrossHairPointStyle``."""
    arm = resolved.get("style", {}).get("arm_thickness")
    half_t = float(arm) / 2.0 if arm is not None else max(size * 0.15, 0.01)
    box_x = primitive("box", {"halfExtents": [size, half_t, half_t]}, position=position)
    box_y = primitive("box", {"halfExtents": [half_t, size, half_t]}, position=position)
    box_z = primitive("box", {"halfExtents": [half_t, half_t, size]}, position=position)
    return combine("union", box_x, box_y, box_z)


def _sphere_tree(
    ent: Sphere,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    kind_name = "ImagSphere" if ent.is_imaginary else "Sphere"
    resolved = _resolve(props, kind_name, {}, styles_map)
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


def _hpoint_tree(
    ent: HPoint,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "HPoint", {"size": 0.08}, styles_map)
    size = float(_param(resolved, "size", 0.08))
    tree = primitive(
        "sphere", {"radius": size}, position=(ent.point.x, ent.point.y, ent.point.z)
    )
    return tree, resolved


def _direction_tree(
    ent: Direction,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Direction", {"length": 2.0}, styles_map)
    length = float(_param(resolved, "length", 2.0))
    direction = _normalize((ent.x, ent.y, ent.z))
    if direction == (0.0, 0.0, 0.0):
        direction = _Z
    tree = _arrow_node((0.0, 0.0, 0.0), direction, length, max(length * 0.05, 0.02))
    return tree, resolved


def _hdirection_tree(
    ent: HDirection,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Direction", {"length": 2.0}, styles_map)
    length = float(_param(resolved, "length", 2.0))
    direction = _normalize((ent.direction.x, ent.direction.y, ent.direction.z))
    if direction == (0.0, 0.0, 0.0):
        direction = _Z
    tree = _arrow_node((0.0, 0.0, 0.0), direction, length, max(length * 0.05, 0.02))
    return tree, resolved


def _space_tree(
    ent: Space,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Space", {"extent": 10.0}, styles_map)
    extent = float(_param(resolved, "extent", 10.0))
    tree = primitive("box", {"halfExtents": [extent, extent, extent]})
    return tree, resolved


# ── Operator tree builders ─────────────────────────────────


def _reflection_line_tree(
    ent: ReflectionLine,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(
        props, "ReflectionLine", {"length": 5.0, "thickness": 0.04}, styles_map
    )
    length = float(_param(resolved, "length", 5.0))
    thickness = float(_param(resolved, "thickness", 0.04))
    origin = (ent.line.origin.x, ent.line.origin.y, ent.line.origin.z)
    direction = (ent.line.direction.x, ent.line.direction.y, ent.line.direction.z)
    tree = _tube(origin, direction, length / 2.0, thickness)
    return tree, resolved


def _reflection_plane_tree(
    ent: ReflectionPlane,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    plane = ent.plane
    local_props = dict(props)
    if plane.extent is not None:
        local_props["extent"] = plane.extent
    resolved = _resolve(local_props, "ReflectionPlane", {"extent": 5.0}, styles_map)
    extent = float(_param(resolved, "extent", 5.0))
    if plane.span_u is not None and plane.span_v is not None:
        hu = plane.span_u.mag() / 2.0
        hv = plane.span_v.mag() / 2.0
    else:
        hu = extent
        hv = extent
    eps = max(0.02, min(hu, hv) * 0.01)
    normal = _normalize((plane.normal.x, plane.normal.y, plane.normal.z))
    if normal == (0.0, 0.0, 0.0):
        normal = _Z
    rotation = _rotation_align(_Z, normal)
    tree = primitive(
        "box",
        {"halfExtents": [hu, hv, eps]},
        position=(plane.point.x, plane.point.y, plane.point.z),
        rotation=rotation,
    )
    return tree, resolved


def _reflection_point_tree(
    ent: ReflectionPoint,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "ReflectionPoint", {"extent": 1.0}, styles_map)
    extent = float(_param(resolved, "extent", 1.0))
    size = 0.08 * max(extent, 0.1)
    tree = primitive(
        "sphere", {"radius": size}, position=(ent.point.x, ent.point.y, ent.point.z)
    )
    return tree, resolved


def _inversion_tree(
    ent: Inversion,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Inversion", {}, styles_map)
    tree = primitive(
        "sphere",
        {"radius": ent.radius},
        position=(ent.center.x, ent.center.y, ent.center.z),
    )
    return tree, resolved


def _rotor_tree(
    ent: Rotor,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Rotor", {"discRadius": 1.5}, styles_map)
    radius = float(_param(resolved, "discRadius", 1.5))
    tree = _rotor_glyph(
        (0.0, 0.0, 0.0), (ent.axis.x, ent.axis.y, ent.axis.z), radius, ent.angle
    )
    return tree, resolved


def _translator_tree(
    ent: Translator,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Translator", {"length": 3.0}, styles_map)
    length = float(_param(resolved, "length", 3.0))
    direction = _normalize((ent.vector.x, ent.vector.y, ent.vector.z))
    if direction == (0.0, 0.0, 0.0):
        direction = _Z
    tree = _arrow_node((0.0, 0.0, 0.0), direction, length, max(length * 0.04, 0.02))
    return tree, resolved


def _dilator_tree(
    ent: Dilator,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Dilator", {"ringCount": 4, "maxRadius": 3.0}, styles_map)
    ring_count = max(int(_param(resolved, "ringCount", 4)), 1)
    max_radius = float(_param(resolved, "maxRadius", 3.0))
    position = (ent.origin.x, ent.origin.y, ent.origin.z)
    rings = []
    for i in range(1, ring_count + 1):
        r = max_radius * i / ring_count
        rings.append(
            primitive(
                "torus",
                {"mainRadius": r, "tubeRadius": max(0.015, r * 0.02)},
                position=position,
            )
        )
    return combine("union", *rings), resolved


def _motor_tree(
    ent: Motor,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Motor", {}, styles_map)
    axis = _normalize((ent.rotor.axis.x, ent.rotor.axis.y, ent.rotor.axis.z))
    if axis == (0.0, 0.0, 0.0):
        axis = _Z
    disc = _disc_node((0.0, 0.0, 0.0), axis, 1.0)
    vector = _normalize(
        (ent.translator.vector.x, ent.translator.vector.y, ent.translator.vector.z)
    )
    if vector == (0.0, 0.0, 0.0):
        vector = _Z
    arrow = _arrow_node((0.0, 0.0, 0.0), vector, 2.0, 0.08)
    tree = combine("union", disc, arrow)
    return tree, resolved


def _general_rotor_tree(
    ent: GeneralRotor,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "GeneralRotor", {}, styles_map)
    tree = _rotor_glyph(
        (ent.origin.x, ent.origin.y, ent.origin.z),
        (ent.axis.x, ent.axis.y, ent.axis.z),
        1.0,
        ent.angle,
    )
    return tree, resolved