# Phase 4 — Tolerant conic/quadric analysis via `Geometry`

## Goal

Make conic/quadric classification tolerance-aware and reachable through the `Geometry`
subsystem: `Geometry` gains a `tol`, threaded through `refine` into the classifiers, so a
noisy quadric can be classified "within a tolerance" (e.g. `cone` instead of `hyperboloid_1s`).

## Files

- Edit: `py/pytanga/quadric/conic.py` (tolerance-aware classifiers + `refine(tol=...)`)
- Edit: `py/pytanga/quadric/refine.py` (`refine_conic`/`refine_quadric` accept `tol`)
- Edit: `py/pytanga/geometry/refine.py` (`refine(entity, *, tol=None)`)
- Edit: `py/pytanga/geometry/_geometry.py` (`Geometry.tol` + threaded `refine`)
- New: `py/tests/quadric/test_tolerant_kind.py`, `py/tests/geometry/test_geometry_tol.py`

## Steps

- [x] **4.1 — tolerance-aware classifiers in `conic.py`**
  - Add `tol: float | None = None` (default `_TOL`) to `_rank`, `_inertia`,
    `_is_isotropic`, `_nonzero_evals`, `_classify_conic`, `_classify_quadric`; keep the
    cached `.kind`/`.rank`/`.signature` calling with the default so they are byte-identical.
- [x] **4.2 — `refine_conic`/`refine_quadric` accept `tol`**
  - Signature `refine_conic(conic, *, tol=None)` / `refine_quadric(quadric, *, tol=None)`;
    dispatch on `_classify_conic(conic.matrix, tol=...)` / `_classify_quadric(...)`
    (and thread `tol` into derived helpers that threshold, e.g. `rho`'s circle check).
- [x] **4.3 — `Conic.refine(tol=None)` / `Quadric3D.refine(tol=None)`**
  - Forward `tol` to `refine_conic`/`refine_quadric`.
- [x] **4.4 — `geometry/refine.py` + `Geometry`**
  - `refine(entity, *, tol=None)` calls `entity.refine(tol=tol)` when `tol` is given
    (else `entity.refine()`).
  - `Geometry.__init__(..., *, tol=None)` stores `self._tol` (add to `__slots__`);
    `Geometry.tol` getter/setter; `Geometry.refine(entity, *, tol=None)` uses
    `tol if tol is not None else self._tol`; `__call__`'s `Conic|Quadric3D` branch
    delegates to `self.refine(obj)`.
- [x] **4.5 — tests**
  - `test_tolerant_kind.py`: noise sweep (0 / 1e-6 / 1e-4 / 1e-3 / 1e-2) classifies as
    `cone` via `refine_quadric(quadric, tol=1e-4)` while the default `.kind` stays
    `hyperboloid_1s` for the noisy cases.
  - `test_geometry_tol.py`: `Geometry(BasisQ3(), tol=1e-4).refine(q) -> Cone`; a per-call
    `tol` override wins over `Geometry.tol`; setting `geo.tol` changes later results.

## Validation

`uv run pytest py/tests/quadric py/tests/geometry -q`

## Notes

- Default behavior is unchanged (all default tolerances remain `_TOL`).
- `which_entity`/`analyze` keep returning the raw `Conic`/`Quadric3D`; the tolerant
  classification is reached via `geo(raw)` / `geo.refine(raw)`.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
