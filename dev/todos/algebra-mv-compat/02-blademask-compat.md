# Phase 2 — Relax `BladeMask` algebra-identity checks

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Let `BladeMask` operations (union, intersection, `from_array`, blade diff, and
`__eq__`) treat equal-parameter algebras as the same algebra, using the `==`
from Phase 1.

## Files

- Edit: `py/pytanga/blade_mask/_mask.py`
- Edit: `py/pytanga/blade_mask/predict.py`
- New: `py/tests/blade_mask/test_blade_mask_compat.py`

## Steps

- [ ] **2.1 — `_mask.py` checks**
  - `from_array` (l.185): `elif mv.algebra is not alg:` → `elif mv.algebra !=
    alg:`.
  - blade-diff guard (l.270): `assert mv.algebra is self._alg, …` → `==`.
  - `union` (l.352): `assert other._alg is self._alg, …` → `==`.
  - `intersection` (l.380): `assert other._alg is self._alg, …` → `==`.
  - `__eq__` (l.417): `self._alg is other._alg and self._ids == other._ids` →
    `self._alg == other._alg and self._ids == other._ids`.

- [ ] **2.2 — `predict.py` checks**
  - l.43: `assert c_mask.algebra is a_mask.algebra, …` → `==`.
  - l.114: `assert b_mask.algebra is a_mask.algebra, …` → `==`.

- [ ] **2.3 — Tests**
  - New `py/tests/blade_mask/test_blade_mask_compat.py` (annotate `-> None`):
    - Union/intersection of a `BladeMask(a_basis)` with a mask built from a
      second, equal-parameter basis instance no longer raises and returns the
      expected ids.
    - `BladeMask.from_array([a_mv, b_mv])` across two equal-parameter instances
      succeeds.
    - `mask_from_a == mask_from_b` when the ids are equal and the algebras are
      equal-parameter (but distinct instances).
    - Genuinely different algebras (e.g. N3 vs E3) still raise as before.

## Validation

```
uv run pytest py/tests/blade_mask -q
```

## Notes

- The `assert`s stay `assert` (they are stripped under `python -O`); only the
  operator changes.
- `BladeMask` remains unhashable (no `__hash__` added in this work).
