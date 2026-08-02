# Wireframe Dash Patterns + Plane & Line Wireframe — Implementation Plan

**Date:** 1 August 2026
**Status:** Plan — do not implement yet

---

## Motivation

1. **Plane and Line wireframe support**: `PlaneStyle` and `LineStyle` currently lack `wireframe` fields, unlike `SphereStyle`, `CircleStyle`, and `PointPairStyle` which already support wireframe overlays.
2. **Configurable dash patterns**: All current wireframes use `MeshBasicMaterial({wireframe: true})`, which renders solid triangle edges with no dash support. Users need dashed, dotted, and solid wireframe patterns.
3. **Unified approach**: Rather than adding dash support only to new renderers, all wireframe-capable entities should move to a single `EdgesGeometry` + `LineSegments` approach, enabling both solid and dashed wireframes from one code path.

---

## Design Overview

### WireframeDashPattern Dataclasses

A new `WireframeDashPattern` dataclass in `_styles.py` captures dash parameters, with three preset subclasses:

```python
@dataclass
class WireframeDashPattern:
    dash_size: float = 0.0   # 0 = solid line
    gap_size: float = 0.0
    scale: float = 1.0

@dataclass
class SolidWireframe(WireframeDashPattern):
    dash_size: float = 0.0   # renders with LineBasicMaterial

@dataclass
class DashedWireframe(WireframeDashPattern):
    dash_size: float = 0.3
    gap_size: float = 0.2

@dataclass
class DottedWireframe(WireframeDashPattern):
    dash_size: float = 0.08
    gap_size: float = 0.15
```

### Style Class Changes

Five style classes gain `wireframe_dash`; two also gain `wireframe`:

| Style | `wireframe` | `wireframe_dash` |
|---|---|---|
| `SphereStyle` | already exists | new |
| `CircleStyle` | already exists | new |
| `PointPairStyle` | already exists | new |
| `PlaneStyle` | new | new |
| `LineStyle` | new | new |

When `wireframe=True` and `wireframe_dash=None`, the JS renderer defaults to solid lines (`LineBasicMaterial`). This is fully backward-compatible.

### JS Helper (`utils.js`)

A single shared function replaces the inline wireframe code in all 5 renderers:

```js
export function addWireframeOverlay(parent, geometry, color, dashPattern) {
    const edges = new THREE.EdgesGeometry(geometry);
    const useDash = dashPattern && dashPattern.dash_size > 0;
    const material = useDash
        ? new THREE.LineDashedMaterial({
            color, dashSize: dashPattern.dash_size,
            gapSize: dashPattern.gap_size, scale: dashPattern.scale || 1.0,
        })
        : new THREE.LineBasicMaterial({ color });
    const lines = new THREE.LineSegments(edges, material);
    if (useDash) lines.computeLineDistances();
    parent.add(lines);
}
```

### Renderer Unification

| Renderer | Current approach | New approach |
|---|---|---|
| `sphere.js` | `Mesh` + `MeshBasicMaterial({wireframe:true})` around full sphere | `EdgesGeometry` + `addWireframeOverlay()` |
| `circle.js` | `Mesh` + `MeshBasicMaterial({wireframe:true})` torus overlay | `EdgesGeometry` + `addWireframeOverlay()` |
| `point_pair.js` | `Mesh` + `MeshBasicMaterial({wireframe:true})` sphere overlay on each point | `EdgesGeometry` + `addWireframeOverlay()` |
| `plane.js` | No wireframe support | `addWireframeOverlay()` added |
| `line.js` | No wireframe support | `addWireframeOverlay()` added |

---

## Files to Modify

| File | Change |
|---|---|
| `py/pytanga/viz/_styles.py` | Add `WireframeDashPattern`, `SolidWireframe`, `DashedWireframe`, `DottedWireframe`; add `wireframe` to `PlaneStyle`/`LineStyle`; add `wireframe_dash` to all 5 styles; update `to_dict()` for all 5; export new classes |
| `py/pytanga/viz/templates/renderers/utils.js` | Add `addWireframeOverlay()` helper |
| `py/pytanga/viz/templates/renderers/sphere.js` | Switch to `EdgesGeometry` + helper |
| `py/pytanga/viz/templates/renderers/circle.js` | Switch to `EdgesGeometry` + helper |
| `py/pytanga/viz/templates/renderers/operators/point_pair.js` | Switch to `EdgesGeometry` + helper |
| `py/pytanga/viz/templates/renderers/plane.js` | Add wireframe overlay |
| `py/pytanga/viz/templates/renderers/line.js` | Add wireframe overlay |

---

## Detailed Steps

### Step 1 — Add WireframeDashPattern Classes to `_styles.py`

Add four dataclasses after the existing style classes (before `_DEFAULT_STYLE_FOR_KIND`):

```python
@dataclass
class WireframeDashPattern:
    """Dash pattern for wireframe overlays.
    
    When ``dash_size=0``, a solid line is rendered.
    When ``dash_size > 0``, ``LineDashedMaterial`` is used.
    """

    dash_size: float = 0.0
    gap_size: float = 0.0
    scale: float = 1.0

    def to_dict(self) -> dict:
        return {"dash_size": self.dash_size, "gap_size": self.gap_size, "scale": self.scale}


@dataclass
class SolidWireframe(WireframeDashPattern):
    """Solid (unbroken) wireframe lines — the default."""

    dash_size: float = 0.0


@dataclass
class DashedWireframe(WireframeDashPattern):
    """Standard dashed wireframe."""

    dash_size: float = 0.3
    gap_size: float = 0.2


@dataclass
class DottedWireframe(WireframeDashPattern):
    """Dotted wireframe (very short dashes)."""

    dash_size: float = 0.08
    gap_size: float = 0.15
```

### Step 2 — Update Wireframe-Capable Style Classes

#### 2a. `SphereStyle` — add `wireframe_dash`

Add field: `wireframe_dash: WireframeDashPattern | None = None`

Update `to_dict()` to serialize `wireframe_dash` via `to_dict()` if not None.

#### 2b. `CircleStyle` — add `wireframe_dash`

Same as sphere.

#### 2c. `PointPairStyle` — add `wireframe_dash`

Same as sphere.

#### 2d. `PlaneStyle` — add `wireframe` + `wireframe_dash`

Add fields: `wireframe: bool | None = None`, `wireframe_dash: WireframeDashPattern | None = None`

Update `to_dict()`.

#### 2e. `LineStyle` — add `wireframe` + `wireframe_dash`

Same as plane.

### Step 3 — Add `addWireframeOverlay()` to `utils.js`

Add the shared helper function. Import it from all 5 renderers. The function takes the parent group/mesh, the geometry (same one used for the solid mesh), the color, and the optional dash pattern dict from the serialized style.

### Step 4 — Update `sphere.js`

Replace the current wireframe block (inside the `if (wireframe !== false ...)` condition):

**Before:**
```js
mesh.add(new THREE.Mesh(wg, new THREE.MeshBasicMaterial({ color: c, wireframe: true, ... })));
```

**After:**
```js
const dash = styleParam(ent, 'wireframe_dash', null);
addWireframeOverlay(mesh, new THREE.SphereGeometry(radius * 1.005, 24, 24), c, dash);
```

`styleParam` needs to handle nested objects — if `wireframe_dash` is `{dash_size: 0.3, ...}`, return it as-is; if not present, return `null`.

### Step 5 — Update `circle.js`

Replace the wireframe torus `Mesh` with `EdgesGeometry` + helper:
```js
if (wireframe) {
    const dash = styleParam(ent, 'wireframe_dash', null);
    addWireframeOverlay(mesh, new THREE.TorusGeometry(radius * 1.005, tubeRadius, 16, 64), color, dash);
}
```

### Step 6 — Update `point_pair.js`

Replace the wireframe sphere `Mesh` inside the point loop with `EdgesGeometry` + helper:
```js
if (wireframe) {
    const dash = styleParam(ent, 'wireframe_dash', null);
    addWireframeOverlay(gm, new THREE.SphereGeometry(sz * 1.005, 16, 16), col, dash);
}
```

### Step 7 — Add Wireframe to `plane.js`

After the solid mesh is created, add:
```js
const wireframe = styleParam(ent, 'wireframe', false);
if (wireframe) {
    const dash = styleParam(ent, 'wireframe_dash', null);
    addWireframeOverlay(mesh, new THREE.PlaneGeometry(extent * 2, extent * 2), color, dash);
}
```

### Step 8 — Add Wireframe to `line.js`

After the solid cylinder mesh is created, add:
```js
const wireframe = styleParam(ent, 'wireframe', false);
if (wireframe) {
    const dash = styleParam(ent, 'wireframe_dash', null);
    addWireframeOverlay(mesh, new THREE.CylinderGeometry(thickness, thickness, length, 8, 1), color, dash);
}
```

### Step 9 — Handle `styleParam` for Nested Objects

The `styleParam()` function in `utils.js` may need updating to handle the `wireframe_dash` field, which is a nested object in the JSON (not a flat value). Confirm that `styleParam` can return the raw value from the `style` sub-object when it's a dict. If not, add a fallback like `ent.style?.wireframe_dash || null`.

---

## Edge Cases

| Scenario | Behavior |
|---|---|
| `wireframe=False`, `wireframe_dash=DashedWireframe()` | No wireframe rendered (dash pattern ignored) |
| `wireframe=True`, `wireframe_dash=None` | Solid wireframe via `LineBasicMaterial` |
| `wireframe=True`, `wireframe_dash=SolidWireframe()` | Solid wireframe (dash_size=0) |
| `wireframe=True`, `wireframe_dash=DashedWireframe()` | Dashed wireframe via `LineDashedMaterial` |
| `wireframe=True`, `wireframe_dash=DottedWireframe(dash_size=0.05, gap_size=0.3)` | Custom dotted pattern |
| Plane with `wireframe=True` | Shows the 4 border edges of the plane (EdgesGeometry behavior) |
| Legacy styles without `wireframe_dash` | JS defaults to `null` → solid wireframe |

---

## Files NOT Requiring Changes

- **`_style_dict.py`**: Style fields flow through `_apply_defaults` generically.
- **`serializer.py`**: `_apply_defaults` passes all props; `_style_to_output` merges all fields.
- **`visualizer.py`**: No API changes needed.
- **`scene.py`**: No protocol change.
- **`_DEFAULT_STYLE_FOR_KIND`**: Default styles remain unchanged (`wireframe=None` for Plane/Line, `wireframe_dash=None` for all). Users opt in explicitly.

---

## Verification

```python
from pytanga.viz import Visualizer
from pytanga.viz._styles import (
    CircleStyle, DashedWireframe, DottedWireframe, SolidWireframe
)

viz = Visualizer()

# Dashed circle
viz.default_styles[Circle].wireframe = True
viz.default_styles[Circle].wireframe_dash = DashedWireframe()

# Dotted sphere via style override
from pytanga.viz._styles import SphereStyle
viz.add(sphere_entity, style=SphereStyle(
    wireframe=True,
    wireframe_dash=DottedWireframe(dash_size=0.05, gap_size=0.3)
))

# Solid wireframe plane
viz.default_styles[Plane].wireframe = True
viz.default_styles[Plane].wireframe_dash = SolidWireframe()