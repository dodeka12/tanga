# Phase 5 — Frontend `Arc` renderer (with cone arrow tip)

## Goal

A `templates/renderers/arc.js` module that renders an arcing cylinder (partial
torus) with an optional cone arrow tip at its end, plus factory dispatch and
export-bundle registration.

## Steps

- [x] **5.1 — `py/pytanga/viz/templates/renderers/arc.js`**
  - `createArc(ent)`:
    - `color = parseColor(ent, '#ffcc44')`, `opacity = styleParam(ent,
      'opacity', 0.9)`, `radius = Math.max(ent.radius || 1.0, 0.001)`,
      `tubeRadius = Math.max(ent.tubeRadius || 0.05, 0.001)`.
    - `angleRad = THREE.MathUtils.clamp(ent.angle ?? 2 * Math.PI, 0,
      2 * Math.PI)`; build
      `new THREE.TorusGeometry(radius, tubeRadius, 16, 64, angleRad)` (the
      `arc` parameter is already radians — pass it through directly).
    - Build a `THREE.Group` positioned at `origin`.
    - Orientation (arc lies in the plane ⊥ `axis`, starting at `startDirection`):
      1. `qAxis = rotationFromNormal(axis)` (maps +Z → `axis`).
      2. `xPrime = new THREE.Vector3(1, 0, 0).applyQuaternion(qAxis)`.
      3. `qStart = new THREE.Quaternion().setFromUnitVectors(xPrime,
         startDirection)`.
      4. `group.quaternion = qStart.multiply(qAxis)` so the torus's local +X
         (arc angle 0) lands on `startDirection`.
    - Optional wireframe overlay via `addWireframeOverlay` on a matching
      `TorusGeometry` when `styleParam(ent, 'wireframe', false)`.
    - Arrow tip (cone) when `ent.arrow` is truthy:
      - End point (local, before group transform) =
        `(radius·cos(angleRad), radius·sin(angleRad), 0)`; forward tangent
        (CCW) = `(-sin(angleRad), cos(angleRad), 0)`.
      - `new THREE.ConeGeometry(arrow.radius, arrow.length, 16, 1)`, orient +Y →
        tangent via `rotationFromDirection`, position at
        `endPoint + tangent * arrow.length / 2` (base at end, apex ahead).
      - Add the cone to the group so it inherits the group's quaternion/position.
    - `tagEntity(group, ent)`.
  - `updateArc(mesh, ent, prev)`:
    - Reposition/reorient in place; return `false` (rebuild) when
      `radius`/`tubeRadius`/`angle`/`axis`/`arrow` changed; otherwise
      `applyStyleUpdate(mesh, ent)` and return `true`.

- [x] **5.2 — `py/pytanga/viz/templates/renderers/utils.js`**
  - Extend `entityRequiresRebuild` to also return `true` when `ent.angle`,
    `ent.tubeRadius`, or `ent.arrow` differ from `prev` (so the generic update
    path rebuilds the arc on structural change even without the dedicated
    updater).

- [x] **5.3 — `py/pytanga/viz/templates/renderers/factory.js`**
  - Import `createArc, updateArc`.
  - Add `case 'Arc': mesh = createArc(ent); break;` in `createEntityMesh`.
  - Add `case 'Arc': return updateArc(mesh, ent, prev);` in `updateEntityMesh`.

- [x] **5.4 — `py/pytanga/viz/export/_bootstrap/_html.py`**
  - Add `_RENDERERS_DIR / "arc.js"` to `_RENDERER_FILES`, inserted **before**
    `factory.js` so `generate_bootstrap_js` bundles `createArc` into the static
    HTML export (imports and `export` keywords stripped), exactly like the other
    renderers. `render_snapshot` / `render_figure` then render an `Arc` out of
    the box.
  - Keep `test_renderer_files_match_live_view_directory` and
    `test_bootstrap_defines_every_renderer_function` green.

- [x] **5.5 — Validate**
  - `node --input-type=module --check` on `arc.js` + `factory.js` + `utils.js`;
    `uv run pytest py/tests/viz/test_export_renderers.py -q`.
  - Static-export smoke: `render_snapshot(scene.full_state(),
    scene.config.to_dict())` for a scene containing an `Arc` and assert
    `"function createArc(" in html`.

## Validation

`node --input-type=module --check` on `arc.js`/`factory.js`/`utils.js`;
`uv run pytest py/tests/viz/test_export_renderers.py -q`; static-export smoke
(`render_snapshot` contains `function createArc(`).

## Notes

- A full torus (`angle ≥ 2π`) has no end, so the renderer only draws the arrow
  cone for a genuine partial arc (`arrow && angle < 2π`); the serializer still
  emits the resolved `arrow` config whenever `show_arrow` is `True`.
- `TorusGeometry`'s `arc` starts at local +X and sweeps CCW; aligning +X →
  `startDirection` and +Z → `axis` fully determines the arc's placement.
- Registered in `_RENDERER_FILES`, the renderer is bundled into static HTML
  export automatically — the same `createEntityMesh` dispatch the live viewer
  uses, so no separate export renderer is needed.
