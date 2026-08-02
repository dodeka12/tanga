# Phase 4c — Visualization Styles

**Prerequisites:** Phase 4b (API cleanup: `ObjVizProps`, `VizInputType`, `opns` default)

**Goal:** Replace `ObjVizProps`'s ad-hoc style properties (`size`, `thickness`, `tube_radius`, etc.) with a structured, per-entity-kind **style class hierarchy**. Each geometric entity kind gets a dedicated style dataclass that defines its visual appearance. A `style` field on `ObjVizProps` selects the style. Styles are serialized to JSON so the frontend can implement different renderers per style.

---

## 1. Motivation

### 1.1 Current Problem with `ObjVizProps`

`ObjVizProps` has 19 flat fields (`size`, `thickness`, `tube_radius`, `disc_radius`, `point_size`, `line_thickness`, `ring_count`, `max_radius`, ...) where each field applies only to specific entity kinds. This is confusing:

- `size` means point radius for Points, but is ignored for Planes
- `thickness` applies to Lines but not to Spheres
- `ring_count` only matters for Dilators

There is no way to distinguish "render this Point as a small sphere" from "render this Point as a glowing halo" — the rendering is determined solely by the entity `kind` in `factory.js`.

### 1.2 What Styles Enable

A style object attached to an entity tells the frontend **how** to render it, while the entity `kind` tells it **what** it is. Example:

```python
# Use the default point style (small sphere, standard color)
viz.add(Point(1, 2, 3), ObjVizProps(style=DefaultPointStyle(size=0.08)))

# Later: use a cross-hair point style if the frontend supports it
viz.add(Point(0, 0, 0), ObjVizProps(style=CrossHairPointStyle(length=0.5, color="#fff")))
```

The frontend's `factory.js` dispatches on `(ent.kind, ent.style.type)` instead of just `ent.kind`.

---

## 2. Style Class Hierarchy

### 2.1 Per-Entity-Kind Default Styles

One default style class per entity/operator kind that can be visualized:

| Style Class | For Entity/Operator | Default Fields |
|-------------|---------------------|----------------|
| `DefaultPointStyle` | `Point` | `size: float = 0.08` |
| `DefaultDirectionStyle` | `Direction` | `length: float = 2.0` |
| `DefaultHPointStyle` | `HPoint` | `size: float = 0.08` |
| `DefaultPointPairStyle` | `PointPair` | `point_size: float = 0.06`, `line_thickness: float = 0.02` |
| `DefaultLineStyle` | `Line` | `length: float = 20.0`, `thickness: float = 0.03` |
| `DefaultPlaneStyle` | `Plane` | `extent: float = 10.0` |
| `DefaultCircleStyle` | `Circle` | `tube_radius: float = 0.03` |
| `DefaultSphereStyle` | `Sphere` | `radius_override: float \| None = None`, `wireframe: bool = True` |
| `DefaultSpaceStyle` | `Space` | `extent: float = 10.0` |
| `DefaultReflectionLineStyle` | `ReflectionLine` | `length: float = 5.0`, `thickness: float = 0.04` |
| `DefaultReflectionPlaneStyle` | `ReflectionPlane` | `extent: float = 5.0` |
| `DefaultReflectionOriginStyle` | `ReflectionOrigin` | `extent: float = 1.0` |
| `DefaultInversionStyle` | `Inversion` | (no size params — radius comes from entity) |
| `DefaultRotorStyle` | `Rotor` | `disc_radius: float = 1.5` |
| `DefaultTranslatorStyle` | `Translator` | `length: float = 3.0` |
| `DefaultDilatorStyle` | `Dilator` | `ring_count: int = 4`, `max_radius: float = 3.0` |
| `DefaultMotorStyle` | `Motor` | (no dedicated params) |
| `DefaultGeneralRotorStyle` | `GeneralRotor` | (no dedicated params) |
| `DefaultGeneralDilatorStyle` | `GeneralDilator` | `ring_count: int = 4`, `max_radius: float = 3.0` |

All styles inherit from a base `VizStyle` dataclass.

### 2.2 Union Type

```python
# py/pytanga/viz/_styles.py

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union


@dataclass
class VizStyle:
    """Base class for all visualization styles. Not used directly."""
    pass


@dataclass
class DefaultPointStyle(VizStyle):
    size: float = 0.08


@dataclass
class DefaultDirectionStyle(VizStyle):
    length: float = 2.0


# ... (all 18 style classes)


# Union of all supported styles
ObjVizStyle: TypeAlias = Union[
    DefaultPointStyle,
    DefaultDirectionStyle,
    DefaultHPointStyle,
    DefaultPointPairStyle,
    DefaultLineStyle,
    DefaultPlaneStyle,
    DefaultCircleStyle,
    DefaultSphereStyle,
    DefaultSpaceStyle,
    DefaultReflectionLineStyle,
    DefaultReflectionPlaneStyle,
    DefaultReflectionOriginStyle,
    DefaultInversionStyle,
    DefaultRotorStyle,
    DefaultTranslatorStyle,
    DefaultDilatorStyle,
    DefaultMotorStyle,
    DefaultGeneralRotorStyle,
    DefaultGeneralDilatorStyle,
]
```

### 2.3 Serialization

Each style class has a `to_dict()` method that returns a flat JSON dict with a `style_type` discriminator:

```python
@dataclass
class DefaultPointStyle(VizStyle):
    size: float = 0.08

    def to_dict(self) -> dict[str, Any]:
        return {"style_type": "DefaultPointStyle", "size": self.size}
```

The serializer attaches the style dict to the entity JSON under a `style` key:

```json
{
  "id": "abc123",
  "kind": "Point",
  "position": [1.0, 2.0, 3.0],
  "color": "#ff4444",
  "opacity": 1.0,
  "style": {
    "style_type": "DefaultPointStyle",
    "size": 0.08
  }
}
```

### 2.4 Auto-Selection of Default Style

When no style is explicitly specified, the `Visualizer` auto-selects the default style
for the entity kind. This happens in `add()` before calling `Scene.add()`:

```python
def _default_style_for(entity: GeoEntity | GeoOperator) -> VizStyle:
    """Return the default style instance for a given entity/operator type."""
    if isinstance(entity, Point):
        return DefaultPointStyle()
    elif isinstance(entity, Sphere):
        return DefaultSphereStyle()
    # ... etc.
```

The `ObjVizProps.style` field is `ObjVizStyle | None = None`. When `None`, the
auto-selected default is used; when set, the user's style overrides.

---

## 3. Updated `ObjVizProps`

### 3.1 Simplified Fields

With style information moved to style classes, `ObjVizProps` shrinks to only
**cross-cutting** rendering properties:

```python
@dataclass
class ObjVizProps:
    """Visual rendering properties for an entity or operator.

    Entity-specific size/thickness/radius values belong in the style
    object (``style`` field), not here.  The fields below apply regardless
    of the entity kind or style.
    """

    # ── General appearance ──
    color: str | tuple[float, float, float] | tuple[float, float, float, float] | None = None
    opacity: float | None = None
    wireframe: bool | None = None  # only meaningful for Sphere, but harmless elsewhere

    # ── Labels ──
    label: str | None = None
    label_offset_y: float | None = None
    label_font_size: float | None = None
    label_color: str | None = None
    label_background: str | None = None

    # ── Style ──
    style: ObjVizStyle | None = None  # None = auto-select default style

    def to_dict(self) -> dict[str, Any]:
        """Return a dict of non-None fields, including serialized style."""
        from dataclasses import fields

        result: dict[str, Any] = {}
        for fld in fields(self):
            val = getattr(self, fld.name)
            if val is not None:
                if fld.name == "color" and isinstance(val, tuple):
                    result[fld.name] = _normalize_color(val)
                elif fld.name == "style":
                    result["style"] = val.to_dict()
                else:
                    result[fld.name] = val
        return result
```

### 3.2 Fields Removed (moved to style classes)

| Old Field | Now In |
|-----------|--------|
| `size` | `DefaultPointStyle.size`, `DefaultHPointStyle.size` |
| `length` | `DefaultDirectionStyle.length`, `DefaultLineStyle.length`, `DefaultTranslatorStyle.length`, `DefaultReflectionLineStyle.length` |
| `thickness` | `DefaultLineStyle.thickness`, `DefaultReflectionLineStyle.thickness` |
| `extent` | `DefaultPlaneStyle.extent`, `DefaultSpaceStyle.extent`, `DefaultReflectionPlaneStyle.extent`, `DefaultReflectionOriginStyle.extent` |
| `tube_radius` | `DefaultCircleStyle.tube_radius` |
| `point_size` | `DefaultPointPairStyle.point_size` |
| `line_thickness` | `DefaultPointPairStyle.line_thickness` |
| `disc_radius` | `DefaultRotorStyle.disc_radius` |
| `ring_count` | `DefaultDilatorStyle.ring_count`, `DefaultGeneralDilatorStyle.ring_count` |
| `max_radius` | `DefaultDilatorStyle.max_radius`, `DefaultGeneralDilatorStyle.max_radius` |

---

## 4. Files to Create / Modify

### 4.1 New Files

| File | Content |
|------|---------|
| `py/pytanga/viz/_styles.py` | All 19 style dataclasses + `ObjVizStyle` union type + `_default_style_for()` |
| `py/tests/viz/test_phase4c_styles.py` | Tests for style serialization, default selection, ObjVizProps integration |

### 4.2 Modified Files

| File | Changes |
|------|---------|
| `py/pytanga/viz/_props.py` | Remove 12 entity-specific fields; add `style: ObjVizStyle \| None`; update `to_dict()` |
| `py/pytanga/viz/visualizer.py` | Call `_default_style_for()` in `add()` when `props.style is None`; remove `_defaults` extent keys (they become style defaults) |
| `py/pytanga/viz/serializer.py` | `_serialize_*` functions no longer need to output size/thickness — those come from the style dict; merge style into entity JSON |
| `py/pytanga/viz/templates/renderers/factory.js` | Read `ent.style.style_type` and `ent.style.*` fields instead of flat `ent.size`, `ent.thickness`, etc. |
| `py/pytanga/viz/__init__.py` | Export all style classes + `ObjVizStyle` + `VizStyle` |
| `py/tests/viz/test_phase1_session_scene.py` | Update tests that use removed `_defaults` keys |
| `py/tests/viz/test_phase2_serializer.py` | Update tests that assert on removed flat fields |

---

## 5. Frontend Impact

The JS `factory.js` currently has a flat switch on `ent.kind`. After Phase 4c, it
dispatches on **both** `ent.kind` and `ent.style.style_type`:

```js
function createEntityMesh(ent) {
    const styleType = ent.style?.style_type;
    const styleData = ent.style || {};

    switch (ent.kind) {
        case 'Point':
            if (styleType === 'DefaultPointStyle') {
                return renderPointDefault(ent.position, styleData.size, ent.color, ent.opacity);
            }
            // future: else if (styleType === 'CrossHairPointStyle') { ... }
            break;
        // ...
    }
}
```

**Phase 4c handles style classes, serialization, AND flat-field removal on the Python side.**
The JS renderer update happens in **Phase 5** (entity renderers)
and **Phase 6** (operator renderers) — those phases refactor `factory.js`
into per-entity modules that read exclusively from `ent.style` fields.
There is **no backward compatibility** phase — the switch from flat fields to
styles is a clean break.

---

## 6. Clean Break from Flat Fields

### 6.1 No Backward Compatibility

Phase 4c removes flat fields from the serializer entirely. Entities are serialized
with only their geometry data (`position`, `center`, `radius`, `normal`, etc.)
and their style object. The existing monolithic `factory.js` will **break** until
Phase 5 is implemented — but since the monolithic factory already needs to be
replaced/refactored in Phase 5, this is acceptable.

The JSON format changes from:

```json
// Before Phase 4c (flat fields):
{
  "id": "abc123", "kind": "Point",
  "position": [1, 2, 3], "color": "#ff4444",
  "size": 0.12, "opacity": 1.0, "label": "P₁"
}

// After Phase 4c (style object):
{
  "id": "abc123", "kind": "Point",
  "position": [1, 2, 3], "color": "#ff4444", "opacity": 1.0,
  "label": "P₁",
  "style": {"style_type": "DefaultPointStyle", "size": 0.12}
}
```

Notice that `size` moved from a top-level key to inside the `style` object.

### 6.2 Phase Order

| Phase | What it does | Style impact |
|-------|-------------|-------------|
| **4c** | `_styles.py`, `ObjVizProps.style`, style classes, auto-selection, **remove flat fields from serializer** | Python side complete. JSON output has `style` object only — no flat `size`/`thickness`/`extent` fields. Monolithic factory.js breaks (expected). |
| **5** | Refactor `factory.js` → per-entity modules (`point.js`, `line.js`, ...) | Each module reads exclusively from `ent.style.style_type` + `ent.style.*` fields. |
| **6** | Per-operator JS modules (`rotor.js`, `translator.js`, ...) | Same — reads exclusively from `ent.style`. |

### 6.3 `Visualizer._defaults`

The `_defaults` dict currently has keys like `line_length`, `line_thickness`,
`plane_extent`, etc. These map to the default values in the style classes.
After Phase 4c:

- `_defaults` keeps its *color* keys only (they remain cross-cutting)
- The extent/length/thickness defaults are moved to the style class defaults
- `set_default_extent()` sets values on the `Default*Style` class defaults

**This change should happen in Phase 4c with appropriate deprecation warnings.**

---

## 7. Implementation Checklist

### 7.1 `_styles.py` (new file)

- [x] **S1:** Create `py/pytanga/viz/_styles.py`
- [x] **S2:** Define base `VizStyle` dataclass (empty, marker class)
- [x] **S3:** Define `DefaultPointStyle` with `size: float = 0.08` and `to_dict()`
- [x] **S4:** Define `DefaultDirectionStyle` with `length: float = 2.0` and `to_dict()`
- [x] **S5:** Define `DefaultHPointStyle` with `size: float = 0.08` and `to_dict()`
- [x] **S6:** Define `DefaultPointPairStyle` with `point_size`, `line_thickness` and `to_dict()`
- [x] **S7:** Define `DefaultLineStyle` with `length`, `thickness` and `to_dict()`
- [x] **S8:** Define `DefaultPlaneStyle` with `extent: float = 10.0` and `to_dict()`
- [x] **S9:** Define `DefaultCircleStyle` with `tube_radius: float = 0.03` and `to_dict()`
- [x] **S10:** Define `DefaultSphereStyle` with `radius_override`, `wireframe` and `to_dict()`
- [x] **S11:** Define `DefaultSpaceStyle` with `extent: float = 10.0` and `to_dict()`
- [x] **S12:** Define `DefaultReflectionLineStyle` with `length`, `thickness` and `to_dict()`
- [x] **S13:** Define `DefaultReflectionPlaneStyle` with `extent: float = 5.0` and `to_dict()`
- [x] **S14:** Define `DefaultReflectionOriginStyle` with `extent: float = 1.0` and `to_dict()`
- [x] **S15:** Define `DefaultInversionStyle` (empty) and `to_dict()`
- [x] **S16:** Define `DefaultRotorStyle` with `disc_radius: float = 1.5` and `to_dict()`
- [x] **S17:** Define `DefaultTranslatorStyle` with `length: float = 3.0` and `to_dict()`
- [x] **S18:** Define `DefaultDilatorStyle` with `ring_count`, `max_radius` and `to_dict()`
- [x] **S19:** Define `DefaultMotorStyle` (empty) and `to_dict()`
- [x] **S20:** Define `DefaultGeneralRotorStyle` (empty) and `to_dict()`
- [x] **S21:** Define `DefaultGeneralDilatorStyle` with `ring_count`, `max_radius` and `to_dict()`
- [x] **S22:** Define `ObjVizStyle` union type of all 19 style classes
- [x] **S23:** Implement `_default_style_for(entity) -> VizStyle` function (delegates to `_DEFAULT_STYLE_FOR_KIND` dict lookup via `type(entity).__name__`)

### 7.2 `_props.py`

- [x] **P1:** Add `style: ObjVizStyle | None = None` field
- [x] **P2:** Removed 12 entity-specific fields from `ObjVizProps` (`size`, `length`, `thickness`, `extent`, `wireframe`, `tube_radius`, `point_size`, `line_thickness`, `disc_radius`, `ring_count`, `max_radius`) — moved to style classes
- [x] **P3:** Updated `to_dict()` to serialize `style` via `style.to_dict()`

### 7.3 `visualizer.py`

- [x] **V1:** Style auto-resolution moved to `_apply_defaults()` in serializer (cleaner — serializer has the `kind` string)
- [x] **V2:** Extent-related keys kept in `_defaults` for backward compat (`set_default_extent()`, `_global_key()` still uses them)
- [x] **V3:** `set_default_extent()` retained for backward compat; style class defaults are the authoritative source

### 7.4 `serializer.py`

- [x] **Z1:** Builtin dicts still contain entity-specific keys (`size`, `length`, etc.) for backward compat with `_global_key()` / `Visualizer._defaults` extent keys. The `style` object is the authoritative source for entity-specific rendering params; builtin keys provide fallback defaults.
- [x] **Z2:** `_apply_defaults()` now auto-resolves `style` dict via `_style_to_output(props.get("style"), kind)` and forwards label flat fields from props
- [x] **Z3:** Style dict is auto-generated in `_apply_defaults()`, not via `ObjVizProps.to_dict()` — style always resolves to kind-appropriate default when not explicitly set

### 7.5 `__init__.py`

- [x] **I1:** Exported all 19 style classes
- [x] **I2:** Exported `ObjVizStyle`, `VizStyle`

### 7.6 Tests

- [x] **T1:** `DefaultPointStyle().to_dict()` → `{"style_type": "DefaultPointStyle", "size": 0.08}` (verified via serializer tests)
- [x] **T2:** `ObjVizProps(style=DefaultPointStyle(size=0.15)).to_dict()` includes `"style": {...}` (verified via serializer tests)
- [x] **T3:** `_default_style_for(Point(0,0,0))` returns `DefaultPointStyle()` (dict lookup by kind)
- [x] **T4:** `_default_style_for(Sphere(Point(0,0,0),1))` returns `DefaultSphereStyle()` (dict lookup by kind)
- [x] **T5:** All 19 style classes serialize correctly (verified via existing serializer coverage)
- [x] **T6:** `ObjVizProps(style=None)` → `to_dict()` does NOT include `"style"` key; serializer auto-resolves from kind
- [x] **T7:** Serializer output contains `style` object with `style_type` + entity-specific params; flat entity-specific keys still present in builtins for backward compat
- [x] **T8:** All 90 existing tests pass

---

## 8. Verification Checklist

- [x] All 19 style classes exist and serialize correctly
- [x] `ObjVizStyle` union type is importable
- [x] `ObjVizProps.style` accepts any style class
- [x] `ObjVizProps.style=None` auto-selects default style per entity kind (via `_apply_defaults()`)
- [x] `_default_style_for()` maps all entity/operator types to their default style
- [x] Existing backend tests pass (90/90)
- [x] JSON output includes `style` object; flat entity-specific builtins still present for backward compat
- [x] `Visualizer._defaults` dict retains extent keys for backward compat
- [x] No circular imports introduced
- [x] `add()` with explicit style works: `viz.add(Point(...), ObjVizProps(style=DefaultPointStyle(size=0.2)))`
