# Active Elements

Active elements are high-level convenience classes that create interactive
3D entities and register their own interaction handlers automatically.
They simplify the common case of "add a draggable X to the scene."

## Available Active Elements

| Class | Entity | Interaction | Page |
|-------|--------|-------------|------|
| `ActPoint` | Draggable `Point` | Left-drag on four constraint planes | [ActPoint](act-point.md) |

## Common Behaviour

All active elements inherit from `ActSceneObject` and share:

| Feature | Description |
|---------|-------------|
| Auto-registration | Triggers and handlers are set up automatically by `viz.add()` |
| Custom handler | Optional callback invoked before default movement; returns `bool` to signal full handling |
| Standard drag triggers | View-plane, XY, XZ, YZ with Shift/Ctrl modifiers (left mouse button) |
| Self-contained flush | Default handler calls `update()` + `flush()` after moving |
| Labels | `viz.add(ap, label=...)` creates an attached label, removed together with the entity |

## Usage Pattern

```python
from pytanga.viz import ActPoint, Visualizer
from pytanga.geometry import Point

viz = Visualizer()

# Without custom handler — just drag the point:
ap = ActPoint(Point(1, 2, 3))
viz.add(ap, color="#ff4444")

# With custom handler — update other entities on every drag:
async def on_move(event, ap):
    # event.world_position is a Point
    # ap.point is the current position
    # ap.viz_handle gives access to the scene for updates
    return False  # let ActPoint move the point and flush

ap = ActPoint(Point(0, 0, 2), handler=on_move)
viz.add(ap)

viz.run()
```

## Custom Handler Contract

```python
ActHandler = Callable[[DragEvent, ActSceneObject], Awaitable[bool]]
```

| Return value | Behaviour |
|-------------|-----------|
| `True` | Fully handled — no default movement, no automatic flush (handler is responsible) |
| `False` | Default behaviour runs: entity is moved to `event.world_position`, `update()` + `flush()` are called |

## Drag Lifecycle Handlers

In addition to the move-phase `handler`, an active element accepts two
notification callbacks for the start and end of a drag:

```python
ActEventHandler = Callable[[DragEvent, ActSceneObject], Awaitable[None]]

ap = ActPoint(
    Point(0, 0, 2),
    handler=on_move,
    on_drag_start=on_start,   # called on DRAG_START
    on_drag_end=on_end,       # called on DRAG_END
)
```

`on_drag_start` / `on_drag_end` receive the same `(event, ap)` arguments as the
move handler, but their return value is ignored — they observe the drag
lifecycle and never override the default movement.

## Writing Custom Active Elements

Subclass `ActSceneObject` and implement three properties:

```python
from pytanga.viz import ActSceneObject, InteractionConfig, MouseButton
from pytanga.viz._active import _default_drag_triggers
from pytanga.geometry import Sphere, Point

class ActSphere(ActSceneObject):
    def __init__(self, sphere, *, handler=None, on_drag_start=None, on_drag_end=None):
        super().__init__(
            handler=handler,
            on_drag_start=on_drag_start,
            on_drag_end=on_drag_end,
        )
        self._sphere = sphere

    @property
    def entity(self):
        return self._sphere

    @property
    def interaction_config(self):
        return InteractionConfig(
            enabled=True,
            triggers=_default_drag_triggers(MouseButton.LEFT),
            throttle_ms=40,
        )

    def _move_to(self, pos: Point):
        self._sphere = Sphere(pos, self._sphere.radius)
```

Then `viz.add(ActSphere(...))` will work automatically.

## See Also

- [Object Interaction](../../interaction/object-interaction.md) — the low-level interaction API
- [`act_point.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/interaction/act_point.py) — reusable ActPoint example
- [`drag_point.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/interaction/drag_point.py) — explicit low-level API example