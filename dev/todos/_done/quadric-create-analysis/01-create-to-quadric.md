# Phase 1 — Move Q2/Q3 creation into quadric

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md`) for the subsystem(s) this work touches, so the
> new code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Move the Q2/Q3 entity→MV creation out of `geometry/create_q2.py` and
`geometry/create_q3.py` into a single `quadric/_create.py`; turn the geometry
modules into thin re-export shims.

## Files

- New: `py/pytanga/quadric/_create.py`
- Edit: `py/pytanga/quadric/__init__.py`
- Replace (shim): `py/pytanga/geometry/create_q2.py`, `py/pytanga/geometry/create_q3.py`

## Steps

- [x] **1.1 — Create `quadric/_create.py`**
  - Concatenate the logic from `create_q2.py` and `create_q3.py`.
  - `create_entity(basis, entity)`, `create_point(basis, x, y, z)`, and
    `create_rotor(basis, angle, axis)` dispatch on `basis.dim` (6 → Q2, 10 → Q3).
  - Imports: `Conic`/`Quadric3D` from `.conic`; `embed_point`/`to_coeffs` from
    `._embedding`/`._mapping`; the specific entities (Circle, Ellipse, Hyperbola,
    Parabola, Line, LinePair, ParallelLinePair, Sphere, Ellipsoid, Cylinder, Cone,
    Plane) via a lazy `_entities()` helper (mirror `quadric/refine.py`).
  - Move the Perwass rotor (currently in `geometry/create_q2.py`) here.
- [x] **1.2 — Shim `geometry/create_q2.py` and `geometry/create_q3.py`**
  - Replace each body with re-exports from `pytanga.quadric._create` (Q2 subset in
    `create_q2.py`, Q3 subset in `create_q3.py`).
  - `create_entity`/`create_point`/`create_rotor` in each shim delegate to the same
    dim-dispatching `quadric._create` functions (the dispatcher always passes the
    matching basis).
- [x] **1.3 — Export from `quadric/__init__.py`**
  - Import the create functions from `._create` and add them to `__all__`.
- [x] **1.4 — Tests**
  - Add a smoke test that `pytanga.quadric._create.create_rotor(...)` returns the
    rotor (grades {0, 2, 4}, normalized) and that `create_entity` round-trips for a
    representative Q2 and Q3 entity.
  - Existing `test_conic_create.py` / `test_conic_analysis.py` must stay green.

## Validation

`uv run pytest py/tests/geometry -q`

## Notes

- `geometry/create.py` already lists `create_q2`/`create_q3` in both the entity and
  operator `modules` dicts (from the earlier rotor work), so no dispatcher edit is
  needed here — only the shims.
- No behavior change: the moved functions keep identical bodies; only the import
  paths change.
