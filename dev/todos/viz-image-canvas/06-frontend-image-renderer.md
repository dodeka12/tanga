# Phase 6 — Frontend image renderer

## Goal

A `renderers/image.js` that turns the `image` entity into a three.js
`ShaderMaterial` plane: uploads `uint8`/`uint16`/`float32` as textures, runs the
standard shader (brightness/contrast/mid + channel modes), and applies the
nearest-neighbour / rotation-AA sampling gate.

## Files

- New: `py/pytanga/viz/templates/renderers/image.js`
- New: `py/pytanga/viz/templates/renderers/image-shader.js` (pure GLSL string
  building — Node-testable)
- Edit: `py/pytanga/viz/templates/renderers/factory.js` (dispatch `kind: "image"`)

## Steps

- [x] **6.1 — texture upload (`image.js`)**
  - For each image: `THREE.DataTexture` with the format per dtype —
    `uint8` → `UNSIGNED_BYTE` (normalized), `uint16` → float/half-float texture,
    `float32` → `FLOAT` texture (guard with `_isWebGL2`/`OES_texture_float`).
  - Set `magFilter`/`minFilter` to `NearestFilter` (hard pixel borders) and
    `flipY = false` (frame is already y-down).
  - Handle `source:"url"` via `THREE.TextureLoader` (async, log errors via the
    log pipeline).

- [x] **6.2 — standard fragment shader (`image-shader.js`)**
  - Build GLSL implementing channel mode (`u_mode`) then
    `out = clamp((in − mid) * contrast + mid + brightness, 0, 1)`, reading
    `u_value_min`/`u_value_max` normalization first.
  - `buildImageFragment()` returns the GLSL; a custom `shader.fragment` overrides
    it.

- [x] **6.3 — nearest/AA sampling gate**
  - In the fragment shader, compute the texel-space derivative (`fwidth` of
    `vUv * imageSize`); when axis-aligned/integer (zoom/pan), sample nearest;
    when non-axis-aligned (rotation), blend a 2×2 neighbourhood by sub-texel
    coverage.

- [x] **6.4 — `factory.js` dispatch**
  - Add `case 'image'` → `buildImageObject(...)`; handle the `image_update`
    uniform patch message (merge `uniforms` into the `ShaderMaterial.uniforms`
    without rebuilding the plane).

- [x] **6.5 — syntax + smoke**
  - `node --check` the new JS; browser smoke page loads a `uint8` image and a
    `float32` image with a custom shader.

## Validation

`node --check py/pytanga/viz/templates/renderers/image.js && node --check py/pytanga/viz/templates/renderers/image-shader.js && node --check py/pytanga/viz/templates/renderers/factory.js`

## Notes

- The AA gate is the Phase-8 answer from the design: nearest for integer zoom,
  coverage-blend for rotation.  MSAA alone is insufficient (it only antialiases
  geometric edges, not texel boundaries).
- Keep GLSL string building in `image-shader.js` so the dtype/normalization/AA
  logic is Node-testable separately from DOM/WebGL.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
