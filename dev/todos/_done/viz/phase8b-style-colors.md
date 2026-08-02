# Phase 8b — Colors & Opacity in Style Classes

**Prerequisites:** Phase 8 (integration), Phase 4c (style hierarchy), Phase 5 (entity renderers)

**Goal:** Move all default color and opacity values into the style dataclasses, remove
the `Visualizer._defaults` dict and `ObjVizProps` entirely, support 4-tuple
`(r, g, b, a)` color inputs, rename style classes to concise `*Style` names
(e.g. `PointStyle`), and establish them as the base class for future extended
styles (e.g. `CrossHairPointStyle(PointStyle)`). Eliminate hardcoded opacity in
JS renderers.

**Status:** ❌ Not started

---

## 1. Motivation

### 1.1 Current Problems

1. **Default colors live in three places:** The `Visualizer._defaults` dict holds
   per-kind color keys, the `serializer.py` builtin dicts hold the same colors,
   and the style class instances carry no color or opacity at all.

2. **Default opacities are scattered:** Most serializer builtin dicts include
   `"opacity"`, but `sphere.js` hardcodes `ent.opacity ?? 0.4` — the sphere
   serializer builtin has no opacity key.

3. **`_normalize_color()` discards alpha.** 4-tuples lose their 4th component.

4. **`ObjVizProps` is reducing to a thin wrapper** around `color`, `opacity`, and
   `style`. After Phase 4c moved entity-specific params into style classes, only
   three fields remain — and Phase 8b moves `color` and `opacity` into style
   classes as well, leaving only `style`.

5. **Extent defaults are duplicated** between `_defaults` and style classes, with
   `_global_key()` doing fragile string-based mappings.

6. **Verbose style class names.** `DefaultPointStyle`, `DefaultSphereStyle`, etc.
   are unnecessarily long. Future extended styles (crosshair point, dashed line)
   should derive from a concise base: `CrossHairPointStyle(PointStyle)`.

### 1.2 Design Goals

1. **One source of truth:** The fully-initialized style instances in
   `_DEFAULT_STYLE_FOR_KIND` are the only place where default rendering
   parameters are defined.

2. **`Visualizer._defaults` is removed** entirely.

3. **`ObjVizProps` is removed** entirely. `add()` takes `color`, `opacity`, and
   `style` as direct keyword arguments.

4. **User-supplied styles use `None` defaults.** All fields on every style class
   default to `None`. A user passes only the fields they want to override:

   ```python
   viz.add(entity, style=SphereStyle(wireframe=False))
   ```

5. **Merge happens Python-side.** The serializer fills `None` fields from the
   fully-initialized canonical default. The JS side always receives a complete
   style dict — no merge logic needed on the frontend.

6. **4-tuple color support:** `(r, g, b, a)` sets both color (RGB → hex) and
   opacity (alpha from the 4th component).

7. **Concise `*Style` class names** that serve as the base class for future
   extended styles. For example, `PointStyle` is the base; a hypothetical
   `CrossHairPointStyle` would inherit from it:

   ```python
   class CrossHairPointStyle(PointStyle):
       arm_length: float | None = None
       arm_thickness: float | None = None
   ```

---

## 2. Style Class Hierarchy

### 2.1 Class Renames & Inheritance Design

Every style class is renamed from `Default*Style` to `*Style`. The style classes
are **not abstract** — they are the default styles AND the base classes for
future extended styles.

| Old Name | New Name |
|---|---|
| `DefaultPointStyle` | `PointStyle` |
| `DefaultDirectionStyle` | `DirectionStyle` |
| `DefaultHPointStyle` | `HPointStyle` |
| `DefaultPointPairStyle` | `PointPairStyle` |
| `DefaultLineStyle` | `LineStyle` |
| `DefaultPlaneStyle` | `PlaneStyle` |
| `DefaultCircleStyle` | `CircleStyle` |
| `DefaultSphereStyle` | `SphereStyle` |
| `DefaultSpaceStyle` | `SpaceStyle` |
| `DefaultReflectionLineStyle` | `ReflectionLineStyle` |
| `DefaultReflectionPlaneStyle` | `ReflectionPlaneStyle` |
| `DefaultReflectionOriginStyle` | `ReflectionOriginStyle` |
| `DefaultInversionStyle` | `InversionStyle` |
| `DefaultRotorStyle` | `RotorStyle` |
| `DefaultTranslatorStyle` | `TranslatorStyle` |
| `DefaultDilatorStyle` | `DilatorStyle` |
| `DefaultMotorStyle` | `MotorStyle` |
| `DefaultGeneralRotorStyle` | `GeneralRotorStyle` |
| `DefaultGeneralDilatorStyle` | `GeneralDilatorStyle` |

The `style_type` string in `to_dict()` and in the JS frontend remains the
**Python class name** (e.g. `"PointStyle"`, `"SphereStyle"`). Future extended
styles would emit their own name (e.g. `"CrossHairPointStyle"`), which the
frontend can dispatch on. If the frontend doesn't know about an extended style,
it falls back to rendering as the base style (since extended styles carry all
base fields plus their own).

### 2.2 All Fields Default to `None`

Every `*Style` dataclass uses `None` as the default for every field:

```python
@dataclass
class PointStyle(VizStyle):
    """Visual style for Point.  Serves as the base class for future
    extended point styles (e.g. ``CrossHairPointStyle``).

    All fields default to ``None`` — the Visualizer fills missing values
    from its canonical defaults in ``_DEFAULT_STYLE_FOR_KIND``.
    """

    color: str | None = None
    opacity: float | None = None
    size: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "PointStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.size is not None:
            result["size"] = self.size
        return result
```

Same for all 19 style classes. Each `to_dict()` only includes non-`None` values.
The `style_type` string matches the class name — concise and self-documenting.

### 2.3 Canonical Defaults in `_DEFAULT_STYLE_FOR_KIND`

The module-level dict stores **fully-initialized** instances (all fields
explicitly set, no `None` values):

```python
_DEFAULT_STYLE_FOR_KIND: dict[str, VizStyle] = {
    "Point":      PointStyle(color="#ff4444", opacity=1.0, size=0.08),
    "Direction":  DirectionStyle(color="#ffffff", opacity=0.9, length=2.0),
    "HPoint":     HPointStyle(color="#ff8844", opacity=1.0, size=0.08),
    "PointPair":  PointPairStyle(color="#44ff44", opacity=1.0, point_size=0.06, line_thickness=0.02),
    "Line":       LineStyle(color="#44ff44", opacity=0.8, length=20.0, thickness=0.03),
    "Plane":      PlaneStyle(color="#4488ff", opacity=0.3, extent=10.0),
    "Circle":     CircleStyle(color="#ff44ff", opacity=0.7, tube_radius=0.03),
    "Sphere":     SphereStyle(color="#ffaa00", opacity=0.4, wireframe=True, wireframe_resolution=12),
    "Space":      SpaceStyle(color="#888888", opacity=0.1, extent=10.0),
    # Operators
    "ReflectionLine":   ReflectionLineStyle(color="#aaccff", opacity=0.6, length=5.0, thickness=0.04),
    "ReflectionPlane":  ReflectionPlaneStyle(color="#88ccff", opacity=0.35, extent=5.0),
    "ReflectionOrigin": ReflectionOriginStyle(color="#ffffff", opacity=0.5, extent=1.0),
    "Inversion":        InversionStyle(color="#cc88ff", opacity=0.4),
    "Rotor":            RotorStyle(color="#ff8844", opacity=0.7, disc_radius=1.5),
    "Translator":       TranslatorStyle(color="#44aaff", opacity=0.9, length=3.0),
    "Dilator":          DilatorStyle(color="#ffcc44", opacity=0.6, ring_count=4, max_radius=3.0),
    "Motor":            MotorStyle(color="#ff66cc", opacity=0.7),
    "GeneralRotor":     GeneralRotorStyle(color="#ff9966", opacity=0.6),
    "GeneralDilator":   GeneralDilatorStyle(color="#ffcc88", opacity=0.6, ring_count=4, max_radius=3.0),
}
```

When a user mutates `viz.default_styles[Point].color = "#00ff00"`, they mutate the
canonical instance in this dict. All future serializations pick up the change.

### 2.4 Merge Logic in `_style_to_output()`

When a user passes a sparse style (some fields `None`), the serializer fills the
gaps from the canonical default:

```python
def _style_to_output(
    style: VizStyle | dict[str, Any] | None,
    kind: str,
    styles_map: dict[str, VizStyle] | None = None,
) -> dict[str, Any]:
    """Resolve a (possibly partial) style to a complete dict.

    1. If ``style is None`` → return the canonical default's ``to_dict()``.
    2. If ``style`` is a ``VizStyle`` instance → merge its non-None fields
       with the canonical default, then serialize.
    3. If ``style`` is already a dict → return it as-is.
    """
    canonical = _style_for_kind(kind, styles_map=styles_map)

    if style is None:
        return canonical.to_dict() if hasattr(canonical, "to_dict") else {}

    if isinstance(style, VizStyle):
        user_dict = style.to_dict()
        canonical_dict = canonical.to_dict() if hasattr(canonical, "to_dict") else {}
        # Start with canonical, overlay user's non-None values
        merged = dict(canonical_dict)
        for k, v in user_dict.items():
            if v is not None:
                merged[k] = v
        return merged

    if isinstance(style, dict):
        return style

    return {}
```

This means the JS side always receives a **complete** style dict — no merge
logic needed in JavaScript. `styleParam(ent, 'wireframe', true)` will always
find `ent.style.wireframe`.

### 2.5 Extended Style Example: `CrossHairPointStyle`

This phase **implements** `CrossHairPointStyle` as a concrete example of how
styles and renderers are extended. It serves as the reference pattern for all
future extended styles.

#### 2.5.1 Python Style Class

```python
@dataclass
class CrossHairPointStyle(PointStyle):
    """Extended point style — renders a 3D crosshair instead of a sphere.

    Inherits ``color``, ``opacity``, and ``size`` from ``PointStyle``.
    ``size`` controls the overall scale of the crosshair (length of each arm).
    """

    arm_thickness: float | None = None  # thickness of each arm; default = size * 0.15

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()  # includes color, opacity, size from PointStyle
        result["style_type"] = "CrossHairPointStyle"
        if self.arm_thickness is not None:
            result["arm_thickness"] = self.arm_thickness
        return result
```

#### 2.5.2 JS Renderer: `crosshair_point.js`

```js
// py/pytanga/viz/templates/renderers/crosshair_point.js
import * as THREE from 'three';
import { makeMaterial, styleParam, parseColor, tagEntity } from './utils.js';

export function createCrossHairPoint(ent) {
    const color = parseColor(ent, '#ff4444');
    const opacity = styleParam(ent, 'opacity', 1.0);
    const size = styleParam(ent, 'size', 0.3);
    const armThickness = styleParam(ent, 'arm_thickness', size * 0.15);
    const pos = ent.position || [0, 0, 0];

    const group = new THREE.Group();
    const material = makeMaterial(color, opacity);

    // Three orthogonal arms (X, Y, Z)
    const directions = [
        [1, 0, 0], [0, 1, 0], [0, 0, 1],
    ];

    for (const [dx, dy, dz] of directions) {
        // Cylinder centered at origin, extending ±size along direction
        const cylGeo = new THREE.CylinderGeometry(armThickness, armThickness, size * 2, 6, 1);
        const cyl = new THREE.Mesh(cylGeo, material);

        // Orient cylinder along direction
        const dir = new THREE.Vector3(dx, dy, dz).normalize();
        const quat = new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 1, 0), dir
        );
        cyl.setRotationFromQuaternion(quat);

        group.add(cyl);
    }

    group.position.set(pos[0], pos[1], pos[2]);
    tagEntity(group, ent);
    return group;
}
```

#### 2.5.3 Factory Dispatch

The `factory.js` dispatcher already dispatches on `ent.kind`. The crosshair is
not a new entity kind — it's a new **style** for the existing `Point` / `HPoint`
kind. The dispatch inside `createPoint()` therefore checks `style_type`:

```js
// In factory.js — updated createEntityMesh():

case 'Point':
case 'HPoint':
    if (ent.style?.style_type === 'CrossHairPointStyle') {
        mesh = createCrossHairPoint(ent);
    } else {
        mesh = createPoint(ent);  // default sphere
    }
    break;
```

And the import at the top of `factory.js`:

```js
import { createCrossHairPoint } from './crosshair_point.js';
```

#### 2.5.4 Usage

```python
from pytanga.viz import Visualizer, CrossHairPointStyle
from pytanga.geometry import Point

viz = Visualizer()

# Crosshair using defaults (color/opacity from canonical PointStyle, size=0.3)
viz.add(Point(1, 2, 3), style=CrossHairPointStyle())

# Crosshair with overrides
viz.add(Point(5, 0, 0), style=CrossHairPointStyle(
    color="#00ff00", opacity=0.8, size=0.5, arm_thickness=0.05
))

# Per-call color/opacity override still works (takes precedence over style)
viz.add(Point(0, 5, 0), color="#ff0", style=CrossHairPointStyle(size=0.3))
```

#### 2.5.5 Canonical Default for Crosshair

The `CrossHairPointStyle` does NOT get its own entry in
`_DEFAULT_STYLE_FOR_KIND` — that dict maps entity *kinds* to styles, and
crosshair is not an entity kind. Instead, when the user specifies
`style=CrossHairPointStyle()` with `None` fields, the merge logic in
`_style_to_output()` fills missing fields (like `color` and `opacity`)
from the canonical `PointStyle` instance (since `CrossHairPointStyle` is
an `isinstance` of `PointStyle` and the serializer resolves styles by kind).

The `_style_to_output()` merge treats inherited styles correctly: if the
user's style is a subclass of the canonical kind's style, the merge still
works because the canonical style's `to_dict()` provides the base fields,
and the user's `to_dict()` overrides with non-`None` values.

---

## 3. `ObjVizProps` — Removed

### 3.1 New `add()` Signature

```python
def add(
    self,
    obj: VizInputType | None = None,
    *,
    entity_id: str | None = None,
    opns: bool | None = None,
    # ── Convenience overrides (override style defaults) ──
    color: str | tuple[float, float, float] | tuple[float, float, float, float] | None = None,
    opacity: float | None = None,
    style: ObjVizStyle | None = None,
    # ── Label shortcut ──
    label: str | None = None,
    label_style: LabelStyle | None = None,
) -> str | list[str]:
```

`color` and `opacity` are normalized/handled directly in `add()` before being
passed to `Scene.add()` as properties. No intermediate dataclass.

### 3.2 `_normalize_color()` — Returns Hex or `(hex, opacity)`

Moved to `_props.py` (kept there since `_props.py` becomes a utility module
for color handling rather than a dataclass definition):

```python
def _normalize_color(
    color: str | tuple[float, float, float] | tuple[float, float, float, float],
) -> str | tuple[str, float]:
    """Convert a color value to hex, extracting opacity from 4-tuples.

    Returns:
        - Hex string for str input or RGB 3-tuples.
        - ``(hex_str, opacity)`` for RGBA 4-tuples.
    """
    if isinstance(color, str):
        return color
    if isinstance(color, tuple):
        if len(color) == 3:
            r, g, b = color
            a = None
        elif len(color) == 4:
            r, g, b, a = color
        else:
            raise ValueError(f"Color tuple must have 3 or 4 elements, got {len(color)}")
        r_byte = max(0, min(255, round(r * 255)))
        g_byte = max(0, min(255, round(g * 255)))
        b_byte = max(0, min(255, round(b * 255)))
        hex_str = f"#{r_byte:02x}{g_byte:02x}{b_byte:02x}"
        if a is not None:
            return (hex_str, a)
        return hex_str
    raise TypeError(f"Color must be str or tuple, got {type(color).__name__}")
```

### 3.3 Color/Opacity Handling in `add()`

```python
def add(self, obj, *, color=None, opacity=None, style=None, label=None, label_style=None, ...):
    from ._label import Label, get_label_anchor

    if isinstance(obj, Label):
        return self._scene.add_label(obj)

    if opns is None:
        opns = self._opns

    # Build properties dict from explicit kwargs
    properties: dict[str, Any] = {}

    if color is not None:
        normalized = _normalize_color(color)
        if isinstance(normalized, tuple):
            properties["color"] = normalized[0]
            # Only set opacity from 4-tuple if not explicitly provided
            if opacity is None:
                properties["opacity"] = normalized[1]
        else:
            properties["color"] = normalized

    if opacity is not None:
        properties["opacity"] = float(opacity)

    if style is not None:
        properties["style"] = style  # VizStyle instance — merged in serializer

    entity = self._resolve(obj, opns=opns)
    ...
    eid = self._scene.add(entity, entity_id=entity_id, **properties)
    ...
```

### 3.4 Priority Chain

For color:

```
add(color=...)              → explicit per-call override
  ↓ if not provided
User style.color            → from style=PointStyle(color="#00ff00")
  ↓ if None in user style
Canonical default's .color  → from _DEFAULT_STYLE_FOR_KIND["Point"].color
```

For opacity:

```
add(opacity=...)            → explicit per-call override
  ↓ if not provided
4-tuple alpha from color    → extracted by _normalize_color()
  ↓ if not a 4-tuple
User style.opacity          → from style=PointStyle(opacity=0.5)
  ↓ if None in user style
Canonical default's .opacity → from _DEFAULT_STYLE_FOR_KIND["Point"].opacity
```

---

## 4. Serializer Changes

### 4.1 `_apply_defaults()` — Color/Opacity from Style, Not Builtins

```python
def _apply_defaults(
    props: dict[str, Any],
    kind: str,
    builtin: dict[str, Any],          # no longer contains "color" / "opacity"
    *,
    styles_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from ._styles import _style_for_kind, _style_to_output

    result: dict[str, Any] = {"kind": kind}

    # Entity-specific params (size, length, extent, …) from builtin dict
    for key, default_value in builtin.items():
        result[key] = props.get(key, default_value)

    # Pass through extra props not in builtin or handled explicitly
    for key, value in props.items():
        if key not in result and key not in ("style",):
            result[key] = value

    # ── Color ──
    # Already resolved by add() and present in props if user set it.
    # If not in props, the style merge below fills it from canonical default.
    resolved_style = _style_for_kind(kind, styles_map=styles_map)
    if "color" not in props and hasattr(resolved_style, "color"):
        result["color"] = resolved_style.color

    # ── Opacity ──
    if "opacity" not in props and hasattr(resolved_style, "opacity"):
        result["opacity"] = resolved_style.opacity

    # ── Style object (merged: user overrides + canonical defaults) ──
    result["style"] = _style_to_output(props.get("style"), kind, styles_map=styles_map)

    return result
```

Note: `color` and `opacity` are **also** present in the merged `style` dict
(via `_style_to_output()`), so the JS side can read them from `ent.style.color`
/ `ent.style.opacity`. They remain at the top level as well for backward
compat with existing JS renderers that use `ent.color` / `ent.opacity`.

### 4.2 `_global_key()` Is Removed

No longer needed — `_defaults` dict is gone, so there is nothing to map.

### 4.3 Individual Serializers — Remove `color`/`opacity` from Builtin Dicts

**Before:**
```python
def _serialize_point(ent, props, *, kind, defaults, styles_map):
    return _apply_defaults(props, kind, {
        "color": "#ff4444",
        "opacity": 1.0,
        "size": 0.08,
    }, defaults=defaults, styles_map=styles_map) | {"position": [...]}
```

**After:**
```python
def _serialize_point(ent, props, *, kind, styles_map):
    return _apply_defaults(props, kind, {
        "size": 0.08,
    }, styles_map=styles_map) | {"position": [...]}
```

The `defaults` parameter is dropped entirely from all serializer signatures.
Same change for all 19 `_serialize_*()` functions.

### 4.4 `serialize_entity()` — `defaults` Parameter Removed

```python
def serialize_entity(
    entity,
    entity_id,
    properties=None,
    *,
    kind=None,
    styles_map=None,
) -> dict[str, Any]:
```

---

## 5. `Visualizer` Changes

### 5.1 `_defaults` Dict — Removed

```python
class Visualizer:
    def __init__(self, ...):
        ...
        self._default_styles = _make_default_styles()
        # _defaults dict: GONE
```

### 5.2 API Surface Changes

| Old | Fate |
|---|---|
| `defaults` (property) | **Removed.** |
| `set_defaults(**kwargs)` | **Removed.** |
| `set_default_color(kind, color)` | **Kept.** Re-routed to `self._default_styles[_kind_to_key(kind)].color = hex`. Extracts alpha from 4-tuples. |
| `set_default_extent(...)` | **Removed.** Use `viz.default_styles[Line].length = 30.0`. |
| `ObjVizProps` import | **Removed** from `__init__.py` exports. |

### 5.3 `set_default_color()` with 4-Tuple Support

```python
def set_default_color(self, kind: str, color: str | tuple) -> None:
    """Set the default color (and optionally opacity) for an entity kind."""
    from ._props import _normalize_color

    normalized = _normalize_color(color)
    key = _kind_to_key(kind)  # "point" → "Point", "reflection_line" → "ReflectionLine"
    if key not in self._default_styles:
        raise ValueError(f"Unknown entity kind: {kind!r}")

    if isinstance(normalized, tuple):
        self._default_styles[key].color = normalized[0]
        self._default_styles[key].opacity = normalized[1]
    else:
        self._default_styles[key].color = normalized
```

### 5.4 `flush()` / `export()` — Stop Passing `defaults`

All call sites that pass `defaults=self._defaults` are updated:

```python
# Before:
entities = self._scene.full_state(defaults=self._defaults, styles_map=self._default_styles)

# After:
entities = self._scene.full_state(styles_map=self._default_styles)
```

### 5.5 `Scene` — `defaults` Parameter Removed

```python
class Scene:
    def flush(self, *, styles_map=None) -> tuple[list[dict], list[str]]:
        ...

    def full_state(self, *, styles_map=None) -> list[dict]:
        ...

def _serialize_object(obj, *, styles_map=None) -> dict:
    from .serializer import serialize_entity, _serialize_label
    if obj.layer == "overlay":
        ...
    return serialize_entity(obj.data, obj.id, obj.properties, kind=obj.kind, styles_map=styles_map)
```

---

## 6. `_props.py` — Reduced to Utility Module

After removing `ObjVizProps`, `_props.py` retains only `_normalize_color()`.
It no longer defines any dataclass.

```python
# py/pytanga/viz/_props.py
"""Color normalisation utility for the Tanga 3D viewer."""

def _normalize_color(color):
    ...
```

---

## 7. `_style_dict.py` & `ObjVizStyle` — Name Changes

The `_StyleDict` helper and the `ObjVizStyle` type alias update their
references from `Default*Style` to `*Style` names.

The `_DEFAULT_STYLE_FOR_KIND` dict and `_make_default_styles()` use the new
names.

---

## 8. JS Renderer Changes

### 8.1 All Renderers Use `styleParam` for Opacity

Currently several renderers read `ent.opacity ?? <hardcoded>`. These are
updated to read from the style dict:

```js
// Before:
const opacity = ent.opacity ?? 0.4;

// After:
const opacity = styleParam(ent, 'opacity', 0.4);
```

After Phase 8b, the style dict always contains `opacity` (merged Python-side),
so `styleParam` will always find it. The fallback only triggers if the dict is
malformed.

Files to update:
- `sphere.js`: `ent.opacity ?? 0.4` → `styleParam(ent, 'opacity', 0.4)`
- `point.js`: `ent.opacity ?? 1.0` → `styleParam(ent, 'opacity', 1.0)`
- `direction.js`: `ent.opacity ?? 0.9` → `styleParam(ent, 'opacity', 0.9)`
- `line.js`: `ent.opacity ?? 0.8` → `styleParam(ent, 'opacity', 0.8)`
- `plane.js`: `ent.opacity ?? 0.3` → `styleParam(ent, 'opacity', 0.3)`
- `circle.js`: `ent.opacity ?? 0.7` → `styleParam(ent, 'opacity', 0.7)`
- `space.js`: `ent.opacity ?? 0.15` → `styleParam(ent, 'opacity', 0.15)`
- All operator JS modules: same pattern.

### 8.2 JS Dispatches on `style_type`

The `style_type` string in the JSON style dict changes from e.g.
`"DefaultSphereStyle"` to `"SphereStyle"`. The `factory.js` and per-entity
renderers that check `ent.style.style_type` must be updated accordingly.

### 8.3 Color Already in Style Dict

`styleParam(ent, 'color', '#ffffff')` also works for color resolution, though
current JS renderers read `ent.color` directly (which is still present at the
top level). This is fine — both paths work.

---

## 9. Files to Modify

| File | Changes |
|---|---|
| `py/pytanga/viz/_styles.py` | Rename all 19 `Default*Style` → `*Style` classes; all fields default to `None`; `to_dict()` omits `None`, uses new `style_type` name; `_DEFAULT_STYLE_FOR_KIND` uses new class names with fully-initialized instances; `_style_to_output()` merges user style with canonical default; `ObjVizStyle` union type updates |
| `py/pytanga/viz/_props.py` | Remove `ObjVizProps` dataclass; keep `_normalize_color()` with 4-tuple support |
| `py/pytanga/viz/_style_dict.py` | Update `_make_default_styles()` to use new class names |
| `py/pytanga/viz/serializer.py` | Remove `color`/`opacity` from all builtin dicts; `_apply_defaults()` reads from resolved style; remove `_global_key()`; remove `defaults` parameter everywhere |
| `py/pytanga/viz/scene.py` | Remove `defaults` parameter from `flush()`, `full_state()`, `_serialize_object()` |
| `py/pytanga/viz/visualizer.py` | Remove `_defaults` dict, `defaults` property, `set_defaults()`, `set_default_extent()`, `_normalize_color` staticmethod; re-route `set_default_color()`; add `color`/`opacity`/`style` kwargs to `add()`; update all `Default*Style` references to `*Style` |
| `py/pytanga/viz/__init__.py` | Remove `ObjVizProps` from exports; rename all exported style classes |
| `py/pytanga/viz/templates/renderers/sphere.js` | `ent.opacity` → `styleParam(ent, 'opacity', ...)`; update `style_type` string |
| `py/pytanga/viz/templates/renderers/point.js` | same |
| `py/pytanga/viz/templates/renderers/direction.js` | same |
| `py/pytanga/viz/templates/renderers/line.js` | same |
| `py/pytanga/viz/templates/renderers/plane.js` | same |
| `py/pytanga/viz/templates/renderers/circle.js` | same |
| `py/pytanga/viz/templates/renderers/space.js` | same |
| `py/pytanga/viz/templates/renderers/operators/*.js` | same (all operator modules) |
| `py/pytanga/viz/templates/renderers/factory.js` | Update `style_type` dispatch strings |
| `py/pytanga/viz/templates/renderers/utils.js` | `styleParam()` unchanged |
| `py/pytanga/viz/export/_html.py` | Update `style_type` strings in bootstrap adapter |
| `py/tests/viz/test_phase1_session_scene.py` | Remove tests referencing `_defaults` dict, `ObjVizProps`; update `Default*Style` → `*Style` imports |
| `py/tests/viz/test_phase2_serializer.py` | Update tests for new serializer signatures; update style class references |
| `py/tests/viz/` (all test files) | Replace `ObjVizProps(...)` → `add(..., color=..., opacity=..., style=...)`; update all `Default*Style` → `*Style` |
| `dev/src/test_viz_smoke.py` | Replace `ObjVizProps(...)` → direct kwargs; update style class names |
| `dev/src/test_viz_play.py` | Replace `ObjVizProps(...)` → direct kwargs; update style class names |

---

## 10. Implementation Checklist

### 10.1 `_styles.py` — Rename Classes, `None` Defaults, `_DEFAULT_STYLE_FOR_KIND`, Merge Logic

- [ ] **S1:** Rename all 19 `Default*Style` classes to `*Style` (e.g. `DefaultPointStyle` → `PointStyle`)
- [ ] **S2:** Update each `to_dict()` to emit the new `style_type` string (matching the class name)
- [ ] **S3:** Change all fields on all 19 `*Style` classes to default to `None`
- [ ] **S4:** Update each `to_dict()` to omit `None` values
- [ ] **S5:** Populate `_DEFAULT_STYLE_FOR_KIND` with fully-initialized instances using new class names
- [ ] **S6:** Implement merge logic in `_style_to_output()`: start with canonical `to_dict()`, overlay user's non-None values
- [ ] **S7:** Update `ObjVizStyle` union type to use new class names

### 10.2 `_props.py` — Remove `ObjVizProps`, 4-Tuple in `_normalize_color`

- [ ] **P1:** Remove `ObjVizProps` dataclass entirely
- [ ] **P2:** `_normalize_color()` returns `(hex, opacity)` for 4-tuples, `hex` for 3-tuples/strings
- [ ] **P3:** File becomes a single-function utility module

### 10.3 `_style_dict.py` — Update Class References

- [ ] **D1:** Update `_make_default_styles()` to import and use new `*Style` class names

### 10.4 `serializer.py` — Clean Up Builtins, Remove `defaults` / `_global_key`

- [ ] **Z1:** Remove `"color"` and `"opacity"` from all 19 `_serialize_*()` builtin dicts
- [ ] **Z2:** `_apply_defaults()` resolves `color`/`opacity` from `_style_for_kind()` when not in `props`
- [ ] **Z3:** Remove `_global_key()` function
- [ ] **Z4:** Remove `defaults` parameter from `_apply_defaults()` and all 19 `_serialize_*()` signatures
- [ ] **Z5:** Remove `defaults` parameter from `serialize_entity()` signature
- [ ] **Z6:** Verify all 19 entity/operator kinds serialize with correct colors (from canonical styles)

### 10.5 `visualizer.py` — Remove `_defaults` and `ObjVizProps`, Update `add()`

- [ ] **V1:** Remove `self._defaults` dict from `__init__`
- [ ] **V2:** Remove `defaults` property
- [ ] **V3:** Remove `set_defaults()` method
- [ ] **V4:** Re-route `set_default_color(kind, color)` to `self._default_styles[key].color` + `.opacity` (for 4-tuples)
- [ ] **V5:** Remove `set_default_extent()` method
- [ ] **V6:** Remove `_normalize_color = staticmethod(...)` line (moved to `_props.py`)
- [ ] **V7:** Add `color`, `opacity`, `style` keyword arguments to `add()`; normalize color in `add()` body
- [ ] **V8:** Remove `ObjVizProps` import and usage from `add()`
- [ ] **V9:** Update `_flush_async()` — stop passing `defaults`
- [ ] **V10:** Update `export_html()` — stop passing `defaults`, use new serializer signatures
- [ ] **V11:** Update `export_glb()` — same
- [ ] **V12:** Update `start()` and `run()` lambdas — stop passing `defaults`
- [ ] **V13:** Update `_props.py` import to only import `_normalize_color`
- [ ] **V14:** Update all `Default*Style` → `*Style` references in docstrings and comments

### 10.6 CrossHairPointStyle — Extended Style & Renderer

- [ ] **X1:** Add `CrossHairPointStyle(PointStyle)` class to `_styles.py` (inherits `color`, `opacity`, `size`; adds `arm_thickness`)
- [ ] **X2:** Update `ObjVizStyle` union type to include `CrossHairPointStyle`
- [ ] **X3:** Create `py/pytanga/viz/templates/renderers/crosshair_point.js` — renders three orthogonal cylinders at the entity position
- [ ] **X4:** Add `createCrossHairPoint` import and dispatch to `factory.js` (under `Point`/`HPoint` case, gated on `style_type === 'CrossHairPointStyle'`)
- [ ] **X5:** Export `CrossHairPointStyle` from `__init__.py`
- [ ] **X6:** Verify merge: `add(point, style=CrossHairPointStyle())` inherits `color`/`opacity` from `_DEFAULT_STYLE_FOR_KIND["Point"]`
- [ ] **X7:** Manual test: crosshair renders in browser at the correct position
- [ ] **X8:** Manual test: crosshair with explicit `color`, `opacity`, `size` overrides
- [ ] **X9:** Manual test: crosshair with per-call `add(..., color=...)` takes precedence over style color

### 10.7 `scene.py` — Remove `defaults` Parameter

- [ ] **C1:** `flush()`: remove `defaults` parameter
- [ ] **C2:** `full_state()`: remove `defaults` parameter
- [ ] **C3:** `_serialize_object()`: remove `defaults` parameter

### 10.8 `__init__.py`

- [ ] **I1:** Remove `ObjVizProps` from imports and `__all__`
- [ ] **I2:** Rename all exported style class names (`DefaultPointStyle` → `PointStyle`, etc.)
- [ ] **I3:** Export `CrossHairPointStyle`
- [ ] **I4:** Update `ObjVizStyle` export if present

### 10.9 JS Renderers — Opacity via `styleParam`, Update `style_type` Strings

- [ ] **J1:** `sphere.js`: `ent.opacity ?? 0.4` → `styleParam(ent, 'opacity', 0.4)`
- [ ] **J2:** `point.js`: `ent.opacity ?? 1.0` → `styleParam(ent, 'opacity', 1.0)`
- [ ] **J3:** `direction.js`: `ent.opacity ?? 0.9` → `styleParam(ent, 'opacity', 0.9)`
- [ ] **J4:** `line.js`: `ent.opacity ?? 0.8` → `styleParam(ent, 'opacity', 0.8)`
- [ ] **J5:** `plane.js`: `ent.opacity ?? 0.3` → `styleParam(ent, 'opacity', 0.3)`
- [ ] **J6:** `circle.js`: `ent.opacity ?? 0.7` → `styleParam(ent, 'opacity', 0.7)`
- [ ] **J7:** `space.js`: `ent.opacity ?? 0.15` → `styleParam(ent, 'opacity', 0.15)`
- [ ] **J8:** All operator JS modules (`rotor.js`, `translator.js`, …): same pattern
- [ ] **J9:** Update `style_type` strings in all JS modules (`"DefaultSphereStyle"` → `"SphereStyle"`, etc.)
- [ ] **J10:** `factory.js`: update `style_type` strings if dispatch uses them
- [ ] **J11:** `_html.py` export bootstrap: update `style_type` strings
- [ ] **J12:** `styleParam(ent, key, fallback)` already in `utils.js` — no changes needed

### 10.10 Tests — Update All Call Sites

- [ ] **T1:** Remove `ObjVizProps` imports from all test files
- [ ] **T2:** Replace `ObjVizProps(color=..., opacity=...)` with `viz.add(..., color=..., opacity=...)`
- [ ] **T3:** Replace `ObjVizProps(style=...)` with `viz.add(..., style=...)`
- [ ] **T4:** Replace `ObjVizProps()` with `viz.add(...)` (no extra args)
- [ ] **T5:** Remove tests that specifically test `ObjVizProps` dataclass
- [ ] **T6:** Remove tests referencing `Visualizer._defaults` / `.defaults` / `set_defaults()`
- [ ] **T7:** Update all `Default*Style` references to `*Style` in all test files
- [ ] **T8:** Test `PointStyle().size is None` (all fields `None` by default)
- [ ] **T9:** Test `_DEFAULT_STYLE_FOR_KIND["Sphere"].opacity == 0.4` (canonical instance is fully populated)
- [ ] **T10:** Test `_DEFAULT_STYLE_FOR_KIND` keys map to correct new class instances
- [ ] **T11:** Test `_normalize_color((1.0, 0, 0, 0.5))` returns `("#ff0000", 0.5)`
- [ ] **T12:** Test `add(point, color=(1,0,0,0.5))` produces JSON with `color: "#ff0000"`, `opacity: 0.5`
- [ ] **T13:** Test `add(point, color=(1,0,0,0.5), opacity=0.8)` — explicit `opacity` wins
- [ ] **T14:** Test `add(sphere)` produces style dict with `style_type: "SphereStyle"`, `opacity: 0.4`, `wireframe: True` (from canonical default)
- [ ] **T15:** Test `add(sphere, style=SphereStyle(wireframe=False))` — style dict has `style_type: "SphereStyle"`, `wireframe: False` but `opacity: 0.4` (merged from canonical)
- [ ] **T16:** Test `set_default_color("point", "#00ff00")` mutates canonical style and affects next serialized point
- [ ] **T17:** Test `set_default_color("point", (1,0,0,0.3))` sets both `.color = "#ff0000"` and `.opacity = 0.3`
- [ ] **T18:** All existing tests updated and passing

### 10.11 Smoke / Manual Verification

- [ ] **M1:** `dev/src/test_viz_smoke.py` — all entity types render with correct colors
- [ ] **M2:** Spheres render with opacity 0.4 and wireframe (unchanged visual)
- [ ] **M3:** `viz.add(Point(1,2,3), color=(1,0,0,0.5))` — red point at 50% opacity
- [ ] **M4:** `viz.set_default_color("sphere", "#0000ff")` — next sphere is blue
- [ ] **M5:** `viz.default_styles[Sphere].opacity = 0.9` — next sphere nearly opaque
- [ ] **M6:** `viz.add(sphere, style=SphereStyle(wireframe=False))` — solid sphere, no wireframe, but retains canonical color and opacity
- [ ] **M7:** Labels still render (no regression)
- [ ] **M8:** `export_html()` produces correct colors in self-contained file
- [ ] **M9:** `export_glb()` produces correct glTF material colors
- [ ] **M10:** Browser console has no errors
- [ ] **M11:** Verify JSON style dicts contain new `style_type` strings (e.g. `"SphereStyle"`, not `"DefaultSphereStyle"`)

---

## 11. Summary of New API

### 11.1 Adding Entities

```python
from pytanga.viz import PointStyle, SphereStyle

# Use all defaults
viz.add(Point(1, 2, 3))

# Override color
viz.add(Point(1, 2, 3), color="#00ff00")

# Override color with RGBA tuple (4th = opacity)
viz.add(Point(1, 2, 3), color=(0.0, 1.0, 0.0, 0.5))  # green, 50% opacity

# Override opacity
viz.add(Point(1, 2, 3), opacity=0.3)

# Override specific style fields (rest from canonical defaults)
viz.add(Sphere(Point(0,0,0), 2), style=SphereStyle(wireframe=False, wireframe_resolution=24))

# Combine
viz.add(Point(1, 2, 3), color="#ff0", opacity=0.8, style=PointStyle(size=0.2))
```

### 11.2 Configuring Defaults

```python
from pytanga.geometry import Sphere, Line, Point

# Per-kind color (str or 4-tuple for color+opacity)
viz.set_default_color("sphere", "#0000ff")
viz.set_default_color("point", (1.0, 0.0, 0.0, 0.5))  # red + 50% opacity

# Direct mutation of canonical style instances
viz.default_styles[Sphere].opacity = 0.9
viz.default_styles[Sphere].wireframe = False
viz.default_styles[Line].length = 30.0
viz.default_styles[Line].thickness = 0.05
```

### 11.3 Extended Styles (Implemented: `CrossHairPointStyle`)

```python
from pytanga.viz import Visualizer, CrossHairPointStyle
from pytanga.geometry import Point

viz = Visualizer()

# Crosshair with defaults (color/opacity from canonical PointStyle)
viz.add(Point(1, 2, 3), style=CrossHairPointStyle())

# Crosshair with explicit overrides
viz.add(Point(5, 0, 0), style=CrossHairPointStyle(
    color="#00ff00", opacity=0.8, size=0.5, arm_thickness=0.05
))
```

---

## 12. Relationship to Other Phases

| Phase | Impact |
|---|---|
| **4c** | Style classes are the foundation — renamed, fields change to `None` defaults |
| **4d** | Labels unchanged |
| **5/6** | JS renderers updated: opacity via `styleParam()`, `style_type` strings updated |
| **8** | `_defaults` removal touches server, flush, export paths |
| **8a** | Unified overlay — no conflict |
| **10** | Example scripts: `ObjVizProps(...)` → `add(..., color=..., style=...)`; `Default*Style` → `*Style` |
| **11** | Export adapters: stop passing `defaults`, use new serializer signatures, update `style_type` strings |

---

## 13. Verification Checklist

- [ ] All 19 style classes renamed from `Default*Style` to `*Style`
- [ ] All 19 style classes have `None` defaults for every field
- [ ] `to_dict()` emits concise `style_type` strings (e.g. `"SphereStyle"`)
- [ ] `_DEFAULT_STYLE_FOR_KIND` has fully-initialized instances using new class names
- [ ] `_style_to_output()` merges user's non-None values with canonical defaults
- [ ] JS side always receives a complete style dict (all fields present)
- [ ] `ObjVizProps` class is removed
- [ ] `_normalize_color((r,g,b,a))` returns `(hex, alpha)`
- [ ] `add()` accepts `color`, `opacity`, `style` as direct kwargs
- [ ] `Visualizer._defaults` dict is removed
- [ ] `Visualizer.defaults` property is removed
- [ ] `Visualizer.set_defaults()` method is removed
- [ ] `Visualizer.set_default_extent()` is removed
- [ ] `set_default_color()` still works (re-routed to style instances, handles 4-tuples)
- [ ] `_global_key()` is removed from serializer
- [ ] `defaults` parameter removed from all serializer/scene signatures
- [ ] All JS renderers read opacity via `styleParam(ent, 'opacity', <fallback>)`
- [ ] JS dispatch uses new `style_type` strings
- [ ] Sphere renders with opacity from canonical style (not hardcoded)
- [ ] All existing tests pass
- [ ] No circular imports
- [ ] Browser console has no errors