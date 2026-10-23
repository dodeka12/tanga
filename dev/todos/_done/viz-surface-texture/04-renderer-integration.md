# Phase 4 — Renderer integration + bundle regen

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` ("New entity kind" renderer notes)
> and `py/pytanga/viz/export/_bootstrap/_html.py` (`_RENDERER_FILES`).  Adding a
> renderer module is an established extension, not an architecture change.

## Goal

Make the seven solid-surface renderers branch on `ent.style?.surface`, wire the
live per-scene lighting override into the new shader path, and register the new
modules in the export bundle.

## Files

- **Edit** `renderers/plane.js`, `sphere.js`, `ellipsoid.js`, `disk.js`, `box.js`, `cylinder.js`, `cone.js`.
- **Edit** `renderers/utils.js` (`style-diff.js` sibling) if needed for rebuild decisions.
- **Edit** `py/pytanga/viz/templates/views/three-view.js` — re-light surface materials on `scene_config`.
- **Edit** `py/pytanga/viz/export/_bootstrap/_html.py` — `_RENDERER_FILES`.

## Steps

- [x] **4.1 — branch each renderer on `ent.style?.surface`**
  - In `createPlane/createSphere/createEllipsoid/createDisk/createBox/createCylinder/createCone`, after computing the fallback `makeMaterial(...)`, call
    `createSurfaceMaterial(ent, { fallbackMaterial })` and build the mesh with the returned material.  Keep the existing texture-label and wireframe paths unchanged for the no-surface case.
  - `cone.js`: the entity is a `THREE.Group` of two child cone meshes — create one surface material and assign it to both children.

- [x] **4.2 — surface rebuild decisions**
  - Ensure a change to the nested `ent.style.surface` triggers a rebuild (the current `CHEAP_STYLE_FIELDS = {'color','opacity'}` already rebuilds on anything else; add a `style-diff` test that a `surface` change is not "cheap").

- [x] **4.3 — live lighting override**
  - In `three-view.js`, where the scene re-pushes `scene_config` (the `_applyShaderLighting` / re-light hook), also call `applySurfaceMaterialLighting(material, lighting)` for surface materials (or route through the existing shader-relight loop that already covers SDF/depth proxies).

- [x] **4.4 — register modules + regenerate bundle**
  - Add `_RENDERERS_DIR / "surface-shader.js"` and `_RENDERERS_DIR / "surface-material.js"` to `_RENDERER_FILES` (after `shader-lighting.js`, before `depth-shader.js`), so `generate_library_js()` inlines them and `library_source_files()` includes them.
  - Run `uv run python tools/build-viewer-js.py` and commit the regenerated `js/tanga-viewer.js` + manifest.

## Validation

```bash
node js/dev/tests/check-syntax.mjs
node --test js/dev/tests/style-diff.test.mjs js/dev/tests/surface-shader.test.mjs
uv run python tools/build-viewer-js.py --check
```

## Notes

- The per-entity renderers are ES modules in the live viewer but are concatenated
  (imports stripped) in the export bundle; verify both with `check-syntax.mjs` and
  the bundle `--check` gate.
- Manual smoke (after phase 6 examples exist): add a textured sphere and confirm
  lighting follows `viz.set_scene_lighting(...)`.
