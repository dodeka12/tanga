# P2 — OPNS Entity Creation

Algebra `BasisP2`, Clifford algebra **Cl(3,0)** used as a projective plane:
basis `e1, e2, e3` where `e3` is the homogeneous coordinate. Homogeneous point
embedding `Hop(a) = a + e3`.

Source of truth: `py/pytanga/geometry/create_p2.py`.
(Recorded at commit `eade1fe`; the `opns` keyword is still an explicit parameter
here, `opns=True` selects the OPNS output; `opns=False` returns the dual.)

## Entities

### Point

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `x·e1 + y·e2 + e3` = `Hop(x,y)` | 1 |
| IPNS | `Hop(x,y).dual()` | 2 |

Built **directly** as a grade-1 homogeneous vector. The IPNS form is the grade-2
`dual()` (intersection of two lines through the point).

### Direction

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `x·e1 + y·e2` (ideal point, `e3 = 0`) | 1 |
| IPNS | `(x·e1 + y·e2).dual()` | 2 |

Built **directly** as a grade-1 direction vector (no `e3` component). Zero-norm
raises `ValueError`.

### Line

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `Hop(origin) ∧ Hop(origin + d)` | 2 |
| IPNS | `(OPNS).dual()` → grade-1 `â − α·e3` | 1 |

OPNS built **directly** as the outer product of two homogeneous points on the
line (both `e3 = 1`). IPNS = dual.

### Space

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `scale · e123` | 3 |
| IPNS | `(scale · e123).dual()` → scalar | 0 |

Built **directly** as the pseudoscalar, then dualized for IPNS.

### Plane / Sphere / Circle / PointPair / HPoint / HDirection

- **Not representable** in P2 (no plane entity in a 2D projective space, and the
  rest are conformal/N2-only). `create_plane` is absent (dispatch raises
  `AttributeError`); the others raise `ValueError`.

## Operators (no OPNS/IPNS distinction)

| Operator | Construction | Grade |
|----------|--------------|-------|
| Rotor | `cos(θ/2) − sin(θ/2)·e12` | 0 + 2 |
| ReflectionLine | bivector `d.x·e13 + d.y·e23` = `d∧e3` | 2 |
| ReflectionPoint | `Hop(point)` = `x·e1 + y·e2 + e3` (via `create_point(opns=True)`) | 1 |

`Translator`, `Dilator`, `Inversion`, `Motor`, `GeneralRotor` all raise
`ValueError` (conformal/N2-only).