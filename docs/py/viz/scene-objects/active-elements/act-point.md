# ActPoint

`ActPoint` is a self-registering interactive point that can be dragged
with the mouse. It creates a `Point` geometry entity and registers its own
interaction handler automatically. In 3D it exposes four standard drag-mode
triggers; in 2D (`space_dim=2`) the unmodified drag defaults to the XY plane.

## Quick Start

```python
from pytanga.viz import ActPoint, Visualizer
from pytanga.geometry import Point

viz = Visualizer()
ap = ActPoint(Point(0, 0, 2))
viz.add(ap, color="#ff4444")
viz.run()
```

The point can be dragged with the left mouse button. Modifier keys switch
the drag constraint plane:

| Modifier | Drag Plane |
|----------|-----------|
| *(none)* | View plane (screen-parallel) |
| `Shift` | XY plane (Z-locked) |
| `Ctrl` | XZ plane (Y-locked) |
| `Ctrl+Shift` | YZ plane (X-locked) |

## Constructor

```python
ActPoint(
    x: float | Point,
    y: float = 0.0,
    z: float = 0.0,
    *,
    drag_mode: DragMode | None = None,
    act_style: ActPointStyle | None = None,
    handler: ActHandler | None = None,
    on_drag_start: ActEventHandler | None = None,
    on_drag_end: ActEventHandler | None = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `x` | `float \| Point` | *(required)* | X coordinate, or a `Point` instance (then `y`/`z` are ignored) |
| `y` | `float` | `0.0` | Y coordinate |
| `z` | `float` | `0.0` | Z coordinate |
| `drag_mode` | `DragMode \| None` | `None` | Constrains the unmodified left-button drag to a single plane |
| `act_style` | `ActPointStyle \| None` | `None` | Hover highlighting / interactive feedback |
| `handler` | `ActHandler \| None` | `None` | Move-phase callback invoked before the default movement |
| `on_drag_start` | `ActEventHandler \| None` | `None` | Callback invoked when a drag starts |
| `on_drag_end` | `ActEventHandler \| None` | `None` | Callback invoked when a drag ends |

The point's visual style (colour, size, opacity) and an optional text `label`
are set via `viz.add(ap, color=..., style=..., label=...)`, not on the
constructor.

## Drag Mode

Pass `drag_mode=` to constrain the unmodified left-button drag to a single
plane instead of the four standard modifier-switched planes. This keeps the
point on that plane throughout the gesture:

```python
from pytanga.viz import DragMode

ap = ActPoint(Point(1.0, 2.0, 0.0), drag_mode=DragMode.XY_PLANE)
```

When `drag_mode` is set, the primary unmodified left-button trigger uses that
plane and no modifier-based alternate triggers are registered.

When `drag_mode` is omitted (the default `None`), the behaviour depends on the
scene dimension:

- In a 3D visualizer, the four standard triggers remain available, as shown
  in the table above.
- In a 2D visualizer (`VisualizerApp(space_dim=2)` or
  `Visualizer(space_dim=2)`), the unmodified left-button drag automatically
  uses `XY_PLANE` instead of the view plane. This prevents an unmodified drag
  on the view plane of a tilted camera from changing the point's Z coordinate.

## Labels

Pass `label=` to `viz.add()` to attach a text label to the point, just like
any other entity (supporting `label_style`, `attach_to`, and `parent_id`):

```python
ap = ActPoint(Point(0, 0, 2))
eid = viz.add(ap, color="#ff4444", label="P")
```

Removing the point also removes its attached label.

## Custom Handler

```python
from pytanga.viz import ActHandler

async def my_handler(event, ap):
    # event: DragEvent — carries world_position (Point), world_delta (Direction),
    #        camera (Camera), drag_mode, modifiers, etc.
    # ap:    ActPoint — has .point (current Point), .entity_id, .viz_handle

    # Update other scene objects based on the drag:
    new_pos = event.world_position
    ap.viz_handle.update_entity(some_line_id, Line.from_points(ap.point, new_pos))

    return False   # let ActPoint move the point and flush
    # return True  # fully handled; no default move, no automatic flush

ap = ActPoint(Point(0, 0, 2), handler=my_handler)
```

## Drag Lifecycle Handlers

The `handler` callback runs on every drag **move**. To observe the start and
end of a drag, pass `on_drag_start` and/or `on_drag_end`:

```python
async def on_start(event, ap):
    # Drag began — e.g. remember the initial position or highlight the point.

async def on_end(event, ap):
    # Drag finished — e.g. commit the final position or clear the highlight.

ap = ActPoint(
    Point(0, 0, 2),
    handler=my_handler,
    on_drag_start=on_start,
    on_drag_end=on_end,
)
```

These lifecycle handlers receive the same `(event, ap)` arguments as the move
handler, but their return value is ignored — they are pure notifications and
never override the default movement. `event.event_type` is
`InteractionEventType.DRAG_START` / `DRAG_END` respectively.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `point` | `Point` | Current position (updated on every drag move) |
| `entity` | `Point` | Same as `point` — the geometry entity rendered in the scene |
| `entity_id` | `str` | The scene entity ID assigned by the visualizer |
| `viz_handle` | `VizSceneHandle \| None` | Handle for scene operations (update, flush, etc.) |
| `interaction_config` | `InteractionConfig` | Drag triggers (standard four, or a single `drag_mode`-constrained trigger) with `throttle_ms=40` |

## Interaction Configuration

In a 3D visualizer with `drag_mode=None`, the config uses four drag triggers
on the left mouse button:

```python
InteractionConfig(
    enabled=True,
    triggers=[
        InteractionTrigger(event_type=DRAG, mouse_button=LEFT,
                          drag_mode=VIEW_PLANE),
        InteractionTrigger(event_type=DRAG, mouse_button=LEFT,
                          modifiers={SHIFT}, drag_mode=XY_PLANE),
        InteractionTrigger(event_type=DRAG, mouse_button=LEFT,
                          modifiers={CTRL}, drag_mode=XZ_PLANE),
        InteractionTrigger(event_type=DRAG, mouse_button=LEFT,
                          modifiers={CTRL, SHIFT}, drag_mode=YZ_PLANE),
    ],
    throttle_ms=40,
)
```

When `drag_mode` is set, the config instead registers a single unmodified
left-button trigger with that mode:

```python
InteractionConfig(
    enabled=True,
    triggers=[
        InteractionTrigger(event_type=DRAG, mouse_button=LEFT,
                          drag_mode=XY_PLANE),
    ],
    throttle_ms=40,
)
```

To customise the triggers further (e.g., use right button instead, or
different modifier keys), subclass `ActPoint` and override
`interaction_config`.

## See Also

- [Active Elements Overview](index.md) — common behaviour, handler contract, writing custom active elements
- [Object Interaction](../../visualizer/object-interaction.md) — low-level interaction API
- [`act_point.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/interaction/act_point.py) — full working example with projection lines