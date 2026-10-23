# Phase 4 — Standard-renderer lighting driven by scene config

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (scene config handling on the
> frontend) and `three-view.js::_applySceneConfig` / `_addDefaultLights`.  This
> phase changes how the standard `MeshPhongMaterial` lights are created (from
> hardcoded to config-driven) — a small, contained frontend behavior change.

## Goal

Replace the hardcoded `_addDefaultLights()` with `_applyLighting(wireLighting)`
that creates the three.js `AmbientLight` + `DirectionalLight`s from the
`scene_config.lighting` block (falling back to the shared default), so the
standard renderer and the shaders read the same config.

## Files

- **Edit** `py/pytanga/viz/templates/views/three-view.js` — add `_applyLighting`,
  replace `_addDefaultLights`, apply in `_applySceneConfig`.

## Steps

- [x] 4.1 Import `DEFAULT_LIGHTING` (and `parseHexColor` if useful) from
  `../renderers/shader-lighting.js` into `three-view.js`.
- [x] 4.2 Add `_applyLighting(wireLighting)`:
  - remove any lights previously added by this method (keep them in
    `this._sceneLights = []`; call `.remove(light)` + `light.dispose?.()`),
  - `const wire = wireLighting || DEFAULT_LIGHTING`,
  - add `new THREE.AmbientLight(ambientColor, ambientIntensity)`,
  - for each `lights[]` entry, `new THREE.DirectionalLight(color, intensity)` with
    `position.set(dir[0], dir[1], dir[2]).multiplyScalar(1000)` (target stays at
    origin so the travel direction = `-position` = `-dir`, i.e. light comes
    *from* the `direction` vector, matching the "toward the light" convention),
  - push all created lights onto `this._sceneLights`.
- [x] 4.3 Replace the constructor call `this._addDefaultLights()` with
  `this._applyLighting(null)` (line ~304).
- [x] 4.4 Replace the reset call `this._addDefaultLights()` with
  `this._applyLighting(this.sceneConfig && this.sceneConfig.lighting)` (line ~550),
  so a cleared scene keeps the scene's configured lights.
- [x] 4.5 In `_applySceneConfig`, after storing `this.sceneConfig`, call
  `this._applyLighting(config.lighting)`.  (Re-pushes are cheap and idempotent
  because `_applyLighting` removes its own previous lights first.)
- [x] 4.6 Remove the now-unused `_addDefaultLights` method.

## Validation

```bash
node js/dev/tests/check-syntax.mjs
uv run python tools/build-viewer-js.py
# Manual smoke: run a standard (non-SDF) scene and an SDF scene; confirm the
# standard surfaces still look identical (default config == old hardcoded lights).
```
