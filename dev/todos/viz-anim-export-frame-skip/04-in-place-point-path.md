# Phase 4 — `PointPath` updates in place

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs
> (phase 6 writes up the extended `update<Kind>` contract this phase starts).

## Goal

A `PointPath` whose points/colours change rewrites its fat-segment geometry
instead of being disposed and rebuilt.  After phase 2 the only remaining
rebuilds are entities that genuinely changed — a growing trace is the most
common kind in real use, so this is where the remaining per-frame churn lives.

## Files

- Edit: `py/pytanga/viz/templates/renderers/point_path.js`
- Edit: `py/pytanga/viz/templates/renderers/utils.js`
  (`applyStyleUpdate` split + `entityRequiresRebuild` short-circuit removal)
- New: `py/tests/viz/test_export_inplace_updaters.py`

## Steps

- [x] **4.1 — Split the opacity part out of `applyStyleUpdate` (`utils.js`)**
  - Extract the opacity / `fill_opacity` traversal (the whole
    `if (opacity !== undefined || fillOpacity !== undefined) { … }` block,
    lines ~329-363) into `export function applyOpacityUpdate(mesh, ent)`.
  - `applyStyleUpdate` becomes: `applyOpacityUpdate(mesh, ent)` + the existing
    colour block + the existing `ent.scale` block.  Behaviour must be
    **identical** — no other caller changes.
  - JSDoc both: `applyStyleUpdate` = opacity + colour + scale;
    `applyOpacityUpdate` = opacity only, safe for meshes whose colour comes from
    vertex attributes (a `LineMaterial` colour multiplies vertex colours, so the
    colour block must not run there).

- [x] **4.2 — Extract the flattening helpers (`point_path.js`)**
  - Add `function hasVertexColors(ent)` →
    `(ent.colors || []).some((c) => c !== null && c !== undefined)`
    (the same predicate `createPointPath` inlines today).
  - Add `function flattenPath(points, perPointColors, uniformColor)` returning
    `{ positions, vertexColors }`, built from the existing segment loop of
    `createPointPath` (verbatim: `numVertices = (n - 1) * 2`, `_resolveColor`
    per endpoint, `null` → uniform colour).
  - `createPointPath` calls both helpers; its output is unchanged.

- [x] **4.3 — Rewrite `updatePointPath`**
  ```js
  export function updatePointPath(mesh, ent, prev) {
      if (!prev) return false;
      // Coloured ↔ uniform switches the material (vertexColors flag) → recreate.
      if (hasVertexColors(ent) !== hasVertexColors(prev)) return false;
      // Non-cheap style fields (line_thickness, …) are create-time inputs.
      if (styleNeedsRebuild(ent, prev)) return false;
      const points = ent.points || [];
      if (points.length < 2) return false;          // degenerate → recreate
      if (!mesh.geometry || typeof mesh.geometry.setPositions !== 'function') return false;

      const colored = hasVertexColors(ent);
      const { positions, vertexColors } = flattenPath(
          points, ent.colors || [], parseColor(ent, '#ffffff'));
      mesh.geometry.setPositions(positions);
      if (colored && vertexColors) mesh.geometry.setColors(vertexColors);
      mesh.geometry.computeBoundingBox();
      mesh.geometry.computeBoundingSphere();
      if (colored) applyOpacityUpdate(mesh, ent);
      else applyStyleUpdate(mesh, ent);
      if (mesh.material && mesh.material.dashed) mesh.computeLineDistances();
      return true;
  }
  ```
  - Imports to add: `applyOpacityUpdate` from `./utils.js`,
    `styleNeedsRebuild` from `./style-diff.js`.
  - Docstring: the fat-line geometry is rewritten from `points`/`colors`;
    a change of *representation* (uniform ↔ per-vertex colour) or of a
    create-time style field still returns `false`.
  - Note: the `mesh` for a `<2`-point path is a plain `THREE.Group` (no
    geometry) — the `setPositions` guard plus the `<2` check cover it, so the
    `createPointPath` group/line transition still rebuilds.

- [x] **4.4 — Drop the blanket `PointPath` rebuild (`utils.js`)**
  - `entityRequiresRebuild`: delete `if (ent.kind === 'PointPath') return true;`
    (the kind now owns the decision via `updatePointPath`).
  - Also drop the now-unused `PointPath` mention from the function's JSDoc if
    the comment refers to it.

- [x] **4.5 — Structural regression test (`test_export_inplace_updaters.py`)**
  - SPDX + copyright header; module docstring: renderer modules import
    `three`, which is not installed in `js/dev/node_modules`, so `node --test`
    cannot load them — the emitted-library text plus
    `js/dev/tests/anim-export-smoke.mjs` are the guard (behavioural gate).
  - Read `point_path.js` from `_RENDERERS_DIR` (same helper style as
    `test_export_renderers.py`) and assert:
    - `"export function updatePointPath"` exists and its body **contains**
      `"setPositions("` and `"hasVertexColors"` (in-place rewrite);
    - `"export function flattenPath"` and `"export function hasVertexColors"`
      exist and `createPointPath` calls `flattenPath(`;
    - the updater's first statement is not a bare `return false;` (the
      regression this phase removes) — check the text between the signature and
      the first `return false;` contains `if (`.
  - Read `utils.js` and assert:
    - `"export function applyOpacityUpdate"` exists, and the body of
      `applyStyleUpdate` calls it;
    - the body of `entityRequiresRebuild` no longer contains
      `"ent.kind === 'PointPath'"`.
  - In `generate_library_js()` assert both helpers survive import stripping
    (`"function applyOpacityUpdate("` and `"function flattenPath("`).
  - Cross-check the routing: `factory.js` still lists
    `case 'PointPath':` followed by `return updatePointPath(...)`.

## Validation

```bash
uv run pytest py/tests/viz -q && (cd js/dev && npm run check && npm test)
node js/dev/tests/anim-export-smoke.mjs <url>
```

Smoke: the growing `PointPath` of the phase-1 scene must show up in `updated`
(not `created`/`removed`) and the rebuild budget keeps holding.

## Notes

- Verified entity shape (scratch probe): a `PointPath` entity carries
  `points`, `colors`, flat `color`/`opacity`/`line_thickness`, and
  `style: {style_type: 'PointPathStyle', color, opacity, line_thickness}`.
  `line_thickness` therefore lives in `style` **and** is compared by
  `styleNeedsRebuild` — no extra field check is needed in the updater.
- A fallback-`color` change on a *per-vertex-coloured* path is applied in place
  because `flattenPath` re-resolves every `null` colour on each call — and the
  colour block of `applyStyleUpdate` is deliberately skipped there (it would
  tint the white base colour and multiply into the vertex colours).
- `LineSegmentsGeometry.setPositions` reallocates both instanced attributes, so
  a path that grows or shrinks works without touching the material.
- Raycast hit-testing and the camera fit read the geometry bounds, hence the
  explicit `computeBoundingBox()` / `computeBoundingSphere()` after the
  rewrite.
