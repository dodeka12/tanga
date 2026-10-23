# Phase 3 — Frontend: default background shader + shared helpers

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — "Image
> canvas (extension recipe)" and "Image background").  This phase extracts shared
> JS/GLSL helpers and gives the background a brightness/contrast default shader.

## Goal

Extract the shared GLSL color pipeline and the `buildUniforms`/`applyImageUniforms`
JS helpers, then rebuild the background material from the serialized
`shader`/`uniforms` (default = letterbox/crop UV + brightness/contrast).

## Files

- Edit: `py/pytanga/viz/templates/renderers/image-shader.js`
- Edit: `py/pytanga/viz/templates/renderers/image.js`
- Edit: `py/pytanga/viz/templates/renderers/image-background.js`

## Steps

- [x] **3.1 — Extract the shared GLSL color pipeline.**
  - In `image-shader.js`, add `buildImageColorPipeline()` returning the GLSL
    `color`-normalize → brightness/contrast → clamp body (from `buildImageFragment`,
    plus the `u_value_min`/`u_value_max`/`u_mode`/`u_brightness`/`u_contrast`/
    `u_midpoint` `uniform` declarations as needed).
  - `buildImageFragment()` is rewritten to use it (no rendering change).

- [x] **3.2 — Export shared `buildUniforms`/`applyImageUniforms`.**
  - Export `buildUniforms` from `image.js` (or move it and `applyImageUniforms` to
    a small shared module); keep `image.js` behavior identical.

- [x] **3.3 — Background default shader + uniforms.**
  - In `image-background.js`, make `_buildMaterial(imageMeta)` build uniforms from
    `imageMeta.uniforms` (seeding `u_brightness`/`u_contrast`/`u_midpoint` and
    value-range keys, plus any custom uniforms) and select
    `imageMeta.shader?.fragment || <default>`.
  - The default background fragment = the existing `_BG_FRAGMENT` letterbox/crop UV
    math, then the shared color pipeline (`buildImageColorPipeline()`) before
    `gl_FragColor`.  `uImage` sampling is unchanged.
  - `updateImageBackground` re-applies uniform defaults alongside `uImageAspect`.

- [x] **3.4 — Syntax gate.**
  - Confirm the rebuilt material still resolves textures via
    `_backgroundTexture`/`registerImageFrameConsumer` (unchanged).

## Validation

`node js/dev/tests/check-syntax.mjs && node --test js/dev/tests/*.test.mjs && uv run python tools/build-viewer-js.py`

## Notes

- Keep the background vertex shader (`_BG_VERTEX`) and the `hx/hy/q/uv` block
  unchanged — only the color section is replaced.
- `uImageAspect`/`uPaneAspect`/`uFit`/`uCrop`/`uHx`/`uHy` remain background-only
  uniforms and must stay seeded in `_buildMaterial`.
- The templates are the source of the published `js/tanga-viewer.js` bundle; after
  editing them run `uv run python tools/build-viewer-js.py` so the committed bundle
  + manifest stay in sync.
