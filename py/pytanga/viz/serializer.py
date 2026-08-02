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
    result: Dict[str, Any] = {"id": entity_id, "layer": "scene"}

    if kind is None:
        kind = type(entity).__name__

    # ── Entities ──
    if isinstance(entity, Point):
        result.update(_serialize_point(entity, props, kind=kind, styles_map=styles_map))
    elif isinstance(entity, Direction):
        result.update(
            _serialize_direction(entity, props, kind=kind, styles_map=styles_map)
        )
    elif isinstance(entity, HPoint):
        result.update(
            _serialize_hpoint(entity, props, kind=kind, styles_map=styles_map)
        )
    elif isinstance(entity, PointPair):
        result.update(
            _serialize_point_pair(entity, props, kind=kind, styles_map=styles_map)
        )
    elif isinstance(entity, Line):
        result.update(_serialize_line(entity, props, kind=kind, styles_map=styles_map))
    elif isinstance(entity, Plane):
        result.update(_serialize_plane(entity, props, kind=kind, styles_map=styles_map))
    elif isinstance(entity, Circle):
        result.update(
            _serialize_circle(entity, props, kind=kind, styles_map=styles_map)
        )
    elif isinstance(entity, Sphere):
        result.update(
            _serialize_sphere(entity, props, kind=kind, styles_map=styles_map)
        )
    elif isinstance(entity, Space):
        result.update(_serialize_space(entity, props, kind=kind, styles_map=styles_map))

    # ── Operators ──
    elif isinstance(entity, ReflectionLine):
        result.update(
            _serialize_reflection_line(entity, props, kind=kind, styles_map=styles_map)
        )
    elif isinstance(entity, ReflectionPlane):
        result.update(
            _serialize_reflection_plane(entity, props, kind=kind, styles_map=styles_map)
        )
    elif isinstance(entity, ReflectionOrigin):
        result.update(
            _serialize_reflection_origin(
                entity, props, kind=kind, styles_map=styles_map
            )
        )
    elif isinstance(entity, Inversion):
        result.update(
            _serialize_inversion(entity, props, kind=kind, styles_map=styles_map)
        )
    elif isinstance(entity, Rotor):
        result.update(_serialize_rotor(entity, props, kind=kind, styles_map=styles_map))
    elif isinstance(entity, Translator):
        result.update(
            _serialize_translator(entity, props, kind=kind, styles_map=styles_map)
        )
    elif isinstance(entity, Dilator):
        result.update(
            _serialize_dilator(entity, props, kind=kind, styles_map=styles_map)
        )
    elif isinstance(entity, Motor):
        result.update(_serialize_motor(entity, props, kind=kind, styles_map=styles_map))
    elif isinstance(entity, GeneralRotor):
        result.update(
            _serialize_general_rotor(entity, props, kind=kind, styles_map=styles_map)
        )
    elif isinstance(entity, GeneralDilator):
        result.update(
            _serialize_general_dilator(entity, props, kind=kind, styles_map=styles_map)
        )

    else:
        raise TypeError(f"Unknown entity type: {kind}")

    return result


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


def _serialize_label(label: Any, label_id: str) -> dict[str, Any]:
    """Serialize a :class:`~pytanga.viz._label.Label` to a JSON-ready dict.

    The ``position`` is already the parent-relative anchor computed from
    ``compute_label_position()``.  ``offset_local`` is NOT sent to the
    frontend — it was already applied when computing ``position``.
    """
    from ._styles import LabelStyle

    style = label.style if label.style is not None else LabelStyle()
    style_dict = style.to_dict()

    # offset_local is NOT included in the wire format
    style_dict.pop("offset_local", None)

    return {
        "id": label_id,
        "layer": "overlay",
        "kind": "label",
        "text": label.text,
        "position": list(label.position),
        "parentId": label.parent_id,
        "style": style_dict,
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


def _serialize_line(
    ent: Line,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return _apply_defaults(
        props,
        kind,
        {"thickness": 0.03, "length": 20.0},
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
    return _apply_defaults(
        props,
        kind,
        {"extent": 10.0},
        styles_map=styles_map,
    ) | {
        "point": [ent.point.x, ent.point.y, ent.point.z],
        "normal": [ent.normal.x, ent.normal.y, ent.normal.z],
    }


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
        "direction": [ent.direction.x, ent.direction.y, ent.direction.z],
        "origin": [0.0, 0.0, 0.0],
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
        "normal": [ent.normal.x, ent.normal.y, ent.normal.z],
        "origin": [0.0, 0.0, 0.0],
    }


def _serialize_reflection_origin(
    ent: ReflectionOrigin,
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
        "origin": [0.0, 0.0, 0.0],
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


def _serialize_general_dilator(
    ent: GeneralDilator,
    props: Dict[str, Any],
    *,
    kind: str,
    styles_map: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    result = _apply_defaults(
        props,
        kind,
        {"ringCount": 4, "maxRadius": 3.0},
        styles_map=styles_map,
    )
    result.update(
        {
            "factor": ent.factor,
            "origin": [0.0, 0.0, 0.0],
        }
    )
    if ent.translator is not None:
        result["translator"] = {
            "vector": [
                ent.translator.vector.x,
                ent.translator.vector.y,
                ent.translator.vector.z,
            ],
        }
    return result
