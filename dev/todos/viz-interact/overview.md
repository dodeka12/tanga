# Object Interaction — Overview

**Goal:** Add interactive object manipulation to the Tanga 3D viewer. The frontend
captures pointer events (click, double-click, drag, scroll) on 3D entities and sends
them to the Python backend over WebSocket. The backend dispatches events to
user-registered async handlers, which can move, transform, or otherwise react to the
events. The frontend does **not** move objects autonomously — it only reports events.

**Prerequisites:** Working WebSocket server (Phase 1 viz), entity renderers (Phase 5 viz),
OrbitControls integration (existing `controls.js`).

---

## Architecture

```
User API:
  viz.set_interaction(point_id, InteractionConfig(
      enabled=True,
      triggers=[
          InteractionTrigger(event_type=InteractionEventType.DRAG,
                             mouse_button=MouseButton.LEFT),
          InteractionTrigger(event_type=InteractionEventType.CLICK,
                             mouse_button=MouseButton.LEFT,
                             modifiers={ModifierKey.CTRL}),
      ],
      throttle_ms=50,
  ))
  viz.on_interaction(point_id, InteractionEventType.DRAG_MOVE, on_drag_handler)
         │
         ▼  InteractionConfig → to_dict() → "interaction" field in entity JSON
         │
WebSocket message (scene_update) ──────────► JS frontend
                                                   │
                                                   ▼
                                     interaction.js
                                     ├── Tracks interactive objects
                                     ├── Raycaster on pointermove (only interactive objects)
                                     ├── Throttles events per (object_id, event_type)
                                     ├── Drag: setPointerCapture + controls.enabled=false
                                     ├── Click/dblclick: distance + time threshold
                                     ├── Scroll: non-passive wheel listener
                                     └── Computes delta_transform 4×4 matrix per drag event
                                                   │
WebSocket message ◄──────────────────────────────┘
  {"type": "interaction:drag_move", "object_id": "pt1", ...}
         │
         ▼  server.py → parses → interaction_callback
         │
         ▼  visualizer.py → _dispatch_interaction_event()
         │
         ▼  InteractionHandlerRegistry
         │  ├── Lookup handler for (object_id, event_type)
         │  ├── For drag_move: coalesce multiple pending events
         │  └── Fire-and-forget: asyncio.create_task(handler(event))
         │
         ▼  User's async handler receives ClickEvent | DragEvent | ScrollEvent
```

---

## Data Model — Enums

| Enum | Values |
|------|--------|
| `InteractionEventType` | `CLICK`, `DBLCLICK`, `DRAG_START`, `DRAG_MOVE`, `DRAG_END`, `SCROLL` |
| `MouseButton` | `LEFT` (0), `MIDDLE` (1), `RIGHT` (2) |
| `ModifierKey` | `CTRL`, `SHIFT`, `ALT` |

All enum values are serialized as their `value` (lowercase string) in JSON and
deserialized back to enum members on the Python side.

---

## Dataclass Hierarchy

| Dataclass | Fields |
|-----------|--------|
| `InteractionTrigger` | `event_type: InteractionEventType`, `mouse_button: MouseButton \| None`, `modifiers: frozenset[ModifierKey]` |
| `InteractionConfig` | `enabled: bool`, `triggers: list[InteractionTrigger]`, `throttle_ms: int` |
| `ControlEvent` (base) | `browser_id: str \| None` |
| `ClickEvent(ControlEvent)` | `object_id`, `event_type`, `mouse_button`, `modifiers`, `screen_position`, `world_position`, `world_normal` |
| `DragEvent(ControlEvent)` | `object_id`, `event_type`, `mouse_button`, `modifiers`, `screen_position`, `delta_pixels`, `world_position`, `delta_transform` |
| `ScrollEvent(ControlEvent)` | `object_id`, `event_type`, `modifiers`, `screen_position`, `delta_xy` |

---

## Utility Functions

```python
def apply_delta_transform(
    delta_pixels: tuple[float, float],
    transform: tuple[float, ...],   # 16-element 4×4 row-major matrix
) -> tuple[float, float, float]:
    """Convert pixel delta → world-space delta using the transform matrix.
    Equal pixel deltas produce equal-length world vectors in any direction."""

def extract_camera_directions(
    transform: tuple[float, ...],
) -> tuple[Direction, Direction, Direction]:
    """Extract right, up, and forward camera directions from the delta transform.
    Returns unit vectors of the view frame at the interaction point."""
```

---

## Delta Transform Matrix

A 4×4 row-major matrix mapping pixel deltas to world-space deltas at the
object's depth:

```
screen_scale = 2 * distance_to_camera * tan(fov/2) / viewport_height_px

row_0 = [right.x*scale,  right.y*scale,  right.z*scale,  0]   (screen +X → world)
row_1 = [up.x*scale,     up.y*scale,     up.z*scale,     0]   (screen -Y → world)
row_2 = [forward.x*scale, forward.y*scale, forward.z*scale, 0] (depth    → world)
row_3 = [0, 0, 0, 1]
```

Where `right`, `up`, `forward` are extracted from the camera's world matrix,
and `distance_to_camera` is the distance from camera to the intersection point.

**Key property:** Equal-length pixel deltas in any direction (screen-parallel or
depth) produce equal-length world-space vectors. This allows the handler to
apply intuitive, direction-agnostic transforms.

---

## Drag Move Coalescing (Backend)

When drag events arrive faster than the user handler can process them, multiple
`drag_move` events for the same object are coalesced:

- **`drag_start`** and **`drag_end`**: Flush any pending `drag_move` queue, then
  dispatch immediately.
- **`drag_move`**: If a handler is already running for that object, coalesce into
  the pending event (sum `delta_pixels`, keep latest `screen_position`,
  `world_position`, `delta_transform`).
- When the handler finishes and another `drag_move` is pending, coalesce all
  pending events from the queue into one and dispatch.

This avoids unbounded queue growth and reduces handler invocations during
rapid dragging.

---

## WebSocket Protocol

### Python → Browser (entity creation/update gains `interaction` field):

```json
{
  "type": "scene_update",
  "entities": [{
    "id": "abc123",
    "kind": "Point",
    "position": [1, 2, 3],
    "interaction": {
      "enabled": true,
      "triggers": [
        {"event_type": "drag", "mouse_button": "left", "modifiers": []},
        {"event_type": "click", "mouse_button": "left", "modifiers": ["ctrl"]}
      ],
      "throttle_ms": 50
    }
  }]
}
```

### Browser → Python (6 new message types):

| Message Type | Payload Fields |
|-------------|----------------|
| `interaction:click` | `browser_id`, `object_id`, `event_type`, `mouse_button`, `modifiers`, `screen_position`, `world_position`, `world_normal` |
| `interaction:dblclick` | Same as click |
| `interaction:drag_start` | `browser_id`, `object_id`, `event_type`, `mouse_button`, `modifiers`, `screen_position`, `delta_pixels`, `world_position`, `delta_transform` |
| `interaction:drag_move` | Same as drag_start |
| `interaction:drag_end` | Same as drag_start |
| `interaction:scroll` | `browser_id`, `object_id`, `event_type`, `modifiers`, `screen_position`, `delta_xy` |

---

## File Inventory

### New Files

| File | Content |
|------|---------|
| `py/pytanga/viz/_interaction.py` | Enums, dataclasses, handler registry, coalescing, utilities |
| `py/pytanga/viz/templates/interaction.js` | Frontend interaction capture, throttling, raycaster, delta_transform |
| `py/tests/viz/test_interaction_config.py` | Serialization + coalescing + utility tests |
| `py/tests/viz/test_interaction_registry.py` | Handler registry tests |
| `py/examples/viz/demo_drag_point.py` | Drag-a-point example |
| `py/examples/viz/demo_interactive_sphere.py` | Click + scroll example |

### Modified Files

| File | Change |
|------|--------|
| `py/pytanga/viz/serializer.py` | Append `"interaction"` field to entity JSON |
| `py/pytanga/viz/server.py` | Route 6 new `interaction:*` message types; parse → dataclass → dispatch |
| `py/pytanga/viz/visualizer.py` | `set_interaction()`, `on_interaction()`, dispatch, wire callback |
| `py/pytanga/viz/_scene_handle.py` | Expose interaction methods per scene |
| `py/pytanga/viz/__init__.py` | Export new public symbols |
| `py/pytanga/viz/templates/viewer.js` | Import `interaction.js`; wire entity lifecycle |
| `py/pytanga/viz/templates/controls.js` | Expose `controls.enabled` setter for drag conflicts |
| `docs/py/viz/index.md` | Add interaction docs link |

---

## Phases

| Phase | File | Summary |
|-------|------|---------|
| **1** | `phase1-interaction-dataclasses.md` | Enums, dataclasses, handler registry, coalescing, utilities |
| **2** | `phase2-serializer-integration.md` | Serializer + Scene integration for interaction configs |
| **3** | `phase3-server-routing.md` | Server WebSocket routing for 6 interaction message types |
| **4** | `phase4-visualizer-api.md` | Visualizer + VizSceneHandle user-facing API |
| **5** | `phase5-frontend-interaction.md` | New `interaction.js` frontend module |
| **6** | `phase6-viewer-wiring.md` | Wire into `viewer.js` + `controls.js` |
| **7** | `phase7-tests-examples-docs.md` | Tests, examples, documentation |

---

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Object removed while dragging | Frontend: `pointerup` fires `drag_end` (normal capture release). Backend: handler checks if entity still exists. |
| Multiple overlapping interactive objects | Raycaster picks frontmost hit only (standard behavior). |
| OrbitControls conflict during drag | `controls.enabled = false` on drag_start, re-enable on drag_end. |
| Drag leaves browser window | `setPointerCapture()` keeps delivering events. |
| Handler raises exception | Fire-and-forget task fails silently (logged). Coalesced queue is preserved. |
| `update_entity()` replaces geometry | Interaction config persists (tied to entity ID, not mesh). |
| `throttle_ms = 0` | No throttling — every event sent immediately. |
| Scroll on non-interactive object | Ignored (only triggers when hovering an interactive object with a scroll trigger). |
| kaTeX not relevant | Interaction system has no KaTeX dependency. |