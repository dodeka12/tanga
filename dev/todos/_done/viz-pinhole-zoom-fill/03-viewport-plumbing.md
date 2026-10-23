# Phase 3 — Viewport plumbing (view_mode + three-view) and bundle rebuild

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`, §
> "Viewport navigation").  This phase wires the new `pinholeFraming` return
> values through the existing `applyPinhole` → `ThreeJsView` seam; no new message
> or registry.

## Goal

Carry the zoom-scaled letterbox and the base fit half-extents from
`pinholeFraming` into the background quad and the pan clamp, and regenerate the
committed viewer bundle.

## Files

- Edit: `py/pytanga/viz/templates/view_mode.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`
- Regenerate: `js/tanga-viewer.js` (via `tools/build-viewer-js.py`)

## Steps

- [x] **3.1 — Retain the framing result in `applyPinhole` (`view_mode.js`).**
  - In `applyPinhole`, alongside the existing
    `camera.userData._pinholeCrop = f.crop;`, add
    `camera.userData._pinholeLetterbox = { hx: f.hx, hy: f.hy };` and
    `camera.userData._pinholeFit = { hx: f.fitHx, hy: f.fitHy };`.

- [x] **3.2 — Import `setBackgroundLetterbox` (`three-view.js`).**
  - Add `setBackgroundLetterbox` to the existing import from
    `'../renderers/image-background.js'`.

- [x] **3.3 — Apply the letterbox to the background quad.**
  - In `_applyPinholeFraming`, after the existing `setBackgroundCrop(...)` call,
    read `const lb = this.camera.userData._pinholeLetterbox;` and call
    `setBackgroundLetterbox(this._backgroundMesh, lb.hx, lb.hy)` when `lb` is
    present.

- [x] **3.4 — Per-axis pan clamp (`_clampPan`).**
  - Replace the single `lim = 1 - 1 / zoom` with per-axis limits from
    `this.camera.userData._pinholeFit`:
    `const fit = this.camera && this.camera.userData._pinholeFit || { hx: 1, hy: 1 };`,
    `const limX = Math.max(0, 1 - 1 / (fit.hx * zoom));`,
    `const limY = Math.max(0, 1 - 1 / (fit.hy * zoom));`, returning
    `[clamp(pan[0], ±limX), clamp(pan[1], ±limY)]`.

- [x] **3.5 — Rebuild the viewer bundle.**
  - Run `uv run python tools/build-viewer-js.py` and commit the regenerated
    `js/tanga-viewer.js` (and manifest) with the source edits.

## Validation

`uv run python tools/build-viewer-js.py --check && uv run pytest py/tests/viz -q`

## Notes

- Manual smoke (final): `uv run python py/examples/apps/calibrated_labeling_app.py`
  — wheel-zoom in the left pane; the image should grow to fill the pane (black
  bars shrink) and crop at the edges, while the overlaid shapes stay pixel-locked.
- The bundle is content-addressed and incremental; `--check` fails if source JS
  changed without a rebuild, so keep 3.5 in the same phase as the JS edits.
