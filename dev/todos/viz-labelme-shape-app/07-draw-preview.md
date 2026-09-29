# Phase 7 — `ShapeFromPoints` protocol + `DragPreview`

## Goal

Define the `ShapeFromPoints` protocol that the composite `create_from_points`
classmethods implement, and a generic `DragPreview` helper that drives the
transient-entity lifecycle for any factory supporting the protocol.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  Reuses the existing scene-handle add/update/remove
> API and the `Act*` composites; no architecture change.

## Files

- New: `py/pytanga/viz/_draw_preview.py` (protocol + `DragPreview`)
- Edit: `py/pytanga/viz/__init__.py` (export `ShapeFromPoints`, `DragPreview`)
- New: `py/tests/viz/test_draw_preview.py`

## Steps

- [x] **7.1 — `ShapeFromPoints` protocol**
  - A `typing.Protocol` with `@classmethod create_from_points(cls, a, b,
    **kwargs) -> ActSceneObject`; document the per-shape interpretation (corners
    / center+rim / endpoints).
- [x] **7.2 — `DragPreview` helper**
  - `DragPreview(handle, *, factory: type[ShapeFromPoints], style=None)` owns the
    anchor, the transient preview entity id, and:
    - `begin(anchor)` — record the anchor;
    - `update(pos)` — add/update `factory.create_from_points(anchor, pos).entity`
      as a transient entity on `handle`;
    - `finalize(pos)` — discard the preview and return
      `factory.create_from_points(anchor, pos)` (the composite to add);
    - `discard()` — remove the transient entity.
- [x] **7.3 — Export + tests**
  - Export both names; test `begin`/`update`/`finalize`/`discard` against a fake
    `VizSceneHandle` (or a real scene), and that the transient entity is
    removed on `finalize`.

## Validation

```
uv run pytest py/tests/viz -q
```

## Notes

- The protocol is a type-only contract; the `create_from_points` classmethods
  already exist on the composites (phases 3–6).  `DragPreview` derives the
  preview entity from `create_from_points(…).entity` so preview and finalized
  shape always agree on clamps/defaults.
- `style` is a `DragPreview`/`add` concern, not part of the protocol.
