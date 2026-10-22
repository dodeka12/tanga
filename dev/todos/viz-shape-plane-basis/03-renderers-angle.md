# Phase 3 — Ellipse renderer applies `rotateZ(angle)`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the per-entity renderer recipe).
>  This stays inside the existing renderer pattern; no architecture change.

## Goal

Make the ellipse renderer apply the in-plane `angle` (about the plane normal)
the same way `rectangle2d.js` already does.  This is what makes the
`_decompose` change from Phase 2 visually correct.

## Files

- Edit: `py/pytanga/viz/templates/renderers/ellipse.js`

## Steps

- [x] **3.1 — `rotateZ(angle)` in `createEllipse`.**
  - Read `const angle = ent.angle || 0.0;` near the top.
  - After building the outline (and fill), add `if (angle) { group.rotateZ(angle); }`
    — mirror `rectangle2d.js` `:45-47`.  The fill and outline are both children of
    `group`, so one rotation covers both.

- [x] **3.2 — `angle` in `updateEllipse`.**
  - Add `'angle'` to the `contentChanged(ent, prev, [...])` list (`:57`) so an
    angle change triggers a rebuild.

## Validation

`node js/dev/tests/check-syntax.mjs && uv run pytest py/tests/viz/test_entity_decompose.py -q`

## Notes

- `rectangle2d.js` already does this; `circle.js` is left unchanged (symmetric —
  a `rotateZ` would be a no-op).
- The real behaviour (ellipse rotates on a tilted plane) is exercised end-to-end
  by the tilted-plane labelme round-trip in Phase 6.
