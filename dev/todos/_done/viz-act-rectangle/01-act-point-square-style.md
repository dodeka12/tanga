# Phase 1 — `SquarePointStyle` (square `ActPoint` marker)

## Goal

Add a `PointStyle` variant that renders a `Point` as a small flat square marker,
so `ActPoint` handles can be drawn as squares.  Follows the existing
`CrossHairPointStyle` pattern (a style discriminator + a dedicated renderer
dispatched in `factory.js`).

## Files

- Edit: `py/pytanga/viz/_styles/_entity_styles.py` (add `SquarePointStyle`)
- New: `py/pytanga/viz/templates/renderers/square_point.js`
- Edit: `py/pytanga/viz/templates/renderers/factory.js` (dispatch + update)
- Edit: `py/pytanga/viz/__init__.py` (export `SquarePointStyle`)
- New: `py/tests/viz/test_square_point_style.py`

## Steps

- [x] **1.1 — `SquarePointStyle(PointStyle)` dataclass**
  - Fields: `color`, `opacity`, `size` (half-extent, world units), `thickness`
    (slab depth).  `to_dict()` emits `style_type: "SquarePointStyle"` + non-None
    fields (mirror `PointStyle.to_dict`).

- [x] **1.2 — `square_point.js` renderer**
  - A thin square slab facing `+z` (`THREE.BoxGeometry(size*2, size*2, thickness)`
    or a double-sided `PlaneGeometry`), positioned at `ent.position`, tagged via
    `tagEntity(mesh, ent)`.  Reuse `makeMaterial`/`styleParam`/`parseColor` from
    `utils.js`.  Keep it visible in a 2D top-down view and on the xy-plane in 3D.

- [x] **1.3 — factory dispatch**
  - In `factory.js::createEntityMesh` `case 'Point'`/`'HPoint'`, add
    `ent.style?.style_type === 'SquarePointStyle'` → `createSquarePoint(ent)`
    (next to the `CrossHairPointStyle` branch).  No custom `update` needed unless
    geometry depends on style fields that change live (then add
    `updateSquarePoint` and the `updateEntityMesh` case).

- [x] **1.4 — export + tests**
  - Re-export `SquarePointStyle` from `pytanga.viz`.
  - Test: `SquarePointStyle().to_dict()` → `{"style_type": "SquarePointStyle"}`;
    round-trip through a `Point` entity serialize.

## Validation

`uv run pytest py/tests/viz/test_square_point_style.py -q && uv run python tools/build-viewer-js.py && node --check py/pytanga/viz/templates/renderers/square_point.js`

## Notes

- Do not add a new `kind`; this is a style variant on the existing `Point` kind,
  dispatched by `style_type`, exactly like `CrossHairPointStyle`.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
