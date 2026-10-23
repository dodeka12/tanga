# Phase 5 — Frontend: live uniform updates

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (granular `image_update` seam) and
> the `three-view.js` `handleMessage` routing.  This phase dispatches the
> `depth_image_update` message.

## Goal

Route the server's `depth_image_update` message to the depth material's
`applyDepthImageUniforms`, so `set_selected_segments`/`set_uniform` update the
surface without a rebuild or pixel re-send.

## Files

- Edit: `py/pytanga/viz/templates/viewer.js` (add to the `_forMyScene` message list)
- Edit: `py/pytanga/viz/templates/views/three-view.js` (dispatch + handler)

## Steps

- [x] **5.1 — Scene routing in `viewer.js`.**
  - Add `|| msg.type === 'depth_image_update'` to the `_forMyScene` check beside
    `image_update`.

- [x] **5.2 — Dispatch in `three-view.js`.**
  - In `handleMessage`, add `else if (msg.type === 'depth_image_update')` that
    resolves `this.sceneObjects.get(msg.id)` and calls
    `applyDepthImageUniforms(entry.mesh, msg.uniforms)` (import the helper).

- [x] **5.3 — Rebuild on structural change.**
  - Confirm `factory.js::updateEntityMesh` returns `false` for `depth_image`
    structural changes (mesh resolution / texture metadata / shader source), so
    a content re-push rebuilds the material — mirroring the `image` updater.

## Validation

`node js/dev/tests/check-syntax.mjs && uv run python tools/build-viewer-js.py && uv run pytest py/tests/viz -q`

## Notes

- `applyDepthImageUniforms` must only set uniforms that already exist on the
  material (guard `if (material.uniforms[name])`), and must handle the
  `u_selected_segments` int-array and `u_color` vector specially (`.value` vs
  `.fromArray`/`Vector3`).
- No pixel re-send: the patch travels as JSON only.
