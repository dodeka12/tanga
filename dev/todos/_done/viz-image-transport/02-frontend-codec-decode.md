# Phase 2 — Frontend codec decode

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Teach the frontend to decode v2 frames: JPEG via `createImageBitmap`
(off-main-thread, GPU decode) and zlib via `DecompressionStream`, while keeping
the existing raw `DataTexture` path for lossless/float data.

## Files

- Edit: `py/pytanga/viz/templates/image-frames.js`
- Edit: `py/pytanga/viz/templates/renderers/image.js`
- Edit: `py/pytanga/viz/templates/renderers/image-background.js`
- Edit: `js/tanga-viewer.js` (regenerated bundle — see Notes)
- New: `js/dev/tests/*.test.mjs` (extend/add a decode test)

## Steps

- [x] **2.1 — decode v2 header (`image-frames.js`)**
  - Parse `codec` at offset 7 (README contract); keep accepting v1 (codec 0).
  - Return `{ id, width, height, channels, dtype, codec, bytes }`.

- [x] **2.2 — async encoded-texture path (`renderers/image.js`)**
  - Add `makeEncodedTexture(img, frame)` (async): for `codec === "jpeg"` build a
    `Blob` and `createImageBitmap`, then `new THREE.Texture(bitmap)` with
    `NearestFilter` + `needsUpdate`; for `codec === "zlib_raw"` decompress via
    `new DecompressionStream("deflate")` and fall through to the existing
    typed-array `makeDataTexture` logic; for `codec === "raw"` use
    `makeDataTexture` unchanged.
  - Make `createImage` await the encoded path in the `source === "data"` branch
    (it is already `async`).

- [x] **2.3 — background path (`renderers/image-background.js`)**
  - `createImageBackground` becomes async and awaits `makeEncodedTexture` for
    data images (JPEG/zlib/raw); `ThreeJsView` must `await` it when mounting
    the background quad.

- [x] **2.4 — JS tests**
  - Unit-test `decodeImageFrame` against a hand-built v2 buffer (all three
    codecs) and a v1 buffer.
  - Run `node --test` and `check-syntax.mjs`.

## Validation

```powershell
node --test 'js/dev/tests/*.test.mjs'
node js/dev/tests/check-syntax.mjs
uv run pytest py/tests/viz -q
```

## Notes

- `js/tanga-viewer.js` is a bundled artifact of the `templates/` modules; after
  editing templates, regenerate it with the repo's esbuild toolchain (see
  `js/dev/README.md`) so the live + offline viewers stay in sync.
- Keep the raw `toRgba` expansion for raw/float data only; JPEG textures
  already arrive as RGBA and skip that JS loop.
