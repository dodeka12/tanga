# Image Display Fixes — Overview

**Created:** 2026-09-26 | **Status:** Done | **Branch:** `fix/image-display`

## Goal

Fix the `ImageCanvas` image-display bugs found while exercising
`load_image_from_disk.py` and the image examples: the **JPEG path renders
vertically flipped**, replacing the primary image with a **different dtype keeps
a stale value range** (so a `uint16` image loaded after a `uint8` placeholder
clamps to white), and a **large image scaled down flickers** because there is no
minification filter.  Preserve the custom-shader contract and document the
minification behaviour for custom shaders.

## Architecture (short)

- Frontend image renderer: `py/pytanga/viz/templates/renderers/image.js`
  (`makeDataTexture`, `makeEncodedTexture`, `makeTiledTexture`,
  `makeStreamTexture`), `image-shader.js` (default fragment/vertex),
  `image-background.js` (NDC background); bundled into `js/tanga-viewer.js` via
  `tools/build-viewer-js.py`.
- Backend: `py/pytanga/viz/_image_view.py` — `ImageView` seeds uniforms and
  `ImageCanvas` drives it.
- **Fixed custom-shader contract (unchanged):** `vUv`, `uImage0`…`uImage3`,
  `uImageSize` (level-0 pixel size), the standard uniforms (`u_mode`,
  `u_value_min`, `u_value_max`, `u_brightness`, `u_contrast`, `u_midpoint`), plus
  any name registered with `register_uniform`.

## Decisions (confirmed)

- **Flip root cause:** `createImageBitmap(blob)` + `new THREE.Texture(bitmap)`
  renders upside-down with `flipY=true`, unlike the `DataTexture` path (which is
  correct with `flipY=true`).  Fix by drawing the decoded `ImageBitmap` into a
  2D canvas and returning a `THREE.CanvasTexture` with `flipY=true`, matching
  `makeTiledTexture`/`makeStreamTexture`.
- **Minification:** `magFilter = NearestFilter` (hard 1:1 pixels);
  `generateMipmaps = true` + `minFilter = LinearMipmapLinearFilter` for 8-bit
  textures; `minFilter = LinearFilter` for `uint16`/`float32` (float mipmap
  generation is not universally supported).  The default fragment switches to
  hardware `texture2D(uImage0, vUv)`; the manual nearest/bilinear sampling is
  removed from the *default* shader only.
- **Custom-shader contract preserved:** keep `uImageSize` and every uniform in
  `buildUniforms`; keep `buildImageVertex`'s `vUv` output; only the default
  fragment changes.
- **Value range:** `ImageView.set_image` re-derives `u_mode`/`u_value_min`/
  `u_value_max` from the new image (overwrite, not `setdefault`);
  `add_image` keeps `setdefault`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-frontend-image-rendering.md](./01-frontend-image-rendering.md) | Flip fix + minification filtering + default-shader simplification |
| 2 | [02-value-range-reset.md](./02-value-range-reset.md) | Reset value-range/mode on `ImageView.set_image` |
| 3 | [03-docs-changelog.md](./03-docs-changelog.md) | Custom-shader minification docs + changelog |

## Testing as you go

- JS: `cd js/dev && node tests/check-syntax.mjs && node --test 'tests/*.test.mjs'`
- Bundle: `uv run python tools/build-viewer-js.py --check`
- Python: `uv run pytest py/tests/viz/ -q`
- Docs: `uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`
- Headless smoke (manual): quadrant-image orientation (uint8 + uint16), gray-128
  value, and a minified large image for flicker.

## Non-goals

- Overlay (`Rectangle2D`/`ActRectangle2D`) coordinate alignment — verify after
  phase 1 and triage separately if misaligned.
- Downscaling/tiling the non-tiled transport ("sent in full") — out of scope;
  `register_image_pyramid` remains the large-image path.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
