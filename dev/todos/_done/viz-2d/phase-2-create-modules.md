# Phase 2 — Create Modules

Entity/operator dataclass → MV construction for each 2D algebra. Follow the
pattern of `create_e3.py` with 2D‑specific entity mappings.

## Entity Mapping (2D)

| 3D Entity | 2D Interpretation | Fields Used | Notes |
|-----------|-------------------|-------------|-------|
| `Point(x,y,z)` | 2D point | `x`, `y` | `z` always 0 |
| `Direction(x,y,z)` | 2D direction | `x`, `y` | `z` always 0 |
| `Line(origin, dir)` | 2D line | `origin.{x,y}`, `dir.{x,y}` | `z` always 0 |
| `Plane(point, normal)` | 2D line (dual) | `point.{x,y}`, `normal.{x,y}` | 2D line = hyperplane |
| `Circle(center, normal, r)` | Circle in E2/P2/N2 | `center.{x,y}`, `normal=(0,0,1)`, `r` | Same as 3D, embedded in XY plane |
| `Sphere(center, r)` | Circle in N2 | `center.{x,y}`, `r` | N2 sphere = 2D circle |
| `Space(scale)` | Pseudoscalar | `scale` | Grade-2 for E2, grade-3 for P2, grade-4 for N2/PGA2 |
| `PointPair(a, b)` | Point pair in 2D | `a.{x,y}`, `b.{x,y}` | N2/PGA2 only |

## Files to Create

### `py/pytanga/geometry/create_e2.py`

E2 (Cl(2)): only origin‑through entities + direction vectors.

- `create_point(basis, x, y, *z*)` → raises ValueError (no points in E2)
- `create_direction(basis, x, y, *z*)` → `{1:x, 2:y}` (grade‑1 vector)
- `create_line(basis, origin, direction)` → raises if origin ≠ (0,0,0), else direction vector
- `create_plane(basis, plane)` → raises if point ≠ (0,0,0), else normal as grade‑1 vector, dualize for OPNS
- `create_space(basis, scale)` → `{3: scale}` (the bivector e12)
- `create_rotor(basis, angle, axis)` → `cos(θ/2) + sin(θ/2)·e12` (scalar + 1 bivector in 2D)
- `create_reflection_line(basis, direction)` → grade‑1 vector
- `create_reflection_plane(basis, normal)` → `−n·I⁻¹` = `−nx·e₂ + ny·e₁` in OPNS (or just the normal in IPNS)
- Stub functions raising ValueError for: `create_sphere`, `create_circle`,
  `create_point_pair`, `create_homogeneous_point`, `create_translator`,
  `create_dilator`, `create_inversion`, `create_motor`,
  `create_general_rotor`, `create_reflection_origin`,
  `create_general_dilator`

### `py/pytanga/geometry/create_p2.py`

P2 (Cl(3) with homogeneous e₃): points, lines, directions.

- `create_point(basis, x, y, *z*)` → `{1:x, 2:y, 4:1}` (homogeneous)
- `create_direction(basis, x, y, *z*)` → `{1:x, 2:y}` (no e₃ component)
- `create_line(basis, origin, direction)` → `Cop(a) ∧ Cop(b)` in OPNS (grade‑2), with e₃ terms
- `create_plane(basis, plane)` → Normal as grade‑1, e₃ component = signed distance
- `create_space(basis, scale)` → `{7: scale}` (e123)
- `create_rotor(basis, angle, axis)` → `cos(θ/2) + sin(θ/2)·e12`
- `create_reflection_line(basis, direction)` → grade‑1 vector (with 0 e₃)
- `create_reflection_plane(basis, normal)` → bivector `n·I⁻¹`
- `create_reflection_origin(basis)` → `e₃` as versor
- Stubs for N2‑only operators

### `py/pytanga/geometry/_n2_helpers.py`

Helper module for N2 blade IDs and null vector construction.

- Blade IDs: `E1=1, E2=2, EP=4, EM=8, E12=3`
- `get_einf(basis)` → `{EP:1, EM:1}`
- `get_eo(basis)` → `{EP:-0.5, EM:0.5}`

### `py/pytanga/geometry/_pga2_utils.py`

Helper module for PGA2 dual and blade IDs.

- Blade IDs: `E1=1, E2=2, EP=4, EM=8, E12=3`
- `_get_e0(basis)` → `{EP:1, EM:1}`
- `_get_e0_recip(basis)` → `{EP:0.5, EM:-0.5}`
- `_pga2_dual(mv)` → Dual via Gunn/Dorst convention for 4D PGA

### `py/pytanga/geometry/create_n2.py`

N2 (Cl(4) with null embedding): full conformal 2D.

- `create_point(basis, x, y, *z*)` → `Cop(x,y)` = `x·e₁ + y·e₂ + ½r²·e∞ + e₀`
- `create_direction(basis, x, y, *z*)` → `{1:x, 2:y}`
- `create_line(basis, origin, direction)` → `Cop(a)∧Cop(b)∧e∞` (grade‑3 OPNS)
- `create_plane(basis, plane)` → IPNS grade‑1 vector `â + α·e∞`, dualize for OPNS
- `create_circle(basis, center, normal, radius)` → IPNS `S∧P`, dualize for OPNS
- `create_sphere(basis, center, radius)` → IPNS `Cop(c) − ½r²·e∞`, dualize for OPNS
- `create_point_pair(basis, a, b)` → `Cop(a)∧Cop(b)` (grade‑2)
- `create_space(basis, scale)` → `{15: scale}` (e1∧e2∧ep∧em)
- `create_rotor(basis, angle, axis)` → `cos(θ/2) + sin(θ/2)·e12`
- `create_translator(basis, dx, dy)` → `1 − ½·t·e∞`
- `create_dilator(basis, factor)` → `1 + (1−d)/(1+d)·E` where `E=ei∧eo`
- `create_motor(basis, rotor, translator)` → `T·R`
- `create_reflection_line(basis, dir)` → `d∧e∞` (grade‑2)
- `create_reflection_plane(basis, normal)` → grade‑1 `{1:nx, 2:ny}`
- `create_inversion(basis, center, radius)` → sphere IPNS
- `create_reflection_origin(basis)` → e₀
- `create_general_rotor(basis, rotor, translator)` → `T·R·T̃`
- `create_general_dilator(basis, factor, translator)` → `T·D·T̃`

### `py/pytanga/geometry/create_pga2.py`

PGA2 (Gunn/Dorst 4D PGA for 2D via null embedding).

- `create_point(basis, x, y, *z*)` → IPNS: `{1:x, 2:y, EP:1, EM:1}`; OPNS: three 1‑vectors wedged
- `create_direction(basis, x, y, *z*)` → IPNS: `{1:x, 2:y}`; OPNS: `_pga2_dual(ipns)`
- `create_line(basis, origin, direction)` → wedge of two planes (grade‑2)
- `create_plane(basis, plane)` → `{1:nx, 2:ny, EP:d, EM:d}` with `d = −n·p`
- `create_space(basis, scale)` → `e1∧e2∧e0` (grade‑3)
- `create_rotor(basis, angle, axis)` → `cos(θ/2) + sin(θ/2)·e12`
- `create_translator(basis, dx, dy)` → `1 − ½·(dx·e1∧e0 + dy·e2∧e0)`
- `create_motor(basis, rotor, translator)` → `T·R`
- `create_reflection_line(basis, dir)` → bivector `d∧e0`
- `create_reflection_plane(basis, normal)` → grade‑1 vector in Euclidean subspace
- `create_reflection_origin(basis)` → `e1∧e2` (grade‑2 trivector? No — e1∧e2 is grade‑2 bivector)
- `create_general_rotor(basis, rotor, translator)` → `T·R·T̃`
- Stubs for N2‑only operators: `create_sphere`, `create_circle`, `create_point_pair`,
  `create_dilator`, `create_inversion`, `create_general_dilator`

## Implementation Checklist

- [ ] 2.1  Create `py/pytanga/geometry/_n2_helpers.py` — blade IDs + `get_einf`/`get_eo`
- [ ] 2.2  Create `py/pytanga/geometry/_pga2_utils.py` — blade IDs + `_get_e0`/`_get_e0_recip`/`_pga2_dual`
- [ ] 2.3  Create `py/pytanga/geometry/create_e2.py` — all E2 entity + operator creation functions
- [ ] 2.4  Create `py/pytanga/geometry/create_p2.py` — all P2 entity + operator creation functions
- [ ] 2.5  Create `py/pytanga/geometry/create_n2.py` — all N2 entity + operator creation functions
- [ ] 2.6  Create `py/pytanga/geometry/create_pga2.py` — all PGA2 entity + operator creation functions
- [ ] 2.7  Verify: `create_e2.create_direction(e2_basis, 3, 4, 0)` = `3·e1 + 4·e2`
- [ ] 2.8  Verify: `create_e2.create_rotor(e2_basis, π/2, Dir(0,0,1))` = `cos(π/4) + sin(π/4)·e12`
- [ ] 2.9  Verify: `create_p2.create_point(p2_basis, 5, 3, 0)` = `5·e1 + 3·e2 + e3`
- [ ] 2.10 Verify: `create_n2.create_point(n2_basis, 2, 3, 0)` lies on null cone (sp(mv, rev(mv)) ≈ 0)
- [ ] 2.11 Verify: `create_n2.create_sphere(n2_basis, Point(1,1,0), 2)` → dualize → sphere in OPNS
- [ ] 2.12 Verify: `create_pga2.create_point(pga2_basis, 1, 2, 0, opns=False)` → `e1 + 2·e2 + e0`
- [ ] 2.13 Verify: 2D rotor `create_rotor(..., π/2, Dir(0,0,1))` has only scalar + e12 components (all algebras)