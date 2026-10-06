# Phase 4 — Screen-space marker scale for the off-center pinhole

## Goal

Correct screen-space marker sizing in the calibrated pane (the "can screen-space
scaling work in the background view?" question).

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/templates/camera-fit.js` (`screenWorldScale`)
- Edit: `py/pytanga/viz/templates/view_mode.js` (`applyPinhole`, to retain the
  frustum bounds if needed)

## Steps

- [x] **4.1 — Compute scale from the actual projection**
  - `screenWorldScale` uses `camera.fov` for perspective cameras; the off-center
    pinhole (`makePerspective(left,right,top,bottom,…)`) never updates `fov`, so
    the scale is wrong.  Compute world-units-per-pixel from the actual frustum
    (top/bottom span at the marker's distance) instead — retain the pinhole
    framing bounds in `camera.userData._pinholeFrustum` and use them.
- [x] **4.2 — Verify**
  - `uv run pytest py/tests/viz/test_camera_fit_math.py -q` (added a pinhole-frustum
    case).  Manual smoke: screen-space markers keep a constant on-screen size
    under zoom in the calibrated pane.  (Manual browser smoke — pending.)

## Validation

```
uv run pytest py/tests/viz/test_camera_fit_math.py -q && node --test 'js/dev/tests/*.test.mjs'
```

Manual smoke: markers constant size on zoom in both panes.

## Notes

- Yes — screen-space scaling already works for perspective cameras; only the
  off-center pinhole scale is wrong.  This fixes that one case generally.
