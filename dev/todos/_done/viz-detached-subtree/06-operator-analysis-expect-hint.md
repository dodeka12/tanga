# Phase 6 — `expect=` hint for `analyze_operator`

## Goal

Support the `wafer_grinding.versor_to_operator` use case: let callers ask
`analyze_operator(mv, expect=Rotor)` or `analyze_operator(mv,
expect=GeneralRotor)` and get the requested rotation instead of a half-turn
reflection (`ReflectionLine` in 3D, `ReflectionPoint` in 2D) — an exact
reinterpretation — without the caller hand-rolling the conversion.

## Files

- Edit: `py/pytanga/geometry/analysis.py`
- Edit: `py/pytanga/geometry/_geometry.py`
- Edit: `py/tests/geometry/test_typed_analyzers.py` (and/or the per-algebra
  `test_geometry_*_analysis.py` files, incl. N2/PGA2 for the 2D case)

## Steps

- [x] **6.1 — `analyze_operator(mv, *, expect=None)`**
  - Add the keyword; after the natural classification, apply the coercion rule:
    if `expect` is given and the result is not an instance of `expect`, try
    `_coerce_operator(result, expect, alg_type)` (passing `_detect(mv._alg)`);
    return the coerced operator when it matches, else the natural result.
    Accept `type[Operator] | tuple[type, ...]`.

- [x] **6.2 — `_coerce_operator` reflection → rotation rules (dimension-gated)**
  - 3D (`alg_type in {"e3", "p3", "pga3", "n3"}`): `ReflectionLine` →
    `Rotor(angle=math.pi, axis=line.direction)` for `expect=Rotor` (only when
    the line passes through the origin); → `GeneralRotor(angle=math.pi,
    axis=line.direction, origin=line.origin)` for `expect=GeneralRotor`.
  - 2D (`alg_type in {"p2", "pga2", "n2"}`): `ReflectionPoint` →
    `Rotor(angle=math.pi, axis=Direction(0,0,1))` for `expect=Rotor` (only when
    the point is the origin); → `GeneralRotor(angle=math.pi,
    axis=Direction(0,0,1), origin=point)` for `expect=GeneralRotor`.
  - `ReflectionPlane`, 3D `ReflectionPoint`, and 2D `ReflectionLine` are
    improper and never coerce (guard returns the natural result).
  - One extensible mapping; a non-origin half-turn only coerces to
    `GeneralRotor` (a plain `Rotor` cannot carry the origin).

- [x] **6.3 — Thread `expect` through `analyze` (module) and `Geometry`**
  - `analysis.analyze(mv, *, expect=None)`: forward `expect` only to the
    `analyze_operator` fallback (entity analysis ignores it).
  - `Geometry.which_operator(mv, *, expect=None)` and
    `Geometry.analyze(mv, *, expect=None)`: thin forwarders.

- [x] **6.4 — Tests**
  - 3D half-turn + perpendicular-offset versor: `analyze_operator(mv)` →
    `ReflectionLine`; `analyze_operator(mv, expect=GeneralRotor)` →
    `GeneralRotor` with `angle≈π`, matching axis/origin;
    `analyze_operator(mv, expect=Rotor)` → `Rotor` with `angle≈π` (through
    origin); `expect=<unrelated type>` still returns `ReflectionLine`.
  - 2D point reflection: `analyze_operator(mv, expect=GeneralRotor)` →
    `GeneralRotor(angle≈π, axis=(0,0,1), origin=point)`; `expect=Rotor` (origin
    point) → `Rotor(angle≈π, axis=(0,0,1))`.
  - Gating guards: a 3D `ReflectionPoint` and a 2D `ReflectionLine` are **not**
    coerced to `Rotor`/`GeneralRotor` (returned unchanged).
  - `Geometry.analyze(mv, expect=GeneralRotor)` returns `GeneralRotor`.

## Validation

`uv run pytest py/tests/geometry/test_typed_analyzers.py py/tests/geometry/test_geometry_e3_analysis.py py/tests/geometry/test_geometry_n2_analysis.py py/tests/geometry/test_geometry_pga2_analysis.py -q && uv run ruff check py/pytanga/geometry/analysis.py py/pytanga/geometry/_geometry.py`

## Notes

- `expect` only *widens* what is accepted — it never hides a different
  classification; when no rule matches, the natural result is returned.
- Verify the exact half-turn construction used by `wafer_grinding` (reference:
  `_input/pytanga-operator-analysis-hint-and-vizgroup-auto-id.md`) when writing
  the test so it reproduces the real 3D `ReflectionLine` case.
- Confirm the per-algebra support (which algebras emit `ReflectionPoint` in 2D
  vs 3D, and where `GeneralRotor` is accepted) against the operator coverage
  matrix in `docs/py/ga/geometry/operators.md` before finalizing the gating.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture. If this
work introduces or changes architecture, update the developer docs.
