# Phase 1 — Frontend image rendering (flip + minification)

## Goal

Make the JPEG path render upright and give the default image shader proper
minification filtering so a large image scaled down no longer aliases/flickers.

## Files

- Edit: `py/pytanga/viz/templates/renderers/image.js`
- Edit: `py/pytanga/viz/templates/renderers/image-shader.js`
- Edit: `py/pytanga/viz/templates/renderers/image-background.js`
- Generated: `js/tanga-viewer.js` + `js/tanga-viewer.manifest.json`

## Steps

- [x] **1.1 — Fix the JPEG texture orientation**
  - In `makeEncodedTexture`'s `codec === 'jpeg'` branch, after
    `createImageBitmap`, draw the bitmap into a 2D canvas and return a
    `THREE.CanvasTexture` with `flipY = true` (close the bitmap after the draw).
  - Set `magFilter = NearestFilter`, `generateMipmaps = true`,
    `minFilter = LinearMipmapLinearFilter`, `needsUpdate = true`.
- [x] **1.2 — Add minification filtering to the other texture builders**
  - `makeDataTexture`: keep `flipY = true`; set `generateMipmaps = true` +
    `minFilter = LinearMipmapLinearFilter` for `dtype === 0`, and
    `minFilter = LinearFilter` for `dtype` 1/2 (no float mipmaps).
  - `makeTiledTexture` / `makeStreamTexture`: `generateMipmaps = true` +
    `minFilter = LinearMipmapLinearFilter`.
- [x] **1.3 — Simplify the default fragment shader**
  - In `image-shader.js` `buildImageFragment`: replace the manual
    `sampleNearest`/`sampleBilinear` + rotation-detection with
    `texture2D(uImage0, vUv)`; keep `u_mode` / `u_value_min` / `u_value_max` /
    `u_brightness` / `u_contrast` / `u_midpoint` handling.
  - Keep `buildImageVertex` unchanged (`vUv = uv`).
- [x] **1.4 — Drop the redundant background flip override**
  - In `image-background.js` `_backgroundTexture`, return
    `makeEncodedTexture(img, frame)` directly and remove the
    `.then(tex => { tex.flipY = true; … })` override plus its now-stale comment
    (the builders set the correct orientation themselves).
- [x] **1.5 — Rebuild the viewer bundle**
  - `uv run python tools/build-viewer-js.py`

## Validation

```
cd js/dev && node tests/check-syntax.mjs && node --test 'tests/*.test.mjs' \
  && cd ../.. && uv run python tools/build-viewer-js.py --check
```

## Notes

- The minification filter relies on WebGL2 (NPOT mipmaps); the viewer's
  `WebGLRenderer` already defaults to WebGL2 when available.
- After this phase, verify orientation with a headless quadrant image (uint8 +
  uint16) and check a minified large image for flicker.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
