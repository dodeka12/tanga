# Phase 5 — Example scripts

## Goal

Ship example scripts demonstrating the new capabilities: GA-native fitting + diagnostics,
the cone lift, and tolerant classification. All are headless (print-based, no `Visualizer`)
so they run in validation.

## Files

- New: `py/examples/ga/quadric/fit_conic_quadric.py`
- New: `py/examples/ga/quadric/cone_from_conic.py`
- New: `py/examples/ga/quadric/tolerant_classification.py`

## Steps

- [x] **5.1 — `fit_conic_quadric.py`**
  - Fit an ellipse from 5 points and a quadric from 9 points via `conic_from_points_svd`
    / `quadric_from_points_svd`; print `fit_singular_values` / `fit_nullity`; include a
    coplanar-circle degenerate case showing `fit_nullity >= 2`.
  - Docstring per `dev/workflows/example-docs.md` (one-line desc, `Run with:`, `Keywords:`).
- [x] **5.2 — `cone_from_conic.py`**
  - Fit a 2D conic, lift it via `BasisQ3(c)` / `cone_from_conic(basis, apex, conic)`;
    print the `Quadric3D` rank/kind and the zero incidence at the apex + base points.
- [x] **5.3 — `tolerant_classification.py`**
  - Build a noisy near-cone quadric, classify with `Geometry(BasisQ3(), tol=...)` →
    `geo.refine(...)`; show the default `.kind` vs the tolerant result across the noise sweep.
- [x] **5.4 — regenerate example docs**
  - `uv run python tools/generate-example-docs.py` then `--check` (per
    `dev/workflows/example-docs.md`).

## Validation

`uv run python py/examples/ga/quadric/fit_conic_quadric.py && uv run python py/examples/ga/quadric/cone_from_conic.py && uv run python py/examples/ga/quadric/tolerant_classification.py && uv run python tools/generate-example-docs.py --check`

## Notes

- Use `Keywords:` terms that cluster with the existing quadric examples (e.g.
  `conic, quadric, fitting, cone, SVD, classification, tolerance`).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
