# Phase 4 — examples to pure GA

## Goal

Rewrite the quadric examples to use only `BasisQ2`/`BasisQ3` + `geo(...)` + GA ops
(`op`/`join`, `^`, `dual`, `sp`) + `analyze`/`refine`, and add a dedicated 2D
conic-intersection demo.

## Files

- Edit: `py/examples/ga/quadric/quadric3d_raycast.py`, `quadric_intersection_demo.py`,
  `general_quadric.py`, `tolerant_classification.py`, `quadric3d_demo.py`,
  `conic_demo.py`
- New: `py/examples/ga/quadric/conic_intersection_demo.py`
- Regenerate: `docs/py/examples/**` (via `generate-example-docs.py`)

## Steps

- [x] **4.1 — `quadric3d_raycast.py`**
  - Replace `quadric_from_points` + `to_coeffs` + `basis.multivector({…})` with
    `join([geo(Point(*p)) for p in points])` + `geo.analyze` + `refine`.

- [x] **4.2 — `quadric_intersection_demo.py`**
  - Replace `intersect_quadrics(Q1, Q2)` with
    `geo.analyze(geo(Quadric3D(m1)) ^ geo(Quadric3D(m2)))` (3D only).

- [x] **4.3 — `general_quadric.py` + `tolerant_classification.py`**
  - Build quadrics as `Quadric3D(matrix)` directly (drop the explicit `to_coeffs`).

- [x] **4.4 — `quadric3d_demo.py` + `conic_demo.py`**
  - Use the new `join` / `op` sequence functions in place of
    `functools.reduce(…)` / `^` chains.

- [x] **4.5 — new `conic_intersection_demo.py`**
  - Two 2D conics (`geo(Conic(m1)) ^ geo(Conic(m2))` in IPNS) → `geo.analyze` →
    `PointSet`; print the intersection points. Follow `dev/workflows/example-docs.md`
    (description + `Keywords:` header).

- [x] **4.6 — regenerate example docs**
  - `uv run python tools/generate-example-docs.py`; confirm `--check` is clean.

## Validation

`uv run pytest py/tests/quadric -q && uv run python tools/generate-example-docs.py --check && uv run ruff check . && uv run ty check`

## Notes

- The 2D conic intersection is verified to work today: `analyze(c1 ^ c2)` → a
  `PointSet` of 4 points (see `_analysis.py::_analyze_q2` → `pointset_from_blade`).

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
> touches, so the new code aligns with the documented architecture. If this work
> introduces or changes architecture, update the developer docs.
