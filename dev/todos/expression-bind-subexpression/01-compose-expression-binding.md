# Phase 1 — Compose a variable onto a sub-expression

## Goal

Add the private `_expression_binding_tensors` helper and wire an `Expression`
branch into `Expression._evaluate`, delivering single-occurrence composition
(the motivating `bind(Omega_b=omega_local)` case).  The helper already carries
the general `k`-occurrence block expansion from the README §3; this phase
validates `k == 1` end-to-end.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- New: `py/tests/expression/test_bind_expression.py`

## Steps

- [x] **1.1 — Add `_expression_binding_tensors(inner, mask, labels, name)`**
  - Implement per README §2/§3: validate `inner.out_mask == mask` and
    `not inner._has_counting_axes()` (raise `ValueError` otherwise).
  - For each inner free variable `v` (`m_v = len(inner.names[v])`), allocate
    `block_v = allocate_block(m_v * len(labels))`.
  - Build one `MVLabeledTensor` per occurrence label `l_j`: a copy of
    `inner.tensor` whose axis 0 (`"k"`) is renamed to `l_j` (mode `"*"`) and
    whose free-variable axes are relabelled `block_v[j * m_v + occ]` (look up
    `(v, occ)` for each axis label via a `label -> (var, occ)` map built from
    `inner.names`).
  - Return `(tensors, free_names, free_masks)` where `free_names[v] = block_v`
    and `free_masks[v] = inner.masks[v]`.

- [x] **1.2 — Wire the `Expression` branch into `Expression._evaluate`**
  - In the variable-binding loop, before the `int/float`/`MV` handling, add:
    `if isinstance(value, Expression):` → call the helper, `labeled.extend(...)`,
    and merge `free_names`/`free_masks` into local `extra_names`/`extra_masks`
    accumulators (raising on a free name already in `extra_names`).
  - After `contract_labeled`, compute `remaining = set(self._names) - set(var_bindings)`;
    raise `ValueError` if `remaining` or `set(var_bindings)` intersects
    `extra_names`; then add `extra_names`/`extra_masks` to `new_names`/`new_masks`.
  - Keep the `MV`/`DataArray`/`int`/`float` paths unchanged; a constant inner
    expression (no free vars) still returns `MV` when nothing else remains.

- [x] **1.3 — Unit tests (single occurrence)**
  - Reproduce the feature-request shape with `BasisN3`: `wedge_expr = x_b ^
    (x_b | Omega_b)`; bind `Omega_b` to `omega_local = e1 * Omega * e1`; assert
    `result.names == {"x_b", "Omega"}`; then bind `x_b` and `Omega` to MVs and
    compare against the numerically-sandwiched reference.
  - Mask mismatch (`inner.out_mask != mask`) raises `ValueError`.
  - Binding to a constant expression equals binding to that `MV`.
  - Nested composition: `bind(...)` then `bind(...)` again on the result.

## Validation

`uv run pytest py/tests/expression/test_bind_expression.py -q`

## Notes

- Import `Expression` inside the loop guard is unnecessary — it is the same
  class; use a direct `isinstance(value, Expression)`.
- `AffineExpression` is not exercised here; it is covered in Phase 3.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
