# Axes & Grid

Grid and axes are explicit scene objects, not hard-coded frontend helpers.
They work identically in the live viewer, in HTML export, and in glTF
export (without text labels).

## Axis

A single coordinate axis from `start` to `end` with ticks and optional
value labels.  The `Axes3D` and `Axes2D` convenience classes expand into
individual `Axis` objects.

```python
from pytanga.viz import Axis

viz.add(Axis(start=(0, 0, 0), end=(10, 0, 0), major_interval=2.0, label="X"))
```

| Field | Type | Description |
|-------|------|-------------|
| `start` | `(float, float, float)` | Start point |
| `end` | `(float, float, float)` | End point |
| `major_interval` | `float` | Spacing between major ticks |
| `minor_interval` | `float \| None` | Spacing between minor ticks |
| `label_at_major` | `bool` | Draw a value label at each major tick |
| `label_format` | `str` | Python format specifier (e.g. `.2f`) |
| `label_size` | `float \| None` | Font size in px for CSS2D labels |
| `show_ticks` | `bool` | Draw tick marks |
| `label` | `str \| None` | Axis name label near the end |

## Grid

A coordinate grid in a plane spanned by `dir_u` and `dir_v`.

```python
from pytanga.viz import Grid

viz.add(Grid(dir_u=(1, 0, 0), dir_v=(0, 1, 0), range_u=10.0, range_v=6.0))
```

| Field | Type | Description |
|-------|------|-------------|
| `origin` | `(float, float, float)` | Grid centre |
| `dir_u` | `(float, float, float)` | First in-plane direction |
| `dir_v` | `(float, float, float)` | Second in-plane direction |
| `range_u` | `float` | Total extent along `dir_u` |
| `range_v` | `float` | Total extent along `dir_v` |
| `interval_u` | `float` | Spacing between lines parallel to `dir_v` |
| `interval_v` | `float` | Spacing between lines parallel to `dir_u` |

## Convenience Classes

### Axes3D

Expands to three `Axis` objects along `dir_u`, `dir_v`, and `dir_w`.

```python
from pytanga.viz import Axes3D

viz.add(Axes3D(range_u=5, range_v=5, range_w=5, labels=("X", "Y", "Z")))
```

### Axes2D

Expands to two `Axis` objects along `dir_u` and `dir_v`.

```python
from pytanga.viz import Axes2D

viz.add(Axes2D(range_u=5, range_v=5, labels=("X", "Y")))
```

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
