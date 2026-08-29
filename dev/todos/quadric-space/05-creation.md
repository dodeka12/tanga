# Phase 5 — Creation (entities → quadric-space MV)

## Goal

`create(basis, Conic/Quadric3D)` → MV (embed the symmetric matrix), and
`create(basis, specific entity)` → MV where applicable. Inverse of the analysis
round-trip.

## Files

- New: `py/pytanga/geometry/create_q2.py`
- New: `py/pytanga/geometry/create_q3.py`
- Modify: `py/pytanga/geometry/create.py` (dispatch + `create_entity` branches)
- New: `py/tests/geometry/test_conic_create.py`

## Steps

- [ ] **5.1 — `create_q2.py`**
  - `create_conic(basis, Conic)` → MV from `to_coeffs(coeffs)`.
  - `create_<entity>` for `Circle`, `Ellipse`, `Hyperbola`, `Parabola`, `Line`,
    `LinePair`, `ParallelLinePair` → their symmetric-matrix coeffs (via the
    inverse of the Phase-3 refinement formulas).

- [ ] **5.2 — `create_q3.py`**
  - `create_quadric(basis, Quadric3D)` → MV.
  - `create_<entity>` for `Sphere`, `Ellipsoid`, `Cylinder`, `Cone`, `Plane`.

- [ ] **5.3 — dispatch** — add q2/q3 to `create._detect`; route
  `Conic`/`Quadric3D` and the specific entities to the new modules.

- [ ] **5.4 — Tests**
  - `create(basis, analyze(mv)) == mv` (up to scale) for conic/quadric MVs.
  - `create(basis, Ellipsoid(...))` → MV that `analyze` → `Quadric3D` → `refine`
    → equivalent `Ellipsoid`.
  - `create` rejects unsupported entity kinds with a clear error.

- [ ] **5.5 — Validate** — `uv run pytest py/tests/geometry/test_conic_create.py -q`.

## Validation

`uv run pytest py/tests/geometry/test_conic_create.py -q`

## Notes

- Creation from specific entities is the inverse of `refine`; keep the two in
  lockstep (a shared `_coeffs_for(entity)` helper is acceptable).
