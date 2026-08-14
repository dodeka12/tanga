# PointPath — Connected Line Segments

The `PointPath` class renders an ordered list of 3D points as connected line
segments in the 3D scene. It supports FIFO capping for object trails,
per-point colors, and a `PointPathStyle` for uniform appearance.

Use cases:

- Visualizing **graphs** (nodes connected by edges)
- Drawing **object trails** with a fading color gradient
- Rendering **polylines** in 3D space

## Quick Start

```python
from pytanga.viz import Visualizer, PointPath, PointPathStyle, gradient_colors
from pytanga.geometry import Point

viz = Visualizer()

# Simple path
path = PointPath()
path.add((0, 0, 0), color="#ff0000")
path.add((1, 2, 0), color="#00ff00")
path.add(Point(3, 1, 0), color="#0000ff")
viz.add(path, style=PointPathStyle(line_thickness=2))

viz.run()
```

## PointPath Class

```python
PointPath(max_points=None, pop_colors=True, default_colors=None)
```

| Parameter       | Type                      | Default | Description                                                              |
|----------------|---------------------------|---------|--------------------------------------------------------------------------|
| `max_points`    | `int \| None`             | `None`  | FIFO cap — oldest point is dropped when limit is reached                 |
| `pop_colors`    | `bool`                    | `True`  | When `True`, dropping a point also drops its color. When `False`, colors stay anchored to position slots |
| `default_colors`| `list[str \| None] \| None`| `None` | Template mapping position index → fallback color for `add()` without explicit color |

### Methods

**`add(point, *, color=None)`**

Appends a point to the path. The *point* argument accepts:

| Input type         | Example                  | Behaviour                                                    |
|-------------------|--------------------------|--------------------------------------------------------------|
| `(x, y, z)` tuple | `(1.0, 2.0, 3.0)`      | Position directly                                            |
| `(x, y)` tuple    | `(1.0, 2.0)`           | Assumes `z=0`                                                |
| `Point(x, y, z)`  | `Point(1, 2, 3)`       | Extracts `.x`, `.y`, `.z`                                    |
| MV                | any multivector         | Resolved via `analyze()` → `Point` / `HPoint` (`.point`) / `Sphere` (`.center`) |

When *color* is `None`, the color is resolved with this priority:

1. Existing color at that index in the current color list
2. Value from `default_colors` at that index (wrapping around)
3. Previous point's color (inheritance)
4. `None` — falls back to uniform `PointPathStyle.color` on the frontend

**`remove(index=-1)`** — Remove a point and its color by index.

**`clear()`** — Remove all points and colors.

**`set_colors(colors)`** — Replace the entire color list.

**`set_default_colors(colors)`** — Replace the default color template.

### Properties

| Property   | Type                              | Description                                          |
|-----------|-----------------------------------|------------------------------------------------------|
| `points`   | `list[tuple[float, float, float]]`| Copy of the current point list                       |
| `colors`   | `list[str \| None]`               | Copy of the current color list (parallel to `points`)|
| `dim`      | `int`                             | Always `3`                                           |
| `is_full`  | `bool`                            | `True` when `len(points) >= max_points`             |

## FIFO Behaviour

### `pop_colors=True` (default)

Both the oldest point **and** its color are removed. `len(points) == len(colors)` always.

```python
path = PointPath(max_points=3, pop_colors=True)
path.add((0,0,0), color="#ff0000")
path.add((1,0,0), color="#00ff00")
path.add((2,0,0), color="#0000ff")
# len=3, colors: ['#ff0000', '#00ff00', '#0000ff']

path.add((3,0,0))
# len=3, colors: ['#00ff00', '#0000ff', '#0000ff']  (inherits previous)
```

### `pop_colors=False`

Points shift out but colors stay anchored to their ordinal positions.
This is ideal for **trails with a fixed color gradient** — older segments
fade out while the head stays bright.

```python
path = PointPath(max_points=3, pop_colors=False,
                 default_colors=["#440000", "#aa4400", "#ffaa00"])
path.add((0,0,0))
path.add((1,0,0))
path.add((2,0,0))
# colors: ['#440000', '#aa4400', '#ffaa00']

path.add((3,0,0))
# colors: ['#440000', '#aa4400', '#ffaa00']  (anchored)
# points: [(1,0,0), (2,0,0), (3,0,0)]      (shifted)
```

## Color Utilities

### `gradient_colors(start, end, steps)`

Linear RGB interpolation returning a list of `steps` CSS hex strings.

```python
from pytanga.viz import gradient_colors

# 5-color gradient from dark red to bright orange
colors = gradient_colors("#440000", "#ffaa00", 5)
# ['#440000', '#723200', '#a16500', '#cf9700', '#ffaa00']
```

### `multi_gradient_colors(stops, steps)`

Multi-stop gradient with positional anchors (0.0–1.0).

```python
from pytanga.viz import multi_gradient_colors

# Rainbow with 200 steps
rainbow = multi_gradient_colors(
    [(0.0, "#ff0000"), (0.33, "#00ff00"), (0.66, "#0000ff"), (1.0, "#ff0000")],
    200
)

path = PointPath()
path.set_default_colors(rainbow)
for node in graph_nodes:
    path.add(node)
```

## PointPathStyle

```python
@dataclass
class PointPathStyle(VizStyle):
    color: str | None = None           # fallback uniform color
    opacity: float | None = None       # 0..1
    line_thickness: float | None = None # line width in screen-space pixels
```

Canonical default: `PointPathStyle(color="#ffffff", opacity=1.0, line_thickness=2.0)`

??? note "Line thickness"
    `line_thickness` is a **screen-space pixel width** rendered via three.js
    `Line2` fat lines, so it stays constant on screen regardless of zoom.
    Per-vertex variable thickness is not supported — this can be added later
    via custom ribbon/tube geometry.

## Adding to a Visualizer

`PointPath` is a `SceneEntity` — use it with `add()`, `update_entity()`, and `update()` just like any geometry entity:

```python
trail = PointPath(max_points=100, pop_colors=False,
                  default_colors=gradient_colors("#440000", "#ffaa00", 100))
for _ in range(100):          # pre-fill so it draws immediately
    trail.add((0, 0, 0))

trail_id = viz.add(trail, style=PointPathStyle(line_thickness=2))

# In animation loop:
trail.add((x, y, z))
viz.update_entity(trail_id, trail)
viz.flush()
```

When using `update_entity()`, the `PointPath` instance is passed through
`:meth:`~pytanga.viz.Visualizer._resolve` unchanged — no MV analysis is attempted.

## Updating Style

Use `update_style()` to change properties of an existing PointPath without
rebuilding the geometry:

```python
from pytanga.viz import PointPathStyle

# Change line thickness and opacity
viz.update_style(trail_id, PointPathStyle(line_thickness=3, opacity=0.7))

# Change only the color
viz.update_style(trail_id, PointPathStyle(color="#ff8844"))
```

## Complete Example: Object Trail

See the ready-to-run example:

```
uv run python py/examples/viz/demo_point_path_trail.py
```

A point orbits in a circle with a 150-point gradient trail using
`pop_colors=False`. The trail transitions from dark red at the tail to
bright orange at the head, while the point shifts through the fixed color
positions.