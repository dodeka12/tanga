# Phase 6 — Frontend renderers (ellipse line, cone) + factory

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture. If this
> work introduces or changes architecture, update the developer docs.

## Goal

Consume the Phase 5 wire contract on the frontend: draw `Ellipse` as a fat line,
add a `Cone` renderer, and wire `factory.js`.

## Files

- Edit: `py/pytanga/viz/templates/renderers/ellipse.js`
- New: `py/pytanga/viz/templates/renderers/cone.js`
- Edit: `py/pytanga/viz/templates/renderers/factory.js`
- Edit: `py/tests/viz/test_export_renderers.py` (if it snapshots the renderer set)

## Steps

- [ ] **6.1 — `ellipse.js` → fat line.**
  - Sample `N` points `center + (radiusU·cos t) e_u + (radiusV·sin t) e_v` in the
    plane perpendicular to `normal`, and draw with `makeFatLine(color, opacity,
    thickness)` (mirror `hyperbola.js`/`parabola.js`). Read `thickness` via
    `styleParam(ent, 'thickness', 1.0)`. Remove the filled `CircleGeometry` mesh.
- [ ] **6.2 — `cone.js` (new).**
  - Draw a double cone from `vertex`, `axis`, `halfAngle` (`ConeGeometry` +
    `makeMaterial`), oriented along `axis`, with `wireframe` overlay support.
- [ ] **6.3 — `factory.js`.**
  - Add `case 'Cone': mesh = createCone(ent);`. Confirm `ParallelLinePair` already
    routes to `createLinePair` (it does at the `LinePair` case); keep it.
- [ ] **6.4 — Export lockstep.**
  - Ensure the renderer bundle test (`test_export_renderers.py`) still passes;
    add `cone.js` to the expected set if the test enumerates renderers.

## Validation

`node --input-type=module --check py/pytanga/viz/templates/renderers/ellipse.js py/pytanga/viz/templates/renderers/cone.js py/pytanga/viz/templates/renderers/factory.js && uv run pytest py/tests/viz/test_export_renderers.py -q`

## Notes

- `circle.js` was updated in Phase 2; this phase only touches ellipse/cone/factory.
- `factory.js` dispatch is on `ent.kind`; style variants dispatch inside the
  renderer on `ent.style?.style_type` (as `circle.js` does after Phase 2).
