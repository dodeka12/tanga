# Phase 1 — Per-scene `space_dim` API + runtime switch

## Goal

Expose the space dimension as a per-scene, settable, switchable property of
`Visualizer` and `VizSceneHandle`.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/pytanga/viz/_scene_handle.py`
- Edit: `py/tests/viz/test_scene_session.py`

## Steps

- [x] **1.1 — Validate helper + per-scene `space_dim` creation**
  - In `visualizer.py`, add module-level `_validate_space_dim(space_dim)`:
    reject non-int / bool / values not in `{2, 3}` with a `ValueError`.
  - Change `_create_scene(self, name, space_dim=None)` to accept `space_dim`
    and, for named scenes, use `_validate_space_dim(space_dim)` when given,
    else fall back to `self._config.space_dim`.
  - Change `add_scene(..., space_dim=None, ...)` and `scene(..., space_dim=None,
    ...)` to validate `space_dim` (when not `None`) and forward it to
    `self._layout.add_scene(name, space_dim)`.
  - Change `LayoutHostImpl.add_scene(self, name, space_dim=None)` to call
    `self._scene_factory(name, space_dim)`.

- [x] **1.2 — `Visualizer.set_space_dim`**
  - Add `set_space_dim(space_dim, *, scene_name="", camera=None)` near
    `set_camera`: validate `space_dim`; set `scene.config.space_dim`; apply the
    camera rules from the README (normalize + dim-check a given camera; clear a
    conflicting camera when omitted); `self._push_scene_config(scene_name)`.
  - Reuse the already-imported `_normalize_camera_config` and
    `_deduce_space_dim`.

- [x] **1.3 — `VizSceneHandle` accessor + setter**
  - Add a `space_dim` property (getter reads `self._scene().config.space_dim`,
    setter calls `self._viz.set_space_dim(value, scene_name=self._name)`).
  - Add `set_space_dim(space_dim, camera=None)` forwarding to the visualizer.

- [x] **1.4 — Tests**
  - In `test_scene_session.py`, add tests: `scene(name, space_dim=2)` /
    `add_scene(name, space_dim=2)` create a scene with that dim; `None`
    inherits; `set_space_dim` updates the config and clears a conflicting
    camera; `set_space_dim` raises on a mismatched explicit camera; the handle
    `space_dim` getter/setter works.

## Validation

`uv run pytest py/tests/viz/test_scene_session.py -q && uv run ruff check py/pytanga/viz/visualizer.py py/pytanga/viz/_layout.py py/pytanga/viz/_scene_handle.py py/tests/viz/test_scene_session.py`

## Notes

- `_normalize_camera_config` and `_deduce_space_dim` are already imported in
  `visualizer.py`; do not add new imports.
- `self._config` **is** the main scene's `SceneConfig` object, so
  `set_space_dim(..., scene_name="")` also updates the default used by new
  named scenes via `_create_scene`'s fallback.
- Keep `add_scene("")` in `__init__` working unchanged (it passes no
  `space_dim`, so `None` → `self._config.space_dim`).
