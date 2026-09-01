# Phase 2 — PH curve core (`PHCurve2D` / `PHCurve3D`)

## Goal

Add `py/pytanga/geometry/phcurve.py` implementing the quintic PH Hermite
interpolant (Perwass reflection form) with pre-computed curve parameter vectors
and the full evaluation API, and export it from the geometry package.

## Files

- New: `py/pytanga/geometry/phcurve.py`
- New: `py/tests/geometry/test_phcurve.py`
- Edit: `py/pytanga/geometry/__init__.py` (import + `__all__`)

## Steps

- [ ] **2.1 — Implement `_PHCurveBase(dim)` constructor pre-computation**
  - Coerce inputs (`to_point`, `to_direction`, `to_float`); require
    `total_time > 0`; validate velocities have the right dimensionality
    (2D: `z == 0`; 3D: any).
  - Convert to `[0,1]` data: `d0 = T·v0`, `d2 = T·v2`, `Δp = p2 − p0`
    (numpy arrays of length `dim`).
  - Choose unit `ν`: default `normalize(d̂0 + d̂2)`; if near-zero, a unit
    perpendicular of `d0`; honor a user-supplied `nu=`.
  - Follow the README math contract to compute `a0, a2, u, v, a1`, the
    hodograph coefficients `c0…c4`, and the control points `P0…P5`.
  - Store as read-only attributes: `control_points` (6×dim), `hodograph`
    (5×dim), plus `start`, `end`, `start_vel`, `end_vel`, `total_time`, `nu`.
- [ ] **2.2 — Implement scalar evaluators**
  - Bernstein evaluation (numpy `polyval`-free, e.g. via `np.polynomial` or
    explicit binomial weights) for position (degree 5), velocity (degree 4, ÷T),
    acceleration (`4Σ(c_{i+1}−c_i)B_i³`, ÷T²).
  - `position(t) -> Point`, `velocity(t) -> Direction`,
    `acceleration(t) -> Direction` (2D returns `z=0`).
- [ ] **2.3 — Implement list / regular-interval accessors**
  - `positions/velocities/accelerations(times)` accept an iterable of floats.
  - `*_regular(n)` sample `n` points over `np.linspace(0, total_time, n)`
    (validate `n >= 2`).
- [ ] **2.4 — Implement acceleration decomposition + curvature**
  - `acceleration_along(t) -> Direction` = `(a·v̂)v̂`.
  - `acceleration_perpendicular(t) -> Direction` = `a − a_along`.
  - `curvature(t) -> float` = `|a_perp| / |v|²` (guard `|v| ≈ 0` → raise or
    return `inf`; document the choice).
  - Each with `_times(times)` and `_regular(n)` variants.
- [ ] **2.5 — Export from `pytanga.geometry`** (add to `__init__.py`/`__all__`).
- [ ] **2.6 — Tests**
  - Endpoints: `position(0) == start`, `position(T) == end`,
    `velocity(0) == start_vel`, `velocity(T) == end_vel`.
  - Straight-line case (collinear data) is a straight line.
  - `∫r′ ≈ Δp` (trapezoid over dense samples).
  - PH property: `|v(t)|²` is a quartic polynomial (evaluate at several `t`).
  - `curvature` of a known planar case (e.g. constant-radius arc data)
    approximates the expected value; `acceleration_along + _perpendicular == a`.
  - 2D/3D parity: a planar 3D curve matches the corresponding 2D curve in x,y.

## Validation

`uv run pytest py/tests/geometry/test_phcurve.py -q`

## Notes

- Keep the module free of any `pytanga.viz` import (viz consumes geometry, not
  the reverse).
- `positions_regular`/`velocities_regular` are the sampling entry points the
  viz serializer will call in Phase 4.
