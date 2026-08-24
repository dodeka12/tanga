# N2 — OPNS Entity Creation

Algebra `BasisN2`, conformal 2D model (**Cl(3,1)**): basis `e1, e2, ep, em`
with the null pair `e∞ = ep + em` (`e∞² = 0`) and `e0 = 0.5·em − 0.5·ep` with
`e∞·e0 = −1`. Conformal point embedding `Cop(x) = x + ½‖x‖²·e∞ + e0`.

Only the null vectors `e∞` and `e0` are used; raw `ep/em` IDs are never
referenced. The "space" for 2D is a circle (a "sphere" or "plane" is a line).

Source of truth: `py/pytanga/geometry/create_n2.py`.
(Recorded at commit `eade1fe`; the `opns` keyword is still an explicit parameter,
`opns=True` selects the OPNS output, `opns=False` the IPNS/dual.)

## Entities

### Point

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `Cop(x,y) = x·e1 + y·e2 + ½‖p‖²·e∞ + e0` | 1 |
| IPNS | `Cop(x,y).dual()` | 3 |

Built **directly** as a null grade-1 conformal point. IPNS = `dual()`.

### Direction

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `x·e1 + y·e2` (no `e∞`/`e0`) | 1 |
| IPNS | `(x·e1 + y·e2).dual()` | 3 |

Built **directly** as a grade-1 Euclidean vector.

### HPoint (homogeneous point)

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `Cop(p) ∧ e∞ · weight` | 2 |
| IPNS | `(Cop(p) ∧ e∞ · w).dual()` | 2 |

Built **directly** as `a.op(einf) * weight`.

### HDirection (homogeneous direction)

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `d ∧ e∞` (`d = x·e1 + y·e2`) | 2 |
| IPNS | `(d ∧ e∞).dual()` | 2 |

Built **directly** as `d.op(einf)`. (The `z` argument is ignored — 2D.)

### PointPair

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `Cop(a) ∧ Cop(b)` | 2 |
| IPNS | `(Cop(a) ∧ Cop(b)).dual()` | 2 |

Built **directly** as the outer product of two conformal points.

### Line

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `Cop(a) ∧ Cop(b) ∧ e∞` (two points + infinity) | 3 |
| IPNS | `(OPNS).dual()` | 1 |

OPNS built **directly** as `a.op(b).op(einf)`.

### Circle / Sphere

2D "circle" and "sphere" are the same entity (a codimension-0 2D object).

| Path | Construction | Grade |
|------|--------------|-------|
| IPNS | `S = Cop(c) − ½·r²·e∞` | 1 |
| OPNS | `S.dual()` | 3 |

Built **via IPNS formula then dualized** for the OPNS output. `create_circle`
delegates to `create_sphere` (normal ignored in 2D).

Imaginary circles/spheres (`is_imaginary=True`) are currently **unsupported** and
raise `NotImplementedError`.

### Space

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `scale · I` (pseudoscalar) | 4 |
| IPNS | the scalar `scale` (dual of the pseudoscalar) | 0 |

Built **directly** as the pseudoscalar; IPNS = `dual()` (a scalar).

### ImagPointPair / ImagCircle

- **Unsupported.** `create_imag_point_pair` and `create_imag_circle` currently
  raise `NotImplementedError` (implementation pending).

### Plane

- **Not representable** in N2 (no plane entity in 2D conformal; a line occupies
  this role). `create_plane` is absent.

## Operators (no OPNS/IPNS distinction)

| Operator | Construction | Grade |
|----------|--------------|-------|
| Rotor | `cos(θ/2) − sin(θ/2)·e12` | 0 + 2 |
| Translator | `1 − ½·t·e∞` | 0 + 2 |
| Dilator | `1 + (1−d)/(1+d)·(e∞∧e0)` (optionally conjugated by T for displaced origin) | 0 + 2 |
| Motor | `T·R` | 0 + 2 + 3 |
| Inversion | `create_sphere(opns=False)` = grade-1 circle IPNS `S = Cop(c) − ½·r²·e∞` | 1 |
| ReflectionLine | `Cop(a)∧Cop(b)∧e∞` (same as OPNS line) | 3 |
| ReflectionPoint | `Cop(p)∧e∞` (same as OPNS HPoint, weight 1) | 2 |
| GeneralRotor | `T·R·T̃` | 0 + 2 |