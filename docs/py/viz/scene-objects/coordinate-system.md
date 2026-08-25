# CoordinateSystem

The `CoordinateSystem` helper builds a complete plotting coordinate system —
grid, axes (with value labels), an optional background plane, and plotted
point paths — inside a single `VizGroup`. It is **not** a scene object itself;
it owns the group and the `VizObjectRef`s of the objects it creates, and
updates them in place when the axis ranges change.

It supports **logarithmic scales for any base** while keeping the underlying
world coordinates linear: tick positions and labels are computed in Python and
the data → world conversion is applied before plotting.

For runnable examples showing the effect of several parameter combinations, see
[coordinate-system.ipynb](coordinate-system.ipynb).

## Quick Start

```python
from pytanga.viz import Visualizer, CoordinateSystem, PointPathStyle

viz = Visualizer(add_default_axes=False, add_default_grid=False)

cs = CoordinateSystem(viz, xlim=(0.1, 1000), ylim=(1, 1e6),
                      xscale="log", yscale="log")

xs = [0.1 * (10 ** (0.1 * i)) for i in range(40)]
cs.plot(xs, [x * x for x in xs], color="#ffcc00",
        style=PointPathStyle(line_thickness=3))

viz.show()
viz.wait()
```

`CoordinateSystem` accepts a `Visualizer` (main scene) or a `VizSceneHandle`
(named scene), e.g. `CoordinateSystem(viz.scene("plots"), ...)`.

## Data coordinate system

| Parameter | Type | Description |
|-----------|------|-------------|
| `xlim` / `ylim` | `(lo, hi)` | Data range per axis. `None` auto-derives from a configured 2D camera rect, or defaults to `(-5, 5)` (`(0.1, 100)` for log). |
| `xscale` / `yscale` | `"linear"` \| `"log"` \| `Scale` | Axis scale. |
| `size` | `(size_x, size_y)` | External world extent of the plot (plane width/height). `None` (or a `None` element) derives that axis from the data range. |
| `align` | `(ax, ay)` | Fractional point of the plot plane that coincides with `position`: `(0, 0)` = bottom-left corner, `(1, 1)` = top-right. Default `(0.5, 0.5)` (centre). |
| `axis_origin` | `(x, y)` | Data point where the two axes cross. `None` (or a `None` element) uses that axis' min edge (the spine layout). |
| `min_x_span` | `float` | Minimum x-range span used when auto-fitting the x axis from registered plots (default `5.0`). |
| `base` | `float` | Log base when a scale is given as `"log"` (default `10`). |
| `value_format` | `str` | Python format specifier for tick labels (default `".4g"`). |
| `labels` | `(str, str)` | Axis name labels (default `("x", "y")`). |

### Logarithmic scales

```python
cs = CoordinateSystem(viz, xlim=(0.1, 100), ylim=(1, 10000),
                      xscale="log", yscale="log")   # base 10
cs = CoordinateSystem(viz, xlim=(1, 64), ylim=(1, 64),
                      xscale="log", yscale="log", base=2)  # base 2
```

Log axes must have a strictly positive range. Tick labels are integer powers of
the base (e.g. `0.1, 1, 10, 100`). The world coordinate of a value `v` is
`log(v, base)`; everything is converted automatically by `plot()` /
`transform()`.

The underlying scale classes are available for direct use:

```python
from pytanga.viz import Scale, LinearScale, LogScale

LogScale(2).to_world(8)   # 3.0
```

### External vs internal dimensions

`size` sets the **physical** extent of the plot in world/embedding units,
independently of the data range. The data range (`xlim`/`ylim`) is stretched
onto that size, so a plane can be e.g. 2×1 world units while the data ranges
from 0 to 4π:

```python
import math
cs = CoordinateSystem(viz, xlim=(0, 4 * math.pi), ylim=(-4, 3),
                      size=(2.0, 1.0),
                      position=(1, 2, 3), normal=(0, 1, 0), up=(0, 0, 1))
```

With `size=None` (the default) each axis keeps its data-derived extent (the
current behaviour). `size` affects only the plot geometry — never the camera.

`align` controls **where** the plane sits relative to `position`: with
`align=(0, 0)` the bottom-left corner of the plane is at `position`, with
`align=(1, 1)` the top-right corner is there, and with the default
`align=(0.5, 0.5)` the plane is centred on `position`.

## 2D: auto span & camera

In 2D (`Visualizer(space_dim=2)` or a 2D camera), `CoordinateSystem` spans the
camera view by default and, when no camera is configured, computes and sets a
default `View2DConfig` with a pixel border so the axis labels stay visible:

```python
viz = Visualizer(space_dim=2, add_default_axes=False, add_default_grid=False)
cs = CoordinateSystem(viz, xlim=(0.1, 100), ylim=(0.1, 100),
                      xscale="log", yscale="log")
# → sets a centered View2DConfig with border_px=60
```

Control this with:

| Parameter | Default | Effect |
|-----------|---------|--------|
| `camera` | `"auto"` | `"auto"` sets a framing camera only if none is configured; `True` always sets/updates it; `False` never touches it. |
| `border_px` | `60.0` | Pixel margin on all sides (applied by the frontend). |
| `border_world` | `0.0` | Additional world-unit margin. |

The default `AxisStyle`s place the **x** value labels below the axis (with the
name label further down) and the **y** value labels to the left (right-aligned,
with a 90°-rotated name label). Override via `x_style`/`y_style`.

If you already set a `View2DConfig` on the visualizer, `xlim=None`/`ylim=None`
reuse its visible rectangle.

### Manual 2D placement

If you pass `size`, the 2D plot stops auto-configuring the camera and instead
places the plot in the 2D world using `position`, `align`, and `up` (the
in-plane vertical direction, default `(0, 1, 0)`). This lets you draw several
plots side by side, or next to a geometric animation:

```python
cs = CoordinateSystem(viz, xlim=(0, 10), ylim=(-1, 1), size=(2.0, 1.0),
                      position=(1, 0, 0), up=(0, 1, 0))
```

## 3D: background plane placement

In 3D the whole system (background plane + grid + axes + plotted paths) lives
in one group, placed/oriented with `position`, `normal`, and `up`:

```python
import math
cs = CoordinateSystem(viz,
                      xlim=(0, 4 * math.pi), ylim=(-1.5, 1.5),
                      position=(0, 1, 0), normal=(0, 1, 0.4), up=(0, 0, 1))
cs.plot(xs, [math.sin(x) for x in xs], color="#44ff44")
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `position` | `(0, 0, 0)` | World point the plot plane sits at (combined with `align`). |
| `normal` | `(0, 0, 1)` | Plot-plane normal (the group's local +z). |
| `up` | `(0, 1, 0)` | In-plane vertical direction. |
| `plane` | `None` | Whether to draw the background plane. `None` auto-enables in 3D and disables in 2D. |

The plane is sized to the coordinate system's world span (derived from
`xlim`/`ylim` + scales, or the explicit `size`). A 3D coordinate system **never
sets the camera** — place and aim it yourself; the plot is meant to sit inside a
larger 3D scene. `axis_origin=(x, y)` moves where the axes cross (in data
coordinates); the default keeps the spine layout (x-axis along the bottom,
y-axis along the left).

## Plotting & transformation

```python
# Map a data point to its centred in-plane coordinate.
lx, ly = cs.to_local(10.0, 100.0)

# Map a data point to its embedded 3D world position (applies the group transform).
x, y, z = cs.to_world(10.0, 100.0)

# Map data series to group-local 3D points (inherits the group transform).
pts = cs.transform(xs, ys)

# Plot a series as a PointPath child of the data group (data coordinates).
ref = cs.plot(xs, ys, color="#ffcc00", style=PointPathStyle(line_thickness=3))
```

## Annotations & the data group

Every data-space object (`plot`, `add_plot`, and the annotation helpers below)
is a child of an inner **data group** whose transform maps data coordinates onto
the plot plane. For linear axes the group is a pure translate+scale, so you can
draw directly in data coordinates; for log axes the group handles only the
affine part, so the `log` is still applied in Python (`to_data()`).

The inner group is exposed as `cs.data_group` (a `VizObjectRef`) for custom
drawings:

```python
# Map a data point to data-group coordinates (log-mapped for log axes).
wx, wy = cs.to_data(10.0, 100.0)

# Draw a custom annotation in data coordinates.
path = PointPath()
path.add((1.0, 0.0))
path.add((3.0, 2.0))
cs.data_group.new(path, color="#ffffff")
```

### vline / hline

Draw (and animate) vertical/horizontal marker lines at fixed data values:

```python
# Create (or update, by name) a vertical line at x=3 spanning the current ylim.
v = cs.vline(x=3.0, name="cursor", color="#ff5555")

# Create (or update) a horizontal line at y=0 spanning the current xlim.
h = cs.hline(y=0.0, name="zero", color="#8888ff")

# Move the vertical line each frame (animation):
cs.vline(x=t, name="cursor")

# Remove a named line:
cs.remove_vline("cursor")
cs.remove_hline("zero")
```

- `vline(x, *, name=None, y0=None, y1=None, color=None, style=None)` and
  `hline(y, *, name=None, x0=None, x1=None, color=None, style=None)` create a
  line (or update it in place when `name` is given) and return its
  `VizObjectRef`. `y0/y1` (resp. `x0/x1`) default to the current `ylim` (resp.
  `xlim`).
- Without `name`, each call creates a new line.
- `remove_vline(name)` / `remove_hline(name)` remove a named line.

### line

Draw a line between two arbitrary data points, each given as an `(x, y)`
2-tuple or a `Point()` instance:

```python
from pytanga.geometry.entities import Point

cs.line((1.0, 0.0), (3.0, 2.0), color="#ffffff")
cs.line(Point(1.0, 0.0), Point(3.0, 2.0), name="seg", color="#ff88ff")
cs.line(Point(4.0, -1.0), Point(6.0, 1.0), name="seg")  # update in place
cs.remove_line("seg")
```

- `line(start, end, *, name=None, color=None, style=None)` creates a line (or
  updates it in place when `name` is given) between `start` and `end`, and
  returns its `VizObjectRef`.
- `remove_line(name)` removes a named line.

### point

Draw a point marker at a data location, given as an `(x, y)` 2-tuple or a
`Point()` instance:

```python
from pytanga.geometry.entities import Point
from pytanga.viz import PointStyle

cs.point((2.0, 0.5), color="#ffffff")
cs.point(Point(3.0, 1.0), name="marker", color="#ff8888", style=PointStyle(size=0.1))
cs.point(Point(4.0, -0.5), name="marker")  # update in place
cs.remove_point("marker")
```

- `point(p, *, name=None, color=None, style=None)` creates a point marker (or
  updates it in place when `name` is given) and returns its `VizObjectRef`.
- `remove_point(name)` removes a named point marker.
- The marker is added to the outer group at its local position (not the data
  group), so its `size` is not stretched by the data group's non-uniform scale.

> **Note:** `data_group` applies a non-uniform scale (it stretches data onto the
> plot's `size`), so it is ideal for paths/lines. The `point()` helper places
> shaded markers in the outer group (undistorted); for other shaded entities
> place them with `to_world()` instead.

See `py/examples/viz/demo_cs_annotations.py` for a full example.

## Live plots (trails)

For live data (e.g. a trail that grows every frame), register a `PointPath`
(in **data** coordinates) with `add_plot` and re-sync it each frame with
`update_plots`:

```python
trail = PointPath(max_points=600)
cs.add_plot(trail, color="#ffcc00", style=PointPathStyle(line_thickness=2),
            auto_x=True)

# each frame:
trail.add((t, value))
cs.update_plots()
viz.flush()
```

- `add_plot(path, *, color=None, style=None, auto_x=False)` registers the path
  and adds it to the group; the path's points are mapped onto the plot plane
  automatically.
- `update_plots()` re-syncs every registered path and, for `auto_x` paths, fits
  the x axis to their current x range with a minimum span of `min_x_span`
  (default `5.0`) — useful for a live time axis.
- `position`, `normal`, and `up` accept tuples or `Point()`/`Direction()`
  objects.

See `py/examples/viz/demo_pendulum_plot.py` for a full pendulum example.

## Updating in place

Changing a range rebuilds the children **in place** (same object IDs), so the
scene updates without re-adding objects:

```python
cs.xlim = (1, 1000)          # rescale the x axis (grid + axes + labels update)
cs.yscale = "log"            # switch the y axis to log
cs.base = 2                  # change the log base of both log axes
cs.size = (4, 2)             # change the external world/plane extent
cs.align = (0, 0)            # move the plane so its bottom-left corner is at `position`
cs.axis_origin = (0, 0)      # make the axes cross at the data origin
cs.position = (1, 2, 3)      # move the 3D plane
cs.normal = (0, 0, 1)        # re-orient the 3D plane
```

Styles are set at construction via `x_style`/`y_style` (`AxisStyle`),
`grid_style` (`GridStyle`), and `plane_style` (`PlaneStyle`). The group itself
is exposed as `cs.group` for further manipulation.
