# Phase 2 — Screen-space point renderers

## Goal

Teach the point renderers to mark screen-space markers, so the view (Phase 3)
can rescale them.  The renderers keep their current geometry build; they only
tag the mesh when `screen_space` is set.  A pure scale helper is added so the
ortho/perspective math is testable.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> renderer recipe (`styleParam` + `tagEntity`) and `camera-fit.js` for the pure
> camera math, so the helper and tagging align with the existing pattern.  No
> architecture change is expected.

## Files

- Edit: `py/pytanga/viz/templates/camera-fit.js` (pure scale helper)
- Edit: `py/pytanga/viz/templates/renderers/square_point.js`
- Edit: `py/pytanga/viz/templates/renderers/circle_point.js`
- Edit: `py/pytanga/viz/templates/renderers/icon_point.js`
- Edit: `py/pytanga/viz/templates/renderers/crosshair_point.js`
- Edit: `py/tests/viz/test_camera_fit_math.py` (helper test)

## Steps

- [x] **2.1 — pure scale helper in `camera-fit.js`**
  - Add `screenWorldScale(camera, viewportPx, worldPos)` (pure, three/DOM-free;
    camera/worldPos are plain objects) returning the world-units-per-CSS-pixel
    scale factor.  Ortho: `(top - bottom) / (viewportPx · zoom)`; perspective:
    `2 · dist · tan(fov/2) / viewportPx`.  Document the formulas.
- [x] **2.2 — square/circle/icon screen-space tag**
  - In each `create*Point`, read `screenSpace = styleParam(ent, 'screen_space', false)`
    and, when true, set `mesh.userData.isScreenSpace = true` (after `tagEntity`).
    Keep the geometry build unchanged — `size`/`thickness` are baked as-is and
    the view scales them.
- [x] **2.3 — crosshair screen-space tag**
  - Same treatment for `createCrossHairPoint` (tag the returned `Group`).
- [x] **2.4 — helper test**
  - In `test_camera_fit_math.py`, assert the ortho formula and the perspective
    distance formula (mirror the existing `clampOrthoView` node tests).
- [x] **2.5 — rebuild bundle**
  - `uv run python tools/build-viewer-js.py`

## Validation

```
node --check py/pytanga/viz/templates/camera-fit.js
node --check py/pytanga/viz/templates/renderers/square_point.js
node --check py/pytanga/viz/templates/renderers/circle_point.js
node --check py/pytanga/viz/templates/renderers/icon_point.js
node --check py/pytanga/viz/templates/renderers/crosshair_point.js
uv run pytest py/tests/viz/test_camera_fit_math.py -q
uv run python tools/build-viewer-js.py --check
```

## Notes

- The z-lift (`size * 0.1`) and any z-thickness are baked into the geometry; the
  view must scale **x/y only** for the flat markers so the lift stays a fixed
  world offset (avoids z-fighting).  Note this for Phase 3.
