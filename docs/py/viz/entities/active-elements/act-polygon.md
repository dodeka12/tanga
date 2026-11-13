# ActPolygon

`ActPolygon` is a self-registering editable polygon rendered as a `PointPath`.
It spawns one `ActPoint` handle per vertex plus a centroid translate handle.
Ctrl+dragging the start or end vertex inserts a new endpoint; Ctrl+right-clicking
it deletes the endpoint.

## PointPath entity

`PointPath` is an ordered list of 3D points rendered as connected line segments
(a viz-only helper, no multivector representation). `ActPolygon` builds the body
from its vertex list and, when `closed=True`, appends the first vertex at the
end so the path closes.

## Quick Start

```python
from pytanga.viz import ActPolygon, PointPathStyle, SquarePointStyle, Visualizer
from pytanga.geometry import Point

viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)

poly = ActPolygon(
    [Point(50, 50, 0), Point(150, 60, 0), Point(140, 140, 0), Point(60, 120, 0)],
    closed=True,
    handle_style=SquarePointStyle(size=6, thickness=2),
)
viz.add(poly, style=PointPathStyle(color="#ff4444", line_thickness=2))
viz.run()
```

Drag a vertex to reshape; drag the centre handle to translate. Ctrl+drag the
start/end vertex to extend the path; Ctrl+right-click it to trim it.

## Constructor

```python
ActPolygon(
    points: list[Point],
    *,
    closed: bool = True,
    show_translate_handle: bool = True,
    handle_style: SquarePointStyle | None = None,
    end_handle_style: SquarePointStyle | None = None,
    auto_close: bool = False,
    close_tolerance: float | None = None,
    act_style: ActPointStyle | None = None,
    on_vertex_drag=None,  # Callable[[int, DragEvent, ActPolygon], Awaitable[bool]] | None
    on_translate=None,    # Callable[[DragEvent, ActPolygon], Awaitable[bool]] | None
    on_change=None,       # Callable[[list[Point]], None] | None
    on_click=None,        # ActClickHandler | None
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `points` | `list[Point]` | — | Initial vertex positions |
| `closed` | `bool` | `True` | Close the rendered path |
| `show_translate_handle` | `bool` | `True` | Add the centroid translation handle |
| `handle_style` | `SquarePointStyle \| None` | square marker | Visual style of the handles |
| `end_handle_style` | `SquarePointStyle \| None` | `handle_style` | Visual style of the start/end vertices |
| `auto_close` | `bool` | `False` | Fuse the two endpoints into one and close the path when an endpoint is dragged onto the other endpoint |
| `close_tolerance` | `float \| None` | `2 * handle size` | World-unit distance within which the endpoints count as coincident (derived from the handle `size` when `None`) |
| `act_style` | `ActPointStyle \| None` | `None` | Hover highlighting of the handles |
| `on_vertex_drag` | `Callable \| None` | `None` | Overrides vertex drag (incl. Ctrl insert); return `True` to fully handle |
| `on_translate` | `Callable \| None` | `None` | Overrides translation; return `True` to fully handle |
| `on_change` | `Callable \| None` | `None` | Fired after any change with the new vertex list |
| `on_click` | `ActClickHandler \| None` | `None` | Fired when the body is clicked (makes it selectable) |

## Editing

- **Move a vertex** — drag it (left mouse).
- **Extend the path** — hold Ctrl and drag the start (first) or end (last)
  vertex: the dragged position becomes the new endpoint.
- **Trim the path** — hold Ctrl and right-click the start or end vertex to
  delete it (a path never drops below two vertices).
- **Close the path** — with `auto_close=True`, drag an endpoint onto the other
  endpoint: the two endpoints fuse into one and the path closes (a closed
  polygon has no distinct start/end handles).

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `points` | `list[Point]` | Copy of the current vertex positions |
| `entity` | `PointPath` | Current path (body entity) |
| `entity_id` | `str` | Scene entity ID of the body |
| `viz_handle` | `VizSceneHandle \| None` | Handle for scene operations |

`remove()` / `clear()` remove the body and all handle entities.

## Vertex tags, selection, and segment colors

Each vertex has a stable identity, so its tag, selection, and segment colors
survive insert/prepend/delete/fuse edits (the public API works with indices,
which remap automatically).

| Member | Description |
|--------|-------------|
| `vertex_tags` | `list[str \| None]` of per-vertex tags (`None` = untagged) |
| `set_vertex_tag(i, tag)` / `set_vertex_tags(tags)` | Set one / all tags |
| `default_vertex_tag` | Constructor kwarg; tag assigned to vertices created later by Ctrl+drag insertion |
| `tagging` / `set_tagging(bool)` | Show tag colors on the vertex handles (default `False`) |
| `set_tag_color(tag, color)` | Explicit tag→color override; otherwise a deterministic `TAG_PALETTE` fallback |
| `selected_vertex` / `set_selected_vertex(i)` | The selected vertex index (`None` clears it) |
| `selected_handle_style` / `set_selected_handle_style(style)` | Custom marker for the selected vertex (default a yellow copy of the base handle style) |
| `select_on_click` | Select a vertex when its handle is clicked (default `True`) |
| `on_vertex_click(i, event, act)` | Async callback fired after a vertex click |
| `segment_count` | `n` for a closed polygon, `n-1` for an open one |
| `segment_colors` | `list[str \| None]` of per-segment overrides (segment `i` = vertex `i` → `i+1`) |
| `set_segment_colors(colors)` / `set_segment_color(i, color)` / `clear_segment_color(i)` | Set / clear segment colors |

Handle style precedence: endpoint style (unless tagging) → tag color (only in
tagging mode) → the selected style (which always wins).  Tag, selection, and
segment-color changes are visual only — they never fire `on_change`.

```python
poly = ActPolygon(
    [Point(0, 0, 0), Point(1, 0, 0), Point(1, 1, 0)],
    default_vertex_tag="1",
    tagging=True,
)
poly.set_tag_color("1", "#ff4444")
poly.set_tag_color("2", "#ff00ff")

poly.set_vertex_tag(1, "2")          # tag the middle vertex
poly.set_selected_vertex(1)          # select it (yellow marker)
poly.set_segment_color(0, "#ff00ff") # color segment 0 magenta
```

## See Also

- [Active Elements Overview](index.md)
- [ActRectangle2D](act-rectangle2d.md)
- [ActEllipse](act-ellipse.md)
