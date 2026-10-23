# Planar-shape plane basis & labelme storage — Overview

**Created:** 2026-10-22 | **Status:** Done | **Branch:** `fix/rectangle2d`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` and
> `viz-controls-and-interactions.md`) for the subsystem(s) this work touches, so
> the new code aligns with the documented architecture.  If this work introduces
> or changes architecture, update the developer docs.

## Goal

Make every 2D annotation shape (`Rectangle2D`, `Ellipse`, `Circle`) carry
plane-independent intrinsic data (center, angle, axis lengths/radius) plus an
explicit plane placement, so a shape drawn on a tilted calibrated plane renders
with its body and handles in the same frame, and so labelme import/export is
exact on any 3D plane.  Resolves `_input/pytanga-issue-rectangle2d-tilted-plane.md`
(Finding 1: body/handle frame mismatch; Finding 2: labelme world-XY rectangle).

## Background / root cause

- **Finding 1** — the `Rectangle2D` body is placed by
  `_decompose._entity_decompose` with `quat_from_vectors((0,0,1), normal)`
  (`py/pytanga/viz/_decompose.py:236-241`); for a normal near `-z` this shortest-arc
  rotation is ~180° with its axis set by the tiny tilt components, so the body's
  in-plane roll is arbitrary.  The handles (`_active.py` `_corners`/`_dir_u`/
  `_dir_v`) use the deterministic `_plane_basis(normal)` (`ref = (0,1,0)`).  The two
  frames agree near `+z`, diverge arbitrarily near `-z`.
- **Finding 2** — `LabelMeStore` builds rectangles with `Rectangle2D.between`
  (world x/y size, default `normal=+z`) and exports corners along world x/y, so on
  a tilted plane the corners leave the plane and pixels do not round-trip.

`Ellipse` is shared with the GA conic path (`quadric/refine.py` emits
`dir_u`/`dir_v` = principal directions, `quadric/_intersection.py` consumes them
as semi-axes), which is why the `angle` reinterpretation below must stay
backward compatible (`angle == 0` ⇒ `dir_u`/`dir_v` *are* the semi-axes).

## Architecture (short)

- **Python entities** (`py/pytanga/geometry/entities/`) — `Rectangle2D` gains
  `dir_u`/`dir_v`; `Ellipse` gains `angle`.  `Circle` is unchanged (symmetric).
- **Decompose** (`py/pytanga/viz/_decompose.py`) — one deterministic in-plane
  frame for the planar entities via `_frame_quaternion(base, normal)` where
  `base = dir_u` if set else `_plane_basis_u0(normal)` (a numpy mirror of
  `_active._plane_basis`).  `angle` stays in the shape; renderers apply it with
  `rotateZ(angle)` in local space (local `+Z → normal`).
- **Frontend** (`py/pytanga/viz/templates/renderers/`) — `ellipse.js` gains
  `rotateZ(angle)` (rectangle already has it; circle is symmetric and unchanged).
- **Active** (`py/pytanga/viz/_active.py`) — `ActRectangle2D`/`ActEllipse` build
  their body with `dir_u=_u0, dir_v=_v0, angle=_angle` (no longer baking angle
  into `dir_u`).
- **Mapper** (`py/pytanga/viz/camera.py`) — `CoordinateMapper` gains
  `pixel_axes() -> (Direction, Direction)`, the unit world directions of pixel
  `+u`/`+v`, so `LabelMeStore` can build/export shapes in the mapper's plane.
- **LabelMe** (`py/pytanga/viz/labelme.py`) — rectangles built/exported in the
  mapper's pixel basis; ellipse stored in a new scalar form; circle keeps
  labelme's standard 2-point form but with exact on-plane math.

## Decisions (confirmed)

- `Rectangle2D` and `Ellipse` use the uniform "basis + scalar angle" model:
  `dir_u`/`dir_v` = plane basis, `angle` = in-plane rotation from `dir_u`.
- `Circle` is the symmetric case: no `dir_u`/`dir_v`/`angle` on the entity, and
  labelme keeps the standard `[center, rim]` 2-point circle (no format change).
- Ellipse labelme storage changes to our own canonical form
  (`points=[center]` + `radius_u`/`radius_v`/`angle`), with the legacy
  `[center, rim_u, rim_v]` form still accepted on load.
- `CoordinateMapper.pixel_axes()` is added to the protocol (architecture
  extension confirmed by the user); the architecture docs are updated to match.
- `_plane_basis` stays in `_active.py`; `_decompose.py` adds a numpy mirror
  `_plane_basis_u0(normal)` with a cross-referencing comment (avoids a
  module-import cycle; the decompose phase adds a parity test).

## Contract (fixed)

```python
# entities
Rectangle2D(center, size, normal=+z, angle=0.0, dir_u=None, dir_v=None)
Ellipse(center, radius_u, radius_v, normal=+z, dir_u=None, dir_v=None, angle=0.0)
Circle(center, radius, normal=+z, is_imaginary=False)   # unchanged

# _decompose.py — planar frame (Rectangle2D + Ellipse)
base = dir_u if dir_u is not None else _plane_basis_u0(normal)
q = _frame_quaternion(base, normal)
# Rectangle2D shape: {"size", "angle"}; Ellipse shape: {"radiusU","radiusV","angle"}

# _active.py — body carries the basis; handles use the same basis
_dir_u() = cos(angle)·u0 + sin(angle)·v0
_dir_v() = -sin(angle)·u0 + cos(angle)·v0

# camera.py — CoordinateMapper protocol
def pixel_axes(self) -> tuple[Direction, Direction]: ...   # (pixel +u, pixel +v) world dirs
# PlanarMapper         -> (Direction(1,0,0), Direction(0,1,0))
# CalibratedPlaneMapper -> (normalize(c2w @ [1,0,0]), normalize(c2w @ [0,1,0]))

# labelme ellipse — canonical (new) form
{ "label": "...", "points": [[cx, cy]], "shape_type": "ellipse",
  "radius_u": 10.0, "radius_v": 4.0, "angle": 0.78 }
# labelme circle — unchanged standard
{ "label": "...", "points": [[cx, cy], [rx, ry]], "shape_type": "circle" }
```

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-entity-fields.md](./01-entity-fields.md) | `Rectangle2D.dir_u/dir_v` + `Ellipse.angle` data fields |
| 2 | [02-decompose-plane-basis.md](./02-decompose-plane-basis.md) | `_plane_basis_u0` + stable frame for Rectangle2D/Ellipse |
| 3 | [03-renderers-angle.md](./03-renderers-angle.md) | `ellipse.js` applies `rotateZ(angle)` |
| 4 | [04-active-bodies.md](./04-active-bodies.md) | `ActRectangle2D`/`ActEllipse` bodies carry `dir_u`/`angle` |
| 5 | [05-mapper-pixel-axes.md](./05-mapper-pixel-axes.md) | `CoordinateMapper.pixel_axes()` + architecture docs |
| 6 | [06-labelme-plane-basis.md](./06-labelme-plane-basis.md) | plane-basis rectangles, new ellipse storage, circle radius/rim |
| 7 | [07-quadric-ellipse-angle.md](./07-quadric-ellipse-angle.md) | `_intersection.py` applies `Ellipse.angle` |
| 8 | [08-docs-changelog.md](./08-docs-changelog.md) | docs + examples + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` (fast, per phase)
- `uv run pytest py/tests/geometry -q` (entity/conic/quadric)
- `node js/dev/tests/check-syntax.mjs` (frontend templates, phase 3)
- `uv run ruff check .` + `uv run ty check` (lint/types, phase 8)
- `uv run mkdocs build --strict` (docs, phase 8)

## Non-goals

- `Plane` (without spans) keeps its `quat_from_vectors` frame — an infinite plane
  has no semantic in-plane orientation.  `RegularPolygon`, `Circle`, and `Disk`
  now use the same `_frame_quaternion(_plane_basis_u0(normal), normal)` helper.
- No `Plane` change (in-plane orientation of an infinite plane is not semantic).
- No wire/JSON *schema* change beyond the ellipse shape dict gaining `"angle"`
  and the ellipse labelme scalar keys; no new `DragMode`, no interaction model.
- `Rectangle2D.between` is left as the `+z`/2D convenience (labelme no longer
  uses it for tilted planes).
