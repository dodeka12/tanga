# Phase 5 — Clamp drag delta / line length

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`).
> Frontend/example-only guard; no architecture change.

## Goal

Prevent a spurious over-large drag delta from producing a "very long line" when
the line tool is clicked/dragged, by clamping the world delta (and, for the line,
its length to the canvas extent).

## Files

- Edit: `py/pytanga/viz/templates/interaction.js` (or the example drag handler —
  decided during implementation)
- Edit: `py/examples/apps/calibrated_labeling_app.py` / `image_labeling_app.py` (line length clamp, if app-level)

## Steps

- [x] **5.1 — Pin the over-large-delta source.**
  - Runtime-check `_pixelToWorldDelta` / `_computeScreenPlaneVectors` /
    `screenWorldScale` on the 2D orthographic canvas to identify where the huge
    `world_delta` originates on the first drag move.
- [x] **5.2 — Clamp the delta.**
  - Clamp the computed world delta (e.g. bound its magnitude to a sane multiple of
    the viewport world size, or discard non-finite values) so a single drag step
    can't jump the endpoint far off-canvas.
- [x] **5.3 — Clamp the line length (app-level).**
  - In the line-tool `_on_drag`/`_on_drag_end`, clamp the endpoint to the canvas
    extent (and/or a max length) before `finalize`.

## Validation

`node js/dev/tests/check-syntax.mjs && node --test 'js/dev/tests/*.test.mjs'` + manual smoke of the line tool.

## Notes

- The clamp is the defensive fix; the root cause (step 5.1) is fixed in the same
  phase if it's a clear bug, otherwise the clamp alone gates it.
