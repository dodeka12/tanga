# Phase 3 — `visible_in` add-time scope

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add `visible_in=` to the scene add path and serialize it on the entity so panes
outside the scope skip construction.

## Files

- Edit: `py/pytanga/viz/_nodes.py` (`VizSceneObject` stores/serializes `visible_in`)
- Edit: `py/pytanga/viz/scene.py` (`Scene.new`/`Scene.add` accept + pass it)
- Edit: `py/pytanga/viz/_scene_handle.py` (`VizSceneHandle.new` forwards it)
- Edit: `py/pytanga/viz/visualizer.py` (`Visualizer.add` forwards it)
- Edit: `py/tests/viz/test_node_serialization.py`, `py/tests/viz/test_entity_visibility.py`

## Steps

- [x] **3.1 — Node model**
  - `VizSceneObject` accepts `visible_in: set[str] | None`; normalize to a set of
    non-empty strings (empty → `None`). Serialize it as `visible_in` (sorted)
    only in the full content payload, and omit it from patches.
- [x] **3.2 — Scene add path**
  - Thread `visible_in` through `Scene.new`/`Scene.add` into the `VizSceneObject`.
- [x] **3.3 — Public forwards**
  - `VizSceneHandle.new(...)` and `Visualizer.add(...)` accept and forward `visible_in`.
- [x] **3.4 — Tests**
  - Full serialization includes `visible_in` when set and omits it when empty;
    `VizSceneHandle.new(..., visible_in={"sv0"})` stores it on the node.

## Validation

`uv run pytest py/tests/viz/test_node_serialization.py py/tests/viz/test_entity_visibility.py -q`
