# Phase 5 — Canonical-shape renderers + update simplification

## Goal

Rewrite the placement-baking renderers to draw **canonical shapes** (no
`mesh.position`/`setRotationFromQuaternion`/baked-center) and simplify the
`update<Kind>()` path: placement is now the `transform` aspect, so updaters only
rebuild on shape change and rebuild on non-color/opacity style change.

## Files

- Edit: `py/pytanga/viz/templates/renderers/point.js`, `circle.js`,
  `ellipse.js`, `hyperbola.js`, `parabola.js`, `cone.js`, `cylinder.js`,
  `line.js`, `direction.js`, `arc.js`, `sphere.js`, `disk.js`,
  `partial_disk.js`, `box.js`, `ellipsoid.js`, `regular_polygon.js`,
  `rectangle2d.js`, `plane.js`, `plane_pair.js`, `line_pair.js`
- Edit: `py/pytanga/viz/templates/renderers/factory.js` (generic fallback)

## Steps

- [x] **5.1 — canonical shapes**
  - For each listed renderer, remove baked placement and emit the shape at the
    canonical frame (README): linear along +Y, planar in XY (+Z), volumes at
    origin axis-aligned. E.g. `circle.js` drops `mesh.position.set(center)` and
    `setRotationFromQuaternion(normal)` and the line variant stops baking
    `center` into points; `cylinder.js`/`cone.js`/`line.js`/`direction.js` draw
    along +Y; `box.js`/`ellipsoid.js` drop `mesh.position`/`mesh.rotation`;
    `plane.js` draws in XY; `ellipse/hyperbola/parabola` center/vertex at origin.

- [x] **5.2 — simplify `update<Kind>()`**
  - Drop repositioning (no `mesh.position`/`setRotationFromQuaternion`); keep
    shape-change rebuild checks (`contentChanged`/`approxEqual`) and add the
    `styleNeedsRebuild(ent, prev) → return false` guard (port from the
    superseded parity plan) since `applyStyleUpdate` still only handles
    color/opacity/scale.

- [x] **5.3 — generic fallback in `factory.js`**
  - Remove the in-place `center`/`position`/`vector`/`direction`/`rotation`
    re-application (`factory.js:283-306`); placement is now the `transform`
    aspect. Keep `applyStyleUpdate` + `return !entityRequiresRebuild(ent, prev)`.

- [x] **5.4 — syntax check**
  - `node --check` every edited renderer.

## Validation

`for f in point circle ellipse hyperbola parabola cone cylinder line direction arc sphere disk partial_disk box ellipsoid regular_polygon rectangle2d plane plane_pair line_pair factory; do node --check py/pytanga/viz/templates/renderers/$f.js; done`

## Notes

- `entityRequiresRebuild` (`utils.js`) keeps its creation-only field list; after
  this phase the only in-place mutations left are color/opacity/scale.
- The `Circle`-center bug is resolved structurally: a center change is now a
  `transform` patch applied to the group, not a content patch the renderer must
  re-apply.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
