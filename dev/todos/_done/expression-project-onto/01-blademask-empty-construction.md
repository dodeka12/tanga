# Phase 1 — `BladeMask` empty construction

## Goal

Make `BladeMask(alg)` return the full algebra mask while `BladeMask(alg, [])` (or
`BladeMask(alg, set())`) returns an empty mask, and fix the downstream
`intersection` / `union` / `from_mv` behaviour this unblocks.

## Files

- Edit: `py/pytanga/blade_mask/_mask.py`
- Edit: `py/tests/blade_mask/test_blade_mask.py`

## Steps

- [x] **1.1 — Sentinel default for `ids`**
  - Change `__init__` signature to
    `ids: Iterable[int] | str | Iterable[str] | None = None`.
  - In the `Algebra` branch, treat `ids is None` as "no ids"; resolve strings,
    string-lists, and int-iterables as today; apply the full-mask default only when
    `ids is None` **and** `grades is None`.
  - Update the constructor docstring to document `BladeMask(alg)` (full) vs
    `BladeMask(alg, [])` (empty).

- [x] **1.2 — Tests**
  - Add: `BladeMask(alg)` → full; `BladeMask(alg, [])` → empty;
    `BladeMask(alg, set())` → empty.
  - Add: disjoint `intersection` → empty; `union(empty, empty)` → empty.
  - Add: `BladeMask(zero_mv)` and `BladeMask.from_mv(zero_mv)` → empty.
  - Keep the existing construction tests passing.

## Validation

`uv run pytest py/tests/blade_mask/test_blade_mask.py -q`

## Notes

- No other production caller relies on `BladeMask(alg, [])` meaning "full"
  (defaults use `BladeMask.full(alg)`); `from_mv` / `from_array` / `intersection` /
  `union` all pass an explicit (possibly empty) iterable and now resolve correctly.
- Empty product masks are now reachable (e.g. ``bivector ^ bivector`` in E3);
  `py/pytanga/tensor/product.py::product_tensor` gained a zero-tensor fast path
  because the C++ tensor builders assume non-empty masks.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
