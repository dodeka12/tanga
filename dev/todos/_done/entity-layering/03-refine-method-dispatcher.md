# Phase 3 — `refine` as a `Refinable` method + duck-typed dispatcher

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Replace the module-level `isinstance` dispatch with `Conic.refine()` /
`Quadric3D.refine()` methods (satisfying `Refinable`) and make
`pytanga.geometry.refine` a duck-typed dispatcher.  Keep the refinement math in
`quadric.refine` with its lazy `geometry.entities` import.

## Files

- Edit: `py/pytanga/quadric/conic.py` (add `refine()` methods)
- Edit: `py/pytanga/quadric/refine.py` (drop `refine`/`refine_entity`; keep `refine_conic`/`refine_quadric` + helpers)
- Edit: `py/pytanga/quadric/__init__.py` (export `refine_conic`/`refine_quadric` only)
- Edit: `py/pytanga/geometry/refine.py` (duck-typed dispatcher, no longer a shim)
- Edit: `py/pytanga/geometry/__init__.py` (re-export `refine`/`refine_entity` unchanged)
- Edit: `py/tests/geometry/test_conic_analysis.py`, `test_conic_create.py` (verify; no API change expected)

## Steps

- [x] **3.1 — Add `refine()` methods**
  - `quadric/conic.py`: `from .refine import refine_conic, refine_quadric` at
    module level (no cycle: `refine.py` lazy-imports `geometry.entities`).
  - `Conic.refine(self)` → `return refine_conic(self)`.
  - `Quadric3D.refine(self)` → `return refine_quadric(self)`.

- [x] **3.2 — Slim `quadric/refine.py`**
  - Remove `refine` and `refine_entity` (move to `geometry.refine`).
  - Keep `refine_conic`, `refine_quadric`, `_E()`, and all private helpers.

- [x] **3.3 — Update `quadric/__init__.py`**
  - Export `refine_conic`, `refine_quadric` (drop `refine`, `refine_entity`).

- [x] **3.4 — Duck-typed `geometry/refine.py`**
  - Implement `refine(entity)` via `getattr(entity, "refine", None)` +
    `callable` check, raising `TypeError` for non-refinable entities.
  - `refine_entity = refine` (or thin alias) for backward compat.
  - Remove the `from pytanga.quadric.refine import ...` shim.

- [x] **3.5 — Verify the public API**
  - `from pytanga.geometry import refine` and `refine_entity` still work.
  - `from pytanga.geometry import Conic, Quadric3D` and `refine(conic)` work.
  - `refine("not an entity")` raises `TypeError`.

## Validation

```
uv run pytest py/tests/geometry -q py/tests/viz -q
uv run python -c "from pytanga.geometry import Conic, refine; from pytanga.entity import Refinable; assert hasattr(Conic, 'refine'); print('ok')"
```

## Notes

- The generic `refine` is now geometry-level; `quadric` no longer exposes a
  geometry-typed dispatcher.  Per the pre-plan grep, only `geometry/refine.py`
  imported `pytanga.quadric.refine`'s dispatchers — confirm nothing else does
  (`uv run grep -rn "quadric.refine" py/pytanga py/tests`).
