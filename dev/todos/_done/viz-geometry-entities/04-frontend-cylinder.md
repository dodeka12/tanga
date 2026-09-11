# Phase 4 — Frontend `Cylinder` renderer

## Goal

A `templates/renderers/cylinder.js` module that renders a solid cylinder from
the wire contract, plus factory dispatch and export-bundle registration.

## Steps

- [x] **4.1 — `py/pytanga/viz/templates/renderers/cylinder.js`**
  - `createCylinder(ent)`:
    - `color = parseColor(ent, '#44aaff')`, `opacity = styleParam(ent,
      'opacity', 0.9)`, `radius = Math.max(ent.radius || 0.1, 0.001)`,
      `length = Math.max(ent.length || 1.0, 0.001)`.
    - `new THREE.CylinderGeometry(radius, radius, length, 24, 1)` +
      `makeMaterial(color, opacity)`.
    - Center at `origin + normalize(axis) * length / 2` (origin is the cylinder
      **center**, per the contract).
    - Orient via `rotationFromDirection(axis)` (maps +Y → `axis`, matching
      `line.js`'s cylinder path).
    - Optional wireframe overlay via `addWireframeOverlay` when
      `styleParam(ent, 'wireframe', false)` (geometry `* 1.005` like circle).
    - `tagEntity(mesh, ent)`.
  - `updateCylinder(mesh, ent, prev)`:
    - Reposition/reorient in place (same math as `createCylinder`).
    - Return `false` (rebuild) when `length`/`radius`/`axis` changed; otherwise
      `applyStyleUpdate(mesh, ent)` and return `true`.

- [x] **4.2 — `py/pytanga/viz/templates/renderers/factory.js`**
  - Import `createCylinder, updateCylinder`.
  - Add `case 'Cylinder': mesh = createCylinder(ent); break;` in
    `createEntityMesh`.
  - Add `case 'Cylinder': return updateCylinder(mesh, ent, prev);` in
    `updateEntityMesh` (before the generic fallback).

- [x] **4.3 — `py/pytanga/viz/export/_bootstrap/_html.py`**
  - Add `_RENDERERS_DIR / "cylinder.js"` to `_RENDERER_FILES`, inserted **before**
    `factory.js` (currently last). `generate_bootstrap_js` concatenates this
    list into the single `<script type="module">` block used by `render_snapshot`
    / `render_figure`, so the static HTML export bundles `createCylinder` exactly
    like the other renderers (imports and `export` keywords are stripped).
  - Keep `test_renderer_files_match_live_view_directory` and
    `test_bootstrap_defines_every_renderer_function` green (the latter asserts
    `createCylinder` appears in the generated bootstrap).

- [x] **4.4 — Validate**
  - `node --input-type=module --check py/pytanga/viz/templates/renderers/cylinder.js`
    and `uv run pytest py/tests/viz/test_export_renderers.py -q`.
  - Static-export smoke: `render_snapshot(scene.full_state(),
    scene.config.to_dict())` for a scene containing a `Cylinder` and assert
    `"function createCylinder(" in html` (mirrors `test_export_static.py`).

## Validation

`node --input-type=module --check` on `cylinder.js` + `factory.js`;
`uv run pytest py/tests/viz/test_export_renderers.py -q`; static-export smoke
(`render_snapshot` contains `function createCylinder(`).

## Notes

- The cylinder is centered on `origin`; if product later wants a base-point
  semantic, only `createCylinder`/`updateCylinder` and `_serialize_cylinder`
  change — the wire contract stays `origin` + `axis` + `length` + `radius`.
- No texture label support in this phase (Cylinder is not in the
  `texture_label` surface list).
- By riding `factory.js` + `_RENDERER_FILES`, the renderer is available to the
  static HTML export with no extra steps — the live viewer and export bootstrap
  both call the same `createEntityMesh`.
