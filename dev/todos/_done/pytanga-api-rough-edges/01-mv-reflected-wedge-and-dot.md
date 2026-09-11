# Phase 1 — `MV` reflected `^` / `|` with non-`MV` operands

## Goal

Make `constant_mv ^ variable`, `constant_mv ^ expression`, `constant_mv |
variable`, and `constant_mv | expression` build the expected `Expression`
instead of raising `AttributeError: 'Variable' object has no attribute '_impl'`.
(`constant_mv * variable` already works because `MV.__mul__` returns
`NotImplemented`.)

## Files

- Edit: `py/pytanga/algebra/_mv.py`
- Edit: `py/tests/expression/test_variable.py` (add reflected-op tests)
- Edit: `py/tests/expression/test_expression.py` (add `Expression`-right tests)

## Steps

- [x] **1.1 — Guard `MV.__xor__` / `MV.__or__`**
  - In `_mv.py`, add `from types import NotImplementedType` to the existing
    import block.
  - Change `__xor__` and `__or__` to return `NotImplemented` when `other` is
    not an `MV` (mirror `__mul__`), keeping the existing `self._alg.op(...)` /
    `self._alg.ip(...)` bodies for the `MV`-vs-`MV` case:
    ```python
    def __xor__(self, other: "MV") -> "MV | NotImplementedType":
        if not isinstance(other, MV):
            return NotImplemented
        return self._alg.op(self, other)

    def __or__(self, other: "MV") -> "MV | NotImplementedType":
        if not isinstance(other, MV):
            return NotImplemented
        return self._alg.ip(self, other)
    ```

- [x] **1.2 — Tests: reflected ops with a `Variable` on the right**
  - In `py/tests/expression/test_variable.py`, add tests asserting `x_cm ^ omega`,
    `x_cm | omega`, and `x_cm * omega` each return an `Expression` whose `names`
    is `{"omega"}` (use a constant `MV` from `BasisN3` and a `Variable` over a
    `BladeMask`, mirroring the note's minimal repro). Reset the label allocator
    first (`_reset_allocator()`) per existing convention.

- [x] **1.3 — Tests: reflected ops with an `Expression` on the right**
  - In `py/tests/expression/test_expression.py`, add a test that `x_cm ^ (omega |
    x_b)` (constant on the left, `Expression` on the right) builds an
    `Expression` with the expected combined `names`.

## Validation

`uv run pytest py/tests/expression/ py/tests/algebra/ -q`

## Notes

- The reflected dunders (`__rxor__`/`__ror__`/`__rmul__`) already exist on
  `Variable`, `Expression`, and `AffineExpression`; they were simply unreachable
  because `MV.__xor__`/`__or__` never returned `NotImplemented`. No new product
  logic is needed — `_product` already handles a constant `MV` on either side.
- `MV.__mul__` (already guarded) is the reference for the exact pattern; do not
  change `__truediv__`/`__rtruediv__`, which already return `NotImplemented` for
  non-`MV`.
