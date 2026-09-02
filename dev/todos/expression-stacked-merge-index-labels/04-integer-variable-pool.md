# Phase 4 — integer pool for `Variable` labels

## Goal

Switch `Variable` from the exhaustible letter alphabet to a monotonic integer
pool, and finish the expression-layer integration so `Expression`s are built and
evaluated with integer axis labels. This removes the `max_variables() == 12`
limit.

## Files

- Edit: `py/pytanga/expression/_labels.py`
- Edit: `py/pytanga/expression/_variable.py`
- Edit: `py/pytanga/expression/_expression.py`
- Edit: `py/tests/expression/test_labels.py`
- Edit: `py/tests/expression/test_variable.py`
- Edit: `py/tests/expression/test_expression.py`

## Steps

- [x] **4.1 — Add the integer pool**
  - In `_labels.py`, reimplement `allocate_block(size=MAX_DEGREE)` to return a
    `tuple[int, ...]` from a module-level monotonic counter
    (`(0,1,2,3)`, `(4,5,6,7)`, …).
  - Update `allocate_label()` to return the first integer of a block, and
    `block_for_label(label: int)` to resolve an integer back to its full block
    (keep a dict, or compute `base = label - label % MAX_DEGREE`).
  - Change `max_variables()` to reflect the integer pool (e.g. return
    `sys.maxsize // MAX_DEGREE`, or document it as effectively unbounded) and
    drop the letter-alphabet exhaustion path. Keep the letter helpers only where
    tests/back-compat require them, or remove them and their tests.

- [x] **4.2 — Make `Variable` use integer labels**
  - In `_variable.py`, leave `_name` as the user-facing string but let
    `_labels = allocate_block()` become `tuple[int, ...]`; `label` returns
    `self._labels[0]` (an `int`).
  - Update `__repr__` so it still shows the name and mask (no change needed to
    the letter-based display).

- [x] **4.3 — Integrate integer labels into `_expression.py`**
  - Confirm `_product`'s `add("var", ...)` / `add("expr", ...)` and
    `block_for_label` work with `int` keys (they now do, since `block_for_label`
    accepts `int`).
  - Update the `_involution` Variable path, `inv` (`allocate_block()[0]`), and
    `_evaluate` binding construction to pass integer occurrence labels through
    the structured `MVLabeledTensor` constructor (single `AxisName` and
    `[(label, "*"), (batch, "_")]` forms).
  - Ensure `OUT_LABEL` stays `"k"` (string) so labels legitimately mix `str`
    output with `int` variables.

- [x] **4.4 — Update and extend tests**
  - In `test_labels.py` and `test_variable.py`, assert `allocate_block()`
    returns `tuple[int, ...]`, `Variable.labels`/`label` are integers, and
    creating more than 12 variables no longer raises.
  - In `test_expression.py`, keep the existing behaviour assertions (they should
    be label-agnostic) and add one mixed-label smoke test exercising a product
    with integer variable labels.

## Validation

`uv run pytest py/tests/expression/ py/tests/tensor/ -q`

## Notes

- `OUT_LABEL` and the per-evaluation batch-letter pool are intentionally kept as
  strings; they do not accumulate across `Variable` instances, so they cannot
  exhaust the integer pool.
- After this phase, the expression subsystem no longer depends on the
  50-letter alphabet for variable identity.
