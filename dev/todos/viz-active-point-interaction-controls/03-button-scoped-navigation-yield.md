# Phase 3 — Button-scoped navigation yield (frontend)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`).
> This refines the existing per-pane gesture-arbitration predicate; no new seam.

## Goal

A pane with only a left-button surface drag no longer suppresses right-button pan.

## Files

- Edit: `py/pytanga/viz/templates/interaction.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`

## Steps

- [x] **3.1 — Report armed buttons.**
  - In `InteractionController`, add `armedSurfaceButtons()` returning a `Set` of
    button-name strings: for each `drag` trigger in
    `this._surface.interaction.triggers`, if `t.mouse_button == null` add all of
    `'left'`/`'middle'`/`'right'`, otherwise add `t.mouse_button`.  Return
    `new Set()` when there is no surface / the surface is disabled.
- [x] **3.2 — Reimplement `hasArmedSurface()`.**
  - Return `this.armedSurfaceButtons().size > 0` (keeps the existing boolean
    semantics for any other caller).
- [x] **3.3 — Scope the pan skip by button.**
  - In `three-view.js` `_onViewportPointerDown(e)`: after the existing
    `if (this._interaction && this._interaction.isDragActive()) return;` gate, map
    `e.button` (`0`→`'left'`, `1`→`'middle'`, `2`→`'right'`) and return early when
    that button is in `this._interaction.armedSurfaceButtons()`; keep the existing
    `if (e.button !== 0 && e.button !== 2) return;`.
  - Leave `_interactionActive()` / `_onViewportPointerMove` as-is (a drag that
    starts mid-pan still stops the pan regardless of button).

## Validation

`node js/dev/tests/check-syntax.mjs`

## Notes

- Manual smoke: `uv run python py/examples/apps/calibrated_labeling_app.py` —
  arm a draw mode (left-button surface drag) and confirm right-click still pans.
