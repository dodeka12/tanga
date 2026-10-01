# Phase 3 — Per-frame view rescale

## Goal

Add `_updateScreenSpaceMarkers()` to `three-view.js` and call it each frame so
screen-space markers keep a constant on-screen size under zoom/pan/resize, in
both ortho and perspective cameras.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> view/render-loop structure (the `render()` method and the per-frame
> `_updateImageLod` pattern), so the new method matches the documented view
> lifecycle.  No architecture change is expected.

## Files

- Edit: `py/pytanga/viz/templates/views/three-view.js`

## Steps

- [x] **3.1 — `_updateScreenSpaceMarkers()`**
  - Iterate `this.sceneObjects`; for each entry with
    `entry.mesh && entry.mesh.userData.isScreenSpace`, compute the world position
    (`entry.mesh.getWorldPosition`) and set `entry.mesh.scale` via
    `screenWorldScale(this.camera, viewportPx, worldPos)`.
  - Ortho: a single uniform factor; perspective: per-marker distance and set the
    marker quaternion to face the camera (`quaternion.copy(camera.quaternion)`).
  - Billboard only flat markers (`mesh.isMesh`); the crosshair `Group` keeps its
    world orientation.
- [x] **3.2 — call in `render()`**
  - Call `this._updateScreenSpaceMarkers()` after `clampOrthoView(...)` (next to
    `this._updateImageLod()`).
- [x] **3.3 — verify no bundle rebuild is needed**
  - `three-view.js` is served live (not bundled); confirm no bundled file changed
    this phase.

## Validation

```
node --check py/pytanga/viz/templates/views/three-view.js
uv run python tools/build-viewer-js.py --check
```

## Notes

- `viewportPx` should be CSS pixels (`this.width`/`this.height`, not the drawing
  buffer), so sizes match `LineMaterial.linewidth` and DPR is handled by the
  renderer.
