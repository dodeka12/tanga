# Phase 2 — `scenes` into `LayoutHost` + auto-layout on `add_scene`

## Goal

Move the scene registry from `Visualizer._scenes` into `LayoutHost`, and make
`add_scene(name)` auto-create `Layout(name, base=SceneView(name))` (raise if the
name is taken).  This makes URLs name layouts only, with scene URLs for free.

## Files

- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_scene_handle.py`
- Edit: `py/pytanga/viz/_hosts.py` (hosts use `layout.scene`)

## Steps

- [x] **2.1 — `LayoutHost` owns scenes**
  - `scenes: dict[name, Scene]`, `add_scene(name)` (Scene + auto Layout, raise on
    conflict), `scene(name)`, `scene_names()`.
- [x] **2.2 — `Visualizer` delegates**
  - `viz.scene(name)` / `viz.add_scene(name)` → `layout`; drop `Visualizer._scenes`.
- [x] **2.3 — Repoint hosts / `VizSceneHandle`**
  - Replace `self._layout.scene(...)` / `_scenes` reach-throughs.
- [x] **2.4 — Tests**
  - Green; add an `add_scene` auto-layout + conflict test.

## Validation

`uv run pytest py/tests/viz -q`

## Notes

- Main scene `""` is created in `__init__` via `add_scene("")`.
