# E3 — OPNS Entity Creation

Algebra `BasisE3`, Clifford algebra **Cl(3,0)**: basis `e1, e2, e3`, pseudoscalar
`I = e123`. No homogeneous or conformal embedding, so only entities *through the
origin* are representable.

Source of truth: `py/pytanga/geometry/create_e3.py`.
(Recorded at commit `eade1fe`; the `opns` keyword is still an explicit parameter
here, `opns=True` selects the OPNS output.)

## Entities

### Point

A point cannot be represented as a null space in E3 (that requires P3 or N3),
but its Euclidean coordinates always map to the **e1, e2, e3 components**,
independent of OPNS/IPNS:

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `x·e1 + y·e2 + z·e3` | 1 |
| IPNS | `x·e1 + y·e2 + z·e3` (same — OPNS/IPNS independent) | 1 |

### Direction

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `x·e1 + y·e2 + z·e3` | 1 |
| IPNS | `(x·e1 + y·e2 + z·e3).dual()` | 2 |

OPNS built **directly** as a grade-1 vector; IPNS is its `dual()` (a bivector).

### Line

- Through origin only. Built as the **same grade-1 vector** as `Direction`
  (`x·e1 + y·e2 + z·e3`, via `create_direction`), so it also dualizes for IPNS.
- Not through the origin → `ValueError` ("only lines through the origin").
- Note: analyzing the resulting grade-1 vector with `opns=True` yields a
  `Direction`, not a `Line` (E3 cannot distinguish a line-through-origin from a
  raw direction vector).

### Plane

| Path | Construction | Grade |
|------|--------------|-------|
| IPNS | `nx·e1 + ny·e2 + nz·e3` (plane normal; only valid when plane passes through origin) | 1 |
| OPNS | `ipns.dual()` → grade-2 bivector `nx·e23 + ny·e31 + nz·e12` | 2 |

Built **via IPNS then dualized** for the OPNS output. A plane must pass through
the origin (`ValueError` otherwise).

### Space

| Path | Construction | Grade |
|------|--------------|-------|
| OPNS | `scale · e123` | 3 |
| IPNS | the scalar `scale` (dual of the pseudoscalar) | 0 |

Built **directly** as the pseudoscalar; IPNS = `dual()` (a scalar).

### Sphere / Circle / PointPair / HPoint / HDirection

- **Not representable** in E3. `create_sphere`, `create_circle`,
  `create_point_pair`, `create_homogeneous_point` all raise `ValueError`
  (conformal/N3-only).

## Operators (no OPNS/IPNS distinction)

| Operator | Construction | Grade |
|----------|--------------|-------|
| Rotor | `cos(θ/2) − sin(θ/2)·(ax·e23 + ay·e31 + az·e12)` | 0 + 2 |
| ReflectionLine | grade-1 vector `d.x·e1 + d.y·e2 + d.z·e3` | 1 |
| ReflectionPlane | bivector `nx·e23 − ny·e31 + nz·e12` = `n·I⁻¹` | 2 |

`Translator`, `Dilator`, `Inversion`, `Motor`, `GeneralRotor`,
`ReflectionOrigin` all raise `ValueError` (conformal/projective-only).