# Phase 1 — Reflection primitive (`refor`, `reflector`)

## Goal

Add `py/pytanga/geometry/reflection.py` with the Perwass reflector vector and
a `reflector()` function returning the reflection **line (E2) / plane (E3)** MV
that maps one vector into another, and export it from the geometry package.

## Files

- New: `py/pytanga/geometry/reflection.py`
- New: `py/tests/geometry/test_reflection.py`
- Edit: `py/pytanga/geometry/__init__.py` (import + `__all__`)

## Steps

- [ ] **1.1 — Implement `refor(x, y) -> Direction`**
  - Accept `Direction | Point | 3-sequence` (coerce with `to_direction` /
    `to_triple`), reject zero-length inputs.
  - Return `sqrt(|y|/|x|) * (x̂ + ŷ)/|x̂ + ŷ|` as a `Direction`.
  - Use numpy for the arithmetic; convert the result to floats.
- [ ] **1.2 — Implement `reflector(basis, a, b) -> MV`**
  - Detect `BasisE2`/`BasisE3` (mirror `create._detect`); raise `ValueError`
    for other bases.
  - Normalize `a`, `b` to unit directions (coerce MVs via `to_direction`).
  - E2: build grade-1 vector along `(â + b̂)`; fall back to a perpendicular of
    `â` when `|â + b̂| ≈ 0` (anti-parallel input).
  - E3: build grade-2 bivector `{E23: n.x, E13: -n.y, E12: n.z}` with unit
    normal `n = (â − b̂)`; fall back to a perpendicular of `â` when
    `|â − b̂| ≈ 0` (parallel input).
  - Return the unit-normed MV (`basis.multivector({...})`).
- [ ] **1.3 — Export from `pytanga.geometry`**
  - Add `from .reflection import refor, reflector` and both names to
    `__all__`.
- [ ] **1.4 — Tests**
  - `test_reflection.py`: `refor` maps `refor·x·refor = y` (numeric via
    numpy); `reflector(E2, e1, e2)` reflects `e1 → e2` under `d·v·d.rev()`;
    `reflector(E3, e1, e2)` reflects `e1 → e2` under `−B·v·B.rev()`; parallel
    and anti-parallel fallbacks; non-E2/E3 basis raises `ValueError`.

## Validation

`uv run pytest py/tests/geometry/test_reflection.py -q`

## Notes

- The E3 plane blade layout matches `create_e3.create_reflection_plane`.
- `refor` is the scaled bisector (magnitude `sqrt(|y|/|x|)`), reused verbatim by
  the PH curve in Phase 2 — do not normalize it there.
