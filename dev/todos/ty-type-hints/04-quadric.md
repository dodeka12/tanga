# Phase 4 — `pytanga/quadric`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `quadric-module.md` and `geometry-module-layering.md`) for the subsystem(s)
> this work touches, so the new code aligns with the documented architecture.
> If this work introduces or changes architecture, update the developer docs.

## Goal

Annotate `py/pytanga/quadric` (101 untyped functions) — the `Conic` / `Quadric3D`
types, refine/create/analysis, point recovery, and quadric intersection.  This
package sits below `geometry.entities` in the documented DAG and lazily imports
`geometry.entities`, so cross-references use `TYPE_CHECKING`.

## Files

- Edit: `py/pytanga/quadric/__init__.py`
- Edit: `py/pytanga/quadric/_build.py`
- Edit: `py/pytanga/quadric/_embedding.py`
- Edit: `py/pytanga/quadric/_create.py`
- Edit: `py/pytanga/quadric/_analysis.py`
- Edit: `py/pytanga/quadric/_intersection.py`
- Edit: `py/pytanga/quadric/_pointset.py`
- Edit: `py/pytanga/quadric/refine.py`
- Edit: `py/pytanga/quadric/_conic.py` (if present) and any remaining modules

## Steps

- [x] **4.1 — Core types** — `Conic` / `Quadric3D` dataclasses, `from_coeffs` /
  `to_coeffs`, the `EConicKind` / `EQuadricKind` enums, and `Refinable.refine`
  implementations (`-> Ellipse | Hyperbola | ...`, i.e. the `Entity` union via
  `TYPE_CHECKING`).
- [x] **4.2 — `refine.py`** — `refine_conic` / `refine_quadric` and their private
  helpers (`_plane_from_quadric`, `_plane_pair_from_quadric`, etc.), all
  `-> <specific entity>` / `-> tuple[Plane, Plane]`.
- [x] **4.3 — `_build.py` + `_embedding.py`** — `embed_point`, the quadric-matrix
  builders (`-> np.ndarray`), and the rotation-rotor construction (`-> MV`).
- [x] **4.4 — `_create.py`** — entity→MV creation (`-> MV`); inputs are entity
  types via `TYPE_CHECKING`.
- [x] **4.5 — `_analysis.py`** — MV→entity analysis (`analyze_operator`,
  `_analyze_q3`, `_analyze_q3_opns`) with `MV` / `Algebra` under `TYPE_CHECKING`.
- [x] **4.6 — `_intersection.py` + `_pointset.py`** — `intersect_quadrics`,
  `intersect_three_quadrics`, point-recovery helpers (`-> PlaneConicPair | Curve`,
  `-> PointSet`), keeping the existing lazy entity imports.

- [x] **4.7 — Resolve `pytanga/quadric` ty diagnostics**
  - `uv run ty check py/pytanga/quadric` → 0 (baseline: 21 diagnostics).
  - Fix each (real bug / annotation inaccuracy) or add
    `# ty: ignore[<rule>]  # <reason>` for verified false positives.

## Validation

`uv run ruff check --select ANN --ignore ANN401 py/pytanga/quadric` → 0
`uv run ty check py/pytanga/quadric` → 0
`uv run pytest py/tests/geometry/test_conic_analysis.py py/tests/geometry/test_conic_create.py py/tests/geometry/test_conic_entities.py py/tests/geometry/test_conic_intersections.py -q`

## Notes

- Respect the documented `quadric ↔ geometry.entities` lazy cycle: import
  `Point` / `Direction` / `Plane` / entity types under `TYPE_CHECKING` (or keep
  the existing lazy imports inside functions) — never at module import time.
- The `Refinable` protocol's `refine()` return type must stay consistent with the
  entity types returned by `geometry.refine`.
