# ActRectangle2D

`ActRectangle2D` is a self-registering interactive axis-aligned rectangle. It
draws a `Rectangle2D` body and spawns square `ActPoint` handles — four corners
for resizing and one centre handle for translating. All interaction happens
through the handles; the body itself is visual-only.

## Rectangle2D entity

`Rectangle2D` is a viz-only geometry data class (no multivector representation,
like `Box`/`RegularPolygon`). It lies in the plane perpendicular to `normal`
(default `+z`), centred on `center`, with full width/height `size` and an
in-plane `angle` (radians, default `0.0` = axis-aligned).

```python
from pytanga.geometry import Rectangle2D, Point

rect = Rectangle2D(center=Point(0, 0, 0), size=(200, 100))
```

`Rectangle2DStyle` controls its appearance — outline-only by default, with an
optional semi-transparent fill:

```python
from pytanga.viz import Rectangle2DStyle

style = Rectangle2DStyle(color="#ff4444", fill=True, fill_opacity=0.2, thickness=2)
```

The handles use `SquarePointStyle` (a `PointStyle` variant that renders a flat
square marker instead of a sphere), passable via `handle_style=`.

## Quick Start

```python
from pytanga.viz import ActRectangle2D, SquarePointStyle, Visualizer
from pytanga.geometry import Point

viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)

rect = ActRectangle2D(
    center=Point(50, 50, 0),
    size=(200, 100),
    handle_style=SquarePointStyle(size=6, thickness=2),
)
viz.add(rect, style=Rectangle2DStyle(color="#ff4444"))
viz.run()
```

Drag a corner to resize; drag the centre handle to translate. In 2D
(`space_dim=2`) the handles default to the XY plane.

## Constructor

```python
ActRectangle2D(
    center: Point | None = None,
    size: tuple[float, float] | None = None,
    *,
    show_translate_handle: bool = True,
    handle_style: SquarePointStyle | None = None,
    act_style: ActPointStyle | None = None,
    on_corner_drag: Callable[[int, DragEvent, ActRectangle2D], Awaitable[bool]] | None = None,
    on_translate: Callable[[DragEvent, ActRectangle2D], Awaitable[bool]] | None = None,
    on_change: Callable[[Rectangle2D], None] | None = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `center` | `Point \| None` | `(0, 0, 0)` | Centre of the rectangle |
| `size` | `(float, float) \| None` | `(1, 1)` | Full `(width, height)` |
| `show_translate_handle` | `bool` | `True` | Add the centre translation handle |
| `handle_style` | `SquarePointStyle \| None` | square marker | Visual style of the handles |
| `act_style` | `ActPointStyle \| None` | `None` | Hover highlighting of the handles |
| `on_corner_drag` | `Callable \| None` | `None` | Overrides the corner-resize behaviour; return `True` to fully handle |
| `on_translate` | `Callable \| None` | `None` | Overrides the translation behaviour; return `True` to fully handle |
| `on_change` | `Callable \| None` | `None` | Fired after any geometry change with the new `Rectangle2D` |

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `rectangle` / `entity` | `Rectangle2D` | Current rectangle (body entity) |
| `entity_id` | `str` | Scene entity ID of the body |
| `viz_handle` | `VizSceneHandle \| None` | Handle for scene operations |

`remove()` / `clear()` remove the body and all handle entities.

## Custom Handlers

The default behaviour can be overridden, mirroring `ActPoint`:

```python
async def on_corner_drag(i, event, rect):
    # i: 0..3 corner index; rect.rectangle is the current Rectangle2D
    return True   # fully handled — no default resize

rect = ActRectangle2D(
    center=Point(50, 50, 0),
    size=(200, 100),
    on_corner_drag=on_corner_drag,
    on_change=lambda r: print("rectangle changed", r),
)
```

## Drawing on an ImageCanvas

`ImageCanvas.draw_rectangle(on_done=…)` enters a drag-to-create mode: the next
drag on the image draws a preview `Rectangle2D`, and on drag end it is replaced
by an `ActRectangle2D` and `on_done(rect)` is called. It returns a `cancel()`
callable that aborts the mode.

```python
def on_rect(rect):
    print(f"drawn: {rect.rectangle}")

canvas.draw_rectangle(on_done=on_rect)
```

## See Also

- [Active Elements Overview](index.md) — common behaviour, handler contract
- [ActPoint](act-point.md) — the single-point active element
- [Image Canvas](../../../examples/viz/image/image_canvas.md) — the image display helper
