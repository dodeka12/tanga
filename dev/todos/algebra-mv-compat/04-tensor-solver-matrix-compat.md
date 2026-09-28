# Phase 4 — Relax `tensor` / `solver` / `matrix` algebra-identity checks

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Let the tensor, solver, and matrix layers treat equal-parameter algebras as
interchangeable.

## Files

- Edit: `py/pytanga/tensor/ops.py`
- Edit: `py/pytanga/tensor/product.py`
- Edit: `py/pytanga/tensor/_labeled.py`
- Edit: `py/pytanga/matrix/_product_data.py`
- Edit: `py/pytanga/solver/solve.py`
- New: `py/tests/tensor/test_tensor_compat.py`

## Steps

- [ ] **4.1 — `tensor/ops.py` l.39**
  - `return (mask_a.algebra is mask_b.algebra) and (mask_a.ids == mask_b.ids)`
    → `mask_a.algebra == mask_b.algebra`.

- [ ] **4.2 — `tensor/product.py`**
  - l.75 and l.134: `assert b_mask.algebra is a_mask.algebra, …` → `==`.
  - l.83 and l.142: `assert c_mask.algebra is alg` → `==`.

- [ ] **4.3 — `tensor/_labeled.py`**
  - l.360: `if s_mask.algebra is not v_mask.algebra:` → `!=`.
  - l.703: `if mask_a.algebra is not mask_b.algebra:` → `!=`.

- [ ] **4.4 — `matrix/_product_data.py` l.70**
  - `if self.b_mask.algebra is not self.c_mask.algebra:` → `!=`.

- [ ] **4.5 — `solver/solve.py` l.373 and l.375**
  - `if isinstance(a, MV) and a.algebra is not alg:` → `!=`.
  - `if isinstance(c, MV) and c.algebra is not alg:` → `!=`.

- [ ] **4.6 — Tests**
  - New `py/tests/tensor/test_tensor_compat.py` (annotate `-> None`): build
    tensor/`MVTensor`/labeled-tensor inputs from two equal-parameter algebra
    instances and confirm alignment succeeds without `ValueError`; a genuinely
    different algebra still raises.

## Validation

```
uv run pytest py/tests/tensor py/tests/solver py/tests/matrix -q
```

## Notes

- Keep the existing assert/raise mechanism at each site; only swap the
  operator.
- The solver guards (`solve.py`) are `raise ValueError`; the tensor/product
  guards are `assert` — do not change their kind.
