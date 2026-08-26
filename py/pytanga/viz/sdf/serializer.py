# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Entity → SDF primitive-tree serialization (the analytic path).

Maps the initially-supported geometric entities to compositions of the Phase 1
SDF primitive library. The result is a nested, JSON-ready tree consumed by
``templates/sdf/scene-builder.js``, which dispatches on the node ``kind`` to
emit the GLSL expression (mirroring ``renderers/factory.js``).

Supported kinds (others raise :class:`TypeError`):

    Entities: Point, HPoint, Direction, HDirection, Line, Plane, Circle,
    Sphere, PointPair, Space, Disk, PartialDisk, Box, Ellipsoid, Ellipse,
    RegularPolygon (imaginary variants use their base mapping).

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
    Box,
    Circle,
    Direction,
    Disk,
    Ellipse,
    Ellipsoid,
    Entity,
    HDirection,
    HPoint,
    Line,
    PartialDisk,
    Plane,
    Point,
    PointPair,
    RegularPolygon,
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
from ._compose import Combine, ECompose, SdfElement
from .composed import Composed
from .group import SdfGroup
from .object import SdfObject
from .bounds import compute_bounds
from .primitives import (
    SdfNode,
    _as_rotation,
    _basis_rotation,
    _rotate_about,
    combine,
    group,
    primitive,
)

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
    smoothness = props.get("smoothness")
    if smoothness is not None:
        result["smoothness"] = smoothness

    return result


def serialize_entity_local(
    entity: Entity | Any,
    entity_id: str,
    properties: dict[str, Any] | None = None,
    *,
    styles_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Serialize an entity for the standard viewer's per-object SDF renderer.

    Returns the full ``kind:"sdf"`` object shape from the wire contract (the
    README), including ``id``/``layer``. Unlike :func:`serialize_entity` (the
    fullscreen SDF viewer), this entry targets the standard viewer's
    bounding-volume proxy technique: a single object marches only its own tree
    in **local space**, and the node ``transform`` carries all placement.

    Phase 1 delegates to :func:`_dispatch_object` for the world-space tree and
    color/opacity resolution, and emits identity ``bound``/``transform`` stubs
    so the object shape is stable. Phase 2 replaces those stubs with a
    conservative local-space AABB and the placement transform.
    """
    props = dict(properties) if properties else {}

    if isinstance(entity, SdfGroup):
        return _serialize_sdf_group(entity, entity_id, props, styles_map)


    tree, resolved, sdf_kind = _dispatch_object(entity, props, styles_map)

    # Conservative AABB of the world-space tree (inflated by the SDF style's
    # ``bound_padding``).
    padding = _bound_padding(resolved)
    bounds = compute_bounds(tree, padding=padding)
    center = (
        (bounds["min"][0] + bounds["max"][0]) / 2.0,
        (bounds["min"][1] + bounds["max"][1]) / 2.0,
        (bounds["min"][2] + bounds["max"][2]) / 2.0,
    )
    half = (
        (bounds["max"][0] - bounds["min"][0]) / 2.0,
        (bounds["max"][1] - bounds["min"][1]) / 2.0,
        (bounds["max"][2] - bounds["min"][2]) / 2.0,
    )

    # Emit the tree in object-local space: shift the whole tree so the AABB is
    # centred at the origin; the node ``transform`` carries all placement.
    local_tree = _translate_tree(tree, (-center[0], -center[1], -center[2]))

    result: dict[str, Any] = {
        "id": entity_id,
        "layer": "scene",
        "kind": "sdf",
        "sdfKind": sdf_kind,
        "tree": local_tree.to_dict(),
        "bound": {
            "min": [-half[0], -half[1], -half[2]],
            "max": [half[0], half[1], half[2]],
        },
        "transform": {
            "position": list(center),
            "rotation": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0],
        },
    }

    # Multi-member foldables (Composed) carry a per-member material array, one
    # ``{color, opacity}`` per member (``None`` = inherit the object default).
    if isinstance(entity, Composed):
        result["materials"] = [_member_material(m) for m, _ in entity.parts]

    _finalize_sdf_object(result, resolved)
    return result


def _finalize_sdf_object(result: dict[str, Any], resolved: dict[str, Any]) -> None:
    """Attach color/opacity/style to an SDF object result dict (in place).

    For bare ``SdfNode``/``Composed``/``SdfGroup`` objects the color/opacity may
    arrive only via the style instance (e.g. ``SdfStyle(color=…)``), not as
    top-level props.
    """
    color = resolved.get("color")
    opacity = resolved.get("opacity")
    style = resolved.get("style")
    if isinstance(style, dict):
        style_dict = style
    elif style is not None and hasattr(style, "to_dict"):
        style_dict = style.to_dict()
    else:
        style_dict = {"style_type": "SdfStyle"}

    if color is None:
        color = style_dict.get("color")
    if opacity is None:
        opacity = style_dict.get("opacity")

    if color is not None:
        result["color"] = color
    if opacity is not None:
        result["opacity"] = opacity

    result["style"] = style_dict if style_dict else {"style_type": "SdfStyle"}


def _serialize_sdf_group(
    group: SdfGroup,
    entity_id: str,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> dict[str, Any]:
    """Serialize an :class:`SdfGroup` for the standard viewer's proxy renderer.

    Each member is emitted in its own local space with a runtime transform; the
    group tree is a ``group`` node whose children carry the per-member
    ``combine`` mode. The proxy ``bound`` is the union of the members' AABBs
    (recomputed dynamically by the frontend as members move).
    """
    resolved = dict(props)
    padding = _bound_padding(resolved)

    # 1. Serialize each member to a local tree + intrinsic centre + half-extent.
    children: list[SdfNode] = []
    centers: list[tuple[float, float, float]] = []
    halves: list[tuple[float, float, float]] = []
    materials: list[dict[str, Any]] = []
    for obj, combine_mode in group.parts:
        tree = _lower_member(obj)

        bounds = compute_bounds(tree, padding=padding)
        center = (
            (bounds["min"][0] + bounds["max"][0]) / 2.0,
            (bounds["min"][1] + bounds["max"][1]) / 2.0,
            (bounds["min"][2] + bounds["max"][2]) / 2.0,
        )
        half = (
            (bounds["max"][0] - bounds["min"][0]) / 2.0,
            (bounds["max"][1] - bounds["min"][1]) / 2.0,
            (bounds["max"][2] - bounds["min"][2]) / 2.0,
        )

        local_tree = _translate_tree(tree, (-center[0], -center[1], -center[2]))
        child = copy.copy(local_tree)
        child.combine = combine_mode.value
        children.append(child)
        centers.append(center)
        halves.append(half)
        materials.append(_member_material(obj))

    # 2. Group origin = union centre of the members' *intrinsic* placements.
    lo = [math.inf, math.inf, math.inf]
    hi = [-math.inf, -math.inf, -math.inf]
    for center, half in zip(centers, halves):
        for i in range(3):
            lo[i] = min(lo[i], center[i] - half[i])
            hi[i] = max(hi[i], center[i] + half[i])
    origin = (
        (lo[0] + hi[0]) / 2.0,
        (lo[1] + hi[1]) / 2.0,
        (lo[2] + hi[2]) / 2.0,
    )

    # 3. Build members, applying any per-member transform overrides (absolute,
    #    group-local; defaults to the intrinsic placement relative to origin).
    members: list[dict[str, Any]] = []
    for idx, (center, half) in enumerate(zip(centers, halves)):
        override = group.transforms.get(idx, {})
        position = override.get(
            "position",
            [center[0] - origin[0], center[1] - origin[1], center[2] - origin[2]],
        )
        rotation = override.get("rotation", [0.0, 0.0, 0.0])
        scale = override.get("scale", [1.0, 1.0, 1.0])
        members.append(
            {
                "transform": {
                    "position": list(position),
                    "rotation": list(rotation),
                    "scale": list(scale),
                },
                "bound": {
                    "min": [-half[0], -half[1], -half[2]],
                    "max": [half[0], half[1], half[2]],
                },
            }
        )

    # 4. Proxy box = union AABB of the members, centred at the (fixed) origin.
    lo = [math.inf, math.inf, math.inf]
    hi = [-math.inf, -math.inf, -math.inf]
    for member in members:
        pos = member["transform"]["position"]
        mlo = member["bound"]["min"]
        mhi = member["bound"]["max"]
        for i in range(3):
            lo[i] = min(lo[i], pos[i] + mlo[i])
            hi[i] = max(hi[i], pos[i] + mhi[i])
    half = [max(abs(lo[i]), abs(hi[i])) for i in range(3)]

    result: dict[str, Any] = {
        "id": entity_id,
        "layer": "scene",
        "kind": "sdf",
        "sdfKind": "SdfGroup",
        "tree": {"kind": "group", "children": [c.to_dict() for c in children]},
        "members": members,
        "materials": materials,
        "bound": {
            "min": [-half[0], -half[1], -half[2]],
            "max": [half[0], half[1], half[2]],
        },
        "transform": {
            "position": list(origin),
            "rotation": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0],
        },
    }

    _finalize_sdf_object(result, resolved)
    return result



def _bound_padding(resolved: dict[str, Any]) -> float:
    """Extract the SDF ``bound_padding`` knob from a resolved style."""
    style = resolved.get("style")
    if isinstance(style, dict):
        return float(style.get("bound_padding", 0.05))
    if style is not None and hasattr(style, "bound_padding"):
        return float(style.bound_padding)
    return 0.05


def _translate_tree(node: SdfNode, delta: tuple[float, float, float]) -> SdfNode:
    """Return a copy of *node* with every primitive position shifted by *delta*.

    Combinator nodes are copied recursively; only leaf primitives carry a
    ``transform`` (their ``position``). The world-space ``SdfVisualizer`` path
    never calls this, so its output is unchanged.
    """
    new = copy.copy(node)
    if node.children:
        new.children = [_translate_tree(c, delta) for c in node.children]
        return new

    position = node.transform.get("position") if node.transform else None
    new_position = (
        [position[0] + delta[0], position[1] + delta[1], position[2] + delta[2]]
        if position is not None
        else [delta[0], delta[1], delta[2]]
    )
    new_transform = dict(node.transform) if node.transform is not None else {}
    new_transform["position"] = new_position
    new.transform = new_transform
    return new


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
    if isinstance(entity, SdfObject):
        return entity.to_sdf_node(), _sdf_object_props(entity, props), "SdfObject"
    if isinstance(entity, Combine):
        return entity.to_sdf_node(), dict(props), "Combine"
    tree, resolved = _dispatch_tree(entity, props, styles_map)
    return tree, resolved, type(entity).__name__


def _sdf_object_props(entity: SdfObject, props: dict[str, Any]) -> dict[str, Any]:
    """Build resolved props for an ``SdfObject`` (its bundled style wins)."""
    resolved = dict(props)
    if entity.style is not None:
        resolved["style"] = entity.style
    return resolved


def _resolve_constituent(obj: Any) -> Any:
    """Resolve a raw MV constituent to a geometric entity via ``analyze()``.

    A :class:`Composed` may contain a raw MV alongside entities/operators/
    ``SdfNode``/nested ``Composed``. The analytic serializer has no MV path, so
    such constituents are reduced through ``geometry.analyze()`` first; anything
    else is returned unchanged.
    """
    from pytanga.algebra import MV

    if isinstance(obj, MV):
        from pytanga.geometry import analyze

        resolved = analyze(obj)
        if resolved is None:
            raise TypeError(f"Could not analyze object: {obj!r}")
        return resolved
    return obj


def _composed_tree(composed: Composed, styles_map: dict[str, Any] | None) -> SdfNode:
    """Build a ``group`` node from a :class:`Composed`'s members.

    Each member is an ``SdfElement`` (lowered via ``to_sdf_node()``) or an
    ``SdfNode``, tagged with its own ``combine`` mode for the ordered fold.
    """
    children: list[SdfNode] = []
    for part_obj, combine_mode in composed.parts:
        child = copy.copy(_lower_member(part_obj))
        child.combine = combine_mode.value
        children.append(child)
    return group(children)


def _lower_member(element: Any) -> SdfNode:
    """Lower a member (``SdfElement`` or ``SdfNode``) to an ``SdfNode``."""
    if isinstance(element, SdfElement):
        return element.to_sdf_node()
    return element


def _member_material(element: Any) -> dict[str, Any]:
    """Return a member's per-member ``{color, opacity}`` (``None`` = inherit)."""
    style = getattr(element, "style", None)
    return {
        "color": getattr(style, "color", None) if style is not None else None,
        "opacity": getattr(style, "opacity", None) if style is not None else None,
    }


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

    valid_combine = {
        "union",
        "intersection",
        "subtract",
        "smooth_union",
        "smooth_intersection",
        "smooth_subtract",
    }
    valid_polarity = {"positive", "negative"}

    combine = combine_value if combine_value in valid_combine else "union"
    polarity = polarity_value if polarity_value in valid_polarity else "positive"

    if combine_value is None and polarity_value == "negative":
        combine = "subtract"
    if polarity_value is None and combine_value in ("subtract", "smooth_subtract"):
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
    if isinstance(entity, Disk):
        return _disk_tree(entity, props, styles_map)
    if isinstance(entity, PartialDisk):
        return _partial_disk_tree(entity, props, styles_map)
    if isinstance(entity, Box):
        return _box_tree(entity, props, styles_map)
    if isinstance(entity, Ellipsoid):
        return _ellipsoid_tree(entity, props, styles_map)
    if isinstance(entity, Ellipse):
        return _ellipse_tree(entity, props, styles_map)
    if isinstance(entity, RegularPolygon):
        return _regular_polygon_tree(entity, props, styles_map)
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


def _disk_tree(
    ent: Disk,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Disk", {"thickness": 0.02}, styles_map)
    thickness = float(_param(resolved, "thickness", 0.02))
    normal = _normalize((ent.normal.x, ent.normal.y, ent.normal.z))
    if normal == (0.0, 0.0, 0.0):
        normal = _Z
    tree = primitive(
        "cappedCylinder",
        {"halfHeight": thickness / 2.0, "radius": ent.radius},
        position=(ent.center.x, ent.center.y, ent.center.z),
        rotation=_rotation_align(_Y, normal),
    )
    return tree, resolved


def _partial_disk_tree(
    ent: PartialDisk,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "PartialDisk", {"thickness": 0.02}, styles_map)
    thickness = float(_param(resolved, "thickness", 0.02))
    radius = float(ent.radius)
    angle = float(ent.angle)
    normal = _normalize((ent.normal.x, ent.normal.y, ent.normal.z))
    if normal == (0.0, 0.0, 0.0):
        normal = _Z
    center = (ent.center.x, ent.center.y, ent.center.z)

    # A full disk (angle >= 2π) is a plain capped cylinder.
    if angle >= 2.0 * math.pi - 1e-9:
        tree = primitive(
            "cappedCylinder",
            {"halfHeight": thickness / 2.0, "radius": radius},
            position=center,
            rotation=_rotation_align(_Y, normal),
        )
    else:
        start = (ent.start_direction.x, ent.start_direction.y, ent.start_direction.z)
        bisector = _rotate_about(start, normal, angle / 2.0)
        rotation = _basis_rotation(normal, bisector)
        tree = primitive(
            "partialDisk",
            {"halfHeight": thickness / 2.0, "radius": radius, "angle": angle},
            position=center,
            rotation=rotation,
        )
    return tree, resolved


def _box_tree(
    ent: Box,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Box", {}, styles_map)
    rotation = _as_rotation(ent.rotation) if ent.rotation is not None else None
    tree = primitive(
        "box",
        {"halfExtents": [ent.size[0] / 2.0, ent.size[1] / 2.0, ent.size[2] / 2.0]},
        position=(ent.center.x, ent.center.y, ent.center.z),
        rotation=rotation,
    )
    return tree, resolved


def _ellipsoid_tree(
    ent: Ellipsoid,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Ellipsoid", {}, styles_map)
    rotation = _as_rotation(ent.rotation) if ent.rotation is not None else None
    tree = primitive(
        "ellipsoid",
        {"radii": [ent.radii[0], ent.radii[1], ent.radii[2]]},
        position=(ent.center.x, ent.center.y, ent.center.z),
        rotation=rotation,
    )
    return tree, resolved


def _ellipse_tree(
    ent: Ellipse,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "Ellipse", {"thickness": 0.02}, styles_map)
    thickness = float(_param(resolved, "thickness", 0.02))
    normal = _normalize((ent.normal.x, ent.normal.y, ent.normal.z))
    if normal == (0.0, 0.0, 0.0):
        normal = _Z
    tree = primitive(
        "ellipsoid",
        {"radii": [ent.radius_u, ent.radius_v, thickness / 2.0]},
        position=(ent.center.x, ent.center.y, ent.center.z),
        rotation=_rotation_align(_Z, normal),
    )
    return tree, resolved


def _regular_polygon_tree(
    ent: RegularPolygon,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    resolved = _resolve(props, "RegularPolygon", {"thickness": 0.02}, styles_map)
    thickness = float(_param(resolved, "thickness", 0.02))
    normal = _normalize((ent.normal.x, ent.normal.y, ent.normal.z))
    if normal == (0.0, 0.0, 0.0):
        normal = _Z
    vertex_dir = _rotate_about(_Z, normal, ent.angle)
    rotation = _basis_rotation(normal, vertex_dir)
    tree = primitive(
        "regularPolygon",
        {"halfHeight": thickness / 2.0, "radius": float(ent.radius), "sides": int(ent.sides)},
        position=(ent.center.x, ent.center.y, ent.center.z),
        rotation=rotation,
    )
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