# Phase 2 — `pytanga/entity` (Vec3 / Point / Direction)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md`) for the subsystem(s) this work touches, so the
> new code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Annotate every function and method in `py/pytanga/entity` (31 untyped) — the leaf
package.  This phase establishes the canonical pattern every later phase copies.

## Files

- Edit: `py/pytanga/entity/vec3.py`
- Edit: `py/pytanga/entity/point.py`
- Edit: `py/pytanga/entity/direction.py`
- Edit: `py/pytanga/entity/base.py`
- Edit: `py/pytanga/entity/_util.py`

## Steps

- [x] **2.1 — `vec3.py`**
  - `__eq__(self, other: object) -> bool`; `__neg__`, `__add__`, `__sub__`,
    `elem_mul`, `dot`, `cross`, `mag`, `normalized` already typed — confirm they
    stay `-> Vec3` / `-> float`.
  - `__mul__(self, other: "Vec3" | int | float) -> "Vec3"` (element-wise for
    `Vec3`, scalar otherwise).
  - `__rmul__` / `__truediv__(self, scalar: int | float) -> "Vec3"`.
  - `to_point(self) -> "Point"`, `to_direction(self) -> "Direction"`,
    `from_point(cls, p: "Point") -> "Vec3"`,
    `from_direction(cls, d: "Direction") -> "Vec3"` (imports stay local/string).
- [x] **2.2 — `point.py` / `direction.py`**
  - `__init__(self, x: float | MV = 0.0, y: float = 0.0, z: float = 0.0) -> None`
    (constructor accepts coords **or** a single MV via `_convert_mv`).
  - Add `if TYPE_CHECKING: from pytanga.algebra._mv import MV` — **no runtime
    import** (entities must stay pure, per `geometry-module-layering.md`).
  - Annotate `__eq__(self, other: object) -> bool`, `__neg__`, `__add__` /
    `__radd__`, `__sub__`, `__mul__` / `__rmul__`, `__truediv__`, `cross`,
    `normalized`, `to_vec3` with precise unions (`Point | Direction`,
    `-> Direction`, etc.) — do **not** weaken to `Any`.
- [x] **2.3 — `base.py`**
  - `Refinable.refine(self) -> object` (the protocol lives in the leaf package,
    which must not import `pytanga.geometry`/`pytanga.quadric`; the concrete
    implementations — `Conic`, `Quadric3D` — override with the precise entity
    return type).  Keep the protocol's `...` body.
- [x] **2.4 — `_util.py`**
  - `_fmt_v(x: float, y: float, z: float) -> str`;
    `_is_mv(x: object) -> bool`;
    `_convert_mv(name: str, mv: object) -> "Entity"`;
    `_scalar(value: float | MV) -> float`;
    `register_analyzer(name: str, fn: Callable[[object], "Entity"]) -> None`
    (import `Callable` from `collections.abc`).

- [x] **2.5 — Resolve `pytanga/entity` ty diagnostics**
  - `uv run ty check py/pytanga/entity` → 0 (baseline: 7 diagnostics).
  - Fix each (real bug / annotation inaccuracy) or add
    `# ty: ignore[<rule>]  # <reason>` for verified false positives (see the
    README "Suppression convention").  Remove any suppression that becomes stale.

## Validation

`uv run ruff check --select ANN --ignore ANN401 py/pytanga/entity` → 0
`uv run ty check py/pytanga/entity` → 0
`uv run pytest py/tests/geometry/test_vec3.py py/tests/geometry/test_entity_leaf.py -q`

## Notes

- This is the canonical example phase; every later phase copies this pattern
  (`from __future__ import annotations`, `TYPE_CHECKING` for `MV`, `-> None`).
- `Point`/`Direction` constructor coercion (`_is_mv(x)` branch) must be
  preserved exactly — only the signature gains annotations.
