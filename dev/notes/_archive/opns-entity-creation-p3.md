# P3 — OPNS Entity Creation

Algebra `BasisP3`, Clifford algebra **Cl(4,0)** used as a projective space:
basis `e1, e2, e3, e4` where `e4` is the homogeneous coordinate. Homogeneous
point embedding `Hop(a) = a + e4`.

Source of truth: `py/pytanga/geometry/create_p3.py`.
(Recorded at commit `eade1fe`; the `opns` keyword is still an explicit parameter
here, `opns=True` selects the OPNS output; `opns=False` returns the dual.)

## Entities

### Point

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `x·e1 + y·e2 + z·e3 + e4` = `Hop(x,y,z)` | 1 |
| IPNS | `Hop(x,y,z).dual()` (intersection of 3 orthogonal planes) | 3 |

Built **directly** as a grade-1 homogeneous vector. IPNS = the grade-3 dual.

### Direction

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `x·e1 + y·e2 + z·e3` (ideal point, `e4 = 0`) | 1 |
| IPNS | `(x·e1 + y·e2 + z·e3).dual()` | 3 |

Built **directly** as a grade-1 direction vector (no `e4` component). Zero-norm
raises `ValueError`.

### Line

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `Hop(origin) ∧ Hop(origin + d)` | 2 |
| IPNS | `(OPNS).dual()` (intersection of two IPNS planes) | 2 |

OPNS built **directly** as the outer product of two homogeneous points on the
line (both `e4 = 1`). In G(4,0) grade 2 is the self-dual grade, so OPNS and IPNS
are **both bivectors** but with different coefficients.

### Plane

| Path | Construction | Grade |
|------|--------------|-------|
| IPNS | `â − α·e4` = `ux·e1 + uy·e2 + uz·e3 − α·e4` (unit normal `â`, signed distance `α`) | 1 |
| OPNS | `ipns.dual()` → grade-3 trivector | 3 |

Built **via IPNS formula then dualized** for the OPNS output (`P = â − α·e4`,
Perwass GIPNS).

### Space

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `scale · e1234` | 4 |
| IPNS | `(scale · e1234).dual()` → scalar | 0 |

Built **directly** as the pseudoscalar, then dualized for IPNS.

### Sphere / Circle / PointPair / HPoint / HDirection

- **Not representable** in P3 (conformal/N3-only). `create_sphere`,
  `create_circle`, `create_point_pair`, `create_homogeneous_point` all raise
  `ValueError`.

## Operators (no OPNS/IPNS distinction)

| Operator | Construction | Grade |
|----------|--------------|-------|
| Rotor | `cos(θ/2) − sin(θ/2)·(ax·e23 + ay·e31 + az·e12)` | 0 + 2 |
| ReflectionLine | bivector `d.x·e14 + d.y·e24 + d.z·e34` = `d∧e4` | 2 |
| ReflectionPlane | grade-1 vector `n.x·e1 + n.y·e2 + n.z·e3` (IPNS of the plane, `e4 = 0`) | 1 |
| ReflectionPoint | `Hop(point)` (via `create_point(opns=True)`) | 1 |

`Translator`, `Dilator`, `Inversion`, `Motor`, `GeneralRotor` all raise
`ValueError` (conformal/N3-only).