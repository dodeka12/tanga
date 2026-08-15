# PGA3 — OPNS Entity Creation

Algebra `BasisPGA3`, Gunn/Dorst plane-based PGA for 3D geometry, modelled via
the **5D null-vector embedding** `e0 = ep + em` (`ep² = +1`, `em² = −1`,
`e0² = 0`). The geometric subspace `{e1, e2, e3, e0}` is isomorphic to
G(3,0,1). The complement dual (J-map/Hodge star, `mv.dual()` via
`BasisPGA3.dual`) maps grade `k` → grade `4−k` in the PGA subspace; it is a
**complement** map, not the metric dual.

Entity grades follow Gunn/Dorst:
plane = grade-1, line = grade-2, point = grade-3, space = grade-4.

Source of truth: `py/pytanga/geometry/create_pga3.py` and
`docs/py/basis/pga_null_embedding.md`.
(Recorded at commit `eade1fe`; the `opns` keyword is still an explicit parameter,
`opns=True` selects the OPNS output, `opns=False` the IPNS/dual.)

## Entities

### Point

| Path | Construction | Grade |
|------|--------------|-------|
| IPNS | `x·e1 + y·e2 + z·e3 + e0` | 1 |
| OPNS | `p_ipns.dual()` → grade-3 trivector (intersection of three planes) | 3 |

Built **via IPNS then J-dualized** for the OPNS output.

### Direction (ideal point)

| Path | Construction | Grade |
|------|--------------|-------|
| IPNS | `x·e1 + y·e2 + z·e3` (written `−x·e1 − y·e2 − z·e3`) | 1 |
| OPNS | `d_ipns.dual()` → grade-3 trivector (ideal point) | 3 |

Built **via IPNS then J-dualized** for the OPNS output.

### Line

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `p1.op(p2)` — the intersection of two planes, both containing the line | 2 |
| IPNS | `(OPNS).dual()` | 2 |

OPNS built **directly** as the wedge of two plane blades (grade-1 vectors). The
two planes are chosen orthogonal-perpendicular to the line: `n1·direction = 0`,
`n2 = direction × n1`. IPNS = `dual()` (grade 2 is self-dual in PGA3 subspace).

### Plane

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `nx·e1 + ny·e2 + nz·e3 + d·e0` (`d = −n·point`) | 1 |
| IPNS | `(OPNS).dual()` | 3 |

OPNS built **directly** as a grade-1 vector. IPNS = `dual()`.

### Space

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `scale · e1 ∧ e2 ∧ e3 ∧ e0` | 4 |
| IPNS | `(OPNS).dual()` → scalar | 0 |

Built **directly** as the grade-4 PGA pseudoscalar, then dualized for IPNS.

### Sphere / Circle / PointPair / HPoint / HDirection

- **Not representable** in PGA3. `create_sphere`, `create_circle`,
  `create_point_pair`, `create_homogeneous_point` raise `ValueError`
  (conformal/N3-only).

## Operators (no OPNS/IPNS distinction)

| Operator | Construction | Grade |
|----------|--------------|-------|
| Rotor | `cos(θ/2) − sin(θ/2)·(ax·e23 + ay·e31 + az·e12)` | 0 + 2 |
| Translator | `1 + 0.5·(dx·e1∧e0 + dy·e2∧e0 + dz·e3∧e0)` | 0 + 2 |
| Motor | `T·R` | 0 + 2 + 4 |
| GeneralRotor | `T·R·T̃` | 0 + 2 |
| ReflectionPlane | grade-1 plane blade (same as OPNS plane) | 1 |
| ReflectionLine | grade-2 line bivector (same as OPNS line) | 2 |
| ReflectionPoint | grade-3 point trivector (same as OPNS point) | 3 |

`Dilator`, `Inversion` raise `ValueError` (conformal/N3-only).