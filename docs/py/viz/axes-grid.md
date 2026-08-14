# Axes & Grid

Grid and axes are explicit scene objects, not hard-coded frontend helpers.
They work identically in the live viewer, in HTML export, and in glTF
export (without text labels).

## Axis

A single coordinate axis from `start` to `end` with optional value labels.
There is no tick rendering; the name label is drawn at the end of the axis.

```python
from pytanga.viz import Axis

viz.add(Axis(start=(0, 0, 0), end=(10, 0, 0), major_interval=2.0, label="X"))
```

| Field | Type | Description |
|-------|------|-------------|
| `start` | `(float, float, float)` | Start point |
| `end` | `(float, float, float)` | End point |
| `major_interval` | `float` | Spacing between value labels |
| `minor_interval` | `float \| None` | Accepted, but minor ticks are not currently rendered |
| `label_at_major` | `bool` | Draw a value label at each major interval |
| `label_format` | `str` | Python format specifier (e.g. `.2f`) |
| `label_size` | `float \| None` | Font size in px for CSS2D labels |
| `show_ticks` | `bool` | Accepted, but tick marks are not currently rendered |
| `label` | `str \| None` | Axis name label near the end |
| `value_start` | `float` | Numeric value at `start` (defaults to `0`) |
| `value_step` | `float` | Numeric increment per world unit along `start` → `end` |

`AxisStyle` additionally controls the value labels:
`label_at_major` (bool, hide value labels when ``False``) and `label_style`
(a :class:`~pytanga.viz.LabelStyle` with `font_size`, `color`, `align`,
`offset_2d`, and `offset_local`).

For value labels, `offset_local` is a 3D offset in the axis local frame:

- `x` shifts the label **along** the axis,
- `y` shifts it **perpendicular** to the axis (this is the label separation;
  the sign/flip depends on the axis direction),
- `z` shifts it along the binormal ``cross(axis, perpendicular)``.

`offset_2d` and `align` remain screen-space pixel offset / text alignment
applied on top of the 3D position.

## Grid

A coordinate grid in a plane spanned by `dir_u` and `dir_v`.

```python
from pytanga.viz import Grid

viz.add(Grid(dir_u=(1, 0, 0), dir_v=(0, 1, 0), range_u=(-5, 5), range_v=(-3, 3)))
```

| Field | Type | Description |
|-------|------|-------------|
| `origin` | `(float, float, float)` | Grid anchor point. A 2D `(x, y)` pair is placed behind all other objects. |
| `dir_u` | `(float, float, float)` | First in-plane direction |
| `dir_v` | `(float, float, float)` | Second in-plane direction |
| `range_u` | `(float, float)` | `(min, max)` extent along `dir_u` |
| `range_v` | `(float, float)` | `(min, max)` extent along `dir_v` |
| `interval_u` | `float` | Spacing between lines parallel to `dir_v` |
| `interval_v` | `float` | Spacing between lines parallel to `dir_u` |

Rendering properties (color, opacity, line thickness) are set via the
dedicated style classes.  `line_thickness` is expressed in **screen-space
pixels** (constant on screen regardless of zoom) via three.js `Line2` fat
lines:

- `GridStyle` for :class:`~pytanga.viz.Grid`.
- `AxisStyle` for a standalone :class:`~pytanga.viz.Axis`.
- `Axes2DStyle` / `Axes3DStyle` for :class:`~pytanga.viz.Axes2D` /
  :class:`~pytanga.viz.Axes3D`, holding one `AxisStyle` per direction.

Styles are passed to `add()` as the `style` argument, or configured via
`default_styles`.  See [Styles](styles.md) for details.

```python
from pytanga.viz import Axes2D, Axes2DStyle, AxisStyle, Grid, GridStyle

viz.add(Grid(range_u=(-5, 5), range_v=(-3, 3)),
        style=GridStyle(color="#3a3a3a", line_thickness=1))
viz.add(
    Axes2D(range_u=(-5, 5), range_v=(-3, 3), labels=("X", "Y")),
    style=Axes2DStyle(
        u=AxisStyle(color="#ff6666"),
        v=AxisStyle(color="#6666ff"),
    ),
)
```

## Axes Groups

### Axes3D

A single scene object drawing up to six axis halves (a positive and negative
half for each of `dir_u`, `dir_v`, `dir_w`).  Each `range_*` is a
`(min, max)` pair defining the extent along the negative and positive side of
`origin`; a zero extent is skipped.  Style each direction independently via
`Axes3DStyle(u=..., v=..., w=...)`.

```python
from pytanga.viz import Axes3D

viz.add(Axes3D(range_u=(-5, 5), range_v=(-5, 5), range_w=(0, 5), labels=("X", "Y", "Z")))
```

### Axes2D

A single scene object drawing up to four axis halves for the two directions
`dir_u`, `dir_v`, using the same `(min, max)` pairs.  `origin` accepts a 2D
`(x, y)` pair, which is placed at a default z that sits in front of the grid
but behind other objects.  Passing a full 3D `(x, y, z)` origin preserves the
explicit z for custom layering.  Style each direction via
`Axes2DStyle(u=..., v=...)`.

```python
from pytanga.viz import Axes2D

viz.add(Axes2D(origin=(0, 0), range_u=(-5, 5), range_v=(-5, 5), labels=("X", "Y")))
```

The name label (e.g. `"X"`) is drawn on the positive half of a direction only,
while the negative half is drawn as a separate unlabeled axis whose value
labels count downward.  Both halves of a direction share that direction's
`AxisStyle`.

## Defaults

If you do not add any `Axis` or `Grid` objects to a scene, the visualizer
inserts a default `Axes3D` (or `Axes2D` for `space_dim=2`) and a `Grid`
the first time the scene is served:

```python
viz = Visualizer()        # 3D → default XYZ axes + XZ grid
viz = Visualizer(space_dim=2)  # 2D → default XY axes + XY grid
```

Adding at least one explicit `Axis` or `Grid` disables the automatic
defaults for that scene:

```python
viz = Visualizer()
viz.add(Axis((0, 0, 0), (4, 0, 0), label="X"))  # no auto grid/axes
```

Providing a custom camera configuration also disables the defaults, since
the automatic axes/grid assume an origin-centred auto-fit view:

```python
viz = Visualizer(camera=View2DConfig(xmin=0, xmax=2, ymin=0, ymax=1))  # no auto grid/axes
```
