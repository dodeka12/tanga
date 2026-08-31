# Object Interaction

The `pytanga.viz` module supports pointer-based interaction with 3D entities
in the scene — clicking, double-clicking, dragging, and scrolling on objects.
The frontend sends events over WebSocket; the backend dispatches them to
user-registered async handlers.

## Overview

| Concept | Description |
|---------|-------------|
| [InteractionTrigger](#interactiontrigger) | Defines *when* an event fires: event type, mouse button, modifier keys, drag mode |
| [InteractionConfig](#interactionconfig) | Per-entity trigger list with throttling |
| InteractionEventType | `CLICK`, `DBLCLICK`, `DRAG_START`, `DRAG_MOVE`, `DRAG_END`, `SCROLL` |
| DragMode | Constraint plane for drag movement: `VIEW_PLANE`, `XY_PLANE`, `XZ_PLANE`, `YZ_PLANE` |
| [ClickEvent](#clickevent) | Fired on click or double-click; carries world position + normal |
| [DragEvent](#dragevent) | Fired during drags; carries world position, delta, and drag mode |
| [ScrollEvent](#scrollevent) | Fired on scroll while hovering an interactive object |
| [Camera](#camera) | Attached to every event; supports `project()` and `unproject()` for world↔screen conversion |

## Enabling Interaction

### InteractionTrigger

```python
from pytanga.viz import (
    InteractionTrigger, InteractionEventType, MouseButton,
    ModifierKey, DragMode,
)

# Left-click
trigger = InteractionTrigger(
    event_type=InteractionEventType.DRAG,
    mouse_button=MouseButton.LEFT,
)

# Ctrl+Shift drag on YZ plane
trigger = InteractionTrigger(
    event_type=InteractionEventType.DRAG,
    mouse_button=MouseButton.LEFT,
    modifiers=frozenset({ModifierKey.CTRL, ModifierKey.SHIFT}),
    drag_mode=DragMode.YZ_PLANE,
)
```

### InteractionConfig

```python
from pytanga.viz import InteractionConfig

config = InteractionConfig(
    enabled=True,
    triggers=[...],
    throttle_ms=40,   # max rate for drag_move / scroll events
    hover_emissive="#ffff44",  # optional glow color on hover
    hover_opacity=0.5,         # optional opacity override on hover
)
```

Optional hover feedback fields (`hover_emissive` glow color, `hover_scale`
uniform scale multiplier, `hover_opacity` opacity override) default to no
change when unset.

### Registering on a Specific Entity

```python
viz.set_interaction(point_id, config)
```

The config is sent to the frontend with the next `flush()`. Only meshes
with an attached `interaction` field in their JSON are picked up by the
raycaster.

## Event Dataclasses

All events inherit from `ControlEvent` and carry a `camera: Camera` field
for world↔screen coordinate conversion (see [Camera](#camera) below).

### ClickEvent

```python
@dataclass
class ClickEvent(ControlEvent):
    object_id: str
    event_type: InteractionEventType   # CLICK or DBLCLICK
    mouse_button: MouseButton
    modifiers: frozenset[ModifierKey]
    screen_position: tuple[float, float]
    world_position: Point              # world-space hit point
    world_normal: Direction            # surface normal at hit point
```

### DragEvent

```python
@dataclass
class DragEvent(ControlEvent):
    object_id: str
    event_type: InteractionEventType   # DRAG_START, DRAG_MOVE, DRAG_END
    mouse_button: MouseButton
    modifiers: frozenset[ModifierKey]
    screen_position: tuple[float, float]
    delta_pixels: tuple[float, float]  # pixel delta since last event
    world_position: Point              # current world position on constraint plane
    world_delta: Direction             # world-space delta since last event
    drag_mode: DragMode                # active constraint plane
```

### ScrollEvent

```python
@dataclass
class ScrollEvent(ControlEvent):
    object_id: str
    event_type: InteractionEventType   # SCROLL
    modifiers: frozenset[ModifierKey]
    screen_position: tuple[float, float]
    delta_xy: tuple[float, float]      # raw scroll delta (pixels)
```

## Drag Modes

| Mode | Constraint Plane | Behaviour |
|------|-----------------|-----------|
| `VIEW_PLANE` | Plane ⟂ camera view at drag-start depth | Screen-parallel movement |
| `XY_PLANE` | World XY plane at drag-start Z | Z-locked horizontal |
| `XZ_PLANE` | World XZ plane at drag-start Y | Y-locked ground plane |
| `YZ_PLANE` | World YZ plane at drag-start X | X-locked vertical plane |

## Registering Handlers

```python
from pytanga.viz import InteractionEventType

async def on_drag(event):
    p = event.world_position          # p is a pytanga.geometry.Point
    viz.update_entity(event.object_id, p)
    viz.flush()

viz.on_interaction(point_id, InteractionEventType.DRAG_MOVE, on_drag)
```

Handlers are **async** callables receiving the appropriate event type.
The handler registry coalesces rapid `DRAG_MOVE` events to prevent queue
build-up.

### Camera Caching

The frontend sends the full camera matrices only on `drag_start`, `click`,
`dblclick`, and `scroll`. For `drag_move` and `drag_end`, the backend
injects the cached camera from the preceding `drag_start`. Handlers always
see a fully populated `Camera`.

## Camera

Every event carries a `camera: Camera` field that stores the view and
projection matrices from the frontend. This enables world↔screen coordinate
conversion directly in Python handlers.

```python
@dataclass
class Camera:
    view: tuple[float, ...]          # 16 floats, column-major (matrixWorldInverse)
    view_inv: tuple[float, ...]      # 16 floats (matrixWorld)
    proj: tuple[float, ...]          # 16 floats (projectionMatrix)
    proj_inv: tuple[float, ...]      # 16 floats (projectionMatrixInverse)
    viewport_width: int
    viewport_height: int
    space_dim: int                   # 2 or 3
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `position` | `Point` | Camera world-space position |
| `right` | `Direction` | Camera right axis |
| `up` | `Direction` | Camera up axis |
| `view_dir` | `Direction` | Camera look-at direction (forward) |
| `focal_length_px` | `float` | Focal length in pixel units |

### `project(obj)`

Dispatches on the input type:

```python
# Point → screen pixel coordinates (x, y)
px, py = camera.project(world_point)

# Direction → screen pixel displacement (dx, dy)
px, py = camera.project(world_direction)
```

### `unproject(obj, depth)`

Dispatches on the input type:

```python
# Screen pixel point + world depth → world Point
wp = camera.unproject(Point(px, py), depth=5.0)

# Screen pixel displacement + world depth → world Direction
wd = camera.unproject(Direction(dx, dy), depth=5.0)
```

## Complete Example

```python
from pytanga.viz import Visualizer
from pytanga.viz import (
    InteractionConfig, InteractionTrigger,
    InteractionEventType, MouseButton, ModifierKey, DragMode,
)
from pytanga.geometry import Point

viz = Visualizer()
pid = viz.add(Point(0, 0, 2), color="#ff4444")

viz.set_interaction(pid, InteractionConfig(
    enabled=True,
    triggers=[
        InteractionTrigger(
            event_type=InteractionEventType.DRAG,
            mouse_button=MouseButton.LEFT,
            modifiers=frozenset({ModifierKey.SHIFT}),
            drag_mode=DragMode.XY_PLANE,
        ),
    ],
    throttle_ms=40,
))

async def on_drag(event):
    viz.update_entity(event.object_id, event.world_position)
    viz.flush()

viz.on_interaction(pid, InteractionEventType.DRAG_MOVE, on_drag)
viz.run()
```

## See Also

- [Active Elements](../entities/active-elements/index.md) — simplified high-level API for common interactive objects
- [`drag_point.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/interaction/drag_point.py) — full working example with four drag modes and projection lines