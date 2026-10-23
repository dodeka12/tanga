# Phase 1 — Frontend LOD hysteresis + generation token

## Goal

Kill the resolution toggle: `levelForScreen` gains hysteresis around power-of-two
boundaries, and `updateImageLod` uses a monotonic generation token so a stale
in-flight fetch can never overwrite a newer texture.

## Files

- Edit: `py/pytanga/viz/templates/renderers/image-tiles.js`
- Edit: `py/pytanga/viz/templates/renderers/image.js`
- Edit: `js/dev/tests/image-tiles.test.mjs`
- Regenerate: `js/tanga-viewer.js` (via `tools/build-viewer-js.py`)

## Steps

- [x] **1.1 — Add hysteresis to `levelForScreen` (`image-tiles.js`)**
  - Implement the exact `_HYSTERESIS` / `_levelResolution` / `levelForScreen`
    logic from the README "Fixed contract" (optional integer `currentLevel`,
    ±2% dead-band, backward-compatible with the current 2-arg call sites).
  - Keep the existing `levelForScreen(pyramid, screenLongSide)` behavior when
    `currentLevel` is omitted (returns the ideal level).

- [x] **1.2 — Generation token in `updateImageLod` (`image.js`)**
  - Change `levelForScreen(layer.img, maxDim)` to
    `levelForScreen(layer.img, maxDim, layer.level)`.
  - Replace the bare `pendingLevel` supersede logic with `pendingLevel` +
    `generation`: capture `const gen = (layer.generation || 0) + 1` before the
    fetch, bump `layer.generation` when starting **and** when cancelling an
    in-flight fetch, and only swap the texture when `layer.generation === gen`.
  - No event emission yet (Phase 4).

- [x] **1.3 — Unit-test the hysteresis (`image-tiles.test.mjs`)**
  - Add cases: a boundary value holds the coarser level until the screen clearly
    exceeds the finer threshold (`*(1 + 0.02)`), and holds the finer level until
    it clearly falls below (`*(1 - 0.02)`); a big jump still changes level.
  - Assert the 2-arg call (no `currentLevel`) still returns the ideal level.

## Validation

```
node --test js/dev/tests/image-tiles.test.mjs && node js/dev/tests/check-syntax.mjs && uv run python tools/build-viewer-js.py
```

## Notes

- `image-background.js` shares `updateImageLod` and `levelForScreen`, so the fix
  covers both the scene `image` entity and the `background_image` quad with no
  further edits.
- `_tiledLayers.push({ img, index, level })` sites need no change: the new
  `pendingLevel`/`generation` fields are lazily initialized (`undefined`/`0`).
