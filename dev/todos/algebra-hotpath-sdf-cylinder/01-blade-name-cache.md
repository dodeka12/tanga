# Phase 1 — Cache blade-name string parsing per algebra

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Stop `Algebra._resolve_key_signed` re-parsing the same string blade name on
every call by adding a per-algebra cache. This removes the per-access
string-parse cost from `mv["e14"]`, `mv["e12"] = x`, and string keys in
`Algebra.multivector(...)` (report
`_input/pytanga-mv-string-blade-key-parsing-overhead.md`, fix #1, per-algebra
dict alternative).

## Files

- Edit: `py/pytanga/algebra/_algebra.py`
- New: `py/tests/algebra/test_resolve_key_cache.py`

## Steps

- [x] **1.1 — Add a per-algebra cache attribute**
  - In `Algebra.__init__`, next to the other instance attributes, add
    `self._blade_name_cache: dict[str, tuple[int, int]] = {}`.

- [x] **1.2 — Populate the cache on the string branch**
  - In `Algebra._resolve_key_signed`, after the `int` and `tuple` fast paths,
    check and populate the cache:
    ```python
    cached = self._blade_name_cache.get(key)
    if cached is not None:
        return cached
    from ._blade_names import blade_id_signed
    result = blade_id_signed(key, self._dim, self.blade_names_comma_separated)
    self._blade_name_cache[key] = result
    return result
    ```
  - `key` is a `str` here (the int/tuple branches returned earlier), so it is
    hashable. Do not cache failures: only store `result` after a successful
    parse, so invalid names keep raising `ValueError` on every call.
  - `blade_id_signed` stays an uncached, pure function; only the string branch
    of `_resolve_key_signed` is cached.

- [x] **1.3 — Add tests**
  - New `py/tests/algebra/test_resolve_key_cache.py` (annotated `-> None` tests):
    - `test_string_key_is_cached`: on `BasisE3()`, call
      `alg._resolve_key_signed("e12")` twice; assert both return `(3, 1)` and
      `alg._blade_name_cache == {"e12": (3, 1)}` (one entry, no re-parse).
    - `test_reversed_name_caches_sign`: `alg._resolve_key_signed("e21")` returns
      `(3, -1)` and is stored under `"e21"` (distinct key, correct sign).
    - `test_public_access_roundtrip`: `mv = alg.multivector({"e12": 2.0})`;
      `mv["e12"] == 2.0` and `mv["e21"] == -2.0`.
  - Import `BasisE3` from `pytanga.basis` (float, dim=3, non-modular).

## Validation

```
uv run pytest py/tests/algebra/test_resolve_key_cache.py -q
uv run ruff check py/pytanga/algebra/_algebra.py py/tests/algebra/test_resolve_key_cache.py
```

## Notes

- The cache key is just the blade name because `dim` and `comma` are per-algebra
  constants — no cross-algebra collision is possible.
- `Algebra.blade_id(name)` / `blade_name(...)` (display/formatting helpers) do
  not go through `_resolve_key_signed`, so they stay uncached; they are not hot
  paths.
- `BladeMask` string parsing goes through `_parse_mv_string`, not
  `_resolve_key_signed`; it runs once at construction, so it is intentionally
  not cached here.
