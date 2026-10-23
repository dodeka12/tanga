# Phase 4 — Frontend: uniform patch + shader rebuild

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — "Image
> background" and the `view_*` granular-message pattern in `viz-controls-and-interactions.md`).
>  This phase wires the new `view_background_uniforms` message.

## Goal

Route the new `view_background_uniforms` message to the background quad's material,
and make a background shader-source change rebuild the material.

## Files

- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`

## Steps

- [x] **4.1 — Dispatch `view_background_uniforms` (viewer.js).**
  - Next to `view_background_image`/`view_surface`, add
    `if (msg.type === 'view_background_uniforms') { const t = _viewById.get(msg.view_id);
    if (t) t.setBackgroundUniforms(msg.uniforms); return; }`.

- [x] **4.2 — `ThreeJsView.setBackgroundUniforms(patch)`.**
  - Add the method; it calls `applyImageUniforms(this._backgroundMesh, patch)` (the
    shared helper from Phase 3), no-oping when there is no background mesh.

- [x] **4.3 — Rebuild on shader change.**
  - In `setBackgroundImage(imageMeta)`, detect a fragment/vertex change versus the
    current material and rebuild the background mesh (a `ShaderMaterial` cannot swap
    source in place) instead of only updating the texture.  Preserve `uCrop`/zoom
    across the rebuild when possible.

- [x] **4.4 — Syntax gate + manual smoke.**
  - Run the syntax gate, then smoke-test against the app: ctrl+drag should change
    brightness/contrast live, and a `register_background_shader` re-push should
    swap the shader without a page reload.

## Validation

`node js/dev/tests/check-syntax.mjs && uv run python tools/build-viewer-js.py && uv run python tools/build-viewer-js.py --check`

## Notes

- Do not reuse the `image_update` branch in `three-view.js::handleMessage` (it
  resolves `sceneObjects`, which does not contain the background quad).
- The rebuild branch must keep `renderOrder = -1`, `depthTest/depthWrite = false`,
  and `frustumCulled = false` from `createImageBackground`.
