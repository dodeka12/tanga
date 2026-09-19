# Phase 1 — Cheap blade validation

## Goal

Add `BladeMask.ids_outside(mv)` and rewrite `_check_blades` to use it, so
validating a concrete `MV` against a variable mask costs one C++ `blade_mask`
call instead of a full `BladeMask` build + display-basis attachment (~33 C++
calls). No change to the validation *semantics* (it still raises on blades
outside the mask).

## Files

- Edit: `py/pytanga/blade_mask/_mask.py`
- Edit: `py/pytanga/expression/_expression.py` (`_check_blades`)
- Edit: `py/tests/blade_mask/test_blade_mask.py` (add `ids_outside` tests)
- Edit: `py/tests/expression/test_expression.py` (validation still raises)

## Steps

- [x] **1.1 — Add `BladeMask.ids_outside(mv)`**
  - Signature: `def ids_outside(self, mv: MV) -> list[int]`.
  - Assert `mv.algebra is self._alg` (match the `union`/`intersection` guard
    style), then `raw = self._ids_from_mv(mv, only_nonzero=True)` and return
    `[bid for bid in raw if bid not in self._index]`.
  - Do **not** call `_attach_display_basis` and do **not** construct a
    `BladeMask`. Docstring states this is the cheap membership diff used by the
    expression evaluator.

- [x] **1.2 — Rewrite `_check_blades`**
  - In `_expression.py:1907`, replace the `BladeMask(value).ids` body with
    `outside = mask.ids_outside(value)`; keep the identical `ValueError` message.
  - `_check_blades` is only ever called after the value is confirmed to be an
    `MV` (both call sites coerce `int`/`float` first), so no type re-check is
    needed.

- [x] **1.3 — Unit tests**
  - `ids_outside` returns `[]` for an `MV` fully inside the mask.
  - `ids_outside` returns exactly the out-of-mask ids, ascending, for an `MV`
    with extra blades (use `BasisN3`; e.g. mask `[e12, e13]`, value with `e12 +
    e23` → `[e23_id]`).
  - `_check_blades` still raises for an out-of-mask binding and still passes for
    an in-mask binding (reuse/extend the existing expression tests; assert the
    raised message is unchanged).

## Validation

`uv run pytest py/tests/blade_mask/test_blade_mask.py py/tests/expression/test_expression.py -q`

## Notes

- `_ids_from_mv` is already a `@classmethod` (`_mask.py:136`), so the new method
  can call it directly.
- Do not change `BladeMask.__init__` or `union` here; the display-basis
  attachment is still needed for mask *construction*, just not for this
  membership diff.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
