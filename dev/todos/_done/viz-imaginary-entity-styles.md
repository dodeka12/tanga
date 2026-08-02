# Imaginary Entity Default Styles — Implementation Plan

**Date:** 1 August 2026
**Status:** Implemented — 1 August 2026

---

## Motivation

The `Visualizer` currently uses a single `CircleStyle` default for all circles and a single `SphereStyle` default for all spheres, regardless of whether the entity is real or imaginary (`is_imaginary=True`). Users need the ability to set distinct default styles (color, opacity, wireframe, etc.) for imaginary variants.

The `Circle`, `Sphere`, and `PointPair` dataclasses already carry an `is_imaginary: bool` field, but this flag is not consulted during style resolution. The serializer always passes `kind="Circle"` (resp. `"Sphere"`, `"PointPair"`) to `_apply_defaults()`, so all instances share one default style.

---

## Design Decisions

### Subclass Dataclasses as Style Keys

New frozen dataclasses `ImagCircle`, `ImagSphere`, and `ImagPointPair` are introduced in `entities.py`. Each inherits from its real counterpart and overrides the default of `is_imaginary` to `True`.

**Why subclasses and not just string keys?** The `_StyleDict` normalises class keys to `__name__`, so `viz.default_styles[ImagCircle]` works naturally alongside `viz.default_styles[Circle]`. This keeps the API consistent — users never need to switch between class keys and string keys. The subclasses also serve as convenience constructors: `ImagCircle(center=..., normal=..., radius=2.0)` sets `is_imaginary=True` automatically.

**Dual role.** The analysis functions (`pytanga.geometry.analyze`) always return base types (`Circle`, `Sphere`, `PointPair`) with `is_imaginary=True` for imaginary entities. The new subclasses are **not** returned by analysis — they are only used for:
1. Convenient user-side construction (`ImagCircle(...)`)
2. Class-based keys in the style dict (`viz.default_styles[ImagCircle]`)

**Serializer remapping is still required.** Even with the subclasses in place, the serializer must still remap the effective style lookup key based on `ent.is_imaginary`, because base-type entities with `is_imaginary=True` arrive from the analysis pipeline.

---

## Files to Modify

| File | Change |
|---|---|
| `py/pytanga/geometry/entities.py` | Add `ImagPointPair`, `ImagCircle`, `ImagSphere` subclasses; update `Entity` union type |
| `py/pytanga/geometry/__init__.py` | Export the three new classes |
| `py/pytanga/viz/_styles.py` | Add three entries to `_DEFAULT_STYLE_FOR_KIND`; import new entity classes; extend `_default_style_for()` type hint and `ObjVizStyle` union if needed |
| `py/pytanga/viz/_style_dict.py` | Extend `_kind_to_key()` and `_make_default_label_styles()` |
| `py/pytanga/viz/serializer.py` | Branch on `is_imaginary` in `_serialize_circle()`, `_serialize_sphere()`, `_serialize_point_pair()` to use `"ImagCircle"` / `"ImagSphere"` / `"ImagPointPair"` as effective kind |
| `py/pytanga/viz/visualizer.py` | Update docstrings for `set_default_color()` and `default_styles` property |

---

## Detailed Steps

### Step 1 — Add `ImagPointPair`, `ImagCircle`, `ImagSphere` to `entities.py`

Add three frozen dataclass subclasses after their respective parent definitions:

```python
@dataclass(frozen=True)
class ImagPointPair(PointPair):
    """An imaginary point pair (N3/PGA3 only).

    Inherits all fields from :class:`PointPair` with ``is_imaginary=True``.
    """
    is_imaginary: bool = True


@dataclass(frozen=True)
class ImagCircle(Circle):
    """An imaginary circle in 3D space.

    Inherits all fields from :class:`Circle` with ``is_imaginary=True``.
    """

    is_imaginary: bool = True


@dataclass(frozen=True)
class ImagSphere(Sphere):
    """An imaginary sphere in 3D space.

    Inherits all fields from :class:`Sphere` with ``is_imaginary=True``.
    """

    is_imaginary: bool = True
```

Update the `Entity` union type at the bottom of the file to include `ImagPointPair`, `ImagCircle`, `ImagSphere`.

**Ordering constraint:** Subclasses must be defined **after** their parent classes and **before** any module-level code that references them (e.g., the `Entity` union).

---

### Step 2 — Export New Classes from `py/pytanga/geometry/__init__.py`

Add `ImagPointPair`, `ImagCircle`, `ImagSphere` to the `__all__` list (or the equivalent import block). Confirm the exact export mechanism by reading the existing `__init__.py`.

---

### Step 3 — Add Canonical Default Styles in `_styles.py`

#### 3a. Import new entity classes

Add `ImagPointPair`, `ImagCircle`, `ImagSphere` to the imports from `pytanga.geometry.entities`.

#### 3b. Add entries to `_DEFAULT_STYLE_FOR_KIND`

```python
"ImagPointPair": PointPairStyle(
    color="#ff88ff", opacity=1.0, point_size=0.06, line_thickness=0.02
),
"ImagCircle": CircleStyle(color="#ff88ff", opacity=0.5, tube_radius=0.03),
"ImagSphere": SphereStyle(
    color="#ff8844", opacity=0.3, wireframe=True, wireframe_resolution=12
),
```

Imaginary entities get a distinct color palette:
- Imaginary circles: magenta (`#ff88ff`) vs real circles: magenta (`#ff44ff`)
- Imaginary spheres: orange (`#ff8844`) vs real spheres: gold (`#ffaa00`)
- Imaginary point pairs: magenta (`#ff88ff`) vs real point pairs: green (`#44ff44`)

These are initial defaults and can be tuned later.

#### 3c. Extend `_default_style_for()` type hint

Add `ImagPointPair`, `ImagCircle`, `ImagSphere` to the union type in `_default_style_for()`'s parameter type annotation.

---

### Step 4 — Extend Kind-Key Mapping in `_style_dict.py`

#### 4a. `_kind_to_key()`

Add three new mappings:
```python
"imagpointpair": "ImagPointPair",
"imagcircle": "ImagCircle",
"imagsphere": "ImagSphere",
```

This enables `viz.set_default_color("imagcircle", "#ff0000")` to work.

#### 4b. `_make_default_label_styles()`

Add three entries (all `None` initially, following the existing pattern):
```python
"ImagPointPair": None,
"ImagCircle": None,
"ImagSphere": None,
```

---

### Step 5 — Branch on `is_imaginary` in `serializer.py`

#### 5a. `_serialize_circle()`

```python
def _serialize_circle(ent, props, *, kind, styles_map=None):
    effective_kind = "ImagCircle" if ent.is_imaginary else "Circle"
    return _apply_defaults(
        props, effective_kind, {"tubeRadius": 0.03}, styles_map=styles_map
    ) | {
        "center": [ent.center.x, ent.center.y, ent.center.z],
        "normal": [ent.normal.x, ent.normal.y, ent.normal.z],
        "radius": _clamp_positive(ent.radius),
        "isImaginary": ent.is_imaginary,
    }
```

The output dict still uses the base kind (`"Circle"`) for frontend rendering dispatch — the `"kind"` field in the result dict comes from `_apply_defaults`, which receives `effective_kind`. Note: `_apply_defaults` sets `result["kind"] = kind` (the `effective_kind`). This means imaginary entities would carry `kind: "ImagCircle"` in the wire format. The frontend must handle this — **or** the kind in the result dict must be overridden back to the base kind.

**Decision needed:** The `_apply_defaults` helper sets `result["kind"] = effective_kind`. This means the frontend would receive `kind: "ImagCircle"` for imaginary circles. Options:

1. **Override kind after `_apply_defaults`** — set `result["kind"] = "Circle"` in the output dict. The frontend sees the base kind, style is already resolved. This is the safer choice.
2. **Let the frontend handle `ImagCircle`** — add frontend dispatch for the new kind strings. More work, more coupling.

**Recommendation:** Use option 1. After `_apply_defaults`, override `kind` back to the base type name. The style is already fully resolved at this point; the `kind` field is only used for frontend rendering dispatch, which should be identical for real and imaginary variants.

Concretely:
```python
def _serialize_circle(ent, props, *, kind, styles_map=None):
    effective_kind = "ImagCircle" if ent.is_imaginary else "Circle"
    result = _apply_defaults(
        props, effective_kind, {"tubeRadius": 0.03}, styles_map=styles_map
    )
    result["kind"] = "Circle"  # frontend dispatch uses base kind
    result.update({
        "center": [...],
        "normal": [...],
        "radius": _clamp_positive(ent.radius),
        "isImaginary": ent.is_imaginary,
    })
    return result
```

#### 5b. `_serialize_sphere()`

Same pattern — use `"ImagSphere"` for style lookup, override kind to `"Sphere"`:

```python
def _serialize_sphere(ent, props, *, kind, styles_map=None):
    effective_kind = "ImagSphere" if ent.is_imaginary else "Sphere"
    result = _apply_defaults(props, effective_kind, {}, styles_map=styles_map)
    result["kind"] = "Sphere"
    result.update({
        "center": [...],
        "radius": _clamp_positive(ent.radius),
        "isImaginary": ent.is_imaginary,
    })
    return result
```

#### 5c. `_serialize_point_pair()`

Same pattern — use `"ImagPointPair"` for style lookup, override kind to `"PointPair"`:

```python
def _serialize_point_pair(ent, props, *, kind, styles_map=None):
    effective_kind = "ImagPointPair" if ent.is_imaginary else "PointPair"
    result = _apply_defaults(
        props, effective_kind, {"lineThickness": 0.02, "pointSize": 0.06}, styles_map=styles_map
    )
    result["kind"] = "PointPair"
    result.update({
        "pointA": [...],
        "pointB": [...],
        "isImaginary": ent.is_imaginary,
    })
    return result
```

---

### Step 6 — Update Docstrings in `visualizer.py`

#### 6a. `set_default_color()` docstring

Add `"imagpointpair"`, `"imagcircle"`, `"imagsphere"` to the list of valid kinds in the docstring.

#### 6b. `default_styles` property docstring

Add `ImagPointPair`, `ImagCircle`, `ImagSphere` to the list of valid class keys in the docstring.

---

## Edge Cases

| Scenario | `SceneObject.kind` | Effective style key | Wire format `kind` | Result |
|---|---|---|---|---|
| User passes `Circle(..., is_imaginary=False)` | `"Circle"` | `"Circle"` | `"Circle"` | Real circle defaults applied |
| User passes `Circle(..., is_imaginary=True)` | `"Circle"` | `"ImagCircle"` (remapped) | `"Circle"` (overridden) | Imaginary circle defaults applied |
| User passes `ImagCircle(...)` | `"ImagCircle"` | `"ImagCircle"` | `"Circle"` (overridden) | Imaginary circle defaults applied |
| Analysis returns `Circle(..., is_imaginary=True)` | `"Circle"` | `"ImagCircle"` (remapped) | `"Circle"` (overridden) | Imaginary circle defaults applied |
| `viz.default_styles[ImagCircle] = CircleStyle(...)` | — | — | — | User's style stored under `"ImagCircle"` key |
| `viz.set_default_color("imagcircle", "#ff0000")` | — | — | — | Updates `styles_map["ImagCircle"].color` |

---

## Files NOT Requiring Changes

- **`scene.py`**: `SceneObject.kind` uses `type(entity).__name__` — no change needed. The imaginary branching happens at serialization time.
- **`_props.py`**: Unrelated color normalisation.
- **`_StyleDict`** (`_style_dict.py`): Already supports class-to-name normalisation via `_key()`.
- **Frontend/JS**: The wire format continues to use base kind strings (`"Circle"`, `"Sphere"`, `"PointPair"`) with `isImaginary: true/false`. No protocol changes.
- **`ObjVizStyle` union type**: Since `ImagCircle` uses `CircleStyle` and is a subclass of `Circle`, no new style types are needed.
- **Analysis modules** (`analysis_pga3.py`, etc.): Analysis returns base types with `is_imaginary=True` — no change.
- **Create modules** (`create_pga3.py`, etc.): No new create functions needed; users construct `ImagCircle(...)` directly.

---

## Verification

After implementation, the following should work:

```python
from pytanga.viz import Visualizer
from pytanga.geometry import Circle, ImagCircle, Point, Direction, Sphere, ImagSphere

viz = Visualizer()

# Set distinct defaults via subclass keys
from pytanga.viz._styles import CircleStyle, SphereStyle
viz.default_styles[ImagCircle] = CircleStyle(color="#ff00ff", opacity=0.5)
viz.default_styles[ImagSphere] = SphereStyle(color="#ff8800", opacity=0.3, wireframe=False)

# Or via string API
viz.set_default_color("imagcircle", "#ff00ff")

# Construction convenience
c = ImagCircle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2.0)
assert c.is_imaginary == True

# Analysis returns base type — serializer remaps style
from pytanga.geometry import analyze
mv = ...  # some PGA3 imaginary circle multivector
result = analyze(mv, opns=False)
assert isinstance(result, Circle)  # base type, not ImagCircle
assert result.is_imaginary == True

viz.add(result)  # uses ImagCircle defaults because serializer remaps