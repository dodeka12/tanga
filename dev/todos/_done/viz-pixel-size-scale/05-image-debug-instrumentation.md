# Phase 5 — Image visibility debug instrumentation

## Goal

Add temporary debug output on both sides to pinpoint why the calibrated
background image is no longer visible, without changing behaviour.

## Files

- Edit: `py/pytanga/viz/templates/renderers/image-background.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`
- Edit: `py/pytanga/viz/_image_wire.py` (and/or the background-image send path)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [x] **5.1 — Frontend: background quad state**
  - `image-background.js` `createImageBackground` / `updateImageBackground` log
    `[tanga-debug] bgImage {…}` (width, height, source, imageAspect, paneAspect,
    crop, textureLoaded), once per build/update.
- [x] **5.2 — Frontend: pane background wiring**
  - `three-view.js` `setBackgroundImage` logs the imageMeta + reuse flag;
    `_applyPinholeFraming` logs `vp` + `pinholeCrop`.
- [x] **5.3 — Backend: background frame send**
  - `_layout.py` `_collect_background_frames` prints `[tanga-debug] bg-frame`
    (id, shape, codec, bytes) when a frame is queued.

## Validation

`uv run python py/examples/apps/calibrated_labeling_app.py` (manual) — capture
the browser console and terminal output; record the `[tanga-debug]` lines.

## Notes

- These messages are temporary and removed in Phase 6.
- The expected signal: confirm whether `uImage` is a loaded texture, whether
  `uCrop`/`uPaneAspect`/`uImageAspect` are sane, and whether the backend frame
  reaches the pane.
