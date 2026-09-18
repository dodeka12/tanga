# Phase 2 — Memoize `AffineExpression` structural metadata

## Goal

Cache the three structural computations that `AffineExpression.__call__`
recomputes on every call — `_union_masks()`, `out_mask`, and
`_counting_axes_union()` — so repeated evaluation skips `BladeMask.union` +
`_attach_display_basis` work. All three are pure functions of the immutable
`_terms` list, so a lazy once-only cache is safe.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- Edit: `py/tests/expression/test_expression.py` (or a new focused test file) —
  assert repeated `__call__`/property access reuses cached objects.

## Steps

- [x] **2.1 — Extend `AffineExpression.__slots__` and `__init__`**
  - Change `__slots__ = ("_terms",)` to include `"_union_cache"`,
    `"_out_mask_cache"`, `"_counting_cache"`.
  - In `__init__`, initialise the three cache slots to `None`.

- [x] **2.2 — Memoize `_union_masks()`**
  - `_union_masks` (line 820) returns `self._union_cache` when not `None`;
    otherwise computes the union into a local dict, stores it, and returns it.
  - Keep the result dict as-is (the public `masks` property already returns a
    fresh dict; `_union_masks` is internal — but do not let callers mutate the
    cached dict: return it directly only if no caller mutates it. Audit the two
    internal callers: `__call__` and `get_tensor`/`_variable_matrix`. If any
    mutates, return `dict(...)` copies as needed and cache the canonical copy.)

- [x] **2.3 — Memoize `out_mask`**
  - The `out_mask` property (line 848) computes the union of term output masks;
    cache it in `_out_mask_cache` (first term's mask when `len(_terms) == 1`,
    else fold `union`).

- [x] **2.4 — Memoize `_counting_axes_union()`**
  - Cache in `_counting_cache` (the method at line 831 may raise on inconsistent
    lengths; cache only after a successful computation).

- [x] **2.5 — Unit tests**
  - Build an `AffineExpression` of ≥ 2 terms sharing a variable; call `__call__`
    twice and assert `aff._union_cache is not None` and that the second call
    returns the same cached dict (via `aff._union_masks()` identity).
  - Assert `aff.out_mask` returns the same object on repeated access.
  - Assert `_counting_axes_union()` caches (build a counting-axis affine
    expression and access twice).

## Validation

`uv run pytest py/tests/expression -q`

## Notes

- `AffineExpression._terms` is written only in `__init__` (verified); nothing
  mutates it in place, so no invalidation is required. If a later phase ever
  mutates `_terms`, this cache must be dropped — keep that in mind.
- This phase is independent of Phase 1 but lands first because Phase 3's
  `AffineExpression.compile()`/auto-path relies on cheap `_union_masks` and
  `out_mask`.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
