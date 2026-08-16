# Phase 4 — Visualizer & VizSceneHandle User-Facing API

**Prerequisites:** Phase 1 (dataclasses + registry), Phase 2 (Scene integration), Phase 3 (server routing)

**Goal:** Add `set_interaction()` and `on_interaction()` methods to `Visualizer`
and `VizSceneHandle`, wire the interaction callback into the server, and
implement the `_dispatch_interaction_event()` dispatch path.

---

## 1. Motivation

The user interacts with the visualizer via `Visualizer` (for the main scene)
and `VizSceneHandle` (for named scenes). Both need to expose:
- `set_interaction(object_id, config)` — configure which events are captured
- `on_interaction(object_id, event_type, handler)` — register an async handler

The `Visualizer` also needs to bridge incoming WebSocket events from the
server into the `InteractionHandlerRegistry`.

---

## 2. Modified File: `py/pytanga/viz/visualizer.py`

### 2.1 Storage

Add to `__init__()`:

```python
# Interaction handler registry (already exists from Phase 1 via _controls.py import)
# The self._handler_registry is a ControlHandlerRegistry — we need a separate
# InteractionHandlerRegistry for object interaction.
from ._interaction import InteractionHandlerRegistry

self._interaction_registry = InteractionHandlerRegistry()
self._interaction_configs: dict[str, dict[str, InteractionConfig]] = {}  # scene_name → object_id → config
```

### 2.2 Public Methods

```python
def set_interaction(
    self,
    object_id: str,
    config: InteractionConfig,
    *,
    scene_name: str = "",
) -> None:
    """Set the interaction configuration for an entity.

    The config is sent to the frontend with the next scene flush.
    """
    # Store for flush injection
    self._interaction_configs.setdefault(scene_name, {})[object_id] = config
    # Also store on the Scene object so Scene.flush() picks it up
    scene = self._scenes[scene_name]
    scene.set_interaction(object_id, config)
    # Mark entity as dirty so its interaction config is re-sent
    scene.mark_dirty(object_id)


def on_interaction(
    self,
    object_id: str,
    event_type: InteractionEventType,
    handler: Handler,
    *,
    scene_name: str = "",
) -> None:
    """Register an async handler for interaction events on an entity.

    Args:
        object_id: The entity ID.
        event_type: The event type to listen for.
        handler: Async callable receiving a ``ClickEvent``, ``DragEvent``,
            or ``ScrollEvent``.
        scene_name: Target scene (default ``""`` = main scene).
    """
    self._interaction_registry.register(object_id, event_type, handler)
```

### 2.3 Dispatch Method

```python
async def _dispatch_interaction_event(self, msg_type: str, event: ControlEvent) -> None:
    """Callback invoked by the server for incoming interaction events.

    Dispatches to the :class:`InteractionHandlerRegistry` for fire-and-forget
    handler execution with drag_move coalescing.
    """
    await self._interaction_registry.dispatch(event)
```

### 2.4 Wire into Server

In `start()` and `run()`, pass the dispatch callback to `VizServer.start()`:

```python
await self._server.start(
    flush_callback=...,
    config_callback=...,
    control_callback=self._dispatch_control_event,
    interaction_callback=self._dispatch_interaction_event,  # ← NEW
    # ... other callbacks ...
)
```

### 2.5 Cleanup on `clear()`

```python
def clear(self) -> None:
    self._scenes[""].clear()
    # Also clean up interaction handlers for the main scene
    # (handler registry is shared, but scene-specific configs need cleanup)
    self._interaction_configs.pop("", None)
```

---

## 3. Modified File: `py/pytanga/viz/_scene_handle.py`

### 3.1 Add Methods

```python
class VizSceneHandle:
    def set_interaction(self, object_id: str, config: InteractionConfig) -> None:
        """Set the interaction configuration for an entity in this scene."""
        self._viz.set_interaction(object_id, config, scene_name=self._name)

    def on_interaction(
        self, object_id: str, event_type: InteractionEventType, handler: Handler
    ) -> None:
        """Register an async handler for interaction events on an entity."""
        self._viz.on_interaction(object_id, event_type, handler, scene_name=self._name)
```

---

## 4. Modified File: `py/pytanga/viz/scene.py`

### 4.1 Add `mark_dirty()` Method

The `Scene` class needs a way to mark a single entity as dirty so its
data (including the interaction field) is re-sent on the next flush:

```python
def mark_dirty(self, entity_id: str) -> None:
    """Mark a single entity as dirty so it is included in the next flush."""
    # If the entity is tracked in a _dirty_ids set or similar, add it.
    # Alternatively, if the Scene tracks entities in a dict with a "dirty" flag,
    # set that flag.
    # Implementation depends on existing Scene internals.
```

---

- [x] Add `InteractionHandlerRegistry` import and instance to `Visualizer.__init__()`
- [x] Add `_interaction_configs` storage dict to `Visualizer`
- [x] Implement `Visualizer.set_interaction()` (store config, update Scene, mark dirty)
- [x] Implement `Visualizer.on_interaction()` (delegate to registry)
- [x] Implement `Visualizer._dispatch_interaction_event()` (delegate to registry.dispatch)
- [x] Wire `interaction_callback` into `VizServer.start()` calls in `start()` and `run()`
- [x] Add `set_interaction()` and `on_interaction()` to `VizSceneHandle`
- [x] Add `Scene.mark_dirty()` if not already present
- [x] Clean up interaction configs in `Visualizer.clear()`

---

## 6. Verification

- [x] `viz.set_interaction("abc", InteractionConfig(enabled=True, triggers=[...]))` → entity flush includes `"interaction"` field
- [x] `viz.on_interaction("abc", InteractionEventType.DRAG_MOVE, handler)` → handler called on drag events
- [x] `scene_handle.set_interaction("abc", config)` → works for named scenes
- [x] `viz.clear()` → interaction configs cleaned up
