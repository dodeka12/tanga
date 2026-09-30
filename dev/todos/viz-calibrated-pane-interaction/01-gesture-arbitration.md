# Phase 1 — Per-pane gesture arbitration

## Goal

Introduce a single per-pane "interaction armed / active" signal and make the
viewport-crop pan yield to it, so a draw-drag no longer also pans the background.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/templates/interaction.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`

## Steps

- [ ] **1.1 — `InteractionController.hasArmedSurface()` / `isDragActive()`**
  - `hasArmedSurface()` returns true when `this._surface` has
    `interaction.enabled` and at least one drag/click trigger.
  - `isDragActive()` returns `!!this._activeDrag`.
- [ ] **1.2 — Viewport pan yields**
  - In `three-view.js` `_onViewportPointerDown` / `_onViewportPointerMove`, skip
    when `this._interaction` reports `hasArmedSurface() || isDragActive()`.
  - Also gate pan on the pan mouse button(s) rather than any pointerdown.

## Validation

```
node js/dev/tests/check-syntax.mjs
```

Manual smoke: arm a tool and drag — the background image must not move.

## Notes

- This is the only new seam; it makes both labelers' mode-switch drive the same
  navigation-yield behaviour.
- OrbitControls already yields via `controls.enabled = false`; this phase brings
  the custom viewport-crop pan up to parity.
