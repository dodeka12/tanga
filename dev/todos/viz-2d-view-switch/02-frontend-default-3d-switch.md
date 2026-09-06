# Phase 2 — `switchToCamera` default perspective branch

## Goal

Make a live `space_dim` switch (2D → 3D) work even when no explicit camera is
provided, by recreating a perspective camera when the current camera is
orthographic.

## Files

- Edit: `py/pytanga/viz/templates/view_mode.js`

## Steps

- [x] **2.1 — Add the default-3D branch**
  - In `switchToCamera`, immediately after the existing "Default 2D" branch and
    before `return camera;`, add:
    - `if (spaceDim === 3 && camera.isOrthographicCamera)` → create
      `_newPerspective(aspect, 50)`, set `position (6, 4.5, 7.5)`,
      `lookAt(0, 0, 0)`, `updateProjectionMatrix()`, assign `controls.object`,
      and return it.
  - Leave the 3D perspective and 2D ortho branches unchanged.

## Validation

`node --check py/pytanga/viz/templates/view_mode.js && uv run pytest py/tests/viz -q`

## Notes

- `_newPerspective(aspect, fov = 50)` already exists in `view_mode.js`.
- `spaceDim` comes from `sceneConfig.space_dim`; `_applySceneConfig` sets
  `this.sceneConfig` **before** `_applyCamera`, so `switchToCamera` sees the
  new dimension.
- No browser-less JS unit test covers this file; `node --check` is a syntax
  gate and the Python suite guards regressions in the backend that drives it.
