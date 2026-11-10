# Phase 5 — `Axis` / `Axes2D` / `Axes3D` / `Grid` update in place

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs
> (phase 6 records the extended updater contract).

## Goal

A changing axis or grid refills its existing entity instead of being disposed
and recreated.  Rebuilding an `Axis`/`Axes2D`/`Axes3D` destroys and recreates
its CSS2D label DOM nodes (one per value tick plus the name label) — the most
expensive part of the current per-frame churn after phases 2–4.

## Files

- Edit: `py/pytanga/viz/templates/renderers/utils.js` (`clearGroupChildren`,
  `entityRequiresRebuild`)
- Edit: `py/pytanga/viz/templates/renderers/axis.js` (`updateAxis`)
- Edit: `py/pytanga/viz/templates/renderers/axes2d.js` (`updateAxes2D`)
- Edit: `py/pytanga/viz/templates/renderers/axes3d.js` (`updateAxes3D`)
- Edit: `py/pytanga/viz/templates/renderers/grid.js` (`updateGrid`)
- Edit: `py/pytanga/viz/templates/renderers/factory.js` (route the five kinds)
- Edit: `py/tests/viz/test_export_inplace_updaters.py` (extend)

## Steps

- [x] **5.1 — `clearGroupChildren(group, { disposeMaterials = true } = {})` (`utils.js`)**
  - Walk `group.children` backwards: detach CSS2D elements first (same reason as
    `removeEntityMesh`: `Object3D.remove()` does not dispose nested CSS2D DOM,
    so labels would linger as ghosts), then dispose geometry and (optionally)
    material, then `group.remove(child)`.
  - `disposeMaterials: false` is for callers that keep a shared material (the
    grid uses one material for every segment line).
  - JSDoc: empty the group for an in-place refill, leaving the group object
    (and therefore `userData`, parents, transforms and the registry entry)
    intact.

- [x] **5.2 — `updateAxis` (`axis.js`)**
  - Import `contentChanged`, `applyStyleUpdate`, `clearGroupChildren` from
    `./utils.js` and `styleNeedsRebuild` from `./style-diff.js`.
  - ```js
    export function updateAxis(mesh, ent, prev) {
        if (!prev) return false;
        // value_style / label_style are create-time (font, offsets, align).
        if (styleNeedsRebuild(ent, prev)) return false;
        if (contentChanged(ent, prev, [
            'start', 'end', 'majorInterval', 'ticks', 'showValueLabels',
            'valueFormat', 'valueStart', 'valueStep', 'label', 'showTicks',
        ])) {
            clearGroupChildren(mesh);
            addAxis(mesh, ent);
        }
        applyStyleUpdate(mesh, ent);
        return true;
    }
    ```
  - `addAxis` keeps its signature/behaviour (shared by `createAxis`,
    `createAxes2D`, `createAxes3D`) — do **not** fork the drawing code; the
    in-place path empties the group and calls the same builder.
  - `createAxis` unchanged.  Docstring: refilling keeps the group (and its
    parent/transform) so only the axis' own lines and labels are recreated, and
    a pure `color`/`opacity` change recreates nothing at all.

- [x] **5.3 — `updateAxes2D` / `updateAxes3D` (`axes2d.js`, `axes3d.js`)**
  - Same shape, keyed on `contentChanged(ent, prev, ['axes'])`: on change
    `clearGroupChildren(mesh)` then re-add every axis via `addAxis`; then
    `applyStyleUpdate(mesh, ent)`; `return true`.
  - `styleNeedsRebuild` gate first (returns `false` → rebuild) and
    `if (!prev) return false;`.
  - Per-axis colours/labels live inside `ent.axes[i]`, so they are covered by
    the `axes` content comparison.

- [x] **5.4 — `updateGrid` (`grid.js`)**
  - Extract from `createGrid`, without changing its output:
    - `_gridSegments(ent)` → the ordered `[a, b]` `Vector3` pairs currently
      added by the two `addLine` loops (including the
      `line_positions_u` / `line_positions_v` variants);
    - `_gridMaterial(ent)` → `makeLineMaterial(parseColor(ent, '#555555'),
      styleParam(ent, 'opacity', 0.5), styleParam(ent, 'line_thickness', 1))`.
  - `createGrid` iterates `_gridSegments` with one shared `_gridMaterial`.
  - Imports to add in `grid.js`: `applyStyleUpdate`, `clearGroupChildren` from
    `./utils.js` and `styleNeedsRebuild` from `./style-diff.js`.
  - ```js
  export function updateGrid(mesh, ent, prev) {
      if (!prev) return false;
      if (styleNeedsRebuild(ent, prev)) return false;
      const segs = _gridSegments(ent);
      const lines = mesh.children.filter(
          (c) => c.geometry && typeof c.geometry.setPositions === 'function');
      if (lines.length === segs.length && lines.length === mesh.children.length) {
          // Same segment count → rewrite each line's positions, reuse material.
          for (let i = 0; i < segs.length; i++) {
              const [a, b] = segs[i];
              lines[i].geometry.setPositions([a.x, a.y, a.z, b.x, b.y, b.z]);
              lines[i].geometry.computeBoundingSphere();
          }
      } else {
          const material = lines.length ? lines[0].material : _gridMaterial(ent);
          clearGroupChildren(mesh, { disposeMaterials: false });
          for (const [a, b] of segs) mesh.add(makeFatLineWithMaterial([a, b], material));
      }
      applyStyleUpdate(mesh, ent);
      return true;
  }
  ```

- [x] **5.5 — Narrow `entityRequiresRebuild` + wire the dispatcher**
  - `utils.js::entityRequiresRebuild`: delete the
    `if (ent.kind === 'Axis' || ent.kind === 'Axes2D' || ent.kind === 'Axes3D')
    return true;` and `if (ent.kind === 'Grid') return true;` blocks **and** the
    three-line comment that justifies them ("Axes/grids are drawn fresh … e.g.
    a live time axis whose ticks move each frame") — replace it with a pointer
    that those kinds own the decision in their co-located updaters.
  - `factory.js::updateEntityMesh`: add cases next to the existing ones
    ```js
    case 'Axis':    return updateAxis(mesh, ent, prev);
    case 'Axes2D':  return updateAxes2D(mesh, ent, prev);
    case 'Axes3D':  return updateAxes3D(mesh, ent, prev);
    case 'Grid':    return updateGrid(mesh, ent, prev);
    ```
    plus the corresponding imports (`createAxis` is already imported; add
    `updateAxis`, `updateAxes2D`, `updateAxes3D`, `updateGrid`).

- [x] **5.6 — Extend `test_export_inplace_updaters.py`**
  - For each of `axis.js`, `axes2d.js`, `axes3d.js`, `grid.js`: assert the
    `export function update<Kind>` exists and its body calls the shared builder
    (`addAxis(`) or `setPositions(`.
  - `utils.js`: assert `"export function clearGroupChildren"` exists and the
    body of `entityRequiresRebuild` contains none of `'Axis'`, `'Axes2D'`,
    `'Axes3D'`, `'Grid'`.
  - `factory.js`: assert the four `case '…':` labels are present with the
    matching `update…(` call.
  - `generate_library_js()`: assert `function clearGroupChildren(`,
    `function updateAxis(`, `function updateAxes2D(`, `function updateAxes3D(`
    and `function updateGrid(` are all in the stripped bundle.

- [x] **5.7 — Harness label-DOM check (`anim-export-smoke.mjs`)**
  - Count the CSS2D label elements before playback with
    `document.querySelectorAll('div[style*="pointer-events: none"]').length`
    (every `CSS2DObject` wrapper and the label-renderer container carry that
    style; the container is a constant, so the count is stable) and again after
    the scrub pass.
  - Assert the count is **identical** and report it in the printed JSON — a
    rebuild-recreated label tree would show drift here even if the entity
    counters looked acceptable.

## Validation

```bash
uv run pytest py/tests/viz -q && (cd js/dev && npm run check && npm test)
node js/dev/tests/anim-export-smoke.mjs <url>
```

Smoke: the phase-1 scene has one changing `Axis`, one growing-count `Grid` and
one constant-count `Grid`; all three must land in `updated`, and the rebuild
budget (`removed` delta) must now be at its floor (≈ 0 for the whole run).
Also check the CSS2D DOM does not grow: the harness can report
`document.querySelectorAll('.tanga-label').length` (or the label wrapper count
under the figure container) before/after playback — it must stay constant.

## Notes

- Refilling an axis group recreates its label DOM nodes, which is unavoidable
  when tick values change.  What the phase removes is the *outer* entity churn:
  the wrapper node, registry entry, mesh-map entry, transform re-application and
  `removeEntityMesh` traversal of every CSS2D descendant.
- `styleNeedsRebuild` returns `true` for any style field other than
  `color`/`opacity`.  For axes that means `value_style` / `label_style` changes
  (fonts, offsets, alignment) rebuild — deliberate: those are create-time label
  inputs, and they do not change per frame in real animations.
- Grid material sharing is load-bearing: `applyStyleUpdate` must touch **one**
  material per grid, not one per segment.
- Ordering: `updateEntityMesh` dispatches before the generic
  `applyStyleUpdate`/`entityRequiresRebuild` fallback, so once the kinds are
  routed the blanket-`true` entries in `entityRequiresRebuild` are dead code —
  removing them is the regression guard (a forgotten route would otherwise
  silently keep rebuilding).

  - Keep the shared-material reuse: a grid of N segments must stay one
    material, otherwise a colour change would have to touch N materials.
