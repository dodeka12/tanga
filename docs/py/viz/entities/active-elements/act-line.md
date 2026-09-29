# ActLine

`ActLine` is a self-registering interactive two-point line segment. It draws a
`Line` body (via `Line.from_points`) and spawns two endpoint `ActPoint` handles
plus a midpoint translate handle. A line always has exactly two points and is
never closed. The body itself is visual-only; `on_click` makes it selectable.

## Line entity

`Line` is a viz-only geometry data class (no multivector representation): an
`origin`, a `direction`, and an optional `length`. `Line.from_points(start, end)`
sets `length` to the segment length so the visualizer draws exactly the segment.
`ActLine` keeps the line as a finite segment via `start`/`end`.

## Quick Start

```python
from pytanga.viz import ActLine, LineStyle, Visualizer
from pytanga.geometry import Point

viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
line = ActLine(start=Point(10, 10, 0), end=Point(200, 100, 0))
viz.add(line, style=LineStyle(color="#ff4444", thickness=2))
viz.run()
```

Drag an endpoint to move it; drag the midpoint to translate the whole line.

## Constructor

```python
ActLine(
    start: Point | None = None,
    end: Point | None = None,
    *,
    show_translate_handle: bool = True,
    handle_style: PointStyle | None = None,
    translate_handle_style: PointStyle | None = None,
    act_style: ActPointStyle | None = None,
    on_endpoint_drag=None,  # Callable[[int, DragEvent, ActLine], Awaitable[bool]] | None
    on_translate=None,      # Callable[[DragEvent, ActLine], Awaitable[bool]] | None
    on_change=None,         # Callable[[Line], None] | None
    on_click=None,          # ActClickHandler | None
)
```

- `entity` / `line` return the current `Line`.
- `start` / `end` expose the two endpoints.
- `create_from_points(a, b)` builds a line from two points, implementing the
  `ShapeFromPoints` protocol.

## labelme

labelme `line` shapes (two points) map to `ActLine`; open `linestrip` shapes
map to `ActPolygon(closed=False)`. See [`pytanga.viz.labelme`](../labelme.md).
