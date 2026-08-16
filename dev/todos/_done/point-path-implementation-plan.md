# PointPath — Connected Line Segments in Viz Module

## Overview

Add a `PointPath` class to the viz module that renders connected line segments
through an ordered list of 3D points. Supports FIFO capping for object trails,
per-point colors, and color gradient utilities.

## API Design

### `PointPath` class (`py/pytanga/viz/_point_path.py`)

```python
PointPath(max_points=None, pop_colors=True, default_colors=None)
```

| Parameter        | Purpose                                                       |
| ---------------- | ------------------------------------------------------------- |
| `max_points`     | FIFO cap; `None` = unlimited                                  |
| `pop_colors`     | `True` → pop oldest color with oldest point; `False` → colors anchored to slot positions |
| `default_colors` | Template list mapping position index → fallback color for `add()` calls without explicit color |

**Methods:**

- `add(point, *, color=None)` — appends a point. Accepts:
  - `Point(x, y, z)` — uses `.x`, `.y`, `.z`
  - `(x, y, z)` tuple — direct coordinates
  - MV — resolved via `pytanga.geometry.analyze()` → `Point` / `HPoint` (uses `.point`) / `Sphere` (uses `.center`)
  - When `color=None`: resolves default color from current color list, then default_colors, then inherits previous point's color, then falls back to style default
- `remove(index=-1)` — remove by index
- `clear()` — empty both points and colors
- `set_colors(colors)` — replace color list
- `set_default_colors(colors)` — replace default color template
- Properties: `points`, `colors`, `default_colors`, `dim` (always 3), `is_full`

**Color resolution when `add(point, color=None)`:**

1. If a color exists at the new point's index in `_colors` → use it
2. Else if `_default_colors` has a value at that index → use it
3. Else inherit from the previous point's color
4. Else `None` (falls back to style default on frontend)

**FIFO behavior with `max_points`:**

- `pop_colors=True`: `add()` when full pops oldest point AND oldest color. New point gets color resolved as above. `len(points) == len(colors)` always.
- `pop_colors=False`: `add()` when full pops oldest point only. Colors stay anchored to their position slots. `len(colors)` stabilizes at `max_points` (or `len(default_colors)`).

### Color Utility Functions (`py/pytanga/viz/_point_path.py`)

```python
def gradient_colors(start: str, end: str, steps: int) -> list[str]:
    """Linear RGB interpolation returning `steps` CSS hex strings."""

def multi_gradient_colors(
    stops: list[tuple[float, str]],  # e.g. [(0.0, "#440000"), (0.5, "#ff0000"), (1.0, "#ff8844")]
    steps: int,
) -> list[str]:
    """Multi-stop gradient with positional anchors (0.0–1.0)."""
```

### `PointPathStyle` (`py/pytanga/viz/_styles/_entity_styles.py`)

```python
@dataclass
class PointPathStyle(VizStyle):
    color: str | None = None          # fallback uniform color
    opacity: float | None = None
    line_thickness: float | None = None
```

Canonical default: `PointPathStyle(color="#ffffff", opacity=1.0, line_thickness=0.03)`

### Serialized JSON (frontend wire format)

```json
{
    "id": "abc123",
    "layer": "scene",
    "kind": "PointPath",
    "points": [[0,0,0], [1,2,3], [3,1,0]],
    "colors": ["#ff0000", null, "#00ff00"],
    "color": "#ffffff",
    "opacity": 1.0,
    "line_thickness": 0.03
}
```

`null` in colors means "use the uniform fallback `color`."

---

## Files to Create/Modify

| #  | File                                           | Action   | Description                                                  |
| -- | ---------------------------------------------- | -------- | ------------------------------------------------------------ |
| 1  | `py/pytanga/viz/_point_path.py`                | **New**  | `PointPath` class + `gradient_colors()` + `multi_gradient_colors()` |
| 2  | `py/pytanga/viz/_styles/_entity_styles.py`     | Modify   | Append `PointPathStyle` dataclass                            |
| 3  | `py/pytanga/viz/_styles/__init__.py`           | Modify   | Export `PointPathStyle`, add to `ObjVizStyle` union and `_DEFAULT_STYLE_FOR_KIND` |
| 4  | `py/pytanga/viz/_style_dict.py`                | Modify   | Add `"pointpath": "PointPath"` to `_kind_to_key()`, `"PointPath": None` to `_make_default_label_styles()` |
| 5  | `py/pytanga/viz/serializer.py`                 | Modify   | Add `_serialize_point_path()` function, dispatch via `isinstance` in `serialize_entity()` |
| 6  | `py/pytanga/viz/templates/renderers/point_path.js` | **New**  | Three.js renderer using `THREE.Line` with `BufferGeometry` |
| 7  | `py/pytanga/viz/templates/renderers/factory.js` | Modify   | Import `createPointPath`, add `case 'PointPath'` dispatch    |
| 8  | `py/pytanga/viz/templates/viewer.js`           | Modify   | Update `inPlaceUpdate()` to rebuild on points change for `PointPath` |
| 9  | `py/pytanga/viz/visualizer.py`                 | Modify   | Recognize `PointPath` instances in `_add_to_scene()` (before `_resolve()` call) |
| 10 | `py/pytanga/viz/__init__.py`                   | Modify   | Export `PointPath`, `PointPathStyle`, `gradient_colors`, `multi_gradient_colors` |
| 11 | `dev/todos/point-path-implementation-plan.md`  | **New**  | This file                                                    |

`py/pytanga/viz/_scene_handle.py` needs **no changes** — `VizSceneHandle.add()` delegates to `Visualizer._add_to_scene()`.

---

## Implementation Details

### 1. `_point_path.py` — `PointPath` class

- Stores `_points: list[tuple[float, float, float]]` and `_colors: list[str | None]`
- `_resolve_point(point)` helper: dispatches on type to extract `(x, y, z)`
- `add()`: calls `_resolve_point()`, handles FIFO/pop_colors logic, resolves color
- `remove(index)`: pop from both lists
- `clear()`: reset both lists
- Properties expose slices/properties for serialization

### 2. `_entity_styles.py` — `PointPathStyle`

Follows the exact same pattern as `LineStyle` / `PointStyle`:
- Dataclass with `VizStyle` base
- `to_dict()` with `style_type: "PointPathStyle"`

### 3. `_styles/__init__.py`

- Import `PointPathStyle` from `_entity_styles`
- Add to `ObjVizStyle` union
- Add to `_DEFAULT_STYLE_FOR_KIND` dict with default values
- Export in module-level `__all__`

### 4. `_style_dict.py`

- Add `"pointpath": "PointPath"` mapping
- Add `"PointPath": None` to label style overrides

### 5. `serializer.py`

- Add `_serialize_point_path(ent: PointPath, props, kind, styles_map)` function
- Returns dict with `kind: "PointPath"`, `points`, `colors`, and style-merged `color`, `opacity`, `line_thickness`
- Add `isinstance(entity, PointPath)` branch in `serialize_entity()` — placed **before** the `isinstance(entity, Point)` check since `PointPath` is not a `GeoEntity` and won't false-match

### 6. `point_path.js` renderer

- **Uniform mode** (all colors `null`): `LineBasicMaterial({ color })` with position-only `BufferGeometry`
- **Vertex-colors mode** (any color non-null): `LineBasicMaterial({ vertexColors: true })` with color buffer attribute
- Uses `THREE.Line` with pairwise segments (each pair: `[i, i+1]` for `n-1` segments)
- Handles 0 or 1 point gracefully (returns empty group)
- Rebuilds on update by disposing old geometry/material
- **Thickness**: `THREE.Line` uses `gl.lineWidth` which is a global uniform — per-vertex thickness is not supported by WebGL lines. The initial implementation uses uniform `line_thickness`. For per-vertex variable thickness later, we can switch to a custom ribbon/tube `BufferGeometry` or cylinder-per-segment approach (similar to the existing `Line` entity renderer in `line.js`).

### 7. `factory.js`

- Import `createPointPath`
- Add `case 'PointPath': mesh = createPointPath(ent); break;`

### 8. `viewer.js` — `inPlaceUpdate()`

- Add early check: if `ent.kind === 'PointPath'`, return `false` → triggers full `createEntityMesh` rebuild
- (Could be optimized later with partial buffer updates)

### 9. `visualizer.py` — `_add_to_scene()`

- Before the `isinstance(obj, (GeoEntity, GeoOperator))` check in `_resolve()`, add:
  ```python
  if isinstance(obj, PointPath):
      return scene.add_object(SceneObject(
          layer="scene", kind="PointPath", data=obj, properties=properties, dirty=True
      ), object_id=entity_id)
  ```
- This bypasses `_resolve()` since `PointPath` is not an MV/Entity/Operator

### 10. `viz/__init__.py`

- Import and export: `PointPath`, `PointPathStyle`, `gradient_colors`, `multi_gradient_colors`

---

## Usage Examples

### Graph Display

```python
from pytanga.viz import Visualizer, PointPath, PointPathStyle

viz = Visualizer()
path = PointPath()
path.add((0, 0, 0), color="#ff0000")
path.add((1, 2, 0), color="#00ff00")
path.add((3, 1, 0), color="#0000ff")
viz.add(path, style=PointPathStyle(line_thickness=0.05))
```

### Moving Object Trail

```python
from pytanga.viz import Visualizer, PointPath, gradient_colors

viz = Visualizer()
trail = PointPath(max_points=100, pop_colors=False,
                  default_colors=gradient_colors("#440000", "#ffaa00", 100))
tid = viz.add(trail)

for pos in positions:
    trail.add(pos)
    viz.update_entity(tid, trail)
    viz.sleep_ms(50)
    viz.flush()
```

### Multi-Stop Rainbow

```python
path = PointPath()
path.set_default_colors(multi_gradient_colors(
    [(0, "#ff0000"), (0.33, "#00ff00"), (0.66, "#0000ff"), (1.0, "#ff0000")],
    200
))
for node in graph_nodes:
    path.add(node)
viz.add(path)
```

---

## Edge Cases

- **Empty path**: No segments rendered (empty group in Three.js)
- **Single point**: No segments (needs ≥2 points to draw)
- **max_points=0**: Raises `ValueError`
- **Color list shorter than points**: Missing slots get `None` (style fallback)
- **Color list longer than points**: Trailing colors ignored until points catch up
- **default_colors with max_points and pop_colors=False**: Default colors define per-slot templates; when points exceed `max_points`, new points at slot N use `default_colors[N]`
- **MV that resolves to non-Point/Sphere**: Raises `ValueError` ("Cannot extract point from ...")