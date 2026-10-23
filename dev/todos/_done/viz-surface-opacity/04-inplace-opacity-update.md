# Phase 4 — In-place opacity updates

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (the hover opacity
> path already reads/writes `u_opacity` for `ShaderMaterial`s) and
> `renderers/utils.js::applyStyleUpdate`.  This phase reuses that pattern for
> entity style updates; it adds no new seam.

## Goal

Make `viz.update(id, opacity=…)` (and other cheap in-place style updates) reach
the surface material's `u_opacity` uniform instead of the ignored
`material.opacity` property.

## Files

- Edit `py/pytanga/viz/templates/renderers/utils.js`
- Regenerate `js/tanga-viewer.js` + `js/tanga-viewer.manifest.json`

## Steps

- [x] **4.1 — Handle the `u_opacity` uniform in `applyStyleUpdate`**
  - In `applyStyleUpdate`, inside the `mesh.traverse` callback, before the
    existing `child.material.opacity !== undefined` branch, add a branch for
    `child.material.uniforms && child.material.uniforms.uOpacity`:
    - set `m.uniforms.uOpacity.value = target` (when `target !== undefined`);
    - set `m.transparent = target < 1.0 || (m.userData && m.userData._alphaTexture)`;
    - set `m.depthWrite = target >= 0.99 && !(m.userData && m.userData._alphaTexture)`;
    - set `m.needsUpdate = true`; then `continue` (do not fall through to the
      `.opacity` path for this child).
  - Keep the existing `.opacity`/`transparent`/`depthWrite` behavior for plain
    `MeshPhongMaterial`s unchanged.

- [x] **4.2 — Regenerate the bundle**
  - `uv run python tools/build-viewer-js.py`

## Validation

```bash
node js/dev/tests/check-syntax.mjs
node --test js/dev/tests/*.test.mjs
uv run python tools/build-viewer-js.py --check
```

## Notes

- `applyStyleUpdate` is only used by regular entities; SDF/ray proxies route
  through `updateSdfProxy`/`updateRayProxy`, so their `uOpacity` is untouched.
- The `_alphaTexture` marker is set in Phase 3 (`surface-material.js`).
