# ActEllipse

`ActEllipse` is a self-registering interactive ellipse. It draws an `Ellipse`
body and spawns square `ActPoint` handles — two radius handles (along the
semi-axis directions), a centre translate handle, and a rim rotate handle. All
interaction happens through the handles; the body itself is visual-only.

## Ellipse entity

`Ellipse` is a viz-only geometry data class (no multivector representation). It
lies in the plane perpendicular to `normal` (default `+z`), centred on `center`,
with semi-axis radii `radius_u` / `radius_v`. Rotation is encoded in the
orthogonal in-plane directions `dir_u` / `dir_v`; when unset the ellipse is
axis-aligned. `ActEllipse` keeps an internal `angle` (radians) measured within
the plane perpendicular to `normal` (default `+z`), and derives the orthogonal
in-plane `dir_u` / `dir_v` from it.

```python
from pytanga.geometry import Ellipse, Point

ellipse = Ellipse(center=Point(0, 0, 0), radius_u=200, radius_v=100)
```

`EllipseStyle` controls its appearance (line-only; `thickness` is the line width
in pixels).

## Quick Start

```python
from pytanga.viz import ActEllipse, EllipseStyle, SquarePointStyle, Visualizer
from pytanga.geometry import Point

viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)

ellipse = ActEllipse(
    center=Point(160, 100, 0),
    radius_u=80,
    radius_v=40,
    handle_style=SquarePointStyle(size=6, thickness=2),
)
viz.add(ellipse, style=EllipseStyle(color="#ff4444"))
viz.run()
```

Drag a radius handle to resize; drag the centre handle to translate; drag the
rotate handle to rotate.

## Constructor

```python
ActEllipse(
    center: Point | None = None,
    radius_u: float = 1.0,
    radius_v: float = 0.5,
    *,
    angle: float = 0.0,
    normal: Direction | None = None,
    show_translate_handle: bool = True,
    show_rotate_handle: bool = True,
    handle_style: SquarePointStyle | None = None,
    act_style: ActPointStyle | None = None,
    on_radius_drag=None,   # Callable[[int, DragEvent, ActEllipse], Awaitable[bool]] | None
    on_translate=None,     # Callable[[DragEvent, ActEllipse], Awaitable[bool]] | None
    on_rotate=None,        # Callable[[DragEvent, ActEllipse], Awaitable[bool]] | None
    on_change=None,        # Callable[[Ellipse], None] | None
    on_click=None,         # ActClickHandler | None
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `center` | `Point \| None` | `(0, 0, 0)` | Centre of the ellipse |
| `radius_u` | `float` | `1.0` | Semi-axis radius along `dir_u` |
| `radius_v` | `float` | `0.5` | Semi-axis radius along `dir_v` |
| `angle` | `float` | `0.0` | In-plane rotation in radians, measured in the plane ⟂ `normal` |
| `normal` | `Direction \| None` | `+z` | Plane normal direction (the ellipse lies ⟂ this normal) |
| `show_translate_handle` | `bool` | `True` | Add the centre translation handle |
| `show_rotate_handle` | `bool` | `True` | Add the rim rotation handle |
| `handle_style` | `SquarePointStyle \| None` | square marker | Visual style of the handles |
| `act_style` | `ActPointStyle \| None` | `None` | Hover highlighting of the handles |
| `on_radius_drag` | `Callable \| None` | `None` | Overrides radius resize; return `True` to fully handle |
| `on_translate` | `Callable \| None` | `None` | Overrides translation; return `True` to fully handle |
| `on_rotate` | `Callable \| None` | `None` | Overrides rotation; return `True` to fully handle |
| `on_change` | `Callable \| None` | `None` | Fired after any geometry change with the new `Ellipse` |
| `on_click` | `ActClickHandler \| None` | `None` | Fired when the body is clicked (makes it selectable) |

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `ellipse` / `entity` | `Ellipse` | Current ellipse (body entity) |
| `center` | `Point` | Centre |
| `angle` | `float` | In-plane rotation in radians |
| `entity_id` | `str` | Scene entity ID of the body |
| `viz_handle` | `VizSceneHandle \| None` | Handle for scene operations |

`remove()` / `clear()` remove the body and all handle entities.

## See Also

- [Active Elements Overview](index.md)
- [ActRectangle2D](act-rectangle2d.md)
- [ActPolygon](act-polygon.md)
