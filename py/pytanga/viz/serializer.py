# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Entity/Operator → JSON serialization for the Tanga 3D viewer.

Pure functions with no network or Three.js dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pytanga.geometry.entities import (
    Circle,
    Direction,
    Entity,
    HPoint,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
)

from ._point_path import PointPath
from ._scene_objects import (
    Axes2D,
    Axes3D,
    Axis,
    Grid,
    _AXES_Z,
    _pad_origin,
    _scale_dir,
)
from pytanga.geometry.operators import (
    Dilator,
    GeneralRotor,
    Inversion,
    Motor,
    ReflectionLine,
    ReflectionPoint,
    ReflectionPlane,
    Rotor,
    Translator,
)

# ── Public API ─────────────────────────────────────────────


def serialize_entity(
    entity: Entity | Any,
    entity_id: str,
    properties: Dict[str, Any] | None = None,
    *,
    kind: str | None = None,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Convert a geometry entity + rendering properties into a flat JSON-ready dict.

    Args:
        entity: A pytanga.geometry Entity or Operator instance.
        entity_id: The scene-assigned ID string.
        properties: Per-entity rendering properties (color, opacity, ...).
        kind: The kind string (``type(entity).__name__``).  When ``None`` it
            is auto-detected from ``entity``.  Passing the pre-computed kind
            from ``SceneObject`` avoids duplicating type checks.
        styles_map: Per-kind style dict from Visualizer.default_styles.

    Returns:
        A flat dict suitable for ``json.dumps()``.
    """
    props = dict(properties) if properties else {}
    if kind is None:
        kind = type(entity).__name__

    result: Dict[str, Any] = {"id": entity_id, "layer": "scene"}
    result.update(_dispatch_entity(entity, kind, props, styles_map))
    return result


def _dispatch_entity(
    entity: Any,
    kind: str,
    props: Dict[str, Any],
    styles_map: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Route an entity/operator to its per-kind leaf serializer.

    Returns the flat geometry + style fields (no ``id``/``layer``).  Shared by
    :func:`serialize_entity` (backward-compat trampoline) and the scene-graph
    node serializers in ``_nodes.py``.
    """
    # ── Entities ──
    if isinstance(entity, PointPath):
        return _serialize_point_path(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Axes2D):
        return _serialize_axes2d(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Axes3D):
        return _serialize_axes3d(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Axis):
        return _serialize_axis(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Grid):
        return _serialize_grid(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Point):
        return _serialize_point(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Direction):
        return _serialize_direction(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, HPoint):
        return _serialize_hpoint(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, PointPair):
        return _serialize_point_pair(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Line):
        return _serialize_line(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Plane):
        return _serialize_plane(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Circle):
        return _serialize_circle(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Sphere):
        return _serialize_sphere(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Space):
        return _serialize_space(entity, props, kind=kind, styles_map=styles_map)

    # ── Operators ──
    if isinstance(entity, ReflectionLine):
        return _serialize_reflection_line(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, ReflectionPlane):
        return _serialize_reflection_plane(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, ReflectionPoint):
        return _serialize_reflection_origin(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Inversion):
        return _serialize_inversion(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Rotor):
        return _serialize_rotor(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Translator):
        return _serialize_translator(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Dilator):
        return _serialize_dilator(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, Motor):
        return _serialize_motor(entity, props, kind=kind, styles_map=styles_map)
    if isinstance(entity, GeneralRotor):
        return _serialize_general_rotor(entity, props, kind=kind, styles_map=styles_map)

    raise TypeError(f"Unknown entity type: {kind}")


def serialize_scene_update(
    entities: List[Dict[str, Any]],
    removed: List[str],
    *,
    labels: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Wrap entity/removed/label lists into the top-level WebSocket message format."""
    objects = list(entities)
    if labels:
        objects.extend(labels)
    return {
        "type": "scene_update",
        "objects": objects,
        "removed": removed,
    }


def serialize_object_update(
    patches: List[Dict[str, Any]],
    removed: List[str],
) -> Dict[str, Any]:
    """Wrap aspect-scoped patches + removals into the ``object_update`` message.

    Each patch is ``{"id", "aspect", "value"}`` (see ``VizNode.patch``).
    ``scene`` is left empty here; the caller sets the scene name.
    """
    return {
        "type": "object_update",
        "scene": "",
        "patches": list(patches),
        "removed": list(removed),
    }


# ── Helpers ────────────────────────────────────────────────


def _apply_defaults(
    props: Dict[str, Any],
    kind: str,
    builtin: Dict[str, Any],
    *,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Merge priorities: per-entity props > user style > canonical style > builtin.

    ``styles_map`` is the Visualizer's per-kind style dict.
    Entity-specific params (size, length, extent, …) are read from the
    resolved style first, falling back to ``builtin``.
    """
    from ._styles import _style_for_kind, _style_to_output

    result: Dict[str, Any] = {"kind": kind}
    resolved = _style_for_kind(kind, styles_map=styles_map)

    # ── Build result from props, then style, then builtin ──
    # Start with builtin defaults (lowest priority)
    for key, default_value in builtin.items():
        result[key] = default_value
    # Overlay from canonical style (medium priority)
    for key in builtin:
        style_val = getattr(resolved, key, None)
        if style_val is not None:
            result[key] = style_val
    # Overlay from per-entity props (highest priority for builtin keys)
    for key, value in props.items():
        if key in builtin or key not in ("style",):
            result[key] = value

    # ── Style object (merged: user overrides + canonical defaults) ──
    merged_style = _style_to_output(props.get("style"), kind, styles_map=styles_map)

    # ── Overlay per-entity color/opacity into the style dict ──
    # This ensures styleParam() on the JS side sees the override.
    if "color" in result:
        merged_style["color"] = result["color"]
    if "opacity" in result:
        merged_style["opacity"] = result["opacity"]

    # ── Overlay per-entity builtin overrides into the style dict ──
    # The JS styleParam() checks ent.style first, so any per-entity
    # override of a builtin key (length, thickness, extent, …) must
    # also be mirrored into the merged style dict.  We only overlay
    # keys that were explicitly set in per-entity props — not keys
    # that merely inherited from the canonical style or builtins.
    for key in builtin:
        if key in props and key not in ("color", "opacity"):
            merged_style[key] = result[key]

    # Also pull color/opacity from merged style if not otherwise resolved
    if "color" not in result and "color" in merged_style:
        result["color"] = merged_style["color"]
    if "opacity" not in result and "opacity" in merged_style:
        result["opacity"] = merged_style["opacity"]

    result["style"] = merged_style
    return result


def _clamp_positive(val: float, minimum: float = 0.001) -> float:
    return max(val, minimum)


# ── Entities ────────────────────────────────────────────────


def _serialize_point_path(
    ent: PointPath,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {"line_thickness": 0.03},
        styles_map=styles_map,
    ) | {
        "points": [list(p) for p in ent.points],
        "colors": ent.colors,
    }


def _serialize_axis(
    ent: Axis,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    result = _apply_defaults(
        props,
        kind,
        {"line_thickness": 0.03},
        styles_map=styles_map,
    ) | {
        "start": list(ent.start),
        "end": list(ent.end),
        "majorInterval": ent.major_interval,
        "labelAtMajor": ent.label_at_major,
        "labelFormat": ent.label_format,
        "showTicks": ent.show_ticks,
    }
    if ent.minor_interval is not None:
        result["minorInterval"] = ent.minor_interval
    if ent.label_size is not None:
        result["labelSize"] = ent.label_size
    if ent.label is not None:
        result["label"] = ent.label
    if ent.value_start != 0.0:
        result["valueStart"] = ent.value_start
    if ent.value_step != 1.0:
        result["valueStep"] = ent.value_step
    return result


def _serialize_axes2d(
    ent: Axes2D,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Serialize an :class:`Axes2D` as a single scene object.

    The group carries an ``axes`` list, each entry describing one axis half
    (positive and/or negative) with its resolved per-direction style.
    """
    origin = _pad_origin(ent.origin, _AXES_Z)
    u_label = ent.labels[0] if ent.labels is not None else None
    v_label = ent.labels[1] if ent.labels is not None else None
    styles = _resolve_group_axis_styles(props, kind, 2, styles_map=styles_map)
    axes = _build_axes_entries(
        origin,
        [
            (ent.dir_u, ent.range_u, u_label),
            (ent.dir_v, ent.range_v, v_label),
        ],
        styles,
        ent.major_interval,
    )
    result: Dict[str, Any] = {
        "kind": kind,
        "origin": list(origin),
        "dir_u": list(ent.dir_u),
        "dir_v": list(ent.dir_v),
        "range_u": list(ent.range_u),
        "range_v": list(ent.range_v),
        "major_interval": ent.major_interval,
        "axes": axes,
    }
    if ent.labels is not None:
        result["labels"] = list(ent.labels)
    return result


def _serialize_axes3d(
    ent: Axes3D,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Serialize an :class:`Axes3D` as a single scene object."""
    origin = ent.origin if len(ent.origin) == 3 else _pad_origin(ent.origin, 0.0)
    u_label = ent.labels[0] if ent.labels is not None else None
    v_label = ent.labels[1] if ent.labels is not None else None
    w_label = ent.labels[2] if ent.labels is not None else None
    styles = _resolve_group_axis_styles(props, kind, 3, styles_map=styles_map)
    axes = _build_axes_entries(
        origin,
        [
            (ent.dir_u, ent.range_u, u_label),
            (ent.dir_v, ent.range_v, v_label),
            (ent.dir_w, ent.range_w, w_label),
        ],
        styles,
        ent.major_interval,
    )
    result: Dict[str, Any] = {
        "kind": kind,
        "origin": list(origin),
        "dir_u": list(ent.dir_u),
        "dir_v": list(ent.dir_v),
        "dir_w": list(ent.dir_w),
        "range_u": list(ent.range_u),
        "range_v": list(ent.range_v),
        "range_w": list(ent.range_w),
        "major_interval": ent.major_interval,
        "axes": axes,
    }
    if ent.labels is not None:
        result["labels"] = list(ent.labels)
    return result


def _resolve_group_axis_styles(
    props: Dict[str, Any],
    kind: str,
    n: int,
    *,
    styles_map: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Resolve per-direction axis styles into complete merged dicts.

    Priority for the per-direction style source:
    1. a user :class:`AxisStyle` applied to every direction,
    2. a user :class:`Axes2DStyle` / :class:`Axes3DStyle` instance,
    3. the canonical group style for ``kind``.

    Each :class:`AxisStyle` is then resolved against the canonical ``"Axis"``
    default so sparse styles still get ``color``/``opacity``/``line_thickness``.
    """
    from ._styles import (
        Axes2DStyle,
        Axes3DStyle,
        AxisStyle,
        _style_for_kind,
        _style_to_output,
    )

    group_style = props.get("style")
    canonical = _style_for_kind(kind, styles_map=styles_map)

    if isinstance(group_style, AxisStyle):
        base: List[Any] = [group_style] * n
    elif isinstance(group_style, (Axes2DStyle, Axes3DStyle)):
        base = [getattr(group_style, name) for name in ("u", "v", "w")[:n]]
    elif isinstance(canonical, (Axes2DStyle, Axes3DStyle)):
        base = [getattr(canonical, name) for name in ("u", "v", "w")[:n]]
    else:
        base = [AxisStyle()] * n

    resolved: List[Dict[str, Any]] = []
    for axis_style in base:
        style = _style_to_output(axis_style, "Axis", styles_map=styles_map)
        if props.get("color") is not None:
            style["color"] = props["color"]
        if props.get("opacity") is not None:
            style["opacity"] = props["opacity"]
        resolved.append(style)
    return resolved


def _build_axes_entries(
    origin: Any,
    directions: List[tuple[Any, tuple[float, float], str | None]],
    styles: List[Dict[str, Any]],
    major_interval: float,
) -> List[Dict[str, Any]]:
    """Expand direction extents into axis-half dicts with per-direction styles."""
    axes: List[Dict[str, Any]] = []
    for (direction, extent, label), style in zip(directions, styles):
        lo, hi = extent
        if hi != 0.0:
            axes.append(
                _axis_entry(
                    origin,
                    _scale_dir(origin, direction, hi),
                    label,
                    1.0,
                    style,
                    major_interval,
                )
            )
        if lo != 0.0:
            axes.append(
                _axis_entry(
                    origin,
                    _scale_dir(origin, direction, lo),
                    None,
                    -1.0,
                    style,
                    major_interval,
                )
            )
    return axes


def _axis_entry(
    origin: Any,
    end: Any,
    label: str | None,
    value_step: float,
    style: Dict[str, Any],
    major_interval: float,
) -> Dict[str, Any]:
    """Build a single axis-half dict with a flat color/opacity for the shared renderer."""
    label_at_major = style.get("label_at_major", True)
    entry: Dict[str, Any] = {
        "start": list(origin),
        "end": list(end),
        "majorInterval": major_interval,
        "labelAtMajor": label_at_major,
        "labelFormat": ".1f",
        "valueStep": value_step,
        "style": style,
    }
    if style.get("color") is not None:
        entry["color"] = style["color"]
    if style.get("opacity") is not None:
        entry["opacity"] = style["opacity"]
    if label is not None:
        entry["label"] = label
    return entry


def _serialize_grid(
    ent: Grid,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {"line_thickness": 0.02},
        styles_map=styles_map,
    ) | {
        "origin": list(ent.origin),
        "dir_u": list(ent.dir_u),
        "dir_v": list(ent.dir_v),
        "range_u": list(ent.range_u),
        "range_v": list(ent.range_v),
        "interval_u": ent.interval_u,
        "interval_v": ent.interval_v,
    }


def _serialize_point(
    ent: Point,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {"size": 0.08},
        styles_map=styles_map,
    ) | {"position": [ent.x, ent.y, ent.z]}


def _serialize_direction(
    ent: Direction,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {
            "length": 2.0,
            "origin": [0.0, 0.0, 0.0],
        },
        styles_map=styles_map,
    ) | {"vector": [ent.x, ent.y, ent.z]}


def _serialize_hpoint(
    ent: HPoint,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {"size": 0.08},
        styles_map=styles_map,
    ) | {
        "position": [ent.point.x, ent.point.y, ent.point.z],
        "weight": ent.weight,
    }


def _serialize_point_pair(
    ent: PointPair,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    effective_kind = "ImagPointPair" if ent.is_imaginary else "PointPair"
    result = _apply_defaults(
        props,
        effective_kind,
        {"lineThickness": 0.02, "pointSize": 0.06},
        styles_map=styles_map,
    )
    result["kind"] = "PointPair"  # frontend dispatch uses base kind
    result.update(
        {
            "pointA": [ent.point_a.x, ent.point_a.y, ent.point_a.z],
            "pointB": [ent.point_b.x, ent.point_b.y, ent.point_b.z],
            "isImaginary": ent.is_imaginary,
        }
    )
    return result


def resolve_line_length(
    line: Line,
    *,
    styles_map: Dict[str, Any] | None = None,
    props: Dict[str, Any] | None = None,
) -> float:
    """Return the effective rendered length of a Line.

    Finite lines use their explicit ``length``; infinite lines (``length`` is
    ``None``) fall back to a per-call ``style`` override, then the canonical
    ``LineStyle.length`` default.  Matches the frontend ``resolveLength()``.
    """
    if line.length is not None and line.length > 0:
        return float(line.length)

    props = props or {}
    style = props.get("style")
    if style is not None:
        override = getattr(style, "length", None)
        if override is not None and override > 0:
            return float(override)

    if styles_map is not None:
        from ._styles import _style_for_kind

        canonical = _style_for_kind("Line", styles_map=styles_map)
        length = getattr(canonical, "length", None)
        if length is not None:
            return float(length)

    return 20.0


def _serialize_line(
    ent: Line,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    builtins = {"thickness": 1.0}
    # Resolve the length here so the frontend always receives a valid value
    # (infinite lines use the canonical `LineStyle.length` default).
    props["length"] = resolve_line_length(ent, styles_map=styles_map, props=props)
    return _apply_defaults(
        props,
        kind,
        builtins,
        styles_map=styles_map,
    ) | {
        "origin": [ent.origin.x, ent.origin.y, ent.origin.z],
        "direction": [ent.direction.x, ent.direction.y, ent.direction.z],
    }


def _serialize_plane(
    ent: Plane,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    builtins: dict[str, Any] = {"extent": 10.0}
    if ent.extent is not None:
        props["extent"] = ent.extent
    result = _apply_defaults(props, kind, builtins, styles_map=styles_map) | {
        "point": [ent.point.x, ent.point.y, ent.point.z],
        "normal": [ent.normal.x, ent.normal.y, ent.normal.z],
    }
    if ent.span_u is not None and ent.span_v is not None:
        result["span_u"] = [ent.span_u.x, ent.span_u.y, ent.span_u.z]
        result["span_v"] = [ent.span_v.x, ent.span_v.y, ent.span_v.z]
    return result


def _serialize_circle(
    ent: Circle,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    effective_kind = "ImagCircle" if ent.is_imaginary else "Circle"
    result = _apply_defaults(
        props,
        effective_kind,
        {"tubeRadius": 0.03},
        styles_map=styles_map,
    )
    result["kind"] = "Circle"  # frontend dispatch uses base kind
    result.update(
        {
            "center": [ent.center.x, ent.center.y, ent.center.z],
            "normal": [ent.normal.x, ent.normal.y, ent.normal.z],
            "radius": _clamp_positive(ent.radius),
            "isImaginary": ent.is_imaginary,
        }
    )
    return result


def _serialize_sphere(
    ent: Sphere,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    effective_kind = "ImagSphere" if ent.is_imaginary else "Sphere"
    result = _apply_defaults(
        props,
        effective_kind,
        {},
        styles_map=styles_map,
    )
    result["kind"] = "Sphere"  # frontend dispatch uses base kind
    result.update(
        {
            "center": [ent.center.x, ent.center.y, ent.center.z],
            "radius": _clamp_positive(ent.radius),
            "isImaginary": ent.is_imaginary,
        }
    )
    return result


def _serialize_space(
    ent: Space,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {"extent": 10.0},
        styles_map=styles_map,
    ) | {"scale": ent.scale}


# ── Operators ──────────────────────────────────────────────


def _serialize_reflection_line(
    ent: ReflectionLine,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {"length": 5.0, "thickness": 0.04},
        styles_map=styles_map,
    ) | {
        "direction": [ent.line.direction.x, ent.line.direction.y, ent.line.direction.z],
        "origin": [ent.line.origin.x, ent.line.origin.y, ent.line.origin.z],
    }


def _serialize_reflection_plane(
    ent: ReflectionPlane,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {"extent": 5.0},
        styles_map=styles_map,
    ) | {
        "normal": [ent.plane.normal.x, ent.plane.normal.y, ent.plane.normal.z],
        "origin": [ent.plane.point.x, ent.plane.point.y, ent.plane.point.z],
    }


def _serialize_reflection_origin(
    ent: ReflectionPoint,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {"extent": 1.0},
        styles_map=styles_map,
    ) | {
        "origin": [0.0, 0.0, 0.0],
    }


def _serialize_inversion(
    ent: Inversion,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {},
        styles_map=styles_map,
    ) | {
        "center": [ent.center.x, ent.center.y, ent.center.z],
        "radius": ent.radius,
    }


def _serialize_rotor(
    ent: Rotor,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {"discRadius": 1.5},
        styles_map=styles_map,
    ) | {
        "angle": ent.angle,
        "axis": [ent.axis.x, ent.axis.y, ent.axis.z],
        "origin": [0.0, 0.0, 0.0],
    }


def _serialize_translator(
    ent: Translator,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {"length": 3.0},
        styles_map=styles_map,
    ) | {
        "vector": [ent.vector.x, ent.vector.y, ent.vector.z],
        "origin": [0.0, 0.0, 0.0],
    }


def _serialize_dilator(
    ent: Dilator,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {"ringCount": 4, "maxRadius": 3.0},
        styles_map=styles_map,
    ) | {
        "factor": ent.factor,
        "origin": [ent.origin.x, ent.origin.y, ent.origin.z],
    }


def _serialize_motor(
    ent: Motor,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {},
        styles_map=styles_map,
    ) | {
        "rotor": {
            "angle": ent.rotor.angle,
            "axis": [ent.rotor.axis.x, ent.rotor.axis.y, ent.rotor.axis.z],
        },
        "translator": {
            "vector": [
                ent.translator.vector.x,
                ent.translator.vector.y,
                ent.translator.vector.z,
            ],
        },
        "origin": [0.0, 0.0, 0.0],
    }


def _serialize_general_rotor(
    ent: GeneralRotor,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {},
        styles_map=styles_map,
    ) | {
        "angle": ent.angle,
        "axis": [ent.axis.x, ent.axis.y, ent.axis.z],
        "origin": [ent.origin.x, ent.origin.y, ent.origin.z],
    }
