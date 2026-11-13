# Phase 4 — Frontend colored path

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Render per-segment colors in the `PointPath` fat-line renderer and keep
in-place updates correct when only the uniform fallback color changes.

## Files

- New: `py/pytanga/viz/templates/renderers/path-colors.js`
- Edit: `py/pytanga/viz/templates/renderers/point_path.js`
- Edit: `py/pytanga/viz/templates/renderers/utils.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`
- Edit: `py/pytanga/viz/export/_bootstrap/_html.py` (`_RENDERER_FILES`)
- New: `js/dev/tests/path-colors.test.mjs`
- Generated: `js/tanga-viewer.js`, `js/tanga-viewer.manifest.json`

## Steps

- [x] **4.1 — Pure color-decision module**
  - Create `path-colors.js` with no `three` import:
    - `hasExplicitPathColors(ent)` — true when any entry of `ent.colors` or
      `ent.segmentColors` is non-null;
    - `pathColorChangeNeedsColorUpdate(ent, prev)` — true when both entities
      have explicit path colors and `ent.style.color` differs from
      `prev.style.color`, or when the `colors`/`segmentColors` arrays differ
      while both stay colored.
  - Keep the helpers pure so `js/dev/tests/path-colors.test.mjs` can import
    them without a browser or WebGL.

- [x] **4.2 — `point_path.js`**
  - Import `hasExplicitPathColors` from `./path-colors.js`; make
    `hasVertexColors(ent)` delegate to it.
  - Extend `flattenPath(points, perPointColors, uniformColor,
    segmentColors = [])`:
    - `hasAnyVertexColor = hasExplicitPathColors({colors: perPointColors,
      segmentColors})`;
    - for segment `i`, if `segmentColors[i]` is non-null use it for both
      endpoints; otherwise use `perPointColors[i]` / `perPointColors[i + 1]`
      with the uniform fallback;
    - return `{positions, vertexColors}`.
  - `createPointPath` passes `ent.segmentColors || []`.
  - `updatePointPath` uses `hasExplicitPathColors` for the colored/uniform
    switch and passes `ent.segmentColors || []`.  When colored, call
    `setColors` + `applyOpacityUpdate` only; when uniform, call
    `applyStyleUpdate`.

- [x] **4.3 — Do not tint explicit vertex colors**
  - In `applyStyleUpdate` (`utils.js`), skip
    `child.material.color.copy(c)` when `child.material.vertexColors` is true.
  - Keep opacity and scale updates unchanged.

- [x] **4.4 — Route colored-path base-color changes**
  - Import `pathColorChangeNeedsColorUpdate` in `views/three-view.js`.
  - In the `style`-aspect update, before `entityRequiresRebuild`, if
    `pathColorChangeNeedsColorUpdate(merged, prev)` is true, call
    `_updateEntityContent(id, merged)` and return.  This reaches
    `updateEntityMesh` → `updatePointPath`, which recomputes the fallback
    colors and writes the color attribute in place.
  - Otherwise keep the existing rebuild/`applyStyleUpdate` path.

- [x] **4.5 — Bundle registration**
  - Add `_RENDERERS_DIR / "path-colors.js"` to `_RENDERER_FILES` before
    `point_path.js`.
  - Run `uv run python tools/build-viewer-js.py`; commit the regenerated
    `js/tanga-viewer.js` and `js/tanga-viewer.manifest.json`.
  - Run `uv run python tools/build-viewer-js.py --check`.

- [x] **4.6 — JS tests**
  - `path-colors.test.mjs`:
    - `hasExplicitPathColors` with all-null, per-point colors, and segment
      colors;
    - `pathColorChangeNeedsColorUpdate` with a changed base color, unchanged
      color, uniform path, and changed `colors`/`segmentColors` arrays.
  - Run `npm --prefix js/dev test` and `npm --prefix js/dev run check`.

## Validation

`npm --prefix js/dev test && npm --prefix js/dev run check && uv run pytest py/tests/viz/test_export_renderers.py -q && uv run python tools/build-viewer-js.py --check`

## Notes

- `path-colors.js` is imported by both the live viewer and the export bundle,
  so it must be in `_RENDERER_FILES`.
- `three-view.js` is live-view only; it is not part of `_RENDERER_FILES`.
- Keep the wire key camelCase (`segmentColors`); Python emits it.
- No new interaction/event wiring is needed: vertex clicks already use the
  existing `on_click` path.
