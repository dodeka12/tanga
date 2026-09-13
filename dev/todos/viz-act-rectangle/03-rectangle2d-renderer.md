# Phase 3 — `Rectangle2D` frontend renderer

## Goal

Render the `Rectangle2D` entity in the browser: an outline rectangle by default
with an optional semi-transparent fill, oriented in the xy-plane.

## Files

- New: `py/pytanga/viz/templates/renderers/rectangle2d.js`
- Edit: `py/pytanga/viz/templates/renderers/factory.js` (create + update)
- (Bundle rebuilt via `tools/build-viewer-js.py` — the export bootstrap picks up
  new renderer modules from `library_source_files`.)

## Steps

- [x] **3.1 — `createRectangle2D(ent)`**
  - Fill (when `ent.style.fill`): a double-sided `THREE.PlaneGeometry(size[0],
    size[1])` mesh with `fill_opacity` (default ~0.2), rotated by `angle` around
    z (and oriented to `normal` if non-+z, mirroring `regular_polygon.js`).
  - Outline (always): a rectangle loop through the 4 corners, using the existing
    fat-line primitive from `line.js`/`utils.js` (`thickness` = pixel width), or
    `THREE.EdgesGeometry` + `LineSegments` if simpler.  Default colour/opacity
    from `ent.style`.
  - Position at `ent.center`; `tagEntity` the returned group.

- [x] **3.2 — factory wiring**
  - `case 'Rectangle2D': createRectangle2D(ent)` in `createEntityMesh`.
  - Add an `updateRectangle2D(mesh, ent, prev)` in `updateEntityMesh` that
    updates center/size/angle/style in place and returns
    `!entityRequiresRebuild(ent, prev)`; rebuild when size changes (geometry).

- [ ] **3.3 — bundle + smoke**
  - `uv run python tools/build-viewer-js.py` and `node --check rectangle2d.js`.

## Validation

`uv run python tools/build-viewer-js.py && node --check py/pytanga/viz/templates/renderers/rectangle2d.js`

## Notes

- Follow the `box.js`/`regular_polygon.js` templates; `utils.js` provides
  `makeMaterial`/`styleParam`/`parseColor`/`tagEntity`/`addWireframeOverlay`.
- No custom `updateRectangle2D` is needed: the generic `updateEntityMesh`
  in-place path updates `center` + style, and `entityRequiresRebuild` already
  rebuilds on `size`/`normal`/`angle` changes (same mechanism `Box` /
  `RegularPolygon` use).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
