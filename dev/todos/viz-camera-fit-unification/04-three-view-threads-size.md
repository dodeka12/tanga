# Phase 4 — `three-view.js` passes the pane size

## Goal

Pass the pane's measured width/height into `fitCamera` and `switchToCamera`.

## Files

- Edit: `py/pytanga/viz/templates/views/three-view.js`

## Steps

- [x] **4.1 — `fitCamera()` passes pane size**
  - Change the `fitCamera(...)` call to pass
    `this.width || window.innerWidth, this.height || window.innerHeight` as the
    final two arguments (mirroring `resize()`).

- [x] **4.2 — `_applyCamera()` passes `viewWidth`/`viewHeight`**
  - Replace the `viewAspect` computation with
    `const viewWidth = this.width > 0 ? this.width : null;` and the
    `viewHeight` equivalent.
  - Pass them as the new 5th/6th args to `switchToCamera(...)`.

## Validation

`node --check py/pytanga/viz/templates/views/three-view.js`

## Notes

- `this.width`/`this.height` come from `view.js`'s `ResizeObserver`; they are
  `0` until the pane is laid out, hence the `|| window.innerWidth` /
  `> 0 ? … : null` fallbacks that `resize()` already uses.
