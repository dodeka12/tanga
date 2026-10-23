# Interactive shapes use the plane's pixel basis — Overview

**Created:** 2026-10-23 | **Status:** Done | **Branch:** `fix/act-rect-ellipse`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`) for the subsystem(s) this work touches, so the new
> code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Finish what the `fix/rectangle2d` branch started and `_input/pytanga-plan-act-pixel-basis.md`
specifies: give the interactive `Act*` classes the same in-plane basis as their
backing entity, make labelme export consistent with the entity's frame, and give
consumers one correct way to wrap an entity in an Act — so a shape loaded, drawn,
or edited through an `Act*` exports back to the same pixels.

## Background / root cause

`LabelMeStore` builds entities in the mapper's pixel frame (`dir_u = pixel_u`),
but `ActRectangle2D`/`ActEllipse`/`ActCircle` only accept `normal` and build their
frame via `_plane_basis(normal)`.  For a real camera the two frames differ by the
camera roll, so `load → Act → save` shifts pixels.  Labelme ellipse export also
writes `angle = ellipse.angle` (only correct when `ellipse.dir_u` is the pixel
axis), and consumers re-implement "entity → Act" and get the angle wrong.

## Architecture (short)

- `Act*` composites gain an optional in-plane basis (`dir_u`/`dir_v`), defaulting
  to `_plane_basis(normal)`; the body + handles + rotate handle already derive
  from `_u0`/`_v0`, now fed by `_resolve_basis`.
- `LabelMeStore` export derives axes from the entity's `dir_u`/`dir_v` (rotated by
  `angle`) and writes the ellipse `angle` in the documented pixel frame.
- `from_entity` classmethods and `axis_directions()` entity methods become the
  single source of truth for "entity → Act" and "effective axes".

## Decisions (confirmed)

- `dir_u`/`dir_v` on the `Act*` classes are the plane basis; `angle` stays
  "rotation about the normal, measured from `dir_u`".
- Basis validation: `dir_u`/`dir_v` must be orthonormal and right-handed
  (`du × dv == normal`); raise `ValueError` otherwise.
- `from_entity` copies centre/size/radii/normal/`dir_u`/`dir_v`/`angle` verbatim.
- `LabelMeStore.to_act` is an optional convenience; the store stays data-only for
  its load/save API.  The required path is `Act*.from_entity`.
- `axis_directions()` returns `dir_u`/`dir_v` rotated by `angle` about `normal`,
  or `None` when the entity has no explicit basis (the viz layer falls back to
  `_plane_basis(normal)` so `geometry` stays self-contained).

## Contract (fixed)

```python
# Act* basis (Phase 1)
ActRectangle2D(..., normal=None, dir_u=None, dir_v=None)
ActEllipse(..., normal=None, dir_u=None, dir_v=None)
ActCircle(..., normal=None, dir_u=None, dir_v=None)   # basis orients the radius handle
# .dir_u / .dir_v read-only properties (normalized); du × dv == normal (validated)

# entity → Act (Phase 3)
ActRectangle2D.from_entity(rect, **kwargs) -> ActRectangle2D
ActEllipse.from_entity(ellipse, **kwargs) -> ActEllipse
ActCircle.from_entity(circle, **kwargs) -> ActCircle

# effective axes (Phase 4)
Rectangle2D.axis_directions() -> (Direction, Direction) | None
Ellipse.axis_directions() -> (Direction, Direction) | None

# labelme ellipse angle (Phase 2)
angle_px = ellipse.angle + signed_angle(pixel_u -> ellipse.dir_u)   # about normal
```

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-act-basis.md](./01-act-basis.md) | `Act*` in-plane basis (`dir_u`/`dir_v`, validation, properties) |
| 2 | [02-export-frame.md](./02-export-frame.md) | labelme export consistent with the entity's frame |
| 3 | [03-from-entity.md](./03-from-entity.md) | `from_entity` (+ optional `to_act`) + example apps |
| 4 | [04-axis-directions.md](./04-axis-directions.md) | `axis_directions()` entity helpers |
| 5 | [05-tests.md](./05-tests.md) | roll + tilted-normal round-trip tests |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q`
- `uv run pytest py/tests/geometry -q`
- `uv run ruff check .` + `uv run ty check`
- `uv run mkdocs build --strict` (phase 6)

## Non-goals

- No new `DragMode`, interaction model, or wire/schema change.
- No change to `CoordinateMapper` (already extended in `fix/rectangle2d`).
- `LabelMeStore.to_act` is optional and must not change the store's data-only
  load/save contract.
- No change to the consumer repo's `_act_from_entity`/`ellipse_cone.py` here —
  that is tracked in the report's "after the release" section.
