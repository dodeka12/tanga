# Image Interaction

`ImageCanvas` exposes pointer interaction through drag and click bindings.  The
canvas wraps its interactive image plane (`ActImagePlane`), so the second
argument to every handler is the `ImageCanvas` itself, and `event.world_position`
is in **pixel coordinates** (y-down).

## Bindings

Bind a mouse button (and optional modifier keys) to a handler:

```python
from pytanga.viz import DragBinding, ClickBinding, MouseButton, ModifierKey

DragBinding(MouseButton.LEFT, on_drag, ModifierKey.CTRL)   # ctrl+left drag
ClickBinding(MouseButton.LEFT, on_click)                   # plain left click
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `button` | `MouseButton` | The button that starts the drag / triggers the click |
| `handler` | `Callable` | Async callback (see below) |
| `modifiers` | `ModifierKey` (varargs) | All must be held; none → fires regardless |
| `enabled` | `bool` | `True` — set `False` to register a disabled binding and toggle it later |

The most specific binding (greatest number of required modifiers) wins over less
specific bindings and over the general `on_drag` handler.

## Handler signatures

- `on_drag(event: DragEvent, canvas: ImageCanvas) -> bool` — return `True` to
  mark the event handled.
- `on_drag_start(event, canvas)` / `on_drag_end(event, canvas)` — fire at the
  start/end of a drag.
- `on_click(event: ClickEvent, canvas: ImageCanvas) -> None`.

Bindings are passed as lists to the constructor, or you can use the convenience
keyword arguments `on_drag=` / `on_drag_start=` / `on_drag_end=` / `on_click=`:

```python
canvas = ImageCanvas(
    viz,
    on_drag_start=on_drag_start,
    drag_handlers=[DragBinding(MouseButton.LEFT, on_drag)],
)
```

`event.world_position` is a `Point` in the canvas's pixel frame, so the
horizontal/vertical position map directly to pixel columns/rows:

```python
async def on_drag(event, canvas):
    px, py = event.world_position.x, event.world_position.y
    canvas.set_uniform("u_contrast", 0.5 + 1.5 * px / width)
    return True
```

## Cursor and toggles

- `canvas.set_cursor("crosshair")` sets the CSS cursor over the canvas;
  `set_cursor(None)` clears it.
- `canvas.set_handler_enabled(bool)` / `set_click_enabled(bool)` enable/disable
  the general `on_drag`/`on_click` handlers.
- `canvas.refresh_interaction()` re-registers the interaction config — call it
  after mutating a `DragBinding.enabled` / `ClickBinding.enabled` flag so the new
  trigger set reaches the frontend.

The interactive plane is reachable via `canvas.act_plane`.

## Example — armed drag-to-draw rectangles

`py/examples/viz/image/rectangle_labeling.py` registers a **disabled** left-drag
binding, then a `ToolbarView` button toggles a mode flag: it flips
`binding.enabled`, calls `refresh_interaction()`, and switches the cursor to
`crosshair`.  Dragging draws a preview `Rectangle2D`; on release it is finalized
into an `ActRectangle2D` (corner handles resize, the centre handle translates).

```python
self._binding = DragBinding(MouseButton.LEFT, self._on_drag, enabled=False)
self.canvas = ImageCanvas(
    viz,
    drag_handlers=[self._binding],
    on_drag_start=self._on_drag_start,
    on_drag_end=self._on_drag_end,
)

def set_adding(self, adding: bool) -> None:
    self._binding.enabled = adding
    self.canvas.refresh_interaction()
    self.canvas.set_cursor("crosshair" if adding else None)
```

See also [Object Interaction](../interaction/object-interaction.md) for the
general `InteractionTrigger`/`InteractionConfig` API used on scene entities.
