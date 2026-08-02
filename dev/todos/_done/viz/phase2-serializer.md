# Phase 2: Entity → JSON Serializer

**File:** `py/pytanga/viz/serializer.py`

**Goal:** Convert `pytanga.geometry` entity dataclasses into JSON-compatible Python dicts
suitable for transmission over WebSocket. The serializer is a pure function with no
dependencies on the server, network, or Three.js.

**Prerequisites:** Phase 1 (needs `SceneEntity` and entity types from `pytanga.geometry`)

---

## 1. Design

### 1.1 Serialization Format

Each entity type maps to a flat JSON dict with a `kind` discriminator:

```json
{
  "id": "abc12345",
  "kind": "Point",
  "color": "#ff4444",
  "opacity": 1.0,
  "size": 0.1,
  "position": [1.0, 2.0, 3.0]
}
```

Key design decisions:
- **Flat structure:** No nested `geometry`/`material` sub-objects. The JS renderer
  consumes a flat dict for simplicity. Geometry coordinates are separate from
  rendering properties but at the same level.
- **Arrays for vectors:** All 3D vectors are serialized as `[x, y, z]` arrays
  (compact, fast to parse in JS, no key overhead per component).
- **All fields present:** Every entity dict includes all possible fields for its
  kind, even if default-valued. This avoids `undefined` checks on the JS side.
  Exception: during frame streaming (Phase 6), only changed fields are sent.

### 1.2 Serializer API

```python
# py/pytanga/viz/serializer.py

from __future__ import annotations
from typing import Any, Dict, List

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
    Entity,
)


def serialize_entity(
    entity: Entity,
    entity_id: str,
    properties: Dict[str, Any] | None = None,
    *,
    defaults: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Convert a geometry entity + optional render properties into a JSON-ready dict.

    Args:
        entity: A pytanga.geometry Entity instance.
        entity_id: The scene-assigned ID string.
        properties: Per-entity rendering properties (color, opacity, etc.).
                    Override individual values. If None, global defaults are used.
        defaults: Global default rendering properties from Visualizer._defaults.
                  If None, built-in defaults are used.

    Returns:
        A flat dict suitable for json.dumps() and transmission over WebSocket.
    """
    props = dict(properties) if properties else {}
    defs = dict(defaults) if defaults else {}
    result: Dict[str, Any] = {"id": entity_id}
    result: Dict[str, Any] = {"id": entity_id}

    # Dispatch by type
    if isinstance(entity, Point):
        result.update(_serialize_point(entity, props))
    elif isinstance(entity, Direction):
        result.update(_serialize_direction(entity, props))
    elif isinstance(entity, HPoint):
        result.update(_serialize_homogeneous_point(entity, props))
    elif isinstance(entity, PointPair):
        result.update(_serialize_point_pair(entity, props))
    elif isinstance(entity, Line):
        result.update(_serialize_line(entity, props))
    elif isinstance(entity, Plane):
        result.update(_serialize_plane(entity, props))
    elif isinstance(entity, Circle):
        result.update(_serialize_circle(entity, props))
    elif isinstance(entity, Sphere):
        result.update(_serialize_sphere(entity, props))
    elif isinstance(entity, Space):
        result.update(_serialize_space(entity, props))
    else:
        raise TypeError(f"Unknown entity type: {type(entity).__name__}")

    return result


def serialize_scene_update(
    entities: List[Dict[str, Any]],
    removed: List[str],
) -> Dict[str, Any]:
    """Wrap entity list + removed list into the top-level WebSocket message format."""
    return {
        "type": "scene_update",
        "entities": entities,
        "removed": removed,
    }
```

### 1.3 Per-Entity Serializers

```python
def _apply_render_defaults(
    props: Dict[str, Any],
    kind: str,
    builtin_defaults: Dict[str, Any],
    *,
    global_defaults: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Merge render property defaults, ensuring all expected keys exist.

    Priority: per-entity props > global_defaults > builtin_defaults.
    """
    result = {"kind": kind}
    gd = dict(global_defaults) if global_defaults else {}
    for key, default in builtin_defaults.items():
        # Check global defaults first, then builtin
        global_key = _global_default_key(kind, key)
        resolved = gd.get(global_key, default)
        result[key] = props.get(key, resolved)
    return result


def _global_default_key(kind: str, property_name: str) -> str:
    """Map a builtin property key to the Visualizer._defaults key if applicable.

    e.g. ("point", "color") → "color_point"
         ("line", "length") → "line_length"
    """
    # Color is the main cross-cutting property
    if property_name == "color":
        return f"color_{kind.lower()}"
    # Extent properties map by entity category
    if kind.lower() in ("line", "direction"):
        if property_name == "length":
            return "line_length"
        if property_name == "thickness":
            return "line_thickness"
    if kind.lower() == "plane":
        if property_name == "extent":
            return "plane_extent"
    if kind.lower() == "space":
        if property_name == "extent":
            return "space_extent_render"
    # No global mapping — use the builtin default
    return ""


def _serialize_point(entity: Point, props: Dict[str, Any]) -> Dict[str, Any]:
    result = _apply_render_defaults(props, "Point", {
        "color": "#ff4444",
        "opacity": 1.0,
        "size": 0.08,
    })
    result["position"] = [entity.x, entity.y, entity.z]
    return result


def _serialize_direction(entity: Direction, props: Dict[str, Any]) -> Dict[str, Any]:
    result = _apply_render_defaults(props, "Direction", {
        "color": "#ffffff",
        "opacity": 0.9,
        "length": 2.0,
        "origin": [0.0, 0.0, 0.0],  # default: direction arrow starts at origin
    })
    result["vector"] = [entity.x, entity.y, entity.z]
    return result


def _serialize_homogeneous_point(
    entity: HPoint, props: Dict[str, Any]
) -> Dict[str, Any]:
    result = _apply_render_defaults(props, "HPoint", {
        "color": "#ff8844",
        "opacity": 1.0,
        "size": 0.08,
    })
    result["position"] = [entity.point.x, entity.point.y, entity.point.z]
    result["weight"] = entity.weight
    return result


def _serialize_point_pair(
    entity: PointPair, props: Dict[str, Any]
) -> Dict[str, Any]:
    result = _apply_render_defaults(props, "PointPair", {
        "color": "#44ff44",
        "opacity": 1.0,
        "lineThickness": 0.02,
        "pointSize": 0.06,
    })
    result["pointA"] = [entity.point_a.x, entity.point_a.y, entity.point_a.z]
    result["pointB"] = [entity.point_b.x, entity.point_b.y, entity.point_b.z]
    return result


def _serialize_line(entity: Line, props: Dict[str, Any]) -> Dict[str, Any]:
    result = _apply_render_defaults(props, "Line", {
        "color": "#44ff44",
        "opacity": 0.8,
        "thickness": 0.03,
        "length": 20.0,     # rendered length (GA lines are infinite)
    })
    result["origin"] = [entity.origin.x, entity.origin.y, entity.origin.z]
    result["direction"] = [entity.direction.x, entity.direction.y, entity.direction.z]
    return result


def _serialize_plane(entity: Plane, props: Dict[str, Any]) -> Dict[str, Any]:
    result = _apply_render_defaults(props, "Plane", {
        "color": "#4488ff",
        "opacity": 0.3,
        "extent": 10.0,      # half-extent of the rendered quad
    })
    result["point"] = [entity.point.x, entity.point.y, entity.point.z]
    result["normal"] = [entity.normal.x, entity.normal.y, entity.normal.z]
    return result


def _serialize_circle(entity: Circle, props: Dict[str, Any]) -> Dict[str, Any]:
    result = _apply_render_defaults(props, "Circle", {
        "color": "#ff44ff",
        "opacity": 0.7,
        "tubeRadius": 0.03,
    })
    result["center"] = [entity.center.x, entity.center.y, entity.center.z]
    result["normal"] = [entity.normal.x, entity.normal.y, entity.normal.z]
    result["radius"] = max(entity.radius, 0.001)  # avoid zero-radius torus
    return result


def _serialize_sphere(entity: Sphere, props: Dict[str, Any]) -> Dict[str, Any]:
    result = _apply_render_defaults(props, "Sphere", {
        "color": "#ffaa00",
        "opacity": 0.4,
        "wireframe": True,
    })
    result["center"] = [entity.center.x, entity.center.y, entity.center.z]
    result["radius"] = max(entity.radius, 0.001)
    return result


def _serialize_space(entity: Space, props: Dict[str, Any]) -> Dict[str, Any]:
    result = _apply_render_defaults(props, "Space", {
        "color": "#888888",
        "opacity": 0.1,
        "extent": 10.0,
    })
    result["scale"] = entity.scale
    return result
```

### 1.4 Default Render Properties by Entity Kind

| Kind | Default Color | Default Opacity | Special Defaults |
|------|---------------|-----------------|------------------|
| Point | `#ff4444` (red) | 1.0 | `size: 0.08` |
| Direction | `#ffffff` (white) | 0.9 | `length: 2.0`, `origin: [0,0,0]` |
| HPoint | `#ff8844` (orange) | 1.0 | `size: 0.08`, `weight: 1.0` |
| PointPair | `#44ff44` (green) | 1.0 | `lineThickness: 0.02`, `pointSize: 0.06` |
| Line | `#44ff44` (green) | 0.8 | `thickness: 0.03`, `length: 20.0` |
| Plane | `#4488ff` (blue) | 0.3 | `extent: 10.0` |
| Circle | `#ff44ff` (magenta) | 0.7 | `tubeRadius: 0.03` |
| Sphere | `#ffaa00` (amber) | 0.4 | `wireframe: true` |
| Space | `#888888` (grey) | 0.1 | `extent: 10.0`, `scale: 1.0` |

---

## 2. Design Decisions

1. **All serializers are pure functions.** No class, no state, no side effects.
   Input: entity + properties dict. Output: JSON-ready dict.

2. **Explicit dispatch via `isinstance`.** No metaprogramming or `getattr` magic.
   Easy to read, easy to debug, easy to extend with new entity types.

3. **Defaults defined per-kind in code**, not in a config file. This keeps the
   serializer self-contained and the default values are trivial constants.

4. **Scalar clamping:** `radius` and similar values are clamped to `0.001` minimum
   to prevent degenerate Three.js geometries (zero-radius spheres/tori crash the
   renderer or produce NaN vertices).

5. **No circular references, no custom types.** Every dict is directly `json.dumps`-able.
   No custom JSONEncoder needed.

---

## 3. Implementation Steps

1. Create `py/pytanga/viz/serializer.py`.
2. Implement `_apply_render_defaults()` helper.
3. Implement each `_serialize_*()` function.
4. Implement `serialize_entity()` dispatcher.
5. Implement `serialize_scene_update()` wrapper.
6. Write unit tests:
   - Serialize each entity kind with default properties → verify output dict structure.
   - Serialize with custom properties → verify overrides are respected.
   - Verify all output dicts are `json.dumps()` compatible.
   - Verify radius clamping for Circle and Sphere with zero/negative values.
   - Verify `serialize_scene_update()` produces the correct top-level message format.

## 4. Verification Checklist

### Entity Serialization
- [x] All 9 entity types produce correct `kind` field.
- [x] All vector fields (position, origin, direction, normal, center, etc.) are `[x, y, z]` lists.
- [x] Zero/negative radius values are clamped to 0.001.

### Default Properties
- [x] Default render properties are applied when not provided.
- [x] Custom render properties override defaults.

### Operator Serialization
- [x] All 8 operator types serialize to correct JSON.

### JSON Compatibility
- [x] All output dicts serialize to JSON without errors.
- [ ] `serialize_scene_update()` wraps entities + removed in `{"type": "scene_update", ...}` format.
- [ ] No imports from `pytanga.algebra`, `pytanga.MV`, `pytanga.basis`, `aiohttp`.

### Geo-fix status
- [ ] ❌ Still imports `Reflection` (deprecated alias) — needs Phase 4a sync (S6-S11)
- [x] Already imports `HPoint` (post-rename)
- [ ] ❌ `_serialize_point_pair()` does not pass `isImaginary` field (S3)
- [ ] ❌ `_serialize_circle()` does not pass `isImaginary` field (S4)
- [ ] ❌ `_serialize_sphere()` does not pass `isImaginary` field (S5)
- [ ] ❌ `_serialize_inversion()` uses hardcoded `sphereRadius` instead of `ent.radius` (S9)
- [ ] ❌ Missing `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin`, `Reflector` serializers (S6-S8, S10)

### Dependencies
- [x] No imports from `pytanga.algebra`, `pytanga.MV`, `pytanga.basis`, `aiohttp`.
