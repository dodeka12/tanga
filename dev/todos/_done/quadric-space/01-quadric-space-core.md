# Phase 1 — Quadric space core module (`pytanga.quadric`)

## Goal

New `py/pytanga/quadric/` package with the algebra bases, point embedding, symmetric
matrix ↔ coeff maps, and conic/quadric construction from points. Pure math + tests,
no entities or viz yet.

## Files

- New: `py/pytanga/quadric/__init__.py`
- New: `py/pytanga/quadric/_basis.py` (`BasisQ2`, `BasisQ3`)
- New: `py/pytanga/quadric/_mapping.py` (`to_coeffs`, `from_coeffs`)
- New: `py/pytanga/quadric/_embedding.py` (`embed_point`)
- New: `py/pytanga/quadric/_build.py` (`conic_from_points`, `quadric_from_points`,
  `conic_from_points_svd`, `quadric_from_points_svd`, `line_from_points`)
- New: `py/tests/quadric/__init__.py`, `py/tests/quadric/test_core.py`

## Steps

- [x] **1.1 — `_basis.py`**
  - `BasisQ2(Algebra)` → `super().__init__(6, 0, …)`, named blades `b1…b6`
    (`E1…E6` = `1,2,4,8,16,32`), `I = pseudoscalar`.
  - `BasisQ3(Algebra)` → `super().__init__(10, 0, …)`, `b1…b10`, `I`.
  - `_display_basis` via `build_display_basis` with the `b1…b6` / `b1…b10` names.

- [x] **1.2 — `_mapping.py`**
  - `to_coeffs(A)` (symmetric 3×3 → 6-tuple) and `from_coeffs(t)` (6-tuple → 3×3)
    using the README ordering with `√2/2` on the diagonal terms.
  - `to_coeffs(Q)` (4×4 → 10-tuple) and `from_coeffs(t)` (10-tuple → 4×4).
  - Accept numpy arrays and nested lists; validate symmetry.

- [x] **1.3 — `_embedding.py`**
  - `embed_point(basis, x, y)` → rank-1 symmetric matrix as a grade-1 MV
    (`x b₁ + y b₂ + (√2/2) b₃ + (√2/2)x² b₄ + (√2/2)y² b₅ + xy b₆`).
  - `embed_point(basis, x, y, z)` → 3D form (README).

- [x] **1.4 — `_build.py`**
  - `conic_from_points(basis, points)` = `from_coeffs(dual(∧ embed_point(pᵢ)))`
    (5 points).
  - `quadric_from_points(basis, points)` (9 points).
  - `conic_from_points_svd(basis, points)` / `quadric_from_points_svd(...)`:
    stack `to_coeffs(p pᵀ)` rows, take the right singular vector for the smallest
    singular value.
  - `line_from_points(basis, a, b)` = `embed(a) ∧ embed(b) ∧ b₄ ∧ b₅ ∧ b₆`.

- [x] **1.5 — `__init__.py` exports** — `BasisQ2`, `BasisQ3`,
  `embed_point`, `to_coeffs`, `from_coeffs`, the `*_from_points` helpers.

- [x] **1.6 — Tests** (`test_core.py`)
  - `to_coeffs ∘ from_coeffs == id` (2D and 3D).
  - Incidence: `embed_point(p) · coeff(A) == ½ pᵀ A p` for sample points/matrices.
  - `conic_from_points` agrees with `conic_from_points_svd` up to scale, and all
    5 points satisfy `pᵀ A p = 0`.
  - `quadric_from_points` agrees with the SVD path up to scale (9 points).
  - `line_from_points(a, b)` has `embed(a) ∧ result == 0` and
    `embed(b) ∧ result == 0`.

- [x] **1.7 — Validate** — `uv run pytest py/tests/quadric/test_core.py -q`.

## Validation

`uv run pytest py/tests/quadric/test_core.py -q`

## Notes

- Keep `pytanga.quadric` free of `pytanga.geometry` / `pytanga.viz` imports.
- The rotation rotor from the thesis (`R₁ = cosθ − ½sinθ (b₄−b₅)∧b₆` with the `√2`
  rescaling, `R₂ = cos(θ/2) − sin(θ/2) b₁∧b₂`) can be added later; not required here.
