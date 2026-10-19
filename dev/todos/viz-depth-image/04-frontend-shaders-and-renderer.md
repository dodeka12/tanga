# Phase 4 — Frontend: default shaders + renderer

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` ("New entity kind" — frontend
> renderer step).  This phase adds the `depth-image` renderer and wires it into
> `factory.js`.

## Goal

Build the `depth_image` mesh on the frontend: a decimated grid whose vertex
shader samples the depth texture and displaces +Z (setting `vUv`), with a
fragment shader that does colormap / image / plain coloring and segmentation
`discard`.

## Files

- New: `py/pytanga/viz/templates/renderers/depth-shader.js`
- New: `py/pytanga/viz/templates/renderers/depth-image.js`
- Edit: `py/pytanga/viz/templates/renderers/factory.js`
- New: `js/dev/tests/depth-shader.test.mjs`

## Steps

- [x] **4.1 — `depth-shader.js` (pure GLSL builders).**
  - `buildDepthVertex()`: declares `vUv`/`vDepth`/`vValid` varyings, `uDepth`/
    `uDepthSize`/`uDepthScale`/`uDepthOffset`/`uMissingDepth`/`uDepthMin`/
    `uDepthMax` uniforms; snaps `uv` to the pixel centre, samples `uDepth`,
    sets `vDepth` (clamped) and `vValid` (0 when `== uMissingDepth`), displaces
    `position.z += (depth - uDepthOffset) * uDepthScale`, emits `gl_Position`.
  - `buildDepthColormap()`: a `vec3 depthColormap(float t, int m)` with
    `m==0` viridis, `m==1` turbo, `m==2` gray (standard polynomial
    approximations).
  - `buildDepthFragment()`: declares the `u_render_mode`/`u_colormap`/`u_color`/
    `u_opacity`/`u_discard_missing`/segmentation uniforms + `uImage0`/
    `uImageSize`/`uSegMask`; discards on missing depth (when enabled) and on
    non-selected segment ids (via a `tangaSegmentSelected(vUv)` helper); colors
    by mode.

- [x] **4.2 — `depth-image.js` renderer.**
  - `makeScalarTexture(img, bytes)` — single-channel float `DataTexture` with
    `NearestFilter` (mag + min), `flipY=true`, from the id-keyed frame store
    (reuse `hasImageFrame`/`takeImageFrame`/`registerImageFrameConsumer`); a
    `typedArrayFor`/`toRgba`-style expansion is fine (value in `.r`).
  - `createDepthImage(ent, opts)`: build `PlaneGeometry(w, h, segments_u,
    segments_v)` from `ent.mesh`; build uniforms (all contract uniforms +
    custom uniforms, `u_color` → `Vector3`, `u_selected_segments` → int array,
    `uDepthSize`/`uImageSize`/`uSegSize` from the metadata); select
    `ent.shader?.vertex || buildDepthVertex()` and
    `ent.shader?.fragment || buildDepthFragment()`; `ShaderMaterial` with
    `depthWrite: true`, `side: DoubleSide`; bind `uDepth`/`uSegMask`/`uImage0`
    (fallback 1×1 when absent) via the frame store; `tagEntity`.
  - Export `applyDepthImageUniforms(mesh, patch)` and `updateDepthImage(mesh,
    ent, prev)` (structural changes → return `false`).

- [x] **4.3 — Wire `factory.js`.**
  - Import `createDepthImage`/`updateDepthImage`; add `case 'depth_image':` to
    `createEntityMesh` and `updateEntityMesh`.

- [x] **4.4 — JS unit test + syntax gate.**
  - `depth-shader.test.mjs`: the built vertex/fragment strings contain the
    required uniforms/varyings (`uDepth`, `vUv`, `discard`, `tangaSegmentSelected`).

## Validation

`node js/dev/tests/check-syntax.mjs && node --test js/dev/tests/depth-shader.test.mjs && uv run python tools/build-viewer-js.py`

## Notes

- The templates are the source of `js/tanga-viewer.js`; run
  `uv run python tools/build-viewer-js.py` after editing so the bundle + manifest
  stay in sync.
- Do not mipmap depth/segmentation (nearest, full-res).  The color image keeps
  the standard mipmapped path from `image.js`.
