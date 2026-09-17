# Phase 5 — `TwistBivector` geometry entity

## Goal

Add a `TwistBivector` operator to the geometry submodule: a N3-only, grade-2
twist bivector derived from a rotor + translator via a motor, with working
`create_var()` / `mask_for()` support and no visualization.

## Files

- Edit: `py/pytanga/geometry/operators.py`
- Edit: `py/pytanga/geometry/create_n3.py`
- Edit: `py/pytanga/geometry/create.py`
- Edit: `py/pytanga/geometry/mask.py`
- Edit: `py/pytanga/geometry/__init__.py`
- Edit: `py/tests/geometry/test_operators.py`
- Edit: `py/tests/geometry/test_geometry_n3.py`
- Edit: `py/tests/geometry/test_geometry_mask.py`

## Steps

- [x] **5.1 — `TwistBivector` dataclass**
  - Add `TwistBivector(rotor: Rotor, translator: Translator)` in
    `operators.py`, mirroring `Motor`'s constructor shape; add it to the
    `Operator` union.

- [x] **5.2 — `create_twist_bivector`**
  - In `create_n3.py`, add `create_twist_bivector(basis, rotor, translator) -> MV`
    that:
    1. builds `motor = create_motor(basis, rotor, translator)`;
    2. computes the twist mask as
       `mask_for(basis, Motor).intersection(BladeMask(basis, grades=[2]))`
       (deferred `from .mask import mask_for` inside the function to avoid a
       circular import);
    3. returns `motor.project_onto(twist_mask)`.

- [x] **5.3 — Dispatch + N3 guard**
  - In `create_operator` (`create.py`), add a `TwistBivector` branch that raises
    `TypeError` unless `_detect(basis) == "n3"`, then delegates to
    `mod.create_twist_bivector(basis, operator.rotor, operator.translator)`.

- [x] **5.4 — `_template` + exports**
  - Add a `TwistBivector` branch to `_template` in `mask.py`
    (`TwistBivector(Rotor(0.7, Direction(1, 2, 3)), Translator(Direction(4, 5, 6)))`).
  - Import `TwistBivector` and add it to `__all__` in `geometry/__init__.py`.

- [x] **5.5 — Tests**
  - `test_operators.py`: constructor + `repr`.
  - `test_geometry_n3.py`: `create(alg, TwistBivector(...))` equals
    `create_motor(...).project_onto(twist_mask)`; non-N3 bases raise.
  - `test_geometry_mask.py`: `mask_for(alg, TwistBivector)` equals
    `mask_for(alg, Motor).intersection(BladeMask(alg, grades=[2]))` (ids
    `[3, 5, 6, 9, 10, 12, 17, 18, 20]`); `create_var` returns a variable with
    that mask.

## Validation

`uv run pytest py/tests/geometry/test_operators.py py/tests/geometry/test_geometry_n3.py py/tests/geometry/test_geometry_mask.py -q`

## Notes

- "create_mask" in the request maps to `mask_for` (module-level and
  `Geometry.mask_for`); there is no `create_mask` function.
- The twist mask is the 9 grade-2 blades of a motor (rotation + translation
  bivectors), excluding the `e∞∧e₀` (E) dilator bivector — verified ids
  `[3, 5, 6, 9, 10, 12, 17, 18, 20]`.
- No analysis or viz handler is added — a TwistBivector MV is intentionally not
  visualizable / not analyzable.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
