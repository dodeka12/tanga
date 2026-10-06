# Viz — image-bearing HTML export (bridge + compression) — Overview

**Created:** 2026-10-06 | **Status:** Done | **Branch:** `fix/html-export-transform`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture. If this work introduces or changes architecture, update the
> developer docs.

## Goal

Make image-bearing HTML exports actually render — both the **animated**
`py/examples/viz/export/animated_image_stream.py` example and the **static**
`image_export.py` snapshot — and make the `compress=True` animated export
robust against the async decompression race.

Two root causes were found:

1. **Missing bridge symbols.** The export bootstrap calls `storeImageFrame(...)`
   (in the animated `_playFrame`, and in the static `js_image_assets_hydration`),
   but the `window.__tanga` bridge does not expose it (or its siblings). The
   viewer library and the bootstrap are **separate** `<script type="module">`
   scopes, so the call throws
   `ReferenceError: storeImageFrame is not defined` and the image never renders.
2. **Decompression race.** `compress=True` embeds the animation JSON as
   gzip+base64 and decompresses it in an *async* `<script type="module">`, while
   the bootstrap reads `window.__TANGA_ANIMATION__` *synchronously*. When the
   decompression has not finished by the time the bootstrap runs (most visible
   with `delivery="offline"`, where nothing is fetched over the network), the
   data reads back as empty.

## Architecture (short)

- `py/pytanga/viz/templates/image-frames.js` defines the pixel frame store:
  `storeImageFrame`, `takeImageFrame`, `hasImageFrame`,
  `registerImageFrameConsumer` (plus `decodeImageFrame`, used only by the live
  binary wire). It is bundled into the viewer library via `_SHARED_JS_FILES`
  (`generate_library_js()`).
- The library exposes its public API through `window.__tanga`, generated from
  `_TANGA_BRIDGE_SYMBOLS` in `py/pytanga/viz/export/_bootstrap/_scene.py`. The
  export bootstrap (`adapter_js`) destructures the same symbols.
- `py/pytanga/viz/export/_bootstrap/_animation.py` generates the playback
  engine (`_playFrame` → image hydration) and the compressed-data
  embed/decompress pair (`embed_animation_data` / `_ANIMATION_DECOMPRESS_JS`).

**Fixed contract (up front):**

- `window.__tanga` exposes the library helpers the bootstrap references: the
  frame-store API (`storeImageFrame`, `takeImageFrame`, `hasImageFrame`,
  `registerImageFrameConsumer`) and the camera-fit helper `applyOrthoFrustum`.
  `decodeImageFrame` stays out — the export path base64-decodes via `atob`,
  never touching the binary wire codec.
- Compressed animation data is decompressed asynchronously into a
  `window.__tangaAnimReady` Promise; the bootstrap awaits it before reading
  `window.__TANGA_ANIMATION__`.

## Decisions (confirmed)

- Expose the **four** frame-store helpers (`storeImageFrame`, `takeImageFrame`,
  `hasImageFrame`, `registerImageFrameConsumer`) in the bridge — not
  `decodeImageFrame`, which is live-wire only.
- Fix the compression race by **async-gating** the bootstrap's data init on
  `window.__tangaAnimReady` — not by dropping gzip, and not by adding a JS
  inflate dependency.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-expose-image-frame-bridge.md](./01-expose-image-frame-bridge.md) | Expose the image-frame helpers in `window.__tanga` + rebuild the bundle |
| 2 | [02-fix-compression-decompression-race.md](./02-fix-compression-decompression-race.md) | Async-gate the bootstrap on the gzip decompression promise |
| 3 | [03-docs-changelog.md](./03-docs-changelog.md) | Document the bridge/hydration contract + branch changelog |

## Testing as you go

- Python: `uv run pytest py/tests/viz/test_image_canvas_export.py -q`
- Bundle drift: `uv run python tools/build-viewer-js.py --check`
- JS syntax: `node js/dev/tests/check-syntax.mjs`
- Docs: `uv run mkdocs build --strict`
- Browser smoke (manual): regenerate `animated_image_stream.py`'s HTML and load
  it headlessly (Playwright) — confirm no `ReferenceError` and that
  `window.__TANGA_ANIMATION__.frame_count` populates.

## Non-goals

- `decodeImageFrame` in the bridge (live binary-wire only).
- The esbuild/`offline` toolchain failure (a separate issue; `delivery="offline"`
  currently cannot bundle because `find_esbuild()` feeds the native ELF binary
  to `node`).
- Recompressing per-frame JPEG data URLs (gzip gains little on already-compressed
  JPEG; this plan makes the existing `compress=True` path *reliable*, not smaller).
