# Phase 2 — Serializer & Scene Integration

**Prerequisites:** Phase 1 (interaction dataclasses exist)

**Goal:** Extend the serializer and `Scene` class so that `InteractionConfig`
objects attached to entities are included in the JSON output sent to the frontend.

---

## 1. Motivation

The frontend needs to know which entities are interactive and what events to
capture. This information travels as an `"interaction"` field inside the
entity's JSON representation in `scene_update` messages. The serializer is
the single point where Python entities become JSON, so it's the right place
to inject this field.

---

## 2. Modified File: `py/pytanga/viz/serializer.py`

### 2.1 Current State

The serializer produces JSON dicts for each entity with fields like `id`,
`kind`, `color`, `opacity`, `position`, etc. There is currently no
interaction-related field.

### 2.2 Required Change

After serializing the entity's standard fields, check if an
`InteractionConfig` exists for that entity ID. If so, add an `"interaction"`
field:

```python
# In the entity serialization function (e.g., _serialize_entity or
# serialize_scene_update), add after the entity dict is constructed:

def _serialize_entity(entity, *, interaction_configs: dict[str, InteractionConfig] | None = None):
    """Serialize one entity, optionally including its interaction config."""
    result = {
        "id": entity.id,
        "kind": entity.kind,
        # ... all existing fields ...
    }

    # Inject interaction config if present
    if interaction_configs:
        ic = interaction_configs.get(entity.id)
        if ic is not None and ic.enabled:
            result["interaction"] = ic.to_dict()

    return result
```

### 2.3 Alternative: Inline in Scene

Since `Scene.flush()` already constructs the list of entity dicts (via
`full_state()` or `flush()`), an alternative is to inject the
`"interaction"` field at that level rather than in the serializer. This
avoids threading `interaction_configs` through the serializer API.

**Recommendation:** Add the interaction injection in `Scene.flush()` so
the serializer remains focused on entity-geometry-to-JSON conversion.

---

## 3. Modified File: `py/pytanga/viz/scene.py`

### 3.1 Storage

Add a `_interaction_configs: dict[str, InteractionConfig]` dict to `Scene`:

```python
class Scene:
    def __init__(self, config, name=""):
        # ... existing fields ...
        self._interaction_configs: dict[str, InteractionConfig] = {}
```

### 3.2 Methods

```python
def set_interaction(self, object_id: str, ic: InteractionConfig) -> None:
    """Set or update the interaction config for an entity."""
    self._interaction_configs[object_id] = ic

def get_interaction(self, object_id: str) -> InteractionConfig | None:
    """Get the interaction config for an entity, or ``None``."""
    return self._interaction_configs.get(object_id)

def remove_interaction(self, object_id: str) -> None:
    """Remove the interaction config for an entity."""
    self._interaction_configs.pop(object_id, None)
```

### 3.3 Injection in `flush()` / `full_state()`

When building entity dicts, inject the interaction field:

```python
def flush(self, styles_map=None):
    # ... existing logic to build entity dicts ...
    for entity_dict in entity_dicts:
        ic = self._interaction_configs.get(entity_dict["id"])
        if ic is not None and ic.enabled:
            entity_dict["interaction"] = ic.to_dict()
```

### 3.4 Lifecycle

- **`remove(entity_id)`**: Also call `self.remove_interaction(entity_id)` to
  clean up stale configs.
- **`clear()`**: Also call `self._interaction_configs.clear()`.
- **`update_entity(entity_id, new_entity)`**: Interaction config persists
  (no change needed — it's tied to the entity ID, not the geometry).

---

## 4. Modified File: `py/pytanga/viz/serializer.py` (if needed)

If the serializer has a separate path for `scene_update` message construction
(which it does via `serialize_scene_update()`), ensure that the entity dicts
already contain the `"interaction"` field. Since we're injecting at the
`Scene.flush()` level, no serializer changes should be needed — the dict
already carries the field.

**Verify:** Check that `serialize_scene_update()` passes through unknown
fields (it should, since it adds `"id"`, `"kind"`, etc. via a template
but the entity dict from `Scene` may have additional fields).

---

## 5. Implementation Checklist

- [x] Add `_interaction_configs: dict` storage to `Scene.__init__()`
- [x] Add `Scene.set_interaction()`, `get_interaction()`, `remove_interaction()`
- [x] Inject `"interaction"` field into entity dicts in `Scene.flush()` / `full_state()`
- [x] Clean up interaction configs in `Scene.remove()` and `Scene.clear()`
- [x] Verify `serialize_scene_update()` passes through the `"interaction"` field
- [x] Write a test: create Scene, set interaction config, flush, verify JSON contains `"interaction"` key

---

## 6. Verification

- [x] `scene.set_interaction("abc", InteractionConfig(enabled=True))` → `scene.flush()` includes `"interaction"` in entity dict
- [x] `scene.set_interaction("abc", InteractionConfig(enabled=False))` → `"interaction"` field absent (disabled)
- [x] `scene.remove("abc")` → interaction config cleaned up
- [x] `scene.clear()` → all interaction configs cleared
- [x] `scene.update_entity("abc", new_entity)` → interaction config still present
