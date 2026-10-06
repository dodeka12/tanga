# Phase 3 — `Act*` rendering over the background in the pinhole pane

## Goal

Make the `Act*` entities (bodies + handles) render over the background image in
the calibrated pane, so shapes can be created, selected, and edited there.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Investigate: `py/pytanga/viz/templates/renderers/line.js`, `circle.js`,
  `point.js`, `factory.js`, `utils.js`; `three-view.js` render/resize path.

## Steps

- [ ] **3.1 — Reproduce and isolate**
  - In the browser confirm: orbit pane shows the shapes, the pinhole pane does
    not.  Check the fat-line `resolution` uniform (`updateLineResolutions`) is
    correct **per pane** for the pinhole pane, and that the bodies are not
    occluded by the NDC background (`depthTest:false` / `renderOrder:-1`).
- [ ] **3.2 — Fix the root cause**
  - Fix the rendering issue (per-pane line resolution / depth / material) so
    bodies and handles render over the background in the pinhole pane.
- [ ] **3.3 — Test / document**
  - Add a JS/Python test if the fix is testable headlessly; otherwise record the
    manual smoke in the example's docs.

## Validation

```
node --test 'js/dev/tests/*.test.mjs' && node js/dev/tests/check-syntax.mjs
```

Manual smoke: shapes + handles visible in both panes.

## Notes

- This is a rendering bug in the calibrated path, not an architecture change.
  The leading hypothesis is the fat-line screen-space `resolution` not being set
  per pane; confirm before fixing.
