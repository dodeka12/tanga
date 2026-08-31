# Phase 4 — Frontend renderers

## Goal

Six Three.js renderer modules, dispatched by `factory.js` and registered in the
export bundle so the live viewer and static HTML export render them identically.

## Files

- New: `py/pytanga/viz/templates/renderers/disk.js`
- New: `py/pytanga/viz/templates/renderers/partial_disk.js`
- New: `py/pytanga/viz/templates/renderers/box.js`
- New: `py/pytanga/viz/templates/renderers/ellipsoid.js`
- New: `py/pytanga/viz/templates/renderers/ellipse.js`
- New: `py/pytanga/viz/templates/renderers/regular_polygon.js`
- Modify: `py/pytanga/viz/templates/renderers/factory.js`
- Modify: `py/pytanga/viz/export/_bootstrap/_html.py` (`_RENDERER_FILES`)

## Steps

- [x] **4.1 — `disk.js`**
  - Thin `CylinderGeometry(radius, radius, thickness, 32, 1)` oriented along the
    `normal` (reuse `rotationFromNormal`); `thickness` read from
    `styleParam(ent, 'thickness', 0.02)`.

- [x] **4.2 — `partial_disk.js`**
  - `CylinderGeometry(radius, radius, thickness, 32, 1, false, 0, angle)` — a
    pie-slab using `thetaStart`/`thetaLength`; oriented along `normal`.
    `angle` from `ent.angle` (radians, clamped to `[0, 2π]`), `startDirection`
    from `ent.startDirection`.

- [x] **4.3 — `box.js`**
  - `BoxGeometry(size[0], size[1], size[2])`; `center` position; `rotation`
    (Euler) applied via `mesh.rotation.set(...)` when present.

- [x] **4.4 — `ellipsoid.js`**
  - `SphereGeometry(1, 32, 32)` scaled by `radii` via `mesh.scale.set(...)`.

- [x] **4.5 — `ellipse.js`**
  - `CircleGeometry(1, 64)` scaled to `(radiusU, radiusV, 1)`; oriented along
    `normal`. Read `thickness` (used to orient the thin slab in the 2D case;
    for the flat mesh, thickness only matters if a wireframe prism is desired).

- [x] **4.6 — `regular_polygon.js`**
  - `CylinderGeometry(radius, radius, thickness, sides, 1)` — a regular `sides`
    prism (flat slab); oriented along `normal`; apply in-plane `angle` by
    rotating around `normal`.

- [x] **4.7 — `factory.js`**
  - Add `case 'Disk'/'PartialDisk'/'Box'/'Ellipsoid'/'Ellipse'/'RegularPolygon'`
    to `createEntityMesh`, plus generic position/rotation handling in
    `updateEntityMesh` (these are simple shapes with no bespoke updater).

- [x] **4.8 — Export bundle (`_html.py`)**
  - Add the six new modules to `_RENDERER_FILES` so `generate_bootstrap_js`
    concatenates them (imports/`export` keywords stripped).

- [x] **4.9 — Validate**
  - `node --input-type=module --check` each new renderer + `factory.js`.
  - `uv run pytest py/tests/viz/test_export_renderers.py -q`.

## Validation

`uv run pytest py/tests/viz/test_export_renderers.py -q` +
`node --input-type=module --check <each new renderer> factory.js`

## Notes

- Use `makeMaterial`, `parseColor`, `styleParam`, `rotationFromNormal`,
  `tagEntity`, `addWireframeOverlay` from `utils.js` (like `cylinder.js` /
  `circle.js`).
- Wireframe overlays are optional but encouraged to match `SphereStyle`/
  `CircleStyle` behavior.
- The slab thickness comes from the resolved `style.thickness` (Phase 2/3), so
  the mesh and SDF paths agree.
