# Phase 1 — Create `pytanga.entity` leaf (Vec3 / Point / Direction / Refinable)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Introduce a dependency-free `pytanga.entity` package that owns `Vec3`, `Point`,
`Direction`, the `Refinable` protocol, and the MV-conversion registry; re-point
`geometry.entities` at it via re-export shims so the public API is unchanged.

## Files

- New: `py/pytanga/entity/__init__.py`
- New: `py/pytanga/entity/vec3.py`
- New: `py/pytanga/entity/point.py`
- New: `py/pytanga/entity/direction.py`
- New: `py/pytanga/entity/base.py`
- New: `py/pytanga/entity/_util.py`
- Edit: `py/pytanga/geometry/entities/point.py` (→ shim)
- Edit: `py/pytanga/geometry/entities/direction.py` (→ shim)
- Edit: `py/pytanga/geometry/entities/_util.py` (keep `_compute_start_direction`; registry moves)
- Edit: `py/pytanga/geometry/entities/_coerce.py`
- Edit: `py/pytanga/geometry/entities/__init__.py`
- Edit: `py/pytanga/geometry/analysis.py` (register_analyzer import path)
- New: `py/tests/geometry/test_vec3.py`
- New: `py/tests/geometry/test_entity_leaf.py`

## Steps

- [x] **1.1 — Create `pytanga.entity` registry helper (`_util.py`)**
  - Move `_fmt_v`, `_is_mv`, `_ANALYZERS`, `register_analyzer`, `_convert_mv`,
    `_scalar` from `geometry/entities/_util.py` verbatim.
  - Do NOT move `_compute_start_direction` (it is geometry-specific and stays in
    `geometry.entities._util`).

- [x] **1.2 — Add `Vec3` (`vec3.py`)**
  - Implement the `Vec3` frozen dataclass per the README contract: `+`, `-`,
    `__neg__`, `*` (scalar OR element-wise), `__rmul__`, `__truediv__`,
    `elem_mul`, `dot`, `cross`, `mag`, `normalized`, `to_point`,
    `to_direction`, `from_point`, `from_direction`.
  - `to_point`/`to_direction`/`from_point`/`from_direction` import `Point`/
    `Direction` lazily inside the method to keep `vec3.py` free of an import-time
    cycle with `point.py`/`direction.py`.

- [x] **1.3 — Re-home `Point` as `Point(Vec3)` (`point.py`)**
  - Subclass `Vec3`; inherit `x`/`y`/`z` and the pure `+`/`-`/`dot`/`mag` math.
  - Override `__init__` (MV conversion + float coercion, unchanged), `__repr__`
    (`Point(...)`), `__eq__` (Point or 3-tuple), `__neg__`, `__add__`, `__radd__`,
    `__sub__`, `__mul__`/`__rmul__`/`__truediv__` (scalar → Point), `cross`
    (→ Direction), `normalized` (→ Point), and add `to_vec3()`.
  - Preserve exact current behavior (see `geometry/entities/point.py`).

- [x] **1.4 — Re-home `Direction` as `Direction(Vec3)` (`direction.py`)**
  - Mirror 1.3 with `Dir(...)` repr and Direction-typed returns; add `to_vec3()`.

- [x] **1.5 — Add `Refinable` protocol (`base.py`)**
  - `@runtime_checkable class Refinable(Protocol)` with `def refine(self): ...`.
  - No `Entity` base class (see README non-goals).

- [x] **1.6 — Package `__init__` + re-export shims**
  - `pytanga/entity/__init__.py` exports `Vec3`, `Point`, `Direction`,
    `Refinable`, `register_analyzer`, `_is_mv`, `_scalar`.
  - `geometry/entities/point.py` → `from pytanga.entity import Point`.
  - `geometry/entities/direction.py` → `from pytanga.entity import Direction`.
  - `geometry/entities/_util.py` → re-export the registry from `pytanga.entity`
    for backward compat; keep `_compute_start_direction` (its `from .direction
    import Direction` now resolves through the shim).
  - `geometry/entities/_coerce.py` → import `Point`/`Direction` from
    `pytanga.entity` (or keep `from .point import Point` via the shim).
  - `geometry/entities/__init__.py` → import `Point`/`Direction` from
    `pytanga.entity`.

- [x] **1.7 — Update `analysis.py` registry registration**
  - `from pytanga.entity import register_analyzer` (keep the `.entities`
    re-export working too).

- [x] **1.8 — Tests**
  - `test_vec3.py`: `+`, `-`, `__neg__`, scalar `*`, element-wise `*`/`elem_mul`,
    `dot`, `cross`, `mag`, `normalized` (+ zero-length raises), `to_point`/
    `to_direction`/`from_point`/`from_direction` round-trips.
  - `test_entity_leaf.py`: Point/Direction behavior parity (equality with tuples,
    repr, typed arithmetic, `to_vec3`), and MV→Point conversion still works after
    `import pytanga.geometry` (registry populated).

## Validation

```
uv run pytest py/tests/geometry -q
uv run python -c "from pytanga.entity import Vec3, Point, Direction, Refinable; from pytanga.geometry import Point as P, Direction as D; assert P is Point and D is Direction; print('ok')"
```

## Notes

- Frozen-dataclass inheritance (`Point(Vec3)`, `Direction(Vec3)`) with a custom
  `__init__` and `__eq__`: do not redeclare `x`/`y`/`z` in the subclass; use
  `object.__setattr__` in the custom `__init__` as today.  Verify hashability and
  `==`-with-tuple still behave as before (add a regression assertion if needed).
- `Vec3.to_point()`/`to_direction()` lazy-import to avoid a `vec3 ↔ point/direction`
  import cycle within the leaf.
