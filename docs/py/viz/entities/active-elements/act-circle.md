# ActCircle

`ActCircle` is a self-registering interactive circle. It draws a `Circle` body
and spawns two `ActPoint` handles — a centre translate handle and one radius
handle. A circle is rotationally symmetric, so there is no rotate handle. The
body itself is visual-only; `on_click` makes it selectable.

## Circle entity

`Circle` is a viz-only geometry data class (no multivector representation): a
centre `center`, a `radius`, and a plane `normal` (default `+z`). `ActCircle`
keeps `normal = +z` and only edits `center`/`radius`.

## Quick Start

```python
from pytanga.viz import ActCircle, CircleStyle, Visualizer
from pytanga.geometry import Point

viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
circle = ActCircle(center=Point(160, 100, 0), radius=60, min_radius=5)
viz.add(circle, style=CircleStyle(color="#ff4444", thickness=2))
viz.run()
```

Drag the radius handle to resize (clamped to `min_radius`); drag the centre
handle to translate.

## Constructor

```python
ActCircle(
    center: Point | None = None,
    radius: float = 1.0,
    *,
    min_radius: float | None = None,
    show_translate_handle: bool = True,
    handle_style: PointStyle | None = None,
    translate_handle_style: PointStyle | None = None,
    act_style: ActPointStyle | None = None,
    on_radius_drag=None,   # Callable[[DragEvent, ActCircle], Awaitable[bool]] | None
    on_translate=None,     # Callable[[DragEvent, ActCircle], Awaitable[bool]] | None
    on_change=None,        # Callable[[Circle], None] | None
    on_click=None,         # ActClickHandler | None
)
```

- `entity` / `circle` return the current `Circle`.
- `center` / `radius` expose the current geometry.
- `create_from_points(center, rim)` builds a circle from a centre and rim point
  (radius = distance), implementing the `ShapeFromPoints` protocol.

## labelme

labelme `circle` shapes map to `ActCircle` (centre + rim point). See
[`pytanga.viz.labelme`](../labelme.md).
