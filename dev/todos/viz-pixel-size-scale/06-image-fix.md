# Phase 6 — Fix the image regression

## Goal

Apply the fix for the background-image visibility regression (root-caused in
Phase 5) and remove the temporary debug output.

## Files

- Edit: whatever the Phase 5 diagnosis points at (likely
  `image-background.js`, `three-view.js`, or the backend frame path)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [x] **6.1 — Implement the fix identified in Phase 5**
  - No rendering fix was needed: the debug showed the background quad is wired
    correctly.  The "image not visible" was the `ActPoint.set_pixel_scale`
    crash in `main()` (fixed in Phase 4 with the `hasattr` guard).
- [x] **6.2 — Remove the `[tanga-debug]` instrumentation from Phase 5**
  - Reverted the `console.log` / `print` additions in `image-background.js`,
    `three-view.js`, and `_layout.py`.
- [x] **6.3 — Regression/smoke**
  - Image renders in the calibrated pane (manual), JS syntax + viz suite pass.

## Validation

`node js/dev/tests/check-syntax.mjs && uv run pytest py/tests/viz -q`

## Notes

- If the diagnosis reveals the image was never a z-convention issue (expected:
  the background quad is an NDC quad with `depthTest:false`), the fix is likely
  a crop/aspect/texture handling change, not a camera flip.
