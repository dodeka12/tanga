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

## Usage Pattern

```python
from pytanga.viz import Visualizer
from pytanga.viz._active import ActPoint
from pytanga.geometry import Point

viz = Visualizer()

# Without custom handler — just drag the point:
ap = ActPoint(Point(1, 2, 3), color="#ff4444")
viz.add(ap)

# With custom handler — update other entities on every drag:
async def on_move(event, ap):
    # event.world_position is a Point
    # ap.point is the current position
    # ap.viz_handle gives access to the scene for updates
    return False  # let ActPoint move the point and flush

ap = ActPoint(Point(0, 0, 2), custom_handler=on_move)
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

## Writing Custom Active Elements

Subclass `ActSceneObject` and implement three properties:

```python
from pytanga.viz._active import ActSceneObject, _default_drag_triggers
from pytanga.viz._interaction import InteractionConfig, MouseButton
from pytanga.geometry import Sphere, Point

class ActSphere(ActSceneObject):
    def __init__(self, sphere, *, custom_handler=None):
        super().__init__(custom_handler=custom_handler)
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

- [Object Interaction](../../visualizer/object-interaction.md) — the low-level interaction API
- [`act_point.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/interaction/act_point.py) — reusable ActPoint example
- [`drag_point.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/interaction/drag_point.py) — explicit low-level API example