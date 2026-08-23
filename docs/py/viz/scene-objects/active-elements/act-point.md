# ActPoint

`ActPoint` is a self-registering interactive point that can be dragged
with the mouse. It creates a `Point` geometry entity with four standard
drag-mode triggers and registers its own interaction handler automatically.

## Quick Start

```python
from pytanga.viz import Visualizer
from pytanga.viz._active import ActPoint
from pytanga.geometry import Point

viz = Visualizer()
ap = ActPoint(Point(0, 0, 2), color="#ff4444")
viz.add(ap)
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
    point: Point,
    *,
    color: str | None = None,
    size: float | None = None,
    opacity: float | None = None,
    custom_handler: ActHandler | None = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `point` | `Point` | *(required)* | Initial position |
| `color` | `str \| None` | `None` | CSS colour string (e.g. `"#ff4444"`). Override with `viz.default_styles["Point"].color` |
| `size` | `float \| None` | `None` | Point size in world units. Override with `viz.default_styles["Point"].size` |
| `opacity` | `float \| None` | `None` | Opacity (0–1). Override with `viz.default_styles["Point"].opacity` |
| `custom_handler` | `ActHandler \| None` | `None` | Optional async callback invoked before the default point movement |

## Custom Handler

```python
from pytanga.viz._active import ActHandler

async def my_handler(event, ap):
    # event: DragEvent — carries world_position (Point), world_delta (Direction),
    #        camera (Camera), drag_mode, modifiers, etc.
    # ap:    ActPoint — has .point (current Point), .entity_id, .viz_handle

    # Update other scene objects based on the drag:
    new_pos = event.world_position
    ap.viz_handle.update_entity(some_line_id, Line.from_points(ap.point, new_pos))

    return False   # let ActPoint move the point and flush
    # return True  # fully handled; no default move, no automatic flush

ap = ActPoint(Point(0, 0, 2), custom_handler=my_handler)
```

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `point` | `Point` | Current position (updated on every drag move) |
| `entity` | `Point` | Same as `point` — the geometry entity rendered in the scene |
| `entity_id` | `str` | The scene entity ID assigned by the visualizer |
| `viz_handle` | `VizSceneHandle \| None` | Handle for scene operations (update, flush, etc.) |
| `interaction_config` | `InteractionConfig` | Standard drag triggers with `throttle_ms=40` |

## Interaction Configuration

The default config uses four drag triggers on the left mouse button:

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

To customise the triggers (e.g., use right button instead, or different
modifier keys), subclass `ActPoint` and override `interaction_config`.

## See Also

- [Active Elements Overview](index.md) — common behaviour, handler contract, writing custom active elements
- [Object Interaction](../../visualizer/object-interaction.md) — low-level interaction API
- [`demo_act_point.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_act_point.py) — full working example with projection lines