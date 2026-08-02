# Phase 4a — Synchronize Viz with Geo-Fix Changes

**Prerequisites:** Phases 1–4 implemented (Python server + Three.js frontend functional)

**Goal:** Update the visualization submodule code to match the entity and operator
changes introduced by the `dev/todos/geo_fix/` plan (Phases 2–6, all COMPLETE ✅).

---

## 1. Audit — What Changed in `pytanga.geometry`

### 1.1 Entity Changes

| Change | Old (pre-fix) | New (post-fix) | Impact on Viz |
|--------|--------------|----------------|--------------|
| `HomogeneousPoint` renamed | `HomogeneousPoint(point, weight)` | `HPoint(point, weight)` | `serializer.py` import, `factory.js` case string |
| `PointPair.is_imaginary` | (did not exist) | `is_imaginary: bool = False` | serializer must pass flag; JS must render dashed/ghost style |
| `Circle.is_imaginary` | (did not exist) | `is_imaginary: bool = False` | serializer must pass flag; JS must render dashed/ghost style |
| `Sphere.is_imaginary` | (did not exist) | `is_imaginary: bool = False` | serializer must pass flag; JS must render dashed/ghost style |

### 1.2 Operator Changes

| Change | Old (pre-fix) | New (post-fix) | Impact on Viz |
|--------|--------------|----------------|--------------|
| `Reflection` split | Single `Reflection(normal)` | `ReflectionLine(direction)`, `ReflectionPlane(normal)`, `ReflectionOrigin()` | `serializer.py` imports new classes; `factory.js` new cases; backward-compat alias exists |
| `Inversion.radius` added | `Inversion(origin)` | `Inversion(center, radius=1.0)` | serializer passes `radius`; JS can size wireframe sphere |
| `Reflector` added | (did not exist) | `Reflector(source, target)` | serializer + factory.js new entry |

**Backward compatibility note:** `operators.py` has `Reflection = ReflectionPlane` as a deprecated alias. The serializer currently imports `Reflection` from `operators`. This import still works but should be updated to import the explicit types.

### 1.3 New Geometry Convenience Class

| Addition | File | Impact on Viz |
|----------|------|--------------|
| `Geometry` class | `py/pytanga/geometry/_geometry.py` | `visualizer.py._resolve()` could optionally accept `Geometry` instances for the algebra binding, but not strictly needed — `Geometry.create()` outputs an MV, and `_resolve` already handles MVs. |

**No mandatory viz changes** for `Geometry`. It produces MVs which `_resolve()` already handles.

### 1.4 Exports from `py/pytanga/geometry/__init__.py`

Verify that all new types are importable. Viz imports from:
- `pytanga.geometry.entities` — `Entity` union type
- `pytanga.geometry.operators` — `Operator` union type

Check that `HPoint`, `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin`, `Reflector` are properly exported.

---

## 2. Files to Modify

### 2.1 `py/pytanga/viz/serializer.py`

**Current state:** Imports `HomogeneousPoint`, `Reflection`, etc. from old names.
Dispatches `isinstance(entity, Reflection)` etc.

**Changes needed:**

| # | Change | Details |
|---|--------|---------|
| S1 | Rename import `HomogeneousPoint` → `HPoint` | Line ~20: `from pytanga.geometry.entities import ... HomogeneousPoint ...` |
| S2 | Update `_serialize_homogeneous_point` → `_serialize_hpoint` | Rename function, update `isinstance` check and builtin defaults |
| S3 | Handle `PointPair.is_imaginary` | Pass `is_imaginary` field to JSON output |
| S4 | Handle `Circle.is_imaginary` | Pass `is_imaginary` field to JSON output |
| S5 | Handle `Sphere.is_imaginary` | Pass `is_imaginary` field to JSON output |
| S6 | Add `ReflectionLine` serializer | `_serialize_reflection_line()` — direction vector, origin at (0,0,0) |
| S7 | Add `ReflectionPlane` serializer | `_serialize_reflection_plane()` — plane normal, origin at (0,0,0) |
| S8 | Add `ReflectionOrigin` serializer | `_serialize_reflection_origin()` — marker entity (small cross at origin) |
| S9 | Update `Inversion` serializer | Pass `radius` field instead of hardcoded `sphereRadius` |
| S10 | Add `Reflector` serializer | `_serialize_reflector()` — double-ended arrow or bisector plane + arrow |
| S11 | Update `serialize_entity()` dispatcher | Replace old `Reflection` isinstance with new three-type dispatch |
| S12 | Update builtin defaults | Add default colors for `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin`, `Reflector` |

### 2.2 `py/pytanga/viz/visualizer.py`

**Current state:** `_resolve()` imports `Operator` from `operators`, `_kind_from_entity()` uses `type(entity).__name__`. `_defaults` dict has color keys.

**Changes needed:**

| # | Change | Details |
|---|--------|---------|
| V1 | Update `_defaults` color keys | Add `color_reflection_line`, `color_reflection_plane`, `color_reflection_origin`, `color_reflector` |
| V2 | `set_default_color()` valid kinds | Add `"reflection_line"`, `"reflection_plane"`, `"reflection_origin"`, `"reflector"` to valid kind list |
| V3 | Verify `_resolve()` works with new operator types | Already checks `GeoOperator` — the new types are automatically covered since they're part of the `Operator` union |

### 2.3 `py/pytanga/viz/scene.py`

**No changes needed.** `_kind_from_entity()` uses `type(entity).__name__` which returns the correct Python class name for all new types.

### 2.4 `py/pytanga/viz/templates/renderers/factory.js`

**Current state:** Monolithic switch on `ent.kind` covering 17 types.

**Changes needed:**

| # | Change | Details |
|---|--------|---------|
| F1 | Rename `HomogeneousPoint` case → `HPoint` | Same rendering (small sphere with weight displayed) |
| F2 | Add `PointPair` imaginary rendering | When `ent.is_imaginary`, render dashed line + ghost points (lower opacity, dashed connector) |
| F3 | Add `Circle` imaginary rendering | When `ent.is_imaginary`, render dashed torus |
| F4 | Add `Sphere` imaginary rendering | When `ent.is_imaginary`, render dashed wireframe |
| F5 | Split `Reflection` case into three | `ReflectionLine` → line through origin + direction arrow; `ReflectionPlane` → translucent plane + normal; `ReflectionOrigin` → small cross-hair at origin |
| F6 | Add `Reflector` case | Double-ended arrow (direction from source to target, or bisector plane) |
| F7 | Update `Inversion` case | Use `ent.radius` instead of `ent.sphereRadius` |

### 2.5 Test File `py/tests/viz/test_phase2_serializer.py`

| # | Change | Details |
|---|--------|---------|
| T1 | Update `HomogeneousPoint` imports → `HPoint` | Fix failing import |
| T2 | Update `Reflection` imports → `ReflectionPlane` | Fix failing import |
| T3 | Add tests for `ReflectionLine`, `ReflectionOrigin`, `Reflector` | New serializer functions |
| T4 | Add tests for `is_imaginary` flag serialization | PointPair, Circle, Sphere |

---

## 3. JS Renderer Visual Design for New Types

### 3.1 ReflectionLine
- Thin cylinder line through origin along the `direction` vector
- Semi-transparent, distinct color (e.g., `#88ccff` light blue)
- Length controlled by `space_extent_render` default

### 3.2 ReflectionPlane
- Same as current `Reflection` rendering: translucent quad + normal arrow
- Default color `#88ccff`

### 3.3 ReflectionOrigin
- Small cross-hair (three orthogonal axis lines) at origin
- Default color `#ffffff`

### 3.4 Reflector
- Double-ended arrow showing the bisector between `source` and `target` directions
- Or: a translucent plane whose normal is the bisector
- Default color `#ccff88`

### 3.5 Imaginary PointPair / Circle / Sphere
- Same geometry as real versions but with:
  - Dashed/dotted line style (using `LineDashedMaterial` or segmented lines)
  - Reduced opacity (0.3 default instead of 0.7)
  - Ghost-like appearance to convey "no real points"

---

## 4. Implementation Checklist

### serializer.py

- [ ] **S1:** Rename `HomogeneousPoint` → `HPoint` import
- [ ] **S2:** Rename function `_serialize_homogeneous_point` → `_serialize_hpoint`, update isinstance
- [ ] **S3:** `_serialize_point_pair()` passes `"isImaginary": ent.is_imaginary`
- [ ] **S4:** `_serialize_circle()` passes `"isImaginary": ent.is_imaginary`
- [ ] **S5:** `_serialize_sphere()` passes `"isImaginary": ent.is_imaginary`
- [ ] **S6:** Add `_serialize_reflection_line()` — `{kind: "ReflectionLine", direction: [...], color: ..., opacity: ...}`
- [ ] **S7:** Add `_serialize_reflection_plane()` — `{kind: "ReflectionPlane", normal: [...], origin: [...], planeExtent: ...}`
- [ ] **S8:** Add `_serialize_reflection_origin()` — `{kind: "ReflectionOrigin", origin: [0,0,0]}`
- [ ] **S9:** Update `_serialize_inversion()` — `{..., radius: ent.radius}` (no longer hardcoded `sphereRadius`)
- [ ] **S10:** Add `_serialize_reflector()` — `{kind: "Reflector", source: [...], target: [...]}`
- [ ] **S11:** Update `serialize_entity()` dispatcher: `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin`, `Reflector` isinstance checks
- [ ] **S12:** Add default colors: `color_reflection_line="#aaccff"`, `color_reflection_plane="#88ccff"`, `color_reflection_origin="#ffffff"`, `color_reflector="#ccff88"`

### visualizer.py

- [ ] **V1:** Add `color_reflection_line`, `color_reflection_plane`, `color_reflection_origin`, `color_reflector` to `_defaults`
- [ ] **V2:** Update `set_default_color()` valid kinds

### factory.js

- [ ] **F1:** Rename `HomogeneousPoint` case → `HPoint`
- [ ] **F2:** `PointPair`: if `ent.isImaginary`, use dashed line + ghost points
- [ ] **F3:** `Circle`: if `ent.isImaginary`, use dashed torus
- [ ] **F4:** `Sphere`: if `ent.isImaginary`, use dashed wireframe
- [ ] **F5:** Replace `Reflection` case with `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin`
- [ ] **F6:** Add `Reflector` case
- [ ] **F7:** `Inversion` case reads `ent.radius` instead of `ent.sphereRadius`

### Tests

- [ ] **T1:** Fix `HomogeneousPoint` → `HPoint` in test imports
- [ ] **T2:** Fix `Reflection` → `ReflectionPlane` in test imports
- [ ] **T3:** Test `ReflectionLine`, `ReflectionOrigin`, `Reflector` serialization
- [ ] **T4:** Test `is_imaginary` flag in PointPair/Circle/Sphere JSON output
- [ ] **T5:** Run all existing 89 tests — verify zero regressions
- [ ] **T6:** Run `dev/src/test_viz_smoke.py` — all 8 tests pass

---

## 5. Verification Checklist

- [ ] All existing tests pass (89 backend tests)
- [ ] Smoke test passes (8 integration tests)
- [ ] `from pytanga.viz import Visualizer` works
- [ ] `viz.add(HPoint(point=Point(0,0,0)))` works
- [ ] `viz.add(ReflectionLine(direction=Direction(0,0,1)))` works
- [ ] `viz.add(ReflectionPlane(normal=Direction(0,0,1)))` works
- [ ] `viz.add(ReflectionOrigin())` works
- [ ] `viz.add(Reflector(source=Direction(1,0,0), target=Direction(0,1,0)))` works
- [ ] `viz.add(Sphere(Point(0,0,0), 2, is_imaginary=True))` → wireframe is dashed
- [ ] `viz.add(Circle(Point(0,0,0), Direction(0,0,1), 2, is_imaginary=True))` → torus is dashed
- [ ] `viz.add(PointPair(Point(0,0,0), Point(1,0,0), is_imaginary=True))` → dashed connector
- [ ] Visualizer `_defaults` dict contains all 4 new color keys
- [ ] `set_default_color("reflection_line", "#fff")` works
- [ ] `set_default_color("reflection_plane", "#fff")` works
- [ ] `set_default_color("reflection_origin", "#fff")` works
- [ ] `set_default_color("reflector", "#fff")` works
- [ ] No console errors in browser for any new operator type