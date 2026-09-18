# Phase 3 — Per-algebra `basis_for` and `mask_for` type-specific bases

## Goal

Add a per-algebra `basis_for(basis, typ)` hook (mirroring `create_operator`) and
have `mask.py::mask_for` attach a type-specific named basis via `with_basis`.
`basis_for_twist_bivector` (N3) returns the 6 physical DOF directions
(`e12, e13, e23, e1∧e∞, e2∧e∞, e3∧e∞`) over the 9 raw twist blades.

## Files

- Edit: `py/pytanga/geometry/create_n3.py`
- New: `py/pytanga/geometry/basis.py` (dispatcher) — or add the dispatcher in `mask.py`
- Edit: `py/pytanga/geometry/mask.py`
- Edit: `py/tests/geometry/test_geometry_mask.py`

## Steps

- [x] **3.1 — `basis_for` dispatcher**
  - Add `basis_for(basis, typ) -> list[tuple[str, MV]] | None` mirroring
    `create_operator`'s `isinstance` branches; default `None` ("no type-specific
    basis, keep the auto display basis").  Use lazy imports to respect the
    `docs/dev/architecture/geometry-module-layering.md` import DAG.

- [x] **3.2 — `basis_for_twist_bivector` (N3)**
  - In `create_n3.py`, add a helper returning the 6 named directions built from
    `basis.e1/e2/e3/einf` via `op`:
    `e12, e13, e23, e1∧e∞, e2∧e∞, e3∧e∞` (names `"e12","e13","e23","e1∧einf","e2∧einf","e3∧einf"`).
  - Guard for `_detect(basis) != "n3"` → `None` (or raise, mirroring
    `create_operator`).

- [x] **3.3 — `mask_for` attaches the type-specific basis**
  - In `mask.py::mask_for`, after `mv = _create(basis, inst)`: call
    `basis_for(basis, typ)`; if non-`None`, return `BladeMask(mv).with_basis(...)`,
    else `BladeMask(mv)`.
  - `Geometry.mask_for` (facade) already delegates to this, so it inherits the
    behavior.

- [x] **3.4 — tests**
  - `mask_for(N3, TwistBivector).ids == [3, 5, 6, 9, 10, 12, 17, 18, 20]`.
  - `mask_for(N3, TwistBivector).basis_names == ["e12","e13","e23","e1∧einf","e2∧einf","e3∧einf"]`
    and `len(mask.basis) == 6`.
  - `mask_for(N3, TwistBivector).basis_matrix().shape == (9, 6)`.
  - Other algebras (`mask_for(E3, TwistBivector)`) still raise `TypeError`.

## Validation

`uv run pytest py/tests/geometry/test_geometry_mask.py py/tests/geometry/test_operators.py py/tests/geometry/test_geometry_n3.py -q`

## Notes

- `mask_for(Motor)` / `mask_for(Point)` etc. keep the auto display basis (no
  type-specific hook) — only `TwistBivector` overrides for now.
- The existing `create_twist_bivector` (MV creation) is unchanged; only the mask
  gains the named basis.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
