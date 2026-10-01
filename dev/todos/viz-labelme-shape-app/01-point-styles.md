# Phase 1 — Circle + icon point styles

## Goal

Add two `PointStyle` variants — `CirclePointStyle` (outline/filled disc) and
`IconPointStyle` (a `material:*` glyph marker) — with renderers and `factory.js`
dispatch, so later phases can use them as composite handles.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`) for the style/renderer extension recipe, so the new
> code aligns with the documented architecture.  No architecture change is
> expected; this follows the existing `SquarePointStyle` recipe.

## Files

- Edit: `py/pytanga/viz/_styles/_operator_styles.py` (two new dataclasses)
- New: `py/pytanga/viz/templates/renderers/circle_point.js`
- New: `py/pytanga/viz/templates/renderers/icon_point.js`
- Edit: `py/pytanga/viz/templates/renderers/factory.js` (dispatch + applyStyleUpdate)
- Edit: `py/pytanga/viz/_styles/__init__.py`, `py/pytanga/viz/__init__.py` (exports)
- New: `py/tests/viz/test_circle_icon_point_style.py`

## Steps

- [x] **1.1 — `CirclePointStyle(PointStyle)` dataclass**
  - Fields: `thickness: float | None`, `filled: bool | None`, `fill_opacity: float | None`
    (inherits `color`/`opacity`/`size`; `size` is the circle radius).
  - `to_dict()` emits `style_type: "CirclePointStyle"` + non-None fields.
- [x] **1.2 — `IconPointStyle(PointStyle)` dataclass**
  - Field: `icon: Icon | None` (any `material:*` glyph).  `to_dict()` emits
    `style_type: "IconPointStyle"` + `icon` + non-None `PointStyle` fields.
- [x] **1.3 — `circle_point.js` renderer**
  - `createCirclePoint(ent)` → a flat disc (filled `CircleGeometry`) and/or an
    outline ring (`RingGeometry`), sized by `ent.style.size`, slab depth by
    `thickness`, tagged with `tagEntity`.  Return a `Group` when both fill and
    ring are present; tag the fill disc `isFillQuad` so `applyStyleUpdate` applies
    `fill_opacity` to it (mirror `ellipse.js`).
- [x] **1.4 — `icon_point.js` renderer**
  - `createIconPoint(ent)` → a flat plane with a canvas-textured glyph drawn in
    the loaded Material Symbols font (canvas → `THREE.CanvasTexture`), sized by
    `ent.style.size`; tag with `tagEntity`.  Fall back to a small square if the
    font is unavailable.
- [x] **1.5 — `factory.js` dispatch**
  - In the `'Point'`/`'HPoint'` case, add branches for
    `style_type === 'CirclePointStyle'` → `createCirclePoint` and
    `'IconPointStyle'` → `createIconPoint`, next to `CrossHairPointStyle` /
    `SquarePointStyle`.  Add `applyStyleUpdate` support for the live-updatable
    fields (`color`, `opacity`, `size`, `filled`, `fill_opacity`).
- [x] **1.6 — Exports**
  - Re-export both styles from `pytanga.viz` and `pytanga.viz._styles`
    (mirror `SquarePointStyle`).
- [x] **1.7 — Tests**
  - `CirclePointStyle().to_dict()` / `IconPointStyle().to_dict()` defaults; a
    full round-trip through a `Point` entity serialize (mirror
    `test_square_point_style.py`).

## Validation

```
uv run pytest py/tests/viz -q
node --check py/pytanga/viz/templates/renderers/circle_point.js
node --check py/pytanga/viz/templates/renderers/icon_point.js
uv run python tools/build-viewer-js.py --check
```

## Notes

- The Material Symbols font is already loaded by the viewer; the icon renderer
  reuses it (draw text to a canvas, use as a texture).  Keep `size` in **world
  units** so handles stay screen-constant via the same sizing path as other
  point renderers (check `square_point.js` for the world↔screen scale handling).
