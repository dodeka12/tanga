# Phase 0 — Shared `basis_for` dispatcher and test helper

## Goal

Generalize `basis_for(basis, typ)` from the single `TwistBivector` branch into a
full per-type dispatcher mirroring `create_operator`, and add a reusable test
helper that pins a mask's named basis.

## Files

- Edit: `py/pytanga/geometry/mask.py`
- Edit: `py/tests/geometry/test_geometry_mask.py`

## Steps

- [x] **0.1 — full `basis_for` dispatcher**
  - Rework `basis_for(basis, typ)` so it resolves the type key the same way
    `create_operator` does (`isinstance` branches over the operator/entity types)
    and delegates to the matching `create_*` module's `basis_for_<key>(basis)`
    via `getattr`/`hasattr`; return `None` when the module has no such function.
  - Keep the existing `TwistBivector` behaviour unchanged.

- [x] **0.2 — test helper**
  - Add a module-level helper in `test_geometry_mask.py`:
    `assert_mask_basis(alg, typ, expected_names)` that asserts
    `mask_for(alg, typ).basis_names == expected_names` (with a clear message
    including the type name).

## Validation

`uv run pytest py/tests/geometry/test_geometry_mask.py -q`

## Notes

- The dispatcher is the single registration point; each algebra phase only adds
  `basis_for_<type>` functions to its `create_*` module.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
