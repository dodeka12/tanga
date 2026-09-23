# Phase 2 — `Conic` / `Quadric3D` matrix constructor + `to_matrix()`

## Goal

Let `Conic` / `Quadric3D` be built from a symmetric matrix (not only the coefficient
vector) and expose `to_matrix()` so they satisfy `MatrixProvider`.

## Files

- Edit: `py/pytanga/quadric/conic.py`
- Edit: `py/tests/quadric/test_core.py` (or a new `test_matrix_ctor.py`)

## Steps

- [x] **2.1 — matrix-accepting constructor**
  - `Conic.__init__(data)` / `Quadric3D.__init__(data)`: `arr = np.asarray(data,
    float)`; 1-D of length 6/10 → coefficient vector; 2-D of shape `(3,3)`/`(4,4)`
    → `to_coeffs(arr)`; otherwise raise `ValueError`.
  - `np.asarray` covers `tuple`, `np.ndarray`, nested lists, and
    `pytanga.geometry.Matrix` (it implements `__array__`) — no `geometry` import,
    no cycle.

- [x] **2.2 — `to_matrix()`**
  - Add `def to_matrix(self) -> np.ndarray: return self.matrix` to both dataclasses
    (this satisfies the `@runtime_checkable MatrixProvider` protocol).

- [x] **2.3 — tests**
  - Coefficient-vector construction still works; a 3×3/4×4 `np.ndarray` and a
    `pytanga.geometry.Matrix` produce the same `.coeffs` / `.kind`; `to_matrix()`
    round-trips through `to_coeffs`; wrong shapes/lengths raise.

## Validation

`uv run pytest py/tests/quadric -q`

## Notes

- Import `to_coeffs` in `conic.py` (currently only `from_coeffs`). Phase 3 renames
  both to `_to_coeffs` / `_from_coeffs`; update the import there.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
> touches, so the new code aligns with the documented architecture. If this work
> introduces or changes architecture, update the developer docs.
