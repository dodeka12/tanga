# Phase 2 — Object-oriented rebuild detection (frontend)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture. If this
> work introduces or changes architecture, update the developer docs.

## Goal

Replace the flat, kind-agnostic `entityRequiresRebuild` field list with
per-kind `update*` functions so each renderer owns its own rebuild decision —
fixing "hyperbolas only show the first time".

## Files

- Edit: `py/pytanga/viz/templates/renderers/hyperbola.js`
- Edit: `py/pytanga/viz/templates/renderers/parabola.js`
- Edit: `py/pytanga/viz/templates/renderers/ellipse.js`
- Edit: `py/pytanga/viz/templates/renderers/circle.js`
- Edit: `py/pytanga/viz/templates/renderers/line_pair.js`
- Edit: `py/pytanga/viz/templates/renderers/point_set.js`
- Edit: `py/pytanga/viz/templates/renderers/cone.js`
- Edit: `py/pytanga/viz/templates/renderers/factory.js`
- Edit: `py/pytanga/viz/templates/renderers/utils.js`

## Steps

- [x] **2.1 — Add `update*` to the curve renderers.**
  - `updateHyperbola(mesh, ent, prev)`: return `false` when `a`, `b`, `dir1`,
    `dir2`, or `center` changed (rebuild); else `applyStyleUpdate` and return
    `true`.
  - `updateParabola`: return `false` when `vertex`, `direction`, or `p` changed.
  - `updateEllipse`: return `false` when `radiusU`, `radiusV`, `dirU`, `dirV`,
    `normal`, or `center` changed.
  - `updateCircle`: return `false` when `radius`, `normal`, `tubeRadius`, or the
    `style_type` (tube ↔ thick-line) changed.
  - `updateLinePair`: return `false` when `line1` or `line2` changed.
  - `updatePointSet`: return `false` when `points` changed.
  - `updateCone`: return `false` when `vertex`, `axis`, or `halfAngle` changed.
  - Use a small shared `_contentChanged(ent, prev, keys)` helper (or reuse
    `approxEqual`/`JSON.stringify` from `utils.js`) rather than duplicating the
    comparison inline.
- [x] **2.2 — Dispatch in `factory.js`.**
  - Add `case 'Hyperbola': return updateHyperbola(...)`, and the same for
    `Parabola`, `Ellipse`, `Circle`, `LinePair`, `ParallelLinePair`, `PointSet`,
    `Cone` in `updateEntityMesh` (import the new `update*` functions).
- [x] **2.3 — Shrink `entityRequiresRebuild`.**
  - Remove the per-kind geometry-field lists that are now owned by `update*`
    (`a`, `b`, `dir1`, `dir2`, `vertex`, `p`, `radiusU/radiusV`, `dirU/dirV`,
    `tubeRadius`, `halfAngle`, …). Keep only the truly kind-agnostic checks:
    kind change and non-color/opacity style change (`styleNeedsRebuild`), plus
    the special kinds that still need it (`PointPath`, `sdf`, `Axis*`, `Grid`).
  - Verify the remaining kinds (Point, Sphere, Plane, Box, Disk, …) still
    rebuild correctly via the generic path.
- [x] **2.4 — Tests.**
  - `node --check` each touched renderer; run
    `uv run pytest py/tests/viz/test_export_renderers.py -q`.

## Validation

`node --check py/pytanga/viz/templates/renderers/{hyperbola,parabola,ellipse,circle,line_pair,point_set,cone,factory,utils}.js && uv run pytest py/tests/viz/test_export_renderers.py -q`

## Notes

- `update*` follows the existing `updateLine`/`updateArc`/`updateCylinder`
  convention (return `false` = rebuild, `true` = applied in place).
- `factory.js` already imports `applyStyleUpdate`, `entityRequiresRebuild`, and
  `tagEntity` from `utils.js`; keep the shared helpers there.
