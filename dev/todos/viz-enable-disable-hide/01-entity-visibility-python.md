# Phase 1 — Entity visibility (Python model + API)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make `VizNode.visible` actually drive rendering and expose a runtime hide/show
API. `visible` becomes a first-class, aspect-scoped entity state on the existing
`object_update` diff channel (a new `"visible"` aspect), so toggling it does not
re-serialize geometry or style.

## Files

- Edit: `py/pytanga/viz/_nodes.py`
- Edit: `py/pytanga/viz/scene.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_scene_handle.py`
- Edit: `py/pytanga/viz/_object_ref.py`
- New: `py/tests/viz/test_entity_visibility.py`

## Steps

- [x] **1.1 — `VizSceneObject.set_visible` + `visible` aspect (`_nodes.py`)**
  - Add `set_visible(self, visible: bool)` that sets `self.visible` and calls
    `self.mark("visible")`.
  - Add a `"visible"` case to `VizSceneObject.patch()` returning
    `{"id": self.id, "aspect": "visible", "value": {"visible": self.visible}}`.
  - In `apply_props()`, special-case `visible` (delegate to `set_visible`) and
    exclude it from the `extra` dict so it never leaks into the resolved style.

- [x] **1.2 — `Scene.set_visible` + flush walk (`scene.py`)**
  - Add `Scene.set_visible(self, object_id: str, visible: bool)` that resolves
    the node and calls `node.set_visible(visible)` (raise `KeyError` on an
    unknown id, mirroring `update`).
  - Add `"visible"` to the aspect order in `Scene.flush()` so the patch is
    emitted.

- [x] **1.3 — Public API (`visualizer.py`, `_scene_handle.py`, `_object_ref.py`)**
  - `Visualizer.set_visible(object_id, visible, *, scene_name="")` and
    `Visualizer.hide(object_id, *, scene_name="")`. Do **not** add `show` here —
    `Visualizer.show(...)` already means "start the server".
  - `VizSceneHandle.set_visible(object_id, visible)` and `.hide(object_id)`.
    `show` is **also** taken on `VizSceneHandle` (it serves + displays the
    scene), so show via `set_visible(object_id, True)`.
  - `VizObjectRef.set_visible(visible)` (delegates to the handle, like
    `color`/`opacity`).

- [x] **1.4 — Tests (`py/tests/viz/test_entity_visibility.py`)**
  - `patch("visible")` shape; `apply_props(visible=False)` marks `visible`
    (not `style`); `Scene.set_visible` → `flush` emits a `visible` patch;
    `VizObjectRef.set_visible`.

## Validation

```bash
uv run pytest py/tests/viz/test_entity_visibility.py -q
```

## Notes

- `visible` is already serialized in the `full` payload; the new aspect is the
  cheap incremental path (mirrors `style`/`transform`/`content`) and avoids a
  `full` rebuild re-uploading image pixels.
