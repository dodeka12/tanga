# Phase 6 — Pinhole crop-window framing

## Goal

Extend `pinhole-framing.js` to accept a viewport crop window and return **both**
the sub-frustum bounds **and** the background image crop, so a zoomed/panned
pinhole overlay stays pixel-locked to its background image. Add the Node math
test that locks the crop contract.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/templates/pinhole-framing.js`
- Edit: `py/pytanga/viz/templates/renderers/image-background.js`
- Edit: `py/tests/viz/test_pinhole_math.py`

## Steps

- [x] **6.1 — crop window in `pinholeFraming`**
  - Accept an optional `crop` (`{zoom, pan}` → an image-pixel sub-rectangle
    `[u0,u1]×[v0,v1]`, default full image).
  - Map the crop onto the full-image frustum bounds
    (`left↔u=0`, `right↔u=W`, `top↔v=0`, `bottom↔v=H`) to the sub-frustum
    `{left', right', top', bottom'}`.
  - Return the sub-frustum **and** a background crop
    `{u0, v0, scale, hx, hy}` alongside the existing `near/far`.
- [x] **6.2 — `image-background.js` consumes the crop**
  - Add crop uniforms; sample the image sub-region (offset + scale in the
    existing letterboxed `texture2D` call) instead of the whole image, so the
    image zooms/pans with the projection.
  - Keep the data-path `flipY = true` fix intact.
- [x] **6.3 — `view_mode.js` `applyPinhole` uses the crop**
  - Pass the pane's viewport state into `pinholeFraming`; the projection and the
    background consume the same returned window.
- [x] **6.4 — Node test (`test_pinhole_math.py`)**
  - Assert the full-image (no crop) case is unchanged (regression).
  - Assert a `zoom=2` centred crop halves the frustum span and centres it; assert
    a `pan` shifts the sub-frustum/background crop by the expected amount.

## Validation

```
uv run pytest py/tests/viz/test_pinhole_math.py -q && uv run python tools/build-viewer-js.py --check
```

## Notes

- Keep `pinholeFraming` pure (`three`/DOM-free) — it is Node-tested.
- The crop math must stay the single source of truth for both the frustum and
  the background (same invariant as the existing `{hx, hy}`).
