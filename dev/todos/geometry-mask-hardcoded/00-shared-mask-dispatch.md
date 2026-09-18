# Phase 0 — Shared hard-coded mask dispatch

## Goal

Rewrite `mask.py::mask_for` to dispatch to hard-coded `mask_for_<key>(basis)`
functions, and remove the instance-derived `_template` + `basis_for` machinery.

## Files

- Edit: `py/pytanga/geometry/mask.py`
- Edit: `py/tests/geometry/test_geometry_mask.py`

## Steps

- [x] **0.1 — dispatch rewrite**
  - `mask_for(basis, typ)`: if `typ` is a class → `_create_module(_detect(basis)).mask_for_<key>(basis)`
    (raise `TypeError` if the module lacks it); if `typ` is an instance →
    `BladeMask(_create(basis, typ))`.
  - Reuse `_create_module` / `_basis_type_key` from `geometry-mask-basis` Phase 0.

- [x] **0.2 — remove `_template` and `basis_for`**
  - Delete `_template`; delete the `basis_for` dispatcher (the named basis is now
    attached inside each `mask_for_<key>`).
  - Update `create_n3.basis_for_twist_bivector` → `mask_for_twist_bivector`
    (returns the full 9-blade mask with the 6-DOF basis via `with_basis`).

- [x] **0.3 — test helper**
  - Add `assert_type_mask(alg, typ, expected_ids, expected_names)` and keep
    `assert_mask_basis`; update the existing `mask_for`-based tests that relied on
    `_template`.

## Validation

`uv run pytest py/tests/geometry/test_geometry_mask.py -q`

## Notes

- `_template` is the root cause of the partial-mask bug — removing it is the point
  of this whole plan.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
