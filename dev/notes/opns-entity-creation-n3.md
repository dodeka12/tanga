# N3 — OPNS Entity Creation

Algebra `BasisN3`, conformal 3D model (**Cl(4,1)**): basis `e1, e2, e3, ep,
em` with the null pair `e∞ = ep + em` (`e∞² = 0`) and `e0 = 0.5·em − 0.5·ep`
(`e∞·e0 = −1`). Conformal point embedding `Cop(x) = x + ½‖x‖²·e∞ + e0`.

Only the null vectors `e∞` and `e0` are used; raw `ep/em` IDs are never
referenced.

Source of truth: `py/pytanga/geometry/create_n3.py`.
(Recorded at commit `eade1fe`; the `opns` keyword is still an explicit parameter,
`opns=True` selects the OPNS output, `opns=False` the IPNS/dual.)

## Entities

### Point

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `Cop(x,y,z) = x·e1 + y·e2 + z·e3 + ½‖p‖²·e∞ + e0` | 1 |
| IPNS | `Cop(x,y,z).dual()` | 4 |

Built **directly** as a null grade-1 conformal point. IPNS = `dual()`.

### Direction

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `x·e1 + y·e2 + z·e3` (no `e∞`/`e0`) | 1 |
| IPNS | `(x·e1 + y·e2 + z·e3).dual()` | 4 |

Built **directly** as a grade-1 Euclidean vector.

### HPoint (homogeneous point)

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `Cop(p) ∧ e∞ · weight` | 2 |
| IPNS | `(Cop(p) ∧ e∞ · w).dual()` | 3 |

Built **directly** as `a.op(einf) * weight`.

### HDirection (homogeneous direction)

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `d ∧ e∞` (`d = x·e1 + y·e2 + z·e3`) | 2 |
| IPNS | `(d ∧ e∞).dual()` | 3 |

Built **directly** as `d.op(einf)`.

### PointPair

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `Cop(a) ∧ Cop(b)` | 2 |
| IPNS | `(Cop(a) ∧ Cop(b)).dual()` | 3 |

Built **directly** as the outer product of two conformal points.

### Line

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `Cop(a) ∧ Cop(b) ∧ e∞` (two points + infinity) | 3 |
| IPNS | `(OPNS).dual()` | 2 |

OPNS built **directly** as `a.op(b).op(einf)`.

### Plane

| Path | Construction | Grade |
|------|--------------|-------|
| IPNS | `P = â + α·e∞` (unit normal `â`, signed distance `α`) | 1 |
| OPNS | `P.dual()` | 4 |

Built **via IPNS formula then dualized** for the OPNS output.

### Sphere

| Path | Construction | Grade |
|------|--------------|-------|
| IPNS | `S = Cop(c) − ½·r²·e∞` | 1 |
| OPNS | `S.dual()` | 4 |

Built **via IPNS formula then dualized** for the OPNS output.

Imaginary spheres (`is_imaginary=True`) are currently **unsupported** and raise
`NotImplementedError`.

### Circle

| Path | Construction | Grade |
|------|--------------|-------|
| IPNS | `S ∧ P` (sphere IPNS `S` ∧ plane IPNS `P`) | 2 |
| OPNS | `(S ∧ P).dual()` | 3 |

Built **via IPNS intersection then dualized** for the OPNS output.

### Space

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `scale · I` (pseudoscalar) | 5 |
| IPNS | the scalar `scale` (dual of the pseudoscalar) | 0 |

Built **directly** as the pseudoscalar; IPNS = `dual()` (a scalar).

### ImagPointPair / ImagCircle

- **Unsupported.** `create_imag_point_pair` and `create_imag_circle` currently
  raise `NotImplementedError` (implementation pending).

## Operators (no OPNS/IPNS distinction)

| Operator | Construction | Grade |
|----------|--------------|-------|
| Rotor | `cos(θ/2) − sin(θ/2)·(ax·e23 + ay·e31 + az·e12)` | 0 + 2 |
| Translator | `1 − ½·t·e∞` | 0 + 2 |
| Dilator | `1 + (1−d)/(1+d)·(e∞∧e0)` (optionally conjugated by T for displaced origin) | 0 + 2 |
| Motor | `T·R` | 0 + 2 + 4 |
| Inversion | `create_sphere(opns=False)` = grade-1 sphere IPNS `S = Cop(c) − ½·r²·e∞` | 1 |
| ReflectionPlane | `Cop(a)∧Cop(b)∧Cop(c)∧e∞` (same as OPNS plane) | 4 |
| ReflectionLine | `Cop(a)∧Cop(b)∧e∞` (same as OPNS line) | 3 |
| ReflectionPoint | `Cop(p)∧e∞` (same as OPNS HPoint, weight 1) | 2 |
| GeneralRotor | `T·R·T̃` | 0 + 2 |