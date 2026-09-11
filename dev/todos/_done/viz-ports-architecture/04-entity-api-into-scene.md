# Phase 4 — Entity API into `Scene`

## Goal

Move the typed entity facade (`_add_to_scene`, `add`, `new`, `update`, `remove`,
`clear`, `add_group`, `add_label`, …) from `Visualizer` into `Scene`, so `Scene`
owns its entities *and* their API.  `Visualizer`/`VizSceneHandle` become
"pick the right scene" delegates.  (This is an API-neutral move; signatures stay.)

## Files

- Edit: `py/pytanga/viz/scene.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_scene_handle.py`

## Steps

- [x] **4.1 — Move construction into `Scene`**
  - Move `_add_to_scene`/`_attach_to_parent`/`_add_label_for_entity` into `Scene`
    (as `Scene.add` internals).
- [x] **4.2 — Move mutation into `Scene`**
  - `update`/`update_style`/`update_entity`/`update_label`/`get_label_ids`/`remove`/
    `clear` become `Scene` methods.
- [x] **4.3 — Delegate from `Visualizer`/`VizSceneHandle`**
  - `viz.add(...)` → `layout.scene("").add(...)`; `viz.scene(name).add(...)`.
- [x] **4.4 — Tests**
  - Green; `Scene` needs a style/default reference (pass `_global_styles`).

## Validation

`uv run pytest py/tests/viz -q`
