# Phase 1 — `Expression._substitute` + `Expression.rename_var`

## Goal

Add the private relabel helper `Expression._substitute(mapping)` and the public
name-only `Expression.rename_var(old, new_name)` — the two primitives the later
phases build on.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- New: `py/tests/expression/test_rename.py`

## Steps

- [x] **1.1 — Add `Expression._substitute(mapping)`**
  - Implement the relabel per the README contract: skip absent names; validate
    `mapping[n].mask == self._masks[n]`; group sources by `id(target)`; assign
    block slots (with merge support); rebuild `_tensor.labels`, `_names`,
    `_masks`.
  - Raise `ValueError` on mask mismatch and when a target would exceed
    `len(target.labels)`.
  - Build the new tensor with `MVLabeledTensor(self._tensor.tensor, new_labels)`;
    leave the output axis `"k"` and any `None`-mask counting axes unchanged.

- [x] **1.2 — Add `Expression.rename_var(old, new_name)`**
  - Resolve `old` (`str` or `Variable`) to a name; require it to be present;
    require `new_name` not to collide with a different existing name.
  - Return `Expression(self._tensor, new_names, new_masks)` with only the name
    key changed (labels/masks/tensor reused as-is).

- [x] **1.3 — Unit tests**
  - Two `Variable("X")` instances: `e1 = X1*a`, `e2 = X2*b`; after
    `e1._substitute({"X": X})` and `e2._substitute({"X": X})` their sum is a
    single merged `Expression` and evaluates to `x*a + x*b`.
  - `_substitute` rename `{"X": Variable("Y", mask)}` → `names == {"Y"}`.
  - Merge: an expression with `a` and `b` (same mask) →
    `_substitute({"a": X, "b": X})` yields one variable `X` with two occurrences.
  - Mask mismatch → `ValueError`; `rename_var` on an unknown name → `ValueError`;
    `rename_var` is name-only (the renamed expression still merges with the
    original).

## Validation

`uv run pytest py/tests/expression/test_rename.py -q`

## Notes

- `_substitute` is lenient (skips absent names) by design; `rename_var` is
  strict.  `bind`/`unify` layer their own strictness in later phases.
- Keep the helper private (`_` prefix); the public surface is `bind`,
  `rename_var`, `unify`.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
