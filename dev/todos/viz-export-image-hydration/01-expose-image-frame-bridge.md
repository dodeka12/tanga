# Phase 1 — Expose image-frame helpers in `window.__tanga`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture. If this work introduces or changes architecture, update the
> developer docs.

## Goal

Add `storeImageFrame`, `takeImageFrame`, `hasImageFrame`, and
`registerImageFrameConsumer` to the export bridge so the bootstrap's
`storeImageFrame(...)` call resolves (fixing the `ReferenceError`), then rebuild
the committed CDN bundle.

## Files

- Edit: `py/pytanga/viz/export/_bootstrap/_scene.py`
- Rebuild: `js/tanga-viewer.js`, `js/tanga-viewer.manifest.json`
- Edit: `py/tests/viz/test_image_canvas_export.py`

## Steps

- [x] **1.1 — Add the missing helpers to `_TANGA_BRIDGE_SYMBOLS`**
  - In `_scene.py`, extend `_TANGA_BRIDGE_SYMBOLS` with the frame-store helpers
    `storeImageFrame, takeImageFrame, hasImageFrame, registerImageFrameConsumer`
    and the camera-fit helper `applyOrthoFrustum`.
  - These are defined in `templates/image-frames.js` and
    `templates/camera-fit.js` (both bundled before the `js_tanga_bridge()`
    assignment), so the shorthand `{ ... }` bridge resolves them.
- [x] **1.2 — Rebuild the committed bundle**
  - Run `uv run python tools/build-viewer-js.py`; confirm
    `uv run python tools/build-viewer-js.py --check` reports "up to date".
- [x] **1.3 — Regression test**
  - In `test_image_canvas_export.py`, assert `generate_library_js()` contains the
    four symbols inside the `window.__tanga = {...}` assignment, and that the
    animated image-stream HTML destructures `storeImageFrame` from
    `window.__tanga` (so `_playFrame`'s call is no longer a free variable).

## Validation

```
uv run pytest py/tests/viz/test_image_canvas_export.py -q
uv run python tools/build-viewer-js.py --check
```

## Notes

- This only *exposes* already-existing functions; no behaviour change in
  `image-frames.js` itself.
- Keep `decodeImageFrame` out of the bridge — the export path base64-decodes via
  `atob` and never uses the binary wire codec.
- The bundle (`js/tanga-viewer.js`) is generated from `generate_library_js()`;
  its `window.__tanga` object must match `_TANGA_BRIDGE_SYMBOLS`, which is why
  the rebuild is required for `delivery="cdn"`.
