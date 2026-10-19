# Phase 3 — Shared shader-lighting module

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the SDF renderer + custom-shader
> notes) and the existing `renderers/sdf/lighting.js` comments.  This is a pure
> file move/generalize + re-point of imports; it does not change the GLSL or
> uniform contract.

## Goal

Promote the SDF lighting module to a renderer-agnostic shared module so both the
SDF renderer and (in phase 5) the depth renderer import one source of truth, and
align its `DEFAULT_LIGHTING` with the new scene default.

## Files

- **New** `py/pytanga/viz/templates/renderers/shader-lighting.js` (from
  `renderers/sdf/lighting.js`).
- **Delete** `py/pytanga/viz/templates/renderers/sdf/lighting.js`.
- **Edit** import sites:
  - `py/pytanga/viz/templates/renderers/ray.js` (`./sdf/lighting.js` → `./shader-lighting.js`)
  - `py/pytanga/viz/templates/renderers/sdf/glsl.js` (`./lighting.js` → `../shader-lighting.js`)
  - `py/pytanga/viz/templates/renderers/sdf.js` (`./sdf/lighting.js` → `./shader-lighting.js`)
  - `py/pytanga/viz/templates/sdf/material-table.js` (`../renderers/sdf/lighting.js` → `../renderers/shader-lighting.js`)
  - `py/pytanga/viz/templates/sdf/sdf_viewer.js` (`../renderers/sdf/lighting.js` → `../renderers/shader-lighting.js`)
- **Edit** the stale comments in `renderers/sdf.js` (line ~8) and
  `templates/sdf/sdf_viewer.js` (line ~63) that reference `sdf/lighting.js`.
- **New** `js/dev/tests/shader-lighting.test.mjs` (or extend an existing SDF
  lighting test if one exists).

## Steps

- [x] 3.1 Create `renderers/shader-lighting.js` with the existing exports
  (`MAX_LIGHTS`, `DEFAULT_LIGHTING`, `lightPreamble`, `parseHexColor`,
  `parseAmbient`, `parseLight`, `parseLighting`, `setLightUniforms`), updating:
  - the module header comment to describe the *scene-wide* shared model,
  - `DEFAULT_LIGHTING` to match `DEFAULT_SCENE_LIGHTING`: ambient `#ffffff` @ `0.5`;
    lights `normalize((10,20,10))` @ `0.8` and `normalize((-5,-2,-8))` @ `0.3`
    (pre-normalized direction arrays).
- [x] 3.2 Update the five import sites listed above and the two stale comments.
- [x] 3.3 Delete `renderers/sdf/lighting.js`.
- [x] 3.4 Add a JS test covering: `parseLighting()` with the *new* wire shape
  (ambient + two lights) returns the right ambient + two parsed lights;
  `parseLight` normalizes a non-unit direction; `setLightUniforms` writes
  `uLightCount`/`uLightDir`/`uLightColor`/`uAmbientColor` (including zeroing
  unused light slots).

## Validation

```bash
node js/dev/tests/check-syntax.mjs
node --test js/dev/tests/shader-lighting.test.mjs
uv run python tools/build-viewer-js.py
```
