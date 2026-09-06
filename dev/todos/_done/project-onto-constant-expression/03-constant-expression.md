# Phase 3 — constant `Expression(A)` / `Expression(A, BladeMask)`

## Goal

Make `Expression` constructible directly from a multivector, producing a
zero-variable constant expression.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- Edit: `py/tests/expression/test_expression.py`

## Steps

- [x] **3.1 — Extend `Expression.__init__`**
  - Change the signature to `def __init__(self, tensor, names=None, masks=None)`.
  - Add an MV fast path at the top:
    ```python
    if isinstance(tensor, MV):
        mask = names if isinstance(names, BladeMask) else BladeMask(tensor)
        self._tensor = MVLabeledTensor(to_tensor(tensor, mask=mask), OUT_LABEL)
        self._names = {}
        self._masks = {}
        return
    self._tensor = tensor
    self._names = dict(names)
    self._masks = dict(masks)
    ```
  - `MV`, `BladeMask`, `to_tensor`, `MVLabeledTensor`, `OUT_LABEL` are already
    imported in this module; add nothing unless a lint check says otherwise.

- [x] **3.2 — Tests**
  - In `py/tests/expression/test_expression.py`, add:
    - `Expression(A)` has `names == {}`, `masks == {}`, `out_mask ==
      BladeMask(A)`, `ndim == 1`, and `E()` returns `A` (constant → MV).
    - `Expression(A, mask)` has `out_mask == mask` and drops `A`'s blades
      outside the mask (assert via `E()` returning an MV equal to the filtered
      `A`, e.g. `A.project_onto(BladeMask(A).intersection(mask))`-style value or
      an explicit coefficient check).
  - Keep the existing internal-construction tests passing (no signature
    regression for `Expression(tensor, names, masks)`).

## Validation

`uv run pytest py/tests/expression/ -q`

## Notes

- `Expression(A)` deliberately produces a **constant** expression; evaluating it
  with no bindings returns `A` (restricted to the mask), and it can be added /
  multiplied with other expressions like any constant.
- This reuses the exact constant-folding path already used by `_to_expression`.
