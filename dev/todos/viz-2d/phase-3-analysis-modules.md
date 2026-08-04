# Phase 3 — Analysis Modules

MV → entity/operator dataclass recognition for each 2D algebra. **All algorithms
are direct mirrors of the corresponding 3D analysis modules.** The only
differences are the number of spatial basis blades (2D: E1, E2 instead of E1,
E2, E3) and the maximum parseable grades. The geometric extraction formulas
(`blade_factorize`, `blade_factorize_versor`, IPNS/OPNS dualization, `e∞·e₀`
coefficient extraction, etc.) are dimension‑agnostic and remain identical.

## Files to Create

### `py/pytanga/geometry/analysis_e2.py`

**Mirrors `analysis_e3.py`** — same `_get_grades`, same entity/operator dispatch
structure, same `_rotor_from_factors`, same `_reflection_from_factor`, etc.

Differences from E3:
- Blade IDs from `BasisE2` instead of `BasisE3`: only `E1`, `E2`, `E12` (no `E3`, `E13`, `E23`, `E123`)
- Grade 1 → `Direction` (line through origin, same as `_direction_from_factor` in E3 but only x,y)
- Grade 2 → `Space` (bivector e12 = pseudoscalar, same as E3's grade‑3 Space)
- IPNS grade 1 → `Plane` through origin (`_plane_from_ipns_vector` — mirrors E3, only nx,ny)
- IPNS grade 2 → raises ValueError (cannot represent points in E2, same as E3 IPNS grade 3 raising)
- `_plane_from_bivector` — mirrors E3 version, only bivector `E12` component
- Operator analysis: identical factorization logic, same `_rotor_from_factors`
- `make_point`, `make_plane` factory helpers — same pattern, 2D signatures

### `py/pytanga/geometry/analysis_p2.py`

**Mirrors `analysis_p3.py`** — same `_point_or_direction_from_coeffs`, same
`_line_from_factors` (via `blade_factorize`), same `_plane_from_trivector`, same
`_rotor_from_factors`, same versor classification (`_classify_grade1_versor`,
`_classify_grade2_versor`).

Differences from P3:
- Blade IDs from `BasisP2` instead of `BasisP3`: `E1`, `E2`, `E3` (homogeneous), `E12`, `E13`, `E23`, `E123` (no `E4` — P2's homogenous dimension is `E3`)
- `_point_or_direction_from_coeffs` — reads `E1`, `E2`, `E3` (as `e3`, the homogeneous w); same algorithm, only 2 spatial components (x,y from E1,E2)
- Homogeneous weight from `E3` instead of `E4`
- `_line_from_factors` — same `blade_factorize()` logic, dehomogenizes via `E3` instead of `E4`
- `_plane_from_trivector` — same dual → IPNS extraction, reads `E1,E2,E3` (3D plane in P2 = line in 2D)
- Space at grade 3 (pseudoscalar), not grade 4
- `_classify_grade1_versor` — same logic, `E3` replaces `E4`
- `_classify_grade2_versor` — same logic reading `E13`, `E23` (instead of `E14`, `E24`, etc.)

### `py/pytanga/geometry/analysis_n2.py`

**Mirrors `analysis_n3.py`** — same entity dispatch by grade (`_point_or_direction_n2`,
`_decompose_grade2`, `_line_or_circle_n2`, `_sphere_or_plane_n2`), same operator
classification (`_classify_single_grade_versor`, `_classify_double_reflector`,
`_classify_quad_reflector`). All geometric extraction formulas are identical.

Differences from N3:
- Imports from `._n2_helpers` instead of `._n3_helpers` — same helper function names (`einf_coeff`, `eo_coeff`, `eucl_part`, `has_E_component`, `has_translator_components`, `translator_coeffs`, `E_coefficient`, `bivec_has_null`)
- Blade IDs: `E1`, `E2`, `E12` only (no `E3`, `E13`, `E23`)
- Grade ranges shift down by ~1 (5→4):
  - Grade 1 → Point/Direction (same as N3's `_point_or_direction_n3`)
  - Grade 2 → PointPair/HPoint (same as N3's `_decompose_grade2`)
  - Grade 3 → Line/Circle (same as N3's `_line_or_circle_n3`)
  - Grade 4 → Sphere/Plane/Space (same as N3's `_sphere_or_plane_n3` + Space)
- `_decompose_grade2` — identical Perwass extraction: `Q∧e∞` test, `L = Q∧e∞`, `P* = Q·e∞`, midpoint, separation. Only changes: fewer spatial components.
- `_line_or_circle_n2` — identical `C∧e∞` test, same `_decompose_line` and `_decompose_circle` logic
- `_sphere_or_plane_n2` — same IPNS dual → `eo_c` discrimination → Plane vs Sphere
- `_rotor_from_factors` — identical, reads `E12` bivector only (no `E23`, `E13`)
- `_translator_from_versor` — identical, reads `translator_coeffs` (dx, dy only)
- `_dilator_from_versor` — identical, reads `E_coefficient`
- `_factor_to_point` — identical homogeneous point extraction
- All operator classification logic (`_classify_single_grade_versor`, `_classify_double_reflector`, `_classify_quad_reflector`) — identical algorithms

### `py/pytanga/geometry/analysis_pga2.py`

**Mirrors `analysis_pga3.py`** — same Gunn/Dorst 4D PGA entity dispatch
(`_plane_from_vector`, `_line_from_bivector`, `_point_from_trivector`),
same IPNS analysis, same operator classification via `blade_factorize_versor`.

Differences from PGA3:
- Imports from `._pga2_utils` instead of `._pga3_utils` — same function names (`_pga2_dual`, `_get_e0_coeff`)
- Blade IDs: `E1`, `E2`, `E12` only (no `E3`, `E13`, `E23`, `E123`)
- Grade ranges shift down:
  - Grade 1 → Plane (same as `_plane_from_vector` in PGA3, only nx,ny)
  - Grade 2 → Line (same as `_line_from_bivector` in PGA3, 2D line = point intersection)
  - Grade 3 → Point/Direction (same as `_point_from_trivector` in PGA3)
  - Grade 3 also → Space (I_3d = e₁∧e₂∧e₀, grade 3 pseudoscalar in PGA2)
- `_plane_from_vector` — reads `E1`,`E2` normal, `EP` (e₀) for distance
- `_line_from_bivector` — same `blade_factorize()` → 2 plane vectors → intersection point + direction
- `_line_origin_from_planes` — identical Cramer's rule, 2D plane intersection
- `_point_from_trivector` — identical `_pga2_dual` → IPNS → dehomogenize
- `_point_or_direction_from_ipns` — identical, `_get_e0_coeff` for α
- Operator analysis — identical `blade_factorize_versor` logic:
  - `_reflection_from_factor` → `Reflection`
  - `_rotor_from_factors` → `Rotor`
  - `_translator_from_versor` → `Translator`
  - `_motor_from_factors` → `Motor`
  - `_general_rotor_from_versor` → `GeneralRotor`
  - No Stubs for N3‑only operators that PGA3 also stubs

### `py/pytanga/geometry/_n2_helpers.py`

**Mirrors `_n3_helpers.py`** — same function names, same algebraic identities
but for 2D.

```python
# Blade IDs
E1 = 1
E2 = 2
EP = 4
EM = 8
E12 = 3

# Same functions, adapted for 2D:
# - get_einf(basis), get_eo(basis)
# - einf_coeff(mv, eo), eo_coeff(mv, einf)
# - eucl_part(mv, einf, eo)  → returns (ex, ey) instead of (ex, ey, ez)
# - has_E_component(mv, alg), has_translator_components(mv, alg)
# - translator_coeffs(mv, alg)  → returns (dx, dy) instead of (dx, dy, dz)
# - E_coefficient(mv, alg)
# - bivec_has_null(mv, einf, eo)
```

### `py/pytanga/geometry/_pga2_utils.py`

**Mirrors `_pga3_utils.py`** — same function names but for 4D PGA:

```python
# Blade IDs
E1 = 1
E2 = 2
EP = 4
EM = 8
E12 = 3
E123 = 7

# Same functions:
# - _get_e0(basis)     → MV({EP:1, EM:1})
# - _get_e0_coeff(mv)  → algebraic extraction of e₀ coefficient
# - _pga2_dual(mv)     → 4D PGA dual: mv.ip(I_3d_pinv) where I_3d = e₁∧e₂∧e₀
```

## Implementation Checklist

- [ ] 3.1  Create `py/pytanga/geometry/_n2_helpers.py` — mirror of `_n3_helpers.py`, 2D blade IDs + helpers
- [ ] 3.2  Create `py/pytanga/geometry/_pga2_utils.py` — mirror of `_pga3_utils.py`, 4D PGA dual + helpers
- [ ] 3.3  Create `py/pytanga/geometry/analysis_e2.py` — mirror of `analysis_e3.py`, all same methods, 2D blade IDs
- [ ] 3.4  Create `py/pytanga/geometry/analysis_p2.py` — mirror of `analysis_p3.py`, all same methods, E3=homogeneous
- [ ] 3.5  Create `py/pytanga/geometry/analysis_n2.py` — mirror of `analysis_n3.py`, all same methods, 2D grades
- [ ] 3.6  Create `py/pytanga/geometry/analysis_pga2.py` — mirror of `analysis_pga3.py`, all same methods, 4D PGA
- [ ] 3.7  Verify E2 round‑trip: `create_e2.create_direction(b, 3,4,0)` → `analysis_e2.analyze_entity(mv)` → `Direction(3,4,0)`
- [ ] 3.8  Verify E2 rotor round‑trip: `create_e2.create_rotor(b, π/2, Dir(0,0,1))` → `analysis_e2.analyze_operator(mv)` → `Rotor(angle=π/2, axis=Dir(0,0,1))`
- [ ] 3.9  Verify P2 point round‑trip: `create_p2.create_point(b, 5,3,0)` → `analyze_entity(mv)` → `Point(5,3,0)`
- [ ] 3.10 Verify P2 line: `create_p2.create_line(b, Point(1,1,0), Dir(2,0,0))` → `analyze_entity(mv)` → `Line`
- [ ] 3.11 Verify N2 point round‑trip: `create_n2.create_point(b, 2,3,0)` → `analyze_entity(mv)` → `Point(2,3,0)`
- [ ] 3.12 Verify N2 sphere round‑trip: `create_n2.create_sphere(b, Point(1,1,0), 2)` → `analyze_entity(mv)` → `Sphere(Point(1,1,0), 2)`
- [ ] 3.13 Verify PGA2 point round‑trip: `create_pga2.create_point(b, 1,2,0)` → `analyze_entity(mv)` → `Point(1,2,0)`