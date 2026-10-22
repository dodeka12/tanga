# Phase 1 — Entity data fields (`Rectangle2D.dir_u/dir_v`, `Ellipse.angle`)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`).  This phase only extends
> entity data classes; it introduces no new architecture.

## Goal

Add the plane-basis fields to `Rectangle2D` and the scalar `angle` field to
`Ellipse`, without changing any rendering/placement behaviour yet (defaults keep
current behaviour).  `Circle` is documented but not changed.

## Files

- Edit: `py/pytanga/geometry/entities/rectangle.py`
- Edit: `py/pytanga/geometry/entities/ellipsoid.py`
- Edit: `py/pytanga/geometry/entities/circle.py` (docstring only)
- Edit: `py/tests/viz/test_rectangle2d.py`
- Edit: `py/tests/geometry/test_conic_analysis.py` (add an `angle == 0` assertion)

## Steps

- [x] **1.1 — `Rectangle2D` `dir_u`/`dir_v` fields.**
  - Add `dir_u: Direction | None = None` and `dir_v: Direction | None = None`
    (mirror `Ellipse` in `ellipsoid.py`); coerce via `to_direction`.
  - Update the `__init__` signature + `object.__setattr__` calls and the class
    docstring: `dir_u`/`dir_v` are the in-plane basis; `angle` rotates from
    `dir_u` (default basis = `_plane_basis(normal)`).

- [x] **1.2 — `Ellipse` `angle` field.**
  - Add `angle: float = 0.0`; coerce via `to_float`; set via
    `object.__setattr__`; add to `__repr__`.
  - Update the docstring: `dir_u`/`dir_v` are the plane basis and the semi-axes
    are `R(normal, angle)·dir_u` / `·dir_v`; when `angle == 0` the basis *is* the
    semi-axes (backward compatible with `quadric/refine.py`).

- [x] **1.3 — `Circle` docstring.**
  - Note that `Circle` is the symmetric case (no `dir_u`/`dir_v`/`angle`).  No
    field change.

- [x] **1.4 — Tests.**
  - `test_rectangle2d.py`: `dir_u`/`dir_v` default `None`, coerce MVs/tuples,
    survive `Rectangle2D.between` (both sides `None`).
  - `test_conic_analysis.py`: assert `e.angle == 0.0` for the analyzed ellipse
    (conic path keeps `dir_u`/`dir_v` = principal directions).

## Validation

`uv run pytest py/tests/viz/test_rectangle2d.py py/tests/geometry/test_conic_analysis.py -q`

## Notes

- Entities stay dumb data classes (no `_plane_basis` import here — that lives in
  the viz layer).  Frame derivation is Phase 2's job.
- `dataclass(frozen=True)` equality/hash now include the new fields; the
  existing `between` equality test is unaffected (both sides default `None`).
