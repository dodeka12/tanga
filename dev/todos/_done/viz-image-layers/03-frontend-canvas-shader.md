# Phase 3 — Frontend default multi-layer canvas shader

## Goal

Replace the default fragment shader (which samples only `uImage0`) with a
bottom-up 4-layer compositor, and seed the per-layer uniforms in `image.js`.

## Files

- Edit: `py/pytanga/viz/templates/renderers/image-shader.js`
- Edit: `py/pytanga/viz/templates/renderers/image.js`
- Edit: `js/dev/tests/*` (new `image-layers.test.mjs`)

## Steps

- [x] **3.1 — Per-layer color pipeline + blend helpers in `image-shader.js`.**
  - Change `tangaSampleColor(tex)` → `tangaSampleColor(tex, chmode, vmin, vmax)`
    (global brightness/contrast/midpoint stay).
  - Add `tangaBlend(dst, src, mode)` for normal (source-over) / add / multiply /
    screen, each respecting `src.a`.

- [x] **3.2 — `buildImageFragment` composites 4 layers.**
  - Declare `uImage0..3`, per-layer uniforms `u_layer{i}_enabled/opacity/blend/
    mode/value_min/value_max`, and loop 0..3: sample, per-layer color, composite
    with the layer's blend/opacity (skip when disabled).  Layer 0 is the base.

- [x] **3.3 — `image.js` seeds per-layer uniforms + applies them.**
  - `buildUniforms` adds the six per-layer uniform slots for 0..3 (from the
    serialized `ent.uniforms`); `updateImage` applies them from `ent.uniforms`.

- [x] **3.4 — JS tests.**  `image-layers.test.mjs` asserts the default fragment
  declares `uImage0..3` + per-layer uniforms and is brace-balanced; `tangaBlend`
  has the four modes.

## Validation

```
node js/dev/tests/check-syntax.mjs
node --test js/dev/tests/*.test.mjs
uv run python tools/build-viewer-js.py
```
